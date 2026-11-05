"""The typing — sorts, the clause-wise scope check, the mode per clause, and the result grade
(dn-query-sentence-algebra §2.4; the laws QSA-5 in `formal/Palace/Sentence.lean`).

Three judgements on a parsed sentence:

* **sorts** (`sort_of`): each node has a sort — field, region, chain or witness in this version
  (kernels appear only as the columns their fields are, QSA-3; metrics only through `diffuse`) —
  and an ill-sorted sentence is refused with the structure's reason (`not` on a field: the cone has
  no complement).
* **scopes** (`clauses_of`, `admissible`): each clause requires the scope its verb and relation
  noun need, Rule NOUN — the letter in `E` is the relation walked, so `diffuse S` is
  kernel-licensed (`E = ∅`, semantic) while `reach F` is citation-structural; a sentence is
  admissible under a grant iff every clause's scope lies under some granted plane (QSA-5,
  `Sentence.admissible_iff_clauses`). Under `assume` a clause's `Σ` gains the overlay stratum, so
  a grant must name it (`admissible_assume_overlay`); the Ambassador's does not
  (`ambassador_no_assume`).
* **the result grade** (`hyps_of`, `is_inv`): a result under `assume` is `Hyp` of the assumptions
  in force, never `Inv` (Rule HYP, `not_isInv_assume`).
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum

from core.kernel.scope import ANCHOR, Clock, Scope, Stratum, Window
from core.query import CURATED_REF, Grant, Mode, mode_of, scope
from core.sentence import ast
from core.sentence.ast import Node, Rel
from core.sentence.precedents import DEFAULT, Precedents


class Sort(StrEnum):
    FIELD = "field"
    REGION = "region"
    KERNEL = "kernel"
    METRIC = "metric"
    RELATION = "relation"
    CHAIN = "chain"
    WITNESS = "witness"
    TEXT = "text"


class SortError(TypeError):
    """The sentence is ill-sorted; the message names the structure that forbids it."""


class IllScopedSentence(PermissionError):
    """A clause's required scope lies under no granted plane (QSA-5)."""


class AmbiguousSentence(ValueError):
    """A name or a reading the precedents do not settle; the message lists the candidates."""


# ── sorts ──────────────────────────────────────────────────────────────────────────────────────


def _note_atom(atom: str | None, verb: str) -> None:
    """A curated paper's ref handed to a verb that walks the owner's notes alone — the relation
    edges and the version chains — is refused at compile time, with where to go instead, before
    any store opens (once the retired table's `OutOfScopeTarget`; now a sort error). `diffuse`,
    `reach` and `walk` take a paper: the stratified universe seeds its neighbourhood."""
    if atom is not None and atom.startswith(CURATED_REF):
        raise SortError(f"{verb}: {atom!r} is a curated paper; {verb} walks the owner's notes "
                        f'only. For papers: near "…" over curated, diffuse S from the ref, or '
                        f"read it")


