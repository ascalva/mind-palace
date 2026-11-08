"""`mind-palace shell`: a read-only interactive shell over the query sentence language, with
completion that knows the language (dn-query-sentence-algebra §2.3, docs/query/asking.md).

A query shell, not a conversation (`scripts/talk.py` is the Ambassador's): every line is a
sentence, or one of a few commands about sentences. A sentence is compiled under the surfaces'
grant (`sentence_grant`), its universe built from the instance the configuration names, and the
plan executed; the answer is printed with each hit's provenance and the universe's notes, the
`missing` list among them.

**Read-only by construction.** The shell calls three things of the core: `compile_sentence`,
`universe.build` and `execute`, the read path `palace query` runs. It never calls the ingress: a
request (`do …`) is the action sort, and the shell refuses it before anything is opened, because
a request lands through the daemon's writer. It takes no lock: neither the supervisor lock nor a
store's writer lock is on the read path, and a store a writer holds is reported as busy, never
waited on or taken. It writes no query-log line either: the log is the surfaces' sensor of what
agents and the owner ask, and a shell for learning the language would flood it with drafts.

**Completion comes from the parser.** What may follow a prefix is decided by asking the parser
itself (`expected`): each keyword of `grammar.KEYWORDS`, each symbol of a path and one
placeholder per token class is appended to the prefix, and a candidate is offered when the parser
consumes it. The kind of an open slot (a note, a stratum, a number, a path) is read off the
parser's own refusal of the prefix, and the slot is filled from the instance: the strata the type
checker accepts, the corpus sources the configuration declares, the paths and titles the catalog
and the reference index hold, and the precedents' default for a number left unsaid. Nothing here
lists the verbs: a verb the grammar gains is offered the moment the parser accepts it, and
`tests/unit/test_sentence_shell.py` checks that every verb the parser accepts is offered and has
a help entry whose shape the parser accepts keyword for keyword.

The front end is the standard library's `readline` (libedit on macOS); see `docs/sentence-cheat-
sheet.md` for the language on one page, or `:cheat` inside the shell.
"""

from __future__ import annotations

import os
import re
import sqlite3
import sys
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, fields, is_dataclass
from pathlib import Path
from typing import Any, TextIO

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:                     # run as a script: the repo root on the path
    sys.path.insert(0, str(REPO))

from core.kernel.scope import Stratum  # noqa: E402
from core.sentence import ast  # noqa: E402
from core.sentence.grammar import (  # noqa: E402
    _STOP_PATH,
    KEYWORDS,
    ParseError,
    _Parser,
    is_request,
    quote,
    tokenize,
)
from core.sentence.precedents import DEFAULT, Precedents  # noqa: E402

CHEAT_SHEET = REPO / "docs" / "sentence-cheat-sheet.md"
PROMPT, MORE = "palace> ", "   ...> "
HISTORY_ENV = "MIND_PALACE_SHELL_HISTORY"
HISTORY_DEFAULT = Path("~/.local/state/mind-palace/shell_history")

# ── the grammar, asked ─────────────────────────────────────────────────────────────────────────

#: The action sort: the parser accepts it, the shell does not (it would reach the ingress).
ACTION = "do"
#: One placeholder per token class: a string, a number, and a word that is no keyword.
PLACEHOLDER = {"string": '"zz"', "number": "2", "word": "zz9"}
#: The symbols a sentence may carry: a group, and the operators of a path or a signed weight.
SYMBOLS = ("(", ")", "|", "*", "+", "?", "{", "}", ",", "-")
#: The relation letters, the alphabet of a path.
RELATIONS = frozenset(r.value for r in ast.Rel)


def consumes(prefix: str, candidate: str) -> bool:
    """Whether the parser, reading `prefix` then the one token `candidate`, gets past the
    candidate: it either parses the whole text or fails on a later token (the end among them)."""
    text = f"{prefix} {candidate}" if prefix.strip() else candidate
    if is_request(text):
        return False
    try:
        tokens = tokenize(text)
    except ParseError:
        return False
    at = len(tokens) - 2                    # the candidate: the last token before the end
    if at < 0:
        return False
    p = _Parser(text)
    try:
        p.parse()
    except ParseError:
        return p.i > at
    return True


