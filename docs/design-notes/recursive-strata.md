---
type: design-note
id: dn-recursive-strata
status: draft
implementation: partial   # corpus-audit 2026-07 verification
created: 2026-07-03
updated: 2026-07-04
links: []
supersedes: null
superseded_by: null
warrant: null
---

# Recursive Strata: The Dreamer as a Map on Complexes

**Status:** Parked. Design captured; no implementation.
**Re-entry condition:** the Track L adoption criterion (L4) is met — the Dreamer has demonstrated single-pass insight against the baseline at the ratified threshold.
**Immediate actions:** two, both cheap, both listed in §8. Everything else in this note waits.

---

## 1. Position

Track L validates the Dreamer as a single-pass function: authored corpus in, interpretations out, verdicts back, tuning through the owner's hand. This note specifies the successor capability: Dreamer outputs re-entering the complex as reasoning substrate, so that cycle *n* reasons over the corpus *plus* the accumulated validated interpretations of cycles 1 through *n−1*.

This is deliberately sequenced after adoption, not alongside it. Recursion amplifies whatever the Dreamer is. Until Track L establishes what the Dreamer is, recursion amplifies an unvalidated process — machinery applied to noise. The ordering principle is the same one that parks Track G behind Dreamer usefulness: validated Dreamer before recursive Dreamer, for the same reason as deeper Dreamer before hands.

## 2. Formal statement

Let K₀ be the authored complex (the current object of all reasoning). Each Dreamer cycle *n* emits a **stratum** Sₙ: a set of derived nodes (interpretations, theme clusters, synthesized claims) and derived edges (their citations into the complex, and relations among themselves). The complex reasoned over at cycle *n* is

&nbsp;&nbsp;&nbsp;&nbsp;Kₙ = K₀ ∪ S₁ ∪ … ∪ Sₙ₋₁

and the generalized Laplacian is rebuilt on Kₙ. The Dreamer is thereby promoted from a function on notes to a map **D** on complexes, and the recursion is fixed-point iteration of D — not call-stack recursion. The natural questions become dynamical: what are D's attractors, does iteration converge or drift, what governs the basin.

> **Cross-ref (ingest operations):** `design-notes/dialogue-ingest-and-recursion.md` is the concrete ingest-operation instantiation of this map D — the operation vocabulary (supersede / attach_defeater / record_warrant) that turns "a thought" into a graph change, composing with the I5 budgets and the γ^d bound (built: `core/recursion.py`; I5 budgets still parked).

A **belief**, in this formalism, is an attractor: a derived cluster that survives repeated application of D and continues to earn verdicts. Fruitful-but-not-permanent is definitional — an attractor holds its basin only while renewal maintains it (§4).

Strata are a typed layer of the complex like any other. Their contribution to the shared operator carries its own layer weight, which is where all governance attaches.

## 3. What recursion buys, and the symmetric hazard

**The mechanism.** A derived node bridging two weakly connected regions of K₀ inserts a low-resistance path. Diffusion between the regions rises; the bridging edges' curvature shifts; cycle *n+1* sees amplified signal where cycle *n* saw a whisper. This is the intended effect: weak-but-real relationships in the authored corpus become progressively legible as validated interpretation accumulates around them.

**The hazard, stated symmetrically.** The identical mechanism amplifies apophenia. A spurious interpretation, once written into a stratum, manufactures the structural evidence for its own confirmation in the next cycle. The failure mode is not individual wrongness — single wrong insights get bad verdicts and decay. The failure mode is the **tower**: stratum-5 nodes citing predominantly stratum-4 nodes, derivation drifting free of authored ground while remaining internally coherent and confidently scored. An echo chamber is provable, attested, and useless.

Everything in §4 exists to make the mechanism available and the tower impossible.

## 4. Governance invariants

These extend existing invariants; none replaces one.

**I1 — Promotion by verdict only.** A derived node's edge weights are increased only through an explicit owner verdict ("promote"), never through the Dreamer's own confidence scores, and never automatically. This is the existing verdicts-feed-tuning-through-the-owner's-hand invariant applied to the strata layer. Auto-promotion is self-modification and sits behind the same separate gate.

