"""Status snapshot — the core→edge monitoring handoff (Invariant 2) AND the `status` payload.

The launcher writes a small JSON snapshot of operational METADATA to a file each health tick; the
edge monitor process READS only that file to render its dashboard. Same asymmetry as the airlock:
the core emits, the networked side never reads a store. The snapshot carries only what the OpsView
already narrates — action counts, health, the *shape* of recent activity, queue depth, memory
headroom — plus dream/finding counts. NO note text, NO authored-note titles, NO secrets/tokens.

**bp-102 — levels are not enough.** `status` reported LEVELS while every symptom of the 2026-07-25
incident was a RATE or a BUDGET (finding-0172): a queue growing at ~2/min with zero drain, an hour
of zero throughput, a job that failed fifteen minutes earlier, and a `RUNNING` banner over a dead
pid. This module therefore also carries:

  * `run_state`   — the liveness verdict, PURE, with the liveness primitive INJECTED (there is
                    exactly one `_pid_alive`, in `ops/lifecycle/launcher.py`; this module never
                    writes a second one, and taking it as an argument also avoids an import cycle);
  * `read_queue_stats` — windowed throughput / in-rate / out-rate / per-kind oldest age / running
                    elapsed / lease-derived orphanhood / last failure, read from the `jobs` schema
                    (`scheduler/queue.py:62+`) over a **read-only** connection;
  * `read_store_stats` — the METADATA-ONLY store figures.

**Cost is a correctness property here** (finding-0169 one level up): a diagnostic tool that
full-scans `data/vectors.lance` — or materializes the `vector` column — is disqualifying even if
every number it prints is right. Every read below is an aggregate or a `LIMIT`-ed row; nothing
materializes a payload column, and `QueueStats` carries `rows_read`/`queries` so that bound is
asserted mechanically in the tests rather than merely claimed.
"""

from __future__ import annotations

import json
import os
import sqlite3
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Protocol

# The ONE implementation of "has this deadline passed?", imported rather than re-derived. The
# state-name constants below are deliberately kept local (they are schema literals, and this module
# reads the `jobs` table with raw SQL rather than through `JobQueue`), but the lease POLARITY is a
# semantic rule, not a literal: `NULL ⇒ not expired` is what keeps a pre-migration queue file — the
# live one, 302,010 rows, every deadline NULL — from reading as 300k orphans. Two copies of that
# rule would be two chances to invert it, so there is one (bp-109 §6).
from scheduler.queue import deadline_lapsed

# --- the rate window W ---------------------------------------------------------------------
# bp-102 §11 parked decision, resolved here. 20 minutes: long enough to smooth the chat watcher's
# 0.5 s debounce (which bursts a couple of enqueues a minute), short enough that the 2026-07-25
# incident reads as an emergency the moment it is sampled — at the owner's 03:45 check it would
# have shown 0 completions against 1,714 queued. 1 min is noise against the debounce; 1 h would
# have read "normal" for most of that night. NOT a config knob: `core/config/loader.py` is schema'd
# and drops unknown sections, so a `[status]` key would be inert — a decorative constant is worse
# than a documented one (the same reasoning that dropped bp-102's job-timeout knob; finding-0174).
STATUS_WINDOW_MINUTES = 20.0

QUEUED, RUNNING, DONE, FAILED, DEFERRED = "queued", "running", "done", "failed", "deferred"
_TERMINAL = (DONE, FAILED)


def _utcnow() -> str:
    return datetime.now(UTC).replace(tzinfo=None).isoformat(timespec="seconds")


def _parse(ts: str | None) -> datetime | None:
    """A queue/ledger timestamp (naive UTC ISO-8601) → datetime; None/garbage → None."""
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts)
    except ValueError:
        return None


def _lease_of(row: sqlite3.Row) -> str | None:
    """`row["lease_expires_at"]`, or None when the row came off a pre-bp-109 queue file whose
    projection could not include the column. One helper rather than a repeated `in row.keys()`
    test at each of the two use sites."""
    return row["lease_expires_at"] if "lease_expires_at" in row.keys() else None


