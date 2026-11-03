"""Direct falsifiers for the Laplacian family (MF-2; `docs/LAWS.md` §II: LAP-2, LAP-3, LAP-4's
degree-0 convention and SPC-2).

Until these, the laws were documented rather than asserted: PSD of L and L̄ only implied by spectra
in range, the nullity never counted, the degree-0 convention never checked pointwise, and the
never-merge rule seen only through a clustering outcome. Hypothesis draws small weighted graphs and
each law is checked on the code's own operators. Each law also has a control, a deliberately wrong
operator the same check must reject, so none of these is a falsifier that cannot fail (the note's
§3, MF-2).
"""

from __future__ import annotations

import numpy as np
import pytest
import scipy.sparse as sp
from hypothesis import given, settings
from hypothesis import strategies as st
from scipy.sparse.csgraph import connected_components

from core.complex.spectral import spectral_labels
from core.kernel.complex.laplacian import laplacian, laplacian_sym, signed_laplacian
from tests.fixtures.graphs import graphs

# The float64 tolerance LAP-2's row defers to this falsifier: a quadratic form or an eigenvalue is
# nonnegative when it is above −TOL·scale, `scale` the largest absolute entry of the operator, at
# least 1. A true zero eigenvalue comes out near 1e-15·scale; on these graphs λ₂ is above 1e-4.
TOL = 1e-9


def _scale(m: np.ndarray) -> float:
    return max(1.0, float(np.abs(m).max(initial=0.0)))


def _is_psd(m: np.ndarray) -> bool:
    return bool(np.linalg.eigvalsh(m).min(initial=0.0) >= -TOL * _scale(m))


def _nullity(m: np.ndarray) -> int:
    return int((np.abs(np.linalg.eigvalsh(m)) <= TOL * _scale(m)).sum())


# ── LAP-2: L and L̄ are PSD, through their energies ──────────────────────────────────────────────

@settings(deadline=None, max_examples=200)
@given(A=graphs(), seed=st.integers(min_value=0, max_value=2**32 - 1))
def test_the_laplacian_is_psd_and_its_form_is_the_dirichlet_energy(A, seed):
    """LAP-2: `xᵀLx = Σ_{u<v} w_uv (x_u − x_v)²`, expanding `D − A` over the pairs, a sum of
    nonnegative terms for symmetric `A ≥ 0`; so `L` is PSD."""
    L, a = laplacian(A).toarray(), A.toarray()
    x = np.random.default_rng(seed).normal(size=a.shape[0])
    n = len(x)
    energy = sum(a[u, v] * (x[u] - x[v]) ** 2 for u in range(n) for v in range(u + 1, n))
    assert x @ L @ x == pytest.approx(energy, rel=1e-9, abs=TOL * _scale(L) * (x @ x))
    assert _is_psd(L)


@settings(deadline=None, max_examples=200)
@given(A=graphs(signed=True), seed=st.integers(min_value=0, max_value=2**32 - 1))
def test_the_signed_laplacian_is_psd_through_its_signed_identity(A, seed):
    """LAP-2: `xᵀL̄x = Σ_{w>0} w (x_u − x_v)² + Σ_{w<0} |w| (x_u + x_v)²`, expanding `D̄ − A` over
    the pairs with `D̄` the absolute degrees, a sum of nonnegative terms for symmetric `A` of any
    sign; so `L̄` is PSD."""
    L, a = signed_laplacian(A).toarray(), A.toarray()
    x = np.random.default_rng(seed).normal(size=a.shape[0])
    n = len(x)
    energy = sum(abs(a[u, v]) * (x[u] - np.sign(a[u, v]) * x[v]) ** 2
                 for u in range(n) for v in range(u + 1, n))
    assert x @ L @ x == pytest.approx(energy, rel=1e-9, abs=TOL * _scale(L) * (x @ x))
    assert _is_psd(L)


def test_the_psd_check_rejects_the_unsigned_laplacian_of_a_signed_graph():
    """Control: `laplacian` on a signed adjacency, the slip `signed_laplacian` exists to prevent,
    is not PSD: one negative edge has eigenvalue `−2|w|`."""
    A = sp.csr_matrix(np.array([[0.0, -0.5], [-0.5, 0.0]]))
    assert _is_psd(signed_laplacian(A).toarray())
    assert not _is_psd(laplacian(A).toarray())


# ── LAP-3: the nullity counts the components ────────────────────────────────────────────────────

@settings(deadline=None, max_examples=200)
@given(A=graphs())
def test_the_nullity_of_the_laplacian_counts_the_components(A):
    """LAP-3: `dim ker L` is the number of connected components of the support, for symmetric
    `A ≥ 0`, counted on the code's float64 `L` at the tolerance above."""
    n_comp, _ = connected_components(A, directed=False)
    assert _nullity(laplacian(A).toarray()) == n_comp


def test_the_nullity_check_rejects_the_signless_laplacian():
    """Control: the signless `D + A` has nullity the number of bipartite components, so on a
    triangle it counts none where there is one component."""
    tri = sp.csr_matrix(np.ones((3, 3)) - np.eye(3))
    signless = np.diag(np.asarray(tri.sum(axis=1)).ravel()) + tri.toarray()
    assert _nullity(laplacian(tri).toarray()) == 1
    assert _nullity(signless) == 0


