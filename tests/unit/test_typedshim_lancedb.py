"""The `core/typedshims/lancedb.py` boundary (bp-103 Item 1, warrant finding-0176).

The shim is the ONE place core touches raw `lancedb`. bp-103 widened it with the four surfaces
`supersede_source`/`rows_for_source` need — `update()`, a filtered `count_rows()`, `select()`, and
`scan()` — and in doing so turned it from a pure typing facade into a thin runtime adapter, because
`scan()` has no counterpart on the raw table (it is `search(None)`).

This module is the structural enforcement of two things a type annotation cannot prove:

1. **`limit(0)` really means UNLIMITED.** finding-0176 asserts it; bp-103 §10 makes it a
   stop-and-raise. If a future lancedb quietly caps it, `rows_for_source` silently under-reads a
   deep path and `supersede_source` silently under-flips it — corpus corruption, not a perf bug.
   So the claim is pinned by a test on a path deeper than any plausible default cap, not by a
   comment. This is the ratchet that fires on version drift.
2. **The shim is HONEST, not a laundering `__getattr__` proxy.** The declared Protocol surface is
   the WHOLE surface: a raw-lancedb method the Protocols do not declare must not be reachable
   through the adapter, and no caller may have to pass `None` to `search` to mean "scan".

Temp stores only (`tmp_path`). No network, no live store, no daemon.
"""

from __future__ import annotations

import inspect
from pathlib import Path

import pyarrow as pa
import pytest

from core.typedshims.lancedb import VectorDB, VectorTable, connect

DIM = 4
TABLE = "chunks"

# Deeper than LanceDB's default vector-search cap (10) by an order of magnitude, so a truncation
# regression cannot hide inside a small fixture.
DEEP = 137

# The hostile path from `test_vectorstore_supersede.py` — apostrophe, double space, non-ASCII.
NASTY = "notes/it's a  café/π.md"


def _schema() -> pa.Schema:
    return pa.schema([
        ("id", pa.string()),
        ("source_path", pa.string()),
        ("current", pa.bool_()),
        ("vector", pa.list_(pa.float32(), DIM)),
    ])


