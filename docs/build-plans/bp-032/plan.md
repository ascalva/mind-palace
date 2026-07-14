---
type: build-plan
id: bp-032
status: complete
design_ref:
  - docs/design-notes/temporal-retrieval-algebra.md
contract: builder
write_scope:
  - core/temporal/**
  - tests/unit/test_temporal_complex.py
  - tests/integration/test_temporal_isolation.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 400k
  actual:
    model: opus            # orchestrator-driven, high effort, single-lane (0 subagents)
    tokens: 67k            # non-cache: 11.4k in + 55.2k out (delta over bp-031's seal; owner /usage)
    dollars: 9.83          # $19.02 session-total − $9.19 at bp-031's seal
    ratio: 0.17            # 67k / 400k — WELL under (read-only greenfield math, interfaces pinned)
    session_delta: "+4pp (35%->39%)"
    week_delta: "+0pp (80%, cache-dominated — near-free on the weekly quota)"
depends_on:
  - bp-031
parallelizable_with: []
created: 2026-07-14
updated: 2026-07-14  # in-progress → complete (Items 5–8; 5-leg gate green; e2e flake unrelated)
links:
  - docs/design-notes/temporal-retrieval-algebra.md
  - docs/design-notes/edge-dynamics.md
  - core/stores/reference_edges.py
  - core/complex/hodge.py
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — `core/temporal/`: the X_cite citation complex + the topological falsifier

> **Every section below is required.** Inapplicable sections are marked `N/A — <reason>`.

## 0. Mode & provenance

Investigation and planning produced this plan (grounded pass, §3 citations inline); implementation
proceeds **item-by-item on owner approval**. It graduates `dn-temporal-retrieval-algebra` §3 Consequence
1 (the module) — **the topological half**: `X_cite` assembly, the boundary maps `∂`/`δ_D`, and the
`dim ker L₁ == β₁` falsifier. **The temporal-transport half** (σ_\*/σ^\*/π_active, `‖[d,τ]‖`) is the
companion **bp-033** (`depends_on: bp-032`) — split because the objective carries an "and" and each half
has an independent runnable falsifier (graduate sizing heuristic). Authority-to-act is separate from the
`proposed → ready` blessing (owner-only, by hand).

**This plan RESOLVES parked decision TA-d:** the module home is pinned to **`core/temporal/`** (the note
§2.4 / §3 leaned here; the graduating plan pins the name). It is **greenfield** for the math but reads
two existing stores and reuses `core/complex/hodge` — so §3/§4 are NOT N/A.

**Read-only sensing, no store mutation (opus, deterministic).** Every object here is a pure, sparse,
deterministic computation over content-addressed inputs; the module holds no write handle to any store,
no model, no network — and, load-bearing, **never routes citation edges into the balance math** (the
isolation invariant, §6 / Item 4).

## 1. Objective

Assemble the deterministic citation complex `X_cite` from `ReferenceEdgeStore` in a new `core/temporal/`
package — with its boundary maps and a `dim ker L₁ == β₁` topological falsifier — structurally isolated
from `core/complex/`'s balance math.

## 2. Context manifest

Read whole, in order:

1. `docs/design-notes/temporal-retrieval-algebra.md` — §2.3 (Results 1–2: the bicomplex, `[d,τ]`), §2.4
   (A4: the separate `X_cite` complex + its home-outside-`core/complex/` constraint; A5: Hodge on
   `E_geom ⊔ E_disp`, do-not-mix), §2.7 (the inversion binds every result), §3 (Consequence 1 + its
   falsifier verbatim).
2. `core/stores/reference_edges.py` — `ReferenceEdgeStore.all(direction=…, source_ref=…, target_ref=…)`,
   `ReferenceEdge` fields, `KINDS`/`DIRECTIONS` (`corpus_to_corpus` is the doc→doc 1-cell source).
3. `tests/integration/test_reference_edge_isolation.py` — the B-c falsifier: `build_complex`'s signature
   is exactly `{view, edges, derived, sim_floor}` and `core/complex/**` never imports `reference_edges`.
   The NEW module must not weaken this — and gets its own twin (Item 4).
