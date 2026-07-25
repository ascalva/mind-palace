# Supervision and liveness — the OS layer of Ouroboros

Brainstorms on the general liveness/supervision architecture: how the system knows its own runs are
healthy, bounds them, and keeps supervising while they execute. Warrant: finding-0188 (bp-105
shipped a *lane-specific* wedge detector and named its own ceiling), finding-0178 (there is no job
timeout at all), finding-0171 / oq-0035 (the unbounded drain). Feeds **NEW NOTE 1 — the ops design
note** (`design-pass-routing.md:57-64`), which already lists *liveness* as a Tier-2 macro axis.

## 2026-07-25 — the general probe, and why one seam blocks all of it

```capsule
topic: supervision-and-liveness
date: 2026-07-25 (session-47, immediately after bp-105 shipped)

warrant (owner, verbatim): "the general liveness probe, the is the OS side of the system, it
manages state, manages runs, manages memory, manages that the system runs as expected, and the
system's demands will only increase as we keep stacking features, density, runs, etc, so we have
to get this right"

--- what bp-105 actually bought, and its ceiling (stated by the build itself) ---

bp-105 made `status` able to separate a healthy backfill from a wedged one, by asking whether the
vector store was written AFTER the running job started. Threshold-free, 0.80 ms, verified on the
real incident (orphan 300246: 13h51m elapsed, store last written 13h53m ago ⇒ landed nothing).

It is a POINT SOLUTION and the build said so: it senses the EMBEDDING lane, via ONE side channel.
A long `dream` / `curate` / `integrate` job legitimately never touches the vector store and reads
as not-progressing.

⚑ EXPLICIT ANTI-GOAL: do NOT "generalize" bp-105 by adding a per-lane mtime probe for each store.
That is N ad-hoc detectors, each with its own falsifier and its own rot. The store-clock is right
for its lane and does not deserve to be a pattern.

--- the taxonomy: four failure modes, four different mechanisms ---

  1. GONE       — the process is dead, the ledger says RUNNING.
                  Mechanism: pid liveness (+ identity). ✅ HAVE IT — finding-0172 (bp-102),
                  identity-checked in bp-105 (`_supervisor_alive`, D1/D2).
  2. STUCK-IN-LANE — job alive, producing nothing observable in its own lane.
                  Mechanism: an out-of-band side channel. ⚠️ HAVE IT FOR EMBEDDING ONLY (bp-105).
  3. SLOW       — genuinely progressing, too slowly to matter.
                  Mechanism: a rate AND an expectation to compare it against. ❌ DON'T HAVE.
  4. HUNG       — the thread is wedged in a syscall / C-level call and has stopped cooperating.
                  Mechanism: external observation + the POWER TO ACT. ❌ DON'T HAVE, and cannot
                  have without the structural change below.

⚑ THE TRAP IN THE OBVIOUS ANSWER: "give jobs a heartbeat" detects (3) and NOT (4) — because a
wedge IS a handler that stopped cooperating. A cooperative signal cannot report its own absence of
cooperation. This is why the answer is not a progress protocol on its own.

--- ⚑⚑ THE STRUCTURAL FINDING: the cancellation seam and the observability seam are ONE SEAM ---

`Supervisor.tick` calls `handler(job)` synchronously and unbounded (`scheduler/supervisor.py:87`).
Two consequences that look unrelated and are not:

  - You cannot enforce a budget from OUTSIDE a synchronous in-process call. (oq-0035 option (b):
    "needs a cancellation seam in the handlers that does not exist today.")
  - You cannot observe progress from a BLOCKED loop. `Launcher._serve`'s health tick, snapshot
    tick and housekeeping tick all stop for the job's duration.

Same cause: **the handler owns the supervisor's thread.** One change unblocks both. Everything
else in this space is downstream of it.

AND — the part that gets worse with density, which is the owner's actual argument: the blocked loop
does not merely stop MONITORING. It stops CHILD RESTARTS, WATCHER HEALTH and HOUSEKEEPING. As lanes
multiply, P(something is always running) → 1, so the supervisor's supervisory functions → never
running. That is an AVAILABILITY property degrading with scale, not a diagnostics nicety.

--- ⚑⚑ THE REFRAMING: oq-0035's stated crux may be an artifact, not a real trade ---

oq-0035 states the crux as: *"whether an interrupted store write is acceptable to guarantee
availability. That trades data integrity against a shutdown guarantee."*

That trade exists ONLY because a handler today does COMPUTE **and** WRITE on the same thread
(`code_backfill_handler` → `sync.backfill` → `_embed_and_land` → store write; the docstring even
says "Store writes stay on the caller (the supervisor handler), single-writer kept").

Split them — **the handler computes a batch and RETURNS it; the supervisor lands it** — and:
  - you never interrupt a write. You interrupt a COMPUTATION and land nothing.
  - the single-writer invariant is PRESERVED, not weakened — it gets stronger, because landing
    becomes a short atomic step the supervisor owns rather than an hours-long span it delegates.
  - the interruptible region is exactly the region where interruption is free.

⚑ And this is the shape the constitution already mandates elsewhere: non-negotiable #4, *"Executed
code is powerless… Returns data, never actions"*, and #3, *"the model advises; code acts."* The
supervisor would finally be supervisory. Fourth arrival of the same principle in this system
(cf. design-pass-routing's "append-only substrate + derived projection" note).

Memory stays bounded by BATCHING, and the lanes are content-addressed/idempotent (`(path, blob_sha)`
keyed), so an interrupted batch costs a re-embed, never corruption.

⚠️ NOT YET VERIFIED, and it must be before this is asserted in a note: whether ALL handlers can be
split this way. `code_sync`/`code_backfill` clearly can. `dream`, `curate`, `integrate`,
`vault_sync`, `chat_sync` are UNSURVEYED. If some handler is irreducibly write-interleaved, the
split is partial and the fail-safe (a) carries more weight. **A handler-shape survey is the first
investigation the ops note owes.**

--- what this implies for the memory ceiling (non-negotiable #8) ---

If handlers move off-thread or out-of-process, model-residency accounting changes. finding-0174
already says the ceiling IGNORES the embedder. So NEW NOTE 1 (ops) and NEW NOTE 2 (local-model-
runtime) share a boundary here: "is the embedder a third process or an unaccounted ghost" is the
same question from two directions. Flag the seam; do not resolve it in one note without the other.

--- the recommendation on oq-0035 (the gate) ---

`design-pass-routing.md:140` already says: rule oq-0035, "without it the ops note carries a parked
decision in a load-bearing section." bp-105 + this session add evidence oq-0035 did not have.

RECOMMEND **(c) both**, with a specific shape:
  - (b) the real fix = the compute/land split, which is what makes budgets ENFORCEABLE at all
    rather than merely configured — and which, per the reframing above, may cost none of the data
    integrity oq-0035 assumed it would.
  - (a) the fail-safe = bounded SIGTERM → N → SIGKILL, behind it. Note that (a) ALONE is close to
    the status quo default, and leaves modes (3) and (4) undetected forever.

The owner's "we have to get this right" is an argument against (a)-alone specifically: an
escalation timer bounds the damage of a wedge without ever making the system able to SEE one.

--- open questions for the note / panel (systems + core) ---

  Q1. Thread, subprocess, or cooperative-batch for the compute side? Each trades differently
      against the memory ceiling, the sealed-core boundary, and crash isolation.
  Q2. Does the ops note absorb finding-0165 (background starvation) and tier scheduling, or do
      those stay scheduler-local? (Already an open question on design-pass-routing:160.)
  Q3. What is the EXPECTATION that makes mode (3) computable? A rate needs a denominator. Is it
      per-kind historical p50 from the queue's own history, or declared per handler?
  Q4. Detection lag as a tracked metric (already in NEW NOTE 1's scope) — does the taxonomy above
      give it four different numbers rather than one?
  Q5. Where does the probe RUN? `status` is operator-pulled. A continuous probe needs a home that
      is not the blocked loop — which is the same seam again, from the monitoring side.
```

open questions:
  - Is "supervision" its own design note, or the load-bearing half of NEW NOTE 1 (the ops note)?
    The routing map assumed one ops note; this capsule is large enough to reopen that.
  - The compute/land split touches `scheduler/`, `core/ingest/`, and the queue schema. That is
    three write scopes and an integrator hand-off — finding-0191 territory. Plan the partition
    BEFORE graduating, not at build time.
