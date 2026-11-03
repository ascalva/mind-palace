"""Falsifiers for the Hodge complex's laws and its bridges (`docs/LAWS.md` §II LAP-11 and §IX
BRG-1, BRG-2, BRG-3, BRG-6), over the flag complex `core/kernel/complex/hodge.py` builds.

Each law is checked on the code's own boundary operators, Laplacians and splits, on graphs
Hypothesis draws, and each has a control, a deliberately wrong operator the same check must reject
(the note's §3: a falsifier that cannot fail is the defect). The formal column of each row states
the same law over exact arithmetic in `formal/`; these are the code's evidence for it.
"""

from __future__ import annotations

from collections import deque

import numpy as np
import pytest
import scipy.sparse as sp
from hypothesis import assume, given, settings
from hypothesis import strategies as st
from scipy.sparse.csgraph import connected_components

from core.graph.conductance import _r_eff_matrix
from core.kernel.complex.curvature import forman
from core.kernel.complex.hodge import (
    boundary_1,
    boundary_2,
    edge_index,
    harmonic_basis,
    hodge_decompose,
    hodge_laplacian_1,
)
from core.kernel.complex.laplacian import laplacian
from tests.fixtures.graphs import graphs

# Agreement of two float64 computations of one real quantity (projections by least squares, a
# pseudo-inverse): exact over ℝ, so only rounding separates them on graphs this small.
TOL = 1e-9


def _support(A: sp.csr_matrix) -> sp.csr_matrix:
    """The 0/1 adjacency of `A`'s support, the graph the complex is built on."""
    return sp.csr_matrix(A.astype(bool).astype(np.float64))


# ── LAP-11: the orientation is a convention ─────────────────────────────────────────────────────

def _relabel(A: sp.csr_matrix, perm: list[int]) -> tuple[sp.csr_matrix, np.ndarray]:
    """`A` with vertex `i` renamed `perm[i]`, and the signed edge map `S`: old edge `ij` goes to the
    new edge on `{perm[i], perm[j]}`, with sign `−1` where the renaming reverses it."""
    p = np.asarray(perm, dtype=np.int64)
    inv = np.argsort(p)
    B = sp.csr_matrix(A.toarray()[np.ix_(inv, inv)])
    old, new = edge_index(A), edge_index(B)
    S = np.zeros((len(new), len(old)))
    for (i, j), e in old.items():
        a, b = int(p[i]), int(p[j])
        S[new[(min(a, b), max(a, b))], e] = 1.0 if a < b else -1.0
    return B, S


@settings(deadline=None, max_examples=150)
@given(A=graphs(max_n=7), data=st.data())
def test_relabelling_the_vertices_reorients_the_complex_and_changes_nothing(A, data):
    """LAP-11: renaming the vertices reorients the edges and triangles it reverses (each runs from
    its smaller end). `L₁` is conjugated by the edge map and its involution of signs, exactly, so
    the spectrum, `dim ker L₁` and the three-way split do not depend on the orientation."""
    perm = data.draw(st.permutations(range(A.shape[0])))
    B, S = _relabel(A, list(perm))
    L1, L1b = hodge_laplacian_1(A).toarray(), hodge_laplacian_1(B).toarray()
    assert np.array_equal(L1b, S @ L1 @ S.T)
    assert np.allclose(np.linalg.eigvalsh(L1b), np.linalg.eigvalsh(L1), atol=TOL)
    assert harmonic_basis(B).shape[1] == harmonic_basis(A).shape[1]
    c = np.random.default_rng(data.draw(st.integers(0, 2**32 - 1))).normal(size=L1.shape[0])
    split, split_b = hodge_decompose(c, A), hodge_decompose(S @ c, B)
    for part, part_b in ((split.gradient, split_b.gradient), (split.curl, split_b.curl),
                         (split.harmonic, split_b.harmonic)):
        assert np.allclose(S @ part, part_b, atol=TOL)


def test_the_conjugation_check_rejects_an_edge_map_without_its_signs():
    """Control: renaming the path `0 − 1 − 2` by `0 ↔ 1` reverses one edge; without the sign the
    edge map does not conjugate `L₁`."""
    A = sp.csr_matrix(np.array([[0.0, 1.0, 0.0], [1.0, 0.0, 1.0], [0.0, 1.0, 0.0]]))
    B, S = _relabel(A, [1, 0, 2])
    L1, L1b = hodge_laplacian_1(A).toarray(), hodge_laplacian_1(B).toarray()
    assert np.array_equal(L1b, S @ L1 @ S.T)
    assert not np.array_equal(L1b, np.abs(S) @ L1 @ np.abs(S).T)


