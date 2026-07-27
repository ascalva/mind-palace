# agent-interface-and-role-messaging

## 2026-07-26T00:00:00Z

```capsule
topic: agent-interface-and-role-messaging
date: 2026-07-26

seed: |
  Owner, verbatim: "building you a code agent interface, through which you can schedule, fetch
  info, evict your job, priority level, all the things you as the orchestrator need to give the
  resulting claude agent, segmented from you through code process, a code process that we track,
  the queue, you can also broadcast or one-to-one messaging queue to relevant party/role."

⚑⚑ THE UNCOMFORTABLE PART, AND IT IS THE STRONGEST ARGUMENT FOR THE IDEA: |
  **NN-3 says "The model advises; code acts. No model holds a shell, raw secrets, or direct infra
  mutation." The orchestrator holds a shell.** Right now the orchestrating MODEL runs `git commit`,
  edits files, and spawns agents directly.

  There is a defensible reading under which this is not a breach — NN-3 governs the RUNTIME system
  (the Ouroboros daemon and its resident models), while the development-plane agents building it
  are a different population. That reading has never been written down, which is itself the
  problem: an unstated exemption to a non-negotiable is indistinguishable from a violation nobody
  noticed.
  ⇒ This proposal makes the dev plane inherit the runtime plane's discipline instead of quietly
  claiming an exemption. That is a better resolution than either reading.

⚑ AGENT SPAWNS ARE CURRENTLY UNTRACKED, AND TONIGHT PROVES IT: |
  Three agents were spawned in session-54/55 (bp-110 builder, a Fable design pass, a
  sub-orchestrator). **The only durable record of any of them is prose the orchestrator chose to
  write.** No row, no ledger, no lifecycle state. If the orchestrator's context had been lost
  mid-run, the next occupant would know exactly what the brief happened to say — the same defect
  class as everything else found today (finding-0222: a note is not a control).
  A queue row survives the occupant. That is the whole point, and it is the just-ratified
  `dn-role-state-and-scoped-handoff` principle applied one level up: **the seat persists, the
  occupant does not.**

⚑ THE MECHANISM ALREADY LANDED, TODAY: |
  bp-110 (merged and sealed 2026-07-26) built exactly this shape — a compute half dispatched to a
  subprocess that holds NO store handle, sealed against egress, streaming batches back while the
  SUPERVISOR performs every landing (single-writer preserved). **A Claude agent as a job kind is
  that shape**: compute out-of-process, the supervisor lands the result.
  The queue also already has what lifecycle control needs: durable rows, ordering, leases and
  deadlines (bp-109), checkpointing, an orphan sweep, and `job_budgets` per kind. `worker_mode`
  ships `inproc` and default-off, so nothing is presumed.

⚑ THREE THREADS FROM TONIGHT COLLAPSE INTO ONE PRIMITIVE: |
    role STATE      (ratified note — the seat's durable state)
    role ADDRESS    (the email thread — `orchestrator@`, `scheduler@`)
    role MESSAGING  (this — broadcast and one-to-one to a party/role)
  ⇒ **A role is an addressable seat with durable state and a mailbox.** The ratified note already
  fixed the registry (singletons: `orchestrator`, `scheduler`; builders are PLURAL and get no role
  scope, their state is plan-bound), so "message a role" finally has a well-defined target — and
  "message a builder" correctly does not.
  Also settles the earlier email thread's open question at zero cost: an inbound queue the daemon
  polls IS the return path (`ambassador-thread-and-the-afk-loop` reached the same place: "the
  scheduler already owns a job queue; a message is a job").

open_questions:
  - ⚑ THE HARNESS BOUNDARY — **RESOLVED by the owner: use the Claude Agent SDK.** *"using the sdk,
    that's how we spawn one of those code agents, via a claude-code session with a starting
    prompt."* `[GROUNDED]` in the `claude-api` skill's four-approaches table: the **Claude Agent
    SDK** (`claude-agent-sdk` / `@anthropic-ai/claude-agent-sdk`) is **Claude Code packaged as a
    library** — you call `query(prompt, options)` and it supplies the full agent loop, context
    management, hooks, subagents, permissions, sessions, and the built-in
    Read/Write/Edit/Bash/Glob/Grep/WebSearch/WebFetch tools plus MCP.
    ⚑ It is **harness-only: YOU HOST AND DEPLOY IT.** That is exactly the right shape here — the
    scheduler/queue IS the deployment, and the SDK supplies the agent. It also settles the earlier
    worry: this is a real library boundary, not `claude -p` one-shots.
    ⚑ It is a **different package from the API "Tool Runner"** (`client.beta.messages.tool_runner`),
    which loops over tools you define and ships no built-in tools — do not substitute one for the
    other. The Agent SDK has its own docs (`code.claude.com/docs/en/agent-sdk`); the `claude-api`
    skill explicitly does NOT cover it.

  - ⚑⚑ THE ALTERNATIVE TO REJECT DELIBERATELY — **Managed Agents (CMA)**. It is the only option that
    supplies harness **AND** managed deployment: Anthropic runs the loop *and hosts a per-session
    sandbox* where bash/file-ops execute. It even ships **scheduled deployments** (cron firing
    sessions autonomously), which directly overlaps the scheduler idea above.
    **Reject it, and for a stated reason rather than by default:** the owner's frame is
    *LOCAL = internal, the residency of Ouroboros*. CMA would put tool execution — the filesystem,
    the repo, the corpus-adjacent work — inside Anthropic's cloud container. That is the opposite of
    the boundary he drew.
    ⚑ **The genuine middle path, worth knowing before deciding:** CMA supports **self-hosted
    sandboxes** (`config: {type: "self_hosted"}`) — the agent loop stays on Anthropic's
    orchestration layer while tool execution runs in a container HE controls, reached by an
    **outbound-polling worker** (Anthropic never dials in). The outbound-only property matches his
    security posture well. The residual: the *loop* is still orchestrated remotely.
    ⚑ HONEST NOTE ON ALL THREE: **the model runs at Anthropic in every case.** The choice is where
    the HARNESS and the TOOL EXECUTION live, not where the reasoning happens. NN-1 already settles
    the core question — sealed core has zero egress, so every one of these is edge-plane by
    construction and none can live in core.

  - ⚑ A PRACTICAL TRAP, `[GROUNDED]` in the CLI skill: Claude Code and the Claude Agent SDK
    **honour the same credential-profile resolution**, and after an `ant auth login` Claude Code may
    warn about a conflict between the profile and its own `/login` credential — keep ONE. A stale
    exported `ANTHROPIC_API_KEY` also silently outranks every profile (an *empty* one still wins its
    slot). Since the daemon would be spawning agents while he uses Claude Code interactively on the
    same machine, this collision is likely, not hypothetical.
  - ⚑ EVICTION IS THE FEATURE WITH NO CURRENT EQUIVALENT. Today a running agent can only be killed
    out-of-band; the artifact chain never learns. bp-110's escalation path (SIGTERM → grace →
    SIGKILL, `escalation_grace_s`, consumed by bp-112) is the mechanism — but a killed AGENT is not
    a killed compute job: it may hold a worktree with uncommitted work. What does eviction owe the
    victim? (Precedent to reuse: the checkpoint contract, and worktree-resume corruption is a known
    hazard — never resume an agent that died during setup.)
  - **Budget as a first-class field.** Today the orchestrator probes `/usage` and eyeballs whether a
    spawn fits. A queue that already carries `job_budgets` could make that structural instead of
    judgemental — the single highest-value item here, because it converts a standing discipline
    into a control.
  - NN-8's memory ceiling and bp-110's single-model-in-flight rule govern RESIDENT LOCAL models. A
    Claude agent consumes tokens and API quota, not GB — so the accounting axis is different and
    the ceiling does not cover it. A second budget dimension, not a reuse of the first.
  - Priority: does this reuse the existing tier/`blocked_tiers` machinery or need its own? Reusing
    a field for a second meaning is how `blocked_tiers` would get overloaded — bp-110's Item 4
    explicitly refused that ("two different reasons to refuse a tier, conflated into one predicate,
    is how a reader later cannot tell which rule refused a job").
  - Broadcast semantics: at-least-once or at-most-once? A broadcast to a PLURAL role (all builders)
    has no closed recipient set at send time, since builders come into existence after the send.

next_steps:
  - Hold as a brainstorm. Sequence AFTER the role-state plans land (they define the seat and its
    state; this gives the seat a scheduler and a mailbox — building the mailbox first would invent
    a second addressing scheme).
  - ⚑ Its cheapest genuinely-useful first slice is probably **recording agent spawns as queue rows**
    — no lifecycle control, no messaging, just making the untracked tracked. That alone fixes the
    defect this capsule opens with, and it is a small plan.
```
