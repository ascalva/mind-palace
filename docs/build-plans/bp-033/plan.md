---
type: build-plan
id: bp-033
status: proposed
design_ref:
  - docs/design-notes/temporal-retrieval-algebra.md
contract: builder
write_scope:
  - core/temporal/**
  - tests/unit/test_temporal_operators.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 400k
  actual: null
depends_on:
  - bp-032
parallelizable_with: []
created: 2026-07-14
updated: 2026-07-14
links:
  - docs/design-notes/temporal-retrieval-algebra.md
  - docs/design-notes/core-query-protocol.md
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — `core/temporal/`: the mode-3 operators + the superconnection curvature `‖[d,τ]‖`

> **Every section below is required.** Inapplicable sections are marked `N/A — <reason>`.

## 0. Mode & provenance

Investigation and planning produced this plan (grounded pass, §3 citations inline); implementation
proceeds **item-by-item on owner approval**. It graduates the **temporal-transport half** of
`dn-temporal-retrieval-algebra` §3 Consequence 1 — the two mode-3 operators (`π_active`, `σ_*`/`σ^*`) and
the superconnection curvature norm `‖[d,τ]‖` — over the `X_cite` complex that **bp-032** assembles.
`depends_on: bp-032` (it consumes bp-032's pinned module API). Authority-to-act is separate from the
owner-only `proposed → ready` blessing.

**Read-only sensing, no store mutation (opus, deterministic).** These are pure operators over the sparse
citation complex — no store write handle, no model, no network. The bp-032 isolation twin covers the
whole `core/temporal/` package, so these operators inherit it (they add no store reach).

## 1. Objective

Add the mode-3 operators `π_active` (ledger-compression), `σ_*`/`σ^*` (correspondence-transport +
pullback), and the superconnection curvature norm `‖[d,τ]‖` over `X_cite` — each carrying the note's
operator laws as runnable checks.

## 2. Context manifest

Read whole, in order:

1. `docs/design-notes/temporal-retrieval-algebra.md` — §2.2 (A2: the two operators, formalized and
   re-ranked — `π_active` the ambient default, `σ_*` the opt-in traversal; the composite `T_active`),
   §2.3 (Result 2 `[d,τ]` closed form; Result 3 the superconnection; Result 5 Sz.-Nagy dilation, pin the
   pullback `σ^*`; Result 6 γ-contraction), §2.7 (the inversion Rule 2 binds every result).
2. `core/temporal/complex.py`, `core/temporal/boundary.py` (**bp-032**) — the `X_cite` assembler, the
   `∂`/`δ_D` boundary maps, and the two-snapshot accessor (`X_cite` at commit n and n+1) these operators
   consume. **Pinned API in §6.**
3. `core/stores/reference_edges.py` — `for_commit(commit_sha)` (the two-snapshot source) and `all(...)`.
4. `core/stores/versions.py` — `supersessions(doc_id)` / `history(doc_id)`: the note-correspondence σ is
   induced by the supersession relation D between the two snapshots.
5. `docs/design-notes/core-query-protocol.md` — C3 (the operators' naming/typing:
   `T = window, E ∋ D, direction ∈ {forward = σ_*, backward = σ^*}`); the "declare which" framing A2
   corrects.

## 3. Investigation & grounding

- **Q1 — What is `π_active`, precisely?** Orthogonal projection onto the not-yet-superseded subspace
  (note §2.2): a **contraction** (`‖Π‖ ≤ 1`), **idempotent** (`Π² = Π`), **not** a chain map, does not
  compose functorially. It is the operator form of the `D`-exclusion invariant applied to *every*
  non-temporal query (the ambient default, `T = now`). **The note settles the definition**; the code
  handle is bp-032's active-subspace basis (the not-yet-superseded 0-/1-cells).
- **Q2 — What is `σ_*` / `σ^*`?** `σ_*` : `C^•(X_n) → C^•(X_{n+1})` is a **chain map**, degree 0,
  covariant **iff F1** (simpliciality — a revised note's citations carry forward); it **composes** iff F2;
  it **retains** superseded content (points forward, keeps lineage). `σ^*` is the pullback/adjoint (the
  `backward` direction; **always a contraction** — the Sz.-Nagy dilation is pinned to it, Result 5). **The
  note settles the definitions**; σ is *induced by the supersession correspondence* between the two
  snapshots (Q4).
- **Q3 — What is `‖[d,τ]‖`, and what does it equal?** For the superconnection `𝔸 = d + τ`,
  `𝔸² = [d,τ] + τ²`; the curvature is `[d,τ]`, and (Result 2, PROVEN tight)
  `([d,τ]φ)(u,v) = (φ(σv) − φ(σu)) · 𝟙[{σu,σv} ∉ X_{n+1}]` — so **`‖[d,τ]‖` IS the (weighted) count of
  citations that fail to carry forward** (severed citations), *not a proxy*. "Now computable on the
  authored-note citation graph (bp-026 complete)" (note §2.3). **The note settles the closed form** →
  the check is the closed form vs the operator computation.
- **Q4 — Where does the correspondence σ come from?** From the supersession relation D between the
  snapshots: a note superseded at the version boundary maps to its successor; `σ` is that map on 0-cells,
  lifted to citations. Source: `VersionStore.supersessions(doc_id)` (`versions.py:101`) +
  `reference_edges.for_commit(n)`/`for_commit(n+1)`. **The code settles the source**; bp-032 exposes the
  two-snapshot accessor. *Where the note does not settle:* fork/merge diamonds (`σ` not single-valued) —
  Result 3's homotopy-coherent case is **SKETCH/Parked (TA-c)**; **this plan handles the linear chain
  only** (single-valued σ) and stop-and-raises on a diamond (§10).
- **Q5 — What binds these continuous operators to reality?** The inversion Rule 2 (note §2.7): every
  computed quantity must reproduce the exact discrete invariants at the sample times — so `‖[d,τ]‖`'s
  operator value must equal the discrete severed-citation count, and `σ_* d = d σ_*` must hold exactly
  when F1 holds. **The note settles the falsification discipline.**

**Additional risks or questions surfaced during reading:** (a) `σ_*` preserves **homology** but not
**kernels** (Result 4: needs σ isometric for `σ_* δ = δ σ_*`) — this plan asserts only the *chain-map*
law `σ_* d = d σ_*` (topological coherence), NOT metric/kernel coherence (that is PD-b's customer, TA-a,
out of scope). (b) `T_active = π_active ∘ σ_* ∘ ι` (Result 5) is the one canonical composite — this plan
builds it and checks it is a **contraction** (`‖T_active‖ ≤ 1`); the full Sz.-Nagy *dilation* as a
constructed object is heavier and deferred (the note states it as a theorem; v1 checks the contraction +
that `σ^*` is a contraction).

## 4. Reconciliation

- `dn-temporal-retrieval-algebra §2.2` corrects `dn-core-query-protocol §2.5`'s "declare which" framing
  (the two operators are **not peers** — `π_active` is the ambient default, `σ_*` the opt-in). →
  **[cross-ref: extension]** this plan implements the corrected ranking; both notes are ratified/immutable
  (the correction already lives in the ratified successor note — no note is edited here).
- No committed code is corrected — the operators are additive over bp-032's module.

## 5. Write scope

Front-matter: `core/temporal/**` (extends bp-032's package — `operators.py` for `π_active`/`σ`,
`superconnection.py` for `[d,τ]`/`‖·‖`), `tests/unit/test_temporal_operators.py` (the operator-law +
`‖[d,τ]‖` unit tests). **Deliberately OUT of scope:** `core/complex/**` (read/import only),
`core/stores/**` (read only), bp-032's already-landed files insofar as their **public API is honored, not
redesigned** (a needed API change is a stop-and-raise → re-graduate bp-032, never edit its contract
mid-build), all design notes, the denylist. The isolation twin (`test_temporal_isolation.py`) is bp-032's
— not re-authored here.

## 6. Interfaces pinned inline

```python
# core/temporal/ (bp-032) — the API this plan consumes (honored, not redesigned):
#   complex.py:   assemble X_cite at a commit → cells + A_cite (symmetric csr backbone); a two-snapshot
#                 accessor for (X_n, X_{n+1}); the active-subspace basis (not-yet-superseded cells).
#   boundary.py:  ∂ (citation boundary) and δ_D (supersession coboundary), δ_D² = 0 verified.
# (bp-032 pins the exact signatures in its §6/§7; this plan builds ON them.)

# The note's operator laws (dn-temporal-retrieval-algebra §2.2–§2.3), as runnable checks:
#   π_active : projection onto not-yet-superseded subspace — idempotent (Π²=Π), contraction (‖Π‖≤1),
#              NOT a chain map. Ambient default (T = now).
#   σ_*      : C^•(X_n) → C^•(X_{n+1}), degree 0, chain map iff F1 (σ_* d = d σ_*); composes iff F2;
#              retains superseded content.
#   σ^*      : the pullback/adjoint (backward), ALWAYS a contraction (Result 5 dilation pin).
#   T_active = π_active ∘ σ_* ∘ ι  — the canonical composite; a contraction (‖T_active‖ ≤ 1).
#   [d,τ]    : 𝔸 = d + τ, 𝔸² = [d,τ] + τ² ; ([d,τ]φ)(u,v) = (φ(σv) − φ(σu))·𝟙[{σu,σv} ∉ X_{n+1}]
#              ‖[d,τ]‖ = the (weighted) severed-citation-carry-forward count (Result 2, tight).

# core/stores/reference_edges.py — two-snapshot source:
def for_commit(self, commit_sha: str) -> list[ReferenceEdge]: ...
# core/stores/versions.py — the σ correspondence source:
def supersessions(self, doc_id: str) -> list[tuple[int, int]]: ...
```

## 7. Items

### Item 9 — `π_active` (ledger-compression projection)
- **Objective:** the orthogonal projection onto the not-yet-superseded subspace of `X_cite` — the
  `D`-exclusion operator applied by default (`T = now`).
- **Files:** `core/temporal/operators.py`.
- **Acceptance test:** on fixtures with superseded cells, `Π² == Π` (idempotent) and `‖Π x‖ ≤ ‖x‖` for
  all x (contraction); `Π` annihilates the superseded subspace exactly.
- **Falsifier:** `Π² ≠ Π` (not a projection) or `‖Π‖ > 1` (not a contraction) — the operator is not
  `π_active`; OR `Π` is (incorrectly) implemented as a chain map (it must NOT be — note §2.2).
- **Invariant(s):** `π_active` destroys superseded content (the ambient default view); no store write.
- **Touches stored data?** No.  **Parallelizable?** No (shares the package).  **Depends on:** bp-032.

### Item 10 — `σ_*` / `σ^*` (correspondence-transport + pullback)
- **Objective:** the chain map `σ_*` : `C^•(X_n) → C^•(X_{n+1})` induced by the supersession
  correspondence, and its pullback `σ^*` — the opt-in temporal traversal (C3 typing).
- **Files:** `core/temporal/operators.py`.
- **Acceptance test:** on a **linear-chain** fixture where F1 holds, `σ_* ∘ ∂ == ∂ ∘ σ_*` (the chain-map
  law) to numerical zero, `σ_*` is degree 0, and `σ^*` is a contraction (`‖σ^* x‖ ≤ ‖x‖`); on a fixture
  with a **severed** citation (F1 fails) the chain-map law visibly breaks (the honest negative).
- **Falsifier:** `σ_* ∂ ≠ ∂ σ_*` when F1 holds (implementation bug — σ is not a chain map), OR `σ_*`
  changes degree, OR `σ^*` is not a contraction.
- **Invariant(s):** `σ_*` retains superseded content (never destroys — the opposite of `π_active`);
  linear-chain only (single-valued σ) — a diamond is a stop-and-raise (§10, TA-c).
- **Touches stored data?** No.  **Parallelizable?** No.  **Depends on:** bp-032; Item 9 (for `T_active`).

### Item 11 — `‖[d,τ]‖` (the superconnection curvature norm)
- **Objective:** compute `[d,τ]` via `𝔸 = d + τ` and its norm — asserting it **equals the closed-form
  severed-citation-carry-forward count** (Result 2, tight).
- **Files:** `core/temporal/superconnection.py`.
- **Acceptance test:** on a fixture with a **known** set of severed citations, the operator `‖[d,τ]‖`
  equals the direct count `Σ 𝟙[{σu,σv} ∉ X_{n+1}]` (weighted) exactly (the inversion Rule 2); on a fixture
  where every citation carries forward (F1 holds fully), `[d,τ] = 0` (flat — the bicomplex case).
- **Falsifier:** `‖[d,τ]‖` differs from the discrete severed-citation count — the operator is a proxy,
  not the invariant (the note's explicit "not a proxy" claim would be violated); OR `[d,τ] ≠ 0` when no
  citation is severed.
- **Invariant(s):** the operator value reproduces the exact discrete invariant at the sample times
  (inversion Rule 2); the two curvature layers stay distinct (this `[d,τ]` is the linear-chain
  superconnection, NOT diamond holonomy, NOT static Forman–Ricci — note §2.3 Result 3).
- **Touches stored data?** No.  **Parallelizable?** No.  **Depends on:** Item 10 (needs σ).

### Item 12 — `T_active` composite + the contraction check
- **Objective:** the canonical composite `T_active = π_active ∘ σ_* ∘ ι` and the runnable form of Result
  5 — `T_active` is a contraction; `σ^*` is the pinned dilation direction.
- **Files:** `core/temporal/operators.py`, the test in `tests/unit/test_temporal_operators.py`.
- **Acceptance test:** `‖T_active x‖ ≤ ‖x‖` for all fixture x (contraction); the composite is assembled
  exactly as `π_active ∘ σ_* ∘ ι` (embed → transport → compress), matching the note's naming.
- **Falsifier:** `‖T_active‖ > 1` (not a contraction — Result 5's Sz.-Nagy framing would be false); OR
  the composite is assembled in the wrong order.
- **Invariant(s):** deterministic; no store write.
- **Touches stored data?** No.  **Parallelizable?** No.  **Depends on:** Items 9–10.

## 8. Math carried explicitly

- **`π_active` — ledger-compression projection** — *measures:* the active (not-yet-superseded) view of a
  cochain (`T = now`). *valid when:* an orthogonal projection onto the active subspace — idempotent,
  `‖·‖ ≤ 1`. *fails its keep if:* `Π² ≠ Π` or `‖Π‖ > 1`, or it is (wrongly) a chain map.
- **`σ_*` / `σ^*` — correspondence-transport / pullback** — *measures:* how citations/threads carry across
  a supersession boundary (`σ_*` forward, `σ^*` backward). *valid when:* linear chain (single-valued σ);
  F1 ⇒ `σ_*` is a chain map (`σ_* ∂ = ∂ σ_*`), degree 0; `σ^*` a contraction. *fails its keep if:* the
  chain-map law fails under F1, or σ changes degree, or a diamond is silently averaged (TA-c).
- **`‖[d,τ]‖` — superconnection curvature norm** — *measures:* the (weighted) count of citations that
  fail to carry forward — the exact obstruction to bicomplex flatness (Result 2). *valid when:* the
  linear time-chain superconnection `𝔸 = d + τ`; σ single-valued. *fails its keep if:* it differs from
  the discrete severed-citation count (it would be a proxy, not the invariant), or it is conflated with
  diamond holonomy or Forman–Ricci curvature (same word, different tensors — note §2.3 Result 3).
- **`T_active` — active-view transport composite** — *measures:* embed-active → transport → compress-back.
  *valid when:* `π_active ∘ σ_* ∘ ι`, a contraction. *fails its keep if:* `‖T_active‖ > 1`.

## 9. Non-goals

- **No `X_cite` assembly / boundary maps / `dim ker L₁==β₁` falsifier** — that is bp-032 (consumed here).
- **No metric/kernel coherence** (`σ_* δ = δ σ_*`, weighted inner products) — Result 4 / PD-b / TA-a,
  deferred; this plan asserts only the topological chain-map law.
- **No diamond (fork/merge) superconnection** — the homotopy-coherent `τ_k` rigor is TA-c (SKETCH,
  data-gated on measured diamond frequency); this plan is the **linear chain only**.
- **No `(β,z)` retrieval curve, no empirical sweep, no census** — downstream plans (§12).

## 10. Stop-and-raise conditions

- **A fork/merge diamond appears** (σ not single-valued between the snapshots) → the linear-chain
  operators do not apply; **file a `math` finding** citing TA-c (measured-diamond-frequency gate) and park
  the affected criterion — do NOT average a multi-valued σ into a single map.
- **bp-032's public API needs to change** to build these operators → **stop and surface** (re-graduate
  bp-032 on a `spec-defect` warrant); never edit bp-032's contract mid-build.
- **`‖[d,τ]‖ ≠ the discrete severed-citation count`** after review → **file a `math` finding** (the
  operator is a proxy, violating Result 2); do not fudge tolerance to force agreement.
- Any blessing flip → must not.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| Fork/merge diamonds (TA-c) | **Linear chain only**; stop-and-raise on a diamond | Implement the homotopy-coherent twisted-complex (`τ_k`) now (rejected: SKETCH-grade in the note; unwarranted until measured diamond frequency) | measured fork/merge diamond frequency warrants the twisted-complex rigor (TA-c) |
| `T_active` as a constructed Sz.-Nagy dilation | Check the **contraction** (`‖T_active‖≤1`) + `σ^*` contraction; state the dilation as a theorem | Construct the full isometric dilation object now (rejected: heavy, no consumer until the ledger-space reader) | the ledger-space reader (Result 5 consumer) is proposed |
| Weighted vs combinatorial norm for `‖[d,τ]‖` | Combinatorial v1 (inherits bp-032's unweighted `A_cite`) | Weighted (rejected: PD-b/TA-a parked — no second customer) | TA-a re-entry |

## 12. Dependency & ordering summary

Blast-radius order (all read-only sensing, one session): **Item 9** (`π_active`) → **Item 10**
(`σ_*`/`σ^*`) → **Item 11** (`‖[d,τ]‖`, needs σ) → **Item 12** (`T_active` composite, needs 9–10). All
share `core/temporal/**` → one session, not parallel. **`depends_on: bp-032`** (consumes its `X_cite`
assembler + boundary maps + two-snapshot accessor). Model: **opus** (operator-law falsifiers and the
`‖[d,τ]‖`-equals-the-discrete-invariant check need judgment). **Downstream, gated on THIS + bp-032
landing:** the empirical **Thread-C sweep + arrow-aware census** (note §3 Consequence 2 — measures
`‖[d,τ]‖` flatness, F2-violation count, diamond frequency, β\* over the real corpus) and the **`K(β)`
retrieval curve** (note §3 Consequence 3, TA-b) — each graduates once these operators are concrete.
