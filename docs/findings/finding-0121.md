---
type: finding
id: finding-0121
status: routed
created: 2026-07-20
updated: 2026-07-26
links:
  - .claude/skills/delegate/SKILL.md               # "worktrees are cheap" — cleanup is convention, not enforced
  - .claude/hooks/journal-gate.sh                  # the Stop-gate family a reaper-audit would join
  - .claude/skills/triage/SKILL.md                 # the reflection sweep a reaper could hook
re_entry: null
ftype: discovery
origin_plan: orchestrator
route: orchestrator
resolution: open — no reaper exists; leak re-accumulated to 4.3 GB. Closing act = a `proposed` tooling plan
---

# Delegated-build worktrees leak — 10 stale trees (~7 GB) accumulated with no reaper; workspace hygiene is convention, not enforcement

> **Triage 2026-07-26 (session-52) — still exactly true, and re-accumulated.** No reaper exists
> anywhere: `grep -rEn "worktree (remove|prune|gc)|worktree-gc"` over `scripts/ .claude/` returns
> **zero hits**. `.claude/worktrees/` holds 8 directories totalling **4.3 GB**; `git worktree list`
> registers 7 agent trees, **all 7 branches merged to `main` and clean**; 16 `worktree-agent-*`
> branches exist (8 merged). One directory (`agent-a75921da9dde8c99d`, Jul 22) is **not registered at
> all** — a `git worktree prune` candidate.
> **No owner ruling needed** (the direction "keep our workspace clean" was already given). The
> closing act is a `proposed` tooling plan with this finding as warrant:
> `scripts/palace.py worktree-gc` (remove merged+clean, report unmerged/dirty, never force) + wiring
> (a `/triage` call and/or a journal-gate Stop clause) + the `.venv`-sharing investigation.
> **Interim:** reap the 7 merged trees and prune the unregistered dir — but confirm no sibling agent
> of the current wave is live in one first.

## What
Surfaced by the owner (2026-07-20) mid plane-migration: `.claude/worktrees/` held **10 stale
delegated-build worktrees consuming 7.0 GB** — nine of them fully **merged to main and clean**,
leaked from builds over Jul 16–17. Each carries its own **~640 MB `.venv`** (the bulk of the 7 GB;
per-tree `data/` is small), so the cost is ~640 MB per leaked build.

Grounding: **no automated cleanup exists anywhere** — `grep -rE "worktree (remove|prune)"` over
`scripts/`, `.claude/hooks/`, `.claude/skills/`, `.claude/commands/` returns nothing. The only
reaper is the orchestrator manually running `git worktree remove` after a merge (which THIS session
did for bp-078, but which ~10 prior builds did not).

## Why it matters
- **Silent, unbounded bloat.** The repo had grown to 16 GB, ~7 GB of it dead worktree venvs. It
  grows by ~640 MB every time a delegated build's cleanup is skipped, with nothing surfacing it.
- **It bit a live operation.** The plane migration's §3 (`chgrp -R palace $REPO` + `chmod -R g+w` +
  setgid over the whole tree) would have ground through 7 GB of cruft and stamped the new shared
  `palace` group + setgid onto abandoned trees — ownership/mode sprawl baked into the very step
  meant to make ownership crisp. Cleaning first cut the §3 surface from ~16 GB to ~9.7 GB.
- **Stale `git worktree list` + dangling branches** accumulate (9 `worktree-agent-*` branches were
  removable only after the worktrees were), muddying the ref namespace.

## Root cause — cleanup is a convention with no forcing function
The `Agent` tool's `isolation: "worktree"` auto-removes a worktree **only if it is unchanged**; a
builder that commits (every real build) leaves changes, so the harness keeps it. Post-merge removal
is then the orchestrator's manual step — and a manual step is skipped whenever a session dies before
it, or simply forgets. Nothing sweeps merged worktrees afterward: no gc script, no Stop-gate clause,
no `/triage` sweep. This is the `structural-enforcement` pattern exactly: a property ("the workspace
is clean") that nothing *proves* is a property that drifts. Convention held often enough to stay
invisible until 7 GB had piled up.

## Proposed fix (structural — build the reaper, don't trust the habit)
1. **A reaper** — `scripts/palace.py worktree-gc` (or a small dedicated script): for each
   `.claude/worktrees/agent-*` whose branch is **merged to main AND clean**, `git worktree remove` +
   `git branch -d`; leave unmerged/dirty trees and REPORT them (never force-delete unmerged work —
   e.g. this sweep correctly spared `agent-a1d5f2b78350b8586`, an unmerged superseded-bp-060 tree).
2. **Wire it to run automatically** so it is enforcement, not another convention:
   - `/triage` (the reflection sweep) calls the reaper each reflection — reclaim on every cadence;
   - **and/or** a Stop-gate clause (journal-gate family) that FLAGS stale merged worktrees at an
     orchestrator close, the same shape as clauses (b)/(e): "workspace not clean — N merged worktrees
     unreaped." Caught, not trusted.
3. **Cut the per-tree cost** (secondary): each worktree duplicates a ~640 MB `.venv`. Investigate
   sharing the main venv into worktrees (a `uv` link / `UV_PROJECT_ENVIRONMENT` pointing at the main
   `.venv`, or excluding `.venv` and letting `uv sync` hardlink from cache) so a leaked tree costs
   megabytes, not ~640 MB. (Even with the reaper, cheaper trees mean a missed sweep hurts less.)

## Re-entry condition
Graduate a small tooling plan (the reaper + its wiring, warrant = this finding); flip to `promoted`
when it lands. Interim: the orchestrator's post-merge `git worktree remove` + `git branch -d`
discipline stands (bp-078 did it), but that is the very convention this finding exists to replace.

## Routing
`discovery` / direction → orchestrator. Owner direction already given ("keep our workspace clean",
2026-07-20). Small `ops`/`scripts` build once graduated; the Stop-gate-clause option touches
`.claude/hooks/_lib.py` (the enforcement surface) and would carry its own tests.
