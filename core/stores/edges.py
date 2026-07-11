"""The typed/signed edge store — the fiber ε(e) = (t, w, s, τ) (companion III §1.2; Prompt H1).

A *binary* typed edge carries a relation type, a strength w ≥ 0, and a polarity s ∈ {+1, −1}
(`EdgeSign` — the R1 enum). This is the persistent home for edges that are **not recomputable from
embeddings** (BUILD §1.1): explicit contradictions/links a detector or the owner asserts. Similarity
edges are *recomputed* each pass from the embeddings and are NOT stored here (that would duplicate a
regenerable signal); this table stores the polarity/relations the cosine graph cannot carry —
chiefly contradiction, the input to `balance.py`.

Derivation (a B-arc, tail set → head) is a *hyperedge*, stored in the `DerivedStore` junction, not
here; the two are deliberately distinct structures (companion III §1.3). Zone A, no network.
"""

from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from config.loader import Config
from core.complex_types import EdgeSign

# Binary relation types (a small, mostly-closed set; kept as string constants rather than an enum
# because it is still growing — unlike the polarity, which is a closed ±1 set and IS an enum).
SIMILAR = "similar"              # cosine backbone (usually recomputed, not stored)
SUPPORTS = "supports"            # one note reinforces another (+)
CONTRADICTS = "contradicts"      # one note is in tension with another (−) — the balance input
CONTEXTUALIZES = "contextualizes"
# NOTE: note-version supersession is deliberately NOT an edge type here (build plan Item 6; §4A
# C1–C2). It is PRIMARY provenance keyed on version identity — a `sign` in this balance-fed store
# would corrupt the signed-graph math — so it lives in `core/stores/versions.py`, a store the
# reasoning complex has no handle to. Do not re-add a `supersedes` rel-type to this table.

_DDL = """
CREATE TABLE IF NOT EXISTS edges (
    edge_id     TEXT PRIMARY KEY,      -- content-id(u, v, rel_type)
    u           TEXT NOT NULL,         -- source atom digest
    v           TEXT NOT NULL,         -- target atom digest
    w           REAL NOT NULL,         -- strength >= 0
    sign        INTEGER NOT NULL,      -- +1 support / -1 contradict (EdgeSign; polarity)
    rel_type    TEXT NOT NULL,         -- similar | supports | contradicts | contextualizes
    created_at  TEXT NOT NULL,         -- ISO ts (the temporal index τ)
    provenance  TEXT NOT NULL          -- authored_* | interpreted (edges are layered too)
);
CREATE INDEX IF NOT EXISTS edges_u ON edges(u);
CREATE INDEX IF NOT EXISTS edges_v ON edges(v);
CREATE INDEX IF NOT EXISTS edges_rel ON edges(rel_type);
"""


def _utcnow() -> str:
    return datetime.now(UTC).replace(tzinfo=None).isoformat(timespec="seconds")


def _edge_id(u: str, v: str, rel_type: str) -> str:
    """Content-derived id from (u, v, rel_type) so re-asserting the same edge is idempotent."""
    return hashlib.sha256("\x00".join([rel_type, u, v]).encode("utf-8")).hexdigest()[:16]


@dataclass(frozen=True)
class Edge:
    """One typed/signed binary edge — the fiber (w, s, rel_type, τ) over the pair (u, v)."""

    edge_id: str
    u: str
    v: str
    w: float
    sign: EdgeSign
    rel_type: str
    created_at: str
    provenance: str


@dataclass
class EdgeStore:
    path: Path

    def __post_init__(self) -> None:
        if str(self.path) != ":memory:":
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.path))
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_DDL)
        self._conn.commit()

    def add(self, u: str, v: str, *, sign: EdgeSign, rel_type: str, w: float = 1.0,
            provenance: str = "interpreted", created_at: str | None = None) -> Edge:
        """Assert a typed/signed edge. `sign` is the `EdgeSign` enum (±1); `w ≥ 0` is the strength.
        Idempotent on (u, v, rel_type) — re-asserting replaces (INSERT OR REPLACE)."""
        if w < 0.0:
            raise ValueError(f"edge strength w must be >= 0 (polarity is `sign`), got {w}")
        sign = EdgeSign(sign)                              # reject any non-±1 value at the boundary
        rec = Edge(edge_id=_edge_id(u, v, rel_type), u=u, v=v, w=float(w), sign=sign,
                   rel_type=rel_type, created_at=created_at or _utcnow(), provenance=provenance)
        self._conn.execute(
            "INSERT OR REPLACE INTO edges VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [rec.edge_id, rec.u, rec.v, rec.w, int(rec.sign), rec.rel_type,
             rec.created_at, rec.provenance],
        )
        self._conn.commit()
        return rec

    def all(self, *, rel_type: str | None = None) -> list[Edge]:
        sql = "SELECT * FROM edges"
        params: list[str] = []
        if rel_type is not None:
            sql += " WHERE rel_type = ?"
            params.append(rel_type)
        sql += " ORDER BY edge_id"
        return [self._row(r) for r in self._conn.execute(sql, params).fetchall()]

    def count(self) -> int:
        row = self._conn.execute("SELECT count(*) FROM edges").fetchone()
        return int(row[0]) if row else 0

    def reset(self) -> None:
        """Drop all edges. Similarity edges are regenerable; asserted edges are re-derivable by
        the detector/owner that created them."""
        self._conn.execute("DELETE FROM edges")
        self._conn.commit()

    def delete_rel_type(self, rel_type: str) -> int:
        """Delete every edge of a given `rel_type`; returns rows removed. The migration for build
        plan Item 6: retire any misplaced `supersedes` rows a prior build wrote here, now that
        note-version history lives in the dedicated `VersionStore` the balance math cannot read."""
        cur = self._conn.execute("DELETE FROM edges WHERE rel_type = ?", [rel_type])
        self._conn.commit()
        return cur.rowcount

    @staticmethod
    def _row(r: sqlite3.Row) -> Edge:
        return Edge(edge_id=r["edge_id"], u=r["u"], v=r["v"], w=r["w"],
                    sign=EdgeSign(r["sign"]), rel_type=r["rel_type"],
                    created_at=r["created_at"], provenance=r["provenance"])

    def close(self) -> None:
        self._conn.close()


def open_edge_store(config: Config | None = None) -> EdgeStore:
    from config.loader import get_config

    cfg = config or get_config()
    # Reuse the derived-store directory; edges are interpreted-layer structure alongside dreams.
    return EdgeStore(cfg.paths.derived_store.parent / "edges.sqlite")
