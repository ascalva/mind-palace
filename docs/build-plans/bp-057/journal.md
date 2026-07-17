# bp-057 (sigma-gate) — builder journal

Frame: `CONSTITUTION.md` → `CLAUDE.md` → plan `docs/build-plans/bp-057/plan.md`.
Conditional plan of the wave — **park-and-record is a sanctioned completion**, not a failure.

## Contract / write scope
- `eval/harness/gate.py`
- `tests/quality/test_sigma_gate.py`
- `tests/quality/fixtures_sigma_gate.py`
- this journal; new files under `docs/findings/`
Everything else DENIED.

## Worktree hygiene (done)
- `git merge --ff-only main` → "Already up to date" (fresh off main tip `61fdedb`).
- Dep check: `ClaimFiber` present at `eval/harness/fibers.py:96` (bp-050 merged). ✅
- `registry.py` (bp-054) present; `sigma_persistence.*` family registered. No pre-existing
  `gate.py` / `TieredClaim` / `GATE_THRESH` symbols anywhere (clean slate).

## Key facts grounded from the context manifest
- **§2.5 rule (verbatim).** Two thresholds `0<θ_weak<θ_strong≤1` partition `pers∈(0,1]`:
  `pers≥θ_strong→SETTLED`; `θ_weak≤pers<θ_strong→HUNCH` (capped, labelled); `pers<θ_weak→RETAINED`
  (ledger-only, never surfaced). Within a tier, order by confidence c(κ) ALONE. Provisional
  defaults `θ_weak=2/m`, `θ_strong=0.5`. THRESH lifecycle (tuning, not code).
- **I1 (recursive-strata §4/§9).** Persistence never changes a weight/confidence/promotion. Gate
  filters SURFACING of PROPOSED candidates only. "No Dreamer-confidence-based weighting of derived
  content, ever" (§9) — the never-list re-asserted in the tests.
- **One-scalar prohibition (adjudicator.py:20-21).** c decides belief, utility decides surfacing;
  one scalar forbidden. `pers` is NEVER multiplied into c(κ). Tier by pers; within-tier rank by
  c(κ). Lexicographic two-axis, never a product.
- **ClaimFiber (fibers.py:96, verbatim input type).** Fields: `claim_id, kind, pers, sigma_min,
  sigma_max, gap, n_cells, n_seeds_rule`. NB: **carries no `support`** — so ground-truth labels for
  the F9 precision measurement must be reconstructed from the run ledger (claim_id → support_json).
- **σ mechanics.** `MirrorGraph`: edge iff `cos ≥ σ` (monotone: strict σ ⇒ subgraph). Community
  interpreter = single-linkage connected components (`cluster_notes`, min_size 2); one Claim per
  component, `support = component digests`. phase7 claims carry `confidence=0.0` (un-adjudicated);
  dream_v2 claims carry `e.confidence` = c(κ). σ grid `[0.55,0.75]` (lever `dream_rnd_sigma`).

## Design decisions (recorded)
### gate.py — pure, mutates nothing (I1)
- Imports only stdlib + `ClaimFiber` under `TYPE_CHECKING` (with `from __future__ import
  annotations`), so gate.py's runtime namespace holds NO store writer at all. Asserted by a
  source-grep test (no `EvalResultsStore`/`RunLedger`/`DerivedStore`/`.put(`/`LEVERS`/`register`).
- Pinned surface (verbatim §6): `Tier`, `GATE_THRESH={theta_weak_cells:2.0, theta_strong:0.5}`,
  `TieredClaim(fiber,tier,within_tier_rank)`, `assign_tiers(fibers,*,m,confidence)`,
  `hunch_section(claims,*,cap)`.
- Added (required by Item 2, not silent): `GateNotValidated`, `GateValidation` (pure record of the
  three criteria + `.ship`), `surfaced(claims,*,cap,validation)` — raises `GateNotValidated` unless
  `validation.ship`; RETAINED never appears in its output.
