---
type: build-plan
id: bp-049
alias: sweep-engine
status: ready
design_ref:
  - docs/design-notes/evaluation-harness.md   # §2.6 the sweep spec + deterministic optimizer; §2.8 overnight profile; §2.9 sweep.dreamer-sigma-ab (bp-040 re-derived)
contract: builder
write_scope:
  - eval/harness/sweep.py
  - config/sweeps/dreamer-sigma-ab.toml
  - scripts/sweep.py
  - tests/unit/test_sweep.py
  - tests/integration/test_sweep_engine.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 240k
  actual: null
depends_on: [bp-046]
parallelizable_with: []
created: 2026-07-16
updated: 2026-07-16
links:
  - docs/design-notes/evaluation-harness.md
  - docs/build-plans/bp-040/plan.md   # superseded: this plan re-derives its σ-sweep as sweep.dreamer-sigma-ab (§2.9)
re_entry: null
supersedes: bp-040
superseded_by: null
warrant: null
---

# Build Plan — E3a-1b: the sweep engine + deterministic optimizer (grid → curve → admissible selection → §14 proposal)

## 0. Mode & provenance

Investigation and planning produced this plan; implementation proceeds item-by-item on owner approval.
Authority-to-act (the owner's 2026-07-16 directive to graduate E3a-1) is separate from the readiness
blessing (owner-only `proposed → ready`); no agent flips readiness. This is the **engine half** of
E3a-1: the deterministic, model-free optimizer that sweeps a registered lever's grid, builds the curve
from the eval store, filters by admissibility, selects a value, and emits a `ProposedChange` into the
built §14 ledger. It **depends on bp-046** (the registered `dream_rnd_sigma` lever + the widened
`_config_fingerprint` that gives each grid cell a distinct key). It **supersedes bp-040** (`dream-calibrate`):
its `config/sweeps/dreamer-sigma-ab.toml` re-derives bp-040's σ-connectivity sweep as the first sweep
instance (§2.9). No model anywhere in the tuning loop — the curve is the adviser (§2.6).

## 1. Objective

Add `eval/harness/sweep.py` — a declarative-spec-driven grid optimizer — plus `scripts/sweep.py` (the
run entry) and `config/sweeps/dreamer-sigma-ab.toml` (the first instance), so an overnight run can sweep
`dream_rnd_sigma` across its grid, drive the BUILT `ShadowRunner` once per cell (resumable by key), build
the per-lever curve from the eval store, apply the admissibility filter (guardrails lexicographically
prior), select the value (plateau center, least-motion tie-break), and emit that selection as a
`ProposedChange` into the §14 proposal ledger.

## 2. Context manifest

Read in order before any work:

1. `docs/design-notes/evaluation-harness.md` §2.6 (the sweep spec TOML, the deterministic-optimizer
   pipeline, the two autonomy modes — this plan is `mode = "propose"` only), §2.8 (the overnight profile:
   full grids, resumability, no silent caps), §2.9 (`sweep.dreamer-sigma-ab` = bp-040 re-derived).
2. `docs/build-plans/bp-046/plan.md` — the dependency: the `dream_rnd_sigma` lever + the widened
   `_config_fingerprint`. This plan does NOT touch either; it CONSUMES them.
3. `core/dreaming/shadow.py` (whole) — `ShadowRunner` (`run(*, config) -> tuple[run7, run_v2]`), its
   injectable seams (`ledger`, `eval_store`, `store`, `snapshots`, `retriever`, `golden`, `baseline`,
   `drift_cfg`, `seed`), and WHAT it writes to the eval store per run (`golden_recall`, `drift_D`,
   `structural_axes.*` — `:206-235`). The engine drives this per cell.
4. `eval/harness/store.py` (whole) — `EvalKey`, `Reading`, `EvalResultsStore` (`put -> bool`
   resumability, `query(metric_name, corpus_ref) -> list[Reading]` the curve substrate, `get`, `has`),
   `open_eval_store`.
5. `ops/levers.py` — `Lever` (`section`/`key`/`lo`/`hi`/`kind`/`validate`), `LEVERS`, `get_lever`,
   `ProposedChange` (`lever`, `target`, `rationale`; `resolve()` fail-closed). The sweep resolves the
   swept lever here and builds `ProposedChange`s here.
6. `ops/selfmod.py` — `SelfModLoop` (`propose(ProposedChange, *, proposer) -> Proposal`,
   `_require_enabled` raising `SelfModDisabled` when `[selfmod] enabled=false`), `build_loop(validator,
   *, config, ledger)`. The emission seam. `ops/ledger.py` — `ProposalLedger`, `open_ledger`, `Proposal`,
   `LedgerStatus`.
7. `config/loader.py:256-263` — `Config` / `dream_rnd: DreamRnDConfig`, both `@dataclass(frozen=True)`.
   The per-cell modified config is built with `dataclasses.replace`.
8. `eval/harness/registry.py` — `is_registered`, `get`. The objective + swept metrics must be registered
   keys (§2.5, read-only use).
9. `docs/build-plans/bp-040/plan.md` — the superseded plan; its σ-sweep intent is re-derived here.

## 3. Investigation & grounding

- **Q1 — How does a cell drive the built runner with a modified lever value?** `ShadowRunner.run(*,
  config)` accepts a `Config` (`shadow.py:125`). `Config` and `DreamRnDConfig` are frozen dataclasses
  (`loader.py:256-263`), so a cell builds `modified = replace(cfg, dream_rnd=replace(cfg.dream_rnd,
  sigma=v))` — GENERICALLY: given `lever.section`/`lever.key`, `replace(cfg, **{lever.section:
  replace(getattr(cfg, lever.section), **{lever.key: v})})`. dream_v2 then reads `rnd.sigma`
  (`shadow.py:139-141`) = the cell's value. Confirmed the modification reaches the run.
- **Q2 — Is resumability free, or does the engine implement it?** Free — it falls out of bp-046 + the
  store. A cell's `config_fingerprint` is computed by the runner from the modified config (bp-046 makes it
  move with σ); `EvalResultsStore.put` returns False on a present `(key, metric)` (`store.py:100-104`). So
  a re-run of a completed cell re-derives the same key and every `put` skips — the interrupted-night
  resume of §2.8. The engine MUST NOT re-key or cache around this; it drives the runner and lets the store
  dedup. (It MAY skip the whole runner call if `eval_store.has(expected_key, objective)` — an
  optimization; the correctness guarantee is the store's, not the engine's.)
