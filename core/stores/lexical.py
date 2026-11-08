"""The lexical index of landed items: BM25 postings over the chunks a landing derived, in SQLite
beside the other derived stores (dn-two-phase-ingestion D1, D2).

The units are the chunks `derive_chunks` yields from the raw bytes, the plane's own units, so a
lexical ranking and a vector ranking rank the same things. A unit's row keeps its path, the
version it belongs to, its position, its class, its title and its length in tokens; a posting
keeps one term's count in one unit. Landing is idempotent by reconciliation, as the plane's is
(`SharedPlane.land`): a version's units are written once, then made current, and the path's other
versions stop being current, the currency flag the last write of the transaction; a retire makes
the path's units not current and keeps them, as the plane keeps a retired version's rows. The
UNCHANGED check of a lazy landing reads this currency (`Writer.holds`), so an active key implies
the units are held (ING-7 at the item's grain, with the lexical units in the plane rows' place).
Each landed version is also recorded with its count of units, in the same transaction, so a
version with no text (no unit) is known landed and complete, and an item landed before the index
was opened is known not to be: the drain tells the two apart (`derive.pending`) and the backfill
lands the second (`derive.derive_lexical`).

A query is scored over the current units of the classes a reader may see, by the arithmetic of
`core/ingest/lexical.py`, with the document frequencies, the unit count and the mean length read
from the current units at query time; so a landing changes no stored weight, and the index
needs no rebuild as the corpus grows. The index is derived and regenerable: it can be rebuilt
from the raw store and the catalog, and nothing but a lexical `near` and the UNCHANGED check of a
lazy landing reads it.

The units' terms are a tokenizer's (`core/ingest/lexical.py::Tokenizer`), and the store records
the tokenizer's identity with its first landing, as the plane records its embedder's. A store
whose recorded identity is not its tokenizer's refuses to land or to score (`TokenizerMismatch`):
a query tokenized one way against units tokenized another would match some words and silently
miss others. A store that holds versions and records no identity predates the record, and its
units are LEGACY's. Re-deriving is the lexical backfill over a reset index: `reset` forgets the
units, the postings, the versions and the identity, and `derive.derive_lexical`, which resets a
stale index itself, lands every active item again under the current tokenizer. The currency
reads (`holds_current`, `units_of`, the version records) do not depend on the terms and do not
refuse.
"""

from __future__ import annotations

import sqlite3
from collections import Counter
from collections.abc import Collection, Iterable, Iterator, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import core.ingest.lexical as lexical
from core.ingest.lexical import LEGACY, Tokenizer, TokenizerMismatch, idf, tf_weight
from core.kernel.config import Config
from core.kernel.ingest.chunk import Chunk
from core.kernel.provenance import Provenance

LEXICAL_FILE = "lexical.sqlite"
_BATCH = 400

_DDL = """
CREATE TABLE IF NOT EXISTS units (
    unit_id     INTEGER PRIMARY KEY,
    source_path TEXT    NOT NULL,
    digest      TEXT    NOT NULL,
    chunk_index INTEGER NOT NULL,
    provenance  TEXT    NOT NULL,
    title       TEXT    NOT NULL,
    length      INTEGER NOT NULL,
    current     INTEGER NOT NULL DEFAULT 0,
    landed_at   TEXT    NOT NULL,
    UNIQUE (source_path, digest, chunk_index)
);
CREATE INDEX IF NOT EXISTS units_path ON units (source_path, current);
CREATE INDEX IF NOT EXISTS units_current ON units (current, provenance);
CREATE TABLE IF NOT EXISTS postings (
    term    TEXT    NOT NULL,
    unit_id INTEGER NOT NULL,
    tf      INTEGER NOT NULL,
    PRIMARY KEY (term, unit_id)
) WITHOUT ROWID;
CREATE INDEX IF NOT EXISTS postings_unit ON postings (unit_id);
CREATE TABLE IF NOT EXISTS versions (
    source_path TEXT    NOT NULL,
    digest      TEXT    NOT NULL,
    units       INTEGER NOT NULL,
    PRIMARY KEY (source_path, digest)
) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
"""


def _now() -> str:
    return datetime.now(UTC).replace(tzinfo=None).isoformat(timespec="seconds")