def parses(text: str) -> bool:
    if not text.strip() or is_request(text):
        return False
    try:
        _Parser(text).parse()
    except ParseError:
        return False
    return True


@dataclass(frozen=True)
class Slot:
    """What the parser asks for at the end of a prefix: the production and what it expected."""

    kind: str          # note | string | number | path | strata | none
    production: str
    expected: str


_AT_END = re.compile(r"^(?P<production>[^:]+): expected (?P<expected>.+), got the end of the "
                     r"sentence$")


def slot(prefix: str) -> Slot:
    """The open slot at the end of `prefix`, read off the parser's refusal of it; `none` when the
    prefix fails before its end or leaves no argument open."""
    if not prefix.strip():
        return Slot("none", "sentence", "a verb")
    try:
        _Parser(prefix).parse()
    except ParseError as e:
        m = _AT_END.match(str(e))
        if m is None:
            return Slot("none", "", str(e))
        production, expected = m["production"], m["expected"]
        kind = ("note" if expected.startswith("a note") else
                "string" if expected == "a quoted string" else
                "number" if expected in ("a number", "a whole number") else
                "path" if expected.startswith("a path") else
                "strata" if expected.startswith("one or more strata") else "none")
        return Slot(kind, production, expected)
    # the prefix is a whole sentence: an `over` list may take another stratum, a path another
    # letter; where a word would land in the tree says which
    word = PLACEHOLDER["word"]
    probe = f"{prefix} {word}"
    if parses(probe):
        for n in ast_nodes(_Parser(probe).parse()):
            if isinstance(n, ast.Over) and word in n.strata:
                return Slot("strata", "over", "more strata names")
            if isinstance(n, ast.Walk) and n.path.endswith(word):
                return Slot("path", "via", "more of the path")
    return Slot("none", "", "")


def ast_nodes(node: object) -> Iterable[object]:
    yield node
    if is_dataclass(node) and not isinstance(node, type):
        for f in fields(node):
            yield from ast_nodes(getattr(node, f.name))


def accepted_keywords(prefix: str) -> list[str]:
    """The keywords the parser consumes after `prefix`, the action sort left out."""
    return sorted(k for k in KEYWORDS if k != ACTION and consumes(prefix, k))


def parser_verbs() -> list[str]:
    """The verbs of the read language, as the parser accepts them: the keywords a sentence may
    begin with, and those it consumes after a whole sentence (the connectives and adjectives;
    `as` reads as `as of`)."""
    whole = 'near "x"'
    starts = {k for k in KEYWORDS if consumes("", k)}
    after = {k for k in KEYWORDS if consumes(whole, k)}
    return sorted({("as of" if k == "as" else k) for k in starts | after} - {ACTION})


# ── the instance, read ─────────────────────────────────────────────────────────────────────────

#: A number's production → the precedent the elaborator fills in when it is left unsaid.
NUMBER_PRECEDENT = {"reach depth": "depth", "walk depth": "walk_depth", "diffuse beta": "beta",
                    "top": "k", "read chunk": "read_chunk"}


def _ro(path: Path) -> sqlite3.Connection | None:
    """A read-only connection (`mode=ro`): opening it can neither create nor write the file."""
    if not path.is_file():
        return None
    try:
        return sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=0.5)
    except sqlite3.Error:
        return None


