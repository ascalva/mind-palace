"""Unit tests for the GC-2 clock maps p_κ + N_s (dn-global-event-clock §2.3 laws C1–C4).

THESE ARE THE REAL FALSIFIERS. `tests/integrity/test_clock_laws.py` runs on the live stores, which
a fresh worktree lacks (`data/` absent) — there it passes TRIVIALLY and proves nothing. So the laws
are exercised HERE, on INJECTED fakes (in-memory stores + a synthetic commit map), where the poset
and the p_κ are both under full control:

  * C1 (monotone)      — `a ≼ b ⇒ p(a) ≤ p(b)`: a monotone injected commit map holds; an inverted
                         one is CAUGHT (the property test has teeth).
  * C2 (convex fibers) — `p_κ⁻¹(tick)` order-convex ("a commit is a RANGE of N"): a range-respecting
                         map is convex; a gap-skipping map ({A1,A3} skipping A2) is CAUGHT.
  * C3 (frontier borrow) — read-clock ticks equal the observed per-store write frontier.
  * C4 (wall excluded)  — `p(WALL, …)` / `fiber(WALL, …)` RAISE; no p_wall exists.
  * proper_time         — finding-0090: EXACT (== event count) ONLY on a total chain; every
                         cross-chain / cross-stratum / concurrent pair returns chain_complete=False.
"""

from __future__ import annotations

import random
from collections.abc import Hashable
from pathlib import Path

import pytest

from core.complex_types import EdgeSign
from core.scope import Clock
from core.stores.derived import DerivedStore
from core.stores.edges import EdgeStore
from core.stores.runledger import RunLedger
from core.stores.versions import VersionStore
from core.temporal.spine import Order, Spine, SpineEvent, SpineSources
from eval.harness.store import EvalKey, EvalResultsStore, Reading

_MEM = Path(":memory:")
_READ_CLOCKS = (Clock.PROJECTION_EVENT, Clock.LAST_WRITE, Clock.NOW)


def _find_ref(spine: Spine, store: str, ident: str) -> SpineEvent:
    return next(e for e in spine.events() if e.store == store and ident in e.refs)


def _chain_spine() -> tuple[Spine, str, str, str]:
    """versions docA: v1 ≺ v2 ≺ v3 (a single total chain) — the cleanest C2/C1 fixture."""
    vs = VersionStore(_MEM)
    vs.record("docA", "digA1")
    vs.record("docA", "digA2")
    vs.record("docA", "digA3")
    spine = Spine.derive(SpineSources(versions=vs))
    return spine, "versions:docA:1", "versions:docA:2", "versions:docA:3"


# ── C4 — wall generates nothing; p/fiber RAISE ─────────────────────────────────────────────────


def test_c4_wall_has_no_p_and_no_fiber() -> None:
    spine, a1, _a2, _a3 = _chain_spine()
    with pytest.raises(ValueError, match="Law C4"):
        spine.p(Clock.WALL, a1)
    with pytest.raises(ValueError, match="Law C4"):
        spine.fiber(Clock.WALL, 0)


# ── N and N_S — the finest clocks (identity / per-stratum), singleton fibers ─────────────────────


def test_n_is_identity_with_singleton_fibers() -> None:
    spine, a1, a2, _a3 = _chain_spine()
    assert spine.p(Clock.N, a1) == a1                       # p_N(e) = e
    assert spine.fiber(Clock.N, a1) == [a1]                 # singleton ⇒ trivially convex (C2)
    assert spine.is_fiber_convex(Clock.N, a1)
    # identity preserves ≼ (C1): a1 ≺ a2 stays a1 ≺ a2 under p_N
    assert spine.order(spine.p(Clock.N, a1), spine.p(Clock.N, a2)) is Order.BEFORE  # type: ignore[arg-type]


def test_n_s_is_the_per_stratum_event_tick() -> None:
    spine, a1, _a2, _a3 = _chain_spine()
    ev = spine._events[a1]
    assert spine.p(Clock.N_S, a1) == (ev.stratum, a1)       # (stratum, event) — per-stratum tick
    assert spine.fiber(Clock.N_S, (ev.stratum, a1)) == [a1]
    assert spine.is_fiber_convex(Clock.N_S, (ev.stratum, a1))


