# ── Family 1 boundary · the provenance layer (version history, NOT the semantic edge graph) ──
# OBJECT:    the append-only version-history store — note-version supersession as PRIMARY
#            provenance, keyed on version identity (ingest-identity-and-amendment.md §4A).
# INVARIANT: append-only; version identity = (doc_id, monotonic version_seq), NOT content digest
#            (C1: a revert stays linear, no cycle); the balance math cannot read this store (C2:
#            version history never enters the signed-edge projection — there is no code handle).
# ENFORCED:  structural — append + reads only (no update/delete); a store distinct from EdgeStore,
#            so no consumer of the signed graph (build_complex takes an EdgeStore, not this) can
#            reach a version row. Ordering is by version_seq, never by walking edges (§4A).
"""Append-only note-version history (ingest-identity-and-amendment.md §4A; build plan Item 6).

A note edited over time is a sequence of VERSIONS, and "v2 supersedes v1" is a PRIMARY provenance
fact — distinct from the semantic support/contradiction edges the balance math consumes. It lives
HERE, not in the `EdgeStore`, for two reasons the shipped implementation got wrong (§4A C1–C2):

  * **Keyed on version identity, not content digest.** Endpoints are `(doc_id, version_seq)`, so a
    revert (v1 → v2 → back to v1's exact bytes) is v3 at seq 3 — distinct from v1 even though the
    digest repeats. The chain stays linear; NO cycle-guard is wanted (rejecting the revert would
    refuse truthful history and break append-only). Content-hash stays the key for the vector
    projection; version-seq is the key here — two layers, two identities.
  * **The balance math cannot read it.** A version relation must never enter the signed-edge graph
    (a placeholder `sign` corrupts λ_min / frustration). `build_complex` takes an `EdgeStore` and
    has no handle to this store, so the exclusion is structural — not a rel-type-filter discipline
    every consumer must remember (the prior design was excluded only *accidentally*; see Q8).

Append-only: each version is one row, `version_seq` monotonic per `doc_id`. The current version is
`max(version_seq)`; supersession is the consecutive-seq relation — both DERIVED from the ordered
sequence, never from edge topology (§4A Ordering authority). Zone A, no network.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from config.loader import Config


def _utcnow() -> str:
    return datetime.now(UTC).replace(tzinfo=None).isoformat(timespec="seconds")


@dataclass(frozen=True)
class Version:
    doc_id: str
    version_seq: int
    digest: str
    at: str


_DDL = """
CREATE TABLE IF NOT EXISTS versions (
    doc_id      TEXT NOT NULL,        -- stable document identity (the catalog source_path)
    version_seq INTEGER NOT NULL,     -- monotonic per doc_id (1,2,3,…) — the VERSION identity
    digest      TEXT NOT NULL,        -- content digest of THIS version (may repeat on a revert)
    at          TEXT NOT NULL,        -- when this version was recorded
    PRIMARY KEY (doc_id, version_seq)
);
CREATE INDEX IF NOT EXISTS versions_doc ON versions(doc_id, version_seq);
"""


@dataclass
class VersionStore:
    path: Path

    def __post_init__(self) -> None:
        if str(self.path) != ":memory:":
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.path))
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_DDL)
        self._conn.commit()

    def current(self, doc_id: str) -> Version | None:
        """The current (highest-seq) version of a document, or None if never recorded."""
        row = self._conn.execute(
            "SELECT * FROM versions WHERE doc_id = ? ORDER BY version_seq DESC LIMIT 1", [doc_id]
        ).fetchone()
        return _row(row) if row else None

    def record(self, doc_id: str, digest: str) -> Version:
        """Append the next version of `doc_id` at `digest` (version_seq = current + 1, or 1). A
        revert to an earlier version's bytes is a NEW version at a higher seq — never a cycle, never
        a merge (§4A C1). Append-only: no prior row is mutated."""
        cur = self.current(doc_id)
        seq = (cur.version_seq + 1) if cur is not None else 1
        v = Version(doc_id=doc_id, version_seq=seq, digest=digest, at=_utcnow())
        self._conn.execute("INSERT INTO versions VALUES (?, ?, ?, ?)",
                           [v.doc_id, v.version_seq, v.digest, v.at])
        self._conn.commit()
        return v

    def history(self, doc_id: str) -> list[Version]:
        """Every version of a document in version-seq order (the append-only chain)."""
        return [_row(r) for r in self._conn.execute(
            "SELECT * FROM versions WHERE doc_id = ? ORDER BY version_seq", [doc_id]).fetchall()]

    def supersessions(self, doc_id: str) -> list[tuple[int, int]]:
        """The `(superseded_seq, superseding_seq)` pairs — consecutive versions, DERIVED from the
        ordered sequence (never from edge topology, §4A Ordering authority)."""
        seqs = [v.version_seq for v in self.history(doc_id)]
        return list(zip(seqs, seqs[1:], strict=False))

    def count(self) -> int:
        row = self._conn.execute("SELECT count(*) FROM versions").fetchone()
        return int(row[0]) if row else 0

    def close(self) -> None:
        self._conn.close()


def _row(r: sqlite3.Row) -> Version:
    return Version(doc_id=r["doc_id"], version_seq=r["version_seq"], digest=r["digest"], at=r["at"])


def open_version_store(config: Config | None = None) -> VersionStore:
    from config.loader import get_config

    cfg = config or get_config()
    return VersionStore(cfg.paths.derived_store.parent / "versions.sqlite")
