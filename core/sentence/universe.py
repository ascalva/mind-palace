"""The stratified universe — the nodes a sentence reads, built per sentence from the strata its
clauses name and bounded by a support (dn-query-sentence-algebra §2.9, 2026-11-04).

The owner's question — "what about the code, the dialogue and the papers?" — is the universe's.
The mirror is a few dozen notes, but the stores hold thousands of code atoms, a hundred thousand
paper chunks, the dialogue, and a citation graph of millions of edges over the repo's docs and
code at every commit. A dense backbone over all of it is impossible (n² weights, n³ for the
kernel), so the universe is not the corpus: it is the **support** of the sentence — the nodes its
clauses can reach — materialized lazily:

* the mirror and the dialogue, as far as the sentence's admitted clauses read them
  (`admitted_strata`): the owner's notes and chat turns by default, every turn when a clause
  reads the dialogue (small; the backbone among them is exact, and an anchor named by title is
  found here). Nothing outside the admitted strata is loaded, so no answer, note or refusal can
  carry a row the grant did not admit;
* curated papers and code: the `support` nearest units to each `near` text and to each anchor,
  by the store's index, the paper or the file their occupancies name as the node;
* reference (the repo's docs and code): the citation graph's nodes within the clause's radius of
  each anchor, at the cut — the `as of` commit, else the view's anchor, else the newest cut the
  store holds — bounded by `support`;
* the causal edges, when the sentence walks `C`: the proven edges of the causal store, each one
  dialogue action's image (a transcript turn → the file or doc it produced, the witness law of
  dn-agent-taxonomy §2.5), within the anchor's radius — the turns as `transcript/<session>/<turn>`
  nodes of the dialogue's transcript stratum, the endpoints as the reference graph's nodes (a
  checkout's or a worktree's path, repo-relative) or the mirror's (a vault path); an endpoint
  outside both, or an artifact id, is named as a node that `read` cannot open, never dropped.
  A reader whose grant names no stratum of the mirror is shown an edge only when it ends at a
  commit or at a file git tracks in this repo at HEAD; any other edge is withheld whole, since
  an endpoint is a path and a path can be a note's (`_Builder._named`, dn-guest-principal §5).

On the support the laws hold exactly: masks, products, thresholds (QSA-1 to QSA-4). What the
support loses is bounded and one-sided: restricting the walk to a subgraph whose complement
absorbs can only raise free-energy distances (RSP-5), so `diffuse` on the support under-estimates
nearness and never invents it — PROVIDED the walk keeps the full graph's degrees, which is why
the universe carries them: the backbone `S` lives within a stratum (notes among notes, papers
among papers, files among files; the citation graph is what crosses strata), the loaded strata's
degrees are exact, a paper's is a census by the index (its nearest papers, truncated at
`support` and said so), and a file's is induced, which the answer names as the one place the
bound does not hold. `reach` is exact within its radius unless the bound truncates, and the
answer says which. `over <strata>` is the mask onto the support's nodes of those strata (QSA-2).
The answer's notes carry the support's census and the cut.
"""

from __future__ import annotations

import os
import unicodedata
from collections import deque
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from core.kernel.clearance import CODE_READ, CURATED_READ, DIALOGUE_READ
from core.kernel.scope import Stratum, StratumScope
from core.query import CURATED_REF, QueryEngine
from core.sentence import ast
from core.sentence.ast import Node, Rel
from core.sentence.automaton import letters
from core.sentence.execute import (
    Relation,
    Universe,
    is_commit_sha,
    membership,
    read_ref,
    tracked_paths,
)
from core.sentence.plan import Plan
from core.sentence.precedents import DEFAULT, Precedents
from core.sentence.trace import Trace
from core.sentence.types import (
    CURATED_NAMES,
    REFERENCE_NAMES,
    TRANSCRIPT_REF,
    AmbiguousSentence,
    IllScopedSentence,
    clauses_of,
    stratum_of_provenance,
)

# ── what the sentence names ────────────────────────────────────────────────────────────────────


@dataclass
class Seeds:
    """The texts, anchors and cut a sentence names, with the strata in force at each."""

    texts: list[tuple[str, frozenset[Stratum]]] = field(default_factory=list)
    anchors: list[tuple[str, int]] = field(default_factory=list)   # (atom, radius in hops)
    cut: str | None = None
    moves: set[Rel] = field(default_factory=set)                   # the letters the verbs walk
    transcript: bool = False      # some clause reads the dialogue's transcript stratum


def seeds_of(term: Node, precedents: Precedents = DEFAULT) -> Seeds:
    """Walk the term as `clauses_of` does: `over` sets the strata, `as of` the cut, and every verb
    with a noun contributes its text or its anchor with the radius its evaluator will walk."""
    seeds = Seeds()
    _collect(term, frozenset(precedents.strata), seeds, precedents)
    return seeds


def _collect(node: Node, strata: frozenset[Stratum], s: Seeds, p: Precedents) -> None:
    if Stratum.DIALOGUE_TRANSCRIPT in StratumScope.of(*strata).strata:
        s.transcript = True
    match node:
        case ast.Near(text=t):
            s.texts.append((t, strata))
        case ast.Diffuse(atom=a, rel=rel):
            s.anchors.append((a, 1))
            s.moves.add(rel)
        case ast.Reach(atom=a, depth=d, rel=rel):
            s.anchors.append((a, p.depth if d is None else d))
            s.moves.add(rel)
        case ast.Relate(atom=a) | ast.Trace(atom=a):
            s.anchors.append((a, 0))
        case ast.Walk(atom=a, to=t, depth=d, path=path):
            s.anchors.append((a, p.walk_depth if d is None else d))
            s.moves |= letters(path)
            if t is not None:
                s.anchors.append((t, 0))
        case ast.Read() | ast.Witness():
            pass
        case ast.Far(field=b) | ast.Top(field=b) | ast.AtLeast(field=b) | ast.Not(region=b):
            _collect(b, strata, s, p)
        case (ast.Minus(left=a, right=b) | ast.And(left=a, right=b) | ast.Or(left=a, right=b)
              | ast.Then(left=a, right=b)):
            _collect(a, strata, s, p)
            _collect(b, strata, s, p)
        case ast.Within(body=b, region=r):
            _collect(b, strata, s, p)
            _collect(r, strata, s, p)
        case ast.Over(body=b, strata=names):
            _collect(b, frozenset(Stratum(n) for n in names), s, p)
        case ast.AsOf(body=b, cut=c):
            s.cut = c
            _collect(b, strata, s, p)
        case ast.Assume(hypothesis=h, body=b):
            for atom in (h.a, h.b):
                s.anchors.append((atom, 0))
            if isinstance(h, ast.EdgeHyp | ast.SeverHyp):
                s.moves.add(h.rel)
            _collect(b, strata, s, p)


