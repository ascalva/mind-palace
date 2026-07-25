"""`supersede_source` / `delete_source` / `rows_for_source` — keep-and-link semantics and the
quoting identity (bp-100 Items 2–3, warrant finding-0169).

bp-100 changed HOW these three cost what they cost, not WHAT they mean. This module pins the
"what" so the "how" can keep moving — including through the typedshim widening in finding-0176,
which replaces the re-land with an in-place `update()` and must leave every assertion here true.

The load-bearing one is `test_vectors_are_byte_identical_across_a_supersede`. A re-land that
silently re-derives or drops an embedding is a corpus-integrity failure, not a performance bug
(§8: vectors are carried through the move, never recomputed).

Deterministic, hand-built vectors; temp stores only; no embedder, no network, no daemon.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pyarrow as pa
import pytest

from core.kernel.provenance import Provenance
from core.stores.vectorstore import LAYER_CODE_AST, TABLE, VectorStore
from core.typedshims.lancedb import UpdateResult, VectorTable

DIM = 4

# A path that breaks a naively-quoted predicate — the Item 2 falsifier. It carries an apostrophe,
# a space, and a non-ASCII character, all of which the old Python-side filter handled for free and
# a pushed-down predicate must not regress.
NASTY = "notes/it's a  café/π.md"


def _row(rid: str, path: str, *, current: bool = True, seed: int = 0) -> dict[str, Any]:
    return {
        "id": rid, "digest": f"d{seed}", "title": path, "source_path": path,
        "chunk_index": seed, "provenance": Provenance.CODE.value, "text": f"body {rid}",
        "layer": LAYER_CODE_AST, "qualname": f"q{seed}", "line_start": seed, "line_end": seed + 3,
        "current": current,
        # float32-exact values, so a round-trip through Arrow is bit-for-bit comparable.
        "vector": [0.5 * seed, -0.25, 0.125 * (seed + 1), 2.0],
    }


def _by_id(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(r["id"]): r for r in rows}


def _store(tmp_path: Path) -> VectorStore:
    return VectorStore(tmp_path / "v.lance", dim=DIM)


# ── Item 3's falsifier: the vectors must survive the move untouched ───────────────────────

def test_vectors_are_byte_identical_across_a_supersede(tmp_path: Path) -> None:
    """THE falsifier. Every row of the path, every float, before vs after — exact equality, not
    approximate. If this ever fires, the store re-derived or dropped an embedding and the finding
    is a corpus-integrity one, not a perf one."""
    vs = _store(tmp_path)
    vs.add([_row(f"a:{i}", "a.py", seed=i) for i in range(5)])
    before = _by_id(vs.rows_for_source("a.py"))

    assert vs.supersede_source("a.py") == 5

    after = _by_id(vs.rows_for_source("a.py"))
    assert set(after) == set(before)
    for rid, row in after.items():
        assert row["vector"] == before[rid]["vector"], f"vector changed for {rid}"
        # everything except the flag is carried through untouched, too
        assert {k: v for k, v in row.items() if k != "current"} == \
               {k: v for k, v in before[rid].items() if k != "current"}
        assert row["current"] is False


def test_supersede_retains_every_row_and_flips_only_current(tmp_path: Path) -> None:
    """Keep-and-link (dn-temporal-code-corpus D2): a superseded version is RETAINED, never deleted.
    The count is the check — a delete-shaped bug shows up here first."""
    vs = _store(tmp_path)
    vs.add([_row(f"a:{i}", "a.py", seed=i) for i in range(3)])
    vs.add([_row(f"b:{i}", "b.py", seed=i) for i in range(2)])

    assert vs.supersede_source("a.py") == 3
    assert vs.count() == 5                                   # nothing deleted
    assert all(r["current"] is False for r in vs.rows_for_source("a.py"))
    assert all(r["current"] is True for r in vs.rows_for_source("b.py"))   # neighbours untouched


def test_supersede_is_idempotent_and_leaves_rows_byte_identical(tmp_path: Path) -> None:
    """Second call returns 0 (nothing was current) and writes NOTHING — the rows, vectors included,
    are the same objects' values as after the first call."""
    vs = _store(tmp_path)
    vs.add([_row(f"a:{i}", "a.py", seed=i) for i in range(4)])
    assert vs.supersede_source("a.py") == 4
    after_first = _by_id(vs.rows_for_source("a.py"))

    assert vs.supersede_source("a.py") == 0
    assert _by_id(vs.rows_for_source("a.py")) == after_first
    assert vs.count() == 4


