"""ops/code_sensor.py — the model-less code-sensor agent (hermetic tmp git repo)."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from ops.code_sensor import CodeSensor
from ops.code_snapshot import open_snapshot_db


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True,
                          capture_output=True, text=True).stdout


def _commit(repo: Path, name: str, body: str) -> None:
    (repo / name).write_text(body)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", name)


@dataclass
class FakeAttestor:
    emitted: list[dict] = field(default_factory=list)

    def emit(self, **kw):
        self.emitted.append(kw)


@pytest.fixture
def repo(tmp_path) -> Path:
    r = tmp_path / "repo"
    r.mkdir()
    _git(r, "init", "-q")
    _git(r, "config", "user.email", "t@t")
    _git(r, "config", "user.name", "t")
    _commit(r, "a.py", "def a():\n    pass\n")
    _commit(r, "b.py", "def b():\n    pass\n")
    return r


def test_sync_catches_up_and_attests_each_commit(repo, tmp_path):
    att = FakeAttestor()
    agent = CodeSensor(repo=repo, db=open_snapshot_db(tmp_path / "s.sqlite"), attestor=att)

    report = agent.sync()
    assert report.ingested == 2 and report.ledger_total == 2
    assert [e["action"] for e in att.emitted] == ["ingest_commit", "ingest_commit"]
    assert all(e["agent_role"] == "code_sensor" for e in att.emitted)
    # chain leaf: input == output == the commit sha, oldest first
    shas = _git(repo, "rev-list", "--reverse", "HEAD").splitlines()
    assert [e["input_hashes"] for e in att.emitted] == [[s] for s in shas]


def test_sync_is_idempotent_and_heals_missed_commits(repo, tmp_path):
    agent = CodeSensor(repo=repo, db=open_snapshot_db(tmp_path / "s.sqlite"), attestor=None)
    assert agent.sync().ingested == 2
    assert agent.sync().ingested == 0          # no-op re-sync

    _commit(repo, "c.py", "def c():\n    pass\n")   # a commit the hook "missed"
    report = agent.sync()
    assert report.ingested == 1 and report.ledger_total == 3


def test_agent_without_attestor_still_ingests(repo, tmp_path):
    agent = CodeSensor(repo=repo, db=open_snapshot_db(tmp_path / "s.sqlite"), attestor=None)
    assert agent.sync().ingested == 2
    rows = agent.db.execute(
        "SELECT commit_sha, qualname FROM symbols ORDER BY commit_sha, qualname").fetchall()
    assert len(rows) == 3                       # commit1: a — commit2: a AND b (rows per commit)
    assert {q for _, q in rows} == {"a", "b"}
