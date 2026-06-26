"""Load non-secret configuration into frozen, typed dataclasses.

Secrets are never stored here. `get_secret` is the single sanctioned access point for
later phases, and reads the environment (Keychain-backed in the owner's setup) only.
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
_DEFAULTS = Path(__file__).resolve().parent / "defaults.toml"


@dataclass(frozen=True)
class OllamaConfig:
    host: str
    port: int
    default_keep_alive: str
    request_timeout_s: int

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"


@dataclass(frozen=True)
class ResourceConfig:
    usable_ram_gb: float
    max_resident_models: int


@dataclass(frozen=True)
class PathsConfig:
    data_dir: Path
    telemetry_db: Path
    raw_store: Path
    vector_store: Path
    derived_store: Path      # INTERPRETED artifacts (dreams + curator findings), §8


@dataclass(frozen=True)
class VaultConfig:
    path: Path
    pattern: str


@dataclass(frozen=True)
class EmbeddingConfig:
    model: str
    dim: int
    query_instruction: str


@dataclass(frozen=True)
class DreamingConfig:
    similarity_threshold: float   # cosine to join two notes into a theme cluster
    min_cluster_size: int
    max_clusters: int
    near_dup_threshold: float     # cosine to flag two notes as a near-duplicate candidate


@dataclass(frozen=True)
class InterfaceConfig:
    handoff_dir: Path        # the sole core<->gateway channel (filesystem handoff, §6)
    default_adapter: str


@dataclass(frozen=True)
class SandboxConfig:
    runtime: str            # "podman" (default substrate) | "wasm" (pure-compute, future)
    image: str
    timeout_s: int
    memory: str
    cpus: float
    pids_limit: int
    max_concurrency: int
    warm_pool_size: int


@dataclass(frozen=True)
class ModelConfig:
    name: str
    tier: str
    pinned: bool
    resident_gb: float
    num_ctx: int
    evicts_pinned: bool = False


@dataclass(frozen=True)
class Config:
    ollama: OllamaConfig
    resources: ResourceConfig
    paths: PathsConfig
    vault: VaultConfig
    embedding: EmbeddingConfig
    dreaming: DreamingConfig
    sandbox: SandboxConfig
    interface: InterfaceConfig
    models: tuple[ModelConfig, ...]

    def model_for_tier(self, tier: str) -> ModelConfig:
        for m in self.models:
            if m.tier == tier:
                return m
        raise KeyError(f"no model configured for tier {tier!r}")

    @property
    def pinned_model(self) -> ModelConfig:
        for m in self.models:
            if m.pinned:
                return m
        raise KeyError("no pinned model configured")


def _resolve(p: str) -> Path:
    path = Path(p)
    return path if path.is_absolute() else REPO_ROOT / path


def load_config(path: Path | None = None) -> Config:
    raw = tomllib.loads((path or _DEFAULTS).read_text(encoding="utf-8"))
    o, r, p = raw["ollama"], raw["resources"], raw["paths"]
    v, e, s = raw["vault"], raw["embedding"], raw["sandbox"]
    itf, dr = raw["interface"], raw["dreaming"]
    return Config(
        ollama=OllamaConfig(
            host=o["host"],
            port=int(o["port"]),
            default_keep_alive=str(o["default_keep_alive"]),
            request_timeout_s=int(o["request_timeout_s"]),
        ),
        resources=ResourceConfig(
            usable_ram_gb=float(r["usable_ram_gb"]),
            max_resident_models=int(r["max_resident_models"]),
        ),
        paths=PathsConfig(
            data_dir=_resolve(p["data_dir"]),
            telemetry_db=_resolve(p["telemetry_db"]),
            raw_store=_resolve(p["raw_store"]),
            vector_store=_resolve(p["vector_store"]),
            derived_store=_resolve(p["derived_store"]),
        ),
        vault=VaultConfig(
            # ~ expands to $HOME; the vault is the owner's source corpus, outside the repo.
            path=Path(v["path"]).expanduser(),
            pattern=str(v["pattern"]),
        ),
        embedding=EmbeddingConfig(
            model=str(e["model"]),
            dim=int(e["dim"]),
            query_instruction=str(e["query_instruction"]),
        ),
        dreaming=DreamingConfig(
            similarity_threshold=float(dr["similarity_threshold"]),
            min_cluster_size=int(dr["min_cluster_size"]),
            max_clusters=int(dr["max_clusters"]),
            near_dup_threshold=float(dr["near_dup_threshold"]),
        ),
        sandbox=SandboxConfig(
            runtime=str(s["runtime"]),
            image=str(s["image"]),
            timeout_s=int(s["timeout_s"]),
            memory=str(s["memory"]),
            cpus=float(s["cpus"]),
            pids_limit=int(s["pids_limit"]),
            max_concurrency=int(s["max_concurrency"]),
            warm_pool_size=int(s["warm_pool_size"]),
        ),
        interface=InterfaceConfig(
            handoff_dir=_resolve(itf["handoff_dir"]),
            default_adapter=str(itf["default_adapter"]),
        ),
        models=tuple(
            ModelConfig(
                name=m["name"],
                tier=m["tier"],
                pinned=bool(m.get("pinned", False)),
                resident_gb=float(m["resident_gb"]),
                num_ctx=int(m["num_ctx"]),
                evicts_pinned=bool(m.get("evicts_pinned", False)),
            )
            for m in raw["models"]
        ),
    )


@lru_cache(maxsize=1)
def get_config() -> Config:
    return load_config()


def get_secret(name: str) -> str | None:
    """Fetch a secret from the environment (Keychain-backed in the owner's setup).

    Secrets are NEVER stored in config files or committed, and never passed to a model
    (Invariant 10). No secrets are required in Phase 0; this exists as the single
    sanctioned access point for later phases.
    """
    return os.environ.get(name)
