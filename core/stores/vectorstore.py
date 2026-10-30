"""LanceDB thought-graph vector store (BUILD-SPEC §7, §8).

Embedded, no daemon. Every chunk row carries its `provenance` so retrieval can be
filtered by provenance class — this is what makes the mirror=AUTHORED-only firewall
(design-notes/observed-data-and-the-assistant-tier.md) structural, not advisory: a
mirror query passes `provenances={AUTHORED}` and cannot surface observed exhaust.

Vectors are a derived, regenerable layer; the raw store remains the source of truth.

[banner: extension] dn-vector-membership-store Amendment A3 (2026-10-29): every PROSE stratum now
lands in the shared plane (`core/stores/plane.py`) — one atom row per distinct chunk text in this
table, classless, and its occupancies in one relation per provenance class beside it. Every read
takes a `Clearance` (a capability minted only by an authority, `core/kernel/clearance.py`) and
returns `Row[L]` values built by a sealed constructor that re-checks the class, so a row the
clearance does not admit cannot exist. CODE keeps its own atom plane (D1) and membership store.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import Any, cast

import pyarrow as pa

from core.kernel.clearance import _MINT, MAINTENANCE_READ, Clearance, ClearanceViolation, Row
from core.kernel.config import Config
from core.kernel.provenance import Provenance
from core.stores.plane import (
    PLANE_CLASSES,
    AtomRecord,
    Candidate,
    Fingerprint,
    PlaneReader,
    SharedPlane,
)
from core.typedshims.lancedb import VectorTable, connect

TABLE = "chunks"

# How many ids one `id IN (...)` predicate may name before `set_current_any` starts a new batch.
# Bounds the SQL string, never the semantics: the batches are independent in-place updates.
_ID_PREDICATE_CHUNK = 400


# The layer coordinate (dn-code-ingest-pipeline §2.2): note rows default 'prose'; the code embed
# lane discriminates its three projections. One shared table, one additive schema — the fiber
# ruling (§2.4 L2a): the (path, qualname, line-range) code↔code containment is carried ON the rows
# as backpointers, never minted as edge rows.
LAYER_PROSE = "prose"        # authored notes (the pre-code default)
LAYER_CODE_AST = "code_ast"  # L0a — per-symbol structural slice
LAYER_CODE_TEXT = "code_text"  # L0b — windowed raw-source reading
LAYER_CODEDOC = "codedoc"    # L1 — docstrings + comments as prose


def _schema(dim: int) -> pa.Schema:
    fields: list[tuple[str, pa.DataType]] = [
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
        # [banner: correction] The temporal-corpus flag (dn-temporal-code-corpus D2/D3, bp-099)
        # WAS one reading: is this row part of the source path's CURRENT (HEAD) projection? Under
        # dn-vector-membership-store D1 (bp-152) this ONE column now carries TWO readings, because
        # the two lanes store different objects under one schema:
        #   * NOTE rows (and any pre-D1 per-version code row) keep the old reading — the vacuous
        #     current=true for prose, keep-and-link current=false for a superseded code version.
        #   * CODE-ATOM rows read it as **`current_any`**: does ANY current membership contain this
        #     atom? An atom is not a version, so "is this the HEAD projection" is not a question it
        #     can answer; `current_any` is the cheap ANN prefilter over membership truth (D3), and
        #     the membership SQLite store is the reference truth it caches (D8, R3).
        # Both readings are served by the ONE `current = true` prefilter clause in `search` — which
        # is exactly why D1 re-reads the column instead of adding a second one.
        ("current", pa.bool_()),
        # [A3] The shared plane's ANN prefilter cache: on a PROSE ATOM row, the classes whose
        # relations hold a current (`held`) / any (`held_ever`) occupancy of it; `[]` on every
        # other row. A CACHE of `core/stores/plane.py`'s relations — it narrows candidates and never
        # decides what a reader receives (a stale entry drops results, never widens them).
        ("held", pa.list_(pa.string())),
        ("held_ever", pa.list_(pa.string())),
        ("vector", pa.list_(pa.float32(), dim)),
    ]
    return pa.schema(fields)


# The default coordinates a NOTE row (or any pre-code row) carries for the code-only columns.
# `current=True` is the vacuous note-row default (D3) and the HEAD default for a landed code row.
_NOTE_LAYER_DEFAULTS: dict[str, Any] = {
    "layer": LAYER_PROSE, "qualname": "", "line_start": 0, "line_end": 0, "current": True,
    "held": [], "held_ever": [],
}

# The occupancy columns a CODE-ATOM row sheds (dn-vector-membership-store D1, bp-152). They are
# shed from the ROW, never from the schema — note rows still carry them, so every prose-lane
# consumer is untouched. The empty values are load-bearing, not cosmetic: `delete_source` /
# `index_amendment` are `source_path`-scoped and can never match `''` (the note's D1 shed-safety
# claim, verified at `core/ingest/index.py:87`), and `is_code_atom_row` reads them as the shed
# marker. `provenance` is NOT here — it STAYS, because the mirror firewall is a row PREFILTER
# (`search`, below) and shedding the column would not weaken the firewall, it would REMOVE it.
ATOM_ROW_SHED: dict[str, Any] = {
    "digest": "", "source_path": "", "chunk_index": 0, "qualname": "",
    "line_start": 0, "line_end": 0,
}


@dataclass(frozen=True)
class CompactionReport:
    """What `VectorStore.compact` physically did (§3).

    Both a BEFORE and an AFTER row count are carried on purpose. Compaction's whole contract is
    that it is semantically invisible, and the only way to assert invisibility without asserting it
    vacuously is to have the two numbers side by side and require them equal WHILE the version
    count fell — a compaction that no-ops leaves every number equal, including the one that is
    supposed to move."""

    rows_before: int = 0
    rows_after: int = 0
    versions_before: int = 0
    versions_after: int = 0

    @property
    def rows_preserved(self) -> bool:
        """The invariant: compaction removes no logical row."""
        return self.rows_before == self.rows_after

    @property
    def versions_dropped(self) -> int:
        return max(0, self.versions_before - self.versions_after)

    def __str__(self) -> str:
        return (f"rows {self.rows_before}->{self.rows_after} "
                f"versions {self.versions_before}->{self.versions_after} "
                f"({self.versions_dropped} dropped)")


def is_code_atom_row(row: Mapping[str, Any]) -> bool:
    """Is this row a shed CODE **atom** row (D1) rather than a source-object chunk row?

    An atom row is geometry with no occupancy: its occupancy lives in the membership relation
    (`core/stores/memberships.py`), so it carries no `source_path` and no `digest`. This predicate
    is the ONE place that reading is spelled out, so `all_rows`' structural guard and the
    membership store's repair pass cannot drift apart."""
    return (row.get("provenance") == Provenance.CODE.value
            and not str(row.get("source_path") or "")
            and not str(row.get("digest") or ""))


