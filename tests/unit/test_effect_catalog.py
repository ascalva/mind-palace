"""The effector catalog — the audited registry the gate consumes (Track G, item G4).

The catalog is the single source of truth for the hands the layer can express; each entry is a
recorded §8 audit outcome (docs/design-notes/skill-mining-pipeline.md). These pin: a shipped hand
is audited; lookup is fail-closed; the gate registry is DERIVED from the catalog (one source of
truth); the acting classes are cataloged yet unreachable at the wired ε = 0 ceiling (the §4
filtration held in the rollout, not just the types); and per-actuator param caps let a drafted body
through without widening the sensing hole.
"""

from __future__ import annotations

import pytest

from ops.effect_catalog import (
    ACTUATORS,
    CATALOG,
    actuators_for,
    get_actuator,
    get_entry,
)
from ops.effects import (
    ApprovalRef,
    ApprovalStrength,
    CeilingExceededError,
    Effect,
    EffectView,
    ReversibilityClass,
    ScopedCapability,
)


def test_every_cataloged_hand_is_audited():
    # A hand ships only when every §8 step was walked. `audited=True` is the recorded claim of that,
    # a required field so a half-audited hand cannot be added silently.
    for entry in CATALOG.values():
        assert entry.audited, f"{entry.spec.name} is in the catalog but not marked audited"
        assert entry.sandbox_profile, f"{entry.spec.name} has no sandbox exec profile (§8.5)"


def test_gate_registry_is_derived_from_the_catalog():
    # ACTUATORS is the gate-facing view of the catalog — same names, the spec of each entry. One
    # source of truth: you cannot register a hand with the gate without cataloging (auditing) it.
    assert set(ACTUATORS) == set(CATALOG)
    for name, spec in ACTUATORS.items():
        assert spec is CATALOG[name].spec


def test_lookup_is_fail_closed():
    assert get_actuator("sense_fetch").scope == "sense:fetch"
    assert get_entry("sense_fetch").audited is True
    with pytest.raises(KeyError):
        get_actuator("rm_rf")           # an uncataloged hand is unexpressible
    with pytest.raises(KeyError):
        get_entry("exfiltrate")


def test_the_three_classes_are_present_and_ordered():
    sensing = actuators_for(ReversibilityClass.SENSING)
    reversible = actuators_for(ReversibilityClass.REVERSIBLE)
    irreversible = actuators_for(ReversibilityClass.IRREVERSIBLE)
    assert [e.spec.name for e in sensing] == ["sense_fetch"]
    assert {e.spec.name for e in reversible} == {"draft_reply", "calendar_hold", "stage_file"}
    assert [e.spec.name for e in irreversible] == ["send_email"]
    # Every acting-class entry declares the scope its capability must match (narrow, per-hand).
    for e in reversible + irreversible:
        assert e.spec.scope and ":" in e.spec.scope


def test_content_hands_get_a_larger_param_cap_than_sensing():
    # A drafted body is real content, not a query term: the send/draft hands raise the per-actuator
    # value cap while sensing keeps the tight 256-char default (hygiene, not the security boundary).
    assert get_actuator("sense_fetch").max_param_chars == 256
    assert get_actuator("draft_reply").max_param_chars > 256
    assert get_actuator("send_email").max_param_chars > 256
    assert get_actuator("stage_file").max_param_chars >= get_actuator("draft_reply").max_param_chars


def test_cataloged_acting_hands_are_unreachable_at_the_wired_ceiling():
    # The rollout discipline (§4): cataloging a hand does NOT enable it. A REVERSIBLE draft effect
    # is refused by an EffectView at the default ε = SENSING ceiling — exactly what the wired
    # sensing surface admits at. Reaching it requires deliberately raising ε.
    draft = Effect(
        actuator="draft_reply",
        capability=ScopedCapability(scope="draft:reply"),
        reversibility=ReversibilityClass.REVERSIBLE,
        proposal_att="att",
        approval_ref=ApprovalRef(approver="owner", strength=ApprovalStrength.LIGHT),
    )
    with pytest.raises(CeilingExceededError):
        EffectView.admit((draft,))                                   # ε = SENSING default
    # Raising ε to REVERSIBLE is the deliberate, visible act that admits it.
    assert len(EffectView.admit((draft,), ceiling=ReversibilityClass.REVERSIBLE)) == 1
