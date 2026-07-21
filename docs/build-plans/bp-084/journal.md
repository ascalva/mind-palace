# Journal — bp-084 (S1)

**Status:** proposed (awaiting owner `proposed → ready` blessing, by hand).
**Design ref:** `docs/design-notes/inner-outer-core.md`.

## Graduation — 2026-07-21 (session-40)

Minted `proposed` by `/graduate` over the three ratified notes (`fbea48d`). Decomposition and
grounding done in a single orchestrator context (subagent-assisted decomposition parked, §14);
seams/instruments re-verified on disk at HEAD `d08da37`. No implementation performed —
graduation implements nothing (A4). The plan's §3 carries the grounding citations; §6 pins the
interfaces verbatim so a fresh builder infers no design.

Next: owner blesses `proposed → ready` by hand, then `/build bp-084` in a fresh (delegated)
session.

## Build attempt — 2026-07-21 (session-41, delegated builder) — STOP-AND-RAISE (finding-0144)

Synced worktree to `main` (ff `d08da37..bf16865`); `core/rings.py` present (M0/bp-083 landed).
Set active-plan pointer; flipped `ready → in-progress`. Read the four seam files whole + `rings.py`
+ `test_inner_ring.py` + the temporal package (`__init__`, `operators`, `superconnection`, `atlas`)
+ `temporal_view.py` + `authored_supersession.py`. Grounded every importer of the moving symbols.

**Item 3 (DRY audit) — DONE, read-only.** Per seam:
- `boundary.py:114 supersession_poset` → home `core/temporal/acquire.py` (new, outer). No store
  reuse question (it wraps `VersionStore`, already an existing store).
- `complex.py:59 build_citation_complex` → home `core/temporal/acquire.py`. Reuses existing
  `ReferenceEdgeStore`; no new store.
- `integrator.py` ledger → **stays** in `integrator.py` (outer); pure gauges `IntegrationReport`/
  `CoverageGauge` → `core/integrator_math.py` (new, inner). No new store (ledger = existing
  `code_snapshots.sqlite`, read-only, owned by `ops.code_snapshot`).
- `recursion_ops.py:53,62` `ClaimOpStore` → **NO existing `core/stores/*` covers `claim_ops`**
  (checked: `authored_supersession.py` is a distinct owner-declared edge type — §4A C3; `versions.py`
  is note-version supersedes; no `claim_ops` table anywhere). A NEW store is genuinely needed —
  reuse rule NOT breached, so §10's "a store already covers it" stop does not fire. Correct home:
  new `core/stores/claim_ops.py`.

**Three blockers found before writing any code (tree pristine) — full detail in finding-0144:**
1. **Temporal cluster (5 of 7) hard-blocked:** `core/temporal_view.py` imports BOTH moved symbols
   (`build_citation_complex` top-level `:56`/`:187`; `supersession_poset` lazy `:340`) and is NOT
   in `write_scope`; scope-guard denies the edit and clean-break forbids a shim. Plan §4 mis-names
   the importers (`atlas.py`/`eval/harness` — neither imports them; `temporal_view.py` omitted).
2. **`recursion_ops` blocked:** its `claim_ops` persistence needs a NEW `core/stores/claim_ops.py`,
   but `core/stores/**` is out of `write_scope`; the plan's contemplated homes (`acquire.py`
   temporal / `integrator_math.py` inner) are both wrong.
3. **Integrator naming:** the achievable in-scope promotion is `core.integrator_math`, not
   `core.integrator` (making `core.integrator` itself inner would break out-of-scope
   `scheduler/cron.py` + `ops/lifecycle/launcher.py`). Documentation slip, builder-annotatable.

Decision: STOP-AND-RAISE (§10; honesty mandate) rather than force a red `INNER` or route around
scope-guard. **No code written.** Committed: journal + finding-0144 + status/re_entry only. The
fixed-point *computation* is sound; the plan needs a 3-edit amendment (add `temporal_view.py` +
`core/stores/claim_ops.py` to `write_scope`; rename the integrator member). Item 3 need not repeat.

Re-entry: see `re_entry` front-matter + finding-0144 §Re-entry.
