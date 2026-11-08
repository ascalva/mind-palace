---
type: track
slug: dynamics
title: Graph dynamics — the evolving graph's velocity, flows, ripples and macro regime
status: active
warrant: null
audit_refs: []
dod:
  - GD-0 the design proved — dn-graph-dynamics with its first theorems machine-checked in formal/Palace/Dynamics.lean (the velocity, the Neumann resolvent and its tail, HodgeRank, the modes and the mode-decay bound, the quotient Laplacian and the gap, the ripple across a transport, the mixing scaffold), attacks and controls green
  - GD-1 the Flow sort and the projections gradient, curl, harmonic, with their QSA-style laws transcribed and property-tested
  - GD-2 ripple on a directed relation with a damping, diffuse its symmetric case, with the tail bound as the trace's accuracy line
  - GD-3 at scale t and coarse by a partition, the heat kernel and the quotient as adjectives, with the gap and the mode bounds as their laws
  - GD-4 velocity of an identity over a window of cuts, on the D moves at the node grain and the snapshot (L7), once the versions store holds a second generation
  - UF-0 the utility field's design proved: dn-utility-field with UTL-1 to UTL-6 machine-checked in formal/Palace/Utility.lean (the box, the decay window and the arcs, no localization, the fold and the switch-off, the bounded nudge through Weyl, the loop's contraction), the regimes' controls, attacks and controls green, the simulator on synthetic graphs
backlog_deskcheck: null
links:
  - docs/design-notes/dn-graph-dynamics.md
  - papers/2026-11-07-graph-dynamics/paper.tex
  - docs/design-notes/dn-utility-field.md
  - papers/2026-11-08-utility-field/paper.tex
  - docs/design-notes/edge-dynamics.md
  - docs/design-notes/temporal-retrieval-algebra.md
  - docs/design-notes/dn-query-sentence-algebra.md
---
# Track — Graph dynamics (the evolving graph's velocity, flows, ripples and macro regime)

The identity card for the dynamics track, minted alongside its founding note (the
query-language and mathematical-foundations precedent; ⚑ renamed or rejected at the
merge). **Scope:** what an evolving graph's state, direction and
magnitude are in the palace's own terms, proved before any code: a value's velocity over a
window of cuts, an edge flow and its Hodge reading, the ripple of a shock along a relation
as a resolvent, the modes of the heat kernel as the macro variables, coarse-graining by a
partition, and the laws the language needs to say any of it. Members are the artifacts
declaring `track: dynamics`.

**Not in scope:** the observed-side series that would feed a velocity (Lane B of
`dn-edge-dynamics` stays parked on its sample depth); the magnetic operator's build
(`dn-magnetic-laplacian` ML-a); `core/` changes before they are licensed at the merge; any
back-action on the graph.

## Relationship to other tracks

`mathematical-foundations` holds the families this one builds on (Hodge, Heat, Retrieval,
Transport, Frustration, Leak, Sever) and the ledger the design theorems enter when code
relies on them. `query-language` owns the sentence algebra; the sorts and verbs this track
asks for (a Flow sort, `gradient`, `curl`, `harmonic`, `ripple`, `at scale`, `coarse by`,
`velocity of`) are proposals to it, each with its laws stated first. `fiber-geometry`
designed the chain language the `D` moves at the node grain would extend.

**Definition of done:** the dod rows above; GD-0 is the note and its theorems, GD-1 to GD-4
are the order to build in, each licensed at the merge.

**Owed deskcheck:** none standing.
