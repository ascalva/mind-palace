---
name: context-economy
description: When to clear, compact, or continue a session — token spend is O(context × turns × tier), and the artifact chain makes sessions disposable. Session typing (model/effort per purpose), polling discipline, and the usage ledger.
---

# context-economy — sessions are disposable; artifacts are not

The cost model (owner rule, 2026-07-11): every turn pays roughly **context-length ×
model-tier × effort**, and the prompt cache only softens gaps under ~5 minutes. A
marathon session at the top tier is the single most expensive object in the system —
measured 2026-07-11: one all-day orchestrator session dominated the entire day's spend,
exceeding every delegated build combined. The constitution already built the fix: the
fresh-agent test means state lives in artifacts (plan + journal + PROGRESS + findings),
so **a session that ends loses nothing it was supposed to keep.**

## The decision rule

- **CLEAR (end the session) at unit boundaries.** After a seal, a merge, a graduation, a
  triage sweep, a deploy — if the next task's context manifest is *files on disk* rather
  than *this conversation*, end. Proactively SAY SO: close the unit with a one-paragraph
  resume brief (what's in flight, where the artifacts are) and recommend the owner clear.
  The next session resumes from artifacts at a fraction of the cost.
- **COMPACT mid-unit** when work must continue (uncommitted state, live supervision) but
  the conversation carries dead threads. **Journal before compact** — compaction is lossy;
  anything load-bearing that lives only in chat gets checkpointed to the journal/PROGRESS
  first, then compaction is safe by construction.
- **CONTINUE** only when the thread is genuinely live and the cache is warm.

## Session typing (set /model + /effort to the session's purpose at its start)

| Session type | Model | Effort | Examples |
|---|---|---|---|
| Design / gates / scrutiny | top tier (Fable) | xhigh | graduation, amendment drafting, merge scrutiny, triage |
| Supervision / plumbing | mid (Opus/Sonnet) | default | poll-merge-report loops, CI babysitting, routine seals |
| Grind | delegate down (sonnet/haiku builder) | — | crisp-checker work; never done in the orchestrator |

Reserve the top tier for the ~20% of work that is judgment; the mechanical majority
must run where the meter doesn't matter.

## Sensing complexity (the auto-switching rubric, owner rule 2026-07-11)

The session CANNOT flip its own model/effort — those are the owner's commands. The skill
delivers the same economics through two mechanisms:

**1. Route work through right-sized subagents** (the Agent tool takes model + effort per
spawn). Score the unit on four axes; the highest axis wins:

| Axis | cheap (haiku/sonnet) | full-strength (top tier) |
|---|---|---|
| Verification | a crisp checker judges (mypy, tests, grep) | a falsifier needs judgment to evaluate |
| Blast radius | new files, docs, additive | hooks/enforcement, core invariants, migrations |
| Novelty | grounded plan pins everything | open design, unpinned interfaces, spikes |
| Reversibility | worktree-contained, revertable | touches live stores, published surfaces |

If any axis says full-strength, the unit is full-strength. When axes disagree wildly,
split the unit instead of averaging.

**2. Declare the tier at every boundary.** Each resume brief MUST end with the next
session's recommended `/model` + `/effort`, derived from the rubric applied to the
queue's next unit — the owner's switch becomes one informed keystroke. A session that
discovers mid-flight it is under-tiered for an emergent design question does not strain:
it notes the question for a top-tier session and continues its own lane. Over-tiered is
the silent failure — notice it at the next boundary and say so in the brief.

## Polling & notification discipline

Attested machinery does not need watching — CI, the witness, launchd, builders in
worktrees all leave verifiable records. Prefer: long poll intervals, bundled verdicts,
background tasks over foreground loops, and NEVER a top-tier re-invocation whose only
work is reading a progress bar. A builder's death is recoverable from its worktree +
journal (proven 2026-07-11), so a cleared session does not orphan in-flight work —
the next session inspects `.claude/worktrees/` and the plan journals.

## The usage ledger

Every delegated build's completion notification carries measured token usage — record it
in the plan's SEAL entry (tokens, tool calls, duration, model). PROGRESS checkpoints for
heavy days note session shape (how many sessions, which tiers). Two weeks of seals = a
real per-plan cost table; the evolution study gains an economics axis.

## Anti-patterns (all field-observed)

- The all-day orchestrator session (the whale — this skill exists because of it).
- Fable-at-xhigh turns spent running `curl` in a loop.
- Re-deriving state from conversation that a journal already holds.
- Delegating the work but supervising it at ten times the worker's token cost.
