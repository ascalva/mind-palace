import Mathlib.Analysis.Matrix.HermitianFunctionalCalculus
import Mathlib.Analysis.Matrix.PosDef
import Mathlib.Analysis.Real.Sqrt
import Mathlib.Testing.Plausible.Sampleable
import Palace.Laplacian

/-!
# The normalized Laplacian and the pseudo-inverse: LAP-4, L_sym PSD, L⁺

`L_sym = I − D^{-1/2} A D^{-1/2}` with the convention `D^{-1/2} := 0` at degree 0
(`core/kernel/complex/laplacian.py`, `laplacian_sym`), and the Moore–Penrose pseudo-inverse `L⁺`
that `core/graph/conductance.py` takes with `np.linalg.pinv` for effective resistance (CND-1).
-/

open Matrix Finset Unitary

namespace Palace

variable {V R : Type*} [Fintype V] [DecidableEq V]

/-! ### The scaled identity, over any commutative ring -/

/-- The reduction behind LAP-4: for any scaling `s`, the form of `I − S A S` (with `S = diag s`)
is a diagonal remainder plus the form of `L` at `s ∘ x`. -/
theorem dotProduct_one_sub_scaled [CommRing R] (A : Matrix V V R) (s x : V → R) :
    x ⬝ᵥ ((1 - diagonal s * A * diagonal s) *ᵥ x) =
      ∑ i, (1 - s i ^ 2 * degree A i) * x i ^ 2 + (s * x) ⬝ᵥ (lap A *ᵥ (s * x)) := by
  have hS (v : V → R) : diagonal s *ᵥ v = s * v := funext fun i ↦ mulVec_diagonal s v i
  rw [sub_mulVec, one_mulVec, ← mulVec_mulVec, ← mulVec_mulVec, hS, hS, lap, sub_mulVec]
  simp only [dotProduct, Pi.sub_apply, Pi.mul_apply, mulVec_diagonal, ← sum_add_distrib]
  exact sum_congr rfl fun i _ ↦ by ring

/-- The signless Laplacian `Q = D + A`, the partner that bounds `L_sym` from above. -/
def signless [Ring R] (A : Matrix V V R) : Matrix V V R := diagonal (degree A) + A

/-- Row `i` of `Q·x` is `Σⱼ Aᵢⱼ (xᵢ + xⱼ)`. -/
theorem signless_mulVec_apply [CommRing R] (A : Matrix V V R) (x : V → R) (i : V) :
    (signless A *ᵥ x) i = ∑ j, A i j * (x i + x j) := by
  rw [signless, add_mulVec, Pi.add_apply, mulVec_diagonal, degree, sum_mul]
  simp only [mulVec, dotProduct]
  rw [← sum_add_distrib]
  exact sum_congr rfl fun j _ ↦ by ring

/-- `2 xᵀQx = Σᵢⱼ Aᵢⱼ (xᵢ + xⱼ)²` for symmetric `A`. -/
theorem two_mul_dotProduct_signless [CommRing R] (A : Matrix V V R) (hA : A.IsSymm)
    (x : V → R) : 2 * (x ⬝ᵥ (signless A *ᵥ x)) = ∑ i, ∑ j, A i j * (x i + x j) ^ 2 := by
  have row : x ⬝ᵥ (signless A *ᵥ x) = ∑ i, ∑ j, A i j * (x i * (x i + x j)) := by
    simp only [dotProduct, signless_mulVec_apply, mul_sum]
    exact sum_congr rfl fun i _ ↦ sum_congr rfl fun j _ ↦ by ring
  have swap : ∑ i, ∑ j, A i j * (x j * (x j + x i)) = ∑ i, ∑ j, A i j * (x i * (x i + x j)) := by
    rw [sum_comm]
    exact sum_congr rfl fun i _ ↦ sum_congr rfl fun j _ ↦ by rw [hA.apply i j]
  rw [row, two_mul]
  nth_rewrite 2 [← swap]
  rw [← sum_add_distrib]
  refine sum_congr rfl fun i _ ↦ ?_
  rw [← sum_add_distrib]
  exact sum_congr rfl fun j _ ↦ by ring