- **Q3 — What metric can be the objective TODAY?** Only a metric `ShadowRunner` writes per cell:
  `golden_recall`, `drift_D`, or `structural_axes.<axis>` (`shadow.py:219-235`). **`f9_composite` is
  REGISTERED (`registry.py:80`) but NOT written by the runner** — the design note's example
  `objective = "f9_composite"` (§2.6) cannot be satisfied until F9 is wired into the per-cell run (E5/E7 or
  a rider). So the first instance's objective is a written metric; the spec's objective is validated
  against BOTH `registry.is_registered` AND presence-in-store-after-a-cell (fail-closed with a clear
  message if the objective is registered but no cell produced it). See §11.
- **Q4 — What are the admissibility guardrails, and where do their readings come from?** §2.5's always-on
  set: golden-set recall unchanged vs `baseline.json`, drift `D(t)` within Θ (advisory until Θ blessed —
  report, don't trip), grounding-defect ≈ 0, integrity green. The runner already writes `golden_recall`
  and `drift_D` per cell into the store — so admissibility reads THOSE keyed readings. A cell whose
  `golden_recall` regressed below baseline (or `drift_D` breaches Θ once Θ is blessed) is **inadmissible
  regardless of objective** — guardrails lexicographically prior (§2.6). Grounding-defect + integrity are
  run-level gates the harness asserts elsewhere (not per-cell metrics); the engine treats the two stored
  guardrails as the per-cell admissibility signal and records which it applied (no silent cap).
- **Q5 — How is the proposal emitted without a ledger schema change?** Via the BUILT
  `SelfModLoop.propose(ProposedChange(lever, target, rationale))` (`ops/selfmod.py`) → a PROPOSED
  `Proposal` row (`ops/ledger.py`). The design note's conceptual `TuningProposal(lever, curve,
  selected_value, evidence_keys)` maps onto this: `lever`/`target` = the selection; `rationale` = a curve
  summary + the evidence `EvalKey`s (as text) — NO new ledger column. E4's report reconstructs the curve
  from the store by the evidence keys. `propose` requires `[selfmod] enabled` (`_require_enabled`); when
  disabled, the sweep still writes the curve + records the selection in its output and LOGS that the
  proposal was not emitted (owner enables to emit) — honoring the fail-closed switch, never forcing it.
- **Q6 — Is the optimizer model-free?** Yes, structurally — it reads scalar readings from a DuckDB store
  and runs arithmetic (plateau detection, argmax, tie-break). No model import, no LLM call. The one model
  in `dream_v2` (synthesize, step 8) is NEVER reached: `ShadowRunner` runs the pipeline STEPS, not the
  method (`shadow.py:19-22`). The engine adds no model.

**Additional risks surfaced during reading:** (a) an overnight σ×2-pipeline×k-seed grid is many runner
calls; each opens/holds the eval store + a scratch snapshot store — the engine must reuse ONE
`EvalResultsStore` + ONE `RunLedger` across cells (inject them into every `ShadowRunner`), not reopen per
cell. (b) The runner needs a `retriever` for guardrails or they are not-captured (`shadow.py:210-211`) —
the sweep must inject the golden-FIXTURE retriever (the `live`-e2e pattern, reads the fixture not the
vault, firewall intact) or admissibility has no golden signal; if absent, the engine records
admissibility as "guardrails not-captured" (no silent pass). (c) `seeds > 1` (§2.6) means k runs per
cell at distinct `seed`s — the engine varies `ShadowRunner.seed`, and the curve aggregates across seeds
(intervals at n≤13, §2.5/EH-f), never collapsing them into a false point.

## 4. Reconciliation

- `docs/design-notes/evaluation-harness.md` §2.6 — the `TuningProposal(lever, curve, selected_value,
  evidence_keys)` shape → **cross-reference-on-extension**: emitted as a `ProposedChange` into the BUILT
  ledger (no schema change), `rationale` carrying the curve summary + evidence keys (§3 Q5). Recorded in
  code + journal so the note's conceptual object and the built row are known to be the same thing.
- `docs/design-notes/evaluation-harness.md` §2.6 example `objective = "f9_composite"` → **banner-on-
  correction** (in the sweep spec + a code comment): the first instance CANNOT use `f9_composite` (not
  written per-cell, §3 Q3); it uses a written metric and the plan records that F9-per-cell wiring is a
  separate concern. Not a silent substitution — the spec comment says why.
- `docs/build-plans/bp-040/plan.md` — **supersession** (§2.9): this plan re-derives bp-040's σ sweep as
  `config/sweeps/dreamer-sigma-ab.toml`. bp-040 → `superseded`, `superseded_by: bp-049` (an orchestrator
  act at graduation, committed separately; not the builder's).
- No committed code is corrected. `ShadowRunner`, the eval store, the levers, the §14 loop, the ledger,
  the registry, the loader are all read-only dependencies — the engine composes them.

## 5. Write scope

- `eval/harness/sweep.py` — the engine: spec model + grid builder + per-cell driver + curve assembler +
  admissibility filter + selection rule + proposal emitter (new).
- `config/sweeps/dreamer-sigma-ab.toml` — the first sweep instance, bp-040 re-derived (new).
- `scripts/sweep.py` — the run entry (`uv run scripts/sweep.py <spec>`) (new).
- `tests/unit/test_sweep.py` — spec parse + the selection-rule instrument (§8) as pure-function tests (new).
- `tests/integration/test_sweep_engine.py` — end-to-end over an in-memory store + a stub/seeded runner
  (new).

**Deliberately OUT of scope** (read-only dependencies, guard denies writes): `core/dreaming/shadow.py`
(the runner is driven, never edited — bp-046 already widened its fingerprint), `ops/levers.py`
(bp-046 registers the lever), `ops/selfmod.py` / `ops/ledger.py` (the gate + ledger are reused, never
reimplemented), `eval/harness/store.py` / `eval/harness/registry.py` / `eval/harness/tuning.py`
(read-only), `config/loader.py`, and every foundation-denylist file. No `eval/golden/**`, no
`baseline.json` (read via the built loaders only).

## 6. Interfaces pinned inline

```python
# core/dreaming/shadow.py — the per-cell engine (verbatim; inject shared stores, vary config+seed)
@dataclass
class ShadowRunner:
    ledger: RunLedger; store: RowSource | None = None; eval_store: EvalResultsStore | None = None
    snapshots: SnapshotStore | None = None; retriever: Retriever | None = None
    golden: Sequence[GoldenQuery] | None = None; baseline: dict[str, float] | None = None
    drift_cfg: DriftConfig | None = None; seed: int = 0
    def run(self, *, config: Config | None = None) -> tuple[str, str]: ...   # (run7_id, run_v2_id)
# writes per run: golden_recall, drift_D (guardrails), structural_axes.<axis> (dream_v2 only)

# eval/harness/store.py — the curve substrate (verbatim)
@dataclass(frozen=True)
class EvalKey: spec_hash: str; corpus_ref: str; config_fingerprint: str; seed: int
class EvalResultsStore:
    def put(self, r: Reading) -> bool                        # False => cell present => SKIP (resume)
    def has(self, key: EvalKey, metric_name: str) -> bool
    def query(self, *, metric_name: str | None = None, corpus_ref: str | None = None) -> list[Reading]

# ops/levers.py — the swept lever + the proposal shape (verbatim)
@dataclass(frozen=True)
class Lever: name: str; section: str; key: str; kind: LeverKind; lo: float; hi: float; description: str = ""
def get_lever(name: str) -> Lever                            # fail-closed on unknown
@dataclass(frozen=True)
class ProposedChange:
    lever: str; target: float; rationale: str = ""
    def resolve(self) -> tuple[Lever, float | int]: ...      # bounds-checks before the ledger

# ops/selfmod.py — the emission seam (verbatim; honors [selfmod] enabled)
class SelfModLoop:
    def propose(self, change: ProposedChange, *, proposer: str = "") -> Proposal   # raises SelfModDisabled if off
def build_loop(validator, *, config=None, ledger=None) -> SelfModLoop

# config/loader.py — per-cell modified config (frozen -> replace)
from dataclasses import replace
modified = replace(cfg, **{lever.section: replace(getattr(cfg, lever.section), **{lever.key: v})})
```

**The sweep spec** (design note §2.6 — this plan's parser accepts exactly this shape; `mode="propose"` only):

```toml
[sweep.dreamer-sigma-ab]
levers      = { dream_rnd_sigma = "full" }   # "full" = the lever's [lo,hi] at `resolution`, or an explicit list
resolution  = 21                             # grid points across the lever range
pipelines   = ["phase7", "dream_v2"]         # native A/B (the runner produces both per cell)
corpus      = "mirror-snapshot"              # or "fixture:<hash>" | "control"
seeds       = 5
metrics     = ["golden_recall", "drift_D", "structural_axes.frustration"]   # written per cell
objective   = "golden_recall"                # a REGISTERED, per-cell-WRITTEN key (NOT f9_composite yet — §3 Q3)
guardrails  = []                             # additive only; the §2.5 defaults are always on
mode        = "propose"                      # can never exceed the lever's autonomy (bp-047 manifest = propose)
```

## 7. Items

### Item 13 — `eval/harness/sweep.py` (spec + grid driver) + `config/sweeps/dreamer-sigma-ab.toml` + `scripts/sweep.py`

- **Objective:** parse a sweep-spec TOML into a validated `SweepSpec` (levers/resolution/pipelines/corpus/
  seeds/metrics/objective/mode; `mode` must be `"propose"`, objective must be `registry.is_registered`);
  build the grid for the swept lever (`"full"` → `lo..hi` at `resolution`, coerced to the lever kind, or an
  explicit list, each `lever.validate`-d); for each (cell value × seed) build the modified `Config`
  (§3 Q1) and drive ONE shared-store `ShadowRunner.run(config=modified)`; the per-cell Readings land in the
  eval store resumable-by-key (§3 Q2). `scripts/sweep.py <spec>` is the run entry.
- **Files:** `eval/harness/sweep.py`, `config/sweeps/dreamer-sigma-ab.toml`, `scripts/sweep.py`.
- **Acceptance test:** `uv run pytest tests/integration/test_sweep_engine.py -q` green: a 3-point ×
  1-seed sweep over `dream_rnd_sigma` against an in-memory `RunLedger` + in-memory `EvalResultsStore` + a
  seeded fixture retriever drives 3 distinct cells (3 distinct `config_fingerprint`s — the bp-046 property);
  re-running the SAME sweep writes ZERO new rows (every `put` skips — resumability, §2.8); an out-of-bounds
  grid point raises via `lever.validate` before any run; `mode = "auto"` in a spec raises a clear "E3b"
  error; an unregistered `objective` raises fail-closed.
- **Falsifier:** two σ cells collide on `config_fingerprint` (bp-046 regression / the modified config not
  reaching the runner); OR a re-run duplicates rows (resumability broken); OR the engine reopens the store
  per cell instead of reusing one (risk (a)); OR a grid point outside `[lo,hi]` reaches a run.
- **Invariant(s):** model-free (no model import; the runner's step-8 synth is never reached); eval
  isolation (the sweep writes ONLY the eval store + run ledger via the runner — never the interpreted/
  derived store, never ingest); no silent caps (a bounded/sampled grid records what it dropped, §2.8);
  reads the mirror only through the runner's `MirrorView` seam (firewall).
- **Touches stored data?** Yes — per-cell Readings into the eval store + runs/claims into the run ledger,
  both via the BUILT `ShadowRunner`, both append-only/resumable. Test against in-memory stores; a real
  overnight run is the owner's/scheduler's act, not the builder's.
- **Parallelizable?** No (Item 14 consumes its cells). **Depends on:** bp-046 (the registered lever + moved
  fingerprint).

### Item 14 — the optimizer: curve → admissibility → selection → `ProposedChange` into §14

- **Objective:** after the grid is evaluated, `query` the eval store for the objective across cells; build
  the per-lever curve (lever value → objective reading, aggregated across seeds with an interval, per
  pipeline); apply the **admissibility filter** (a cell whose stored `golden_recall` regressed below
  baseline — or `drift_D` breaches Θ once blessed — is inadmissible regardless of objective, guardrails
  lexicographically prior); apply the **selection rule** (§8: widest near-optimal plateau center, tie-break
  least motion from the current value); emit `SelfModLoop.propose(ProposedChange(swept_lever,
  selected_value, rationale=<curve summary + evidence EvalKeys>))` when `[selfmod] enabled`, else record
  the selection + log "proposal not emitted (selfmod disabled)".
- **Files:** `eval/harness/sweep.py` (the optimizer half + the selection instrument).
- **Acceptance test:** `uv run pytest tests/unit/test_sweep.py -q` green — the selection instrument as a
  pure function over synthetic curves: a flat-topped curve selects the PLATEAU CENTER (not the first max);
  two equal plateaus tie-break toward the value nearest the current; an inadmissible cell (guardrail-failed)
  is excluded even when it holds the objective max; an all-inadmissible curve emits NO proposal (and says
  so); a selected value is always in `[lo, hi]` (`ProposedChange.resolve` would else raise). PLUS in
  `test_sweep_engine.py`: with `[selfmod] enabled`, a completed sweep lands exactly ONE PROPOSED ledger
  row whose `target` = the selected value and whose `rationale` names the evidence keys; with selfmod
  disabled, ZERO ledger rows + a recorded selection.
- **Falsifier:** the rule selects a knife-edge maximum over a wider plateau (peak-chasing — the exact
  failure §2.6 forbids); OR an inadmissible cell wins (guardrails not lexicographically prior); OR a
  proposal is emitted with a value outside bounds, or auto-approved/executed (it must land PROPOSED only —
  the owner blesses); OR a model is consulted to pick the value.
- **Invariant(s):** the model advises, code acts — the curve is the adviser, the optimizer is arithmetic,
  every apply transits §14 (this plan only PROPOSES); guardrails lexicographically prior; `[selfmod]
  enabled`/`unattended_enabled` honored, never forced; the proposal references evidence keys, adds no
  ledger column.
- **Touches stored data?** Yes — a PROPOSED row in the §14 ledger (when enabled), via the built loop. No
  overlay write, no execute (that is the owner's blessing path, bp-047's `tune.py`/the selfmod CLI).
- **Parallelizable?** No. **Depends on:** Item 13.

## 8. Math carried explicitly

**The selection instrument** — `select(curve, current) -> selected_value | None`.

- **What it measures:** given the admissible sub-curve `{(xᵢ, ȳᵢ)}` (lever value → seed-aggregated
  objective, ascending xᵢ, guardrail-failed cells already removed), it returns the lever value that is
  *robustly* near-optimal — the center of the widest plateau of near-optimal points — with least motion
  from `current` as the tie-break. Formally: let `M = max ȳᵢ` over admissible cells; the near-optimal set
  `P = {xᵢ : ȳᵢ ≥ M − ε}` for a declared tolerance `ε` (absolute for a bounded metric like recall, or a
  fraction of `M`; declared in the spec/defaults, recorded with the reading). Partition `P` into maximal
  runs of grid-adjacent xᵢ (a "plateau"); pick the longest run; its selected value is the run's CENTER
  (median grid point). Ties between equal-length runs break toward `argmin |center − current|`. The
  objective's DIRECTION (maximize vs minimize) is declared per metric (recall maximizes; `drift_D`
  minimizes) — `M` is the best in that direction.
- **Validity assumptions:** the grid is dense enough that "adjacent" is meaningful (§2.8 full resolution,
  e.g. 21 points — a 3-point grid degenerates to argmax, recorded as such); the objective is comparable
  across cells (same `spec_hash`/`corpus_ref`, the store's keying guarantees it); admissibility has already
  removed guardrail failures (lexicographic priority is applied BEFORE `select`, never inside the argmax);
  seed aggregation produced `ȳᵢ` with an interval, and `ε` ≥ the interval half-width so plateau membership
  is not seed noise.
- **The observable that falsifies it (three-clause discipline):** if `select` ever returns a knife-edge
  maximum (a singleton `P` run) when a strictly wider near-optimal plateau exists, it has failed its
  purpose (peak-chasing over stability — §2.6). The unit test constructs exactly this curve and asserts
  the plateau center wins. A second falsifier: `select` returns a value ∉ admissible set, or ∉ `[lo,hi]`.

## 9. Non-goals

- No `auto` autonomy, no `apply_unattended`, no derived `SAFE_LEVERS`, no cooldowns, no auto-`set` —
  **E3b** (`mode="auto"` in a spec is rejected here).
- No F9-per-cell wiring / `f9_composite` as objective — the runner does not write it (§3 Q3); a rider/
  E5-E7 concern. The first instance uses a written metric.
- No report rendering (curves-as-sparklines, the drift study, the cost appendix) — **E4** (`report.py`);
  this plan writes the curve to the STORE + emits the proposal; the report reconstructs from the store.
- No new registered metric, no `registry.py` edit; no `structural_axes.*` registration (finding-0086's
  rider — the sweep reads by `metric_name`, which `query` does not gate on registration).
- No change to `ShadowRunner`, the eval-store schema, the §14 gate, the ledger schema, or the loader.
- No multi-lever joint sweep (EH-d), no Bayesian/black-box search (EH-b) — grid-first, one lever.

## 10. Stop-and-raise conditions

- If the objective is registered but NO cell produces it in the store (e.g. a spec naming `f9_composite`) —
  STOP the selection with a clear "objective produced no readings; wire it into the per-cell run first"
  error; do NOT silently select over an empty curve. (This is the honest form of the §3-Q3 gap.)
- If `SelfModLoop.propose` proves to have a side effect beyond writing a PROPOSED row (an execute, an
  overlay touch) — STOP and file a `codebase` finding; the sweep must PROPOSE only, never apply.
- If the admissibility guardrails cannot be read per cell (no `golden_recall`/`drift_D` in the store
  because no retriever was injected) — record admissibility as "not-captured" and REFUSE to emit a proposal
  (an unguarded selection is inadmissible by construction), rather than proposing on an unguarded curve.
- If a spec's grid or metric set implies a run the memory ceiling (§2.8, ≤2 resident models) would refuse —
  record the bound in the run output (no silent cap) and proceed with what fits.
- Any blessing (`proposed→ready`, `draft→ratified`) the builder would have to perform: it must not.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| first-instance objective | a written metric (`golden_recall` / a `structural_axes.*`) | `f9_composite` (registered but not written per-cell — §3 Q3) | F9 wired into `ShadowRunner`'s per-cell writes (E5/E7 or a rider) |
| plateau tolerance `ε` | spec key with a default (absolute for bounded metrics; ≥ seed interval half-width) | a fixed global ε (fiction across metrics of different scales) | a metric whose scale the default mis-serves |
| fold bp-047 policy fingerprint into the cell key | no — the runner's live-value `config_fingerprint` (bp-046) is the cell identity | fold it in (couples the cell key to manifest edits; a policy change would falsely re-key a σ curve) | a manifest-version confound appears in a longitudinal curve |
| proposal emission when `[selfmod] disabled` | record selection + log, emit nothing | force-enable (violates the fail-closed switch) / always emit (can't — `propose` raises) | owner enables selfmod to emit |

## 12. Dependency & ordering summary

- **Items:** 13 → 14 (14 consumes 13's cells). Blast-radius order: Item 13 writes append-only/resumable
  eval cells (reversible — a wrong cell is re-keyed, not corrupting); Item 14 emits a §14 proposal (the
  "effect", though still only PROPOSED — the owner blesses the apply). Correctly last.
- **Cross-plan:** `depends_on: [bp-046]` (the registered lever + moved fingerprint — NOT parallelizable
  with it). `supersedes: bp-040` (re-derives its σ sweep as `sweep.dreamer-sigma-ab`, §2.9 — flip bp-040 →
  superseded at graduation). Feeds E4 (the report reconstructs the curve from the store by the proposal's
  evidence keys) and bp-041 (the σ curve is the wire-live evidence) — forward references, not dependencies.