def _age_s(ts: str | None, now: datetime) -> float | None:
    at = _parse(ts)
    return None if at is None else max(0.0, (now - at).total_seconds())


def humanize_seconds(seconds: float | None) -> str:
    """`4490.0` → `'1h14m50s'`. Compact and exact — an operator reading a status line during an
    incident needs the magnitude at a glance, and rounding a budget away is how a 74-minute job
    reads as fine."""
    if seconds is None:
        return "?"
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    if h:
        return f"{h}h{m:02d}m{sec:02d}s"
    if m:
        return f"{m}m{sec:02d}s"
    return f"{sec}s"


# --- liveness ------------------------------------------------------------------------------
def run_state(run: Any, *, pid_alive: Callable[[int], bool]) -> tuple[str, bool | None]:
    """`(rendered state, is_alive)` for one run ledger row.

    The defect this closes (finding-0172): `status` rendered `"RUNNING" if r.active` straight from
    the ledger, so a `kill -9`'d daemon kept reporting `RUNNING` — the one question an operator
    trusts `status` to answer, answered wrongly. `deploy` already tested `_pid_alive(run.pid)`;
    the primitive existed and the reporting path simply did not call it.

    `pid_alive` is INJECTED rather than imported: `ops.lifecycle.launcher._pid_alive` is the single
    implementation (`os.kill(pid, 0)`), and injecting it keeps this function pure/testable and
    `snapshot` free of an import cycle back into `launcher`.

    Note on the false-alarm falsifier: `_pid_alive` returns True on `PermissionError`, so a daemon
    running as another principal (the `ouroboros` LaunchDaemon user, dn-plane-principals) is still
    LIVE here. Only `ProcessLookupError` reads dead. Residual, documented and unfixed: pid REUSE
    would read a recycled pid as alive — a false green, no worse than the unconditional `RUNNING`
    it replaces.

    `is_alive` is None where liveness is not applicable (no run, or a run already closed out).
    """
    if run is None:
        return ("none", None)
    if not run.active:
        return (("clean" if run.clean_shutdown else "UNCLEAN"), None)
    if pid_alive(run.pid):
        return ("RUNNING", True)
    return ("DEAD (stale ledger row)", False)


# --- the rate / budget block ---------------------------------------------------------------
@dataclass(frozen=True)
class RunningJob:
    """A job the queue believes is RUNNING, with its elapsed wall clock.

    There is deliberately NO budget fraction: **no job-level timeout exists anywhere in the
    system** (bp-102 Q4, finding-0174). The 2026-07-25 `TimeoutError` was the `[ollama]`
    `request_timeout_s` socket timeout on one embed call after 74m50s of elapsed work, not a job
    budget firing. Printing `elapsed / budget` would require inventing the denominator.

    `lease_expired` is where "the queue *believes* it is RUNNING" stops being the end of the story
    (bp-109 Item 3): a row whose claim deadline has passed is orphaned by definition, and this
    reader says so with **no sweep having run** — the sweep stops being a call someone must
    remember to make (finding-0187's exact failure). Computed at read time from the same `now` as
    `elapsed_s`, because this dataclass is a snapshot, not a live row. It is False whenever the
    deadline is NULL, which is every row a pre-bp-109 daemon wrote and every kind with no budget
    configured — so on today's live file every one of these reads exactly as it did before."""

    id: int
    kind: str
    started_at: str | None
    elapsed_s: float | None
    lease_expires_at: str | None = None
    lease_expired: bool = False


@dataclass(frozen=True)
class QueuedKind:
    """Per-kind backlog: how many are waiting and how long the oldest has waited."""

    kind: str
    count: int
    oldest_created_at: str | None
    oldest_age_s: float | None


@dataclass(frozen=True)
class JobFailure:
    """The most recent FAILED job — the thing `status` showed six green checkmarks over."""

    id: int
    kind: str
    error: str
    finished_at: str | None
    age_s: float | None


