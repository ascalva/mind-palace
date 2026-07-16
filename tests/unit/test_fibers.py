"""The σ-fibers metric — the exact-partition oracle + the §2.3 falsifier clauses (bp-050 Item 2).

The design note's persistence functional (§2.3) rests on §2.1 fact 3: every deterministic
computation over G_σ is piecewise-constant in σ, changing only when σ crosses one of the ≤ n(n−1)/2
distinct cosine entries. So `[σ_lo, σ_hi]` partitions into finitely many intervals on each of which
the emitted claim set is fixed — and the TRUE support measure `λ(Σ*(χ))` is exact, grid-free
(§2.4.5). This module builds that exact evaluator TEST-SIDE (parked SF-f: test-oracle only) and uses
it to falsify the consumer's grid estimator (`eval/harness/fibers.fiber_metrics`):

  * **(i) the degeneracy anchor** — a bare-edge claim's exact `pers` == the analytic value
    `clip((min(w, σ_hi) − σ_lo)/(σ_hi − σ_lo), 0, 1)`. The pipeline here is phase7 (=
    `community_interpreter`, `core/dreaming/shadow.py:154`): an isolated 2-note component is exactly
    the bare edge of §2.1, its σ-support the interval `{σ : σ ≤ w}`.
  * **(ii) the ruler test** — recomputing on the refined grid `Γ_{2m-1}` (which CONTAINS `Γ_m`)
    moves `pers(χ)` by no more than the bound `B·Δσ/(σ_hi−σ_lo)` (B=1 crossing here).
  * **(gap)** — a support set with a hole sets `gap=True` and `pers` counts CELLS, not the hull.

The falsifier (plan §7 Item 2): if the grid estimator disagrees with the exact oracle beyond the
stated bound, the computation is broken — STOP and fix before anything ships.
"""

from __future__ import annotations

import dataclasses
import math
from collections.abc import Callable
from typing import Any

import pytest

from config.loader import get_config
from core.dreaming.graph import MirrorGraph
from core.dreaming.interpreters import community_interpreter
from core.mirror import MirrorView
from core.provenance import Provenance
from core.stores.runledger import claim_id, polarity_for
from eval.harness.fibers import (
    STRONG_THRESHOLD,
    fiber_metrics,
    fibers_spec_hash,
    lever_registry_hash,
)
from ops.levers import get_lever

# The dream_rnd_sigma lever's hard bounds (ops/levers.py:112-122) — the swept σ range.
LO, HI = 0.55, 0.75


class _RowSource:
    """A MirrorView-admissible (authored-only) row source (the RowSource protocol)."""

    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows

    def all_rows(self, *, provenances: Any = None) -> list[dict[str, Any]]:
        if provenances is None:
            return list(self._rows)
        allowed = {Provenance(p).value for p in provenances}
        return [r for r in self._rows if r.get("provenance") in allowed]


def _bare_edge_rows(cos: float) -> list[dict[str, Any]]:
    """Three authored notes with exactly ONE pairwise cosine in range: u·v = `cos` (planted), and
    z orthogonal to both (cosine 0, out of range). The only phase7 community claim is the isolated
    2-note component {u, v} — the bare edge of §2.1."""
    y = math.sqrt(max(0.0, 1.0 - cos * cos))
    return [
        {"digest": "dU", "title": "U", "provenance": "authored-solo", "vector": [1.0, 0.0, 0.0]},
        {"digest": "dV", "title": "V", "provenance": "authored-solo", "vector": [cos, y, 0.0]},
        {"digest": "dZ", "title": "Z", "provenance": "authored-solo", "vector": [0.0, 0.0, 1.0]},
    ]


