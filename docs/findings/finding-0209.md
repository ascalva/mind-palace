---
type: finding
id: finding-0209
status: routed
created: 2026-07-26
updated: 2026-07-26
links:
  - CLAUDE.md                                   # §Routing — the rule that creates this lane
  - .claude/skills/finding/SKILL.md             # the routing taxonomy
  - .claude/commands/triage.md                  # step 1: "note it and leave for the owning plan's session"
  - docs/findings/finding-0193.md               # the ftype vocabularies that make routing undecidable
  - docs/DESKCHECK-QUEUE.md                     # the third inbox — the precedent for a *raised* backlog
ftype: spec-defect
origin_plan: orchestrator                       # surfaced by the /triage session-52 backlog sweep
route: orchestrator
resolution: null
---

# The builder-routed finding lane has no bookkeeping: 23 of 23 were mis-stated — 13 orphaned, 10 stale-open

## What

`CLAUDE.md` §Routing sends findings typed `codebase | spec-fidelity` to *the builder*, and the
`/triage` skill instructs the orchestrator to "note it and leave for the owning plan's session. Do
not resolve it here." That is correct as a separation of concerns — and it is the **only** lane in the
artifact chain with **no mechanism that ever closes it**. Orchestrator-routed findings get swept every
`/triage`; owner-routed findings get batched into `owner-questions.md` and answered; builder-routed
findings get *noted*, forever.

This sweep (session-52, the first `/triage` in four sessions) re-verified **all 23** open
builder-routed findings against the tree. **Every single one was mis-stated.** Two disjoint failure
modes, and both are the same missing mechanism:

**A — 13 ORPHANS: still live, and no plan will ever pick them up.** A grep for the finding id across
every `docs/build-plans/*/plan.md` and `journal.md` returns nothing but the originating plan, which is
already `complete`. There is no session in the future that will see them.

| finding | the live symptom, re-verified | why orphaned |
|---|---|---|
| 0073 | `cloud/fetcher/sources.py:201-203` still hardcodes arXiv `full_text: None` | follow-up never graduated |
| 0076 | `catalog.py:64-72` still migrates on open; `mint_ids.py:141` still claims "mutates no store" | unclaimed, incl. by bp-034 |
| 0106 | `bin/mind-palace:56` routes `deploy` but **not** `up`/`down`/`restart` | partially fixed, remainder unowned |
| 0107 | `launcher.py:1219` builds `OpsView.over(...)` with no `drift=`, so status prints `None` | bp-102 fixed the sibling, not this |
| 0130 | no `SWEEP_KIND`/`sweep_handler` in `scheduler/cron.py`; `run_sweep` caller-only | bp-081/082 say the wiring plan is unminted |
| 0179 | `StoreStats` still `vector_rows`-only; `read_queue_stats` still raw SQL outside `JobQueue` | no successor to bp-102 |
| 0189 | `test_core_self_containment.py:119-143` has no `<= N` bound | **zero** plan references — and it is the ratchet guarding NN-1 |
| 0194 | four code sites cite the wrong finding ids (0174↔0178, 0178↔0179) | zero plan references |
| 0195 | `_embedder_state` still calls `ps()` with the 120 s default timeout | bp-105 explicitly deferred it, no plan followed |
| 0197 | `launcher.py:721` bare `sweep_orphans` before signal handlers, inside the unclean-exit `try` | bp-105 explicitly deferred it |
| 0202 | no `__pycache__`/`PYTHONDONTWRITEBYTECODE` guard in any skill — stale-bytecode drills still possible | finding's own resolution asks the orchestrator to decide; nobody did |
| 0203 | `bp-110/plan.md:237` still has a bare `§2.3` inside a docstring | bp-110 is `ready` but does not cite 0203 |
| 0208 | `scripts/board.py:123,142,150` parse `audit_refs` and nothing reads it | folds into "AP7", which is a roadmap bullet, not a minted plan |

**B — 10 STALE-OPEN: fixed weeks ago, still reading `open`.** The fix landed, the plan sealed, and
nobody flipped the finding — so the backlog count has been overstating live defects. Closed in this
sweep with cited evidence: **0046** (`tests/e2e/conftest.py:31-64` autouse `flock`, bp-023),
**0059** (bp-020 re-grounded), **0064** (`test_interpreter_versions.py:65-68` sha matches the tree;
bp-026 then bp-094), **0108** (bp-068 in-plan + `router.py:43-44` `_PINNED_KINDS`), **0170**
(`queue.py:232-271` coalescing, bp-101), **0172** (`launcher.py:1116-1300` rates/liveness, bp-102),
**0173** (`queue.py:350-394` + `launcher.py:717-721`, bp-101/`be225fd`), **0176**
(`typedshims/lancedb.py:54-97` + `vectorstore.py:221-236`, bp-103), **0177**
(`launcher.py:83-89,721`, `be225fd`), **0201** (self-resolved in bp-108).

## Why it matters

Three separate harms, in increasing order:

1. **The backlog lies in both directions at once.** 10 phantom defects inflate it; 13 real ones are
   invisible because nothing raises them. Any judgement made off the count — "how much debt do we
   carry", a wave's sizing, a deskcheck's readiness — was made on a number that was wrong by 23.
2. **⚑ One orphan is load-bearing for a non-negotiable.** finding-0189 is the missing monotonicity
   pin on `test_core_self_containment.py`, the ratchet that finding-0185 shows is the *conditional*
   on which non-negotiable #1's static tier rests. It regressed 19→20 undetected (finding-0103), it
   has **zero** plan references, and the green gate deselects it. A safety-discharge ratchet with no
   owner and no alarm is exactly the "built-but-unvalidated" shape the project keeps rediscovering.
3. **It is a convention where the project demands a mechanism.** The standing rule is that a property
   is real only when a test or ratchet proves it. "The builder will pick it up" is proved by nothing;
   the deskcheck queue exists precisely because the same reasoning failed for delivery, and the fix
   there was a *derived, raised* inbox, not a habit.

Note this compounds with finding-0193: because the two `ftype` vocabularies are disjoint and nothing
validates them, "is this finding builder-routed?" is itself undecidable — so the lane cannot even be
enumerated reliably by tooling today.

## Re-entry condition

The lane gets a mechanism, in the same shape that worked for deskchecks — **derived and raised, never
remembered**:

- a **derived orphan register**: for each open finding whose `route: builder`, does any
  `proposed | ready | in-progress` plan reference it? If not, it is an orphan. `scripts/board.py`
  already parses plans and findings and already emits two derived views, so this is an additive
  reader, not a new subsystem — and it would consume the `audit_refs` field that finding-0208 shows
  is parsed and thrown away.
- **`/triage` surfaces the orphan count** beside findings, owner questions, and deskchecks owed.
- optionally, at graduation: a wave that touches a file named by an orphan adopts it or states why
  not.

Closes when the orphan register exists and reads zero, or when each of the 13 above is either adopted
by a plan or explicitly retired.

## Routing

`spec-defect` → orchestrator. It is a defect in the artifact chain itself (the thing this
orchestrator is the single writer of), not in any plan's code. The remedy is tooling plus one
`/triage` step, so it needs no owner ruling — but the 13-orphan list should be adopted deliberately,
and finding-0189 should be sequenced **before** any further core-adjacent build.