def test_already_superseded_rows_are_carried_through_unchanged(tmp_path: Path) -> None:
    """A path with BOTH history and a current version: superseding flips only the current rows and
    re-lands the old ones exactly as they were. `flipped` counts the flips, not the rows moved."""
    vs = _store(tmp_path)
    vs.add([_row("old:0", "a.py", current=False, seed=9)])          # a retained older version
    vs.add([_row(f"new:{i}", "a.py", seed=i) for i in range(2)])    # the HEAD projection
    old_before = _by_id(vs.rows_for_source("a.py"))["old:0"]

    assert vs.supersede_source("a.py") == 2                          # only the 2 current ones

    rows = _by_id(vs.rows_for_source("a.py"))
    assert set(rows) == {"old:0", "new:0", "new:1"}
    assert rows["old:0"] == old_before                               # the history row is untouched
    assert all(r["current"] is False for r in rows.values())


def test_supersede_on_an_unknown_path_is_a_no_op(tmp_path: Path) -> None:
    vs = _store(tmp_path)
    vs.add([_row("a:0", "a.py")])
    assert vs.supersede_source("nowhere.py") == 0
    assert vs.count() == 1


def test_supersede_before_any_write_is_a_no_op(tmp_path: Path) -> None:
    """No table yet — the store must not create one, or crash, on a read-shaped call."""
    assert _store(tmp_path).supersede_source("a.py") == 0


# ── Item 2's falsifier: a hostile path must not break the pushed-down predicate ───────────

def test_a_path_with_a_quote_is_read_and_superseded_correctly(tmp_path: Path) -> None:
    """The pushdown's falsifier: an apostrophe in the source path must not truncate the predicate,
    return the wrong rows, or return none. A decoy path shares a prefix up to the quote."""
    vs = _store(tmp_path)
    vs.add([_row(f"n:{i}", NASTY, seed=i) for i in range(3)])
    vs.add([_row("decoy:0", "notes/it", seed=7)])
    vs.add([_row("other:0", "b.py", seed=8)])

    assert {r["id"] for r in vs.rows_for_source(NASTY)} == {"n:0", "n:1", "n:2"}
    assert vs.supersede_source(NASTY) == 3
    assert all(r["current"] is False for r in vs.rows_for_source(NASTY))
    assert vs.rows_for_source("notes/it")[0]["current"] is True      # the decoy is untouched
    assert vs.count() == 5


def test_a_path_deeper_than_any_default_limit_is_fully_read_and_fully_flipped(
        tmp_path: Path) -> None:
    """Item 2's OTHER falsifier (bp-103), and the sharper of the two. The pushdown reads and writes
    through a query builder, and LanceDB's vector search caps at 10 rows by default; the pushdown
    relies on `limit(0)` meaning UNLIMITED. If that is ever wrong, a deep path is silently
    HALF-superseded — some rows flipped, some left `current=true` — which is worse than the O(N)
    cost bp-103 removed, because a half-flipped path corrupts the current-view (D3) permanently and
    silently. 137 rows: an order of magnitude past the default cap.

    (The `update` half needs no `limit` at all — it takes a predicate, not a query. This test pins
    that too: it is exactly the asymmetry that would let the READ truncate while the WRITE did
    not, leaving `rows_for_source` reporting a path that looks shorter than it is.)"""
    deep = 137
    vs = _store(tmp_path)
    vs.add([_row(f"d:{i}", "deep.py", seed=i) for i in range(deep)])
    vs.add([_row("other:0", "b.py", seed=1)])

    assert len(vs.rows_for_source("deep.py")) == deep       # the READ is not truncated

    assert vs.supersede_source("deep.py") == deep           # ...and neither is the count
    rows = vs.rows_for_source("deep.py")
    assert len(rows) == deep and all(r["current"] is False for r in rows), (
        f"only {sum(1 for r in rows if r['current'] is False)} of {deep} rows flipped — a deep "
        "path was silently half-superseded (bp-103 §10: limit(0) is not unlimited here)"
    )
    assert vs.count() == deep + 1                           # keep-and-link: nothing deleted
    assert vs.rows_for_source("b.py")[0]["current"] is True  # neighbour untouched
    assert vs.supersede_source("deep.py") == 0              # idempotent at depth


