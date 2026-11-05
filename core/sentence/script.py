"""The door's language: a script's tree and its parser (dn-door-language §E1, §E6, §E11, §E12).

A request is `do` and a script: a call of a library script, `do name(k: v, …)`, or a script
inline, `do { … }`. The language knows no source, no place and no job by name; those are the
palace's table's (`core/ingest/table.py`), and a script names them with string literals. Its one
definition is the grammar `script.lark` beside this module, read by Lark (LALR(1)); this module
turns Lark's tree into the frozen tree below. A newline ends a statement in a block or at the top
level and is space inside `( )` and `[ ]`. A read sentence nests in backquotes and captures names
of the enclosing scope as `$name`. Functions close over the scope where they are defined and
cannot name themselves, so a script has no recursion, and with every loop over a finite list its
evaluation ends; the meter bounds it in any case.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Any

from lark import Lark, Token, Transformer_NonRecursive, Tree
from lark.exceptions import UnexpectedCharacters, UnexpectedEOF, UnexpectedInput, UnexpectedToken

from core.sentence.grammar import ParseError

KEYWORDS = frozenset({
    "let", "for", "in", "if", "else", "param", "store", "at", "as", "titled", "retire", "link",
    "to", "run", "with", "and", "or", "not", "true", "false", "none", "fn", "return", "call",
})

MAX_SCRIPT_CHARS = 64 * 1024        # a script longer than this is refused before it is read
MAX_DEPTH = 64                      # nesting of the tree, blocks and expressions together


# ── the tree ────────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Lit:
    """A literal: a string, an integer, a boolean or `none`."""
    value: str | int | bool | None


@dataclass(frozen=True)
class Name:
    id: str


@dataclass(frozen=True)
class Field:
    obj: Expr
    name: str


@dataclass(frozen=True)
class Index:
    obj: Expr
    key: Expr


@dataclass(frozen=True)
class Slice:
    obj: Expr
    lo: Expr | None
    hi: Expr | None


@dataclass(frozen=True)
class ListLit:
    items: tuple[Expr, ...]


@dataclass(frozen=True)
class Comp:
    """`[expr for var in iter if cond]`."""
    expr: Expr
    var: str
    iter: Expr
    cond: Expr | None


@dataclass(frozen=True)
class Call:
    """A call by name, of a built-in function or of a function bound in scope: positional
    arguments, then `k: v` ones."""
    fn: str
    args: tuple[Expr, ...]
    kwargs: tuple[tuple[str, Expr], ...]


@dataclass(frozen=True)
class Sentence:
    """A read sentence nested in backquotes, with the names it captures as `$name` (§E11)."""
    text: str
    captures: tuple[str, ...]


@dataclass(frozen=True)
class BinOp:
    op: str          # + == != < <= > >= in "not in" and or
    left: Expr
    right: Expr


@dataclass(frozen=True)
class Not:
    expr: Expr


Expr = Lit | Name | Field | Index | Slice | ListLit | Comp | Call | Sentence | BinOp | Not


@dataclass(frozen=True)
class Param:
    """A library script's parameters, each with an optional literal default."""
    names: tuple[tuple[str, Lit | None], ...]


@dataclass(frozen=True)
class Let:
    name: str
    expr: Expr


@dataclass(frozen=True)
class For:
    var: str
    iter: Expr
    body: tuple[Stmt, ...]


@dataclass(frozen=True)
class If:
    cond: Expr
    then: tuple[Stmt, ...]
    orelse: tuple[Stmt, ...]


@dataclass(frozen=True)
class Store:
    """`store content [at path] [as identity] in "place" [titled title]`."""
    content: Expr
    at: Expr | None
    ident: Expr | None
    place: str
    titled: Expr | None


@dataclass(frozen=True)
class Retire:
    path: Expr
    place: str


@dataclass(frozen=True)
class Link:
    a: Expr
    b: Expr
    relation: Expr


@dataclass(frozen=True)
class Run:
    job: str
    args: tuple[tuple[str, Expr], ...]


@dataclass(frozen=True)
class Fn:
    """`fn name(x, …) { … }`: a function closing over the scope where it is defined (§E11)."""
    name: str
    params: tuple[str, ...]
    body: tuple[Stmt, ...]


@dataclass(frozen=True)
class Return:
    expr: Expr


@dataclass(frozen=True)
class CallStmt:
    """`call name(k: v, …)`: a library script, in a scope of its own (§E11)."""
    name: str
    args: tuple[Lit, ...]
    kwargs: tuple[tuple[str, Lit], ...]


Stmt = Param | Let | For | If | Store | Retire | Link | Run | Fn | Return | CallStmt


