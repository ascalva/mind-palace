"""The run ledger — every supervised run pinned to a git commit (operational lifecycle).

The system's state (corpus, vectors, queue, ledgers, secrets) already persists in stores +
files, so a normal restart just resumes. What was MISSING is an operational record of the runs
themselves: *which commit* executed, when it started/stopped, and — crucially — whether it shut
down **cleanly**. That last bit is the basis for recovery mode (nervous-system-and-ambassador.md
§1): a previous run that never marked itself stopped (killed -9, panic, power loss) means the
next start should come up cautious rather than assume consistency.

A small dedicated SQLite (`data/runs.sqlite`), the same pattern as the other state stores. It is
append-mostly: `open_run` inserts; `mark_stopped` closes the row. A row with `stopped_at IS NULL`
is either the live run or a crashed one — `last_was_clean()` distinguishes by recency.
"""

from __future__ import annotations

import sqlite3
import subprocess
import threading
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from config.loader import Config

_DDL = """
CREATE TABLE IF NOT EXISTS runs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    commit_sha      TEXT NOT NULL,
    dirty           INTEGER NOT NULL DEFAULT 0,   -- uncommitted changes in the working tree
    pid             INTEGER NOT NULL,
    started_at      TEXT NOT NULL,
    stopped_at      TEXT,                          -- NULL while running OR if it crashed
    clean_shutdown  INTEGER NOT NULL DEFAULT 0,    -- 1 only after a graceful stop hook ran
    recovery        INTEGER NOT NULL DEFAULT 0,    -- started in recovery mode
    note            TEXT NOT NULL DEFAULT ''
);
"""


def _utcnow() -> str:
    return datetime.now(UTC).replace(tzinfo=None).isoformat(timespec="seconds")


def git_state(repo_root: Path) -> tuple[str, bool]:
    """`(commit_sha, dirty)` for `repo_root`. Best-effort: a non-git checkout reports
    ('unknown', False) rather than raising — the launcher must still run."""
    def _git(*args: str) -> str:
        return subprocess.run(["git", "-C", str(repo_root), *args],  # noqa: S607
                              capture_output=True, text=True, timeout=10).stdout.strip()
    try:
        sha = _git("rev-parse", "HEAD") or "unknown"
        dirty = bool(_git("status", "--porcelain"))
        return sha, dirty
    except (OSError, subprocess.SubprocessError):
        return "unknown", False


@dataclass(frozen=True)
class RunRecord:
    id: int
    commit_sha: str
    dirty: bool
    pid: int
    started_at: str
    stopped_at: str | None
    clean_shutdown: bool
    recovery: bool
    note: str

    @property
    def active(self) -> bool:
        """Still running (or crashed without closing) — `stopped_at` was never set."""
        return self.stopped_at is None


def _row(r: sqlite3.Row) -> RunRecord:
    return RunRecord(
        id=r["id"], commit_sha=r["commit_sha"], dirty=bool(r["dirty"]), pid=r["pid"],
        started_at=r["started_at"], stopped_at=r["stopped_at"],
        clean_shutdown=bool(r["clean_shutdown"]), recovery=bool(r["recovery"]), note=r["note"],
    )


@dataclass
class RunLedger:
    path: Path

    def __post_init__(self) -> None:
        if str(self.path) != ":memory:":
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(str(self.path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        with self._lock:
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.executescript(_DDL)
            self._conn.commit()

    def open_run(self, *, commit_sha: str, dirty: bool, pid: int, recovery: bool = False,
                 note: str = "") -> RunRecord:
        with self._lock:
            cur = self._conn.execute(
                "INSERT INTO runs (commit_sha, dirty, pid, started_at, recovery, note) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                [commit_sha, int(dirty), pid, _utcnow(), int(recovery), note],
            )
            self._conn.commit()
            assert cur.lastrowid is not None  # sqlite3: set after a successful INSERT
            return self.get(cur.lastrowid)

    def mark_stopped(self, run_id: int, *, clean: bool, note: str = "") -> RunRecord:
        with self._lock:
            existing = self.get(run_id)
            new_note = note or (existing.note if existing else "")
            self._conn.execute(
                "UPDATE runs SET stopped_at = ?, clean_shutdown = ?, note = ? WHERE id = ?",
                [_utcnow(), int(clean), new_note, run_id],
            )
            self._conn.commit()
        return self.get(run_id)

    def get(self, run_id: int) -> RunRecord:
        with self._lock:
            r = self._conn.execute("SELECT * FROM runs WHERE id = ?", [run_id]).fetchone()
        if r is None:
            raise KeyError(f"no run {run_id}")
        return _row(r)

    def last(self) -> RunRecord | None:
        """The most recently started run (the live one, if any)."""
        with self._lock:
            r = self._conn.execute("SELECT * FROM runs ORDER BY id DESC LIMIT 1").fetchone()
        return _row(r) if r else None

    def last_was_clean(self) -> bool:
        """Did the PRIOR run end cleanly? True if there is no prior run. A prior run still marked
        active (`stopped_at IS NULL`) means it crashed — unclean → the caller should recover.

        Call this BEFORE `open_run` (then `last()` is the prior run) — the launcher does."""
        prev = self.last()
        if prev is None:
            return True
        return (not prev.active) and prev.clean_shutdown

    def recent(self, n: int = 10) -> list[RunRecord]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM runs ORDER BY id DESC LIMIT ?", [n]
            ).fetchall()
        return [_row(r) for r in rows]

    def close(self) -> None:
        with self._lock:
            self._conn.close()


def open_run_ledger(config: Config | None = None) -> RunLedger:
    from config.loader import get_config

    cfg = config or get_config()
    return RunLedger(cfg.paths.data_dir / "runs.sqlite")
