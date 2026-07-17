# ── Family 1 boundary (labelings & information-flow) · symbols in docs/NOTATION.md ──
# OBJECT:    the chat-observation stratum — where φ_chat's per-session, utterance-grain
#            readings of the local Claude Code transcripts land (dn-chat-sensor CS-2/CS-3).
# INVARIANT: every row is ρ ≡ observed; a wrong-class row is UNREPRESENTABLE at this
#            boundary — no provenance parameter exists anywhere in this module's API, and
#            provenance is NEVER derived from `speaker` (CS-2's never-automatic rule).
# ENFORCED:  structural — `ChatUtterance.to_row()` hardcodes `Provenance.OBSERVED` (the
#            DerivedStore/SensedObservation/CodeObservation mint discipline, verbatim); the
#            identity key (session_id, turn_index) makes re-ingest of a frozen session
#            idempotent; a `MirrorView` built over these rows RAISES (mirror-opacity, CS-2).
"""OBSERVED-only store for chat utterances (ratified dn-chat-sensor CS-2/CS-3).

One row = one utterance-grain reading of one Claude Code session transcript: the owner's
and the agent's natural-language prose, extracted at `(session_id, turn_index, speaker,
text)` grain with tool exhaust structurally stripped (the sensor `ops/chat_sensor.py` is
the sole interpreter φ_chat — deterministic, model-free, sole path in). Every row lands
wearing `observed` — there is deliberately NO provenance parameter on any API surface, so
a caller physically cannot launder a chat reading into an authored (or any other) class:
the SAME structural move as `core/stores/code_observations.py` (`CodeObservation.to_row`),
`DerivedStore.add`, and `core/sensing.py`'s `SensedObservation.to_row`. In particular
provenance is NEVER derived from `speaker`: owner utterances and agent utterances both land
`observed` (CS-2 — decided against auto-classing owner CLI prose as `AUTHORED_DIALOGUE`;
CLI sessions mix registers, and machine authorship-inference is exactly what the taxonomy
forbids, `core/provenance.py:74-77`). `/capture` remains the one working promotion path;
the typed `promote(x: Derived[T], cap: OwnerVerdict) -> Authored[T]` seam
(`core/provenance.py:145`) is registered here as a consumer and depended on by nothing.

Mirror-opacity (CS-2): `observed` ∉ `MIRROR_READABLE` (`core/provenance.py:78-80`), so a
`MirrorView` (`core/mirror.py:66`) refuses these rows by construction — the self-model
never reads them, and the proof extends to chat rows without touching the view. The only
typed read container is `ObservedView` (`core/sensing.py:190`); `all_rows` returns
view-compatible dict rows, so the ratified cross-strata correlator (CS-5, the sole future
reader — its own scoped grant) inherits "I read exhaust, never ground truth".

CS-1 (verbatim-first): the sensor stores each closed transcript byte-verbatim in the
immutable rawstore (`core/stores/rawstore.py`) BEFORE any extraction; every row carries the
`transcript_digest` it is recoverable from. This store is the DERIVED, regenerable layer
over those bytes — the same two-layer shape as ingest (raw → derived), no new pattern.

Engine: SQLite — an identity-keyed append-style ledger, the sibling-store convention
(`code_observations.py`), not the DuckDB telemetry lane. Reset semantics (Q6): this store
is CORPUS-side (the observed stratum) and joins `reset_targets()` (`ops/lifecycle/
launcher.py`) as a wipe target — wiped with the corpus, rebuilt by re-ingest from the
IMMUTABLE rawstore (which is NOT a reset target — raw is sacred). [cross-ref: extension,
dn-chat-sensor; the launcher registration is the orchestrator's post-merge step.]

Spine-invisible in v1 (dn-chat-sensor §3): this plan writes NO chain and registers NO
stratum. bp-064 (clock wiring, CS-4) joins the store to the spine as a g1-chained store
(chain-key = session_id, position = turn_index) with session-close cut certificates.
`ts_bookmark` is METADATA ONLY — order is turn index, never wall time (Law C4; CS-4).
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from config.loader import Config
from core.provenance import Provenance

# φ_chat's worldview coordinate (the self-sensor / code-sensor precedent: a deterministic
# interpreter stamps its version so a later grain change is a declared, versioned refactor
# rather than a silent reshaping). v1 extraction: text-block utterances, tool/thinking stripped.
INTERPRETER_VERSION = "1.0.0"

# The speaker vocabulary (CS-3 grain). Derived from `message.role` (user→owner, assistant→
# agent) — a row METADATA field, NEVER a provenance input (CS-2's firewall; the item-1
# falsifier). Both speakers land `observed`.
SPEAKERS = ("owner", "agent")

_DDL = """
CREATE TABLE IF NOT EXISTS chat_utterances (
    session_id        TEXT NOT NULL,             -- the transcript's session uuid (chain key, CS-4)
    turn_index        INTEGER NOT NULL,          -- monotonic per session, extraction order
                                                 -- (the chain position — total per session)
    speaker           TEXT NOT NULL,             -- 'owner' | 'agent' (from message.role; NEVER
                                                 -- a provenance input)
    text              TEXT NOT NULL,             -- the utterance prose (a `text` block's content)
    transcript_digest TEXT NOT NULL,             -- the rawstore SHA-256 the row is recoverable
                                                 -- from (CS-1 — the verbatim archive)
    provenance        TEXT NOT NULL,             -- always 'observed' (nothing else is written)
    ts_bookmark       TEXT NOT NULL DEFAULT '',  -- the wall timestamp — METADATA ONLY, never an
                                                 -- ordering key (Law C4/CS-4)
    observed_at       TEXT NOT NULL,             -- when the extraction landed the row
    interpreter       TEXT NOT NULL DEFAULT '1.0.0',   -- φ_chat's worldview coordinate
    PRIMARY KEY (session_id, turn_index)
);
"""


def _utcnow() -> str:
    return datetime.now(UTC).replace(tzinfo=None).isoformat(timespec="seconds")


@dataclass(frozen=True)
class ChatUtterance:
    """One utterance-grain reading of one session transcript (CS-3 grain, verbatim columns).

    Deliberately has NO provenance field: like `CodeObservation`/`SensedObservation`, the
    class label is minted at `to_row()` with no parameter — the wire payload carries nothing
    a caller could forge a class with, and `speaker` is metadata, never a provenance input."""

    session_id: str
    turn_index: int                     # monotonic per session, extraction order (chain position)
    speaker: str                        # one of SPEAKERS — from message.role, NEVER → provenance
    text: str                           # the utterance prose (a `text` block; tool/thinking gone)
    transcript_digest: str              # the rawstore SHA-256 the utterance is recoverable from
    ts_bookmark: str = ""               # the wall timestamp — METADATA ONLY (Law C4)

    def to_dict(self) -> dict[str, Any]:
        """The wire payload — schema fields only, NO provenance (nothing to forge)."""
        return {
            "session_id": self.session_id,
            "turn_index": self.turn_index,
            "speaker": self.speaker,
            "text": self.text,
            "transcript_digest": self.transcript_digest,
            "ts_bookmark": self.ts_bookmark,
        }

    def to_row(self) -> dict[str, Any]:
        """The observed-tier row. Provenance is HARDCODED — there is no parameter, so no
        caller can launder a chat reading into another class, and `speaker` is NEVER read to
        decide it (CS-2 — the never-automatic rule). `ObservedView` admits these rows;
        `MirrorView` refuses them (mirror-opacity)."""
        return {**self.to_dict(), "provenance": Provenance.OBSERVED.value}


@dataclass
class ChatlogStore:
    """The observed stratum's chat-utterance table. Writes `observed` UNCONDITIONALLY — no
    method on this class accepts a provenance value (the item-1 falsifier, ruled out by
    construction and pinned by test), and none derives provenance from `speaker`. Identity
    key (session_id, turn_index): a re-ingest of a frozen session is idempotent."""

    path: Path

    def __post_init__(self) -> None:
        if str(self.path) != ":memory:":
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.path))
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_DDL)
        self._conn.commit()

    def add_batch(self, utterances: Iterable[ChatUtterance]) -> int:
        """Land utterances, returning the count of NEW rows. Idempotent by the identity key
        (session_id, turn_index): a re-add of an already-stored utterance is a no-op (an
        already-frozen session re-ingested writes 0). `INSERT OR IGNORE` — first write per
        identity wins; a grown open session is out of v1 (Q4 — a session is frozen once
        ingested)."""
        added = 0
        with self._conn:
            for u in utterances:
                cur = self._conn.execute(
                    "INSERT OR IGNORE INTO chat_utterances "
                    "(session_id, turn_index, speaker, text, transcript_digest, "
                    " provenance, ts_bookmark, observed_at, interpreter) "
                    "VALUES (?,?,?,?,?,?,?,?,?)",
                    [u.session_id, u.turn_index, u.speaker, u.text, u.transcript_digest,
                     Provenance.OBSERVED.value, u.ts_bookmark, _utcnow(), INTERPRETER_VERSION],
                )
                added += cur.rowcount
        return added

    # --- reads (view-compatible dict rows) ----------------------------------------------
    def all_rows(self, *,
                 provenances: Iterable[Provenance] | None = None) -> list[dict[str, Any]]:
        """Full scan, optionally restricted to provenance classes (the `RowSource` shape).
        Every stored row is `observed`, so a filter containing OBSERVED sees ALL rows and any
        filter excluding it sees NONE — there is no third case. Ordered by the chain grain
        (session_id, turn_index) for a stable read."""
        rows = [self._row(r) for r in self._conn.execute(
            "SELECT * FROM chat_utterances ORDER BY session_id, turn_index"
        ).fetchall()]
        if provenances is None:
            return rows
        allowed = {Provenance(p).value for p in provenances}
        return [r for r in rows if r["provenance"] in allowed]

    def rows_for(self, session_id: str) -> list[dict[str, Any]]:
        """One session's utterances, in chain order (turn_index)."""
        return [self._row(r) for r in self._conn.execute(
            "SELECT * FROM chat_utterances WHERE session_id = ? ORDER BY turn_index",
            [session_id],
        ).fetchall()]

    def count(self) -> int:
        row = self._conn.execute("SELECT count(*) FROM chat_utterances").fetchone()
        return int(row[0]) if row else 0

    def sessions(self) -> list[str]:
        """The distinct session ids present — the sensor's idempotency read (a session already
        ingested is frozen, Q4)."""
        return [str(r[0]) for r in self._conn.execute(
            "SELECT DISTINCT session_id FROM chat_utterances ORDER BY session_id"
        ).fetchall()]

    @staticmethod
    def _row(r: sqlite3.Row) -> dict[str, Any]:
        return dict(r)

    def close(self) -> None:
        self._conn.close()


def open_chatlog_store(config: Config | None = None) -> ChatlogStore:
    """The `open_*` helper: `data/chatlog.sqlite` (the sibling-store convention beside
    `code_observations`, no dedicated cfg path; registered in `reset_targets()` as a
    corpus-side wipe target — the orchestrator's post-merge step, Q6)."""
    from config.loader import get_config

    cfg = config or get_config()
    return ChatlogStore(cfg.paths.data_dir / "chatlog.sqlite")
