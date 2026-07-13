"""ops/code_sensor.py — the model-less code-sensor agent (hermetic tmp git repo)."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

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
    emitted: list[dict[str, Any]] = field(default_factory=list)

    def emit(self, **kw):
        self.emitted.append(kw)


@pytest.fixture
def repo(tmp_path) -> Path:
    r = tmp_path / "repo"
    r.mkdir()
    _git(r, "init", "-q", "-b", "main")
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


def test_main_is_the_ingestion_branch(repo, tmp_path):
    agent = CodeSensor(repo=repo, db=open_snapshot_db(tmp_path / "s.sqlite"), attestor=None)
    assert agent.sync().ingested == 2

    _git(repo, "checkout", "-qb", "feature")
    _commit(repo, "wip.py", "def wip():\n    pass\n")
    report = agent.sync()                       # run FROM the feature branch
    assert report.ingested == 0                 # pinned by ref: branch work invisible
    assert report.ledger_total == 2

    _git(repo, "checkout", "-q", "main")
    _git(repo, "merge", "-q", "--no-edit", "feature")
    report = agent.sync()
    assert report.ingested >= 1                 # lands on main -> enters the ledger
    assert "wip" in {q for (q,) in agent.db.execute("SELECT qualname FROM symbols")}


def test_commit_headers_parsed_and_healed(repo, tmp_path):
    db = open_snapshot_db(tmp_path / "s.sqlite")
    agent = CodeSensor(repo=repo, db=db, attestor=None)
    _commit(repo, "c.py", "def c():\n    pass\n")  # message: "c.py" (non-conforming)
    (repo / "d.py").write_text("def d():\n    pass\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "feat(core): add d")
    agent.sync()

    rows = dict(db.execute("SELECT subject, ctype || '|' || scope FROM snapshots"))
    assert rows["feat(core): add d"] == "feat|core"
    assert rows["c.py"] == "|"                  # non-conforming: lookup degrades, honestly

    # healing: blank a subject (a pre-header row) and re-sync
    with db:
        db.execute("UPDATE snapshots SET subject='', ctype='', scope=''")
    agent.sync()
    healed = {s for (s,) in db.execute("SELECT subject FROM snapshots")}
    assert "feat(core): add d" in healed and "" not in healed


def test_agent_without_attestor_still_ingests(repo, tmp_path):
    agent = CodeSensor(repo=repo, db=open_snapshot_db(tmp_path / "s.sqlite"), attestor=None)
    assert agent.sync().ingested == 2
    rows = agent.db.execute(
        "SELECT commit_sha, qualname FROM symbols ORDER BY commit_sha, qualname").fetchall()
    assert len(rows) == 3                       # commit1: a — commit2: a AND b (rows per commit)
    assert {q for _, q in rows} == {"a", "b"}


# --- bp-018 Item 4: the interpreter version is live end-to-end --------------------------------
def test_version_bump_makes_backfill_reproject_and_archive(repo, tmp_path, monkeypatch):
    """The Item 4 falsifier, inverted: after a version bump, `backfill_observations()`
    re-projects EVERY ledger commit (the version key is live through is_projected →
    add_batch → mark_projected), old generations land in the history sidecar, and
    `sync()` still projects only newly-ingested commits (re-projection stays
    deliberate — plan Q5, the §11 parked decision unchanged)."""
    from core.sensing import CodeSensingHandoff
    from core.stores.code_observations import CodeObservationStore
    from core.stores.observation_history import ObservationHistoryStore

    obs = CodeObservationStore(tmp_path / "code_observations.sqlite")
    hist = ObservationHistoryStore(tmp_path / "observation_history.sqlite")
    sensor = CodeSensor(repo=repo, db=open_snapshot_db(tmp_path / "s.sqlite"), attestor=None,
                        observations=obs,
                        obs_handoff=CodeSensingHandoff(handoff=tmp_path / "handoff"),
                        history=hist)
    assert sensor.sync().projected == 2
    rows_v1 = obs.count()
    assert rows_v1 == 6                     # c1: a.py module+a — c2: a.py module+a, b.py module+b
    shas = _git(repo, "rev-list", "--reverse", "main").splitlines()

    monkeypatch.setattr("ops.code_sensor.INTERPRETER_VERSION", "2.0.0")
    assert sensor.sync().projected == 0     # invariant: sync projects newly-ingested ONLY (Q5)
    assert sensor.backfill_observations() == 2   # the deliberate act: ALL commits eligible again
    assert obs.count() == rows_v1                # latest-per-identity: replaced, never doubled
    assert {r["interpreter"] for r in obs.all_rows()} == {"2.0.0"}
    assert hist.count("code") == rows_v1         # every superseded generation archived
    for sha in shas:
        assert obs.is_projected(sha, "2.0.0")    # projected counts it, version-keyed
        assert obs.is_projected(sha, "1.0.0")    # the old worldview's mark is history, not erased
    chain = obs.chain_for(shas[0], "a.py", "a", history=hist)
    assert [g["interpreter"] for g in chain] == ["1.0.0", "2.0.0"]   # the §2.4 queryable chain
    assert sensor.backfill_observations() == 0   # idempotent at the new version


def test_reset_wipes_readings_but_refuses_the_worldview_history(tmp_path):
    """Pins §6(f): `reset_targets()` still lists the readings store (corpus-side, wiped,
    rebuilt by re-projection) and the history sidecar is NOT a target — it sits in
    `_RESET_GUARD`, where the launcher's target assertion refuses it outright."""
    from typing import cast

    from config.loader import Config
    from ops.lifecycle.launcher import _RESET_GUARD, Launcher
    from ops.lifecycle.runs import RunLedger

    class _Paths:
        def __init__(self, d: Path) -> None:
            self.data_dir = d
            self.raw_store = d / "raw.sqlite"
            self.vector_store = d / "vectors.lance"
            self.vault_catalog = d / "vault_catalog.sqlite"
            self.derived_store = d / "derived.sqlite"
            self.attestation_store = d / "attestations.sqlite"

    class _Cfg:
        def __init__(self, d: Path) -> None:
            self.paths = _Paths(d)

    launcher = Launcher(cfg=cast(Config, _Cfg(tmp_path / "data")),
                        runs=cast(RunLedger, None), repo_root=tmp_path)
    names = {t.name for t in launcher.reset_targets()}
    assert "code_observations.sqlite" in names           # readings: corpus-side, wiped
    assert "observation_history.sqlite" not in names     # the worldview ledger is NOT a target…
    assert "observation_history.sqlite" in _RESET_GUARD  # …and the guard refuses it structurally
