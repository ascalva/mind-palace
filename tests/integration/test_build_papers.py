"""`scripts/build_papers.sh`, run on papers made to fail and on the template.

Every test runs the script in a copy of the repository's layout under `tmp_path`, from a working
directory outside that copy, so a relative `PAPERS_OUT` resolves inside the copy and nothing writes
into the checkout. The tests that build need TeX Live with latexmk: they carry `needs_tex` and skip
without it, and the papers workflow, which installs TeX Live, runs them with `-m needs_tex`. The
last test puts a stand-in latexmk on PATH, so it needs no TeX and runs everywhere.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = ROOT / "papers" / "_template"
FIXTURES = ROOT / "tests" / "fixtures" / "papers"

_HAS_TEX = shutil.which("latexmk") is not None and shutil.which("pdflatex") is not None
_skip_without_tex = pytest.mark.skipif(not _HAS_TEX, reason="TeX Live with latexmk not installed")


def _sandbox(tmp_path: Path, *papers: Path) -> Path:
    """A copy of the repository's layout: the build script and the given paper directories."""
    repo = tmp_path / "repo"
    (repo / "scripts").mkdir(parents=True)
    shutil.copy2(ROOT / "scripts" / "build_papers.sh", repo / "scripts" / "build_papers.sh")
    for paper in papers:
        shutil.copytree(paper, repo / "papers" / paper.name)
    (tmp_path / "elsewhere").mkdir()                     # the caller's working directory
    return repo


def _build(repo: Path, out: str | Path, *dirs: str,
           path: str | None = None) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "PAPERS_OUT": str(out)}
    if path is not None:
        env["PATH"] = path
    return subprocess.run([str(repo / "scripts" / "build_papers.sh"), *dirs],
                          cwd=repo.parent / "elsewhere", env=env, capture_output=True, text=True,
                          timeout=600)


def _tree(root: Path) -> dict[Path, str]:
    """Every path under `root`: a digest of each file's bytes, and '' for a directory."""
    return {p: "" if p.is_dir() else hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob("*")}


def _written(before: dict[Path, str], after: dict[Path, str]) -> set[Path]:
    """The paths created, changed or removed between two trees."""
    return {p for p in before.keys() | after.keys() if before.get(p) != after.get(p)}


@pytest.mark.needs_tex
@_skip_without_tex
@pytest.mark.parametrize("absolute", [True, False], ids=["absolute", "relative"])
def test_the_template_builds_into_the_output_directory_and_nowhere_else(
        tmp_path: Path, absolute: bool) -> None:
    repo = _sandbox(tmp_path, TEMPLATE)
    out_dir = tmp_path / "out" if absolute else repo / "build" / "papers"
    before = _tree(tmp_path)
    done = _build(repo, out_dir if absolute else "build/papers", "papers/_template")
    assert done.returncode == 0, done.stdout + done.stderr
    assert done.stdout == "✓ _template\n"
    assert (out_dir / "_template" / "paper.pdf").is_file()
    assert not (out_dir / "_template" / "failed.log").exists()
    # Nothing outside the output directory changed, except the directories that lead to it: not
    # the repository copy, not its sources, not the caller's working directory.
    stray = {p for p in _written(before, _tree(tmp_path))
             if not (p.is_relative_to(out_dir) or out_dir.is_relative_to(p))}
    assert not stray, sorted(str(p.relative_to(tmp_path)) for p in stray)


@pytest.mark.needs_tex
@_skip_without_tex
@pytest.mark.parametrize("absolute", [True, False], ids=["absolute", "relative"])
def test_an_undefined_citation_fails_the_build(tmp_path: Path, absolute: bool) -> None:
    repo = _sandbox(tmp_path, FIXTURES / "undefined-citation")
    out_dir = tmp_path / "out" if absolute else repo / "build" / "papers"
    done = _build(repo, out_dir if absolute else "build/papers", "papers/undefined-citation")
    assert done.returncode == 1, done.stdout + done.stderr
    assert done.stdout.startswith("✗ undefined-citation: undefined references or citations\n")
    assert "Citation `nosuchkey'" in done.stdout                 # the warning, with the key
    assert (out_dir / "undefined-citation" / "failed.log").is_file()


@pytest.mark.needs_tex
@_skip_without_tex
def test_a_failed_build_prints_its_error_and_the_next_paper_still_builds(tmp_path: Path) -> None:
    repo = _sandbox(tmp_path, FIXTURES / "broken", TEMPLATE)
    out_dir = tmp_path / "out"
    done = _build(repo, out_dir, "papers/broken", "papers/_template")
    assert done.returncode == 1, done.stdout + done.stderr
    assert done.stdout.startswith("✗ broken: latexmk failed\n")
    assert "! Undefined control sequence." in done.stdout       # TeX's error line
    assert r"\buildtestundefinedmacro" in done.stdout           # and its context: where it stopped
    assert done.stdout.endswith("✓ _template\n")                # one failure does not stop the rest
    broken = out_dir / "broken"
    assert (broken / "failed.log").read_bytes() == (broken / "paper.log").read_bytes()
    assert not (out_dir / "_template" / "failed.log").exists()


def test_a_build_that_leaves_no_log_fails(tmp_path: Path) -> None:
    """A latexmk that succeeds without writing a log leaves the undefined-reference check nothing
    to read, so the paper fails instead of passing unchecked."""
    repo = _sandbox(tmp_path)
    (repo / "papers" / "quiet").mkdir(parents=True)
    (repo / "papers" / "quiet" / "paper.tex").write_text("\\documentclass{article}\n")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "latexmk").write_text("#!/bin/sh\nexit 0\n")
    (bin_dir / "latexmk").chmod(0o755)
    path = f"{bin_dir}:{os.environ.get('PATH', '/usr/bin:/bin')}"
    done = _build(repo, tmp_path / "out", "papers/quiet", path=path)
    assert done.returncode == 1, done.stdout + done.stderr
    assert done.stdout.startswith("✗ quiet: no log at ")
    assert (tmp_path / "out" / "quiet" / "failed.log").is_file()
