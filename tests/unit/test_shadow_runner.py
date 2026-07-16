"""The shadow runner — both pipelines, one snapshot; ledger + eval-store writes (bp-043 Item 6).

Acceptance (plan §7): a shadow run over a small fixture mirror writes exactly two `dream_runs`
(one per pipeline) sharing ONE `corpus_digest`, >=1 `dream_claims`, and keyed Readings in the eval
store for the registered guardrails + `structural_axes.*` (dream_v2 only), each carrying the run's
`corpus_digest`/`config_fingerprint`; the live derived store is unmodified and no `[dream_rnd]` disk
flag changed; a second run marks re-emitted claim_ids `novel=False` and skips already-present metric
cells (append-only-by-key).

Falsifier actively checked: two runs get the SAME corpus_digest; every Reading's key matches its
run's corpus_digest/config_fingerprint; model-free (no synthesizer wired — the model is never
called); the derived store row count is unchanged.
"""

from __future__ import annotations

import dataclasses
from typing import Any

from config.loader import get_config
from core.provenance import Provenance
from core.stores.runledger import RunLedger, claim_id, polarity_for
from eval.harness.store import EvalResultsStore

# The planted shape the R0/R1 + dream_v2 tests use (two clusters + a bridge + an outlier) so every
# lens fires deterministically and dream_v2 produces at least one adjudicated candidate.
ROWS = [
    {"digest": "dA1", "title": "A1", "provenance": "authored-solo", "vector": [1.0, 0.0, 0.0]},
    {"digest": "dA2", "title": "A2", "provenance": "authored-solo", "vector": [0.97, 0.03, 0.0]},
    {"digest": "dB1", "title": "B1", "provenance": "authored-solo", "vector": [0.0, 1.0, 0.0]},
    {"digest": "dB2", "title": "B2", "provenance": "authored-solo", "vector": [0.0, 0.97, 0.03]},
    {"digest": "dG1", "title": "G1", "provenance": "authored-solo", "vector": [0.7, 0.7, 0.0]},
    {"digest": "dZ1", "title": "Z1", "provenance": "authored-solo", "vector": [0.0, 0.0, 1.0]},
]


class _RowSource:
    """A MirrorView row source (the RowSource protocol). Authored-only so `MirrorView.project`
    accepts it."""

    def __init__(self, rows: list[dict[str, Any]]):
        self._rows = rows

    def all_rows(self, *, provenances: Any = None) -> list[dict[str, Any]]:
        if provenances is None:
            return list(self._rows)
        allowed = {Provenance(p).value for p in provenances}
        return [r for r in self._rows if r.get("provenance") in allowed]


def _fake_retriever(query: str, k: int) -> list[dict[str, Any]]:
    """A deterministic golden-fixture retriever stub — returns fixed rows so recall is stable and
    the guardrail readings are computed without a model."""
    return [{"title": "A1", "_distance": 0.1}, {"title": "B1", "_distance": 0.2}][:k]


def _runner(**overrides: Any):
    from pathlib import Path

    from core.complex.temporal import SnapshotStore
    from core.dreaming.shadow import ShadowRunner
    from eval.drift import DriftConfig
    from eval.golden import GoldenQuery

    ledger = overrides.pop("ledger", RunLedger(":memory:"))
    kwargs: dict[str, Any] = dict(
        ledger=ledger,
        store=_RowSource(ROWS),
        eval_store=EvalResultsStore(":memory:"),
        snapshots=SnapshotStore(Path(":memory:")),
        retriever=_fake_retriever,
        golden=[GoldenQuery(id="q1", query="alpha", expected=frozenset({"A1"}), k=2)],
        baseline={"recall_at_k": 0.5, "overlap": 0.4, "mean_distance": 0.2},
        drift_cfg=DriftConfig(),
    )
    kwargs.update(overrides)
    return ShadowRunner(**kwargs)


def test_two_runs_one_corpus_digest_and_claims() -> None:
    runner = _runner()
    run7, run_v2 = runner.run(config=get_config())

    runs = runner.ledger.runs()
    assert len(runs) == 2, "exactly one run per pipeline"
    pipelines = {r["pipeline"] for r in runs}
    assert pipelines == {"phase7", "dream_v2"}
    digests = {r["corpus_digest"] for r in runs}
    assert len(digests) == 1, "both pipelines scored ONE snapshot -> one corpus_digest (falsifier)"
    fingerprints = {r["config_fingerprint"] for r in runs}
    # STILL one fingerprint per run: both pipelines share ONE cfg. bp-046 widened the fingerprint's
    # BASIS (the [dreaming] four PLUS the registered [dream_rnd] levers), not its per-run count.
    assert len(fingerprints) == 1, "both pipelines share one cfg -> one config_fingerprint"

    assert len(runner.ledger.claims()) >= 1
    # phase7 emits community claims; dream_v2 emits adjudicated panel claims.
    assert runner.ledger.claims(run_id=run7)
    assert runner.ledger.claims(run_id=run_v2)


