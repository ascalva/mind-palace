"""bp-105 — the restart is trustworthy: a fail-closed `start`, a covered sweep, a live instrument.

Three named falsifiers from three audit findings, in the plan's blast-radius order:

* **Item 2 / finding-0186** — a second `start` over a live supervisor reclaims the first's
  in-flight rows (double execution + a falsified FAILED row). It must refuse, and `--force` must
  not bypass. The equally-required trap: a **recycled pid must not brick start forever**.
* **Item 3 / finding-0187** — `launcher.py`'s `sweep_orphans` call had zero coverage: deleting it
  left 85/85 green. Driven here against a **real `JobQueue`**, not `_FakeQueue`.
* **Item 1 / finding-0188** — a healthy backfill and a wedged one rendered IDENTICALLY. Both
  states are constructed and the renders must DIFFER.
"""

import dataclasses
import os
import sqlite3
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

import psutil  # type: ignore[import-untyped]  # untyped upstream; same warrant as launcher.py
import pytest

from config.loader import load_config
from ops.lifecycle.launcher import (
    Components,
    Launcher,
    _process_identity,
    _supervisor_alive,
)
from ops.lifecycle.lock import SupervisorLock, SupervisorLockHeld
from ops.lifecycle.preflight import Check, Preflight
from ops.lifecycle.runs import RunLedger, RunRecord
from ops.lifecycle.snapshot import store_idle_seconds
from scheduler.queue import RUNNING, JobQueue

DEAD_PID = 2 ** 22          # above the pid ceiling → ProcessLookupError → not alive


def _cfg(tmp_path):
    """Every store path into tmp so nothing here can touch the live data dir."""
    base = load_config()
    paths = dataclasses.replace(
        base.paths, data_dir=tmp_path, raw_store=tmp_path / "raw",
        vector_store=tmp_path / "v.lance", vault_catalog=tmp_path / "cat.sqlite",
        derived_store=tmp_path / "d.sqlite", attestation_store=tmp_path / "att.sqlite",
        telemetry_db=tmp_path / "t.duckdb")
    selfmod = dataclasses.replace(base.selfmod, ledger_db=tmp_path / "selfmod.sqlite")
    ingestion = dataclasses.replace(
        base.ingestion,
        vault=dataclasses.replace(base.ingestion.vault, path=tmp_path / "vault"))
    return dataclasses.replace(base, paths=paths, selfmod=selfmod, ingestion=ingestion)


class _FakeSupervisor:
    def __init__(self):
        self.runs = 0
        self.max_ticks_seen: list[int | None] = []

    def run(self, *, max_ticks=None):     # bp-108 Item 4 widened the call site to the real shape
        self.runs += 1
        self.max_ticks_seen.append(max_ticks)
        return 0                          # 0 dispatched = nothing runnable


def _launcher(tmp_path, runs, *, queue=None, monkeypatch=None, **kw):
    """A Launcher whose preflight always passes, so a refusal can only come from the gate."""
    probes = {"preflight": 0}

    def _pf(_cfg_):
        probes["preflight"] += 1
        return Preflight((Check("x", required=True, ok=True, detail="ok"),))

    comps = Components(supervisor=_FakeSupervisor(), watchers=[],
                       queue=queue if queue is not None else _NullQueue())
    if monkeypatch is not None:
        monkeypatch.setattr("ops.lifecycle.launcher.git_state", lambda _r: ("abc123456789", False))
    launcher = Launcher(
        cfg=_cfg(tmp_path), runs=runs, repo_root=Path(".").resolve(),
        components_factory=lambda _c: comps, preflight_fn=_pf,
        tick_seconds=0, health_interval_s=0, **kw)
    return launcher, probes


class _NullQueue:
    def close(self):
        pass

    def sweep_orphans(self, active_run_id):
        return _Swept(active_run_id)


class _Swept:
    def __init__(self, run_id):
        self.run_id = run_id

    def render(self):
        return f"orphan sweep: nothing stranded (run #{self.run_id})"


# =================================================================================================
# Item 2 — `start` refuses on an identity-confirmed live supervisor (warrant finding-0186)
# =================================================================================================

# --- the identity primitive, in isolation ------------------------------------------------------
def _Run(*, pid: int, started_at: str | None = None) -> RunRecord:  # noqa: N802 — reads as a type
    """A real `RunRecord`, not a stand-in. `_supervisor_alive` reads only `pid` and `started_at`,
    but constructing the genuine row keeps the production signature strictly typed — a structural
    fake would have forced `_supervisor_alive` to widen to `Any` to satisfy the type gate."""
    return RunRecord(
        id=7, commit_sha="abcdef123456", dirty=False, pid=pid,
        started_at=started_at or datetime.now(UTC).replace(
            tzinfo=None).isoformat(timespec="seconds"),
        stopped_at=None, clean_shutdown=False, recovery=False, note="")


def _ident(created=None, name=None):
    return lambda _pid: (created, name)


def _alive(_pid):
    """Pin pid-existence True so each test below isolates the IDENTITY half of the verdict — the
    fixtures use pids the host does not have, and `_pid_alive` would short-circuit on them."""
    return True


def _epoch(iso: str) -> float:
    return datetime.fromisoformat(iso).replace(tzinfo=UTC).timestamp()


