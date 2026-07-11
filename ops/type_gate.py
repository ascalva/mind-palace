"""The `type-gate` CI job's two mechanical scans (B-2, `type-system-as-core-audit.md`).

`type-system-as-core-audit.md` §2.5 draws the two-tier checked region and states the
membership rule as a mechanical invariant, not a judgment call: **a top-level package
that imports anything from `core/` must appear in `[tool.mypy].files`** (Tier 2), so
that mypy actually analyzes every caller of core (the scoping rule: "a caller must
respect the callee's types" is only enforceable if every caller is itself checked).
§2.3 T3 disciplines the OTHER hole gradual typing leaves open: a bare `# type:
ignore` (no error code) silences the checker without naming what it silenced, making
T3 friction ungrep-able and unauditable. Both are decidable from the AST / source
text without running the program — the same "promote a runtime property to a static
one, provable by reading the AST" move `ops/import_lint.py` already performs for I2
(that module's `_imported_names`/`scan_file`/`Violation` shape is the direct pattern
this module generalizes to a second invariant).

Two scans, each importable and CLI-runnable:

  * `membership()` — walks every top-level package's `.py` files; a package that
    imports `core` anywhere but is absent from `[tool.mypy].files` is a violation.
  * `bare_ignores()` — regexes every checked-region `.py` file for a `# type: ignore`
    with no bracketed error code, which is a T3 discipline violation (§2.3: "every
    ignore carries an error code and a warrant comment").

Both scans are read-only (no writes, no network, no subprocess) — they only read
source text and (for membership) `pyproject.toml`.

Run: `python -m ops.type_gate` (also `uv run python -m ops.type_gate`). Wired into
the `type-gate` CI job (`.gitlab-ci.yml`), alongside `mypy` itself.
"""

from __future__ import annotations

import ast
import re
import tokenize
import tomllib
from dataclasses import dataclass
from pathlib import Path

# Directories that are never themselves a "top-level package" candidate for the
# membership scan: VCS/tooling/build noise, docs, and generated/site output. `core`
# is Tier 1 (always required to be in `files`) but is included in the walk like any
# other package — it trivially satisfies membership (it is always present).
_EXCLUDED_DIRS: frozenset[str] = frozenset({
    ".git", ".jj", ".venv", ".uv-cache", "__pycache__", "node_modules",
    "docs", "site", "public", "bin", ".claude", ".ruff_cache", ".mypy_cache",
    ".pytest_cache",
})


@dataclass(frozen=True)
class MembershipViolation:
    package: str      # top-level package name (e.g. "edge")
    sample_path: str  # one repo-relative file in that package that imports core
    lineno: int

    def __str__(self) -> str:
        return (
            f"{self.package}: imports `core` (e.g. {self.sample_path}:{self.lineno}) "
            f"but is absent from [tool.mypy].files"
        )


@dataclass(frozen=True)
class BareIgnoreViolation:
    path: str  # repo-relative file path
    lineno: int
    text: str  # the offending comment token's text, stripped

    def __str__(self) -> str:
        return f"{self.path}:{self.lineno}: bare `# type: ignore` (no error code) — {self.text}"


def _top_level_packages(repo_root: Path) -> list[str]:
    """Every directory directly under repo_root that contains at least one `.py`
    file and is not an excluded/tooling directory — i.e. every Python package
    candidate for Tier-2 membership."""
    packages: list[str] = []
    for entry in sorted(repo_root.iterdir()):
        if not entry.is_dir() or entry.name in _EXCLUDED_DIRS or entry.name.startswith("."):
            continue
        if any(entry.rglob("*.py")):
            packages.append(entry.name)
    return packages


