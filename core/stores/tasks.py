"""The owner's task, reminder and job ledger — the agent loop's bookkeeping.

Phase 1 of docs/brainstorms/ambassador-agent-loop.md. One small SQLite store OUTSIDE the knowledge
strata: what the owner asked the Ambassador to track (`task`), to bring up at a moment
(`reminder`), and the long palace jobs running on their behalf (`job`: a lane, a re-embed, an
import). None of it is evidence about the owner's mind — it is operational state, so it is never
embedded, never dreamed over, and not part of a corpus reset.

Three readers and writers: the Ambassador's task tools (add, list, update, remind), the long jobs
(`start_job`/`finish_job`, with progress), and the heartbeat (`palace tick`), which reconciles jobs
whose process is gone and computes `notices` — the short lines the Open WebUI bridge adds to the
Ambassador's instructions so it raises what is due without being asked or spending a tool call
(dn-ambassador-as-reasoning-agent §3: speak when the owner expects an update — never noise).
Times are local ISO strings: the owner's clock is the one reminders are read against.
"""

from __future__ import annotations

import json
import re
import sqlite3
from collections.abc import Callable, Iterable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from core.kernel.config import Config

KINDS = ("task", "reminder", "job")
STATUSES = ("open", "waiting", "running", "done", "failed", "dropped")
OPEN = ("open", "waiting")
RECENT_JOB_HOURS = 12   # a finished or failed job is news for this long, then it ages out
NOTICES = "notices.json"   # in the bridge's handoff directory; the edge serves it

_SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    kind        TEXT NOT NULL CHECK (kind IN ('task', 'reminder', 'job')),
    title       TEXT NOT NULL,
    detail      TEXT NOT NULL DEFAULT '',
    status      TEXT NOT NULL
                CHECK (status IN ('open', 'waiting', 'running', 'done', 'failed', 'dropped')),
    due_at      TEXT,                     -- local ISO: a reminder's moment, a task's deadline
    created_by  TEXT NOT NULL,            -- owner | ambassador | system
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL,
    finished_at TEXT,
    pid         INTEGER,                  -- a job's process
    progress    TEXT NOT NULL DEFAULT '', -- a job's "n/N", or free text
    log         TEXT NOT NULL DEFAULT '', -- appended notes, one timestamped line each
    notified_at TEXT                      -- when the heartbeat pushed it (once per due time)
);
CREATE INDEX IF NOT EXISTS items_status ON items(status);
"""
_ADDED_COLUMNS = {"notified_at": "TEXT"}   # columns a ledger made before them lacks
_RELATIVE = re.compile(r"^\+(\d+)\s*([mhd])$")


def now_local() -> datetime:
    return datetime.now().replace(microsecond=0)


def parse_when(text: str, *, now: datetime | None = None) -> str:
    """`2026-10-30T09:00` (local) or `+30m` / `+2h` / `+1d` → a local ISO time; a time with an
    explicit offset (`…Z`, `…+02:00`) is converted to local. Anything else, or a moment past the
    calendar's end, is a ValueError: the caller rephrases, nothing is guessed."""
    now = now or now_local()
    t = text.strip()
    try:
        m = _RELATIVE.match(t)
        if m:
            n, unit = int(m.group(1)), m.group(2)
            return (now + timedelta(**{{"m": "minutes", "h": "hours", "d": "days"}[unit]: n})
                    ).isoformat(timespec="minutes")
        at = datetime.fromisoformat(t.replace(" ", "T"))
        if at.tzinfo is not None:   # an explicit offset is an absolute moment: say it locally
            at = at.astimezone()
        return at.replace(tzinfo=None).isoformat(timespec="minutes")
    except (ValueError, OverflowError):
        raise ValueError(
            f"{text!r}: use local ISO time (2026-10-30T09:00) or +30m, +2h, +1d") from None


@dataclass(frozen=True)
class Item:
    id: int
    kind: str
    title: str
    detail: str
    status: str
    due_at: str | None
    created_by: str
    created_at: str
    updated_at: str
    finished_at: str | None
    pid: int | None
    progress: str
    log: str
    notified_at: str | None = None

    def brief(self) -> dict[str, object]:
        """What a tool result shows — no empty fields."""
        out: dict[str, object] = {"id": self.id, "kind": self.kind, "title": self.title,
                                  "status": self.status}
        for key in ("detail", "due_at", "finished_at", "progress"):
            if getattr(self, key):
                out[key] = getattr(self, key)
        if self.log:
            out["last_note"] = self.log.splitlines()[-1]
        return out


