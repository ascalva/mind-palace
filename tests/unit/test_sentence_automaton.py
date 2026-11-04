"""The chain language (`core/sentence/automaton.py`): paths compile to automata, the set is the
one-state automaton, and the product walk prunes at dead states (QSA-7 in
`formal/Palace/Sentence.lean`)."""

from __future__ import annotations

import itertools

import pytest

from core.sentence.ast import Rel
from core.sentence.automaton import (
    GROUNDING,
    Chain,
    PathError,
    TypedGraph,
    compile_path,
    letters,
    of_set,
    product_walk,
)

S, F, D, C = Rel.S, Rel.F, Rel.D, Rel.C


def test_the_grounding_production_and_the_set_that_shadows_it() -> None:
    """`grounding_words`, `ofSet_accepts`: the order is the content."""
    g = compile_path(GROUNDING)
    assert g.accepts([S, S, C]) and g.accepts([D]) and g.accepts([S, D])
    assert not g.accepts([C, S]) and not g.accepts([]) and not g.accepts([S, S])
    e = of_set({S, C, D})
    assert e.accepts([C, S]) and e.accepts([]) and not e.accepts([F])
    assert letters("S{0,2}C+") == frozenset({S, C})


def test_dead_states_are_exactly_the_states_no_word_completes() -> None:
    """`grounding_live_iff`: live off the dead state; `prune_sound`."""
    g = compile_path(GROUNDING)
    assert g.is_live(g.start)
    assert g.is_live(g.run(g.start, [S, S]))
    assert g.is_live(g.run(g.start, [C]))
    assert not g.is_live(g.run(g.start, [C, S]))
    assert not g.is_live(g.run(g.start, [F]))


@pytest.mark.parametrize("pattern, word, ok", [
    ("S{0,2}C+", [C], True),
    ("S{0,2}C+", [S, S, C, C], True),
    ("S{0,2}C+", [S, S, S, C], False),
    ("(S|F)*D", [S, F, S, D], True),
    ("(S|F)*D", [S, F, D, S], False),
    ("F?C", [F, C], True),
    ("F?C", [F, F, C], False),
    ("S{2}", [S, S], True),
    ("S{2}", [S], False),
    ("S{2,}", [S, S, S, S], True),
])
def test_regular_paths_accept_what_they_say(pattern: str, word: list[Rel], ok: bool) -> None:
    assert compile_path(pattern).accepts(word) is ok


@pytest.mark.parametrize("bad", ["", "X", "S{2,1}", "(S", "S)", "S{", "*"])
def test_a_bad_path_is_refused(bad: str) -> None:
    with pytest.raises(PathError):
        compile_path(bad)


def _graph() -> TypedGraph:
    return {
        S: {"a": {"b"}, "b": {"a", "c"}, "c": {"b"}},
        F: {"a": {"c"}},
        C: {"c": {"d"}},
        D: {},
    }


def _brute(graph: TypedGraph, pattern: str, start: str, depth: int) -> set[Chain]:
    """Every simple chain of at most `depth` moves, filtered by the automaton: the direct check."""
    dfa = compile_path(pattern)
    out: set[Chain] = set()
    frontier: list[Chain] = [Chain(start, ())]
    for _ in range(depth):
        nxt: list[Chain] = []
        for ch in frontier:
            visited = {ch.start, *(v for _, v in ch.steps)}
            for move in (S, F, D, C):
                for v in graph.get(move, {}).get(ch.end, ()):
                    if v not in visited:
                        nxt.append(Chain(ch.start, ch.steps + ((move, v),)))
        frontier = nxt
        out.update(c for c in frontier if dfa.accepts(c.word))
    return out


def test_the_product_walk_is_the_direct_check_with_pruning() -> None:
    """`admissible_iff_prodOk`, `prune_sound`: the walk finds exactly the admissible chains."""
    g = _graph()
    for pattern in [GROUNDING, "S*", "F?C", "(S|F)+", "S{1,2}C"]:
        for start in ["a", "b", "c"]:
            found = set(product_walk(g, compile_path(pattern), start, depth=3, limit=1000))
            assert found == _brute(g, pattern, start, 3), (pattern, start)


def test_a_target_filters_the_chains_and_an_added_edge_only_adds() -> None:
    """`admissible_assume`: more edges, more chains."""
    g = _graph()
    to_d = product_walk(g, compile_path("S*C"), "a", depth=3, target="d")
    assert {str(c) for c in to_d} == {"a →S→ b →S→ c →C→ d"}
    bigger: dict[Rel, dict[str, set[str]]] = {m: {u: set(vs) for u, vs in adj.items()}
                                              for m, adj in g.items()}
    bigger[C].setdefault("b", set()).add("d")
    before = set(product_walk(g, compile_path("S*C"), "a", depth=3))
    after = set(product_walk(bigger, compile_path("S*C"), "a", depth=3))
    assert before <= after and "a →S→ b →C→ d" in {str(c) for c in after - before}


def test_words_and_chains_render() -> None:
    chain = Chain("a", ((S, "b"), (C, "d")))
    assert str(chain) == "a →S→ b →C→ d" and chain.end == "d" and chain.word == (S, C)
    words = set(itertools.product([S, F, D, C], repeat=2))
    g = compile_path("S*(C|D)")
    assert {w for w in words if g.accepts(w)} == {(S, C), (S, D)}