def _imported_roots(tree: ast.AST) -> list[tuple[int, str]]:
    """Every top-level imported package name in a module, with its line number.
    Relative imports (`from . import x`) stay inside the file's own package and
    can never name a sibling top-level package, so they are excluded — mirrors
    `ops/import_lint.py`'s `_imported_names`."""
    out: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            out.extend((node.lineno, alias.name.split(".", 1)[0]) for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            out.append((node.lineno, node.module.split(".", 1)[0]))
    return out


def _mypy_files(repo_root: Path) -> list[str]:
    """The Tier-2 config: `[tool.mypy].files` from pyproject.toml."""
    pyproject = repo_root / "pyproject.toml"
    with pyproject.open("rb") as f:
        data = tomllib.load(f)
    files = data.get("tool", {}).get("mypy", {}).get("files", [])
    return [str(f) for f in files]


def membership(repo_root: Path | None = None) -> list[MembershipViolation]:
    """Tier-2 membership invariant: every top-level package that imports anything
    from `core` must be listed in `[tool.mypy].files`. Returns one violation per
    offending package (first import site found), not one per import site."""
    repo_root = repo_root or Path(__file__).resolve().parent.parent
    mypy_files = set(_mypy_files(repo_root))
    violations: list[MembershipViolation] = []
    for package in _top_level_packages(repo_root):
        if package in mypy_files:
            continue
        found: tuple[int, str] | None = None
        for path in sorted((repo_root / package).rglob("*.py")):
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            except SyntaxError:
                continue
            for lineno, root in _imported_roots(tree):
                if root == "core":
                    found = (lineno, path.relative_to(repo_root).as_posix())
                    break
            if found:
                break
        if found:
            lineno, rel = found
            violations.append(MembershipViolation(package=package, sample_path=rel, lineno=lineno))
    return violations


# The plan's pinned core pattern (§6/Item 8, verbatim): `type:\s*ignore(?!\[)` — a
# bare ignore directive has no `[` immediately after the word "ignore" (a qualified
# one always does: a hash-comment reading `type ignore, bracket, arg dash type,
# bracket`). Applied ONLY to genuine `tokenize.COMMENT` tokens (see
# `_bare_ignore_comments` below), not to raw source text: prose that merely
# discusses the directive by name (as this module's own docstrings necessarily
# do) would otherwise self-match a raw substring scan (confirmed live while
# building this scan — see journal). `tokenize` is the principled fix — it is the
# same lexer mypy/CPython use, so "is this a comment vs. a string literal" is
# decided the same way the language itself decides it, not by a weaker heuristic
# (e.g. "first hash character on the line", which breaks on a hash appearing
# inside a string literal).
_BARE_IGNORE_RE = re.compile(r"type:\s*ignore(?!\[)")


def _checked_region_files(repo_root: Path) -> list[Path]:
    """Every `.py` file under a `[tool.mypy].files` top-level entry — the region
    the bare-ignore discipline applies to (per §2.3, scoped to the checked region;
    Tier-3 code has no annotations to be honest or dishonest about)."""
    out: list[Path] = []
    for entry in _mypy_files(repo_root):
        base = repo_root / entry
        if base.is_file() and base.suffix == ".py":
            out.append(base)
        elif base.is_dir():
            out.extend(sorted(base.rglob("*.py")))
    return out


def _bare_ignore_comments(path: Path) -> list[tuple[int, str]]:
    """Every genuine comment token in `path` matching the bare-ignore pattern, as
    (lineno, comment text) pairs. Uses `tokenize` (not raw-text regex) so a `#`
    inside a string/docstring literal is never mistaken for a real comment."""
    out: list[tuple[int, str]] = []
    try:
        with path.open("rb") as f:
            tokens = tokenize.tokenize(f.readline)
            for tok in tokens:
                if tok.type == tokenize.COMMENT and _BARE_IGNORE_RE.search(tok.string):
                    out.append((tok.start[0], tok.string))
    except (tokenize.TokenError, SyntaxError, UnicodeDecodeError, IndentationError):
        return []
    return out


def bare_ignores(repo_root: Path | None = None) -> list[BareIgnoreViolation]:
    """T3 discipline scan: a `# type: ignore` with no bracketed error code, over
    every file in the checked region (`[tool.mypy].files`). Matches only real
    comment tokens (via `tokenize`), so prose in docstrings/strings that merely
    mentions the phrase is never flagged."""
    repo_root = repo_root or Path(__file__).resolve().parent.parent
    violations: list[BareIgnoreViolation] = []
    for path in _checked_region_files(repo_root):
        for lineno, text in _bare_ignore_comments(path):
            violations.append(
                BareIgnoreViolation(
                    path=path.relative_to(repo_root).as_posix(),
                    lineno=lineno,
                    text=text.strip(),
                )
            )
    return violations


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    membership_violations = membership(repo_root)
    ignore_violations = bare_ignores(repo_root)

    ok = True
    if membership_violations:
        ok = False
        print("Tier-2 membership (type-gate) VIOLATIONS — imports `core` but not in "
              "[tool.mypy].files:")
        for mv in membership_violations:
            print(f"  {mv}")
    else:
        print("Tier-2 membership: OK — every core-importing top-level package is in "
              "[tool.mypy].files")

    if ignore_violations:
        ok = False
        print("Bare `# type: ignore` (type-gate) VIOLATIONS — no error code:")
        for iv in ignore_violations:
            print(f"  {iv}")
    else:
        print("Bare-ignore scan: OK — every `# type: ignore` in the checked region "
              "carries an error code")

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
