"""The executor — a plan evaluated against the notes, deterministically, with the overlay for
`assume` (dn-query-sentence-algebra §2.6–§2.7).

A `Universe` is what one evaluation reads: the authored notes with their unit vectors and the
similarity backbone (the σ-graph `QueryEngine.note_graph` builds), the typed edges among them
(citations `F`; `D` and `C` at the note grain are empty in this version and said so), the signed
relation edges, and the readers for the version chain and the witnessing commit. `assume` applies
an `Overlay` to a copy of the universe and evaluates the body there — nothing is written to any
store; the result is a `Hyp` beside the actual value, and the notes name the response class the
assumption falls in (QSA-9: adding weight lowers every effective resistance, removing it raises
every one, a contradiction keeps or breaks the camps).

Sorts evaluate to values: a field is a vector of scores in `[0, 1]` over the notes, a region a set
of note indices, a chain a list of `Chain`s, a witness a record, a text the record at a ref (`read`,
the dereference: a note, a dialogue turn, or a window of a curated paper — the executor holds the
record's stratum to the clause's). Connectives follow the algebra of `core/sentence/algebra.py`,
whose laws the Lean proves.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field, replace
from typing import Any

import numpy as np

from core.kernel.recursion import DEFAULT_GAMMA
from core.kernel.scope import Hyp, Stratum
from core.query import CURATED_REF, Hit, QueryEngine, free_energy_distances
from core.sentence import ast
from core.sentence.algebra import atleast, camps, effective_resistance, far, mask_field, topk
from core.sentence.ast import Direction, Node, Rel
from core.sentence.automaton import Chain, compile_path, product_walk
from core.sentence.plan import Plan
from core.sentence.precedents import DEFAULT, Precedents
from core.sentence.trace import Trace
from core.sentence.types import (
    REFERENCE_NAMES,
    AmbiguousSentence,
    IllScopedSentence,
    Sort,
    read_strata,
    short_names,
)


class UnsupportedSentence(NotImplementedError):
    """Well-typed and admissible, but this executor has no evaluator for it yet; the message says
    what is missing, never an empty answer that reads as "nothing there"."""


@dataclass(frozen=True)
class Relation:
    """A signed relation edge between two notes, by digest (`core/stores/edges.py`)."""

    u: str
    v: str
    sign: int
    rel_type: str
    w: float


@dataclass
class Universe:
    """What one evaluation reads. Build one from a `QueryEngine` (`from_engine`) or by hand."""

    notes: list[dict[str, Any]]
    vectors: np.ndarray
    weights: np.ndarray
    edges: dict[Rel, dict[str, set[str]]]
    relations: list[Relation]
    embed: Callable[[str], np.ndarray]
    history: Callable[[str], list[tuple[str, int, str, str]]]
    witness: Callable[[str], Mapping[str, object] | None]
    cut: str | None = None
    missing: tuple[str, ...] = field(default_factory=tuple)
    # `read`: the record at a ref, `(ref, chunk, window)` → the text with its stratum, or None
    text: Callable[[str, int | None, int], Mapping[str, object] | None] = field(
        default=lambda ref, chunk, window: None)
    # the FULL backbone's degrees of these nodes, where the universe is a support (RSP-5): None
    # when the nodes are the whole graph, so the walk's own degrees are the full ones
    degrees: np.ndarray | None = None

    def __len__(self) -> int:
        return len(self.notes)

    def index_of(self, atom: str) -> int:
        """The node a name picks out: by path, digest or title; refused when none or several —
        a name this universe did not seed is a lookup refusal, never an empty answer."""
        hits = [i for i, n in enumerate(self.notes)
                if atom in (n.get("source_path"), n.get("digest"), n.get("title"))]
        if not hits:
            where = ("a paper is a node once named as an anchor or reached by near … over curated"
                     if atom.startswith(CURATED_REF) else
                     "the universe holds the notes, the dialogue, and what the sentence's texts "
                     "and anchors reach")
            raise LookupError(f"no node of this universe matches {atom!r}; {where}")
        if len(hits) > 1:
            names = ", ".join(repr(self.notes[i]["source_path"]) for i in hits)
            raise AmbiguousSentence(f"{atom!r} names {len(hits)} notes: {names}; use a path")
        return hits[0]

    def path_of(self, i: int) -> str:
        return str(self.notes[i]["source_path"])

    def in_strata(self, names: Iterable[str]) -> frozenset[int]:
        """The nodes `over <strata>` keeps: by the row's provenance class, as the clearances read it
        (`STRATUM_CLASSES`), and the reference graph's nodes under `reference` (QSA-2: a mask)."""
        from core.kernel.clearance import classes_of

        strata = {Stratum(n) for n in names}
        classes = {p.value for p in classes_of(strata)}
        reference = bool(strata & REFERENCE_NAMES)
        return frozenset(
            i for i, n in enumerate(self.notes)
            if str(n.get("provenance", "")) in classes
            or (reference and n.get("stratum") == "reference"))

    def digest_of(self, i: int) -> str:
        return str(self.notes[i].get("digest", ""))

    def typed_graph(self) -> dict[Rel, dict[str, set[str]]]:
        """The moves among the notes: `S` from the backbone, the recorded edges for the rest."""
        paths = [self.path_of(i) for i in range(len(self))]
        s_edges: dict[str, set[str]] = {}
        rows, cols = np.nonzero(self.weights > 0)
        for i, j in zip(rows.tolist(), cols.tolist(), strict=True):
            s_edges.setdefault(paths[i], set()).add(paths[j])
        graph: dict[Rel, dict[str, set[str]]] = {Rel.S: s_edges}
        for rel in (Rel.F, Rel.D, Rel.C):
            graph[rel] = {u: set(vs) for u, vs in self.edges.get(rel, {}).items()}
        return graph

    def relation_matrix(self, rel: Rel) -> np.ndarray:
        """The symmetrized 0/1 adjacency of a recorded relation among the notes."""
        n = len(self)
        at = {self.path_of(i): i for i in range(n)}
        A = np.zeros((n, n))
        for u, vs in self.edges.get(rel, {}).items():
            if u not in at:
                continue
            for v in vs:
                if v in at and at[u] != at[v]:
                    A[at[u], at[v]] = 1.0
                    A[at[v], at[u]] = 1.0
        return A

    @classmethod
    def reader(cls, engine: QueryEngine) -> Universe:
        """The universe a bare `read` needs: no note graph, only the dereference — so reading a
        paper opens the curated store and nothing else, as the retired `read` tool did."""
        dim = int(engine.config.embedding.dim)
        return cls(notes=[], vectors=np.zeros((0, dim)), weights=np.zeros((0, 0)),
                   edges={Rel.F: {}, Rel.D: {}, Rel.C: {}}, relations=[],
                   embed=lambda text: np.zeros(dim), history=lambda atom: [],
                   witness=lambda edge: None,
                   text=lambda ref, chunk, window: read_ref(engine, ref, chunk, window=window))

    @classmethod
    def from_engine(cls, engine: QueryEngine) -> Universe:
        """The live universe: the engine's note graph, the reference edges among the notes at the
        anchor commit, the signed relation edges, the version chains and the C-fiber witness."""
        from core.origin_view import origin
        from core.reference_view import open_reference_view

        notes, mat, weights = engine.note_graph()
        paths = {str(n["source_path"]) for n in notes}
        view = open_reference_view(engine.config)
        f_edges: dict[str, set[str]] = {}
        for p in sorted(paths):
            for e in view.references_from(p):
                if e.target_ref in paths:
                    f_edges.setdefault(p, set()).add(e.target_ref)
        relations = [
            Relation(e.u, e.v, int(e.sign), e.rel_type, float(e.w))
            for e in engine._get("edges").all()
        ]
        embedder = engine._get("embedder")
        catalog = engine._get("catalog")
        versions = engine._get("versions")

        def embed(text: str) -> np.ndarray:
            return np.asarray(embedder.embed_query(text), dtype=np.float64)

        def history(atom: str) -> list[tuple[str, int, str, str]]:
            doc_id = catalog.doc_id_for(atom) if catalog.get(atom) is not None else atom
            return [(v.doc_id, v.version_seq, v.digest, v.at) for v in versions.history(doc_id)]

        def witness(edge_id: str) -> Mapping[str, object] | None:
            edge = origin(edge_id, causal_edges=engine._get("causal"),
                          reference_edges=engine._get("references"))
            return None if edge is None else {k: str(v) for k, v in edge.__dict__.items()}

        def text(ref: str, chunk: int | None, window: int) -> Mapping[str, object] | None:
            return read_ref(engine, ref, chunk, window=window)

        return cls(notes=notes, vectors=mat, weights=weights,
                   edges={Rel.F: f_edges, Rel.D: {}, Rel.C: {}}, relations=relations,
                   embed=embed, history=history, witness=witness, cut=view.commit,
                   missing=("D and C moves at the note grain: the version chains are per note "
                            "(use trace) and the causal edges key on structural endpoints",),
                   text=text)