/-- `xᵀQx ≥ 0` for symmetric `A` with nonnegative entries. -/
theorem dotProduct_signless_nonneg [CommRing R] [LinearOrder R] [IsStrictOrderedRing R]
    (A : Matrix V V R) (hA : A.IsSymm) (hw : ∀ i j, 0 ≤ A i j) (x : V → R) :
    0 ≤ x ⬝ᵥ (signless A *ᵥ x) := by
  have h := two_mul_dotProduct_signless A hA x
  have : 0 ≤ ∑ i, ∑ j, A i j * (x i + x j) ^ 2 :=
    sum_nonneg fun i _ ↦ sum_nonneg fun j _ ↦ mul_nonneg (hw i j) (sq_nonneg _)
  linarith

/-- The upper partner of the scaled identity: the form of `I + S A S` is the same diagonal
remainder plus the form of `Q` at `s ∘ x`. -/
theorem dotProduct_one_add_scaled [CommRing R] (A : Matrix V V R) (s x : V → R) :
    x ⬝ᵥ ((1 + diagonal s * A * diagonal s) *ᵥ x) =
      ∑ i, (1 - s i ^ 2 * degree A i) * x i ^ 2 + (s * x) ⬝ᵥ (signless A *ᵥ (s * x)) := by
  have hS (v : V → R) : diagonal s *ᵥ v = s * v := funext fun i ↦ mulVec_diagonal s v i
  rw [add_mulVec, one_mulVec, ← mulVec_mulVec, ← mulVec_mulVec, hS, hS, signless, add_mulVec]
  simp only [dotProduct, Pi.add_apply, Pi.mul_apply, mulVec_diagonal, ← sum_add_distrib]
  exact sum_congr rfl fun i _ ↦ by ring

/-! ### `L_sym` -/

/-- `D^{-1/2}`, with `0` at degree `0`: `np.where(d > 0, 1/√d, 0)` in `laplacian_sym`. -/
noncomputable def invSqrtDegree (A : Matrix V V ℝ) (i : V) : ℝ :=
  if 0 < degree A i then (√(degree A i))⁻¹ else 0

/-- The normalized Laplacian `L_sym = I − D^{-1/2} A D^{-1/2}` (`laplacian.py`, `laplacian_sym`). -/
noncomputable def lapSym (A : Matrix V V ℝ) : Matrix V V ℝ :=
  1 - diagonal (invSqrtDegree A) * A * diagonal (invSqrtDegree A)

