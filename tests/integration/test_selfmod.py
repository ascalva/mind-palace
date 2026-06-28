"""The self-modification loop end to end (BUILD-SPEC §14, §18 Phase-10 gate; Invariant 5).

This file IS the Phase-10 verification the spec calls for:
  * a proposed change traverses the gate (propose→approve→execute→validate, kept);
  * a deliberately-bad change auto-rolls-back (the knob is restored, no residue);
  * the frozen anchor catches slow drift the rolling baseline misses (boiling-frog);
  * the master switch and the unattended switch are both fail-closed by default.
"""

from __future__ import annotations

import dataclasses

import pytest

from config.loader import get_config
from ops.apply import read_overlay
from ops.ledger import IllegalTransition, LedgerStatus, ProposalLedger
from ops.levers import ProposedChange
from ops.selfmod import (
    NotASafeLever,
    SelfModDisabled,
    SelfModLoop,
    UnattendedDisabled,
    ValidationResult,
)

# --- stub validators (inject deterministic gate decisions, per the eval.golden Retriever idiom)
GOOD = lambda lever, value: ValidationResult(True, True, {"v": value})            # noqa: E731
BAD_CAPABILITY = lambda lever, value: ValidationResult(False, True, {"v": value})  # noqa: E731
# Boiling-frog: passes the adapting rolling check (drift ok) yet fails the FROZEN golden anchor.
FROZEN_CATCHES = lambda lever, value: ValidationResult(False, True, {"v": value})  # noqa: E731


def _cfg(*, enabled=True, unattended=False):
    cfg = get_config()
    return dataclasses.replace(
        cfg,
        selfmod=dataclasses.replace(
            cfg.selfmod, enabled=enabled, unattended_enabled=unattended
        ),
    )


def _loop(tmp_path, validator=GOOD, *, enabled=True, unattended=False) -> SelfModLoop:
    return SelfModLoop(
        config=_cfg(enabled=enabled, unattended=unattended),
        ledger=ProposalLedger(tmp_path / "ledger.sqlite"),
        validator=validator,
        overlay_path=tmp_path / "levers.toml",
    )


def _change(target=0.66):
    return ProposedChange(lever="dream_similarity_threshold", target=target, rationale="tighten")


# --- fail-closed switches --------------------------------------------------------------------
def test_master_switch_off_refuses_to_propose(tmp_path):
    loop = _loop(tmp_path, enabled=False)
    with pytest.raises(SelfModDisabled):
        loop.propose(_change())


def test_out_of_bounds_proposal_never_reaches_the_ledger(tmp_path):
    loop = _loop(tmp_path)
    with pytest.raises(ValueError):
        loop.propose(_change(target=0.95))     # outside [0.55, 0.75]
    assert loop.ledger.all() == []


# --- the happy path: a good change traverses and is kept -------------------------------------
def test_good_change_traverses_the_gate_and_is_kept(tmp_path):
    loop = _loop(tmp_path, GOOD)
    p = loop.propose(_change(), proposer="watchdog")
    assert p.status is LedgerStatus.PROPOSED and p.current_value == 0.62

    loop.approve(p.id, approver="owner")
    final = loop.execute_and_validate(p.id)

    assert final.status is LedgerStatus.VALIDATED
    # the knob is live in the machine-owned overlay
    assert read_overlay(tmp_path / "levers.toml") == {"dreaming": {"similarity_threshold": 0.66}}


def test_execute_requires_approval(tmp_path):
    loop = _loop(tmp_path, GOOD)
    p = loop.propose(_change())
    with pytest.raises(IllegalTransition):
        loop.execute(p.id)                      # not approved → the ledger refuses


# --- the safety property: a bad change rolls back automatically ------------------------------
def test_bad_change_auto_rolls_back_and_restores_the_knob(tmp_path):
    loop = _loop(tmp_path, BAD_CAPABILITY)
    p = loop.propose(_change())
    loop.approve(p.id)
    final = loop.execute_and_validate(p.id)

    assert final.status is LedgerStatus.ROLLED_BACK
    assert "golden" in final.rollback_reason
    # the overlay is back to its prior state — the loop introduced the key, so rollback removed it
    assert read_overlay(tmp_path / "levers.toml") == {}


