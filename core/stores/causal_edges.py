# ── Family 1 boundary (labelings & information-flow) · symbols in docs/NOTATION.md ──
# OBJECT:    the C-fiber proven-edge store — the first full INTEGRATOR's output (bp-071,
#            dn-agent-taxonomy §2.5). One row = one causal-witnessed edge from a DIALOGUE
#            action (a session's L1 event) to the endpoint that action produced: a commit,
#            a file, or a doc artifact. Each edge carries its WITNESS (transcript_digest,
#            turn_index) and its PAIR-CUT (transcript_digest, full commit sha).
# INVARIANT: every edge is the image of ONE L1 tool record under a deterministic resolver
#            (the witness law — E_proven, re-derivable from retained raw + the ledger). No
#            edge is inferred, joined, or time-derived; no `dst` carries verbatim content
#            (sha | path | artifact-id only). C-fiber only in v1 (F declared-but-unfed —
#            no read/cite endpoint survives L1; finding-0111).
# ENFORCED:  structural — the schema has no content column; the content-derived `edge_id`
#            makes re-integration idempotent; `replace_session` keeps a grown session's
#            edge set consistent (the digest sidecar drives incremental re-integration,
#            the landed L1 `replace_session` pattern). Guard: tests/unit/test_causal_edges.py.
"""The C-fiber causal-edge store — the integrator's proven output (bp-071 Item 1).

One row = one proven cross-strata edge: a DIALOGUE L1 action → the endpoint it produced.
Two species (finding-0111): a `commit` event resolves (by abbreviated-sha prefix match) to a
ledger commit — `dst_type='commit'`, `pair_cut_sha`=the full sha (the (digest, sha) consistent
cut); a `file_edit`/`build_plan`/`finding`/`design_note` event mints its endpoint directly (the
Write tool record is the proof) — `dst_type='file'|'doc'`, `pair_cut_sha=''` (a working-tree
write has no commit anchor). The endpoints are NOT fanned out from a commit's file set: the
commit ledger stores the full tree, not the diff, so fanning would be an inferred edge (the
falsifier). Composing action→commit with commit→file is Δ's `ComposedGraph` job (C≠D composition).

Sibling-store convention (`chat_events.py`/`reference_edges.py`): SQLite, no dedicated cfg path —
`data/causal_edges.sqlite` beside the L1 store. A corpus-side derived layer (a pure function of
retained raw + the ledger), so it joins `reset_targets()` and rebuilds by re-integration.
"""

from __future__ import annotations

import hashlib
import sqlite3
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from core.config import Config

# The edge fiber vocabulary this store admits. v1 mints only C (causal-witnessed production);
# F (citation) is a declared-but-unfed capability of the integrator scope — no read/cite
# endpoint survives the landed L1 (finding-0111). D is never an integrator's (dn-agent-taxonomy).
EDGE_KINDS = frozenset({"C", "F"})
# The endpoint species a proven edge may point at (dn-agent-taxonomy §2.5; finding-0111).
DST_TYPES = frozenset({"commit", "file", "doc"})

_DDL = """
CREATE TABLE IF NOT EXISTS causal_edges (
    edge_id        TEXT PRIMARY KEY,       -- content id: (digest, event_order, dst_type, dst)
    session_id     TEXT NOT NULL,          -- the originating session (chain key)
    event_order    INTEGER NOT NULL,       -- the L1 event's ord within its session
    kind           TEXT NOT NULL,          -- 'C' (v1) | 'F' (reserved) — the fiber
    dst_type       TEXT NOT NULL,          -- 'commit' | 'file' | 'doc'
    dst            TEXT NOT NULL,          -- sha | path | artifact-id — NEVER content
    witness_digest TEXT NOT NULL,          -- transcript_digest (witness + first pair-cut token)
    witness_turn   INTEGER NOT NULL,       -- turn_index — the dialogue turn the action ran under
    pair_cut_sha   TEXT NOT NULL DEFAULT '' -- full sha (commit edges) | '' (working-tree writes)
);
CREATE INDEX IF NOT EXISTS causal_edges_session ON causal_edges(session_id);
CREATE INDEX IF NOT EXISTS causal_edges_dst ON causal_edges(dst_type, dst);
CREATE TABLE IF NOT EXISTS causal_edge_digests (
    session_id        TEXT PRIMARY KEY,
    transcript_digest TEXT NOT NULL        -- the L1 digest the session's edges were minted from
);
"""


def _edge_id(witness_digest: str, event_order: int, dst_type: str, dst: str) -> str:
    """Content-derived identity over the witness-keyed tuple (finding-0111 Q3): the digest
    pins the raw the edge was read from, `event_order` the L1 event, `(dst_type, dst)` the
    endpoint — so re-integrating the same (session-digest) is a byte-identical no-op."""
    payload = "\x00".join([witness_digest, str(event_order), dst_type, dst])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


