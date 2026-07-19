---
type: finding
id: finding-0096
status: resolved
created: 2026-07-17
updated: 2026-07-17
links:
  - docs/experiments/sigma-sweep-run-1.md          # the run that surfaced it (SE-1)
  - docs/design-notes/sigma-sweep-experiment.md    # FROZEN @ d932670 — SE-1(b) + the parked f9_composite objective
  - config/sweeps/dreamer-sigma-ab.toml            # objective = golden_recall
  - docs/inbox/owner-questions.md                  # oq-0024 — retired by this run per SE-1(b)
ftype: math
origin_plan: dn-sigma-sweep-experiment run 1 (SE-1)
route: orchestrator
resolution: RESOLVED by finding-0113 (bp-073 Phase Δ, owner-blessed 2026-07-19). The golden_recall saturation was INPUT-STARVATION, not a real ceiling — at n=208 (the dialogue-artifact corpus) the connectivity gauge already discriminates under E_sim alone (frac_connected 1.0→0.004 across σ). E_proven adds a real second lever via σ*-uplift (+0.74 at σ=0.7). Necessary-but-insufficient, refined.
---

# golden_recall is SATURATED (1.0 across the entire σ-grid) at the 13-doc corpus scale — the sweep objective has zero discriminating power, so SE-1's "insensitive in-range" is objective saturation, NOT σ-invariance of structure

## What
Run 1 of the σ-sweep swept `dream_rnd_sigma` over 21 points in [0.55, 0.75] × 5 seeds, objective
`golden_recall`, select_pipeline `dream_v2`. **Every cell scored golden_recall = 1.0000, halfwidth
0.0000, all 21 admissible.** The curve is perfectly flat, so SE-1 rule (b) fires: oq-0024 retires as
"insensitive in-range; default (0.62) stands." That disposition is correct per the FROZEN protocol —
but the ROOT CAUSE is that golden_recall has **no dynamic range** at this corpus scale (13 authored
docs): the frozen golden fixture is fully recalled regardless of σ, so the objective literally cannot
see σ.

## Why it matters
The flatness is an ARTIFACT of a saturated objective, not evidence that σ is structurally inert. The
same run's **SE-2 proves the opposite**: the dream_v2 σ-fibers are non-degenerate (n=32, pers mean
0.235, max 1.0, frac_ge_strong 0.063) — the σ-hierarchy carries real, σ-*sensitive* structure. So
"σ doesn't matter" (what golden_recall reports) and "σ organizes real multiscale structure" (what the
fibers report) are both true, measured on the same night. The σ-selection question (oq-0024) simply
cannot be answered by golden_recall here — the objective is the wrong instrument at this scale.

## Recommendation (re-entry)
oq-0024 is RETIRED as a completion (default 0.62 stands). A FUTURE σ-selection question needs a
**discriminating objective** — the parked `f9_composite` / per-cell F9 wiring the sweep spec's banner
names (dn-evaluation-harness E5/E7), which the note §Parked already tracks — AND/OR a **larger
corpus** (the corpus-growth re-entry). Until one exists, a σ-sweep on golden_recall will keep
returning a flat curve. Non-blocking; informs a run-2 note update (a re-ratified pre-registration
with a discriminating objective) and the connectivity-instruments tranche's corpus-size floor.

## Non-goals
Not re-opening SE-1's rule (b) disposition (correct per the frozen note). Not a correctness defect in
the optimizer (it did exactly the right thing on a flat curve). Purely: the objective/corpus can't
discriminate σ yet.
