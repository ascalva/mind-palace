"""The chat sensor's retention ledger: which raw objects are transcripts, in the order the sensor
retained them (dn-instance-lifecycle §3.4).

The chat log is derived: its rows are a deterministic parse of a transcript's bytes, and the bytes
are in the raw store (CS-1). What no other store holds is which raw objects are transcripts and in
what order they were retained, and the order matters: the first write of a turn stands
(`ChatlogStore.add_batch`), and a session that later shows a candidate secret is held at its state
before it. So the chat log is the fold of the retained transcripts in retention order, and this
ledger is that order. The sensor appends a row when it retains bytes that are new, before it
extracts anything; a reset replays the rows through the same parse, guard and landing, reading
the bytes back from the raw store, with no transcript directory.

Append-only: a row is never updated or deleted, and its `seq` is the retention order. `at` is a
wall-clock bookmark only (Law C4).

An instance whose chat log predates this ledger has one row a transcript digest the chat log
names, seeded at the ledger's first open (`seed_from`): ordered within a session by the lowest
turn the digest wrote. A digest that wrote no row (refused, empty, unparseable, or grown with no
new prose) is not in that seed, and leaving it out changes nothing in a replay, so the replay of
the seed gives back the chat log as it stands.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from core.kernel.config import Config

RETENTION_FILE = "chat_retention.sqlite"

_DDL = """
CREATE TABLE IF NOT EXISTS retained (
    seq     INTEGER PRIMARY KEY,     -- the retention order
    digest  TEXT NOT NULL UNIQUE,    -- the raw object's SHA-256
    file    TEXT NOT NULL,           -- the transcript's file stem when retained (for the report)
    at      TEXT NOT NULL            -- wall bookmark only
);
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
"""


def _now() -> str:
    return datetime.now(UTC).replace(tzinfo=None).isoformat(timespec="seconds")


@dataclass(frozen=True)
class Retained:
    seq: int
    digest: str
    file: str


@dataclass
class RetentionLedger:
    path: Path

    def __post_init__(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.path))
        self._conn.executescript(_DDL)
        self._conn.commit()

    def append(self, digest: str, file: str) -> bool:
        """Record that the sensor retained `digest`; False when it is recorded already."""
        with self._conn:
            cur = self._conn.execute(
                "INSERT OR IGNORE INTO retained (digest, file, at) VALUES (?, ?, ?)",
                [digest, file, _now()])
        return cur.rowcount == 1

    def rows(self) -> list[Retained]:
        return [Retained(int(s), str(d), str(f)) for s, d, f in self._conn.execute(
            "SELECT seq, digest, file FROM retained ORDER BY seq")]

    def count(self) -> int:
        return int(self._conn.execute("SELECT count(*) FROM retained").fetchone()[0])

    def seeded(self) -> bool:
        return self._conn.execute("SELECT 1 FROM meta WHERE key = 'seeded'").fetchone() is not None

    def seed_from(self, chatlog_path: Path) -> int:
        """Fill an empty ledger from a chat log that predates it, once: one row a distinct
        `transcript_digest`, ordered by session and, within one, by the lowest turn the digest
        wrote. Read only from the chat log; returns the rows written."""
        if self.seeded():
            return 0
        written = 0
        if self.count() == 0 and chatlog_path.exists():
            src = sqlite3.connect(f"file:{chatlog_path}?mode=ro", uri=True)
            try:
                found = src.execute(
                    "SELECT transcript_digest, session_id, MIN(turn_index) AS first "
                    "FROM chat_utterances GROUP BY transcript_digest "
                    "ORDER BY session_id, first, transcript_digest").fetchall()
            except sqlite3.OperationalError:
                found = []
            finally:
                src.close()
            with self._conn:
                for digest, session, _first in found:
                    cur = self._conn.execute(
                        "INSERT OR IGNORE INTO retained (digest, file, at) VALUES (?, ?, ?)",
                        [str(digest), str(session), _now()])
                    written += cur.rowcount
        with self._conn:
            self._conn.execute("INSERT OR REPLACE INTO meta (key, value) VALUES ('seeded', ?)",
                               [str(written)])
        return written

    def close(self) -> None:
        self._conn.close()


def open_retention_ledger(config: Config | None = None) -> RetentionLedger:
    """`data/chat_retention.sqlite`, beside the chat log it orders."""
    from core.kernel.config import get_config

    cfg = config or get_config()
    return RetentionLedger(cfg.paths.data_dir / RETENTION_FILE)
