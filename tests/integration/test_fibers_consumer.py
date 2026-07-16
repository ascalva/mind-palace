"""The σ-fibers consumer end-to-end (bp-050 Item 1) — the reconstruction + per-claim scoring +
aggregate write, over a run ledger the REAL sweep produced and over a hand-planted ledger with
known persistences.

Acceptance killers (plan §7 Item 1):
  * over a 3-cell sweep the consumer JOINS ALL cells (a claim that survives every σ reads pers=1.0
    over the full grid), computes pers per planted claim, and writes EXACTLY the five aggregate
    readings ONCE per pipeline;
  * a RE-RUN writes ZERO new rows (the store dedups by key — the consumer never re-keys);
  * a registry-state mismatch (simulated) REFUSES with the §2.4.1 message.

Falsifiers actively defeated:
  * re-key/overwrite — a pre-seeded reading at the consumer's key is SKIPPED (put() returns False),
    its value untouched;
  * reconstruction under a changed registry — an `expected_registry_hash` mismatch refuses;
  * per-claim data read from the eval store — the planted-ledger test starts with an EMPTY eval
    store and still computes correct per-claim fibers (claims live ONLY in the run ledger);
  * mixed corpus_digest across cells — refused (a σ/corpus-growth confound, §8/§10).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from config.loader import get_config
from core.complex.temporal import SnapshotStore
from core.dreaming.shadow import _config_fingerprint
from core.provenance import Provenance
from core.stores.runledger import RunLedger, claim_id, polarity_for
from eval.drift import DriftConfig
from eval.golden import GoldenQuery
from eval.harness.fibers import (
    MixedCorpusError,
    RegistryStateMismatch,
    _modify_config,
    fibers_spec_hash,
    lever_registry_hash,
    run_fibers,
)
from eval.harness.store import EvalKey, EvalResultsStore, Reading
from eval.harness.sweep import SweepEngine, parse_spec_text
from ops.levers import get_lever

# Two ISOLATED tight pairs (cos 0.99, in orthogonal subspaces) + an outlier. Isolation matters: a
# bridge would merge a pair into a bigger component at low σ, morphing the claim's IDENTITY across
# cells (the §2.3 caveat). With no bridge each pair's community claim keeps ONE identity across the
# whole [0.55, 0.75] range, so it persists on ALL grid cells (pers = 1.0) — the "joins all cells"
# probe. Cross-pair cosine is 0 (out of range), so nothing merges.
_C = 0.99
_S = (1.0 - _C * _C) ** 0.5   # sqrt(1 - 0.99²) ≈ 0.141


def _row(digest: str, title: str, vec: list[float]) -> dict[str, Any]:
    return {"digest": digest, "title": title, "provenance": "authored-solo", "vector": vec}


ROWS: list[dict[str, Any]] = [
    _row("dP1", "P1", [1.0, 0.0, 0.0, 0.0, 0.0]),
    _row("dP2", "P2", [_C, _S, 0.0, 0.0, 0.0]),
    _row("dQ1", "Q1", [0.0, 0.0, 1.0, 0.0, 0.0]),
    _row("dQ2", "Q2", [0.0, 0.0, _C, _S, 0.0]),
    _row("dZ1", "Z1", [0.0, 0.0, 0.0, 0.0, 1.0]),
]

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


class _RowSource:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows

    def all_rows(self, *, provenances: Any = None) -> list[dict[str, Any]]:
        if provenances is None:
            return list(self._rows)
        allowed = {Provenance(p).value for p in provenances}
        return [r for r in self._rows if r.get("provenance") in allowed]


def _fake_retriever(query: str, k: int) -> list[dict[str, Any]]:
    return [{"title": "A1", "_distance": 0.1}, {"title": "B1", "_distance": 0.2}][:k]


def _drive_three_cell_sweep() -> tuple[RunLedger, EvalResultsStore, list[float]]:
    """Drive the REAL `ShadowRunner` over a 3-point σ grid (both pipelines) → a run ledger + eval
    store exactly as an overnight sweep leaves them. Returns them plus the grid."""
    spec = parse_spec_text(_SPEC_3PT)
    ledger = RunLedger(":memory:")
    eval_store = EvalResultsStore(":memory:")
    engine = SweepEngine(
        spec=spec,
        base_config=get_config(),
        eval_store=eval_store,
        ledger=ledger,
        store=_RowSource(ROWS),
        retriever=_fake_retriever,
        golden=[GoldenQuery(id="q1", query="alpha", expected=frozenset({"A1"}), k=2)],
        baseline={"recall_at_k": 0.5, "overlap": 0.4, "mean_distance": 0.2},
        drift_cfg=DriftConfig(),
        snapshots=SnapshotStore(Path(":memory:")),
    )
    engine.drive()
    return ledger, eval_store, [float(v) for v in spec.grid()]


def test_consumer_joins_all_cells_and_writes_five_per_pipeline_once() -> None:
    ledger, eval_store, grid = _drive_three_cell_sweep()
    lever = get_lever("dream_rnd_sigma")

    result = run_fibers(ledger=ledger, eval_store=eval_store, base_config=get_config(),
                        lever=lever, grid=grid)

    # Both pipelines joined and produced claims.
    assert set(result.fibers) == {"phase7", "dream_v2"}
    # JOINS ALL CELLS: a tight cluster survives the whole σ-range → a claim on all 3 grid cells.
    phase7 = result.fibers["phase7"]
    full_span = [f for f in phase7 if f.n_cells == len(grid)]
    assert full_span, "a persistent community claim must span all 3 joined cells"
    assert full_span[0].pers == pytest.approx(1.0)
    assert full_span[0].sigma_min == pytest.approx(min(grid))
    assert full_span[0].sigma_max == pytest.approx(max(grid))

    # EXACTLY five aggregate readings per pipeline, written ONCE (10 total for two pipelines).
    assert result.readings_written == 10
    for pipeline in ("phase7", "dream_v2"):
        spec_hash = fibers_spec_hash(pipeline, lever, grid)
        rows = [r for r in eval_store.query() if r.key.spec_hash == spec_hash]
        assert len(rows) == 5
        assert {r.metric_name for r in rows} == {
            "sigma_persistence.mean", "sigma_persistence.p50", "sigma_persistence.max",
            "sigma_persistence.frac_ge_strong", "sigma_persistence.n_claims",
        }
        # keyed per §6: base config_fingerprint, seed=0, shared corpus_ref, Res(sigma).
        base_fp = _config_fingerprint(get_config())
        for r in rows:
            assert r.key.config_fingerprint == base_fp
            assert r.key.seed == 0
            assert r.key.corpus_ref == result.corpus_ref
            assert r.type_tag == "Res(sigma)"


def test_rerun_writes_zero_new_rows() -> None:
    ledger, eval_store, grid = _drive_three_cell_sweep()
    lever = get_lever("dream_rnd_sigma")
    kwargs: dict[str, Any] = dict(ledger=ledger, eval_store=eval_store,
                                  base_config=get_config(), lever=lever, grid=grid)

    first = run_fibers(**kwargs)
    assert first.readings_written == 10
    before = len(eval_store.query())

    second = run_fibers(**kwargs)            # same stores, same grid → every put() skips
    assert second.readings_written == 0, "a re-run writes ZERO new rows (the store dedups by key)"
    assert len(eval_store.query()) == before


def _planted_ledger(grid: list[float]) -> tuple[RunLedger, dict[str, str]]:
    """A hand-planted single-pipeline ledger with KNOWN persistences over `grid` (m=3):
      α present at cells {0,1,2} → pers 1.0 (no gap);
      β present at cells {0,2}   → pers 2/3 (GAP);
      γ present at cell  {0}     → pers 1/3.
    The eval store never sees a claim — claims live ONLY here (§2.4.2)."""
    base = get_config()
    lever = get_lever("dream_rnd_sigma")
    ledger = RunLedger(":memory:")
    fps = [_config_fingerprint(_modify_config(base, lever, s)) for s in grid]
    cell_claims: dict[int, list[tuple[str, str]]] = {  # (kind, support-tuple key)
        0: [("community", "a"), ("community", "b"), ("community", "g")],
        1: [("community", "a")],
        2: [("community", "a"), ("community", "b")],
    }
    supports = {"a": ("d1", "d2"), "b": ("d3", "d4"), "g": ("d5", "d6")}
    for i, fp in enumerate(fps):
        run_id = ledger.start_run(pipeline="dream_v2", config_fingerprint=fp,
                                  corpus_digest="corpusX", node_count=6, edge_count=3,
                                  duration_s=0.0, spectral_stats={})
        for kind, key in cell_claims[i]:
            ledger.add_claim(run_id, kind=kind, confidence=0.5, support=supports[key],
                             surface_text=f"{key}@{i}", polarity=polarity_for(kind))
    ids = {key: claim_id("community", tuple(sorted(supports[key])), "+") for key in supports}
    return ledger, ids


def test_pers_per_planted_claim_and_exact_aggregates() -> None:
    grid = [0.55, 0.65, 0.75]
    ledger, ids = _planted_ledger(grid)
    eval_store = EvalResultsStore(":memory:")          # EMPTY — claims come from the LEDGER only
    lever = get_lever("dream_rnd_sigma")

    result = run_fibers(ledger=ledger, eval_store=eval_store, base_config=get_config(),
                        lever=lever, grid=grid)

    fibers = {f.claim_id: f for f in result.fibers["dream_v2"]}
    assert fibers[ids["a"]].pers == pytest.approx(1.0)
    assert fibers[ids["a"]].gap is False and fibers[ids["a"]].n_cells == 3
    assert fibers[ids["b"]].pers == pytest.approx(2 / 3)
    assert fibers[ids["b"]].gap is True and fibers[ids["b"]].n_cells == 2   # a hole at cell 1
    assert fibers[ids["b"]].sigma_min == pytest.approx(0.55)
    assert fibers[ids["b"]].sigma_max == pytest.approx(0.75)
    assert fibers[ids["g"]].pers == pytest.approx(1 / 3)

    agg = result.aggregates["dream_v2"]
    assert agg["sigma_persistence.mean"] == pytest.approx((1.0 + 2 / 3 + 1 / 3) / 3)
    assert agg["sigma_persistence.p50"] == pytest.approx(2 / 3)     # median of {1/3, 2/3, 1.0}
    assert agg["sigma_persistence.max"] == pytest.approx(1.0)
    assert agg["sigma_persistence.frac_ge_strong"] == pytest.approx(2 / 3)  # α,β ≥ 0.5; γ < 0.5
    assert agg["sigma_persistence.n_claims"] == pytest.approx(3.0)
    assert result.readings_written == 5                # single pipeline → exactly five


def test_never_overwrites_a_present_reading() -> None:
    """Falsifier: the consumer must never overwrite an existing reading. A pre-seeded reading at
    the consumer's own key is SKIPPED (put() returns False), its value untouched."""
    grid = [0.55, 0.65, 0.75]
    ledger, _ = _planted_ledger(grid)
    eval_store = EvalResultsStore(":memory:")
    lever = get_lever("dream_rnd_sigma")
    base_fp = _config_fingerprint(get_config())
    spec_hash = fibers_spec_hash("dream_v2", lever, grid)
    key = EvalKey(spec_hash=spec_hash, corpus_ref="corpusX", config_fingerprint=base_fp, seed=0)
    # A DIFFERENT value pre-seeded at the mean's key — the consumer must not clobber it.
    eval_store.put(Reading(key=key, metric_name="sigma_persistence.mean", value=-999.0,
                           type_tag="Res(sigma)"))

    result = run_fibers(ledger=ledger, eval_store=eval_store, base_config=get_config(),
                        lever=lever, grid=grid)

    assert result.readings_written == 4, "the pre-seeded cell is skipped, not overwritten"
    got = eval_store.get(key, "sigma_persistence.mean")
    assert got is not None and got.value == -999.0, "an existing reading is NEVER overwritten"