def test_a_dead_pid_is_not_a_live_supervisor():
    """The cheap exit: no process, no gate. `--force` is moot — there is nothing to protect."""
    assert _supervisor_alive(_Run(pid=DEAD_PID), identity=_ident()) is False


def test_this_very_process_reads_as_a_live_supervisor():
    """The end-to-end positive against the real probe: a python process alive now, with a run row
    opened now, is exactly the shape of a genuine live supervisor — and must refuse."""
    assert _supervisor_alive(_Run(pid=os.getpid())) is True


def test_a_genuine_supervisor_predates_its_own_run_row_and_still_refuses():
    """⚑ finding-0198, the inverted-rule regression guard.

    `start()` stamps `pid=os.getpid()` from inside itself, so the supervisor ALWAYS exists before
    the row it writes. The plan pinned "created BEFORE its own run row ⇒ not the supervisor",
    which would return False here — a guard that never fires on the case it exists for. Nail the
    correct direction down: predating the row is the NORMAL case and must still refuse."""
    row = _Run(pid=1234, started_at="2026-07-25T12:00:00")
    created = _epoch("2026-07-25T11:58:30")          # spawned 90 s before the row: slow preflight
    assert _supervisor_alive(row, pid_alive=_alive, identity=_ident(created, "python3.13")) is True


def test_a_recycled_pid_does_not_brick_start():
    """⚑ NAMED FALSIFIER B — the trap. A process that POSTDATES the row cannot have written it
    (the row already existed), so identity is positively disproven and start must proceed. Without
    this, a fail-closed gate keyed on pid existence refuses forever, and under launchd KeepAlive
    that is a self-inflicted brick with `--force` — the flag being closed — as the only escape."""
    row = _Run(pid=1234, started_at="2026-07-25T12:00:00")
    created = _epoch("2026-07-25T14:30:00")          # 2.5 h later — a different process entirely
    assert _supervisor_alive(row, pid_alive=_alive, identity=_ident(created, "python3.13")) is False


def test_a_pid_recycled_onto_a_long_lived_system_process_does_not_brick_start():
    """The recycle D1 cannot see: the pid counter wrapped onto `launchd`/`systemd`, which PREDATES
    the row like a genuine supervisor does. Identity is still positively disproven — the supervisor
    is always a python process (`palace.plist` runs `uv run scripts/palace.py start`)."""
    row = _Run(pid=1, started_at="2026-07-25T12:00:00")
    created = _epoch("2026-07-09T04:36:50")          # boot time, 16 days earlier
    assert _supervisor_alive(row, pid_alive=_alive, identity=_ident(created, "launchd")) is False


def test_whole_second_truncation_does_not_read_as_a_recycled_pid():
    """`runs.py` writes `started_at` at timespec='seconds', so a supervisor that opened its row
    0.3 s after spawning measures as created AFTER it. Without slack that genuine supervisor reads
    as recycled and the gate silently stops protecting anything."""
    row = _Run(pid=1234, started_at="2026-07-25T12:00:00")
    created = _epoch("2026-07-25T12:00:00") + 0.9    # inside the truncation window
    assert _supervisor_alive(row, pid_alive=_alive, identity=_ident(created, "Python")) is True


@pytest.mark.parametrize(("created", "name"), [
    (None, None),                       # both unreadable (psutil.Process raised)
    (None, "python3.13"),               # create_time denied
    (_epoch("2026-07-25T11:00:00"), None),   # name denied — the foreign-owner case
])
def test_ambiguity_refuses(created, name):
    """The owner ruling, applied: identity that cannot be established REFUSES. Refusing wrongly is
    recoverable (`palace stop` closes the row even when the process is gone, launcher.py:818-822);
    starting wrongly rewrites a live worker's rows."""
    row = _Run(pid=1234, started_at="2026-07-25T12:00:00")
    assert _supervisor_alive(row, pid_alive=_alive, identity=_ident(created, name)) is True


def test_an_unparseable_started_at_refuses():
    """D1 needs the row's timestamp. Garbage in it is ambiguity, not a licence to proceed."""
    row = _Run(pid=1234, started_at="not-a-timestamp")
    assert _supervisor_alive(row, pid_alive=_alive, identity=_ident(1.0, "python3.13")) is True


# --- the identity PROBE itself, against a faked psutil (warrant finding-0211) -------------------
#
# ⚑ Every test above INJECTS `identity`, so none of them reaches `_process_identity` — and that
# is exactly where the platform bug lived. `name()` answers "what is this process's comm/argv0
# basename?", which varies with HOW the interpreter was invoked: on the Linux runner a
# `uv run pytest` process reads as the console script, with no "python" in it, so D2 disproved a
# live interpreter and CI was red for 55 consecutive pushes while the same file was 32-passed
# locally. The host cannot be made to have the other platform's shape, so the probe is driven
# against a faked `psutil.Process` — pinning the shape rather than the host is what makes this
# unable to regress silently on *either* platform.

_ROW_AT = "2026-07-25T12:00:00"
_PREDATES = _epoch("2026-07-25T11:58:30")     # 90 s before the row: the genuine-supervisor shape


