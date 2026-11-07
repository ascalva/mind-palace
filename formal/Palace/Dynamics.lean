module

public import Mathlib.Analysis.Matrix.Normed
public import Mathlib.Analysis.SpecificLimits.Normed
public import Mathlib.Topology.UniformSpace.Matrix
public import Palace.Dynamics.Defs
public import Palace.Heat
public import Palace.Hodge
public import Palace.Rayleigh
public import Palace.Retrieval
public import Palace.Spectral
public import Palace.Transport

/-!
# The dynamics of an evolving graph

The design theorems of `docs/design-notes/dn-graph-dynamics.md` (Palace only, no Spec rows: no
code relies on them yet).

* DYN-1, the velocity: the displacement of a value over a window of cuts adds along the chain and
  is the sum of its steps; the edge field a changing potential induces is the gradient of the
  node velocity, so it has no curl and no harmonic part.
* DYN-2, the Neumann resolvent: in a complete normed ring, `Σ_k x^k = (1 − x)⁻¹` when `‖x‖ < 1`
  (Mathlib's geometric series), and for a matrix under the row-sum operator norm, so for every
  nonnegative matrix whose rows sum to at most `s < 1`: the killed walk's fundamental matrix is
  the sum over all walks, and the ripple of a shock is the resolvent applied to it. The tail after
  `n` terms is at most `s^n / (1 − s)` entrywise, and the partial sums approach from below. The
  control: a matrix with an eigenvalue `1` (rows summing to `1`) has a singular `1 − M` and
  divergent partial sums.
* DYN-3, HodgeRank: `s = L_w⁺ div_w Y` is a least-squares potential of the flow `Y` under the
  weights `w`; the residual is divergence-free; `s` is unique up to the kernel of `L_w`, which on
  a connected graph with positive weights is the constants.
* DYN-4, the modes: a function of a symmetric matrix acts on each eigenvector by the function of
  its eigenvalue; the heat kernel commutes with the projection onto any set of modes, and the
  dropped part decays at least as `e^{−μt}` for `μ` under the dropped eigenvalues; the energy of a
  field lying on modes above `μ` is at least `μ` times its norm (Courant–Fischer on the modes a
  field lives on).
* DYN-5, coarse-graining: the Laplacian of the quotient by a partition is `Pᵀ L P`, so the energy
  of a block-constant field is the quotient's energy of its block values; on a connected graph a
  block field orthogonal to the constants has at least the fine spectral gap as its Rayleigh
  quotient, so coarse-graining never lowers the gap; and the ripple commutes with a merge-free
  transport that carries every weight forward.
* DYN-6, mixing: a spectral gap as a Poincaré inequality, exactly a bound under the nonzero
  eigenvalues on a connected support; total variation against `L²` by `√N / 2`; the heat kernel
  and the lazy walk contracting every field orthogonal to the constants at the gap's rate. The
  shapes follow the switch-chain family of openai/math
  (`lean/ComparatorChallenges/SwitchChain.lean`, Apache 2.0), restated over the Laplacian's
  modes; nothing is copied.
-/

@[expose] public section

open Matrix Finset Filter Topology
open scoped InnerProductSpace

namespace Palace.Dynamics

/-! ### DYN-1 The velocity of a value -/

section Velocity

variable {V E : Type*} [AddCommGroup E]

/-- DYN-1 Velocity adds along the chain of cuts: the displacement from `a` to `c` is the
displacement from `a` to `b` plus that from `b` to `c`. -/
theorem velocity_add (x : ℕ → V → E) (a b c : ℕ) :
    velocity x a b + velocity x b c = velocity x a c := by
  funext v
  simp only [velocity, Pi.add_apply]
  abel

/-- DYN-1 The displacement over a window is the sum of its steps, version to version. -/
theorem velocity_eq_sum (x : ℕ → V → E) (a n : ℕ) :
    velocity x a (a + n) = ∑ k ∈ range n, velocity x (a + k) (a + k + 1) := by
  funext v
  simp only [velocity, Finset.sum_apply]
  have h := Finset.sum_range_sub (fun k ↦ x (a + k) v) n
  simp only [add_zero, add_assoc] at h ⊢
  exact h.symm

/-- DYN-1 The edge field a changing potential induces is the gradient of the velocity: the drop
across a citation changes by the difference of the ends' velocities. -/
theorem coboundary_velocity (x : ℕ → V → ℝ) (a b : ℕ) (u v : V) :
    Transport.coboundary (velocity x a b) u v =
      Transport.coboundary (x b) u v - Transport.coboundary (x a) u v := by
  simp only [Transport.coboundary, velocity]
  ring

end Velocity

/-- DYN-1 On a complex, the edge velocity of a potential flow is a gradient, so it is orthogonal
to every curl: a changing potential never makes circulation. -/
theorem grad_velocity_dot_curl {V E T : Type*} [Fintype V] [Fintype E] [Fintype T]
    {B₁ : Matrix V E ℝ} {B₂ : Matrix E T ℝ} (h : B₁ * B₂ = 0) (x : ℕ → V → ℝ) (a b : ℕ)
    (y : T → ℝ) : (B₁ᵀ *ᵥ velocity x a b) ⬝ᵥ (B₂ *ᵥ y) = 0 :=
  Hodge.grad_dot_curl h _ y

/-! ### DYN-2 The Neumann resolvent -/

section Neumann

/-- DYN-2 Mathlib's geometric series in a complete normed ring: when `‖x‖ < 1` the powers are
summable and their sum inverts `1 − x` on both sides. -/
theorem neumann_tsum {R : Type*} [NormedRing R] [CompleteSpace R] (x : R) (hx : ‖x‖ < 1) :
    Summable (fun k ↦ x ^ k) ∧ (1 - x) * ∑' k, x ^ k = 1 ∧ (∑' k, x ^ k) * (1 - x) = 1 :=
  ⟨summable_geometric_of_norm_lt_one hx, mul_neg_geom_series x hx, geom_series_mul_neg x hx⟩

variable {V : Type*} [Fintype V] [DecidableEq V]

attribute [local instance] Matrix.linftyOpNormedRing

/-- DYN-2 For a real matrix under the row-sum operator norm, the walk sum is the inverse:
`(1 − M)⁻¹ = Σ_k M^k` when `‖M‖ < 1`, the powers summable entrywise. The matrices are complete
under this norm because its uniform structure is the product's, which Lean checks by unfolding. -/
theorem inv_one_sub_eq_tsum (M : Matrix V V ℝ) (h : ‖M‖ < 1) :
    Summable (fun k ↦ M ^ k) ∧ (1 - M)⁻¹ = ∑' k, M ^ k := by
  let nr : NormedRing (Matrix V V ℝ) := Matrix.linftyOpNormedRing
  have : @CompleteSpace (Matrix V V ℝ) nr.toMetricSpace.toPseudoMetricSpace.toUniformSpace :=
    inferInstanceAs (CompleteSpace (V → V → ℝ))
  exact ⟨summable_geometric_of_norm_lt_one h,
    (Matrix.nonsing_inv_eq_ringInverse _).trans (geom_series_eq_inverse M h).symm⟩

/-- The row-sum operator norm of a nonnegative matrix is at most a bound on its row sums. -/
theorem linfty_opNorm_le_of_rows {M : Matrix V V ℝ} {s : ℝ} (hM : ∀ i j, 0 ≤ M i j)
    (hrow : ∀ i, ∑ j, M i j ≤ s) (hs : 0 ≤ s) : ‖M‖ ≤ s := by
  rw [Matrix.linfty_opNorm_def]
  have key : ∀ i, ((∑ j, ‖M i j‖₊ : NNReal) : ℝ) ≤ s := by
    intro i
    rw [NNReal.coe_sum]
    calc ∑ j, ((‖M i j‖₊ : NNReal) : ℝ) = ∑ j, M i j :=
          sum_congr rfl fun j _ ↦ by rw [coe_nnnorm, Real.norm_of_nonneg (hM i j)]
      _ ≤ s := hrow i
  have hsup : (univ.sup fun i ↦ ∑ j, ‖M i j‖₊ : NNReal) ≤ NNReal.mk s hs :=
    Finset.sup_le fun i _ ↦ by rw [← NNReal.coe_le_coe, NNReal.coe_mk]; exact key i
  simpa using NNReal.coe_le_coe.2 hsup

/-- DYN-2 For a nonnegative matrix whose rows sum to at most `s < 1`, the walk sum converges to
the inverse: RSP-1's resolvent is the sum over all walks, and `diffuse` computes it exactly. -/
theorem inv_one_sub_eq_tsum_of_rows {M : Matrix V V ℝ} {s : ℝ} (hM : ∀ i j, 0 ≤ M i j)
    (hrow : ∀ i, ∑ j, M i j ≤ s) (hs : s < 1) (hs0 : 0 ≤ s) : (1 - M)⁻¹ = ∑' k, M ^ k :=
  (inv_one_sub_eq_tsum M ((linfty_opNorm_le_of_rows hM hrow hs0).trans_lt hs)).2

