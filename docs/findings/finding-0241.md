---
type: finding
id: finding-0241
status: open
created: 2026-07-27
updated: 2026-07-27
links:
  - docs/design-notes/role-state-and-scoped-handoff.md   # §4 stage (a)/(b) — the overlapping window
  - docs/build-plans/bp-125/plan.md                      # the migration that raced its own input
  - docs/build-plans/bp-126/plan.md                      # the cutover that deletes the input
  - docs/roles/orchestrator/journal.md                   # where the delta was carried
ftype: spec-defect
origin_plan: bp-125
route: orchestrator
resolution: null
---

# The migration races its own input: the overlapping window lets content arrive *after* the migration and *before* the deletion

## What

`bp-125` migrates `.claude/state/resume-brief.md` into the orchestrator seat; `bp-126` deletes
that file. The design note's §4 stages the two deliberately, with an overlapping window in which
**the outgoing artifact keeps being written** (stage (a): *"old brief still written — a
deliberately overlapping window, at the cost of double bookkeeping for its duration"*).

The window has a gap nobody stated: **content written into the artifact after the migration reads
it, but before the cutover deletes it, is migrated by nothing and destroyed by the cutover.**

This is not hypothetical. It happened during `bp-125`'s own build, and was caught only because the
plan required a snapshot to be taken before reading:

- Snapshot at build start: 122 lines / 8,196 bytes.
- The same file at build end: 125 lines / 8,441 bytes, different digest.
- The delta was **not** noise. It contained a **fresh owner ruling** on commit economy (two parts,
  the second gating the first behind a build), plus a correction retiring an item the migrated
  entry still listed as unresolved.

Had the snapshot not been re-diffed at seal, that ruling would have been migrated by no plan and
deleted by `bp-126`, and its only other copy is an **untracked** brainstorm — so it would have
left the system entirely, with no history anywhere to recover it from. The migrated content is
carried in `docs/roles/orchestrator/journal.md` as a delta entry.

## Why it matters

The whole warrant of this family (`finding-0175`) is that the artifact is destructively
overwritten and historyless. The migration was supposed to end that. But a *staged* migration of a
live file inherits the same defect for the duration of its window: the file has no history, so
"what changed since the migration read it" is answerable **only** by a snapshot taken at read
time. Nothing in `bp-126` currently requires one.

The exposure is proportional to the window's length, and the window is at least "however long
`bp-125` runs, plus however long `bp-126` waits." For a wave running under a live orchestrator
session that keeps closing units, that is exactly when the file is being written most.

## The concrete instruction for `bp-126`

Before deleting `.claude/state/resume-brief.md`, **diff it against what `bp-125` actually
migrated** and carry anything new into the seat journal in the same diff as the deletion. The
migrated state is pinned in `bp-125`'s plan journal by digest:

```
122 lines / 8196 bytes   sha256 0a5bbfb28b829ed1a7203fd568f97d146415a31c9cb713309ec137f3bd547057   (snapshot 1, the census base)
125 lines / 8441 bytes   sha256 e8860173b11efbcc30397105479b71a2814ff89ca82edf4b56a5579536d063a8   (snapshot 2, delta migrated)
```

If the file's digest at cutover matches snapshot 2, nothing new arrived and the deletion is safe.
If it does not, the difference is unmigrated content and must be carried before the file is
removed. **This check is cheap, mechanical, and the last chance** — after the deletion there is no
history to recover from.

## Re-entry condition

Resolved when `bp-126` either (a) carries the delete-time diff check as an acceptance criterion,
or (b) records that it verified the digest matched and no delta existed. Either discharges it;
silently deleting does not.

## Routing

`spec-defect` on the design note's stage model → **orchestrator**. It needs a decision the builder
should not make alone, because it changes another plan's acceptance criteria and because the
general lesson — *a staged migration of an unversioned live file must pin its input by digest and
re-check at cutover* — belongs in the note rather than in one plan's journal.

Not a blocker for `bp-125`: its own items are complete and the observed delta is migrated.
