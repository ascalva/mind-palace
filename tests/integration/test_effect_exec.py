"""Irreversible effects under a just-in-time credential (Track G, item G6).

The class-3 hands are "fully gated with JIT scoped credentials and attested records." These pin the
load-bearing security facts of §8.4/§8.6:
  * the credential is minted PER ACTION, scoped to the actuator's policy, with a short TTL;
  * a doomed effect (unproposed / unattested / wrong class) causes NO mint at all — a persuaded
    reasoner cannot even make a credential exist;
  * the token is handed to the transport transiently and NEVER retained — the action record and the
    ExecRecord carry the non-secret accessor, and the token appears nowhere in the attestation; and
  * an irreversible effect is unconstructable without the full-gate approval in the first place.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import pytest

from config.secrets_backend import FakeVault
from core.attestation.attestor import StoreAttestor
from core.attestation.store import AttestationStore
from ops.effect_exec import (
    EffectDenied,
    ExecRecord,
    IrreversibleExecutor,
    _ttl_seconds,
)
from ops.effects import (
    ApprovalRef,
    ApprovalStrength,
    Effect,
    ReversibilityClass,
    ScopedCapability,
    UnapprovedEffectError,
)


class FakeEffectTransport:
    """Records what it was asked to perform (including the token it received) and returns a receipt.
    The real send/pay transports are edge-side; this proves the wiring without a network."""

    def __init__(self):
        self.calls: list[tuple[str, dict[str, str], str]] = []

    def perform(self, actuator: str, params: dict[str, str], *, token: str) -> str:
        self.calls.append((actuator, dict(params), token))
        return f"receipt-{actuator}-001"


def _executor(ttl: str = "60s"):
    vault = FakeVault(policies={"send:email": frozenset({"smtp-credential"})},
                      secrets={"smtp-credential": "hunter2"})
    store = AttestationStore(Path(":memory:"))
    transport = FakeEffectTransport()
    ex = IrreversibleExecutor(secrets=vault, attestor=StoreAttestor(store), transport=transport,
                              credential_ttl=ttl)
    return ex, vault, store, transport


def _approved_send() -> Effect:
    return Effect(
        actuator="send_email",
        capability=ScopedCapability(scope="send:email"),
        reversibility=ReversibilityClass.IRREVERSIBLE,
        proposal_att="att-propose",
        approval_ref=ApprovalRef(approver="owner", strength=ApprovalStrength.FULL_GATE),
    )


def test_jit_credential_is_minted_per_action_scoped_and_attested():
    ex, vault, store, transport = _executor()
    rec = ex.execute(_approved_send(), {"to": "a@b.c", "subject": "s", "body": "b"},
                     proposed=True, attested=True)

    # Exactly one mint, scoped to the actuator's policy, short TTL — minted at the moment of action.
    assert vault.minted == [("send:email", "60s")]

    # The transport received the real minted token (code acts; the token is used, then discarded).
    assert len(transport.calls) == 1
    actuator, _params, token = transport.calls[0]
    assert actuator == "send_email"
    assert token.startswith("fake-token-send:email")

    # The action record is attested with the ACCESSOR — the Step-5 Vault↔attestation join — which
    # ties back to the right role; the accessor is not the token (different keyspaces).
    assert rec.accessor.startswith("fake-accessor-send:email")
    assert rec.accessor != token
    assert vault.role_for_accessor(rec.accessor) == "send:email"

    att = store.get(rec.attestation_id)
    assert att is not None
    assert att.action == "effect:send_email"
    assert att.vault_token_accessor == rec.accessor


def test_the_token_is_never_retained_or_recorded():
    ex, vault, store, transport = _executor()
    rec = ex.execute(_approved_send(), {"to": "a@b.c", "subject": "s", "body": "b"},
                     proposed=True, attested=True)
    _actuator, _params, token = transport.calls[0]

    # The ExecRecord has no token field — the credential cannot be logged/persisted through it.
    fields = {f.name for f in dataclasses.fields(ExecRecord)}
    assert "token" not in fields and "accessor" in fields

    # The executor retains nothing between calls (mint authority yes, a credential no).
    assert getattr(ex, "token", None) is None
    assert token not in vars(ex).values()

    # The token appears NOWHERE in the attestation record — only the accessor does.
    att = store.get(rec.attestation_id)
    assert token not in json.dumps(att.to_dict())
    assert rec.accessor in json.dumps(att.to_dict())


def test_a_doomed_effect_causes_no_mint():
    # The confused-deputy answer, sharpest form: an effect that will not pass the gate must not even
    # cause a credential to be minted. Unproposed / unattested → refused before the mint.
    ex, vault, store, transport = _executor()
    effect = _approved_send()
    with pytest.raises(EffectDenied):
        ex.execute(effect, {"to": "a"}, proposed=False, attested=True)
    with pytest.raises(EffectDenied):
        ex.execute(effect, {"to": "a"}, proposed=True, attested=False)
    assert vault.minted == []            # no credential ever came into existence
    assert transport.calls == []         # nothing performed
    assert store.count() == 0            # nothing attested


def test_executor_refuses_a_non_irreversible_effect():
    ex, vault, _store, transport = _executor()
    draft = Effect(
        actuator="draft_reply",
        capability=ScopedCapability(scope="draft:reply"),
        reversibility=ReversibilityClass.REVERSIBLE,
        proposal_att="a",
        approval_ref=ApprovalRef(approver="owner", strength=ApprovalStrength.FULL_GATE),
    )
    with pytest.raises(EffectDenied):
        ex.execute(draft, {"to": "a"}, proposed=True, attested=True)
    assert vault.minted == [] and transport.calls == []


def test_irreversible_effect_is_unconstructable_without_the_full_gate():
    # The executor's input can never BE an unapproved send: the type deletes that state upstream.
    with pytest.raises(UnapprovedEffectError):
        Effect(actuator="send_email", capability=ScopedCapability(scope="send:email"),
               reversibility=ReversibilityClass.IRREVERSIBLE, proposal_att="a")   # no approval
    with pytest.raises(UnapprovedEffectError):
        Effect(actuator="send_email", capability=ScopedCapability(scope="send:email"),
               reversibility=ReversibilityClass.IRREVERSIBLE, proposal_att="a",
               approval_ref=ApprovalRef(approver="owner", strength=ApprovalStrength.LIGHT))


def test_ttl_parsing_is_fail_closed():
    assert (_ttl_seconds("60s"), _ttl_seconds("5m"), _ttl_seconds("1h")) == (60, 300, 3600)
    for bad in ("forever", "", "10", "10x", "-5s"):
        with pytest.raises(ValueError):
            _ttl_seconds(bad)
