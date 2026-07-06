---
description: Decompose a ratified design note into one-session build plans (status proposed).
argument-hint: <design-note path or slug>
---
Graduate the design note `$1` into build plans. Use the **graduate** skill for
the decomposition rules, session-sizing heuristics, and the
split-at-graduation-never-mid-build discipline.

**Gate (refuse otherwise).** Read the note's front-matter. If `status` is not
`ratified`, STOP and report: "graduate refuses `$1` — status is `<status>`, not
`ratified`. Ratification is an owner-only hand edit (§10)." Do not proceed.

When ratified:
1. Load the graduate skill and decompose the note into session-sized build plans
   against `docs/templates/build-plan.md`. Each plan: `status: proposed`,
   `session_budget: 1`, a least-privilege `write_scope`, an ordered **§2 context
   manifest**, **§7** items each with a runnable **Acceptance test**, and
   **interfaces pinned inline** (§6) — copy signatures/schemas/invariants from the
   note, never reference. (These are A4-template body sections, not front-matter
   keys, A6; `re_entry` stays a front-matter key.)
2. Write each to `docs/build-plans/<id>/plan.md`; create `journal.md` (alive) via
   the same template's journal shape.
3. Cross-link: each plan's `design_ref`/`links` → the note; note the plan ids in
   your summary.
4. Emit `status: proposed` only. **Never** set `ready` — that is the owner's
   split-approval blessing gate (§10); `gate-guard` will deny it, and `/build`
   refuses any plan not `ready`.

Report the plan ids and their write_scopes for the owner's ready-flip review.
