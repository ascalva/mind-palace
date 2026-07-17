# ── GC-4 · the concrete clock atlas over the derived spine (dn-global-event-clock §2.5) ──────────
# OBJECT:    SpineAtlas — the `core.scope.ClockAtlas` backed by the spine's p_κ (bp-053). It pulls a
#            window over any spine-materialized clock back to the event level (`p_κ⁻¹(W)`) and meets
#            those pullbacks AS EVENT SETS — the machinery `TimeScope.meet` consults for the
#            cross-clock T-meet completion (the CS-a unpark, note §2.5 / plan §6).
# INVARIANT: this module imports stores (via the spine); `core/scope.py` stays pure-core and imports
#            the Protocol ONLY, never THIS (the pure-core seam, plan §3). The N-window token is the
#            pulled-back EVENT SET as a `frozenset[str]` of event_ids — the v1 opaque, hashable form
#            of CS-b's antichain window (plan §11); intersection is set intersection; the empty set
#            is the EMPTY window. Read-only: no store write handle, no model, no socket.
# ENFORCED:  static (core.* strict mypy) + the cross-clock property tests in
#            tests/unit/test_tmeet_completion.py (pullback == hand-enumerated fiber intersection;
#            commutativity / associativity on covered triples; wall/now REFUSE).
"""The concrete clock atlas — `SpineAtlas`, the injectable pullback the T-meet totalizes through.

Register with `core.scope.register_atlas(SpineAtlas(spine))` after building the spine. `has(clock)`
reports whether a window over that clock can be pulled back to N (wall/now are exogenous — no `p_κ`;
the repo-backed coarsenings are covered only once their external ticks are injected, bp-053);
`pullback(clock, window)` returns the pulled-back event set `p_κ⁻¹(W)`; `intersect` meets two such
sets. Scope.py wraps a non-empty token as a degenerate interval `[S, S]` over `Clock.N` (the
cut-pair window of note §2.5, opaque in v1) and an empty one as the EMPTY window.
"""

from __future__ import annotations

from collections.abc import Hashable
from typing import cast

from core.scope import Clock, Window, WindowKind
from core.temporal.spine import Spine

# Exogenous coordinates with no `p_κ` over Ev: `wall` (Law C4 — generates no event order) and `now`
# (the live-present anchor — no fixed event set). A cross-clock meet touching either stays the
# honest partial-meet error `NoCommonClockError` (note §2.5: "wall ⊓ anything remains an error").
_EXOGENOUS: frozenset[Clock] = frozenset({Clock.WALL, Clock.NOW})

# Clocks whose `p_κ` is materialized ONLY when external ticks are injected (the repo-backed
# coarsenings — a commit SHA / content snapshot the spine never sources itself, §2.10 / bp-053).
_INJECTED: frozenset[Clock] = frozenset({Clock.COMMIT, Clock.DISTINCT_SNAPSHOT})

# A sentinel tick that no real `p_κ` value equals — probes `fiber` for materialization WITHOUT
# reaching into spine internals (`fiber` raises for an un-materialized coarsening, returns [] here).
_PROBE: Hashable = object()


class SpineAtlas:
    """A `core.scope.ClockAtlas` backed by a derived `Spine` (bp-053's `p_κ`). Holds a read-only
    spine handle and computes pullbacks by coarsening every event through `spine.p` (`ClockAtlas` is
    a structural Protocol — no explicit subclassing needed; mypy checks the three methods match)."""

    def __init__(self, spine: Spine) -> None:
        self._spine = spine

    def has(self, clock: Clock) -> bool:
        """True iff a window over `clock` can be pulled back to N. Wall/now are exogenous (no
        `p_κ`); the repo-backed coarsenings are covered only once their ticks are injected —
        otherwise the meet stays an honest error rather than silently returning an empty pullback
        (a covert guess). N / N_s / the read-clocks always have a `p_κ` over the spine."""
        if clock in _EXOGENOUS:
            return False
        if clock in _INJECTED:
            try:
                self._spine.fiber(clock, _PROBE)      # raises iff the coarsening is un-materialized
            except ValueError:
                return False
            return True
        return True

    def pullback(self, clock: Clock, window: Window) -> Hashable:
        """`p_κ⁻¹(W)` — the event set (a `frozenset[str]`) of events whose `p_κ` tick lies in `W`.
        Events outside `dom(p_κ)` (e.g. a non-repo event under COMMIT) are honestly ABSENT, never
        fabricated. An N-window `W` (an event-set interval `[S, S]`, wrapped by scope.py) pulls back
        to its OWN set — so re-meeting an already-computed N-window recovers it (associativity)."""
        out: set[str] = set()
        for ev in self._spine.events():
            try:
                tick = self._spine.p(clock, ev.event_id)
            except (ValueError, KeyError):
                continue                              # ev ∉ dom(p_κ): not in the pullback (honest)
            if _in_window(tick, window):
                out.add(ev.event_id)
        return frozenset(out)

    def intersect(self, a: Hashable, b: Hashable) -> Hashable | None:
        """Meet two N-window tokens as event sets; the empty intersection is `None` (⇒ EMPTY)."""
        inter = cast("frozenset[str]", a) & cast("frozenset[str]", b)
        return inter if inter else None


def _in_window(tick: Hashable, window: Window) -> bool:
    """Is a `p_κ` tick inside window `W`? ALL ⇒ always; EMPTY ⇒ never; an N-window (a frozenset-
    bounded interval — the event set `[S, S]`) ⇒ set membership; a POINT ⇒ equality; an int-bounded
    interval ⇒ inclusive range; any other opaque interval ⇒ conservative endpoint membership (opaque
    bounds are not orderable, mirroring `Window`'s own conservatism — never over-includes)."""
    if window.kind is WindowKind.EMPTY:
        return False
    if window.kind is WindowKind.ALL:
        return True
    lo, hi = window.lo, window.hi
    if isinstance(lo, frozenset):                     # an N-window token: the event set [S, S]
        return tick in lo
    if window.kind is WindowKind.POINT:
        return tick == lo
    if isinstance(tick, int) and isinstance(lo, int) and isinstance(hi, int):
        return lo <= tick <= hi
    return tick == lo or tick == hi
