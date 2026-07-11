"""ops/type_gate.py — the two type-gate scans (B-2, `type-system-as-core-audit.md`).

Each scan is proven on PLANTED fixtures (tmp trees), both a violating tree (the scan
must catch it) and a clean tree (the scan must pass it) — the plan's Item 8 acceptance
test, and the falsifier (a planted violation the scan misses) this file exists to rule
out for both scans.
"""

from __future__ import annotations

from pathlib import Path

from ops.type_gate import (
    BareIgnoreViolation,
    MembershipViolation,
    bare_ignores,
    membership,
)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def _write_pyproject(root: Path, files: list[str]) -> None:
    files_toml = ", ".join(f'"{f}"' for f in files)
    _write(root / "pyproject.toml", f"[tool.mypy]\nfiles = [{files_toml}]\n")


# --------------------------------------------------------------------------- membership


def test_membership_catches_a_core_importer_absent_from_tier2_config(tmp_path):
    """Falsifier (ii): a scratch top-level package imports `core` but is not listed
    in [tool.mypy].files — membership() must catch it."""
    _write_pyproject(tmp_path, ["core"])  # "scratch" package deliberately omitted
    _write(tmp_path / "core" / "__init__.py", "")
    _write(tmp_path / "scratch" / "__init__.py", "")
    _write(tmp_path / "scratch" / "user.py", "import core\n\ndef f():\n    return core\n")

    violations = membership(tmp_path)

    assert violations == [
        MembershipViolation(package="scratch", sample_path="scratch/user.py", lineno=1)
    ]


def test_membership_catches_via_from_import_too(tmp_path):
    """`from core.sub import thing` must be caught the same as `import core`."""
    _write_pyproject(tmp_path, ["core"])
    _write(tmp_path / "core" / "sub.py", "THING = 1\n")
    _write(tmp_path / "scratch" / "user.py", "from core.sub import THING\n")

    violations = membership(tmp_path)

    assert len(violations) == 1
    assert violations[0].package == "scratch"


def test_membership_passes_a_clean_tree_where_importer_is_in_config(tmp_path):
    """Same shape as the violating fixture, except `scratch` IS listed in
    [tool.mypy].files — no violation."""
    _write_pyproject(tmp_path, ["core", "scratch"])
    _write(tmp_path / "core" / "__init__.py", "")
    _write(tmp_path / "scratch" / "__init__.py", "")
    _write(tmp_path / "scratch" / "user.py", "import core\n")

    assert membership(tmp_path) == []


def test_membership_passes_a_clean_tree_with_no_core_importers_at_all(tmp_path):
    """A package that imports nothing from core needs no Tier-2 entry — this is the
    Tier-3 "recorded default, not deferred debt" case (edge/cloud today)."""
    _write_pyproject(tmp_path, ["core"])
    _write(tmp_path / "core" / "__init__.py", "")
    _write(tmp_path / "edge" / "__init__.py", "")
    _write(tmp_path / "edge" / "gateway.py", "import socket\n\ndef f():\n    return socket\n")

    assert membership(tmp_path) == []


def test_membership_ignores_relative_imports(tmp_path):
    """A relative import (`from . import x`) stays inside the importer's own
    package and can never name `core` as a sibling top-level package — not a
    membership signal (mirrors ops/import_lint.py's treatment of relative imports)."""
    _write_pyproject(tmp_path, ["core"])
    _write(tmp_path / "core" / "__init__.py", "")
    _write(tmp_path / "scratch" / "__init__.py", "")
    _write(tmp_path / "scratch" / "a.py", "X = 1\n")
    _write(tmp_path / "scratch" / "b.py", "from . import a\n")

    assert membership(tmp_path) == []


# -------------------------------------------------------------------------- bare_ignores


def test_bare_ignores_catches_an_unqualified_ignore_comment(tmp_path):
    """Falsifier (iii): a bare `# type: ignore` with no bracketed error code must
    be caught."""
    _write_pyproject(tmp_path, ["scratch"])
    _write(
        tmp_path / "scratch" / "leaky.py",
        "x: int = 'oops'  # type: ignore\n",
    )

    violations = bare_ignores(tmp_path)

    assert len(violations) == 1
    assert violations[0] == BareIgnoreViolation(
        path="scratch/leaky.py", lineno=1, text="# type: ignore"
    )


def test_bare_ignores_passes_a_clean_tree_with_qualified_ignores_only(tmp_path):
    """A qualified `# type: ignore[code]` is the disciplined form (§2.3) and must
    NOT be flagged, including with a trailing warrant comment."""
    _write_pyproject(tmp_path, ["scratch"])
    _write(
        tmp_path / "scratch" / "clean.py",
        "x: int = 1  # type: ignore[assignment]  # warrant: reasoned exemption\n",
    )

    assert bare_ignores(tmp_path) == []


def test_bare_ignores_scoped_to_checked_region_only(tmp_path):
    """A bare ignore OUTSIDE [tool.mypy].files (Tier 3) is not in the checked
    region and must not be flagged — §2.3's discipline applies to the checked
    region, not the whole repo."""
    _write_pyproject(tmp_path, ["scratch"])
    _write(tmp_path / "scratch" / "clean.py", "x = 1\n")
    _write(tmp_path / "unchecked" / "wild.py", "x = 1  # type: ignore\n")

    assert bare_ignores(tmp_path) == []


def test_bare_ignores_does_not_flag_prose_mentioning_the_phrase_in_a_docstring(tmp_path):
    """Regression: a module documenting its own bare-ignore detection necessarily
    discusses the phrase `# type: ignore` in a DOCSTRING (a STRING token, not a
    COMMENT token) — this must never be mistaken for a real directive. Caught live
    while building ops/type_gate.py itself (see bp-008 journal, Item 8)."""
    _write_pyproject(tmp_path, ["scratch"])
    _write(
        tmp_path / "scratch" / "documents_itself.py",
        '"""This module explains what a bare `# type: ignore` looks like."""\n'
        "x = 1\n",
    )

    assert bare_ignores(tmp_path) == []


def test_bare_ignores_does_not_flag_prose_in_a_real_comment_either(tmp_path):
    """A genuine `#`-comment that merely discusses the directive by name (not as
    a trailing directive on a statement) must not be flagged either — only a
    comment token where the pattern matches (bare `type: ignore`, no bracket) is
    a real directive-shaped violation."""
    _write_pyproject(tmp_path, ["scratch"])
    _write(
        tmp_path / "scratch" / "discusses.py",
        "# Discipline: every ignore comment needs a bracketed error code.\n"
        "x = 1  # type: ignore[assignment]\n",
    )

    assert bare_ignores(tmp_path) == []


def test_bare_ignores_reports_line_numbers_for_multiple_violations(tmp_path):
    _write_pyproject(tmp_path, ["scratch"])
    _write(
        tmp_path / "scratch" / "two.py",
        "a = 1  # type: ignore\n"
        "b = 2  # fine, no ignore here\n"
        "c = 3  # type:ignore\n",  # no space — still bare
    )

    violations = bare_ignores(tmp_path)

    assert [v.lineno for v in violations] == [1, 3]
