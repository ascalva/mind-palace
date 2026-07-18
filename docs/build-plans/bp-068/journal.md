# Journal — bp-068 (chat-sensor wiring)

## 2026-07-18 — minted (proposed), awaiting owner bless
Owner-directed (session-27 game plan): the FIRST forward action of the settled roadmap. bp-063 built the
chat sensor + store, bp-064 wired the clock — but **nothing invokes the sensor** (no scheduler
registration, no entrypoint), so `data/chatlog.sqlite` doesn't exist and chat has never been ingested.
This plan wires `ChatSensor.sync()` to run (a `CHAT_SYNC_KIND` trough job at startup + housekeeping,
mirroring `scheduler/vault_sync.py`) plus a `palace ingest-chat` on-demand verb. Status `proposed` —
awaits the owner's `proposed → ready` blessing (owner-only, by hand).

**Grounding carried in the plan (so a fresh builder needn't re-derive):**
- Driver: `ChatSensor(transcripts_dir, rawstore, store, guard, active_session_id=None).sync() ->
  ChatSyncReport` (idempotent, skips frozen sessions, OBSERVED-only). No sensor-logic change.
- Pattern: mirror `scheduler/vault_sync.py` (`VAULT_SYNC_KIND`/handler/enqueue/build) → `chat_sync.py`;
  wire into `ops/lifecycle/launcher.py:160-200` beside vault_sync.
- Transcripts live at `~/.claude/projects/<slug>/*.jsonl` → add `chat_transcripts_dir` to `PathsConfig`
  (config-sourced, local.toml-overridable); `active_session_id=None` in the daemon (not a CLI session).
- ⚠️ core.config gains a plain `Path` field only — the self-containment ratchet must STAY 19 (no new
  first-party import).

**Next action when blessed:** item 1 (`scheduler/chat_sync.py` + the config path) → item 2 (launcher
wiring + `ingest-chat` verb). Estimate opus/100k. Feeds the observed chat stratum + the CS-4 chains, and
is the data source for the game plan's Track 2 (connectivity strata-access) + CS-5.

## 2026-07-18 (session-28, OPUS) — build started; grounding complete, plan of record set

Owner-blessed `858b20c` (proposed→ready by hand). Grounded §2 manifest in order before writing.

**Two grounding gaps caught at build start (filed finding-0108, resolved in-plan — [[ground-before-building]]):**

- **G1 — `build_chat_sensor` ALREADY exists (unused) in `ops/chat_sensor.py`.** The plan §6 pinned a
  NEW builder into `scheduler/chat_sync.py` reading a NEW `cfg.paths.chat_transcripts_dir` via a
  nonexistent `open_rawstore` — the plan wasn't grounded against the existing function (which resolves
  the dir via `_default_transcripts_dir()`, REPO_ROOT cwd-mangling, and uses `RawStore(cfg.paths
  .raw_store)` + `open_chatlog_store(cfg)`; zero callers). **Resolution: REUSE it.** The true mirror of
  vault_sync is that the LAUNCHER builds the driver from where it lives —
  `vault_sync_handler(build_vault_sync(cfg))`, `build_vault_sync` imported from `core.ingest.sync`, NOT
  from `scheduler.vault_sync`. So `scheduler/chat_sync.py` carries KIND/handler/enqueue ONLY; the
  launcher does `chat_sync_handler(build_chat_sensor(cfg))`. **Consequence:** the `chat_transcripts_dir`
  config field is DEFERRED — wiring it needs a one-line edit INSIDE `ops/chat_sensor.py` (out of scope,
  §5 "imported, not modified"); an unused field is dead config; `_default_transcripts_dir()` already
  resolves correctly for the daemon. **Bonus:** core.config is never touched → the ratchet stays 19
  (better than the plan's "gains a Path field"). [[owner-dry-strictness]] — no duplicate builder.

- **G2 — pinning chat_sync needs `router._PINNED_KINDS`, out of scope.** vault_sync pins (model-less →
  always-warm tier) via `_PINNED_KINDS` in `scheduler/router.py` (not in write_scope).
  **Resolution (in-scope):** `enqueue_chat_sync` enqueues DIRECTLY on the pinned tier
  (`router.config.pinned_model.tier/num_ctx`, PRIORITY_BACKGROUND). Verified the supervisor dispatches
  on the STORED `job.tier` (`scheduler/supervisor.py:71` `ensure_tier(job.tier)`), never re-planning by
  kind — so this fully pins the job without a router edit. Follow-up (finding-0108): register in
  `_PINNED_KINDS`.

**Grounding facts a fresh builder needs (so none of the above must be re-derived):**
- `ChatSensor.sync()` idempotent (`(session_id, turn_index)`; skips known sessions); model-free; handler
  just calls `sync()` + logs `ChatSyncReport` (`__str__` is a ready log line).
- `ChatlogStore(":memory:")` + `RawStore(tmp_path)` work for tests; `chatlog.sqlite` is ALREADY a
  `reset_targets()` wipe target (launcher.py:626) — no reset change (plan §3 Q5).
- Launcher wiring site: `build_components` (`ops/lifecycle/launcher.py:146-234`) — `handlers` dict,
  `_catchup` (startup enqueue), `_housekeeping` (tick enqueue).
- `scheduler/interface.py:33` already imports `ops.gate` at runtime (scheduler→ops sanctioned); chat_sync
  keeps `ChatSensor` under TYPE_CHECKING (sensor injected — no runtime ops import needed).

**Plan of record (items serial):**
1. `scheduler/chat_sync.py` (NEW): KIND + handler + enqueue (pinned, background) + `tests/unit/
   test_chat_sync.py`. NO config field (deferred, G1).
2. Launcher wiring (`build_components`: handler + catchup + housekeeping) + `palace ingest-chat` verb +
   `tests/integration/test_chat_sensor_wiring.py`.

Acceptance: both new tests green; suite green-EXCEPT the intentional ratchet (`test_core_self_containment`
at 19, count non-increasing); ruff + mypy clean.

## 2026-07-18 (session-28, OPUS) — BOTH items complete; verified LIVE; acceptance met

**Item 1 — `scheduler/chat_sync.py` + `tests/unit/test_chat_sync.py` (5 tests, green).** KIND + handler
+ `enqueue_chat_sync` (pins directly to `router.config.pinned_model` tier/num_ctx at BACKGROUND
priority — G2). Falsifiers covered: double-ingest is a no-op (idempotent), a secret-bearing session is
refused whole (nothing lands), the reused `ops.build_chat_sensor` is the wiring path (no duplicate). No
config field added (G1 defer) → **core.config untouched, ratchet stays 19.**

**Item 2 — launcher wiring + `palace ingest-chat` + `tests/integration/test_chat_sensor_wiring.py`
(2 tests, green).**
- `build_components`: registered `CHAT_SYNC_KIND: chat_sync_handler(build_chat_sensor(cfg))` beside
  vault_sync; `_catchup` enqueues chat at startup (backfill), `_housekeeping` enqueues it on the tick.
- `Launcher.ingest_chat()` + the `palace ingest-chat` verb (USAGE + dispatch in scripts/palace.py).
- Integration test drives a REAL `Supervisor` (warm=False, no Ollama) that drains an `enqueue_chat_sync`
  job on the pinned tier and lands OBSERVED rows; and the verb in-process (injected temp-store sensor).

**Verified LIVE (not just tests) — the objective is achieved:**
`uv run scripts/palace.py ingest-chat` →
`chat-sensor: sessions=110 utterances=6365 retained=111 refused=1 active_skipped=no`. The real parser
+ secret guard ran over the real ~/.claude transcripts: **110 sessions / 6365 utterances landed in
`data/chatlog.sqlite` (OBSERVED)**, 111 raw blobs retained, **1 session fail-closed by the secret guard**
(bright line #10 — never stored). Second run = `sessions=0 utterances=0 retained=0` (idempotent no-op;
the 1 refused session correctly re-refuses without landing — bp-063 by-design, raw retained for
post-guard-tuning recovery). Chat had NEVER ingested before this; it does now.

**Suite:** full deterministic `-m "not live and not podman and not needs_vault and not needs_restic"` →
**1 failed (the intentional ratchet, `test_core_self_containment` at 19) / 1543 passed / 4 skipped** in
49s. Ruff + mypy clean on all changed files. Acceptance = only-the-ratchet-fails AND count == 19: MET.

**Findings:** filed **finding-0108** (spec-fidelity, resolved-in-plan) — G1 (builder already existed →
reused, config field deferred) + G2 (pinning needs a router edge, done in-scope via direct enqueue). Two
owner/orchestrator follow-ups parked there: TOML-overridable transcripts dir (touches ops/chat_sensor.py)
+ register `chat_sync` in `router._PINNED_KINDS`.

**Next:** flip plan → complete, PROGRESS checkpoint, commit, seal. Then the game plan's Track 2
(connectivity strata-access) now has its observed chat data.

## 2026-07-18 (session-28, OPUS) — SEALED `2093c69`; owner cadence Q surfaced a v1 caveat to record

Sealed at commit **`2093c69`** (amended to correct cost.actual to the real /usage: $9.83, 7% session).
Plan `complete`, PROGRESS checkpointed, finding-0108 filed.

**Owner asked how ingestion works now (layers 0/1/2, cadence, "are transcripts constantly diffed?").**
Answered: 3 triggers (startup catch-up + 6h housekeeping tick + `palace ingest-chat`), NO watcher —
session-level reconcile, NOT content-diffed. Layer 0 = rawstore (once/session, immutable); layer 1a =
chatlog extraction (once/session, verbatim tool-stripped — NOT model-summarized); layer 1b (dreamer
synthesis over chat) + layer 2 (CS-5 reference correlator) are NOT wired — that's Track 2.

**Real v1 caveat surfaced (worth an owner-question / bp-069 candidate):** `sync()` FREEZES a session
once its id is in the store (bp-063 Q4), and the daemon can't know which session is live
(`active_session_id=None`), so an OPEN session captured mid-flight is frozen PARTIAL — its later turns
are never picked up (a future `sync()` skips the known id). Safe pattern = ingest after close; but a
session open during a 6h tick is captured partial. Options put to the owner: skip-until-closed (mtime
heuristic) / growth-aware re-ingest (`backfill()` + turn-append) / a real transcripts watcher. Awaiting
the owner's steer (v1-good-enough vs. a small follow-up) before filing.
