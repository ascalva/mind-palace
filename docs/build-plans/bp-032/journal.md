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
