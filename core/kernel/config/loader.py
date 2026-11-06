"""Load non-secret configuration into frozen, typed dataclasses.

Secrets are never stored here. `get_secret` is the single sanctioned access point for
later phases, and reads the environment (Keychain-backed in the owner's setup) only.
"""

from __future__ import annotations

import os
import re
import tomllib
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

# bp-067: the LOADER moved into core.config (core owns its config-loading code — self-contained,
# stdlib-only, network-free). The config DATA (the tomls) stays in the repo-root `config/` dir — its
# gitignore entries (`config/ouroboros.toml`, `config/levers.toml`) are path-specific and out of
# this plan's write_scope, so relocating the data would strand them; the loader reads them by path
# instead (a filesystem read, no first-party import — self-containment is about IMPORTS, not data).
# kernel/config/loader.py → core/kernel/config → core/kernel → core → <repo> (K1, bp-090)
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_CONFIG_DIR = REPO_ROOT / "config"                          # the committed + per-machine toml data
_DEFAULTS = _CONFIG_DIR / "defaults.toml"
# Deployment-specific overrides: a gitignored config/ouroboros.toml that overlays the committed
# defaults section-by-section (e.g. `[secrets] enabled = true` on a machine where Vault is stood
# up, or `[attestation] enabled = true` once signing keys are placed). Keeps the shipped repo
# safe-by-default — a fresh clone / CI has no ouroboros.toml, so those flags stay off.
#
# Named for the INSTANCE (owner ruling, 2026-07-26): `mind-palace` is the framework, Ouroboros is
# this live instance, so the instance's own overlay carries the instance's name rather than the
# generic "local". The file was called `local.toml` before that date — see `_LEGACY_OVERLAY`.
#
# The default chain IS Ouroboros (DI-2, #25): its instance id is this name, its namespaces are the
# ones it had before instances had ids, and no named overlay may claim either.
OUROBOROS = "ouroboros"
_INSTANCE_OVERLAY = _CONFIG_DIR / f"{OUROBOROS}.toml"
# The pre-2026-07-26 name. Retained ONLY so the loader can REFUSE (`_refuse_on_legacy_overlay`)
# rather than silently ignore an un-migrated overlay; it is never read as config. Delete this
# constant and its guard once every instance has migrated (bp-123 §11).
_LEGACY_OVERLAY = _CONFIG_DIR / "local.toml"
# Machine-owned knob overlay, written ONLY by the self-modification loop (ops/apply.py) through
# the §14 gate. Overlaid UNDER ouroboros.toml below, so a human override in ouroboros.toml always
# wins over a loop-tuned knob — human authority stays supreme. Gitignored; deleting it reverts
# every tuned knob to its committed default.
LEVERS_OVERLAY = _CONFIG_DIR / "levers.toml"
# Instance selection at run time (DI-2, #25; the bench deployment, `ops/container/README.md`). When
# this variable is set it names the ONE overlay the loader reads, in place of BOTH files above: a
# named instance is a different individual, so it must not inherit Ouroboros's hand overlay or the
# knobs Ouroboros's own self-modification loop tuned. It reads its own levers file instead
# (`InstanceConfig.levers`). Unset, the chain is exactly as before.
OVERLAY_ENV = "MIND_PALACE_OVERLAY"

# ── Instance identity (DI-2, #25) ────────────────────────────────────────────────────────────────
# A named overlay declares `[instance] id`, and every namespace the instance holds is derived from
# it (`InstanceConfig`, `namespaces_of`). The id is lowercase ASCII, so names built from it stay
# distinct on a case-insensitive filesystem (APFS folds case by default); it holds no `.` or `/`,
# so it is one path segment and one dotted component wherever it appears, and a derived name splits
# back into exactly one id.
_INSTANCE_ID = re.compile(r"[a-z][a-z0-9-]{0,31}")
# A named instance's state lives under `<repo>/instances/<id>/` (gitignored), never under `data/`:
# nested in Ouroboros's data dir it would ride Ouroboros's backup and fall to Ouroboros's `reset`.
_INSTANCES = "instances"
LABEL_PREFIX = "com.mind-palace."
LAUNCHD_ROLES = ("palace", "tick")      # the supervisor (ops/lifecycle/launcher.py), the heartbeat
SUPERVISOR_LOCK = "supervisor.lock"     # beside the queue it guards (ops/lifecycle/lock.py)
# Every path the config names that an instance WRITES. Each resolves against the instance's root,
# so `data/…` is Ouroboros's `<repo>/data/…` and a named instance's `instances/<id>/data/…`. A named
# overlay may move one only within its root: relative, and without `..`.
_DATA_PLANE = (
    ("paths", "data_dir"), ("paths", "telemetry_db"), ("paths", "raw_store"),
    ("paths", "vector_store"), ("paths", "derived_store"), ("paths", "vault_catalog"),
    ("paths", "attestation_store"), ("paths", "curated_store"),
    ("interface", "handoff_dir"), ("airlock", "handoff_dir"), ("selfmod", "ledger_db"),
    ("effectors", "handoff_dir"), ("effectors", "ledger_db"), ("effectors", "drafts_dir"),
)
# The Keychain/env items (and the AWS profile) an instance reads its secrets from. A named
# instance's are `<id>.<name>`, derived from the committed defaults and never set in its overlay, so
# two instances hold no secret in common unless the owner deliberately places one value under both.
_SECRET_NAMES = (
    ("attestation", "signing_key_secret"), ("attestation", "owner_key_secret"),
    ("backup", "password_secret"), ("backup", "aws_access_key_id_secret"),
    ("backup", "aws_secret_access_key_secret"), ("airlock", "aws_profile"),
)
# The dialogue lanes Ouroboros reads, each an edge reader over one of the owner's chat applications
# (core/ingest/table.py). A named instance has none: no configuration yet names a lane of its own.
DIALOGUE_READERS = ("openwebui", "opencode")
# The Keychain/env item holding the supervisor's Vault token (config/secrets_backend.py). Not a
# config key; derived per instance like the items above, so a named instance's own Vault is never
# handed Ouroboros's token.
VAULT_TOKEN = "vault-supervisor-token"
# A Vault address: an optional scheme, a host (bracketed for IPv6) and an optional port.
_ADDRESS = re.compile(r"(?:(?P<scheme>[A-Za-z][A-Za-z0-9+.-]*)://)?"
                      r"(?P<host>\[[^\]]*\]|[^:/?#]*)(?::(?P<port>\d+))?")
_LOOPBACK = frozenset({"", "localhost", "::1", "0:0:0:0:0:0:0:1", "0.0.0.0", "::"})


class ConfigMigrationError(RuntimeError):
    """The per-machine overlay is in a state where loading would apply the WRONG values.

    Raised, never warned: see `_refuse_on_legacy_overlay`.
    """


class InstanceOverlayError(RuntimeError):
    """An overlay cannot be loaded as the instance it would be: `MIND_PALACE_OVERLAY` names no
    file; the overlay it names declares no valid `[instance] id`, or claims Ouroboros's; it sets
    what its id derives; or the instance would share a namespace with Ouroboros. The default chain,
    and a file passed to `load_config` by path, refuse the same way if they declare an id other
    than Ouroboros's.

    Raised, never warned, for the same reason as `ConfigMigrationError`: falling back to the
    committed defaults would bring a named instance up on the wrong embedder and σ, silently, and
    an instance that shares a namespace writes into another individual's state.
    """


