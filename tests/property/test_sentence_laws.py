"""The sentence algebra's laws on the code's own arrays (`core/sentence/algebra.py`,
`core/sentence/automaton.py`), each the statement `formal/Palace/Sentence.lean` proves over exact
arithmetic: the two-sided bridge of dn-mathematical-foundations §2.4.

QSA-1 `and` keeps the cone · QSA-2 `within` keeps it, distributes and stacks · QSA-3 the anchor's
column · QSA-4 a threshold passes a mask, the top-k does not · QSA-7 the product walk is the direct
check and more edges give more chains · QSA-9 the rank-one updates, both Rayleigh directions, the
camps, Sherman–Morrison. Controls: a mask of an indefinite matrix stays indefinite; the top-k
counterexample; a contradiction between allies breaks the camps; the correction added instead of
subtracted is not the inverse.
"""

from __future__ import annotations

import numpy as np
import scipy.sparse as sp
from hypothesis import assume, given, settings
from hypothesis import strategies as st
from scipy.sparse.csgraph import connected_components

from core.sentence.algebra import (
    assume_edge,
    atleast,
    camps,
    dvec,
    effective_resistance,
    field_at,
    laplacian,
    mask,
    mask_field,
    sherman_morrison,
    signed_laplacian,
    topk,
)
from core.sentence.ast import Rel
from core.sentence.automaton import Chain, compile_path, product_walk
from tests.fixtures.graphs import graphs

TOL = 1e-9

small = st.integers(min_value=2, max_value=6)
entries = st.floats(min_value=-2.0, max_value=2.0)


@st.composite
def matrices(draw: st.DrawFn, n: int | None = None) -> np.ndarray:
    m = n if n is not None else draw(small)
    return np.array([[draw(entries) for _ in range(m)] for _ in range(m)])


@st.composite
def gram(draw: st.DrawFn, n: int | None = None) -> np.ndarray:
    """`Bᵀ B`: in the cone by construction."""
    b = draw(matrices(n))
    return b.T @ b


@st.composite
def regions(draw: st.DrawFn, n: int) -> frozenset[int]:
    return frozenset(i for i in range(n) if draw(st.booleans()))


def _min_eig(K: np.ndarray) -> float:
    return float(np.linalg.eigvalsh((K + K.T) / 2).min())


@st.composite
def gram_pairs(draw: st.DrawFn) -> tuple[np.ndarray, np.ndarray, frozenset[int], frozenset[int]]:
    n = draw(small)
    return draw(gram(n)), draw(gram(n)), draw(regions(n)), draw(regions(n))


# ── QSA-1, QSA-2 ───────────────────────────────────────────────────────────────────────────────


@given(gram_pairs())
@settings(max_examples=150)
def test_and_and_within_keep_the_cone(data: tuple[np.ndarray, np.ndarray, frozenset[int],
                                                  frozenset[int]]) -> None:
    """`and_posSemidef`, `or_posSemidef`, `posSemidef_mask`."""
    A, B, S, _ = data
    assert _min_eig(A * B) >= -TOL
    assert _min_eig(A + B) >= -TOL
    assert _min_eig(mask(A, S)) >= -TOL


def test_control_a_mask_of_an_indefinite_matrix_stays_indefinite() -> None:
    A = np.array([[0.0, 1.0, 0.0], [1.0, 0.0, 1.0], [0.0, 1.0, 0.0]])
    assert _min_eig(mask(A, {0, 1})) < -0.5
    assert _min_eig(A * A.T.copy().__neg__()) < 0 or _min_eig(-A) < 0


@given(gram_pairs())
@settings(max_examples=150)
def test_within_distributes_and_stacks(data: tuple[np.ndarray, np.ndarray, frozenset[int],
                                                   frozenset[int]]) -> None:
    """`mask_add`, `mask_hadamard`, `mask_mask`, `mask_univ`."""
    A, B, S, T = data
    n = A.shape[0]
    np.testing.assert_allclose(mask(A + B, S), mask(A, S) + mask(B, S), atol=TOL)
    np.testing.assert_allclose(mask(A * B, S), mask(A, S) * mask(B, S), atol=TOL)
    np.testing.assert_allclose(mask(mask(A, T), S), mask(A, S & T), atol=TOL)
    np.testing.assert_allclose(mask(A, range(n)), A, atol=TOL)


# ── QSA-3, QSA-4 ───────────────────────────────────────────────────────────────────────────────


