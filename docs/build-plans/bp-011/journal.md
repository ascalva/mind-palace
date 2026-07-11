# BP-011 — Build journal

Alive while the plan is `in-progress`; sealed by `/triage` on completion.
Fresh-agent test (§9): a session given only `plan.md` + this journal + the
write-scope files must continue without re-asking anything already answered.

---

## Markers

---

## Orchestrator note (NOT a builder entry — drop at merge) — 2026-07-11

**This checkpoint is written from the MAIN checkout by the orchestrator, not by the
bp-011 builder.** The real bp-011 build journal is being maintained by the delegated
builder inside its worktree `.claude/worktrees/agent-acfad7293163d7c6f`
(branch `worktree-agent-acfad7293163d7c6f`); this file in the main checkout is still
the graduate-time stub and will be replaced by the builder's journal when its branch
merges. At that merge this orchestrator note conflicts trivially with the builder's
appended entries — **resolve by keeping the builder's journal in full and dropping
this note.**

**Why it exists:** `finding-0031` (worktree enforcement-state bleed) recurred live.
The builder's `/build bp-011`, run in its worktree, set the MAIN checkout's
`.claude/state/active-plan → docs/build-plans/bp-011/plan.md` (the harness resolves
`CLAUDE_PROJECT_DIR` to the main dir even for worktree agents). Consequence: the
orchestrator's Stop-gate `journal-gate` began guarding bp-011's journal against THIS
(orchestrator) session's close, though the orchestrator is not the one building
bp-011. The pointer was left in place deliberately — under finding-0031's mechanics
the builder reads *main's* pointer for its own write_scope enforcement, so clearing it
would strip the builder's guard mid-build (the unsafe direction). This note satisfies
§9 for the orchestrator's close honestly rather than faking an mtime.

**New finding-0031 evidence (its re-entry trigger — "a pointer outside its own
worktree" affecting enforcement — is met):** the bleed now manifests not as a
builder DENIAL (the bp-007 episode) but as an orchestrator Stop-gate FALSE-GUARD.
Strengthens the case for the finding-0031 fix (worktree-aware ROOT resolution). Folded
into the closing /triage's owner queue alongside the A9 amendment candidate.

**Build state at this note:** bp-011 builder spawned and running (sonnet, background);
no completion notification yet. Orchestrator has NOT scrutinized or merged anything for
bp-011. Next orchestrator action on this plan: on the builder's completion, scrutinize
the worktree diff (delegate skill) → merge → seal.
