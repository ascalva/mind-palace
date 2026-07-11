"""Credential-level scope (vault-runtime-auth.md §2): the factory mints an ephemeral Vault token
for a granted role, binds it OFF the model prompt, and records only the non-secret accessor.

Proves the §2 lifecycle end-to-end with FakeVault: in-scope read works (step 4), out-of-scope is
denied and the agent learns only "denied" (step 5), an ungranted role / a missing backend holds no
token (fail-closed), and the token never reaches the model prompt or the attestation — only the
accessor does (the Vault↔attestation join; Invariant 10).
"""

from pathlib import Path

import pytest

from config.secrets_backend import SecretsBackend, VaultPermissionDenied
from core.attestation import Attestor
from core.attestation.attestor import StoreAttestor
from core.attestation.store import AttestationStore
from core.factory import AgentFactory, build_default_registry
from core.factory.factory import MintedAgent
from core.factory.roles import RoleTemplate
from tests.fixtures.secrets import fake_vault

# A correlator role (the §3 consumer of biometric aggregates) — its name matches the Vault policy,
# so the grant lines up. A custom role keeps Win-2 self-contained without touching BASE_ROLES.
_ROLES = {
    "correlator": RoleTemplate("correlator", "You correlate observed signals.", scope=frozenset()),
    "writer_editor": RoleTemplate("writer_editor", "You edit."),
}


def _factory(
    fv: SecretsBackend,
    *,
    attestor: Attestor | None = None,
    grant_roles: frozenset[str] = frozenset({"correlator"}),
) -> AgentFactory:
    return AgentFactory(tools=build_default_registry(), roles=dict(_ROLES),
                        secrets=fv, attestor=attestor, grant_roles=grant_roles)


def _mint(factory: AgentFactory, role_name: str) -> MintedAgent:
    """`factory.mint(role_name)`, narrowed: every `_ROLES` entry here has an empty `scope`, and
    every call site uses the default `requested_tools=frozenset()` — `beyond` (AgentFactory.mint)
    is always empty, so `mint` never routes to the gate for this file's own roles. The real
    return type is honestly `MintedAgent | GateRequest`; this test module only exercises the
    granted-mint path."""
    agent = factory.mint(role_name)
    assert isinstance(agent, MintedAgent)
    return agent


def _use_for_reads(monkeypatch, fv):
    """Point `get_secret`'s backend at the same FakeVault that minted (in production both are a
    VaultClient at the same addr — the agent holds only the token; `get_secret` does the call)."""
    monkeypatch.setattr("config.secrets_backend.build_secrets_backend", lambda *a, **k: fv)


def test_granted_role_reads_an_in_scope_secret(monkeypatch):
    fv = fake_vault(**{"oura-daily-aggregates": "hrv=42"})
    _use_for_reads(monkeypatch, fv)
    agent = _mint(_factory(fv), "correlator")
    assert agent.token is not None and agent.accessor is not None
    assert agent.read_secret("oura-daily-aggregates") == "hrv=42"     # §2 step 4: in scope → value


def test_out_of_scope_read_is_denied_learning_nothing(monkeypatch):
    fv = fake_vault(**{"oura-daily-aggregates": "hrv=42", "financial-readonly-key": "$$$"})
    _use_for_reads(monkeypatch, fv)
    agent = _mint(_factory(fv), "correlator")
    with pytest.raises(VaultPermissionDenied):                        # §2 step 5: denied, opaque
        agent.read_secret("financial-readonly-key")
    assert (agent.token, "financial-readonly-key") in fv.denials      # the attempt IS logged


def test_ungranted_role_holds_no_credential():
    agent = _mint(_factory(fake_vault()), "writer_editor")            # not in grant_roles
    assert agent.token is None
    with pytest.raises(RuntimeError):
        agent.read_secret("oura-daily-aggregates")


def test_no_backend_means_no_grant():
    f = AgentFactory(tools=build_default_registry(), roles=dict(_ROLES),
                     secrets=None, grant_roles=frozenset({"correlator"}))
    assert _mint(f, "correlator").token is None                       # fail-closed without Vault


def test_mint_attests_the_accessor_not_the_token():
    fv = fake_vault(**{"oura-daily-aggregates": "hrv=42"})
    store = AttestationStore(Path(":memory:"))
    agent = _mint(_factory(fv, attestor=StoreAttestor(store)), "correlator")
    mint_atts = [a for a in store.all() if a.action == "mint_token"]
    assert len(mint_atts) == 1
    att = mint_atts[0]
    assert att.vault_token_accessor == agent.accessor                # the audit handle is recorded
    assert att.vault_token_accessor != agent.token                   # the credential is NOT
    # the accessor resolves back to the role — the verifiable join, WITHOUT the token
    assert fv.role_for_accessor(att.vault_token_accessor) == "correlator"


def test_token_never_reaches_the_model_prompt_or_repr():
    agent = _mint(_factory(fake_vault(**{"oura-daily-aggregates": "x"})), "correlator")
    assert agent.token is not None   # correlator is granted here — a token was minted
    ctx = " ".join(m["content"] for m in agent.build_context("find patterns"))
    assert agent.token not in ctx                                    # held off the prompt (Inv 10)
    assert agent.token not in repr(agent)                            # and off the repr (repr=False)
