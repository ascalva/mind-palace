# ── Family: arrow-aware census · directed structure as time's residue · docs/NOTATION.md ──────────
# OBJECT:    the combinatorial census — exact directed invariants over the composed assembly's arrow
#            layer at ONE certified cut (dn-synchronic-diachronic-dreamer §2.8 the ARROW-READ, §2.3
#            "the directional sense is the census, and only the census"). Three claim shapes, each
#            WITNESSED by construction: influence loops (directed cycles on X_cite), revision-effort
#            asymmetries (unbalanced diamonds — a branch's revision count vs its sibling's), and
#            reach-backs (a note re-citing something younger than its own first authorship).
# INVARIANT: read-only and PURELY combinatorial — gauge-immune by construction (ML §2.7b: no phase,
#            no spectrum, no flux enters). Direction is time's RESIDUE (a frozen record of a
#            temporal event), never a causal claim. Deterministic: same arcs + cut ⇒ same readings.
#            Every claim carries its reproducible witness (arc ids / first-authorship evidence); the
#            empty census yields ZERO claims (silence, never filler — §2.9-d). No store import, no
#            clock materialized, no ML-a operator (the deferral is ratified — §2.3).
# ENFORCED:  guard (tests/unit/test_census.py) — a planted 3-cycle / unbalanced diamond /
#            retro-citation each enumerate with their exact witness; an arrowless control returns
#            empty; two runs at one cut are bit-identical; every reading records its anchored cut.
r"""The arrow-aware combinatorial census (dn-synchronic-diachronic-dreamer §2.8 SD-8 / §2.3 SD-3).

Direction is time's residue in the *synchronic* graph: a directed edge (a citation, a supersession,
a derivation) is a frozen record of a temporal event, so a point-window dispatch at ONE certified
cut can read temporal structure without touching the parked diachronic execution (§2.8). This module
is that read — the census instrument named in the `DreamCharter`'s grant
(`core/dreaming/charter.py`, `Instrument.CENSUS`). It enumerates three families, each witnessed:

  * **influence loops** — directed cycles ("A cites B cites C cites A, a closed influence loop").
    Witness: the ordered arc set that closes the loop.
  * **revision-effort asymmetries** — unbalanced diamonds ("this branch took three revisions where
    its sibling took one"). Witness: the two internally-disjoint paths' chain positions.
  * **reach-backs** — a note re-cites something younger than its own first authorship, a
    revision-mediated backflow. Witness: the citing arc plus BOTH endpoints' first-authorship
    evidence (chain positions, never a wall clock — Law C4).

**PURE-CORE / INJECTED (the composed.py + evaluate.py pattern).** The census reads no store: its
input is an explicit directed arc set (the arrow layer over the composed assembly's node set —
`core/graph/composed.py` carries the *undirected* σ-layer; the arrows come from `reference_edges`
X_cite and `versions` supersession chains) plus a first-authorship map, both INJECTED. Adapting the
live `ReferenceEdgeStore` / `VersionStore` reads at a cut into these records is a later plan's call
(the first live Thread-C sweep, note §2.8 — "likely empty on today's corpus"); here the acquisition
side is fixtures, so the reader is exercised store-free. Imports only stdlib and
`core.temporal.spine.CertifiedCut` (both pure-core) — no sibling first-party import, so the census
adds nothing to the finding-0103 ratchet.

**The vocabulary is records-not-causes (§2.9 ADOPTED).** This module produces the FACTS (member
refs + witnesses); the narration layer (`core/dreaming/interpreters.py`, the census lens) renders
them arrow-literally. Nothing here phrases a claim as causation; nothing here speaks flux/spectral
language — there is none to speak (combinatorial invariants are gauge-immune, ML §2.7b).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any

from core.temporal.spine import CertifiedCut

# ═══════════════════════════════════════════════════════════════════════════════════════════════
# Claim-kind discriminators — one per claim SHAPE (plan §11 parked default: per-shape, not one
# CENSUS kind, so adjudication keeps the per-shape signal). Cited by the census lens.
# ═══════════════════════════════════════════════════════════════════════════════════════════════

# A simple path as (node sequence, arc-witness sequence) — the shape `_simple_paths` yields.
_Path = tuple[tuple[str, ...], tuple[str, ...]]

INFLUENCE_LOOP = "influence_loop"           # a directed cycle on the citation arcs
REVISION_ASYMMETRY = "revision_asymmetry"   # an unbalanced diamond (a branch vs its sibling)
REACH_BACK = "reach_back"                   # a citation to a node younger than the citer

# A generous, documented bound on path/cycle length — a guard against combinatorial blow-up on a
# pathological arc set, NOT a modelling choice: on the empty/tiny corpus the census actually reads
# (§2.8) it never binds. Raise it deliberately if a real sweep ever needs a longer loop.
DEFAULT_MAX_LEN = 12


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# Inputs — the injected directed arc set + the first-authorship map (both fixtures here)
# ═══════════════════════════════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class Arc:
    """A directed arc — `source → target` — carrying the identifier of the record that WITNESSES it
    (a `ReferenceEdge.edge_id` for a citation, a version-pair key for a supersession). `kind` tags
    the arrow's provenance (`citation` | `supersession` | `derivation`). Direction is time's
    residue, never a causal assertion (§2.9-b)."""

    source: str
    target: str
    witness: str
    kind: str = "citation"


@dataclass(frozen=True)
class FirstAuthorship:
    """A node's first-authorship record — the `version_seq = 1` evidence for a corpus artifact.
    `rank` is a chain position (an integer causal rank the caller derives from the certified cut's
    frontier, NEVER a wall timestamp — Law C4, `core/temporal/spine.py`); `evidence` names the
    version row(s) that witness it (`doc_id:version_seq` / digest). A reach-back needs BOTH
    endpoints' records witnessed — a missing one yields no claim (the honest seam, §2.9-d)."""

    ref: str
    rank: int
    evidence: tuple[str, ...] = ()


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# Outputs — a witnessed claim + a reading anchored to its cut
# ═══════════════════════════════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class CensusClaim:
    """One census fact, WITNESSED by construction. `members` are the corpus artifacts the claim
    rests on (authored refs — they become the panel `Claim.support`); `witness` is the reproducible
    evidence (arc ids / first-authorship evidence — the census's whole claim is exactness); `detail`
    carries shape-specific structure (the ordered path, the branch lengths, the ranks). No narration
    here — the lens renders records-not-causes (§2.9)."""

    kind: str
    members: tuple[str, ...]
    witness: tuple[str, ...]
    detail: dict[str, Any] = field(default_factory=dict[str, Any])