@dataclass(frozen=True)
class CausalEdge:
    """One proven C-fiber edge: a DIALOGUE action → its produced endpoint. `dst` is STRUCTURAL
    (sha | path | artifact-id). The witness is `(witness_digest, witness_turn)` plus the L1
    event's own `(kind, ref)`; the pair-cut is `(witness_digest, pair_cut_sha)` — a full sha for
    a commit edge, `''` for a working-tree write (no cross-clock cut)."""

    edge_id: str
    session_id: str
    event_order: int
    kind: str            # one of EDGE_KINDS (v1: always 'C')
    dst_type: str        # one of DST_TYPES
    dst: str             # sha | path | artifact-id — never content
    witness_digest: str
    witness_turn: int
    pair_cut_sha: str = ""

    @classmethod
    def mint(cls, *, session_id: str, event_order: int, kind: str, dst_type: str, dst: str,
             witness_digest: str, witness_turn: int, pair_cut_sha: str = "") -> CausalEdge:
        """Construct with the content-derived identity; validates the closed vocabularies at the
        boundary (a typo'd fiber/dst_type is unrepresentable in the store)."""
        if kind not in EDGE_KINDS:
            raise ValueError(f"kind must be one of {sorted(EDGE_KINDS)}, got {kind!r}")
        if dst_type not in DST_TYPES:
            raise ValueError(f"dst_type must be one of {sorted(DST_TYPES)}, got {dst_type!r}")
        return cls(
            edge_id=_edge_id(witness_digest, event_order, dst_type, dst),
            session_id=session_id, event_order=event_order, kind=kind,
            dst_type=dst_type, dst=dst, witness_digest=witness_digest,
            witness_turn=witness_turn, pair_cut_sha=pair_cut_sha,
        )


@dataclass
class CausalEdgeStore:
    """The C-fiber edge table. `replace_session` is the only mutator — it wipes and rewrites one
    session's edges atomically (a grown session re-integrates cleanly) and records the L1 digest
    they were minted from, so `digest_for` drives incremental re-integration (the landed L1
    pattern). The sole writer is the model-free integrator (`core/integrator.py`)."""

    path: Path

    def __post_init__(self) -> None:
        if str(self.path) != ":memory:":
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.path))
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_DDL)
        self._conn.commit()

    def replace_session(self, session_id: str, edges: Iterable[CausalEdge],
                        transcript_digest: str) -> int:
        """Replace one session's edges wholesale (the resolver is deterministic, so a re-run over
        a grown transcript rewrites the full set) and record the digest they came from. Returns
        the number of edges written. Every edge must belong to `session_id` — a mismatch would
        orphan a row past the keyed DELETE, so it fails loudly rather than silently."""
        edges = list(edges)
        stray = [e.session_id for e in edges if e.session_id != session_id]
        if stray:
            raise ValueError(f"replace_session({session_id!r}) got edges for other sessions: "
                             f"{sorted(set(stray))}")
        rows = [(e.edge_id, e.session_id, e.event_order, e.kind, e.dst_type, e.dst,
                 e.witness_digest, e.witness_turn, e.pair_cut_sha) for e in edges]
        with self._conn:
            self._conn.execute("DELETE FROM causal_edges WHERE session_id = ?", [session_id])
            self._conn.executemany(
                "INSERT OR REPLACE INTO causal_edges (edge_id, session_id, event_order, kind, "
                "dst_type, dst, witness_digest, witness_turn, pair_cut_sha) "
                "VALUES (?,?,?,?,?,?,?,?,?)", rows)
            self._conn.execute(
                "INSERT INTO causal_edge_digests (session_id, transcript_digest) VALUES (?,?) "
                "ON CONFLICT(session_id) DO UPDATE SET "
                "transcript_digest = excluded.transcript_digest",
                [session_id, transcript_digest])
        return len(rows)

    def digest_for(self, session_id: str) -> str | None:
        """The L1 digest this session's edges were last minted from — None if never integrated.
        The incrementality signal: unchanged digest ⇒ skip re-integration (no churn)."""
        row = self._conn.execute(
            "SELECT transcript_digest FROM causal_edge_digests WHERE session_id = ?",
            [session_id]).fetchone()
        return str(row[0]) if row else None

    def edges_for(self, session_id: str) -> list[dict[str, Any]]:
        """One session's edges, in event order."""
        return [dict(r) for r in self._conn.execute(
            "SELECT * FROM causal_edges WHERE session_id = ? ORDER BY event_order, dst_type, dst",
            [session_id]).fetchall()]

    def all_edges(self) -> list[dict[str, Any]]:
        return [dict(r) for r in self._conn.execute(
            "SELECT * FROM causal_edges ORDER BY session_id, event_order, dst_type, dst"
        ).fetchall()]

    def count(self) -> int:
        row = self._conn.execute("SELECT count(*) FROM causal_edges").fetchone()
        return int(row[0]) if row else 0

    def sessions_with_edges(self) -> list[str]:
        return [str(r[0]) for r in self._conn.execute(
            "SELECT DISTINCT session_id FROM causal_edges ORDER BY session_id").fetchall()]

    def close(self) -> None:
        self._conn.close()


def open_causal_edge_store(config: Config | None = None) -> CausalEdgeStore:
    """`data/causal_edges.sqlite` beside the L1 store (the sibling-store convention; no dedicated
    cfg path). Registered in `reset_targets()` as a corpus-side wipe target — rebuilt by
    re-integration from the immutable rawstore-backed L1 + the commit ledger."""
    from core.config import get_config

    cfg = config or get_config()
    return CausalEdgeStore(cfg.paths.data_dir / "causal_edges.sqlite")
