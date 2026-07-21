# ── Family 1 boundary (labelings & information-flow) + capability algebra · docs/NOTATION.md ──
# OBJECT:    Scope = (Σ, E, T, A) — the capability an agent/View holds, as a point in a bounded
#            lattice (dn-capability-scope §2.1). meet = safe composition (delegation); join = a
#            widening; ⊑ = "no more authority than". The five built Views are instances (§2.4).
# INVARIANT: monotone delegation — meet(parent, template) ⊑ parent, ALWAYS (non-negotiable #6);
#            the foundation denylist 𝔇 is subtracted from ⊤_Σ (CONSTITUTION.md / eval/golden never
#            grantable); cross-clock meets are a PARTIAL semilattice — a constructor error, never a
#            silent guess, until the global event clock N materializes (CS-a).
# ENFORCED:  static (this pure-core typing layer; mypy-checked) + guard (tests/unit/test_scope.py
#            proves the lattice laws, the partial T-meet, and delegation-monotonicity). This module
#            wires NO enforcement into any read path — it is vocabulary, not a gate (bp-039 §0).
"""The capability-scope algebra (`CQ-scope`) as types (dn-capability-scope, ratified 2026-07-15).

`dn-core-query-protocol` §2.1 seeded the scope grammar `s = (Σ, E, T, A)`; `dn-capability-scope`
made each component well-posed and this module types it. A `Scope` is a point in a bounded lattice
whose four coordinates are themselves lattices:

  * **Σ (`StratumScope`)** — a downward-closed subset of the stratum-refinement forest R. Base
    strata (mirror, curated, observed, ops, reference, interpreted, world, dialogue) with refinement
    predicates BELOW them as first-class elements (`reference_repo ⊂ reference`,
    `mirror_authored ⊂ mirror`, `dialogue_transcript`/`dialogue_artifact ⊂ dialogue`, and the
    default-EXCLUDED `exhaust ⊂ dialogue` — grantable only when named, dn-agentic-loop §2.4b).
    `⊤_Σ = R ∖ 𝔇`: even the fullest grant excludes the foundation denylist 𝔇 (an order-ideal),
    so `CONSTITUTION.md` / `eval/golden/**` are structurally ungrantable.
  * **E (`EdgeScope`)** — the edge-class fibers `E ⊆ {F, D, C}` (F = citation, D = supersession,
    C = causal-witnessed; dn-agent-taxonomy §2.5).
  * **T (`TimeScope`)** — `(clock, window)`. A clock is a monotone coarsening of the ledger causal
    order; the clock poset has the global event clock N (finest, PARKED — not yet materialized) at
    the top. The T-meet is PARTIAL: same clock → intersect windows; different clocks → a constructor
    error `NoCommonClockError` until N materializes (the honesty the partiality preserves).
  * **A (`Authority`)** — `P × W_Σ × W_world`: the advisory ladder `P ∈ {READ < READ_PROPOSE}`
    (non-negotiable #3), the projection-write bit `W_Σ ∈ {0 < 1}` (the sensor dual), and the
    effector blast-radius chain `W_world` (`WorldReach`). The seed's single "write" rung conflated
    store-projection and world-mutation; the product repairs it.

`meet`/`join`/`⊑` are componentwise; the enforcement `tier` is an annotation (min-composed along the
construction chain), NOT a lattice element — so it is `compare=False` and rides beside the four
lattice coordinates. Result typing (`Inv` vs `Rate(κ)`, Rule CLOCK) lives at the bottom of the file.

This is a PURE-CORE module: it imports nothing from `ops/`, `edge/`, or a store (the sealed-core
egress rule, and the ops→core dependency direction — the `ReversibilityClass → WorldReach` bridge
lives ops-side in `ops/effects.py`). It materializes no clock; N stays parked (CS-a).

The zone-boundary law `PRIVATE_STRATA`/`zone_admissible` (below the deployed top) types the
bright-line inversion "broad private read ⊥ world reach" as a cross-coordinate predicate over Σ × A
(dn-agentic-loop §2.3, gap G-D) — its warrant, and the adversarial ratchet (F-AL3), live there.
"""

from __future__ import annotations

from collections.abc import Hashable, Iterable
from dataclasses import dataclass, field
from enum import Enum, IntEnum, StrEnum
from typing import Any, Literal, Protocol, cast

# ═══════════════════════════════════════════════════════════════════════════════════════════════
# Σ — the stratum-refinement forest R (dn-capability-scope §2.1; fable pass S1)
# ═══════════════════════════════════════════════════════════════════════════════════════════════

