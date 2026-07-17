"""GC-4 — the T-meet completion (bp-056, dn-global-event-clock §2.5).

The completed cross-clock `TimeScope.meet`: with a `ClockAtlas` registered, two covered clocks meet
by pulling each window back to the event level and intersecting (`T₁ ⊓ T₂ = (N, p₁⁻¹(W₁) ∩
p₂⁻¹(W₂))`); WITHOUT one, and for exogenous clocks (wall / now), the honest partial-meet error
stands. The lattice-law falsifier — every previously-legal (same-clock) meet stays bit-identical —
lives in `tests/unit/test_scope.py` (unedited, the owner's ratification condition); THIS file adds
the new-path coverage: the seam's default-off honesty, the `SpineAtlas` pullback math against
hand-enumerated fibers, and commutativity / associativity on atlas-covered triples.

These tests register a process-wide atlas, so an autouse fixture RESETS it to `None` around each one
— otherwise a leaked atlas would make test_scope.py's cross-clock-raises falsifier compute instead.
"""

from __future__ import annotations

import itertools
from collections.abc import Iterator
from pathlib import Path

import pytest

from core.scope import (
    Clock,
    NoCommonClockError,
    TimeScope,
    Window,
    WindowKind,
    register_atlas,
)
from core.stores.runledger import RunLedger
from core.stores.versions import VersionStore
from core.temporal.atlas import SpineAtlas, _in_window
from core.temporal.spine import Spine, SpineSources

_MEM = Path(":memory:")

# The three repo-backed version events docA:{1,2,3} (stratum "mirror"), with injected coarsening
# ticks: commit fibers {A1,A2}→1, {A3}→2 (a commit is a RANGE); distinct-snapshot {A1}→s1,
# {A2,A3}→s2. The run+claim events (stratum "ops", store "runledger") carry NO commit/snapshot tick.
_A1, _A2, _A3 = "versions:docA:1", "versions:docA:2", "versions:docA:3"
_VERSIONS = frozenset({_A1, _A2, _A3})


def _seed_spine() -> Spine:
    vs = VersionStore(_MEM)
    vs.record("docA", "digA1")
    vs.record("docA", "digA2")
    vs.record("docA", "digA3")
    led = RunLedger(_MEM)
    run_id = led.start_run(pipeline="dream_v2", config_fingerprint="cf", corpus_digest="cd",
                           node_count=1, edge_count=0, duration_s=0.1, spectral_stats={})
    led.add_claim(run_id, kind="tension", confidence=0.5, support=("digA1",),
                  surface_text="t", polarity="-")
    return Spine.derive(
        SpineSources(versions=vs, ledger=led),
        coarsening_ticks={
            Clock.COMMIT: {_A1: 1, _A2: 1, _A3: 2},
            Clock.DISTINCT_SNAPSHOT: {_A1: "s1", _A2: "s2", _A3: "s2"},
        },
    )


@pytest.fixture(autouse=True)
def _isolate_atlas() -> Iterator[None]:
    """No test may leak an atlas — test_scope.py's falsifier depends on `_ATLAS is None`."""
    register_atlas(None)
    yield
    register_atlas(None)


# ── Item 1 — the seam is honest OFF by default; legal meets are bit-identical ────────────────────


def test_default_atlas_is_none_so_cross_clock_still_raises() -> None:
    """The ship default (`_ATLAS is None`): a cross-clock meet is the partial-meet constructor
    error, the same error type as before GC-4 — no silent guess."""
    with pytest.raises(NoCommonClockError):
        TimeScope(Clock.COMMIT, Window.all()).meet(TimeScope(Clock.N_S, Window.all()))


def test_same_clock_meet_is_bit_identical_with_and_without_atlas() -> None:
    """The cardinal falsifier, on a same-clock (previously-legal) meet: registering an atlas changes
    NOTHING — the atlas branch is reached only cross-clock."""
    a = TimeScope(Clock.COMMIT, Window.interval(0, 10))
    b = TimeScope(Clock.COMMIT, Window.interval(4, 20))
    expected = TimeScope(Clock.COMMIT, Window.interval(4, 10))
    register_atlas(None)
    without = a.meet(b)
    register_atlas(SpineAtlas(_seed_spine()))
    with_atlas = a.meet(b)
    assert without == with_atlas == expected


def test_clearing_the_atlas_restores_the_partial_meet() -> None:
    register_atlas(SpineAtlas(_seed_spine()))
    assert TimeScope(Clock.COMMIT, Window.all()).meet(
        TimeScope(Clock.N_S, Window.all())).clock is Clock.N
    register_atlas(None)
    with pytest.raises(NoCommonClockError):
        TimeScope(Clock.COMMIT, Window.all()).meet(TimeScope(Clock.N_S, Window.all()))


# ── Item 2 — SpineAtlas coverage + the pullback math ─────────────────────────────────────────────


def test_exogenous_clocks_are_never_covered() -> None:
    """wall (Law C4 — no `p_κ`) and now (the live-present anchor) are exogenous; the event clocks
    and read-clocks are covered, and the repo-backed coarsenings are covered once injected."""
    atlas = SpineAtlas(_seed_spine())
    assert not atlas.has(Clock.WALL)
    assert not atlas.has(Clock.NOW)
    assert atlas.has(Clock.N)
    assert atlas.has(Clock.N_S)
    assert atlas.has(Clock.COMMIT)
    assert atlas.has(Clock.DISTINCT_SNAPSHOT)


