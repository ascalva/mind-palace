---
type: experiment-run-journal
experiment: dn-sigma-sweep-experiment
run: 1
pre_registration_sha: d932670          # the FROZEN pre-registration this run MUST obey (note §2.3)
status: sealed                         # pre-flight → running → analyzed → sealed (2026-07-17)
started: 2026-07-17
links:
  - docs/design-notes/sigma-sweep-experiment.md   # RATIFIED, FROZEN @ d932670 — the authority
  - config/sweeps/dreamer-sigma-ab.toml           # the frozen sweep spec run 1 executes
  - docs/inbox/owner-questions.md                 # oq-0024 — SE-1 disposes it
---

# σ-sweep experiment — RUN 1 journal

**Authority:** the RATIFIED, FROZEN pre-registration `dn-sigma-sweep-experiment` at commit **`d932670`**.
Every rule below is read off §2.2/§2.1 verbatim. **Any deviation from the frozen protocol is recorded
here as a finding — never a silent analysis change (§2.3).**

## Environment
- Daemon QUIESCED for the run: `palace stop` (drain) → `palace down` (bootout, outlasts KeepAlive).
  Rationale: V2's certified cut requires quiescence (trough-empty ∧ handoff-empty); a live dreamer
  would keep them non-empty and mutate the corpus mid-sweep. Bring back with `palace up` after sealing.
