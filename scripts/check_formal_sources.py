#!/usr/bin/env python3
"""Nothing in the library or the statements runs while they build (the L1 gate, `formal/check.sh`).

`check.sh` builds `Palace` and `Spec` before it replays and judges them, and a command that runs
code at elaboration time (`run_cmd`, `#eval`, an `initialize`, a macro or elaborator of the file's
own, `IO`) would run then, as the user who owns the toolchain, before any checker looks: it could
rewrite a checker or the oleans the comparator reuses. This scan runs first, on the sources with
their comments and strings stripped, and refuses:

* the commands and declaration forms that run or define code at elaboration time, and the escapes
  around the kernel (`unsafe`, `implemented_by`, `extern`, `opaque`);
* any `set_option` but the elaboration budgets the library uses;
* in `lakefile.toml`, any `leanOptions` key beyond the ones it sets now (a `warn.sorry = false`
  would silence the `sorry` warning `--wfail` relies on), and a linter exception file.

The attacks in `PalaceTest/` run code by design (`#eval survives`) and are not scanned.

    python3 scripts/check_formal_sources.py [formal-root]
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

FORBIDDEN = re.compile(
    r"(?<![\w.'])(run_cmd|run_elab|run_meta|#eval|#exit|#guard_msgs|initialize|builtin_initialize|"
    r"elab|elab_rules|macro|macro_rules|syntax|declare_syntax_cat|meta|unsafe|partial|"
    r"implemented_by|extern|opaque|IO|import\s+Lean\.Elab)(?![\w'])")
SET_OPTION = re.compile(r"set_option\s+([\w.]+)")
ALLOWED_OPTIONS = frozenset({"synthInstance.maxSize", "maxHeartbeats", "maxRecDepth"})
LAKE_OPTIONS = frozenset({"pp.unicode.fun", "autoImplicit", "relaxedAutoImplicit",
                          "weak.linter.mathlibStandardSet", "weak.linter.style.header",
                          "maxSynthPendingDepth"})


def strip(src: str) -> str:
    """The source with `--` comments, nested `/- … -/` blocks and string literals blanked, line
    structure kept so reported lines match the file."""
    out: list[str] = []
    i, depth, n = 0, 0, len(src)
    while i < n:
        if depth == 0 and src.startswith("--", i):
            j = src.find("\n", i)
            i = n if j < 0 else j
        elif src.startswith("/-", i):
            depth += 1
            i += 2
        elif depth and src.startswith("-/", i):
            depth -= 1
            i += 2
        elif depth:
            out.append("\n" if src[i] == "\n" else " ")
            i += 1
        elif src[i] == '"':
            j = i + 1
            while j < n and src[j] != '"':
                j += 2 if src[j] == "\\" else 1
            out.append(" " * (j - i + 1))
            i = j + 1
        else:
            out.append(src[i])
            i += 1
    return "".join(out)


def scan(root: Path) -> list[str]:
    problems: list[str] = []
    files = [root / "Palace.lean", root / "Spec.lean",
             *sorted((root / "Palace").rglob("*.lean")), *sorted((root / "Spec").rglob("*.lean"))]
    for f in files:
        if not f.exists():
            continue
        code = strip(f.read_text(encoding="utf-8"))
        for lineno, line in enumerate(code.splitlines(), 1):
            for m in FORBIDDEN.finditer(line):
                problems.append(f"{f.relative_to(root)}:{lineno}: `{m.group(1)}`")
            for m in SET_OPTION.finditer(line):
                if m.group(1) not in ALLOWED_OPTIONS:
                    problems.append(f"{f.relative_to(root)}:{lineno}: set_option {m.group(1)}")
    lakefile = (root / "lakefile.toml").read_text(encoding="utf-8")
    section = re.search(r"^\[leanOptions\]\n(.*?)(?=^\[|\Z)", lakefile, re.M | re.S)
    keys = re.findall(r"^\s*([\w.]+)\s*=", section.group(1), re.M) if section else []
    problems += [f"lakefile.toml: leanOptions.{k}" for k in keys if k not in LAKE_OPTIONS]
    for nolints in (root / "scripts" / "nolints.json", root / "nolints.json"):
        if nolints.exists():
            problems.append(f"{nolints.relative_to(root)}: a linter exception file")
    return problems


def main(argv: list[str]) -> int:
    root = Path(argv[1]) if len(argv) > 1 else Path(__file__).resolve().parent.parent / "formal"
    problems = scan(root)
    for p in problems:
        print(p, file=sys.stderr)
    if problems:
        print(f"build-time code or a weakened check in the library: {len(problems)} line(s) above",
              file=sys.stderr)
        return 1
    print("sources: nothing in Palace or Spec runs while it builds; the build options are the "
          "reviewed ones")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