class Stratum(StrEnum):
    """An element of the refinement forest R. Base strata + refinement predicates (BELOW their base)
    as first-class elements, plus FOUNDATION — the denylist 𝔇, never in a grant (`⊤_Σ = R ∖ 𝔇`)."""

    MIRROR = "mirror"
    MIRROR_AUTHORED = "mirror_authored"      # ⊂ mirror (the π_MR refinement predicate)
    CURATED = "curated"
    OBSERVED = "observed"
    OPS = "ops"
    REFERENCE = "reference"
    REFERENCE_REPO = "reference_repo"        # ⊂ reference (the C1 refinement predicate)
    INTERPRETED = "interpreted"
    WORLD = "world"
    # the discourse substrate + its two refinements (dn-agent-taxonomy §2.3): dialogue_transcript =
    # the chat stores (rawstore/chatlog/chat_events); dialogue_artifact = brainstorms/design-notes/
    # docs (overlaps reference_repo in v1 — R is grant vocabulary, not a disk partition).
    DIALOGUE = "dialogue"
    DIALOGUE_TRANSCRIPT = "dialogue_transcript"      # ⊂ dialogue
    DIALOGUE_ARTIFACT = "dialogue_artifact"          # ⊂ dialogue
    # the agent-exhaust refinement (dn-agentic-loop §2.4b EX-1). A genuine refinement
    # `exhaust ⊂ dialogue` (`_REFINES` below, so it sits BELOW dialogue in R) BUT an EXCLUDED
    # refinement (`_EXCLUDED_REFINEMENTS`): unlike dialogue_transcript/dialogue_artifact it is NOT
    # auto-added by a parent's downward closure — a read of agent-exhaust rows is constructible only
    # under a grant that NAMES it (the bp-081 HYPOTHETICAL default-grant precedent, applied to a
    # refinement). So `⊤_Σ`/`of(dialogue)` omit it and stay byte-identical; only `of(…, exhaust)`
    # sees it (the Σ-visibility capability test, F-AL6). "Low priority" ≠ this cut: set-membership
    # isolation is the safety property; the retrieval weight `w(a_self)` is tuning, owner-gated.
    EXHAUST = "exhaust"                      # ⊂ dialogue; excluded-by-default refinement (§2.4b)
    # the counterfactual overlay stratum (dn-synchronic-diachronic-dreamer §2.6-1). An OVERLAY, not
    # a refinement: staged hypotheses carry their would-be stratum/provenance as ROW DATA (stratum ≠
    # provenance), so one element serves overlays beside any stratum. Unlike every other base
    # stratum it is EXCLUDED from ⊤_Σ (`_BASE_STRATA` below) — grantable ONLY by a scope that names
    # it explicitly, never by the fullest ordinary grant, so "default grants exclude it" is
    # structural (the Σ-visibility capability test: a read of staged rows is constructible only
    # under a grant naming HYPOTHETICAL). NOT the denylist: unlike FOUNDATION it IS admissible.
    HYPOTHETICAL = "hypothetical"            # overlay stratum; ∉ ⊤_Σ, grantable only when named
    FOUNDATION = "foundation"                # 𝔇 — CONSTITUTION.md / eval/golden/**; NEVER grantable


# child ⊂ parent: the refinement predicate `child` sits BELOW `parent` in R (a downset holding the
# parent holds the child — a grant over `reference` includes its `reference_repo` sub-part).
_REFINES: dict[Stratum, Stratum] = {
    Stratum.MIRROR_AUTHORED: Stratum.MIRROR,
    Stratum.REFERENCE_REPO: Stratum.REFERENCE,
    Stratum.DIALOGUE_TRANSCRIPT: Stratum.DIALOGUE,   # dn-agent-taxonomy §2.3
    Stratum.DIALOGUE_ARTIFACT: Stratum.DIALOGUE,     # dn-agent-taxonomy §2.3
    Stratum.EXHAUST: Stratum.DIALOGUE,               # dn-agentic-loop §2.4b EX-1 (excluded refine)
}

# the base strata (the roots of R) — everything a maximal grant may name, minus the denylist AND the
# HYPOTHETICAL overlay. FOUNDATION is excluded because it is never grantable (𝔇); HYPOTHETICAL is
# excluded because it must be named EXPLICITLY (an overlay is not part of the fullest ordinary
# grant — dn-synchronic-diachronic-dreamer §2.6-1). Both exclusions leave ⊤_Σ byte-identical to
# before this stratum existed (additive property): HYPOTHETICAL was never in top(), so no law moves.
_BASE_STRATA: frozenset[Stratum] = frozenset(
    s for s in Stratum
    if s not in _REFINES and s not in (Stratum.FOUNDATION, Stratum.HYPOTHETICAL)
)


# EXCLUDED refinements — the `exhaust ⊂ dialogue` default-grant exclusion (dn-agentic-loop §2.4b
# EX-1(ii)). A genuine refinement (it IS in `_REFINES`, so it sits below its parent in R and is
# excluded from `_BASE_STRATA` like every refinement), YET a parent's downward closure does NOT
# auto-add it: it enters a downset ONLY when named directly. This is the bp-081 HYPOTHETICAL
# precedent applied to a refinement — `⊤_Σ`/`of(dialogue)` stay byte-identical (exhaust never
# auto-added), and a read of agent-exhaust rows is constructible only under a grant naming `exhaust`
# (the Σ-visibility capability test the F-AL6 ratchet pins). Set-membership isolation is the safety
# property; NOT a trust weight (`w(a_self)` is tuning, owner-gated at the authorship-axis note).
_EXCLUDED_REFINEMENTS: frozenset[Stratum] = frozenset({Stratum.EXHAUST})


def _refinements_below(s: Stratum) -> frozenset[Stratum]:
    """The refinement predicates strictly below `s` in R (child ⊂ s). One level in v1 (the forest is
    shallow); recursion-ready if a refinement ever refines a refinement."""
    return frozenset(child for child, parent in _REFINES.items() if parent == s)