def test_eval_readings_keyed_to_the_run_and_structural_axes_dream_v2_only() -> None:
    runner = _runner()
    runner.run(config=get_config())
    store = runner.eval_store
    assert store is not None

    corpus_digest = runner.ledger.runs()[0]["corpus_digest"]
    config_fp = runner.ledger.runs()[0]["config_fingerprint"]

    # guardrails present for BOTH pipelines (distinct spec_hash), each keyed to this run.
    recall = store.query(metric_name="golden_recall")
    assert len(recall) == 2
    for r in recall:
        assert r.key.corpus_ref == corpus_digest and r.key.config_fingerprint == config_fp
    assert store.query(metric_name="drift_D")

    # structural_axes.* are dream_v2-only and correctly keyed.
    axes = [r for r in store.query() if r.metric_name.startswith("structural_axes.")]
    assert axes, "dream_v2 must write structural_axes.* (bp-045 A2 landed)"
    for r in axes:
        assert r.key.corpus_ref == corpus_digest and r.key.config_fingerprint == config_fp
    # every axis reading belongs to the dream_v2 spec_hash, never phase7.
    v2_specs = {r.key.spec_hash for r in axes}
    phase7_recall_specs = {
        r.key.spec_hash for r in recall
        if r.key.spec_hash not in v2_specs
    }
    assert phase7_recall_specs, "phase7 has guardrails but NO structural_axes"


def test_live_derived_store_unmodified_and_flag_unchanged(tmp_path) -> None:
    """The whole-plan falsifier: shadow writes NO interpreted/derived store, flips NO disk flag."""
    from core.stores.derived import open_derived_store

    cfg = get_config()
    paths = dataclasses.replace(cfg.paths, derived_store=tmp_path / "derived.sqlite")
    cfg = dataclasses.replace(cfg, paths=paths)

    derived = open_derived_store(cfg)
    before = len(derived.all())

    runner = _runner()
    runner.run(config=cfg)

    assert len(open_derived_store(cfg).all()) == before, "shadow must not write the derived store"
    # the on-disk flag is untouched (dream_v2 was enabled in-process via replace()).
    assert get_config().dream_rnd.enabled is False


def test_second_run_marks_reemits_not_novel_and_skips_present_cells() -> None:
    runner = _runner()
    runner.run(config=get_config())
    first_novel = len(runner.ledger.claims(novel_only=True))
    store = runner.eval_store
    assert store is not None
    cells_after_first = len(store.query())

    runner.run(config=get_config())     # same mirror -> same claim_ids, same keys
    # no NEW novel claims on the second pass (all claim_ids already seen).
    assert len(runner.ledger.claims(novel_only=True)) == first_novel
    # append-only-by-key: the metric cells are unchanged (put skipped every present cell).
    assert len(store.query()) == cells_after_first


def test_config_fingerprint_moves_with_registered_sigma_only() -> None:
    """bp-046 falsifier killers: the config_fingerprint MUST move when a REGISTERED lever
    (dream_rnd.sigma — what dream_v2 reads) changes, and MUST NOT move for an UNregistered
    [dream_rnd] knob (min_degree). If sigma collided, a σ-sweep would produce one flat point and
    skip every cell after the first as a resume (§4)."""
    from core.dreaming.shadow import _config_fingerprint

    base = get_config()

    # a REGISTERED lever changed -> the identity MUST move (the sweep-breaking bug this plan kills).
    sigma_a = dataclasses.replace(base, dream_rnd=dataclasses.replace(base.dream_rnd, sigma=0.60))
    sigma_b = dataclasses.replace(base, dream_rnd=dataclasses.replace(base.dream_rnd, sigma=0.62))
    assert _config_fingerprint(sigma_a) != _config_fingerprint(sigma_b)

    # an UNREGISTERED [dream_rnd] knob changed -> the identity MUST NOT move (only registered
    # levers count; min_degree is not a lever, so it stays out of the config identity).
    deg_a = dataclasses.replace(base, dream_rnd=dataclasses.replace(base.dream_rnd, min_degree=2))
    deg_b = dataclasses.replace(base, dream_rnd=dataclasses.replace(base.dream_rnd, min_degree=3))
    assert _config_fingerprint(deg_a) == _config_fingerprint(deg_b)


def test_claim_ids_are_content_addressed_from_support() -> None:
    """A ledger claim_id reproduces from (kind, support, polarity) — content-addressed, not
    surface-addressed."""
    runner = _runner()
    runner.run(config=get_config())
    for c in runner.ledger.claims():
        import json as _json
        support = tuple(_json.loads(c["support_json"]))
        expected = claim_id(c["kind"], support, polarity_for(c["kind"]))
        assert c["claim_id"] == expected
