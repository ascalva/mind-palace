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
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Lower number = higher priority. Reactive/watchdog escalations use REACTIVE.
PRIORITY_REACTIVE = 0
PRIORITY_INTERACTIVE = 10
PRIORITY_DEFAULT = 50
PRIORITY_BACKGROUND = 100

QUEUED, RUNNING, DONE, FAILED, DEFERRED = "queued", "running", "done", "failed", "deferred"

_DDL = """
CREATE TABLE IF NOT EXISTS jobs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    kind        TEXT NOT NULL,
    tier        TEXT NOT NULL,
    num_ctx     INTEGER NOT NULL,
    priority    INTEGER NOT NULL,
    state       TEXT NOT NULL,
    payload     TEXT,            -- JSON
    result      TEXT,
    error       TEXT,
    attempts    INTEGER NOT NULL DEFAULT 0,
    checkpoint  TEXT,            -- resume token for checkpointed-step jobs
    created_at  TEXT NOT NULL,
    started_at  TEXT,
    finished_at TEXT
);
CREATE INDEX IF NOT EXISTS jobs_ready ON jobs (state, priority, id);
"""


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

    @property
    def load_key(self) -> tuple[str, int]:
        """The (tier, window) that must be resident to run this job. Changing either forces
        a model reload (§13), so the supervisor batches jobs sharing a load_key."""
        return (self.tier, self.num_ctx)


def _row_to_job(r: sqlite3.Row) -> Job:
    return Job(
        id=r["id"], kind=r["kind"], tier=r["tier"], num_ctx=r["num_ctx"],
        priority=r["priority"], state=r["state"],
        payload=json.loads(r["payload"]) if r["payload"] else {},
        result=r["result"], error=r["error"], attempts=r["attempts"],
        checkpoint=r["checkpoint"], created_at=r["created_at"],
        started_at=r["started_at"], finished_at=r["finished_at"],
    )


@dataclass
class JobQueue:
    path: Path

    def __post_init__(self) -> None:
        if str(self.path) != ":memory:":
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.path))
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._conn.executescript(_DDL)
        self._conn.commit()

    # --- write path (supervisor-owned) -------------------------------------------
    def enqueue(self, kind: str, tier: str, num_ctx: int, *,
                priority: int = PRIORITY_DEFAULT,
                payload: dict[str, Any] | None = None) -> Job:
        cur = self._conn.execute(
            "INSERT INTO jobs (kind, tier, num_ctx, priority, state, payload, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            [kind, tier, num_ctx, priority, QUEUED,
             json.dumps(payload) if payload else None, _utcnow()],
        )
        self._conn.commit()
        return self.get(int(cur.lastrowid))

    def claim(self, *, loaded_key: tuple[str, int] | None = None,
              blocked_tiers: frozenset[str] = frozenset()) -> Job | None:
        """Select + mark RUNNING the next eligible job (§13 policy): highest priority first;
        within the top-priority band prefer the job needing no model swap (matching
        `loaded_key`), then FIFO; skip tiers in `blocked_tiers` (the foreground gate). They
        stay QUEUED and are revisited once the block clears. Returns None if nothing is
        runnable now."""
        rows = self._conn.execute(
            "SELECT * FROM jobs WHERE state = ? ORDER BY priority, id", [QUEUED]
        ).fetchall()
        eligible = [_row_to_job(r) for r in rows if r["tier"] not in blocked_tiers]
        if not eligible:
            return None
        top = min(j.priority for j in eligible)
        band = [j for j in eligible if j.priority == top]
        band.sort(key=lambda j: (0 if j.load_key == loaded_key else 1, j.id))
        chosen = band[0]
        self._conn.execute(
            "UPDATE jobs SET state = ?, started_at = ?, attempts = attempts + 1 WHERE id = ?",
            [RUNNING, _utcnow(), chosen.id],
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
        self._conn.execute(
            "UPDATE jobs SET state = ?, error = ? WHERE id = ?", [DEFERRED, reason, job_id]
        )
        self._conn.commit()

    def revive_deferred(self) -> int:
        """Return deferred jobs to QUEUED (call when conditions change, e.g. RAM freed)."""
        cur = self._conn.execute(
            "UPDATE jobs SET state = ?, error = NULL WHERE state = ?", [QUEUED, DEFERRED]
        )
        self._conn.commit()
        return cur.rowcount

    def checkpoint(self, job_id: int, token: str) -> None:
        """Persist a resume token for a checkpointed-step job, then re-queue it so the next
        unit is dispatched at a job boundary (cooperative yielding, roadmap §7)."""
        self._conn.execute(
            "UPDATE jobs SET checkpoint = ?, state = ? WHERE id = ?", [token, QUEUED, job_id]
        )
        self._conn.commit()

    def _finish(self, job_id: int, state: str, *, result: str | None = None,
                error: str | None = None) -> None:
        self._conn.execute(
            "UPDATE jobs SET state = ?, result = ?, error = ?, finished_at = ? WHERE id = ?",
            [state, result, error, _utcnow(), job_id],
        )
        self._conn.commit()

    # --- read path ---------------------------------------------------------------
    def get(self, job_id: int) -> Job:
        r = self._conn.execute("SELECT * FROM jobs WHERE id = ?", [job_id]).fetchone()
        if r is None:
            raise KeyError(f"no job {job_id}")
        return _row_to_job(r)

    def list(self, state: str | None = None) -> list[Job]:
        if state is None:
            rows = self._conn.execute("SELECT * FROM jobs ORDER BY id").fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM jobs WHERE state = ? ORDER BY id", [state]
            ).fetchall()
        return [_row_to_job(r) for r in rows]

    def depth(self) -> int:
        """Number of jobs waiting to run (queue depth — a vital, §8)."""
        return self._conn.execute(
            "SELECT count(*) FROM jobs WHERE state = ?", [QUEUED]
        ).fetchone()[0]

    def counts(self) -> dict[str, int]:
        rows = self._conn.execute("SELECT state, count(*) FROM jobs GROUP BY state").fetchall()
        return {r[0]: r[1] for r in rows}

    def close(self) -> None:
        self._conn.close()
