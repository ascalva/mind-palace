# ── Family 3 boundary (guarded transition systems) · symbols in docs/NOTATION.md ──
# OBJECT:    the irreversible-effect executor — the moment-of-action side of the effect gate for
#            class 3: mint a JIT scoped credential, gate, perform, attest, discard (hands-and-the-
#            effector-layer.md §5, §8.4, §8.6).
# INVARIANT: nothing is performed unless G_effect admits with a FRESH per-action capability; the
#            credential is minted at the instant of action and NEVER held (no field retains it); the
#            action record is attested with the token ACCESSOR (non-secret handle), never the token.
# ENFORCED:  structural + fail-closed — a non-irreversible/under-approved Effect is rejected before
#            any mint; the token is a local that leaves scope after the perform; the ExecRecord has
#            an accessor + attestation id and no token field.
"""Execute an irreversible / external effect under a just-in-time credential (Track G, item G6).

The irreversible class (send, pay, post, actuate) is the hardest gate: no undo. §8.4 answers the
confused deputy for it — **mint scope, not credential, at the moment of action, never ambient**. So
this executor is the one place a live credential briefly exists, and it exists only for the span of
a single approved effect:

  1. **Refuse before minting.** The `Effect` is IRREVERSIBLE and FULL_GATE-approved (the type
     already guarantees it cannot exist otherwise); the executor re-asserts that, plus the recorded
     `proposed` and `attested` facts. If any is false, it raises — *no credential is minted for a
     doomed effect* (a persuaded reasoner cannot even cause a mint).
  2. **Mint JIT.** Only then does it ask the Vault backend for a short-TTL token scoped to exactly
     this actuator's policy (`secrets.mint_token(scope, ttl)`). The freshly minted capability is
     what satisfies the gate's `scoped_cap_valid` conjunct — there is no ambient authority to reuse.
  3. **Gate, then act.** `effect_gate_admits` is checked over the recorded facts + the fresh
     capability (defense in depth; True by construction here). Only on admit does the injected
     transport perform the effect, holding the token *transiently*.
  4. **Attest, then discard.** An attested action record is appended (the token **accessor**, never
     the token — the Step-5 Vault↔attestation join), and the token leaves scope. Nothing retains it.

The transport is injected (`EffectTransport`): the real send/pay transports live in Zone B (edge)
and touch the network; this module orchestrates mint→gate→attest and never imports them, so it holds
no network dependency itself (a `FakeEffectTransport` proves the wiring, exactly as `FakeVault`
proves the credential path without a live Vault).
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Protocol

from ops.effect_catalog import get_actuator
from ops.effect_gate import EffectGateDecision, capability_covers, effect_gate_admits
from ops.effects import (
    ApprovalStrength,
    Effect,
    ReversibilityClass,
    ScopedCapability,
    required_approval,
)

if TYPE_CHECKING:  # annotations only — no runtime import (config/attestation stay injectable)
    from config.secrets_backend import SecretsBackend
    from core.attestation.attestor import Attestor

_TTL = re.compile(r"^\s*(\d+)\s*([smh])\s*$")
_TTL_UNIT = {"s": 1, "m": 60, "h": 3600}


def _ttl_seconds(ttl: str) -> int:
    """Parse a short Vault-style TTL ("60s", "5m", "1h") to seconds. Fail-closed: an unparseable TTL
    raises rather than defaulting to something long-lived (a per-action credential is short)."""
    m = _TTL.match(ttl)
    if not m:
        raise ValueError(f"unparseable credential TTL {ttl!r} (want e.g. '60s', '5m', '1h')")
    return int(m.group(1)) * _TTL_UNIT[m.group(2)]


class EffectTransport(Protocol):
    """The minimal outward-effect surface. `perform` receives the JIT token for THIS action and
    returns a receipt/id (a string the attestation hashes). Real implementations live in Zone B and
    touch the network; they never see anything but the token minted for this single effect."""

    def perform(self, actuator: str, params: dict, *, token: str) -> str: ...


class EffectDenied(RuntimeError):
    """The effect was refused before/at the gate — no credential minted, nothing performed."""


@dataclass(frozen=True)
class ExecRecord:
    """The record of one performed irreversible effect. Carries the token ACCESSOR (a non-secret
    audit handle) and the attestation id — deliberately NO token field, so the credential cannot be
    logged or persisted through this record (the MintedToken discipline, held one step harder)."""

    actuator: str
    accessor: str          # the minted token's non-secret audit handle (never the token)
    attestation_id: str
    receipt: str           # what the transport returned (a send id / receipt)


@dataclass
class IrreversibleExecutor:
    """Performs approved irreversible effects under a per-action JIT credential. Holds the mint
    authority (`secrets`), the attestor, and the transport — never a credential between calls."""

    secrets: SecretsBackend
    attestor: Attestor
    transport: EffectTransport
    credential_ttl: str = "60s"
    agent_role: str = "effector"

    def execute(
        self, effect: Effect, params: dict, *, proposed: bool, attested: bool
    ) -> ExecRecord:
        """Perform one approved irreversible effect. `proposed` / `attested` are the recorded facts
        (from the `EffectLedger` / attestation store) the gate conjoins. Raises `EffectDenied` (and
        mints nothing) unless the effect is a FULL_GATE-approved irreversible one with those facts
        true; the JIT credential is minted only after that check and never retained."""
        spec = get_actuator(effect.actuator)             # fail-closed on an uncataloged hand

        # (1) Refuse BEFORE minting — a doomed effect must not cause a credential to exist.
        if effect.reversibility is not ReversibilityClass.IRREVERSIBLE:
            raise EffectDenied(
                f"executor is for IRREVERSIBLE effects; {effect.actuator!r} is "
                f"{effect.reversibility.name} (use the reversible-write path)"
            )
        held = effect.approval_ref.strength if effect.approval_ref else ApprovalStrength.NONE
        if not (proposed and attested and held >= required_approval(effect.reversibility)):
            raise EffectDenied(
                f"effect {effect.actuator!r} not admissible pre-mint "
                f"(proposed={proposed}, attested={attested}, approval={held.name}) — no mint"
            )

        # (2) Mint JIT — a fresh short-TTL token scoped to exactly this actuator's policy. The token
        #     is a LOCAL; it is never stored on the executor. `scope` is the Vault role name.
        minted = self.secrets.mint_token(spec.scope, self.credential_ttl)
        expires = (datetime.now(UTC) + timedelta(seconds=_ttl_seconds(self.credential_ttl)))
        capability = ScopedCapability(
            scope=spec.scope, accessor=minted.accessor,
            expires_at=expires.replace(tzinfo=None).isoformat(timespec="seconds"),
        )

        # (3) Gate over recorded facts + the FRESH capability (defense in depth). By construction
        #     this admits; if it ever does not, we refuse rather than perform (the token expires).
        decision = EffectGateDecision(
            reversibility=effect.reversibility,
            proposed=proposed,
            approval=held,
            capability_valid=capability_covers(capability, spec),
            attested=attested,
        )
        if not effect_gate_admits(decision):
            raise EffectDenied(f"gate refused {effect.actuator!r} at execution — not performed")

        # (4) Act (transport holds the token transiently), then attest with the ACCESSOR — never the
        #     token — and let the token leave scope. Nothing here retains the credential.
        receipt = self.transport.perform(effect.actuator, params, token=minted.token)
        att = self.attestor.emit(
            agent_role=self.agent_role,
            action=f"effect:{effect.actuator}",
            input_hashes=(effect.proposal_att,) if effect.proposal_att else (),
            output_hashes=(hashlib.sha256(receipt.encode("utf-8")).hexdigest(),),
            vault_token_accessor=minted.accessor,
        )
        return ExecRecord(actuator=effect.actuator, accessor=minted.accessor,
                          attestation_id=att.id, receipt=receipt)


def build_irreversible_executor(config: object | None = None, *,
                                transport: EffectTransport) -> IrreversibleExecutor:
    """Wire the executor against the real Vault backend + attestor. REFUSES unless `[secrets]` is
    enabled (there is no mint authority otherwise) — the acting classes are owner-activated, and the
    irreversible one additionally requires a live credential backend. The `transport` is supplied by
    the caller (Zone B): this module never imports a network transport."""
    from config.loader import get_config
    from config.secrets_backend import build_secrets_backend
    from core.attestation import build_attestor

    cfg = config or get_config()
    secrets = build_secrets_backend(cfg)
    if secrets is None:
        raise EffectDenied(
            "[secrets] is disabled — no mint authority for a JIT credential; the irreversible "
            "class cannot be enabled without a Vault backend (hands-and-the-effector-layer.md §8.4)"
        )
    return IrreversibleExecutor(
        secrets=secrets,
        attestor=build_attestor(cfg),
        transport=transport,
        credential_ttl=cfg.effectors.jit_credential_ttl,
    )
