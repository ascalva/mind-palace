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

## Architecture the decision sits in — one agent, MULTI-RATE PROJECTION (owner, 2026-07-18, refined)
One source (the transcript), projected at different rates — all DETERMINISTIC / model-free:
- **Layer 0 (real-time)** — the rich dialogue: raw byte-verbatim snapshot + tool-stripped prose utterances,
  appended live, lossless. The full text lives here. **bp-069.**
- **Layer 1 (delayed) — WHAT actions were performed.** An ordered, typed ACTION LOG per session
  (`owner_prompt → agent_response → commit → ratify → build_plan → …`), extracted deterministically from the
  transcript's turns + TOOL RECORDS. No prose ("for prose, read layer 0"), no model. Reads the FULL raw
  transcript (the tool records layer 0 strips). **bp-069.**
- **Layer 2 (delayed) — WHERE they happened.** Deterministic edges connecting each action to the exact
  commit / file / doc — read straight from the same tool records (the SHAs + file_paths the transcript
  records), proving causation. NOT a time-based co-occurrence join; NOT CS-5; NO strata-access/`MirrorView`
  needed. A SEPARATE deterministic connector agent. **bp-070.**

**Corrections to my first framing (recorded so the plan doesn't inherit them):** (a) layers 1/2 do NOT need
the Track-2 strata-access machinery — the agent reads its OWN transcript, never other strata; (b) layer 1 is
NOT modeled on the dreamer (no synthesis/clustering); (c) layer 2 is deterministic CAUSATION from the tool
records, not a time-join. The abstractive model summary is a LATER rate (not bp-069). **#10:** bp-069 has no
model at all; when the later model summary lands it reads only the scrubbed store — the model boundary is the
#10 line.

## Why layer 2 matters — the free proven-edge substrate (owner, 2026-07-18) — warrants bp-070
Layer 2 is a MECHANICAL/deterministic agent that automates the cross-sensor connections, producing PROVEN
edges (causal, model-free, FREE). Proven edges are exactly what the interpretive/analytic layers cannot
safely manufacture themselves, so they RIDE ON layer 2's output:
- **The dreamer** interprets over GROUND-TRUTH connections instead of guessing them. Its only cross-item
  edges today are similarity edges (`E_sim = cos ≥ σ`) — where apophenia lives (a high cosine can be
  coincidence). Layer 2 hands it edges that ACTUALLY HAPPENED (chat → commit → files → doc), so interpretation
  stands on fact. The deterministic FLOOR keeps the interpretive CEILING honest.
- **The capability-scope-algebra** exploits them as real structure.
- **Conductance + connectivity ride on them** (`docs/design-notes/connectivity-instruments.md`): the graph
  stops being similarity-only — the free edges are real conductive paths ACROSS strata. This is the answer to
  **oq-0031** (the σ-sweep saturating at 13 docs): the graph was thin because cosine was its ONLY connective
  signal; layer 2 injects a second class — proven causal edges — so connectivity has real structure to measure.

**Division of labor:** layers 0/1 project the transcript deterministically → **layer 2 (bp-070)** unifies them
into free proven edges (a `reference_edges`-shaped store, chat as causal origin) → the dreamer / scope algebra
/ conductance / connectivity all consume that ground truth. bp-070 must ref the ratified
`connectivity-instruments.md` + `cross-strata-dreamer.md` + `capability-scope-algebra.md` as its downstream
consumers.

## Routing
`design` → owner (DECIDED). Warrants **bp-069** (owner-directed). Not a bright-line change: still
OBSERVED-only, local-file, model-free, secret-guarded — only the freshness/completeness semantics change.
