"""Forman–Ricci curvature — the cheap deterministic floor (companion III §3.2; H4).

Curvature is the intrinsic, embedding-free way to find where the interesting structure is: an
edge inside a triangle-dense community is positively curved; an edge with high endpoint degree and
little triangle support is a **bridge** spanning a structural hole — negatively curved. Bridges are
where cross-domain insight lives, so the Dreamer ranks edges ascending by curvature and looks at
the most negative first.

Augmented unweighted Forman form (variants exist; this is the doc's declared one):

    Ric_F(u, v) = 4 − deg(u) − deg(v) + 3·|△(u, v)|

computed on the *support* of the σ-graph (edges present at the working threshold — the same graph
the other lenses see; a weighted Forman variant is a later refinement, not silently substituted).
O(#triangles) total, exact, deterministic. Ollivier–Ricci (the principled OT form, §3.1) is an
optional enrichment gated on cost and is deliberately NOT implemented here — Forman is the floor.
"""

from __future__ import annotations

import numpy as np
import scipy.sparse as sp


def forman(A: sp.csr_matrix) -> dict[tuple[int, int], float]:
    """Augmented Forman–Ricci curvature per edge of A's support, keyed (i, j) with i < j.

    Negative on bridges (high endpoint degree, low triangle support); positive inside
    triangle-dense communities. Exact and deterministic — pure degree/triangle combinatorics."""
    B = (A != 0).astype(np.int64)  # type: ignore[attr-defined]  # warrant: sparse __ne__ returns a matrix at runtime; stubs over-narrow to bool (T3)
    B = B.tocsr()
    B.setdiag(0)
    B.eliminate_zeros()
    deg = np.asarray(B.sum(axis=1)).ravel()
    # triangles through each edge = (B @ B)[i, j] counts common neighbours of i and j
    common = (B @ B).tocsr()
    out: dict[tuple[int, int], float] = {}
    coo = B.tocoo()
    for i, j in zip(coo.row, coo.col, strict=True):
        if i < j:
            tri = int(common[i, j])
            out[(int(i), int(j))] = float(4 - deg[i] - deg[j] + 3 * tri)
    return out


def most_negative_edges(A: sp.csr_matrix, *, top_k: int) -> list[tuple[int, int, float]]:
    """The candidate cross-domain bridges: edges ranked ascending by Forman curvature.

    Emission rule (deterministic, no magic threshold): candidates are the edges with κ ≤ 0 —
    genuinely bridge-like — or, when every edge is positive (tiny/dense graphs), only the edges
    achieving the graph's minimum κ (the *relatively* most bridge-like; never the whole graph).
    At most `top_k`, tie-broken by (κ, i, j) so the ranking is reproducible."""
    curv = forman(A)
    if not curv:
        return []
    lo = min(curv.values())
    candidates = [(i, j, k) for (i, j), k in curv.items() if k <= 0.0] or \
                 [(i, j, k) for (i, j), k in curv.items() if k == lo]
    candidates.sort(key=lambda e: (e[2], e[0], e[1]))
    return candidates[: max(0, top_k)]
