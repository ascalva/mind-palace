"""The operational lifecycle — run ledger, preflight, the launcher (start/stop/reset).

Exercises the whole lifecycle without any live daemon or model: the run ledger's clean/unclean
detection (the basis for recovery), preflight's fail-closed aggregation, the launcher's graceful
start→serve→mark-clean, recovery on an unclean prior run, and that `reset` wipes the corpus but
NEVER the production Vault Raft store.
"""

import dataclasses
from pathlib import Path

from config.loader import load_config
from ops.lifecycle.launcher import Components, Launcher
from ops.lifecycle.preflight import Check, Preflight, run_preflight
from ops.lifecycle.runs import RunLedger


# --- run ledger ---------------------------------------------------------------------------------
def test_run_ledger_clean_shutdown_detection(tmp_path):
    runs = RunLedger(tmp_path / "runs.sqlite")
    assert runs.last_was_clean() is True            # no prior run → clean
    r = runs.open_run(commit_sha="abc123", dirty=False, pid=999)
    assert r.active and runs.last().id == r.id
    runs.mark_stopped(r.id, clean=True)
    assert runs.last_was_clean() is True            # prior run closed clean


def test_run_ledger_crash_is_unclean(tmp_path):
    runs = RunLedger(tmp_path / "runs.sqlite")
    runs.open_run(commit_sha="abc", dirty=True, pid=1)   # never marked stopped = crash
    assert runs.last_was_clean() is False               # → next start should recover
    assert runs.last().dirty is True                    # commit/dirty round-trip


# --- preflight ----------------------------------------------------------------------------------
def _cfg(tmp_path):
    base = load_config()
    paths = dataclasses.replace(base.paths, data_dir=tmp_path,
                                raw_store=tmp_path / "raw", vector_store=tmp_path / "v.lance",
                                vault_catalog=tmp_path / "cat.sqlite",
                                derived_store=tmp_path / "d.sqlite",
                                attestation_store=tmp_path / "att.sqlite",
                                telemetry_db=tmp_path / "t.duckdb")
    vault = dataclasses.replace(base.vault, path=tmp_path / "vault")
    return dataclasses.replace(base, paths=paths, vault=vault)


def test_preflight_fails_closed_on_a_required_check(tmp_path):
    cfg = _cfg(tmp_path)

    def ok(_c):
        return Check("ollama", required=True, ok=True, detail="up")

    def down(_c):
        return Check("ollama", required=True, ok=False, detail="down")

    def warn(_c):
        return Check("sandbox", required=False, ok=False, detail="no podman")

    assert run_preflight(cfg, ollama=ok, vault=ok, podman=warn).ok is True   # optional fail = warn
    pf = run_preflight(cfg, ollama=down, vault=ok, podman=warn)
    assert pf.ok is False and any(c.name == "ollama" for c in pf.failures())


# --- the launcher (fake components; no models) --------------------------------------------------
class _FakeSupervisor:
    def __init__(self):
        self.runs = 0

    def run(self):
        self.runs += 1
        return 0


class _FakeWatcher:
    def __init__(self):
        self.started = self.stopped = False

    def start(self):
        self.started = True
        return "poll"

    def stop(self):
        self.stopped = True


class _FakeQueue:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


def _launcher(tmp_path, **kw):
    sup, watch, q = _FakeSupervisor(), _FakeWatcher(), _FakeQueue()
    calls = {"catchup": 0, "housekeeping": 0, "health": 0}
    comps = Components(
        supervisor=sup, watcher=watch, queue=q,
        enqueue_catchup=lambda: calls.__setitem__("catchup", calls["catchup"] + 1),
        enqueue_housekeeping=lambda: calls.__setitem__("housekeeping", calls["housekeeping"] + 1),
        health_check=lambda: (calls.__setitem__("health", calls["health"] + 1), [])[1],
    )
    passing = Preflight((Check("x", required=True, ok=True, detail="ok"),))
    launcher = Launcher(
        cfg=_cfg(tmp_path), runs=RunLedger(tmp_path / "runs.sqlite"),
        repo_root=Path(".").resolve(), components_factory=lambda _cfg: comps,
        preflight_fn=lambda _cfg: passing, tick_seconds=0, health_interval_s=0, **kw,
    )
    return launcher, sup, watch, q, calls


def test_start_serves_then_marks_run_clean(tmp_path):
    launcher, sup, watch, q, calls = _launcher(tmp_path)
    rc = launcher.start(max_ticks=3)
    assert rc == 0
    assert watch.started and watch.stopped          # watcher lifecycle
    assert sup.runs == 3                             # supervised N boundaries
    assert calls["catchup"] == 1 and calls["housekeeping"] >= 1
    assert calls["health"] >= 1                       # the OS-health agent ran (sense + report)
    last = launcher.runs.last()
    assert (not last.active) and last.clean_shutdown and not last.recovery   # graceful clean stop