@dataclass
class Catalog:
    """What completion offers from the instance: identifiers and paths the stores hold, the
    strata the type checker accepts, the corpus sources declared, the precedents in force."""

    atoms: tuple[str, ...] = ()
    sources: tuple[str, ...] = ()
    precedents: Precedents = DEFAULT
    limit: int = 20_000

    @property
    def strata(self) -> tuple[str, ...]:
        # what `over` accepts (types._strata): every stratum but the denylist's
        return tuple(s.value for s in Stratum if s is not Stratum.FOUNDATION)

    @classmethod
    def of(cls, cfg: Any, *, limit: int = 20_000) -> Catalog:
        """Read the catalog and the reference index read-only; an absent or busy store gives
        nothing to complete, never an error."""
        atoms: list[str] = []
        queries = ((Path(cfg.paths.vault_catalog),
                    "SELECT source_path, title FROM vault_files WHERE active = 1 "
                    "ORDER BY source_path LIMIT ?"),
                   (Path(cfg.paths.data_dir) / "reference_edges.sqlite",
                    "SELECT DISTINCT source_ref, target_ref FROM reference_edges LIMIT ?"))
        for path, sql in queries:
            con = _ro(path)
            if con is None:
                continue
            try:
                for a, b in con.execute(sql, (limit,)):
                    atoms += [str(a), str(b)]
            except sqlite3.Error:
                pass
            finally:
                con.close()
        corpus = cfg.ingestion.corpus
        sources = tuple(corpus.sources) if corpus.enabled else ()
        seen = dict.fromkeys(a for a in atoms if a)
        return cls(atoms=tuple(seen)[:limit], sources=sources, limit=limit)

    def note_candidates(self) -> list[str]:
        """A note is a quoted path, digest or title, or a bare word that is no keyword."""
        word = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_./:#@\-]*")
        out = [f"corpus/{s}/" for s in self.sources]
        for a in self.atoms:
            out.append(quote(a))
            if word.fullmatch(a) and a not in KEYWORDS:
                out.append(a)
        return out

    def number_default(self, production: str) -> str | None:
        name = NUMBER_PRECEDENT.get(production)
        if name is None:
            return None
        v = getattr(self.precedents, name)
        return f"{v:g}" if isinstance(v, float) else str(v)


# ── completion ─────────────────────────────────────────────────────────────────────────────────

COMMANDS = ("plan", "run", "help", "?", ":cheat", ":precedents", ":quit")


def split_fragment(buffer: str) -> tuple[str, str]:
    """The text before the word being typed, and that word: an open quote runs to the end; else
    the word starts after the last space or parenthesis."""
    quotes = [m.start() for m in re.finditer(r'(?<!\\)"', buffer)]
    if len(quotes) % 2 == 1:
        return buffer[:quotes[-1]], buffer[quotes[-1]:]
    m = re.search(r"[^\s()]*$", buffer)
    start = m.start() if m else len(buffer)
    return buffer[:start], buffer[start:]


@dataclass
class Completer:
    catalog: Catalog

    def complete(self, buffer: str) -> list[str]:
        """The candidates for the word being typed at the end of `buffer`, each a whole word
        that starts with it."""
        prefix, frag = split_fragment(buffer)
        stripped = prefix.lstrip()
        head = stripped.split(maxsplit=1)[0] if stripped.split() else ""
        if not stripped:                                   # the line's first word
            return _matching([*COMMANDS, *accepted_keywords("")], frag)
        if head in ("help", "?") and len(stripped.split()) == 1:
            return _matching(parser_verbs(), frag)
        if head in (":cheat", ":precedents", ":quit"):
            return []
        sentence = stripped[len(head):] if head in ("plan", "run") else stripped
        return _matching(self.sentence(sentence), frag)

    def sentence(self, prefix: str) -> list[str]:
        out = accepted_keywords(prefix)
        symbols = [c for c in SYMBOLS if consumes(prefix, c)]
        s = slot(prefix)
        if s.kind == "note":
            out += self.catalog.note_candidates()
        elif s.kind == "strata":
            out += self.catalog.strata
        elif s.kind == "number":
            d = self.catalog.number_default(s.production)
            out += [d] if d is not None else []
        elif s.kind == "path":
            # a path takes any word up to the parser's stop words, so only the relation letters
            # and the stop words are offered, then the path's own symbols
            out = [k for k in out if k in RELATIONS or k in _STOP_PATH]
        elif s.kind == "string":
            out.append('"')
        return list(dict.fromkeys(out + symbols))


