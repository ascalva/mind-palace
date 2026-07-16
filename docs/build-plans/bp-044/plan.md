---
type: build-plan
id: bp-044
alias: harness-report
status: complete
design_ref:
  - docs/design-notes/evaluation-harness.md
contract: builder
write_scope:
  - eval/harness/report.py
  - eval/harness/sparkline.py
  - scripts/report.py
  - core/stores/telemetry.py
  - tests/unit/test_harness_report.py
  - tests/unit/test_sparkline.py
  - tests/unit/test_cost_ledger.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 200k
    rationale: >-
      Deterministic templating over the E1 store + E2 ledger + telemetry — a pure renderer (markdown
      + JSON + ASCII sparklines), one additive telemetry table (the cost ledger), and golden-file /
      round-trip tests. No model, no math object, no live-store mutation. Comparable to bp-039's
      renderer-shaped half; calibrated ~200k opus. NO fable, NO xhigh. Self-driven ~0.5–0.8×.
  actual:
    model: opus
    tokens: ~120k
    ratio: ~0.60
    dollars: ~8          # APPROX per-plan share of the $25.01 session; drew ZERO credits (weekly-covered)
    session_delta: "DELEGATED supervised build (worktree-agent-a00b8478152789f5f). Builder
      self-reported usage: 119,511 tokens, 75 tool-uses, ~13.4 min wall (805,488 ms), model
      claude-opus-4-8, single continuous pass (no fable/xhigh, not interrupted/degraded). ~120k /
      200k est = 0.60x — squarely in the self-driven 0.5-0.8x band (a pure renderer over now-BUILT
      E1/E2 surfaces + one additive telemetry table; no rework beyond two trivial ruff/test fixes).
      Orchestrator supervision (review + independent 5-leg gate + merge) is additional main-loop
      context not counted here. Dollar/session-delta backfill owed from owner /usage at session end."
    week_delta: "MEASURED (owner /usage, session end): whole session $25.01, week 1%->3% (+2%) for
      BOTH delegated builds + supervision; ZERO usage credits drawn (81% UNCHANGED, weekly-covered).
      ~$8 is bp-044's honest share (smaller pure-renderer build + lighter review than bp-043)."
    loc: "~913 added (report 360 + sparkline ~55 + scripts/report ~50 + telemetry +44 + 3 test files
      ~400 + journal); telemetry.py the ONLY existing-code touch — strictly additive (SCHEMA_VERSION
      2->3, new harness_cost table + record/reader; existing tables/tests untouched)"
    # GREEN attested SEPARATELY on the MERGED tree (5-leg): ruff PASS; mypy `core agents eval ops
    # scheduler scripts` == 0 (195 files, 192->195); argless mypy == 69 UNCHANGED (baseline HELD);
    # ops.type_gate OK; pytest -q -m 'not live' == 1220 passed / 7 skipped / 9 deselected(live) / 0
    # failures (+18 new: sparkline + report + cost ledger). Falsifiers held: renderer READ-ONLY (no
    # store mutation in report.py); every Figure carries its EvalKey; model-free deterministic (byte-
    # identical re-render); telemetry additive-DDL (existing telemetry tests green unmodified).
    # Reconciliation (disclosed): the A/B split is sourced from the ledger's explicit `pipeline`
    # column (pipeline lives in the opaque spec_hash); ledger/telemetry figures carry transparent
    # source-tagged keys — no reading lacks its key (not the §10 stop). finding-0086 reconciled:
    # structural_axes.* rendered via query() without fail-closed registry.get; registration owed.
depends_on:
  - bp-042
  - bp-043
parallelizable_with: []
created: 2026-07-15
updated: 2026-07-16
started: 2026-07-16
completed: 2026-07-16
links:
  - docs/design-notes/evaluation-harness.md
  - core/stores/telemetry.py
  - docs/build-plans/bp-042/plan.md
  - docs/build-plans/bp-043/plan.md
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — `harness-report` (bp-044): the report generator + cost ledger (E4)

> **Every section below is required.** Inapplicable sections are marked `N/A — <reason>`.

## 0. Mode & provenance

