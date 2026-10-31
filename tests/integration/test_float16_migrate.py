"""Moving a store's vectors to float16 (dn-vector-membership-store A4; ops/float16_migrate.py).

The build must BE the old store cast — every column as it was, every vector in float16, the plane's
relations untouched — and anything else refuses the swap with the live store left alone. Driven on
real LanceDB through the real writers: dialogue turns land in the shared plane, code rows stay
physical.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import numpy as np
import pytest

from core.ingest.dialogue import DialogueCapture
from core.ingest.embed import Embedder
from core.kernel.clearance import CODE_READ, DIALOGUE_READ, MAINTENANCE_READ, MIRROR_READ
from core.kernel.stores.rawstore import RawStore
from core.stores.catalog import VaultCatalog
from core.stores.vectorstore import TABLE, VectorStore
from core.typedshims.lancedb import connect
from ops import float16_migrate
from ops.float16_migrate import migrate, verify
from tests.fixtures.fakes import HashingEmbedder

DIM = 32


def _code_row(rid: str, vector: list[float]) -> dict[str, Any]:
    return {"id": rid, "digest": "d1", "title": "x.py", "source_path": "core/x.py",
            "chunk_index": 0, "provenance": "code", "text": f"def {rid}(): ...",
            "layer": "code_text", "vector": vector}


def _float32_store(root: Path) -> Path:
    """A store as the live ones are before A4: float32, on the plane, prose and code both."""
    path = root / "data" / "vectors.lance"
    store = VectorStore(path, dim=DIM, precision="float32")
    emb = HashingEmbedder(DIM)
    cap = DialogueCapture(raw=RawStore(root / "raw"), store=store,
                          embedder=cast(Embedder, emb), catalog=VaultCatalog(root / "c.sqlite"))
    cap.capture_turn("ok, do it", conversation="c", turn_id="t1", role="user")
    cap.capture_turn("ok, do it", conversation="c", turn_id="t2", role="assistant")
    cap.capture_turn("a longer thought about atoms", conversation="c", turn_id="t3", role="user")
    store.add([_code_row(f"f{i}", v) for i, v in
               enumerate(emb.embed_documents(["def a(): pass", "def b(): return 1"]))])
    return path


def _physical(store: VectorStore) -> dict[str, dict[str, Any]]:
    return {str(r["id"]): r for page in store.physical_pages(clearance=MAINTENANCE_READ)
            for r in page}


def test_a_float32_store_becomes_exactly_its_float16_cast(tmp_path: Path) -> None:
    path = _float32_store(tmp_path)
    before = VectorStore(path, dim=DIM)
    rows_before = _physical(before)
    mirror_before = sorted((r["id"], r["text"]) for r in before.all_rows(clearance=MIRROR_READ))
    dialogue_before = sorted(r["id"] for r in before.all_rows(clearance=DIALOGUE_READ))
    report = migrate(path, dim=DIM, fingerprint=None, archive_root=tmp_path / "archive")
    assert report.verified and report.swapped and report.plane_copied, str(report)
    assert report.rows == len(rows_before) == 4          # 2 prose atoms (one shared) + 2 code

    after = VectorStore(path, dim=DIM)
    assert after.vector_precision() == "float16"
    rows_after = _physical(after)
    assert rows_after.keys() == rows_before.keys()
    for rid, old in rows_before.items():
        new = rows_after[rid]
        assert {k: v for k, v in new.items() if k != "vector"} == {
            k: v for k, v in old.items() if k != "vector"}
        assert np.array_equal(np.asarray(new["vector"], dtype=np.float32),
                              np.asarray(old["vector"], dtype=np.float32).astype(np.float16)
                              .astype(np.float32))
    # the plane's relations came across whole: every reader sees what it saw
    assert sorted((r["id"], r["text"]) for r in after.all_rows(clearance=MIRROR_READ)) == \
        mirror_before
    assert sorted(r["id"] for r in after.all_rows(clearance=DIALOGUE_READ)) == dialogue_before
    query = [float(x) for x in rows_before["f1"]["vector"]]
    assert after.search(query, k=1, clearance=CODE_READ)[0]["id"] == "f1"
    # the old store is archived intact, still float32
    archived = VectorStore(Path(report.archive), dim=DIM)
    assert Path(report.archive).name.startswith("vectors.lance-pre-f16")
    assert archived.vector_precision() == "float32" and len(_physical(archived)) == 4
    # idempotent
    assert migrate(path, dim=DIM, fingerprint=None,
                   archive_root=tmp_path / "archive").already_float16


def test_a_dry_run_swaps_nothing(tmp_path: Path) -> None:
    path = _float32_store(tmp_path)
    report = migrate(path, dim=DIM, fingerprint=None, archive_root=tmp_path / "archive",
                     dry_run=True)
    assert report.verified and not report.swapped
    assert VectorStore(path, dim=DIM).vector_precision() == "float32"
    assert Path(report.build).exists() and not (tmp_path / "archive").exists()


def test_verify_catches_one_vector_the_cast_does_not_explain(tmp_path: Path) -> None:
    old = VectorStore(_float32_store(tmp_path), dim=DIM)
    rows = [r for page in old.physical_pages(clearance=MAINTENANCE_READ) for r in page]
    rows[0] = {**rows[0], "vector": [float(x) + 0.01 for x in rows[0]["vector"]]}
    tampered = VectorStore(tmp_path / "tampered.lance", dim=DIM)
    tampered.copy_in(rows)
    problems = verify(old, tampered)
    assert any("1 old rows not reproduced, 1 rows the old store lacks" in p for p in problems)
    assert any("plane database" in p for p in problems)    # and its relations were never copied


def test_a_writer_after_the_build_refuses_the_swap(tmp_path: Path,
                                                   monkeypatch: pytest.MonkeyPatch) -> None:
    path = _float32_store(tmp_path)
    real = float16_migrate.verify

    def verify_then_write(old: VectorStore, new: VectorStore) -> list[str]:
        out = real(old, new)
        connect(str(path)).open_table(TABLE).add(
            [{**_code_row("late", [0.5] * DIM), "qualname": "", "line_start": 0,
              "line_end": 0, "current": True, "held": [], "held_ever": []}])
        return out

    monkeypatch.setattr(float16_migrate, "verify", verify_then_write)
    report = migrate(path, dim=DIM, fingerprint=None, archive_root=tmp_path / "archive")
    assert report.refused and not report.swapped
    live = VectorStore(path, dim=DIM)
    assert live.vector_precision() == "float32" and "late" in _physical(live)


def test_a_store_not_on_the_plane_is_sent_to_plane_migrate_first(tmp_path: Path) -> None:
    import pyarrow as pa

    path = tmp_path / "vectors.lance"
    fields: list[tuple[str, pa.DataType]] = [
        ("id", pa.string()), ("digest", pa.string()), ("title", pa.string()),
        ("source_path", pa.string()), ("chunk_index", pa.int32()), ("provenance", pa.string()),
        ("text", pa.string()), ("layer", pa.string()), ("qualname", pa.string()),
        ("line_start", pa.int32()), ("line_end", pa.int32()), ("current", pa.bool_()),
        ("vector", pa.list_(pa.float32(), DIM))]
    connect(str(path)).create_table(TABLE, schema=pa.schema(fields)).add(
        [{**_code_row("a", [0.1] * DIM), "qualname": "", "line_start": 0, "line_end": 0,
          "current": True}])
    report = migrate(path, dim=DIM, fingerprint=None, archive_root=tmp_path / "archive")
    assert "plane_migrate" in report.refused and not report.swapped
