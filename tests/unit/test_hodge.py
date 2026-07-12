"""Unit tests for the Hodge 1-Laplacian family (bp-021 Items 1-3).

Proves: the oriented flag complex and boundary operators satisfy the fundamental chain-complex
identity ∂₁∂₂ = 0 on hand-built fixtures (Item 1); the synthetic-topology suite (filled triangle,
empty cycle, two disjoint cycles, cycle-with-chord) recovers the KNOWN β₁ via `dim ker L₁`, the
Hodge decomposition is exact/orthogonal/idempotent, and the size guard raises past the dense-path
ceiling (Item 2); the ripser cross-check harness agrees with the incidence-algebra β₁ across
multiple σ values on a hermetic fixture, plus one read-only live-corpus run journaled separately
(Item 3).
"""

from __future__ import annotations

import numpy as np
import pytest
import scipy.sparse as sp

from core.complex.build import cosine_adjacency
from core.complex.hodge import (
    _MAX_DENSE_EDGES,
    HodgeParts,
    boundary_1,
    boundary_2,
    edge_index,
    flag_triangles,
    harmonic_basis,
    hodge_decompose,
    hodge_laplacian_1,
    l1_spectrum,
)
from core.complex.topology import cosine_distance_matrix, persistence

# --- fixture builders -------------------------------------------------------------------------

def _cycle_adjacency(n: int) -> sp.csr_matrix:
    """An n-cycle (0-1-2-...-(n-1)-0), unweighted, no chords."""
    A = np.zeros((n, n))
    for i in range(n):
        j = (i + 1) % n
        A[i, j] = A[j, i] = 1.0
    return sp.csr_matrix(A)


def _filled_triangle() -> sp.csr_matrix:
    """3-clique — a single filled triangle, β₁ = 0."""
    return _cycle_adjacency(3)


def _empty_4cycle() -> sp.csr_matrix:
    """4-cycle, no chord — β₁ = 1 (the fundamental empty hole)."""
    return _cycle_adjacency(4)


def _two_disjoint_4cycles() -> sp.csr_matrix:
    """Two disconnected 4-cycles — β₁ = 2 (holes don't interact across components)."""
    A = np.zeros((8, 8))
    for i, j in [(0, 1), (1, 2), (2, 3), (0, 3), (4, 5), (5, 6), (6, 7), (4, 7)]:
        A[i, j] = A[j, i] = 1.0
    return sp.csr_matrix(A)


def _cycle_with_chord() -> sp.csr_matrix:
    """4-cycle plus the (0,2) chord — splits into two filled triangles, β₁ = 0 (both regions
    filled; a two-hole complex would instead leave a chord unfilled — used in the cross-check)."""
    A = np.zeros((4, 4))
    for i, j in [(0, 1), (1, 2), (2, 3), (0, 3), (0, 2)]:
        A[i, j] = A[j, i] = 1.0
    return sp.csr_matrix(A)


def _two_hole_complex() -> sp.csr_matrix:
    """A 7-node complex: two 4-cycles sharing a single vertex — two independent holes joined at
    one point (connected, unlike `_two_disjoint_4cycles`), β₁ = 2. Vertex 0 is shared."""
    A = np.zeros((7, 7))
    ring1 = [0, 1, 2, 3]
    ring2 = [0, 4, 5, 6]
    for ring in (ring1, ring2):
        for a, b in zip(ring, ring[1:] + ring[:1], strict=True):
            A[a, b] = A[b, a] = 1.0
    return sp.csr_matrix(A)


def _ring_points(n: int) -> np.ndarray:
    """n points evenly spaced on a 2-D circle — a controllable cosine-distance ring (used by the
    cross-check harness, whose scale-matching logic is itself under test)."""
    theta = np.linspace(0, 2 * np.pi, n, endpoint=False)
    return np.stack([np.cos(theta), np.sin(theta)], axis=1)


# --- the reusable cross-check harness (Item 3, §6(f)) -----------------------------------------

def ripser_alive_h1_count(D: np.ndarray, *, sigma: float) -> int:
    """#{(b, d) ∈ dgms[1] : b ≤ 1−σ < d} — the ripser side of the Q4 cross-check (design note
    §6(f)), reused by bp-022 and future rungs. `sigma` is the similarity floor; `t = 1 − sigma`
    is the matching Rips distance threshold."""
    t = 1.0 - sigma
    out = persistence(D, maxdim=1)
    dgm1 = out["dgms"][1]
    return sum(1 for b, d in dgm1 if b <= t < d)


def dim_ker_l1_at_sigma(vectors: np.ndarray, *, sigma: float) -> int:
    """dim ker L₁ of the flag complex built at similarity floor `sigma` — the incidence-algebra
    side of the Q4 cross-check, built the same way `cosine_adjacency`/`build_complex` do."""
    A = cosine_adjacency(vectors, sim_floor=sigma)
    n_edges = len(edge_index(A))
    if n_edges == 0:
        return 0
    L1 = hodge_laplacian_1(A).toarray()
    eigvals = np.linalg.eigvalsh(L1)
    return int(np.sum(np.abs(eigvals) < 1e-8))


