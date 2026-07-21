# ── Family: the temporal acquisition seam — the OUTER ring of core/temporal/ (bp-089, S1′) ──
# OBJECT:    the store-reading wrappers that feed the inner, pure temporal builders — read the
#            version chains / citation edges from the sqlite stores, then call the store-free
#            `poset_from_chains` (boundary.py) and `build_citation_complex`'s pure assembly.
# INVARIANT: this module ACQUIRES (holds the store types); `boundary`/`complex` now only COMPUTE.
#            The math is unchanged — this is a relocation of *where the data is read*, never *what
#            is computed* (bp-089 P4 no-silent-change). Reads only: no write handle, no model, no
#            network. Imports the inner pure modules (the safe direction — they never import THIS).
"""The temporal acquisition seam — `supersession_poset` and `build_citation_complex` (bp-089, S1′).

The inner-ring promotion (dn-inner-outer-core §2.6b) moves the two store-reading wrappers OFF
`core/temporal/{boundary,complex}.py` — so those modules become inner (they take data, they do not
acquire it) — and lands them here, one ring outward (still core, still Zone A). Byte-identical
behavior: `supersession_poset` reads the same `VersionStore.history` chains and delegates to the
unchanged pure `poset_from_chains`; `build_citation_complex` reads the same `ReferenceEdgeStore`
rows and assembles the same `CitationComplex`. No new mathematics; a clean-break relocation
(bp-065): the old homes keep no alias shim.
"""

from __future__ import annotations

import numpy as np
import scipy.sparse as sp

from core.stores.reference_edges import ReferenceEdgeStore
from core.stores.versions import VersionStore
from core.temporal.boundary import SupersessionPoset, poset_from_chains
from core.temporal.complex import CitationComplex


def supersession_poset(
    version_store: VersionStore, doc_ids: list[str]
) -> SupersessionPoset:
    """Read the version chains for `doc_ids` from a live `VersionStore` and build the poset. Uses
    the rename-stable `doc_id` (bp-031) as the chain identity — so a rename no longer forks a chain
    into two orphan lineages (which would show up here as a well-foundedness defect).

    The store-reading seam (bp-089, S1′ inner-ring promotion): it acquires the chains, then
    delegates to the pure store-free `core.temporal.boundary.poset_from_chains` — math unchanged."""
    chains = {doc_id: [v.version_seq for v in version_store.history(doc_id)] for doc_id in doc_ids}
    return poset_from_chains(chains)


def build_citation_complex(ref_store: ReferenceEdgeStore, *,
                           commit: str | None = None) -> CitationComplex:
    """Assemble `X_cite` from the doc→doc citation edges — deterministic, run-to-run byte-identical
    on the same store (node/edge ordering is sorted, never dict-iteration-dependent).

    0-cells = the sorted set of note ids appearing as either endpoint of a `corpus_to_corpus` edge;
    1-cells = the undirected, de-duplicated citation pairs (a self-citation `u==u` is dropped — no
    1-cell). `A_cite` is binary (combinatorial v1). Reads only; no store mutation.

    `commit` is the OPTIONAL anchor (dn-core-query-protocol §3 Q2; bp-037/`TemporalView`): edges are
    per-commit (`commit_sha` is part of edge identity — `reference_edges.py`), so `commit=None`
    (default) assembles over the ALL-HISTORY union of citation edges — the original behaviour, kept
    bit-for-bit — while `commit=<sha>` filters to that anchor, giving β₁ "as of" one commit rather
    than a union that can count threads across citations that never co-existed. A pure-Python filter
    over already-read rows: no new import, no store-API change, isolation untouched (§2.4).

    The store-reading seam (bp-089, S1′ inner-ring promotion): it acquires the citation rows, then
    assembles the same `core.temporal.complex.CitationComplex` — the math is unchanged."""
    citations = ref_store.all(direction="corpus_to_corpus")
    if commit is not None:
        citations = [e for e in citations if e.commit_sha == commit]

    node_set: set[str] = set()
    for e in citations:
        node_set.add(e.source_ref)
        node_set.add(e.target_ref)
    nodes = tuple(sorted(node_set))
    node_index = {name: i for i, name in enumerate(nodes)}

    edge_set: set[tuple[int, int]] = set()
    for e in citations:
        u, v = node_index[e.source_ref], node_index[e.target_ref]
        if u == v:
            continue                                   # a self-citation is not a 1-cell
        edge_set.add((u, v) if u < v else (v, u))      # undirected backbone (A5: E_geom)
    edges = tuple(sorted(edge_set))

    n = len(nodes)
    if edges:
        rows = np.array([u for u, _ in edges] + [v for _, v in edges], dtype=np.int64)
        cols = np.array([v for _, v in edges] + [u for u, _ in edges], dtype=np.int64)
        data = np.ones(2 * len(edges), dtype=np.float64)
        A_cite = sp.csr_matrix((data, (rows, cols)), shape=(n, n))
    else:
        A_cite = sp.csr_matrix((n, n))

    return CitationComplex(nodes=nodes, node_index=node_index, edges=edges, A_cite=A_cite)
