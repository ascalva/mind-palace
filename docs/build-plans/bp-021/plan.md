---
type: build-plan
id: bp-021
status: ready
design_ref:
  - docs/design-notes/edge-dynamics.md # Lane A, §2.2 (the degree-1 lift, pinned); §3.1 L-a
contract: builder
write_scope:
  - "core/complex/hodge.py"
  - "tests/unit/test_hodge.py"
  - "docs/build-plans/bp-021/**"
  - "docs/findings/**"
session_budget: 1
cost:
  estimate: { model: sonnet, tokens: 300k } # pinned formulas + crisp synthetic-topology falsifiers (the tests ARE the judge); sign/orientation subtleties are what the estimate buys
  actual: null
depends_on: []
parallelizable_with: []
created: 2026-07-12
updated: 2026-07-12
links:
  - docs/brainstorms/edge-dynamics-and-continuum.md # the charter (physics dictionary; the inversion)
  - docs/REASONING-COMPLEX-BUILD.md # companion III — the degree-0 derivations this lifts
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — L-a: `core/complex/hodge.py` — the degree-1 instruments

> **Every section below is required.** N/A is an accountability act.

## 0. Mode & provenance

Graduated 2026-07-12 from the **ratified** `dn-edge-dynamics` (§2.2's pinned
definitions; §3.1 L-a). Investigation and planning produced this; implementation
proceeds item-by-item on owner approval. `proposed → ready` is the owner's hand edit.
First plan of the Lane A pair; bp-022 (the THREAD lens + temporal fields) depends on it.

## 1. Objective

`core/complex/hodge.py` exists: oriented flag-complex assembly over the existing
backbone, boundary operators `∂₁`/`∂₂`, the Hodge 1-Laplacian, the three-way
decomposition of any edge vector, a deterministic harmonic basis, and the L₁ eigenbasis
— all sparse, deterministic, model-free, network-free, proven on synthetic complexes of
known topology and cross-checked against the ripser β₁ on the live complex.

## 2. Context manifest

1. `docs/design-notes/edge-dynamics.md` §2.2 — every definition below is pinned there;
   this plan restates them as interfaces (§6) so no design is inferred.
2. `core/complex/laplacian.py` — the degree-0 house style being lifted (docstring
   discipline, PSD-by-construction, scipy.sparse-only).
3. `core/complex/build.py` — `ReasoningComplex` (`nodes/idx/A/A_signed`; NO triangle
   set exists today — this module derives it) and `cosine_adjacency` (`sim_floor`
   semantics).
4. `core/complex/topology.py` — `cosine_distance_matrix`, `persistence` (ripser,
   maxdim=1), `long_lived_holes` — the independent β₁ the falsifier compares against.
5. `tests/unit/test_complex.py` — the fixture/style precedent for complex-module tests.

## 3. Investigation & grounding

- **Q1 — does any triangle set exist to reuse?** No. `ReasoningComplex` carries
  `nodes/idx/A/A_signed/hyper/layers/created` only (`core/complex/build.py:40-60`);
  `hyper` is directed B-arcs (tail-set → head), explicitly NOT symmetric 2-simplices
  (note §2.2). The flag triangles are derived here from `A`'s sparsity pattern.
- **Q2 — is the flag choice consistent with the persistence machinery?**
  Yes, by construction: `topology.py` runs Vietoris–Rips over
  `cosine_distance_matrix` (`:45-67`), and Rips at scale t IS the flag complex of the
  distance-≤t graph. `distance = 1 − similarity` (`:45-58`), so the backbone at
  `sim_floor = σ` matches Rips at `t = 1 − σ`. This equivalence is what makes the Q4
  cross-check exact rather than approximate.
- **Q3 — what corpus scale must this handle?** The live complex is hundreds of notes /
  low-thousands of edges (the dreamer builds it per pass today). Dense null-space
  extraction at that scale is milliseconds-to-seconds and exactly deterministic; pinned
  §6(e) with an explicit size guard rather than a silent fallback to a nondeterministic
  sparse solver.
