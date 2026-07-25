"""The `supersede_source` cost ratchet (bp-100 Item 1 / bp-103, warrant finding-0169).

A property is only real when a test PROVES it. finding-0169 measured `VectorStore.supersede_source`
materializing the WHOLE table — vectors included — **twice** per call (11.7 s per materialization at
22,621 rows x 2560 dims), which killed the `code_backfill` job at 847 of ~1,542 versions. The
semantics (keep-and-link, dn-temporal-code-corpus D2) are correct; the cost is not.

This module is the structural enforcement. It measures, deterministically, how much the store pulls
out of Arrow into Python per call — **never wall-clock**, so it cannot flake on a loaded machine.
The instrument is a counting proxy wrapped around the store's own `_table()`.

[cross-ref: extension] bp-103 closed the two ratchets and their `xfail(strict=True)` markers came
off in the same commit as the fix. It also WIDENED the instrument, which is the more important
change: bp-100's proxy counted only `to_arrow().to_pylist()`, and bp-103's pushdown reads through
`scan().…to_list()` instead — a route the old meter could not see at all. Left alone, the ratchets
would have gone green partly because the instrument had gone blind. So `scan()`/`search()` reads are
now counted on the same `rows`/`vector_floats` totals ("rows marshalled into Python", by whatever
route), `materializations` keeps its narrower meaning (FULL-table Arrow pulls), and a new
`scan_reads` counter records the pushed-down route separately. Both ratchets are therefore strictly
STRONGER than when they were written: they now also catch a regression that scans without a
predicate.

Two ratchets, deliberately separate:

* `test_supersede_cost_is_independent_of_unrelated_store_size` — the REAL bound (O(d), not O(N)).
  GREEN since bp-103: `supersede_source` is one filtered `count_rows` plus one in-place `update`,
  so it marshals NOTHING and the measured cost is 0 at every store size.
* `test_supersede_makes_at_most_one_full_materialization` — the half bp-100 landed in scope (2 full
  materializations became 1). Kept as the lower ratchet: it must never climb back.

Two negative controls keep the instrument honest at both routes — a green ratchet must mean "the
cost is bounded", never "the meter is broken".

Temp stores only. No network, no live store, no daemon.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from core.kernel.provenance import Provenance
from core.stores.vectorstore import VectorStore

# NOTE: no `import pytest` above — bp-103 removed this module's last two
# `pytest.mark.xfail(strict=True)` markers along with the defect they guarded. Its absence is itself
# a small ratchet: re-introducing an xfail here has to be a deliberate, visible act.

DIM = 8


@dataclass
class Meter:
    """What one operation pulled out of the store and into Python — by EITHER route."""

    materializations: int = 0        # full `to_arrow().to_pylist()` calls
    scan_reads: int = 0              # pushed-down `scan()`/`search()` reads (bp-103's route)
    rows: int = 0                    # rows marshalled across all of them, both routes
    vector_floats: int = 0           # float values marshalled from the `vector` column
    sizes: list[int] = field(default_factory=list)

    def reset(self) -> None:
        self.materializations = 0
        self.scan_reads = 0
        self.rows = 0
        self.vector_floats = 0
        self.sizes = []

    def _charge(self, rows: list[dict[str, Any]]) -> None:
        self.rows += len(rows)
        self.sizes.append(len(rows))
        self.vector_floats += sum(len(r.get("vector") or ()) for r in rows)


class _CountingArrow:
    def __init__(self, inner: Any, meter: Meter) -> None:
        self._inner, self._meter = inner, meter

    def to_pylist(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = self._inner.to_pylist()
        self._meter.materializations += 1
        self._meter._charge(rows)
        return rows

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)


class _CountingQuery:
    """bp-103's route. The pushed-down builder is chainable, so every chaining method has to hand
    the proxy back — otherwise the count is lost at the first `.where()` and the meter reports a
    reassuring zero for a read that really happened."""

    def __init__(self, inner: Any, meter: Meter) -> None:
        self._inner, self._meter = inner, meter

    def where(self, predicate: str, **kw: Any) -> _CountingQuery:
        return _CountingQuery(self._inner.where(predicate, **kw), self._meter)

    def select(self, columns: Any) -> _CountingQuery:
        return _CountingQuery(self._inner.select(columns), self._meter)

    def limit(self, k: int) -> _CountingQuery:
        return _CountingQuery(self._inner.limit(k), self._meter)

    def metric(self, name: str) -> _CountingQuery:
        return _CountingQuery(self._inner.metric(name), self._meter)

    def to_list(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = self._inner.to_list()
        self._meter.scan_reads += 1
        self._meter._charge(rows)
        return rows


class _CountingTable:
    def __init__(self, inner: Any, meter: Meter) -> None:
        self._inner, self._meter = inner, meter

    def to_arrow(self) -> _CountingArrow:
        return _CountingArrow(self._inner.to_arrow(), self._meter)

    def scan(self) -> _CountingQuery:
        return _CountingQuery(self._inner.scan(), self._meter)

    def search(self, vector: list[float]) -> _CountingQuery:
        return _CountingQuery(self._inner.search(vector), self._meter)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)


def _instrument(store: VectorStore) -> Meter:
    """Wrap `store._table()` so every Arrow->Python materialization is counted. `VectorStore` is a
    plain dataclass, so an instance attribute shadows the method for this instance only."""
    meter = Meter()
    inner = type(store)._table

    def counted(_self: VectorStore = store) -> Any:
        return _CountingTable(inner(_self), meter)

    store._table = counted        # type: ignore[method-assign]  # test instrument, instance-scoped
    return meter


def _row(rid: str, path: str, *, current: bool = True) -> dict[str, Any]:
    return {
        "id": rid, "digest": "d", "title": path, "source_path": path,
        "chunk_index": 0, "provenance": Provenance.CODE.value, "text": rid,
        "layer": "code_ast", "qualname": "", "line_start": 0, "line_end": 0,
        "current": current, "vector": [float(len(rid) % 7)] * DIM,
    }


def _store_with(tmp_path: Path, *, depth: int, unrelated: int) -> VectorStore:
    """A temp store holding `depth` rows for path `hot.py` and `unrelated` rows on other paths."""
    vs = VectorStore(tmp_path / "v.lance", dim=DIM)
    vs.add([_row(f"hot:{i}", "hot.py") for i in range(depth)])
    if unrelated:
        vs.add([_row(f"cold{i}:0", f"cold{i}.py") for i in range(unrelated)])
    return vs


def _cost_of_supersede(tmp_path: Path, *, depth: int, unrelated: int) -> Meter:
    vs = _store_with(tmp_path, depth=depth, unrelated=unrelated)
    meter = _instrument(vs)
    assert vs.supersede_source("hot.py") == depth      # the semantics, unchanged
    return meter


# ── the real bound: O(depth), not O(total store) ─────────────────────────────────────────

def test_supersede_cost_is_independent_of_unrelated_store_size(tmp_path: Path) -> None:
    """finding-0169's bound, stated as a test: superseding one path costs a function of THAT PATH's
    rows, not of the store's size. The falsifier for the whole plan — if this passes with the old
    full-scan implementation, the instrument is theatre.

    [banner: correction] Was `xfail(strict=True)` (bp-100, blocked on the typedshim). bp-103 landed
    the pushdown, so the marker came off in the same commit as the fix. The ASSERTION is unchanged
    — the same bound, measured the same way; only the instrument grew, to also see bp-103's
    `scan()` route (see this module's docstring). It now reads 0 at both sizes, and the trailing
    assertion pins WHY that 0 is real rather than a blind meter."""
    small = _cost_of_supersede(tmp_path / "small", depth=4, unrelated=0)
    large = _cost_of_supersede(tmp_path / "large", depth=4, unrelated=200)
    assert large.rows == small.rows, (
        f"cost grows with unrelated store size: {small.rows} rows at N=4, "
        f"{large.rows} rows at N=204 (finding-0169)"
    )
    # ...and the bound is now ZERO, not merely equal: the flip is a predicate, so no row of any
    # kind — matched or unmatched — crosses into Python. Equality alone would also hold if both
    # sides scanned everything, which is precisely the state finding-0169 measured.
    assert (large.rows, large.materializations, large.scan_reads) == (0, 0, 0), (
        f"supersede_source still reads rows: {large.sizes} via {large.materializations} full "
        f"materializations + {large.scan_reads} scans (finding-0176 makes it zero of both)"
    )


def test_supersede_does_not_marshal_the_vector_column_of_unrelated_rows(tmp_path: Path) -> None:
    """Q2 of the plan: the measured cost is Arrow->Python marshalling of the embedding column
    (`FixedSizeListArray::value_slice` in the wedged worker's stack), not inference. Flipping a
    boolean must not drag 2560 floats per unrelated row through Python.

    [banner: correction] Was `xfail(strict=True)` (bp-100). Marker removed by bp-103 with the fix,
    assertion untouched. Post-bp-103 the guarantee is structural, not merely measured: `update()`
    never NAMES the `vector` column, so it is not read at all — it cannot be re-derived or
    dropped."""
    small = _cost_of_supersede(tmp_path / "small", depth=4, unrelated=0)
    large = _cost_of_supersede(tmp_path / "large", depth=4, unrelated=200)
    assert large.vector_floats == small.vector_floats
    assert large.vector_floats == 0, "the flip marshalled embedding floats it never needed"


# ── the lower ratchet bp-100 landed: it must never climb back ────────────────────────────

def test_supersede_makes_at_most_one_full_materialization(tmp_path: Path) -> None:
    """RED before bp-100: `supersede_source` read the whole table via `rows_for_source`, then
    `delete_source` read it AGAIN to collect the very ids the caller already held. Whatever the
    scan costs, paying it twice is indefensible. bp-100 took it to one; bp-103 to zero. Kept at
    `<= 1` deliberately — it is the FLOOR, and a floor that only ever ratchets down."""
    meter = _cost_of_supersede(tmp_path, depth=4, unrelated=25)
    assert meter.materializations <= 1, (
        f"{meter.materializations} full materializations per supersede_source "
        f"(sizes={meter.sizes}); finding-0169 measured two"
    )


def test_rows_for_source_reads_only_that_paths_rows(tmp_path: Path) -> None:
    """bp-103's other half. `rows_for_source` MUST keep carrying the `vector` column (the amendment
    path reuses those vectors instead of re-embedding), so unlike `supersede_source` its cost is
    not zero — but it must be O(depth), never O(store). Pushed down, it reads 4 rows out of 204."""
    vs = _store_with(tmp_path, depth=4, unrelated=200)
    meter = _instrument(vs)

    rows = vs.rows_for_source("hot.py")

    assert len(rows) == 4
    assert meter.materializations == 0, "rows_for_source still pulls the whole table through Arrow"
    assert meter.rows == 4, f"read {meter.rows} rows to return 4 (sizes={meter.sizes})"
    assert meter.vector_floats == 4 * DIM       # only the returned rows' vectors, nobody else's


def test_delete_source_needs_no_full_materialization(tmp_path: Path) -> None:
    """RED at HEAD: `delete_source` materializes the whole table just to rebuild an `id IN (...)`
    predicate. The path itself is a predicate — push it down. This is the note-amendment hot path
    too (`core/ingest/index.py:87`), not only the code lane."""
    vs = _store_with(tmp_path, depth=4, unrelated=25)
    meter = _instrument(vs)
    vs.delete_source("hot.py")
    assert meter.materializations == 0, \
        f"delete_source scanned {meter.sizes} rows just to rebuild an id list"
    assert vs.count() == 25


def test_the_instrument_actually_sees_a_full_scan(tmp_path: Path) -> None:
    """Negative control #1 — the Arrow route. The counting proxy is wired to something real:
    `all_rows`, which is honestly a full scan, must register as one. Without this, a green ratchet
    could mean 'the instrument is broken', not 'the cost is bounded'."""
    vs = _store_with(tmp_path, depth=2, unrelated=3)
    meter = _instrument(vs)
    assert len(vs.all_rows()) == 5
    assert meter.materializations == 1 and meter.rows == 5
    assert meter.vector_floats == 5 * DIM


def test_the_instrument_also_sees_the_pushed_down_scan_route(tmp_path: Path) -> None:
    """Negative control #2 — bp-103's route, and the reason the instrument had to grow. The
    pushdown reads through `scan().where(...).limit(0).to_list()`, which bp-100's meter could not
    see AT ALL. Had the ratchets been turned green against the old meter, the zero would have
    partly measured the instrument's blindness rather than the store's cost. This proves the new
    counter is wired to a read that really happens."""
    vs = _store_with(tmp_path, depth=2, unrelated=3)
    meter = _instrument(vs)

    assert len(vs.rows_for_source("hot.py")) == 2

    assert meter.scan_reads == 1, "the scan route is invisible to the meter — ratchets are theatre"
    assert meter.materializations == 0                 # and it did NOT go the Arrow route
    assert meter.rows == 2 and meter.vector_floats == 2 * DIM