@dataclass(frozen=True)
class OllamaConfig:
    host: str
    port: int
    default_keep_alive: str
    request_timeout_s: int          # control-plane ops (health, load, embed, evict) — fail fast
    generation_timeout_s: int       # chat generation — a heavy thinking-model pass runs minutes

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
    # The CURATED literature store (dn-external-grounding §2.2/§2.4) — a SEPARATE LanceDB from
    # `vector_store`, holding embedded open-access full text (provenance CURATED, never the mirror).
    # Default carries a value so direct `PathsConfig(...)` construction (tests) needs no change;
    # under `data/` + `*.lance/` it is gitignored by construction (Inv 11 — never git/egress).
    curated_store: Path = Path("data/research_curated.lance")


@dataclass(frozen=True)
class VaultConfig:
    """The AUTHOR-CORPUS ingestion agent — the owner's markdown vault (`vault_sync`).

    `enabled` gates every path this agent uses: its DirectoryWatcher and the startup catch-up
    reconcile. See `IngestionConfig` for why each agent carries its own lever."""

    path: Path
    pattern: str
    enabled: bool = True
    watch_debounce_s: float = 1.0
    watch_poll_interval_s: float = 5.0


@dataclass(frozen=True)
class ExhaustConfig:
    """The OUTBOUND lane (dn-exhaust-lane §2.1) — system-emitted artifacts the owner reads on his
    phone, starting with delegated-build reports under `reports/`. A sibling to [vault], NEVER an
    ingest root (§2.2, enforced by the ingest-invariant test): reports describe the system, so
    ingesting them would be recursive self-ingestion. Mirrors VaultConfig's `path`: `~` expands to
    $HOME; the exhaust dir lives outside the repo. Single source of truth — the report writer and
    the invariant test both read `get_config().exhaust.path`."""

    path: Path


@dataclass(frozen=True)
class TranscriptIngestConfig:
    """The TRANSCRIPT-SYNC ingestion agent — the dialogue sensor over the local Claude Code
    transcripts (bp-069, φ_chat; the sensor itself is `ops/chat_sensor.py`). Plain fields — the
    self-containment ratchet stays 19 (no first-party import into core.config).

    `enabled` gates the whole agent, which is BOTH of its job kinds: `chat_sync` (embed transcript
    text) and `chat_events` (project the L1 action log from those same transcripts). They are one
    agent, so they share one lever (owner ruling 2026-07-28). Every path is covered — the live
    watcher, the housekeeping pass, and the startup catch-up backfill — because a gate that misses
    the catch-up unpauses itself on the next daemon start, which is exactly deploy time.

    `transcripts_dir` is the finding-0108 G1 override: None ⇒ the resolved default
    `_default_transcripts_dir()` (`~/.claude/projects/<repo-slug>`); set it when the canonical repo
    path differs from a worktree. A small `watch_debounce_s` (0.5s) makes ingestion "immediate" to a
    human (Q4). `events_max_per_pass` caps the L1 action-log projector per pass (Item 3)."""

    enabled: bool = True
    transcripts_dir: Path | None = None
    watch_debounce_s: float = 0.5
    watch_poll_interval_s: float = 5.0
    events_max_per_pass: int = 50


@dataclass(frozen=True)
class EmbeddingConfig:
    model: str
    dim: int
    query_instruction: str
    # The model family's prompt formats. Defaults are Qwen3-Embedding's (instruction on the query,
    # plain documents) — today's behaviour; another family is a config edit, e.g. EmbeddingGemma:
    # "task: search result | query: {text}" and "title: none | text: {text}".
    query_template: str = "Instruct: {instruction}\nQuery: {text}"
    document_template: str = "{text}"


@dataclass(frozen=True)
class DreamingConfig:
    similarity_threshold: float   # cosine to join two notes into a theme cluster
    min_cluster_size: int
    max_clusters: int
    near_dup_threshold: float     # cosine to flag two notes as a near-duplicate candidate
    scheduled: bool = True        # the daemon's trough passes enqueue dream + curate; False =
                                  # on demand only (`palace dream`)


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
    # Structural interpreters (H4-H7) over core/complex/ — declared bounds (G7):
    bridge_top_k: int             # most-negative-curvature edges the bridge interpreter surfaces
    hole_min_persistence: float   # min H1 lifetime (cosine-distance units) for a long-lived hole
    thread_min_persistence: float  # min H1 lifetime (cosine-distance units) for a thread's cycle
    sbm_k_max: int                # model-selection cap for the SBM theme count (>= 1)


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
class QueryConfig:
    """The query sentence algebra's surface (dn-query-sentence-algebra §4, QL-3). The Ambassador's
    MCP server speaks one command, `query` — a sentence under the Ambassador's grant — and
    `palace query` is the owner's hand. `hypotheticals` is the owner's grant of the overlay
    (2026-11-04, §4 d): on, `assume` sentences are admitted and answered as `Hyp`, never `Inv`;
    off, they are refused as ill-scoped."""

    hypotheticals: bool = True


@dataclass(frozen=True)
class EffectorsConfig:
    """Track G effector surface (docs/design-notes/hands-and-the-effector-layer.md). Fail-closed
    twice over: `enabled` off refuses to build either side of the handoff, and an empty
    `upstreams` allowlist refuses every fetch even when enabled. `upstreams` is (name, url)
    pairs — the ONLY place a URL exists in the sensing path; the core-side request carries
    just the name.

    Sensing (β = 0) is the only class the WIRED surface admits (EffectView ceiling ε = SENSING).
    The acting-class knobs below (`ledger_db`, `drafts_dir`, `jit_credential_ttl`) support the
    built-but-off reversible/irreversible hands (G5/G6): the durable effect ledger, where a
    reversible write stages its draft, and the short TTL of the per-action JIT credential minted at
    send time. They are inert until ε is deliberately raised past sensing."""

    enabled: bool = False
    handoff_dir: Path = Path("data/handoff/sensing")
    timeout_s: float = 20.0
    max_response_kb: int = 512
    upstreams: tuple[tuple[str, str], ...] = ()
    # Acting classes (G5/G6) — built, flag-off. The ledger is a record (safe to open even off).
    ledger_db: Path = Path("data/effectors/effects.sqlite")
    drafts_dir: Path = Path("data/effectors/drafts")   # where a reversible write stages its draft
    jit_credential_ttl: str = "60s"           # per-action send credential's short TTL (class 3)


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
    # the minimum; the owner opts in per role in ouroboros.toml). vault-runtime-auth.md §3 is the
    # recommended set (e.g. correlator, advisor) — each must have a matching Vault token role.
    grant_roles: frozenset[str] = frozenset()
    token_ttl: str = "10m"   # TTL of a minted agent token — short; the grant expires by itself


@dataclass(frozen=True)
class BackupConfig:
    """restic → S3 encrypted backups (BUILD-SPEC §16b). restic encrypts + deduplicates CLIENT-SIDE,
    so AWS never sees plaintext; the bucket's SSE-KMS is defense in depth. `enabled` gates the
    scheduled job only. The repo password and the backup AWS key live in Keychain (named here, never
    stored here). Off by default — turn on per machine via config/ouroboros.toml once the bucket is
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
    until the owner deliberately turns each on in config/ouroboros.toml."""

    enabled: bool = False
    unattended_enabled: bool = False
    ledger_db: Path = Path("data/selfmod_ledger.sqlite")