# --- Item 1: the oriented flag complex + boundary operators ------------------------------------

class TestItem1FlagComplexAndBoundaries:
    def test_filled_triangle_yields_one_triangle(self):
        A = _filled_triangle()
        tris = flag_triangles(A)
        assert tris.shape == (1, 3)
        assert tuple(tris[0]) == (0, 1, 2)

    def test_four_cycle_yields_no_triangles(self):
        A = _empty_4cycle()
        tris = flag_triangles(A)
        assert tris.shape == (0, 3)

    def test_edge_index_ordering_byte_stable(self):
        A = _two_hole_complex()
        e1 = edge_index(A)
        e2 = edge_index(A)
        assert e1 == e2
        # lexicographic, i < j
        keys = list(e1.keys())
        assert keys == sorted(keys)
        assert all(i < j for i, j in keys)

    def test_triangle_ordering_byte_stable(self):
        A = _cycle_with_chord()
        t1 = flag_triangles(A)
        t2 = flag_triangles(A)
        assert np.array_equal(t1, t2)
        assert all(i < j < k for i, j, k in t1)

    @pytest.mark.parametrize("fixture", [
        _filled_triangle, _empty_4cycle, _two_disjoint_4cycles, _cycle_with_chord,
        _two_hole_complex,
    ])
    def test_fundamental_identity_d1_d2_is_zero(self, fixture):
        """Falsifier: ∂₁∂₂ ≠ 0 on ANY fixture — an orientation sign error, caught exactly."""
        A = fixture()
        d1 = boundary_1(A)
        d2 = boundary_2(A)
        prod = (d1 @ d2).toarray()
        assert prod.shape == (A.shape[0], flag_triangles(A).shape[0])
        assert np.array_equal(prod, np.zeros_like(prod))   # exact zero, no tolerance

    def test_boundary_shapes(self):
        A = _filled_triangle()
        n_edges = len(edge_index(A))
        n_tri = flag_triangles(A).shape[0]
        assert boundary_1(A).shape == (A.shape[0], n_edges)
        assert boundary_2(A).shape == (n_edges, n_tri)

    def test_no_mutation_of_A(self):
        A = _empty_4cycle()
        before = A.toarray().copy()
        boundary_1(A)
        boundary_2(A)
        flag_triangles(A)
        hodge_laplacian_1(A)
        assert np.array_equal(A.toarray(), before)


# --- Item 2: L1, decomposition, harmonic basis, spectrum ---------------------------------------

