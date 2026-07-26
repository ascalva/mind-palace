---
type: finding
id: finding-0191
status: routed
created: 2026-07-25
updated: 2026-07-26
links:
  - docs/audits/ops-wave-2026-07-25.md
  - ops/lifecycle/launcher.py
  - tests/integration/test_lifecycle.py
  - docs/findings/finding-0177.md
  - .claude/hooks/scope-guard.sh
ftype: spec-defect
origin_plan: orchestrator
route: orchestrator
resolution: routed — PROMOTE: an owner-blessed amendment to ratified dn-agent-workflow; instances 2/3/4 are the evidence package
---

# `write_scope` is not a partition of the wave diff — ungoverned seam code carried both serious findings

> **Triage 2026-07-26 (session-52) — PROMOTION PROPOSED (owner ratifies; agent never edits).** Both
> factual legs check out: bp-102's `write_scope` was `tests/unit/test_lifecycle*.py`, so
> `tests/integration/test_lifecycle.py` was ungoverned, and `be225fd` is the orchestrator-committed
> integration. **The mechanism is only half-adopted and only per-wave:** an integrator plan is
> required by two *ratified* notes (`dn-supervision-and-liveness:551-553`,
> `dn-local-model-runtime:439-444`) and instantiated as bp-110 (`ready`) — but the **general rule is
> absent** from `dn-agent-workflow` (zero "wave" occurrences) and from the delegate skill, and no
> wave-level gate exists in `.claude/hooks/`.
> **⚑ It recurred twice more after filing** — finding-0198 and finding-0204 (*"the THIRD instance"*),
> both discharged by the ad-hoc amended-`write_scope` route now marked a *"REUSABLE PRECEDENT"*
> (`bp-115/plan.md:48`). A fourth in miniature is finding-0181. The specific ungoverned file is now
> governed (bp-109 + bp-111 both list it), so the **instance is closed and the mechanism is not**.
> **Proposed amendment** to **ratified** `docs/design-notes/agent-workflow.md` (owner-blessed, A1–A8
> pattern): *`write_scope` must partition the wave diff — at seal, any `*.py` in `wave_base..HEAD`
> minus every plan's `write_scope`, `docs/findings/**`, and the orchestrator's declared files blocks
> the seal; a wave with known hand-offs mints an integrator plan at graduation; a mid-build hand-off
> is discharged only by an amended `write_scope` on the record, never by an orchestrator commit.*
> Fold finding-0182's `dn-agent-workflow` half into the same amendment, and pair it with a
> wave-level `scope-guard` — a property is real only when something proves it.

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
