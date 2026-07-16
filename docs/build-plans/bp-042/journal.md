# Journal — bp-042 `eval-results-store`: the eval-results store + metric registry (E1, keystone)

> The fresh-agent contract: a new session with only `plan.md` + this journal + the write-scope files
> must continue without re-asking. Checkpoint at every semantic boundary. Status flips are the
> orchestrator's, by hand.

## 2026-07-15 — GRADUATED (proposed), awaiting owner `proposed→ready` blessing

- Graduated by the orchestrator (opus, self-driven) from ratified `dn-evaluation-harness` §3 **E1**
  — the keystone of the milestone-1 tranche. (Full graduation rationale in the git history / PROGRESS.)

## 2026-07-15 — BUILD STARTED (owner blessed `proposed→ready`; orchestrator flipped `ready→in-progress`)

- Owner hand-blessed bp-042 (+ bp-045) `proposed→ready`; flips committed `d9be748`/`fc52eb9` (rule 0060).
- **Item 1 DONE — `eval/harness/store.py` + `__init__.py`.** `EvalKey`/`Reading` frozen dataclasses;
  `EvalResultsStore` over one DuckDB table `eval_results` PK `(spec_hash,corpus_ref,config_fingerprint,
  seed,metric_name)`; `put()` idempotent-by-key (present cell → return False, NEVER overwrites/dups),
  `has()`/`get()`/`query()`/`close()`; `open_eval_store(config)` → `derived_store.parent/eval_results.duckdb`
  (telemetry precedent). Smoke-verified append-only-by-key + confound separability.
- **Item 2 DONE — `tests/unit/test_eval_store.py`.** 5 tests PASS: round-trip; idempotent-by-key-no-overwrite
  (the append-only falsifier); resumability across a store REOPEN (replay inserts 0, all put=False);
  confounds separable one-key-component-at-a-time; query filters compose + empty store empty.
- **Item 3 IN PROGRESS — `eval/harness/registry.py` written** (MetricSpec + register/get fail-closed +
  dup-reject; the 4 built families registered: golden_recall/overlap/mean_distance [Inv,row1;recall
  guardrail], drift_D [Inv,row2,guardrail], f9_composite+3 components [Inv,row5], telemetry_wall
  [Rate(wall),row4]+context_usage [Inv,row4]).
- **BLOCKED then handled — scope-guard parse defect.** Editing `eval/metrics.py` (the absorption
  header) was DENIED: its write_scope entry has an INLINE COMMENT (`eval/metrics.py  # absorbed…`) that
  scope-guard did not strip, so the path didn't match. Same for `tests/integrity/test_eval_isolation.py`
  (Item 4's file). File SET is correct; only the YAML format breaks the guard. → Orchestrator plan-fix
  (strip inline comments from write_scope globs; intent unchanged) + a `spec-defect` finding (the
  recurring 0071/0072/0075/0084 lineage — the /graduate skill should forbid inline comments on
  write_scope globs). Then resume Item 3 (metrics.py absorption) + Item 4.

## 2026-07-15 — ALL 4 ITEMS DONE + 5-leg gate GREEN (build complete, awaiting orchestrator seal)

- **Item 3 DONE** — `eval/metrics.py` absorbed (header cross-reference + `__all__`; signatures
  unchanged); `tests/unit/test_metric_registry.py` 6 tests PASS (families resolve w/ correct
  type/source/guardrail; fail-closed on unknown; dup-reject; regression-default; absorption additive).
- **Item 4 DONE** — `tests/integrity/test_eval_isolation.py` 3 tests PASS: a transitive first-party
  import-graph BFS proves (a) no path eval-store → `core.ingest`, (b) no touch of the mirror world
  (`core.mirror`/`core.provenance`) ⇒ ∉ MIRROR_READABLE; + a negative control (the BFS *does* catch
  `core/ingest/pipeline.py` reaching `core.ingest`), so green means isolation, not a broken scanner.
- **5-LEG GREEN GATE (run SEPARATELY):**
  1. ruff `.` — PASS (fixed 15 E501 in-session).
  2. mypy `core agents eval ops scheduler scripts` — 0 issues, **190 files** (187→190 = +eval/harness
     `__init__`/`store`/`registry`).
  3. argless mypy — **69** UNCHANGED (the tooth HELD; the 5 test-only errors introduced were fixed:
     `EvalResultsStore.path` widened to `Path | str` so `":memory:"` typechecks; one Optional-access
     guarded).
  4. `ops.type_gate` — OK (tier-2 membership + bare-ignore scan).
  5. `pytest -q -m 'not live'` — **1183 passed / 7 skipped / 9 deselected (live)**, 0 failures; +14 new
     (5 store + 6 registry + 3 isolation). Live dream-e2e deselected (real 27b, Ollama-contended,
     finding-0069; the project's CI invocation deselects `live` too) — the deterministic + integration
     tiers are fully green.
- **Falsifiers all held:** same-key-diff-value → `put` returns False + first value preserved (append-
  only); replay across REOPEN inserts 0; confounds separable one-component-at-a-time; absorption keeps
  `recall_at_k` et al. bit-identical; the isolation BFS's negative control fires.
- **Scope note:** hit + handled the write_scope inline-comment parse defect (finding-0085); one
  orchestrator plan-fix commit (`e52151b`) unblocked, intent unchanged. bp-043/044/045 need the same
  one-line cleanup before they build (tracked in 0085 + the resume brief).
- **Next:** commit the build (Co-Authored-By — agent-authored code); orchestrator flips
  `in-progress→complete` + seals `cost.actual`; then `/build bp-045`.