@dataclass(frozen=True)
class QueueStats:
    """Levels AND derivatives over the `jobs` table, all from bounded aggregates.

    `rows_read` / `queries` are the cost witnesses: both are independent of table size, which is
    what the Item-2 falsifier test asserts (a 50-job and a 5,000-job queue must agree)."""

    exists: bool
    depth: int
    window_minutes: float
    enqueued_in_window: int
    done_in_window: int
    failed_in_window: int
    lifetime: Mapping[str, int]
    running: tuple[RunningJob, ...]
    queued_by_kind: tuple[QueuedKind, ...]
    last_failure: JobFailure | None
    rows_read: int
    queries: int
    # The one datum here that is NOT from the `jobs` table (bp-105 Item 1, finding-0188): seconds
    # since the vector store was last written. Every other figure in this class is a job-BOUNDARY
    # count, and the wedge is INTRA-job — so on their own they cannot separate a healthy backfill
    # from a wedged one. This is the intra-job derivative that can, and it lives here because this
    # is where the anomaly predicates live. None = not measured (no store, or an unreadable path).
    store_idle_s: float | None = None

    @property
    def in_rate_per_min(self) -> float:
        return self.enqueued_in_window / self.window_minutes if self.window_minutes else 0.0

    @property
    def out_rate_per_min(self) -> float:
        n = self.done_in_window + self.failed_in_window
        return n / self.window_minutes if self.window_minutes else 0.0

    @property
    def net_rate_per_min(self) -> float:
        """d(depth)/dt over W. Positive = the backlog is growing. Both `done` AND `failed` leave
        the queue, so the out term must count both for this to be an honest derivative of depth."""
        return self.in_rate_per_min - self.out_rate_per_min

    @property
    def embedding(self) -> bool | None:
        """Is the RUNNING job demonstrably landing rows? `True` / `False` / `None` = unknown.

        **The discriminator bp-102 was missing** (finding-0188). Every other figure in this class
        counts job BOUNDARIES, and `code_backfill_handler` makes one synchronous non-checkpointing
        call while `Supervisor.tick` waits (`scheduler/supervisor.py:87`, no job timeout), so a
        perfectly healthy multi-hour backfill emits zero terminal transitions — indistinguishable
        from the wedge, which is exactly what shipped.

        The test is threshold-free, which is what makes it trustworthy: **was the vector store
        written after the running job started?** If yes, that job has landed rows and is working.
        If the last write PREDATES the job's own start, the job has landed nothing since it began.
        No magic constant, no tuned window — the job's own elapsed is the denominator.

        Conservative on purpose: with several rows RUNNING it compares against the *youngest*
        job's elapsed, so an ambiguous multi-job state reads as NOT progressing. A false alarm
        costs a second look; a false green is what the incident already cost.

        Honest limitation, stated rather than papered over: this senses the *embedding* lane. A
        long non-embedding job (`dream`, `curate`) legitimately never touches the vector store and
        so reads as not-progressing — no worse than today, where it also trips both flags."""
        floor = self.youngest_running_elapsed_s
        if self.store_idle_s is None or floor is None:
            return None
        return self.store_idle_s < floor

    @property
    def orphaned_running(self) -> tuple[RunningJob, ...]:
        """The RUNNING rows whose claim deadline has demonstrably lapsed — **the derived view**
        (bp-109 Item 3 / dn-supervision-and-liveness §2.6). No sweep has to have run for this to be
        populated; orphanhood is read off the row, not off whether anybody remembered to reclaim it.

        Empty on every queue file written before the lease column existed, and empty for every kind
        with no configured budget (which is all of them by default) — so this is strictly NEW
        information, never a reinterpretation of an old row.

        Deliberately NOT folded into `wedged` / `stalled` / `embedding`. Every candidate way of
        doing that makes an existing flag QUIETER (excluding an orphan from `wedged`'s `running`
        test, or from `youngest_running_elapsed_s`'s min, both let a state that flags today go
        unflagged), and the render that would carry the orphan reason instead
        (`launcher.py:1271-1285`, keyed on daemon liveness) belongs to a later plan's write scope.
        A trade of one loud imprecise flag for one silent precise one is a false green, which is the
        failure this whole track exists to remove — so the sharpening waits for the render."""
        return tuple(j for j in self.running if j.lease_expired)

    @property
    def youngest_running_elapsed_s(self) -> float | None:
        """Elapsed of the most recently STARTED running job — `embedding`'s denominator, exposed so
        the render prints the same number the predicate decided on rather than recomputing it."""
        elapsed = [j.elapsed_s for j in self.running if j.elapsed_s is not None]
        return min(elapsed) if elapsed else None

    @property
    def progressing(self) -> bool:
        """Demonstrably making progress — the one state in which an anomaly flag must stay quiet."""
        return self.embedding is True

    @property
    def stalled(self) -> bool:
        """ZERO DRAIN: work is waiting and **nothing completed** in the whole window.

        Keyed on `done`, not on `done + failed`, deliberately. A failure is a terminal transition
        (it belongs in `out_rate`, which must stay a true d(depth)/dt term) but it is not
        progress — and at the exact moment the owner sampled the incident, one job HAD just
        failed. Counting that as drain would have silenced this flag at 03:45:07, which is
        precisely when it needed to fire.

        Suppressed while `progressing` (bp-102 §10, discharged by bp-105): a long healthy backfill
        drains nothing at the job boundary for hours, and an instrument that cries wolf through all
        of it will be ignored during the next incident."""
        return self.depth > 0 and self.done_in_window == 0 and not self.progressing

    @property
    def wedged(self) -> bool:
        """A job is RUNNING and yet nothing has COMPLETED all window — the worker is busy doing
        the wrong kind of work (99% CPU, 0.3% embedder). Level + derivative, together.

        Now genuinely a WEDGE test rather than a long-job test: a running job that is landing rows
        is working, not wedged (finding-0188)."""
        return bool(self.running) and self.done_in_window == 0 and not self.progressing

    @property
    def failure_in_window(self) -> bool:
        f = self.last_failure
        return f is not None and f.age_s is not None and f.age_s <= self.window_minutes * 60.0


