---
type: finding
id: finding-0155
status: open             # open → routed → resolved | promoted
created: 2026-07-21
updated: 2026-07-21
links:
  - docs/design-notes/track-board-and-deskcheck-gate.md
  - docs/build-plans/bp-097/plan.md
ftype: discovery         # blocker | spec-defect | question | discovery
origin_plan: bp-097
route: orchestrator      # design|direction — the owner decides whether to graduate a new plan
resolution: null
---

# P-WF1 probe: the running model id is NOT directly exposed to hooks, but IS reachable indirectly via `transcript_path`

## What

bp-097 Item 7 (the ≤5-min P-WF1 probe, design-note D7): *does the PreToolUse hook
environment expose the running model id* (the re-entry condition for a structural
model-per-phase gate — e.g. gate-guard refusing a **non-Fable** design-note
*creation*)? Evidence gathered live (session on this worktree):

- **Environment variables — NO model id.** The harness exposes `CLAUDE_EFFORT`
  (=`high` here — the effort tier) plus `CLAUDECODE`, `CLAUDE_CODE_SESSION_ID`,
  `CLAUDE_JOB_DIR`, `AI_AGENT=claude-code_2-1-206_agent`, but **no** `CLAUDE_MODEL`
  or any variable that distinguishes fable from opus. (Effort tier ≠ model id — the
  fable↔opus mismatch this repo tracks as a live harness bug is invisible to env.)
- **stdin JSON — no direct `model` field.** The standard PreToolUse hook payload
  (which `_lib.load_stdin` parses) carries `session_id`, `transcript_path`, `cwd`,
  `permission_mode`, `hook_event_name`, `tool_name`, `tool_input` — no `model` key.
- **Transcript — records the model per message.** The session transcript JSONL
  (`~/.claude/projects/<slug>/<session>.jsonl`) records `message.model` on every
  assistant turn; for this builder it read `claude-opus-4-8` (independently
  confirming the delegate-skill warning that a `model: fable` spawn can silently
  land on opus — this build did).
- **The reachable path.** Because the hook payload includes `transcript_path`, a
  hook *can* read that JSONL and extract the last assistant message's `message.model`
  to learn the running model id. So the id is **indirectly available**, not directly.

## Why it matters

D7 parked structural model-per-phase enforcement on the assumption (flagged
`[INFERENCE]`) that a hook *cannot* read the model id. The probe refines this: the
**direct** path (a clean env var / stdin field) does **not** exist, but an
**indirect** path (parse `transcript_path` → last `message.model`) **does**. That
partially satisfies P-WF1's re-entry condition — enough to warrant an owner
decision, not enough to justify building the gate under bp-097 (§10 stop-and-raise:
"the probe surfaces that the model id IS available ⇒ do not build the structural
gate here; journal the path and let the owner graduate a new plan"). No code shipped
from this probe.

The indirect path is **fragile and non-trivial**, which the graduating plan must
weigh: (a) reading + JSON-parsing a growing transcript on *every* PreToolUse fires
in the hot path; (b) "the last assistant message" is a race against the in-flight
turn — the model that will *execute* the edit vs. the last *recorded* message may
differ at boundaries; (c) it couples enforcement to an undocumented transcript
schema that the harness may change; (d) it must fail-open (a missing/parse-failed
transcript can never block a legitimate write). A robust structural gate really
wants a first-class model-id field in the hook payload — worth an upstream ask.

## Re-entry condition

Owner decides whether the indirect `transcript_path` path is robust enough to
graduate a **new** plan for structural model-per-phase enforcement (e.g. gate-guard
refusing a non-Fable design-note *creation*), or whether P-WF1 stays parked pending
a first-class hook-payload model field. The procedural backstop (context-economy's
banner + usage-verify + board visibility) remains the default until then.

## Routing

- `design | direction` → the orchestrator batches to `owner-questions.md`: this is
  a parked-decision re-entry (D7 / §11 P-WF1), owner's call to graduate or keep
  parked. A design-changing decision would supersede/amend the note, warrant-linked
  to this finding, then this flips to `promoted`.