def _read_repo_file(ref: str) -> Mapping[str, object] | None:
    """A repo-relative path — a node of the reference graph — read from the checkout, inside the
    repo root only: a path that resolves outside it, or to nothing, is `None`."""
    from pathlib import Path

    from core.kernel.config import REPO_ROOT

    root = Path(REPO_ROOT).resolve()
    path = (root / ref).resolve()
    if root not in path.parents or not path.is_file():
        return None
    body = path.read_text(encoding="utf-8", errors="replace")
    return {"ref": ref, "title": ref, "provenance": "code" if ref.endswith(".py") else "corpus",
            "stratum": "reference", "text": body}


def read_ref(engine: QueryEngine, ref: str, chunk: int | None, *,
             window: int) -> Mapping[str, object] | None:
    """The record at a ref: a curated paper's window of `window` chunks around `chunk` (from its
    start when absent), or the full text of an active note or dialogue turn — read from the vault
    file when the ref is a path under it, else from the raw store. The stratum rides with the
    record for the executor's scope check. `None` when nothing active bears the ref."""
    from pathlib import Path

    from core.kernel.clearance import CURATED_READ
    from core.kernel.provenance import Provenance
    from core.kernel.stores.rawstore import RawStore
    from core.query import _STRATUM_OF
    from core.stores.catalog import VaultCatalog

    cfg = engine.config
    if ref.startswith(CURATED_REF):
        rows = sorted(engine._get("curated").rows_for_source(ref, clearance=CURATED_READ),
                      key=lambda r: int(r.get("chunk_index", 0) or 0))
        if not rows:
            return None
        start = 0 if chunk is None else max(0, int(chunk) - 2)
        picked = rows[start:start + window]
        return {"ref": ref, "title": rows[0].get("title", ""), "provenance": "curated",
                "stratum": "curated", "chunks": f"{start}–{start + len(picked) - 1} of {len(rows)}",
                "text": "\n".join(str(r.get("text", "")) for r in picked)}
    if "/" in ref and not ref.startswith(("/", "~", "dialogue/")):
        return _read_repo_file(ref)
    entry = VaultCatalog(cfg.paths.vault_catalog).get(ref)
    if entry is None or not entry.active:
        return None
    vault = Path(cfg.ingestion.vault.path).resolve()
    path = Path(ref)
    if path.is_absolute() and vault in path.resolve().parents and path.exists():
        body = path.read_text(encoding="utf-8", errors="replace")
    else:
        body = RawStore(cfg.paths.raw_store).get(entry.digest).decode("utf-8", errors="replace")
    try:
        stratum = _STRATUM_OF.get(Provenance(entry.provenance), "")
    except ValueError:
        stratum = ""
    return {"ref": ref, "title": entry.title, "provenance": entry.provenance, "stratum": stratum,
            "text": body}


