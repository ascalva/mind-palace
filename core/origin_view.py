# ── Family 1 boundary (labelings & information-flow) · symbols in docs/NOTATION.md ──
# OBJECT:    `origin(e)` — the provenance-spine read: given a durable edge id, the C-edge whose
#            witnessed commit MINTED it (dn-agentic-loop §2.4b EX-2). A derived, regenerable
#            two-hop join `C ∘ commit-keying` over the built stores (`reference_edges` supply the
#            commit key an edge carries; `causal_edges` supply the dialogue action that witnessed
#            that commit) — the exhaust→created-structure relation, queried, never materialized.
# INVARIANT: NO store, NO minted rows. This is a pure read over two existing stores — it composes
#            what rows already carry (the fiber-vs-edge criterion, dn-agent-taxonomy §2.4) and
#            mints nothing. The origin links are DISPOSITIONAL (E_disp, the-edge-model §3): they are
#            NEVER assembled into `A_geom`/L — this module returns a single `CausalEdge` (or None),
#            builds no adjacency, exposes no graph. Acyclic by construction (exhaust → created only;
#            no PD-7 "informed-by" return edge). Read-only: it calls only the stores' READERS.
# ENFORCED:  static (a free function returning `CausalEdge | None`, no store/connection reachable
#            through it) + guard (tests/unit/test_origin_view.py: F-AL7 — the result is reproduced
#            from witnesses + commit keys ALONE, and no row is minted).
"""`origin(e)` — the exhaust→created-structure provenance spine as a derived view (dn-agentic-loop
§2.4b EX-2, ruled: "expose `origin` as a derived, regenerable traversal/view — do not mint
edge-of-edges rows").

The owner's sharpest ask — *which dialogue action produced this durable edge?* — is answerable
today without any new store, because every durable edge already carries its origin coordinate:

  * **the commit key (F-side).** A reference edge (`core/stores/reference_edges.py`, X_cite) carries
    `commit_sha` — the commit at which the reading landed, i.e. the commit that MINTED that edge.
  * **the witness (C-side).** A causal edge (`core/stores/causal_edges.py`) with `dst_type='commit'`
    carries `pair_cut_sha` = the full sha of the commit its dialogue action produced, plus the
    witness `(witness_digest, witness_turn)` (dn-agent-taxonomy §2.5).

So `origin(e) := the C-edge whose witnessed commit minted e` is a typed **two-hop join**
`C ∘ commit-keying` — the same family as C∘D ("which conversation produced this version?"): hop 1
resolves `e`'s commit key (`reference_edges → commit_sha`); hop 2 finds the causal edge whose
`pair_cut_sha` equals that key. It regenerates from the rows every run; nothing is stored.

**The target-kind boundary (F-AL7 / §3 Q3).** `origin` is scoped to the durable-edge kind that
carries a resolvable commit key: **reference edges** (X_cite), whose `commit_sha` IS that key. A
causal edge's own file/doc endpoints carry `pair_cut_sha=''` (a working-tree write has no commit
anchor, finding-0111) — so an edge-of-edge over those has no commit key to join on and is OUT of
`origin`'s domain (recorded, not papered over). When a consumer needs row-grain origin over those,
the edge-as-endpoint vocabulary is expressible then (PD-8) — parked.

**Why a view, never a store (EX-2, two grounds).** (1) The fiber-vs-edge criterion: derivation
tissue stored as graph edges duplicates what rows already carry and pollutes connectivity with
derivation stars (dn-agent-taxonomy §2.4). (2) The edge-model classifies provenance-spine links as
dispositional (E_disp — never assembled into `A_geom`/L), so materializing them buys no instrument
any power the join lacks. This module therefore returns a value, holds no state, and mints nothing.

Pure-core: imports only `core.stores.*` (themselves store-free of network/model); no `edge/`, no
network, no model in the path.
"""

from __future__ import annotations

from typing import Any

from core.stores.causal_edges import CausalEdge, CausalEdgeStore
from core.stores.reference_edges import ReferenceEdgeStore


def _causal_edge_from_row(row: dict[str, Any]) -> CausalEdge:
    """Rebuild the frozen `CausalEdge` from a store row (the store hands back dicts). No identity is
    re-minted — the row's `edge_id` is carried through verbatim; this only re-types the read."""
    return CausalEdge(
        edge_id=row["edge_id"],
        session_id=row["session_id"],
        event_order=int(row["event_order"]),
        kind=row["kind"],
        dst_type=row["dst_type"],
        dst=row["dst"],
        witness_digest=row["witness_digest"],
        witness_turn=int(row["witness_turn"]),
        pair_cut_sha=row["pair_cut_sha"],
    )


def origin(
    edge_id: str,
    *,
    causal_edges: CausalEdgeStore,
    reference_edges: ReferenceEdgeStore,
) -> CausalEdge | None:
    """The C-edge whose witnessed commit minted the durable edge `edge_id` — the derived regenerable
    two-hop join `C ∘ commit-keying` (dn-agentic-loop §2.4b EX-2). Returns `None` when `edge_id` is
    not a known reference edge, carries no commit key, or no causal edge witnessed that commit
    (a legitimate empty answer — e.g. a pre-integration commit; NOT a falsifier).

    Read-only over the two stores; mints nothing; the returned link is dispositional (E_disp — never
    enters `A_geom`/L). Scoped to reference-edge (X_cite) ids — the durable kind that carries a
    resolvable `commit_sha` (the recorded target-kind boundary, F-AL7 / §3 Q3)."""
    # Hop 1 — commit-keying: resolve `edge_id` to the commit key the reference edge carries. The
    # store exposes no by-id reader (adding one is out of scope: `core/stores/**` stays read-only),
    # so filter the read surface. `commit_sha` IS the minting-commit coordinate (edge identity).
    commit_key = ""
    for ref in reference_edges.all():
        if ref.edge_id == edge_id:
            commit_key = ref.commit_sha
            break
    if not commit_key:
        return None

    # Hop 2 — C: the causal edge whose WITNESSED commit is that key. A commit-species C-edge carries
    # `pair_cut_sha` = the full sha (finding-0111); file/doc edges carry '' and so never match a
    # non-empty key. Deterministic on the (rare) multi-witness case: lowest (event_order, edge_id).
    matches = [
        _causal_edge_from_row(row)
        for row in causal_edges.all_edges()
        if row["pair_cut_sha"] == commit_key
    ]
    if not matches:
        return None
    return min(matches, key=lambda e: (e.event_order, e.edge_id))
