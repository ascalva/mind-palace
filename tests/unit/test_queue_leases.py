"""bp-109 — a RUNNING row carries its own deadline (dn-supervision-and-liveness §2.6).

Four falsifiers live in this file, one per item, and each is named where it is asserted:

* **Item 1** — *any pre-existing row differs after the migration.* `data/queue.sqlite` carries
  302,010 lifetime rows and is never recreated, so a migration that touches one of them is
  unrecoverable. Asserted against a file built with the pre-change DDL and digested row-by-row over
  every pre-change column.
* **Item 1, the polarity** — ⚑ *a NULL deadline read as expired.* Every pre-existing row gets NULL
  on first open, so inverting that one comparison mass-orphans the queue's whole history at
  migration time. `deadline_lapsed(None, …)` is False, and a legacy RUNNING row (job 300246's
  counterpart) is asserted NOT orphaned.
* **Item 2** — *a RUNNING row minted after this item with a NULL deadline where a budget exists.*
  That is the tier-2 claim failing at its only constructor.
* **Item 5** — ⚑ *a second `state = RUNNING` writer leaves the ratchet green.* The scan is exercised
  against synthetic sources that place the second writer exactly where a naive walk would miss it:
  inside a nested function, and with `state` in second position in the SET clause.

The lease's own liveness rule, asserted here rather than trusted: **a lease lives exactly as long
as the claim that minted it.** `claim` sets it; `checkpoint`, `defer`, `revive_deferred` and the
sweep's requeue all clear it. So no QUEUED or DEFERRED row ever carries a deadline, and a
checkpointed row — which is QUEUED with its resume token still on it — cannot read as an orphan.
"""

from __future__ import annotations

import ast
import hashlib
import random
import re
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from ops.lifecycle.snapshot import read_queue_stats
from scheduler.queue import (
    DEFERRED,
    DONE,
    FAILED,
    QUEUED,
    RUNNING,
    JobQueue,
    deadline_lapsed,
    lease_expired,
)

LIVE_RUN = 36
DEAD_RUN = 35

# The `jobs` DDL as it stood BEFORE this plan (bp-101's shape: `claimed_by_run` present,
# `lease_expires_at` absent) — the shape a queue file written by the previous release has. Kept
# verbatim rather than derived from `_DDL`, so this test still describes the OLD world after the
# current DDL drifts further.
_PRE_CHANGE_DDL = """
CREATE TABLE IF NOT EXISTS jobs (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    kind           TEXT NOT NULL,
    tier           TEXT NOT NULL,
    num_ctx        INTEGER NOT NULL,
    priority       INTEGER NOT NULL,
    state          TEXT NOT NULL,
    payload        TEXT,
    result         TEXT,
    error          TEXT,
    attempts       INTEGER NOT NULL DEFAULT 0,
    checkpoint     TEXT,
    created_at     TEXT NOT NULL,
    started_at     TEXT,
    finished_at    TEXT,
    claimed_by_run INTEGER
);
CREATE INDEX IF NOT EXISTS jobs_ready ON jobs (state, priority, id);
"""

# Every column that existed before this plan. The falsifier is "any pre-existing row DIFFERS", so
# the digest covers all of them, not just the three the bp-101 test named.
_PRE_CHANGE_COLUMNS = ("id", "kind", "tier", "num_ctx", "priority", "state", "payload", "result",
                       "error", "attempts", "checkpoint", "created_at", "started_at",
                       "finished_at", "claimed_by_run")

# A miniature of the live file's histogram: done-heavy, a queued backlog, and one stranded RUNNING
# row with no owning run — job 300246, which after this migration must have a NULL deadline and
# therefore must NOT read as lease-orphaned.
_LEGACY_ROWS = [
    (1, "vault_sync", "pinned", 8192, 100, DONE, "2026-07-24T01:00:00", 3, None),
    (2, "chat_sync", "pinned", 8192, 100, DONE, "2026-07-24T01:00:05", 1, None),
    (3, "dream", "synthesis", 32768, 100, FAILED, "2026-07-24T02:00:00", 2, 34),
    (4, "chat_sync", "pinned", 8192, 100, QUEUED, "2026-07-25T02:30:00", 0, None),
    (5, "vault_sync", "pinned", 8192, 100, QUEUED, "2026-07-25T02:30:01", 0, None),
    (6, "code_sync", "pinned", 8192, 100, RUNNING, "2026-07-25T03:45:07", 1, None),
]


