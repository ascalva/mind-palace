"""The self-modification loop (BUILD-SPEC §14, Phase 10 — the last + most privileged capability).

Ties the pieces together into the §14 cycle, with every step held by deterministic code or a
human — never a model:

    propose   a model may write a PROPOSED knob change (ops/levers.ProposedChange — knobs only,
              code/infra structurally unrepresentable). Bounds are checked here; out-of-range
              never reaches the ledger.
    approve   a human moves it to APPROVED (ProposalLedger). The loop never auto-approves on the
              attended path.
    execute   deterministic code writes the knob into the machine-owned overlay (ops/apply.py)
              and records the exact prior value for an exact rollback. No model holds the write.
    validate  run the validator → build the §15 gate decision (ops/gate.GateDecision) from the
              FROZEN golden anchor (capability) + the rolling baseline (acute drift). `conforms`
              (behavioral) stays honestly deferred, exactly as ops/gate documents.
    rollback  if the gate denies, mechanically restore the prior overlay value. Keep-or-revert is
              not a judgment call — it is `gate_admits(...)` returning False.

Two fail-closed switches gate all of this (config/loader.SelfModConfig): `selfmod.enabled` is the
master switch; `selfmod.unattended_enabled` separately gates the ONLY path that skips human
approval (the §14 "safe levers"), and is OFF by default. The owner's Phase-10 ceiling — tune
alignment/quality knobs, treat code and infrastructure as an extremely privileged resource the
loop cannot write — is enforced upstream in ops/levers.py (structural) and here (the switches).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from config.loader import LEVERS_OVERLAY, Config, get_config, refresh_config
from ops.apply import overlay_restore, overlay_set
from ops.gate import GateDecision, gate_admits
from ops.ledger import Proposal, ProposalLedger
from ops.levers import Lever, ProposedChange, get_lever


class SelfModDisabled(RuntimeError):
    """The master switch `[selfmod] enabled` is off — the loop refuses to act (fail-closed)."""


class UnattendedDisabled(RuntimeError):
    """`[selfmod] unattended_enabled` is off — no change may skip the human gate (fail-closed)."""


class NotASafeLever(RuntimeError):
    """A lever not in the pre-declared SAFE_LEVERS set was offered to the unattended path."""


# --- Pre-declared safe levers (the §14 unattended set) ---------------------------------------
#
# The ONLY knobs that MAY be tuned without human approval — and only when `unattended_enabled` is
# also on (it isn't, by default). Kept explicit and minimal: a workload cap whose every in-bounds
# value is harmless. `dream_max_clusters` only bounds HOW MANY dream syntheses run per trough; it
# cannot alter, merge, or drop any authored note (the §8 mirror firewall holds regardless of its
# value), so nudging it within [4, 16] is genuinely low-risk. Everything else routes through the
# human gate. Widening this set is a deliberate, reviewable diff — never a guess.
SAFE_LEVERS: frozenset[str] = frozenset({"dream_max_clusters"})


@dataclass(frozen=True)
class ValidationResult:
    """What the validator measured about the post-change state. Mirrors the gate's MEASURABLE
    conjuncts (ops/gate.GateDecision); `conforms` (behavioral) is deferred, not stubbed True."""

    golden_non_regressing: bool   # frozen golden anchor (capability) didn't drop (§15)
    drift_within_tolerance: bool  # rolling baseline: no acute regression right after the change
    metrics: dict = field(default_factory=dict)


# (lever, applied-value) -> ValidationResult. Injectable, mirroring eval.golden's Retriever seam:
# the default reads the live retriever + frozen baseline; tests pass a deterministic stub.
Validator = Callable[[Lever, float], ValidationResult]


def _section_value(cfg: Config, lever: Lever) -> float:
    return float(getattr(getattr(cfg, lever.section), lever.key))


def _deny_reason(decision: GateDecision) -> str:
    failed = []
    if not decision.golden_non_regressing:
        failed.append("golden-set regressed vs frozen anchor")
    if not decision.drift_within_tolerance:
        failed.append("drift exceeded rolling-baseline tolerance")
    if not decision.approved:
        failed.append("not approved")
    return "; ".join(failed) or "gate denied"


@dataclass
class SelfModLoop:
    """Orchestrates one proposal through the §14 cycle. Construct with the live config + ledger
    for production; tests inject a crafted config, an in-memory ledger, a tmp overlay path, and a
    stub validator."""

    config: Config
    ledger: ProposalLedger
    validator: Validator
    overlay_path: Path = LEVERS_OVERLAY

    def _require_enabled(self) -> None:
        if not self.config.selfmod.enabled:
            raise SelfModDisabled("[selfmod] enabled is false — self-modification is off")

    # --- propose / approve / deny ------------------------------------------------------------
    def propose(self, change: ProposedChange, *, proposer: str = "") -> Proposal:
        """Record a PROPOSED knob change. `change.resolve()` validates bounds first (fail-closed),
        so an unknown lever or out-of-range target raises here and never reaches the ledger."""
        self._require_enabled()
        lever, target = change.resolve()
        current = _section_value(self.config, lever)
        return self.ledger.propose(
            lever.name, current, float(target),
            rationale=change.rationale, proposer=proposer,
        )

    def approve(self, proposal_id: int, *, approver: str = "owner") -> Proposal:
        self._require_enabled()
        return self.ledger.approve(proposal_id, approver=approver)

    def deny(self, proposal_id: int, *, approver: str = "owner") -> Proposal:
        self._require_enabled()
        return self.ledger.deny(proposal_id, approver=approver)

    # --- execute -----------------------------------------------------------------------------
    def execute(self, proposal_id: int) -> Proposal:
        """Apply an APPROVED proposal's knob to the overlay (deterministic code, no model). The
        ledger enforces APPROVED→EXECUTED, so an un-approved proposal cannot be executed."""
        self._require_enabled()
        p = self.ledger.get(proposal_id)
        if p is None:
            raise KeyError(f"proposal {proposal_id} not found")
        lever = get_lever(p.lever)
        prior = overlay_set(lever, p.target_value, self.overlay_path)
        proposal = self.ledger.mark_executed(proposal_id, prior_overlay=prior)
        refresh_config()  # the tuned knob now takes effect for subsequent get_config() callers
        return proposal

    # --- validate (keep) or rollback (revert) ------------------------------------------------
    def validate(self, proposal_id: int) -> Proposal:
        """Run the validator on the EXECUTED change and let the §15 gate decide, mechanically:
        admit → VALIDATED (kept); deny → restore the prior overlay value → ROLLED_BACK."""
        self._require_enabled()
        p = self.ledger.get(proposal_id)
        if p is None:
            raise KeyError(f"proposal {proposal_id} not found")
        lever = get_lever(p.lever)
        result = self.validator(lever, p.target_value)
        decision = GateDecision(
            approved=p.approver is not None,  # a recorded fact: it cleared the human gate
            golden_non_regressing=result.golden_non_regressing,
            drift_within_tolerance=result.drift_within_tolerance,
        )
        if gate_admits(decision):
            return self.ledger.mark_validated(proposal_id, metrics=result.metrics)
        # Mechanical rollback — keep-or-revert is gate_admits(...) == False, not a judgment.
        overlay_restore(lever, p.prior_overlay, self.overlay_path)
        refresh_config()
        return self.ledger.mark_rolled_back(
            proposal_id, reason=_deny_reason(decision), metrics=result.metrics
        )

    # --- the attended convenience: approve→execute→validate in one mechanical step -----------
    def execute_and_validate(self, proposal_id: int) -> Proposal:
        """For an already-APPROVED proposal, run execute then validate. Still no auto-approval —
        approval is the human act that happened before this is called."""
        self.execute(proposal_id)
        return self.validate(proposal_id)

    # --- the unattended safe-lever path (flag-OFF by default) --------------------------------
    def apply_unattended(self, change: ProposedChange, *, proposer: str = "watchdog") -> Proposal:
        """Propose → AUTO-approve → execute → validate, with NO human, for a pre-declared safe
        lever. Gated by BOTH switches: refuses unless `enabled` AND `unattended_enabled`, and the
        lever must be in SAFE_LEVERS. The auto-approval is recorded as approver='unattended' so
        the ledger shows plainly that no human signed off. Default config never reaches the body —
        `unattended_enabled` is off."""
        self._require_enabled()
        if not self.config.selfmod.unattended_enabled:
            raise UnattendedDisabled(
                "[selfmod] unattended_enabled is false — every change needs the human gate"
            )
        if change.lever not in SAFE_LEVERS:
            raise NotASafeLever(
                f"{change.lever!r} is not a safe lever {sorted(SAFE_LEVERS)} — route to the gate"
            )
        proposal = self.propose(change, proposer=proposer)
        self.ledger.approve(proposal.id, approver="unattended")
        return self.execute_and_validate(proposal.id)


def build_golden_validator(
    retriever,
    *,
    golden=None,
    frozen_baseline: dict | None = None,
    rolling_baseline: dict | None = None,
) -> Validator:
    """Default validator: run the frozen golden set through `retriever` and decide both §15
    conjuncts from it. `golden_non_regressing` is measured against the FROZEN anchor (baseline.json,
    Invariant 9); `drift_within_tolerance` against a supplied `rolling_baseline` (the adapting
    before/after) when present — together they defeat the boiling-frog problem (§15): a change can
    pass the rolling check yet still be caught by the frozen anchor, which triggers rollback.

    Imports eval lazily so ops/selfmod stays importable without the eval fixtures loaded."""
    from eval.golden import evaluate, load_baseline, load_golden_set, regressions

    golden = golden or load_golden_set()
    frozen_baseline = frozen_baseline or load_baseline()

    def _validate(lever: Lever, value: float) -> ValidationResult:
        report = evaluate(golden, retriever)
        after = report.as_metrics()
        frozen_regs = regressions(report, frozen_baseline)
        drift_ok = True
        rolling_regs: list[str] = []
        if rolling_baseline is not None:
            rolling_regs = regressions(report, rolling_baseline)
            drift_ok = not rolling_regs
        return ValidationResult(
            golden_non_regressing=not frozen_regs,
            drift_within_tolerance=drift_ok,
            metrics={
                "lever": lever.name,
                "value": value,
                "after": after,
                "frozen_regressions": frozen_regs,
                "rolling_regressions": rolling_regs,
            },
        )

    return _validate


def build_loop(
    validator: Validator,
    *,
    config: Config | None = None,
    ledger: ProposalLedger | None = None,
) -> SelfModLoop:
    """Wire a loop from live config + the durable ledger. The validator is required (the caller
    decides whether to use `build_golden_validator` with a live retriever or a custom one)."""
    from ops.ledger import open_ledger

    cfg = config or get_config()
    return SelfModLoop(config=cfg, ledger=ledger or open_ledger(cfg), validator=validator)
