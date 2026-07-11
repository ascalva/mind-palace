"""Supervised child processes (the thin-master/child model) — start/alive/stop, idempotence,
restart-on-death, and graceful SIGTERM→SIGKILL. Spawn is injected, so no real OS process runs."""

import subprocess

from ops.lifecycle.children import Child


class _FakeProc:
    def __init__(self, pid=4242):
        self.pid = pid
        self._alive = True
        self.terminated = self.killed = self.waited = False

    def poll(self):
        return None if self._alive else 0          # None = alive (Popen contract)

    def terminate(self):
        self.terminated = True
        self._alive = False

    def wait(self, timeout=None):
        self.waited = True
        return 0

    def kill(self):
        self.killed = True
        self._alive = False


def test_start_spawns_and_tracks_pid():
    procs: list[_FakeProc] = []

    def _spawn(_argv):
        proc = _FakeProc()
        procs.append(proc)
        return proc

    child = Child("monitor", ["x"], spawn=_spawn)
    child.start()
    assert child.alive() and child.pid == 4242
    child.start()                                   # idempotent — already alive, no re-spawn
    assert len(procs) == 1


def test_stop_is_graceful_then_completes():
    proc = _FakeProc()
    child = Child("monitor", ["x"], spawn=lambda _a: proc)
    child.start()
    child.stop()
    assert proc.terminated and proc.waited and not proc.killed
    assert not child.alive()


def test_stop_force_kills_on_timeout():
    class _Slow(_FakeProc):
        def wait(self, timeout=None):
            raise subprocess.TimeoutExpired(cmd="x", timeout=timeout)

    proc = _Slow()
    child = Child("monitor", ["x"], spawn=lambda _a: proc, stop_timeout_s=0.01)
    child.start()
    child.stop()
    assert proc.terminated and proc.killed          # didn't drain in time → forced


def test_restart_after_death():
    procs: list[_FakeProc] = []

    def spawn(_a):
        procs.append(_FakeProc(pid=100 + len(procs)))
        return procs[-1]

    child = Child("monitor", ["x"], spawn=spawn)
    child.start()
    procs[0]._alive = False                          # the child died
    assert not child.alive()
    child.start()                                    # supervisor restarts it
    assert child.alive() and len(procs) == 2 and child.pid == 101
