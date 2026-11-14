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

The catalog keeps its own past (dn-temporal-snapshot §3.2, stage SN-1): the landing log of
`core/stores/landings.py`, two tables in this file that the six writing methods below append to
in the transaction of the row each writes, so a `deferred()` batch carries its log rows and the
catalog is the fold of the log. The migration that fills `doc_id` also creates the log and, on a
catalog that has rows and no log yet, writes its genesis: every process's first open of such a
catalog runs it, a reader's included. The log's keyed hash of a path needs the instance's
landing-log secret, which is read from the environment and never stored here: without it the
genesis, every write that appends a row (`record` and `tombstone` when they change the map, the
re-key) and `remove` refuse, loudly, and nothing is written unkeyed; `relabel_provenance` and
`remove_digest` append no row and need none. The reads of the log (`chains`, `head`, `read_at`,
`state_at`, `history_at`, `heads_at`, `read_between`, `verify`) have no reader yet; the two by
path, `state_at` and `history_at`, need the secret.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable, Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from core.kernel.provenance import Provenance
from core.stores.authored_supersession import OwnerDeclaration, verify_owner_declaration
from core.stores.cuts import Evaluation
from core.stores.landings import (
    ChainCheck,
    Landing,
    LandingLog,
    Prior,
    landing_log_key,
    parse_key,
)
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


