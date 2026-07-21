---
type: finding
id: finding-0142
status: open
created: 2026-07-21
updated: 2026-07-21
links:
  - docs/design-notes/fiber-geometry.md            # §2.6 the M1–M10 battery; §2.5 PD-a re-entry; §2.4 phase model
  - docs/build-plans/bp-085/plan.md                # G-A — the survey plan this reading fulfils
  - eval/harness/fiber_survey.py                   # the survey instrument (read-only, eval-side)
  - docs/findings/finding-0140.md                  # the Σ_move = {S,F,D,C} alphabet the labels obey
ftype: discovery
origin_plan: bp-085
route: orchestrator                                # math | direction
resolution: null
---

# Fiber-geometry measure-first survey (M1–M8): the recorded classes measured, the S (computed) class deferred; D-integrity holds; C is no longer empty

## What

The G-A read-only survey (`eval/harness/fiber_survey.py`, bp-085) ran M1–M8 over the live corpus
at **HEAD `42123068`** (σ-grid `(0.55, 0.65, 0.75)`; every reading carries its CN-1 index tuple
+ grid + coordinate digest). All claims below are `[GROUNDED]` in the survey's JSON output unless
graded otherwise. **Nulls/deferrals are recorded as results, never as measured zeros.**

**The one environmental block (§10 stop-and-raise, honestly recorded).** The **S (similarity)
class is DEFERRED**: it requires embedding the docs/ dialogue-artifacts eval-side, and the embed
model shares the memory-ceiling'd ollama (≤2 resident models, bright line 8) with the live
daemon (`qwen3.5:9b` + `qwen3-embedding:4b` both resident at run time). Under that contention
even a single 1500-char embed exceeds the 120 s fail-fast timeout. The survey **must not** evict
or restart the daemon, so it degrades gracefully: the S (computed) rows defer with a re-entry
condition; the F/D/C (recorded) rows compute unaffected. `[GROUNDED — survey embedder_status;
timing probe]`

### M-row-by-M-row result (each with its CN-1 index: HEAD 42123068, grid (0.55,0.65,0.75))

