"""The ingress language: its values, the checker, and the metered evaluator (dn-ingress-language §E1
to §E5, §E10).

Evaluation reads and writes nothing. A script's value is a **plan**, the effects it would have
with their content resolved; the writer (`core/ingest/writer.py`) lands a plan. The evaluator
reads the palace only through a `Palace` the caller hands it, so this module opens no store and
names no source: the palace's table (`core/ingest/table.py`) does both.

The values the palace's labels ride on (§E3), held by the evaluator and never by a script:

- `Content`: bytes with a label and an origin. A script can store it, compare it and take its
  digest; no expression reads, compares or changes its label.
- `OStr`: a string read off an item or an entry, keeping the item's label and origin. Any
  operation on it returns a plain `str`, so a composed string is the observed label's by
  construction, whoever composes it.

Every operation charges the meter; a request out of budget stops, and since evaluation has no
effect, it lands nothing (§E10).
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence, Sized
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol

from core.kernel.provenance import Provenance
from core.sentence import script as S

OBSERVED = Provenance.OBSERVED.value       # the label of whatever a script composes


class ScriptError(ValueError):
    """A script that cannot be evaluated: a name unbound, a value of the wrong kind, a bound
    passed. The message says which, and where."""


class OutOfGas(ScriptError):
    """The request's budget ran out before its plan was whole; nothing lands (§E10)."""


# ── the values ──────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Origin:
    """Where a projected value came from: an item of a source, or an entry of a place."""

    kind: str           # "item" | "entry"
    of: str             # the source's name, or the place's
    path: str           # the item's or the entry's path
    title: str = ""


@dataclass(frozen=True)
class Content:
    """Bytes with a label and an origin, opaque to the language."""

    data: bytes
    label: str
    origin: Origin | None
    oversize: int = 0           # an item over its source's cap: its size; its bytes never read

    @property
    def digest(self) -> str:
        return "" if self.oversize else hashlib.sha256(self.data).hexdigest()

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Content) and other.data == self.data

    def __hash__(self) -> int:
        return hash(self.data)


class OStr(str):
    """A string read off an item or an entry. Its value is the string's; it keeps the item's
    label and origin, so an identity can be shown to be the item's own (R6) and a property
    stored as content keeps its item's label (a projection, ING-13). Every `str` operation
    returns a plain `str`: a composed string is observed."""

    label: str
    origin: Origin

    def __new__(cls, value: str, label: str, origin: Origin) -> OStr:
        s = super().__new__(cls, value)
        s.label = label
        s.origin = origin
        return s


class Record(Mapping[str, Any]):
    """A read-only record: an item, an entry, a parsed property set. A missing field is `none`."""

    def __init__(self, fields: Mapping[str, Any]) -> None:
        self._f = dict(fields)

    def __getitem__(self, key: str) -> Any:
        return self._f[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._f)

    def __len__(self) -> int:
        return len(self._f)

    def __repr__(self) -> str:
        return f"Record({', '.join(sorted(self._f))})"


@dataclass(frozen=True)
class Handle:
    """A source the speaker opened: its name in the palace's table, and its root."""

    name: str
    root: str


@dataclass(frozen=True)
class Closure:
    """A function and the scope it closed over, by value: the names bound where it was defined,
    which never include its own name (§E11)."""

    fn: S.Fn
    scope: Mapping[str, Any]


class SentenceV:
    """A nested read sentence with its captures resolved where it was written. Its hits are read
    when a value is needed (a loop, an index, a length), once."""

    def __init__(self, text: str) -> None:
        self.text = text
        self._hits: list[Record] | None = None

    def hits(self, palace: Palace, meter: Meter) -> list[Record]:
        if self._hits is None:
            meter.charge("query")
            self._hits = palace.query(self.text)
        return self._hits


# ── the plan ────────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Naming:
    """How a store names a new path's identity (R6): its own, one read off the item stored (`prop`,
    with the value), one held at another path (`held`, with that path), or a plain string
    (`named`), which the writer admits only when it is the path itself."""

    kind: str                     # "own" | "prop" | "held" | "named"
    value: str | None = None
    origin: Origin | None = None