def _write_legacy_queue(path: Path) -> None:
    conn = sqlite3.connect(str(path))
    conn.executescript(_PRE_CHANGE_DDL)
    conn.executemany(
        "INSERT INTO jobs (id, kind, tier, num_ctx, priority, state, created_at, attempts, "
        "claimed_by_run) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        _LEGACY_ROWS,
    )
    conn.commit()
    conn.close()


def _history_digest(path: Path) -> str:
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    h = hashlib.sha256()
    for row in conn.execute(f"SELECT {', '.join(_PRE_CHANGE_COLUMNS)} FROM jobs ORDER BY id"):
        h.update(("\x1f".join("" if v is None else str(v) for v in row) + "\x1e").encode())
    conn.close()
    return h.hexdigest()


def _columns(path: Path) -> list[str]:
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    cols = [r[1] for r in conn.execute("PRAGMA table_info(jobs)")]
    conn.close()
    return cols


@pytest.fixture
def q(tmp_path):
    queue = JobQueue(tmp_path / "q.sqlite")
    yield queue
    queue.close()


# =================================================================================================
# Item 1 — the additive column
# =================================================================================================

def test_opening_a_pre_change_file_adds_the_column_and_changes_no_row(tmp_path):
    """THE FALSIFIER for Item 1: the digest over every pre-change column of every row must be
    byte-identical across the migration."""
    path = tmp_path / "legacy.sqlite"
    _write_legacy_queue(path)
    before = _history_digest(path)
    assert "lease_expires_at" not in _columns(path)

    queue = JobQueue(path)
    try:
        assert "lease_expires_at" in _columns(path)
        assert _history_digest(path) == before
        assert len(queue.list()) == len(_LEGACY_ROWS)
        assert queue.counts() == {DONE: 2, FAILED: 1, QUEUED: 2, RUNNING: 1}
        # id / state / created_at / attempts, spelled out per the plan's acceptance wording.
        for row, job in zip(_LEGACY_ROWS, queue.list(), strict=True):
            assert (job.id, job.state, job.created_at, job.attempts) == (row[0], row[5], row[6],
                                                                        row[7])
        assert all(job.lease_expires_at is None for job in queue.list())
    finally:
        queue.close()


def test_the_migration_is_a_no_op_on_every_later_open(tmp_path):
    path = tmp_path / "legacy.sqlite"
    _write_legacy_queue(path)
    JobQueue(path).close()
    after_first = (_history_digest(path), _columns(path))
    JobQueue(path).close()
    JobQueue(path).close()
    assert (_history_digest(path), _columns(path)) == after_first


def test_a_fresh_file_gets_the_column_from_the_ddl_not_the_migration(tmp_path):
    """`_DDL` and `_MIGRATIONS` must agree, or a fresh file and a migrated file diverge in shape.
    Compared as SETS of columns because the DDL puts the column in a different ordinal position
    than `ALTER TABLE … ADD COLUMN` does."""
    fresh, legacy = tmp_path / "fresh.sqlite", tmp_path / "legacy.sqlite"
    JobQueue(fresh).close()
    _write_legacy_queue(legacy)
    JobQueue(legacy).close()
    assert set(_columns(fresh)) == set(_columns(legacy))
    assert "lease_expires_at" in _columns(fresh)