# ── values ─────────────────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class FieldV:
    scores: np.ndarray


@dataclass(frozen=True)
class RegionV:
    members: frozenset[int]
    detail: Mapping[int, Mapping[str, object]] = field(default_factory=dict)


@dataclass(frozen=True)
class ChainsV:
    chains: tuple[Chain, ...]


@dataclass(frozen=True)
class WitnessV:
    record: Mapping[str, object] | None


@dataclass(frozen=True)
class TextV:
    """The record `read` returns: the text at a ref with its title, provenance and stratum."""

    record: Mapping[str, object]


@dataclass(frozen=True)
class HypV:
    """A value under assumptions, beside the actual one, with the response read off."""

    actual: Value
    assumed: Value
    assumptions: tuple[str, ...]
    notes: tuple[str, ...]


Value = FieldV | RegionV | ChainsV | WitnessV | TextV | HypV


# ── the overlay ────────────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Overlay:
    """A hypothesis as a perturbation of the universe: backbone weights, citation edges, a
    contradiction among the relations. Applied to a copy; stores are never written."""

    s_edges: tuple[tuple[int, int, float], ...] = ()
    f_add: tuple[tuple[str, str], ...] = ()
    f_sever: tuple[tuple[str, str], ...] = ()
    contradictions: tuple[tuple[str, str], ...] = ()

    @classmethod
    def of(cls, h: ast.Hypothesis, u: Universe) -> Overlay:
        a, b = u.index_of(h.a), u.index_of(h.b)
        if isinstance(h, ast.ContradictHyp):
            return cls(contradictions=((u.digest_of(a), u.digest_of(b)),))
        rel = h.rel
        if rel is Rel.S:
            if isinstance(h, ast.SeverHyp):
                return cls(s_edges=((a, b, -float(u.weights[a, b])),))
            return cls(s_edges=((a, b, h.weight),))
        if rel is Rel.F:
            pair = (u.path_of(a), u.path_of(b))
            if isinstance(h, ast.SeverHyp) or h.weight < 0:
                return cls(f_sever=(pair,))
            return cls(f_add=(pair,))
        raise UnsupportedSentence(f"assume: {rel.value} edges are not in this universe at the note "
                                  f"grain; assume S or F edges, or contradict")

    def apply(self, u: Universe) -> Universe:
        weights = u.weights.copy()
        degrees = None if u.degrees is None else u.degrees.copy()
        for i, j, delta in self.s_edges:
            before = float(weights[i, j])
            weights[i, j] = weights[j, i] = float(np.clip(before + delta, 0.0, 1.0))
            if degrees is not None:      # the graph's degrees move with the edge (RSP-5 holds)
                moved = float(weights[i, j]) - before
                degrees[i] += moved
                degrees[j] += moved
        f_edges = {k: set(v) for k, v in u.edges.get(Rel.F, {}).items()}
        for a, b in self.f_add:
            f_edges.setdefault(a, set()).add(b)
        for a, b in self.f_sever:
            f_edges.get(a, set()).discard(b)
            f_edges.get(b, set()).discard(a)
        relations = list(u.relations) + [
            Relation(a, b, -1, "contradicts", 1.0) for a, b in self.contradictions]
        edges = dict(u.edges)
        edges[Rel.F] = f_edges
        return replace(u, weights=weights, edges=edges, relations=relations, degrees=degrees)

    def describe_response(self, u: Universe) -> list[str]:
        """The response class (QSA-9), stated before anything is computed."""
        notes: list[str] = []
        for _i, _j, delta in self.s_edges:
            if delta > 0:
                notes.append("adds weight on the backbone: every effective resistance falls or "
                             "holds (CND-2); diffusion and reach can only grow")
            elif delta < 0:
                notes.append("removes weight from the backbone: every effective resistance along "
                             "paths through the edge rises or holds (CND-2, backwards)")
        if self.f_add:
            notes.append("adds a citation: reach and the admissible chains over F can only grow "
                         "(QSA-7)")
        if self.f_sever:
            notes.append("severs a citation: reach and the chains over F can only shrink")
        if self.contradictions:
            before = _balanced(u.relations)
            after = _balanced(self.apply(u).relations)
            notes.append("a contradiction: a negative relation edge along e_u + e_v; the camps "
                         + ("still hold" if after else "are broken: the signed relation graph is "
                            "frustrated and its zero mode is lifted (LAP-5, LAP-6)")
                         + ("" if before else " (it was frustrated already)"))
        return notes


