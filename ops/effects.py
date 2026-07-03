# ── Family 1 boundary (labelings & information-flow) + family 4 filtration · docs/NOTATION.md ──
# OBJECT:    EffectView — the write-only-into-world boundary (the dual of MirrorView), filtered
#            by blast radius: Effects_{β≤ε} (hands-and-the-effector-layer.md §3–§4).
# INVARIANT: an Effect of non-SENSING class cannot exist without an approval reference whose
#            strength covers w(β); an EffectView never holds an effect above its ceiling ε.
# ENFORCED:  structural — Effect.__post_init__ / EffectView.__post_init__ raise; the illegal
#            states are deleted, not checked-then-refused.
"""The effector layer's first-class types (Track G, items G1; hands-and-the-effector-layer.md).

Effection is the mirror image of ingestion (companion IV, family 1): `MirrorView` constrains
*read*-flow into the introspective agents (a non-authored view is untypable); `Effect` /
`EffectView` constrain *action*-flow out into the world (an unapproved consequential effect is
unbuildable). Same object family — typed labels that constrain flow, enforced by making the
wrong flow unrepresentable — so the guarantees are inherited, not invented.

Three structural facts live here:

  1. **An illegal effect is unconstructable.** `Effect.__post_init__` raises if a non-SENSING
     reversibility class has no approval reference, or an approval weaker than its class
     demands. There is no code path that "checks and refuses" a rogue effect later — the
     object cannot exist (the `MirrorView` / `ProposedChange` move).
  2. **An effect carries no confidence of its own.** Worth-doing-ness is u-like — subjective,
     owner-judged — and must never be read off the adjudicator's c (companion III's axis
     separation, held as a hard rule at the actuator). An `Effect` may *cite* the motivating
     interpretations (`cites`), but deliberately has no `confidence` field: a high-c dream
     cannot earn an automatic action.
  3. **The rollout is a filtration by blast radius** (§4). `blast_radius` (β) places each
     reversibility class at a distance from the reversible origin; `required_approval` (w∘β)
     is non-decreasing in that distance; `EffectView` is Effects_{β≤ε} as a *type*, with the
     ceiling ε defaulting to the origin (SENSING). Raising ε is a deliberate, visible act —
     "you do not get a class until the one below is solid" is structural, not convention.

No credential appears anywhere in these types: `ScopedCapability` carries a *scope name* and a
Vault token *accessor* (a non-secret reference) — execution-time code resolves the accessor to
a live credential at the moment of action (G6, not built), the same discipline as
`MintedAgent.token` staying off the prompt and off the repr, held one step harder: here the
field does not exist at all.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import IntEnum


class ReversibilityClass(IntEnum):
    """The blast-radius classes, in rollout order (hands-and-the-effector-layer.md §3).

    Deliberately an IntEnum: unlike provenance — where G8 retired the trust *order* because no
    code used it — the order here is load-bearing. It is the §4 filtration index: β is monotone
    in it, w(β) is monotone in it, and `EffectView`'s ceiling comparison is `>` on it."""

    SENSING = 0        # read-only; reversible by definition (β = 0)
    REVERSIBLE = 1     # draft / hold / stage — the owner can undo (β small)
    IRREVERSIBLE = 2   # send / pay / post / actuate — no undo (β = ∞)


class ApprovalStrength(IntEnum):
    """How much human approval an effect holds (or requires). Ordered so `>=` means 'covers':
    a FULL_GATE approval satisfies a LIGHT requirement, never the reverse."""

    NONE = 0        # no human act — admissible only where w(β) demands nothing (sensing)
    LIGHT = 1       # approval-light: a one-tap / standing owner ack for reversible writes
    FULL_GATE = 2   # the full Phase-10-shaped gate: explicit human approval, attested


def blast_radius(reversibility: ReversibilityClass) -> float:
    """β : Effect → ℝ≥0 — distance from the reversible origin (§4). Sensing sits AT the origin
    (reversible by definition); reversible writes are a bounded undo away; irreversible external
    effects are at infinity (no undo exists at any cost)."""
    return {
        ReversibilityClass.SENSING: 0.0,
        ReversibilityClass.REVERSIBLE: 1.0,
        ReversibilityClass.IRREVERSIBLE: math.inf,
    }[reversibility]


def required_approval(reversibility: ReversibilityClass) -> ApprovalStrength:
    """w(β) — approval strength as a non-decreasing function of blast radius (§4): sensing needs
    none, reversible needs light approval, irreversible needs the full gate. Monotonicity is
    property-tested (β(a) ≤ β(b) ⟹ w(a) ≤ w(b)) — the effector analogue of 'confidence decays
    with derivational depth'."""
    return {
        ReversibilityClass.SENSING: ApprovalStrength.NONE,
        ReversibilityClass.REVERSIBLE: ApprovalStrength.LIGHT,
        ReversibilityClass.IRREVERSIBLE: ApprovalStrength.FULL_GATE,
    }[reversibility]