def test_rollback_restores_a_prior_overlay_value_not_just_absence(tmp_path):
    # First change is kept (sets 0.66); a second, bad change must restore to 0.66, not remove it.
    loop = _loop(tmp_path, GOOD)
    p1 = loop.propose(_change(0.66))
    loop.approve(p1.id)
    loop.execute_and_validate(p1.id)

    loop.validator = BAD_CAPABILITY
    p2 = loop.propose(_change(0.70))
    loop.approve(p2.id)
    final = loop.execute_and_validate(p2.id)

    assert final.status is LedgerStatus.ROLLED_BACK
    assert read_overlay(tmp_path / "levers.toml") == {"dreaming": {"similarity_threshold": 0.66}}


def test_frozen_anchor_catches_drift_the_rolling_baseline_misses(tmp_path):
    # Boiling-frog (§15): the validator reports drift_within_tolerance=True (the adapting rolling
    # check is happy) but golden_non_regressing=False (the FROZEN anchor caught cumulative drift).
    # The gate must still deny → rollback, and the reason must cite the frozen anchor, not drift.
    loop = _loop(tmp_path, FROZEN_CATCHES)
    p = loop.propose(_change())
    loop.approve(p.id)
    final = loop.execute_and_validate(p.id)

    assert final.status is LedgerStatus.ROLLED_BACK
    assert "frozen anchor" in final.rollback_reason
    assert "drift" not in final.rollback_reason     # rolling passed; only the frozen anchor fired


# --- the unattended safe-lever path is OFF by default ----------------------------------------
def test_unattended_path_refused_by_default(tmp_path):
    loop = _loop(tmp_path, GOOD, unattended=False)        # default
    with pytest.raises(UnattendedDisabled):
        loop.apply_unattended(ProposedChange(lever="dream_max_clusters", target=6))


def test_unattended_on_applies_a_safe_lever_without_a_human(tmp_path):
    loop = _loop(tmp_path, GOOD, unattended=True)
    final = loop.apply_unattended(ProposedChange(lever="dream_max_clusters", target=6))
    assert final.status is LedgerStatus.VALIDATED
    assert final.approver == "unattended"                 # auditable: no human signed off
    assert read_overlay(tmp_path / "levers.toml") == {"dreaming": {"max_clusters": 6}}


def test_unattended_refuses_a_non_safe_lever_even_when_enabled(tmp_path):
    loop = _loop(tmp_path, GOOD, unattended=True)
    with pytest.raises(NotASafeLever):
        loop.apply_unattended(_change())                  # similarity_threshold is not safe-listed


# --- the DEFAULT validator wired to the real frozen golden anchor (not a stub) ---------------
def _stub_retriever(hits_by_query):
    return lambda query, k: hits_by_query.get(query, [])


def test_default_validator_passes_when_capability_is_unharmed():
    # A retriever that returns each golden query's expected title scores at/above the frozen
    # baseline → golden_non_regressing True. (A dreaming-knob change doesn't touch retrieval, so
    # this "no capability harm" result is the correct real-world signal for our shipped levers.)
    from eval.golden import load_golden_set
    from ops.levers import LEVERS
    from ops.selfmod import build_golden_validator

    golden = load_golden_set()
    hits = {gq.query: [{"title": t} for t in gq.expected] for gq in golden}
    validator = build_golden_validator(_stub_retriever(hits))
    result = validator(LEVERS["dream_similarity_threshold"], 0.66)
    assert result.golden_non_regressing is True
    assert result.metrics["frozen_regressions"] == []


def test_default_validator_flags_a_real_capability_regression():
    from ops.levers import LEVERS
    from ops.selfmod import build_golden_validator

    validator = build_golden_validator(_stub_retriever({}))   # retrieves nothing → recall drops
    result = validator(LEVERS["dream_similarity_threshold"], 0.66)
    assert result.golden_non_regressing is False
    assert "recall_at_k" in result.metrics["frozen_regressions"]