def _downward_close(strata: Iterable[Stratum]) -> frozenset[Stratum]:
    """The downward closure in R: adding a base stratum pulls in its refinement predicates (a grant
    over `reference` includes `reference_repo`). A downset is closed under this — EXCEPT for the
    excluded refinements (`_EXCLUDED_REFINEMENTS`): a parent's closure SKIPS them, and one enters a
    downset only when it is directly among the input strata (the `exhaust ⊂ dialogue` default-grant
    exclusion, dn-agentic-loop §2.4b EX-1(ii)). A directly-named stratum is always kept."""
    out: set[Stratum] = set(strata)                             # named strata kept verbatim
    for s in out.copy():
        out |= _refinements_below(s) - _EXCLUDED_REFINEMENTS    # auto-close skips excluded ones
    return frozenset(out)


@dataclass(frozen=True)
class StratumScope:
    """A downward-closed subset of R. Construct via `of(...)` (auto-closes); `meet`/`join`
    are ∩/∪ (both preserve downward-closure), `⊑` is ⊆. `top()` is `R ∖ 𝔇`."""

    strata: frozenset[Stratum]

    @classmethod
    def of(cls, *strata: Stratum) -> StratumScope:
        """Build the downset generated by `strata` (auto-closes downward). FOUNDATION is admissible
        here only to construct the denylist ideal — a real grant never names it (`admissible`)."""
        return cls(strata=_downward_close(strata))

    @classmethod
    def top(cls) -> StratumScope:
        """`⊤_Σ = R ∖ 𝔇` — the fullest grant: every stratum + its refinements, minus FOUNDATION."""
        return cls(strata=_downward_close(_BASE_STRATA))

    @classmethod
    def bottom(cls) -> StratumScope:
        """`⊥_Σ = ∅` — no stratum."""
        return cls(strata=frozenset())

    def meet(self, other: StratumScope) -> StratumScope:
        return StratumScope(self.strata & other.strata)

    def join(self, other: StratumScope) -> StratumScope:
        return StratumScope(self.strata | other.strata)

    def __le__(self, other: StratumScope) -> bool:
        return self.strata <= other.strata


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# E — the edge-class fibers (dn-capability-scope §2.1)
# ═══════════════════════════════════════════════════════════════════════════════════════════════

# F = citation/warrant edges; D = supersession edges; C = causal-witnessed production edges
# (dn-agent-taxonomy §2.5 — origin, not lineage: a dialogue action → the artifact it produced).
Fiber = Literal["F", "D", "C"]


@dataclass(frozen=True)
class EdgeScope:
    """`E ⊆ {F, D, C}` — dispositional edge-class fibers. meet = ∩, join = ∪, ⊑ = ⊆."""

    fibers: frozenset[str]

    @classmethod
    def of(cls, *fibers: Fiber) -> EdgeScope:
        return cls(frozenset(fibers))

    @classmethod
    def bottom(cls) -> EdgeScope:
        return cls(frozenset())

    @classmethod
    def top(cls) -> EdgeScope:
        return cls(frozenset({"F", "D", "C"}))

    def meet(self, other: EdgeScope) -> EdgeScope:
        return EdgeScope(self.fibers & other.fibers)

    def join(self, other: EdgeScope) -> EdgeScope:
        return EdgeScope(self.fibers | other.fibers)

    def __le__(self, other: EdgeScope) -> bool:
        return self.fibers <= other.fibers


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# T — time scope = (clock, window) (dn-capability-scope §2.1/§2.2; fable pass S2/S3)
# ═══════════════════════════════════════════════════════════════════════════════════════════════

class Clock(Enum):
    """A monotone coarsening of the ledger's causal order (op-seq spine). The poset is ordered by
    fineness `⪰` ("at least as fine as"); N is the finest and the top, but PARKED — not materialized
    (CS-a), so it is the canonical cross-clock refinement that does not yet exist. `wall`/`now` are
    exogenous labelings, not event clocks."""

    N = "N"                          # global event clock — finest; PARKED (CS-a), not materialized
    N_S = "N_s"                      # per-stratum event clock
    COMMIT = "commit"                # a commit is a RANGE of N; the consistent cut for repo strata
    DISTINCT_SNAPSHOT = "distinct_snapshot"
    PROJECTION_EVENT = "projection_event"   # MirrorView's clock (a projection is an event)
    LAST_WRITE = "last_write"        # OpsView's clock
    WALL = "wall"                    # exogenous wall-time labeling — not an event clock
    NOW = "now"                      # EffectView — the live present (an exogenous anchor)


# PARKED clocks: named but not materialized. A cross-clock refinement resolving ONLY to a parked
# clock is a constructor error (the partial-meet honesty). CS-a materializes N and this shrinks.
_PARKED_CLOCKS: frozenset[Clock] = frozenset({Clock.N})

# The strict-finer relation `⪰` (a ⪰ b ⟺ a refines b), as {clock: set of clocks it is finer than}.
# N is finer than everything (the top); a commit refines to distinct snapshots. Everything else is
# incomparable in v1 (their only common refinement is N — parked — so they meet to a constructor
# error, which is exactly the note's "canonically N" resolution while N is parked).
_FINER_THAN: dict[Clock, frozenset[Clock]] = {
    Clock.N: frozenset(c for c in Clock if c is not Clock.N),
    Clock.COMMIT: frozenset({Clock.DISTINCT_SNAPSHOT}),
}


def _finer_or_equal(a: Clock, b: Clock) -> bool:
    """`a ⪰ b` — a is at least as fine as b."""
    return a is b or b in _FINER_THAN.get(a, frozenset())


