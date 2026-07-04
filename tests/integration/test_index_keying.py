"""Index-keying — build plan Item 1c CLOSED behavior (was the Q1 §4 gap the Item-1a harness proved).

After 1c the derived index is keyed by a doc-scoped content address `(source_path, chunk_hash)`, so
amending ONE block of a note re-embeds ONLY that block: the unchanged chunk keeps its point id and
its vector is reused, not recomputed (version-history provenance: test_version_history.py).
This is the Item-1a falsifier, now flipped to assert the closed state. Real ingest/sync/vector-store
path + a counting embedder (to prove no re-embed); deterministic, no model, no network.
"""

from __future__ import annotations

from core.ingest.amend import chunk_point_id
from core.ingest.chunk import chunk_text
from core.ingest.sync import VaultSync
from core.stores.catalog import VaultCatalog
from core.stores.rawstore import RawStore
from core.stores.vectorstore import VectorStore
from tests.fixtures.embedding import DIM, FakeEmbedder

BLOCK1 = ("alpha " * 150).strip()
NOTE_V1 = f"{BLOCK1}\n\n{('beta ' * 180).strip()}"
NOTE_V2 = f"{BLOCK1}\n\n{('gamma ' * 180).strip()}"


class _CountingEmbedder(FakeEmbedder):
    """A deterministic FakeEmbedder that records how many chunk texts it embedded — so a test can
    prove an unchanged chunk was NOT re-embedded (the vector alone can't show it: same text ⇒ same
    vector whether reused or recomputed)."""

    def __init__(self) -> None:
        self.embedded: list[str] = []

    def embed_documents(self, texts):
        self.embedded.extend(texts)
        return super().embed_documents(texts)


def _sync(tmp_path, embedder):
    vault = tmp_path / "vault"
    vault.mkdir(exist_ok=True)
    store = VectorStore(tmp_path / "v.lance", dim=DIM)
    sync = VaultSync(vault=vault, raw=RawStore(tmp_path / "raw"), store=store,
                     catalog=VaultCatalog(tmp_path / "catalog.sqlite"), embedder=embedder)
    return vault, store, sync


def _by_chunk(store):
    return {r["chunk_index"]: r for r in store.all_rows()}


def test_amending_one_chunk_reembeds_only_that_chunk(tmp_path):
    v1, v2 = chunk_text(NOTE_V1), chunk_text(NOTE_V2)
    assert len(v1) >= 2 and v1[0].text == v2[0].text and v1[1].text != v2[1].text

    embedder = _CountingEmbedder()
    vault, store, sync = _sync(tmp_path, embedder)
    note = vault / "n.md"

    note.write_text(NOTE_V1, encoding="utf-8")
    sync.rescan()
    before = _by_chunk(store)
    id0 = before[0]["id"]
    embedder.embedded.clear()                       # ignore the initial full embed

    note.write_text(NOTE_V2, encoding="utf-8")
    sync.rescan()
    after = _by_chunk(store)

    # CLOSED: only the CHANGED chunk (block 2) was embedded on the amendment; chunk 0 was reused.
    assert len(embedder.embedded) == 1
    # Chunk 0's text is unchanged AND its point id is now STABLE across the amendment (was the gap).
    assert after[0]["text"] == before[0]["text"]
    assert after[0]["id"] == id0
    # The changed chunk (1) has a different id, because its content hash changed.
    assert after[1]["id"] != before[1]["id"]
    # The id IS the doc-scoped content address (source_path, chunk_hash), not the old digest:index.
    assert after[0]["id"] == chunk_point_id(after[0]["source_path"], v1[0])
