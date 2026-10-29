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
  - Quick decisions: Jev is hosted-only — no open weights, and no local "Tev" exists as of
    2026-10-29. Palace content never goes to it (Invariant 11). For typed decisions over private
    data, a small local model with grammar-constrained output (the router slot); Jev for decisions
    over public or owner-cleared state (reflex's pattern).

phases (proposal):
  1. Heartbeat and bookkeeping: `palace tick` (dialogue auto-sync, which the brief already
     promises; due checks), a task and reminder ledger with tools (task_add, task_list,
     task_update, remind), the `status` tool, and the brief as Open WebUI's model preset.
  2. Senses and delegation: calendar and mail readers; delegation through an egress gate (local
     OpenCode agents; Claude Code headless for larger work; Jev for non-private decisions); the
     local quick-decision model.
  3. Learning and a channel: lessons, approved skill drafts, a push channel to janus.

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
