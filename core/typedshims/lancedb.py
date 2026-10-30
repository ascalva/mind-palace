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
from datetime import timedelta
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

    def offset(self, n: int) -> VectorQuery: ...

    def to_list(self) -> list[Row]: ...

    # [cross-ref: extension] step C (docs/brainstorms/shared-vectors.md; eval/quantization_bench.py)
    # sweeps the compressed indexes, so it needs their three query knobs. Read off the INSTALLED
    # 0.33.0, not the docs: on IVF_PQ, IVF_SQ and IVF_RQ indexes each built here, `nprobes` and
    # `refine_factor` chain and answer, and `bypass_vector_index()` returns the pre-index flat
    # result exactly.

    def nprobes(self, n: int) -> VectorQuery: ...

    def refine_factor(self, factor: int) -> VectorQuery: ...

    def bypass_vector_index(self) -> VectorQuery: ...


class VectorTable(Protocol):
    """The slice of a LanceDB table the store calls."""

    def add(self, rows: Sequence[Mapping[str, object]] | pa.Table) -> None: ...

    def create_index(self, *, metric: str, index_type: str, num_partitions: int | None = ...,
                     num_sub_vectors: int | None = ..., num_bits: int | None = ...,
                     replace: bool = ...) -> None: ...

    def count_rows(self, filter: str | None = ...) -> int: ...

    def delete(self, predicate: str) -> None: ...

    def update(self, where: str, values: Mapping[str, object] | None = ..., *,
               values_sql: Mapping[str, str] | None = ...) -> UpdateResult: ...

    def schema_names(self) -> list[str]: ...

    def version(self) -> int: ...

    def to_arrow(self) -> ArrowTable: ...

    def search(self, vector: list[float]) -> VectorQuery: ...

    def scan(self) -> VectorQuery: ...

    # [cross-ref: extension] bp-153 brings the PHYSICAL maintenance calls
    # (dn-vector-membership-store §3): the dataset accumulates a version per write batch, and D2
    # makes `current_any` flips routine, so the rebuild ends with compaction + old-version cleanup
    # and housekeeping runs cleanup on cadence.
    #
    # ⚑ The note's §3 Q5 splits into two cases and only one is a finding. Widening THIS Protocol is
    # ordinary in-scope work — the shim is our code. The finding case would be the pinned lancedb
    # release having no such capability underneath, where widening conjures nothing. It does NOT
    # apply, and the check is the bp-103 rule (read the INSTALLED package, never the docs): 0.33.0's
    # `lancedb.table.Table` exposes `optimize` and `list_versions`, both verified to run here.
    #
    # `optimize` is named rather than the `compact_files` + `cleanup_old_versions` pair the API also
    # carries, for a reason found by running it: BOTH of those are deprecated as of 0.21.0 and route
    # through `Table.to_lance()`, which raises `ImportError` unless the optional `pylance` package
    # is installed — not a dependency of this project, and adding one to reach a deprecated path
    # would be the wrong direction. `optimize` (modeled on PostgreSQL's VACUUM) does both halves in
    # one call, on the supported path, with no extra package. Measured on a 7-version table: 7 -> 1
    # versions, row count unchanged.

    def optimize(self, *, cleanup_older_than: timedelta | None = ...,
                 delete_unverified: bool = ..., retrain: bool = ...) -> None: ...

    def list_versions(self) -> list[dict[str, object]]: ...


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

    def add(self, rows: Sequence[Mapping[str, object]] | pa.Table) -> None:
        """Rows as mappings, or one Arrow table — the bulk path: 147k vectors as Python lists cost
        gigabytes of boxed floats that an Arrow batch never allocates (step C's scratch copy)."""
        self._raw.add(rows)

    def create_index(self, *, metric: str, index_type: str, num_partitions: int | None = None,
                     num_sub_vectors: int | None = None, num_bits: int | None = None,
                     replace: bool = True) -> None:
        """Build (or replace) the table's vector index. Step C measures IVF_FLAT, IVF_PQ, IVF_SQ and
        IVF_RQ through this call, each verified on 0.33.0; `None` takes the package's default.

        `num_bits` is forwarded only when given: the package's own default is 8, and for IVF_RQ
        that choice matters — measured on the 768-dimension paper vectors, 1-bit RaBitQ answers
        (recall@10 0.72, 0.85 refined) while the 8-bit default returns near-random neighbours."""
        bits: dict[str, int] = {} if num_bits is None else {"num_bits": num_bits}
        self._raw.create_index(metric=metric, index_type=index_type,
                               num_partitions=num_partitions, num_sub_vectors=num_sub_vectors,
                               replace=replace, **bits)

    def count_rows(self, filter: str | None = None) -> int:
        """Row count, optionally restricted by a SQL predicate. Server-side: a filtered count
        materializes nothing into Python (the whole point at the `supersede_source` call site)."""
        n: int = self._raw.count_rows(filter)
        return n

    def delete(self, predicate: str) -> None:
        self._raw.delete(predicate)

    def update(self, where: str, values: Mapping[str, object] | None = None, *,
               values_sql: Mapping[str, str] | None = None) -> UpdateResult:
        """In-place column write on every row matching `where`. Rows are UPDATED, never
        rewritten by the caller: columns the caller does not name — `vector` above all — are
        not read, not marshalled, and therefore cannot be re-derived or dropped.

        [cross-ref: extension] `values_sql` (A3, the shared plane's `held` cache) sets columns from
        SQL expressions. It exists for one measured reason: 0.33.0 cannot write an EMPTY list
        through `values` (`[]` fails Arrow's concat with "requires input of at least one array"),
        while `arrow_cast(make_array(), 'List(Utf8)')` through `values_sql` works."""
        result: UpdateResult = self._raw.update(
            where=where, values=dict(values) if values is not None else None,
            values_sql=dict(values_sql) if values_sql is not None else None)
        return result

    def schema_names(self) -> list[str]:
        """The table's column names — how a store tells a schema generation apart (A3's `held`)."""
        names: list[str] = list(self._raw.schema.names)
        return names

    def version(self) -> int:
        """The dataset's current version — how a migration notices a write it did not make."""
        return int(self._raw.version)

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

    def optimize(self, *, cleanup_older_than: timedelta | None = None,
                 delete_unverified: bool = False, retrain: bool = False) -> None:
        """Compact fragments and drop superseded dataset versions — the VACUUM-shaped call (§3).

        PHYSICAL only: it removes no logical row, so row count and search results are invariant
        across it — the property the compaction test asserts rather than assumes. A `None` window
        takes the package's own retention default; choosing a window is the caller's policy
        (`VectorStore.compact`), never the boundary shim's. Returns nothing in 0.33.0, which is why
        the store measures the effect with `list_versions` instead of trusting a return value."""
        self._raw.optimize(cleanup_older_than=cleanup_older_than,
                           delete_unverified=delete_unverified, retrain=retrain)

    def list_versions(self) -> list[dict[str, object]]:
        """Every dataset version the table still retains — the measurement that makes "the version
        count DROPPED" checkable instead of asserted."""
        versions: list[dict[str, object]] = self._raw.list_versions()
        return versions


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
