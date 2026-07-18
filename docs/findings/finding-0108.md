---
type: finding
id: finding-0108
status: open
created: 2026-07-18
updated: 2026-07-18
links:
  - ops/chat_sensor.py                             # build_chat_sensor + _default_transcripts_dir ALREADY exist (bp-063), unused
  - scheduler/chat_sync.py                         # bp-068: KIND/handler/enqueue only (NO duplicate builder)
  - scheduler/router.py                            # _PINNED_KINDS omits "chat_sync" (out of bp-068 scope)
  - docs/build-plans/bp-068/plan.md                # §5/§6 mis-grounded: builder location + the config field
re_entry: owner/orchestrator — decide whether the transcripts dir needs TOML-overridability (a small follow-up touching ops/chat_sensor.py) and whether chat_sync should be registered in router._PINNED_KINDS
ftype: spec-fidelity
origin_plan: bp-068
route: builder
resolution: resolved-in-plan (bp-068) — reused the existing builder + enqueued on the pinned tier in-scope; config field deferred
---

# bp-068 grounding gaps: `build_chat_sensor` already existed, and `chat_sync` pinning needs a router edge out of scope

## What (two grounding gaps caught at build start — [[ground-before-building]])

**G1 — the builder already exists.** bp-068 §6 pins a NEW `build_chat_sensor(cfg)` into
`scheduler/chat_sync.py`, reading a NEW `cfg.paths.chat_transcripts_dir` via a nonexistent
`open_rawstore(cfg)`. But `ops/chat_sensor.py` (bp-063) ALREADY defines a working
`build_chat_sensor(config=None, *, active_session_id=None)` — it resolves the transcripts dir via
`_default_transcripts_dir()` (REPO_ROOT cwd-mangling) and uses `RawStore(cfg.paths.raw_store)` +
`open_chatlog_store(cfg)`. It has **zero callers** (built in anticipation, never wired). Creating a
second builder would duplicate it (owner DRY strictness, [[owner-dry-strictness]]) and leave the
bp-063 one dead. The true mirror of vault_sync is that the launcher builds the DRIVER from where it
lives (`vault_sync_handler(build_vault_sync(cfg))` — `build_vault_sync` is imported from
`core.ingest.sync`, NOT from `scheduler.vault_sync`); the scheduler module carries only
KIND/handler/enqueue.

**G2 — pinning the job needs a router edge that is out of scope.** vault_sync is a model-less
maintenance job routed to the always-warm PINNED tier because it is registered in
`scheduler/router.py:_PINNED_KINDS = {"vault_sync", "ambassador"}`. chat_sync is the same species
(deterministic, model-free file scan), so it should pin too — else `router.plan("chat_sync")`
defaults to the "routine" tier and the supervisor needlessly loads the 9B worker to run a job that
touches no model. But `scheduler/router.py` is NOT in bp-068's write_scope.

## Resolution (builder, in bp-068 — both `spec-fidelity`, routing rule → builder resolves + continues)

- **G1:** reused `ops.chat_sensor.build_chat_sensor` (no duplicate). `scheduler/chat_sync.py` provides
  `CHAT_SYNC_KIND` + `chat_sync_handler(sensor)` + `enqueue_chat_sync(queue, router)` only; the
  launcher wires `chat_sync_handler(build_chat_sensor(cfg))` exactly as it wires vault_sync.
  **Consequence — the `chat_transcripts_dir` config field is DEFERRED.** Wiring it cleanly would
  require pointing the existing `build_chat_sensor` at `cfg.paths.chat_transcripts_dir` — a one-line
  edit INSIDE `ops/chat_sensor.py`, which §5 explicitly excludes ("imported, not modified"). Adding
  the field without wiring it = dead config. `_default_transcripts_dir()` already resolves correctly
  for the daemon (REPO_ROOT = the canonical repo), so nothing is lost for v1. **Side effect:** the
  self-containment ratchet is untouched (core.config is never edited) — stays 19, better than the
  plan's "gains a Path field" target.
- **G2:** enqueued chat_sync DIRECTLY on the pinned tier in `enqueue_chat_sync`
  (`router.config.pinned_model.tier/num_ctx`, PRIORITY_BACKGROUND). The supervisor dispatches on the
  job's STORED `job.tier` (`scheduler/supervisor.py:71` `ensure_tier(job.tier)`), never re-planning by
  kind, so this fully achieves the pinned, always-warm routing without editing `router.py`.

## Follow-ups for the owner/orchestrator (re-entry)
1. **TOML-overridability of the transcripts dir** (esp. for worktrees, whose REPO_ROOT-mangled slug
   differs from the canonical repo's — `_default_transcripts_dir`'s own docstring flags this): a small
   follow-up plan touching `ops/chat_sensor.py` to add `chat_transcripts_dir` to `PathsConfig` +
   `defaults.toml` and point the existing builder at it. Keep it a plain `Path` field (no first-party
   import into core.config — ratchet stays put).
2. **Register `chat_sync` in `router._PINNED_KINDS`** so any future `router.plan("chat_sync")` caller
   also pins, not just the in-scope direct enqueue. One-line router edit.

## Routing
`spec-fidelity` → builder (resolved in bp-068). Neither gap is a blocker; the core objective (the chat
sensor RUNS and ingests) is delivered. The two follow-ups are owner/orchestrator calls, parked here.
