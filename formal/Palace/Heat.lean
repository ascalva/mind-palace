import Mathlib.Analysis.InnerProductSpace.PiL2
import Mathlib.Analysis.SpecialFunctions.Exp
import Palace.Spectral

/-!
# The heat kernel and the diffusion distance: CND-4

`core/graph/conductance.py`'s `_diffusion_distances` reads the heat kernel `H_t = e^{−tL}` of the
combinatorial Laplacian through `L = Σ λ_k φ_k φ_kᵀ`: the Gram matrix `G = Σ e^{−2tλ_k} φ_k φ_kᵀ`
and `d_t(i, j) = √(G_ii + G_jj − 2G_ij)`, CND-1's effective-resistance form applied to `G`. Here
`H_t` is the continuous functional calculus `cfc (e^{−t·}) L`, which agrees with the spectral
triple product (`Matrix.IsHermitian.cfc_eq`).

* `H_t` is symmetric, `H_0 = 1` and `H_{s+t} = H_s H_t`, so every `H_t` is invertible.
* The code's Gram matrix is `H_{2t} = H_t H_t`, and its `d_t(i, j)` is the Euclidean distance
  between the vertices' heat-kernel images `H_t eᵢ` and `H_t eⱼ`. So `d_t` is a metric on the
  vertices for every `t`: zero exactly on the diagonal, and finite and positive between vertices
  of different components, where effective resistance is `∞` (the regime split of CND-3).
* For symmetric `A ≥ 0` the distances shrink as `t` grows, since `e^{−2tλ}` decreases on the
  nonnegative spectrum.
-/

open Matrix

namespace Palace

variable {V : Type*} [Fintype V] [DecidableEq V]

/-- The heat kernel `e^{−tM}` of a real symmetric matrix, by the functional calculus. -/
noncomputable def heat (M : Matrix V V ℝ) (t : ℝ) : Matrix V V ℝ :=
  cfc (fun x ↦ Real.exp (-t * x)) M

/-- The vertex `i` seen from time `t`: column `i` of the heat kernel, `H_t eᵢ`, as a point of
Euclidean space. -/
noncomputable def heatPoint (M : Matrix V V ℝ) (t : ℝ) (i : V) : EuclideanSpace ℝ V :=
  WithLp.toLp 2 (heat M t *ᵥ Pi.single i 1)

/-- **CND-4** `_diffusion_distances`: `√(G_ii + G_jj − 2G_ij)` with `G = H_{2t}`. -/
noncomputable def diffusionDist (M : Matrix V V ℝ) (t : ℝ) (i j : V) : ℝ :=
  Real.sqrt (rEff (heat M (2 * t)) i j)

section Heat

variable {M : Matrix V V ℝ} (hM : M.IsHermitian)
include hM

/-- `H_0 = 1`. -/
theorem heat_zero : heat M 0 = 1 := by
  simp only [heat, neg_zero, zero_mul, Real.exp_zero]
  exact cfc_const_one ℝ M hM.isSelfAdjoint

omit hM in
/-- **CND-4** The semigroup law `H_{s+t} = H_s H_t`. -/
theorem heat_add (s t : ℝ) : heat M (s + t) = heat M s * heat M t := by
  rw [heat, heat, heat, ← cfc_mul (fun x ↦ Real.exp (-s * x)) (fun x ↦ Real.exp (-t * x)) M]
  congr 1
  funext x
  rw [← Real.exp_add]
  ring_nf

omit hM in
/-- `H_t` is symmetric. -/
theorem isHermitian_heat (t : ℝ) : (heat M t).IsHermitian :=
  cfc_predicate (fun x ↦ Real.exp (-t * x)) M

/-- `H_{−t}` inverts `H_t`. -/
theorem heat_neg_mul (t : ℝ) : heat M (-t) * heat M t = 1 := by
  rw [← heat_add, neg_add_cancel, heat_zero hM]

omit hM in
/-- The code's Gram matrix is `H_{2t} = H_t H_t`. -/
theorem heat_two_mul (t : ℝ) : heat M (2 * t) = heat M t * heat M t := by
  rw [two_mul, heat_add]

