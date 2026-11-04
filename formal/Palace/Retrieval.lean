module

public import Palace.Retrieval.Defs
public import Mathlib.LinearAlgebra.Matrix.ToLinearEquiv
public import Mathlib.LinearAlgebra.Matrix.PosDef
public import Mathlib.Analysis.SpecialFunctions.Log.Basic
public import Mathlib.Analysis.SpecialFunctions.Sqrt
public import Mathlib.Combinatorics.SimpleGraph.Connectivity.Connected

/-!
# The retrieval curve: RSP-1 to RSP-4

`core/query.py`'s `free_energy_distances` computes the β-curve of
`docs/design-notes/temporal-retrieval-algebra.md` §2.1 (Theorem A1). Its laws, over exact
arithmetic:

* RSP-1: for weights in `[0, 1]`, `β ≥ 0` and `0 ≤ z < 1` every row of the killed walk sums to at
  most `z`, so `I − W_β` is invertible, `Z = (I − W_β)⁻¹` is nonnegative with `z_ii ≥ 1`, and
  `z_ij > 0` exactly when `j` is reachable from `i`: the code's `+∞` marks the unreachable pairs.
* RSP-2: with every degree positive, `Z = G_β D` for the symmetric kernel
  `G_β = (D − z·w∘w^β)⁻¹`, which is positive definite for every `β`: Theorem A1's "`K(β)` is PSD
  for all finite β", in the code's normalization.
* RSP-3: `e^{−β d_ij} = G_ij / √(G_ii G_jj)`, so on a connected support the matrix `e^{−β d}` is
  positive definite for every `β`; at the code's default `β = 1` that matrix is `K_struct`.
* RSP-4: the free energy is a quasi-metric (`φ ≥ 0`, `φ_ii = 0`, the triangle inequality, from
  the path product `z_ij z_jk ≤ z_ik z_jj`), so the code's symmetrized distance is a pseudometric.

The first section proves what these rest on for any nonnegative matrix whose rows sum to at most
`s < 1`, by extremal principles: a vertex where a vector is largest or least.
-/

@[expose] public section

open Matrix Finset

namespace Palace.Retrieval

variable {V : Type*} [Fintype V] [DecidableEq V]

/-! ## Substochastic matrices: extremal principles -/

section Substochastic

variable {M : Matrix V V ℝ} {s : ℝ}

/-- `I − M` is injective when `M ≥ 0` has row sums at most `s < 1`: at a vertex where `|x|` is
largest, `|x_i| ≤ s |x_i|`. -/
theorem eq_zero_of_one_sub_mulVec_eq_zero (hM : ∀ i j, 0 ≤ M i j)
    (hrow : ∀ i, ∑ j, M i j ≤ s) (hs : s < 1) {x : V → ℝ} (hx : (1 - M) *ᵥ x = 0) : x = 0 := by
  by_contra hne
  obtain ⟨i₀, -⟩ := Function.ne_iff.mp hne
  have : Nonempty V := ⟨i₀⟩
  obtain ⟨i, hi⟩ := Finite.exists_max fun k ↦ |x k|
  have hfix : x i = ∑ j, M i j * x j := by
    rw [sub_mulVec, one_mulVec] at hx
    have h := congrFun hx i
    simp only [Pi.sub_apply, Pi.zero_apply, mulVec, dotProduct] at h
    linarith
  have hle : |x i| ≤ s * |x i| :=
    calc |x i| = |∑ j, M i j * x j| := by rw [← hfix]
      _ ≤ ∑ j, |M i j * x j| := abs_sum_le_sum_abs _ _
      _ = ∑ j, M i j * |x j| := sum_congr rfl fun j _ ↦ by rw [abs_mul, abs_of_nonneg (hM i j)]
      _ ≤ ∑ j, M i j * |x i| := sum_le_sum fun j _ ↦ mul_le_mul_of_nonneg_left (hi j) (hM i j)
      _ = (∑ j, M i j) * |x i| := by rw [sum_mul]
      _ ≤ s * |x i| := mul_le_mul_of_nonneg_right (hrow i) (abs_nonneg _)
  have h0 : |x i| = 0 := by nlinarith [abs_nonneg (x i)]
  exact hne (funext fun k ↦ abs_eq_zero.mp (le_antisymm (h0 ▸ hi k) (abs_nonneg _)))

theorem det_one_sub_ne_zero (hM : ∀ i j, 0 ≤ M i j) (hrow : ∀ i, ∑ j, M i j ≤ s) (hs : s < 1) :
    (1 - M).det ≠ 0 := fun h ↦ by
  obtain ⟨x, hx0, hx⟩ := exists_mulVec_eq_zero_iff.mpr h
  exact hx0 (eq_zero_of_one_sub_mulVec_eq_zero hM hrow hs hx)