def sort_of(node: Node) -> Sort:
    """The sort of a node, or `SortError` with the reason (dn-query-sentence-algebra §2.4)."""
    match node:
        case ast.Near():
            return Sort.FIELD
        case ast.Diffuse():
            return Sort.FIELD
        case ast.Far(field=f):
            _want(f, Sort.FIELD, "far", "the bounded reversal 1 − f is a field operation")
            return Sort.FIELD
        case ast.Reach():
            return Sort.REGION
        case ast.Relate(atom=a):
            _note_atom(a, "relate")
            return Sort.REGION
        case ast.Top(field=f):
            _want(f, Sort.FIELD, "top", "the top-k ranks a field")
            return Sort.REGION
        case ast.AtLeast(field=f):
            _want(f, Sort.FIELD, "atleast", "a threshold cuts a field")
            return Sort.REGION
        case ast.Not(region=r):
            s = sort_of(r)
            if s is not Sort.REGION:
                raise SortError(
                    f"not: regions only, got a {s.value}; the cone has no complement, so write "
                    f"'far' for the bounded reversal of a field or 'not' on a region")
            return Sort.REGION
        case ast.Minus(left=a, right=b):
            _want(a, Sort.REGION, "minus", "set difference is a region operation")
            _want(b, Sort.REGION, "minus", "set difference is a region operation")
            return Sort.REGION
        case ast.Trace(atom=a):
            _note_atom(a, "trace")
            return Sort.CHAIN
        case ast.Walk():
            return Sort.CHAIN
        case ast.Witness():
            return Sort.WITNESS
        case ast.Read():
            return Sort.TEXT
        case ast.And(left=a, right=b):
            sa, sb = sort_of(a), sort_of(b)
            if sa is Sort.FIELD and sb is Sort.FIELD:
                return Sort.FIELD            # the Schur product, QSA-1
            if sa is Sort.REGION and sb is Sort.REGION:
                return Sort.REGION           # intersection
            if {sa, sb} == {Sort.FIELD, Sort.REGION}:
                return Sort.FIELD            # a field masked by a region, QSA-2
            raise SortError(f"and: fields and regions compose, not a {sa.value} with a {sb.value}")
        case ast.Or(left=a, right=b):
            sa, sb = sort_of(a), sort_of(b)
            if sa is sb and sa in (Sort.FIELD, Sort.REGION):
                return sa                    # the convex mixture, or the union
            raise SortError(f"or: two fields or two regions, not a {sa.value} with a {sb.value}")
        case ast.Then(left=a, right=b):
            sa = sort_of(a)
            if sa is not Sort.REGION:
                raise SortError(
                    f"then: the left clause must be a region to mask the right one, got a "
                    f"{sa.value}; write 'top k' or 'atleast t' to make it one")
            return sort_of(b)
        case ast.Within(body=b, region=r):
            _want(r, Sort.REGION, "within", "an adjective restricts to a region")
            sb = sort_of(b)
            if sb not in (Sort.FIELD, Sort.REGION):
                raise SortError(f"within: restricts a field or a region, not a {sb.value}")
            return sb
        case ast.Over(body=b) | ast.AsOf(body=b) | ast.Assume(body=b):
            return sort_of(b)
    raise SortError(f"unknown node {node!r}")  # pragma: no cover - the match is total


def _want(node: Node, sort: Sort, production: str, reason: str) -> None:
    got = sort_of(node)
    if got is not sort:
        raise SortError(f"{production}: needs a {sort.value}, got a {got.value}; {reason}")


def typecheck(node: Node) -> Sort:
    """Check a sentence and return its sort. Hypotheses must name two distinct notes."""
    sort = sort_of(node)
    for h in _hypotheses(node):
        a, b = _endpoints(h)
        if a == b:
            raise SortError(f"assume: an edge joins two distinct notes, got {a!r} twice")
    return sort


# ── clauses and scopes ─────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Clause:
    """One verb occurrence with the scope it requires and the mode that follows from it."""

    verb: str
    rel: Rel | None
    req: Scope
    mode: Mode
    overlay: bool

    def describe(self) -> str:
        sigma = ",".join(sorted(s.value for s in self.req.sigma.strata))
        edges = ",".join(sorted(self.req.edges.fibers)) or "∅"
        rel = f" {self.rel.value}" if self.rel is not None else ""
        return (f"{self.verb}{rel}: {self.mode.value}; Σ={{{sigma}}} E={{{edges}}} "
                f"T=({self.req.time.clock.value}, {self.req.time.window.kind.value})")


@dataclass(frozen=True)
class _Context:
    strata: tuple[Stratum, ...]
    cut: str | None
    overlay: bool


# The strata by the name a node carries (`Universe.notes[i]["stratum"]`): what `over` masks to and
# what `read` holds a record to.
MIRROR_NAMES: frozenset[Stratum] = frozenset({Stratum.MIRROR, Stratum.MIRROR_AUTHORED})
DIALOGUE_NAMES: frozenset[Stratum] = frozenset(
    {Stratum.DIALOGUE, Stratum.DIALOGUE_TRANSCRIPT, Stratum.DIALOGUE_ARTIFACT})
