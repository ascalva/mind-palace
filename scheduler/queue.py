# ── Family 3 boundary (guarded transition systems) · symbols in docs/NOTATION.md ──
# OBJECT:    the job-queue lifecycle — a guarded transition system with monotone anti-starvation
#            aging. Forward: QUEUED→RUNNING→DONE/FAILED/DEFERRED. Return edges (all of them):
#            RUNNING→QUEUED (checkpoint yield; orphan reclaim), DEFERRED→QUEUED (revive).
#            DONE/FAILED are terminal — nothing ever leaves them.
# INVARIANT: every transition is precondition-checked; queued jobs *eventually* run — aging
#            never lifts a job above the REACTIVE floor (liveness, G6). A RUNNING row carries the
#            deadline of the claim that minted it, and a lease lives exactly as long as its claim.
# ENFORCED:  runtime guard + test — single-writer SQLite under an RLock; AgingPolicy is a
#            no-op under normal load. Liveness is a supervisor progress guarantee, not safety.
#            The lease reaches TIER 2 + TIER 4 and no further, stated exactly (§2.6): tier 2
#            because `claim` is the sole constructor of a RUNNING row, tier 4 because an AST
#            ratchet re-derives that from this file rather than trusting the claim. NOT tier 1 —
#            SQLite cannot retrofit a CHECK without a table rewrite, which is forbidden here.
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
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
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
    claimed_by_run INTEGER,         -- ops.lifecycle.runs `runs.id` of the run that claimed it
    lease_expires_at TEXT           -- the claim's deadline; NULL = no deadline (see _MIGRATIONS)
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
# `lease_expires_at` (bp-109) is the deadline `claim()` stamps on the one row it takes, so a
# RUNNING row carries its own liveness bound instead of relying on someone remembering to sweep
# (dn-supervision-and-liveness §2.6; finding-0187 is what happens when nobody does). It is
# NULLABLE, and ⚑ **NULL means "no deadline"** — never "expired". Every one of the live file's
# pre-existing rows gets NULL on first open (job 300246 included), so a reader that read NULL as
# expired would mass-orphan the queue's entire history at migration time. That polarity is the
# single most dangerous mistake available here, which is why it is asserted by
# `deadline_lapsed` below and by `tests/unit/test_queue_leases.py` rather than merely intended.
#
# NOT done here, deliberately: finding-0170 suggests a partial UNIQUE index on
# `(kind, payload) WHERE state = 'queued'` to make coalescing structural rather than conventional.
# It cannot be created yet — the live file holds 1,766 duplicate queued rows (883 `chat_sync` +
# 883 `vault_sync`), so `CREATE UNIQUE INDEX` would raise on open and make the daemon unstartable.
# It becomes available once the restart clears those duplicates; see the journal.
_MIGRATIONS: tuple[tuple[str, str], ...] = (
    ("claimed_by_run", "ALTER TABLE jobs ADD COLUMN claimed_by_run INTEGER"),
    ("lease_expires_at", "ALTER TABLE jobs ADD COLUMN lease_expires_at TEXT"),
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


def _plus_seconds(stamp: str, seconds: float) -> str:
    """`stamp + seconds`, in the queue's own timestamp format. Wall-clock, matching `_utcnow` and
    `_effective_priority`'s arithmetic over `created_at` — a parked decision, not an oversight
    (plan §11): the deadline must be readable by a SEPARATE process (`status`), and a monotonic
    value is meaningless across processes. Named exposure: a backwards clock step makes a deadline
    look further away, so the sweep under-reports rather than over-reports. That direction is the
    safe one — an orphan missed costs a second look; an orphan invented races a live worker."""
    return (datetime.fromisoformat(stamp)
            + timedelta(seconds=seconds)).isoformat(timespec="seconds")


def deadline_lapsed(deadline: str | None, now: datetime) -> bool:
    """Has an ISO deadline passed? **The one implementation of that question**, so the polarity
    cannot drift between the two readers that ask it (this file's sweep and `status`'s
    `ops.lifecycle.snapshot.read_queue_stats`).

    ⚑ `None` ⇒ **False**. A row with no deadline is not expired, it is undeadlined — which is
    exactly what every row written before this column existed carries (`_MIGRATIONS`). Inverting
    this one line would mass-orphan 300k rows on first open. Unparseable ⇒ False for the same
    conservative reason: a reader must never *invent* an orphan, and `status` must not crash on a
    corrupt cell during the incident it exists to describe."""
    if deadline is None:
        return False
    try:
        return now >= datetime.fromisoformat(deadline)
    except ValueError:
        return False


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
    # The deadline of the claim that put this row in RUNNING. None = no deadline (an undeadlined
    # claim, or a row written before the column existed). A lease lives exactly as long as its
    # claim: `claim` sets it, and every edge that returns the row to QUEUED/DEFERRED clears it.
    lease_expires_at: str | None = None

    @property
    def load_key(self) -> tuple[str, int]:
        """The (tier, window) that must be resident to run this job. Changing either forces
        a model reload (§13), so the supervisor batches jobs sharing a load_key."""
        return (self.tier, self.num_ctx)


def lease_expired(job: Job, now: datetime) -> bool:
    """True iff this row's claim has demonstrably lapsed. NULL deadline ⇒ False (today's
    behaviour, and every row written before this column existed). The orphan question stops
    being "did someone remember to sweep?" and becomes a property of the row.

    The conjunction is the whole content of the tier-2 claim (dn-supervision-and-liveness §2.6):
    RUNNING is still *necessary* — a QUEUED row is waiting, not orphaned — but it is no longer
    *sufficient*, and the second conjunct is a fact about the clock rather than a byte some dead
    actor wrote. Gating on `state` here is also structural insurance: a leftover deadline on a
    non-RUNNING row (a writer that forgot to clear one) cannot manufacture an orphan, so the
    reader is safe even if the invariant `claim`/`checkpoint`/`defer` maintain is ever broken."""
    return job.state == RUNNING and deadline_lapsed(job.lease_expires_at, now)


@dataclass(frozen=True)
class OrphanSweep:
    """What one `sweep_orphans` pass did — the job ids it requeued and the ones it failed. Empty
    tuples mean a clean previous exit (the normal case), which is why the sweep is safe to run on
    every start.

    `lease_expired` is the third tuple and the one this pass did NOT act on: rows THIS run owns
    whose deadline has lapsed. They are reported, never reclaimed — reclaiming a row whose stamp
    says a live run holds it is the double-execution falsifier (finding-0173 / the sweep's own
    guard), and enforcement is a later plan's (dn-supervision-and-liveness §2.6; bp-109 §9). So
    `total` deliberately counts only what MOVED: it is the answer to "what did this sweep do?",
    and a reported-but-untouched row did not move."""

    requeued: tuple[int, ...] = ()
    failed: tuple[int, ...] = ()
    lease_expired: tuple[int, ...] = ()

    @property
    def total(self) -> int:
        return len(self.requeued) + len(self.failed)

    def render(self) -> str:
        lapsed = (f"; {len(self.lease_expired)} live-owned row(s) past their lease "
                  f"{sorted(self.lease_expired)} — reported, NOT reclaimed"
                  if self.lease_expired else "")
        if not self.total:
            return f"orphan sweep: nothing stranded{lapsed}"
        return (f"orphan sweep: requeued {len(self.requeued)} "
                f"{sorted(self.requeued)}, failed {len(self.failed)} "
                f"{sorted(self.failed)}{lapsed}")


def _row_to_job(r: sqlite3.Row) -> Job:
    return Job(
        id=r["id"], kind=r["kind"], tier=r["tier"], num_ctx=r["num_ctx"],
        priority=r["priority"], state=r["state"],
        payload=json.loads(r["payload"]) if r["payload"] else {},
        result=r["result"], error=r["error"], attempts=r["attempts"],
        checkpoint=r["checkpoint"], created_at=r["created_at"],
        started_at=r["started_at"], finished_at=r["finished_at"],
        claimed_by_run=r["claimed_by_run"], lease_expires_at=r["lease_expires_at"],
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
    # kind → seconds a claim of that kind may hold a row before its lease lapses. ⚑ EMPTY BY
    # DEFAULT, and empty means every claim stamps a NULL deadline — byte-for-byte today's
    # behaviour. No number is invented here: no job budget exists anywhere in the system to
    # calibrate against (finding-0178; `launcher.py` still prints "(no enforced job budget)"), and
    # the live `code_backfill` lane legitimately runs for hours, so a guessed value would kill a
    # healthy 14-hour pass on schedule — the cry-wolf disqualifier (bp-102 §10). The value is a
    # PARKED decision (bp-109 §11) whose re-entry condition is bp-112's escalation landing with a
    # measured budget; this field is the enable path that will carry it, wired but empty.
    job_budgets: Mapping[str, float] = field(default_factory=dict)

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

        Four properties make the collapse safe to reason about — the fourth is a **correction**,
        not a feature: a checkpointed row WAS a collapse target and should never have been (V6,
        read off the code in bp-105 journal CP1 and confirmed by `dn-supervision-and-liveness`
        V6 before any batch-yield protocol lands):

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
        * **A CHECKPOINTED row is not a collapse target** (`AND checkpoint IS NULL`). `checkpoint`
          re-queues a partially-advanced job with its resume token still on the row, so it sits in
          QUEUED matching every other clause of this key. Without this clause a fresh
          `enqueue("code_backfill", …)` returned that half-advanced row: the caller asked for a
          full re-derivation and was silently handed a resume from mid-pass, with nothing to
          re-derive the units the earlier pass had already claimed to cover. Like the `tier`/
          `num_ctx` narrowing this can only ever CREATE a row, never drop one — the conservative
          direction this docstring commits to in its last paragraph.

        Payload matching is on the stored JSON text, so two dicts with the same items in a
        different key order do NOT collapse. That errs toward an extra row, never a lost job."""
        blob = json.dumps(payload) if payload else None
        with self._lock:
            if kind in _IDEMPOTENT_KINDS:
                waiting = self._conn.execute(
                    "SELECT id, priority FROM jobs WHERE state = ? AND kind = ? AND payload IS ? "
                    "AND tier = ? AND num_ctx = ? AND checkpoint IS NULL ORDER BY id LIMIT 1",
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
        reclaimed. Without that call the stamp is NULL and `running` means only what it used to.

        **Also stamps the lease** (extension, dn-supervision-and-liveness §2.6). This is the queue's
        ONLY constructor of a RUNNING row — nothing else in this file writes `state = RUNNING`, a
        fact `tests/unit/test_queue_leases.py` re-derives from the AST on every run rather than
        trusting this sentence — so stamping here is what lets a reader treat an expired deadline as
        orphanhood *by definition* instead of waiting for a sweep someone must remember to call.
        `lease_expires_at = started_at + job_budgets[kind]`, computed off the same single clock read
        as `started_at` so `deadline - started_at == budget` exactly; NULL when the kind has no
        configured budget, which is every kind by default.

        Note what checkpointing buys for free: `checkpoint` clears the lease and re-queues, and the
        next `claim` stamps a fresh one, so for a yielding lane the deadline is **per batch**, not
        per job-elapsed — the shape §2.10 requires ("deadlines must be per-batch, or a healthy
        14-hour backfill dies at hour N on schedule"). A non-yielding lane gets a per-job-elapsed
        deadline, which is precisely why no budget is configured for one yet (bp-110 lands the
        yield protocol for `code_backfill`).

        The selection policy above is untouched by any of this: the stamp is written after `chosen`
        is decided, and the deadline is stamped, never ENFORCED here (§9 — a queue that terminates
        its own jobs would be the ledger written by the actor it must record)."""
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
            started = _utcnow()
            budget = self.job_budgets.get(chosen.kind)
            deadline = None if budget is None else _plus_seconds(started, budget)
            self._conn.execute(
                "UPDATE jobs SET state = ?, started_at = ?, attempts = attempts + 1, "
                "claimed_by_run = ?, lease_expires_at = ? WHERE id = ?",
                [RUNNING, started, self.active_run_id, deadline, chosen.id],
            )
            self._conn.commit()
            return self.get(chosen.id)

    def complete(self, job_id: int, result: str | None = None) -> None:
        self._finish(job_id, DONE, result=result)

    def fail(self, job_id: int, error: str) -> None:
        self._finish(job_id, FAILED, error=error)

    def defer(self, job_id: int, reason: str) -> None:
        """Park a job that cannot run under current conditions (e.g. ceiling breach). Not
        re-selected until `revive_deferred()` puts it back when conditions change.

        Called on a row `claim` has already put in RUNNING (`supervisor.py` defers on a ceiling
        breach), so it is one of the edges that ends a claim and therefore clears the lease."""
        with self._lock:
            self._conn.execute(
                "UPDATE jobs SET state = ?, error = ?, lease_expires_at = NULL WHERE id = ?",
                [DEFERRED, reason, job_id],
            )
            self._conn.commit()

    def revive_deferred(self) -> int:
        """Return deferred jobs to QUEUED (call when conditions change, e.g. RAM freed)."""
        with self._lock:
            cur = self._conn.execute(
                "UPDATE jobs SET state = ?, error = NULL, lease_expires_at = NULL WHERE state = ?",
                [QUEUED, DEFERRED],
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

        **The lease is a second, independent reason a row is orphaned — and it does NOT widen what
        this method reclaims** (extension, dn-supervision-and-liveness §2.6). For the population
        reason (2) already selects, the two reasons agree, so the deadline adds nothing the sweep
        needs. For the complement — a row stamped by THIS run — the stamp stays an absolute VETO
        that no deadline overrides, because reason (1)'s ordering argument is what protects rows
        this run actually claimed, and a lapsed deadline is not evidence that the holder is dead:
        a *hung but alive* worker has exactly that shape, and reclaiming under it would hand the
        same job to a second worker. Worse than the orphan it fixes. So such rows are counted into
        `OrphanSweep.lease_expired` and **reported**, never touched (§9: stamping is here, killing
        is a later plan's; an expired-deadline row is reported orphaned, never silently reclaimed).
        The derived-reader half of the mechanism — orphanhood visible with no sweep having run at
        all — lives in `lease_expired` above and in `ops.lifecycle.snapshot.read_queue_stats`.

        `done`/`failed`/`queued`/`deferred` rows are never examined. Runs the same UPDATE-over-a-
        state-class shape as `revive_deferred`, split in two only because the two classes of kind
        land in different states. Returns what it did; empty on a clean previous exit."""
        with self._lock:
            self.active_run_id = active_run_id
            rows = self._conn.execute(
                "SELECT id, kind, claimed_by_run, lease_expires_at, state FROM jobs "
                "WHERE state = ?", [RUNNING],
            ).fetchall()
            # The reclaim predicate, unchanged and deliberately narrow: not-this-run. Reading every
            # RUNNING row (rather than filtering in SQL) is what lets the same pass also REPORT the
            # rows it must not touch; the set it acts on is identical either way, which is the
            # property `tests/unit/test_queue_orphan_sweep.py` pins.
            stranded = [r for r in rows
                        if r["claimed_by_run"] is None or r["claimed_by_run"] != active_run_id]
            now = datetime.now(UTC).replace(tzinfo=None)
            lapsed = tuple(r["id"] for r in rows
                           if r["claimed_by_run"] == active_run_id
                           and deadline_lapsed(r["lease_expires_at"], now))
            requeue = tuple(r["id"] for r in stranded if r["kind"] in _IDEMPOTENT_KINDS)
            strand = tuple((r["id"], r["claimed_by_run"])
                           for r in stranded if r["kind"] not in _IDEMPOTENT_KINDS)
            if requeue:
                # created_at is deliberately untouched — the reclaimed job keeps the age it earned
                # (Q3). `attempts` also stands: the run that died did consume an attempt. The lease
                # goes because the claim that minted it is over: a QUEUED row holds no claim, so it
                # must hold no deadline.
                self._conn.executemany(
                    "UPDATE jobs SET state = ?, started_at = NULL, claimed_by_run = NULL, "
                    "lease_expires_at = NULL WHERE id = ?",
                    [[QUEUED, job_id] for job_id in requeue],
                )
                self._conn.commit()
            for job_id, owner in strand:
                self.fail(job_id, f"orphaned by unclean exit of run #"
                                  f"{owner if owner is not None else '?'}")
            return OrphanSweep(requeued=requeue, failed=tuple(j for j, _ in strand),
                               lease_expired=lapsed)

    def checkpoint(self, job_id: int, token: str) -> None:
        """Persist a resume token for a checkpointed-step job, then re-queue it so the next
        unit is dispatched at a job boundary (cooperative yielding, roadmap §7).

        **Clears the lease**, which is what stops a checkpointed row from reading as an orphan: the
        claim that minted the deadline ended when the handler yielded, and the row is now waiting,
        not running. `claim` stamps a fresh deadline on the next batch, so a yielding lane's bound
        is per-batch (see `claim`). A row left QUEUED with a stale deadline would be a lie the
        derived reader has to be defended against instead of one the writer never tells — and
        `enqueue` no longer collapses onto this row either (V6, the fourth property there)."""
        with self._lock:
            self._conn.execute(
                "UPDATE jobs SET checkpoint = ?, state = ?, lease_expires_at = NULL WHERE id = ?",
                [token, QUEUED, job_id],
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
