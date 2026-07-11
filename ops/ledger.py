"""The durable propose→approve→execute→validate→rollback ledger (BUILD-SPEC §14; Invariant 5).

This is the Phase-10 upgrade of the in-memory `HumanGate` inbox (ops/gate.py): a SQLite table
that records every self-modification proposal and walks it through a strict lifecycle. The table
is the system's tamper-evident memory of what it tried to change to itself, whether a human let
it, what happened, and — when a change regressed — that it was reversed.

The lifecycle is a finite state machine, enforced here so the safety ordering of §14 cannot be
skipped by a caller (Invariant 5: "no step skipped"):

    PROPOSED ─approve→ APPROVED ─execute→ EXECUTED ─validate→ VALIDATED   (kept)
       │                                      └────rollback→ ROLLED_BACK  (reverted)
       └──────deny──────────────────────→ DENIED

Each transition asserts the current state is exactly its precondition (fail-closed): you cannot
execute something un-approved, validate something un-executed, or approve something already
decided. A model can write a PROPOSED row; only a human moves it to APPROVED; only code that
holds that approval moves it onward. Storage only — the judgment (bounds, the admit predicate,
the apply) lives in ops/levers.py, ops/gate.py, ops/apply.py and is orchestrated by ops/selfmod.py.

Thread-safety mirrors the AttestationStore / JobQueue idiom (PROGRESS 2026-06-27): opened
`check_same_thread=False` with a reentrant lock guarding every method, since a background
scheduler thread may propose while the foreground approves.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from config.loader import Config


class LedgerStatus(StrEnum):
    PROPOSED = "proposed"
    APPROVED = "approved"
    DENIED = "denied"
    EXECUTED = "executed"
    VALIDATED = "validated"      # kept: cleared the gate after execution
    ROLLED_BACK = "rolled_back"  # reverted: regressed an anchor after execution


# The only legal transitions. A method's precondition is the key; its allowed successors the set.
# Anything not listed (e.g. EXECUTED→APPROVED, VALIDATED→anything) is refused — terminal states
# (DENIED, VALIDATED, ROLLED_BACK) have no successors.
_TRANSITIONS: dict[LedgerStatus, frozenset[LedgerStatus]] = {
    LedgerStatus.PROPOSED: frozenset({LedgerStatus.APPROVED, LedgerStatus.DENIED}),
    LedgerStatus.APPROVED: frozenset({LedgerStatus.EXECUTED}),
    LedgerStatus.EXECUTED: frozenset({LedgerStatus.VALIDATED, LedgerStatus.ROLLED_BACK}),
}


def _utcnow() -> str:
    return datetime.now(UTC).replace(tzinfo=None).isoformat(timespec="seconds")


_DDL = """
CREATE TABLE IF NOT EXISTS proposals (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    lever          TEXT NOT NULL,
    current_value  REAL NOT NULL,         -- effective live value at propose time (for the record)
    target_value   REAL NOT NULL,         -- the validated, in-bounds target
    status         TEXT NOT NULL,
    rationale      TEXT NOT NULL DEFAULT '',
    proposer       TEXT NOT NULL DEFAULT '',
    approver       TEXT,                  -- who approved/denied (a human act)
    prior_overlay  REAL,                  -- overlay value to restore on rollback; NULL = was absent
    metrics_json   TEXT,                  -- validation metrics (golden before/after, drift)
    rollback_reason TEXT,
    attestation_id TEXT,                  -- link to a signed gate-decision attestation, if any
    proposed_at    TEXT NOT NULL,
    decided_at     TEXT,
    executed_at    TEXT,
    resolved_at    TEXT                   -- when it reached VALIDATED or ROLLED_BACK
);
CREATE INDEX IF NOT EXISTS proposals_status ON proposals(status);
"""


@dataclass(frozen=True)
class Proposal:
    id: int
    lever: str
    current_value: float
    target_value: float
    status: LedgerStatus
    rationale: str
    proposer: str
    approver: str | None
    prior_overlay: float | None
    metrics: dict[str, Any] | None
    rollback_reason: str | None
    attestation_id: str | None
    proposed_at: str
    decided_at: str | None
    executed_at: str | None
    resolved_at: str | None


def _row_to_proposal(r: sqlite3.Row) -> Proposal:
    return Proposal(
        id=r["id"],
        lever=r["lever"],
        current_value=r["current_value"],
        target_value=r["target_value"],
        status=LedgerStatus(r["status"]),
        rationale=r["rationale"],
        proposer=r["proposer"],
        approver=r["approver"],
        prior_overlay=r["prior_overlay"],
        metrics=json.loads(r["metrics_json"]) if r["metrics_json"] else None,
        rollback_reason=r["rollback_reason"],
        attestation_id=r["attestation_id"],
        proposed_at=r["proposed_at"],
        decided_at=r["decided_at"],
        executed_at=r["executed_at"],
        resolved_at=r["resolved_at"],
    )


class IllegalTransition(RuntimeError):
    """A lifecycle step was attempted from the wrong state (fail-closed §14 ordering guard)."""


@dataclass
class ProposalLedger:
    path: Path

    def __post_init__(self) -> None:
        if str(self.path) != ":memory:":
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(str(self.path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        with self._lock:
            self._conn.executescript(_DDL)
            self._conn.commit()

    # --- reads -------------------------------------------------------------------------------
    def get(self, proposal_id: int) -> Proposal | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM proposals WHERE id = ?", [proposal_id]
            ).fetchone()
        return _row_to_proposal(row) if row else None

    def _require(self, proposal_id: int, expected: LedgerStatus) -> Proposal:
        p = self.get(proposal_id)
        if p is None:
            raise IllegalTransition(f"proposal {proposal_id} not found")
        if p.status is not expected:
            raise IllegalTransition(
                f"proposal {proposal_id} is {p.status}, not {expected} — transition refused"
            )
        return p

    def _get_or_die(self, proposal_id: int) -> Proposal:
        """Re-fetch a row this same method just wrote — never None in practice (a `_require()`
        precondition check or the INSERT itself guarantees the row exists), but `get()`'s
        signature is honestly `Proposal | None` (any id could 404), so narrow it explicitly (T3:
        mypy can't see the existence guarantee across the intervening SQL statement)."""
        rec = self.get(proposal_id)
        assert rec is not None
        return rec

    def all(self) -> list[Proposal]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM proposals ORDER BY id"
            ).fetchall()
        return [_row_to_proposal(r) for r in rows]

    def pending(self) -> list[Proposal]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM proposals WHERE status = ? ORDER BY id",
                [LedgerStatus.PROPOSED],
            ).fetchall()
        return [_row_to_proposal(r) for r in rows]

    # --- lifecycle transitions (each fail-closed on its precondition) ------------------------
    def propose(
        self,
        lever: str,
        current_value: float,
        target_value: float,
        *,
        rationale: str = "",
        proposer: str = "",
    ) -> Proposal:
        """Record a new PROPOSED change. Nothing is applied — this is just the inbox row."""
        with self._lock:
            cur = self._conn.execute(
                "INSERT INTO proposals (lever, current_value, target_value, status, rationale, "
                "proposer, proposed_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                [lever, current_value, target_value, LedgerStatus.PROPOSED, rationale,
                 proposer, _utcnow()],
            )
            self._conn.commit()
            new_id = cur.lastrowid
            assert new_id is not None  # sqlite3: set after a successful INSERT
        rec = self.get(new_id)
        assert rec is not None  # warrant: the row we just committed must be gettable by its id (T3)
        return rec

    def _decide(self, proposal_id: int, status: LedgerStatus, approver: str) -> Proposal:
        self._require(proposal_id, LedgerStatus.PROPOSED)
        if status not in _TRANSITIONS[LedgerStatus.PROPOSED]:
            raise IllegalTransition(f"{status} is not a decision")
        with self._lock:
            self._conn.execute(
                "UPDATE proposals SET status = ?, approver = ?, decided_at = ? WHERE id = ?",
                [status, approver, _utcnow(), proposal_id],
            )
            self._conn.commit()
        return self._get_or_die(proposal_id)

    def approve(self, proposal_id: int, *, approver: str = "owner") -> Proposal:
        """PROPOSED → APPROVED. A human act — never auto-called by the loop (Invariant 5)."""
        return self._decide(proposal_id, LedgerStatus.APPROVED, approver)

    def deny(self, proposal_id: int, *, approver: str = "owner") -> Proposal:
        """PROPOSED → DENIED (terminal)."""
        return self._decide(proposal_id, LedgerStatus.DENIED, approver)

    def mark_executed(self, proposal_id: int, *, prior_overlay: float | None) -> Proposal:
        """APPROVED → EXECUTED. Records the prior overlay value so rollback is exact (NULL means
        the loop introduced the key and rollback should remove it)."""
        self._require(proposal_id, LedgerStatus.APPROVED)
        with self._lock:
            self._conn.execute(
                "UPDATE proposals SET status = ?, prior_overlay = ?, executed_at = ? WHERE id = ?",
                [LedgerStatus.EXECUTED, prior_overlay, _utcnow(), proposal_id],
            )
            self._conn.commit()
        return self._get_or_die(proposal_id)

    def mark_validated(
        self, proposal_id: int, *, metrics: dict[str, Any] | None = None
    ) -> Proposal:
        """EXECUTED → VALIDATED (kept). Stores the validation metrics that cleared the gate."""
        self._require(proposal_id, LedgerStatus.EXECUTED)
        with self._lock:
            self._conn.execute(
                "UPDATE proposals SET status = ?, metrics_json = ?, resolved_at = ? WHERE id = ?",
                [LedgerStatus.VALIDATED,
                 json.dumps(metrics) if metrics is not None else None,
                 _utcnow(), proposal_id],
            )
            self._conn.commit()
        return self._get_or_die(proposal_id)

    def mark_rolled_back(
        self, proposal_id: int, *, reason: str, metrics: dict[str, Any] | None = None
    ) -> Proposal:
        """EXECUTED → ROLLED_BACK (reverted). Records why an anchor regressed."""
        self._require(proposal_id, LedgerStatus.EXECUTED)
        with self._lock:
            self._conn.execute(
                "UPDATE proposals SET status = ?, rollback_reason = ?, metrics_json = ?, "
                "resolved_at = ? WHERE id = ?",
                [LedgerStatus.ROLLED_BACK, reason,
                 json.dumps(metrics) if metrics is not None else None,
                 _utcnow(), proposal_id],
            )
            self._conn.commit()
        return self._get_or_die(proposal_id)

    def attach_attestation(self, proposal_id: int, attestation_id: str) -> None:
        """Link a signed gate-decision attestation to this proposal (records the accessor-join
        seam; optional, used when [attestation] signing is on)."""
        with self._lock:
            self._conn.execute(
                "UPDATE proposals SET attestation_id = ? WHERE id = ?",
                [attestation_id, proposal_id],
            )
            self._conn.commit()

    def close(self) -> None:
        with self._lock:
            self._conn.close()


def open_ledger(config: Config | None = None) -> ProposalLedger:
    from config.loader import get_config

    cfg = config or get_config()
    return ProposalLedger(cfg.selfmod.ledger_db)
