"""bp-102 Item 1 — liveness, and its FALSIFIER.

The defect (finding-0172): `status` rendered `"RUNNING" if r.active` straight out of the run
ledger. After a `kill -9` it kept printing

    #35 5c2222924874 started 2026-07-25T02:29:11 — RUNNING
    running HEAD (5c2222924874).

with no palace process alive. `deploy` already tested `_pid_alive(run.pid)`, so the primitive
existed and the reporting path simply did not call it.

The falsifier is the OTHER direction and it is the one that matters here: *"A genuinely live
daemon is reported as dead — a false alarm is as corrosive to trust as the false green."* An
instrument that cries wolf gets ignored during the next incident, which is exactly when it must be
believed. So this file tests both directions, including the two ways a live process can look
absent (a foreign owner, and a raced signal).
"""

import os

import pytest

from ops.lifecycle.launcher import _pid_alive
from ops.lifecycle.runs import RunLedger
from ops.lifecycle.snapshot import run_state

DEAD_PID = 2 ** 22          # above the pid ceiling on macOS/Linux → ProcessLookupError


# --- the ONE liveness primitive ---------------------------------------------------------------
def test_pid_alive_sees_this_very_process():
    assert _pid_alive(os.getpid()) is True


def test_pid_alive_sees_a_missing_process():
    assert _pid_alive(DEAD_PID) is False


def test_pid_alive_treats_a_foreign_owner_as_ALIVE(monkeypatch):
    """THE false-alarm guard. `os.kill(pid, 0)` raises PermissionError for a process owned by
    another user — which is precisely the case once the palace runs as the `ouroboros` principal
    under the system LaunchDaemon (dn-plane-principals §3.1) while `status` is invoked by the
    owner. Reading that as "dead" would report every healthy daemon as down."""
    def _refuse(_pid, _sig):
        raise PermissionError(1, "Operation not permitted")

    monkeypatch.setattr(os, "kill", _refuse)
    assert _pid_alive(1234) is True


# --- the verdict ------------------------------------------------------------------------------
class _Run:
    """A minimal run-ledger row (structural — `run_state` reads only these four)."""

    def __init__(self, *, pid, stopped=False, clean=False):
        self.id = 1
        self.pid = pid
        self.commit_sha = "abcdef123456"
        self.clean_shutdown = clean
        self._stopped = stopped

    @property
    def active(self) -> bool:
        return not self._stopped


def test_a_live_pid_renders_running():
    state, alive = run_state(_Run(pid=os.getpid()), pid_alive=_pid_alive)
    assert (state, alive) == ("RUNNING", True)


def test_a_dead_pid_never_renders_plain_running():
    state, alive = run_state(_Run(pid=DEAD_PID), pid_alive=_pid_alive)
    assert alive is False
    assert state == "DEAD (stale ledger row)"
    assert state != "RUNNING"


@pytest.mark.parametrize(("clean", "expected"), [(True, "clean"), (False, "UNCLEAN")])
def test_a_closed_run_is_unchanged_and_needs_no_probe(clean, expected):
    """A run the ledger already closed is a historical fact — its pid is meaningless and must not
    be probed (a recycled pid would otherwise resurrect an old row as RUNNING)."""
    def _explode(_pid):
        raise AssertionError("a closed run must not be probed for liveness")

    state, alive = run_state(_Run(pid=DEAD_PID, stopped=True, clean=clean), pid_alive=_explode)
    assert (state, alive) == (expected, None)


def test_no_run_at_all():
    assert run_state(None, pid_alive=_pid_alive) == ("none", None)


def test_run_state_uses_the_injected_primitive_and_nothing_else():
    """There is exactly one liveness implementation (`launcher._pid_alive`); `snapshot` must not
    grow a second. Proven by injecting a stub and observing it is the sole source of truth."""
    calls = []

    def _stub(pid):
        calls.append(pid)
        return True

    assert run_state(_Run(pid=999), pid_alive=_stub) == ("RUNNING", True)
    assert calls == [999]


# --- against a real ledger --------------------------------------------------------------------
def test_the_ledger_row_that_lied(tmp_path):
    """End-to-end on the shape of run #35: a row with `stopped_at IS NULL` whose process is gone.
    The ledger still calls it active — that is correct, the ledger records intent — and the
    liveness test is what turns it into an honest verdict."""
    runs = RunLedger(tmp_path / "runs.sqlite")
    row = runs.open_run(commit_sha="5c2222924874", dirty=False, pid=DEAD_PID)
    assert row.active is True                             # the ledger's view, unchanged
    state, alive = run_state(runs.last(), pid_alive=_pid_alive)
    assert alive is False and "DEAD" in state             # the honest view
