import Mathlib.Combinatorics.SimpleGraph.LapMatrix
import Mathlib.Testing.Plausible.Sampleable
import Palace.Attack

/-!
# The Laplacian family: LAP-1, LAP-2, LAP-3

Statements of the ledger's first Laplacian laws (dn-mathematical-foundations §2.2, seed table),
mirroring `core/kernel/complex/laplacian.py`. `A` is any square matrix over a ring; the Python
builds it from a sparse adjacency and allows self-loops, so nothing here assumes a zero diagonal.
-/

open Matrix Finset

namespace Palace

variable {V R : Type*} [Fintype V] [DecidableEq V]

/-- The weighted degree: the row sums of `A` (`laplacian.py`, `_degree`). -/
def degree [AddCommMonoid R] (A : Matrix V V R) (i : V) : R := ∑ j, A i j

/-- The combinatorial Laplacian `L = D − A` (`laplacian.py`, `laplacian`). -/
def lap [Ring R] (A : Matrix V V R) : Matrix V V R := diagonal (degree A) - A

/-- The signed Laplacian `L̄ = D̄ − A`, `D̄ᵢᵢ = Σⱼ |Aᵢⱼ|` (`laplacian.py`, `signed_laplacian`). -/
def signedLap [Ring R] [LinearOrder R] (A : Matrix V V R) : Matrix V V R :=
  diagonal (fun i ↦ ∑ j, |A i j|) - A

/-- **LAP-1** `L·1 = 0`, for every `A`: no symmetry, sign or weight condition is needed. -/
theorem lap_mulVec_one [Ring R] (A : Matrix V V R) : lap A *ᵥ 1 = 0 := by
  ext i
  rw [lap, sub_mulVec, Pi.sub_apply, mulVec_diagonal, Pi.one_apply, mul_one, Pi.zero_apply,
    sub_eq_zero]
  simp [degree, mulVec, dotProduct]

/-- Row `i` of `L·x` is `Σⱼ Aᵢⱼ (xᵢ − xⱼ)`. -/
theorem lap_mulVec_apply [CommRing R] (A : Matrix V V R) (x : V → R) (i : V) :
    (lap A *ᵥ x) i = ∑ j, A i j * (x i - x j) := by
  rw [lap, sub_mulVec, Pi.sub_apply, mulVec_diagonal, degree, sum_mul]
  simp only [mulVec, dotProduct]
  rw [← sum_sub_distrib]
  exact sum_congr rfl fun j _ ↦ by ring

/-- Row `i` of `L̄·x` is `Σⱼ (|Aᵢⱼ| xᵢ − Aᵢⱼ xⱼ)`. -/
theorem signedLap_mulVec_apply [CommRing R] [LinearOrder R] (A : Matrix V V R) (x : V → R)
    (i : V) : (signedLap A *ᵥ x) i = ∑ j, (|A i j| * x i - A i j * x j) := by
  rw [signedLap, sub_mulVec, Pi.sub_apply, mulVec_diagonal, sum_mul]
  simp only [mulVec, dotProduct]
  rw [← sum_sub_distrib]

/-- The Dirichlet identity behind LAP-2: `2 xᵀLx = Σᵢⱼ Aᵢⱼ (xᵢ − xⱼ)²` for symmetric `A`. -/
theorem two_mul_dotProduct_lap [CommRing R] (A : Matrix V V R) (hA : A.IsSymm) (x : V → R) :
    2 * (x ⬝ᵥ (lap A *ᵥ x)) = ∑ i, ∑ j, A i j * (x i - x j) ^ 2 := by
  have row : x ⬝ᵥ (lap A *ᵥ x) = ∑ i, ∑ j, A i j * (x i * (x i - x j)) := by
    simp only [dotProduct, lap_mulVec_apply, mul_sum]
    exact sum_congr rfl fun i _ ↦ sum_congr rfl fun j _ ↦ by ring
  have swap : ∑ i, ∑ j, A i j * (x j * (x j - x i)) = ∑ i, ∑ j, A i j * (x i * (x i - x j)) := by
    rw [sum_comm]
    exact sum_congr rfl fun i _ ↦ sum_congr rfl fun j _ ↦ by rw [hA.apply i j]
  rw [row, two_mul]
  nth_rewrite 2 [← swap]
  rw [← sum_add_distrib]
  refine sum_congr rfl fun i _ ↦ ?_
  rw [← sum_add_distrib]
  exact sum_congr rfl fun j _ ↦ by ring