@dataclass(frozen=True)
class CodeIngestConfig:
    """The CODE-SYNC ingestion agent (dn-code-ingest-pipeline / bp-092..094; enable path bp-098).

    `enabled` gates the agent's automatic paths — the INCREMENTAL housekeeping sync (`code_sync`)
    and the startup catch-up history backfill (`code_backfill`). The one-time heavy SEED stays the
    deliberate owner-visible `palace code-seed`, never auto-run from a flag flip (note §2.7).
    `max_chars`/`overlap_chars` mirror the note chunker budget so L0b windows and L1 prose chunks
    share the corpus-wide grain (note §2.2)."""

    enabled: bool = False
    max_chars: int = 1200
    overlap_chars: int = 150


@dataclass(frozen=True)
class IntegrateConfig:
    """The INTEGRATOR — its own agent type, deliberately NOT an ingestion agent (owner ruling
    2026-07-28). It ingests nothing: it derives C-fiber proven edges from the already-ingested L1
    action log and the ledger (bp-071). That is why it sits outside `[ingestion]` and carries its
    own lever, rather than riding on the transcript agent's the way `chat_events` does."""

    enabled: bool = True
    max_per_pass: int = 50


@dataclass(frozen=True)
class IngestionConfig:
    """The ingestion agents, one subsection each (owner ruling 2026-07-28: *"it should be per
    agent... the code-sync ingestion agent is its own ingestion section, the transcript-sync
    ingestion is its own ingestion section, the author corpus ingestion (vault) is its own
    ingestion section"*).

    Each agent owns exactly one `enabled` lever, and that lever gates EVERY path the agent uses —
    watcher, housekeeping pass, and startup catch-up. One flag spanning several agents was rejected
    for the reason this grouping fixes: a lever has to say which agent it stops, and a section has
    to contain only what its lever governs. `chat_events` rides the transcript agent because it is
    part of transcript ingestion; `integrate` does not, because it is a different kind of agent.

    Mirrors `[ingestion.*]` in the TOML exactly, so `cfg.ingestion.code.enabled` and
    `[ingestion.code] enabled` are the same name twice rather than two names that must be kept in
    sync by hand."""

    vault: VaultConfig
    transcripts: TranscriptIngestConfig = field(default_factory=TranscriptIngestConfig)
    code: CodeIngestConfig = field(default_factory=CodeIngestConfig)


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
class RuntimeConfig:
    """Which local inference RUNTIME serves each role (dn-local-model-runtime §4).

    Landed WHOLE, including the keys the process manager (bp-116) and the cutover (bp-118)
    consume, because `_overlay` merges by section NAME: a `[runtime]` block in `ouroboros.toml`
    with no dataclass behind it is silently DROPPED (the bp-102 / finding-0174 mechanism), so a
    half-defined section is worse than none. Every default here is TODAY'S behaviour — the seam
    changes nothing at landing, and each flip is the owner's, per role, in `config/ouroboros.toml`.

    `chat_backend` is a plain dict rather than this file's usual immutable tuple/frozenset: the
    per-tier override map is pinned as `dict[str, str]` by bp-115 §6. `Config` is consequently
    no longer hashable — nothing hashes it (no `lru_cache` takes a Config; `get_config` caches
    on no arguments), and `dataclasses.replace` is unaffected.
    """

    embedding_backend: str = "ollama"        # "ollama" | "llamacpp"; default UNCHANGED
    chat_backend: dict[str, str] = field(default_factory=dict)  # per-tier; empty = ollama
    server_binary: str = ""                  # llama-server path; "" = not configured (bp-116)
    pinned_build: str = ""                   # asserted at spawn (bp-116); "" = unpinned
    embed_ctx: int = 8192                    # §2.3: right-sized from the model default 40960
    grace_s: float = 5.0                     # SIGTERM -> SIGKILL window (bp-116)
    # Owner-launched llama-servers (interim, until bp-116 assigns ports at spawn): the port each
    # role's server listens on — `embedding` or a tier name. Empty = every role on the
    # llama-server default port, today's behaviour.
    ports: dict[str, int] = field(default_factory=dict)
    # NAME of an environment variable holding a bearer key for those servers ("" = no key). The
    # value is read from the environment at client build time and never from a file or this
    # config (Invariant 10).
    api_key_env: str = ""

    def chat_backend_for(self, tier: str) -> str:
        """Backend serving one chat tier. An unlisted tier stays on `ollama` — per-ROLE
        selection is what makes the embedder cutover (P4) independently reversible."""
        return self.chat_backend.get(tier, "ollama")

    def port_for(self, role: str) -> int | None:
        """The configured llama-server port for `role` (`embedding` or a tier), or None for the
        client's default."""
        return self.ports.get(role)


@dataclass(frozen=True)
class SchedulerConfig:
    """The supervisor's execution model (dn-supervision-and-liveness §4 Wiring).

    Landed WHOLE, including the keys bp-111 (lease) and bp-112 (escalation) consume, because
    `_overlay` merges by section NAME: a `[scheduler]` block in `ouroboros.toml` with no dataclass
    behind it is silently DROPPED (the bp-102 / finding-0174 mechanism). A half-defined section is
    worse than none — the owner flips a knob, the flip looks applied, and it never took. Same
    reasoning, same shape, as `RuntimeConfig` above.

    Every default here is TODAY'S BEHAVIOUR: `inproc` dispatch, no deadlines, no budgets, no
    lease. Nothing observable changes by this section existing.

    ⚑ `job_budgets` is a PER-KIND MAP, not the scalar `job_budget_s` bp-110 §6 pinned — a
    deliberate, recorded correction (finding-0228, `[banner: correction]`). The consumer that
    already exists is `JobQueue.job_budgets: Mapping[str, float]` (`scheduler/queue.py:296`, used
    at `:435` to stamp `lease_expires_at = started_at + job_budgets[kind]`), and a scalar cannot
    be expressed in it: `claim()` looks the budget up BY KIND, so a single number would have to be
    fanned out over every kind at construction, or merged with a second per-kind source — which is
    the parallel budget source finding-0225 exists to prevent. The design note's own §4 says
    "`job_budget_s` **per-kind overrides**"; the scalar in §6 is the drafting slip. An unconsumable
    key would be an inert knob that looks live, which is precisely the failure this whole section
    is schema'd to avoid.

    Empty map = every claim stamps a NULL deadline = byte-for-byte today's behaviour. No number is
    invented here: the value is a parked decision (bp-109 §11) whose re-entry is bp-112 landing
    escalation with a MEASURED budget. The live `code_backfill` lane legitimately runs for hours,
    so a guessed value would kill a healthy pass on schedule — bp-102 §10's cry-wolf disqualifier.
    """

    worker_mode: str = "inproc"        # "inproc" | "subprocess"; default per note §4
    batch_deadline_s: float = 0.0      # 0 = no deadline (today's behaviour)
    job_budgets: dict[str, float] = field(default_factory=dict)  # kind -> seconds; {} = no budget
    escalation_grace_s: float = 30.0   # SIGTERM -> N -> SIGKILL; consumed by bp-112
    lease_ttl_s: float = 0.0           # 0 = no lease; consumed by bp-111 after V9  (lease plan)


@dataclass(frozen=True)
class ModelConfig:
    name: str
    tier: str
    pinned: bool
    resident_gb: float
    num_ctx: int
    evicts_pinned: bool = False


