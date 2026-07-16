# bp-050 journal — FB-1: the σ-fibers consumer

Builder session. Contract `builder`. Write scope: `eval/harness/fibers.py`,
`scripts/fibers.py`, `tests/unit/test_fibers.py`, `tests/integration/test_fibers_consumer.py`
(+ this journal + `docs/findings/`). Branch `worktree-agent-a94c5161e38749aec`.

## Frame read (in manifest order)
- `dn-sigma-fibers` (RATIFIED) §2.1–§2.4 — the design. Math held verbatim from §2.3 (see below).
- `core/stores/runledger.py` — `claim_id = sha256(kind‖canonical(support)‖polarity)` (:37-42);
  `dream_runs` carries `config_fingerprint`+`corpus_digest`, NO seed column (seed reaches only
  the EvalKey — shadow.py:208-212); `runs(pipeline=)`, `claims(run_id=, novel_only=)` reads.
- `eval/harness/store.py` — `EvalKey(spec_hash, corpus_ref, config_fingerprint, seed)`,
  `Reading`, `put` (False=>present=>skip), `type_tag` a free VARCHAR; spec_hash =
  "instrument id+version ‖ pipeline ‖ battery params" (:32). `open_eval_store`.
- `core/dreaming/shadow.py` — `_config_fingerprint(config)` (:94-113) hashes EVERY registered
  lever (from `ops.levers.LEVERS`); `_SPEC_PREFIX`, `_key` (:208-212). This is the pure fn the
  fibers reconstruction MUST reuse so the drive's fingerprint and our regeneration agree.
- `eval/harness/sweep.py` — `_modify_config` generic-replace pattern (:328-331);
  `DriveResult.fp_to_value` (:297-303) is the in-memory map we regenerate; `select` is the
  SELECTION consumer sibling; `parse_spec`/`SweepSpec.grid()` reused by the script.
- `core/dreaming/graph.py`, `core/dreaming/interpreters.py` — `MirrorGraph`, `community_interpreter`
  (= the phase7 pipeline) for the Item-2 exact oracle.
- `config/sweeps/dreamer-sigma-ab.toml` — the shipped grid (dream_rnd_sigma "full", m=21, seeds=5).
- `ops/levers.py` — `LEVERS`, `Lever` (dream_rnd_sigma lo=0.55 hi=0.75); `config/loader.py` Config.

## Math held verbatim (ratified §2.3)
`S(χ) = {σ_i ∈ Γ_m : e(χ,σ_i)=1}`; `pers(χ) = |S(χ)|/m ∈ (0,1]` (SUPPORT MEASURE, not hull
length — gaps do NOT count); hull `[min S, max S]`; `gap(χ)=1` iff S not one run of consecutive
grid indices. Per-cell emission `e(χ,σ_i)=1` iff χ emitted in ≥ ⌈k/2⌉ of k seeds (today
seed-invariant → collapses to a 0/k indicator; the majority rule is implemented anyway,
forward-compat). Validity: ONE corpus_digest across cells (mixed ⇒ refuse); deterministic
pipelines per (config, seed).

## Grounding honored (§3, resolved at graduation — verified, not re-opened)
- fp→σ reconstruction is pure: regenerate `_config_fingerprint(modify(base, sigma=σ_i))` per σ_i
  and join to `dream_runs.config_fingerprint`. Reused `shadow._config_fingerprint` (the exact
  drive fn) + `sweep._modify_config` (the exact drive modification) so the join is byte-exact.
- Records (grid, base fingerprint, lever-registry hash) into the fibers evidence at run time;
  a supplied `expected_registry_hash` that differs from the live registry hash refuses
  fail-closed (§2.4.1 — a bp-046-widening would silently re-key).
- Per-claim layer reads the RUN LEDGER; aggregates go TO the eval store (the §2.4 capsule
  correction).