def _balanced(relations: list[Relation]) -> bool:
    """Whether the signed relation graph has consistent camps (the `camps` test on its matrix)."""
    nodes = sorted({r.u for r in relations} | {r.v for r in relations})
    if not nodes:
        return True
    at = {d: i for i, d in enumerate(nodes)}
    signs: dict[tuple[int, int], int] = {}
    for r in relations:
        if r.u == r.v or r.sign == 0:
            continue
        pair = (min(at[r.u], at[r.v]), max(at[r.u], at[r.v]))
        if signs.setdefault(pair, r.sign) != r.sign:
            return False                     # support and contradiction on one pair: frustrated
    A = np.zeros((len(nodes), len(nodes)))
    for (i, j), sign in signs.items():
        A[i, j] = A[j, i] = float(sign)
    return camps(A) is not None


# ── evaluation ─────────────────────────────────────────────────────────────────────────────────


class Evaluator:
    """Evaluates a normalized term against a universe."""

    def __init__(self, universe: Universe, precedents: Precedents = DEFAULT,
                 trace: Trace | None = None) -> None:
        self.u = universe
        self.p = precedents
        self.t = trace
        # one walk per (relation, β) per evaluation: a sentence that diffuses from two anchors, or
        # `and`s two diffusions, solves `(I − W_β)⁻¹` once
        self._walks: dict[tuple[Rel, float], np.ndarray] = {}

    # the proof of work ------------------------------------------------------------------------
    def _note(self, what: str, law: str = "") -> None:
        if self.t is not None:
            self.t.note("eval", what, law)

    def _best(self, scores: np.ndarray, n: int = 3) -> str:
        order = [int(j) for j in np.argsort(-scores, kind="stable") if scores[j] > 0][:n]
        return ", ".join(f"{self.u.path_of(j)} {scores[j]:.4f}" for j in order) or "none"

    def _size(self, v: Value) -> str:
        if isinstance(v, FieldV):
            return f"{int(np.count_nonzero(v.scores > 0))} positive"
        if isinstance(v, RegionV):
            return f"{len(v.members)} members"
        if isinstance(v, ChainsV):
            return f"{len(v.chains)} chains"
        return type(v).__name__

    def eval(self, node: Node) -> Value:
        match node:
            case ast.Near(text=text):
                v = self.u.embed(text)
                v = v / (np.linalg.norm(v) or 1.0)
                scores = np.clip(self.u.vectors @ v, 0.0, 1.0)
                self._note(f"near {text!r}: the kernel column s = clip(V·q̂, 0, 1) over "
                           f"{len(self.u)} nodes; {int(np.count_nonzero(scores > 0))} positive; "
                           f"best: {self._best(scores)}", "QSA-3")
                return FieldV(scores)
            case ast.Diffuse(rel=rel, atom=atom, beta=beta):
                return self._diffuse(rel, atom, beta)
            case ast.Far(field=f):
                self._note("far: 1 − f, the bounded reversal of the field")
                return FieldV(far(self._field(f)))
            case ast.Reach(rel=rel, atom=atom, depth=depth, direction=direction):
                return self._reach(rel, atom, depth, direction)
            case ast.Relate(atom=atom):
                return self._relate(atom)
            case ast.Top(k=k, field=f):
                scores = self._field(f)
                members = frozenset(i for i in topk(scores, k) if scores[i] > 0)
                positive = int(np.count_nonzero(scores > 0))
                cut = min((float(scores[i]) for i in members), default=0.0)
                self._note(f"top {k}: {len(members)} kept of {positive} positive scores, ties "
                           f"kept; the cut is {cut:.4f}", "QSA-4")
                return RegionV(members,
                               {i: {"score": round(float(scores[i]), 4)} for i in range(len(scores))
                                if scores[i] > 0})
            case ast.AtLeast(t=t, field=f):
                scores = self._field(f)
                members = atleast(scores, t)
                self._note(f"atleast {t:g}: {len(members)} of {len(scores)} scores reach the "
                           "threshold", "QSA-4")
                return RegionV(members,
                               {i: {"score": round(float(scores[i]), 4)}
                                for i in range(len(scores))})
            case ast.Not(region=r):
                region = self._region(r)
                self._note(f"not: the complement, {len(self.u) - len(region)} of {len(self.u)} "
                           "nodes")
                return RegionV(frozenset(range(len(self.u))) - region)
            case ast.Minus(left=a, right=b):
                left, right = self._region(a), self._region(b)
                self._note(f"minus: {len(left)} members less {len(left & right)} shared → "
                           f"{len(left - right)}")
                return RegionV(left - right)
            case ast.And(left=a, right=b):
                return self._and(self.eval(a), self.eval(b))
            case ast.Or(left=a, right=b):
                return self._or(self.eval(a), self.eval(b))
            case ast.Then(left=a, right=b):
                region = self._region(a)
                val = self.eval(b)
                out = self._mask(val, region)
                self._note(f"then: the right side masked to the left's region of {len(region)}: "
                           f"{self._size(val)} → {self._size(out)}", "QSA-2")
                return out
            case ast.Within(body=b, region=r):
                region = self._region(r)
                val = self.eval(b)
                out = self._mask(val, region)
                self._note(f"within: masked to a region of {len(region)} nodes: "
                           f"{self._size(val)} → {self._size(out)}", "QSA-2")
                return out
            case ast.Over(body=b, strata=strata):
                val = self.eval(b)
                if isinstance(val, FieldV | RegionV):
                    region = self.u.in_strata(strata)
                    out = self._mask(val, region)
                    self._note(f"over {' '.join(strata)}: masked to the strata's {len(region)} "
                               f"nodes: {self._size(val)} → {self._size(out)}", "QSA-2, QSA-10")
                    return out
                return val
            case ast.AsOf(body=b, cut=cut):
                if self.u.cut is None or not self.u.cut.startswith(cut):
                    at = "no cut" if self.u.cut is None else f"cut {self.u.cut[:7]!r}"
                    raise UnsupportedSentence(
                        f"as of {cut!r}: this universe is read at {at}; the store holds no edges "
                        f"at that cut, and the notes have no snapshot store")
                self._note(f"as of {cut!r}: the universe is read at cut {self.u.cut[:7]}")
                return self.eval(b)
            case ast.Trace(atom=atom, direction=direction):
                return self._trace(atom, direction)
            case ast.Walk(atom=atom, path=path, to=to, depth=depth):
                return self._walk(atom, path, to, depth)
            case ast.Witness(edge=edge):
                record = self.u.witness(edge)
                found = "the minting commit found" if record else "no record"
                self._note(f"witness {edge!r}: {found}")
                return WitnessV(record)
            case ast.Read(atom=atom, chunk=chunk):
                return self._read(atom, chunk)
            case ast.Assume(hypothesis=h, body=b):
                overlay = Overlay.of(h, self.u)
                self._note_assume(h, overlay)
                self._note("— under the assumption:")
                assumed = Evaluator(overlay.apply(self.u), self.p, self.t).eval(b)
                self._note("— and without it:")
                actual = self.eval(b)
                notes = (tuple(overlay.describe_response(self.u))
                         + tuple(_response(actual, assumed, self.u)))
                return HypV(actual, assumed, (ast.describe(h),), notes)
        raise UnsupportedSentence(f"no evaluator for {node!r}")  # pragma: no cover

    def _note_assume(self, h: ast.Hypothesis, overlay: Overlay) -> None:
        """The hypothetical's arithmetic: the rank-one update (QSA-9) and, for a backbone edge,
        its sever horizon `w·R_eff` (SEV-3 to SEV-5) — one at a bridge, where the response is
        singular."""
        if self.t is None:
            return
        for i, j, delta in overlay.s_edges:
            w = float(self.u.weights[i, j])
            after = float(np.clip(w + delta, 0.0, 1.0))
            sign = "+" if delta >= 0 else "−"
            self._note(f"assume {ast.describe(h)}: a rank-one update of the backbone's Laplacian, "
                       f"L ↦ L {sign} {abs(delta):g}·(e_u − e_v)(e_u − e_v)ᵀ; w_uv {w:.4f} → "
                       f"{after:.4f}", "QSA-9")
            if w > 0:
                wr = w * effective_resistance(self.u.weights, i, j)
                if wr >= 1 - 1e-6:
                    where = ("= 1: the edge is a bridge, severing it disconnects, and the "
                             "response is singular")
                else:
                    where = (f"< 1: the response is regular, the Sherman–Morrison denominator "
                             f"1 − w·R_eff = {1 - wr:.4f}")
                self._note(f"the sever horizon: w·R_eff(u, v) = {wr:.4f} {where}",
                           "SEV-3, SEV-4, SEV-5")
        for a, b in overlay.f_add:
            self._note(f"assume a citation {a!r} → {b!r}: reach and the chains over F can only "
                       "grow", "QSA-7")
        for a, b in overlay.f_sever:
            self._note(f"assume the citation {a!r} → {b!r} severed: reach and the chains over F "
                       "can only shrink", "QSA-7")
        for a, b in overlay.contradictions:
            self._note(f"assume a contradiction between {a[:8]} and {b[:8]}: a negative relation "
                       "edge along e_u + e_v; the signed Laplacian's zero mode lifts iff the "
                       "camps break", "LAP-5, LAP-6, QSA-9")

    # ── helpers ────────────────────────────────────────────────────────────────────────────────

    def _read(self, atom: str, chunk: int | None) -> TextV:
        """The dereference, with the record's stratum held to the clause's: a paper ref reads the
        curated stratum, any other ref the mirror or the dialogue — whatever the catalog says the
        record is, it must be one of those, or the read is refused as ill-scoped."""
        rec = self.u.text(atom, chunk, self.p.read_window)
        if rec is None:
            raise LookupError(f"read: no active note, dialogue turn, repo file or paper {atom!r}")
        self._note(f"read {atom!r}: the record in stratum {rec.get('stratum')!r}"
                   + (f", chunks {rec['chunks']}" if "chunks" in rec else ""))
        allowed = short_names(read_strata(atom))
        if str(rec.get("stratum", "")) not in allowed:
            raise IllScopedSentence(
                f"read {atom!r}: the record is in stratum {rec.get('stratum')!r}, outside the "
                f"clause's {sorted(allowed)}")
        return TextV(rec)
    def _field(self, node: Node) -> np.ndarray:
        v = self.eval(node)
        if isinstance(v, FieldV):
            return v.scores
        if isinstance(v, RegionV):
            return mask_field(np.ones(len(self.u)), v.members)
        raise UnsupportedSentence(f"a field was needed, got {type(v).__name__}")

    def _region(self, node: Node) -> frozenset[int]:
        v = self.eval(node)
        if isinstance(v, RegionV):
            return v.members
        raise UnsupportedSentence(f"a region was needed, got {type(v).__name__}")

    def _mask(self, v: Value, region: frozenset[int]) -> Value:
        if isinstance(v, FieldV):
            return FieldV(mask_field(v.scores, region))
        if isinstance(v, RegionV):
            return RegionV(v.members & region, v.detail)
        if isinstance(v, ChainsV):
            paths = {self.u.path_of(i) for i in region}
            return ChainsV(tuple(c for c in v.chains if c.end in paths))
        raise UnsupportedSentence(f"within: cannot restrict a {type(v).__name__}")

    def _and(self, a: Value, b: Value) -> Value:
        if isinstance(a, FieldV) and isinstance(b, FieldV):
            product = a.scores * b.scores                         # the Schur product, QSA-1
            if self.t is not None:
                order = [int(j) for j in np.argsort(-product, kind="stable") if product[j] > 0][:3]
                factors = ", ".join(f"{self.u.path_of(j)} {a.scores[j]:.3f}×{b.scores[j]:.3f}="
                                    f"{product[j]:.4f}" for j in order) or "none"
                self._note(f"and: the Schur product f ⊙ g; {self._size(a)} ⊙ {self._size(b)} → "
                           f"{int(np.count_nonzero(product > 0))} positive; best: {factors}",
                           "QSA-1, QSA-3")
            return FieldV(product)
        if isinstance(a, RegionV) and isinstance(b, RegionV):
            self._note(f"and: the regions met, {len(a.members)} ∩ {len(b.members)} = "
                       f"{len(a.members & b.members)}", "QSA-2")
            return RegionV(a.members & b.members, {**dict(b.detail), **dict(a.detail)})
        if isinstance(a, FieldV) and isinstance(b, RegionV):
            out = self._mask(a, b.members)
            self._note(f"and: the field masked to the region of {len(b.members)}: "
                       f"{self._size(a)} → {self._size(out)}", "QSA-2")
            return out
        if isinstance(a, RegionV) and isinstance(b, FieldV):
            out = self._mask(b, a.members)
            self._note(f"and: the field masked to the region of {len(a.members)}: "
                       f"{self._size(b)} → {self._size(out)}", "QSA-2")
            return out
        raise UnsupportedSentence("and: fields and regions only")

    def _or(self, a: Value, b: Value) -> Value:
        if isinstance(a, FieldV) and isinstance(b, FieldV):
            mixed = (a.scores + b.scores) / 2.0                    # the convex mixture
            self._note(f"or: the convex mixture (f + g)/2; {self._size(a)}, {self._size(b)} → "
                       f"{int(np.count_nonzero(mixed > 0))} positive", "QSA-1")
            return FieldV(mixed)
        if isinstance(a, RegionV) and isinstance(b, RegionV):
            self._note(f"or: the regions joined, {len(a.members)} ∪ {len(b.members)} = "
                       f"{len(a.members | b.members)}")
            return RegionV(a.members | b.members, {**dict(a.detail), **dict(b.detail)})
        raise UnsupportedSentence("or: two fields or two regions")

    def _diffuse(self, rel: Rel, atom: str, beta: float | None) -> FieldV:
        i = self.u.index_of(atom)
        if rel is Rel.S:
            W = self.u.weights
        elif rel is Rel.F:
            W = self.u.relation_matrix(Rel.F)
        else:
            raise UnsupportedSentence(f"diffuse {rel.value}: no weights at the note grain")
        if not np.any(W > 0):
            self._note(f"diffuse {rel.value} from {atom!r}: no {rel.value} edges in this "
                       "universe; the field is zero")
            return FieldV(np.zeros(len(self.u)))
        degrees = self.u.degrees if rel is Rel.S else None   # the support's walk keeps the
        b = beta if beta is not None else self.p.beta                                     # graph's
        if (rel, b) not in self._walks:
            self._walks[(rel, b)] = free_energy_distances(W, beta=b, degrees=degrees)
        dist = self._walks[(rel, b)][i]
        scores = np.where(np.isfinite(dist), np.exp(-dist), 0.0)
        scores[i] = 0.0                                  # a note is not retrieved from itself
        scores = np.clip(scores, 0.0, 1.0)
        if self.t is not None:
            m = int(np.count_nonzero(np.triu(W, 1) > 0))
            reached = int(np.count_nonzero(np.isfinite(dist))) - 1
            kept = (" with the full graph's degrees on this support, so the walk never invents "
                    "nearness" if degrees is not None else "")
            self._note(f"diffuse {rel.value} from {atom!r}: the killed walk W_β = z·D⁻¹W∘W^β on "
                       f"{len(self.u)} nodes and {m} edges, β = {b:g}, z = γ = {DEFAULT_GAMMA:g}"
                       f"{kept}; Z = (I − W_β)⁻¹, φ_aj = −log(z_aj / z_jj)/β, score e^{{−φ}}; "
                       f"{reached} nodes reachable; best: {self._best(scores)}",
                       "RSP-1, RSP-4" + (", RSP-5" if degrees is not None else ""))
        return FieldV(scores)

    def _neighbours(self, rel: Rel, direction: Direction) -> dict[str, set[str]]:
        graph = self.u.typed_graph()
        fwd = graph.get(rel, {})
        if rel is Rel.S or direction is Direction.FORWARD:
            return fwd
        back: dict[str, set[str]] = {}
        for a, bs in fwd.items():
            for b in bs:
                back.setdefault(b, set()).add(a)
        if direction is Direction.BACK:
            return back
        both = {a: set(bs) for a, bs in fwd.items()}
        for a, bs in back.items():
            both.setdefault(a, set()).update(bs)
        return both

    def _reach(self, rel: Rel, atom: str, depth: int | None, direction: Direction) -> RegionV:
        start = self.u.path_of(self.u.index_of(atom))
        at = {self.u.path_of(i): i for i in range(len(self.u))}
        nbrs = self._neighbours(rel, direction)
        hops = depth if depth is not None else self.p.depth
        seen = {start: 0}
        frontier = [start]
        frontiers: list[int] = []
        for h in range(1, hops + 1):
            nxt: list[str] = []
            for u in frontier:
                for v in sorted(nbrs.get(u, ())):
                    if v not in seen:
                        seen[v] = h
                        nxt.append(v)
            frontier = nxt
            frontiers.append(len(nxt))
        members = frozenset(at[p] for p in seen if p != start and p in at)
        self._note(f"reach {rel.value} from {atom!r} depth {hops} {direction.value}: breadth "
                   f"first over the typed edges, frontiers {frontiers}; {len(members)} reached")
        return RegionV(members, {at[p]: {"hops": h} for p, h in seen.items()
                                 if p in at and p != start})

    def _relate(self, atom: str) -> RegionV:
        i = self.u.index_of(atom)
        digest = self.u.digest_of(i)
        by_digest = {self.u.digest_of(j): j for j in range(len(self.u))}
        members: set[int] = set()
        detail: dict[int, Mapping[str, object]] = {}
        for r in self.u.relations:
            if digest not in (r.u, r.v):
                continue
            other = r.v if r.u == digest else r.u
            j = by_digest.get(other)
            if j is None:
                continue
            members.add(j)
            detail[j] = {"relation": r.rel_type, "sign": r.sign, "w": r.w,
                         "direction": "out" if r.u == digest else "in"}
        positive = sum(1 for d in detail.values() if d.get("sign") == 1)
        self._note(f"relate {atom!r}: {len(members)} notes joined by a signed relation edge "
                   f"({positive} supporting, {len(members) - positive} contradicting)")
        return RegionV(frozenset(members), detail)

    def _trace(self, atom: str, direction: Direction) -> ChainsV:
        versions = self.u.history(atom)
        if direction is Direction.BACK:
            versions = list(reversed(versions))
        self._note(f"trace {atom!r} {direction.value}: {len(versions)} versions on the note's "
                   "supersession chain")
        if not versions:
            return ChainsV(())
        head = f"{versions[0][0]}@{versions[0][1]}"
        steps = tuple((Rel.D, f"{d}@{s}") for d, s, _digest, _at in versions[1:])
        return ChainsV((Chain(head, steps),))

    def _walk(self, atom: str, path: str, to: str | None, depth: int | None) -> ChainsV:
        start = self.u.path_of(self.u.index_of(atom))
        target = self.u.path_of(self.u.index_of(to)) if to is not None else None
        dfa = compile_path(path)
        d = depth if depth is not None else self.p.walk_depth
        chains = product_walk(self.u.typed_graph(), dfa, start, depth=d, target=target,
                              limit=self.p.walk_limit)
        self._note(f"walk from {atom!r} via {path}: the product of the typed graph with the "
                   f"path's automaton, depth {d}, at most {self.p.walk_limit} chains; "
                   f"{len(chains)} found", "QSA-7")
        return ChainsV(tuple(chains))