def _sql_str(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _db(tmp_path: Path) -> VectorDB:
    return connect(str(tmp_path / "v.lance"))


def _seeded(tmp_path: Path) -> VectorTable:
    """`DEEP` rows on the nasty path, one decoy sharing its prefix, 50 unrelated rows."""
    t = _db(tmp_path).create_table(TABLE, schema=_schema())
    t.add([{"id": f"n:{i}", "source_path": NASTY, "current": True,
            "vector": [0.5 * i, -0.25, 0.125, 2.0]} for i in range(DEEP)])
    t.add([{"id": "decoy:0", "source_path": "notes/it", "current": True,
            "vector": [1.0] * DIM}])
    t.add([{"id": f"cold:{i}", "source_path": f"c{i}.py", "current": True,
            "vector": [0.0] * DIM} for i in range(50)])
    return t


# ── the ratchet on the claim the whole plan rests on ─────────────────────────────────────

def test_scan_limit_zero_returns_every_matching_row(tmp_path: Path) -> None:
    """THE version-drift ratchet (bp-103 §10). `limit(0)` == unlimited: a path with 137 rows must
    come back with 137, not with a default page of 10. If this ever fails, STOP — deep paths are
    being silently truncated on both the read and the supersede path."""
    t = _seeded(tmp_path)
    rows = t.scan().where(f"source_path = {_sql_str(NASTY)}").limit(0).to_list()
    assert len(rows) == DEEP, (
        f"limit(0) returned {len(rows)} of {DEEP} rows — it is NOT unlimited on this lancedb; "
        "finding-0176's premise has drifted (bp-103 §10 stop-and-raise)"
    )
    assert {r["id"] for r in rows} == {f"n:{i}" for i in range(DEEP)}


def test_scan_predicate_does_not_leak_into_a_prefix_neighbour(tmp_path: Path) -> None:
    """`notes/it` is a prefix of `notes/it's …` up to the apostrophe. Equality, quoted through the
    store's escaping idiom, must not confuse them — a broken quote would either error or match
    both."""
    t = _seeded(tmp_path)
    decoy = t.scan().where(f"source_path = {_sql_str('notes/it')}").limit(0).to_list()
    assert [r["id"] for r in decoy] == ["decoy:0"]


def test_scan_carries_the_vector_column_when_nothing_is_projected(tmp_path: Path) -> None:
    """`rows_for_source` feeds the amendment path, which REUSES stored vectors instead of
    re-embedding (ingest-identity §4). An unprojected scan must therefore still carry `vector`."""
    t = _seeded(tmp_path)
    row = t.scan().where(f"source_path = {_sql_str(NASTY)}").limit(0).to_list()[0]
    assert set(row) == {"id", "source_path", "current", "vector"}
    assert len(row["vector"]) == DIM        # type: ignore[arg-type]  # Row values are `object`


def test_select_projects_away_the_expensive_column(tmp_path: Path) -> None:
    """Column projection is real, not advisory: asking for two columns yields exactly two."""
    t = _seeded(tmp_path)
    rows = (t.scan().where(f"source_path = {_sql_str(NASTY)}")
            .select(["id", "current"]).limit(0).to_list())
    assert len(rows) == DEEP
    assert all(set(r) == {"id", "current"} for r in rows)


def test_scan_returns_no_distance_column_and_no_distance_ordering(tmp_path: Path) -> None:
    """Why `scan()` and not the rejected "KNN masquerade" (finding-0176): a sentinel-vector search
    pollutes every row with `_distance` and returns them in distance order. A filter-only scan
    does neither — rows come back in insertion order, clean."""
    t = _seeded(tmp_path)
    rows = t.scan().where(f"source_path = {_sql_str(NASTY)}").limit(0).to_list()
    assert all("_distance" not in r for r in rows)
    assert [r["id"] for r in rows] == [f"n:{i}" for i in range(DEEP)]


# ── the new write/count surface ──────────────────────────────────────────────────────────

def test_count_rows_filters_server_side(tmp_path: Path) -> None:
    """The filtered count is what `supersede_source` uses for its return value (bp-103 §11's
    portable route, in place of `UpdateResult.rows_updated`). Unfiltered still counts everything —
    the pre-existing `VectorStore.count()` caller is unchanged."""
    t = _seeded(tmp_path)
    assert t.count_rows() == DEEP + 1 + 50
    assert t.count_rows(f"source_path = {_sql_str(NASTY)}") == DEEP
    assert t.count_rows(f"source_path = {_sql_str(NASTY)} AND current = true") == DEEP
    assert t.count_rows("source_path = 'nowhere.py'") == 0


def test_update_flips_every_matching_row_and_retains_all_of_them(tmp_path: Path) -> None:
    """In-place update over a deep path: all `DEEP` rows flip, nothing is deleted, the prefix
    decoy and the 50 unrelated rows are untouched."""
    t = _seeded(tmp_path)
    where = f"source_path = {_sql_str(NASTY)} AND current = true"

    t.update(where, {"current": False})

    assert t.count_rows(where) == 0
    assert t.count_rows(f"source_path = {_sql_str(NASTY)} AND current = false") == DEEP
    assert t.count_rows("source_path = 'notes/it' AND current = true") == 1
    assert t.count_rows() == DEEP + 1 + 50               # keep-and-link: nothing deleted


def test_update_does_not_touch_the_vector_column(tmp_path: Path) -> None:
    """The guarantee that makes bp-103 STRONGER than a re-land: an unnamed column is never read,
    so it cannot be re-derived or dropped. Byte-exact float32 values, before vs after."""
    t = _seeded(tmp_path)
    pred = f"source_path = {_sql_str(NASTY)}"
    before = {r["id"]: r["vector"] for r in t.scan().where(pred).limit(0).to_list()}

    t.update(f"{pred} AND current = true", {"current": False})

    after = {r["id"]: r["vector"] for r in t.scan().where(pred).limit(0).to_list()}
    assert after == before


def test_update_on_a_predicate_matching_nothing_is_a_no_op(tmp_path: Path) -> None:
    t = _seeded(tmp_path)
    t.update("source_path = 'nowhere.py'", {"current": False})
    assert t.count_rows("current = true") == DEEP + 1 + 50


# ── Item 1's falsifier: the shim must ABSORB the raw overloads, not leak them ─────────────

def test_scan_is_honest_no_caller_passes_none_to_mean_no_vector(tmp_path: Path) -> None:
    """Item 1's falsifier, stated as a test. `search` takes a vector — a REAL one; `None` is not
    in its type and `scan()` is the named way to ask for a filter-only query. If someone ever
    'simplifies' this by widening `search` to `list[float] | None`, the raw package's overload has
    leaked through the boundary and this fails."""
    sig = inspect.signature(type(_seeded(tmp_path)).search)
    assert str(sig.parameters["vector"].annotation) == "list[float]", (
        "`search` was widened to accept None — the raw lancedb overload leaked past the shim "
        "(bp-103 Item 1 falsifier; §11 records `scan()` as the recorded default)"
    )


def test_the_adapter_exposes_the_declared_surface_and_nothing_else(tmp_path: Path) -> None:
    """The shim is an adapter, not a `__getattr__` passthrough. A passthrough would re-launder
    `Any` into the checked region — precisely the hole the module docstring says it closes — and
    would let core call raw lancedb surface that no Protocol describes. `compact_files` is real on
    the raw table and deliberately unreachable here."""
    t = _seeded(tmp_path)
    for name in ("add", "count_rows", "delete", "update", "to_arrow", "search", "scan"):
        assert callable(getattr(t, name)), f"declared surface {name} missing"
    assert not hasattr(type(t), "__getattr__"), "the adapter forwards blindly — Any is laundering"
    with pytest.raises(AttributeError):
        # `compact_files` is real on the raw lancedb table; reaching it through the adapter must
        # fail. `getattr` (not attribute syntax) so the assertion is an expression, not a
        # statement ruff reads as dead code.
        getattr(t, "compact_files")     # noqa: B009  # the point IS the dynamic lookup


def test_the_db_adapter_hands_back_adapted_tables(tmp_path: Path) -> None:
    """`open_table` and `create_table` must both yield something with `scan()` — otherwise the
    store's `_table()` returns a raw table on one branch and an adapter on the other, and the bug
    only shows on the second call."""
    db = _db(tmp_path)
    created = db.create_table(TABLE, schema=_schema())
    assert callable(created.scan)
    assert callable(db.open_table(TABLE).scan)
    assert TABLE in db.list_tables().tables
    db.drop_table(TABLE)
    assert TABLE not in db.list_tables().tables


# ── the pre-existing surface, unchanged by the widening ──────────────────────────────────

def test_the_pre_bp103_surface_still_works_through_the_adapter(tmp_path: Path) -> None:
    """Item 1's acceptance bar: additive. `add`/`delete`/`to_arrow`/`search(vector).metric()` are
    exactly what the shim declared before bp-103; every one still behaves."""
    t = _db(tmp_path).create_table(TABLE, schema=_schema())
    t.add([{"id": f"r{i}", "source_path": "a.py", "current": True,
            "vector": [float(i), 0.0, 0.0, 1.0]} for i in range(3)])

    assert {r["id"] for r in t.to_arrow().to_pylist()} == {"r0", "r1", "r2"}

    hits = t.search([0.0, 0.0, 0.0, 1.0]).metric("cosine").limit(2).to_list()
    assert len(hits) == 2

    filtered = (t.search([0.0, 0.0, 0.0, 1.0]).metric("cosine")
                .where("current = true", prefilter=True).limit(5).to_list())
    assert len(filtered) == 3

    t.delete("id = 'r1'")
    assert t.count_rows() == 2
