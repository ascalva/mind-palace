"""FakeVault — the dev/test double for Vault-as-runtime-authorization (vault-runtime-auth.md).

Pure scope-enforcement logic, no real Vault, no network: a token only unlocks what its role's
policy names; everything else is `VaultPermissionDenied`, the same denial an agent would see
against a real Vault server. `get_secret`'s env-fallback path (no token) is unchanged by any of
this — asserted here too so a future edit can't silently couple the two paths.
"""

from __future__ import annotations

import pytest

from config.loader import get_secret
from config.secrets_backend import VaultPermissionDenied
from tests.fixtures.secrets import fake_vault


def test_mint_token_for_known_role_succeeds():
    vault = fake_vault()
    minted = vault.mint_token("dreamer", "10m")
    assert minted.token and minted.accessor
    assert vault.minted == [("dreamer", "10m")]


def test_mint_token_for_unknown_role_is_denied():
    vault = fake_vault()
    with pytest.raises(VaultPermissionDenied):
        vault.mint_token("not-a-real-role", "10m")


def test_read_secret_in_policy_succeeds():
    vault = fake_vault(**{"oura-daily-aggregates": "42 steps"})
    minted = vault.mint_token("dreamer", "10m")
    assert vault.read_secret("oura-daily-aggregates", minted.token) == "42 steps"


def test_read_secret_outside_policy_is_denied_and_logged():
    vault = fake_vault(**{"financial-readonly-key": "secret-value"})
    minted = vault.mint_token("dreamer", "10m")   # dreamer's policy has no financial grant
    with pytest.raises(VaultPermissionDenied):
        vault.read_secret("financial-readonly-key", minted.token)
    assert (minted.token, "financial-readonly-key") in vault.denials


def test_read_secret_with_unknown_token_is_denied():
    vault = fake_vault(**{"oura-daily-aggregates": "42 steps"})
    with pytest.raises(VaultPermissionDenied):
        vault.read_secret("oura-daily-aggregates", "not-a-real-token")


def test_token_and_accessor_occupy_separate_keyspaces():
    # The accessor is an audit handle, never a credential: it cannot authenticate a read, and a
    # token is not a valid accessor. This separation is what makes the Step-5 join safe — recording
    # the accessor in an attestation leaks no ability to read, whereas the token would be the keys.
    vault = fake_vault(**{"oura-daily-aggregates": "42 steps"})
    minted = vault.mint_token("dreamer", "10m")
    assert minted.token != minted.accessor
    with pytest.raises(VaultPermissionDenied):
        vault.read_secret("oura-daily-aggregates", minted.accessor)   # accessor can't authenticate
    assert vault.role_for_accessor(minted.token) is None              # token isn't an accessor
    assert vault.role_for_accessor(minted.accessor) == "dreamer"      # accessor resolves the role


def test_two_roles_with_overlapping_grants_each_stay_scoped():
    # advisor and correlator both touch oura-* names but via disjoint policy entries (advisor.hcl
    # grants oura-api-token, correlator.hcl grants oura-daily-aggregates) — neither token should
    # unlock the other's secret.
    vault = fake_vault(**{"oura-api-token": "tok-a", "oura-daily-aggregates": "agg-b"})
    advisor = vault.mint_token("advisor", "10m")
    correlator = vault.mint_token("correlator", "10m")
    assert vault.read_secret("oura-api-token", advisor.token) == "tok-a"
    assert vault.read_secret("oura-daily-aggregates", correlator.token) == "agg-b"
    with pytest.raises(VaultPermissionDenied):
        vault.read_secret("oura-daily-aggregates", advisor.token)
    with pytest.raises(VaultPermissionDenied):
        vault.read_secret("oura-api-token", correlator.token)


def test_get_secret_with_no_token_still_reads_env_unchanged(monkeypatch):
    monkeypatch.setenv("MIND_PALACE_TEST_SECRET", "from-env")
    assert get_secret("MIND_PALACE_TEST_SECRET") == "from-env"
    assert get_secret("MIND_PALACE_TEST_SECRET_ABSENT") is None