@dataclass(frozen=True)
class InstanceConfig:
    """Which individual this configuration is (DI-2, issue #25), and the names derived from it.

    `id` is `ouroboros` for the default chain: no `MIND_PALACE_OVERLAY`, the live instance, read
    exactly as before instances had ids. Its overlay may restate `[instance] id = "ouroboros"` and
    nothing else. A named overlay must declare its own id, which may not be Ouroboros's, and every
    namespace the instance holds is derived from that id:

        namespace          Ouroboros                     named instance <id>
        root               <repo>                        <repo>/instances/<id>
        data dir, stores   <repo>/data/…                 <root>/data/…
        ingestion spool    <repo>/data/handoff           <root>/data/handoff
        supervisor lock    <repo>/data/supervisor.lock   <root>/data/supervisor.lock
        levers overlay     <repo>/config/levers.toml     <root>/levers.toml
        Keychain items     attestation-signing-key, …    <id>.attestation-signing-key, …
        launchd labels     com.mind-palace.palace, …     com.mind-palace.<id>.palace, …
        restic repository  as its overlay names it       its overlay's, whose last segment is <id>
        vault source       ~/.mind-palace/vault          declared, else <root>/vault and off
        transcripts        ~/.claude/projects/<repo>     declared, else <root>/transcripts and off
        code agent         the checkout                  off unless its overlay turns it on
        dialogue lanes     openwebui, opencode           none
        airlock in S3      as its overlay names it       as its overlay names it
        exhaust lane       ~/.mind-palace/exhaust        <root>/exhaust, moved only within root
        Vault server       [secrets] addr                its overlay's own; none if it names none

    A declared source may lie anywhere but inside, around or at one of Ouroboros's locations.
    `namespaces_of` reads them off a built Config, and `shared` says what two instances hold in
    common. The map is injective: distinct ids give disjoint namespaces, none of them Ouroboros's.
    """

    id: str = OUROBOROS

    def __post_init__(self) -> None:
        # The map is defined on well-formed ids only: built from `../x`, `root` would climb out of
        # `instances/`. The loader refuses such an id with a message first; this holds for any
        # other caller too.
        if not isinstance(self.id, str) or not _INSTANCE_ID.fullmatch(self.id):
            raise ValueError(f"not an instance id: {self.id!r}")

    @property
    def named(self) -> bool:
        """True for an instance other than Ouroboros."""
        return self.id != OUROBOROS

    @property
    def root(self) -> Path:
        """What this instance's relative data paths resolve against: the repo root for Ouroboros,
        so `data/` is where it always was, and `<repo>/instances/<id>` for a named instance."""
        return REPO_ROOT / _INSTANCES / self.id if self.named else REPO_ROOT

    @property
    def levers(self) -> Path:
        """The machine-owned knob overlay this instance's self-modification loop writes and its
        loader reads: `config/levers.toml` for Ouroboros, `<root>/levers.toml` for a named one."""
        return self.root / "levers.toml" if self.named else LEVERS_OVERLAY

    @property
    def dialogue(self) -> tuple[str, ...]:
        """The dialogue lanes this instance reads: Ouroboros's two, a named instance none."""
        return () if self.named else DIALOGUE_READERS

    def label(self, role: str) -> str:
        """The launchd label of this instance's `role` service, one of `LAUNCHD_ROLES`."""
        return LABEL_PREFIX + (f"{self.id}.{role}" if self.named else role)

    def secret(self, name: str) -> str:
        """The Keychain/env item this instance reads the secret `name` from."""
        return f"{self.id}.{name}" if self.named else name


@dataclass(frozen=True)
class Config:
    ollama: OllamaConfig
    resources: ResourceConfig
    paths: PathsConfig
    # The ingestion agents, one subsection each — mirrors `[ingestion.*]` in the TOML.
    ingestion: IngestionConfig
    exhaust: ExhaustConfig
    embedding: EmbeddingConfig
    dreaming: DreamingConfig
    dream_rnd: DreamRnDConfig
    sandbox: SandboxConfig
    interface: InterfaceConfig
    airlock: AirlockConfig
    models: tuple[ModelConfig, ...]
    # Default keeps direct Config(...) construction (e.g. in tests) working without this section.
    integrate: IntegrateConfig = field(default_factory=IntegrateConfig)  # bp-071, not an ingestor
    ambassador: AmbassadorConfig = field(default_factory=AmbassadorConfig)
    attestation: AttestationConfig = field(default_factory=AttestationConfig)
    secrets: SecretsConfig = field(default_factory=SecretsConfig)
    backup: BackupConfig = field(default_factory=BackupConfig)
    selfmod: SelfModConfig = field(default_factory=SelfModConfig)
    effectors: EffectorsConfig = field(default_factory=EffectorsConfig)
    runtime: RuntimeConfig = field(default_factory=RuntimeConfig)  # bp-115 inference backend
    scheduler: SchedulerConfig = field(default_factory=SchedulerConfig)  # bp-110 execution model
    query: QueryConfig = field(default_factory=QueryConfig)  # QL-3: the sentence algebra's surface
    instance: InstanceConfig = field(default_factory=InstanceConfig)  # DI-2: which individual

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


@dataclass(frozen=True)
class Namespaces:
    """What one instance holds as its own: the state it writes, the sources it reads, the secrets
    it reads, the services it runs as, the repository it backs up to (DI-2).

    The invariant: for instances i ≠ j, Ouroboros among them, `shared(N(i), N(j))` is empty: no
    location one writes or reads lies at, inside or around a location of the other. For named
    instances it holds by construction, because each name is derived from the id
    (`InstanceConfig`) and none of the derived names is Ouroboros's; a named overlay that would
    break it refuses at load (`_refuse_reaching_out`, `_refuse_shared`). A source a named overlay
    declares is checked against Ouroboros's; two named instances may deliberately read one corpus.
    The property test over generated ids is tests/property/test_instance_namespaces.py.
    """

    data_dir: Path
    spool: Path               # cfg.interface.handoff_dir: the ingestion spool and the inbox
    supervisor_lock: Path
    levers: Path
    exhaust: Path             # the outbound lane its reports land in
    paths: frozenset[Path]    # the five above, and every other path the config names it writes
    sources: frozenset[Path]  # the corpus locations it reads: its vault and transcripts dirs
    dialogue: frozenset[str]  # the dialogue lanes it reads (`DIALOGUE_READERS`)
    secrets: frozenset[str]   # Keychain/env item names
    labels: frozenset[str]    # launchd labels
    backup: str               # its restic repository; "" when none is configured
    airlock: frozenset[str]   # its airlock's S3 request and result prefixes, when it has a bucket
    vault: str                # its Vault server as `host:port`; "" when it has none


def namespaces_of(cfg: Config) -> Namespaces:
    """The namespaces `cfg`'s instance holds, read off the config as built."""
    data, instance = cfg.paths.data_dir, cfg.instance
    lock = data / SUPERVISOR_LOCK
    written = {getattr(getattr(cfg, section), key) for section, key in _DATA_PLANE}
    transcripts = cfg.ingestion.transcripts.transcripts_dir or default_transcripts_dir()
    air = cfg.airlock
    return Namespaces(
        data_dir=data,
        spool=cfg.interface.handoff_dir,
        supervisor_lock=lock,
        levers=instance.levers,
        exhaust=cfg.exhaust.path,
        paths=frozenset({*written, lock, instance.levers, cfg.exhaust.path}),
        sources=frozenset({cfg.ingestion.vault.path, transcripts}),
        dialogue=frozenset(instance.dialogue),
        secrets=frozenset({*(getattr(getattr(cfg, section), key) for section, key in _SECRET_NAMES),
                           instance.secret(VAULT_TOKEN)}),
        labels=frozenset(instance.label(role) for role in LAUNCHD_ROLES),
        backup=cfg.backup.repository,
        airlock=frozenset({f"s3://{air.s3_bucket}/{prefix}"
                           for prefix in (air.requests_prefix, air.results_prefix)}
                          if air.s3_bucket else ()),
        vault=vault_location(cfg.secrets.addr),
    )


