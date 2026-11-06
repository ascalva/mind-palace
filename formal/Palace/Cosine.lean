module

public import Palace.Cosine.Defs
public import Palace.Format

/-!
# Vectors stored in float16: the cosine error bound and the margin certificate (VEC-1)

Since 2026-10-31 the vector store holds its vectors as float16 (dn-vector-membership-store A4):
a float32 vector `y` from the embedder is stored as `round16 y`, each coordinate rounded to
binary16. Measured on this machine (lancedb 0.33.0), LanceDB scores a query against that column by
rounding the query to float16 too, and computes `1 − cosine` of the two float16 vectors in float32.
Two of those three roundings are modelled here; the float32 arithmetic of the distance kernel is a
stated hypothesis, a bound `γ` on its error.

* `abs_rn16_sub_le`: rounding moves a coordinate by at most `2⁻¹¹ · max |x| 2⁻¹⁴`;
* `norm_round16_sub_le`: so a vector moves by at most `2⁻¹¹ √(‖x‖² + d · 2⁻²⁸)`;
* `abs_cosine_sub_le`: a cosine moves by at most `2 ‖x − y‖ / (‖x‖ + ‖y‖)` when either vector
  moves from `x` to `y`, the inner-product form of Dunkl and Williams' inequality;
* `abs_cosine_round16_sub_le`: so float16 storage moves a cosine by at most `betaStore d ν`, about
  `2⁻¹¹` (`4.884e-4` for `d = 768`), for every vector of norm at least `ν`;
* `top_eq_of_margin`: if each score is within `β` of a true score and the members of a set `S`
  beat every non-member by more than `2β`, the true scores rank `S` strictly above the rest, and
  `S` is their only top set of its size;
* `top_unchanged`: the certificate the store computes. When the gap between the `k`-th and the
  `(k+1)`-th score exceeds `2 (betaStore + betaQuery + γ)`, the top `k` the store returns is the
  top `k` of the exact cosines between the query and the float32 vectors: float16 storage cannot
  have changed it.
-/

@[expose] public section

namespace Palace.Cosine

open Palace.Format

section Coordinate

/-- **VEC-1** Rounding to binary16 moves a real number by at most `2⁻¹¹ · max |x| 2⁻¹⁴`: relative
error `2⁻¹¹` in the normal range, half the subnormal spacing `2⁻²⁴` below it. -/
theorem abs_rn16_sub_le (x : ℝ) : |rn16 x - x| ≤ u16 * max |x| tau16 := by
  have h := abs_rnf_sub_le 11 (-24) x
  norm_num at h ⊢
  exact h

end Coordinate

section Vector

variable {ι : Type*} [Fintype ι]

