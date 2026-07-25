---
type: finding
id: finding-0182
status: open
created: 2026-07-25
updated: 2026-07-25
links:
  - .claude/skills/delegate/SKILL.md                   # the skill that should carry this
  - docs/build-plans/bp-103/journal.md                 # where it was caught
  - docs/design-notes/agent-workflow.md                # the delegation contract
ftype: spec-defect
origin_plan: orchestrator
route: orchestrator
resolution: null
---

# Worktree agents branch from `origin/main`, so an unpushed wave is invisible to them — and the failure is silent

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