theorem one_sub_mul_inv (hM : ∀ i j, 0 ≤ M i j) (hrow : ∀ i, ∑ j, M i j ≤ s) (hs : s < 1) :
    (1 - M) * (1 - M)⁻¹ = 1 :=
  mul_nonsing_inv _ (isUnit_iff_ne_zero.mpr (det_one_sub_ne_zero hM hrow hs))

/-- The walk-sum recursion `Z = I + M Z`, entrywise. -/
theorem inv_apply_eq (hM : ∀ i j, 0 ≤ M i j) (hrow : ∀ i, ∑ j, M i j ≤ s) (hs : s < 1)
    (i k : V) : (1 - M)⁻¹ i k = (if i = k then 1 else 0) + ∑ j, M i j * (1 - M)⁻¹ j k := by
  have h0 := one_sub_mul_inv hM hrow hs
  rw [sub_mul, one_mul] at h0
  have h := congrFun (congrFun h0 i) k
  rw [Matrix.sub_apply, Matrix.mul_apply, Matrix.one_apply] at h
  linarith

/-- `(I − M)⁻¹ ≥ 0`: at a vertex where a column is least, it is at least `s` times itself. -/
theorem inv_nonneg (hM : ∀ i j, 0 ≤ M i j) (hrow : ∀ i, ∑ j, M i j ≤ s) (hs : s < 1)
    (i k : V) : 0 ≤ (1 - M)⁻¹ i k := by
  have : Nonempty V := ⟨i⟩
  obtain ⟨m, hm⟩ := Finite.exists_min fun a ↦ (1 - M)⁻¹ a k
  refine le_trans ?_ (hm i)
  by_contra hneg
  push Not at hneg
  have e := inv_apply_eq hM hrow hs m k
  have h1 : (∑ j, M m j) * (1 - M)⁻¹ m k ≤ ∑ j, M m j * (1 - M)⁻¹ j k := by
    rw [sum_mul]
    exact sum_le_sum fun j _ ↦ mul_le_mul_of_nonneg_left (hm j) (hM m j)
  have h2 : s * (1 - M)⁻¹ m k ≤ (∑ j, M m j) * (1 - M)⁻¹ m k :=
    mul_le_mul_of_nonpos_right (hrow m) hneg.le
  have hδ : (0 : ℝ) ≤ if m = k then 1 else 0 := by split_ifs <;> norm_num
  nlinarith

/-- `z_kk ≥ 1`: the empty walk. -/
theorem one_le_inv_apply_self (hM : ∀ i j, 0 ≤ M i j) (hrow : ∀ i, ∑ j, M i j ≤ s) (hs : s < 1)
    (k : V) : 1 ≤ (1 - M)⁻¹ k k := by
  have e := inv_apply_eq hM hrow hs k k
  have h : 0 ≤ ∑ j, M k j * (1 - M)⁻¹ j k :=
    sum_nonneg fun j _ ↦ mul_nonneg (hM k j) (inv_nonneg hM hrow hs j k)
  simp only [ite_true] at e
  linarith

/-- First passage: `z_ij ≤ z_jj`. At a vertex other than `j` where column `j` is largest, it is
at most `s` times itself. -/
theorem inv_apply_le_inv_apply_self (hM : ∀ i j, 0 ≤ M i j) (hrow : ∀ i, ∑ j, M i j ≤ s)
    (hs : s < 1) (i j : V) : (1 - M)⁻¹ i j ≤ (1 - M)⁻¹ j j := by
  have : Nonempty V := ⟨i⟩
  obtain ⟨m, hm⟩ := Finite.exists_max fun a ↦ (1 - M)⁻¹ a j
  refine (hm i).trans ?_
  by_contra hlt
  push Not at hlt
  have hmj : m ≠ j := by rintro rfl; exact lt_irrefl _ hlt
  have e := inv_apply_eq hM hrow hs m j
  simp only [hmj, ite_false, zero_add] at e
  have hpos : 0 < (1 - M)⁻¹ m j :=
    lt_of_lt_of_le one_pos ((one_le_inv_apply_self hM hrow hs j).trans hlt.le)
  have hle : (1 - M)⁻¹ m j ≤ s * (1 - M)⁻¹ m j :=
    calc (1 - M)⁻¹ m j = ∑ b, M m b * (1 - M)⁻¹ b j := e
      _ ≤ ∑ b, M m b * (1 - M)⁻¹ m j :=
          sum_le_sum fun b _ ↦ mul_le_mul_of_nonneg_left (hm b) (hM m b)
      _ = (∑ b, M m b) * (1 - M)⁻¹ m j := by rw [sum_mul]
      _ ≤ s * (1 - M)⁻¹ m j := mul_le_mul_of_nonneg_right (hrow m) hpos.le
  nlinarith