def _sql_str(value: str) -> str:
    """One arbitrary string as a SQL literal for a LanceDB predicate — single quotes doubled.

    The ONE escaping idiom in this module (it used to live inline in `delete_source`), so a
    predicate over user-controlled text — a `source_path` with an apostrophe, say — is written the
    same way everywhere. Filtering in Python "to avoid a quoting hazard" was never the alternative
    to this; it was the alternative to *doing this once* (finding-0169)."""
    return "'" + value.replace("'", "''") + "'"


# A shared PROSE atom row (A3): classless and occupancy-free; its occupancies live in the plane's
# per-class relations. No class gate admits it (`provenance IN (…)` never matches ''), which is how
# every record read stays clear of raw atoms.
_PROSE_ATOM = "provenance = '' AND source_path = '' AND digest = ''"
_EMPTY_LIST = "arrow_cast(make_array(), 'List(Utf8)')"
_ALL_CLASSES = frozenset(Provenance)
_PLANE_VALUES = frozenset(p.value for p in PLANE_CLASSES)


def _gate(clearance: Clearance[Provenance]) -> str:
    """The physical-row predicate for a clearance: its classes, spelled from the clearance alone."""
    return "provenance IN (" + ", ".join(_sql_str(c.value) for c in clearance) + ")"


def _id_in(ids: Sequence[str]) -> str:
    return f"id IN ({', '.join(_sql_str(i) for i in ids)})"


def _sql_list(values: Iterable[str]) -> str:
    """A list<string> literal for an update's `values_sql` — empty lists only work this way."""
    items = sorted(values)
    return f"make_array({', '.join(_sql_str(v) for v in items)})" if items else _EMPTY_LIST