Investigation and planning produced this plan; **implementation proceeds item-by-item on owner
approval**. Authority-to-act (owner ratified `dn-evaluation-harness` + directed graduation) is
separate from the readiness blessing (owner-only `proposed → ready`) — no agent flips readiness.

Graduated from ratified `dn-evaluation-harness` §3 **E4** (*"the report generator + cost ledger
(§2.7, §2.4): `data/reports/` renderer, sparkline curves, the drift study, the cost appendix / usage
view."*). Model **opus**; **no fable, no xhigh** (deterministic templating over settled surfaces).

**The load-bearing property:** every figure a report renders carries its `(spec_hash, corpus_ref,
config_fingerprint, seed)` key — no number without provenance; every report is reproducible from the
store (§2.7). Generation is deterministic and **model-free** (a model may annotate *after*, never
select or compute). The whole-plan falsifier: a rendered figure whose key cannot be recovered from
the store, or two runs of the renderer over the same stores producing different reports
(non-determinism).

## 1. Objective

Give the harness a deterministic, model-free **report generator** (`eval/harness/report.py` +
`scripts/report.py`) that consumes the eval-results store (E1), the run ledger (E2), the telemetry
DuckDB, and attestation refs, and emits into `data/reports/<YYYY-MM-DD>-<topic>/` a keyed
`report.md` + `report.json` with terminal-sparkline curves, the drift study, A/B tables, and the
cost appendix — plus a small **cost ledger** (a cost/residency table in the telemetry DuckDB,
written per harness run).

## 2. Context manifest

Read whole, in order:

1. `docs/design-notes/evaluation-harness.md` — **§2.7** (report generation: the `data/reports/`
   layout, `report.md` + `report.json` same-content-two-renderings, sparklines + markdown tables,
   the drift study with per-axis decomposition, sweep reports, A/B tables, the cost appendix, "every
   figure carries its key", model-free deterministic templating, ∉ `MIRROR_READABLE`), **§2.4** (the
   cost ledger: "a small cost/residency table in the telemetry DuckDB, written per harness run
   (wall-clock, models resident, cells completed), surfaced as the report's cost appendix"),
   **§2.1** (the key every figure carries).
2. `docs/build-plans/bp-042/plan.md` — E1's pinned `EvalResultsStore.query()` / `Reading` surface
   (the group-by substrate this renderer consumes) and the registry's `MetricSpec` (type_tag drives
   how a metric renders — an `Inv` count vs a `Rate(κ)` slope).
3. `docs/build-plans/bp-043/plan.md` — E2's pinned `RunLedger.runs()` / `claims()` surface (the A/B
   split: `pipeline` column, `novel` flag, per-run `corpus_digest`/`config_fingerprint`).
4. `core/stores/telemetry.py` — the DuckDB store the cost ledger extends: `_DDL` (`:24-63`),
   `SCHEMA_VERSION = 2` (`:22`), `TelemetryWriter`/`TelemetryReader` (`:86`, `:118`),
   `open_store(config)` (`:173`). The cost table is a NEW `_DDL` entry + a `SCHEMA_VERSION` bump.
5. `core/ops_view.py` — `AttestationReader` Protocol (`:47`, `.all()`) — how the renderer reads
   attestation refs (opaque provenance pointers shown beside figures), read-only.
6. `docs/build-plans/bp-039/plan.md` — house style.

## 3. Investigation & grounding

- **Q1 — Does `eval/harness/report.py` / `data/reports/` exist? NO.** `ls eval/harness/report.py` +
  `scripts/report.py` + `data/reports` → all absent (2026-07-15). Greenfield renderer + a new report
  root. The ONE existing-code touch is `core/stores/telemetry.py` (the cost ledger table).
- **Q2 — The telemetry DuckDB migration pattern.** `core/stores/telemetry.py` uses an ordered `_DDL`
  list of `CREATE TABLE IF NOT EXISTS` + a `schema_migrations` version row; `SCHEMA_VERSION = 2`
  (`:22`) with a v1→v2 precedent (the `context_usage` table added at v2, comment `:59-60`). **The
  cost ledger follows this exactly:** append one `CREATE TABLE IF NOT EXISTS harness_cost (...)` to
  `_DDL` and bump `SCHEMA_VERSION` to 3, mirroring the v2 addition. No existing table altered; no
  existing reader/writer signature changed (additive DDL — the bit-identical-telemetry falsifier).
