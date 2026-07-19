r"""Phase Δ — the oq-0031 connectivity re-measure (bp-073). Eval-side, model-free assembly.

The payoff measurement of the Β→Γ→Δ arc: does a SECOND, proven edge class break the
13-doc connectivity saturation (finding-0096), or is the ceiling real? This module
assembles the composed graph `{dialogue-artifact nodes} × {E_sim ∪ E_proven}` and feeds it
UNCHANGED to the ratified σ*/conductance math (`core.graph.sigma_star`, `.conductance`),
then attributes connectivity to E_sim vs E_proven via `ComposedGraph.classes_of` (the
falsifier the taxonomy names).

**Grounding (bp-073 Item 0, owner ruling A; finding-0112).** The mirror vectorstore holds
only 17 authored janus_notes, which carry NO C-edges — so E_proven is empty over the mirror
and cannot break its saturation. The measurement is non-trivial only over the
**dialogue-artifact** corpus (the ~208 docs that DO carry C-edges: build-plans, findings,
design-notes, brainstorms). Those docs are unembedded and the mirror firewall
(`MIRROR_READABLE={authored}`) refuses them, so Δ **embeds them eval-side** (ephemeral,
never persisted — Item 2b) to obtain E_sim. This is the note's own intent (§3) + the Q3
lean ("reuse the mirror's cosine machinery over dialogue_artifact embeddings").

**The two edge classes.**
- **E_sim** — cosine over doc centroids, kept where `cos >= sigma_floor` (the loosest grid
  σ) exactly as `MirrorGraph.build(view, sigma=min(grid))` does, so the σ*/MST math (whose
  `_grid_snap` floors at grid[0]) sees an equivalent graph. Reuses `core.dreaming.cluster`.
- **E_proven** — **shared-witness co-production**: two docs edited in the SAME dialogue
  session are causally co-produced, so every unordered pair of distinct doc endpoints in a
  session is a proven doc↔doc edge (weight 1.0, present at every grid σ — it can bridge two
  similarity components). Each carries its witness; a pair with no witness FAILS LOUD (the
  Item 1 falsifier). NO commit→file fan-out (finding-0111's inferred-edge falsifier) — the
  pair comes from the two proven writes directly (Q2, owner-confirmed at mint).

**Pure/injected (finding-0100 + composed.py's discipline).** `assemble_composed_graph`
takes the node set, an embeddings map, and the C-edge rows as arguments — it reads no store
and calls no embedder, so it is fixture-testable without ollama. The live read-only loaders
(`*_ro` / `embed_docs`) feed it the real corpus (Item 2).
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

from core.dreaming.cluster import NoteVector, similarity_matrix
from core.dreaming.graph import MirrorGraph
from core.graph.composed import (
    E_PROVEN,
    E_SIM,
    PROVEN_WEIGHT,
    ComposedGraph,
    WeightedEdge,
    compose,
)
from core.graph.sigma_star import SigmaStar, build_max_spanning_tree, pairwise_sigma_star


# ── the witness the co-production projection carries (the witness law, §2.5) ──────────────
@dataclass(frozen=True)
class ProvenEndpoint:
    """One doc endpoint's coordinates within its session — a proven L1 write event."""

    dst: str                 # the doc artifact-id (the graph node)
    event_order: int         # the L1 event's ord within its session
    witness_turn: int        # the dialogue turn the write ran under
    witness_digest: str      # the session transcript_digest (the raw the edge was read from)


@dataclass(frozen=True)
class ProvenPair:
    """A witnessed E_proven doc↔doc edge: two docs co-produced in one session. `a < b`, and
    the witness is the concatenated tuple (session + both endpoints) — enough to re-derive or
    refute the edge from retained raw (§2.5). A pair without a witness is not proven."""

    a: str
    b: str
    session_id: str
    endpoints: tuple[ProvenEndpoint, ProvenEndpoint]

    @property
    def witness_digests(self) -> tuple[str, str]:
        return (self.endpoints[0].witness_digest, self.endpoints[1].witness_digest)


class WitnesslessProvenEdge(ValueError):
    """A proven edge was projected without a witness digest — it cannot be re-derived from
    raw, so it is not proven (the Item 1 falsifier). Fail loud, never mint it."""