- **Q4 — how exactly do the two β₁ computations compare?** `dim ker L₁` of the flag
  complex at threshold t equals the number of H₁ persistence intervals ALIVE at t
  (born ≤ t, not yet dead at t) from `persistence(D, maxdim=1)`. Exact equality, no
  tolerance on the count (the dimensions are integers; the SVD tolerance in §6(e)
  affects only the rank cut, and the synthetic suite pins that it cuts correctly).
- **Q5 — where will this be consumed?** bp-022's THREAD lens and temporal fields
  (`STRUCTURAL_INTERPRETERS` registry, `compute_snapshot`). Nothing else imports it in
  this plan — the module lands consumer-free (the write-side-first house pattern).

**Additional risks surfaced during reading:** orientation-sign errors in `∂₂` produce a
WRONG kernel dimension only on some topologies — the synthetic suite must include a
filled triangle (β₁ = 0, catches a sign error that leaves the triangle's boundary
outside `im ∂₂`) AND an empty cycle (β₁ = 1) AND a two-hole complex; a wrong adjoint
convention breaks component orthogonality — asserted directly.

## 4. Reconciliation

N/A — nothing corrected or extended: a new module beside the degree-0 family; no
existing docstring claims anything about degree 1 (checked `laplacian.py`'s "deferred
sheaf/hypergraph members" line — that deferral is about transport generality, untouched
here and still true).

## 5. Write scope

In: the new module, its new test file, own plan dir, findings. Out, deliberately:
`core/complex/build.py` (`ReasoningComplex` gains NO field — the flag complex is
derived, not stored), every other `core/complex/` module, `core/dreaming/**` (bp-022),
`config/**` (bp-022), design notes, the foundation denylist.

## 6. Interfaces pinned inline