def common_refinement(a: Clock, b: Clock) -> Clock | None:
    """The materialized clock ⪰-above BOTH `a` and `b` (their least common refinement), or None when
    the only such clock is parked (N). None ⇒ a cross-clock T-meet is a constructor error.

    v1 poset: comparable clocks return the finer of the two; every other distinct pair resolves only
    through the parked N, hence None. Extensible at CS-a (materialize N ⇒ fewer None results)."""
    if _finer_or_equal(a, b):
        return None if a in _PARKED_CLOCKS else a
    if _finer_or_equal(b, a):
        return None if b in _PARKED_CLOCKS else b
    return None


class WindowKind(Enum):
    POINT = "point"
    INTERVAL = "interval"
    ALL = "all"          # ∗ — the dilation space, uncompressed (the ledger window (N, ∗))
    EMPTY = "empty"      # ⊥ — the disjoint/empty window


@dataclass(frozen=True)
class Window:
    """A window over a clock's index: `pt(a)`, `[a, b]`, `∗` (ALL), or EMPTY (⊥). Bounds are opaque
    tokens (a commit SHA, an event count, …); meet/⊑ handle ALL/EMPTY/equality and int-orderable
    bounds, and are conservative (→ EMPTY / not-⊑) where opaque overlap is indeterminate. Precise
    window arithmetic is retrieval math (out of scope, dn-capability-scope §1)."""

    kind: WindowKind
    lo: Hashable = None
    hi: Hashable = None

    @classmethod
    def point(cls, a: Hashable) -> Window:
        return cls(WindowKind.POINT, a, a)

    @classmethod
    def interval(cls, a: Hashable, b: Hashable) -> Window:
        return cls(WindowKind.INTERVAL, a, b)

    @classmethod
    def all(cls) -> Window:
        return cls(WindowKind.ALL)

    @classmethod
    def empty(cls) -> Window:
        return cls(WindowKind.EMPTY)

    def _orderable(self, other: Window) -> bool:
        return all(isinstance(x, int) for x in (self.lo, self.hi, other.lo, other.hi))

    def meet(self, other: Window) -> Window:
        """Window intersection (same clock). ALL is the identity, EMPTY the annihilator; equal
        windows meet to themselves; int-bounded intervals/points intersect exactly; opaque, unequal
        windows meet conservatively to EMPTY (safe — never over-grants)."""
        if self.kind is WindowKind.EMPTY or other.kind is WindowKind.EMPTY:
            return Window.empty()
        if self.kind is WindowKind.ALL:
            return other
        if other.kind is WindowKind.ALL:
            return self
        if self == other:
            return self
        if self._orderable(other):
            lo = max(cast(int, self.lo), cast(int, other.lo))
            hi = min(cast(int, self.hi), cast(int, other.hi))
            if lo > hi:
                return Window.empty()
            return Window.point(lo) if lo == hi else Window.interval(lo, hi)
        return Window.empty()

    def join(self, other: Window) -> Window:
        """Window widening (the convex hull / union over-approximation). ALL is the annihilator,
        EMPTY the identity; equal windows join to themselves; int-bounded windows join to their
        convex hull; opaque, unequal windows widen conservatively to ALL (safe — never under-grants
        a widening)."""
        if self.kind is WindowKind.ALL or other.kind is WindowKind.ALL:
            return Window.all()
        if self.kind is WindowKind.EMPTY:
            return other
        if other.kind is WindowKind.EMPTY:
            return self
        if self == other:
            return self
        if self._orderable(other):
            lo = min(cast(int, self.lo), cast(int, other.lo))
            hi = max(cast(int, self.hi), cast(int, other.hi))
            return Window.point(lo) if lo == hi else Window.interval(lo, hi)
        return Window.all()

    def __le__(self, other: Window) -> bool:
        """`self ⊆ other`. EMPTY ⊑ anything; anything ⊑ ALL; equal ⊑; int-bounded by containment;
        otherwise conservatively False (opaque containment is unprovable here)."""
        if self.kind is WindowKind.EMPTY:
            return True
        if other.kind is WindowKind.ALL:
            return True
        if self == other:
            return True
        if (self.kind is not WindowKind.ALL and other.kind is not WindowKind.EMPTY
                and self._orderable(other)):
            return (cast(int, other.lo) <= cast(int, self.lo)
                    and cast(int, self.hi) <= cast(int, other.hi))
        return False


class NoCommonClockError(ValueError):
    """A cross-clock T-meet whose only common refinement is a parked clock (canonically N). The
    partial-meet honesty: no shared MATERIALIZED clock ⇒ a constructor error, never a silent guess
    (dn-capability-scope §2.2). Re-entry: CS-a materializes N."""


# ── The clock-atlas seam (GC-4, dn-global-event-clock §2.5) ──────────────────────────────────────
# A cross-clock T-meet totalizes ONLY through a materialized common refinement (canonically N). The
# derived spine (`core/temporal/spine.py`) IS that object, but THIS module is pure-core and imports
# no store — so it knows the atlas only as a Protocol. A consumer that has built the spine registers
# a concrete atlas (`core/temporal/atlas.py`, which DOES import stores); `core/scope.py` never
# imports it. With NO atlas registered (`_ATLAS is None`, the default), the T-meet stays the honest
# PARTIAL semilattice it ships as — every current behavior byte-identical (the GC-4 falsifier).
class ClockAtlas(Protocol):
    """The injectable clock-pullback seam `TimeScope.meet` consults for a cross-clock meet. `has`
    reports whether a window over κ can be pulled back to N (an exogenous coordinate with no `p_κ` —
    wall, the live-present anchor — is NOT covered); `pullback` maps a κ-window to an opaque,
    hashable N-window token (the event set `p_κ⁻¹(W)`); `intersect` meets two such tokens. The
    concrete `SpineAtlas` lives in `core/temporal/atlas.py`; scope.py stays store-free (plan §3)."""

    def has(self, clock: Clock) -> bool: ...
    def pullback(self, clock: Clock, window: Window) -> Hashable: ...      # an N-window token
    def intersect(self, a: Hashable, b: Hashable) -> Hashable | None: ...  # None ⇒ the empty set