_EMPTY_QUEUE_STATS = QueueStats(
    exists=False, depth=0, window_minutes=STATUS_WINDOW_MINUTES, enqueued_in_window=0,
    done_in_window=0, failed_in_window=0, lifetime={}, running=(), queued_by_kind=(),
    last_failure=None, rows_read=0, queries=0,
)


def read_queue_stats(path: Path, *, now: datetime | None = None,
                     window_minutes: float = STATUS_WINDOW_MINUTES,
                     max_kinds: int = 6,
                     store_idle_s: float | None = None) -> QueueStats:
    """Read the rate/budget block off the durable queue — **read-only and O(1) in rows returned**.

    Opened with a `file:…?mode=ro` URI so this can never create or mutate `queue.sqlite`: `status`
    is the first command anyone runs after an incident and must be safe with the daemon down (it
    previously CREATED the queue file via `JobQueue(...)` just to read `depth()`). A missing file
    reports `exists=False` rather than raising.

    Why raw SQL rather than `JobQueue`: `JobQueue` exposes no windowed or aggregate reads
    (`list()` would materialize every one of 300k rows with payloads), and `scheduler/queue.py` is
    bp-101's write scope. bp-102 §2.6 pins the `jobs` schema as the source for exactly these
    queries. The hand-off — these belong on `JobQueue` — is finding-0178.
    """
    if not path.exists():
        return _EMPTY_QUEUE_STATS
    now = now or datetime.now(UTC).replace(tzinfo=None)
    cutoff = (now - timedelta(minutes=window_minutes)).isoformat(timespec="seconds")
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    rows_read = 0
    queries = 0

    def q(sql: str, args: tuple[object, ...] = ()) -> list[sqlite3.Row]:
        nonlocal rows_read, queries
        queries += 1
        out = conn.execute(sql, args).fetchall()
        rows_read += len(out)
        return out

    try:
        lifetime = {str(r[0]): int(r[1]) for r in q(
            "SELECT state, count(*) FROM jobs GROUP BY state")}
        enqueued = int(q("SELECT count(*) FROM jobs WHERE created_at > ?", (cutoff,))[0][0])
        done_w = int(q("SELECT count(*) FROM jobs WHERE state = ? AND finished_at > ?",
                       (DONE, cutoff))[0][0])
        failed_w = int(q("SELECT count(*) FROM jobs WHERE state = ? AND finished_at > ?",
                         (FAILED, cutoff))[0][0])
        running_sql = ("SELECT id, kind, started_at, lease_expires_at FROM jobs WHERE state = ? "
                       "ORDER BY started_at LIMIT 10")
        try:
            running_rows = q(running_sql, (RUNNING,))
        except sqlite3.OperationalError:
            # A queue file written before bp-109's migration has no `lease_expires_at`, and this
            # connection is `mode=ro` on purpose, so it cannot add one — `status` is the first thing
            # anyone runs after an incident and must never mutate the file it is describing. Fall
            # back to the pre-change projection; every row then reports no deadline, which is
            # precisely what a row without the column means (NULL ⇒ not expired).
            # A `PRAGMA table_info(jobs)` probe would be the obvious alternative and is deliberately
            # NOT used: every statement this function issues must be an aggregate or carry a LIMIT,
            # asserted by test_status_cost_bound.py::test_every_queue_statement_is_bounded, and a
            # PRAGMA is neither. The legacy form is derived from the new one rather than spelt
            # twice, so the projection cannot drift between the two paths.
            running_rows = q(running_sql.replace(", lease_expires_at", ""), (RUNNING,))
        running = tuple(
            RunningJob(id=int(r["id"]), kind=str(r["kind"]), started_at=r["started_at"],
                       elapsed_s=_age_s(r["started_at"], now),
                       lease_expires_at=_lease_of(r),
                       # `state = RUNNING` is already this query's own WHERE clause, so the state
                       # half of `scheduler.queue.lease_expired`'s conjunction holds by construction
                       # and only the clock half is left to evaluate.
                       lease_expired=deadline_lapsed(_lease_of(r), now))
            for r in running_rows
        )
        by_kind = tuple(
            QueuedKind(kind=str(r["kind"]), count=int(r["n"]),
                       oldest_created_at=r["oldest"], oldest_age_s=_age_s(r["oldest"], now))
            for r in q("SELECT kind, count(*) AS n, min(created_at) AS oldest FROM jobs "
                       "WHERE state = ? GROUP BY kind ORDER BY oldest LIMIT ?",
                       (QUEUED, max_kinds))
        )
        fail_rows = q("SELECT id, kind, error, finished_at FROM jobs WHERE state = ? "
                      "ORDER BY finished_at DESC, id DESC LIMIT 1", (FAILED,))
        last_failure = None
        if fail_rows:
            fr = fail_rows[0]
            last_failure = JobFailure(
                id=int(fr["id"]), kind=str(fr["kind"]), error=str(fr["error"] or ""),
                finished_at=fr["finished_at"], age_s=_age_s(fr["finished_at"], now))
    finally:
        conn.close()

    return QueueStats(
        exists=True, depth=lifetime.get(QUEUED, 0), window_minutes=window_minutes,
        enqueued_in_window=enqueued, done_in_window=done_w, failed_in_window=failed_w,
        lifetime=lifetime, running=running, queued_by_kind=by_kind, last_failure=last_failure,
        rows_read=rows_read, queries=queries, store_idle_s=store_idle_s,
    )