- `assign_tiers` reads module-global `GATE_THRESH` (keeps the pinned signature verbatim — no extra
  param). Tier derived from `pers` alone; `within_tier_rank = confidence[claim_id]` alone. Sort key
  `(tier_order, -within_tier_rank, claim_id)` — two-axis lexicographic, NO product of pers×conf.

### F9 validation protocol (the ship/park decision) — the fixture design
- **Pipeline: phase7** (pure community lens, model-free, cleanest ground truth). Confidence does
  NOT enter criteria (i)/(ii)/(iii) — those are pure tier-assignment (pers) — so phase7's 0.0
  confidence is fine; genuine-c(κ) within-tier ordering is exercised in the Item-1 unit tests.
- **Vectors with KNOWN cosines** (deterministic, model-free), swept through the BUILT ShadowRunner
  via `SweepEngine` at m=5 grid `[0.55,0.60,0.65,0.70,0.75]`; `run_fibers` produces the ClaimFibers.
- **Planted:** two ISOLATED tight clusters (cos ~0.99 within, orthogonal between + to noise) →
  each persists on ALL cells → pers=1.0 → SETTLED. (criterion ii)
- **Noise = a MORPHING STAR** centred at node `a` with graded edge cosines to
  b,c₁,c₂,c₃,c₄ = 0.76,0.72,0.67,0.62,0.57 (each in a distinct orthogonal side-dim, so side-nodes
  never inter-connect — max side cosine 0.76·0.72≈0.547 < σ_lo=0.55). The connected component
  centred on `a` GROWS by one node as σ drops past each threshold ⇒ a DISTINCT support set (claim
  identity) at every cell ⇒ 5 noise identities each with pers=1/5=0.2 → all RETAINED.
- **Why this is the honest multi-scale test:** cos(a,b)=0.76 > σ_hi so `{a,b}` is a noise FP even at
  the STRICTEST cell (σ=0.75) — but it MORPHS at lower σ, so it is non-persistent. Hence EVERY
  single σ carries a noise false positive (single-σ precision < 1 at every scale, incl. the
  strictest), yet persistence-tiering filters all of it. The strong form of criterion (iii) holds.

### The three criteria (COMPUTED by the test; recorded here after the run)
- (i) noise-fixture SETTLED-tier rate ≈ 0 (tol `NOISE_SETTLED_MAX=0.05`).
- (ii) planted community claims reach SETTLED.
- (iii) tiered surfaced precision  >  best single-σ precision (baseline = **max over σ** of
  single-σ surfaced precision — the STRONGEST/most-conservative reading, not a cherry-picked σ).
- Ground truth: claim is TRUE iff `support ⊆ planted_digests`, NOISE iff `support ∩ noise_digests`
  (planted & noise never share a component). Labels reconstructed from the ledger by claim_id.

## SHIP/PARK DECISION — **SHIP** (all three §2.5 criteria hold, computed by the test)
Computed by `tests/quality/test_sigma_gate.py::_compute_validation` over the F1-variant fixtures
(m=5 grid `[0.55,0.60,0.65,0.70,0.75]`, phase7 lens), recorded verbatim (§7 Item-2 acceptance):

| criterion | value | verdict |
|---|---|---|
| (i) noise-fixture SETTLED-tier rate ≈ 0 | **0.0** (≤ tol 0.05; all 5 noise identities RETAINED) | ✅ |
| (ii) planted claims reach SETTLED | **True** (both isolated cos≈0.99 clusters, pers=1.0) | ✅ |
| (iii) tiered precision > best single-σ | **1.0 > 0.6667** (baseline = MAX over σ, strongest form) | ✅ |
| **SHIP** | **True** | ✅ |