class _FakeProc:
    """A `psutil.Process` stand-in. `None` for `exe`/`name` means that accessor RAISES — the
    unreadable case (`AccessDenied` against a foreign owner), which is the branch the fallback
    exists for and which no injected-tuple test can reach."""

    def __init__(self, *, exe: str | None, name: str | None, created: float):
        self._exe, self._name, self._created = exe, name, created

    def create_time(self) -> float:
        return self._created

    def exe(self) -> str:
        if self._exe is None:
            raise PermissionError("psutil.AccessDenied")
        return self._exe

    def name(self) -> str:
        if self._name is None:
            raise PermissionError("psutil.AccessDenied")
        return self._name


def _fake_psutil(monkeypatch, **kw) -> None:
    """Patch `Process` on the REAL psutil module. `_process_identity` imports psutil lazily inside
    its own body (warrant finding-0198), so it resolves the attribute at call time and the patch
    lands without replacing the module."""
    monkeypatch.setattr(psutil, "Process", lambda _pid: _FakeProc(**kw))


def _probed(pid: int, started_at: str = _ROW_AT) -> bool:
    """`_supervisor_alive` over the REAL probe — the composition the injected tests skip."""
    return _supervisor_alive(_Run(pid=pid, started_at=started_at),
                             pid_alive=_alive, identity=_process_identity)


def test_a_console_script_invocation_still_reads_as_a_python_interpreter(monkeypatch):
    """⚑ NAMED FALSIFIER (finding-0211) — the regression pin, and the shape that broke CI.

    `uv run pytest` on Linux leaves a real CPython interpreter whose `name()` is the console
    script. Probing that, D2 positively disproves a *live* supervisor — fail-OPEN on a
    fail-closed guard, which is finding-0186's hazard reintroduced by a probe choice. The
    executed binary is what D2 is actually asking about.

    Verified RED against the pre-change probe before the fix landed (journal, Checkpoint 1)."""
    _fake_psutil(monkeypatch, exe="/home/runner/work/mind-palace/.venv/bin/python3.13",
                 name="pytest", created=_PREDATES)
    assert _probed(1234) is True


def test_an_unreadable_exe_falls_back_to_the_invocation_name(monkeypatch):
    """The fallback is load-bearing, not defensive padding. On Linux `/proc/<pid>/exe` is
    unreadable for a foreign owner while `name()` reads fine, and a stale pid recycled onto
    `systemd` is precisely finding-0186's brick trap: drop the fallback and D2 goes unavailable
    there, the verdict is ambiguous, and a fail-closed `start` refuses forever."""
    _fake_psutil(monkeypatch, exe=None, name="systemd", created=_epoch("2026-07-09T04:36:50"))
    assert _probed(1) is False


def test_an_empty_exe_is_treated_as_unreadable_not_as_an_answer(monkeypatch):
    """psutil reports `''` — not a raise — when a process's executable cannot be determined. An
    empty string is evidence of nothing, and taking it as the answer makes D2 fire on every such
    process (mutation: drop the emptiness guard and this goes False)."""
    _fake_psutil(monkeypatch, exe="", name="python3.13", created=_PREDATES)
    assert _probed(1234) is True


def test_both_probes_unreadable_still_refuses(monkeypatch):
    """finding-0186's ruling at the probe layer this time: `exe()` AND `name()` denied is
    ambiguity, and ambiguity REFUSES. The fallback must not become a permissive shortcut."""
    _fake_psutil(monkeypatch, exe=None, name=None, created=_PREDATES)
    assert _probed(1234) is True


def test_an_unconstructable_process_is_ambiguity_not_a_crash(monkeypatch):
    """`psutil.Process(pid)` itself raising (a vanished process) must degrade to (None, None) —
    the probe is on `start`'s critical path and may never be the thing that kills it."""
    def _boom(_pid):
        raise psutil.NoSuchProcess(_pid)

    monkeypatch.setattr(psutil, "Process", _boom)
    assert _process_identity(1234) == (None, None)
    assert _probed(1234) is True


# --- the gate, in `start()` --------------------------------------------------------------------
def test_start_refuses_over_a_live_supervisor_without_opening_a_run_or_sweeping(
        tmp_path, monkeypatch, capsys):
    """⚑ NAMED FALSIFIER A — the hazard itself. The audit's scenario: run A is live, run B starts
    and its sweep reclaims A's in-flight rows. Assert B never gets far enough to do it."""
    runs = RunLedger(tmp_path / "runs.sqlite")
    live = runs.open_run(commit_sha="abc123456789", dirty=False, pid=os.getpid())
    queue = _NullQueue()
    swept: list[int] = []

    def _record_sweep(_self, run_id):
        swept.append(run_id)
        return _Swept(run_id)

    monkeypatch.setattr(_NullQueue, "sweep_orphans", _record_sweep)
    launcher, probes = _launcher(tmp_path, runs, queue=queue, monkeypatch=monkeypatch)

    assert launcher.start(max_ticks=1) == 1
    out = capsys.readouterr().out
    assert f"refusing to start — run #{live.id}" in out
    assert "palace stop" in out
    assert swept == []                                  # the sweep never ran
    still = runs.last()
    assert still is not None and still.id == live.id    # no second run row was opened
    assert probes["preflight"] == 0                     # refused BEFORE preflight's 120 s probe


