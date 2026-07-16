"""The report generator's load-bearing invariants (bp-044 Item 9 + Item 10 appendix).

Falsifier (plan §7 Item 9, the whole-plan falsifier): a figure renders without its key (provenance
lost); OR `report.md` and `report.json` disagree on a value; OR the renderer mutates a store /
calls a model; OR two builds over the same stores diverge (non-determinism).
"""

from __future__ import annotations

import json

from core.stores.runledger import RunLedger
from core.stores.telemetry import TelemetryStore
from eval.harness.report import (
    FigureKind,
    build_report,
    render_json,
    render_markdown,
    write_report,
)
from eval.harness.store import EvalKey, EvalResultsStore, Reading


def _key(spec: str, *, seed: int = 0, corpus: str = "corpusX", cfg: str = "cfgX") -> EvalKey:
    return EvalKey(spec_hash=spec, corpus_ref=corpus, config_fingerprint=cfg, seed=seed)


def _close(*closeables: object) -> None:
    for c in closeables:
        c.close()  # type: ignore[attr-defined]  # each fixture store exposes .close()


def _fixture_eval_store() -> EvalResultsStore:
    store = EvalResultsStore(":memory:")
    # a registered metric with several points → a real curve
    for s in range(4):
        store.put(Reading(_key("specA", seed=s), "golden_recall", 0.80 + 0.02 * s, "Inv",
                          evidence_ref=f"att:gr{s}"))
    # drift_D (registered; the drift study owns it, excluded from curves)
    for s in range(3):
        store.put(Reading(_key("specA", seed=s), "drift_D", 0.10 + 0.01 * s, "Inv",
                          evidence_ref="att:drift"))
    # structural_axes.* (UNREGISTERED — finding-0086; read WITHOUT registry.get)
    store.put(Reading(_key("specB"), "structural_axes.beta0", 3.0, "Inv"))
    store.put(Reading(_key("specB", seed=1), "structural_axes.beta0", 4.0, "Inv"))
    store.put(Reading(_key("specB"), "structural_axes.n_communities", 5.0, "Inv"))
    return store


def _fixture_ledger() -> tuple[RunLedger, str]:
    ledger = RunLedger(":memory:")
    r7 = ledger.start_run(pipeline="phase7", config_fingerprint="cfgX", corpus_digest="corpusX",
                          node_count=10, edge_count=12, duration_s=1.5,
                          spectral_stats={"sigma": 0.6})
    ledger.add_claim(r7, kind="community", confidence=0.0, support=("a", "b"),
                     surface_text="a community", polarity="+")
    rv2 = ledger.start_run(pipeline="dream_v2", config_fingerprint="cfgX", corpus_digest="corpusX",
                           node_count=10, edge_count=12, duration_s=2.5,
                           spectral_stats={"sigma": 0.6})
    ledger.add_claim(rv2, kind="tension", confidence=0.7, support=("c", "d"),
                     surface_text="a tension", polarity="-")
    ledger.add_claim(rv2, kind="community", confidence=0.5, support=("a", "b"),
                     surface_text="a community", polarity="+")   # NOT novel (seen in r7)
    return ledger, r7


def _build(tmp_path):
    eval_store = _fixture_eval_store()
    ledger, r7 = _fixture_ledger()
    telem = TelemetryStore(tmp_path / "t.duckdb")
    telem.writer().record_harness_cost(r7, wall_clock_s=3.5, models_resident=1,
                                       cells_completed=8, cells_skipped=1, note="fixture")
    report = build_report("sigma-ab", "2026-07-16", eval_store=eval_store, run_ledger=ledger,
                          telemetry=telem.reader())
    return report, eval_store, ledger, telem


def test_every_figure_carries_a_nonempty_key(tmp_path) -> None:
    report, eval_store, ledger, telem = _build(tmp_path)
    try:
        assert report.figures                                   # non-empty
        for fig in report.figures:
            assert fig.key.spec_hash != ""                      # provenance present
            assert fig.key.corpus_ref != ""
            assert isinstance(fig.key, EvalKey)
    finally:
        _close(eval_store, ledger, telem)


