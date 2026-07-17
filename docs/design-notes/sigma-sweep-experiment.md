---
type: design-note
id: dn-sigma-sweep-experiment
status: draft               # draft → ratified → superseded.  draft→ratified is an OWNER-ONLY hand edit.
implementation: design-only
created: 2026-07-17
updated: 2026-07-17
links:
  - docs/design-notes/evaluation-harness.md                    # ratified — the harness frame; E3a-1b's optimizer IS SE-1's analysis
  - docs/design-notes/sigma-fibers-and-multiscale-dreaming.md  # ratified — fibers + gate; SE-2/SE-3 test it on real data
  - docs/design-notes/dreamer-quality-suite-evaluation.md      # F9 — the control battery SE-4/V3 reuses
  - docs/design-notes/global-event-clock.md                    # ratified — certified cuts; V2's snapshot indexing
  - docs/design-notes/connectivity-instruments.md              # draft — phase-B re-analysis consumer; the pre-registered linkage question
  - config/sweeps/dreamer-sigma-ab.toml                        # the frozen sweep spec run 1 executes
  - docs/inbox/owner-questions.md                              # oq-0024 — the question SE-1 disposes
supersedes: null
superseded_by: null
warrant: null
---

# The σ-sweep experiment: a pre-registered protocol for run 1 (SE-1..SE-4)

