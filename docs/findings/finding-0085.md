---
type: finding
id: finding-0085
status: open
created: 2026-07-15
updated: 2026-07-15
links:
  - .claude/hooks/scope-guard.sh
  - .claude/skills/graduate/SKILL.md
  - docs/build-plans/bp-042/plan.md
  - docs/build-plans/bp-043/plan.md
  - docs/build-plans/bp-044/plan.md
  - docs/build-plans/bp-045/plan.md
ftype: spec-defect
origin_plan: bp-042
route: orchestrator
resolution: null
---

# Inline comments on `write_scope` globs break scope-guard's path match

## What
`scope-guard.sh` reads a plan's `write_scope` YAML list without stripping inline `#` comments, so a
glob written as `- eval/metrics.py  # absorbed into the registry` is stored as the literal string
`eval/metrics.py  # absorbed into the registry` and never matches the target path `eval/metrics.py`.
During the bp-042 build, editing `eval/metrics.py` (Item 3 absorption) was denied even though the
file *is* in write_scope — the comment defeated the match. Two bp-042 entries carried inline comments
(`eval/metrics.py`, `tests/integrity/test_eval_isolation.py`); the same pattern is present in
bp-043 / bp-044 / bp-045 and will block those builds identically.

This is the **standing fix owed** the resume-brief tracks (findings 0071/0072/0075 + 0084 lineage):
the graduation habit of annotating write_scope globs inline is legible to humans but breaks the
guard. Fixed in bp-042 by moving the rationale to §5 and leaving bare globs; bp-043/044/045 still
need the same one-line cleanup before they build.

## Why it matters
A builder that hits this mid-session is blocked on a file its plan explicitly grants — the exact
false-negative scope-guard must never produce. The workaround (an orchestrator plan-edit mid-build)
is safe here (format-only, intent unchanged) but should be unnecessary: the defect belongs to the
tooling + the graduation habit, not the plan's intent.

## Re-entry condition
Not parked — bp-042 is unblocked (write_scope cleaned in-session). This finding tracks the durable
fix: (a) **the `/graduate` skill** should forbid inline comments on `write_scope` globs (put
rationale in §5), and/or (b) **scope-guard** should strip trailing ` #…` before matching (the
robust fix — humans will keep annotating). Pre-build cleanup owed on bp-043/044/045.

## Routing
`spec-defect` bearing on tooling + a skill → orchestrator. Batches with the standing /graduate-skill
fix already owed (resume-brief "Standing-fix owed"). The scope-guard strip is a small hook edit; the
skill amendment is a one-line rule. Neither blocks the current build (bp-042 proceeds).
