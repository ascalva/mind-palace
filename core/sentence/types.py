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
from typing import Any

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
    EVENT = "event"          # a command's value: a receipt, never a field (dn-ingest-door D2)


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
        case ast.Do():
            return Sort.EVENT
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
            return _maskable(b, "then", "the left's region masks the right")
        case ast.Within(body=b, region=r):
            _want(r, Sort.REGION, "within", "an adjective restricts to a region")
            sb = sort_of(b)
            if sb not in (Sort.FIELD, Sort.REGION):
                raise SortError(f"within: restricts a field or a region, not a {sb.value}")
            return sb
        case ast.Over(body=b):
            return _maskable(b, "over", "it masks to its strata")
        case ast.Assume(body=b):
            return _maskable(b, "assume", "a hypothesis perturbs what is computed")
        case ast.AsOf(body=b):
            return sort_of(b)
    raise SortError(f"unknown node {node!r}")  # pragma: no cover - the match is total


def _maskable(node: Node, production: str, reason: str) -> Sort:
    """A field, a region or chains: what a mask restricts and a hypothesis moves. A `read` is
    the record at its ref, held to the ref's stratum, and a witness is an edge's record; neither
    composes (`docs/query/asking.md`)."""
    got = sort_of(node)
    if got in (Sort.TEXT, Sort.WITNESS, Sort.EVENT):
        raise SortError(f"{production}: a field, a region or chains, not a {got.value}; {reason}, "
                        f"and a {got.value} is a record that composes with nothing")
    return got


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
class Context:
    """What is in force at a node: the strata (`over`, else the precedent), the cut (`as of`) and
    whether the node is under `assume`. The typing and the evaluator walk a term with it alike, so
    a verb is evaluated on exactly the strata its clause was admitted for."""

    strata: tuple[Stratum, ...]
    cut: str | None
    overlay: bool

    @classmethod
    def initial(cls, precedents: Precedents = DEFAULT) -> Context:
        return cls(precedents.strata, None, False)

    def over(self, names: tuple[str, ...]) -> Context:
        return Context(_strata(names), self.cut, self.overlay)

    def as_of(self, cut: str) -> Context:
        return Context(self.strata, cut, self.overlay)

    def assumed(self) -> Context:
        return Context(self.strata, self.cut, True)


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


# The repo paths that are the foundation denylist 𝔇 (`Stratum.FOUNDATION`, never in a grant): the
# constitution and the frozen golden set, the paths the CI denylist job guards. A `read` of one is
# typed in FOUNDATION, so admission refuses it before anything is opened.
FOUNDATION_PATHS: tuple[str, ...] = ("CONSTITUTION.md", "eval/golden.py", "eval/golden/")


def repo_path(atom: str) -> str | None:
    """The repo-relative path a `read` atom names, a leading `./` dropped; None when the atom is
    not a repo path (a paper, transcript or dialogue ref, an absolute or home path, a title) or has
    an empty, `.` or `..` part (git's tree has no such names, and `..` would climb)."""
    if "/" not in atom or atom.startswith((CURATED_REF, TRANSCRIPT_REF, "dialogue/", "/", "~")):
        return None
    rel = atom.removeprefix("./")
    return None if any(part in ("", ".", "..") for part in rel.split("/")) else rel


def is_foundation(rel: str) -> bool:
    """Whether a repo-relative path lies in the foundation denylist, compared case-folded: the
    checkout's file system need not be case-sensitive, so `constitution.md` names the same file."""
    r = rel.casefold()
    return any(r == f.casefold() or (f.endswith("/") and r.startswith(f.casefold()))
               for f in FOUNDATION_PATHS)


def read_strata(atom: str) -> tuple[Stratum, ...]:
    """The strata a `read` of `atom` can land in, by the ref's shape: a paper ref reads the
    curated stratum; a transcript turn the dialogue's transcript stratum (the chat stores); a
    dialogue turn the dialogue; a repo-relative path the reference stratum (the repo's own docs
    and code), save the foundation's paths, which are FOUNDATION and so never admitted; an
    absolute path the mirror; a title the mirror or the dialogue."""
    if atom.startswith(CURATED_REF):
        return (Stratum.CURATED,)
    if atom.startswith(TRANSCRIPT_REF):
        return (Stratum.DIALOGUE_TRANSCRIPT,)
    if atom.startswith("dialogue/"):
        return (Stratum.DIALOGUE,)
    if atom.startswith(("/", "~")):
        return (Stratum.MIRROR_AUTHORED,)
    if "/" in atom:
        rel = repo_path(atom)
        return (Stratum.FOUNDATION,) if rel is not None and is_foundation(rel) \
            else (Stratum.REFERENCE,)
    return (Stratum.MIRROR_AUTHORED, Stratum.DIALOGUE)


