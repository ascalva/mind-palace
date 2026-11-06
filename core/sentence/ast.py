"""The sentence's syntax tree — the untyped term the parser builds and the typed, normalized term
the planner emits (one node family serves both; `types.sort_of` assigns the sorts).

Every node is a frozen dataclass, so a plan is a value: equal plans compare equal, and the
normal form is a pure function of the sentence (dn-query-sentence-algebra §2.7, determinism).
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, fields
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.sentence.script import Request
    from core.sentence.script_check import Requirement


class Rel(StrEnum):
    """The move alphabet `Σ_move` (fiber-geometry §2.0): similarity, citation, supersession,
    causal witness. The relation noun a verb walks; its letter is what the scope's `E` carries,
    except `S`, which kernel-carrying strata license (Rule NOUN)."""

    S = "S"
    F = "F"
    D = "D"
    C = "C"


class Direction(StrEnum):
    FORWARD = "forward"
    BACK = "back"
    BOTH = "both"


# ── field verbs ────────────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Near:
    """`near "<text>"`: the embedding kernel's column at the text (mode 2, the old SEARCH)."""

    text: str


@dataclass(frozen=True)
class Diffuse:
    """`diffuse <rel> from <note> [beta <β>]`: the retrieval curve's `e^{−β d}` column at the
    note (RSP-3), over the similarity backbone or the citation graph."""

    rel: Rel
    atom: str
    beta: float | None = None


@dataclass(frozen=True)
class Far:
    """`far <field>`: the bounded reversal `1 − f`: a field operation; the cone has no
    complement."""

    field: Node


# ── region verbs ───────────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Reach:
    """`reach <rel> from <note> [depth <n>] [back|forward|both]`: reachability (mode 1a)."""

    rel: Rel
    atom: str
    depth: int | None = None
    direction: Direction = Direction.BOTH


@dataclass(frozen=True)
class Relate:
    """`relate <note>`: the signed relation edges touching the note (supports, contradicts,
    contextualizes)."""

    atom: str


@dataclass(frozen=True)
class Top:
    """`top <k> <field>`: the `k` best, ties kept — the lossy bridge from a field to a region
    (QSA-4: it does not commute with `within`, so it stays last)."""

    k: int
    field: Node


@dataclass(frozen=True)
class AtLeast:
    """`atleast <t> <field>`: the threshold bridge (QSA-4: a positive threshold commutes with
    `within`)."""

    t: float
    field: Node


@dataclass(frozen=True)
class Not:
    """`not <region>`: the complement within the universe. Regions only."""

    region: Node


@dataclass(frozen=True)
class Minus:
    """`<region> minus <region>`."""

    left: Node
    right: Node


# ── chains and witnesses ───────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Trace:
    """`trace <note> [forward|back]`: the version chain along `D` (`σ_*` forward, `σ^*` back;
    the old HISTORY)."""

    atom: str
    direction: Direction = Direction.FORWARD


@dataclass(frozen=True)
class Walk:
    """`walk from <note> [to <note>] via <path> [depth <n>]`: the chains the path language admits,
    found by the product automaton with dead-state pruning (QSA-7)."""

    atom: str
    path: str
    to: str | None = None
    depth: int | None = None


@dataclass(frozen=True)
class Witness:
    """`witness "<edge id>"`: the C-fiber record that minted a durable edge (the old ORIGIN)."""

    edge: str


@dataclass(frozen=True)
class Read:
    """`read <ref> [chunk <n>]`: the text at a ref — a note, a dialogue turn, or a window of a
    curated paper (`reference:…`) around `chunk` — the dereference every answer's refs invite.
    Sort `text`: it composes with nothing (the one verb that returns content, not structure), so
    the Ambassador's one command covers reading too (the owner's order, 2026-11-04)."""

    atom: str
    chunk: int | None = None


# ── connectives, adjectives, the modality ──────────────────────────────────────────────────────


@dataclass(frozen=True)
class And:
    """`and`: the Schur product on fields, intersection on regions, a field masked by a region."""

    left: Node
    right: Node


