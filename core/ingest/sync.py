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
from core.kernel.config import Config
from core.kernel.ingest.logseq import DEFAULT_EXCLUDE_DIRS, iter_vault, parse_note
from core.kernel.ingest.pipeline import ingest_note
from core.kernel.stores.rawstore import RawStore
from core.stores.catalog import VaultCatalog
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
    # (doc_id, version_seq), NOT content digest, so a revert stays linear (no cycle) — to a store
    # the balance math cannot read (never EdgeStore). The `doc_id` is resolved by the catalog
    # (`doc_id_for`), so a rename does not fork the chain (bp-031); it equals `source_path` until a
    # mechanism diverges it. None = no version log.
    version_store: VersionStore | None = None

    def sync_path(self, path: Path,
                  *, rename_by_digest: dict[str, tuple[str, str]] | None = None) -> SyncOutcome:
        """Re-ingest one note as a chunk-level amendment; unchanged content is a no-op.

        `rename_by_digest` (passed by `rescan`) maps a just-vanished path's content digest to its
        `(source_path, doc_id)`; a NEW path with an exact-content match adopts that `doc_id` so a
        rename continues the version chain instead of forking it (bp-031 Item 2)."""
        parsed = parse_note(path, self.vault)
        source_path = parsed.source_path
        record = ingest_note(parsed, self.raw,                       # raw.add: keep + dedup
                             max_chars=self.max_chars, overlap_chars=self.overlap_chars)
        digest = record.digest

        prev = self.catalog.get(source_path)
        if prev is not None and prev.active and prev.digest == digest:
            return SyncOutcome.UNCHANGED                            # content didn't change

        # Resolve the note's stable doc_id at FIRST bind only (prev is None): prefer an existing
        # `id::` (already parsed into properties, no vault mutation), else a renamed predecessor's
        # carried doc_id (exact-content match). An already-bound note keeps its identity — switching
        # a historied note's id is the owner-run re-key (bp-034), never a sync-time act. None ⇒ the
        # catalog defaults doc_id := source_path (Item 1 behavior, byte-identical).
        resolved_doc_id: str | None = None
        if prev is None:
            resolved_doc_id = parsed.properties.get("id")
            if resolved_doc_id is None and rename_by_digest is not None:
                match = rename_by_digest.get(digest)
                if match is not None:
                    resolved_doc_id = match[1]

        # Chunk-level amendment (ingest-identity-and-amendment.md §4): reuse the vectors of chunks
        # whose content is unchanged (NO re-embed), embed only changed/new chunks, and replace this
        # note's projection under its stable `source_path`. Keyed by (source_path, chunk_hash), so a
        # note's unchanged parts keep their point ids across edits — the §4 gap this closes.
        existing = self.store.rows_for_source(source_path)
        index_amendment(record, existing, self.embedder, self.store)
        self.catalog.record(source_path, digest, record.title, doc_id=resolved_doc_id)
        if self.attestor is not None:
            # input == output == the content digest: for AUTHORED content the bytes read and the
            # content-addressed object written share one address. This is the chain's leaf.
            self.attestor.emit(agent_role="vault_watcher", action="ingest_note",
                               input_hashes=[digest], output_hashes=[digest])

        # Append the note's next VERSION so an amendment ENHANCES provenance — a queryable version
        # chain, not a silent overwrite (§4A). Keyed on version identity (the store allocates the
        # next version_seq for this note's stable `doc_id`), NOT content digest, so a revert is a
        # new version, never a cycle; and it lives OUTSIDE the balance-fed edge store (Constr. 2).
        # Every INDEXED outcome is a new version (v1 on first ingest, v2… on each amendment). The
        # `doc_id` is resolved by the catalog (== source_path until a mechanism diverges it), so a
        # rename carries the chain forward instead of forking it. Resolved AFTER `catalog.record`
        # above, so the row (and its doc_id) exists.
        if self.version_store is not None:
            self.version_store.record(self.catalog.doc_id_for(source_path), digest)
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
        present: dict[str, Path] = {
            str(path): path
            for path in iter_vault(self.vault, pattern=self.pattern, exclude_dirs=self.exclude_dirs)
        }
        gone = self.catalog.active_paths() - set(present)

        # Exact-content rename carry-forward (bp-031 Item 2): index each vanished path's held
        # (digest -> its doc_id); a new path whose content digest matches adopts that doc_id, so the
        # version chain continues under one identity rather than forking into an orphan seq-1 chain.
        # A digest shared by >1 vanished path is AMBIGUOUS (dedup, no single predecessor), dropped
        # — fall back to a fresh identity, no worse than today. id:: resolution wins over content
        # match (decided in sync_path). Built PRE-sync, so `gone` paths are still recorded.
        rename_by_digest: dict[str, tuple[str, str]] = {}
        ambiguous: set[str] = set()
        for g in gone:
            entry = self.catalog.get(g)
            if entry is None or not entry.active:
                continue
            if entry.digest in rename_by_digest:
                ambiguous.add(entry.digest)
            else:
                rename_by_digest[entry.digest] = (g, self.catalog.doc_id_for(g))
        for digest in ambiguous:
            rename_by_digest.pop(digest, None)

        for path in present.values():
            report.tally(self.sync_path(path, rename_by_digest=rename_by_digest))
        for g in gone:
            report.tally(self.handle_deleted(g))
        return report


def build_vault_sync(config: Config | None = None) -> VaultSync:
    """Wire a VaultSync against the configured vault + real stores + embedder."""
    from core.attestation import build_attestor
    from core.ingest.embed import build_embedder
    from core.kernel.config import get_config
    from core.stores.versions import open_version_store

    cfg = config or get_config()
    return VaultSync(
        vault=cfg.ingestion.vault.path,
        raw=RawStore(cfg.paths.raw_store),
        store=VectorStore(cfg.paths.vector_store, dim=cfg.embedding.dim),
        catalog=VaultCatalog(cfg.paths.vault_catalog),
        embedder=build_embedder(cfg),
        pattern=cfg.ingestion.vault.pattern,
        attestor=build_attestor(cfg),
        version_store=open_version_store(cfg),   # each (re)ingest appends a note version (§4A)
    )
