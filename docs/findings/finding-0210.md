---
type: finding
id: finding-0210
status: routed
created: 2026-07-26
updated: 2026-07-26
links:
  - .claude/commands/capture.md                 # ":14 — Append a `## <UTC timestamp>` section" (source unspecified)
  - docs/templates/capsule.md                   # the capsule shape
  - docs/brainstorms/autopilot-mode.md          # where the drift is measurable
ftype: spec-defect
origin_plan: orchestrator                       # observed while appending a capsule, /triage session-52
route: orchestrator
resolution: null
---

# Brainstorm capsule timestamps drift ahead of the clock, and capsule order is load-bearing

## What

`.claude/commands/capture.md:14` says only *"Append a `## <UTC timestamp>` section"* — it does not say
where the timestamp comes from. In practice a session composes it, and it drifts.

Measured this session in `docs/brainstorms/autopilot-mode.md`: the last four capsules are labelled
`04:58Z`, `05:14Z`, `05:33Z`, `06:34Z`, `07:14Z` — but the commit that carries them, `3e88bae`, is
dated `2026-07-26 01:44:37 -0400`, i.e. **05:44Z**. So the final three labels are **stamped ahead of
the moment the file was written**, the last by roughly 90 minutes. Appending a truthfully-stamped
capsule after them therefore produces a file whose headings run `07:14Z` then `06:05Z` — non-monotonic,
and visibly wrong either way.

## Why it matters

Small, except that **capsule order carries meaning**. The standing reading convention for these files
is *"later capsules supersede earlier ones and say so"* — that is how a multi-capsule brainstorm like
`autopilot-mode.md` (now 14 capsules, several explicitly reversing earlier ones) stays legible at all.
A label that runs ahead of the clock inverts the only ordering signal a reader has, for a reader who
reasonably trusts the timestamp over file position.

Two ways that bites:

1. **A human or agent resolving a contradiction between capsules** picks the later timestamp and gets
   the earlier decision. In this very file, capsules disagree about the primitive (HMAC → signature),
   about granularity, and about whether a wave grant is permitted — exactly the places where picking
   the wrong one is expensive.
2. **The corpus ingests these files.** Once code and docs are embedded as first-class semantic sources,
   a fabricated timestamp is durably-recorded false metadata, and the temporal machinery (diachronic
   reader, β\* over lineage, "graph at a past cut") is precisely the machinery that would key on it.

Direction of the error is *not* safe here: unlike a stale claim that under-reports, this one silently
reverses a supersession.

## Re-entry condition

Cheapest fix, and it removes the discretion rather than asking for care: `.claude/commands/capture.md`
pins the source explicitly — the timestamp is taken from `date -u +"%Y-%m-%dT%H:%M:00Z"`, never
composed. Optionally, a check that a newly appended heading is not earlier than the file's last
heading (a two-line guard, and the only ordering invariant these files have).

The already-written labels stay as they are: a brainstorm is an append-only record and rewriting its
history to look tidy is worse than a documented drift. The `06:05Z` capsule in `autopilot-mode.md`
carries an inline ordering note saying position, not label, is authoritative there.

## Routing

`spec-defect` → orchestrator. It is a defect in a command the orchestrator owns; no owner ruling and
no design change is required. Fold into the next workflow/tooling touch — it is one line.
