"""The supervisor lock — the supervisor ROLE is kernel-exclusive (dn-supervision-and-liveness §2.6).

An OS-exclusive `flock` on a lockfile beside the queue, acquired before `sweep_orphans` and held
for the supervisor's lifetime. This is the mechanism that moves "two supervisors, one queue" from
**tier 5** (remember to check the pid) to **tier 3** (a kernel fact) on the note's enforcement
ladder, and it is what structurally closes finding-0186's open half: a second claimant fails to
acquire *whatever entrypoint built it* — `palace start`, `start --force`, or `scripts/watch.py`.

Two properties earn the tier, and both were measured on this platform before the module was
written (bp-108 Item 1 / V8; commands and output in `docs/build-plans/bp-108/journal.md`):

* **Held-or-not is a kernel fact, so no stale-lock state exists.** The kernel drops the lock when
  the holding process dies, however it dies. Measured: `kill -9` on the holder frees it in 17 ms
  with nothing to clean up. The zero-byte file left behind carries no state — it is a name for the
  lock, not a record of it. Contrast a pidfile, which *is* stale state and needs a liveness probe
  to interpret; that probe is exactly the tier-5 mechanism this replaces.
* **Acquisition is atomic — no check-then-act.** bp-105's identity gate (`launcher.py`'s
  `_supervisor_alive`) probes and then proceeds, a TOCTOU window in which a second start can slip
  through. `flock(LOCK_EX | LOCK_NB)` has no window: the kernel either grants or refuses.

**Acquire-or-fail, never acquire-or-wait.** A supervisor that blocks waiting for the lock is a
second supervisor that starts the instant the first dies — precisely the failure the lock exists
to deny. Hence `LOCK_NB` and a raise: no busy-wait, no timeout, no retry loop.

**What it does NOT guard: queue writes.** The lock covers the supervisor role (sweep + claim), not
the queue. CLI enqueues (`palace code-seed`) legitimately insert concurrently and stay lock-free
under WAL; a lock spanning enqueues would break them (§2.6, and bp-108 §9).

**Deliberately no pid in the file.** Writing the holder's pid would be handy diagnostics and would
also reintroduce the thing this mechanism removes: a stored assertion that outlives the actor that
made it. The "which run is live, and why" answer stays with bp-105's identity gate — the layer
that *explains*, sitting ahead of the layer that *guarantees*.
"""

from __future__ import annotations

import fcntl
import os
from dataclasses import dataclass, field
from pathlib import Path


class SupervisorLockHeld(RuntimeError):
    """Another process holds the supervisor role."""


@dataclass
class SupervisorLock:
    """An acquire-or-fail exclusive lock on `path`, held for the process lifetime.

    `path` is `cfg.paths.data_dir / "supervisor.lock"` — beside the queue it guards, never in the
    repo (which would scope exclusion to a *checkout*, so two worktrees over one data dir would
    both start) and never in `/tmp` (cleared by the OS, and not co-located with the resource).
    """

    path: Path
    _fd: int | None = field(default=None, init=False, repr=False)

    @property
    def held(self) -> bool:
        """True while THIS instance holds the lock. Not a probe of the file — a lock held by some
        other process is not observable here, and deliberately so: the only question this object
        can answer honestly is whether it is the holder."""
        return self._fd is not None

    def acquire(self) -> None:
        """Take the lock, or raise. Never blocks.

        The fd is kept on the instance and never closed except by `release()` or process death —
        the kernel drops it either way, so there is no stale-lock state and nothing to clean up
        after a crash.

        Raises:
            SupervisorLockHeld: another process holds it.
            RuntimeError: this instance already holds it. Re-acquiring is a caller bug (two
                acquisition sites, or a missing release), and it must not pass silently: `flock`
                is per-open-file-description, so a naive re-open would ALSO be refused by the
                kernel (measured: `errno 35` even within one process), and reporting that as
                "another process holds it" would be a lie about which process is at fault.
        """
        if self._fd is not None:
            raise RuntimeError(f"supervisor lock {self.path} is already held by this instance")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(self.path, os.O_CREAT | os.O_RDWR, 0o644)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as e:      # EWOULDBLOCK/EAGAIN (errno 35 on darwin) — someone else holds it
            os.close(fd)          # do not leak the descriptor on a refused acquire
            raise SupervisorLockHeld(
                f"another process holds the supervisor lock {self.path}") from e
        self._fd = fd

    def release(self) -> None:
        """Drop the lock. Idempotent — releasing an unheld lock is a no-op, so every exit path can
        call it unconditionally without first asking whether it got that far.

        The lockfile itself is deliberately NOT unlinked. Unlinking races: a successor may already
        have opened the same path, and removing it out from under them would leave two processes
        holding flocks on two different inodes with the same name — two supervisors, which is the
        one outcome this module exists to prevent."""
        fd, self._fd = self._fd, None
        if fd is None:
            return
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)          # closing alone would release it; the explicit LOCK_UN documents

    def __enter__(self) -> SupervisorLock:
        self.acquire()
        return self

    def __exit__(self, *exc: object) -> None:
        self.release()
