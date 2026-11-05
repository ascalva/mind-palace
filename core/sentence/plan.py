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

import re
from dataclasses import dataclass

from core.query import Grant
from core.sentence import ast
from core.sentence.ast import Node
from core.sentence.grammar import ParseError, parse
from core.sentence.precedents import DEFAULT, Precedents
from core.sentence.trace import Trace
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


def normalize(node: Node, trace: Trace | None = None) -> Node:
    """The normal form, by the proved identities (idempotent); with a trace, every rewrite that
    changed the term is noted with the law it rests on."""
    return _norm(node, trace)


def _note(t: Trace | None, what: str, law: str = "") -> None:
    if t is not None:
        t.note("plan", what, law)


def _norm(node: Node, t: Trace | None = None) -> Node:
    match node:
        case ast.Far(field=f):
            inner = _norm(f, t)
            if isinstance(inner, ast.Far) and isinstance(inner.field, ast.Or):
                # 1 − (1 − f) = f, but an `or` let out would join an enclosing `or` chain and
                # change its weights, as `within` would (QSA-2): it stays under the reversals
                _note(t, "far far stays over `or`: its disjuncts would join an enclosing mixture "
                         "and change its weights")
                return ast.Far(inner)
            if isinstance(inner, ast.Far):
                _note(t, "far far f → f: the bounded reversal is an involution")
                return inner.field                    # 1 − (1 − f) = f
            return ast.Far(inner)
        case ast.Not(region=r):
            inner = _norm(r, t)
            if isinstance(inner, ast.Not):
                _note(t, "not not r → r: the complement is an involution")
                return inner.region
            return ast.Not(inner)
        case ast.Top(k=k, field=f):
            return ast.Top(k, _norm(f, t))
        case ast.AtLeast(t=th, field=f):
            return ast.AtLeast(th, _norm(f, t))
        case ast.Minus(left=a, right=b):
            return ast.Minus(_norm(a, t), _norm(b, t))
        case ast.And():
            return _flatten(node, ast.And, t)
        case ast.Or():
            return _flatten(node, ast.Or, t)
        case ast.Then(left=a, right=b):
            return ast.Then(_norm(a, t), _norm(b, t))
        case ast.Within(body=b, region=r):
            return _push_within(_norm(b, t), _norm(r, t), t)
        case ast.Over(body=b, strata=s):
            return ast.Over(_norm(b, t), s)
        case ast.AsOf(body=b, cut=c):
            return ast.AsOf(_norm(b, t), c)
        case ast.Assume(hypothesis=h, body=b):
            return ast.Assume(h, _norm(b, t))
        case _:
            return node


def _push_within(body: Node, region: Node, t: Trace | None = None) -> Node:
    """QSA-2 and QSA-4: the adjective to the leaves, stopping at `top` and `far`."""
    match body:
        case ast.Within(body=inner, region=r2):
            _note(t, "within within → one mask: the regions met by ∩", "QSA-2")
            return _push_within(inner, _flatten(ast.And(r2, region), ast.And, t), t)   # mask_mask
        case ast.And(left=a, right=b):
            _note(t, "within pushed through `and` to both sides: the mask distributes over the "
                     "Schur product", "QSA-2")
            return _flatten(ast.And(_push_within(a, region, t), _push_within(b, region, t)),
                            ast.And, t)
        case ast.Or():
            # the mask distributes over the mean, but pushed in, the disjuncts would join an
            # enclosing `or` chain and change its weights: it stays over the mixture
            _note(t, "within stays over `or`: the masked disjuncts would join an enclosing "
                     "mixture and change its weights", "QSA-2")
            return ast.Within(body, region)
        case ast.AtLeast(t=th, field=f) if th > 0:
            _note(t, f"within under `atleast {th:g}`: a positive threshold commutes with the mask",
                  "QSA-4")
            return ast.AtLeast(th, _push_within(f, region, t))                    # thresh_maskF
        case ast.Top():
            _note(t, "within stays over `top`: ranking does not commute with the mask", "QSA-4")
            return ast.Within(body, region)
        case ast.Far():
            _note(t, "within stays over `far`: the reversal does not commute with the mask")
            return ast.Within(body, region)
        case _:
            return ast.Within(body, region)                        # a verb: stays


def _operands(node: Node, op: type[ast.And] | type[ast.Or]) -> list[Node]:
    if isinstance(node, op):
        return _operands(node.left, op) + _operands(node.right, op)
    return [node]