def _response(actual: Value, assumed: Value, u: Universe) -> list[str]:
    """What moved between the two evaluations, on the result's sort."""
    if isinstance(actual, FieldV) and isinstance(assumed, FieldV):
        delta = assumed.scores - actual.scores
        changed = np.flatnonzero(np.abs(delta) > 1e-12)
        if changed.size == 0:
            return ["the field did not move"]
        up = int(np.sum(delta > 1e-12))
        down = int(np.sum(delta < -1e-12))
        j = int(changed[np.argmax(np.abs(delta[changed]))])
        return [f"the field moved on {changed.size} notes ({up} up, {down} down); the largest "
                f"change is {delta[j]:+.4f} at {u.path_of(j)!r}"]
    if isinstance(actual, RegionV) and isinstance(assumed, RegionV):
        added = sorted(u.path_of(i) for i in assumed.members - actual.members)
        removed = sorted(u.path_of(i) for i in actual.members - assumed.members)
        return [f"the region gained {added} and lost {removed}"]
    if isinstance(actual, ChainsV) and isinstance(assumed, ChainsV):
        return [f"{len(assumed.chains)} chains under the assumption, {len(actual.chains)} without"]
    return []


# ── the answer ─────────────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class SentenceAnswer:
    """The plan, the hits it produced, and — under `assume` — the `Hyp` beside the actual hits."""

    plan: Plan
    hits: tuple[Hit, ...]
    hyp: Hyp[tuple[Hit, ...]] | None
    notes: tuple[str, ...]
    trace: Trace | None = None

    def to_dict(self) -> dict[str, Any]:
        def rows(hits: tuple[Hit, ...]) -> list[dict[str, Any]]:
            return [{k: v for k, v in h.__dict__.items() if v not in (None, "", {})} for h in hits]

        out: dict[str, Any] = {
            "sentence": self.plan.sentence,
            "sort": self.plan.sort.value,
            "modes": list(self.plan.modes),
            "plan": self.plan.explain(),
            "notes": list(self.notes),
            "hits": rows(self.hits),
        }
        if self.hyp is not None:
            out["hyp"] = {"assumptions": list(self.hyp.assumptions), "hits": rows(self.hyp.value)}
        if self.trace is not None:
            out["trace"] = self.trace.to_dict()
        return out