def _matching(cands: Iterable[str], frag: str) -> list[str]:
    return [c for c in cands if c.startswith(frag)]


# ── help ───────────────────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Verb:
    """A verb's help: its shapes (checked against the parser by the tests), one example, what
    it returns. `<s>` is a sentence; `<note>` a quoted path, digest or title."""

    shapes: tuple[str, ...]
    example: str
    returns: str


VERBS: dict[str, Verb] = {
    "near": Verb(('near <text>',), 'near "sleep debt"',
                 "a field: a score per note, the embedding kernel's column at the text"),
    "diffuse": Verb(("diffuse [S|F|D|C] from <note> [beta <number>]",),
                    'diffuse S from "health/sleep.md" beta 2',
                    "a field: the retrieval curve e^(-beta d) out of the note"),
    "far": Verb(("far <s>",), 'near "x" and far near "y"',
                "a field: the bounded reversal 1 - f of a field"),
    "reach": Verb(("reach [S|F|D|C] from <note> [depth <n>] [forward|back|both]",),
                  'reach F from "core/query.py" depth 2 back',
                  "a region: the notes reachable along the relation, with their hops"),
    "relate": Verb(("relate <note>",), 'relate "health/sleep.md"',
                   "a region: the notes a signed relation edge ties to the note"),
    "top": Verb(("top <n> <s>",), 'top 10 near "x"',
                "a region: the k best of a field, with their scores"),
    "atleast": Verb(("atleast <number> <s>",), 'atleast 0.5 near "x"',
                    "a region: the notes whose score reaches the threshold"),
    "not": Verb(("not <s>",), 'reach F from "a.md" and not reach F from "b.md"',
                "a region: the complement of a region in the universe"),
    "minus": Verb(("<s> minus <s>",), 'reach F from "a.md" minus reach F from "b.md"',
                  "a region: the left region without the right"),
    "and": Verb(("<s> and <s>",), 'near "x" and reach F from "n.md"',
                "a field (the product, or a field masked by a region) or a region (the meet)"),
    "or": Verb(("<s> or <s>",), 'near "x" or near "y"',
               "a field (the convex mixture) or a region (the union)"),
    "then": Verb(("<s> then <s>",), 'reach F from "n.md" back then near "x"',
                 "the right sentence, masked by the left one's region"),
    "trace": Verb(("trace <note> [forward|back|both]",), 'trace "health/sleep.md" back',
                  "chains: the note's version chain along D"),
    "walk": Verb(("walk from <note> [to <note>] via <path> [depth <n>]",),
                 'walk from "a.md" to "b.md" via F+',
                 "chains: the paths a regular language over S F D C admits"),
    "witness": Verb(("witness <text>",), 'witness "e-1"',
                    "the record that minted an edge, or the attestation a receipt names"),
    "read": Verb(("read <note> [chunk <n>]",), 'read "core/sealing.py" chunk 2',
                 "the text at a ref: a note, a turn, or a window of a paper or a repo file"),
    "within": Verb(("<s> within <s>",), 'near "x" within reach F from "n.md" depth 2',
                   "the left sentence restricted to the right one's region"),
    "over": Verb(("<s> over <strata>",), 'near "x" over curated reference',
                 "the sentence evaluated on the named strata instead of the default"),
    "as of": Verb(("<s> as of <text>",), 'reach F from "core/query.py" as of "HEAD"',
                  "the sentence with the citation graph read at that commit"),
    "assume": Verb(("assume S|F|D|C <note> <note> [+|- <number>] in <s>",
                    "assume sever S|F|D|C <note> <note> in <s>",
                    "assume contradict <note> <note> in <s>"),
                   'assume sever F "a.md" "b.md" in reach F from "a.md" depth 3',
                   "a Hyp: the answer on the perturbed graph beside the actual one, never an Inv"),
}

