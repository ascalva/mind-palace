"""Reversible writes end to end — propose (tailored, firewalled) → approve → stage → rollback
(Track G, item G5). The class-2 hands "propose (never send) with a MirrorView tailoring read".

Three things are proven together:
  * the tailoring read is a `MirrorView` — the composer cannot draw on observed/curated exhaust
    (the firewall, by type), and the output is a `ProposedEffect`, never a sent artifact;
  * the approved effect is constructable (LIGHT covers REVERSIBLE) and rides the ledger; and
  * the edge effector STAGES a draft the owner can delete (reversible), never sends, and no param
    can direct the on-disk write (traversal is unrepresentable).
"""

from __future__ import annotations

import pytest

from core.effect_proposal import (
    NotAReversibleWriteError,
    ReversibleWriteProposer,
)
from core.mirror import MirrorView, NonMirrorRowError
from edge.effectors.writes import (
    EffectorsDisabled,
    NotStageableError,
    ReversibleWriteEffector,
)
from ops.effect_ledger import EffectLedger
from ops.effects import ApprovalRef, ApprovalStrength, Effect, ReversibilityClass, ScopedCapability


class _Source:
    """A row source that filters to the requested provenances, like the real VectorStore."""

    def __init__(self, rows):
        self._rows = rows

    def all_rows(self, *, provenances=None):
        allowed = {p.value for p in provenances} if provenances is not None else None
        return [r for r in self._rows if allowed is None or r.get("provenance") in allowed]


def _authored_mirror() -> MirrorView:
    # The projection keeps authored, drops the observed exhaust — so the tailor only ever sees the
    # owner's own notes (π_MR). The observed row below must NOT reach the draft.
    return MirrorView.project(_Source([
        {"title": "voice", "text": "I write short and plain.", "provenance": "authored-solo"},
        {"title": "leak", "text": "SECRET from a sensed web page", "provenance": "observed"},
    ]))


# --- the firewall: tailoring reads authored-only, and cannot even be handed observed data ---------
def test_tailor_sees_only_authored_rows(tmp_path):
    seen: list[str] = []

    def spy_tailor(mirror: MirrorView, request: str) -> str:
        # Every row the tailor sees is authored — the observed exhaust was projected out.
        for r in mirror.rows():
            assert r["provenance"] == "authored-solo"
            seen.append(r["text"])
        return "a plain draft"

    proposer = ReversibleWriteProposer(tailor=spy_tailor)
    proposal = proposer.propose_draft_reply(
        to="bob@example.com", subject="re: meeting", request="meeting", mirror=_authored_mirror()
    )
    assert proposal.actuator == "draft_reply"
    assert dict(proposal.params)["body"] == "a plain draft"
    assert seen == ["I write short and plain."]      # the observed row never reached the tailor


def test_observed_data_cannot_be_handed_to_the_proposer():
    # The firewall is structural: you cannot build a MirrorView holding observed rows, so the tailor
    # cannot be handed exhaust in the first place (not "checked and refused" — unrepresentable).
    with pytest.raises(NonMirrorRowError):
        MirrorView(_rows=({"provenance": "observed", "text": "x"},))


def test_proposer_refuses_a_non_reversible_actuator():
    proposer = ReversibleWriteProposer()
    with pytest.raises(NotAReversibleWriteError):
        proposer.propose("send_email", {"to": "x", "subject": "y", "body": "z"})  # irreversible
    with pytest.raises(NotAReversibleWriteError):
        proposer.propose("sense_fetch", {"upstream": "weather"})                  # sensing


# --- the full loop: propose → ledger → approve → construct Effect → stage → validate --------------
def test_full_reversible_write_loop_stages_a_draft_never_sends(tmp_path):
    proposer = ReversibleWriteProposer()
    proposal = proposer.propose_draft_reply(
        to="bob@example.com", subject="re: meeting", request="meeting", mirror=_authored_mirror()
    )
    params = dict(proposal.params)

    lg = EffectLedger(tmp_path / "effects.sqlite")
    rec = lg.propose(proposal.actuator, ReversibilityClass.REVERSIBLE, scope="draft:reply",
                     params=params, rationale=proposal.rationale)
    rec = lg.approve(rec.id, strength=ApprovalStrength.LIGHT)     # approval-light: a one-tap ack

    # The approval makes a REVERSIBLE Effect constructable (the type inherits the proof it was
    # approved). This is the "code acts" side — distinct from the proposal above.
    effect = Effect(
        actuator=proposal.actuator,
        capability=ScopedCapability(scope="draft:reply"),
        reversibility=ReversibilityClass.REVERSIBLE,
        proposal_att="att-propose",
        approval_ref=ApprovalRef(approver="owner", strength=ApprovalStrength.LIGHT),
    )
    assert effect.reversibility is ReversibilityClass.REVERSIBLE

    effector = ReversibleWriteEffector(drafts_dir=tmp_path / "drafts", enabled=True)
    ref = effector.stage(effect.actuator, params)
    rec = lg.mark_executed(rec.id, artifact_ref=ref)
    lg.mark_validated(rec.id)

    # What landed is a DRAFT envelope — never a sent artifact. The tailored body is there.
    staged = effector.read(ref)
    assert staged is not None   # just staged this exact ref
    assert staged["actuator"] == "draft_reply"
    assert staged["params"]["to"] == "bob@example.com"
    assert "body" in staged["params"]
    assert (tmp_path / "drafts" / f"{ref}.draft").exists()
    # The effector has no send path at all — staging is the whole (reversible) action.
    assert not hasattr(effector, "send")
    lg.close()


def test_rollback_removes_the_staged_draft(tmp_path):
    effector = ReversibleWriteEffector(drafts_dir=tmp_path / "drafts", enabled=True)
    ref = effector.stage("draft_reply", {"to": "a@b.c", "subject": "s", "body": "b"})
    assert effector.read(ref) is not None
    assert effector.rollback(ref) is True                 # undone
    assert effector.read(ref) is None
    assert effector.rollback(ref) is False                # idempotent: already gone


def test_effector_off_by_default_and_refuses_unstageable(tmp_path):
    off = ReversibleWriteEffector(drafts_dir=tmp_path / "drafts")    # enabled defaults False
    with pytest.raises(EffectorsDisabled):
        off.stage("draft_reply", {"to": "a", "subject": "b", "body": "c"})
    on = ReversibleWriteEffector(drafts_dir=tmp_path / "drafts", enabled=True)
    with pytest.raises(NotStageableError):
        on.stage("send_email", {"to": "a", "subject": "b", "body": "c"})   # not stageable


def test_no_param_can_direct_the_on_disk_write(tmp_path):
    # A stage_file whose NAME is a traversal string still lands as one file inside drafts_dir — the
    # on-disk name is the effector's ref, and the requested name rides inside the envelope as data.
    drafts = tmp_path / "drafts"
    effector = ReversibleWriteEffector(drafts_dir=drafts, enabled=True)
    ref = effector.stage("stage_file", {"name": "../../../etc/authorized_keys", "content": "pwn"})
    staged_files = list(drafts.glob("*.draft"))
    assert staged_files == [drafts / f"{ref}.draft"]                  # exactly one file, in drafts
    assert not (tmp_path.parent / "etc" / "authorized_keys").exists()
    staged = effector.read(ref)
    assert staged is not None   # just staged this exact ref
    assert staged["params"]["name"] == "../../../etc/authorized_keys"  # kept as data
    # A malicious REF is refused outright (the second traversal guard).
    with pytest.raises(ValueError):
        effector._path_for("../../evil")
