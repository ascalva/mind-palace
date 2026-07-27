---
type: finding
id: finding-0257
status: open
created: 2026-07-27
updated: 2026-07-27
links:
  - docs/findings/                          # the flat, monotonically-numbered id space
  - .claude/skills/finding/SKILL.md          # where allocation is described
  - .claude/skills/delegate/SKILL.md         # parallel builders / sub-orchestrators
ftype: design
origin_plan: bp-127
route: orchestrator
resolution: null
---

# Concurrent sessions race the finding id space — four collisions in one day, and the loser is whoever commits second

## What

Finding ids are allocated by reading `docs/findings/` and taking the next integer. That is a
**read-then-write with no reservation**, so any two agents who read before either writes allocate
the *same* id. With one session at a time this never fires. This repo now runs several concurrently
— parallel builders in worktrees, sub-orchestrators owning waves, and independent sessions in the
primary checkout.

**Measured today, 2026-07-27, in a single wave:**

| id | claimant A | claimant B | resolution |
|---|---|---|---|
| `0252` | sub-orchestrator (clause (f) substring defect) | `bp-127` builder in its worktree | builder renumbered to `0254` on instruction |
| `0253` | `bp-127` builder (judge is quote-verified) | another session in the primary checkout (grant-code attempt bound) | **unresolved at merge** |
| `0254` | `bp-127` builder (tool-less agent fabricates) | another session (`touches_stored_data` predicate) | **unresolved at merge** |
| `0255` | `bp-127` builder (F2 mechanically tautological) | another session (`dn-erratum-relation` §5 mis-cite) | **unresolved at merge** |

The first collision was caught only because the sub-orchestrator happened to inspect the builder's
worktree before it sealed. The other three surfaced as a **merge abort** —
*"untracked working tree files would be overwritten by merge"* — which is a lucky failure mode: git
refused rather than silently clobbering three findings that had never been committed.

⚑ **The near-miss is the point.** Had the other session committed first, `git merge` would have
reported a content conflict in three files whose *ids match and whose subjects are unrelated*, and
the natural resolution — take one side — silently destroys a finding. Findings are the **only**
channel from build back to design. A lost one is a lost design input with no trace that it existed.

## Why it matters

The id is not decoration; it is the **join key**. `finding-0248` is cited by plans, journals,
readings rows, commit bodies, and design-note residuals. Two artifacts sharing an id do not merely
collide at the filesystem — every downstream citation becomes ambiguous, and the ambiguity is
undetectable by reading either one.

This is a **structural-enforcement gap**, the class this repo has repeatedly ruled on: *a property
is real only when something proves it.* Uniqueness is currently a property of **timing**, held by
convention, and the convention silently stopped holding the moment concurrency became routine.
Nothing lints it, and nothing could have — the colliding artifacts do not coexist in any one tree
until the merge.

Note also that the resolution rule that actually applied — **first to commit keeps the id** — was
invented at the merge by the agent holding it, not read from anywhere. That is the
rules-live-in-an-agent's-working-memory failure the delegate skill was amended to end.

## What is NOT claimed

- **Not that anyone erred.** Every claimant read the directory correctly and took the next free
  number. The allocator is the defect, not its users.
- **Not that renumbering is expensive.** It is cheap *when caught* — a `git mv` and a front-matter
  edit. The cost is entirely in the not-catching.
- **Not that a lock is the answer.** Several mechanisms are plausible and none is ruled here.
- **Not measured:** whether any historical finding was already lost this way. Four collisions in one
  day is the first time anyone looked; the id space has never been audited for gaps or duplicates.

## Candidate mechanisms — recorded so the next author does not re-derive them, none chosen

1. **Content-addressed or timestamped ids** (`finding-20260727-a3f`) — collision-free by
   construction, but breaks the human-readable monotonic sequence every existing citation uses, and
   the id is the join key, so this is a corpus-wide rename. Almost certainly too expensive.
2. **Per-agent id ranges** — a sub-orchestrator reserves a block before spawning. Cheap, no format
   change, no coordination at write time; wastes ids and needs a place to record the reservation.
3. **A uniqueness ratchet in CI plus a merge-time check** — does not *prevent* the collision, but
   converts it from silent to loud, which is the property that actually matters. Cheapest by far,
   and it composes with any of the others.
4. **Allocate at merge, not at write** — findings are drafted with a placeholder and numbered by the
   merging orchestrator. Correct by construction; adds a step to every merge and breaks in-flight
   cross-references between findings filed in the same session.

`[INFERENCE]` (3) is the right first move regardless of which of the others is eventually chosen: it
is the only one that makes the failure *observable*, and every other option is easier to evaluate
once the collision rate is measured rather than anecdotal.

## Re-entry condition

**Immediate and concrete:** three ids (`0253`, `0254`, `0255`) are live duplicates the moment the
other session commits. `bp-127`'s versions are **merged to main first**, so by the first-to-commit
rule the uncommitted copies renumber. ⚑ **The other session must be told** — it cannot discover this
except by a failed pull, and it did not choose to lose the race.

**Structural:** the next plan holding `.claude/skills/finding/SKILL.md`, or any plan that touches CI
composition, inherits mechanism (3) — a duplicate-id check — as a required item. It should assert on
the **committed corpus**, so it fires at merge, which is the only moment both claimants exist in one
tree.

## Routing

`design` → the orchestrator, because choosing among the four mechanisms is a design ruling, not a
codebase fix. Filed at `bp-127`'s seal by the sub-orchestrator that hit all four collisions while
merging.
