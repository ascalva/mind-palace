module

public import Palace.Gap.Defs

/-!
# The spectral-gap lemma: when a tolerance tells zero from nonzero (SPC-3)

Three tolerances in the code decide whether a computed spectral value is zero: the cut below which
`core/graph/conductance.py`'s pseudo-inverse treats a singular value of the Laplacian as zero, the
rank cut of `core/kernel/complex/hodge.py`, and, through the first, the rise threshold of the
reconnection scan. NumPy's decompositions are backward stable: the values they return are the
exact eigenvalues or singular values of `A + E` with `‖E‖ ≤ ε` (the hypothesis, `ε = n u ‖A‖`).
Weyl's inequality, counted, turns that into what a cut needs, and the spectral-gap lemma follows:
a cut `θ` with `ε ≤ θ` and `θ + ε < g`, `g` the least nonzero value of the exact matrix, keeps
exactly the kernel's dimension below it.

Mathlib has the spectral theorem for symmetric operators and Rayleigh's quotient for the extreme
eigenvalues, but neither Weyl's inequality nor Courant and Fischer's (checked 2026-11-05). The proof
here is the dimension count beneath both (`exists_of_card_lt`): fewer than `n` linear constraints
leave a nonzero vector, whose quadratic forms under the two operators then disagree.
-/

@[expose] public section

namespace Palace.Gap

variable {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E] [FiniteDimensional ℝ E]
  {n : ℕ}

/-- A symmetric operator's quadratic form in its eigenbasis: `⟪x, T x⟫ = Σ λᵢ ⟪bᵢ, x⟫²`. -/
theorem inner_self_apply_eq_sum {T : E →ₗ[ℝ] E} (hT : T.IsSymmetric) (hn : Module.finrank ℝ E = n)
    (x : E) : inner ℝ x (T x) =
      ∑ i, hT.eigenvalues hn i * inner ℝ (hT.eigenvectorBasis hn i) x ^ 2 := by
  rw [← (hT.eigenvectorBasis hn).sum_inner_mul_inner x (T x)]
  refine Finset.sum_congr rfl fun i _ ↦ ?_
  rw [← hT (hT.eigenvectorBasis hn i) x, hT.apply_eigenvectorBasis, real_inner_smul_left,
    real_inner_comm]
  simp only [RCLike.ofReal_real_eq_id, id]
  ring

/-- Parseval in the eigenbasis: `‖x‖² = Σ ⟪bᵢ, x⟫²`. -/
theorem norm_sq_eq_sum {T : E →ₗ[ℝ] E} (hT : T.IsSymmetric) (hn : Module.finrank ℝ E = n)
    (x : E) : ‖x‖ ^ 2 = ∑ i, inner ℝ (hT.eigenvectorBasis hn i) x ^ 2 := by
  rw [← real_inner_self_eq_norm_sq, ← (hT.eigenvectorBasis hn).sum_inner_mul_inner x x]
  refine Finset.sum_congr rfl fun i _ ↦ ?_
  rw [real_inner_comm x]; ring