CURATED_NAMES: frozenset[Stratum] = frozenset({Stratum.CURATED})
REFERENCE_NAMES: frozenset[Stratum] = frozenset({Stratum.REFERENCE, Stratum.REFERENCE_REPO})
_SHORT: dict[Stratum, str] = {
    **{s: "mirror" for s in MIRROR_NAMES}, **{s: "dialogue" for s in DIALOGUE_NAMES},
    Stratum.DIALOGUE_TRANSCRIPT: "transcript",
    **{s: "curated" for s in CURATED_NAMES}, **{s: "reference" for s in REFERENCE_NAMES},
}
# A transcript turn's ref — `transcript/<session>/<turn>` — the chat stores' node (the
# `dialogue_transcript` stratum): the witness of a causal edge, read from the chatlog.
TRANSCRIPT_REF = "transcript/"
_PROVENANCE_STRATUM: dict[str, str] = {
    "authored-solo": "mirror", "authored-dialogue": "dialogue", "observed": "dialogue",
    "curated": "curated", "code": "reference",
}


def stratum_of_provenance(provenance: str) -> str:
    """The stratum a row's provenance places its node in ('' for a class the universe does not
    hold)."""
    return _PROVENANCE_STRATUM.get(provenance, "")


def short_names(strata: Iterable[Stratum]) -> frozenset[str]:
    """The node-stratum names a set of strata admits."""
    return frozenset(_SHORT[s] for s in strata if s in _SHORT)


def read_strata(atom: str) -> tuple[Stratum, ...]:
    """The strata a `read` of `atom` can land in, by the ref's shape: a paper ref reads the
    curated stratum; a transcript turn the dialogue's transcript stratum (the chat stores); a
    dialogue turn the dialogue; a repo-relative path the reference stratum (the repo's own docs
    and code); an absolute path the mirror; a title the mirror or the dialogue."""
    if atom.startswith(CURATED_REF):
        return (Stratum.CURATED,)
    if atom.startswith(TRANSCRIPT_REF):
        return (Stratum.DIALOGUE_TRANSCRIPT,)
    if atom.startswith("dialogue/"):
        return (Stratum.DIALOGUE,)
    if atom.startswith(("/", "~")):
        return (Stratum.MIRROR_AUTHORED,)
    if "/" in atom:
        return (Stratum.REFERENCE,)
    return (Stratum.MIRROR_AUTHORED, Stratum.DIALOGUE)


_REL_STRATA: dict[Rel, tuple[Stratum, ...]] = {
    Rel.S: (Stratum.MIRROR_AUTHORED,),
    Rel.F: (Stratum.REFERENCE,),
    Rel.D: (Stratum.MIRROR_AUTHORED,),
    Rel.C: (Stratum.REFERENCE, Stratum.DIALOGUE_TRANSCRIPT),
}


def _strata(names: tuple[str, ...]) -> tuple[Stratum, ...]:
    out: list[Stratum] = []
    for name in names:
        try:
            out.append(Stratum(name))
        except ValueError as e:
            raise AmbiguousSentence(
                f"over: {name!r} is not a stratum; one of "
                f"{', '.join(s.value for s in Stratum if s is not Stratum.FOUNDATION)}") from e
    return tuple(out)


def _required(verb: str, rel: Rel | None, strata: tuple[Stratum, ...], *, fibers: set[str],
              clock: Clock, point: bool, ctx: _Context) -> Scope:
    """The least scope a clause needs, with the overlay stratum under `assume` (QSA-5)."""
    sigma = tuple(strata) + ((Stratum.HYPOTHETICAL,) if ctx.overlay else ())
    window = Window.point(ctx.cut if ctx.cut is not None else ANCHOR) if point else Window.all()
    # The SLICE rule: a multi-stratum point read off a cut clock carries a consistent cut, the
    # single-read cut SEARCH uses (SCO-8); the overlay is read at the same anchor as the base.
    from core.kernel.scope import StratumScope
    closed = StratumScope.of(*sigma).strata
    cut = None
    if point and len(closed) > 1 and clock is not Clock.COMMIT:
        cut = ctx.cut if ctx.cut is not None else "single-read"
    return scope(sigma, fibers, clock, window, cut=cut)