@dataclass(frozen=True)
class Script:
    body: tuple[Stmt, ...]


@dataclass(frozen=True)
class CallScript:
    """`do name(k: v, …)`: a library script by name, with literal arguments."""
    name: str
    args: tuple[Lit, ...]
    kwargs: tuple[tuple[str, Lit], ...]


@dataclass(frozen=True)
class Inline:
    """`do { … }`: a script spoken whole."""
    script: Script


Request = CallScript | Inline


def effects(body: tuple[Stmt, ...]) -> list[Store | Retire | Link | Run]:
    """Every effect statement of a script, in order, at any depth."""
    out: list[Store | Retire | Link | Run] = []
    for s in body:
        match s:
            case Store() | Retire() | Link() | Run():
                out.append(s)
            case For(body=b) | Fn(body=b):
                out += effects(b)
            case If(then=t, orelse=e):
                out += effects(t) + effects(e)
    return out


def params(script: Script) -> list[tuple[str, Lit | None]]:
    """The parameters a script declares, in order."""
    return [p for s in script.body if isinstance(s, Param) for p in s.names]


# ── the parser ──────────────────────────────────────────────────────────────────────────────

GRAMMAR = Path(__file__).with_name("script.lark")
_CAPTURE = re.compile(r"\$([A-Za-z_][A-Za-z0-9_]*)")
_ESC = re.compile(r"\\(.)")
_ESCAPES = {'"': '"', "'": "'", "\\": "\\", "n": "\n", "t": "\t"}


class _Lines:
    """The post-lexer: a newline inside `( )` or `[ ]` is space."""

    always_accept = ("_NL",)

    def process(self, stream: Iterator[Token]) -> Iterator[Token]:
        depth = 0
        for t in stream:
            if t.type in ("LPAR", "LSQB"):
                depth += 1
            elif t.type in ("RPAR", "RSQB"):
                depth -= 1
            if t.type == "_NL" and depth > 0:
                continue
            yield t


@cache
def _lark() -> Lark:
    return Lark(GRAMMAR.read_text(encoding="utf-8"), start=["script", "request"], parser="lalr",
                postlex=_Lines(), maybe_placeholders=True, propagate_positions=False)


def _unquote(tok: str) -> str:
    def one(m: re.Match[str]) -> str:
        c = m.group(1)
        if c not in _ESCAPES:
            raise ParseError(f"script: unknown escape \\{c} in a string")
        return _ESCAPES[c]
    return _ESC.sub(one, tok[1:-1])


def _block(tree: Any) -> tuple[Stmt, ...]:
    return tree if isinstance(tree, tuple) else ()


def _bound(tok: Any) -> str:
    """A name a statement binds: never a keyword (the contextual lexer reads `let` as a name where
    only a name may come, so the grammar alone would take `let let = 1`)."""
    name = str(tok)
    if name in KEYWORDS:
        raise ParseError(f"script: {name!r} is a keyword and cannot be bound")
    return name