def _phase7_emitter(rows: list[dict[str, Any]]) -> tuple[MirrorGraph, Callable[[float], set[str]]]:
    """Build the mirror graph once (note centroids are σ-independent) and return an `emit(σ)` that
    reproduces the phase7 (community_interpreter) claim-id set at threshold σ — exactly the per-cell
    claim set the shadow runner would write to the ledger at that σ."""
    view = MirrorView.project(_RowSource(rows))
    graph = MirrorGraph.build(view, sigma=0.0)   # notes σ-independent; community re-clusters at σ
    base_rnd = get_config().dream_rnd

    def emit(sigma: float) -> set[str]:
        cfg = dataclasses.replace(base_rnd, sigma=sigma)
        return {
            claim_id(c.method, c.support, polarity_for(c.method))
            for c in community_interpreter(graph, cfg)
        }

    return graph, emit


def _distinct_breakpoints(sim: Any, lo: float, hi: float) -> list[float]:
    """The distinct cosine entries strictly inside (lo, hi) — the ≤ n(n−1)/2 breakpoints of the
    piecewise-constant filtration (§2.1 fact 3)."""
    n = int(sim.shape[0])
    vals: set[float] = set()
    for i in range(n):
        for j in range(i + 1, n):
            w = float(sim[i, j])
            if lo < w < hi:
                vals.add(w)
    return sorted(vals)


def _exact_pers(rows: list[dict[str, Any]], lo: float, hi: float) -> dict[str, float]:
    """The EXACT-partition oracle (§2.4.5): evaluate the deterministic pipeline once per equivalence
    interval between breakpoints and sum interval lengths where each claim is present → exact
    `λ(Σ*(χ))/(σ_hi−σ_lo)`, grid-free."""
    graph, emit = _phase7_emitter(rows)
    bps = [lo, *_distinct_breakpoints(graph.sim, lo, hi), hi]
    span = hi - lo
    length: dict[str, float] = {}
    for a, b in zip(bps, bps[1:], strict=False):   # consecutive breakpoints (one fewer pair)
        for cid in emit((a + b) / 2.0):   # a representative σ inside the open interval
            length[cid] = length.get(cid, 0.0) + (b - a)
    return {cid: lg / span for cid, lg in length.items()}


def _uniform_grid(lo: float, hi: float, m: int) -> list[float]:
    return [lo + (hi - lo) * i / (m - 1) for i in range(m)]


def _grid_pers(rows: list[dict[str, Any]], grid: list[float]) -> dict[str, float]:
    """The consumer's GRID estimator over one corpus: run the pipeline at each grid σ_i, group by
    claim id, and feed each support-index set through the SAME `fiber_metrics` the consumer uses."""
    _graph, emit = _phase7_emitter(rows)
    support: dict[str, set[int]] = {}
    for i, sigma in enumerate(grid):
        for cid in emit(sigma):
            support.setdefault(cid, set()).add(i)
    return {cid: fiber_metrics(idxs, grid)[0] for cid, idxs in support.items()}