omit [DecidableEq V] in
/-- The diagonal remainder at `D^{-1/2}`: `0` where the degree is positive, `1` where it is not. -/
theorem one_sub_invSqrtDegree_sq (A : Matrix V V ℝ) (i : V) :
    1 - invSqrtDegree A i ^ 2 * degree A i = if 0 < degree A i then 0 else 1 := by
  unfold invSqrtDegree
  split_ifs with h
  · rw [inv_pow, Real.sq_sqrt h.le, inv_mul_cancel₀ h.ne', sub_self]
  · simp

omit [DecidableEq V] in
theorem remainder_nonneg (A : Matrix V V ℝ) (i : V) :
    0 ≤ 1 - invSqrtDegree A i ^ 2 * degree A i := by
  rw [one_sub_invSqrtDegree_sq]; split_ifs <;> norm_num

/-- **L_sym PSD** `xᵀL_sym x ≥ 0` for symmetric `A` with nonnegative entries. -/
theorem dotProduct_lapSym_nonneg (A : Matrix V V ℝ) (hA : A.IsSymm) (hw : ∀ i j, 0 ≤ A i j)
    (x : V → ℝ) : 0 ≤ x ⬝ᵥ (lapSym A *ᵥ x) := by
  rw [lapSym, dotProduct_one_sub_scaled]
  have h1 : 0 ≤ ∑ i, (1 - invSqrtDegree A i ^ 2 * degree A i) * x i ^ 2 :=
    sum_nonneg fun i _ ↦ mul_nonneg (remainder_nonneg A i) (sq_nonneg _)
  have h2 := dotProduct_lap_nonneg A hA hw (invSqrtDegree A * x)
  linarith

/-- **L_sym PSD** as a matrix statement. -/
theorem posSemidef_lapSym (A : Matrix V V ℝ) (hA : A.IsSymm) (hw : ∀ i j, 0 ≤ A i j) :
    (lapSym A).PosSemidef := by
  refine .of_dotProduct_mulVec_nonneg ?_ fun x ↦ ?_
  · rw [IsHermitian, conjTranspose_eq_transpose_of_trivial]
    simp only [lapSym, transpose_sub, transpose_one, transpose_mul, diagonal_transpose, hA.eq,
      Matrix.mul_assoc]
  · rw [star_trivial]
    exact dotProduct_lapSym_nonneg A hA hw x

/-- The upper half of LAP-4: `xᵀL_sym x ≤ 2 xᵀx`. -/
theorem dotProduct_lapSym_le (A : Matrix V V ℝ) (hA : A.IsSymm) (hw : ∀ i j, 0 ≤ A i j)
    (x : V → ℝ) : x ⬝ᵥ (lapSym A *ᵥ x) ≤ 2 * (x ⬝ᵥ x) := by
  have up := dotProduct_one_add_scaled A (invSqrtDegree A) x
  have h1 : 0 ≤ ∑ i, (1 - invSqrtDegree A i ^ 2 * degree A i) * x i ^ 2 :=
    sum_nonneg fun i _ ↦ mul_nonneg (remainder_nonneg A i) (sq_nonneg _)
  have h2 := dotProduct_signless_nonneg A hA hw (invSqrtDegree A * x)
  rw [add_mulVec, one_mulVec, dotProduct_add] at up
  rw [lapSym, sub_mulVec, one_mulVec, dotProduct_sub]
  linarith

/-- **LAP-4** `Spec(L_sym) ⊆ [0, 2]`, for symmetric `A` with nonnegative entries: every eigenvalue
of the real symmetric `L_sym` has a real eigenvector, and lies in `[0, 2]`. -/
theorem lapSym_eigenvalue_mem_Icc (A : Matrix V V ℝ) (hA : A.IsSymm) (hw : ∀ i j, 0 ≤ A i j)
    {μ : ℝ} {x : V → ℝ} (hx : x ≠ 0) (h : lapSym A *ᵥ x = μ • x) : μ ∈ Set.Icc 0 2 := by
  have hxx : 0 < x ⬝ᵥ x := by
    refine lt_of_le_of_ne (sum_nonneg fun i _ ↦ mul_self_nonneg (x i)) (Ne.symm ?_)
    exact fun h0 ↦ hx (dotProduct_self_eq_zero.1 h0)
  have lo := dotProduct_lapSym_nonneg A hA hw x
  have hi := dotProduct_lapSym_le A hA hw x
  rw [h, dotProduct_smul, smul_eq_mul] at lo hi
  constructor <;> nlinarith

/-- **LAP-4** The convention `D^{-1/2} := 0` at degree 0, pointwise: an isolated vertex's row of
`L_sym` is the identity row, so its indicator is an eigenvector of eigenvalue `1`, not `0`. -/
theorem lapSym_mulVec_single_of_degree_eq_zero (A : Matrix V V ℝ) {i : V}
    (hi : degree A i = 0) : lapSym A *ᵥ Pi.single i 1 = Pi.single i 1 := by
  ext j
  have hs : invSqrtDegree A i = 0 := by simp [invSqrtDegree, hi]
  simp [lapSym, mul_diagonal, diagonal_mul, hs, Pi.single_apply, Matrix.one_apply, eq_comm]

/-- **L_sym** The correction the note makes: `L_sym` does not annihilate `1`, it annihilates
`D^{1/2}·1` (symmetric `A` with nonnegative entries). -/
theorem lapSym_mulVec_sqrt_degree (A : Matrix V V ℝ) (hA : A.IsSymm) (hw : ∀ i j, 0 ≤ A i j) :
    lapSym A *ᵥ (fun i ↦ √(degree A i)) = 0 := by
  have hS (v : V → ℝ) : diagonal (invSqrtDegree A) *ᵥ v = invSqrtDegree A * v :=
    funext fun i ↦ mulVec_diagonal _ v i
  have ind : invSqrtDegree A * (fun i ↦ √(degree A i)) =
      fun j ↦ if 0 < degree A j then 1 else 0 := by
    funext j
    simp only [Pi.mul_apply, invSqrtDegree]
    split_ifs with h
    · exact inv_mul_cancel₀ (Real.sqrt_pos.2 h).ne'
    · exact zero_mul _
  have row (i : V) : (A *ᵥ fun j ↦ if 0 < degree A j then (1 : ℝ) else 0) i = degree A i := by
    have term (j : V) : A i j * (if 0 < degree A j then (1 : ℝ) else 0) = A i j := by
      by_cases h : 0 < degree A j
      · rw [ite_eq_left h, mul_one]
      · have hdj : degree A j = 0 := le_antisymm (not_lt.1 h) (sum_nonneg fun k _ ↦ hw j k)
        have hji := (sum_eq_zero_iff_of_nonneg fun k _ ↦ hw j k).1 hdj i (mem_univ _)
        have hij : A i j = 0 := by rw [← hA.apply i j]; exact hji
        rw [ite_eq_right h, mul_zero, hij]
    simp only [mulVec, dotProduct, term]
    rfl
  ext i
  rw [lapSym, sub_mulVec, one_mulVec, ← mulVec_mulVec, ← mulVec_mulVec, hS, hS, ind,
    Pi.sub_apply, Pi.mul_apply, row, Pi.zero_apply]
  unfold invSqrtDegree
  split_ifs with h
  · have e : (√(degree A i))⁻¹ * degree A i = √(degree A i) := by
      rw [inv_mul_eq_div, div_eq_iff (Real.sqrt_pos.2 h).ne', Real.mul_self_sqrt h.le]
    rw [e, sub_self]
  · have h0 : degree A i = 0 := le_antisymm (not_lt.1 h) (sum_nonneg fun k _ ↦ hw i k)
    simp [h0]

/-! ### `L⁺` -/

/-- `L` is Hermitian whenever `A` is symmetric (over ℝ, Hermitian is symmetric). -/
theorem isHermitian_lap (A : Matrix V V ℝ) (hA : A.IsSymm) : (lap A).IsHermitian := by
  rw [IsHermitian, conjTranspose_eq_transpose_of_trivial]
  simp only [lap, transpose_sub, diagonal_transpose, hA.eq]

/-- The Moore–Penrose pseudo-inverse of a real symmetric matrix, through its spectral
decomposition: `M = U diag(λ) Uᵀ` gives `M⁺ = U diag(λ⁻¹) Uᵀ`, and Lean's `0⁻¹ = 0` is the
pseudo-inverse's own convention on the kernel. -/
noncomputable def pinv (M : Matrix V V ℝ) (hM : M.IsHermitian) : Matrix V V ℝ := hM.cfc (·⁻¹)

section Pinv

variable {M : Matrix V V ℝ} (hM : M.IsHermitian)

/-- Both `M` and `M⁺` are images of diagonal matrices under one conjugation. -/
private theorem pinv_conj :
    M = conjStarAlgAut ℝ _ hM.eigenvectorUnitary (diagonal (RCLike.ofReal ∘ hM.eigenvalues)) ∧
      pinv M hM = conjStarAlgAut ℝ _ hM.eigenvectorUnitary
        (diagonal (RCLike.ofReal ∘ (·⁻¹) ∘ hM.eigenvalues)) :=
  ⟨hM.spectral_theorem, rfl⟩

/-- **L⁺** Penrose's first equation, `M M⁺ M = M`. -/
theorem mul_pinv_mul : M * pinv M hM * M = M := by
  obtain ⟨e, hp⟩ := pinv_conj hM
  set c := conjStarAlgAut ℝ (Matrix V V ℝ) hM.eigenvectorUnitary
  calc M * pinv M hM * M
      = c (diagonal (RCLike.ofReal ∘ hM.eigenvalues)) *
          c (diagonal (RCLike.ofReal ∘ (·⁻¹) ∘ hM.eigenvalues)) *
          c (diagonal (RCLike.ofReal ∘ hM.eigenvalues)) := by rw [hp, ← e]
    _ = c (diagonal (RCLike.ofReal ∘ hM.eigenvalues)) := by
      rw [← map_mul, ← map_mul, diagonal_mul_diagonal, diagonal_mul_diagonal]
      congr 2
      funext i
      simp [mul_inv_mul_cancel]
    _ = M := e.symm

/-- **L⁺** Penrose's second equation, `M⁺ M M⁺ = M⁺`. -/
theorem pinv_mul_pinv : pinv M hM * M * pinv M hM = pinv M hM := by
  obtain ⟨e, hp⟩ := pinv_conj hM
  set c := conjStarAlgAut ℝ (Matrix V V ℝ) hM.eigenvectorUnitary
  calc pinv M hM * M * pinv M hM
      = c (diagonal (RCLike.ofReal ∘ (·⁻¹) ∘ hM.eigenvalues)) *
          c (diagonal (RCLike.ofReal ∘ hM.eigenvalues)) *
          c (diagonal (RCLike.ofReal ∘ (·⁻¹) ∘ hM.eigenvalues)) := by rw [hp, ← e]
    _ = c (diagonal (RCLike.ofReal ∘ (·⁻¹) ∘ hM.eigenvalues)) := by
      rw [← map_mul, ← map_mul, diagonal_mul_diagonal, diagonal_mul_diagonal]
      congr 2
      funext i
      simpa using mul_inv_mul_cancel (hM.eigenvalues i)⁻¹
    _ = pinv M hM := hp.symm

/-- **L⁺** `M` and `M⁺` commute, so with both symmetric, Penrose's last two equations hold. -/
theorem mul_pinv_comm : M * pinv M hM = pinv M hM * M := by
  obtain ⟨e, hp⟩ := pinv_conj hM
  set c := conjStarAlgAut ℝ (Matrix V V ℝ) hM.eigenvectorUnitary
  calc M * pinv M hM
      = c (diagonal (RCLike.ofReal ∘ hM.eigenvalues)) *
          c (diagonal (RCLike.ofReal ∘ (·⁻¹) ∘ hM.eigenvalues)) := by rw [hp, ← e]
    _ = c (diagonal (RCLike.ofReal ∘ (·⁻¹) ∘ hM.eigenvalues)) *
          c (diagonal (RCLike.ofReal ∘ hM.eigenvalues)) := by
      rw [← map_mul, ← map_mul, diagonal_mul_diagonal, diagonal_mul_diagonal]
      congr 2
      funext i
      exact mul_comm _ _
    _ = pinv M hM * M := by rw [hp, ← e]

/-- `M⁺` is symmetric. -/
theorem isHermitian_pinv : (pinv M hM).IsHermitian := by
  rw [IsHermitian, ← star_eq_conjTranspose, (pinv_conj hM).2, ← map_star, star_eq_conjTranspose,
    diagonal_conjTranspose]
  simp

/-- `M⁺` is positive semidefinite when `M` is. -/
theorem posSemidef_pinv (h : M.PosSemidef) : (pinv M h.isHermitian).PosSemidef := by
  rw [(pinv_conj h.isHermitian).2, conjStarAlgAut_apply, star_eq_conjTranspose]
  refine PosSemidef.mul_mul_conjTranspose_same (posSemidef_diagonal_iff.2 fun i ↦ ?_) _
  simpa using inv_nonneg.2 (h.eigenvalues_nonneg i)

end Pinv

/-- `L⁺`, the pseudo-inverse of the Laplacian (`conductance.py`: `np.linalg.pinv(L)`). -/
noncomputable def lapPinv (A : Matrix V V ℝ) (hA : A.IsSymm) : Matrix V V ℝ :=
  pinv (lap A) (isHermitian_lap A hA)

/-- **L⁺** is symmetric. -/
theorem isHermitian_lapPinv (A : Matrix V V ℝ) (hA : A.IsSymm) : (lapPinv A hA).IsHermitian :=
  isHermitian_pinv _

/-- **L⁺** is positive semidefinite, for symmetric `A` with nonnegative entries. -/
theorem posSemidef_lapPinv (A : Matrix V V ℝ) (hA : A.IsSymm) (hw : ∀ i j, 0 ≤ A i j) :
    (lapPinv A hA).PosSemidef :=
  posSemidef_pinv (posSemidef_lap A hA hw)

/-- CND-1's effective resistance read off a matrix `X`: `X i i + X j j − 2 X i j`. -/
def rEff (X : Matrix V V ℝ) (i j : V) : ℝ := X i i + X j j - 2 * X i j

/-- **CND-1** On `L⁺` (symmetric `A`, nonnegative entries) the effective resistance is a value of
its quadratic form, `(eᵢ − eⱼ)ᵀ L⁺ (eᵢ − eⱼ)`, so it is never negative. -/
theorem rEff_lapPinv_nonneg (A : Matrix V V ℝ) (hA : A.IsSymm) (hw : ∀ i j, 0 ≤ A i j)
    (i j : V) : 0 ≤ rEff (lapPinv A hA) i j := by
  set X := lapPinv A hA
  have hX := posSemidef_lapPinv A hA hw
  have h := hX.dotProduct_mulVec_nonneg (Pi.single i 1 - Pi.single j 1)
  have hs : X j i = X i j := by simpa using hX.isHermitian.apply i j
  simp only [star_trivial, mulVec_sub, mulVec_single_one, dotProduct_sub, sub_dotProduct,
    single_dotProduct, col_apply, one_mul] at h
  rw [rEff]
  linarith

/-! ## Attacks

`L_sym` and `L⁺` have no executable form here: one needs square roots, the other a spectral
decomposition over ℝ. Their laws are attacked where they are exact. `L_sym`'s rest on two
identities over any commutative ring, attacked over ℚ on `Fin 5` with arbitrary weights, scalings
and vectors. `L⁺`'s are attacked on an exact shadow: for a rational Laplacian with nonnegative
weights, `(L + P)⁻¹ − P` with `P` the orthogonal projector onto the component indicators. The
attack checks all four Penrose equations on it, so whenever it passes, the shadow is the
Moore–Penrose inverse itself.
-/

namespace Attack

/-- A 5 × 5 rational matrix stored as rows, for the shadow: every entry is computed once. -/
abbrev Rows := Array (Array ℚ)

/-- Store a matrix's entries. -/
def rows (M : Matrix (Fin 5) (Fin 5) ℚ) : Rows :=
  Array.ofFn fun i : Fin 5 ↦ Array.ofFn fun j : Fin 5 ↦ M i j

/-- Read an entry. -/
def entry (t : Rows) (i j : ℕ) : ℚ := (t[i]!)[j]!

/-- Entrywise sum on stored rows. -/
def addR (x y : Rows) : Rows := Array.ofFn fun i : Fin 5 ↦ Array.ofFn fun j : Fin 5 ↦
  entry x i j + entry y i j

/-- Entrywise difference on stored rows. -/
def subR (x y : Rows) : Rows := Array.ofFn fun i : Fin 5 ↦ Array.ofFn fun j : Fin 5 ↦
  entry x i j - entry y i j

/-- Transpose on stored rows. -/
def transR (x : Rows) : Rows := Array.ofFn fun i : Fin 5 ↦ Array.ofFn fun j : Fin 5 ↦ entry x j i

/-- The matrix product on stored rows. -/
def mulR (x y : Rows) : Rows := Array.ofFn fun i : Fin 5 ↦ Array.ofFn fun j : Fin 5 ↦
  ∑ k : Fin 5, entry x i k * entry y k j

/-- Gauss–Jordan elimination with row swaps: the inverse, or `none` when singular. -/
def invR (m : Rows) : Option Rows := Id.run do
  let mut a := m
  let mut b := rows 1
  for c in List.range 5 do
    let some r := (List.range 5).find? (fun r ↦ decide (c ≤ r) && entry a r c != 0)
      | return none
    let (ar, ac, br, bc) := (a[r]!, a[c]!, b[r]!, b[c]!)
    a := (a.setIfInBounds c ar).setIfInBounds r ac
    b := (b.setIfInBounds c br).setIfInBounds r bc
    let p := entry a c c
    a := a.setIfInBounds c (a[c]!.map (· / p))
    b := b.setIfInBounds c (b[c]!.map (· / p))
    for r' in List.range 5 do
      if r' != c then
        let f := entry a r' c
        a := a.setIfInBounds r' (Array.ofFn fun j : Fin 5 ↦ entry a r' j - f * entry a c j)
        b := b.setIfInBounds r' (Array.ofFn fun j : Fin 5 ↦ entry b r' j - f * entry b c j)
  return some b