_BUSY_MS = 5000             # sqlite3.connect's own timeout, five seconds
_GENESIS_WAIT_MS = 120_000  # how long an open before the genesis waits for another's lock


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
    # The landing log's secret, 32 bytes or more. None, the usual case: read from the environment
    # when the log first needs it (`core.stores.landings.landing_log_key`), and never stored.
    key: bytes | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        if str(self.path) != ":memory:":
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._defer = False
        self._conn = sqlite3.connect(str(self.path))
        self._conn.row_factory = sqlite3.Row
        # Each write in a batch is a savepoint (`_writing`), and SQLite keeps a savepoint's
        # journal in a temporary file unless told otherwise: 46 to 50 µs a write, against 6 in
        # memory, on a catalog of 100,000 rows. No query of the catalog's sorts or groups more
        # than a few rows in the temporary store, so nothing else of size is held there.
        self._conn.execute("PRAGMA temp_store = MEMORY")
        self._log = LandingLog(self._conn, self._landing_key)
        try:
            # Until the log's genesis is written another process may be writing it, six seconds
            # on a catalog of 400,274 rows: the migration then waits for its lock longer than the
            # connection's five seconds. Once the log has chains an open waits as it always did.
            if not self._logged():
                self._conn.execute(f"PRAGMA busy_timeout = {_GENESIS_WAIT_MS}")
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.executescript(_DDL)
            self._migrate()
            self._conn.commit()
            self._conn.execute(f"PRAGMA busy_timeout = {_BUSY_MS}")
        except BaseException:
            self._conn.close()
            raise

    def _logged(self) -> bool:
        """Whether the file holds the landing log with a chain: read only, no lock taken."""
        if self._conn.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' "
                              "AND name = 'landing_chains'").fetchone() is None:
            return False
        return self._log.has_chains()

    def _landing_key(self) -> bytes:
        return parse_key(self.key.hex()) if self.key is not None else landing_log_key()

    def _migrate(self) -> None:
        """Bring a pre-`doc_id` catalog forward, idempotently (bp-031 Item 1). `CREATE TABLE IF NOT
        EXISTS` is a no-op on a live store that predates the column, so the additive `doc_id` needs
        an explicit `ALTER … ADD COLUMN` + a one-time backfill `doc_id := source_path` for every
        legacy row. Behavior-preserving: identity stays equal to the path until a mechanism (Item 2)
        diverges it. A second run matches no `doc_id IS NULL` rows — same shape as
        `relabel_provenance`.

        Then the landing log (dn-temporal-snapshot §3.2): its two tables and their indexes, and,
        on the first open of a catalog that has rows and no log, the genesis, in one transaction.
        The genesis keys every row it writes, so it needs the landing-log secret: absent, it raises
        `LandingLogKeyMissing` and writes no row of the log."""
        cols = {r["name"] for r in self._conn.execute("PRAGMA table_info(vault_files)").fetchall()}
        if "doc_id" not in cols:
            self._conn.execute("ALTER TABLE vault_files ADD COLUMN doc_id TEXT")
        # Created here (not in _DDL) so it runs AFTER the column exists — the index references
        # doc_id, which a legacy `CREATE TABLE IF NOT EXISTS` would not yet have. IF NOT EXISTS on
        # both the fresh (column via _DDL) and migrated (column via ALTER) paths.
        self._conn.execute("CREATE INDEX IF NOT EXISTS vault_files_doc_id ON vault_files (doc_id)")
        self._conn.execute("UPDATE vault_files SET doc_id = source_path WHERE doc_id IS NULL")
        self._conn.commit()
        self._log.create()
        if self._log.has_chains() or self._empty():
            return                      # a log already, or nothing to begin from yet
        with self._writing():           # asked again under the write lock: one genesis only
            if not self._log.has_chains() and not self._empty():
                self._log.genesis()

    def _empty(self) -> bool:
        return self._conn.execute("SELECT 1 FROM vault_files LIMIT 1").fetchone() is None

    @contextmanager
    def _writing(self) -> Iterator[None]:
        """The transaction of one write: the catalog's row and its log rows commit together, or
        neither does. Inside `deferred()` the batch's transaction is the one, and it commits at
        the end of the batch; each write in it is a savepoint, so a write that fails leaves
        neither of its rows, even when the batch's caller catches the error and goes on."""
        if not self._conn.in_transaction:
            self._conn.execute("BEGIN IMMEDIATE")
        if self._defer:
            self._conn.execute("SAVEPOINT catalog_write")
            try:
                yield
            except BaseException:
                if self._conn.in_transaction:   # an error SQLite rolled back whole has no savepoint
                    self._conn.execute("ROLLBACK TO catalog_write")
                    self._conn.execute("RELEASE catalog_write")
                raise
            self._conn.execute("RELEASE catalog_write")
            return
        try:
            yield
        except BaseException:
            self._conn.rollback()
            raise
        self._conn.commit()

    def _prior(self, source_path: str) -> Prior | None:
        r = self._conn.execute(
            "SELECT digest, title, provenance, active, doc_id FROM vault_files "
            "WHERE source_path = ?", [source_path]).fetchone()
        if r is None:
            return None
        return Prior(digest=r["digest"], title=r["title"], provenance=r["provenance"],
                     active=bool(r["active"]),
                     doc_id=r["doc_id"] if r["doc_id"] is not None else source_path)

    def get(self, source_path: str) -> CatalogEntry | None:
        r = self._conn.execute(
            "SELECT * FROM vault_files WHERE source_path = ?", [source_path]
        ).fetchone()
        return _to_entry(r) if r else None

    def record(self, source_path: str, digest: str, title: str, *,
               provenance: Provenance = Provenance.AUTHORED_SOLO,
               doc_id: str | None = None, version: int | None = None) -> None:
        """Upsert a file as active at `digest` (re-adding a tombstoned file reactivates it).

        `doc_id` binds the note's stable identity (bp-031 Item 2): pass an explicit id (an existing
        `id::`, or a renamed predecessor's carried id) to bind it; omit it and a NEW row defaults
        `doc_id := source_path` (identity == path) while a re-record PRESERVES the stored `doc_id`.
        An explicit `doc_id` DOES overwrite on conflict — but sync only passes one at first bind,
        never to switch a historied note's identity (the re-key is owner-run bp-034).

        The landing log takes a `store` in the same transaction, carrying `version`, the number of
        the version this landing is where the place keeps a version chain (`None` elsewhere). A
        record that changes nothing, the same digest, title, class and identity as the path's
        active row, appends nothing: the log is of the changes of the map."""
        insert_doc_id = doc_id if doc_id is not None else source_path
        # Preserve the stored doc_id on a re-record; overwrite only when an explicit id is given.
        set_doc = ", doc_id=excluded.doc_id" if doc_id is not None else ""
        with self._writing():
            prior = self._prior(source_path)
            doc = doc_id if doc_id is not None else (prior.doc_id if prior else source_path)
            self._conn.execute(
                "INSERT INTO vault_files"
                " (source_path, digest, title, provenance, active, updated_at, doc_id)"
                " VALUES (?, ?, ?, ?, 1, ?, ?)"
                " ON CONFLICT(source_path) DO UPDATE SET"
                "   digest=excluded.digest, title=excluded.title,"
                "   provenance=excluded.provenance, active=1, updated_at=excluded.updated_at"
                + set_doc,
                [source_path, digest, title, str(provenance), _utcnow(), insert_doc_id],
            )
            if prior is None or not (prior.active and prior.digest == digest
                                     and prior.title == title
                                     and prior.provenance == str(provenance)
                                     and prior.doc_id == doc):
                self._log.store(source_path, str(provenance), doc, version, digest, title, prior)

    @contextmanager
    def deferred(self) -> Iterator[None]:
        """The records made inside commit once, at the end, in one transaction (a batch's keys,
        the last writes of its landing, and their rows of the landing log); an exception inside
        rolls them back, so none of them is written. A write inside that fails is undone, its
        catalog row with its log rows, before its error reaches the caller, so a caller that
        catches it and goes on commits neither."""
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
        deletion is the separate, owner-gated purge (core/ingest/purge.py).

        The landing log takes the tombstone of an active path in the same transaction: a `move`
        when another active path holds its identity (the second half of a rename), a `retire`
        otherwise. A tombstone of a path already inactive changes nothing and appends nothing."""
        with self._writing():
            prior = self._prior(source_path)
            if prior is None:
                return None
            self._conn.execute(
                "UPDATE vault_files SET active = 0, updated_at = ? WHERE source_path = ?",
                [_utcnow(), source_path],
            )
            if prior.active:
                moved = self._conn.execute(
                    "SELECT 1 FROM vault_files WHERE doc_id = ? AND active = 1 "
                    "AND source_path <> ? LIMIT 1", [prior.doc_id, source_path]).fetchone()
                self._log.tombstone(source_path, prior, "move" if moved else "retire")
            return prior.digest

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
        `old` rows). In the landing log it rewrites the label of the class's chains and no row,
        so no position moves and every chain still verifies; after a relabel into a class that
        has rows, the class has two chains."""
        if old == new:
            return 0
        with self._writing():
            cur = self._conn.execute(
                "UPDATE vault_files SET provenance = ?, updated_at = ? WHERE provenance = ?",
                [new, _utcnow(), old],
            )
            self._log.relabel(old, new)
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
        with self._writing():
            prior = self._prior(source_path)
            self._conn.execute(
                "UPDATE vault_files SET doc_id = ?, updated_at = ? WHERE source_path = ?",
                [new_doc_id, _utcnow(), source_path],
            )
            if prior is not None:           # the log: a `move` of the old identity, then the new
                self._log.rekey(source_path, prior, new_doc_id)

    def remove(self, source_path: str) -> None:
        """Delete the catalog row entirely (used by the gated purge after raw removal). Every row
        of the path in the landing log is emptied in the same transaction: the path, the
        identity, the digest, the title, the salt and the bookmark go; the position, the key,
        the commitment and the hash stay (dn-temporal-snapshot §6.1), so the chain still
        verifies and the hole still shadows the path's earlier versions. It seeks the path's
        rows by their key, so it needs the landing log's secret."""
        with self._writing():
            self._conn.execute("DELETE FROM vault_files WHERE source_path = ?", [source_path])
            self._log.empty_path(source_path)

    def paths_for_digest(self, digest: str) -> list[str]:
        rows = self._conn.execute(
            "SELECT source_path FROM vault_files WHERE digest = ? ORDER BY source_path", [digest]
        ).fetchall()
        return [r["source_path"] for r in rows]

    def remove_digest(self, digest: str) -> int:
        """Delete every catalog row for a digest (the gated purge removes only tombstoned
        content — callers must verify `active_refs(digest) == 0` first). Returns rows removed.

        Every row of the digest in the landing log is emptied in the same transaction, as
        `remove` empties a path's, including a version a live path held before: the log then
        returns a hole at a cut where that version was the head, never the version before it. A
        path none of whose versions keeps its content afterwards has its tombstones emptied too,
        so no row of the log names it (`LandingLog.empty_digest`). It needs no secret."""
        with self._writing():
            cur = self._conn.execute("DELETE FROM vault_files WHERE digest = ?", [digest])
            self._log.empty_digest(digest)
        return cur.rowcount

    # the landing log's reads (dn-temporal-snapshot §4.1; SNP-1 to SNP-5). A cut over a class is
    # one position a chain, `{chain: seq}`; a bare integer is taken for a class with one chain.

    def chains(self, provenance: Provenance | str) -> list[int]:
        """The ids of the landing chains that hold a class now, oldest first."""
        return self._log.chains(str(provenance))

    def head(self, chain: int) -> int:
        """A chain's last position: its head."""
        return self._log.head(chain)

    def read_at(self, chain: int, c: int) -> list[Landing]:
        """The prefix of a chain at `c`: its rows with `seq ≤ c`, in order."""
        return self._log.read_at(chain, c)

    def read_between(self, chain: int, a: int, b: int) -> list[Landing]:
        """A chain's rows after `a` and up to `b`, in order."""
        return self._log.read_between(chain, a, b)

    def state_at(self, provenance: Provenance | str, source_path: str,
                 c: Mapping[int, int] | int) -> Landing | None:
        """A path's last event at or under the cut, over the class's chains: a `store`, a
        `retire`, a `move` or a `leave`, a hole, or nothing. One seek on the key index a chain."""
        return self._log.state_at(str(provenance), source_path, c)

    def history_at(self, provenance: Provenance | str, source_path: str,
                   c: Mapping[int, int] | int) -> list[Landing]:
        """A path's `store` rows at or under the cut, over the class's chains; a purged version
        is a hole in place. Oldest first in each chain; across two chains of one class, which a
        path has only after a change of class and a relabel that merged the two, the chains it
        left come first and the one that holds its present last, a rule of the prefixes and not
        the order the versions landed in (`LandingLog.history_at`)."""
        return self._log.history_at(str(provenance), source_path, c)

    def heads_at(self, provenance: Provenance | str, c: Mapping[int, int] | int) -> list[Landing]:
        """Every head of a class at the cut: the `store` rows alive there, through the closing
        stamp, a hole returned as a hole with its position and no name."""
        return self._log.heads_at(str(provenance), c)

    def verify(self, chain: int) -> ChainCheck:
        """A chain's hashes recomputed from its first row, and every commitment that still has
        its salt: the first position where one fails, or none."""
        return self._log.verify(chain)

    def cuts(self, provenances: Iterable[Provenance | str]) -> Evaluation:
        """An evaluation of the algebra of cuts over the chains these classes hold now, the head
        of each read once, now (`core/stores/cuts.py`, dn-temporal-snapshot §4.4): the cut as a
        value, the versions a cut holds and the operators on them. It reads the log's rows as
        they are and needs no secret."""
        return Evaluation(self._conn, (str(p) for p in provenances))

    def close(self) -> None:
        self._conn.close()


def _to_entry(r: sqlite3.Row) -> CatalogEntry:
    return CatalogEntry(
        source_path=r["source_path"], digest=r["digest"], title=r["title"],
        active=bool(r["active"]), provenance=r["provenance"],
    )
