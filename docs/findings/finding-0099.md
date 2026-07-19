---
type: finding
id: finding-0099
status: resolved
created: 2026-07-17
updated: 2026-07-17
links:
  - docs/design-notes/connectivity-instruments.md   # CN-3 — the statement this refines
  - docs/build-plans/bp-060/plan.md                 # item 6 + §8 amended with the banner (pre-blessing)
  - docs/brainstorms/graph-at-a-past-cut.md         # the design pass that surfaced it (D5)
ftype: math
origin_plan: graph-at-a-past-cut design pass (Fable/xhigh, 2026-07-17)
route: orchestrator
resolution: RESOLVED by finding-0113 (bp-073 Δ, owner-blessed 2026-07-19). The CN-3 connectivity statement was exercised on the real composed graph over 208 nodes: the σ*/conductance instruments discriminate strongly (frac_connected sweeps 1.0→0.004), and the σ*-uplift under E_proven confirms the multiscale reading is non-degenerate at adequate corpus scale. The refinement this finding named is validated by measurement.
---

# CN-3's "a conductance rise requires new edges" is the unweighted shadow — under the CN-4 weighted measure the exact law is edge-WEIGHT monotonicity, and the attribution set includes edits

## What
CN-3 (ratified) states: "Rayleigh monotonicity binds: removals can never raise conductance;
therefore a conductance rise between consecutive cuts requires **new edges**, and the contributing
additions are enumerable and individually testable." That statement is exact for **unweighted**
(threshold) graphs. But CN-4 pins the family's edges as **weighted**: `w(u,v) = cos(u,v)^α ·
exp(s_lat·a_lat − s_seq·a_seq)` — and even at shipped magnitudes (0) the weight is `cos^α`, which
**moves when a note is edited**. The exact law (standard Rayleigh monotonicity, numerically checked
2026-07-17: C(0,2) rose .5437→.5881 on a single weight increase with no new edge, fell to .4548 on
a decrease): *effective conductance is monotone non-decreasing in each edge weight; a rise between
cuts requires ≥1 edge-**weight** increase, of which a new edge is the 0→w special case.* An **edit**
that moves two notes closer raises conductance with no new edge at all.

## Why it matters
bp-060's reconnection rider attributes Δ-conductance spikes by enumerating "the contributing
additions." On the real corpus, an enumeration restricted to *new edges* would miss edit-driven
rises (a false "no attribution found" — or worse, a misattribution to an innocent new edge that
survives leave-one-out only by coincidence). The correct attribution set between cuts is **the
edges whose weight increased** = the Δ-elements (added chains, edited chains) projected to edges;
the leave-one-out verification discipline applies to it verbatim and unchanged. Symmetrically, a
conductance **drop** on an interval certifies a weight decrease (edit-apart or tombstone) — the
same enumeration answers "what did I forget," not just "what did I reconnect" (the memory-curve
generalization, capture D5/D7).

## Disposition
- The design note is ratified (A8-immutable): this finding is the erratum-of-record channel
  (the oq-0028 discipline); no note edit.
- **bp-060 (still `proposed`, pre-blessing) amended this session**: item 6's acceptance/falsifier
  and §8 now carry the weighted statement with a banner citing this finding — so the builder
  enumerates weight increases, not just new edges. The synthetic G2=G1+{e} test is unaffected
  (a new edge IS a weight increase); one synthetic edit-rise case is added to the battery.
- No code exists yet to correct (the tranche is unbuilt); this lands the law before the builder
  reads the plan — the cheapest possible time to catch it.
