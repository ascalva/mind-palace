"""The surface of the query sentence algebra — `palace query`, the Ambassador's `query` tool and the
query log as a sensor (dn-query-sentence-algebra §3, QL-3; the lessons loop of
docs/brainstorms/scoped-context-queries.md).

Every sentence a surface asks goes through `ask_logged`: compile it under the client's grant, run
it against the live universe, and append one line to the query log — the sentence, the surface and
the role that asked, the strata its clauses read, the modes, and the outcome: `answered`, `empty`
(well-formed, admissible, nothing there: the mechanical proxy for a translation that failed) or
`refused`, with the refusal's class (`parse`, `sort`, `scope`, `ambiguous`, `lookup`,
`unsupported`) and its reason. The log holds no note text: a sentence is the asker's own words and
the hits are counted, never named. `summarize` reads the log back as the sensor the brainstorm
asked for — which strata serve which roles, which translations fail — and `palace query --log`
renders it. A sensor never breaks the instrument: a log that cannot be written is reported on
stderr and the answer is returned anyway.

`run_query` is `palace query` (scripts/palace.py): read-only, under `sentence_grant()` — the
Ambassador's grant with the hypothetical overlay the owner granted on 2026-11-04 (the note's
§4 d; `[query] hypotheticals` turns it off). `--as <role>` labels the asker for the sensor and
grants nothing.
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
from core.sentence.types import (
    AmbiguousSentence,
    IllScopedSentence,
    Sort,
    SortError,
    clauses_of,
)

LOG_NAME = "query_log.jsonl"
REASON_MAX = 240   # a refusal's reason, truncated: the log is a sensor, not a transcript
USAGE = ('usage: palace query "<sentence>" [--json] [--no-plan] [--as <role>]\n'
         "       palace query --log [--json]      the sensor: strata by role, failed translations")


# ── the log ────────────────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Entry:
    """One line of the query log."""

    at: str                      # UTC, to the second
    surface: str                 # cli | mcp
    role: str                    # who asked, a label for the sensor — never a permission
    sentence: str
    outcome: str                 # answered | empty | refused
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
    return ""


# ── the logged ask ─────────────────────────────────────────────────────────────────────────────


def ask_logged(text: str, grant: Grant, *, surface: str, role: str,
               engine: QueryEngine | None = None, universe: Universe | None = None,
               log: QueryLog | None = None, precedents: Precedents = DEFAULT) -> SentenceAnswer:
    """Compile `text` under `grant`, run it, log the outcome; a refusal is logged, then raised."""
    log = log if log is not None else default_log()
    started = time.perf_counter()
    plan: Plan | None = None
    try:
        plan = compile_sentence(text, grant, precedents=precedents)
        if universe is not None:
            u = universe
        elif plan.sort is Sort.TEXT and plan.is_inv:   # a bare read opens no note graph
            u = Universe.reader(engine or QueryEngine())
        else:
            u = Universe.from_engine(engine or QueryEngine())
        answer = execute(plan, u, precedents=precedents)
    except Exception as e:
        log.record(_entry(text, surface, role, started, plan, precedents, outcome="refused",
                          refusal=refusal_class(e) or "error", reason=str(e)[:REASON_MAX]))
        raise
    n = max(len(answer.hits), 0 if answer.hyp is None else len(answer.hyp.value))
    log.record(_entry(text, surface, role, started, plan, precedents,
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
                   for e in rows if e.outcome != "answered"][-10:],
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


def render_text(answer: SentenceAnswer, *, plan: bool = True) -> str:
    """The answer as text: the sentence, its sort and modes, the plan, the hits with their
    provenance, the assumed hits beside the actual ones under `assume`, and the notes."""
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
    """`palace query "<sentence>" [--json] [--no-plan] [--as <role>]`, and `palace query --log`.
    Exit 0 for an answer (an empty one included: it says what emptied it), 1 for a refusal, 2 for
    usage. The grant is `sentence_grant()` unless one is passed."""
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
    if flags - {"--json", "--no-plan", "--log"} or ("--log" in flags) == bool(words):
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
                            universe=universe, log=log)
    except Exception as e:
        cls = refusal_class(e)
        if not cls:
            raise
        print(json.dumps({"refused": cls, "reason": str(e)}, ensure_ascii=False) if as_json
              else f"refused ({cls}): {e}", file=out)
        return 1
    print(json.dumps(answer.to_dict(), ensure_ascii=False, indent=1) if as_json
          else render_text(answer, plan="--no-plan" not in flags), file=out)
    return 0
