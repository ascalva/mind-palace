# ambassador-agent-loop

## 2026-10-29

```capsule
topic: ambassador-agent-loop
date: 2026-10-29

seed (owner, verbatim, four messages): |
  "another way to also make qwen aware of ouroboros: like an agent, giving a pre prompt with a small
  brief on the ouroboros, what context it can provide, where and how to look to better understand
  what's available in terms of tools or type of data, and maybe even suggesting when it would be
  important to make updates (less common since the conversations will be auto ingested), but i do
  want to the qwen model, like a hermes or open claw, to have some loose loop that can allow the
  agent to check on tasks, remember to check on tasks, learn, know when and how to delegate to even
  larger agents or get quick decisions from jev (arent there also local system 1 models like tev?)"
  "the loop and bookkeeping might be where we can get heavy inspo on those open source projects, or
  even make use of those projects, but selective of course"
  "it would be nice if i could even ask the qwen agent how the ingestion is going, or running
  processes with regards to the mind palace ecosystem or any other long running task, or even to
  look at my calendar or emails (reading)"

built already (2026-10-29):
  - The brief: agents/ambassador/brief.md — what Ouroboros holds, when to look unasked, how to
    query, when to write. Open WebUI's model preset carries it; eval/ambassador_e2e.py measures it.
  - The Open WebUI bridge (12 tools, sealed responder) and curated literature in reach.

extends (ratified, do not re-decide):
  - dn-agentic-loop: sense → act → confirm; its gap catalog (G-A..G-G) still stands.
  - dn-ambassador-as-reasoning-agent §3: speak when an update is expected, when it is earned, or
    to set effort expectations — never noise. §2: cadence is the agent's judgment, within bounds.
  - dn-autopilot-and-delegated-blessing, dn-supervision-and-liveness, exhaust-lane.
  - Code: agents/ambassador (intents; TASK → gate → queue), policy.InterruptionPolicy, scheduler/
    (cron, queue, supervisor, presence, power), ops/effect_gate (approvals), ops/selfmod (gated).

borrow, selectively (OpenClaw; Hermes Agent, MIT — both read 2026-10-29, secondary sources):
  - TAKE heartbeat (OpenClaw): a periodic turn over a checklist, silent unless something needs
    attention. Here: a `palace tick` LaunchAgent whose checks are deterministic first (due tasks,
    new chats to sync, failed or finished runs) and which wakes Qwen only when one fires — the
    "earned interruptions" bar, and models stay asleep otherwise.
  - TAKE cron-as-isolated-runs (both): a scheduled task runs in a fresh context; continuity comes
    from the ledger and the palace, not a long chat. Cron runs cannot create cron jobs (Hermes).
  - TAKE delegation shape (both): a sub-agent gets a brief, a cheaper or larger model, a timeout,
    restricted tools, no recursive spawning, and returns a condensed result.
  - TAKE skills that grow (Hermes): after a repeated task the agent DRAFTS a SKILL.md; drafts wait
    in a staging folder until the owner approves (the selfmod/approval pattern), never auto-load.
  - TAKE memory nudges, adapted (Hermes): after a long conversation or a correction, the agent may
    write a short "lesson" (interpreted provenance) — the palace stays the one memory.
  - LEAVE Markdown memory files (MEMORY.md/USER.md/SOUL.md): a second memory without provenance.
  - LATER messaging gateways (Hermes/OpenClaw): see the channel question.
  - NOT NOW running Hermes or OpenClaw as the host: a parallel memory and a wider surface. Revisit
    one as a gateway only, pointed at the palace over MCP with its own memory off.

new senses asked for:
  - Ecosystem status ("how is the ingestion going?"): a read-only `status` tool over the run ledger,
    the job queue, model residency (lmtune, the embedder), the bridge, LaunchAgents, and a runs
    registry long jobs report into — today the curated ingest leaves no run record.
  - Calendar and mail, read-only: local readers. Calendar through EventKit (a small Swift CLI; macOS
    asks the owner once). Mail through Mail.app or IMAP with a Keychain app password. Live queries
    by default; ingesting them into a stratum (with retention) only if the owner wants.
  - Quick decisions: Jev is hosted-only. CORRECTED the same day (next capsule): local Jev-style
    decision models do exist (tev1 and nimble on Ollama's /v1/systemone; Clef's open weights), so
    "no local Tev exists" was wrong. Palace content never goes to Jev (Invariant 11): typed
    decisions over private data go to a local decision model; Jev decides over public or
    owner-cleared state (reflex's pattern).

owner ruling — Jev (2026-10-29, verbatim): |
  "handing off tasks to jev should be fine whenever with my written permission, or when browsing
  for something (research or upon my request), jev could be used in the actuation/agent/action
  decision loop, taking in context, sensor data with respect to domain"
  Read as three grants: (1) any hand-off the owner approves in writing; (2) browsing and research,
  on public content, or on the owner's request; (3) the action-decision loop (actuation, agents),
  given the decision's context and its domain's sensor data. Proposed boundary, to confirm: a Jev
  request carries the minimum state the decision needs — never bulk palace content — and every
  call is logged with what was sent (reflex's audit JSONL is the pattern).

chartered dreams (owner, 2026-10-29): |
  "qwen could also kick off a dreaming scenario, where i might want to give it certain
  topics/params, then it would research and gather external temporary/persistent context, and use
  that temporary context in relation to persistent context and dream over them with both types of
  dreamers to investigate relationships"
  Maps onto ratified dn-synchronic-diachronic-dreamer: the request IS a DreamCharter (SD-2: scope
  grant, instrument grant, budget, gauge) — built in core/dreaming/charter.py, but no live entry
  constructs one (dn-agentic-loop gap G-A). Temporary context → the HYPOTHETICAL staging store
  (SD-6: append-only, no promotion path to any durable store, by construction); persistent context
  → the curated store. Synchronic dreaming is live; the diachronic dreamer is designed in full and
  parked (SD-8) — "both dreamers" needs SD-8's execution. Build: a `dream_charter` tool (OpenCode
  and the owner's confirmation only — a dream holds the 27B for minutes), research staged through
  the airlock, the charter dispatched as a queued job, the result narrated by the Ambassador.

phases (proposal):
  1. Heartbeat and bookkeeping: `palace tick` (dialogue auto-sync, which the brief already
     promises; due checks), a task and reminder ledger with tools (task_add, task_list,
     task_update, remind), the `status` tool, and the brief as Open WebUI's model preset.
  2. Senses and delegation: calendar and mail readers; delegation through an egress gate (local
     OpenCode agents; Claude Code headless for larger work; Jev for non-private decisions); the
     local quick-decision model.
  3. Learning and a channel: lessons, approved skill drafts, a push channel to janus; chartered
     dreams (wiring G-A; SD-8's diachronic execution).

open questions (owner), with defaults:
  - Channel: how does Qwen reach you away from the Mac? ntfy on the tailnet, iMessage to janus, a
    daily digest note, or none. Default: none until phase 3; the tick's findings wait in the
    ledger and Qwen mentions them at the next conversation.
  - Egress: what may leave the Mac in a delegation brief? Default: nothing from the palace without
    a per-task approval, logged.
  - Mail: which account(s); live read-only queries only, or ingested (and kept how long)?
    Default: live and read-only, nothing stored.
  - Tick cadence and quiet hours. Default: every 30 minutes, quiet 23:00–07:00.
  - Skill drafts: approval required (default) or automatic.
```

