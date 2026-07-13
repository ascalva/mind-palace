---
type: finding
id: finding-0058
status: open
created: 2026-07-12
updated: 2026-07-12
links:
  - ops/self_sensor.py
  - docs/build-plans/bp-019/plan.md
ftype: spec-defect
origin_plan: bp-019
route: builder
resolution: resolved
---

# bp-019 §6(e)'s pinned candidate-scan command omits `--first-parent`/`--root`, contradicting its own §3 risk analysis

## What

Plan §6(e) pins the candidate-commit scan as `git rev-list --reverse <branch> --
docs/build-plans/*/plan.md` (no `--first-parent`), and §3 Q3/parked-decision table
(§11 "candidate-commit scan") likewise says `rev-list <branch> -- docs/build-plans/*/plan.md
full-history reconcile`. But the plan's own §3 "Additional risks" paragraph states as a
LOAD-BEARING property: "candidate commits come from `rev-list main` (first-parent diffs,
§6(e)), so the branch-side duplicates are never candidates." That property is FALSE for a
bare (non-`--first-parent`) `rev-list` — empirically verified (a throwaway fixture repo
with a feature-branch commit merged via `--no-ff`): `git rev-list --reverse main --
docs/build-plans` INCLUDES the feature-branch-only commit as a candidate (it is a reachable
ancestor of the merge commit and touches the pathspec); only `git rev-list --first-parent
--reverse main -- docs/build-plans` excludes it, matching what the design text promises.

A second, smaller gap in the same section: `git diff-tree --first-parent -m sha --
docs/build-plans` (the per-commit diff, §6(e) as literally pinned) emits NOTHING for a
ROOT commit (no parent) — verified empirically. `--root` is required for `diff-tree` to
show the full-tree diff at a root commit, and is a no-op for every non-root commit (safe
to always pass). The plan itself requires root-commit support ("Root commits (no parent)
treat all present facts as new"), so this is the same class of gap: the pinned command
text under-specifies what its own surrounding prose requires.

## Why it matters

Building §6(e) exactly as literally written would: (a) double-project every merge-landed
fact (once at the branch-side commit under a candidacy the design explicitly rules out,
again at the merge commit) — silently violating the B-b idempotence falsifier's SPIRIT even
though each individual projection is itself idempotent; and (b) silently drop every root
commit's facts (the very first plan ever created, if its `cost:` block landed at the
initial commit) since `diff-tree` without `--root` returns empty for it — a false "zero
facts" rather than "all facts are new."

Caught in testing: `test_estimate_and_actual_land_at_their_own_commits` and
`test_root_commit_projects_all_present_facts_as_new`
(`tests/unit/test_self_sensor.py`) exercised these paths directly against real fixture
repos (not fixtures shaped to avoid the edge case) and reproduced both gaps empirically
before the fix.

## Re-entry condition

None — not a blocker, already resolved in this session (see Routing/resolution below). No
re-entry needed; recorded for the orchestrator's awareness in case bp-020's real backfill
run surfaces a related edge case the fixture repos here didn't cover (e.g. an octopus
merge, `-m` semantics with >2 parents — untested, believed safe by the same `--first-parent`
reasoning but not exercised).

## Routing

`spec-fidelity` — the builder (this session) resolved it directly, per the routing rule
("the builder resolves it, annotates the finding and the journal, and continues"):
- `sync()`'s `rev-list` call now passes `--first-parent` (matching the plan's OWN §3 risk-
  analysis prose, which is unambiguous about the required property even though §6(e)'s
  literal command text omitted the flag).
- `_changed_plan_files()`'s `diff-tree` call now also passes `--root` (a no-op for non-root
  commits, required for root-commit support the plan itself demands).
Both changes are additive flags to git invocations already named in §6(e) — not a
deviation from the design's INTENT, only a correction to command text that
under-specified it. `ops/self_sensor.py`'s inline comments document both additions and
their empirical verification at the call sites. Flagging for the orchestrator in case
§6(e)'s pinned text should be corrected at the design-note level for future builders who
might copy the literal (buggy) command instead of reading the surrounding prose.