def _hits(value: Value, u: Universe, k: int) -> tuple[Hit, ...]:
    if isinstance(value, FieldV):
        ranked = np.argsort(-value.scores, kind="stable")
        order = [int(j) for j in ranked if value.scores[j] > 0][:k]
        return tuple(_hit(u, j, score=float(value.scores[j])) for j in order)
    if isinstance(value, RegionV):
        return tuple(_hit(u, j, detail=dict(value.detail.get(j, {})))
                     for j in sorted(value.members))
    if isinstance(value, ChainsV):
        return tuple(Hit(ref=str(c), stratum="mirror",
                         detail={"word": "".join(m.value for m in c.word), "length": len(c.steps)})
                     for c in value.chains)
    if isinstance(value, WitnessV):
        return () if value.record is None else (
            Hit(ref=str(value.record.get("edge_id", "")), stratum="dialogue",
                detail=dict(value.record)),)
    if isinstance(value, TextV):
        r = value.record
        detail = {"chunks": str(r["chunks"])} if "chunks" in r else {}
        return (Hit(ref=str(r.get("ref", "")), title=str(r.get("title", "")),
                    stratum=str(r.get("stratum", "")), provenance=str(r.get("provenance", "")),
                    text=str(r.get("text", "")), detail=detail),)
    raise UnsupportedSentence("a Hyp inside a Hyp")  # pragma: no cover


