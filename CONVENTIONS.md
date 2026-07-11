# CONVENTIONS

Engineering and security practice for this repo. Binding unless the full `docs/BUILD-SPEC.md` says otherwise. The goal is **efficient, secure, open-source code, with thin custom logic where we want ownership** — a flexible system we expand as needs grow.

## Language & style
- **Python** for orchestration, agents, stores access, and the supervisor — the owner's strongest language and the native home of the ML/embedding ecosystem.
- Performance-critical deterministic stream math (EWMA, z-scores, changepoint) uses **Polars/NumPy**; it may later move to Rust if it becomes a bottleneck. Don't prematurely optimize.
- The job queue is **SQLite-backed Python** by default; **River (Go)** is the sanctioned alternative if more robustness is wanted (decision point).
- Type-hint everything. Keep modules small and single-purpose. Prefer pure functions for anything testable.
- **Run everything via `uv`** (house rule, 2026-07-11): `uv run scripts/palace.py start`, `uv run pytest -q`, `uv sync --extra dev` for setup. Never hand-built `./.venv/bin/...` paths — `uv.lock` is authoritative and `uv run` owns env resolution. Daemon surfaces (launchd plists, cron shells) use the absolute `/opt/homebrew/bin/uv` because launchd's PATH is minimal.

## Frameworks — what NOT to use
Do **not** pull in LangGraph, CrewAI, AutoGen, or similar agent frameworks. They are ceremony that obscures ownership and fights the resource model. **Hand-roll the ReAct/tool loop and the supervisor.** Build thin wrappers over solid primitives (Ollama HTTP, LanceDB, DuckDB, SQLite, Podman) rather than adopting large abstractions.

## Data stores & access
- **LanceDB** — thought-graph vectors (in-process, no daemon).
- **DuckDB** — telemetry/time-series (system vitals now; body-sensor adapter contract built but dormant).
- **SQLite** — job queue, scheduler state, the propose/approve/validate gate ledger, rollback metadata, persisted-agent registry.
- **Scoped access is enforced in code, not by convention.** Each agent gets a store handle limited to exactly the reads/writes its role needs. The introspection agents have no write access to telemetry; the watchdog has no write access to the vault. Build a small access layer that makes the wrong access impossible, not just discouraged.
- Ship migrations and a `schema.md`. Keep each store independently replaceable.

## Model serving & the resource ceiling
- Serve models over **HTTP via Ollama** (or `llama-server`); keep the interface abstract so a future Linux/GPU node can join as another worker.
- Honor the **two-slot model** (BUILD-SPEC §5): one pinned tiny model, one swappable worker. Never attempt to hold more, or exceed ~20–24 GB usable. The scheduler must refuse breaching work. The ~32B stretch model evicts the pinned model — account for that.
- Group same-tier jobs to minimize model-load swaps; that latency is the real cost.
- **Context budgets are deterministic.** Count tokens with the model's tokenizer and assemble each context (Constitution → role/task → retrieval → history → tool output) to fit the active model's window with reply headroom; on overflow, trim retrieval top-k, compact history, then escalate model tier — never silently drop. Track usage to telemetry.
- **Size the context window per role at load time** (`num_ctx` / KV-cache), not at the model's max — small for the router and the conversational role, large for synthesis — from tracked per-role usage. Smaller windows save RAM (KV cache scales with context length) and latency.
- **Inject persona and parameters at request time via the Ollama API — never bake `SYSTEM`/`PARAMETER` into Modelfiles.** Keep two lifecycles separate: agent lifecycle (the factory + SQLite registry, runtime config) and model lifecycle (pull/update + the two-slot loader). The router decides routing/tier/window; code assembles prompts and drives Ollama. Changing `num_ctx` reloads the model, so vary it per role at load, not per call.

## Code execution (sandbox)
Any code an agent runs is **powerless** (Invariant 4):
- Default substrate: **ephemeral rootless Podman** — `--network=none`, no vault mount, read-only base + scratch tmpfs, dropped capabilities, seccomp profile, non-root user, CPU/memory/pids limits, wall-clock timeout.
- Keep a **warm pool** of sandboxes to avoid cold start; cap concurrency to the memory ceiling. Wrap it in a thin execution-broker.
- For pure computation, prefer **wasmtime + Pyodide** (no syscalls). For hardening, the upgrade path is **gVisor/Firecracker**.
- Executed code returns **data**, never actions on the system. Any network grant is per-execution, narrowly scoped, and logged.

