---
type: track
slug: ops
title: Ops — operating the live system: cost, observability, and the shutdown contract
status: active
warrant: docs/findings/finding-0169.md
audit_refs: []
dod:
  - OPS-1 store cost bounded — `supersede_source` O(path depth), proven by a ratchet, not asserted (bp-100, warrant finding-0169)
  - OPS-2 queue hygiene — enqueue coalescing + orphaned-job reclaim (bp-101, warrant findings 0170/0173)
  - OPS-3 status tells the truth — liveness, failures, and the rate/budget block; command-center TIER 1 (bp-102, warrant finding-0172)
  - OPS-4 the shutdown contract closed — oq-0035 ruled and built (finding-0171); `down` must be able to stop a wedged daemon
  - OPS-5 the command center proper — TIER 2, real-time, macro axes; design note + adversarial panel, then graduate (docs/brainstorms/command-center.md)
  - OPS-6 cost as a checkable property — the performance-ratchet suite generalized beyond one method; scale witnesses (docs/brainstorms/ops-and-optimal-form.md)
  - OPS-7 the local model RUNTIME and model SELECTION — llama.cpp-direct migration, residency owned by palace code, and choosing the model against measured performance limits (owner 2026-07-25; docs/brainstorms/local-model-runtime.md, warrant finding-0174)
  - OPS-8 detection LAG is measured, not asserted — the reconciliation-audit's central model made self-measuring (owner 2026-07-25 "we will need to also measure lag"; substrate blocked on finding-0175)
  - the restart PROVES it — daemon back up, backfill completes to ~1,542 versions, rate observable throughout (owner-visible run, not merely built)
backlog_deskcheck: null
links:
  - docs/brainstorms/command-center.md
  - docs/brainstorms/ops-and-optimal-form.md
  - docs/brainstorms/reconciliation-audit.md
  - docs/brainstorms/local-model-runtime.md
  - docs/findings/finding-0169.md
  - docs/findings/finding-0170.md
  - docs/findings/finding-0171.md
  - docs/findings/finding-0172.md
  - docs/findings/finding-0173.md
  - docs/findings/finding-0174.md
  - docs/findings/finding-0175.md
  - docs/build-plans/bp-100/plan.md
  - docs/build-plans/bp-101/plan.md
  - docs/build-plans/bp-102/plan.md
---
# Track — Ops (operating the live system)

The identity card for the ops track. **Scope:** everything about running Ouroboros as a live system
rather than building it — the **cost** of operations, the **observability** that makes their state
knowable, and the **lifecycle contracts** (shutdown, drain, job budgets) that must hold when
something goes wrong. Members are the artifacts declaring `track: ops`.

**Why this track exists.** It was minted 2026-07-25, warranted by finding-0169, after the first real
performance incident: the bp-099 deploy landed correctly, keep-and-link worked exactly as designed,
and the system still wedged for 90 minutes — because `supersede_source` cost O(total store), the
queue grew unbounded behind it, `down` could not stop it, and `status` reported everything as
healthy throughout. Every one of those is an *operational* property. None belonged to any existing
track, which is precisely why none of them had an owner.

**The organizing thesis** (`docs/brainstorms/ops-and-optimal-form.md`): **cost is not a property of a
function, it is a property of a function in a context.** This codebase has strong discipline about
semantics — types, provenance, the import firewall, attestations, the sealed core — and had none
about cost. An O(n) primitive was promoted into an O(n) loop and no line of code had to be wrong.
This track's job is to give cost and liveness the same structural enforcement that correctness
already has.

**The second thesis** (`docs/brainstorms/reconciliation-audit.md`, 2026-07-25 capsule): **you cannot
catch an inconsistency without first having made a consistency claim.** The refinement cycle closed
in ~2 hours once the problem was noticed — but it did not *start* on its own; the owner noticed
because his laptop fans went quiet. Detection lag was bounded by an accident, not an instrument.
So this track's deliverables are not only fixes: they are the *declared expectations* (scale
witnesses, rate budgets, timeout knobs) that make "operating as expected" a computable predicate.

## Definition of done

A deskcheck evaluates against the `dod` list above. In short: OPS-1..3 land (the three incident
plans), OPS-4 closes the shutdown contract once the owner rules oq-0035, OPS-5 delivers the command
center proper through the normal design gate, OPS-6 generalizes the ratchet from one method to a
suite — and the **restart proves it**: the daemon comes back up, the backfill runs to completion at
~1,542 versions, and its rate is observable the whole way. Per [[deskcheck-discipline]], this track
cannot be deskchecked while it merely *could* work; the completing backfill is the demonstration.

## Relationship to other tracks

- **code-ingest** — bp-100 fixes a store method the code-ingest lane depends on, and the backfill it
  unblocks is part of code-ingest's own definition of done. The two tracks share that milestone;
  they do not merge. Code-ingest owns *what is embedded and retrievable*; ops owns *what it costs
  and whether the run is observable*.
- **fiber-geometry / inner-outer-core** — no overlap today, but OPS-6's "measure the system's own
  access patterns before choosing a representation" will eventually want their instruments.
- **the local model runtime is OPS** (owner ruling 2026-07-25). `docs/brainstorms/local-model-runtime.md`
  had no track coordinate; it is ops-shaped by every criterion here, and the owner extended it:
  **choosing the appropriate model against measured performance limits is itself an ops function**,
  not a one-off configuration choice. That makes residency, the memory accounting (finding-0174), and
  model selection one concern with one owner. The EMBEDDER-choice question
  (`docs/brainstorms/embedding-space-specialization.md`) is downstream of it and is not separately
  owned.
- **finding-0168 (the membership store)** — NOT owned here. It is a design pass with its own path,
  and it structurally retires the re-land idiom OPS-1 is bounding. Ops supplies the performance
  argument for it (independently derived from the semantic one); it does not absorb it.

**Owed:** WORK, not a deskcheck. All three plans are `proposed` and await the owner's hand
`proposed → ready`. Do NOT surface this track as deskcheck-owed until the restart demonstrably
completes the backfill.
