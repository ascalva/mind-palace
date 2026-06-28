"""The human gate — seam for routing privileged requests (BUILD-SPEC §10, §14; Invariant 5).

When the factory is asked for capability beyond an agent's scope ceiling, it routes the
request HERE instead of minting a privileged agent (§10). This is the Phase-5 seam: it
records the request as PENDING so nothing privileged ever happens unattended (Invariant 5,
Constitution §II.4). The full propose → approve → execute → validate → rollback ledger landed
in Phase 10 as the durable `ops/ledger.ProposalLedger` (orchestrated by `ops/selfmod.py`); this
module remains the lightweight in-memory inbox for routed privileged requests, plus the decidable
gate predicate (`gate_admits`) that the Phase-10 validate step consumes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class GateStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"


# --- The admission predicate G(Δ, s) (Invariant 12; gaps G5) ---------------------
#
# The self-modification gate admits a change Δ to state s iff `G(Δ, s)` holds; otherwise the
# state is unchanged (`s' = Δ·s iff G(Δ,s) else s`). The *specified* guard is
#
#     G(Δ,s) = approved(Δ) ∧ golden(Δ·s) ≥ golden(B) ∧ D(Δ·s) ≤ Θ ∧ conforms(Δ·s).
#
# The subjective `conforms` conjunct needs the small-model judge + frozen baseline, which is
# deferred (Phase 10, like the §4 self-check judge seam). So the HONEST live guard (gap G5) is
#
#     G_now(Δ,s) = approved(Δ) ∧ golden(Δ·s) ≥ golden(B) ∧ D(Δ·s) ≤ Θ        (no `conforms` yet).
#
# `conforms` is NOT defaulted to True — silently passing an unevaluated condition would
# overclaim. It is simply absent from the admissible decision until the judge lands; until
# then self-modification is gated behind human approval + the two *measurable* conjuncts.
#
# This predicate is a pure, data-in / bool-out decision: it takes only facts ABOUT Δ·s and
# returns admit/deny. There is no callback to Δ and no apply step here, so **Δ can never
# self-apply through the gate** (I12) — only code that holds the human approval applies a Δ,
# and only when this returns True. The propose→approve→execute→validate→rollback loop that
# *uses* this is `ops/selfmod.SelfModLoop.validate` (Phase 10); this is its decidable core,
# FSM-checked in test_gate_fsm.py.


@dataclass(frozen=True)
class GateDecision:
    """The measurable facts the live gate decides on (gap G5). `conforms` is intentionally
    absent — it is deferred, not assumed."""

    approved: bool                  # a human approved Δ (never auto-approved)
    golden_non_regressing: bool     # golden(Δ·s) ≥ golden(B): the frozen golden set didn't drop
    drift_within_tolerance: bool    # D(Δ·s) ≤ Θ: drift vs the frozen baseline is within band


def gate_admits(decision: GateDecision) -> bool:
    """G_now(Δ,s) = approved ∧ golden-non-regressing ∧ drift-within-tolerance (gap G5).

    Fail-closed: every conjunct must hold; any False (or unknown, surfaced as False) denies.
    The deferred `conforms` conjunct is omitted honestly rather than stubbed True."""
    return (
        decision.approved
        and decision.golden_non_regressing
        and decision.drift_within_tolerance
    )


@dataclass(frozen=True)
class GateRequest:
    id: int
    kind: str             # "privileged_mint" | "out_of_scope_tool" | ...
    detail: str
    status: GateStatus
    created_at: str
    agent: str | None = None


def _utcnow() -> str:
    return datetime.now(UTC).replace(tzinfo=None).isoformat(timespec="seconds")


@dataclass
class HumanGate:
    """Records routed requests. Nothing is auto-approved — approval is a human act
    (Phase 10 wires the durable SQLite ledger + the approve/execute/validate/rollback loop)."""

    _requests: list[GateRequest] = field(default_factory=list)

    def submit(self, kind: str, detail: str, *, agent: str | None = None) -> GateRequest:
        req = GateRequest(
            id=len(self._requests) + 1,
            kind=kind,
            detail=detail,
            status=GateStatus.PENDING,
            created_at=_utcnow(),
            agent=agent,
        )
        self._requests.append(req)
        return req

    def pending(self) -> list[GateRequest]:
        return [r for r in self._requests if r.status is GateStatus.PENDING]

    def all(self) -> list[GateRequest]:
        return list(self._requests)
