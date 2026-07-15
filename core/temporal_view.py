# ── Family 1 boundary (labelings & information-flow) · symbols in docs/NOTATION.md ──
# OBJECT:    The §2.7 corpus-structural read surface — a deterministic, commit-anchored read
#            window over the citation complex X_cite (`core/temporal/complex.py`). The read-side
#            sibling of `ReferenceView` (bp-035): where ReferenceView answers "who cites this?"
#            over the raw reference edges, TemporalView answers "how many independent citation
#            threads (β₁) does the corpus carry, as of one commit?" over the flag complex.
# INVARIANT: read-only + in-core. The view holds an ALREADY-ASSEMBLED `CitationComplex` (built
#            eagerly at `.over()`), never a live store handle — so no mutator and no connection is
#            reachable through it (Inv 4 flavor: reports data, takes no action). An in-core reader
#            is not a plane crossing (dn-core-query-protocol §2.4 item 5). No model, no network,
#            and — by construction of `core/temporal` — no path into the balance math (§2.4 A4).
# ENFORCED:  static (the frozen dataclass exposes read methods + a bound `CitationComplex`, no
#            store) + guard (test_temporal_view.py asserts no store/`add_batch`/`_conn` reachable).
"""`TemporalView` — the deterministic "how many citation threads?" read window (bp-037 / CQ-wire).

`core/temporal/complex.py` (`build_citation_complex`, `dim_ker_L1`) is built and graded, but its
only importers were tests (finding-0059/0061's staleness class, one level up: the *algebra* was
built and agent-unreachable). This module is the first live consumer — a typed read window in the
mould of `ReferenceView` (`core/reference_view.py`): assemble the anchored `X_cite`, expose β₁ and a
structural self-check, and only those.

**Commit-anchored (the §3 Q2 decision).** Citation edges are per-commit (`commit_sha` is part of
edge identity), so β₁ over the all-history union can count threads across citations that never
co-existed. `TemporalView.over(store, *, commit=…)` builds `X_cite` from ONLY that anchor's edges,
and `open_temporal_view` resolves the default anchor **identically to `ReferenceView`** (the active
run's `commit_sha`, else git HEAD) — so the two Views agree on what "now" means.

**Single-snapshot (bp-037 scope).** This wires the single-snapshot half of `core/temporal` (β₁
threads, `∂₁∂₂=0`). The two-snapshot `‖[d,τ]‖` citation-coherence (`σ_*`, severed citations) is
`CQ-wire-2`, a follow-on that extends this surface.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
import scipy.sparse as sp

from core.temporal.complex import (
    CitationComplex,
    build_citation_complex,
    dim_ker_L1,
    flag_boundary_composition_is_zero,
)
from core.temporal.operators import sigma_node_map
from core.temporal.superconnection import curvature_norm, is_flat, severed_citations

if TYPE_CHECKING:  # annotations only — the factory imports the config/store lazily at runtime
    from config.loader import Config
    from core.stores.reference_edges import ReferenceEdgeStore
    from core.stores.versions import VersionStore


@dataclass(frozen=True)
class CoherenceReport:
    """Two-snapshot citation-coherence between an earlier view (n) and a later view (n+1), over the
    notes present at BOTH commits (§3 Q1 restrict-to-common). `coherence_norm` is `‖[d,τ]‖` — the
    count of common-note citations that failed to carry forward; node add/drop is a SEPARATE axis
    (`nodes_added`/`nodes_dropped`), never folded into the coherence obstruction."""

    commit_from: str
    commit_to: str
    common_nodes: int                      # |X_n.nodes ∩ X_{n+1}.nodes| — the measured domain
    coherence_norm: int                    # ‖[d,τ]‖ = # common-node citations that failed to carry
    severed: tuple[tuple[str, str], ...]   # the severed citation pairs (by note id, lex-sorted)
    is_flat: bool                          # ‖[d,τ]‖ == 0 ⟺ every common-node citation carried fwd
    nodes_added: int                       # |X_{n+1}.nodes \ X_n.nodes| — the node-delta axis
    nodes_dropped: int                     # |X_n.nodes \ X_{n+1}.nodes|


def _restrict(cx: CitationComplex, keep: set[str]) -> CitationComplex:
    """A sub-complex over `keep ⊆ cx.nodes`: re-index the kept nodes (sorted) and keep only edges
    with BOTH endpoints kept, rebuilding the binary `A_cite` — mirrors `build_citation_complex`'s
    assembly, no store. Deterministic. Makes σ total on the common set (§3 Q1)."""
    nodes = tuple(sorted(n for n in cx.nodes if n in keep))
    node_index = {name: i for i, name in enumerate(nodes)}
    edge_set: set[tuple[int, int]] = set()
    for u, v in cx.edges:
        nu, nv = cx.nodes[u], cx.nodes[v]
        if nu in node_index and nv in node_index:
            a, b = node_index[nu], node_index[nv]
            edge_set.add((a, b) if a < b else (b, a))
    edges = tuple(sorted(edge_set))
    n = len(nodes)
    if edges:
        rows = np.array([u for u, _ in edges] + [v for _, v in edges], dtype=np.int64)
        cols = np.array([v for _, v in edges] + [u for u, _ in edges], dtype=np.int64)
        data = np.ones(2 * len(edges), dtype=np.float64)
        a_cite: sp.csr_matrix = sp.csr_matrix((data, (rows, cols)), shape=(n, n))
    else:
        a_cite = sp.csr_matrix((n, n))
    return CitationComplex(nodes=nodes, node_index=node_index, edges=edges, A_cite=a_cite)


@dataclass(frozen=True)
class TemporalView:
    """A deterministic, commit-anchored read window over the citation complex `X_cite`.

    Construct with `TemporalView.over(store, commit=…)`; the view holds the assembled
    `CitationComplex` (built once, eagerly) and the anchor commit — the store's mutators are
    unreachable because no store handle is retained (§2.1 scope: the type names reads, never a
    mutator). Read-only + in-core (Inv 4/Inv 2)."""

    _complex: CitationComplex   # the anchored X_cite, built eagerly at .over(), frozen here
    commit: str                 # the anchor commit these reads are scoped to (as ReferenceView)

    @classmethod
    def over(cls, store: ReferenceEdgeStore, *, commit: str) -> TemporalView:
        """Assemble the commit-anchored `X_cite` from the store's citation edges and freeze it into
        a view. The store is READ here (eagerly, once) and NOT retained — the view exposes the reads
        below and only those; the store's `add_batch`/`_conn` are unreachable through it."""
        return cls(_complex=build_citation_complex(store, commit=commit), commit=commit)

    # --- reads -----------------------------------------------------------------------------------
    def citation_threads(self) -> int:
        """β₁ = `dim ker L₁` — the number of independent citation "threads" (1-cycles in the flag
        complex not bounding a filled 2-simplex) at the anchor. Combinatorial v1 (unweighted
        `A_cite`). Deterministic; cross-checked vs an independent ripser β₁ in the live test."""
        return dim_ker_L1(self._complex)

    def boundary_composition_is_zero(self) -> bool:
        """`∂₁∂₂ = 0` on the citation backbone — the chain-complex identity; a self-check that the
        assembled incidence is sign-consistent (a backbone sign error would break it)."""
        return flag_boundary_composition_is_zero(self._complex)

    @property
    def n_nodes(self) -> int:
        """The number of 0-cells: distinct notes that are a citation endpoint at the anchor."""
        return self._complex.n_nodes

    @property
    def n_edges(self) -> int:
        """The number of 1-cells: distinct undirected citation pairs at the anchor commit."""
        return self._complex.n_edges

    def coherence_to(self, other: TemporalView) -> CoherenceReport:
        """Two-snapshot `‖[d,τ]‖` citation-coherence from THIS view (earlier, X_n) to `other`
        (later, X_{n+1}). σ = identity on the common node set (§3 Q1 restrict-to-common): `X_n` is
        restricted to the notes present at BOTH commits, σ maps each to itself (total + injective),
        and severed citations are the restricted X_n edges whose image is not an X_{n+1} edge. Reads
        only the two views' assembled complexes (same-class private access) — no store handle."""
        cx_n, cx_np1 = self._complex, other._complex
        nodes_n, nodes_np1 = set(cx_n.nodes), set(cx_np1.nodes)
        common = nodes_n & nodes_np1

        restricted_n = _restrict(cx_n, common)
        sigma = {name: name for name in restricted_n.nodes}          # identity on the common domain
        index_map = sigma_node_map(restricted_n, cx_np1, sigma)

        severed_idx = severed_citations(restricted_n, cx_np1, index_map)
        severed = tuple(sorted(
            (restricted_n.nodes[u], restricted_n.nodes[v]) for u, v in severed_idx
        ))
        return CoherenceReport(
            commit_from=self.commit,
            commit_to=other.commit,
            common_nodes=len(common),
            coherence_norm=curvature_norm(restricted_n, cx_np1, index_map),
            severed=severed,
            is_flat=is_flat(restricted_n, cx_np1, index_map),
            nodes_added=len(nodes_np1 - nodes_n),
            nodes_dropped=len(nodes_n - nodes_np1),
        )


