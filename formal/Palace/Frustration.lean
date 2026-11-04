module

public import Palace.Frustration.Defs
public import Palace.Laplacian
public import Palace.Rayleigh

/-!
# The frustration lift: `sᵀ L̄ s = 2·frustrated(s)`, and the least eigenvalue under it

The limits program's L4 (`docs/brainstorms/limits-of-the-algebra.md`) conjectured
`λ_min(L̄) ≤ 4·w_max·frustration / n` and measured it on the live relation edges. It holds for a
reason sharper than the conjecture: the signed energy of any signing `s ∈ {±1}^V` is
`2·frustrated(s)` — four times the frustrated weight counted over unordered pairs — and
`sᵀ s = n`, so the Rayleigh quotient of the switching that balances all but the frustrated edges
is `4·F_w / n`, with `F_w` the weighted frustration index (FRU-1). Courant–Fischer's floor — some
eigenvalue lies under every Rayleigh quotient, proved here through the orthonormal eigenbasis —
carries the quotient to the spectrum: the least eigenvalue of `L̄` is at most `4·F_w / n`
(FRU-2), and `w_max · frustration ≥ F_w`. Design theorems (Palace only, no Spec rows):
`eval/frustration_lift.py` is the measurement, not a law of the code.
-/

@[expose] public section

open Matrix Finset
open scoped InnerProductSpace

namespace Palace.Frustration

variable {V : Type*} [Fintype V] [DecidableEq V]

/-! ### FRU-1 The signed energy of a signing is its frustrated weight -/

omit [Fintype V] [DecidableEq V] in
/-- A signing squares to one. -/
theorem sq_signing {s : V → ℝ} (hs : ∀ i, s i = 1 ∨ s i = -1) (i : V) : s i ^ 2 = 1 := by
  rcases hs i with h | h <;> rw [h] <;> norm_num

/-- FRU-1 The signed energy of a signing is twice its frustrated weight: with `sᵢ² = 1`, every
term of the signed energy identity (`two_mul_dotProduct_signedLap`) is `2|Aᵢⱼ| − 2 Aᵢⱼ sᵢ sⱼ`. -/
theorem dotProduct_signedLap_signing (A : Matrix V V ℝ) (hA : A.IsSymm) {s : V → ℝ}
    (hs : ∀ i, s i = 1 ∨ s i = -1) :
    s ⬝ᵥ (signedLap A *ᵥ s) = 2 * frustrated A s := by
  have h := two_mul_dotProduct_signedLap A hA s
  have e : ∑ i, ∑ j, (|A i j| * (s i ^ 2 + s j ^ 2) - 2 * A i j * s i * s j) =
      ∑ i, ∑ j, 4 * ((|A i j| - A i j * s i * s j) / 2) := by
    refine sum_congr rfl fun i _ ↦ sum_congr rfl fun j _ ↦ ?_
    rw [sq_signing hs i, sq_signing hs j]
    ring
  rw [e] at h
  simp only [← mul_sum] at h
  unfold frustrated
  linarith

omit [DecidableEq V] in
/-- A signing has `sᵀ s = |V|`. -/
theorem dotProduct_self_signing {s : V → ℝ} (hs : ∀ i, s i = 1 ∨ s i = -1) :
    s ⬝ᵥ s = Fintype.card V := by
  have h1 : ∀ i, s i * s i = 1 := fun i ↦ by rcases hs i with h | h <;> rw [h] <;> norm_num
  simp [dotProduct, h1]

/-- FRU-1, read as a Rayleigh quotient: a signing's quotient is `2·frustrated(s) / |V|`. -/
theorem rayleigh_signing (A : Matrix V V ℝ) (hA : A.IsSymm) {s : V → ℝ}
    (hs : ∀ i, s i = 1 ∨ s i = -1) :
    s ⬝ᵥ (signedLap A *ᵥ s) / (s ⬝ᵥ s) = 2 * frustrated A s / Fintype.card V := by
  rw [dotProduct_signedLap_signing A hA hs, dotProduct_self_signing hs]

/-! ### Courant–Fischer, the floor: some eigenvalue lies under every Rayleigh quotient -/

