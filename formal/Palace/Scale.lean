module

public import Mathlib.Algebra.Order.Field.GeomSum
public import Palace.Dynamics
public import Palace.Scale.Defs

/-!
# Scale and attribution

The design theorems of `docs/design-notes/dn-scale-and-attribution.md` (Palace only, no Spec
rows: no code relies on them yet).

* SCL-1, the estimation threshold: the time average of a mean-zero field under the lazy walk
  `1 − εL` over a window of `T` steps has energy at most `((1/T) Σ_{n<T} (1 − εγ)^n)²` times the
  field's, so at most `‖x‖² / (T ε γ)²`: the window must span many relaxation times `1/(εγ)`,
  and precision `δ` needs `T ≥ ‖x‖ / (ε γ δ)`.
* SCL-2, scale separation: with the kept modes' eigenvalues at most `ν` and the dropped modes'
  at least `μ`, the dropped part's energy relative to the kept part's falls by `e^{−2(μ−ν)t}`
  under the heat kernel, so with a gap `g = μ − ν > 0` the `k`-mode description explains all but
  `ε` of what remains once `t ≥ log(R/ε) / (2g)`, `R` the initial ratio; the discrete twin under
  the lazy walk. The control: when every eigenvalue is the same (the identity), the share never
  changes, so no time separates the scales.