def test_markdown_and_json_carry_the_same_figures_and_keys(tmp_path) -> None:
    report, eval_store, ledger, telem = _build(tmp_path)
    try:
        md = render_markdown(report)
        js = render_json(report)
        parsed = json.loads(js)
        assert len(parsed["figures"]) == len(report.figures)
        for fig in report.figures:
            # title + full key appear in BOTH renderings → they cannot disagree on a figure/key
            assert fig.title in md
            assert fig.key.spec_hash in md
            assert fig.key.spec_hash in js
            match = [f for f in parsed["figures"] if f["title"] == fig.title]
            assert len(match) == 1
            assert match[0]["key"]["spec_hash"] == fig.key.spec_hash
            assert match[0]["key"]["corpus_ref"] == fig.key.corpus_ref
    finally:
        _close(eval_store, ledger, telem)


def test_ab_table_splits_phase7_and_dream_v2(tmp_path) -> None:
    report, eval_store, ledger, telem = _build(tmp_path)
    try:
        ab = [f for f in report.figures if f.kind == FigureKind.AB]
        assert len(ab) == 1
        pipelines = {row["pipeline"]: row for row in ab[0].payload["pipelines"]}
        assert set(pipelines) == {"phase7", "dream_v2"}
        assert pipelines["phase7"]["claims"] == 1
        assert pipelines["dream_v2"]["claims"] == 2
        assert pipelines["dream_v2"]["novel"] == 1               # the tension; the re-emit isn't
        md = render_markdown(report)
        assert "phase7" in md and "dream_v2" in md
    finally:
        _close(eval_store, ledger, telem)


def test_drift_study_decomposes_structural_axes_without_registry(tmp_path) -> None:
    report, eval_store, ledger, telem = _build(tmp_path)
    try:
        drift = [f for f in report.figures if f.kind == FigureKind.DRIFT]
        assert len(drift) == 1
        axes = {ax["axis"] for ax in drift[0].payload["axes"]}
        assert axes == {"beta0", "n_communities"}               # unregistered family, read directly
        assert drift[0].payload["D"]["points"]                  # drift_D trajectory present
    finally:
        _close(eval_store, ledger, telem)


def test_cost_appendix_reports_the_ledger_totals(tmp_path) -> None:
    report, eval_store, ledger, telem = _build(tmp_path)
    try:
        cost = [f for f in report.figures if f.kind == FigureKind.COST]
        assert len(cost) == 1
        assert cost[0].payload["totals"]["cells_completed"] == 8
        assert cost[0].payload["totals"]["cells_skipped"] == 1
    finally:
        _close(eval_store, ledger, telem)


def test_rerender_is_byte_identical_determinism(tmp_path) -> None:
    """Two independent builds over the SAME stores render byte-identically (the determinism leg of
    the whole-plan falsifier)."""
    eval_store = _fixture_eval_store()
    ledger, r7 = _fixture_ledger()
    telem = TelemetryStore(tmp_path / "t.duckdb")
    telem.writer().record_harness_cost(r7, wall_clock_s=3.5, models_resident=1,
                                       cells_completed=8, cells_skipped=1)
    try:
        a = build_report("t", "2026-07-16", eval_store=eval_store, run_ledger=ledger,
                         telemetry=telem.reader())
        b = build_report("t", "2026-07-16", eval_store=eval_store, run_ledger=ledger,
                         telemetry=telem.reader())
        assert render_markdown(a) == render_markdown(b)
        assert render_json(a) == render_json(b)
    finally:
        _close(eval_store, ledger, telem)


def test_build_report_does_not_mutate_the_stores(tmp_path) -> None:
    """READ-ONLY: the row counts are unchanged after a build (the renderer never writes a store)."""
    report, eval_store, ledger, telem = _build(tmp_path)
    try:
        before = len(eval_store.query())
        build_report("again", "2026-07-16", eval_store=eval_store, run_ledger=ledger,
                     telemetry=telem.reader())
        assert len(eval_store.query()) == before
        assert telem.reader().harness_cost_count() == 1
    finally:
        _close(eval_store, ledger, telem)


def test_write_report_emits_both_files_into_dated_topic_dir(tmp_path) -> None:
    report, eval_store, ledger, telem = _build(tmp_path)
    try:
        out = write_report(report, root=tmp_path / "reports")
        assert out.name == "2026-07-16-sigma-ab"
        assert (out / "report.md").exists()
        assert (out / "report.json").exists()
        # the written JSON round-trips and matches the in-memory rendering
        assert (out / "report.json").read_text(encoding="utf-8") == render_json(report)
    finally:
        _close(eval_store, ledger, telem)