@dataclass
class TaskStore:
    path: Path

    def __post_init__(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.path, timeout=10)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        have = {r["name"] for r in self._conn.execute("PRAGMA table_info(items)")}
        for col, decl in _ADDED_COLUMNS.items():
            if col not in have:
                self._conn.execute(f"ALTER TABLE items ADD COLUMN {col} {decl}")
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    # reads ---------------------------------------------------------------------------------------
    def get(self, item_id: int) -> Item | None:
        row = self._conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
        return Item(**dict(row)) if row else None

    def select(self, *, kinds: Iterable[str] | None = None, statuses: Iterable[str] | None = None,
             limit: int = 50) -> list[Item]:
        clauses, params = [], []
        for col, vals in (("kind", kinds), ("status", statuses)):
            if vals is not None:
                vals = list(vals)
                clauses.append(f"{col} IN ({', '.join('?' * len(vals))})")
                params.extend(vals)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = self._conn.execute(
            f"SELECT * FROM items{where} ORDER BY COALESCE(due_at, created_at), id LIMIT ?",
            (*params, limit)).fetchall()
        return [Item(**dict(r)) for r in rows]

    def due(self, *, now: datetime | None = None) -> list[Item]:
        """Open tasks and reminders whose moment has come."""
        at = (now or now_local()).isoformat(timespec="minutes")
        rows = self._conn.execute(
            "SELECT * FROM items WHERE status IN ('open', 'waiting') AND due_at IS NOT NULL "
            "AND due_at <= ? ORDER BY due_at, id", (at,)).fetchall()
        return [Item(**dict(r)) for r in rows]

    def to_notify(self, *, now: datetime | None = None) -> list[Item]:
        """Due items the heartbeat has not pushed yet."""
        return [i for i in self.due(now=now) if i.notified_at is None]

    def mark_notified(self, item_ids: Iterable[int], *, now: datetime | None = None) -> None:
        stamp = (now or now_local()).isoformat()
        self._conn.executemany("UPDATE items SET notified_at = ? WHERE id = ?",
                               [(stamp, i) for i in item_ids])
        self._conn.commit()

    # writes --------------------------------------------------------------------------------------
    def add(self, kind: str, title: str, *, detail: str = "", due_at: str | None = None,
            created_by: str = "ambassador") -> Item:
        if kind not in KINDS:
            raise ValueError(f"kind must be one of {KINDS}")
        if not title.strip():
            raise ValueError("a title is required")
        stamp = now_local().isoformat()
        cur = self._conn.execute(
            "INSERT INTO items (kind, title, detail, status, due_at, created_by, created_at, "
            "updated_at) VALUES (?, ?, ?, 'open', ?, ?, ?, ?)",
            (kind, title.strip(), detail.strip(), due_at, created_by, stamp, stamp))
        self._conn.commit()
        item = self.get(int(cur.lastrowid or 0))
        assert item is not None
        return item

    def update(self, item_id: int, *, status: str | None = None, due_at: str | None = None,
               note: str | None = None, progress: str | None = None) -> Item:
        item = self.get(item_id)
        if item is None:
            raise LookupError(f"no item #{item_id}")
        if status is not None and status not in STATUSES:
            raise ValueError(f"status must be one of {STATUSES}")
        stamp = now_local().isoformat()
        log = item.log + (f"{stamp} {note.strip()}\n" if note and note.strip() else "")
        finished = item.finished_at
        if status in ("done", "failed", "dropped") and not finished:
            finished = stamp
        moved = due_at is not None and due_at != item.due_at   # a new moment: push it again then
        self._conn.execute(
            "UPDATE items SET status = ?, due_at = ?, log = ?, progress = ?, finished_at = ?, "
            "notified_at = ?, updated_at = ? WHERE id = ?",
            (status or item.status, due_at if due_at is not None else item.due_at, log,
             progress if progress is not None else item.progress, finished,
             None if moved else item.notified_at, stamp, item_id))
        self._conn.commit()
        out = self.get(item_id)
        assert out is not None
        return out

    # jobs ----------------------------------------------------------------------------------------
    def start_job(self, title: str, *, pid: int, created_by: str = "system") -> Item:
        item = self.add("job", title, created_by=created_by)
        self._conn.execute("UPDATE items SET status = 'running', pid = ? WHERE id = ?",
                           (pid, item.id))
        self._conn.commit()
        out = self.get(item.id)
        assert out is not None
        return out

    def finish_job(self, item_id: int, *, ok: bool, summary: str = "") -> Item:
        return self.update(item_id, status="done" if ok else "failed", note=summary or None)

    def reconcile_jobs(self, alive: Callable[[int], bool]) -> list[Item]:
        """Running jobs whose process is gone ended without a record: mark them failed."""
        gone = [j for j in self.select(kinds=("job",), statuses=("running",), limit=500)
                if j.pid is None or not alive(j.pid)]
        return [self.finish_job(j.id, ok=False, summary="ended without a record (process gone)")
                for j in gone]

    def recent_jobs(self, *, title: str | None = None, created_by: str | None = None,
                    limit: int = 10) -> list[Item]:
        """Finished jobs, newest first (the heartbeat's circuit breaker reads its own streak)."""
        clauses, params = ["kind = 'job'", "status IN ('done', 'failed')"], []
        for col, val in (("title", title), ("created_by", created_by)):
            if val is not None:
                clauses.append(f"{col} = ?")
                params.append(val)
        rows = self._conn.execute(
            f"SELECT * FROM items WHERE {' AND '.join(clauses)} ORDER BY id DESC LIMIT ?",
            (*params, limit)).fetchall()
        return [Item(**dict(r)) for r in rows]

    def finished(self, *, limit: int = 10) -> list[Item]:
        """What ended lately, newest first: tasks, reminders and jobs, without the heartbeat's
        routine successes (upkeep is news only when it fails)."""
        rows = self._conn.execute(
            "SELECT * FROM items WHERE status IN ('done', 'failed', 'dropped') "
            "AND NOT (created_by = 'heartbeat' AND status = 'done') "
            "ORDER BY COALESCE(finished_at, updated_at) DESC, id DESC LIMIT ?",
            (limit,)).fetchall()
        return [Item(**dict(r)) for r in rows]

    # the heartbeat's output ----------------------------------------------------------------------
    def notices(self, *, now: datetime | None = None) -> list[str]:
        """Short lines for the Ambassador: what is due, what just finished or failed. Of the
        heartbeat's own upkeep only the latest run per kind counts, and only if it failed."""
        now = now or now_local()
        lines = [f"#{i.id} {i.kind} due {i.due_at}: {i.title}" for i in self.due(now=now)]
        since = (now - timedelta(hours=RECENT_JOB_HOURS)).isoformat()
        rows = self._conn.execute(
            "SELECT * FROM items WHERE kind = 'job' AND status IN ('done', 'failed') "
            "AND finished_at >= ? ORDER BY finished_at DESC, id DESC", (since,)).fetchall()
        upkeep_seen: set[str] = set()
        news: list[str] = []
        for j in (Item(**dict(r)) for r in rows):   # newest first
            if j.created_by == "heartbeat":
                if j.title in upkeep_seen:
                    continue
                upkeep_seen.add(j.title)
                if j.status == "done":
                    continue
            last = j.log.splitlines()[-1].split(" ", 1)[-1] if j.log else ""
            news.append(f"#{j.id} job {j.status} {(j.finished_at or '')[11:16]}: {j.title}"
                        + (f" — {last[:120]}" if last else ""))
        return lines + news[::-1]