# ── BRG-1: the Laplacian is the vertex end of the complex ───────────────────────────────────────

@settings(deadline=None, max_examples=200)
@given(A=graphs(max_n=8))
def test_the_graph_laplacian_is_the_vertex_end_of_the_hodge_complex(A):
    """BRG-1: `∂₁ ∂₁ᵀ = D − A` on the 0/1 adjacency of the support, exactly: `boundary_1` and
    `laplacian` describe one operator."""
    d1 = boundary_1(A)
    assert np.array_equal((d1 @ d1.T).toarray(), laplacian(_support(A)).toarray())


def test_the_vertex_end_check_rejects_the_signless_laplacian():
    """Control: `∂₁ ∂₁ᵀ` is not the signless `D + A` on any graph with an edge."""
    A = sp.csr_matrix(np.array([[0.0, 1.0], [1.0, 0.0]]))
    d1 = boundary_1(A)
    signless = np.diag(np.asarray(A.sum(axis=1)).ravel()) + A.toarray()
    assert not np.array_equal((d1 @ d1.T).toarray(), signless)


# ── BRG-2: Euler and Poincaré ───────────────────────────────────────────────────────────────────

def _rank(m: np.ndarray) -> int:
    return int(np.linalg.matrix_rank(m)) if m.size else 0


def _betti(A: sp.csr_matrix, *, b1_of_graph: bool = False) -> tuple[int, int, int]:
    """`(b₀, b₁, b₂)` of the flag complex: the components, `dim ker L₁` from `harmonic_basis`, and
    `dim ker ∂₂`. With `b1_of_graph`, the control's `b₁`: the graph's cycle rank, `dim ker ∂₁`,
    which forgets the filled triangles."""
    d1, d2 = boundary_1(A).toarray(), boundary_2(A).toarray()
    b0, _ = connected_components(A, directed=False)
    b1 = d1.shape[1] - _rank(d1) if b1_of_graph else harmonic_basis(A).shape[1]
    return int(b0), int(b1), d2.shape[1] - _rank(d2)


@settings(deadline=None, max_examples=200)
@given(A=graphs(max_n=8))
def test_euler_and_poincare_on_the_flag_complex(A):
    """BRG-2: `|V| − |E| + |T| = b₀ − b₁ + b₂`, with `b₀` the components, `b₁ = dim ker L₁` and
    `b₂ = dim ker ∂₂`; and `b₀ = |V| − rank ∂₁`."""
    n, n_e, n_t = A.shape[0], len(edge_index(A)), boundary_2(A).shape[1]
    b0, b1, b2 = _betti(A)
    assert n - n_e + n_t == b0 - b1 + b2
    assert b0 == n - _rank(boundary_1(A).toarray())


def test_the_euler_check_rejects_the_cycle_rank_of_the_graph():
    """Control: on a filled triangle the graph's cycle rank is 1 but `dim ker L₁` is 0; with the
    former as `b₁` the two sides differ."""
    A = sp.csr_matrix(np.ones((3, 3)) - np.eye(3))
    chi = 3 - 3 + 1
    b0, b1, b2 = _betti(A)
    assert chi == b0 - b1 + b2
    b0, b1, b2 = _betti(A, b1_of_graph=True)
    assert chi != b0 - b1 + b2


# ── BRG-3: Thomson's principle on edge flows ────────────────────────────────────────────────────

def _path_flow(A: sp.csr_matrix, i: int, j: int) -> np.ndarray:
    """A unit flow from `i` to `j` along one shortest path: `+1` on an edge walked from its smaller
    end, `−1` on one walked against it, so `∂₁ f = δ_j − δ_i`."""
    a = A.toarray() != 0
    prev = {i: i}
    queue = deque([i])
    while queue:
        u = queue.popleft()
        for v in np.flatnonzero(a[u]).tolist():
            if v not in prev:
                prev[v] = u
                queue.append(v)
    idx = edge_index(A)
    f = np.zeros(len(idx))
    v = j
    while v != i:
        u = prev[v]
        f[idx[(min(u, v), max(u, v))]] += 1.0 if u < v else -1.0
        v = u
    return f


