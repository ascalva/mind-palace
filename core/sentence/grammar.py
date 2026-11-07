"""The grammar — a sentence's concrete syntax, parsed by precedence into `core.sentence.ast`
(dn-query-sentence-algebra §2.3).

    sentence  := "do" request | or-expr ("then" or-expr)*       -- a request is a whole sentence
    request   := a library call or a script inline, in the ingress language (`script.lark`)
    or-expr   := and-expr ("or" and-expr)*
    and-expr  := unary (("and" | "minus") unary)*               -- `and` binds tighter than `or`
    unary     := operand adjunct*                               -- adjectives bind tightest
    adjunct   := "within" operand | "over" WORD+ | "as" "of" STRING
    operand   := "far" operand | "top" NUMBER unary | "atleast" NUMBER unary | "not" operand
               | "(" sentence ")" | "assume" hypothesis "in" sentence | clause
    clause    := "near" STRING
               | "diffuse" [rel] "from" atom ["beta" NUMBER]
               | "reach" [rel] "from" atom ["depth" NUMBER] [direction]
               | "relate" atom
               | "trace" atom [direction]
               | "walk" "from" atom ["to" atom] "via" path ["depth" NUMBER]
               | "witness" STRING
               | "read" atom ["chunk" NUMBER]
    hypothesis:= rel atom atom [("+" | "-") NUMBER] | "sever" rel atom atom | "contradict" atom atom
    rel       := "S" | "F" | "D" | "C"
    direction := "forward" | "back" | "both"
    path      := a regular expression over S, F, D, C: letters, `(` `)` `|` `*` `+` `?` `{m}`
                 `{m,n}`
    atom      := STRING | WORD                                   -- a path, digest or title

`top` and `atleast` take their field with its adjectives, so `top 10 near "x" within R` ranks
within `R` and `top 1 near "x" over dialogue` ranks the dialogue: a ranking is not pointwise, and
masking after it would drop hits the mask would have kept (the review of 2026-11-05). `far` and
`not` take the bare operand, so an adjective after them restricts the reversal or the complement.
`assume` extends as far right as it can (parenthesize it to continue the sentence). `do` takes
the rest of the text as a request of the ingress language (dn-ingress-language §E6), which has its
own grammar: a request composes with nothing, since its value is a receipt and what it writes
lands later. A parse error names the production that failed and
the token it saw.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from core.sentence.ast import (
    And,
    AsOf,
    Assume,
    AtLeast,
    ContradictHyp,
    Diffuse,
    Direction,
    Do,
    EdgeHyp,
    Far,
    Hypothesis,
    Minus,
    Near,
    Node,
    Not,
    Or,
    Over,
    Reach,
    Read,
    Rel,
    Relate,
    SeverHyp,
    Then,
    Top,
    Trace,
    Walk,
    Within,
    Witness,
)


class ParseError(ValueError):
    """The sentence is not in the grammar; the message names the production and the token."""


@dataclass(frozen=True)
class Token:
    kind: str       # STRING | NUMBER | WORD | SYM | END
    text: str
    pos: int


_TOKEN = re.compile(
    r"""\s*(?:
        "(?P<string>(?:[^"\\]|\\.)*)"          # a quoted string, with \" escapes
      | (?P<number>\d+(?:\.\d+)?(?![A-Za-z0-9_])) # an unsigned number, never the head of a word
      | (?P<word>[A-Za-z0-9_][A-Za-z0-9_./:#@\-]*) # a word: a keyword, a letter, an atom, an id
      | (?P<sym>[(){}|*+?,\-])                  # a symbol of a path or a signed weight
    )""",
    re.VERBOSE,
)

KEYWORDS = frozenset({
    "near", "diffuse", "far", "reach", "relate", "top", "atleast", "not", "minus", "trace",
    "walk", "witness", "read", "chunk", "assume", "sever", "contradict", "in", "and", "or", "then",
    "within",
    "over", "as", "of", "from", "to", "via", "beta", "depth", "back", "forward", "both",
    "S", "F", "D", "C",
    "do",      # the ingress: the rest of the text is a request of the ingress language
})

_STOP_PATH = frozenset({"depth", "and", "or", "then", "within", "over", "as", "in", "minus", ")"})
_STOP_STRATA = KEYWORDS | {")"}


_UNESCAPE = re.compile(r'\\(["\\])')


def quote(s: str) -> str:
    """A string literal the grammar reads back as `s`: quoted, with `\\` and `\"` escapes, the
    tokenizer's inverse for every text (a client's text can never end a literal early)."""
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def tokenize(text: str) -> list[Token]:
    tokens: list[Token] = []
    pos = 0
    while pos < len(text):
        m = _TOKEN.match(text, pos)
        if m is None or m.end() == pos:
            if text[pos:].strip() == "":
                break
            raise ParseError(f"tokens: unexpected character {text[pos]!r} at {pos}")
        if m.group("string") is not None:
            tokens.append(Token("STRING", _UNESCAPE.sub(r"\1", m.group("string")), m.start()))
        elif m.group("number") is not None:
            tokens.append(Token("NUMBER", m.group("number"), m.start()))
        elif m.group("word") is not None:
            tokens.append(Token("WORD", m.group("word"), m.start()))
        else:
            tokens.append(Token("SYM", m.group("sym"), m.start()))
        pos = m.end()
    tokens.append(Token("END", "", len(text)))
    return tokens


class _Parser:
    def __init__(self, text: str) -> None:
        self.text = text
        self.tokens = tokenize(text)
        self.i = 0

    # ── token helpers ──────────────────────────────────────────────────────────────────────────
    def peek(self, ahead: int = 0) -> Token:
        return self.tokens[min(self.i + ahead, len(self.tokens) - 1)]

    def at_word(self, *words: str) -> bool:
        t = self.peek()
        return t.kind == "WORD" and t.text in words

    def at_sym(self, sym: str) -> bool:
        t = self.peek()
        return t.kind == "SYM" and t.text == sym

    def next(self) -> Token:
        t = self.peek()
        self.i += 1
        return t

    def fail(self, production: str, expected: str) -> ParseError:
        t = self.peek()
        if t.kind == "END":
            seen = "the end of the sentence"
        elif t.kind == "STRING":          # a string's text never enters an error (the query log)
            seen = f"a string of {len(t.text)} characters at {t.pos}"
        else:
            seen = f"{t.text!r} at {t.pos}"
        return ParseError(f"{production}: expected {expected}, got {seen}")

    def expect_word(self, production: str, word: str) -> None:
        if not self.at_word(word):
            raise self.fail(production, repr(word))
        self.next()

    def number(self, production: str) -> float:
        t = self.peek()
        if t.kind != "NUMBER":
            raise self.fail(production, "a number")
        self.next()
        return float(t.text)

    def integer(self, production: str) -> int:
        t = self.peek()
        if t.kind != "NUMBER" or "." in t.text:
            raise self.fail(production, "a whole number")
        self.next()
        return int(t.text)

    def string(self, production: str) -> str:
        t = self.peek()
        if t.kind != "STRING":
            raise self.fail(production, "a quoted string")
        self.next()
        return t.text

    def atom(self, production: str) -> str:
        t = self.peek()
        if t.kind == "STRING" or (t.kind == "WORD" and t.text not in KEYWORDS):
            self.next()
            return t.text
        raise self.fail(production, "a note: a quoted string, or a path or digest")

    def rel(self, production: str) -> Rel | None:
        if self.at_word("S", "F", "D", "C"):
            return Rel(self.next().text)
        return None

    def direction(self) -> Direction | None:
        if self.at_word("forward", "back", "both"):
            return Direction(self.next().text)
        return None

    # ── the grammar ────────────────────────────────────────────────────────────────────────────
    def sentence(self) -> Node:
        left = self.or_expr()
        while self.at_word("then"):
            self.next()
            left = Then(left, self.or_expr())
        return left

    def or_expr(self) -> Node:
        left = self.and_expr()
        while self.at_word("or"):
            self.next()
            left = Or(left, self.and_expr())
        return left

    def and_expr(self) -> Node:
        left = self.unary()
        while self.at_word("and", "minus"):
            op = self.next().text
            right = self.unary()
            left = And(left, right) if op == "and" else Minus(left, right)
        return left

    def unary(self) -> Node:
        node = self.operand()
        while True:
            if self.at_word("within"):
                self.next()
                node = Within(node, self.operand())
            elif self.at_word("over"):
                self.next()
                strata: list[str] = []
                while self.peek().kind == "WORD" and self.peek().text not in _STOP_STRATA:
                    strata.append(self.next().text)
                if not strata:
                    raise self.fail("over", "one or more strata names")
                node = Over(node, tuple(strata))
            elif self.at_word("as"):
                self.next()
                self.expect_word("as of", "of")
                node = AsOf(node, self.string("as of"))
            else:
                return node

    def operand(self) -> Node:
        if self.at_word("far"):
            self.next()
            return Far(self.operand())
        if self.at_word("top"):
            self.next()
            return Top(self.integer("top"), self.unary())
        if self.at_word("atleast"):
            self.next()
            return AtLeast(self.number("atleast"), self.unary())
        if self.at_word("not"):
            self.next()
            return Not(self.operand())
        if self.at_sym("("):
            self.next()
            inner = self.sentence()
            if not self.at_sym(")"):
                raise self.fail("parenthesis", "')'")
            self.next()
            return inner
        if self.at_word("assume"):
            self.next()
            hyp = self.hypothesis()
            self.expect_word("assume", "in")
            return Assume(hyp, self.sentence())
        return self.clause()

    def clause(self) -> Node:
        t = self.peek()
        if t.kind != "WORD":
            raise self.fail("clause", "a verb")
        if t.text == "near":
            self.next()
            return Near(self.string("near"))
        if t.text == "diffuse":
            self.next()
            rel = self.rel("diffuse") or Rel.S
            self.expect_word("diffuse", "from")
            atom = self.atom("diffuse")
            beta: float | None = None
            if self.at_word("beta"):
                self.next()
                beta = self.number("diffuse beta")
                if not beta > 0:
                    raise ParseError(f"diffuse beta: the free energy needs β > 0 (RSP-1), got "
                                     f"{beta:g}")
            return Diffuse(rel, atom, beta)
        if t.text == "reach":
            self.next()
            rel = self.rel("reach") or Rel.F
            self.expect_word("reach", "from")
            atom = self.atom("reach")
            depth: int | None = None
            if self.at_word("depth"):
                self.next()
                depth = self.integer("reach depth")
            direction = self.direction() or Direction.BOTH
            return Reach(rel, atom, depth, direction)
        if t.text == "relate":
            self.next()
            return Relate(self.atom("relate"))
        if t.text == "trace":
            self.next()
            atom = self.atom("trace")
            return Trace(atom, self.direction() or Direction.FORWARD)
        if t.text == "walk":
            self.next()
            self.expect_word("walk", "from")
            atom = self.atom("walk")
            to: str | None = None
            if self.at_word("to"):
                self.next()
                to = self.atom("walk to")
            self.expect_word("walk", "via")
            path = self.path()
            depth = None
            if self.at_word("depth"):
                self.next()
                depth = self.integer("walk depth")
            return Walk(atom, path, to, depth)
        if t.text == "witness":
            self.next()
            return Witness(self.string("witness"))
        if t.text == "read":
            self.next()
            atom = self.atom("read")
            chunk: int | None = None
            if self.at_word("chunk"):
                self.next()
                chunk = self.integer("read chunk")
            return Read(atom, chunk)
        if t.text in KEYWORDS:
            raise self.fail("clause", f"a verb, not the keyword {t.text!r}")
        raise self.fail("clause", "a verb (near, diffuse, reach, relate, trace, walk, witness, "
                                  f"read), not {t.text!r}")

    def path(self) -> str:
        """The path's tokens up to the next keyword or the `)` that closes an enclosing group:
        the path's own parentheses are balanced first, so `via (S|F)+` is one path."""
        parts: list[str] = []
        depth = 0
        while True:
            t = self.peek()
            if t.kind == "END" or (t.kind in ("WORD", "SYM") and t.text in _STOP_PATH
                                   and not (t.text == ")" and depth > 0)):
                break
            if t.kind == "STRING":
                raise self.fail("via", "a path over S, F, D, C, not a quoted string")
            if t.kind == "SYM" and t.text in "()":
                depth += 1 if t.text == "(" else -1
            parts.append(self.next().text)
        if not parts:
            raise self.fail("via", "a path over S, F, D, C")
        return "".join(parts)

    def hypothesis(self) -> Hypothesis:
        if self.at_word("sever"):
            self.next()
            rel = self.rel("sever")
            if rel is None:
                raise self.fail("sever", "a relation letter")
            return SeverHyp(rel, self.atom("sever"), self.atom("sever"))
        if self.at_word("contradict"):
            self.next()
            return ContradictHyp(self.atom("contradict"), self.atom("contradict"))
        rel = self.rel("assume")
        if rel is None:
            raise self.fail("assume", "a relation letter, 'sever' or 'contradict'")
        a = self.atom("assume")
        b = self.atom("assume")
        weight = 1.0
        if self.at_sym("+") or self.at_sym("-"):
            sign = -1.0 if self.next().text == "-" else 1.0
            weight = sign * self.number("assume weight")
        return EdgeHyp(rel, a, b, weight)

    # ── commands ───────────────────────────────────────────────────────────────────────────────
    def parse(self) -> Node:
        if self.peek().kind == "END":
            raise ParseError("sentence: the sentence is empty")
        node = self.sentence()
        if self.peek().kind != "END":
            raise self.fail("sentence", "the end of the sentence")
        return node


_DO = re.compile(r"\s*do(?=[\s{]|$)")


def is_request(text: str) -> bool:
    """Whether a text is a request of the ingress language: the one rule every surface and every
    filter asks, the same the parser follows, so none can disagree about what is a request."""
    return _DO.match(text) is not None


def parse(text: str) -> Node:
    """Parse a sentence, or raise `ParseError` naming the production that failed. A sentence that
    begins with `do` is a request of the ingress language, read by its own grammar."""
    m = _DO.match(text)
    if m is not None:
        from core.sentence.script import parse_request

        rest = text[m.end():]
        if not rest.strip():
            raise ParseError("do: a request: a library script's name, or a script in { }")
        return Do(parse_request(rest), text=rest.strip())
    return _Parser(text).parse()