@dataclass(frozen=True)
class ScopedCapability:
    """The authority envelope an effect requires — a NAME and a reference, never a credential.

    `scope` is what the capability authorizes ("sense:fetch", "send:one-email-to:<addr>") —
    minted per-task, narrow by construction. `accessor` is the Vault token *accessor* (the
    non-secret handle the factory already attests); "" means credential-free (sensing).
    `expires_at` is an ISO timestamp; "" means bounded by the task, not the clock.

    Deliberately there is NO `token` / secret field — the type physically cannot carry a live
    credential, so no agent holding an `Effect` holds authority (Track G constraint: security
    comes from the effector being narrow, not the reasoner being trusted)."""

    scope: str
    accessor: str = ""
    expires_at: str = ""


@dataclass(frozen=True)
class ApprovalRef:
    """A reference to a *recorded* human approval act: who approved, at what strength, and
    where the act is written down (a ledger row / attestation id — auditable, never implied).
    The honesty lives in the orchestrator that only constructs one from a real record, exactly
    as `GateDecision.approved` is a recorded fact, not a guess."""

    approver: str
    strength: ApprovalStrength
    ref: str = ""


class UnapprovedEffectError(ValueError):
    """A consequential effect was constructed without an approval covering its class — the
    illegal state the type deletes (dual of NonMirrorRowError)."""


@dataclass(frozen=True)
class Effect:
    """One typed, scoped, attested world effect (hands-and-the-effector-layer.md §3).

    Unconstructable illegally: `__post_init__` raises unless the approval reference covers the
    reversibility class (None is admissible ONLY for SENSING). Functions typed to accept an
    `Effect` therefore inherit the proof that any consequential effect they see was approved.

    `cites` names the interpretations that *motivated* the effect (ids into the derived layer)
    — a citation, never a confidence. There is deliberately no confidence field here (module
    docstring, point 2): the gate weighs an effect by its reversibility class and the owner's
    judgment, never by a c it could smuggle in."""

    actuator: str                       # which hand (sense_fetch, send_email, ...)
    capability: ScopedCapability        # the scope it requires — a name, not a credential
    reversibility: ReversibilityClass
    proposal_att: str                   # attestation id of the signed proposal
    approval_ref: ApprovalRef | None = None   # REQUIRED (and covering) for non-SENSING classes
    cites: tuple[str, ...] = ()         # motivating interpretation ids — citation, not confidence

    def __post_init__(self) -> None:
        # Structural backstop (the MirrorView move, reflected): an Effect whose approval does
        # not cover its class CANNOT exist, however it was constructed. The gate re-checks the
        # same facts later (defense in depth) — but this is what makes "unapproved irreversible
        # effect" unrepresentable rather than merely refused.
        needed = required_approval(self.reversibility)
        if needed is ApprovalStrength.NONE:
            return
        if self.approval_ref is None:
            raise UnapprovedEffectError(
                f"effect {self.actuator!r} is {self.reversibility.name} and carries no "
                f"approval reference — {needed.name} approval is required (Track G §3)"
            )
        if self.approval_ref.strength < needed:
            raise UnapprovedEffectError(
                f"effect {self.actuator!r} is {self.reversibility.name} but its approval is "
                f"{self.approval_ref.strength.name} — {needed.name} is required (w(β), §4)"
            )


class CeilingExceededError(ValueError):
    """An effect above the view's blast-radius ceiling ε was offered to an EffectView."""


@dataclass(frozen=True)
class EffectView:
    """Effects_{β≤ε} as a type — the write-only-into-world boundary (dual of MirrorView).

    Every contained effect is guaranteed to sit within the ceiling ε — the type itself is the
    proof, so code typed to accept an `EffectView` (a dispatcher, a handoff emitter) inherits
    "nothing above ε reaches the world through me". Obtain one via `admit`; direct construction
    re-validates, so a hand-built view cannot smuggle a higher class past the filtration.

    The ceiling defaults to SENSING (ε = 0, the reversible origin): a fresh surface can dispatch
    read-only hands and nothing else. Raising ε is a deliberate, per-surface act — the §4
    graduated rollout expressed structurally."""

    _effects: tuple[Effect, ...] = ()
    ceiling: ReversibilityClass = ReversibilityClass.SENSING

    def __post_init__(self) -> None:
        over = [e.actuator for e in self._effects if e.reversibility > self.ceiling]
        if over:
            raise CeilingExceededError(
                f"effects {over!r} exceed the view's blast-radius ceiling "
                f"{self.ceiling.name} (Effects_{{β≤ε}} filtration, Track G §4)"
            )

    @classmethod
    def admit(
        cls,
        effects: tuple[Effect, ...] | list[Effect],
        *,
        ceiling: ReversibilityClass = ReversibilityClass.SENSING,
    ) -> EffectView:
        """The sanctioned constructor: admit `effects` under a declared ceiling. Raises
        `CeilingExceededError` (fail-closed) if any effect's class exceeds ε — admission is
        the construction; there is no admitted-but-unchecked state."""
        return cls(_effects=tuple(effects), ceiling=ceiling)

    def effects(self) -> list[Effect]:
        """The admitted effects (a fresh list; the view is immutable)."""
        return list(self._effects)

    def __len__(self) -> int:
        return len(self._effects)
