r"""G-A — the fiber-geometry measure-first survey (bp-085; ratified `dn-fiber-geometry` §2.6/§3).

The ONE read-only survey the note authorizes: eval-side readings only, **no core write**. It
imports the built instruments (`composed`, `hodge`, `curvature`, `conductance`, `sigma_star`,
`census`) and the `re_measure` assembly UNCHANGED, assembles the per-class graphs over the live
corpus (read-only), runs the M1–M8 battery, and emits every reading CN-1-indexed. Its **nulls
are results** — an expected-null / disjoint-population / deferred row is recorded as such, never
as measured zero-signal structure. A reading emitted without its CN-1 index tuple + grid is
malformed (the battery's own falsifier).

The battery (`dn-fiber-geometry` §2.6, verbatim so the reader reads no design from a pointer):

  | id | measurement | instruments (built) | gates |
  |----|-------------|---------------------|-------|
  | M1 | S/F/D/C skeleton overlap (pairwise support Jaccard on shared nodes) + per-class
         population census | composed assembly + reference_edges + versions | PD-a re-entry
         cond. 1; bundle-vs-sheaf |
  | M2 | mismatch densities (S↔C, S↔F) + cross-class gradient-potential correlation + conditional
         minting intensities (does C/F minting concentrate on high-cos pairs; E[Δw_S | D-event]) |
         composed.edge_classes, hodge potentials, version store | PD-a cond. 2; §2.2 coupling |
  | M3 | per-class triangle census (D: MUST be 0 — covering-only integrity, ML owner decision 3;
         F, C: empirical) | hodge.flag_triangles per class | §2.2 Hodge honesty table; D integrity |
  | M4 | S-field Hodge split (gradient/curl/harmonic energy fractions) | hodge.py | the deficit
         reading (§2.1-2); PD-b's potential customer |
  | M5 | Forman-vs-churn: forman() on the σ-graph conditioned on per-region D-minting rate — the
         sign question | curvature.py + versions | the routing story's sign (§2.4b); PD-c |
  | M6 | thermometer check: D-minting rate per region vs churn stats CN-4's a_seq consumes;
         per-region χ_s | versions + conductance.chi_s | §2.4c; CN-4 magnitude calibration |
  | M7 | dead-vs-live cluster three-field signature; the metric-mismatch field | all of the above |
         the phase model (§2.4a); the horizon prediction's first look |
  | M8 | σ-sweep (oq-0024) + bottleneck-vs-product chain divergence, scored against endorsed
         chains where any exist | sigma_star + conductance | the functional question (§2.4b) |
  | M9 | R1 sample-depth recheck (per-edge series counts) | reference/version stores | velocity
         tier gate (ride-along) |
  | M10| which fiber signatures appear in endorsed/census chains | census.py + dreamer exhaust |
         grammar calibration (ride-along) |

**Canonical alphabet Σ_move = {S, F, D, C}** (§2.0, finding-0140 correction): S = similarity
(`E_sim`, computed cosine), F = citation (`reference_edges`, recorded), D = supersession
(`versions`, recorded), C = causal-witnessed (`causal_edges` co-production, `E_proven`). **F is
citation, NOT similarity** — the survey's labels obey this table.

**Read-only discipline.** The class stores are opened `?mode=ro` (the `re_measure`
`open_causal_edges_ro` pattern) — NOT via `VersionStore`/`ReferenceEdgeStore`, which open
read-write and `mkdir` (they would touch the daemon's live dir). S is embedded eval-side
(ephemeral, never persisted — the `re_measure.embed_docs` pattern). No writable handle to any
corpus store is ever held.

**The node-space fact (drives M1).** The three recorded classes index DIFFERENT node spaces: C
endpoints are artifact-ids (`bp-000`, `finding-XXXX`, `agent-taxonomy.md`) → resolve to `docs/**`
repo paths; F corpus→corpus rows are already `docs/**` repo paths; D `versions.doc_id` is vault
janus-note paths + catalog UUIDs — a corpus DISJOINT from the docs/ dialogue-artifacts. So S/F/C
are normalized to the docs/ repo-relative path space (C via `re_measure.resolve_doc_path`), and D
sits over its own population — a measured fact, not an artifact.

**CN-1 index for an eval-side survey.** The σ*/connectivity family's live certified cut is a
Spine op over the mirror stratum (not buildable read-only over dialogue-artifacts from a
worktree). Each reading therefore pins its recoverable corpus coordinate as
`(git HEAD, σ-grid, node-space label, n_nodes, a content digest over the exact node set + edge
multiset measured)`. Every reading carries this index or it is malformed.
"""

from __future__ import annotations

import hashlib
import json
import math
import sqlite3
import subprocess
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np
import scipy.sparse as sp

from core.complex.curvature import forman
from core.complex.hodge import edge_index, flag_triangles, hodge_decompose
from core.graph.sigma_star import build_max_spanning_tree, pairwise_sigma_star
from eval.harness.re_measure import (
    _as_mirror,
    assemble_composed_graph,
    embed_docs,
    load_causal_edges,
    open_causal_edges_ro,
    proven_pairs_from_causal,
    resolve_doc_path,
    sim_edges_from_embeddings,
)

# The house fibers σ-grid (F9 lineage: bp-057 `_M` on [0.55, 0.75]). Declared, never inferred —
# CN-1 requires each reading declare its grid. `floor = min(grid)` is where the composed
# assembly / MST math thresholds (`re_measure`); `tight = max(grid)` is the strict semantic
# backbone the S geometry rows read (tractable under hodge.py's dense guard, and the most
# meaningful σ for triangle/curl structure). Each reading's index records the σ it used.
DEFAULT_GRID: tuple[float, ...] = (0.55, 0.65, 0.75)

