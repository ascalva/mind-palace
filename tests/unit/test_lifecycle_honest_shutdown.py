"""bp-102 Item 3 — `down`/`stop` report what they VERIFIED, never what they requested.

Observed 2026-07-25 (finding-0171): `palace down` printed

    down: booted out com.mind-palace.palace — stays down past KeepAlive. `palace up` to bring
    it back.

while pid 96950 kept running at 96% CPU and `launchctl print` still showed `active count = 1`
pending on process exit. The launchd JOB was unloaded; the PROCESS was not. Those are two facts
and the command reported only the first as if it were both.

What is in scope here is REPORTING. What is NOT — and is asserted below as an invariant — is any
escalation: SIGTERM→SIGKILL and worker-enforced job budgets are the owner's open decision
(finding-0171 (a)/(b)/(c), oq-0035). The verification window is an *observation* window; when it
elapses nothing is signalled and nothing is killed. The command simply stops lying.

A live subprocess (`sleep`) with SIGTERM ignored stands in for the wedged daemon: it is genuinely
alive, genuinely unresponsive to the graceful path, and genuinely reaped at teardown.
"""

import os
import signal
import subprocess
import sys
import threading
from pathlib import Path

import pytest

from config.loader import load_config
from ops.lifecycle.launcher import Launcher
from ops.lifecycle.runs import RunLedger

_LABEL = "com.mind-palace.palace"


class _FakeLaunchctl:
    """Models `launchctl` for our label (same shape as tests/integration/test_lifecycle_control)."""

    def __init__(self, *, managed: bool):
        self.managed = managed
        self.calls: list[list[str]] = []

    def __call__(self, argv: list[str]) -> subprocess.CompletedProcess[str]:
        self.calls.append(argv)
        verb = argv[0]
        rc = 0
        if verb == "print":
            rc = 0 if self.managed else 1
        elif verb == "bootout":
            self.managed = False           # the JOB unloads immediately; the PROCESS may not exit
        elif verb == "bootstrap":
            self.managed = True
        return subprocess.CompletedProcess(argv, rc, stdout="", stderr="")

    def verbs(self) -> list[str]:
        return [c[0] for c in self.calls]


def _reap_in_background(proc: "subprocess.Popen[bytes]") -> None:
    """Reap the child the instant it exits.

    A test artefact, not a property of the system: an unreaped child of *this* process lingers as
    a ZOMBIE, and `os.kill(zombie, 0)` succeeds — so `_pid_alive` would (correctly) still say
    alive. The real daemon's parent is launchd, which reaps immediately, so this thread simply
    reproduces production reaping inside the test."""
    threading.Thread(target=proc.wait, daemon=True).start()


@pytest.fixture
def stubborn_pid():
    """A live process that IGNORES SIGTERM — the wedged daemon, in miniature."""
    proc = subprocess.Popen(
        [sys.executable, "-c",
         "import signal, time; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(120)"])
    try:
        yield proc.pid
    finally:
        proc.kill()                        # test teardown only — the command under test never does
        proc.wait()


def _launcher(tmp_path, *, managed=True, installed=True, pid=None, verify_s=0.5):
    plist = tmp_path / "com.mind-palace.palace.plist"
    if installed:
        plist.write_text("<plist/>")
    runs = RunLedger(tmp_path / "runs.sqlite")
    if pid is not None:
        runs.open_run(commit_sha="abcdef123456", dirty=False, pid=pid)
    fake = _FakeLaunchctl(managed=managed)
    launcher = Launcher(cfg=load_config(), runs=runs, repo_root=Path(".").resolve(),
                        launchctl=fake, installed_plist=plist,
                        stop_verify_s=verify_s, stop_poll_s=0.05)
    return launcher, fake, runs


# --- down --------------------------------------------------------------------------------------
def test_down_reports_STILL_ALIVE_and_fails_when_the_process_outlives_the_bootout(
        tmp_path, capsys, stubborn_pid):
    """The 2026-07-25 case, exactly: bootout succeeds, the process does not exit."""
    launcher, fake, _ = _launcher(tmp_path, pid=stubborn_pid)
    rc = launcher.down()
    out = capsys.readouterr().out
    assert ["bootout", f"gui/{os.getuid()}/{_LABEL}"] in fake.calls   # it still DID the bootout
    assert "STILL ALIVE" in out
    assert str(stubborn_pid) in out                     # names the process, so `ps` is one step
    assert "NOT down" in out
    assert rc != 0                                      # and it does not claim success


def test_down_verifies_and_says_so_when_the_process_really_exits(tmp_path, capsys):
    """The happy path must still be reported as verified — and it must say VERIFIED, because a
    command that hedges on every outcome is as uninformative as one that never hedges. The child
    exits on its own inside the observation window; `down` never signals it."""
    proc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(0.3)"])
    _reap_in_background(proc)
    launcher, _, _ = _launcher(tmp_path, pid=proc.pid, verify_s=5.0)
    assert launcher.down() == 0
    out = capsys.readouterr().out
    assert "verified down" in out and "exited" in out
    assert "STILL ALIVE" not in out


