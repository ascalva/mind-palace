---
type: finding
id: finding-0109
status: open
created: 2026-07-18
updated: 2026-07-18
links:
  - ops/chat_sensor.py                             # sync() freezes a session by id (Q4) → open sessions lost
  - docs/design-notes/chat-sensor.md               # RATIFIED — CS-4/Q4 "freeze once, mid-append out of v1"
  - docs/build-plans/bp-068/journal.md             # where the freeze-once caveat was surfaced + owner reacted
re_entry: owner-DECIDED (2026-07-18) — growth-aware append + a LIVE transcript watcher (real-time); build as bp-069
ftype: design
origin_plan: bp-068
route: owner
resolution: decided (owner) — reverse Q4 freeze-once → growth-aware + live watcher; warrants bp-069
---

# Chat freeze-once is lossy — a session left open (hours / overnight) drops its tail. UNACCEPTABLE.

## What
bp-063's `ChatSensor.sync()` FREEZES a session once its id is in the store (Q4:
`paths = [p for p in self._transcript_paths() if p.stem not in known]`), and the daemon can't know
which session is live (`active_session_id=None`). So an OPEN session captured mid-flight is frozen
PARTIAL — a later `sync()` skips the known id, and its subsequent turns are never ingested into layer 1.
`parse_transcript` also has NO torn-trailing-line guard (`ops/chat_sensor.py:91` bare `json.loads`), so
reading a live-appended file mid-write can crash the pass.

## Why it matters (owner, 2026-07-18, emphatic)
The owner routinely leaves a session open for HOURS without using it, and leaves sessions running
OVERNIGHT so the builder/orchestrator finishes in-flight builds before bed — exactly the longest, most
valuable sessions. Freeze-once would drop their tails: **"data loss would be very common."** The owner's
standard: chat ingestion must have the SAME completeness guarantee as code ingestion — the code sensor
fires on EVERY commit; the chat sensor must capture EVERY transcript change. "An incomplete transcript is
not acceptable — a lossy process." **"The system is a real-time system, so ingestion of transcripts must
be immediate."**

## Decision (owner) — reverses the RATIFIED dn-chat-sensor Q4
**Growth-aware append + a live transcript watcher.** Two parts:
1. **Growth-aware re-ingest (the data-model fix, mandatory):** re-parse a changed transcript and APPEND
   new turns by `(session_id, turn_index)` (`add_batch` is already idempotent) instead of skipping a
   known session. Never freeze. Raw keeps versioned snapshots (content-addressed — "git for transcripts").
   Plus torn-trailing-line tolerance so reading a live file never crashes.
2. **Live watcher (the trigger, for immediacy):** a debounced FS watcher on the transcripts dir (mirror/
   generalize `VaultWatcher`) that re-ingests the instant a transcript changes — minimal debounce, real-
   time. The 6h housekeeping tick stays as a backstop.

This SUPERSEDES the Q4 "freeze once / mid-append out of v1" decision in the ratified note — the owner is
the design authority; the note's Q4 should be amended to record it (owner-gated).

## Architecture the decision sits in — one agent, MULTI-RATE PROJECTION (owner, 2026-07-18)
The chat sensor is the single model-free agent that always accepts the latest real-time transcripts and
performs the projections of the different layers AT DIFFERENT RATES:
- **Real-time rate** — raw snapshot (layer 0) + the dialogue-strata projection (cleaned utterances). This
  is bp-069.
- **Lower rates** — layer 1 (summaries) + layer 2 (references touched), each projected on its own cadence
  from the already-scrubbed dialogue strata (Track 2 / CS-5; hung off a periodic tick like dream/curate).

**Safety ordering (bright line #10):** credential removal is the agent's DETERMINISTIC gate at the
real-time rate (the existing `ChatSecretGuard`, model-free) — NOT a model. Every downstream (lower-rate)
projection reads only scrubbed text, so a model never touches a secret. An "agent that removes
credentials" must never mean a MODEL reading un-scrubbed text.

## Routing
`design` → owner (DECIDED). Warrants **bp-069** (owner-directed). Not a bright-line change: still
OBSERVED-only, local-file, model-free, secret-guarded — only the freshness/completeness semantics change.