- **M1 — populations + skeleton overlap** (σ=0.55; F/D/C measured, S deferred):
  - **C** (causal-witnessed, `E_proven` co-production): **237 nodes, 1193 undirected edges**, docs/** space.
  - **F** (citation, `reference_edges` corpus→corpus, deduped undirected): **207 nodes, 593 edges**, docs/** space.
    (293,721 raw commit-keyed rows collapse to 593 distinct doc↔doc pairs.)
  - **D** (supersession, `versions`): **19 docs, 28 version-digest nodes, 16 arcs** (15 consecutive
    + 1 authored) — in the **vault/catalog space, DISJOINT** from docs/**.
  - **S** (similarity): **DEFERRED** (embedder) — 0 nodes recorded, expected-null-by-block, NOT a measured zero.
  - **Node Jaccard (support overlap):** `F|C = 0.396` (**126 shared nodes**); `C|D = F|D = 0`
    (D disjoint, a measured fact); `S|C = S|F = S|D = 0` (S deferred, 0-by-absence not overlap). `[GROUNDED]`
- **M2 — mismatch densities / conditional minting:** **DEFERRED** (S↔C, S↔F, `E[Δw_S|D]` all need cosines). `[GROUNDED — deferred]`
- **M3 — per-class triangle census** (σ=0.75; the D data-integrity check):
  - **D_triangles = 0** — **covering-only supersession integrity HOLDS** (ML owner decision 3);
    the stop-and-raise did NOT fire. C_triangles = 3976; F_triangles = 583; S_triangles deferred. `[GROUNDED]`
- **M4 — S-field Hodge split:** **DEFERRED** (S). `[GROUNDED — deferred]`
- **M5 — Forman-vs-churn:** **DEFERRED** (Forman runs on the S σ-graph). `[GROUNDED — deferred]`
- **M6 — D-thermometer** (measured): 19 docs with history, 34 versions, 15 supersession arcs,
  1 authored supersession, 28 distinct version digests. **Per-region χ_s is instrument-blocked**
  (`conductance.chi_s` needs a live `Spine` over the stratum — a daemon op, not buildable
  read-only over dialogue-artifacts from a worktree); the raw D-minting rate stands as the
  thermometer signal (§2.4c). `[GROUNDED]`
- **M7 — dead-vs-live signature:** **DEFERRED**. CF-density measured (C=1193, F=593); the D-rate
  field is disjoint-population (D off docs/**); S-velocity coherence needs two A7-clean cuts
  (only one eval-side cut). Dead-vs-live labeling parks on the finished-arc corpus (barely exists,
  bp-080 seal) — expected-thin, silence recorded not narrated. `[GROUNDED]`
- **M8 — σ-sweep + bottleneck-vs-product:** **DEFERRED** (S cosine MST); oq-0024's owed run
  re-enters when S is embeddable; no endorsed-chain corpus exists to score against either way. `[GROUNDED — deferred]`
- **M9/M10 (ride-along):** M9 sample-depth rides M6's version counts (34 versions / 19 docs — thin,
  the velocity/spectral tier's gate is not met); M10 endorsed-chain fiber signatures ride M7's
  deferral (no endorsed corpus). `[GROUNDED — thin/deferred]`

## Why it matters — gate dispositions

1. **PD-a re-entry cond. 1 (support non-degenerate) — PARTIALLY assessed, leans PARK. `[GROUNDED
   + INFERENCE]`** D is **fully disjoint** from the docs/** classes (Jaccard 0 to S/F/C — a
   measured node-space fact, not a thin sample), so any S⊕D or F⊕D coupled operator is
   contentless by construction today. F∩C overlap **is** non-degenerate (0.40, 126 shared nodes)
   — so the F/C pair alone does not fail cond. 1. But the note's coupling of interest is
   **S-seeded** (S dense continuum seeding C/F minting, §2.2), and every S-involving overlap is
   **deferred**. Verdict: cond. 1 is **not met for any D-involving pair (park)**; the S-involving
   pairs are **unresolved pending the S re-run** — PD-a stays parked, sharpened re-entry
   unchanged. The bundle-vs-sheaf sub-question (§2.5) likewise waits on the S overlaps.
2. **D-integrity (§2.2 / ML owner decision 3) — CONFIRMED CLEAN.** D_triangles = 0: the Hasse DAG
   is triangle-free on the live corpus; covering-only supersession is not violated. No corpus
   defect; the stop-and-raise condition did not fire. `[GROUNDED]`
3. **The note's "C is empty" premise has MOVED — a direction flag. `[GROUNDED]`** §2.0 / §2.5
   record "the live census read came back empty (bp-080 seal)" for the C fiber. At HEAD 42123068
   the C co-production fiber is **non-trivial: 237 nodes, 1193 edges** (and F∩C = 126 shared). The
   note's parking rationales that lean on "C thin/empty" (PD-a cond. 1 for C; the C-conditioned
   rows) should be re-read against this: **C is now a populated class.** This does not by itself
   fire any re-entry (the S-vs-C mismatch structure, M2, is the cond. 2 evidence and is deferred),
   but it changes the premise and is the strongest single reason to schedule the **S re-run**.
4. **FG-b (hop-priced functional) / oq-0024 — still owed, deferred cleanly.** M8's σ-sweep and
   bottleneck-vs-product divergence are the deciding measurement; they run over the S MST and
   defer with S. FG-b default (bottleneck σ*) stands; no silent change. `[GROUNDED — deferred]`
5. **FG-f (CN-4 magnitude calibration) — parked, unaffected.** M6's thermometer signal exists
   (D-minting rate) but per-region χ_s is instrument-blocked; magnitudes stay 0 (shipped inert).

**No gate is declared "resolved" off a deferred/expected-null row** (the survey's own falsifier).
The only two *positively closed* readings are: **D-integrity is clean (M3)** and **D is a disjoint
node population (M1)**.

## Re-entry condition

**The S rows (M2, M4, M5, M8, and the S columns of M1/M3/M7) re-enter by re-running
`uv run python -m eval.harness.fiber_survey` when the eval-side embedder has headroom** — i.e.
the live daemon is idle or not holding both model slots (bright line 8). No code change is
needed; the survey embeds ephemerally and degrades/upgrades automatically on `s_embeddings`
presence. A convenience: point it at the main `data/` (default) with the daemon paused for the
embed window (owner-gated; the survey never touches daemon lifecycle itself). The χ_s sub-reading
(M6) re-enters only if a read-only Spine surface over the dialogue-artifact stratum is built
(out of scope here; a separate `core/` plan with its own warrant).

## Routing

`math` / `direction` → **orchestrator**. Two items for the owner batch:
- **(direction)** the S re-run is the single highest-value follow-up — it closes PD-a cond. 1/2,
  the functional question (M8/oq-0024), and the phase model's first look. It needs an embed
  window, not new design.
- **(direction)** the note's "C empty" premise (§2.0/§2.5) is stale at HEAD 42123068 — C is a
  populated fiber (1193 edges). Worth an annotation on the next `/triage` pass (no ratified-text
  edit — A8; the correction lives here).

No `blocker`, no `spec-defect`: the plan was well-specified; the S deferral is an environmental
memory-ceiling constraint the survey handled by design, not a plan defect.
