"""The `type-gate` CI job's three mechanical scans (B-2, `type-system-as-core-audit.md`).

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

§2.5 draws a THIRD mechanical line, the boundary-wrapper rule: a dependency with no
`py.typed` gets one thin typed shim, and that shim is the ONE module permitted to
import it raw, so `Any` is quarantined at one file per dependency instead of smeared
through the checked region. Until bp-106 that rule had **zero enforcement** — nothing
in this module, `ops/import_lint.py`, `scripts/check_imports.py`, the hooks, CI or
`[tool.ruff]` mentioned `typedshims` at all, so it was a docstring sentence. bp-105
then imported raw `psutil` in `ops/lifecycle/launcher.py` and it was authored,
reviewed, gated and merged with nothing objecting (**finding-0198**). `raw_shim_imports`
is the ratchet that makes the rule decidable from the AST, which is the same
"promote a convention to a static property" move the other two scans make.

Three scans, each importable and CLI-runnable:

  * `membership()` — walks every top-level package's `.py` files; a package that
    imports `core` anywhere but is absent from `[tool.mypy].files` is a violation.
  * `bare_ignores()` — regexes every checked-region `.py` file for a `# type: ignore`
    with no bracketed error code, which is a T3 discipline violation (§2.3: "every
    ignore carries an error code and a warrant comment").
  * `raw_shim_imports()` — walks the whole repo; a raw import of a shimmed dependency
    from anywhere but its own shim, without an inline `# typedshim-exempt: <reason>`,
    is a violation (§2.5 boundary wrappers; bp-106 Item 4, warrant finding-0198).

All three scans are read-only (no writes, no network, no subprocess) — they only read
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


@dataclass(frozen=True)
class RawShimImportViolation:
    path: str        # repo-relative file path
    lineno: int
    dependency: str  # the shimmed package imported raw (e.g. "psutil")
    shim: str        # the ONE module permitted to import it

    def __str__(self) -> str:
        return (
            f"{self.path}:{self.lineno}: raw `{self.dependency}` import outside {self.shim} "
            f"— route through the shim, or warrant it inline with `# {_WAIVER} <reason>`"
        )


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


# ═══ scan 3 — the §2.5 boundary-wrapper rule (bp-106 Item 4, warrant finding-0198) ═══════════
#
# Dependency -> the ONE module permitted to import it raw (§2.5 boundary wrappers).
# `duckdb` is deliberately ABSENT although §2.5 lists it as a candidate: it resolves TYPED, so it
# needs no shim (bp-106 §3 Q2 — it is in neither the shim list nor the `ignore_missing_imports`
# override at `pyproject.toml:155-157`, and the Tier-2 floor is 0 errors, which is impossible if an
# unshimmed untyped `duckdb` were imported by `core/stores/telemetry.py`). §2.5's list is the
# CANDIDATE list; V2 evidently cleared duckdb. Adding a shim for it would be cargo-culting the
# candidate list over its own finding.
_SHIMMED: dict[str, str] = {
    "psutil":    "core/typedshims/psutil.py",
    "lancedb":   "core/typedshims/lancedb.py",
    "sknetwork": "core/typedshims/sknetwork.py",
}

# The waiver deliberately mirrors the bare-ignore scan's shape: that rule is "every `# type:
# ignore` carries an error code", this one is "every raw shimmed import outside its shim carries a
# REASON". Inline at the import site, never a central path list — a path list outlives the reason
# and nobody rereads it, and it moves the justification away from the code (bp-106 §11).
_WAIVER = "typedshim-exempt:"

# `\S` after the colon: the token alone is not a waiver. A bare `# typedshim-exempt` carrying no
# reason is a violation, on the same principle the sibling scan applies to an unqualified ignore
# directive — the whole point is that an exemption has to SAY something.
#
# (Written without quoting that directive verbatim: this is a real COMMENT token, so quoting it
# here would make this module fail its own `bare_ignores` scan. Caught live while building this
# scan — the docstring hazard `_bare_ignore_comments` documents, one token type over.)
_WAIVER_RE = re.compile(re.escape(_WAIVER) + r"\s*\S")


def _repo_py_files(repo_root: Path) -> list[Path]:
    """Every `.py` file in the repo, skipping `_EXCLUDED_DIRS` at ANY depth.

    Whole-repo and not checked-region-scoped: `tests/` is in scope on purpose. The one legitimate
    test violation is waived explicitly (`test_code_corpus.py`, bp-106 §3 Q4), which is more honest
    than a blanket `tests/` exemption that would silently hide future real ones — and a blanket
    exemption is precisely how this rule decayed into a docstring in the first place (§11)."""
    return [
        p for p in sorted(repo_root.rglob("*.py"))
        if not (_EXCLUDED_DIRS & set(p.relative_to(repo_root).parts))
    ]


def _waived_lines(path: Path) -> set[int]:
    """Line numbers carrying a warranted `# typedshim-exempt: <reason>` COMMENT.

    `tokenize`, not raw text, for the same reason `_bare_ignore_comments` uses it: a `#` inside a
    string literal is not a comment, and a module documenting the protocol (this one) would
    otherwise self-match."""
    out: set[int] = set()
    try:
        with path.open("rb") as f:
            for tok in tokenize.tokenize(f.readline):
                if tok.type == tokenize.COMMENT and _WAIVER_RE.search(tok.string):
                    out.add(tok.start[0])
    except (tokenize.TokenError, SyntaxError, UnicodeDecodeError, IndentationError):
        return set()
    return out


def raw_shim_imports(repo_root: Path | None = None) -> list[RawShimImportViolation]:
    """§2.5 boundary-wrapper invariant: a shimmed dependency is imported raw ONLY by its own shim.

    Reuses `_imported_roots`, which walks the whole AST — so a FUNCTION-LOCAL `import psutil` is
    caught. That is not incidental: bp-105's violation *was* function-local (inside
    `_process_identity`), so a walker that inspected only module level would reproduce the exact
    hole this scan exists to close (bp-106 §7 Item 4 invariant).

    A violation is waived by an inline `# {_WAIVER} <reason>` on the import line, and only with a
    reason. Read-only, like its two siblings."""
    repo_root = repo_root or Path(__file__).resolve().parent.parent
    violations: list[RawShimImportViolation] = []
    for path in _repo_py_files(repo_root):
        rel = path.relative_to(repo_root).as_posix()
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (SyntaxError, UnicodeDecodeError):
            continue
        roots = [(ln, r) for ln, r in _imported_roots(tree) if r in _SHIMMED]
        if not roots:
            continue
        waived = _waived_lines(path)
        for lineno, dependency in roots:
            if rel == _SHIMMED[dependency] or lineno in waived:
                continue
            violations.append(RawShimImportViolation(
                path=rel, lineno=lineno, dependency=dependency, shim=_SHIMMED[dependency]))
    return violations


# ⚑ PARKED, and the only thing standing between detection and enforcement. bp-106 §10 says: *"the
# scan finds violations beyond the two in §3 Q3 ⇒ STOP, enumerate them, and file before waiving
# anything. A ratchet whose first act is to grant itself waivers is not a ratchet."* It found a
# third: `tests/unit/test_restart_trustworthy.py:21`, added the same day by `e49a715` (bp-121) —
# AFTER bp-106 was authored, so §3 Q3's census could not have known. It is legitimate (it patches
# `psutil.Process` and names `psutil.NoSuchProcess` to pin process shapes the host cannot have;
# the shim cannot hand those over without becoming the laundering proxy its own test forbids) and
# it needs exactly one waiver comment — but that file is deliberately OUTSIDE bp-106's
# `write_scope` (§5) and Item 2's acceptance requires it byte-untouched, so this plan may neither
# waive it nor edit it. Self-waiving via a hardcoded exception is what §10 forbids; reddening the
# authoritative gate is worse. So the scan REPORTS and does not yet vote on the exit code.
#
# Detection is NOT parked, and enforcement is not on the honour system: the scan is fully
# unit-tested on planted fixtures (`tests/unit/test_type_gate.py`), including a reproduction of
# bp-105's exact import line, and a live-tree test there asserts the repo contains that ONE known
# violation and nothing else — so a new bp-105-shaped import goes red in CI's `ratchet` job today.
#
# RE-ENTRY (one line): once `tests/unit/test_restart_trustworthy.py:21` carries
# `# typedshim-exempt: <reason>`, flip this to True and delete the live-tree test's parked branch.
# Owed to `/triage` — see `docs/findings/finding-0223.md`.
_RAW_SHIM_SCAN_IS_FATAL = False


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    membership_violations = membership(repo_root)
    ignore_violations = bare_ignores(repo_root)
    raw_import_violations = raw_shim_imports(repo_root)

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

    if raw_import_violations:
        if _RAW_SHIM_SCAN_IS_FATAL:
            ok = False
        print("Raw shimmed-dependency imports (type-gate) "
              f"{'VIOLATIONS' if _RAW_SHIM_SCAN_IS_FATAL else 'REPORTED (parked, non-fatal)'} "
              "— §2.5 says one shim per dependency owns the raw import:")
        for rv in raw_import_violations:
            print(f"  {rv}")
        if not _RAW_SHIM_SCAN_IS_FATAL:
            print("  ^ non-fatal pending finding-0223 (bp-106 §10): the remaining violation needs a"
                  " one-line waiver in a file outside bp-106's write_scope. Detection is enforced"
                  " by tests/unit/test_type_gate.py, which reddens on any NEW violation.")
    else:
        print("Raw shimmed-dependency imports: OK — every shimmed package is imported raw only by "
              "its own shim (or waived inline with a reason)")

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