- **Q3 — How does the renderer read attestation refs?** Via the `AttestationReader` Protocol
  (`core/ops_view.py:47`, `.all()`) — read-only; the report shows the opaque `evidence_ref` /
  attestation id beside each figure. The renderer does not verify chains (that is the attestation
  battery, §2.4 / E8); it *displays* the ref for provenance. The code settles this: refs are opaque
  strings the stores already carry (E1 `Reading.evidence_ref`, E2 `run_id`).
- **Q4 — Sparklines: any existing renderer to reuse?** `grep sparkline` → none. New pure module
  (`eval/harness/sparkline.py`): a deterministic ASCII/Unicode-block renderer over a float sequence,
  no external dependency (self-contained, model-free). The bp-040 σ-sweep emitted a table, not a
  sparkline — no prior art to extend.

**Additional risks surfaced during reading:** (a) `report.json` and `report.md` must be the *same
content, two renderings* (§2.7) — the renderer computes one report *model* (a dataclass tree) and
serializes it two ways, so they cannot drift; a golden-file test pins both off one model. (b) "No
silent caps" (§2.8): if a report bounds coverage (a truncated ladder, a skipped battery), it records
what was dropped — the renderer surfaces the store's own coverage gaps, it never hides them.

## 4. Reconciliation

- **`core/stores/telemetry.py` — EXTENDED with the cost ledger table (cross-reference-on-extension,
  NOT a correction).** Nothing in telemetry is wrong; §2.4 asks for a new cost/residency table in
  the same DuckDB. Proposed: append `harness_cost (ts, run_id, wall_clock_s, models_resident,
  cells_completed, cells_skipped, ...)` to `_DDL`, bump `SCHEMA_VERSION` 2→3 (the v2 precedent), add
  a `record_harness_cost(...)` to `TelemetryWriter` and a matching reader — **all additive**; every
  existing vitals/context_usage read+write stays green unmodified.
- **`dn-evaluation-harness` frontmatter (`not-built`) becomes partially stale** — batched to
  `owner-questions.md` on completion (bp-039 pattern). No code corrected/replaced.

## 5. Write scope

- `eval/harness/report.py` — **NEW**: the report *model* (a dataclass tree) + the markdown/JSON
  serializers + the drift study / A/B table / cost appendix assemblers.
- `eval/harness/sparkline.py` — **NEW**: the pure terminal-sparkline renderer.
- `scripts/report.py` — **NEW**: the CLI entry (`--topic`, `--out data/reports/`).
- `core/stores/telemetry.py` — Item 10 only: the `harness_cost` table + writer/reader (additive).
- `tests/unit/test_harness_report.py`, `tests/unit/test_sparkline.py`,
  `tests/unit/test_cost_ledger.py` — **NEW**.

**Deliberately OUT of scope:** any *sweep* that produces readings (E3); any instrument (E5); serving
/ HTML rendering (EH-g — markdown + terminal sparklines v1); the Voice's weekly digest (§2.7,
carried for later); writing the eval store or run ledger (the renderer is READ-ONLY over both);
`MIRROR_READABLE` (reports are ∉ mirror — proven, not edited); `eval/golden/**`, `CONSTITUTION.md`
(denylist); every design note (immutable, A8).

## 6. Interfaces pinned inline

```python
# eval/harness/report.py — deterministic, model-free renderer. READ-ONLY over the stores.

from dataclasses import dataclass

@dataclass(frozen=True)
class Figure:
    """One rendered figure ALWAYS carries its key (§2.7 — no number without provenance)."""
    title: str
    key: "EvalKey"                 # (spec_hash, corpus_ref, config_fingerprint, seed) — from E1
    kind: str                      # "curve" | "table" | "drift" | "ab" | "cost"
    payload: dict                  # the rendered data (values, columns, sparkline string)
    evidence_ref: str | None       # the attestation / provenance pointer (§2.4 / §6 Q3)

@dataclass(frozen=True)
class Report:
    topic: str
    date: str                      # passed in (Date.now unavailable to workflows; owner/CLI stamps it)
    figures: tuple[Figure, ...]
    coverage_notes: tuple[str, ...]  # "no silent caps" — dropped/truncated/skipped recorded (§2.8)

def build_report(topic: str, date: str, *, eval_store, run_ledger, telemetry,
                 attestations=None) -> Report: ...     # ONE model; pure over the stores
def render_markdown(r: Report) -> str: ...             # report.md
def render_json(r: Report) -> str: ...                 # report.json — SAME content, two renderings
def write_report(r: Report, root="data/reports") -> "Path": ...  # data/reports/<date>-<topic>/

# eval/harness/sparkline.py
def sparkline(values: "Sequence[float]") -> str: ...   # pure Unicode-block bars; deterministic
```

