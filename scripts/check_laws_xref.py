#!/usr/bin/env python3
"""The ledger ⇄ formal cross-reference: the mechanical half of MFF-4 (dn-mathematical-foundations
§2.4). Read from the sources alone; no Lean toolchain is needed.

Three directions:

  1. **Ledger → formal.** Every declaration a row of `docs/LAWS.md` cites in its formal column
     (`File.lean::name`) is declared in `formal/Palace/File.lean` or in its model,
     `formal/Palace/File/Defs.lean`, and the bold marker at the head of its docstring
     (`/-- **LAP-1** …`) names that row's law. A name may carry its namespaces
     (`Window.le_meet`); it must pick out one declaration.
  2. **Formal → ledger.** Every law id a bold docstring marker in `formal/Palace/` or
     `formal/Spec/` names has a row, and that row cites at least one declaration.
  3. **Ledger ⇄ spec.** Every cited theorem is stated in `formal/Spec/File.lean`, under the same
     name and marker, and named in `formal/comparator.json`; every statement there and every name
     the comparator judges is one a row cites.

A law id is one of the ledger's own families followed by a number, so a new family is picked up
when its rows land. MFF-4's other half, whether a statement says what its row says, is a reader's:
`lake comparator` ensures the library proves exactly the statements in `formal/Spec/`, so the
reader checks those and the definitions they use (`formal/Palace/*/Defs.lean`) against the rows,
and nothing else can change what is proved.

Run: `python3 scripts/check_laws_xref.py` (stdlib only; `formal/check.sh` runs it).
"""

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LEDGER = REPO_ROOT / "docs" / "LAWS.md"
FORMAL = REPO_ROOT / "formal" / "Palace"
SPEC = REPO_ROOT / "formal" / "Spec"
COMPARATOR = REPO_ROOT / "formal" / "comparator.json"

ROW = re.compile(r"^\|\s*([A-Z]{2,4}-\d+)\s*\|")
CELL_SPLIT = re.compile(r"(?<!\\)\|")
REF = re.compile(r"`([A-Za-z0-9]+\.lean)::([^`\s]+)`")
MARKER = re.compile(r"^\s*/--\s*\*\*([^*]+)\*\*")
DECL = re.compile(
    r"^\s*(?:@\[[^\]]*\]\s*)?(?:(?:private|protected|public|meta|noncomputable|partial|unsafe)\s+)*"
    r"(theorem|lemma|def|abbrev|instance|structure|inductive|class|example)\b\s*([^\s:({\[]*)"
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


def declarations(path: Path, theorems: set[str] | None = None) -> dict[str, list[str]]:
    """Each declaration in a Lean file, by its name under the namespaces open where it is
    declared, with the bold marker heading its docstring ("" if none). The names of theorems are
    added to `theorems` when it is given.

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
            if d.group(2):
                name = ".".join([s for s in scopes if s] + [d.group(2)])
                found[name].append(marker)
                if theorems is not None and d.group(1) in ("theorem", "lemma"):
                    theorems.add(name)
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
    theorems: set[str] = set()
    lean: dict[str, dict[str, list[str]]] = {}
    for path in sorted(FORMAL.glob("*.lean")):
        decls = declarations(path, theorems)
        model = FORMAL / path.stem / "Defs.lean"
        if model.exists():
            for name, markers in declarations(model, theorems).items():
                decls[name].extend(markers)
        lean[path.name] = decls
    stated: set[str] = set()
    spec = {path.name: declarations(path, stated) for path in sorted(SPEC.glob("*.lean"))}
    judged = set(json.loads(COMPARATOR.read_text())["theorem_names"])

    cited = 0
    cited_theorems: set[str] = set()
    for law, refs in rows.items():
        for file, name in refs:
            cited += 1
            if file not in lean:
                problems.append(f"{law}: cites {file}, which is not in formal/Palace/")
                continue
            found = resolve(lean[file], name)
            if not found:
                problems.append(f"{law}: cites {file}::{name}, which {file} does not declare")
                continue
            if len(found) > 1:
                problems.append(f"{law}: cites {file}::{name}, which is {len(found)} declarations")
                continue
            full = found[0]
            if not any(law in law_id.findall(mk) for mk in lean[file][full]):
                problems.append(f"{law}: cites {file}::{name}, whose docstring is not marked {law}")
            if full not in theorems:
                continue  # a definition: it belongs to the model, Palace/*/Defs.lean
            cited_theorems.add(full)
            stated_markers = spec.get(file, {}).get(full)
            if stated_markers is None:
                problems.append(f"{law}: {full} is not stated in formal/Spec/{file}")
            elif not any(law in law_id.findall(mk) for mk in stated_markers):
                problems.append(f"{law}: formal/Spec/{file}::{name} is not marked {law}")
            if full not in judged:
                problems.append(f"{law}: {full} is not in formal/comparator.json")

    for name in sorted(stated - cited_theorems):
        problems.append(f"formal/Spec/ states {name}, which no row cites")
    for name in sorted(judged - stated):
        problems.append(f"formal/comparator.json judges {name}, which formal/Spec/ does not state")
    for name in sorted(stated - judged):
        problems.append(f"formal/Spec/ states {name}, which formal/comparator.json does not judge")

    marked: set[str] = set()
    for where, files in (("Palace", lean), ("Spec", spec)):
        for file, decls in files.items():
            for name, markers in decls.items():
                for law in {law for mk in markers for law in law_id.findall(mk)}:
                    marked.add(law)
                    at = f"{where}/{file}::{name} is marked {law}"
                    if law not in rows:
                        problems.append(f"{at}, which has no ledger row")
                    elif not rows[law]:
                        problems.append(f"{at}, whose row cites nothing")

    for problem in problems:
        print(problem, file=sys.stderr)
    if problems:
        print(f"ledger ⇄ formal: {len(problems)} problem(s)", file=sys.stderr)
        return 1
    print(
        f"ledger ⇄ formal: {len(rows)} rows, {cited} cited declarations, "
        f"{len(marked)} laws marked in formal/, {len(cited_theorems)} statements in formal/Spec/ "
        "judged by the comparator, all consistent"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