def anchor_strata(atom: str, in_force: tuple[Stratum, ...]) -> tuple[Stratum, ...]:
    """The strata a named node lies in, read off the name as `read_strata` reads a ref: a paper
    ref is curated, a transcript turn the transcript's, a dialogue turn the dialogue's, an
    absolute path the mirror's, a repo path the reference graph's; a title names a node of the
    strata in force. Naming a node reads its stratum."""
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
    return in_force


def _union(*groups: Iterable[Stratum]) -> tuple[Stratum, ...]:
    out: list[Stratum] = []
    for group in groups:
        for s in group:
            if s not in out:
                out.append(s)
    return tuple(out)


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
              clock: Clock, point: bool, ctx: Context) -> Scope:
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


def _clause(verb: str, rel: Rel | None, ctx: Context, precedents: Precedents,
            atoms: tuple[str, ...] = ()) -> Clause:
    """A verb's clause. The similarity backbone joins nodes of one stratum, so an `S` walk reads
    the strata in force and its anchors' own (`diffuse S from` a paper walks among the papers);
    the recorded relations read their own strata whatever is in force (QSA-b)."""
    strata = _union(ctx.strata, *(anchor_strata(a, ctx.strata) for a in atoms))
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


def _walk_clause(path: str, ctx: Context, atoms: tuple[str, ...] = ()) -> Clause:
    from core.sentence.automaton import letters
    rels = letters(path)
    fibers = {r.value for r in rels if r is not Rel.S}
    in_s = _union(ctx.strata, *(anchor_strata(a, ctx.strata) for a in atoms))
    strata: list[Stratum] = []
    for r in sorted(rels, key=lambda r: r.value):
        for s in (in_s if r is Rel.S else _REL_STRATA[r]):
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


def _read_clause(atom: str, ctx: Context) -> Clause:
    """`read <ref>`: the clause requires the strata the ref's shape can land in (`read_strata`),
    and the executor holds the record's stratum to them — the shape decides at compile time, the
    catalog or the repo at run time."""
    strata = read_strata(atom)
    clock = Clock.COMMIT if strata in ((Stratum.REFERENCE,), (Stratum.FOUNDATION,)) \
        else Clock.PROJECTION_EVENT
    req = _required("read", None, strata, fibers=set(), clock=clock, point=True, ctx=ctx)
    return Clause("read", None, req, mode_of(req), ctx.overlay)


def requirement_clause(r: Any) -> Clause:
    """What one of a script's effects requires (R1; DOR-1 effect by effect, QSA-5): the write bit
    at `now` on the place's stratum for a store or a retire, on the strata a job declares for a
    `run`, on the interpreted stratum for a link, which proposes. The provenance of what lands is
    the palace's, never a word of the script (dn-door-language §E3)."""
    from core.ingest.table import JOBS, PLACES
    from core.kernel.scope import StratumScope

    strata: tuple[Stratum, ...]
    match r.kind:
        case "place":
            p = PLACES[r.name]
            name, strata, fibers, clock, propose = (f"store in {r.name}", (p.stratum,), set(),
                                                    p.clock, False)
        case "job":
            j = JOBS[r.name]
            name, strata, fibers, clock, propose = (f"run {r.name}", j.strata, set(j.fibers),
                                                    j.clock, j.propose)
        case _:
            name, strata, fibers, clock, propose = ("link", (Stratum.INTERPRETED,), set(),
                                                    Clock.PROJECTION_EVENT, True)
    # The SLICE rule, as `_required` applies it: a point write across several closed strata on a
    # clock that is not a cut clock names the single-read cut (SCO-8), as a read would.
    closed = StratumScope.of(*strata).strata
    cut = "single-read" if len(closed) > 1 and clock is not Clock.COMMIT else None
    req = scope(set(strata), fibers, clock, Window.point(ANCHOR), propose=propose, write=True,
                cut=cut)
    return Clause(name, None, req, mode_of(req), False)


def _anchored(clause: Clause, atoms: Iterable[str | None], ctx: Context, *,
              causal: bool = False) -> list[Clause]:
    """A verb's clause, then the clauses for what it names or reaches outside its own strata. An
    anchor whose stratum the verb's scope does not cover is a `name` clause: finding the node a
    name picks out reads its stratum, so `reach C from` a note reads the mirror to find the note
    as surely as it reads the causal edges from it. A causal walk's endpoints are any node a
    session wrote, a vault note among them, so a walk over `C` reads its endpoints in the strata
    in force (the mirror by default) as an `endpoints` clause, on the clock those strata keep."""
    from core.kernel.scope import StratumScope

    out = [clause]
    covered = clause.req.sigma.strata
    if causal and not StratumScope.of(*ctx.strata).strata <= covered:
        req = _required("endpoints", None, ctx.strata, fibers=set(),
                        clock=Clock.PROJECTION_EVENT, point=True, ctx=ctx)
        out.append(Clause("endpoints", None, req, mode_of(req), ctx.overlay))
        covered = covered | req.sigma.strata
    for atom in atoms:
        if atom is None:
            continue
        strata = anchor_strata(atom, ctx.strata)
        if StratumScope.of(*strata).strata <= covered:
            continue
        clock = Clock.COMMIT if strata == (Stratum.REFERENCE,) else Clock.PROJECTION_EVENT
        req = _required("name", None, strata, fibers=set(), clock=clock, point=True, ctx=ctx)
        out.append(Clause("name", None, req, mode_of(req), ctx.overlay))
    return out


