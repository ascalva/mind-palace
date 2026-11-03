"""Direct falsifiers for `most_negative_edges`'s emission rule (MF-3; `docs/LAWS.md` §IV, CRV-3).

The Dreamer's bridge lens consumes this ranking, and until these it had no direct test: the edges
with `κ ≤ 0`, or, when every edge is positive, only those at the minimum, never the whole graph; in
`(κ, i, j)` order; at most `top_k`. Each test is one of `formal/Palace/Curvature.lean`'s CRV-3
statements, checked on the code over graphs Hypothesis draws, plus known graphs and a control.
"""

from __future__ import annotations

import numpy as np
import scipy.sparse as sp
from hypothesis import given, settings
from hypothesis import strategies as st

from core.kernel.complex.curvature import forman, most_negative_edges
from tests.fixtures.graphs import graphs


def _diamond() -> sp.csr_matrix:
    """`K₄` less the edge `2 − 3`: the edge `0 − 1` has κ = 4, the other four κ = 2."""
    a = np.ones((4, 4)) - np.eye(4)
    a[2, 3] = a[3, 2] = 0.0
    return sp.csr_matrix(a)


@settings(deadline=None, max_examples=300)
@given(A=graphs(max_n=9), top_k=st.integers(min_value=-2, max_value=12))
def test_the_emission_rule(A, top_k):
    """CRV-3: when some edge has `κ ≤ 0` only such edges are emitted (`kappa_nonpos`), otherwise
    only edges at the minimum (`kappa_min`); in strictly increasing `(κ, i, j)` order
    (`mostNegative_pairwise`); `min(top_k, |candidates|)` of them (`length_mostNegative`); and they
    are the smallest candidates, so a candidate left out ranks after every one emitted
    (`emitKey_lt`)."""
    kappa = forman(A)
    out = most_negative_edges(A, top_k=top_k)
    if not kappa:
        assert out == []
        return
    lo = min(kappa.values())
    nonpos = [e for e, k in kappa.items() if k <= 0.0]
    candidates = nonpos or [e for e, k in kappa.items() if k == lo]
    assert all(kappa[(i, j)] == k for i, j, k in out)
    if nonpos:
        assert all(k <= 0.0 for _, _, k in out)
    else:
        assert all(k == lo for _, _, k in out)
    keys = [(k, i, j) for i, j, k in out]
    assert all(a < b for a, b in zip(keys, keys[1:], strict=False))
    assert len(out) == min(max(0, top_k), len(candidates))
    emitted = {(i, j) for i, j, _ in out}
    left_out = [(kappa[e], *e) for e in candidates if e not in emitted]
    assert all(key < rest for key in keys for rest in left_out)


@settings(deadline=None, max_examples=200)
@given(A=graphs(max_n=9), k=st.integers(min_value=0, max_value=12),
       extra=st.integers(min_value=0, max_value=6))
def test_a_larger_top_k_extends_the_emission_and_never_reorders_it(A, k, extra):
    """CRV-3: the emission for `top_k` is a prefix of the emission for any larger `top_k`
    (`mostNegative_prefix`)."""
    short = most_negative_edges(A, top_k=k)
    assert most_negative_edges(A, top_k=k + extra)[:len(short)] == short


def test_a_planted_bridge_is_emitted_first():
    """CRV-3 on CRV-2's family: two 4-cliques joined by one edge; the bridge is the strict minimum,
    `4 − 4 − 4 = −4`, and is emitted first."""
    a = np.zeros((8, 8))
    a[:4, :4] = a[4:, 4:] = np.ones((4, 4)) - np.eye(4)
    a[3, 4] = a[4, 3] = 1.0
    out = most_negative_edges(sp.csr_matrix(a), top_k=3)
    assert out[0] == (3, 4, -4.0)
    assert all(k > -4.0 for _, _, k in out[1:])


def test_when_every_edge_is_positive_only_the_minimum_is_emitted():
    """CRV-3: on the diamond every edge is positive; the four at the minimum, κ = 2, are emitted
    in `(i, j)` order, and the edge with κ = 4 is not, however large `top_k`. The control, the whole
    graph ranked, would emit it."""
    out = most_negative_edges(_diamond(), top_k=10)
    assert out == [(0, 2, 2.0), (0, 3, 2.0), (1, 2, 2.0), (1, 3, 2.0)]
    whole = sorted(((i, j, k) for (i, j), k in forman(_diamond()).items()),
                   key=lambda e: (e[2], e[0], e[1]))
    assert whole[:10] != out


def test_no_edges_or_no_room_emits_nothing():
    """CRV-3: an edgeless graph, `top_k = 0` and a negative `top_k` emit nothing."""
    assert most_negative_edges(sp.csr_matrix((3, 3)), top_k=5) == []
    assert most_negative_edges(_diamond(), top_k=0) == []
    assert most_negative_edges(_diamond(), top_k=-1) == []
