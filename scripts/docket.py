#!/usr/bin/env python
"""The docket — the owner's *awaiting-the-owner* view (bp-072, decision-routing v1).

A DERIVED view, recomputed from the artifact tree on every run: NO persisted state,
so it cannot drift (the falsifier). It surfaces exactly the three things that wait on
the owner's hand and NOTHING an agent can act on:

    proposed build plans   -> "bless proposed->ready"   (the owner-only readiness gate)
    draft design notes      -> "ratify (or leave working)"
    open owner-questions     -> "answer"                  (blocking flag carried)

EXCLUDED by design: `ready` plans and answered/swept oqs — those are agent-actionable,
not owner-awaiting. This is a guide, not a gate: it points; it never flips anything.

Front-matter parsing is REUSED from `.claude/hooks/_lib.py` (DRY, plan §2 audit) — this
script never re-derives a YAML parser and never imports `core` (repo-workflow tooling).

    uv run scripts/docket.py            # render the rows to stdout
    uv run scripts/docket.py --count    # print ONE integer (the ambient count)
    uv run scripts/docket.py --write    # render to .claude/state/docket.md (vim landing buffer)
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Reuse the artifact front-matter machinery — never re-derive it (plan §2 DRY audit).
sys.path.insert(0, str(ROOT / ".claude" / "hooks"))
from _lib import (  # type: ignore[import-not-found]  # noqa: E402
    _normalize_status,
    parse_front_matter,
)

# Sort classes (lower = higher on the docket). Blocking questions first — a blocked
# builder is the sharpest cost; then the readiness gate; then notes; then the rest.
_CLASS_BLOCKING_OQ = 0
_CLASS_PROPOSED_PLAN = 1
_CLASS_DRAFT_NOTE = 2
_CLASS_OPEN_OQ = 3


@dataclass(frozen=True)
class DocketRow:
    id: str
    kind: str  # "plan" | "note" | "oq"
    action: str
    sort_key: tuple[int, str]  # (class_rank, secondary) — secondary sorts oldest-first within class
    title: str
    path: str  # repo-relative


def _first_h1(text: str) -> str:
    for ln in text.splitlines():
        if ln.startswith("# "):
            return ln[2:].strip()
    return ""


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _status(fm: dict[str, object]) -> str | None:
    s = fm.get("status")
    if isinstance(s, str) and s:
        return _normalize_status(s)
    return None


def _scan_plans(root: Path) -> list[DocketRow]:
    rows = []
    for plan in sorted(root.glob("docs/build-plans/*/plan.md")):
        text = _read(plan)
        fm = parse_front_matter(text)
        if _status(fm) != "proposed":
            continue  # `ready` plans are agent-actionable — excluded by design
        pid = str(fm.get("id") or plan.parent.name)
        created = str(fm.get("created") or "")  # ISO date sorts lexicographically
        title = _first_h1(text) or str(fm.get("alias") or pid)
        rows.append(DocketRow(
            id=pid, kind="plan", action="bless proposed->ready",
            sort_key=(_CLASS_PROPOSED_PLAN, created),
            title=title, path=str(plan.relative_to(root)),
        ))
    return rows


def _scan_notes(root: Path) -> list[DocketRow]:
    rows = []
    for note in sorted(root.glob("docs/design-notes/*.md")):
        text = _read(note)
        fm = parse_front_matter(text)
        if _status(fm) != "draft":
            continue
        created = str(fm.get("created") or "")
        title = _first_h1(text) or note.stem
        rows.append(DocketRow(
            id=note.stem, kind="note", action="ratify (or leave working)",
            sort_key=(_CLASS_DRAFT_NOTE, created),
            title=title, path=str(note.relative_to(root)),
        ))
    return rows


# `## oq-NNNN — <title>` header, capturing id and the trailing title text.
_OQ_HEADER = re.compile(r"(?m)^##\s+(oq-\d+)\b[ \t]*[—-]*[ \t]*(.*)$")


def _scan_oqs(root: Path) -> list[DocketRow]:
    path = root / "docs" / "inbox" / "owner-questions.md"
    text = _read(path)
    if not text:
        return []
    rows = []
    matches = list(_OQ_HEADER.finditer(text))
    rel = str(path.relative_to(root))
    for i, m in enumerate(matches):
        oid, title = m.group(1), m.group(2).strip()
        body = text[m.end():(matches[i + 1].start() if i + 1 < len(matches) else len(text))]
        sm = re.search(r"(?m)^-\s*status:\s*(\S+)", body)
        status = _normalize_status(sm.group(1)) if sm else None
        if status != "open":
            continue  # answered / swept are not owner-awaiting
        bm = re.search(r"(?m)^-\s*blocking:\s*(\w+)", body)
        blocking = bm is not None and bm.group(1).strip().lower() == "true"
        cls = _CLASS_BLOCKING_OQ if blocking else _CLASS_OPEN_OQ
        rows.append(DocketRow(
            id=oid, kind="oq",
            action="answer (BLOCKING)" if blocking else "answer",
            sort_key=(cls, oid),  # id ascending — zero-padded, so lexicographic == numeric (Q3)
            title=title, path=rel,
        ))
    return rows


def scan_docket(root: Path) -> list[DocketRow]:
    """The whole derived view, sorted: blocking oqs -> proposed plans -> draft notes ->
    non-blocking oqs; oldest-first within class. Recomputed every call — never cached."""
    rows = _scan_plans(root) + _scan_notes(root) + _scan_oqs(root)
    return sorted(rows, key=lambda r: r.sort_key)


# Redundant H1 prefixes ("Design note — ", "Build Plan — ") are display noise once the
# item sits under a grouped section header — stripped at render time only (rows keep
# the raw title).
_TITLE_PREFIX = re.compile(r"^(?:Design note|Build Plan)\s*—\s*", re.IGNORECASE)


def _n(count: int, word: str) -> str:
    return f"{count} {word}{'' if count == 1 else 's'}"


def render(rows: list[DocketRow]) -> str:
    """Grouped by owner action (the section IS the action, so item lines stay short):
    blocking answers -> bless -> ratify -> answer, mirroring the class sort ranks."""
    if not rows:
        return "# Docket — nothing awaits the owner. Inbox zero.\n"
    blocking = [r for r in rows if r.kind == "oq" and "BLOCKING" in r.action]
    plans = [r for r in rows if r.kind == "plan"]
    notes = [r for r in rows if r.kind == "note"]
    oqs = [r for r in rows if r.kind == "oq" and "BLOCKING" not in r.action]

    out = [f"# Docket — {len(rows)} awaiting the owner"]

    def section(header: str, items: list[DocketRow]) -> None:
        if not items:
            return
        out.extend(["", header, ""])
        for r in items:
            out.append(f"- `{r.id}` — {_TITLE_PREFIX.sub('', r.title)}")
            out.append(f"    {r.path}")

    section(f"## ⚑ Blocking — {_n(len(blocking), 'answer')} needed NOW", blocking)
    section(f"## Bless — {_n(len(plans), 'plan')} proposed→ready  (`palace bless <id>`)", plans)
    section(f"## Ratify — {_n(len(notes), 'draft note')}  (or leave working)", notes)
    section(f"## Answer — {_n(len(oqs), 'open question')}", oqs)
    out.append("")
    out.append("_A derived view — recomputed from the artifact tree, never hand-maintained._")
    out.append("_Guide, not gate: it points; the owner acts (bless, ratify, answer)._")
    return "\n".join(out) + "\n"


def main(argv: list[str]) -> int:
    rows = scan_docket(ROOT)
    if "--count" in argv:
        print(len(rows))
        return 0
    if "--write" in argv:
        dest = ROOT / ".claude" / "state" / "docket.md"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(render(rows), encoding="utf-8")
        print(f"wrote {dest.relative_to(ROOT)} ({len(rows)} rows)")
        return 0
    sys.stdout.write(render(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