4. `core/complex/hodge.py` — `boundary_1`/`boundary_2`, `hodge_laplacian_1(A) -> csr` (`dim ker L₁ = β₁`),
   `harmonic_basis`, `edge_index` — the degree-1 machinery, **reused on the symmetrized citation
   backbone** (importing `core/complex/hodge` FROM `core/temporal/` is the safe direction).
5. `core/complex/topology.py` — `persistence(D, maxdim=1)` (lazy `ripser`): the **independent β₁ oracle**
   for the falsifier.
6. `core/stores/versions.py` — `VersionStore.supersessions(doc_id)` / `history(doc_id)`: the D-arrow
   (supersession/version-chain) source. Rename-stable `doc_id` is why **bp-031 is a prerequisite**.
7. `docs/design-notes/edge-dynamics.md` — §2.2 (the Hodge object, the `dim ker L₁ == ripser β₁` built
   falsifier this generalizes), §2.5 (the inversion / INTERPRETED-class discipline).

## 3. Investigation & grounding

- **Q1 — What are `X_cite`'s cells, and where do they come from?** 0-cells = notes; 1-cells = `doc→doc`
  citation edges = `ReferenceEdgeStore.all(direction="corpus_to_corpus")` (`reference_edges.py:107,282`);
  D-arrows = supersession/version chains. **The store supplies the 1-cells directly** (bp-026 landed
  `corpus_to_corpus`; the note §2.4 states `X_cite` is "built from `reference_edges.sqlite`"). **The code
  settles the 1-cell source.**
- **Q2 — Where do the D-arrows come from, and why is bp-031 a prerequisite?** From the version chains:
  `VersionStore.supersessions(doc_id)` (`versions.py:101`). For `δ_D² = 0` (Result 1 H0, a strict
  partial order) the identity carrying those chains must be **rename-stable** — else a rename forks a
  chain and the poset/acyclicity hypothesis (H1) breaks (`sync.py`, closed by **bp-031**). **The code +
  the note settle this → `depends_on: bp-031`.**
- **Q3 — Can `core/temporal/` exist without weakening the isolation invariant?** Yes. The invariant is
  precisely: `build_complex`'s signature is `{view, edges, derived, sim_floor}` and `core/complex/**`
  never imports `reference_edges` (`test_reference_edge_isolation.py:126-132`). A new `core/temporal/`
  package that *reads* `reference_edges` and *imports* `core/complex/hodge` does not touch either fact —
  the forbidden direction is `reference_edges → core/complex`, not `core/temporal → core/complex/hodge`.
  **The code settles this**; Item 4 pins a twin test so it stays true.
- **Q4 — What is the falsifier oracle for `dim ker L₁ == β₁`?** `hodge.hodge_laplacian_1(A)` gives
  `dim ker L₁` (`hodge.py:136-144`, `= β₁` of the flag complex); `topology.persistence(D, maxdim=1)`
  gives ripser's H₁ (`topology.py:61-66`) — an **independent** computation. On the symmetrized citation
  backbone `A_cite` with `distance = 1 − w` they must agree (the note §2.4/§2.7 Rule 2). **The code
  settles the oracle.**
- **Q5 — Does the dense-path size guard apply?** `hodge` raises above `_MAX_DENSE_EDGES = 20_000`
  (`hodge.py:41,126-133`). The authored-note citation graph is far below this (order 10²–10³ edges), so
  the deterministic dense path holds; the module inherits the same guard, never a silent sparse fallback.
  **The code settles this** at today's corpus scale.

**Additional risks or questions surfaced during reading:** (a) **Weight normalization** — the note
§2.1(i) sub-ruling: citation weights normalize to `(0,1]` before any `−log`, and on the *binary*
citation graph the β-deformation is degenerate (1a≡1b). This plan builds the **combinatorial v1**
(unweighted) complex — the `(β,z)` curve is bp-034+/TA-b, out of scope here. (b) `hodge`'s orientation
(`edge_index`: `i<j` ascending, `hodge.py:48-56`) is symmetric-backbone; the **directed** D-arrows carry
their orientation separately (they are `δ_D`, not `∂₁`) — do NOT symmetrize the D-arrows into `A_cite`
(A5: `E_disp` is acyclic/directed, `E_geom` undirected — a mixed `L₁` is a type error).

## 4. Reconciliation

