"""Direct falsifiers for `core/complex/cut.py`'s conductance (MF-3; `docs/LAWS.md` §III, CUT-1).

`conductance` and `min_conductance` had no direct test, only downstream range checks, while they
carry two opposite-direction conventions: a degenerate `S` reads 0.0, "maximally sealed", and no
qualifying community reads 1.0, "healthy" (dn-mathematical-foundations §2.6). Here: known values,
`Φ(S) ∈ [0, 1]` and `Φ(S) = 0 iff no weight crosses` on graphs Hypothesis draws (the statements of
`formal/Palace/Cut.lean`), both conventions, and the singleton skip, with a control that leaves the
skip out.
"""

from __future__ import annotations

import numpy as np
import pytest
import scipy.sparse as sp
from hypothesis import given, settings
from hypothesis import strategies as st

from core.complex.cut import conductance, min_conductance
from tests.fixtures.graphs import graphs

# `w(∂S)` and `min(vol S, vol S̄)` sum different subsets of `A` in different orders, so where they
# agree over ℝ (every edge at S crosses) float64 can put Φ an ulp above 1.
TOL = 1e-12


def _barbell() -> sp.csr_matrix:
    """Two triangles, `{0, 1, 2}` and `{3, 4, 5}`, joined by the edge `2 − 3`."""
    a = np.zeros((6, 6))
    for i, j in [(0, 1), (0, 2), (1, 2), (3, 4), (3, 5), (4, 5), (2, 3)]:
        a[i, j] = a[j, i] = 1.0
    return sp.csr_matrix(a)


def _with_isolated(A: sp.csr_matrix) -> sp.csr_matrix:
    """`A` with one isolated vertex appended."""
    n = A.shape[0]
    return sp.csr_matrix(sp.block_diag([A, sp.csr_matrix((1, 1))]).toarray(), shape=(n + 1, n + 1))


# ── known values ────────────────────────────────────────────────────────────────────────────────

def test_conductance_of_known_cuts():
    """`Φ(S) = w(∂S) / min(vol S, vol S̄)`: the barbell's triangle has one crossing edge and
    volume 7 on each side; with the bridge's far end added, two edges cross and the smaller side,
    `S̄`, has volume 4; a pair of `K₄`'s vertices has four crossing edges and volume 6 on each side;
    a path's end has its one edge crossing; and weights scale out."""
    assert conductance(_barbell(), {0, 1, 2}) == pytest.approx(1 / 7)
    assert conductance(_barbell(), {0, 1, 2, 3}) == pytest.approx(2 / 4)
    k4 = sp.csr_matrix(np.ones((4, 4)) - np.eye(4))
    assert conductance(k4, {0, 1}) == pytest.approx(4 / 6)
    path = sp.csr_matrix(np.array([[0.0, 1.0, 0.0], [1.0, 0.0, 1.0], [0.0, 1.0, 0.0]]))
    assert conductance(path, {0}) == pytest.approx(1.0)
    assert conductance(2.5 * _barbell(), {0, 1, 2}) == pytest.approx(1 / 7)


# ── the bounds, over graphs Hypothesis draws ────────────────────────────────────────────────────

@settings(deadline=None, max_examples=300)
@given(A=graphs(max_n=9), data=st.data())
def test_conductance_lies_in_the_unit_interval_and_is_zero_iff_nothing_crosses(A, data):
    """CUT-1: `Φ(S) ∈ [0, 1]` for symmetric `A ≥ 0`, degenerate `S` included, and `Φ(S) = 0` iff no
    weight crosses from `S` to the rest (`Cut.lean::conductance_mem_Icc`,
    `Cut.lean::conductance_eq_zero_iff`). Proof: each crossing edge's weight is counted once in
    `vol S` and once in `vol S̄`, so `0 ≤ w(∂S) ≤ min(vol S, vol S̄)`; a degenerate `S` reads 0.0 and
    has nothing crossing, since no edge leaves an empty side or a side of zero volume."""
    n = A.shape[0]
    S = data.draw(st.sets(st.integers(min_value=0, max_value=n - 1)))
    phi = conductance(A, S)
    assert 0.0 <= phi <= 1.0 + TOL
    a = A.toarray()
    crossing = sum(a[i, j] for i in S for j in range(n) if j not in S)
    assert (phi == 0.0) == (crossing == 0.0)


@settings(deadline=None, max_examples=200)
@given(A=graphs(max_n=9))
def test_min_conductance_lies_in_the_unit_interval(A):
    """CUT-1: the worst community conductance over the spectral partition lies in `[0, 1]`."""
    assert 0.0 <= min_conductance(A) <= 1.0 + TOL


# ── the two conventions, opposite alarms ────────────────────────────────────────────────────────

def test_a_degenerate_set_reads_maximally_sealed():
    """CUT-1: an empty `S`, all of `V`, an `S` of zero volume or one whose complement has zero
    volume read 0.0, "maximally sealed"."""
    A = _with_isolated(_barbell())
    assert conductance(A, set()) == 0.0
    assert conductance(A, set(range(7))) == 0.0
    assert conductance(A, {6}) == 0.0                     # vol S = 0: S is the isolated vertex
    assert conductance(A, set(range(6))) == 0.0           # vol S̄ = 0: S̄ is the isolated vertex


def test_no_qualifying_community_reads_healthy():
    """CUT-1: with no community of two or more vertices short of the whole graph,
    `min_conductance` reads 1.0, "healthy", the opposite alarm to a degenerate `S`."""
    assert min_conductance(sp.csr_matrix((1, 1))) == 1.0                    # fewer than 2 vertices
    A = _barbell()
    assert min_conductance(A, labels=np.arange(6)) == 1.0                    # all singletons
    assert min_conductance(A, labels=np.zeros(6, dtype=np.int64)) == 1.0     # one community: all


# ── the singleton skip ──────────────────────────────────────────────────────────────────────────

def _min_conductance_without_the_skip(A: sp.csr_matrix, labels: np.ndarray) -> float:
    """The control: every community counted, singletons included."""
    phis = [conductance(A, set(np.flatnonzero(labels == lab).tolist()))
            for lab in np.unique(labels)]
    return float(min(phis))


def test_a_singleton_community_is_not_a_chamber():
    """CUT-1: communities of fewer than two vertices are skipped. An isolated vertex in a community
    of its own has zero volume, so counting it would read the graph as maximally sealed; skipped,
    the worst community is a triangle of the barbell. The control counts it and reads 0.0."""
    A = _with_isolated(_barbell())
    labels = np.array([0, 0, 0, 1, 1, 1, 2])
    assert min_conductance(A, labels=labels) == pytest.approx(1 / 7)
    assert _min_conductance_without_the_skip(A, labels) == 0.0
