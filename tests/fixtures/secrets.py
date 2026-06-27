"""Secrets-backend test helpers — a pre-populated `FakeVault` matching the committed AppRole
policy taxonomy (ops/vault/policies/, design-notes/vault-runtime-auth.md §3), so tests exercise
the same role/grant shape the real HCL documents, not an ad-hoc stand-in."""

from __future__ import annotations

from config.secrets_backend import FakeVault

# Mirrors ops/vault/policies/*.hcl exactly — one frozenset of secret names per role.
POLICIES: dict[str, frozenset[str]] = {
    "dreamer": frozenset({"oura-daily-aggregates"}),
    "bridge": frozenset({"oura-api-token"}),       # aws/creds/bridge-role has no kv analogue here
    "research-airlock": frozenset(),               # aws/creds/airlock-role only, no kv grant
    "advisor": frozenset({"financial-readonly-key", "oura-api-token"}),
    "correlator": frozenset({"oura-daily-aggregates"}),
    "supervisor": frozenset(),                            # token-creation authority only, no reads
    "gate": frozenset({"gate-ledger-key"}),
}


def fake_vault(**secrets: str) -> FakeVault:
    """A `FakeVault` over the standard policy taxonomy with the given {name: value} secrets
    pre-loaded (e.g. `fake_vault(**{"oura-daily-aggregates": "42"})`)."""
    return FakeVault(policies=dict(POLICIES), secrets=dict(secrets))
