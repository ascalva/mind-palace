"""The generalized Laplacian family L = δ*δ (companion III §2.1–§2.3) — the operator.

Three members, all built from a sparse adjacency, all PSD by construction (the Dirichlet energy
xᵀLx = ‖δx‖² measures disagreement across edges):

  * ordinary       L      = D − A                              (§2.2: diffusion, clusters, Fourier)
  * sym-normalized L_sym  = I − D^{-1/2} A D^{-1/2}            (§2.2: spectral clustering basis)
  * signed         L̄      = D̄ − A_signed,  D̄_ii = Σ_j|A_ij|   (§2.3: balance / frustration)

They differ only in what δ does on an edge (id transport for L/L_sym, ±1 transport for L̄); the
deferred sheaf/hypergraph members are the general-transport cases (companion III §2.4–§2.5), not
built here. scipy.sparse only; deterministic; no model, no network.
"""

from __future__ import annotations

import numpy as np
import scipy.sparse as sp


def _degree(A: sp.csr_matrix) -> np.ndarray:
    """Row sums (weighted degree) as a dense 1-D vector."""
    return np.asarray(A.sum(axis=1)).ravel()


def laplacian(A: sp.csr_matrix) -> sp.csr_matrix:
    """Combinatorial Laplacian L = D − A. dim ker L = number of connected components (§2.2)."""
    d = _degree(A)
    L: sp.csr_matrix = (sp.diags(d) - A).tocsr()
    return L


def laplacian_sym(A: sp.csr_matrix) -> sp.csr_matrix:
    """Symmetric normalized Laplacian L_sym = I − D^{-1/2} A D^{-1/2} (§2.2).

    The eigenbasis for spectral clustering; eigenvalues lie in [0, 2]. Isolated nodes (degree 0)
    contribute a zeroed row/column (D^{-1/2} := 0 there), so the operator is well-defined on a
    graph with singletons — the standard convention."""
    d = _degree(A)
    with np.errstate(divide="ignore"):
        d_inv_sqrt = np.where(d > 0.0, 1.0 / np.sqrt(d), 0.0)
    n = A.shape[0]
    Dis = sp.diags(d_inv_sqrt)
    L: sp.csr_matrix = (sp.identity(n, format="csr") - Dis @ A @ Dis).tocsr()
    return L


def signed_laplacian(A_signed: sp.csr_matrix) -> sp.csr_matrix:
    """Signed Laplacian L̄ = D̄ − A_signed with absolute degree D̄_ii = Σ_j |A_ij| (§2.3).

    PSD, and singular **iff the signed graph is balanced** (λ_min(L̄) = 0 ⇔ balanced; Hou/Kunegis).
    xᵀL̄x = Σ_{+}w(x_u−x_v)² + Σ_{−}w(x_u+x_v)² — the energy that a frustrated cycle cannot drive
    to zero. `balance.py` reads its spectrum for the global dissonance proxy."""
    abs_deg = np.asarray(abs(A_signed).sum(axis=1)).ravel()
    L: sp.csr_matrix = (sp.diags(abs_deg) - A_signed).tocsr()
    return L