def test_force_does_not_bypass_the_single_instance_gate(tmp_path, monkeypatch, capsys):
    """⚑ THE INVARIANT. `--force` overrides *preflight*, not *safety*: a live supervisor is an
    unrunnable state, and the whole point of the ruling is that the operator cannot flag past it."""
    runs = RunLedger(tmp_path / "runs.sqlite")
    live = runs.open_run(commit_sha="abc123456789", dirty=False, pid=os.getpid())
    launcher, _ = _launcher(tmp_path, runs, monkeypatch=monkeypatch)

    assert launcher.start(force=True, max_ticks=1) == 1
    assert f"refusing to start — run #{live.id}" in capsys.readouterr().out
    still = runs.last()
    assert still is not None and still.id == live.id


def test_start_proceeds_when_the_previous_run_is_genuinely_dead(tmp_path, monkeypatch):
    """The false-alarm guard for the gate: an unclean exit whose process is gone must still start
    (in recovery mode). A gate that cannot tell dead from live is a brick, not a guard."""
    runs = RunLedger(tmp_path / "runs.sqlite")
    runs.open_run(commit_sha="old000000000", dirty=False, pid=DEAD_PID)
    launcher, probes = _launcher(tmp_path, runs, monkeypatch=monkeypatch)

    assert launcher.start(max_ticks=1) == 0
    assert probes["preflight"] == 1
    last = runs.last()
    assert last is not None and last.recovery and last.clean_shutdown


def test_the_recovery_message_no_longer_prescribes_start_force(tmp_path, monkeypatch, capsys):
    """finding-0186's tail: the recovery banner printed `start --force` as the way out. With the
    gate in place that is now a wall — this run is itself live — so it must say `palace stop`."""
    runs = RunLedger(tmp_path / "runs.sqlite")
    runs.open_run(commit_sha="old000000000", dirty=False, pid=DEAD_PID)
    launcher, _ = _launcher(tmp_path, runs, monkeypatch=monkeypatch)

    assert launcher.start(max_ticks=1) == 0
    out = capsys.readouterr().out
    assert "recovery mode:" in out
    assert "`palace stop`" in out
    assert "will NOT get you out" in out


# =================================================================================================
# Item 3 — the sweep call is covered, against a REAL JobQueue (warrant finding-0187)
# =================================================================================================

def _strand_a_running_row(path: Path, *, kind: str) -> int:
    """Seed a row the way a dead run leaves one: RUNNING, stamped by a run id that is not ours.

    Written with raw SQL through the real schema rather than `JobQueue.claim()` — claim() would
    stamp it with THIS queue's `active_run_id`, which is the one value the sweep must ignore."""
    q = JobQueue(path)
    job = q.enqueue(kind, "router", 8192)
    q.close()
    conn = sqlite3.connect(path)
    conn.execute("UPDATE jobs SET state = ?, claimed_by_run = ? WHERE id = ?",
                 [RUNNING, 999, job.id])
    conn.commit()
    conn.close()
    return job.id


class _RecordingQueue(JobQueue):
    """A real `JobQueue` that remembers the ORDER of sweep vs claim. Subclassed, not faked: the
    defect finding-0187 names is that every `Components(...)` in the suite passed a fake, so the
    launcher's one integration point was never driven against the real thing."""

    def __post_init__(self):
        super().__post_init__()
        self.trace: list[str] = []

    def sweep_orphans(self, active_run_id):
        self.trace.append(f"sweep:{active_run_id}")
        return super().sweep_orphans(active_run_id)

    def claim(self, **kw):
        self.trace.append("claim")
        return super().claim(**kw)


def _read_job(path: Path, job_id: int) -> sqlite3.Row:
    """Read a row back AFTER `start()` — `_shutdown` closes the queue handle it was given
    (`launcher.py:610-614`), so the assertions cannot go through the same object."""
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        return conn.execute("SELECT * FROM jobs WHERE id = ?", [job_id]).fetchone()
    finally:
        conn.close()


@pytest.fixture
def real_queue(tmp_path):
    path = tmp_path / "queue.sqlite"
    job_id = _strand_a_running_row(path, kind="vault_sync")
    yield _RecordingQueue(path), job_id


def _serving_launcher(tmp_path, runs, queue, monkeypatch):
    """A launcher whose supervisor actually claims, so sweep-vs-claim ordering is observable."""
    class _ClaimingSupervisor:
        def __init__(self):
            self.runs = 0

        def run(self, *, max_ticks=None):   # bp-108 Item 4 — the real `run` shape
            self.runs += 1
            claimed = queue.claim()
            return 1 if claimed is not None else 0

    comps = Components(supervisor=_ClaimingSupervisor(), watchers=[], queue=queue)
    monkeypatch.setattr("ops.lifecycle.launcher.git_state", lambda _r: ("abc123456789", False))
    passing = Preflight((Check("x", required=True, ok=True, detail="ok"),))
    return Launcher(cfg=_cfg(tmp_path), runs=runs, repo_root=Path(".").resolve(),
                    components_factory=lambda _c: comps, preflight_fn=lambda _c: passing,
                    tick_seconds=0, health_interval_s=0)


