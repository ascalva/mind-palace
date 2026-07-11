"""Incremental vault sync (design-notes/vault-sync-and-capture.md).

The task's verification, cold (a deterministic fake embedder, real raw/vector/catalog stores):
edit a note → embeddings update; delete → stops surfacing; unchanged re-scan → no-op; and the
dedup-safe tombstone semantics (shared content isn't pulled out from under a still-present
file; raw is always kept).
"""

from __future__ import annotations

from pathlib import Path

from core.attestation import Attestor
from core.ingest.index import semantic_search
from core.ingest.sync import SyncOutcome, VaultSync
from core.stores.catalog import CatalogEntry, VaultCatalog
from core.stores.rawstore import RawStore
from core.stores.vectorstore import VectorStore
from tests.fixtures.attestation import attestor_with_store
from tests.fixtures.embedding import DIM, FakeEmbedder


def _sync(tmp_path: Path, *, attestor: Attestor | None = None) -> VaultSync:
    vault = tmp_path / "vault"
    vault.mkdir()
    return VaultSync(
        vault=vault,
        raw=RawStore(tmp_path / "raw"),
        store=VectorStore(tmp_path / "v.lance", dim=DIM),
        catalog=VaultCatalog(tmp_path / "catalog.sqlite"),
        embedder=FakeEmbedder(),
        attestor=attestor,
    )


def _write(sync: VaultSync, name: str, content: str) -> Path:
    p = sync.vault / name
    p.write_text(content, encoding="utf-8")
    return p


def _entry(sync: VaultSync, path: str) -> CatalogEntry:
    """`catalog.get(path)`, narrowed: every call site in this file looks up a path immediately
    after `sync_path`/`rescan`/`handle_deleted` indexed or tombstoned it, so the row always
    exists (`VaultCatalog.get`'s honest `CatalogEntry | None` return covers an arbitrary/unknown
    path — a shape this test's own construction never produces)."""
    entry = sync.catalog.get(path)
    assert entry is not None, f"catalog has no entry for {path!r} — the test's own setup is broken"
    return entry


def _titles_for(sync: VaultSync, query: str) -> list[str]:
    return [r["title"] for r in semantic_search(query, sync.embedder, sync.store, k=5)]


def test_edit_updates_embeddings(tmp_path):
    sync = _sync(tmp_path)
    p = _write(sync, "note.md", "the original content about gardening")
    assert sync.sync_path(p) is SyncOutcome.INDEXED
    d1 = _entry(sync, str(p)).digest
    assert "note" in _titles_for(sync, "the original content about gardening")

    # Edit the note → re-embed; the old digest's rows are dropped.
    p.write_text("a completely different topic: astrophysics", encoding="utf-8")
    assert sync.sync_path(p) is SyncOutcome.INDEXED
    d2 = _entry(sync, str(p)).digest
    assert d2 != d1
    # New content is searchable; the old content's rows are gone.
    assert sync.store.all_rows() and all(r["digest"] != d1 for r in sync.store.all_rows())
    assert any(r["digest"] == d2 for r in sync.store.all_rows())
    # Raw is sacred — the previous version's bytes are still kept.
    assert sync.raw.exists(d1)


def test_unchanged_rescan_is_noop(tmp_path):
    sync = _sync(tmp_path)
    _write(sync, "a.md", "alpha content")
    _write(sync, "b.md", "beta content")
    first = sync.rescan()
    assert first.indexed == 2
    rows_before = sync.store.count()

    second = sync.rescan()                       # nothing changed
    assert second.indexed == 0
    assert second.unchanged == 2
    assert second.tombstoned == 0
    assert sync.store.count() == rows_before     # no new rows, no duplicates