def test_a_legacy_running_row_is_not_orphaned_by_the_migration(tmp_path):
    """⚑ THE POLARITY FALSIFIER. Job 300246's counterpart is RUNNING with a NULL deadline after the
    migration. If NULL read as *expired*, every one of the live file's 302,010 rows would be
    reinterpreted the instant the daemon next opened the file — 300k invented orphans."""
    path = tmp_path / "legacy.sqlite"
    _write_legacy_queue(path)
    queue = JobQueue(path)
    try:
        stranded = queue.get(6)
        assert stranded.state == RUNNING and stranded.lease_expires_at is None
        assert lease_expired(stranded, datetime(2030, 1, 1)) is False
    finally:
        queue.close()
    assert read_queue_stats(path, now=datetime(2030, 1, 1)).orphaned_running == ()


# =================================================================================================
# Item 2 — `claim()` stamps the deadline at the single RUNNING constructor
# =================================================================================================

def test_claim_stamps_the_deadline_from_the_configured_budget(tmp_path):
    """The deadline is `started_at + budget`, asserted against the row's OWN clock read rather than
    against `datetime.now()` — that is the property `claim` actually maintains (one clock read
    serves both columns), and it is exact rather than tolerance-bounded."""
    queue = JobQueue(tmp_path / "q.sqlite", job_budgets={"chat_sync": 900.0})
    try:
        queue.enqueue("chat_sync", "pinned", 8192)
        claimed = queue.claim()
        assert claimed is not None and claimed.state == RUNNING
        assert claimed.started_at is not None and claimed.lease_expires_at is not None
        assert (datetime.fromisoformat(claimed.lease_expires_at)
                - datetime.fromisoformat(claimed.started_at)) == timedelta(seconds=900)
        # …and it round-trips through `_row_to_job` on a fresh read, not just on `claim`'s return.
        assert queue.get(claimed.id).lease_expires_at == claimed.lease_expires_at
    finally:
        queue.close()


def test_a_kind_with_no_configured_budget_is_claimed_with_a_null_deadline(tmp_path):
    """The default, and the reason it is safe: `job_budgets` is empty unless a caller fills it, so
    every claim today stamps NULL and the queue behaves exactly as it did before this plan. No
    number is invented (plan §3 Q7 / §11)."""
    queue = JobQueue(tmp_path / "q.sqlite", job_budgets={"chat_sync": 900.0})
    try:
        queue.enqueue("code_backfill", "pinned", 8192)
        claimed = queue.claim()
        assert claimed is not None and claimed.lease_expires_at is None
        assert lease_expired(claimed, datetime(2030, 1, 1)) is False
    finally:
        queue.close()


def test_the_default_queue_stamps_no_deadline_at_all(q):
    q.enqueue("chat_sync", "pinned", 8192)
    claimed = q.claim()
    assert claimed is not None and claimed.lease_expires_at is None
    assert q.job_budgets == {}


def test_the_selection_policy_is_unchanged_by_the_stamp(tmp_path):
    """Item 2's invariant: effective priority → swap-avoidance → FIFO, untouched. A budgeted queue
    and an unbudgeted one must claim the SAME jobs in the SAME order."""
    order = []
    for budgets in ({}, {"chat_sync": 60.0, "dream": 60.0, "librarian": 60.0}):
        queue = JobQueue(tmp_path / f"q{len(budgets)}.sqlite", job_budgets=budgets)
        try:
            queue.enqueue("dream", "synthesis", 32768, priority=100)
            queue.enqueue("chat_sync", "pinned", 8192, priority=10)
            queue.enqueue("librarian", "routine", 16384, priority=50)
            picked = []
            while (job := queue.claim(loaded_key=("routine", 16384))) is not None:
                picked.append((job.kind, job.priority))
                queue.complete(job.id)
            order.append(picked)
        finally:
            queue.close()
    assert order[0] == order[1] == [("chat_sync", 10), ("librarian", 50), ("dream", 100)]