/-- **VEC-1** Float16 storage moves a vector in `d` dimensions by at most
`2⁻¹¹ √(‖x‖² + d · 2⁻²⁸)`. -/
theorem norm_round16_sub_le (x : EuclideanSpace ℝ ι) :
    ‖round16 x - x‖ ≤ u16 * √(‖x‖ ^ 2 + Fintype.card ι * tau16 ^ 2) := by
  have hcoord : ∀ i, (rn16 (x i) - x i) ^ 2 ≤ u16 ^ 2 * (x i ^ 2 + tau16 ^ 2) := by
    intro i
    have h := abs_rn16_sub_le (x i)
    have hm : max |x i| tau16 ^ 2 ≤ x i ^ 2 + tau16 ^ 2 := by
      rcases le_total |x i| tau16 with h' | h'
      · rw [max_eq_right h']; nlinarith [sq_nonneg (x i)]
      · rw [max_eq_left h', sq_abs]; nlinarith [sq_nonneg tau16]
    calc (rn16 (x i) - x i) ^ 2 = |rn16 (x i) - x i| ^ 2 := (sq_abs _).symm
      _ ≤ (u16 * max |x i| tau16) ^ 2 := by gcongr
      _ = u16 ^ 2 * max |x i| tau16 ^ 2 := by ring
      _ ≤ u16 ^ 2 * (x i ^ 2 + tau16 ^ 2) := by gcongr
  have hsq : ‖round16 x - x‖ ^ 2 ≤ u16 ^ 2 * (‖x‖ ^ 2 + Fintype.card ι * tau16 ^ 2) := by
    rw [EuclideanSpace.norm_sq_eq, EuclideanSpace.norm_sq_eq]
    calc ∑ i, ‖(round16 x - x).ofLp i‖ ^ 2 = ∑ i, (rn16 (x i) - x i) ^ 2 := by
          refine Finset.sum_congr rfl fun i _ ↦ ?_
          rw [Real.norm_eq_abs, sq_abs]
          rfl
      _ ≤ ∑ i, u16 ^ 2 * (x i ^ 2 + tau16 ^ 2) := Finset.sum_le_sum fun i _ ↦ hcoord i
      _ = u16 ^ 2 * (∑ i, ‖x.ofLp i‖ ^ 2 + Fintype.card ι * tau16 ^ 2) := by
          rw [← Finset.mul_sum, Finset.sum_add_distrib, Finset.sum_const, Finset.card_univ,
            nsmul_eq_mul]
          congr 2
          refine Finset.sum_congr rfl fun i _ ↦ ?_
          rw [Real.norm_eq_abs, sq_abs]
  calc ‖round16 x - x‖ = √(‖round16 x - x‖ ^ 2) := (Real.sqrt_sq (norm_nonneg _)).symm
    _ ≤ √(u16 ^ 2 * (‖x‖ ^ 2 + Fintype.card ι * tau16 ^ 2)) := Real.sqrt_le_sqrt hsq
    _ = u16 * √(‖x‖ ^ 2 + Fintype.card ι * tau16 ^ 2) := by
      rw [Real.sqrt_mul (by positivity), Real.sqrt_sq (by positivity)]

end Vector

section Perturbation

variable {F : Type*} [NormedAddCommGroup F] [InnerProductSpace ℝ F]

theorem abs_cosine_le_one (q x : F) : |cosine q x| ≤ 1 := by
  rw [cosine, abs_div, abs_mul, abs_norm, abs_norm]
  rcases eq_or_ne (‖q‖ * ‖x‖) 0 with h | h
  · rw [h, div_zero]; exact zero_le_one
  · exact (div_le_one (lt_of_le_of_ne (by positivity) (Ne.symm h))).2 (abs_real_inner_le_norm q x)

theorem cosine_comm (q x : F) : cosine q x = cosine x q := by
  rw [cosine, cosine, real_inner_comm, mul_comm]

/-- **VEC-1** Moving either vector from `x` to `y` moves a cosine by at most
`2 ‖x − y‖ / (‖x‖ + ‖y‖)`: Cauchy and Schwarz, and the inner-product form of Dunkl and Williams'
inequality `‖x/‖x‖ − y/‖y‖‖ ≤ 2 ‖x − y‖ / (‖x‖ + ‖y‖)`. -/
theorem abs_cosine_sub_le (q x y : F) :
    |cosine q x - cosine q y| ≤ 2 * ‖x - y‖ / (‖x‖ + ‖y‖) := by
  have hR : 0 ≤ 2 * ‖x - y‖ / (‖x‖ + ‖y‖) := by positivity
  rcases eq_or_ne q 0 with rfl | hq
  · simpa [cosine] using hR
  rcases eq_or_ne x 0 with rfl | hx
  · rcases eq_or_ne y 0 with rfl | hy
    · simp [cosine]
    · have h2 : 2 * ‖(0 : F) - y‖ / (‖(0 : F)‖ + ‖y‖) = 2 := by
        rw [zero_sub, norm_neg, norm_zero, zero_add, mul_div_assoc,
          div_self (norm_ne_zero_iff.2 hy), mul_one]
      have h0 : cosine q (0 : F) = 0 := by simp [cosine]
      have h1 := abs_cosine_le_one q y
      rw [h2, h0, zero_sub, abs_neg]
      linarith
  rcases eq_or_ne y 0 with rfl | hy
  · have h2 : 2 * ‖x - 0‖ / (‖x‖ + ‖(0 : F)‖) = 2 := by
      rw [sub_zero, norm_zero, add_zero, mul_div_assoc, div_self (norm_ne_zero_iff.2 hx),
        mul_one]
    have h0 : cosine q (0 : F) = 0 := by simp [cosine]
    have h1 := abs_cosine_le_one q x
    rw [h2, h0, sub_zero]
    linarith
  set a := ‖x‖ with ha_def
  set b := ‖y‖ with hb_def
  set n := ‖q‖ with hn_def
  have ha : 0 < a := norm_pos_iff.2 hx
  have hb : 0 < b := norm_pos_iff.2 hy
  have hn : 0 < n := norm_pos_iff.2 hq
  set s := inner ℝ x y with hs_def
  have hs : -(a * b) ≤ s := (abs_le.1 (abs_real_inner_le_norm x y)).1
  have hdiff : cosine q x - cosine q y = inner ℝ q (b • x - a • y) / (n * (a * b)) := by
    simp only [cosine, inner_sub_right, real_inner_smul_right, ← ha_def, ← hb_def, ← hn_def]
    field_simp
  have hv : ‖b • x - a • y‖ ^ 2 = 2 * (a * b) * (a * b - s) := by
    rw [norm_sub_sq_real, norm_smul, norm_smul, real_inner_smul_left, real_inner_smul_right,
      Real.norm_eq_abs, Real.norm_eq_abs, abs_of_pos ha, abs_of_pos hb, ← ha_def, ← hb_def,
      ← hs_def]
    ring
  have hxy : ‖x - y‖ ^ 2 = a ^ 2 - 2 * s + b ^ 2 := by
    rw [norm_sub_sq_real, ← ha_def, ← hb_def, ← hs_def]
  have hkey : ‖b • x - a • y‖ * (a + b) ≤ 2 * (a * b) * ‖x - y‖ := by
    rw [← pow_le_pow_iff_left₀ (by positivity) (by positivity) two_ne_zero, mul_pow, mul_pow, hv,
      hxy]
    nlinarith [mul_nonneg (mul_nonneg ha.le hb.le) (mul_nonneg (by linarith : 0 ≤ a * b + s)
      (sq_nonneg (a - b)))]
  rw [hdiff, abs_div, abs_of_pos (by positivity : 0 < n * (a * b))]
  calc |inner ℝ q (b • x - a • y)| / (n * (a * b)) ≤ n * ‖b • x - a • y‖ / (n * (a * b)) := by
        gcongr; exact abs_real_inner_le_norm _ _
    _ = ‖b • x - a • y‖ / (a * b) := by rw [mul_div_mul_left _ _ hn.ne']
    _ ≤ 2 * ‖x - y‖ / (a + b) := by
        rw [div_le_div_iff₀ (by positivity) (by positivity)]
        linarith

/-- **VEC-1** Scoring with `q'` in place of the query `q` moves a cosine by at most
`betaQuery q q'`; the store computes it from the query and its float16 rounding. -/
theorem abs_cosine_sub_query (x q q' : F) : |cosine q' x - cosine q x| ≤ betaQuery q q' := by
  rw [cosine_comm q' x, cosine_comm q x, betaQuery, add_comm]
  exact abs_cosine_sub_le x q' q

end Perturbation

section Storage

variable {ι : Type*} [Fintype ι]

/-- **VEC-1** Float16 storage moves the cosine between any query and a vector of norm at least `ν`
by at most `betaStore d ν = 2η / (2 − η)`, `η = 2⁻¹¹ √(1 + d · 2⁻²⁸ / ν²)`. -/
theorem abs_cosine_round16_sub_le (q x : EuclideanSpace ℝ ι) {ν : ℝ} (hν : 0 < ν)
    (hx : ν ≤ ‖x‖) (hη : eta (Fintype.card ι) ν < 2) :
    |cosine q (round16 x) - cosine q x| ≤ betaStore (Fintype.card ι) ν := by
  set d := Fintype.card ι
  set A := ‖x‖ with hA_def
  set E := ‖round16 x - x‖ with hE_def
  set η := eta d ν with hη_def
  have hA : 0 < A := hν.trans_le hx
  have hη0 : 0 ≤ η := by rw [hη_def, eta]; positivity
  -- the vector moves by at most `η A`
  have hE : E ≤ η * A := by
    refine (norm_round16_sub_le x).trans ?_
    have hroot : √(A ^ 2 + d * tau16 ^ 2) = A * √(1 + d * tau16 ^ 2 / A ^ 2) := by
      rw [← Real.sqrt_sq hA.le, ← Real.sqrt_mul (sq_nonneg A), Real.sqrt_sq hA.le]
      congr 1
      field_simp
    rw [← hA_def, hroot, hη_def, eta]
    have : √(1 + d * tau16 ^ 2 / A ^ 2) ≤ √(1 + d * tau16 ^ 2 / ν ^ 2) := by
      gcongr
    calc u16 * (A * √(1 + d * tau16 ^ 2 / A ^ 2)) = u16 * √(1 + d * tau16 ^ 2 / A ^ 2) * A := by
          ring
      _ ≤ u16 * √(1 + d * tau16 ^ 2 / ν ^ 2) * A := by gcongr
  have hE0 : 0 ≤ E := norm_nonneg _
  have hlow : A - E ≤ ‖round16 x‖ := by
    have := norm_sub_norm_le x (round16 x)
    rw [norm_sub_rev] at this
    linarith
  have hden : 0 < 2 * A - E := by nlinarith
  refine (abs_cosine_sub_le q (round16 x) x).trans ?_
  rw [← hE_def, ← hA_def]
  calc 2 * E / (‖round16 x‖ + A) ≤ 2 * E / (2 * A - E) :=
        div_le_div_of_nonneg_left (by positivity) hden (by linarith)
    _ ≤ betaStore d ν := by
        rw [betaStore, ← hη_def, div_le_div_iff₀ hden (by linarith)]
        nlinarith

end Storage

section Margin

/-- **VEC-1** The margin certificate. If every score `s j` is within `β` of the true score `t j`,
and the members of `S` beat every non-member by more than `2β`, then under the true scores every
member still beats every non-member, and `S` is their only top set of its size. -/
theorem top_eq_of_margin {κ : Type*} {s t : κ → ℝ} {β : ℝ} (h : ∀ j, |s j - t j| ≤ β)
    {S : Finset κ} (hm : ∀ i ∈ S, ∀ j ∉ S, s j + 2 * β < s i) :
    (∀ i ∈ S, ∀ j ∉ S, t j < t i) ∧ ∀ T : Finset κ, T.card = S.card → IsTop t T → T = S := by
  have hlt : ∀ i ∈ S, ∀ j ∉ S, t j < t i := by
    intro i hi j hj
    have h1 := abs_le.1 (h i)
    have h2 := abs_le.1 (h j)
    have := hm i hi j hj
    linarith [h1.1, h1.2, h2.1, h2.2]
  refine ⟨hlt, fun T hcard hT ↦ ?_⟩
  by_contra hne
  obtain ⟨i, hiS, hiT⟩ : ∃ i ∈ S, i ∉ T := by
    by_contra h'
    push Not at h'
    exact hne (Finset.eq_of_subset_of_card_le h' hcard.le).symm
  obtain ⟨j, hjT, hjS⟩ : ∃ j ∈ T, j ∉ S := by
    by_contra h'
    push Not at h'
    exact hne (Finset.eq_of_subset_of_card_le h' hcard.ge)
  exact absurd (hT j hjT i hiT) (not_le.2 (hlt i hiS j hjS))

variable {ι : Type*} [Fintype ι]

/-- **VEC-1** The certificate the store computes. Let each stored vector be the float16 rounding
of a float32 vector `y j` of norm at least `ν`, let the store score with `q'` in place of the
query `q`, and let each computed score `s j` be within `γ` of the cosine of `q'` and the stored
vector. When the members of `S` beat every non-member by more than
`2 (betaStore d ν + betaQuery q q' + γ)`, the exact cosines between `q` and the `y j` rank `S`
strictly above the rest, and `S` is their only top set of its size: float16 storage cannot have
changed it. -/
theorem top_unchanged {κ : Type*} {y : κ → EuclideanSpace ℝ ι} {q q' : EuclideanSpace ℝ ι}
    {s : κ → ℝ} {γ ν : ℝ} (hν : 0 < ν) (hy : ∀ j, ν ≤ ‖y j‖)
    (hη : eta (Fintype.card ι) ν < 2) (hs : ∀ j, |s j - cosine q' (round16 (y j))| ≤ γ)
    {S : Finset κ}
    (hm : ∀ i ∈ S, ∀ j ∉ S,
      s j + 2 * (betaStore (Fintype.card ι) ν + betaQuery q q' + γ) < s i) :
    (∀ i ∈ S, ∀ j ∉ S, cosine q (y j) < cosine q (y i)) ∧
      ∀ T : Finset κ, T.card = S.card → IsTop (fun j ↦ cosine q (y j)) T → T = S := by
  refine top_eq_of_margin (t := fun j ↦ cosine q (y j)) (fun j ↦ ?_) hm
  have h1 := hs j
  have h2 := abs_cosine_sub_query (round16 (y j)) q q'
  have h3 := abs_cosine_round16_sub_le q (y j) hν (hy j) hη
  calc |s j - cosine q (y j)|
      ≤ |s j - cosine q' (round16 (y j))| + |cosine q' (round16 (y j)) - cosine q (y j)| :=
        abs_sub_le _ _ _
    _ ≤ |s j - cosine q' (round16 (y j))| + (|cosine q' (round16 (y j)) -
          cosine q (round16 (y j))| + |cosine q (round16 (y j)) - cosine q (y j)|) := by
        gcongr; exact abs_sub_le _ _ _
    _ ≤ betaStore (Fintype.card ι) ν + betaQuery q q' + γ := by linarith

end Margin

end Palace.Cosine
