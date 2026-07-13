---
type: finding
id: finding-0051
status: routed # 2026-07-12 — routed to orchestrator at filing; prompt-level fix applied same session
created: 2026-07-12
updated: 2026-07-12
links:
  - docs/findings/finding-0031.md
  - docs/build-plans/bp-014/plan.md
  - docs/inbox/owner-questions.md # oq-0013's answer documents the Bash-mediated workaround
ftype: discovery
origin_plan: orchestrator
route: orchestrator
resolution: null
---

# Pointer bleed recurs builder-side: a worktree builder's Bash write set MAIN's active-plan

## What

At bp-022's spawn (2026-07-12), the builder set BOTH its worktree-local
`.claude/state/active-plan` (correct — its own enforcement armed properly) AND the MAIN
checkout's (`/Users/ascalva/mind-palace/.claude/state/active-plan` ← "bp-022"). The
orchestrator's next root-session Edit (the resume brief) was denied against bp-022's
write_scope. Verified: bp-018's and bp-021's builders did NOT bleed (root stayed empty
through both spawns); this was one builder's act, most plausibly a Bash write through
`$CLAUDE_PROJECT_DIR` — which the harness still resolves to the MAIN project directory
for worktree-isolated agents.

Restored per the documented precedent (finding-0031 / oq-0013's answer): Bash-mediated
`printf '' >` on the root pointer; orchestrator work resumed. No enforcement gap
resulted for the builder — its worktree pointer governs its hooks (bp-014's fix held).

## Why it matters

finding-0031 was FIXED at the HOOK layer (worktree-aware ROOT in `_lib.py` + wrappers,
bp-014) — hooks now resolve the right pointer. But the fix cannot govern what a builder
WRITES via Bash: `$CLAUDE_PROJECT_DIR`-anchored paths still reach main's checkout from
inside a worktree, and Bash writes are audited post-hoc (journal-gate), not denied
pre-hoc. Effect: a builder can silently mis-scope the ORCHESTRATOR's root session (as
here), or in the worst interleaving, another parallel builder whose hooks fall back to
the root pointer. Same root cause as 0031 (`CLAUDE_PROJECT_DIR` = main for worktree
agents), different expression (builder act, not hook resolution) — hence a new finding,
not a re-open.

## Fixes

1. **Prompt-level (applied 2026-07-12, this session):** the delegation-prompt skeleton
   now pins the pointer write to `$PWD/.claude/state/active-plan` and forbids
   `$CLAUDE_PROJECT_DIR`-anchored writes. Carried in the resume brief's spawn skeleton.
2. **Hook-level candidate (for a scoped plan / next triage):** journal-gate (or a
   PostToolUse Bash audit) flags any write from a worktree session that lands under the
   MAIN checkout's `.claude/state/**` — the cross-checkout direction is never legitimate
   for a builder.

## Re-entry condition

The next /triage weighs fix 2 (a small hooks plan or a rider on an existing one). Until
then: the orchestrator re-verifies the root pointer is empty at every unit boundary
(standing rule already in the resume brief) and clears bleeds per the oq-0013 precedent.

## Routing

`discovery` → orchestrator (enforcement/process). Non-blocking; prompt fix live.

## Triage note (third /triage, 2026-07-12) — fix 2 PROMOTED into bp-024

Fix 2 (the hook-level backstop) is promoted to **bp-024** (`proposed`): a `(d)` check in
`cmd_stop_audit` that BLOCKS a worktree session's close when the MAIN checkout's
`active-plan` points to that worktree's own plan — the exact bleed signature here. Fix 1
(the `$PWD`-anchored spawn prompt) remains the pre-hoc primary control; bp-024 is the
post-hoc Stop-gate backstop for the residual Bash path. This finding flips
`routed → promoted` when the owner blesses bp-024 `proposed → ready`.
