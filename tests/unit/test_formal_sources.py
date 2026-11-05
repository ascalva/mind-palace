"""The L1 gate's first step refuses build-time code (the review of 2026-11-05, gate finding 1): a
`run_cmd` in a proof file ran while `check.sh` built the library, before any checker looked, with
no warning of its own, so `--wfail` passed. The scan strips comments and strings, so prose that
says "syntax" or "opaque" passes, and code that runs does not."""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("check_formal_sources",
                                               ROOT / "scripts" / "check_formal_sources.py")
assert _spec is not None and _spec.loader is not None
cfs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cfs)

LAKEFILE = (ROOT / "formal" / "lakefile.toml").read_text(encoding="utf-8")


def _root(tmp_path: Path, lean: str, lakefile: str = LAKEFILE) -> Path:
    (tmp_path / "Palace").mkdir()
    (tmp_path / "Palace" / "X.lean").write_text(lean, encoding="utf-8")
    (tmp_path / "lakefile.toml").write_text(lakefile, encoding="utf-8")
    return tmp_path


def test_the_tree_as_it_is_passes() -> None:
    assert cfs.scan(ROOT / "formal") == []


def test_code_that_runs_at_build_time_is_refused_and_prose_is_not(tmp_path: Path) -> None:
    lean = ('/-- The syntax of an opaque token; `run_cmd` in a docstring is prose. -/\n'
            'theorem t : True := trivial -- #eval in a comment is prose\n'
            'def s : String := "run_cmd in a string is data"\n'
            'run_cmd IO.FS.writeFile "x" "y"\n'
            'set_option warn.sorry false in\n'
            'set_option synthInstance.maxSize 256 in\n'
            'unsafe def u : Nat := 0\n')
    problems = cfs.scan(_root(tmp_path, lean))
    assert {p.split(": ", 1)[1] for p in problems} == {
        "`run_cmd`", "`IO`", "set_option warn.sorry", "`unsafe`"}
    assert all(p.startswith("Palace/X.lean:") for p in problems)
    assert {int(p.split(":")[1]) for p in problems} == {4, 5, 7}


def test_a_weakened_build_option_and_a_lint_exception_are_refused(tmp_path: Path) -> None:
    lakefile = LAKEFILE.replace("autoImplicit = false\n",
                                "autoImplicit = false\nwarn.sorry = false\n")
    root = _root(tmp_path, "theorem t : True := trivial\n", lakefile)
    (root / "scripts").mkdir()
    (root / "scripts" / "nolints.json").write_text("[]", encoding="utf-8")
    assert cfs.scan(root) == ["lakefile.toml: leanOptions.warn.sorry",
                              "scripts/nolints.json: a linter exception file"]