def _batches(items: Sequence[str]) -> Iterator[Sequence[str]]:
    for i in range(0, len(items), _BATCH):
        yield items[i:i + _BATCH]


@dataclass(frozen=True)
class LexicalLanding:
    """What one landing did: the units written (none when the version was held already), the
    versions of the path that stopped being current, and whether the version became current."""

    units_written: int = 0
    superseded: int = 0
    made_current: bool = False


@dataclass(frozen=True)
class LexicalHit:
    """One unit a query ranks: where it is, what it is, and its score."""

    source_path: str
    digest: str
    chunk_index: int
    title: str
    provenance: str
    score: float


def lexical_path(cfg: Config) -> Path:
    """Where an instance keeps its lexical index: beside its other derived stores."""
    return Path(cfg.paths.data_dir) / LEXICAL_FILE


def open_lexical_store(cfg: Config) -> LexicalStore:
    return LexicalStore(lexical_path(cfg))


def _current() -> Tokenizer:
    return lexical.TOKENIZER


@dataclass
class LexicalStore:
    path: Path
    tokenizer: Tokenizer = field(default_factory=_current)

    def __post_init__(self) -> None:
        if str(self.path) != ":memory:":
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.path), timeout=30.0, isolation_level=None)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA busy_timeout=30000")
        self._conn.executescript(_DDL)

    def close(self) -> None:
        self._conn.close()

    # ── the tokenizer's identity ─────────────────────────────────────────────────────────────

    def recorded_tokenizer(self) -> str | None:
        """The identity of the tokenizer the units were made by: the recorded one; LEGACY's for a
        store that holds versions from before identities were recorded; None for an empty store
        that has recorded nothing yet."""
        row = self._conn.execute("SELECT value FROM meta WHERE key = 'tokenizer'").fetchone()
        if row is not None:
            return str(row[0])
        held = self._conn.execute("SELECT 1 FROM versions LIMIT 1").fetchone()
        return LEGACY.identity if held is not None else None

    @property
    def stale(self) -> bool:
        """Whether the units were made by another tokenizer than this store's: they must be
        re-derived (`reset`, then the lexical backfill) before the store lands or scores."""
        recorded = self.recorded_tokenizer()
        return recorded is not None and recorded != self.tokenizer.identity

    def _check_tokenizer(self, *, record: bool) -> None:
        recorded = self.recorded_tokenizer()
        mine = self.tokenizer.identity
        if recorded is None:
            if record:
                self._conn.execute("INSERT OR REPLACE INTO meta (key, value) "
                                   "VALUES ('tokenizer', ?)", [mine])
            return
        if recorded != mine:
            raise TokenizerMismatch(
                f"the lexical index's units were tokenized by {recorded}; this store's tokenizer "
                f"is {mine}. Re-derive the index (the embed command resets it and lands every "
                "item again)")

    def reset(self) -> None:
        """Forget every unit, posting and version record, and the recorded tokenizer, in one
        transaction: the index is derived, and the lexical backfill rebuilds it from the raw
        store (`derive.derive_lexical`)."""
        conn = self._conn
        conn.execute("BEGIN IMMEDIATE")
        try:
            conn.execute("DELETE FROM postings")
            conn.execute("DELETE FROM units")
            conn.execute("DELETE FROM versions")
            conn.execute("DELETE FROM meta WHERE key = 'tokenizer'")
            conn.execute("COMMIT")
        except BaseException:
            conn.execute("ROLLBACK")
            raise

    # ── landing and retiring ─────────────────────────────────────────────────────────────────

    def land(self, *, source_path: str, digest: str, provenance: str, title: str,
             chunks: Sequence[Chunk]) -> LexicalLanding:
        """Land one version's units and make it the path's current version. Idempotent by
        reconciliation: a version whose units are held already is not written again, and only
        the currency moves; the currency is the transaction's last write, so a crash anywhere
        before it leaves the version as it was, not current, for the next landing to finish."""
        return self.land_many([(source_path, digest, provenance, title, chunks)])[0]

    def land_many(self, items: Sequence[tuple[str, str, str, str, Sequence[Chunk]]]
                  ) -> list[LexicalLanding]:
        """Land several versions, each `(source_path, digest, provenance, title, chunks)`, in one
        transaction, each as `land` lands it: a batched landing's lexical stage, or a backfill's.
        The transaction commits every version or none."""
        conn = self._conn
        conn.execute("BEGIN IMMEDIATE")
        try:
            self._check_tokenizer(record=True)
            out = [self._land_one(*item) for item in items]
            conn.execute("COMMIT")
        except BaseException:
            conn.execute("ROLLBACK")
            raise
        return out

    def _land_one(self, source_path: str, digest: str, provenance: str, title: str,
                  chunks: Sequence[Chunk]) -> LexicalLanding:
        conn = self._conn
        wanted = {c.index for c in chunks}
        held = {int(r[0]) for r in conn.execute(
            "SELECT chunk_index FROM units WHERE source_path = ? AND digest = ?",
            [source_path, digest])}
        written = 0
        if held != wanted:
            for (uid,) in conn.execute(
                    "SELECT unit_id FROM units WHERE source_path = ? AND digest = ?",
                    [source_path, digest]).fetchall():
                conn.execute("DELETE FROM postings WHERE unit_id = ?", [uid])
            conn.execute("DELETE FROM units WHERE source_path = ? AND digest = ?",
                         [source_path, digest])
            now = _now()
            for c in chunks:
                counts = Counter(self.tokenizer(c.text))
                cur = conn.execute(
                    "INSERT INTO units (source_path, digest, chunk_index, provenance, title, "
                    "length, current, landed_at) VALUES (?, ?, ?, ?, ?, ?, 0, ?)",
                    [source_path, digest, c.index, provenance, title,
                     sum(counts.values()), now])
                uid = int(cur.lastrowid or 0)
                conn.executemany("INSERT INTO postings (term, unit_id, tf) VALUES (?, ?, ?)",
                                 [(t, uid, n) for t, n in counts.items()])
                written += 1
        conn.execute("INSERT OR REPLACE INTO versions (source_path, digest, units) "
                     "VALUES (?, ?, ?)", [source_path, digest, len(wanted)])
        superseded = conn.execute(
            "UPDATE units SET current = 0 WHERE source_path = ? AND digest <> ? "
            "AND current = 1", [source_path, digest]).rowcount
        made = conn.execute(
            "UPDATE units SET current = 1 WHERE source_path = ? AND digest = ? "
            "AND current = 0", [source_path, digest]).rowcount
        return LexicalLanding(units_written=written, superseded=int(superseded),
                              made_current=made > 0)

    def retire(self, source_path: str) -> int:
        """The path is gone: its units stop being current and stay, as the plane keeps a retired
        version's rows. Returns the units retired."""
        return int(self._conn.execute(
            "UPDATE units SET current = 0 WHERE source_path = ? AND current = 1",
            [source_path]).rowcount)

    # ── what is held ─────────────────────────────────────────────────────────────────────────

    def holds_current(self, source_path: str, digest: str) -> bool:
        """Whether the index holds `source_path` at version `digest`, current: the lexical half
        of a lazy landing's UNCHANGED check."""
        return self._conn.execute(
            "SELECT 1 FROM units WHERE source_path = ? AND digest = ? AND current = 1 LIMIT 1",
            [source_path, digest]).fetchone() is not None

    def units_of(self, source_path: str, *, digest: str | None = None,
                 current: bool = True) -> int:
        """How many units the index holds for a path (of one version when given)."""
        clauses, params = ["source_path = ?"], [source_path]
        if digest is not None:
            clauses.append("digest = ?")
            params.append(digest)
        if current:
            clauses.append("current = 1")
        return int(self._conn.execute(
            f"SELECT count(*) FROM units WHERE {' AND '.join(clauses)}", params).fetchone()[0])

    def empty_versions(self) -> set[tuple[str, str]]:
        """The versions landed with no unit, `(source_path, digest)`: items with no text,
        complete, with nothing for the drain to derive."""
        return {(str(p), str(d)) for p, d in self._conn.execute(
            "SELECT source_path, digest FROM versions WHERE units = 0")}

    def landed_versions(self) -> set[tuple[str, str]]:
        """Every version the index has landed, `(source_path, digest)`, with units or without."""
        return {(str(p), str(d)) for p, d in self._conn.execute(
            "SELECT source_path, digest FROM versions")}

    def count(self, *, classes: Iterable[Provenance] | None = None) -> int:
        """The current units, of the given classes when given."""
        where, params = self._class_clause(classes)
        return int(self._conn.execute(
            f"SELECT count(*) FROM units WHERE current = 1{where}", params).fetchone()[0])

    # ── scoring ──────────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _class_clause(classes: Iterable[Provenance] | None) -> tuple[str, list[str]]:
        if classes is None:
            return "", []
        values = sorted({p.value for p in classes})
        if not values:
            return " AND 0", []
        return f" AND provenance IN ({', '.join('?' for _ in values)})", values

    def _stats(self, classes: Iterable[Provenance] | None) -> tuple[int, float]:
        where, params = self._class_clause(classes)
        n, total = self._conn.execute(
            f"SELECT count(*), COALESCE(sum(length), 0) FROM units WHERE current = 1{where}",
            params).fetchone()
        return int(n), (float(total) / int(n) if n else 0.0)

    def _score_units(self, query: str, *, classes: Iterable[Provenance] | None,
                     paths: Collection[str] | None) -> dict[int, float]:
        """Every current unit's BM25 score for a query, among the classes (all when None) and the
        paths (all when None); units sharing no term with the query are absent."""
        self._check_tokenizer(record=False)
        terms = sorted(set(self.tokenizer(query)))
        cls = list(classes) if classes is not None else None
        n, avgdl = self._stats(cls)
        if n == 0 or not terms:
            return {}
        where, params = self._class_clause(cls)
        scores: dict[int, float] = {}
        path_batches: list[Sequence[str]] = (list(_batches(sorted(set(paths))))
                                             if paths is not None else [()])
        for term in terms:
            df = int(self._conn.execute(
                "SELECT count(*) FROM postings p JOIN units u ON u.unit_id = p.unit_id "
                f"WHERE p.term = ? AND u.current = 1{where}", [term, *params]).fetchone()[0])
            if df == 0:
                continue
            weight = idf(n, df)
            for batch in path_batches:
                extra, more = "", []
                if paths is not None:
                    if not batch:
                        continue
                    extra = f" AND u.source_path IN ({', '.join('?' for _ in batch)})"
                    more = list(batch)
                for uid, tf, dl in self._conn.execute(
                        "SELECT p.unit_id, p.tf, u.length FROM postings p "
                        "JOIN units u ON u.unit_id = p.unit_id "
                        f"WHERE p.term = ? AND u.current = 1{where}{extra}",
                        [term, *params, *more]):
                    scores[int(uid)] = scores.get(int(uid), 0.0) \
                        + weight * tf_weight(int(tf), int(dl), avgdl)
        return scores

    def search(self, query: str, *, k: int = 10, classes: Iterable[Provenance] | None = None,
               paths: Collection[str] | None = None) -> list[LexicalHit]:
        """The `k` best current units for a query, best first, ties by unit id; a unit that
        shares no term with the query is never returned."""
        scored = self._score_units(query, classes=classes, paths=paths)
        if not scored:
            return []
        best = sorted(scored.items(), key=lambda kv: (-kv[1], kv[0]))[:k]
        out = []
        for uid, score in best:
            row = self._conn.execute(
                "SELECT source_path, digest, chunk_index, title, provenance FROM units "
                "WHERE unit_id = ?", [uid]).fetchone()
            out.append(LexicalHit(str(row[0]), str(row[1]), int(row[2]), str(row[3]),
                                  str(row[4]), float(score)))
        return out

    def scores(self, query: str, *, classes: Iterable[Provenance] | None = None,
               paths: Collection[str] | None = None) -> dict[str, float]:
        """Each path's score for a query: the best of its current units' scores; paths sharing no
        term with the query are absent."""
        scored = self._score_units(query, classes=classes, paths=paths)
        if not scored:
            return {}
        out: dict[str, float] = {}
        ids = sorted(scored)
        for i in range(0, len(ids), _BATCH):
            batch = ids[i:i + _BATCH]
            for uid, path in self._conn.execute(
                    "SELECT unit_id, source_path FROM units WHERE unit_id IN "
                    f"({', '.join('?' for _ in batch)})", batch):
                p = str(path)
                out[p] = max(out.get(p, 0.0), scored[int(uid)])
        return out
