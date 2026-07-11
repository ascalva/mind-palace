"""ops/code_snapshot.py — structural per-commit snapshots (hermetic tmp git repo)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from ops.code_snapshot import backfill, open_snapshot_db, parse_source, snapshot_commit


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True,
                          capture_output=True, text=True).stdout


@pytest.fixture
def repo(tmp_path) -> Path:
    r = tmp_path / "repo"
    r.mkdir()
    _git(r, "init", "-q")
    _git(r, "config", "user.email", "t@t")
    _git(r, "config", "user.name", "t")
    (r / "mod.py").write_text(
        "import json\nfrom pathlib import Path\n\n"
        "class Thing:\n    def method(self, x):\n        return x\n\n"
        "async def run():\n    pass\n")
    _git(r, "add", "-A")
    _git(r, "commit", "-qm", "one")
    return r


def test_snapshot_records_structure(repo, tmp_path):
    db = open_snapshot_db(tmp_path / "snap.sqlite")
    sha = snapshot_commit(db, repo)
    assert sha is not None

    files = db.execute("SELECT path, loc, functions, classes FROM files").fetchall()
    assert files == [("mod.py", 9, 2, 1)]
    kinds = dict(db.execute("SELECT qualname, kind FROM symbols"))
    assert kinds == {"Thing": "class", "Thing.method": "function", "run": "async_function"}
    sig = db.execute("SELECT signature FROM symbols WHERE qualname='Thing.method'").fetchone()[0]
    assert sig == "(self, x)"
    imports = {m for (m,) in db.execute("SELECT module FROM imports")}
    assert imports == {"json", "pathlib"}


def test_idempotent_by_sha(repo, tmp_path):
    db = open_snapshot_db(tmp_path / "snap.sqlite")
    assert snapshot_commit(db, repo) is not None
    assert snapshot_commit(db, repo) is None  # second run: no-op
    assert db.execute("SELECT count(*) FROM snapshots").fetchone()[0] == 1


def test_backfill_walks_history_and_snapshots_committed_tree(repo, tmp_path):
    # second commit changes the file; a dirty working tree must NOT leak into snapshots
    (repo / "mod.py").write_text("def solo():\n    pass\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "two")
    (repo / "mod.py").write_text("SYNTAX ERROR (\n")  # uncommitted — must be invisible

    db = open_snapshot_db(tmp_path / "snap.sqlite")
    assert backfill(db, repo) == 2
    shas = [s for (s,) in db.execute(
        "SELECT commit_sha FROM snapshots ORDER BY committed_at")]
    assert len(shas) == 2
    v2 = {q for (q,) in db.execute(
        "SELECT qualname FROM symbols WHERE commit_sha=?", (shas[1],))}
    assert v2 == {"solo"}                      # committed tree, not working dir
    assert backfill(db, repo) == 0             # idempotent


def test_parse_error_recorded_not_fatal():
    shape = parse_source("bad.py", "0" * 40, "def broken(:\n")
    assert shape.parse_error and shape.loc == 1 and not shape.symbols
