"""Incremental vault sync — re-ingest changed notes (design-notes/vault-sync-and-capture.md).

Core-side, LOCAL filesystem only: it reads vault files and writes the local stores. No
network, no `edge`, no sockets — the seal holds and the import-lint proves it. This is the
deterministic engine; the watcher (`core/ingest/watch.py`) only *triggers* it, and the
scheduler runs it as a background job so all store mutation stays on the single writer.

Idempotency rides on the existing content-addressing plus the vault catalog:

  * **unchanged** (same digest, still active) → no-op: no re-embed, no new rows.
  * **changed / new** → (re)embed the note's chunks; the previous digest's derived rows are
    dropped iff no other active file still references that content.
  * **deleted** → tombstone: derived rows dropped, the catalog row marked inactive, and the
    **raw blob kept** (raw is sacred) so a later re-add dedups. True deletion is the separate,
    owner-gated purge (`core/ingest/purge.py`), never done here.

Everything ingested is `authored-solo` — the existing AUTHORED provenance tag (the spectrum
split is deferred, see PROGRESS.md). The mirror firewall is unaffected: these are the owner's
own notes, the mirror's ground truth.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from core.attestation import Attestor
from core.ingest.embed import Embedder
from core.ingest.index import index_amendment
from core.ingest.logseq import DEFAULT_EXCLUDE_DIRS, iter_vault, parse_note
from core.ingest.pipeline import ingest_note
from core.stores.catalog import VaultCatalog
from core.stores.rawstore import RawStore
from core.stores.vectorstore import VectorStore
from core.stores.versions import VersionStore


class SyncOutcome(Enum):
    UNCHANGED = "unchanged"   # same digest, already indexed → no work
    INDEXED = "indexed"       # new or changed content → (re)embedded
    TOMBSTONED = "tombstoned"  # file gone → derived dropped, raw kept


@dataclass
class SyncReport:
    indexed: int = 0
    unchanged: int = 0
    tombstoned: int = 0

    def tally(self, outcome: SyncOutcome) -> None:
        setattr(self, outcome.value, getattr(self, outcome.value) + 1)

    def __str__(self) -> str:
        return (f"indexed={self.indexed} unchanged={self.unchanged} "
                f"tombstoned={self.tombstoned}")


@dataclass
class VaultSync:
    vault: Path
    raw: RawStore
    store: VectorStore
    catalog: VaultCatalog
    embedder: Embedder
    pattern: str = "**/*.md"
    exclude_dirs: frozenset[str] = DEFAULT_EXCLUDE_DIRS
    max_chars: int = 1200
    overlap_chars: int = 150
    # Optional runtime proof layer: when present, each (re)indexed note emits a signed-provenance
    # ingest attestation ("the authorized watcher ingested digest D under Constitution F",
    # attestation-layer.md §3) — the authored leaf every dream chain bottoms out in. None = off.
    attestor: Attestor | None = None
    # Optional version-history provenance (ingest-identity-and-amendment.md §4A; build plan Item 6):
    # when present, each indexed (re)ingest appends the note's next VERSION — keyed on
    # (source_path, version_seq), NOT content digest, so a revert stays linear (no cycle) —
    # to a dedicated store the balance math cannot read (never EdgeStore). None = no version log.
    version_store: VersionStore | None = None

    def sync_path(self, path: Path) -> SyncOutcome:
        """Re-ingest one note as a chunk-level amendment; unchanged content is a no-op."""
        parsed = parse_note(path, self.vault)
        source_path = parsed.source_path
        record = ingest_note(parsed, self.raw,                       # raw.add: keep + dedup
                             max_chars=self.max_chars, overlap_chars=self.overlap_chars)
        digest = record.digest

        prev = self.catalog.get(source_path)
        if prev is not None and prev.active and prev.digest == digest:
            return SyncOutcome.UNCHANGED                            # content didn't change

        # Chunk-level amendment (ingest-identity-and-amendment.md §4): reuse the vectors of chunks
        # whose content is unchanged (NO re-embed), embed only changed/new chunks, and replace this
        # note's projection under its stable `source_path`. Keyed by (source_path, chunk_hash), so a
        # note's unchanged parts keep their point ids across edits — the §4 gap this closes.
        existing = self.store.rows_for_source(source_path)
        index_amendment(record, existing, self.embedder, self.store)
        self.catalog.record(source_path, digest, record.title)
        if self.attestor is not None:
            # input == output == the content digest: for AUTHORED content the bytes read and the
            # content-addressed object written share one address. This is the chain's leaf.
            self.attestor.emit(agent_role="vault_watcher", action="ingest_note",
                               input_hashes=[digest], output_hashes=[digest])

        # Append the note's next VERSION so an amendment ENHANCES provenance — a queryable version
        # chain, not a silent overwrite (§4A). Keyed on version identity (the store allocates the
        # next version_seq for this source_path), NOT content digest, so a revert is a new version,
        # never a cycle; and it lives OUTSIDE the balance-fed edge store (Constraint 2). Every
        # INDEXED outcome is a new version (v1 on first ingest, v2… on each amendment).
        if self.version_store is not None:
            self.version_store.record(source_path, digest)
        return SyncOutcome.INDEXED

    def handle_deleted(self, source_path: str) -> SyncOutcome:
        """A vault file disappeared: tombstone it and drop its projection (by `source_path`).
        Source-scoped, so an identical-content file elsewhere keeps its own rows. Raw is kept
        (sacred); true deletion is the separate, owner-gated purge (core/ingest/purge.py)."""
        self.catalog.tombstone(source_path)
        self.store.delete_source(source_path)
        return SyncOutcome.TOMBSTONED

    def rescan(self) -> SyncReport:
        """Full catalog-vs-vault reconciliation. The watcher triggers this; it is the
        idempotent backbone (an unchanged re-scan does no work) and also the catch-up path
        for changes that happened while no watcher was running."""
        report = SyncReport()
        seen: set[str] = set()
        for path in iter_vault(self.vault, pattern=self.pattern, exclude_dirs=self.exclude_dirs):
            seen.add(str(path))
            report.tally(self.sync_path(path))
        for gone in self.catalog.active_paths() - seen:
            report.tally(self.handle_deleted(gone))
        return report


def build_vault_sync(config: object | None = None) -> VaultSync:
    """Wire a VaultSync against the configured vault + real stores + embedder."""
    from config.loader import get_config
    from core.attestation import build_attestor
    from core.ingest.embed import build_embedder
    from core.stores.versions import open_version_store

    cfg = config or get_config()
    return VaultSync(
        vault=cfg.vault.path,
        raw=RawStore(cfg.paths.raw_store),
        store=VectorStore(cfg.paths.vector_store, dim=cfg.embedding.dim),
        catalog=VaultCatalog(cfg.paths.vault_catalog),
        embedder=build_embedder(cfg),
        pattern=cfg.vault.pattern,
        attestor=build_attestor(cfg),
        version_store=open_version_store(cfg),   # each (re)ingest appends a note version (§4A)
    )