class _FakeChild:
    name = "monitor"
    pid = 123

    def __init__(self):
        self.started = self.stopped = 0
        self._alive = True

    def start(self):
        self.started += 1

    def alive(self):
        return self._alive

    def stop(self):
        self.stopped += 1
        self._alive = False


def test_launcher_supervises_children_and_writes_snapshots(tmp_path):
    sup, watch, q = _FakeSupervisor(), _FakeWatcher(), _FakeQueue()
    child, snaps = _FakeChild(), []
    comps = Components(supervisor=sup, watcher=watch, queue=q, children=[child],
                       snapshot=lambda run, flags: snaps.append((run, flags)))
    passing = Preflight((Check("x", required=True, ok=True, detail="ok"),))
    launcher = Launcher(
        cfg=_cfg(tmp_path), runs=RunLedger(tmp_path / "runs.sqlite"),
        repo_root=Path(".").resolve(), components_factory=lambda _c: comps,
        preflight_fn=lambda _c: passing, tick_seconds=0, health_interval_s=0, snapshot_interval_s=0)
    launcher.start(max_ticks=2)
    assert child.started == 1                  # spawned once on serve (alive → not re-spawned)
    assert child.stopped == 1                  # drained on graceful shutdown (SIGTERM)
    assert len(snaps) >= 1 and snaps[0][0] is not None   # snapshot written with the active run


def test_unclean_prior_run_enters_recovery(tmp_path):
    runs = RunLedger(tmp_path / "runs.sqlite")
    runs.open_run(commit_sha="old", dirty=False, pid=1)   # a crash (never stopped)
    launcher, sup, watch, _q, _c = _launcher(tmp_path)
    launcher.runs = runs                                   # share the ledger with the crash
    launcher.start(max_ticks=2)
    assert sup.runs == 0 and not watch.started            # scheduler halted in recovery
    last = launcher.runs.last()
    assert last.recovery and last.clean_shutdown           # recorded recovery, exited clean


def test_force_resumes_normally_after_unclean(tmp_path):
    runs = RunLedger(tmp_path / "runs.sqlite")
    runs.open_run(commit_sha="old", dirty=False, pid=1)
    launcher, sup, watch, _q, _c = _launcher(tmp_path)
    launcher.runs = runs
    launcher.start(force=True, max_ticks=1)
    assert sup.runs == 1 and watch.started                 # --force boots normally
    assert not launcher.runs.last().recovery


# --- reset (the fresh-start wipe) ---------------------------------------------------------------
def test_reset_wipes_corpus_but_never_the_vault_raft(tmp_path):
    cfg = _cfg(tmp_path)
    # seed the corpus layer + a production Vault Raft store that MUST survive
    (cfg.paths.raw_store).mkdir(parents=True)
    (cfg.paths.raw_store / "blob").write_text("x")
    cfg.paths.vault_catalog.write_text("catalog")
    (cfg.paths.data_dir / "vault").mkdir()
    (cfg.paths.data_dir / "vault" / "raft.db").write_text("VAULT RAFT — DO NOT DELETE")
    runs = RunLedger(tmp_path / "runs.sqlite")
    launcher = Launcher(cfg=cfg, runs=runs, repo_root=Path(".").resolve())

    assert launcher.reset(confirm=False) == 0            # dry-run removes nothing
    assert cfg.paths.raw_store.exists()

    assert launcher.reset(confirm=True) == 0
    assert not cfg.paths.raw_store.exists()              # corpus wiped
    assert not cfg.paths.vault_catalog.exists()
    assert (cfg.paths.data_dir / "vault" / "raft.db").exists()   # Vault Raft UNTOUCHED


def test_reset_refused_while_a_run_is_live(tmp_path):
    import os
    cfg = _cfg(tmp_path)
    runs = RunLedger(tmp_path / "runs.sqlite")
    runs.open_run(commit_sha="x", dirty=False, pid=os.getpid())   # "live" = this process, alive
    launcher = Launcher(cfg=cfg, runs=runs, repo_root=Path(".").resolve())
    assert launcher.reset(confirm=True) == 1                       # refused — stop first


def test_stop_with_no_active_run(tmp_path):
    launcher = Launcher(cfg=_cfg(tmp_path), runs=RunLedger(tmp_path / "runs.sqlite"),
                        repo_root=Path(".").resolve())
    assert launcher.stop() == 1            # nothing to stop


def test_stop_dead_pid_is_marked_unclean(tmp_path):
    runs = RunLedger(tmp_path / "runs.sqlite")
    runs.open_run(commit_sha="x", dirty=False, pid=2_000_000_000)   # a pid that isn't alive
    launcher = Launcher(cfg=_cfg(tmp_path), runs=runs, repo_root=Path(".").resolve())
    assert launcher.stop() == 1
    assert (not runs.last().active) and not runs.last().clean_shutdown   # recorded as a crash
