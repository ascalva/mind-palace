"""LanceDB thought-graph vector store (BUILD-SPEC §7, §8).

Embedded, no daemon. Every chunk row carries its `provenance` so retrieval can be
filtered by provenance class — this is what makes the mirror=AUTHORED-only firewall
(design-notes/observed-data-and-the-assistant-tier.md) structural, not advisory: a
mirror query passes `provenances={AUTHORED}` and cannot surface observed exhaust.

Vectors are a derived, regenerable layer; the raw store remains the source of truth.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import lancedb
import pyarrow as pa

from core.provenance import Provenance

TABLE = "chunks"


def _schema(dim: int) -> pa.Schema:
    return pa.schema([
        ("id", pa.string()),            # f"{digest}:{chunk_index}"
        ("digest", pa.string()),        # raw-store identity of the source note
        ("title", pa.string()),
        ("source_path", pa.string()),
        ("chunk_index", pa.int32()),
        ("provenance", pa.string()),
        ("text", pa.string()),
        ("vector", pa.list_(pa.float32(), dim)),
    ])


@dataclass
class VectorStore:
    path: Path
    dim: int

    def __post_init__(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._db = lancedb.connect(str(self.path))

    def _table(self):
        if TABLE in self._db.list_tables().tables:
            return self._db.open_table(TABLE)
        return self._db.create_table(TABLE, schema=_schema(self.dim))

    def add(self, rows: Iterable[dict[str, Any]]) -> int:
        rows = list(rows)
        if not rows:
            return 0
        for r in rows:  # fail fast on a model/config dimension mismatch
            if len(r["vector"]) != self.dim:
                raise ValueError(
                    f"vector dim {len(r['vector'])} != configured {self.dim}; "
                    "re-embed from raw or fix config (§8)"
                )
        self._table().add(rows)
        return len(rows)

    def count(self) -> int:
        if TABLE not in self._db.list_tables().tables:
            return 0
        return self._table().count_rows()

    def reset(self) -> None:
        """Drop the vector table. Vectors are derived (§8): a full re-ingest rebuilds
        them from the raw corpus, so this is the idempotent path for re-indexing."""
        if TABLE in self._db.list_tables().tables:
            self._db.drop_table(TABLE)

    def delete(self, *, digest: str) -> None:
        """Drop all derived rows for a source note (by its raw-store digest). Idempotent.

        The incremental watcher uses this to retire stale embeddings when a note changes or is
        deleted — derived layer only; the raw blob is untouched (§8). `digest` is a hex SHA-256
        (no quoting hazard)."""
        if TABLE not in self._db.list_tables().tables:
            return
        self._table().delete(f"digest = '{digest}'")

    def relabel_provenance(self, old: str, new: str) -> int:
        """Rewrite every row's provenance from `old` to `new`. Returns rows relabeled.

        Used by the §1 spectrum-split migration to relabel the legacy `'authored'` rows to
        `'authored-solo'`. This is a SAME-TRUST-TIER relabel (both are mirror-readable), not a
        promotion across the §8 firewall — so it is a safe, deterministic data migration, not a
        gated provenance change. Idempotent by construction: a second run finds no `old` rows
        and is a no-op. Implemented as delete-then-re-add (the store's existing re-index idiom)
        so it stays portable — no dependency on a LanceDB in-place `update`."""
        if old == new or TABLE not in self._db.list_tables().tables:
            return 0
        rows = [r for r in self._table().to_arrow().to_pylist() if r.get("provenance") == old]
        if not rows:
            return 0
        for r in rows:
            r["provenance"] = new
        self._table().delete(f"provenance = '{old}'")
        self.add(rows)
        return len(rows)

    def all_rows(self, *,
                 provenances: Iterable[Provenance] | None = None) -> list[dict[str, Any]]:
        """Full scan, optionally restricted to provenance classes — the read the dreaming
        agent clusters over. The clustering itself is deterministic and model-free (§9), so
        the mirror passes `provenances={AUTHORED}` and observed exhaust never seeds a dream.
        Single-user corpus scale; filtered in Python after the Arrow scan for portability."""
        if TABLE not in self._db.list_tables().tables:
            return []
        rows = self._table().to_arrow().to_pylist()
        if provenances is None:
            return rows
        allowed = {Provenance(p).value for p in provenances}
        return [r for r in rows if r.get("provenance") in allowed]

    def search(self, vector: list[float], *, k: int = 5,
               provenances: Iterable[Provenance] | None = None) -> list[dict[str, Any]]:
        """Nearest-neighbour search, optionally restricted to provenance classes.
        `provenances=None` searches everything; the mirror passes {AUTHORED}."""
        if TABLE not in self._db.list_tables().tables:
            return []
        q = self._table().search(vector).metric("cosine")
        if provenances is not None:
            allowed = ", ".join(f"'{Provenance(p).value}'" for p in provenances)
            # prefilter so the k nearest are taken from the permitted set, not after.
            q = q.where(f"provenance IN ({allowed})", prefilter=True)
        return q.limit(k).to_list()


def open_vector_store(config: object | None = None) -> VectorStore:
    from config.loader import get_config

    cfg = config or get_config()
    return VectorStore(path=cfg.paths.vector_store, dim=cfg.embedding.dim)