# ── E_proven — shared-witness co-production (Q2) ──────────────────────────────────────────
def proven_pairs_from_causal(
    causal_edges: Iterable[Mapping[str, object]], *, node_ids: Iterable[str]
) -> list[ProvenPair]:
    """Project the C-edge action-log into witnessed doc↔doc pairs by shared-witness
    co-production: group edges by `session_id`; within a session, every unordered pair of
    DISTINCT `doc` endpoints (restricted to `node_ids`) is a proven edge carrying both
    writes' witnesses. An empty `witness_digest` raises `WitnesslessProvenEdge`. Returns one
    `ProvenPair` per (session, doc-pair); the same pair across sessions yields several pairs
    (several witnesses) — dedup to graph edges happens at `compose` time (max weight)."""
    keep = frozenset(node_ids)
    # session_id -> {dst: earliest ProvenEndpoint for that doc in the session (min order)}
    by_session: dict[str, dict[str, ProvenEndpoint]] = {}
    for e in causal_edges:
        if str(e["dst_type"]) != "doc":
            continue
        dst = str(e["dst"])
        if dst not in keep:
            continue
        digest = str(e["witness_digest"])
        if not digest:
            raise WitnesslessProvenEdge(
                f"doc endpoint {dst!r} (session {e['session_id']!r}, order "
                f"{e['event_order']!r}) has an empty witness_digest — a proven edge must "
                "carry the raw it was read from"
            )
        endpoint = ProvenEndpoint(
            dst=dst, event_order=int(e["event_order"]),
            witness_turn=int(e["witness_turn"]), witness_digest=digest,
        )
        docs = by_session.setdefault(str(e["session_id"]), {})
        prior = docs.get(dst)
        if prior is None or endpoint.event_order < prior.event_order:
            docs[dst] = endpoint

    pairs: list[ProvenPair] = []
    for session_id, docs in by_session.items():
        ordered = sorted(docs.values(), key=lambda ep: ep.dst)
        for i in range(len(ordered)):
            for j in range(i + 1, len(ordered)):
                pairs.append(ProvenPair(
                    a=ordered[i].dst, b=ordered[j].dst,
                    session_id=session_id, endpoints=(ordered[i], ordered[j]),
                ))
    pairs.sort(key=lambda p: (p.a, p.b, p.session_id))
    return pairs


def _proven_weighted_edges(
    pairs: Sequence[ProvenPair], *, proven_weight: float
) -> list[WeightedEdge]:
    """Collapse the witnessed pairs to the distinct `(a, b, weight)` triples `compose`
    consumes (the witness rides on `ProvenPair`; `compose` flattens duplicates by max)."""
    seen: set[tuple[str, str]] = set()
    out: list[WeightedEdge] = []
    for p in pairs:
        if (p.a, p.b) not in seen:
            seen.add((p.a, p.b))
            out.append((p.a, p.b, proven_weight))
    return out


# ── E_sim — cosine over doc centroids, thresholded at the loosest grid σ (Q3) ─────────────
def sim_edges_from_embeddings(
    embeddings: Mapping[str, Sequence[float]], *, node_ids: Iterable[str], sigma_floor: float
) -> list[WeightedEdge]:
    """Pairwise cosine over doc centroids, kept where `cos >= sigma_floor` — the same
    adjacency `MirrorGraph.build(view, sigma=min(grid))` produces (so the σ*/MST math, whose
    `_grid_snap` floors at grid[0], sees an equivalent graph). Only nodes with an embedding
    participate; a node in `node_ids` without one is E_sim-absent (proven-only). Reuses
    `core.dreaming.cluster` — no new similarity invented (Q3)."""
    keep = frozenset(node_ids)
    vecs = [
        NoteVector(digest=nid, title="", vector=tuple(float(x) for x in vec))
        for nid, vec in embeddings.items()
        if nid in keep
    ]
    vecs.sort(key=lambda nv: nv.digest)          # deterministic order → deterministic matrix
    if len(vecs) < 2:
        return []
    sim = similarity_matrix(vecs)
    out: list[WeightedEdge] = []
    for i in range(len(vecs)):
        for j in range(i + 1, len(vecs)):
            w = float(sim[i, j])
            if w >= sigma_floor:
                out.append((vecs[i].digest, vecs[j].digest, w))
    return out


