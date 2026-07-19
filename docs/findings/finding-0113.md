---
type: finding
id: finding-0113
status: resolved
created: 2026-07-19
updated: 2026-07-19
links:
  - docs/build-plans/bp-073/plan.md                # Phase Δ — the measurement that produced this
  - docs/findings/finding-0096.md                  # the golden_recall saturation this re-measures
  - docs/design-notes/agent-taxonomy.md            # §2.2 grounding law ("a second edge class, not a better σ")
  - eval/harness/re_measure.py                     # the measurement (assemble + re_measure_oq0031)
re_entry: RESOLVED — owner blessed the verdict (2026-07-19, session-32) and the resolution of the 0096–0100 cluster with it.
ftype: math
origin_plan: bp-073
route: orchestrator
resolution: owner-blessed (2026-07-19, session-32). The oq-0031 verdict stands: the 13-doc saturation was INPUT-STARVATION (n=208 discriminates under E_sim alone); E_proven is a real but SECONDARY lever via σ*-uplift (+0.74 at σ=0.7), not loose-grid bridging — sufficient to enrich connectivity, NOT necessary to break the saturation (node count was the primary cure). Findings 0096/0099/0100 resolved directly; 0097/0098 resolved root-cause (starvation), the optimizer-guard hardening left as a separate future finding if wanted. oq-0031 retired.
---

# oq-0031 re-measured: the 13-doc saturation was INPUT-STARVATION; E_proven is a real second lever via σ*-uplift, NOT loose-grid bridging

## The question (oq-0031)
Was the 13-doc connectivity saturation (finding-0096: golden_recall flat at 1.0) **input
starvation** — fixable by a second, proven edge class + more nodes — or a **real ceiling**?

## What was measured (bp-073 Δ, real corpus)
The composed graph `{208 dialogue-artifact docs} × {E_sim ∪ E_proven}`: E_sim = cosine over
eval-side doc embeddings (qwen3-embedding:4b, ephemeral/read-only); E_proven = 1068 witnessed
shared-witness co-production edges projected from 3700 live C-edges (bp-071's integrator). The
RATIFIED `sigma_star` ran over BOTH the E_sim-only and the E_sim∪E_proven graphs, unchanged.

- doc-doc cosine: min 0.20, **p50 0.46**, p90 0.57, max 0.93 — a topically DENSE corpus (every doc
  is about the same project).
- **frac_connected (fraction of pairs connected at σ), E_sim-only → E_sim∪E_proven:**
  | σ | E_sim | E_sim∪E_proven | Δ |
  |---|---|---|---|
  | 0.30 | 1.000 | 1.000 | +0.000 |
  | 0.50 | 1.000 | 1.000 | +0.000 |
  | 0.60 | 0.943 | 1.000 | +0.057 |
  | 0.70 | **0.261** | **1.000** | **+0.739** |
  | 0.80 | 0.004 | 0.770 | +0.766 |
  | 0.90 | 0.0002 | 0.457 | +0.456 |
- `proven_bridges = 0`, `discriminates (pinned criterion) = False`.
- **σ\*-uplift, derived from the curve:** at σ=0.7, connected pairs rise 26.1% → 100%, so **≥73.9%
  of the 21528 pairs** (≈15.9k) had σ* cross the 0.7 threshold alone — the total uplifted count is
  larger still (any pair whose σ* rose at all). `n_sigma_uplifted` is a report field; the exact scalar
  was not separately captured because the eval-side embedder timed out under contention with the LIVE
  daemon (run #29 also embeds) on the confirmation rerun — a fitting reminder that Δ is read-only and
  daemon-safe (Item 2b) yet SHARES the deterministic embedder. The frac_connected curve is the primary
  quantification and needs no rerun.

## Verdict (honest, non-forced — the Q4 criterion was pinned BEFORE measuring)
Three findings, in order of weight:

1. **The 13-doc saturation was INPUT-STARVATION.** At n=13–17 (the mirror/golden scale) the corpus
   is too small to discriminate (golden_recall pinned at 1.0). At **n=208** (the dialogue-artifact
   corpus) the connectivity gauge ALREADY discriminates strongly **under E_sim alone** — frac_connected
   sweeps 1.00→0.004 across σ, the opposite of flat. More nodes un-saturate connectivity. oq-0031's
   ceiling was **not real**; it was starvation.

2. **E_proven is a real SECOND lever — via σ\*-uplift, not component-bridging.** With the node set and
   E_sim edges held identical, adding the 1068 proven edges raises tight-threshold connectivity
   massively (σ=0.7: 26%→100% of pairs connected; +0.74). The delta is cleanly attributable to
   E_proven. This CONFIRMS the taxonomy's grounding law (§2.2: "a second, proven edge class, not a
   better σ") as a genuine mechanism — the proven weight 1.0 supplies high-bottleneck paths that
   cosine (p50 0.46) cannot.

3. **The pinned bridge-criterion (None→reading at the loosest grid) is VACUOUS on this corpus — a
   measurement-calibration lesson.** Because the corpus is topically dense, E_sim ALONE fully connects
   all 208 docs at the loosest grid (σ=0.30 → frac=1.0), so there is **no disconnected pair for a
   proven edge to rescue** → zero bridges → `discriminates=False`. This is NOT evidence E_proven is
   inert (§2 shows it is not); it is that the σ*/MST bridge test only sees E_proven when E_sim leaves
   the graph DISCONNECTED at the loosest grid — which a single-topic corpus never is. The correctly-
   calibrated structural signal for a floor-connected corpus is **σ\*-uplift** (`n_sigma_uplifted` /
   the frac_connected curve), not the loose-grid component-bridge count.

**Net (precise wording — "necessary-but-insufficient" is too generous):** the taxonomy's answer had
two halves. The **"not a better σ"** half is CONFIRMED — the fix is structural, not parametric. The
**"E_proven is the fix"** half is REFINED: E_proven is a **real but SECONDARY lever** (σ*-uplift), NOT
the primary cure and NOT strictly necessary — E_sim ALONE discriminates once the corpus is large
enough (n=208). The dominant cure for the 13-doc saturation was **node count** (input-starvation).
So E_proven is *sufficient to enrich* connectivity but *not necessary to break the saturation*. And
the falsifier the note/plan named (loose-grid bridging) is the wrong instrument on a dense corpus; the
right one is the σ*-uplift curve. No instrument was edited; no green was forced (`discriminates=False`
stands, honestly, beside the strong σ*-uplift the curve records).

## Consequence
Proposes resolving the **oq-0031 saturation cluster (findings 0096–0100)** with this measured verdict
(owner-routed — a `math` finding re-enters design through the same gate a brainstorm does). Downstream:
the dreamer's grounding law (Law 2) consumes E_proven with empirical warrant; the connectivity/sweep
track's validation (0096–0100) unblocks; a future measurement wanting the bridge-criterion to bite
needs an E_sim-disconnected-at-floor corpus (cross-topic, or a tighter grid floor).
