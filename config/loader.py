"""Load non-secret configuration into frozen, typed dataclasses.

Secrets are never stored here. `get_secret` is the single sanctioned access point for
later phases, and reads the environment (Keychain-backed in the owner's setup) only.
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
_DEFAULTS = Path(__file__).resolve().parent / "defaults.toml"
# Deployment-specific overrides: a gitignored config/local.toml that overlays the committed
# defaults section-by-section (e.g. `[secrets] enabled = true` on a machine where Vault is stood
# up, or `[attestation] enabled = true` once signing keys are placed). Keeps the shipped repo
# safe-by-default — a fresh clone / CI has no local.toml, so those flags stay off.
_LOCAL = Path(__file__).resolve().parent / "local.toml"
# Machine-owned knob overlay, written ONLY by the self-modification loop (ops/apply.py) through
# the §14 gate. Overlaid UNDER local.toml below, so a human override in local.toml always wins
# over a loop-tuned knob — human authority stays supreme. Gitignored; deleting it reverts every
# tuned knob to its committed default.
LEVERS_OVERLAY = Path(__file__).resolve().parent / "levers.toml"


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
    vault_catalog: Path      # active/tombstone ledger for incremental ingest (vault-sync)
    attestation_store: Path  # append-only attestation records (runtime proof layer)


@dataclass(frozen=True)
class VaultConfig:
    path: Path
    pattern: str
    watch_debounce_s: float = 1.0
    watch_poll_interval_s: float = 5.0


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
class DreamRnDConfig:
    """Dream-phase R&D track (FEATURE-FLAG OFF by default). The interpreter panel + adjudicator
    refuse to run unless `enabled` is True — see core/dreaming/rnd.py."""

    enabled: bool
    sigma: float                  # σ: cosine edge threshold for the mirror graph
    min_degree: int               # σ-neighbours to count a node as a graph "core"
    bridge_clustering_max: float  # local clustering coefficient ceiling for a structural hole
    centrality_top_k: int         # how many hub claims the centrality interpreter emits
    agreement_jaccard: float      # support overlap at which interpreters corroborate one claim


@dataclass(frozen=True)
class InterfaceConfig:
    handoff_dir: Path        # the sole core<->gateway channel (filesystem handoff, §6)
    default_adapter: str


@dataclass(frozen=True)
class AmbassadorConfig:
    """The conversational front door (Track B). Runs on the pinned tier (always warm); these
    are its judgment bounds, not behavior switches: `retrieval_k` caps per-turn retrieval depth
    (the budgeter enforces the window regardless), `history_max_turns` caps the cheap in-memory
    working context (older context is RE-retrieved from the authored-dialogue corpus, not
    double-stored), and `interruption_sensitivity` ∈ {off, earned_only, verbose} is the
    owner-tunable unprompted-message dial (default earned_only — note §3)."""

    retrieval_k: int = 5
    history_max_turns: int = 6
    interruption_sensitivity: str = "earned_only"


@dataclass(frozen=True)
class MonitorConfig:
    """The edge monitor — a small dashboard + chat surface over Tailscale (Zone B). A SEPARATE
    process palace supervises; it reads the core-emitted status snapshot and relays chat over the
    interface handoff, never importing core (Invariant 2). OFF by default; bind `host` to the
    Tailscale IP (not 0.0.0.0) so the tailnet is the auth boundary, same as the note-sync setup.
    `status_path` is where the launcher writes the metadata snapshot the dashboard renders."""

    enabled: bool = False
    host: str = "127.0.0.1"
    port: int = 8787
    status_path: Path = Path("data/monitor/status.json")
    request_timeout_s: float = 30.0


@dataclass(frozen=True)
class AirlockConfig:
    """Research airlock (§16). The sealed core uses only `handoff_dir`; the rest is Zone-B
    bridge config (S3 target + the narrowly-scoped assumed role). The core never reads S3."""

    handoff_dir: Path
    s3_bucket: str
    s3_region: str
    aws_profile: str
    requests_prefix: str
    results_prefix: str
    poll_interval_s: int
    poll_timeout_s: int


@dataclass(frozen=True)
class AttestationConfig:
    """Runtime proof layer (attestation-layer.md). Records are always written; `enabled` gates
    SIGNING. Pub-key paths are committed (non-secret); the private seeds live in Keychain/Vault."""

    enabled: bool = False
    signing_key_secret: str = "attestation-signing-key"
    owner_key_secret: str = "attestation-owner-key"
    supervisor_pub: Path = Path("ops/attestation/supervisor.pub")
    owner_pub: Path = Path("ops/attestation/owner.pub")


@dataclass(frozen=True)
class SecretsConfig:
    """Vault as a per-interaction runtime authorization layer (vault-runtime-auth.md). `enabled`
    only gates whether `build_secrets_backend` wires a real VaultClient — `get_secret(name)`
    with no token is unaffected either way (env/Keychain, unchanged)."""

    enabled: bool = False
    addr: str = "http://127.0.0.1:8200"
    kv_mount: str = "kv"
    aws_mount: str = "aws"
    # Agent roles that receive an ephemeral scoped credential grant when minted (§2 lifecycle).
    # FAIL-CLOSED EMPTY: a minted agent holds NO credential unless its role is listed here (grant
    # the minimum; the owner opts in per role in local.toml). vault-runtime-auth.md §3 is the
    # recommended set (e.g. correlator, advisor) — each must have a matching Vault token role.
    grant_roles: frozenset[str] = frozenset()
    token_ttl: str = "10m"   # TTL of a minted agent token — short; the grant expires by itself


@dataclass(frozen=True)
class BackupConfig:
    """restic → S3 encrypted backups (BUILD-SPEC §16b). restic encrypts + deduplicates CLIENT-SIDE,
    so AWS never sees plaintext; the bucket's SSE-KMS is defense in depth. `enabled` gates the
    scheduled job only. The repo password and the backup AWS key live in Keychain (named here, never
    stored here). Off by default — turn on per machine via config/local.toml once the bucket is
    applied and Keychain is placed."""

    enabled: bool = False
    repository: str = ""              # restic repo URL (terraform output restic_repository)
    password_secret: str = "restic-password"                       # Keychain item: repo password
    aws_access_key_id_secret: str = "backup-aws-access-key-id"     # Keychain item: backup key id
    aws_secret_access_key_secret: str = "backup-aws-secret-access-key"  # Keychain item: its secret
    region: str = "us-east-1"
    vault_snapshot: bool = True       # also capture a consistent `vault operator raft snapshot`
    exclude: tuple[str, ...] = (
        "logs", "queue.sqlite", "queue.sqlite-wal", "queue.sqlite-shm",
        "*-shm", "*.lock", ".DS_Store",
    )
    keep_daily: int = 7
    keep_weekly: int = 4
    keep_monthly: int = 6


@dataclass(frozen=True)
class SelfModConfig:
    """The self-modification loop (BUILD-SPEC §14, Phase 10). Two fail-closed switches:
    `enabled` is the master switch for the whole propose→approve→execute→validate→rollback loop;
    `unattended_enabled` separately gates the ONLY path that acts without human approval (the §14
    'safe levers'). Both OFF by default — a fresh clone can't self-modify, and never unattended,
    until the owner deliberately turns each on in config/local.toml."""

    enabled: bool = False
    unattended_enabled: bool = False
    ledger_db: Path = Path("data/selfmod_ledger.sqlite")


@dataclass(frozen=True)
class SandboxConfig:
    runtime: str            # "podman" (default) | "wasm" (pure-compute) | "routing" (wasm→podman)
    image: str
    timeout_s: int
    memory: str
    cpus: float
    pids_limit: int
    max_concurrency: int
    warm_pool_size: int
    wasm_module: str = ""   # path to a WASI python (python.wasm) for the wasm/routing runtimes


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
    dream_rnd: DreamRnDConfig
    sandbox: SandboxConfig
    interface: InterfaceConfig
    airlock: AirlockConfig
    models: tuple[ModelConfig, ...]
    # Default keeps direct Config(...) construction (e.g. in tests) working without this section.
    ambassador: AmbassadorConfig = field(default_factory=AmbassadorConfig)
    monitor: MonitorConfig = field(default_factory=MonitorConfig)
    attestation: AttestationConfig = field(default_factory=AttestationConfig)
    secrets: SecretsConfig = field(default_factory=SecretsConfig)
    backup: BackupConfig = field(default_factory=BackupConfig)
    selfmod: SelfModConfig = field(default_factory=SelfModConfig)

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


def _overlay(raw: dict, path: Path) -> None:
    """Shallow per-section merge of `path` onto `raw` in place — the overlay names just the keys
    it changes (e.g. `[secrets]\nenabled = true`), leaving every other default intact."""
    if not path.exists():
        return
    for section, values in tomllib.loads(path.read_text(encoding="utf-8")).items():
        if isinstance(values, dict) and isinstance(raw.get(section), dict):
            raw[section].update(values)
        else:
            raw[section] = values


def load_config(path: Path | None = None) -> Config:
    raw = tomllib.loads((path or _DEFAULTS).read_text(encoding="utf-8"))
    # Overlay precedence (only for the default path — an explicit `path`, as tests pass, is taken
    # verbatim): defaults ← levers.toml ← local.toml. The machine-tuned knobs land first; the
    # owner's hand-authored local.toml lands LAST so a human override always wins over a loop-tuned
    # knob (human authority supreme — the §14 ceiling). See LEVERS_OVERLAY / _LOCAL above.
    if path is None:
        _overlay(raw, LEVERS_OVERLAY)
        _overlay(raw, _LOCAL)
    o, r, p = raw["ollama"], raw["resources"], raw["paths"]
    v, e, s = raw["vault"], raw["embedding"], raw["sandbox"]
    itf, dr, rnd = raw["interface"], raw["dreaming"], raw["dream_rnd"]
    al, at = raw["airlock"], raw.get("attestation", {})
    amb = raw.get("ambassador", {})
    mon = raw.get("monitor", {})
    sec = raw.get("secrets", {})
    bak = raw.get("backup", {})
    sm = raw.get("selfmod", {})
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
            vault_catalog=_resolve(p["vault_catalog"]),
            # .get default keeps older/custom TOMLs (without this key) loading.
            attestation_store=_resolve(p.get("attestation_store", "data/attestations.sqlite")),
        ),
        vault=VaultConfig(
            # ~ expands to $HOME; the vault is the owner's source corpus, outside the repo.
            path=Path(v["path"]).expanduser(),
            pattern=str(v["pattern"]),
            watch_debounce_s=float(v.get("watch_debounce_s", 1.0)),
            watch_poll_interval_s=float(v.get("watch_poll_interval_s", 5.0)),
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
        dream_rnd=DreamRnDConfig(
            enabled=bool(rnd["enabled"]),
            sigma=float(rnd["sigma"]),
            min_degree=int(rnd["min_degree"]),
            bridge_clustering_max=float(rnd["bridge_clustering_max"]),
            centrality_top_k=int(rnd["centrality_top_k"]),
            agreement_jaccard=float(rnd["agreement_jaccard"]),
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
            wasm_module=str(s.get("wasm_module", "")),
        ),
        interface=InterfaceConfig(
            handoff_dir=_resolve(itf["handoff_dir"]),
            default_adapter=str(itf["default_adapter"]),
        ),
        airlock=AirlockConfig(
            handoff_dir=_resolve(al["handoff_dir"]),
            s3_bucket=str(al["s3_bucket"]),
            s3_region=str(al["s3_region"]),
            aws_profile=str(al["aws_profile"]),
            requests_prefix=str(al["requests_prefix"]),
            results_prefix=str(al["results_prefix"]),
            poll_interval_s=int(al["poll_interval_s"]),
            poll_timeout_s=int(al["poll_timeout_s"]),
        ),
        ambassador=AmbassadorConfig(
            retrieval_k=int(amb.get("retrieval_k", 5)),
            history_max_turns=int(amb.get("history_max_turns", 6)),
            interruption_sensitivity=str(amb.get("interruption_sensitivity", "earned_only")),
        ),
        monitor=MonitorConfig(
            enabled=bool(mon.get("enabled", False)),
            host=str(mon.get("host", "127.0.0.1")),
            port=int(mon.get("port", 8787)),
            status_path=_resolve(mon.get("status_path", "data/monitor/status.json")),
            request_timeout_s=float(mon.get("request_timeout_s", 30.0)),
        ),
        attestation=AttestationConfig(
            enabled=bool(at.get("enabled", False)),
            signing_key_secret=str(at.get("signing_key_secret", "attestation-signing-key")),
            owner_key_secret=str(at.get("owner_key_secret", "attestation-owner-key")),
            supervisor_pub=_resolve(at.get("supervisor_pub", "ops/attestation/supervisor.pub")),
            owner_pub=_resolve(at.get("owner_pub", "ops/attestation/owner.pub")),
        ),
        secrets=SecretsConfig(
            enabled=bool(sec.get("enabled", False)),
            addr=str(sec.get("addr", "http://127.0.0.1:8200")),
            kv_mount=str(sec.get("kv_mount", "kv")),
            aws_mount=str(sec.get("aws_mount", "aws")),
            grant_roles=frozenset(sec.get("grant_roles", [])),
            token_ttl=str(sec.get("token_ttl", "10m")),
        ),
        backup=BackupConfig(
            enabled=bool(bak.get("enabled", False)),
            repository=str(bak.get("repository", "")),
            password_secret=str(bak.get("password_secret", "restic-password")),
            aws_access_key_id_secret=str(
                bak.get("aws_access_key_id_secret", "backup-aws-access-key-id")
            ),
            aws_secret_access_key_secret=str(
                bak.get("aws_secret_access_key_secret", "backup-aws-secret-access-key")
            ),
            region=str(bak.get("region", "us-east-1")),
            vault_snapshot=bool(bak.get("vault_snapshot", True)),
            exclude=tuple(
                str(x) for x in bak.get(
                    "exclude",
                    ["logs", "queue.sqlite", "queue.sqlite-wal", "queue.sqlite-shm",
                     "*-shm", "*.lock", ".DS_Store"],
                )
            ),
            keep_daily=int(bak.get("keep_daily", 7)),
            keep_weekly=int(bak.get("keep_weekly", 4)),
            keep_monthly=int(bak.get("keep_monthly", 6)),
        ),
        selfmod=SelfModConfig(
            enabled=bool(sm.get("enabled", False)),
            unattended_enabled=bool(sm.get("unattended_enabled", False)),
            ledger_db=_resolve(sm.get("ledger_db", "data/selfmod_ledger.sqlite")),
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


def refresh_config() -> Config:
    """Drop the cached Config and reload from disk. Called after the self-mod loop writes a knob
    to `levers.toml` (ops/apply.py) so the change actually takes effect for subsequent
    `get_config()` callers in a long-running process, rather than waiting on a restart."""
    get_config.cache_clear()
    return get_config()


def get_secret(name: str, token: str | None = None) -> str | None:
    """Fetch a secret. With no token: environment (Keychain-backed in the owner's setup) —
    the owner-operated / bootstrap path, unchanged from Phase 0.

    With a token: a Vault ephemeral token minted for the calling agent's role
    (`Supervisor.mint_token`, vault-runtime-auth.md §2). The agent receives the token in its
    context, passes it here, and never constructs or stores it; Vault enforces the role's
    policy and raises `VaultPermissionDenied` if the path is out of scope — the agent learns
    nothing beyond "denied". The import lazily inside this branch only: `config.loader` is
    imported throughout `core/`, and `hvac` must never become a transitive hard dependency of
    that import (mirrors the lazy `boto3`/`watchdog` pattern elsewhere in this repo).

    Secrets are NEVER stored in config files or committed, and never passed to a model
    (Invariant 10).
    """
    if token is not None:
        from config.secrets_backend import build_secrets_backend

        backend = build_secrets_backend()
        if backend is None:
            raise RuntimeError("a token was passed but [secrets] is not enabled")
        return backend.read_secret(name, token)
    return os.environ.get(name)
