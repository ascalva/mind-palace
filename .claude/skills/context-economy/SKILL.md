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
  than *this conversation*, end. Proactively SAY SO: close the unit by writing the seat's
  **NARRATIVE** entry and regenerating its **DERIVED** rendering (the handoff pair, below),
  then recommend the owner clear. The next session resumes from artifacts at a fraction of
  the cost.
- **COMPACT mid-unit** when work must continue (uncommitted state, live supervision) but
  the conversation carries dead threads. **Journal before compact** — compaction is lossy;
  anything load-bearing that lives only in chat gets checkpointed to the journal/PROGRESS
  first, then compaction is safe by construction.
- **CONTINUE** only when the thread is genuinely live and the cache is warm.

## Session typing (set /model + /effort to the session's purpose at its start)

| Session type | Model | Effort | Examples |
|---|---|---|---|
| Design / gates / scrutiny | top tier (Fable) | xhigh | graduation, amendment drafting, merge scrutiny, triage |
| Supervision / plumbing | mid (Opus/Sonnet) | **high** (orchestrator default, owner rule 2026-07-21 — raised from medium after the audit sweep) | poll-merge-report loops, CI babysitting, routine seals |
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

**2. Declare the tier at every boundary.** Each seat-journal entry written at a clearing
boundary MUST end with the next session's recommended `/model` + `/effort`, derived from the
rubric applied to the queue's next unit — the owner's switch becomes one informed keystroke.
The duty is unchanged and was never wrong; only its container moved (the recommendation is a
judgement about the *next* unit, so it is NARRATIVE and no generator can render it). A session that
discovers mid-flight it is under-tiered for an emergent design question does not strain:
it notes the question for a top-tier session and continues its own lane. Over-tiered is
the silent failure — notice it at the next boundary and say so in the brief.

## The handoff pair — the seat's DERIVED rendering + its NARRATIVE segment (dn-role-state-and-scoped-handoff §2.9)

> ⚑ **CORRECTION — a prior ratified discipline was replaced, not drifted away from.** This section
> previously specified a single ephemeral, gitignored, **destructively overwritten** file under
> `.claude/state/`, hand-rewritten at every boundary to a seven-section schema (finding-0035). That
> discipline is **superseded** by `dn-role-state-and-scoped-handoff` and migrated by `bp-125`.
> Three things changed and each was a defect, not a preference:
> **(1)** the artifact was outside git, so it had no history — the last destructively-overwritten
> artifact in a system that had outlawed destructive overwrite (`finding-0175`, the warrant);
> **(2)** the seven-section schema mixed four kinds of fact with four different freshness rules, so
> the derivable ones rotted in place while sitting in prose; **(3)** the "rewrite it yourself at
> every boundary" step made freshness a hand-authored act that every later commit re-armed. It is
> replaced by **regenerate and commit**.

A seat's handoff is **three artifacts, not one**, split by *who can produce the fact* — because
each kind has a different freshness rule and mixing them is what rotted the old one:

| pane | artifact | what it holds | freshness |
|---|---|---|---|
| **DERIVED** | `docs/roles/<role>/handoff.md` | anything a scan of the artifact tree can produce — statuses, tallies, what awaits the owner | **regenerate**; staleness impossible by construction |
| **MEASURED** | `docs/roles/<role>/readings.md` | the result of *running* something — a suite, a usage probe, a daemon check | a timestamped row; **age displayed, never hidden** |
| **NARRATIVE** | `docs/roles/<role>/journal.md` | judgement no generator can write — what to spawn, what to watch, an ordering intent | append-only; an entry exists for this session |

All three are **git-tracked** — so they are present in every checkout a successor might start
from, which is the constraint that decided the substrate.

- **Write the NARRATIVE, regenerate the DERIVED.** At a clearing boundary: append a seat-journal
  entry (the checkpoint contract, one scope up — see the **checkpoint** skill), then
  `uv run scripts/handoff.py --role <role> --write` and commit. Verify with `--check`, which exits
  0 when the committed rendering matches a fresh one. Because the rendering embeds **no commit sha
  and no timestamp**, that converges in **one step** — regenerating never re-arms itself.
- **Never hand-write a derivable fact into the narrative.** The **purity rule**: narrative names
  artifacts by stable id (`bp-110`, `finding-0227`, `oq-0051`) and **never states a machine-derivable
  value** — no commit hashes, no plan statuses, no counts, no `path:line` into code that moves. The
  id is the join key; the value lives in the pane. A hand-copied value is a value that will be
  wrong later, and the seat will not know when.
- **A reading is never gated.** Take one when the work warrants it; the pane shows its age. If a
  reading's own timestamp is unknown, record it as unknown — a fabricated timestamp lets a stale
  reading impersonate a current fact, which is precisely what the age display exists to prevent.
- **Retention is append-only** (`finding-0164` / `finding-0168`: keep and link, never delete and
  replace). Compaction writes a **capsule** — one entry carrying every still-live judgement forward
  and naming the range it supersedes, with the superseded entries retained beneath it. After
  compaction the authoritative narrative is *the latest capsule plus every entry after it*;
  everything before is readable history, and **non-binding**.
- **Declare the next session's tier in the narrative entry** — see the tier duty above; it is one
  of the judgements a generator cannot make, so the seat journal is its home.

⚑ **During the cutover window** the *previous* Stop-gate clause is still the one installed, and it
still demands the outgoing ephemeral artifact at close; its own block message names the file and
the act. That double bookkeeping is deliberate and ends when `bp-126` lands the replacement clause,
retires the outgoing artifact and its template together, and re-points the session-brief hook.

## Rules do not live in handoff state

A durable rule is **not** handoff state at all, and putting one there is how it stops binding: it
**loads at the moment of use, or it does not hold**. Commit and staging discipline → the **commit**
skill. Gate legs, spawn/worktree mechanics, the budget gate → the **delegate** skill. Clearing and
tiering → this skill. The domain non-negotiables and the blessing gates → `CLAUDE.md` and
`CONSTITUTION.md`. A rule already living in one of those is **already home** — copying it into a
handoff makes a second copy that drifts, and the prose copy is always the one that rots.

This is not a style preference; it is the repo's own measured result. The `git add -A` and
`git commit -F -` rules **held once they were moved into the commit skill and failed repeatedly
while they lived in the handoff** — the same rules, the same agents, a different container.

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
