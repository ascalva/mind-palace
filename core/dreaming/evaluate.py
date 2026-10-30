# ── Family 1 boundary (capability algebra) · the materialization boundary · docs/NOTATION.md ──────
# OBJECT:    the estimate/force seam (dn-synchronic-diachronic-dreamer §2.4 SD-4, N2) — the ONE
#            store-touching evaluator a dream dispatch holds. `force(grant, cut[, generation])` is
#            single point where rows become real (L2); `estimate` prices a force from metadata only
#            (L3); composition of scope expressions is symbolic and store-free (L1). The three gates
#            (admissibility, budget, cache) coincide on this one boundary — the closed-evaluator
#            condition, guard tier (honest label: conformance inventory + counting-fake tests, NOT a
#            structural v3 — SD-g parked).
# INVARIANT: the evaluator is the dispatch's ONLY store-touching capability (L2); every `force` is
#            preceded by an `estimate` and refused before ANY row read if the estimate exceeds the
#            budget (L3, rule-#8 kin); composing k expressions performs zero reads (L1). A store
#            handle not derivable from the evaluator is a `ConformanceError` (the red team).
# ENFORCED:  guard (tests/unit/test_materialization_boundary.py): a counting `RowSource` proves L1
#            zero-reads and L2 exactly-one-burst; an over-budget estimate refuses with zero reads
#            (L3, F-SD4a); no row is obtained without a force (F-SD4b); a direct handle raises.
"""The materialization boundary — estimate then force (dn-synchronic-diachronic-dreamer §2.4 SD-4).

Laziness is a *requirement* here, not an optimization (the owner's addendum, adopted as law): the
graph grows in size and time, so evaluation strategy is first-class. This module is the dispatch
layer's realization of three of the five laws:

  * **L1 — composition is symbolic; cost is O(expression).** A `ScopeExpression` composes scope
    operations (meet / restrict / anchor-shift) without touching a store. Composing k of them is
    pure `core.scope` arithmetic — zero row reads.
  * **L2 — one materialization boundary.** `Evaluator.force(grant, cut[, generation]) → readings` is
    the single seam where rows become real, and it applies the admissibility check at the same call.
    The evaluator is the dispatch's ONLY store-touching capability (the closed-evaluator condition);
    a store handle not derivable from it fails `assert_conforms` (guard tier — honestly labelled;
    the structural v3 is SD-g, parked).
  * **L3 — estimate-then-force (the refusal gate).** Every force is preceded by a `CostEstimate`
    computed from the *unevaluated* expression against an injected `StatsProvider` (metadata only —
    chain/node counts, grid sizes, eigensolve dims). The estimate is pure data computed core-side;
    the **refusal is machinery-side** (the model advises / code acts split, non-negotiable #3). An
    over-budget estimate refuses BEFORE a single row is read, reporting budget and estimate,
    quantified.

PURE-CORE: imports only `core.scope`, `core.agent_scope`, `core.mirror`, and `core.dreaming.charter`
— all pure-core. It reads no live store: `force` reads through an injected `RowSource` (the
`core.mirror` seam, reused — §2.5), and `estimate` reads through an injected `StatsProvider`. Wiring
a live stats source or a live row source is a LATER plan's call (Q4 parked); both are Protocols,
exercised by counting fakes.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field, replace
from typing import Any, Protocol

from core.dreaming.charter import Budget
from core.kernel.agent_scope import ConformanceError, HandleInventory, assert_conforms
from core.kernel.clearance import clearance_of
from core.kernel.mirror import RowSource
from core.kernel.scope import DENYLIST_IDEAL, Scope, Window, WindowKind, admissible

# ═══════════════════════════════════════════════════════════════════════════════════════════════
# L1 — the symbolic scope expression (composition is store-free)
# ═══════════════════════════════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class ScopeExpression:
    """An UNEVALUATED composition of scope operations (L1). A `ScopeExpression` wraps a resolved
    `Scope` (`grant`) and records the composition trail (`ops`) for provenance; every combinator
    (`meet`, `restrict`, `anchor_shift`) returns a NEW expression via pure `core.scope` arithmetic,
    touches no store. Composing k expressions is therefore O(expression) with zero row reads — the
    honest baseline the force seam sits behind."""

    grant: Scope
    ops: tuple[str, ...] = ()

    def meet(self, other: Scope) -> ScopeExpression:
        """Compose with another scope (the delegation/intersection law) — symbolic, store-free."""
        return ScopeExpression(self.grant.meet(other), self.ops + ("meet",))

    def restrict(self, other: Scope) -> ScopeExpression:
        """Narrow this expression by another scope (a restriction is a meet by a narrower grant).
        Named separately for the composition trail; the arithmetic is the meet."""
        return ScopeExpression(self.grant.meet(other), self.ops + ("restrict",))

    def anchor_shift(self, window: Window, cut: Any | None = None) -> ScopeExpression:
        """Rebind the time window (an anchor-shift: same Σ/E/A, a new cut/interval) — symbolic.
        The re-anchored scope is a fresh `Scope`; SLICE re-checks for free at its construction, so a
        multi-stratum point anchor supplies its `cut` here (a downset over a base stratum is already
        multi-element, so a point window always carries one)."""
        shifted = replace(self.grant, time=replace(self.grant.time, window=window), cut=cut)
        return ScopeExpression(shifted, self.ops + ("anchor_shift",))


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# L3 — the cost estimate and the injected stats surface (metadata only)
# ═══════════════════════════════════════════════════════════════════════════════════════════════


class StatsProvider(Protocol):
    """The injected metadata surface an estimate reads (Q4, parked — Protocol only, no live wiring).
    Every method is a METADATA read (chain counts, node/edge counts, grid/eigensolve dims) over a
    grant — never a row read. A live provider is a later plan's call (the first live dispatch names
    its source); here it is exercised by counting fakes so the estimate is proven store-free."""

    def node_count(self, grant: Scope) -> int: ...

    def edge_count(self, grant: Scope) -> int: ...

    def eigensolve_dim(self, grant: Scope) -> int: ...

    def walk_steps(self, grant: Scope) -> int: ...


@dataclass(frozen=True)
class CostEstimate:
    """A force priced from metadata only (L3) — pure data computed core-side, no rows touched. Each
    field mirrors a `Budget` ceiling so `over(budget)` is a componentwise comparison; the refusal
    message reports both, quantified."""

    nodes: int
    edges: int
    eigensolve_dim: int
    walk_steps: int

    def over(self, budget: Budget) -> dict[str, tuple[int, int]]:
        """The dimensions where this estimate exceeds `budget`, as `{dim: (estimate, ceiling)}` —
        empty iff the force is within budget. Pure comparison; reads nothing."""
        checks = (
            ("nodes", self.nodes, budget.node_ceiling),
            ("edges", self.edges, budget.edge_ceiling),
            ("eigensolve_dim", self.eigensolve_dim, budget.eigensolve_dim_cap),
            ("walk_steps", self.walk_steps, budget.walk_budget),
        )
        return {name: (est, ceil) for name, est, ceil in checks if est > ceil}


class BudgetRefusalError(RuntimeError):
    """A force refused at estimate because its cost exceeds the budget (L3, F-SD4a). Machinery-side
    (the model advises / code acts split); the message carries both budget and estimate, quantified,
    and is raised BEFORE any row is read (the counting fake proves zero reads)."""


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# L2 — the closed evaluator: the ONE store-touching capability
# ═══════════════════════════════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class Evaluator:
    """The dispatch's single store-touching capability (L2, the closed-evaluator condition). Holds
    exactly one `RowSource` (the `core.mirror` seam, reused — a later representation swap behind
    `force` touches nothing here: F-SD5) and its declared handle inventory. `estimate` prices it
    from metadata (zero row reads); `force` is the one materialization boundary; `materialize` is
    the L3 gate (estimate → refuse-or-force). Guard tier: `assert_dispatch_conforms` checks it
    against the grant — a store handle not derivable from the evaluator is a `ConformanceError`."""

    source: RowSource
    handles: HandleInventory = field(default_factory=tuple)

    def estimate(self, expr: ScopeExpression, stats: StatsProvider) -> CostEstimate:
        """Price a force of `expr` from METADATA only (L3) — reads `stats`, never `source`; pure
        computed core-side; the refusal it feeds is machinery-side (see `materialize`)."""
        grant = expr.grant
        return CostEstimate(
            nodes=stats.node_count(grant),
            edges=stats.edge_count(grant),
            eigensolve_dim=stats.eigensolve_dim(grant),
            walk_steps=stats.walk_steps(grant),
        )

    def force(
        self, grant: Scope, cut: Any, generation: Any | None = None
    ) -> list[dict[str, Any]]:
        """The ONE materialization boundary (L2) — the single point where rows become real, and the
        dispatch's only store-touching call. Applies the admissibility check at the SAME call (the
        unification), then reads one burst through the `RowSource`. `cut` (and, for a counterfactual
        read, `generation`) pin the read; a multi-stratum point read already demanded its cut for
        free at the grant's construction (SLICE), so this seam never re-implements legality."""
        if not admissible(grant, [DENYLIST_IDEAL]):
            raise ConformanceError(
                f"force refused: grant names a denylist stratum (𝔇) — inadmissible "
                f"(Σ={sorted(s.value for s in grant.sigma.strata)})"
            )
        # A point read that is multi-stratum must carry a cut — enforced structurally at Scope
        # construction (SliceError); this asserts the seam's contract for the caller's clarity.
        multi_stratum_point = (
            grant.time.window.kind is WindowKind.POINT and len(grant.sigma.strata) > 1
        )
        if multi_stratum_point and cut is None:
            raise ConformanceError(
                "force refused: a multi-stratum point read needs a cut (SLICE) — none supplied"
            )
        return [dict(r) for r in self.source.all_rows(clearance=clearance_of(grant))]

    def materialize(
        self,
        expr: ScopeExpression,
        budget: Budget,
        stats: StatsProvider,
        cut: Any,
        generation: Any | None = None,
    ) -> list[dict[str, Any]]:
        """The L3 refusal gate — estimate-then-force in one seam. Prices `expr` from metadata; if
        the estimate exceeds `budget` on any dimension, REFUSES (`BudgetRefusalError`) BEFORE
        any row is read; otherwise forces exactly one read burst. This is the only sanctioned way a
        dispatch obtains rows, so F-SD4b (a row with no force event) and F-SD4a (a breach with no
        prior estimate) are both closed by construction."""
        est = self.estimate(expr, stats)
        over = est.over(budget)
        if over:
            raise BudgetRefusalError(
                f"refused at estimate: budget={budget}, estimate={est}, over={over}"
            )
        return self.force(expr.grant, cut, generation)


def assert_dispatch_conforms(grant: Scope, evaluator: Evaluator) -> None:
    """Guard-tier closed-evaluator check (L2): the evaluator's handle inventory is within `grant`
    (`assert_conforms`, reused verbatim — the algebra's own conformance). A store handle not derived
    from the evaluator — one reaching a stratum outside Σ, or projection-writing/edge-writing beyond
    the grant — raises `ConformanceError`. Honest label: a construction-site check, not a structural
    impossibility (the structural v3 is SD-g, parked; F-SD4b re-opens it)."""
    assert_conforms(grant, evaluator.handles)


def compose(exprs: Iterable[ScopeExpression]) -> ScopeExpression:
    """Fold a sequence of expressions by meet — a convenience for the L1 zero-read demonstration.
    Pure `core.scope` arithmetic; touches no store."""
    it = iter(exprs)
    acc = next(it)
    for e in it:
        acc = acc.meet(e.grant)
    return acc
