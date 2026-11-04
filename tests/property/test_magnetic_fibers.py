"""The magnetic Laplacian's ground in the code (`docs/LAWS.md` §IX, BRG-7).

`docs/design-notes/magnetic-laplacian.md` defers building the magnetic Laplacian
`L^θ = D − H^θ`, `H^θ_{uv} = w_{uv} e^{iθ(u,v)}`, and grounds it in operators the code already
runs. Here `L^θ` is built from that definition in complex NumPy and held against the code: at
`θ = 0` it is `laplacian`, and with weights `|A|` and phase `π` on the negative entries it is
`signed_laplacian`, self-loops included. The kernel half: on a connected support,
`signed_laplacian` has a zero eigenvalue iff the sign connection is flux-trivial and no self-loop
is negative. Flux-trivial is read in its gauge form, a ±1 potential that every edge's sign agrees
with (`GaugeTrivial`; the two are one condition, `gaugeTrivial_of_fluxTrivial`).
`formal/Palace/Magnetic.lean` proves all three over exact arithmetic.

Controls: the zero phase is not the signed fiber once an entry is negative, and the kernel check
without the loop condition misreads a balanced graph that carries one negative self-loop.
"""

from __future__ import annotations

from collections import deque

import numpy as np
import scipy.sparse as sp
from hypothesis import assume, given, settings
from hypothesis import strategies as st
from scipy.sparse.csgraph import connected_components

from core.kernel.complex.laplacian import laplacian, signed_laplacian
from tests.fixtures.graphs import graphs

# `e^{iπ}` in float64 is `−1 + 1.2e-16i`, so the built fiber matches the code's to rounding.
ATOL = 1e-12
# A zero eigenvalue comes out near 1e-15·scale; on these graphs the least nonzero one of a
# connected frustrated support is above 1e-4.
TOL = 1e-9

loops = st.lists(st.sampled_from([0.0, 0.5, -0.5]), min_size=9, max_size=9)


def magnetic(w: np.ndarray, theta: np.ndarray) -> np.ndarray:
    """`L^θ = D − H^θ` from its definition: `D` the row sums of `w`, `H^θ = w ∘ e^{iθ}`."""
    return np.diag(w.sum(axis=1)).astype(complex) - w * np.exp(1j * theta)


def sign_phase(a: np.ndarray) -> np.ndarray:
    """The sign connection: phase `π` on a negative entry, `0` elsewhere."""
    return np.where(a < 0, np.pi, 0.0)


def with_loops(A: sp.csr_matrix, diagonal: list[float]) -> np.ndarray:
    a = A.toarray()
    np.fill_diagonal(a, diagonal[: a.shape[0]])
    return a


def gauge_trivial(a: np.ndarray) -> bool:
    """On a connected support, the sign connection is gauge-trivial: the ±1 potential grown by
    breadth-first search from vertex 0 agrees with the sign of every edge,
    `sign(A_uv) = s_u s_v`."""
    n = a.shape[0]
    s = np.zeros(n)
    s[0] = 1.0
    queue = deque([0])
    while queue:
        u = queue.popleft()
        for v in range(n):
            if v != u and a[u, v] != 0 and s[v] == 0:
                s[v] = s[u] * np.sign(a[u, v])
                queue.append(v)
    return all(np.sign(a[u, v]) == s[u] * s[v]
               for u in range(n) for v in range(n) if u != v and a[u, v] != 0)


def has_zero_eigenvalue(L: np.ndarray) -> bool:
    scale = max(1.0, float(np.abs(L).max(initial=0.0)))
    return bool(np.linalg.eigvalsh(L).min() <= TOL * scale)


def connected(a: np.ndarray) -> bool:
    off = a - np.diag(np.diag(a))
    return connected_components(sp.csr_matrix(off != 0), directed=False)[0] == 1


@settings(max_examples=200, deadline=None)
@given(graphs())
def test_the_laplacian_is_the_zero_phase_fiber(A):
    """BRG-7: at `θ = 0` the magnetic Laplacian is the code's `laplacian`, `D − A`."""
    a = A.toarray()
    np.testing.assert_allclose(magnetic(a, np.zeros_like(a)), laplacian(A).toarray(), atol=ATOL)


@settings(max_examples=200, deadline=None)
@given(graphs(signed=True), loops)
def test_the_signed_laplacian_is_the_sign_phase_fiber(A, diagonal):
    """BRG-7: with weights `|A|` and phase `π` on the negative entries, self-loops included, the
    magnetic Laplacian is the code's `signed_laplacian`, `D̄ − A`."""
    a = with_loops(A, diagonal)
    np.testing.assert_allclose(magnetic(np.abs(a), sign_phase(a)),
                               signed_laplacian(sp.csr_matrix(a)).toarray(), atol=ATOL)


@settings(max_examples=300, deadline=None)
@given(graphs(signed=True), loops)
def test_a_zero_eigenvalue_is_a_flux_trivial_sign_connection_with_no_negative_loop(A, diagonal):
    """BRG-7, the kernel theorem at ℤ/2: on a connected support, `signed_laplacian` has a zero
    eigenvalue iff the sign connection is gauge-trivial and no self-loop is negative."""
    a = with_loops(A, diagonal)
    assume(connected(a))
    off = a - np.diag(np.diag(a))
    zero = has_zero_eigenvalue(signed_laplacian(sp.csr_matrix(a)).toarray())
    assert zero == (gauge_trivial(off) and bool((np.diag(a) >= 0).all()))


def test_the_zero_phase_is_not_the_signed_fiber():
    """Control: with a negative entry, `|A|` at phase `0` is the Laplacian of `|A|`, which the
    fiber check rejects as the signed Laplacian."""
    a = np.array([[0.0, -1.0, 0.5], [-1.0, 0.0, 1.0], [0.5, 1.0, 0.0]])
    assert not np.allclose(magnetic(np.abs(a), np.zeros_like(a)),
                           signed_laplacian(sp.csr_matrix(a)).toarray(), atol=ATOL)


def test_the_kernel_check_needs_the_loop_condition():
    """Control: a triangle balanced by camps `(+, +, −)`, with a negative self-loop at vertex 0.
    Its sign connection is gauge-trivial, yet the negative loop alone is frustrated, so
    `signed_laplacian` has no zero eigenvalue: a check without the loop condition fails."""
    a = np.array([[-0.5, 1.0, -1.0], [1.0, 0.0, -1.0], [-1.0, -1.0, 0.0]])
    off = a - np.diag(np.diag(a))
    assert connected(a) and gauge_trivial(off)
    zero = has_zero_eigenvalue(signed_laplacian(sp.csr_matrix(a)).toarray())
    assert zero != gauge_trivial(off)
    assert zero == (gauge_trivial(off) and bool((np.diag(a) >= 0).all()))