- Vault / backup / token-rotate agents remain up (they do not mutate the corpus).
- HEAD at run time: `214eaf4` (recorded in V2's cut evidence).

## Pre-flight — V1–V5 (note §2.1, checked BEFORE any hypothesis is read)

- **V1 — environment pinning.** Auto-captured into the composite's evidence block from the fibers
  evidence: config_fingerprint, `lever_registry_hash`, corpus_ref (merkle), the σ-grid (21 pts over
  [0.55,0.75]), and `fibers_spec_hash` per pipeline; commit SHA passed in. STATUS: wired ✓ (populated
  at report-assembly time).
- **V2 — certified cut (bp-055's production debut).** DERIVED + CERTIFIED 2026-07-17:
  - `SpineSources.resolve(cfg)` enumerated: versions, ledger, derived, attestations, eval, catalog.
  - `Spine.derive(sources, cut_sources=CutSources(commit_sha=214eaf4…)).cut_at(strata={"mirror"})`.
  - **certificates:** `['commit']` (the COMMIT certificate the mirror stratum requires).
  - **frontier:** 13 per-doc version chains (the corpus = 13 documents at their version positions).
  - **evidence:** `commit:214eaf485df3e617aa9fbe65ef07140a6b98339e`.
  - This IS "the corpus this run measured" as an honest, reproducible object. STATUS: ✓ CERTIFIED.
- **V3 — control battery (instrument integrity before data).** `uv run scripts/experiment.py controls`
  → **GREEN** 2026-07-17: (i) noise SETTLED rate 0.0000 (≤0.05); (ii) planted reached SETTLED True;
  (iii) tiered precision 1.0000 > best single-σ 0.6667. All three F9 criteria reproduce. STATUS: ✓ GREEN.
  (Controls RED would have made the run INVALID — stop, finding, no hypothesis read. Did not occur.)
- **V4 — determinism.** Two in-memory drives of cell (σ=0.65, seed=2) produced BIT-WISE IDENTICAL
  dream_v2 claim-id sets (10 = 10). `MirrorGraph` determinism confirmed. STATUS: ✓ PASS.
- **V5 — selfmod posture.** OWNER-BY-HAND: `config/defaults.toml:251` `enabled` (line 252
  `unattended_enabled` stays false). `enabled=true` ⇒ SE-1 emits a `ProposedChange` for owner
  blessing (propose-only). `enabled=false` ⇒ preview (SE-1's proposal step deferred; SE-2..SE-4
  unaffected). Auto-apply: never. **DECISION: propose-only** — owner flipped `enabled=true`
  (unattended stays false), verified via the config loader (`selfmod.enabled=True`). STATUS: ✓ set.

## The run
- Command (owner-fired): `uv run scripts/sweep.py config/sweeps/dreamer-sigma-ab.toml` — FIRED 2026-07-17.
- Result: 210 run-ledger rows (105 phase7 + 105 dream_v2 = 21 σ × 5 seeds × 2 pipelines); 212
  golden_recall readings. corpus_ref `1b8d9d1e…` (13-doc mirror, matching V2's 13-chain cut).
- ALL FIVE validity criteria hold (V1–V5) → the run is VALID.

## Deviations (each a finding)
- **finding-0097** — SE-1 rules (a) and (b) are NOT mutually exclusive on a PERFECTLY FLAT curve:
  the plateau-center (0.65) ≠ default (0.62) satisfies (a)'s literal conditions, while (b)'s "flat
  within ε" also holds. RESOLUTION (recorded, not silent): **(b) governs** — a flat curve carries no
  signal that could justify a move. The sweep engine emitted proposal #1 mechanically (it has no
  flat-curve carve-out); the FROZEN analysis DECLINES it. Routes to orchestrator; informs a run-2
  note update.

## Outcomes — SE-1..SE-4 (analyzed STRICTLY per FROZEN §2.2)
- **SE-1 (σ value; disposes oq-0024) → RETIRE per rule (b).** golden_recall = **1.0000 across ALL 21
  σ-cells** (halfwidth 0, every cell admissible). The curve is flat within ε ⇒ rule (b): "insensitive
  in-range; default stands — a completion." **Proposal #1 (`dream_rnd_sigma 0.62→0.65`, status
  `proposed`, propose-only) is DECLINED** (see finding-0097). The default **σ = 0.62 stands**.
  ROOT CAUSE recorded as **finding-0096**: golden_recall is SATURATED at this corpus scale (13 docs)
  — the objective has zero discriminating power, so "insensitive" is objective-saturation, NOT
  σ-invariance of the underlying structure (SE-2 proves structure IS σ-sensitive).
- **SE-2 (real multiscale signal) → dream_v2 PASSES; phase7 parked.** dream_v2: n_claims=32 (≥10),
  pers mean 0.235 / p50 0.190 / max 1.000 / frac_ge_strong 0.063 — variance>0, not-all-pers-1,
  ≥10 floor ⇒ **NON-DEGENERATE. dn-sigma-fibers' first real dataset, positive.** phase7: n_claims=8
  < 10 ⇒ below floor ⇒ "insufficient claims at this corpus size" — parked on the corpus-growth
  re-entry (SE-2's own rule). No claim-identity flicker observed (seed-invariant paths; SF-a not
  triggered).
- **SE-3 (gate calibration; owner as blinded judge) — occupancy + stability PASS; ratings pending.**
  dream_v2 tiering at frozen θ (θ_weak=2/21=0.095, θ_strong=0.5): SETTLED 2 / HUNCH 26 / RETAINED 4.
  SETTLED occupancy = **0.0625 ≤ 0.20** (apophenia cap) ✓. Tier stability **100% ≥ 0.80** ✓
  (seed-invariant paths ⇒ tiers identical across seed-majority reruns). The 2 SETTLED: a `theme`
  (pers 1.0, persists the whole grid) + a `centrality` (pers 0.62). **Blind judgment: 14 claims
  (2 SETTLED / 8 HUNCH / 4 RETAINED) sampled (seed 20260717); owner rates BEFORE unblinding.** The
  rating bars (SETTLED median > RETAINED; ≥70% SETTLED ≥ plausible; >2 SETTLED-rated-noise ⇒ finding)
  resolve once ratings are recorded. Single-subject calibration evidence, labelled as such.
  **RATINGS RECORDED (owner, blind, then unblinded; legend 0=noise/1=real/2=plausible):** SETTLED
  both `plausible` (median q=1.0); RETAINED 3×plausible + 1×real (median q=1.0); HUNCH 5 plausible /
  2 real / 1 noise. **Bar (1) SETTLED median > RETAINED median: FAIL** (1.0 = 1.0). **Bar (2) ≥70%
  SETTLED ≥ plausible: PASS** (100%). **Bar (3) SETTLED-rated-noise: 0, no trip.** ⇒ a bar failed ⇒
  **finding-0098** + owner decision (θ does NOT move in-run, frozen). VERDICT: the apophenia guard
  HOLDS (SETTLED never noise), but persistence-tier does not yet discriminate owner-perceived realness
  at 13-doc scale (compounded by the rater not recalling the notes → ratings compressed to plausible).
  Gate's real-data rung recorded as "guard holds; discrimination unproven at scale" — a PARK (the
  gate's surfacing API was already closed). Re-entry: larger corpus + more claim context in the sheet.
- **SE-4 (descriptive riders; decide nothing) — recorded.** `structural_axes.frustration` = 0.0 on
  every cell (no community frustration on this corpus); `structural_axes.min_conductance` ∈ {0.0, 1.0}
  (bimodal — perfect bottleneck or fully connected). Curve shapes vs σ recorded for phase-B.

## oq-0024 disposition
- **RETIRED — "insensitive in-range; default (0.62) stands" (SE-1 rule (b)). A COMPLETION, not a
  failure.** Caveat (finding-0096): the insensitivity is golden_recall SATURATION at 13-doc scale,
  not evidence σ is structurally inert (SE-2 shows σ-sensitive structure). Re-entry for a future
  σ question: a discriminating objective (the parked `f9_composite`/per-cell F9 wiring) AND/OR a
  larger corpus. Proposal #1 stays `proposed` and unblessed (owner may formally reject it in the
  §14 ledger).

---
## SEALED 2026-07-17. Run 1 VALID (V1–V5 all hold). Composite: data/reports/2026-07-17-sigma-run1/composite.{md,json}.
**Headline:** oq-0024 RETIRED (σ insensitive in-range per SE-1(b); default 0.62 stands) — but the
insensitivity is golden_recall SATURATION at 13-doc scale (finding-0096), NOT structural. SE-2 shows
dream_v2 carries REAL σ-sensitive multiscale structure (n=32, non-degenerate). SE-3: apophenia guard
holds (no SETTLED-noise) but persistence-tier doesn't discriminate realness at this scale (finding-0098).
Findings: 0096 (objective saturation) · 0097 (SE-1 (a)/(b) flat-curve precedence) · 0098 (SE-3 discrimination).
Proposal #1 (0.62→0.65) declined per SE-1(b); stays `proposed`-unblessed in the §14 ledger. **The
convergent signal from all three findings: the 13-doc authored mirror is too small + too homogeneous —
the corpus-scale / cross-strata substrate is the re-entry (owner direction 2026-07-17).**
