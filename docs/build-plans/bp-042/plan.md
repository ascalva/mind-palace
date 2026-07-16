---
type: build-plan
id: bp-042
alias: eval-results-store
status: proposed
design_ref:
  - docs/design-notes/evaluation-harness.md
contract: builder
write_scope:
  - eval/harness/__init__.py
  - eval/harness/store.py
  - eval/harness/registry.py
  - eval/metrics.py                 # absorbed into the registry (§2.2, E1); kept importable, re-exported
  - tests/unit/test_eval_store.py
  - tests/unit/test_metric_registry.py
  - tests/integrity/test_eval_isolation.py   # the "no path from eval store to ingest" integrity tooth
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 200k
    rationale: >-
      A NEW analytical store (DuckDB, one append-only keyed table) + a NEW metric registry
      (a namespace with typed declarations) + the absorption of `eval/metrics.py`, plus store
      round-trip tests, resumability tests, and one integrity tooth. Same deterministic,
      test-pinned, no-live-model character as bp-039 (240k est / 170k actual, self-driven) but
      SMALLER: one table, one registry dataclass, no lattice algebra. Calibrated at ~200k opus.
      Deterministic — NO fable, NO xhigh. Self-driven lands ~0.5–0.8×; delegated ~1.6×.
  actual: null
depends_on: []
parallelizable_with: []             # the keystone; E2/E4 read its surface but do not write it
created: 2026-07-15
updated: 2026-07-15
links:
  - docs/design-notes/evaluation-harness.md
  - docs/brainstorms/evaluation-harness.md
  - eval/metrics.py
  - eval/drift.py
  - core/stores/telemetry.py
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — `eval-results-store` (bp-042): the eval-results store + metric registry (E1, the keystone)

> **Every section below is required.** Inapplicable sections are marked `N/A — <reason>`.

## 0. Mode & provenance

Investigation and planning produced this plan; **implementation proceeds item-by-item on owner
approval**. Authority-to-act (the owner ratified `dn-evaluation-harness` 2026-07-15 and directed
its graduation) is separate from the readiness blessing (owner-only `proposed → ready`, by hand) —
no agent flips readiness.

