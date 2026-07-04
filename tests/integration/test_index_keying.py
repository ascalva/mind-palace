"""Index-keying verification — build plan Item 1a (Q1 of the sacred-boundary set, read-only).

Documents, as a FALSIFIABLE fixture, how the derived embedding index is keyed today: by
`(raw-note-content-digest, chunk-position)` — an occurrence / whole-note key — NOT by
chunk-content-hash (core/ingest/index.py:33, core/stores/vectorstore.py:27-28). The consequence
(ingest-identity-and-amendment.md §4 gap): amending ONE chunk of a note re-embeds EVERY chunk
under a new note-digest, so an unchanged chunk does NOT keep its point.

This is the Item-1a keystone: its result gates whether the stored-data chunk-key migration
(build plan Items 1b/1c) is warranted (PD5). The FALSIFIER is a live assertion — if a future
content-addressed chunk key makes an unchanged chunk's point id stable across an amendment, the
marked assertion flips and this test must be updated to assert the closed behavior.

Deterministic: the real ingest/sync/vector-store path with the offline FakeEmbedder, temp stores,
no model, no network.
"""

from __future__ import annotations

from core.ingest.chunk import chunk_text
from core.ingest.sync import VaultSync
from core.stores.catalog import VaultCatalog
from core.stores.rawstore import RawStore
from core.stores.vectorstore import VectorStore
from tests.fixtures.embedding import DIM, FakeEmbedder

# Two ~900-char blocks → two chunks. Amending block 2 leaves chunk 0 byte-identical (block 1 is
# its own chunk) and changes chunk 1 — the "amend one chunk" case §4 is about.
BLOCK1 = ("alpha " * 150).strip()
NOTE_V1 = f"{BLOCK1}\n\n{('beta ' * 180).strip()}"
NOTE_V2 = f"{BLOCK1}\n\n{('gamma ' * 180).strip()}"


def _sync(tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir(exist_ok=True)
    store = VectorStore(tmp_path / "v.lance", dim=DIM)
    sync = VaultSync(
        vault=vault, raw=RawStore(tmp_path / "raw"), store=store,
        catalog=VaultCatalog(tmp_path / "catalog.sqlite"), embedder=FakeEmbedder(),
    )
    return vault, store, sync


def _by_chunk(store) -> dict[int, dict]:
    return {r["chunk_index"]: r for r in store.all_rows()}


def test_amending_one_chunk_reembeds_every_chunk_under_a_new_key(tmp_path):
    # Precondition, self-checked: the versions share chunk 0 byte-for-byte, differ at chunk 1.
    v1, v2 = chunk_text(NOTE_V1), chunk_text(NOTE_V2)
    assert len(v1) >= 2 and v1[0].text == v2[0].text and v1[1].text != v2[1].text

    vault, store, sync = _sync(tmp_path)
    note = vault / "n.md"

    note.write_text(NOTE_V1, encoding="utf-8")
    sync.rescan()
    before = _by_chunk(store)
    digest_v1 = before[0]["digest"]
    id_chunk0_v1 = before[0]["id"]

    # Amend ONLY block 2 → chunk 0's text is unchanged, chunk 1's changes.
    note.write_text(NOTE_V2, encoding="utf-8")
    sync.rescan()
    after = _by_chunk(store)
    digest_v2 = after[0]["digest"]

    # Whole-note-content keying: the note digest changed because the note's bytes changed.
    assert digest_v2 != digest_v1
    # Destroy-and-replace, not versioned amendment: the old version's rows are gone entirely
    # (core/ingest/sync.py:99-101) — no supersession edge, no chunk-level diff.
    assert not any(r["digest"] == digest_v1 for r in store.all_rows())

    # THE GAP (ingest-identity §4): chunk 0's TEXT is unchanged ...
    assert after[0]["text"] == before[0]["text"]
    # ... yet its POINT ID changed, because the key is (note-digest, index), not chunk-hash.
    # FALSIFIER: adopting a content-addressed chunk key (Items 1b/1c) makes the unchanged chunk
    # keep its id — this assertion would flip to `==` and this test must then assert the closed
    # behavior. Today it holds, so the gap is real and the migration is warranted.
    assert after[0]["id"] != id_chunk0_v1
    assert after[0]["id"] == f"{digest_v2}:0"