def test_a_re_claim_after_a_checkpoint_gets_a_fresh_deadline(tmp_path):
    """Why a yielding lane's deadline is PER BATCH and not per job-elapsed (§2.10's requirement):
    the token survives the yield, the deadline does not, and the next claim re-stamps."""
    queue = JobQueue(tmp_path / "q.sqlite", job_budgets={"code_backfill": 300.0})
    try:
        queue.enqueue("code_backfill", "pinned", 8192)
        first = queue.claim()
        assert first is not None and first.lease_expires_at is not None
        queue.checkpoint(first.id, "cursor:1000")

        yielded = queue.get(first.id)
        assert yielded.state == QUEUED
        assert yielded.checkpoint == "cursor:1000"          # the token survives …
        assert yielded.lease_expires_at is None             # … the lease does not

        second = queue.claim()
        assert second is not None and second.id == first.id
        assert second.lease_expires_at is not None
        assert (datetime.fromisoformat(second.lease_expires_at)
                - datetime.fromisoformat(second.started_at or "")) == timedelta(seconds=300)
    finally:
        queue.close()


# =================================================================================================
# Item 3 — readers derive orphanhood instead of trusting `state`
# =================================================================================================

def test_deadline_lapsed_is_the_one_polarity_rule(q):
    now = datetime(2026, 7, 26, 12, 0, 0)
    assert deadline_lapsed(None, now) is False                       # ⚑ NULL is never expired
    assert deadline_lapsed("2026-07-26T11:59:59", now) is True
    assert deadline_lapsed("2026-07-26T12:00:00", now) is True       # at the deadline, it is up
    assert deadline_lapsed("2026-07-26T12:00:01", now) is False
    assert deadline_lapsed("not-a-timestamp", now) is False          # never invent an orphan
    assert deadline_lapsed("", now) is False


def test_lease_expired_needs_running_as_well_as_a_lapsed_clock(q):
    """RUNNING is necessary but no longer sufficient — and a stale deadline on a row that is NOT
    running cannot manufacture an orphan even if some writer forgets to clear it."""
    job = q.enqueue("chat_sync", "pinned", 8192)
    q._conn.execute("UPDATE jobs SET lease_expires_at = ? WHERE id = ?",
                    ["2020-01-01T00:00:00", job.id])
    q._conn.commit()
    now = datetime(2026, 7, 26, 12, 0, 0)

    waiting = q.get(job.id)
    assert waiting.state == QUEUED
    assert deadline_lapsed(waiting.lease_expires_at, now) is True    # the clock says yes …
    assert lease_expired(waiting, now) is False                     # … the conjunction says no

    q._conn.execute("UPDATE jobs SET state = ? WHERE id = ?", [RUNNING, job.id])
    q._conn.commit()
    assert lease_expired(q.get(job.id), now) is True


def _seed_running(path: Path, *, deadline: str | None, owner: int | None = LIVE_RUN,
                  kind: str = "code_backfill", started: str = "2026-07-26T10:00:00") -> int:
    """A RUNNING row with an explicit deadline, written through the real schema."""
    queue = JobQueue(path)
    job = queue.enqueue(kind, "pinned", 8192)
    queue._conn.execute(
        "UPDATE jobs SET state = ?, started_at = ?, claimed_by_run = ?, lease_expires_at = ? "
        "WHERE id = ?", [RUNNING, started, owner, deadline, job.id])
    queue._conn.commit()
    queue.close()
    return job.id


def test_an_elapsed_deadline_reads_as_orphaned_with_no_sweep_having_run(tmp_path):
    """THE ITEM 3 ACCEPTANCE TEST. No `sweep_orphans` call appears anywhere in this test: the row
    is orphaned because of what it says about itself, which is the whole inversion (§2.6)."""
    path = tmp_path / "q.sqlite"
    job_id = _seed_running(path, deadline="2026-07-26T10:30:00")

    stats = read_queue_stats(path, now=datetime(2026, 7, 26, 11, 0, 0))

    assert [j.id for j in stats.running] == [job_id]
    assert [j.id for j in stats.orphaned_running] == [job_id]
    assert stats.running[0].lease_expired is True
    assert stats.running[0].lease_expires_at == "2026-07-26T10:30:00"


def test_a_deadline_still_in_the_future_is_not_orphaned(tmp_path):
    path = tmp_path / "q.sqlite"
    _seed_running(path, deadline="2026-07-26T23:00:00")
    stats = read_queue_stats(path, now=datetime(2026, 7, 26, 11, 0, 0))
    assert stats.running and stats.orphaned_running == ()
    assert stats.running[0].lease_expired is False