# The process-wide registered atlas — `None` by default (the T-meet is the partial semilattice it
# ships as until a consumer materializes the spine and registers one). Single-writer registration at
# daemon start; plan §11 parks auto-registration until a second consumer needs it.
_ATLAS: ClockAtlas | None = None


def register_atlas(atlas: ClockAtlas | None) -> None:
    """Register (or clear, with `None`) the process-wide clock atlas the cross-clock
    `TimeScope.meet` consults. Consumers that build the spine call this; `core/scope.py` never
    imports the concrete atlas (the pure-core seam). Idempotent — last write wins."""
    global _ATLAS
    _ATLAS = atlas


@dataclass(frozen=True)
class TimeScope:
    """`T = (clock, window)`. The anchor is first-class: `now = (κ, pt(latest))`, `ledger = (N, ∗)`.
    The meet is PARTIAL — a cross-clock meet raises `NoCommonClockError` until N materializes."""

    clock: Clock
    window: Window

    @classmethod
    def now(cls, clock: Clock, latest: Hashable) -> TimeScope:
        return cls(clock, Window.point(latest))

    @classmethod
    def ledger(cls) -> TimeScope:
        """`(N, ∗)` — the dilation space, uncompressed."""
        return cls(Clock.N, Window.all())

    def meet(self, other: TimeScope) -> TimeScope:
        if self.clock is other.clock:
            return TimeScope(self.clock, self.window.meet(other.window))
        atlas = _ATLAS
        if atlas is not None and atlas.has(self.clock) and atlas.has(other.clock):
            # GC-4: both clocks are atlas-covered ⇒ pull each window back to the event level and
            # intersect (T₁ ⊓ T₂ = (N, p₁⁻¹(W₁) ∩ p₂⁻¹(W₂)); dn-global-event-clock §2.5). The
            # intersected event set is an opaque N-window token wrapped in the existing Window
            # grammar; the empty intersection is the EMPTY window, NEVER an error. This branch's
            # domain is EXACTLY the cross-clock path that raised below — no previously-legal (same-
            # clock) meet is touched, and with no atlas registered this is skipped entirely.
            token = atlas.intersect(atlas.pullback(self.clock, self.window),
                                    atlas.pullback(other.clock, other.window))
            return TimeScope(Clock.N,
                             Window.empty() if token is None else Window.interval(token, token))
        if common_refinement(self.clock, other.clock) is None:
            raise NoCommonClockError(
                f"no common materialized clock for {self.clock.value!r} ⊓ {other.clock.value!r} — "
                f"the canonical refinement N is parked (CS-a); a cross-clock meet is a constructor "
                f"error, not a silent guess (dn-capability-scope §2.2)"
            )
        # A materialized common refinement exists only for comparable clocks; transporting a window
        # ACROSS clocks is retrieval math (out of scope, §1). v1 declines it rather than guess.
        raise NoCommonClockError(
            f"cross-clock transport {self.clock.value!r} ⊓ {other.clock.value!r} is retrieval "
            f"math (out of scope); v1 meets only same-clock windows (dn-capability-scope §1/§2.2)"
        )

    def __le__(self, other: TimeScope) -> bool:
        """Same clock → window containment. Different clocks → conservatively not-⊑ (containment
        across clocks needs transport, declined in v1)."""
        if self.clock is not other.clock:
            return False
        return self.window <= other.window


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# A — authority = P × W_Σ × W_world (dn-capability-scope §2.1; fable pass S5)
# ═══════════════════════════════════════════════════════════════════════════════════════════════

class Privilege(IntEnum):
    """P — the advisory ladder. The model advises; code acts (non-negotiable #3). No rung above
    READ_PROPOSE exists: nothing here can *act*."""

    READ = 0
    READ_PROPOSE = 1


class WorldReach(IntEnum):
    """W_world — the effector blast-radius chain, WITH the `NONE` floor the note names (§2.1) that
    the code's `ReversibilityClass` (SENSING-floored, `ops/effects.py`) has no member for. `NONE`
    means "no world reach at all" — what every read-only View holds, and (finding-0011) the deployed
    ceiling `⊤_deployed.W_world = NONE`: no EffectView is wired at any tier. The `ReversibilityClass
    → WorldReach` bridge lives ops-side (`ops.effects.world_reach`) so it stays pure-core."""

    NONE = 0
    SENSING = 1
    REVERSIBLE = 2
    IRREVERSIBLE = 3