@dataclass(frozen=True)
class StoreEff:
    path: str
    content: Content
    place: str
    naming: Naming
    title: str


@dataclass(frozen=True)
class RetireEff:
    path: str
    place: str


@dataclass(frozen=True)
class LinkEff:
    a: str               # the entries' paths
    b: str
    a_digest: str
    b_digest: str
    relation: str


@dataclass(frozen=True)
class RunEff:
    job: str
    args: tuple[tuple[str, str | int | bool | None], ...]


Effect = StoreEff | RetireEff | LinkEff | RunEff


# ── the palace, as the evaluator reads it ───────────────────────────────────────────────────

class Palace(Protocol):
    """What a script reads through: the palace's table's sources and places, opened under the
    speaker's role. The daemon hands the evaluator one; a test hands it a fake. `files` and `items`
    may yield lazily: the evaluator charges each item as it arrives, so a request out of budget
    stops reading at the item that ran it out, not after the whole source."""

    def open(self, name: str) -> Handle: ...
    def files(self, h: Handle) -> Iterable[Record]: ...
    def file(self, h: Handle, path: str) -> Record: ...
    def exists(self, h: Handle, path: str) -> bool: ...
    def items(self, h: Handle) -> Iterable[Record]: ...
    def stored(self, place: str, prefix: str) -> list[Record]: ...
    def query(self, sentence: str) -> list[Record]: ...



# ── the meter ───────────────────────────────────────────────────────────────────────────────

# The price of each operation, in units of work, one unit the time of one evaluation step
# (§E10). Measured on fixtures, never assumed: `eval/ingress_gas.py` measures them, and
# `docs/query/precedents.md` records the table and the run it came from (2026-11-05: a step
# 0.30 µs; the embeds on the palace's embedder). Rounded to two figures.
PRICES: Mapping[str, int] = {
    "step": 1,          # a statement, an expression node, a loop iteration
    "item": 270,        # an item read from a source (a file opened and parsed, a record)
    "kib": 75,          # a kibibyte of an item's content read
    "entry": 22,        # an entry read from a place
    "effect": 10_000,   # an effect added to the plan, and the writer's two checks of it
    "write": 140_000,   # an effect that will write (a store not unchanged, a retire, a link, a run)
    "query": 360_000,   # a read sentence: not measured, one embed (its text's) as its floor
    "embed": 360_000,   # an atom the plane does not hold, embedded when the plan lands
}


@dataclass
class Meter:
    """Work charged against a budget; out of budget, `OutOfGas`."""

    budget: int
    used: int = 0
    by: dict[str, int] = field(default_factory=dict)

    def charge(self, what: str, units: int = 1) -> None:
        cost = PRICES[what] * units
        self.used += cost
        self.by[what] = self.by.get(what, 0) + cost
        if self.used > self.budget:
            raise OutOfGas(f"out of budget at {what}: {self.used} units of {self.budget}; "
                           "nothing lands")


# ── the evaluator ───────────────────────────────────────────────────────────────────────────

BUILTINS = frozenset({
    "source", "files", "file", "exists", "items", "stored", "entry", "digest", "len", "str",
    "paths", "unique_by", "first", "iso",
})
MAX_CALLS = 64                      # library scripts and functions open at once

MAX_EFFECTS = 100_000               # effects one plan may hold
MAX_STRING = 1 << 20                # characters a composed string may have
MAX_LIST = 1_000_000                # elements a composed list may have
MAX_SENTENCE = 32 * 1024            # characters a nested sentence may have, its captures in place
_PER_STEP = 64                      # characters (or bytes) one step pays for when work is sized


def _truthy(v: Any) -> bool:
    if isinstance(v, (Content, Handle, Record, Closure, SentenceV)):
        return True
    return bool(v)


class _Return(Exception):
    def __init__(self, value: Any) -> None:
        self.value = value


