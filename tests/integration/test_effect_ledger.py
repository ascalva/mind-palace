"""The durable effect ledger — the §14 lifecycle for hands (Track G, item G5).

The effector twin of `ProposalLedger`, reusing the same §14 FSM (`ops.ledger.LedgerStatus`). These
pin: the kept and undone paths; that every transition fail-closes on its exact precondition (no step
skipped, I5); and the load-bearing new invariant — an approval recorded for a class must COVER w(β)
for that class, so a LIGHT ack can never approve an irreversible effect.
"""

from __future__ import annotations

import pytest

from ops.effect_ledger import EffectLedger
from ops.effects import ApprovalStrength, ReversibilityClass
from ops.ledger import IllegalTransition, LedgerStatus


def _ledger(tmp_path) -> EffectLedger:
    return EffectLedger(tmp_path / "effects.sqlite")


def test_reversible_write_kept_lifecycle(tmp_path):
    lg = _ledger(tmp_path)
    rec = lg.propose("draft_reply", ReversibilityClass.REVERSIBLE, scope="draft:reply",
                     params={"to": "bob@example.com"}, proposer="ambassador")
    assert rec.status is LedgerStatus.PROPOSED and rec.params == {"to": "bob@example.com"}

    rec = lg.approve(rec.id, strength=ApprovalStrength.LIGHT)
    assert rec.status is LedgerStatus.APPROVED
    assert rec.approval_strength is ApprovalStrength.LIGHT and rec.approver == "owner"

    rec = lg.mark_executed(rec.id, artifact_ref="draft-abc")
    assert rec.status is LedgerStatus.EXECUTED and rec.artifact_ref == "draft-abc"

    rec = lg.mark_validated(rec.id)
    assert rec.status is LedgerStatus.VALIDATED and rec.resolved_at
    lg.close()


def test_reversible_write_rolled_back(tmp_path):
    lg = _ledger(tmp_path)
    rec = lg.propose("stage_file", ReversibilityClass.REVERSIBLE)
    rec = lg.approve(rec.id, strength=ApprovalStrength.LIGHT)
    rec = lg.mark_executed(rec.id, artifact_ref="draft-xyz")
    rec = lg.mark_rolled_back(rec.id, reason="owner deleted draft")
    assert rec.status is LedgerStatus.ROLLED_BACK and rec.rollback_reason == "owner deleted draft"
    lg.close()


def test_light_approval_cannot_cover_an_irreversible_effect(tmp_path):
    # The load-bearing invariant: w(β) selects the approval weight. An IRREVERSIBLE effect needs the
    # FULL gate; a LIGHT ack is refused (fail-closed), the same rule Effect.__post_init__ enforces,
    # checked here so the ledger never holds an under-approved record.
    lg = _ledger(tmp_path)
    rec = lg.propose("send_email", ReversibilityClass.IRREVERSIBLE, scope="send:email")
    with pytest.raises(IllegalTransition):
        lg.approve(rec.id, strength=ApprovalStrength.LIGHT)
    with pytest.raises(IllegalTransition):
        lg.approve(rec.id, strength=ApprovalStrength.NONE)
    rec = lg.approve(rec.id, strength=ApprovalStrength.FULL_GATE)   # only FULL covers
    assert rec.status is LedgerStatus.APPROVED
    lg.close()


def test_reversible_needs_at_least_light(tmp_path):
    # A REVERSIBLE effect needs LIGHT; a NONE "approval" (no human act) does not cover it.
    lg = _ledger(tmp_path)
    rec = lg.propose("draft_reply", ReversibilityClass.REVERSIBLE)
    with pytest.raises(IllegalTransition):
        lg.approve(rec.id, strength=ApprovalStrength.NONE)
    lg.close()


def test_no_step_may_be_skipped(tmp_path):
    lg = _ledger(tmp_path)
    rec = lg.propose("draft_reply", ReversibilityClass.REVERSIBLE)
    # Cannot execute something unapproved.
    with pytest.raises(IllegalTransition):
        lg.mark_executed(rec.id, artifact_ref="x")
    # Cannot validate something unexecuted.
    lg.approve(rec.id, strength=ApprovalStrength.LIGHT)
    with pytest.raises(IllegalTransition):
        lg.mark_validated(rec.id)
    lg.close()


def test_denied_is_terminal(tmp_path):
    lg = _ledger(tmp_path)
    rec = lg.propose("draft_reply", ReversibilityClass.REVERSIBLE)
    rec = lg.deny(rec.id)
    assert rec.status is LedgerStatus.DENIED
    # No successor from a terminal state.
    with pytest.raises(IllegalTransition):
        lg.approve(rec.id, strength=ApprovalStrength.LIGHT)
    with pytest.raises(IllegalTransition):
        lg.mark_executed(rec.id, artifact_ref="x")
    lg.close()


def test_pending_and_attestation_link(tmp_path):
    lg = _ledger(tmp_path)
    a = lg.propose("draft_reply", ReversibilityClass.REVERSIBLE)
    lg.propose("calendar_hold", ReversibilityClass.REVERSIBLE)
    assert {r.actuator for r in lg.pending()} == {"draft_reply", "calendar_hold"}
    lg.attach_attestation(a.id, "att-123")
    rec = lg.get(a.id)
    assert rec is not None and rec.attestation_id == "att-123"   # just proposed this exact id
    lg.close()