/-- Warshall's closure: `j` is reachable from `i` along edges of nonzero weight. -/
def reach (A : Matrix (Fin 5) (Fin 5) ℚ) : Array (Array Bool) := Id.run do
  let mut r : Array (Array Bool) :=
    Array.ofFn fun i : Fin 5 ↦ Array.ofFn fun j : Fin 5 ↦ decide (i = j) || A i j != 0
  for k in List.range 5 do
    r := Array.ofFn fun i : Fin 5 ↦ Array.ofFn fun j : Fin 5 ↦
      (r[i.val]!)[j.val]! || ((r[i.val]!)[k]! && (r[k]!)[j.val]!)
  return r

/-- The orthogonal projector onto the component indicators: `1/|C|` on each component's block. -/
def projR (A : Matrix (Fin 5) (Fin 5) ℚ) : Rows :=
  let r := reach A
  Array.ofFn fun i : Fin 5 ↦ Array.ofFn fun j : Fin 5 ↦
    if (r[i.val]!)[j.val]! then 1 / ((r[i.val]!).count true : ℚ) else 0

/-- The laws of `L⁺` on the shadow `(L + P)⁻¹ − P`: the four Penrose equations (`L` and the shadow
commute and both are symmetric), `xᵀL⁺x ≥ 0`, and `R_eff ≥ 0` for every pair. -/
def pinvLaws (A : Matrix (Fin 5) (Fin 5) ℚ) (x : Fin 5 → ℚ) : Bool :=
  let L := rows (lap A)
  let P := projR A
  match invR (addR L P) with
  | none => false
  | some Y =>
    let X := subR Y P
    mulR (mulR L X) L == L && mulR (mulR X L) X == X && mulR L X == mulR X L &&
      transR X == X && decide (0 ≤ ∑ i : Fin 5, x i * ∑ j : Fin 5, entry X i j * x j) &&
      (List.range 5).all fun i ↦ (List.range 5).all fun j ↦
        decide (0 ≤ entry X i i + entry X j j - 2 * entry X i j)

