# Journal — bp-044 `harness-report`: the report generator + cost ledger (E4)

> The fresh-agent contract: a new session with only `plan.md` + this journal + the write-scope files
> must continue without re-asking. Checkpoint at every semantic boundary. Status flips are the
> orchestrator's, by hand.

## 2026-07-15 — GRADUATED (proposed), awaiting owner `proposed→ready` blessing

- Graduated by the orchestrator (opus, self-driven) from ratified `dn-evaluation-harness` §3 **E4**.
  Milestone-1 tranche member (renders the first A/B run).
- **Grounding done in-session** (direct reads, no subagents). Key facts:
  - `eval/harness/report.py`, `scripts/report.py`, `data/reports/` all ABSENT → greenfield renderer +
    a new report root. The ONE existing-code touch is `core/stores/telemetry.py` (the cost ledger).
  - Telemetry migration pattern grounded (`telemetry.py:22` `SCHEMA_VERSION = 2`; ordered `_DDL` list
    of `CREATE TABLE IF NOT EXISTS` + a `schema_migrations` version row; the `context_usage` table was
    the v1→v2 precedent). The cost ledger follows exactly: append one `harness_cost` table, bump to 3 —
    additive, every existing telemetry read/write stays green (the bit-identical-telemetry falsifier).
  - Attestation refs are OPAQUE provenance pointers read via `AttestationReader` Protocol
    (`core/ops_view.py:47`, `.all()`); the report *displays* the ref, does NOT verify chains (that's the
    E8 attestation battery). E1's `Reading.evidence_ref` + E2's `run_id` carry the refs.
  - No sparkline prior art (`grep` = 0) → a new pure `eval/harness/sparkline.py` (Unicode-block, no deps).
  - The load-bearing invariants: every figure carries its `(spec_hash, corpus_ref, config_fingerprint,
    seed)` key (no unprovenanced number); `report.md` + `report.json` are ONE model, two renderings (a
    golden-file test pins both, so they can't drift); the renderer is model-free + deterministic; "no
    silent caps" — dropped/truncated coverage is recorded, never hidden.
- **Scope decisions:** three items — (8) pure sparkline; (9) the report model + markdown/JSON renderers
  (read-only over E1/E2/telemetry); (10) the additive `harness_cost` table + cost appendix. Item
  numbering continues the family (Items 8–10).
- **Cost estimate:** opus 200k (deterministic templating + one additive telemetry table + golden-file
  tests). Self-driven ~0.5–0.8×. No fable, no xhigh.
- **Not started** — `proposed`. `depends_on: [bp-042, bp-043]` (reads their store surfaces; must build
  AFTER both land). Owner blesses `proposed→ready`, then `/build bp-044` (or delegate — budget gate first).

## 2026-07-16 — IN-PROGRESS (delegated builder, opus). Item 8 CLOSED.

Worktree bootstrap: my branch was 21 commits behind main; fast-forwarded (`git merge --ff-only main`)
so bp-042/bp-043 built code + the plan are present. `active-plan` = bp-044.

**Grounding refreshed against the BUILT surfaces (not the plans):**
- `eval/harness/store.py` — `EvalResultsStore.query(*, metric_name=None, corpus_ref=None)` returns
  `Reading`s ORDERED by full key then metric_name (deterministic). `Reading.key: EvalKey`,
  `type_tag`, `evidence_ref`. `query()` does NOT gate on registration.
- `eval/harness/registry.py` — `get(name)` is FAIL-CLOSED (raises KeyError on unregistered).
- `core/stores/runledger.py` — `runs(*, pipeline=None)` / `claims(*, run_id=None, novel_only=False)`
  return `list[dict]`; runs carry `pipeline`, `corpus_digest`, `config_fingerprint`; claims carry
  `run_id`, `kind`, `confidence`, `novel`. NO seed/spec_hash on ledger rows.
- `core/stores/telemetry.py` — `SCHEMA_VERSION=2`, ordered `_DDL`, version-guarded insert; the
  `context_usage` table is the v1→v2 additive precedent I mirror for v3.
- `core/dreaming/shadow.py` — writes eval Readings keyed with `spec_hash=sha256("shadow-runner/v1‖"
  +pipeline)`, `corpus_ref=corpus_digest`, `config_fingerprint`, `seed=self.seed`, AND
  `structural_axes.<axis>` (type_tag "Inv", UN-registered — finding-0086).

**finding-0086 reconciliation (recorded, resolved in-session — spec-fidelity, NOT routed):** the
renderer resolves REGISTERED metrics via `registry.get(...)` for their `type_tag`; the
`structural_axes.*` family is read directly from `query(metric_name=...)` WITHOUT registry resolution
(they'd raise KeyError through the fail-closed `get`). Treated as `type_tag="Inv"` as written. I do
NOT register them (registry.py is out of write_scope) and do NOT widen scope.

**Key design reconciliation (spec-fidelity, resolved — NOT a §10 stop):** "every figure carries its
EvalKey" is absolute for eval-store-sourced figures (curves, drift) — the anchor is a REAL
`Reading.key`. But the A/B table is sourced from the RUN LEDGER and the cost appendix from TELEMETRY,
neither of which carries a full EvalKey (no spec_hash/seed on a ledger run; only run_id on a cost
row). Critically, eval-store readings CANNOT be attributed to a pipeline by the report — pipeline is
encoded opaquely in `spec_hash` (shadow's `sha256(prefix‖pipeline)`), which the report doesn't know;
(corpus_digest, config_fingerprint) are SHARED by both pipelines over one snapshot. So the A/B split
comes from the ledger's explicit `pipeline` column, NOT from attributing eval readings. For
ledger/telemetry-sourced figures I construct a provenance key from the source row's REAL identifiers
(`corpus_ref=corpus_digest`, real `config_fingerprint`) with a transparent `spec_hash` source-tag
(`"ledger:ab"` / `"telemetry:harness_cost"`) and `seed=0` (the source has no seed dimension);
`evidence_ref` always carries the source's primary id (a `run_id`). No eval-store reading lacks its
key → not the §10 stop; the ledger/telemetry simply have their own narrower identity, faithfully
carried. Every number keeps a recoverable provenance.

**Item 8 CLOSED** — `eval/harness/sparkline.py` + `tests/unit/test_sparkline.py`. Pure Unicode-block
renderer: empty→"", single/constant→flat lowest-bar row, else round-to-nearest band position
(monotone in v → deterministic). 6 tests green. (Fixed one test bug: `zip(strict=True)` over offset
slices → `strict=False`.)

**Item 10 CLOSED** (built before Item 9's appendix consumes it) — `core/stores/telemetry.py`
additive cost ledger: `SCHEMA_VERSION` 2→3, appended `harness_cost (ts, run_id, wall_clock_s,
models_resident, cells_completed, cells_skipped, note)` to `_DDL` (mirrors the v2 `context_usage`
precedent EXACTLY), `TelemetryWriter.record_harness_cost(run_id, *, wall_clock_s, models_resident,
cells_completed, cells_skipped, note=None)`, `TelemetryReader.harness_costs(run_id=None)` +
`harness_cost_count()`. `tests/unit/test_cost_ledger.py` (4 tests): round-trip, v3 migration row,
run_id filter+ordering, and the additive-DDL proof (vitals+context_usage paths + the scoped
write-only/read-only split UNCHANGED). `tests/integration/test_telemetry.py` stays green UNMODIFIED
(the additive falsifier). No existing table/reader/writer signature touched.

**Item 9 CLOSED** — `eval/harness/report.py` + `scripts/report.py` + `tests/unit/test_harness_report.py`
(9 tests). The ONE model `Report(topic, date, figures, coverage_notes)` / `Figure(title, key, kind,
payload, evidence_ref)`; `build_report(...)` pure + READ-ONLY over E1/E2/telemetry; `render_markdown`
+ `render_json` both derive from `asdict(report)` (sort_keys) so they cannot drift; `write_report`
into `data/reports/<date>-<topic>/`. Figures: curves (per registered metric, drift_D + structural_axes
excluded), the drift study (`drift_D` trajectory + per-axis `structural_axes.*` decomposition read
WITHOUT `registry.get` — finding-0086), the A/B table (per-pipeline run/claim/novel from the ledger's
`pipeline` column — eval store can't be pipeline-attributed, see the design reconciliation above), and
the cost appendix (from `harness_costs()`). `FigureKind(StrEnum)` (members are str → `kind: str` pin
honored). Tests assert: every figure keyed (b), md/json same figures+keys (a), A/B splits phase7 vs
dream_v2 (c), byte-identical re-render (d), no store mutation (read-only), write emits both files.
`scripts/report.py` stamps the date at the CLI boundary (renderer stays clock-free).

**GREEN GATE — all 5 legs, run separately:**
1. `ruff check .` → **All checks passed!**
2. `mypy core agents eval ops scheduler scripts` → **Success: no issues found in 195 source files** (0).
3. argless `uv run mypy` → **Found 69 errors in 20 files (checked 399)** — EQUALS the pinned
   tests/-baseline of 69 (my new tests added ZERO; exit 1 there, as expected — that is why the legs
   are NOT &&-chained).
4. `python -m ops.type_gate` → membership OK + bare-ignore scan OK (exit 0).
5. `pytest -q -m 'not live'` → **1217 passed, 10 skipped, 9 deselected** (63s). Existing telemetry
   tests green UNMODIFIED.

All three items landed, all acceptance tests + falsifiers satisfied. No §10 stop hit; no finding
filed (finding-0086 reconciled in-session per the task brief; the ledger/telemetry key reconciliation
resolved in-session as spec-fidelity). Ready to commit on the worktree branch (orchestrator merges).