def open_temporal_view(config: Config | None = None, *,
                       commit: str | None = None) -> TemporalView:
    """Factory: open the live reference store read-only and build a `TemporalView` anchored at
    `commit` — defaulting (§3 Q1/Q2) to the active run's `commit_sha` (`RunLedger.last()`), else git
    HEAD. The default is resolved via `core.reference_view._resolve_default_commit` so this View and
    `ReferenceView` anchor identically (both answer "now" the same way); reference_view.py is the
    authoritative resolver, out of this plan's scope to make public."""
    from config.loader import get_config
    from core.reference_view import _resolve_default_commit
    from core.stores.reference_edges import open_reference_edge_store

    cfg = config or get_config()
    anchor = commit if commit is not None else _resolve_default_commit(cfg)
    store = open_reference_edge_store(cfg)
    return TemporalView.over(store, commit=anchor)


def open_coherence(config: Config | None = None, *,
                   commit_from: str, commit_to: str) -> CoherenceReport:
    """Factory: open the reference store once and compute the two-snapshot coherence between the
    citation snapshots at `commit_from` (earlier, X_n) and `commit_to` (later, X_{n+1}). Both views
    are built off the SAME store handle (then discarded); the returned report holds no store
    reference."""
    from config.loader import get_config
    from core.stores.reference_edges import open_reference_edge_store

    cfg = config or get_config()
    store = open_reference_edge_store(cfg)
    view_from = TemporalView.over(store, commit=commit_from)
    view_to = TemporalView.over(store, commit=commit_to)
    return view_from.coherence_to(view_to)