def producing_turn(e: Mapping[str, Any]) -> str:
    """The transcript turn that produced a causal edge's action: the utterance just before it.
    The event projector stamps an action with the index the next utterance will take
    (`core/chat_events.py::extract_events`), so the producing turn is that index less one; an
    action before any utterance names the session's first turn."""
    t = int(e["witness_turn"])
    return f"{TRANSCRIPT_REF}{e['session_id']}/{max(t - 1, 0)}"


def _doc_path(doc_id: str) -> str | None:
    """A doc's id as the event projector mints it (`dn-…`, `finding-…`, `bp-…`), resolved to its
    repo-relative file when exactly one file is it; `None` otherwise."""
    from core.kernel.config import REPO_ROOT

    root = Path(REPO_ROOT)
    stem = doc_id.removesuffix(".md")
    if stem.startswith("dn-"):
        hits = [root / "docs" / "design-notes" / f"{stem}.md"]
    elif stem.startswith("finding-"):
        hits = sorted((root / "docs" / "findings").glob(f"{stem}*.md"))
    elif stem.startswith("bp-"):
        hits = sorted((root / "docs" / "build-plans").glob(f"{stem}*/plan.md")) + sorted(
            (root / "docs" / "build-plans").glob(f"{stem}*.md"))
    else:
        return None
    hits = [h for h in hits if h.is_file()]
    return hits[0].relative_to(root).as_posix() if len(hits) == 1 else None


# ── the builder ────────────────────────────────────────────────────────────────────────────────


@dataclass
class _Node:
    ref: str
    stratum: str                  # mirror | dialogue | curated | reference
    title: str
    digest: str
    provenance: str
    vector: np.ndarray | None
    detail: dict[str, Any]


def _unit(v: Sequence[float] | np.ndarray | None) -> np.ndarray | None:
    if v is None:
        return None
    arr = np.asarray(v, dtype=np.float64)
    if arr.size == 0:
        return None
    n = float(np.linalg.norm(arr))
    return np.asarray(arr / n, dtype=np.float64) if n > 0 else None


def _mean_vector(rows: Iterable[Mapping[str, Any]]) -> np.ndarray | None:
    vecs = [np.asarray(r["vector"], dtype=np.float64) for r in rows
            if r.get("vector") is not None and len(r.get("vector") or ()) > 0]
    return _unit(np.mean(vecs, axis=0)) if vecs else None


def _int(x: object) -> int:
    return int(x) if isinstance(x, int | float | str) and str(x) != "" else 0


def _folded(path: Path) -> tuple[str, ...]:
    """A path's components as a file system that ignores letter case and normalisation compares
    them: each one decomposed, case-folded and decomposed again."""
    return tuple(unicodedata.normalize("NFKD", unicodedata.normalize("NFKD", part).casefold())
                 for part in path.parts)


def is_repo_path(atom: str) -> bool:
    """A repo-relative path — the reference graph's node identity: relative, with a directory
    part, never a dialogue or transcript turn or a paper ref."""
    return ("/" in atom
            and not atom.startswith(("/", "dialogue/", TRANSCRIPT_REF, CURATED_REF, "~"))
            and ".." not in atom.split("/"))


def admitted_strata(plan: Plan, precedents: Precedents = DEFAULT) -> frozenset[Stratum]:
    """The strata a plan's clauses read, closed downward: admission checked each against the
    grant, so this is the most the universe may hold (the overlay aside, which is not stored)."""
    out: set[Stratum] = set()
    for c in clauses_of(plan.term, precedents=precedents):
        out |= StratumScope.of(*c.req.sigma.strata).strata
    return frozenset(out - {Stratum.HYPOTHETICAL})