> Composed at **fable** (`claude-fable-5`/xhigh, 2026-07-17, owner-chartered: "design the
> experiment to accurately and reliably produce reports, test our theories"). Filed as `draft`.
> **Ratification here has a specific meaning: it FREEZES the pre-registration** — hypotheses,
> decision rules, and bars below become immutable for run 1; any post-freeze deviation is a
> finding, never a silent analysis change. The RUN itself remains an owner-fired act (the
> selfmod master switch is the owner's, per non-negotiable 5); `/graduate` refuses this note
> until ratified. Design only; the single thin build item is licensed in §3, not performed.

## 1. Purpose and scope

The σ-sweep has been staged since the harness landed; what was missing was not the machine but
the *protocol* — the difference between running a sweep and running an **experiment**. This
note pre-registers run 1: four hypotheses (SE-1..SE-4) with frozen decision rules, five
validity criteria (V1..V5) checked before any hypothesis is read, a report contract, and the
phase-B re-analysis hooks that let the connectivity instruments (dn-connectivity-instruments,
once ratified and built) re-read this run's data without re-running it.

**The theories under test, named:** oq-0024/finding-0079 (does σ have a value worth moving
to?); dn-sigma-fibers on *real* data for the first time (is there multiscale signal in the
live corpus, and does the shipped gate stay honest outside its fixtures?); and — as recorded
descriptive riders — the first real readings of the conductance-flavored axis that phase B
will formalize. **Out of scope:** any θ/lever retune inside the run (a lever change is a
separate owner-visible act); unattended selfmod (never); phase-B instruments before their
tranche; any build beyond §3's one thin wiring item.

## 2. Principles / decision

### 2.1 Validity criteria V1–V5 (run-validity; checked before any hypothesis is read)

- **V1 — environment pinning.** Every reading carries: config fingerprint, `lever_registry_hash`,
  corpus digest, commit SHA, and the declared σ-grid (`fibers_spec_hash` / the FibersEvidence
  pattern, already built). A reading missing its evidence block is malformed.
- **V2 — cut indexing (the quartet's operational debut).** The mirror snapshot is taken at a
  **certified cut** (GC-3); the cut's frontier and certificate set are recorded in the run
  evidence. "The corpus this run measured" is thereby an honest, reproducible object — the
  first production use of bp-055.
- **V3 — the control battery (instrument integrity before data).** bp-057's synthetic fixtures
  (pure-noise + planted two-cluster) run through the SAME pipeline version first; all three F9
  criteria must reproduce (noise SETTLED ≈ 0; planted reach SETTLED; tiering beats the best
  single-σ baseline). **Controls fail ⇒ the run is INVALID regardless of real-data output** —
  stop, finding, no hypothesis is read.
- **V4 — determinism.** Seeds pinned (the spec's 5); `MirrorGraph` is deterministic given row
  order; one duplicated (σ, seed) cell is re-run as a spot check and must agree bit-wise.
- **V5 — selfmod posture.** `enabled = true, unattended_enabled = false` (propose-only): SE-1's
  selection emits a `ProposedChange` into the §14 ledger for owner blessing. Fallback:
  `enabled = false` runs as a preview (SE-1's proposal step deferred; SE-2..SE-4 unaffected).
  Auto-apply: never.

### 2.2 Hypotheses (frozen at ratification)

**SE-1 — the σ value (disposes oq-0024).**
*Theory:* `dream_rnd_sigma` has a non-degenerate response on the clean graph; a plateau-
centered value exists. *Measurement:* the sweep exactly as specced (grid 21 over [0.55, 0.75],
5 seeds, phase7/dream_v2 A/B, objective `golden_recall`, `select_pipeline = dream_v2` per
finding-0089). *Analysis:* **the optimizer's own rule, verbatim and unmodified**
(`eval/harness/sweep.py`: admissibility lexicographically prior — a cell whose `golden_recall`
regresses below baseline is inadmissible before any argmax; widest near-optimal plateau center
within ε; least-motion tie-break). No post-hoc re-analysis. *Decision rule:*
(a) selection ≠ current default AND plateau width ≥ 3 admissible cells ⇒ the emitted proposal
stands for owner blessing — oq-0024's VALUE axis closes;
(b) curve flat within ε across admissible cells ⇒ oq-0024 retires as "insensitive in-range;
default stands" — **a completion, not a failure**;
(c) every cell inadmissible ⇒ STOP, finding (the lane is mis-tuned more deeply than σ; do not
select).

**SE-2 — real multiscale signal (dn-sigma-fibers' first real dataset).**
*Theory:* the σ-hierarchy carries non-degenerate structure on the live corpus. *Measurement:*
the built `FibersConsumer` over the run's retained cells → the registered
`sigma_persistence.{mean, p50, max, frac_ge_strong, n_claims}` per pipeline. *Decision rule:*
non-degeneracy = pers variance > 0 AND not all claims at pers = 1 AND `n_claims ≥ 10` per
pipeline. Below the floor ⇒ "insufficient claims at this corpus size" — parked on the
corpus-growth re-entry (bp-057's own park taxonomy, reused). *Pre-registered caveat:* if
degeneracy traces to claim-identity flicker across cells, that is **SF-a's re-entry** — file
the finding naming it; never patch identity ad hoc inside the run.

**SE-3 — gate calibration on real claims, with the owner as blinded judge.**
*Theory:* the shipped gate's tiers are meaningful outside its fixtures (the apophenia gate
holds on real data). *Measurement:* `assign_tiers` at the **frozen** θ defaults over SE-2's
fibers; occupancy counts; tier stability across seed-majority reruns; and the **blind
judgment**: up to 24 claims sampled stratified across tiers (8/8/8 or as available),
presented **unlabeled, in seeded-random order**; the owner rates each `real connection /
plausible / noise`; unblinding only after all ratings are recorded. *Pre-registered bars:*
SETTLED occupancy ≤ 20% of claims (the apophenia cap); tier stability ≥ 80%; SETTLED median
rating > RETAINED median; ≥ 70% of SETTLED rated at least `plausible`; > 2 SETTLED rated
`noise` trips a finding. *Honesty label:* single-subject calibration evidence, not inferential
statistics — recorded as such. *Action:* bars pass ⇒ the gate's first real-data validation
rung is recorded. Any bar fails ⇒ finding + owner decision; **θ moves only as a subsequent
lever act, never inside the run.**

**SE-4 — descriptive riders (exploratory by declaration; no decisions attached).**
`structural_axes.{frustration, min_conductance}` per cell (min_conductance is already
registered — the conductance family's first real readings, ahead of its formal instruments)
and `drift_D` (advisory). Curve shapes vs σ are recorded for phase-B comparison. The
exploratory/confirmatory line is drawn here, at ratification — these generate phase-B
hypotheses; they decide nothing in run 1.

### 2.3 The report contract

One composite report per run, content-addressed, assembled from: the E4 A/B report; the curve
+ selection (+ the proposal id if emitted); the fibers summary; tier occupancy + stability;
the control-battery outcomes; the V1–V5 evidence block (including the certified cut); and —
after unblinding — the blind-judgment record. All numeric readings land in the eval store
under **registered names only** (registry discipline; no ad-hoc metric emission). The run
journal records: the pre-registration commit SHA (the frozen version of THIS note), the run
command, every deviation (each one a finding), the SE-1..SE-4 outcomes, and the oq-0024
disposition. Re-runs under changed config are run 2 with their own journal — runs are
append-only, never overwritten.

### 2.4 Phase B (re-entry: dn-connectivity-instruments ratified + its tranche built)

V1/V2/V4 make re-analysis free: the pinned snapshot + grid + determinism reproduce every
per-cell graph without re-running the dreamer. Phase B re-reads this run with: σ\*/MST
ultrametrics over the same graphs; (σ,t) conductance profiles compared against the recorded
`min_conductance` axis; per-stratum `χ_s` sequentiality; a reconnection scan between this
run's cut and a later one. **One linkage question is pre-registered NOW so it stays
confirmatory then:** *does SE-1's selected σ sit within the principal merge band of the σ\*
distribution?* (The plateau ↔ merge-structure hypothesis — the sweep meeting CN-2.)

## 3. Consequences

- **The RUN** — owner-fired: `uv run scripts/sweep.py config/sweeps/dreamer-sigma-ab.toml`,
  selfmod per V5. Scheduler-fired recurrence stays parked (§4).
- **One thin build item** post-ratification (~100–120k, eval/scripts write scope, no core):
  the control-battery pre-flight command (V3 as one invocation); the blind-sample generator
  (deterministic, seeded, labels sealed to a file opened only after rating); the composite
  report assembler (§2.3). Everything else this experiment needs is already built.
- **Ratification = freezing.** After the owner's hand edit, §2's rules and bars are immutable
  for run 1; deviations are findings; changes for run 2 are a note update ratified again.

## Parked decisions

| Decision | Default | Re-entry |
|---|---|---|
| scheduler-fired recurring runs | manual owner-fired runs | two clean manual runs (then the scheduler variant is a small owner-visible plan) |
| `f9_composite` as the objective | `golden_recall` (registered AND written per cell) | the E5/E7 per-cell F9 wiring the spec's banner names |
| phase-B instruments in the loop | recorded riders only (SE-4) | dn-connectivity-instruments ratified + tranche items 1–2 built |
| θ retuning | frozen defaults through run 1 | a separate owner-visible lever act, informed by SE-3's record |

## Cross-references

- **Code (all built):** `eval/harness/sweep.py:14-16,89-90,171-176` (admissibility-prior
  optimizer, ε/plateau/least-motion, `select_pipeline`) · `eval/harness/fibers.py`
  (`FibersConsumer.consume`, `fibers_spec_hash`, `lever_registry_hash` — V1's evidence) ·
  `eval/harness/registry.py:68,76,82,124-132,137` (`golden_recall`, `drift_D`, `f9_composite`
  banner, `sigma_persistence.*`, `structural_axes.{frustration,min_conductance}`) ·
  `eval/harness/gate.py` (`assign_tiers`, frozen θ THRESH) · `core/temporal/spine.py`
  (`CertifiedCut` — V2) · `core/dreaming/graph.py:25-33` (`MirrorGraph.build`, deterministic —
  V4) · `scripts/sweep.py` (the entry; seal-first; propose-only emission).
- **Artifacts:** oq-0024 / finding-0079 (the question) · finding-0089 (`select_pipeline`) ·
  bp-049 (optimizer) · bp-050 (fibers) · bp-054 (registry rows) · bp-055 (cuts) · bp-057 (gate
  + the F9 fixture battery V3 reuses) · dn-connectivity-instruments (phase B).
