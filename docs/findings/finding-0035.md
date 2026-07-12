---
type: finding
id: finding-0035
status: resolved
ftype: direction
origin_plan: null   # workflow practice — owner-directed, 2026-07-11
route: orchestrator
created: 2026-07-11
updated: 2026-07-12
links:
  - .claude/skills/context-economy/SKILL.md   # where the practice is documented
  - .claude/hooks/session-brief.sh             # the SessionStart hook that would auto-surface it
  - docs/build-plans/bp-014/plan.md            # the hooks session this hook change folds into
  - docs/templates/resume-brief.md             # rec 2's template (landed 2026-07-12)
resolution: all three recommendations landed — rec 3 (auto-surface) by bp-014 Item 3 (2026-07-12); recs 1+2 at /triage same day (location/lifecycle/schema rule in context-economy SKILL.md + the seven-section `docs/templates/resume-brief.md` template).
---

# finding-0035 — The orchestrator emits a documented-style self-resume prompt at clearing boundaries

## What

The owner directed (2026-07-11): when context builds up and a session clears, the ORCHESTRATOR
should **emit its own resume prompt** — the first thing the next session reads — so the owner
never has to know how to re-prompt it. And critically: **the prompt STYLE must be well-documented**
so every session produces a consistent, complete handoff.

## Why it matters

Today the resume brief is ad-hoc — the owner literally had to ask "how do I prompt you?". The
context-economy skill already says "end at unit boundaries with a resume brief," but it doesn't
(a) fix a durable LOCATION, (b) define the prompt's required SHAPE, or (c) auto-surface it. Without
a documented style, resume prompts drift in completeness — and a missing "in-flight" line is exactly
how a fresh session re-asks or RACES a running builder (the bp-008 near-miss this session, where a
builder assumed dead was only slow-polling).

## The documented style (proposed — required sections)

A resume prompt is NOT free-form; it must carry, in order:

1. **Session tier** — the derived `/model` + `/effort` for the next unit (context-economy rubric).
2. **In-flight** — any running builder (worktree PATH + branch), what to check, and the
   merge/seal/park owed. **The single load-bearing section** — a cleared session must never orphan
   or race in-flight work.
3. **Then-queue** — the ordered next units (blessed/ready plans), each with its tier.
4. **Design-tier deferrals** — threads to NOTE, not do, in a supervision session (with pointers).
5. **Standing rules** — the session-invariant constraints (push/deploy/trailer/uv).
6. **Open desk** — outstanding owner questions.
7. **Self-rewrite instruction** — the next session rewrites the file at ITS own boundary.

(A live example written this session: `.claude/state/resume-brief.md`.)

## Recommended direction (route: orchestrator)

1. **Location + lifecycle:** `.claude/state/resume-brief.md` (ephemeral, gitignored) — written by
   the orchestrator at a clearing boundary, consumed + cleared by the next session. `docs/PROGRESS.md`
   stays the committed durable backstop (portable across machines; the resume-brief is the fast path).
2. **Documented style:** formalize the section schema above into `docs/templates/resume-brief.md` +
   a rule in `context-economy` (SKILL.md).
3. **Auto-surface:** the `session-brief.sh` SessionStart hook emits `.claude/state/resume-brief.md`
   (if present) at the TOP of the SESSION BRIEF, so a fresh session reads it FIRST with ZERO owner
   action. Small hook change — **fold into bp-014** (which already opens `.claude/hooks/**`).

## Re-entry

Parked for the hooks session (bp-014-adjacent) + a skill/template pass. Trigger that reopens
immediately: the next clear where the owner has to ask "how do I prompt you?" again.

## Partially addressed (2026-07-12, bp-014 Item 3)

Recommendation **3 (auto-surface)** is DONE: `.claude/hooks/session-brief.sh` now emits
`.claude/state/resume-brief.md` (if present) at the TOP of the SESSION BRIEF, above the
`═══ SESSION BRIEF ═══` block, resolved under the worktree-aware ROOT (bp-014 Item 1). It is
fail-open (a missing/unreadable brief never errors the hook) and the absent-file case is
byte-identical to before. Verified via `bash .claude/hooks/session-brief.sh --standalone`.

Still OPEN (route at /triage — OUT of bp-014's write_scope, deliberately not touched here):
- Recommendation **1 (location + lifecycle)** — formalizing `.claude/state/resume-brief.md` as
  the durable location + the write/consume/clear lifecycle in workflow docs.
- Recommendation **2 (documented style)** — the section schema → `docs/templates/resume-brief.md`
  + a `context-economy` SKILL.md rule.

Status stays `routed` (NOT `resolved`): only 1 of 3 recommendations landed.

## Resolved (2026-07-12, /triage) — recs 1+2 landed; all three now closed

- **Rec 1 (location + lifecycle):** formalized in the context-economy skill — a dedicated
  "resume brief" section fixing `.claude/state/resume-brief.md` as the ephemeral fast path
  (PROGRESS.md the durable backstop) and the write → auto-surface → consume → REWRITE cycle,
  including the never-stale rule.
- **Rec 2 (documented style):** the seven-section schema is now `docs/templates/resume-brief.md`
  (annotated template, in-order required sections, §2 In-flight flagged load-bearing) + the
  schema digest in the same context-economy section.
- **Rec 3 (auto-surface):** was already live via bp-014 Item 3 (`session-brief.sh`).

Reopen trigger: a cleared session's brief missing a required section (esp. in-flight), or the
owner having to ask "how do I prompt you?" again.
