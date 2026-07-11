"""The durable propose→approve→execute→validate→rollback ledger (BUILD-SPEC §14; Invariant 5).

The FSM tests prove the §14 ordering "no step skipped" is enforced by the store, not merely by
the orchestrator on top of it: you cannot execute the un-approved or validate the un-executed.
"""

from __future__ import annotations

import pytest

from ops.ledger import IllegalTransition, LedgerStatus, Proposal, ProposalLedger


def _ledger(tmp_path) -> ProposalLedger:
    return ProposalLedger(tmp_path / "ledger.sqlite")


def _propose(led: ProposalLedger):
    return led.propose("dream_similarity_threshold", 0.62, 0.66, rationale="tighten themes")


def _get(led: ProposalLedger, proposal_id: int) -> Proposal:
    """`led.get(id)`, narrowed: both call sites look up a proposal this same test just proposed
    (`ProposalLedger.get`'s honest `Proposal | None` covers an unknown id — a shape neither
    call site here produces)."""
    p = led.get(proposal_id)
    assert p is not None
    return p


def test_propose_creates_a_pending_row(tmp_path):
    led = _ledger(tmp_path)
    p = _propose(led)
    assert p.id == 1 and p.status is LedgerStatus.PROPOSED
    assert p.current_value == 0.62 and p.target_value == 0.66
    assert led.pending() == [p]


def test_happy_path_propose_approve_execute_validate(tmp_path):
    led = _ledger(tmp_path)
    p = _propose(led)
    led.approve(p.id, approver="owner")
    led.mark_executed(p.id, prior_overlay=None)
    final = led.mark_validated(p.id, metrics={"after": {"recall_at_k": 1.0}})
    assert final.status is LedgerStatus.VALIDATED
    assert final.approver == "owner"
    assert final.metrics == {"after": {"recall_at_k": 1.0}}
    assert led.pending() == []


def test_cannot_execute_without_approval(tmp_path):
    led = _ledger(tmp_path)
    p = _propose(led)
    with pytest.raises(IllegalTransition, match="not approved|is proposed"):
        led.mark_executed(p.id, prior_overlay=None)


def test_cannot_validate_without_execute(tmp_path):
    led = _ledger(tmp_path)
    p = _propose(led)
    led.approve(p.id)
    with pytest.raises(IllegalTransition):
        led.mark_validated(p.id)


def test_denied_is_terminal(tmp_path):
    led = _ledger(tmp_path)
    p = _propose(led)
    led.deny(p.id)
    assert _get(led, p.id).status is LedgerStatus.DENIED
    with pytest.raises(IllegalTransition):
        led.approve(p.id)        # cannot resurrect a denied proposal


def test_validated_is_terminal(tmp_path):
    led = _ledger(tmp_path)
    p = _propose(led)
    led.approve(p.id)
    led.mark_executed(p.id, prior_overlay=0.62)
    led.mark_validated(p.id)
    with pytest.raises(IllegalTransition):
        led.mark_rolled_back(p.id, reason="too late")


def test_rollback_records_reason_and_keeps_prior_overlay(tmp_path):
    led = _ledger(tmp_path)
    p = _propose(led)
    led.approve(p.id)
    led.mark_executed(p.id, prior_overlay=0.62)
    rb = led.mark_rolled_back(p.id, reason="golden-set regressed vs frozen anchor")
    assert rb.status is LedgerStatus.ROLLED_BACK
    assert rb.rollback_reason == "golden-set regressed vs frozen anchor"
    assert rb.prior_overlay == 0.62


def test_prior_overlay_none_means_absent(tmp_path):
    led = _ledger(tmp_path)
    p = _propose(led)
    led.approve(p.id)
    executed = led.mark_executed(p.id, prior_overlay=None)
    assert executed.prior_overlay is None   # NULL distinguishes "loop introduced the key"


def test_durable_across_reopen(tmp_path):
    db = tmp_path / "ledger.sqlite"
    led = ProposalLedger(db)
    p = _propose(led)
    led.approve(p.id)
    led.close()
    reopened = ProposalLedger(db)
    again = _get(reopened, p.id)
    assert again.status is LedgerStatus.APPROVED and again.target_value == 0.66