# Default live corpus (read-only). The worktree has no live `data/`; the real stores are at the
# main checkout. Overridable for fixtures/tests.
DEFAULT_DATA_DIR = Path("/Users/ascalva/mind-palace/data")
DEFAULT_REPO_ROOT = Path("/Users/ascalva/mind-palace")


# ── the CN-1 index + the reading envelope ────────────────────────────────────────────────────
@dataclass(frozen=True)
class SurveyIndex:
    """The CN-1 coordinate every reading carries. `head` = git HEAD sha (the corpus commit);
    `grid` = the declared σ-grid; `sigma` = the grid point THIS reading measured at (a declared
    grid member); `node_space` = which node identity the reading lives over; `n_nodes` = its node
    count; `coordinate` = a sha256 over the exact node set + edge multiset measured (so the
    reading is independently recoverable). A reading whose index is absent/partial is malformed."""

    head: str
    grid: tuple[float, ...]
    sigma: float
    node_space: str
    n_nodes: int
    coordinate: str


@dataclass(frozen=True)
class Reading:
    """One M-row result. `status` ∈ {measured, expected-null, disjoint-population, deferred,
    instrument-blocked, data-integrity-violation}. A non-`measured` status carries its `reason`;
    `value` holds the numbers (possibly empty for a null). `index` is MANDATORY — the malformed
    check keys on it."""

    row: str
    status: str
    index: SurveyIndex
    value: dict[str, object] = field(default_factory=dict)
    reason: str = ""

    def to_dict(self) -> dict[str, object]:
        return {"row": self.row, "status": self.status, "index": asdict(self.index),
                "value": self.value, "reason": self.reason}


_MEASURED = "measured"
_EXPECTED_NULL = "expected-null"
_DISJOINT = "disjoint-population"
_DEFERRED = "deferred"
_BLOCKED = "instrument-blocked"
_INTEGRITY = "data-integrity-violation"


def _s_available(ctx: SurveyContext) -> bool:
    """S (computed) rows require eval-side embeddings. Absent ⇒ the S instrument is deferred (see
    `ctx.embedder_status`) — the row records the deferral + re-entry, never a measured zero."""
    return bool(ctx.s_embeddings)


