---
type: finding
id: finding-0224
status: open
created: 2026-07-26
updated: 2026-07-26
links:
  - docs/build-plans/bp-109/plan.md            # §3 Q5 + §4 vs §9 + §7 Item 2/3 invariants
  - docs/design-notes/dn-supervision-and-liveness.md   # §2.6 (leased RUNNING rows)
  - scheduler/queue.py                          # sweep_orphans — the reclaim predicate, unchanged
  - docs/findings/finding-0173.md               # why claimed_by_run exists; the safety argument
  - docs/findings/finding-0186.md               # a reclaim that races a live claimant
ftype: spec-defect
origin_plan: bp-109
route: orchestrator
resolution: null
---

# bp-109 §4 calls the lease "a second, independent reason a row is **reclaimable**"; §9 forbids
# enforcing it. Built the safe reading — record which one the design meant.

## What

bp-109 says three things about the deadline's relationship to `sweep_orphans`, and they do not all
hold at once:

1. **§4 Reconciliation** — "The deadline is a *second, independent* reason a row is **reclaimable**.
   Extend the argument; do not replace it — finding-0173's reasoning still holds and is what
   protects rows this run actually claimed."
2. **§3 Q5** — lists the sweep's own SELECT as one of the two readers "Item 3 changes".
3. **§9 Non-goals / §7 Item 2 + Item 3 invariants** — "**No enforcement of the deadline.** Stamping
   is here; killing is bp-112"; "the deadline is stamped, never *enforced* here"; "an
   expired-deadline row is *reported* orphaned, never silently deleted".

Read literally, (1) makes a lapsed deadline sufficient for reclamation. But the sweep's population
is defined by the stamp, so the only rows a deadline could *add* are rows carrying
`claimed_by_run == active_run_id` — a live run's own work. Reclaiming those is the double-execution
falsifier this whole mechanism is fenced by (`test_a_job_the_live_run_is_running_is_never_reclaimed`,
finding-0173/0186): a lapsed lease is **not** evidence the holder is dead, because a hung-but-alive
worker has exactly that shape. And reclaiming on a deadline *is* enforcing it, which (3) forbids.

The two readings are also incompatible with (1)'s own second clause: under the widening reading,
run-id ordering would no longer be "what protects rows this run actually claimed" — the deadline
would override it.

**What was built (the reading every invariant supports):** the reclaim predicate is
byte-for-byte unchanged — `state = RUNNING AND (claimed_by_run IS NULL OR claimed_by_run != ?)`.
`claimed_by_run == active_run_id` is an absolute **veto** no deadline overrides. The sweep now reads
every RUNNING row so the same pass can *report* the rows it must not touch: they are returned in a
new `OrphanSweep.lease_expired` tuple and rendered as "reported, NOT reclaimed" (`OrphanSweep.total`
still counts only what MOVED). The two reasons are independently sufficient for a **reader** to
judge a row orphaned — which is where Item 3's acceptance test puts them (`snapshot.py`, with no
sweep having run) — not for a **writer** to act.

Three mutations were planted and each reddens the suite (bp-109 journal, Checkpoint 4), including
MUT-7, which widens the reclaim predicate exactly as reading (1) would: it fails
`test_a_lapsed_deadline_on_this_runs_own_row_is_reported_not_reclaimed`,
`test_a_live_workers_checkpointed_row_is_never_reclaimable`, and
`test_a_lapsed_deadline_does_not_change_the_set_the_sweep_acts_on`.

## Why it matters

The safe reading is now pinned by three tests, so the ambiguity cannot be resolved *by accident*
later — a future builder who reads §4 literally will hit a red suite rather than ship a reclaim that
races a live worker. But the ambiguity itself is still in the plan and in the design note's
neighbourhood, and it is the kind that reads as licence: "the deadline makes the row reclaimable" is
one edit away from double execution on a partially-advanced `code_backfill` cursor.

The design layer should say plainly which of these it means, because the answer determines what
bp-112's escalation is allowed to do:

- **(a) the veto is permanent** — nothing ever reclaims a row its own live run holds; a lapsed lease
  escalates to the *supervisor* (kill the worker, let the worker's death make the row not-live),
  never to the queue. This is what §2.8's "every ops ledger is written by the actor whose failure it
  must record" argues for, and what §9 says today.
- **(b) the veto is conditional** — a lapsed lease plus some *independent* liveness fact (the
  supervisor lock is unheld, the pid is gone, the lease renewal in §2.6 has itself expired) does
  license reclamation. That is defensible, but it is a conjunction, and the second conjunct does not
  exist in the queue's schema today: the queue cannot see whether the holder is alive. Naming it
  makes the missing input explicit rather than assumed.

## Re-entry condition

Not blocking: bp-109 shipped the safe reading with the widening fenced by tests, so no criterion is
parked on this. Re-enter when **bp-112's escalation is graduated** — its plan must state which of
(a)/(b) it implements, and if (b), which liveness fact supplies the second conjunct. If the answer
is (b), `sweep_orphans`'s docstring paragraph added by this plan and the three tests named above are
the exact places that must change, deliberately and together.

## Routing

`spec-fidelity` with a design consequence → **orchestrator**. The builder resolved the immediate
question conservatively (build the reading all the invariants support, fence the other with tests)
and continued; what remains is a design ruling about the veto's permanence, which is not a builder's
to make.
