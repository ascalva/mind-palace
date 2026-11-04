"""The executor — a plan evaluated against the notes, deterministically, with the overlay for
`assume` (dn-query-sentence-algebra §2.6–§2.7).

A `Universe` is what one evaluation reads: the authored notes with their unit vectors and the
similarity backbone (the σ-graph `QueryEngine._note_graph` builds), the typed edges among them
(citations `F`; `D` and `C` at the note grain are empty in this version and said so), the signed
relation edges, and the readers for the version chain and the witnessing commit. `assume` applies
an `Overlay` to a copy of the universe and evaluates the body there — nothing is written to any
store; the result is a `Hyp` beside the actual value, and the notes name the response class the
assumption falls in (QSA-9: adding weight lowers every effective resistance, removing it raises
every one, a contradiction keeps or breaks the camps).

Sorts evaluate to values: a field is a vector of scores in `[0, 1]` over the notes, a region a set
of note indices, a chain a list of `Chain`s, a witness a record. Connectives follow the algebra of
`core/sentence/algebra.py`, whose laws the Lean proves.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, replace
from typing import Any

import numpy as np

from core.kernel.scope import Hyp, Stratum
from core.query import Hit, QueryEngine, free_energy_distances
from core.sentence import ast
from core.sentence.algebra import atleast, camps, far, mask_field, topk
from core.sentence.ast import Direction, Node, Rel
from core.sentence.automaton import Chain, compile_path, product_walk
from core.sentence.plan import Plan
from core.sentence.precedents import DEFAULT, Precedents
from core.sentence.types import AmbiguousSentence, Sort


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

    def __len__(self) -> int:
        return len(self.notes)

    def index_of(self, atom: str) -> int:
        """The note a name picks out: by path, digest or title; refused when none or several."""
        hits = [i for i, n in enumerate(self.notes)
                if atom in (n.get("source_path"), n.get("digest"), n.get("title"))]
        if not hits:
            raise LookupError(f"no authored note matches {atom!r}")
        if len(hits) > 1:
            names = ", ".join(repr(self.notes[i]["source_path"]) for i in hits)
            raise AmbiguousSentence(f"{atom!r} names {len(hits)} notes: {names}; use a path")
        return hits[0]

    def path_of(self, i: int) -> str:
        return str(self.notes[i]["source_path"])

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
    def from_engine(cls, engine: QueryEngine) -> Universe:
        """The live universe: the engine's note graph, the reference edges among the notes at the
        anchor commit, the signed relation edges, the version chains and the C-fiber witness."""
        from core.origin_view import origin
        from core.reference_view import open_reference_view

        notes, mat, weights = engine._note_graph()
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

        return cls(notes=notes, vectors=mat, weights=weights,
                   edges={Rel.F: f_edges, Rel.D: {}, Rel.C: {}}, relations=relations,
                   embed=embed, history=history, witness=witness, cut=view.commit,
                   missing=("D and C moves at the note grain: the version chains are per note "
                            "(use trace) and the causal edges key on structural endpoints",))


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
class HypV:
    """A value under assumptions, beside the actual one, with the response read off."""

    actual: Value
    assumed: Value
    assumptions: tuple[str, ...]
    notes: tuple[str, ...]


Value = FieldV | RegionV | ChainsV | WitnessV | HypV


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
        for i, j, delta in self.s_edges:
            weights[i, j] = weights[j, i] = float(np.clip(weights[i, j] + delta, 0.0, 1.0))
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
        return replace(u, weights=weights, edges=edges, relations=relations)

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

    def __init__(self, universe: Universe, precedents: Precedents = DEFAULT) -> None:
        self.u = universe
        self.p = precedents

    def eval(self, node: Node) -> Value:
        match node:
            case ast.Near(text=text):
                v = self.u.embed(text)
                v = v / (np.linalg.norm(v) or 1.0)
                return FieldV(np.clip(self.u.vectors @ v, 0.0, 1.0))
            case ast.Diffuse(rel=rel, atom=atom, beta=beta):
                return self._diffuse(rel, atom, beta)
            case ast.Far(field=f):
                return FieldV(far(self._field(f)))
            case ast.Reach(rel=rel, atom=atom, depth=depth, direction=direction):
                return self._reach(rel, atom, depth, direction)
            case ast.Relate(atom=atom):
                return self._relate(atom)
            case ast.Top(k=k, field=f):
                scores = self._field(f)
                return RegionV(frozenset(i for i in topk(scores, k) if scores[i] > 0),
                               {i: {"score": round(float(scores[i]), 4)} for i in range(len(scores))
                                if scores[i] > 0})
            case ast.AtLeast(t=t, field=f):
                scores = self._field(f)
                return RegionV(atleast(scores, t),
                               {i: {"score": round(float(scores[i]), 4)}
                                for i in range(len(scores))})
            case ast.Not(region=r):
                return RegionV(frozenset(range(len(self.u))) - self._region(r))
            case ast.Minus(left=a, right=b):
                return RegionV(self._region(a) - self._region(b))
            case ast.And(left=a, right=b):
                return self._and(self.eval(a), self.eval(b))
            case ast.Or(left=a, right=b):
                return self._or(self.eval(a), self.eval(b))
            case ast.Then(left=a, right=b):
                return self._mask(self.eval(b), self._region(a))
            case ast.Within(body=b, region=r):
                return self._mask(self.eval(b), self._region(r))
            case ast.Over(body=b, strata=strata):
                allowed = {Stratum.MIRROR_AUTHORED.value, Stratum.MIRROR.value}
                if any(s not in allowed for s in strata):
                    raise UnsupportedSentence(
                        f"over {' '.join(strata)}: this universe holds the authored notes "
                        f"(mirror_authored); other strata need their stores wired")
                return self.eval(b)
            case ast.AsOf(body=b, cut=cut):
                if self.u.cut is not None and cut != self.u.cut:
                    raise UnsupportedSentence(
                        f"as of {cut!r}: this universe is read at {self.u.cut!r}; a past cut needs "
                        f"the snapshot store")
                return self.eval(b)
            case ast.Trace(atom=atom, direction=direction):
                return self._trace(atom, direction)
            case ast.Walk(atom=atom, path=path, to=to, depth=depth):
                return self._walk(atom, path, to, depth)
            case ast.Witness(edge=edge):
                return WitnessV(self.u.witness(edge))
            case ast.Assume(hypothesis=h, body=b):
                overlay = Overlay.of(h, self.u)
                assumed = Evaluator(overlay.apply(self.u), self.p).eval(b)
                actual = self.eval(b)
                notes = (tuple(overlay.describe_response(self.u))
                         + tuple(_response(actual, assumed, self.u)))
                return HypV(actual, assumed, (ast.describe(h),), notes)
        raise UnsupportedSentence(f"no evaluator for {node!r}")  # pragma: no cover

    # ── helpers ────────────────────────────────────────────────────────────────────────────────
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
            return FieldV(a.scores * b.scores)                    # the Schur product, QSA-1
        if isinstance(a, RegionV) and isinstance(b, RegionV):
            return RegionV(a.members & b.members, {**dict(b.detail), **dict(a.detail)})
        if isinstance(a, FieldV) and isinstance(b, RegionV):
            return self._mask(a, b.members)
        if isinstance(a, RegionV) and isinstance(b, FieldV):
            return self._mask(b, a.members)
        raise UnsupportedSentence("and: fields and regions only")

    def _or(self, a: Value, b: Value) -> Value:
        if isinstance(a, FieldV) and isinstance(b, FieldV):
            return FieldV((a.scores + b.scores) / 2.0)             # the convex mixture
        if isinstance(a, RegionV) and isinstance(b, RegionV):
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
            return FieldV(np.zeros(len(self.u)))
        dist = free_energy_distances(W, beta=beta if beta is not None else self.p.beta)[i]
        scores = np.where(np.isfinite(dist), np.exp(-dist), 0.0)
        scores[i] = 0.0                                  # a note is not retrieved from itself
        return FieldV(np.clip(scores, 0.0, 1.0))

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
        for h in range(1, hops + 1):
            nxt: list[str] = []
            for u in frontier:
                for v in sorted(nbrs.get(u, ())):
                    if v not in seen:
                        seen[v] = h
                        nxt.append(v)
            frontier = nxt
        members = frozenset(at[p] for p in seen if p != start and p in at)
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
        return RegionV(frozenset(members), detail)

    def _trace(self, atom: str, direction: Direction) -> ChainsV:
        versions = self.u.history(atom)
        if direction is Direction.BACK:
            versions = list(reversed(versions))
        if not versions:
            return ChainsV(())
        head = f"{versions[0][0]}@{versions[0][1]}"
        steps = tuple((Rel.D, f"{d}@{s}") for d, s, _digest, _at in versions[1:])
        return ChainsV((Chain(head, steps),))

    def _walk(self, atom: str, path: str, to: str | None, depth: int | None) -> ChainsV:
        start = self.u.path_of(self.u.index_of(atom))
        target = self.u.path_of(self.u.index_of(to)) if to is not None else None
        dfa = compile_path(path)
        chains = product_walk(self.u.typed_graph(), dfa, start,
                              depth=depth if depth is not None else self.p.walk_depth,
                              target=target, limit=self.p.walk_limit)
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
    raise UnsupportedSentence("a Hyp inside a Hyp")  # pragma: no cover


def _hit(u: Universe, j: int, *, score: float | None = None,
         detail: dict[str, Any] | None = None) -> Hit:
    n = u.notes[j]
    return Hit(ref=str(n.get("source_path", "")), title=str(n.get("title", "")),
               score=None if score is None else round(score, 4), stratum="mirror",
               provenance=str(n.get("provenance", "")), detail=detail or {})


def execute(plan: Plan, universe: Universe, *, precedents: Precedents = DEFAULT) -> SentenceAnswer:
    """Evaluate a compiled plan: deterministic for one universe, the plan riding with the answer."""
    value = Evaluator(universe, precedents).eval(plan.term)
    notes: list[str] = list(universe.missing)
    if plan.sort is Sort.FIELD and not isinstance(plan.term, ast.Top):
        notes.append(f"a field: the {precedents.k} best scores are shown; write 'top k' to rank "
                     f"explicitly")
    if isinstance(value, HypV):
        actual = _hits(value.actual, universe, precedents.k)
        assumed = _hits(value.assumed, universe, precedents.k)
        return SentenceAnswer(plan, actual, Hyp(assumed, value.assumptions),
                              tuple(notes) + value.notes)
    return SentenceAnswer(plan, _hits(value, universe, precedents.k), None, tuple(notes))


def ask(text: str, grant: Any, engine: QueryEngine | None = None, *,
        precedents: Precedents = DEFAULT) -> SentenceAnswer:
    """Compile a sentence under a grant and run it against the live universe."""
    from core.sentence.plan import compile_sentence

    plan = compile_sentence(text, grant, precedents=precedents)
    return execute(plan, Universe.from_engine(engine or QueryEngine()), precedents=precedents)