omit hM in
theorem heat_two_mul_apply (t : ℝ) (a b : V) :
    heat M (2 * t) a b = ∑ k, heat M t a k * heat M t k b := by
  rw [heat_two_mul]
  exact Matrix.mul_apply

omit hM in
/-- **CND-4** The code's distance is the Euclidean distance between the vertices' heat-kernel
images. -/
theorem diffusionDist_eq (t : ℝ) (i j : V) :
    diffusionDist M t i j = dist (heatPoint M t i) (heatPoint M t j) := by
  have hs : ∀ a b, heat M t a b = heat M t b a := fun a b ↦ by
    simpa using (isHermitian_heat (M := M) t).apply b a
  rw [EuclideanSpace.dist_eq, diffusionDist]
  congr 1
  simp only [rEff, heat_two_mul_apply, heatPoint, Real.dist_eq, sq_abs]
  simp only [mulVec_single_one, col_apply]
  rw [Finset.mul_sum, ← Finset.sum_add_distrib, ← Finset.sum_sub_distrib]
  refine Finset.sum_congr rfl fun k _ ↦ ?_
  rw [hs i k, hs j k]
  ring

omit hM in
/-- **CND-4** `d_t` vanishes on the diagonal. -/
theorem diffusionDist_self (t : ℝ) (i : V) : diffusionDist M t i i = 0 := by
  rw [diffusionDist_eq]
  exact dist_self _

omit hM in
/-- **CND-4** `d_t` is symmetric. -/
theorem diffusionDist_comm (t : ℝ) (i j : V) : diffusionDist M t i j = diffusionDist M t j i := by
  rw [diffusionDist_eq, diffusionDist_eq, dist_comm]

omit hM in
/-- **CND-4** `d_t` satisfies the triangle inequality. -/
theorem diffusionDist_triangle (t : ℝ) (i j k : V) :
    diffusionDist M t i k ≤ diffusionDist M t i j + diffusionDist M t j k := by
  simp only [diffusionDist_eq]
  exact dist_triangle _ _ _

/-- **CND-4** `d_t` separates every two vertices, for every `t`, also across components: `H_t` is
invertible. -/
theorem diffusionDist_eq_zero_iff (t : ℝ) (i j : V) : diffusionDist M t i j = 0 ↔ i = j := by
  rw [diffusionDist_eq, dist_eq_zero]
  refine ⟨fun h ↦ ?_, fun h ↦ h ▸ rfl⟩
  have h1 : heat M t *ᵥ Pi.single i 1 = heat M t *ᵥ Pi.single j 1 :=
    congrArg WithLp.ofLp h
  have h2 := congrArg (heat M (-t) *ᵥ ·) h1
  simp only [mulVec_mulVec, heat_neg_mul hM, one_mulVec] at h2
  by_contra hij
  simpa [Pi.single_apply, hij] using congrFun h2 i

end Heat

/-- A function of the spectrum that is nonnegative on it gives a positive semidefinite matrix. -/
theorem posSemidef_cfc {M : Matrix V V ℝ} (hM : M.IsHermitian) {f : ℝ → ℝ}
    (hf : ∀ i, 0 ≤ f (hM.eigenvalues i)) : (cfc f M).PosSemidef := by
  rw [hM.cfc_eq, IsHermitian.cfc, Unitary.conjStarAlgAut_apply, star_eq_conjTranspose]
  exact PosSemidef.mul_mul_conjTranspose_same
    (posSemidef_diagonal_iff.2 fun i ↦ by simpa using hf i) _