def test_start_sweeps_a_stranded_row_against_a_real_queue(tmp_path, real_queue, monkeypatch):
    """⚑ NAMED FALSIFIER — deleting `launcher.py`'s `sweep_orphans` call left the suite green
    (85/85), because `Launcher.start()` was never exercised against a real `JobQueue`. This test
    must fail when the line is deleted, when the run id is wrong, and when it moves after
    `_serve()`. All three are asserted below."""
    queue, job_id = real_queue
    runs = RunLedger(tmp_path / "runs.sqlite")
    launcher = _serving_launcher(tmp_path, runs, queue, monkeypatch)

    assert launcher.start(max_ticks=1) == 0
    opened = runs.last()
    assert opened is not None
    run_id = opened.id

    # (1) DELETED — the stranded row is reclaimed. `vault_sync` is idempotent, so it re-queues,
    # and this run's first claim then takes it (which is why `claimed_by_run` is THIS run, not
    # NULL — the reclaim-then-claim sequence is the whole point of the ordering).
    reclaimed = _read_job(queue.path, job_id)
    assert reclaimed["state"] == "running"
    assert reclaimed["claimed_by_run"] == run_id

    # (2) WRONG RUN ID — the sweep must adopt THIS run's id, not any id. Without adoption
    # `claimed_by_run` stays NULL forever and the next sweep has nothing to key on.
    assert f"sweep:{run_id}" in queue.trace
    assert queue.active_run_id == run_id

    # (3) MOVED AFTER `_serve()` — the sweep must precede the first claim, which is the entire
    # safety argument (`scheduler/queue.py:357`). Ordering, not mere presence.
    assert queue.trace.index(f"sweep:{run_id}") < queue.trace.index("claim")


def test_the_swept_row_is_reclaimed_before_it_can_be_claimed_by_this_run(tmp_path, real_queue,
                                                                        monkeypatch):
    """The consequence that makes the ordering matter: the reclaimed row is available to this run's
    first claim and comes back stamped with THIS run — the property `claimed_by_run` exists for."""
    queue, job_id = real_queue
    runs = RunLedger(tmp_path / "runs.sqlite")
    launcher = _serving_launcher(tmp_path, runs, queue, monkeypatch)

    assert launcher.start(max_ticks=1) == 0
    opened = runs.last()
    assert opened is not None
    assert _read_job(queue.path, job_id)["claimed_by_run"] == opened.id


def test_a_non_idempotent_stranded_row_is_failed_not_silently_requeued(tmp_path, monkeypatch):
    """The other half of the sweep's contract, driven through `start()` for the first time: a kind
    that cannot be safely re-run is made VISIBLE as FAILED rather than left pending forever."""
    path = tmp_path / "queue.sqlite"
    job_id = _strand_a_running_row(path, kind="research")
    queue = _RecordingQueue(path)
    runs = RunLedger(tmp_path / "runs.sqlite")
    launcher = _serving_launcher(tmp_path, runs, queue, monkeypatch)
    assert launcher.start(max_ticks=1) == 0
    row = _read_job(path, job_id)
    assert row["state"] == "failed"
    assert "orphaned by unclean exit of run #999" in (row["error"] or "")


# =================================================================================================
# Item 1 — the status block discriminates healthy from wedged (warrant finding-0188)
# =================================================================================================
#
# bp-102 §0 promised: "Without a throughput and rate readout there is no way to tell a healthy
# backfill from tonight's wedged one." Both states were constructed at audit time and EVERY
# anomaly flag was identical, because every figure in the block counts job BOUNDARIES while the
# failure mode is intra-job. These two states differ in exactly one physical fact — whether the
# vector store has been written since the running job started — and the renders must differ.

_JOBS_DDL = """
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT NOT NULL, tier TEXT NOT NULL,
    num_ctx INTEGER NOT NULL, priority INTEGER NOT NULL, state TEXT NOT NULL,
    payload TEXT, result TEXT, error TEXT, attempts INTEGER NOT NULL DEFAULT 0,
    checkpoint TEXT, created_at TEXT NOT NULL, started_at TEXT, finished_at TEXT
);
"""


def _backfill_in_flight(tmp_path, *, job_elapsed_min: float, backlog: int = 40) -> None:
    """The shared fixture: a `code_backfill` RUNNING for `job_elapsed_min`, a real backlog behind
    it, and zero completions in the window. This is the state BOTH readings share — healthy and
    wedged are byte-identical here, which is precisely why the queue alone cannot separate them."""
    now = datetime.now(UTC).replace(tzinfo=None)

    def at(**d):
        return (now - timedelta(**d)).isoformat(timespec="seconds")

    rows = [(1, "code_backfill", "router", 8192, 100, "running", None,
             at(minutes=job_elapsed_min + 1), at(minutes=job_elapsed_min), None)]
    for i in range(backlog):                      # depth > 0, so `stalled`'s precondition is met
        rows.append((10 + i, "vault_sync", "router", 8192, 100, "queued", None,
                     at(minutes=i), None, None))
    conn = sqlite3.connect(tmp_path / "queue.sqlite")
    conn.executescript(_JOBS_DDL)
    conn.executemany(
        "INSERT INTO jobs (id, kind, tier, num_ctx, priority, state, error, created_at, "
        "started_at, finished_at) VALUES (?,?,?,?,?,?,?,?,?,?)", rows)
    conn.commit()
    conn.close()


def _store_last_written(tmp_path, *, seconds_ago: float) -> None:
    """Pin the vector store's last-write time. A lance write bumps its parent directory's mtime
    (measured against the real store), so `os.utime` reproduces the signal exactly.

    Stamped RECURSIVELY and applied AFTER the store exists, because `store_idle_seconds` takes the
    MAXIMUM over the tree — ageing only the top directory leaves a fresh child and reads as a
    write that never happened. (Opening and `count()`ing the store do NOT bump any mtime — measured
    — so `status` is not self-blinding; it is only *creating* an absent table that writes.)"""
    store = tmp_path / "v.lance"
    store.mkdir(exist_ok=True)
    stamp = time.time() - seconds_ago
    for p in [store, *store.rglob("*")]:
        os.utime(p, (stamp, stamp))


