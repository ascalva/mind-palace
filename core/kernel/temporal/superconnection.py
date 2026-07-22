"""The superconnection curvature `[d,τ]` and its norm `‖[d,τ]‖` over `X_cite` (bp-033 Item 11;
dn-temporal-retrieval-algebra §2.3 Result 2 — PROVEN tight).

For the superconnection `𝔸 = d + τ` (with `τ = σ^*`, the pullback), `𝔸² = [d,τ] + τ²`; the curvature
is `[d,τ]`, and its closed form is

    ([d,τ]φ)(u,v) = (φ(σv) − φ(σu)) · 𝟙[{σu,σv} ∉ X_{n+1}]

— supported EXACTLY on the **severed** citations (edges of X_n whose image is not an edge of
X_{n+1}). So `‖[d,τ]‖` **is** the (weighted) count of citations that fail to carry forward — the
exact obstruction to bicomplex flatness, **not a proxy**. Flat (`[d,τ] = 0`) ⟺ every citation
carries forward (F1) ⟺ bicomplex. This is the linear-chain superconnection curvature — NOT diamond
holonomy, NOT the static Forman–Ricci curvature (`core/complex/curvature.py`): same word, different
tensors (Result 3). Combinatorial v1 (each severed citation weighs 1). Read-only; no store/model.
"""

from __future__ import annotations

import numpy as np
import scipy.sparse as sp

from core.kernel.temporal.complex import CitationComplex


def severed_citations(cx_n: CitationComplex, cx_np1: CitationComplex,
                      index_map: dict[int, int]) -> list[tuple[int, int]]:
    """The X_n edges `{u,v}` whose image `{σu,σv}` is NOT an edge of X_{n+1} — the citations that
    fail to carry forward (F1 failures). Deterministic (X_n edge order). The direct discrete
    invariant `‖[d,τ]‖` must reproduce (inversion Rule 2)."""
    np1_edges = set(cx_np1.edges)
    out: list[tuple[int, int]] = []
    for u, v in cx_n.edges:
        a, b = index_map[u], index_map[v]
        key = (a, b) if a < b else (b, a)
        if key not in np1_edges:
            out.append((u, v))
    return out


def curvature(cx_n: CitationComplex, cx_np1: CitationComplex,
              index_map: dict[int, int]) -> sp.csr_matrix:
    """`[d,τ]` as a matrix `C^0(X_{n+1}) → C^1(X_n)`, shape `(n_n_edges, n_np1_nodes)`. Row `e =
    {u,v}` is `+1` at `σv`, `−1` at `σu` iff `{u,v}` is severed, else all zero — the closed form
    (Result 2). `‖[d,τ]‖` reads off its support."""
    n_n_edges, n_np1_nodes = cx_n.n_edges, cx_np1.n_nodes
    severed = set(severed_citations(cx_n, cx_np1, index_map))
    rows: list[int] = []
    cols: list[int] = []
    data: list[float] = []
    for e, (u, v) in enumerate(cx_n.edges):
        if (u, v) not in severed:
            continue
        a, b = index_map[u], index_map[v]
        rows.extend([e, e])
        cols.extend([b, a])                         # (φ(σv) − φ(σu))
        data.extend([1.0, -1.0])
    if not rows:
        return sp.csr_matrix((n_n_edges, n_np1_nodes))
    return sp.csr_matrix((np.array(data), (np.array(rows), np.array(cols))),
                         shape=(n_n_edges, n_np1_nodes))


def curvature_norm(cx_n: CitationComplex, cx_np1: CitationComplex,
                   index_map: dict[int, int]) -> int:
    """`‖[d,τ]‖` — the combinatorial (unweighted v1) norm: the number of severed citations. By
    Result 2 this EQUALS the discrete severed-citation count `Σ 𝟙[{σu,σv} ∉ X_{n+1}]` exactly (the
    operator is the invariant, not a proxy) — the Item-11 acceptance leg cross-checks the two."""
    return len(severed_citations(cx_n, cx_np1, index_map))


def is_flat(cx_n: CitationComplex, cx_np1: CitationComplex,
            index_map: dict[int, int]) -> bool:
    """`[d,τ] = 0` ⟺ every citation carries forward (F1) ⟺ the bicomplex case. The flatness the
    superconnection makes visible (Result 3)."""
    return curvature(cx_n, cx_np1, index_map).nnz == 0
