---
type: finding
id: finding-0189
status: open
created: 2026-07-25
updated: 2026-07-25
links:
  - docs/audits/ops-wave-2026-07-25.md
  - tests/unit/test_core_self_containment.py
  - core/ingest/code_corpus.py
  - docs/findings/finding-0103.md
  - docs/findings/finding-0185.md
ftype: spec-defect
origin_plan: orchestrator
route: builder
resolution: null
---

# The outer self-containment ratchet regressed 19 -> 20 and nothing detected it; monotonicity is prose, not mechanism

## What
Violation counts recomputed at three refs: `97c245c`=19, `bdcd9bc`=19, `a806daa`=20,
`ff36348`=20. The added violation is `core/ingest/code_corpus.py:56 -> ops.code_snapshot`,
introduced by `4acb9f0` (bp-092).

`tests/unit/test_core_self_containment.py::test_core_imports_nothing_outside_core` asserts
only `violations == []`. The "count may only ever decrease" rule exists ONLY as a string
inside the failure banner (line 138). `dn-inner-outer-core` cites "19 -> 0" and "count
only decreases" as law — it is convention, not mechanism.

## Why it matters
A red-by-design ratchet is structurally blind to its own regression: every future
core->sibling import is free. Per finding-0185 this ratchet is the (*) discharge for
non-negotiable #1 (sealed core, zero network egress) — so this is a safety-discharge
regression, not hygiene. The standing `structural-enforcement` rule says a property is
real only when a test PROVES it.

One-line fix: pin `len(violations) <= 20` alongside the existing assertion so the count
is a ratchet in code rather than in prose.