# --- the store block (METADATA ONLY) --------------------------------------------------------
class _CountableStore(Protocol):
    """The ONLY vector-store method this module is permitted to call. Anything wider
    (`all_rows`, `rows_for_source`, `search`, `to_arrow`) does a full `to_pylist()` that
    materializes the `vector` column — the finding-0169 mistake, one level up."""

    def count(self) -> int: ...


@dataclass(frozen=True)
class StoreStats:
    """Metadata-only corpus figures. Exactly ONE, because exactly one is cheap.

    Deliberately ABSENT, each for a MEASURED reason rather than an assumed one — bp-102's Item 2
    falsifier disqualifies an expensive status even when every number is right:

    * **distinct code versions embedded** and the **`current=true/false` split** — `VectorStore`'s
      only cheap read is `count()`; `all_rows`/`rows_for_source`/`relabel_provenance` all go
      through `to_arrow().to_pylist()`, which materializes the `vector` column. The metadata-only
      reader would be `count_rows(filter=…)` on `core/typedshims/lancedb.py` plus a method on
      `core/stores/vectorstore.py` — both outside bp-102's write scope (`core/stores/**` is
      bp-100's).
    * **the ledger target** (`COUNT(DISTINCT path, blob_sha)` over `code_snapshots.sqlite`) —
      measured at **3.5 s**: 423,855 rows, `SCAN files` + `USE TEMP B-TREE FOR DISTINCT`, over a
      2.3 GB table whose rows carry a `docstring` column. `files` is keyed `(commit_sha, path)`,
      so nothing indexes the pair this needs. That is a full scan by any name, and it belongs to
      the class of read this plan exists to keep out of `status`.

    Both hand-offs are finding-0178. Reporting an expensive figure would fail the falsifier;
    reporting a fabricated one would be worse; saying nothing and pretending coverage is unknown
    for a mysterious reason would be worst. The render says which figure is missing and why."""

    vector_rows: int | None


