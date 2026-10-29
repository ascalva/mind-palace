"""The task, reminder and job ledger (core/stores/tasks.py), phase 1 of
docs/brainstorms/ambassador-agent-loop.md.

Proves: times parse to local ISO or fail loudly, with an explicit offset converted and nothing
guessed; a due item is pushed once, and again only when its moment moves; a ledger made before
`notified_at` gains the column in place; titles are data, never SQL; `run_as_job` records a
success, a failing exit and an exception (re-raised); a job whose process is gone is reconciled to
failed; a job record carries progress; the notices show what is due and what finished, but the
heartbeat's upkeep only as its
latest failure; the newest-first queries stay newest-first past their limits; the notices file is
written whole, with the heartbeat's extra lines.
"""

from __future__ import annotations

import json
import os
import sqlite3
from collections.abc import Callable, Iterator
from datetime import datetime, timedelta

import pytest

from core.stores.tasks import (
    TaskStore,
    job_record,
    now_local,
    parse_when,
    run_as_job,
    write_notices,
)

NOW = datetime(2026, 10, 29, 12, 0)


@pytest.fixture
def store(tmp_path) -> Iterator[TaskStore]:
    s = TaskStore(tmp_path / "tasks.sqlite")
    yield s
    s.close()


def _raises(exc: BaseException) -> Callable[[], int]:
    def fn() -> int:
        raise exc
    return fn


def test_times_parse_to_local_iso_or_fail_loudly():
    assert parse_when("+30m", now=NOW) == "2026-10-29T12:30"
    assert parse_when("+2h", now=NOW) == "2026-10-29T14:00"
    assert parse_when("+1d", now=NOW) == "2026-10-30T12:00"
    assert parse_when("2026-10-30T09:00", now=NOW) == "2026-10-30T09:00"
    assert parse_when(" 2026-10-30 09:00 ", now=NOW) == "2026-10-30T09:00"
    utc = datetime.fromisoformat("2026-10-30T13:00:00+00:00")
    assert parse_when("2026-10-30T13:00:00Z", now=NOW) == utc.astimezone().replace(
        tzinfo=None).isoformat(timespec="minutes")   # an absolute moment, said locally
    for bad in ("tomorrow", "+2w", "9am", "", "+-1h", "+9999999d", "2026-13-01T00:00"):
        with pytest.raises(ValueError):
            parse_when(bad, now=NOW)


def test_a_due_item_is_pushed_once_and_again_only_when_its_moment_moves(store):
    r = store.add("reminder", "call the dentist", due_at="2026-10-29T11:00")
    store.add("reminder", "later", due_at="2026-10-29T18:00")
    assert [i.id for i in store.to_notify(now=NOW)] == [r.id]
    store.mark_notified([r.id], now=NOW)
    assert store.to_notify(now=NOW) == []
    assert [i.id for i in store.due(now=NOW)] == [r.id]          # still due: the notices keep it
    store.update(r.id, note="snoozed")                           # a note does not re-arm it
    store.update(r.id, due_at="2026-10-29T11:00")                # nor does the same moment
    assert store.to_notify(now=NOW) == []
    store.update(r.id, due_at="2026-10-29T11:30")                # a new moment does
    assert [i.id for i in store.to_notify(now=NOW)] == [r.id]
    store.update(r.id, status="done")
    assert store.due(now=NOW) == [] and store.to_notify(now=NOW) == []


def test_an_older_ledger_gains_the_new_column_in_place(tmp_path):
    path = tmp_path / "tasks.sqlite"
    con = sqlite3.connect(path)
    con.executescript("""
        CREATE TABLE items (id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT NOT NULL,
            title TEXT NOT NULL, detail TEXT NOT NULL DEFAULT '', status TEXT NOT NULL,
            due_at TEXT, created_by TEXT NOT NULL, created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL, finished_at TEXT, pid INTEGER,
            progress TEXT NOT NULL DEFAULT '', log TEXT NOT NULL DEFAULT '');
        INSERT INTO items (kind, title, status, due_at, created_by, created_at, updated_at)
            VALUES ('reminder', 'kept', 'open', '2026-10-29T11:00', 'owner', 'x', 'x');""")
    con.commit()
    con.close()
    s = TaskStore(path)
    try:
        (item,) = s.to_notify(now=NOW)
        assert item.title == "kept" and item.notified_at is None
        s.mark_notified([item.id], now=NOW)
        assert s.to_notify(now=NOW) == []
    finally:
        s.close()
    TaskStore(path).close()   # opening again is idempotent


def test_titles_are_data_never_sql(store):
    hostile = "x'); DROP TABLE items; --"
    item = store.add("task", hostile, detail="\"; DELETE FROM items; --")
    assert store.get(item.id).title == hostile
    assert len(store.select()) == 1


