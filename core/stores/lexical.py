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
`core/ingest/lexical.py`, with the unit count, the mean length and the document frequencies of
those classes' current units. They are kept, not counted at query time: per class, the current
units and their total length (`class_stats`), and per class and term, the current units holding
the term (`term_stats`), written in the transaction of every write that changes which units are
current (a landing, a retire, a reset), from the units whose currency the transaction changed. A
reader's statistics are the sums over its cleared classes' rows and nothing else, so a filtered
read is a function of the cleared rows alone, as when they were counted. A landing changes no
stored weight, and the index needs no rebuild as the corpus grows. The index is derived and
regenerable: it can be rebuilt from the raw store and the catalog, and nothing but a lexical
`near` and the UNCHANGED check of a lazy landing reads it. A store written before the statistics
existed gets them on its first open, counted from its current units in one transaction (a store
whose units another tokenizer made is re-derived first, and its statistics with it); from then on
its units refuse a write that does not come through this class, since a writer that does not
keep the statistics (an older process still running) would leave them wrong without a sign.

The rows a query scores are read from the query terms' postings, or from the given paths' units
when a caller passes paths (the palace's own call, `core/sentence/universe.py`), and the
arithmetic, the sum over the terms and the top `k` are one statement. The sum is written out in
the order of the sorted terms, not taken by SQLite's `sum()`, which compensates its rounding, so
a score is the reference's to the last bit (ties broken by unit id); a query of more terms than
SQLite parses in one sum (`_SUM_TERMS`) has the same weights summed outside the statement, in the
same order.

The units' terms are a tokenizer's (`core/ingest/lexical.py::Tokenizer`), and the store records
the tokenizer's identity with its first landing, as the plane records its embedder's. A store
whose recorded identity is not its tokenizer's refuses to land or to score (`TokenizerMismatch`):
a query tokenized one way against units tokenized another would match some words and silently
miss others. A store that holds versions and records no identity predates the record, and its
units are LEGACY's. Re-deriving is the lexical backfill over a reset index: `reset` forgets the
units, the postings, the versions, the statistics and the identity, and `derive.derive_lexical`,
which resets a stale index itself, lands every active item again under the current tokenizer. The
currency reads (`holds_current`, `units_of`, the version records) do not depend on the terms and
do not refuse.
"""

from __future__ import annotations

import sqlite3
from collections import Counter
from collections.abc import Collection, Iterable, Iterator, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import core.ingest.lexical as lexical
from core.ingest.lexical import LEGACY, Tokenizer, TokenizerMismatch, idf
from core.kernel.config import Config
from core.kernel.ingest.chunk import Chunk
from core.kernel.provenance import Provenance

LEXICAL_FILE = "lexical.sqlite"
_BATCH = 400
# The most terms a query's sum is written out for in one statement: SQLite parses `a + b + ...`
# as a tree as deep as its terms and refuses one deeper than 1,000. A longer query's weights are
# summed outside the statement, in the same order.
_SUM_TERMS = 500
_STATISTICS = "statistics"     # the meta key set once the statistics are counted
_WRITER = "writer"             # the meta key this class's write transactions hold while they run

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
CREATE TABLE IF NOT EXISTS class_stats (
    provenance TEXT    PRIMARY KEY,
    units      INTEGER NOT NULL,
    tokens     INTEGER NOT NULL
) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS term_stats (
    term       TEXT    NOT NULL,
    provenance TEXT    NOT NULL,
    df         INTEGER NOT NULL,
    PRIMARY KEY (term, provenance)
) WITHOUT ROWID;
"""

# Installed with the statistics: a write to the units from outside this class's transactions (a
# process that does not keep the statistics) is refused, whole, rather than left to make them
# wrong. A unit's postings are written and deleted only with it, in the same transaction.
_GUARDS = tuple(
    f"CREATE TRIGGER IF NOT EXISTS units_kept_{name} BEFORE {event} ON units "
    f"WHEN NOT EXISTS (SELECT 1 FROM meta WHERE key = '{_WRITER}') BEGIN "
    "SELECT RAISE(ABORT, 'the lexical index keeps statistics of its current units: write its "
    "units through core/stores/lexical.py, which keeps them (an older process does not)'); END"
    for name, event in (("insert", "INSERT"),
                        ("update", "UPDATE OF current, provenance, length, unit_id"),
                        ("delete", "DELETE")))


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


@dataclass(frozen=True)
class LexicalStatistics:
    """What a reader's scores are computed with: over the current units of its classes, their
    count, their total length in tokens and, for each term asked about, the units holding it."""

    units: int
    tokens: int
    df: dict[str, int]


class _Currency:
    """The units whose currency a transaction changed, each with the sign of its net change (+1
    made current, -1 no longer current); a unit made current and then not, in one transaction,
    leaves no change."""

    def __init__(self) -> None:
        self.net: dict[int, int] = {}

    def add(self, unit_ids: Iterable[int], sign: int) -> None:
        for uid in unit_ids:
            value = self.net.get(uid, 0) + sign
            if value:
                self.net[uid] = value
            else:
                self.net.pop(uid, None)

    def take(self, unit_ids: Iterable[int]) -> dict[int, int]:
        """The pending changes of these units, removed from the transaction's: they are kept now,
        while the units' postings still exist."""
        return {uid: self.net.pop(uid) for uid in unit_ids if uid in self.net}


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
        self._migrate()

    def close(self) -> None:
        self._conn.close()

    # ── transactions ─────────────────────────────────────────────────────────────────────────

    def _begin(self) -> None:
        """A write transaction of this class: it holds the writer's key, which the units' guards
        read, and removes it before it commits, so no other transaction ever sees it."""
        self._conn.execute("BEGIN IMMEDIATE")
        self._conn.execute("INSERT OR REPLACE INTO meta (key, value) VALUES (?, '1')", [_WRITER])

    def _commit(self) -> None:
        self._conn.execute("DELETE FROM meta WHERE key = ?", [_WRITER])
        self._conn.execute("COMMIT")

    # ── the statistics ───────────────────────────────────────────────────────────────────────

    def _counted(self) -> bool:
        return self._conn.execute("SELECT 1 FROM meta WHERE key = ?",
                                  [_STATISTICS]).fetchone() is not None

    def _migrate(self) -> None:
        """Count the statistics of a store that has none yet (one written before they existed,
        or whose record of them was removed), from its current units, in one transaction, and
        install the units' guards with them. A store whose units another tokenizer made is left
        alone: it neither lands nor scores until it is re-derived, and its `reset` counts them."""
        if self._counted() or self.stale:
            return
        conn = self._conn
        self._begin()
        try:
            if not self._counted():
                self._count_statistics()
            self._commit()
        except BaseException:
            conn.execute("ROLLBACK")
            raise

    def _count_statistics(self) -> None:
        """The statistics counted from the units, inside the caller's transaction: one pass over
        the postings a class, in term order, so the counts arrive in the table's order."""
        conn = self._conn
        conn.execute("DELETE FROM class_stats")
        conn.execute("DELETE FROM term_stats")
        conn.execute("INSERT INTO class_stats (provenance, units, tokens) "
                     "SELECT provenance, count(*), sum(length) FROM units WHERE current = 1 "
                     "GROUP BY provenance")
        for (prov,) in conn.execute(
                "SELECT provenance FROM class_stats ORDER BY provenance").fetchall():
            conn.execute("INSERT INTO term_stats (term, provenance, df) "
                         "SELECT p.term, ?, count(*) FROM postings p "
                         "CROSS JOIN units u ON u.unit_id = p.unit_id "
                         "WHERE u.current = 1 AND u.provenance = ? GROUP BY p.term", [prov, prov])
        for guard in _GUARDS:
            conn.execute(guard)
        conn.execute("INSERT OR REPLACE INTO meta (key, value) VALUES (?, '1')", [_STATISTICS])

    def _keep(self, changes: dict[int, int]) -> None:
        """Move the statistics by the units whose currency changed (+1 made current, -1 no
        longer current), inside the caller's transaction and before any of their postings goes;
        nothing while the statistics are not counted (their count, when it comes, reads the
        units as they are then)."""
        if not changes or not self._counted():
            return
        conn = self._conn
        conn.execute("CREATE TEMP TABLE IF NOT EXISTS lex_shift (unit_id INTEGER PRIMARY KEY)")
        conn.execute("CREATE TEMP TABLE IF NOT EXISTS lex_delta (term TEXT NOT NULL, "
                     "provenance TEXT NOT NULL, n INTEGER NOT NULL, "
                     "PRIMARY KEY (term, provenance)) WITHOUT ROWID")
        for sign in sorted(set(changes.values())):
            conn.execute("DELETE FROM temp.lex_shift")
            conn.executemany("INSERT INTO temp.lex_shift (unit_id) VALUES (?)",
                             [(uid,) for uid, s in changes.items() if s == sign])
            conn.execute("INSERT INTO class_stats (provenance, units, tokens) "
                         "SELECT u.provenance, ? * count(*), ? * sum(u.length) "
                         "FROM temp.lex_shift s CROSS JOIN units u ON u.unit_id = s.unit_id "
                         "WHERE true GROUP BY u.provenance "
                         "ON CONFLICT (provenance) DO UPDATE SET units = units + excluded.units, "
                         "tokens = tokens + excluded.tokens", [sign, sign])
            conn.execute("DELETE FROM temp.lex_delta")
            conn.execute("INSERT INTO temp.lex_delta (term, provenance, n) "
                         "SELECT p.term, u.provenance, count(*) FROM temp.lex_shift s "
                         "CROSS JOIN units u ON u.unit_id = s.unit_id "
                         "CROSS JOIN postings p ON p.unit_id = s.unit_id "
                         "GROUP BY p.term, u.provenance")
            conn.execute("INSERT INTO term_stats (term, provenance, df) "
                         "SELECT term, provenance, ? * n FROM temp.lex_delta WHERE true "
                         "ON CONFLICT (term, provenance) DO UPDATE SET df = df + excluded.df",
                         [sign])
            if sign < 0:
                conn.execute("DELETE FROM term_stats WHERE df = 0 AND (term, provenance) IN "
                             "(SELECT term, provenance FROM temp.lex_delta)")
                conn.execute("DELETE FROM class_stats WHERE units = 0")

    def statistics(self, *, classes: Iterable[Provenance] | None = None,
                   terms: Iterable[str] = ()) -> LexicalStatistics:
        """A reader's statistics: the sums of its classes' rows (every class when None), over
        the current units; a term no current unit of those classes holds has no entry."""
        values = sorted({p.value for p in classes}) if classes is not None else None
        if values is not None and not values:
            return LexicalStatistics(0, 0, {})
        where = f" WHERE provenance IN ({', '.join('?' for _ in values)})" if values else ""
        n, total = self._conn.execute(
            f"SELECT COALESCE(sum(units), 0), COALESCE(sum(tokens), 0) FROM class_stats{where}",
            values or []).fetchone()
        df: dict[str, int] = {}
        wanted = sorted(set(terms))
        for batch in _batches(wanted):
            marks = ", ".join("?" for _ in batch)
            clause = f" AND provenance IN ({', '.join('?' for _ in values)})" if values else ""
            for term, count in self._conn.execute(
                    f"SELECT term, sum(df) FROM term_stats WHERE term IN ({marks}){clause} "
                    "GROUP BY term", [*batch, *(values or [])]):
                if int(count):
                    df[str(term)] = int(count)
        return LexicalStatistics(int(n), int(total), df)

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
        """Forget every unit, posting, version record and statistic, and the recorded tokenizer,
        in one transaction: the index is derived, and the lexical backfill rebuilds it from the
        raw store (`derive.derive_lexical`). The empty store's statistics are counted (none)."""
        conn = self._conn
        self._begin()
        try:
            conn.execute("DELETE FROM postings")
            conn.execute("DELETE FROM units")
            conn.execute("DELETE FROM versions")
            conn.execute("DELETE FROM meta WHERE key = 'tokenizer'")
            self._count_statistics()
            self._commit()
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
        The statistics move with the currency in the same transaction, once for the whole batch.
        The transaction commits every version or none."""
        conn = self._conn
        self._begin()
        try:
            self._check_tokenizer(record=True)
            currency = _Currency()
            out = [self._land_one(*item, currency=currency) for item in items]
            self._keep(currency.net)
            self._commit()
        except BaseException:
            conn.execute("ROLLBACK")
            raise
        return out

    def _land_one(self, source_path: str, digest: str, provenance: str, title: str,
                  chunks: Sequence[Chunk], *, currency: _Currency) -> LexicalLanding:
        conn = self._conn
        wanted = {c.index for c in chunks}
        held = {int(r[0]) for r in conn.execute(
            "SELECT chunk_index FROM units WHERE source_path = ? AND digest = ?",
            [source_path, digest])}
        written = 0
        if held != wanted:
            gone = [int(r[0]) for r in conn.execute(
                "SELECT unit_id FROM units WHERE source_path = ? AND digest = ?",
                [source_path, digest]).fetchall()]
            # units leaving while current leave the statistics first, while their postings exist
            currency.add([int(r[0]) for r in conn.execute(
                "UPDATE units SET current = 0 WHERE source_path = ? AND digest = ? "
                "AND current = 1 RETURNING unit_id", [source_path, digest]).fetchall()], -1)
            self._keep(currency.take(gone))
            for uid in gone:
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
        superseded = [int(r[0]) for r in conn.execute(
            "UPDATE units SET current = 0 WHERE source_path = ? AND digest <> ? "
            "AND current = 1 RETURNING unit_id", [source_path, digest]).fetchall()]
        made = [int(r[0]) for r in conn.execute(
            "UPDATE units SET current = 1 WHERE source_path = ? AND digest = ? "
            "AND current = 0 RETURNING unit_id", [source_path, digest]).fetchall()]
        currency.add(superseded, -1)
        currency.add(made, +1)
        return LexicalLanding(units_written=written, superseded=len(superseded),
                              made_current=bool(made))

    def retire(self, source_path: str) -> int:
        """The path is gone: its units stop being current and stay, as the plane keeps a retired
        version's rows, and leave the statistics in the same transaction. Returns the units
        retired."""
        conn = self._conn
        self._begin()
        try:
            gone = [int(r[0]) for r in conn.execute(
                "UPDATE units SET current = 0 WHERE source_path = ? AND current = 1 "
                "RETURNING unit_id", [source_path]).fetchall()]
            self._keep({uid: -1 for uid in gone})
            self._commit()
        except BaseException:
            conn.execute("ROLLBACK")
            raise
        return len(gone)

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
    def _class_clause(classes: Iterable[Provenance] | None,
                      column: str = "provenance") -> tuple[str, list[str]]:
        if classes is None:
            return "", []
        values = sorted({p.value for p in classes})
        if not values:
            return " AND 0", []
        return f" AND {column} IN ({', '.join('?' for _ in values)})", values

    def _ranked(self, query: str, *, classes: Iterable[Provenance] | None,
                paths: Collection[str] | None, k: int | None, per_path: bool) -> list[Any]:
        """The current units' BM25 scores for a query, among the classes (all when None) and the
        paths (all when None), in one statement: `(unit_id, score, source_path, digest,
        chunk_index, title, provenance)` best first, ties by unit id, the first `k` (every one
        when None); or with `per_path`, `(source_path, score)`, each path's best unit. A unit
        that shares no term with the query is absent.

        Each posting's weight is `core/ingest/lexical.py`'s arithmetic, operation for operation,
        and a unit's score is the sum of its terms' weights in the order of the sorted terms,
        written out, each term the unit lacks adding 0.0; adding 0.0 leaves a positive double as
        it is, so the sum is the reference loop's to the bit. Past `_SUM_TERMS` terms the weights
        come out of the statement in that order and are summed here."""
        self._check_tokenizer(record=False)
        if not self._counted():
            self._migrate()
        terms = sorted(set(self.tokenizer(query)))
        cls = list(classes) if classes is not None else None
        stats = self.statistics(classes=cls, terms=terms)
        if stats.units == 0 or not terms:
            return []
        avgdl = float(stats.tokens) / stats.units
        weighted = [(t, idf(stats.units, stats.df[t])) for t in terms if stats.df.get(t, 0)]
        wanted = sorted(set(paths)) if paths is not None else None
        if not weighted or wanted == []:
            return []
        conn = self._conn
        conn.execute("CREATE TEMP TABLE IF NOT EXISTS lex_query (i INTEGER PRIMARY KEY, "
                      "term TEXT NOT NULL, w REAL NOT NULL)")
        conn.execute("DELETE FROM temp.lex_query")
        conn.executemany("INSERT INTO temp.lex_query (i, term, w) VALUES (?, ?, ?)",
                         [(i, t, w) for i, (t, w) in enumerate(weighted)])
        where, values = self._class_clause(cls, "u.provenance")
        if wanted is not None:
            conn.execute("CREATE TEMP TABLE IF NOT EXISTS lex_paths (path TEXT PRIMARY KEY)")
            conn.execute("DELETE FROM temp.lex_paths")
            conn.executemany("INSERT INTO temp.lex_paths (path) VALUES (?)",
                             [(p,) for p in wanted])
            # the paths' units by their index: with no planner statistics, SQLite would take the
            # class's index and visit every current unit of the class for each path
            rows = ("FROM temp.lex_paths w CROSS JOIN units u INDEXED BY units_path "
                    "ON u.source_path = w.path AND u.current = 1 CROSS JOIN temp.lex_query q "
                    "CROSS JOIN postings p ON p.term = q.term AND p.unit_id = u.unit_id "
                    f"WHERE true{where}")
        else:
            rows = ("FROM temp.lex_query q CROSS JOIN postings p ON p.term = q.term "
                    f"CROSS JOIN units u ON u.unit_id = p.unit_id WHERE u.current = 1{where}")
        k1, b = lexical.K1, lexical.B
        weights = ("SELECT p.unit_id AS unit_id, q.i AS i, "
                   "q.w * ((p.tf * ?) / (p.tf + ? * (? + (? * u.length) / ?))) AS c " + rows)
        params: list[Any] = [k1 + 1.0, k1, 1.0 - b, b, avgdl, *values]
        if len(weighted) > _SUM_TERMS:
            # past SQLite's depth for one written-out sum: the same weights, summed here in the
            # same order of the terms
            acc: dict[int, float] = {}
            for uid, _, c in conn.execute(weights + " ORDER BY q.i", params):
                acc[int(uid)] = acc.get(int(uid), 0.0) + float(c)
            return self._rank_sums(acc, k=k, per_path=per_path)
        total = " + ".join(f"COALESCE(max(r.c) FILTER (WHERE r.i = {i}), 0.0)"
                           for i in range(len(weighted)))
        scored = f"SELECT r.unit_id AS unit_id, {total} AS score FROM ({weights}) r " \
                 "GROUP BY r.unit_id"
        if per_path:
            sql = (f"SELECT u.source_path, max(s.score) FROM ({scored}) s "
                   "CROSS JOIN units u ON u.unit_id = s.unit_id "
                   "GROUP BY u.source_path ORDER BY min(s.unit_id)")
        else:
            sql = (f"SELECT s.unit_id, s.score, u.source_path, u.digest, u.chunk_index, u.title, "
                   f"u.provenance FROM ({scored} ORDER BY score DESC, unit_id LIMIT ?) s "
                   "CROSS JOIN units u ON u.unit_id = s.unit_id "
                   "ORDER BY s.score DESC, s.unit_id")
            params.append(-1 if k is None else k)
        return conn.execute(sql, params).fetchall()

    def _rank_sums(self, acc: dict[int, float], *, k: int | None,
                   per_path: bool) -> list[Any]:
        """`_ranked`'s rows from scores summed outside the statement: the top `k` with their
        units' fields, best first, ties by unit id; or each path's best, in the order of its
        first unit."""
        conn = self._conn
        if per_path:
            best: dict[str, float] = {}
            ids = sorted(acc)
            for i in range(0, len(ids), _BATCH):
                batch = ids[i:i + _BATCH]
                for uid, path in conn.execute(
                        "SELECT unit_id, source_path FROM units WHERE unit_id IN "
                        f"({', '.join('?' for _ in batch)}) ORDER BY unit_id", batch):
                    p = str(path)
                    best[p] = max(best[p], acc[int(uid)]) if p in best else acc[int(uid)]
            return list(best.items())
        ranked = sorted(acc.items(), key=lambda kv: (-kv[1], kv[0]))
        out = []
        for uid, score in ranked if k is None else ranked[:k]:
            row = conn.execute("SELECT source_path, digest, chunk_index, title, provenance "
                               "FROM units WHERE unit_id = ?", [uid]).fetchone()
            out.append((uid, score, *row))
        return out

    def search(self, query: str, *, k: int = 10, classes: Iterable[Provenance] | None = None,
               paths: Collection[str] | None = None) -> list[LexicalHit]:
        """The `k` best current units for a query, best first, ties by unit id; a unit that
        shares no term with the query is never returned."""
        rows = self._ranked(query, classes=classes, paths=paths, k=k if k >= 0 else None,
                            per_path=False)
        hits = [LexicalHit(str(r[2]), str(r[3]), int(r[4]), str(r[5]), str(r[6]), float(r[1]))
                for r in rows]
        return hits if k >= 0 else hits[:k]

    def scores(self, query: str, *, classes: Iterable[Provenance] | None = None,
               paths: Collection[str] | None = None) -> dict[str, float]:
        """Each path's score for a query: the best of its current units' scores; paths sharing no
        term with the query are absent."""
        return {str(p): float(s) for p, s in
                self._ranked(query, classes=classes, paths=paths, k=None, per_path=True)}
