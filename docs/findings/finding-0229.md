---
type: finding
id: finding-0229
status: open
created: 2026-07-26
updated: 2026-07-26
links:
  - docs/design-notes/dn-supervision-and-liveness.md   # §1 objective, §2.2 the seam, §2.5, §2.7
  - docs/build-plans/bp-110/plan.md                    # §1 Objective; §3 Q7; §5 scope; Item 4
  - scheduler/supervisor.py                            # _dispatch_to_worker, model_blocked_tiers
  - ops/lifecycle/launcher.py                          # _serve — the loop, OUT of bp-110's scope
  - docs/findings/finding-0165.md                      # background starvation under a long job
ftype: spec-defect
origin_plan: bp-110
route: orchestrator
resolution: null
---

# bp-110 ships the compute/land split with SYNCHRONOUS dispatch, so it delivers cancellability but
# not yet liveness — and §2.7's concurrency hazard therefore does not arise in this plan, contrary
# to its own §3 Q7

## What

bp-110 §1's objective is: *"A job's long-running compute can be dispatched to a subprocess that
holds no store writer, **so the supervisor stays live**, owns the clocks, and performs every
landing itself."*

What landed does the first and third clauses fully. `Supervisor._dispatch_to_worker` spawns
`python -m scheduler.worker`, the worker holds no store handle (tier 2, tier-4 ratcheted), and
every landing happens on the supervisor's thread (single-writer preserved). Cancellability is real
and tier 3: a wedged worker is SIGTERM→SIGKILL-able by the kernel, and the wall-clock bound is
enforced *during* the read, not merely between frames.

**The middle clause is not yet delivered.** `_dispatch_to_worker` iterates `run_batches(...)` to
completion inside a single `tick()`. The supervisor is therefore blocked on a pipe for the whole
job — it is no longer *computing*, but it is still not *returning*. For a 14-hour `code_backfill`,
`tick()` still does not return for 14 hours, so `ops/lifecycle/launcher.py`'s `_serve` loop — and
with it the health, snapshot and housekeeping ticks — still stalls for the full job. That is §2.2's
complaint verbatim ("the blocked span is not one job but the whole drain"), one layer in.

**The direct consequence, which bp-110's own §3 Q7 gets backwards:** Q7 asserts the §2.7
concurrency hazard "arises with this plan, not before". Under synchronous dispatch it does not
arise at all — there is no instant at which the supervisor can claim a second job while a worker is
out, because `tick()` has not returned. Item 4's single-model-in-flight rule is therefore built,
tested and enforced at the one claim site, but the window it guards is **currently empty**. That is
recorded in `model_blocked_tiers`' docstring rather than left for a reader to discover, and the
guard was shipped anyway on Q7's own reasoning — "shipping the split without it is a regression" —
so that concurrency cannot later be introduced without the guard already in place.

## Why it matters

**Nothing shipped is wrong, and no criterion was parked.** Every Item 3 and Item 4 acceptance
clause is met as written: the parallel-run proof passes, the flag-off path is bit-identical, the
ceiling gate still precedes the spawn, and the model rule refuses correctly when armed. The gap is
between what the plan's §1 *objective sentence* promises and what its *items* actually specify —
no item asks for non-blocking dispatch.

Two things follow that the design layer should decide rather than a builder:

1. **Which plan owns non-blocking dispatch?** It cannot be bp-110: making `tick()` return while a
   worker is out means the supervisor must hold an in-flight worker slot and pump it across ticks,
   and the loop that would drive that is `_serve` in `ops/lifecycle/launcher.py` — **explicitly out
   of bp-110's write_scope** (§5: "bp-108/bp-111/bp-112 own it"). The note's §2.5 interim,
   `run(max_ticks=K)`, is the same file. So the liveness half was structurally unbuildable here,
   and the wave's sequencing should say where it lands. bp-111 (lease) is the natural candidate,
   because §2.6 is explicit that the lease renewer *needs* the unblocked loop — "B depends on
   §2.5; it does not replace it" — and a lease renewed only between whole jobs would decay during
   exactly the long job it exists to observe.
2. **Two of the note's claimed wins are deferred with it, and should not be reported as landed.**
   The batch as the *fairness* unit ("between batches the supervisor may claim other-lane work",
   closing finding-0165's starvation) and the batch landing as the *in-band progress signal*
   (generalizing mode-2 detection past the embedding lane, §2.1/§2.9) both require the supervisor
   to act between batches. Today it lands each batch and immediately blocks for the next, so
   neither is realized. The note's §2.9 detection-lag numbers for STUCK ("one landing-batch
   interval") are correspondingly not yet achieved.

The honest summary for the wave's ledger: **bp-110 delivers the protocol, the capability
restriction, and cancellability. Liveness, fairness and in-band progress arrive with non-blocking
dispatch, in whichever plan owns the serve loop.**

## Re-entry condition

Not blocking; bp-110 is complete against its items. Re-enter at **whichever comes first**:

- **bp-111's or bp-112's graduation** — its plan must state whether it takes non-blocking dispatch,
  and if so, its write_scope needs `ops/lifecycle/launcher.py` alongside `scheduler/supervisor.py`.
  The moment it does, Item 4's rule stops being pre-placed and starts being load-bearing, and
  `model_blocked_tiers`' scope note must be updated in the same commit.
- **bp-113/bp-114 migrating the first real lane.** A long lane (`code_backfill`, `code_sync`,
  `vault_sync` — the uncapped three) moving to `worker_mode = "subprocess"` while dispatch is still
  synchronous would put the daemon's supervisory ticks behind an hours-long pipe read, which is no
  worse than today but is not the improvement the migration is being done for. Worth knowing before
  a deskcheck concludes the split "did not help".

## Routing

`spec-defect` with a **sequencing** consequence → **orchestrator**. Not a builder's call: it
decides which plan's write_scope grows and how the wave is ordered, which is a graduation-time
decision (finding-0191's own lesson — the write_scope partition belongs at graduation, not
build time). No `owner-questions.md` entry is warranted: no ruling is needed, only that the next
graduation reads this before sizing, and that the wave's seal does not report liveness as landed.
