"""bp-101 Item 1 — the additive `claimed_by_run` column and its idempotent migration.

The falsifier this file exists to fire on: **any pre-existing row's `id`, `state` or `created_at`
changing across the migration**. That would mean the migration rewrites history rather than
extending the schema, and the live `data/queue.sqlite` (302,010 lifetime rows) is not recreatable.
So the central test builds a queue file with the PRE-CHANGE schema, opens it with the current code,
and compares a digest of every row's `(id, state, created_at)` before and after.
"""

from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

from scheduler.queue import DONE, FAILED, QUEUED, RUNNING, JobQueue

# The exact `jobs` DDL as it stood before bp-101 (scheduler/queue.py:62, pre-change) — the shape a
# queue file on disk actually has. Kept verbatim rather than derived, so the test still describes
# the OLD world after the new DDL drifts further.
_PRE_CHANGE_DDL = """
CREATE TABLE IF NOT EXISTS jobs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    kind        TEXT NOT NULL,
    tier        TEXT NOT NULL,
    num_ctx     INTEGER NOT NULL,
    priority    INTEGER NOT NULL,
    state       TEXT NOT NULL,
    payload     TEXT,
    result      TEXT,
    error       TEXT,
    attempts    INTEGER NOT NULL DEFAULT 0,
    checkpoint  TEXT,
    created_at  TEXT NOT NULL,
    started_at  TEXT,
    finished_at TEXT
);
CREATE INDEX IF NOT EXISTS jobs_ready ON jobs (state, priority, id);
"""

# A miniature of the live file's state histogram (done-heavy, a queued backlog, one stranded
# `running` row = job 300246's counterpart).
_LEGACY_ROWS = [
    (1, "vault_sync", "pinned", 8192, 100, DONE, "2026-07-24T01:00:00"),
    (2, "chat_sync", "pinned", 8192, 100, DONE, "2026-07-24T01:00:05"),
    (3, "dream", "synthesis", 32768, 100, FAILED, "2026-07-24T02:00:00"),
    (4, "chat_sync", "pinned", 8192, 100, QUEUED, "2026-07-25T02:30:00"),
    (5, "vault_sync", "pinned", 8192, 100, QUEUED, "2026-07-25T02:30:01"),
    (6, "code_sync", "pinned", 8192, 100, RUNNING, "2026-07-25T03:45:07"),
]


def _write_legacy_queue(path: Path) -> None:
    conn = sqlite3.connect(str(path))
    conn.executescript(_PRE_CHANGE_DDL)
    conn.executemany(
        "INSERT INTO jobs (id, kind, tier, num_ctx, priority, state, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        _LEGACY_ROWS,
    )
    conn.commit()
    conn.close()


def _history_digest(path: Path) -> str:
    """A digest over EVERY row's `(id, state, created_at)` — the three fields the falsifier
    names. Any rewrite, renumber or state flip changes it."""
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    h = hashlib.sha256()
    for row in conn.execute("SELECT id, state, created_at FROM jobs ORDER BY id"):
        h.update(f"{row[0]}\x1f{row[1]}\x1f{row[2]}\x1e".encode())
    conn.close()
    return h.hexdigest()


def _columns(path: Path) -> list[str]:
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    cols = [r[1] for r in conn.execute("PRAGMA table_info(jobs)")]
    conn.close()
    return cols


def test_opening_a_pre_change_file_adds_the_column_and_preserves_every_row(tmp_path):
    path = tmp_path / "legacy.sqlite"
    _write_legacy_queue(path)
    before = _history_digest(path)
    assert "claimed_by_run" not in _columns(path)

    q = JobQueue(path)
    try:
        assert "claimed_by_run" in _columns(path)
        assert _history_digest(path) == before          # THE falsifier: history is untouched
        assert len(q.list()) == len(_LEGACY_ROWS)
        assert q.counts() == {DONE: 2, FAILED: 1, QUEUED: 2, RUNNING: 1}
        assert q.get(6).kind == "code_sync" and q.get(6).state == RUNNING
        assert all(job.claimed_by_run is None for job in q.list())   # legacy rows: unstamped
    finally:
        q.close()


def test_migration_is_a_no_op_on_the_second_open(tmp_path):
    path = tmp_path / "legacy.sqlite"
    _write_legacy_queue(path)

    JobQueue(path).close()
    after_first = (_history_digest(path), _columns(path))
    JobQueue(path).close()
    JobQueue(path).close()
    assert (_history_digest(path), _columns(path)) == after_first


def test_a_fresh_file_gets_the_column_from_the_ddl_not_the_migration(tmp_path):
    q = JobQueue(tmp_path / "fresh.sqlite")
    try:
        assert "claimed_by_run" in _columns(tmp_path / "fresh.sqlite")
        assert q.enqueue("librarian", "routine", 16384).claimed_by_run is None
    finally:
        q.close()


def test_claim_stamps_the_active_run_and_leaves_it_null_when_unset(tmp_path):
    unstamped = JobQueue(tmp_path / "a.sqlite")
    stamped = JobQueue(tmp_path / "b.sqlite", active_run_id=36)
    try:
        unstamped.enqueue("librarian", "routine", 16384)
        stamped.enqueue("librarian", "routine", 16384)
        plain, owned = unstamped.claim(), stamped.claim()
        assert plain is not None and owned is not None
        assert plain.claimed_by_run is None                # unchanged for every existing caller
        assert owned.claimed_by_run == 36
    finally:
        unstamped.close()
        stamped.close()


def test_pre_change_writers_and_the_new_reader_interoperate(tmp_path):
    """A row inserted by pre-change code (no `claimed_by_run` in the INSERT) is still readable and
    claimable — the column is nullable, so an older writer cannot break a newer reader."""
    path = tmp_path / "mixed.sqlite"
    _write_legacy_queue(path)
    q = JobQueue(path)
    try:
        claimed = q.claim()
        assert claimed is not None and claimed.id == 4      # the oldest QUEUED row, aging intact
        assert claimed.created_at == "2026-07-25T02:30:00"
    finally:
        q.close()