## 2026-10-29 (later): phase 1 built, the heartbeat

```capsule
topic: ambassador-agent-loop / heartbeat
date: 2026-10-29

owner (verbatim, while it was being built): |
  "let's build it smart: the heartbeat should need to trigger a model load, it can be pure code
  making a decision, or even a jev call, does the current state require a model/agent wake up? is
  battery in good state? are there ongoing/background tasks? are reminders overdue for a
  notification? etc" (read as: should NOT need to trigger a model load)
  "make sure it is extremely efficient, reliable, and can easily be disabled if not needed
  (temporarily of course), test thoroughly for bugs and security, utilizing state of the art
  patterns where necessary and call them out by name when in use for easier debugging/research in
  the future, also since ouroboros ingests its own code"

built (ops/heartbeat.py; `mind-palace tick`; LaunchAgent com.mind-palace.tick, every 15 minutes):
  rule: the tick never loads a model to decide whether to load one.
  reads (plain code, no model): power, battery and Low Power Mode (pmset); a thermal warning; the
    chat model's state (llama-server /props, then /slots only when it is awake, so the probe never
    wakes a sleeping model); the embedder's state; palace jobs (the ledger and the process table);
    due items; each dialogue source's newest change against its high-water mark; free disk; the
    circuit breaker (read off the ledger).
  decision table (`decide`, a pure function):
    notify         an item came due and was not pushed yet          → wakes nothing
    sync-dialogue  a source changed since its last good sync, the   → wakes the embedder, for
                   breaker is closed, and nothing blocks: AC or a      new turns only
                   battery ≥ 40%, no Low Power Mode, no thermal
                   warning (unreadable counts as one), the embedder
                   up, the chat model not mid-answer, no palace job
                   running, ≥ 10 GB free
    wake-agent     never in phase 1: no scheduled work needs        → (the chat model)
                   reasoning; phase 3 adds rows (scheduled agent
                   runs, chartered dreams)
  kill switch: `mind-palace tick pause 2h [reason]` (30m, 1d, or until a local time; 7 days at
    most), `tick resume`, `tick status`; a row off for good: config/stack.toml [tick] actions;
    everything off: `mind-palace stack down`.
  notifications: macOS Notification Center on ouroboros, once per due time (a moved reminder is
    pushed again); the text goes to a fixed AppleScript as arguments, never as script. janus (the
    phone) remains phase 3's channel question.
  the date: the bridge adds "Today is <weekday>, <date>." to the instructions. Day resolution keeps
    llama-server's prompt cache warm. The e2e had shown Qwen stamping a capture "2026-07-14".
  measured: a beat costs 0.37 s wall, 0.24 s CPU, 37 MB peak; a paused beat reads nothing.

patterns in use, by name (the module docstring lists where each lives): the sense-decide-act
  control loop; functional core, imperative shell; ports and adapters; decision table, with
  decision-table testing (86,400 rows) and property-based tests (Hypothesis; the safety invariant
  is monotonicity: a blocker only takes permission away); fail-safe defaults; high-water mark;
  scatter-gather; circuit breaker with exponential backoff (Nygard, Release It!); reconciliation
  loop; at-least-once delivery; kill switch with expiry (a time-boxed feature flag); single-instance
  lock (flock); atomic write; watchdog (stale beats; notices older than 3 hours dropped); lazy
  loading; cache-stable prompt prefix.

decided while building (open defaults above): cadence 15 minutes, not 30 (a beat costs 0.3 s and
  wakes nothing); no quiet hours in code, since macOS Focus already holds notifications at night.

decision models (facts checked 2026-10-29; vendor numbers, not verified here):
  - Ollama ≥ 0.35 serves Jev-style decision models on /v1/systemone (Ollama blog, 2026-09-29):
    tev1 (Together AI; Qwen3.5 4B and 0.8B; 4.4 GB and ~0.8 GB; the fine-tuned weights' license is
    not final) and nimble (Bespoke Labs; 9B; Apache-2.0). Ollama 0.40.6 runs on ouroboros, with no
    model pulled yet.
  - Clef (Cloudflare, 2026-10-01): Clef (on Qwen3.8-27B) and Clef-flash (on Qwen3.5-9B),
    Apache-2.0, weights on Hugging Face, Jev-API-compatible; a routing head plus adapters, so not a
    plain GGUF.
  - Mean accuracy over 13 public datasets (Ollama's runs): Jev 1.13 76.0%, nimble 75.7%, tev1 4B
    73.3%, tev1 0.8B 63.5%.
owner direction (verbatim): |
  "we can use the local decision models potentially for the heartbeat decisions, and jev for more
  complex decisions and browsing/research"
  "or even local models could be used (if efficient and fast) for quick branch/edge predictions?
  not sure if that's possible due to it not being trained on the local data"
  tiering: exact inputs → code (free and certain); a judgment over language → a local decision
  model (private data stays on the Mac); harder judgments, browsing and research → Jev, under the
  ruling above. Every heartbeat row today reads exact inputs, so code decides them. First
  candidates for a local model: a commitment in new turns that the Ambassador did not record
  ("remind me…" with no remind call); a failed job's log, transient or needing the owner; mail and
  calendar (phase 2).
  edges and branches: a decision model judges the state it is shown (both texts in the request),
  so it needs no training on palace data; the palace supplies the context per question. Two fits:
  (1) the relate lane (supports / contradicts / neither) at a reported 40–200 ms a pair, against
  the 27B's seconds, so hundreds of pairs a pass instead of 24; (2) pruning in lazy evaluation,
  where REACH and DIFFUSE ask "does this neighbor bear on the question?" before expanding (the
  rerank pattern). Gate: a labeled sample at the code sensor's bar (bp-011: 100% precision on 30)
  before any proposed edge lands; every such edge records its model and probability.
```
