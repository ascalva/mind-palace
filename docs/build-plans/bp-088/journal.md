# Journal — bp-088 (AL-3)

**Status:** proposed (awaiting owner `proposed → ready` blessing, by hand).
**Design ref:** `docs/design-notes/agentic-loop.md`.

## Graduation — 2026-07-21 (session-40)

Minted `proposed` by `/graduate` over the three ratified notes (`fbea48d`). Decomposition and
grounding done in a single orchestrator context (subagent-assisted decomposition parked, §14);
seams/instruments re-verified on disk at HEAD `d08da37`. No implementation performed —
graduation implements nothing (A4). The plan's §3 carries the grounding citations; §6 pins the
interfaces verbatim so a fresh builder infers no design.

Next: owner blesses `proposed → ready` by hand, then `/build bp-088` in a fresh (delegated)
session.

## Build — 2026-07-21 (session-41, delegated builder, opus[1m])

Worktree merged to current main (`cea89b7`, fast-forward) — confirmed AL-1's `PRIVATE_STRATA` +
`zone_admissible` present in `core/scope.py` before extending. Both items landed in one build.

### Item 16 — `exhaust ⊂ dialogue` refinement with default-grant exclusion [DONE]

`core/scope.py`:
- Added `Stratum.EXHAUST = "exhaust"` and `_REFINES[EXHAUST] = DIALOGUE` — so exhaust is a genuine
  refinement below dialogue in R (and excluded from `_BASE_STRATA` automatically, since it is in
  `_REFINES`, like every refinement).
- Added `_EXCLUDED_REFINEMENTS: frozenset = {EXHAUST}` and changed `_downward_close`: a directly
  named stratum is always kept (`out = set(strata)`), but a parent's closure adds
  `_refinements_below(s) - _EXCLUDED_REFINEMENTS` — so a `dialogue`/`top()` grant never auto-adds
  EXHAUST; it enters a downset ONLY when named directly. This keeps `⊤_Σ` byte-identical (the
  additive property HYPOTHETICAL already has).

**Spec-fidelity note (recorded, not a stop).** Plan §7 Item 16 acceptance (iv) reads
"`of(EXHAUST) ⊑ of(DIALOGUE)` (the refinement ⊑)". Under the lattice's `⊑ = ⊆` on downward-closed
sets, that is INCOMPATIBLE with F-AL6 (the crux + stop condition): default-grant exclusion means
`of(DIALOGUE)` does NOT contain EXHAUST, so `{EXHAUST} ⊄ of(DIALOGUE)` and `of(EXHAUST) ⋢
of(DIALOGUE)`. The ratified design note (§2.4b EX-1(ii)) is unambiguous — the exclusion is the
safety property (F-AL6) — so I implemented exclusion and pinned the GENUINE refinement order the
predicate earns instead: `of(EXHAUST) ⊑ of(DIALOGUE, EXHAUST)` and `of(DIALOGUE) ⊑ of(DIALOGUE,
EXHAUST)` (naming exhaust widens), plus the load-bearing NON-order `of(EXHAUST) ⋢ of(DIALOGUE)`
and the structural `_REFINES[EXHAUST] is DIALOGUE`. (iv) as literally written is a plan-author
gloss inconsistent with its own F-AL6; the design note wins.

Tests (`tests/unit/test_scope.py`, new AL-3 section + `test_scope_laws.py` pins extended):
- `test_scope_laws.py`: `_EXPECTED_MEMBERS` += `"exhaust"`; `_EXPECTED_PRIVATE` -= `"exhaust"`
  (PRIVATE_STRATA derives from ⊤_Σ, which excludes the excluded refinement — byte-identical).
- New: `test_exhaust_is_a_genuine_but_excluded_refinement_of_dialogue`,
  `test_default_grants_exclude_exhaust`, `test_top_sigma_is_byte_identical_across_the_exhaust_addition`,
  `test_exhaust_refinement_order_holds_only_when_named`,
  `test_req_admissible_refuses_an_exhaust_read_under_a_grant_that_omits_it` (F-AL6 capability half),
  `test_lattice_laws_hold_over_exhaust`.

**F-AL6 HOLDS:** `top()` and `of(DIALOGUE)` structurally exclude EXHAUST; only `of(…, EXHAUST)`
admits an exhaust read (`req_admissible` refuses it under ⊤_Σ and under `of(DIALOGUE)`). ⊤_Σ
byte-identical — all existing `top()`/law/zone tests stay green.

### Item 17 — `origin(e)` derived view [DONE]

`core/origin_view.py` (NEW): `origin(edge_id, *, causal_edges, reference_edges) -> CausalEdge |
None`. Two-hop join `C ∘ commit-keying`: hop 1 resolves `edge_id` in `reference_edges` → its
`commit_sha` (the minting-commit key an X_cite row carries); hop 2 returns the `causal_edges` row
whose `pair_cut_sha == commit_sha` (deterministic min on `(event_order, edge_id)`). No store, no
minted rows; reads only the stores' readers (`.all()`, `.all_edges()`); returns a value, no
`A_geom` assembly (E_disp).

**Target-kind boundary (F-AL7 / §3 Q3), recorded:** `origin` is scoped to reference-edge (X_cite)
ids — the durable kind carrying a resolvable `commit_sha`. A causal edge's own file/doc endpoint
carries `pair_cut_sha=''` (working-tree write, no commit anchor, finding-0111), so it has no commit
key to join on and is OUT of `origin`'s domain (documented in the module + test, PD-8 parks
row-grain). `reference_edges` has no by-id reader and `core/stores/**` is out of write scope, so hop
1 filters `.all()` — read-only, regenerable.

**F-AL7 HOLDS:** `test_F_AL7_result_is_regenerable_from_witnesses_and_commit_keys_alone` reproduces
`origin`'s result by hand from ONLY the raw rows' commit key (F-side) + witnessed commit/witness
(C-side) — byte-identical, so no fact the rows don't carry is needed; the view needs no store.
Empty answers (`None`) for unknown id / unwitnessed commit / working-tree edge are honest, not
falsifiers. `test_origin_mints_nothing` pins store counts unchanged.

### Gate (each leg separately)
- `ruff check .` — All checks passed.
- `scripts/check_imports.py` — OK (core imports no zone/networking; origin_view is pure-core:
  only `core.stores.*` + stdlib).
- `mypy core agents eval ops scheduler scripts` — Success, 240 files.
- argless `mypy` — 69 errors (tests baseline, unchanged).
- `python -m ops.type_gate` — OK.
- `pytest -q` — **1 failed, 1842 passed, 15 skipped** (612s). The single failure is
  `test_core_imports_nothing_outside_core` — the finding-0103/0105 ratchet, RED-BY-DESIGN (CI
  deselects it), listing pre-existing core→outside imports (shadow.py, factory.py, ops_view.py,
  reference_view.py, …). `core/origin_view.py` and `core/scope.py` do NOT appear in it (grep-clean)
  — origin_view imports only `core.stores.*` + stdlib. No NEW reds; every new exhaust/origin test
  green; all existing scope-law/`top()`/zone tests green.

No findings filed (both falsifiers hold; the exclusion is structural). No trust weight `w(a_self)`,
no provenance-enum change, no φ_exhaust, no PD-7 return edges (non-goals respected).
