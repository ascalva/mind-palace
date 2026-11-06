"""Core-owned configuration (bp-067, the config leg of finding-0103 / the core-is-sacred principle).

`core.config` is the single home of config LOADING — stdlib-only, side-effect-free (`lru_cache`'d
pure TOML reads → frozen dataclasses), and network-free (it falls under `import_lint`'s core ban, so
config loading is now structurally proven free of any network path). `get_secret` here is the ENV
path only; the Vault-token capability stays in the OUTSIDE `config.loader` facade (the machinery
zone). The config DATA (tomls) lives in the repo-root `config/` dir; the loader reads it by path.

The outside `config/` package re-exports from here (outside → core is the allowed arrow), so the
~147 non-core importers are untouched. Core imports `from core.config import …`.
"""

from __future__ import annotations

from core.kernel.config.loader import (
    LEVERS_OVERLAY,
    OUROBOROS,
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
    InstanceConfig,
    InstanceOverlayError,
    InterfaceConfig,
    ModelConfig,
    Namespaces,
    OllamaConfig,
    PathsConfig,
    ResourceConfig,
    SandboxConfig,
    SecretsConfig,
    SelfModConfig,
    VaultConfig,
    get_config,
    get_secret,
    load_config,
    namespaces_of,
    refresh_config,
    shared,
)

__all__ = [
    "AirlockConfig",
    "AmbassadorConfig",
    "AttestationConfig",
    "BackupConfig",
    "Config",
    "DreamRnDConfig",
    "DreamingConfig",
    "EffectorsConfig",
    "EmbeddingConfig",
    "InstanceConfig",
    "InstanceOverlayError",
    "InterfaceConfig",
    "LEVERS_OVERLAY",
    "ModelConfig",
    "Namespaces",
    "OUROBOROS",
    "OllamaConfig",
    "PathsConfig",
    "REPO_ROOT",
    "ResourceConfig",
    "SandboxConfig",
    "SecretsConfig",
    "SelfModConfig",
    "VaultConfig",
    "get_config",
    "get_secret",
    "load_config",
    "namespaces_of",
    "refresh_config",
    "shared",
]
