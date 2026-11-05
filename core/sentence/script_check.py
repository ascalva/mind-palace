"""The door's language: its types, and the checking pass (dn-door-language §E12).

The types carry the label sets of §E3: `str⟨L⟩` and `content⟨L⟩` for the strings and bytes whose
label is one of `L`, lists, the records a source's items and a place's entries are, sources,
sentences, functions. The pass interprets a script over these types: an item's fields carry its
source's labels, a projection keeps its operand's, anything composed is `{observed}`, and where
two types meet (a list's elements, `first`'s arguments, a function's returns) their label sets
join by union, so an inferred set only grows. A function is checked at each call with the types
it is called with, which is sound because nothing recurses; a body checked once with some types
is not checked again with the same ones, and the pass as a whole is bounded (`MAX_CHECK_STEPS`),
so no script costs the surface or the drain more than a bounded check. Stored, a string is
composed whatever it was read off: only content keeps an item's label. Soundness: a value's
label at run time is in its type's set (DOR-18, `formal/Palace/Script.lean::label_typed`), so R2
is decided here wherever the set is known, and the writer's run-time check is the second wall.

The pass also resolves every name to its binding, refuses a name used before it is bound, checks
each place, job and source a script names against the palace's table, parses each nested
sentence with its captures in place, and collects what admission needs (R1): the places a script
writes, the jobs it starts, the relation store if it links.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol

from core.sentence import script as S
from core.sentence.grammar import ParseError
from core.sentence.interpret import BUILTINS, MAX_CALLS, OBSERVED, ScriptError

Labels = frozenset[str] | None          # None: not known here; the writer decides

MAX_CHECK_STEPS = 200_000               # the nodes one checking pass may visit


# ── the types ───────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class T:
    """A type. `kind` names it; the fields say what it holds."""

    kind: str                            # any int bool none str content list item entry hit
    labels: Labels = None                # map record source sentence fn
    elem: T | None = None                # a list's element, a map's value
    of: str = ""                         # a source's or a place's name
    fn: S.Fn | None = None               # a function's definition
    scope: Mapping[str, T] = field(default_factory=dict)    # what it closed over

    def __repr__(self) -> str:
        ls = "" if self.labels is None else "⟨" + ",".join(sorted(self.labels)) + "⟩"
        inner = f"[{self.elem!r}]" if self.elem is not None else ""
        of = f"({self.of})" if self.of else ""
        return f"{self.kind}{ls}{inner}{of}"


ANY = T("any")
INT, BOOL, NONE = T("int"), T("bool"), T("none")
OBS = frozenset({OBSERVED})


def _union(a: Labels, b: Labels) -> Labels:
    return None if a is None or b is None else a | b


def join(a: T, b: T) -> T:
    """Where two types meet: the same kind joins its labels and elements; `none` gives way to the
    other (a missing field); different kinds are `any`."""
    if a.kind == "none":
        return b
    if b.kind == "none":
        return a
    if a.kind != b.kind or a.kind in ("any", "fn"):
        return ANY
    elem = join(a.elem, b.elem) if a.elem is not None and b.elem is not None else (a.elem or b.elem)
    return T(a.kind, _union(a.labels, b.labels), elem, a.of if a.of == b.of else "")


def labels_of(t: T) -> Labels:
    """The label set a value of type `t` could be stored with: content keeps its item's labels, a
    string or an integer is composed when stored, whatever it was read off. An empty set is no
    knowledge: the writer decides."""
    match t.kind:
        case "content":
            return t.labels or None
        case "str" | "int":
            return OBS
    return None


def _key(t: T) -> Any:
    """A type as a key: what a function's check depends on. A function type is its definition and
    the scope it closed over, by identity: one definition closes over one scope, so its key is
    constant-sized however many functions that scope holds."""
    if t.fn is not None:
        return (t.kind, id(t.fn), id(t.scope))
    return (t.kind, t.labels, None if t.elem is None else _key(t.elem), t.of)


# ── the table, as the pass reads it ─────────────────────────────────────────────────────────

class TableView(Protocol):
    """What the pass needs of the palace's table."""

    def place_accepts(self, place: str) -> frozenset[str] | None: ...
    def job_known(self, job: str) -> bool: ...
    def source_readable(self, name: str, role: str) -> bool | None: ...
    def source_labels(self, name: str) -> frozenset[str] | None: ...


