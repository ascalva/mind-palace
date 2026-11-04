"""The sort algebra on arrays — the operations the laws are stated over, in the code's arithmetic
(float64), each named for the Lean definition it transcribes (`formal/Palace/Sentence/Defs.lean`).

These are the code anchors for the sentence algebra's laws: the planner's rewrites and the
executor's connectives are built from them, and `tests/property/test_sentence_laws.py` checks each
law here against the same statement `formal/Palace/Sentence.lean` proves over exact arithmetic.
"""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np


def indicator(members: Iterable[int], n: int) -> np.ndarray:
    """`ind S`: the region's indicator over `n` notes."""
    v = np.zeros(n)
    for i in members:
        v[i] = 1.0
    return v


def mask_field(f: np.ndarray, members: Iterable[int]) -> np.ndarray:
    """`maskF S f`: the field, zero outside the region (QSA-2 on a column)."""
    return np.asarray(f * indicator(members, f.shape[0]), dtype=float)


def mask(K: np.ndarray, members: Iterable[int]) -> np.ndarray:
    """`mask S K`: the kernel, zero outside `S × S` — the congruence `P K P` by the projection onto
    the region (QSA-2, `mask_eq_diagonal_mul_mul`)."""
    p = indicator(members, K.shape[0])
    return K * np.outer(p, p)


def field_at(K: np.ndarray, anchor: int) -> np.ndarray:
    """`fieldAt K a`: the kernel's column at the anchor, `K e_a` (QSA-3)."""
    return np.asarray(K[:, anchor], dtype=float).copy()


def topk(f: np.ndarray, k: int) -> frozenset[int]:
    """`topk k f`: every note that fewer than `k` notes beat strictly, so ties are kept (QSA-4:
    it does not commute with `within`)."""
    out: set[int] = set()
    for i in range(f.shape[0]):
        if int(np.sum(f > f[i])) < k:
            out.add(i)
    return frozenset(out)


def atleast(f: np.ndarray, t: float) -> frozenset[int]:
    """`thresh t f`: every note scoring at least `t` (QSA-4: commutes with `within` for `t > 0`)."""
    return frozenset(int(i) for i in np.flatnonzero(f >= t))


def far(f: np.ndarray) -> np.ndarray:
    """`far f = 1 − f`: the bounded reversal, a field operation (the cone has no complement)."""
    return 1.0 - f


def assume_edge(A: np.ndarray, u: int, v: int, delta: float) -> np.ndarray:
    """`assumeEdge A u v δ`: the weights with `δ` added on the undirected edge `{u, v}` (QSA-9)."""
    B = A.copy()
    B[u, v] += delta
    if u != v:
        B[v, u] += delta
    return B


def dvec(n: int, u: int, v: int, sigma: float = 1.0) -> np.ndarray:
    """`dvec u v σ = e_u − σ e_v`: the direction of the rank-one update (QSA-9)."""
    d = np.zeros(n)
    d[u] += 1.0
    d[v] -= sigma
    return d


def laplacian(A: np.ndarray) -> np.ndarray:
    """`L = D − A`, the combinatorial Laplacian (LAP rows)."""
    return np.asarray(np.diag(A.sum(axis=1)) - A, dtype=float)


def signed_laplacian(A: np.ndarray) -> np.ndarray:
    """`L̄ = D̄ − A`, `D̄ᵢᵢ = Σⱼ |Aᵢⱼ|` (the signed Laplacian of LAP-5)."""
    return np.asarray(np.diag(np.abs(A).sum(axis=1)) - A, dtype=float)


def effective_resistance(A: np.ndarray, i: int, j: int) -> float:
    """`R_eff = L⁺ᵢᵢ + L⁺ⱼⱼ − 2L⁺ᵢⱼ` through the pseudo-inverse (CND-1), on one component."""
    P = np.linalg.pinv(laplacian(A), hermitian=True)
    return float(P[i, i] + P[j, j] - 2 * P[i, j])


def camps(A: np.ndarray) -> np.ndarray | None:
    """The camps `s ∈ {±1}ⁿ` with `Aᵢⱼ sᵢ sⱼ ≥ 0` everywhere, found by two-colouring each
    component along the signs; `None` when the signed graph is frustrated (LAP-5, LAP-6). The
    `Balanced` witness of `formal/Palace/Balance/Defs.lean`."""
    n = A.shape[0]
    s = np.zeros(n)
    for root in range(n):
        if s[root] != 0:
            continue
        s[root] = 1.0
        stack = [root]
        while stack:
            u = stack.pop()
            for v in np.flatnonzero(A[u]):
                want = s[u] * (1.0 if A[u, v] > 0 else -1.0)
                if s[v] == 0:
                    s[v] = want
                    stack.append(int(v))
                elif s[v] != want:
                    return None
    return s


def sherman_morrison(M_inv: np.ndarray, u: np.ndarray, v: np.ndarray, c: float) -> np.ndarray:
    """`(M + c u vᵀ)⁻¹ = M⁻¹ − c/(1 + c vᵀM⁻¹u) · (M⁻¹u)(vᵀM⁻¹)` (QSA-9, `inv_add_vecMulVec`)."""
    Mu = M_inv @ u
    vM = v @ M_inv
    denom = 1.0 + c * float(v @ Mu)
    if denom == 0.0:
        raise ZeroDivisionError("the rank-one update is singular: 1 + c vᵀM⁻¹u = 0")
    return M_inv - (c / denom) * np.outer(Mu, vM)