def vault_location(addr: str) -> str:
    """A Vault server as `host:port`, every loopback spelling as one host, so two spellings of
    one server compare equal: `http://127.0.0.1:8200`, `localhost:8200/` and `http://[::1]:8200` are
    all `loopback:8200`. A port left out is the scheme's. "" for no address."""
    match = _ADDRESS.match(addr.strip())
    if not addr.strip() or match is None:
        return addr.strip().casefold()
    host = match["host"].strip("[]").casefold()
    if host in _LOOPBACK or host.startswith("127."):
        host = "loopback"
    port = match["port"] or ("443" if (match["scheme"] or "").casefold() == "https" else "80")
    return f"{host}:{int(port)}"


def default_transcripts_dir() -> Path:
    """This checkout's Claude Code transcripts dir, `~/.claude/projects/<repo path, / as ->`: the
    transcript source when `[ingestion.transcripts] transcripts_dir` is unset (Ouroboros's; a named
    instance's is always set)."""
    return Path.home() / ".claude" / "projects" / str(REPO_ROOT).replace("/", "-")


def _within(a: str, b: str, separators: str) -> bool:
    """`a` and `b` name one location, or one lies inside the other at a separator."""
    return a == b or any(a.startswith(b + s) or b.startswith(a + s) for s in separators)


def _location(path: Path) -> str:
    # Absolute, normalised and case-folded, because APFS (the macOS default) folds case: `Data` and
    # `data` are one directory.
    return os.path.abspath(path).casefold()


def _remote(url: str) -> str:
    return url.rstrip("/").casefold()


def shared(a: Namespaces, b: Namespaces) -> list[str]:
    """What two instances' namespaces have in common, one line each; [] when they are disjoint.
    Every location either writes or reads is compared with every location of the other, so a
    source inside the other's data dir is shared, and so is a directory nested in one of the
    other's. Remote locations (the restic repository, the airlock prefixes) compare the same way:
    one nested in another's is written under the other's prefix."""
    here, there = a.paths | a.sources, b.paths | b.sources
    out = [f"location {p} and {q}" for p in sorted(here) for q in sorted(there)
           if _within(_location(p), _location(q), os.sep)]
    out += [f"dialogue lane {lane}" for lane in sorted(a.dialogue & b.dialogue)]
    out += [f"secret {name}" for name in sorted(a.secrets & b.secrets)]
    out += [f"label {label}" for label in sorted(a.labels & b.labels)]
    if a.backup and b.backup and _within(_remote(a.backup), _remote(b.backup), "/:"):
        out.append(f"backup repository {a.backup} and {b.backup}")
    out += [f"airlock prefix {x} and {y}" for x in sorted(a.airlock) for y in sorted(b.airlock)
            if _within(_remote(x), _remote(y), "/")]
    if a.vault and a.vault == b.vault:
        out.append(f"Vault server {a.vault}")
    return out


def _resolve(p: str, base: Path | None = None) -> Path:
    """A relative path joins `base`, the repo root unless given; an absolute one stands."""
    path = Path(p)
    return path if path.is_absolute() else (REPO_ROOT if base is None else base) / path


def _deep_merge(base: dict[str, Any], incoming: dict[str, Any]) -> None:
    """Recursively merge `incoming` into `base` in place: table-vs-table recurses, anything else
    replaces. Depth matters as soon as a section has SUBSECTIONS (`[ingestion.transcripts]`).

    A one-level `base[section].update(values)` is wrong there, and wrong SILENTLY. An overlay
    saying only

        [ingestion.transcripts]
        enabled = false

    parses as `{"ingestion": {"transcripts": {"enabled": False}}}`, and a shallow update replaces
    the whole `transcripts` table — dropping `transcripts_dir`, `watch_debounce_s`,
    `events_max_per_pass`. Nothing raises: every reader below uses `.get(key, default)`, so the
    instance silently falls back to the dataclass defaults instead of the committed defaults.toml
    values. That is the same class of failure `_refuse_on_legacy_overlay` refuses one level up —
    a config reversion learned about from behaviour weeks later — so it is fixed here rather than
    documented as a footgun."""
    for key, value in incoming.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value


def _overlay(raw: dict[str, Any], path: Path) -> None:
    """Per-section merge of `path` onto `raw` in place — the overlay names just the keys it
    changes (e.g. `[secrets]\nenabled = true`), leaving every other default intact. Recursive, so
    a nested `[ingestion.code]` overlay merges into that subsection instead of replacing it."""
    if not path.exists():
        return
    _deep_merge(raw, tomllib.loads(path.read_text(encoding="utf-8")))


def _refuse_on_legacy_overlay() -> None:
    """Refuse to load while a pre-2026-07-26 `local.toml` would be silently ignored (bp-123).

    ⚑ This RAISES; it deliberately does not warn. A warning on the config path is a false green one
    level down: the process would come up on the committed defaults — the wrong σ, and every flag
    the owner enabled in his overlay silently off — and he would learn about it from behaviour weeks
    later instead of from an error. Refusing costs one `mv`; warning costs a silent config reversion
    on the live instance.

    Three states:
      legacy present, current absent -> the overlay would be ignored outright. REFUSE, name the mv.
      both present                   -> authority is ambiguous. REFUSE; do not guess a winner.
      neither present                -> a fresh clone or CI. Silent by design: committed defaults
                                        only, so a guard for a one-time migration never breaks a
                                        machine that has nothing to migrate.
    """
    if not _LEGACY_OVERLAY.exists():
        return
    if _INSTANCE_OVERLAY.exists():
        raise ConfigMigrationError(
            f"two per-machine config overlays are present, and which one carries authority is "
            f"ambiguous:\n"
            f"    {_LEGACY_OVERLAY}  (the pre-2026-07-26 name)\n"
            f"    {_INSTANCE_OVERLAY}  (the current name)\n"
            f"Refusing to load rather than guess which one wins. Merge whatever you still need out "
            f"of local.toml into ouroboros.toml by hand, then remove the legacy file:\n"
            f"    rm {_LEGACY_OVERLAY}"
        )
    raise ConfigMigrationError(
        f"the per-machine config overlay was renamed local.toml -> ouroboros.toml on 2026-07-26, "
        f"and this machine has not been migrated:\n"
        f"    {_LEGACY_OVERLAY}  exists (the old name — NO LONGER READ)\n"
        f"    {_INSTANCE_OVERLAY}  is missing (the name the loader reads)\n"
        f"Loading now would silently ignore every setting in local.toml and come up on the "
        f"committed defaults instead. Refusing to load. Move the file — `mv`, never rewrite, the "
        f"bytes are an owner ruling:\n"
        f"    mv {_LEGACY_OVERLAY} {_INSTANCE_OVERLAY}"
    )


