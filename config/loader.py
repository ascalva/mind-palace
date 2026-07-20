"""FACADE — the config loader now lives in `core.config.loader` (bp-067, finding-0103).

`core` owns its config-loading code (self-contained, stdlib-only, network-free). This module is a
thin re-export so the ~147 non-core importers (`from config.loader import get_config, Config, …`)
are untouched — outside → core is the allowed arrow. It DEFINES nothing but the token-capable
`get_secret` (the machinery zone MAY reach the network Vault path `config.secrets_backend`, which
core may not); the env path delegates to `core.config`, the single source of truth.

The public API is re-exported explicitly (not `import *`) so `get_secret` is unambiguously the
token-capable form here while `core.config`'s stays env-only — the trust-boundary split, visible to
the type checker. tests that MONKEYPATCH loader internals (`LEVERS_OVERLAY`/`_LOCAL`/`get_config`)
must patch `core.config.loader` — the real module whose `load_config` runs (finding-0104).
"""

from __future__ import annotations

from core.config.loader import (
    LEVERS_OVERLAY,
    REPO_ROOT,
    AirlockConfig,
    AmbassadorConfig,
    AttestationConfig,
    BackupConfig,
    Config,
    DreamingConfig,
    DreamRnDConfig,
    EffectorsConfig,
    EmbeddingConfig,
    ExhaustConfig,
    InterfaceConfig,
    ModelConfig,
    OllamaConfig,
    PathsConfig,
    ResourceConfig,
    SandboxConfig,
    SecretsConfig,
    SelfModConfig,
    VaultConfig,
    get_config,
    load_config,
    refresh_config,
)
from core.config.loader import get_secret as _env_secret

__all__ = [
    "AirlockConfig", "AmbassadorConfig", "AttestationConfig", "BackupConfig", "Config",
    "DreamRnDConfig", "DreamingConfig", "EffectorsConfig", "EmbeddingConfig", "ExhaustConfig",
    "InterfaceConfig",
    "LEVERS_OVERLAY", "ModelConfig", "OllamaConfig", "PathsConfig", "REPO_ROOT", "ResourceConfig",
    "SandboxConfig", "SecretsConfig", "SelfModConfig", "VaultConfig",
    "get_config", "get_secret", "load_config", "refresh_config",
]


def get_secret(name: str, token: str | None = None) -> str | None:
    """Token-capable secret access (the machinery form). With no token: the environment (delegates
    to `core.config`). With a token: a Vault ephemeral token minted for the calling agent's role —
    this branch reaches `config.secrets_backend` (network-capable, `hvac`), which is why it lives
    OUT here and not in core (Invariant 1). Secrets are never stored in config, read by a model, or
    logged (Invariant 10)."""
    if token is not None:
        from config.secrets_backend import build_secrets_backend

        backend = build_secrets_backend()
        if backend is None:
            raise RuntimeError("a token was passed but [secrets] is not enabled")
        return backend.read_secret(name, token)
    return _env_secret(name)
