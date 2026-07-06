---
description: Begin a build plan (must be status ready). Sets the worktree pointer, loads the contract, starts.
argument-hint: <plan-id>
---
Execute build plan `$1` under its declared contract.

**Gate (refuse otherwise).** Read `docs/build-plans/$1/plan.md` front-matter. If
`status` is not `ready`, STOP and report: "build refuses `$1` — status is
`<status>`, not `ready`. The proposed→ready split-approval is an owner-only hand
edit (§10)." Do not proceed.

When ready:
1. Write the worktree pointer: `printf '%s\n' "docs/build-plans/$1/plan.md" >
   .claude/state/active-plan`. From now on `scope-guard` enforces this plan's
   `write_scope` on every Edit/Write.
2. Flip the plan `status: ready → in-progress` (a non-blessing transition;
   allowed). Update `updated:`.
3. Load the contract named by the plan's `contract` field:
   - `builder` → `.claude/agents/builder.md` posture: concern is the codebase and
     spec fidelity; writable surfaces are exactly `write_scope` + the plan's
     `journal.md` + new `docs/findings/`. Raise design questions as findings; do
     not resolve them.
   - `scribe` → `.claude/agents/scribe.md` posture + the **book** skill: concern
     is exposition in `docs/book/**`; accuracy outranks style; gaps exit as
     findings, never as design edits.
4. Read the **§2 Context manifest** in order. Then execute against each **§7** item's
   **Acceptance test**, honoring the **§9 Non-goals** and **§10 Stop-and-raise
   conditions** — these are A4-template body sections, not front-matter keys (A6).
   (`re_entry` remains a front-matter key.)
5. Obey the journal contract (§9) — checkpoint `journal.md` at every semantic
   boundary. Never block on the owner: park a criterion with a re-entry condition
   and continue (§5). Only a `blocker` finding ends the session early, and the
   Stop gate still demands a fresh journal.
