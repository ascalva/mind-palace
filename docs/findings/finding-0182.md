---
type: finding
id: finding-0182
status: routed
created: 2026-07-25
updated: 2026-07-26
links:
  - .claude/skills/delegate/SKILL.md                   # the skill that should carry this
  - docs/build-plans/bp-103/journal.md                 # where it was caught
  - docs/design-notes/agent-workflow.md                # the delegation contract
ftype: spec-defect
origin_plan: orchestrator
route: orchestrator
resolution: routed — neither half landed; the rule lives only in user-level memory, which does not reach a spawned worktree agent
---

# Worktree agents branch from `origin/main`, so an unpushed wave is invisible to them — and the failure is silent

> **Triage 2026-07-26 (session-52) — neither half landed, and the gap is sharper than filed.**
> `.claude/skills/delegate/SKILL.md` contains **no** push-before-spawn or base-verification guidance
> (its only "push" hit, `:162`, is about CI after push; last touched `f0bf7f6`, predating this
> finding), `docs/design-notes/agent-workflow.md` has **zero** occurrences of "wave", "merge-base",
> "origin/main" or "baseRef", and no hook asserts a worker's base.
> **⚑ The rule exists only in the orchestrator's user-level memory — which is not a repo artifact and
> does not reach a spawned worktree agent at all.** Practice is being followed ad hoc
> (`bp-108/journal.md:13` records the expected base), which is exactly the convention-not-enforcement
> shape the project rejects.
> **Land the cheap half now:** one paragraph in the delegate skill beside the pre-flight budget gate —
> `git push` immediately before spawning, state the expected base SHA in the spawn prompt, and have
> the worker assert `git merge-base --is-ancestor HEAD origin/main` + fast-forward at start. The
> `dn-agent-workflow` half is owner-gated and should ride finding-0191's amendment.

## What

Caught by the **bp-103 builder**, self-reported (2026-07-25, session-45):

> *"the worktree was based at `cb6f1fa`, **behind** the bp-100/101/102 seals — `vectorstore.py` had
> no `_sql_str` and `finding-0176.md` did not exist. `HEAD` was a strict ancestor of `main`, so I
> fast-forwarded (`cb6f1fa..ed72554`) before reading anything. Worth checking at spawn time for
> future worktrees."*

Agent worktrees are created from **`origin/<default-branch>`**, not from local HEAD (the
`worktree.baseRef: fresh` default). The orchestrator had merged and sealed the three-builder wave
locally but **pushed after spawning bp-103**. So the worker came up on a tree missing:

- `_sql_str` in `core/stores/vectorstore.py` — the helper its plan's §2 DRY audit told it to reuse;
- `docs/findings/finding-0176.md` — **its own warrant**, named in its §2 context manifest.

## Why it matters

**The failure mode is not an error — it is a wrong answer delivered confidently.** The worker reads
a real file at a real path and receives an *older* truth. Nothing raises. Every downstream inference
is then built on it, and the plan's §6 "interfaces pinned inline" — the mechanism that exists
specifically to stop drift — is exactly what goes stale.

The blast radius is a whole delegated build. bp-103 cost **175k tokens**; a wave costs ~520k. This
one survived because the builder independently checked its ancestry and fast-forwarded *before*
reading its manifest. **That was builder competence, not a property of the system** — and the
delegate skill's own guidance nowhere mentions it. A worker that read first and reasoned later would
have produced plausible, well-tested, wrong work against a base that no longer exists.

It is also self-similar to this session's other defects: an unstated premise (here, "the worktree
sees what I see") that nothing checks. See the reconciliation-audit 2026-07-25 capsule — *you cannot
catch an inconsistency without first having made a consistency claim.*

## The fix

Two halves, cheap:

1. **Process (immediate):** `git push` immediately *before* spawning any worktree agent, and **state
   the expected base commit in the spawn prompt** so the worker verifies rather than assumes. Belongs
   in the **delegate** skill beside the pre-flight budget gate — same shape, same reason.
2. **Structural (preferred, per the standing rule that a property is real only when something proves
   it):** have the worker assert its base at start. A one-line check — `git merge-base --is-ancestor
   HEAD origin/main` plus a fast-forward when true — converts a silent staleness into a loud,
   self-healing one. Better still, the spawn could pass the expected SHA and the worker could refuse
   to proceed on a mismatch.

## Re-entry condition

Not blocking: bp-103 self-corrected and merged clean (`fe32b59`). **bp-104's scribe was checked and
is on a current base.** Re-entry: fold into the workflow-taxonomy design pass, which already owns
`dn-agent-workflow` amendments — or land the delegate-skill note sooner, since it costs one paragraph
and prevents a five-figure-token loss.

## Routing

`design` → orchestrator. It amends the delegation contract (skill + `dn-agent-workflow`), not any
builder's code.
