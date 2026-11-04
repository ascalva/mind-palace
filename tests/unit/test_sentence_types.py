"""The typing of the query sentence algebra (`core/sentence/types.py`): sorts, Rule NOUN, the
clause-wise scope check (QSA-5, `formal/Palace/Sentence.lean`), and the result grade (Rule HYP)."""

from __future__ import annotations

import pytest

from core.kernel.scope import Clock, Stratum, Window
from core.query import AMBASSADOR, Grant, Mode, Verb, mode_of, required, scope
from core.sentence import (
    AmbiguousSentence,
    IllScopedSentence,
    Sort,
    SortError,
    admissible,
    clauses_of,
    hyps_of,
    is_inv,
    parse,
    sort_of,
    typecheck,
)
from core.sentence.types import check_admissible


def test_sorts_follow_the_structure() -> None:
    assert sort_of(parse('near "x"')) is Sort.FIELD
    assert sort_of(parse('top 3 near "x"')) is Sort.REGION
    assert sort_of(parse('near "x" and reach F from "n"')) is Sort.FIELD   # a masked field
    assert sort_of(parse('reach F from "n" and relate "n"')) is Sort.REGION
    assert sort_of(parse('trace "n"')) is Sort.CHAIN
    assert sort_of(parse('witness "e"')) is Sort.WITNESS
    assert sort_of(parse('assume S "a" "b" in near "x"')) is Sort.FIELD


@pytest.mark.parametrize("text, reason", [
    ('not near "x"', "complement"),            # the cone has no complement
    ('near "x" then near "y"', "region"),      # then needs a region on the left
    ('near "x" or reach F from "n"', "two fields or two regions"),
    ('trace "n" and near "x"', "fields and regions"),
    ('far reach F from "n"', "field"),
    ('assume S "a" "a" in near "x"', "distinct"),
])
def test_an_ill_sorted_sentence_is_refused_with_the_reason(text: str, reason: str) -> None:
    with pytest.raises(SortError) as e:
        typecheck(parse(text))
    assert reason in str(e.value)


def test_rule_noun_the_relation_carries_the_letter() -> None:
    (near,) = clauses_of(parse('near "x"'))
    assert near.mode is Mode.SEMANTIC and near.req.edges.fibers == frozenset()
    assert near.req.sigma.strata == frozenset({Stratum.MIRROR_AUTHORED})
    (diffuse,) = clauses_of(parse('diffuse S from "n"'))
    assert diffuse.mode is Mode.SEMANTIC and diffuse.req.edges.fibers == frozenset()
    # the legacy table types DIFFUSE as citation-structural though it walks the backbone
    assert mode_of(required(Verb.DIFFUSE)) is Mode.STRUCTURAL
    (reach,) = clauses_of(parse('reach F from "n"'))
    assert reach.mode is Mode.STRUCTURAL and reach.req.edges.fibers == frozenset({"F"})
    assert reach.req.time.clock is Clock.COMMIT
    (trace,) = clauses_of(parse('trace "n"'))
    assert trace.mode is Mode.TEMPORAL and trace.req.edges.fibers == frozenset({"D"})
    (witness,) = clauses_of(parse('witness "e"'))
    assert witness.mode is Mode.CAUSAL
    (walk,) = clauses_of(parse('walk from "a" via S*C'))
    assert walk.mode is Mode.CAUSAL and walk.req.edges.fibers == frozenset({"C"})
    assert walk.req.time.clock is Clock.COMMIT


def test_over_sets_the_strata_and_refuses_an_unknown_one() -> None:
    (c,) = clauses_of(parse('near "x" over curated'))
    assert c.req.sigma.strata == frozenset({Stratum.CURATED})
    with pytest.raises(AmbiguousSentence, match="not a stratum"):
        clauses_of(parse('near "x" over nowhere'))


def test_admissibility_is_clause_wise() -> None:
    """QSA-5: `and`, `or` and `then` are admissible iff both halves are (`admissible_and`)."""
    mirror_only = Grant((scope({Stratum.MIRROR}, set(), Clock.PROJECTION_EVENT, Window.all()),))
    cases = ['near "x"', 'reach F from "n"', 'diffuse S from "n"', 'witness "e"', 'trace "n"']
    for grant in (AMBASSADOR, mirror_only):
        for a in cases:
            for b in cases:
                both = admissible(parse(f"({a}) and ({b})"), grant)
                assert both == (admissible(parse(a), grant) and admissible(parse(b), grant))
    assert admissible(parse('near "x"'), mirror_only)
    assert not admissible(parse('reach F from "n"'), mirror_only)
    with pytest.raises(IllScopedSentence, match="reach F"):
        check_admissible(parse('near "x" and reach F from "n"'), mirror_only)


def test_assume_needs_a_plane_naming_the_overlay() -> None:
    """QSA-5: `admissible_assume_overlay`, `ambassador_no_assume`."""
    sentence = parse('assume S "a" "b" +0.5 in near "x"')
    assert admissible(parse('near "x"'), AMBASSADOR)
    assert not admissible(sentence, AMBASSADOR)
    with pytest.raises(IllScopedSentence, match="overlay"):
        check_admissible(sentence, AMBASSADOR)
    with_overlay = Grant((scope({Stratum.MIRROR, Stratum.HYPOTHETICAL}, set(),
                                Clock.PROJECTION_EVENT, Window.all()),))
    assert admissible(sentence, with_overlay)
    (c,) = clauses_of(sentence)
    assert c.overlay and Stratum.HYPOTHETICAL in c.req.sigma.strata


def test_rule_hyp_a_result_under_assume_is_never_inv() -> None:
    assert is_inv(parse('near "x" and reach F from "n"'))
    assert hyps_of(parse('near "x"')) == ()
    s = parse('(assume S "a" "b" +0.5 in near "x") and assume contradict "c" "d" in near "y"')
    assert not is_inv(s)
    assert hyps_of(s) == ("S 'a' 'b' +0.5", "contradict 'c' 'd'")
