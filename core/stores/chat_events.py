# ── Family 1 boundary (labelings & information-flow) · symbols in docs/NOTATION.md ──
# OBJECT:    the L1 ACTION LOG of the dialogue stratum — an ordered, typed record of WHAT was
#            performed in each Claude Code session (owner_prompt → commit → file_edit → …),
#            extracted deterministically from the transcript's turns + tool records (bp-069 Item 3,
#            dn-agent-taxonomy §2.4). One layer above the L0 chatlog, same DIALOGUE source.
# INVARIANT: every ref is STRUCTURAL — a sha / path / artifact-id / turn_index, NEVER verbatim
#            content ("for prose, read L0"). The store holds no model output; the sole writer is the
#            model-free projector `core/chat_events.py`. `replace-per-session` keeps a re-extracted
#            (grown) session's log consistent — the digest sidecar makes re-projection incremental.
# ENFORCED:  structural — the schema has no `text`/content column a caller could write prose into;
#            the identity key (session_id, ord) makes the log an ordered ledger.
"""The L1 action-log store for the dialogue sensor (bp-069 Item 3).

One row = one typed ACTION in one Claude Code session, at `(session_id, ord)` grain: the actor
(owner|agent), the kind (`prompt|response|commit|file_edit|build_plan|finding|design_note|ratify|
tool_use`), a STRUCTURAL `ref` (sha|path|artifact-id|turn_index — never verbatim content), and the
`turn_index` backpointer into the L0 chatlog (the projection fiber). The projector
(`core/chat_events.py`) is the sole writer; it reads the session's OWN raw transcript via the
chatlog's `transcript_digest` and re-extracts iff that digest changed (`replace_session`).

Sibling-store convention (`code_observations.py`/`chatlog.py`): SQLite, no dedicated cfg path —
`data/chat_events.sqlite` beside the chatlog. A corpus-side derived layer, so it joins
`reset_targets()` (launcher) as a wipe target, rebuilt by re-projection from the immutable rawstore.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # annotation only — avoids a runtime import cycle (core.chat_events imports us)
    from core.chat_events import ChatEvent

from core.config import Config

_DDL = """
CREATE TABLE IF NOT EXISTS chat_events (
    session_id  TEXT NOT NULL,             -- the transcript's session uuid (chain key)
    ord         INTEGER NOT NULL,          -- position in the session's action log (0-based, dense)
    actor       TEXT NOT NULL,             -- 'owner' | 'agent'
    kind        TEXT NOT NULL,             -- the typed action (see module docstring)
    ref         TEXT NOT NULL,             -- STRUCTURAL: sha | path | artifact-id | turn_index
    turn_index  INTEGER NOT NULL,          -- the L0 chatlog backpointer (the projection fiber)
    PRIMARY KEY (session_id, ord)
);
CREATE TABLE IF NOT EXISTS chat_event_digests (
    session_id        TEXT PRIMARY KEY,
    transcript_digest TEXT NOT NULL        -- the raw the log was extracted from (incrementality)
);
"""


@dataclass
class ChatEventStore:
    """The dialogue stratum's L1 action-log table. `replace_session` is the only mutator — it wipes
    and rewrites one session's log atomically (a grown session re-extracts cleanly), and records the
    `transcript_digest` it was extracted from so `digest_for` drives incremental re-projection."""

    path: Path

    def __post_init__(self) -> None:
        if str(self.path) != ":memory:":
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.path))
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_DDL)
        self._conn.commit()

    def replace_session(self, session_id: str, events: Iterable[ChatEvent],
                        transcript_digest: str) -> int:
        """Replace one session's action log wholesale (the extractor is deterministic, so a re-run
        over a grown transcript rewrites the full ordered log) and record the digest it came from.
        Returns the number of events written."""
        rows = [(session_id, e.order, e.actor, e.kind, e.ref, e.turn_index) for e in events]
        with self._conn:
            self._conn.execute("DELETE FROM chat_events WHERE session_id = ?", [session_id])
            self._conn.executemany(
                "INSERT INTO chat_events (session_id, ord, actor, kind, ref, turn_index) "
                "VALUES (?,?,?,?,?,?)", rows)
            self._conn.execute(
                "INSERT INTO chat_event_digests (session_id, transcript_digest) VALUES (?,?) "
                "ON CONFLICT(session_id) DO UPDATE SET "
                "transcript_digest = excluded.transcript_digest",
                [session_id, transcript_digest])
        return len(rows)

    def digest_for(self, session_id: str) -> str | None:
        """The transcript digest this session's log was last extracted from — None if never
        projected. The incrementality signal: unchanged digest ⇒ skip re-extraction (no churn)."""
        row = self._conn.execute(
            "SELECT transcript_digest FROM chat_event_digests WHERE session_id = ?",
            [session_id]).fetchone()
        return str(row[0]) if row else None

    def events_for(self, session_id: str) -> list[dict[str, Any]]:
        """One session's action log, in order (ord)."""
        return [dict(r) for r in self._conn.execute(
            "SELECT * FROM chat_events WHERE session_id = ? ORDER BY ord", [session_id]).fetchall()]

    def count(self) -> int:
        row = self._conn.execute("SELECT count(*) FROM chat_events").fetchone()
        return int(row[0]) if row else 0

    def sessions(self) -> list[str]:
        return [str(r[0]) for r in self._conn.execute(
            "SELECT DISTINCT session_id FROM chat_events ORDER BY session_id").fetchall()]

    def close(self) -> None:
        self._conn.close()


def open_chat_event_store(config: Config | None = None) -> ChatEventStore:
    """`data/chat_events.sqlite` beside the chatlog (the sibling-store convention; no dedicated cfg
    path). Registered in `reset_targets()` as a corpus-side wipe target — rebuilt by re-projection
    from the immutable rawstore (the orchestrator's post-merge step)."""
    from core.config import get_config

    cfg = config or get_config()
    return ChatEventStore(cfg.paths.data_dir / "chat_events.sqlite")
