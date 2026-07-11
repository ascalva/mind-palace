"""Live gate: a real Vault dev-server enforces the committed AppRole policies (vault-runtime-
auth.md, ops/vault/policies/). Auto-skips when no dev-server is reachable, like the Podman/Ollama
live tests. Run: pytest -m needs_vault.

Dev-mode only — `vault server -dev` auto-unseals and prints a root token to its own stdout; the
owner exports that as VAULT_TOKEN/VAULT_ADDR before running this (Step 6 runbook). This is not
production init/unseal: dev mode is Vault's own intentionally-disposable, no-such-thing-as-
durability sandbox, built for exactly this. Policy/secret seeding below uses that root token
directly via hvac, mirroring how `vault policy write`/`vault kv put` would be run by hand —
*not* a stand-in for the owner-operated production application in ops/vault/README.md.
"""

from __future__ import annotations

import os

import pytest

from config.loader import get_config
from config.secrets_backend import VaultClient, VaultPermissionDenied

pytestmark = pytest.mark.needs_vault

_POLICY_DIR = "ops/vault/policies"
_VAULT_ADDR = os.environ.get("VAULT_ADDR") or get_config().secrets.addr
_VAULT_TOKEN = os.environ.get("VAULT_TOKEN")


def _vault_available() -> bool:
    if not _VAULT_TOKEN:
        return False
    try:
        import hvac  # type: ignore[import-untyped]  # warrant: no py.typed upstream (V2); optional [secrets] extra

        client = hvac.Client(url=_VAULT_ADDR, token=_VAULT_TOKEN)
        return client.is_authenticated()
    except Exception:
        return False


_skip = pytest.mark.skipif(
    not _vault_available(), reason="no reachable Vault dev-server (VAULT_ADDR/VAULT_TOKEN unset?)"
)


@pytest.fixture
def root_client():
    import hvac

    return hvac.Client(url=_VAULT_ADDR, token=_VAULT_TOKEN)


def _apply_policy(root_client, *, role: str) -> None:
    """The dev-mode equivalent of `vault policy write <role> ops/vault/policies/<role>.hcl` —
    idempotent, so re-running this test repeatedly against the same dev-server is safe."""
    with open(f"{_POLICY_DIR}/{role}.hcl") as f:
        root_client.sys.create_or_update_policy(name=role, policy=f.read())


def _apply_token_role(root_client, *, role: str) -> None:
    """The dev-mode equivalent of `vault write auth/token/roles/<role> allowed_policies=<role>`
    (ops/vault/setup_policies.sh) — so a *scoped* (non-root) supervisor can mint a token carrying
    <role>'s policy via the role, without holding that policy itself (VaultClient.mint_token)."""
    root_client.auth.token.create_or_update_role(role_name=role, allowed_policies=[role])


def _put_secret(root_client, *, name: str, value: str, kv_mount: str) -> None:
    """The dev-mode equivalent of `vault kv put <kv_mount>/<name> value=<value>` by hand."""
    if not root_client.sys.list_mounted_secrets_engines().get(f"{kv_mount}/"):
        root_client.sys.enable_secrets_engine(
            backend_type="kv", path=kv_mount, options={"version": "2"}
        )
    root_client.secrets.kv.v2.create_or_update_secret(
        path=name, secret={"value": value}, mount_point=kv_mount
    )


@_skip
def test_mint_and_read_round_trips_through_a_real_dev_server(root_client):
    cfg = get_config()
    _apply_policy(root_client, role="dreamer")
    _apply_token_role(root_client, role="dreamer")
    _put_secret(root_client, name="oura-daily-aggregates", value="42 steps",
                kv_mount=cfg.secrets.kv_mount)

    client = VaultClient(
        addr=_VAULT_ADDR, kv_mount=cfg.secrets.kv_mount, supervisor_token=_VAULT_TOKEN
    )
    minted = client.mint_token("dreamer", "10m")
    assert minted.token and minted.accessor and minted.token != minted.accessor
    assert client.read_secret("oura-daily-aggregates", minted.token) == "42 steps"


@_skip
def test_out_of_policy_read_is_denied_by_the_real_server(root_client):
    cfg = get_config()
    _apply_policy(root_client, role="dreamer")    # grants oura-daily-aggregates only
    _apply_token_role(root_client, role="dreamer")
    _put_secret(root_client, name="financial-readonly-key", value="should-not-be-readable",
                kv_mount=cfg.secrets.kv_mount)

    client = VaultClient(
        addr=_VAULT_ADDR, kv_mount=cfg.secrets.kv_mount, supervisor_token=_VAULT_TOKEN
    )
    minted = client.mint_token("dreamer", "10m")
    with pytest.raises(VaultPermissionDenied):
        client.read_secret("financial-readonly-key", minted.token)


@_skip
def test_scoped_supervisor_mints_but_cannot_read(root_client):
    # The crux of the layer (vault-runtime-auth.md §3), proven against real Vault with a NON-root
    # supervisor token: it can mint a dreamer token (the token role authorizes the scope) yet is
    # itself denied the secret that token unlocks. dev-mode's root token hid this — root bypasses
    # the subset rule, so `policies=[role]` minting silently "worked" there but would fail here.
    cfg = get_config()
    _apply_policy(root_client, role="supervisor")
    _apply_policy(root_client, role="dreamer")
    _apply_token_role(root_client, role="dreamer")
    _put_secret(root_client, name="oura-daily-aggregates", value="42 steps",
                kv_mount=cfg.secrets.kv_mount)
    supervisor_token = root_client.auth.token.create(
        policies=["supervisor"], no_default_policy=True
    )["auth"]["client_token"]

    sup = VaultClient(addr=_VAULT_ADDR, kv_mount=cfg.secrets.kv_mount,
                      supervisor_token=supervisor_token)
    minted = sup.mint_token("dreamer", "10m")
    # The agent (minted token) reads its secret; the minter (supervisor token) is denied it.
    assert sup.read_secret("oura-daily-aggregates", minted.token) == "42 steps"
    with pytest.raises(VaultPermissionDenied):
        sup.read_secret("oura-daily-aggregates", supervisor_token)
