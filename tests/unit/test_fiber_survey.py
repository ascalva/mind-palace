"""Smoke + honesty guard for the fiber-geometry survey (bp-085 / `dn-fiber-geometry` §2.6).

NOT a corpus assertion — the survey's numbers are a findings artifact (finding-0142), not a
test oracle. These tests prove the machinery: the survey runs on a small in-memory fixture with
NO live store and NO embedder, every reading carries its CN-1 index tuple + grid (the battery's
own falsifier — a reading without its index is malformed), and the D data-integrity check fires
on a planted triangle. Read-only throughout.
"""

from __future__ import annotations

from pathlib import Path
from typing import cast

import numpy as np
import pytest

from eval.harness.fiber_survey import (
    SurveyContext,
    SurveyIndex,
    m3_triangles,
    run_survey,
)
from eval.harness.re_measure import sim_edges_from_embeddings

_GRID = (0.55, 0.65, 0.75)
_PATHS = ["docs/x/a.md", "docs/x/b.md", "docs/x/c.md", "docs/x/d.md"]


def _fixture_ctx(
    *, c_pairs: list[tuple[str, str]] | None = None,
    d_arcs: list[tuple[str, str]] | None = None,
    d_authored: list[tuple[str, str]] | None = None,
) -> SurveyContext:
    """A tiny, deterministic context — four docs with near-basis embeddings, one F pair, one C
    pair, a short D chain. No store, no embedder: `run_survey(ctx=...)` bypasses `load_context`."""
    rng = np.eye(4) * 0.9 + 0.1
    emb = {p: list(rng[i]) for i, p in enumerate(_PATHS)}
    s_edges = sim_edges_from_embeddings(emb, node_ids=_PATHS, sigma_floor=min(_GRID))
    return SurveyContext(
        head="deadbeef", grid=_GRID, repo_root=Path("/fixture"),
        s_embeddings=emb, s_edges=s_edges,
        f_pairs=[("docs/x/a.md", "docs/x/b.md")],
        c_pairs=c_pairs if c_pairs is not None else [("docs/x/a.md", "docs/x/c.md")],
        c_ids=["a", "b", "c", "d"], unresolved_c=[],
        d_arcs=d_arcs if d_arcs is not None else [("d0", "d1"), ("d1", "d2")],
        d_authored=d_authored if d_authored is not None else [],
        d_doc_count=1, d_version_count=3,
    )


def test_survey_runs_on_fixture_no_store_no_embedder() -> None:
    readings = run_survey(ctx=_fixture_ctx())
    rows = [r.row for r in readings]
    assert rows == ["M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8"]


def test_every_reading_carries_its_cn1_index_and_grid() -> None:
    """The battery falsifier: a reading without its index tuple + grid is malformed."""
    for r in run_survey(ctx=_fixture_ctx()):
        assert isinstance(r.index, SurveyIndex), f"{r.row} has no CN-1 index"
        assert r.index.grid == _GRID, f"{r.row} dropped its grid"
        assert r.index.sigma in _GRID, f"{r.row} σ={r.index.sigma} is not a declared grid point"
        assert r.index.head == "deadbeef" and r.index.coordinate, f"{r.row} index incomplete"
        assert r.status in {
            "measured", "expected-null", "disjoint-population", "deferred",
            "instrument-blocked", "data-integrity-violation",
        }, f"{r.row} has an unknown status {r.status!r}"


def test_m1_reports_four_populations_and_pairwise_overlap() -> None:
    (m1,) = [r for r in run_survey(ctx=_fixture_ctx()) if r.row == "M1"]
    pops = cast("dict[str, object]", m1.value["populations"])
    assert set(pops) == {"S", "F", "D", "C"}
    # all six unordered class pairs are present in the Jaccard table.
    assert len(cast("dict[str, object]", m1.value["node_jaccard"])) == 6


def test_m3_d_triangle_is_zero_on_a_covering_chain() -> None:
    """A linear D chain (covering-only) has no triangle — the integrity check passes, no
    violation reading is appended."""
    readings = run_survey(ctx=_fixture_ctx())
    assert not any(r.row == "M3-D-INTEGRITY" for r in readings)
    (m3,) = [r for r in readings if r.row == "M3"]
    assert cast("dict[str, object]", m3.value["D_triangles"])["count"] == 0
    assert m3.status == "measured"


def test_m3_planted_d_triangle_raises_integrity_violation() -> None:
    """A nonzero D-triangle is a real corpus defect (§10 stop-and-raise), surfaced as a distinct
    data-integrity-violation reading — never swallowed."""
    ctx = _fixture_ctx(d_arcs=[("d0", "d1"), ("d1", "d2"), ("d0", "d2")])  # a filled triangle
    _m3, violation = m3_triangles(ctx)
    assert violation is not None
    assert violation.status == "data-integrity-violation"
    assert cast("int", violation.value["d_triangles"]) >= 1
    assert violation.index.grid == _GRID


def test_m2_e_dws_given_d_is_disjoint_not_zero() -> None:
    """D indexes a disjoint node space — E[Δw_S | D-event] is recorded expected-null by
    disjointness, never as a measured zero (silence must not be narrated as structure)."""
    (m2,) = [r for r in run_survey(ctx=_fixture_ctx()) if r.row == "M2"]
    assert cast("dict[str, object]", m2.value["E_dwS_given_D"])["status"] == "disjoint-population"


def test_embedder_deferral_defers_S_rows_and_still_measures_recorded_classes() -> None:
    """When eval-side embedding is unreachable (memory-ceiling'd ollama contention, bright line 8),
    the S (computed) rows DEFER with a re-entry reason — never a measured zero — while F/D/C
    (recorded) rows still compute. Graceful degradation, not a whole-survey failure."""
    ctx = _fixture_ctx()
    # simulate the embedder trip: no embeddings, no S edges, a deferral reason recorded.
    object.__setattr__(ctx, "s_embeddings", {})
    object.__setattr__(ctx, "s_edges", [])
    object.__setattr__(ctx, "embedder_status", "deferred: embedder unreachable (test)")
    readings = {r.row: r for r in run_survey(ctx=ctx)}
    # S-dependent rows defer, carrying the reason (and still their CN-1 index).
    for row in ("M2", "M4", "M5", "M8"):
        assert readings[row].status == "deferred", f"{row} did not defer"
        assert "embedder" in readings[row].reason.lower()
        assert isinstance(readings[row].index, SurveyIndex)
    # M3 still runs the recorded-class triangle census; the D-integrity check is unaffected.
    assert readings["M3"].value["D_triangles"]["count"] == 0  # type: ignore[index]
    assert readings["M3"].value["F_triangles"]["count"] is not None  # type: ignore[index]
    # M6 (D thermometer, recorded) still measures.
    assert readings["M6"].status == "measured"


@pytest.mark.parametrize("row", ["M6", "M8"])
def test_null_rows_declare_a_reason(row: str) -> None:
    """Every non-measured sub-result names why (expected-null/deferred/blocked/disjoint) — a null
    is a result with a reason, never bare absence."""
    (reading,) = [r for r in run_survey(ctx=_fixture_ctx()) if r.row == row]
    blob = str(reading.value) + reading.reason
    assert any(tag in blob for tag in ("deferred", "instrument-blocked", "disjoint", "expected"))
