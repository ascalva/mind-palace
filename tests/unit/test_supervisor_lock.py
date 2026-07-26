"""bp-108 Item 2 — the supervisor lock, in isolation (dn-supervision-and-liveness §2.6).

The mechanism that moves "two supervisors, one queue" from tier 5 (remember to probe the pid) to
tier 3 (a kernel fact). What makes that claim true is *not* testable by calling `acquire()` twice
and seeing an exception — it is testable only across a **process boundary**, so the load-bearing
test here forks.

⚑ **NAMED FALSIFIER (plan §7 Item 2): a second acquirer in the SAME process succeeds.** A test
that only exercises one process would pass while the guarantee is absent — that is the shape of
finding-0187 (deleting the mechanism left the suite green). Two independent process boundaries are
therefore used: `os.fork()` (shares everything — the hardest case, where an inherited-descriptor
mistake shows) and a fresh `sys.executable` subprocess (shares nothing — proves the refusal is not
an artifact of the fork).

The V8 measurements these encode were taken before the module was written; the commands and their
output are in `docs/build-plans/bp-108/journal.md`.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from collections.abc import Iterator
from contextlib import contextmanager, suppress
from pathlib import Path

import pytest

from ops.lifecycle.lock import SupervisorLock, SupervisorLockHeld

REPO_ROOT = Path(__file__).resolve().parents[2]

_ACQUIRED = 0
_REFUSED = 3
_UNEXPECTED = 4


@pytest.fixture
def lock_path(tmp_path: Path) -> Path:
    return tmp_path / "supervisor.lock"


# --- process-boundary helpers -------------------------------------------------------------------
def _forked_acquire(path: Path) -> int:
    """Fork; the child attempts a FRESH acquire and reports the verdict as an exit code.

    The child opens its own descriptor rather than reusing the parent's. That distinction is the
    whole test: `flock` is per-open-file-description, so an inherited fd would be the SAME lock
    (a fork shares the description) while a fresh `open()` is a genuine second claimant.
    `os._exit` skips pytest's teardown — the child must not run atexit handlers or flush the
    parent's captured output twice."""
    pid = os.fork()
    if pid == 0:                                          # ---- child
        code = _UNEXPECTED
        try:
            SupervisorLock(path).acquire()
            code = _ACQUIRED
        except SupervisorLockHeld:
            code = _REFUSED
        except BaseException:                             # noqa: BLE001 — reported as an exit code
            code = _UNEXPECTED
        os._exit(code)
    _, status = os.waitpid(pid, 0)
    return os.waitstatus_to_exitcode(status)


_SUBPROCESS_ACQUIRE = """
import sys
from pathlib import Path
from ops.lifecycle.lock import SupervisorLock, SupervisorLockHeld
try:
    SupervisorLock(Path(sys.argv[1])).acquire()
except SupervisorLockHeld:
    raise SystemExit(3)
raise SystemExit(0)
"""


def _subprocess_acquire(path: Path) -> int:
    """A wholly separate interpreter attempts the acquire — no shared memory, no shared fds."""
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT)}
    return subprocess.run([sys.executable, "-c", _SUBPROCESS_ACQUIRE, str(path)],
                          cwd=REPO_ROOT, env=env, capture_output=True, text=True).returncode


_HOLDER_MAX_HOLD_S = 60.0


@contextmanager
def _forked_holder(path: Path) -> Iterator[int]:
    """A forked child that ACQUIRES and then blocks, yielded as a pid and ALWAYS reaped.

    Three deliberate safety properties, because a leaked holder is not a mild test smell — it is
    a hang. This was learned the hard way while drilling the mutation below: a holder leaked past
    a failing assertion was reparented to init, kept pytest's inherited stdout pipe open, and any
    parent capturing that output waited on EOF forever.

    1. `finally` kills and reaps, so a failing assertion in the body cannot leak it.
    2. The child re-points fds 0/1/2 at `/dev/null` immediately after the fork, so even a leaked
       holder holds no capture pipe and can never wedge a reader.
    3. The child self-terminates after `_HOLDER_MAX_HOLD_S` — a bounded blast radius if both of
       the above are somehow defeated.
    """
    read_fd, write_fd = os.pipe()
    pid = os.fork()
    if pid == 0:                                          # ---- child
        os.close(read_fd)
        devnull = os.open(os.devnull, os.O_RDWR)          # (2) never hold the parent's pipes
        for stdio in (0, 1, 2):
            os.dup2(devnull, stdio)
        try:
            SupervisorLock(path).acquire()
        except BaseException:                             # noqa: BLE001 — reported down the pipe
            os.write(write_fd, b"X")
            os._exit(_UNEXPECTED)
        os.write(write_fd, b"H")
        deadline = time.monotonic() + _HOLDER_MAX_HOLD_S  # (3) bounded, even if never reaped
        while time.monotonic() < deadline:
            time.sleep(0.05)
        os._exit(_UNEXPECTED)
    os.close(write_fd)
    try:
        assert os.read(read_fd, 1) == b"H", "the forked holder failed to acquire"
        yield pid
    finally:                                              # (1) unconditional
        os.close(read_fd)
        with suppress(ProcessLookupError):                # already dead — a test may have killed it
            os.kill(pid, signal.SIGKILL)
        with suppress(ChildProcessError):                 # already reaped, likewise
            os.waitpid(pid, 0)


