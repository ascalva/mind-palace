---
type: design-note
id: dn-stability-adjudication
status: draft
implementation: not-built   # corpus-audit 2026-07 verification
created: 2026-07-02
updated: 2026-07-03
links: []
supersedes: null
superseded_by: null
warrant: null
---

# Design note — Stability adjudication: perturbation consensus over the reasoning complex

*Family tag → family 5 (the reasoning complex): confidence from survival under nondestructive,
systematic perturbation of 𝔎|_MR. See [`../NOTATION.md`](../NOTATION.md).*

**Status:** design only; **parked**. A post-panel adjudicator enhancement — it consumes the
completed interpreter panel (`support.py`, tension, temporal, loop v2 assembly must land first)
and its validation instrument is Track L's verdict store (L2), which does not exist yet. It does
not block, and must not delay, the Track L prerequisites (provenance `--apply`, self-knowledge
ingest). Flag-OFF R&D under the existing `[dream_rnd]` boundary; the live path is untouched.

## The idea in one line
Run the deterministic instrument passes (loop-v2 steps 1–7) K times over systematically
perturbed, ephemeral replicates of the complex; a claim's **survival rate across replicates**
becomes a second confidence axis, orthogonal to the panel note's cross-lens agreement.
Multiple rounds of *instrumentation*, one round of *dreaming* — synthesis still runs once,
only for claims that survive.

## What exists today — perturbation lives only at test time
1. **ε-jitter bottleneck-stability** (`test_structural_interpreters`) — verifies the persistence
   instrument, exploiting the stability theorem it carries by construction.
2. **Full-support-set ablation** (dreamer quality suite) — perturbation as a faithfulness
   falsifier, per the earned lesson that single-citation removal is too weak.
3. **The frozen control corpus** (Track L4) — a fixed reference, not a perturbation.

Nothing in `dream()` or `dream_v2()` perturbs at runtime. Each pass builds one complex at one σ
and adjudicates once. This note moves the test-time discipline into the adjudicator.

## Where survival earns its keep — a per-lens analysis
The lenses differ in whether robustness is already guaranteed:
- **Persistence (holes): exempt.** The bottleneck stability theorem makes small-perturbation
  survival a property of the instrument, not new information. Compute it once per pass;
  perturbation rounds here are cost without signal.
- **SBM / diffusion clustering (themes): the primary beneficiary.** Mean-field VEM with
  fixed-seed kmeans2 init has no stability guarantee; a planted-looking block can be an
  artifact of one σ or a handful of borderline edge weights. Co-membership frequency across
  replicates (consensus clustering) converts "the model selected k=3" into "this block
  persists in 94% of replicates."
- **Curvature bridges: the secondary beneficiary.** Ollivier-Ricci on a sparse graph moves
  substantially under small weight jitter; a bridge that appears in one replicate and vanishes
  in the next has not earned narration.
- **Tension / grounding cuts:** survival applies once the tension lens lands; grounding via
  noisy-OR is already multi-path and partially self-robust — measure before deciding.

## The perturbation family — typed, declared, bounded (G7 discipline)
Three perturbation types, each a `[dream_rnd]` tunable with declared bounds:
1. **Edge-weight jitter** within the noise floor of the embedding's cosine similarities — a
   principled band, not an arbitrary ε. (Estimating that floor is an open item below.)
2. **Node jackknife** (leave-k-out, default k=1) — does the claim survive removing any single
   member note? Generalizes the ablation-test lesson: full-set removal tests faithfulness,
   single-node removal tests fragility.
3. **σ-sweep** — a parameter perturbation; tests whether a claim is an artifact of the
   threshold rather than of the corpus.

## Nondestructive by construction, reproducible by discipline
The MirrorView is read-only and the complex is built per-pass in memory; replicates are
ephemeral copies and no store, firewall, or provenance surface is touched. The one hard
requirement is determinism: derive all K replicate seeds from a **recorded master seed**, and
put the master seed + perturbation config into the attestation `input_hashes` alongside the
authored digests. Without this, a dream's confidence is irreproducible — a regression of the
"prove *why* it believes" thesis at exactly the layer being strengthened. Determinism per
(corpus, master seed, config) is preserved.

## Integration with the clamp law — report first, gate later
c = min{1, γ^d·g·(1+λ(|Agr|−1))} already encodes cross-lens agreement. Options, in order of
increasing commitment:
1. **Report-only (first step):** survival rate s ∈ [0,1] recorded per claim in the dream
   record's `data`, not affecting c. Zero semantic risk; produces the data the validation
   test needs.
2. **Gate:** claims with s below a declared floor never reach synthesis.
3. **Multiplier:** fold s into c (e.g. on g). Changes adjudicator semantics; requires its own
   property suite and a ratified tunable range.
Do not skip to 3. Step 1 is sufficient until the validation below has run.

## The load-bearing caveat — stability filters artifacts; it does not detect insight
A trivially robust claim ("the corpus has one giant component") survives every perturbation
and is worthless. Survival improves the *precision* of the instrument layer — fewer
hallucinated structures reach the model — but is orthogonal to the Dreamer quality gap.
This note must not quietly substitute for Track L. The honest relationship is the reverse:

**The falsifiable test (runs once L2 verdicts exist):** correlate per-claim survival rate
with the owner's keep-verdicts over a steady-state window. If survival predicts keeps, it has
earned a permanent place in the clamp law (option 2 or 3). If it does not, it is decorative
formalism and is cut. This is why the note is parked: its validation instrument is the
longitudinal harness itself.

## Cost envelope
K × the deterministic pass (trough-tier, model-free; persistence computed once, not K times),
0 additional model calls. On the M2 Max the binding cost is K × (SBM VEM + curvature); K in
the 10–30 range is the expected regime, to be measured, not assumed.

## Cross-reference
`docs/research/security-planes.md` §6 names this note's stability filter as the intended input
to the adjudicator: artifacts failing perturbation stability are discarded before reaching the
owner's review queue, which is the concrete mechanism that note relies on to cut review fatigue.
That dependency runs one direction only — the adjudicator consumes survival rate as a report-only
signal (per the clamp-law integration above); it does not grant the adjudicator authority to
promote on its own. Promotion still spends only owner verdicts, per that note's owner-facing
boundary. Keep the two notes' validation stories aligned: both are gated on the same L2 verdict
store existing.

## Explicitly not this
- **Not** multiple rounds of synthesis — no model calls over perturbed views, no
  interpreted-over-interpreted recursion (that remains the separate, flag-OFF
  recursive-dreaming path, bounded by γ^d·g).
- **Not** a live-path change, a firewall change, or a store change.
- **Not** a substitute for Dreamer quality validation.

## Open questions
- Estimating the embedding noise floor that bounds edge-weight jitter (empirical, per model).
- K, and the aggregation statistic: mean survival vs. worst-case (min over perturbation
  types) — worst-case is the more honest default for a system that prizes provability.
- Whether σ-sweep survival should be reported separately from data-perturbation survival
  (parameter fragility and corpus fragility are different diagnoses).
- Whether the structural snapshot (§5.4 / A2 axes) should also record consensus statistics,
  giving the drift gauge a robustness axis over time.