def test_down_names_an_already_stale_ledger_row(tmp_path, capsys):
    """The state the daemon is in right now: booted out, the row still `active`, the pid long
    gone. `down` should confirm down and name the stale row — not claim it verified an exit it
    never saw, and not report a failure either."""
    launcher, _, _ = _launcher(tmp_path, pid=2 ** 22)
    assert launcher.down() == 0
    out = capsys.readouterr().out
    assert "already gone" in out and "stale ledger row" in out
    assert "verified down" in out


def test_down_with_no_live_run_says_it_verified_nothing(tmp_path, capsys):
    """No run in the ledger ⇒ nothing to verify. Say that, rather than implying a process check
    happened. (This is also the shape the existing integration tests drive.)"""
    launcher, fake, _ = _launcher(tmp_path, pid=None)
    assert launcher.down() == 0
    out = capsys.readouterr().out
    assert "no process to verify" in out.lower()
    assert ["bootout", f"gui/{os.getuid()}/{_LABEL}"] in fake.calls


def test_down_does_not_escalate(tmp_path, capsys, stubborn_pid):
    """INVARIANT (finding-0171 is an OWNER decision): the verification window is not a kill
    deadline. After `down` returns, the process must still be alive and never have been signalled
    with anything beyond what launchd itself did."""
    sent: list[tuple[int, int]] = []
    real_kill = os.kill

    launcher, _, _ = _launcher(tmp_path, pid=stubborn_pid)

    def _record(pid, sig):
        if sig != 0:                                    # signal 0 is the liveness PROBE, not a kill
            sent.append((pid, sig))
        return real_kill(pid, sig)

    original = os.kill
    os.kill = _record
    try:
        launcher.down()
    finally:
        os.kill = original
    assert sent == []                                   # no SIGTERM, no SIGKILL, nothing
    real_kill(stubborn_pid, 0)                          # still alive (this would raise if not)


def test_restart_refuses_to_bring_up_a_still_live_instance(tmp_path, capsys, stubborn_pid):
    """The double-instance hazard: bootstrapping a successor while the predecessor still runs.
    The old `down` returned 0 unconditionally, so `restart` would have done exactly that."""
    launcher, fake, _ = _launcher(tmp_path, pid=stubborn_pid)
    assert launcher.restart() != 0
    assert "bootstrap" not in fake.verbs()              # never brought a second one up
    assert "REFUSED" in capsys.readouterr().out


# --- stop --------------------------------------------------------------------------------------
def test_stop_reports_still_alive_rather_than_promising_a_clean_drain(
        tmp_path, capsys, stubborn_pid):
    """The old line — "it will drain + mark clean" — asserted a future `stop` cannot see. The
    drain has no time bound (finding-0171), so a wedged job means it never happens."""
    launcher, _, _ = _launcher(tmp_path, pid=stubborn_pid)
    assert launcher.stop() == 0                         # the signal WAS sent; that part is true
    out = capsys.readouterr().out
    assert "STILL ALIVE" in out
    assert "will drain + mark clean" not in out
    assert "ps -o" in out                               # tells the operator how to look for itself


def test_stop_confirms_an_exit_it_actually_observed(tmp_path, capsys):
    proc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
    _reap_in_background(proc)
    launcher, _, _ = _launcher(tmp_path, pid=proc.pid, verify_s=5.0)
    try:
        assert launcher.stop() == 0                     # a real SIGTERM to a real process
        out = capsys.readouterr().out
        assert "process exited" in out
        assert "STILL ALIVE" not in out
    finally:
        if proc.poll() is None:                         # only if `stop`'s SIGTERM did not land
            proc.kill()


def test_stop_closes_a_stale_ledger_row_for_a_dead_pid(tmp_path, capsys):
    """The finding-0172 row, from the other side: `stop` on a run whose process is already gone
    must mark it unclean rather than signalling into the void."""
    launcher, _, runs = _launcher(tmp_path, pid=2 ** 22)
    assert launcher.stop() == 1
    assert "was not alive" in capsys.readouterr().out
    last = runs.last()
    assert last is not None and not last.active and not last.clean_shutdown


def test_stop_with_no_active_run(tmp_path, capsys):
    launcher, _, _ = _launcher(tmp_path, pid=None)
    assert launcher.stop() == 1
    assert "no active run to stop." in capsys.readouterr().out


def test_signal_zero_is_a_probe_not_a_signal():
    """Documents the primitive `down`/`stop` lean on: `os.kill(pid, 0)` delivers nothing. If this
    were ever a real signal, the liveness check would itself be an intervention."""
    os.kill(os.getpid(), 0)                 # delivers nothing; raises only if the pid is gone
    assert signal.SIGTERM != 0              # a real signal is never 0, so a probe cannot be one
