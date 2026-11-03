module

public import Mathlib.Combinatorics.SimpleGraph.LapMatrix

/-!
# The Laplacian family: LAP-1, LAP-2, LAP-3

Statements of the ledger's first Laplacian laws (dn-mathematical-foundations §2.2, seed table),
mirroring `core/kernel/complex/laplacian.py`. `A` is any square matrix over a ring; the Python
builds it from a sparse adjacency and allows self-loops, so nothing here assumes a zero diagonal.
-/

@[expose] public section

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
theorem signed_term_nonneg [CommRing R] [LinearOrder R] [IsStrictOrderedRing R]
    (a x y : R) : 0 ≤ |a| * (x ^ 2 + y ^ 2) - 2 * a * x * y := by
  rcases le_total 0 a with ha | ha
  · rw [abs_of_nonneg ha]; nlinarith [mul_nonneg ha (sq_nonneg (x - y))]
  · rw [abs_of_nonpos ha]; nlinarith [mul_nonneg (neg_nonneg.mpr ha) (sq_nonneg (x + y))]

/-- The signed energy identity: `2 xᵀL̄x = Σᵢⱼ (|Aᵢⱼ|(xᵢ² + xⱼ²) − 2 Aᵢⱼ xᵢ xⱼ)` for symmetric
`A`. -/
theorem two_mul_dotProduct_signedLap [CommRing R] [LinearOrder R]
    (A : Matrix V V R) (hA : A.IsSymm) (x : V → R) :
    2 * (x ⬝ᵥ (signedLap A *ᵥ x)) =
      ∑ i, ∑ j, (|A i j| * (x i ^ 2 + x j ^ 2) - 2 * A i j * x i * x j) := by
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
  rw [split, swap, row, two_mul]

/-- **LAP-2** for the signed Laplacian: `xᵀL̄x ≥ 0` for every symmetric `A`, of any sign. -/
theorem dotProduct_signedLap_nonneg [CommRing R] [LinearOrder R] [IsStrictOrderedRing R]
    (A : Matrix V V R) (hA : A.IsSymm) (x : V → R) :
    0 ≤ x ⬝ᵥ (signedLap A *ᵥ x) := by
  have energy := two_mul_dotProduct_signedLap A hA x
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

end Palace
