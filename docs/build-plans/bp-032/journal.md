# bp-032 journal

## 2026-07-14 — authored `proposed` (orchestrator, opus/xhigh graduation)

Graduated from `dn-temporal-retrieval-algebra` §3 Consequence 1 (the `core/temporal/` module) — the
**topological half**: `X_cite` assembly, `∂`/`δ_D`, the `dim ker L₁ == β₁` falsifier, and the isolation
twin. The **temporal-transport half** (σ_\*/σ^\*/π_active, `‖[d,τ]‖`) split off as **bp-033**
(`depends_on: bp-032`) — the objective carried an "and" and each half has an independent runnable
falsifier (graduate sizing heuristic).

**Grounded pass (citations in §3):**
- 1-cells come straight from `ReferenceEdgeStore.all(direction="corpus_to_corpus")` (bp-026 v2,
  `reference_edges.py:107,282`); D-arrows from `VersionStore.supersessions(doc_id)` (`versions.py:101`).
- **`depends_on: bp-031`** is a hard edge: `δ_D²=0` (Result-1 H0/H1) needs rename-stable `doc_id` for the
  version chains — a rename fork breaks the poset hypothesis.
- The isolation invariant is **not** weakened: the forbidden direction is `reference_edges →
  core/complex` (`test_reference_edge_isolation.py:126-132`); `core/temporal → core/complex/hodge` is the
  safe direction → `hodge.hodge_laplacian_1`/`harmonic_basis` reused as-is on the symmetrized backbone.
- Falsifier oracle: `dim ker L₁` (`hodge.py:136`) vs an **independent** ripser β₁
  (`topology.persistence`, `topology.py:61`) — the `edge-dynamics §2.2` falsifier lifted to citations.

**Design decisions PINNED here:** TA-d resolved → module home = **`core/temporal/`** (not `core/query/`,
which conflates with the retrieval protocol). Combinatorial v1 (unweighted `A_cite`); the flag complex
(matches `hodge`/Rips so the falsifier holds); D-arrows kept **directed**, never symmetrized into
`A_cite` (A5 — a mixed `L₁` is a type error).

**write_scope** = `core/temporal/**` + two NEW test paths (`test_temporal_complex.py`,
`test_temporal_isolation.py`) — clean, no inline comments (finding-0075). `core/complex/**` and both
stores are read-only, explicitly out of scope.

Estimate opus/400k (a new deterministic math module; `δ_D²=0` + `dim ker L₁==β₁` falsifiers need
judgment). Item numbering continues the family (5–8). Awaiting the owner-only `proposed → ready` blessing;
**do not build before bp-031 lands.** No code written.

## 2026-07-14 — blessed `proposed → ready` (owner, by hand); orchestrator commits the flip

Owner hand-blessed bp-032 (with bp-031/033) `proposed → ready`. Orchestrator commits the flip (rule 0060).
**`depends_on: bp-031` binds — DO NOT `/build` bp-032 before bp-031 lands** (the D-arrows need rename-stable
`doc_id`). No code written yet.

## 2026-07-14 — `/build` START + Items 5–8 COMPLETE (bp-031 landed; opus/high, orchestrator-driven)

bp-031 sealed (`f002985`) → dependency satisfied. `/build bp-032` set active-plan + flipped `ready →
in-progress`. Context manifest read in full: `hodge.py` (boundary_1/2, hodge_laplacian_1, harmonic_basis,
edge_index, `_MAX_DENSE_EDGES`), `reference_edges.py` (`all(direction="corpus_to_corpus")`, symmetric v2
endpoints), `topology.py` (`persistence` = the ripser oracle), `test_reference_edge_isolation.py` (the B-c
twin pattern), `versions.py` (`history`/`supersessions`), and the note §2.3/§2.4 (Result 1 H0, A5).

**Confirmed greenfield:** `core/temporal/` did NOT exist; `core/complex/temporal.py` (H9 snapshots) +
`tests/unit/test_temporal.py` are an UNRELATED module — no collision with `core/temporal/**` +
`test_temporal_complex.py`.

**Item 5 — assembly** (`core/temporal/__init__.py`, `core/temporal/complex.py`): `build_citation_complex(
ref_store) -> CitationComplex` reads `corpus_to_corpus` edges → sorted 0-cells, undirected deduped 1-cells,
binary symmetric `A_cite` (csr). Deterministic (sorted throughout, self-citations dropped). `dim_ker_L1`
via `hodge.harmonic_basis(A_cite).shape[1]`; `citation_distance_matrix` (edge→0, non-edge→1) is the ripser
input; `flag_boundary_composition_is_zero` confirms `∂₁∂₂=0` reusing hodge.