/-- **CND-4** For the combinatorial Laplacian (symmetric `A ≥ 0`) diffusion distances shrink as
`t` grows: `e^{−2tλ}` decreases on the nonnegative spectrum. -/
theorem diffusionDist_antitone (A : Matrix V V ℝ) (hA : A.IsSymm) (hw : ∀ i j, 0 ≤ A i j)
    {t t' : ℝ} (htt : t ≤ t') (i j : V) :
    diffusionDist (lap A) t' i j ≤ diffusionDist (lap A) t i j := by
  have hL := posSemidef_lap A hA hw
  have hP : (heat (lap A) (2 * t) - heat (lap A) (2 * t')).PosSemidef := by
    rw [heat, heat,
      ← cfc_sub (fun x ↦ Real.exp (-(2 * t) * x)) (fun x ↦ Real.exp (-(2 * t') * x))]
    refine posSemidef_cfc hL.isHermitian fun k ↦ ?_
    have := hL.eigenvalues_nonneg k
    simp only [sub_nonneg]
    exact Real.exp_le_exp.2 (by nlinarith)
  have h := hP.dotProduct_mulVec_nonneg (Pi.single i 1 - Pi.single j 1)
  have hs : ∀ s : ℝ, heat (lap A) s j i = heat (lap A) s i j := fun s ↦ by
    simpa using (isHermitian_heat (M := lap A) s).apply i j
  simp only [star_trivial, mulVec_sub, mulVec_single_one, dotProduct_sub, sub_dotProduct,
    single_dotProduct, col_apply, one_mul, Matrix.sub_apply] at h
  refine Real.sqrt_le_sqrt ?_
  simp only [rEff]
  linarith [hs (2 * t), hs (2 * t')]

/-! ## Attacks

`H_t` has no executable form (it needs `exp` of a matrix), so CND-4 is attacked where it is
exact, over ℚ on `Fin 4`: the identity that makes `d_t` a Euclidean distance holds for the square
of any symmetric matrix, and the Gram form `√(G_ii + G_jj − 2G_ij)` satisfies the triangle
inequality for any positive semidefinite `G` (checked squared, without roots). Each control drops
the hypothesis the law needs and must be refuted.
-/

namespace Attack

/-- A random matrix on `Fin 4`, entries read off a list. -/
def mat (xs : List ℤ) : Matrix (Fin 4) (Fin 4) ℚ := fun i j ↦ xs.getD (4 * i.val + j.val) 0

/-- `d_t² = ‖H eᵢ − H eⱼ‖²` with `G = H H`, on every pair. -/
def gramIdentity (H : Matrix (Fin 4) (Fin 4) ℚ) : Bool :=
  let G := H * H
  (List.finRange 4).all fun i ↦ (List.finRange 4).all fun j ↦
    decide (G i i + G j j - 2 * G i j = ∑ k, (H k i - H k j) ^ 2)

/- CND-4: the Gram distance of `H²` is the Euclidean distance of `H`'s columns, for symmetric
`H`. -/
#eval survives (∀ xs : List ℤ, gramIdentity (mat xs + (mat xs).transpose) = true) 111

/- Control, `H` not symmetric. -/
#eval refuted (∀ xs : List ℤ, gramIdentity (mat xs) = true) 112

/-- The squared Gram distance `G_ii + G_jj − 2G_ij`, over ℚ. -/
def gramSq (G : Matrix (Fin 4) (Fin 4) ℚ) (i j : Fin 4) : ℚ := G i i + G j j - 2 * G i j

/-- The triangle inequality of `√(gramSq G)` on every triple, squared: with `a`, `b`, `x` the
squared sides, `a ≥ 0` and `x ≤ (√a + √b)²`, that is `x − a − b ≤ 0` or `(x − a − b)² ≤ 4ab`. -/
def gramTriangle (G : Matrix (Fin 4) (Fin 4) ℚ) : Bool :=
  (List.finRange 4).all fun i ↦ (List.finRange 4).all fun j ↦ (List.finRange 4).all fun k ↦
    let a := gramSq G i j
    let b := gramSq G j k
    let x := gramSq G i k
    decide (0 ≤ a ∧ (x - a - b ≤ 0 ∨ (x - a - b) ^ 2 ≤ 4 * a * b))

/- CND-4: the Gram distance is a metric for positive semidefinite `G = BᵀB`. -/
#eval survives (∀ xs : List ℤ, gramTriangle ((mat xs).transpose * mat xs) = true) 113

/- Control, `G` symmetric but indefinite. -/
#eval refuted (∀ xs : List ℤ, gramTriangle (mat xs + (mat xs).transpose) = true) 114

end Attack

end Palace
