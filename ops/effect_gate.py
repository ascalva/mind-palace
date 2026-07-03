# ── Family 3 boundary (guarded transition systems) · symbols in docs/NOTATION.md ──
# OBJECT:    the effect gate — world′ = apply(E) iff G_effect(E, world) else world
#            (hands-and-the-effector-layer.md §6; the Phase-10 gate, wider domain).
# INVARIANT: G_effect(E) = proposed(E) ∧ approved_{w(β(E))}(E) ∧ scoped_cap_valid(E) ∧ attested(E);
#            E never self-applies (the predicate is data-in/bool-out, no E handle, no apply).
# ENFORCED:  structural + FSM-verified — effect_gate_admits is a pure conjunction over recorded
#            facts, exhaustively enumerated in tests/property/test_effect_gate_fsm.py.
"""The Phase-10 gate generalized from config knobs to world effects (Track G, item G2).

The self-mod gate is already a guarded transition system (I12): s′ = Δ·s iff G_now(Δ,s), else s;
the model emits Δ, **code** applies it, rejection is identity. Hands generalize Δ from a
`ProposedChange` (a bounded numeric knob) to a `ProposedEffect` (a world effect) — the SAME
machine, wider domain, two new conjuncts:

    G_effect(E, world) = proposed(E) ∧ approved_{w(β(E))}(E) ∧ scoped_cap_valid(E) ∧ attested(E)

  * the approval conjunct is **blast-radius-weighted** (§4): the strength a class demands is
    w(β(E)) (`ops.effects.required_approval`) — sensing needs none, reversible needs light,
    irreversible needs the full gate; and
  * the **scoped-capability check** is a first-class conjunct: no matching, unexpired, minted
    scope ⇒ no effect, regardless of approval (the confused-deputy answer — even a persuaded
    reasoner cannot fire an effect no capability was minted for).

Because it is the same machine it inherits the FSM-verification discipline: the decision space
is small enough to enumerate in full (3 classes × 2 proposed × 3 approval strengths × 2
capability × 2 attested = 72 states), exactly like the 8-state config gate. Nothing new to
trust; one machine, wider inputs.

`ProposedEffect` inherits `ProposedChange`'s structural ceiling: it is an (actuator-name,
allowlisted-string-params) pair and NOTHING more — no field anywhere can hold a file path, a
diff, a command, code, or a URL, so "run this" / "fetch that address" is not a proposal the
layer can *express*. Actuators resolve fail-closed against the registry below (sensing-only
until G4's catalog process lands; widening it is a visible, reviewable diff — never a guess).

Scope note (stated, not silent): the durable per-effect ledger — the EffectLedger analogue of
`ops/ledger.ProposalLedger`, with execute/validate/rollback rows — lands with the first class
above β=0 (G5), where there is something to roll back. For β=0 sensing there is no world state
to restore; the guard, the types, and the attestation trail are the whole machine.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from ops.effect_catalog import ACTUATORS, ActuatorSpec, get_actuator
from ops.effects import ApprovalStrength, ReversibilityClass, ScopedCapability, required_approval

# The actuator registry (`ActuatorSpec`, `ACTUATORS`, `get_actuator`) moved to `ops/effect_catalog`
# in G4 — the catalog is the single source of truth for the hands the layer can express (each an
# audited §8 record), and the gate CONSUMES it. Re-exported here so callers that reason about the
# gate can name the spec without reaching for the catalog. Param-value cap now lives per-actuator
# (`ActuatorSpec.max_param_chars`): 256 for sensing, larger for content hands (a drafted body).
__all__ = [
    "ACTUATORS", "ActuatorSpec", "get_actuator", "ProposedEffect", "EffectGateDecision",
    "capability_covers", "effect_gate_admits",
]


@dataclass(frozen=True)
class ProposedEffect:
    """A proposed world effect — the ONLY shape an effect proposal can take (the Δ of §6).

    It is an actuator name plus allowlisted string params and nothing more. Deliberately there
    is no `path`, `diff`, `command`, `code`, `script`, or `url` field: the layer physically
    cannot propose "edit this file" / "run this" / "fetch this address", the same way
    `ProposedChange` cannot carry a code change and `ResearchCriteria` cannot carry a note.
    Params are stored as a sorted tuple of (key, value) pairs so the object stays frozen and
    hashable; `resolve()` is the fail-closed door to a dict."""

    actuator: str
    params: tuple[tuple[str, str], ...] = ()
    rationale: str = ""

    def resolve(self) -> tuple[ActuatorSpec, dict[str, str]]:
        """Resolve to (spec, validated-params). Raises on an unknown actuator, a param key
        outside the spec's closed allowlist, a non-string value, or an oversized value — all
        fail-closed, so an invalid proposal never reaches a decision as `proposed`."""
        spec = get_actuator(self.actuator)
        out: dict[str, str] = {}
        for key, value in self.params:
            if key not in spec.param_keys:
                raise ValueError(
                    f"actuator {spec.name!r} does not accept param {key!r}; "
                    f"allowed: {sorted(spec.param_keys)}"
                )
            if not isinstance(value, str):
                raise ValueError(f"param {key!r} must be a string, got {type(value).__name__}")
            if len(value) > spec.max_param_chars:
                raise ValueError(
                    f"param {key!r} too long ({len(value)} > {spec.max_param_chars} chars)"
                )
            out[key] = value
        return spec, out


def capability_covers(
    capability: ScopedCapability, spec: ActuatorSpec, *, now: datetime | None = None
) -> bool:
    """`scoped_cap_valid` as a decidable fact: the capability's scope is EXACTLY the scope the
    actuator requires (no prefix/glob authority — narrow means narrow), and it has not expired.
    An unparseable expiry is treated as expired (fail-closed), never as forever."""
    if capability.scope != spec.scope:
        return False
    if not capability.expires_at:
        return True  # bounded by the task, not the clock (module docstring in ops.effects)
    try:
        expires = datetime.fromisoformat(capability.expires_at)
    except ValueError:
        return False
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=UTC)
    return (now or datetime.now(UTC)) < expires


@dataclass(frozen=True)
class EffectGateDecision:
    """The recorded facts G_effect decides on — the effect analogue of `GateDecision`.

    Every field is a FACT an orchestrator recorded (a ledger row, an attestation, a capability
    check), never a judgment made here. `approval` is the strength actually held (NONE when no
    human acted); the strength *required* is not a field — it is computed from `reversibility`
    via w(β), so a decision cannot claim a weaker requirement than its class demands."""

    reversibility: ReversibilityClass   # sets w(β) — the required approval strength
    proposed: bool                      # a recorded proposal exists (attested inbox row)
    approval: ApprovalStrength          # the approval actually held (NONE if no human act)
    capability_valid: bool              # a minted, matching, unexpired scoped capability
    attested: bool                      # proposal (+ decision) attestations recorded


def effect_gate_admits(decision: EffectGateDecision) -> bool:
    """G_effect(E, world) = proposed ∧ approved_{w(β)} ∧ scoped_cap_valid ∧ attested (§6).

    Fail-closed: every conjunct must hold; any False denies and the world is unchanged
    (rejection is identity — the caller applies nothing on False). Pure data-in/bool-out:
    there is no E handle and no apply callback here, so an effect can never self-apply
    through the gate (I12, inherited). FSM-verified over all 72 states."""
    return (
        decision.proposed
        and decision.approval >= required_approval(decision.reversibility)
        and decision.capability_valid
        and decision.attested
    )
