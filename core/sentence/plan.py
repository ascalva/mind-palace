"""The planner — the sentence's normal form, reached by rewrites that are theorems
(dn-query-sentence-algebra §2.7; `formal/Palace/Sentence.lean`).

A plan denotes what its sentence denotes, by construction: every rewrite below is one of the
proved identities, and the one rewrite the planner refuses is refused by a proved counterexample.

* `within` is pushed to the leaves: over `and` (`mask_hadamard`), over `or` (`mask_add`), through a
  positive `atleast` (`thresh_maskF`); adjectives stack by intersection (`mask_mask`).
* `within` is **not** pushed through `top` (`topk_maskF_ne`), nor through `far` (`1 − f` is not
  zero outside the region): ranking and reversal stay where the sentence put them.
* `and` and `or` are flattened and canonically ordered (`hadamard_comm`, `hadamard_assoc`);
  `then` is kept in order.
* `far far f = f`, `not not r = r`.

The intermediate form is this normalized term together with its clauses' scopes and the
assumptions in force (`Plan`); `explain` renders it as the plan that rides with the answer.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.query import Grant
from core.sentence import ast
from core.sentence.ast import Node
from core.sentence.grammar import parse
from core.sentence.precedents import DEFAULT, Precedents
from core.sentence.types import (
    Clause,
    Sort,
    check_admissible,
    clauses_of,
    hyps_of,
    typecheck,
)


@dataclass(frozen=True)
class Plan:
    """The intermediate form: the normalized term, its sort, its clauses and their scopes, the
    assumptions in force. A value: two sentences with the same plan mean the same thing."""

    sentence: str
    term: Node
    sort: Sort
    clauses: tuple[Clause, ...]
    hyps: tuple[str, ...]

    @property
    def is_inv(self) -> bool:
        return not self.hyps

    @property
    def modes(self) -> tuple[str, ...]:
        return tuple(sorted({c.mode.value for c in self.clauses}))

    def explain(self) -> str:
        """The plan as text: the term tree, then each clause's scope, then the assumptions."""
        lines = [f"plan ({self.sort.value}{'' if self.is_inv else ', Hyp'}):"]
        lines += _render(self.term, 1)
        lines.append("clauses:")
        lines += [f"  {c.describe()}" for c in self.clauses]
        if self.hyps:
            lines.append("assumptions:")
            lines += [f"  {h}" for h in self.hyps]
        return "\n".join(lines)


# ── normalization ──────────────────────────────────────────────────────────────────────────────


def normalize(node: Node) -> Node:
    """The normal form, by the proved identities (idempotent)."""
    out = _norm(node)
    return out


def _norm(node: Node) -> Node:
    match node:
        case ast.Far(field=f):
            inner = _norm(f)
            if isinstance(inner, ast.Far):
                return inner.field                    # 1 − (1 − f) = f
            return ast.Far(inner)
        case ast.Not(region=r):
            inner = _norm(r)
            if isinstance(inner, ast.Not):
                return inner.region
            return ast.Not(inner)
        case ast.Top(k=k, field=f):
            return ast.Top(k, _norm(f))
        case ast.AtLeast(t=t, field=f):
            return ast.AtLeast(t, _norm(f))
        case ast.Minus(left=a, right=b):
            return ast.Minus(_norm(a), _norm(b))
        case ast.And():
            return _flatten(node, ast.And)
        case ast.Or():
            return _flatten(node, ast.Or)
        case ast.Then(left=a, right=b):
            return ast.Then(_norm(a), _norm(b))
        case ast.Within(body=b, region=r):
            return _push_within(_norm(b), _norm(r))
        case ast.Over(body=b, strata=s):
            return ast.Over(_norm(b), s)
        case ast.AsOf(body=b, cut=c):
            return ast.AsOf(_norm(b), c)
        case ast.Assume(hypothesis=h, body=b):
            return ast.Assume(h, _norm(b))
        case _:
            return node


def _push_within(body: Node, region: Node) -> Node:
    """QSA-2 and QSA-4: the adjective to the leaves, stopping at `top` and `far`."""
    match body:
        case ast.Within(body=inner, region=r2):
            return _push_within(inner, _flatten(ast.And(r2, region), ast.And))   # mask_mask
        case ast.And(left=a, right=b):
            return _flatten(ast.And(_push_within(a, region), _push_within(b, region)), ast.And)
        case ast.Or(left=a, right=b):
            return _flatten(ast.Or(_push_within(a, region), _push_within(b, region)), ast.Or)
        case ast.AtLeast(t=t, field=f) if t > 0:
            return ast.AtLeast(t, _push_within(f, region))                        # thresh_maskF
        case _:
            return ast.Within(body, region)                        # top, far, a verb: stays


