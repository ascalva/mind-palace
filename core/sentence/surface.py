"""The surface of the query sentence algebra — `palace query`, the Ambassador's `query` tool and the
query log as a sensor (dn-query-sentence-algebra §3, QL-3; the lessons loop of
docs/brainstorms/scoped-context-queries.md).

Every sentence a surface asks goes through `ask_logged`: compile it under the client's grant, run
it against the live universe, and append one line to the query log — the sentence, the surface and
the role that asked, the strata its clauses read, the modes, and the outcome: `answered`, `empty`
(well-formed, admissible, nothing there: the mechanical proxy for a translation that failed) or
`refused`, with the refusal's class (`parse`, `sort`, `scope`, `ambiguous`, `lookup`,
`unsupported`) and its reason, or `requested` for a command the ingress spooled. The log holds no
note text: a sentence is the asker's own words and the hits are counted, never named; a command's
string literals, which may be corpus text (`do capture "…"`), are logged as their lengths
(`redact_command`). `summarize` reads the log back as the sensor the brainstorm asked for — which
strata serve which roles, which translations fail — and `palace query --log` renders it. A sensor
never breaks the instrument: a log that cannot be written is reported on stderr and the answer is
returned anyway.

`run_query` is `palace query` (scripts/palace.py): read-only, under `sentence_grant()` — the
Ambassador's grant with the hypothetical overlay the owner granted on 2026-11-04 (the note's
§4 d; `[query] hypotheticals` turns it off). `--as <role>` labels the asker for the sensor and
grants nothing: a command the CLI speaks goes to the ingress as the role `cli`, whatever the label
(`ingress_role`), and the MCP's `query` speaks as `ambassador`.
"""

from __future__ import annotations

import json
import sys
import time
from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, fields
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TextIO

from core.kernel.config import get_config
from core.query import AMBASSADOR, AMBASSADOR_OVERLAY, Grant, Hit, QueryEngine
from core.sentence.execute import SentenceAnswer, Universe, UnsupportedSentence, execute
from core.sentence.grammar import ParseError, parse
from core.sentence.plan import Plan, compile_sentence, normalize
from core.sentence.precedents import DEFAULT, Precedents
from core.sentence.trace import Trace
from core.sentence.types import (
    MIRROR_NAMES,
    AmbiguousSentence,
    IllScopedSentence,
    Sort,
    SortError,
    clauses_of,
)

LOG_NAME = "query_log.jsonl"
REASON_MAX = 240   # a refusal's reason, truncated: the log is a sensor, not a transcript
MAX_COMMAND_BYTES = 32 * 1024     # the ingress's cap (`core/ingest/ingress.py`), checked first
USAGE = ('usage: palace query "<sentence>" [--json] [--no-plan] [--trace] [--as <role>]\n'
         "       palace query --log [--json]      the sensor: strata by role, failed translations")


# ── the log ────────────────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Entry:
    """One line of the query log."""

    at: str                      # UTC, to the second
    surface: str                 # cli | mcp
    role: str                    # who asked, a label for the sensor — never a permission
    sentence: str
    outcome: str                 # answered | empty | refused | requested (a command spooled)
    refusal: str = ""            # parse | sort | scope | ambiguous | lookup | unsupported | error
    reason: str = ""
    sort: str = ""
    modes: tuple[str, ...] = ()
    strata: tuple[str, ...] = ()
    hits: int = 0
    hyp: bool = False
    ms: int = 0


_FIELDS = {f.name for f in fields(Entry)}


@dataclass(frozen=True)
class QueryLog:
    """An append-only JSON-lines file under the data dir; one `Entry` per sentence asked."""

    path: Path

    def record(self, entry: Entry) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")
        except OSError as e:   # the sensor never breaks the instrument
            print(f"query log not written ({self.path}): {e}", file=sys.stderr)

    def entries(self) -> list[Entry]:
        if not self.path.exists():
            return []
        out: list[Entry] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            d = {k: v for k, v in json.loads(line).items() if k in _FIELDS}
            d["modes"], d["strata"] = tuple(d.get("modes", ())), tuple(d.get("strata", ()))
            out.append(Entry(**d))
        return out


def default_log() -> QueryLog:
    return QueryLog(get_config().paths.data_dir / LOG_NAME)


def sentence_grant() -> Grant:
    """The grant the surfaces evaluate under: the Ambassador's, widened by the hypothetical
    overlay while `[query] hypotheticals` is on — the owner's grant of 2026-11-04 (the note's
    §4 d). A result under `assume` is a `Hyp` either way; the switch only decides whether the
    sentence is admitted at all."""
    return AMBASSADOR_OVERLAY if get_config().query.hypotheticals else AMBASSADOR


