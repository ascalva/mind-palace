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

import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from core.attestation import Attestor
from core.ingest.embed import Embedder
from core.ingest.index import index_amendment
from core.ingest.landing import attest_once, record_version_if_new
from core.kernel.clearance import MIRROR_READ
from core.kernel.config import Config
from core.kernel.ingest.logseq import DEFAULT_EXCLUDE_DIRS, iter_vault, parse_note
from core.kernel.ingest.pipeline import ingest_note
from core.kernel.stores.rawstore import RawStore
from core.stores.catalog import VaultCatalog
from core.stores.vectorstore import VectorStore, open_vector_store
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


def in_vault_scope(vault: Path, path: Path, *, pattern: str = "**/*.md",
                   exclude_dirs: frozenset[str] = DEFAULT_EXCLUDE_DIRS) -> bool:
    """`iter_vault`'s predicate for one path: a regular file under `vault` (resolved, so a
    symlink out of the vault is out of scope) that matches `pattern`, lies in no excluded
    directory, and is spelled as the disk spells it. On a case-insensitive disk `PAGES/A.md`
    opens `pages/a.md`, but the rescan names it `pages/a.md`: a path in another case is out of
    scope, and an excluded directory is excluded in any case."""
    root = Path(vault).expanduser().resolve()
    try:
        rel = Path(path).expanduser().resolve().relative_to(root)
    except ValueError:
        return False
    if not rel.parts or not Path(path).is_file():
        return False
    excluded = {d.casefold() for d in exclude_dirs}
    if any(part.casefold() in excluded for part in rel.parts):
        return False
    here = root
    for part in rel.parts:                    # every component as the directory lists it
        try:
            if part not in os.listdir(here):
                return False
        except OSError:
            return False
        here = here / part
    return rel.full_match(pattern)


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

    def in_scope(self, path: Path) -> bool:
        """Whether one path is a note the rescan would see: a regular file under the vault that
        matches the note pattern and lies in no excluded directory. The door's `ingest note`
        asks before landing a single note (dn-ingest-door §9), so the scope that binds the
        rescan binds the sentence."""
        return in_vault_scope(self.vault, path, pattern=self.pattern,
                              exclude_dirs=self.exclude_dirs)

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

        # UNCHANGED reads the key and the plane: the invariant is that an active key implies
        # current rows (for bytes that have chunks). A delete that died after its retire and
        # before its tombstone leaves the key active over retired rows, and if the same bytes
        # come back before the next rescan, a check of the key alone would read them UNCHANGED
        # for ever (the formal audit of the tombstone-last delete).
        prev = self.catalog.get(source_path)
        if (prev is not None and prev.active and prev.digest == digest
                and (not record.chunks
                     or self.store.holds_current(source_path, digest, clearance=MIRROR_READ))):
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

        # The landing order (dn-ingest-door D1, DOR-7; core/ingest/landing.py): land, then the
        # version row, then the attestation, and LAST the catalog's digest, the idempotence key the
        # UNCHANGED check above reads. A crash anywhere before the key leaves a run the next run
        # repeats in full and lands exactly the same (the version is appended only when new, the
        # attestation emitted once per digest); the old order wrote the key first, so a crash
        # between it and the version row was never repaired (the audit's defect 1).
        #
        # Chunk-level amendment (ingest-identity-and-amendment.md §4): embed only chunks the plane
        # does not hold, land the new version, supersede the old one with an edge (A3: the old
        # version's occupancies stay, history kept). Unchanged chunks keep their atoms — no re-embed
        # and no read of the old rows needed, so the writer never reads what it does not own.
        index_amendment(record, [], self.embedder, self.store)

        # Append the note's next VERSION so an amendment ENHANCES provenance — a queryable version
        # chain, not a silent overwrite (§4A). Keyed on version identity (the store allocates the
        # next version_seq for this note's stable `doc_id`), NOT content digest, so a revert is a
        # new version, never a cycle; and it lives OUTSIDE the balance-fed edge store (Constr. 2).
        # The `doc_id` is the one the catalog holds for an already-bound note, else the identity
        # resolved above, else the path (what the catalog will default to when the key lands), so a
        # rename carries the chain forward instead of forking it.
        appended = False
        if self.version_store is not None:
            doc_id = (self.catalog.doc_id_for(source_path) if prev is not None
                      else resolved_doc_id if resolved_doc_id is not None else source_path)
            # A rename, a new path whose identity another active row still binds (the old path,
            # tombstoned after this pass), is a version event (bp-031) and appends even at the
            # same digest; anything else appends only when the digest is new, so a re-run after a
            # crash appends nothing. The one window this cannot tell apart is a crash inside a
            # rename's landing, which a path on the version row would close (dn-ingest-door §9).
            rename = prev is None and any(
                other != source_path for other in self.catalog.paths_for(doc_id))
            if rename:
                self.version_store.record(doc_id, digest)
                appended = True
            else:
                appended = record_version_if_new(self.version_store, doc_id, digest) is not None
        # input == output == the content digest: for AUTHORED content the bytes read and the
        # content-addressed object written share one address. This is the chain's leaf. A landing
        # that appended a version is an event of its own (a revert to bytes attested before);
        # one that did not attests only when nothing names its digest (a re-run after a crash)
        attest_once(self.attestor, agent_role="vault_watcher", action="ingest_note", digest=digest,
                    event=appended)
        self.catalog.record(source_path, digest, record.title, doc_id=resolved_doc_id)   # the key
        return SyncOutcome.INDEXED

    def sync_one(self, path: Path) -> SyncOutcome:
        """One note, as the rescan would land it: a path new to the catalog whose bytes are a
        vanished note's (one still active whose file is gone) adopts that note's identity, so a
        note renamed just before it is ingested alone keeps its version chain (the door's
        `ingest note`)."""
        source_path = str(path)
        rename_by_digest: dict[str, tuple[str, str]] = {}
        if self.catalog.get(source_path) is None:
            ambiguous: set[str] = set()
            for g in self.catalog.active_paths():
                if g == source_path or not Path(g).is_relative_to(self.vault) or Path(g).exists():
                    continue
                entry = self.catalog.get(g)
                if entry is None or not entry.active:
                    continue
                if entry.digest in rename_by_digest:
                    ambiguous.add(entry.digest)
                else:
                    rename_by_digest[entry.digest] = (g, self.catalog.doc_id_for(g))
            for digest in ambiguous:
                rename_by_digest.pop(digest, None)
        return self.sync_path(path, rename_by_digest=rename_by_digest)

    def handle_deleted(self, source_path: str) -> SyncOutcome:
        """A vault file disappeared: drop its projection (by `source_path`), then tombstone it.
        Source-scoped, so an identical-content file elsewhere keeps its own rows. Raw is kept
        (sacred); true deletion is the separate, owner-gated purge (core/ingest/purge.py).

        [banner: correction] The tombstone is the delete's key: the rescan retires only paths the
        catalog holds active whose file is gone. It was written first, so a crash before the
        retire left the deleted note current in the plane and no rescan ever came back to it. It
        is written last now (DOR-7's order, key last): a crash between the two leaves the path
        active, the next rescan repeats the delete, and the retire is idempotent."""
        self.store.delete_source(source_path)
        self.catalog.tombstone(source_path)                                   # the key, last
        return SyncOutcome.TOMBSTONED

    def owns(self, source_path: str) -> bool:
        """Whether a catalog row is the vault's: its path lies under the vault, as the rescan
        names its notes. The dialogue's turns (`dialogue/…`), the curated docs and anything else
        the shared catalog holds are not, and a rescan never tombstones them."""
        try:
            Path(source_path).relative_to(self.vault)
        except ValueError:
            return False
        return True

    def rescan(self) -> SyncReport:
        """Full catalog-vs-vault reconciliation. The watcher triggers this; it is the
        idempotent backbone (an unchanged re-scan does no work) and also the catch-up path
        for changes that happened while no watcher was running."""
        report = SyncReport()
        present: dict[str, Path] = {
            str(path): path
            for path in iter_vault(self.vault, pattern=self.pattern, exclude_dirs=self.exclude_dirs)
        }
        # the catalog is shared (the dialogue's turns, the curated docs, the door's captures):
        # a rescan reconciles only the vault's own rows, the paths under the vault
        gone = {g for g in self.catalog.active_paths() if self.owns(g)} - set(present)

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
        store=open_vector_store(cfg),
        catalog=VaultCatalog(cfg.paths.vault_catalog),
        embedder=build_embedder(cfg),
        pattern=cfg.ingestion.vault.pattern,
        attestor=build_attestor(cfg),
        version_store=open_version_store(cfg),   # each (re)ingest appends a note version (§4A)
    )
