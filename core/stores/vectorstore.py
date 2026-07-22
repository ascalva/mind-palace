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

import pyarrow as pa

from core.kernel.config import Config
from core.kernel.provenance import Provenance
from core.typedshims.lancedb import VectorTable, connect

TABLE = "chunks"


# The layer coordinate (dn-code-ingest-pipeline §2.2): note rows default 'prose'; the code embed
# lane discriminates its three projections. One shared table, one additive schema — the fiber
# ruling (§2.4 L2a): the (path, qualname, line-range) code↔code containment is carried ON the rows
# as backpointers, never minted as edge rows.
LAYER_PROSE = "prose"        # authored notes (the pre-code default)
LAYER_CODE_AST = "code_ast"  # L0a — per-symbol structural slice
LAYER_CODE_TEXT = "code_text"  # L0b — windowed raw-source reading
LAYER_CODEDOC = "codedoc"    # L1 — docstrings + comments as prose


def _schema(dim: int) -> pa.Schema:
    return pa.schema([
        ("id", pa.string()),            # doc-scoped content id: f"{source_path}:{chunk_hash}" (§4)
        ("digest", pa.string()),        # raw-store identity of the source note's CURRENT version
        ("title", pa.string()),
        ("source_path", pa.string()),
        ("chunk_index", pa.int32()),
        ("provenance", pa.string()),
        ("text", pa.string()),
        # The layer coordinate + the code fiber coordinates (dn-code-ingest-pipeline §2.2/§2.4).
        # Note rows carry 'prose' / '' / 0 / 0; the code lane fills them. Additive: an old 8-col
        # store is migrated in place by `_migrate_layer_if_needed` (rows preserved, vectors intact).
        ("layer", pa.string()),
        ("qualname", pa.string()),      # code fiber: the symbol ('' for note/L0b/module-shell rows)
        ("line_start", pa.int32()),     # code fiber: first source line (0 for note rows)
        ("line_end", pa.int32()),       # code fiber: last source line (0 for note rows)
        # The temporal-corpus flag (dn-temporal-code-corpus D2/D3, bp-099): is this row part of the
        # source path's CURRENT (HEAD) projection? A superseded code version is RETAINED with
        # current=false (keep-and-link, never deleted); note rows carry the vacuous current=true.
        # Additive: a pre-bp-099 store (no `current`) is migrated in place by
        # `_migrate_current_if_needed` (every row stamped current=true — correct while the store
        # holds only HEAD code + note rows, which is why the migration lands BEFORE any backfill).
        ("current", pa.bool_()),
        ("vector", pa.list_(pa.float32(), dim)),
    ])


# The default coordinates a NOTE row (or any pre-code row) carries for the code-only columns.
# `current=True` is the vacuous note-row default (D3) and the HEAD default for a landed code row.
_NOTE_LAYER_DEFAULTS: dict[str, Any] = {
    "layer": LAYER_PROSE, "qualname": "", "line_start": 0, "line_end": 0, "current": True,
}


