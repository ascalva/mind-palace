---
type: build-plan
id: bp-058
alias: sigma-sweep-experiment-wiring
status: proposed
design_ref:
  - docs/design-notes/sigma-sweep-experiment.md   # RATIFIED @ d932670 (FROZEN pre-registration) — §2.1 V1–V5, §2.2 SE-1..SE-4, §2.3 report contract, §3 licenses THIS one thin build item
contract: builder
write_scope:
  - eval/harness/experiment.py
  - scripts/experiment.py
  - tests/unit/test_experiment_controls.py
  - tests/unit/test_experiment_blind.py
  - tests/unit/test_experiment_report.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 150k
  actual: null
depends_on: [bp-049, bp-050, bp-054, bp-055, bp-057]
parallelizable_with: []
created: 2026-07-17
updated: 2026-07-17
links:
  - config/sweeps/dreamer-sigma-ab.toml                          # the frozen sweep spec run 1 executes
  - docs/design-notes/evaluation-harness.md                      # E4 report contract this assembler composes over
  - docs/design-notes/sigma-fibers-and-multiscale-dreaming.md    # §2.5 the gate SE-3 exercises; the fibers SE-2 reads
  - docs/design-notes/dreamer-quality-suite-evaluation.md        # F9 — the control battery V3 reuses (bp-057 fixtures)
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — bp-058: the σ-sweep experiment wiring (V3 controls · blind sample · composite report)

