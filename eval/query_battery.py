"""The falsifier battery of the query sentence algebra (dn-query-sentence-algebra §2.8, QL-4).

    uv run python eval/query_battery.py [--k 5] [--out docs/experiments/query-battery-<date>.md]

Each question of §2.1's table is asked three ways on the live instance — the flat `near`, the
composed sentence, and the composed sentence with its plan — read-only (the executor, not the
logged surface), and written to an experiment record with a column the owner fills: the
endorsed answer set. Where a mechanical proxy exists it is measured beside the owner's column,
never instead of it: a flat answer that interleaves uncited notes with cited ones is counted,
the hypothetical's symbolic class is checked against the numeric movement. A majority of ties
or losses for the sentence retires the layer to a planning aid (QSF-5). Measure; never assume.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))  # repo root on path
os.chdir(ROOT)  # config and data paths resolve against the repo root


@dataclass(frozen=True)
class Row:
    """One question of the battery: its flat form, its composed form, and §2.8's win condition."""

    name: str
    question: str
    flat: str
    composed: str
    wins_when: str
    proxy: str = ""        # the mechanical proxy, named; "" when only the owner can judge


@dataclass
class Answer:
    sentence: str
    hits: list[tuple[str, str, float | None, dict[str, Any]]] = field(default_factory=list)
    plan: str = ""
    notes: list[str] = field(default_factory=list)
    hyp: list[tuple[str, str]] = field(default_factory=list)
    seconds: float = 0.0
    error: str = ""


def _ask(engine: Any, grant: Any, sentence: str, k: int) -> Answer:
    from core.sentence import compile_sentence, execute
    from core.sentence.precedents import Precedents
    from core.sentence.universe import build

    a = Answer(sentence)
    t0 = time.perf_counter()
    try:
        plan = compile_sentence(sentence, grant)
        pre = Precedents(k=k)
        u = build(engine, plan, precedents=pre)
        ans = execute(plan, u, precedents=pre)
        a.hits = [(h.ref, h.title, h.score, dict(h.detail)) for h in ans.hits]
        a.plan = plan.explain()
        a.notes = list(ans.notes)
        if ans.hyp is not None:
            a.hyp = [(h.ref, h.title) for h in ans.hyp.value]
    except Exception as e:   # a refusal is a result of the battery
        a.error = f"{type(e).__name__}: {str(e)[:200]}"
    a.seconds = time.perf_counter() - t0
    return a


def _oldest_cut_with_edges(engine: Any, newest: str) -> str | None:
    """A past cut the citation store holds: the oldest commit of the live checkout's history
    (newest first, 400 deep) that has edges — for the `as of` row."""
    store = engine._get("references")
    try:
        out = subprocess.run(["git", "log", "--format=%H", "-n", "400", newest],
                             capture_output=True, text=True, check=True, cwd=ROOT).stdout.split()
    except (subprocess.CalledProcessError, OSError):
        return None
    for sha in reversed(out):
        if sha != newest and store.for_commit(sha):
            return sha
    return None


def rows_for(engine: Any, k: int) -> list[Row]:
    """The battery, instantiated on the live corpus's own anchors."""
    from core.sentence import compile_sentence
    from core.sentence.universe import build

    notes, _, _ = engine._note_graph()
    note_a = str(notes[0]["source_path"]) if notes else "a.md"
    note_b = str(notes[1]["source_path"]) if len(notes) > 1 else note_a
    cut = build(engine, compile_sentence('reach F from "core/query.py"')).cut or ""
    old = _oldest_cut_with_edges(engine, cut) if cut else None
    rows = [
        Row("near-and-cited-by",
            "the code near 'the egress guard' among what core/sealing.py cites",
            f'top {k} near "the sealed core\'s egress guard" over reference',
            f'top {k} near "the sealed core\'s egress guard" over reference within reach F from '
            f'"core/sealing.py" depth 1',
            "the endorsed cited files rank above uncited near ones; flat search interleaves them",
            "flat hits outside the citation neighbourhood"),
        Row("near-t1-far-t2", "notes near 'retrieval' that are far from 'dreaming'",
            f'top {k} near "retrieval"',
            f'top {k} (near "retrieval" and far near "dreaming")',
            "the endorsed set excludes the dreaming-near notes flat search keeps",
            "flat hits that the composed sentence drops"),
        Row("far-in-text-close-by-citation",
            "what core/sealing.py cites that is far from 'attestation'",
            f'top {k} near "attestation" over reference',
            'reach F from "core/sealing.py" depth 1 minus top 20 near "attestation" over reference',
            "the endorsed cross-domain imports appear; flat search returns none"),
        Row("as-of-a-past-cut", "what core/query.py cited at a past cut",
            'reach F from "core/query.py" depth 1',
            (f'reach F from "core/query.py" depth 1 as of "{old[:12]}"' if old
             else 'reach F from "core/query.py" depth 1 as of "0000000"'),
            "the answer matches the snapshot's; the present differs",
            "files present at one cut and not the other"),
        Row("onboarding-with-bounds",
            "how the palace stays sealed, bounded to the sealing module's neighbourhood",
            f'top {k} near "how does the palace stay sealed"',
            f'top {k} near "how does the palace stay sealed" over reference within '
            f'reach F from "core/sealing.py" depth 2',
            "the endorsed direction files appear and the unbounded list's noise does not"),
        Row("a-hypothetical-s-response",
            "the owner's note's neighbourhood if two notes were linked",
            f'top {k} diffuse S from "{note_a}"',
            f'assume S "{note_a}" "{note_b}" +0.5 in top {k} diffuse S from "{note_a}"',
            "the symbolic sign agrees with the numeric response on every pair",
            "the response class named vs the region's movement"),
        Row("papers-then-read", "papers on Kaplansky's direct finiteness, and the one to read",
            f'top {k} near "Kaplansky direct finiteness conjecture"',
            f'top {k} near "Kaplansky direct finiteness conjecture" over curated',
            "the endorsed papers appear under `over curated`; the flat mirror answer has none"),
        Row("dialogue-recall", "what we talked about regarding the capstone",
            f'top {k} near "my grad capstone"',
            f'top {k} near "my grad capstone" over dialogue',
            "the endorsed turns appear under `over dialogue`"),
    ]
    return rows