@dataclass
class VectorStore:
    path: Path
    dim: int

    def __post_init__(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._db = connect(str(self.path))
        self._schema_checked = False
        self._current_checked = False

    def _table(self) -> VectorTable:
        if TABLE in self._db.list_tables().tables:
            return self._db.open_table(TABLE)
        return self._db.create_table(TABLE, schema=_schema(self.dim))

    def _migrate_layer_if_needed(self) -> None:
        """Reset+rebuild an old 8-column store to the layer schema (dn-code-ingest-pipeline §2.2),
        ONCE per instance. Vectors are derived (§8), so this is safe; it PRESERVES every existing
        row bit-identically (text/digest/vector unchanged — `core.ingest.verify` still passes) by
        re-landing note rows with the code-only columns defaulted ('prose'/''/0/0). An empty old
        table is simply dropped (the next add recreates it fresh). Idempotent: a table already
        carrying `layer` is left untouched."""
        if self._schema_checked:
            return
        self._schema_checked = True
        if TABLE not in self._db.list_tables().tables:
            return                                  # no table yet → next add creates the new schema
        rows = self._table().to_arrow().to_pylist()
        if rows and "layer" in rows[0]:
            return                                  # already the layer schema
        self._db.drop_table(TABLE)
        if not rows:
            return                                  # empty old table → recreate fresh on next add
        migrated = [{**r, **{k: v for k, v in _NOTE_LAYER_DEFAULTS.items() if k not in r}}
                    for r in rows]
        self._table().add(migrated)                 # recreates the layer schema, vectors intact

    def _migrate_current_if_needed(self) -> None:
        """Additive migration for the `current` column (dn-temporal-code-corpus D2, bp-099) — the
        exact `_migrate_layer_if_needed` precedent. Reset+rebuild a pre-bp-099 store (schema without
        `current`) ONCE per instance, PRESERVING every row bit-identically (vectors are derived, §8)
        by re-landing it with `current=true`. That default is correct BECAUSE the migration runs
        before any history backfill, when the store holds only HEAD code rows + note rows — each of
        which IS current. Idempotent: a table already carrying `current` is left untouched. Runs
        AFTER the layer migration, which (via `_NOTE_LAYER_DEFAULTS`) already stamps `current` when
        it fires, so this is a no-op on a store that just came through the 8→layer path."""
        if self._current_checked:
            return
        self._current_checked = True
        if TABLE not in self._db.list_tables().tables:
            return                                  # no table yet → next add creates the new schema
        rows = self._table().to_arrow().to_pylist()
        if rows and "current" in rows[0]:
            return                                  # already the temporal schema
        self._db.drop_table(TABLE)
        if not rows:
            return                                  # empty old table → recreate fresh on next add
        migrated = [{**r, "current": True} for r in rows]
        self._table().add(migrated)             # recreates the schema + `current`, vectors intact

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
        # Default the code-only columns (layer/qualname/line_start/line_end) on any row that omits
        # them — so every legacy 8-key caller (a note row, a test row) lands as a valid layer-schema
        # row (layer='prose') without change, and the code lane's explicit values pass through.
        rows = [{**_NOTE_LAYER_DEFAULTS, **r} for r in rows]
        self._migrate_layer_if_needed()             # bring an old 8-col store to the layer schema
        self._migrate_current_if_needed()       # then bring a pre-bp-099 store to temporal schema
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

    def rows_for_source(self, source_path: str) -> list[dict[str, Any]]:
        """Every stored chunk row for one source document (by `source_path`) — the note's current
        projection. The amendment path (ingest-identity §4) reads this to REUSE unchanged chunks'
        vectors instead of re-embedding. Python-side filter (single-user scale; avoids a quoting
        hazard on arbitrary source paths, matching `all_rows`)."""
        if TABLE not in self._db.list_tables().tables:
            return []
        return [r for r in self._table().to_arrow().to_pylist()
                if r.get("source_path") == source_path]

    def delete_source(self, source_path: str) -> None:
        """Drop every derived row for one source document, by `source_path` (the stable doc identity
        an amendment replaces a projection under — §4). Idempotent. Deletes by the rows' own ids
        with single-quotes escaped, so an arbitrary source path never breaks the predicate."""
        rows = self.rows_for_source(source_path)
        if not rows:
            return
        ids = ", ".join("'" + str(r["id"]).replace("'", "''") + "'" for r in rows)
        self._table().delete(f"id IN ({ids})")

    def supersede_source(self, source_path: str) -> int:
        """Keep-and-link (dn-temporal-code-corpus D2, bp-099): flip every CURRENTLY-current row of
        `source_path` to `current=false` while RETAINING it — a superseded code version is never
        deleted. Returns the number of rows flipped (0 if the path had no current rows).

        Implemented as read → delete-whole-path → re-add, the store's portable re-index idiom
        (`relabel_provenance`): every one of the path's rows (all versions) is dropped by id and
        re-landed, with the still-current ones now `current=false` and any already-superseded rows
        unchanged — vectors carried through the move (§8). Deleting the whole path in one pass, then
        re-adding, sidesteps the id collision a version-scoped delete would hit (an unchanged chunk
        keeps its content-addressed id across versions, so ids are no longer unique once history is
        retained). Idempotent: a path with nothing current re-lands identical rows (a no-op)."""
        rows = self.rows_for_source(source_path)
        flipped = sum(1 for r in rows if r.get("current"))
        if flipped == 0:
            return 0
        self.delete_source(source_path)             # drop all versions' rows (id-IN, collisions ok)
        for r in rows:
            r["current"] = False
        self.add(rows)                              # re-land ALL as current=false (vectors intact)
        return flipped

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
               provenances: Iterable[Provenance] | None = None,
               include_superseded: bool = False) -> list[dict[str, Any]]:
        """Nearest-neighbour search, optionally restricted to provenance classes.
        `provenances=None` searches everything; the mirror passes {AUTHORED}.

        Default retrieval is CURRENT-VIEW (dn-temporal-code-corpus D3, bp-099): a superseded code
        version (`current=false`, kept by keep-and-link) never surfaces unasked, so every existing
        consumer is unchanged (note rows carry the vacuous current=true). A temporal consumer opts
        into history with `include_superseded=True`."""
        if TABLE not in self._db.list_tables().tables:
            return []
        q = self._table().search(vector).metric("cosine")
        clauses: list[str] = []
        if provenances is not None:
            allowed = ", ".join(f"'{Provenance(p).value}'" for p in provenances)
            clauses.append(f"provenance IN ({allowed})")
        if not include_superseded:
            clauses.append("current = true")        # current-view default (D3)
        if clauses:
            # prefilter so the k nearest are taken from the permitted set, not after.
            q = q.where(" AND ".join(clauses), prefilter=True)
        return q.limit(k).to_list()


def open_vector_store(config: Config | None = None) -> VectorStore:
    from core.kernel.config import get_config

    cfg = config or get_config()
    return VectorStore(path=cfg.paths.vector_store, dim=cfg.embedding.dim)