def _named_overlay() -> Path | None:
    """The overlay `MIND_PALACE_OVERLAY` names, or None when it is unset or empty. A relative path
    resolves against the repo root, like every path in the tomls; one that is not a file refuses."""
    named = os.environ.get(OVERLAY_ENV, "")
    if not named:
        return None
    path = Path(named).expanduser()
    path = path if path.is_absolute() else REPO_ROOT / path
    if not path.is_file():
        raise InstanceOverlayError(
            f"{OVERLAY_ENV}={named!r} names no file ({path}). Refusing to load: the committed "
            f"defaults are not this instance's configuration. Unset {OVERLAY_ENV} to load the "
            f"default chain, or point it at the instance's overlay."
        )
    return path


def ouroboros_only(what: str) -> None:
    """Refuse while `MIND_PALACE_OVERLAY` selects a named instance, for a tool that names
    Ouroboros's own state outside the config: its data dir by path, its services, its sources, its
    archive, its Vault. Such a tool would act on Ouroboros's state for the named instance (DI-2)."""
    named = os.environ.get(OVERLAY_ENV, "")
    if named:
        raise InstanceOverlayError(
            f"{what} acts on Ouroboros's own state; refusing under {OVERLAY_ENV}={named!r}. "
            f"Unset {OVERLAY_ENV} to run it for Ouroboros.")


def _read(path: Path) -> dict[str, Any]:
    return tomllib.loads(path.read_text(encoding="utf-8"))


def _declared_id(table: object, source: str) -> str | None:
    """The id an `[instance]` table declares, or None when there is no table or no id in it.

    The table holds `id` and nothing else, so any other key refuses: the loader would ignore it,
    and a setting that looks applied but never took is the failure every refusal here exists for.
    """
    if table is None:
        return None
    if not isinstance(table, dict):
        raise InstanceOverlayError(f"{source}: [instance] must be a table holding one key, id.")
    extra = sorted(set(table) - {"id"})
    if extra:
        raise InstanceOverlayError(
            f"{source}: [instance] holds one key, id; refusing the unknown key(s) {extra}.")
    if "id" not in table:
        return None
    iid = table["id"]
    if not isinstance(iid, str) or not _INSTANCE_ID.fullmatch(iid):
        raise InstanceOverlayError(
            f"{source}: [instance] id = {iid!r} is not an instance id. An id is a lowercase "
            f"letter followed by up to 31 lowercase letters, digits or hyphens.")
    return iid


def _named_instance(declared: dict[str, Any], source: Path) -> InstanceConfig:
    """The instance a named overlay declares. The id is required: it is what tells this instance
    apart from every other, Ouroboros included, and Ouroboros's id belongs to the default chain."""
    iid = _declared_id(declared.get("instance"), str(source))
    if iid is None:
        raise InstanceOverlayError(
            f"{source} declares no instance id. A named overlay says which individual it is:\n"
            f"    [instance]\n"
            f'    id = "<id>"\n'
            f"Refusing to load it unnamed. Unset {OVERLAY_ENV} to load the default chain.")
    if iid == OUROBOROS:
        raise InstanceOverlayError(
            f"{source}: [instance] id = {OUROBOROS!r} is the default chain's, the live instance. "
            f"Refusing to load a second {OUROBOROS!r}: give this instance its own id, or unset "
            f"{OVERLAY_ENV} to load the default chain.")
    return InstanceConfig(iid)


def _ouroboros_instance(raw: dict[str, Any], source: str) -> InstanceConfig:
    """The default chain is Ouroboros, and so is a file `load_config` reads by path. Its
    `[instance]` may restate that; another id would rename the live instance in place."""
    iid = _declared_id(raw.get("instance"), source)
    if iid is not None and iid != OUROBOROS:
        raise InstanceOverlayError(
            f"{source}: [instance] id = {iid!r}, but this configuration is {OUROBOROS!r}. "
            f"Another instance is loaded from its own overlay, {OVERLAY_ENV}=<path>; refusing to "
            f"load {OUROBOROS!r} under another id.")
    return InstanceConfig()


def _last_segment(repository: str) -> str:
    """The final path component of a restic repository location (`s3:host/bucket/<seg>`,
    `/srv/restic/<seg>`, `sftp:host:/srv/<seg>`, `b2:bucket:<seg>`)."""
    return re.split(r"[/:]", repository.rstrip("/"))[-1]


def _own_source(instance: InstanceConfig, name: str) -> Path:
    """Where an undeclared source or lane of a named instance points: `<root>/<name>`, inside
    its own root, where nothing is unless the instance puts it there."""
    return instance.root / name


def _own_sources(raw: dict[str, Any], declared: dict[str, Any], instance: InstanceConfig,
                 source: Path) -> None:
    """A named instance reads only the sources its own overlay declares; the committed defaults
    name Ouroboros's corpus, so they never reach it. An undeclared vault or transcripts dir points
    into its root (`_own_source`) and its agent is off; the code agent, whose source is the shared
    checkout, is off unless the overlay turns it on. Turning an agent on without naming its source
    refuses. A declared location is taken as given, a relative one under the root, and
    `_refuse_shared` then refuses one at, inside or around a location of Ouroboros's."""
    agents = raw.setdefault("ingestion", {})
    said = declared.get("ingestion", {})
    for agent, key in (("vault", "path"), ("transcripts", "transcripts_dir")):
        section, own = agents.setdefault(agent, {}), said.get(agent, {})
        if own.get(key):
            path = Path(str(own[key])).expanduser()
            section[key] = str(path if path.is_absolute() else instance.root / path)
            continue
        if own.get("enabled") is True:
            raise InstanceOverlayError(
                f"{source}: [ingestion.{agent}] enabled = true, but the overlay names no {key}. "
                f"A named instance reads only a source it declares; refusing to read the "
                f"committed default, which is Ouroboros's.")
        section[key] = str(_own_source(instance, agent))
        section["enabled"] = False
    if "enabled" not in said.get("code", {}):
        agents.setdefault("code", {})["enabled"] = False
    # The exhaust lane is written, not read, so it derives like a data path: `<root>/exhaust`
    # unless the overlay moves it within the root (`_refuse_reaching_out` checks that).
    if not declared.get("exhaust", {}).get("path"):
        raw.setdefault("exhaust", {})["path"] = str(_own_source(instance, "exhaust"))


def _own_vault_addr(instance: InstanceConfig) -> str:
    """The Vault a named instance reaches when its overlay names none: none at all."""
    return ""


def _own_vault(raw: dict[str, Any], declared: dict[str, Any], instance: InstanceConfig,
               source: Path) -> None:
    """A named instance reaches only a Vault its overlay names (`[secrets] addr`); the committed
    default is the Vault on this host, which is Ouroboros's. Naming none, it runs with no Vault
    secrets, and turning `[secrets]` on without an address refuses. A named address that is
    Ouroboros's server, in any spelling, refuses through `_refuse_shared`."""
    secrets = raw.setdefault("secrets", {})
    if declared.get("secrets", {}).get("addr"):
        return
    if secrets.get("enabled") is True:
        raise InstanceOverlayError(
            f"{source}: [secrets] enabled = true, but the overlay names no addr. A named instance "
            f"reaches only a Vault of its own; refusing to reach the default, which is "
            f"Ouroboros's.")
    secrets["addr"] = _own_vault_addr(instance)
    secrets["enabled"] = False