def test_a_null_deadline_running_row_behaves_exactly_as_today(tmp_path):
    """The third clause of Item 3's acceptance. A row with no deadline is reported RUNNING with its
    elapsed and nothing else — byte-for-byte the pre-change reading, however old it is."""
    path = tmp_path / "q.sqlite"
    _seed_running(path, deadline=None)
    stats = read_queue_stats(path, now=datetime(2030, 1, 1))
    assert len(stats.running) == 1
    assert stats.running[0].lease_expired is False
    assert stats.running[0].lease_expires_at is None
    assert stats.orphaned_running == ()
    assert stats.running[0].elapsed_s is not None and stats.running[0].elapsed_s > 0


def test_status_still_reads_a_queue_file_that_predates_the_column(tmp_path):
    """`status` is opened `mode=ro` and cannot migrate, so it must tolerate a file whose daemon has
    not restarted since this plan landed — which is the state of the live file right now. Reported
    as un-deadlined, never as expired, and never as a crash."""
    path = tmp_path / "legacy.sqlite"
    _write_legacy_queue(path)
    stats = read_queue_stats(path, now=datetime(2030, 1, 1))
    assert stats.exists is True and stats.depth == 2
    assert [j.id for j in stats.running] == [6]
    assert stats.running[0].lease_expires_at is None
    assert stats.running[0].lease_expired is False
    assert stats.orphaned_running == ()


def test_the_status_read_stays_bounded_and_read_only_over_the_new_column(tmp_path):
    """bp-102's cost falsifier, re-asserted for the added projection: the extra column must not
    turn a bounded metadata read into a scan, and it must not create or mutate anything."""
    path = tmp_path / "q.sqlite"
    _seed_running(path, deadline="2026-07-26T10:30:00")
    queue = JobQueue(path)
    try:
        for _ in range(500):
            queue.enqueue("dream", "synthesis", 32768)
    finally:
        queue.close()
    stats = read_queue_stats(path, now=datetime(2026, 7, 26, 11, 0, 0))
    assert stats.rows_read <= 24                 # bp-102's MAX_ROWS_READ, over 501 rows
    assert stats.depth == 500 and len(stats.orphaned_running) == 1
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        with pytest.raises(sqlite3.OperationalError):
            conn.execute("UPDATE jobs SET lease_expires_at = NULL")
    finally:
        conn.close()


# =================================================================================================
# The lease's liveness rule — it lives exactly as long as the claim that minted it
# =================================================================================================

def _lease_of(queue: JobQueue, job_id: int) -> str | None:
    return queue.get(job_id).lease_expires_at


def test_no_waiting_or_deferred_row_ever_carries_a_deadline(tmp_path):
    """Enumerated over EVERY edge that ends a claim without finishing the job: checkpoint yield,
    orphan reclaim, ceiling defer, and the revive that follows it. A QUEUED row holds no claim, so
    it must hold no deadline — that is what makes a checkpointed row stop being an orphan."""
    queue = JobQueue(tmp_path / "q.sqlite", job_budgets={"code_backfill": 60.0, "chat_sync": 60.0,
                                                        "vault_sync": 60.0})
    try:
        # (a) checkpoint yield
        queue.enqueue("code_backfill", "pinned", 8192)
        yielded = queue.claim()
        assert yielded is not None and _lease_of(queue, yielded.id) is not None
        queue.checkpoint(yielded.id, "cursor:1")
        assert _lease_of(queue, yielded.id) is None

        # (b) ceiling defer, then revive
        queue.enqueue("chat_sync", "pinned", 8192)
        deferred = queue.claim()
        assert deferred is not None and _lease_of(queue, deferred.id) is not None
        queue.defer(deferred.id, "ceiling: 2 resident")
        assert queue.get(deferred.id).state == DEFERRED
        assert _lease_of(queue, deferred.id) is None
        queue.revive_deferred()
        assert _lease_of(queue, deferred.id) is None

        # (c) orphan reclaim
        queue.enqueue("vault_sync", "pinned", 8192)
        queue.sweep_orphans(LIVE_RUN)
        stranded = queue.claim()
        assert stranded is not None and _lease_of(queue, stranded.id) is not None
        queue._conn.execute("UPDATE jobs SET claimed_by_run = ? WHERE id = ?",
                            [DEAD_RUN, stranded.id])
        queue._conn.commit()
        assert queue.sweep_orphans(LIVE_RUN).requeued == (stranded.id,)
        assert queue.get(stranded.id).state == QUEUED
        assert _lease_of(queue, stranded.id) is None

        for job in queue.list():
            if job.state in (QUEUED, DEFERRED):
                assert job.lease_expires_at is None, f"job {job.id} ({job.state}) kept a lease"
    finally:
        queue.close()


