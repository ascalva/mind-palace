# ── Family 3 boundary (guarded transition systems) · symbols in docs/NOTATION.md ──
# OBJECT:    the job-queue lifecycle — a guarded transition system with monotone anti-starvation
#            aging. Forward: QUEUED→RUNNING→DONE/FAILED/DEFERRED. Return edges (all of them):
#            RUNNING→QUEUED (checkpoint yield; orphan reclaim), DEFERRED→QUEUED (revive).
#            DONE/FAILED are terminal — nothing ever leaves them.
# INVARIANT: every transition is precondition-checked; queued jobs *eventually* run — aging
#            never lifts a job above the REACTIVE floor (liveness, G6).
# ENFORCED:  runtime guard + test — single-writer SQLite under an RLock; AgingPolicy is a
#            no-op under normal load. Liveness is a supervisor progress guarantee, not safety.
"""Durable job queue — the scheduler's heartbeat (BUILD-SPEC §8, §13; roadmap §7).

SQLite, WAL mode, **single-writer by design**: one supervisor owns this queue, so there is
no write contention to reason about. The queue is the single safe serialization point —
agents are config (re-composed per invocation from the stores), not OS processes, so
"restoring" a job is cheap; the only heavyweight cost is a model load, which is what the
scheduler is built to minimize.

Scheduling is cooperative and acts at **job boundaries** (roadmap §7): `claim()` selects the
next job by priority, skipping tiers the caller says are currently blocked (the foreground
gate), and — within the top-priority band — prefers a job that needs no model swap. A
reactive escalation is just a high-priority job; it is dispatched next, never mid-generation.
`checkpoint`/`resume` support long jobs (dreaming, curation) written as yielding steps.

Two hygiene properties keep the queue bounded and self-healing (bp-101, findings 0170/0173):
`enqueue` **coalesces** an idempotent kind onto the QUEUED row that is already waiting instead of
stacking a duplicate behind a busy worker, and `sweep_orphans` **reclaims** RUNNING rows stranded by
a run that died without finishing them. Both are keyed off `_IDEMPOTENT_KINDS` — see its comment for
what earns membership, and never widen it by assumption.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Lower number = higher priority. Reactive/watchdog escalations use REACTIVE.
PRIORITY_REACTIVE = 0
PRIORITY_INTERACTIVE = 10
PRIORITY_DEFAULT = 50
PRIORITY_BACKGROUND = 100

QUEUED, RUNNING, DONE, FAILED, DEFERRED = "queued", "running", "done", "failed", "deferred"

# The kinds whose handler is a FULL RE-DERIVATION that is safe to run twice and carries no
# distinguishing payload. Membership grants exactly two things (bp-101):
#   * `enqueue` may coalesce a second request onto a QUEUED one instead of stacking it (f-0170);
#   * `sweep_orphans` may REQUEUE a row stranded mid-flight instead of failing it (f-0173).
# Both rest on the same property, so they share one set rather than two that could drift.
#
# A kind earns membership only when its own handler module asserts idempotence:
#   chat_sync     scheduler/chat_sync.py:48   "idempotent + growth-aware"
#   vault_sync    scheduler/vault_sync.py:39  "duplicate jobs are harmless — rescan() is idempotent"
#   code_sync     scheduler/code_sync.py:45   "idempotent + blob-sha keyed"
#   code_backfill scheduler/code_sync.py:53   "idempotent — already-embedded digests are skipped"
#   chat_events   scheduler/cron.py:114       "incremental … and idempotent"
#   integrate     scheduler/cron.py:136       "incremental … and idempotent"
# DELIBERATELY ABSENT: `dream`/`curate`/`shadow` mint fresh ledger rows per pass (not idempotent);
# `research`/`ambassador_task` are payload-bearing model work; `ambassador` IS re-runnable
# (`CoreInbox.process_once` drains all and consumes each file) but is the REACTIVE conversational
# front door and was never part of the observed stacking — excluded conservatively. Anything not
# listed is NOT collapsible: the default is "duplicate it" (waste), never "drop it" (lost work).
#
# These are string literals, not imports of `CHAT_SYNC_KIND` &c., because those modules import
# THIS one — importing back would cycle. `tests/unit/test_queue_coalescing.py` asserts the literals
# equal the constants, so the duplication is caught by a test rather than trusted.
_IDEMPOTENT_KINDS = frozenset(
    {"chat_sync", "vault_sync", "code_sync", "code_backfill", "chat_events", "integrate"})


@dataclass(frozen=True)
class AgingPolicy:
    """Anti-starvation aging (gap G6 — the liveness fix). A QUEUED job's EFFECTIVE priority
    improves (its number falls) the longer it waits, so background work (dreaming, curation)
    *eventually* outranks a perpetual stream of newer higher-priority jobs instead of starving
    under sustained foreground load — `◇ queued jobs eventually run`.

    Bounds, deliberately conservative:
      * a job that has waited < `step_seconds` ages zero steps, so NORMAL-load ordering is
        unchanged (jobs are usually claimed within seconds of enqueue);
      * aging never lifts a job above `floor` (default = INTERACTIVE), so an aged background
        job can come to tie with interactive work and win on FIFO, but can NEVER preempt a
        genuine REACTIVE escalation (a low-memory alarm must still go first — if those arrive
        perpetually the system is in crisis and background SHOULD wait)."""

    step_seconds: float = 900.0          # every 15 min waited, priority improves by one step
    step: int = 10                       # one priority band per step
    floor: int = PRIORITY_INTERACTIVE    # never age above this (reactive stays untouchable)

_DDL = """
CREATE TABLE IF NOT EXISTS jobs (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    kind           TEXT NOT NULL,
    tier           TEXT NOT NULL,
    num_ctx        INTEGER NOT NULL,
    priority       INTEGER NOT NULL,
    state          TEXT NOT NULL,
    payload        TEXT,            -- JSON
    result         TEXT,
    error          TEXT,
    attempts       INTEGER NOT NULL DEFAULT 0,
    checkpoint     TEXT,            -- resume token for checkpointed-step jobs
    created_at     TEXT NOT NULL,
    started_at     TEXT,
    finished_at    TEXT,
    claimed_by_run INTEGER          -- ops.lifecycle.runs `runs.id` of the run that claimed it
);
CREATE INDEX IF NOT EXISTS jobs_ready ON jobs (state, priority, id);
CREATE INDEX IF NOT EXISTS jobs_coalesce ON jobs (state, kind, id);
"""

# Additive-only migrations, applied in order on every open (finding-0173). Each entry is
# `(column, DDL)`; a column already present is skipped, so running twice is a no-op and a queue
# file written by the pre-change code is EXTENDED, never rewritten — no row's `id`, `state` or
# `created_at` is touched. `data/queue.sqlite` carries 300k+ lifetime rows on the live system and
# is never recreated (plan §7 Item 1 invariant).
#
# NOT done here, deliberately: finding-0170 suggests a partial UNIQUE index on
# `(kind, payload) WHERE state = 'queued'` to make coalescing structural rather than conventional.
# It cannot be created yet — the live file holds 1,766 duplicate queued rows (883 `chat_sync` +
# 883 `vault_sync`), so `CREATE UNIQUE INDEX` would raise on open and make the daemon unstartable.
# It becomes available once the restart clears those duplicates; see the journal.
_MIGRATIONS: tuple[tuple[str, str], ...] = (
    ("claimed_by_run", "ALTER TABLE jobs ADD COLUMN claimed_by_run INTEGER"),
)


def _migrate(conn: sqlite3.Connection) -> None:
    """Bring an existing `jobs` table up to `_DDL`'s columns. Purely additive and idempotent:
    reads `PRAGMA table_info` and applies only the `ALTER TABLE … ADD COLUMN` statements whose
    column is missing. Never UPDATEs, never DROPs, never rewrites a row."""
    present = {r["name"] for r in conn.execute("PRAGMA table_info(jobs)").fetchall()}
    for column, ddl in _MIGRATIONS:
        if column not in present:
            conn.execute(ddl)


def _utcnow() -> str:
    return datetime.now(UTC).replace(tzinfo=None).isoformat(timespec="seconds")


@dataclass(frozen=True)
class Job:
    id: int
    kind: str
    tier: str
    num_ctx: int
    priority: int
    state: str
    payload: dict[str, Any]
    result: str | None
    error: str | None
    attempts: int
    checkpoint: str | None
    created_at: str
    started_at: str | None
    finished_at: str | None
    claimed_by_run: int | None = None   # the run (`ops.lifecycle.runs`) that claimed it, if known

    @property
    def load_key(self) -> tuple[str, int]:
        """The (tier, window) that must be resident to run this job. Changing either forces
        a model reload (§13), so the supervisor batches jobs sharing a load_key."""
        return (self.tier, self.num_ctx)


@dataclass(frozen=True)
class OrphanSweep:
    """What one `sweep_orphans` pass did — the job ids it requeued and the ones it failed. Empty
    tuples mean a clean previous exit (the normal case), which is why the sweep is safe to run on
    every start."""

    requeued: tuple[int, ...] = ()
    failed: tuple[int, ...] = ()

    @property
    def total(self) -> int:
        return len(self.requeued) + len(self.failed)

    def render(self) -> str:
        if not self.total:
            return "orphan sweep: nothing stranded"
        return (f"orphan sweep: requeued {len(self.requeued)} "
                f"{sorted(self.requeued)}, failed {len(self.failed)} {sorted(self.failed)}")


def _row_to_job(r: sqlite3.Row) -> Job:
    return Job(
        id=r["id"], kind=r["kind"], tier=r["tier"], num_ctx=r["num_ctx"],
        priority=r["priority"], state=r["state"],
        payload=json.loads(r["payload"]) if r["payload"] else {},
        result=r["result"], error=r["error"], attempts=r["attempts"],
        checkpoint=r["checkpoint"], created_at=r["created_at"],
        started_at=r["started_at"], finished_at=r["finished_at"],
        claimed_by_run=r["claimed_by_run"],
    )


@dataclass
class JobQueue:
    path: Path
    aging: AgingPolicy = field(default_factory=AgingPolicy)   # anti-starvation (gap G6)
    # The run (`ops.lifecycle.runs` `runs.id`) that owns this queue handle. `claim()` stamps it on
    # every row it takes, which is what lets `sweep_orphans` tell live work from work stranded by a
    # dead run (finding-0173). None = unstamped; the supervisor sets it via `sweep_orphans` at
    # start. Leaving it None keeps every existing caller (CLI one-shots, tests) byte-identical.
    active_run_id: int | None = None

    def __post_init__(self) -> None:
        if str(self.path) != ":memory:":
            self.path.parent.mkdir(parents=True, exist_ok=True)
        # check_same_thread=False + an explicit lock: the watcher's debounce timer and poll
        # loop (core/ingest/watch.py) fire on_change from a thread they spawn themselves, not
        # the supervisor's main thread that constructs this queue — so enqueue() is genuinely
        # cross-thread. WAL mode + committing after every statement keeps each access short, so
        # a coarse lock around the connection is sufficient (no held transactions to block).
        # RLock (not Lock): enqueue()/claim() call self.get() while already holding the lock.
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(str(self.path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._conn.executescript(_DDL)
        _migrate(self._conn)          # additive-only; extends a pre-change file, never rewrites it
        self._conn.commit()

    # --- write path (supervisor-owned) -------------------------------------------
    def enqueue(self, kind: str, tier: str, num_ctx: int, *,
                priority: int = PRIORITY_DEFAULT,
                payload: dict[str, Any] | None = None) -> Job:
        """Add a job and return it. **Coalescing (extension, finding-0170):** for a kind in
        `_IDEMPOTENT_KINDS` (`chat_sync`, `vault_sync`, `code_sync`, `code_backfill`,
        `chat_events`, `integrate`) this returns the job ALREADY WAITING instead of inserting a
        duplicate. Every other kind behaves exactly as before — an unconditional INSERT.

        Three properties make the collapse safe to reason about:

        * **Only QUEUED rows collapse.** A job that is RUNNING is past the point where a new
          request can be folded into it (it may already have read the state the new request is
          about), so enqueueing `code_backfill` while one runs still inserts. Dropping that row
          would silently cancel the follow-up pass — the falsifier this rule exists to prevent.
        * **The key is `(kind, payload)`**, never `kind` alone, so a payload-bearing job is never
          swallowed by an unrelated one. `tier`/`num_ctx` must match too — a strictly narrower key
          that can only ever create a row, never drop one (routing is deterministic per kind today,
          so it never fires; it is here so a future re-route cannot silently mis-tier a job).
        * **The FIRST row wins, and keeps its `created_at`** (plan Q3): anti-starvation aging
          (`_effective_priority`) measures wait from `created_at`, so collapsing onto a fresh row
          would reset the clock and could starve a kind that sustained load keeps re-enqueueing.
          The one field a collapse may improve is `priority` — if the incoming request is more
          urgent than the waiting row, the waiting row is promoted rather than the urgency lost.

        Payload matching is on the stored JSON text, so two dicts with the same items in a
        different key order do NOT collapse. That errs toward an extra row, never a lost job."""
        blob = json.dumps(payload) if payload else None
        with self._lock:
            if kind in _IDEMPOTENT_KINDS:
                waiting = self._conn.execute(
                    "SELECT id, priority FROM jobs WHERE state = ? AND kind = ? AND payload IS ? "
                    "AND tier = ? AND num_ctx = ? ORDER BY id LIMIT 1",
                    [QUEUED, kind, blob, tier, num_ctx],
                ).fetchone()
                if waiting is not None:
                    if priority < waiting["priority"]:      # lower number = more urgent
                        self._conn.execute("UPDATE jobs SET priority = ? WHERE id = ?",
                                           [priority, waiting["id"]])
                        self._conn.commit()
                    return self.get(waiting["id"])
            cur = self._conn.execute(
                "INSERT INTO jobs (kind, tier, num_ctx, priority, state, payload, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                [kind, tier, num_ctx, priority, QUEUED, blob, _utcnow()],
            )
            self._conn.commit()
            assert cur.lastrowid is not None  # sqlite3: set after a successful INSERT
            return self.get(cur.lastrowid)

    def _effective_priority(self, job: Job, now: datetime) -> int:
        """A job's priority after anti-starvation aging (gap G6): the longer it has waited, the
        lower (better) the number — clamped at the aging floor, and never raised above a job
        already at/under the floor (so REACTIVE work is never demoted)."""
        if job.priority <= self.aging.floor:
            return job.priority
        waited = (now - datetime.fromisoformat(job.created_at)).total_seconds()
        steps = max(0, int(waited // self.aging.step_seconds))
        aged = job.priority - steps * self.aging.step
        return max(aged, self.aging.floor)

    def claim(self, *, loaded_key: tuple[str, int] | None = None,
              blocked_tiers: frozenset[str] = frozenset(),
              now: datetime | None = None) -> Job | None:
        """Select + mark RUNNING the next eligible job (§13 policy): highest EFFECTIVE priority
        first (priority + anti-starvation aging, gap G6); within the top band prefer the job
        needing no model swap (matching `loaded_key`), then FIFO; skip tiers in `blocked_tiers`
        (the foreground gate) — they stay QUEUED and are revisited once the block clears.
        Returns None if nothing is runnable now.

        Stamps `claimed_by_run = self.active_run_id` on the row it takes (extension,
        finding-0173). A supervisor that calls `sweep_orphans` at start therefore leaves the
        `running` rows TRUSTWORTHY: each one is either this run's live work or was already
        reclaimed. Without that call the stamp is NULL and `running` means only what it used to."""
        now = now or datetime.now(UTC).replace(tzinfo=None)
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM jobs WHERE state = ? ORDER BY priority, id", [QUEUED]
            ).fetchall()
            eligible = [_row_to_job(r) for r in rows if r["tier"] not in blocked_tiers]
            if not eligible:
                return None
            eff = {j.id: self._effective_priority(j, now) for j in eligible}
            top = min(eff.values())
            band = [j for j in eligible if eff[j.id] == top]
            band.sort(key=lambda j: (0 if j.load_key == loaded_key else 1, j.id))
            chosen = band[0]
            self._conn.execute(
                "UPDATE jobs SET state = ?, started_at = ?, attempts = attempts + 1, "
                "claimed_by_run = ? WHERE id = ?",
                [RUNNING, _utcnow(), self.active_run_id, chosen.id],
            )
            self._conn.commit()
            return self.get(chosen.id)

    def complete(self, job_id: int, result: str | None = None) -> None:
        self._finish(job_id, DONE, result=result)

    def fail(self, job_id: int, error: str) -> None:
        self._finish(job_id, FAILED, error=error)

    def defer(self, job_id: int, reason: str) -> None:
        """Park a job that cannot run under current conditions (e.g. ceiling breach). Not
        re-selected until `revive_deferred()` puts it back when conditions change."""
        with self._lock:
            self._conn.execute(
                "UPDATE jobs SET state = ?, error = ? WHERE id = ?", [DEFERRED, reason, job_id]
            )
            self._conn.commit()

    def revive_deferred(self) -> int:
        """Return deferred jobs to QUEUED (call when conditions change, e.g. RAM freed)."""
        with self._lock:
            cur = self._conn.execute(
                "UPDATE jobs SET state = ?, error = NULL WHERE state = ?", [QUEUED, DEFERRED]
            )
            self._conn.commit()
            return cur.rowcount

    def sweep_orphans(self, active_run_id: int) -> OrphanSweep:
        """Reclaim RUNNING rows left behind by a run that died without finishing them
        (finding-0173 — job 300246 is the live example). Idempotent kinds go back to QUEUED;
        everything else is FAILED with an explicit `error`, so stranded work is *visible* rather
        than silently pending forever. Adopts `active_run_id` as this queue's owning run, so every
        later `claim()` stamps `claimed_by_run` and a subsequent sweep can tell live from stranded.

        **Call it at supervisor start, BEFORE the first `claim()`.** That ordering is what makes it
        safe, and it is safe for two independent reasons:

        1. Run ids come from `ops.lifecycle.runs` (`INTEGER PRIMARY KEY AUTOINCREMENT`), so a
           freshly-opened run's id is greater than any id already stamped on a row — no
           pre-existing row can be mistaken for this run's work.
        2. The guard is positive, not inferential: a row is reclaimed only if its
           `claimed_by_run` is *not* `active_run_id`. A job this run actually claimed carries the
           stamp and is therefore never touched — the double-execution falsifier. A NULL stamp
           (every row written before this column existed, job 300246 included) is reclaimable
           precisely because no live run can have written it.

        `done`/`failed`/`queued`/`deferred` rows are never examined. Runs the same UPDATE-over-a-
        state-class shape as `revive_deferred`, split in two only because the two classes of kind
        land in different states. Returns what it did; empty on a clean previous exit."""
        with self._lock:
            self.active_run_id = active_run_id
            rows = self._conn.execute(
                "SELECT id, kind, claimed_by_run FROM jobs "
                "WHERE state = ? AND (claimed_by_run IS NULL OR claimed_by_run != ?)",
                [RUNNING, active_run_id],
            ).fetchall()
            requeue = tuple(r["id"] for r in rows if r["kind"] in _IDEMPOTENT_KINDS)
            strand = tuple((r["id"], r["claimed_by_run"])
                           for r in rows if r["kind"] not in _IDEMPOTENT_KINDS)
            if requeue:
                # created_at is deliberately untouched — the reclaimed job keeps the age it earned
                # (Q3). `attempts` also stands: the run that died did consume an attempt.
                self._conn.executemany(
                    "UPDATE jobs SET state = ?, started_at = NULL, claimed_by_run = NULL "
                    "WHERE id = ?",
                    [[QUEUED, job_id] for job_id in requeue],
                )
                self._conn.commit()
            for job_id, owner in strand:
                self.fail(job_id, f"orphaned by unclean exit of run #"
                                  f"{owner if owner is not None else '?'}")
            return OrphanSweep(requeued=requeue, failed=tuple(j for j, _ in strand))

    def checkpoint(self, job_id: int, token: str) -> None:
        """Persist a resume token for a checkpointed-step job, then re-queue it so the next
        unit is dispatched at a job boundary (cooperative yielding, roadmap §7)."""
        with self._lock:
            self._conn.execute(
                "UPDATE jobs SET checkpoint = ?, state = ? WHERE id = ?", [token, QUEUED, job_id]
            )
            self._conn.commit()

    def _finish(self, job_id: int, state: str, *, result: str | None = None,
                error: str | None = None) -> None:
        with self._lock:
            self._conn.execute(
                "UPDATE jobs SET state = ?, result = ?, error = ?, finished_at = ? WHERE id = ?",
                [state, result, error, _utcnow(), job_id],
            )
            self._conn.commit()

    # --- read path ---------------------------------------------------------------
    def get(self, job_id: int) -> Job:
        with self._lock:
            r = self._conn.execute("SELECT * FROM jobs WHERE id = ?", [job_id]).fetchone()
            if r is None:
                raise KeyError(f"no job {job_id}")
            return _row_to_job(r)

    def list(self, state: str | None = None) -> list[Job]:
        with self._lock:
            if state is None:
                rows = self._conn.execute("SELECT * FROM jobs ORDER BY id").fetchall()
            else:
                rows = self._conn.execute(
                    "SELECT * FROM jobs WHERE state = ? ORDER BY id", [state]
                ).fetchall()
            return [_row_to_job(r) for r in rows]

    def depth(self) -> int:
        """Number of jobs waiting to run (queue depth — a vital, §8)."""
        with self._lock:
            return self._conn.execute(
                "SELECT count(*) FROM jobs WHERE state = ?", [QUEUED]
            ).fetchone()[0]

    def counts(self) -> dict[str, int]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT state, count(*) FROM jobs GROUP BY state"
            ).fetchall()
            return {r[0]: r[1] for r in rows}

    def close(self) -> None:
        with self._lock:
            self._conn.close()