# ── read-only class loaders (the re_measure `?mode=ro` pattern; NOT the RW store classes) ─────
def _open_ro(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def load_f_pairs(conn: sqlite3.Connection) -> list[tuple[str, str]]:
    """F = citation. The corpus→corpus `reference_edges` as undirected, deduplicated doc↔doc
    pairs in `docs/**` repo-path space (self-loops dropped). Recorded, commit-keyed (§2.0)."""
    seen: set[tuple[str, str]] = set()
    for r in conn.execute(
        "SELECT source_ref, target_ref FROM reference_edges "
        "WHERE source_kind='corpus' AND target_kind='corpus'"
    ):
        a, b = str(r["source_ref"]), str(r["target_ref"])
        if a == b:
            continue
        seen.add((min(a, b), max(a, b)))
    return sorted(seen)


def load_d_arcs(conn: sqlite3.Connection) -> list[tuple[str, str]]:
    """D = supersession. The consecutive-version arcs `(digest_k → digest_{k+1})` per `doc_id`
    (DERIVED from the ordered sequence, §4A ordering authority — never edge topology). Nodes are
    version content digests (vault / catalog space — DISJOINT from the docs/ artifacts)."""
    by_doc: dict[str, list[tuple[int, str]]] = {}
    q = "SELECT doc_id, version_seq, digest FROM versions ORDER BY doc_id, version_seq"
    for r in conn.execute(q):
        by_doc.setdefault(str(r["doc_id"]), []).append((int(r["version_seq"]), str(r["digest"])))
    arcs: list[tuple[str, str]] = []
    for _doc, seq_digests in by_doc.items():
        ordered = sorted(seq_digests)
        for (_, d0), (_, d1) in zip(ordered, ordered[1:], strict=False):
            if d0 != d1:                                   # a revert to identical bytes: not an arc
                arcs.append((d0, d1))
    return arcs


def load_authored_supersessions(conn: sqlite3.Connection) -> list[tuple[str, str]]:
    """The owner-declared D arcs `(superseded → superseding)` — the authored supersession layer."""
    return [(str(r["superseded"]), str(r["superseding"]))
            for r in conn.execute("SELECT superseded, superseding FROM authored_supersessions")]


def git_head(repo_root: Path) -> str:
    try:
        out = subprocess.run(["git", "-C", str(repo_root), "rev-parse", "HEAD"],
                             capture_output=True, text=True, check=True, timeout=15)
        return out.stdout.strip()
    except Exception:
        return "unknown"


# ── node-space normalization: S/F/C → docs/** repo-relative path ──────────────────────────────
def normalize_c_id(artifact_id: str, *, repo_root: Path) -> str | None:
    """A C artifact-id → its `docs/**` repo-relative path (the S/F/C common node key), or None if
    it does not resolve to a docs/ file (then it is not comparable to F and is dropped from the
    shared space, noted)."""
    p = resolve_doc_path(artifact_id, repo_root=repo_root)
    if p is None:
        return None
    try:
        return str(p.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return None


# ── graph helpers (build a per-class csr support over a shared node index) ────────────────────
def _csr_from_pairs(
    node_index: Mapping[str, int], pairs: Iterable[tuple[str, str]], *, weight: float = 1.0
) -> sp.csr_matrix:
    """A symmetric csr support over `node_index` from undirected `pairs` (endpoints outside the
    index are skipped). Weight is constant unless the caller supplies weighted triples elsewhere."""
    n = len(node_index)
    rows: list[int] = []
    cols: list[int] = []
    data: list[float] = []
    for a, b in pairs:
        ia, ib = node_index.get(a), node_index.get(b)
        if ia is None or ib is None or ia == ib:
            continue
        rows += [ia, ib]
        cols += [ib, ia]
        data += [weight, weight]
    if not rows:
        return sp.csr_matrix((n, n))
    coo = (np.asarray(data, dtype=np.float64),
           (np.asarray(rows, dtype=np.int64), np.asarray(cols, dtype=np.int64)))
    m = sp.coo_matrix(coo, shape=(n, n)).tocsr()
    m.data[:] = np.maximum(m.data, 0.0)
    return m


def _jaccard(a: set[str], b: set[str]) -> float:
    u = a | b
    return len(a & b) / len(u) if u else 0.0


def _coordinate(nodes: Sequence[str], edges: Iterable[tuple[str, ...]]) -> str:
    """A content digest over the exact node set + sorted edge multiset a reading measured — the
    CN-1 recoverability coordinate."""
    payload = json.dumps(
        {"nodes": sorted(nodes), "edges": sorted(tuple(e) for e in edges)},
        sort_keys=True, separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


# ── the assembled corpus context (loaded once, read-only) ─────────────────────────────────────
@dataclass
class SurveyContext:
    head: str
    grid: tuple[float, ...]
    repo_root: Path
    # S/F/C in docs/** path space:
    s_embeddings: dict[str, list[float]]       # path -> vector (embedded docs)
    s_edges: list[tuple[str, str, float]]      # path,path,cosine ≥ floor
    f_pairs: list[tuple[str, str]]             # path,path citation pairs (all, corpus→corpus)
    c_pairs: list[tuple[str, str]]             # path,path co-production pairs
    c_ids: list[str]                           # raw C artifact-ids (for population census)
    unresolved_c: list[str]                    # C ids that do not resolve to docs/** files
    # D in its own (disjoint) space:
    d_arcs: list[tuple[str, str]]              # version supersession arcs (content digests)
    d_authored: list[tuple[str, str]]          # authored supersessions
    d_doc_count: int
    d_version_count: int
    # "ok" when S embeddings are present; otherwise a deferral reason (embedder unreachable). The
    # recorded classes F/D/C are computed regardless — only the S (computed) rows defer.
    embedder_status: str = "ok"

    @property
    def floor(self) -> float:
        return min(self.grid)

    @property
    def tight(self) -> float:
        return max(self.grid)

    def s_nodes(self) -> set[str]:
        return set(self.s_embeddings)

    def f_nodes(self) -> set[str]:
        return {x for p in self.f_pairs for x in p}

    def c_nodes(self) -> set[str]:
        return {x for p in self.c_pairs for x in p}

    def d_nodes(self) -> set[str]:
        return {x for p in self.d_arcs for x in p} | {x for p in self.d_authored for x in p}


def load_context(
    *, data_dir: Path = DEFAULT_DATA_DIR, repo_root: Path = DEFAULT_REPO_ROOT,
    grid: tuple[float, ...] = DEFAULT_GRID, char_limit: int = 2000, batch: int = 4,
) -> SurveyContext:
    """Assemble the read-only corpus context: embed the C-doc node set eval-side (S), load F/D/C
    from `?mode=ro` connections, normalize S/F/C to docs/** path space, keep D in its own space.
    Reads no store writably and persists nothing."""
    floor = min(grid)
    c_conn = open_causal_edges_ro(data_dir / "causal_edges.sqlite")
    try:
        causal = load_causal_edges(c_conn)
    finally:
        c_conn.close()
    c_ids = sorted({str(e["dst"]) for e in causal if str(e["dst_type"]) == "doc"})

    # id -> docs/** path; drop unresolved from the shared space.
    id2path: dict[str, str] = {}
    unresolved: list[str] = []
    for cid in c_ids:
        path = normalize_c_id(cid, repo_root=repo_root)
        (id2path.__setitem__(cid, path) if path else unresolved.append(cid))

    # C co-production pairs (re_measure projection), re-keyed to path space.
    proven = proven_pairs_from_causal(causal, node_ids=c_ids)
    c_pairs: set[tuple[str, str]] = set()
    for p in proven:
        pa, pb = id2path.get(p.a), id2path.get(p.b)
        if pa and pb and pa != pb:
            c_pairs.add((min(pa, pb), max(pa, pb)))

    # S: embed the resolvable docs eval-side (ephemeral); re-key embeddings to path space. The
    # embedder shares the memory-ceiling'd ollama with the live daemon (bright line 8); under
    # contention the fail-fast embed timeout trips. A trip is NOT a corpus null — it defers the S
    # (computed) rows with a re-entry condition, while F/D/C (recorded, no embedder) still compute.
    s_embeddings: dict[str, list[float]] = {}
    embedder_status = "ok"
    try:
        emb_by_id, _unres_embed = embed_docs(
            c_ids, repo_root=repo_root, char_limit=char_limit, batch=batch)
        for cid, vec in emb_by_id.items():
            path = id2path.get(cid)
            if path is not None:
                s_embeddings[path] = vec
    except Exception as exc:  # noqa: BLE001 — any embedder failure (timeout/URLError/OllamaError)
        embedder_status = (
            f"deferred: eval-side embedder unreachable within the fail-fast timeout "
            f"({type(exc).__name__}: {exc}). The embed model shares the memory-ceiling'd ollama "
            f"with the live daemon (bright line 8) — the survey must not evict/restart it. "
            f"RE-ENTRY: re-run when the daemon is idle (or embed headroom exists). S rows defer; "
            f"F/D/C (recorded) rows are unaffected.")
    s_edges = sim_edges_from_embeddings(
        s_embeddings, node_ids=list(s_embeddings), sigma_floor=floor)

    # F: corpus→corpus citation pairs (already docs/** path space).
    f_conn = _open_ro(data_dir / "reference_edges.sqlite")
    try:
        f_pairs = load_f_pairs(f_conn)
    finally:
        f_conn.close()

    # D: supersession arcs (disjoint vault/catalog space).
    v_conn = _open_ro(data_dir / "versions.sqlite")
    try:
        d_arcs = load_d_arcs(v_conn)
        d_doc_count = len({str(r["doc_id"]) for r in v_conn.execute("SELECT doc_id FROM versions")})
        d_version_count = int(next(iter(v_conn.execute("SELECT count(*) FROM versions")))[0])
    finally:
        v_conn.close()
    a_conn = _open_ro(data_dir / "authored_supersessions.sqlite")
    try:
        d_authored = load_authored_supersessions(a_conn)
    finally:
        a_conn.close()

    return SurveyContext(
        head=git_head(repo_root), grid=grid, repo_root=repo_root,
        s_embeddings=s_embeddings, s_edges=s_edges, f_pairs=f_pairs,
        c_pairs=sorted(c_pairs), c_ids=c_ids, unresolved_c=unresolved,
        d_arcs=d_arcs, d_authored=d_authored,
        d_doc_count=d_doc_count, d_version_count=d_version_count,
        embedder_status=embedder_status,
    )


# ── the battery (each row → one CN-1-indexed Reading) ─────────────────────────────────────────
def m1_overlap_census(ctx: SurveyContext) -> Reading:
    """M1 — per-class population census + pairwise support Jaccard on shared nodes."""
    s, f, c, d = ctx.s_nodes(), ctx.f_nodes(), ctx.c_nodes(), ctx.d_nodes()
    s_available = _s_available(ctx)
    populations: dict[str, dict[str, object]] = {
        "S": {"nodes": len(s), "edges": len(ctx.s_edges), "space": "docs/**",
              "provenance": "computed (cosine, embedder-versioned)",
              **({} if s_available else {"status": _DEFERRED, "reason": ctx.embedder_status})},
        "F": {"nodes": len(f), "edges": len(ctx.f_pairs), "space": "docs/**",
              "provenance": "recorded (reference_edges, commit-keyed)"},
        "C": {"nodes": len(c), "edges": len(ctx.c_pairs), "space": "docs/**",
              "provenance": "recorded+proven (co-production witness)"},
        "D": {"nodes": len(d), "edges": len(ctx.d_arcs) + len(ctx.d_authored),
              "space": "vault/catalog (DISJOINT)", "docs": ctx.d_doc_count,
              "versions": ctx.d_version_count,
              "provenance": "recorded (versions, append-only)"},
    }
    node_sets = {"S": s, "F": f, "C": c, "D": d}
    jaccard = {f"{x}|{y}": round(_jaccard(node_sets[x], node_sets[y]), 6)
               for i, x in enumerate("SFCD") for y in "SFCD"[i + 1:]}
    shared = {f"{x}|{y}": len(node_sets[x] & node_sets[y])
              for i, x in enumerate("SFCD") for y in "SFCD"[i + 1:]}
    idx = _index(ctx, sigma=ctx.floor, node_space="union(S,F,C,D)",
                 n_nodes=len(s | f | c | d),
                 coord_nodes=sorted(s | f | c | d),
                 coord_edges=[(a, b) for a, b, _ in ctx.s_edges]
                 + [*ctx.f_pairs, *ctx.c_pairs, *ctx.d_arcs])
    s_caveat = ("" if s_available else
                " S is DEFERRED (embedder) — every S|* Jaccard below is 0 by S-absence, NOT a "
                "measured zero overlap; F/D/C overlaps are real.")
    return Reading(row="M1", status=_MEASURED if s_available else _DEFERRED, index=idx, value={
        "populations": populations, "node_jaccard": jaccard, "shared_nodes": shared,
        "embedder_status": ctx.embedder_status,
        "note": (s_caveat + " D indexes a DISJOINT node space (vault janus-notes + catalog UUIDs) "
                 "from the docs/** dialogue-artifacts S/F/C share — so D|* overlap is 0, a "
                 "measured fact. Low S/F/C skeleton overlap ⇒ PD-a re-entry cond. 1 (support "
                 "non-degenerate) is NOT met → PD-a parks; bundle-vs-sheaf: low overlap ⇒ sheaf "
                 "is the correct object IF re-entry ever fires (§2.5)."),
    })


def m2_mismatch(ctx: SurveyContext) -> Reading:
    """M2 — S↔C, S↔F mismatch densities + conditional minting + cross-class gradient corr."""
    idx = _index(ctx, sigma=ctx.floor, node_space="docs/**", n_nodes=len(ctx.s_nodes()),
                 coord_nodes=sorted(ctx.s_nodes()),
                 coord_edges=[*ctx.c_pairs, *ctx.f_pairs])
    if not _s_available(ctx):
        return Reading(row="M2", status=_DEFERRED, index=idx, reason=ctx.embedder_status, value={
            "note": ("S↔C / S↔F mismatch densities and conditional minting all need cosines "
                     "(the S instrument) — deferred with M's S rows. F/D/C population structure "
                     "(recorded) is in M1/M3/M6.")})
    emb = ctx.s_embeddings
    floor = ctx.floor

    def cos(a: str, b: str) -> float | None:
        if a not in emb or b not in emb:
            return None
        va, vb = np.asarray(emb[a]), np.asarray(emb[b])
        na, nb = np.linalg.norm(va), np.linalg.norm(vb)
        if na == 0 or nb == 0:
            return None
        return float(va @ vb / (na * nb))

    def mismatch(pairs: Sequence[tuple[str, str]]) -> dict[str, object]:
        cosines = [c for c in (cos(a, b) for a, b in pairs) if c is not None]
        n_scored = len(cosines)
        below = sum(1 for c in cosines if c < floor)
        return {"pairs_total": len(pairs), "pairs_scored_in_S_space": n_scored,
                "below_floor": below,
                "mismatch_density": round(below / n_scored, 6) if n_scored else None,
                "mean_cos": round(float(np.mean(cosines)), 6) if cosines else None}

    sc = mismatch(ctx.c_pairs)
    sf = mismatch(ctx.f_pairs)
    # conditional minting: mean cosine of C/F pairs vs the ambient all-pairs mean.
    node_list = sorted(emb)
    ambient = []
    for i in range(len(node_list)):
        for j in range(i + 1, len(node_list)):
            v = cos(node_list[i], node_list[j])
            if v is not None:
                ambient.append(v)
    ambient_mean = round(float(np.mean(ambient)), 6) if ambient else None
    return Reading(row="M2", status=_MEASURED, index=idx, value={
        "S_C_mismatch": sc, "S_F_mismatch": sf,
        "conditional_minting": {
            "ambient_mean_cos": ambient_mean,
            "C_mean_cos": sc["mean_cos"], "F_mean_cos": sf["mean_cos"],
            "reading": ("C/F minting concentrates on high-cos pairs iff class mean_cos > "
                        "ambient_mean_cos (S seeds C/F, §2.2)."),
        },
        "E_dwS_given_D": {
            "status": _DISJOINT,
            "reason": ("E[Δw_S | D-event] is unmeasurable at doc grain: D (versions) indexes the "
                       "vault/catalog corpus, disjoint from the docs/** S node space — no D-event "
                       "sits at an S endpoint. Expected-null by disjointness, not a zero."),
        },
        "cross_class_gradient_correlation": {
            "status": _DEFERRED,
            "reason": ("PD-a cond. 2 quantitative correlation of per-class Hodge gradient "
                       "potentials is deferred: it consumes the combinatorial split "
                       "quantitatively, which is PD-b's line (§2.1-3, qualitative only)."),
        },
        "gate": ("PD-a re-entry cond. 2 (measured cut-stable nonzero cross-class structure): "
                 "the mismatch densities ARE that structure where nonzero — see values."),
    })


def _triangle_census_class(node_index: Mapping[str, int], pairs: Iterable[tuple[str, str]]) -> int:
    A = _csr_from_pairs(node_index, pairs)
    return int(flag_triangles(A).shape[0])


def m3_triangles(ctx: SurveyContext) -> tuple[Reading, Reading | None]:
    """M3 — per-class triangle census. D MUST be 0 (covering-only integrity). Returns the M3
    reading and, iff a nonzero D-triangle appears, a data-integrity violation reading (§10)."""
    # S at the tight grid point (strict backbone — tractable under hodge's dense guard).
    s_nodes = sorted(ctx.s_nodes())
    s_index = {p: i for i, p in enumerate(s_nodes)}
    s_tight_pairs = [(a, b) for a, b, w in ctx.s_edges if w >= ctx.tight]
    s_available = _s_available(ctx)
    s_tri = _triangle_census_class(s_index, s_tight_pairs) if s_available else None

    f_nodes = sorted(ctx.f_nodes())
    f_index = {p: i for i, p in enumerate(f_nodes)}
    f_tri = _triangle_census_class(f_index, ctx.f_pairs)

    c_nodes = sorted(ctx.c_nodes())
    c_index = {p: i for i, p in enumerate(c_nodes)}
    c_tri = _triangle_census_class(c_index, ctx.c_pairs)

    d_nodes = sorted(ctx.d_nodes())
    d_index = {p: i for i, p in enumerate(d_nodes)}
    d_tri = _triangle_census_class(d_index, [*ctx.d_arcs, *ctx.d_authored])

    idx = _index(ctx, sigma=ctx.tight, node_space="per-class support",
                 n_nodes=len(s_nodes),
                 coord_nodes=s_nodes, coord_edges=s_tight_pairs)
    s_tri_val: dict[str, object] = (
        {"count": s_tri, "sigma": ctx.tight, "status": "empirical (full split, §2.2)"}
        if s_available else {"count": None, "status": _DEFERRED, "reason": ctx.embedder_status})
    reading = Reading(row="M3", status=_MEASURED if d_tri == 0 else _INTEGRITY, index=idx, value={
        "S_triangles": s_tri_val,
        "F_triangles": {"count": f_tri, "status": "empirical (plain q=0 Hodge, §2.2)"},
        "C_triangles": {"count": c_tri, "status": "empirical (near-triangle-free expected, §2.2)"},
        "D_triangles": {"count": d_tri,
                        "status": "MUST be 0 — covering-only supersession (ML owner decision 3)"},
        "gate": "§2.2 Hodge honesty table; the D data-integrity check.",
    })
    violation: Reading | None = None
    if d_tri != 0:
        violation = Reading(row="M3-D-INTEGRITY", status=_INTEGRITY, index=idx, value={
            "d_triangles": d_tri,
            "raise": ("STOP-AND-RAISE (§10): a nonzero D-triangle violates covering-only "
                      "supersession (the Hasse DAG must be triangle-free, ML §2.2 / owner "
                      "decision 3). This is a real corpus defect, not a survey artifact."),
        })
    return reading, violation


def m4_hodge_split(ctx: SurveyContext) -> Reading:
    """M4 — S-field Hodge split (gradient/curl/harmonic energy fractions), read qualitatively."""
    if not _s_available(ctx):
        return Reading(row="M4", status=_DEFERRED,
                       index=_index(ctx, sigma=ctx.tight, node_space="docs/** (S support)",
                                    n_nodes=0, coord_nodes=[], coord_edges=[]),
                       reason=ctx.embedder_status)
    s_nodes = sorted(ctx.s_nodes())
    s_index = {p: i for i, p in enumerate(s_nodes)}
    # tight backbone: the strict σ, sparse enough for the dense-SVD path (hodge guard = 20k edges).
    tight_edges = [(a, b, w) for a, b, w in ctx.s_edges if w >= ctx.tight]
    A = _weighted_csr(s_index, tight_edges)
    n_edges = len(edge_index(A))
    idx = _index(ctx, sigma=ctx.tight, node_space="docs/** (S support)", n_nodes=len(s_nodes),
                 coord_nodes=s_nodes, coord_edges=[(a, b) for a, b, _ in tight_edges])
    if n_edges == 0:
        return Reading(row="M4", status=_EXPECTED_NULL, index=idx,
                       reason="no S edges at the tight σ — no cochain (expected-null).")
    if n_edges > 20_000:
        return Reading(row="M4", status=_BLOCKED, index=idx, value={"n_edges": n_edges},
                       reason=("S support exceeds hodge.py's dense-path guard (20k edges) even at "
                               "the tight σ — a sparse-eigensolver upgrade is the deliberate next "
                               "act (§2.5), never a silent fallback. Blocked, not zero."))
    ei = edge_index(A)
    c = np.zeros(len(ei))
    for (i, j), k in ei.items():
        c[k] = A[i, j]
    parts = hodge_decompose(c, A)
    eg, ec, eh = (float(np.dot(p, p)) for p in (parts.gradient, parts.curl, parts.harmonic))
    total = eg + ec + eh

    def frac(x: float) -> float:
        return round(x / total, 6) if total else 0.0
    return Reading(row="M4", status=_MEASURED, index=idx, value={
        "n_edges": n_edges,
        "energy": {"gradient": round(eg, 6), "curl": round(ec, 6), "harmonic": round(eh, 6)},
        "energy_fraction": {"gradient": frac(eg), "curl": frac(ec), "harmonic": frac(eh)},
        "reading": ("QUALITATIVE only (combinatorial inner product, PD-b parked, §2.1-3). Harmonic "
                    "fraction = the conductivity-deficit signal; curl = circulation no node "
                    "potential explains. A quantitative transport claim would be PD-b's re-entry."),
        "gate": "the deficit reading (§2.1-2); PD-b's potential customer.",
    })


def m5_forman(ctx: SurveyContext) -> Reading:
    """M5 — Forman curvature sign summary on the σ-graph; churn-conditioning where feasible."""
    if not _s_available(ctx):
        return Reading(row="M5", status=_DEFERRED,
                       index=_index(ctx, sigma=ctx.tight, node_space="docs/** (S support)",
                                    n_nodes=0, coord_nodes=[], coord_edges=[]),
                       reason=ctx.embedder_status)
    s_nodes = sorted(ctx.s_nodes())
    s_index = {p: i for i, p in enumerate(s_nodes)}
    tight_pairs = [(a, b) for a, b, w in ctx.s_edges if w >= ctx.tight]
    A = _csr_from_pairs(s_index, tight_pairs)
    idx = _index(ctx, sigma=ctx.tight, node_space="docs/** (S support)", n_nodes=len(s_nodes),
                 coord_nodes=s_nodes, coord_edges=tight_pairs)
    curv = forman(A)
    if not curv:
        return Reading(row="M5", status=_EXPECTED_NULL, index=idx,
                       reason="no S edges at the tight σ — no curvature to read (expected-null).")
    vals = list(curv.values())
    neg = sum(1 for v in vals if v < 0)
    pos = sum(1 for v in vals if v > 0)
    zero = sum(1 for v in vals if v == 0)
    return Reading(row="M5", status=_MEASURED, index=idx, value={
        "edges": len(vals),
        "sign": {"negative_bridge": neg, "positive_clique": pos, "zero": zero},
        "min": round(min(vals), 4), "max": round(max(vals), 4),
        "mean": round(float(np.mean(vals)), 4),
        "churn_conditioning": {
            "status": _DISJOINT,
            "reason": ("Per-region D-minting-rate conditioning is unavailable at doc grain: D "
                       "(versions) is disjoint from the docs/** S node space, so no per-region "
                       "D-rate maps onto S edges. The unconditioned Forman sign summary stands; "
                       "the clique-positive vs hub-negative split is reported above."),
        },
        "gate": "the routing story's sign (§2.4b); PD-c's eventual customer case.",
    })


def m6_thermometer(ctx: SurveyContext) -> Reading:
    """M6 — D-minting-rate thermometer + per-region χ_s (the latter needs a live Spine)."""
    idx = _index(ctx, sigma=ctx.floor, node_space="vault/catalog (D)",
                 n_nodes=ctx.d_doc_count,
                 coord_nodes=sorted(ctx.d_nodes()), coord_edges=ctx.d_arcs)
    return Reading(row="M6", status=_MEASURED, index=idx, value={
        "D_minting": {"docs_with_history": ctx.d_doc_count, "total_versions": ctx.d_version_count,
                      "supersession_arcs": len(ctx.d_arcs),
                      "authored_supersessions": len(ctx.d_authored),
                      "distinct_version_digests": len(ctx.d_nodes())},
        "chi_s": {
            "status": _BLOCKED,
            "reason": ("per-region χ_s needs a live `Spine` over the stratum (conductance.chi_s "
                       "takes a Spine), which is a daemon op not buildable read-only over the "
                       "dialogue-artifacts from a worktree (sigma_star.py: the cut is a mirror-"
                       "stratum Spine op). Blocked; the raw D-minting rate stands as the "
                       "thermometer signal (§2.4c)."),
        },
        "gate": "§2.4c thermometer; CN-4 magnitude calibration (FG-f — parked, magnitudes 0).",
    })


def m7_dead_vs_live(ctx: SurveyContext) -> Reading:
    """M7 — dead-vs-live three-field signature + metric-mismatch field."""
    idx = _index(ctx, sigma=ctx.floor, node_space="docs/**", n_nodes=len(ctx.s_nodes()),
                 coord_nodes=sorted(ctx.s_nodes()), coord_edges=ctx.c_pairs)
    return Reading(row="M7", status=_DEFERRED, index=idx, value={
        "three_field_signature": {
            "D_rate_field": {"status": _DISJOINT,
                             "reason": "D disjoint from docs/** — no D-rate on S nodes."},
            "S_velocity_coherence": {"status": _DEFERRED,
                                     "reason": ("needs two A7-clean cuts (VI-b harmonic-velocity); "
                                                "only one cut is embedded eval-side here.")},
            "CF_density": {"status": _MEASURED,
                           "C_pairs": len(ctx.c_pairs), "F_pairs_docs": len(ctx.f_pairs)},
        },
        "dead_vs_live_classification": {
            "status": _DEFERRED,
            "reason": ("dead-vs-live arc labeling needs the census/dreamer-exhaust finished-arc "
                       "corpus, which barely exists (bp-080 seal). Expected-thin; the phase model "
                       "(§2.4a) parks on it — silence recorded, never narrated as structure."),
        },
        "gate": "the phase model (§2.4a); the horizon prediction's first look — both park on data.",
    })


def m8_sigma_sweep(ctx: SurveyContext) -> Reading:
    """M8 — σ-sweep (oq-0024) + bottleneck-vs-product chain divergence; endorsed-chain scoring."""
    s_nodes = sorted(ctx.s_nodes())
    idx = _index(ctx, sigma=ctx.floor, node_space="docs/** (S)", n_nodes=len(s_nodes),
                 coord_nodes=s_nodes, coord_edges=[(a, b) for a, b, _ in ctx.s_edges])
    if not _s_available(ctx):
        return Reading(row="M8", status=_DEFERRED, index=idx, reason=ctx.embedder_status, value={
            "note": ("the σ-sweep and bottleneck-vs-product divergence run over the S (cosine) MST "
                     "— deferred with M's S rows; oq-0024's owed run re-enters when embeddable.")})
    if len(s_nodes) < 2 or not ctx.s_edges:
        return Reading(row="M8", status=_EXPECTED_NULL, index=idx,
                       reason="fewer than 2 S nodes or no S edges — no σ-sweep (expected-null).")
    # Assemble the S-only composed graph (E_sim), build the MST, run the ratified σ* (bottleneck).
    g = assemble_composed_graph(node_ids=s_nodes, embeddings=ctx.s_embeddings,
                                causal_edges=[], sigma_floor=ctx.floor)
    forest = build_max_spanning_tree(_as_mirror(g))
    readings = pairwise_sigma_star(forest, grid=ctx.grid)
    connected = [r for r in readings if r.sigma_star is not None]
    # σ-sweep: fraction of pairs connected at each grid σ (bottleneck ≥ σ).
    sweep = {float(s): round(sum(1 for r in connected if r.sigma_star is not None
                                 and r.sigma_star >= s - 1e-12) / len(readings), 6)
             for s in ctx.grid} if readings else {}
    # bottleneck-vs-product divergence on a sample: does the max-product (−log w) optimal path's
    # endpoints/route differ from the MST bottleneck chain? (independent eval-side computation —
    # sigma_star is NOT changed; the clock-curvature park honored.)
    divergence = _bottleneck_vs_product(g, ctx.floor, sample=connected[:200])
    return Reading(row="M8", status=_MEASURED, index=idx, value={
        "sigma_sweep": sweep,
        "pairs_total": len(readings), "pairs_connected_at_floor": len(connected),
        "bottleneck_vs_product": divergence,
        "endorsed_chain_scoring": {
            "status": _DEFERRED,
            "reason": ("no endorsed-chain corpus exists (bp-080 seal) — the 'which functional "
                       "predicts endorsed chains better' arm is DEFERRED, recorded as absent (not "
                       "silently dropped, per the M8 falsifier). FG-b default (bottleneck σ*) "
                       "stands until material divergence AND endorsed-chain evidence coincide."),
        },
        "gate": "the functional question (§2.4b); oq-0024's owed σ-sweep.",
    })


def _bottleneck_vs_product(g: object, floor: float, sample: Sequence[object]) -> dict[str, object]:
    """Do bottleneck-optimal (σ*/MST) and max-product (−log w shortest) chains diverge? Product
    path is computed independently over the SAME thresholded S adjacency (Dijkstra on −log w) — no
    change to `sigma_star`. Divergence = the two realizing chains differ for a connected pair."""
    sim = g.sim  # type: ignore[attr-defined]
    nodes = g.nodes  # type: ignore[attr-defined]
    idx_of = {d: i for i, d in enumerate(nodes)}
    n = len(nodes)
    # adjacency lists over edges ≥ floor with weight −log(w).
    adj: list[list[tuple[int, float]]] = [[] for _ in range(n)]
    for i in range(n):
        row = sim[i]
        for j in range(i + 1, n):
            w = float(row[j])
            if w >= floor and w > 0.0:
                cost = -math.log(min(w, 1.0)) + 1e-12
                adj[i].append((j, cost))
                adj[j].append((i, cost))

    def product_path(a: int, b: int) -> tuple[str, ...] | None:
        import heapq
        dist = [math.inf] * n
        prev = [-1] * n
        dist[a] = 0.0
        pq: list[tuple[float, int]] = [(0.0, a)]
        while pq:
            d, u = heapq.heappop(pq)
            if d > dist[u]:
                continue
            if u == b:
                break
            for v, c in adj[u]:
                nd = d + c
                if nd < dist[v]:
                    dist[v] = nd
                    prev[v] = u
                    heapq.heappush(pq, (nd, v))
        if dist[b] == math.inf:
            return None
        path = [b]
        while path[-1] != a:
            path.append(prev[path[-1]])
        return tuple(nodes[k] for k in reversed(path))

    diverged = 0
    compared = 0
    for r in sample:
        chain = r.chain  # type: ignore[attr-defined]
        if len(chain) < 2:
            continue
        a, b = idx_of.get(chain[0]), idx_of.get(chain[-1])
        if a is None or b is None:
            continue
        pp = product_path(a, b)
        if pp is None:
            continue
        compared += 1
        if pp != tuple(chain) and pp != tuple(reversed(chain)):
            diverged += 1
    return {"pairs_compared": compared, "chains_diverged": diverged,
            "divergence_rate": round(diverged / compared, 6) if compared else None,
            "reading": ("chains diverge ⇒ hop-pricing (−log-product) REFINES the bottleneck σ* "
                        "(FG-b re-entry candidate); no divergence ⇒ hop-pricing complements, "
                        "FG-b default stands — either way a RESULT, not a failure.")}


def _weighted_csr(
    node_index: Mapping[str, int], triples: Iterable[tuple[str, str, float]]
) -> sp.csr_matrix:
    n = len(node_index)
    rows: list[int] = []
    cols: list[int] = []
    data: list[float] = []
    for a, b, w in triples:
        ia, ib = node_index.get(a), node_index.get(b)
        if ia is None or ib is None or ia == ib:
            continue
        rows += [ia, ib]
        cols += [ib, ia]
        data += [float(w), float(w)]
    if not rows:
        return sp.csr_matrix((n, n))
    coo = (np.asarray(data, dtype=np.float64),
           (np.asarray(rows, dtype=np.int64), np.asarray(cols, dtype=np.int64)))
    return sp.coo_matrix(coo, shape=(n, n)).tocsr()


def _index(ctx: SurveyContext, *, sigma: float, node_space: str, n_nodes: int,
           coord_nodes: Sequence[str], coord_edges: Iterable[tuple[str, ...]]) -> SurveyIndex:
    return SurveyIndex(head=ctx.head, grid=ctx.grid, sigma=sigma, node_space=node_space,
                       n_nodes=n_nodes, coordinate=_coordinate(coord_nodes, coord_edges))


def run_survey(
    *, data_dir: Path = DEFAULT_DATA_DIR, repo_root: Path = DEFAULT_REPO_ROOT,
    grid: tuple[float, ...] = DEFAULT_GRID, char_limit: int = 2000, batch: int = 4,
    ctx: SurveyContext | None = None,
) -> list[Reading]:
    """Run M1–M8 over the live corpus (read-only) and return the CN-1-indexed readings. M9/M10
    ride along inside M6/M7's population reads where the stores make them free (§2.6). Pass `ctx`
    to run over a prebuilt (e.g. fixture) context without touching live stores."""
    if ctx is None:
        ctx = load_context(data_dir=data_dir, repo_root=repo_root, grid=grid,
                           char_limit=char_limit, batch=batch)
    m3, m3_violation = m3_triangles(ctx)
    readings = [m1_overlap_census(ctx), m2_mismatch(ctx), m3, m4_hodge_split(ctx),
                m5_forman(ctx), m6_thermometer(ctx), m7_dead_vs_live(ctx), m8_sigma_sweep(ctx)]
    if m3_violation is not None:
        readings.append(m3_violation)
    return readings


def main() -> None:
    readings = run_survey()
    print(json.dumps([r.to_dict() for r in readings], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