# =================================================================================================
# Item 5 — the ratchet the tier-4 claim rests on
# =================================================================================================

_QUEUE_SOURCE = Path(__file__).resolve().parents[2] / "scheduler" / "queue.py"
_EXECUTORS = {"execute", "executemany", "executescript"}


def _strings_in(node: ast.AST) -> list[str]:
    return [n.value for n in ast.walk(node) if isinstance(n, ast.Constant)
            and isinstance(n.value, str)]


def _writes_state(call: ast.Call) -> bool:
    """Does this DB call write the `state` column? Matched on the SQL text, and deliberately NOT
    anchored to `state` being the FIRST assignment in the SET clause: `UPDATE jobs SET error = ?,
    state = ?` is the shape a mutation would take to slip past a naive prefix match."""
    sql = " ".join(" ".join(_strings_in(call)).upper().split())
    if "UPDATE JOBS" in sql and re.search(r"\bSTATE\s*=", sql):
        return True
    return "INSERT INTO JOBS" in sql and bool(re.search(r"\bSTATE\b", sql))


def _mentions_running(call: ast.Call) -> bool:
    """Does the call bind the RUNNING constant (or the raw literal) as a parameter?"""
    for node in ast.walk(call):
        if isinstance(node, ast.Name) and node.id == "RUNNING":
            return True
        if isinstance(node, ast.Constant) and node.value == RUNNING:
            return True
    return False


def _is_executor(func: ast.expr) -> bool:
    return isinstance(func, ast.Attribute) and func.attr in _EXECUTORS


def running_writers(source: str) -> set[str]:
    """The name of every function that constructs a `state = RUNNING` row, read off the AST.

    Walks the WHOLE module, not just module-level defs, and resolves each hit to its innermost
    enclosing function — bp-106 Item 4 records that a module-level-only walk reproduces the hole it
    is meant to close, so a writer buried in a nested helper must be caught here."""
    tree = ast.parse(source)
    parents: dict[ast.AST, ast.AST] = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[child] = node

    writers: set[str] = set()
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and _is_executor(node.func)):
            continue
        if not (_writes_state(node) and _mentions_running(node)):
            continue
        cur: ast.AST | None = parents.get(node)
        name = "<module>"
        while cur is not None:
            if isinstance(cur, ast.FunctionDef | ast.AsyncFunctionDef):
                name = cur.name
                break
            cur = parents.get(cur)
        writers.add(name)
    return writers


def test_claim_is_the_only_constructor_of_a_running_row():
    """⚑ THE TIER-2 RATCHET. The note claims tier 2 *because* `claim()` is the sole RUNNING
    constructor; this re-derives that from the file on every run, so a second constructor added
    later fails the gate instead of quietly invalidating the claim."""
    assert running_writers(_QUEUE_SOURCE.read_text()) == {"claim"}