* SCL-3, attribution: the Shapley value, the average over every ordering of the marginal
  contribution of a source to the sources before it, is efficient, symmetric, attributes nothing
  to a null source and is additive; it is the only attribution with the four (every score is a
  combination of unanimity games with its Harsanyi dividends as coefficients, and the axioms pin
  an attribution on each unanimity game), and it equals the Harsanyi dividend formula
  `Σ_{T ∋ i} c_T / |T|`. Leave-one-out agrees with it on scores with constant marginals and
  disagrees in general: two redundant sources, either sufficient, each leave-one-out `0` while
  each Shapley value is half (the shape of the Rayleigh family's `loo_confirms_nothing`).
-/

@[expose] public section

open Matrix Finset

namespace Palace.Scale

open Palace.Dynamics

/-! ### SCL-1 The time average over a window -/

section Window

variable {V : Type*} [Fintype V] [DecidableEq V]

/-- The time average on a mode: the operator's powers average to the geometric sum of the mode's
multiplier. -/
theorem timeAverage_dotProduct_mode {M : Matrix V V ℝ} (hM : M.IsHermitian) {N : Matrix V V ℝ}
    (hN : N.IsHermitian) {g : V → ℝ} (hg : ∀ j, N *ᵥ mode hM j = g j • mode hM j) (T : ℕ)
    (x : V → ℝ) (j : V) :
    timeAverage N T x ⬝ᵥ mode hM j = 1 / (T : ℝ) * (∑ n ∈ range T, g j ^ n) * (x ⬝ᵥ mode hM j) := by
  rw [timeAverage, smul_dotProduct, sum_dotProduct, smul_eq_mul, mul_assoc, Finset.sum_mul]
  congr 1
  refine sum_congr rfl fun n _ ↦ ?_
  rw [dotProduct_comm, dotProduct_mulVec_symm (hN.pow n), pow_mulVec_mode hM hg, smul_dotProduct,
    smul_eq_mul, dotProduct_comm]

/-- SCL-1 The energy of the time average: when every mode `x` lives on has a multiplier in
`[0, ρ]`, `‖avg‖² ≤ ((1/T) Σ_{n<T} ρ^n)² ‖x‖²`. -/
theorem timeAverage_energy_le {M : Matrix V V ℝ} (hM : M.IsHermitian) {N : Matrix V V ℝ}
    (hN : N.IsHermitian) {g : V → ℝ} (hg : ∀ j, N *ᵥ mode hM j = g j • mode hM j) (T : ℕ)
    (x : V → ℝ) {ρ : ℝ} (hρ : ∀ j, x ⬝ᵥ mode hM j ≠ 0 → 0 ≤ g j ∧ g j ≤ ρ) :
    timeAverage N T x ⬝ᵥ timeAverage N T x ≤
      (1 / (T : ℝ) * ∑ n ∈ range T, ρ ^ n) ^ 2 * (x ⬝ᵥ x) := by
  rw [dotProduct_eq_sum_modes hM, dotProduct_eq_sum_modes hM x x, Finset.mul_sum]
  refine sum_le_sum fun j _ ↦ ?_
  rw [timeAverage_dotProduct_mode hM hN hg, ← sq, ← sq]
  by_cases h : x ⬝ᵥ mode hM j = 0
  · simp [h]
  · obtain ⟨h0, h1⟩ := hρ j h
    rw [mul_pow]
    have hs : (1 / (T : ℝ) * ∑ n ∈ range T, g j ^ n) ^ 2 ≤
        (1 / (T : ℝ) * ∑ n ∈ range T, ρ ^ n) ^ 2 :=
      pow_le_pow_left₀ (mul_nonneg (by positivity) (sum_nonneg fun n _ ↦ pow_nonneg h0 n))
        (mul_le_mul_of_nonneg_left (sum_le_sum fun n _ ↦ pow_le_pow_left₀ h0 h1 n)
          (by positivity)) 2
    exact mul_le_mul_of_nonneg_right hs (sq_nonneg _)

/-- SCL-1 Under the lazy walk `1 − εL` on a connected support with gap `γ`, with `ε λ_j ≤ 1` on
every eigenvalue, the time average of a mean-zero field over `T` steps has energy at most
`((1/T) Σ_{n<T} (1 − εγ)^n)² ‖x‖²`. -/
theorem lazy_timeAverage_energy_le {A : Matrix V V ℝ} (hA : A.IsSymm) (hw : ∀ i j, 0 ≤ A i j)
    (hc : (support A).Connected) {γ ε : ℝ} (hε : 0 ≤ ε)
    (hγ : ∀ j, (isHermitian_lap A hA).eigenvalues j ≠ 0 →
      γ ≤ (isHermitian_lap A hA).eigenvalues j)
    (hup : ∀ j, ε * (isHermitian_lap A hA).eigenvalues j ≤ 1) {x : V → ℝ} (hx : x ⬝ᵥ 1 = 0)
    (T : ℕ) :
    timeAverage (1 - ε • lap A) T x ⬝ᵥ timeAverage (1 - ε • lap A) T x ≤
      (1 / (T : ℝ) * ∑ n ∈ range T, (1 - ε * γ) ^ n) ^ 2 * (x ⬝ᵥ x) := by
  have hN : (1 - ε • lap A).IsHermitian := by
    rw [IsHermitian, conjTranspose_eq_transpose_of_trivial, transpose_sub, transpose_one,
      transpose_smul, transpose_eq_of_isHermitian (isHermitian_lap A hA)]
  refine timeAverage_energy_le (isHermitian_lap A hA) hN (one_sub_smul_mulVec_mode _ ε) T x
    fun j hj ↦ ?_
  have hj0 : (isHermitian_lap A hA).eigenvalues j ≠ 0 :=
    fun h0 ↦ hj (dotProduct_mode_eq_zero hA hw hc hx h0)
  exact ⟨by linarith [hup j], by linarith [mul_le_mul_of_nonneg_left (hγ j hj0) hε]⟩

/-- The geometric sum is at most `1 / (1 − ρ)`, for `0 ≤ ρ < 1`. -/
theorem sum_pow_le_inv_one_sub {ρ : ℝ} (h0 : 0 ≤ ρ) (h1 : ρ < 1) (T : ℕ) :
    ∑ n ∈ range T, ρ ^ n ≤ 1 / (1 - ρ) := by
  have h := geom_sum_Ico_le_of_lt_one (m := 0) (n := T) h0 h1
  rwa [← Finset.range_eq_Ico, pow_zero] at h

/-- SCL-1 The estimation threshold: the energy of the time average is at most `‖x‖² / (T ε γ)²`,
so a window of `T` steps estimates the mean to within `‖x‖ / (T ε γ)`: `T ε γ` is the number of
relaxation times the window spans. -/
theorem lazy_timeAverage_energy_le_window {A : Matrix V V ℝ} (hA : A.IsSymm)
    (hw : ∀ i j, 0 ≤ A i j) (hc : (support A).Connected) {γ ε : ℝ} (hε : 0 ≤ ε)
    (hγ : ∀ j, (isHermitian_lap A hA).eigenvalues j ≠ 0 →
      γ ≤ (isHermitian_lap A hA).eigenvalues j)
    (hup : ∀ j, ε * (isHermitian_lap A hA).eigenvalues j ≤ 1) (hεγ : 0 < ε * γ)
    (hεγ1 : ε * γ ≤ 1) {x : V → ℝ} (hx : x ⬝ᵥ 1 = 0) {T : ℕ} (hT : 0 < T) :
    timeAverage (1 - ε • lap A) T x ⬝ᵥ timeAverage (1 - ε • lap A) T x ≤
      (1 / ((T : ℝ) * (ε * γ))) ^ 2 * (x ⬝ᵥ x) := by
  refine (lazy_timeAverage_energy_le hA hw hc hε hγ hup hx T).trans
    (mul_le_mul_of_nonneg_right ?_ (dotProduct_self_star_nonneg x))
  have hT' : (0 : ℝ) < T := by exact_mod_cast hT
  refine pow_le_pow_left₀ (by positivity) ?_ 2
  calc 1 / (T : ℝ) * ∑ n ∈ range T, (1 - ε * γ) ^ n
      ≤ 1 / (T : ℝ) * (1 / (1 - (1 - ε * γ))) :=
        mul_le_mul_of_nonneg_left (sum_pow_le_inv_one_sub (by linarith) (by linarith) T)
          (by positivity)
    _ = 1 / ((T : ℝ) * (ε * γ)) := by
        rw [sub_sub_cancel, one_div_mul_one_div, one_div]

/-- SCL-1 The window a precision needs: once `T ≥ ‖x‖ / (ε γ δ)`, the time average is within
`δ` of the mean, `‖avg‖² ≤ δ²`. The window spans `‖x‖ / δ` relaxation times. -/
theorem lazy_timeAverage_precision {A : Matrix V V ℝ} (hA : A.IsSymm) (hw : ∀ i j, 0 ≤ A i j)
    (hc : (support A).Connected) {γ ε : ℝ} (hε : 0 ≤ ε)
    (hγ : ∀ j, (isHermitian_lap A hA).eigenvalues j ≠ 0 →
      γ ≤ (isHermitian_lap A hA).eigenvalues j)
    (hup : ∀ j, ε * (isHermitian_lap A hA).eigenvalues j ≤ 1) (hεγ : 0 < ε * γ)
    (hεγ1 : ε * γ ≤ 1) {x : V → ℝ} (hx : x ⬝ᵥ 1 = 0) {δ : ℝ} (hδ : 0 < δ) {T : ℕ} (hT : 0 < T)
    (hwin : Real.sqrt (x ⬝ᵥ x) / (ε * γ * δ) ≤ T) :
    timeAverage (1 - ε • lap A) T x ⬝ᵥ timeAverage (1 - ε • lap A) T x ≤ δ ^ 2 := by
  refine (lazy_timeAverage_energy_le_window hA hw hc hε hγ hup hεγ hεγ1 hx hT).trans ?_
  have hT' : (0 : ℝ) < T := by exact_mod_cast hT
  have hxx : 0 ≤ x ⬝ᵥ x := dotProduct_self_star_nonneg x
  have hs : x ⬝ᵥ x = Real.sqrt (x ⬝ᵥ x) ^ 2 := (Real.sq_sqrt hxx).symm
  have hle : Real.sqrt (x ⬝ᵥ x) ≤ (T : ℝ) * (ε * γ) * δ := by
    rw [div_le_iff₀ (by positivity)] at hwin
    linarith
  rw [hs, ← mul_pow, one_div_mul_eq_div]
  refine pow_le_pow_left₀ (by positivity) ?_ 2
  rw [div_le_iff₀ (by positivity)]
  linarith

end Window

/-! ### SCL-2 Scale separation -/

section Separation

variable {V : Type*} [Fintype V] [DecidableEq V] {M : Matrix V V ℝ} (hM : M.IsHermitian)

/-- The component of the projection on a mode: `f`'s on a kept mode, zero on a dropped one. -/
theorem modeProj_dotProduct_mode (S : Finset V) (f : V → ℝ) (j : V) :
    modeProj hM S f ⬝ᵥ mode hM j = if j ∈ S then f ⬝ᵥ mode hM j else 0 := by
  rw [modeProj, sum_dotProduct]
  simp only [smul_dotProduct, smul_eq_mul, mode_dotProduct_mode, mul_ite, mul_one, mul_zero,
    Finset.sum_ite_eq']

/-- The heat kernel decays no faster than the largest eigenvalue a field lives on: for `t ≥ 0`
and `ν` at least every such eigenvalue, `e^{−2νt} ‖x‖² ≤ ‖H_t x‖²`. -/
theorem heat_energy_ge (x : V → ℝ) {t : ℝ} (ht : 0 ≤ t) {ν : ℝ}
    (hν : ∀ j, x ⬝ᵥ mode hM j ≠ 0 → hM.eigenvalues j ≤ ν) :
    Real.exp (-(2 * ν * t)) * (x ⬝ᵥ x) ≤ (heat M t *ᵥ x) ⬝ᵥ (heat M t *ᵥ x) := by
  rw [← dotProduct_mulVec_symm (isHermitian_heat t) x (heat M t *ᵥ x), mulVec_mulVec,
    ← heat_add, ← two_mul, heat, dotProduct_cfc_mulVec hM, dotProduct_eq_sum_modes hM x x,
    Finset.mul_sum]
  refine sum_le_sum fun j _ ↦ ?_
  by_cases h : x ⬝ᵥ mode hM j = 0
  · simp [h]
  · rw [← sq]
    refine mul_le_mul_of_nonneg_right (Real.exp_le_exp.2 ?_) (sq_nonneg _)
    nlinarith [hν j h]

/-- The heat kernel's energy is exact when every mode a field lives on has the same eigenvalue:
`‖H_t x‖² = e^{−2μt} ‖x‖²`. -/
theorem heat_energy_eq (x : V → ℝ) (t : ℝ) {μ : ℝ}
    (hμ : ∀ j, x ⬝ᵥ mode hM j ≠ 0 → hM.eigenvalues j = μ) :
    (heat M t *ᵥ x) ⬝ᵥ (heat M t *ᵥ x) = Real.exp (-(2 * μ * t)) * (x ⬝ᵥ x) := by
  rw [← dotProduct_mulVec_symm (isHermitian_heat t) x (heat M t *ᵥ x), mulVec_mulVec,
    ← heat_add, ← two_mul, heat, dotProduct_cfc_mulVec hM, dotProduct_eq_sum_modes hM x x,
    Finset.mul_sum]
  refine sum_congr rfl fun j _ ↦ ?_
  by_cases h : x ⬝ᵥ mode hM j = 0
  · simp [h]
  · rw [hμ j h, ← sq]
    ring_nf

/-- The kept part decays no faster than the slowest kept rate: for `ν` at least every kept
eigenvalue, `e^{−2νt} ‖P_S f‖² ≤ ‖H_t P_S f‖²`. -/
theorem heat_modeProj_energy_ge (S : Finset V) (f : V → ℝ) {t : ℝ} (ht : 0 ≤ t) {ν : ℝ}
    (hν : ∀ j ∈ S, hM.eigenvalues j ≤ ν) :
    Real.exp (-(2 * ν * t)) * (modeProj hM S f ⬝ᵥ modeProj hM S f) ≤
      (heat M t *ᵥ modeProj hM S f) ⬝ᵥ (heat M t *ᵥ modeProj hM S f) := by
  refine heat_energy_ge hM _ ht fun j hj ↦ ?_
  rw [modeProj_dotProduct_mode] at hj
  by_cases h : j ∈ S
  · exact hν j h
  · simp [h] at hj

/-- SCL-2 Scale separation: with the dropped eigenvalues at least `μ` and the kept ones at most
`ν`, the dropped part's energy relative to the kept part's falls by `e^{−2(μ−ν)t}`:
`‖H_t (f − P_S f)‖² ‖P_S f‖² ≤ e^{−2(μ−ν)t} ‖f − P_S f‖² ‖H_t P_S f‖²`. -/
theorem scale_separation (S : Finset V) (f : V → ℝ) {t : ℝ} (ht : 0 ≤ t) {μ ν : ℝ}
    (hμ : ∀ j ∉ S, μ ≤ hM.eigenvalues j) (hν : ∀ j ∈ S, hM.eigenvalues j ≤ ν) :
    (heat M t *ᵥ (f - modeProj hM S f)) ⬝ᵥ (heat M t *ᵥ (f - modeProj hM S f)) *
        (modeProj hM S f ⬝ᵥ modeProj hM S f) ≤
      Real.exp (-(2 * (μ - ν) * t)) *
        (((f - modeProj hM S f) ⬝ᵥ (f - modeProj hM S f)) *
          ((heat M t *ᵥ modeProj hM S f) ⬝ᵥ (heat M t *ᵥ modeProj hM S f))) := by
  have h1 := heat_sub_modeProj_le hM S f ht hμ
  have h2 := heat_modeProj_energy_ge hM S f ht hν
  have hb : 0 ≤ (f - modeProj hM S f) ⬝ᵥ (f - modeProj hM S f) := dotProduct_self_star_nonneg _
  have hc : 0 ≤ modeProj hM S f ⬝ᵥ modeProj hM S f := dotProduct_self_star_nonneg _
  have he : Real.exp (-(2 * μ * t)) = Real.exp (-(2 * (μ - ν) * t)) * Real.exp (-(2 * ν * t)) := by
    rw [← Real.exp_add]; ring_nf
  calc (heat M t *ᵥ (f - modeProj hM S f)) ⬝ᵥ (heat M t *ᵥ (f - modeProj hM S f)) *
        (modeProj hM S f ⬝ᵥ modeProj hM S f)
      ≤ Real.exp (-(2 * μ * t)) * ((f - modeProj hM S f) ⬝ᵥ (f - modeProj hM S f)) *
          (modeProj hM S f ⬝ᵥ modeProj hM S f) := mul_le_mul_of_nonneg_right h1 hc
    _ = Real.exp (-(2 * (μ - ν) * t)) * ((f - modeProj hM S f) ⬝ᵥ (f - modeProj hM S f)) *
          (Real.exp (-(2 * ν * t)) * (modeProj hM S f ⬝ᵥ modeProj hM S f)) := by
        rw [he]; ring
    _ ≤ Real.exp (-(2 * (μ - ν) * t)) * ((f - modeProj hM S f) ⬝ᵥ (f - modeProj hM S f)) *
          ((heat M t *ᵥ modeProj hM S f) ⬝ᵥ (heat M t *ᵥ modeProj hM S f)) :=
        mul_le_mul_of_nonneg_left h2 (mul_nonneg (Real.exp_nonneg _) hb)
    _ = _ := by ring

/-- SCL-2 The time: with a gap `g = μ − ν > 0` between the dropped and the kept eigenvalues and
a kept part that is not zero, once `t ≥ log(R/ε) / (2g)` for `R` the initial ratio of the
dropped energy to the kept, the `S`-mode description explains all but `ε` of what remains:
`‖H_t (f − P_S f)‖² ≤ ε ‖H_t P_S f‖²`. -/
theorem scale_separation_time (S : Finset V) (f : V → ℝ) {μ ν ε t : ℝ} (hg : 0 < μ - ν)
    (hμ : ∀ j ∉ S, μ ≤ hM.eigenvalues j) (hν : ∀ j ∈ S, hM.eigenvalues j ≤ ν) (hε : 0 < ε)
    (hP : 0 < modeProj hM S f ⬝ᵥ modeProj hM S f) (ht0 : 0 ≤ t)
    (ht : Real.log ((f - modeProj hM S f) ⬝ᵥ (f - modeProj hM S f) /
      (modeProj hM S f ⬝ᵥ modeProj hM S f) / ε) / (2 * (μ - ν)) ≤ t) :
    (heat M t *ᵥ (f - modeProj hM S f)) ⬝ᵥ (heat M t *ᵥ (f - modeProj hM S f)) ≤
      ε * ((heat M t *ᵥ modeProj hM S f) ⬝ᵥ (heat M t *ᵥ modeProj hM S f)) := by
  set a := (heat M t *ᵥ (f - modeProj hM S f)) ⬝ᵥ (heat M t *ᵥ (f - modeProj hM S f))
  set b := (f - modeProj hM S f) ⬝ᵥ (f - modeProj hM S f)
  set c := modeProj hM S f ⬝ᵥ modeProj hM S f
  set d := (heat M t *ᵥ modeProj hM S f) ⬝ᵥ (heat M t *ᵥ modeProj hM S f)
  have hsep : a * c ≤ Real.exp (-(2 * (μ - ν) * t)) * (b * d) := scale_separation hM S f ht0 hμ hν
  have ha : 0 ≤ a := dotProduct_self_star_nonneg _
  have hb : 0 ≤ b := dotProduct_self_star_nonneg _
  have hd : 0 ≤ d := dotProduct_self_star_nonneg _
  -- the exponential factor brings the initial ratio under `ε`
  have hkey : Real.exp (-(2 * (μ - ν) * t)) * b ≤ ε * c := by
    rcases hb.lt_or_eq with hb0 | hb0
    · have hR : 0 < b / c / ε := by positivity
      rw [div_le_iff₀ (by positivity)] at ht
      have h1 := (Real.log_le_iff_le_exp hR).1 ht
      have hprod : Real.exp (-(2 * (μ - ν) * t)) * Real.exp (t * (2 * (μ - ν))) = 1 := by
        rw [← Real.exp_add]
        have : -(2 * (μ - ν) * t) + t * (2 * (μ - ν)) = 0 := by ring
        rw [this, Real.exp_zero]
      have h2 : Real.exp (-(2 * (μ - ν) * t)) * (b / c / ε) ≤ 1 :=
        calc Real.exp (-(2 * (μ - ν) * t)) * (b / c / ε)
            ≤ Real.exp (-(2 * (μ - ν) * t)) * Real.exp (t * (2 * (μ - ν))) :=
              mul_le_mul_of_nonneg_left h1 (Real.exp_nonneg _)
          _ = 1 := hprod
      have h3 : Real.exp (-(2 * (μ - ν) * t)) * (b / c / ε) * (ε * c) ≤ ε * c :=
        mul_le_of_le_one_left (by positivity) h2
      calc Real.exp (-(2 * (μ - ν) * t)) * b
          = Real.exp (-(2 * (μ - ν) * t)) * (b / c / ε) * (ε * c) := by
            field_simp
        _ ≤ ε * c := h3
    · rw [← hb0, mul_zero]
      positivity
  have h4 : a * c ≤ ε * d * c :=
    calc a * c ≤ Real.exp (-(2 * (μ - ν) * t)) * b * d := by rw [mul_assoc]; exact hsep
      _ ≤ ε * c * d := mul_le_mul_of_nonneg_right hkey hd
      _ = ε * d * c := by ring
  exact le_of_mul_le_mul_right h4 hP

/-- Every eigenvalue of the identity is `1`: on each mode, `φ_j = λ_j φ_j`. -/
theorem eigenvalues_one (j : V) : (isHermitian_one (n := V) (α := ℝ)).eigenvalues j = 1 := by
  have h : mode isHermitian_one j =
      (isHermitian_one (n := V) (α := ℝ)).eigenvalues j • mode isHermitian_one j := by
    have := (isHermitian_one (n := V) (α := ℝ)).mulVec_eigenvectorBasis j
    rwa [one_mulVec] at this
  have h2 := congrArg (· ⬝ᵥ mode isHermitian_one j) h
  simp only [smul_dotProduct, smul_eq_mul, mode_dotProduct_mode, ↓reduceIte, mul_one] at h2
  exact h2.symm

/-- SCL-2, the control: when the dropped and the kept eigenvalues coincide there is no gap and
no time separates the scales. On the identity, two equal eigenvalues straddle every cut, and the
dropped part's share of the energy is the same at every time:
`‖H_t (f − P_S f)‖² ‖P_S f‖² = ‖f − P_S f‖² ‖H_t P_S f‖²`. -/
theorem no_gap_no_separation (S : Finset V) (f : V → ℝ) (t : ℝ) :
    (heat (1 : Matrix V V ℝ) t *ᵥ (f - modeProj isHermitian_one S f)) ⬝ᵥ
        (heat 1 t *ᵥ (f - modeProj isHermitian_one S f)) *
        (modeProj isHermitian_one S f ⬝ᵥ modeProj isHermitian_one S f) =
      ((f - modeProj isHermitian_one S f) ⬝ᵥ (f - modeProj isHermitian_one S f)) *
        ((heat 1 t *ᵥ modeProj isHermitian_one S f) ⬝ᵥ
          (heat 1 t *ᵥ modeProj isHermitian_one S f)) := by
  rw [heat_energy_eq isHermitian_one _ t (μ := 1) fun j _ ↦ eigenvalues_one j,
    heat_energy_eq isHermitian_one _ t (μ := 1) fun j _ ↦ eigenvalues_one j]
  ring

/-- SCL-2, the control read as a refusal: on the identity, if some time makes the dropped part at
most `ε` of the kept part, it already was at time zero, so no time improves the separation. -/
theorem no_gap_no_time (S : Finset V) (f : V → ℝ) {ε t : ℝ}
    (h : (heat (1 : Matrix V V ℝ) t *ᵥ (f - modeProj isHermitian_one S f)) ⬝ᵥ
        (heat 1 t *ᵥ (f - modeProj isHermitian_one S f)) ≤
      ε * ((heat 1 t *ᵥ modeProj isHermitian_one S f) ⬝ᵥ
        (heat 1 t *ᵥ modeProj isHermitian_one S f))) :
    (f - modeProj isHermitian_one S f) ⬝ᵥ (f - modeProj isHermitian_one S f) ≤
      ε * (modeProj isHermitian_one S f ⬝ᵥ modeProj isHermitian_one S f) := by
  have e1 := heat_energy_eq isHermitian_one (f - modeProj isHermitian_one S f) t (μ := 1)
    fun j _ ↦ eigenvalues_one j
  have e2 := heat_energy_eq isHermitian_one (modeProj isHermitian_one S f) t (μ := 1)
    fun j _ ↦ eigenvalues_one j
  rw [e1, e2] at h
  have hexp : 0 < Real.exp (-(2 * 1 * t)) := Real.exp_pos _
  nlinarith

end Separation

/-! ### SCL-2 The discrete twin: scale separation under the lazy walk -/

section LazySeparation

variable {V : Type*} [Fintype V] [DecidableEq V] {M : Matrix V V ℝ} (hM : M.IsHermitian)

/-- Geometric decay from below: when `ρ ≤ |g j|` on every mode `x` lives on,
`ρ^{2n} ‖x‖² ≤ ‖N^n x‖²`. -/
theorem pow_energy_ge {N : Matrix V V ℝ} (hN : N.IsHermitian) {g : V → ℝ}
    (hg : ∀ j, N *ᵥ mode hM j = g j • mode hM j) (x : V → ℝ) {ρ : ℝ} (hρ0 : 0 ≤ ρ)
    (hρ : ∀ j, x ⬝ᵥ mode hM j ≠ 0 → ρ ≤ |g j|) (n : ℕ) :
    ρ ^ (2 * n) * (x ⬝ᵥ x) ≤ (N ^ n *ᵥ x) ⬝ᵥ (N ^ n *ᵥ x) := by
  rw [dotProduct_self_mulVec_of_modes hM (hN.pow n) (pow_mulVec_mode hM hg n) x,
    dotProduct_eq_sum_modes hM x x, Finset.mul_sum]
  refine sum_le_sum fun j _ ↦ ?_
  by_cases h : x ⬝ᵥ mode hM j = 0
  · simp [h]
  · have e : (g j ^ n) ^ 2 = |g j| ^ (2 * n) := by
      rw [← sq_abs, abs_pow, ← pow_mul, mul_comm]
    rw [e, ← sq]
    exact mul_le_mul_of_nonneg_right (pow_le_pow_left₀ hρ0 (hρ j h) _) (sq_nonneg _)

/-- SCL-2, discrete: under an operator that multiplies the dropped modes by at most `ρ₁` in
absolute value and the kept modes by at least `ρ₂`, after `n` steps
`ρ₂^{2n} ‖N^n (f − P_S f)‖² ‖P_S f‖² ≤ ρ₁^{2n} ‖f − P_S f‖² ‖N^n P_S f‖²`: the dropped share
falls by `(ρ₁/ρ₂)²` a step. -/
theorem scale_separation_pow {N : Matrix V V ℝ} (hN : N.IsHermitian) {g : V → ℝ}
    (hg : ∀ j, N *ᵥ mode hM j = g j • mode hM j) (S : Finset V) (f : V → ℝ) {ρ₁ ρ₂ : ℝ}
    (hρ₁ : 0 ≤ ρ₁) (hρ₂ : 0 ≤ ρ₂) (h₁ : ∀ j ∉ S, |g j| ≤ ρ₁) (h₂ : ∀ j ∈ S, ρ₂ ≤ |g j|)
    (n : ℕ) :
    ρ₂ ^ (2 * n) * ((N ^ n *ᵥ (f - modeProj hM S f)) ⬝ᵥ (N ^ n *ᵥ (f - modeProj hM S f)) *
        (modeProj hM S f ⬝ᵥ modeProj hM S f)) ≤
      ρ₁ ^ (2 * n) * (((f - modeProj hM S f) ⬝ᵥ (f - modeProj hM S f)) *
        ((N ^ n *ᵥ modeProj hM S f) ⬝ᵥ (N ^ n *ᵥ modeProj hM S f))) := by
  have h1 : (N ^ n *ᵥ (f - modeProj hM S f)) ⬝ᵥ (N ^ n *ᵥ (f - modeProj hM S f)) ≤
      ρ₁ ^ (2 * n) * ((f - modeProj hM S f) ⬝ᵥ (f - modeProj hM S f)) := by
    refine pow_energy_le hM hN hg _ (fun j hj ↦ ?_) n
    rw [sub_modeProj_dotProduct_mode] at hj
    by_cases h : j ∈ S
    · simp [h] at hj
    · exact h₁ j h
  have h2 : ρ₂ ^ (2 * n) * (modeProj hM S f ⬝ᵥ modeProj hM S f) ≤
      (N ^ n *ᵥ modeProj hM S f) ⬝ᵥ (N ^ n *ᵥ modeProj hM S f) := by
    refine pow_energy_ge hM hN hg _ hρ₂ (fun j hj ↦ ?_) n
    rw [modeProj_dotProduct_mode] at hj
    by_cases h : j ∈ S
    · exact h₂ j h
    · simp [h] at hj
  have hb : 0 ≤ (f - modeProj hM S f) ⬝ᵥ (f - modeProj hM S f) := dotProduct_self_star_nonneg _
  have hc : 0 ≤ modeProj hM S f ⬝ᵥ modeProj hM S f := dotProduct_self_star_nonneg _
  have hρ1 : 0 ≤ ρ₁ ^ (2 * n) := pow_nonneg hρ₁ _
  calc ρ₂ ^ (2 * n) * ((N ^ n *ᵥ (f - modeProj hM S f)) ⬝ᵥ (N ^ n *ᵥ (f - modeProj hM S f)) *
        (modeProj hM S f ⬝ᵥ modeProj hM S f))
      ≤ ρ₂ ^ (2 * n) * (ρ₁ ^ (2 * n) * ((f - modeProj hM S f) ⬝ᵥ (f - modeProj hM S f)) *
          (modeProj hM S f ⬝ᵥ modeProj hM S f)) :=
        mul_le_mul_of_nonneg_left (mul_le_mul_of_nonneg_right h1 hc) (pow_nonneg hρ₂ _)
    _ = ρ₁ ^ (2 * n) * ((f - modeProj hM S f) ⬝ᵥ (f - modeProj hM S f)) *
          (ρ₂ ^ (2 * n) * (modeProj hM S f ⬝ᵥ modeProj hM S f)) := by ring
    _ ≤ ρ₁ ^ (2 * n) * ((f - modeProj hM S f) ⬝ᵥ (f - modeProj hM S f)) *
          ((N ^ n *ᵥ modeProj hM S f) ⬝ᵥ (N ^ n *ᵥ modeProj hM S f)) :=
        mul_le_mul_of_nonneg_left h2 (mul_nonneg hρ1 hb)
    _ = _ := by ring

end LazySeparation

/-! ### SCL-3 Attribution: the Shapley value and its axioms -/

section Attribution

variable {α K : Type*} [Fintype α] [DecidableEq α]

/-! #### The chain of an ordering, and efficiency -/

/-- The sources ordered strictly before position `k`: the `k`-th set of the chain
`∅ ⊂ … ⊂ univ` an ordering runs through. -/
def chain (σ : Ordering α) (k : ℕ) : Finset α := univ.filter fun j ↦ (σ j).val < k

omit [DecidableEq α] in
theorem chain_zero (σ : Ordering α) : chain σ 0 = ∅ := by
  ext j
  simp [chain]

omit [DecidableEq α] in
theorem chain_card (σ : Ordering α) : chain σ (Fintype.card α) = univ := by
  ext j
  simp [chain]

omit [DecidableEq α] in
/-- The sources before the one at position `k` are the chain's `k`-th set. -/
theorem pred_symm (σ : Ordering α) (k : Fin (Fintype.card α)) :
    pred σ (σ.symm k) = chain σ k.val := by
  ext j
  simp [pred, chain]

/-- Adding the source at position `k` to the sources before it gives the chain's next set. -/
theorem insert_pred_symm (σ : Ordering α) (k : Fin (Fintype.card α)) :
    insert (σ.symm k) (pred σ (σ.symm k)) = chain σ (k.val + 1) := by
  ext j
  simp only [mem_insert, pred_symm, chain, mem_filter, mem_univ, true_and, Equiv.eq_symm_apply,
    Fin.ext_iff]
  omega

/-- Along one ordering the marginal contributions telescope: they sum to what the full set adds
over the empty one. -/
theorem sum_marginal_pred [Ring K] (σ : Ordering α) (v : Finset α → K) :
    ∑ i, marginal v (pred σ i) i = v univ - v ∅ := by
  rw [← Fintype.sum_equiv σ.symm (fun k ↦ marginal v (pred σ (σ.symm k)) (σ.symm k)) _
    fun k ↦ rfl]
  simp only [marginal]
  have h : ∀ k : Fin (Fintype.card α),
      v (insert (σ.symm k) (pred σ (σ.symm k))) - v (pred σ (σ.symm k)) =
        v (chain σ (k.val + 1)) - v (chain σ k.val) := fun k ↦ by
    rw [insert_pred_symm, pred_symm]
  simp only [h]
  rw [Fin.sum_univ_eq_sum_range (fun k ↦ v (chain σ (k + 1)) - v (chain σ k))]
  rw [Finset.sum_range_sub (fun k ↦ v (chain σ k)) (Fintype.card α), chain_card, chain_zero]

/-- **SCL-3** The Shapley value is efficient: the attributions sum to what the full set of
sources adds over none of them. -/
theorem shapley_efficient [Field K] [CharZero K] : Efficient (shapley (α := α) (K := K)) := by
  intro v
  simp only [shapley]
  rw [← Finset.sum_div, Finset.sum_comm]
  simp only [sum_marginal_pred, Finset.sum_const, Finset.card_univ, nsmul_eq_mul,
    Fintype.card_equiv (Fintype.equivFin α)]
  have h : ((Fintype.card α).factorial : K) ≠ 0 := by
    exact_mod_cast Nat.factorial_ne_zero _
  field_simp

/-- **SCL-3** A null source, one that changes no score, is attributed nothing. -/
theorem shapley_nullPlayer [Field K] : NullPlayer (shapley (α := α) (K := K)) := by
  intro v i h
  simp [shapley, marginal, h]

omit [Fintype α] in
theorem marginal_add [Ring K] (v w : Finset α → K) (S : Finset α) (i : α) :
    marginal (v + w) S i = marginal v S i + marginal w S i := by
  simp only [marginal, Pi.add_apply]
  abel

/-- **SCL-3** The Shapley value is additive over scores. -/
theorem shapley_additive [Field K] : Additive (shapley (α := α) (K := K)) := by
  intro v w
  funext i
  simp only [shapley, Pi.add_apply, marginal_add, Finset.sum_add_distrib, add_div]

/-! #### Symmetry, through the swap of two sources -/

/-- Composing with the swap of `i` and `j` is a bijection on orderings, its own inverse. -/
def swapOrd (i j : α) : Ordering α ≃ Ordering α where
  toFun σ := (Equiv.swap i j).trans σ
  invFun σ := (Equiv.swap i j).trans σ
  left_inv σ := by
    change (Equiv.swap i j).trans ((Equiv.swap i j).trans σ) = σ
    rw [← Equiv.trans_assoc, Equiv.swap_swap, Equiv.refl_trans]
  right_inv σ := by
    change (Equiv.swap i j).trans ((Equiv.swap i j).trans σ) = σ
    rw [← Equiv.trans_assoc, Equiv.swap_swap, Equiv.refl_trans]

/-- Under the swapped ordering, the sources before `i` are the sources before `j`, with `i`
replaced by `j` when `i` was among them. -/
theorem pred_swap (σ : Ordering α) {i j : α} (hij : i ≠ j) :
    pred ((Equiv.swap i j).trans σ) i =
      if i ∈ pred σ j then insert j ((pred σ j).erase i) else pred σ j := by
  ext k
  simp only [pred, mem_filter, mem_univ, true_and]
  simp only [Equiv.trans_apply, Equiv.swap_apply_left]
  by_cases hi : σ i < σ j
  · simp only [hi, ↓reduceIte, mem_insert, mem_erase, mem_filter, mem_univ, true_and]
    rcases eq_or_ne k i with rfl | hk
    · simp [Equiv.swap_apply_left, hij]
    rcases eq_or_ne k j with rfl | hk'
    · simp [Equiv.swap_apply_right, hi]
    · rw [Equiv.swap_apply_of_ne_of_ne hk hk']
      simp [hk, hk']
  · simp only [hi, ↓reduceIte, mem_filter, mem_univ, true_and]
    rcases eq_or_ne k i with rfl | hk
    · simp [Equiv.swap_apply_left, hi]
    rcases eq_or_ne k j with rfl | hk'
    · simp [Equiv.swap_apply_right, hi]
    · rw [Equiv.swap_apply_of_ne_of_ne hk hk']

/-- Two sources that add the same to every configuration holding neither have the same marginal
contribution under an ordering and its swap. -/
theorem marginal_swap [Ring K] (σ : Ordering α) {v : Finset α → K} {i j : α} (hij : i ≠ j)
    (hs : ∀ S, i ∉ S → j ∉ S → v (insert i S) = v (insert j S)) :
    marginal v (pred ((Equiv.swap i j).trans σ) i) i = marginal v (pred σ j) j := by
  rw [pred_swap σ hij]
  have hj : j ∉ pred σ j := by simp [pred]
  split_ifs with hi
  · have hiQ : i ∉ (pred σ j).erase i := Finset.notMem_erase i _
    have hjQ : j ∉ (pred σ j).erase i := fun h ↦ hj (Finset.mem_of_mem_erase h)
    simp only [marginal]
    conv_rhs => rw [← Finset.insert_erase hi]
    rw [Finset.insert_comm j i, hs _ hiQ hjQ]
  · simp only [marginal]
    rw [hs _ hi hj]

/-- **SCL-3** The Shapley value is symmetric: two sources that add the same to every
configuration holding neither are attributed the same. -/
theorem shapley_symmetric [Field K] : Symmetric (shapley (α := α) (K := K)) := by
  intro v i j hs
  by_cases hij : i = j
  · subst hij
    rfl
  simp only [shapley]
  congr 1
  exact (Fintype.sum_equiv (swapOrd i j) _ _ fun σ ↦ (marginal_swap σ hij hs).symm).symm

/-! #### Uniqueness: the unanimity games and the Harsanyi dividends -/

section Unanimity

variable [Field K] {ψ : Attribution α K}

omit [Fintype α] in
theorem unanimity_insert_of_notMem (T : Finset α) {i : α} (hi : i ∉ T) (S : Finset α) :
    unanimity (K := K) T (insert i S) = unanimity T S := by
  simp only [unanimity, Finset.subset_insert_iff_of_notMem hi]

omit [Fintype α] in
/-- On a scaled unanimity game, a source outside `T` is null. -/
theorem attribution_unanimity_notMem (hN : NullPlayer ψ) (c : K) (T : Finset α) {i : α}
    (hi : i ∉ T) : ψ (c • unanimity T) i = 0 :=
  hN _ i fun S ↦ by simp only [Pi.smul_apply, unanimity_insert_of_notMem T hi]

omit [Fintype α] in
/-- On a scaled unanimity game, two sources inside `T` are symmetric. -/
theorem attribution_unanimity_mem (hS : Symmetric ψ) (c : K) (T : Finset α) {i j : α}
    (hi : i ∈ T) (hj : j ∈ T) : ψ (c • unanimity T) i = ψ (c • unanimity T) j := by
  refine hS _ i j fun S hiS hjS ↦ ?_
  by_cases hij : i = j
  · subst hij
    rfl
  have h1 : ¬ T ⊆ insert i S := fun h ↦ by
    rcases Finset.mem_insert.1 (h hj) with h' | h'
    · exact hij h'.symm
    · exact hjS h'
  have h2 : ¬ T ⊆ insert j S := fun h ↦ by
    rcases Finset.mem_insert.1 (h hi) with h' | h'
    · exact hij h'
    · exact hiS h'
  simp only [Pi.smul_apply, unanimity, h1, h2, ite_false]

/-- On a scaled unanimity game of a nonempty `T`, an efficient attribution sums to the scale. -/
theorem sum_attribution_unanimity (hE : Efficient ψ) (c : K) {T : Finset α} (hT : T.Nonempty) :
    ∑ i, ψ (c • unanimity T) i = c := by
  rw [hE]
  simp [Pi.smul_apply, unanimity, hT.ne_empty]

/-- **SCL-3** The axioms pin an attribution on every scaled unanimity game: `c / |T|` to each
source of `T`, nothing to the others. -/
theorem attribution_unanimity [CharZero K] (hE : Efficient ψ) (hS : Symmetric ψ)
    (hN : NullPlayer ψ) (c : K) (T : Finset α) (i : α) :
    ψ (c • unanimity T) i = if i ∈ T then c / T.card else 0 := by
  split_ifs with hi
  · have hT : T.Nonempty := ⟨i, hi⟩
    have hsum := sum_attribution_unanimity hE c hT
    rw [← Finset.sum_subset (Finset.subset_univ T)
      (fun j _ hj ↦ attribution_unanimity_notMem hN c T hj),
      Finset.sum_congr rfl (fun j hj ↦ attribution_unanimity_mem hS c T hj hi), Finset.sum_const,
      nsmul_eq_mul] at hsum
    have hc : (T.card : K) ≠ 0 := by exact_mod_cast (Finset.card_pos.2 hT).ne'
    rw [eq_div_iff hc, mul_comm]
    exact hsum
  · exact attribution_unanimity_notMem hN c T hi

omit [Fintype α] in
/-- The inclusion–exclusion sum over the sets between `R` and `S`: `Σ_{R ⊆ T ⊆ S} (−1)^{|T|−|R|}`
is `1` when `S = R` and `0` otherwise. -/
theorem sum_powerset_filter_neg_one_pow {S R : Finset α} (hR : R ⊆ S) :
    ∑ T ∈ S.powerset.filter (fun T ↦ R ⊆ T), (-1 : K) ^ (T.card - R.card) =
      if S = R then 1 else 0 := by
  have key : ∑ T ∈ S.powerset.filter (fun T ↦ R ⊆ T), (-1 : K) ^ (T.card - R.card) =
      ∑ U ∈ (S \ R).powerset, (-1 : K) ^ U.card := by
    refine Finset.sum_nbij' (fun T ↦ T \ R) (fun U ↦ R ∪ U) ?_ ?_ ?_ ?_ ?_
    · intro T hT
      simp only [mem_filter, mem_powerset] at hT ⊢
      exact Finset.sdiff_subset_sdiff hT.1 le_rfl
    · intro U hU
      simp only [mem_powerset] at hU
      simp only [mem_filter, mem_powerset]
      exact ⟨Finset.union_subset hR (hU.trans Finset.sdiff_subset), Finset.subset_union_left⟩
    · intro T hT
      simp only [mem_filter, mem_powerset] at hT
      exact Finset.union_sdiff_of_subset hT.2
    · intro U hU
      simp only [mem_powerset] at hU
      exact Finset.union_sdiff_cancel_left
        (Finset.disjoint_of_subset_right hU Finset.disjoint_sdiff)
    · intro T hT
      simp only [mem_filter, mem_powerset] at hT
      rw [Finset.card_sdiff_of_subset hT.2]
  rw [key]
  have h := sum_powerset_neg_one_pow_card (x := S \ R)
  have h' : ∑ U ∈ (S \ R).powerset, (-1 : K) ^ U.card =
      ((∑ U ∈ (S \ R).powerset, (-1 : ℤ) ^ U.card : ℤ) : K) := by
    push_cast
    rfl
  rw [h', h]
  by_cases hSR : S = R
  · simp [hSR]
  · have hne : S \ R ≠ ∅ := fun h0 ↦
      hSR (Finset.Subset.antisymm (Finset.sdiff_eq_empty_iff_subset.1 h0) hR)
    simp [hne, hSR]

/-- **SCL-3** Every score is the combination of the unanimity games with its Harsanyi dividends
as coefficients: `Σ_T c_T u_T(S) = v(S)`. -/
theorem sum_harsanyi_unanimity (v : Finset α → K) (S : Finset α) :
    ∑ T, harsanyi v T * unanimity T S = v S := by
  have hp : (univ.filter fun T : Finset α ↦ T ⊆ S) = S.powerset := by
    ext T
    simp
  have h1 : ∑ T, harsanyi v T * unanimity T S = ∑ T ∈ S.powerset, harsanyi v T := by
    rw [← hp, Finset.sum_filter]
    refine sum_congr rfl fun T _ ↦ ?_
    simp only [unanimity, mul_ite, mul_one, mul_zero]
  rw [h1]
  simp only [harsanyi]
  rw [Finset.sum_comm' (t' := S.powerset) (s' := fun R ↦ S.powerset.filter fun T ↦ R ⊆ T)
    (fun T R ↦ by
      simp only [mem_powerset, mem_filter]
      constructor
      · rintro ⟨h1, h2⟩
        exact ⟨⟨h1, h2⟩, h2.trans h1⟩
      · rintro ⟨⟨h1, h2⟩, _⟩
        exact ⟨h1, h2⟩)]
  simp only [← Finset.sum_mul]
  rw [Finset.sum_congr rfl fun R hR ↦ by
    rw [sum_powerset_filter_neg_one_pow (Finset.mem_powerset.1 hR)]]
  simp [Finset.sum_ite_eq]

/-- The decomposition as functions: `v = Σ_T c_T • u_T`. -/
theorem eq_sum_harsanyi_smul_unanimity (v : Finset α → K) :
    v = ∑ T, harsanyi v T • unanimity T := by
  funext S
  rw [Finset.sum_apply]
  simp only [Pi.smul_apply, smul_eq_mul]
  exact (sum_harsanyi_unanimity v S).symm

omit [Fintype α] [DecidableEq α] in
theorem additive_zero (hA : Additive ψ) : ψ 0 = 0 := by
  have h := hA 0 0
  rw [add_zero] at h
  exact add_eq_left.1 h.symm

omit [Fintype α] [DecidableEq α] in
/-- An additive attribution is additive over finite sums of scores. -/
theorem additive_sum (hA : Additive ψ) {ι : Type*} (s : Finset ι) (f : ι → Finset α → K) :
    ψ (∑ x ∈ s, f x) = ∑ x ∈ s, ψ (f x) := by
  classical
  induction s using Finset.induction_on with
  | empty => simp [additive_zero hA]
  | insert a s ha ih => rw [Finset.sum_insert ha, Finset.sum_insert ha, hA, ih]

/-- **SCL-3** Any attribution with the four axioms is the Harsanyi dividend formula:
`ψ v i = Σ_{T ∋ i} c_T / |T|`. -/
theorem attribution_eq_sum_harsanyi [CharZero K] (hE : Efficient ψ) (hS : Symmetric ψ)
    (hN : NullPlayer ψ) (hA : Additive ψ) (v : Finset α → K) (i : α) :
    ψ v i = ∑ T ∈ univ.filter (fun T ↦ i ∈ T), harsanyi v T / T.card := by
  conv_lhs => rw [eq_sum_harsanyi_smul_unanimity v]
  rw [additive_sum hA, Finset.sum_apply, Finset.sum_filter]
  exact sum_congr rfl fun T _ ↦ attribution_unanimity hE hS hN _ T i

/-- **SCL-3** The Shapley value is the Harsanyi dividend formula. -/
theorem shapley_eq_sum_harsanyi [CharZero K] (v : Finset α → K) (i : α) :
    shapley v i = ∑ T ∈ univ.filter (fun T ↦ i ∈ T), harsanyi v T / T.card :=
  attribution_eq_sum_harsanyi shapley_efficient shapley_symmetric shapley_nullPlayer
    shapley_additive v i

/-- **SCL-3** Uniqueness: an attribution with the four axioms is the Shapley value. -/
theorem eq_shapley_of_axioms [CharZero K] (hE : Efficient ψ) (hS : Symmetric ψ)
    (hN : NullPlayer ψ) (hA : Additive ψ) : ψ = shapley := by
  funext v i
  rw [attribution_eq_sum_harsanyi hE hS hN hA, shapley_eq_sum_harsanyi]

end Unanimity

/-! #### Leave-one-out -/

section LeaveOneOut

variable [Field K]

/-- Leave-one-out is the marginal contribution of `i` to every other source. -/
theorem loo_eq_marginal (v : Finset α → K) (i : α) : loo v i = marginal v (univ.erase i) i := by
  simp [loo, marginal, Finset.insert_erase (mem_univ i)]

/-- On a score with constant marginals, every source's Shapley value is its marginal. -/
theorem shapley_eq_of_marginal_const [CharZero K] (v : Finset α → K) {a : α → K}
    (h : ∀ S i, i ∉ S → marginal v S i = a i) (i : α) : shapley v i = a i := by
  simp only [shapley]
  rw [Finset.sum_congr rfl (fun σ _ ↦ h _ i (by simp [pred])), Finset.sum_const,
    Finset.card_univ, Fintype.card_equiv (Fintype.equivFin α), nsmul_eq_mul]
  have hf : ((Fintype.card α).factorial : K) ≠ 0 := by
    exact_mod_cast Nat.factorial_ne_zero _
  field_simp

/-- **SCL-3** Leave-one-out agrees with the Shapley value on scores with constant marginals:
when every source adds the same whatever the others, removing it from the full set measures
its contribution. -/
theorem loo_eq_shapley_of_marginal_const [CharZero K] (v : Finset α → K) {a : α → K}
    (h : ∀ S i, i ∉ S → marginal v S i = a i) (i : α) : loo v i = shapley v i := by
  rw [loo_eq_marginal, h _ i (Finset.notMem_erase i univ), shapley_eq_of_marginal_const v h i]

end LeaveOneOut

namespace Witness

/-- Two sources, either sufficient: every nonempty configuration scores `1`. -/
def redundant : Finset (Fin 2) → ℚ := fun S ↦ if S = ∅ then 0 else 1

theorem univ_ne_empty : (univ : Finset (Fin 2)) ≠ ∅ := Finset.univ_nonempty.ne_empty

theorem erase_ne_empty (i : Fin 2) : (univ : Finset (Fin 2)).erase i ≠ ∅ := by
  fin_cases i
  · exact Finset.ne_empty_of_mem (a := (1 : Fin 2)) (by simp)
  · exact Finset.ne_empty_of_mem (a := (0 : Fin 2)) (by simp)

theorem redundant_empty : redundant ∅ = 0 := by simp [redundant]

theorem redundant_univ : redundant univ = 1 := by simp [redundant, univ_ne_empty]

/-- Each redundant source has Shapley value one half: the two are symmetric and the score they
carry together is `1`. -/
theorem shapley_redundant (i : Fin 2) : shapley redundant i = 1 / 2 := by
  have hsym : shapley redundant 0 = shapley redundant 1 :=
    shapley_symmetric _ 0 1 fun S _ _ ↦ by simp [redundant]
  have heff := shapley_efficient (α := Fin 2) (K := ℚ) redundant
  rw [Fin.sum_univ_two, redundant_empty, redundant_univ, sub_zero] at heff
  have h0 : shapley redundant 0 = 1 / 2 := by linarith
  have h1 : shapley redundant 1 = 1 / 2 := by linarith
  fin_cases i
  · exact h0
  · exact h1

/-- Each redundant source has leave-one-out `0`: the other one still carries the whole score. -/
theorem loo_redundant (i : Fin 2) : loo redundant i = 0 := by
  simp only [loo, redundant, univ_ne_empty, erase_ne_empty, ↓reduceIte, sub_self]

/-- **SCL-3, the control.** Leave-one-out confirms neither of two redundant sources, though
together they carry the whole score: it is not efficient, and it disagrees with the Shapley
value on both. The shape of the Rayleigh family's `loo_confirms_nothing`. -/
theorem loo_confirms_nothing :
    (∑ i, loo redundant i ≠ redundant univ - redundant ∅) ∧
      ∀ i, loo redundant i ≠ shapley redundant i := by
  refine ⟨?_, fun i ↦ ?_⟩
  · simp [loo_redundant, redundant_empty, redundant_univ]
  · rw [loo_redundant, shapley_redundant]
    norm_num

end Witness

end Attribution

end Palace.Scale
