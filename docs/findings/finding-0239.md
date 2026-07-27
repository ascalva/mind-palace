---
type: finding
id: finding-0239
status: resolved
created: 2026-07-27
updated: 2026-07-27
links:
  - docs/build-plans/bp-125/plan.md                          # Item 6 — the acceptance test at issue
  - docs/design-notes/role-state-and-scoped-handoff.md       # §2.9 — the idempotence pin that excludes shas
  - scripts/handoff.py                                       # the generator; renders no sha by construction
ftype: spec-defect
origin_plan: bp-125
route: builder
resolution: resolved in-plan — the DERIVED class has TWO replacement sources, not one; the sha subclass is replaced by `git log`, which §2.9 names explicitly. Item 6's acceptance sentence is narrower than the note it graduates. Census records the source per fact.
---

# Item 6's acceptance test names one replacement source; the design names two, and the second is `git log`

## What

bp-125 Item 6's acceptance test reads, verbatim:

> Re-running `uv run scripts/handoff.py --role orchestrator` shows each dropped fact present in
> the rendering.

and its falsifier: *"a fact classified DERIVED that the generator does **not** in fact render."*

Applied literally, that falsifier **fires** — on one subclass, in every case. The live brief's
DERIVED content includes four commit shas (the HEAD sha in its title, the merge and seal shas for
`bp-124`, the two blessing shas for the wave, and one sha attached to an owner-question ruling).
`scripts/handoff.py` renders **none** of them, and never will: `dn-role-state-and-scoped-handoff`
§2.9 forbids it in the load-bearing idempotence pin —

> the rendering is a pure function of the artifact tree *excluding itself*, and embeds **no HEAD
> sha and no generation timestamp** … This pin is *why* hashes leave the handoff: **a tracked
> artifact never needs to cite its own tree's commits — `git log` is already the derived view of
> commits.** The old brief cited hashes only because it lived outside git.

So the plan's acceptance sentence and the note's §2.9 pin cannot both be read literally. The
generator is correct; the acceptance sentence is under-specified.

## Why it matters

Read literally, the criterion is unsatisfiable and the falsifier reports content destruction where
none occurred — the plan's own §10 would demand a STOP on a healthy migration. Read loosely, a
builder could wave through a genuinely destroyed fact by asserting "some source has it." Neither
is acceptable, so the distinction has to be written down rather than judged per-case.

The substantive test the falsifier is protecting — *nothing is dropped without a named replacement
source* — is stated in Item 6's own invariant line and is the honest one. The rendering is one
such source; `git log` is the other, and it is strictly better than what it replaces: a sha
hand-copied into prose is exactly the class of fact the note observed rotting in place (§2.2's
second sub-fact, where a hand-copied line number drifted inside the paragraph documenting the
staleness defect).

## Resolution (builder, in-plan)

The DERIVED class is recorded in the census with a **replacement source per fact**, drawn from a
closed set of two:

1. **the handoff rendering** — for facts derived from artifact front matter (plan statuses and the
   status tally, finding ids, deskchecks owed, open-owner-question counts);
2. **`git log`** — for commit shas, per §2.9's explicit ruling.

Every dropped fact in this migration resolves to one of the two, and the census names which. No
fact was dropped to a third source, to "memory," or to nothing. The falsifier's *purpose* is
therefore discharged even though its literal text fires on subclass (2).

## Re-entry condition

None — resolved in-plan. If a future plan in this family restates Item 6's acceptance sentence,
it should say "a named replacement source (the rendering **or** `git log`)" rather than "the
rendering."

## Routing

`spec-fidelity` → the builder resolves, annotates here and in the plan journal, and continues.
No owner input is needed: the design note already rules the question, and this finding only
records that the plan's paraphrase of it was narrower than the ruling.