/-- **LAP-2** `xᵀLx ≥ 0` for symmetric `A` with nonnegative entries. -/
theorem dotProduct_lap_nonneg [CommRing R] [LinearOrder R] [IsStrictOrderedRing R]
    (A : Matrix V V R) (hA : A.IsSymm) (hw : ∀ i j, 0 ≤ A i j) (x : V → R) :
    0 ≤ x ⬝ᵥ (lap A *ᵥ x) := by
  have h := two_mul_dotProduct_lap A hA x
  have : 0 ≤ ∑ i, ∑ j, A i j * (x i - x j) ^ 2 :=
    sum_nonneg fun i _ ↦ sum_nonneg fun j _ ↦ mul_nonneg (hw i j) (sq_nonneg _)
  linarith

/-- **LAP-2** as a matrix statement: `L` is positive semidefinite. -/
theorem posSemidef_lap [Field R] [LinearOrder R] [IsStrictOrderedRing R] [StarRing R]
    [TrivialStar R] (A : Matrix V V R) (hA : A.IsSymm) (hw : ∀ i j, 0 ≤ A i j) :
    (lap A).PosSemidef := by
  refine .of_dotProduct_mulVec_nonneg ?_ fun x ↦ ?_
  · rw [IsHermitian, conjTranspose_eq_transpose_of_trivial]
    simp only [lap, transpose_sub, diagonal_transpose, hA.eq]
  · rw [star_trivial]
    exact dotProduct_lap_nonneg A hA hw x

/-- One term of the signed energy is nonnegative: `|a|(x² + y²) − 2axy ≥ 0`. -/
private lemma signed_term_nonneg [CommRing R] [LinearOrder R] [IsStrictOrderedRing R]
    (a x y : R) : 0 ≤ |a| * (x ^ 2 + y ^ 2) - 2 * a * x * y := by
  rcases le_total 0 a with ha | ha
  · rw [abs_of_nonneg ha]; nlinarith [mul_nonneg ha (sq_nonneg (x - y))]
  · rw [abs_of_nonpos ha]; nlinarith [mul_nonneg (neg_nonneg.mpr ha) (sq_nonneg (x + y))]

/-- **LAP-2** for the signed Laplacian: `xᵀL̄x ≥ 0` for every symmetric `A`, of any sign. -/
theorem dotProduct_signedLap_nonneg [CommRing R] [LinearOrder R] [IsStrictOrderedRing R]
    (A : Matrix V V R) (hA : A.IsSymm) (x : V → R) :
    0 ≤ x ⬝ᵥ (signedLap A *ᵥ x) := by
  have row : x ⬝ᵥ (signedLap A *ᵥ x) = ∑ i, ∑ j, (|A i j| * x i ^ 2 - A i j * x i * x j) := by
    simp only [dotProduct, signedLap_mulVec_apply, mul_sum]
    exact sum_congr rfl fun i _ ↦ sum_congr rfl fun j _ ↦ by ring
  have split : ∑ i, ∑ j, (|A i j| * (x i ^ 2 + x j ^ 2) - 2 * A i j * x i * x j) =
      ∑ i, ∑ j, (|A i j| * x i ^ 2 - A i j * x i * x j) +
        ∑ i, ∑ j, (|A i j| * x j ^ 2 - A i j * x i * x j) := by
    rw [← sum_add_distrib]
    refine sum_congr rfl fun i _ ↦ ?_
    rw [← sum_add_distrib]
    exact sum_congr rfl fun j _ ↦ by ring
  have swap : ∑ i, ∑ j, (|A i j| * x j ^ 2 - A i j * x i * x j) =
      ∑ i, ∑ j, (|A i j| * x i ^ 2 - A i j * x i * x j) := by
    rw [sum_comm]
    exact sum_congr rfl fun i _ ↦ sum_congr rfl fun j _ ↦ by rw [hA.apply i j]; ring
  have energy : 2 * (x ⬝ᵥ (signedLap A *ᵥ x)) =
      ∑ i, ∑ j, (|A i j| * (x i ^ 2 + x j ^ 2) - 2 * A i j * x i * x j) := by
    rw [split, swap, row, two_mul]
  have : 0 ≤ ∑ i, ∑ j, (|A i j| * (x i ^ 2 + x j ^ 2) - 2 * A i j * x i * x j) :=
    sum_nonneg fun i _ ↦ sum_nonneg fun j _ ↦ signed_term_nonneg _ _ _
  linarith