@dataclass(frozen=True)
class CensusReading:
    """A census read at ONE certified cut (§2.8: synchronic only — point window, no cross-cut
    transport). `cut` is the anchor recorded in every reading (Item 4 acceptance); `claims` are the
    witnessed facts, deterministically ordered. An empty tuple is the honest seam — the census found
    no directed structure, and that is silence, not a dream (§2.9-d)."""

    cut: CertifiedCut
    claims: tuple[CensusClaim, ...]


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# The combinatorial core — deterministic, witnessed enumeration
# ═══════════════════════════════════════════════════════════════════════════════════════════════


def _adjacency(arcs: Iterable[Arc]) -> tuple[list[str], dict[str, list[tuple[str, str]]]]:
    """Sorted node list + a sorted out-adjacency `node → [(target, witness), …]`. Sorted throughout
    so every downstream enumeration is deterministic regardless of input arc order."""
    adj: dict[str, list[tuple[str, str]]] = {}
    nodes: set[str] = set()
    for a in arcs:
        nodes.add(a.source)
        nodes.add(a.target)
        adj.setdefault(a.source, []).append((a.target, a.witness))
    for src in adj:
        adj[src].sort()
    return sorted(nodes), adj


def influence_loops(arcs: Iterable[Arc], *, max_len: int = DEFAULT_MAX_LEN) -> list[CensusClaim]:
    """Enumerate directed elementary cycles — closed influence loops (§2.8). Each cycle is emitted
    ONCE, canonicalized to start at its minimum node (only nodes ranked above the start extend the
    path), so `A→B→C→A` and its rotations are one claim. Witness = the ordered arc ids that close
    the loop; members = the loop's nodes in traversal order. Deterministic (sorted throughout)."""
    nodes, adj = _adjacency(arcs)
    rank = {n: i for i, n in enumerate(nodes)}
    claims: list[CensusClaim] = []

    for start in nodes:
        start_rank = rank[start]

        def _extend(v: str, path: list[str], used: list[str], seen: set[str],
                    start: str = start, start_rank: int = start_rank) -> None:
            for target, witness in adj.get(v, []):
                if target == start and len(path) >= 2:
                    claims.append(CensusClaim(
                        kind=INFLUENCE_LOOP,
                        members=tuple(path),
                        witness=tuple(used + [witness]),
                        detail={"cycle": list(path), "length": len(path)},
                    ))
                elif (rank.get(target, -1) > start_rank and target not in seen
                      and len(path) < max_len):
                    _extend(target, path + [target], used + [witness], seen | {target})

        _extend(start, [start], [], {start})

    claims.sort(key=lambda c: (c.members, c.witness))
    return claims


def _simple_paths(adj: dict[str, list[tuple[str, str]]], start: str, max_len: int,
                  ) -> dict[str, list[_Path]]:
    """Every simple directed path out of `start`, grouped by endpoint: `target → [(nodes, arcs), …]`
    with node/arc counts bounded by `max_len`. Deterministic (sorted adjacency)."""
    results: dict[str, list[_Path]] = {}

    def _walk(v: str, path: list[str], used: list[str], seen: set[str]) -> None:
        for target, witness in adj.get(v, []):
            if target in seen:
                continue
            npath, nused = path + [target], used + [witness]
            results.setdefault(target, []).append((tuple(npath), tuple(nused)))
            if len(npath) <= max_len:
                _walk(target, npath, nused, seen | {target})

    _walk(start, [start], [], {start})
    return results


