---
type: finding
id: finding-0079
status: routed           # open → routed → resolved | promoted  (batched → oq-0024)
created: 2026-07-14
updated: 2026-07-14
links:
  - config/defaults.toml            # [dreaming] similarity_threshold = 0.62 (σ)
  - docs/findings/finding-0077.md   # the id:: embedding pollution this de-pollution followed from
  - docs/build-plans/bp-036/plan.md
  - core/dreaming/cluster.py        # single-linkage at σ
ftype: direction         # blocker | spec-defect | question | discovery
origin_plan: bp-036
route: orchestrator       # design/direction → owner-gated config tuning + a methodology
resolution: null
---

# σ (dreaming similarity threshold) was implicitly calibrated on the id::-polluted graph — re-tune it

## What

The bp-036 body-only re-embed + re-dream experiment (owner-run 2026-07-14, daemon down) surfaced a
threshold-calibration problem. σ = `dreaming.similarity_threshold` = 0.62. The id:: mint's shared
`"id:: "` prefix had uniformly LIFTED every pairwise cosine (finding-0077), so σ=0.62 was effectively
looser than its nominal value. Removing the properties dropped all pairwise cosines ~5% (centroid shift
mean 0.95), so the SAME σ=0.62 is now materially stricter. Measured on the clean (body-only) graph:

- The 5 pre-wipe dreams → **1** clean dream (the 4-note recursion core, cos 0.64–0.72 — a genuine win:
  4 of the 5 old dreams were redundant snapshots of one over-merged cluster).
- **Lost:** the art/creation cluster (`132225`/`132316`/`132412`) — content cosines **0.46–0.57, all
  below σ**. Artifact-driven in the old graph (correct to drop) BUT thematically real and only
  **0.05–0.09 below** the bar.
- **Trimmed:** two recursion notes (`000928`, `130834`) fell **0.005 / 0.018 below σ** — genuine near-core
  members lost by a hair.

So σ=0.62, tuned against the inflated graph, now under-clusters genuine-but-subtle themes on the honest
content-only graph.

## Why it matters

The dream/theme layer is downstream of this threshold. Left at 0.62, the de-polluted graph will silently
MISS real subtle themes (the art cluster is the concrete example) — the opposite failure from the old
over-merging. This is the "calibrate σ on the owner's own corpus" the config comment already flags
(`σ ∈ [0.55, 0.75]`), now actionable for the FIRST time on a graph that reflects content, not metadata.

## Re-entry condition

Not parked (bp-036 sealed; the graph is clean). When the owner wants the dream layer tuned: lower σ toward
~0.56–0.58 (a candidate that recovers the art theme + the two near-core notes) and re-dream, comparing.

**Do this as a PROPER experiment, not a one-off** — this session's A/B + single re-dream was a quick
gauge (informative, but N=13 notes, one σ, one dream pass, judged by hand). A real calibration should:
sweep σ across [0.55, 0.75] in steps; at each σ record the graph (edges, clusters, near-threshold pairs)
and the resulting dreams; judge cluster quality against the owner's own sense of which note-groupings are
real; and pick σ by that curve, not a single guess. Consider a small harness (mirror `reembed_bodyonly`)
that emits the σ-sweep so the choice is evidence-based and repeatable, and re-run it whenever the embedder
or corpus changes materially. The gauge axes stay the same (better / uncovered / regressed).

## Routing

`direction` → orchestrator. Non-blocking; the fix stands. Batch to owner-questions for the σ value +
whether to build the sweep harness; a config-only tune is owner-gated (`config/local.toml` or
`levers.toml`), never auto-modified.