/-- **Courant–Fischer, the floor**: for a real symmetric `M` and any `x`, some eigenvalue `μ`
has `μ ‖x‖² ≤ xᵀ M x` — the least eigenvalue is at most every Rayleigh quotient. Through the
orthonormal eigenbasis: `xᵀ M x = Σⱼ λⱼ cⱼ²` and `‖x‖² = Σⱼ cⱼ²` for `cⱼ = ⟪vⱼ, x⟫`. -/
theorem exists_eigenvalue_mul_le_dotProduct [Nonempty V] {M : Matrix V V ℝ}
    (hM : M.IsHermitian) (x : V → ℝ) :
    ∃ j, hM.eigenvalues j * (x ⬝ᵥ x) ≤ x ⬝ᵥ (M *ᵥ x) := by
  obtain ⟨j₀, -, hj₀⟩ :=
    Set.exists_min_image Set.univ hM.eigenvalues Set.finite_univ Set.univ_nonempty
  refine ⟨j₀, ?_⟩
  have key : ∀ u v : V → ℝ,
      ⟪(WithLp.toLp 2 u : EuclideanSpace ℝ V), WithLp.toLp 2 v⟫_ℝ = u ⬝ᵥ v := by
    intro u v
    rw [EuclideanSpace.inner_eq_star_dotProduct, star_trivial, WithLp.ofLp_toLp,
      WithLp.ofLp_toLp, dotProduct_comm]
  have c_def : ∀ j, ⟪hM.eigenvectorBasis j, (WithLp.toLp 2 x : EuclideanSpace ℝ V)⟫_ℝ =
      x ⬝ᵥ WithLp.ofLp (hM.eigenvectorBasis j) := by
    intro j
    rw [EuclideanSpace.inner_eq_star_dotProduct, star_trivial, WithLp.ofLp_toLp]
  have hxx : x ⬝ᵥ x = ∑ j, (x ⬝ᵥ WithLp.ofLp (hM.eigenvectorBasis j)) *
      (x ⬝ᵥ WithLp.ofLp (hM.eigenvectorBasis j)) := by
    have h := hM.eigenvectorBasis.sum_inner_mul_inner (WithLp.toLp 2 x) (WithLp.toLp 2 x)
    rw [key] at h
    rw [← h]
    refine sum_congr rfl fun j _ ↦ ?_
    rw [real_inner_comm (hM.eigenvectorBasis j) (WithLp.toLp 2 x), c_def]
  have hxMx : x ⬝ᵥ (M *ᵥ x) = ∑ j, hM.eigenvalues j *
      ((x ⬝ᵥ WithLp.ofLp (hM.eigenvectorBasis j)) *
        (x ⬝ᵥ WithLp.ofLp (hM.eigenvectorBasis j))) := by
    have h := hM.eigenvectorBasis.sum_inner_mul_inner (WithLp.toLp 2 x) (WithLp.toLp 2 (M *ᵥ x))
    rw [key] at h
    rw [← h]
    refine sum_congr rfl fun j _ ↦ ?_
    rw [real_inner_comm (hM.eigenvectorBasis j) (WithLp.toLp 2 x), c_def,
      EuclideanSpace.inner_eq_star_dotProduct, star_trivial, WithLp.ofLp_toLp,
      dotProduct_comm (M *ᵥ x), dotProduct_mulVec_symm hM, hM.mulVec_eigenvectorBasis j,
      smul_dotProduct, smul_eq_mul, dotProduct_comm (WithLp.ofLp (hM.eigenvectorBasis j)) x]
    ring
  rw [hxx, hxMx, mul_sum]
  exact sum_le_sum fun j _ ↦
    mul_le_mul_of_nonneg_right (hj₀ j (Set.mem_univ j)) (mul_self_nonneg _)

/-! ### FRU-2 The lift is bounded by the frustration -/

/-- The signed Laplacian of a symmetric `A` is symmetric. -/
theorem isHermitian_signedLap (A : Matrix V V ℝ) (hA : A.IsSymm) :
    (signedLap A).IsHermitian := by
  rw [IsHermitian, conjTranspose_eq_transpose_of_trivial]
  simp only [signedLap, transpose_sub, diagonal_transpose, hA.eq]

/-- FRU-2 The frustration lift is bounded: some eigenvalue of `L̄` — so its least — is at most
`2·frustrated(s) / |V|` for every signing `s`, and so at most `4·F_w / n` for the best one: L4's
bound, machine-checked, with the weighted frustration in place of `w_max · frustration`. -/
theorem exists_eigenvalue_le_frustrated [Nonempty V] (A : Matrix V V ℝ) (hA : A.IsSymm)
    {s : V → ℝ} (hs : ∀ i, s i = 1 ∨ s i = -1) :
    ∃ j, (isHermitian_signedLap A hA).eigenvalues j ≤ 2 * frustrated A s / Fintype.card V := by
  obtain ⟨j, hj⟩ := exists_eigenvalue_mul_le_dotProduct (isHermitian_signedLap A hA) s
  refine ⟨j, ?_⟩
  rw [dotProduct_signedLap_signing A hA hs, dotProduct_self_signing hs] at hj
  have hn : (0 : ℝ) < Fintype.card V := by exact_mod_cast Fintype.card_pos
  rwa [le_div_iff₀ hn]

end Palace.Frustration
