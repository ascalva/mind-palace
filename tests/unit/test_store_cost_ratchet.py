"""The `supersede_source` cost ratchet (bp-100 Item 1, warrant finding-0169).

A property is only real when a test PROVES it. finding-0169 measured `VectorStore.supersede_source`
materializing the WHOLE table — vectors included — **twice** per call (11.7 s per materialization at
22,621 rows x 2560 dims), which killed the `code_backfill` job at 847 of ~1,542 versions. The
semantics (keep-and-link, dn-temporal-code-corpus D2) are correct; the cost is not.

This module is the structural enforcement. It measures, deterministically, how much the store pulls
out of Arrow into Python per call — **never wall-clock**, so it cannot flake on a loaded machine.
The instrument is a counting proxy wrapped around the store's own `_table()`: every
`to_arrow().to_pylist()` is counted, along with the rows and vector floats it marshalled.

Two ratchets, deliberately separate:

* `test_supersede_cost_is_independent_of_unrelated_store_size` — the REAL bound (O(d), not O(N)).
  It is `xfail(strict=True)` today: closing it needs a store-side predicate + projection, i.e. new
  LanceDB surface on `core/typedshims/lancedb.py`, which is OUTSIDE bp-100's write_scope
  (finding-0176). Strict xfail means the day the fix lands this test XPASSes and FAILS the suite,
  forcing the marker off — a ratchet that cannot be quietly left behind.
* `test_supersede_makes_at_most_one_full_materialization` — the half bp-100 can land in scope.
  RED at HEAD (2 materializations: `rows_for_source` directly, then again inside `delete_source`).

Temp stores only. No network, no live store, no daemon.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from core.kernel.provenance import Provenance
from core.stores.vectorstore import VectorStore

DIM = 8


@dataclass
class Meter:
    """What one operation pulled out of Arrow and into Python."""

    materializations: int = 0        # full `to_arrow().to_pylist()` calls
    rows: int = 0                    # rows marshalled across all of them
    vector_floats: int = 0           # float values marshalled from the `vector` column
    sizes: list[int] = field(default_factory=list)

    def reset(self) -> None:
        self.materializations = 0
        self.rows = 0
        self.vector_floats = 0
        self.sizes = []


class _CountingArrow:
    def __init__(self, inner: Any, meter: Meter) -> None:
        self._inner, self._meter = inner, meter

    def to_pylist(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = self._inner.to_pylist()
        self._meter.materializations += 1
        self._meter.rows += len(rows)
        self._meter.sizes.append(len(rows))
        self._meter.vector_floats += sum(len(r.get("vector") or ()) for r in rows)
        return rows

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)


class _CountingTable:
    def __init__(self, inner: Any, meter: Meter) -> None:
        self._inner, self._meter = inner, meter

    def to_arrow(self) -> _CountingArrow:
        return _CountingArrow(self._inner.to_arrow(), self._meter)

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

@pytest.mark.xfail(
    strict=True,
    reason="blocked on the typedshim widening (finding-0176): a store-side predicate + column "
           "projection needs new LanceDB surface on core/typedshims/lancedb.py, outside bp-100's "
           "write_scope. Remove this marker the moment the pushdown lands.",
)
def test_supersede_cost_is_independent_of_unrelated_store_size(tmp_path: Path) -> None:
    """finding-0169's bound, stated as a test: superseding one path costs a function of THAT PATH's
    rows, not of the store's size. The falsifier for the whole plan — if this passes with the old
    full-scan implementation, the instrument is theatre."""
    small = _cost_of_supersede(tmp_path / "small", depth=4, unrelated=0)
    large = _cost_of_supersede(tmp_path / "large", depth=4, unrelated=200)
    assert large.rows == small.rows, (
        f"cost grows with unrelated store size: {small.rows} rows at N=4, "
        f"{large.rows} rows at N=204 (finding-0169)"
    )


@pytest.mark.xfail(
    strict=True,
    reason="blocked on the typedshim widening (finding-0176) — same pushdown as the row ratchet.",
)
def test_supersede_does_not_marshal_the_vector_column_of_unrelated_rows(tmp_path: Path) -> None:
    """Q2 of the plan: the measured cost is Arrow->Python marshalling of the embedding column
    (`FixedSizeListArray::value_slice` in the wedged worker's stack), not inference. Flipping a
    boolean must not drag 2560 floats per unrelated row through Python."""
    small = _cost_of_supersede(tmp_path / "small", depth=4, unrelated=0)
    large = _cost_of_supersede(tmp_path / "large", depth=4, unrelated=200)
    assert large.vector_floats == small.vector_floats


# ── the half that lands inside bp-100's write_scope ──────────────────────────────────────

def test_supersede_makes_at_most_one_full_materialization(tmp_path: Path) -> None:
    """RED at HEAD: `supersede_source` reads the whole table via `rows_for_source`, then
    `delete_source` reads it AGAIN to collect the very ids the caller already holds. Whatever the
    scan costs, paying it twice is indefensible."""
    meter = _cost_of_supersede(tmp_path, depth=4, unrelated=25)
    assert meter.materializations <= 1, (
        f"{meter.materializations} full materializations per supersede_source "
        f"(sizes={meter.sizes}); finding-0169 measured two"
    )


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
    """Negative control: the counting proxy is wired to something real — `all_rows`, which is
    honestly a full scan, must register as one. Without this, a green ratchet could mean 'the
    instrument is broken', not 'the cost is bounded'."""
    vs = _store_with(tmp_path, depth=2, unrelated=3)
    meter = _instrument(vs)
    assert len(vs.all_rows()) == 5
    assert meter.materializations == 1 and meter.rows == 5
    assert meter.vector_floats == 5 * DIM