# ── the assembly (pure/injected — the Δ composed graph) ───────────────────────────────────
def assemble_composed_graph(
    *,
    node_ids: Iterable[str],
    embeddings: Mapping[str, Sequence[float]],
    causal_edges: Iterable[Mapping[str, object]],
    sigma_floor: float,
    proven_weight: float = PROVEN_WEIGHT,
) -> ComposedGraph:
    """Assemble the Δ composed graph over an explicit doc node set: E_sim = doc cosine ≥
    `sigma_floor` (Q3), E_proven = witnessed co-production (Q2, weight `proven_weight`). The
    witness is asserted per proven edge in `proven_pairs_from_causal` (fail-loud).
    Pure/injected: reads no store, calls no embedder. Feed the result to
    `build_max_spanning_tree` via a `cast(MirrorGraph, …)`. `sigma_floor` MUST be min(grid)."""
    nodes = tuple(node_ids)
    proven = proven_pairs_from_causal(causal_edges, node_ids=nodes)
    sim_edges = sim_edges_from_embeddings(embeddings, node_ids=nodes, sigma_floor=sigma_floor)
    proven_edges = _proven_weighted_edges(proven, proven_weight=proven_weight)
    return compose(nodes, sim_edges, proven_edges, sigma=sigma_floor)


def _as_mirror(g: ComposedGraph) -> MirrorGraph:
    """composed.py's static bridge: `ComposedGraph` presents `MirrorGraph`'s runtime surface,
    so the σ*/MST math runs on it unchanged (the cast touches no math module)."""
    return cast(MirrorGraph, g)


# ── the re-measure + the oq-0031 verdict (Item 2) ─────────────────────────────────────────
@dataclass(frozen=True)
class ProvenBridge:
    """A pair E_sim leaves in different σ-components that E_proven connects — the oq-0031
    falsifier. `sigma_star_full` is the pair's σ* under E_sim∪E_proven (None under E_sim
    alone); `chain` is the realizing path; `chain_uses_proven` records that the path crosses
    ≥1 E_proven edge. NOTE: the proven edge (weight 1.0) is rarely the σ* BOTTLENECK — the
    bottleneck is the weakest E_sim edge on the path (it sets the threshold); the proven edge
    is what makes the path EXIST. So attribution is 'the path uses a proven edge'."""

    a: str
    b: str
    sigma_star_full: float
    chain: tuple[str, ...]
    chain_uses_proven: bool


@dataclass
class ReMeasureReport:
    """The oq-0031 re-measure verdict. `discriminates` is the Q4 criterion PINNED at Item 0:
    the PRIMARY signal is structural — ≥1 proven bridge (a pair None under E_sim, connected
    via a path crossing an E_proven edge). `frac_connected_by_sigma` is the saturation gauge
    (the finding-0096 analog): per grid σ, the fraction of pairs connected under E_sim alone
    vs E_sim∪E_proven — equal across the grid ⇒ E_proven adds nothing. golden_recall is a
    MIRROR-retrieval metric and does NOT transfer to the doc graph (Q4); its non-transfer is
    in `notes`, never forced green."""

    n_nodes: int
    n_sim_edges: int
    n_proven_edges: int
    n_pairs: int
    frac_connected_by_sigma: dict[float, tuple[float, float]]   # σ -> (E_sim, E_sim∪E_proven)
    proven_bridges: tuple[ProvenBridge, ...]
    discriminates: bool
    # σ*-uplift: pairs whose σ* strictly ROSE from E_sim-only to E_sim∪E_proven (None treated as
    # below any value, so a None→reading bridge counts too). On a corpus that is E_sim-connected at
    # the loosest grid, `proven_bridges` is vacuous (no disconnected pair to rescue) and THIS is the
    # correctly-calibrated structural signal — same nodes + E_sim, so the rise is due to E_proven.
    n_sigma_uplifted: int = 0
    notes: tuple[str, ...] = field(default_factory=tuple)


