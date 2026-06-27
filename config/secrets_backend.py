"""Vault as a per-interaction runtime authorization layer (design-notes/vault-runtime-auth.md).

The object-capability model already scopes *store handles* at the code level (the dreamer
gets a `MirrorView`, never a raw vector store). This module closes the matching gap at the
*credential* level: an agent never holds a real secret, only an ephemeral token minted by the
supervisor and scoped to a named policy (role). A token that doesn't cover a path is denied —
the agent learns nothing beyond "denied" (`VaultPermissionDenied`).

`hvac` (the Vault HTTP client) is real-Vault-only and lazily imported inside `VaultClient`, so
importing this module — or `config.loader`, which imports it lazily too — never requires hvac
to be installed. The import-firewall (`ops/import_lint.py`) additionally blocks `hvac` from
ever appearing under `core/`: agents receive tokens in context (Phase 5), they never call
Vault directly. This module lives in `config/`, one level below `get_secret()`, exactly like
the design note's import-discipline section specifies.

Phase scope (Steps 4–5 of the security & attestation track, NOT a numbered phase): the primitives
below (`FakeVault`, `VaultClient`, `build_secrets_backend`, and `MintedToken`) and the
scope-enforcement tests that exercise them. Step 5 added the `accessor` half of `MintedToken` — a
mint's non-secret audit handle, which an attestation records in `vault_token_accessor` to tie an
action to its authorization (the Vault↔attestation join; never the token — see `MintedToken`).
Threading minted tokens into the dreamer/curator/vault-sync call sites is explicitly deferred to
Phase 5 (agent factory + dispatcher) per the design note's own framing — this module makes that
wiring possible without itself performing it.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Protocol


class VaultPermissionDenied(Exception):
    """Raised when a token is unknown, or known but its role's policy doesn't cover the path.
    Deliberately uninformative beyond that — the caller (an agent) must not learn *why* it was
    denied, only that it was; the Vault audit log (or `FakeVault.denials` in tests) is where the
    detail belongs (vault-runtime-auth.md §6 — denials are an alignment signal, not noise)."""


@dataclass(frozen=True)
class MintedToken:
    """What a mint returns: the secret `token` AND its `accessor` — Vault hands back both in one
    response (`resp["auth"]["client_token"]` / `["accessor"]`). The two live in different
    keyspaces and do different jobs (the Step-5 Vault↔attestation join, attestation-layer.md §2):

      • `token`     — the *credential*. The agent uses it (`get_secret(name, token=...)`) and
                      nothing else may. NEVER logged, attested, or shown to a model (Invariant 10).
      • `accessor`  — a non-secret *audit handle*. It can look up a token's metadata or revoke it,
                      but cannot authenticate or read any secret. THIS is what an attestation
                      records in `vault_token_accessor`, tying an action to its Vault authorization
                      without ever exposing the credential.

    The supervisor holds the whole `MintedToken`: it passes `.token` to the agent (in context,
    Phase 5) and records `.accessor` in the attestation it emits for that action."""

    token: str
    accessor: str


class SecretsBackend(Protocol):
    """What both `FakeVault` (tests) and `VaultClient` (real Vault) implement — the supervisor
    and `get_secret(..., token=...)` depend on this shape, never on which one is wired."""

    def mint_token(self, role: str, ttl: str) -> MintedToken: ...

    def read_secret(self, name: str, token: str) -> str: ...


@dataclass
class FakeVault:
    """An in-memory dev/test double — no real Vault, no network, no subprocess. `policies`
    maps a role name to the exact set of secret names its tokens may read (the dev-mode
    analogue of an HCL policy's path stanzas, see `ops/vault/policies/`); `secrets` is the
    backing key-value store. Every mint and every read/deny is recorded for assertions."""

    policies: dict[str, frozenset[str]]
    secrets: dict[str, str] = field(default_factory=dict)
    _tokens: dict[str, str] = field(default_factory=dict)      # token -> role (the credential side)
    _accessors: dict[str, str] = field(default_factory=dict)   # accessor -> role (the audit side)
    minted: list[tuple[str, str]] = field(default_factory=list)     # (role, ttl), audit trail
    denials: list[tuple[str, str]] = field(default_factory=list)    # (token, name), audit trail

    def mint_token(self, role: str, ttl: str) -> MintedToken:
        if role not in self.policies:
            raise VaultPermissionDenied(f"no policy registered for role {role!r}")
        # Distinct random ids in distinct prefixes: a token can't be passed where an accessor is
        # expected, nor vice versa (the keyspaces never overlap — mirrors real Vault).
        token = f"fake-token-{role}-{os.urandom(8).hex()}"
        accessor = f"fake-accessor-{role}-{os.urandom(8).hex()}"
        self._tokens[token] = role
        self._accessors[accessor] = role
        self.minted.append((role, ttl))
        return MintedToken(token=token, accessor=accessor)

    def read_secret(self, name: str, token: str) -> str:
        role = self._tokens.get(token)
        if role is None or name not in self.policies.get(role, frozenset()):
            self.denials.append((token, name))
            raise VaultPermissionDenied(f"token denied for secret {name!r}")
        return self.secrets[name]

    def role_for_accessor(self, accessor: str) -> str | None:
        """The dev-mode analogue of Vault's `lookup-accessor`: resolve an accessor to the role it
        was minted for, WITHOUT the token. This is what makes the Step-5 join *verifiable* — an
        attestation's `vault_token_accessor` can be confirmed to match its claimed `agent_role`.
        Returns None for an unknown accessor (or for a *token* passed here — wrong keyspace)."""
        return self._accessors.get(accessor)


class VaultClient:
    """Real Vault, via `hvac`. Construction is side-effect-free — no connection is opened until
    `mint_token`/`read_secret` is actually called — mirroring `OllamaClient`/`lancedb.connect`
    elsewhere: safe to build in a wiring test without a live Vault dev-server running.

    `supervisor_token` is the supervisor's own bootstrap credential (the bottom turtle for this
    layer — placed in Keychain/env via `get_secret("vault-supervisor-token")`, same pattern as
    the attestation signing keys). It is used only to mint child tokens; reads always go through
    a freshly-scoped client built from the *caller's* token, never the supervisor's.

    `hvac` is imported per-method, not in `__init__`: `edge/bridge/bridge.py` holds the same
    line for boto3 ("imported LAZILY... so tests with a fake client never require boto3
    installed") — this is that pattern applied here, so a wiring test can construct and inspect
    a `VaultClient` (addr, kv_mount) with no Vault dev-server *and no hvac installed*; only an
    actual `mint_token`/`read_secret` call needs the real package.
    """

    def __init__(self, addr: str, kv_mount: str = "kv", *, supervisor_token: str | None = None):
        self.addr = addr
        self.kv_mount = kv_mount
        self._supervisor_token = supervisor_token

    def mint_token(self, role: str, ttl: str) -> MintedToken:
        import hvac  # real-Vault-only (optional `[secrets]` extra) — see class docstring

        client = hvac.Client(url=self.addr, token=self._supervisor_token)
        resp = client.auth.token.create(policies=[role], ttl=ttl)
        # Vault returns both in one response: the credential and its non-secret audit handle.
        return MintedToken(token=resp["auth"]["client_token"], accessor=resp["auth"]["accessor"])

    def read_secret(self, name: str, token: str) -> str:
        import hvac  # real-Vault-only (optional `[secrets]` extra) — see class docstring

        client = hvac.Client(url=self.addr, token=token)
        try:
            resp = client.secrets.kv.v2.read_secret_version(
                path=name, mount_point=self.kv_mount, raise_on_deleted_version=True
            )
        except hvac.exceptions.Forbidden as e:
            raise VaultPermissionDenied(f"token denied for secret {name!r}") from e
        return resp["data"]["data"]["value"]


def build_secrets_backend(config: object | None = None) -> SecretsBackend | None:
    """Wire a real `VaultClient` from `[secrets]` — `None` when disabled, the normal state
    until the owner stands up a Vault dev-server (Step 6 runbook). Unlike attestation's
    fail-closed signing gate, a missing supervisor token here is not a silent-fallback risk
    (there is no insecure fallback path to slip into) — it simply surfaces as an hvac auth
    error on the first real `mint_token` call, not at construction."""
    from config.loader import get_config, get_secret

    cfg = config or get_config()
    if not cfg.secrets.enabled:
        return None
    return VaultClient(
        addr=cfg.secrets.addr,
        kv_mount=cfg.secrets.kv_mount,
        supervisor_token=get_secret("vault-supervisor-token"),
    )
