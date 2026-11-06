"""SPC-3's falsifier: when a tolerance tells zero from nonzero (docs/LAWS.md, II).

The law (`formal/Palace/Gap.lean`) takes NumPy's backward stability as its hypothesis: an SVD or a
symmetric eigensolver returns the exact values of a matrix within `8·n·u·‖A‖` of the float64 one
(LAPACK's "modestly growing" `p(n)`, taken as `8n`), and a weighted Laplacian, whose degree sums
float64 forms within `n·u·‖L‖`, so carries `ε = 9·n·u·‖L‖`. The eigenvalue errors measured here on
matrices whose spectra are known in closed form reach `3.3·n·u·‖A‖` (the SVD of a 19-cycle), a lower
bound on the backward error, so consistent with the hypothesis and not a proof of it. Each
tolerance's gap condition is checked on fixtures: the Hodge rank cut on flag complexes with known
β₁, the pseudo-inverse's cut and the rise threshold on weighted graphs like the conductance
profile's, and on each the kernel's computed values lie within the hypothesis' `ε`. The control is a
graph the condition refuses, two clusters joined by a bridge far lighter than the cut, where the cut
does lose the bridge's mode. The rise threshold's condition rests also on Wedin's bound for the
pseudo-inverse, cited and not formalized; it holds where the gap allows, and the last test records a
graph where it does not.
"""

from __future__ import annotations

import math

import numpy as np
import numpy.typing as npt
import scipy.sparse as sp
from scipy.sparse.csgraph import connected_components

from core.graph.conductance import (
    _PINV_RTOL,
    _RISE_EPS,
    _components,
    _dense_laplacian,
    _pair_conductance,
    _r_eff_matrix,
)
from core.kernel.complex.hodge import _RANK_TOL, harmonic_basis, hodge_laplacian_1

F64 = npt.NDArray[np.float64]
U = 2.0 ** -53


C = 8          # the decomposition's constant: ‖E‖ ≤ C·n·u·‖A‖
FORMED = C + 1  # a weighted Laplacian's: its degree sums add n·u·‖L‖ before the decomposition
MU = (1 + math.sqrt(5)) / 2     # Wedin's constant for the pseudo-inverse in the 2-norm


def eps_bound(values: F64, c: float = C) -> float:
    """`ε ≤ c·n·u·‖A‖`, with `‖A‖ ≤ max σ̂ + ε` by Weyl: the hypothesis, from computed values."""
    cnu = c * len(values) * U
    return cnu * float(np.max(values)) / (1 - cnu)


def decisive(values: F64, rtol: float, nullity: int, c: float = C) -> bool:
    """SPC-3's conditions for the cut `rtol · max σ̂`: `ε ≤ θ` and `θ + ε < g`, with `g` at least the
    `(nullity + 1)`-th smallest computed value less `ε` (Weyl)."""
    s = np.sort(values)
    eps, theta = eps_bound(values, c), rtol * float(s[-1])
    return eps <= theta and (nullity == len(s) or theta + eps < float(s[nullity]) - eps)


def _svals(a: F64) -> F64:
    return np.asarray(np.linalg.svd(a, compute_uv=False), dtype=np.float64)


def _laplacian(n: int, edges: list[tuple[int, int, float]]) -> F64:
    w = np.zeros((n, n))
    for i, j, x in edges:
        w[i, j] = w[j, i] = x
    return np.asarray(np.diag(w.sum(axis=1)) - w, dtype=np.float64)


def test_the_backward_error_hypothesis_holds_on_known_spectra() -> None:
    worst = 0.0
    for n in range(3, 61):
        k = np.arange(n)
        cases = [
            (_laplacian(n, [(i, (i + 1) % n, 1.0) for i in range(n)]),
             2 - 2 * np.cos(2 * np.pi * k / n)),
            (_laplacian(n, [(i, i + 1, 1.0) for i in range(n - 1)]), 2 - 2 * np.cos(np.pi * k / n)),
            (_laplacian(n, [(i, j, 1.0) for i in range(n) for j in range(i + 1, n)]),
             np.where(k == 0, 0.0, float(n))),
        ]
        for a, exact in cases:
            ref = np.sort(exact)
            for got in (np.sort(_svals(a)), np.sort(np.linalg.eigvalsh(a))):
                ratio = float(np.max(np.abs(got - ref))) / (U * float(ref[-1]))
                worst = max(worst, ratio / n)
                assert np.max(np.abs(got - ref)) <= (C * n + 8) * U * ref[-1]   # 8 u: the reference
    assert worst < C / 2                     # measured at most 3.3: the eigenvalue error, a lower
    # bound on the backward error, consistent with the hypothesis


def _adjacency(n: int, edges: list[tuple[int, int]]) -> sp.csr_matrix:
    a = np.zeros((n, n))
    for i, j in edges:
        a[i, j] = a[j, i] = 1.0
    return sp.csr_matrix(a)


def _cycle(n: int, start: int = 0) -> list[tuple[int, int]]:
    return [(start + i, start + (i + 1) % n) for i in range(n)]


def test_the_hodge_rank_cut_is_decisive_on_flag_complexes() -> None:
    complexes = [
        (_adjacency(3, _cycle(3)), 0),                                    # a filled triangle
        (_adjacency(4, [(i, j) for i in range(4) for j in range(i + 1, 4)]), 0),   # K4
        (_adjacency(8, _cycle(4) + _cycle(4, 4)), 2),                     # two empty squares
        (_adjacency(8, _cycle(5) + [(0, 5), (5, 6), (6, 7), (7, 0)]), 2),  # two holes at a vertex
        *[(_adjacency(n, _cycle(n)), 1) for n in range(4, 40)],
    ]
    for a, beta1 in complexes:
        s = _svals(hodge_laplacian_1(a).toarray())
        assert decisive(s, _RANK_TOL, beta1)
        assert int(np.sum(s <= _RANK_TOL * s.max())) == beta1 == harmonic_basis(a).shape[1]
        assert beta1 == 0 or float(np.sort(s)[beta1 - 1]) <= eps_bound(s)   # the kernel within ε


