#!/usr/bin/env python
"""readmap — emit a seal's read map as vim quickfix lines (bp-072 Item 2).

From session-29 on, every seal journal carries a READ MAP: the ~15% of the diff worth
reading, as `path:line: why` lines inside a fenced ```read-map block. This tool finds
the LAST such block in a plan's `journal.md` and emits its lines VERBATIM — the authoring
format IS the quickfix format, so nothing transforms and nothing can drift (the falsifier).
In vim:  `uv run scripts/readmap.py <plan-id> | ...`  ->  `:cfile` / `]q` to walk the map.

It NEVER parses legacy prose read maps. A journal with no ```read-map block exits 1 with
an honest message — guessing at prose would be a trust-surface violation (guide-not-gate:
the full diff stays one command away, not behind a cleverer filter).

    uv run scripts/readmap.py bp-073        # -> quickfix lines, or exit 1 if the seal is prose
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# A fenced ```read-map … ``` block. Non-greedy body; DOTALL so it spans lines. We take
# the LAST match — a journal accretes seals, and the final block is the current read map.
_BLOCK = re.compile(r"(?m)^```read-map[ \t]*\n(.*?)^```[ \t]*$", re.DOTALL)


def extract_block(journal_text: str) -> list[str] | None:
    """The lines of the LAST ```read-map block, verbatim (trailing blanks trimmed), or
    None when no such block exists. A None return is the honest 'legacy prose seal' signal
    — the caller exits 1; it does not fall back to parsing prose."""
    matches = _BLOCK.findall(journal_text)
    if not matches:
        return None
    body = matches[-1]
    lines = [ln for ln in body.splitlines()]
    # drop leading/trailing blank lines but keep interior spacing verbatim
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


# A quickfix line is `path:line: why`; the leading token up to the first ':' is the path.
_PATHLINE = re.compile(r"^([^:]+):(\d+):")


def _warn_missing_paths(lines: list[str], root: Path) -> None:
    """A listed path that no longer exists → WARNING to stderr; the line is STILL emitted
    (the map records where the concept lived at seal time; the reader decides)."""
    for ln in lines:
        m = _PATHLINE.match(ln.strip())
        if m and not (root / m.group(1)).exists():
            print(f"warning: {m.group(1)} no longer exists (line kept)", file=sys.stderr)


def main(argv: list[str]) -> int:
    if len(argv) != 1 or argv[0] in {"-h", "--help"}:
        print("usage: readmap.py <plan-id>", file=sys.stderr)
        return 2
    plan_id = argv[0]
    journal = ROOT / "docs" / "build-plans" / plan_id / "journal.md"
    if not journal.exists():
        print(f"no journal for {plan_id} ({journal.relative_to(ROOT)})", file=sys.stderr)
        return 1
    lines = extract_block(journal.read_text(encoding="utf-8"))
    if lines is None:
        print(
            f"{plan_id}: no structured read-map block (legacy prose seal?) — "
            "read the seal journal directly.",
            file=sys.stderr,
        )
        return 1
    _warn_missing_paths(lines, ROOT)
    for ln in lines:
        print(ln)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