def _status_render(tmp_path, monkeypatch, capsys) -> str:
    runs = RunLedger(tmp_path / "runs.sqlite")
    runs.open_run(commit_sha="abc123456789", dirty=False, pid=os.getpid())   # a LIVE daemon
    monkeypatch.setattr("ops.lifecycle.launcher.git_state", lambda _r: ("abc123456789", False))
    passing = Preflight((Check("x", required=True, ok=True, detail="ok"),))
    launcher = Launcher(cfg=_cfg(tmp_path), runs=runs, repo_root=Path(".").resolve(),
                        preflight_fn=lambda _c: passing)
    monkeypatch.setattr(Launcher, "_embedder_state", lambda _s, _ok: "qwen3-embedding:4b resident")
    assert launcher.status() == 0
    return capsys.readouterr().out


def _system_block(out: str) -> str:
    """Just the `system:` block — the part bp-102 built and finding-0188 measured as identical."""
    return out.split("system:", 1)[1]


def test_a_healthy_backfill_and_a_wedged_one_do_not_render_the_same(tmp_path, monkeypatch,
                                                                    capsys):
    """⚑ THE NAMED FALSIFIER: *the two renders are identical.* This is the plan's whole reason to
    exist — if they match, the instrument has failed regardless of any other test passing.

    The two states get their OWN data dirs: identical queue, identical live daemon, identical
    everything, differing in exactly one physical fact — whether the store has been written since
    the job started. Sharing a dir would let the first render's table creation age into the
    second's measurement."""
    healthy_dir, wedged_dir = tmp_path / "healthy", tmp_path / "wedged"
    for d, idle_s in ((healthy_dir, 12), (wedged_dir, 90 * 60)):
        d.mkdir()
        _backfill_in_flight(d, job_elapsed_min=75)
        _store_last_written(d, seconds_ago=idle_s)

    healthy = _system_block(_status_render(healthy_dir, monkeypatch, capsys))
    wedged = _system_block(_status_render(wedged_dir, monkeypatch, capsys))

    assert healthy != wedged, "the wedge detector cannot tell the two states apart (finding-0188)"
    assert "embedding: YES" in healthy and "⚠" not in healthy
    assert "embedding: NO" in wedged and "⚠ WEDGED" in wedged


def test_the_healthy_backfill_raises_no_anomaly_flag_at_all(tmp_path, monkeypatch, capsys):
    """⚑ THE SECOND FALSIFIER — the false-alarm guard, REBUILT NON-TRIVIALLY.

    bp-102's version used `depth == 0` with no running row, which makes both anomaly predicates
    unreachable **by construction**: mutating `stalled` to fire unconditionally passed all 9 tests.
    This fixture has `depth > 0` AND a running job, so every predicate's preconditions are
    genuinely satisfied and only the discriminator keeps the block quiet."""
    _backfill_in_flight(tmp_path, job_elapsed_min=75)
    _store_last_written(tmp_path, seconds_ago=12)
    out = _status_render(tmp_path, monkeypatch, capsys)
    block = _system_block(out)

    assert "running: #1 code_backfill" in block          # the precondition really is satisfied
    assert "waiting: vault_sync 40" in block             # depth > 0 really is satisfied
    assert "throughput: 0 done" in block                 # zero drain really is satisfied
    assert "⚠" not in block                              # …and the instrument still says nothing


def test_the_wedge_is_still_caught_when_the_job_genuinely_embeds_nothing(tmp_path, monkeypatch,
                                                                        capsys):
    """The other direction: suppressing the false alarm must not suppress the real one. The
    incident's shape — a job running 75 min with a store untouched for 90 — must still fire."""
    _backfill_in_flight(tmp_path, job_elapsed_min=75)
    _store_last_written(tmp_path, seconds_ago=90 * 60)
    block = _system_block(_status_render(tmp_path, monkeypatch, capsys))

    assert "⚠ WEDGED" in block
    assert "ZERO DRAIN" in block
    assert "running while NOTHING completed this window" in block


def test_a_store_written_just_before_the_job_started_is_not_progress(tmp_path, monkeypatch,
                                                                     capsys):
    """The boundary that makes the predicate threshold-free, and the one an off-by-one would eat:
    rows landed by the PREVIOUS job are not evidence that THIS one is working."""
    _backfill_in_flight(tmp_path, job_elapsed_min=60)
    _store_last_written(tmp_path, seconds_ago=61 * 60)     # just before this job started
    assert "⚠ WEDGED" in _system_block(_status_render(tmp_path, monkeypatch, capsys))


