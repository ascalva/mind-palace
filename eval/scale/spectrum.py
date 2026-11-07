"""The smallest eigenvalues of the normalized Laplacian and the quantities built on them."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import scipy.linalg
import scipy.sparse as sp
import scipy.sparse.linalg as spla

from eval.scale.graphs import Component, FloatArr, normalized_laplacian

DENSE_LIMIT = 500
#: Shift for the shift-invert solve. L is positive semidefinite with a zero eigenvalue, so a small
#: negative shift keeps L - sigma I positive definite and the sparse LU well posed.
SIGMA = -1e-2
#: eigsh convergence tolerance (relative); the eigenvalues here are of order 1e-3 to 1.
EIG_TOL = 1e-8


def smallest_eigenvalues(lap: sp.csr_matrix, k: int = 20) -> FloatArr:
    """The `k` smallest eigenvalues of `lap`, ascending.

    Dense `eigh` when the graph has at most DENSE_LIMIT nodes; otherwise `eigsh` in shift-invert
    mode (sigma = SIGMA, which='LM', tol = EIG_TOL), which resolves the small end of the
    spectrum and its clusters far faster than the plain Lanczos iteration.
    """
    n = lap.shape[0]
    k = min(k, n)
    if n <= DENSE_LIMIT or k >= n - 1:
        vals = scipy.linalg.eigvalsh(lap.toarray())
        return np.asarray(np.sort(vals)[:k], dtype=np.float64)
    vals = spla.eigsh(
        lap.tocsc(), k=k, sigma=SIGMA, which="LM", tol=EIG_TOL, return_eigenvectors=False
    )
    return np.asarray(np.sort(vals), dtype=np.float64)


@dataclass(frozen=True)
class CutStats:
    """The macro quantities of one graph."""

    n: int
    m: int
    mean_degree: float
    min_degree: int
    degree_over_logn: float
    mindeg_over_logn: float
    eigenvalues: FloatArr

    @property
    def gamma(self) -> float:
        """The spectral gap, the second-smallest eigenvalue (the first is zero)."""
        return float(self.eigenvalues[1]) if len(self.eigenvalues) > 1 else float("nan")

    def gap(self, k: int) -> float:
        """The eigengap lambda_{k+1} - lambda_k, 1-indexed, so gap(1) equals gamma."""
        if len(self.eigenvalues) <= k:
            return float("nan")
        return float(self.eigenvalues[k] - self.eigenvalues[k - 1])


def cut_stats(comp: Component, k: int = 20) -> CutStats:
    """N, degrees, degree over log N and the smallest `k` eigenvalues of a component."""
    n = comp.n
    if n < 3:
        return CutStats(n, comp.m, 0.0, 0, 0.0, 0.0, np.zeros(0))
    deg = comp.degrees()
    logn = float(np.log(n))
    mean = float(deg.mean())
    mn = int(deg.min())
    eig = smallest_eigenvalues(normalized_laplacian(comp.adj), k)
    return CutStats(n, comp.m, mean, mn, mean / logn, mn / logn, eig)