#: Where the elaborator's defaults bite, per verb (the precedents' names).
VERB_PRECEDENTS = {"near": ("strata", "support"), "diffuse": ("diffuse_rel", "beta"),
                   "reach": ("reach_rel", "depth", "reach_direction"),
                   "trace": ("trace_direction",), "walk": ("walk_depth", "walk_limit"),
                   "read": ("read_chunk", "read_window"), "top": ("k",)}


def verb_help(name: str, precedents: Precedents = DEFAULT) -> str:
    v = VERBS.get(name)
    if v is None:
        return f"no verb {name!r}; the verbs: {', '.join(parser_verbs())}"
    lines = [*v.shapes, f"  example: {v.example}", f"  returns: {v.returns}"]
    defaults = [f"{p} = {_value(getattr(precedents, p))}" for p in VERB_PRECEDENTS.get(name, ())]
    if defaults:
        lines.append(f"  defaults: {', '.join(defaults)}")
    return "\n".join(lines)


def _value(v: object) -> str:
    if isinstance(v, tuple):
        return " ".join(str(getattr(x, "value", x)) for x in v)
    return str(getattr(v, "value", v))


def verb_list() -> str:
    """The cheat sheet's verbs, generated: every verb the parser accepts, its shape, what it
    returns and one example (`tests/unit/test_sentence_shell.py` pins the document to it)."""
    rows = []
    for name in parser_verbs():
        v = VERBS[name]
        shapes = " · ".join(f"`{s}`" for s in v.shapes)
        rows.append(f"- **{name}** {shapes}: {v.returns}. Example: `{v.example}`")
    return "\n".join(rows)


OVERVIEW = """\
Type a sentence and press Enter to run it. Tab completes.
  <sentence> | run <sentence>   execute, print the hits, their provenance and the notes
  plan <sentence>               the compiled plan and the universe's support, not executed
  help [verb] | ? [verb]        the verbs, or one verb's shape, example and result
  :cheat                        the cheat sheet
  :precedents                   the defaults a sentence leaves unsaid
  :quit                         leave (or Ctrl-D)
A sentence the parser can still complete continues on the next line; an empty line ends it.
verbs: """


# ── the shell ──────────────────────────────────────────────────────────────────────────────────


class Refused(Exception):
    """A sentence the shell will not run, with why."""


def caret(text: str, message: str) -> str:
    """The refusal with a caret under the position the parser names."""
    m = re.search(r" at (\d+)\b", message)
    pos = int(m.group(1)) if m else (len(text) if "end of the sentence" in message else None)
    if pos is None:
        return message
    line = text.replace("\n", " ")
    while pos < len(line) and line[pos].isspace():      # a token's position counts its spaces
        pos += 1
    return f"{message}\n  {line}\n  {' ' * pos}^"