def _hit(u: Universe, j: int, *, score: float | None = None,
         detail: dict[str, Any] | None = None) -> Hit:
    n = u.notes[j]
    node_detail = n.get("detail") or {}
    return Hit(ref=str(n.get("source_path", "")), title=str(n.get("title", "")),
               score=None if score is None else round(score, 4),
               stratum=str(n.get("stratum", "mirror") or "mirror"),
               provenance=str(n.get("provenance", "")),
               detail={**dict(node_detail), **(detail or {})})


def _rank_note(value: Value, k: int) -> str:
    if isinstance(value, FieldV):
        return (f"rank: the field's {k} best positive scores, ties by the universe's order "
                f"({int(np.count_nonzero(value.scores > 0))} positive)")
    if isinstance(value, RegionV):
        return f"rank: the region's {len(value.members)} members, in the universe's order"
    if isinstance(value, ChainsV):
        return f"rank: the {len(value.chains)} chains, as the walk found them"
    if isinstance(value, WitnessV):
        return "rank: the one record"
    if isinstance(value, TextV):
        return "rank: the text, one record"
    return "rank: the actual answer, then the assumed one"


def execute(plan: Plan, universe: Universe, *, precedents: Precedents = DEFAULT,
            trace: Trace | None = None) -> SentenceAnswer:
    """Evaluate a compiled plan: deterministic for one universe, the plan riding with the answer
    and, with a trace, the work shown step by step."""
    value = Evaluator(universe, precedents, trace).eval(plan.term)
    notes: list[str] = list(universe.missing)
    if plan.sort is Sort.FIELD and not isinstance(plan.term, ast.Top):
        notes.append(f"a field: the {precedents.k} best scores are shown; write 'top k' to rank "
                     f"explicitly")
    if trace is not None:
        trace.note("rank", _rank_note(value.actual if isinstance(value, HypV) else value,
                                      precedents.k))
    if isinstance(value, HypV):
        actual = _hits(value.actual, universe, precedents.k)
        assumed = _hits(value.assumed, universe, precedents.k)
        return SentenceAnswer(plan, actual, Hyp(assumed, value.assumptions),
                              tuple(notes) + value.notes, trace)
    return SentenceAnswer(plan, _hits(value, universe, precedents.k), None, tuple(notes), trace)


def ask(text: str, grant: Any, engine: QueryEngine | None = None, *,
        precedents: Precedents = DEFAULT) -> SentenceAnswer:
    """Compile a sentence under a grant and run it against the live universe."""
    from core.sentence.plan import compile_sentence

    plan = compile_sentence(text, grant, precedents=precedents)
    return execute(plan, Universe.from_engine(engine or QueryEngine()), precedents=precedents)
