# ── Family 1 boundary (labelings & information-flow) + Family 2 (regenerable derivation) ──
# OBJECT:    the shared prose plane — atoms V (one row per distinct chunk text, one geometry per
#            plane) and the occupancy relation partitioned by provenance class, M = ⊔_c M_c, with a
#            per-class supersession log (dn-vector-membership-store Amendment A3).
# INVARIANT: a read under clearance C touches only M_C: its SQL names only `occ_<c>`/`sup_<c>` for
#            c ∈ C, and every record it returns is minted through core.kernel.clearance's sealed
#            constructors. Noninterference (A3.5): mutating M_c for c ∉ C changes no C-read. The
#            ANN prefilter columns (`held`, `held_ever`) are a CACHE — stale, they can only drop
#            results, never widen them, because hits are built from the cleared relations alone.
# ENFORCED:  structural (per-class relations, sealed records, the clearance-derived table list) +
#            property (tests/property/test_plane_noninterference.py) + the R3 repair ratchet.
"""The shared plane: every prose stratum's chunks, stored once, read only through a clearance.

The owner's direction (2026-10-29), in their words: documents that share chunks "have pointers to
those vectors in common", an edit creates "a supersession edge from the doc … to the updated doc
with the new vector reference set", and the whole thing must not leak — "accessible records without
the correct permission should be unrepresentable".

**What is stored where.**

* An **atom** is one distinct chunk text under one embedder: `"{layer}:{sha256(text)}"` →
  `(text, vector)`, a row in the shared LanceDB table that carries NO provenance and no occupancy.
  Notes, chat turns, model replies and (in their own plane) papers point at it.
* An **occupancy** says "document `source_path`, at version `digest`, holds that atom at
  `chunk_index`". Occupancies live in one SQLite relation PER PROVENANCE CLASS (`occ_<class>`), so
  a record's class is the table it lives in, not a column some query must remember to filter.
* A **version** is a fiber `(source_path, digest)`. Landing a fiber makes it the path's current
  version and supersedes the path's others (D2 step 4 — reconcile on every land, never
  short-circuit), and each change of a path's head appends to `sup_<class>`: the supersession edge,
  keyed by position (`seq`), so A → B → A is two edges, not a cycle collapsed into none (C1).

**Reading.** `plane.reader(clearance)` returns a `PlaneReader[L]` whose table list is computed
from the clearance and nothing else; it mints `Occupancy[L]`, `PlaneHit[L]` and `Row[L]` through
the kernel's sealed constructors, which re-check every class. Search asks LanceDB for nearest atoms
whose `held` cache names a cleared class (the prefilter, a speed device), then keeps only atoms
that a cleared relation actually holds (the boundary).

**Writing** is serialized across processes by an advisory file lock beside the database, in the
D8 order: atoms first (an unreferenced atom is dormant geometry), occupancies second (one SQLite
transaction), the `held` cache last (re-derivable; `repair()` rebuilds it). A purge deletes the
atoms it frees BEFORE their occupancies, so a crash mid-purge never leaves private text behind.

Patterns, named for whoever reads this later: content-addressed storage (Git's model at chunk
grain); a partitioned relation as an object-capability boundary; a derived prefilter cache with a
repair ratchet (fail-closed under staleness); an append-only, position-keyed supersession log;
advisory locking for cross-process single-writer.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import sqlite3
import threading
import time
from collections import defaultdict
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

from core.kernel.clearance import _MINT, Clearance, Occupancy, PlaneHit, Row
from core.kernel.provenance import Provenance

PLANE_FILE = "plane.sqlite"
LOCK_FILE = "plane.lock"
SCHEMA_VERSION = 1
LOCK_TIMEOUT_S = 60.0
_BATCH = 400                     # ids per `IN (…)` — bounds SQL size, never semantics

#: The classes the plane holds. CODE is not one of them: code atoms keep D0's identity and the code
#: lane's own membership store — a disjoint identity space, since their embed texts carry a path
#: header no prose chunk has (A3.3).
PLANE_CLASSES: tuple[Provenance, ...] = tuple(p for p in Provenance if p is not Provenance.CODE)


def _table_suffix(p: Provenance) -> str:
    name = p.value.replace("-", "_")
    if not (name.isascii() and name.isidentifier()):
        raise ValueError(f"provenance {p.value!r} cannot name a relation")
    return name


#: Relation names, generated once from the enum — never from input.
OCC: Mapping[Provenance, str] = {p: f"occ_{_table_suffix(p)}" for p in PLANE_CLASSES}
SUP: Mapping[Provenance, str] = {p: f"sup_{_table_suffix(p)}" for p in PLANE_CLASSES}


def atom_id(text: str, layer: str = "prose") -> str:
    """The atom's identity: its layer and the SHA-256 of its text (`Chunk.content_hash`)."""
    return f"{layer}:{hashlib.sha256(text.encode('utf-8')).hexdigest()}"