**I2 — Decay by default.** Unrenewed derived weights decay on the temporal layer. Persistence must be earned repeatedly; no interpretation is grandfathered. The temporal layer, previously along for the ride, becomes load-bearing here. Decay rate is a manifest parameter (§5).

> **Cross-ref (identity & amendment):** `design-notes/ingest-identity-and-amendment.md` gives the structural-layer instantiation — corrections are supersession + re-projection of the derived index, never in-place edits. Decay (I2) and *supersession* are distinct mechanisms: supersession as an edge type is introduced there (built as `SUPERSEDES`, `core/stores/edges.py`), not here.

**I3 — Bounded strata contribution.** The strata layer weight in the generalized operator lives in the tuning manifest with a typed, bounded range whose ceiling keeps K₀ dominant. Whatever the bound is ratified to be, the authored corpus must remain the majority of the operator's mass. The floor is zero: setting the weight to 0 exactly recovers the single-pass Dreamer, which is the modularity guarantee — recursion is a dial, not a rewrite.

**I4 — Depth is typed and visible.** Every derived node carries its stratum depth as data. Instruments and digests can therefore condition on depth, and the grounding gauge (§6) is computable by construction.

**I5 — Bounded strata cardinality.** Distinct from I3, which bounds the strata layer's *mass* (Σ weight) so K₀ stays dominant. I5 bounds its *population* — the node and edge counts admitted per cycle. The two are orthogonal: a cycle can satisfy the I3 mass ceiling with a swarm of low-weight nodes, leaving the operator's dimension and the owner's review queue to blow up while every individual weight stays negligible. I5 is a ceiling on proposals per cycle, not a quota — the Dreamer proposes under it, and the promotion gate (I1) throttles again downstream. Two budgets:

- `strata.node_budget` — maximum derived nodes proposed per cycle, expressed relative to the grounded node count, not as an absolute integer (a fixed count means opposite things at 10³ and 10⁵ nodes). At current corpus scale the binding constraint is not this fraction but owner review capacity; the fraction becomes binding only past the crossover where it exceeds what the owner can verdict in one session. Both bounds are recorded; review capacity binds first, which ties the node budget to review fatigue — the Track L primary failure mode — rather than to an arbitrary constant.
- `strata.edge_budget` — typed, because the three edge kinds carry different risk. Grounding edges (derived→K₀) are unbudgeted or cheap: throttling them throttles accountability, the opposite of the intent. Lateral edges (derived→derived, same stratum) carry a real budget. Cross-stratum edges (derived→earlier-derived) carry the tightest budget — they are the tower's building material (§3), the stratum-*n*-citing-stratum-(*n*−1) pattern that manufactures self-confirmation. Budgeting edges by type makes I5 a *preventive* control on tower formation, complementing the grounding-ratio gauge's *detective* one (§6): the material is capped ex ante, not only measured after the tower stands.

I5 damps *population*; the confidence bound `c ≤ γ^d·g` (Invariant 10) together with I2 and I3 damps *influence*. Both dampers are required for D to be a contraction: γ^d bounds how much a derived node may matter, I5 bounds how many may exist. Neither substitutes for the other, and setting either budget to its floor (node_budget 0, or all edge types to 0) recovers the non-recursive Dreamer exactly, preserving the I3 modularity guarantee in the cardinality dimension.

**Provenance classification.** Derived strata are a third provenance class: neither authored (sealed core) nor external (network zone). They are self-generated — trusted as to origin (the attestation chain proves the Dreamer produced them and how), untrusted as to truth (verdicts alone confer that). The provenance firewall treats them as readable by the Dreamer but never confusable with authored content: no instrument may consume a derived node as if it were K₀. This is a new label type, not a new firewall mechanism.

**Indexing policy cross-reference.** `docs/research/security-planes.md` §6 specifies the librarian's indexing policy as a function of this label lattice: external strata index on ingest, derived strata index on promotion only. This is the concrete mechanism that keeps I1 (promotion by verdict only) enforced at the retrieval layer, not just at the weight layer — an unpromoted `DERIVED_STRATUM` node must not be retrievable, not merely unweighted. Treat the two notes as one policy; do not let them diverge at unpark time.

## 5. Manifest additions (L3 schema, reserved now, ranges ratified later)