/-- On a simple graph's 0/1 adjacency, `lap` is Mathlib's `lapMatrix`. -/
theorem lap_adjMatrix [Ring R] (G : SimpleGraph V) [DecidableRel G.Adj] :
    lap (G.adjMatrix R) = G.lapMatrix R := by
  have deg : degree (G.adjMatrix R) = fun i ↦ (G.degree i : R) := by
    funext i
    rw [degree, SimpleGraph.degree_eq_sum_if_adj (G := G) (R := R) i]
    simp [SimpleGraph.adjMatrix_apply]
  rw [lap, deg]
  rfl

/-- **LAP-2** on the binarized support: Mathlib's lemma, in one line. -/
theorem posSemidef_lap_adjMatrix (G : SimpleGraph V) [DecidableRel G.Adj] :
    (lap (G.adjMatrix ℝ)).PosSemidef := by
  rw [lap_adjMatrix]; exact G.posSemidef_lapMatrix ℝ

/-- **LAP-3** on the binarized support: `dim ker L` is the number of connected components
(Mathlib's lemma, in one line). -/
theorem card_components_eq_nullity_adjMatrix (G : SimpleGraph V) [DecidableRel G.Adj] :
    Fintype.card G.ConnectedComponent =
      Module.finrank ℝ (LinearMap.ker (lap (G.adjMatrix ℝ)).toLin') := by
  rw [lap_adjMatrix]; exact G.card_connectedComponent_eq_finrank_ker_toLin'_lapMatrix

/-- The support graph of a weight matrix: `i ~ j` iff `i ≠ j` and `Aᵢⱼ ≠ 0` or `Aⱼᵢ ≠ 0`. A
self-loop is no edge: its weight enters `D` and `A` alike and cancels in `L`. -/
def support [Zero R] (A : Matrix V V R) : SimpleGraph V :=
  SimpleGraph.fromRel fun i j ↦ A i j ≠ 0

/-- The house reduction behind weighted LAP-3 (dn-mathematical-foundations §2.4): for symmetric
nonnegative `A`, `L·x = 0` iff `x` takes one value across every edge of nonzero weight. -/
theorem lap_mulVec_eq_zero_iff [CommRing R] [LinearOrder R] [IsStrictOrderedRing R]
    (A : Matrix V V R) (hA : A.IsSymm) (hw : ∀ i j, 0 ≤ A i j) (x : V → R) :
    lap A *ᵥ x = 0 ↔ ∀ i j, A i j ≠ 0 → x i = x j := by
  constructor
  · intro h i j hij
    have e := two_mul_dotProduct_lap A hA x
    rw [h, dotProduct_zero, mul_zero] at e
    have row := (sum_eq_zero_iff_of_nonneg fun i _ ↦ sum_nonneg fun j _ ↦
      mul_nonneg (hw i j) (sq_nonneg (x i - x j))).1 e.symm i (mem_univ _)
    have term := (sum_eq_zero_iff_of_nonneg fun j _ ↦
      mul_nonneg (hw i j) (sq_nonneg (x i - x j))).1 row j (mem_univ _)
    rcases mul_eq_zero.1 term with h0 | h0
    · exact absurd h0 hij
    · exact sub_eq_zero.1 (pow_eq_zero_iff two_ne_zero |>.1 h0)
  · intro h
    ext i
    rw [lap_mulVec_apply, Pi.zero_apply]
    refine sum_eq_zero fun j _ ↦ ?_
    by_cases hij : A i j = 0
    · rw [hij, zero_mul]
    · rw [h i j hij, sub_self, mul_zero]

/-- **LAP-3** weighted: for symmetric `A` with nonnegative entries, `dim ker L` is the number of
connected components of the support graph. -/
theorem card_components_eq_nullity (A : Matrix V V ℝ) (hA : A.IsSymm) (hw : ∀ i j, 0 ≤ A i j)
    [DecidableRel (support A).Adj] :
    Fintype.card (support A).ConnectedComponent =
      Module.finrank ℝ (LinearMap.ker (lap A).toLin') := by
  have ker : LinearMap.ker (lap A).toLin' = LinearMap.ker ((support A).lapMatrix ℝ).toLin' := by
    ext x
    simp only [LinearMap.mem_ker, toLin'_apply]
    rw [lap_mulVec_eq_zero_iff A hA hw, SimpleGraph.lapMatrix_mulVec_eq_zero_iff_forall_adj]
    constructor
    · rintro h i j ⟨-, hij | hji⟩
      · exact h i j hij
      · exact (h j i hji).symm
    · intro h i j hij
      by_cases hne : i = j
      · rw [hne]
      · exact h i j ⟨hne, Or.inl hij⟩
  rw [ker]
  exact (support A).card_connectedComponent_eq_finrank_ker_toLin'_lapMatrix

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