def refusal_class(e: BaseException) -> str:
    """The class a refusal is logged and rendered under; `''` for an exception that is not one."""
    if isinstance(e, ParseError):
        return "parse"
    if isinstance(e, SortError):
        return "sort"
    if isinstance(e, IllScopedSentence):
        return "scope"
    if isinstance(e, AmbiguousSentence):
        return "ambiguous"
    if isinstance(e, UnsupportedSentence):
        return "unsupported"
    if isinstance(e, LookupError):
        return "lookup"
    from core.ingest.ingress import Busy

    if isinstance(e, Busy):
        return "busy"
    return ""


# ── the logged ask ─────────────────────────────────────────────────────────────────────────────




def is_command(text: str) -> bool:
    from core.sentence.grammar import is_request

    return is_request(text)


def _redact(text: str, *, sentences: bool = True) -> str:
    """Each quoted string replaced by its length in characters, an unterminated one cut at its
    quote; inside backquotes (a nested sentence) the same, the sentence's own strings included.
    One pass over the text: a hostile text costs what any text does (a regex over escapes is
    quadratic on an unterminated string)."""
    out: list[str] = []
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c in "\"'":
            j = i + 1
            while j < n and text[j] != c and text[j] != "\n":
                j += 2 if text[j] == "\\" else 1
            if j < n and text[j] == c:
                out.append(f'"<{j - i - 1}>"')
                i = j + 1
            else:
                out.append(f"<{n - i} characters, unterminated>")
                i = n
        elif c == "`" and sentences:
            j = text.find("`", i + 1)
            end = n if j < 0 else j
            out.append("`" + _redact(text[i + 1:end], sentences=False) + ("`" if j >= 0 else ""))
            i = end + 1
        else:
            out.append(c)
            i += 1
    return "".join(out)


def redact_command(text: str) -> str:
    """A request as the log keeps it: each quoted string replaced by its length in characters, in
    the script and in any sentence nested in it, so a captured text or a turn's words never enter
    the query log; an unterminated string cut at its quote; whitespace collapsed."""
    return " ".join(_redact(text).split())[:4096]


def _command_word(text: str) -> str:
    words = text[:256].split(maxsplit=2)
    return words[1] if len(words) > 1 and words[1].isidentifier() else "?"


def redact_reason(reason: str) -> str:
    """A refusal's reason as the log keeps it for a command: every quoted run replaced by its
    length, since a refusal may name a conversation or a text. A reason's own apostrophe opens
    a run too, so the log may keep less of a reason than it says, never more."""
    return _redact(reason)