class Scope:
    """A block's names, over the enclosing block's: a `let` binds here, a lookup walks out."""

    def __init__(self, parent: Scope | None = None,
                 names: Mapping[str, Any] | None = None) -> None:
        self.parent = parent
        self.names: dict[str, Any] = dict(names or {})

    def lookup(self, n: str) -> tuple[bool, Any]:
        s: Scope | None = self
        while s is not None:
            if n in s.names:
                return True, s.names[n]
            s = s.parent
        return False, None

    def flat(self) -> dict[str, Any]:
        """Every name visible here, the innermost binding of each: what a closure keeps."""
        chain: list[Scope] = []
        s: Scope | None = self
        while s is not None:
            chain.append(s)
            s = s.parent
        out: dict[str, Any] = {}
        for sc in reversed(chain):
            out.update(sc.names)
        return out


class Evaluator:
    """One evaluation of one script, under one role, against one palace, metered. `library`
    loads a library script by name, for `call`."""

    def __init__(self, palace: Palace, role: str, meter: Meter,
                 library: Callable[[str], S.Script] | None = None) -> None:
        self.palace = palace
        self.role = role
        self.meter = meter
        self.library = library
        self.plan: list[Effect] = []
        self.calls: list[str] = []
        self.read_bytes = 0                 # the content read so far, charged by the KiB
        self._places: dict[str, list[Record]] = {}   # a place's entries, read once
        self._index: dict[str, dict[str, dict[str, list[Record]]]] = {}

    # entry point -------------------------------------------------------------------------

    def run(self, script: S.Script, args: Sequence[Any] = (),
            kwargs: Mapping[str, Any] | None = None, *, name: str = "") -> list[Effect]:
        scope = Scope(names=bind_params(script, args, kwargs))
        if name:
            self.calls.append(name)
        try:
            self.block(script.body, scope)
        except _Return:
            raise ScriptError("return outside a function") from None
        finally:
            if name:
                self.calls.pop()
        return self.plan

    # statements --------------------------------------------------------------------------

    def block(self, body: Sequence[S.Stmt], scope: Scope) -> None:
        for s in body:
            self.meter.charge("step")
            self.stmt(s, scope)

    def stmt(self, s: S.Stmt, scope: Scope) -> None:
        match s:
            case S.Param():
                return                                   # bound before the body ran
            case S.Let(name=n, expr=e):
                scope.names[n] = self.eval(e, scope)
            case S.Fn(name=n):
                scope.names[n] = Closure(s, scope.flat())   # its own name is not yet bound
            case S.Return(expr=e):
                raise _Return(self.eval(e, scope))
            case S.CallStmt(name=n, args=args, kwargs=kwargs):
                self.call_script(n, [a.value for a in args], {k: v.value for k, v in kwargs})
            case S.For(var=v, iter=it, body=body):
                xs = self.listish(self.eval(it, scope), f"for {v}")
                for x in xs:
                    self.meter.charge("step")
                    self.block(body, Scope(scope, {v: x}))
            case S.If(cond=c, then=t, orelse=o):
                self.block(t if _truthy(self.eval(c, scope)) else o, Scope(scope))
            case S.Store():
                self.store(s, scope)
            case S.Retire(path=p, place=place):
                path = self.eval(p, scope)
                if not isinstance(path, str):
                    raise ScriptError(f"retire: a path is a string, not {_kind(path)}")
                self.add(RetireEff(str(path), place))
            case S.Link(a=a, b=b, relation=r):
                ea, eb, rel = self.eval(a, scope), self.eval(b, scope), self.eval(r, scope)
                for side, e in (("from", ea), ("to", eb)):
                    d = e.get("digest") if isinstance(e, Record) else None
                    if not (isinstance(d, OStr) and d.origin.kind == "entry"):
                        raise ScriptError(f"link {side}: an entry of a place (`entry(…)`), not "
                                          f"{_kind(e)}")
                if not isinstance(rel, str):
                    raise ScriptError(f"link: a relation is a string, not {_kind(rel)}")
                self.add(LinkEff(str(ea["path"]), str(eb["path"]), str(ea["digest"]),
                                 str(eb["digest"]), str(rel)))
            case S.Run(job=job, args=args):
                vals: list[tuple[str, str | int | bool | None]] = []
                for k, e in args:
                    v = self.eval(e, scope)
                    if v is not None and not isinstance(v, (str, int, bool)):
                        raise ScriptError(f"run {job}: {k} is a string, an integer or a "
                                          f"boolean, not {_kind(v)}")
                    vals.append((k, str(v) if isinstance(v, OStr) else v))
                self.add(RunEff(job, tuple(vals)))

    def call_script(self, name: str, args: Sequence[Any], kwargs: Mapping[str, Any]) -> None:
        if self.library is None:
            raise ScriptError(f"call {name}: no library is open here")
        if name in self.calls:
            raise ScriptError(f"call {name}: a cycle of calls ({' → '.join([*self.calls, name])})")
        if len(self.calls) >= MAX_CALLS:
            raise ScriptError(f"call {name}: more than {MAX_CALLS} calls open at once")
        callee = self.library(name)
        self.meter.charge("step")
        self.calls.append(name)
        try:
            self.block(callee.body, Scope(names=bind_params(callee, args, kwargs)))
        except _Return:
            raise ScriptError(f"call {name}: return outside a function") from None
        finally:
            self.calls.pop()

    def call_closure(self, c: Closure, args: list[Any], kwargs: dict[str, Any]) -> Any:
        fn = c.fn
        if kwargs:
            raise ScriptError(f"{fn.name}(…): a function takes its arguments in order")
        if len(args) != len(fn.params):
            raise ScriptError(f"{fn.name}(…) takes {len(fn.params)} argument(s), "
                              f"{len(args)} given")
        if len(self.calls) >= MAX_CALLS:
            raise ScriptError(f"{fn.name}(…): more than {MAX_CALLS} calls open at once")
        self.meter.charge("step")
        self.calls.append(fn.name)
        try:
            self.block(fn.body, Scope(Scope(names=c.scope), dict(zip(fn.params, args,
                                                                         strict=True))))
        except _Return as r:
            return r.value
        finally:
            self.calls.pop()
        return None

    def listish(self, v: Any, where: str) -> list[Any]:
        if isinstance(v, SentenceV):
            return list(v.hits(self.palace, self.meter))
        if not isinstance(v, list):
            raise ScriptError(f"{where}: ranges over a list or a sentence's hits, not "
                              f"{_kind(v)}")
        return v

    def add(self, eff: Effect) -> None:
        self.meter.charge("effect")
        if len(self.plan) >= MAX_EFFECTS:
            raise ScriptError(f"a plan holds at most {MAX_EFFECTS} effects")
        self.plan.append(eff)

    def store(self, s: S.Store, env: Scope) -> None:
        v = self.eval(s.content, env)
        if isinstance(v, Content):
            content = v                     # an item's own bytes, its label and its origin
        elif isinstance(v, (str, int)) and not isinstance(v, bool):
            # a string, even one read off an item (its title, its digest, a field), is not the
            # item's bytes: stored, it is composed, observed and of no origin (§E3)
            content = Content(str(v).encode("utf-8"), OBSERVED, None)
        else:
            raise ScriptError(f"store: content is bytes or a string, not {_kind(v)}")
        if len(content.data) >= 1024:
            self.meter.charge("kib", len(content.data) // 1024)   # the writer chunks and lands it
        if s.at is not None:
            at = self.eval(s.at, env)
            if not isinstance(at, str):
                raise ScriptError(f"store at: a path is a string, not {_kind(at)}")
            path = str(at)
        elif content.origin is not None and content.origin.kind == "item":
            path = content.origin.path
        else:
            raise ScriptError("store: composed content has no origin; say where with `at`")
        naming = Naming("own")
        if s.ident is not None:
            ident = self.eval(s.ident, env)
            if isinstance(ident, OStr) and ident.origin.kind == "id":
                naming = Naming("prop", str(ident), ident.origin)     # the item's declared id
            elif isinstance(ident, OStr) and ident.origin.kind == "entry":
                naming = Naming("held", ident.origin.path, ident.origin)   # a path's identity
            elif isinstance(ident, str):
                naming = Naming("named", ident)
            elif ident is not None:
                raise ScriptError(f"store as: an identity is a string, not {_kind(ident)}")
        if s.titled is not None:
            t = self.eval(s.titled, env)
            if not isinstance(t, str):
                raise ScriptError(f"store titled: a title is a string, not {_kind(t)}")
            title = str(t)
        elif content.origin is not None and content.origin.title:
            title = content.origin.title
        else:
            title = path
        self.add(StoreEff(path, content, s.place, naming, title))

    # expressions -------------------------------------------------------------------------

    def eval(self, e: S.Expr, env: Scope) -> Any:
        self.meter.charge("step")
        match e:
            case S.Lit(value=v):
                return v
            case S.Name(id=n):
                found, v = env.lookup(n)
                if found:
                    return v
                if n == "me":
                    return self.role
                raise ScriptError(f"{n!r} is not bound: a name is a `let`, a `fn`, a `for` "
                                  "variable, a parameter, or `me`")
            case S.Sentence(text=text, captures=caps):
                return SentenceV(self.resolve_sentence(text, caps, env))
            case S.Field(obj=o, name=f):
                return self.field(self.eval(o, env), f)
            case S.Index(obj=o, key=k):
                return self.index(self.eval(o, env), self.eval(k, env))
            case S.Slice(obj=o, lo=lo, hi=hi):
                v = self.eval(o, env)
                a = None if lo is None else self.eval(lo, env)
                b = None if hi is None else self.eval(hi, env)
                if not all(x is None or (isinstance(x, int) and not isinstance(x, bool))
                           for x in (a, b)):
                    raise ScriptError("a slice's bounds are integers")
                if isinstance(v, str):
                    return str(v)[a:b]
                if isinstance(v, list):
                    return v[a:b]
                raise ScriptError(f"a slice is of a string or a list, not {_kind(v)}")
            case S.ListLit(items=items):
                return [self.eval(x, env) for x in items]
            case S.Comp(expr=x, var=v, iter=it, cond=c):
                xs = self.listish(self.eval(it, env), f"[… for {v} in …]")
                out = []
                for item in xs:
                    self.meter.charge("step")
                    inner = Scope(env, {v: item})
                    if c is None or _truthy(self.eval(c, inner)):
                        out.append(self.eval(x, inner))
                return out
            case S.Call(fn=fn, args=args, kwargs=kwargs):
                vals = [self.eval(a, env) for a in args]
                kw = {k: self.eval(v, env) for k, v in kwargs}
                found, f = env.lookup(fn)
                if found:
                    if not isinstance(f, Closure):
                        raise ScriptError(f"{fn}(…): {fn!r} is {_kind(f)}, not a function")
                    return self.call_closure(f, vals, kw)
                return self.call(fn, vals, kw)
            case S.Not(expr=x):
                return not _truthy(self.eval(x, env))
            case S.BinOp(op="and", left=a, right=b):
                return _truthy(self.eval(a, env)) and _truthy(self.eval(b, env))
            case S.BinOp(op="or", left=a, right=b):
                return _truthy(self.eval(a, env)) or _truthy(self.eval(b, env))
            case S.BinOp(op=op, left=a, right=b):
                return self.binop(op, self.eval(a, env), self.eval(b, env))
        raise ScriptError(f"cannot evaluate {e!r}")  # pragma: no cover

    def resolve_sentence(self, text: str, caps: Sequence[str], env: Scope) -> str:  # noqa: ARG002
        """The sentence with each `$name` replaced: a nested sentence as itself in parentheses, a
        string or an integer as a quoted literal, never as syntax (§E11)."""
        from core.sentence.grammar import quote

        def value(name: str) -> str:
            found, v = env.lookup(name)
            if not found:
                raise ScriptError(f"${name} in a sentence is not bound")
            if isinstance(v, SentenceV):
                return f"({v.text})"
            if isinstance(v, str) or (isinstance(v, int) and not isinstance(v, bool)):
                return quote(str(v))
            raise ScriptError(f"${name} in a sentence is {_kind(v)}: a sentence takes a string, "
                              "an integer or another sentence")
        def one(m: re.Match[str]) -> str:
            out = value(m.group(1))
            if len(out) > MAX_SENTENCE:
                raise ScriptError(f"a nested sentence of more than {MAX_SENTENCE} characters")
            return out

        resolved = re.sub(r"\$([A-Za-z_][A-Za-z0-9_]*)", one, text)
        if len(resolved) > MAX_SENTENCE:
            raise ScriptError(f"a nested sentence of more than {MAX_SENTENCE} characters")
        self.meter.charge("step", len(resolved) // _PER_STEP)
        return resolved

    def field(self, v: Any, f: str) -> Any:
        if v is None:
            return None
        if isinstance(v, Record):
            return v.get(f)
        if isinstance(v, Content):
            if f == "digest":
                return v.digest
            if f == "path":
                return None if v.origin is None else v.origin.path
            raise ScriptError(f"content has fields `digest` and `path`, not {f!r}: its bytes "
                              "are stored as they are")
        if isinstance(v, Handle) and f == "root":
            return v.root
        raise ScriptError(f"{_kind(v)} has no field {f!r}")

    def index(self, v: Any, k: Any) -> Any:
        if v is None:
            return None
        if isinstance(v, SentenceV):
            v = v.hits(self.palace, self.meter)
        if isinstance(v, list):
            if not isinstance(k, int) or isinstance(k, bool):
                raise ScriptError("a list is indexed by an integer")
            return v[k] if -len(v) <= k < len(v) else None
        if isinstance(v, Record):
            if k is None:
                return None                             # a missing key: none (§E1)
            if not isinstance(k, str):
                raise ScriptError("a record is indexed by a string")
            return v.get(str(k))
        raise ScriptError(f"{_kind(v)} cannot be indexed")

    def binop(self, op: str, a: Any, b: Any) -> Any:
        match op:
            case "+":
                if isinstance(a, int) and isinstance(b, int) and not isinstance(a, bool) \
                        and not isinstance(b, bool):
                    return a + b
                if isinstance(a, str) and isinstance(b, str):
                    if len(a) + len(b) > MAX_STRING:
                        raise ScriptError(f"a string of more than {MAX_STRING} characters")
                    self.meter.charge("step", (len(a) + len(b)) // _PER_STEP)
                    return str(a) + str(b)
                if isinstance(a, list) and isinstance(b, list):
                    if len(a) + len(b) > MAX_LIST:
                        raise ScriptError(f"a list of more than {MAX_LIST} elements")
                    self.meter.charge("step", len(a) + len(b))            # each element copied
                    return a + b
                raise ScriptError(f"{_kind(a)} + {_kind(b)}: `+` joins two strings, two "
                                  "integers or two lists")
            case "==" | "!=":
                if isinstance(a, Content) and isinstance(b, Content):
                    self.meter.charge("step", min(len(a.data), len(b.data)) // _PER_STEP)
                elif isinstance(a, str) and isinstance(b, str):
                    self.meter.charge("step", min(len(a), len(b)) // _PER_STEP)
                return _same(a, b) if op == "==" else not _same(a, b)
            case "<" | "<=" | ">" | ">=":
                if isinstance(a, int) and isinstance(b, int):
                    return _order(op, a, b)
                if isinstance(a, str) and isinstance(b, str):
                    return _order(op, str(a), str(b))
                raise ScriptError(f"{_kind(a)} {op} {_kind(b)}: an order compares two integers "
                                  "or two strings")
            case "in" | "not in":
                if isinstance(b, SentenceV):
                    b = b.hits(self.palace, self.meter)
                if isinstance(b, list):
                    self.meter.charge("step", len(b))                    # each element compared
                    found = any(_same(a, x) for x in b)
                elif isinstance(b, str) and isinstance(a, str):
                    self.meter.charge("step", len(b) // _PER_STEP)
                    found = str(a) in str(b)
                elif isinstance(b, Record) and isinstance(a, str):
                    found = str(a) in b
                elif b is None:
                    found = False
                else:
                    raise ScriptError(f"{_kind(a)} in {_kind(b)}: membership is in a list, a "
                                      "string or a record")
                return found if op == "in" else not found
        raise ScriptError(f"unknown operator {op}")  # pragma: no cover

    # the built-ins -----------------------------------------------------------------------

    def call(self, fn: str, args: list[Any], kwargs: dict[str, Any]) -> Any:
        if fn not in BUILTINS:
            raise ScriptError(f"{fn}(…) is not a built-in function; they are "
                              f"{', '.join(sorted(BUILTINS))}")
        allowed = {"stored": {"under"}}.get(fn, set())
        if set(kwargs) - allowed:
            raise ScriptError(f"{fn}(…) takes no argument {sorted(set(kwargs) - allowed)[0]!r}")

        def arity(n: int) -> None:
            if len(args) != n:
                raise ScriptError(f"{fn}(…) takes {n} argument(s), {len(args)} given")

        def handle(v: Any) -> Handle:
            if not isinstance(v, Handle):
                raise ScriptError(f"{fn}(…): a source, from `source(name)`, not {_kind(v)}")
            return v

        def string(v: Any, what: str) -> str:
            if not isinstance(v, str):
                raise ScriptError(f"{fn}(…): {what} is a string, not {_kind(v)}")
            return str(v)

        match fn:
            case "source":
                arity(1)
                return self.palace.open(string(args[0], "a source's name"))
            case "files":
                arity(1)
                listing = self.palace.files(handle(args[0]))
                if isinstance(listing, Sized):
                    self.meter.charge("entry", len(listing))     # the paths listed, before reading
                return self._read(listing)
            case "file":
                arity(2)
                rec = self.palace.file(handle(args[0]), string(args[1], "a path"))
                self._charge_item(rec)
                return rec
            case "exists":
                arity(2)
                self.meter.charge("item")                # a stat and the directories' listings
                return self.palace.exists(handle(args[0]), string(args[1], "a path"))
            case "items":
                arity(1)
                return self._read(self.palace.items(handle(args[0])))
            case "stored":
                arity(1)
                under = kwargs.get("under", "")
                # a source's root names its directory: `<vault>-old/` is not under `<vault>/`
                prefix = (under.root.rstrip("/") + "/" if isinstance(under, Handle)
                          else string(under, "under"))
                rows = self._entries(string(args[0], "a place"))
                self.meter.charge("step", len(rows))                  # each row looked at
                return [r for r in rows if str(r.get("path")).startswith(prefix)]
            case "entry":
                arity(2)
                return self._entry(string(args[0], "a place"), string(args[1], "a name"))
            case "digest":
                arity(1)
                v = args[0]
                if isinstance(v, Content):
                    return v.digest
                return hashlib.sha256(string(v, "what is digested").encode("utf-8")).hexdigest()
            case "len":
                arity(1)
                v = args[0]
                if isinstance(v, SentenceV):
                    v = v.hits(self.palace, self.meter)
                if isinstance(v, Content):
                    return len(v.data)
                if isinstance(v, (str, list, Record)):
                    return len(v)
                raise ScriptError(f"len(…) of {_kind(v)}")
            case "str":
                arity(1)
                v = args[0]
                if isinstance(v, (Content, Handle, Record, list, Closure, SentenceV)):
                    raise ScriptError(f"str(…) of {_kind(v)}: only a string, an integer, a "
                                      "boolean or none has a text")
                return "none" if v is None else (str(v).lower() if isinstance(v, bool)
                                                 else str(v))
            case "paths":
                arity(1)
                xs = self.listish(args[0], "paths(…)")
                if not isinstance(xs, list):
                    raise ScriptError(f"paths(…) of a list, not {_kind(xs)}")
                return [x.get("path") if isinstance(x, Record) else None for x in xs]
            case "unique_by":
                arity(2)
                xs, f = self.listish(args[0], "unique_by(…)"), args[1]
                if not isinstance(xs, list):
                    raise ScriptError(f"unique_by(…) of a list, not {_kind(xs)}")
                key = string(f, "a field")
                seen: dict[str, Any] = {}
                twice: set[str] = set()
                for x in xs:
                    k = x.get(key) if isinstance(x, Record) else None
                    if not isinstance(k, str):
                        continue
                    if str(k) in seen:
                        twice.add(str(k))
                    else:
                        seen[str(k)] = x
                return Record({k: v for k, v in seen.items() if k not in twice})
            case "first":
                return next((v for v in args if v is not None), None)
            case "iso":
                arity(1)
                v = args[0]
                if v is None:
                    return ""
                if not isinstance(v, int) or isinstance(v, bool):
                    raise ScriptError(f"iso(…) of seconds, an integer, not {_kind(v)}")
                return datetime.fromtimestamp(v, UTC).isoformat(timespec="seconds")
        raise ScriptError(f"{fn}(…) is not wired")  # pragma: no cover

    def _entries(self, place: str) -> list[Record]:
        """A place's active entries, read from the palace once an evaluation, each paid for."""
        if place not in self._places:
            rows = list(self.palace.stored(place, ""))
            self.meter.charge("entry", len(rows))
            self._places[place] = rows
        return self._places[place]

    def _entry(self, place: str, name: str) -> Record:
        """The entry a name picks: by its path, else its title, else its digest; a name two
        entries share is refused, naming them by path is the way."""
        self.meter.charge("entry")
        if place not in self._index:
            idx: dict[str, dict[str, list[Record]]] = {"path": {}, "title": {}, "digest": {}}
            for r in self._entries(place):
                for key in idx:
                    idx[key].setdefault(str(r.get(key)), []).append(r)
            self._index[place] = idx
        idx = self._index[place]
        for key in ("path", "title", "digest"):
            hits = idx[key].get(name, [])
            if len(hits) == 1:
                return hits[0]
            if len(hits) > 1:
                raise ScriptError(f"entry({place!r}, …): {len(hits)} entries have that {key}; "
                                  "name one by its path")
        raise ScriptError(f"entry({place!r}, …): no entry has that path, title or digest")

    def _read(self, items: Iterable[Record]) -> list[Record]:
        """A source's items, each charged as it arrives: out of budget, the read stops there."""
        out: list[Record] = []
        for rec in items:
            self._charge_item(rec)
            out.append(rec)
        return out

    def _charge_item(self, rec: Record) -> None:
        """An item and its content's bytes: the KiB are charged as the evaluation's running total
        crosses each, so many small items pay for their bytes as one large one does."""
        self.meter.charge("item")
        before = self.read_bytes
        self.read_bytes += sum(len(c.data) for c in rec.values() if isinstance(c, Content))
        crossed = self.read_bytes // 1024 - before // 1024
        if crossed:
            self.meter.charge("kib", crossed)


def _order[T: (int, str)](op: str, a: T, b: T) -> bool:
    match op:
        case "<":
            return a < b
        case "<=":
            return a <= b
        case ">":
            return a > b
    return a >= b


def bind_params(script: S.Script, args: Sequence[Any],
                kwargs: Mapping[str, Any] | None) -> dict[str, Any]:
    """A script's parameters bound from a call's arguments, in order then by name, defaults for
    the rest; every parameter must end with a value."""
    env: dict[str, Any] = {}
    declared = S.params(script)
    names = [n for n, _ in declared]
    if len(args) > len(names):
        raise ScriptError(f"the script takes {len(names)} parameter(s), {len(args)} given")
    given = dict(zip(names, args, strict=False))
    for k, v in (kwargs or {}).items():
        if k not in names:
            raise ScriptError(f"the script has no parameter {k!r}; its parameters are "
                              f"{', '.join(names) or 'none'}")
        if k in given:
            raise ScriptError(f"parameter {k!r} given twice")
        given[k] = v
    for n, default in declared:
        if n in given:
            env[n] = given[n]
        elif default is not None:
            env[n] = default.value
        else:
            raise ScriptError(f"parameter {n!r} has no value and no default")
    return env


def _same(a: Any, b: Any) -> bool:
    if isinstance(a, Content) or isinstance(b, Content):
        return isinstance(a, Content) and isinstance(b, Content) and a.data == b.data
    if isinstance(a, bool) or isinstance(b, bool):
        return type(a) is type(b) and a == b
    return bool(a == b)


def _kind(v: Any) -> str:
    if v is None:
        return "none"
    if isinstance(v, bool):
        return "a boolean"
    if isinstance(v, int):
        return "an integer"
    if isinstance(v, str):
        return "a string"
    if isinstance(v, list):
        return "a list"
    if isinstance(v, Content):
        return "content"
    if isinstance(v, Handle):
        return "a source"
    if isinstance(v, Record):
        return "a record"
    if isinstance(v, Closure):
        return "a function"
    if isinstance(v, SentenceV):
        return "a sentence"
    return type(v).__name__