**(a) Module contract (header discipline per the complex family):** deterministic;
scipy.sparse + numpy only; no model, no network, no store handle; consumes a weighted
symmetric adjacency `A` (zero diagonal, w ≥ 0 — `cosine_adjacency`'s output shape).

**(b) The complex and its orientation (note §2.2, verbatim):**

```python
def edge_index(A: sp.csr_matrix) -> dict[tuple[int, int], int]:
    """C₁ basis: edges {i, j} with i < j (A's upper triangle), lexicographic order.
    Orientation i→j by ascending node index. Deterministic from A's sparsity."""

def flag_triangles(A: sp.csr_matrix) -> np.ndarray:
    """C₂ basis: the 3-cliques {i, j, k}, i < j < k, lexicographic. The FLAG complex —
    forced by Rips consistency (plan Q2); derivation hyperedges stay out (note §2.2)."""
```

**(c) Boundary operators (real coefficients; orientation signs from (b)):**

```python
def boundary_1(A) -> sp.csr_matrix:   # shape (n_nodes, n_edges): ∂₁(e_ij) = δ_j − δ_i
def boundary_2(A) -> sp.csr_matrix:   # shape (n_edges, n_tris): ∂₂(t_ijk) = e_jk − e_ik + e_ij
```

**(d) The operator and the decomposition:**

```python
def hodge_laplacian_1(A) -> sp.csr_matrix:
    """L₁ = ∂₁ᵀ∂₁ + ∂₂∂₂ᵀ (down + up). PSD by construction. dim ker L₁ = β₁ (flag)."""

@dataclass(frozen=True)
class HodgeParts:
    gradient: np.ndarray   # ∈ im ∂₁ᵀ  (induced by node potentials)
    curl: np.ndarray       # ∈ im ∂₂   (circulation around filled triangles)
    harmonic: np.ndarray   # ∈ ker L₁  (the threads)

def hodge_decompose(c: np.ndarray, A) -> HodgeParts:
    """c = gradient + curl + harmonic, the three mutually orthogonal (⟨·,·⟩ standard —
    v1 is combinatorial, note §2.2). Exact reconstruction to numerical tolerance."""

def harmonic_basis(A) -> np.ndarray:
    """(n_edges, β₁), orthonormal, DETERMINISTIC — §6(e). β₁ = 0 ⇒ shape (n_edges, 0)."""

def l1_spectrum(A, k: int) -> tuple[np.ndarray, np.ndarray]:
    """The k smallest eigenpairs of L₁ — the degree-1 Fourier basis (low = smooth
    large-scale flow). Consumed by later rungs (P5); provided, not yet wired."""
```

**(e) Determinism pin:** the harmonic basis and decomposition use DENSE numpy linear
algebra (SVD null space; projectors via lstsq/pinv) — exactly reproducible, no
iterative-solver nondeterminism. Rank cut: singular values `< 1e-10 * s_max`. A guard
raises `ValueError` when `n_edges > 20_000` (an order of magnitude above today's
corpus, Q3) naming the sparse-eigensolver upgrade as the deliberate future act — never
a silent switch.

**(f) The cross-check contract (Q4, the note's built-in falsifier):**
`dim ker L₁`(flag at σ) `== #{(b, d) ∈ dgms[1] : b ≤ 1−σ < d}` — exact integer
equality; the comparison harness is a test helper so bp-022 and future rungs reuse it.

## 7. Items

_(Lane A family numbering starts here)_

### Item 1 — the oriented flag complex + boundary operators

- **Objective:** §6(b,c) exactly.
- **Files:** `core/complex/hodge.py`, `tests/unit/test_hodge.py`
- **Acceptance test:** on hand-built fixtures: a triangle graph yields 1 flag triangle
  with `∂₁∂₂ = 0` (the fundamental identity, asserted as an exact sparse-matrix zero);
  a 4-cycle yields 0 triangles; edge/triangle orderings byte-stable across two calls.
- **Falsifier:** `∂₁ ∂₂ ≠ 0` on ANY fixture — the orientation signs are wrong (this
  single identity catches every sign-convention error).
- **Invariant(s):** no mutation of `A`; no new field on `ReasoningComplex`.
- **Touches stored data?** no
- **Parallelizable?** no **Depends on:** none

### Item 2 — L₁, the decomposition, the harmonic basis, the spectrum

- **Objective:** §6(d,e) exactly.
- **Files:** `core/complex/hodge.py`, `tests/unit/test_hodge.py`
- **Acceptance test:** synthetic-topology suite: empty 4-cycle → β₁ = 1; filled
  triangle → β₁ = 0; two disjoint cycles → β₁ = 2; cycle-with-chord (two filled
  regions) → the fixture's known β₁. For random edge vectors on each fixture:
  three-way orthogonality (pairwise dot < 1e-8), exact reconstruction (‖c − Σparts‖ <
  1e-8), idempotent re-decomposition. `l1_spectrum`'s smallest eigenvalue ≈ 0 exactly
  β₁ times. Size guard raises past the §6(e) ceiling (tested with a mock shape).
- **Falsifier:** any fixture's `dim ker L₁ ≠ known β₁` (the math is wrong, not tuned);
  or two runs of `harmonic_basis` on the same A differing in any element
  (determinism broken).
- **Invariant(s):** PSD (min eigenvalue ≥ −1e-10); dense path only under the guard.
- **Touches stored data?** no
- **Parallelizable?** no **Depends on:** Item 1

### Item 3 — the live cross-check (the two β₁'s agree on real data)

- **Objective:** the §6(f) harness + one journaled read-only run against the live
  corpus complex (build the `ReasoningComplex` exactly as `build_structural_context`
  does, compute both counts, record them).
- **Files:** `tests/unit/test_hodge.py` (the harness as a reusable helper + a hermetic
  fixture-complex test), `docs/build-plans/bp-021/journal.md` (the live numbers)
- **Acceptance test:** hermetic: harness equality holds on every synthetic fixture
  ACROSS three σ values (the scale-matching logic itself is what's under test). Live
  (read-only, journaled, not a committed test): both counts computed at the configured
  σ; equality holds; the numbers and σ recorded in the journal.
- **Falsifier:** the note's Lane A falsifier verbatim — at matching scale,
  `dim ker L₁ ≠ ` ripser's alive-bar count on the live complex (incidence algebra and
  persistent homology disagree ⇒ one implementation is wrong; stop-and-raise).
- **Invariant(s):** the live run reads stores, writes nothing (no snapshot, no
  attestation — measurement of the measurement machinery only).
- **Touches stored data?** no (read-only)
- **Parallelizable?** no **Depends on:** Item 2

## 8. Math carried explicitly

- **flag complex** — _measures:_ the 2-skeleton the backbone's cliques imply (which
  triangles are "filled"). _valid when:_ the backbone A is symmetric, non-negative,
  zero-diagonal (cosine_adjacency's contract). _fails its keep if:_ triangle
  enumeration dominates pass runtime at corpus scale (it must not — sparse A, Q3).
- **∂₁, ∂₂ (boundary operators)** — _measure:_ how edges attach to nodes and triangles
  to edges, with orientation. _valid when:_ `∂₁∂₂ = 0` exactly (chain-complex law).
  _fails its keep if:_ the identity fails on any input (sign bug — Item 1 falsifier).
- **L₁ = ∂₁ᵀ∂₁ + ∂₂∂₂ᵀ (Hodge 1-Laplacian)** — _measures:_ edge-flow smoothness; its
  kernel is exactly the harmonic (thread) space. _valid when:_ real coefficients,
  combinatorial inner product (v1). _fails its keep if:_ PSD violated or
  `dim ker L₁ ≠ β₁` on known topology.
- **Hodge decomposition (gradient ⊕ curl ⊕ harmonic)** — _measures:_ the unique
  three-way split of any edge vector: potential-driven flow, local circulation,
  and hole-orbiting flow. _valid when:_ the three subspaces are mutually orthogonal
  (finite-dimensional real Hodge theory — unconditional). _fails its keep if:_
  reconstruction or orthogonality fails tolerance, or downstream (bp-022) the harmonic
  part never yields a narratable thread (then the machinery is right but the corpus
  has no threads — an honest empirical no-signal, reported, not tuned away).

## 9. Non-goals

The THREAD lens, temporal fields, config constants (bp-022); any dreamer/panel change;
weighted inner products (note PD-b — parked); Lomb–Scargle/DMD/action rungs (P5,
data-gated); Ricci flow (note §2.4); reading observed strata (Lane B, gated); any
consumer wiring; sparse eigensolvers past the size guard.

## 10. Stop-and-raise conditions

Item 3's live cross-check fails (one of the two β₁ implementations is wrong — a
`math`-type finding routed to the orchestrator; do NOT adjust tolerances to force
agreement); the corpus complex exceeds the size guard already today (Q3's premise is
stale — re-plan the solver strategy); any need to modify `build.py` or `topology.py`
(the seam assumption broke — spec-defect finding).

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
| --- | --- | --- | --- |
| inner product | combinatorial (unweighted) v1 | strength-weighted L₁ (sharpens representatives, does not change β₁; premature geometry — note PD-b) | bp-022 finds harmonic representatives too delocalized to narrate |
| null-space method | dense SVD under an explicit size guard | sparse `eigsh` near zero (iterative nondeterminism poisons lens determinism); Smith normal form over ℤ (exact but overkill; ℝ suffices for β₁) | corpus edge count approaches the guard |
| spectrum exposure | provided (`l1_spectrum`), unconsumed | omit until a rung needs it (would force a second pass over this module at P5-R2; the marginal cost now is one thin function) | consumed by the first spectral rung |

## 12. Dependency & ordering summary

Item 1 → Item 2 → Item 3; strictly serial (each item's falsifier guards the next's
premise). All writes reversible; nothing stored is touched. Cross-plan: **bp-022
depends on this plan** (lens + temporal fields consume §6(d)); no parallel plan shares
scope. The module lands consumer-free; Lane A goes live for the owner only when bp-022
wires the lens.
