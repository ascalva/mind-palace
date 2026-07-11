"""The effector types — illegal states unrepresentable (Track G, item G1).

The load-bearing claim of §3: an `Effect` of a consequential class cannot be *constructed*
without an approval reference covering it — the dual of `MirrorView` refusing a non-authored
row. These pin that the illegal state is deleted (not checked-then-refused), that an effect
carries no confidence of its own (§3, companion III's u≠c separation), and that `EffectView`
is the §4 blast-radius filtration Effects_{β≤ε} as a type.
"""

from __future__ import annotations

import math

import pytest

from ops.effects import (
    ApprovalRef,
    ApprovalStrength,
    CeilingExceededError,
    Effect,
    EffectView,
    ReversibilityClass,
    ScopedCapability,
    UnapprovedEffectError,
    blast_radius,
    required_approval,
)

_SENSE_CAP = ScopedCapability(scope="sense:fetch")
_SEND_CAP = ScopedCapability(scope="send:email", accessor="acc-123")
_FULL = ApprovalRef(approver="owner", strength=ApprovalStrength.FULL_GATE, ref="ledger:7")
_LIGHT = ApprovalRef(approver="owner", strength=ApprovalStrength.LIGHT, ref="ledger:8")


# --- G1: the illegal state is unconstructable ------------------------------------------------
def test_sensing_effect_needs_no_approval():
    e = Effect(
        actuator="sense_fetch",
        capability=_SENSE_CAP,
        reversibility=ReversibilityClass.SENSING,
        proposal_att="att-1",
    )
    assert e.approval_ref is None  # None is admissible ONLY for sensing


def test_irreversible_effect_without_approval_is_unrepresentable():
    # The structural guarantee (the MirrorView move): you cannot BUILD an unapproved
    # irreversible effect at all — not by hand, not anywhere.
    with pytest.raises(UnapprovedEffectError):
        Effect(
            actuator="send_email",
            capability=_SEND_CAP,
            reversibility=ReversibilityClass.IRREVERSIBLE,
            proposal_att="att-2",
        )


def test_reversible_effect_without_approval_is_unrepresentable():
    with pytest.raises(UnapprovedEffectError):
        Effect(
            actuator="draft_reply",
            capability=_SEND_CAP,
            reversibility=ReversibilityClass.REVERSIBLE,
            proposal_att="att-3",
        )


def test_irreversible_effect_with_too_weak_an_approval_is_refused():
    # A LIGHT approval does not cover an IRREVERSIBLE class — w(β) demands the FULL gate.
    with pytest.raises(UnapprovedEffectError):
        Effect(
            actuator="send_email",
            capability=_SEND_CAP,
            reversibility=ReversibilityClass.IRREVERSIBLE,
            proposal_att="att-4",
            approval_ref=_LIGHT,
        )


def test_reversible_effect_with_light_approval_constructs():
    e = Effect(
        actuator="draft_reply",
        capability=_SEND_CAP,
        reversibility=ReversibilityClass.REVERSIBLE,
        proposal_att="att-5",
        approval_ref=_LIGHT,
    )
    assert e.approval_ref is _LIGHT


def test_irreversible_effect_with_full_approval_constructs():
    e = Effect(
        actuator="send_email",
        capability=_SEND_CAP,
        reversibility=ReversibilityClass.IRREVERSIBLE,
        proposal_att="att-6",
        approval_ref=_FULL,
    )
    assert e.approval_ref is not None   # set explicitly above
    assert e.approval_ref.strength is ApprovalStrength.FULL_GATE


def test_full_approval_over_covers_a_reversible_class():
    # 'covers' is >= on strength: a full-gate approval satisfies a light requirement.
    e = Effect(
        actuator="draft_reply",
        capability=_SEND_CAP,
        reversibility=ReversibilityClass.REVERSIBLE,
        proposal_att="att-7",
        approval_ref=_FULL,
    )
    assert e.reversibility is ReversibilityClass.REVERSIBLE


