# ── Family: the temporal / citation complex (X_cite) — OUTSIDE core/complex/ (A4, isolation) ──
# OBJECT:    the deterministic, embedder-independent citation complex — 0-cells notes, 1-cells the
#            corpus→corpus citation edges (reference_edges.sqlite), assembled at one commit.
# INVARIANT: read-only (no store write handle); no model, no network; the citation backbone A_cite
#            (E_geom, undirected) is NEVER mixed with the directed supersession D-arrows (E_disp) —
#            a single L₁ over the union is a type error (A5). This module reuses core/complex/hodge
#            (the safe import direction) but NOTHING here ever reaches build_complex / A_signed.
"""The citation complex X_cite — the topological half of dn-temporal-retrieval-algebra §3 (bp-032).

`X_cite` is the flag complex of the doc→doc citation graph read from `ReferenceEdgeStore`
(`direction="corpus_to_corpus"`, bp-026): 0-cells are notes, 1-cells are citation edges, and the
symmetrized binary backbone `A_cite` feeds the degree-1 Hodge machinery UNCHANGED from
`core/complex/hodge` (the note §2.4: "shared mathematics, never shared state"). It is
**embedder-independent by construction** — a deterministic parse of stored references, no embedding
read — which is the hinge of the A7 signal/noise discriminator.

The combinatorial v1 (unweighted) object: `A_cite` is binary (edge or no edge), matching `hodge`'s
v1 inner product; the `(β,z)` weighted retrieval curve is TA-a/bp-034+, out of scope. The directed
supersession D-arrows live in `boundary.py` and are NEVER symmetrized into `A_cite` (A5 — `E_disp`
is acyclic/directed, `E_geom` undirected; a mixed `L₁` conflates incompatible metrics).

Zone A: takes the assembled `CitationComplex` (built by the outer acquisition seam from
`reference_edges`), holds no write handle, imports `core/complex/hodge` (the safe direction —
`core/complex/**` never imports THIS module; pinned by test_temporal_isolation.py). **Inner (bp-089,
S1′):** the store-reading builder `build_citation_complex` relocated to `core/temporal/acquire.py`
(inner-ring promotion) — this module now COMPUTES over an assembled complex, it does not acquire it;
it holds no `ReferenceEdgeStore` import.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import scipy.sparse as sp

from core.kernel.complex.hodge import boundary_1, boundary_2, edge_index, harmonic_basis


@dataclass(frozen=True)
class CitationComplex:
    """The assembled citation complex at one commit — a pure function of the store contents.

    `nodes` is the deterministic 0-cell ordering (sorted note ids); `node_index` maps a note id to
    its row in `A_cite`; `edges` are the 1-cells as `(u, v)` index pairs with `u < v`, sorted;
    `A_cite` is the binary symmetric backbone (csr, zero diagonal) fed to the Hodge machinery."""

    nodes: tuple[str, ...]
    node_index: dict[str, int]
    edges: tuple[tuple[int, int], ...]
    A_cite: sp.csr_matrix

    @property
    def n_nodes(self) -> int:
        return len(self.nodes)

    @property
    def n_edges(self) -> int:
        return len(self.edges)


def dim_ker_L1(cx: CitationComplex) -> int:
    """β₁ of the citation flag complex — the number of independent citation "threads" (1-cycles not
    bounding a filled 2-simplex), computed as `dim ker L₁` via `hodge.harmonic_basis` (dense SVD
    null space, deterministic; inherits `hodge`'s `_MAX_DENSE_EDGES` guard). The Item-7 falsifier
    cross-checks this against an INDEPENDENT ripser β₁ (`citation_distance_matrix` + ripser)."""
    if cx.n_edges == 0:
        return 0
    return int(harmonic_basis(cx.A_cite).shape[1])


def citation_distance_matrix(cx: CitationComplex) -> np.ndarray:
    """The ripser input for the independent β₁ oracle: a dense distance matrix with `distance = 0`
    on a citation edge, `1` on a non-edge, `0` on the diagonal. Rips at threshold `t = 0` IS the
    flag complex of the (binary) citation graph, so ripser's H₁ alive at `t = 0` equals
    `dim ker L₁` (note §2.4/§2.7 Rule 2). Deterministic, symmetric."""
    n = cx.n_nodes
    D = np.ones((n, n), dtype=np.float64)
    np.fill_diagonal(D, 0.0)
    for u, v in cx.edges:
        D[u, v] = 0.0
        D[v, u] = 0.0
    return D


def flag_boundary_composition_is_zero(cx: CitationComplex) -> bool:
    """`∂₁∂₂ = 0` on `A_cite` — the fundamental chain-complex identity, reused from `hodge` (any
    sign error in the citation backbone's incidence would break it). Confirmed as an Item-6
    acceptance leg alongside the `δ_D² = 0` supersession check in `boundary.py`."""
    d1 = boundary_1(cx.A_cite)
    d2 = boundary_2(cx.A_cite)
    if d2.shape[1] == 0:
        return True                                    # no 2-cells ⇒ trivially zero
    comp = (d1 @ d2).tocoo()
    # edge_index is consumed to keep the reuse honest (same C₁ basis both boundaries key on).
    _ = edge_index(cx.A_cite)
    return bool(np.allclose(comp.data, 0.0))
