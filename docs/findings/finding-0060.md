---
type: finding
id: finding-0060
status: routed
created: 2026-07-13
updated: 2026-07-13
links:
  - .claude/hooks/_lib.py # cmd_stop_audit (c)/A3 blessing checks
  - .claude/skills/context-economy/SKILL.md # the resume-brief lifecycle
ftype: direction
origin_plan: orchestrator
route: orchestrator
resolution: null
---

# The owner-blessing → commit dance is undocumented recurring friction at the Stop gate

## What

When the owner hand-flips a plan `proposed → ready` (or a note `draft → ratified`), the
edit sits UNCOMMITTED in the working tree. The journal-gate's `(c)` / A3 blessing check
diffs the working tree against HEAD, so the orchestrator's very NEXT action trips
"BLOCK: (c) uncommitted blessing transition vs HEAD" — even though the flip is entirely
legitimate (it IS the owner's manual blessing). Observed 2026-07-13: the owner blessed
bp-023/024/025 → ready; the next Stop fired the block; the orchestrator had to commit the
blessing (`chore(gate): owner blesses …`) before proceeding. This recurs on EVERY hand
blessing and is nowhere documented as the expected flow — it reads as an error the first
time, every time.

## Why it matters

The gate is correct (a blessing must become accountable to a commit — that is the whole
point of the check). But an *expected* step that presents as an *error* is a papercut that
(a) costs a fresh orchestrator a beat of "did I do something wrong?", and (b) risks a
session ending with an uncommitted blessing if the orchestrator doesn't know to commit it.
The fix is to make the step expected, not to loosen the gate.

## Re-entry condition

The next /triage weighs the smoothing. Candidates: (1) a standing rule (already added to the
resume brief 2026-07-13: "the orchestrator's first act after a hand-blessing is to commit
it"); (2) a session-start nudge — `session-brief.sh` detects a pending
`proposed→ready`/`draft→ratified` flip vs HEAD and prints "owner blessing pending — commit
it" at the top of the brief; (3) a tiny `commit-blessing` helper the orchestrator runs.
(1) is done; (2)/(3) are the promotion decision.

## Routing

`direction` → orchestrator (workflow/enforcement ergonomics). Non-blocking; the gate works,
this is about making its expected path legible.