def _flatten(node: Node, op: type[ast.And] | type[ast.Or], t: Trace | None = None) -> Node:
    """Flatten nested `and`/`or`, normalize the operands and order them canonically: the Schur
    product is commutative and associative, and `or` is the mean of its chain's disjuncts, so
    neither the grouping nor the order of either changes the answer."""
    parts = [_norm(p, t) for p in _operands(node, op)]
    ordered = sorted(parts, key=repr)
    if t is not None:
        done = ([f"flattened {len(parts)} operands"] if len(parts) > 2 else []) + \
            (["ordered canonically"] if ordered != parts else [])
        if done:
            name, kind = (("and", "the Schur product is commutative and associative")
                          if op is ast.And else
                          ("or", "the mixture is the mean of the disjuncts, whatever their "
                                 "grouping or order"))
            _note(t, f"`{name}` {' and '.join(done)}: {kind}", "QSA-1")
    out = ordered[0]
    for p in ordered[1:]:
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
        case ast.Read(atom=a, chunk=c):
            return [f"{pad}read {a!r}" + (f" chunk {c}" if c is not None else "")]
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
        case ast.Do(command=c):
            return [f"{pad}do {ast.describe_command(c)}"]
    return [f"{pad}{node!r}"]  # pragma: no cover


# ── the compiler's front half ──────────────────────────────────────────────────────────────────


_COUNT = re.compile(r"\{(\d+)(?:,(\d*))?\}")


def check_bounds(node: Node, precedents: Precedents = DEFAULT) -> None:
    """The most a sentence may ask (the ledger's bounds): `reach` and `walk` depth, `top k`, and a
    path's counts. Refused when compiled, with the bound named, so no sentence can hold the
    surfaces, which answer one call at a time (the review of 2026-11-05)."""
    p = precedents
    for n in ast.walk(node):
        match n:
            case ast.Reach(depth=d) | ast.Walk(depth=d) if d is not None and d > p.max_depth:
                verb = "reach" if isinstance(n, ast.Reach) else "walk"
                raise ParseError(f"{verb} depth {d}: at most {p.max_depth} hops (the bound in "
                                 "docs/query/precedents.md)")
            case ast.Top(k=k) if k > p.max_k:
                raise ParseError(f"top {k}: at most {p.max_k} (the bound in "
                                 "docs/query/precedents.md)")
            case ast.Walk(path=path):
                from core.sentence.automaton import PathError, compile_path

                for m in _COUNT.finditer(path):
                    if max(int(m.group(1)), int(m.group(2) or 0)) > p.max_repeat:
                        raise ParseError(f"via {path}: a count {m.group(0)} past "
                                         f"{p.max_repeat} (the bound in docs/query/precedents.md)")
                try:                    # the path is the sentence's syntax: refused with it
                    compile_path(path)
                except PathError as e:
                    raise ParseError(str(e)) from e


def compile_sentence(text: str, grant: Grant | None = None, *,
                     precedents: Precedents = DEFAULT, trace: Trace | None = None) -> Plan:
    """Parse, type, normalize and, with a grant, check admissibility: the plan. With a trace,
    the work is noted: the parse and its sort, the rewrites, the clauses' scopes, the admission.

    Raises `ParseError` (a bound past the ledger's among them), `SortError`, `AmbiguousSentence`
    or `IllScopedSentence`, each naming its cause; a sentence that compiles is well-formed,
    within bounds, well-sorted and admissible."""
    tree = parse(text)
    check_bounds(tree, precedents)
    sort = typecheck(tree)
    if trace is not None:
        trace.note("parse", "parsed:\n" + "\n".join(_render(tree, 1)))
        trace.note("parse", f"sort: {sort.value} — the sentence is well-sorted")
    term = normalize(tree, trace)
    clauses = clauses_of(term, precedents=precedents)
    if trace is not None:
        if repr(term) == repr(tree):
            trace.note("plan", "already in normal form: no rewrite applied")
        else:
            trace.note("plan", "normal form:\n" + "\n".join(_render(term, 1)))
        for c in clauses:
            trace.note("plan", f"clause {c.describe()}", "QSA-8")
    if grant is not None:
        check_admissible(term, grant, precedents=precedents)
        if trace is not None:
            trace.note("plan", f"admissible: each of the {len(clauses)} clauses' required scopes "
                               "lies under a granted plane", "QSA-5")
    return Plan(sentence=text, term=term, sort=sort, clauses=clauses, hyps=hyps_of(term))