def ask_logged(text: str, grant: Grant, *, surface: str, role: str,
               engine: QueryEngine | None = None, universe: Universe | None = None,
               log: QueryLog | None = None, precedents: Precedents = DEFAULT,
               trace: bool = False, ingress_role: str | None = None) -> SentenceAnswer:
    """Compile `text` under `grant`, run it, log the outcome; a refusal is logged, then raised.
    With `trace`, the answer carries its proof of work (`core/sentence/trace.py`); the log entry
    is the same either way. A command (`do …`) compiles under the grant of `ingress_role`, the role
    the surface speaks for at the ingress (`role` when not given), and is spooled for the daemon."""
    log = log if log is not None else default_log()
    started = time.perf_counter()
    plan: Plan | None = None
    t = Trace() if trace else None
    command = is_command(text)
    ingress_role = ingress_role if ingress_role is not None else role
    if command and len(text.encode("utf-8")) > MAX_COMMAND_BYTES:
        e = ValueError(f"a command is at most {MAX_COMMAND_BYTES} bytes")
        log.record(_entry(f"do {_command_word(text)} <{len(text)} characters, over the cap>",
                          surface, role, started, None, precedents, outcome="refused",
                          refusal="error", reason=str(e)))
        raise e
    logged = redact_command(text) if command else text
    try:
        # a command compiles under the grant of the role that speaks it (dn-ingress D3):
        # the first check; the daemon's writer makes the second
        if command:
            from core.ingest import ingress

            grant = ingress.grant_for(ingress_role)
        plan = compile_sentence(text, grant, precedents=precedents, trace=t,
                                role=ingress_role if command else None)
        if plan.sort is Sort.EVENT:
            from core.ingest import ingress

            cfg = engine.config if engine is not None else get_config()
            receipt = ingress.write_request(cfg, role=ingress_role, plan=plan)
            if t is not None:
                t.note("act", f"request {receipt.request} spooled for role {ingress_role!r} as "
                              f"kind {receipt.kind!r}: the daemon evaluates its script and its "
                              "one writer lands the plan, then writes the receipt", "ING-4")
            from core.sentence.ast import Do
            from core.sentence.script import CallScript

            request = plan.term.request if isinstance(plan.term, Do) else None
            title = request.name if isinstance(request, CallScript) else "inline script"
            answer = SentenceAnswer(
                plan, (Hit(ref=f"ingress:{receipt.request}", title=title, stratum="ingress",
                           provenance=ingress_role, detail=receipt.to_dict()),), None,
                ("the request is written for the daemon's one writer; the receipt names it, "
                 "and `palace queue` shows the job (dn-ingress-language §E6)",), t)
            log.record(_entry(logged, surface, role, started, plan, precedents,
                              outcome="requested", hits=1))
            return answer
        if universe is not None:
            u = universe
        elif plan.sort is Sort.TEXT and plan.is_inv:   # a bare read opens no note graph
            u = Universe.reader(engine or QueryEngine())
        else:
            from core.sentence.universe import build

            # a grant that names no stratum of the mirror (the guest's) is shown no vault path:
            # the universe withholds what the other stores say of the notes (dn-guest-principal)
            hide = {"hide_mirror": True} if not grant.strata & MIRROR_NAMES else {}
            u = build(engine or QueryEngine(), plan, precedents=precedents, trace=t, **hide)
        answer = execute(plan, u, precedents=precedents, trace=t)
    except Exception as e:
        reason = redact_reason(str(e)) if command else str(e)
        log.record(_entry(logged, surface, role, started, plan, precedents, outcome="refused",
                          refusal=refusal_class(e) or "error", reason=reason[:REASON_MAX]))
        raise
    n = max(len(answer.hits), 0 if answer.hyp is None else len(answer.hyp.value))
    log.record(_entry(logged, surface, role, started, plan, precedents,
                      outcome="answered" if n else "empty", hits=n, hyp=answer.hyp is not None))
    return answer


def _entry(text: str, surface: str, role: str, started: float, plan: Plan | None,
           precedents: Precedents, **rest: Any) -> Entry:
    sort, modes, strata = _shape(text, plan, precedents)
    return Entry(at=datetime.now(UTC).replace(tzinfo=None).isoformat(timespec="seconds"),
                 surface=surface, role=role, sentence=text, sort=sort, modes=modes, strata=strata,
                 ms=int((time.perf_counter() - started) * 1000), **rest)


def _shape(text: str, plan: Plan | None,
           precedents: Precedents) -> tuple[str, tuple[str, ...], tuple[str, ...]]:
    """The sort, modes and strata a sentence asked for: from its plan, or, for a sentence refused
    before it had one, from its clauses alone (so a scope refusal still says which strata it
    wanted); nothing for a sentence that does not parse."""
    if plan is not None:
        clauses, sort = plan.clauses, plan.sort.value
    else:
        try:
            clauses, sort = clauses_of(normalize(parse(text)), precedents=precedents), ""
        except Exception:
            return "", (), ()
    modes = tuple(sorted({c.mode.value for c in clauses}))
    strata = tuple(sorted({s.value for c in clauses for s in c.req.sigma.strata}))
    return sort, modes, strata


# ── the sensor ─────────────────────────────────────────────────────────────────────────────────


def summarize(entries: Iterable[Entry]) -> dict[str, Any]:
    """Which strata served which roles, and which translations failed (the lessons loop)."""
    rows = list(entries)
    served: dict[str, Counter[str]] = {}
    for e in rows:
        served.setdefault(f"{e.role} · {','.join(e.strata) or '∅'}", Counter())[e.outcome] += 1
    return {
        "asked": len(rows),
        "outcomes": dict(sorted(Counter(e.outcome for e in rows).items())),
        "served": {k: dict(sorted(v.items())) for k, v in sorted(served.items())},
        "refusals": dict(sorted(Counter(e.refusal for e in rows
                                        if e.outcome == "refused").items())),
        "failed": [{"at": e.at, "role": e.role, "sentence": e.sentence,
                    "why": f"{e.refusal}: {e.reason}" if e.outcome == "refused" else "empty"}
                   for e in rows if e.outcome in ("refused", "empty")][-10:],
    }