/-- The path product of an inverse M-matrix: `z_ij z_jk ≤ z_ik z_jj`, the walks from `i` to `k`
through `j` being some of the walks from `i` to `k`. The vector `v_a = z_ak z_jj − z_aj z_jk`
vanishes at `j` and, elsewhere, is at least `M v`; where it is least it is nonnegative. -/
theorem inv_mul_inv_le (hM : ∀ i j, 0 ≤ M i j) (hrow : ∀ i, ∑ j, M i j ≤ s) (hs : s < 1)
    (i j k : V) : (1 - M)⁻¹ i j * (1 - M)⁻¹ j k ≤ (1 - M)⁻¹ i k * (1 - M)⁻¹ j j := by
  set Z := (1 - M)⁻¹ with hZ
  let v : V → ℝ := fun a ↦ Z a k * Z j j - Z a j * Z j k
  suffices h : ∀ a, 0 ≤ v a by have := h i; simp only [v] at this; linarith
  have : Nonempty V := ⟨i⟩
  obtain ⟨m, hm⟩ := Finite.exists_min v
  intro a
  refine le_trans ?_ (hm a)
  by_contra hneg
  push Not at hneg
  have hmj : m ≠ j := by
    rintro rfl
    simp only [v, mul_comm, sub_self, lt_irrefl] at hneg
  have ek := inv_apply_eq hM hrow hs m k
  have ej := inv_apply_eq hM hrow hs m j
  simp only [hmj, ite_false, zero_add] at ej
  have hv : v m = (if m = k then Z j j else 0) + ∑ b, M m b * v b := by
    simp only [v]
    rw [← hZ] at ek ej
    rw [ek, ej, add_mul, sum_mul, sum_mul, add_sub_assoc, ← sum_sub_distrib]
    congr 1
    · split_ifs <;> simp
    · exact sum_congr rfl fun b _ ↦ by ring
  have hδ : 0 ≤ if m = k then Z j j else 0 := by
    split_ifs
    · exact (zero_le_one.trans (one_le_inv_apply_self hM hrow hs j))
    · exact le_refl 0
  have h1 : (∑ b, M m b) * v m ≤ ∑ b, M m b * v b := by
    rw [sum_mul]
    exact sum_le_sum fun b _ ↦ mul_le_mul_of_nonneg_left (hm b) (hM m b)
  have h2 : s * v m ≤ (∑ b, M m b) * v m := mul_le_mul_of_nonpos_right (hrow m) hneg.le
  nlinarith

end Substochastic

/-! ## RSP-1: the walk sum is well posed -/

section Curve

variable {w : Matrix V V ℝ} {β z : ℝ}

omit [Fintype V] [DecidableEq V] in
theorem adj_of_ne {i j : V} (hij : i ≠ j) (h : w i j ≠ 0) : (support w).Adj i j := by
  rw [support, SimpleGraph.fromRel_adj]
  exact ⟨hij, Or.inl h⟩

omit [DecidableEq V] in
theorem degree_nonneg (hw0 : ∀ i j, 0 ≤ w i j) (i : V) : 0 ≤ degree w i :=
  sum_nonneg fun j _ ↦ hw0 i j

omit [DecidableEq V] in
theorem killedWalk_nonneg (hw0 : ∀ i j, 0 ≤ w i j) (hz : 0 ≤ z) (i j : V) :
    0 ≤ killedWalk w β z i j := by
  simp only [killedWalk, of_apply]
  exact mul_nonneg (mul_nonneg hz (div_nonneg (hw0 i j) (degree_nonneg hw0 i)))
    (Real.rpow_nonneg (hw0 i j) β)

