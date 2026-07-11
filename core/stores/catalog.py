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
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from core.provenance import Provenance

_DDL = """
CREATE TABLE IF NOT EXISTS vault_files (
    source_path TEXT PRIMARY KEY,
    digest      TEXT NOT NULL,
    title       TEXT NOT NULL,
    provenance  TEXT NOT NULL DEFAULT 'authored-solo',
    active      INTEGER NOT NULL DEFAULT 1,
    updated_at  TEXT NOT NULL
);
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
        self._conn = sqlite3.connect(str(self.path))
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript(_DDL)
        self._conn.commit()

    def get(self, source_path: str) -> CatalogEntry | None:
        r = self._conn.execute(
            "SELECT * FROM vault_files WHERE source_path = ?", [source_path]
        ).fetchone()
        return _to_entry(r) if r else None

    def record(self, source_path: str, digest: str, title: str, *,
               provenance: Provenance = Provenance.AUTHORED_SOLO) -> None:
        """Upsert a file as active at `digest` (re-adding a tombstoned file reactivates it)."""
        self._conn.execute(
            "INSERT INTO vault_files (source_path, digest, title, provenance, active, updated_at)"
            " VALUES (?, ?, ?, ?, 1, ?)"
            " ON CONFLICT(source_path) DO UPDATE SET"
            "   digest=excluded.digest, title=excluded.title,"
            "   provenance=excluded.provenance, active=1, updated_at=excluded.updated_at",
            [source_path, digest, title, str(provenance), _utcnow()],
        )
        self._conn.commit()

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