def _frac_connected(readings: Sequence[SigmaStar], grid: Sequence[float]) -> dict[float, float]:
    """Per grid σ, the fraction of pairs connected AT σ — i.e. σ* (grid-snapped) ≥ σ. A flat
    curve across the grid is the saturation signature (finding-0096); a curve that varies is
    discrimination. Denominator is the total pair count (unconnected pairs count as 0)."""
    total = len(readings)
    if total == 0:
        return {float(g): 0.0 for g in grid}
    out: dict[float, float] = {}
    for g in grid:
        hit = sum(1 for r in readings if r.sigma_star is not None and r.sigma_star >= g - 1e-12)
        out[float(g)] = hit / total
    return out


def _chain_uses_proven(graph: ComposedGraph, chain: Sequence[str]) -> bool:
    """True iff the realizing chain crosses ≥1 E_proven edge (`classes_of`). For a pair
    unconnected under E_sim, the connecting path MUST cross a proven edge — this verifies the
    attribution rather than assuming it (a bridge failing this is a bug, not a finding)."""
    return any(E_PROVEN in graph.classes_of(u, v)
               for u, v in zip(chain, chain[1:], strict=False))   # chain[1:] is one shorter


def re_measure_oq0031(
    *,
    node_ids: Iterable[str],
    embeddings: Mapping[str, Sequence[float]],
    causal_edges: Iterable[Mapping[str, object]],
    grid: Sequence[float],
    proven_weight: float = PROVEN_WEIGHT,
) -> ReMeasureReport:
    """Assemble the E_sim-only and E_sim∪E_proven graphs over the same node set, run the
    RATIFIED `sigma_star` over BOTH (via the `cast` bridge — no instrument change), and
    attribute the delta. A pair whose σ* flips None→reading between the two graphs is a
    **proven bridge**; `discriminates` iff any exist (Q4). Pure/injected — fixture-testable."""
    grid = tuple(sorted(float(g) for g in grid))
    if not grid:
        raise ValueError("re_measure_oq0031: empty σ-grid")
    floor = grid[0]
    nodes = tuple(node_ids)
    edges = list(causal_edges)

    g_sim = assemble_composed_graph(node_ids=nodes, embeddings=embeddings, causal_edges=[],
                                    sigma_floor=floor, proven_weight=proven_weight)
    g_full = assemble_composed_graph(node_ids=nodes, embeddings=embeddings, causal_edges=edges,
                                     sigma_floor=floor, proven_weight=proven_weight)
    f_sim = build_max_spanning_tree(_as_mirror(g_sim))
    f_full = build_max_spanning_tree(_as_mirror(g_full))

    r_sim = pairwise_sigma_star(f_sim, grid=grid)
    r_full = pairwise_sigma_star(f_full, grid=grid)
    sim_by_pair = {(r.a, r.b): r for r in r_sim}

    bridges: list[ProvenBridge] = []
    for r in r_full:
        if r.sigma_star is None:
            continue
        before = sim_by_pair.get((r.a, r.b))
        if before is not None and before.sigma_star is None:      # None under E_sim → reading
            bridges.append(ProvenBridge(
                a=r.a, b=r.b, sigma_star_full=float(r.sigma_star), chain=r.chain,
                chain_uses_proven=_chain_uses_proven(g_full, r.chain),
            ))
    bridges.sort(key=lambda br: (-br.sigma_star_full, br.a, br.b))

    neg_inf = float("-inf")
    n_uplifted = sum(
        1 for r in r_full
        if (r.sigma_star if r.sigma_star is not None else neg_inf)
        > (sim_by_pair[(r.a, r.b)].sigma_star
           if sim_by_pair.get((r.a, r.b)) and sim_by_pair[(r.a, r.b)].sigma_star is not None
           else neg_inf)
    )

    frac_sim = _frac_connected(r_sim, grid)
    frac_full = _frac_connected(r_full, grid)
    n_sim_edges = sum(1 for c in g_full.edge_classes.values() if E_SIM in c)
    n_proven_edges = sum(1 for c in g_full.edge_classes.values() if E_PROVEN in c)

    notes = (
        "golden_recall is a MIRROR-retrieval metric (janus_notes + the golden set); it does "
        "NOT transfer to the dialogue-artifact doc graph, so it is NOT reported here (Item 0 "
        "Q4). The saturation gauge is frac_connected_by_sigma; the PRIMARY verdict is "
        "structural (proven_bridges).",
    )
    return ReMeasureReport(
        n_nodes=g_full.n, n_sim_edges=n_sim_edges, n_proven_edges=n_proven_edges,
        n_pairs=len(r_full),
        frac_connected_by_sigma={g: (frac_sim[g], frac_full[g]) for g in map(float, grid)},
        proven_bridges=tuple(bridges), discriminates=bool(bridges),
        n_sigma_uplifted=n_uplifted, notes=notes,
    )


