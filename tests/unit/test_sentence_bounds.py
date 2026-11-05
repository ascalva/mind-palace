"""The bounds: no sentence can hold the surfaces (the review of 2026-11-05, finding 3).

The stdio server and the web responder answer one call at a time, so one slow sentence blocks the
rest. The ledger bounds what a sentence may ask (`docs/query/precedents.md`): depth, `top k`, a
path's counts, a walk's budget; `beta` must be positive for the free energy to exist (RSP-1).
Each bound is refused when the sentence is compiled, by name; `reach` stops when nothing is left
to reach; a walk goes breadth first, so it returns the shortest chains, and says when it stopped.
"""

from __future__ import annotations

import time

import pytest

from core.sentence import compile_sentence, execute
from core.sentence.ast import Rel
from core.sentence.automaton import PathError, compile_path, walk_product
from core.sentence.grammar import ParseError
from core.sentence.precedents import Precedents
from tests.unit.test_sentence_execute import _universe


@pytest.mark.parametrize(("sentence", "why"), [
    ('reach F from "a.md" depth 1000000000', "at most 50 hops"),
    ('walk from "a.md" via F+ depth 51', "at most 50 hops"),
    ('top 5000 near "q"', "at most 1000"),
    ('walk from "a.md" via S{0,100000}', "past 32"),
    ('walk from "a.md" via ((S{32}){32}){32}', "states"),
    ('diffuse S from "a.md" beta 0', "β > 0"),
    ('diffuse S from "a.md" beta 0.0', "β > 0"),
])
def test_a_sentence_past_a_bound_is_refused_when_compiled(sentence: str, why: str) -> None:
    t0 = time.perf_counter()
    with pytest.raises(ParseError, match=why):
        compile_sentence(sentence)
    assert time.perf_counter() - t0 < 1.0


def test_nested_counts_are_refused_before_the_automaton_is_built() -> None:
    with pytest.raises(PathError, match="states"):
        compile_path("((S{32}){32}){32}")
    compile_path("S{0,32}C")                    # a count at the bound builds


def test_reach_stops_when_nothing_is_left_to_reach() -> None:
    """At the bound, on a graph whose component is three notes, `reach` is immediate."""
    u = _universe()
    t0 = time.perf_counter()
    answer = execute(compile_sentence('reach F from "a.md" depth 50'), u)
    assert {h.ref for h in answer.hits} == {"b.md", "c.md"}
    assert time.perf_counter() - t0 < 1.0


def test_a_walk_returns_the_shortest_chains_and_says_when_it_stopped() -> None:
    """Breadth first: at a limit of two, the two one-move chains, not a longer one found first by
    a depth-first walk; and the reason it stopped is said."""
    g = {Rel.S: {"s": {"a", "z"}, "a": {"s", "b"}, "b": {"a"}, "z": {"s"}}}
    chains, short = walk_product(g, compile_path("S+"), "s", depth=3, limit=2)
    assert [str(c) for c in chains] == ["s →S→ a", "s →S→ z"]
    assert "2 shortest chains" in short
    everything, none = walk_product(g, compile_path("S+"), "s", depth=3, limit=200)
    assert len(everything) == 3 and none == ""          # s→a, s→z, s→a→b: exhaustive, unsaid


def test_a_walk_with_no_way_through_stops_at_its_budget() -> None:
    """A complete graph of fourteen notes and a target that is not there: every simple path is
    a candidate, so the walk stops at its budget, fast, and says so."""
    nodes = [f"n{i}" for i in range(14)]
    g = {Rel.S: {a: {b for b in nodes if b != a} for a in nodes}}
    t0 = time.perf_counter()
    chains, short = walk_product(g, compile_path("S+"), "n0", depth=10, target="nowhere",
                                 budget=5_000)
    assert chains == [] and "budget of 5000" in short
    assert time.perf_counter() - t0 < 2.0


def test_the_answer_says_when_a_walk_stopped_short() -> None:
    answer = execute(compile_sentence('walk from "a.md" via S+ depth 3'), _universe(),
                     precedents=Precedents(walk_limit=1))
    assert len(answer.hits) == 1
    assert any("the 1 shortest chains" in n for n in answer.notes)


def test_a_path_keeps_its_own_parentheses() -> None:
    """`via (S|F)+` is one path: the reader balances the path's own parentheses before a `)`
    can close an enclosing group (it cut the path at the first `)` before)."""
    from core.sentence.grammar import parse

    (walk,) = [n for n in [parse('walk from "a" via (S|F)+ depth 2')]]
    assert walk.path == "(S|F)+" and walk.depth == 2           # type: ignore[union-attr]
    grouped = parse('(walk from "a" via (S|F)+) and (walk from "b" via F)')
    assert "(S|F)+" in repr(grouped)
    hits = execute(compile_sentence('walk from "a.md" via (S|F)+ depth 2'), _universe()).hits
    assert {h.detail["word"] for h in hits} == {"S", "F", "SS", "SF", "FS", "FF"}


@pytest.mark.parametrize("title", ["x\\", 'a "b" c', "back\\slash\\", "C:\\dir\\file"])
def test_quote_round_trips_any_title(title: str) -> None:
    """`quote` escapes a backslash as well as a quote, so `link` can name a note whose title ends
    in a backslash (it was a parse error)."""
    from core.sentence.grammar import parse, quote

    assert parse(f"relate {quote(title)}").atom == title         # type: ignore[union-attr]