## 0. Mode & provenance
Graduated from the RATIFIED, FROZEN pre-registration `dn-sigma-sweep-experiment` (commit `d932670`).
Investigation and planning produced this; implementation proceeds item-by-item on owner approval.
Authority-to-act (the owner's charter to build the experiment machinery) is separate from the
readiness blessing (`proposed → ready` is OWNER-ONLY, by hand — no agent flips it). **This plan
builds instrumentation ONLY — it does not run the experiment** (the run is owner-fired per V5 and
non-negotiable 5) and it changes no analysis rule (every rule is frozen in the note §2.2). Write
scope is `eval/harness/` + `scripts/experiment.py` + three unit tests; **no `core/`**, no config,
no sweep spec, no design note.

## 1. Objective
Build the one thin wiring item the note §3 licenses: (a) a **control-battery pre-flight** command
that runs bp-057's noise + planted fixtures through the CURRENT pipeline and reproduces all three F9
criteria as one GREEN/RED invocation (V3); (b) a deterministic, seeded **blind-sample generator**
that emits ≤24 tier-stratified claims unlabeled in seeded-random order with labels SEALED to a
separate file (SE-3); (c) a deterministic, model-free **composite report assembler** that renders the
§2.3 contract (E4 A/B + curve/selection + fibers + tier occupancy/stability + control outcomes + the
V1–V5 evidence block incl. the certified cut + the post-unblinding blind-judgment record) over
registered readings only.

## 2. Context manifest (read in order)
1. `docs/design-notes/sigma-sweep-experiment.md` (WHOLE — the FROZEN authority: §2.1 V1–V5, §2.2
   SE-1..SE-4 decision rules, §2.3 the report contract, §3 the single licensed build item).
2. `eval/harness/sweep.py` — `SweepResult`, `CurvePoint`, `SweepEngine`, `run_sweep` (SE-1's curve +
   selection; the report reads its verdict, never re-derives it).
3. `eval/harness/fibers.py` — `FibersConsumer`/`run_fibers`, `FibersResult`, `ClaimFiber`,
   `FibersEvidence`, `fibers_spec_hash`, `lever_registry_hash`, `render_markdown` (SE-2 + V1's
   evidence + the fibers section).
4. `eval/harness/gate.py` — `assign_tiers`, `Tier`, `TieredClaim`, `thresholds`, `GateValidation`
   (SE-3's tiering + the three ship criteria; the gate mutates nothing).
5. `eval/harness/report.py` — `build_report`, `Report`, `Figure`, `render_markdown`/`render_json`,
   `write_report` (E4 — the A/B report the composite embeds; the "every figure carries its key" +
   "no silent caps" disciplines this assembler inherits).
6. `eval/harness/registry.py` — `is_registered`, `get` (the registered-names-only discipline; the
   documented `structural_axes.*` / `sigma_gate.validation.*` unregistered families).
7. `eval/harness/store.py` — `EvalKey`, `Reading`, `EvalResultsStore.query` (the read substrate).
8. `tests/quality/fixtures_sigma_gate.py` — `PLANTED_ROWS`, `NOISE_ROWS`, `PLANTED_IN_NOISE_ROWS`,
   `phase7_fibers`, `ledger_labels`, `ledger_confidence`, `single_sigma_precisions` (the V3 battery's
   substrate — reuse VERBATIM; do not re-plant).
9. `tests/quality/test_sigma_gate.py:314-351` (`_compute_validation`) — the exact three-criteria
   computation the control battery LIFTS into the harness (today it is private to the quality test).
10. `core/temporal/spine.py:217-229` (`CertifiedCut`) + `:820-846` (`Spine.cut_at`) — V2's certified
    cut (read-only; the assembler RECORDS a cut, never fabricates one; None ⇒ preview).
11. `scripts/sweep.py` — the seal-first / fixture-retriever / config-resolution entry pattern
    `scripts/experiment.py` mirrors.

## 3. Investigation & grounding
- **Q1 — where does the three-criteria control computation already live?** In the quality test as the
  private `_compute_validation()` — `tests/quality/test_sigma_gate.py:314-351`: (i) noise SETTLED
  rate over `NOISE_ROWS`; (ii) planted-reach-SETTLED over `PLANTED_IN_NOISE_ROWS`; (iii) tiered
  precision vs `max(single_sigma_precisions(...))`. The battery must reuse the SAME fixtures +
  `phase7_fibers` + `assign_tiers` + `GateValidation` so "the CURRENT pipeline" is exactly what the
  suite tests — `tests/quality/fixtures_sigma_gate.py:124-205`.
- **Q2 — is the F9 pass a fixed constant or computed live?** Computed live through the BUILT
  `ShadowRunner`/`SweepEngine` each invocation — `fixtures_sigma_gate.py:124-146` drives an in-memory
  sweep. So the battery genuinely re-exercises the pipeline; a pipeline regression reddens it. The
  three ship criteria are `GateValidation.crit_noise_clean / crit_planted_settles /
  crit_precision_gain` — `eval/harness/gate.py:174-192`.
- **Q3 — does the assembler emit new metrics?** No. §2.3: "All numeric readings land in the eval
  store under registered names only." The run's readings (`golden_recall`, `drift_D`,
  `sigma_persistence.*`, `structural_axes.*`) are already written by sweep/fibers; the assembler
  READS them (like `report.py`) and writes ONLY to `data/reports/`. Control outcomes + tier
  occupancy/stability + blind judgments are **report-layer computed values, not eval-store readings**,
  so the registered-names rule (which governs eval-store emission) is satisfied by emitting nothing to
  the store. `sigma_gate.validation.*` is unregistered (bp-057 journal: registration deferred to E6)
  — the assembler treats it exactly as `report.py` treats `structural_axes.*`: read/display without
  `registry.get`, never as a store write — `eval/harness/report.py:25-28,142-145`.
- **Q4 — how is the certified cut obtained in a unit test with no live stores?** It is NOT. `cut_at`
  needs a live `Spine` over real stores (`core/temporal/spine.py:820`). The assembler therefore
  ACCEPTS a `CertifiedCut | None` and records its `frontier`/`certificates`/`evidence` when present,
  or a "preview — no certified cut" note when None (no fabrication; the owner-fired run supplies the
  real cut, V2). Unit tests run in-memory with `cut=None` or a hand-built `CertifiedCut` — the
  5-leg pytest-not-live gate stays clean.
- **Q5 — determinism (V4) at the instrument layer.** The assembler reads no clock and no
  randomness: `date` and `commit_sha` are PASSED IN (the `report.py` pattern — `report.py:88-93`),
  and the blind sample's ordering is a seeded PRNG over a sorted claim list, so identical inputs +
  seed ⇒ identical bytes. `render_json` uses `sort_keys=True` (`report.py:302-304`).
- **Q6 — tier stability's definition (SE-3).** The note says "tier stability across seed-majority
  reruns" but does not fix the partition. GROUNDED DECISION (recorded, §11): stability = the fraction
  of claims whose assigned `Tier` is IDENTICAL between two tierings the CALLER supplies (the
  full-seed tiering vs a leave-one-seed-out majority tiering, or any two the run's 5 seeds license).
  The harness function computes the agreement fraction over the claim-id intersection; the seed
  partition mechanics live in the script. This keeps the harness pure and the definition explicit so
  no builder infers it. The SE-3 bar (≥ 80%) is applied in ANALYSIS (frozen note §2.2), not by this
  code — the assembler REPORTS the number, it does not judge it.

**Additional risks surfaced:** (1) the fixtures module lives under `tests/quality/` — importing it
from `eval/harness/experiment.py` couples a shipped harness module to a test module. MITIGATION: the
import is confined to the control-battery function and is a legitimate reuse of the F9 fixture
substrate (the note §2.1 V3 names bp-057's fixtures as the battery); the alternative — copying the
fixtures into `eval/harness/` — would fork the planted-structure definitions and risk drift from the
suite the battery is meant to mirror. Recorded so it does not read as a layering violation.
(2) No silent caps anywhere (dn-eval-harness §2.8): an undersampled blind stratum, an unregistered
metric, an absent cut, a missing store — each is a recorded note, never a silent drop.

## 4. Reconciliation
None — this plan adds new files and reads built interfaces verbatim; it corrects no committed code
and edits no doc. The one grounded decision (Q6 tier-stability definition) is recorded here and in
§11, not slipped into another module. If SE-1..SE-4 analysis later needs a rule this instrument
cannot express, that is a note update re-ratified for run 2 (note §2.3), never an edit to frozen §2.2.

## 5. Write scope
The five files in front-matter: `eval/harness/experiment.py` (the three pure/deterministic
functions), `scripts/experiment.py` (the thin CLI: `controls` | `blind-sample` | `report`
subcommands, seal-first, config-resolved), and the three unit tests. **OUT (deliberately):**
`core/**` (read-only imports only — the script may import core read paths as `scripts/sweep.py`
does, but writes NOTHING there); `config/**` and `config/sweeps/**` (the spec is frozen);
`eval/harness/sweep.py|fibers.py|gate.py|report.py|registry.py|store.py` (built — consumed verbatim,
never edited); `tests/quality/**` (bp-057's fixtures reused, never modified); every design note; the
foundation denylist (`CONSTITUTION.md`, `eval/golden/**`, `eval/golden.py`). Reports write only into
`data/reports/` (∉ MIRROR_READABLE, local, no egress — the `report.py`/`fibers.py` precedent).

## 6. Interfaces pinned inline
```python
# --- eval/harness/sweep.py (SE-1's verdict — READ, never re-derive) ---
@dataclass(frozen=True)
class CurvePoint:
    value: float | int; mean: float; halfwidth: float
    admissible: bool; grid_index: int; n_seeds: int
@dataclass(frozen=True)
class SweepResult:
    spec_name: str; lever: str; grid: tuple[float | int, ...]; curve: tuple[CurvePoint, ...]
    select_pipeline: str; current: float; selected: float | int | None
    epsilon: float; direction: str; degenerate_argmax: bool; guardrails_captured: bool
    proposal_emitted: bool; proposal_id: int | None
    evidence_keys: tuple[str, ...]; notes: tuple[str, ...]

# --- eval/harness/fibers.py (SE-2 + V1 evidence + the fibers section) ---
@dataclass(frozen=True)
class ClaimFiber:
    claim_id: str; kind: str; pers: float; sigma_min: float; sigma_max: float
    gap: bool; n_cells: int; n_seeds_rule: int
@dataclass(frozen=True)
class FibersEvidence:
    grid: tuple[float, ...]; base_fingerprint: str; lever_registry_hash: str
    def as_ref(self) -> str: ...
@dataclass
class FibersResult:
    corpus_ref: str | None; evidence: FibersEvidence
    fibers: dict[str, tuple[ClaimFiber, ...]]          # pipeline -> claim fibers
    aggregates: dict[str, dict[str, float]]            # pipeline -> {metric_name: value}
    spec_hashes: dict[str, str]; readings_written: int; notes: tuple[str, ...]
def lever_registry_hash() -> str: ...                  # V1 — a mismatch means re-key
def fibers_spec_hash(pipeline: str, lever: Lever, grid: Sequence[float]) -> str: ...
def render_markdown(result: FibersResult, *, date: str, topic: str = "sigma-fibers",
                    top_n: int = 10) -> str: ...        # the fibers section, deterministic

# --- eval/harness/gate.py (SE-3 tiering + the 3 ship criteria; MUTATES NOTHING) ---
class Tier(Enum): SETTLED = "settled"; HUNCH = "hunch"; RETAINED = "retained"
@dataclass(frozen=True)
class TieredClaim: fiber: ClaimFiber; tier: Tier; within_tier_rank: float
def assign_tiers(fibers: Sequence[ClaimFiber], *, m: int,
                 confidence: Mapping[str, float]) -> list[TieredClaim]
def thresholds(m: int) -> tuple[float, float]          # (θ_weak=2/m, θ_strong=0.5); raises if coarse
@dataclass(frozen=True)
class GateValidation:
    noise_settled_rate: float; planted_reached_settled: bool
    tiered_precision: float; baseline_precision: float; noise_settled_max: float = 0.05
    # .crit_noise_clean / .crit_planted_settles / .crit_precision_gain / .ship / .failing_clauses()

# --- eval/harness/report.py (E4 — the A/B report the composite embeds) ---
@dataclass(frozen=True)
class Report:
    topic: str; date: str; figures: tuple[Figure, ...]; coverage_notes: tuple[str, ...]
def build_report(topic: str, date: str, *, eval_store, run_ledger, telemetry,
                 attestations=None) -> Report: ...     # pure, READ-ONLY over the stores
def render_markdown(r: Report) -> str: ...
def render_json(r: Report) -> str: ...                 # sort_keys=True — deterministic

# --- eval/harness/registry.py ---
def is_registered(name: str) -> bool: ...              # registered-names-only gate

# --- eval/harness/store.py ---
@dataclass(frozen=True)
class EvalKey: spec_hash: str; corpus_ref: str; config_fingerprint: str; seed: int
def query(self, *, metric_name: str | None = None, corpus_ref: str | None = None) -> list[Reading]

# --- core/temporal/spine.py (V2 — RECORD a cut, never fabricate; None ⇒ preview) ---
@dataclass(frozen=True)   # HASHABLE
class CertifiedCut:
    frontier: tuple[tuple[str, int], ...]              # sorted (chain-key, position)
    certificates: frozenset[Certificate]
    evidence: tuple[str, ...]
# Spine.cut_at(*, strata: frozenset[str]) -> CertifiedCut   (live stores only)

# --- tests/quality/fixtures_sigma_gate.py (the V3 battery substrate — reuse VERBATIM) ---
PLANTED_ROWS; NOISE_ROWS; PLANTED_IN_NOISE_ROWS       # hand-placed unit-vector corpora
def phase7_fibers(rows, *, resolution=5) -> tuple[tuple[ClaimFiber, ...], RunLedger, list[float]]
def ledger_labels(ledger) -> dict[str, str]           # claim_id -> "planted"|"noise"|"other"
def ledger_confidence(ledger) -> dict[str, float]     # within-tier ordering key
def single_sigma_precisions(ledger, labels) -> list[float]   # per-cell precision; take max() for (iii)

# --- config fingerprint (V1) — the DRIVE's own pure fn, reuse for byte-exactness ---
from core.dreaming.shadow import _config_fingerprint   # (cfg) -> sha256 str
```

## 7. Items

### Item 1 — the control battery (V3 as one invocation)
- **Objective:** lift the three-criteria F9 computation into the harness as a reusable, importable
  function and expose it as `scripts/experiment.py controls` — one invocation, GREEN iff all three
  reproduce, non-zero exit on RED (so "controls fail ⇒ run INVALID" is mechanical).
- **Files:** `eval/harness/experiment.py` (`run_control_battery() -> ControlOutcome` holding the
  three `GateValidation` criteria + the raw values + a `.green` flag), `scripts/experiment.py`
  (`controls` subcommand), `tests/unit/test_experiment_controls.py`.
- **Acceptance test:** `uv run scripts/experiment.py controls` exits 0 and prints all three criteria
  GREEN on the current pipeline; `uv run pytest tests/unit/test_experiment_controls.py -q` green —
  the battery's three values EQUAL the quality test's `_compute_validation()` values (noise SETTLED
  ≈ 0, planted→SETTLED, tiered precision > best single-σ), and a synthetically-failed
  `GateValidation` makes the command exit non-zero.
- **Falsifier:** the battery reports `.green = True` while any underlying bp-057 criterion is RED
  (the instrument is lying — divergence from `test_sigma_gate.py` on the same fixtures), OR it fixes
  the pass as a constant instead of re-driving the pipeline.
- **Invariant(s):** reuses bp-057 fixtures VERBATIM (no re-planted structure); model-free,
  deterministic; writes to no store (report-layer values only); I1 untouched.
- **Touches stored data?** No — computes in-memory over fixture stores; prints/returns only.
- **Parallelizable?** No (Items 2–3 import its `ControlOutcome`).  **Depends on:** bp-057.

### Item 2 — the blind-sample generator (SE-3; labels sealed)
- **Objective:** from a tiering (SE-3's `assign_tiers` output), sample ≤24 claims stratified 8/8/8
  across SETTLED/HUNCH/RETAINED (or as available, shortfall RECORDED), emit an UNLABELED presentation
  in seeded-random order + a SEALED labels file (`claim_id → tier`) written to a separate path opened
  only after the owner rates.
- **Files:** `eval/harness/experiment.py` (`generate_blind_sample(tiered, *, seed, cap=24) ->
  BlindSample` with `.presentation` (unlabeled, ordered) + `.sealed_labels` + `.notes`),
  `scripts/experiment.py` (`blind-sample` subcommand → `data/reports/<date>-<topic>/blind/{presentation.md,
  labels.sealed.json}`), `tests/unit/test_experiment_blind.py`.
- **Acceptance test:** `uv run pytest tests/unit/test_experiment_blind.py -q` green — identical seed
  ⇒ identical selection AND order (bit-wise); stratification is 8/8/8 or the shortfall is a recorded
  note; the presentation contains NO tier/label/pers string (assert absence); the sealed file carries
  the `claim_id → tier` join; re-running writes identical bytes.
- **Falsifier:** any tier/label/pers value present in the presentation (blinding leak); different
  order or selection across two same-seed runs (non-determinism); a stratum silently undersampled
  with no recorded note.
- **Invariant(s):** the sealed file is a DISTINCT path from the presentation (never co-mingled);
  seeded PRNG over a SORTED claim list (determinism); no clock read; local write only (data/reports/).
- **Touches stored data?** No eval-store/ledger write; writes only report-layer files under
  `data/reports/` (dry-run: the unit test exercises the pure generator without touching the FS).
- **Parallelizable?** No.  **Depends on:** Item 1 (shared module), SE-3 tiering interface.

### Item 3 — the composite report assembler (§2.3 contract)
- **Objective:** assemble ONE deterministic, model-free composite report rendering the §2.3
  contract, reading registered readings only and writing solely to `data/reports/`.
- **Files:** `eval/harness/experiment.py` (`assemble_composite(*, topic, date, commit_sha,
  sweep_result, fibers_result, tiered, control, cut, determinism, selfmod_posture,
  blind_record=None, eval_store, run_ledger, telemetry) -> CompositeReport` + `render_markdown` /
  `render_json` / `write_composite`), `scripts/experiment.py` (`report` subcommand),
  `tests/unit/test_experiment_report.py`.
- **Acceptance test:** `uv run pytest tests/unit/test_experiment_report.py -q` green — the assembled
  report contains EVERY §2.3 section (E4 A/B; curve + selection + proposal id if any; fibers summary;
  tier occupancy + stability; control-battery outcomes; the V1–V5 evidence block incl. the certified
  cut fields — or a "preview — no cut" note when `cut=None`; and, when `blind_record` is supplied, the
  blind-judgment record); every eval-store number carries its key and a registered metric name (the
  `structural_axes.*` / `sigma_gate.validation.*` exceptions handled exactly as `report.py` does, and
  RECORDED as coverage notes); identical inputs + `date` + `commit_sha` ⇒ identical `render_json`
  bytes.
- **Falsifier:** a numeric reading emitted to the eval store under an unregistered name (ad-hoc metric
  emission — §2.3 violation), OR a §2.3 section silently missing (no coverage note), OR non-identical
  bytes across two same-input renders.
- **Invariant(s):** READ-ONLY over every store; writes only `data/reports/`; the V1–V5 block records
  config fingerprint + `lever_registry_hash` + corpus digest + `commit_sha` + σ-grid/`fibers_spec_hash`
  (V1), the cut frontier + certificates (V2), control outcomes (V3), the determinism spot-check
  result (V4), and the selfmod posture + proposal id (V5); no silent caps.
- **Touches stored data?** No — reads stores, writes only report files.
- **Parallelizable?** No.  **Depends on:** Items 1–2.

## 8. Math carried explicitly
- **tier occupancy** — *measures:* the count/fraction of claims in each `Tier` for a tiering.
  *valid when:* the tiering is over one corpus snapshot at one grid (`FibersResult.corpus_ref` single;
  `thresholds(m)` well-formed). *fails its keep if:* SETTLED occupancy is reported as a fraction of a
  claim set that mixes snapshots (the confound the fibers `MixedCorpusError` already forecloses).
- **tier stability** — *measures:* the fraction of claims whose `Tier` is identical between two
  caller-supplied tierings over the same claim set (§3 Q6 definition). *valid when:* both tierings
  cover the same `claim_id` set at the same `m`; stability is computed over the intersection with the
  non-intersection recorded. *fails its keep if:* it is computed across different grids/m (θ_weak =
  2/m shifts) — an apples-to-oranges agreement number. The SE-3 ≥ 80% bar is applied in ANALYSIS
  (frozen §2.2), never by this code.
- **tiered vs single-σ precision (control iii)** — held VERBATIM from bp-057
  (`GateValidation.crit_precision_gain`): *measures:* surfaced precision of persistence-tiering vs
  `max(single_sigma_precisions)`. *valid when:* over the planted-in-noise fixture at the F9 grid.
  *fails its keep if:* it diverges from `test_sigma_gate.py`'s computation on the same fixtures — then
  the battery, not the pipeline, is broken (Item 1 falsifier).

## 9. Non-goals
No RUN (owner-fired, V5 — this plan builds the machine, never fires it). No selfmod flip (OWNER-ONLY,
config/defaults.toml:240 — never touched here). No θ retune, no lever motion, no sweep-spec edit
(all frozen). No new registered metric, no eval-store emission of report-layer values. No `core/`
write. No phase-B / connectivity-instrument code (deferred tranche). No claim-identity matching
(SF-a). No scheduler-fired recurrence (parked, note §4).

## 10. Stop-and-raise
- A discovered spec defect in a consumed interface (sweep/fibers/gate/report) → file a `spec-defect`
  finding (RESERVE **finding-0096**), park the item, continue the others — never route around by
  editing the built module (it is out of scope).
- Any pressure to fabricate a certified cut, weaken a control criterion, or de-blind the sample
  before ratings are recorded → STOP; those are the experiment's integrity teeth failing.
- Any blessing (`proposed→ready`, `draft→ratified`, a selfmod flip) → never; it is the owner's.
- An owner-level question → park the criterion with a re-entry note, batch to the orchestrator,
  continue. Never block on the owner (§5).

## 11. Parked decisions
| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| tier-stability partition | full-seed vs leave-one-seed-out majority; harness computes the agreement fraction, script supplies the two tierings (§3 Q6) | a fixed k-fold reshuffle (over-specifies; the note leaves it open) — rejected as inferring design; a single-tiering "stability = 1" stub (vacuous) — rejected | run-1 findings show the chosen partition mis-measures stability ⇒ a note update re-ratified for run 2 |
| control-battery fixture home | reuse `tests/quality/fixtures_sigma_gate.py` verbatim | copy the fixtures into `eval/harness/` (forks the planted defs; risks drift from the suite the battery mirrors) — rejected | the fixtures graduate into a shared `eval/` fixture module (a separate tidy plan) |
| `sigma_gate.validation.*` registration | unregistered; displayed like `structural_axes.*` (read without `registry.get`, recorded as a coverage note) | register them now (out of scope; bp-057 deferred it to E6) — rejected | the E6 registration plan |

## 12. Dependency & ordering summary
Serial within the plan: **Item 1 → Item 2 → Item 3** (2 and 3 import Item 1's module and
`ControlOutcome`; 3 embeds 2's blind record). Cross-plan: depends on bp-049 (`SweepResult`), bp-050
(`FibersResult`/`ClaimFiber`), bp-054 (registered names), bp-055 (`CertifiedCut`), bp-057 (the gate +
the F9 fixtures). Blast radius: **all read-only sensing** — every item computes/reads and writes only
report-layer files under `data/reports/`; no store mutation, no `core/` write, no network. This is
the note's "everything else is already built" — the plan is glue + evidence rendering + tests.
