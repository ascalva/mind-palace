---
type: finding
id: finding-0011
status: routed
created: 2026-07-06
updated: 2026-07-08
links:
  - docs/design-notes/hands-and-the-effector-layer.md
  - docs/PROGRESS.md
  - docs/audits/corpus-state-audit-2026-07.md
ftype: spec-defect
origin_plan: orchestrator
route: orchestrator
resolution: null
---

# finding-0011 — "Wired ceiling ε = SENSING" overstates: no effector is wired into any live path

> **Triage 2026-07-08 (/triage):** routed → orchestrator. Corrected in-triage where the orchestrator owns the surface — the project memory note and this triage's PROGRESS checkpoint now state "effectors cataloged but **not** wired; max reachable tier NONE; `[effectors] enabled=false`." The remaining owner-gated design-note (`hands-and-the-effector-layer.md` §10) reword folds into the built-vs-wired umbrella `owner-questions.md` **oq-0007**. Re-entry per §Re-entry condition below.

## What
The tracking record (`docs/PROGRESS.md:1085-1087`), project memory, and
`hands-and-the-effector-layer.md` §10 describe the Track-G effector layer as having
a "WIRED ceiling ε = SENSING" — i.e. the read-only sensing hand is live while the
acting hands are flag-off. In code, **no live entry point imports or calls any
effector module, sensing included**: a grep of `scripts/palace.py`,
`ops/lifecycle/launcher.py` (`build_components`/`build_launcher`),
`core/runtime.py bootstrap`, and `scheduler/` for
`effector|effect_gate|effect_exec|effect_ledger|effect_proposal|effect_catalog|SensingEffector|build_sensing|EffectView|core.sensing`
returns zero hits. `[effectors] enabled = false` (`config/defaults.toml:138`), not
overridden in `config/local.toml`. "ε = SENSING" is only the default constructor
argument of the `EffectView` type (`ops/effects.py:184`); nothing live constructs an
`EffectView`. The maximum effector tier reachable from a live entry point in the
default/live config is **NONE**.

## Why it matters
This is a safety-adjacent posture claim in the tracking record. It reads as "the
read-only sensing hand is live," when in fact the entire hand layer is dormant.
Accurate posture matters for reasoning about the outbound-effect boundary
(Invariants 2/3/4). The direction of the inaccuracy is strictly *safe* (dormant is
safer than wired), so this is a wording/accuracy defect, not a safety hole — but the
tracking record should not claim a wire that does not exist.

## Re-entry condition
Reword `docs/PROGRESS.md`, the memory note, and `hands-and-the-effector-layer.md`
§10 to "sensing is built and safe-to-wire, not wired." Alternatively, the claim
becomes true once a live entry point actually constructs the sensing handoff/effector
with `[effectors] enabled = true` in the live config.

## Routing
`spec-fidelity`/`direction` → orchestrator. Tracking-vs-code accuracy on a
safety-adjacent claim.
