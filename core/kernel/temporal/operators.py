"""The mode-3 temporal operators over `X_cite` — `π_active`, `σ_*`/`σ^*`, and the `T_active`
composite (dn-temporal-retrieval-algebra §2.2–§2.3; bp-033 Items 9–10, 12).

These are pure operators over the sparse citation complex `bp-032` assembles: `π_active` is the
ambient-default projection onto the not-yet-superseded subspace (`T = now`); `σ_*` is the
correspondence-transport chain map across a supersession boundary (the opt-in traversal, covariant
iff F1 — a revised note's citations carry forward); `σ^*` its pullback/adjoint (the Sz.-Nagy
dilation direction, always a contraction); `T_active = π_active ∘ σ_* ∘ ι` the canonical composite.

Linear-chain only (single-valued, injective σ): a fork/merge **diamond** is a stop-and-raise
(`DiamondError`, §10 / TA-c) — the homotopy-coherent `τ_k` rigor is data-gated on measured diamond
frequency, never silently averaged. Read-only sensing: no store handle, no model, no network (the
bp-032 isolation twin covers the whole package). Combinatorial v1 (unweighted — PD-b/TA-a parked).
"""

from __future__ import annotations

import numpy as np
import scipy.sparse as sp

from core.kernel.complex.hodge import boundary_1
from core.kernel.temporal.complex import CitationComplex


class DiamondError(ValueError):
    """The supersession correspondence σ is not single-valued/injective between the two snapshots (a
    fork/merge diamond) — the linear-chain operators do not apply (§10 / TA-c). Raised, never
    averaged into a single map."""


def sigma_node_map(cx_n: CitationComplex, cx_np1: CitationComplex,
                   sigma: dict[str, str]) -> dict[int, int]:
    """Resolve the node correspondence σ (by note id) to an X_n→X_{n+1} index map. σ must be total
    on X_n's nodes (every active note has a successor in the linear chain) and INJECTIVE — a merge
    (two X_n notes onto one X_{n+1} note) is a diamond (`DiamondError`)."""
    index_map: dict[int, int] = {}
    hit: dict[int, int] = {}
    for name, i in cx_n.node_index.items():
        if name not in sigma:
            raise ValueError(f"σ is not total on X_n: no image for node {name!r}")
        target = sigma[name]
        if target not in cx_np1.node_index:
            raise ValueError(f"σ maps {name!r} → {target!r}, absent from X_(n+1)")
        j = cx_np1.node_index[target]
        if j in hit:
            raise DiamondError(
                f"σ merges nodes {cx_n.nodes[hit[j]]!r} and {name!r} onto {target!r} — a diamond "
                "(§10 / TA-c); the linear-chain operators do not apply."
            )
        hit[j] = i
        index_map[i] = j
    return index_map


def active_projection(cx: CitationComplex, superseded: set[str]) -> np.ndarray:
    """`π_active` on 0-cochains: the diagonal orthogonal projection onto the not-yet-superseded node
    subspace (`T = now`). Idempotent (`Π² = Π`) and a contraction (`‖Π‖ ≤ 1`) by construction, and
    deliberately NOT a chain map — it destroys superseded content rather than transporting it."""
    diag = np.array([0.0 if name in superseded else 1.0 for name in cx.nodes], dtype=np.float64)
    return np.diag(diag)


def pushforward_0(cx_n: CitationComplex, cx_np1: CitationComplex,
                  index_map: dict[int, int]) -> sp.csr_matrix:
    """`σ_*` on 0-chains: `e_v ↦ e_{σv}`. Shape `(n_np1_nodes, n_n_nodes)`."""
    n_n, n_np1 = cx_n.n_nodes, cx_np1.n_nodes
    if n_n == 0:
        return sp.csr_matrix((n_np1, 0))
    rows = np.array([index_map[i] for i in range(n_n)], dtype=np.int64)
    cols = np.arange(n_n, dtype=np.int64)
    data = np.ones(n_n, dtype=np.float64)
    return sp.csr_matrix((data, (rows, cols)), shape=(n_np1, n_n))


def pushforward_1(cx_n: CitationComplex, cx_np1: CitationComplex,
                  index_map: dict[int, int]) -> sp.csr_matrix:
    """`σ_*` on 1-chains: an X_n edge `{u,v}` maps to `{σu,σv}` (with orientation sign) IF that is
    an edge of X_{n+1}, else to 0 — a **severed** citation (F1 failure). Shape `(n_np1_edges,
    n_n_edges)`. The severing is exactly what makes `σ_*` a chain map only when F1 holds."""
    np1_edge_index = {e: k for k, e in enumerate(cx_np1.edges)}
    n_n_edges, n_np1_edges = cx_n.n_edges, cx_np1.n_edges
    rows: list[int] = []
    cols: list[int] = []
    data: list[float] = []
    for e, (u, v) in enumerate(cx_n.edges):
        a, b = index_map[u], index_map[v]           # injective ⇒ a != b
        key = (a, b) if a < b else (b, a)
        target = np1_edge_index.get(key)
        if target is None:
            continue                                # severed — column stays zero
        rows.append(target)
        cols.append(e)
        data.append(1.0 if a < b else -1.0)         # +1 orientation-preserving, −1 reversed
    if not rows:
        return sp.csr_matrix((n_np1_edges, n_n_edges))
    return sp.csr_matrix((np.array(data), (np.array(rows), np.array(cols))),
                         shape=(n_np1_edges, n_n_edges))


def is_chain_map(cx_n: CitationComplex, cx_np1: CitationComplex,
                 index_map: dict[int, int]) -> bool:
    """The chain-map law `∂_{n+1} σ_*^1 == σ_*^0 ∂_n` (Result 2 — holds iff F1: every citation
    carries forward). A severed citation breaks it — the honest negative the falsifier wants."""
    q0 = pushforward_0(cx_n, cx_np1, index_map)
    q1 = pushforward_1(cx_n, cx_np1, index_map)
    lhs = (boundary_1(cx_np1.A_cite) @ q1).tocsr()
    rhs = (q0 @ boundary_1(cx_n.A_cite)).tocsr()
    diff = (lhs - rhs).tocsr()
    return diff.nnz == 0 or bool(np.allclose(diff.toarray(), 0.0))


def pullback_0(cx_n: CitationComplex, cx_np1: CitationComplex,
               index_map: dict[int, int]) -> sp.csr_matrix:
    """`σ^*` on 0-cochains: `(σ^*φ)(v) = φ(σv)` — the adjoint of `σ_*`, the pinned Sz.-Nagy dilation
    direction. Shape `(n_n_nodes, n_np1_nodes)`; for an injective σ a contraction (`‖σ^*‖ ≤ 1`,
    each row a single unit entry)."""
    m: sp.csr_matrix = pushforward_0(cx_n, cx_np1, index_map).transpose().tocsr()
    return m


def t_active(cx_n: CitationComplex, cx_np1: CitationComplex, index_map: dict[int, int],
             superseded_np1: set[str]) -> np.ndarray:
    """`T_active = π_active ∘ σ_* ∘ ι` on 0-cochains (embed active → transport → compress to the
    active view) — the canonical composite, Result 5. A contraction (`‖T_active‖ ≤ 1`) for an
    injective σ. Returned dense (small; the caller checks the operator norm)."""
    q0 = pushforward_0(cx_n, cx_np1, index_map).toarray()
    projection = active_projection(cx_np1, superseded_np1)
    composite: np.ndarray = projection @ q0
    return composite