# ── C3 — read-clocks borrow the observed per-store write frontier ───────────────────────────────


def test_c3_read_clocks_borrow_the_write_frontier() -> None:
    vs = VersionStore(_MEM)
    vs.record("docA", "a1")
    vs.record("docA", "a2")
    vs.record("docB", "b1")
    spine = Spine.derive(SpineSources(versions=vs))
    assert spine.frontier_at("versions") == 2               # max position across the store's chains
    # every read-clock ticks at the store frontier, for every event in the store (C3, no mint)
    for clock in _READ_CLOCKS:
        for eid in ("versions:docA:1", "versions:docA:2", "versions:docB:1"):
            assert spine.p(clock, eid) == 2


def test_frontier_at_is_zero_for_absent_or_chainless_store() -> None:
    es = EvalResultsStore(_MEM)                             # chain-less (position=None) events only
    es.put(Reading(key=EvalKey("s", "c", "cfg", 1), metric_name="m", value=1.0, type_tag="Inv"))
    spine = Spine.derive(SpineSources(eval=es))
    assert spine.frontier_at("eval") == 0                   # chain-less ⇒ no frontier
    assert spine.frontier_at("nonesuch") == 0               # absent store ⇒ 0


# ── C1 (monotone) + C2 (convex fibers) on COMMIT — the injected-map falsifiers ──────────────────


def _c1_holds_int_clock(spine: Spine, clock: Clock) -> bool:
    """C1 for an int-tick clock: `a ≼ b ⇒ tick(a) ≤ tick(b)` over the clock's (partial) domain."""
    ticks: dict[str, Hashable] = {}
    for e in spine.events():
        try:
            ticks[e.event_id] = spine.p(clock, e.event_id)
        except ValueError:
            pass                                            # event not in this clock's domain
    for a in ticks:
        for b in ticks:
            if a != b and spine.order(a, b) is Order.BEFORE and ticks[a] > ticks[b]:  # type: ignore[operator]
                return False
    return True


def test_commit_uninjected_raises() -> None:
    spine, a1, _a2, _a3 = _chain_spine()
    with pytest.raises(ValueError, match="sourced|not materialized"):
        spine.p(Clock.COMMIT, a1)
    with pytest.raises(ValueError, match="not materialized"):
        spine.fiber(Clock.COMMIT, 1)


def test_c1_monotone_commit_map_holds_but_inversion_is_caught() -> None:
    spine, a1, a2, a3 = _chain_spine()
    good = Spine.derive(  # commit ticks non-decreasing along the chain a1 ≺ a2 ≺ a3
        SpineSources(versions=_reseed_chain()),
        coarsening_ticks={Clock.COMMIT: {a1: 1, a2: 1, a3: 2}},
    )
    assert _c1_holds_int_clock(good, Clock.COMMIT)          # monotone ⇒ C1 holds
    bad = Spine.derive(  # an EARLIER event given a LATER commit tick — C1 violated
        SpineSources(versions=_reseed_chain()),
        coarsening_ticks={Clock.COMMIT: {a1: 2, a2: 1, a3: 1}},
    )
    assert not _c1_holds_int_clock(bad, Clock.COMMIT)       # the falsifier bites


def test_c2_range_map_is_convex_but_a_gap_skipping_map_is_caught() -> None:
    spine, a1, a2, a3 = _chain_spine()
    convex = Spine.derive(  # fibers are contiguous ranges of the chain: {a1,a2} then {a3}
        SpineSources(versions=_reseed_chain()),
        coarsening_ticks={Clock.COMMIT: {a1: 1, a2: 1, a3: 2}},
    )
    assert convex.fiber(Clock.COMMIT, 1) == [a1, a2]
    assert convex.is_fiber_convex(Clock.COMMIT, 1)          # a range ⇒ convex
    assert convex.is_fiber_convex(Clock.COMMIT, 2)
    # tick 1 = {a1, a3} SKIPS a2 (a1 ≺ a2 ≺ a3) — a commit that is NOT a range of N
    nonconvex = Spine.derive(
        SpineSources(versions=_reseed_chain()),
        coarsening_ticks={Clock.COMMIT: {a1: 1, a2: 2, a3: 1}},
    )
    assert nonconvex.fiber(Clock.COMMIT, 1) == [a1, a3]
    assert not nonconvex.is_fiber_convex(Clock.COMMIT, 1)   # C2 broken ⇒ the falsifier bites