@dataclass
class Shell:
    """The command interpreter, front-end free: `handle` takes one composed entry and returns
    what to print. `engine` is opened lazily, so help and completion never touch a store."""

    open_engine: Callable[[], Any]
    grant: Any
    catalog: Catalog
    precedents: Precedents = DEFAULT
    _engine: Any = None

    @property
    def engine(self) -> Any:
        if self._engine is None:
            self._engine = self.open_engine()
        return self._engine

    def handle(self, entry: str) -> str:
        text = entry.strip()
        if not text:
            return ""
        head, _, rest = text.partition(" ")
        if text in ("help", "?", ":help"):
            return OVERVIEW + ", ".join(parser_verbs())
        if head in ("help", "?"):
            return verb_help(rest.strip(), self.precedents)
        if text.endswith("?") and text[:-1].strip() in VERBS:
            return verb_help(text[:-1].strip(), self.precedents)
        if text == ":cheat":
            return cheat_sheet()
        if text == ":precedents":
            return "\n".join(f"{f.name} = {_value(getattr(self.precedents, f.name))}"
                             for f in fields(self.precedents))
        if head == "plan":
            return self.plan(rest)
        if head == "run":
            return self.run(rest)
        if head.startswith(":"):
            return f"unknown command {head!r}; try help"
        return self.run(text)

    def _compile(self, text: str) -> Any:
        from core.sentence.plan import compile_sentence

        if is_request(text):
            raise Refused("refused (read-only): a request ('do ...') is the action sort; it "
                          "lands through the daemon's writer and its lock, which this shell "
                          "never takes. Ask it with `mind-palace query` instead.")
        return compile_sentence(text, self.grant, precedents=self.precedents)

    def _refusal(self, text: str, e: BaseException) -> str:
        from core.sentence.surface import refusal_class

        if isinstance(e, Refused):
            return str(e)
        if isinstance(e, sqlite3.OperationalError) and "locked" in str(e):
            return ("refused (busy): a store is locked by its writer (the daemon); the shell "
                    "takes no lock and does not wait for one. Try again when it is idle.")
        cls = refusal_class(e)
        if not cls:
            raise e
        return caret(text, f"refused ({cls}): {e}") if cls == "parse" else f"refused ({cls}): {e}"

    def plan(self, text: str) -> str:
        """The compiled plan, the seeds, and the universe's support and `missing`: nothing is
        executed."""
        from core.sentence.universe import admitted_strata, build, seeds_of

        text = text.strip()
        try:
            plan = self._compile(text)
        except Exception as e:  # noqa: BLE001 - a refusal is rendered, anything else re-raised
            return self._refusal(text, e)
        seeds = seeds_of(plan.term, self.precedents)
        lines = [plan.explain(), "seeds:"]
        lines += [f"  text of {len(t)} characters over {', '.join(sorted(s.value for s in st))}"
                  for t, st in seeds.texts]
        lines += [f"  anchor {a} within {r} hops" for a, r in seeds.anchors]
        if seeds.moves:
            lines.append(f"  moves: {' '.join(sorted(m.value for m in seeds.moves))}")
        if seeds.cut:
            lines.append(f"  cut: {seeds.cut}")
        lines.append("strata admitted: " + ", ".join(
            sorted(s.value for s in admitted_strata(plan, self.precedents))))
        try:
            u = build(self.engine, plan, precedents=self.precedents)
        except Exception as e:  # noqa: BLE001 - the plan stands; the support is reported absent
            if isinstance(e, sqlite3.OperationalError) and "locked" in str(e):
                return "\n".join(lines) + "\n" + self._refusal(text, e)
            lines.append(f"support: not built ({type(e).__name__}: {e})")
            return "\n".join(lines)
        lines.append(f"support: {len(u)} nodes")
        lines.append("missing:")
        lines += [f"  - {m}" for m in u.missing]
        return "\n".join(lines)

    def run(self, text: str) -> str:
        from core.sentence.execute import execute
        from core.sentence.surface import render_text
        from core.sentence.universe import build

        text = text.strip()
        try:
            plan = self._compile(text)
            answer = execute(plan, build(self.engine, plan, precedents=self.precedents),
                             precedents=self.precedents)
        except Exception as e:  # noqa: BLE001 - a refusal is rendered, anything else re-raised
            return self._refusal(text, e)
        return render_text(answer, plan=False)


def needs_more(buffer: str) -> bool:
    """Whether a composed entry continues on the next line: a trailing backslash, an open quote,
    or a sentence the parser fails on only at its end (it can still be completed)."""
    text = buffer.rstrip()
    if not text:
        return False
    if text.endswith("\\"):
        return True
    head = text.split(maxsplit=1)[0]
    if head in ("help", "?") or head.startswith(":"):
        return False
    sentence = text[len(head):] if head in ("plan", "run") else text
    if not sentence.strip() or is_request(sentence):
        return False
    if len(re.findall(r'(?<!\\)"', sentence)) % 2 == 1:
        return True
    try:
        _Parser(sentence).parse()
    except ParseError as e:
        return str(e).endswith("got the end of the sentence")
    return False


