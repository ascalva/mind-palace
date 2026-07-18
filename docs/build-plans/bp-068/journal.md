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