def _reseed_chain() -> VersionStore:
    vs = VersionStore(_MEM)
    vs.record("docA", "digA1")
    vs.record("docA", "digA2")
    vs.record("docA", "digA3")
    return vs


def test_c1_c2_hold_for_randomized_monotone_commit_maps() -> None:
    """Randomized: on a linear chain, ANY non-decreasing tick assignment satisfies C1 AND every
    fiber is convex (a range). The plan's "randomized event pairs satisfy C1/C2" for a real p_κ."""
    rng = random.Random(0xC10C)
    a1, a2, a3 = "versions:docA:1", "versions:docA:2", "versions:docA:3"
    for _ in range(50):
        t1 = rng.randint(0, 3)
        t2 = rng.randint(t1, t1 + 3)                        # non-decreasing along the chain
        t3 = rng.randint(t2, t2 + 3)
        spine = Spine.derive(
            SpineSources(versions=_reseed_chain()),
            coarsening_ticks={Clock.COMMIT: {a1: t1, a2: t2, a3: t3}},
        )
        assert _c1_holds_int_clock(spine, Clock.COMMIT)
        for tick in {t1, t2, t3}:
            assert spine.is_fiber_convex(Clock.COMMIT, tick)


def test_commit_p_is_partial_over_ev_only_repo_backed_events() -> None:
    """p_commit is defined only on injected (repo-backed) events; asking for a non-repo event's
    commit tick RAISES — honest partiality, never a fabricated tick. fiber ranges only the map."""
    vs = VersionStore(_MEM)
    vs.record("docX", "DIG")
    led = RunLedger(_MEM)
    run_id = led.start_run(pipeline="dream_v2", config_fingerprint="cf", corpus_digest="cd",
                           node_count=1, edge_count=0, duration_s=0.1, spectral_stats={})
    led.add_claim(run_id, kind="tension", confidence=0.5, support=("DIG",), surface_text="t",
                  polarity="-")
    version_ev = "versions:docX:1"
    spine = Spine.derive(SpineSources(versions=vs, ledger=led),
                         coarsening_ticks={Clock.COMMIT: {version_ev: 7}})
    assert spine.p(Clock.COMMIT, version_ev) == 7
    claim_ev = _find_ref(spine, "runledger", "DIG")        # a run/claim event has no commit tick
    with pytest.raises(ValueError, match="no p_κ tick"):
        spine.p(Clock.COMMIT, claim_ev.event_id)
    assert spine.fiber(Clock.COMMIT, 7) == [version_ev]    # fiber ranges the injected map only


# ── proper_time — the finding-0090 discipline ───────────────────────────────────────────────────


def test_proper_time_is_exact_on_a_total_chain() -> None:
    spine, a1, a2, a3 = _chain_spine()
    assert spine.proper_time(a1, a1) == (1, True)          # trivial 1-chain
    assert spine.proper_time(a1, a2) == (2, True)          # v1 ≺ v2 — exact
    assert spine.proper_time(a1, a3) == (3, True)          # v1 ≺ v2 ≺ v3 — count == chain length
    assert spine.proper_time(a3, a1) == (3, True)          # magnitude is symmetric


def test_proper_time_cross_doc_same_stratum_is_never_exact() -> None:
    """finding-0090's headline: a per-DOC pair across docs (same stratum, different chains) must NOT
    report an exact proper time — they are concurrent, on no single chain."""
    vs = VersionStore(_MEM)
    vs.record("docA", "a1")
    vs.record("docA", "a2")
    vs.record("docB", "b1")
    spine = Spine.derive(SpineSources(versions=vs))
    length, complete = spine.proper_time("versions:docA:2", "versions:docB:1")
    assert complete is False                               # cross-chain ⇒ chain_complete=False
    assert length == 0                                     # concurrent ⇒ no chain connects them