def cheat_sheet() -> str:
    try:
        return CHEAT_SHEET.read_text(encoding="utf-8").rstrip("\n")
    except OSError:                              # an installed copy without docs/
        return verb_list()


# ── the front end ──────────────────────────────────────────────────────────────────────────────


def history_path() -> Path:
    return Path(os.environ.get(HISTORY_ENV) or HISTORY_DEFAULT).expanduser()


def _readline(completer: Completer, pending: list[str]) -> Any:
    """Wire the standard library's readline: completion over the whole composed entry, and a
    history file kept across sessions."""
    try:
        import readline
    except ImportError:                          # a platform without it: no completion
        return None
    matches: list[str] = []

    def complete(text: str, state: int) -> str | None:
        nonlocal matches
        if state == 0:
            line = readline.get_line_buffer()[:readline.get_endidx()]
            buffer = "\n".join([*pending, line])
            _, frag = split_fragment(buffer)
            cut = len(frag) - len(text)           # readline's word is a suffix of ours
            matches = [c[cut:] for c in completer.complete(buffer)] if cut >= 0 else []
        return matches[state] if state < len(matches) else None

    readline.set_completer(complete)
    readline.set_completer_delims(" \t\n()")
    if "libedit" in (readline.__doc__ or ""):
        readline.parse_and_bind("bind ^I rl_complete")
    else:
        readline.parse_and_bind("tab: complete")
    path = history_path()
    try:
        readline.read_history_file(path)
    except OSError:
        pass
    readline.set_history_length(5000)
    return readline


def repl(shell: Shell, *, stdin: TextIO | None = None, out: TextIO | None = None,
         interactive: bool | None = None) -> int:
    """Read entries, compose multi-line ones, print what `handle` returns."""
    stdin = stdin if stdin is not None else sys.stdin
    out = out if out is not None else sys.stdout
    interactive = stdin.isatty() if interactive is None else interactive
    pending: list[str] = []
    rl = _readline(Completer(shell.catalog), pending) if interactive else None
    if interactive:
        print("mind-palace shell: read-only sentences. help for the commands, Tab to complete, "
              "Ctrl-D to leave.", file=out)
    try:
        while True:
            prompt = MORE if pending else PROMPT
            try:
                line = input(prompt) if interactive else _next(stdin)
            except EOFError:
                break
            except KeyboardInterrupt:
                pending.clear()
                print(file=out)
                continue
            if pending and not line.strip():
                entry = "\n".join(pending)
            else:
                cont = line.rstrip().endswith("\\")
                pending.append(line.rstrip()[:-1] if cont else line)
                entry = "\n".join(pending)
                if cont or needs_more(entry):
                    continue
            pending.clear()
            if entry.strip() in (":quit", ":q", "exit", "quit"):
                break
            result = shell.handle(entry)
            if result:
                print(result, file=out)
    finally:
        if rl is not None:
            path = history_path()
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                rl.write_history_file(path)
            except OSError:
                pass
    return 0


def _next(stdin: TextIO) -> str:
    line = stdin.readline()
    if not line:
        raise EOFError
    return line.rstrip("\n")


def open_shell(cfg: Any | None = None) -> Shell:
    """The shell over the instance the configuration names, under the surfaces' grant."""
    from core.kernel.config import get_config
    from core.query import QueryEngine
    from core.sentence.surface import sentence_grant

    cfg = cfg if cfg is not None else get_config()
    return Shell(open_engine=lambda: QueryEngine(cfg), grant=sentence_grant(),
                 catalog=Catalog.of(cfg))


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] in ("-h", "--help"):
        print("usage: mind-palace shell     a read-only REPL over the sentence language\n\n"
              + OVERVIEW + ", ".join(parser_verbs()))
        return 0
    if args:
        print("usage: mind-palace shell", file=sys.stderr)
        return 2
    return repl(open_shell())


if __name__ == "__main__":
    raise SystemExit(main())
