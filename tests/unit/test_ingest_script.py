"""`scripts/ingest.py` beside a live daemon (dn-ingest-door §9; DOR-12's one writer).

The script rebuilds the knowledge base, and its first act is `VectorStore.reset()`, which drops the
table and every relation the daemon writes: a write that commutes with none of the daemon's. So it
refuses while a daemon run is live, through the launcher's `_refuse_if_live`, as the on-demand
verbs do, and it holds the supervisor lock for the rebuild's duration, so no daemon can start
while it runs: the check alone would leave a window between it and the reset."""

from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from core.ingest import run as ingest_run
from ops.lifecycle import launcher as launcher_mod
from ops.lifecycle.launcher import Launcher
from ops.lifecycle.lock import SupervisorLock, SupervisorLockHeld
from ops.lifecycle.runs import RunLedger
from scripts import ingest as ingest_script


def _launcher(runs: RunLedger, data_dir: Path) -> Any:
    """The launcher's live check over a real run ledger, without the rest of a launcher."""
    stub = SimpleNamespace(runs=runs, cfg=SimpleNamespace(paths=SimpleNamespace(data_dir=data_dir)))
    stub._refuse_if_live = lambda what: Launcher._refuse_if_live(stub, what)  # type: ignore[arg-type]
    return stub


@pytest.fixture
def rebuilds(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> list[bool]:
    """Each rebuild the script starts, and whether the supervisor lock was held while it ran."""
    calls: list[bool] = []

    def run_ingest(*args: Any, **kwargs: Any) -> str:
        try:
            with SupervisorLock(tmp_path / "supervisor.lock"):
                calls.append(False)       # a daemon could have started beside the rebuild
        except SupervisorLockHeld:
            calls.append(True)
        return "summary"
    monkeypatch.setattr(ingest_script, "seal", lambda: None)
    monkeypatch.setattr(ingest_run, "run_ingest", run_ingest)
    return calls


def test_the_rebuild_refuses_while_a_daemon_run_is_live(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, rebuilds: list[bool],
        capsys: pytest.CaptureFixture[str]) -> None:
    runs = RunLedger(tmp_path / "runs.sqlite")
    run = runs.open_run(commit_sha="abc", dirty=False, pid=os.getpid())   # live: this process
    monkeypatch.setattr(launcher_mod, "build_launcher", lambda *a, **k: _launcher(runs, tmp_path))
    assert ingest_script.main() == 1
    assert rebuilds == [], "nothing reset, nothing rebuilt"
    assert f"run #{run.id}" in capsys.readouterr().out

    runs.mark_stopped(run.id, clean=True)          # the control: no live run, so it rebuilds
    assert ingest_script.main() == 0
    assert rebuilds == [True], "...holding the supervisor lock while it does"


def test_the_rebuild_refuses_while_another_process_holds_the_supervisor_lock(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, rebuilds: list[bool]) -> None:
    """A supervisor that started after the run ledger was read holds the lock: the rebuild does
    not reset beside it."""
    runs = RunLedger(tmp_path / "runs.sqlite")
    monkeypatch.setattr(launcher_mod, "build_launcher", lambda *a, **k: _launcher(runs, tmp_path))
    with SupervisorLock(tmp_path / "supervisor.lock"):
        assert ingest_script.main() == 1
    assert rebuilds == []
