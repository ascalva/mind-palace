"""The OpsView read-only introspection scope (Track B / B3) — an integrity-tier invariant.

The Ambassador may *read* the audit layer to narrate it, never *write* it. These assert the
read-only surface (no mutator is an attribute of the view — `approve`/`deny`/`append`/`mark_*`
are unreachable through it) and that the plain-language narration leaks no internal nouns
(tier names, "job"/"queue", credentials/accessors/signatures) per the authoritative note §4.
"""

from pathlib import Path

from core.attestation.attestor import StoreAttestor
from core.attestation.store import AttestationStore
from core.ops_view import OpsView
from ops.ledger import ProposalLedger

# Names that would mean the view can mutate the audit/gate/ledger layer — must NOT be present.
_FORBIDDEN = (
    "approve", "deny", "append", "mark_executed", "mark_validated", "mark_rolled_back",
    "propose", "attach_attestation", "tombstone", "delete", "add",
)


def _wired():
    store = AttestationStore(Path(":memory:"))
    att = StoreAttestor(store)
    att.emit(agent_role="ambassador", action="capture", input_hashes=["d1"], output_hashes=["d1"])
    att.emit(agent_role="ambassador", action="read", input_hashes=["d1"])
    ledger = ProposalLedger(Path(":memory:"))
    return OpsView.over(store, ledger), store, ledger


def test_ops_view_exposes_only_reads():
    view, _store, _ledger = _wired()
    public = {n for n in dir(view) if not n.startswith("_")}
    leaked = public & set(_FORBIDDEN)
    assert leaked == set(), f"OpsView exposes a mutator: {leaked}"
    # And the mutators are genuinely not attributes (can't be called through the view).
    for name in _FORBIDDEN:
        assert not hasattr(view, name), f"OpsView has reachable mutator {name!r}"


def test_ops_view_reads_reflect_the_stores():
    view, _store, ledger = _wired()
    assert view.attestation_count() == 2
    roles_actions = {(r, a) for r, a, _ts in view.recent_actions()}
    assert ("ambassador", "capture") in roles_actions
    assert view.pending_proposals() == []          # nothing proposed yet
    ledger.propose("decay_rate", 0.9, 0.8, rationale="test")
    assert len(view.pending_proposals()) == 1      # the read is live


def test_narrate_is_plain_language_no_internal_nouns():
    view, _store, _ledger = _wired()
    text = view.narrate().lower()
    for leak in ("synthesis", "tier", "queue", "job", "token", "accessor", "signature",
                 "sqlite", "lancedb", "qwen", "attestation", "ledger"):
        assert leak not in text, f"status narration leaked internal noun {leak!r}: {text!r}"
    assert "logged" in text or "recorded" in text   # it does say what it's been doing


class _FakeDrift:
    def __init__(self, within, intact=True):
        self.within_tolerance = within
        self.constitution_intact = intact


def test_narrate_reflects_drift_health():
    store, ledger = AttestationStore(Path(":memory:")), ProposalLedger(Path(":memory:"))
    healthy = OpsView.over(store, ledger, drift=lambda: _FakeDrift(True))
    assert "healthy" in healthy.narrate().lower()

    drifting = OpsView.over(store, ledger, drift=lambda: _FakeDrift(False))
    assert "drift" in drifting.narrate().lower()

    breached = OpsView.over(store, ledger, drift=lambda: _FakeDrift(False, intact=False))
    assert "core" in breached.narrate().lower()

    unmeasured = OpsView.over(store, ledger, drift=None)
    assert "health" in unmeasured.narrate().lower()