# --- G1: an effect carries no confidence of its own (§3; companion III u≠c) -------------------
def test_effect_has_no_confidence_field():
    # The u≠c separation held at the actuator: worth-doing-ness must never be a c read off the
    # adjudicator. `cites` is a citation (ids), not a number — there is no confidence field.
    import inspect

    params = set(inspect.signature(Effect).parameters)
    assert "cites" in params
    for forbidden in ("confidence", "c", "score", "certainty"):
        assert forbidden not in params


def test_scoped_capability_has_no_credential_field():
    # Security comes from the effector being narrow: the capability names a scope + a Vault
    # accessor (a non-secret reference), never a live credential/token/secret.
    import inspect

    params = set(inspect.signature(ScopedCapability).parameters)
    assert params == {"scope", "accessor", "expires_at"}
    for forbidden in ("token", "secret", "credential", "password", "key"):
        assert forbidden not in params


# --- G1/§4: blast radius is a monotone filtration index --------------------------------------
def test_blast_radius_is_monotone_in_class():
    assert blast_radius(ReversibilityClass.SENSING) == 0.0
    assert blast_radius(ReversibilityClass.REVERSIBLE) > 0.0
    assert math.isinf(blast_radius(ReversibilityClass.IRREVERSIBLE))
    # β non-decreasing in the class order.
    classes = sorted(ReversibilityClass)
    betas = [blast_radius(c) for c in classes]
    assert betas == sorted(betas)


def test_required_approval_is_monotone_in_blast_radius():
    # w(β) non-decreasing: β(a) <= β(b)  ⟹  w(a) <= w(b) (§4). Exhaustive over the 3 classes.
    classes = sorted(ReversibilityClass)
    for a in classes:
        for b in classes:
            if blast_radius(a) <= blast_radius(b):
                assert required_approval(a) <= required_approval(b)


def test_required_approval_maps_each_class():
    assert required_approval(ReversibilityClass.SENSING) is ApprovalStrength.NONE
    assert required_approval(ReversibilityClass.REVERSIBLE) is ApprovalStrength.LIGHT
    assert required_approval(ReversibilityClass.IRREVERSIBLE) is ApprovalStrength.FULL_GATE


# --- G1/§4: EffectView is Effects_{β≤ε} as a type --------------------------------------------
def _sensing_effect(actuator: str = "sense_fetch") -> Effect:
    return Effect(
        actuator=actuator,
        capability=_SENSE_CAP,
        reversibility=ReversibilityClass.SENSING,
        proposal_att="att",
    )


def _reversible_effect() -> Effect:
    return Effect(
        actuator="draft_reply",
        capability=_SEND_CAP,
        reversibility=ReversibilityClass.REVERSIBLE,
        proposal_att="att",
        approval_ref=_LIGHT,
    )


def test_effect_view_default_ceiling_is_sensing_origin():
    view = EffectView.admit((_sensing_effect(),))
    assert view.ceiling is ReversibilityClass.SENSING
    assert len(view) == 1


def test_effect_view_refuses_effect_above_ceiling():
    # A reversible write above the default ε = 0 ceiling cannot be admitted — the §4 filtration
    # as a type, not a review step.
    with pytest.raises(CeilingExceededError):
        EffectView.admit((_reversible_effect(),))


def test_effect_view_admits_up_to_a_raised_ceiling():
    # Raising ε (the deliberate graduated-rollout act) admits the class below it.
    view = EffectView.admit(
        (_sensing_effect(), _reversible_effect()),
        ceiling=ReversibilityClass.REVERSIBLE,
    )
    assert len(view) == 2


def test_effect_view_direct_construction_re_validates():
    # Even bypassing `admit`, the constructor refuses an over-ceiling effect (fail-closed).
    with pytest.raises(CeilingExceededError):
        EffectView(_effects=(_reversible_effect(),), ceiling=ReversibilityClass.SENSING)


def test_empty_effect_view_is_valid():
    assert len(EffectView.admit(())) == 0
    assert EffectView.admit(()).effects() == []
