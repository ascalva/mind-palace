"""The code embed lane's firewall + isolation ratchets (bp-092 Item 4; dn-code-ingest-pipeline).

F-CI1 — a CODE row must NEVER surface through a MirrorView or the MIRROR_READABLE-default search.
F-CI5 — a mirror-path instrument result must be BIT-IDENTICAL whether code rows are present or
        absent (the isolation ratchet, the `test_reference_edge_isolation` pattern on the vector
        plane). Permanent: this is the guard that adding the whole codebase to the store cannot
        perturb the self-model.

Plus the `layer`-column migration: an old 8-column store reset+rebuilds preserving every note row
bit-identically (text/digest/vector), count intact.
"""

from __future__ import annotations

from typing import cast

import pyarrow as pa
import pytest

from core.ingest.code_corpus import code_rows, derive_code_chunks
from core.ingest.embed import Embedder
from core.ingest.index import _chunk_row, semantic_search
from core.kernel.ingest.chunk import Chunk
from core.kernel.ingest.pipeline import IngestRecord
from core.kernel.mirror import MirrorView
from core.kernel.provenance import Provenance
from core.stores.vectorstore import TABLE, VectorStore
from tests.fixtures.embedding import DIM, FakeEmbedder


def _note_rows(store: VectorStore) -> int:
    rec = IngestRecord(digest="noteA", source_path="notes/a.md", title="A",
                       provenance=Provenance.AUTHORED_SOLO,
                       tags=frozenset(), links=frozenset(),
                       chunks=(Chunk(0, "alpha note about vectors"),
                               Chunk(1, "beta note about dreaming")), is_new=True)
    emb = FakeEmbedder()
    vecs = emb.embed_documents([c.text for c in rec.chunks])
    return store.add([_chunk_row(rec, c, v) for c, v in zip(rec.chunks, vecs, strict=True)])


def _add_code(store: VectorStore) -> int:
    src = '"""doc about vectors and dreaming."""\ndef f():\n    return 1\n'
    chunks = derive_code_chunks("m.py", src)
    vecs = FakeEmbedder().embed_documents([c.text for c in chunks])
    return store.add(code_rows("m.py", "blob1", chunks, vecs))


# ── F-CI1: CODE is unreachable through the mirror surfaces ───────────────────────────────

def test_fci1_code_never_surfaces_through_default_search(tmp_path):
    store = VectorStore(tmp_path / "v.lance", dim=DIM)
    _note_rows(store)
    _add_code(store)
    emb = cast(Embedder, FakeEmbedder())
    # the MIRROR_READABLE default must return only authored rows, never code
    hits = semantic_search("vectors and dreaming", emb, store, k=10)
    assert hits, "sanity: authored notes are retrievable"
    assert all(h["provenance"] != Provenance.CODE.value for h in hits)
    # the deliberate opt-in CAN reach code
    code_hits = semantic_search("vectors and dreaming", emb, store, k=10,
                                provenances={Provenance.CODE})
    assert code_hits and all(h["provenance"] == Provenance.CODE.value for h in code_hits)


def test_fci1_mirrorview_refuses_a_store_holding_code(tmp_path):
    store = VectorStore(tmp_path / "v.lance", dim=DIM)
    _note_rows(store)
    _add_code(store)
    # MirrorView.project reads MIRROR_READABLE only and re-validates — it must hold zero code rows
    view = MirrorView.project(store)
    assert all(r["provenance"] != Provenance.CODE.value for r in view.rows())
    assert len(view) == 2                              # exactly the two authored note chunks


# ── F-CI5: code rows present/absent leaves every mirror-path result unchanged ────────────

def test_fci5_mirror_path_results_bit_identical_with_and_without_code(tmp_path):
    store = VectorStore(tmp_path / "v.lance", dim=DIM)
    _note_rows(store)
    emb = cast(Embedder, FakeEmbedder())

    before_search = semantic_search("vectors and dreaming", emb, store, k=10)
    before_mirror = MirrorView.project(store).rows()

    _add_code(store)                                   # add the whole "code corpus"

    after_search = semantic_search("vectors and dreaming", emb, store, k=10)
    after_mirror = MirrorView.project(store).rows()

    assert after_search == before_search               # ← the isolation ratchet (F-CI5)
    assert after_mirror == before_mirror


# ── the layer-column migration: an old 8-col store rebuilds preserving note rows ─────────

def _old_schema(dim: int) -> pa.Schema:
    return pa.schema([
        ("id", pa.string()), ("digest", pa.string()), ("title", pa.string()),
        ("source_path", pa.string()), ("chunk_index", pa.int32()),
        ("provenance", pa.string()), ("text", pa.string()),
        ("vector", pa.list_(pa.float32(), dim)),
    ])


def test_layer_migration_preserves_note_rows_bit_identically(tmp_path):
    # hand-build a legacy 8-column store with two authored rows (pre-CI-1 shape)
    store = VectorStore(tmp_path / "v.lance", dim=DIM)
    legacy = store._db.create_table(TABLE, schema=_old_schema(DIM))
    legacy.add([
        {"id": "n:0", "digest": "d0", "title": "A", "source_path": "notes/a.md",
         "chunk_index": 0, "provenance": Provenance.AUTHORED_SOLO.value,
         "text": "alpha", "vector": [0.1] * DIM},
        {"id": "n:1", "digest": "d0", "title": "A", "source_path": "notes/a.md",
         "chunk_index": 1, "provenance": Provenance.AUTHORED_SOLO.value,
         "text": "beta", "vector": [0.2] * DIM},
    ])
    # a fresh handle triggers the lazy migration on the next add; force it by adding a code row
    store2 = VectorStore(tmp_path / "v.lance", dim=DIM)
    _add_code(store2)

    rows = store2.all_rows()
    assert TABLE in store2._db.list_tables().tables
    notes = {r["id"]: r for r in rows if r["provenance"] == Provenance.AUTHORED_SOLO.value}
    assert set(notes) == {"n:0", "n:1"}                # both note rows survived
    assert notes["n:0"]["text"] == "alpha" and notes["n:1"]["text"] == "beta"  # text intact
    assert notes["n:0"]["layer"] == "prose"            # defaulted to prose by the migration
    assert list(notes["n:0"]["vector"]) == pytest.approx([0.1] * DIM)  # vector NOT re-embedded