# =================================================================================================
# The falsifier: a second acquirer across a process boundary must be REFUSED
# =================================================================================================

def test_a_forked_second_acquirer_is_refused(lock_path):
    """⚑ NAMED FALSIFIER. The guarantee in one assertion: while this process holds the lock, a
    second process opening the same path is refused by the kernel."""
    lock = SupervisorLock(lock_path)
    lock.acquire()
    try:
        assert _forked_acquire(lock_path) == _REFUSED
    finally:
        lock.release()


def test_a_separate_interpreter_is_refused_too(lock_path):
    """The same claim without a shared address space — a fork could in principle refuse for the
    wrong reason (inherited state); a fresh interpreter cannot."""
    lock = SupervisorLock(lock_path)
    lock.acquire()
    try:
        assert _subprocess_acquire(lock_path) == _REFUSED
    finally:
        lock.release()


def test_the_refusal_lifts_the_moment_the_holder_releases(lock_path):
    """The complement, and the reason the refusal is not simply a broken lock: the SAME probe that
    was refused above succeeds once nothing holds the lock. Without this, a lock that always
    refused everyone would pass the falsifier above."""
    lock = SupervisorLock(lock_path)
    lock.acquire()
    assert _forked_acquire(lock_path) == _REFUSED
    lock.release()
    assert _forked_acquire(lock_path) == _ACQUIRED


# =================================================================================================
# Acquire-or-fail, never acquire-or-wait
# =================================================================================================

def test_a_contended_acquire_fails_immediately_and_does_not_wait(lock_path):
    """The invariant from plan §7 Item 2: *no busy-wait, no timeout, no retry loop* — acquisition
    is non-blocking and terminal. A supervisor that BLOCKED for the lock would be a second
    supervisor that starts the instant the first dies, which is the failure the lock exists to
    deny. The bound is deliberately loose (a whole second); a blocking implementation would hang
    here forever, not merely run slowly."""
    with _forked_holder(lock_path):
        started = time.monotonic()
        with pytest.raises(SupervisorLockHeld):
            SupervisorLock(lock_path).acquire()
        assert time.monotonic() - started < 1.0


def test_the_refusal_names_the_lockfile(lock_path):
    """An operator reading the failure must be able to find the thing that refused them — the
    message is the only diagnostic the lock itself offers (bp-105's identity gate supplies the
    rest). Raised from a genuinely-contended acquire, not a same-process one."""
    with _forked_holder(lock_path):
        with pytest.raises(SupervisorLockHeld, match=str(lock_path)):
            SupervisorLock(lock_path).acquire()


def test_a_second_lock_object_in_the_same_process_is_also_refused(lock_path):
    """Documents the measured platform behaviour that the falsifier's wording anticipates the
    other way round. This assertion must NOT be mistaken for the guarantee — it is per-open-file-
    description behaviour, and the cross-process tests above are what the tier-3 claim rests on."""
    lock = SupervisorLock(lock_path)
    lock.acquire()
    try:
        with pytest.raises(SupervisorLockHeld):
            SupervisorLock(lock_path).acquire()
    finally:
        lock.release()


# =================================================================================================
# Re-acquire, release, and the lifecycle
# =================================================================================================

def test_the_same_object_re_acquiring_is_an_explicit_error_not_a_silent_success(lock_path):
    """Plan §7 Item 2: *the same object re-acquiring is an explicit error, not a silent success.*
    And specifically NOT `SupervisorLockHeld` — that would blame another process for what is a
    caller bug (two acquisition sites, or a missing release)."""
    lock = SupervisorLock(lock_path)
    lock.acquire()
    try:
        with pytest.raises(RuntimeError, match="already held by this instance"):
            lock.acquire()
        assert not isinstance(_capture(lock), SupervisorLockHeld)
        assert lock.held                                  # the failed re-acquire is inert
    finally:
        lock.release()


