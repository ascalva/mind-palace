# Journal — bp-089 (S1′)

**Status:** proposed (supersedes bp-084 on `finding-0144`; awaiting owner `proposed → ready`).
**Design ref:** `docs/design-notes/inner-outer-core.md` §2.6b.

## Minted — 2026-07-21 (session-40), by the orchestrator

bp-084 (S1) was graduation-defective — its `write_scope` could not deliver the atomic +7. The
delegated builder ran the read-only DRY audit (Item 3), hit the wall, and STOPPED CLEAN (no code),
filing `finding-0144` (spec-fidelity → orchestrator). Per the graduate discipline (supersession,
not in-place editing), bp-089 is minted with the three corrections + the naming fix (see §0-bis):
`write_scope` += `core/temporal_view.py`, `core/temporal/__init__.py`, `core/stores/claim_ops.py`;
the +7 promotes `core.integrator_math` (new inner), not `core.integrator` (stays outer, keeps the
ledger). Item 3 is pre-completed (recorded in finding-0144) — the builder skips it.

Importer discovery redone repo-wide (the graduation defect was incomplete): the moved temporal
symbols are imported by `core/temporal_view.py` (`:56/:187/:340/:348`) + `core/temporal/__init__.py`
(`:18,22,50,69`) + the six temporal test files (already in scope). `IntegrationReport`/`CoverageGauge`
have NO external importer — that split needs no extra repoint. Final `|INNER| = 37`.

Next: owner blesses `proposed → ready`, then `/build bp-089` (run against post-M0 main; `git merge
main` first if the worktree is stale). bp-084 stays inspectable, superseded.

## Session-41 (2026-07-21, delegated builder, opus) — execution

Merged main (`d635dc6`); `core/rings.py` (30 incl. core.rings) + `core/scope.py` present. Flipped
`ready → in-progress`. Item 3 pre-done (finding-0144) — started at Item 4.

**Importer discovery (repo-wide grep, confirmed ALL in write_scope — no new graduation defect):**
- `build_citation_complex`: `core/temporal_view.py:56` (top-level), `core/temporal/__init__.py:22/50`,
  + tests test_temporal_complex/operators/view/view_live/isolation. All in scope.
- `supersession_poset`: `core/temporal_view.py:340` (lazy), `core/temporal/__init__.py:18/69`. No test
  imports it directly. All in scope.
- `IntegrationReport`/`CoverageGauge`: NO external importer (integrator.py re-imports for own use).
- `ClaimOpStore`/`apply_operations`/`stale_closure`: tests test_dialogue_ops + test_edge_partition
  only (the rest are comments/string-literals — build.py:150, derived.py:226, authored_supersession).
  All in scope.

### Item 4 — temporal seams relocated — DONE, GREEN

Created `core/temporal/acquire.py` (NEW, outer): holds `supersession_poset` + `build_citation_complex`
verbatim (byte-identical bodies), imports `VersionStore`/`ReferenceEdgeStore` + the inner pure
`poset_from_chains`/`SupersessionPoset`/`CitationComplex`. `boundary.py` + `complex.py` shed their
store imports (`grep core.stores` → NONE) + banner-on-correction docstrings; they now COMPUTE, not
acquire. `core/temporal/__init__.py` DROPS both moved symbols from imports AND `__all__` (re-adding
from acquire would repull store types into the package `__init__` → keep `core.temporal` OUTER — the
finding-0144 trap; left a comment). Repointed `temporal_view.py` (top-level→acquire for
build_citation_complex; lazy split for supersession_poset) + the 5 temporal test files (clean-break,
no alias shim). **Acceptance:** `test_temporal_complex/operators/view + test_temporal_isolation +
test_temporal_view_live` → 34 passed, 2 skipped. Zero behavior change (same fixtures, same assertions,
identical output — the seam bodies are verbatim). Purity: boundary/complex import 0 stores.
Next: Item 5 (integrator_math + claim_ops split).

### Item 5 — integrator + recursion_ops persistence split — DONE, GREEN

`core/integrator_math.py` (NEW, inner, pure — dataclasses only): `IntegrationReport` + `CoverageGauge`
relocated verbatim. `integrator.py` re-imports them (a genuine use, no external importer), keeps the
`ledger: sqlite3.Connection` + `Integrator`/`build_integrator`/`coverage_gauge` — STAYS OUTER (sqlite3
+ out-of-scope importers scheduler/cron.py:39, ops/lifecycle/launcher.py:238 untouched). Dropped the
now-unused `field` import.

`core/stores/claim_ops.py` (NEW, outer): the sqlite-backed `ClaimOpStore` (idempotent CREATE TABLE IF
NOT EXISTS + index, INSERT OR REPLACE) + `open_claim_op_store` + the `DerivedStore`-consuming
`apply_operations`/`stale_closure` — all relocated verbatim. Imports the pure vocabulary
(`OpKind`/`ClaimOp`/`Supersede`/…/`_op_id`/`_utcnow`) from its inner home. This is finding-0144's
option (a) in-scope home; recursion_ops keeps the pure vocabulary + id scheme and SHEDS `sqlite3`,
`core.stores.derived`, `pathlib.Path`, `core.config`, `collections.abc.Iterable`. Repointed the two
importers test_dialogue_ops + test_edge_partition (split imports, clean break). Purity confirmed:
`grep sqlite|core.stores|DerivedStore` in integrator_math/recursion_ops → prose-only, 0 imports.
**Acceptance:** test_integrator + test_rotation_report + test_integrator_wiring + test_dialogue_ops +
test_edge_partition → 40 passed. Zero behavior change (verbatim bodies, identical assertions).

### Item 6 — the +7 map diff — DONE, GREEN

Ran the inner-ring fixed point BEFORE editing INNER: computed − declared = exactly
`{core.integrator_math, core.recursion_ops, core.temporal, core.temporal.boundary,
core.temporal.complex, core.temporal.operators, core.temporal.superconnection}` — the +7, no eighth,
none missing, `core.integrator` correctly NOT among them. **F10 did NOT fire for any module.** Updated
`core/rings.py` INNER (30→37) with the 7, annotated + count comment. `test_inner_ring.py` → 4 passed;
`|INNER| == 37`; `core.integrator in INNER == False`.

### Full attestable-green gate (each leg separately)
- `ruff check .` → All checks passed
- `check_imports.py` → OK (core imports no zone/network)
- `mypy core agents eval ops scheduler scripts` → Success, 243 files
- argless `mypy` → **Found 69 errors** (baseline held, unchanged)
- `python -m ops.type_gate` → OK (tier-2 membership + bare-ignore scan)
- `pytest -q` → **1842 passed, 15 skipped, 1 failed** — the ONLY failure is
  `test_core_imports_nothing_outside_core` (the finding-0103 OUTER ratchet, red-by-design at **19**,
  NOT this plan's; confirmed the 19 are all pre-existing modules — shadow/effect_proposal/factory/
  interface/ops_view/reference_view/sensing/temporal.spine — and NONE of my new files appear). Every
  moved import is core-internal, so the outer ratchet is untouched.

**S1′ COMPLETE.** Committed on the worktree branch. Left `status: in-progress` (orchestrator flips
`complete` on merge). No new graduation defect surfaced (all importers were in write_scope).
