# Journal — bp-058: the σ-sweep experiment wiring

## Status: PROPOSED (awaiting owner `proposed → ready` blessing — owner-only, by hand)

### Graduation (2026-07-17, orchestrator, opus/high)
Graduated from the RATIFIED, FROZEN pre-registration `dn-sigma-sweep-experiment` (commit `d932670`).
The note §3 licenses exactly ONE thin build item (~100–120k, eval/scripts write scope, no core); this
plan is that item, decomposed into three serial sub-items (control battery → blind sample → composite
report). All consumed interfaces are BUILT (sweep/fibers/gate/report/registry/store/CertifiedCut/the
F9 fixtures) and pinned inline in §6 verbatim from their sources — a builder infers no design.

Grounded pass complete: §3 answers Q1–Q6 with `path:line` citations; the one open definition
(tier-stability partition, Q6) is a recorded grounded decision, parked in §11, not inferred silently.
Two layering risks surfaced and mitigated in §3 (importing the `tests/quality/` fixtures into a
shipped harness module — a legitimate reuse the note V3 mandates; and no-silent-caps everywhere).

**Estimate:** opus / 150k (calibrated against bp-057: 2 items, 162k actual; this is 3 thinner
wiring items, no new math — glue + evidence rendering + tests). Blast radius: all read-only sensing;
writes only `data/reports/`.

**Next (gated on the owner):** owner reviews bp-058 item-by-item and blesses `proposed → ready` by
hand (record the bless commit). THEN `/build bp-058` — self-build or one delegated opus builder,
serial, fresh worktree off HEAD, RESERVE finding-0096, 5-leg gate (ruff · mypy targeted 0 · argless
**69** · type_gate · pytest not-live), merge, seal with cost.actual. Do NOT build before the bless.

---

## Build session (2026-07-17, session-23, OPUS/high, self-build, branch `bp-058-build` off `b16dbb2`)

Owner blessed `proposed → ready` by hand (`d646a25`) and directed self-build with supervision here.
Context manifest §2 was read in full during graduation — grounded, no re-read needed.

### Item 1 — control battery (V3) — CLOSED ✅
- `eval/harness/experiment.py`: `ControlOutcome` + `run_control_battery(*, resolution=5)` — a faithful
  LIFT of `test_sigma_gate._compute_validation` into the harness (noise-only rate; planted-in-noise
  planted-reach + tiered-vs-best-single-σ precision), verdict via `GateValidation.ship`. Fixtures
  imported LAZILY from `tests/quality/fixtures_sigma_gate` (no test-dep drag at import). Model-free,
  re-drives the pipeline each call, writes no store. `render_control_markdown` returns the section
  lines for the composite report (report-layer values, NOT eval-store readings — §3 Q3).
- `scripts/experiment.py`: `controls` subcommand, seal-first (Invariant 1), GREEN⇒exit 0 / RED⇒exit 1.
- `tests/unit/test_experiment_controls.py`: 4 tests — GREEN on current pipeline; faithful to bp-057's
  known-good values (noise 0.0, tiered 1.0, baseline < 1.0); determinism; a synthetic RED names 3
  failing clauses.
- **Acceptance MET:** `uv run scripts/experiment.py controls` → GREEN, exit 0, all three criteria
  reproduce (noise 0.0000, planted True, tiered 1.0000 vs 0.6667); `pytest tests/unit/test_experiment_controls.py`
  4 passed. Falsifier (battery green while a criterion red) foreclosed by the equality check.
- No finding needed. Next: Item 2 (blind-sample generator).

### Item 2 — blind-sample generator (SE-3) — CLOSED ✅
- `eval/harness/experiment.py`: `BlindItem` / `BlindSample` + `generate_blind_sample(tiered, content,
  *, seed, cap=24)` — stratified ⌊cap/3⌋ per tier (8/8/8 @ 24), all-available + a recorded note on
  shortfall; deterministic via one `random.Random(seed)` consumed in fixed order (sample SETTLED→
  HUNCH→RETAINED over claim-id-sorted strata, then shuffle presentation). Content is caller-supplied
  (`claim_id → surface_text`), NEVER the tier; blinding is structural. `render_blind_presentation`
  (UNLABELED — no tier/pers/label) + `render_sealed_labels` (JSON `claim_id → tier`, sort_keys) +
  `write_blind_sample` → two DISTINCT files under `data/reports/<date>-<topic>/blind/`.