- `dn-temporal-retrieval-algebra §2.4` (A4) — *"the `X_cite`/temporal module MUST live OUTSIDE
  `core/complex/` — proposed `core/temporal/`."* → **[cross-ref: extension]** this plan pins the home to
  `core/temporal/` (resolves TA-d). No note is edited (ratified/immutable).
- `dn-edge-dynamics §2.2` — the built `dim ker L₁ == ripser β₁` falsifier on the **similarity** backbone.
  → **[cross-ref: extension]** this plan lifts the *same* falsifier onto the **citation** backbone (a new
  customer of the same methodology, "shared mathematics, never shared state", note §2.4). No edit to the
  ratified `edge-dynamics` note.
- No committed code is corrected — the module is additive and *reuses* `core/complex/hodge` unchanged.

## 5. Write scope

Front-matter: `core/temporal/**` (the new package — assembly, boundary maps, the falsifier compute),
`tests/unit/test_temporal_complex.py` (the assembly + `δ_D²=0` + boundary unit tests),
`tests/integration/test_temporal_isolation.py` (the NEW isolation twin). **Deliberately OUT of scope:**
`core/complex/**` (imported/read only — **never modified**; `hodge`/`topology` are reused as-is),
`core/stores/reference_edges.py` + `core/stores/versions.py` (read only), every store's schema, the
existing `test_reference_edge_isolation.py` (untouched — the new module gets its own twin), all design
notes, the denylist. **bp-033's surface** (`test_temporal_operators.py`, the σ/π operators, `‖[d,τ]‖`) is
out of THIS plan.

## 6. Interfaces pinned inline

