# Journal — bp-049 `sweep-engine` (E3a-1b: the grid optimizer)

Alive at graduation (2026-07-16). Status `proposed` — awaits owner `proposed → ready` blessing.
**Depends on bp-046** (the registered `dream_rnd_sigma` lever + the widened `_config_fingerprint`);
**supersedes bp-040** (re-derives its σ sweep as `config/sweeps/dreamer-sigma-ab.toml`, §2.9).

## Fresh-agent orientation
Read `plan.md` in full, then the §2 context manifest IN ORDER. This is the deterministic, model-free
optimizer: sweep a registered lever's grid → drive the BUILT `ShadowRunner` per cell (resumable by the
eval store's keying — free, don't reimplement it) → build the curve from `EvalResultsStore.query` →
admissibility filter (guardrails lexicographically prior) → selection (§8: plateau center, least-motion
tie-break) → emit `ProposedChange` into the §14 ledger via `SelfModLoop.propose` (PROPOSED only; the owner
blesses the apply). Two items: 13 (spec + grid driver, writes cells) → 14 (optimizer + emit, the effect).

## The three grounding nuances the plan bakes in (read §3)
1. **Objective must be a metric the runner WRITES per cell** — `golden_recall` / `drift_D` /
   `structural_axes.*`. `f9_composite` is registered but NOT written per-cell (§3 Q3) → first instance
   can't use it; wiring F9 per-cell is a separate concern (§11 parked, §10 stop-and-raise if empty).
2. **Resumability is the store's guarantee, not the engine's** — bp-046 makes `config_fingerprint` move
   with σ; `put` returns False on a present cell. Reuse ONE eval store + ONE run ledger across cells.
3. **The proposal is a `ProposedChange`, not a new `TuningProposal` type** — no ledger schema change;
   `rationale` carries the curve summary + evidence `EvalKey`s; honors `[selfmod] enabled` (emit only when
   on; else record + log).

## §8 math — the selection instrument
A pure function `select(admissible_curve, current) -> value | None`. Falsifier: it must NOT return a
knife-edge max when a wider near-optimal plateau exists (peak-chasing — the exact failure §2.6 forbids).
Unit-tested as a pure function on synthetic curves before the integration test.

## Supersession
bp-040 flipped `proposed → superseded` (`superseded_by: bp-049`) at this graduation — an orchestrator act
(not a blessing). bp-040 stays inspectable; this plan re-derives its intent.

## Checkpoints

### 2026-07-16 — build session start (builder)
- Active plan registered (`.claude/state/active-plan` = bp-049); `uv sync --all-extras` done.
- Context manifest read in full + existing `test_shadow_runner.py` (fixture-retriever pattern:
  `_RowSource`, `_fake_retriever`, injected shared stores) and `scripts/eval.py::_build_retriever`
  (the real fixture-corpus retriever for a production run).

### Grounding decisions (builder-resolvable; recorded, not routed)
- **Curve reconstruction.** The engine cannot read a lever value out of a `config_fingerprint`
  (sha256). So the DRIVE phase records `fp_to_value = {config_fingerprint -> grid value}` by computing
  `shadow._config_fingerprint(modified)` per cell BEFORE the run; the curve joins eval-store readings'
  `key.config_fingerprint` back to the grid value through this map. No re-keying (§3 Q2).
- **Pipeline partition + SPEC-FIDELITY GAP (finding-0090).** Objective readings partition by
  `key.spec_hash` (shadow encodes the pipeline into spec_hash). `select` needs ONE curve, but the spec
  (§6) does not say which pipeline the optimizer selects on when `pipelines` has >1 entry. RESOLUTION:
  optional spec key `select_pipeline`, default = LAST entry of `pipelines` (the dream_v2 lane the
  `dream_rnd_sigma` lever actually drives). Recorded in spec + rationale, never silent. Filed
  `docs/findings/finding-0089.md` (spec-fidelity).
- **Resumability.** Engine does NOT re-key/cache (§3 Q2: drive + let the store dedup). A re-run
  re-drives every cell but every eval `put` returns False → eval-store row count unchanged (the
  asserted property). The RunLedger appends a fresh run-event row per drive (event, not identity).
- **Direction.** `drift_D` minimizes; else maximizes (spec `direction` may override).
- **ε.** effective ε = max(spec `epsilon` default 0.0, max seed-interval half-width over admissible
  cells) — honors §8 "ε ≥ interval half-width".
- **Admissibility.** Per cell, read `golden_recall` at the same EvalKey; a value regressing below
  baseline recall is inadmissible (guardrails LEXICOGRAPHICALLY PRIOR — filtered before argmax). If any
  needed guardrail reading is missing (no retriever) → admissibility "not-captured" → REFUSE to emit
  (§10). `drift_D` is advisory-only until Θ blessed (report, don't trip).

### Selection instrument (§8)
`select(points, *, current, epsilon, direction, grid_size)`: drop inadmissible → M=best in direction →
near-optimal P within ε → grid_size≤3 degenerate to argmax → else maximal grid-adjacent runs, longest
run's CENTER (`run[len(run)//2].value`) → tie between equal-length runs by `argmin|center−current|`.
CARDINAL FALSIFIER covered: singleton max + wider near-optimal plateau → plateau center.

### Progress
- [DONE] Item 13 — `eval/harness/sweep.py` spec parse + grid driver; `config/sweeps/dreamer-sigma-ab.toml`;
  `scripts/sweep.py` run entry. Drives ONE shared eval store + ONE shared RunLedger per (grid×seed).
- [DONE] Item 14 — optimizer half in `eval/harness/sweep.py`: curve → admissibility (lexicographically
  prior) → `select` (§8) → `SelfModLoop.propose` (PROPOSED only).
- [DONE] `tests/unit/test_sweep.py` (16 tests: §8 selection + spec parse) + `tests/integration/
  test_sweep_engine.py` (9 tests: distinct cells, resume, OOB-before-run, E3b, unregistered objective,
  selfmod enabled=1 PROPOSED row, disabled=0 rows).

### Green gate (all 5 legs, from worktree root)
1. `uv run ruff check .` → clean.
2. `uv run mypy core agents eval ops scheduler scripts` → Success, 0 issues (201 files).
3. argless `uv run mypy` → 69 (HELD baseline; the two transient errors from `ProposalLedger(":memory:")`
   were fixed to `ProposalLedger(Path(":memory:"))`, the repo idiom).
4. `uv run python -m ops.type_gate` → OK.
5. `uv run pytest -q -m 'not live'` → 1287 passed, 10 skipped (1264 baseline + 23 new).

### Notes for a fresh agent
- The engine NEVER auto-approves/executes: `optimize` calls `SelfModLoop.propose` only, which writes a
  PROPOSED row via `ledger.propose`. Verified in `test_selfmod_enabled_lands_exactly_one_proposed_row`
  (status PROPOSED, approver None, executed_at/resolved_at None).
- Emission gates on `selfmod_loop.config.selfmod.enabled` — never forces the switch.
- Finding-0089 (spec-fidelity, open) records the select-pipeline ambiguity + the recorded default.
- Committed on `build/bp-049`. Orchestrator merges after scrutiny (do NOT merge here).
