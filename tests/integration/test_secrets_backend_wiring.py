"""build_secrets_backend wires a real VaultClient from [secrets] (vault-runtime-auth.md §5).

Disabled (the default) -> None, so get_secret(name) with no token is the only path and hvac is
never touched. Enabled -> a VaultClient, constructible with no live Vault dev-server *and no
hvac installed* (construction is side-effect-free, same guarantee as OllamaClient/lancedb.connect
and exercised the same way as test_attestor_build_wiring.py for the attestation layer).
"""

from __future__ import annotations

import dataclasses

import pytest

from config.loader import get_secret
from config.secrets_backend import VaultClient, build_secrets_backend

# bp-067: loader internals live in core.config now (patch its globals THERE — finding-0104); the
# token-capable get_secret stays on the outside config.loader facade (the machinery/Vault zone).
from core.kernel.config import loader
from core.kernel.config.loader import _DEFAULTS, get_config, load_config


def _cfg(*, enabled: bool):
    cfg = get_config()
    return dataclasses.replace(cfg, secrets=dataclasses.replace(cfg.secrets, enabled=enabled))


def test_secrets_disabled_in_shipped_defaults():
    # The committed defaults.toml has [secrets] OFF — a deployment opts in via the gitignored
    # config/ouroboros.toml overlay, not by editing the shared default. Asserted against defaults
    # DIRECTLY (load_config bypasses the overlay for an explicit path), so an owner's overlay
    # enabling secrets can't mask a regression in the shipped safe default.
    assert load_config(_DEFAULTS).secrets.enabled is False
    assert build_secrets_backend(_cfg(enabled=False)) is None


def test_instance_overlay_enables_a_section(tmp_path, monkeypatch):
    # The gitignored config/ouroboros.toml overlays defaults section-by-section: it names only the
    # keys it changes, and every other shipped default survives the shallow merge.
    overlay = tmp_path / "ouroboros.toml"
    overlay.write_text("[secrets]\nenabled = true\n")
    monkeypatch.setattr(loader, "_INSTANCE_OVERLAY", overlay)
    # bp-123: redirect the guard's legacy probe too, so the case does not depend on whether this
    # machine still has a pre-rename config/local.toml.
    monkeypatch.setattr(loader, "_LEGACY_OVERLAY", tmp_path / "absent-legacy.toml")
    cfg = load_config()                                  # default path -> overlay applies
    assert cfg.secrets.enabled is True
    assert cfg.secrets.kv_mount == "kv"                  # untouched default preserved


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
    # SecretsBackend (the Protocol) declares only mint_token/read_secret; .addr/.kv_mount are
    # VaultClient-specific, so narrow first (same as test_enabled_wires_a_vault_client_..., above).
    assert isinstance(backend, VaultClient)
    assert backend.addr == "http://10.0.0.5:8200"
    assert backend.kv_mount == "secret"


def test_get_secret_with_token_but_backend_disabled_raises(monkeypatch):
    # A token passed while [secrets] is disabled is a hard error — no insecure fallback to env.
    # Force the disabled path so an owner's overlay (which may enable secrets) can't mask it.
    monkeypatch.setattr("config.secrets_backend.build_secrets_backend", lambda config=None: None)
    with pytest.raises(RuntimeError):
        get_secret("anything", token="some-token")