@given(gram_pairs(), st.data())
@settings(max_examples=150)
def test_the_anchors_column_of_and_is_the_product_of_columns(
        data: tuple[np.ndarray, np.ndarray, frozenset[int], frozenset[int]],
        draw: st.DataObject) -> None:
    """`fieldAt_hadamard`, `fieldAt_add`, `fieldAt_mask`."""
    A, B, S, _ = data
    a = draw.draw(st.integers(min_value=0, max_value=A.shape[0] - 1))
    np.testing.assert_allclose(field_at(A * B, a), field_at(A, a) * field_at(B, a), atol=TOL)
    np.testing.assert_allclose(field_at(A + B, a), field_at(A, a) + field_at(B, a), atol=TOL)
    expected = mask_field(field_at(A, a), S) if a in S else np.zeros(A.shape[0])
    np.testing.assert_allclose(field_at(mask(A, S), a), expected, atol=TOL)


@given(st.lists(st.floats(min_value=0.0, max_value=1.0), min_size=1, max_size=8), st.data())
@settings(max_examples=200)
def test_a_positive_threshold_commutes_with_within(values: list[float],
                                                   draw: st.DataObject) -> None:
    """`thresh_maskF`."""
    f = np.array(values)
    S = draw.draw(regions(len(values)))
    t = draw.draw(st.floats(min_value=1e-6, max_value=1.0))
    assert atleast(mask_field(f, S), t) == S & atleast(f, t)


def test_control_the_top_k_does_not_commute_with_within() -> None:
    """`topk_maskF_ne`: the Lean witness, on the code's functions."""
    f = np.array([3.0, 2.0, 1.0])
    assert topk(mask_field(f, {1, 2}), 1) == frozenset({1})
    assert {1, 2} & topk(f, 1) == set()
    assert topk(np.array([2.0, 2.0, 1.0]), 1) == frozenset({0, 1})      # ties are kept
    assert atleast(np.array([0.5, 0.2]), 0.5) == frozenset({0})         # the threshold is inclusive


# ── QSA-7 ──────────────────────────────────────────────────────────────────────────────────────

MOVES = (Rel.S, Rel.F, Rel.D, Rel.C)
PATTERNS = ["S*(C|D)", "S*", "F?C", "(S|F)+", "S{1,2}C", "(S|F|D|C)*"]


@st.composite
def typed_graphs(draw: st.DrawFn) -> dict[Rel, dict[str, set[str]]]:
    names = ["a", "b", "c", "d"]
    graph: dict[Rel, dict[str, set[str]]] = {m: {} for m in MOVES}
    for m in MOVES:
        for u in names:
            for v in names:
                if u != v and draw(st.booleans()):
                    graph[m].setdefault(u, set()).add(v)
    return graph


def _brute(graph: dict[Rel, dict[str, set[str]]], pattern: str, start: str,
           depth: int) -> set[Chain]:
    dfa = compile_path(pattern)
    out: set[Chain] = set()
    frontier = [Chain(start, ())]
    for _ in range(depth):
        nxt: list[Chain] = []
        for ch in frontier:
            visited = {ch.start, *(v for _, v in ch.steps)}
            for m in MOVES:
                for v in graph.get(m, {}).get(ch.end, ()):
                    if v not in visited:
                        nxt.append(Chain(ch.start, ch.steps + ((m, v),)))
        frontier = nxt
        out.update(c for c in frontier if dfa.accepts(c.word))
    return out


@given(typed_graphs(), st.sampled_from(PATTERNS), st.sampled_from(["a", "b", "c", "d"]))
@settings(max_examples=120)
def test_the_product_walk_is_the_direct_check(graph: dict[Rel, dict[str, set[str]]],
                                              pattern: str, start: str) -> None:
    """`admissible_iff_prodOk`, `prune_sound`."""
    found = set(product_walk(graph, compile_path(pattern), start, depth=3, limit=100000))
    assert found == _brute(graph, pattern, start, 3)


@given(typed_graphs(), st.sampled_from(PATTERNS), st.sampled_from(MOVES), st.data())
@settings(max_examples=120)
def test_an_assumed_edge_only_adds_chains(graph: dict[Rel, dict[str, set[str]]], pattern: str,
                                          move: Rel, draw: st.DataObject) -> None:
    """`admissible_assume`, `admissible_mono`."""
    names = st.sampled_from(["a", "b", "c", "d"])
    a, b = draw.draw(names), draw.draw(names)
    assume(a != b)
    bigger = {m: {u: set(vs) for u, vs in adj.items()} for m, adj in graph.items()}
    bigger[move].setdefault(a, set()).add(b)
    before = set(product_walk(graph, compile_path(pattern), "a", depth=3, limit=100000))
    after = set(product_walk(bigger, compile_path(pattern), "a", depth=3, limit=100000))
    assert before <= after