class _Build(Transformer_NonRecursive[Token, Any]):
    """Lark's tree to the frozen tree."""

    def string(self, c: list[Token]) -> Lit:
        return Lit(_unquote(str(c[0])))

    def int(self, c: list[Token]) -> Lit:
        return Lit(int(str(c[0])))

    def true(self, c: list[Any]) -> Lit:
        return Lit(True)

    def false(self, c: list[Any]) -> Lit:
        return Lit(False)

    def none(self, c: list[Any]) -> Lit:
        return Lit(None)

    def name(self, c: list[Token]) -> Name:
        if str(c[0]) in KEYWORDS:
            raise ParseError(f"script: {str(c[0])!r} is a keyword, not a value")
        return Name(str(c[0]))

    def sentence(self, c: list[Token]) -> Sentence:
        text = str(c[0])[1:-1]
        return Sentence(text, tuple(dict.fromkeys(_CAPTURE.findall(text))))

    def field(self, c: list[Any]) -> Field:
        return Field(c[0], str(c[1]))

    def index(self, c: list[Any]) -> Index:
        return Index(c[0], c[1])

    def slice(self, c: list[Any]) -> Slice:
        return Slice(c[0], c[1], c[2])

    def empty_list(self, c: list[Any]) -> ListLit:
        return ListLit(())

    def list_(self, c: list[Any]) -> ListLit:
        return ListLit(tuple(c))

    def comp(self, c: list[Any]) -> Comp:
        return Comp(c[0], _bound(c[1]), c[2], c[3])

    def kwarg(self, c: list[Any]) -> tuple[str, Expr]:
        return (str(c[0]), c[1])

    def call_fn(self, c: list[Any]) -> Call:
        args = [a for a in c[1:] if a is not None]
        pos = [a for a in args if not isinstance(a, tuple)]
        kw = [a for a in args if isinstance(a, tuple)]
        seen_kw = False
        for a in args:
            if isinstance(a, tuple):
                seen_kw = True
            elif seen_kw:
                raise ParseError(f"script: {c[0]}(…): positional arguments come before "
                                 "keyword ones")
        return Call(str(c[0]), tuple(pos), tuple(kw))

    def not_(self, c: list[Any]) -> Not:
        return Not(c[0])

    def or_(self, c: list[Any]) -> BinOp:
        return BinOp("or", c[0], c[1])

    def and_(self, c: list[Any]) -> BinOp:
        return BinOp("and", c[0], c[1])

    def compare(self, c: list[Any]) -> BinOp:
        return BinOp(str(c[1]), c[0], c[2])

    def in_(self, c: list[Any]) -> BinOp:
        return BinOp("in", c[0], c[1])

    def not_in(self, c: list[Any]) -> BinOp:
        return BinOp("not in", c[0], c[2])

    def add(self, c: list[Any]) -> BinOp:
        return BinOp("+", c[0], c[1])

    # statements --------------------------------------------------------------------------

    def script(self, c: list[Any]) -> tuple[Stmt, ...]:
        return tuple(x for x in c if x is not None)

    def block(self, c: list[Any]) -> tuple[Stmt, ...]:
        return _block(c[0])

    def pdecl(self, c: list[Any]) -> tuple[str, Lit | None]:
        return (_bound(c[0]), c[1])

    def param(self, c: list[Any]) -> Param:
        return Param(tuple(c))

    def let(self, c: list[Any]) -> Let:
        return Let(_bound(c[0]), c[1])

    def fn(self, c: list[Any]) -> Fn:
        params = tuple(_bound(x) for x in c[1:-1] if x is not None)
        if len(set(params)) != len(params):
            raise ParseError(f"script: fn {c[0]}: a parameter named twice")
        return Fn(_bound(c[0]), params, _block(c[-1]))

    def for_(self, c: list[Any]) -> For:
        return For(_bound(c[0]), c[1], _block(c[2]))

    def if_(self, c: list[Any]) -> If:
        orelse = c[2]
        if isinstance(orelse, If):
            orelse = (orelse,)
        return If(c[0], _block(c[1]), orelse if isinstance(orelse, tuple) else ())

    def at(self, c: list[Any]) -> tuple[str, Any]:
        return ("at", c[0])

    def as_(self, c: list[Any]) -> tuple[str, Any]:
        return ("as", c[0])

    def place(self, c: list[Token]) -> tuple[str, Any]:
        return ("in", _unquote(str(c[0])))

    def titled(self, c: list[Any]) -> tuple[str, Any]:
        return ("titled", c[0])

    def store(self, c: list[Any]) -> Store:
        clauses: dict[str, Any] = {}
        for word, value in c[1:]:
            if word in clauses:
                raise ParseError(f"script: store: one {word!r} clause")
            clauses[word] = value
        if "in" not in clauses:
            raise ParseError("script: store: 'in' and the place are required")
        return Store(c[0], clauses.get("at"), clauses.get("as"), clauses["in"],
                     clauses.get("titled"))

    def retire(self, c: list[Any]) -> Retire:
        return Retire(c[0], _unquote(str(c[1])))

    def link(self, c: list[Any]) -> Link:
        return Link(c[0], c[1], c[2])

    def run(self, c: list[Any]) -> Run:
        return Run(_unquote(str(c[0])), tuple(x for x in c[1:] if x is not None))

    def call_args(self, c: list[Any]) -> tuple[list[Lit], list[tuple[str, Lit]]]:
        args = [a for a in c if a is not None]
        pos, kw = [], []
        for a in args:
            if isinstance(a, tuple):
                kw.append(a)
            elif kw:
                raise ParseError("script: positional arguments come before keyword ones")
            else:
                pos.append(a)
        return pos, kw

    def ckwarg(self, c: list[Any]) -> tuple[str, Lit]:
        return (str(c[0]), c[1])

    def call(self, c: list[Any]) -> CallStmt:
        pos, kw = c[1] if c[1] is not None else ([], [])
        return CallStmt(str(c[0]), tuple(pos), tuple(kw))

    def return_(self, c: list[Any]) -> Return:
        return Return(c[0])

    def call_request(self, c: list[Any]) -> CallScript:
        pos, kw = c[1] if c[1] is not None else ([], [])
        return CallScript(str(c[0]), tuple(pos), tuple(kw))

    def inline_request(self, c: list[Any]) -> Inline:
        return Inline(Script(_block(c[0])))