def _capture(lock: SupervisorLock) -> BaseException:
    try:
        lock.acquire()
    except BaseException as e:                            # noqa: BLE001 — the object IS the assertion
        return e
    raise AssertionError("re-acquire unexpectedly succeeded")


def test_release_then_re_acquire_succeeds(lock_path):
    lock = SupervisorLock(lock_path)
    lock.acquire()
    lock.release()
    assert not lock.held
    lock.acquire()                                        # the same object, cleanly reusable
    assert lock.held
    lock.release()


def test_release_is_idempotent(lock_path):
    """Every exit path calls `release()` unconditionally rather than first asking whether it got
    far enough to acquire — so a second release must be a no-op, not a crash during shutdown."""
    lock = SupervisorLock(lock_path)
    lock.release()                                        # never acquired at all
    lock.acquire()
    lock.release()
    lock.release()
    assert not lock.held


def test_it_works_as_a_context_manager(lock_path):
    with SupervisorLock(lock_path) as lock:
        assert lock.held
        assert _forked_acquire(lock_path) == _REFUSED
    assert _forked_acquire(lock_path) == _ACQUIRED


def test_the_context_manager_releases_when_the_body_raises(lock_path):
    with pytest.raises(ValueError):
        with SupervisorLock(lock_path):
            raise ValueError("boom")
    assert _forked_acquire(lock_path) == _ACQUIRED


# =================================================================================================
# Death frees it — the property that makes "no stale-lock state" true
# =================================================================================================

def test_a_killed_holder_frees_the_lock_with_no_residue(lock_path):
    """SIGKILL is the case a pidfile cannot survive: no handler runs, no cleanup executes. The
    kernel drops the flock anyway, so there is nothing to reap and no stale state to interpret —
    which is exactly why this is tier 3 and a pidfile-plus-liveness-probe is tier 5."""
    with _forked_holder(lock_path) as holder_pid:
        assert _forked_acquire(lock_path) == _REFUSED     # genuinely held before we kill it
        os.kill(holder_pid, signal.SIGKILL)               # the manager's own reap tolerates this
        os.waitpid(holder_pid, 0)

        assert _forked_acquire(lock_path) == _ACQUIRED    # successor acquires; no cleanup needed
        lock = SupervisorLock(lock_path)
        lock.acquire()
        lock.release()


def test_release_does_not_unlink_the_lockfile(lock_path):
    """Unlinking would race: a successor may already have opened the path, and removing it would
    leave two processes flocking two different inodes under one name — two supervisors, the single
    outcome this module exists to prevent."""
    lock = SupervisorLock(lock_path)
    lock.acquire()
    inode_while_held = lock_path.stat().st_ino
    lock.release()
    assert lock_path.exists()
    assert lock_path.stat().st_ino == inode_while_held


def test_the_lockfile_carries_no_state(lock_path):
    """Deliberately no pid written into it (module docstring). A pid in the file would be a stored
    assertion outliving the actor that made it — the exact polarity §2.6 inverts."""
    with SupervisorLock(lock_path):
        assert lock_path.stat().st_size == 0


# =================================================================================================
# The descriptor must not outlive the supervisor via a child process
# =================================================================================================

def test_the_lock_descriptor_is_not_inherited_by_spawned_children(lock_path):
    """⚑ A quiet way for the guarantee to rot. `ops/lifecycle/children.py` spawns the edge monitor
    with `subprocess.Popen(argv)`; if that descriptor were inherited, a surviving child would keep
    the lock alive after the supervisor died and the successor would be locked out **forever** —
    an exclusivity guarantee turned into a permanent outage.

    Two independent reasons it cannot happen, both asserted: PEP 446 makes Python-created
    descriptors non-inheritable by default, and `Popen`'s `close_fds=True` default closes them
    across the exec. Asserting the first is what makes this a ratchet rather than a coincidence."""
    lock = SupervisorLock(lock_path)
    lock.acquire()
    try:
        assert lock._fd is not None
        assert not os.get_inheritable(lock._fd), "the lock fd must be CLOEXEC"

        # A real spawned child, exactly as `Child.start()` does it, that outlives the check.
        child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
        try:
            lock.release()                                # the supervisor "dies" here
            assert child.poll() is None                   # ...while the child is still running
            assert _forked_acquire(lock_path) == _ACQUIRED  # the successor is NOT locked out
        finally:
            child.kill()
            child.wait(timeout=10)
    finally:
        lock.release()
