# ── Family 3 boundary (guarded transition systems) · symbols in docs/NOTATION.md ──
# OBJECT:    the durable effect lifecycle — the §14 propose→approve→execute→validate/rollback FSM,
#            the effector analogue of ops/ledger.ProposalLedger (hands-and-the-effector-layer.md
#            §5, §10; G2 deferred this "to where there is world state to roll back" — G5).
# INVARIANT: every transition asserts its exact precondition (no step skipped, I5); an approval
#            recorded for a class must COVER w(β) for that class (a LIGHT ack cannot approve an
#            irreversible effect); terminal states have no successors.
# ENFORCED:  structural — _require() fail-closes on the wrong state; approve() fail-closes on an
#            under-strength approval; the table exposes append/transition, never delete/rewrite.
"""The durable effect ledger (Track G, item G5).

The in-memory `HumanGate` records that a routed request happened; this SQLite table is the
tamper-evident memory of what the hands tried to DO in the world, whether the owner let them, what
was staged, and — for a reversible write the owner undid — that it was rolled back. It is the
effector twin of `ops/ledger.ProposalLedger` (which tracks self-mod knob changes); it reuses the
*same* §14 lifecycle FSM (`ops.ledger.LedgerStatus` / `IllegalTransition`) because it is the same
machine, wider domain (§6) — only the recorded facts differ (an actuator + params, not a lever +
numeric target).

The lifecycle, enforced here so a caller cannot skip the safety ordering (I5):

    PROPOSED ─approve→ APPROVED ─execute→ EXECUTED ─validate→ VALIDATED   (kept)
       │                                     └────rollback→ ROLLED_BACK   (undone)
       └──────deny──────────────────────→ DENIED

`artifact_ref` is what rollback acts on: the staged draft path for a reversible write (the edge
effector unlinks it), or the attested send-record id for an irreversible one (which has no world
undo — that is *why* it is full-gated; the ledger still records it happened). Storage only: the
judgment (the gate predicate, the class→w(β) mapping, the actual staging/send) lives in
`ops/effect_gate.py`, `ops/effects.py`, `ops/effect_exec.py`, and the edge effectors.

Thread-safety mirrors `ProposalLedger` / `AttestationStore`: opened `check_same_thread=False` with a
reentrant lock guarding every method (a scheduler thread may propose while the owner approves).
"""

from __future__ import annotations

import json
import sqlite3
import threading
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from config.loader import Config
from ops.effects import ApprovalStrength, ReversibilityClass, required_approval
from ops.ledger import IllegalTransition, LedgerStatus

# The same §14 FSM as ProposalLedger (imported enum ⇒ no drift). A method's precondition is the key;
# its allowed successors the set. Terminal states (DENIED, VALIDATED, ROLLED_BACK) are absent ⇒ no
# successors — refused.
_TRANSITIONS: dict[LedgerStatus, frozenset[LedgerStatus]] = {
    LedgerStatus.PROPOSED: frozenset({LedgerStatus.APPROVED, LedgerStatus.DENIED}),
    LedgerStatus.APPROVED: frozenset({LedgerStatus.EXECUTED}),
    LedgerStatus.EXECUTED: frozenset({LedgerStatus.VALIDATED, LedgerStatus.ROLLED_BACK}),
}


def _utcnow() -> str:
    return datetime.now(UTC).replace(tzinfo=None).isoformat(timespec="seconds")


_DDL = """
CREATE TABLE IF NOT EXISTS effects (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    actuator       TEXT NOT NULL,
    reversibility  INTEGER NOT NULL,      -- ReversibilityClass value (0 sensing / 1 rev / 2 irrev)
    scope          TEXT NOT NULL DEFAULT '',
    params_json    TEXT NOT NULL DEFAULT '{}',
    status         TEXT NOT NULL,
    rationale      TEXT NOT NULL DEFAULT '',
    proposer       TEXT NOT NULL DEFAULT '',
    approver       TEXT,                  -- who approved/denied (a human act)
    approval_strength INTEGER,            -- ApprovalStrength held at approval; must cover w(β)
    artifact_ref   TEXT,                  -- staged draft path (rev) / send-record id (irrev)
    attestation_id TEXT,                  -- link to the attested action record
    rollback_reason TEXT,
    proposed_at    TEXT NOT NULL,
    decided_at     TEXT,
    executed_at    TEXT,
    resolved_at    TEXT                   -- when it reached VALIDATED or ROLLED_BACK
);
CREATE INDEX IF NOT EXISTS effects_status ON effects(status);
"""