def _now() -> str:
    return datetime.now(UTC).replace(tzinfo=None).isoformat(timespec="seconds")


def _batches(items: Sequence[str]) -> Iterator[Sequence[str]]:
    for i in range(0, len(items), _BATCH):
        yield items[i:i + _BATCH]


class PlaneError(RuntimeError):
    """A plane operation that would corrupt the plane was refused."""


class StratumConflict(PlaneError):
    """A path already lives in another class's relation: a source lives at one stratum (A3.6).
    Moving it is a deliberate `relabel`, never a side effect of landing."""


class GeometryMismatch(PlaneError):
    """The configured embedder differs from the one the plane's vectors came from. Mixing two
    geometries in one ANN space is a corruption nothing downstream can detect, so landing and
    searching refuse until the plane is rebuilt (`palace reembed --confirm`)."""


class MissingVector(PlaneError):
    """A row named an atom the plane does not hold and brought no vector to create it."""


@dataclass(frozen=True)
class Fingerprint:
    """The embedder geometry: model, document template and dimension. The template is part of it
    because it changes the vector; `query_instruction` is not (it conditions queries only)."""

    model: str
    template: str
    dim: int

    def as_json(self) -> str:
        return json.dumps({"model": self.model, "template": self.template, "dim": self.dim},
                          sort_keys=True)


@dataclass(frozen=True)
class AtomRecord:
    """An atom as the shared table stores it: identity, layer, text and vector."""

    atom_id: str
    layer: str
    text: str
    vector: Sequence[float]


@dataclass(frozen=True)
class Candidate:
    """A nearest-atom candidate from the ANN search, before the cleared join decides."""

    atom_id: str
    text: str
    vector: Sequence[float]
    distance: float


class AtomTable(Protocol):
    """The shared atom table the plane writes and searches — the vector store's LanceDB table in
    production, an in-memory table in the property tests. Every method takes and returns plain
    data; the boundary (what a reader may see) is the plane's, never the table's."""

    def present(self, atom_ids: Sequence[str]) -> set[str]: ...

    def insert(self, atoms: Sequence[AtomRecord]) -> int: ...

    def payload(self, atom_ids: Sequence[str]) -> dict[str, tuple[str, Sequence[float]]]: ...

    def nearest(self, vector: Sequence[float], *, classes: Sequence[str], superseded: bool,
                limit: int) -> list[Candidate]: ...

    def held(self, atom_ids: Sequence[str]) -> dict[str, tuple[frozenset[str], frozenset[str]]]:
        ...

    def set_held(self, updates: Mapping[str, tuple[frozenset[str], frozenset[str]]]) -> int: ...

    def delete(self, atom_ids: Sequence[str]) -> int: ...

    def ids(self) -> set[str]: ...


@dataclass(frozen=True)
class LandReport:
    atoms_inserted: int = 0
    atoms_reused: int = 0
    fibers_written: int = 0
    made_current: int = 0
    superseded: int = 0


@dataclass(frozen=True)
class PurgeReport:
    """What a purge removed. All three are counted so a purge that did nothing is visible."""

    occupancies_deleted: int = 0
    atoms_deleted: int = 0
    supersessions_deleted: int = 0


@dataclass(frozen=True)
class RepairReport:
    held_fixed: int = 0
    orphan_atoms: int = 0
    dangling_occupancies: int = 0


@dataclass(frozen=True)
class ClassGauge:
    """One class's frequency-plane reading (D6), taken in one scan so |M| and |V| share a cut."""

    occupancies: int = 0           # |M_c|, current
    atoms: int = 0                 # distinct atoms the class currently holds
    documents: int = 0             # distinct current paths

    @property
    def dedup_factor(self) -> float:
        return self.occupancies / self.atoms if self.atoms else 0.0

    @property
    def embeds_avoided(self) -> int:
        return max(0, self.occupancies - self.atoms)


@dataclass(frozen=True)
class _Fiber:
    source_path: str
    digest: str
    provenance: Provenance
    title: str
    chunks: tuple[tuple[int, str, str], ...]     # (chunk_index, atom_id, row_id), chunk order


