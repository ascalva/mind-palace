"""ops/type_gate.py — the three type-gate scans (B-2, `type-system-as-core-audit.md`).

Each scan is proven on PLANTED fixtures (tmp trees), both a violating tree (the scan
must catch it) and a clean tree (the scan must pass it) — the plan's Item 8 acceptance
test, and the falsifier (a planted violation the scan misses) this file exists to rule
out for every scan.

bp-106 Item 4 adds the third scan, `raw_shim_imports` — the §2.5 boundary-wrapper rule
(one shim per untyped dependency owns the raw import). Its named falsifier is stronger
than "a planted violation is missed": **the scan must catch the exact import line that
caused finding-0198**, because a ratchet that cannot reproduce its own warrant is
decoration. That reproduction is `test_the_scan_catches_bp105s_exact_violation_line`.
"""

from __future__ import annotations

from pathlib import Path

from ops.type_gate import (
    BareIgnoreViolation,
    MembershipViolation,
    RawShimImportViolation,
    bare_ignores,
    membership,
    raw_shim_imports,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


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


# --------------------------------------------------------------------- raw_shim_imports
#
# bp-106 Item 4. The shimmed set is pinned in `ops/type_gate.py` as
# `{psutil: core/typedshims/psutil.py, lancedb: …, sknetwork: …}`, so the fixtures below plant
# files at those exact repo-relative paths when they mean "the shim itself".

# bp-105's violation, character-for-character as it stood at `ops/lifecycle/launcher.py:159`
# before bp-106 moved it. Note it already carried a warrant comment and a `noqa` — neither is
# the waiver token, and the scan must not accept either as one.
_BP105_LINE = (
    "        import psutil  # type: ignore[import-untyped]  "
    "# noqa: PLC0415  # warrant: see finding-0198\n"
)


def test_the_shim_itself_may_import_its_own_dependency_raw(tmp_path):
    """The rule is "ONE place", not "nowhere" — the shim is that place, unwaived."""
    _write(tmp_path / "core" / "typedshims" / "psutil.py",
           "import psutil  # type: ignore[import-untyped]  # warrant: no py.typed upstream\n")

    assert raw_shim_imports(tmp_path) == []


def test_a_raw_import_outside_the_shim_is_a_violation(tmp_path):
    """The core rule. `ops/` is not `core/typedshims/psutil.py`, so this is caught."""
    _write(tmp_path / "ops" / "thing.py", "import psutil\n")

    assert raw_shim_imports(tmp_path) == [
        RawShimImportViolation(path="ops/thing.py", lineno=1, dependency="psutil",
                               shim="core/typedshims/psutil.py")
    ]


def test_the_shim_of_one_dependency_may_not_import_ANOTHER_raw(tmp_path):
    """Each shim owns exactly its own dependency. The psutil shim importing raw lancedb is as much
    a violation as any other module doing it — otherwise `core/typedshims/` would be a blanket
    exemption zone rather than one quarantine per package."""
    _write(tmp_path / "core" / "typedshims" / "psutil.py", "import psutil\nimport lancedb\n")

    violations = raw_shim_imports(tmp_path)

    assert [(v.dependency, v.lineno) for v in violations] == [("lancedb", 2)]


def test_the_scan_catches_bp105s_exact_violation_line(tmp_path):
    """⚑ ITEM 4's NAMED FALSIFIER (bp-106 §7): *"reintroducing bp-105's exact line at
    `ops/lifecycle/launcher.py` leaves the gate green."* A ratchet that cannot reproduce its own
    warrant is decoration, so finding-0198's import is replanted verbatim — at its real path, inside
    a function body, with its original warrant and `noqa` comments intact — and must be caught.

    This simultaneously proves the two things that made the original invisible: the import was
    FUNCTION-LOCAL (a module-level-only walker would miss it) and it CARRIED A WARRANT COMMENT (so
    "has some comment" cannot be what waives a violation)."""
    _write(tmp_path / "ops" / "lifecycle" / "launcher.py",
           "def _process_identity(pid):\n"
           "    try:\n"
           + _BP105_LINE +
           "        proc = psutil.Process(pid)\n"
           "    except Exception:\n"
           "        return (None, None)\n")

    violations = raw_shim_imports(tmp_path)

    assert len(violations) == 1, f"finding-0198's own import line was not caught: {violations}"
    assert violations[0].path == "ops/lifecycle/launcher.py"
    assert violations[0].lineno == 3
    assert violations[0].dependency == "psutil"


def test_a_function_local_import_is_caught(tmp_path):
    """Stated on its own, because it is the invariant that decides whether the scan is worth
    anything: bp-105's violation was nested two blocks deep."""
    _write(tmp_path / "ops" / "deep.py",
           "def f():\n    if True:\n        for _ in range(1):\n            import sknetwork\n")

    violations = raw_shim_imports(tmp_path)

    assert [(v.dependency, v.lineno) for v in violations] == [("sknetwork", 4)]


def test_a_from_import_is_caught_too(tmp_path):
    """`from psutil import Process` binds raw psutil surface just as `import psutil` does —
    `_imported_roots` reduces both to the root package (mirrors the membership scan)."""
    _write(tmp_path / "ops" / "thing.py", "from psutil import Process\n")

    violations = raw_shim_imports(tmp_path)

    assert [(v.dependency, v.lineno) for v in violations] == [("psutil", 1)]


def test_importing_the_SHIM_is_never_a_violation(tmp_path):
    """The compliant call site — what `ops/lifecycle/launcher.py` and `core/vitals.py` do. The root
    package is `core`, not `psutil`, so nothing fires. If this ever flagged, the scan would be
    punishing the very pattern it exists to require."""
    _write(tmp_path / "ops" / "good.py",
           "from core.typedshims.psutil import process_name\n"
           "import core.typedshims.psutil as shim\n")

    assert raw_shim_imports(tmp_path) == []


def test_an_inline_waiver_with_a_reason_is_accepted(tmp_path):
    """§11's recorded default: the exemption lives at the import site, WITH its justification, so
    the reason cannot drift away from the code the way a central path list does."""
    _write(tmp_path / "tests" / "unit" / "test_x.py",
           "import lancedb  # typedshim-exempt: builds a legacy table the shim cannot model\n")

    assert raw_shim_imports(tmp_path) == []


def test_a_bare_waiver_token_with_no_reason_is_still_a_violation(tmp_path):
    """The token is not a magic word. An exemption with no reason is the failure mode the sibling
    bare-ignore scan exists to prevent, one rule over — so it is rejected here for the same
    reason."""
    _write(tmp_path / "tests" / "unit" / "test_x.py", "import lancedb  # typedshim-exempt\n")

    assert len(raw_shim_imports(tmp_path)) == 1


def test_a_waiver_token_with_a_colon_but_nothing_after_it_is_a_violation(tmp_path):
    """The near-miss of the near-miss: the colon is present, the reason is not."""
    _write(tmp_path / "tests" / "unit" / "test_x.py", "import lancedb  # typedshim-exempt:   \n")

    assert len(raw_shim_imports(tmp_path)) == 1


def test_a_waiver_on_a_DIFFERENT_line_does_not_cover_the_import(tmp_path):
    """"Inline at the import site" is literal. A waiver floating elsewhere in the file would
    re-create the central-allowlist rot §11 rejects, at file granularity."""
    _write(tmp_path / "ops" / "thing.py",
           "# typedshim-exempt: a reason, but not where the import is\n"
           "import psutil\n")

    violations = raw_shim_imports(tmp_path)

    assert [v.lineno for v in violations] == [2]


def test_a_waiver_inside_a_string_literal_does_not_waive_anything(tmp_path):
    """`tokenize`, not raw text (the sibling scan's lesson): a module that DOCUMENTS the protocol
    mentions the token in prose, and prose must not grant exemptions. `ops/type_gate.py` itself and
    this very test file are both live instances."""
    _write(tmp_path / "ops" / "thing.py",
           'DOC = "waive it with # typedshim-exempt: like this"\n'
           "import psutil\n")

    violations = raw_shim_imports(tmp_path)

    assert [v.lineno for v in violations] == [2]


def test_excluded_dirs_are_skipped_at_any_depth(tmp_path):
    """`.venv` holds the dependencies themselves — psutil's own sources import psutil constantly.
    Reuses `_EXCLUDED_DIRS`, and must skip it at ANY depth, not only at the top level."""
    _write(tmp_path / ".venv" / "lib" / "psutil" / "__init__.py", "import psutil\n")
    _write(tmp_path / "core" / "__pycache__" / "stale.py", "import lancedb\n")
    _write(tmp_path / "docs" / "snippets" / "example.py", "import psutil\n")

    assert raw_shim_imports(tmp_path) == []


def test_a_syntactically_broken_file_is_skipped_not_crashed_on(tmp_path):
    """The scan runs in CI over whatever is on disk and may never be the thing that kills the job —
    the same tolerance `membership` applies to a SyntaxError."""
    _write(tmp_path / "ops" / "broken.py", "def f(:\n")
    _write(tmp_path / "ops" / "real.py", "import psutil\n")

    violations = raw_shim_imports(tmp_path)

    assert [v.path for v in violations] == ["ops/real.py"]


def test_duckdb_is_deliberately_not_in_the_shimmed_set(tmp_path):
    """bp-106 §3 Q2: duckdb resolves TYPED, so it needs no shim and its raw imports are legitimate
    (`core/stores/telemetry.py` imports it directly and the Tier-1 floor is 0 errors). §2.5 lists it
    as a *candidate*; V2 cleared it. Pinned as a test so a future reader does not "complete" the
    candidate list and break every duckdb call site."""
    _write(tmp_path / "core" / "stores" / "telemetry.py", "import duckdb\n")

    assert raw_shim_imports(tmp_path) == []


# --- the LIVE tree: this is the enforcement, while main()'s exit code is parked ------------------

def test_the_live_tree_has_exactly_the_one_known_parked_violation():
    """⚑ THE RATCHET, and the reason `_RAW_SHIM_SCAN_IS_FATAL` being False is not a hole.

    bp-106 §10 forbade the plan from waiving the one violation it found beyond §3 Q3's census
    (`tests/unit/test_restart_trustworthy.py:21`, added the same day by bp-121's `e49a715`, in a
    file outside bp-106's write_scope), so `main()` reports it without voting on the exit code.
    Detection is enforced HERE instead, in the suite CI's `ratchet` job runs:

    * a NEW raw shimmed import anywhere in the repo turns this RED immediately — which is the
      property finding-0198 shows was missing, and the whole point of Item 4;
    * and when that last violation is finally waived, this goes red too, with the instruction
      below. That is deliberate: the parked state cannot be forgotten, because clearing it is what
      breaks the test.
    """
    violations = raw_shim_imports(REPO_ROOT)
    parked = "tests/unit/test_restart_trustworthy.py"

    unexpected = [v for v in violations if v.path != parked]
    assert not unexpected, (
        "a NEW raw import of a shimmed dependency landed outside its shim — route it through "
        f"core/typedshims/, or warrant it inline with `# typedshim-exempt: <reason>`: {unexpected}"
    )
    assert [v.path for v in violations] == [parked], (
        f"{parked} no longer imports raw psutil unwaived — finding-0223 is discharged. "
        "Flip `_RAW_SHIM_SCAN_IS_FATAL` to True in ops/type_gate.py and replace this test with "
        "`assert raw_shim_imports(REPO_ROOT) == []`."
    )