/-- The connected-graph formula `L⁺ = (L + J/n)⁻¹ − J/n`, checked against Penrose's first two
equations on any graph. -/
def connectedFormulaLaws (A : Matrix (Fin 5) (Fin 5) ℚ) : Bool :=
  let L := rows (lap A)
  let J : Rows := Array.ofFn fun _ : Fin 5 ↦ Array.ofFn fun _ : Fin 5 ↦ (1 / 5 : ℚ)
  match invR (addR L J) with
  | none => false
  | some Y =>
    let X := subR Y J
    mulR (mulR L X) L == L && mulR (mulR X L) X == X

/- `L_sym`'s lower identity, for every `A`, scaling `s` and vector `x`. -/
#eval survives (∀ es : List (Fin 5 × Fin 5 × ℤ), ∀ ss xs : List ℤ,
  vec xs ⬝ᵥ ((1 - diagonal (vec ss) * ofArcs es * diagonal (vec ss)) *ᵥ vec xs) =
    ∑ i, (1 - vec ss i ^ 2 * degree (ofArcs es) i) * vec xs i ^ 2 +
      (vec ss * vec xs) ⬝ᵥ (lap (ofArcs es) *ᵥ (vec ss * vec xs))) 41

/- Control: the identity without its diagonal remainder. -/
#eval refuted (∀ es : List (Fin 5 × Fin 5 × ℤ), ∀ ss xs : List ℤ,
  vec xs ⬝ᵥ ((1 - diagonal (vec ss) * ofArcs es * diagonal (vec ss)) *ᵥ vec xs) =
    (vec ss * vec xs) ⬝ᵥ (lap (ofArcs es) *ᵥ (vec ss * vec xs))) 42

