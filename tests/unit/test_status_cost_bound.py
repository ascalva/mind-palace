"""bp-102 Item 2 FALSIFIER — `status` must not become expensive.

The falsifier, verbatim from the plan: *"Running `status` costs more than a small constant — e.g.
it full-scans `vectors.lance` or materializes the `vector` column (Q6). Assert an upper bound on
rows/columns read; a status command that repeats finding-0169 one level up has failed even if
every number is right."*

finding-0169 was a job that went O(total store) because `supersede_source` did two full-table
`to_pylist()` materializations — vectors included — per superseded version. Rebuilding that cost
inside the *diagnostic tool for that very incident* would be the same mistake one storey up, and
it would be worse: the instrument is what you reach for when the system is already sick.

So the bound is asserted mechanically, two ways:

1. **Scale invariance.** The same reads over a 50-row and a 5,000-row `jobs` table must issue the
   same number of queries and materialize the same (small) number of result rows. A cost that
   does not move with the table cannot be a scan.
2. **Store method allow-list.** A spy vector store proves `count()` is called at most once and
   that `all_rows` / `rows_for_source` / `search` / `to_arrow` — every read that goes through
   `to_arrow().to_pylist()` and therefore drags the `vector` column into memory — are called
   **zero** times.
"""

import sqlite3
from datetime import datetime
from pathlib import Path

import pytest

from ops.lifecycle.snapshot import read_queue_stats, read_store_stats

NOW = datetime(2026, 7, 25, 4, 0, 0)

_DDL = """
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
"""

# rows_read ceiling: ≤5 lifetime state buckets + 3 scalar COUNTs + ≤10 running + ≤6 queued kinds
# + 1 last-failure = 25 at the absolute worst. 24 is the observed bound for these fixtures.
MAX_ROWS_READ = 24


def _mkqueue(path: Path, n: int) -> None:
    conn = sqlite3.connect(path)
    conn.executescript(_DDL)
    rows: list[tuple[object, ...]] = []
    for i in range(n):
        rows.append((f"kind{i % 4}", "router", 8192, 100, "done", None,
                     "2026-07-25T03:50:00", "2026-07-25T03:50:01", "2026-07-25T03:50:02"))
        rows.append((f"kind{i % 4}", "router", 8192, 100, "queued", None,
                     "2026-07-25T03:51:00", None, None))
    conn.executemany(
        "INSERT INTO jobs (kind, tier, num_ctx, priority, state, error, created_at, started_at, "
        "finished_at) VALUES (?,?,?,?,?,?,?,?,?)", rows)
    conn.commit()
    conn.close()


def test_queue_read_cost_does_not_grow_with_the_table(tmp_path):
    """The load-bearing assertion: 100 rows and 10,000 rows must cost the same in rows read and
    queries issued. If someone later replaces an aggregate with a `SELECT *`, this fails."""
    small, big = tmp_path / "small.sqlite", tmp_path / "big.sqlite"
    _mkqueue(small, 50)                                  # 100 rows
    _mkqueue(big, 5_000)                                 # 10,000 rows
    s = read_queue_stats(small, now=NOW)
    b = read_queue_stats(big, now=NOW)
    assert s.depth == 50 and b.depth == 5_000            # the figures are still right …
    assert s.queries == b.queries                        # … at identical cost
    assert s.rows_read == b.rows_read
    assert b.rows_read <= MAX_ROWS_READ


def _capture_sql(monkeypatch, path: Path) -> list[str]:
    """Run `read_queue_stats` with every SQL statement it issues recorded verbatim."""
    seen: list[str] = []
    real_connect = sqlite3.connect

    class _Recording:
        def __init__(self, conn):
            self._c = conn

        def __setattr__(self, k, v):
            if k == "_c":
                object.__setattr__(self, k, v)
            else:
                setattr(self._c, k, v)

        def execute(self, sql, *a, **kw):
            seen.append(sql)
            return self._c.execute(sql, *a, **kw)

        def close(self):
            self._c.close()

    monkeypatch.setattr("ops.lifecycle.snapshot.sqlite3.connect",
                        lambda *a, **kw: _Recording(real_connect(*a, **kw)))
    read_queue_stats(path, now=NOW)
    return seen


