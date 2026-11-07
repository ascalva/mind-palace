"""`head_sha` answers what `git rev-parse HEAD` answers, from files, or declines (None)."""

from __future__ import annotations

import subprocess
from pathlib import Path

from core.reference_view import head_sha

CHECKOUT = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists())


def _git(root: Path, *a: str) -> str:
    return subprocess.run(["git", "-C", str(root), *a], capture_output=True, text=True,
                          check=True).stdout.strip()


def _repo(tmp: Path) -> Path:
    _git(tmp, "init", "-q", "-b", "main")
    for k, v in (("user.email", "t@t"), ("user.name", "t"), ("commit.gpgsign", "false")):
        _git(tmp, "config", k, v)
    (tmp / "f").write_text("x")
    _git(tmp, "add", "f")
    _git(tmp, "commit", "-q", "-m", "one")
    return tmp


def test_this_checkout_agrees_with_git() -> None:
    assert head_sha(CHECKOUT) == _git(CHECKOUT, "rev-parse", "HEAD")


def test_loose_ref_packed_ref_and_detached(tmp_path: Path) -> None:
    r = _repo(tmp_path)
    assert head_sha(r) == _git(r, "rev-parse", "HEAD")
    _git(r, "pack-refs", "--all", "--prune")                 # the ref now lives in packed-refs
    assert head_sha(r) == _git(r, "rev-parse", "HEAD")
    _git(r, "checkout", "-q", "--detach")
    assert head_sha(r) == _git(r, "rev-parse", "HEAD")


def test_a_linked_worktree_reads_through_its_gitdir(tmp_path: Path) -> None:
    (tmp_path / "main").mkdir()
    r = _repo(tmp_path / "main")
    w = tmp_path / "wt"
    _git(r, "worktree", "add", "-q", "-b", "other", str(w))
    (w / "g").write_text("y")
    _git(w, "add", "g")
    _git(w, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "two")
    assert head_sha(w) == _git(w, "rev-parse", "HEAD") != head_sha(r)


def test_what_it_cannot_place_it_declines(tmp_path: Path) -> None:
    assert head_sha(tmp_path) is None                         # no .git at all
    (tmp_path / ".git").mkdir()
    assert head_sha(tmp_path) is None                         # no HEAD in it
