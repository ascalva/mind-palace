"""The sweep engine end-to-end (bp-049, Items 13 + 14) — the real `ShadowRunner` driven over an
in-memory eval store + run ledger, with the golden-fixture retriever injected.

Acceptance killers (plan §7/§14):
  * a 3-point × 1-seed sweep drives 3 DISTINCT cells — 3 distinct `config_fingerprint`s (the bp-046
    property; a collision would flatten the curve and skip every cell after the first as a resume);
  * a re-run of the SAME sweep writes ZERO new eval rows (resumability is the store's guarantee —
    the engine never re-keys);
  * an out-of-bounds grid point raises via `lever.validate` BEFORE any run (no cell is driven);
  * `mode = "auto"` raises a clear 'E3b' error; an unregistered objective raises fail-closed;
  * with `[selfmod] enabled`, a completed sweep lands EXACTLY ONE PROPOSED ledger row whose `target`
    is the selected value and whose `rationale` names the evidence keys — PROPOSED only, nothing
    auto-approved/executed;
  * with selfmod disabled, ZERO ledger rows + a recorded selection.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import Any

import pytest

from config.loader import get_config
from core.complex.temporal import SnapshotStore
from core.provenance import Provenance
from core.stores.runledger import RunLedger
from eval.drift import DriftConfig
from eval.golden import GoldenQuery
from eval.harness.store import EvalResultsStore
from eval.harness.sweep import SweepEngine, SweepSpecError, parse_spec_text, run_sweep
from ops.ledger import LedgerStatus, ProposalLedger
from ops.selfmod import SelfModLoop, ValidationResult

# Same planted shape the shadow-runner tests use (two clusters + bridge + outlier).
ROWS = [
    {"digest": "dA1", "title": "A1", "provenance": "authored-solo", "vector": [1.0, 0.0, 0.0]},
    {"digest": "dA2", "title": "A2", "provenance": "authored-solo", "vector": [0.97, 0.03, 0.0]},
    {"digest": "dB1", "title": "B1", "provenance": "authored-solo", "vector": [0.0, 1.0, 0.0]},
    {"digest": "dB2", "title": "B2", "provenance": "authored-solo", "vector": [0.0, 0.97, 0.03]},
    {"digest": "dG1", "title": "G1", "provenance": "authored-solo", "vector": [0.7, 0.7, 0.0]},
    {"digest": "dZ1", "title": "Z1", "provenance": "authored-solo", "vector": [0.0, 0.0, 1.0]},
]


class _RowSource:
    def __init__(self, rows: list[dict[str, Any]]):
        self._rows = rows

    def all_rows(self, *, provenances: Any = None) -> list[dict[str, Any]]:
        if provenances is None:
            return list(self._rows)
        allowed = {Provenance(p).value for p in provenances}
        return [r for r in self._rows if r.get("provenance") in allowed]


def _fake_retriever(query: str, k: int) -> list[dict[str, Any]]:
    return [{"title": "A1", "_distance": 0.1}, {"title": "B1", "_distance": 0.2}][:k]


_SPEC_3PT = """
[sweep.demo]
levers = { dream_rnd_sigma = "full" }
resolution = 3
pipelines = ["phase7", "dream_v2"]
corpus = "mirror-snapshot"
seeds = 1
metrics = ["golden_recall", "drift_D"]
objective = "golden_recall"
mode = "propose"
"""


def _engine(eval_store: EvalResultsStore, ledger: RunLedger, spec_text: str = _SPEC_3PT,
            baseline_recall: float = 0.5) -> SweepEngine:
    spec = parse_spec_text(spec_text)
    return SweepEngine(
        spec=spec,
        base_config=get_config(),
        eval_store=eval_store,
        ledger=ledger,
        store=_RowSource(ROWS),
        retriever=_fake_retriever,
        golden=[GoldenQuery(id="q1", query="alpha", expected=frozenset({"A1"}), k=2)],
        baseline={"recall_at_k": baseline_recall, "overlap": 0.4, "mean_distance": 0.2},
        drift_cfg=DriftConfig(),
        snapshots=SnapshotStore(Path(":memory:")),
    )


def test_three_point_sweep_drives_three_distinct_cells() -> None:
    eval_store = EvalResultsStore(":memory:")
    engine = _engine(eval_store, RunLedger(":memory:"))
    engine.drive()

    recall = eval_store.query(metric_name="golden_recall")
    fps = {r.key.config_fingerprint for r in recall}
    assert len(fps) == 3, "3 σ cells -> 3 distinct config_fingerprints (the bp-046 property)"


def test_rerun_writes_zero_new_eval_rows() -> None:
    eval_store = EvalResultsStore(":memory:")
    ledger = RunLedger(":memory:")
    engine = _engine(eval_store, ledger)
    engine.drive()
    after_first = len(eval_store.query())
    assert after_first > 0

    engine.drive()  # same spec, same shared stores -> every put() skips (resume)
    assert len(eval_store.query()) == after_first, "a re-run writes ZERO new eval rows (resume)"


def test_out_of_bounds_grid_point_raises_before_any_run() -> None:
    bad = _SPEC_3PT.replace('{ dream_rnd_sigma = "full" }',
                            "{ dream_rnd_sigma = [0.55, 0.60, 0.99] }")  # 0.99 > hi
    eval_store = EvalResultsStore(":memory:")
    engine = _engine(eval_store, RunLedger(":memory:"), spec_text=bad)
    with pytest.raises(ValueError, match="outside hard bounds"):
        engine.drive()
    assert eval_store.query() == [], "no cell was driven — the grid is validated before any run"


def test_mode_auto_raises_e3b() -> None:
    with pytest.raises(SweepSpecError, match="E3b"):
        parse_spec_text(_SPEC_3PT.replace('mode = "propose"', 'mode = "auto"'))


def test_unregistered_objective_fails_closed() -> None:
    with pytest.raises(SweepSpecError, match="not a registered metric"):
        parse_spec_text(_SPEC_3PT.replace('objective = "golden_recall"', 'objective = "bogus"'))


def _enabled_loop(ledger: ProposalLedger, *, enabled: bool) -> SelfModLoop:
    cfg = get_config()
    cfg = dataclasses.replace(cfg, selfmod=dataclasses.replace(cfg.selfmod, enabled=enabled))

    def _validator(lever: Any, value: float) -> ValidationResult:  # never called by propose
        return ValidationResult(golden_non_regressing=True, drift_within_tolerance=True)

    return SelfModLoop(config=cfg, ledger=ledger, validator=_validator)


def test_selfmod_enabled_lands_exactly_one_proposed_row() -> None:
    eval_store = EvalResultsStore(":memory:")
    prop_ledger = ProposalLedger(Path(":memory:"))
    loop = _enabled_loop(prop_ledger, enabled=True)
    engine = _engine(eval_store, RunLedger(":memory:"))
    drive = engine.drive()
    result = engine.optimize(drive, selfmod_loop=loop)

    assert result.selected is not None
    assert result.proposal_emitted is True

    rows = prop_ledger.all()
    assert len(rows) == 1, "exactly ONE proposal row"
    (row,) = rows
    # PROPOSED only — nothing auto-approved/executed.
    assert row.status is LedgerStatus.PROPOSED
    assert row.approver is None
    assert row.executed_at is None and row.resolved_at is None
    # target is the selected value; the rationale names the evidence keys.
    assert row.target_value == float(result.selected)
    assert row.lever == "dream_rnd_sigma"
    assert "evidence[" in row.rationale and result.evidence_keys[0] in row.rationale
    # the selected value is a grid point in bounds (ProposedChange.resolve would else have raised).
    assert result.selected in result.grid
    assert engine.spec.lever.lo <= float(result.selected) <= engine.spec.lever.hi


def test_selfmod_disabled_emits_nothing_but_records_selection() -> None:
    eval_store = EvalResultsStore(":memory:")
    prop_ledger = ProposalLedger(Path(":memory:"))
    loop = _enabled_loop(prop_ledger, enabled=False)
    engine = _engine(eval_store, RunLedger(":memory:"))
    drive = engine.drive()
    result = engine.optimize(drive, selfmod_loop=loop)

    assert result.selected is not None, "a selection is still recorded"
    assert result.proposal_emitted is False
    assert result.proposal_id is None
    assert prop_ledger.all() == [], "ZERO ledger rows when selfmod is disabled"
    assert any("selfmod disabled" in n for n in result.notes)


def test_run_sweep_one_call_entry_matches_engine() -> None:
    """The `run_sweep` convenience does drive+optimize in one call (the script's entry)."""
    eval_store = EvalResultsStore(":memory:")
    result = run_sweep(
        parse_spec_text(_SPEC_3PT),
        base_config=get_config(),
        eval_store=eval_store,
        ledger=RunLedger(":memory:"),
        store=_RowSource(ROWS),
        retriever=_fake_retriever,
        golden=[GoldenQuery(id="q1", query="alpha", expected=frozenset({"A1"}), k=2)],
        baseline={"recall_at_k": 0.5, "overlap": 0.4, "mean_distance": 0.2},
        drift_cfg=DriftConfig(),
        snapshots=SnapshotStore(Path(":memory:")),
        selfmod_loop=None,
    )
    assert result.selected in result.grid
    assert result.guardrails_captured is True