def test_a_write_into_a_nested_fragment_directory_counts_as_a_write(tmp_path):
    """The subdirectory walk is LOAD-BEARING, and only a nested fixture proves it.

    Caught by mutation: stubbing the `os.walk` out of `store_idle_seconds` left every other test in
    this file green, because they age the whole tree uniformly and the top directory alone then
    carries the answer. **The real store does not look like that.** Measured on
    `data/vectors.lance`: the top directory's mtime was 14.9 h old while
    `chunks.lance/{_versions,_transactions,data}` were 13.7 h old — a lance write adds entries to
    the nested directories and never touches the root. Statting only the root would report a store
    written minutes ago as idle for hours, and a healthy backfill as WEDGED.

    So this fixture reproduces the real layout: a STALE root with a FRESH fragment directory."""
    root = tmp_path / "v.lance"
    (root / "chunks.lance" / "_versions").mkdir(parents=True)
    stale = time.time() - 6 * 3600
    for p in [root, root / "chunks.lance"]:
        os.utime(p, (stale, stale))
    fresh = time.time() - 30
    os.utime(root / "chunks.lance" / "_versions", (fresh, fresh))

    idle = store_idle_seconds(root)
    assert idle is not None
    assert idle < 120, f"a write into a nested fragment dir was missed (idle={idle:.0f}s)"


def test_store_idle_is_none_when_there_is_no_store(tmp_path):
    """No store is an honest `None`, never a fabricated zero — a missing figure must not read as
    'written just now', which is the false green one level down."""
    assert store_idle_seconds(tmp_path / "does-not-exist") is None


def test_an_absent_store_says_unknown_rather_than_claiming_either_state(tmp_path, monkeypatch,
                                                                        capsys):
    """No store, no discriminator — and the block says so instead of guessing. An instrument that
    cannot measure must not report a verdict; the flags fall back to bp-102's behaviour."""
    _backfill_in_flight(tmp_path, job_elapsed_min=75)     # note: no `_store_last_written`
    block = _system_block(_status_render(tmp_path, monkeypatch, capsys))
    assert "embedding: unknown" in block
    assert "⚠ running while NOTHING completed this window" in block


# =================================================================================================
# bp-108 Item 3 — the supervisor role is KERNEL-exclusive (dn-supervision-and-liveness §2.6)
# =================================================================================================
#
# The gate above is now the DIAGNOSTIC layer: it can say WHICH run is live, but it is a probe with
# a check-then-act window, and it is blind to a claimant that never opened a run row. The lock is
# the guarantee. These tests assert the WIRING — that `start()` acquires it, refuses on it, and
# releases it. The kernel semantics themselves (cross-process exclusion, death-frees-it, the
# `flock`-vs-`lockf` choice) are proven in `tests/unit/test_supervisor_lock.py`; deliberately not
# restated here, so each layer is asserted exactly once.


def _lock_path(tmp_path: Path) -> Path:
    return tmp_path / "supervisor.lock"


def _someone_holds_the_lock(tmp_path: Path) -> bool:
    """Probe by attempting a real acquire. On this platform `flock` is per-open-file-description,
    so this answers correctly even from inside the process that holds it (measured, bp-108 Item 1)
    — which is what lets a test observe the launcher's own lock mid-`start()`."""
    probe = SupervisorLock(_lock_path(tmp_path))
    try:
        probe.acquire()
    except SupervisorLockHeld:
        return True
    probe.release()
    return False


def test_start_refuses_when_something_already_holds_the_supervisor_lock(tmp_path, monkeypatch,
                                                                       capsys):
    """⚑ NAMED FALSIFIER (finding-0186's OPEN half). The run ledger is EMPTY here, so the identity
    gate has nothing to refuse on and waves this start through. That is exactly `scripts/watch.py`'s
    shape — a claimant that never opened a run row — and the lock is what stops it."""
    runs = RunLedger(tmp_path / "runs.sqlite")
    assert runs.last() is None                          # the gate cannot help; only the lock can
    holder = SupervisorLock(_lock_path(tmp_path))
    holder.acquire()
    try:
        launcher, probes = _launcher(tmp_path, runs, monkeypatch=monkeypatch)
        assert launcher.start(max_ticks=1) == 1
        out = capsys.readouterr().out
        assert "supervisor lock" in out                  # the message NAMES the mechanism
        assert str(_lock_path(tmp_path)) in out          # ...and the file, so it can be found
        assert probes["preflight"] == 0                  # refused before the 120 s Ollama probe
        assert runs.last() is None                       # and before any run row was opened
    finally:
        holder.release()


def test_force_does_not_bypass_the_supervisor_lock(tmp_path, monkeypatch, capsys):
    """⚑ THE INVARIANT, restated one layer down. §4 of the note: "a mutual-exclusion guarantee
    behind a flag is a contradiction". `--force` overrides preflight, never exclusivity."""
    runs = RunLedger(tmp_path / "runs.sqlite")
    holder = SupervisorLock(_lock_path(tmp_path))
    holder.acquire()
    try:
        launcher, _ = _launcher(tmp_path, runs, monkeypatch=monkeypatch)
        assert launcher.start(force=True, max_ticks=1) == 1
        assert "supervisor lock" in capsys.readouterr().out
        assert runs.last() is None
    finally:
        holder.release()