def _ddl() -> str:
    parts = ["CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);"]
    for p in PLANE_CLASSES:
        occ, sup = OCC[p], SUP[p]
        parts.append(f"""
CREATE TABLE IF NOT EXISTS {occ} (
    source_path TEXT NOT NULL,
    digest      TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    atom_id     TEXT NOT NULL,
    row_id      TEXT NOT NULL,      -- the id its writer gave the row (kept, never re-derived)
    title       TEXT NOT NULL,
    current     INTEGER NOT NULL DEFAULT 0,
    landed_at   TEXT NOT NULL,
    PRIMARY KEY (source_path, digest, chunk_index)
);
CREATE INDEX IF NOT EXISTS {occ}_atom ON {occ}(atom_id, current);
CREATE INDEX IF NOT EXISTS {occ}_digest ON {occ}(digest);
CREATE INDEX IF NOT EXISTS {occ}_head ON {occ}(source_path, current);
CREATE TABLE IF NOT EXISTS {sup} (
    source_path TEXT NOT NULL,
    seq         INTEGER NOT NULL,
    old_digest  TEXT NOT NULL,
    new_digest  TEXT NOT NULL,
    at          TEXT NOT NULL,
    PRIMARY KEY (source_path, seq)
);""")
    return "\n".join(parts)


