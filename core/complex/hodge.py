"""The Hodge 1-Laplacian family (companion III lift; design note `dn-edge-dynamics` §2.2) —
the degree-1 instruments over the existing backbone.

Lifts the degree-0 family (`laplacian.py`: L, L_sym, signed L̄) one degree, over the **flag
(clique) complex** of the weighted similarity backbone `A` (`build.py`'s `cosine_adjacency`
output — symmetric, zero-diagonal, w ≥ 0): 1-simplices are `A`'s edges, 2-simplices are the
3-cliques those edges imply. This choice is forced by Rips consistency (the design note's
Q2/§2.2): `topology.py`'s persistence runs Vietoris–Rips over `cosine_distance_matrix`, and
Rips at scale t IS the flag complex of the distance-≤t graph, so the persistent H₁ computed
there and `dim ker L₁` computed here describe the same object at matching scale
(`distance = 1 − similarity`). Derivation hyperedges (`ReasoningComplex.hyper`) are directed
B-arcs, not symmetric 2-simplices — they stay out (design note PD-a).

Orientation: each edge {i, j} oriented i→j by ascending node index; each triangle {i, j, k} by
ascending index triple (design note §2.2). Convention only — every quantity below is
orientation-invariant. Boundary operators `∂₁`/`∂₂` are the signed incidence matrices; `L₁ =
∂₁ᵀ∂₁ + ∂₂∂₂ᵀ` (down + up) is PSD by construction, `dim ker L₁ = β₁` of the flag complex. Any
edge vector (1-cochain) splits uniquely into **gradient** (im ∂₁ᵀ, induced by node potentials),
**curl** (im ∂₂, circulation around filled triangles), and **harmonic** (ker L₁, the threads) —
the three mutually orthogonal under the combinatorial (v1, unweighted — PD-b parked) inner
product.

Determinism pin (§6(e)): the harmonic basis and decomposition use DENSE numpy linear algebra
(SVD null space; projectors via lstsq) — exactly reproducible, no iterative-solver
nondeterminism. A guard raises `ValueError` when `n_edges > 20_000` (an order of magnitude
above today's corpus scale), naming the future sparse-eigensolver upgrade as a deliberate act,
never a silent switch. scipy.sparse + numpy only; deterministic; no model, no network, no store
handle (module contract per the complex family, `laplacian.py`'s house style).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import scipy.sparse as sp

# §6(e): the dense null-space/projector path is licensed only below this many edges; past it a
# sparse-eigensolver upgrade is a deliberate future act (design note §2.5, Q3), never a silent
# fallback to a nondeterministic iterative solver.
_MAX_DENSE_EDGES = 20_000

# Rank cut for the dense SVD null space (§6(e)): singular values below this fraction of the
# largest are treated as numerically zero.
_RANK_TOL = 1e-10


def edge_index(A: sp.csr_matrix) -> dict[tuple[int, int], int]:
    """C₁ basis: edges {i, j} with i < j (A's upper triangle), lexicographic order.

    Orientation i→j by ascending node index. Deterministic from A's sparsity pattern only (not
    A's weights) — two structurally identical adjacencies index their edges identically."""
    coo = sp.triu(A, k=1).tocoo()
    pairs = sorted({(int(i), int(j)) for i, j, v in zip(coo.row, coo.col, coo.data, strict=True)
                   if v != 0.0})
    return {pair: k for k, pair in enumerate(pairs)}


def flag_triangles(A: sp.csr_matrix) -> np.ndarray:
    """C₂ basis: the 3-cliques {i, j, k}, i < j < k, lexicographic. The FLAG complex — forced by
    Rips consistency (design note §2.2, plan Q2); derivation hyperedges stay out (note §2.2,
    PD-a). Shape (n_tri, 3), int64; empty complex ⇒ shape (0, 3)."""
    n = A.shape[0]
    upper = sp.triu(A, k=1).tocsr()
    neighbors: list[set[int]] = [set() for _ in range(n)]
    coo = upper.tocoo()
    for i, j, v in zip(coo.row, coo.col, coo.data, strict=True):
        if v == 0.0:
            continue
        neighbors[int(i)].add(int(j))
        neighbors[int(j)].add(int(i))
    triangles: list[tuple[int, int, int]] = []
    for i in range(n):
        js = sorted(x for x in neighbors[i] if x > i)
        for jpos, j in enumerate(js):
            for k in js[jpos + 1:]:
                if k in neighbors[j]:
                    triangles.append((i, j, k))
    if not triangles:
        return np.zeros((0, 3), dtype=np.int64)
    return np.asarray(sorted(triangles), dtype=np.int64)


def boundary_1(A: sp.csr_matrix) -> sp.csr_matrix:
    """∂₁ : C₁ → C₀, shape (n_nodes, n_edges). ∂₁(e_ij) = δ_j − δ_i (§6(c)).

    The signed node-edge incidence matrix — the down-boundary of the degree-1 lift, the same
    incidence structure `laplacian.py`'s combinatorial L = ∂₁∂₁ᵀ = D − A already implies."""
    n = A.shape[0]
    idx = edge_index(A)
    n_edges = len(idx)
    if n_edges == 0:
        return sp.csr_matrix((n, 0))
    rows = np.empty(2 * n_edges, dtype=np.int64)
    cols = np.empty(2 * n_edges, dtype=np.int64)
    data = np.empty(2 * n_edges, dtype=np.float64)
    for (i, j), e in idx.items():
        rows[2 * e], cols[2 * e], data[2 * e] = i, e, -1.0
        rows[2 * e + 1], cols[2 * e + 1], data[2 * e + 1] = j, e, 1.0
    return sp.csr_matrix((data, (rows, cols)), shape=(n, n_edges))


def boundary_2(A: sp.csr_matrix) -> sp.csr_matrix:
    """∂₂ : C₂ → C₁, shape (n_edges, n_tris). ∂₂(t_ijk) = e_jk − e_ik + e_ij (§6(c)).

    The up-boundary: each filled triangle's oriented edges. The fundamental chain-complex
    identity ∂₁∂₂ = 0 holds exactly for this sign convention (Item 1's falsifier — any sign
    error here breaks it on some fixture)."""
    idx = edge_index(A)
    n_edges = len(idx)
    tris = flag_triangles(A)
    n_tri = tris.shape[0]
    if n_tri == 0:
        return sp.csr_matrix((n_edges, 0))
    rows = np.empty(3 * n_tri, dtype=np.int64)
    cols = np.empty(3 * n_tri, dtype=np.int64)
    data = np.empty(3 * n_tri, dtype=np.float64)
    for t, (i, j, k) in enumerate(tris):
        i, j, k = int(i), int(j), int(k)
        rows[3 * t], cols[3 * t], data[3 * t] = idx[(j, k)], t, 1.0
        rows[3 * t + 1], cols[3 * t + 1], data[3 * t + 1] = idx[(i, k)], t, -1.0
        rows[3 * t + 2], cols[3 * t + 2], data[3 * t + 2] = idx[(i, j)], t, 1.0
    return sp.csr_matrix((data, (rows, cols)), shape=(n_edges, n_tri))


def _guard_size(n_edges: int) -> None:
    if n_edges > _MAX_DENSE_EDGES:
        raise ValueError(
            f"n_edges={n_edges} exceeds the dense-path guard ({_MAX_DENSE_EDGES}); "
            "the corpus has outgrown v1's deterministic dense SVD null-space/projector path "
            "(design note §2.5, Q3) — a sparse-eigensolver upgrade is the deliberate next act, "
            "never a silent fallback to a nondeterministic iterative solver."
        )


def hodge_laplacian_1(A: sp.csr_matrix) -> sp.csr_matrix:
    """L₁ = ∂₁ᵀ∂₁ + ∂₂∂₂ᵀ (down + up). PSD by construction. dim ker L₁ = β₁ (flag complex,
    design note §2.2). Sparse, deterministic — same house invariants as the degree-0 family."""
    d1 = boundary_1(A)
    d2 = boundary_2(A)
    down = (d1.T @ d1).tocsr()
    up = (d2 @ d2.T).tocsr()
    L1: sp.csr_matrix = (down + up).tocsr()
    return L1


@dataclass(frozen=True)
class HodgeParts:
    """The unique three-way Hodge split of a 1-cochain (design note §2.2): C₁ = im ∂₁ᵀ ⊕ im
    ∂₂ ⊕ ker L₁, mutually orthogonal under the standard (combinatorial, v1) inner product."""

    gradient: np.ndarray   # ∈ im ∂₁ᵀ  (induced by node potentials)
    curl: np.ndarray       # ∈ im ∂₂   (circulation around filled triangles)
    harmonic: np.ndarray   # ∈ ker L₁  (the threads)


def hodge_decompose(c: np.ndarray, A: sp.csr_matrix) -> HodgeParts:
    """c = gradient + curl + harmonic, the three mutually orthogonal (⟨·,·⟩ standard — v1 is
    combinatorial, design note §2.2). Exact reconstruction to numerical tolerance (§6(e): dense
    lstsq projectors, deterministic).

    gradient = ∂₁ᵀ x* where x* solves min ‖∂₁ᵀx − c‖ (least-squares node potential); curl = ∂₂ y*
    where y* solves min ‖∂₂y − (c − gradient)‖; harmonic = c − gradient − curl (the remainder,
    exactly ker L₁ by orthogonality of the first two terms)."""
    n_edges = len(edge_index(A))
    _guard_size(n_edges)
    d1 = boundary_1(A)
    d2 = boundary_2(A)
    d1t_dense = d1.T.toarray()
    d2_dense = d2.toarray()

    # gradient: project c onto im(∂₁ᵀ) via the least-squares node potential.
    x_star, *_ = np.linalg.lstsq(d1t_dense, c, rcond=_RANK_TOL)
    gradient = d1t_dense @ x_star

    # curl: project the remainder onto im(∂₂) via the least-squares triangle potential.
    remainder = c - gradient
    if d2_dense.shape[1] == 0:
        curl = np.zeros_like(c)
    else:
        y_star, *_ = np.linalg.lstsq(d2_dense, remainder, rcond=_RANK_TOL)
        curl = d2_dense @ y_star

    harmonic = c - gradient - curl
    return HodgeParts(gradient=gradient, curl=curl, harmonic=harmonic)


def harmonic_basis(A: sp.csr_matrix) -> np.ndarray:
    """(n_edges, β₁), orthonormal, DETERMINISTIC (§6(e): dense SVD null space, rank cut at
    singular values < 1e-10 * s_max — never an iterative eigensolver). β₁ = 0 ⇒ shape
    (n_edges, 0)."""
    n_edges = len(edge_index(A))
    _guard_size(n_edges)
    if n_edges == 0:
        return np.zeros((0, 0))
    L1 = hodge_laplacian_1(A).toarray()
    # ker(L1) via dense SVD: L1 is symmetric PSD, so its right singular vectors at singular
    # value ~0 span the null space exactly (deterministic — numpy's SVD has no random seed).
    u, s, _vt = np.linalg.svd(L1)
    s_max = s[0] if s.size else 0.0
    tol = _RANK_TOL * s_max
    keep = s <= tol
    basis: np.ndarray = u[:, keep]
    return basis


def l1_spectrum(A: sp.csr_matrix, k: int) -> tuple[np.ndarray, np.ndarray]:
    """The k smallest eigenpairs of L₁ — the degree-1 Fourier basis (low = smooth large-scale
    flow), the degree-1 counterpart of `spectral.py`'s eigenbasis. Consumed by later rungs (P5);
    provided, not yet wired (design note §2.2). Dense, deterministic (§6(e))."""
    n_edges = len(edge_index(A))
    _guard_size(n_edges)
    if n_edges == 0:
        return np.zeros(0), np.zeros((0, 0))
    L1 = hodge_laplacian_1(A).toarray()
    vals, vecs = np.linalg.eigh(L1)
    k = max(1, min(k, n_edges))
    return vals[:k], vecs[:, :k]