- `scripts/experiment.py`: `blind-sample` subcommand + the shared `_resolve_run_tiering(cfg, spec)`
  helper (reads the completed run's ledger + eval store, `run_fibers`, tiers the select_pipeline lane
  at frozen θ; confidence + content built straight from ledger columns — no test-fixture helper on
  the real path). Guards an empty/absent ledger ("nothing to sample — run the sweep first").
- `tests/unit/test_experiment_blind.py`: 6 tests — 8/8/8 stratification; determinism (identical
  bytes same seed); shortfall recorded (no silent cap); NO tier/pers/label leak in the presentation;
  sealed labels a distinct recoverable join; cap bounds total + missing-content note.
- **Acceptance MET:** `pytest tests/unit/test_experiment_blind.py` 6 passed; `blind-sample` wires
  end-to-end (correctly reports "nothing to sample" on the pre-run ledger). Falsifiers (label leak /
  non-determinism / silent undersample) foreclosed by the three targeted tests.
- No finding needed. Next: Item 3 (composite report assembler).

### Item 3 — composite report assembler (§2.3) — CLOSED ✅
- `eval/harness/experiment.py`: the §2.3 assembler. `CompositeReport`/`CompositeSection` (one model,
  two renderings — the report.py anti-drift discipline) + `assemble_composite(...)` gluing six
  sections in FIXED order: **V1–V5 evidence** (V1 from `fibers_result.evidence` + commit_sha; V2 the
  certified cut or a preview note — NEVER fabricated; V3 control verdict; V4 determinism check; V5
  selfmod posture), **SE-1** curve+selection (reads `SweepResult`, never re-derives), **SE-2** fibers
  summary (registered-names discipline: an unregistered displayed metric is RECORDED, report.py
  precedent), **SE-3** tier occupancy + stability (`tier_occupancy` + `tier_stability` = agreement
  fraction over two caller-supplied tierings, §3 Q6), **E4 A/B** (embeds a pre-built `Report`), and
  the **blind-judgment** cross-tab (descriptive; bars read in analysis). Every None piece degrades to
  a preview stub + a coverage note (no silent cap). Deterministic (`date`/`commit_sha` in; sort_keys).
  READ-ONLY: takes verdicts + a pre-built Report; emits NO eval-store readings; writes only
  `data/reports/` (composite.{md,json}).
- **Design refinement (journaled, not a spec change):** the assembler takes a pre-built E4 `Report`
  rather than raw stores (the plan §7 signature listed the stores). Strictly cleaner + testable
  in-memory; the §2.3 content is identical. The script calls `build_report` and passes it in.
- `scripts/experiment.py`: `report` subcommand + `_reoptimize` (reconstructs SE-1's verdict over the
  completed store WITHOUT re-driving — the optimizer is deterministic/model-free). Robust: a
  locked/absent telemetry store (e.g. the live daemon holds the duckdb lock) degrades the E4 A/B to a
  preview + note, never a crash, never a fabricated cost.
- `tests/unit/test_experiment_report.py`: 6 tests — all six §2.3 sections present + V1–V5 recorded;
  determinism (identical json+md bytes); preview degrades gracefully with coverage notes; unregistered
  metric recorded not silently shown; occupancy+stability arithmetic; blind cross-tab join.
- **Acceptance MET:** `pytest tests/unit/test_experiment_report.py` 6 passed; `report` wires
  end-to-end (6 sections written to composite.{md,json}; V1 evidence + V3 GREEN populated pre-run,
  the rest honest previews with coverage notes). data/ gitignored — no artifact in the commit.
- No finding needed.

### 5-leg gate — ALL GREEN (2026-07-17)
- **ruff** (5 files): All checks passed (post reflow + orphan cleanup; house line-length 100).
- **mypy targeted** (5 files): Success, 0 issues (fixed `_reoptimize` return → `SweepResult | None`).
- **argless mypy**: 69 errors (baseline UNCHANGED — the new files add 0).
- **type_gate**: 11 passed.
- **pytest not-live** (`-m 'not live and not podman and not needs_vault and not needs_restic'`):
  **1436 passed, 6 skipped, 20 deselected, 0 failed** (16 new experiment tests).
- **End-to-end verified**: `controls` → GREEN exit 0; `blind-sample` → empty-ledger guard fires;
  `report` → 6-section composite written to data/reports/, V1+V3 populated, honest previews for
  V2/V4/SE-1/SE-2/E4 (pre-run), telemetry-lock degraded gracefully.

**All three items CLOSED. Ready to merge + seal.** No findings filed (finding-0096 reserved, unused).