## Secrets
- **macOS Keychain** (the owner already uses Keychain-backed auth) or environment variables. Never commit secrets, never let a model read them, never log them. Config files hold non-secret config only.

## Cloud (AWS)
- **Terraform for everything.** No click-ops. Least-privilege IAM — the research fetcher gets web egress + the two S3 prefixes and nothing else.
- Backups via **restic → S3** (client-side encrypted + deduplicated) with SSE-KMS on the bucket. macOS is APFS — restic over data directories; don't assume btrfs.

## Trust boundaries in code
- `core/` (Zone A) must contain **no import path that can reach the network.** Treat an accidental network-capable import in core as a build-breaking defect.
- Only `edge/` (bridge, interface gateway) touches the network, containerized, vault unmounted, no inbound listeners beyond what the job needs.
- **Comment the *why*** at every boundary — the airlock's outbound-only/de-identified asymmetry, the propose/execute split, the agent-factory scope ceiling — so a later edit can't quietly erode the property.
- **Voice/telephony adapter** lives in `edge/`; TTS/STT run in `core/` and the adapter pipes raw audio only. The dial target comes from **fixed config, never from model output** — the adapter must be structurally incapable of dialing any number but the owner's registered one. Authenticate the human (passphrase/callback) before relaying privately-derived content.

## Testing & validation
- Write tests alongside code. For retrieval, use **deterministic metrics** (recall@k, set overlap, cosine distance) against the **frozen golden set**. For behavior, check conformance to `CONSTITUTION.md`. Use a model-judge only for subjective cases, always **A/B against a baseline snapshot**, never scored cold.
- The agent that made a change never grades it. Keep **two baselines**: a rolling one for acute regressions, the frozen anchors (golden set + Constitution) for slow drift.
- **Live verification is routine, not opt-in, from 2026-07-02.** The default `pytest` run (deselecting `live`/`podman`/`needs_*`) stays the fast deterministic ratchet — keep it green — but it is not the finish line for a change that touches a model tier or the sandbox. Run `pytest -m live` whenever the tier's model is pulled, and `pytest -m podman` whenever podman-machine is up, as part of verifying that work. A `skipif` gated on an actual `list_models()`/machine-status check is honest; silently relying on the deterministic stand-in when the real thing is available and running is not — say plainly when a live gate was skipped and why.
- **"Live" and "the sandbox" are two different axes — don't conflate them.** `-m podman` exercises the rootless-Podman `run_python` **tool** path: agent-*authored* code execution (network-off, no vault mount, resource-limited, Invariant 4). It is a separate concern from the Dreamer/reasoning-complex (`core/dreaming/`, `core/complex/`), which does its own computation in-process — model-free and deterministic except for the embed/synthesize calls — and never runs inside the sandbox. `-m live` exercises real Ollama tiers. Expect most dreaming/retrieval/synthesis changes to need `-m live`; expect changes to `core/sandbox` itself, or to a role's `run_python` scope, to need `-m podman`.

## Working rhythm
- Build **phase by phase** (BUILD-SPEC §18); verify against the gate; **checkpoint with the human** before advancing.
- **Ask, don't guess** on BUILD-SPEC §20 decisions; otherwise choose a sensible default and state it inline.
- Keep changes small and reversible. When unsure whether something belongs in `core/` or `edge/`, it belongs in `edge/` if it can ever touch the network.

## Commits (house style, 2026-07-11)
- **Conventional Commits, machine-first:** `type(scope): subject`. Types: `feat fix docs test refactor perf ops chore`. Scope names the tree area or artifact the change lives in (`core`, `edge`, `ops`, `hooks`, `eval`, `bp-005`, `triage`) — optional, but a scoped header is a better lookup key.
- **Subject:** imperative, ≤ 72 chars, no trailing period, and it states the *change*, not the activity ("add X", never "worked on X"). **One logical change per commit** — if the subject needs "and" twice, split the commit. Small accurate summaries are what make the ledger a lookup tool.
- **Body:** the *why*, plus whatever the diff can't say (constraint honored, alternative rejected, invariant touched).
- **The machine consumers are real, not aspirational:** semantic-release versions from `type`; the code-sensor ledger (`data/code_snapshots.sqlite`) parses `type(scope): subject` into queryable columns beside each commit's structural snapshot. A malformed header degrades lookup, not just style. Merge commits are exempt (git authors them).
- **`main` is the ingestion branch.** The code sensor ingests `main` history only; the post-commit hook exits silently on any other branch or detached HEAD. Branch work enters the record at merge — write the merge/squash message to this rule.
