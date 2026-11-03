#!/usr/bin/env python3
"""The ledger ⇄ formal cross-reference: the mechanical half of MFF-4 (dn-mathematical-foundations
§2.4). Read from the sources alone; no Lean toolchain is needed.

Two directions:

  1. **Ledger → formal.** Every declaration a row of `docs/LAWS.md` cites in its formal column
     (`File.lean::name`) is declared in `formal/Palace/File.lean`, and the bold marker at the head
     of its docstring (`/-- **LAP-1** …`) names that row's law. A name may carry its namespaces
     (`Window.le_meet`); it must pick out one declaration in the file.
  2. **Formal → ledger.** Every law id a bold docstring marker in `formal/Palace/` names has a row,
     and that row cites at least one declaration.

A law id is one of the ledger's own families followed by a number, so a new family is picked up
when its rows land. What this cannot see is MFF-4's other half: a Lean statement and its row that
say different things. That stays with review.

Run: `python3 scripts/check_laws_xref.py` (stdlib only; `formal/check.sh` runs it).
"""

import re
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LEDGER = REPO_ROOT / "docs" / "LAWS.md"
FORMAL = REPO_ROOT / "formal" / "Palace"

ROW = re.compile(r"^\|\s*([A-Z]{2,4}-\d+)\s*\|")
CELL_SPLIT = re.compile(r"(?<!\\)\|")
REF = re.compile(r"`([A-Za-z0-9]+\.lean)::([^`\s]+)`")
MARKER = re.compile(r"^\s*/--\s*\*\*([^*]+)\*\*")
DECL = re.compile(
    r"^\s*(?:@\[[^\]]*\]\s*)?(?:(?:private|protected|public|meta|noncomputable|partial|unsafe)\s+)*"
    r"(?:theorem|lemma|def|abbrev|instance|structure|inductive|class|example)\b\s*([^\s:({\[]*)"
)
NAMESPACE = re.compile(r"^namespace\s+(\S+)")
SECTION = re.compile(r"^(?:@\[[^\]]*\]\s*)?(?:(?:public|private|noncomputable)\s+)*section\b")
END = re.compile(r"^end\b")


def strip_plain_comments(text: str) -> str:
    """Blank out non-doc block comments (`/- … -/`, nested), keeping docstrings and line breaks."""
    out: list[str] = []
    depth = 0
    i = 0
    while i < len(text):
        if text.startswith("/-", i) and (depth > 0 or text[i + 2 : i + 3] not in ("-", "!")):
            depth += 1
            out.append("  ")
            i += 2
        elif depth > 0 and text.startswith("-/", i):
            depth -= 1
            out.append("  ")
            i += 2
        elif depth > 0:
            out.append("\n" if text[i] == "\n" else " ")
            i += 1
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def declarations(path: Path) -> dict[str, list[str]]:
    """Each declaration in a Lean file, by its name under the namespaces open where it is
    declared, with the bold marker heading its docstring ("" if none).

    An anonymous instance or an `example` takes its docstring's marker with it, unrecorded."""
    found: dict[str, list[str]] = defaultdict(list)
    scopes: list[str] = []  # one entry per open namespace or section; "" for a section
    marker = ""
    in_doc = False
    for line in strip_plain_comments(path.read_text()).splitlines():
        if not in_doc and line.lstrip().startswith(("/--", "/-!")):
            m = MARKER.match(line)
            marker = m.group(1) if m else ""
            in_doc = True
        if in_doc:
            in_doc = "-/" not in line
            continue
        if n := NAMESPACE.match(line):
            scopes.append(n.group(1))
        elif SECTION.match(line):
            scopes.append("")
        elif END.match(line) and scopes:
            scopes.pop()
        elif d := DECL.match(line):
            if d.group(1):
                found[".".join([s for s in scopes if s] + [d.group(1)])].append(marker)
            marker = ""
    return found


def resolve(decls: dict[str, list[str]], name: str) -> list[str]:
    """The declarations a cited name picks out: those whose full name is it or ends in it."""
    return [full for full in decls if full == name or full.endswith("." + name)]


def ledger_rows() -> tuple[dict[str, list[tuple[str, str]]], list[str]]:
    """Each row's law id with the `(file, name)` refs of its formal column, and any defects."""
    rows: dict[str, list[tuple[str, str]]] = {}
    problems: list[str] = []
    for n, line in enumerate(LEDGER.read_text().splitlines(), 1):
        m = ROW.match(line)
        if not m:
            continue
        law = m.group(1)
        cells = [c.strip() for c in CELL_SPLIT.split(line.strip().strip("|"))]
        if len(cells) != 7:
            problems.append(f"LAWS.md:{n}: {law} has {len(cells)} columns, not 7")
            continue
        if law in rows:
            problems.append(f"LAWS.md:{n}: {law} has a second row")
        refs = REF.findall(cells[6])
        if not refs and cells[6] != "—":
            problems.append(f"LAWS.md:{n}: {law}'s formal column is neither `—` nor a ref")
        rows[law] = refs
    return rows, problems


def main() -> int:
    rows, problems = ledger_rows()
    families = sorted({law.split("-")[0] for law in rows})
    law_id = re.compile(r"\b(?:" + "|".join(families) + r")-\d+\b")
    lean = {path.name: declarations(path) for path in sorted(FORMAL.glob("*.lean"))}

    cited = 0
    for law, refs in rows.items():
        for file, name in refs:
            cited += 1
            if file not in lean:
                problems.append(f"{law}: cites {file}, which is not in formal/Palace/")
                continue
            found = resolve(lean[file], name)
            if not found:
                problems.append(f"{law}: cites {file}::{name}, which {file} does not declare")
            elif len(found) > 1:
                problems.append(f"{law}: cites {file}::{name}, which is {len(found)} declarations")
            elif not any(law in law_id.findall(mk) for mk in lean[file][found[0]]):
                problems.append(f"{law}: cites {file}::{name}, whose docstring is not marked {law}")

    marked: set[str] = set()
    for file, decls in lean.items():
        for name, markers in decls.items():
            for law in {law for mk in markers for law in law_id.findall(mk)}:
                marked.add(law)
                if law not in rows:
                    problems.append(f"{file}::{name} is marked {law}, which has no ledger row")
                elif not rows[law]:
                    problems.append(f"{file}::{name} is marked {law}, whose row cites nothing")

    for problem in problems:
        print(problem, file=sys.stderr)
    if problems:
        print(f"ledger ⇄ formal: {len(problems)} problem(s)", file=sys.stderr)
        return 1
    print(
        f"ledger ⇄ formal: {len(rows)} rows, {cited} cited declarations, "
        f"{len(marked)} laws marked in formal/, all consistent"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
