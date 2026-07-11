"""Signed balance & frustration (companion III §2.3) — rigorous contradiction detection.

A signed graph is **balanced** when its nodes 2-color so every + edge stays within a color and
every − edge crosses — the tensions resolve into two coherent camps. When they can't, there is
**frustration**: irreducible dissonance. Two readings, both exact/cheap and model-free:

  * **global** — λ_min(L̄) of the signed Laplacian is a dissonance proxy: λ_min = 0 ⇔ balanced
    (Hou; Kunegis). It rises as the graph becomes harder to 2-color.
  * **local** — a triangle is frustrated **iff it has an odd number of − edges**; enumerating them
    localizes *which* commitments can't co-hold ("these three can't all be true — you keep circling
    this"). O(#triangles), exact.

This replaces the 0.1 draft's deferred contradiction judge with structure. Deterministic; no model,
no network. The signed adjacency comes from `build_complex` (persisted contradiction edges overlaid
on the similarity backbone); with no contradictions the graph is all-support and trivially balanced.
"""

from __future__ import annotations

import numpy as np
import scipy.sparse as sp

from core.complex.laplacian import signed_laplacian

_DENSE_MAX = 4


def signed_spectrum(A_signed: sp.csr_matrix) -> float:
    """The dissonance proxy: the MAX over connected components of λ_min(L̄) on that component.

    On a CONNECTED graph this is exactly §2.3's λ_min(L̄) (0 ⇔ balanced, Hou/Kunegis). On a
    disconnected graph the raw global λ_min is the *min* over components (L̄ is block-diagonal),
    so one balanced domain — or a single isolated note — would MASK a frustrated triangle
    elsewhere. A dissonance detector must register tension anywhere, so we take the max; every
    component balanced ⇔ 0 either way. Components of size < 2 are trivially balanced and skipped.
    Deterministic (fixed ARPACK start; dense-exact fallback)."""
    n = A_signed.shape[0]
    if n < 2:
        return 0.0
    from scipy.sparse.csgraph import connected_components
    A_signed = A_signed.tocsr()
    _n_comp, comp = connected_components(abs(A_signed), directed=False)
    worst = 0.0
    for c in np.unique(comp):
        members = np.where(comp == c)[0]
        if len(members) < 2:
            continue
        worst = max(worst, _lambda_min(signed_laplacian(A_signed[members][:, members])))
    return worst


def _lambda_min(L: sp.csr_matrix) -> float:
    """Smallest eigenvalue of one component's signed Laplacian (clamped at 0 for fp noise).

    The fixed ARPACK start is a normalized ramp, NOT the uniform vector: on a balanced
    all-positive component the uniform vector IS the exact kernel eigenvector, and Lanczos
    breaks down when started on an exact eigenvector (zero residual ⇒ ARPACK error −9). Any
    ARPACK failure falls back to the dense solve, which is exact."""
    m = L.shape[0]
    if m <= _DENSE_MAX:
        return float(max(0.0, np.linalg.eigvalsh(L.toarray())[0]))
    from scipy.sparse.linalg import eigsh
    v0 = np.arange(1, m + 1, dtype=float)
    v0 /= np.linalg.norm(v0)
    try:
        vals = eigsh(L.astype(float), k=1, which="SA", v0=v0, return_eigenvectors=False)
    except Exception:                            # ARPACK breakdown/stall — dense is exact
        vals = np.linalg.eigvalsh(L.toarray())
    return float(max(0.0, vals[0]))


def is_balanced(A_signed: sp.csr_matrix, *, tol: float = 1e-8) -> bool:
    """True iff the signed graph is balanced (λ_min(L̄) ≈ 0 within `tol`)."""
    return signed_spectrum(A_signed) <= tol


def frustrated_triangles(A_signed: sp.csr_matrix) -> list[tuple[int, int, int]]:
    """Every frustrated triangle (i<j<k with all three edges present and an ODD number of −
    edges) — the specific unresolved tensions. Sorted, deterministic. O(#triangles)."""
    A = A_signed.tocsr()
    n = A.shape[0]
    # neighbor sets and signs (undirected; use upper info symmetrically)
    neighbors: list[set[int]] = [set() for _ in range(n)]
    coo = A.tocoo()
    sign: dict[tuple[int, int], int] = {}
    for ci, cj, v in zip(coo.row, coo.col, coo.data, strict=True):
        if ci == cj or v == 0.0:
            continue
        neighbors[int(ci)].add(int(cj))
        a, b = (int(ci), int(cj)) if ci < cj else (int(cj), int(ci))
        sign[(a, b)] = 1 if v > 0 else -1
    out: list[tuple[int, int, int]] = []
    for i in range(n):
        for j in sorted(x for x in neighbors[i] if x > i):
            for k in sorted(x for x in (neighbors[i] & neighbors[j]) if x > j):
                s = sign[(i, j)] * sign[(j, k)] * sign[(i, k)]
                if s < 0:                        # odd number of negative edges
                    out.append((i, j, k))
    return out


def frustration(A_signed: sp.csr_matrix) -> tuple[float, list[tuple[int, int, int]]]:
    """(λ_min(L̄), frustrated_triangles) — the global dissonance proxy plus the localized tensions
    (companion III §2.3 contract). Balanced graph ⇒ (0.0, [])."""
    return signed_spectrum(A_signed), frustrated_triangles(A_signed)