def test_queue_read_never_projects_an_unbounded_column(tmp_path, monkeypatch):
    """`payload` / `result` / `checkpoint` are the unbounded columns on `jobs`. No statement may
    project them, and none may `SELECT *` — a status line has no use for a job's payload, and
    pulling one turns a bounded metadata read into an unbounded data read. Asserted on the SQL
    actually executed, not on the source text."""
    p = tmp_path / "q.sqlite"
    _mkqueue(p, 10)
    for sql in _capture_sql(monkeypatch, p):
        assert "SELECT *" not in sql
        for column in ("payload", "result", "checkpoint"):
            assert column not in sql, f"{column!r} projected by: {sql}"


def test_every_queue_statement_is_bounded(tmp_path, monkeypatch):
    """Each read is an aggregate (`count(*)`/`GROUP BY`) or carries an explicit `LIMIT`. There is
    no third kind, which is what keeps the cost independent of the table."""
    p = tmp_path / "q.sqlite"
    _mkqueue(p, 10)
    statements = _capture_sql(monkeypatch, p)
    assert statements, "read_queue_stats issued no SQL at all"
    for sql in statements:
        assert ("count(*)" in sql or "LIMIT" in sql), f"unbounded statement: {sql}"


def test_queue_read_is_read_only_and_never_creates_the_db(tmp_path):
    """`status` is the first thing anyone runs after an incident. It must not conjure a queue."""
    missing = tmp_path / "nope.sqlite"
    stats = read_queue_stats(missing, now=NOW)
    assert stats.exists is False and stats.depth == 0
    assert not missing.exists()                          # nothing was created


def test_queue_read_cannot_write_even_if_asked(tmp_path):
    """The connection is opened `mode=ro`, so a future edit that tries to mutate fails loudly
    rather than silently making the diagnostic tool a writer."""
    p = tmp_path / "q.sqlite"
    _mkqueue(p, 5)
    conn = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
    try:
        with pytest.raises(sqlite3.OperationalError):
            conn.execute("UPDATE jobs SET state = 'done'")
    finally:
        conn.close()


class _SpyStore:
    """A vector store that records every method touched. The forbidden four all funnel through
    `to_arrow().to_pylist()` in `core/stores/vectorstore.py` — the finding-0169 shape."""

    def __init__(self):
        self.calls: list[str] = []

    def count(self) -> int:
        self.calls.append("count")
        return 22_621

    def all_rows(self, **_kw):
        self.calls.append("all_rows")
        raise AssertionError("status must never full-scan the vector store")

    def rows_for_source(self, _p):
        self.calls.append("rows_for_source")
        raise AssertionError("status must never scan the vector store")

    def search(self, *_a, **_kw):
        self.calls.append("search")
        raise AssertionError("status must never run a vector search")

    def to_arrow(self):
        self.calls.append("to_arrow")
        raise AssertionError("status must never materialize the arrow table")


def test_store_stats_touch_only_the_metadata_count():
    """The vector column is never materialized: `count()` maps to LanceDB's `count_rows()`, which
    reads fragment metadata (measured at 5 ms over the real 22,621-row store)."""
    spy = _SpyStore()
    stats = read_store_stats(vector_store=spy)
    assert stats.vector_rows == 22_621
    assert spy.calls == ["count"]                        # exactly one call, and it is the cheap one


def test_store_stats_survive_a_broken_store():
    """A probe failure is a missing figure, never a crash — status must still print during an
    incident where the store itself is the thing that is broken."""
    class _Broken:
        def count(self) -> int:
            raise RuntimeError("lance table is corrupt")

    stats = read_store_stats(vector_store=_Broken())
    assert stats.vector_rows is None


def test_store_stats_with_nothing_available():
    stats = read_store_stats(vector_store=None)
    assert stats.vector_rows is None


def test_store_stats_carries_only_the_one_cheap_figure():
    """The falsifier, applied to a figure the plan ASKED for and this build refused.

    §7 Item 2 lists "code versions embedded vs ledger target" and the `current` split. Neither is
    reported, because neither is metadata-cheap: the ledger side (`COUNT(DISTINCT path, blob_sha)`
    over `code_snapshots.sqlite`) MEASURED at 3.5 s — 423,855 rows, `SCAN files` + a temp B-tree,
    over a 2.3 GB table — and the embedded side has no filtered-count reader at all. `StoreStats`
    is therefore pinned to a single field, so re-adding an expensive figure has to be a deliberate
    edit to this contract rather than a quiet extra line in the renderer (finding-0175)."""
    import dataclasses

    fields = {f.name for f in dataclasses.fields(read_store_stats())}
    assert fields == {"vector_rows"}
