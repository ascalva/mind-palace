---
type: finding
id: finding-0008
status: promoted
created: 2026-07-05
updated: 2026-07-06
links:
  - docs/design-notes/agent-workflow.md   # §3 front-matter schema (line 74) vs A4 template placement
  - docs/templates/build-plan.md            # the ratified A4 template installed by bp-003
  - docs/build-plans/bp-003/plan.md         # the plan that surfaced this while installing A4
ftype: spec-defect
origin_plan: bp-003
route: orchestrator
resolution: "promoted → agent-workflow.md amendment A6 (§3 build-plan schema reconciled to the A4 template: `re_entry` retained as a front-matter key, `objective`/`context_manifest`/`non_goals`/`stop_conditions` are body sections §1/§2/§9/§10). Command-file fix landed by bp-004: build.md/graduate.md/scribe.md now read the four moved fields from the §2/§7/§9/§10 body sections; template restores the `re_entry` front-matter key. Harness: docs/build-plans/bp-004/acceptance/run.sh."
---

# finding-0008 — §3 front-matter schema and the A4 template disagree on field placement

## What

Installing the ratified A4 template (bp-003) surfaced an internal inconsistency in
the ratified record: the §3 build-plan front-matter schema lists three fields as
*front-matter* that the A4 template realizes as *body sections* and drops from
front-matter.

- **§3 prose** — `docs/design-notes/agent-workflow.md:74`: "Build plan adds:
  `objective` (one sentence), … `context_manifest` (ordered read list), …
  `re_entry` (if parked), …" — i.e. `objective`, `context_manifest`, and `re_entry`
  are named as front-matter keys. Reinforced for parked at
  `docs/design-notes/agent-workflow.md:66`: "**Parked** requires a `re_entry`
  field."
- **A4 template** — `docs/templates/build-plan.md` front-matter (the block ll. 1–17)
  carries `type, id, status, design_ref, contract, write_scope, session_budget,
  depends_on, parallelizable_with, created, updated, links, supersedes,
  superseded_by, warrant` — and **no** `objective`, `context_manifest`, or
  `re_entry`. Those three are instead body sections: **§1 Objective**, **§2 Context
  manifest**, and **§11 Parked decisions** (whose table carries the "Re-entry
  condition" column).

Both artifacts are ratified (the note by hand; the template as the owner-provided A4
form installed verbatim by bp-003). The A4 amendment text says only that "§3 gains
the per-item and section fields" (`agent-workflow.md:272`) — it did not restate the
front-matter list, so the older front-matter placement of these three fields was
left standing in the prose while the new template moved them into the body.

**The same drift reaches the command files** (the operational glue, and the more
consequential instance), which still describe these as front-matter keys:

- `.claude/commands/graduate.md:17` — "…ordered `context_manifest`, runnable
  `acceptance`, and **interfaces pinned inline**".
- `.claude/commands/build.md:26-27` — "Read the `context_manifest` in order. Then
  execute against `acceptance`, honoring `non_goals` and `stop_conditions`." On a
  *new-template* plan these live in §2 (Context manifest), §7 (per-item Acceptance
  test), §9 (Non-goals), §10 (Stop-and-raise) — **not** front-matter keys, so a
  builder reading `/build` literally would look for front-matter fields that a
  new-template plan does not carry.
- `.claude/commands/scribe.md:16` — lists `context_manifest` among the plan fields a
  sync plan sets.

(The old-template plans bp-000/bp-001/bp-002 still *use* the front-matter keys — they
were minted against the old template and are historical; they need no change.)

## Why it matters

Mostly legibility, but with one enforcement edge worth the owner's eye:

- **Greppability (Principle 1).** The workflow's first principle is that state is
  greppable in front-matter. `objective` and `context_manifest` moving to the body
  is cosmetic — they were never enforced keys. `re_entry` is the load-bearing one:
  §3 (`:66`) makes "a plan or criterion without a re-entry condition cannot enter
  `parked`" a *state-machine gate*. If a parked **plan**'s re-entry now lives only in
  a §11 body table rather than a front-matter `re_entry:` key, any mechanical check
  of "parked ⇒ has re_entry" must read the body, not `grep` the front-matter. I did
  not find a hook that currently enforces this gate mechanically (the parked gate
  reads as a discipline, not a script), so nothing breaks *today* — but a future
  enforcement of it would need to know where re-entry lives.
- **Operational break on the command glue.** The command-file drift is the sharper
  edge: `/build` (`build.md:26-27`) instructs the builder to read front-matter
  `context_manifest` and execute against front-matter `acceptance`/`non_goals`/
  `stop_conditions`. On any plan minted from the new A4 template those are body
  sections (§2/§7/§9/§10), so the literal instruction points at keys that are not
  there. It has not bitten yet only because every existing plan (bp-000..bp-003) was
  minted against the *old* template; the first new-template plan through `/build`
  would meet it.
- **The record should not contradict itself.** A4 is exactly the amendment that
  elevates "reconcile, never silently diverge" to a template discipline; the record
  installing it should be internally consistent about its own schema — §3 prose, the
  template, and the commands that operate the template should agree.

## Re-entry condition

N/A — not a parked criterion. bp-003 closed all its acceptance criteria; this
finding is a routed observation, not a blocker. (bp-003 does not touch design notes
and cannot resolve this itself.)

## Routing

`spec-defect`, design-level → **orchestrator**. This is a design-note question (amend
§3 prose to match the A4 template's body-section placement, or amend the template to
restore the three keys to front-matter), so it is not the builder's to resolve.
Proposed disposition for owner triage:

- **Default recorded:** treat the A4 template as authoritative on placement (it is
  the later, purpose-built, owner-provided artifact) and reconcile the *descriptions*
  to it — a prose-only amendment of §3's front-matter sentence (that
  `objective`/`context_manifest` are body sections §1/§2 and a parked plan's re-entry
  lives in §11), **plus** an update to the command files (`graduate.md`, `build.md`,
  `scribe.md`) to reference the §2/§7/§9/§10 body sections instead of front-matter
  keys. No template change. The command-file edits are the operational half and want
  their own small build plan (commands are outside bp-003's scope).
- **Alternative:** if a front-matter `re_entry:` key is wanted for a future
  greppable parked-gate, add it back to the template front-matter (keeping §11 as the
  human-readable expansion). This is the only sub-question with a mechanical stake for
  the *template*; `objective`/`context_manifest` are legibility-only. The command-file
  fix is needed either way.

Non-blocking for bp-003 (all its acceptance closed). Batch to `owner-questions.md` at
the next `/triage` if the owner does not rule inline; the command-file reconciliation
graduates into its own plan once the owner rules on placement.