class _Builder:
    def __init__(self, engine: QueryEngine, precedents: Precedents,
                 strata: frozenset[Stratum] | None = None, *, hide_mirror: bool = False) -> None:
        self.e, self.p = engine, precedents
        # what the sentence's admitted clauses read: a node outside it is never loaded, so no
        # answer, note or refusal can carry a row the grant did not admit (None: everything, for
        # a builder driven by hand)
        self.strata = strata
        self.admits = membership(strata) if strata is not None else (lambda label, prov: True)
        # the reader's grant names no stratum of the mirror (the guest's): the note graph is not
        # built, pending items are listed for the dialogue's classes alone, and a causal edge is
        # shown only when its endpoint is a commit or a file git tracks here (`_named`), so a
        # note's path the transcript stratum holds is withheld with its edge however it is spelled
        self.hide_mirror = hide_mirror
        self._named_of: dict[tuple[str, str], bool] = {}     # `_named`, per (dst, dst_type)
        self._citable_of: dict[str, bool] = {}               # `_citable`, per citation neighbour
        self._tracked_paths: frozenset[str] | None = None    # `_tracked`, read once
        self._vault_forms: frozenset[tuple[str, ...]] | None = None   # the vault, folded
        self.witnessed = False      # some clause is a witness (its record is read in `universe`)
        self.nodes: dict[str, _Node] = {}
        self.f_edges: dict[str, set[str]] = {}
        self.c_edges: dict[str, set[str]] = {}
        self.c_ids: set[str] = set()                 # the proven edges wired, by content id
        self.moves: frozenset[Rel] = frozenset()     # the letters the sentence walks
        self._causal_index: tuple[dict[str, list[tuple[str, dict[str, Any]]]],
                                  dict[str, list[tuple[str, dict[str, Any]]]]] | None = None
        self._chat: dict[tuple[str, str], Mapping[str, Any] | None] = {}
        self.transcript = False     # some clause reads the transcript stratum (`Seeds.transcript`)
        self.notes: list[str] = []
        self.view: Any = None
        self.cut: str | None = None
        self.cut_note: str = ""
        self._embeds: dict[str, np.ndarray] = {}
        self.census: dict[str, float] = {}       # a paper's full-backbone degree, by the index
        self._cited_of: dict[str, set[str]] = {}  # the citation graph's neighbours, per node read
        self.pending: list[str] = []      # the nodes landed without a vector yet (two-phase)
        # the nodes that keep no vector at all: the instance embeds nothing, or their source keeps
        # none (dn-palace-lite); ranked by the lexical index as the pending are, and said so
        self.unembedded: list[str] = []

    # stores --------------------------------------------------------------------------------------
    def store(self, name: str) -> Any:
        return self.e._get(name)

    def embed(self, text: str) -> np.ndarray:
        if text not in self._embeds:
            if not self.embeds:
                # the lite profile: no embedder exists, so a text has no vector (dn-palace-lite);
                # the zero vector scores nothing, and the lexical index ranks what a clause reads
                self._embeds[text] = np.zeros(int(self.e.config.embedding.dim))
                return self._embeds[text]
            v = _unit(self.store("embedder").embed_query(text))
            self._embeds[text] = v if v is not None else np.zeros(int(self.e.config.embedding.dim))
        return self._embeds[text]

    @property
    def embeds(self) -> bool:
        """Whether the instance embeds at all (`[embedding] enabled`)."""
        return bool(self.e.config.embedding.enabled)

    def _vectorless(self, ref: str) -> None:
        """Mark a node as one that keeps no vector, ranked by the lexical index."""
        if ref not in self.unembedded:
            self.unembedded.append(ref)

    # nodes ---------------------------------------------------------------------------------------
    def add(self, node: _Node) -> _Node:
        have = self.nodes.get(node.ref)
        if have is None:
            self.nodes[node.ref] = node
            return node
        if have.vector is None and node.vector is not None:
            have.vector = node.vector
        for k, v in node.detail.items():
            have.detail.setdefault(k, v)
        return have

    def find(self, atom: str) -> _Node | None:
        """A node a name picks out: by ref, digest or title."""
        if atom in self.nodes:
            return self.nodes[atom]
        for n in self.nodes.values():
            if atom in (n.digest, n.title):
                return n
        return None

    # the mirror and the dialogue, as far as the sentence reads them ------------------------------
    def load_mirror(self) -> None:
        from core.kernel.provenance import Provenance

        reads_mirror = self.admits("mirror", Provenance.AUTHORED_SOLO.value) or self.admits(
            "dialogue", Provenance.AUTHORED_DIALOGUE.value)
        if reads_mirror and not self.hide_mirror:      # the guest's dialogue loads below
            notes, mat, _ = self.e.note_graph()
            for i, n in enumerate(notes):
                prov = str(n.get("provenance", ""))
                label = stratum_of_provenance(prov) or "mirror"
                if self.admits(label, prov):
                    self.add(_Node(str(n["source_path"]), label, str(n.get("title", "")),
                                   str(n.get("digest", "")), prov,
                                   _unit(mat[i]) if len(mat) else None, {}))
        if not (self.admits("dialogue", Provenance.OBSERVED.value)
                or self.admits("dialogue", Provenance.AUTHORED_DIALOGUE.value)):
            return
        by_src: dict[str, list[Mapping[str, Any]]] = {}
        for r in self.store("vectors").all_rows(clearance=DIALOGUE_READ):
            by_src.setdefault(str(r["source_path"]), []).append(r)
        for src, rows in sorted(by_src.items()):
            prov = str(rows[0].get("provenance", ""))
            if src in self.nodes or not self.admits("dialogue", prov):
                continue
            self.add(_Node(src, "dialogue", str(rows[0].get("title", "")),
                           str(rows[0].get("digest", "")), prov, _mean_vector(rows), {}))

    # the items landed without a vector yet (dn-two-phase-ingestion D2; ING-21) -------------------
    def lexical_index(self) -> Any:
        """The lexical index, or None: an engine without one (a hand-driven builder, an instance
        that embeds synchronously and never built one) has no pending items to rank."""
        try:
            return self.store("lexical")
        except KeyError:
            return None

    def load_pending(self) -> None:
        """Under lazy embedding, the active items of the whole-loaded strata (the mirror, the
        dialogue) whose vectors the drain has not written yet, read from the plane itself: added
        as nodes without a vector, so a structural or lexical clause reads them and a semantic one
        reports them. A node whose plane rows are an older version's is pending too: its vector
        is another text's, and is dropped rather than read. Nothing here runs when the instance
        embeds synchronously, so its universes are what they were."""
        from core.ingest.derive import pending

        if not bool(self.e.config.embedding.lazy) and self.embeds:
            return
        lexical = self.lexical_index()
        if lexical is None:
            return
        try:
            catalog, plane = self.store("catalog"), self.store("vectors")
        except KeyError:
            return
        from core.kernel.provenance import Provenance

        dialogue = (Provenance.AUTHORED_DIALOGUE, Provenance.OBSERVED)
        for e in pending(catalog, plane, lexical=lexical,
                         classes=dialogue if self.hide_mirror else None):
            prov = str(e.provenance)
            label = stratum_of_provenance(prov) or "mirror"
            if label not in ("mirror", "dialogue") or not self.admits(label, prov):
                continue
            if not self.embeds:              # nothing is pending: no vector will ever come
                self.add(_Node(e.source_path, label, e.title, e.digest, prov, None,
                               {"vector": "none: the instance embeds nothing"}))
                self._vectorless(e.source_path)
                continue
            have = self.nodes.get(e.source_path)
            if have is None:
                self.add(_Node(e.source_path, label, e.title, e.digest, prov, None,
                               {"pending": "no vector yet"}))
            else:
                have.vector = None
                have.digest = e.digest
                have.detail["pending"] = "the vector is an older version's"
            self.pending.append(e.source_path)

    def seed_lexical(self, text: str, why: str) -> int:
        """The pending items of the curated stratum a `near` text reaches, by the lexical index
        (the vector index cannot reach them): at most `support`, added without a vector."""
        from core.kernel.provenance import Provenance

        if (not bool(self.e.config.embedding.lazy) and self.embeds) \
                or not self.admits("curated", "curated"):
            return 0
        lexical = self.lexical_index()
        if lexical is None:
            return 0
        try:
            catalog, plane = self.store("catalog"), self.store("vectors")
        except KeyError:
            return 0
        from core.ingest.derive import pending

        waiting = {e.source_path: e for e in pending(catalog, plane, lexical=lexical,
                                                     classes=[Provenance.CURATED])}
        if not waiting:
            return 0
        added = 0
        for hit in lexical.search(text, k=self.p.support, classes=[Provenance.CURATED],
                                  paths=list(waiting)):
            e = waiting[hit.source_path]
            if hit.source_path in self.nodes:
                continue
            if not self.embeds:
                self.add(_Node(e.source_path, "curated", e.title, e.digest, "curated", None,
                               {"vector": "none: the instance embeds nothing"}))
                self._vectorless(e.source_path)
            else:
                self.add(_Node(e.source_path, "curated", e.title, e.digest, "curated", None,
                               {"pending": "no vector yet"}))
                self.pending.append(e.source_path)
            added += 1
        if added:
            why_none = ("the instance embeds nothing" if not self.embeds
                        else "their vectors are not yet derived")
            self.notes.append(f"curated: {added} papers from the lexical index for {why!r} "
                              f"({why_none})")
        return added

    def seed_reference_lexical(self, text: str, why: str) -> int:
        """The reference stratum's items that keep no vector (a repository source's files,
        dn-palace-lite) a `near` text reaches, by the lexical index: the files of its `support`
        best units, added without a vector, ranked by the index and said so. An instance whose
        index holds no such unit (its code, if any, is the embed lane's) adds nothing here."""
        from core.kernel.provenance import Provenance

        if not self.admits("reference", "code"):
            return 0
        lexical = self.lexical_index()
        if lexical is None:
            return 0
        hits = lexical.search(text, k=self.p.support, classes=[Provenance.CODE])
        files: list[str] = []
        for hit in hits:
            if hit.source_path in files:
                continue
            files.append(hit.source_path)
            self.add(_Node(hit.source_path, "reference", hit.title, hit.digest, "code", None,
                           {"chunk": hit.chunk_index, "vector": "none: the source keeps none"}))
            self._vectorless(hit.source_path)
        if hits:
            self.notes.append(f"reference: {len(files)} files from the {len(hits)} best lexical "
                              f"units for {why!r} (the index's top {self.p.support}; the files "
                              "keep no vectors)")
        return len(files)

    def seed_item(self, atom: str) -> None:
        """An anchor that is a landed item of the reference stratum (a repository source's file):
        its node, with the digest and title the catalog holds, and no vector."""
        try:
            entry = self.store("catalog").get(atom)
        except KeyError:                      # an engine without the catalog
            return
        if entry is None or not entry.active or str(entry.provenance) != "code":
            return
        self.add(_Node(atom, "reference", str(entry.title), str(entry.digest), "code", None,
                       {"vector": "none: the source keeps none"}))
        self._vectorless(atom)

    # the indexed strata --------------------------------------------------------------------------
    def seed_curated(self, vec: np.ndarray, why: str) -> int:
        if not self.admits("curated", "curated"):
            return 0
        rows = self.store("curated").search(list(map(float, vec)), k=self.p.support,
                                            clearance=CURATED_READ)
        by_src: dict[str, list[Mapping[str, Any]]] = {}
        for r in rows:
            by_src.setdefault(str(r.get("source_path", "")), []).append(r)
        added = 0
        for src, group in by_src.items():
            if not src:
                continue
            best = min(group, key=lambda r: float(r.get("_distance", 0.0)))
            node = self.add(_Node(src, "curated", str(best.get("title", "")),
                                  str(best.get("digest", "")), "curated", _mean_vector(group),
                                  {"chunk": int(best.get("chunk_index", 0) or 0),
                                   "chunks_hit": len(group)}))
            added += int(node.ref == src)
        if rows:
            self.notes.append(f"curated: {len(by_src)} papers from the {len(rows)} nearest chunks "
                              f"to {why!r} (the index's top {self.p.support})")
        return added

    def seed_code(self, vec: np.ndarray, why: str) -> int:
        from core.stores.memberships import resolve_occupancies

        if not self.admits("reference", "code") or not self.embeds:
            return 0
        rows = self.store("vectors").search(list(map(float, vec)), k=self.p.support,
                                            clearance=CODE_READ)
        resolved = resolve_occupancies(self.store("memberships"), rows)
        paths: dict[str, int] = {}
        for hit in resolved:
            row = hit.row
            raw = row.get("vector")
            vector = _unit(raw) if isinstance(raw, list | tuple | np.ndarray) else None
            places = [(o.path, o.slot, o.slot_line_start, o.slot_line_end) for o in hit.occupancies]
            if not places and row.get("source_path"):
                places = [(str(row["source_path"]), str(row.get("qualname", "")),
                           _int(row.get("line_start")), _int(row.get("line_end")))]
            for path, slot, a, b in places:
                paths[path] = paths.get(path, 0) + 1
                self.add(_Node(path, "reference", path, "", "code", vector,
                               {"qualname": slot, "lines": f"{a}–{b}"}))
        if rows:
            self.notes.append(f"reference: {len(paths)} files from the {len(rows)} nearest code "
                              f"atoms to {why!r} (the index's top {self.p.support})")
        return len(paths)

    def degree_census(self, nodes: list[_Node]) -> None:
        """The full backbone's degree of each curated node: the similarity, at or above σ, to the
        papers the index returns for its vector (`support` chunks), the index's own estimate of
        the paper's neighbourhood. Cached on the engine across sentences; truncation is noted."""
        sigma = float(self.e.config.dreaming.similarity_threshold)
        cache: dict[str, float] = self.e._cache.setdefault("degree_census", {})
        truncated = 0
        for n in nodes:
            if n.ref in cache:
                self.census[n.ref] = cache[n.ref]
                continue
            if n.vector is None:
                continue
            rows = self.store("curated").search(list(map(float, n.vector)), k=self.p.support,
                                                clearance=CURATED_READ)
            by_src: dict[str, list[Mapping[str, Any]]] = {}
            for r in rows:
                by_src.setdefault(str(r.get("source_path", "")), []).append(r)
            degree = 0.0
            for src, group in by_src.items():
                if src == n.ref or not src:
                    continue
                centroid = _mean_vector(group)
                if centroid is None:
                    continue
                cos = float(n.vector @ centroid)
                if cos >= sigma:
                    degree += min(cos, 1.0)
            if len(rows) >= self.p.support and by_src and min(
                    float(r.get("_distance", 0.0)) for r in rows) <= 1 - sigma:
                truncated += 1
            cache[n.ref] = degree
            self.census[n.ref] = degree
        if truncated:
            self.notes.append(f"degrees: {truncated} papers' censuses were cut at the index's "
                              f"top {self.p.support}; their nearness bound is loose by that much")

    # the citation graph at the cut ---------------------------------------------------------------
    def open_view(self, cut: str | None) -> None:
        from core.reference_view import ReferenceView, _resolve_default_commit

        store = self.store("references")
        wanted = cut if cut is not None else _resolve_default_commit(self.e.config)
        if cut is not None and len(cut) < 40:          # a short sha, resolved as git does
            matches = store.commits_like(cut)
            if len(matches) > 1:
                raise AmbiguousSentence(f"as of {cut!r}: the store holds {len(matches)}+ cuts "
                                        f"starting so; write more of the sha")
            if matches:
                wanted = matches[0]
        anchor = wanted
        if not store.for_commit(wanted):
            latest = store.latest_commit()
            if latest is not None and latest != wanted:
                anchor = latest
                self.cut_note = (f"the citation graph is read at {anchor[:7]}, the newest cut "
                                 f"the store holds; it has no edges at {wanted[:7]}")
        self.cut = anchor
        self.view = ReferenceView.over(store, commit=anchor)

    # the citation graph and the causal edges, around an anchor -----------------------------------
    def _roots(self) -> list[Path]:
        """The checkouts a causal endpoint's absolute path may lie under: this one and, when this
        one is a worktree (`<main>/.claude/worktrees/<name>`), the main checkout."""
        from core.kernel.config import REPO_ROOT

        root = Path(REPO_ROOT)
        roots = [root]
        if root.parent.name == "worktrees" and root.parent.parent.name == ".claude":
            roots.append(root.parent.parent.parent)
        return roots

    def _tracked(self) -> frozenset[str]:
        """The paths git tracks in this checkout at HEAD, read once per builder; the empty set
        when git cannot be asked, so nothing is named then."""
        if self._tracked_paths is None:
            from core.kernel.config import REPO_ROOT

            try:
                self._tracked_paths = tracked_paths(Path(REPO_ROOT))
            except Exception:                           # fail closed: no path is tracked
                self._tracked_paths = frozenset()
        return self._tracked_paths

    def _in_vault(self, ref: str) -> bool:
        """Whether a path is the vault or lies under it, in any spelling the file system treats
        as the same file: another letter case, another Unicode normalisation, `..` components, a
        symlink. The components are compared folded (`_folded`), as a prefix, for the path as
        written (`~` expanded), for its normal form and for its resolved form, against the
        configured vault path and its resolved form. A path that cannot be read this way counts
        as inside, so the test errs toward withholding."""
        try:
            if self._vault_forms is None:
                vault = Path(str(self.e.config.ingestion.vault.path)).expanduser()
                self._vault_forms = frozenset({_folded(vault), _folded(vault.resolve())})
            p = Path(ref).expanduser()
            forms = {_folded(p), _folded(Path(os.path.normpath(p))), _folded(p.resolve())}
        except Exception:                               # fail closed: inside the vault
            return True
        return any(f[:len(v)] == v for v in self._vault_forms for f in forms)

    def _named(self, dst: str, dst_type: str) -> bool:
        """Whether a causal edge's endpoint is one a reader whose grant names no stratum of the
        mirror may see named (`hide_mirror`). An allow list, since an endpoint is whatever path or
        id the action log recorded and a note's path has many spellings: a commit's edge is named
        when its endpoint is a hex sha; any other edge only when its endpoint is not in the vault
        (`_in_vault`) and resolves to a repo-relative path git tracks in this checkout at HEAD
        (`_tracked`), from a doc's id (`_doc_path`) or from an absolute path under a checkout of
        this repo (`_endpoint`). A relative path, one under `~`, a URI, a path outside the repo,
        an untracked or deleted file, a doc's id that is not one tracked file and an endpoint of
        an unknown type are not named, nor is one that cannot be judged. An edge that is not named
        is withheld whole, its id with it, as if the store did not hold it: what the reader sees
        does not depend on it (dn-guest-principal §5)."""
        key = (dst, dst_type)
        if key not in self._named_of:
            try:
                self._named_of[key] = self._allowed(dst, dst_type)
            except Exception:                           # fail closed: not named, never raised
                self._named_of[key] = False
        return self._named_of[key]

    def _allowed(self, dst: str, dst_type: str) -> bool:
        """`_named`'s rule for one endpoint, uncached; it may raise, and `_named` then withholds."""
        if dst_type == "commit":
            return is_commit_sha(dst)
        if self._in_vault(dst):
            return False
        rel: str | None = None
        if dst_type == "doc" and "/" not in dst:
            rel = _doc_path(dst)
        elif dst_type in ("file", "doc") and Path(dst).is_absolute():
            node = self._endpoint(dst, dst_type)
            rel = node.ref if node.stratum == "reference" else None
        return rel is not None and rel in self._tracked()

    def _citable(self, ref: str) -> bool:
        """Whether a citation neighbour is one the reader may see named. The citation graph is
        projected from git history, so its refs are repo-relative paths and denote repo files; a
        reader whose grant names no stratum of the mirror (`hide_mirror`) is shown a neighbour
        only when it is spelled as one (not absolute, not under `~`, no URI, no `..` component)
        and lies in the vault under no checkout of this repo. It need not be tracked at HEAD: the
        graph is read at other cuts too."""
        if not self.hide_mirror:
            return True
        if ref not in self._citable_of:
            plain = not (ref.startswith(("/", "~")) or "://" in ref or ".." in ref.split("/"))
            self._citable_of[ref] = plain and not any(
                self._in_vault(str(root / ref)) for root in self._roots())
        return self._citable_of[ref]

    def _endpoint(self, dst: str, dst_type: str) -> _Node:
        """The node a causal endpoint names, not yet added. A path under a checkout of this repo
        (this one, the main one, or one of the main one's worktrees,
        `<main>/.claude/worktrees/<name>/`) is the reference graph's node by its repo-relative
        path; a path under the vault is the mirror's note; a doc's id (`dn-…`, `finding-…`,
        `bp-…`) is its file in the repo when exactly one file is it. Anything else, a commit's
        sha, an artifact's id, a path outside the repo and the vault or under another repo's
        worktree, is named as a node of the transcript's stratum, the action log it came from,
        which `read` cannot open: named, never silently dropped, and never a reference node (the
        endpoint is structural, a path or an id, never content)."""
        kind = "code" if dst.endswith(".py") else "corpus"

        def logged(why: str) -> _Node:
            return _Node(dst, "transcript", dst, "", "observed", None, {"endpoint": why})

        if dst_type == "commit":
            return logged("a commit, not a file")
        if dst_type == "doc" and "/" not in dst:
            rel = _doc_path(dst)
            if rel is None:
                return logged("a doc's id, not a path")
            return _Node(rel, "reference", rel, "", "corpus", None, {"id": dst})
        p = Path(dst)
        if not p.is_absolute():
            return (_Node(dst, "reference", dst, "", kind, None, {}) if is_repo_path(dst)
                    else logged("not a path in the repo"))
        parts = p.parts
        roots = self._roots()
        # a worktree's file, `<x>/.claude/worktrees/<name>/<rel>`: the LAST such segment (this
        # checkout may itself be a worktree, so its own path holds one), and only when `<x>` is a
        # checkout of this repo; the file is this checkout's own when the prefix is this checkout
        marks = [i for i in range(len(parts) - 3)
                 if parts[i] == ".claude" and parts[i + 1] == "worktrees"]
        if marks and Path(*parts[:marks[-1]]) in roots:
            i = marks[-1]
            rel = "/".join(parts[i + 3:])
            own = Path(*parts[:i + 3]) == roots[0]
            return _Node(rel, "reference", rel, "", kind, None,
                         {} if own else {"worktree": parts[i + 2]})
        if not marks:
            for root in roots:
                if root in p.parents:
                    rel = p.relative_to(root).as_posix()
                    return _Node(rel, "reference", rel, "", kind, None, {})
        vault = Path(str(self.e.config.ingestion.vault.path)).expanduser()
        if vault in p.parents or vault.resolve() in p.parents:
            have = self.nodes.get(dst)
            if have is not None:
                return have
            if not self.admits("mirror", ""):
                return logged("a vault note; the sentence does not read the mirror")
            return _Node(dst, "mirror", p.name, "", "", None, {"inactive": "not in the mirror"})
        return logged("outside the repo and the vault")

    def _utterance(self, session: str, turn: str) -> Mapping[str, Any] | None:
        """One turn of the chatlog, read through the dialogue clearance; `None` when absent."""
        key = (session, turn)
        if key not in self._chat:
            row: Mapping[str, Any] | None = None
            if turn.isdigit():
                try:
                    row = self.e._get("chatlog").utterance(session, int(turn),
                                                           clearance=DIALOGUE_READ)
                except KeyError:                           # an engine without the chat store
                    row = None
            self._chat[key] = row
        return self._chat[key]

    def _turn(self, ref: str) -> _Node:
        """A transcript turn's node, `transcript/<session>/<turn>`, titled with its full ref and
        its speaker when the chatlog holds it: structure only, since the turns are not embedded
        (the raw transcript's digest is never carried)."""
        session, _, turn = ref[len(TRANSCRIPT_REF):].rpartition("/")
        row = self._utterance(session, turn)
        speaker = str(row.get("speaker", "")) if row else ""
        title = ref + (f" ({speaker})" if speaker else "")
        detail: dict[str, Any] = {"session": session, "turn": turn}
        if speaker:
            detail["speaker"] = speaker
        return _Node(ref, "transcript", title, "", "observed", None, detail)

    def _causal(self) -> tuple[dict[str, list[tuple[str, dict[str, Any]]]],
                               dict[str, list[tuple[str, dict[str, Any]]]]]:
        """The causal store read whole, once per sentence — one content-free row per proven
        action (a witness, an endpoint, an id) — and indexed in memory by turn (the endpoints a
        turn produced) and by endpoint (the turns that produced it); the support is cut from it.
        For a reader whose grant names no stratum of the mirror only the edges whose endpoint it
        may see named are indexed (`_named`)."""
        if self._causal_index is None:
            by_turn: dict[str, list[tuple[str, dict[str, Any]]]] = {}
            by_end: dict[str, list[tuple[str, dict[str, Any]]]] = {}
            for e in self.store("causal").all_edges():
                if self.hide_mirror and not self._named(str(e["dst"]), str(e["dst_type"])):
                    continue
                tref = producing_turn(e)
                eref = self._endpoint(str(e["dst"]), str(e["dst_type"])).ref
                by_turn.setdefault(tref, []).append((eref, e))
                by_end.setdefault(eref, []).append((tref, e))
            self._causal_index = (by_turn, by_end)
        return self._causal_index

    def _causal_neighbours(self, node: str) -> list[tuple[str, dict[str, Any]]]:
        by_turn, by_end = self._causal()
        return by_turn.get(node, []) if node.startswith(TRANSCRIPT_REF) else by_end.get(node, [])

    def _add_causal(self, e: Mapping[str, Any]) -> None:
        """The C move of one proven edge, turn → endpoint, both nodes present; the endpoint keeps
        the edge's id so `witness` can be asked for it."""
        tref = producing_turn(e)
        eref = self._endpoint(str(e["dst"]), str(e["dst_type"])).ref
        self.c_edges.setdefault(tref, set()).add(eref)
        self.c_ids.add(str(e["edge_id"]))
        self.nodes[eref].detail.setdefault("witness", str(e["edge_id"]))

    def _cited(self, node: str, ahead: Iterable[str] = ()) -> set[str]:
        """The refs `node` cites or is cited by at the cut. A node's edges are fetched with the
        nodes of `ahead` (the BFS frontier still to be expanded) in one statement per 400 refs,
        and kept: the answer for a node is the same set whenever it is asked."""
        if node not in self._cited_of:
            batch = [node, *(n for n in dict.fromkeys(ahead)
                             if n != node and n not in self._cited_of and is_repo_path(n))]
            for n in batch:
                self._cited_of[n] = set()
            for src, dst in self.view.neighbour_pairs(batch):
                if src in batch:
                    self._cited_of[src].add(dst)
                if dst in batch:
                    self._cited_of[dst].add(src)
        return self._cited_of[node]

    def seed_typed(self, atom: str, radius: int, moves: frozenset[Rel]) -> None:
        """The neighbourhood of an anchor over the moves the sentence walks, breadth first within
        `radius` hops and bounded by `support`: `F` by the citation graph at the cut (from a repo
        path's node), `C` by the causal edges (a transcript turn's endpoints; an endpoint's turns).
        The nodes reached are added as they are admitted; a C edge is wired here, the F edges
        among the reference nodes by `wire_reference` after every seed."""
        if atom.startswith(TRANSCRIPT_REF):
            self.add(self._turn(atom))
        elif is_repo_path(atom):
            kind = "code" if atom.endswith(".py") else "corpus"
            self.add(_Node(atom, "reference", atom, "", kind, None, {}))
        seen, frontier, budget = {atom}, deque([(atom, 0)]), self.p.support
        truncated = False
        while frontier:
            node, d = frontier.popleft()
            if d >= radius:
                continue
            nbrs: list[tuple[str, Rel, Mapping[str, Any] | None]] = []
            if Rel.F in moves and is_repo_path(node):
                nbrs += [(t, Rel.F, None) for t in self._cited(
                    node, (n for n, dd in frontier if dd < radius)) if self._citable(t)]
            if Rel.C in moves:
                nbrs += [(other, Rel.C, e) for other, e in self._causal_neighbours(node)]
            for nb, _rel, e in sorted(nbrs, key=lambda x: (x[0], x[1].value)):
                if nb not in seen:
                    if len(seen) >= budget:
                        truncated = True
                        break
                    seen.add(nb)
                    frontier.append((nb, d + 1))
                    if nb.startswith(TRANSCRIPT_REF):
                        self.add(self._turn(nb))
                    elif e is None:
                        self.add(_Node(nb, "reference", nb, "",
                                       "code" if nb.endswith(".py") else "corpus", None, {}))
                    else:
                        self.add(self._endpoint(str(e["dst"]), str(e["dst_type"])))
                if e is not None:
                    self._add_causal(e)
        if truncated:
            self.notes.append(f"support: the neighbourhood of {atom!r} was cut at the support "
                              f"of {budget} nodes; reach past it is not answered")

    def seed_anchor(self, atom: str, radius: int) -> None:
        if atom.startswith(TRANSCRIPT_REF):
            if Rel.C not in self.moves and not self.transcript:
                raise IllScopedSentence(
                    f"{atom!r} is a transcript turn: a sentence reads one by walking C or over "
                    "dialogue_transcript, and this one does neither")
            session, _, turn = atom[len(TRANSCRIPT_REF):].rpartition("/")
            if not session or not turn.isdigit() or turn != str(int(turn)):
                raise LookupError(f"{atom!r} is not a transcript turn's ref: "
                                  "transcript/<session>/<turn>, the turn without leading zeros")
            by_turn, _ = self._causal()
            if self._utterance(session, turn) is None and atom not in by_turn:
                raise LookupError(f"no transcript turn {atom!r}: the chatlog holds no such turn "
                                  "and no causal edge names it")
            self.seed_typed(atom, radius, frozenset(self.moves & {Rel.C, Rel.F}))
            return
        have = self.find(atom)
        if have is not None and not is_repo_path(atom):
            if Rel.C in self.moves:        # a note's causal history: the turns that wrote it
                self.seed_typed(have.ref, radius, frozenset({Rel.C}))
            return
        if atom.startswith(CURATED_REF):
            if not self.admits("curated", "curated"):
                return
            rows = self.store("curated").rows_for_source(atom, clearance=CURATED_READ)
            if not rows:
                return
            node = self.add(_Node(atom, "curated", str(rows[0].get("title", "")),
                                  str(rows[0].get("digest", "")), "curated", _mean_vector(rows),
                                  {"chunks": len(rows)}))
            if radius >= 1 and node.vector is not None:
                self.seed_curated(node.vector, atom)
            return
        if is_repo_path(atom) and self.admits("reference", "code"):
            self.seed_item(atom)
            self.seed_typed(atom, radius, frozenset({Rel.F}) | (self.moves & {Rel.C}))

    def wire_reference(self) -> None:
        """The F edges among the support's nodes at the cut: a reference node's edges in both
        directions, a mirror or dialogue note's outgoing ones. Two reads for the whole support
        (the edges leaving it, the edges entering the reference nodes), not two per node."""
        refs = {n.ref for n in self.nodes.values() if n.stratum == "reference"}
        notes = {n.ref for n in self.nodes.values() if n.stratum in ("mirror", "dialogue")}
        if not refs and not notes:
            return
        for src, dst in self.view.neighbour_pairs(sorted(refs | notes), incoming=False):
            if dst in self.nodes and (src in notes or (src in refs and dst != src)):
                self.f_edges.setdefault(src, set()).add(dst)
        if refs:
            for src, dst in self.view.neighbour_pairs(sorted(refs), outgoing=False):
                if src in self.nodes and src != dst:
                    self.f_edges.setdefault(src, set()).add(dst)

    # the universe --------------------------------------------------------------------------------
    def universe(self) -> Universe:
        from core.origin_view import origin

        order = list(self.nodes.values())
        dim = int(self.e.config.embedding.dim)
        mat = np.zeros((len(order), dim))
        known = np.zeros(len(order), dtype=bool)
        for i, n in enumerate(order):
            if n.vector is not None and n.vector.shape[0] == dim:
                mat[i] = n.vector
                known[i] = True
        sims = mat @ mat.T if len(order) else np.zeros((0, 0))
        sigma = self.e.config.dreaming.similarity_threshold
        weights = np.where(sims >= sigma, np.clip(sims, 0.0, 1.0), 0.0)
        if len(order):
            np.fill_diagonal(weights, 0.0)
            strata = np.array([n.stratum for n in order])
            weights = np.where(strata[:, None] == strata[None, :], weights, 0.0)   # S per stratum
        # the full backbone's degrees (RSP-5): exact for the loaded strata, the census for papers,
        # induced for files — and never below the support's own
        own = weights.sum(axis=1) if len(order) else np.zeros(0)
        degrees = own.copy()
        for i, n in enumerate(order):
            if n.stratum == "curated" and n.ref in self.census:
                degrees[i] = max(self.census[n.ref], own[i])
        if any(n.stratum == "reference" for n in order):
            self.notes.append("degrees: the backbone among files is induced on the support; "
                              "`diffuse S` over reference is not one-sided")
        notes = [{"source_path": n.ref, "title": n.title, "digest": n.digest,
                  "provenance": n.provenance, "stratum": n.stratum, "detail": dict(n.detail)}
                 for n in order]
        # the signed relation edges are among the mirror's notes (QSA-b): read when it is
        relations = ([Relation(e.u, e.v, int(e.sign), e.rel_type, float(e.w))
                      for e in self.store("edges").all()]
                     if self.admits("mirror", "authored-solo") else [])
        engine = self.e
        catalog, versions = self.store("catalog"), self.store("versions")

        def embed(text: str) -> np.ndarray:
            return self.embed(text)

        def history(atom: str) -> list[tuple[str, int, str, str]]:
            doc_id = catalog.doc_id_for(atom) if catalog.get(atom) is not None else atom
            return [(v.doc_id, v.version_seq, v.digest, v.at) for v in versions.history(doc_id)]

        def witness(edge_id: str) -> Mapping[str, object] | None:
            # an edge whose endpoint the reader may not see named is no record to it (`_named`):
            # the answer is `None`, as for an id the store does not hold
            edge = origin(edge_id, causal_edges=self.store("causal"),
                          reference_edges=self.store("references"))
            if edge is not None:
                if self.hide_mirror and not self._named(str(edge.dst), str(edge.dst_type)):
                    return None
                return {k: str(v) for k, v in edge.__dict__.items()}
            row = self.store("causal").edge(edge_id)      # a causal edge's own id: the witness
            if row is not None:
                if self.hide_mirror and not self._named(str(row["dst"]), str(row["dst_type"])):
                    return None
                # the turn that produced it, by its ref; the raw transcript's digest is a
                # raw-store key and never leaves the store
                out = {k: str(v) for k, v in row.items() if k != "witness_digest"}
                out["transcript"] = producing_turn(row)
                return out
            # a landing's receipt names its attestation (dn-ingress D5, ING-6): the record
            # of what landed, its role, its action and the digests it produced. A reader that
            # holds no receipt, one whose grant names no stratum of the mirror, is shown none:
            # a note's landing is attested too
            if self.hide_mirror:
                return None
            try:
                att = self.e._get("attestations").get(edge_id)
            except KeyError:                              # an engine without the store
                att = None
            return None if att is None else {k: str(v) for k, v in att.__dict__.items()}

        def text(ref: str, chunk: int | None, window: int) -> Mapping[str, object] | None:
            return read_ref(engine, ref, chunk, window=window, cut=self.cut)

        census: dict[str, int] = {}
        for n in order:
            census[n.stratum] = census.get(n.stratum, 0) + 1
        support = ", ".join(f"{k} {v}" for k, v in sorted(census.items()))
        missing = [f"the universe is the sentence's support: {len(order)} nodes ({support}); "
                   f"{int(known.sum())} with vectors; the citation graph at cut "
                   f"{(self.cut or '')[:7] or '?'}"]
        if self.cut_note:
            missing.append(self.cut_note)
        missing += self.notes
        if self.c_ids:
            ends = {v for vs in self.c_edges.values() for v in vs}
            missing.append(f"causal: {len(self.c_ids)} proven edges from {len(self.c_edges)} "
                           f"transcript turns to {len(ends)} endpoints, each one L1 record's "
                           "image (the witness law), never inferred")
            unreadable = sum(1 for n in order if "endpoint" in n.detail)
            if unreadable:
                missing.append(f"causal: {unreadable} endpoints are commits, ids, or paths "
                               "outside the repo and the vault: named in the transcript's "
                               "stratum, not readable")
        if self.hide_mirror and (Rel.C in self.moves or self.witnessed):
            # the same words whether or not anything was withheld: a count would tell
            missing.append("withheld: the grant names no stratum of the mirror, so a causal edge "
                           "is shown only when it ends at a commit or at a file git tracks in "
                           "this repo at HEAD; any other edge is not shown, its id with it, and "
                           "a witness answers no landing's attestation")
        missing.append("D moves at the note grain: the version chains are per note (use trace)")
        waiting = frozenset(i for i, n in enumerate(order) if n.ref in set(self.pending))
        unembedded = frozenset(i for i, n in enumerate(order) if n.ref in set(self.unembedded))
        pending = waiting | unembedded
        lexical = self._lexical_scores(order, pending)
        if waiting:
            named = ", ".join(order[i].ref for i in sorted(waiting)[:5])
            more = f" and {len(waiting) - 5} more" if len(waiting) > 5 else ""
            missing.append(
                f"pending: {len(waiting)} items landed without a vector yet (the embed drain "
                f"derives them); a semantic clause ranks them by the lexical index and says so, "
                f"and S has no edge at them: {named}{more}")
        if unembedded:
            whose = ("the instance embeds nothing" if not self.embeds
                     else "their source keeps no vectors")
            missing.append(
                f"no vector: {len(unembedded)} items keep none ({whose}); a semantic clause ranks "
                "them by the lexical index and says so, and S has no edge at them")
        return Universe(notes=notes, vectors=mat, weights=weights,
                        edges={Rel.F: self.f_edges, Rel.D: {}, Rel.C: self.c_edges},
                        relations=relations,
                        embed=embed, history=history, witness=witness, cut=self.cut,
                        missing=tuple(missing), text=text, degrees=degrees,
                        pending=pending, lexical=lexical, unembedded=unembedded)

    def _lexical_scores(self, order: list[_Node],
                        pending: frozenset[int]) -> Callable[[str], np.ndarray] | None:
        """The lexical index's scores of the pending nodes for a text, each path's best unit,
        divided by the best among them so the best scores 1 (a scale of its own, labelled by the
        evaluator); None when nothing is pending or there is no index."""
        from core.kernel.provenance import Provenance

        lexical = self.lexical_index() if pending else None
        if lexical is None:
            return None
        idx = sorted(pending)
        classes = {Provenance(order[i].provenance) for i in idx
                   if order[i].provenance in {p.value for p in Provenance}}
        paths = [order[i].ref for i in idx]

        def scores(text: str) -> np.ndarray:
            out = np.zeros(len(order))
            scored = lexical.scores(text, classes=classes, paths=paths)
            for i in idx:
                out[i] = float(scored.get(order[i].ref, 0.0))
            top = float(out.max()) if len(out) else 0.0
            return out / top if top > 0 else out

        return scores