@dataclass
class SharedPlane:
    """The plane over one directory (the vector store's own) and one atom table.

    `fingerprint=None` means "unknown embedder" (unit tests): nothing is recorded or checked. The
    live stores always pass the configured one (`open_vector_store`, `open_curated_store`)."""

    directory: Path
    atoms: AtomTable
    fingerprint: Fingerprint | None = None
    _conn: sqlite3.Connection | None = field(default=None, init=False, repr=False)
    _lock: threading.RLock = field(default_factory=threading.RLock, init=False, repr=False)

    # ── plumbing ─────────────────────────────────────────────────────────────────────────────

    def _db(self) -> sqlite3.Connection:
        with self._lock:
            if self._conn is None:
                self.directory.mkdir(parents=True, exist_ok=True)
                conn = sqlite3.connect(self.directory / PLANE_FILE, timeout=30.0,
                                       check_same_thread=False, isolation_level=None)
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA busy_timeout=30000")
                conn.executescript(_ddl())
                conn.execute("INSERT OR IGNORE INTO meta (key, value) VALUES ('schema', ?)",
                             [str(SCHEMA_VERSION)])
                self._conn = conn
            return self._conn

    @contextmanager
    def _writing(self) -> Iterator[sqlite3.Connection]:
        """One writer at a time across processes (advisory `flock` beside the database), and one
        SQLite transaction inside it."""
        with self._lock:
            self.directory.mkdir(parents=True, exist_ok=True)
            with (self.directory / LOCK_FILE).open("a") as lockf:
                deadline = time.monotonic() + LOCK_TIMEOUT_S
                while True:
                    try:
                        fcntl.flock(lockf, fcntl.LOCK_EX | fcntl.LOCK_NB)
                        break
                    except BlockingIOError:
                        if time.monotonic() > deadline:
                            raise PlaneError(f"another process holds {LOCK_FILE} for over "
                                             f"{LOCK_TIMEOUT_S:.0f} s") from None
                        time.sleep(0.05)
                try:
                    yield self._db()
                finally:
                    fcntl.flock(lockf, fcntl.LOCK_UN)

    def close(self) -> None:
        with self._lock:
            if self._conn is not None:
                self._conn.close()
                self._conn = None

    def _check_geometry(self, conn: sqlite3.Connection, *, record: bool) -> None:
        if self.fingerprint is None:
            return
        row = conn.execute("SELECT value FROM meta WHERE key = 'fingerprint'").fetchone()
        mine = self.fingerprint.as_json()
        if row is None:
            if record:
                conn.execute("INSERT OR IGNORE INTO meta (key, value) VALUES ('fingerprint', ?)",
                             [mine])
            return
        if row[0] != mine:
            raise GeometryMismatch(f"the plane's vectors came from {row[0]}; the configured "
                                   f"embedder is {mine}. Re-embed: palace reembed --confirm")

    def check_geometry(self) -> None:
        """Raise `GeometryMismatch` if the configured embedder cannot search this plane."""
        self._check_geometry(self._db(), record=False)

    # ── the trusted write path ───────────────────────────────────────────────────────────────

    def known(self, atom_ids: Sequence[str]) -> set[str]:
        """Which of these atoms the plane already holds — the embeds a caller may skip. The atom
        table is authoritative (no second ledger to drift)."""
        self._check_geometry(self._db(), record=False)
        return self.atoms.present(list(dict.fromkeys(atom_ids)))

    def class_of(self, source_path: str) -> Provenance | None:
        """The one class whose relation holds this path, if any (a write-path lookup)."""
        conn = self._db()
        for p in PLANE_CLASSES:
            if conn.execute(f"SELECT 1 FROM {OCC[p]} WHERE source_path = ? LIMIT 1",
                            [source_path]).fetchone():
                return p
        return None

    def land(self, rows: Sequence[Mapping[str, Any]]) -> LandReport:
        """Land document versions (D2, generalized): insert the atoms the plane lacks, write each
        fiber, make it its path's current version, append the supersession edge when the head
        changed, then bring the `held` cache in step. Idempotent by reconciliation."""
        fibers, vectors = _fibers(rows)
        if not fibers:
            return LandReport()
        wanted = list(dict.fromkeys(a for f in fibers for _, a, _ in f.chunks))
        with self._writing() as conn:
            self._check_geometry(conn, record=True)
            present = self.atoms.present(wanted)
            missing = [a for a in wanted if a not in present]
            lacking = [a for a in missing if a not in vectors]
            if lacking:
                raise MissingVector(f"{len(lacking)} new atom(s) arrived without a vector, e.g. "
                                    f"{lacking[0][:24]}")
            self.atoms.insert([vectors[a] for a in missing])                  # D8: atoms first
            made = superseded = 0
            affected: set[str] = set(wanted)
            conn.execute("BEGIN IMMEDIATE")
            try:
                for f in fibers:
                    m, s, freed = self._write_fiber(conn, f)
                    made, superseded = made + m, superseded + s
                    affected |= freed
                conn.execute("COMMIT")
            except BaseException:
                conn.execute("ROLLBACK")
                raise
            self._refresh_held(conn, sorted(affected))                        # D8: cache last
        return LandReport(atoms_inserted=len(missing), atoms_reused=len(wanted) - len(missing),
                          fibers_written=len(fibers), made_current=made, superseded=superseded)

    def _write_fiber(self, conn: sqlite3.Connection, f: _Fiber) -> tuple[int, int, set[str]]:
        owner = self.class_of(f.source_path)
        if owner is not None and owner is not f.provenance:
            raise StratumConflict(f"{f.source_path!r} lives in {owner.value}; landing it as "
                                  f"{f.provenance.value} would put one source at two strata")
        occ, sup = OCC[f.provenance], SUP[f.provenance]
        # The head BEFORE this land decides whether an edge is owed — read it before any write, so
        # re-landing the current version under a changed derivation is not mistaken for a new head.
        heads = sorted(str(r[0]) for r in conn.execute(
            f"SELECT DISTINCT digest FROM {occ} WHERE source_path = ? AND current = 1",
            [f.source_path]))
        if len(heads) > 1:
            raise PlaneError(f"{f.source_path!r} has {len(heads)} current versions; run repair")
        freed = {str(r[0]) for r in conn.execute(
            f"SELECT atom_id FROM {occ} WHERE source_path = ? AND current = 1 AND digest <> ?",
            [f.source_path, f.digest])}
        existing = {(int(r[0]), str(r[1]), str(r[2])) for r in conn.execute(
            f"SELECT chunk_index, atom_id, row_id FROM {occ} WHERE source_path = ? AND digest = ?",
            [f.source_path, f.digest])}
        if existing != set(f.chunks):              # new version, or its derivation changed
            freed |= {a for _, a, _ in existing}   # atoms the old derivation held may lose a class
            was_head = heads == [f.digest]
            conn.execute(f"DELETE FROM {occ} WHERE source_path = ? AND digest = ?",
                         [f.source_path, f.digest])
            now = _now()
            conn.executemany(
                f"INSERT INTO {occ} (source_path, digest, chunk_index, atom_id, row_id, title, "
                "current, landed_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                [(f.source_path, f.digest, i, a, rid, f.title, int(was_head), now)
                 for i, a, rid in f.chunks])
        superseded = conn.execute(
            f"UPDATE {occ} SET current = 0 WHERE source_path = ? AND digest <> ? AND current = 1",
            [f.source_path, f.digest]).rowcount
        made = conn.execute(
            f"UPDATE {occ} SET current = 1 WHERE source_path = ? AND digest = ? AND current = 0",
            [f.source_path, f.digest]).rowcount
        if heads != [f.digest]:
            self._append_edge(conn, sup, f.source_path, heads[0] if heads else "", f.digest)
        return made, superseded, freed

    @staticmethod
    def _append_edge(conn: sqlite3.Connection, sup: str, path: str, old: str, new: str) -> None:
        row = conn.execute(f"SELECT COALESCE(MAX(seq), 0) FROM {sup} WHERE source_path = ?",
                           [path]).fetchone()
        conn.execute(f"INSERT INTO {sup} (source_path, seq, old_digest, new_digest, at) "
                     "VALUES (?, ?, ?, ?, ?)", [path, int(row[0]) + 1, old, new, _now()])

    def retire(self, source_path: str) -> int:
        """The path is gone (a vault delete): its current version stops being current, its history
        stays, and a `head → ''` edge records the retirement. Returns occupancies retired."""
        with self._writing() as conn:
            p = self.class_of(source_path)
            if p is None:
                return 0
            occ = OCC[p]
            heads = [str(r[0]) for r in conn.execute(
                f"SELECT DISTINCT digest FROM {occ} WHERE source_path = ? AND current = 1",
                [source_path])]
            if not heads:
                return 0
            affected = [str(r[0]) for r in conn.execute(
                f"SELECT DISTINCT atom_id FROM {occ} WHERE source_path = ? AND current = 1",
                [source_path])]
            conn.execute("BEGIN IMMEDIATE")
            try:
                n = conn.execute(f"UPDATE {occ} SET current = 0 WHERE source_path = ? "
                                 "AND current = 1", [source_path]).rowcount
                for h in sorted(heads):
                    self._append_edge(conn, SUP[p], source_path, h, "")
                conn.execute("COMMIT")
            except BaseException:
                conn.execute("ROLLBACK")
                raise
            self._refresh_held(conn, affected)
            return int(n)

    def purge(self, digest: str) -> PurgeReport:
        """Privacy outranks lineage (A3.7): every occupancy of this digest, in every relation, and
        its supersession entries go; so do the atoms nothing else holds — and those atoms go
        FIRST, so a crash mid-purge leaves an occupancy pointing at nothing (repaired by re-running
        the purge), never private text with nothing pointing at it."""
        with self._writing() as conn:
            held_by_digest: set[str] = set()
            for p in PLANE_CLASSES:
                held_by_digest |= {str(r[0]) for r in conn.execute(
                    f"SELECT DISTINCT atom_id FROM {OCC[p]} WHERE digest = ?", [digest])}
            ids = sorted(held_by_digest)
            still_held: set[str] = set()
            for batch in _batches(ids):
                marks = ", ".join("?" for _ in batch)
                for p in PLANE_CLASSES:
                    still_held |= {str(r[0]) for r in conn.execute(
                        f"SELECT DISTINCT atom_id FROM {OCC[p]} WHERE atom_id IN ({marks}) "
                        "AND digest <> ?", [*batch, digest])}
            freed = [a for a in ids if a not in still_held]
            deleted_atoms = self.atoms.delete(freed) if freed else 0          # private text first
            occ_n = sup_n = 0
            conn.execute("BEGIN IMMEDIATE")
            try:
                for p in PLANE_CLASSES:
                    occ_n += conn.execute(f"DELETE FROM {OCC[p]} WHERE digest = ?",
                                          [digest]).rowcount
                    sup_n += conn.execute(f"DELETE FROM {SUP[p]} WHERE old_digest = ? "
                                          "OR new_digest = ?", [digest, digest]).rowcount
                conn.execute("COMMIT")
            except BaseException:
                conn.execute("ROLLBACK")
                raise
            self._refresh_held(conn, sorted(still_held))
            return PurgeReport(occupancies_deleted=occ_n, atoms_deleted=deleted_atoms,
                               supersessions_deleted=sup_n)

    def relabel(self, old: Provenance, new: Provenance) -> int:
        """Move every document of class `old` to class `new` — the one deliberate move between
        strata (a same-tier relabel such as authored → authored-solo, or an owner promotion).
        Returns occupancies moved."""
        if old is new:
            return 0
        if old not in OCC or new not in OCC:
            raise PlaneError("CODE has no relation in the prose plane")
        with self._writing() as conn:
            affected = [str(r[0]) for r in conn.execute(
                f"SELECT DISTINCT atom_id FROM {OCC[old]}")]
            conn.execute("BEGIN IMMEDIATE")
            try:
                clash = conn.execute(
                    f"SELECT 1 FROM {OCC[old]} o JOIN {OCC[new]} n "
                    "ON o.source_path = n.source_path LIMIT 1").fetchone()
                if clash:
                    raise StratumConflict(f"a path exists in both {old.value} and {new.value}")
                n = conn.execute(f"INSERT INTO {OCC[new]} SELECT * FROM {OCC[old]}").rowcount
                conn.execute(f"INSERT INTO {SUP[new]} SELECT * FROM {SUP[old]}")
                conn.execute(f"DELETE FROM {OCC[old]}")
                conn.execute(f"DELETE FROM {SUP[old]}")
                conn.execute("COMMIT")
            except BaseException:
                conn.execute("ROLLBACK")
                raise
            self._refresh_held(conn, affected)
            return int(n)

    def reset(self) -> None:
        """Forget every occupancy, edge and the recorded geometry (the vector store's `reset`
        drops the atoms with its table). Vectors are derived (§8): a re-ingest rebuilds both."""
        with self._writing() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                for p in PLANE_CLASSES:
                    conn.execute(f"DELETE FROM {OCC[p]}")
                    conn.execute(f"DELETE FROM {SUP[p]}")
                conn.execute("DELETE FROM meta WHERE key = 'fingerprint'")
                conn.execute("COMMIT")
            except BaseException:
                conn.execute("ROLLBACK")
                raise

    # ── the `held` cache (the prefilter) and its repair ratchet ──────────────────────────────

    def _held_truth(self, conn: sqlite3.Connection,
                    ids: Sequence[str]) -> dict[str, tuple[frozenset[str], frozenset[str]]]:
        held: dict[str, set[str]] = defaultdict(set)
        ever: dict[str, set[str]] = defaultdict(set)
        for batch in _batches(list(ids)):
            marks = ", ".join("?" for _ in batch)
            for p in PLANE_CLASSES:
                for a, cur in conn.execute(
                        f"SELECT atom_id, MAX(current) FROM {OCC[p]} WHERE atom_id IN ({marks}) "
                        "GROUP BY atom_id", list(batch)):
                    ever[str(a)].add(p.value)
                    if int(cur):
                        held[str(a)].add(p.value)
        return {a: (frozenset(held.get(a, ())), frozenset(ever.get(a, ()))) for a in ids}

    def _refresh_held(self, conn: sqlite3.Connection, ids: Sequence[str]) -> int:
        if not ids:
            return 0
        truth = self._held_truth(conn, ids)
        cached = self.atoms.held(list(ids))
        changed = {a: truth[a] for a in cached if cached[a] != truth[a]}
        return self.atoms.set_held(changed) if changed else 0

    def repair(self) -> RepairReport:
        """R3, the ratchet: rebuild the `held` cache from the relations, and count orphan atoms
        (no occupancy — dormant geometry from a crashed land) and dangling occupancies (an atom
        that is gone — an interrupted purge; re-running the purge finishes it)."""
        with self._writing() as conn:
            on_table = self.atoms.ids()
            referenced: set[str] = set()
            for p in PLANE_CLASSES:
                referenced |= {str(r[0]) for r in conn.execute(
                    f"SELECT DISTINCT atom_id FROM {OCC[p]}")}
            fixed = self._refresh_held(conn, sorted(on_table))
            return RepairReport(held_fixed=fixed, orphan_atoms=len(on_table - referenced),
                                dangling_occupancies=len(referenced - on_table))

    def held_drift(self) -> list[str]:
        """Atoms whose cached `held`/`held_ever` disagree with the relations (empty ⇒ in step)."""
        conn = self._db()
        ids = sorted(self.atoms.ids())
        truth = self._held_truth(conn, ids)
        cached = self.atoms.held(ids)
        return sorted(a for a in ids if cached.get(a) != truth[a])

    # ── reading ──────────────────────────────────────────────────────────────────────────────

    def reader[L: Provenance](self, clearance: Clearance[L]) -> PlaneReader[L]:
        return PlaneReader(self, clearance)