# ── QSA-9 ──────────────────────────────────────────────────────────────────────────────────────


def _connected(a: np.ndarray) -> bool:
    return bool(connected_components(sp.csr_matrix(a), directed=False)[0] == 1)


@given(graphs(max_n=6), st.data())
@settings(max_examples=150)
def test_a_hypothetical_edge_is_a_rank_one_update_of_the_laplacian(A: sp.csr_matrix,
                                                                   draw: st.DataObject) -> None:
    """`lap_assumeEdge`, `dotProduct_lap_le_assumeEdge`."""
    a = A.toarray()
    n = a.shape[0]
    assume(n >= 2)
    u = draw.draw(st.integers(min_value=0, max_value=n - 1))
    v = draw.draw(st.integers(min_value=0, max_value=n - 1))
    assume(u != v)
    delta = draw.draw(st.floats(min_value=0.0, max_value=1.0))
    d = dvec(n, u, v)
    np.testing.assert_allclose(laplacian(assume_edge(a, u, v, delta)),
                               laplacian(a) + delta * np.outer(d, d), atol=TOL)
    x = np.array([draw.draw(entries) for _ in range(n)])
    assert x @ laplacian(a) @ x <= x @ laplacian(assume_edge(a, u, v, delta)) @ x + TOL


@given(graphs(max_n=6), st.data())
@settings(max_examples=150)
def test_adding_weight_lowers_resistance_and_removing_it_raises_it(A: sp.csr_matrix,
                                                                   draw: st.DataObject) -> None:
    """`rEff_assumeEdge_le` (CND-2 forward) and `rEff_le_assumeEdge` (CND-2 backward)."""
    a = A.toarray()
    n = a.shape[0]
    assume(n >= 2 and _connected(a))
    u = draw.draw(st.integers(min_value=0, max_value=n - 1))
    v = draw.draw(st.integers(min_value=0, max_value=n - 1))
    i = draw.draw(st.integers(min_value=0, max_value=n - 1))
    j = draw.draw(st.integers(min_value=0, max_value=n - 1))
    assume(u != v)
    before = effective_resistance(a, i, j)
    added = assume_edge(a, u, v, draw.draw(st.floats(min_value=0.01, max_value=1.0)))
    assert effective_resistance(added, i, j) <= before + 1e-7
    if a[u, v] > 0:
        weakened = assume_edge(a, u, v, -a[u, v] / 2)                 # still connected
        assert effective_resistance(weakened, i, j) >= before - 1e-7


@given(graphs(max_n=6), st.data())
@settings(max_examples=150)
def test_a_signed_edge_updates_along_e_u_minus_sigma_e_v_and_the_camps_decide(
        A: sp.csr_matrix, draw: st.DataObject) -> None:
    """`signedLap_assumeEdge`, `balanced_assumeEdge`; control: the other sign breaks the camps."""
    a = A.toarray()
    n = a.shape[0]
    assume(n >= 2)
    u = draw.draw(st.integers(min_value=0, max_value=n - 1))
    v = draw.draw(st.integers(min_value=0, max_value=n - 1))
    assume(u != v)
    a[u, v] = a[v, u] = 0.0                                             # a new edge
    s = np.array([1.0 if draw.draw(st.booleans()) else -1.0 for _ in range(n)])
    signed = np.abs(a) * np.outer(s, s)                                  # balanced by the camps s
    sigma = 1.0 if draw.draw(st.booleans()) else -1.0
    delta = draw.draw(st.floats(min_value=0.0, max_value=1.0))
    d = dvec(n, u, v, sigma)
    np.testing.assert_allclose(signed_laplacian(assume_edge(signed, u, v, sigma * delta)),
                               signed_laplacian(signed) + delta * np.outer(d, d), atol=TOL)
    consistent = s[u] * s[v]
    assert camps(assume_edge(signed, u, v, consistent * (delta + 0.01))) is not None
    if _connected(np.abs(signed)):
        assert camps(assume_edge(signed, u, v, -consistent * (delta + 0.01))) is None