- `strata.layer_weight` — bounded above per I3; default 0.
- `strata.decay_rate` — temporal decay of unrenewed derived weights.
- `strata.max_depth` — hard ceiling on stratum depth admitted to the operator; small (2–3) at first unpark.
- `strata.promotion_step` — weight increment per promote verdict.
- `strata.node_budget` — per-cycle ceiling on derived-node proposals, relative to grounded count; overridden by the owner review-capacity absolute at current scale (I5).
- `strata.edge_budget` — per-cycle ceiling on derived-edge proposals, typed {grounding: unbudgeted/cheap, lateral: bounded, cross_stratum: tightest} (I5).

## 6. Gauges

**Grounding ratio (primary).** Per derived node: the fraction of its cited support that reaches K₀ (transitively, through however many strata) versus terminating in derived nodes whose own support never grounds. Aggregate distribution per stratum goes in the weekly digest. A healthy recursive Dreamer shows high grounding at every depth; a falling ratio across strata is the tower forming, and it is visible as one number before it is a problem.

**Depth histogram.** Count of derived nodes per stratum depth in the digest. Growth concentrated at max depth is pressure against the ceiling and prompts a decision rather than silently truncating.

**Fixed-point drift.** Cycle-over-cycle stability of the promoted cluster set (Jaccard against previous cycle). Complements the A1 drift gauge: A1 watches the system's sense of itself; this watches the belief set. Stable-under-renewal is the desired attractor signature; oscillation or monotone growth are distinct pathologies worth distinguishing in the digest.

**Proposal budget utilization.** Per cycle: derived nodes and edges proposed against their I5 ceilings, and the edge-type mix (grounding : lateral : cross-stratum). Sustained saturation of the node budget is pressure to raise the ceiling or tighten the Dreamer — a decision, not a silent absorption. A rising cross-stratum fraction is the tower forming in the population dimension, visible before the grounding ratio moves.

## 7. Threat model note

This is a third threat model, distinct from the two already separated: not adversarial ingested content (provenance firewall), not tampering with governing prompts (fingerprinting and attestation), but **self-generated drift** — the system's own outputs degrading its substrate. The controls are correspondingly different: verdict-gated promotion (I1), decay (I2), bounded mass (I3), and the grounding gauge. Conflating this with prompt injection would misapply the firewall; conflating it with tampering would misapply hashing. It is its own row in the threat table.

## 8. Immediate actions (the only work items this note authorizes)

1. **Reserve the label before the migration runs.** Add `DERIVED_STRATUM` to the provenance label taxonomy now, with an integer `depth` field, before the pending migration `--apply` relabels the existing rows. Reserving it costs one enum entry; retrofitting it after the relabel costs a second migration. No code consumes the label yet.
2. **Add a candidate verdict category.** The Track L verdict taxonomy is an open decision awaiting ratification; add "promote insight weight" to the candidate set so the taxonomy is decided once, with recursion's needs on the table.

## 9. Non-goals

- No recursive execution path, shadow or live, before the re-entry condition.
- No Dreamer-confidence-based weighting of derived content, ever, under any future revision — that boundary is I1 and it is load-bearing, not provisional.
- No unbounded depth. If depth pressure appears, it is a ratified decision, not a config bump.
- No treatment of derived strata as authored content anywhere in the system, including in exports, digests, or the review REPL, where derived nodes are always visibly marked with depth.

## 10. Open decisions at unpark time

Deferred deliberately; listing them now so unparking starts from a decision list, not a blank page: initial `layer_weight` ceiling; decay half-life; whether demote verdicts exist symmetrically with promote or decay alone handles removal; whether strata participate in the frozen-control-corpus reruns (recommended: yes, with a separately frozen stratum set, so longitudinal curves isolate recursion's contribution the same way they isolate corpus growth); whether the grounding ratio earns an interruption threshold or remains digest-only; and the I5 budgets — the initial `node_budget` fraction and the review-capacity absolute that overrides it at current scale, the `edge_budget` values per type, and specifically whether cross-stratum edges start at a hard zero at first unpark (strictest: no derived→derived-across-strata citation until the mechanism is trusted) or a small positive ceiling.