# ── live read-only loaders (Item 2 + Item 2b: NO writable handle to a corpus store) ───────
def open_causal_edges_ro(path: Path | str) -> sqlite3.Connection:
    """Open the C-edge store STRICTLY read-only (`file:…?mode=ro`), so the measurement holds
    no writable handle to a store the live daemon owns (Item 2b). A write through this
    connection raises `sqlite3.OperationalError: attempt to write a readonly database`."""
    conn = sqlite3.connect(f"file:{Path(path)}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def load_causal_edges(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Every C-edge row (the `all_edges()` shape), read off a read-only connection."""
    return [dict(r) for r in conn.execute(
        "SELECT * FROM causal_edges ORDER BY session_id, event_order, dst_type, dst").fetchall()]


def doc_node_ids(edges: Iterable[Mapping[str, object]]) -> list[str]:
    """The distinct `doc` endpoints across the C-edges — the dialogue-artifact node set (Q1)."""
    return sorted({str(e["dst"]) for e in edges if str(e["dst_type"]) == "doc"})


def resolve_doc_path(artifact_id: str, *, repo_root: Path) -> Path | None:
    """Map a C-edge doc artifact-id to its file (read-only). finding-XXXX → docs/findings/…;
    bp-XXX → docs/build-plans/bp-XXX/plan.md; a `*.md` basename → the design-note/brainstorm.
    Returns None if unresolved (the doc becomes a proven-only node — E_sim-absent, noted)."""
    root = Path(repo_root)
    if artifact_id.startswith("finding-"):
        cand = root / "docs/findings" / f"{artifact_id}.md"
        return cand if cand.exists() else None
    if artifact_id.startswith("bp-"):
        cand = root / "docs/build-plans" / artifact_id / "plan.md"
        return cand if cand.exists() else None
    name = artifact_id if artifact_id.endswith(".md") else f"{artifact_id}.md"
    for sub in ("docs/design-notes", "docs/brainstorms", "docs"):
        cand = root / sub / name
        if cand.exists():
            return cand
    hits = sorted(root.glob(f"docs/**/{name}"))
    return hits[0] if hits else None


def embed_docs(
    node_ids: Sequence[str], *, repo_root: Path, char_limit: int = 4000, batch: int = 16,
) -> tuple[dict[str, list[float]], list[str]]:
    """Embed each resolvable doc eval-side (ephemeral — NEVER persisted; the daemon's
    `vectors.lance` is untouched). One vector per doc from its head text truncated to
    `char_limit` (a coarse topical centroid within the embedder's context window — the doc
    graph is note-grain like the mirror; the truncation is the coarse-graining Item 0 noted).
    Empty files are skipped. Reads files read-only. Lazy-imports the embedder so this module
    imports without ollama. Returns (embeddings map, unresolved artifact-ids)."""
    from core.ingest.embed import build_embedder

    embedder = build_embedder()
    texts: list[str] = []
    resolved: list[str] = []
    unresolved: list[str] = []
    for nid in node_ids:
        path = resolve_doc_path(nid, repo_root=repo_root)
        if path is None:
            unresolved.append(nid)
            continue
        with open(path, encoding="utf-8") as fh:          # read-mode handle — cannot write
            text = fh.read()[:char_limit]
        if not text.strip():                               # empty doc → no vector (proven-only)
            unresolved.append(nid)
            continue
        texts.append(text)
        resolved.append(nid)

    embeddings: dict[str, list[float]] = {}
    for start in range(0, len(texts), batch):
        chunk = texts[start:start + batch]
        vectors = embedder.embed_documents(chunk)
        for nid, vec in zip(resolved[start:start + batch], vectors, strict=True):
            embeddings[nid] = [float(x) for x in vec]
    return embeddings, unresolved
