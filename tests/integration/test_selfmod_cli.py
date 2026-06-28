"""Operator gate CLI (ops/selfmod_cli.py). Exercises the command functions directly with a temp
ledger + stub validator — the live-embedder `approve` path is covered by the golden-live e2e."""

from __future__ import annotations

import dataclasses

from config.loader import get_config
from ops.ledger import LedgerStatus, ProposalLedger
from ops.selfmod import SelfModLoop, ValidationResult
from ops.selfmod_cli import (
    cmd_approve,
    cmd_deny,
    cmd_history,
    cmd_list,
    cmd_propose,
    cmd_show,
)

GOOD = lambda lever, value: ValidationResult(True, True, {"v": value})        # noqa: E731
BAD = lambda lever, value: ValidationResult(False, True, {"v": value})        # noqa: E731


def _loop(tmp_path, validator=GOOD):
    cfg = get_config()
    cfg = dataclasses.replace(cfg, selfmod=dataclasses.replace(cfg.selfmod, enabled=True))
    return SelfModLoop(
        config=cfg,
        ledger=ProposalLedger(tmp_path / "ledger.sqlite"),
        validator=validator,
        overlay_path=tmp_path / "levers.toml",
    )


def test_propose_list_show_history(tmp_path):
    loop = _loop(tmp_path)
    out = cmd_propose(loop, "dream_similarity_threshold", 0.66, "tighten themes")
    assert "proposed #1" in out and "0.62 -> 0.66" in out

    assert "tighten themes" in cmd_list(loop.ledger)
    assert "#1 [proposed]" in cmd_show(loop.ledger, 1)
    assert "no proposal #9" in cmd_show(loop.ledger, 9)
    assert "#1" in cmd_history(loop.ledger)


def test_empty_states(tmp_path):
    loop = _loop(tmp_path)
    assert cmd_list(loop.ledger) == "no pending proposals."
    assert cmd_history(loop.ledger) == "no proposals yet."


def test_deny(tmp_path):
    loop = _loop(tmp_path)
    cmd_propose(loop, "dream_max_clusters", 6, "")
    assert "denied #1" in cmd_deny(loop, 1)
    assert loop.ledger.get(1).status is LedgerStatus.DENIED
    assert cmd_list(loop.ledger) == "no pending proposals."


def test_approve_keeps_a_good_change(tmp_path):
    loop = _loop(tmp_path, GOOD)
    cmd_propose(loop, "dream_similarity_threshold", 0.66, "")
    out = cmd_approve(loop, 1)
    assert "approved + kept #1" in out
    assert loop.ledger.get(1).status is LedgerStatus.VALIDATED


def test_approve_reports_auto_rollback_for_a_bad_change(tmp_path):
    loop = _loop(tmp_path, BAD)
    cmd_propose(loop, "dream_similarity_threshold", 0.70, "")
    out = cmd_approve(loop, 1)
    assert "AUTO-ROLLED-BACK #1" in out
    assert loop.ledger.get(1).status is LedgerStatus.ROLLED_BACK
