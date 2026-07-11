"""End-to-end tests for the B-b projection: sync() emits φ_code (bp-012 Item 5).

Fixture repo → sync → symbol-grain rows in the OBSERVED-only store, one batch per commit,
each attested `project_observations` with the ingest_commit attestation as chain parent
(plan Q5, via `producers_of`). The B-b falsifier, inverted: a second sync/projection of
the same commits changes NOTHING — row count, projections, attestations all unchanged.
Plus the §2.6 firewall: a MirrorView over a source containing observation rows REFUSES
them, and the honest π_MR projection excludes them.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import pytest

from core.attestation.attestor import StoreAttestor
from core.attestation.store import AttestationStore
from core.mirror import MirrorView, NonMirrorRowError
from core.provenance import Provenance
from core.sensing import CodeSensingHandoff, ObservedView
from core.stores.code_observations import CodeObservationStore
from ops.code_sensor import CodeSensor
from ops.code_snapshot import open_snapshot_db


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True,
                          capture_output=True, text=True).stdout


def _commit(repo: Path, name: str, body: str) -> None:
    (repo / name).write_text(body)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", f"feat: {name}")


@pytest.fixture
def repo(tmp_path) -> Path:
    r = tmp_path / "repo"
    r.mkdir()
    _git(r, "init", "-q", "-b", "main")
    _git(r, "config", "user.email", "t@t")
    _git(r, "config", "user.name", "t")
    _commit(r, "a.py", '"""Module A."""\n\ndef a(x):\n    """Does a."""\n    return x\n')
    _commit(r, "b.py", "class B:\n    def m(self):\n        pass\n")
    return r


def _sensor(repo: Path, tmp_path, *, attested: bool = True) -> tuple[CodeSensor, AttestationStore]:
    att_store = AttestationStore(tmp_path / "attestations.sqlite")
    return CodeSensor(
        repo=repo,
        db=open_snapshot_db(tmp_path / "snapshots.sqlite"),
        attestor=StoreAttestor(att_store) if attested else None,
        observations=CodeObservationStore(tmp_path / "code_observations.sqlite"),
        obs_handoff=CodeSensingHandoff(handoff=tmp_path / "handoff"),
    ), att_store


# --- the projection lands, symbol-grain -----------------------------------------------------
def test_sync_projects_symbol_grain_rows_for_each_new_commit(repo, tmp_path):
    sensor, _ = _sensor(repo, tmp_path)
    report = sensor.sync()
    assert report.ingested == 2 and report.projected == 2
    obs = sensor.observations
    assert obs is not None
    # commit1: a.py (module + def a) = 2.  commit2: a.py (2) + b.py (module + B + B.m) = 5.
    assert obs.count() == report.observation_rows == 7
    shas = _git(repo, "rev-list", "--reverse", "main").splitlines()
    c1 = obs.rows_for(shas[0])
    assert [(r["qualname"], r["kind"]) for r in c1] == [("", "module"), ("a", "function")]
    assert c1[0]["docstring"] == "Module A." and c1[1]["docstring"] == "Does a."  # real, not ''
    assert all(r["provenance"] == Provenance.OBSERVED.value for r in obs.all_rows())
    assert all(r["references_out"] == [] for r in obs.all_rows())   # B-b emits empty; B-c fills
    c2_kinds = {(r["path"], r["qualname"], r["kind"]) for r in obs.rows_for(shas[1])}
    assert ("b.py", "B", "class") in c2_kinds and ("b.py", "B.m", "function") in c2_kinds


# --- the B-b falsifier, inverted (verbatim §6) -----------------------------------------------
def test_second_projection_of_the_same_commit_changes_nothing(repo, tmp_path):
    sensor, att_store = _sensor(repo, tmp_path)
    sensor.sync()
    obs = sensor.observations
    assert obs is not None
    rows_before, atts_before = obs.count(), att_store.count()

    report2 = sensor.sync()                       # a second projection of the same commits
    assert obs.count() == rows_before             # row count UNCHANGED — the falsifier holds
    assert report2.projected == 0 and report2.observation_rows == 0
    assert att_store.count() == atts_before      # and no duplicate attestations either


# --- attestation parentage (plan Q5): ingest_commit → project_observations -------------------
def test_projection_attestation_chains_to_the_ingest_attestation(repo, tmp_path):
    sensor, att_store = _sensor(repo, tmp_path)
    sensor.sync()
    obs = sensor.observations
    assert obs is not None
    ingests = {a.output_hashes[0]: a for a in att_store.all() if a.action == "ingest_commit"}
    projections = [a for a in att_store.all() if a.action == "project_observations"]
    assert len(projections) == 2 and len(ingests) == 2
    for proj in projections:
        sha = proj.input_hashes[0]
        assert proj.agent_role == "code_sensor"
        assert ingests[sha].id in proj.derived_from_ids   # ingest_commit is the chain parent
        chain = att_store.chain_for(proj.id)
        assert chain.is_complete() and ingests[sha] in chain.attestations
        assert obs.is_projected(sha)                       # and the batch hash was recorded


# --- §2.6 firewall: observation rows are mirror-opaque ---------------------------------------
def test_mirror_view_refuses_a_source_containing_observation_rows(repo, tmp_path):
    sensor, _ = _sensor(repo, tmp_path)
    sensor.sync()
    obs = sensor.observations
    assert obs is not None
    store: CodeObservationStore = obs                      # narrowed binding for the closure

    class _LeakySource:
        """A buggy RowSource that ignores the provenance filter — the §2.6 attack shape."""

        def all_rows(self, *, provenances: Any = None) -> list[dict[str, Any]]:
            return store.all_rows()                        # leaks observed rows regardless

    with pytest.raises(NonMirrorRowError):
        MirrorView.project(_LeakySource())                 # refused: OBSERVED is mirror-opaque
    assert len(MirrorView.project(obs)) == 0               # honest π_MR: excluded entirely
    assert len(ObservedView(_rows=tuple(obs.all_rows()))) == obs.count()   # the sanctioned tier


# --- seam healing: a batch left in the handoff (crash) is collected on the next sync ---------
def test_uncollected_handoff_batch_heals_on_next_sync(repo, tmp_path):
    sensor, _ = _sensor(repo, tmp_path)
    sensor.sync()
    obs, handoff = sensor.observations, sensor.obs_handoff
    assert obs is not None and handoff is not None
    from core.stores.code_observations import CodeObservation
    stray = CodeObservation(commit_sha="deadbeef", path="x.py", qualname="", kind="module")
    handoff.emit_batch("deadbeef", [stray])                # emitted, never collected (a crash)

    _commit(repo, "c.py", "def c():\n    pass\n")          # any new commit triggers a projection
    sensor.sync()
    assert obs.rows_for("deadbeef") != []                  # the stray batch healed, rescan-style
    assert list(handoff.batches_dir.glob("*.json")) == []  # and the handoff drained


# --- the history backfill: available, NOT wired into sync ------------------------------------
def test_backfill_observations_projects_ledger_history_idempotently(repo, tmp_path):
    ledger_only = CodeSensor(repo=repo, db=open_snapshot_db(tmp_path / "snapshots.sqlite"),
                             attestor=None)
    ledger_only.sync()                                     # pre-B-b history: ledger, no projection

    sensor, _ = _sensor(repo, tmp_path, attested=False)    # same dbs, projection pair wired
    assert sensor.sync().projected == 0                    # nothing NEW → sync projects nothing
    obs = sensor.observations
    assert obs is not None
    assert obs.count() == 0                                # history is NOT auto-backfilled (§11)

    assert sensor.backfill_observations() == 2             # the owner-nod path projects history
    assert obs.count() == 7
    assert sensor.backfill_observations() == 0             # idempotent re-run


def test_sensor_without_the_projection_pair_degrades_to_ledger_only(repo, tmp_path):
    sensor = CodeSensor(repo=repo, db=open_snapshot_db(tmp_path / "s.sqlite"), attestor=None)
    report = sensor.sync()
    assert report.ingested == 2 and report.projected == 0  # pre-B-b callers unchanged
    assert sensor.backfill_observations() == 0
