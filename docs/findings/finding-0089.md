---
type: finding
id: finding-0089
status: open
created: 2026-07-16
updated: 2026-07-16
links:
  - docs/build-plans/bp-049/plan.md
  - docs/design-notes/evaluation-harness.md
  - eval/harness/sweep.py
ftype: spec-fidelity
origin_plan: bp-049 (sweep-engine, Item 14)
route: orchestrator
---

# bp-049 §6/§8 under-specify which pipeline the optimizer selects on

## What
The sweep spec (§6) declares `pipelines = ["phase7", "dream_v2"]` — the runner produces BOTH per
cell (native A/B). Item 14 says "build the per-lever curve ... per pipeline" and then `select(curve,
current) -> value` (§8) operates on a SINGLE curve, emitting ONE `ProposedChange` for the swept
lever. The plan does not say which of the per-pipeline curves the selection is made on when
`pipelines` has more than one entry.

This matters for correctness of the emitted value: for the first instance the swept lever is
`dream_rnd_sigma`, which ONLY the `dream_v2` lane reads (`shadow.py`: `MirrorGraph.build(view,
sigma=rnd.sigma)`); `phase7` uses a different lever entirely (`dream_similarity_threshold`) and its
objective curve is flat w.r.t. `dream_rnd_sigma`. Selecting on the phase7 curve would optimize a knob
that lane does not respond to.

## Resolution taken (builder-resolvable; recorded, in-scope)
Added an OPTIONAL spec key `select_pipeline`, defaulting to the LAST entry of `pipelines` (the
dream_v2 lane the σ lever drives). The engine partitions objective readings by `key.spec_hash`
(shadow encodes the pipeline into spec_hash), builds the primary pipeline's curve, and selects on it.
The choice is recorded in the `SweepResult` + the proposal rationale — never silent. All per-pipeline
readings remain in the eval store for E4's report to reconstruct.

This is a defensible default that keeps the first σ-instance correct without touching read-only files.

## Open question for the orchestrator/owner (parked, does NOT block this build)
Should the design note §2.6 make the selection pipeline a first-class, REQUIRED spec field (rather
than a defaulted optional), and should the default be "the lane the swept lever reads" derived from a
lever→pipeline map rather than positional "last"? A lever→pipeline map would be more robust than
positional order but requires a new declared relation the codebase does not currently carry.

## Routing
`spec-fidelity`, route → orchestrator. Parks no acceptance criterion (the build proceeds on the
recorded default); re-entry condition: the design note pins the selection-pipeline semantics.
</content>
