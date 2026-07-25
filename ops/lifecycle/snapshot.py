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
                    elapsed / last failure, read from the `jobs` schema
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
import sqlite3
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Protocol

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
    budget firing. Printing `elapsed / budget` would require inventing the denominator."""

    id: int
    kind: str
    started_at: str | None
    elapsed_s: float | None


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
    def stalled(self) -> bool:
        """ZERO DRAIN: work is waiting and **nothing completed** in the whole window.

        Keyed on `done`, not on `done + failed`, deliberately. A failure is a terminal transition
        (it belongs in `out_rate`, which must stay a true d(depth)/dt term) but it is not
        progress — and at the exact moment the owner sampled the incident, one job HAD just
        failed. Counting that as drain would have silenced this flag at 03:45:07, which is
        precisely when it needed to fire."""
        return self.depth > 0 and self.done_in_window == 0

    @property
    def wedged(self) -> bool:
        """A job is RUNNING and yet nothing has COMPLETED all window — the worker is busy doing
        the wrong kind of work (99% CPU, 0.3% embedder). Level + derivative, together."""
        return bool(self.running) and self.done_in_window == 0

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
                     max_kinds: int = 6) -> QueueStats:
    """Read the rate/budget block off the durable queue — **read-only and O(1) in rows returned**.

    Opened with a `file:…?mode=ro` URI so this can never create or mutate `queue.sqlite`: `status`
    is the first command anyone runs after an incident and must be safe with the daemon down (it
    previously CREATED the queue file via `JobQueue(...)` just to read `depth()`). A missing file
    reports `exists=False` rather than raising.

    Why raw SQL rather than `JobQueue`: `JobQueue` exposes no windowed or aggregate reads
    (`list()` would materialize every one of 300k rows with payloads), and `scheduler/queue.py` is
    bp-101's write scope. bp-102 §2.6 pins the `jobs` schema as the source for exactly these
    queries. The hand-off — these belong on `JobQueue` — is finding-0175.
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
        running = tuple(
            RunningJob(id=int(r["id"]), kind=str(r["kind"]), started_at=r["started_at"],
                       elapsed_s=_age_s(r["started_at"], now))
            for r in q("SELECT id, kind, started_at FROM jobs WHERE state = ? "
                       "ORDER BY started_at LIMIT 10", (RUNNING,))
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
        rows_read=rows_read, queries=queries,
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

    Both hand-offs are finding-0175. Reporting an expensive figure would fail the falsifier;
    reporting a fabricated one would be worse; saying nothing and pretending coverage is unknown
    for a mysterious reason would be worst. The render says which figure is missing and why."""

    vector_rows: int | None


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