def _clause(verb: str, rel: Rel | None, ctx: _Context, precedents: Precedents) -> Clause:
    strata = ctx.strata
    match verb, rel:
        case "near", _:
            req = _required(verb, None, strata, fibers=set(), clock=Clock.PROJECTION_EVENT,
                            point=True, ctx=ctx)
        case ("diffuse" | "reach"), Rel.S:
            req = _required(verb, rel, strata, fibers=set(), clock=Clock.PROJECTION_EVENT,
                            point=True, ctx=ctx)
        case ("diffuse" | "reach"), Rel.F:
            req = _required(verb, rel, _REL_STRATA[Rel.F], fibers={"F"}, clock=Clock.COMMIT,
                            point=True, ctx=ctx)
        case "reach", Rel.D:
            req = _required(verb, rel, _REL_STRATA[Rel.D], fibers={"D"}, clock=Clock.N_S,
                            point=False, ctx=ctx)
        case "reach", Rel.C:
            req = _required(verb, rel, _REL_STRATA[Rel.C], fibers={"C"}, clock=Clock.COMMIT,
                            point=True, ctx=ctx)
        case "diffuse", _:
            raise SortError(f"diffuse: walks S or F, not {rel.value if rel else '?'}")
        case "relate", _:
            # The signed relation edges are in no move class yet (QSA-b): typed by their strata.
            req = _required(verb, None, (Stratum.MIRROR_AUTHORED,), fibers=set(),
                            clock=Clock.PROJECTION_EVENT, point=True, ctx=ctx)
        case "trace", _:
            req = _required(verb, Rel.D, (Stratum.MIRROR_AUTHORED,), fibers={"D"},
                            clock=Clock.N_S, point=False, ctx=ctx)
        case "witness", _:
            req = _required(verb, Rel.C, _REL_STRATA[Rel.C], fibers={"C"}, clock=Clock.COMMIT,
                            point=True, ctx=ctx)
        case _:
            raise SortError(f"no scope rule for {verb} {rel}")  # pragma: no cover
    return Clause(verb, rel, req, mode_of(req), ctx.overlay)


def _walk_clause(path: str, ctx: _Context) -> Clause:
    from core.sentence.automaton import letters
    rels = letters(path)
    fibers = {r.value for r in rels if r is not Rel.S}
    strata: list[Stratum] = []
    for r in sorted(rels, key=lambda r: r.value):
        for s in _REL_STRATA[r]:
            if s not in strata:
                strata.append(s)
    if not strata:
        strata = list(ctx.strata)
    if Rel.F in rels or Rel.C in rels:
        clock = Clock.COMMIT
    elif Rel.D in rels:
        clock = Clock.N_S
    else:
        clock = Clock.PROJECTION_EVENT
    req = _required("walk", None, tuple(strata), fibers=fibers, clock=clock,
                    point=not (rels == {Rel.D}), ctx=ctx)
    return Clause("walk", None, req, mode_of(req), ctx.overlay)


def _read_clause(atom: str, ctx: _Context) -> Clause:
    """`read <ref>`: the clause requires the strata the ref's shape can land in (`read_strata`),
    and the executor holds the record's stratum to them — the shape decides at compile time, the
    catalog or the repo at run time."""
    strata = read_strata(atom)
    clock = Clock.COMMIT if strata == (Stratum.REFERENCE,) else Clock.PROJECTION_EVENT
    req = _required("read", None, strata, fibers=set(), clock=clock, point=True, ctx=ctx)
    return Clause("read", None, req, mode_of(req), ctx.overlay)


def clauses_of(node: Node, *, precedents: Precedents = DEFAULT) -> tuple[Clause, ...]:
    """Every clause of a sentence with its required scope, in reading order."""
    return tuple(_clauses(node, _Context(precedents.strata, None, False), precedents))