## Design choices (this plan's only fixed choice, §6)
- `spec_hash = sha256("fibers/v1‖<pipeline>‖<grid-descriptor>")`; grid descriptor = canonical json
  of `{axis, [lo,hi], grid}` (grid IS a battery param). `corpus_ref` = shared corpus_digest;
  `config_fingerprint` = BASE config's; `seed = 0`. type_tag `Res(sigma)` (§2.6/§4 — put() does
  not gate on registration; bp-054 registers). Aggregate names: `sigma_persistence.{mean,p50,max,
  frac_ge_strong,n_claims}` (must match bp-054 EXACTLY, §6).
- `frac_ge_strong` uses STRONG_THRESHOLD=0.5 — the §2.5 SF-e provisional default, DESCRIPTIVE
  ONLY, NOT the surfacing gate (that is bp-057, a non-goal here).
- Consumer processes EACH joined pipeline (spec_hash carries pipeline, §2.4.3) → 5 readings per
  pipeline. A pipeline is filterable via `pipelines=`.

## What landed
- `eval/harness/fibers.py` — the consumer. `FibersConsumer`/`run_fibers` (reconstruct fp→σ →
  join ledger cells → per-claim `(pers,hull,gap)` via seed-majority → 5 aggregate readings/pipeline
  into the eval store); `fiber_metrics` (the pure §2.3 metric); `lever_registry_hash`,
  `fibers_spec_hash`, `FibersEvidence`; `RegistryStateMismatch`/`MixedCorpusError` (fail-closed);
  `render_markdown`/`write_report` (E4 report section, writes only `data/reports/`).
- `scripts/fibers.py` — run entry `uv run scripts/fibers.py <spec.toml> [--date …]` over the SAME
  ledger `scripts/sweep.py` writes; does NOT drive a sweep (non-goal). Seals core first.
- `tests/unit/test_fibers.py` (Item 2) — exact-partition oracle (test-side, SF-f); degeneracy
  anchor == analytic, ruler test Γ_m→Γ_{2m-1} within bound, grid-vs-oracle within bound, gap
  counts cells not hull, spec_hash/registry-hash guards. 8 tests.
- `tests/integration/test_fibers_consumer.py` (Item 1) — real 3-cell drive joins all cells +
  5/pipeline once; re-run 0; planted-ledger known pers/aggregates; never-overwrites; registry
  mismatch refuses; mixed-corpus refuses. 6 tests.

## Key implementation facts (fresh-agent sufficient)
- Reconstruction uses `shadow._config_fingerprint` (the DRIVE's fn) + a local `_modify_config`
  clone of `sweep.py:328-331` → the join is byte-exact (§2.4.1). The registry hash is
  recorded in evidence; a supplied `expected_registry_hash` mismatch refuses fail-closed.
- Seed-majority ⌈k/2⌉ is implemented over the k run-rows sharing (pipeline, config_fingerprint)
  at a cell (the ledger has no seed column); today it collapses to a 0/k indicator (seed-invariant)
  — kept for forward-compat (§2.1 caveat, §3).
- Aggregates keyed per §6: spec_hash=`sha256("fibers/v1‖<pipeline>‖<grid-desc>")`, corpus_ref=shared
  digest, config_fingerprint=BASE, seed=0, type_tag `Res(sigma)` (put() ungated — §4; bp-054 registers).
- FIXTURE NOTE: the "joins all cells" probe needs ISOLATED tight pairs — a bridge merges a pair into
  a bigger component at low σ, morphing the community claim's identity across cells (the §2.3 caveat),
  so no single claim_id spans the grid. Fixed with two orthogonal-subspace pairs (cos 0.99).

## Gate (all five legs, separately) — GREEN
1. `ruff check .` — All checks passed. 2. `mypy core agents eval ops scheduler scripts` — no issues.
3. `mypy` (argless) — 69 errors (baseline preserved; my files added none). 4. `ops.type_gate` — OK.
5. `pytest -q -m 'not live'` — 1301 passed, 10 skipped, 9 deselected.

## Status
- [x] Item 1 — consumer core + script entry (accept: integration green)
- [x] Item 2 — exact-partition oracle + falsifier tests (accept: unit green)
- No findings filed. No parked criteria. No stop-and-raise triggered.
