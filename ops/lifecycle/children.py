"""Supervised child processes — the thin-master/child runtime model.

palace is the always-on master; components that MUST be separate processes (the network-facing edge
monitor — Invariant 2) are spawned, liveness-checked, and gracefully SIGTERM'd by palace, which
waits for them to drain before it exits (ASG-style). The core itself stays one process (it is the
model-slot arbiter — the ceiling has a single owner); only the genuinely-separate components are
children. `spawn` is injectable so the whole lifecycle is testable without real OS processes.
"""

from __future__ import annotations

import subprocess
from collections.abc import Callable
from dataclasses import dataclass, field

# A Popen-like: .pid, .poll() (None = alive), .terminate(), .wait(timeout), .kill().
Proc = object
Spawn = Callable[[list[str]], Proc]


def _default_spawn(argv: list[str]) -> Proc:
    return subprocess.Popen(argv)


@dataclass
class Child:
    """One supervised child process. Idempotent `start` (won't double-spawn a live child); `stop`
    is graceful (SIGTERM → wait → SIGKILL on timeout) and never raises (shutdown must not crash)."""

    name: str
    argv: list[str]
    spawn: Spawn = _default_spawn
    stop_timeout_s: float = 10.0
    _proc: Proc | None = field(default=None, init=False)

    def start(self) -> None:
        if not self.alive():
            self._proc = self.spawn(self.argv)

    def alive(self) -> bool:
        return self._proc is not None and self._proc.poll() is None

    @property
    def pid(self) -> int | None:
        return getattr(self._proc, "pid", None)

    def stop(self) -> None:
        if not self.alive():
            return
        proc = self._proc
        try:
            proc.terminate()                      # SIGTERM — let it drain its own work
            proc.wait(timeout=self.stop_timeout_s)
        except subprocess.TimeoutExpired:
            try:
                proc.kill()                       # didn't drain in time — force it
            except ProcessLookupError:
                pass
        except ProcessLookupError:
            pass                                  # already gone
