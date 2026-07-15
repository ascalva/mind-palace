# Brainstorm — The evaluation / test harness (consolidation synthesis)

> Topic capsule opened 2026-07-15 (orchestrator, opus). Warrant for a consolidated harness design
> note. Owner directive: "testing becomes essential — we've built a unified query language, a second
> dreamer is coming, lots more dreaming machinery; as the system gets sophisticated we need more
> sophisticated tools to properly and thoroughly test." Wants: proper **metrics, benchmarks, telemetry
> extraction, audit logs, report generation, parameter tweaking + AUTOMATED parameter tuning**. And:
> **"I don't mind running the harness/tests overnight"** — the cost ceiling on *running* is lifted.
> Two thorough Explore sweeps (design-intent + built-machinery) fed this.

## 2026-07-15 — the landscape (what exists, what's designed, the gap)

### The through-line is real — three waves, never consolidated
1. **Wave 1 (taxonomy):** `holistic-testing.md` ("test the process, not just the product"; property/
   metamorphic/adversarial/emergent/**attestation-as-oracle**/longitudinal), `test-organization.md`
   (tests by execution profile; built-wired), `alignment-subsystem.md` (the drift gauge + frozen fixed
   points).
2. **Wave 2 (executable capability tests):** F9 `dreamer-quality-suite-evaluation.md` (apophenia /
   signal-vs-noise; **built-wired**; established the tuning philosophy: *"thresholds are tuning, not code
   — `THRESH` driven by the longitudinal harness exactly like γ/λ/σ/Θ"*), `supersession-recovery-
   evaluation.md` (the first labeled, leak-controlled capability eval — "instance #1").
3. **Wave 3 (the two harness generalizations — LOAD-BEARING, both draft, both NOT built):**
   - **`capability-evaluation-harness.md`** — the OFFLINE capability spine: a uniform masked-replay
     substrate, a typed transformation algebra (`subset/mask/scrub/inject/flip/permute/freeze`), an
     **ablation ladder r0→r8** (attributes each score to the instrument that earned it), a six-battery
     capability catalog, an append-only **eval-results store** keyed by `(spec, fixture, corpus-state,
     instrument-config, seed)`. "Which capabilities does the system demonstrably have, at what scale,
     and which instrument is responsible?"
   - **`live-adoption-and-longitudinal-harness.md`** ("Track L") — the OPERATIONAL/longitudinal spine:
     shadow runner + run ledger (L1), verdict store + review REPL (L2), **tuning manifest + gated apply
     (L3)**, longitudinal metrics/curves + control corpus (L4/F4), continuous digest (L5). *"the strong
     Dreamer running continuously on the live mirror, tuned against owner verdicts, measured over
     time… the harness's unit of evidence is a CURVE."*

**The seam to fill:** the two notes already declare they share machinery (replay substrate, run ledger,
eval-results store) — `capability-evaluation-harness.md` §9: *"build it once… Verdict prediction and
longitudinal calibration are Track L's first passengers"* — but were **never merged into one subsystem
note**. And the newest ratified instruments (velocity / temporal-geometry) + the self-sensor telemetry
streams **postdate both** and aren't in either catalog. That un-consolidated seam + the autonomous-tuning
gap is exactly what the new note fills.

### The architecture the notes converge on: instrument → harness → report
- **Instruments** = deterministic, read-only measurements. Each produces ONE reading.
- **Harness** = schedules instruments, keys every reading by `(spec, fixture, corpus-state, config,
  seed)`, turns single readings into **curves** (append-only eval-results / run ledger).
- **Reports** = curves → sparklines + static HTML/markdown into `data/reports/` (local, **no egress**).

### The instrument catalog (built vs flag-off)
- **BUILT + WIRED:** the frozen **golden set** (`eval/golden/**` — 6 synthetic notes, 5 queries,
  `baseline.json`; a SACRED fixed point, never auto-modified, structurally excluded from every grant) +
  the **A1 drift gauge** (`eval/drift.py`: `D(t)=d(μ(sₜ),B)` vs frozen anchor B, tolerance Θ; wired into
  the self-mod validator). Attestation/proposal/run ledgers. Telemetry DuckDB (`vitals` + `context_usage`).
  Self/code sensors → observation stores. OpsView/DreamsView/`build_status`.
- **BUILT but FLAG-OFF / UNWIRED:** the **structural SnapshotStore** (A2 drift axes — β₀/Fiedler/
  frustration/curvature/SBM/conductance/H₁; only written in dream_v2, `build_dreamer` doesn't pass it),
  **effector_drift** (`eval/effector_drift.py`, detection-only, out of the gate), **CoherenceReport / β₁**
  citation instruments (no live caller), the **dream_rnd adjudicator confidence** panel.
- **RATIFIED, design-only (new instruments to fold in):** `dn-velocity-instruments` (RotationReport,
  alive/stale hole discriminator — both Inv-typed, measurement-class per X2), `dn-temporal-geometry` (the
  demon-vs-source experiment is explicitly *"an eval-harness item"*), the **Inv/Rate(κ) result typing**
  (`dn-capability-scope` §2.3 — the type discipline for which readings compare across anchors; dedup
  type-directed). **A2 is the extensibility contract:** any new instrument enters as a drift `Axis` μ absorbs.

### Telemetry & audit (built spine the harness consumes)
- **Audit = the attestation layer** (`core/attestation/**`): Ed25519-signed, content-addressed,
  append-only `(agent, op, input-hashes, output-hash, auth, Constitution-fingerprint)`; **attestation-as-
  oracle** (the system proves its own correct behavior through the records it generates). Owner tool
  `scripts/verify_attestation.py`. Plus the proposal ledger (§14 audit) + run ledger.
- **Telemetry = the sensor streams:** φ_self (cost: frontmatter → `AgentObservationStore`), φ_code (repo →
  `CodeObservationStore` + reference edges), the DuckDB `context_usage` (agent/tier/tokens/retrieved).
  Routing pinned: *telemetry/time-series → DuckDB; ledgers → SQLite.*
- **Gaps:** no `/usage` CLI, no seal-cost store (cost lives only in the `cost:` observation stream), no
  markdown report generator, `sensor_readings` table has no writer.

### Parameter tuning — the owner's headline ask (and the biggest gap)
- **The lever surface (BUILT):** `ops/levers.py` — 4 bounded `[dreaming]` levers (σ [0.55,0.75],
  near_dup [0.90,0.99], min_cluster_size [2,6], max_clusters [4,16]); `config/levers.toml` machine-overlay
  (under `local.toml` so the human always wins); the **§14 gate** (`ops/selfmod.py`: propose→approve→
  execute→validate-against-golden/drift→keep-or-**auto-rollback**; two fail-closed switches
  `[selfmod] enabled=false`, `unattended_enabled=false`; `SAFE_LEVERS={dream_max_clusters}` the sole
  unattended knob).
- **DESIGNED (L3):** the tuning manifest (`config/tuning.toml` + ranges + `scripts/tune.py show/set/
  history/--revert`, attested, config-fingerprinted) — *"tuning efficacy is measured, not vibed."*
  Sweeps designed in two places: the shadow-runner σ-sweep (L1, "3–5 values, cheap") + **finding-0079's
  σ-sweep methodology** (sweep [0.55,0.75], record graph + dreams, pick by the curve, repeatable — the
  ready-made template). A/B is native (interleaved-labeled review REPL; adoption = one pure function over
  the ledger).
- **THE GAP (undesigned frontier — what the owner wants):** **automated / autonomous parameter
  optimization.** `live-adoption` §7: *"No verdict-driven automatic retuning… an auto-optimizer over
  verdicts is a future proposal that would itself need the self-mod gate."* Today = human-on-the-`set`.
  The owner wants to **automate the tweaking** → design a bounded **multi-point sweep + optimizer** that
  MEASURES autonomously (sweep instruments over a lever grid, build the curve) and PROPOSES the curve-
  optimal value — but the APPLY stays §14-gated (owner blesses the `set`). The overnight mandate makes
  exhaustive sweeps (full grids, ablation ladders, many-run curves) affordable to RUN.

### Constraints any harness design MUST honor (BUILD-SPEC §3 + self-imposed)
1. **Sacred fixed points (Inv 9):** golden set + B/Θ + Constitution never auto-modified; the harness
   MEASURES against them, never writes near them (structurally excluded from the fullest grant, CQ-scope
   §64). Θ is owner-blessed, harness-advisory.
2. **Eval isolation (soundness invariant):** no eval run ingests or promotes ANYTHING, ever; scratch
   replay in the `dream_rnd` lane; external corpora → scratch complexes only.
3. **Mirror firewall:** verdicts / eval-results / shadow output ∉ `MIRROR_READABLE` (operational ground
   truth, not mirror content); control corpus in its own CURATED graph.
4. **Sealed core zero egress; reports are local files, no serving.**
5. **Model advises, code acts:** instruments deterministic + read-only; the review path model-free.
6. **Self-mod gate (Inv 5)** bounds all automated tuning; **memory ceiling ≤2 models** bounds sweep cost.
7. **Control-corpus separation:** founding corpus ≠ Track-L control ≠ per-test eval fixtures (three
   artifacts, three lifecycles). **Regression-shaped, not threshold-shaped** assertions at 13-note scale.

### The overnight mandate (new, 2026-07-15) — a design principle
The owner will run the harness/tests overnight → **design for thoroughness over cheapness.** The existing
notes' "3–5 σ values, background priority, cheap" was a scale-constrained compromise; lift it: full σ
grids, complete ablation ladders (r0→r8), long longitudinal curves, big benchmark batteries, dual-dreamer
A/B at many σ. Still bounded by the memory ceiling (≤2 models) and local compute — but wall-clock is no
longer the constraint. (Claude budget is NOT the constraint for RUNS — the dream synthesis is local 27b.)

### What the consolidated note (`dn-evaluation-harness`) should do
1. **Unify the two frames** (offline capability + operational longitudinal) as two halves of one
   subsystem over ONE shared replay substrate + eval-results store + run ledger.
2. **Fold in the new instruments** (velocity/temporal-geometry, structural snapshots, effector drift) +
   the Inv/Rate typing as the instrument-catalog discipline; wire the flag-off ones into the catalog.
3. **Integrate telemetry & audit** (sensor streams, DuckDB, attestation-as-oracle) as the harness's own
   evidence substrate.
4. **DESIGN the automated-tuning layer** (the gap): a bounded sweep + optimizer that autonomously
   MEASURES over a lever grid and PROPOSES, apply stays §14-gated. This is the note's novel core.
5. **Report generation:** markdown/JSON + sparkline curves + the drift study → `data/reports/` (no egress).
6. **Testing the NEW machinery specifically:** CQ-scope (property tests on the scope algebra, Views as
   instances), the dual dreamers (Phase-7 vs dream_v2 A/B, σ-sweep, F9 quality), the growing dream tools.
7. **Honor every constraint above**; name what stays owner-gated vs what automates.
8. **Consequences:** the build decomposition — the shared eval-results store, the sweep/optimizer, the
   report generator, wiring the flag-off instruments, the longitudinal run ledger. bp-040 `dream-calibrate`
   becomes ONE instance/component under this (the dual-dreamer σ-sweep); it should be re-derived from the
   note, not built ad-hoc.

### Open questions for the design pass
- **How autonomous is "automated tuning"?** The optimizer MEASURES + PROPOSES autonomously; does it ever
  auto-APPLY within a pre-blessed band (a bounded auto-`set` under §14's `unattended_enabled`), or is
  every `set` owner-hand? (The owner said "automate the tweaking" — clarify the ceiling.)
- **Supersede or umbrella?** Does `dn-evaluation-harness` SUPERSEDE the two draft harness notes (fold
  their detail in) or sit as the unifying spine that cites them? (They're drafts, so supersedable.)
- **Objective function for the optimizer:** what curve does it optimize — golden recall? F9 quality?
  owner-verdict rate (needs L2 verdicts first)? a composite? At 13-note scale, regression-shaped.
- **Tier to write the note:** fable-grade design (the hardest kind); fable resets Jul-17 (~2 days). Bank
  now (this capsule), fable-pass post-reset for top quality — or opus draft now.

## 2026-07-15 — OWNER DECISIONS (via AskUserQuestion) — the Fable pass is queued

- **WRITE AT FABLE — NOW, on usage credits** (owner update 2026-07-15: "I have usage credits to design
  the harness" — so the pass runs immediately on credits rather than waiting for the Jul-17 fable-weekly
  reset). This capsule is the warrant; the consolidated note `dn-evaluation-harness` is written at
  Fable+xhigh in a fresh session bootstrapped by `.claude/state/resume-brief.md`. The brainstorm→design
  fable-guard is satisfied by this being a Fable pass. (Opus-now was declined in favor of Fable.)
- **AUTOMATED-TUNING AUTONOMY = DESIGN BOTH, OWNER PICKS PER-LEVER.** The note specifies BOTH modes and
  makes per-lever autonomy a **config choice**: *measure+propose* is the default (the optimizer sweeps a
  lever grid, builds the curve, PROPOSES the curve-optimal value; every `set` is an owner §14 hand-
  blessing); *bounded auto-apply* is opt-in per lever (within a pre-blessed band + the frozen golden/drift
  guardrails, the loop may auto-`set` and auto-rollback on any regression — the `SAFE_LEVERS` /
  `unattended_enabled` shape, generalized per-lever). The note must specify the per-lever autonomy field,
  its bounds representation, and that the never-tunable fixed points (golden/Θ/Constitution/gate
  predicates) cannot express either mode (structurally unrepresentable).
- **Overnight-run mandate confirmed** (owner reaffirmed 2026-07-15: "I also want this harness built well,
  I don't mind running the harness/tests overnight") — design for THOROUGHNESS: full σ grids, complete
  r0→r8 ablation ladders, long longitudinal curves, dual-dreamer A/B at many σ. Wall-clock is not the
  constraint; the memory ceiling (≤2 models) + local compute still are. Claude budget is NOT a run cost
  (dream synthesis is local 27b).
- **bp-040 `dream-calibrate` is SUBSUMED** — it becomes ONE component (the dual-dreamer σ-sweep instance)
  under the harness design, re-derived from the ratified note rather than built ad-hoc/standalone. Held
  at `proposed`, NOT built, pending `dn-evaluation-harness`.
- **Remaining open (for the Fable pass):** supersede-vs-umbrella (the two draft harness notes are
  supersedable); the optimizer's objective function (golden recall / F9 quality / owner-verdict rate —
  needs L2 verdicts first / a composite; regression-shaped at 13-note scale).
