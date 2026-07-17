# ── Family: σ-connectivity instruments (graph measurement at a certified cut) · docs/NOTATION.md ──
# OBJECT:    σ*(A,B) = sup{σ : A ∼ B in G_σ(cut)} — the abstraction ultrametric — plus the CN-1
#            (σ-grid, cut) index and the one maximum spanning forest realizing every pairwise σ*
#            and its chain (the bottleneck edge of the unique MST path).
# INVARIANT: grid-relative, never extrapolated (unconnected at the loosest grid ⇒ None — an honest
#            bound); readings exist ONLY at a sound certified cut (crossing edges refuse); model-
#            free, deterministic, clockless (Law C4); imports core substrate only — NEVER eval (P1,
#            dn-core-graph-instruments).
# ENFORCED:  structurally — `acquire_mirror_cut` raises `CrossingEdgeError` / lets
#            `CutCertificateError` propagate (fail-closed); `_grid_snap` bounds σ* to the declared
#            grid; the P1 no-eval and Law-C4 no-clock teeth are permanent AST scans
#            (`tests/unit/test_graph_boundary.py`); the eval harness re-exports are `is`-identity-
#            pinned (P5) so the math cannot silently fork.
r"""CN-2 mathematics: σ*, the abstraction ultrametric, via one maximum spanning tree per cut.

The σ-connectivity family's keystone math, re-homed from `eval/harness/connectivity.py` by
bp-065 under `dn-core-graph-instruments` (P1/P2: graph mathematics is CORE vocabulary — the
peer of `MirrorGraph.local_clustering` and the `core/complex/` spectral family; the eval
harness keeps the *instrument* — readings, evidence, gates — and imports this). Deterministic,
model-free: NumPy cosine + a union-find MST, no model import, no LLM call, no clock (Law C4).
This module imports core substrate ONLY — never `eval` (the P1 boundary tooth,
`tests/unit/test_graph_boundary.py`). Design: `docs/design-notes/connectivity-instruments.md`
CN-1 + CN-2 (RATIFIED — math held verbatim, never re-derived here).

**σ* — the abstraction ultrametric (CN-2).** `σ*(A,B) = sup{σ : A ∼ B in G_σ(cut)}` — the
strictest abstraction threshold at which two thoughts still share a component. It is the
single-linkage / maximin-cosine path value, and **one maximum spanning tree over the
loosest-grid graph yields all pairwise σ* and the realizing chain** (the bottleneck edge of
the unique MST path). σ* is **grid-relative** (the fibers discipline): computed against the
declared σ-grid, the MST built at the loosest grid threshold `min(grid)`, the grid pinned in
every reading's evidence; a pair unconnected there reports **"not connected within grid"**
(`sigma_star=None`) — an honest bounded answer, never an extrapolation.

**The CN-1 index discipline.** Every instrument in this family is indexed by a point in
(σ, t, cut) space and DECLARES which axes it uses. σ* uses **(σ-grid, cut)** — no walk, hence
no t. The cut is the corpus-history coordinate; "the graph at a moment" exists only at a
**certified** cut (GC-3), and wall-clock indexes nothing (Law C4 — this module reads no
clock, stamps no time). `ConnIndex` and the latest-cut acquisition are the shared scaffolding
the whole family (conductance, bridges, helix) builds on.

**The cut gap (cross-reference-on-extension — NOT a correction).** `MirrorGraph.build`
(`core/dreaming/graph.py`) takes **no cut**; `MirrorView` has **no downset/at-cut surface**.
The dreamer never needed a cut, so this is not a bug there. This family *supplies* the cut
index externally: v1 builds the graph over the CURRENT `MirrorView` and records the LATEST
certified cut (`spine.cut_at(strata=frozenset({"mirror"}))`) as its history coordinate.
Historical / cut-restricted graphs are PARKED (bp-059 §11): a future `core/` plan adding a
`MirrorView` downset filter, with its own warrant.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from dataclasses import dataclass

from core.dreaming.graph import MirrorGraph
from core.temporal.spine import CertifiedCut, Spine

_MIRROR_STRATUM = frozenset({"mirror"})    # σ* cuts the mirror stratum (versions/catalog → COMMIT)

# The grid-snap tolerance: a raw bottleneck cosine that equals a grid point up to float noise must
# snap TO that point, not to the one below it. Cosines and grid values are both float64.
_SNAP_EPS = 1e-12


class CrossingEdgeError(RuntimeError):
    """The acquired cut has crossing generator edges (`spine.crossing_edges(cut) != []`) — an event
    inside the down-set reading from one outside it. The cut is not sound; refuse (the CN-1 legality
    tooth). Never emit a reading at an unsound cut (fail-closed)."""


# ── the CN-1 index object ───────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ConnIndex:
    """The CN-1 connectivity index — the coordinate every reading in this family carries. Each
    instrument declares WHICH of (σ-grid, t, cut) it uses; **σ* uses (grid, cut) — no t** (no walk).
    Shared scaffolding: conductance / bridges / helix reuse this object and the latest-cut
    acquisition below."""

    grid: tuple[float, ...]            # the declared σ-grid (ascending; loosest = grid[0])
    cut: CertifiedCut                  # the corpus-history coordinate (latest certified cut, v1)


@dataclass(frozen=True)
class SigmaStar:
    """One pair's σ* reading. `sigma_star` is the **grid-snapped** bottleneck cosine (the largest
    grid σ ≤ the maximin-path bottleneck), or **None** ⇒ "not connected within grid" (the pair's
    components split at the loosest grid threshold). `chain` is the realizing MST path (note
    digests, A→B inclusive); `()` when unconnected."""

    a: str
    b: str
    sigma_star: float | None
    chain: tuple[str, ...]


# ── the maximum spanning forest (CN-2) ──────────────────────────────────────────────────────────


@dataclass(frozen=True)
class MaxSpanningForest:
    """The maximum spanning tree of the loosest-grid graph — a FOREST when that graph is
    disconnected (one tree per component). `tree_adj[i]` are node i's tree neighbours with the edge
    cosine; `component[i]` is i's component root (equal roots ⇔ a maximin path exists ⇔ σ* is not
    None). Built ONCE (Kruskal, O(E log V)); per-pair σ* walks the prebuilt tree — never re-searches
    the MST."""

    digests: tuple[str, ...]                      # node index -> content digest
    index_of: dict[str, int]                      # digest -> node index
    tree_adj: dict[int, list[tuple[int, float]]]  # node -> [(tree-neighbour, edge cosine)]
    component: tuple[int, ...]                     # node -> component root id


def build_max_spanning_tree(graph: MirrorGraph) -> MaxSpanningForest:
    """One maximum spanning tree over the graph's σ-adjacency (built at the loosest grid threshold —
    the caller passes `MirrorGraph.build(view, sigma=min(grid))`). Edges are the pairs `graph`
    admits at its σ (`graph.neighbors`), weighted by the cosine `graph.sim[i,j]`; Kruskal
    descending on weight (ties broken by `(i, j)` for determinism) yields the maximum spanning
    FOREST. O(E log V) — built once; `sim`/`_adj` are never mutated."""
    n = graph.n
    digests = tuple(graph.digest(i) for i in range(n))
    index_of = {d: i for i, d in enumerate(digests)}
    # Distinct undirected edges present at graph.sigma, weighted by cosine.
    edges: list[tuple[float, int, int]] = []
    for i in range(n):
        for j in graph.neighbors(i):
            if j > i:
                edges.append((float(graph.sim[i, j]), i, j))
    edges.sort(key=lambda e: (-e[0], e[1], e[2]))     # descending weight, deterministic tie-break

    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    tree_adj: dict[int, list[tuple[int, float]]] = {i: [] for i in range(n)}
    for w, i, j in edges:
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[max(ri, rj)] = min(ri, rj)
            tree_adj[i].append((j, w))
            tree_adj[j].append((i, w))
    component = tuple(find(x) for x in range(n))
    return MaxSpanningForest(
        digests=digests, index_of=index_of, tree_adj=tree_adj, component=component
    )


def _tree_path_bottleneck(
    forest: MaxSpanningForest, ia: int, ib: int
) -> tuple[list[int], float] | None:
    """The unique tree path `ia → ib` and its **bottleneck** (minimum edge cosine along it), or
    None if the two nodes are in different components (no maximin path within the loosest grid). A
    DFS over the prebuilt tree adjacency — O(V), no MST re-search."""
    if forest.component[ia] != forest.component[ib]:
        return None
    # DFS from ia, recording each node's parent AND the cosine of the edge to that parent, so the
    # path and its bottleneck reconstruct in O(V) without a separate weight lookup.
    prev: dict[int, int] = {ia: ia}
    pw: dict[int, float] = {ia: float("inf")}          # edge cosine to parent (ia has none)
    stack = [ia]
    while stack:
        u = stack.pop()
        if u == ib:
            break
        for v, w in forest.tree_adj[u]:
            if v not in prev:
                prev[v] = u
                pw[v] = w
                stack.append(v)
    # Reconstruct the path ib → ia, then reverse; the bottleneck is the min edge cosine on it.
    path: list[int] = [ib]
    while path[-1] != ia:
        path.append(prev[path[-1]])
    bottleneck = min(pw[node] for node in path[:-1])   # every node except ia carries a parent edge
    path.reverse()
    return path, float(bottleneck)


def _grid_snap(value: float, grid: Sequence[float]) -> float:
    """The largest grid σ ≤ `value` (grid-relativity: σ* is snapped to the declared grid, never
    extrapolated). `value` is a raw path-bottleneck cosine ≥ grid[0] for any connected pair, so the
    result is always ≥ grid[0]. A small tolerance keeps a bottleneck that equals a grid point from
    snapping to the point below it under float noise."""
    snapped = grid[0]
    for g in grid:
        if g <= value + _SNAP_EPS:
            snapped = g
        else:
            break
    return float(snapped)


def sigma_star(
    forest: MaxSpanningForest, a: str, b: str, *, grid: Sequence[float]
) -> SigmaStar:
    """`σ*(A,B)` and its realizing MST chain, read off the prebuilt forest. Grid-snapped bottleneck
    + the tree path (digests, A→B inclusive) for a connected pair; `sigma_star=None, chain=()` for a
    pair whose components split at the loosest grid ("not connected within grid")."""
    ia, ib = forest.index_of[a], forest.index_of[b]
    walked = _tree_path_bottleneck(forest, ia, ib)
    if walked is None:
        return SigmaStar(a=a, b=b, sigma_star=None, chain=())
    path, bottleneck = walked
    chain = tuple(forest.digests[k] for k in path)
    return SigmaStar(a=a, b=b, sigma_star=_grid_snap(bottleneck, grid), chain=chain)


def pairwise_sigma_star(
    forest: MaxSpanningForest, *, grid: Sequence[float]
) -> tuple[SigmaStar, ...]:
    """Every distinct pair's σ*, read off the single prebuilt forest (strongest first, id-stable).
    O(V²) tree walks over ONE MST — no per-pair MST re-search."""
    digests = forest.digests
    out = [
        sigma_star(forest, digests[i], digests[j], grid=grid)
        for i in range(len(digests))
        for j in range(i + 1, len(digests))
    ]
    out.sort(key=lambda s: (s.sigma_star is not None, s.sigma_star or 0.0, s.a, s.b), reverse=True)
    return tuple(out)


# ── the cut acquisition + fingerprint (CN-1) ────────────────────────────────────────────────────


def cut_fingerprint(cut: CertifiedCut) -> str:
    """A deterministic content hash of the certified cut — its frontier, the certificates it
    composed, and their evidence (the sourced observables, never wall-time). Rides in the family's
    evidence pins so the history coordinate a reading measured stays independently recoverable and
    cut drift is detectable."""
    payload = json.dumps(
        {
            "frontier": [list(pair) for pair in cut.frontier],
            "certificates": sorted(c.value for c in cut.certificates),
            "evidence": list(cut.evidence),
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def acquire_mirror_cut(spine: Spine) -> CertifiedCut:
    """The latest certified cut over the mirror stratum — the family's history coordinate (v1). Lets
    `CutCertificateError` propagate (fail-closed: a cut with no COMMIT certificate REFUSES; we never
    fabricate one). Asserts the CN-1 legality tooth (`crossing_edges == []`): an unsound cut raises
    `CrossingEdgeError`, never emits a reading."""
    cut = spine.cut_at(strata=_MIRROR_STRATUM)
    crossings = spine.crossing_edges(cut)
    if crossings:
        raise CrossingEdgeError(
            f"the acquired mirror cut has {len(crossings)} crossing generator edge(s) "
            f"{crossings[:3]}… — an event inside the down-set reads from one outside it, so the "
            "cut is not sound (CN-1 legality tooth). Refusing to emit a reading at an unsound cut."
        )
    return cut