/-- The dimension count behind Courant and Fischer: when fewer than `n` eigenvalues of `T₁` lie
above `c₁` and of `T₂` at most `c₂`, some nonzero `x` is orthogonal to all their eigenvectors, so
its form is at most `c₁ ‖x‖²` under `T₁` and above `c₂ ‖x‖²` under `T₂`. -/
theorem exists_of_card_lt {T₁ T₂ : E →ₗ[ℝ] E} (h₁ : T₁.IsSymmetric) (h₂ : T₂.IsSymmetric)
    (hn : Module.finrank ℝ E = n) {c₁ c₂ : ℝ}
    (hc : (Finset.univ.filter fun i ↦ c₁ < h₁.eigenvalues hn i).card +
      (Finset.univ.filter fun i ↦ h₂.eigenvalues hn i ≤ c₂).card < n) :
    ∃ x : E, x ≠ 0 ∧ inner ℝ x (T₁ x) ≤ c₁ * ‖x‖ ^ 2 ∧ c₂ * ‖x‖ ^ 2 < inner ℝ x (T₂ x) := by
  set S₁ := Finset.univ.filter fun i ↦ c₁ < h₁.eigenvalues hn i
  set S₂ := Finset.univ.filter fun i ↦ h₂.eigenvalues hn i ≤ c₂
  set b₁ := h₁.eigenvectorBasis hn
  set b₂ := h₂.eigenvectorBasis hn
  let f₁ : E →ₗ[ℝ] (↥S₁ → ℝ) := LinearMap.pi fun i ↦ innerₛₗ ℝ (b₁ i)
  let f₂ : E →ₗ[ℝ] (↥S₂ → ℝ) := LinearMap.pi fun i ↦ innerₛₗ ℝ (b₂ i)
  have hdim : Module.finrank ℝ ((↥S₁ → ℝ) × (↥S₂ → ℝ)) < Module.finrank ℝ E := by
    rw [Module.finrank_prod, Module.finrank_fintype_fun_eq_card,
      Module.finrank_fintype_fun_eq_card, Fintype.card_coe, Fintype.card_coe, hn]
    exact hc
  obtain ⟨x, hx, hx0⟩ := Submodule.exists_mem_ne_zero_of_ne_bot
    (LinearMap.ker_ne_bot_of_finrank_lt (f := f₁.prod f₂) hdim)
  rw [LinearMap.ker_prod, Submodule.mem_inf, LinearMap.mem_ker, LinearMap.mem_ker] at hx
  have z₁ : ∀ i, c₁ < h₁.eigenvalues hn i → inner ℝ (b₁ i) x = 0 := fun i hi ↦ by
    have := congrFun hx.1 ⟨i, by simp [S₁, hi]⟩
    simpa [f₁] using this
  have z₂ : ∀ i, h₂.eigenvalues hn i ≤ c₂ → inner ℝ (b₂ i) x = 0 := fun i hi ↦ by
    have := congrFun hx.2 ⟨i, by simp [S₂, hi]⟩
    simpa [f₂] using this
  refine ⟨x, hx0, ?_, ?_⟩
  · rw [inner_self_apply_eq_sum h₁ hn, norm_sq_eq_sum h₁ hn, Finset.mul_sum]
    refine Finset.sum_le_sum fun i _ ↦ ?_
    rcases lt_or_ge c₁ (h₁.eigenvalues hn i) with h | h
    · rw [z₁ i h]; simp
    · exact mul_le_mul_of_nonneg_right h (sq_nonneg _)
  · rw [inner_self_apply_eq_sum h₂ hn, norm_sq_eq_sum h₂ hn, Finset.mul_sum, ← sub_pos,
      ← Finset.sum_sub_distrib]
    have hpos : 0 < ‖x‖ ^ 2 := by positivity
    rw [norm_sq_eq_sum h₂ hn] at hpos
    obtain ⟨j, hj'⟩ : ∃ j, inner ℝ (b₂ j) x ≠ 0 := by
      by_contra h
      push Not at h
      simp [b₂, h] at hpos
    refine Finset.sum_pos' (fun i _ ↦ ?_) ⟨j, Finset.mem_univ _, ?_⟩
    · rcases le_or_gt (h₂.eigenvalues hn i) c₂ with h | h
      · rw [z₂ i h]; simp
      · nlinarith [sq_nonneg (inner ℝ (b₂ i) x)]
    · have hlam : c₂ < h₂.eigenvalues hn j := by
        by_contra h; exact hj' (z₂ j (not_lt.1 h))
      have := pow_pos (abs_pos.2 hj') 2
      rw [sq_abs] at this
      nlinarith

/-- The eigenvalues above `t` and those at most `t` are all `n` of them. -/
theorem card_lt_add_count {T : E →ₗ[ℝ] E} (hT : T.IsSymmetric) (hn : Module.finrank ℝ E = n)
    (t : ℝ) : (Finset.univ.filter fun i ↦ t < hT.eigenvalues hn i).card + count hT hn t = n := by
  unfold count
  have := Finset.card_filter_add_card_filter_not (s := (Finset.univ : Finset (Fin n)))
    (fun i ↦ hT.eigenvalues hn i ≤ t)
  simp only [not_le, Finset.card_univ, Fintype.card_fin] at this
  omega

/-- **SPC-3** Weyl's inequality, counted: a perturbation within `ε` keeps at most `t` every
eigenvalue that was at most `t − ε`. -/
theorem count_sub_le {A B : E →ₗ[ℝ] E} (hA : A.IsSymmetric) (hB : B.IsSymmetric)
    (hn : Module.finrank ℝ E = n) {ε : ℝ} (h : Near A B ε) (t : ℝ) :
    count hA hn (t - ε) ≤ count hB hn t := by
  by_contra hlt
  push Not at hlt
  have hc := card_lt_add_count hA hn (t - ε)
  obtain ⟨x, -, h₁, h₂⟩ := exists_of_card_lt hA hB hn (c₁ := t - ε) (c₂ := t)
    (by unfold count at hlt hc; omega)
  have hx := (abs_le.1 (h x)).2
  rw [LinearMap.sub_apply, inner_sub_right] at hx
  linarith

/-- **SPC-3** Weyl's inequality, counted the other way: a perturbation within `ε` brings at most
`t` only eigenvalues that were at most `t + ε`. -/
theorem count_le_add {A B : E →ₗ[ℝ] E} (hA : A.IsSymmetric) (hB : B.IsSymmetric)
    (hn : Module.finrank ℝ E = n) {ε : ℝ} (h : Near A B ε) (t : ℝ) :
    count hB hn t ≤ count hA hn (t + ε) := by
  by_contra hlt
  push Not at hlt
  have hc := card_lt_add_count hB hn t
  obtain ⟨x, -, h₁, h₂⟩ := exists_of_card_lt hB hA hn (c₁ := t) (c₂ := t + ε)
    (by unfold count at hlt hc; omega)
  have hx := (abs_le.1 (h x)).1
  rw [LinearMap.sub_apply, inner_sub_right] at hx
  linarith

/-- **SPC-3** The spectral-gap lemma for a symmetric eigensolver: if every nonzero eigenvalue of
`A` is at least `g`, the eigenvalues of `B`, within `ε` of `A`, at most a cut `θ` with `ε ≤ θ` and
`θ + ε < g` are exactly as many as `A`'s zero eigenvalues: the cut tells zero from nonzero. -/
theorem count_eq_of_gap {A B : E →ₗ[ℝ] E} (hA : A.IsSymmetric) (hB : B.IsSymmetric)
    (hn : Module.finrank ℝ E = n) {ε θ g : ℝ} (h : Near A B ε)
    (hgap : ∀ i, hA.eigenvalues hn i ≠ 0 → g ≤ hA.eigenvalues hn i)
    (hε : 0 ≤ ε) (hθ : ε ≤ θ) (hθg : θ + ε < g) :
    count hB hn θ = count hA hn 0 := by
  have h0 : count hA hn (θ + ε) = count hA hn 0 := by
    unfold count
    congr 1
    ext i
    simp only [Finset.mem_filter, Finset.mem_univ, true_and]
    constructor
    · intro hi
      by_contra hne
      have := hgap i (by intro h0; exact hne (le_of_eq h0))
      linarith
    · intro hi; linarith
  have h1 : count hA hn 0 ≤ count hA hn (θ - ε) := by
    unfold count
    exact Finset.card_le_card fun i hi ↦ by
      simp only [Finset.mem_filter, Finset.mem_univ, true_and] at hi ⊢; linarith
  exact le_antisymm ((count_le_add hA hB hn h θ).trans h0.le)
    (h1.trans (count_sub_le hA hB hn h θ))

/-- `⟪x, M† M x⟫ = ‖M x‖²`. -/
theorem inner_adjoint_mul_self (M : E →ₗ[ℝ] E) (x : E) :
    inner ℝ x ((LinearMap.adjoint M * M) x) = ‖M x‖ ^ 2 := by
  rw [Module.End.mul_apply, LinearMap.adjoint_inner_right, real_inner_self_eq_norm_sq]

/-- `M† M` is positive semidefinite. -/
theorem eigenvalues_adjoint_mul_self_nonneg (M : E →ₗ[ℝ] E) (hn : Module.finrank ℝ E = n)
    (i : Fin n) : 0 ≤ (LinearMap.isSymmetric_adjoint_mul_self M).eigenvalues hn i := by
  have hT := LinearMap.isSymmetric_adjoint_mul_self M
  have h1 := (hT.eigenvectorBasis hn).orthonormal.1 i
  have := inner_adjoint_mul_self M (hT.eigenvectorBasis hn i)
  rw [hT.apply_eigenvectorBasis, real_inner_smul_right, real_inner_self_eq_norm_sq, h1] at this
  simp only [RCLike.ofReal_real_eq_id, id, one_pow, mul_one] at this
  rw [this]; positivity

/-- **SPC-3** Weyl's inequality for singular values (Mirsky), counted: a perturbation of norm
at most `ε` keeps at most `t` every singular value that was at most `t − ε`. -/
theorem countSV_sub_le {M M' : E →ₗ[ℝ] E} (hn : Module.finrank ℝ E = n) {ε t : ℝ}
    (h : ∀ x, ‖(M' - M) x‖ ≤ ε * ‖x‖) (ht : ε ≤ t) :
    countSV M hn (t - ε) ≤ countSV M' hn t := by
  by_contra hlt
  push Not at hlt
  have hS := LinearMap.isSymmetric_adjoint_mul_self M
  have hS' := LinearMap.isSymmetric_adjoint_mul_self M'
  have hc := card_lt_add_count hS hn ((t - ε) ^ 2)
  obtain ⟨x, -, h₁, h₂⟩ := exists_of_card_lt hS hS' hn (c₁ := (t - ε) ^ 2) (c₂ := t ^ 2)
    (by unfold countSV count at hlt; unfold count at hc; omega)
  rw [inner_adjoint_mul_self] at h₁ h₂
  have hM : ‖M x‖ ≤ (t - ε) * ‖x‖ := by
    rw [← pow_le_pow_iff_left₀ (norm_nonneg _) (by nlinarith [norm_nonneg x]) two_ne_zero,
      mul_pow]
    exact h₁
  have hM' : ‖M' x‖ ≤ ‖M x‖ + ε * ‖x‖ := by
    have := norm_add_le (M x) ((M' - M) x)
    have hx := h x
    rw [LinearMap.sub_apply, add_sub_cancel] at this
    rw [LinearMap.sub_apply] at hx
    linarith
  have : ‖M' x‖ ^ 2 ≤ (t * ‖x‖) ^ 2 :=
    pow_le_pow_left₀ (norm_nonneg _) (by linarith) 2
  rw [mul_pow] at this
  linarith

/-- **SPC-3** And the other way: it brings at most `t` only singular values that were at most
`t + ε`. -/
theorem countSV_le_add {M M' : E →ₗ[ℝ] E} (hn : Module.finrank ℝ E = n) {ε t : ℝ}
    (h : ∀ x, ‖(M' - M) x‖ ≤ ε * ‖x‖) (hε : 0 ≤ ε) (ht : 0 ≤ t) :
    countSV M' hn t ≤ countSV M hn (t + ε) := by
  by_contra hlt
  push Not at hlt
  have hS := LinearMap.isSymmetric_adjoint_mul_self M
  have hS' := LinearMap.isSymmetric_adjoint_mul_self M'
  have hc := card_lt_add_count hS' hn (t ^ 2)
  obtain ⟨x, -, h₁, h₂⟩ := exists_of_card_lt hS' hS hn (c₁ := t ^ 2) (c₂ := (t + ε) ^ 2)
    (by unfold countSV count at hlt; unfold count at hc; omega)
  rw [inner_adjoint_mul_self] at h₁ h₂
  have hM' : ‖M' x‖ ≤ t * ‖x‖ := by
    rw [← pow_le_pow_iff_left₀ (norm_nonneg _) (by positivity) two_ne_zero, mul_pow]
    exact h₁
  have hM : (t + ε) * ‖x‖ < ‖M x‖ := by
    rw [← pow_lt_pow_iff_left₀ (by positivity) (norm_nonneg _) two_ne_zero, mul_pow]
    exact h₂
  have : ‖M x‖ ≤ ‖M' x‖ + ε * ‖x‖ := by
    have := norm_sub_le (M' x) ((M' - M) x)
    have hx := h x
    rw [LinearMap.sub_apply, sub_sub_cancel] at this
    rw [LinearMap.sub_apply] at hx
    linarith
  linarith

/-- **SPC-3** The spectral-gap lemma for an SVD: if every nonzero singular value of `M` is at
least `g`, the singular values of `M'`, within `ε` of `M` in norm, at most a cut `θ` with
`ε ≤ θ` and `θ + ε < g` are exactly as many as `M`'s zero singular values. -/
theorem countSV_eq_of_gap {M M' : E →ₗ[ℝ] E} (hn : Module.finrank ℝ E = n) {ε θ g : ℝ}
    (h : ∀ x, ‖(M' - M) x‖ ≤ ε * ‖x‖)
    (hgap : ∀ i, (LinearMap.isSymmetric_adjoint_mul_self M).eigenvalues hn i ≠ 0 →
      g ^ 2 ≤ (LinearMap.isSymmetric_adjoint_mul_self M).eigenvalues hn i)
    (hε : 0 ≤ ε) (hθ : ε ≤ θ) (hθg : θ + ε < g) :
    countSV M' hn θ = countSV M hn 0 := by
  have hpsd := eigenvalues_adjoint_mul_self_nonneg M hn
  have h0 : countSV M hn (θ + ε) = countSV M hn 0 := by
    unfold countSV count
    congr 1
    ext i
    simp only [Finset.mem_filter, Finset.mem_univ, true_and]
    constructor
    · intro hi
      by_contra hne
      have hg := hgap i (by intro h0; exact hne (by rw [h0]; positivity))
      nlinarith [hpsd i]
    · intro hi; nlinarith [hpsd i]
  have h1 : countSV M hn 0 ≤ countSV M hn (θ - ε) := by
    unfold countSV count
    exact Finset.card_le_card fun i hi ↦ by
      simp only [Finset.mem_filter, Finset.mem_univ, true_and] at hi ⊢; nlinarith [hpsd i]
  exact le_antisymm ((countSV_le_add hn h hε (by linarith)).trans h0.le)
    (h1.trans (countSV_sub_le hn h hθ))

end Palace.Gap
