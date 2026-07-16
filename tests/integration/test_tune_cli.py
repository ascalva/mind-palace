"""The tuning control surface `scripts/tune.py` (bp-047 Item 16) driven against an in-memory ledger
+ stub validator + tmp overlay (the test_selfmod.py idiom).

Proves the attended contract and its falsifiers: `set` PROPOSES only (never auto-approves, never
writes the overlay before approval); an EXECUTED change `--revert`s to ROLLED_BACK and restores the
prior overlay; a VALIDATED (kept) proposal is NOT mutated by `--revert`; an out-of-bounds `set`
fails closed before any ledger row; `show` works with `[selfmod] enabled = false`.
"""

from __future__ import annotations

import dataclasses

import pytest

from config.loader import get_config
from eval.harness.tuning import load_manifest
from ops.apply import read_overlay
from ops.ledger import LedgerStatus, Proposal, ProposalLedger
from ops.levers import ProposedChange
from ops.selfmod import SelfModDisabled, SelfModLoop, ValidationResult
from scripts.tune import cmd_history, cmd_revert, cmd_set, cmd_show, main

GOOD = lambda lever, value: ValidationResult(True, True, {"v": value})   # noqa: E731


def _get(loop: SelfModLoop, pid: int) -> Proposal:
    """Fetch a row that must exist (narrows `Proposal | None` for the assertions below)."""
    p = loop.ledger.get(pid)
    assert p is not None
    return p


def _cfg(*, enabled=True):
    cfg = get_config()
    return dataclasses.replace(cfg, selfmod=dataclasses.replace(cfg.selfmod, enabled=enabled))


def _loop(tmp_path, validator=GOOD, *, enabled=True) -> SelfModLoop:
    return SelfModLoop(
        config=_cfg(enabled=enabled),
        ledger=ProposalLedger(tmp_path / "ledger.sqlite"),
        validator=validator,
        overlay_path=tmp_path / "levers.toml",
    )


# --- set PROPOSES only (no auto-approve, no overlay write) ------------------------------------
def test_set_yields_a_proposed_row_and_never_approves(tmp_path):
    loop = _loop(tmp_path)
    out = cmd_set(loop, "dream_similarity_threshold", 0.66, "tighten themes")
    assert "proposed #1" in out and "awaits OWNER APPROVAL" in out

    p = _get(loop, 1)
    assert p.status is LedgerStatus.PROPOSED   # falsifier: the CLI must NOT approve its own row
    assert p.status is not LedgerStatus.APPROVED
    assert p.approver is None
    # falsifier: `set` must NOT write the overlay before approval
    assert read_overlay(tmp_path / "levers.toml") == {}


def test_set_out_of_bounds_fails_closed_before_any_ledger_write(tmp_path):
    loop = _loop(tmp_path)
    with pytest.raises(ValueError):
        cmd_set(loop, "dream_similarity_threshold", 0.95, "")   # outside [0.55, 0.75]
    assert loop.ledger.all() == []


def test_set_requires_selfmod_enabled(tmp_path):
    loop = _loop(tmp_path, enabled=False)
    with pytest.raises(SelfModDisabled):
        cmd_set(loop, "dream_similarity_threshold", 0.66, "")


# --- history renders the proposal ------------------------------------------------------------
def test_history_shows_a_proposed_change(tmp_path):
    loop = _loop(tmp_path)
    assert cmd_history(loop.ledger) == "no proposals yet."
    cmd_set(loop, "dream_similarity_threshold", 0.66, "tighten")
    hist = cmd_history(loop.ledger)
    assert "#1 [proposed]" in hist and "tighten" in hist


