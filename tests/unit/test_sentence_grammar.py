"""The grammar of the query sentence algebra (`core/sentence/grammar.py`): precedence, adjuncts,
the modality's reach, the errors that name their production, and the legacy verbs as sentences."""

from __future__ import annotations

from typing import Any

import pytest

from core.query import Verb
from core.sentence import ParseError, ast, parse, sentence_of, typecheck
from core.sentence.ast import Direction, Rel
from core.sentence.types import Sort


def test_a_verb_with_its_nouns_parses() -> None:
    assert parse('near "magnetic laplacian"') == ast.Near("magnetic laplacian")
    assert parse('diffuse F from "x" beta 0.5') == ast.Diffuse(Rel.F, "x", 0.5)
    assert parse("reach from docs/a.md depth 2 back") == ast.Reach(Rel.F, "docs/a.md", 2,
                                                                     Direction.BACK)
    assert parse('walk from "a" to "b" via S{0,2}C+ depth 3') == ast.Walk("a", "S{0,2}C+", "b", 3)
    assert parse('trace "a" back') == ast.Trace("a", Direction.BACK)
    assert parse('witness "edge:1"') == ast.Witness("edge:1")


def test_and_binds_tighter_than_or_and_then_binds_loosest() -> None:
    a, b, c = ast.Near("a"), ast.Near("b"), ast.Near("c")
    assert parse('near "a" and near "b" or near "c"') == ast.Or(ast.And(a, b), c)
    assert parse('top 2 near "a" then near "b" or near "c"') == ast.Then(ast.Top(2, a),
                                                                         ast.Or(b, c))


def test_adjectives_bind_to_the_clause() -> None:
    region = ast.Reach(Rel.F, "n", 2, Direction.BOTH)
    parsed = parse('near "a" within reach F from "n" depth 2 and near "b" over curated')
    assert parsed == ast.And(ast.Within(ast.Near("a"), region),
                             ast.Over(ast.Near("b"), ("curated",)))
    assert parse('near "a" as of "c1"') == ast.AsOf(ast.Near("a"), "c1")


def test_assume_extends_to_the_right_unless_parenthesized() -> None:
    body = ast.And(ast.Near("x"), ast.Near("y"))
    assert parse('assume S "a" "b" +0.5 in near "x" and near "y"') == ast.Assume(
        ast.EdgeHyp(Rel.S, "a", "b", 0.5), body)
    assert parse('(assume sever F "a" "b" in near "x") and near "y"') == ast.And(
        ast.Assume(ast.SeverHyp(Rel.F, "a", "b"), ast.Near("x")), ast.Near("y"))
    assert parse('assume contradict "a" "b" in relate "a"') == ast.Assume(
        ast.ContradictHyp("a", "b"), ast.Relate("a"))


def test_prefix_operators_apply_to_the_operand() -> None:
    assert parse('far near "a"') == ast.Far(ast.Near("a"))
    assert parse('atleast 0.3 near "a" minus top 2 near "b"') == ast.Minus(
        ast.AtLeast(0.3, ast.Near("a")), ast.Top(2, ast.Near("b")))
    assert parse('not reach from "n"') == ast.Not(ast.Reach(Rel.F, "n", None, Direction.BOTH))


@pytest.mark.parametrize("text, production", [
    ("near x", "near"),
    ('foo "x"', "clause"),
    ('near "x" within', "clause"),
    ('walk from "a" via', "via"),
    ('top 2.5 near "a"', "top"),
    ("", "sentence"),
    ('near "x" near "y"', "sentence"),
])
def test_a_parse_error_names_its_production(text: str, production: str) -> None:
    with pytest.raises(ParseError) as e:
        parse(text)
    assert production in str(e.value)


def test_the_legacy_verbs_are_sentences_and_hybrid_is_a_composition() -> None:
    hybrid = sentence_of(Verb.HYBRID, text="t", target="n", k=3, beta=2.0)
    assert hybrid == 'top 3 (near "t" and diffuse S from "n" beta 2)'
    assert typecheck(parse(hybrid)) is Sort.REGION
    cases: list[tuple[Verb, dict[str, Any]]] = [
        (Verb.SEARCH, {"text": "t"}),
        (Verb.REACH, {"target": "n", "depth": 2}),
        (Verb.DIFFUSE, {"target": "n"}),
        (Verb.HISTORY, {"target": "n", "direction": "back"}),
        (Verb.RELATED, {"target": "n"}),
        (Verb.ORIGIN, {"target": "e"}),
    ]
    for verb, kwargs in cases:
        typecheck(parse(sentence_of(verb, **kwargs)))
    with pytest.raises(ValueError, match="write"):
        sentence_of(Verb.CAPTURE, text="t")


def test_read_parses_with_an_optional_chunk() -> None:
    """`read <ref> [chunk n]`: the dereference as a verb (the one-command MCP, 2026-11-04)."""
    assert parse('read "a.md"') == ast.Read("a.md", None)
    assert parse('read "reference:paper" chunk 7') == ast.Read("reference:paper", 7)
    assert parse('read "a.md" and near "b"') == ast.And(ast.Read("a.md", None), ast.Near("b"))
    with pytest.raises(ParseError, match="read chunk"):
        parse('read "a.md" chunk x')
