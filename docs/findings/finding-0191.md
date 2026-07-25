---
type: finding
id: finding-0191
status: open
created: 2026-07-25
updated: 2026-07-25
links:
  - docs/audits/ops-wave-2026-07-25.md
  - ops/lifecycle/launcher.py
  - tests/integration/test_lifecycle.py
  - docs/findings/finding-0177.md
  - .claude/hooks/scope-guard.sh
ftype: spec-defect
origin_plan: orchestrator
route: orchestrator
resolution: null
---

# `write_scope` is not a partition of the wave diff — ungoverned seam code carried both serious findings

## What
The wave's five `write_scope` blocks covered every file EXCEPT the two that mattered:
`tests/integration/test_lifecycle.py` (bp-102's scope is `tests/unit/test_lifecycle*.py`)
and the `be225fd` hunk in `ops/lifecycle/launcher.py` (written three commits AFTER bp-102
sealed). ~35 ungoverned lines contained both serious findings of the audit.

`be225fd` exists BECAUSE the workflow worked: bp-101 hit its scope boundary, refused to
route around it, and filed finding-0177 with the exact patch. The failure is what happened
next — a finding whose resolution is a code change was discharged by an orchestrator
commit instead of re-entering the artifact chain.

## Why it matters
The chain says findings return through the same gate brainstorms do; a hand-off finding
carrying a code patch was allowed to skip it. Two proposed mechanisms:

MECHANICAL (detectable by arithmetic, no judgement): diff `wave_base..HEAD`; subtract every
plan's `write_scope`, `docs/findings/**`, and the orchestrator's declared files. Any `*.py`
in the remainder BLOCKS the seal until brought under a plan or waived on the record.
`scope-guard` already knows every plan's scope — this reads the same data at WAVE level
instead of session level, and is the missing pre-hoc counterpart to the `journal-gate`
diff audit. Under that gate this wave stops on exactly the two files.

WORKFLOW (preferred): the INTEGRATOR PLAN. A wave that generates hand-off findings mints
one final `bp-N` whose `write_scope` is the seam files and whose §7 carries an acceptance
criterion and named falsifier per hand-off. bp-101->bp-102's hand-off was known at
graduation. Minimum alternative: hand-offs are absorbed by the RECEIVING plan before it
seals.

The rule that generalizes: the last commit before a seal must never be the first commit of
a behaviour.