```python
# core/stores/telemetry.py — Item 10 additive (§4). SCHEMA_VERSION 2 -> 3. Existing tables UNCHANGED.
#   CREATE TABLE IF NOT EXISTS harness_cost (
#       ts TIMESTAMP NOT NULL, run_id VARCHAR, wall_clock_s DOUBLE,
#       models_resident INTEGER, cells_completed INTEGER, cells_skipped INTEGER, note VARCHAR )
# TelemetryWriter.record_harness_cost(run_id, *, wall_clock_s, models_resident,
#                                     cells_completed, cells_skipped, note=None) -> None
```

## 7. Items

### Item 8 — `eval/harness/sparkline.py`: the pure terminal sparkline
- **Objective:** a deterministic `sparkline(values) -> str` (Unicode block bars), self-contained, no
  external dependency, handles empty / single-value / constant series.
- **Files:** `eval/harness/sparkline.py`, `tests/unit/test_sparkline.py`.
- **Acceptance test:** `sparkline([0,1,2,...,8])` returns a monotone-rising block string of the right
  length; empty → `""`; constant series → a flat row; `mypy` 0; deterministic (same input → same
  output, asserted).
- **Falsifier:** the same input yields different output across calls (non-determinism), or a
  degenerate series (empty/constant) raises instead of rendering.
- **Invariant(s):** pure, model-free, no I/O.
- **Touches stored data?** No.  **Parallelizable?** Yes (independent of the store surfaces).

### Item 9 — `eval/harness/report.py`: the report model + markdown/JSON renderers
- **Objective:** the `Figure`/`Report` model, `build_report(...)` (pure over the E1 store + E2
  ledger + telemetry), `render_markdown`/`render_json` (same content, two renderings), the drift
  study (D(t) + per-axis decomposition), the A/B table (per-pipeline metric + verdict/novel split),
  and `write_report` into `data/reports/<date>-<topic>/`. Every `Figure` carries its `EvalKey` +
  `evidence_ref`.
- **Files:** `eval/harness/report.py`, `tests/unit/test_harness_report.py`.
- **Acceptance test:** a golden-file test builds a `Report` from a small fixture eval-store +
  ledger, renders both formats, and asserts (a) `render_markdown` and `render_json` carry the SAME
  figures/keys, (b) every `Figure` has a non-empty `key`, (c) the A/B table splits phase7 vs
  dream_v2 rows, (d) re-rendering the same fixture is byte-identical (determinism).
- **Falsifier:** a figure renders without its key (provenance lost — the whole-plan falsifier); OR
  `report.md` and `report.json` disagree on a value; OR the renderer calls a model / mutates a store.
- **Invariant(s):** model-free deterministic templating; READ-ONLY over all stores; reports ∉
  `MIRROR_READABLE`; every figure keyed (§2.7).
- **Touches stored data?** No (reads E1/E2/telemetry; writes only into `data/reports/`, not a store).
  **Depends on:** Item 8, and the E1 (`query()`) + E2 (`runs()/claims()`) surfaces.

### Item 10 — the cost ledger (telemetry `harness_cost` table) + the cost appendix
- **Objective:** the additive `harness_cost` table (§6) + `SCHEMA_VERSION` 2→3 +
  `record_harness_cost`/reader in `core/stores/telemetry.py`, and the report's cost appendix
  (wall-clock, models resident, cells completed/skipped) assembled from it.