def test_registry_state_mismatch_refuses() -> None:
    """§2.4.1 / §10: reconstruction across lever-registry versions is refused fail-closed."""
    grid = [0.55, 0.65, 0.75]
    ledger, _ = _planted_ledger(grid)
    lever = get_lever("dream_rnd_sigma")
    with pytest.raises(RegistryStateMismatch, match="registry"):
        run_fibers(ledger=ledger, eval_store=EvalResultsStore(":memory:"),
                   base_config=get_config(), lever=lever, grid=grid,
                   expected_registry_hash="0" * 64)
    # and the happy path: the live hash matches itself → no refusal.
    ok = run_fibers(ledger=ledger, eval_store=EvalResultsStore(":memory:"),
                    base_config=get_config(), lever=lever, grid=grid,
                    expected_registry_hash=lever_registry_hash())
    assert ok.readings_written == 5


def test_mixed_corpus_digest_refuses() -> None:
    """§8 validity / §10: joined cells spanning >1 corpus_digest confound σ with corpus growth."""
    grid = [0.55, 0.65, 0.75]
    base = get_config()
    lever = get_lever("dream_rnd_sigma")
    ledger = RunLedger(":memory:")
    for i, s in enumerate(grid):
        fp = _config_fingerprint(_modify_config(base, lever, s))
        run_id = ledger.start_run(pipeline="dream_v2", config_fingerprint=fp,
                                  corpus_digest=f"corpus{i}",   # DIFFERENT digest per cell
                                  node_count=6, edge_count=3, duration_s=0.0, spectral_stats={})
        ledger.add_claim(run_id, kind="community", confidence=0.5, support=("d1", "d2"),
                         surface_text="x", polarity="+")
    with pytest.raises(MixedCorpusError, match="corpus_digest"):
        run_fibers(ledger=ledger, eval_store=EvalResultsStore(":memory:"),
                   base_config=base, lever=lever, grid=grid)