def render_summary(s: Mapping[str, Any]) -> str:
    counts = "  ".join(f"{k} {v}" for k, v in s["outcomes"].items())
    lines = [f"asked: {s['asked']}  {counts}".rstrip()]
    if s["served"]:
        lines.append("served (role · strata):")
        lines += [f"  {k}: " + ", ".join(f"{o} {n}" for o, n in v.items())
                  for k, v in s["served"].items()]
    if s["refusals"]:
        lines.append("refusals: " + ", ".join(f"{k} {v}" for k, v in s["refusals"].items()))
    if s["failed"]:
        lines.append("failed translations (last 10):")
        lines += [f"  {f['at']}  {f['role']}  {f['sentence']}  — {f['why']}" for f in s["failed"]]
    return "\n".join(lines)


# ── rendering ──────────────────────────────────────────────────────────────────────────────────


def render_text(answer: SentenceAnswer, *, plan: bool = True, trace: bool = False) -> str:
    """The answer as text: the sentence, its sort and modes, the plan, the hits with their
    provenance, the assumed hits beside the actual ones under `assume`, the notes, and — asked
    for, and carried — the trace."""
    p = answer.plan
    lines = [p.sentence,
             f"sort: {p.sort.value} · modes: {', '.join(p.modes) or '∅'} · "
             f"{'Inv' if p.is_inv else 'Hyp'}"]
    if plan:
        lines += ["  " + ln for ln in p.explain().splitlines()]
    lines += _hits("hits", answer.hits)
    if answer.hyp is not None:
        lines.append("under the assumptions:")
        lines += [f"  {a}" for a in answer.hyp.assumptions]
        lines += _hits("hits assumed", answer.hyp.value)
    if answer.notes:
        lines.append("notes:")
        lines += [f"  - {n}" for n in answer.notes]
    if trace and answer.trace is not None:
        lines.append(answer.trace.render())
    return "\n".join(lines)


def _hits(label: str, hits: tuple[Hit, ...]) -> list[str]:
    out = [f"{label} ({len(hits)}):" if hits else f"{label}: none"]
    for h in hits:
        score = "" if h.score is None else f"{h.score:.4f}  "
        title = f" — {h.title}" if h.title else ""
        tag = h.provenance or h.stratum
        where = f"  [{tag}]" if tag else ""
        detail = ""
        if h.detail:
            detail = "  {" + ", ".join(f"{k}: {v}" for k, v in h.detail.items()) + "}"
        out.append(f"  {score}{h.ref}{title}{where}{detail}")
        if h.text:   # `read`: the record itself, indented under its line
            out += ["    " + ln for ln in h.text.splitlines()]
    return out


# ── `palace query` ─────────────────────────────────────────────────────────────────────────────


def run_query(argv: list[str], *, out: TextIO | None = None, grant: Grant | None = None,
              engine: QueryEngine | None = None, universe: Universe | None = None,
              log: QueryLog | None = None) -> int:
    """`palace query "<sentence>" [--json] [--no-plan] [--trace] [--as <role>]`, and
    `palace query --log`. Exit 0 for an answer (an empty one included: it says what emptied it),
    1 for a refusal, 2 for usage. The grant is `sentence_grant()` unless one is passed; `--trace`
    shows the work."""
    out = out if out is not None else sys.stdout
    grant = grant if grant is not None else sentence_grant()
    args, role = list(argv), "cli"
    if "--as" in args:
        i = args.index("--as")
        if i + 1 >= len(args):
            print(USAGE, file=out)
            return 2
        role = args[i + 1]
        del args[i:i + 2]
    flags = {a for a in args if a.startswith("--")}
    words = [a for a in args if not a.startswith("--")]
    if flags - {"--json", "--no-plan", "--trace", "--log"} or ("--log" in flags) == bool(words):
        print(USAGE, file=out)
        return 2
    as_json = "--json" in flags
    if "--log" in flags:
        s = summarize((log if log is not None else default_log()).entries())
        print(json.dumps(s, ensure_ascii=False, indent=1) if as_json else render_summary(s),
              file=out)
        return 0
    text = " ".join(words)
    try:
        answer = ask_logged(text, grant, surface="cli", role=role, engine=engine,
                            universe=universe, log=log, trace="--trace" in flags,
                            ingress_role="cli")             # `--as` labels; the ingress hears `cli`
    except Exception as e:
        cls = refusal_class(e)
        if not cls:
            raise
        print(json.dumps({"refused": cls, "reason": str(e)}, ensure_ascii=False) if as_json
              else f"refused ({cls}): {e}", file=out)
        return 1
    print(json.dumps(answer.to_dict(), ensure_ascii=False, indent=1) if as_json
          else render_text(answer, plan="--no-plan" not in flags, trace="--trace" in flags),
          file=out)
    return 0