@dataclass(frozen=True)
class Requirement:
    """What a script needs admitted: a place it writes, a job it starts, the relation store."""

    kind: str          # "place" | "job" | "link"
    name: str


# ── the pass ────────────────────────────────────────────────────────────────────────────────

class _Return(Exception):
    pass


@dataclass
class _Env:
    names: dict[str, T]
    parent: _Env | None = None

    def lookup(self, n: str) -> T | None:
        e: _Env | None = self
        while e is not None:
            if n in e.names:
                return e.names[n]
            e = e.parent
        return None

    def flat(self) -> dict[str, T]:
        chain: list[_Env] = []
        e: _Env | None = self
        while e is not None:
            chain.append(e)
            e = e.parent
        out: dict[str, T] = {}
        for x in reversed(chain):
            out.update(x.names)
        return out


class Checker:
    """One checking pass over one script, under one role."""

    def __init__(self, view: TableView, role: str,
                 library: Callable[[str], S.Script] | None = None) -> None:
        self.view = view
        self.role = role
        self.library = library
        self.reqs: list[Requirement] = []
        self.calls: list[str] = []
        self.returns: list[list[T]] = []
        self.steps = 0
        self.checked: dict[Any, T] = {}         # a function's body, checked with these types

    def tick(self) -> None:
        self.steps += 1
        if self.steps > MAX_CHECK_STEPS:
            raise ScriptError(f"the script takes more than {MAX_CHECK_STEPS} steps to check; a "
                              "script is a few lines")

    def check(self, script: S.Script, params: Mapping[str, T] | None = None) -> list[Requirement]:
        names = {n: (params or {}).get(n, _lit_type(d)) for n, d in S.params(script)}
        self.block(script.body, _Env(names))
        return self.reqs

    # statements --------------------------------------------------------------------------

    def block(self, body: Sequence[S.Stmt], env: _Env) -> None:
        for s in body:
            self.stmt(s, env)

    def stmt(self, s: S.Stmt, env: _Env) -> None:
        self.tick()
        match s:
            case S.Param():
                return
            case S.Let(name=n, expr=e):
                env.names[n] = self.expr(e, env)
            case S.Fn(name=n):
                env.names[n] = T("fn", fn=s, scope=env.flat())
            case S.Return(expr=e):
                if not self.returns:
                    raise ScriptError("return outside a function")
                self.returns[-1].append(self.expr(e, env))
            case S.CallStmt(name=n, args=args, kwargs=kwargs):
                self.call_script(n, args, kwargs)
            case S.For(var=v, iter=it, body=body):
                xs = self.expr(it, env)
                self.block(body, _Env({v: self.elem(xs, f"for {v}")}, env))
            case S.If(cond=c, then=t, orelse=o):
                self.expr(c, env)
                self.block(t, _Env({}, env))
                self.block(o, _Env({}, env))
            case S.Store(content=c, at=a, ident=i, place=p, titled=ti):
                ct = self.expr(c, env)
                if ct.kind not in ("str", "content", "int", "any"):
                    raise ScriptError(f"store in {p!r}: content is bytes or a string, not {ct!r}")
                stored = labels_of(ct)
                if ti is not None and (stored is None or stored - OBS):
                    may = ("of a label not known here" if stored is None
                           else ", ".join(sorted(stored - OBS)))
                    raise ScriptError(f"store in {p!r} titled: content that may be {may} is "
                                      "titled by its item, not by a script (R2)")
                for what, x, kinds in (("at", a, ("str", "any")), ("as", i, ("str", "any", "none")),
                                       ("titled", ti, ("str", "any"))):
                    if x is not None and self.expr(x, env).kind not in kinds:
                        raise ScriptError(f"store {what}: a string")
                accepts = self.view.place_accepts(p)
                if accepts is None:
                    raise ScriptError(f"store in {p!r}: no such place")
                ls = labels_of(ct)
                if ls is not None and not ls <= accepts:
                    bad = ", ".join(sorted(ls - accepts))
                    raise ScriptError(f"store in {p!r}: the content may be {bad}, and {p!r} takes "
                                      f"only {', '.join(sorted(accepts))} (R2)")
                self.reqs.append(Requirement("place", p))
            case S.Retire(path=x, place=p):
                if self.expr(x, env).kind not in ("str", "any"):
                    raise ScriptError("retire: a path is a string")
                if self.view.place_accepts(p) is None:
                    raise ScriptError(f"retire in {p!r}: no such place")
                self.reqs.append(Requirement("place", p))
            case S.Link(a=a, b=b, relation=r):
                for side, x in (("from", a), ("to", b)):
                    if self.expr(x, env).kind not in ("entry", "any"):
                        raise ScriptError(f"link {side}: an entry of a place, `entry(…)`")
                if self.expr(r, env).kind not in ("str", "any"):
                    raise ScriptError("link: a relation is a string")
                self.reqs.append(Requirement("link", "relations"))
            case S.Run(job=j, args=args):
                for _, x in args:
                    self.expr(x, env)
                if not self.view.job_known(j):
                    raise ScriptError(f"run {j!r}: no such job")
                self.reqs.append(Requirement("job", j))

    def call_script(self, name: str, args: Sequence[S.Lit],
                    kwargs: Sequence[tuple[str, S.Lit]]) -> None:
        if self.library is None:
            raise ScriptError(f"call {name}: no library is open here")
        if name in self.calls:
            raise ScriptError(f"call {name}: a cycle of calls ({' → '.join([*self.calls, name])})")
        if len(self.calls) >= MAX_CALLS:
            raise ScriptError(f"call {name}: more than {MAX_CALLS} calls open")
        callee = self.library(name)
        declared = [n for n, _ in S.params(callee)]
        given = dict(zip(declared, (_lit_type(a) for a in args), strict=False))
        for k, v in kwargs:
            if k not in declared:
                raise ScriptError(f"call {name}: no parameter {k!r}")
            given[k] = _lit_type(v)
        self.calls.append(name)
        try:
            self.check(callee, given)
        finally:
            self.calls.pop()

    # expressions -------------------------------------------------------------------------

    def elem(self, t: T, where: str) -> T:
        if t.kind == "list":
            return t.elem or ANY
        if t.kind == "sentence":
            return T("hit")
        if t.kind == "any":
            return ANY
        raise ScriptError(f"{where}: ranges over a list or a sentence's hits, not {t!r}")

    def expr(self, e: S.Expr, env: _Env) -> T:
        self.tick()
        match e:
            case S.Lit(value=v):
                return _lit_type(S.Lit(v))
            case S.Name(id=n):
                t = env.lookup(n)
                if t is not None:
                    return t
                if n == "me":
                    return T("str", OBS)
                raise ScriptError(f"{n!r} is used before it is bound")
            case S.Sentence(text=text, captures=caps):
                return self.sentence(text, caps, env)
            case S.Field(obj=o, name=f):
                return _field(self.expr(o, env), f)
            case S.Index(obj=o, key=k):
                ot, kt = self.expr(o, env), self.expr(k, env)
                if ot.kind in ("list",):
                    if kt.kind not in ("int", "any"):
                        raise ScriptError("a list is indexed by an integer")
                    return ot.elem or ANY
                if ot.kind == "sentence":
                    return T("hit")
                if ot.kind == "map":
                    return ot.elem or ANY
                if ot.kind in ("record",):
                    return T("str", ot.labels)
                if ot.kind in ("item", "entry", "hit", "any", "none"):
                    return _field(ot, "") if ot.kind != "any" else ANY
                raise ScriptError(f"{ot!r} cannot be indexed")
            case S.Slice(obj=o, lo=lo, hi=hi):
                ot = self.expr(o, env)
                for x in (lo, hi):
                    if x is not None and self.expr(x, env).kind not in ("int", "any"):
                        raise ScriptError("a slice's bounds are integers")
                if ot.kind == "str":
                    return T("str", OBS)                # a slice is composed (§E3)
                if ot.kind in ("list", "any"):
                    return ot
                raise ScriptError(f"a slice is of a string or a list, not {ot!r}")
            case S.ListLit(items=items):
                el: T = NONE
                for x in items:
                    el = join(el, self.expr(x, env))
                return T("list", elem=None if el.kind == "none" else el)
            case S.Comp(expr=x, var=v, iter=it, cond=c):
                inner = _Env({v: self.elem(self.expr(it, env), f"[… for {v} in …]")}, env)
                if c is not None:
                    self.expr(c, inner)
                return T("list", elem=self.expr(x, inner))
            case S.Call(fn=fn, args=args, kwargs=kwargs):
                ft = env.lookup(fn)
                ats = [self.expr(a, env) for a in args]
                kts = {k: self.expr(v, env) for k, v in kwargs}
                if ft is not None:
                    if ft.kind != "fn" or ft.fn is None:
                        raise ScriptError(f"{fn}(…): {fn!r} is {ft!r}, not a function")
                    return self.call_fn(ft, ats, kts)
                return self.builtin(fn, args, ats, kts)
            case S.Not(expr=x):
                self.expr(x, env)
                return BOOL
            case S.BinOp(op=op, left=a, right=b):
                at, bt = self.expr(a, env), self.expr(b, env)
                if op == "+":
                    kinds = {at.kind, bt.kind}
                    if kinds <= {"int", "any"} and "int" in kinds:
                        return INT
                    if kinds <= {"str", "any"}:
                        return T("str", OBS)            # a concatenation is composed (§E3)
                    if kinds <= {"list", "any"} and "list" in kinds:
                        return T("list", elem=join(at.elem or NONE, bt.elem or NONE))
                    if "any" in kinds:
                        return ANY
                    raise ScriptError(f"{at!r} + {bt!r}: `+` joins two strings, two integers or "
                                      "two lists")
                return BOOL
        raise ScriptError(f"cannot type {e!r}")  # pragma: no cover

    def call_fn(self, ft: T, args: list[T], kwargs: dict[str, T]) -> T:
        fn = ft.fn
        assert fn is not None
        if kwargs:
            raise ScriptError(f"{fn.name}(…): a function takes its arguments in order")
        if len(args) != len(fn.params):
            raise ScriptError(f"{fn.name}(…) takes {len(fn.params)} argument(s), {len(args)} given")
        if len(self.calls) >= MAX_CALLS:
            raise ScriptError(f"{fn.name}(…): more than {MAX_CALLS} calls open")
        key = (_key(ft), tuple(_key(a) for a in args))
        if key in self.checked:
            return self.checked[key]
        self.calls.append(fn.name)
        self.returns.append([])
        try:
            self.block(fn.body, _Env(dict(zip(fn.params, args, strict=True)),
                                     _Env(dict(ft.scope))))
            rets = self.returns[-1]
        finally:
            self.returns.pop()
            self.calls.pop()
        out: T = NONE
        for r in rets:
            out = join(out, r)
        self.checked[key] = out
        return out

    def sentence(self, text: str, caps: Sequence[str], env: _Env) -> T:
        """A nested sentence: its captures bound, each a string, an integer or a sentence, and
        its text a sentence of the read half with each capture in place."""
        import re

        from core.sentence.grammar import is_request, parse

        if is_request(text):
            raise ScriptError("a nested sentence reads; a request does not nest")

        def placeholder(m: re.Match[str]) -> str:
            t = env.lookup(m.group(1))
            if t is None:
                raise ScriptError(f"${m.group(1)} in a sentence is not bound")
            if t.kind == "sentence":
                return '(near "placeholder")'
            if t.kind in ("str", "int", "any"):
                return '"placeholder"'
            raise ScriptError(f"${m.group(1)} in a sentence is {t!r}: a sentence takes a string, "
                              "an integer or another sentence")
        try:
            parse(re.sub(r"\$([A-Za-z_][A-Za-z0-9_]*)", placeholder, text))
        except ParseError as err:
            raise ScriptError(f"the nested sentence `{text}`: {err}") from None
        return T("sentence")

    def builtin(self, fn: str, args: Sequence[S.Expr], ats: list[T], kts: dict[str, T]) -> T:
        if fn not in BUILTINS:
            raise ScriptError(f"{fn}(…) is not a built-in function or a function in scope")
        match fn:
            case "source":
                name = args[0].value if args and isinstance(args[0], S.Lit) else None
                if isinstance(name, str):
                    ok = self.view.source_readable(name, self.role)
                    if ok is None:
                        raise ScriptError(f"source({name!r}): no such source")
                    if not ok:
                        raise ScriptError(f"source({name!r}): the role {self.role!r} may not open "
                                          "it")
                    return T("source", self.view.source_labels(name), of=name)
                return T("source")
            case "files" | "items":
                src = ats[0] if ats else ANY
                return T("list", elem=T("item", src.labels, of=src.of))
            case "file":
                src = ats[0] if ats else ANY
                return T("item", src.labels, of=src.of)
            case "exists":
                return BOOL
            case "stored":
                place = args[0].value if args and isinstance(args[0], S.Lit) else ""
                return T("list", elem=T("entry", of=str(place or "")))
            case "entry":
                place = args[0].value if args and isinstance(args[0], S.Lit) else ""
                return T("entry", of=str(place or ""))
            case "digest" | "str" | "iso":
                return T("str", OBS)
            case "len":
                return INT
            case "paths":
                el = ats[0].elem if ats and ats[0].elem is not None else ANY
                return T("list", elem=_field(el, "path"))
            case "unique_by":
                el = ats[0].elem if ats and ats[0].elem is not None else ANY
                return T("map", elem=el)
            case "first":
                out: T = NONE
                for t in ats:
                    out = join(out, t)
                return out
        return ANY  # pragma: no cover


