"""The stratified universe — the nodes a sentence reads, built per sentence from the strata its
clauses name and bounded by a support (dn-query-sentence-algebra §2.9, 2026-11-04).

The owner's question — "what about the code, the dialogue and the papers?" — is the universe's.
The mirror is a few dozen notes, but the stores hold thousands of code atoms, a hundred thousand
paper chunks, the dialogue, and a citation graph of millions of edges over the repo's docs and
code at every commit. A dense backbone over all of it is impossible (n² weights, n³ for the
kernel), so the universe is not the corpus: it is the **support** of the sentence — the nodes its
clauses can reach — materialized lazily:

* the mirror and the dialogue: every note and turn, always (small; the backbone among them is
  exact, and an anchor named by title is found here);
* curated papers and code: the `support` nearest units to each `near` text and to each anchor,
  by the store's index, the paper or the file their occupancies name as the node;
* reference (the repo's docs and code): the citation graph's nodes within the clause's radius of
  each anchor, at the cut — the `as of` commit, else the view's anchor, else the newest cut the
  store holds — bounded by `support`.

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

from collections import deque
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from core.kernel.clearance import CODE_READ, CURATED_READ, DIALOGUE_READ
from core.kernel.scope import Stratum
from core.query import CURATED_REF, QueryEngine
from core.sentence import ast
from core.sentence.ast import Node, Rel
from core.sentence.execute import Relation, Universe, read_ref
from core.sentence.plan import Plan
from core.sentence.precedents import DEFAULT, Precedents
from core.sentence.types import CURATED_NAMES, REFERENCE_NAMES, stratum_of_provenance

# ── what the sentence names ────────────────────────────────────────────────────────────────────


@dataclass
class Seeds:
    """The texts, anchors and cut a sentence names, with the strata in force at each."""

    texts: list[tuple[str, frozenset[Stratum]]] = field(default_factory=list)
    anchors: list[tuple[str, int]] = field(default_factory=list)   # (atom, radius in hops)
    cut: str | None = None


def seeds_of(term: Node, precedents: Precedents = DEFAULT) -> Seeds:
    """Walk the term as `clauses_of` does: `over` sets the strata, `as of` the cut, and every verb
    with a noun contributes its text or its anchor with the radius its evaluator will walk."""
    seeds = Seeds()
    _collect(term, frozenset(precedents.strata), seeds, precedents)
    return seeds


def _collect(node: Node, strata: frozenset[Stratum], s: Seeds, p: Precedents) -> None:
    match node:
        case ast.Near(text=t):
            s.texts.append((t, strata))
        case ast.Diffuse(atom=a):
            s.anchors.append((a, 1))
        case ast.Reach(atom=a, depth=d):
            s.anchors.append((a, p.depth if d is None else d))
        case ast.Relate(atom=a) | ast.Trace(atom=a):
            s.anchors.append((a, 0))
        case ast.Walk(atom=a, to=t, depth=d):
            s.anchors.append((a, p.walk_depth if d is None else d))
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
            _collect(b, strata, s, p)


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


def is_repo_path(atom: str) -> bool:
    """A repo-relative path — the reference graph's node identity: relative, with a directory
    part, never a dialogue turn or a paper ref."""
    return ("/" in atom and not atom.startswith(("/", "dialogue/", CURATED_REF, "~"))
            and ".." not in atom.split("/"))


class _Builder:
    def __init__(self, engine: QueryEngine, precedents: Precedents) -> None:
        self.e, self.p = engine, precedents
        self.nodes: dict[str, _Node] = {}
        self.f_edges: dict[str, set[str]] = {}
        self.notes: list[str] = []
        self.view: Any = None
        self.cut: str | None = None
        self.cut_note: str = ""
        self._embeds: dict[str, np.ndarray] = {}
        self.census: dict[str, float] = {}       # a paper's full-backbone degree, by the index

    # stores --------------------------------------------------------------------------------------
    def store(self, name: str) -> Any:
        return self.e._get(name)

    def embed(self, text: str) -> np.ndarray:
        if text not in self._embeds:
            v = _unit(self.store("embedder").embed_query(text))
            self._embeds[text] = v if v is not None else np.zeros(int(self.e.config.embedding.dim))
        return self._embeds[text]

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

    # the mirror and the dialogue, always ---------------------------------------------------------
    def load_mirror(self) -> None:
        notes, mat, _ = self.e._note_graph()
        for i, n in enumerate(notes):
            prov = str(n.get("provenance", ""))
            self.add(_Node(str(n["source_path"]), stratum_of_provenance(prov) or "mirror",
                           str(n.get("title", "")), str(n.get("digest", "")), prov,
                           _unit(mat[i]) if len(mat) else None, {}))
        by_src: dict[str, list[Mapping[str, Any]]] = {}
        for r in self.store("vectors").all_rows(clearance=DIALOGUE_READ):
            by_src.setdefault(str(r["source_path"]), []).append(r)
        for src, rows in sorted(by_src.items()):
            if src in self.nodes:
                continue
            prov = str(rows[0].get("provenance", ""))
            self.add(_Node(src, "dialogue", str(rows[0].get("title", "")),
                           str(rows[0].get("digest", "")), prov, _mean_vector(rows), {}))

    # the indexed strata --------------------------------------------------------------------------
    def seed_curated(self, vec: np.ndarray, why: str) -> int:
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
        anchor = wanted
        if not store.for_commit(wanted):
            latest = store.latest_commit()
            if latest is not None and latest != wanted:
                anchor = latest
                self.cut_note = (f"the citation graph is read at {anchor[:7]}, the newest cut "
                                 f"the store holds; it has no edges at {wanted[:7]}")
        self.cut = anchor
        self.view = ReferenceView.over(store, commit=anchor)

    def seed_reference_anchor(self, atom: str, radius: int) -> None:
        kind = "code" if atom.endswith(".py") else "corpus"
        self.add(_Node(atom, "reference", atom, "", kind, None, {}))
        seen, frontier, budget = {atom}, deque([(atom, 0)]), self.p.support
        truncated = False
        while frontier:
            node, d = frontier.popleft()
            if d >= radius:
                continue
            neighbours = ({e.target_ref for e in self.view.references_from(node)}
                          | {e.source_ref for e in self.view.references_to(node)})
            for nb in sorted(neighbours):
                if nb in seen:
                    continue
                if len(seen) >= budget:
                    truncated = True
                    break
                seen.add(nb)
                self.add(_Node(nb, "reference", nb, "", "code" if nb.endswith(".py") else "corpus",
                               None, {}))
                frontier.append((nb, d + 1))
        if truncated:
            self.notes.append(f"reference: the neighbourhood of {atom!r} was cut at the support "
                              f"of {budget} nodes; reach past it is not answered")

    def seed_anchor(self, atom: str, radius: int) -> None:
        if self.find(atom) is not None and not is_repo_path(atom):
            return
        if atom.startswith(CURATED_REF):
            rows = self.store("curated").rows_for_source(atom, clearance=CURATED_READ)
            if not rows:
                return
            node = self.add(_Node(atom, "curated", str(rows[0].get("title", "")),
                                  str(rows[0].get("digest", "")), "curated", _mean_vector(rows),
                                  {"chunks": len(rows)}))
            if radius >= 1 and node.vector is not None:
                self.seed_curated(node.vector, atom)
            return
        if is_repo_path(atom):
            self.seed_reference_anchor(atom, radius)

    def wire_reference(self) -> None:
        refs = [n.ref for n in self.nodes.values() if n.stratum == "reference"]
        for ref in refs:
            for e in self.view.references_from(ref):
                if e.target_ref in self.nodes and e.target_ref != ref:
                    self.f_edges.setdefault(ref, set()).add(e.target_ref)
            for e in self.view.references_to(ref):
                if e.source_ref in self.nodes and e.source_ref != ref:
                    self.f_edges.setdefault(e.source_ref, set()).add(ref)
        for n in self.nodes.values():
            if n.stratum in ("mirror", "dialogue"):
                for e in self.view.references_from(n.ref):
                    if e.target_ref in self.nodes:
                        self.f_edges.setdefault(n.ref, set()).add(e.target_ref)

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
        relations = [Relation(e.u, e.v, int(e.sign), e.rel_type, float(e.w))
                     for e in self.store("edges").all()]
        engine = self.e
        catalog, versions = self.store("catalog"), self.store("versions")

        def embed(text: str) -> np.ndarray:
            return self.embed(text)

        def history(atom: str) -> list[tuple[str, int, str, str]]:
            doc_id = catalog.doc_id_for(atom) if catalog.get(atom) is not None else atom
            return [(v.doc_id, v.version_seq, v.digest, v.at) for v in versions.history(doc_id)]

        def witness(edge_id: str) -> Mapping[str, object] | None:
            edge = origin(edge_id, causal_edges=self.store("causal"),
                          reference_edges=self.store("references"))
            return None if edge is None else {k: str(v) for k, v in edge.__dict__.items()}

        def text(ref: str, chunk: int | None, window: int) -> Mapping[str, object] | None:
            return read_ref(engine, ref, chunk, window=window)

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
        missing.append("D and C moves at the note grain: the version chains are per note (use "
                       "trace) and the causal edges key on structural endpoints")
        return Universe(notes=notes, vectors=mat, weights=weights,
                        edges={Rel.F: self.f_edges, Rel.D: {}, Rel.C: {}}, relations=relations,
                        embed=embed, history=history, witness=witness, cut=self.cut,
                        missing=tuple(missing), text=text, degrees=degrees)


def build(engine: QueryEngine, plan: Plan, *, precedents: Precedents = DEFAULT) -> Universe:
    """The universe a plan reads: the mirror and the dialogue, then what the sentence's texts and
    anchors reach in the indexed strata and the citation graph at the cut."""
    seeds = seeds_of(plan.term, precedents)
    b = _Builder(engine, precedents)
    b.load_mirror()
    b.open_view(seeds.cut)
    for text, strata in seeds.texts:
        if strata & CURATED_NAMES:
            b.seed_curated(b.embed(text), text)
        if strata & REFERENCE_NAMES:
            b.seed_code(b.embed(text), text)
    for atom, radius in seeds.anchors:
        b.seed_anchor(atom, radius)
    b.wire_reference()
    b.degree_census([n for n in b.nodes.values() if n.stratum == "curated"])
    return b.universe()
