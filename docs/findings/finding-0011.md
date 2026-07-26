---
type: finding
id: finding-0011
status: routed
created: 2026-07-06
updated: 2026-07-26
links:
  - docs/design-notes/hands-and-the-effector-layer.md
  - docs/PROGRESS.md
  - docs/audits/corpus-state-audit-2026-07.md
  - docs/brainstorms/autopilot-mode.md              # ruling 2, 2026-07-26 — the ε raise
  - docs/brainstorms/public-diffusion-markers.md    # a candidate first stage, read-only/class 1
ftype: spec-defect
origin_plan: orchestrator
route: orchestrator
resolution: null
---

# finding-0011 — "Wired ceiling ε = SENSING" overstates: no effector is wired into any live path

> **Triage 2026-07-08 (/triage):** routed → orchestrator. Corrected in-triage where the orchestrator owns the surface — the project memory note and this triage's PROGRESS checkpoint now state "effectors cataloged but **not** wired; max reachable tier NONE; `[effectors] enabled=false`." The remaining owner-gated design-note (`hands-and-the-effector-layer.md` §10) reword folds into the built-vs-wired umbrella `owner-questions.md` **oq-0007**. Re-entry per §Re-entry condition below.

> **Update 2026-07-26 (/triage, session-52) — OWNER RULING: the ceiling goes up.** The owner ruled
> the effector ceiling UP (`docs/brainstorms/autopilot-mode.md`, 2026-07-26 capsule, ruling 2:
> *"yes, go for it"*) and confirmed in this session that **this finding is to be UPDATED, not
> silently contradicted** — the parked row in that capsule requires the two to move together.
>
> **The factual claim below still HOLDS at this HEAD.** Nothing in the tree has moved: no live entry
> point constructs an effector, `[effectors] enabled = false`, and the maximum reachable tier is
> still **NONE**. The ruling changes the *intent*, not yet the code. Do not read the ruling as a
> wire.
>
> **What the ruling changes is the disposition.** The remedy is no longer only "reword the record":
> - **Interim obligation (still live):** the record must not claim a wire that does not exist. The
>   surviving overclaim is `docs/design-notes/hands-and-the-effector-layer.md:306` — *"the wired
>   ceiling is ε = SENSING"*. `PROGRESS.md` and the project memory were already corrected at the
>   2026-07-08 triage.
> - **Terminal resolution (new):** the wiring itself. This finding closes when a live entry point
>   actually reaches the ruled tier — not when the wording is fixed.
>
> **⚑ The 2026-07-08 park reason is STALE, and this unblocks the interim.** That triage deferred the
> §10 reword as an *"owner-gated design-note"* edit and folded it into `oq-0007`. Amendment **A8**
> (ratified 2026-07-11, three days later) replaced the design-note *location* denylist with a
> *status*-aware guard, and `hands-and-the-effector-layer.md:4` is `status: draft` — therefore
> **agent-writable under a normal `write_scope`**. The reword no longer needs the owner's hand; it
> needs a plan that puts that path in scope.
>
> **Staging — agent recommendation, NOT ruled.** Raise ε **per role / per class, staged**, never in
> one global flip; **class 3 (irreversible / JIT-credential) stays unreachable**, since build
> actions are class 2. Under autopilot ruling 1 a role *is* a catalog subset, so the ceiling becomes
> a property of a role rather than a global constant — which is what makes staging expressible at
> all. A candidate lowest-risk first stage was captured this session: the public-domain probe agent
> (`docs/brainstorms/public-diffusion-markers.md`) — read-only, `edge/`-resident, class 1, touching
> no private data.
>
> **Re-entry condition, restated (supersedes the one below):** (a) *interim* — the `:306` reword
> lands in a plan whose `write_scope` includes that note; (b) *terminal* — the superseding autopilot
> note lands a role-scoped ε raise and this finding is updated in the same change.

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
