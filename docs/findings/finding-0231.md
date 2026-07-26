---
type: finding
id: finding-0231
status: open
created: 2026-07-26
updated: 2026-07-26
links:
  - docs/findings/finding-0226.md      # the orchestrator's — the live dream path refused at 29.7 GB
  - docs/findings/finding-0230.md      # the builder's — filed as 0226, renumbered at merge
  - .claude/skills/finding/SKILL.md    # where id allocation is (not) specified
  - .claude/skills/delegate/SKILL.md   # worktree mechanics — disjoint write_scope, but not disjoint ids
  - docs/build-plans/bp-110/journal.md # six references rewritten by the renumber
ftype: spec-defect
origin_plan: orchestrator
route: orchestrator
resolution: null
---

# Two isolated worktrees allocated the SAME finding id on the same day. Nothing prevented it, and
# only an add/add merge conflict would have caught it — after both files were written.

## What

On 2026-07-26 the orchestrator filed `finding-0226` on `main` (the live dream path refused at
29.7 GB) while a delegated builder concurrently filed a **different** `finding-0226` inside bp-110's
worktree (V5's throughput-vs-liveness measurement). Neither author was at fault and neither could
have seen the other: worktrees branch from `origin/main` and do not observe commits landing on it.

Both had allocated correctly by the only method the repo offers — scan `docs/findings/`, take the
highest id, add one. That method is **correct in a single tree and racy in every other case**, and
this wave runs delegated worktrees routinely (14+ exist today; five ran in parallel two days ago).

⚑ **The collision was caught by luck of mechanism, not by design.** `git merge` reports an add/add
conflict for two new files at the same path, so this instance surfaced loudly at merge time and was
resolved by renumbering to `finding-0230`. But that safety net is **narrower than the failure**:

- It only fires when both files land at the *same path*. Two builders filing `0227` and `0228` in
  the opposite order, or a finding renumbered by one merge and re-collided by the next, produce **no
  conflict at all** — just two findings quietly swapping identity.
- It only fires **at merge**. Both authors had already written, cross-referenced, and *committed*
  their ids. Repairing it meant a rename, a front-matter edit, six journal-reference rewrites, and a
  commit-message provenance defect that **cannot be repaired** (below).

## Why it matters

**1. The commit-message damage is unrepairable.** bp-110's commit `e7a9324` carries the subject
*"Item 1 — V1/V2/V5 measured; no STOP fires; finding-0226"*. After the renumber that string points
at the orchestrator's finding rather than the builder's. It is **not amendable** — the code sensor
ingests commit bodies at commit time (the same property that made the `-m "…"`/backtick corruption
in `7ab5187` and `243fc4d` permanent), so the corpus now holds a commit that cites the wrong
finding. The correction of record lives in `finding-0230`'s banner and in bp-110's merge commit.

**2. Findings are the ONLY channel from build back to design** (CLAUDE.md, the artifact chain). An
id is not decoration on that channel; it is the address a design note's warrant, a plan's `links:`,
and a supersession's three-place record all point at. A silently swapped id mis-addresses a warrant,
and unlike a broken link it **still resolves** — to the wrong document.

**3. It scales with exactly the thing the repo is trying to do more of.** The delegate skill's whole
value is parallel builders in disjoint worktrees, and `parallelizable_with` asserts disjoint
**`write_scope`**. It says nothing about the id space, because `docs/findings/**` is *deliberately*
writable by every builder at once — the one shared, unpartitioned namespace in a system whose entire
concurrency story is partitioning. ⚑ The more the wave parallelises, the more likely this gets.

## Candidate resolutions (a ruling, not a builder's)

- **(a) Allocate from the branch name / agent id.** Each worktree gets a reserved block (e.g. the
  orchestrator takes `xxx0–xxx4`, a builder's block is derived from its branch). Zero coordination,
  no shared state, and collision becomes structurally impossible rather than merely unlikely.
  Cost: ids stop being dense and monotonic, which some readers use as a rough chronology.
- **(b) Make the id non-semantic — a content hash or ULID.** Collision-free by construction and
  ordering-free. Cost: `finding-01J8XQ…` is unreadable in prose, and this repo's documents *cite
  findings conversationally* constantly. Probably disqualifying on those grounds alone.
- **(c) Keep sequential ids, add a pre-hoc guard.** A hook on finding creation that refuses an id
  already present on `origin/main`, plus a merge-time check for id/filename disagreement. Cheapest
  to build and preserves readability, but it is a *narrowing* of the race, not an elimination —
  two worktrees created between the same two fetches still collide.
- **(d) Accept and detect.** Add a ratchet test asserting every `docs/findings/*.md` has `id:`
  matching its filename and that ids are unique. Does not prevent the collision but makes the
  *silent* variant impossible, which is the dangerous one. ⚑ Cheap enough that it is worth doing
  **regardless** of which of (a)–(c) is chosen.

⚑ (d) + (a) is the recommendation: (d) closes the silent failure immediately and is a single test;
(a) closes the loud one without giving up readable ids.

## Re-entry condition

Nothing is parked and no build is blocked — bp-110 merged cleanly after the renumber, and both
findings are intact and distinct on `main` (`0226` orchestrator, `0230` builder).

Re-entry is the next `/triage` or any plan that touches `.claude/skills/finding/SKILL.md`: the
allocation rule is currently **unwritten**, which is why two careful authors both got it wrong. It
should be stated wherever it lands, because the current rule exists only as a habit.

## Routing

`spec-defect` → **orchestrator**. It is a defect in the artifact chain's addressing scheme, not in
any plan's code, and (d) is buildable immediately by anyone while (a)–(c) need a ruling.