def _proxy(row: Row, flat: Answer, comp: Answer) -> str:
    frefs = [h[0] for h in flat.hits]
    crefs = [h[0] for h in comp.hits]
    if row.name == "near-and-cited-by" or row.name == "near-t1-far-t2":
        outside = [r for r in frefs if r not in crefs]
        return f"{len(outside)} of {len(frefs)} flat hits dropped by the composition"
    if row.name == "as-of-a-past-cut":
        now_only, then_only = set(frefs) - set(crefs), set(crefs) - set(frefs)
        return (f"{len(now_only)} now-only, {len(then_only)} then-only, "
                f"{len(set(frefs) & set(crefs))} shared")
    if row.name == "a-hypothetical-s-response":
        cls = [n for n in comp.notes if "resistance" in n or "camps" in n or "gained" in n]
        return " | ".join(c[:90] for c in cls) or "no response note"
    return ""


def render(rows: list[Row], results: list[tuple[Answer, Answer]], *, k: int,
           started: str, seconds: float) -> str:
    out = [f"# The query battery — {started[:10]}", "",
           f"dn-query-sentence-algebra §2.8 (QL-4), run read-only on the live instance at "
           f"{started} with `k = {k}`, {seconds:.1f} s in all. Each question three ways: the flat "
           "`near`, the composed sentence, the plan. **The `endorsed` column is the owner's** — "
           "the held-out arm; the proxy beside it is mechanical and never replaces it. A majority "
           "of ties or losses for the sentence retires the layer to a planning aid (QSF-5).", "",
           "| # | question | wins when | proxy (measured) | endorsed (owner) |",
           "|---|---|---|---|---|"]
    for i, (row, (flat, comp)) in enumerate(zip(rows, results, strict=True), 1):
        out.append(f"| {i} | {row.name}: {row.question} | {row.wins_when} | "
                   f"{_proxy(row, flat, comp) or '—'} |  |")
    out.append("")
    for i, (row, (flat, comp)) in enumerate(zip(rows, results, strict=True), 1):
        out += [f"## {i}. {row.name}", "", f"*{row.question}*", ""]
        for label, a in (("flat", flat), ("composed", comp)):
            out.append(f"**{label}** `{a.sentence}` ({a.seconds:.2f} s)")
            out.append("")
            if a.error:
                out += [f"- refused: {a.error}", ""]
                continue
            if not a.hits:
                out += ["- (no hits)"]
            for ref, title, score, detail in a.hits[:k]:
                s = f" {score:.3f}" if score is not None else ""
                d = (" {" + ", ".join(f"{kk}: {vv}" for kk, vv in detail.items() if kk != "score")
                     + "}") if detail else ""
                t = f" — {title[:70]}" if title and title != ref else ""
                out.append(f"-{s} `{ref[:90]}`{t}{d}")
            if a.hyp:
                assumed = ", ".join(f"`{r[:60]}`" for r, _ in a.hyp[:k])
                out.append(f"- under the assumption: {assumed}")
            out.append("")
        if comp.plan:
            out += ["<details><summary>the plan</summary>", "", "```", comp.plan, "```",
                    "", "notes: " + " | ".join(n[:140] for n in comp.notes[:4]), "",
                    "</details>", ""]
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--out", default="")
    a = ap.parse_args(argv)
    from core.sealing import seal

    seal()
    from core.query import AMBASSADOR_OVERLAY, QueryEngine

    engine = QueryEngine()
    started = datetime.now(UTC).replace(tzinfo=None).isoformat(timespec="seconds")
    t0 = time.perf_counter()
    rows = rows_for(engine, a.k)
    results = [(_ask(engine, AMBASSADOR_OVERLAY, r.flat, a.k),
                _ask(engine, AMBASSADOR_OVERLAY, r.composed, a.k)) for r in rows]
    text = render(rows, results, k=a.k, started=started, seconds=time.perf_counter() - t0)
    default = ROOT / "docs" / "experiments" / f"query-battery-{started[:10]}.md"
    out = Path(a.out) if a.out else default
    out.write_text(text, encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT) if out.is_relative_to(ROOT) else out}")
    for i, (row, (flat, comp)) in enumerate(zip(rows, results, strict=True), 1):
        fe = f" ({flat.error})" if flat.error else ""
        ce = f" ({comp.error})" if comp.error else ""
        print(f"{i}. {row.name}: flat {len(flat.hits)} hits{fe} · composed {len(comp.hits)} "
              f"hits{ce} · {_proxy(row, flat, comp) or '—'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