def _clauses(node: Node, ctx: _Context, p: Precedents) -> list[Clause]:
    match node:
        case ast.Near():
            return [_clause("near", None, ctx, p)]
        case ast.Diffuse(rel=rel):
            return [_clause("diffuse", rel, ctx, p)]
        case ast.Reach(rel=rel):
            return [_clause("reach", rel, ctx, p)]
        case ast.Relate():
            return [_clause("relate", None, ctx, p)]
        case ast.Trace():
            return [_clause("trace", None, ctx, p)]
        case ast.Walk(path=path):
            return [_walk_clause(path, ctx)]
        case ast.Witness():
            return [_clause("witness", None, ctx, p)]
        case ast.Read(atom=atom):
            return [_read_clause(atom, ctx)]
        case ast.Far(field=f) | ast.Top(field=f) | ast.AtLeast(field=f):
            return _clauses(f, ctx, p)
        case ast.Not(region=r):
            return _clauses(r, ctx, p)
        case ast.Minus(left=a, right=b) | ast.And(left=a, right=b) | ast.Or(left=a, right=b) \
                | ast.Then(left=a, right=b):
            return _clauses(a, ctx, p) + _clauses(b, ctx, p)
        case ast.Within(body=b, region=r):
            return _clauses(b, ctx, p) + _clauses(r, ctx, p)
        case ast.Over(body=b, strata=names):
            return _clauses(b, _Context(_strata(names), ctx.cut, ctx.overlay), p)
        case ast.AsOf(body=b, cut=cut):
            return _clauses(b, _Context(ctx.strata, cut, ctx.overlay), p)
        case ast.Assume(hypothesis=h, body=b):
            # the hypothesis reads what it perturbs: an edge of its relation, or a signed
            # relation edge, typed as a clause of its own under the overlay, so `assume C …`
            # needs a plane that admits C as surely as `reach C` does
            octx = _Context(ctx.strata, ctx.cut, True)
            hyp = (_clause("relate", None, octx, p) if isinstance(h, ast.ContradictHyp)
                   else _clause("reach", h.rel, octx, p))
            return [hyp] + _clauses(b, octx, p)
    raise SortError(f"unknown node {node!r}")  # pragma: no cover


def admissible(node: Node, grant: Grant, *, precedents: Precedents = DEFAULT) -> bool:
    """QSA-5: admissible iff every clause's required scope is admitted by the grant."""
    return all(grant.admits(c.req) for c in clauses_of(node, precedents=precedents))


def check_admissible(node: Node, grant: Grant, *, precedents: Precedents = DEFAULT) -> None:
    """`admissible`, raising `IllScopedSentence` for the first clause the grant refuses."""
    for c in clauses_of(node, precedents=precedents):
        if not grant.admits(c.req):
            why = " under 'assume', which needs a plane naming the overlay stratum" \
                if c.overlay else ""
            raise IllScopedSentence(f"{c.describe()} is not under any granted scope{why}")


# ── the result grade ───────────────────────────────────────────────────────────────────────────


def _hypotheses(node: Node) -> list[ast.Hypothesis]:
    match node:
        case ast.Assume(hypothesis=h, body=b):
            return [h] + _hypotheses(b)
        case ast.Far(field=f) | ast.Top(field=f) | ast.AtLeast(field=f):
            return _hypotheses(f)
        case ast.Not(region=r):
            return _hypotheses(r)
        case ast.Minus(left=a, right=b) | ast.And(left=a, right=b) | ast.Or(left=a, right=b) \
                | ast.Then(left=a, right=b) | ast.Within(body=a, region=b):
            return _hypotheses(a) + _hypotheses(b)
        case ast.Over(body=b) | ast.AsOf(body=b):
            return _hypotheses(b)
        case _:
            return []


def _endpoints(h: ast.Hypothesis) -> tuple[str, str]:
    return h.a, h.b


def hyps_of(node: Node) -> tuple[str, ...]:
    """The assumptions in force, in reading order (Rule HYP: they accumulate under connectives)."""
    return tuple(ast.describe(h) for h in _hypotheses(node))


def is_inv(node: Node) -> bool:
    """An `Inv` result: no assumption anywhere in the sentence."""
    return not _hypotheses(node)