def clauses_of(node: Node, *, precedents: Precedents = DEFAULT) -> tuple[Clause, ...]:
    """Every clause of a sentence with its required scope, in reading order."""
    return tuple(_clauses(node, Context.initial(precedents), precedents))


def verb_strata(node: Node, ctx: Context, precedents: Precedents = DEFAULT) -> frozenset[Stratum]:
    """The strata a verb's clause reads under `ctx`, closed downward: what the evaluator holds
    the verb's value to (QSA-5's typing invariant, a clause reads only what it requires)."""
    from core.kernel.scope import StratumScope

    out: set[Stratum] = set()
    for i, c in enumerate(_clauses(node, ctx, precedents)):
        if i == 0 or c.verb == "endpoints":
            out |= StratumScope.of(*c.req.sigma.strata).strata
    return frozenset(out - {Stratum.HYPOTHETICAL})


def term_strata(node: Node, ctx: Context, precedents: Precedents = DEFAULT) -> frozenset[Stratum]:
    """The strata a term's verbs read, the union of their clauses' (a name clause aside): the
    carrier a complement or a reversal of the term is taken within."""
    from core.kernel.scope import StratumScope

    out: set[Stratum] = set()
    for c in _clauses(node, ctx, precedents):
        if c.verb != "name":
            out |= StratumScope.of(*c.req.sigma.strata).strata
    return frozenset(out - {Stratum.HYPOTHETICAL})


def _clauses(node: Node, ctx: Context, p: Precedents) -> list[Clause]:
    match node:
        case ast.Near():
            return [_clause("near", None, ctx, p)]
        case ast.Diffuse(rel=rel, atom=atom):
            return _anchored(_clause("diffuse", rel, ctx, p, _s_atoms(rel, atom)), (atom,), ctx)
        case ast.Reach(rel=rel, atom=atom):
            return _anchored(_clause("reach", rel, ctx, p, _s_atoms(rel, atom)), (atom,), ctx,
                             causal=rel is Rel.C)
        case ast.Relate(atom=atom):
            return _anchored(_clause("relate", None, ctx, p), (atom,), ctx)
        case ast.Trace(atom=atom):
            return _anchored(_clause("trace", None, ctx, p), (atom,), ctx)
        case ast.Walk(path=path, atom=atom, to=to):
            from core.sentence.automaton import letters

            return _anchored(_walk_clause(path, ctx, (atom,)), (atom, to), ctx,
                             causal=Rel.C in letters(path))
        case ast.Witness():
            return [_clause("witness", None, ctx, p)]
        case ast.Read(atom=atom):
            return [_read_clause(atom, ctx)]
        case ast.Do(requirements=reqs):
            return [requirement_clause(r) for r in reqs]
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
            return _clauses(b, ctx.over(names), p)
        case ast.AsOf(body=b, cut=cut):
            return _clauses(b, ctx.as_of(cut), p)
        case ast.Assume(hypothesis=h, body=b):
            # the hypothesis reads what it perturbs: an edge of its relation, or a signed
            # relation edge, typed as a clause of its own under the overlay, so `assume C …`
            # needs a plane that admits C as surely as `reach C` does
            octx = ctx.assumed()
            ends = (h.a, h.b)
            hyp = (_clause("relate", None, octx, p) if isinstance(h, ast.ContradictHyp)
                   else _clause("reach", h.rel, octx, p, _s_atoms(h.rel, *ends)))
            return _anchored(hyp, ends, octx, causal=getattr(h, "rel", None) is Rel.C) \
                + _clauses(b, octx, p)
    raise SortError(f"unknown node {node!r}")  # pragma: no cover


def _s_atoms(rel: Rel, *atoms: str) -> tuple[str, ...]:
    """The anchors whose strata an `S` walk joins (its own stratum's backbone); none for the
    recorded relations, whose anchors are named by a clause of their own when uncovered."""
    return atoms if rel is Rel.S else ()


def admissible(node: Node, grant: Grant, *, precedents: Precedents = DEFAULT) -> bool:
    """QSA-5: admissible iff every clause's required scope is admitted by the grant."""
    return all(grant.admits(c.req) for c in clauses_of(node, precedents=precedents))


def check_admissible(node: Node, grant: Grant, *, precedents: Precedents = DEFAULT) -> None:
    """`admissible`, raising `IllScopedSentence` for the first clause the grant refuses."""
    for c in clauses_of(node, precedents=precedents):
        if not grant.admits(c.req):
            why = " under 'assume', which needs a plane naming the overlay stratum" \
                if c.overlay else ""
            if Stratum.FOUNDATION in c.req.sigma.strata:
                why = ": the foundation (the constitution, the golden set) is never granted"
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