@settings(deadline=None, max_examples=150)
@given(A=graphs(max_n=7), data=st.data())
def test_the_effective_resistance_is_the_least_energy_of_a_unit_flow(A, data):
    """BRG-3: with unit conductances, the effective resistance between `i` and `j`
    (`_r_eff_matrix`, CND-1) is at most the energy `fᵀf` of every unit flow from `i` to `j`, and the
    gradient part of any such flow (`hodge_decompose`) meets the demand with exactly that energy."""
    w = _support(A).toarray()
    _, labels = connected_components(A, directed=False)
    pairs = [(i, j) for i in range(len(w)) for j in range(len(w))
             if i != j and labels[i] == labels[j]]
    assume(pairs)
    i, j = data.draw(st.sampled_from(pairs))
    resistance = _r_eff_matrix(w, labels)[i, j]
    d1 = boundary_1(A).toarray()
    demand = np.zeros(len(w))
    demand[i], demand[j] = -1.0, 1.0
    # any unit flow: a path, plus a cycle (`c` less its gradient part lies in ker ∂₁), scaled
    c = np.random.default_rng(data.draw(st.integers(0, 2**32 - 1))).normal(size=d1.shape[1])
    cycle = c - hodge_decompose(c, A).gradient
    f = _path_flow(A, i, j) + data.draw(st.floats(min_value=-3.0, max_value=3.0)) * cycle
    assert np.allclose(d1 @ f, demand, atol=TOL)
    assert resistance <= f @ f + TOL
    g = hodge_decompose(f, A).gradient
    assert np.allclose(d1 @ g, demand, atol=TOL)
    assert g @ g == pytest.approx(resistance, rel=TOL, abs=TOL)


def test_the_thomson_check_rejects_a_resistance_that_ignores_parallel_routes():
    """Control: on a triangle, the direct edge alone has resistance 1, but the gradient flow
    splits over both routes with energy 2/3, below it; and the path flow's energy is not the
    resistance."""
    A = sp.csr_matrix(np.ones((3, 3)) - np.eye(3))
    w = A.toarray()
    resistance = _r_eff_matrix(w, np.zeros(3, dtype=np.int64))[0, 1]
    g = hodge_decompose(_path_flow(A, 0, 1), A).gradient
    assert g @ g == pytest.approx(resistance) == pytest.approx(2 / 3)
    series = 1.0
    assert not series <= g @ g + TOL
    path = _path_flow(A, 0, 1)
    assert path @ path != pytest.approx(resistance)


# ── BRG-6: Forman's curvature is the Weitzenböck term of L₁ ─────────────────────────────────────

def _weitzenbock(L: np.ndarray) -> np.ndarray:
    """Per edge, the diagonal entry less the absolute values of the rest of its row."""
    return np.diag(L) - (np.abs(L).sum(axis=1) - np.abs(np.diag(L)))


@settings(deadline=None, max_examples=200)
@given(A=graphs(max_n=8))
def test_forman_curvature_is_the_weitzenbock_term_of_the_hodge_laplacian(A):
    """BRG-6: on every edge, Forman's augmented curvature `4 − deg u − deg v + 3 t(e)` (`forman`)
    is the Weitzenböck term of `L₁ = ∂₁ᵀ ∂₁ + ∂₂ ∂₂ᵀ` on the flag complex,
    `L₁(e, e) − Σ_{e' ≠ e} |L₁(e, e')|`, exactly."""
    kappa, idx = forman(A), edge_index(A)
    assert set(kappa) == set(idx)
    term = _weitzenbock(hodge_laplacian_1(A).toarray())
    assert all(kappa[edge] == term[e] for edge, e in idx.items())


def test_the_weitzenbock_check_rejects_the_down_laplacian_alone():
    """Control: without the up part `∂₂ ∂₂ᵀ` the triangles go uncounted, so on a filled triangle
    the down Laplacian's term is not Forman's curvature."""
    A = sp.csr_matrix(np.ones((3, 3)) - np.eye(3))
    d1 = boundary_1(A).toarray()
    kappa, idx = forman(A), edge_index(A)
    assert all(kappa[edge] == _weitzenbock(hodge_laplacian_1(A).toarray())[e]
               for edge, e in idx.items())
    assert not all(kappa[edge] == _weitzenbock(d1.T @ d1)[e] for edge, e in idx.items())