def _clip(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


# --- (i) the degeneracy anchor ------------------------------------------------------------------


def test_degeneracy_anchor_bare_edge_matches_analytic() -> None:
    """§2.3 falsifier (i): a bare-edge claim's exact pers == the analytic monotone transform of the
    stored cosine. Disagreement means the computation is broken (edge persistence IS a re-dressed
    cosine — §2.1 — and the exact oracle must reproduce it precisely)."""
    rows = _bare_edge_rows(0.655)               # a cosine strictly inside (0.55, 0.75)
    graph, _ = _phase7_emitter(rows)
    w = float(graph.sim[0, 1])                  # the ACTUAL computed cosine (fp-consistent)
    cid = claim_id("community", tuple(sorted(("dU", "dV"))), "+")

    exact = _exact_pers(rows, LO, HI)
    analytic = _clip((min(w, HI) - LO) / (HI - LO), 0.0, 1.0)
    assert exact[cid] == pytest.approx(analytic, abs=1e-12)
    # and it is a genuine bare edge: exactly one claim over the whole range.
    assert set(exact) == {cid}


# --- (ii) the ruler test ------------------------------------------------------------------------


def test_ruler_refinement_moves_pers_within_discretization_bound() -> None:
    """§2.3 falsifier (ii): refining Γ_m → Γ_{2m-1} (which contains Γ_m) moves pers by ≤ B·Δσ/span.
    A larger move means the metric is measuring the GRID, not the claim."""
    rows = _bare_edge_rows(0.655)
    m = 11
    coarse = _grid_pers(rows, _uniform_grid(LO, HI, m))
    refined = _grid_pers(rows, _uniform_grid(LO, HI, 2 * m - 1))   # 21 ⊇ Γ_11
    span = HI - LO
    bound = (span / (m - 1)) / span             # B=1 crossing for the bare edge → Δσ_coarse/span
    assert coarse and refined
    for cid, p_coarse in coarse.items():
        assert abs(refined[cid] - p_coarse) <= bound + 1e-12


def test_grid_estimator_agrees_with_exact_oracle_within_bound() -> None:
    """The plan §7 Item 2 falsifier: the grid estimator must not disagree with the exact oracle
    beyond the discretization bound at any resolution."""
    rows = _bare_edge_rows(0.655)
    exact = _exact_pers(rows, LO, HI)
    span = HI - LO
    for m in (11, 21):
        grid_p = _grid_pers(rows, _uniform_grid(LO, HI, m))
        bound = (span / (m - 1)) / span         # B=1 crossing
        for cid, p_exact in exact.items():
            assert abs(grid_p[cid] - p_exact) <= bound + 1e-12


# --- (gap) --------------------------------------------------------------------------------------


def test_gap_flag_and_pers_counts_cells_not_hull() -> None:
    """§2.3: `pers = |S|/m` is the SUPPORT measure — gaps do NOT count. A holey support flags gap
    and its pers stays below the hull-length reading a naive metric would give."""
    grid = _uniform_grid(LO, HI, 3)             # [0.55, 0.65, 0.75], m=3

    pers, s_min, s_max, gap, n_cells = fiber_metrics({0, 2}, grid)     # a hole at index 1
    assert gap is True
    assert n_cells == 2
    assert pers == pytest.approx(2 / 3)         # counts CELLS (2/3), not the hull span (3/3 = 1.0)
    hull_length_reading = (2 - 0 + 1) / 3       # what a naive "hull, not support" metric would give
    assert hull_length_reading == pytest.approx(1.0)
    assert pers < hull_length_reading
    assert s_min == pytest.approx(grid[0]) and s_max == pytest.approx(grid[2])

    # a contiguous support of the same hull is gap-free and reads full persistence.
    pers_full, _, _, gap_full, cells_full = fiber_metrics({0, 1, 2}, grid)
    assert gap_full is False and cells_full == 3 and pers_full == pytest.approx(1.0)


def test_fiber_metrics_rejects_empty_support() -> None:
    with pytest.raises(ValueError, match="empty support"):
        fiber_metrics(set(), _uniform_grid(LO, HI, 5))


# --- pure-helper guards (spec_hash / registry hash / strong threshold) ---------------------------


def test_spec_hash_carries_pipeline_and_grid() -> None:
    """spec_hash keys distinctly per pipeline AND per grid descriptor (the grid is a battery param,
    §2.4.3) — a different grid/range can never collapse onto the same key."""
    lever = get_lever("dream_rnd_sigma")
    g11 = _uniform_grid(LO, HI, 11)
    g21 = _uniform_grid(LO, HI, 21)
    assert fibers_spec_hash("phase7", lever, g11) != fibers_spec_hash("dream_v2", lever, g11)
    assert fibers_spec_hash("phase7", lever, g11) != fibers_spec_hash("phase7", lever, g21)
    # deterministic: same inputs → same hash.
    assert fibers_spec_hash("phase7", lever, g11) == fibers_spec_hash("phase7", lever, list(g11))


def test_lever_registry_hash_is_deterministic() -> None:
    assert lever_registry_hash() == lever_registry_hash()
    assert len(lever_registry_hash()) == 64   # sha256 hexdigest


def test_strong_threshold_is_the_provisional_default() -> None:
    """§2.5 SF-e provisional default — recorded so a change is deliberate; DESCRIPTIVE only."""
    assert STRONG_THRESHOLD == 0.5