def revision_asymmetries(arcs: Iterable[Arc], *, max_len: int = DEFAULT_MAX_LEN,
                         ) -> list[CensusClaim]:
    """Enumerate unbalanced diamonds — a source and a sink joined by two internally-disjoint
    directed paths of DIFFERENT length ("a branch took three revisions where its sibling took one",
    §2.8).
    One claim per (source, sink): the representative pair is the interior-disjoint pair of differing
    length that maximizes the length gap (ties broken lexicographically) — the sharpest asymmetry.
    Witness = both paths' arc ids; members = every node on either branch. Deterministic."""
    nodes, adj = _adjacency(arcs)
    claims: list[CensusClaim] = []

    for source in nodes:
        by_sink = _simple_paths(adj, source, max_len)
        for sink in sorted(by_sink):
            # Deterministic path order: by length, then node sequence, then arc sequence.
            paths = sorted(by_sink[sink], key=lambda pa: (len(pa[0]), pa[0], pa[1]))
            best: tuple[_Path, _Path] | None = None
            best_gap = 0
            for i in range(len(paths)):
                p_nodes, _ = paths[i]
                p_interior = set(p_nodes[1:-1])
                for j in range(i + 1, len(paths)):
                    q_nodes, _ = paths[j]
                    if len(p_nodes) == len(q_nodes):
                        continue                          # balanced — not an asymmetry
                    if p_interior & set(q_nodes[1:-1]):
                        continue                          # branches share an interior node
                    gap = abs(len(p_nodes) - len(q_nodes))
                    if gap > best_gap:
                        best_gap = gap
                        best = (paths[i], paths[j])
            if best is None:
                continue
            short, long = sorted(best, key=lambda p: len(p[0]))   # shorter branch first
            short_nodes, short_arcs = short
            long_nodes, long_arcs = long
            members = tuple(sorted(set(short_nodes) | set(long_nodes)))
            claims.append(CensusClaim(
                kind=REVISION_ASYMMETRY,
                members=members,
                witness=tuple(short_arcs) + tuple(long_arcs),
                detail={
                    "source": source,
                    "sink": sink,
                    # arc counts = revision-effort on each branch (chain positions).
                    "short_revisions": len(short_arcs),
                    "long_revisions": len(long_arcs),
                    "short_path": list(short_nodes),
                    "long_path": list(long_nodes),
                },
            ))

    claims.sort(key=lambda c: (c.members, c.witness))
    return claims


def reach_backs(arcs: Iterable[Arc], authorship: Mapping[str, FirstAuthorship],
                ) -> list[CensusClaim]:
    """Enumerate reach-backs — a citation arc `A → B` where B's first-authorship is YOUNGER than A's
    (rank(B) > rank(A)): A re-cites something that came into being after A did, a revision-mediated
    backflow (§2.8). Only citation arcs qualify (a supersession is not a re-citation). A missing
    first-authorship record for either endpoint yields no claim — the census cannot witness what it
    was not given (the honest seam). Witness = the citing arc id + BOTH endpoints' first-authorship
    evidence. Deterministic."""
    claims: list[CensusClaim] = []
    for arc in sorted(arcs, key=lambda a: (a.source, a.target, a.witness)):
        if arc.kind != "citation":
            continue
        citer, cited = authorship.get(arc.source), authorship.get(arc.target)
        if citer is None or cited is None:
            continue                                      # unwitnessed endpoint — no claim
        if cited.rank > citer.rank:                       # the cited note is younger than the citer
            claims.append(CensusClaim(
                kind=REACH_BACK,
                members=(arc.source, arc.target),
                witness=(arc.witness, *citer.evidence, *cited.evidence),
                detail={
                    "citer": arc.source,
                    "cited": arc.target,
                    "citer_rank": citer.rank,
                    "cited_rank": cited.rank,
                },
            ))
    claims.sort(key=lambda c: (c.members, c.witness))
    return claims


def census(arcs: Iterable[Arc], authorship: Mapping[str, FirstAuthorship], cut: CertifiedCut,
           *, max_len: int = DEFAULT_MAX_LEN) -> CensusReading:
    """The census reader — the three witnessed families over ONE certified cut, in a single reading
    that records its anchor (Item 4). Synchronic only: `cut` pins the point window (§2.8). Snapshot
    `arcs` once so every family reads the same set. An empty census returns an empty reading —
    silence, never filler (§2.9-d)."""
    arc_list = list(arcs)
    claims: list[CensusClaim] = [
        *influence_loops(arc_list, max_len=max_len),
        *revision_asymmetries(arc_list, max_len=max_len),
        *reach_backs(arc_list, authorship),
    ]
    return CensusReading(cut=cut, claims=tuple(claims))