def test_the_lock_is_held_before_the_sweep_and_released_after_shutdown(tmp_path, monkeypatch):
    """⚑ ORDERING, not mere presence. `sweep_orphans` is the operation that rewrites another
    claimant's rows, so acquiring AFTER it would leave the finding-0186 window wide open. And the
    release must happen — a lock still held after `start()` returns would refuse every successor."""
    runs = RunLedger(tmp_path / "runs.sqlite")
    seen: dict[str, bool] = {}

    def _observing_sweep(_self, run_id):
        seen["held_at_sweep"] = _someone_holds_the_lock(tmp_path)
        return _Swept(run_id)

    monkeypatch.setattr(_NullQueue, "sweep_orphans", _observing_sweep)
    launcher, _ = _launcher(tmp_path, runs, monkeypatch=monkeypatch,
                            on_shutdown=lambda _clean: seen.__setitem__(
                                "held_at_shutdown", _someone_holds_the_lock(tmp_path)))

    assert launcher.start(max_ticks=1) == 0
    assert seen["held_at_sweep"] is True                 # acquired BEFORE the sweep ran
    assert seen["held_at_shutdown"] is True              # still held while shutting down
    assert _someone_holds_the_lock(tmp_path) is False    # and dropped by the time start() returns


def test_recovery_mode_holds_the_lock_too(tmp_path, monkeypatch):
    """A recovery run is read-only, but it IS a live supervisor (`launcher.py`'s `_idle` branch),
    and `start` prints `palace stop` as the way out of it. If recovery did not hold the lock, a
    second supervisor could come up beneath the very run the operator is inspecting."""
    runs = RunLedger(tmp_path / "runs.sqlite")
    runs.open_run(commit_sha="old000000000", dirty=False, pid=DEAD_PID)   # unclean → recovery
    held: dict[str, bool] = {}
    launcher, _ = _launcher(tmp_path, runs, monkeypatch=monkeypatch,
                            on_shutdown=lambda _c: held.__setitem__(
                                "during", _someone_holds_the_lock(tmp_path)))

    assert launcher.start(max_ticks=1) == 0
    last = runs.last()
    assert last is not None and last.recovery           # we really did take the recovery branch
    assert held["during"] is True
    assert _someone_holds_the_lock(tmp_path) is False


def test_a_failed_preflight_still_releases_the_lock(tmp_path, monkeypatch, capsys):
    """The early-return path that has no `_shutdown` to clean up after it. A preflight failure that
    leaked the lock would make the FIRST bad start poison every later one — and under launchd
    KeepAlive that is an unrecoverable restart loop, not an inconvenience."""
    runs = RunLedger(tmp_path / "runs.sqlite")
    failing = Preflight((Check("ollama", required=True, ok=False, detail="down"),))
    launcher, _ = _launcher(tmp_path, runs, monkeypatch=monkeypatch)
    launcher.preflight_fn = lambda _c: failing

    assert launcher.start(max_ticks=1) == 1
    assert "preflight failed" in capsys.readouterr().out
    assert _someone_holds_the_lock(tmp_path) is False    # released despite the early return


def test_the_lockfile_sits_beside_the_queue_not_in_the_repo(tmp_path, monkeypatch):
    """§11's parked decision, pinned. In the repo it would scope exclusion to a CHECKOUT, so two
    worktrees over one data dir would both start; in /tmp it would be cleared by the OS and not
    co-located with the resource it guards."""
    runs = RunLedger(tmp_path / "runs.sqlite")
    launcher, _ = _launcher(tmp_path, runs, monkeypatch=monkeypatch)
    assert launcher.start(max_ticks=1) == 0
    assert _lock_path(tmp_path).exists()
    assert _lock_path(tmp_path).parent == launcher.cfg.paths.data_dir


def test_shutdown_relinquishes_the_role_on_its_own(tmp_path, monkeypatch):
    """`_shutdown` is `start`'s NORMAL release site (plan §7 Item 3); `start`'s own `finally` is
    only the net for paths that never reach it. Driven directly so the two are pinned
    independently — a mutation drill showed that with only the net asserted, deleting
    `_shutdown`'s release is completely invisible.

    The release is deliberately the LAST thing `_shutdown` does, after `mark_stopped`. Releasing
    earlier would open a window where a successor holds the lock while this run's row is still
    active, so its `sweep_orphans` would find live rows to reclaim — finding-0186 reintroduced by
    an ordering mistake."""
    runs = RunLedger(tmp_path / "runs.sqlite")
    launcher, _ = _launcher(tmp_path, runs, monkeypatch=monkeypatch)
    run = runs.open_run(commit_sha="abc123456789", dirty=False, pid=os.getpid())
    launcher._run_id = run.id
    launcher._lock = SupervisorLock(_lock_path(tmp_path))
    launcher._lock.acquire()
    assert _someone_holds_the_lock(tmp_path) is True

    launcher._shutdown(clean=True)

    assert _someone_holds_the_lock(tmp_path) is False
    closed = runs.last()
    assert closed is not None and not closed.active      # the row was closed before the release


def test_shutdown_releases_even_when_there_is_no_run_to_close(tmp_path, monkeypatch):
    """`_shutdown` early-returns when no run row was opened. It must still drop the lock on the
    way out — otherwise a start that acquired and then failed before `open_run` would hold the
    role with nothing to show for it."""
    runs = RunLedger(tmp_path / "runs.sqlite")
    launcher, _ = _launcher(tmp_path, runs, monkeypatch=monkeypatch)
    launcher._lock = SupervisorLock(_lock_path(tmp_path))
    launcher._lock.acquire()
    assert launcher._run_id is None                       # nothing to close down

    launcher._shutdown(clean=False)

    assert _someone_holds_the_lock(tmp_path) is False