@dataclass
class VectorStore:
    path: Path
    dim: int
    # The configured embedder geometry (A3). `open_vector_store`/`open_curated_store` always pass
    # it; None (unit tests) records and checks nothing.
    embedder: Fingerprint | None = None

    def __post_init__(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._db = connect(str(self.path))
        self._schema_checked = False
        self._current_checked = False
        if self.embedder is not None and self.embedder.dim != self.dim:
            raise ValueError(f"embedder dim {self.embedder.dim} != store dim {self.dim}")
        # A3: the shared prose plane lives in this store's own directory — its per-class relations
        # in `plane.sqlite` beside the LanceDB tables, its atoms as rows of the one shared table.
        self._plane = SharedPlane(self.path, _LanceAtoms(self), fingerprint=self.embedder)

    @property
    def plane(self) -> SharedPlane:
        """The shared prose plane (A3) — maintenance and the typed readers go through it."""
        return self._plane

    def reader[L: Provenance](self, clearance: Clearance[L]) -> PlaneReader[L]:
        """A typed reader of the plane under `clearance`: `Occupancy[L]`, `PlaneHit[L]`, rows."""
        return self._plane.reader(clearance)

    def plane_enabled(self) -> bool:
        """Does this store land prose in the shared plane? True for a new store (its table is
        created with the plane schema) and for one `migrate_to_plane` converted; False for a table
        that predates A3 (no `held` column), which keeps the pre-A3 row model until migrated."""
        if TABLE not in self._db.list_tables().tables:
            return True
        return "held" in self._table().schema_names()

    def known_atoms(self, atom_ids: Sequence[str]) -> set[str]:
        """Which atoms the plane already holds under this store's geometry — the embeds a landing
        may skip (a row for a known atom may omit its vector). Empty before the plane exists."""
        return self._plane.known(atom_ids) if self.plane_enabled() else set()

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
        """Land rows; returns the number landed.

        [banner: extension] A3 (dn-vector-membership-store): rows of a PROSE class — every class
        but CODE — land in the shared plane: one atom per distinct chunk text, an occupancy in the
        row's class relation, the path's currency reconciled, a supersession edge when its head
        changed. A prose row may omit its vector when the plane already holds the atom
        (`known_atoms`) — that is the embed the plane saves. CODE rows keep the code lane's
        physical path (`_add_physical`), unchanged. A table that predates the plane schema lands
        prose the pre-A3 way (`_legacy_land`) until `migrate_to_plane` converts it."""
        rows = list(rows)
        if not rows:
            return 0
        for r in rows:  # fail fast on a model/config dimension mismatch
            vec = r.get("vector")
            if vec is None:
                if r.get("provenance") not in _PLANE_VALUES:
                    raise ValueError("a physical row lands with its vector")
                continue
            if len(vec) != self.dim:
                raise ValueError(
                    f"vector dim {len(vec)} != configured {self.dim}; "
                    "re-embed from raw or fix config (§8)"
                )
        # A plane class lands in the plane; CODE — and any retired label (the pre-§1 'authored'),
        # which no clearance admits — stays physical, for `relabel_provenance` to bring across.
        prose = [r for r in rows if r.get("provenance") in _PLANE_VALUES]
        code = [r for r in rows if r.get("provenance") not in _PLANE_VALUES]
        if prose:
            if self.plane_enabled():
                self._plane.land(prose)
            else:
                self._legacy_land(prose)
        if code:
            self._add_physical(code)
        return len(rows)

    def _add_physical(self, rows: list[dict[str, Any]]) -> None:
        # Default the code-only columns (layer/qualname/line_start/line_end) on any row that omits
        # them — so every legacy 8-key caller (a note row, a test row) lands as a valid layer-schema
        # row (layer='prose') without change, and the code lane's explicit values pass through.
        rows = [{**_NOTE_LAYER_DEFAULTS, **r} for r in rows]
        self._migrate_layer_if_needed()             # bring an old 8-col store to the layer schema
        self._migrate_current_if_needed()       # then bring a pre-bp-099 store to temporal schema
        if TABLE in self._db.list_tables().tables:
            # A table from before A3 has no `held`/`held_ever`: land only the columns it has.
            names = set(self._table().schema_names())
            rows = [{k: v for k, v in r.items() if k in names} for r in rows]
        self._table().add(rows)

    def _legacy_land(self, rows: list[dict[str, Any]]) -> None:
        """The pre-A3 prose landing, for a table not yet migrated to the plane: replace each
        path's rows (what the retired delete-then-index callers did by hand)."""
        if any(r.get("vector") is None for r in rows):
            raise ValueError("a store without the plane schema needs every row's vector")
        if TABLE in self._db.list_tables().tables:
            for path in sorted({str(r.get("source_path") or "") for r in rows} - {""}):
                self._table().delete(f"source_path = {_sql_str(path)}")
        self._add_physical(rows)

    def count(self) -> int:
        """Rows a full read would see: every physical row that is not a shared prose atom, plus the
        plane's current occupancies — the number the pre-A3 store reported for the same content."""
        physical = 0
        if TABLE in self._db.list_tables().tables:
            physical = self._table().count_rows(f"NOT ({_PROSE_ATOM})")
        return physical + self._plane.reader(MAINTENANCE_READ).count()

    def reset(self) -> None:
        """Drop the vector table and the plane's relations. Vectors are derived (§8): a full
        re-ingest rebuilds them from the raw corpus, so this is the idempotent path for re-indexing
        (and the only way to change a plane's embedder geometry)."""
        if TABLE in self._db.list_tables().tables:
            self._db.drop_table(TABLE)
        self._plane.reset()

    def delete(self, *, digest: str) -> None:
        """PURGE every derived row of one raw digest — the owner-gated privacy path
        (core/ingest/purge.py). Idempotent.

        [banner: correction] A3: this used to double as an "idempotent re-index" (delete by digest,
        then index) in the dialogue, curated and founding writers. Under shared content that was
        wrong twice: it deleted EVERY document's rows with the same bytes (an owner turn and a model
        turn that say the same words), and it deleted by the NEW digest, so an edited document's
        old version stayed current. Landing is idempotent by reconciliation now, those callers are
        gone, and this keeps one meaning: physical rows of the digest go, and the plane purges its
        occupancies, its supersession entries and the atoms nothing else holds."""
        if not digest:
            raise ValueError("a purge names a digest")
        if TABLE in self._db.list_tables().tables:
            self._table().delete(f"digest = {_sql_str(digest)}")
        self._plane.purge(digest)

    def rows_for_source[L: Provenance](self, source_path: str, *,
                                       clearance: Clearance[L]) -> list[Row[L]]:
        """One document's current rows, vectors included, as far as `clearance` admits its class.

        Physical rows (code, and prose not yet migrated) are read with the path pushed down
        (`scan().where(...)`, finding-0169/bp-103; `limit(0)` is UNLIMITED, pinned by the shim
        ratchet); plane rows come from the cleared relations. NO `select()` projection: `vector`
        is a column callers come for."""
        out = [Row(clearance, r, mint=_MINT)
               for r in self._physical(clearance, f"source_path = {_sql_str(source_path)}")]
        out.extend(self._plane.reader(clearance).rows(source_path=source_path))
        return out

    def project(self, columns: Sequence[str], *, clearance: Clearance[Provenance],
                where: str | None = None, limit: int = 0) -> list[dict[str, Any]]:
        """A projected, predicate-pushed PHYSICAL read — the named columns and nothing else.

        It exists for one measurable reason: `vector` is many floats per row, so a scan that does
        not name it costs a small fraction of one that does (the code rebuild's baseline, the
        census). `limit(0)` means UNLIMITED (pinned by the shim ratchet).

        [banner: extension] A3: physical rows include the shared prose ATOMS, which carry no class
        — so this read is gated: under any clearance short of maintenance, only rows whose
        `provenance` the clearance admits come back (no atom ever does); `MAINTENANCE_READ` sees the
        whole physical table. `where` is the caller's raw predicate, ANDed after the gate; build it
        with `_sql_str` for any value this module did not write."""
        if TABLE not in self._db.list_tables().tables or not clearance.classes:
            return []
        clauses = [] if clearance.classes == _ALL_CLASSES else [_gate(clearance)]
        if where is not None:
            clauses.append(f"({where})")
        q = self._table().scan().select(list(columns))
        if clauses:
            q = q.where(" AND ".join(clauses))
        return [dict(r) for r in q.limit(limit).to_list()]

    def supersede_legacy_code_rows(self) -> int:
        """Flip every PRE-D1 duplicated code row to `current=false`, retaining it. Returns rows
        flipped (0 when the store holds none — so a second call is a no-op).

        The predicate is the exact complement of `is_code_atom_row` within the code lane: a row is
        legacy iff it is CODE and still carries the occupancy coordinates an atom row sheds. The
        rebuild lands the atom plane into the same table as the rows it replaces, so without this
        both models answer the default current-view search and the dedup is bought but not served.

        This is keep-and-link (`supersede_source`'s mechanism, D2) pointed at the retired ROW MODEL
        rather than at a superseded version: one pushed-down predicate, a filtered count, one
        in-place `update`. **Nothing is deleted** — `|V|` cannot decrease here, and D5's "purge is
        the ONE removal" is untouched — and because the rows remain, the step is reversible by the
        same update in the other direction."""
        if TABLE not in self._db.list_tables().tables:
            return 0
        table = self._table()
        where = (f"provenance = {_sql_str(Provenance.CODE.value)} "
                 "AND source_path <> '' AND current = true")
        flipped = table.count_rows(where)     # portable: do NOT rely on UpdateResult (bp-103 §11)
        if flipped:
            table.update(where, {"current": False})
        return flipped

    def delete_source(self, source_path: str) -> None:
        """A document is gone (a vault delete): drop its physical rows by `source_path` (pushed
        down, finding-0169) and retire its plane occupancies — superseded, history kept, a
        `head → ''` edge recorded (A3: keep-and-link for prose; the raw store stays sacred).
        Idempotent."""
        if TABLE in self._db.list_tables().tables and source_path:
            self._table().delete(f"source_path = {_sql_str(source_path)}")
        self._plane.retire(source_path)

    def supersede_source(self, source_path: str) -> int:
        """Keep-and-link (dn-temporal-code-corpus D2, bp-099): flip every CURRENTLY-current row of
        `source_path` to `current=false` while RETAINING it. Returns rows flipped (0 if none).

        ONE pushed-down predicate: a filtered `count_rows` for the return value, then a single
        in-place `update` — nothing materialized into Python, the cost a function of the matched
        rows (finding-0169, finding-0176). The count comes from `count_rows(where)`, never from
        `UpdateResult` (bp-103 §11). The predicate names `current`, so this raises on a pre-bp-099
        store rather than silently leaving two versions current (finding-0180).

        [banner: extension] A3: a prose path's occupancies are retired in the plane as well."""
        flipped = 0
        if TABLE in self._db.list_tables().tables:
            table = self._table()
            where = f"source_path = {_sql_str(source_path)} AND current = true"
            flipped = table.count_rows(where)   # portable: do NOT rely on UpdateResult (bp-103 §11)
            if flipped:
                table.update(where, {"current": False})
        return flipped + self._plane.retire(source_path)

    def relabel_provenance(self, old: str, new: str) -> int:
        """Rewrite every row's provenance from `old` to `new`. Returns rows relabeled.

        Used by the §1 spectrum-split migration (legacy `'authored'` → `'authored-solo'`): a
        SAME-TRUST-TIER relabel, not a promotion across the §8 firewall. Idempotent: a second run
        finds no `old` rows. Physical rows go delete-then-re-add (the store's re-index idiom); the
        plane moves the class's relation wholesale (A3: the one deliberate move between strata)."""
        if old == new:
            return 0
        moved = 0
        if TABLE in self._db.list_tables().tables:
            rows = [r for r in self._table().to_arrow().to_pylist() if r.get("provenance") == old]
            if rows:
                for r in rows:
                    r["provenance"] = new
                self._table().delete(f"provenance = {_sql_str(old)}")
                self.add(rows)
                moved = len(rows)
        try:
            src, dst = Provenance(old), Provenance(new)
        except ValueError:
            return moved
        if src is not Provenance.CODE and dst is not Provenance.CODE:
            moved += self._plane.relabel(src, dst)
        return moved

    def all_rows[L: Provenance](self, *, clearance: Clearance[L], include_atom_rows: bool = False,
                                include_superseded: bool = False) -> list[Row[L]]:
        """Every row `clearance` admits — the read the dreaming agent clusters over (the mirror
        passes `MIRROR_READ`, so observed exhaust never seeds a dream).

        [banner: extension] A3: the permission is a CAPABILITY now, not a free provenance set —
        every row comes back as a `Row[L]`, built by the sealed constructor that re-checks its
        class, and plane rows come only from the cleared relations. Prose atoms are never rows:
        their occupancies are. Superseded plane occupancies come back only on
        `include_superseded=True` (the physical rows keep their own `current` column as before).

        [banner: correction] **The shed-atom guard (bp-152 Item 3, the note's §3 Q5 gap).** A
        maintenance-wide read (the old unscoped `provenances=None`) excludes shed CODE-atom rows
        unless asked by name: every structural group-by-`digest` consumer keys on a column an atom
        row does not have, so shed rows (all `digest=''`) would collapse into ONE bogus SourceSet
        that `MixedProvenanceError` cannot catch. A read that admits CODE but not every class — the
        code lane's own read — gets the atoms, as `provenances={CODE}` always did."""
        code_atoms = clearance.admits(Provenance.CODE) and (
            include_atom_rows or clearance.classes != _ALL_CLASSES)
        out = [Row(clearance, r, mint=_MINT) for r in self._physical(clearance)
               if code_atoms or not is_code_atom_row(dict(r))]
        out.extend(self._plane.reader(clearance).rows(include_superseded=include_superseded))
        return out

    def has_digest(self, digest: str, *, clearance: Clearance[Provenance]) -> bool:
        """Does any row `clearance` admits come from this raw digest? A pushed-down count and an
        indexed plane lookup — never a scan of vectors."""
        where = f"{_gate(clearance)} AND digest = {_sql_str(digest)}"
        if (TABLE in self._db.list_tables().tables and clearance.classes
                and self._table().count_rows(where)):
            return True
        return self._plane.reader(clearance).has_digest(digest)

    def digests(self, *, clearance: Clearance[Provenance],
                include_superseded: bool = False) -> set[str]:
        """The raw digests of every document version `clearance` admits (current ones unless asked)
        — what an importer dedupes against without reading a vector."""
        out = {str(r["digest"]) for r in self._physical(clearance)}
        out |= {o.digest for o in self._plane.reader(clearance).occupancies(
            include_superseded=include_superseded)}
        return out

    def table_version(self) -> int:
        """The physical dataset's current version (0 before the table exists): a migration reads it
        before and after its work, and a change it did not make aborts the swap."""
        if TABLE not in self._db.list_tables().tables:
            return 0
        return self._table().version()

    def physical_pages(self, *, clearance: Clearance[Provenance], where: str | None = None,
                       page: int = 2000) -> Iterator[list[dict[str, Any]]]:
        """The physical table in pages of at most `page` rows, vectors included — bounded memory
        however large the store (the A3 migration copies a 148k-row store through it). Gated like
        `project`: short of maintenance, only rows whose class the clearance admits."""
        if TABLE not in self._db.list_tables().tables or not clearance.classes:
            return
        clauses = [] if clearance.classes == _ALL_CLASSES else [_gate(clearance)]
        if where is not None:
            clauses.append(f"({where})")
        offset = 0
        while True:
            q = self._table().scan()
            if clauses:
                q = q.where(" AND ".join(clauses))
            rows = [dict(r) for r in q.offset(offset).limit(page).to_list()]
            if rows:
                yield rows
            if len(rows) < page:
                return
            offset += page

    def _physical(self, clearance: Clearance[Provenance],
                  where: str | None = None) -> list[dict[str, object]]:
        """Physical RECORD rows whose class `clearance` admits, with `where` pushed down beside the
        gate. The gate applies even under maintenance: a classless prose atom, or a row still under
        a retired label, is not a record any clearance reads (`project` / `physical_pages` are the
        physical views)."""
        if TABLE not in self._db.list_tables().tables or not clearance.classes:
            return []
        clause = _gate(clearance) + (f" AND ({where})" if where else "")
        return self._table().scan().where(clause).limit(0).to_list()

    def atom_rows[L: Provenance](self, *, clearance: Clearance[L]) -> list[Row[L]]:
        """Every shed CODE-atom row (D1) — the code plane V, as rows. `len(atom_rows())` is |V| for
        the append-only invariant (§4). A code read: `clearance` must admit CODE."""
        if not clearance.admits(Provenance.CODE):
            raise ClearanceViolation(f"code atoms are not readable under {clearance!r}")
        return [Row(clearance, r, mint=_MINT) for r in self._physical(
            clearance, "source_path = '' AND digest = ''") if is_code_atom_row(dict(r))]

    def atom_row_count(self) -> int:
        """`|V|` — how many shed CODE-atom rows the plane holds, as a SERVER-SIDE count.

        The same number `len(atom_rows())` gives, without the scan: `atom_rows` materializes every
        row INCLUDING its 2560-float vector, which is the right cost for the repair pass (it reads
        the flag on each row) and entirely the wrong cost for a gauge that runs on a cadence. The
        predicate is `is_code_atom_row` written as SQL — the one place those two spellings must
        agree, which is why the Python predicate is the documented reading and this cites it."""
        if TABLE not in self._db.list_tables().tables:
            return 0
        return self._table().count_rows(
            f"provenance = {_sql_str(Provenance.CODE.value)} "
            "AND source_path = '' AND digest = ''")

    def set_current_any(self, ids: Iterable[str], value: bool) -> int:
        """Set `current_any` on exactly the named atom rows (D2 step 5). Returns rows written.

        `current` is a lance column, so a flip rewrites fragments — which is why D2 step 5 and the
        note's §3 pin say *only the atoms whose current-membership count crossed 0↔1*. This method
        takes the crossing set and nothing else; computing it is the lander's job (it is pure
        membership arithmetic and belongs in SQLite, not here). An empty set writes nothing.

        Predicates are chunked so a large crossing set cannot build an unbounded SQL string."""
        wanted = list(dict.fromkeys(ids))
        if not wanted or TABLE not in self._db.list_tables().tables:
            return 0
        table = self._table()
        written = 0
        for start in range(0, len(wanted), _ID_PREDICATE_CHUNK):
            batch = wanted[start:start + _ID_PREDICATE_CHUNK]
            where = f"id IN ({', '.join(_sql_str(i) for i in batch)})"
            # portable count (do NOT rely on UpdateResult — bp-103 §11), then one in-place update
            n = table.count_rows(where)
            if n:
                table.update(where, {"current": value})
                written += n
        return written

    def delete_atom(self, content_id: str) -> int:
        """Delete one atom row by its `(layer, content_hash)` id — the D5 PURGE path, and the ONLY
        machinery in this module that removes a vector row (finding-0164; owner-gated, privacy
        outranks lineage). Returns rows deleted, so a purge that silently no-ops is observable:
        "never deletes" is satisfied vacuously by a purge that does nothing, so the count is the
        thing a test asserts on. The membership half of the hole (tombstoning) is the membership
        store's — see `core.stores.memberships.purge_atom`, which owns both halves."""
        if TABLE not in self._db.list_tables().tables:
            return 0
        table = self._table()
        where = f"id = {_sql_str(content_id)}"
        n = table.count_rows(where)
        if n:
            table.delete(where)
        return n

    def dataset_versions(self) -> int:
        """How many dataset versions the table still retains (§3). One per write batch, and D2 makes
        `current_any` flips routine — so this is the number compaction is measured against."""
        if TABLE not in self._db.list_tables().tables:
            return 0
        return len(self._table().list_versions())

    def compact(self, *, older_than: timedelta | None = None) -> CompactionReport:
        """Physical maintenance: compact fragments, then drop old dataset versions (§3).

        [cross-ref: extension] No compaction path existed in this module (the note verified it), and
        §3 makes it part of the store's semantics rather than an operational afterthought: the lance
        dataset accumulates a version per write batch — 298 versions / 245 MB measured 2026-07-27
        against ~232 MB of raw payload — and `current_any` flips are updates that rewrite fragments.
        The rebuild ends with this, and housekeeping runs the cleanup half on cadence.

        **Compaction is PHYSICAL, never logical.** It removes no row and changes no vector, so row
        count and search results are invariant across it — the acceptance asserts BOTH, because
        "nothing changed" is also what a compaction that silently did nothing produces. The version
        count dropping is the other half, and it is the half that makes the assertion non-vacuous.

        `older_than=None` takes the package's own retention default. Passing `timedelta(0)` reclaims
        every superseded version immediately, which is what the rebuild wants (it has just written
        thousands of batches) and what a test needs to observe a drop at all — but it forfeits
        time-travel to any earlier version, so it is the caller's explicit choice, never the
        default. `current_any` stays in lance throughout: the ANN prefilter needs it (D1/§3)."""
        if TABLE not in self._db.list_tables().tables:
            return CompactionReport()
        table = self._table()
        before_rows, before_versions = table.count_rows(None), len(table.list_versions())
        # ONE call does both halves. The deprecated `compact_files`/`cleanup_old_versions` pair
        # routes through `Table.to_lance()` and raises ImportError without the optional `pylance`
        # package (found by running it, not by reading about it) — see the shim's note.
        table.optimize(cleanup_older_than=older_than, delete_unverified=False)
        after_rows, after_versions = table.count_rows(None), len(table.list_versions())
        return CompactionReport(
            rows_before=before_rows, rows_after=after_rows,
            versions_before=before_versions, versions_after=after_versions,
        )

    def search[L: Provenance](self, vector: list[float], *, k: int = 5, clearance: Clearance[L],
                              include_superseded: bool = False) -> list[Row[L]]:
        """The k nearest rows `clearance` admits.

        Default retrieval is CURRENT-VIEW (dn-temporal-code-corpus D3, bp-099): a superseded
        version never surfaces unasked; `include_superseded=True` opts into history. Physical rows
        (code atoms read as `current_any`, D1) are searched with their class pushed down as a
        PREFILTER, so the k nearest are taken from the permitted set, not after.

        [banner: extension] A3: prose comes from the shared plane — the k nearest atoms that a
        CLEARED relation holds, one row per cleared occupancy — and the two lists merge by
        distance. Resolving a code hit to its occupancies `(path, blob, slot, lines)` remains the
        membership join (D3, `core.stores.memberships.resolve_occupancies`)."""
        out: list[Row[L]] = []
        if TABLE in self._db.list_tables().tables and clearance.classes:
            clause = _gate(clearance) + ("" if include_superseded else " AND current = true")
            q = self._table().search(vector).metric("cosine").where(clause, prefilter=True)
            out = [Row(clearance, r, mint=_MINT) for r in q.limit(k).to_list()]
        if self.plane_enabled():
            out.extend(self._plane.reader(clearance).search_rows(
                vector, k=k, include_superseded=include_superseded))
        out.sort(key=lambda r: float(r.get("_distance", 0.0)))
        return out[:k]


_BATCH = 400


def _batched(items: Sequence[str]) -> Iterable[Sequence[str]]:
    for i in range(0, len(items), _BATCH):
        yield items[i:i + _BATCH]


@dataclass
class _LanceAtoms:
    """The plane's `AtomTable` over this store's one LanceDB table (A3). Plain data in and out;
    which rows a reader may receive is decided by the plane's cleared relations, never here."""

    store: VectorStore

    def _exists(self) -> bool:
        return TABLE in self.store._db.list_tables().tables

    def _scan(self, where: str, columns: list[str]) -> list[dict[str, object]]:
        if not self._exists():
            return []
        return self.store._table().scan().select(columns).where(where).limit(0).to_list()

    def present(self, atom_ids: Sequence[str]) -> set[str]:
        out: set[str] = set()
        for batch in _batched(list(atom_ids)):
            out |= {str(r["id"]) for r in self._scan(f"{_id_in(batch)} AND {_PROSE_ATOM}", ["id"])}
        return out

    def insert(self, atoms: Sequence[AtomRecord]) -> int:
        rows = [{"id": a.atom_id, "digest": "", "title": "", "source_path": "", "chunk_index": 0,
                 "provenance": "", "text": a.text, "layer": a.layer, "qualname": "",
                 "line_start": 0, "line_end": 0, "current": False, "held": [], "held_ever": [],
                 "vector": list(a.vector)} for a in atoms]
        if not rows:
            return 0
        for r in rows:
            if len(cast(list[float], r["vector"])) != self.store.dim:
                raise ValueError(f"atom vector dim != configured {self.store.dim}")
        self.store._table().add(rows)
        return len(rows)

    def payload(self, atom_ids: Sequence[str]) -> dict[str, tuple[str, Sequence[float]]]:
        out: dict[str, tuple[str, Sequence[float]]] = {}
        for batch in _batched(list(atom_ids)):
            for r in self._scan(f"{_id_in(batch)} AND {_PROSE_ATOM}", ["id", "text", "vector"]):
                out[str(r["id"])] = (str(r["text"]), cast(list[float], r["vector"]))
        return out

    def nearest(self, vector: Sequence[float], *, classes: Sequence[str], superseded: bool,
                limit: int) -> list[Candidate]:
        if not self._exists() or not classes:
            return []
        col = "held_ever" if superseded else "held"
        pred = f"array_has_any({col}, [{', '.join(_sql_str(c) for c in classes)}])"
        rows = (self.store._table().search(list(vector)).metric("cosine")
                .where(pred, prefilter=True).select(["id", "text", "vector", "_distance"])
                .limit(limit)
                .to_list())
        return [Candidate(atom_id=str(r["id"]), text=str(r["text"]),
                          vector=cast(list[float], r["vector"]),
                          distance=float(cast(float, r["_distance"]))) for r in rows]

    def held(self, atom_ids: Sequence[str]) -> dict[str, tuple[frozenset[str], frozenset[str]]]:
        out: dict[str, tuple[frozenset[str], frozenset[str]]] = {}
        for batch in _batched(list(atom_ids)):
            for r in self._scan(f"{_id_in(batch)} AND {_PROSE_ATOM}",
                                ["id", "held", "held_ever"]):
                out[str(r["id"])] = (frozenset(cast(list[str] | None, r["held"]) or ()),
                                     frozenset(cast(list[str] | None, r["held_ever"]) or ()))
        return out

    def set_held(self, updates: Mapping[str, tuple[frozenset[str], frozenset[str]]]) -> int:
        groups: dict[tuple[tuple[str, ...], tuple[str, ...]], list[str]] = defaultdict(list)
        for a, (h, e) in updates.items():
            groups[(tuple(sorted(h)), tuple(sorted(e)))].append(a)
        written = 0
        for (held, ever), ids in groups.items():
            for batch in _batched(ids):
                self.store._table().update(f"{_id_in(batch)} AND {_PROSE_ATOM}", values_sql={
                    "held": _sql_list(held), "held_ever": _sql_list(ever),
                    "current": "true" if held else "false"})
                written += len(batch)
        return written

    def delete(self, atom_ids: Sequence[str]) -> int:
        deleted = 0
        for batch in _batched(list(atom_ids)):
            where = f"{_id_in(batch)} AND {_PROSE_ATOM}"
            n = self.store._table().count_rows(where) if self._exists() else 0
            if n:
                self.store._table().delete(where)
                deleted += n
        return deleted

    def ids(self) -> set[str]:
        return {str(r["id"]) for r in self._scan(_PROSE_ATOM, ["id"])}


def fingerprint_of(config: Config) -> Fingerprint:
    """The configured embedder geometry: model, document template, dimension (A3)."""
    e = config.embedding
    return Fingerprint(model=e.model, template=e.document_template, dim=e.dim)


def open_vector_store(config: Config | None = None) -> VectorStore:
    from core.kernel.config import get_config

    cfg = config or get_config()
    return VectorStore(path=cfg.paths.vector_store, dim=cfg.embedding.dim,
                       embedder=fingerprint_of(cfg))