class TestItem2SyntheticTopologySuite:
    @pytest.mark.parametrize("fixture,expected_beta1", [
        (_filled_triangle, 0),
        (_empty_4cycle, 1),
        (_two_disjoint_4cycles, 2),
        (_cycle_with_chord, 0),
        (_two_hole_complex, 2),
    ])
    def test_dim_ker_l1_matches_known_beta1(self, fixture, expected_beta1):
        """Falsifier: any fixture's dim ker L1 != known beta1 (the math is wrong, not tuned)."""
        A = fixture()
        L1 = hodge_laplacian_1(A).toarray()
        eigvals = np.linalg.eigvalsh(L1)
        dim_ker = int(np.sum(np.abs(eigvals) < 1e-8))
        assert dim_ker == expected_beta1
        basis = harmonic_basis(A)
        assert basis.shape == (len(edge_index(A)), expected_beta1)

    @pytest.mark.parametrize("fixture", [
        _filled_triangle, _empty_4cycle, _two_disjoint_4cycles, _cycle_with_chord,
        _two_hole_complex,
    ])
    def test_psd(self, fixture):
        A = fixture()
        L1 = hodge_laplacian_1(A).toarray()
        eigvals = np.linalg.eigvalsh(L1)
        assert eigvals.min() >= -1e-10

    @pytest.mark.parametrize("fixture", [
        _filled_triangle, _empty_4cycle, _two_disjoint_4cycles, _cycle_with_chord,
        _two_hole_complex,
    ])
    def test_decomposition_orthogonality_and_reconstruction(self, fixture):
        A = fixture()
        n_edges = len(edge_index(A))
        rng = np.random.default_rng(0)
        c = rng.normal(size=n_edges)
        parts = hodge_decompose(c, A)
        assert isinstance(parts, HodgeParts)
        # exact reconstruction
        recon = parts.gradient + parts.curl + parts.harmonic
        assert np.linalg.norm(c - recon) < 1e-8
        # pairwise orthogonality
        assert abs(parts.gradient @ parts.curl) < 1e-8
        assert abs(parts.gradient @ parts.harmonic) < 1e-8
        assert abs(parts.curl @ parts.harmonic) < 1e-8

    @pytest.mark.parametrize("fixture", [
        _filled_triangle, _empty_4cycle, _two_disjoint_4cycles, _cycle_with_chord,
        _two_hole_complex,
    ])
    def test_decomposition_idempotent(self, fixture):
        A = fixture()
        n_edges = len(edge_index(A))
        rng = np.random.default_rng(1)
        c = rng.normal(size=n_edges)
        parts = hodge_decompose(c, A)
        # re-decomposing the harmonic part yields itself (already in ker L1)
        parts2 = hodge_decompose(parts.harmonic, A)
        assert np.linalg.norm(parts2.harmonic - parts.harmonic) < 1e-8
        assert np.linalg.norm(parts2.gradient) < 1e-8
        assert np.linalg.norm(parts2.curl) < 1e-8

    def test_harmonic_basis_deterministic(self):
        A = _two_hole_complex()
        b1 = harmonic_basis(A)
        b2 = harmonic_basis(A)
        assert np.array_equal(b1, b2)

    def test_harmonic_basis_orthonormal(self):
        A = _two_hole_complex()
        basis = harmonic_basis(A)
        gram = basis.T @ basis
        assert np.allclose(gram, np.eye(basis.shape[1]), atol=1e-8)

    @pytest.mark.parametrize("fixture,expected_beta1", [
        (_filled_triangle, 0),
        (_empty_4cycle, 1),
        (_two_disjoint_4cycles, 2),
    ])
    def test_l1_spectrum_smallest_eigenvalue_zero_beta1_times(self, fixture, expected_beta1):
        A = fixture()
        n_edges = len(edge_index(A))
        k = max(1, min(n_edges, expected_beta1 + 1))
        vals, vecs = l1_spectrum(A, k=k)
        assert vecs.shape == (n_edges, k)
        n_zero = int(np.sum(np.abs(vals) < 1e-8))
        assert n_zero == expected_beta1

    def test_size_guard_raises_past_ceiling(self):
        """Falsifier target: the guard must raise, never silently switch solver, past the ceiling.
        Exercised via a mock shape (constructing a real >20k-edge complex is unnecessary)."""
        n = 300   # a complete-ish dense graph pushes edge count past the guard cheaply
        rng = np.random.default_rng(2)
        A_dense = (rng.random((n, n)) < 0.9).astype(float)
        A_dense = np.triu(A_dense, k=1)
        A_dense = A_dense + A_dense.T
        A = sp.csr_matrix(A_dense)
        n_edges = len(edge_index(A))
        assert n_edges > _MAX_DENSE_EDGES
        with pytest.raises(ValueError, match="dense-path guard"):
            harmonic_basis(A)
        with pytest.raises(ValueError, match="dense-path guard"):
            hodge_decompose(np.zeros(n_edges), A)
        with pytest.raises(ValueError, match="dense-path guard"):
            l1_spectrum(A, k=1)

    def test_degenerate_empty_and_singleton_graphs_are_honest_not_faked(self):
        """The honest-seam pattern (design note §2.3): a degenerate complex (no nodes, or one
        isolated node — no edges either way) yields empty results, never a fabricated shape."""
        empty = sp.csr_matrix((0, 0))
        assert edge_index(empty) == {}
        assert flag_triangles(empty).shape == (0, 3)
        assert boundary_1(empty).shape == (0, 0)
        assert boundary_2(empty).shape == (0, 0)
        assert hodge_laplacian_1(empty).shape == (0, 0)
        assert harmonic_basis(empty).shape == (0, 0)
        vals, vecs = l1_spectrum(empty, k=1)
        assert vals.shape == (0,) and vecs.shape == (0, 0)

        singleton = sp.csr_matrix((1, 1))
        assert edge_index(singleton) == {}
        assert hodge_laplacian_1(singleton).shape == (0, 0)
        assert harmonic_basis(singleton).shape == (0, 0)


# --- Item 3: the live cross-check (ripser vs incidence algebra) --------------------------------

class TestItem3CrossCheckHarness:
    @pytest.mark.parametrize("sigma", [0.3, 0.5, 0.7])
    def test_ripser_and_incidence_algebra_agree_on_ring_fixture(self, sigma):
        """Falsifier (design note verbatim): at matching scale, dim ker L1 != ripser's alive-bar
        count. Hermetic: three sigma values, exercising the scale-matching logic itself."""
        pts = _ring_points(8)
        D = cosine_distance_matrix(pts)
        incidence_beta1 = dim_ker_l1_at_sigma(pts, sigma=sigma)
        ripser_beta1 = ripser_alive_h1_count(D, sigma=sigma)
        assert incidence_beta1 == ripser_beta1   # exact integer equality, no tolerance

    def test_cross_check_agrees_on_filled_triangle_embedding(self):
        """A degenerate case: 3 points close together (effectively a filled triangle at generous
        sigma) — both sides report 0."""
        pts = np.array([[1.0, 0.0], [0.99, 0.05], [0.98, -0.05]])
        D = cosine_distance_matrix(pts)
        for sigma in (0.3, 0.5, 0.9):
            incidence_beta1 = dim_ker_l1_at_sigma(pts, sigma=sigma)
            ripser_beta1 = ripser_alive_h1_count(D, sigma=sigma)
            assert incidence_beta1 == ripser_beta1
