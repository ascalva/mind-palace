module

public import Palace.Laplacian
public import Mathlib.Testing.Plausible.Sampleable
public import PalaceTest.Attack
public meta import Palace.Laplacian
public meta import Mathlib.Testing.Plausible.Sampleable
public meta import PalaceTest.Attack

/-!
# Attacks on `Palace.Laplacian`

The Plausible attacks and negative controls for the laws of `Palace/Laplacian.lean`. They run
when this module builds (`lake test`); the library itself runs no code at build time.
-/

@[expose] public section

open Matrix Finset

namespace Palace

/-! ## Attacks

Each law is attacked on its exact instance, `V = Fin 5` and `R = ℚ`, with the matrix built from a
random edge list. Repeated edges add up and self-loops are allowed, as in the sparse adjacency the
Python receives. Each control states a nearby false law, with a hypothesis dropped or the signed
Laplacian in place of `L`, and must be refuted.
-/

namespace Attack

/-- The weight matrix of an arc list: entry `(i, j)` sums the weights listed for `(i, j)`. -/
def ofArcs (es : List (Fin 5 × Fin 5 × ℤ)) : Matrix (Fin 5) (Fin 5) ℚ :=
  fun i j ↦ ((es.filter fun e ↦ e.1 = i ∧ e.2.1 = j).map fun e ↦ (e.2.2 : ℚ)).sum

/-- The symmetric weight matrix of an edge list: `(u, v, w)` adds `w` at `(u, v)` and `(v, u)`. -/
def ofEdges (es : List (Fin 5 × Fin 5 × ℤ)) : Matrix (Fin 5) (Fin 5) ℚ :=
  ofArcs es + (ofArcs es)ᵀ

/-- An edge list with nonnegative weights. -/
def nonneg (es : List (Fin 5 × Fin 5 × ℕ)) : List (Fin 5 × Fin 5 × ℤ) :=
  es.map fun e ↦ (e.1, e.2.1, e.2.2)

/-- A vector from a list, padded with zeros. -/
def vec (xs : List ℤ) : Fin 5 → ℚ := fun i ↦ xs.getD i 0

/-- A 0/1 vector from a list: few distinct values, so `L·x = 0` is hit often. -/
def bits (xs : List (Fin 2)) : Fin 5 → ℚ := fun i ↦ (xs.getD i 0 : ℕ)

/-- `x` takes one value across every edge of nonzero weight in `A`. -/
def ConstantOnEdges (A : Matrix (Fin 5) (Fin 5) ℚ) (x : Fin 5 → ℚ) : Prop :=
  ∀ i j, A i j ≠ 0 → x i = x j

/- Instance search does not find the nested `∀ i j : Fin 5` on its own; one quantifier at a time. -/
instance (A : Matrix (Fin 5) (Fin 5) ℚ) (x : Fin 5 → ℚ) : Decidable (ConstantOnEdges A x) :=
  have (i : Fin 5) : Decidable (∀ j, A i j ≠ 0 → x i = x j) := inferInstance
  Nat.decidableForallFin _

/-- `x` takes at least two values, so a kernel vector exercises more than `L·1 = 0`. -/
def NonConstant (x : Fin 5 → ℚ) : Prop := ∃ i, x i ≠ x 0

instance (x : Fin 5 → ℚ) : Decidable (NonConstant x) := Nat.decidableExistsFin _

/- LAP-1, attacked on arbitrary arcs: asymmetric and signed. -/
#eval survives (∀ es : List (Fin 5 × Fin 5 × ℤ), lap (ofArcs es) *ᵥ 1 = 0) 1

/- LAP-1 control: the signed Laplacian does not annihilate `1` (its kernel is not `span 1`). -/
#eval refuted (∀ es : List (Fin 5 × Fin 5 × ℤ), signedLap (ofEdges es) *ᵥ 1 = 0) 2

/- LAP-2: `xᵀLx ≥ 0` on symmetric nonnegative weights. -/
#eval survives (∀ es : List (Fin 5 × Fin 5 × ℕ), ∀ xs : List ℤ,
  0 ≤ vec xs ⬝ᵥ (lap (ofEdges (nonneg es)) *ᵥ vec xs)) 3

/- LAP-2 control, weights of either sign. -/
#eval refuted (∀ es : List (Fin 5 × Fin 5 × ℤ), ∀ xs : List ℤ,
  0 ≤ vec xs ⬝ᵥ (lap (ofEdges es) *ᵥ vec xs)) 4