/- `L_sym`'s upper identity, through the signless Laplacian. -/
#eval survives (∀ es : List (Fin 5 × Fin 5 × ℤ), ∀ ss xs : List ℤ,
  vec xs ⬝ᵥ ((1 + diagonal (vec ss) * ofArcs es * diagonal (vec ss)) *ᵥ vec xs) =
    ∑ i, (1 - vec ss i ^ 2 * degree (ofArcs es) i) * vec xs i ^ 2 +
      (vec ss * vec xs) ⬝ᵥ (signless (ofArcs es) *ᵥ (vec ss * vec xs))) 43

/- The signless Laplacian is positive semidefinite on symmetric nonnegative weights. -/
#eval survives (∀ es : List (Fin 5 × Fin 5 × ℕ), ∀ xs : List ℤ,
  0 ≤ vec xs ⬝ᵥ (signless (ofEdges (nonneg es)) *ᵥ vec xs)) 44

/- Control: weights of either sign. -/
#eval refuted (∀ es : List (Fin 5 × Fin 5 × ℤ), ∀ xs : List ℤ,
  0 ≤ vec xs ⬝ᵥ (signless (ofEdges es) *ᵥ vec xs)) 45

/- `L⁺` on the exact shadow: Penrose, symmetry, positive semidefinite, `R_eff ≥ 0`. -/
#eval survives (∀ es : List (Fin 5 × Fin 5 × ℕ), ∀ xs : List ℤ,
  pinvLaws (ofEdges (nonneg es)) (vec xs) = true) 46

/- Control: the connected-graph formula applied to every graph (CND-1's "per component"). -/
#eval refuted (∀ es : List (Fin 5 × Fin 5 × ℕ),
  connectedFormulaLaws (ofEdges (nonneg es)) = true) 47

end Attack

end Palace