omit [DecidableEq V] in
/-- Every row of the killed walk sums to at most `z`: `w^β ≤ 1` and `P` is substochastic. -/
theorem sum_killedWalk_le (hw0 : ∀ i j, 0 ≤ w i j) (hw1 : ∀ i j, w i j ≤ 1) (hβ : 0 ≤ β)
    (hz : 0 ≤ z) (i : V) : ∑ j, killedWalk w β z i j ≤ z := by
  have hd := degree_nonneg hw0 i
  calc ∑ j, killedWalk w β z i j ≤ ∑ j, z * (w i j / degree w i) :=
        sum_le_sum fun j _ ↦ by
          simp only [killedWalk, of_apply]
          exact mul_le_of_le_one_right (mul_nonneg hz (div_nonneg (hw0 i j) hd))
            (Real.rpow_le_one (hw0 i j) (hw1 i j) hβ)
    _ = z * (degree w i / degree w i) := by
        rw [← mul_sum]
        congr 1
        simp only [div_eq_mul_inv, ← sum_mul]
        rfl
    _ ≤ z := by
        rcases eq_or_lt_of_le hd with h | h
        · rw [← h, div_zero, mul_zero]
          exact hz
        · rw [div_self h.ne', mul_one]

variable (hw0 : ∀ i j, 0 ≤ w i j) (hw1 : ∀ i j, w i j ≤ 1) (hβ : 0 ≤ β) (hz0 : 0 ≤ z)
  (hz1 : z < 1)
include hw0 hw1 hβ hz0 hz1

/-- **RSP-1** The walk sum is well posed: `I − W_β` is invertible, the γ-ceiling `z < 1` bounding
every row of `W_β` by `z`. -/
theorem det_one_sub_killedWalk_ne_zero : (1 - killedWalk w β z).det ≠ 0 :=
  det_one_sub_ne_zero (killedWalk_nonneg hw0 hz0) (sum_killedWalk_le hw0 hw1 hβ hz0) hz1

/-- **RSP-1** `Z = (I − W_β)⁻¹` is nonnegative. -/
theorem fundamental_nonneg (i j : V) : 0 ≤ fundamental w β z i j :=
  inv_nonneg (killedWalk_nonneg hw0 hz0) (sum_killedWalk_le hw0 hw1 hβ hz0) hz1 i j

/-- **RSP-1** `z_ii ≥ 1`. -/
theorem one_le_fundamental_self (i : V) : 1 ≤ fundamental w β z i i :=
  one_le_inv_apply_self (killedWalk_nonneg hw0 hz0) (sum_killedWalk_le hw0 hw1 hβ hz0) hz1 i

theorem fundamental_apply_eq (i k : V) : fundamental w β z i k =
    (if i = k then 1 else 0) + ∑ j, killedWalk w β z i j * fundamental w β z j k :=
  inv_apply_eq (killedWalk_nonneg hw0 hz0) (sum_killedWalk_le hw0 hw1 hβ hz0) hz1 i k

omit [DecidableEq V] hw1 hβ hz0 hz1 in
theorem killedWalk_pos (hz : 0 < z) {i j : V} (h : 0 < w i j) : 0 < killedWalk w β z i j := by
  simp only [killedWalk, of_apply]
  have hd : 0 < degree w i :=
    lt_of_lt_of_le h (single_le_sum (fun k _ ↦ hw0 i k) (mem_univ j))
  exact mul_pos (mul_pos hz (div_pos h hd)) (Real.rpow_pos_of_pos h β)

/-- **RSP-1** `z_ij > 0` when `j` is reachable from `i` along edges of positive weight. -/
theorem fundamental_pos_of_reachable (hw : w.IsSymm) (hz : 0 < z) {i j : V}
    (h : (support w).Reachable i j) : 0 < fundamental w β z i j := by
  obtain ⟨p⟩ := h
  induction p with
  | nil => exact lt_of_lt_of_le one_pos (one_le_fundamental_self hw0 hw1 hβ hz0 hz1 _)
  | @cons a b c hab p ih =>
    have hw' : 0 < w a b := by
      rw [support, SimpleGraph.fromRel_adj] at hab
      rcases hab.2 with h' | h'
      · exact lt_of_le_of_ne (hw0 a b) (Ne.symm h')
      · rw [hw.apply a b] at h'
        exact lt_of_le_of_ne (hw0 a b) (Ne.symm h')
    rw [fundamental_apply_eq hw0 hw1 hβ hz0 hz1]
    have hterm : killedWalk w β z a b * fundamental w β z b c ≤
        ∑ l, killedWalk w β z a l * fundamental w β z l c :=
      single_le_sum (f := fun l ↦ killedWalk w β z a l * fundamental w β z l c)
        (fun l _ ↦ mul_nonneg (killedWalk_nonneg hw0 hz0 a l)
          (fundamental_nonneg hw0 hw1 hβ hz0 hz1 l c)) (mem_univ b)
    have hδ : (0 : ℝ) ≤ if a = c then 1 else 0 := by split_ifs <;> norm_num
    have hprod : 0 < killedWalk w β z a b * fundamental w β z b c :=
      mul_pos (killedWalk_pos hw0 hz hw') ih
    linarith

/-- **RSP-1** `z_ij = 0` when `j` is not reachable from `i`: where column `j` is largest among the
vertices reachable from `i`, it is at most `z` times itself. With `fundamental_pos_of_reachable`,
the code's `+∞` marks exactly the unreachable pairs. -/
theorem fundamental_eq_zero_of_not_reachable {i j : V} (h : ¬(support w).Reachable i j) :
    fundamental w β z i j = 0 := by
  classical
  set Z := fundamental w β z with hZ
  let R : Finset V := univ.filter fun a ↦ (support w).Reachable i a
  have hiR : i ∈ R := by simp [R]
  have hjR : j ∉ R := by simpa [R] using h
  obtain ⟨m, hmR, hm⟩ := R.exists_max_image (fun a ↦ Z a j) ⟨i, hiR⟩
  have hmj : m ≠ j := fun e ↦ hjR (e ▸ hmR)
  have hreach : (support w).Reachable i m := by simpa [R] using hmR
  have e := fundamental_apply_eq hw0 hw1 hβ hz0 hz1 m j
  simp only [hmj, ite_false, zero_add] at e
  rw [← hZ] at e
  have hle (l : V) : killedWalk w β z m l * Z l j ≤ killedWalk w β z m l * Z m j := by
    by_cases hl : l ∈ R
    · exact mul_le_mul_of_nonneg_left (hm l hl) (killedWalk_nonneg hw0 hz0 m l)
    · have h0 : killedWalk w β z m l = 0 := by
        by_contra hne
        have hwml : w m l ≠ 0 := fun h0 ↦ hne (by simp [killedWalk, h0])
        apply hl
        simp only [R, mem_filter, mem_univ, true_and]
        by_cases hml : m = l
        · exact hml ▸ hreach
        · exact hreach.trans (adj_of_ne hml hwml).reachable
      simp [h0]
  have hZmj : 0 ≤ Z m j := fundamental_nonneg hw0 hw1 hβ hz0 hz1 m j
  have hbound : Z m j ≤ z * Z m j :=
    calc Z m j = ∑ l, killedWalk w β z m l * Z l j := e
      _ ≤ ∑ l, killedWalk w β z m l * Z m j := sum_le_sum fun l _ ↦ hle l
      _ = (∑ l, killedWalk w β z m l) * Z m j := by rw [sum_mul]
      _ ≤ z * Z m j := mul_le_mul_of_nonneg_right (sum_killedWalk_le hw0 hw1 hβ hz0 m) hZmj
  have hmax : Z m j ≤ 0 := by nlinarith
  exact le_antisymm ((hm i hiR).trans hmax) (fundamental_nonneg hw0 hw1 hβ hz0 hz1 i j)

end Curve

/-! ## RSP-2 and RSP-3: the symmetric kernel, positive definite for every β -/

section Kernel

variable {w : Matrix V V ℝ} {β z : ℝ}

/-- The weights the kernel sees, `w∘w^β`. -/
local notation "W'" => (of fun i j ↦ w i j * w i j ^ β : Matrix V V ℝ)

omit [DecidableEq V] in
theorem dotProduct_mulVec_weights (x : V → ℝ) :
    x ⬝ᵥ (W' *ᵥ x) = ∑ i, ∑ j, w i j * w i j ^ β * x i * x j := by
  simp only [dotProduct, mulVec, of_apply, mul_sum]
  exact sum_congr rfl fun i _ ↦ sum_congr rfl fun j _ ↦ by ring

/-- **RSP-2** Theorem A1's kernel is positive definite for every `β ≥ 0`: `D − z·w∘w^β` is, for
symmetric weights in `[0, 1]` with every degree positive and `0 ≤ z < 1`, since
`xᵀ(D − z W')x ≥ (1 − z) Σ d_i x_i²` (twice `x_i x_j ≤ x_i² + x_j²`, and `W' ≤ w`). -/
theorem posDef_rspKernel (hw : w.IsSymm) (hw0 : ∀ i j, 0 ≤ w i j) (hw1 : ∀ i j, w i j ≤ 1)
    (hd : ∀ i, 0 < degree w i) (hβ : 0 ≤ β) (hz0 : 0 ≤ z) (hz1 : z < 1) :
    (rspKernel w β z).PosDef := by
  have hW0 (i j : V) : 0 ≤ w i j * w i j ^ β := mul_nonneg (hw0 i j) (Real.rpow_nonneg (hw0 i j) β)
  have hWle (i j : V) : w i j * w i j ^ β ≤ w i j :=
    mul_le_of_le_one_right (hw0 i j) (Real.rpow_le_one (hw0 i j) (hw1 i j) hβ)
  have hWsym (i j : V) : w j i * w j i ^ β = w i j * w i j ^ β := by rw [hw.apply i j]
  refine PosDef.inv (PosDef.of_dotProduct_mulVec_pos ?_ fun x hx ↦ ?_)
  · rw [IsHermitian, conjTranspose_eq_transpose_of_trivial]
    ext i j
    simp only [transpose_apply, Matrix.sub_apply, diagonal_apply, Matrix.smul_apply, of_apply,
      smul_eq_mul, hWsym i j]
    by_cases h : i = j
    · subst h
      rfl
    · simp [h, Ne.symm h]
  · rw [star_trivial, sub_mulVec, dotProduct_sub, smul_mulVec, dotProduct_smul, smul_eq_mul,
      dotProduct_mulVec_weights]
    have hdiag : x ⬝ᵥ (diagonal (degree w) *ᵥ x) = ∑ i, degree w i * x i ^ 2 := by
      simp only [dotProduct, mulVec_diagonal]
      exact sum_congr rfl fun i _ ↦ by ring
    rw [hdiag]
    have h0 : 0 ≤ ∑ i, ∑ j, w i j * w i j ^ β * (x i - x j) ^ 2 :=
      sum_nonneg fun i _ ↦ sum_nonneg fun j _ ↦ mul_nonneg (hW0 i j) (sq_nonneg _)
    have hexp : ∑ i, ∑ j, w i j * w i j ^ β * (x i - x j) ^ 2 =
        ∑ i, ∑ j, w i j * w i j ^ β * x i ^ 2 + ∑ i, ∑ j, w i j * w i j ^ β * x j ^ 2 -
          2 * ∑ i, ∑ j, w i j * w i j ^ β * x i * x j := by
      simp only [mul_sum, ← sum_add_distrib, ← sum_sub_distrib]
      exact sum_congr rfl fun i _ ↦ sum_congr rfl fun j _ ↦ by ring
    have hswap : ∑ i, ∑ j, w i j * w i j ^ β * x j ^ 2 = ∑ i, ∑ j, w i j * w i j ^ β * x i ^ 2 := by
      rw [sum_comm]
      exact sum_congr rfl fun i _ ↦ sum_congr rfl fun j _ ↦ by rw [hWsym]
    have hdeg : ∑ i, ∑ j, w i j * w i j ^ β * x i ^ 2 ≤ ∑ i, degree w i * x i ^ 2 :=
      sum_le_sum fun i _ ↦ by
        rw [← sum_mul, degree]
        exact mul_le_mul_of_nonneg_right (sum_le_sum fun j _ ↦ hWle i j) (sq_nonneg _)
    have hpos : 0 < ∑ i, degree w i * x i ^ 2 := by
      obtain ⟨i, hi⟩ := Function.ne_iff.mp hx
      have hi' : x i ≠ 0 := hi
      exact lt_of_lt_of_le (mul_pos (hd i) (by positivity))
        (single_le_sum (fun k _ ↦ mul_nonneg (hd k).le (sq_nonneg (x k))) (mem_univ i))
    nlinarith

/-- **RSP-2** `Z = G_β D`: `I − W_β = D⁻¹ (D − z W')` when every degree is positive. -/
theorem fundamental_eq_rspKernel_mul (hd : ∀ i, 0 < degree w i) :
    fundamental w β z = rspKernel w β z * diagonal (degree w) := by
  have h1 : 1 - killedWalk w β z =
      diagonal (fun i ↦ (degree w i)⁻¹) * (diagonal (degree w) - z • W') := by
    ext i j
    rw [diagonal_mul]
    simp only [Matrix.sub_apply, Matrix.one_apply, killedWalk, of_apply, diagonal_apply,
      Matrix.smul_apply, smul_eq_mul]
    have := (hd i).ne'
    split_ifs with h
    · subst h
      field_simp
    · simp only [zero_sub]
      field_simp
  have h2 : (diagonal fun i ↦ (degree w i)⁻¹)⁻¹ = diagonal (degree w) := by
    refine inv_eq_left_inv ?_
    rw [diagonal_mul_diagonal, ← diagonal_one]
    congr 1
    ext i
    exact mul_inv_cancel₀ (hd i).ne'
  rw [fundamental, h1, Matrix.mul_inv_rev, h2, rspKernel]

theorem isSymm_rspKernel_aux (hw : w.IsSymm) :
    (diagonal (degree w) - z • W').IsSymm := by
  ext i j
  simp only [transpose_apply, Matrix.sub_apply, diagonal_apply, Matrix.smul_apply, of_apply,
    smul_eq_mul, hw.apply i j]
  by_cases h : i = j
  · subst h
    rfl
  · simp [h, Ne.symm h]

/-- The kernel is symmetric. -/
theorem rspKernel_symm (hw : w.IsSymm) (i j : V) : rspKernel w β z j i = rspKernel w β z i j := by
  have h := (isSymm_rspKernel_aux (β := β) (z := z) hw)
  have : (rspKernel w β z)ᵀ = rspKernel w β z := by
    rw [rspKernel, transpose_nonsing_inv, h.eq]
  exact congrFun (congrFun this i) j

end Kernel

/-! ## RSP-3: `e^{−β d}` is the normalized kernel; RSP-4: a quasi-metric -/

section Distance

variable {w : Matrix V V ℝ} {β z : ℝ}

theorem fundamental_apply_eq_kernel (hd : ∀ i, 0 < degree w i) (a b : V) :
    fundamental w β z a b = rspKernel w β z a b * degree w b := by
  rw [fundamental_eq_rspKernel_mul hd, mul_diagonal]

theorem rspKernel_self_pos (hw0 : ∀ i j, 0 ≤ w i j) (hw1 : ∀ i j, w i j ≤ 1)
    (hd : ∀ i, 0 < degree w i) (hβ : 0 ≤ β) (hz0 : 0 ≤ z) (hz1 : z < 1) (i : V) :
    0 < rspKernel w β z i i := by
  have h1 := one_le_fundamental_self hw0 hw1 hβ hz0 hz1 i
  rw [fundamental_apply_eq_kernel hd] at h1
  by_contra h
  push Not at h
  nlinarith [hd i]

/-- **RSP-3** `e^{−β d_ij} = G_ij / √(G_ii G_jj)` on a pair with `z_ij > 0`: the symmetrized
free energy is the log of the normalized kernel. -/
theorem exp_neg_mul_feDist (hw : w.IsSymm) (hw0 : ∀ i j, 0 ≤ w i j) (hw1 : ∀ i j, w i j ≤ 1)
    (hd : ∀ i, 0 < degree w i) (hβ : 0 < β) (hz0 : 0 ≤ z) (hz1 : z < 1) {i j : V}
    (hij : 0 < fundamental w β z i j) :
    Real.exp (-(β * feDist w β z i j)) =
      rspKernel w β z i j / Real.sqrt (rspKernel w β z i i * rspKernel w β z j j) := by
  have hZ := fundamental_apply_eq_kernel (β := β) (z := z) hd
  have hGii := rspKernel_self_pos hw0 hw1 hd hβ.le hz0 hz1 i
  have hGjj := rspKernel_self_pos hw0 hw1 hd hβ.le hz0 hz1 j
  set G := rspKernel w β z
  have hGij : 0 < G i j := by
    rw [hZ] at hij
    by_contra h
    push Not at h
    nlinarith [hd j]
  have hsym : G j i = G i j := rspKernel_symm hw i j
  have hφ : β * feDist w β z i j = -(Real.log (G i j / G j j) + Real.log (G i j / G i i)) / 2 := by
    simp only [feDist, freeEnergy, hZ]
    rw [mul_div_mul_right _ _ (hd j).ne', mul_div_mul_right _ _ (hd i).ne', hsym]
    field_simp
    ring
  have hab : 0 < G i j / G j j * (G i j / G i i) := by positivity
  rw [hφ, neg_div, neg_neg, ← Real.log_mul (by positivity) (by positivity),
    ← Real.log_sqrt hab.le, Real.exp_log (Real.sqrt_pos.mpr hab),
    show G i j / G j j * (G i j / G i i) = G i j ^ 2 / (G i i * G j j) by field_simp,
    Real.sqrt_div (sq_nonneg _), Real.sqrt_sq hGij.le]

/-- **RSP-3** On a connected support `e^{−β d}` is positive definite for every `β > 0`: it is the
kernel `G_β` congruent by `diag(1/√G_ii)`. -/
theorem posDef_exp_neg_mul_feDist (hw : w.IsSymm) (hw0 : ∀ i j, 0 ≤ w i j)
    (hw1 : ∀ i j, w i j ≤ 1) (hd : ∀ i, 0 < degree w i) (hβ : 0 < β) (hz : 0 < z) (hz1 : z < 1)
    (hc : (support w).Connected) :
    (of fun i j ↦ Real.exp (-(β * feDist w β z i j))).PosDef := by
  have hpos (i j : V) : 0 < fundamental w β z i j :=
    fundamental_pos_of_reachable hw0 hw1 hβ.le hz.le hz1 hw hz (hc.preconnected i j)
  have hGii := rspKernel_self_pos hw0 hw1 hd hβ.le hz.le hz1
  let c : V → ℝ := fun i ↦ (Real.sqrt (rspKernel w β z i i))⁻¹
  have e : (of fun i j ↦ Real.exp (-(β * feDist w β z i j))) =
      (diagonal c)ᴴ * rspKernel w β z * diagonal c := by
    ext i j
    rw [of_apply, exp_neg_mul_feDist hw hw0 hw1 hd hβ hz.le hz1 (hpos i j),
      conjTranspose_eq_transpose_of_trivial, diagonal_transpose, mul_diagonal, diagonal_mul,
      Real.sqrt_mul (hGii i).le]
    have := Real.sqrt_pos.mpr (hGii i)
    have := Real.sqrt_pos.mpr (hGii j)
    simp only [c]
    field_simp
  rw [e]
  refine (posDef_rspKernel hw hw0 hw1 hd hβ.le hz.le hz1).conjTranspose_mul_mul_same ?_
  intro x y hxy
  funext i
  have h := congrFun hxy i
  simp only [mulVec_diagonal] at h
  exact mul_left_cancel₀ (inv_ne_zero (Real.sqrt_pos.mpr (hGii i)).ne') h

/-- **RSP-3** At the code's default `β = 1`, `K_struct = e^{−d}` is positive definite on a
connected support: the HYBRID Schur product stays in the PSD cone there. -/
theorem posDef_kStruct (hw : w.IsSymm) (hw0 : ∀ i j, 0 ≤ w i j) (hw1 : ∀ i j, w i j ≤ 1)
    (hd : ∀ i, 0 < degree w i) (hz : 0 < z) (hz1 : z < 1) (hc : (support w).Connected) :
    (of fun i j ↦ Real.exp (-feDist w 1 z i j)).PosDef := by
  simpa using posDef_exp_neg_mul_feDist hw hw0 hw1 hd one_pos hz hz1 hc

/-- **RSP-4** `φ_ii = 0`. -/
theorem freeEnergy_self (hw0 : ∀ i j, 0 ≤ w i j) (hw1 : ∀ i j, w i j ≤ 1) (hβ : 0 ≤ β)
    (hz0 : 0 ≤ z) (hz1 : z < 1) (i : V) : freeEnergy w β z i i = 0 := by
  have h := one_le_fundamental_self hw0 hw1 hβ hz0 hz1 i
  simp [freeEnergy, div_self (show fundamental w β z i i ≠ 0 by linarith)]

/-- **RSP-4** `φ_ij ≥ 0`: first passage, `z_ij ≤ z_jj`. -/
theorem freeEnergy_nonneg (hw0 : ∀ i j, 0 ≤ w i j) (hw1 : ∀ i j, w i j ≤ 1) (hβ : 0 < β)
    (hz0 : 0 ≤ z) (hz1 : z < 1) (i j : V) : 0 ≤ freeEnergy w β z i j := by
  have hjj := one_le_fundamental_self hw0 hw1 hβ.le hz0 hz1 j
  have hle : fundamental w β z i j ≤ fundamental w β z j j :=
    inv_apply_le_inv_apply_self (killedWalk_nonneg hw0 hz0) (sum_killedWalk_le hw0 hw1 hβ.le hz0)
      hz1 i j
  have h0 := fundamental_nonneg hw0 hw1 hβ.le hz0 hz1 i j
  have hlog : Real.log (fundamental w β z i j / fundamental w β z j j) ≤ 0 :=
    Real.log_nonpos (div_nonneg h0 (by linarith)) ((div_le_one (by linarith)).mpr hle)
  exact div_nonneg (by linarith) hβ.le

/-- **RSP-4** The triangle inequality of the free energy, `φ_ik ≤ φ_ij + φ_jk`, from the path
product `z_ij z_jk ≤ z_ik z_jj`. -/
theorem freeEnergy_triangle (hw0 : ∀ i j, 0 ≤ w i j) (hw1 : ∀ i j, w i j ≤ 1) (hβ : 0 < β)
    (hz0 : 0 ≤ z) (hz1 : z < 1) {i j k : V} (hij : 0 < fundamental w β z i j)
    (hjk : 0 < fundamental w β z j k) :
    freeEnergy w β z i k ≤ freeEnergy w β z i j + freeEnergy w β z j k := by
  have hjj := one_le_fundamental_self hw0 hw1 hβ.le hz0 hz1 j
  have hkk := one_le_fundamental_self hw0 hw1 hβ.le hz0 hz1 k
  set Z := fundamental w β z with hZ
  have hpp : Z i j * Z j k ≤ Z i k * Z j j :=
    inv_mul_inv_le (killedWalk_nonneg hw0 hz0) (sum_killedWalk_le hw0 hw1 hβ.le hz0) hz1 i j k
  have hik : 0 < Z i k := by
    by_contra h
    push Not at h
    nlinarith [mul_pos hij hjk]
  have hlog : Real.log (Z i j / Z j j) + Real.log (Z j k / Z k k) ≤ Real.log (Z i k / Z k k) := by
    rw [← Real.log_mul (by positivity) (by positivity)]
    refine Real.log_le_log (by positivity) ?_
    rw [div_mul_div_comm, div_le_div_iff₀ (by positivity) (by positivity)]
    nlinarith
  simp only [freeEnergy]
  rw [← add_div, div_le_div_iff_of_pos_right hβ]
  linarith

/-- **RSP-4** The code's symmetrized distance is a pseudometric on a connected support: zero on
the diagonal, nonnegative, symmetric, and the triangle inequality. -/
theorem feDist_triangle (hw : w.IsSymm) (hw0 : ∀ i j, 0 ≤ w i j) (hw1 : ∀ i j, w i j ≤ 1)
    (hβ : 0 < β) (hz : 0 < z) (hz1 : z < 1) (hc : (support w).Connected) (i j k : V) :
    feDist w β z i k ≤ feDist w β z i j + feDist w β z j k := by
  have hpos (a b : V) : 0 < fundamental w β z a b :=
    fundamental_pos_of_reachable hw0 hw1 hβ.le hz.le hz1 hw hz (hc.preconnected a b)
  have h1 := freeEnergy_triangle hw0 hw1 hβ hz.le hz1 (hpos i j) (hpos j k)
  have h2 := freeEnergy_triangle hw0 hw1 hβ hz.le hz1 (hpos k j) (hpos j i)
  simp only [feDist]
  linarith

theorem feDist_comm (i j : V) : feDist w β z i j = feDist w β z j i := by
  simp only [feDist, add_comm]

/-- **RSP-4** The distance vanishes on the diagonal and is nonnegative. -/
theorem feDist_self_and_nonneg (hw0 : ∀ i j, 0 ≤ w i j) (hw1 : ∀ i j, w i j ≤ 1) (hβ : 0 < β)
    (hz0 : 0 ≤ z) (hz1 : z < 1) (i j : V) :
    feDist w β z i i = 0 ∧ 0 ≤ feDist w β z i j := by
  refine ⟨?_, ?_⟩
  · simp [feDist, freeEnergy_self hw0 hw1 hβ.le hz0 hz1 i]
  · have := freeEnergy_nonneg hw0 hw1 hβ hz0 hz1 i j
    have := freeEnergy_nonneg hw0 hw1 hβ hz0 hz1 j i
    simp only [feDist]
    linarith

end Distance

end Palace.Retrieval
