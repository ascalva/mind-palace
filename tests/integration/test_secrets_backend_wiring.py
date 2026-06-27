"""build_secrets_backend wires a real VaultClient from [secrets] (vault-runtime-auth.md §5).

Disabled (the default) -> None, so get_secret(name) with no token is the only path and hvac is
never touched. Enabled -> a VaultClient, constructible with no live Vault dev-server *and no
hvac installed* (construction is side-effect-free, same guarantee as OllamaClient/lancedb.connect
and exercised the same way as test_attestor_build_wiring.py for the attestation layer).
"""

from __future__ import annotations

import dataclasses

import pytest

from config.loader import get_config, get_secret
from config.secrets_backend import VaultClient, build_secrets_backend


def _cfg(*, enabled: bool):
    cfg = get_config()
    return dataclasses.replace(cfg, secrets=dataclasses.replace(cfg.secrets, enabled=enabled))


def test_disabled_by_default_returns_none():
    assert get_config().secrets.enabled is False
    assert build_secrets_backend(get_config()) is None


def test_enabled_wires_a_vault_client_without_hvac_installed():
    cfg = _cfg(enabled=True)
    backend = build_secrets_backend(cfg)
    assert isinstance(backend, VaultClient)
    assert backend.addr == cfg.secrets.addr
    assert backend.kv_mount == cfg.secrets.kv_mount


def test_enabled_wiring_picks_up_custom_addr_and_mount():
    cfg = _cfg(enabled=True)
    secrets = dataclasses.replace(cfg.secrets, addr="http://10.0.0.5:8200", kv_mount="secret")
    cfg = dataclasses.replace(cfg, secrets=secrets)
    backend = build_secrets_backend(cfg)
    assert backend.addr == "http://10.0.0.5:8200"
    assert backend.kv_mount == "secret"


def test_get_secret_with_token_but_backend_disabled_raises():
    with pytest.raises(RuntimeError):
        get_secret("anything", token="some-token")
