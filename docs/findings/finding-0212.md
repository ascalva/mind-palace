---
type: finding
id: finding-0212
status: routed
created: 2026-07-26
updated: 2026-07-26
links:
  - docs/findings/finding-0211.md            # the defect this duty-gap allowed to persist 55 runs
  - .claude/skills/commit/SKILL.md           # the uv-run test gate (local)
  - .claude/skills/checkpoint/SKILL.md       # the seal contract
  - .github/workflows/ci.yml                 # the authoritative gate (oq-0014 D4(i))
ftype: spec-defect
origin_plan: orchestrator
route: orchestrator
resolution: null
---

# A seal attests the LOCAL gate while the AUTHORITATIVE gate is red, and nothing compares them

## What

The pre-seal / pre-push discipline is a **local** gate: ruff · `scripts/check_imports.py` · mypy ·
`ops.type_gate` · pytest. Nothing in it consults **GitHub Actions**, which oq-0014's D4(i) ruling made
the *authoritative* CI host and which the deploy witness attests.

The consequence is now measured. `2add267` (bp-105) turned CI red. bp-105 was then **sealed**, and
bp-106, bp-108 and bp-115 were built and sealed after it — each passing the local gate, because the
failure is Linux-only (finding-0211). **55 consecutive red runs** accumulated, spanning four plan seals
and four docs-only capture commits, and nobody noticed until the owner saw the failure notifications.

So the local gate and the authoritative gate diverged, and the artifact chain recorded the local one as
the truth. No seal, no journal, and no `/triage` step ever asked *"is the remote green?"*

## Why it matters

- **A seal is an attestation.** "All six gate legs verified" (`185f16e`) was true of the local gate and
  false of the authoritative one. That is exactly the overclaim class finding-0011 and finding-0020
  exist to police, arriving through a new door.
- **It silently disables the deploy gate.** Deploy needs an attestable green HEAD, so a red remote
  converts every subsequent seal into work that cannot be delivered — and the block is invisible from
  inside the session that caused it.
- **It defeats the point of having an authoritative host.** The whole reason D4(i) named one canonical
  gate was to stop two hosts disagreeing. Two gates disagreeing *unobserved* is worse than one gate,
  because it manufactures false confidence.
- ⚑ It is the same shape as this sweep's other findings: a rule that was written (GitHub is
  authoritative) and never **wired** to the duty that depends on it.

## Re-entry condition

The cheap, sufficient version — one command, in the two places that already own a gate:

- **at seal / before push:** `gh run list --workflow=ci --limit 1` (or on the pushed sha) and record
  the conclusion in the plan's `cost.actual.notes` or the journal's Follow-through. A seal that cannot
  see a green remote says so explicitly rather than omitting it.
- **at `/triage`:** surface the remote CI conclusion beside findings / owner-questions / deskchecks
  owed, so a red main is a *raised* fact and not a thing someone happens to check.

Stronger option, if the cheap one proves insufficient: a Stop-gate clause that refuses a seal whose
HEAD has a failing authoritative run — but that couples session close to network availability, so it
should not be the first attempt.

Closes when a seal's record carries the authoritative conclusion and `/triage` raises it.

## Routing

`spec-defect` → orchestrator. It is a defect in the seal/triage duties, which the orchestrator is the
single writer of; no owner ruling and no code change is required. The code half is **finding-0211**
(carried by bp-121) — deliberately separate: that one is a probe, this one is a duty.