def _refuse_reaching_out(raw: dict[str, Any], declared: dict[str, Any],
                         committed: dict[tuple[str, str], Any], instance: InstanceConfig,
                         source: Path) -> None:
    """A named instance may not set what its id derives. Refused, not overridden: a value the
    overlay states and the loader replaces is a setting that looks applied and never took. A
    secret name refuses when the overlay names it at all, even as the committed default, and when
    the merged chain (`raw`) holds anything but the committed default (`committed`)."""
    for (section, key), value in committed.items():
        if key in declared.get(section, {}) or raw.get(section, {}).get(key) != value:
            raise InstanceOverlayError(
                f"{source}: [{section}] {key} is derived from the instance id, as "
                f"{instance.secret(str(value))!r}, and a named overlay does not set it. Remove the "
                f"key; place the secret under the derived name.")
    lane = declared.get("exhaust", {}).get("path")
    for section, key, value in (*((s, k, raw.get(s, {}).get(k)) for s, k in _DATA_PLANE),
                                ("exhaust", "path", lane)):
        if value and (Path(str(value)).expanduser().is_absolute()
                      or ".." in Path(str(value)).parts):
            raise InstanceOverlayError(
                f"{source}: [{section}] {key} = {value!r} leaves the instance's root "
                f"{instance.root}. A named instance's paths are relative and resolve under its "
                f"root; refusing one that could reach another instance's state.")
    repository = str(raw.get("backup", {}).get("repository", ""))
    if repository and _last_segment(repository) != instance.id:
        raise InstanceOverlayError(
            f"{source}: [backup] repository = {repository!r} is not this instance's own location. "
            f"A named instance's restic repository ends in /{instance.id}, so that no two "
            f"instances write one repository.")


def _ouroboros() -> Config:
    """Ouroboros's configuration, built only for its namespaces: defaults ← levers.toml ←
    ouroboros.toml, the default chain. None of its values reaches a named instance's Config."""
    raw = _read(_DEFAULTS)
    _overlay(raw, LEVERS_OVERLAY)
    _overlay(raw, _INSTANCE_OVERLAY)
    return _build(raw, InstanceConfig())


def _refuse_shared(cfg: Config, source: Path) -> None:
    """A named instance shares no namespace with Ouroboros. Ouroboros's are read off its own
    chain on this host, so an overlay that names Ouroboros's restic repository, or a location
    inside it, refuses outright."""
    both = shared(namespaces_of(cfg), namespaces_of(_ouroboros()))
    if both:
        raise InstanceOverlayError(
            f"{source}: instance {cfg.instance.id!r} would share these with {OUROBOROS!r}:\n    "
            + "\n    ".join(both)
            + "\nRefusing to load: an instance writes only into namespaces of its own.")


def load_config(path: Path | None = None) -> Config:
    raw = _read(path or _DEFAULTS)
    # Overlay precedence (only for the default path — an explicit `path`, as tests pass, is taken
    # verbatim): defaults ← levers.toml ← ouroboros.toml. The machine-tuned knobs land first; the
    # owner's hand-authored ouroboros.toml lands LAST so a human override always wins over a
    # loop-tuned knob (human authority supreme — the §14 ceiling). See LEVERS_OVERLAY /
    # _INSTANCE_OVERLAY above. The legacy guard runs first: an un-migrated overlay must refuse here,
    # not sail past and hand back defaults. An explicit `path` bypasses the whole chain, guard
    # included — it is a verbatim read of the file the caller named, and it is Ouroboros's.
    #
    # A named instance (`MIND_PALACE_OVERLAY`) replaces the chain: defaults ← its own levers file ←
    # its own overlay, and nothing of Ouroboros's. The legacy guard is about Ouroboros's file name,
    # so it does not run. Its namespaces derive from its id (`InstanceConfig`); the overlay may not
    # set them, it reads only the sources it declares (`_own_sources`), and the instance may not
    # share a location with Ouroboros, whose chain is read for that check alone.
    if path is not None:
        return _build(raw, _ouroboros_instance(raw, str(path)))
    named = _named_overlay()
    if named is None:
        _refuse_on_legacy_overlay()
        _overlay(raw, LEVERS_OVERLAY)
        _overlay(raw, _INSTANCE_OVERLAY)
        return _build(raw, _ouroboros_instance(raw, "the default chain"))
    declared = _read(named)
    instance = _named_instance(declared, named)
    committed = {(s, k): raw.get(s, {}).get(k) for s, k in _SECRET_NAMES}
    _overlay(raw, instance.levers)      # its own loop-tuned knobs, under its hand overlay
    _deep_merge(raw, declared)
    _own_sources(raw, declared, instance, named)
    _own_vault(raw, declared, instance, named)
    _refuse_reaching_out(raw, declared, committed, instance, named)
    cfg = _build(raw, instance)
    _refuse_shared(cfg, named)
    return cfg