@dataclass(frozen=True)
class EffectRecord:
    id: int
    actuator: str
    reversibility: ReversibilityClass
    scope: str
    params: dict[str, str]
    status: LedgerStatus
    rationale: str
    proposer: str
    approver: str | None
    approval_strength: ApprovalStrength | None
    artifact_ref: str | None
    attestation_id: str | None
    rollback_reason: str | None
    proposed_at: str
    decided_at: str | None
    executed_at: str | None
    resolved_at: str | None


def _row_to_record(r: sqlite3.Row) -> EffectRecord:
    return EffectRecord(
        id=r["id"],
        actuator=r["actuator"],
        reversibility=ReversibilityClass(r["reversibility"]),
        scope=r["scope"],
        params=json.loads(r["params_json"]) if r["params_json"] else {},
        status=LedgerStatus(r["status"]),
        rationale=r["rationale"],
        proposer=r["proposer"],
        approver=r["approver"],
        approval_strength=(ApprovalStrength(r["approval_strength"])
                           if r["approval_strength"] is not None else None),
        artifact_ref=r["artifact_ref"],
        attestation_id=r["attestation_id"],
        rollback_reason=r["rollback_reason"],
        proposed_at=r["proposed_at"],
        decided_at=r["decided_at"],
        executed_at=r["executed_at"],
        resolved_at=r["resolved_at"],
    )


