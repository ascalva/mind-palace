---
type: finding
id: finding-0061
status: routed
created: 2026-07-13
updated: 2026-07-13
links:
  - docs/findings/finding-0059.md # the instance that made the class visible
  - docs/templates/build-plan.md # §3 investigation & grounding
ftype: direction
origin_plan: orchestrator
route: orchestrator
resolution: null
---

# Quantitative baselines carried from another artifact go stale — a build-plan §3 discipline gap

## What

A plan's §3 grounding often cites a NUMBER from an upstream artifact (a design note's
inventory, a prior plan's count) and carries it forward as an acceptance premise. This
session made the failure mode concrete twice at once (finding-0059): dn-self-sensing §3.2's
"11 pre-rule plans, zero cost blocks" was carried into BOTH bp-019 §3 Q4 AND bp-020 §3 Q1 /
Item 10's acceptance test — and was stale (the true count is 8; bp-006/007/009 were
backfilled after V3's read). Separately, bp-020 §4's premise "bp-013's `actual` is null" was
also stale — it had been seal-filled but mis-encoded. In both cases the plan grounded
against a SNAPSHOT that had drifted by build time; only the builder's at-HEAD re-grep caught
it (for the marker) — but the NUMBER was trusted, not re-grounded.

## Why it matters

Plans are trusted-by-construction: a builder executes §7 against §3's premises. A stale
quantitative premise silently weakens an acceptance test (Item 10's "bp-000..010 → zero
rows" was falsified as literally written by 3 IDs) or sends a builder chasing a phantom
(bp-020's "correct a null" was really "correct an encoding"). The build-plan template
already mandates at-HEAD grounding for CODE ("who calls this API?" with a §3 re-grep
obligation) but says nothing about NUMBERS carried from docs — the easily-missed tooth.

## Re-entry condition

The next /triage weighs a build-plan §3 (and graduate-skill) discipline: **any quantitative
baseline carried from another artifact must be re-grounded at the builder's HEAD and tagged
as re-verified — never trusted from an upstream snapshot.** Cheap to state, catches a real
class. Promotion → a one-line amendment to `docs/templates/build-plan.md` §3 guidance + the
graduate skill's sizing note.

## Routing

`direction` → orchestrator (process/template). Non-blocking; the fix is a documented
grounding discipline, verifiable by a plan reviewer at graduation.
