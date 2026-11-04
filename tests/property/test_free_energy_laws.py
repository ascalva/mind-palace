"""The retrieval curve's laws (`docs/LAWS.md` §X, RSP-1 to RSP-4), on the code's own
`core/query.py::free_energy_distances`.

The β-curve of `docs/design-notes/temporal-retrieval-algebra.md` §2.1 (Theorem A1): weights in
`[0, 1]`, the reference walk `P = D⁻¹W`, the killed walk `W_β = z·P∘w^β` with `z = γ`,
`Z = (I − W_β)⁻¹`, the free energy `φ_ij = −log(z_ij / z_jj) / β`, symmetrized. Each law is
checked on the code's output against objects built here from their definitions: the support's
reachability, and the kernel `G_β = (D − z·W∘W^β)⁻¹`. `formal/Palace/Retrieval.lean` proves the
four over exact arithmetic.

Controls: past the default `β = 1`, `K_struct = e^{−d}` is not positive semidefinite (K₂,₃ with
weights 0.9 at β = 100), so RSP-3's restriction to `β = 1` is load-bearing; the kernel identity
fails with the degrees on the wrong side, `Z = D G`; and the free energy without its `z_jj`
normalization breaks the triangle inequality.
"""

from __future__ import annotations

import itertools

import numpy as np
import scipy.sparse as sp
from hypothesis import assume, given, settings
from hypothesis import strategies as st
from scipy.sparse.csgraph import connected_components

from core.kernel.recursion import DEFAULT_GAMMA
from core.query import free_energy_distances
from tests.fixtures.graphs import graphs

betas = st.sampled_from([0.1, 0.5, 1.0, 2.0, 5.0])
# float64 sums and logarithms: the laws hold exactly, the code's output to rounding.
RTOL = 1e-9


def _weights(A: sp.csr_matrix) -> np.ndarray:
    return A.toarray()


def _components(a: np.ndarray) -> np.ndarray:
    return connected_components(sp.csr_matrix((a > 0).astype(float)), directed=False)[1]


def _killed(a: np.ndarray, beta: float, z: float = DEFAULT_GAMMA) -> np.ndarray:
    """`W_β = z·P∘w^β` from its definition."""
    deg = a.sum(axis=1)
    p = np.divide(a, deg[:, None], out=np.zeros_like(a), where=deg[:, None] > 0)
    return z * p * np.power(a, beta, where=a > 0, out=np.zeros_like(a))


def _kernel(a: np.ndarray, beta: float, z: float = DEFAULT_GAMMA) -> np.ndarray:
    """`G_β = (D − z·W∘W^β)⁻¹` from its definition."""
    wb = np.power(a, beta, where=a > 0, out=np.zeros_like(a))
    return np.linalg.inv(np.diag(a.sum(axis=1)) - z * a * wb)


def _k23(w: float) -> np.ndarray:
    a = np.zeros((5, 5))
    for i in (0, 1):
        for j in (2, 3, 4):
            a[i, j] = a[j, i] = w
    return a


@settings(max_examples=200, deadline=None)
@given(graphs(), betas)
def test_unreachable_pairs_and_only_they_are_infinite(A, beta):
    """RSP-1: the walk sum is well posed under `z = γ < 1` (no singular solve), and `z_ij > 0`
    exactly when `j` is reachable from `i`, so `+∞` marks exactly the pairs in different
    components; the diagonal is zero."""
    a = _weights(A)
    d = free_energy_distances(a, beta=beta)
    labels = _components(a)
    same = labels[:, None] == labels[None, :]
    assert (np.isinf(d) == ~same).all()
    assert (np.diag(d) == 0).all()


