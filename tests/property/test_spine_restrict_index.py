"""`Spine.restrict` by the reachability index equals `restrict` by the closure (packaging
prototype, docs/experiments/profile-2026-11-06.md): on random spines, for every stratum, the same
events, the same closed adjacency, the same generator edges, and the same `order`, `proper_time`
and `report`. The closure version stays in the module as the oracle (`_restrict_by_closure`)."""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from core.temporal.spine import Spine, SpineEdge, SpineEvent

STRATA = ("mirror", "ops", "interpreted", "observed", "eval")


def _spine(n: int, strata: list[str], edges: set[tuple[int, int]], chains: list[int]) -> Spine:
    """n events numbered in a topological order; an edge i -> j only for i < j; event i sits in
    chain `chains[i]` (consecutive events of a chain are joined, g1) and has stratum strata[i]."""
    ids = [f"e{i}" for i in range(n)]
    last: dict[int, int] = {}
    pos: dict[int, int] = {}
    direct = {e for e in edges if e[0] < e[1]}
    for i in range(n):
        c = chains[i]
        if c in last:
            direct.add((last[c], i))
        last[c] = i
        pos[i] = sum(1 for k in range(i) if chains[k] == c)
    succ: dict[str, set[str]] = {e: set() for e in ids}
    for a, b in direct:
        succ[ids[a]].add(ids[b])
    events = {ids[i]: SpineEvent(ids[i], f"s{chains[i]}", strata[i], pos[i], ()) for i in range(n)}
    gens = tuple(SpineEdge(ids[a], ids[b], "g1" if chains[a] == chains[b] else "g2")
                 for a, b in sorted(direct))
    produced = {f"x{i}": {ids[i]} for i in range(n)}
    chain_of = {ids[i]: f"s{chains[i]}:k" for i in range(n)}
    return Spine(_events=events, _succ=succ, _chain_of=chain_of, _gen_edges=gens,
                 _produced_by=produced, _present=("versions",), _refs_without_producer=0)


@st.composite
def spines(draw: st.DrawFn) -> Spine:
    n = draw(st.integers(1, 28))
    strata = draw(st.lists(st.sampled_from(STRATA), min_size=n, max_size=n))
    chains = draw(st.lists(st.integers(0, 4), min_size=n, max_size=n))
    edges = draw(st.sets(st.tuples(st.integers(0, n - 1), st.integers(0, n - 1)), max_size=2 * n))
    return _spine(n, strata, edges, chains)


def _closed(sp: Spine) -> dict[str, set[str]]:
    return {e: set(sp._succ.get(e, set())) for e in sp._events}


@given(spines())
@settings(max_examples=300, deadline=None)
def test_the_index_restriction_equals_the_closure_restriction(sp: Spine) -> None:
    for stratum in STRATA:
        new, old = sp.restrict(stratum), sp._restrict_by_closure(stratum)
        assert {e.event_id for e in new.events()} == {e.event_id for e in old.events()}
        assert _closed(new) == _closed(old)
        assert new.generators() == old.generators()
        assert new.report() == old.report()
        ids = sorted(new._events)
        for a in ids[:6]:
            for b in ids[:6]:
                assert new.order(a, b) == old.order(a, b)
                assert new.proper_time(a, b) == old.proper_time(a, b)


@given(spines())
@settings(max_examples=150, deadline=None)
def test_a_restriction_restricted_is_the_same_poset_either_way(sp: Spine) -> None:
    for first in STRATA[:2]:
        for second in STRATA:
            new = sp.restrict(first).restrict(second)
            old = sp._restrict_by_closure(first)._restrict_by_closure(second)
            assert _closed(new) == _closed(old)


@given(spines())
@settings(max_examples=150, deadline=None)
def test_the_strata_still_partition_the_events(sp: Spine) -> None:
    union: set[str] = set()
    for stratum in {e.stratum for e in sp.events()}:
        sub = {e.event_id for e in sp.n_s(stratum).events()}
        assert union.isdisjoint(sub)
        union |= sub
    assert union == {e.event_id for e in sp.events()}


def test_the_memoized_restriction_is_the_index_view_on_a_frozen_spine() -> None:
    """The index composes with the frozen Spine and its per-stratum memo: one index per spine,
    one restriction object per stratum, and that restriction's successors are the index's view,
    so the closure is never materialized on the memoized path."""
    import dataclasses

    import pytest

    from core.temporal.spine import _ClosureView

    sp = _spine(6, ["mirror", "ops", "mirror", "ops", "mirror", "mirror"],
                {(0, 3), (1, 4), (3, 5)}, [0, 1, 0, 1, 0, 2])
    first = sp.restrict("mirror")
    assert sp.restrict("mirror") is first
    assert isinstance(first._succ, _ClosureView)
    assert sp._index is sp._index
    assert first._restricted == {}
    with pytest.raises(dataclasses.FrozenInstanceError):
        sp._succ = {}                                     # type: ignore[misc]