def supersession_wellfounded(config: Config | None = None, *, doc_ids: list[str],
                             version_store: VersionStore | None = None) -> bool:
    """`δ_D²=0` over the supersession version chains of `doc_ids` — True iff the assembled relation
    is a genuine strict partial order (H0). A `SupersessionCycleError` PROPAGATES (a data defect — a
    rename that forked a chain, bp-031; §10 stop-and-raise), never swallowed into a False.

    `doc_ids` is REQUIRED (no all-docs default): `VersionStore` exposes no doc_id enumerator, so a
    "scan every versioned doc" scope is not reachable from this read (finding-0082 — a
    `VersionStore.doc_ids()` read would enable it, an owner-gated write to versions.py). Callers
    scope explicitly; `open_supersession_wellfounded` scopes to the anchor's corpus nodes.
    `version_store` is an optional injected handle (test seam); None opens the live store."""
    from config.loader import get_config
    from core.stores.versions import open_version_store
    from core.temporal.boundary import delta_D_squared_is_zero, supersession_poset

    vs = version_store
    opened = vs is None
    if vs is None:
        cfg = config or get_config()
        vs = open_version_store(cfg)
    try:
        poset = supersession_poset(vs, doc_ids)
    finally:
        if opened:
            vs.close()
    return delta_D_squared_is_zero(poset)


def open_supersession_wellfounded(config: Config | None = None, *,
                                  commit: str | None = None) -> bool:
    """Convenience: check supersession well-foundedness over the CORPUS NODES of the citation
    snapshot at `commit` (the docs currently participating in citations; `doc_id == source_path`,
    bp-031). Scoped to the cited corpus, not every versioned doc (the gap, finding-0082) —
    the coupling to the citation axis is deliberate (plan §11)."""
    view = open_temporal_view(config, commit=commit)
    return supersession_wellfounded(config, doc_ids=list(view._complex.nodes))
