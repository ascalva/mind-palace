"""The planner (`core/sentence/plan.py`): each rewrite is a law of `formal/Palace/Sentence.lean`,
and the one it refuses is refused by a proved counterexample (QSA-2, QSA-4)."""

from __future__ import annotations

import numpy as np
import pytest

from core.query import AMBASSADOR
from core.sentence import Plan, ast, compile_sentence, normalize, parse
from core.sentence.algebra import atleast, mask_field, topk
from core.sentence.ast import Direction, Rel

R1 = ast.Reach(Rel.F, "n", None, Direction.BOTH)
R2 = ast.Relate("m")


def test_within_is_pushed_to_the_leaves_over_and_and_or() -> None:
    """`mask_hadamard`, `mask_add`."""
    pushed = normalize(parse('(near "a" and near "b") within reach F from "n"'))
    a, b = ast.Within(ast.Near("a"), R1), ast.Within(ast.Near("b"), R1)
    assert pushed == normalize(ast.And(a, b))
    pushed = normalize(parse('(near "a" or near "b") within reach F from "n"'))
    assert pushed == normalize(ast.Or(a, b))


def test_adjectives_stack_by_intersection() -> None:
    """`mask_mask`."""
    stacked = normalize(parse('near "a" within reach F from "n" within relate "m"'))
    assert stacked == ast.Within(ast.Near("a"), normalize(ast.And(R1, R2)))


def test_a_positive_threshold_lets_the_mask_through_and_the_top_k_does_not() -> None:
    """`thresh_maskF` and `topk_maskF_ne`."""
    assert normalize(parse('atleast 0.3 near "a" within reach F from "n"')) == ast.AtLeast(
        0.3, ast.Within(ast.Near("a"), R1))
    top = normalize(parse('top 3 near "a" within reach F from "n"'))
    assert top == ast.Within(ast.Top(3, ast.Near("a")), R1)
    # the counterexample the Lean proves, on the code's own functions
    f = np.array([3.0, 2.0, 1.0])
    region = {1, 2}
    assert topk(mask_field(f, region), 1) == frozenset({1})
    assert region & topk(f, 1) == set()
    assert atleast(mask_field(f, region), 1.5) == region & atleast(f, 1.5)


def test_far_and_not_cancel_and_the_normal_form_is_a_fixed_point() -> None:
    assert normalize(parse('far far near "a"')) == ast.Near("a")
    assert normalize(parse('not not reach F from "n"')) == R1
    for text in [
        '(near "a" and near "b") within reach F from "n" within relate "m"',
        'top 2 (near "b" and near "a") then near "c" or near "d"',
        'assume S "a" "b" +0.5 in near "x" within reach F from "n"',
    ]:
        once = normalize(parse(text))
        assert normalize(once) == once


def test_and_is_canonically_ordered_so_equal_sentences_have_equal_plans() -> None:
    """`hadamard_comm`, `hadamard_assoc`: the plan is a value."""
    p1 = compile_sentence('near "b" and near "a" and near "c"')
    p2 = compile_sentence('near "a" and (near "c" and near "b")')
    assert p1.term == p2.term


def test_compile_yields_the_intermediate_form() -> None:
    plan = compile_sentence('top 4 (near "t" and diffuse S from "n")', AMBASSADOR)
    assert isinstance(plan, Plan)
    assert plan.sort.value == "region" and plan.is_inv
    assert [c.verb for c in plan.clauses] == ["diffuse", "near"] or \
        [c.verb for c in plan.clauses] == ["near", "diffuse"]
    text = plan.explain()
    assert "top 4" in text and "near 't'" in text and "semantic" in text
    hyp = compile_sentence('assume F "a" "b" in reach F from "a"')
    assert not hyp.is_inv and "Hyp" in hyp.explain() and "F 'a' 'b' +1" in hyp.explain()


def test_an_inadmissible_sentence_does_not_compile() -> None:
    with pytest.raises(PermissionError):
        compile_sentence('assume S "a" "b" in near "x"', AMBASSADOR)