def store_idle_seconds(store_dir: Path, *, now: float | None = None) -> float | None:
    """Seconds since anything was last written under the vector store — `None` if it is absent or
    unreadable. The prior sample finding-0188 asks for, taken from the filesystem's own clock.

    **Why a directory walk and not a stored sample.** The obvious channel — have the supervisor
    write a periodic `(t, vector_rows)` sample that `status` differences — cannot work here:
    `Supervisor.tick` calls `handler(job)` synchronously with no timeout, so the launcher's serve
    loop is BLOCKED for the entire duration of the very job being diagnosed. Nothing on that loop
    can emit while it matters. The filesystem, however, is written by the embed itself, from
    inside the blocked call. It is the one channel the wedge cannot mute.

    **Cost is a correctness property** (finding-0169, one level up), so this stats DIRECTORIES
    only, never files: a lance write adds a fragment, a manifest and a transaction record, each of
    which bumps its parent directory's mtime. Measured against the real 22,621-row store —
    **8 directories, 0.80 ms**, and byte-identical to the full-tree maximum (897 files, 3.9 ms).
    O(directories), independent of row count, which is the same bound `read_queue_stats` carries.

    Best-effort like every other probe here: `status` must survive a half-built or corrupt data
    directory, because an incident is exactly when the store is the thing that is broken."""
    try:
        if not store_dir.exists():
            return None
        latest = store_dir.stat().st_mtime
        for dirpath, dirnames, _ in os.walk(store_dir):
            for name in dirnames:
                try:
                    latest = max(latest, os.stat(os.path.join(dirpath, name)).st_mtime)
                except OSError:
                    continue          # a fragment dir vanishing mid-walk is not a status failure
    except OSError:
        return None
    return max(0.0, (now if now is not None else time.time()) - latest)


def read_store_stats(*, vector_store: _CountableStore | None = None) -> StoreStats:
    """`count()` on the vector table — LanceDB fragment metadata, **measured at 1.4–2.9 ms** over
    the real 22,621-row store, and the `vector` column is never touched.

    Best-effort: a probe failure is reported as `None`, never raised, because `status` must
    survive a half-built or corrupt data directory — an incident is exactly when the store is the
    thing that is broken."""
    rows: int | None = None
    if vector_store is not None:
        try:
            rows = vector_store.count()
        except Exception:  # noqa: BLE001 — a probe failure is a missing figure, not a crash
            rows = None
    return StoreStats(vector_rows=rows)