# ── LAP-4: the degree-0 convention, pointwise ───────────────────────────────────────────────────

def _with_isolated(A: sp.csr_matrix, extra: int, stored_zeros: bool) -> sp.csr_matrix:
    """`A` with `extra` isolated vertices appended; with `stored_zeros`, each carries an explicitly
    stored `0.0` to every other vertex, as a thresholded adjacency can."""
    n = A.shape[0] + extra
    coo = A.tocoo()
    rows, cols, data = coo.row.tolist(), coo.col.tolist(), coo.data.tolist()
    if stored_zeros:
        for v in range(A.shape[0], n):
            for u in range(n):
                if u != v:
                    rows += [v, u]
                    cols += [u, v]
                    data += [0.0, 0.0]
    return sp.csr_matrix((data, (rows, cols)), shape=(n, n))


def _identity_rows_at_degree_zero(A: sp.csr_matrix, L_sym: np.ndarray) -> bool:
    deg = np.asarray(A.sum(axis=1)).ravel()
    for v in np.flatnonzero(deg == 0.0):
        e = np.zeros(A.shape[0])
        e[v] = 1.0
        if not (np.array_equal(L_sym[v], e) and np.array_equal(L_sym[:, v], e)):
            return False
    return True


@settings(deadline=None, max_examples=200)
@given(A=graphs(), extra=st.integers(min_value=1, max_value=3), stored_zeros=st.booleans())
def test_an_isolated_vertex_has_an_identity_row_in_the_normalized_laplacian(A, extra,
                                                                            stored_zeros):
    """LAP-4's convention, pointwise: `D^{−1/2} := 0` at degree 0, so every isolated vertex has
    row and column `e_v` in `L_sym`, exactly, even where zeros are stored against it."""
    B = _with_isolated(A, extra, stored_zeros)
    L_sym = laplacian_sym(B).toarray()
    assert np.isfinite(L_sym).all()
    assert _identity_rows_at_degree_zero(B, L_sym)


def test_the_identity_row_check_rejects_the_naive_inverse_square_root():
    """Control: without the convention `1/√0 = ∞`, and against a stored zero `∞·0` is NaN, so the
    isolated vertex's row is not `e_v`."""
    B = _with_isolated(sp.csr_matrix(np.array([[0.0, 1.0], [1.0, 0.0]])), 1, stored_zeros=True)
    deg = np.asarray(B.sum(axis=1)).ravel()
    with np.errstate(divide="ignore", invalid="ignore"):
        dis = sp.diags(1.0 / np.sqrt(deg))
        naive = (sp.identity(3, format="csr") - dis @ B @ dis).toarray()
    assert _identity_rows_at_degree_zero(B, laplacian_sym(B).toarray())
    assert not _identity_rows_at_degree_zero(B, naive)


# ── SPC-2: components are never merged ──────────────────────────────────────────────────────────

@st.composite
def disjoint_unions(draw: st.DrawFn) -> tuple[sp.csr_matrix, np.ndarray]:
    """A disjoint union of one to four connected components of one to six vertices each (a path
    keeps each connected, chords are random), its vertices shuffled; and each vertex's
    component."""
    sizes = draw(st.lists(st.integers(min_value=1, max_value=6), min_size=1, max_size=4))
    n = sum(sizes)
    a = np.zeros((n, n))
    comp = np.empty(n, dtype=np.int64)
    start = 0
    for c, size in enumerate(sizes):
        for i in range(start, start + size):
            for j in range(i + 1, start + size):
                if j == i + 1 or draw(st.booleans()):
                    a[i, j] = a[j, i] = draw(st.floats(min_value=0.05, max_value=1.0))
        comp[start:start + size] = c
        start += size
    perm = np.asarray(draw(st.permutations(range(n))), dtype=np.int64)
    return sp.csr_matrix(a[np.ix_(perm, perm)]), comp[perm]


def _never_merged(labels: np.ndarray, comp: np.ndarray) -> bool:
    groups = [set(labels[comp == c].tolist()) for c in np.unique(comp)]
    return all(g.isdisjoint(h) for i, g in enumerate(groups) for h in groups[i + 1:])


@settings(deadline=None, max_examples=100)
@given(union=disjoint_unions())
def test_distinct_components_never_share_a_cluster_label(union):
    """SPC-2: components are clustered independently and never merged: the label sets of two
    distinct components are disjoint."""
    A, comp = union
    assert _never_merged(spectral_labels(A), comp)


def test_the_never_merge_check_rejects_labels_without_the_per_component_offset():
    """Control: each component's own labels, restarted at 0 (the offset `spectral_labels` adds,
    left out), put two triangles in one cluster."""
    A = sp.csr_matrix(np.kron(np.eye(2), np.ones((3, 3)) - np.eye(3)))
    _, comp = connected_components(A, directed=False)
    assert _never_merged(spectral_labels(A), comp)
    assert not _never_merged(np.zeros(6, dtype=np.int64), comp)