def test_the_ledger_refuses_what_it_cannot_hold(store):
    with pytest.raises(ValueError):
        store.add("errand", "x")
    with pytest.raises(ValueError):
        store.add("task", "   ")
    t = store.add("task", "x")
    with pytest.raises(ValueError):
        store.update(t.id, status="maybe")
    with pytest.raises(LookupError):
        store.update(t.id + 999, note="x")


def test_run_as_job_records_how_a_command_ended(store):
    assert run_as_job("ok", lambda: 0, store=store) == 0
    assert run_as_job("bad exit", lambda: 3, store=store) == 3
    with pytest.raises(KeyboardInterrupt):
        run_as_job("interrupted", _raises(KeyboardInterrupt()), store=store)
    with pytest.raises(RuntimeError):
        run_as_job("crashed", _raises(RuntimeError("embedder down")), store=store)
    jobs = {j.title: j for j in store.recent_jobs(limit=10)}
    assert jobs["ok"].status == "done" and jobs["ok"].finished_at
    assert jobs["bad exit"].status == "failed" and "exit 3" in jobs["bad exit"].log
    assert "KeyboardInterrupt" in jobs["interrupted"].log
    assert "embedder down" in jobs["crashed"].log
    assert {j.pid for j in jobs.values()} == {os.getpid()}
    assert store.select(statuses=("running",)) == []               # nothing left dangling


def test_a_job_record_reports_progress_and_how_it_ended(store):
    with job_record("import", store=store) as progress:
        progress("3/10 documents")
        (running,) = store.select(statuses=("running",))
        assert running.progress == "3/10 documents"
    with pytest.raises(SystemExit), job_record("refused", store=store):
        raise SystemExit("refusing a path outside data/")
    jobs = {j.title: j for j in store.recent_jobs(limit=5)}
    assert jobs["import"].status == "done" and jobs["import"].progress == "3/10 documents"
    assert jobs["refused"].status == "failed" and "outside data/" in jobs["refused"].log


def test_a_job_whose_process_is_gone_is_reconciled(store):
    alive = store.start_job("alive", pid=111)
    gone = store.start_job("gone", pid=222)
    ended = store.reconcile_jobs(lambda pid: pid == 111)
    assert [j.id for j in ended] == [gone.id]
    assert store.get(gone.id).status == "failed" and "process gone" in store.get(gone.id).log
    assert store.get(alive.id).status == "running"
    assert store.reconcile_jobs(lambda pid: pid == 111) == []    # idempotent


def _job(store: TaskStore, title: str, *, ok: bool, by: str = "owner", note: str = "") -> int:
    j = store.start_job(title, pid=1, created_by=by)
    store.finish_job(j.id, ok=ok, summary=note)
    return j.id


def test_notices_show_due_and_finished_and_upkeep_only_as_its_latest_failure(store):
    store.add("reminder", "call the dentist",
              due_at=(now_local() - timedelta(hours=1)).isoformat(timespec="minutes"))
    store.add("reminder", "not yet",
              due_at=(now_local() + timedelta(hours=1)).isoformat(timespec="minutes"))
    _job(store, "re-embed", ok=True)
    _job(store, "dialogue sync", ok=False, by="heartbeat", note="embedder down")
    _job(store, "dialogue sync", ok=True, by="heartbeat")
    lines = store.notices()
    assert any("call the dentist" in ln for ln in lines)
    assert not any("not yet" in ln for ln in lines)
    assert any("re-embed" in ln for ln in lines)
    assert not any("dialogue sync" in ln for ln in lines)       # the latest upkeep succeeded
    _job(store, "dialogue sync", ok=False, by="heartbeat", note="embedder down")
    _job(store, "dialogue sync", ok=False, by="heartbeat", note="disk full")
    upkeep = [ln for ln in store.notices() if "dialogue sync" in ln]
    assert len(upkeep) == 1 and "disk full" in upkeep[0]         # once, the newest


def test_newest_first_queries_stay_newest_first_past_their_limits(store):
    ids = [_job(store, f"job {n}", ok=n % 3 != 0, by="heartbeat" if n % 2 else "owner")
           for n in range(30)]
    assert [j.id for j in store.recent_jobs(limit=5)] == ids[::-1][:5]
    assert [j.title for j in store.recent_jobs(created_by="owner", limit=3)] == [
        "job 28", "job 26", "job 24"]
    fin = store.finished(limit=8)
    assert fin[0].id == max(j.id for j in fin)
    assert all(not (j.created_by == "heartbeat" and j.status == "done") for j in fin)
    assert len(fin) == 8


def test_the_notices_file_is_written_whole_with_extra_lines(store, tmp_path):
    store.add("reminder", "x", due_at=parse_when("+0m"))
    target = tmp_path / "handoff" / "notices.json"
    lines = write_notices(store, path=target, extra=["disk nearly full: 5 GB free"])
    doc = json.loads(target.read_text())
    assert doc["lines"] == lines and lines[-1] == "disk nearly full: 5 GB free"
    assert datetime.fromisoformat(doc["generated_at"])
    assert sorted(p.name for p in target.parent.iterdir()) == ["notices.json"]   # no temp left