def _operands(node: Node, op: type[ast.And] | type[ast.Or]) -> list[Node]:
    if isinstance(node, op):
        return _operands(node.left, op) + _operands(node.right, op)
    return [node]


def _flatten(node: Node, op: type[ast.And] | type[ast.Or]) -> Node:
    """Flatten nested `and`/`or`, normalize the operands and order them canonically
    (commutativity and associativity of the Schur product and the sum)."""
    parts = [_norm(p) for p in _operands(node, op)]
    parts.sort(key=repr)
    out = parts[0]
    for p in parts[1:]:
        out = op(out, p)
    return out


# ── rendering ──────────────────────────────────────────────────────────────────────────────────


def _render(node: Node, indent: int) -> list[str]:
    pad = "  " * indent
    match node:
        case ast.Near(text=t):
            return [f"{pad}near {t!r}"]
        case ast.Diffuse(rel=r, atom=a, beta=b):
            beta = f" beta {b:g}" if b is not None else ""
            return [f"{pad}diffuse {r.value} from {a!r}{beta}"]
        case ast.Far(field=f):
            return [f"{pad}far"] + _render(f, indent + 1)
        case ast.Reach(rel=r, atom=a, depth=d, direction=dr):
            return [f"{pad}reach {r.value} from {a!r}" + (f" depth {d}" if d is not None else "")
                    + f" {dr.value}"]
        case ast.Relate(atom=a):
            return [f"{pad}relate {a!r}"]
        case ast.Top(k=k, field=f):
            return [f"{pad}top {k}"] + _render(f, indent + 1)
        case ast.AtLeast(t=t, field=f):
            return [f"{pad}atleast {t:g}"] + _render(f, indent + 1)
        case ast.Not(region=r):
            return [f"{pad}not"] + _render(r, indent + 1)
        case ast.Minus(left=a, right=b):
            return [f"{pad}minus"] + _render(a, indent + 1) + _render(b, indent + 1)
        case ast.Trace(atom=a, direction=d):
            return [f"{pad}trace {a!r} {d.value}"]
        case ast.Walk(atom=a, path=p, to=t, depth=d):
            return [f"{pad}walk from {a!r}" + (f" to {t!r}" if t else "") + f" via {p}"
                    + (f" depth {d}" if d is not None else "")]
        case ast.Witness(edge=e):
            return [f"{pad}witness {e!r}"]
        case ast.And(left=a, right=b):
            return [f"{pad}and"] + _render(a, indent + 1) + _render(b, indent + 1)
        case ast.Or(left=a, right=b):
            return [f"{pad}or"] + _render(a, indent + 1) + _render(b, indent + 1)
        case ast.Then(left=a, right=b):
            return [f"{pad}then"] + _render(a, indent + 1) + _render(b, indent + 1)
        case ast.Within(body=b, region=r):
            return [f"{pad}within"] + _render(b, indent + 1) + [f"{pad}  region:"] \
                + _render(r, indent + 2)
        case ast.Over(body=b, strata=s):
            return [f"{pad}over {' '.join(s)}"] + _render(b, indent + 1)
        case ast.AsOf(body=b, cut=c):
            return [f"{pad}as of {c!r}"] + _render(b, indent + 1)
        case ast.Assume(hypothesis=h, body=b):
            return [f"{pad}assume {ast.describe(h)} in"] + _render(b, indent + 1)
    return [f"{pad}{node!r}"]  # pragma: no cover


# ── the compiler's front half ──────────────────────────────────────────────────────────────────


def compile_sentence(text: str, grant: Grant | None = None, *,
                     precedents: Precedents = DEFAULT) -> Plan:
    """Parse, type, normalize and, with a grant, check admissibility: the plan.

    Raises `ParseError`, `SortError`, `AmbiguousSentence` or `IllScopedSentence`, each naming its
    cause; a sentence that compiles is well-formed, well-sorted and admissible."""
    tree = parse(text)
    sort = typecheck(tree)
    term = normalize(tree)
    clauses = clauses_of(term, precedents=precedents)
    if grant is not None:
        check_admissible(term, grant, precedents=precedents)
    return Plan(sentence=text, term=term, sort=sort, clauses=clauses, hyps=hyps_of(term))
