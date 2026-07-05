---
type: finding
id: finding-0001
status: resolved
created: 2026-07-05
updated: 2026-07-05
links:
  - CLAUDE.md
  - CONSTITUTION.md
  - docs/design-notes/agent-workflow.md
  - docs/inbox/owner-questions.md
  - docs/build-plans/bp-001/plan.md
ftype: question
origin_plan: bp-000
route: orchestrator
resolution: "oq-0001 answered: re-home the safety-critical non-negotiables digest only (not the other dropped items). Ratified as amendment A2 (warrant: this finding) — agent-workflow.md §5 now exempts the domain bright-line digest from the constitution thinness rule. bp-001 landed the 12-item digest inline in CLAUDE.md's always-loaded body (grep-verified by docs/build-plans/bp-001/acceptance/run.sh). The repo map / current-phase marker / live-verify directive stay pointer-only per §5 (operational context, not guardrails). Question closed."
---

# CLAUDE.md replaced the domain digest with a domain pointer — re-home any of it?

## What
BP-000 §12 delivers `CLAUDE.md` as the persona-neutral workflow constitution
(≤ 1 page, §5). The pre-BP-000 `CLAUDE.md` was a different document — the
mind-palace *operating rules* — carrying, on the auto-loaded surface: a 12-item
non-negotiables digest, the repo map, a "current phase" marker, the
build-session-budget guidance, and the live-verification directive. The new file
keeps only a **pointer** to the domain layer (`CONSTITUTION.md` / `BUILD-SPEC.md` /
`CONVENTIONS.md`). Nothing was lost from the repo — the non-negotiables live in
`BUILD-SPEC §3` and `CONSTITUTION.md`, and the old file is in git history — but the
*auto-loaded digest* is gone.

## Why it matters
This is a `direction` concern, so it routes to the owner (§5). The design note is
explicit that the constitution is persona-neutral and lean ("every constitution
token is paid on every turn"), which argues for the pointer-only form. But the
owner may want a subset (e.g. the four hardest non-negotiables) resident every
turn rather than one indirection away. That is a values call, not a mechanical one.

## Re-entry condition
Owner answers `oq-0001` in `docs/inbox/owner-questions.md`; or a later session
files a `direction` finding reporting that a dropped item caused a real miss.
Until then the default holds: pointer-only.

## Routing
`direction` → `route: orchestrator`; batched to `owner-questions.md` as `oq-0001`
with `default_if_unanswered: pointer-only`. Not blocking — BP-000 proceeds.

## Resolution — resolved (2026-07-05, via bp-001)
The owner did not take the default. `oq-0001` is answered: re-home the
**safety-critical non-negotiables digest** — and only that. The values call landed
as **amendment A2** (warrant: this finding), ratified into `agent-workflow.md` §5:
the domain bright-line digest is the one category exempt from the constitution's
thinness rule, because a guardrail that is not in context at the moment it is
relevant is not a guardrail. `bp-001` re-homed the 12-item digest into CLAUDE.md's
always-loaded body (recovered from the pre-BP-000 CLAUDE.md at git `0b21de6^`,
cross-checked against `CONSTITUTION §II–III`; grep-verified by the bp-001 harness).

The other items the pointer-swap dropped — repo map, current-phase marker,
live-verify directive — are operational context, not guardrails; they stay
pointer-only per §5 and remain authoritative in `BUILD-SPEC.md` / `CONVENTIONS.md` /
git history. This is a `question` closed by an answer, not a defect fix, so it
resolves rather than promotes (A2's design change was the owner's, at the gate).
Status → `resolved`.