def _lit_type(lit: S.Lit | None) -> T:
    if lit is None:
        return ANY                          # a parameter with no default: the caller's value
    v = lit.value
    if v is None:
        return NONE
    if isinstance(v, bool):
        return BOOL
    if isinstance(v, int):
        return INT
    return T("str", OBS)                    # a literal is composed (§E3)


def _field(t: T, f: str) -> T:
    """A field's type: an item's carry its source's labels (the content as content), an entry's
    and a hit's are the palace's account, observed."""
    match t.kind:
        case "item":
            if f == "content":
                return T("content", t.labels)
            if f in ("properties",):
                return T("record", t.labels)
            if f in ("tags", "links"):
                return T("list", elem=T("str", t.labels))
            if f in ("path", "title", "digest"):
                return T("str", t.labels)
            return ANY                       # a structured item's own fields
        case "entry":
            if f == "active":
                return BOOL
            return T("str", OBS)
        case "hit":
            return T("str", OBS)
        case "record":
            return T("str", t.labels)
        case "content":
            return T("str", OBS)
        case "none":
            return NONE
        case "source":
            return T("str", OBS)
    return ANY


def compile_request(do: Any, role: str, view: TableView | None = None,
                    library: Callable[[str], S.Script] | None = None) -> Any:
    """A `do` sentence checked under the speaking role: the library script it calls (its
    arguments bound as the evaluator will bind them) or its script inline, through the pass.
    Returns the `Do` with what admission needs."""
    from dataclasses import replace

    from core.sentence.interpret import bind_params

    if view is None:
        from core.ingest.table import build_table
        from core.kernel.config import get_config

        view = build_table(get_config())
    lib = library or S.load
    req = do.request
    if isinstance(req, S.CallScript):
        script = lib(req.name)
        bind_params(script, [a.value for a in req.args], {k: v.value for k, v in req.kwargs})
        params = {n: _lit_type(a) for n, a in zip([n for n, _ in S.params(script)], req.args,
                                                     strict=False)}
        params.update({k: _lit_type(v) for k, v in req.kwargs})
        checker = Checker(view, role, lib)
        checker.calls.append(req.name)
        reqs = checker.check(script, params)
    else:
        reqs = Checker(view, role, lib).check(req.script)
    return replace(do, requirements=tuple(dict.fromkeys(reqs)))


def check(script: S.Script, view: TableView, role: str,
          library: Callable[[str], S.Script] | None = None) -> list[Requirement]:
    """The checking pass: raises `ScriptError` naming the first failure; returns what admission
    needs."""
    return Checker(view, role, library).check(script)