```python
# core/stores/reference_edges.py — the 1-cell read surface (bp-026 v2):
def all(self, *, direction: str | None = None, ref_type: str | None = None,
        source_ref: str | None = None, target_ref: str | None = None) -> list[ReferenceEdge]: ...
#   direction="corpus_to_corpus" → doc→doc citation edges. DIRECTIONS includes it; KINDS=("code","corpus").
# ReferenceEdge: source_kind/source_ref/source_detail, target_kind/target_ref/target_detail,
#                ref_type, commit_sha, source_line, edge_id;  .direction is DERIVED.

# core/stores/versions.py — the D-arrow (supersession) source:
def supersessions(self, doc_id: str) -> list[tuple[int, int]]: ...   # consecutive (superseded, superseding)
def history(self, doc_id: str) -> list[Version]: ...                 # version_seq order

# core/complex/hodge.py — REUSED UNCHANGED on the symmetrized citation backbone A_cite (csr, symmetric):
def hodge_laplacian_1(A: sp.csr_matrix) -> sp.csr_matrix: ...   # L₁ = ∂₁ᵀ∂₁ + ∂₂∂₂ᵀ ; dim ker L₁ = β₁
def harmonic_basis(A: sp.csr_matrix) -> np.ndarray: ...         # (n_edges, β₁), deterministic dense SVD
def boundary_1(A: sp.csr_matrix) -> sp.csr_matrix: ...          # ∂₁ : C₁→C₀ signed incidence
_MAX_DENSE_EDGES = 20_000   # inherit the guard; never a silent sparse fallback

# core/complex/topology.py — the INDEPENDENT β₁ oracle:
def persistence(D: np.ndarray, *, maxdim: int = 1) -> dict[str, Any]: ...   # ripser dgms; H₁ count = β₁

# The isolation invariant this module MUST NOT weaken (test_reference_edge_isolation.py:131-132):
#   set(inspect.signature(build_complex).parameters) == {"view", "edges", "derived", "sim_floor"}
#   and `core/complex/**` never imports core.stores.reference_edges.
```

## 7. Items

### Item 5 — `X_cite` assembly (0-cells, 1-cells, D-arrows)
- **Objective:** build a deterministic sparse `X_cite` from `ReferenceEdgeStore.all(direction=
  "corpus_to_corpus")` (1-cells over note 0-cells) + `VersionStore` D-arrows — a pure function of the
  store contents at a commit, with a stable node ordering.
- **Files:** `core/temporal/__init__.py`, `core/temporal/complex.py` (the assembler + the `A_cite`
  symmetrized backbone for the Hodge reuse).
- **Acceptance test:** on a fixture citation store, assembly yields the same cells + `A_cite` sparsity
  run-to-run (byte-identical on the same input); node/edge ordering is deterministic (documented, not
  dict-iteration-dependent).
- **Falsifier:** a computed structure differs run-to-run on the same store (nondeterminism); OR
  `core/temporal/complex.py` imports anything that routes `reference_edges` into `core/complex` (Item 4
  reddens).
- **Invariant(s):** no store WRITE handle; no model/network; the D-arrows are kept **directed** and are
  NOT symmetrized into `A_cite` (A5 — a mixed `L₁` is a type error).
- **Touches stored data?** No (reads only).  **Parallelizable?** No (shares the package with 6–8).
  **Depends on:** bp-031 (rename-stable `doc_id` for the D-arrows).

### Item 6 — boundary maps `∂` / `δ_D` and the `δ_D² = 0` check
- **Objective:** the citation-complex boundary `∂` and the supersession coboundary `δ_D`, with the
  Result-1 H0 verification `δ_D² = 0` (the poset ⇒ nerve ⇒ coboundary² = 0 fact).
- **Files:** `core/temporal/boundary.py`.
- **Acceptance test:** `δ_D² == 0` (to numerical zero) on fixtures including a multi-step supersession
  chain; `∂₁∂₂ = 0` reused/confirmed via `hodge` on `A_cite`.
- **Falsifier:** `δ_D² ≠ 0` on a valid (acyclic) fixture — the supersession relation was assembled as
  something other than a strict partial order (H0 violated), OR a rename forked a chain (⇒ bp-031 gap).
- **Invariant(s):** the D-arrows form a strict partial order (acyclic) — a cycle is a **stop-and-raise**
  (§10), not a silently-tolerated input.
- **Touches stored data?** No.  **Parallelizable?** No.  **Depends on:** Item 5.

### Item 7 — the `dim ker L₁ == β₁` topological falsifier
- **Objective:** compute `dim ker L₁` of `X_cite`'s flag complex (reuse `hodge.hodge_laplacian_1` on
  `A_cite`) and assert equality with an **independent** ripser β₁ (`topology.persistence` on
  `distance = 1 − w`), within tolerance — the note §3 Consequence-1 falsifier, lifted to citations.
- **Files:** `core/temporal/complex.py` (the `dim ker L₁` accessor), the test in
  `tests/unit/test_temporal_complex.py`.
- **Acceptance test:** on fixtures with known cycle structure (a tree → β₁=0; an isometric 4-cycle →
  β₁=1), `dim ker L₁` equals the ripser H₁ count exactly.
- **Falsifier:** `dim ker L₁ ≠ ripser β₁` on a fixture — the assembled complex is **not** the flag
  complex of the citation graph (an orientation/incidence bug, or a wrong 2-cell rule), *the* thing this
  falsifier exists to catch (`edge-dynamics §2.2` twin).
- **Invariant(s):** deterministic dense path only (inherit `_MAX_DENSE_EDGES`); never an iterative
  eigensolver.
- **Touches stored data?** No.  **Parallelizable?** No.  **Depends on:** Items 5–6.

### Item 8 — the isolation twin (`core/temporal` never reaches the balance math)
- **Objective:** the forever-green guard that `core/temporal/` reads citation edges but **no instrument
  moves** — the B-c falsifier, one level up (note §2.4 "two complexes, two homes").
- **Files:** `tests/integration/test_temporal_isolation.py` (NEW).
- **Acceptance test:** (structural) no module under `core/complex/` imports `core/temporal`; `build_complex`'s
  signature is still exactly `{view, edges, derived, sim_floor}`; (behavioral) populating `X_cite` over
  the same authored nodes leaves `frustration`/`forman`/clustering **bit-identical** (the
  `test_reference_edge_isolation.py` pattern, twinned for the new module).
- **Falsifier:** any instrument result changes when `X_cite` is populated (a citation edge leaked into
  `A_signed`/`A`) — the fix belongs at the module boundary, never in `core/complex`.
- **Invariant(s):** Inv 2 (cross-stratum edges never reach the balance math); the existing
  `test_reference_edge_isolation.py` stays green (untouched).
- **Touches stored data?** No.  **Parallelizable?** No.  **Depends on:** Item 5.

## 8. Math carried explicitly

- **`X_cite` — the citation complex** — *measures:* the deterministic (embedder-independent) cross-note
  citation structure at a commit — the "embedder-invariant floor" (note §2.5). *valid when:* built from
  `reference_edges` `corpus_to_corpus` 1-cells over note 0-cells; D-arrows rename-stable (bp-031).
  *fails its keep if:* a computed invariant moves run-to-run on the same commit, or it can only be built
  by reading the embedding (it must not — that would collapse the signal/noise discriminator).
- **`∂` / `δ_D` — boundary and supersession coboundary** — *measures:* incidence of the citation complex
  (`∂`) and the supersession poset's coboundary (`δ_D`). *valid when:* supersession is a strict partial
  order (acyclic) ⇒ `δ_D² = 0` (Result 1 H0). *fails its keep if:* `δ_D² ≠ 0` on an acyclic fixture.
- **`dim ker L₁` (= β₁)** — *measures:* the number of independent citation "threads" (1-cycles not
  bounding a filled 2-simplex) — the harmonic content of the flag complex. *valid when:* `A_cite` is the
  symmetrized citation backbone, `n_edges ≤ 20_000` (dense determinism). *fails its keep if:* it
  disagrees with an independent ripser β₁ at matching scale — the built cross-check (Item 7).

## 9. Non-goals

- **No temporal-transport operators** (`σ_*`/`σ^*`/`π_active`) and **no `‖[d,τ]‖`** — that is **bp-033**.
- **No `(β,z)` retrieval curve `K(β)`** (weighted/RSP family) — TA-a/TA-b, bp-034+; this is combinatorial
  v1, unweighted.
- **No empirical Thread-C sweep / arrow-aware census** over the real corpus — that is a downstream
  measurement plan gated on THIS module landing (see §12).
- **No edit to `core/complex/`** — `hodge`/`topology` are reused unchanged.

## 10. Stop-and-raise conditions

- **The supersession relation contains a cycle** (D-arrows not a strict partial order) → `δ_D² ≠ 0`; do
  not silently tolerate — **file a `math`/`codebase` finding** (H0 violated: either a data defect or a
  bp-031 rename fork) and park Item 6's criterion.
- **`dim ker L₁ ≠ ripser β₁`** persists after an orientation/incidence review → **file a `math` finding**
  (the assembled complex is not the flag complex); do not adjust the tolerance to force agreement.
- **Any instrument moves when `X_cite` is populated** (Item 8) → a cross-stratum leak → **stop**, fix at
  the module boundary, file a finding; never touch `core/complex` to make the test pass.
- Any blessing flip → must not.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| Weighting of `A_cite` | **Combinatorial v1** (unweighted), inheriting `hodge`'s v1 inner product | Weighted inner products / magnetic `L^{(q)}` (rejected here: TA-a/PD-b parked; no second customer yet; on the *binary* citation graph the β-deformation is degenerate, note §2.1) | the metric-coherence tier (Result 4) is built, or PD-b's second customer arrives (TA-a) |
| 2-cell rule for `X_cite` | The **flag (clique) complex** of the citation backbone (matches `hodge`/Rips, note §2.2) | A bespoke 2-cell rule (rejected: would break `dim ker L₁ == ripser β₁` — the falsifier is the whole point) | never, without a new falsifier |
| Module package name (TA-d) | **`core/temporal/`** (PINNED by this plan) | `core/query/` (rejected: `query` conflates with the retrieval protocol, which stays in `dn-core-query-protocol`) | — (resolved) |

## 12. Dependency & ordering summary

Blast-radius order (all read-only sensing, one session): **Item 5** (assembly) → **Item 6** (boundary +
`δ_D²=0`) → **Item 7** (`dim ker L₁ == β₁` falsifier) ∥ **Item 8** (isolation twin, needs only Item 5).
All share `core/temporal/**` → one session, not parallel. **`depends_on: bp-031`** (rename-stable
`doc_id` for the D-arrows). Model: **opus** (a new deterministic math module; the `δ_D²=0` and
`dim ker L₁==β₁` falsifiers need judgment to evaluate). **Downstream, gated on THIS plan landing:**
**bp-033** (the σ/π operators + `‖[d,τ]‖`, `depends_on: bp-032`); then the empirical **Thread-C sweep +
arrow-aware census** (note §3 Consequence 2, "no new license") and the **`K(β)` retrieval curve** (note
§3 Consequence 3, TA-b) — each graduates once this module's API is concrete.