@settings(max_examples=200, deadline=None)
@given(graphs(), betas)
def test_exp_of_minus_beta_d_is_the_normalized_kernel(A, beta):
    """RSP-2 and RSP-3: on a connected support with every degree positive, the kernel `G_β` is
    symmetric positive definite and `e^{−β d_ij} = G_ij / √(G_ii G_jj)`."""
    a = _weights(A)
    assume(a.shape[0] >= 2 and len(set(_components(a))) == 1)
    g = _kernel(a, beta)
    np.testing.assert_allclose(g, g.T, rtol=RTOL, atol=0)
    assert np.linalg.eigvalsh((g + g.T) / 2).min() > 0
    d = free_energy_distances(a, beta=beta)
    root = np.sqrt(np.diag(g))
    np.testing.assert_allclose(np.exp(-beta * d), g / np.outer(root, root), rtol=1e-8)


@settings(max_examples=200, deadline=None)
@given(graphs())
def test_k_struct_is_psd_at_the_default_beta(A):
    """RSP-3: at the code's default `β = 1`, `K_struct = e^{−d}` is positive semidefinite on a
    connected support: the HYBRID Schur product stays in the PSD cone there."""
    a = _weights(A)
    assume(a.shape[0] >= 2 and len(set(_components(a))) == 1)
    k = np.exp(-free_energy_distances(a, beta=1.0))
    assert np.linalg.eigvalsh(k).min() >= -1e-12


@settings(max_examples=200, deadline=None)
@given(graphs(), betas)
def test_the_distance_is_a_pseudometric(A, beta):
    """RSP-4: symmetric, zero on the diagonal, nonnegative, and the triangle inequality on every
    triple of finite distances."""
    a = _weights(A)
    d = free_energy_distances(a, beta=beta)
    np.testing.assert_array_equal(d, d.T)
    assert (np.diag(d) == 0).all() and (d >= 0).all()
    n = a.shape[0]
    scale = max(1.0, float(np.abs(d[np.isfinite(d)]).max(initial=0.0)))
    for i, j, k in itertools.product(range(n), repeat=3):
        if np.isfinite(d[i, j]) and np.isfinite(d[j, k]):
            assert d[i, k] <= d[i, j] + d[j, k] + RTOL * scale


def test_k_struct_is_not_psd_past_the_default_beta():
    """Control: K₂,₃ with weights 0.9 has a shortest-path metric of no negative type, so past β*
    the free-energy distance loses it too, and at β = 100 `e^{−d}` has a negative eigenvalue: the
    HYBRID kernel is PSD at `β = 1`, not at every β."""
    k = np.exp(-free_energy_distances(_k23(0.9), beta=100.0))
    assert np.linalg.eigvalsh(k).min() < -1e-3


def test_the_kernel_identity_needs_the_degrees_on_the_right():
    """Control: on a path with unequal degrees, `Z = G D` holds and `Z = D G` does not."""
    a = np.array([[0.0, 0.5, 0.0], [0.5, 0.0, 0.8], [0.0, 0.8, 0.0]])
    z = np.linalg.inv(np.eye(3) - _killed(a, 1.0))
    g, deg = _kernel(a, 1.0), np.diag(a.sum(axis=1))
    np.testing.assert_allclose(z, g @ deg, rtol=RTOL)
    assert not np.allclose(z, deg @ g, rtol=1e-6)


def test_the_unnormalized_free_energy_breaks_the_triangle():
    """Control: on the path 0–1–2 with unit weights, `−log z_ij / β` without the `z_jj`
    normalization breaks the triangle inequality the code's distance keeps."""
    a = np.array([[0.0, 1.0, 0.0], [1.0, 0.0, 1.0], [0.0, 1.0, 0.0]])
    z = np.linalg.inv(np.eye(3) - _killed(a, 1.0))
    phi = -np.log(z)
    assert max(phi[i, k] - phi[i, j] - phi[j, k]
               for i, j, k in itertools.product(range(3), repeat=3)) > 0.1
    d = free_energy_distances(a, beta=1.0)
    assert all(d[i, k] <= d[i, j] + d[j, k] + 1e-12
               for i, j, k in itertools.product(range(3), repeat=3))