@dataclass(frozen=True)
class Or:
    """`or`: the convex mixture of fields, the mean of the chain's disjuncts (one n-ary
    operation, whatever the grouping); the union of regions."""

    left: Node
    right: Node


@dataclass(frozen=True)
class Then:
    """`then`: the left clause's region masks the right clause."""

    left: Node
    right: Node


@dataclass(frozen=True)
class Within:
    """`within <region>`: the adjective — a congruence on a kernel, zero outside on a field,
    intersection on a region (QSA-2)."""

    body: Node
    region: Node


@dataclass(frozen=True)
class Over:
    """`over <strata>`: the strata a clause reads (the scope's `Σ`)."""

    body: Node
    strata: tuple[str, ...]


@dataclass(frozen=True)
class AsOf:
    """`as of "<cut>"`: the index of the reading (CN-1), never a letter."""

    body: Node
    cut: str


@dataclass(frozen=True)
class EdgeHyp:
    """`assume <rel> <a> <b> [±w]`: add (or weaken, for a negative `w`) an edge."""

    rel: Rel
    a: str
    b: str
    weight: float = 1.0


@dataclass(frozen=True)
class SeverHyp:
    """`assume sever <rel> <a> <b>`: remove an edge."""

    rel: Rel
    a: str
    b: str


@dataclass(frozen=True)
class ContradictHyp:
    """`assume contradict <a> <b>`: a negative signed relation edge between two notes."""

    a: str
    b: str


Hypothesis = EdgeHyp | SeverHyp | ContradictHyp


@dataclass(frozen=True)
class Assume:
    """`assume <hypothesis> in <sentence>`: the modality. The body is evaluated on the perturbed
    graph, its clauses require the overlay stratum, and the result is a `Hyp`."""

    hypothesis: Hypothesis
    body: Node


# ── the ingress: a script, the action sort (dn-ingress-language §E6) ─────────────────────────────


@dataclass(frozen=True)
class Do:
    """`do <script>`: the action sort, a whole sentence. Its value is a receipt, and what it writes
    lands later, so nothing reads after it in the same sentence. The request is a library call or
    a script inline (`core/sentence/script.py`); `requirements` are what the checking pass found
    it must have admitted (R1), filled in when it is compiled (`core/sentence/script_check.py`)."""

    request: Request
    text: str = ""
    requirements: tuple[Requirement, ...] = ()


Node = (
    Near | Diffuse | Far | Reach | Relate | Top | AtLeast | Not | Minus | Trace | Walk | Witness
    | Read | And | Or | Then | Within | Over | AsOf | Assume | Do
)


def describe_request(r: Request) -> str:
    """One line naming a request, as the plan and a refusal render it: the call with its
    arguments, a string by its length as the query log keeps it (a capture's text never travels
    past the request file), or the inline script's size, never its text."""
    from core.sentence.script import CallScript

    def arg(v: object) -> str:
        return f'"<{len(v)}>"' if isinstance(v, str) else repr(v)

    if isinstance(r, CallScript):
        parts = [arg(a.value) for a in r.args] + [f"{k}: {arg(v.value)}" for k, v in r.kwargs]
        return f"{r.name}({', '.join(parts)})"
    n = len(r.script.body)
    return f"{{ {n} statement{'s' if n != 1 else ''} }}"


def walk(node: Node) -> Iterator[Node]:
    """Every node of a term, the term first, then its operands depth first (a hypothesis and a
    request are a node's data, not its operands)."""
    yield node
    for f in fields(node):
        child = getattr(node, f.name)
        if isinstance(child, Node):  # type: ignore[arg-type]
            yield from walk(child)


def describe(h: Hypothesis) -> str:
    """One line naming an assumption, for the `Hyp` type and the plan's explanation."""
    if isinstance(h, EdgeHyp):
        sign = "+" if h.weight >= 0 else "-"
        return f"{h.rel.value} {h.a!r} {h.b!r} {sign}{abs(h.weight):g}"
    if isinstance(h, SeverHyp):
        return f"sever {h.rel.value} {h.a!r} {h.b!r}"
    return f"contradict {h.a!r} {h.b!r}"