**Item 6 — δ_D + δ_D²=0** (`core/temporal/boundary.py`): the supersession poset over `(doc_id, seq)`
elements. `poset_from_chains` (pure) / `supersession_poset(version_store, doc_ids)` (store) → transitive
closure → order-complex simplices (pairs, triples). `coboundary_0`/`coboundary_1` are the signed simplicial
δ; `delta_D_squared_is_zero` asserts `δ¹δ⁰=0`. **A cycle → `SupersessionCycleError` (stop-and-raise §10)** —
the closure detects any `a<a`. D-arrows (E_disp, directed/acyclic) NEVER symmetrized into `A_cite` (A5).

**Item 7 — the falsifier**: `dim ker L₁ == ripser β₁` cross-checked on KNOWN fixtures — path/tree → 0,
chordless 4-cycle → 1, filled triangle → 0 — each asserting the incidence-algebra β₁ equals an INDEPENDENT
ripser H₁ alive at `t=0`.

**Item 8 — the isolation twin** (`tests/integration/test_temporal_isolation.py`): (behavioral) populating
`X_cite` + reading `dim_ker_L1` over the same authored nodes leaves frustration/forman/clustering
bit-identical; (structural) `build_complex` signature unchanged `{view,edges,derived,sim_floor}`; (grep-grade
via AST) no `core/complex/**` module imports `core.temporal`.

**Gate (5 legs, separate):** ruff ✓; mypy strict floor **0** (180 files — includes core/temporal); argless
mypy **69** (fixed a sparse `!=`.nnz → dense `.tolist()` compare, and a `no-any-return` via a typed local,
mirroring hodge); type_gate ✓; the 13 new tests green. **Full `pytest -q` running** (leg 5). Next: seal on
green + review diff vs write_scope + flip complete.

## 2026-07-14 — SEAL: bp-032 COMPLETE (in-progress → complete)

**All 4 items landed; the topological half of the temporal algebra is built.** `X_cite` assembly +
`δ_D²=0` + `dim ker L₁ == β₁` + the isolation twin — a new deterministic, embedder-independent math
module in `core/temporal/`, structurally isolated from the balance math. Unblocks **bp-033** (the σ/π
transport operators + `‖[d,τ]‖`, which consume this module's API).

**Diff vs write_scope — CLEAN.** Added exactly `core/temporal/` (`__init__.py`, `complex.py`,
`boundary.py`) + `tests/unit/test_temporal_complex.py` + `tests/integration/test_temporal_isolation.py`
— all in `write_scope` — plus this journal and the plan's own status/cost. `core/complex/**` and both
stores were read-only (imported, never modified). No out-of-scope write.

**5-leg gate:** ruff ✓ · mypy strict floor **0** (180 files) · argless mypy **69** · type_gate ✓ ·
`pytest -q` = **1045 passed, 8 skipped, 1 failed**. The one failure —
`tests/e2e/test_scheduler_live.py::test_supervisor_dispatches_a_real_job` — is a **pre-existing timing
flake in a LIVE-scheduler e2e**, categorically unrelated to a read-only math module: **re-ran in
isolation → PASSED (126s)**. Not a regression; bp-032 touches nothing the scheduler reaches.

**Verification (the /verify obligation):** the falsifiers ARE the end-to-end drive — `dim ker L₁`
(incidence algebra) cross-checked against an INDEPENDENT ripser β₁ on hand-verified fixtures (tree→0,
4-cycle→1, filled-triangle→0), `δ_D²=0` on a real multi-step chain, the cycle stop-and-raise, and the
isolation twin proving frustration/forman/clustering stay bit-identical when `X_cite` is populated.

**Cost (owner /usage relayed at seal):** est opus/400k; actual **67k non-cache** (11.4k in + 55.2k out,
delta over bp-031's seal), **$9.83** ($19.02 session-total − $9.19), ratio **0.17** — WELL under
(read-only greenfield math). session +4pp (35→39%), week +0pp (80%, cache-dominated). Single-lane, 0 subagents.

**⚠ FLAKE TO SURFACE (not a new finding yet):** `test_scheduler_live::test_supervisor_dispatches_a_real_job`
flaked under full-suite load (passed solo). Worth a `codebase` finding if it recurs — flagged to owner.

**Next: bp-033** (strict dependency order; consumes `core/temporal/` API). opus/high.