/-- DYN-2 The fundamental matrix of the killed walk is the sum over all killed walks. -/
theorem fundamental_eq_tsum {w : Matrix V V ℝ} {β z : ℝ} (hw0 : ∀ i j, 0 ≤ w i j)
    (hw1 : ∀ i j, w i j ≤ 1) (hβ : 0 ≤ β) (hz0 : 0 ≤ z) (hz1 : z < 1) :
    Retrieval.fundamental w β z = ∑' k, Retrieval.killedWalk w β z ^ k :=
  inv_one_sub_eq_tsum_of_rows (Retrieval.killedWalk_nonneg hw0 hz0)
    (Retrieval.sum_killedWalk_le hw0 hw1 hβ hz0) hz1 hz0

/-- DYN-2 The ripple of a shock along a relation whose damped rows sum to at most `s < 1` is the
sum of the shock after every number of damped steps. -/
theorem ripple_eq_tsum {A : Matrix V V ℝ} {z s : ℝ} (hA : ∀ i j, 0 ≤ A i j) (hz : 0 ≤ z)
    (hrow : ∀ i, z * ∑ j, A i j ≤ s) (hs : s < 1) (hs0 : 0 ≤ s) (δ : V → ℝ) :
    ripple A z δ = (∑' k, (z • A) ^ k) *ᵥ δ := by
  unfold ripple
  rw [inv_one_sub_eq_tsum_of_rows (fun i j ↦ by simpa using mul_nonneg hz (hA i j))
    (fun i ↦ by simpa [Finset.mul_sum] using hrow i) hs hs0]

end Neumann

/-! ### DYN-2 The tail of the walk sum, entrywise -/

section Tail

variable {V : Type*} [Fintype V] [DecidableEq V] {M : Matrix V V ℝ} {s : ℝ}

/-- The powers of a nonnegative matrix are nonnegative. -/
theorem pow_apply_nonneg (hM : ∀ i j, 0 ≤ M i j) (n : ℕ) (i j : V) : 0 ≤ (M ^ n) i j := by
  induction n generalizing i j with
  | zero => simp [Matrix.one_apply]; split_ifs <;> norm_num
  | succ n ih =>
    rw [pow_succ, Matrix.mul_apply]
    exact sum_nonneg fun k _ ↦ mul_nonneg (ih i k) (hM k j)

/-- The rows of `M^n` sum to at most `s^n`. -/
theorem sum_pow_le (hM : ∀ i j, 0 ≤ M i j) (hrow : ∀ i, ∑ j, M i j ≤ s) (n : ℕ) (i : V) :
    ∑ j, (M ^ n) i j ≤ s ^ n := by
  induction n generalizing i with
  | zero => simp [Matrix.one_apply]
  | succ n ih =>
    have hs0 : 0 ≤ s := (sum_nonneg fun j _ ↦ hM i j).trans (hrow i)
    calc ∑ j, (M ^ (n + 1)) i j = ∑ k, (M ^ n) i k * ∑ j, M k j := by
          simp only [pow_succ, Matrix.mul_apply, Finset.mul_sum]
          rw [Finset.sum_comm]
      _ ≤ ∑ k, (M ^ n) i k * s :=
          sum_le_sum fun k _ ↦ mul_le_mul_of_nonneg_left (hrow k) (pow_apply_nonneg hM n i k)
      _ = (∑ k, (M ^ n) i k) * s := by rw [Finset.sum_mul]
      _ ≤ s ^ n * s := mul_le_mul_of_nonneg_right (ih i) hs0
      _ = s ^ (n + 1) := by rw [pow_succ]

/-- The rows of the walk sum `(1 − M)⁻¹` sum to at most `1 / (1 − s)`: at the row where the sum
is largest, `r ≤ 1 + s r`. -/
theorem sum_inv_le (hM : ∀ i j, 0 ≤ M i j) (hrow : ∀ i, ∑ j, M i j ≤ s) (hs : s < 1) (i : V) :
    ∑ j, (1 - M)⁻¹ i j ≤ 1 / (1 - s) := by
  have : Nonempty V := ⟨i⟩
  obtain ⟨m, hm⟩ := Finite.exists_max fun a ↦ ∑ j, (1 - M)⁻¹ a j
  refine (hm i).trans ?_
  have hZ : ∀ a b, 0 ≤ (1 - M)⁻¹ a b := Retrieval.inv_nonneg hM hrow hs
  have hr0 : 0 ≤ ∑ j, (1 - M)⁻¹ m j := sum_nonneg fun j _ ↦ hZ m j
  have e : ∑ j, (1 - M)⁻¹ m j = 1 + ∑ k, M m k * ∑ j, (1 - M)⁻¹ k j := by
    simp only [Retrieval.inv_apply_eq hM hrow hs m, Finset.sum_add_distrib, Finset.sum_ite_eq,
      Finset.mem_univ, ite_true, Finset.mul_sum]
    rw [Finset.sum_comm]
  have hle : ∑ k, M m k * ∑ j, (1 - M)⁻¹ k j ≤ s * ∑ j, (1 - M)⁻¹ m j :=
    calc ∑ k, M m k * ∑ j, (1 - M)⁻¹ k j ≤ ∑ k, M m k * ∑ j, (1 - M)⁻¹ m j :=
          sum_le_sum fun k _ ↦ mul_le_mul_of_nonneg_left (hm k) (hM m k)
      _ = (∑ k, M m k) * ∑ j, (1 - M)⁻¹ m j := by rw [Finset.sum_mul]
      _ ≤ s * ∑ j, (1 - M)⁻¹ m j := mul_le_mul_of_nonneg_right (hrow m) hr0
  rw [le_div_iff₀ (by linarith)]
  linarith

/-- The walk sum less its first `n` terms is `(1 − M)⁻¹ M^n`: the walks of at least `n` steps. -/
theorem inv_sub_neumann (hM : ∀ i j, 0 ≤ M i j) (hrow : ∀ i, ∑ j, M i j ≤ s) (hs : s < 1)
    (n : ℕ) : (1 - M)⁻¹ - neumann M n = (1 - M)⁻¹ * M ^ n := by
  have hu : IsUnit (1 - M).det := isUnit_iff_ne_zero.mpr (Retrieval.det_one_sub_ne_zero hM hrow hs)
  have h := mul_neg_geom_sum M n
  have h2 : neumann M n = (1 - M)⁻¹ * (1 - M ^ n) := by
    rw [neumann, ← h, Matrix.nonsing_inv_mul_cancel_left _ _ hu]
  rw [h2, Matrix.mul_sub, Matrix.mul_one]
  abel

/-- DYN-2 The tail bound: after `n` terms the walk sum is approached from below, and what is
left is at most `s^n / (1 − s)` entrywise. The cost of the resolvent is one solve; the cost of a
sum over walks to accuracy `ε` is `log ε / log s` terms, and the sum never overshoots. -/
theorem neumann_tail (hM : ∀ i j, 0 ≤ M i j) (hrow : ∀ i, ∑ j, M i j ≤ s) (hs : s < 1) (n : ℕ)
    (i j : V) :
    0 ≤ (1 - M)⁻¹ i j - neumann M n i j ∧
      (1 - M)⁻¹ i j - neumann M n i j ≤ s ^ n / (1 - s) := by
  have hZ : ∀ a b, 0 ≤ (1 - M)⁻¹ a b := Retrieval.inv_nonneg hM hrow hs
  have hs0 : 0 ≤ s := (sum_nonneg fun k _ ↦ hM i k).trans (hrow i)
  have e : (1 - M)⁻¹ i j - neumann M n i j = ∑ k, (1 - M)⁻¹ i k * (M ^ n) k j := by
    rw [← Matrix.sub_apply, inv_sub_neumann hM hrow hs n, Matrix.mul_apply]
  rw [e]
  refine ⟨sum_nonneg fun k _ ↦ mul_nonneg (hZ i k) (pow_apply_nonneg hM n k j), ?_⟩
  calc ∑ k, (1 - M)⁻¹ i k * (M ^ n) k j ≤ ∑ k, (1 - M)⁻¹ i k * s ^ n :=
        sum_le_sum fun k _ ↦ mul_le_mul_of_nonneg_left
          ((single_le_sum (fun l _ ↦ pow_apply_nonneg hM n k l) (mem_univ j)).trans
            (sum_pow_le hM hrow n k)) (hZ i k)
    _ = (∑ k, (1 - M)⁻¹ i k) * s ^ n := by rw [Finset.sum_mul]
    _ ≤ 1 / (1 - s) * s ^ n :=
        mul_le_mul_of_nonneg_right (sum_inv_le hM hrow hs i) (pow_nonneg hs0 n)
    _ = s ^ n / (1 - s) := by ring

/-- DYN-2, the control: when an eigenvalue is `1` the resolvent does not exist. With every row
summing to exactly `1` (the unkilled walk, the stochastic case), `1 − M` annihilates the constant
vector, so it is singular. -/
theorem det_one_sub_eq_zero_of_rows_eq_one [Nonempty V] (hrow : ∀ i, ∑ j, M i j = 1) :
    (1 - M).det = 0 := by
  refine Matrix.exists_mulVec_eq_zero_iff.mp ⟨1, one_ne_zero, ?_⟩
  ext i
  simp [Matrix.mulVec, dotProduct, hrow i, Matrix.one_apply]

/-- The rows of a power of a stochastic matrix sum to `1`. -/
theorem sum_pow_eq_one (hrow : ∀ i, ∑ j, M i j = 1) (n : ℕ) (i : V) :
    ∑ j, (M ^ n) i j = 1 := by
  induction n generalizing i with
  | zero => simp [Matrix.one_apply]
  | succ n ih =>
    calc ∑ j, (M ^ (n + 1)) i j = ∑ k, (M ^ n) i k * ∑ j, M k j := by
          simp only [pow_succ, Matrix.mul_apply, Finset.mul_sum]
          rw [Finset.sum_comm]
      _ = 1 := by simp [hrow, ih]

/-- DYN-2, the control: with every row summing to `1`, the partial sums of the walk series do
not converge, to anything: each row of the `n`-th partial sum sums to `n`. -/
theorem neumann_not_tendsto [Nonempty V] (hrow : ∀ i, ∑ j, M i j = 1) (Z : Matrix V V ℝ) :
    ¬ Tendsto (neumann M) atTop (𝓝 Z) := by
  intro h
  obtain ⟨i⟩ := ‹Nonempty V›
  have hsum : ∀ n, ∑ j, neumann M n i j = n := by
    intro n
    simp only [neumann, Matrix.sum_apply]
    rw [Finset.sum_comm]
    simp [sum_pow_eq_one hrow]
  have h1 : Tendsto (fun n ↦ ∑ j, neumann M n i j) atTop (𝓝 (∑ j, Z i j)) :=
    tendsto_finsetSum _ fun j _ ↦ (tendsto_pi_nhds.1 (tendsto_pi_nhds.1 h i)) j
  simp only [hsum] at h1
  exact not_tendsto_atTop_of_tendsto_nhds h1 tendsto_natCast_atTop_atTop

end Tail

/-! ### DYN-3 HodgeRank: the least-squares potential -/

section HodgeRank

variable {V E : Type*} [Fintype V] [Fintype E] [DecidableEq V] [DecidableEq E]
variable (B₁ : Matrix V E ℝ) (w : E → ℝ)

omit [Fintype V] [DecidableEq V] in
/-- `diag(w) v = w ∘ v`. -/
theorem diagonal_mulVec_eq (v : E → ℝ) : diagonal w *ᵥ v = w * v :=
  funext fun e ↦ mulVec_diagonal w v e

omit [DecidableEq V] in
/-- The energy of `L_w`: `xᵀ L_w x = ⟨∂₁ᵀ x, ∂₁ᵀ x⟩_w`. -/
theorem dotProduct_weightedLap (x : V → ℝ) :
    x ⬝ᵥ (weightedLap B₁ w *ᵥ x) = wdotE w (B₁ᵀ *ᵥ x) (B₁ᵀ *ᵥ x) := by
  rw [weightedLap, ← mulVec_mulVec, ← mulVec_mulVec, dotProduct_mulVec, ← mulVec_transpose,
    diagonal_mulVec_eq, wdotE, dotProduct]
  exact sum_congr rfl fun e _ ↦ by simp only [Pi.mul_apply]; ring

omit [Fintype V] [DecidableEq V] [DecidableEq E] in
/-- The weighted inner product is nonnegative on the diagonal, for nonnegative weights. -/
theorem wdotE_self_nonneg (hw : ∀ e, 0 ≤ w e) (a : E → ℝ) : 0 ≤ wdotE w a a :=
  sum_nonneg fun e _ ↦ mul_nonneg (hw e) (mul_self_nonneg (a e))

omit [Fintype V] [DecidableEq V] [DecidableEq E] in
/-- `⟨a, a⟩_w = 0` exactly when `w ∘ a = 0`, for nonnegative weights. -/
theorem wdotE_self_eq_zero_iff (hw : ∀ e, 0 ≤ w e) (a : E → ℝ) :
    wdotE w a a = 0 ↔ w * a = 0 := by
  constructor
  · intro h
    have h0 := (sum_eq_zero_iff_of_nonneg fun e _ ↦ mul_nonneg (hw e) (mul_self_nonneg (a e))).1 h
    funext e
    have he := h0 e (mem_univ e)
    rcases mul_eq_zero.1 he with h1 | h1
    · simp [h1]
    · simp [mul_self_eq_zero.1 h1]
  · intro h
    unfold wdotE
    refine sum_eq_zero fun e _ ↦ ?_
    have := congrFun h e
    simp only [Pi.mul_apply, Pi.zero_apply] at this
    rw [← mul_assoc, this, zero_mul]

omit [DecidableEq V] in
/-- The kernel of `L_w` is the set of potentials whose weighted gradient vanishes. -/
theorem weightedLap_mulVec_eq_zero_iff (hw : ∀ e, 0 ≤ w e) (k : V → ℝ) :
    weightedLap B₁ w *ᵥ k = 0 ↔ w * (B₁ᵀ *ᵥ k) = 0 := by
  constructor
  · intro h
    have h0 := dotProduct_weightedLap B₁ w k
    rw [h, dotProduct_zero] at h0
    exact (wdotE_self_eq_zero_iff w hw _).1 h0.symm
  · intro h
    rw [weightedLap, ← mulVec_mulVec, ← mulVec_mulVec, diagonal_mulVec_eq, h, mulVec_zero]

omit [DecidableEq V] in
/-- The divergence is orthogonal to the kernel of `L_w`: `⟨div_w Y, k⟩ = ⟨Y, w ∘ ∂₁ᵀ k⟩`. -/
theorem divergence_dotProduct (Y : E → ℝ) (k : V → ℝ) (hk : weightedLap B₁ w *ᵥ k = 0)
    (hw : ∀ e, 0 ≤ w e) : divergence B₁ w Y ⬝ᵥ k = 0 := by
  have h := (weightedLap_mulVec_eq_zero_iff B₁ w hw k).1 hk
  rw [divergence, dotProduct_comm, dotProduct_mulVec, ← mulVec_transpose]
  calc (B₁ᵀ *ᵥ k) ⬝ᵥ (w * Y) = Y ⬝ᵥ (w * (B₁ᵀ *ᵥ k)) := by
        simp only [dotProduct, Pi.mul_apply]
        exact sum_congr rfl fun e _ ↦ by ring
    _ = 0 := by rw [h, dotProduct_zero]

/-- DYN-3 The residual is divergence-free: `L_w s = div_w Y`, the normal equations, since the
divergence lies in the range of `L_w` and `L_w L_w⁺` fixes it. -/
theorem divergence_residual (hw : ∀ e, 0 ≤ w e) (Y : E → ℝ) :
    divergence B₁ w (residual B₁ w Y) = 0 := by
  have hfix : weightedLap B₁ w *ᵥ potential B₁ w Y = divergence B₁ w Y :=
    mulVec_pinv_mulVec_of_orthogonal (isHermitian_weightedLap B₁ w)
      fun k hk ↦ divergence_dotProduct B₁ w Y k hk hw
  rw [residual, divergence, mul_sub, mulVec_sub, ← divergence, ← hfix, weightedLap,
    ← mulVec_mulVec, ← mulVec_mulVec, diagonal_mulVec_eq, sub_self]

/-- The residual is `w`-orthogonal to every gradient. -/
theorem wdotE_residual_grad (hw : ∀ e, 0 ≤ w e) (Y : E → ℝ) (x : V → ℝ) :
    wdotE w (residual B₁ w Y) (B₁ᵀ *ᵥ x) = 0 := by
  have h := divergence_residual B₁ w hw Y
  rw [divergence] at h
  have : wdotE w (residual B₁ w Y) (B₁ᵀ *ᵥ x) = (B₁ *ᵥ (w * residual B₁ w Y)) ⬝ᵥ x := by
    rw [dotProduct_comm, dotProduct_mulVec, ← mulVec_transpose, wdotE, dotProduct]
    exact sum_congr rfl fun e _ ↦ by simp only [Pi.mul_apply]; ring
  rw [this, h, zero_dotProduct]

/-- Pythagoras for the weighted energy: `‖Y − ∂₁ᵀ s‖²_w = ‖r‖²_w + ‖∂₁ᵀ (s* − s)‖²_w`. -/
theorem wdotE_sub_grad (hw : ∀ e, 0 ≤ w e) (Y : E → ℝ) (x : V → ℝ) :
    wdotE w (Y - B₁ᵀ *ᵥ x) (Y - B₁ᵀ *ᵥ x) =
      wdotE w (residual B₁ w Y) (residual B₁ w Y) +
        wdotE w (B₁ᵀ *ᵥ (potential B₁ w Y - x)) (B₁ᵀ *ᵥ (potential B₁ w Y - x)) := by
  have hd : Y - B₁ᵀ *ᵥ x = residual B₁ w Y + B₁ᵀ *ᵥ (potential B₁ w Y - x) := by
    rw [residual, mulVec_sub]
    abel
  have hcross := wdotE_residual_grad B₁ w hw Y (potential B₁ w Y - x)
  rw [hd]
  simp only [wdotE, Pi.add_apply] at hcross ⊢
  rw [← Finset.sum_add_distrib]
  have : ∑ e, w e * ((residual B₁ w Y e + (B₁ᵀ *ᵥ (potential B₁ w Y - x)) e) *
      (residual B₁ w Y e + (B₁ᵀ *ᵥ (potential B₁ w Y - x)) e)) =
      ∑ e, (w e * (residual B₁ w Y e * residual B₁ w Y e) +
        w e * ((B₁ᵀ *ᵥ (potential B₁ w Y - x)) e * (B₁ᵀ *ᵥ (potential B₁ w Y - x)) e)) +
      2 * ∑ e, w e * (residual B₁ w Y e * (B₁ᵀ *ᵥ (potential B₁ w Y - x)) e) := by
    rw [Finset.mul_sum, ← Finset.sum_add_distrib]
    exact sum_congr rfl fun e _ ↦ by ring
  rw [this, hcross, mul_zero, add_zero]

/-- DYN-3 HodgeRank: the potential `s = L_w⁺ div_w Y` is a least-squares potential, its
residual's energy at most that of any other potential's residual. -/
theorem wdotE_residual_le (hw : ∀ e, 0 ≤ w e) (Y : E → ℝ) (x : V → ℝ) :
    wdotE w (residual B₁ w Y) (residual B₁ w Y) ≤ wdotE w (Y - B₁ᵀ *ᵥ x) (Y - B₁ᵀ *ᵥ x) := by
  rw [wdotE_sub_grad B₁ w hw Y x]
  linarith [wdotE_self_nonneg w hw (B₁ᵀ *ᵥ (potential B₁ w Y - x))]

/-- DYN-3 And it is unique up to the kernel of `L_w`: another potential does as well exactly when
it differs from `s` by a vector `L_w` annihilates. -/
theorem wdotE_residual_eq_iff (hw : ∀ e, 0 ≤ w e) (Y : E → ℝ) (x : V → ℝ) :
    wdotE w (Y - B₁ᵀ *ᵥ x) (Y - B₁ᵀ *ᵥ x) = wdotE w (residual B₁ w Y) (residual B₁ w Y) ↔
      weightedLap B₁ w *ᵥ (potential B₁ w Y - x) = 0 := by
  rw [wdotE_sub_grad B₁ w hw Y x, add_eq_left, wdotE_self_eq_zero_iff w hw,
    weightedLap_mulVec_eq_zero_iff B₁ w hw]

end HodgeRank

/-! ### DYN-3 On the flag complex the kernel is the constants -/

section Flag

open Hodge

variable {V : Type*} [LinearOrder V] [Fintype V] {G : SimpleGraph V} [DecidableRel G.Adj]

omit [DecidableRel G.Adj] in
/-- The gradient of a potential across an edge is the drop between its ends. -/
theorem transpose_d1_mulVec_apply (k : V → ℝ) (e : Edge G) :
    ((d1 G ℝ)ᵀ *ᵥ k) e = k e.1.2 - k e.1.1 := by
  simp [d1, mulVec, dotProduct, sub_mul, Finset.sum_sub_distrib, Pi.single_apply]

/-- DYN-3 On a connected graph with positive weights, the kernel of `L_w` is the constants: the
potential of a flow is unique up to a constant, and only its differences rank the nodes. -/
theorem eq_of_weightedLap_mulVec_eq_zero {w : Edge G → ℝ} (hw : ∀ e, 0 < w e)
    (hc : G.Connected) {k : V → ℝ} (hk : weightedLap (d1 G ℝ) w *ᵥ k = 0) (u v : V) :
    k u = k v := by
  have h := (weightedLap_mulVec_eq_zero_iff (d1 G ℝ) w (fun e ↦ (hw e).le) k).1 hk
  have hedge : ∀ e : Edge G, k e.1.1 = k e.1.2 := by
    intro e
    have he := congrFun h e
    simp only [Pi.mul_apply, Pi.zero_apply, transpose_d1_mulVec_apply] at he
    rcases mul_eq_zero.1 he with h0 | h0
    · exact absurd h0 (hw e).ne'
    · linarith
  have hadj : ∀ a b, G.Adj a b → k a = k b := by
    intro a b hab
    rcases lt_or_gt_of_ne (G.ne_of_adj hab) with hlt | hlt
    · exact hedge ⟨(a, b), hlt, hab⟩
    · exact (hedge ⟨(b, a), hlt, hab.symm⟩).symm
  obtain ⟨p⟩ := hc.preconnected u v
  induction p with
  | nil => rfl
  | cons hab _ ih => exact (hadj _ _ hab).trans ih

end Flag

/-! ### DYN-4 The modes of a symmetric operator -/

section Modes

variable {V : Type*} [Fintype V] [DecidableEq V] {M : Matrix V V ℝ} (hM : M.IsHermitian)

omit [DecidableEq V] in
/-- The inner product of Euclidean space is the dot product. -/
theorem inner_toLp (u v : V → ℝ) :
    ⟪(WithLp.toLp 2 u : EuclideanSpace ℝ V), WithLp.toLp 2 v⟫_ℝ = u ⬝ᵥ v := by
  rw [EuclideanSpace.inner_eq_star_dotProduct, star_trivial, WithLp.ofLp_toLp, WithLp.ofLp_toLp,
    dotProduct_comm]

/-- The inner product with a mode is the dot product with it. -/
theorem inner_mode (j : V) (x : V → ℝ) :
    ⟪hM.eigenvectorBasis j, (WithLp.toLp 2 x : EuclideanSpace ℝ V)⟫_ℝ = x ⬝ᵥ mode hM j := by
  rw [EuclideanSpace.inner_eq_star_dotProduct, star_trivial, WithLp.ofLp_toLp, mode]

/-- The modes are orthonormal. -/
theorem mode_dotProduct_mode (i j : V) : mode hM i ⬝ᵥ mode hM j = if i = j then 1 else 0 := by
  have h := orthonormal_iff_ite.1 hM.eigenvectorBasis.orthonormal i j
  rw [EuclideanSpace.inner_eq_star_dotProduct, star_trivial] at h
  rw [mode, mode, dotProduct_comm]
  exact h

/-- Parseval: `⟨x, y⟩ = Σ_j ⟨x, φ_j⟩ ⟨y, φ_j⟩`. -/
theorem dotProduct_eq_sum_modes (x y : V → ℝ) :
    x ⬝ᵥ y = ∑ j, (x ⬝ᵥ mode hM j) * (y ⬝ᵥ mode hM j) := by
  have h := hM.eigenvectorBasis.sum_inner_mul_inner (WithLp.toLp 2 x) (WithLp.toLp 2 y)
  rw [inner_toLp] at h
  rw [← h]
  refine sum_congr rfl fun j _ ↦ ?_
  rw [real_inner_comm (hM.eigenvectorBasis j) (WithLp.toLp 2 x), inner_mode, inner_mode]

/-- Every vector is the sum of its components on the modes. -/
theorem sum_modes (x : V → ℝ) : ∑ j, (x ⬝ᵥ mode hM j) • mode hM j = x := by
  have h := hM.eigenvectorBasis.sum_repr' (WithLp.toLp 2 x)
  have h' := congrArg WithLp.ofLp h
  rw [WithLp.ofLp_sum, WithLp.ofLp_toLp] at h'
  refine Eq.trans ?_ h'
  refine sum_congr rfl fun j _ ↦ ?_
  rw [WithLp.ofLp_smul, inner_mode, mode]

/-- A function of a symmetric matrix acts on a mode by the function of its eigenvalue:
`f(M) φ_j = f(λ_j) φ_j`. -/
theorem cfc_mulVec_mode (f : ℝ → ℝ) (j : V) :
    cfc f M *ᵥ mode hM j = f (hM.eigenvalues j) • mode hM j := by
  rw [hM.cfc_eq, IsHermitian.cfc, Unitary.conjStarAlgAut_apply, ← mulVec_mulVec, ← mulVec_mulVec,
    mode, hM.star_eigenvectorUnitary_mulVec, diagonal_mulVec_single]
  simp only [Function.comp_apply, RCLike.ofReal_real_eq_id, id_eq, mul_one]
  have : (Pi.single j (f (hM.eigenvalues j)) : V → ℝ) = f (hM.eigenvalues j) • Pi.single j 1 := by
    rw [← Pi.single_smul', smul_eq_mul, mul_one]
  rw [this, mulVec_smul, hM.eigenvectorUnitary_mulVec]

/-- A function of a symmetric matrix is symmetric. -/
theorem isHermitian_cfc (f : ℝ → ℝ) : (cfc f M).IsHermitian :=
  cfc_predicate f M

/-- DYN-4 The quadratic form of `f(M)` on the modes: `xᵀ f(M) x = Σ_j f(λ_j) ⟨x, φ_j⟩²`. -/
theorem dotProduct_cfc_mulVec (f : ℝ → ℝ) (x : V → ℝ) :
    x ⬝ᵥ (cfc f M *ᵥ x) = ∑ j, f (hM.eigenvalues j) * (x ⬝ᵥ mode hM j) ^ 2 := by
  rw [dotProduct_eq_sum_modes hM]
  refine sum_congr rfl fun j _ ↦ ?_
  rw [dotProduct_comm (cfc f M *ᵥ x), dotProduct_mulVec_symm (isHermitian_cfc f),
    cfc_mulVec_mode hM f j, smul_dotProduct, smul_eq_mul, dotProduct_comm (mode hM j) x]
  ring

/-- DYN-4 The energy on the modes: `xᵀ M x = Σ_j λ_j ⟨x, φ_j⟩²`. -/
theorem dotProduct_mulVec_eq_sum_modes (x : V → ℝ) :
    x ⬝ᵥ (M *ᵥ x) = ∑ j, hM.eigenvalues j * (x ⬝ᵥ mode hM j) ^ 2 := by
  have h := dotProduct_cfc_mulVec hM id x
  rwa [cfc_id ℝ M] at h

/-- DYN-4 Courant–Fischer on the modes a field lives on: when every mode `x` has weight on has
eigenvalue at least `μ`, `μ ‖x‖² ≤ xᵀ M x`. Frustration's floor is the case `μ = λ_min`. -/
theorem mul_dotProduct_self_le_of_modes (x : V → ℝ) {μ : ℝ}
    (hμ : ∀ j, x ⬝ᵥ mode hM j ≠ 0 → μ ≤ hM.eigenvalues j) :
    μ * (x ⬝ᵥ x) ≤ x ⬝ᵥ (M *ᵥ x) := by
  rw [dotProduct_mulVec_eq_sum_modes hM, dotProduct_eq_sum_modes hM x x, Finset.mul_sum]
  refine sum_le_sum fun j _ ↦ ?_
  by_cases h : x ⬝ᵥ mode hM j = 0
  · simp [h]
  · rw [← sq]
    exact mul_le_mul_of_nonneg_right (hμ j h) (sq_nonneg _)

/-- The heat kernel on a mode: `H_t φ_j = e^{−tλ_j} φ_j`. -/
theorem heat_mulVec_mode (t : ℝ) (j : V) :
    heat M t *ᵥ mode hM j = Real.exp (-t * hM.eigenvalues j) • mode hM j :=
  cfc_mulVec_mode hM _ j

/-- DYN-4 The heat kernel commutes with the projection onto any set of modes: the macro variables
evolve exactly by their own eigenvalues, `H_t (P_S f) = Σ_{j∈S} e^{−tλ_j} ⟨f, φ_j⟩ φ_j`. -/
theorem heat_modeProj (t : ℝ) (S : Finset V) (f : V → ℝ) :
    heat M t *ᵥ modeProj hM S f = ∑ j ∈ S, (Real.exp (-t * hM.eigenvalues j) * (f ⬝ᵥ mode hM j)) •
      mode hM j ∧ heat M t *ᵥ modeProj hM S f = modeProj hM S (heat M t *ᵥ f) := by
  have h1 : heat M t *ᵥ modeProj hM S f =
      ∑ j ∈ S, (Real.exp (-t * hM.eigenvalues j) * (f ⬝ᵥ mode hM j)) • mode hM j := by
    rw [modeProj, mulVec_sum]
    refine sum_congr rfl fun j _ ↦ ?_
    rw [mulVec_smul, heat_mulVec_mode, smul_smul, mul_comm]
  refine ⟨h1, h1.trans ?_⟩
  rw [modeProj]
  refine sum_congr rfl fun j _ ↦ ?_
  rw [dotProduct_comm (heat M t *ᵥ f), dotProduct_mulVec_symm (isHermitian_heat t),
    heat_mulVec_mode, smul_dotProduct, smul_eq_mul, dotProduct_comm (mode hM j) f]

/-- The component of `f − P_S f` on a kept mode is zero, on a dropped mode it is `f`'s. -/
theorem sub_modeProj_dotProduct_mode (S : Finset V) (f : V → ℝ) (j : V) :
    (f - modeProj hM S f) ⬝ᵥ mode hM j = if j ∈ S then 0 else f ⬝ᵥ mode hM j := by
  rw [sub_dotProduct, modeProj, sum_dotProduct]
  simp only [smul_dotProduct, smul_eq_mul, mode_dotProduct_mode, mul_ite, mul_one, mul_zero,
    Finset.sum_ite_eq']
  split_ifs <;> ring

/-- DYN-4 The mode-decay bound in energy: for `t ≥ 0` and `μ` at most every eigenvalue a field has
weight on, `‖H_t x‖² ≤ e^{−2μt} ‖x‖²`. -/
theorem heat_energy_le (x : V → ℝ) {t : ℝ} (ht : 0 ≤ t) {μ : ℝ}
    (hμ : ∀ j, x ⬝ᵥ mode hM j ≠ 0 → μ ≤ hM.eigenvalues j) :
    (heat M t *ᵥ x) ⬝ᵥ (heat M t *ᵥ x) ≤ Real.exp (-(2 * μ * t)) * (x ⬝ᵥ x) := by
  rw [← dotProduct_mulVec_symm (isHermitian_heat t) x (heat M t *ᵥ x), mulVec_mulVec,
    ← heat_add, ← two_mul, heat, dotProduct_cfc_mulVec hM, dotProduct_eq_sum_modes hM x x,
    Finset.mul_sum]
  refine sum_le_sum fun j _ ↦ ?_
  by_cases h : x ⬝ᵥ mode hM j = 0
  · simp [h]
  · rw [← sq]
    refine mul_le_mul_of_nonneg_right (Real.exp_le_exp.2 ?_) (sq_nonneg _)
    nlinarith [hμ j h]

/-- DYN-4 The dropped modes decay: for `t ≥ 0` and `μ` under every dropped eigenvalue,
`‖H_t (f − P_S f)‖² ≤ e^{−2μt} ‖f − P_S f‖²`. With `S` the first `k` modes, `μ = λ_{k+1}`. -/
theorem heat_sub_modeProj_le (S : Finset V) (f : V → ℝ) {t : ℝ} (ht : 0 ≤ t) {μ : ℝ}
    (hμ : ∀ j ∉ S, μ ≤ hM.eigenvalues j) :
    (heat M t *ᵥ (f - modeProj hM S f)) ⬝ᵥ (heat M t *ᵥ (f - modeProj hM S f)) ≤
      Real.exp (-(2 * μ * t)) * ((f - modeProj hM S f) ⬝ᵥ (f - modeProj hM S f)) := by
  refine heat_energy_le hM _ ht fun j hj ↦ ?_
  rw [sub_modeProj_dotProduct_mode] at hj
  by_cases h : j ∈ S
  · simp [h] at hj
  · exact hμ j h

end Modes

/-! ### DYN-5 Coarse-graining by a partition -/

section Coarse

variable {V B : Type*} [Fintype V] [Fintype B] [DecidableEq B]

omit [Fintype V] in
/-- The indicator lifts a block field to the block-constant field: `P h = π^* h`. -/
theorem indicator_mulVec (π : V → B) (h : B → ℝ) : indicator π *ᵥ h = Transport.pull π h := by
  funext v
  simp [indicator, mulVec, dotProduct, Transport.pull]

omit [Fintype B] in
/-- The indicator's transpose sums a field over each block: `Pᵀ g = π_* g`. -/
theorem transpose_indicator_mulVec (π : V → B) (g : V → ℝ) :
    (indicator π)ᵀ *ᵥ g = Transport.push π g := by
  funext b
  simp only [mulVec, dotProduct, transpose_apply, indicator, of_apply, Transport.push,
    Finset.sum_filter]
  exact sum_congr rfl fun v _ ↦ by split_ifs <;> simp

omit [Fintype V] in
/-- Every vertex lies in one block: `P 1 = 1`. -/
theorem indicator_mulVec_one {R : Type*} [NonAssocSemiring R] (π : V → B) :
    indicator π *ᵥ (1 : B → R) = 1 := by
  funext v
  simp [indicator, mulVec, dotProduct]

/-- The degree is the row sum, `A 1`. -/
theorem degree_eq_mulVec_one {R : Type*} [NonAssocSemiring R] (A : Matrix V V R) :
    degree A = A *ᵥ 1 := by
  funext i
  simp [degree, mulVec, dotProduct]

omit [Fintype B] in
/-- The quotient of a diagonal matrix is the diagonal of the block sums: `Pᵀ diag(d) P =
diag(Pᵀ d)`. -/
theorem transpose_indicator_mul_diagonal {R : Type*} [CommRing R] [DecidableEq V] (π : V → B)
    (d : V → R) : (indicator π)ᵀ * diagonal d * indicator π = diagonal ((indicator π)ᵀ *ᵥ d) := by
  ext b b'
  simp only [Matrix.mul_apply, transpose_apply, indicator, of_apply, diagonal_apply, mulVec,
    dotProduct]
  by_cases hbb : b = b'
  · subst hbb
    simp only [ite_true]
    refine sum_congr rfl fun v _ ↦ ?_
    by_cases hv : π v = b <;> simp [hv]
  · simp only [hbb, ite_false]
    refine sum_eq_zero fun v _ ↦ ?_
    by_cases hv : π v = b
    · simp [hv, hbb]
    · simp [hv]

/-- DYN-5 The Laplacian of the quotient is the quotient of the Laplacian, `Pᵀ L P = L_π`, over
any commutative ring: coarse-graining by a partition is exact on block-constant fields. -/
theorem lap_quot {R : Type*} [CommRing R] [DecidableEq V] (π : V → B) (A : Matrix V V R) :
    (indicator π)ᵀ * lap A * indicator π = lap (quot π A) := by
  rw [lap, lap, quot, Matrix.mul_sub, Matrix.sub_mul, transpose_indicator_mul_diagonal,
    degree_eq_mulVec_one, degree_eq_mulVec_one, ← mulVec_mulVec, ← mulVec_mulVec,
    indicator_mulVec_one]

/-- DYN-5 The energy of a block-constant field is the quotient's energy of its block values. -/
theorem dotProduct_lap_pull [DecidableEq V] (π : V → B) (A : Matrix V V ℝ) (h : B → ℝ) :
    Transport.pull π h ⬝ᵥ (lap A *ᵥ Transport.pull π h) = h ⬝ᵥ (lap (quot π A) *ᵥ h) := by
  have h1 : h ⬝ᵥ (lap (quot π A) *ᵥ h) =
      (indicator π *ᵥ h) ⬝ᵥ (lap A *ᵥ (indicator π *ᵥ h)) := by
    rw [← lap_quot, ← mulVec_mulVec, ← mulVec_mulVec, dotProduct_mulVec h, ← mulVec_transpose,
      transpose_transpose]
  rw [h1, indicator_mulVec]

/-- A kernel vector of the Laplacian of a connected support is constant. -/
theorem eq_of_lap_mulVec_eq_zero [DecidableEq V] {A : Matrix V V ℝ} (hA : A.IsSymm)
    (hw : ∀ i j, 0 ≤ A i j) (hc : (support A).Connected) {x : V → ℝ} (hx : lap A *ᵥ x = 0)
    (u v : V) : x u = x v := by
  have h := orthogonal_ker_lap hA hw (hc.preconnected u v) x hx
  simpa [sub_dotProduct, single_dotProduct, sub_eq_zero] using h

/-- A field orthogonal to the constants has no weight on a zero mode of a connected support. -/
theorem dotProduct_mode_eq_zero [DecidableEq V] {A : Matrix V V ℝ} (hA : A.IsSymm)
    (hw : ∀ i j, 0 ≤ A i j) (hc : (support A).Connected) {x : V → ℝ} (hx : x ⬝ᵥ 1 = 0) {j : V}
    (h0 : (isHermitian_lap A hA).eigenvalues j = 0) : x ⬝ᵥ mode (isHermitian_lap A hA) j = 0 := by
  have hker : lap A *ᵥ mode (isHermitian_lap A hA) j = 0 := by
    have := (isHermitian_lap A hA).mulVec_eigenvectorBasis j
    rw [h0, zero_smul] at this
    exact this
  obtain ⟨v₀⟩ := hc.nonempty
  have hconst : mode (isHermitian_lap A hA) j = fun _ ↦ mode (isHermitian_lap A hA) j v₀ :=
    funext fun v ↦ eq_of_lap_mulVec_eq_zero hA hw hc hker v v₀
  rw [hconst]
  have : (fun _ : V ↦ mode (isHermitian_lap A hA) j v₀) =
      mode (isHermitian_lap A hA) j v₀ • (1 : V → ℝ) := by
    funext v; simp
  rw [this, dotProduct_smul, hx, smul_zero]

/-- DYN-5 The spectral gap, on a connected support: a field orthogonal to the constants has
energy at least `μ` times its norm, for `μ` under every nonzero eigenvalue of `L`. -/
theorem gap_le_dotProduct_lap [DecidableEq V] {A : Matrix V V ℝ} (hA : A.IsSymm)
    (hw : ∀ i j, 0 ≤ A i j) (hc : (support A).Connected) {μ : ℝ}
    (hμ : ∀ j, (isHermitian_lap A hA).eigenvalues j ≠ 0 → μ ≤ (isHermitian_lap A hA).eigenvalues j)
    {x : V → ℝ} (hx : x ⬝ᵥ 1 = 0) : μ * (x ⬝ᵥ x) ≤ x ⬝ᵥ (lap A *ᵥ x) :=
  mul_dotProduct_self_le_of_modes (isHermitian_lap A hA) x fun j hj ↦
    hμ j fun h0 ↦ hj (dotProduct_mode_eq_zero hA hw hc hx h0)

/-- DYN-5 Coarse-graining never lowers the gap: on a connected support, a block field orthogonal
to the constants (under the block sizes) has a quotient Rayleigh quotient at least the fine gap,
`μ Σ_b |b| h_b² ≤ hᵀ L_π h`. A partition can lose slow modes; it cannot create one. -/
theorem gap_le_dotProduct_lap_quot [DecidableEq V] {A : Matrix V V ℝ} (hA : A.IsSymm)
    (hw : ∀ i j, 0 ≤ A i j) (hc : (support A).Connected) {μ : ℝ}
    (hμ : ∀ j, (isHermitian_lap A hA).eigenvalues j ≠ 0 → μ ≤ (isHermitian_lap A hA).eigenvalues j)
    (π : V → B) {h : B → ℝ} (hh : Transport.pull π h ⬝ᵥ 1 = 0) :
    μ * Transport.wdot π h h ≤ h ⬝ᵥ (lap (quot π A) *ᵥ h) := by
  rw [← dotProduct_lap_pull, ← Transport.pull_dotProduct_self]
  exact gap_le_dotProduct_lap hA hw hc hμ hh

end Coarse

/-! ### DYN-5 The ripple commutes with a transport that carries every weight forward -/

section Intertwine

variable {A B : Type*} [Fintype A] [Fintype B] [DecidableEq A] [DecidableEq B]

/-- When `P M = M' P`, the resolvents intertwine: `P (1 − M)⁻¹ = (1 − M')⁻¹ P`. Propagating a
shock and then carrying it forward is carrying it forward and then propagating it. -/
theorem resolvent_intertwine {P : Matrix B A ℝ} {M : Matrix A A ℝ} {M' : Matrix B B ℝ}
    (h : P * M = M' * P) (hM : IsUnit (1 - M).det) (hM' : IsUnit (1 - M').det) :
    P * (1 - M)⁻¹ = (1 - M')⁻¹ * P := by
  have h1 : (1 - M') * P = P * (1 - M) := by
    rw [Matrix.sub_mul, Matrix.mul_sub, Matrix.one_mul, Matrix.mul_one, h]
  calc P * (1 - M)⁻¹ = (1 - M')⁻¹ * ((1 - M') * P) * (1 - M)⁻¹ := by
        rw [Matrix.nonsing_inv_mul_cancel_left _ _ hM']
    _ = (1 - M')⁻¹ * P := by
        rw [h1, Matrix.mul_assoc, Matrix.mul_nonsing_inv_cancel_right _ _ hM]

omit [DecidableEq A] in
/-- DYN-5 A merge-free transport that carries every weight forward, with no new note feeding the
carried ones, intertwines the relations: `Pᵀ M = M' Pᵀ` for `P` the indicator of `σ`. -/
theorem transpose_indicator_mul {σ : A → B} (hσ : Function.Injective σ) {M : Matrix A A ℝ}
    {M' : Matrix B B ℝ} (hcarry : ∀ a a', M' (σ a) (σ a') = M a a')
    (hnew : ∀ b, b ∉ Set.range σ → ∀ a, M' b (σ a) = 0) :
    (indicator σ)ᵀ * M = M' * (indicator σ)ᵀ := by
  ext b a
  simp only [Matrix.mul_apply, transpose_apply, indicator, of_apply, ite_mul, one_mul, zero_mul,
    mul_ite, mul_one, mul_zero, Finset.sum_ite_eq, Finset.mem_univ, ite_true]
  by_cases hb : b ∈ Set.range σ
  · obtain ⟨a₀, rfl⟩ := hb
    rw [Finset.sum_eq_single a₀]
    · simp [hcarry]
    · intro a' _ ha'
      rw [ite_eq_right fun h ↦ ha' (hσ h)]
    · simp
  · rw [hnew b hb a]
    exact sum_eq_zero fun a' _ ↦ by rw [ite_eq_right fun h ↦ hb ⟨a', h⟩]

/-- DYN-5 The ripple is path-independent across such a transport: the shock propagated and then
carried forward is the carried shock propagated at the new cut. -/
theorem push_ripple {σ : A → B} (hσ : Function.Injective σ) {M : Matrix A A ℝ}
    {M' : Matrix B B ℝ} (hcarry : ∀ a a', M' (σ a) (σ a') = M a a')
    (hnew : ∀ b, b ∉ Set.range σ → ∀ a, M' b (σ a) = 0) {z : ℝ}
    (hM : IsUnit (1 - z • M).det) (hM' : IsUnit (1 - z • M').det) (δ : A → ℝ) :
    Transport.push σ (ripple M z δ) = ripple M' z (Transport.push σ δ) := by
  rw [← transpose_indicator_mulVec, ← transpose_indicator_mulVec, ripple, ripple, mulVec_mulVec,
    mulVec_mulVec]
  congr 1
  refine resolvent_intertwine ?_ hM hM'
  rw [Matrix.mul_smul, Matrix.smul_mul, transpose_indicator_mul hσ hcarry hnew]

end Intertwine

/-! ### DYN-5 A block read on its own under-estimates nearness -/

section Block

variable {V B : Type*} [Fintype V] [DecidableEq V] [DecidableEq B]

/-- DYN-5 RSP-5 on a block: the nearness computed within one block of a partition, with the
graph's degrees, is at most the graph's. A partition read block by block under-estimates nearness
and never invents it. -/
theorem nearnessOn_block_le {w : Matrix V V ℝ} {β z : ℝ} (hw0 : ∀ i j, 0 ≤ w i j)
    (hw1 : ∀ i j, w i j ≤ 1) (hβ : 0 ≤ β) (hz0 : 0 ≤ z) (hz1 : z < 1) (π : V → B) (b : B)
    (i j : V) :
    Retrieval.nearnessOn w (univ.filter fun v ↦ π v = b) β z i j ≤ Retrieval.nearness w β z i j :=
  Retrieval.nearnessOn_le_nearness hw0 hw1 hβ hz0 hz1 _ i j

end Block

/-! ### DYN-6 Mixing: the gap as a Poincaré inequality, and the fluctuations averaging out

The shapes follow the switch-chain family of openai/math
(`lean/ComparatorChallenges/SwitchChain.lean`, Apache 2.0): a spectral gap as a Poincaré
inequality between a variance and a Dirichlet form, the total-variation distance against the `L²`
distance by `√N / 2`, and geometric `L²` decay step by step. They are restated here over the
Laplacian's modes, for any weighted graph; nothing is copied. -/

section Mixing

variable {V : Type*} [Fintype V] [DecidableEq V] {A : Matrix V V ℝ}

/-- A spectral gap of at least `γ`, as a Poincaré inequality: every field orthogonal to the
constants has Dirichlet energy at least `γ` times its norm. -/
def HasSpectralGapAtLeast (A : Matrix V V ℝ) (γ : ℝ) : Prop :=
  ∀ f : V → ℝ, f ⬝ᵥ 1 = 0 → γ * (f ⬝ᵥ f) ≤ f ⬝ᵥ (lap A *ᵥ f)

/-- DYN-6 On a connected support, `γ` under every nonzero eigenvalue is a gap. -/
theorem hasSpectralGapAtLeast_of_eigenvalues (hA : A.IsSymm) (hw : ∀ i j, 0 ≤ A i j)
    (hc : (support A).Connected) {γ : ℝ}
    (hγ : ∀ j, (isHermitian_lap A hA).eigenvalues j ≠ 0 →
      γ ≤ (isHermitian_lap A hA).eigenvalues j) :
    HasSpectralGapAtLeast A γ :=
  fun _ hf ↦ gap_le_dotProduct_lap hA hw hc hγ hf

/-- A mode with a nonzero eigenvalue is orthogonal to the constants. -/
theorem mode_dotProduct_one (hA : A.IsSymm) {j : V}
    (hj : (isHermitian_lap A hA).eigenvalues j ≠ 0) :
    mode (isHermitian_lap A hA) j ⬝ᵥ 1 = 0 := by
  have h : mode (isHermitian_lap A hA) j ⬝ᵥ (lap A *ᵥ 1) =
      (lap A *ᵥ mode (isHermitian_lap A hA) j) ⬝ᵥ 1 :=
    dotProduct_mulVec_symm (isHermitian_lap A hA) _ _
  rw [lap_mulVec_one, dotProduct_zero] at h
  have h2 : lap A *ᵥ mode (isHermitian_lap A hA) j =
      (isHermitian_lap A hA).eigenvalues j • mode (isHermitian_lap A hA) j :=
    (isHermitian_lap A hA).mulVec_eigenvectorBasis j
  rw [h2, smul_dotProduct, smul_eq_mul] at h
  exact (mul_eq_zero.1 h.symm).resolve_left hj

/-- DYN-6 Conversely, a gap bounds every nonzero eigenvalue: on its mode, the Poincaré
inequality reads `γ ≤ λ_j`. So on a connected support the gap is exactly the least nonzero
eigenvalue. -/
theorem le_eigenvalue_of_hasSpectralGapAtLeast (hA : A.IsSymm) {γ : ℝ}
    (h : HasSpectralGapAtLeast A γ) {j : V} (hj : (isHermitian_lap A hA).eigenvalues j ≠ 0) :
    γ ≤ (isHermitian_lap A hA).eigenvalues j := by
  have hm := h _ (mode_dotProduct_one hA hj)
  have h2 : lap A *ᵥ mode (isHermitian_lap A hA) j =
      (isHermitian_lap A hA).eigenvalues j • mode (isHermitian_lap A hA) j :=
    (isHermitian_lap A hA).mulVec_eigenvectorBasis j
  rw [h2, dotProduct_smul, smul_eq_mul, mode_dotProduct_mode] at hm
  simpa using hm

/-- DYN-6 The gap in the variance form of the switch-chain family: the Dirichlet energy of any
field is at least `γ` times its variance about its mean, since `L` kills the mean. -/
theorem HasSpectralGapAtLeast.variance [Nonempty V] (hA : A.IsSymm) {γ : ℝ}
    (h : HasSpectralGapAtLeast A γ) (f : V → ℝ) :
    γ * ((f - ((f ⬝ᵥ 1) / Fintype.card V) • (1 : V → ℝ)) ⬝ᵥ
        (f - ((f ⬝ᵥ 1) / Fintype.card V) • (1 : V → ℝ))) ≤ f ⬝ᵥ (lap A *ᵥ f) := by
  set c : ℝ := (f ⬝ᵥ 1) / Fintype.card V
  have hN : (Fintype.card V : ℝ) ≠ 0 := by exact_mod_cast Fintype.card_ne_zero
  have hg : (f - c • (1 : V → ℝ)) ⬝ᵥ 1 = 0 := by
    rw [sub_dotProduct, smul_dotProduct, smul_eq_mul, dotProduct_one (1 : V → ℝ)]
    simp only [Pi.one_apply, Finset.sum_const, Finset.card_univ, nsmul_eq_mul, mul_one, c]
    rw [div_mul_cancel₀ _ hN, sub_self]
  have hL : lap A *ᵥ (f - c • (1 : V → ℝ)) = lap A *ᵥ f := by
    rw [mulVec_sub, mulVec_smul, lap_mulVec_one, smul_zero, sub_zero]
  have e : (f - c • (1 : V → ℝ)) ⬝ᵥ (lap A *ᵥ (f - c • (1 : V → ℝ))) = f ⬝ᵥ (lap A *ᵥ f) := by
    rw [hL, sub_dotProduct, smul_dotProduct, dotProduct_mulVec_symm (isHermitian_lap A hA) 1 f,
      lap_mulVec_one, zero_dotProduct, smul_zero, sub_zero]
  rw [← e]
  exact h _ hg

omit [DecidableEq V] in
/-- DYN-6 Total variation against `L²`: `½ Σ_i |x_i| ≤ (√N / 2) ‖x‖`, by Cauchy–Schwarz. -/
theorem half_sum_abs_le (x : V → ℝ) :
    1 / 2 * ∑ i, |x i| ≤ Real.sqrt (Fintype.card V) / 2 * Real.sqrt (x ⬝ᵥ x) := by
  have h : (∑ i, |x i|) ^ 2 ≤ (Fintype.card V : ℝ) * ∑ i, |x i| ^ 2 := by
    simpa [Finset.card_univ] using sq_sum_le_card_mul_sum_sq (s := univ) (f := fun i ↦ |x i|)
  have hx : ∑ i, |x i| ^ 2 = x ⬝ᵥ x := by
    simp only [dotProduct, sq, abs_mul_abs_self]
  rw [hx] at h
  have h2 : ∑ i, |x i| ≤ Real.sqrt (Fintype.card V * (x ⬝ᵥ x)) := Real.le_sqrt_of_sq_le h
  rw [Real.sqrt_mul (Nat.cast_nonneg _)] at h2
  calc 1 / 2 * ∑ i, |x i| ≤ 1 / 2 * (Real.sqrt (Fintype.card V) * Real.sqrt (x ⬝ᵥ x)) :=
        mul_le_mul_of_nonneg_left h2 (by norm_num)
    _ = Real.sqrt (Fintype.card V) / 2 * Real.sqrt (x ⬝ᵥ x) := by ring

/-- DYN-6 Geometric `L²` decay in continuous time: on a connected support with gap `γ`, the heat
kernel contracts every field orthogonal to the constants, `‖H_t x‖² ≤ e^{−2γt} ‖x‖²`. The
fluctuations average out at the rate the gap sets. -/
theorem heat_energy_le_of_gap (hA : A.IsSymm) (hw : ∀ i j, 0 ≤ A i j)
    (hc : (support A).Connected) {γ : ℝ}
    (hγ : ∀ j, (isHermitian_lap A hA).eigenvalues j ≠ 0 →
      γ ≤ (isHermitian_lap A hA).eigenvalues j)
    {x : V → ℝ} (hx : x ⬝ᵥ 1 = 0) {t : ℝ} (ht : 0 ≤ t) :
    (heat (lap A) t *ᵥ x) ⬝ᵥ (heat (lap A) t *ᵥ x) ≤ Real.exp (-(2 * γ * t)) * (x ⬝ᵥ x) :=
  heat_energy_le (isHermitian_lap A hA) x ht fun j hj ↦
    hγ j fun h0 ↦ hj (dotProduct_mode_eq_zero hA hw hc hx h0)

/-- DYN-6 And in total variation: `½ Σ_i |(H_t x)_i| ≤ (√N / 2) e^{−γt} ‖x‖`. -/
theorem half_sum_abs_heat_le (hA : A.IsSymm) (hw : ∀ i j, 0 ≤ A i j)
    (hc : (support A).Connected) {γ : ℝ}
    (hγ : ∀ j, (isHermitian_lap A hA).eigenvalues j ≠ 0 →
      γ ≤ (isHermitian_lap A hA).eigenvalues j)
    {x : V → ℝ} (hx : x ⬝ᵥ 1 = 0) {t : ℝ} (ht : 0 ≤ t) :
    1 / 2 * ∑ i, |(heat (lap A) t *ᵥ x) i| ≤
      Real.sqrt (Fintype.card V) / 2 * (Real.exp (-(γ * t)) * Real.sqrt (x ⬝ᵥ x)) := by
  refine (half_sum_abs_le _).trans (mul_le_mul_of_nonneg_left ?_ (by positivity))
  have h := heat_energy_le_of_gap hA hw hc hγ hx ht
  have e : Real.exp (-(2 * γ * t)) = Real.exp (-(γ * t)) ^ 2 := by
    rw [sq, ← Real.exp_add]
    ring_nf
  rw [e] at h
  calc Real.sqrt ((heat (lap A) t *ᵥ x) ⬝ᵥ (heat (lap A) t *ᵥ x))
      ≤ Real.sqrt (Real.exp (-(γ * t)) ^ 2 * (x ⬝ᵥ x)) := Real.sqrt_le_sqrt h
    _ = Real.exp (-(γ * t)) * Real.sqrt (x ⬝ᵥ x) := by
        rw [Real.sqrt_mul (sq_nonneg _), Real.sqrt_sq (Real.exp_nonneg _)]

/-- A symmetric operator that acts on each mode by `g j` has `‖N x‖² = Σ_j (g j)² ⟨x, φ_j⟩²`. -/
theorem dotProduct_self_mulVec_of_modes {M : Matrix V V ℝ} (hM : M.IsHermitian)
    {N : Matrix V V ℝ} (hN : N.IsHermitian) {g : V → ℝ}
    (hg : ∀ j, N *ᵥ mode hM j = g j • mode hM j) (x : V → ℝ) :
    (N *ᵥ x) ⬝ᵥ (N *ᵥ x) = ∑ j, g j ^ 2 * (x ⬝ᵥ mode hM j) ^ 2 := by
  rw [dotProduct_eq_sum_modes hM]
  refine sum_congr rfl fun j _ ↦ ?_
  rw [dotProduct_comm (N *ᵥ x), dotProduct_mulVec_symm hN, hg j, smul_dotProduct, smul_eq_mul,
    dotProduct_comm (mode hM j) x]
  ring

/-- The powers of such an operator act on each mode by the powers of `g j`. -/
theorem pow_mulVec_mode {M : Matrix V V ℝ} (hM : M.IsHermitian) {N : Matrix V V ℝ} {g : V → ℝ}
    (hg : ∀ j, N *ᵥ mode hM j = g j • mode hM j) (n : ℕ) (j : V) :
    N ^ n *ᵥ mode hM j = g j ^ n • mode hM j := by
  induction n with
  | zero => simp
  | succ n ih => rw [pow_succ', ← mulVec_mulVec, ih, mulVec_smul, hg j, smul_smul, pow_succ]

/-- DYN-6 Geometric `L²` decay step by step: when `|g j| ≤ ρ` on every mode `x` lives on,
`‖N^n x‖² ≤ ρ^{2n} ‖x‖²`. -/
theorem pow_energy_le {M : Matrix V V ℝ} (hM : M.IsHermitian) {N : Matrix V V ℝ}
    (hN : N.IsHermitian) {g : V → ℝ} (hg : ∀ j, N *ᵥ mode hM j = g j • mode hM j) (x : V → ℝ)
    {ρ : ℝ} (hρ : ∀ j, x ⬝ᵥ mode hM j ≠ 0 → |g j| ≤ ρ) (n : ℕ) :
    (N ^ n *ᵥ x) ⬝ᵥ (N ^ n *ᵥ x) ≤ ρ ^ (2 * n) * (x ⬝ᵥ x) := by
  rw [dotProduct_self_mulVec_of_modes hM (hN.pow n) (pow_mulVec_mode hM hg n) x,
    dotProduct_eq_sum_modes hM x x, Finset.mul_sum]
  refine sum_le_sum fun j _ ↦ ?_
  by_cases h : x ⬝ᵥ mode hM j = 0
  · simp [h]
  · have e : (g j ^ n) ^ 2 = |g j| ^ (2 * n) := by
      rw [← sq_abs, abs_pow, ← pow_mul, mul_comm]
    rw [e, ← sq]
    exact mul_le_mul_of_nonneg_right (pow_le_pow_left₀ (abs_nonneg _) (hρ j h) _) (sq_nonneg _)

/-- The lazy walk `1 − εL` acts on a mode by `1 − ελ_j`. -/
theorem one_sub_smul_mulVec_mode {M : Matrix V V ℝ} (hM : M.IsHermitian) (ε : ℝ) (j : V) :
    (1 - ε • M) *ᵥ mode hM j = (1 - ε * hM.eigenvalues j) • mode hM j := by
  rw [sub_mulVec, one_mulVec, smul_mulVec, mode, hM.mulVec_eigenvectorBasis j, smul_smul,
    sub_smul, one_smul]

/-- DYN-6 The lazy walk `1 − εL` contracts every field orthogonal to the constants by `1 − εγ` a
step, when `ε λ_j ≤ 1` for every eigenvalue: after `n` steps,
`‖(1 − εL)^n x‖² ≤ (1 − εγ)^{2n} ‖x‖²`. The discrete form of the heat kernel's decay. -/
theorem lazy_pow_energy_le (hA : A.IsSymm) (hw : ∀ i j, 0 ≤ A i j)
    (hc : (support A).Connected) {γ ε : ℝ} (hε : 0 ≤ ε)
    (hγ : ∀ j, (isHermitian_lap A hA).eigenvalues j ≠ 0 →
      γ ≤ (isHermitian_lap A hA).eigenvalues j)
    (hup : ∀ j, ε * (isHermitian_lap A hA).eigenvalues j ≤ 1) {x : V → ℝ} (hx : x ⬝ᵥ 1 = 0)
    (n : ℕ) :
    ((1 - ε • lap A) ^ n *ᵥ x) ⬝ᵥ ((1 - ε • lap A) ^ n *ᵥ x) ≤
      (1 - ε * γ) ^ (2 * n) * (x ⬝ᵥ x) := by
  have hN : (1 - ε • lap A).IsHermitian := by
    rw [IsHermitian, conjTranspose_eq_transpose_of_trivial, transpose_sub, transpose_one,
      transpose_smul, transpose_eq_of_isHermitian (isHermitian_lap A hA)]
  refine pow_energy_le (isHermitian_lap A hA) hN (one_sub_smul_mulVec_mode _ ε) x
    (fun j hj ↦ ?_) n
  have hj0 : (isHermitian_lap A hA).eigenvalues j ≠ 0 :=
    fun h0 ↦ hj (dotProduct_mode_eq_zero hA hw hc hx h0)
  rw [abs_of_nonneg (by linarith [hup j])]
  linarith [mul_le_mul_of_nonneg_left (hγ j hj0) hε]

end Mixing

end Palace.Dynamics