def test_proper_time_cross_stratum_pair_is_never_chain_complete() -> None:
    """A causally-comparable but cross-stratum pair (a version ≺ a claim that consumes its digest)
    is a valid causal order, but proper time is per-stratum/per-chain — chain_complete MUST be
    False (never conflate a cross-stratum count with a proper time)."""
    vs = VersionStore(_MEM)
    vs.record("noteX", "DIG")
    led = RunLedger(_MEM)
    run_id = led.start_run(pipeline="dream_v2", config_fingerprint="cf", corpus_digest="cd",
                           node_count=1, edge_count=0, duration_s=0.1, spectral_stats={})
    led.add_claim(run_id, kind="tension", confidence=0.5, support=("DIG",), surface_text="t",
                  polarity="-")
    spine = Spine.derive(SpineSources(versions=vs, ledger=led))
    v = _find_ref(spine, "versions", "DIG")                # mirror stratum
    claim = _find_ref(spine, "runledger", "DIG")           # ops stratum
    assert spine.order(v.event_id, claim.event_id) is Order.BEFORE
    _length, complete = spine.proper_time(v.event_id, claim.event_id)
    assert complete is False                               # cross-stratum ⇒ never chain_complete


def test_proper_time_comparable_but_nontotal_interval_is_flagged() -> None:
    """The subtle finding-0090 confound: a ≺ b within ONE stratum but with concurrent events in the
    causal interval (a diamond). The bare interval COUNT (4) is NOT the proper time (3): chain
    length < interval size, so chain_complete=False — the count is never sold as proper time."""
    ds = DerivedStore(_MEM)                                # all "interpreted" stratum, g2 DAG
    # distinct content ⇒ distinct content-addressed ids (id is keyed on kind/summary/subjects)
    a = ds.add(kind="dream", summary="root", subjects=("A",), derived_from=("SEED",))
    c = ds.add(kind="dream", summary="left", subjects=("C",), derived_from=(a.id,))
    d = ds.add(kind="dream", summary="right", subjects=("D",), derived_from=(a.id,))
    b = ds.add(kind="finding", summary="sink", subjects=("B",), derived_from=(c.id, d.id))
    spine = Spine.derive(SpineSources(derived=ds))
    a_ev = next(iter(spine.producers_of({a.id})))
    b_ev = next(iter(spine.producers_of({b.id})))
    length, complete = spine.proper_time(a_ev, b_ev)
    assert length == 3                                     # longest chain a ≺ c ≺ b (or a ≺ d ≺ b)
    assert complete is False                               # interval {a,c,d,b} is not total (c ∥ d)


def test_proper_time_concurrent_pair_reports_no_chain() -> None:
    vs = VersionStore(_MEM)
    vs.record("doc", "DV")
    es = EdgeStore(_MEM)                                    # a different stratum, no shared ident
    e = es.add("uu", "vv", sign=EdgeSign.SUPPORT, rel_type="supports")
    spine = Spine.derive(SpineSources(versions=vs, edges=es))
    v = _find_ref(spine, "versions", "DV")
    edge_ev = _find_ref(spine, "edges", e.edge_id)
    assert spine.order(v.event_id, edge_ev.event_id) is Order.CONCURRENT
    assert spine.proper_time(v.event_id, edge_ev.event_id) == (0, False)


def test_proper_time_unknown_event_raises() -> None:
    spine, a1, _a2, _a3 = _chain_spine()
    with pytest.raises(KeyError):
        spine.proper_time(a1, "versions:ghost:9")


# ── n_s — the N_s object (an alias of restrict) partitions by stratum tag ───────────────────────


def test_n_s_partitions_events_by_stratum() -> None:
    vs = VersionStore(_MEM)                                # mirror
    vs.record("doc", "d")
    es = EdgeStore(_MEM)                                   # interpreted
    es.add("u", "v", sign=EdgeSign.CONTRADICT, rel_type="contradicts")
    spine = Spine.derive(SpineSources(versions=vs, edges=es))
    mirror = spine.n_s("mirror")
    assert {e.store for e in mirror.events()} == {"versions"}
    assert all(e.stratum == "mirror" for e in mirror.events())
    # n_s is exactly restrict — same events
    restricted = spine.restrict("mirror")
    assert [e.event_id for e in mirror.events()] == [e.event_id for e in restricted.events()]
