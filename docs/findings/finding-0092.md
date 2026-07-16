---
type: finding
id: finding-0092
status: resolved
created: 2026-07-16
updated: 2026-07-16
links:
  - core/temporal/spine.py                        # _Builder.attestations() + _add() — the fix (14b3140)
  - docs/build-plans/bp-051/plan.md               # Item 3 acceptance; sealed complete after the fix
  - docs/design-notes/global-event-clock.md       # §2.2 g2 generator; §2.8-5 attestation calibration (authoritative)
ftype: spec-fidelity
origin_plan: bp-051 (spine-skeleton)
route: builder
resolved_by: 14b3140   # fix commit; merged 2c541db; live-corpus acyclicity re-verified PASS
---

# bp-051 spine g2 over-generated on shared attestation hashes — 1467-event cycle on the LIVE corpus (worktree had no data/ to catch it). CAUGHT at merge, FIXED faithful to §2.8-5.

## What
bp-051 passed green in its isolated builder worktree, but that worktree has no `data/`, so its
Item-3 acyclicity test ran against an EMPTY spine and passed trivially. On main (live corpus present)
`derive()` raised `SpineCycleError: cycle over 1467 events`. The defect was only reachable where store
files exist — the merge-time gate on main is what caught it.

## Diagnosis (reproduced via scratchpad/spine_cycle_diag.py on main, code+data co-present)
- SCC = 1467 events: **1457 attestations + 9 runledger + 1 derived** (non-attestation events only
  dragged in transitively).
- Hub identifiers were hashes **produced by ~3 events, consumed by ~20+** — shared artifacts (a common
  corpus/config digest listed by many attestations as BOTH input and output), not unique write-once mints.
- Concrete 2-cycle: `attestations:attestation:1 ↔ attestations:attestation:5`, each producing a hash the
  other consumes. Violated bp-051's own §8 soundness law `≼_derived ⊆ ≼_true`.

## Root cause
`_Builder.attestations()` minted each attestation's `output_hashes` into the `produced_by` map
(`produces=(aid, *output_hashes)`). A hash that is both an output of some attestations and an input of
others generated `producer(h)→consumer(h)` edges in both directions. **An attestation is a proof-layer
record, not the MINTER of its outputs** — each output is written to a store whose OWN event mints it.

## Resolution (14b3140, RESOLVED — no design change needed)
Attestations now produce ONLY their own content-addressed id; attestation→attestation causal order comes
exactly from `derived_from_ids` (the §2.8-5 provenance DAG, acyclic by construction). `output_hashes`
still ride the event's displayed `refs` (a new optional `_add(refs=…)` param) but no longer drive
`produced_by`. Cross-store provenance is preserved — the true minter (version/derived store event) still
produces those hashes, so version→att (input_hashes), att→derived (attestation_id), att→eval
(evidence_ref) all survive. Verified: live `test_acyclicity_on_the_real_repo_stores` PASSES; the
§2.8-5 edge-for-edge calibration test PASSES; the forged-cycle fail-closed test was RETARGETED (mutual
`derived_from_ids`, a genuinely impossible loop) and still raises `SpineCycleError` — the tooth was not
loosened. Two synthetic unit regressions (mutual-hash ⇒ no cycle; shared hub ⇒ no spurious edges) make
it reproducible in any worktree.

## Design read (NOT an errata — recorded for GC-2/GC-3 awareness)
This is NOT a gap in the ratified note. §2.2's g2 rule ("an event whose row records an identifier
another event MINTED") is sound as written — "minted" means the unique write-once mint. The bug was
minter **mis-attribution** in the implementation (an attestation is not the minter of its outputs). The
forward principle for wiring further stores into the spine (GC-2/GC-3): a g2 edge fires only from the
identifier's UNIQUE write-once minter, never from any event that merely lists it. No `design` finding
routed; the builder correctly concluded no design ruling was required.

## Process lesson (folded into the delegate discipline)
An integrity acceptance that requires the live `data/` corpus CANNOT be verified in a builder's isolated
worktree. Such legs must run on main (or a data-populated checkout), and ideally in a scratch integration
BEFORE the merge to main. Recorded for the resume-brief / delegate skill.