@dataclass
class EffectLedger:
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

    # --- reads -----------------------------------------------------------------------------------
    def get(self, effect_id: int) -> EffectRecord | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM effects WHERE id = ?", [effect_id]
            ).fetchone()
        return _row_to_record(row) if row else None

    def all(self) -> list[EffectRecord]:
        with self._lock:
            rows = self._conn.execute("SELECT * FROM effects ORDER BY id").fetchall()
        return [_row_to_record(r) for r in rows]

    def pending(self) -> list[EffectRecord]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM effects WHERE status = ? ORDER BY id", [LedgerStatus.PROPOSED]
            ).fetchall()
        return [_row_to_record(r) for r in rows]

    def _require(self, effect_id: int, expected: LedgerStatus) -> EffectRecord:
        rec = self.get(effect_id)
        if rec is None:
            raise IllegalTransition(f"effect {effect_id} not found")
        if rec.status is not expected:
            raise IllegalTransition(
                f"effect {effect_id} is {rec.status}, not {expected} — transition refused"
            )
        return rec

    # --- lifecycle transitions (each fail-closed on its precondition) ----------------------------
    def propose(
        self,
        actuator: str,
        reversibility: ReversibilityClass,
        *,
        scope: str = "",
        params: dict[str, str] | None = None,
        rationale: str = "",
        proposer: str = "",
    ) -> EffectRecord:
        """Record a new PROPOSED effect. Nothing is staged or sent — this is only the inbox row
        (the model advises; a human moves it to APPROVED; only then does code act)."""
        with self._lock:
            cur = self._conn.execute(
                "INSERT INTO effects (actuator, reversibility, scope, params_json, status, "
                "rationale, proposer, proposed_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                [actuator, int(reversibility), scope,
                 json.dumps(params or {}, separators=(",", ":")),
                 LedgerStatus.PROPOSED, rationale, proposer, _utcnow()],
            )
            self._conn.commit()
            new_id = cur.lastrowid
            assert new_id is not None  # sqlite3: set after a successful INSERT
        rec = self.get(new_id)
        assert rec is not None  # the row we just committed must be gettable by its own id
        return rec

    def approve(
        self, effect_id: int, *, approver: str = "owner",
        strength: ApprovalStrength = ApprovalStrength.LIGHT,
    ) -> EffectRecord:
        """PROPOSED → APPROVED, recording the strength of the human act. Fail-closed if the strength
        does not COVER w(β) for the effect's class — you cannot record a LIGHT ack for an
        irreversible effect (the same invariant `Effect.__post_init__` enforces, checked earlier
        here so the ledger never holds an under-approved record). Never auto-called."""
        rec = self._require(effect_id, LedgerStatus.PROPOSED)
        needed = required_approval(rec.reversibility)
        if strength < needed:
            raise IllegalTransition(
                f"effect {effect_id} is {rec.reversibility.name} and needs {needed.name} approval; "
                f"a {strength.name} act does not cover w(β) (§4)"
            )
        with self._lock:
            self._conn.execute(
                "UPDATE effects SET status = ?, approver = ?, approval_strength = ?, "
                "decided_at = ? WHERE id = ?",
                [LedgerStatus.APPROVED, approver, int(strength), _utcnow(), effect_id],
            )
            self._conn.commit()
        return self.get(effect_id)  # type: ignore[return-value]

    def deny(self, effect_id: int, *, approver: str = "owner") -> EffectRecord:
        """PROPOSED → DENIED (terminal)."""
        self._require(effect_id, LedgerStatus.PROPOSED)
        with self._lock:
            self._conn.execute(
                "UPDATE effects SET status = ?, approver = ?, decided_at = ? WHERE id = ?",
                [LedgerStatus.DENIED, approver, _utcnow(), effect_id],
            )
            self._conn.commit()
        return self.get(effect_id)  # type: ignore[return-value]

    def mark_executed(self, effect_id: int, *, artifact_ref: str | None = None) -> EffectRecord:
        """APPROVED → EXECUTED. Records the artifact rollback acts on (a staged draft path for a
        reversible write; an attested send-record id for an irreversible one)."""
        self._require(effect_id, LedgerStatus.APPROVED)
        with self._lock:
            self._conn.execute(
                "UPDATE effects SET status = ?, artifact_ref = ?, executed_at = ? WHERE id = ?",
                [LedgerStatus.EXECUTED, artifact_ref, _utcnow(), effect_id],
            )
            self._conn.commit()
        return self.get(effect_id)  # type: ignore[return-value]

    def mark_validated(self, effect_id: int) -> EffectRecord:
        """EXECUTED → VALIDATED (kept — the staged artifact stands / the send is confirmed)."""
        self._require(effect_id, LedgerStatus.EXECUTED)
        with self._lock:
            self._conn.execute(
                "UPDATE effects SET status = ?, resolved_at = ? WHERE id = ?",
                [LedgerStatus.VALIDATED, _utcnow(), effect_id],
            )
            self._conn.commit()
        return self.get(effect_id)  # type: ignore[return-value]

    def mark_rolled_back(self, effect_id: int, *, reason: str) -> EffectRecord:
        """EXECUTED → ROLLED_BACK (undone). For a reversible write the edge effector has removed the
        staged artifact; this records why. (An irreversible effect has no world undo — the full gate
        is the point; a rollback here means the SEND itself failed, not an un-send.)"""
        self._require(effect_id, LedgerStatus.EXECUTED)
        with self._lock:
            self._conn.execute(
                "UPDATE effects SET status = ?, rollback_reason = ?, resolved_at = ? WHERE id = ?",
                [LedgerStatus.ROLLED_BACK, reason, _utcnow(), effect_id],
            )
            self._conn.commit()
        return self.get(effect_id)  # type: ignore[return-value]

    def attach_attestation(self, effect_id: int, attestation_id: str) -> None:
        """Link the attested action record to this effect (records the accessor-join seam)."""
        with self._lock:
            self._conn.execute(
                "UPDATE effects SET attestation_id = ? WHERE id = ?", [attestation_id, effect_id]
            )
            self._conn.commit()

    def close(self) -> None:
        with self._lock:
            self._conn.close()


def open_effect_ledger(config: Config | None = None) -> EffectLedger:
    """Wire the effect ledger against the configured effectors data dir (beside sensing handoff).
    Independent of `[effectors] enabled`: the ledger is a record, safe to open read-only for audit
    even when the hands are off."""
    from config.loader import get_config

    cfg = config or get_config()
    return EffectLedger(cfg.effectors.ledger_db)
