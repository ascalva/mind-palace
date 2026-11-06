"""`JobQueue.claim` is a compare-and-set on the row's state, so two processes on one queue file
cannot both take the same job. The interleaving is forced: the first handle's SELECT has returned
its rows when the second handle claims, so the first handle's UPDATE meets a row already RUNNING."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scheduler.queue import RUNNING, JobQueue


class _AfterFetchall:
    """A cursor whose `fetchall` fires a callback once, after it has read the rows."""

    def __init__(self, cur: Any, hook: Any) -> None:
        self._cur, self._hook = cur, hook

    def fetchall(self) -> list[Any]:
        rows = self._cur.fetchall()
        hook, self._hook = self._hook, None
        if hook is not None:
            hook()
        return rows

    def __getattr__(self, name: str) -> Any:
        return getattr(self._cur, name)


class _ConnProxy:
    """Delegates to a sqlite3 connection; the first `SELECT ... FROM jobs` runs `hook` after its
    rows are fetched (the window in which another process can claim)."""

    def __init__(self, conn: Any, hook: Any) -> None:
        self._conn, self._hook = conn, hook

    def execute(self, sql: str, *a: Any) -> Any:
        cur = self._conn.execute(sql, *a)
        if self._hook is not None and sql.startswith("SELECT * FROM jobs WHERE state"):
            hook, self._hook = self._hook, None
            return _AfterFetchall(cur, hook)
        return cur

    def __getattr__(self, name: str) -> Any:
        return getattr(self._conn, name)


def _race(tmp_path: Path, n_jobs: int) -> tuple[list[int | None], list[int | None], JobQueue]:
    path = tmp_path / "queue.sqlite"
    first, second = JobQueue(path), JobQueue(path)
    for _ in range(n_jobs):
        first.enqueue("ambassador_task", "synthesis", 4096)
    won_second: list[int | None] = []

    def other_process_claims() -> None:
        job = second.claim()
        won_second.append(None if job is None else job.id)

    first._conn = _ConnProxy(first._conn, other_process_claims)  # type: ignore[assignment]
    job = first.claim()
    return [None if job is None else job.id], won_second, first


def test_two_handles_never_claim_the_same_job(tmp_path: Path) -> None:
    """One job, two claimers, the first one's SELECT done before the second claims: exactly one
    wins. The old unguarded UPDATE let both mark the row RUNNING and both return it."""
    won_first, won_second, q = _race(tmp_path, 1)
    winners = [j for j in won_first + won_second if j is not None]
    assert len(winners) == 1
    assert [j.state for j in q.list()] == [RUNNING]
    assert q.get(winners[0]).attempts == 1               # one claim, not two


def test_the_loser_takes_the_next_job_instead_of_nothing(tmp_path: Path) -> None:
    """Control: with two jobs the loser re-chooses and gets the other row, so the guard does not
    just refuse; every row is claimed once."""
    won_first, won_second, q = _race(tmp_path, 2)
    assert sorted(won_first + won_second) == [1, 2]      # type: ignore[type-var]
    assert [j.attempts for j in q.list()] == [1, 1]