def build(engine: QueryEngine, plan: Plan, *, precedents: Precedents = DEFAULT,
          trace: Trace | None = None, hide_mirror: bool = False) -> Universe:
    """The universe a plan reads: the mirror and the dialogue, then what the sentence's texts and
    anchors reach in the indexed strata, the citation graph at the cut and, when the sentence
    walks `C`, the causal edges. With a trace, the support's census is noted. `hide_mirror` is for
    a reader whose grant names no stratum of the mirror (`ask_logged` sets it from the grant):
    the note graph is not built, and of what the other stores hold a causal edge is shown only
    when it ends at a commit or at a file git tracks in this repo at HEAD, a citation neighbour
    only when it is a repo-relative path outside the vault."""
    seeds = seeds_of(plan.term, precedents)
    b = _Builder(engine, precedents, admitted_strata(plan, precedents), hide_mirror=hide_mirror)
    b.moves = frozenset(seeds.moves)
    b.transcript = seeds.transcript
    b.witnessed = any(c.verb == "witness" for c in plan.clauses)
    b.load_mirror()
    b.load_pending()
    b.open_view(seeds.cut)
    for text, strata in seeds.texts:
        if strata & CURATED_NAMES:
            b.seed_curated(b.embed(text), text)
            b.seed_lexical(text, text)
        if strata & REFERENCE_NAMES:
            b.seed_code(b.embed(text), text)
            b.seed_reference_lexical(text, text)
    for atom, radius in seeds.anchors:
        b.seed_anchor(atom, radius)
    b.wire_reference()
    b.degree_census([n for n in b.nodes.values() if n.stratum == "curated"])
    u = b.universe()
    if trace is not None:
        census: dict[str, int] = {}
        for n in u.notes:
            name = str(n.get("stratum") or "mirror")
            census[name] = census.get(name, 0) + 1
        edges = int(np.count_nonzero(np.triu(u.weights, 1) > 0))
        trace.note("universe", f"the support: {len(u)} nodes ("
                   + ", ".join(f"{k} {v}" for k, v in sorted(census.items()))
                   + f"); the S backbone among them has {edges} edges"
                   + (f"; the citation graph is read at cut {u.cut[:7]}" if u.cut else "")
                   + (f"; {len(b.c_ids)} causal edges wired" if b.c_ids else ""))
        if u.degrees is not None:
            trace.note("universe", "the walk keeps the graph's degrees on the support: exact for "
                       "the notes and the dialogue, a census for papers, induced for files; a "
                       "support invents no nearness except where a census was cut or a degree "
                       "induced, both named in the notes", "RSP-5")
        for note in u.missing:
            trace.note("universe", note)
    return u
