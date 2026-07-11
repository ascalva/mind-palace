"""Exhaustive FSM check of the effect gate (Track G item G2; the Phase-10 gate, wider domain).

`G_effect(E, world) = proposed ∧ approved_{w(β)} ∧ scoped_cap_valid ∧ attested` (§6) is a
predicate over (reversibility class × proposed × approval strength × capability × attested).
That space is small enough to enumerate in full — 3 × 2 × 3 × 2 × 2 = 72 states — exactly like
the 8-state config gate (test_gate_fsm.py). We assert: it admits ONLY when every conjunct holds
with an approval that *covers* w(β) for the class; the approval requirement is computed from the
class (never a weaker one a decision could claim); and the effect can never self-apply through
the gate (the predicate is data-in/bool-out with no effect handle and no apply callback).
"""

from __future__ import annotations

import inspect
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from itertools import product

from ops.effect_gate import (
    EffectGateDecision,
    capability_covers,
    effect_gate_admits,
    get_actuator,
)
from ops.effects import (
    ApprovalStrength,
    ReversibilityClass,
    ScopedCapability,
    required_approval,
)


def test_effect_gate_admits_exactly_when_all_conjuncts_hold():
    admitted = []
    for rev, proposed, approval, cap_valid, attested in product(
        list(ReversibilityClass),
        [False, True],
        list(ApprovalStrength),
        [False, True],
        [False, True],
    ):
        decision = EffectGateDecision(
            reversibility=rev,
            proposed=proposed,
            approval=approval,
            capability_valid=cap_valid,
            attested=attested,
        )
        result = effect_gate_admits(decision)
        # The predicate IS the four-way conjunction, with the approval conjunct comparing the
        # held strength against the class's REQUIRED strength w(β).
        expected = (
            proposed
            and approval >= required_approval(rev)
            and cap_valid
            and attested
        )
        assert result == expected
        if result:
            admitted.append((rev, proposed, approval, cap_valid, attested))

    # Every admitted state has all three non-approval conjuncts true and an approval covering
    # its class — and nothing weaker ever admits (fail-closed).
    for rev, proposed, approval, cap_valid, attested in admitted:
        assert proposed and cap_valid and attested
        assert approval >= required_approval(rev)


def test_sensing_admits_with_no_human_approval_but_still_needs_the_other_conjuncts():
    # β = 0: w(β) = NONE, so approval=NONE admits — IF proposed, capability-valid, attested.
    base = EffectGateDecision(
        reversibility=ReversibilityClass.SENSING,
        approval=ApprovalStrength.NONE,
        proposed=True,
        capability_valid=True,
        attested=True,
    )
    assert effect_gate_admits(base) is True
    # Drop any single other conjunct → denied (sensing is not a free pass).
    assert effect_gate_admits(replace(base, proposed=False)) is False
    assert effect_gate_admits(replace(base, capability_valid=False)) is False
    assert effect_gate_admits(replace(base, attested=False)) is False


def test_irreversible_requires_the_full_gate_strength():
    # An IRREVERSIBLE effect with everything else true but only LIGHT approval is denied;
    # only FULL_GATE admits. This is w(β) selecting the approval weight (§4).
    base = EffectGateDecision(
        reversibility=ReversibilityClass.IRREVERSIBLE,
        proposed=True,
        approval=ApprovalStrength.NONE,
        capability_valid=True,
        attested=True,
    )
    def admits(approval: ApprovalStrength) -> bool:
        return effect_gate_admits(replace(base, approval=approval))

    assert admits(ApprovalStrength.NONE) is False
    assert admits(ApprovalStrength.LIGHT) is False
    assert admits(ApprovalStrength.FULL_GATE) is True


def test_no_capability_denies_even_a_fully_approved_effect():
    # The confused-deputy answer: no minted scope ⇒ no effect, whatever the approval says.
    decision = EffectGateDecision(
        reversibility=ReversibilityClass.IRREVERSIBLE,
        proposed=True,
        approval=ApprovalStrength.FULL_GATE,
        capability_valid=False,
        attested=True,
    )
    assert effect_gate_admits(decision) is False


def test_required_strength_is_computed_from_the_class_not_a_decision_field():
    # A decision cannot understate its own requirement: there is no 'required' field; the guard
    # derives it from `reversibility` via w(β). So the fields are exactly the recorded facts.
    fields = set(inspect.signature(EffectGateDecision).parameters)
    assert fields == {"reversibility", "proposed", "approval", "capability_valid", "attested"}
    assert "required" not in fields and "required_approval" not in fields


def test_effect_cannot_self_apply_through_the_gate():
    # I12 inherited: the gate is a pure decision over facts — it takes an EffectGateDecision,
    # not an Effect and not an apply callback, so it cannot apply anything.
    params = inspect.signature(effect_gate_admits).parameters
    assert list(params) == ["decision"]
    assert params["decision"].annotation in (EffectGateDecision, "EffectGateDecision")


# --- the scoped-capability conjunct as a decidable fact --------------------------------------
def test_capability_covers_requires_exact_scope_match():
    spec = get_actuator("sense_fetch")
    assert capability_covers(ScopedCapability(scope="sense:fetch"), spec) is True
    # No prefix / glob authority — narrow means narrow.
    assert capability_covers(ScopedCapability(scope="sense:fetch:extra"), spec) is False
    assert capability_covers(ScopedCapability(scope="sense:"), spec) is False
    assert capability_covers(ScopedCapability(scope="send:email"), spec) is False


def test_capability_expiry_is_fail_closed():
    spec = get_actuator("sense_fetch")
    now = datetime(2026, 7, 3, 12, 0, tzinfo=UTC)

    def covers(expires_at: str) -> bool:
        return capability_covers(
            ScopedCapability(scope="sense:fetch", expires_at=expires_at), spec, now=now
        )

    assert covers((now + timedelta(minutes=5)).isoformat()) is True
    assert covers((now - timedelta(minutes=5)).isoformat()) is False
    # An unparseable expiry is treated as expired, never as forever.
    assert covers("not-a-date") is False
    # No expiry = bounded by the task, not the clock.
    assert covers("") is True