def notices_path() -> Path:
    """Where the Open WebUI bridge reads the notices: its handoff directory (config/stack.toml
    [bridge] handoff_dir) — the core↔edge channel the bridge already uses."""
    import tomllib

    from core.kernel.config import REPO_ROOT

    stack = REPO_ROOT / "config" / "stack.toml"
    bridge = tomllib.loads(stack.read_text()).get("bridge", {}) if stack.exists() else {}
    return REPO_ROOT / str(bridge.get("handoff_dir", "data/handoff/mcp")) / NOTICES


def write_notices(store: TaskStore, *, path: Path | None = None, now: datetime | None = None,
                  extra: Iterable[str] = ()) -> list[str]:
    """Publish the notices for the edge: lines the core chose to show, nothing else. `extra`
    carries the heartbeat's own findings (a nearly full disk)."""
    lines = [*store.notices(now=now), *extra]
    target = path or notices_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(".tmp")
    tmp.write_text(json.dumps({"generated_at": (now or now_local()).isoformat(),
                               "lines": lines}, ensure_ascii=False), encoding="utf-8")
    tmp.replace(target)   # atomic: the edge never reads a partial file
    return lines


def open_task_store(config: Config | None = None) -> TaskStore:
    from core.kernel.config import get_config

    cfg = config or get_config()
    return TaskStore(cfg.paths.data_dir / "tasks.sqlite")


@contextmanager
def job_record(title: str, *, created_by: str = "owner",
               store: TaskStore | None = None) -> Iterator[Callable[[str], None]]:
    """A ledger record around a block that reports progress: yields `progress(text)` (the
    status tool and the heartbeat show it), ends done on a clean exit and failed on an exception,
    which is re-raised. `run_as_job` is the same for a command that returns an exit code."""
    import os

    own = store is None
    ledger = store or open_task_store()
    try:
        job = ledger.start_job(title, pid=os.getpid(), created_by=created_by)

        def progress(text: str) -> None:
            ledger.update(job.id, progress=text)

        try:
            yield progress
        except BaseException as e:
            ledger.finish_job(job.id, ok=False, summary=f"{type(e).__name__}: {e}"[:200])
            raise
        ledger.finish_job(job.id, ok=True)
    finally:
        if own:
            ledger.close()


def run_as_job(title: str, fn: Callable[[], int], *, created_by: str = "owner",
               store: TaskStore | None = None) -> int:
    """Run a long palace command under a ledger record: running while it works, then done or
    failed by its exit code. An exception (Ctrl-C included) is recorded, then re-raised; a process
    killed outright is caught later by the heartbeat's `reconcile_jobs`."""
    import os

    own = store is None
    ledger = store or open_task_store()
    try:
        job = ledger.start_job(title, pid=os.getpid(), created_by=created_by)
        try:
            rc = fn()
        except BaseException as e:
            ledger.finish_job(job.id, ok=False, summary=f"{type(e).__name__}: {e}"[:200])
            raise
        ledger.finish_job(job.id, ok=rc == 0, summary="" if rc == 0 else f"exit {rc}")
        return rc
    finally:
        if own:
            ledger.close()
