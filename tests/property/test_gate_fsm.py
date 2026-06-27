"""Exhaustive FSM check of the self-modification gate (Invariant 12; gap G5).

The live admission decision `G_now(Δ,s) = approved ∧ golden≥B ∧ D≤Θ` is a predicate over three
booleans — an 8-state space, enumerated here in full. Asserts: it admits ONLY the all-true
state (fail-closed), it is exactly the conjunction (the deferred `conforms` conjunct is absent,
not stubbed true — G5), Δ cannot self-apply through it (the predicate is data-in/bool-out with
no Δ handle), and the human gate never auto-approves a routed request.
"""

import inspect
from itertools import product

from ops.gate import GateDecision, GateStatus, HumanGate, gate_admits


def test_gate_admits_only_when_all_live_conjuncts_hold():
    admitted = []
    for approved, golden, drift in product([False, True], repeat=3):
        decision = GateDecision(
            approved=approved, golden_non_regressing=golden, drift_within_tolerance=drift
        )
        result = gate_admits(decision)
        # The predicate IS the conjunction of the three live conjuncts.
        assert result == (approved and golden and drift)
        if result:
            admitted.append((approved, golden, drift))
    # Fail-closed: exactly one of eight states admits — all three must hold.
    assert admitted == [(True, True, True)]


def test_conforms_conjunct_is_absent_not_defaulted_true():
    # G5 honesty: the decision exposes only the measurable conjuncts. `conforms` is deferred —
    # it must not appear as a stubbed-true field (which would silently pass it).
    fields = set(inspect.signature(GateDecision).parameters)
    assert fields == {"approved", "golden_non_regressing", "drift_within_tolerance"}
    assert "conforms" not in fields


def test_delta_cannot_self_apply_through_the_gate():
    # I12 "Δ never self-applies": the gate is a pure decision over facts about Δ·s — it takes a
    # GateDecision (booleans), not Δ and not an apply callback, so it cannot apply anything.
    params = inspect.signature(gate_admits).parameters
    assert list(params) == ["decision"]
    assert params["decision"].annotation in (GateDecision, "GateDecision")


def test_human_gate_never_auto_approves():
    gate = HumanGate()
    req = gate.submit("privileged_mint", "wants deploy")
    assert req.status is GateStatus.PENDING            # routed, not granted
    assert gate.pending() == [req]                     # stays pending until a human acts
    assert all(r.status is GateStatus.PENDING for r in gate.all())
