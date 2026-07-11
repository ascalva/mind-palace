"""ops/code_snapshot.py — the docstring column (B-a, bp-011 Item 1).

Falsifier under test: a docstring visible to `ast.get_docstring` missing from the
ledger. Proven both directions — every docstring the AST exposes lands in the ledger,
and nothing the AST does NOT expose is fabricated (absence -> '').
"""

from __future__ import annotations

import ast
import subprocess
from pathlib import Path

import pytest

from ops.code_snapshot import (
    backfill,
    backfill_docstrings,
    open_snapshot_db,
    parse_source,
    snapshot_commit,
)


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True,
                          capture_output=True, text=True).stdout


def _commit(repo: Path, name: str, body: str, msg: str | None = None) -> None:
    (repo / name).write_text(body)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", msg or name)


@pytest.fixture
def repo(tmp_path) -> Path:
    r = tmp_path / "repo"
    r.mkdir()
    _git(r, "init", "-q", "-b", "main")
    _git(r, "config", "user.email", "t@t")
    _git(r, "config", "user.name", "t")
    return r


DOCUMENTED = '''"""Module docstring — the file's own Rosetta payload."""

class Thing:
    """A documented class."""

    def method(self, x):
        """A documented method."""
        return x

async def run():
    """A documented async function."""


def undocumented():
    return 1
'''


def test_parse_source_captures_every_docstring_ast_exposes():
    shape = parse_source("mod.py", "0" * 40, DOCUMENTED)
    assert shape.docstring == "Module docstring — the file's own Rosetta payload."

    by_name = {s.qualname: s.docstring for s in shape.symbols}
    assert by_name["Thing"] == "A documented class."
    assert by_name["Thing.method"] == "A documented method."
    assert by_name["run"] == "A documented async function."
    # falsifier direction 2: absence is honest, not fabricated
    assert by_name["undocumented"] == ""


def test_ast_get_docstring_agrees_with_parse_source():
    """Direct falsifier check: everything ast.get_docstring sees, parse_source records."""
    tree = ast.parse(DOCUMENTED)
    shape = parse_source("mod.py", "0" * 40, DOCUMENTED)
    assert ast.get_docstring(tree) == shape.docstring

    expected: dict[str, str] = {}

    def walk(node: ast.AST, prefix: str) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
                qual = f"{prefix}{child.name}"
                expected[qual] = ast.get_docstring(child) or ""
                walk(child, f"{qual}.")

    walk(tree, "")
    actual = {s.qualname: s.docstring for s in shape.symbols}
    assert actual == expected


def test_snapshot_persists_docstrings_to_ledger(repo, tmp_path):
    _commit(repo, "mod.py", DOCUMENTED)
    db = open_snapshot_db(tmp_path / "snap.sqlite")
    sha = snapshot_commit(db, repo)
    assert sha is not None

    file_doc = db.execute(
        "SELECT docstring FROM files WHERE path='mod.py'").fetchone()[0]
    assert file_doc == "Module docstring — the file's own Rosetta payload."

    docs = dict(db.execute("SELECT qualname, docstring FROM symbols"))
    assert docs["Thing"] == "A documented class."
    assert docs["Thing.method"] == "A documented method."
    assert docs["run"] == "A documented async function."
    assert docs["undocumented"] == ""


def test_parse_error_files_carry_no_fabricated_docstring():
    shape = parse_source("bad.py", "0" * 40, "def broken(:\n")
    assert shape.parse_error
    assert shape.docstring == ""


def test_backfill_docstrings_heals_pre_existing_rows(repo, tmp_path):
    """Simulates the real-ledger migration: rows recorded before docstring columns
    existed (docstring='' in files/symbols) get healed by a re-parse pass, idempotently."""
    _commit(repo, "mod.py", DOCUMENTED)
    db = open_snapshot_db(tmp_path / "snap.sqlite")
    sha = snapshot_commit(db, repo)

    # simulate the pre-migration state: blank every docstring column, as if this row
    # had been written by a version of the code before the docstring columns existed.
    with db:
        db.execute("UPDATE files SET docstring=''")
        db.execute("UPDATE symbols SET docstring=''")

    updated = backfill_docstrings(db, repo)
    assert updated == 1                      # one file healed

    file_doc = db.execute(
        "SELECT docstring FROM files WHERE commit_sha=? AND path='mod.py'", (sha,)
    ).fetchone()[0]
    assert file_doc == "Module docstring — the file's own Rosetta payload."
    docs = dict(db.execute("SELECT qualname, docstring FROM symbols"))
    assert docs["Thing.method"] == "A documented method."
    assert docs["undocumented"] == ""

    # idempotent: a second backfill pass touches nothing (already marked visited)
    assert backfill_docstrings(db, repo) == 0


def test_backfill_docstrings_does_not_reflag_genuinely_undocumented_files(repo, tmp_path):
    """A file with NO docstrings anywhere (docstring='' is correct, not stale) must not
    be re-scanned forever — the _docstring_backfilled mark distinguishes 'undocumented'
    from 'not yet migrated'."""
    _commit(repo, "plain.py", "def undocumented():\n    return 1\n")
    db = open_snapshot_db(tmp_path / "snap.sqlite")
    snapshot_commit(db, repo)

    assert backfill_docstrings(db, repo) == 0   # nothing to update, but marks the row
    marked = db.execute("SELECT count(*) FROM _docstring_backfilled").fetchone()[0]
    assert marked == 1


def test_backfill_over_history_is_idempotent_with_docstrings(repo, tmp_path):
    _commit(repo, "a.py", '"""a module."""\ndef a():\n    """doc a."""\n')
    _commit(repo, "b.py", '"""b module."""\ndef b():\n    pass\n')
    db = open_snapshot_db(tmp_path / "snap.sqlite")
    assert backfill(db, repo) == 2
    assert backfill(db, repo) == 0            # idempotent

    docs = dict(db.execute("SELECT qualname, docstring FROM symbols"))
    assert docs["a"] == "doc a."
    assert docs["b"] == ""

    assert backfill_docstrings(db, repo) == 0   # already fresh from snapshot_commit