@dataclass(frozen=True)
class Authority:
    """`A = P × W_Σ × W_world` — a product of three chains. meet = min per chain (safe composition),
    join = max per chain (a widening), ⊑ = ≤ on all three. `W_Σ ∈ {0, 1}` is the projection-write
    bit (the sensor dual); it and W_world were the seed's single conflated "write" rung."""

    privilege: Privilege
    store_write: int          # W_Σ ∈ {0, 1} — projection-write into the scoped strata
    world: WorldReach         # W_world — the effector blast-radius ceiling

    def __post_init__(self) -> None:
        if self.store_write not in (0, 1):
            raise ValueError(f"W_Σ (store_write) must be 0 or 1, got {self.store_write!r}")

    @classmethod
    def read_only(cls) -> Authority:
        """`(READ, 0, NONE)` — the read-only authority every non-effector View holds (⊥ of A)."""
        return cls(Privilege.READ, 0, WorldReach.NONE)

    def meet(self, other: Authority) -> Authority:
        return Authority(
            Privilege(min(self.privilege, other.privilege)),
            min(self.store_write, other.store_write),
            WorldReach(min(self.world, other.world)),
        )

    def join(self, other: Authority) -> Authority:
        return Authority(
            Privilege(max(self.privilege, other.privilege)),
            max(self.store_write, other.store_write),
            WorldReach(max(self.world, other.world)),
        )

    def __le__(self, other: Authority) -> bool:
        return (self.privilege <= other.privilege
                and self.store_write <= other.store_write
                and self.world <= other.world)


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# Enforcement tier — an ANNOTATION, never a lattice element (dn-capability-scope §2.2)
# ═══════════════════════════════════════════════════════════════════════════════════════════════

class Tier(IntEnum):
    """The assurance strength of a scope's enforcement: `structural ≻ static+guard ≻ convention`.
    Composition takes the MIN along the construction chain — a convention-tier grant cannot launder
    through a structural wrapper. It is an annotation (min-composed), NOT part of ⊑, so it is
    `compare=False` on `Scope`."""

    CONVENTION = 0
    STATIC_GUARD = 1
    STRUCTURAL = 2


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# The scope object, its lattice, and the SLICE rule (dn-capability-scope §2.1/§2.2/§2.4)
# ═══════════════════════════════════════════════════════════════════════════════════════════════

class SliceError(ValueError):
    """A multi-stratum (`|Σ| > 1`) scope with a point window carries no consistent cut. Bare "now"
    is well-typed only single-stratum; across strata it needs an explicit cut (a vector-clock
    timestamp / causal-set antichain — the commit SHA is the cut for repo-backed strata,
    dn-capability-scope §2.2 SLICE rule)."""


# Clocks that intrinsically supply a consistent cut across repo-backed strata (the commit SHA IS the
# cut — this is why bp-035/037 route both Views through one `_resolve_default_commit`).
_CUT_CLOCKS: frozenset[Clock] = frozenset({Clock.COMMIT})


@dataclass(frozen=True)
class Scope:
    """`s = (Σ, E, T, A)` — a capability as a point in the bounded lattice. `tier` rides beside the
    four lattice coordinates as a min-composed annotation (`compare=False` — excluded from `==` and
    the lattice laws). `cut` is the explicit consistent cut a multi-stratum point-window scope must
    carry (the SLICE rule); single-stratum scopes need none.

    meet = safe composition (a delegated agent receives `meet(parent, template)`); join = a widening
    (grantable by a holder of the join); ⊑ = "no more authority than". A cross-clock meet raises
    `NoCommonClockError`; a cut-less multi-stratum point scope raises `SliceError`."""

    sigma: StratumScope
    edges: EdgeScope
    time: TimeScope
    authority: Authority
    tier: Tier = field(compare=False)
    cut: Hashable | None = field(default=None, compare=False)

    def __post_init__(self) -> None:
        if (len(self.sigma.strata) > 1
                and self.time.window.kind is WindowKind.POINT
                and self.time.clock not in _CUT_CLOCKS
                and self.cut is None):
            raise SliceError(
                f"a multi-stratum (|Σ|={len(self.sigma.strata)}) with a point window on clock "
                f"{self.time.clock.value!r} needs an explicit cut — bare 'now' is well-typed "
                f"only single-stratum (dn-capability-scope §2.2 SLICE rule)"
            )

    def meet(self, other: Scope) -> Scope:
        """Safe composition — componentwise meet; `tier` = min along the chain. Raises
        `NoCommonClockError` on a cross-clock T-meet. `meet(parent, template) ⊑ parent` always
        (monotone delegation — non-negotiable #6)."""
        return Scope(
            self.sigma.meet(other.sigma),
            self.edges.meet(other.edges),
            self.time.meet(other.time),
            self.authority.meet(other.authority),
            tier=Tier(min(self.tier, other.tier)),
            cut=self.cut if self.cut == other.cut else None,
        )

    def join(self, other: Scope) -> Scope:
        """A widening — componentwise join; `tier` = min along the chain (a join is no more assured
        than its weakest input). Grantable only by an authority already holding the join."""
        return Scope(
            self.sigma.join(other.sigma),
            self.edges.join(other.edges),
            TimeScope(self.time.clock, self.time.window.join(other.time.window))
            if self.time.clock is other.time.clock
            else _join_time_raise(self.time, other.time),
            self.authority.join(other.authority),
            tier=Tier(min(self.tier, other.tier)),
            cut=self.cut if self.cut == other.cut else None,
        )

    def __le__(self, other: Scope) -> bool:
        """`⊑` on the four coordinates ONLY (tier is an annotation, not a lattice element)."""
        return (self.sigma <= other.sigma
                and self.edges <= other.edges
                and self.time <= other.time
                and self.authority <= other.authority)