def test_supersede_never_reads_or_rewrites_the_vector_column(tmp_path: Path) -> None:
    """bp-103's structural guarantee, distinct from the byte-equality test above. That one proves
    the vectors came back unchanged; this one proves they were never NAMED — `update` writes only
    the columns it is given, so `vector` is not read, not marshalled, and not written. A future
    re-land regression would still pass byte-equality on a good day and fail here always: the
    store's own table proxy records which columns the write touched."""
    vs = _store(tmp_path)
    vs.add([_row(f"a:{i}", "a.py", seed=i) for i in range(3)])

    written: list[set[str]] = []
    inner = type(vs)._table

    class _Spy:
        """Records which columns each `update` names, forwarding everything else untouched."""

        def __init__(self, raw: VectorTable) -> None:
            self._raw = raw

        def update(self, where: str, values: Mapping[str, object]) -> UpdateResult:
            written.append(set(values))
            return self._raw.update(where, values)

        def __getattr__(self, name: str) -> Any:
            return getattr(self._raw, name)

    def spied() -> VectorTable:
        return _Spy(inner(vs))

    vs._table = spied       # type: ignore[method-assign]  # test instrument, instance-scoped

    assert vs.supersede_source("a.py") == 3
    assert written == [{"current"}], f"the flip wrote columns beyond `current`: {written}"


def test_delete_source_with_a_quote_deletes_exactly_that_path(tmp_path: Path) -> None:
    """`delete_source` no longer materializes the table to build an id list; it deletes on the
    `source_path` predicate. Same rows, hostile path included — and nobody else's."""
    vs = _store(tmp_path)
    vs.add([_row(f"n:{i}", NASTY, seed=i) for i in range(3)])
    vs.add([_row("decoy:0", "notes/it", seed=7)])
    vs.add([_row("other:0", "b.py", seed=8)])

    vs.delete_source(NASTY)

    assert vs.rows_for_source(NASTY) == []
    assert {r["id"] for r in vs.all_rows()} == {"decoy:0", "other:0"}


def test_delete_source_is_idempotent_and_safe_before_any_write(tmp_path: Path) -> None:
    vs = _store(tmp_path)
    vs.delete_source("a.py")                        # no table at all
    vs.add([_row("a:0", "a.py")])
    vs.delete_source("a.py")
    vs.delete_source("a.py")                        # already gone
    assert vs.count() == 0


def test_delete_source_does_not_reach_rows_of_another_path(tmp_path: Path) -> None:
    """An `id` is `{doc_id}:{chunk_hash}` and `doc_id` need not equal `source_path` (a rename, an
    `id::` property), so two paths CAN carry the same id. The old id-list delete would take both;
    the predicate takes only the named path. Regression guard on that improvement."""
    vs = _store(tmp_path)
    vs.add([{**_row("shared", "a.md", seed=1)}])
    vs.add([{**_row("shared", "b.md", seed=2)}])
    vs.delete_source("a.md")
    remaining = vs.all_rows()
    assert len(remaining) == 1 and remaining[0]["source_path"] == "b.md"


# ── the migration path must still work on a pre-bp-099 store ─────────────────────────────

