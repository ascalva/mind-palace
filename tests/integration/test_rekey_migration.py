"""Chunk-key migration — build plan Item 1c (`rekey_store`): old `{digest}:{index}` → doc-scoped.

Proves the migration re-keys existing rows to `(source_path, chunk_hash)` IN PLACE, keeps vectors
(no re-embed), coalesces identical chunks within a source (§3), keeps distinct documents' shared
text as two points (§7), and is idempotent — reading the derived rows directly, so it does NOT
depend on the catalog (the reset+rescan trap it replaces). Deterministic; no model, no network.
"""

from __future__ import annotations

import pytest

from core.ingest.index import rekey_preview, rekey_store
from core.kernel.clearance import MAINTENANCE_READ
from core.kernel.ingest.amend import chunk_point_id
from core.kernel.ingest.chunk import Chunk
from core.stores.vectorstore import VectorStore


def _old_row(digest, idx, source_path, text, vector):
    """A row under the OLD `{digest}:{chunk_index}` key scheme (pre-1c)."""
    return {"id": f"{digest}:{idx}", "digest": digest, "title": "n", "source_path": source_path,
            "chunk_index": idx, "provenance": "authored-solo", "text": text, "vector": vector}


def test_rekey_migrates_old_ids_and_preserves_vectors(tmp_path):
    store = VectorStore(tmp_path / "v.lance", dim=2)
    store.add([
        _old_row("dig1", 0, "a.md", "hello", [0.1, 0.2]),
        _old_row("dig1", 1, "a.md", "world", [0.3, 0.4]),
    ])
    assert rekey_preview(store) == (2, 2)     # both old-format ids change; nothing mutated yet
    assert store.count() == 2

    assert rekey_store(store) == (2, 2)
    rows = {r["id"]: r for r in store.all_rows(clearance=MAINTENANCE_READ)}
    assert set(rows) == {chunk_point_id("a.md", Chunk(0, "hello")),
                         chunk_point_id("a.md", Chunk(1, "world"))}
    # Vectors survive the re-key unchanged — no re-embed (float32 round-trip, hence approx).
    v0 = rows[chunk_point_id("a.md", Chunk(0, "hello"))]["vector"]
    assert v0 == pytest.approx([0.1, 0.2], abs=1e-6)


def test_rekey_coalesces_identical_chunks_within_a_source(tmp_path):
    store = VectorStore(tmp_path / "v.lance", dim=2)
    store.add([
        _old_row("dig1", 0, "a.md", "same", [0.1, 0.2]),
        _old_row("dig1", 1, "a.md", "same", [0.1, 0.2]),    # duplicate chunk → one point (§3)
    ])
    assert rekey_store(store) == (2, 1)


def test_rekey_distinct_sources_sharing_text_keep_both_points(tmp_path):
    # §7 corroboration: identical text in two DIFFERENT documents stays two points (doc-scoped id).
    store = VectorStore(tmp_path / "v.lance", dim=2)
    store.add([
        _old_row("dig1", 0, "a.md", "shared", [0.1, 0.2]),
        _old_row("dig2", 0, "b.md", "shared", [0.1, 0.2]),
    ])
    assert rekey_store(store) == (2, 2)
    assert {r["source_path"] for r in store.all_rows(
        clearance=MAINTENANCE_READ)} == {"a.md", "b.md"}


def test_rekey_is_idempotent(tmp_path):
    store = VectorStore(tmp_path / "v.lance", dim=2)
    store.add([_old_row("dig1", 0, "a.md", "hello", [0.1, 0.2])])
    rekey_store(store)
    assert rekey_preview(store) == (1, 0)          # already new-keyed → nothing left to change
    assert rekey_store(store) == (1, 1)            # a second run is a no-op
