---
type: build-plan
id: bp-068
alias: chat-sensor-wiring
status: complete
design_ref:
  - docs/design-notes/chat-sensor.md               # RATIFIED dn-chat-sensor — CS-1/2/3 (the sensor this RUNS)
contract: builder
write_scope:
  - scheduler/chat_sync.py
  - ops/lifecycle/launcher.py
  - scripts/palace.py
  - core/config/**
  - config/defaults.toml
  - tests/unit/test_chat_sync.py
  - tests/integration/test_chat_sensor_wiring.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 100k
  actual:
    model: opus
    tokens: 78.7k out / 16.6k in (+12.2m cache read)   # est 100k; output under, but grounding-heavy
    ratio: 1.0             # on-estimate: well-pinned + clean, but §6 mis-grounded twice offset the win
    dollars: 9.83          # session-28 total (/usage); single build; well within the weekly
    session_delta: 7%      # of the session budget
    week_delta: <1%        # all-models weekly (5% cumulative)
    result: both items complete; verified LIVE (110 sessions/6365 utterances ingested); ratchet held at 19
depends_on: [bp-063]
parallelizable_with: []
supersedes: null
superseded_by: null
warrant: null
created: 2026-07-18
updated: 2026-07-18   # session-28: COMPLETE — chat ingests (110 sessions live); ratchet held 19 (OPUS)
re_entry: null
---

# Build Plan — wire the chat sensor to RUN (ingest the Claude Code transcripts into the observed stratum)

## 0. Mode & provenance
Owner-directed (2026-07-18, the session-27 game plan: the FIRST forward action). bp-063 built the chat
sensor (`ops/chat_sensor.py` — φ_chat, verbatim-first, fail-closed) + the `chatlog` store, and bp-064
wired its clock — but **nothing invokes the sensor**: it has no scheduler registration and no entrypoint,
so `data/chatlog.sqlite` does not exist and no chat has ever been ingested. This plan wires the sensor to
run (a scheduled job + an on-demand command), the same species as the vault watcher. Separate
authority-to-act (owner instruction) from the readiness blessing (owner-only `proposed → ready`).

## 1. Objective
The chat sensor runs — on daemon startup (a catch-up backfill of every closed session) and periodically
(new sessions close over time) — ingesting the local Claude Code transcripts into the OBSERVED chatlog
store via `ChatSensor.sync()`. Plus an on-demand `palace ingest-chat` command so the owner can trigger
the first ingest immediately. No new sensor logic — bp-063's `ChatSensor` is invoked, not rewritten.

## 2. Context manifest (read in order)
1. `docs/design-notes/chat-sensor.md` — the ratified sensor design (CS-1/2/3); confirms the sensor is a
   scheduler/ops job reading local files (no edge seam — informs the job KIND / certificate lane).
2. `ops/chat_sensor.py` — the driver: `class ChatSensor(transcripts_dir, rawstore, store: ChatlogStore,
   guard: ChatSecretGuard, active_session_id=None)`, method **`sync() -> ChatSyncReport`** (idempotent —
   a session already in the store is frozen/skipped; excludes `active_session_id`). This is what a
   handler calls. `ChatSecretGuard` (fail-closed secret scan) + `ChatSyncReport` (counts).
3. `scheduler/vault_sync.py` — the PATTERN TO MIRROR: `VAULT_SYNC_KIND`, `vault_sync_handler(sync)`,
   `enqueue_vault_sync(queue, router)`, `build_vault_watcher(...)`. Copy this shape for chat.
4. `ops/lifecycle/launcher.py:160-200` — the wiring site: `cron_handlers`, the `VAULT_SYNC_KIND` /
   `vault_sync_handler` / `enqueue_vault_sync` imports, the handler-map + enqueue-at-startup wiring. The
   chat job registers here beside vault_sync.
5. `core/stores/chatlog.py` (bp-063) — `open_chatlog_store` (the store path `data_dir/chatlog.sqlite`);
   `core/stores/rawstore.py` — the immutable raw archive the sensor retains to first (CS-1).
6. `scripts/palace.py` — the CLI dispatch (`main()`), to add an `ingest-chat` verb.
7. `config/defaults.toml` + `core/config/loader.py` (`PathsConfig`) — where the transcripts dir path is
   sourced (§3 Q1).

## 3. Investigation & grounding
- **Q1 — where do the transcripts live / how does the sensor find them?** The Claude Code session
  transcripts are `*.jsonl` under `~/.claude/projects/<project-slug>/` (this repo's slug is
  `-Users-ascalva-mind-palace`). `ChatSensor.transcripts_dir` must point there. RESOLVE: add a
  `chat_transcripts_dir` to `PathsConfig` (default `~/.claude/projects/<slug>`), so it is config-sourced
  (not hard-coded) and overridable in `local.toml`. `build_chat_sensor(cfg)` wires transcripts_dir +
  `open_rawstore(cfg)` + `open_chatlog_store(cfg)` + `ChatSecretGuard()`.
- **Q2 — active_session_id in the daemon?** The exclusion (Q4 of bp-063) is for a sensor running INSIDE
  a live CLI session (its own transcript is mid-append). The DAEMON is not a CLI session, so
  `active_session_id = None` → it ingests every closed session. (An owner running `palace ingest-chat`
  from a live CLI session COULD pass their session id to exclude it; default None is safe — a re-ingest
  of a grown open session is out of v1, and the identity key makes it idempotent anyway.)
- **Q3 — job KIND + cadence + certificate lane.** Mirror `vault_sync`: a `CHAT_SYNC_KIND` trough job,
  enqueued at startup (catch-up) and on the housekeeping cadence. The sensor reads LOCAL files, no edge
  seam ⇒ the same lane as vault_sync (no HANDOFF); consistent with bp-064's `observed → {TROUGH}`.
- **Q4 — does a watcher on the transcripts dir make sense?** vault_sync has `build_vault_watcher`
  (filesystem watch). For v1, a periodic enqueue (startup + housekeeping) is sufficient and simpler
  (sessions close on the owner's cadence, not sub-second). A transcripts-dir watcher is a possible
  later refinement — NOT in v1 (§9). Grounded resolution, cross-referenced.
- **Q5 — reset/idempotency.** `chatlog.sqlite` is already a `reset_targets()` wipe target (bp-063,
  registered `38af735`); `sync()` is idempotent (identity key). Re-runs are no-ops. No change needed.

## 4. Reconciliation
- `ops/lifecycle/launcher.py` — EXTENSION (a new job registered beside the existing sensors); no
  reshape of the supervisor loop. An in-file comment cites CS-1/dn-chat-sensor + this plan.
- `core/config/loader.py` / `config/defaults.toml` — ADDITIVE (`chat_transcripts_dir` path); `core.config`
  stays self-contained (the ratchet must not tick up — no new first-party import).
- `scripts/palace.py` — ADDITIVE verb (`ingest-chat`), beside the existing dispatch.
- No change to `ops/chat_sensor.py` or `core/stores/chatlog.py` (bp-063's, invoked not modified).

## 5. Write scope
`scheduler/chat_sync.py` (NEW — the KIND/handler/enqueue/build, mirroring vault_sync),
`ops/lifecycle/launcher.py` (register + enqueue the job), `scripts/palace.py` (the `ingest-chat` verb),
`core/config/**` + `config/defaults.toml` (the `chat_transcripts_dir` path), and the two new tests.
**OUT:** `ops/chat_sensor.py` + `core/stores/chatlog.py` (bp-063's — imported, not modified); the CS-5
correlator + CS-6 lag instrument (owner-gated, separate); a filesystem watcher on the transcripts dir
(v1 uses periodic enqueue, §9); the foundation denylist.

## 6. Interfaces pinned inline
```python
# scheduler/chat_sync.py  (mirror scheduler/vault_sync.py)
CHAT_SYNC_KIND = "chat_sync"
def chat_sync_handler(sensor: ChatSensor) -> Handler:   # calls sensor.sync(); logs the ChatSyncReport
    ...
def enqueue_chat_sync(queue: JobQueue, router: Router) -> Job: ...   # background/trough priority
def build_chat_sensor(cfg: Config) -> ChatSensor:
    return ChatSensor(transcripts_dir=cfg.paths.chat_transcripts_dir,
                      rawstore=open_rawstore(cfg), store=open_chatlog_store(cfg),
                      guard=ChatSecretGuard(), active_session_id=None)

# ops/chat_sensor.py (CONSUMED, verbatim — bp-063):
class ChatSensor:  # transcripts_dir, rawstore, store, guard, active_session_id=None
    def sync(self) -> ChatSyncReport: ...   # idempotent; excludes active_session_id; skips frozen sessions

# core/config/loader.py PathsConfig — ADD:
chat_transcripts_dir: Path    # ~/.claude/projects/<slug>; config-sourced, local.toml-overridable

# scripts/palace.py main() — ADD verb:
#   ingest-chat   → build_chat_sensor(cfg).sync(); print the report   (on-demand first ingest)
```

## 7. Items
### Item 1 — `scheduler/chat_sync.py` + the config path  (blast: new module + additive config)
- **Objective:** the KIND/handler/enqueue/build mirroring vault_sync; `chat_transcripts_dir` in config.
- **Acceptance test:** `uv run pytest tests/unit/test_chat_sync.py -q` green — `chat_sync_handler` over a
  seeded transcripts dir (a temp `*.jsonl`) drives `ChatSensor.sync()` and lands rows in an in-memory
  chatlog store; `build_chat_sensor(cfg)` wires the config path. `get_config().paths.chat_transcripts_dir`
  resolves. ruff + mypy clean; **the self-containment ratchet stays 19** (core.config gains a path, no
  new first-party import).
- **Falsifier:** the handler double-ingests (not idempotent); a secret-bearing transcript is stored
  (the guard must fail-closed the whole session); the config addition ticks the ratchet up.
- **Invariant(s):** OBSERVED-only landing (bp-063's structural firewall, unchanged); idempotent sync.
  **Touches stored data?** Yes — writes the chatlog + rawstore; tests use in-memory/temp stores.  **Parallelizable?** No.

### Item 2 — wire into the launcher + the `ingest-chat` verb  (blast: daemon wiring)
- **Objective:** register `CHAT_SYNC_KIND`/handler in the supervisor's handler map + enqueue at startup
  (catch-up) and on the housekeeping cadence; add the `palace ingest-chat` on-demand command.
- **Acceptance test:** `uv run pytest tests/integration/test_chat_sensor_wiring.py -q` green — a daemon
  built with a seeded transcripts dir enqueues + runs a chat_sync job and the chatlog store gains rows;
  `palace ingest-chat` (invoked in-process against temp stores) returns a `ChatSyncReport` with the
  ingested count. The full deterministic suite is green-except-the-intentional-ratchet.
- **Falsifier:** the job never enqueues (sensor still never runs); the daemon errors on startup wiring;
  `ingest-chat` writes outside the chatlog/rawstore.
- **Invariant(s):** additive-only launcher extension (no supervisor-loop reshape); local-file job (no
  edge seam). **Touches stored data?** Yes (the live chatlog on a real run).  **Parallelizable?** No (after item 1).

## 8. Math carried explicitly
N/A — no mathematical object. A scheduler-job wiring + a config path + a CLI verb.

## 9. Non-goals
NO change to the sensor's extraction/guard logic (bp-063's). NO CS-5 correlator / CS-6 lag instrument
(owner-gated, separate). NO filesystem watcher on the transcripts dir (v1 = periodic enqueue; a watcher
is a later refinement). NO open-session/mid-append ingest (v1 freezes a session once ingested — bp-063
Q4). NO change to the `observed → {TROUGH}` certificate (bp-064). NO ratchet regression (core.config
stays self-contained).

## 10. Stop-and-raise conditions
- The transcripts dir path is not cleanly config-sourceable (e.g. the slug is not derivable) → STOP,
  file a `codebase` finding rather than hard-code a machine-specific path.
- Wiring the chat job reshapes the supervisor loop or another sensor's registration (not purely
  additive) → STOP: that is a reshape, file a `spec-fidelity` finding.
- `build_chat_sensor`/the config addition would require a first-party import INTO `core.config` (ticking
  the ratchet up) → STOP: keep the path a plain `Path` field, no cross-package reach.
- Any blessing (`proposed→ready`): never.

## 11. Parked decisions
| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| transcripts-dir watcher | NO (v1 = periodic enqueue at startup + housekeeping) | a filesystem watcher like vault_sync (sub-second latency the chat lane doesn't need — sessions close on human cadence) | chat latency becomes a felt cost |
| active_session_id in the daemon | None (ingest all closed sessions) | derive + exclude a "current" session (the daemon has none; the identity key makes re-ingest idempotent anyway) | `palace ingest-chat` run from inside a live CLI session wants to exclude its own transcript |
| the job cadence | startup catch-up + housekeeping tick | a dedicated fast interval (over-frequent for a human-paced source) | chat freshness needs tightening |

## 12. Dependency & ordering summary
`depends_on: bp-063` (the sensor + store) — bp-064 (the clock) already complete, so once chat is
ingested the CS-4 chains populate automatically. Items serial: 1 (the module + config) → 2 (the launcher
wiring + CLI verb — needs the module). Blast radius: reversible writes (the sensor retains-raw-first then
lands OBSERVED rows; idempotent). **Downstream:** ingested chat is the observed-stratum data the
connectivity strata-access track (the game plan's Track 2) + the CS-5 correlator will read; this is the
game plan's FIRST step, feeding the observed strata their chat data.