def _join_time_raise(a: TimeScope, b: TimeScope) -> TimeScope:
    """A join across clocks has the same partiality as a meet (no materialized common clock)."""
    raise NoCommonClockError(
        f"no common materialized clock for a join of {a.clock.value!r} and {b.clock.value!r} "
        f"(canonically N, parked — CS-a)"
    )


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# Firewalls as order-ideals (dn-capability-scope §2.2; fable pass S6)
# ═══════════════════════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class Ideal:
    """A firewall as an order-ideal over Σ: a grant is admissible for a class iff it meets the
    ideal at ⊥ (`s.sigma ∩ ι = ∅`). Firewalls are subtracted from scopes, not re-checked
    per query — the grantable lattice is the ideal-quotient."""

    name: str
    strata: frozenset[Stratum]

    def excludes(self, s: Scope) -> bool:
        """True iff `s ⊓ ι = ⊥` — `s` names no stratum in this ideal."""
        return not (s.sigma.strata & self.strata)


# 𝔇 — the foundation denylist, applicable ALWAYS: CONSTITUTION.md / eval/golden/** are ungrantable.
DENYLIST_IDEAL = Ideal(name="foundation-denylist", strata=frozenset({Stratum.FOUNDATION}))


def admissible(s: Scope, ideals: Iterable[Ideal]) -> bool:
    """`s` is admissible iff it meets every firewall ideal at ⊥ (§2.2). The mirror-payload
    firewall for non-exempt clients is expressible the same way (an ideal over the mirror stratum);
    its concrete stratum modeling is parked (MirrorView already enforces it structurally)."""
    return all(iota.excludes(s) for iota in ideals)


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# The query language — req() and the deployed top (dn-capability-scope §2.4)
# ═══════════════════════════════════════════════════════════════════════════════════════════════

# A declared TYPE scope (a View's `SCOPE` constant) names its clock and window SHAPE; the concrete
# anchor value is bound per-instance at `.over()`/`.project()`. `ANCHOR` is the symbolic unbound
# point anchor a class-level `SCOPE` carries in place of that not-yet-resolved value.
ANCHOR: str = "@anchor"


def req_admissible(required: Scope, granted: Scope) -> bool:
    """A query sentence `(verb, s)` is admissible iff `req(verb) ⊑ s_granted` (§2.4). Ill-scoped
    sentences are unrepresentable — this is the check a construction site makes; the five Views
    expose their `req(read)` as a `SCOPE` constant (retrofit, bp-039 Item 3)."""
    return required <= granted


# The deployed lattice top's world reach is NONE — no EffectView is wired at any tier (Track G's
# standing fact, finding-0011: `⊤_deployed.W_world = NONE`, not SENSING). A statement, tested in
# tests/unit/test_view_scopes.py, not a runtime gate.
DEPLOYED_WORLD_CEILING: WorldReach = WorldReach.NONE


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# The zone-boundary law — Σ-breadth ⊥ world-reach (dn-agentic-loop §2.3, gap G-D; bp-086 / AL-1)
# ═══════════════════════════════════════════════════════════════════════════════════════════════
#
# Bright lines 1–2 (CONSTITUTION / BUILD-SPEC §3) invert on the lattice: the component that reads
# broad PRIVATE data has no world reach; the component that touches the world never reads the vault.
# `dn-agentic-loop` §2.3 typed that inversion as ONE implication over a deployed grant s:
#
#     s.Σ ⊓ PRIVATE_STRATA ≠ ⊥   ⇒   s.A.W_world = NONE
#
# It is a CROSS-COORDINATE law (Σ × A), NOT a pure Σ-order-ideal — so it is deliberately NOT modeled
# as an `Ideal` (whose `.excludes` is Σ-only). It rides as a named set + predicate; the ratchet
# that makes it real (an adversarial hand-built violator is REFUSED) lives in test_scope.py
# (F-AL3). Today VACUOUSLY true — `⊤_deployed.W_world = NONE` (finding-0011) — so the predicate
# asserts a property the code already has by shape; the point is to make it a tested ratchet,
# not an accident, before any EffectView is ever wired.

# PRIVATE_STRATA — the corpus/vault side of R: every grantable stratum EXCEPT `world` (the sole
# public/effector coordinate). Derived from `⊤_Σ` (carries refinements too — a scope naming
# only `mirror_authored` still counts as private) minus WORLD; FOUNDATION (never grantable) and the
# HYPOTHETICAL overlay (never in an ordinary grant, and any real staged read composes with a durable
# private stratum that IS in this set) are excluded by construction. This is the WIDEST-exclusion /
# strongest-law default (plan §3 Q3): whether `ops`/`reference` ought to count as "private" for this
# law is an OWNER call at proposed→ready — the default keeps them IN (a leak passing is the unsafe
# direction; over-inclusion only over-constrains a not-yet-wired world reach).
PRIVATE_STRATA: frozenset[Stratum] = _downward_close(_BASE_STRATA - {Stratum.WORLD})


