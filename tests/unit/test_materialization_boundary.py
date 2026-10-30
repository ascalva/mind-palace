"""D-0 Items 2 & 3 — the materialization boundary + the refusal gate (bp-079,
dn-synchronic-diachronic-dreamer §2.4 SD-4, L1/L2/L3).

Guard-tier tests (honestly labelled — the closed-evaluator condition is guard, not the structural
v3, SD-g parked). A counting `RowSource` fake is the instrument: it counts every `all_rows` call, so
"zero row reads" and "exactly one read burst" are mechanical facts, not claims.

  * L1 — composing k scope expressions performs ZERO reads.
  * L2 — exactly one read burst at `force`; the dispatch's handle inventory passes conformance;
    a red-team charter holding a direct store handle raises `ConformanceError`.
  * L3 — an over-budget estimate refuses with zero row reads, and the message carries budget and
    estimate quantified.
  * F-SD4b — no row is obtained without a corresponding force event.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from core.dreaming.charter import Budget
from core.dreaming.evaluate import (
    BudgetRefusalError,
    CostEstimate,
    Evaluator,
    ScopeExpression,
    assert_dispatch_conforms,
    compose,
)
from core.kernel.agent_scope import ConformanceError, Handle, dreamer_scope
from core.kernel.clearance import Clearance
from core.kernel.provenance import Provenance
from core.kernel.scope import (
    Authority,
    Clock,
    EdgeScope,
    Privilege,
    Scope,
    Stratum,
    StratumScope,
    Tier,
    TimeScope,
    Window,
    WorldReach,
)


# ── fakes: a counting row source and a counting stats provider ─────────────────────────────────
@dataclass
class CountingRowSource:
    """A `RowSource` that counts every `all_rows` call. `reads` is the number of read bursts — the
    mechanical witness for L1 (0) and L2 (1)."""

    _rows: list[dict[str, Any]] = field(default_factory=list)
    reads: int = 0

    def all_rows(self, *, clearance: Clearance[Provenance]) -> list[dict[str, Any]]:
        self.reads += 1
        return list(self._rows)


@dataclass
class CountingStats:
    """A `StatsProvider` returning fixed metadata and counting its own calls. Metadata reads are
    allowed at estimate time (L3); the point is that ROW reads stay zero when a dispatch refuses."""

    nodes: int = 10
    edges: int = 20
    dim: int = 8
    walks: int = 100
    calls: int = 0

    def node_count(self, grant: Scope) -> int:
        self.calls += 1
        return self.nodes

    def edge_count(self, grant: Scope) -> int:
        self.calls += 1
        return self.edges

    def eigensolve_dim(self, grant: Scope) -> int:
        self.calls += 1
        return self.dim

    def walk_steps(self, grant: Scope) -> int:
        self.calls += 1
        return self.walks


def _grant(*strata: Stratum) -> Scope:
    return dreamer_scope(strata or (Stratum.MIRROR,))


def _budget(**over: int) -> Budget:
    base = dict(node_ceiling=1000, edge_ceiling=5000, eigensolve_dim_cap=64, walk_budget=10_000)
    base.update(over)
    return Budget(**base)  # type: ignore[arg-type]


# ── L1 — composition is symbolic; zero reads ───────────────────────────────────────────────────
def test_l1_composing_k_expressions_performs_zero_reads():
    """Composing k scope expressions touches no store — the counting source stays at 0 reads."""
    src = CountingRowSource(_rows=[{"id": 1}, {"id": 2}])
    _evaluator = Evaluator(source=src)  # holding a source is not touching it
    base = ScopeExpression(_grant(Stratum.MIRROR))
    exprs = [ScopeExpression(_grant(Stratum.MIRROR)) for _ in range(8)]
    folded = compose([base, *exprs])
    # also exercise the named combinators explicitly
    folded = folded.meet(_grant(Stratum.MIRROR)).restrict(_grant(Stratum.MIRROR))
    folded = folded.anchor_shift(Window.point("cut-c1"), cut="cut-c1")
    assert isinstance(folded.grant, Scope)
    assert src.reads == 0                      # L1: composition performed ZERO row reads


# ── L2 — exactly one read burst at force ───────────────────────────────────────────────────────
def test_l2_force_is_exactly_one_read_burst():
    src = CountingRowSource(_rows=[{"id": 1}, {"id": 2}, {"id": 3}])
    ev = Evaluator(source=src)
    grant = _grant(Stratum.MIRROR)
    rows = ev.force(grant, cut="cut-c1")
    assert len(rows) == 3
    assert src.reads == 1                      # L2: exactly one materialization


def test_l2_multi_stratum_point_read_needs_a_cut():
    """A multi-stratum point read demands its cut (SLICE, for free). The seam refuses a cut-less one
    rather than partially materialize."""
    # Build a multi-stratum point-window grant carrying a cut (so Scope construction succeeds), then
    # call force without a cut to exercise the seam's contract.
    grant = Scope(
        sigma=StratumScope.of(Stratum.MIRROR, Stratum.INTERPRETED),
        edges=EdgeScope.top(),
        time=TimeScope(Clock.N_S, Window.point("cut-c1")),
        authority=Authority(Privilege.READ, 1, WorldReach.NONE),
        tier=Tier.STATIC_GUARD,
        cut="cut-c1",
    )
    src = CountingRowSource(_rows=[{"id": 1}])
    ev = Evaluator(source=src)
    with pytest.raises(ConformanceError, match="cut"):
        ev.force(grant, cut=None)
    assert src.reads == 0                      # refused before any read


# ── L2 conformance — the closed-evaluator inventory ────────────────────────────────────────────
def test_l2_honest_inventory_passes_conformance():
    """The dispatch's handle inventory — a handle within the granted Σ — passes conformance."""
    grant = _grant(Stratum.MIRROR, Stratum.INTERPRETED)
    ev = Evaluator(
        source=CountingRowSource(),
        handles=(Handle(name="evaluator", stratum=Stratum.MIRROR, writes_stratum=True),),
    )
    assert_dispatch_conforms(grant, ev)        # no raise