def _fibers(rows: Sequence[Mapping[str, Any]]) -> tuple[list[_Fiber], dict[str, AtomRecord]]:
    """Group landing rows into fibers, validating what a fiber must be: one class (a plane class),
    one title, distinct chunk positions."""
    grouped: dict[tuple[str, str], list[Mapping[str, Any]]] = {}
    for r in rows:
        grouped.setdefault((str(r["source_path"]), str(r["digest"])), []).append(r)
    fibers: list[_Fiber] = []
    vectors: dict[str, AtomRecord] = {}
    for (path, digest), members in grouped.items():
        if not path or not digest:
            raise PlaneError("a plane row needs a source_path and a digest")
        provs = {str(m["provenance"]) for m in members}
        if len(provs) != 1:
            raise StratumConflict(f"{path!r}@{digest[:8]} spans classes {sorted(provs)}")
        prov = Provenance(provs.pop())
        if prov not in OCC:
            raise PlaneError("CODE rows land through the code lane, never the prose plane")
        chunks: list[tuple[int, str, str]] = []
        seen: set[int] = set()
        for m in sorted(members, key=lambda m: int(m.get("chunk_index", 0) or 0)):
            idx = int(m.get("chunk_index", 0) or 0)
            if idx in seen:
                raise PlaneError(f"{path!r}@{digest[:8]} repeats chunk_index {idx}")
            seen.add(idx)
            layer = str(m.get("layer") or "prose")
            text = str(m["text"])
            a = atom_id(text, layer)
            chunks.append((idx, a, str(m.get("id") or f"{path}:{a.split(':', 1)[1]}")))
            vec = m.get("vector")
            if vec is not None and a not in vectors:
                vectors[a] = AtomRecord(atom_id=a, layer=layer, text=text, vector=list(vec))
        fibers.append(_Fiber(source_path=path, digest=digest, provenance=prov,
                             title=str(members[0].get("title") or ""), chunks=tuple(chunks)))
    return fibers, vectors