def test_pullback_equals_hand_enumerated_fiber() -> None:
    """The Item-2 falsifier: `atlas.pullback` must agree with the spine's own hand-enumerable fiber
    (bp-053's `p_κ` oracle) — a disagreement is a pullback bug."""
    atlas = SpineAtlas(_seed_spine())
    assert atlas.pullback(Clock.COMMIT, Window.interval(1, 1)) == frozenset({_A1, _A2})
    assert atlas.pullback(Clock.COMMIT, Window.all()) == _VERSIONS       # only repo-backed events
    assert atlas.pullback(Clock.COMMIT, Window.interval(1, 1)) == frozenset(
        _seed_spine().fiber(Clock.COMMIT, 1))                            # cross-check the oracle


def test_commit_meet_ns_is_the_pullback_intersection() -> None:
    """`commit ⊓ N_s` computes the pullback intersection; the result's event set == the
    hand-computed one. N_s covers every event, so the meet is exactly commit's repo-backed events —
    the ops run/claim events (no commit tick) are honestly excluded."""
    register_atlas(SpineAtlas(_seed_spine()))
    result = TimeScope(Clock.COMMIT, Window.all()).meet(TimeScope(Clock.N_S, Window.all()))
    assert result.clock is Clock.N
    assert result.window.kind is WindowKind.INTERVAL
    assert result.window.lo == _VERSIONS
    assert result.window.lo == result.window.hi                          # the [S, S] cut-pair form


def test_commit_subwindow_selects_a_subrange() -> None:
    register_atlas(SpineAtlas(_seed_spine()))
    result = TimeScope(Clock.COMMIT, Window.interval(1, 1)).meet(
        TimeScope(Clock.N_S, Window.all()))
    assert result.clock is Clock.N
    assert result.window.lo == frozenset({_A1, _A2})                     # commit fiber 1 = {A1, A2}


def test_wall_and_now_meets_raise_even_with_an_atlas() -> None:
    """`wall ⊓ anything` (and `now ⊓ anything`) stays an error — the honesty survives where it is
    still due (note §2.5); an exogenous clock is not atlas-covered, so the partial path holds."""
    register_atlas(SpineAtlas(_seed_spine()))
    for exo in (Clock.WALL, Clock.NOW):
        with pytest.raises(NoCommonClockError):
            TimeScope(exo, Window.all()).meet(TimeScope(Clock.COMMIT, Window.all()))
        with pytest.raises(NoCommonClockError):
            TimeScope(Clock.COMMIT, Window.all()).meet(TimeScope(exo, Window.all()))


def test_empty_intersection_is_the_empty_window_never_an_error() -> None:
    """Disjoint pullbacks yield the EMPTY window, not an exception (`intersect` → None ⇒ EMPTY)."""
    register_atlas(SpineAtlas(_seed_spine()))
    commit_1 = TimeScope(Clock.COMMIT, Window.interval(1, 1))            # {A1, A2}
    ns_a3 = TimeScope(Clock.N_S, Window.point(("mirror", _A3)))          # {A3} — disjoint
    result = commit_1.meet(ns_a3)
    assert result.clock is Clock.N
    assert result.window.kind is WindowKind.EMPTY


def test_uninjected_commit_is_uncovered_and_meet_refuses() -> None:
    """Honesty over silence: without injected commit ticks the clock is un-materialized, so `has`
    is False and the meet RAISES rather than reporting an empty pullback (a covert guess)."""
    vs = VersionStore(_MEM)
    vs.record("d", "x")
    atlas = SpineAtlas(Spine.derive(SpineSources(versions=vs)))          # no coarsening ticks
    assert atlas.has(Clock.N_S)
    assert not atlas.has(Clock.COMMIT)
    register_atlas(atlas)
    with pytest.raises(NoCommonClockError):
        TimeScope(Clock.COMMIT, Window.all()).meet(TimeScope(Clock.N_S, Window.all()))


# ── Item 2 — the algebra: commutative and associative on atlas-covered scopes ────────────────────


def _covered_scopes() -> list[TimeScope]:
    return [
        TimeScope(Clock.COMMIT, Window.all()),
        TimeScope(Clock.COMMIT, Window.interval(1, 1)),
        TimeScope(Clock.N_S, Window.all()),
        TimeScope(Clock.N, Window.all()),
        TimeScope(Clock.DISTINCT_SNAPSHOT, Window.all()),
    ]


def test_meet_is_commutative_on_covered_scopes() -> None:
    register_atlas(SpineAtlas(_seed_spine()))
    for a, b in itertools.combinations(_covered_scopes(), 2):
        assert a.meet(b) == b.meet(a)


def test_meet_is_associative_on_covered_triples() -> None:
    register_atlas(SpineAtlas(_seed_spine()))
    for a, b, c in itertools.combinations(_covered_scopes(), 3):
        assert a.meet(b).meet(c) == a.meet(b.meet(c))


# ── the pullback membership predicate (unit-level, no atlas) ─────────────────────────────────────


def test_in_window_predicate() -> None:
    assert _in_window(7, Window.all())
    assert not _in_window(7, Window.empty())
    assert _in_window(5, Window.interval(4, 8))
    assert not _in_window(9, Window.interval(4, 8))
    assert _in_window("x", Window.point("x"))
    assert not _in_window("y", Window.point("x"))
    n_window = Window.interval(frozenset({"e1", "e2"}), frozenset({"e1", "e2"}))
    assert _in_window("e1", n_window)                                    # N-window ⇒ set membership
    assert not _in_window("e3", n_window)