def test_delete_stops_surfacing_but_keeps_raw(tmp_path):
    sync = _sync(tmp_path)
    p = _write(sync, "secret.md", "a memorable unique phrase xyzzy")
    sync.sync_path(p)
    digest = _entry(sync, str(p)).digest
    assert "secret" in _titles_for(sync, "a memorable unique phrase xyzzy")

    p.unlink()
    assert sync.handle_deleted(str(p)) is SyncOutcome.TOMBSTONED
    # Stops surfacing in search; catalog entry inactive; derived rows gone.
    assert "secret" not in _titles_for(sync, "a memorable unique phrase xyzzy")
    assert _entry(sync, str(p)).active is False
    assert all(r["digest"] != digest for r in sync.store.all_rows())
    # Raw kept (tombstone, not purge).
    assert sync.raw.exists(digest)


def test_rescan_handles_delete(tmp_path):
    sync = _sync(tmp_path)
    a = _write(sync, "a.md", "alpha")
    _write(sync, "b.md", "beta")
    sync.rescan()
    (sync.vault / "b.md").unlink()
    a.write_text("alpha changed", encoding="utf-8")

    report = sync.rescan()
    assert report.indexed == 1       # a changed
    assert report.tombstoned == 1    # b gone
    # Idempotent: a third pass does nothing.
    again = sync.rescan()
    assert (again.indexed, again.tombstoned) == (0, 0)
    assert again.unchanged == 1


def test_dedup_shared_content_not_dropped_until_last_ref(tmp_path):
    sync = _sync(tmp_path)
    a = _write(sync, "a.md", "identical twins content")
    b = _write(sync, "b.md", "identical twins content")
    sync.sync_path(a)
    sync.sync_path(b)
    digest = _entry(sync, str(a)).digest
    assert _entry(sync, str(b)).digest == digest      # same content, same digest
    assert sync.catalog.active_refs(digest) == 2

    # Deleting one copy must NOT drop the shared derived rows.
    a.unlink()
    sync.handle_deleted(str(a))
    assert any(r["digest"] == digest for r in sync.store.all_rows())
    assert "b" in _titles_for(sync, "identical twins content")

    # Deleting the last copy drops them.
    b.unlink()
    sync.handle_deleted(str(b))
    assert all(r["digest"] != digest for r in sync.store.all_rows())


def test_indexed_emits_a_leaf_ingest_attestation(tmp_path):
    att_store, attestor = attestor_with_store(tmp_path)
    sync = _sync(tmp_path, attestor=attestor)
    p = _write(sync, "note.md", "an attested note about beekeeping")
    assert sync.sync_path(p) is SyncOutcome.INDEXED
    digest = _entry(sync, str(p)).digest

    atts = att_store.by_role("vault_watcher")
    assert len(atts) == 1
    att = atts[0]
    assert att.action == "ingest_note"
    # Input == output == the content digest: the chain's leaf (attestation-layer.md §3).
    assert att.input_hashes == (digest,)
    assert att.output_hashes == (digest,)


def test_unchanged_rescan_does_not_emit_a_duplicate_attestation(tmp_path):
    att_store, attestor = attestor_with_store(tmp_path)
    sync = _sync(tmp_path, attestor=attestor)
    _write(sync, "a.md", "alpha content for attestation")
    first = sync.rescan()
    assert first.indexed == 1
    assert att_store.count() == 1

    second = sync.rescan()                        # nothing changed -> early-return, no emit
    assert second.unchanged == 1
    assert att_store.count() == 1                 # no spurious re-emission


def test_readd_after_tombstone_reactivates(tmp_path):
    sync = _sync(tmp_path)
    p = _write(sync, "n.md", "content that comes and goes")
    sync.sync_path(p)
    digest = _entry(sync, str(p)).digest
    p.unlink()
    sync.handle_deleted(str(p))
    assert _entry(sync, str(p)).active is False

    # Re-adding identical content dedups at raw and reactivates the catalog entry.
    _write(sync, "n.md", "content that comes and goes")
    assert sync.sync_path(p) is SyncOutcome.INDEXED
    entry = _entry(sync, str(p))
    assert entry.active is True
    assert entry.digest == digest
    assert "n" in _titles_for(sync, "content that comes and goes")
