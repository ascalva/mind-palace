"""Owner-gated purge-raw (vault-sync task): true deletion, fail-closed.

A vault delete only tombstones (raw kept). Purge removes the raw bytes too, and it must
refuse unless explicitly confirmed AND the content is held by no active note.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from core.ingest.purge import PurgeRefusedError, purge_raw
from core.ingest.sync import VaultSync
from core.stores.catalog import VaultCatalog
from core.stores.rawstore import RawStore
from core.stores.vectorstore import VectorStore
from tests.fixtures.embedding import DIM, FakeEmbedder


def _sync(tmp_path: Path) -> VaultSync:
    vault = tmp_path / "vault"
    vault.mkdir()
    return VaultSync(
        vault=vault,
        raw=RawStore(tmp_path / "raw"),
        store=VectorStore(tmp_path / "v.lance", dim=DIM),
        catalog=VaultCatalog(tmp_path / "catalog.sqlite"),
        embedder=FakeEmbedder(),
    )


def _index(sync: VaultSync, name: str, content: str) -> str:
    p = sync.vault / name
    p.write_text(content, encoding="utf-8")
    sync.sync_path(p)
    entry = sync.catalog.get(str(p))
    assert entry is not None   # just synced this exact path
    return entry.digest


def test_purge_refused_without_confirm(tmp_path):
    sync = _sync(tmp_path)
    digest = _index(sync, "n.md", "stuff")
    (sync.vault / "n.md").unlink()
    sync.handle_deleted(str(sync.vault / "n.md"))   # tombstoned, purgeable

    with pytest.raises(PurgeRefusedError):
        purge_raw(digest, raw=sync.raw, store=sync.store, catalog=sync.catalog, confirm=False)
    assert sync.raw.exists(digest)                  # nothing destroyed


def test_purge_refused_while_active(tmp_path):
    sync = _sync(tmp_path)
    digest = _index(sync, "n.md", "still here")     # active, not deleted

    with pytest.raises(PurgeRefusedError):
        purge_raw(digest, raw=sync.raw, store=sync.store, catalog=sync.catalog, confirm=True)
    assert sync.raw.exists(digest)                  # active content is protected


def test_purge_removes_raw_when_confirmed_and_tombstoned(tmp_path):
    sync = _sync(tmp_path)
    digest = _index(sync, "n.md", "to be forgotten")
    (sync.vault / "n.md").unlink()
    sync.handle_deleted(str(sync.vault / "n.md"))

    result = purge_raw(digest, raw=sync.raw, store=sync.store, catalog=sync.catalog, confirm=True)
    assert result.raw_removed is True
    assert not sync.raw.exists(digest)              # raw truly gone
    assert sync.catalog.get(str(sync.vault / "n.md")) is None  # catalog row removed
    assert all(r["digest"] != digest for r in sync.store.all_rows())
