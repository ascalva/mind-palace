"""The lexical index as it was before its statistics were kept (core/stores/lexical.py at
f969904e), kept verbatim as the reference the rewritten statements are tested against: the
schema, the landing, and the scoring statements (one count of each term's document frequency and
one row statement a term, scored in Python, a sort of every scored unit).
"""

from __future__ import annotations

import sqlite3
from collections import Counter
from collections.abc import Collection, Iterable, Sequence
from datetime import UTC, datetime
from typing import Any

from core.ingest.lexical import Tokenizer, idf, tf_weight
from core.kernel.ingest.chunk import Chunk
from core.kernel.provenance import Provenance

OLD_DDL = """
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


def old_land(conn: sqlite3.Connection, tokenizer: Tokenizer, source_path: str, digest: str,
             provenance: str, title: str, chunks: Sequence[Chunk]) -> None:
    """One version landed as the old store landed it, in its own transaction (the connection in
    autocommit mode, `isolation_level=None`)."""
    conn.execute("BEGIN IMMEDIATE")
    try:
        if conn.execute("SELECT value FROM meta WHERE key = 'tokenizer'").fetchone() is None:
            conn.execute("INSERT OR REPLACE INTO meta (key, value) VALUES ('tokenizer', ?)",
                         [tokenizer.identity])
        wanted = {c.index for c in chunks}
        held = {int(r[0]) for r in conn.execute(
            "SELECT chunk_index FROM units WHERE source_path = ? AND digest = ?",
            [source_path, digest])}
        if held != wanted:
            for (uid,) in conn.execute(
                    "SELECT unit_id FROM units WHERE source_path = ? AND digest = ?",
                    [source_path, digest]).fetchall():
                conn.execute("DELETE FROM postings WHERE unit_id = ?", [uid])
            conn.execute("DELETE FROM units WHERE source_path = ? AND digest = ?",
                         [source_path, digest])
            now = datetime.now(UTC).replace(tzinfo=None).isoformat(timespec="seconds")
            for c in chunks:
                counts = Counter(tokenizer(c.text))
                cur = conn.execute(
                    "INSERT INTO units (source_path, digest, chunk_index, provenance, title, "
                    "length, current, landed_at) VALUES (?, ?, ?, ?, ?, ?, 0, ?)",
                    [source_path, digest, c.index, provenance, title,
                     sum(counts.values()), now])
                uid = int(cur.lastrowid or 0)
                conn.executemany("INSERT INTO postings (term, unit_id, tf) VALUES (?, ?, ?)",
                                 [(t, uid, n) for t, n in counts.items()])
        conn.execute("INSERT OR REPLACE INTO versions (source_path, digest, units) "
                     "VALUES (?, ?, ?)", [source_path, digest, len(wanted)])
        conn.execute("UPDATE units SET current = 0 WHERE source_path = ? AND digest <> ? "
                     "AND current = 1", [source_path, digest])
        conn.execute("UPDATE units SET current = 1 WHERE source_path = ? AND digest = ? "
                     "AND current = 0", [source_path, digest])
        conn.execute("COMMIT")
    except BaseException:
        conn.execute("ROLLBACK")
        raise


def _old_class_clause(classes: Iterable[Provenance] | None) -> tuple[str, list[str]]:
    if classes is None:
        return "", []
    values = sorted({p.value for p in classes})
    if not values:
        return " AND 0", []
    return f" AND provenance IN ({', '.join('?' for _ in values)})", values


def old_score_units(conn: sqlite3.Connection, tokenizer: Tokenizer, query: str, *,
                    classes: Iterable[Provenance] | None,
                    paths: Collection[str] | None) -> dict[int, float]:
    """Every current unit's BM25 score, as the old `_score_units` computed it."""
    terms = sorted(set(tokenizer(query)))
    cls = list(classes) if classes is not None else None
    where, params = _old_class_clause(cls)
    n, total = conn.execute(
        f"SELECT count(*), COALESCE(sum(length), 0) FROM units WHERE current = 1{where}",
        params).fetchone()
    n, avgdl = int(n), (float(total) / int(n) if n else 0.0)
    if n == 0 or not terms:
        return {}
    scores: dict[int, float] = {}
    ordered = sorted(set(paths)) if paths is not None else None
    path_batches: list[Sequence[str]] = ([ordered[i:i + 400] for i in range(0, len(ordered), 400)]
                                         if ordered is not None else [()])
    for term in terms:
        df = int(conn.execute(
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
            for uid, tf, dl in conn.execute(
                    "SELECT p.unit_id, p.tf, u.length FROM postings p "
                    "JOIN units u ON u.unit_id = p.unit_id "
                    f"WHERE p.term = ? AND u.current = 1{where}{extra}",
                    [term, *params, *more]):
                scores[int(uid)] = scores.get(int(uid), 0.0) \
                    + weight * tf_weight(int(tf), int(dl), avgdl)
    return scores


def old_search(store: Any, query: str, *, k: int = 10,
               classes: Iterable[Provenance] | None = None,
               paths: Collection[str] | None = None) -> list[tuple[Any, ...]]:
    """The old `search`: `(source_path, digest, chunk_index, title, provenance, score)`."""
    scored = old_score_units(store._conn, store.tokenizer, query, classes=classes, paths=paths)
    best = sorted(scored.items(), key=lambda kv: (-kv[1], kv[0]))[:k]
    out = []
    for uid, score in best:
        row = store._conn.execute("SELECT source_path, digest, chunk_index, title, provenance "
                                  "FROM units WHERE unit_id = ?", [uid]).fetchone()
        out.append((str(row[0]), str(row[1]), int(row[2]), str(row[3]), str(row[4]),
                    float(score)))
    return out


def old_scores(store: Any, query: str, *, classes: Iterable[Provenance] | None = None,
               paths: Collection[str] | None = None) -> dict[str, float]:
    """The old `scores`: each path's best unit."""
    scored = old_score_units(store._conn, store.tokenizer, query, classes=classes, paths=paths)
    out: dict[str, float] = {}
    for uid in sorted(scored):
        (path,) = store._conn.execute("SELECT source_path FROM units WHERE unit_id = ?",
                                      [uid]).fetchone()
        out[str(path)] = max(out.get(str(path), 0.0), scored[uid])
    return out


def new_search(store: Any, query: str, **kw: Any) -> list[tuple[Any, ...]]:
    """The store's `search` in the reference's shape."""
    return [(h.source_path, h.digest, h.chunk_index, h.title, h.provenance, h.score)
            for h in store.search(query, **kw)]


def recount(store: Any) -> tuple[set[tuple[Any, ...]], set[tuple[Any, ...]]]:
    """Assert the statistics the store keeps equal a count from its units; return them."""
    conn = store._conn
    counted = ({tuple(r) for r in conn.execute(
                   "SELECT provenance, count(*), sum(length) FROM units WHERE current = 1 "
                   "GROUP BY provenance")},
               {tuple(r) for r in conn.execute(
                   "SELECT p.term, u.provenance, count(*) FROM postings p "
                   "JOIN units u ON u.unit_id = p.unit_id WHERE u.current = 1 "
                   "GROUP BY p.term, u.provenance")})
    kept = ({tuple(r) for r in conn.execute("SELECT provenance, units, tokens FROM class_stats")},
            {tuple(r) for r in conn.execute("SELECT term, provenance, df FROM term_stats")})
    assert kept == counted, (kept, counted)
    return kept