def zone_admissible(s: Scope) -> bool:
    """The G-D zone law as a predicate: True iff `s` does NOT read private strata OR has no world
    reach — i.e. `s.Σ ⊓ PRIVATE_STRATA ≠ ⊥ ⇒ s.A.W_world = NONE`. A grant with non-⊥ private Σ AND
    `W_world > NONE` is REFUSED (returns False); that is the constructable violation F-AL3 requires
    the ratchet to catch. `Σ = ⊥` (the executor) and `Σ = {world}` (world-only) pass at ANY reach —
    they read nothing private, so the antecedent is false (dn-agentic-loop §2.3)."""
    reads_private = bool(s.sigma.strata & PRIVATE_STRATA)
    return (not reads_private) or s.authority.world is WorldReach.NONE


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# Result typing — Inv vs Rate(κ), Rule CLOCK (dn-capability-scope §2.3; bp-039 Item 4)
# ═══════════════════════════════════════════════════════════════════════════════════════════════
#
# A query result is graded by clock-dependence, AHEAD of need (§2.3): the failure it forecloses — a
# drift *rate* read off an unacknowledged clock — is the A7 apophenia class, caught earlier.
# Every BUILT instrument is `Inv` (CoherenceReport returns a count + anchors and never divides);
# the first `Rate` inhabitant will be the R-ladder velocity (R1, dn-velocity-instruments).

@dataclass(frozen=True)
class Inv[T]:
    """An INVARIANT result — depends only on the window's event SET (counts, sets, booleans: β₁,
    ‖[d,τ]‖-as-count, connected sets, well-foundedness). Reparametrization-invariant: no clock
    index divides into it."""

    value: T


@dataclass(frozen=True)
class Rate[T]:
    """A RATE result — a difference quotient against a clock's index (severings per commit, events
    per wall-second, velocity ẇ). It carries its clock in its type and is NEVER a bare number — the
    `clock` field is required, so a clockless Rate is unconstructable (Rule CLOCK, structural)."""

    value: T
    clock: Clock


class ClockMismatchError(ValueError):
    """Rule CLOCK violated: a `Rate(κ)` result was requested under a scope not clocked on κ
    (dn-capability-scope §2.3). `q : s → Rate(κ)` requires `s.T.clock = κ`."""


def rate_under[T](value: T, *, scope: Scope, clock: Clock) -> Rate[T]:
    """Rule CLOCK as a checked constructor: a `Rate(κ)` is admissible only under a scope clocked on
    κ. Raises `ClockMismatchError` otherwise — a Rate can never be minted against a clock the scope
    does not acknowledge (the A7 guard, one type earlier)."""
    if scope.time.clock is not clock:
        raise ClockMismatchError(
            f"Rule CLOCK: a Rate on clock {clock.value!r} needs one clocked on {clock.value!r}, "
            f"but the scope is on {scope.time.clock.value!r} (dn-capability-scope §2.3)"
        )
    return Rate(value=value, clock=clock)


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# Resolution typing — Res(π), Rule SCALE (dn-resolution-result-typing §2.2; bp-054 / FB-2)
# ═══════════════════════════════════════════════════════════════════════════════════════════════
#
# A THIRD result grade beside Inv/Rate — the ratified amendment `dn-resolution-result-typing` to
# `dn-capability-scope` §2.3 (cited, never re-derived). A `Res(π)` is a value with NO clock but an
# irreducible dependence on a declared RESOLUTION RULER — the range and grid it was measured over
# (π). Where Inv sees one construction and Rate divides by an event-clock's index, `Res(π)` spans a
# parameter family none of whose members changes what the client sees: the capability-invisibility
# half (§2.2(ii)) is that π NEVER enters s = (Σ, E, T, A), never affects admissibility, and never
# composes under meet/join — a proof obligation discharged by NOT writing that code (this module
# stays vocabulary; nothing above changes). First inhabitant: `pers(χ) : Res(π_σ)` (dn-sigma-fibers
# §2.3, the sigma_persistence.* family registered in eval/harness/registry.py).

@dataclass(frozen=True)
class ResParam:
    """The RESOLUTION DESCRIPTOR π = (name, U, Γ): the parameter over (`"sigma"`, `"grain"`,
    `"depth"`, ...), its declared range `U = [lo, hi]` (the ruler — e.g. cosine ∈ [0.55, 0.75]), and
    its sampling `Γ` (`grid` — a grid id like `"Γ_21"` or an exact-partition tag like
    `"exact-partition"`). Frozen so a `Res`'s π is an immutable part of its identity — two `Res`
    values compare iff their π compare equal (`res_comparable`)."""

    name: str
    lo: float
    hi: float
    grid: str


@dataclass(frozen=True)
class Res[T]:
    """A RESOLUTION-GRADED result (Rule SCALE) — a measurement of variation across a declared family
    of constructions over one fixed event set. It carries π in its type and is NEVER a bare number:
    the `param` field is REQUIRED, so a π-less Res is unconstructable (the §2.2(i) carriage law,
    structural — mirroring `Rate`'s required `clock`). Comparable to another Res iff their π are
    identical (`res_comparable`); cross-π comparison without a declared transport is refused (RT-a —
    transport is parked, always a new measurement)."""

    value: T
    param: ResParam


def res_under[T](value: T, *, param: ResParam) -> Res[T]:
    """Rule SCALE (i) as a checked constructor — the `rate_under` analog: mint a `Res(π)` carrying
    its resolution descriptor. The carriage law is structural (`param` is required), so a Res can
    never be minted without its ruler; the round-tripping entry point instrument families call."""
    return Res(value=value, param=param)


def res_comparable(a: Res[Any], b: Res[Any]) -> bool:
    """Rule SCALE comparability: two `Res` values compare iff their π are IDENTICAL (same name, same
    declared range U, same grid Γ). Cross-π comparison without a declared transport is refused —
    RT-a, the CS-f conservatism ("re-binning … is a new measurement", dn-capability-scope:171)
    applied to rulers. π-identical only; nothing transports strengths across distinct rulers."""
    return a.param == b.param
