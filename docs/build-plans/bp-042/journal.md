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
