"""Typed facade over `lancedb` (type-system-as-core-audit.md §2.5 boundary wrapper).

lancedb ships no `py.typed` (V2, 2026-07-11), so a raw import launders `Any`
through every downstream call. This module is the ONE place core touches the raw
package: values coming back from lancedb are pinned to the minimal Protocol
surface the vector store actually uses, so the checked region sees honest types.
Compute/storage-only dependency — embedded, no daemon, no network (Invariant 2).

Do not widen these Protocols speculatively: they describe what core calls today,
and each addition should arrive with the call that needs it.

[cross-ref: extension] bp-103 (warrant **finding-0176**) brings four such calls, all
for `VectorStore.supersede_source`/`rows_for_source`: `update()` (in-place column
write), a FILTERED `count_rows(filter)`, `select()` (column projection) and
`scan()`. Additive — every pre-existing caller compiles and behaves unchanged.

**Why this file stopped being a pure typing facade.** Until bp-103 `connect()` simply
annotated the raw object and returned it; nothing was wrapped at runtime. `scan()`
has no counterpart on the raw `Table` — it *is* `search(None)`, an overload whose
`None` arm means "no vector, just filter/project". Absorbing that overload is
precisely what a boundary shim is for (finding-0176: "the shim is the place where the
raw package's overloads are made honest"), and it cannot be done with an annotation
alone. So `connect()` now returns thin ADAPTERS that add `scan()` and forward the
rest. The adapters spell every method out rather than forwarding through
`__getattr__`, because a `__getattr__` wrapper would launder `Any` straight back into
the checked region — the exact hole this module exists to close.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Protocol

import lancedb  # type: ignore[import-untyped]  # warrant: no py.typed upstream (V2); Any quarantined to this shim
import pyarrow as pa

# A row as LanceDB hands it back (Arrow -> Python). `object` values, not `Any`:
# consumers must narrow before doing anything value-shaped with a field.
Row = dict[str, object]


class ArrowTable(Protocol):
    """The slice of `pyarrow.Table` the store consumes from `to_arrow()`."""

    def to_pylist(self) -> list[Row]: ...


class TableNames(Protocol):
    """Result of `list_tables()` — we read only the name list."""

    tables: list[str]


class UpdateResult(Protocol):
    """Result of `Table.update` — rows matched-and-written, and the new table version.

    [banner: correction] Declared for completeness of the boundary, but the store deliberately
    does NOT read `rows_updated`. `UpdateResult` is the 0.33 return shape and `pyproject.toml:12`
    pins `lancedb>=0.10`, a range whose older members returned `None` from `update()`; the pin is
    outside bp-103's write_scope, so `VectorStore.supersede_source` derives its count from a
    filtered `count_rows()` instead (bp-103 §11, first parked decision). Raising the floor pin is
    the re-entry condition for trusting this field."""

    rows_updated: int
    version: int


class VectorQuery(Protocol):
    """LanceDB's chained query builder — `VectorStore.search` (KNN) and `.scan()` (filter-only)."""

    def metric(self, name: str) -> VectorQuery: ...

    def where(self, predicate: str, *, prefilter: bool = ...) -> VectorQuery: ...

    def select(self, columns: Sequence[str]) -> VectorQuery: ...

    def limit(self, k: int) -> VectorQuery: ...

    def to_list(self) -> list[Row]: ...


class VectorTable(Protocol):
    """The slice of a LanceDB table the store calls."""

    def add(self, rows: Sequence[Mapping[str, object]]) -> None: ...

    def count_rows(self, filter: str | None = ...) -> int: ...

    def delete(self, predicate: str) -> None: ...

    def update(self, where: str, values: Mapping[str, object]) -> UpdateResult: ...

    def to_arrow(self) -> ArrowTable: ...

    def search(self, vector: list[float]) -> VectorQuery: ...

    def scan(self) -> VectorQuery: ...


class VectorDB(Protocol):
    """The slice of a LanceDB connection the store calls."""

    def list_tables(self) -> TableNames: ...

    def open_table(self, name: str) -> VectorTable: ...

    def create_table(self, name: str, *, schema: pa.Schema) -> VectorTable: ...

    def drop_table(self, name: str) -> None: ...


class _Table:
    """Runtime adapter for one raw `lancedb.table.Table` — structurally a `VectorTable`.

    Every method is a one-line forward EXCEPT `scan()`, which is the whole reason the adapter
    exists: it names `search(None)` honestly so no caller has to pass a `None` "vector" to mean
    "no vector" (finding-0176). `limit(0)` on the returned builder means UNLIMITED — verified
    empirically against the installed 0.33.0, not read from documentation."""

    __slots__ = ("_raw",)

    def __init__(self, raw: Any) -> None:      # `Any` is the quarantined raw lancedb object
        self._raw = raw

    def add(self, rows: Sequence[Mapping[str, object]]) -> None:
        self._raw.add(rows)

    def count_rows(self, filter: str | None = None) -> int:
        """Row count, optionally restricted by a SQL predicate. Server-side: a filtered count
        materializes nothing into Python (the whole point at the `supersede_source` call site)."""
        n: int = self._raw.count_rows(filter)
        return n

    def delete(self, predicate: str) -> None:
        self._raw.delete(predicate)

    def update(self, where: str, values: Mapping[str, object]) -> UpdateResult:
        """In-place column write on every row matching `where`. Rows are UPDATED, never
        rewritten by the caller: columns the caller does not name — `vector` above all — are
        not read, not marshalled, and therefore cannot be re-derived or dropped."""
        result: UpdateResult = self._raw.update(where, dict(values))
        return result

    def to_arrow(self) -> ArrowTable:
        table: ArrowTable = self._raw.to_arrow()
        return table

    def search(self, vector: list[float]) -> VectorQuery:
        q: VectorQuery = self._raw.search(vector)
        return q

    def scan(self) -> VectorQuery:
        """A filter-only query over the table — no vector, no distance column, no distance
        ordering. This is `search(None)`, whose overload the shim absorbs rather than leaks."""
        q: VectorQuery = self._raw.search(None)
        return q


class _DB:
    """Runtime adapter for a raw lancedb connection — structurally a `VectorDB`.

    Exists only so `open_table`/`create_table` hand back `_Table` (which has `scan()`) rather
    than the raw table (which does not)."""

    __slots__ = ("_raw",)

    def __init__(self, raw: Any) -> None:      # `Any` is the quarantined raw lancedb object
        self._raw = raw

    def list_tables(self) -> TableNames:
        names: TableNames = self._raw.list_tables()
        return names

    def open_table(self, name: str) -> VectorTable:
        return _Table(self._raw.open_table(name))

    def create_table(self, name: str, *, schema: pa.Schema) -> VectorTable:
        return _Table(self._raw.create_table(name, schema=schema))

    def drop_table(self, name: str) -> None:
        self._raw.drop_table(name)


def connect(uri: str) -> VectorDB:
    """Open/create an embedded LanceDB at `uri` — the sole typed entry point."""
    return _DB(lancedb.connect(uri))
