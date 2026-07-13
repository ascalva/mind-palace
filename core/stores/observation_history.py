# ── Family 1 boundary (labelings & information-flow) · symbols in docs/NOTATION.md ──
# OBJECT:    the observation-history sidecar — the LEDGER-class half of the observation
#            stratum (dn-self-sensing §2.5 ruling): superseded worldview generations,
#            archived verbatim when a bumped interpreter re-projects (bp-018, B-a).
# INVARIANT: append-only. No delete/update method EXISTS on this class — ledger-class is
#            structural, the same move as the no-provenance-parameter mint discipline.
# ENFORCED:  structurally (absent API) + INSERT OR IGNORE on the identity PK, and by the
#            reset guard: `observation_history.sqlite` is in `_RESET_GUARD`
#            (ops/lifecycle/launcher.py), never a reset target — history does not rebuild
#            (the old interpreters no longer exist at HEAD).
"""The history sidecar for the observation-store family (bp-018, dn-self-sensing §2.4/§2.5).

ONE store for the FAMILY, discriminated by member name (`store`: 'code' today; 'agent'
lands with bp-019). When a member store replaces a row because a NEW interpreter version
re-projected the same identity key (archive-then-replace, `code_observations.add_batch`),
the superseded generation lands here verbatim (`row_json`) — so the chain across
`interpreter` at a fixed identity key is the fossil record of the changing worldview
(§2.4's second orthogonal history), queryable oldest-first via `chain()`.

Reset semantics split by re-derivability (owner ruling 2026-07-12): current READINGS are
corpus-class (wiped with the corpus, rebuilt by re-projection from git); this HISTORY is
ledger-class, reset-guarded — a superseded generation was produced by an interpreter that
no longer exists at HEAD, so a wipe would be unrecoverable erasure of the epistemology
record the stratum exists to keep.

No provenance parameter exists anywhere in this module: rows are archived VERBATIM —
whatever class label the member row carried rides inside `row_json`, and this store mints
nothing (it is bookkeeping about generations, not a provenance boundary).

Engine: SQLite — an identity-keyed append-only ledger (the runs/versions/snapshots
convention), same reasoning as the member stores' Q2.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from config.loader import Config

_DDL = """
CREATE TABLE IF NOT EXISTS observation_history (
    store          TEXT NOT NULL,   -- family member: 'code' | 'agent' (bp-019)
    identity_json  TEXT NOT NULL,   -- canonical JSON of the member's identity key
    interpreter    TEXT NOT NULL,   -- the superseded worldview version
    row_json       TEXT NOT NULL,   -- the superseded row, verbatim
    superseded_by  TEXT NOT NULL,   -- the interpreter version that replaced it
    archived_at    TEXT NOT NULL,
    PRIMARY KEY (store, identity_json, interpreter)
);
"""

# The family members' identity-key columns. The pinned `archive()` shape carries rows,
# not identity dicts, so the sidecar derives each row's identity from its member's
# registered key columns — a deliberately LIGHT coupling (key columns only, never the
# member's full schema; the §11 rejection of diff-grain storage was about the latter).
# bp-019 registers 'agent': (commit_sha, stream, subject_id, key).
IDENTITY_KEYS: dict[str, tuple[str, ...]] = {
    "code": ("commit_sha", "path", "qualname"),
}


def _utcnow() -> str:
    return datetime.now(UTC).replace(tzinfo=None).isoformat(timespec="seconds")


def _identity_json(store: str, row: dict[str, Any]) -> str:
    """Canonical (sorted-key, separator-tight) JSON of the member's identity key,
    extracted from a row or an identity dict — any mapping carrying the key columns."""
    keys = IDENTITY_KEYS[store]
    return json.dumps({k: row[k] for k in keys}, sort_keys=True, separators=(",", ":"))


@dataclass
class ObservationHistoryStore:
    """APPEND-ONLY: no delete/update method exists on this class — ledger-class is
    structural, like the no-provenance-parameter move (the test suite sweeps the class
    surface and pins the absence)."""

    path: Path

    def __post_init__(self) -> None:
        if str(self.path) != ":memory:":
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.path))
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_DDL)
        self._conn.commit()

    def archive(self, store: str, rows: Iterable[tuple[dict[str, Any], str, str]]) -> int:
        """Land superseded generations: each element is (identity-keyed row verbatim,
        its interpreter, the superseding interpreter). INSERT OR IGNORE on
        (store, identity_json, interpreter) — re-archiving the same generation (a crashed
        archive-then-replace re-run) changes NOTHING. Returns the number of NEW rows."""
        added = 0
        with self._conn:
            for row, interpreter, superseded_by in rows:
                cur = self._conn.execute(
                    "INSERT OR IGNORE INTO observation_history VALUES (?,?,?,?,?,?)",
                    [store, _identity_json(store, row), interpreter,
                     json.dumps(row, sort_keys=True, separators=(",", ":")),
                     superseded_by, _utcnow()],
                )
                added += cur.rowcount
        return added

    def chain(self, store: str, identity: dict[str, Any]) -> list[dict[str, Any]]:
        """Archived generations at one identity key, oldest first (insertion order —
        supersession only ever appends, so rowid IS the generation order). Each element
        is the superseded row verbatim (parsed `row_json`, its own `interpreter` inside)."""
        return [json.loads(r["row_json"]) for r in self._conn.execute(
            "SELECT row_json FROM observation_history "
            "WHERE store = ? AND identity_json = ? ORDER BY rowid",
            [store, _identity_json(store, identity)],
        ).fetchall()]

    def count(self, store: str | None = None) -> int:
        row = (self._conn.execute("SELECT count(*) FROM observation_history").fetchone()
               if store is None else
               self._conn.execute("SELECT count(*) FROM observation_history WHERE store = ?",
                                  [store]).fetchone())
        return int(row[0]) if row else 0

    def close(self) -> None:
        self._conn.close()


def open_observation_history_store(config: Config | None = None) -> ObservationHistoryStore:
    """The `open_*` helper: `data/observation_history.sqlite` (the sibling-store
    convention, no dedicated cfg path). GUARDED (bp-018 Item 4): named in `_RESET_GUARD`,
    never a reset target — dn-self-sensing §2.5, history does not rebuild."""
    from config.loader import get_config

    cfg = config or get_config()
    return ObservationHistoryStore(cfg.paths.data_dir / "observation_history.sqlite")
