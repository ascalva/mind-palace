"""Derived-artifact store for the INTERPRETED layer (BUILD-SPEC §8).

The interpreted layer is what the *system* inferred — dreams (thematic synthesis) and
curator findings (near-duplicate / prune / contradiction candidates). Per §8 it is kept
SEPARATE and PROVENANCE-MARKED from the owner's authored ground truth: this store holds
`INTERPRETED` only and exposes NO way to write any other provenance — so the derived layer
can never masquerade as authored ground truth. That is the structural form of "explicit vs
interpreted — separate, provenance-marked layers"; it is not an honor-system check.

Everything here is regenerable: `reset()` drops it and a fresh dreaming/curation run
rebuilds it from the (immutable) corpus. Artifact ids are content-derived, so re-running a
cron pass is idempotent (INSERT OR REPLACE) rather than accumulating duplicates.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from core.provenance import Provenance

# Artifact kinds (the discriminator). Dreams are thematic synthesis; findings are the
# curator's flagged candidates (subkind carries the finding type).
DREAM = "dream"
FINDING = "finding"

_DDL = """
CREATE TABLE IF NOT EXISTS interpreted_artifacts (
    id          TEXT PRIMARY KEY,
    kind        TEXT NOT NULL,        -- 'dream' | 'finding'
    subkind     TEXT,                 -- finding type: near_duplicate | prune | contradiction
    provenance  TEXT NOT NULL,        -- always 'interpreted' (this store writes nothing else)
    summary     TEXT NOT NULL,
    subjects    TEXT NOT NULL,        -- JSON array of note titles the artifact concerns
    data        TEXT NOT NULL,        -- JSON payload, kind-specific
    created_at  TEXT NOT NULL
);
"""


def _utcnow() -> str:
    return datetime.now(UTC).replace(tzinfo=None).isoformat(timespec="seconds")


def _artifact_id(kind: str, subkind: str | None, subjects: tuple[str, ...]) -> str:
    """Content-derived id so re-running a pass over the same notes is idempotent."""
    key = "|".join([kind, subkind or "", *sorted(subjects)])
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


@dataclass(frozen=True)
class Artifact:
    id: str
    kind: str
    subkind: str | None
    provenance: Provenance       # always INTERPRETED
    summary: str
    subjects: tuple[str, ...]
    data: dict
    created_at: str


@dataclass
class DerivedStore:
    path: Path

    def __post_init__(self) -> None:
        if str(self.path) != ":memory:":
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.path))
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_DDL)
        self._conn.commit()

    def add(self, *, kind: str, summary: str, subjects: tuple[str, ...] | list[str],
            data: dict | None = None, subkind: str | None = None) -> Artifact:
        """Store one INTERPRETED artifact. There is deliberately NO `provenance` parameter:
        the derived store writes `INTERPRETED` and nothing else (§8 firewall, structural)."""
        subjects = tuple(subjects)
        rec = Artifact(
            id=_artifact_id(kind, subkind, subjects),
            kind=kind,
            subkind=subkind,
            provenance=Provenance.INTERPRETED,
            summary=summary,
            subjects=subjects,
            data=data or {},
            created_at=_utcnow(),
        )
        self._conn.execute(
            "INSERT OR REPLACE INTO interpreted_artifacts VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [rec.id, rec.kind, rec.subkind, rec.provenance.value, rec.summary,
             json.dumps(list(rec.subjects)), json.dumps(rec.data), rec.created_at],
        )
        self._conn.commit()
        return rec

    def all(self, *, kind: str | None = None, subkind: str | None = None) -> list[Artifact]:
        sql = "SELECT * FROM interpreted_artifacts"
        clauses, params = [], []
        if kind is not None:
            clauses.append("kind = ?")
            params.append(kind)
        if subkind is not None:
            clauses.append("subkind = ?")
            params.append(subkind)
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY created_at, id"
        return [self._row(r) for r in self._conn.execute(sql, params).fetchall()]

    def count(self, *, kind: str | None = None) -> int:
        if kind is None:
            return self._conn.execute("SELECT count(*) FROM interpreted_artifacts").fetchone()[0]
        return self._conn.execute(
            "SELECT count(*) FROM interpreted_artifacts WHERE kind = ?", [kind]
        ).fetchone()[0]

    def reset(self) -> None:
        """Drop all derived artifacts. Interpreted data is regenerable (§8): a fresh
        dreaming/curation run rebuilds it from the immutable corpus."""
        self._conn.execute("DELETE FROM interpreted_artifacts")
        self._conn.commit()

    @staticmethod
    def _row(r: sqlite3.Row) -> Artifact:
        return Artifact(
            id=r["id"], kind=r["kind"], subkind=r["subkind"],
            provenance=Provenance(r["provenance"]),
            summary=r["summary"], subjects=tuple(json.loads(r["subjects"])),
            data=json.loads(r["data"]), created_at=r["created_at"],
        )

    def close(self) -> None:
        self._conn.close()


def open_derived_store(config: object | None = None) -> DerivedStore:
    from config.loader import get_config

    cfg = config or get_config()
    return DerivedStore(cfg.paths.derived_store)