/- LAP-2 control, nonnegative but asymmetric weights. -/
#eval refuted (∀ es : List (Fin 5 × Fin 5 × ℕ), ∀ xs : List ℤ,
  0 ≤ vec xs ⬝ᵥ (lap (ofArcs (nonneg es)) *ᵥ vec xs)) 5

/- LAP-2, signed: `xᵀL̄x ≥ 0` on symmetric weights of either sign. -/
#eval survives (∀ es : List (Fin 5 × Fin 5 × ℤ), ∀ xs : List ℤ,
  0 ≤ vec xs ⬝ᵥ (signedLap (ofEdges es) *ᵥ vec xs)) 6

/- LAP-2 signed control, asymmetric weights. -/
#eval refuted (∀ es : List (Fin 5 × Fin 5 × ℤ), ∀ xs : List ℤ,
  0 ≤ vec xs ⬝ᵥ (signedLap (ofArcs es) *ᵥ vec xs)) 7

/- LAP-3's reduction, forward: a kernel vector is constant across every weighted edge. The guards
keep only non-constant kernel vectors (a graph with several components), and `survives` requires
100 of them. -/
#eval survives (∀ es : List (Fin 5 × Fin 5 × ℕ), ∀ xs : List (Fin 2),
  NonConstant (bits xs) → lap (ofEdges (nonneg es)) *ᵥ bits xs = 0 →
    ConstantOnEdges (ofEdges (nonneg es)) (bits xs)) 8

/- LAP-3's reduction, backward: a vector constant across every weighted edge is in the kernel. -/
#eval survives (∀ es : List (Fin 5 × Fin 5 × ℕ), ∀ xs : List (Fin 2),
  NonConstant (bits xs) → ConstantOnEdges (ofEdges (nonneg es)) (bits xs) →
    lap (ofEdges (nonneg es)) *ᵥ bits xs = 0) 9

/-! Random search does not refute LAP-3 with a hypothesis dropped: the same `refuted` controls,
signed weights with 0/1 or integer vectors and asymmetric weights with integer vectors, found no
counterexample in 396, 215 and 228 tested instances (seeds 10–12, measured 2026-10-31). A
counterexample needs weights that cancel at every vertex, which random edge lists rarely produce.
Both hypotheses are shown to be needed by proof instead. -/

/-- LAP-3 needs `w ≥ 0`: on the 4-cycle `0 – 1 – 3 – 2 – 0` with alternating signs, the indicator
of `{0, 3}` is in the kernel, yet it differs across the weighted edge `0 – 1`. -/
theorem lap_kernel_needs_nonneg :
    ∃ A : Matrix (Fin 4) (Fin 4) ℚ, A.IsSymm ∧
      ∃ x : Fin 4 → ℚ, lap A *ᵥ x = 0 ∧ A 0 1 ≠ 0 ∧ x 0 ≠ x 1 := by
  refine ⟨!![0, 1, -1, 0; 1, 0, 0, -1; -1, 0, 0, 1; 0, -1, 1, 0], ?_, ![1, 0, 0, 1], ?_,
    by simp, by simp⟩
  · ext i j; fin_cases i <;> fin_cases j <;> rfl
  · ext i; fin_cases i <;> simp [lap, degree, mulVec, dotProduct, Fin.sum_univ_four]

/-- LAP-3 needs symmetry: with arcs `0 → 1` and `0 → 2` of weight 1, `x = (1, 0, 2)` is in the
kernel, yet it differs across the arc `0 → 1`. -/
theorem lap_kernel_needs_symm :
    ∃ A : Matrix (Fin 3) (Fin 3) ℚ, (∀ i j, 0 ≤ A i j) ∧
      ∃ x : Fin 3 → ℚ, lap A *ᵥ x = 0 ∧ A 0 1 ≠ 0 ∧ x 0 ≠ x 1 := by
  refine ⟨!![0, 1, 1; 0, 0, 0; 0, 0, 0], ?_, ![1, 0, 2], ?_, by simp, by simp⟩
  · intro i j; fin_cases i <;> fin_cases j <;> simp
  · ext i; fin_cases i <;> simp [lap, degree, mulVec, dotProduct, Fin.sum_univ_three]
    norm_num

end Attack

end Palace