def _weighted(rng: np.random.Generator, n: int, p: float) -> F64:
    """Cosine-like weights in `[σ, 1]` on a random graph, as the conductance profile builds them."""
    w = np.triu(rng.uniform(0.785, 1.0, (n, n)) * (rng.random((n, n)) < p), 1)
    return np.asarray(w + w.T, dtype=np.float64)


def test_the_pseudo_inverse_cut_is_decisive_on_weighted_graphs() -> None:
    rng = np.random.default_rng(20261105)
    for _ in range(40):
        n = int(rng.integers(10, 120))
        w = _weighted(rng, n, float(rng.uniform(0.03, 0.3)))
        comps = connected_components(sp.csr_matrix(w), directed=False)[0]
        s = _svals(_dense_laplacian(w))
        assert decisive(s, _PINV_RTOL, comps, FORMED)
        assert int(np.sum(s <= _PINV_RTOL * s.max())) == comps
        # the hypothesis' own consequence, by Weyl: the components' computed values lie within ε
        assert float(np.sort(s)[comps - 1]) <= eps_bound(s, FORMED)


def test_control_a_bridge_below_the_cut_fails_the_condition_and_loses_its_mode() -> None:
    bridge = 5e-12                                   # an edge to the components, under the cut
    w = np.zeros((6, 6))
    for i, j in [(0, 1), (1, 2), (0, 2), (3, 4), (4, 5), (3, 5)]:
        w[i, j] = w[j, i] = 1.0
    w[2, 3] = w[3, 2] = bridge
    assert not decisive(_svals(_dense_laplacian(w)), _PINV_RTOL, 1, FORMED)
    r = _r_eff_matrix(w, _components(w))[0, 5]
    exact = 2 / 3 + 1 / bridge + 2 / 3              # two triangles in series through the bridge
    assert r < 1e-3 * exact                          # the cut dropped the bridge's mode


def _rise_bound(w: F64) -> float:
    """SPC-3's bound on a computed conductance's error, over the pairs that share a component:
    `δ = c ĉ (4μ ε / (g (g − ε)) + 4 (n + 3) u / (g − ε)) + u ĉ`. Wedin's bound puts the
    pseudo-inverse of a matrix of L's rank within `2ε` of L within `2μ ε / (g (g − ε))` of L⁺, so
    `R` within twice that (`‖e_i − e_j‖² = 2`); each entry of V·Σ⁺·Uᵀ formed in float64 is within
    `(n + 1) u / (g − ε)`, and R adds four of them and three roundings; `1/R` one more. `c ≤ ĉ (1 +
    10⁻⁶)` for the first factor."""
    labels = _components(w)
    comps = len(set(labels.tolist()))
    s = np.sort(_svals(_dense_laplacian(w)))
    n = len(s)
    eps = eps_bound(s, FORMED)
    g = float(s[comps]) - eps
    r = _r_eff_matrix(w, labels)
    finite = np.isfinite(r) & (r > 0)
    c_hat = float(np.max(1.0 / r[finite]))
    return (c_hat ** 2 * (1 + 1e-6) * (4 * MU * eps / (g * (g - eps)) + 4 * (n + 3) * U / (g - eps))
            + U * c_hat)


def test_the_rise_threshold_is_decisive_where_the_gap_allows() -> None:
    rng = np.random.default_rng(31)
    certified = 0
    for _ in range(40):
        n = int(rng.integers(8, 60))
        w = _weighted(rng, n, float(rng.uniform(0.15, 0.6)))
        # the same graph in a larger index space, beside a second graph: an exact Δ of 0 for its
        # pairs, which the computed conductances must keep within 2δ
        m = int(rng.integers(3, 15))
        big = np.zeros((n + m, n + m))
        big[:n, :n] = w
        big[n:, n:] = _weighted(rng, m, 0.5)
        delta = max(_rise_bound(w), _rise_bound(big))
        if 2 * delta > _RISE_EPS:
            continue                                 # the gap condition fails: SPC-3 is silent
        certified += 1
        labels = _components(w)
        for p, q in [(0, 1), (0, n - 1), (n // 2, n - 1)]:
            if labels[p] == labels[q]:
                assert abs(_pair_conductance(big, p, q) - _pair_conductance(w, p, q)) <= 2 * delta
    assert certified >= 20


def test_the_rise_bound_does_not_reach_a_long_path() -> None:
    """Where SPC-3 stops: on a path of forty notes the least nonzero eigenvalue is about 0.005, and
    the bound on a conductance's error, which grows as its inverse square, passes the absolute
    threshold. The measured movement stays far below it; the law does not say so."""
    w = np.zeros((40, 40))
    for i in range(39):
        w[i, i + 1] = w[i + 1, i] = 0.9
    assert 2 * _rise_bound(w) > _RISE_EPS
    big = np.zeros((45, 45))
    big[:40, :40] = w
    big[40:, 40:] = _weighted(np.random.default_rng(41), 5, 1.0)
    assert abs(_pair_conductance(big, 0, 1) - _pair_conductance(w, 0, 1)) < 1e-3 * _RISE_EPS