@given(matrices(), st.data())
@settings(max_examples=150)
def test_sherman_morrison_is_the_inverse_of_the_rank_one_update(M: np.ndarray,
                                                                draw: st.DataObject) -> None:
    """`inv_add_vecMulVec`; control: the correction added is not."""
    n = M.shape[0]
    assume(abs(np.linalg.det(M)) > 1e-3)
    u = np.array([draw.draw(entries) for _ in range(n)])
    v = np.array([draw.draw(entries) for _ in range(n)])
    c = draw.draw(st.floats(min_value=-2.0, max_value=2.0))
    M_inv = np.linalg.inv(M)
    denom = 1.0 + c * float(v @ M_inv @ u)
    assume(abs(denom) > 1e-3)
    updated = M + c * np.outer(u, v)
    np.testing.assert_allclose(updated @ sherman_morrison(M_inv, u, v, c), np.eye(n), atol=1e-6)
    wrong = M_inv + (c / denom) * np.outer(M_inv @ u, v @ M_inv)
    assume(abs(c) > 1e-2 and np.linalg.norm(np.outer(M_inv @ u, v @ M_inv)) > 1e-2)
    assert not np.allclose(updated @ wrong, np.eye(n), atol=1e-6)


# ── the planner is a theorem: a term and its normal form answer alike (review of 2026-11-05) ──


def _plan_universe():  # type: ignore[no-untyped-def]
    from tests.unit.test_sentence_execute import _universe

    return _universe()


def _sentence_terms():  # type: ignore[no-untyped-def]
    from core.sentence import ast

    near = st.sampled_from([ast.Near("q"), ast.Near("p")])
    diffuse = st.sampled_from([ast.Diffuse(Rel.S, "a.md"), ast.Diffuse(Rel.S, "c.md", 2.0)])
    reach = st.sampled_from([ast.Reach(Rel.F, "a.md", 1), ast.Reach(Rel.F, "c.md", 2),
                             ast.Relate("A")])
    fields = st.deferred(lambda: st.one_of(
        near, diffuse, st.builds(ast.Far, fields), st.builds(ast.And, fields, fields),
        st.builds(ast.Or, fields, fields), st.builds(ast.Within, fields, regions),
        st.builds(ast.And, fields, regions)))
    regions = st.deferred(lambda: st.one_of(
        reach, st.builds(ast.Top, st.integers(1, 3), fields),
        st.builds(ast.AtLeast, st.sampled_from([0.05, 0.3]), fields),
        st.builds(ast.Not, regions), st.builds(ast.Minus, regions, regions),
        st.builds(ast.And, regions, regions), st.builds(ast.Or, regions, regions),
        st.builds(ast.Within, regions, regions), st.builds(ast.Then, regions, regions)))
    return st.one_of(fields, regions)


@given(_sentence_terms())
@settings(max_examples=300, deadline=None)
def test_a_term_and_its_normal_form_answer_alike(term) -> None:  # type: ignore[no-untyped-def]
    """Every rewrite the planner makes is a law: evaluating a term and its normal form give the
    same field (to 1e-12) or the same region. The `or` flattening failed this before `or` was
    the mean of the chain (three disjuncts scored 0.5 written, 0.25 planned)."""
    from core.sentence.execute import Evaluator, FieldV, RegionV
    from core.sentence.plan import normalize
    from core.sentence.types import sort_of

    sort_of(term)                                   # the strategy builds well-sorted terms
    u = _plan_universe()
    written, planned = Evaluator(u).eval(term), Evaluator(u).eval(normalize(term))
    if isinstance(written, FieldV):
        assert isinstance(planned, FieldV)
        assert np.allclose(written.scores, planned.scores, atol=1e-12)
    else:
        assert isinstance(written, RegionV) and isinstance(planned, RegionV)
        assert written.members == planned.members


def test_or_is_one_mixture_however_it_is_grouped() -> None:
    """The reviewer's probe: `near "b" or near "c" or near "a"` as written and as planned."""
    from core.sentence import compile_sentence, execute
    from core.sentence.execute import Evaluator
    from core.sentence.grammar import parse

    u = _plan_universe()
    left = Evaluator(u).eval(parse('(near "q" or near "p") or diffuse S from "a.md"'))
    right = Evaluator(u).eval(parse('near "q" or (near "p" or diffuse S from "a.md")'))
    assert np.allclose(left.scores, right.scores)    # type: ignore[attr-defined]
    plan = compile_sentence('near "q" or near "p" or diffuse S from "a.md"')
    assert execute(plan, u).hits == execute(
        compile_sentence('diffuse S from "a.md" or (near "p" or near "q")'), u).hits