def test_l2_red_team_direct_store_handle_raises_conformance_error():
    """A store handle not derivable from the evaluator — reaching a stratum OUTSIDE the grant — is a
    `ConformanceError` (the red team; the closed-evaluator condition, guard tier)."""
    grant = _grant(Stratum.MIRROR)             # Σ = {mirror, mirror_authored}
    rogue = Evaluator(
        source=CountingRowSource(),
        handles=(Handle(name="smuggled", stratum=Stratum.OBSERVED),),  # OBSERVED ∉ grant
    )
    with pytest.raises(ConformanceError):
        assert_dispatch_conforms(grant, rogue)


# ── L3 — the refusal gate: over-budget refuses with zero reads, quantified ─────────────────────
def test_l3_over_budget_refuses_with_zero_reads():
    src = CountingRowSource(_rows=[{"id": 1}])
    stats = CountingStats(nodes=10_000)        # blows the 1000 node ceiling
    ev = Evaluator(source=src)
    expr = ScopeExpression(_grant(Stratum.MIRROR))
    with pytest.raises(BudgetRefusalError) as exc:
        ev.materialize(expr, _budget(), stats, cut="cut-c1")
    msg = str(exc.value)
    assert "refused at estimate" in msg
    assert "10000" in msg and "1000" in msg    # estimate AND ceiling, quantified
    assert src.reads == 0                      # L3 / F-SD4a: ZERO rows read on refusal


def test_l3_within_budget_forces_exactly_once():
    src = CountingRowSource(_rows=[{"id": 1}, {"id": 2}])
    stats = CountingStats()                    # within all ceilings
    ev = Evaluator(source=src)
    expr = ScopeExpression(_grant(Stratum.MIRROR))
    rows = ev.materialize(expr, _budget(), stats, cut="cut-c1")
    assert len(rows) == 2
    assert src.reads == 1                      # exactly one force event


@pytest.mark.parametrize(
    "dim,val", [("edges", 99_999), ("eigensolve_dim", 999), ("walk_steps", 10**9)]
)
def test_l3_each_budget_dimension_can_refuse(dim: str, val: int):
    """Every ceiling is load-bearing — each dimension independently triggers the refusal."""
    kwargs = {"nodes": 1, "edges": 1, "dim": 1, "walks": 1}
    field_map = {"edges": "edges", "eigensolve_dim": "dim", "walk_steps": "walks"}
    kwargs[field_map[dim]] = val
    stats = CountingStats(**kwargs)
    src = CountingRowSource(_rows=[{"id": 1}])
    ev = Evaluator(source=src)
    expr = ScopeExpression(_grant(Stratum.MIRROR))
    with pytest.raises(BudgetRefusalError):
        ev.materialize(expr, _budget(), stats, cut="cut-c1")
    assert src.reads == 0


# ── F-SD4b — no row obtained without a force event ─────────────────────────────────────────────
def test_f_sd4b_no_row_without_a_force_event():
    """The lazy-view = capability unification is not theater: rows appear ONLY through a force.
    After composition (L1) and a refused materialize (L3), the read count is still 0; it becomes 1
    only when a within-budget materialize forces."""
    src = CountingRowSource(_rows=[{"id": 1}])
    ev = Evaluator(source=src)
    expr = ScopeExpression(_grant(Stratum.MIRROR))

    # compose — no reads
    _ = expr.meet(_grant(Stratum.MIRROR)).restrict(_grant(Stratum.MIRROR))
    assert src.reads == 0

    # refuse — no reads
    with pytest.raises(BudgetRefusalError):
        ev.materialize(expr, _budget(), CountingStats(nodes=10**9), cut="c")
    assert src.reads == 0

    # only a within-budget force yields a row
    rows = ev.materialize(expr, _budget(), CountingStats(), cut="c")
    assert rows == [{"id": 1}]
    assert src.reads == 1                      # exactly one force event = exactly one read burst


# ── the estimate is pure data (the over() comparison reads nothing) ────────────────────────────
def test_cost_estimate_over_is_pure_comparison():
    est = CostEstimate(nodes=5, edges=5, eigensolve_dim=5, walk_steps=5)
    assert est.over(_budget()) == {}                                   # within budget
    tight = Budget(node_ceiling=1, edge_ceiling=1, eigensolve_dim_cap=1, walk_budget=1)
    over = est.over(tight)
    assert over == {
        "nodes": (5, 1),
        "edges": (5, 1),
        "eigensolve_dim": (5, 1),
        "walk_steps": (5, 1),
    }