# --- revert an EXECUTED change → ROLLED_BACK + prior overlay restored -------------------------
def test_revert_an_executed_change_restores_absence(tmp_path):
    loop = _loop(tmp_path)
    p = loop.propose(ProposedChange(lever="dream_similarity_threshold", target=0.66))
    loop.approve(p.id, approver="owner")
    loop.execute(p.id)   # left EXECUTED (not yet validated)
    assert read_overlay(tmp_path / "levers.toml") == {"dreaming": {"similarity_threshold": 0.66}}

    out = cmd_revert(loop, p.id)
    assert "reverted #1" in out and "ROLLED_BACK" in out
    assert _get(loop, p.id).status is LedgerStatus.ROLLED_BACK
    # the loop introduced the key, so revert removes it — prior overlay restored exactly
    assert read_overlay(tmp_path / "levers.toml") == {}


def test_revert_restores_a_prior_value_not_just_absence(tmp_path):
    loop = _loop(tmp_path)
    # a first change is kept at 0.66
    p1 = loop.propose(ProposedChange(lever="dream_similarity_threshold", target=0.66))
    loop.approve(p1.id)
    loop.execute_and_validate(p1.id)   # VALIDATED
    # a second change is executed (not yet validated), then reverted → must restore 0.66
    p2 = loop.propose(ProposedChange(lever="dream_similarity_threshold", target=0.70))
    loop.approve(p2.id)
    loop.execute(p2.id)
    assert read_overlay(tmp_path / "levers.toml") == {"dreaming": {"similarity_threshold": 0.70}}

    cmd_revert(loop, p2.id)
    assert _get(loop, p2.id).status is LedgerStatus.ROLLED_BACK
    assert read_overlay(tmp_path / "levers.toml") == {"dreaming": {"similarity_threshold": 0.66}}


def test_revert_refuses_to_mutate_a_validated_proposal(tmp_path):
    loop = _loop(tmp_path, GOOD)
    p = loop.propose(ProposedChange(lever="dream_similarity_threshold", target=0.66))
    loop.approve(p.id)
    loop.execute_and_validate(p.id)
    assert _get(loop, p.id).status is LedgerStatus.VALIDATED

    out = cmd_revert(loop, p.id)
    assert "cannot be reverted" in out and "inverse" in out.lower()
    # falsifier: the VALIDATED status must NOT change (illegal transition)
    assert _get(loop, p.id).status is LedgerStatus.VALIDATED
    # and the kept overlay value is untouched
    assert read_overlay(tmp_path / "levers.toml") == {"dreaming": {"similarity_threshold": 0.66}}


def test_revert_of_a_missing_proposal_is_reported(tmp_path):
    loop = _loop(tmp_path)
    assert "no proposal #9" in cmd_revert(loop, 9)


def test_revert_of_a_proposed_change_refuses(tmp_path):
    loop = _loop(tmp_path)
    p = loop.propose(ProposedChange(lever="dream_similarity_threshold", target=0.66))
    out = cmd_revert(loop, p.id)
    assert "only an EXECUTED proposal" in out
    assert _get(loop, p.id).status is LedgerStatus.PROPOSED


# --- show is read-only and works with the loop disabled --------------------------------------
def test_show_works_with_selfmod_disabled(tmp_path):
    out = cmd_show(_cfg(enabled=False), load_manifest())
    for name in ("dream_similarity_threshold", "dream_max_clusters"):
        assert name in out
    assert "autonomy=propose" in out and "bounds=" in out


def test_show_reports_the_live_value_not_a_manifest_value(tmp_path):
    cfg = _cfg(enabled=True)
    out = cmd_show(cfg, load_manifest())
    # the live σ from the config chain (default 0.62), proving `show` reads _section_value, not TOML
    live = cfg.dreaming.similarity_threshold
    assert f"dream_similarity_threshold: {live:g}" in out


# --- the argv entrypoint (read-only `show`) --------------------------------------------------
def test_main_show_returns_zero(capsys):
    assert main(["show"]) == 0
    assert "dream_similarity_threshold" in capsys.readouterr().out


def test_main_no_command_is_usage_error(capsys):
    assert main([]) == 2