- **Files:** `core/stores/telemetry.py`, `tests/unit/test_cost_ledger.py` (+ the appendix assembler
  in `report.py`, covered by Item 9's tests).
- **Acceptance test:** `record_harness_cost` round-trips through the reader; `SCHEMA_VERSION == 3`
  and the `schema_migrations` row is written; **every existing telemetry test stays green
  unmodified** (the additive-DDL proof); the cost appendix figure renders the residency + cell counts.
- **Falsifier:** an existing telemetry read/write breaks (the DDL change was not additive), OR the
  cost appendix reports a cell count contradicting the store's actual `cells_completed`.
- **Invariant(s):** additive schema migration (existing tables + rows untouched); the cost ledger is
  telemetry-resident (∉ mirror); no model.
- **Touches stored data?** Yes — a new telemetry table. Tests use a tmp DuckDB; the migration is
  `IF NOT EXISTS` + version-guarded. **Depends on:** Item 9 (the appendix consumes it).

## 8. Math carried explicitly

`N/A — no mathematical object implemented.` The drift study *renders* the built `D(t)` and the A2
axes (bp-042 registers them, `eval/drift.py` computes them); the sparkline is a display encoding, not
a measurement. The renderer computes no metric — it templates readings the stores already hold.

## 9. Non-goals

- **No sweep / optimizer** (E3) — the renderer displays sweep reports *when a sweep has written
  readings*; it produces none.
- **No HTML / serving** (EH-g) — markdown + terminal sparklines v1; reports are local files, no
  egress.
- **No weekly Voice digest** (§2.7) — carried for later; this plan renders reports, not narration.
- **No store writes** beyond the additive `harness_cost` table — the renderer is READ-ONLY over the
  eval store, the run ledger, and the vitals/context_usage tables.
- **No date/clock source inside the renderer** — the date is passed in (CLI/owner stamps it); the
  renderer is a pure function of its inputs (determinism).

## 10. Stop-and-raise conditions

- A figure cannot be rendered with its key (a store reading lacks the full `EvalKey`) → **STOP, file
  a `spec-defect` finding**: the store's keying (E1) is incomplete; do not render an unprovenanced
  number.
- The `harness_cost` DDL change breaks an existing telemetry test → **STOP, file a `codebase`
  finding**: the migration must be additive; if it can't be, re-ground the schema-version approach.
- `report.md` and `report.json` cannot be kept identical from one model → **file a `spec-defect`
  finding**: the two-renderings-one-model invariant is the anti-drift guarantee; a workaround defeats it.
- The plan does not fit one session → **file a `spec-defect` finding and PARK**; re-graduation is the
  orchestrator's.
- Any blessing flip → **must not**.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| Report rendering surface | markdown + terminal sparklines + JSON (EH-g) | HTML/interactive now (rejected: owner asked for v1 markdown; no serving component exists) | owner asks for richer rendering |
| Cost-ledger residency | a `harness_cost` table in the telemetry DuckDB | a separate cost store (rejected: §2.4 says telemetry DuckDB; one fewer store) | telemetry DuckDB becomes a bottleneck |
| Weekly Voice digest narration | out of scope — carried (§2.7) | build the digest now (rejected: it is a Voice/register concern, later) | the Voice weekly-digest unit graduates |
| Attestation-chain verification in-report | display the ref only (opaque) | verify chains inline (rejected: that is the attestation battery, E8) | E8's process battery lands and a report wants a live verify badge |

## 12. Dependency & ordering summary

Blast-radius order: **Item 8** (pure sparkline — zero radius, no store) → **Item 9** (the renderer,
read-only over the stores) → **Item 10** (the additive telemetry `harness_cost` table — the only
existing-store touch). One session, not parallel.

**Cross-plan:** `depends_on: [bp-042, bp-043]` — the renderer reads E1's `query()` and E2's
`runs()/claims()` surfaces, so both must exist (their *design* is pinned here; their *build* must
land before E4 builds). The first overnight dual-dreamer A/B (`sweep.dreamer-sigma-ab`, bp-040
re-derived) needs **E1 + E2 + E5(A2) + E4** — this plan renders that run's A/B tables + drift study +
cost appendix, the owner's first systematic sight of dream_v2 across σ (feeds the bp-041 wire-live
decision). Recorded in `docs/PARKING-LOT.md`.