- Falsifier (i) actively defeated: single-σ surfaces a noise FP at EVERY cell (incl. the strictest,
  σ=0.75, where `{nA,nB}` lives) so min single-σ precision < 1.0, yet the gate's noise-SETTLED rate
  is 0.0 — strictly below the single-σ noise-surfacing rate. The gate filters apophenia along σ.
- **Decision:** the gate SHIPS; its quality tests join the suite green. `surfaced(...)` is LIVE for
  a shipping `GateValidation` and surfaces only the persistent planted structure (transient noise
  filtered); RETAINED never appears. No park, no re-entry triggered, finding 0097 NOT needed.

## Acceptances / falsifiers verified
### Item 1 (unit + I1 guards) — `test_sigma_gate.py`
- Tiers partition at the θ edges (`pers≥θ_strong→SETTLED`; `θ_weak≤pers<θ_strong→HUNCH`; else
  RETAINED); θ_weak = 2/m scales with the grid; a coarse grid collapsing the tiers is REFUSED.
- One-scalar prohibition: within-tier order follows c(κ) ALONE — a high-pers low-conf claim does
  NOT outrank a low-pers high-conf claim within SETTLED. Confidence passes through VERBATIM (§9
  never-list: no confidence-based weighting; unmapped → 0.0, never pers).
- RETAINED appears in NO surfaced output (neither `surfaced` nor `hunch_section`); HUNCH section
  capped + labelled (tier==HUNCH), strongest c(κ) first.
- I1 structural: gate.py RUNTIME imports are stdlib-only (`ClaimFiber` TYPE_CHECKING-only) — AST
  check; no store/ledger/registry mutator called anywhere (AST); no `pers` in any multiplication
  (AST — the source-level one-scalar proof); no promotion/weight symbol exposed.
- Falsifiers defeated: any write path (none — imports no store writer); any pers×confidence scalar
  (none — AST-proven); a RETAINED claim surfacing (excluded by construction).
### Item 2 (F9 protocol + ship/park) — `test_sigma_gate.py`
- The three criteria COMPUTED end-to-end from the ShadowRunner sweep → `run_fibers` → `assign_tiers`.
- Results land as keyed `sigma_gate.validation.*` readings in an in-memory eval store (the gate
  MODULE writes nothing — the test writes the readings; I1 intact).
- Ship/park ENFORCED: `surfaced` raises `GateNotValidated` unless `validation.ship` (never a silent
  ship). Falsifier (the note's): noise reaching SETTLED at ≥ single-σ baseline rate — NOT observed
  (0.0 vs a positive single-σ noise rate).

## Attestable-green gate (each leg run separately, all pass)
- `ruff check .` → All checks passed
- `mypy core agents eval ops scheduler scripts` → Success, no issues (206 files)
- `mypy` (argless) → **69 errors** (exactly; my 3 new files contribute 0 — verified by grep)
- `python -m ops.type_gate` → OK (tier-2 membership + bare-ignore scan)
- `pytest -q -m 'not live'` → 1414 passed, 10 skipped, 9 deselected
- `pytest tests/quality/test_sigma_gate.py -q` → 19 passed

## Interpretation notes (builder-resolved, spec-fidelity)
- **"best single-σ baseline"** (criterion iii) read as **max over σ of single-σ surfaced precision**
  — the STRONGEST/most-conservative reading (not a cherry-picked weak σ). The morphing-noise fixture
  makes even the strictest cell impure, so tiering strictly beats even this hardest baseline.
- **`sigma_gate.validation.*` registration** is NOT done here: registry.py is bp-054's write scope
  (OUT), and the gate module persists nothing (the readings are test-local, in-memory). When E6
  wires a real validation run, that plan registers the family — same precedent as fibers.py writing
  `sigma_persistence.*` before bp-054 registered it. No finding needed.

## Findings filed
None. (SHIP outcome — finding 0097 was reserved for a PARK and is not needed. No
design/math/direction question arose; the two spec-fidelity interpretations above were
builder-resolved and recorded.)

