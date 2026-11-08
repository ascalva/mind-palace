"""Vault catalog — the active/tombstone ledger for incremental ingest (vault-sync task).

The Phase-1 ingest is content-addressed: identical bytes store once (raw is sacred). That
gives dedup for free but says nothing about *which source files currently hold which content*,
which is exactly what an incremental watcher needs to answer "unchanged?", "changed?",
"deleted?". This SQLite catalog is that map — `source_path -> (digest, active)` — and the
authority for the tombstone semantics (design-notes/vault-sync-and-capture.md):

  * **unchanged** — the file's current digest equals the recorded one and it is active → no-op.
  * **changed**   — a new digest → re-embed; the previous digest's derived rows are dropped
                    iff no other active file still references them.
  * **deleted**   — `tombstone()` marks the row inactive; derived rows are dropped, **raw is
                    kept** so a re-add dedups and nothing is lost.

It carries only local bookkeeping (paths, digests) — no note content, no network. All notes
the watcher records are `authored-solo` (the owner's own writing) — the §1 spectrum split is
now realized, so `Provenance.AUTHORED_SOLO` is the concrete tag (was the single `authored`).
Dialogue capture records `authored-dialogue` and curated ingest records `curated` through the
same catalog, by passing `provenance=` to `record`.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from core.kernel.provenance import Provenance
from core.stores.authored_supersession import OwnerDeclaration, verify_owner_declaration
from core.stores.versions import RekeyRefusedError

_DDL = """
CREATE TABLE IF NOT EXISTS vault_files (
    source_path TEXT PRIMARY KEY,
    digest      TEXT NOT NULL,
    title       TEXT NOT NULL,
    provenance  TEXT NOT NULL DEFAULT 'authored-solo',
    active      INTEGER NOT NULL DEFAULT 1,
    updated_at  TEXT NOT NULL,
    doc_id      TEXT                 -- stable identity, decoupled from source_path (bp-031); a
);                                   -- new row defaults doc_id := source_path (identity == path)
CREATE INDEX IF NOT EXISTS vault_files_digest ON vault_files (digest, active);
"""


def _utcnow() -> str:
    return datetime.now(UTC).replace(tzinfo=None).isoformat(timespec="seconds")


@dataclass(frozen=True)
class CatalogEntry:
    source_path: str
    digest: str
    title: str
    active: bool
    provenance: str = Provenance.AUTHORED_SOLO.value


@dataclass
class VaultCatalog:
    path: Path

    def __post_init__(self) -> None:
        if str(self.path) != ":memory:":
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._defer = False
        self._conn = sqlite3.connect(str(self.path))
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript(_DDL)
        self._migrate()
        self._conn.commit()

    def _migrate(self) -> None:
        """Bring a pre-`doc_id` catalog forward, idempotently (bp-031 Item 1). `CREATE TABLE IF NOT
        EXISTS` is a no-op on a live store that predates the column, so the additive `doc_id` needs
        an explicit `ALTER … ADD COLUMN` + a one-time backfill `doc_id := source_path` for every
        legacy row. Behavior-preserving: identity stays equal to the path until a mechanism (Item 2)
        diverges it. A second run matches no `doc_id IS NULL` rows — same shape as
        `relabel_provenance`."""
        cols = {r["name"] for r in self._conn.execute("PRAGMA table_info(vault_files)").fetchall()}
        if "doc_id" not in cols:
            self._conn.execute("ALTER TABLE vault_files ADD COLUMN doc_id TEXT")
        # Created here (not in _DDL) so it runs AFTER the column exists — the index references
        # doc_id, which a legacy `CREATE TABLE IF NOT EXISTS` would not yet have. IF NOT EXISTS on
        # both the fresh (column via _DDL) and migrated (column via ALTER) paths.
        self._conn.execute("CREATE INDEX IF NOT EXISTS vault_files_doc_id ON vault_files (doc_id)")
        self._conn.execute("UPDATE vault_files SET doc_id = source_path WHERE doc_id IS NULL")
        self._conn.commit()

    def get(self, source_path: str) -> CatalogEntry | None:
        r = self._conn.execute(
            "SELECT * FROM vault_files WHERE source_path = ?", [source_path]
        ).fetchone()
        return _to_entry(r) if r else None

    def record(self, source_path: str, digest: str, title: str, *,
               provenance: Provenance = Provenance.AUTHORED_SOLO,
               doc_id: str | None = None) -> None:
        """Upsert a file as active at `digest` (re-adding a tombstoned file reactivates it).

        `doc_id` binds the note's stable identity (bp-031 Item 2): pass an explicit id (an existing
        `id::`, or a renamed predecessor's carried id) to bind it; omit it and a NEW row defaults
        `doc_id := source_path` (identity == path) while a re-record PRESERVES the stored `doc_id`.
        An explicit `doc_id` DOES overwrite on conflict — but sync only passes one at first bind,
        never to switch a historied note's identity (the re-key is owner-run bp-034)."""
        insert_doc_id = doc_id if doc_id is not None else source_path
        # Preserve the stored doc_id on a re-record; overwrite only when an explicit id is given.
        set_doc = ", doc_id=excluded.doc_id" if doc_id is not None else ""
        self._conn.execute(
            "INSERT INTO vault_files"
            " (source_path, digest, title, provenance, active, updated_at, doc_id)"
            " VALUES (?, ?, ?, ?, 1, ?, ?)"
            " ON CONFLICT(source_path) DO UPDATE SET"
            "   digest=excluded.digest, title=excluded.title,"
            "   provenance=excluded.provenance, active=1, updated_at=excluded.updated_at" + set_doc,
            [source_path, digest, title, str(provenance), _utcnow(), insert_doc_id],
        )
        if not self._defer:
            self._conn.commit()

    @contextmanager
    def deferred(self) -> Iterator[None]:
        """The records made inside commit once, at the end, in one transaction (a batch's keys,
        the last writes of its landing); an exception inside rolls them back, so none of them is
        written."""
        self._defer = True
        try:
            yield
            self._conn.commit()
        except BaseException:
            self._conn.rollback()
            raise
        finally:
            self._defer = False

    def paths_for(self, doc_id: str) -> list[str]:
        """The active paths bound to a document identity: one, or two while a rename is being
        synced (the old path is tombstoned after the new one lands). The landing order reads it
        to tell a rename, which is a version event, from a re-run after a crash, which is not
        (core/ingest/landing.py)."""
        rows = self._conn.execute(
            "SELECT source_path FROM vault_files WHERE doc_id = ? AND active = 1 "
            "ORDER BY source_path", [doc_id]).fetchall()
        return [str(r[0]) for r in rows]

    def doc_id_for(self, source_path: str) -> str:
        """The stable `doc_id` bound to this `source_path` — the identity the version store keys on.
        Equals `source_path` (identity == path) until a mechanism (bp-031 Item 2) diverges it. An
        unknown path resolves to itself, so a first-ingest resolve is well-defined even before the
        catalog row exists (the caller records the row, then resolves)."""
        row = self._conn.execute(
            "SELECT doc_id FROM vault_files WHERE source_path = ?", [source_path]
        ).fetchone()
        return row["doc_id"] if row is not None and row["doc_id"] is not None else source_path

    def tombstone(self, source_path: str) -> str | None:
        """Mark a file inactive (deleted from the vault). Returns the digest it held, or None
        if it was unknown. The raw blob is intentionally NOT touched — raw is sacred; true
        deletion is the separate, owner-gated purge (core/ingest/purge.py)."""
        entry = self.get(source_path)
        if entry is None:
            return None
        self._conn.execute(
            "UPDATE vault_files SET active = 0, updated_at = ? WHERE source_path = ?",
            [_utcnow(), source_path],
        )
        self._conn.commit()
        return entry.digest

    def active_refs(self, digest: str) -> int:
        """How many ACTIVE files currently hold this content. Derived rows for a digest may be
        dropped only when this is 0 (so dedup-shared content isn't pulled out from under a
        still-present file)."""
        row = self._conn.execute(
            "SELECT count(*) FROM vault_files WHERE digest = ? AND active = 1", [digest]
        ).fetchone()
        return int(row[0]) if row else 0

    def active_paths(self) -> set[str]:
        rows = self._conn.execute(
            "SELECT source_path FROM vault_files WHERE active = 1"
        ).fetchall()
        return {r["source_path"] for r in rows}

    def active_entries(self) -> list[CatalogEntry]:
        rows = self._conn.execute(
            "SELECT * FROM vault_files WHERE active = 1 ORDER BY source_path"
        ).fetchall()
        return [_to_entry(r) for r in rows]

    def relabel_provenance(self, old: str, new: str) -> int:
        """Rewrite every entry's provenance from `old` to `new`. Returns rows changed.

        The catalog-side half of the §1 spectrum-split migration (relabel legacy `'authored'`
        → `'authored-solo'`). Same-trust-tier relabel, idempotent (a second run matches no
        `old` rows)."""
        if old == new:
            return 0
        cur = self._conn.execute(
            "UPDATE vault_files SET provenance = ?, updated_at = ? WHERE provenance = ?",
            [new, _utcnow(), old],
        )
        self._conn.commit()
        return cur.rowcount

    def migrate_rekey_doc_id(self, source_path: str, new_doc_id: str, *,
                             declaration: OwnerDeclaration) -> None:
        """Owner-gated identity migration (the catalog twin of `versions.migrate_rekey_doc_id`;
        bp-034, §11 ruling 2026-07-14): rebind a note's resolved `doc_id` to `new_doc_id`, keyed by
        the UNCHANGED PK `source_path` (the in-place id:: mint never moves the path). Same owner-
        authority gate — this marks the write as a deliberate migration, not the runtime `record`
        path, even though the catalog is not append-only.

        Fail-closed. `doc_id` carries NO unique index, so this method is the ONLY guard against a
        resolution-level lineage merge: it REFUSES if any OTHER row already resolves to `new_doc_id`
        (guardrail 5). Idempotent — a row already at `new_doc_id` (a re-run) is a no-op; an unknown
        `source_path` matches 0 rows and is a silent no-op."""
        verify_owner_declaration(declaration)                        # owner authority, fail-closed
        if not source_path or not new_doc_id:                        # input sanity
            raise RekeyRefusedError(
                "catalog re-key refused: empty source_path/new_doc_id (both must be non-empty)")
        if self.doc_id_for(source_path) == new_doc_id:               # already migrated → no-op
            return
        clash = self._conn.execute(                                  # guardrail 5: no id merge
            "SELECT count(*) FROM vault_files WHERE doc_id = ? AND source_path != ?",
            [new_doc_id, source_path],
        ).fetchone()
        if clash and int(clash[0]) > 0:
            raise RekeyRefusedError(
                f"catalog re-key refused: doc_id {new_doc_id!r} is already resolved by another "
                "note — rebinding this path onto it would MERGE two identities at resolution."
            )
        self._conn.execute(
            "UPDATE vault_files SET doc_id = ?, updated_at = ? WHERE source_path = ?",
            [new_doc_id, _utcnow(), source_path],
        )
        self._conn.commit()

    def remove(self, source_path: str) -> None:
        """Delete the catalog row entirely (used by the gated purge after raw removal)."""
        self._conn.execute("DELETE FROM vault_files WHERE source_path = ?", [source_path])
        self._conn.commit()

    def paths_for_digest(self, digest: str) -> list[str]:
        rows = self._conn.execute(
            "SELECT source_path FROM vault_files WHERE digest = ? ORDER BY source_path", [digest]
        ).fetchall()
        return [r["source_path"] for r in rows]

    def remove_digest(self, digest: str) -> int:
        """Delete every catalog row for a digest (the gated purge removes only tombstoned
        content — callers must verify `active_refs(digest) == 0` first). Returns rows removed."""
        cur = self._conn.execute("DELETE FROM vault_files WHERE digest = ?", [digest])
        self._conn.commit()
        return cur.rowcount

    def close(self) -> None:
        self._conn.close()


def _to_entry(r: sqlite3.Row) -> CatalogEntry:
    return CatalogEntry(
        source_path=r["source_path"], digest=r["digest"], title=r["title"],
        active=bool(r["active"]), provenance=r["provenance"],
    )