class PlaneReader[L: Provenance]:
    """Reads under one clearance. Every relation name this object ever puts into SQL comes from
    `self._tables`, which is computed from the clearance alone — there is no code path from a
    reader to a relation the clearance does not admit."""

    __slots__ = ("_clearance", "_plane", "_tables")

    def __init__(self, plane: SharedPlane, clearance: Clearance[L]) -> None:
        self._plane = plane
        self._clearance = clearance
        self._tables: tuple[tuple[Provenance, str, str], ...] = tuple(
            (p, OCC[p], SUP[p]) for p in PLANE_CLASSES if clearance.admits(p))

    @property
    def clearance(self) -> Clearance[L]:
        return self._clearance

    def _occupancy(self, p: Provenance, r: Sequence[Any]) -> Occupancy[L]:
        return Occupancy(self._clearance, atom_id=str(r[0]), source_path=str(r[1]),
                         digest=str(r[2]), chunk_index=int(r[3]), title=str(r[4]),
                         provenance=p, current=bool(r[5]), row_id=str(r[6]), mint=_MINT)

    def _select(self, where: str, params: Sequence[Any]) -> list[Occupancy[L]]:
        conn = self._plane._db()
        out: list[Occupancy[L]] = []
        for p, occ, _ in self._tables:
            out.extend(self._occupancy(p, r) for r in conn.execute(
                f"SELECT atom_id, source_path, digest, chunk_index, title, current, row_id "
                f"FROM {occ} "
                f"WHERE {where} ORDER BY source_path, digest, chunk_index", list(params)))
        return out

    def occupancies(self, *, include_superseded: bool = False, source_path: str | None = None,
                    digest: str | None = None) -> list[Occupancy[L]]:
        clauses, params = ["1 = 1"], []
        if not include_superseded:
            clauses.append("current = 1")
        if source_path is not None:
            clauses.append("source_path = ?")
            params.append(source_path)
        if digest is not None:
            clauses.append("digest = ?")
            params.append(digest)
        return self._select(" AND ".join(clauses), params)

    def _occupancies_of(self, ids: Sequence[str], *,
                        include_superseded: bool) -> dict[str, list[Occupancy[L]]]:
        out: dict[str, list[Occupancy[L]]] = defaultdict(list)
        cur = "" if include_superseded else " AND current = 1"
        for batch in _batches(list(ids)):
            marks = ", ".join("?" for _ in batch)
            for o in self._select(f"atom_id IN ({marks}){cur}", batch):
                out[o.atom_id].append(o)
        return out

    def search(self, vector: Sequence[float], *, k: int,
               include_superseded: bool = False) -> list[PlaneHit[L]]:
        """The k nearest atoms that a cleared relation holds, each with its cleared occupancies.
        The ANN prefilter narrows candidates by the `held` cache; the cleared join decides. When a
        stale cache wastes candidates, the window widens until k hits or the table is exhausted."""
        if k <= 0 or not self._tables:
            return []
        self._plane.check_geometry()
        classes = [p.value for p, _, _ in self._tables]
        hits: list[PlaneHit[L]] = []
        seen: set[str] = set()
        limit = k
        while True:
            cands = self._plane.atoms.nearest(vector, classes=classes,
                                              superseded=include_superseded, limit=limit)
            fresh = [c for c in cands if c.atom_id not in seen]
            held = self._occupancies_of([c.atom_id for c in fresh],
                                        include_superseded=include_superseded)
            for c in fresh:
                seen.add(c.atom_id)
                occ = held.get(c.atom_id)
                if occ:
                    hits.append(PlaneHit(self._clearance, atom_id=c.atom_id, text=c.text,
                                         distance=c.distance, vector=c.vector, occupancies=occ,
                                         mint=_MINT))
            if len(hits) >= k or len(cands) < limit:
                return hits[:k]
            limit *= 4

    def _row(self, o: Occupancy[L], text: str, vector: Sequence[float],
             distance: float | None) -> Row[L]:
        fields: dict[str, Any] = {
            "id": o.row_id,
            "digest": o.digest, "title": o.title, "source_path": o.source_path,
            "chunk_index": o.chunk_index, "provenance": o.provenance.value, "text": text,
            "layer": o.atom_id.split(":", 1)[0], "qualname": "", "line_start": 0, "line_end": 0,
            "current": o.current, "vector": list(vector),
        }
        if distance is not None:
            fields["_distance"] = distance
        return Row(self._clearance, fields, mint=_MINT)

    def search_rows(self, vector: Sequence[float], *, k: int,
                    include_superseded: bool = False) -> list[Row[L]]:
        """`search`, flattened to the store's row shape: one row per cleared occupancy, nearest
        first, at most k rows."""
        rows: list[Row[L]] = []
        for hit in self.search(vector, k=k, include_superseded=include_superseded):
            for o in sorted(hit.occupancies,
                            key=lambda o: (o.provenance.value, o.source_path, o.chunk_index)):
                rows.append(self._row(o, hit.text, hit.vector or (), hit.distance))
        return rows[:k]

    def rows(self, *, include_superseded: bool = False,
             source_path: str | None = None) -> list[Row[L]]:
        """Every cleared occupancy as a store row, text and vector included."""
        occ = self.occupancies(include_superseded=include_superseded, source_path=source_path)
        payload: dict[str, tuple[str, Sequence[float]]] = {}
        ids = sorted({o.atom_id for o in occ})
        for batch in _batches(ids):
            payload.update(self._plane.atoms.payload(list(batch)))
        return [self._row(o, *payload[o.atom_id], None) for o in occ if o.atom_id in payload]

    def has_digest(self, digest: str) -> bool:
        conn = self._plane._db()
        return any(conn.execute(f"SELECT 1 FROM {occ} WHERE digest = ? LIMIT 1",
                                [digest]).fetchone() for _, occ, _ in self._tables)

    def count(self, *, include_superseded: bool = False) -> int:
        conn = self._plane._db()
        cur = "" if include_superseded else " WHERE current = 1"
        return sum(int(conn.execute(f"SELECT count(*) FROM {occ}{cur}").fetchone()[0])
                   for _, occ, _ in self._tables)

    def history(self, source_path: str) -> list[Row[L]]:
        """The path's supersession edges, oldest first — empty unless its class is cleared."""
        conn = self._plane._db()
        out: list[Row[L]] = []
        for p, _, sup in self._tables:
            out.extend(Row(self._clearance, {
                "provenance": p.value, "source_path": str(r[0]), "seq": int(r[1]),
                "old_digest": str(r[2]), "new_digest": str(r[3]), "at": str(r[4])}, mint=_MINT)
                for r in conn.execute(
                    f"SELECT source_path, seq, old_digest, new_digest, at FROM {sup} "
                    "WHERE source_path = ? ORDER BY seq", [source_path]))
        return out

    def gauges(self) -> dict[Provenance, ClassGauge]:
        """Per cleared class: current |M_c|, its distinct atoms and documents (D6)."""
        conn = self._plane._db()
        out: dict[Provenance, ClassGauge] = {}
        for p, occ, _ in self._tables:
            n, v, d = conn.execute(
                f"SELECT count(*), count(DISTINCT atom_id), count(DISTINCT source_path) "
                f"FROM {occ} WHERE current = 1").fetchone()
            out[p] = ClassGauge(occupancies=int(n), atoms=int(v), documents=int(d))
        return out

    def rank_frequency(self, *, current_only: bool = False) -> list[int]:
        """n_doc(v) over the cleared classes, sorted descending (the D6 histogram, A3's Zipf
        check across strata — counted only over what this clearance may see)."""
        conn = self._plane._db()
        docs: dict[str, set[tuple[str, str]]] = defaultdict(set)
        cur = " WHERE current = 1" if current_only else ""
        for p, occ, _ in self._tables:
            for a, path in conn.execute(f"SELECT atom_id, source_path FROM {occ}{cur}"):
                docs[str(a)].add((p.value, str(path)))
        return sorted((len(v) for v in docs.values()), reverse=True)