Graduated from ratified `dn-evaluation-harness` §3 **E1** (verbatim: *"the eval-results store +
metric registry. DuckDB store with the §2.1 key, type tags, resumable keyed cells;
`eval/harness/registry.py` with the built metrics registered … The keystone — everything else
writes through it. Absorbs `eval/metrics.py`."*). This plan builds **only** the store, the key, the
registry, and the absorption — no sweep, no report, no instrument wiring (those are E3/E4/E5).
Model tier **opus**: a deterministic store + typed registry over a fully-specified design; **no
fable, no xhigh** (the design is banked, ratified).

**The load-bearing property of the whole plan:** a reading is uniquely addressed by the §2.1 key,
so (a) an already-present keyed cell is *skipped* on re-run — resumability is a consequence of
keying, not a feature bolted on — and (b) every stored number knows exactly what state it measured
(honest longitudinal comparison). The whole-plan falsifier: two writes with the same key and
different values are silently both kept (the key is not the primary discipline).

## 1. Objective

Give the harness a first-class **eval-results store** — an append-only DuckDB table keyed by
`(spec_hash, corpus_ref, config_fingerprint, seed)` holding one typed `(metric_name, value,
type_tag, interval_lo/hi?, evidence_ref)` reading per cell, resumable by key — and a **metric
registry** (`eval/harness/registry.py`) that is the single namespace every sweep, battery, and
report may reference, with the four built metrics (golden recall, drift `D`, F9 components,
telemetry vitals) registered and `eval/metrics.py` absorbed.

## 2. Context manifest

Read whole, in order:

1. `docs/design-notes/evaluation-harness.md` — the ratified design. **§2.1** (the unified key and
   its three separable confounds), **§2.2** ("The eval-results store — new, the keystone: DuckDB,
   append-only discipline … row is `(key, metric_name, value, type_tag, interval_lo/hi?,
   evidence_ref)`. Non-promotable, outside the complex, ∉ `MIRROR_READABLE`" + the two properties
   resumability/honest-comparison + "absorbed into the registry at build time"), **§2.3** (the
   `Inv` / `Rate(κ)` typing discipline the `type_tag` carries), **§2.5** (the metric registry's
   declared fields: name; type; source instrument; comparability rule; assertion shape; guardrail
   eligibility), **§2.10** (the eval-isolation + mirror-firewall constraints this store must honor).
2. `eval/metrics.py` — the module absorbed (read whole; 3 pure functions `recall_at_k`,
   `set_overlap`, `mean_cosine_distance` — the deterministic golden-set half). These become
   *registered metrics*, not deleted; the module stays importable.
3. `eval/drift.py` — the built drift gauge `D(t)` (the catalog row-2 instrument); its public
   reading is a registered metric (source instrument = catalog row 2). Read the public surface
   (the `D`/tolerance computation), not the internals.
4. `core/stores/telemetry.py` — the sibling DuckDB store, for the house pattern: `_connect`
   (`:70`), `CREATE TABLE IF NOT EXISTS` DDL blocks (`:25-63`), `TelemetryStore` /
   `open_store(config)` (`:156`, `:173`). The eval-results store mirrors this shape (DuckDB, a
   `writer()`/`reader()` split, `open_*` factory) — telemetry is the precedent, NOT a dependency.
5. `tests/quality/test_dreamer_quality.py` — **only** the `THRESH` dict (`:456`) and the composite
   assertions (`:497-515`): the F9 components (signal_recall, noise_max_conf, noise_max_mean) whose
   names are registered as the `f9_composite` family's members. Do not read the whole battery.
6. `docs/build-plans/bp-039/plan.md` — the house style for a new-store + registry plan (grounded,
   pinned, per-item acceptance + falsifier).

## 3. Investigation & grounding

`N/A — greenfield.` `eval/harness/` does not exist (verified 2026-07-15: `ls eval/harness/` → no
such directory). The store and registry are new files touching no existing read path. The **one**
existing module touched is `eval/metrics.py`, and it is *absorbed by re-export*, not rewritten — its
three functions keep their signatures and become registered metrics (§4). The registered metrics'
*source* instruments (`eval/golden.py`, `eval/drift.py`, telemetry, F9 `THRESH`) are read-only
references, not modified. Disk-status claims re-verified: `eval/metrics.py` present (1391 B),
`eval/drift.py` present, `core/stores/telemetry.py` present, `eval/harness/` absent — all as the
note asserts.

**Additional risks surfaced during reading:** (a) DuckDB append-only is a *discipline*, not an
engine constraint — the store must enforce "same key ⇒ skip, never overwrite" in code (Item 1's
falsifier), since DuckDB will happily insert a duplicate. (b) The `evidence_ref` column is a
free-form pointer (an attestation id / report path); the note does not fix its type — modelled as
`VARCHAR`, nullable, documented as opaque (parked, §11).

## 4. Reconciliation

- **`eval/metrics.py` — ABSORBED, announced as an extension (cross-reference-on-extension), NOT a
  correction.** The note (§2.2) says *"`eval/metrics.py` (existing metric helpers) is absorbed into
  the registry at build time."* Nothing in it is wrong. Proposed: keep the three pure functions
  verbatim; the registry *imports and registers* them as the golden-recall metric family; a
  one-line module-header cross-reference points at `eval/harness/registry.py` as the namespace that
  now owns their registration. **No function signature changes; no caller of `eval.metrics` breaks**
  (the bit-identical-import falsifier — every existing importer of `recall_at_k` etc. stays green).
- **`dn-evaluation-harness` frontmatter is `implementation: not-built` — becomes partially stale on
  build.** The ratified note is immutable (A8); this plan edits it nowhere. On completion the
  orchestrator batches the standing note-erratum ("`eval/harness/{store,registry}` now built") into
  `owner-questions.md` (the bp-039 pattern). No code corrected/replaced; every change is additive.

## 5. Write scope

- `eval/harness/__init__.py`, `eval/harness/store.py`, `eval/harness/registry.py` — **NEW**: the
  package, the DuckDB store (Items 1–2), the registry (Item 3).
- `eval/metrics.py` — Item 3 only: a header cross-reference comment + (if needed) an
  `__all__` — **no signature change** to the three functions.
- `tests/unit/test_eval_store.py`, `tests/unit/test_metric_registry.py` — **NEW**: round-trip,
  keying/resumability, registry-declaration tests.
- `tests/integrity/test_eval_isolation.py` — **NEW**: the non-skippable tooth proving the eval
  store has no path to ingest and is ∉ `MIRROR_READABLE`.

**Deliberately OUT of scope:** any sweep/optimizer (E3), any report renderer (E4), any instrument
wiring (E5), the run ledger (E2 — a *different* store, SQLite); `eval/golden/**`, `eval/golden.py`,
`baseline.json` (the sacred frozen anchors — the store measures against them, never near them; on
the foundation denylist); every design note (immutable, A8); `MIRROR_READABLE` / `core/mirror.py`
(the store is its own Σ, outside the mirror — proven by the integrity tooth, not edited).

## 6. Interfaces pinned inline

```python
# eval/harness/store.py — the eval-results store. DuckDB, append-only-by-key. Pure eval layer:
# imports nothing from core/ read paths; it is its own Σ, ∉ MIRROR_READABLE (§2.2, §2.10).

from dataclasses import dataclass

# --- The unified key (§2.1). Every reading is addressed by exactly this tuple. ---
@dataclass(frozen=True)
class EvalKey:
    spec_hash: str          # instrument id+version ‖ pipeline identity ‖ battery params
    corpus_ref: str         # "fixture:<hash>" (fixture-bound) | "<merkle-digest>" (mirror-bound)
    config_fingerprint: str # sha256 of the resolved tuning manifest
    seed: int

# --- One reading = one row (§2.2). type_tag carries the Inv/Rate(κ) discipline (§2.3). ---
@dataclass(frozen=True)
class Reading:
    key: EvalKey
    metric_name: str        # MUST be a registered registry key (registry.py) — no ad-hoc metrics
    value: float
    type_tag: str           # "Inv" | "Rate(<clock>)"  (a Rate carries its clock — Rule CLOCK)
    interval_lo: float | None = None   # EH-f: intervals at n≤13 owner scale; point value otherwise
    interval_hi: float | None = None
    evidence_ref: str | None = None    # opaque pointer (attestation id / report path); §3 risk (b)

class EvalResultsStore:
    """Append-only by key. put() is idempotent-by-key: a present (key, metric_name) cell is SKIPPED
    (resumability, §2.2), never overwritten (the whole-plan falsifier)."""
    def put(self, r: Reading) -> bool: ...          # True = inserted, False = skipped (already present)
    def has(self, key: EvalKey, metric_name: str) -> bool: ...   # the resume check
    def get(self, key: EvalKey, metric_name: str) -> Reading | None: ...
    def query(self, *, metric_name: str | None = None,
              corpus_ref: str | None = None) -> list[Reading]: ...  # group-by substrate for curves
    def close(self) -> None: ...

def open_eval_store(config=None) -> EvalResultsStore: ...   # factory; path under the derived-store parent
```

```python
# eval/harness/registry.py — the single metric namespace (§2.5). No sweep/battery/report may
# reference a metric name not registered here.

from dataclasses import dataclass
from typing import Callable, Literal

@dataclass(frozen=True)
class MetricSpec:
    name: str
    type_tag: str                                  # "Inv" | "Rate(<clock>)" (§2.3)
    source_instrument: str                         # a catalog row id, e.g. "row1-golden-recall"
    comparability: str                             # which corpus_refs/anchors it may compare across
    assertion_shape: Literal["regression", "absolute"]   # regression-first (§2.5); absolute only when stable
    guardrail_eligible: bool

REGISTRY: dict[str, MetricSpec] = {}               # populated at import with the built metrics
def register(spec: MetricSpec) -> None: ...        # rejects a duplicate name (single namespace)
def get(name: str) -> MetricSpec: ...              # KeyError on an unregistered name (fail-closed)

# The four BUILT metric families registered at import (§3 E1):
#   golden recall   -> eval.metrics.recall_at_k / set_overlap / mean_cosine_distance  (Inv, row1, guardrail)
#   drift D         -> eval.drift  (Inv, row2, guardrail)
#   f9_composite    -> tests.quality THRESH members: signal_recall / noise_max_conf / noise_max_mean (Inv, row5)
#   telemetry       -> core.stores.telemetry vitals + context_usage  (Rate(wall)/Inv, row4)
```

```python
# eval/metrics.py — ABSORBED (Item 3). Signatures UNCHANGED (§4). Verified current form:
def recall_at_k(expected: set[str], retrieved: Sequence[str], k: int) -> float: ...    # eval/metrics.py:15
def set_overlap(expected: set[str], retrieved: Sequence[str], k: int) -> float: ...    # eval/metrics.py:25
def mean_cosine_distance(distances: Sequence[float]) -> float: ...                     # eval/metrics.py:33
```

## 7. Items

### Item 1 — `eval/harness/store.py`: the DuckDB store + the `EvalKey`/`Reading` types + append-only-by-key
- **Objective:** the frozen `EvalKey` and `Reading` dataclasses (§6), a DuckDB-backed
  `EvalResultsStore` with the one keyed table, and the idempotent `put()` (present cell → skip),
  `has()`, `get()`, `query()`, plus `open_eval_store(config)` (path under the derived-store parent,
  the telemetry precedent).
- **Files:** `eval/harness/__init__.py`, `eval/harness/store.py`.
- **Acceptance test:** the package imports; `mypy core agents eval ops scheduler scripts` stays 0;
  a smoke round-trip (`put` then `get` returns an equal `Reading`); the table's primary discipline
  is `(spec_hash, corpus_ref, config_fingerprint, seed, metric_name)`.
- **Falsifier:** a second `put()` with the same key+metric_name and a **different** value either
  overwrites the first or inserts a duplicate row (both violate append-only-by-key) — `put()` must
  return `False` and leave the store unchanged.
- **Invariant(s) it must not violate:** the store is its own Σ — imports no `core/` read path, holds
  no model, performs no network; ∉ `MIRROR_READABLE`; sealed-core egress untouched.
- **Touches stored data?** Yes — it *is* a new store (a fresh DuckDB file). No existing store row is
  read or written; the acceptance test uses a `:memory:` / tmp path, never the live derived store.
  **Parallelizable?** No (Items 2–3 build on it).

### Item 2 — resumability + honest-comparison tests
- **Objective:** prove the two §2.2 properties: a present keyed cell is skipped on re-`put` (an
  interrupted sweep resumes for free), and readings differing only in one key component
  (`corpus_ref` vs `config_fingerprint` vs `seed`) are distinct rows (the three confounds stay
  separable — §2.1).
- **Files:** `tests/unit/test_eval_store.py`.
- **Acceptance test:** `pytest -q` passes; a test writes N cells, "interrupts", replays, and asserts
  the second pass inserts 0 new rows and issues 0 overwrites (`put` all `False`); a second test
  varies one key component at a time and asserts distinct rows / independent `query` group-bys.
- **Falsifier:** the resume test passes only because `put` overwrites (idempotent-looking but
  lossy); OR two cells that differ only by `seed` collapse to one row (a confound leaked).
- **Invariant(s):** append-only discipline (Item 1); no test writes to a live store.
- **Touches stored data?** No (tmp/`:memory:` only).  **Depends on:** Item 1.

### Item 3 — `eval/harness/registry.py`: the metric registry + absorb `eval/metrics.py`
- **Objective:** the `MetricSpec` dataclass + `register`/`get` (single namespace, fail-closed on an
  unregistered name, reject duplicate registration), the four built metric families registered at
  import (§6), and the `eval/metrics.py` absorption (header cross-reference; the three functions
  registered as the golden-recall family, signatures unchanged).
- **Files:** `eval/harness/registry.py`, `eval/metrics.py` (comment/`__all__` only),
  `tests/unit/test_metric_registry.py`.
- **Acceptance test:** the four families resolve via `registry.get(...)` with the correct
  `type_tag` (golden recall/drift/f9 = `Inv`; telemetry vitals = `Rate(wall)`), `source_instrument`
  (catalog rows 1/2/5/4), and `guardrail_eligible` (golden recall + drift True); `registry.get` on
  an unknown name raises; a duplicate `register` raises; **every existing importer of
  `eval.metrics.recall_at_k` etc. stays green unmodified** (the absorption is additive).
- **Falsifier:** a metric name usable by a sweep/report is NOT in the registry (the "single
  namespace, no ad-hoc metrics" rule is not enforced — `get` should be the only accessor); OR
  `eval/metrics.py`'s functions changed signature (the absorption rewrote instead of re-exporting).
- **Invariant(s):** the type_tag honors Rule CLOCK (a Rate carries its clock — §2.3); regression-
  first assertion shape is the default; the registry holds no model.
- **Touches stored data?** No.  **Depends on:** Item 1.

### Item 4 — the eval-isolation integrity tooth
- **Objective:** the non-skippable integrity test (per `test-organization` §5) proving the store
  honors the §2.10 constraints: no import path from `eval/harness/store.py` to any ingest entry
  point, and the store is ∉ `MIRROR_READABLE` (a `MirrorView` cannot project an eval-results row).
- **Files:** `tests/integrity/test_eval_isolation.py`.
- **Acceptance test:** the test asserts (statically / by construction) that `eval.harness.store`
  imports nothing from the ingest surface and that no `MIRROR_READABLE` membership includes the
  eval table; runs in the `integrity/` profile (non-skippable).
- **Falsifier:** the store can be reached from an ingest path, or a `MirrorView` projection surfaces
  an eval reading — either is a firewall breach and the tooth must fail red, not be relaxed.
- **Invariant(s):** eval isolation + mirror firewall (non-negotiables #2, #11; note §2.10).
- **Touches stored data?** No.  **Depends on:** Items 1, 3.

## 8. Math carried explicitly

`N/A — no new mathematical object.` The `Inv` / `Rate(κ)` result typing and Rule CLOCK the
`type_tag` carries are **already built** in `core/scope.py` (bp-039); this plan *stores the tag*, it
does not re-implement the algebra. The metrics themselves (`recall_at_k` etc.) are pre-existing pure
functions, unchanged.

## 9. Non-goals

- **No sweep, optimizer, or tuning manifest** (E3) — the store is *written through* by later plans;
  this plan provides only the surface.
- **No report renderer** (E4) — `query()` is the group-by substrate reports will consume; no
  rendering here.
- **No instrument wiring** (E5) — no new metric is *produced*; the four registered families already
  exist as instruments.
- **No run ledger** (E2) — a different store (SQLite/WAL), a different plan; the two never merge.
- **No interval-column lifecycle beyond nullable lo/hi** (EH-f) — the columns exist; the first
  battery that reports intervals exercises them (parked).
- **No absolute thresholds** — every registered metric is `regression`-shaped until its distribution
  stabilizes (§2.5); graduation to `absolute` is a later, per-metric act.

## 10. Stop-and-raise conditions

- `eval/harness/store.py` cannot be authored without importing a `core/` read path or the mirror →
  **STOP, file a `codebase` finding**: the store must be its own Σ; if the layering forces a mirror
  import, the isolation premise is wrong and needs re-graduation.
- Absorbing `eval/metrics.py` forces a signature change to keep an existing importer green → **STOP,
  file a `codebase` finding**: the absorption must be additive (re-export), not a rewrite.
- The plan does not fit one session → **file a `spec-defect` finding and PARK**; the orchestrator
  re-graduates — a builder never re-splits mid-session.
- Any blessing flip (`proposed→ready`, `draft→ratified`) → **must not**; the builder has no blessing
  capability.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| `evidence_ref` column type | opaque nullable `VARCHAR` (attestation id / report path) | a typed FK to the attestation store (rejected: couples the eval store to the attestation schema; premature) | a consumer needs to *join* readings to attestations by structured key |
| Interval columns (EH-f) | nullable `interval_lo`/`interval_hi`; point value otherwise | mandatory intervals (rejected: most readings are points at current scale) | the first battery reporting intervals (E8) |
| Store file location | under the derived-store parent (telemetry precedent) | a dedicated `data/eval/` root (deferred: no need until multi-store layout matters) | a second eval store or an ops decision to relocate |

## 12. Dependency & ordering summary

Blast-radius order: **Item 1** (new store module — lowest radius, touches no existing code) →
**Item 2** (tests over it) → **Item 3** (registry + the one additive touch to `eval/metrics.py`) →
**Item 4** (the integrity tooth). All within `eval/harness/` + `eval/metrics.py` (comment only) +
three new test files → **one session, not parallel.** `depends_on: []`. Model **opus**
(deterministic store + typed registry over a ratified design — no fable, no xhigh).

**Cross-plan:** this is the **keystone** — E2 (bp-043 run ledger) is a *sibling* store that does not
write here but shares the harness's keying philosophy; E3 (sweep engine) writes per-cell `Reading`s
through `put()` and resumes via `has()`; E4 (bp-044 report generator) consumes `query()` as its
group-by substrate; E5 (bp-045) instruments produce readings that land here. None of those may start
until this store's surface exists. `parallelizable_with: []` — E2/E4 read this plan's *design* to
pin their interfaces, but the store itself must be built first for anything to write through it.