def test_supersede_works_on_a_store_migrated_from_the_pre_current_schema(tmp_path: Path) -> None:
    """`_migrate_current_if_needed` (`:109`) shares the read-and-re-land idiom bp-100 touched. It
    runs once per instance on a store whose schema predates the `current` column; a store that came
    through it must supersede normally, vectors intact."""
    path = tmp_path / "v.lance"
    legacy = pa.schema([
        ("id", pa.string()), ("digest", pa.string()), ("title", pa.string()),
        ("source_path", pa.string()), ("chunk_index", pa.int32()),
        ("provenance", pa.string()), ("text", pa.string()),
        ("layer", pa.string()), ("qualname", pa.string()),
        ("line_start", pa.int32()), ("line_end", pa.int32()),
        ("vector", pa.list_(pa.float32(), DIM)),
    ])
    pre = VectorStore(path, dim=DIM)
    pre._db.create_table(TABLE, schema=legacy).add(
        [{k: v for k, v in _row("a:0", "a.py", seed=1).items() if k != "current"}]
    )

    vs = VectorStore(path, dim=DIM)                 # fresh instance → the migration arms
    vs.add([_row("a:1", "a.py", seed=2)])           # ...and fires here
    rows = _by_id(vs.rows_for_source("a.py"))
    assert set(rows) == {"a:0", "a:1"}
    assert all(r["current"] is True for r in rows.values())     # migrated rows stamped current

    before = dict(rows)
    assert vs.supersede_source("a.py") == 2
    after = _by_id(vs.rows_for_source("a.py"))
    for rid in before:
        assert after[rid]["vector"] == before[rid]["vector"]
        assert after[rid]["current"] is False


def test_rows_for_source_still_works_on_an_unmigrated_pre_current_store(tmp_path: Path) -> None:
    """The read pushes down on `source_path`, a column EVERY schema version has (it predates both
    the layer and the `current` migrations). So `rows_for_source` is schema-agnostic and unchanged
    by bp-103 on a legacy store — which matters, because `code_corpus.sync` reads before it
    writes."""
    path = tmp_path / "v.lance"
    legacy = pa.schema([
        ("id", pa.string()), ("digest", pa.string()), ("title", pa.string()),
        ("source_path", pa.string()), ("chunk_index", pa.int32()),
        ("provenance", pa.string()), ("text", pa.string()),
        ("vector", pa.list_(pa.float32(), DIM)),
    ])
    pre = VectorStore(path, dim=DIM)
    pre._db.create_table(TABLE, schema=legacy).add([
        {"id": "a:0", "digest": "d1", "title": "a.py", "source_path": "a.py", "chunk_index": 0,
         "provenance": Provenance.CODE.value, "text": "x", "vector": [1.0, 2.0, 3.0, 4.0]},
    ])

    rows = VectorStore(path, dim=DIM).rows_for_source("a.py")
    assert [r["id"] for r in rows] == ["a:0"]
    assert "current" not in rows[0]                 # honestly reflects the un-migrated schema


def test_supersede_on_an_unmigrated_pre_current_store_fails_loudly(tmp_path: Path) -> None:
    """[banner: correction] A RECORDED behavior change from bp-103, pinned so it cannot drift
    unnoticed.

    The pushed-down predicate names `current`, so on a pre-bp-099 store whose schema has no such
    column it RAISES. The old body silently returned 0 — and that silence was the worse outcome:
    `code_corpus.sync` supersedes BEFORE it adds, and the `add` that follows arms
    `_migrate_current_if_needed`, which stamps every existing row `current=true`. So the old path
    left the superseded version AND the new HEAD both current — silent D3 current-view corruption,
    reported as a clean `superseded_rows=0`. Failing loudly is strictly better.

    Whether `supersede_source` should instead ARM the migration is a design question (it would
    reintroduce a full materialization on the first call of each instance, the exact O(N) term
    finding-0169 is about), routed as **finding-0180** rather than settled here. If that decision
    lands, this test changes with it — visibly."""
    path = tmp_path / "v.lance"
    legacy = pa.schema([
        ("id", pa.string()), ("source_path", pa.string()),
        ("vector", pa.list_(pa.float32(), DIM)),
    ])
    pre = VectorStore(path, dim=DIM)
    pre._db.create_table(TABLE, schema=legacy).add(
        [{"id": "a:0", "source_path": "a.py", "vector": [1.0, 2.0, 3.0, 4.0]}]
    )

    with pytest.raises(Exception, match="(?i)current"):
        VectorStore(path, dim=DIM).supersede_source("a.py")