def _build(raw: dict[str, Any], instance: InstanceConfig) -> Config:
    """The typed Config of one merged chain, for `instance`: every path in `_DATA_PLANE` resolves
    against the instance's root, and every secret name in `_SECRET_NAMES` is the instance's item.
    For Ouroboros both are the identity, so its Config is what it was before instances had ids."""
    root = instance.root

    def secret(name: object) -> str:
        return instance.secret(str(name))

    o, r, p = raw["ollama"], raw["resources"], raw["paths"]
    e, s = raw["embedding"], raw["sandbox"]
    itf, dr, rnd = raw["interface"], raw["dreaming"], raw["dream_rnd"]
    al, at = raw["airlock"], raw.get("attestation", {})
    # The ingestion agents live under one nested table, one subsection per agent.
    ing = raw.get("ingestion", {})
    v, ch, ci = ing.get("vault", {}), ing.get("transcripts", {}), ing.get("code", {})
    integ = raw.get("integrate", {})
    amb = raw.get("ambassador", {})
    sec = raw.get("secrets", {})
    bak = raw.get("backup", {})
    sm = raw.get("selfmod", {})
    eff = raw.get("effectors", {})
    rt = raw.get("runtime", {})
    sch = raw.get("scheduler", {})
    qry = raw.get("query", {})
    return Config(
        ollama=OllamaConfig(
            host=o["host"],
            port=int(o["port"]),
            default_keep_alive=str(o["default_keep_alive"]),
            request_timeout_s=int(o["request_timeout_s"]),
            # .get keeps older/custom TOMLs (without this key) loading; default = 10 min, which
            # comfortably covers a large thinking-model synthesis pass (measured ~290s for 27b).
            generation_timeout_s=int(o.get("generation_timeout_s", 600)),
        ),
        resources=ResourceConfig(
            usable_ram_gb=float(r["usable_ram_gb"]),
            max_resident_models=int(r["max_resident_models"]),
        ),
        paths=PathsConfig(
            data_dir=_resolve(p["data_dir"], root),
            telemetry_db=_resolve(p["telemetry_db"], root),
            raw_store=_resolve(p["raw_store"], root),
            vector_store=_resolve(p["vector_store"], root),
            derived_store=_resolve(p["derived_store"], root),
            vault_catalog=_resolve(p["vault_catalog"], root),
            # .get default keeps older/custom TOMLs (without this key) loading.
            attestation_store=_resolve(p.get("attestation_store", "data/attestations.sqlite"),
                                       root),
            curated_store=_resolve(p.get("curated_store", "data/research_curated.lance"), root),
        ),
        ingestion=IngestionConfig(
            vault=VaultConfig(
                # ~ expands to $HOME; the vault is the owner's source corpus, outside the repo.
                path=Path(v["path"]).expanduser(),
                pattern=str(v["pattern"]),
                enabled=bool(v.get("enabled", True)),
                watch_debounce_s=float(v.get("watch_debounce_s", 1.0)),
                watch_poll_interval_s=float(v.get("watch_poll_interval_s", 5.0)),
            ),
            transcripts=TranscriptIngestConfig(
                enabled=bool(ch.get("enabled", True)),
                # transcripts_dir override (finding-0108 G1): ~ expands to $HOME; unset ⇒ None ⇒
                # the sensor's resolved default. Other fields are plain knobs (ratchet stays 19).
                transcripts_dir=(Path(ch["transcripts_dir"]).expanduser()
                                 if ch.get("transcripts_dir") else None),
                watch_debounce_s=float(ch.get("watch_debounce_s", 0.5)),
                watch_poll_interval_s=float(ch.get("watch_poll_interval_s", 5.0)),
                events_max_per_pass=int(ch.get("events_max_per_pass", 50)),
            ),
            code=CodeIngestConfig(
                enabled=bool(ci.get("enabled", False)),
                max_chars=int(ci.get("max_chars", 1200)),
                overlap_chars=int(ci.get("overlap_chars", 150)),
            ),
        ),
        # ~ expands to $HOME; the exhaust dir is the owner's outbound sync, outside the repo.
        exhaust=ExhaustConfig(path=_resolve(raw["exhaust"]["path"], root) if instance.named
                              else Path(raw["exhaust"]["path"]).expanduser()),
        embedding=EmbeddingConfig(
            model=str(e["model"]),
            dim=int(e["dim"]),
            query_instruction=str(e["query_instruction"]),
            query_template=str(e.get("query_template", "Instruct: {instruction}\nQuery: {text}")),
            document_template=str(e.get("document_template", "{text}")),
        ),
        dreaming=DreamingConfig(
            similarity_threshold=float(dr["similarity_threshold"]),
            min_cluster_size=int(dr["min_cluster_size"]),
            max_clusters=int(dr["max_clusters"]),
            near_dup_threshold=float(dr["near_dup_threshold"]),
            scheduled=bool(dr.get("scheduled", True)),
        ),
        dream_rnd=DreamRnDConfig(
            enabled=bool(rnd["enabled"]),
            sigma=float(rnd["sigma"]),
            min_degree=int(rnd["min_degree"]),
            bridge_clustering_max=float(rnd["bridge_clustering_max"]),
            centrality_top_k=int(rnd["centrality_top_k"]),
            agreement_jaccard=float(rnd["agreement_jaccard"]),
            bridge_top_k=int(rnd["bridge_top_k"]),
            hole_min_persistence=float(rnd["hole_min_persistence"]),
            thread_min_persistence=float(rnd["thread_min_persistence"]),
            sbm_k_max=int(rnd["sbm_k_max"]),
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
            handoff_dir=_resolve(itf["handoff_dir"], root),
            default_adapter=str(itf["default_adapter"]),
        ),
        airlock=AirlockConfig(
            handoff_dir=_resolve(al["handoff_dir"], root),
            s3_bucket=str(al["s3_bucket"]),
            s3_region=str(al["s3_region"]),
            aws_profile=secret(al["aws_profile"]),
            requests_prefix=str(al["requests_prefix"]),
            results_prefix=str(al["results_prefix"]),
            poll_interval_s=int(al["poll_interval_s"]),
            poll_timeout_s=int(al["poll_timeout_s"]),
        ),
        integrate=IntegrateConfig(
            enabled=bool(integ.get("enabled", True)),
            max_per_pass=int(integ.get("max_per_pass", 50)),
        ),
        ambassador=AmbassadorConfig(
            retrieval_k=int(amb.get("retrieval_k", 5)),
            history_max_turns=int(amb.get("history_max_turns", 6)),
            interruption_sensitivity=str(amb.get("interruption_sensitivity", "earned_only")),
        ),
        attestation=AttestationConfig(
            enabled=bool(at.get("enabled", False)),
            signing_key_secret=secret(at.get("signing_key_secret", "attestation-signing-key")),
            owner_key_secret=secret(at.get("owner_key_secret", "attestation-owner-key")),
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
            password_secret=secret(bak.get("password_secret", "restic-password")),
            aws_access_key_id_secret=secret(
                bak.get("aws_access_key_id_secret", "backup-aws-access-key-id")
            ),
            aws_secret_access_key_secret=secret(
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
            ledger_db=_resolve(sm.get("ledger_db", "data/selfmod_ledger.sqlite"), root),
        ),
        effectors=EffectorsConfig(
            enabled=bool(eff.get("enabled", False)),
            handoff_dir=_resolve(eff.get("handoff_dir", "data/handoff/sensing"), root),
            timeout_s=float(eff.get("timeout_s", 20.0)),
            max_response_kb=int(eff.get("max_response_kb", 512)),
            upstreams=tuple(
                sorted((str(k), str(v)) for k, v in eff.get("upstreams", {}).items())
            ),
            ledger_db=_resolve(eff.get("ledger_db", "data/effectors/effects.sqlite"), root),
            drafts_dir=_resolve(eff.get("drafts_dir", "data/effectors/drafts"), root),
            jit_credential_ttl=str(eff.get("jit_credential_ttl", "60s")),
        ),
        runtime=RuntimeConfig(
            embedding_backend=str(rt.get("embedding_backend", "ollama")),
            chat_backend={str(k): str(v) for k, v in rt.get("chat_backend", {}).items()},
            server_binary=str(rt.get("server_binary", "")),
            pinned_build=str(rt.get("pinned_build", "")),
            embed_ctx=int(rt.get("embed_ctx", 8192)),
            grace_s=float(rt.get("grace_s", 5.0)),
            ports={str(k): int(v) for k, v in rt.get("ports", {}).items()},
            api_key_env=str(rt.get("api_key_env", "")),
        ),
        scheduler=SchedulerConfig(
            worker_mode=str(sch.get("worker_mode", "inproc")),
            batch_deadline_s=float(sch.get("batch_deadline_s", 0.0)),
            job_budgets={str(k): float(v) for k, v in sch.get("job_budgets", {}).items()},
            escalation_grace_s=float(sch.get("escalation_grace_s", 30.0)),
            lease_ttl_s=float(sch.get("lease_ttl_s", 0.0)),
        ),
        query=QueryConfig(hypotheticals=bool(qry.get("hypotheticals", True))),
        instance=instance,
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


def get_secret(name: str) -> str | None:
    """Fetch a secret from the ENVIRONMENT (Keychain-backed in the owner's setup) — the
    owner-operated / bootstrap path, unchanged from Phase 0.

    bp-067: ENV path ONLY, by design. The Vault-token path (`Supervisor.mint_token`,
    vault-runtime-auth.md §2) reaches `config.secrets_backend` — a network-capable module (`hvac`),
    which `import_lint` bans from `core/` (Invariant 1). So this — now inside `core.config` — is
    env-only, and `core.config` NEVER names the network Vault path: no import can leak in. The
    token-capable `get_secret(name, token=None)` lives in the OUTSIDE `config.loader` facade (the
    machinery zone, which may reach `secrets_backend`); its callers import it from `config.loader`.

    Secrets are NEVER stored in config files or committed, and never passed to a model
    (Invariant 10).
    """
    return os.environ.get(name)