_NAMES = {"NAME": "a name", "STRING": "a quoted string", "INT": "an integer",
          "SENTENCE": "a sentence in backquotes", "_NL": "a newline", "$END": "the end",
          "LBRACE": "'{'", "RBRACE": "'}'", "LPAR": "'('", "RPAR": "')'", "LSQB": "'['",
          "RSQB": "']'", "COMMA": "','", "COLON": "':'", "SEMICOLON": "';'", "DOT": "'.'",
          "EQUAL": "'='", "PLUS": "'+'", "COMPOP": "a comparison"}


def _error(text: str, e: UnexpectedInput) -> ParseError:
    line, col = getattr(e, "line", "?"), getattr(e, "column", "?")
    if isinstance(e, UnexpectedCharacters):
        return ParseError(f"script: unexpected character {getattr(e, 'char', '?')!r} at line "
                          f"{line}, column {col}")
    seen = "the end"
    if isinstance(e, UnexpectedToken) and e.token.type != "$END":
        tok = str(e.token)
        seen = ("a newline" if e.token.type == "_NL"
                else f"a string of {len(tok) - 2} characters" if e.token.type == "STRING"
                else f"a sentence of {len(tok) - 2} characters" if e.token.type == "SENTENCE"
                else repr(tok))
    raw = set(getattr(e, "expected", None) or ())
    if raw & {"_NL", "SEMICOLON"}:
        return ParseError(f"script: at line {line}, column {col}: expected the end of the "
                          f"statement (a newline or ';'), saw {seen}")
    expected = sorted({_NAMES.get(t, repr(t.lower()) if t.isupper() else t) for t in raw})
    shown = ", ".join(expected[:8]) + (", …" if len(expected) > 8 else "")
    return ParseError(f"script: at line {line}, column {col}: expected {shown or 'more'}, "
                      f"saw {seen}")


def _depth(node: Any, at: int = 0) -> int:
    """The tree's depth, refused past `MAX_DEPTH` so no later pass recurses without bound."""
    stack = [(node, at)]
    deepest = 0
    while stack:
        n, d = stack.pop()
        deepest = max(deepest, d)
        if d > MAX_DEPTH:
            raise ParseError(f"script: nested deeper than {MAX_DEPTH}")
        if isinstance(n, tuple):
            stack += [(x, d) for x in n]
        elif hasattr(n, "__dataclass_fields__"):
            stack += [(getattr(n, f), d + 1) for f in n.__dataclass_fields__]
    return deepest


def _parse(text: str, start: str) -> Any:
    if len(text) > MAX_SCRIPT_CHARS:
        raise ParseError(f"script: {len(text)} characters, more than {MAX_SCRIPT_CHARS}")
    try:
        tree: Tree[Token] = _lark().parse(text, start=start)
    except (UnexpectedToken, UnexpectedCharacters, UnexpectedEOF) as e:
        raise _error(text, e) from None
    try:
        out = _Build().transform(tree)
    except Exception as e:                       # a transformer's ParseError, re-raised plain
        cause = e.__context__ if not isinstance(e, ParseError) else e
        if isinstance(cause, ParseError):
            raise cause from None
        raise
    _depth(out)
    return out


def parse_request(text: str) -> Request:
    """The request after `do`: a library call or a script inline."""
    out = _parse(text, "request")
    assert isinstance(out, (CallScript, Inline))
    return out


def parse_script(text: str) -> Script:
    """A library script's text."""
    return Script(_block(_parse(text, "script")))


LIBRARY = Path(__file__).resolve().parents[2] / "door"
_LIBRARY_NAME = re.compile(r"[a-z_][a-z0-9_]{0,63}")


def library_names(root: Path | None = None) -> list[str]:
    """The library's scripts, by name."""
    return sorted(p.stem for p in (root or LIBRARY).glob("*.palace")
                  if _LIBRARY_NAME.fullmatch(p.stem))


def load(name: str, root: Path | None = None) -> Script:
    """A library script by name (`door/<name>.palace`): a name, never a path."""
    if not _LIBRARY_NAME.fullmatch(name):
        raise ParseError(f"script: {name!r} is not a library script's name")
    path = (root or LIBRARY) / f"{name}.palace"
    if not path.is_file():
        raise ParseError(f"script: no library script {name!r} (door/{name}.palace)")
    return parse_script(path.read_text(encoding="utf-8"))


def quote(s: str) -> str:
    """A string literal the script grammar reads back as `s`."""
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") \
        .replace("\t", "\\t") + '"'
