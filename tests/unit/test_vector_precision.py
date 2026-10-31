"""The vector column's precision (dn-vector-membership-store Amendment A4) — unit tier.

A store creates its table in float16; a table keeps the precision it was created with, through
reads, writes and the in-place schema migrations; only `ops/float16_migrate.py` changes it. Each
claim is pinned on the stored bytes, not on a flag: what comes back must be exactly the float16 (or
float32) value of what was written.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pyarrow as pa

from core.kernel.clearance import CODE_READ
from core.stores.vectorstore import TABLE, VectorStore
from core.typedshims.lancedb import connect

DIM = 8
VEC = [0.1234567, -0.7654321, 0.3333333, 0.0001234, -0.5, 0.25, 0.9999999, -0.0000123]


def _code_row(rid: str, vector: list[float]) -> dict[str, Any]:
    return {"id": rid, "digest": "d", "title": "t", "source_path": "core/x.py", "chunk_index": 0,
            "provenance": "code", "text": f"def {rid}(): ...", "layer": "code_text",
            "vector": vector}


def _stored(store: VectorStore) -> list[float]:
    rows = [r for page in store.physical_pages(clearance=CODE_READ) for r in page]
    return [float(x) for x in rows[0]["vector"]]


def _as(dtype: type[np.floating[Any]], v: list[float]) -> list[float]:
    return [float(x) for x in np.asarray(v, dtype=np.float32).astype(dtype)]


def test_a_new_store_keeps_its_vectors_in_float16(tmp_path: Path) -> None:
    store = VectorStore(tmp_path / "v.lance", dim=DIM)
    store.add([_code_row("a", VEC)])
    assert store.vector_precision() == "float16"
    assert _stored(store) == _as(np.float16, VEC)
    assert _stored(store) != _as(np.float32, VEC)          # the control: it really was rounded


def test_a_float32_store_round_trips_exactly(tmp_path: Path) -> None:
    store = VectorStore(tmp_path / "v.lance", dim=DIM, precision="float32")
    store.add([_code_row("a", VEC)])
    assert store.vector_precision() == "float32"
    assert _stored(store) == _as(np.float32, VEC)


def test_an_existing_float32_table_keeps_its_precision_under_the_float16_default(
        tmp_path: Path) -> None:
    path = tmp_path / "v.lance"
    VectorStore(path, dim=DIM, precision="float32").add([_code_row("a", VEC)])
    reopened = VectorStore(path, dim=DIM)                  # default precision: float16
    reopened.add([_code_row("b", VEC)])
    assert reopened.vector_precision() == "float32"
    rows = {r["id"]: [float(x) for x in r["vector"]]
            for page in reopened.physical_pages(clearance=CODE_READ) for r in page}
    assert rows == {"a": _as(np.float32, VEC), "b": _as(np.float32, VEC)}


def test_the_layer_migration_keeps_an_old_tables_precision(tmp_path: Path) -> None:
    """The in-place schema migrations rebuild the table; A4 says they must not change its precision
    (they promise "vectors intact")."""
    path = tmp_path / "v.lance"
    fields: list[tuple[str, pa.DataType]] = [
        ("id", pa.string()), ("digest", pa.string()), ("title", pa.string()),
        ("source_path", pa.string()), ("chunk_index", pa.int32()), ("provenance", pa.string()),
        ("text", pa.string()), ("vector", pa.list_(pa.float32(), DIM))]
    old = {k: v for k, v in _code_row("old", VEC).items() if k != "layer"}
    connect(str(path)).create_table(TABLE, schema=pa.schema(fields)).add([old])
    store = VectorStore(path, dim=DIM)                     # default precision: float16
    store.add([_code_row("new", VEC)])                     # triggers the 8-column migration
    assert store.vector_precision() == "float32"
    rows = {r["id"]: [float(x) for x in r["vector"]]
            for page in store.physical_pages(clearance=CODE_READ) for r in page}
    assert rows["old"] == _as(np.float32, VEC)


def test_copy_in_writes_rows_verbatim_in_the_tables_precision(tmp_path: Path) -> None:
    src = VectorStore(tmp_path / "a.lance", dim=DIM, precision="float32")
    src.add([_code_row("a", VEC)])
    page = next(src.physical_pages(clearance=CODE_READ))
    dst = VectorStore(tmp_path / "b.lance", dim=DIM)
    assert dst.copy_in(page) == 1
    got = next(dst.physical_pages(clearance=CODE_READ))[0]
    assert {k: v for k, v in got.items() if k != "vector"} == {
        k: v for k, v in page[0].items() if k != "vector"}
    assert [float(x) for x in got["vector"]] == _as(np.float16, VEC)