# --- the payload ----------------------------------------------------------------------------
def _queue_payload(qs: QueueStats) -> dict[str, Any]:
    return {
        "window_minutes": qs.window_minutes,
        "depth": qs.depth,
        "in_rate_per_min": round(qs.in_rate_per_min, 2),
        "out_rate_per_min": round(qs.out_rate_per_min, 2),
        "net_rate_per_min": round(qs.net_rate_per_min, 2),
        "done_in_window": qs.done_in_window,
        "failed_in_window": qs.failed_in_window,
        "lifetime": dict(qs.lifetime),
        "running": [{"id": j.id, "kind": j.kind, "started_at": j.started_at,
                     "elapsed_s": None if j.elapsed_s is None else round(j.elapsed_s, 1)}
                    for j in qs.running],
        "queued_by_kind": [{"kind": k.kind, "count": k.count,
                            "oldest_created_at": k.oldest_created_at,
                            "oldest_age_s": None if k.oldest_age_s is None
                            else round(k.oldest_age_s, 1)}
                           for k in qs.queued_by_kind],
        "last_failure": None if qs.last_failure is None else {
            "id": qs.last_failure.id, "kind": qs.last_failure.kind,
            "error": qs.last_failure.error, "finished_at": qs.last_failure.finished_at,
            "age_s": None if qs.last_failure.age_s is None else round(qs.last_failure.age_s, 1),
        },
        # The finding-0188 discriminator, carried in the payload so the render is not the only
        # place it exists. Deliberately NOT under `anomalies`: `embedding: true` is the opposite
        # of an anomaly — it is the evidence that suppresses two of them.
        "progress": {
            "store_idle_s": None if qs.store_idle_s is None else round(qs.store_idle_s, 1),
            # tri-state: True = the running job is landing rows, False = it is not, None = unknown
            "embedding": qs.embedding,
        },
        "anomalies": {"stalled": qs.stalled, "wedged": qs.wedged,
                      "recent_failure": qs.failure_in_window},
    }


def build_status(*, ops_view, dreams_view, queue_depth: int, run=None,
                 mem_available_gb: float | None = None, flags=(),
                 liveness: tuple[str, bool | None] | None = None,
                 queue_stats: QueueStats | None = None,
                 store_stats: StoreStats | None = None,
                 embedder: str | None = None) -> dict[str, Any]:
    """Assemble the snapshot dict from the read-only views. Pure — no I/O — so it is unit-testable
    against in-memory stores. `run` is the active RunRecord (commit-pinned); `flags` are the OS
    watchdog's crossed-threshold flags.

    bp-102 extends the payload with `liveness` / `rates` / `store` / `embedder`. All four are
    keyword-only with `None` defaults, so every existing caller (the dormant edge-monitor snapshot,
    `tests/integration/test_monitor_snapshot.py`) is unchanged, and every value stays
    JSON-serializable — `write_status` still round-trips it. This is the single seam: nothing in
    the status path may print a datum that did not come through here."""
    snap = ops_view.snapshot()
    return {
        "generated_at": _utcnow(),
        "run": None if run is None else {
            "id": run.id,
            "commit": run.commit_sha[:12],
            "dirty": run.dirty,
            "started_at": run.started_at,
            "pid": run.pid,
        },
        # The liveness verdict for the reported run — never `RUNNING` for a dead pid (f-0172).
        "liveness": None if liveness is None else {
            "state": liveness[0], "alive": liveness[1],
        },
        "activity": {
            "actions_logged": snap.attestation_count,
            # (role, action, timestamp) — operational shape, never corpus content.
            "recent": [{"role": r, "action": a, "at": ts} for r, a, ts in snap.recent_actions],
            "pending_approvals": snap.pending_proposals,
        },
        "health": {
            "drift_within_tolerance": snap.drift_within_tolerance,
            "constitution_intact": snap.constitution_intact,
            "memory_available_gb": mem_available_gb,
            "flags": [{"metric": f.metric, "value": f.value, "threshold": f.threshold,
                       "note": f.note} for f in flags],
        },
        "patterns": {
            "dreams": dreams_view.dream_count(),
            "tidy_suggestions": dreams_view.finding_count(),
        },
        "queue_depth": queue_depth,
        # Derivatives, not levels — the bp-102 block.
        "rates": None if queue_stats is None else _queue_payload(queue_stats),
        "store": None if store_stats is None else {"vector_rows": store_stats.vector_rows},
        "embedder": embedder,
    }


def write_status(path: Path, data: dict[str, Any]) -> None:
    """Write the snapshot atomically — the edge reader never sees a partial file (rename swap)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(path)