@pytest.mark.parametrize("mutant,where", [
    # A plain second writer in another method.
    ("""
class JobQueue:
    def revive_deferred(self):
        self._conn.execute("UPDATE jobs SET state = ? WHERE id = ?", [RUNNING, 1])
""", "revive_deferred"),
    # `state` is not the first column in the SET clause — a prefix match would miss it.
    ("""
class JobQueue:
    def resurrect(self):
        self._conn.execute("UPDATE jobs SET error = NULL, state = ? WHERE id = ?", [RUNNING, 1])
""", "resurrect"),
    # FUNCTION-LOCAL: the writer lives in a nested helper, the hole bp-106 Item 4 names.
    ("""
class JobQueue:
    def adopt(self):
        def _inner(job_id):
            self._conn.execute("UPDATE jobs SET state = ? WHERE id = ?", [RUNNING, job_id])
        _inner(1)
""", "_inner"),
    # The raw literal instead of the constant.
    ("""
class JobQueue:
    def sneak(self):
        self._conn.executemany("UPDATE jobs SET state = ? WHERE id = ?", [["running", 1]])
""", "sneak"),
    # An INSERT that mints a RUNNING row outright.
    ("""
class JobQueue:
    def inject(self):
        self._conn.execute(
            "INSERT INTO jobs (kind, tier, num_ctx, priority, state, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)", ["x", "pinned", 8192, 50, RUNNING, "2026-01-01T00:00:00"])
""", "inject"),
])
def test_the_ratchet_reddens_on_a_planted_second_writer(mutant, where):
    """⚑ ITEM 5'S FALSIFIER, run as a test rather than promised in a comment: the scan is fed the
    real file plus a planted writer, and must report it. If any of these passed, the ratchet would
    be decorative — a rule with no mechanical enforcement is not a rule."""
    found = running_writers(_QUEUE_SOURCE.read_text() + mutant)
    assert where in found
    assert found != {"claim"}


def test_the_ratchet_does_not_fire_on_a_reader_or_on_another_state(tmp_path):
    """The other direction: the scan must not flag the sweep's SELECT (which names RUNNING but
    writes nothing) or a writer that moves a row to some other state. A ratchet that fires on
    everything gets deleted."""
    assert running_writers("""
class JobQueue:
    def reads(self):
        self._conn.execute("SELECT id FROM jobs WHERE state = ?", [RUNNING])
    def writes_queued(self):
        self._conn.execute("UPDATE jobs SET state = ? WHERE id = ?", [QUEUED, 1])
""") == set()


def test_every_running_row_minted_under_an_interleaving_carries_a_deadline(tmp_path):
    """Item 5(b): an arbitrary (seeded, so reproducible) interleaving of enqueue / claim /
    checkpoint / sweep / complete. Every row observed RUNNING must carry a deadline, and no QUEUED
    row may carry one — the two halves of the invariant, checked after every single operation."""
    kinds = ["chat_sync", "vault_sync", "code_backfill", "dream", "librarian"]
    queue = JobQueue(tmp_path / "q.sqlite", job_budgets=dict.fromkeys(kinds, 120.0))
    rng = random.Random(1109)
    seen_running = 0
    try:
        queue.sweep_orphans(LIVE_RUN)
        for _ in range(300):
            op = rng.choice(["enqueue", "claim", "checkpoint", "sweep", "complete", "defer"])
            if op == "enqueue":
                queue.enqueue(rng.choice(kinds), "pinned", 8192,
                              priority=rng.choice([0, 10, 50, 100]))
            elif op == "claim":
                queue.claim()
            elif op == "sweep":
                queue.sweep_orphans(LIVE_RUN)
            else:
                running = queue.list(RUNNING)
                if running:
                    target = rng.choice(running)
                    if op == "checkpoint":
                        queue.checkpoint(target.id, "cursor")
                    elif op == "complete":
                        queue.complete(target.id, "ok")
                    else:
                        queue.defer(target.id, "ceiling")
            for job in queue.list():
                if job.state == RUNNING:
                    seen_running += 1
                    assert job.lease_expires_at is not None, f"undeadlined RUNNING row {job.id}"
                elif job.state in (QUEUED, DEFERRED):
                    assert job.lease_expires_at is None, f"waiting row {job.id} kept a lease"
        assert seen_running > 0, "the interleaving never produced a RUNNING row — vacuous"
    finally:
        queue.close()
