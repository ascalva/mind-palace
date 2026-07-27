---
type: finding
id: finding-0240
status: resolved
created: 2026-07-27
updated: 2026-07-27
links:
  - docs/build-plans/bp-125/plan.md                          # Items 6 and 7 — the two criteria in conflict
  - docs/design-notes/role-state-and-scoped-handoff.md       # §2.5 purity rule; §2.11 F1b lint
  - docs/roles/orchestrator/journal.md                       # the seat journal the census must NOT enter
  - docs/build-plans/bp-125/journal.md                       # where the audit trail landed instead
ftype: spec-defect
origin_plan: bp-125
route: builder
resolution: resolved in-plan — the audit trail lands in the PLAN journal (which the plan's own "Owed at seal" section demands), leaving the seat journal purity-clean. The two criteria are jointly unsatisfiable in one file.
---

# The migration census cannot live where Item 6 files it — Item 7's purity lint forbids exactly its contents

## What

Two of bp-125's criteria address the same file and cannot both be met in it.

**Item 6** names `docs/roles/orchestrator/journal.md` in its *Files* field and requires that the
entry carry *"a class-by-class table with line counts summing to the live brief's line count, and
a **named** list of every fact dropped as DERIVED."*

**Item 7** requires of that same file's authoritative segment that
`grep -Ec '\b[0-9a-f]{7,40}\b'` return **0**, and the design note's §2.11 F1b makes that a lint.

The conflict is not stylistic, it is arithmetic. A *named* list of the facts dropped as DERIVED
must name the four commit shas the brief carried — that is what makes it an audit trail rather
than an assertion. Every one of those shas is a word-bounded hex token of length ≥ 7. Writing the
census into the seat journal therefore guarantees the purity lint fails; omitting the shas to pass
the lint destroys the audit trail's whole evidentiary value, which is the outcome Item 6's
falsifier exists to prevent.

Item 7's falsifier anticipates this shape exactly — *"the entry cannot be written without a commit
hash … file a `spec-defect` finding rather than smuggling the value in words ('the sha ending in
4b2')"* — and that instruction is followed here.

## Why it matters

Left unresolved, a builder either reddens bp-127's F1b lint on day one (with the seat journal's
very first migrated entry, the one the lint was written for), or quietly drops the sha list and
leaves no record of what was destroyed. The second failure is silent and permanent: the brief is
gitignored and has no history, so an un-audited drop is unrecoverable.

There is also a category point worth keeping. The seat journal is **NARRATIVE** — judgement no
generator can write, for the *next occupant of the seat*. A migration census is neither: it is
build-time evidence about a one-off act, addressed to a reviewer, and its natural half-life is
this plan. Filing it in the seat journal would make the seat's memory carry construction debris
forever, which is the accretion the note exists to end.

## Resolution (builder, in-plan)

The audit trail — the class census **and** the rule→home table — lands in
`docs/build-plans/bp-125/journal.md`, and the seat journal receives only purity-clean narrative.

This is not a workaround: the plan's own journal already demands it in *"Owed at seal"*, which
states that the Item 9 rule→home table and the Item 6 class census *"must survive in this journal,
not only in a diff"* — written in the plan journal, referring to itself. Item 6's *Files* field is
the outlier, and it is the line this finding corrects.

Verified after the migration: `grep -Ec '\b[0-9a-f]{7,40}\b'` over the seat journal returns 0 with
the migrated entry in place, and the census is present in the plan journal in full.

## Re-entry condition

None — resolved in-plan. A future plan that migrates content into a purity-linted artifact should
route its audit trail to the plan journal by default, and say so at graduation rather than leaving
the builder to discover the conflict.

## Routing

`spec-fidelity` → the builder resolves, annotates here and in the plan journal, and continues.
