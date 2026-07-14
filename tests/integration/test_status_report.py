"""Item 3 (bp-030) — enriched `status`: the running-code-vs-HEAD gap plus the read-only
`build_status` snapshot (queue depth, RAM headroom, drift, dream/tidy counts). Every shown datum
traces to `build_status`/the ledger/git; `status` reports, it never writes.
"""

import dataclasses
import os
from pathlib import Path

from config.loader import load_config
from ops.lifecycle.launcher import Launcher
from ops.lifecycle.preflight import Check, Preflight
from ops.lifecycle.runs import RunLedger


def _cfg(tmp_path):
    """All corpus/derived/ledger paths into tmp so the read-only views the snapshot opens are
    hermetic (the self-mod ledger lives on cfg.selfmod, not cfg.paths — redirect it too)."""
    base = load_config()
    paths = dataclasses.replace(
        base.paths, data_dir=tmp_path, raw_store=tmp_path / "raw",
        vector_store=tmp_path / "v.lance", vault_catalog=tmp_path / "cat.sqlite",
        derived_store=tmp_path / "d.sqlite", attestation_store=tmp_path / "att.sqlite",
        telemetry_db=tmp_path / "t.duckdb")
    selfmod = dataclasses.replace(base.selfmod, ledger_db=tmp_path / "selfmod.sqlite")
    vault = dataclasses.replace(base.vault, path=tmp_path / "vault")
    return dataclasses.replace(base, paths=paths, selfmod=selfmod, vault=vault)


def _launcher(tmp_path, runs, *, head, monkeypatch):
    # a passing preflight keeps status hermetic (no Ollama/podman contact) and fast.
    monkeypatch.setattr("ops.lifecycle.launcher.git_state", lambda _r: (head, False))
    passing = Preflight((Check("x", required=True, ok=True, detail="ok"),))
    return Launcher(cfg=_cfg(tmp_path), runs=runs, repo_root=Path(".").resolve(),
                    preflight_fn=lambda _c: passing)


def test_status_flags_running_behind_head(tmp_path, monkeypatch, capsys):
    runs = RunLedger(tmp_path / "runs.sqlite")
    runs.open_run(commit_sha="oldsha0000aa", dirty=False, pid=os.getpid())   # a live run
    launcher = _launcher(tmp_path, runs, head="newsha1111bb", monkeypatch=monkeypatch)
    assert launcher.status() == 0
    out = capsys.readouterr().out
    assert "oldsha0000aa" in out and "newsha1111bb" in out
    assert "behind" in out                            # the HEAD-gap warning fired


def test_status_reports_running_head_when_current(tmp_path, monkeypatch, capsys):
    runs = RunLedger(tmp_path / "runs.sqlite")
    runs.open_run(commit_sha="samesha0000c", dirty=False, pid=os.getpid())
    launcher = _launcher(tmp_path, runs, head="samesha0000c", monkeypatch=monkeypatch)
    assert launcher.status() == 0
    assert "running HEAD" in capsys.readouterr().out


def test_status_reports_the_snapshot_lines(tmp_path, monkeypatch, capsys):
    runs = RunLedger(tmp_path / "runs.sqlite")
    runs.open_run(commit_sha="sha", dirty=False, pid=os.getpid())
    launcher = _launcher(tmp_path, runs, head="sha", monkeypatch=monkeypatch)
    assert launcher.status() == 0
    out = capsys.readouterr().out
    for label in ("queue depth:", "memory available:", "dreams:", "drift within tolerance:"):
        assert label in out                           # every datum traces to build_status


def test_status_is_read_only(tmp_path, monkeypatch):
    runs = RunLedger(tmp_path / "runs.sqlite")
    r = runs.open_run(commit_sha="sha", dirty=False, pid=os.getpid())
    launcher = _launcher(tmp_path, runs, head="sha", monkeypatch=monkeypatch)
    launcher.status()
    launcher.status()                                 # reporting twice must not mutate state
    last = runs.last()
    assert last is not None and last.id == r.id and last.active   # no new run, no state change


def test_status_with_no_runs_yet(tmp_path, monkeypatch, capsys):
    runs = RunLedger(tmp_path / "runs.sqlite")
    launcher = _launcher(tmp_path, runs, head="sha", monkeypatch=monkeypatch)
    assert launcher.status() == 0
    assert "no runs recorded yet" in capsys.readouterr().out
