module

public import Palace.Hodge.Defs
public import Mathlib.Combinatorics.SimpleGraph.Basic
public import Mathlib.Data.Matrix.ColumnRowPartitioned
public import Mathlib.Algebra.Order.Star.Real
public import Mathlib.LinearAlgebra.Matrix.Charpoly.Basic
public import Mathlib.LinearAlgebra.Matrix.PosDef
public import Mathlib.LinearAlgebra.Matrix.Rank

/-!
# The Hodge 1-Laplacian: LAP-7 to LAP-11

The degree-1 lift of the Laplacian family (`core/kernel/complex/hodge.py`; dn-edge-dynamics §2.2).
The complex is the flag complex of the backbone's support: its edges, each oriented from its
smaller end, and its 3-cliques as ascending triples. `∂₁ e_ij = δ_j − δ_i`,
`∂₂ t_ijk = e_jk − e_ik + e_ij`, and `L₁ = ∂₁ᵀ ∂₁ + ∂₂ ∂₂ᵀ`.

* LAP-7: a boundary has no boundary, `∂₁ ∂₂ = 0`, over any ring.
* LAP-8: `L₁` is positive semidefinite, its energy is `‖∂₁ c‖² + ‖∂₂ᵀ c‖²`, and so a flow is
  harmonic exactly when it is a cycle and a cocycle.
* LAP-9: every edge flow splits uniquely into a gradient (`im ∂₁ᵀ`), a curl (`im ∂₂`) and a
  harmonic flow (`ker L₁`), the three mutually orthogonal.
* LAP-10: `dim ker L₁ + rank ∂₂ = dim ker ∂₁`, so `dim ker L₁` is the first Betti number.
* LAP-11: reorienting edges and triangles conjugates `L₁` by a sign involution: the spectrum, the
  kernel's dimension and the split all carry over.

LAP-8 to LAP-11 hold for any two real matrices with `∂₁ ∂₂ = 0`; LAP-7 is what makes the flag
complex one. The attacks (`PalaceTest/Hodge.lean`) run over `ℤ` on random graphs of six vertices.
-/

@[expose] public section

open Matrix

namespace Palace.Hodge

/-! ### The flag complex -/

section Complex

variable {V : Type*} [LinearOrder V] [Fintype V] (G : SimpleGraph V) [DecidableRel G.Adj]

variable {G}

variable (G)

/-- **LAP-7** A boundary has no boundary: `∂₁ ∂₂ = 0`, exactly, over any ring. -/
theorem d1_mul_d2 (R : Type*) [Ring R] : d1 G R * d2 G R = 0 := by
  refine Matrix.ext fun v ⟨⟨i, j, k⟩, hij, hjk, hadj⟩ ↦ ?_
  rw [Matrix.mul_apply, Matrix.zero_apply]
  simp only [d2, mul_add, mul_sub, mul_ite, mul_one, mul_zero, Finset.sum_add_distrib,
    Finset.sum_sub_distrib, Finset.sum_ite_eq', Finset.mem_univ, ite_true]
  simp only [d1, edgeIJ, edgeIK, edgeJK, Pi.sub_apply]
  abel

end Complex

/-! ### The Hodge Laplacian of any complex -/

section Hodge

variable {V E T : Type*} [Fintype V] [Fintype E] [Fintype T]

variable (B₁ : Matrix V E ℝ) (B₂ : Matrix E T ℝ)

/-- **LAP-8** The energy of an edge flow: `cᵀ L₁ c = ‖∂₁ c‖² + ‖∂₂ᵀ c‖²`. -/
theorem dotProduct_lap1 (c : E → ℝ) :
    c ⬝ᵥ lap1 B₁ B₂ *ᵥ c = (B₁ *ᵥ c) ⬝ᵥ (B₁ *ᵥ c) + (B₂ᵀ *ᵥ c) ⬝ᵥ (B₂ᵀ *ᵥ c) := by
  simp only [lap1, add_mulVec, ← mulVec_mulVec, dotProduct_add, dotProduct_mulVec,
    ← mulVec_transpose, transpose_transpose]

omit [Fintype E] in
/-- **LAP-8** `L₁` is positive semidefinite. -/
theorem posSemidef_lap1 [Finite E] : (lap1 B₁ B₂).PosSemidef := by
  have := Fintype.ofFinite E
  simpa [lap1, conjTranspose_eq_transpose_of_trivial] using
    (posSemidef_conjTranspose_mul_self B₁).add (posSemidef_self_mul_conjTranspose B₂)

theorem dotProduct_self_nonneg' {n : Type*} [Fintype n] (v : n → ℝ) : 0 ≤ v ⬝ᵥ v :=
  Finset.sum_nonneg fun i _ ↦ mul_self_nonneg (v i)

/-- **LAP-8** A flow is harmonic exactly when it is a cycle and a cocycle. -/
theorem lap1_mulVec_eq_zero_iff (c : E → ℝ) :
    lap1 B₁ B₂ *ᵥ c = 0 ↔ B₁ *ᵥ c = 0 ∧ B₂ᵀ *ᵥ c = 0 := by
  constructor
  · intro h
    have h0 := dotProduct_lap1 B₁ B₂ c
    rw [h, dotProduct_zero] at h0
    obtain ⟨h1, h2⟩ := (add_eq_zero_iff_of_nonneg (dotProduct_self_nonneg' _)
      (dotProduct_self_nonneg' _)).1 h0.symm
    exact ⟨dotProduct_self_eq_zero.1 h1, dotProduct_self_eq_zero.1 h2⟩
  · rintro ⟨h1, h2⟩
    simp [lap1, add_mulVec, ← mulVec_mulVec, h1, h2]

variable {B₁ B₂}

/-- **LAP-9** Gradients and curls are orthogonal. -/
theorem grad_dot_curl (h : B₁ * B₂ = 0) (x : V → ℝ) (y : T → ℝ) :
    (B₁ᵀ *ᵥ x) ⬝ᵥ (B₂ *ᵥ y) = 0 := by
  rw [dotProduct_mulVec, mulVec_transpose, vecMul_vecMul, h, vecMul_zero, zero_dotProduct]

/-- **LAP-9** Harmonic flows are orthogonal to gradients. -/
theorem grad_dot_harm {k : E → ℝ} (hk : lap1 B₁ B₂ *ᵥ k = 0) (x : V → ℝ) :
    (B₁ᵀ *ᵥ x) ⬝ᵥ k = 0 := by
  rw [mulVec_transpose, ← dotProduct_mulVec, ((lap1_mulVec_eq_zero_iff B₁ B₂ k).1 hk).1,
    dotProduct_zero]

/-- **LAP-9** And to curls. -/
theorem curl_dot_harm {k : E → ℝ} (hk : lap1 B₁ B₂ *ᵥ k = 0) (y : T → ℝ) :
    (B₂ *ᵥ y) ⬝ᵥ k = 0 := by
  rw [dotProduct_comm, dotProduct_mulVec, ← mulVec_transpose,
    ((lap1_mulVec_eq_zero_iff B₁ B₂ k).1 hk).2, zero_dotProduct]

/-- **LAP-9** The split is unique: two splits of one flow agree part by part. -/
theorem hodge_unique (h : B₁ * B₂ = 0) {x x' : V → ℝ} {y y' : T → ℝ} {k k' : E → ℝ}
    (hk : lap1 B₁ B₂ *ᵥ k = 0) (hk' : lap1 B₁ B₂ *ᵥ k' = 0)
    (he : B₁ᵀ *ᵥ x + B₂ *ᵥ y + k = B₁ᵀ *ᵥ x' + B₂ *ᵥ y' + k') :
    B₁ᵀ *ᵥ x = B₁ᵀ *ᵥ x' ∧ B₂ *ᵥ y = B₂ *ᵥ y' ∧ k = k' := by
  have hd : lap1 B₁ B₂ *ᵥ (k - k') = 0 := by rw [mulVec_sub, hk, hk', sub_zero]
  have hsum : B₁ᵀ *ᵥ (x - x') + B₂ *ᵥ (y - y') + (k - k') = 0 := by
    rw [mulVec_sub, mulVec_sub, ← sub_eq_zero.2 he]
    abel
  have hgr := grad_dot_curl h (x - x') (y - y')
  have hgd := grad_dot_harm hd (x - x')
  have hrd := curl_dot_harm hd (y - y')
  have hg : (B₁ᵀ *ᵥ (x - x')) ⬝ᵥ (B₁ᵀ *ᵥ (x - x')) = 0 := by
    have := congrArg ((B₁ᵀ *ᵥ (x - x')) ⬝ᵥ ·) hsum
    simp only [dotProduct_add, dotProduct_zero] at this
    linarith
  have hr : (B₂ *ᵥ (y - y')) ⬝ᵥ (B₂ *ᵥ (y - y')) = 0 := by
    have := congrArg ((B₂ *ᵥ (y - y')) ⬝ᵥ ·) hsum
    simp only [dotProduct_add, dotProduct_zero] at this
    rw [dotProduct_comm] at hgr
    linarith
  have g0 := dotProduct_self_eq_zero.1 hg
  have r0 := dotProduct_self_eq_zero.1 hr
  rw [g0, r0, zero_add, zero_add, sub_eq_zero] at hsum
  rw [mulVec_sub, sub_eq_zero] at g0 r0
  exact ⟨g0, r0, hsum⟩

omit [Fintype E] in
theorem range_fromCols {n₁ n₂ : Type*} [Fintype n₁] [Fintype n₂] (A : Matrix E n₁ ℝ)
    (B : Matrix E n₂ ℝ) :
    LinearMap.range (fromCols A B).mulVecLin =
      LinearMap.range A.mulVecLin ⊔ LinearMap.range B.mulVecLin := by
  ext v
  simp only [LinearMap.mem_range, mulVecLin_apply, Submodule.mem_sup]
  constructor
  · rintro ⟨w, rfl⟩
    exact ⟨_, ⟨_, rfl⟩, _, ⟨_, rfl⟩, (fromCols_mulVec A B w).symm⟩
  · rintro ⟨_, ⟨a, rfl⟩, _, ⟨b, rfl⟩, rfl⟩
    exact ⟨Sum.elim a b, fromCols_mulVec_sumElim A B a b⟩

/-- Only `0` is both a gradient and a curl. -/
theorem grad_inf_curl (h : B₁ * B₂ = 0) :
    LinearMap.range B₁ᵀ.mulVecLin ⊓ LinearMap.range B₂.mulVecLin = ⊥ := by
  rw [Submodule.eq_bot_iff]
  intro v hv
  obtain ⟨⟨x, hx⟩, ⟨y, hy⟩⟩ := Submodule.mem_inf.1 hv
  simp only [mulVecLin_apply] at hx hy
  apply dotProduct_self_eq_zero.1
  calc v ⬝ᵥ v = (B₁ᵀ *ᵥ x) ⬝ᵥ (B₂ *ᵥ y) := by rw [hx, hy]
    _ = 0 := grad_dot_curl h x y

/-- Only `0` is both harmonic and a sum of a gradient and a curl. -/
theorem sup_inf_harm :
    (LinearMap.range B₁ᵀ.mulVecLin ⊔ LinearMap.range B₂.mulVecLin) ⊓
      LinearMap.ker (lap1 B₁ B₂).mulVecLin = ⊥ := by
  rw [Submodule.eq_bot_iff]
  intro v hvk
  obtain ⟨hv, hk⟩ := Submodule.mem_inf.1 hvk
  obtain ⟨_, ⟨x, rfl⟩, _, ⟨y, rfl⟩, rfl⟩ := Submodule.mem_sup.1 hv
  rw [LinearMap.mem_ker] at hk
  simp only [mulVecLin_apply] at hk ⊢
  apply dotProduct_self_eq_zero.1
  rw [add_dotProduct, grad_dot_harm hk, curl_dot_harm hk, add_zero]

/-- `rank L₁ = rank ∂₁ + rank ∂₂`: `L₁ = M Mᵀ` for `M = [∂₁ᵀ | ∂₂]`, whose two blocks have ranges
meeting only in `0`. -/
theorem rank_lap1 (h : B₁ * B₂ = 0) : (lap1 B₁ B₂).rank = B₁.rank + B₂.rank := by
  have hl : lap1 B₁ B₂ = fromCols B₁ᵀ B₂ * (fromCols B₁ᵀ B₂)ᵀ := by
    rw [transpose_fromCols, transpose_transpose, fromCols_mul_fromRows, lap1]
  rw [hl, rank_self_mul_transpose, rank, range_fromCols]
  have := Submodule.finrank_sup_add_finrank_inf_eq (LinearMap.range B₁ᵀ.mulVecLin)
    (LinearMap.range B₂.mulVecLin)
  rw [grad_inf_curl h, finrank_bot, add_zero] at this
  rw [this, ← rank, ← rank, rank_transpose]

/-- **LAP-10** `dim ker L₁ + rank ∂₂ = dim ker ∂₁`: the harmonic flows count the first Betti
number, `dim ker ∂₁ − dim im ∂₂`. -/
theorem finrank_harm (h : B₁ * B₂ = 0) :
    Module.finrank ℝ (LinearMap.ker (lap1 B₁ B₂).mulVecLin) + B₂.rank =
      Module.finrank ℝ (LinearMap.ker B₁.mulVecLin) := by
  have hl := LinearMap.finrank_range_add_finrank_ker (lap1 B₁ B₂).mulVecLin
  have h1 := LinearMap.finrank_range_add_finrank_ker B₁.mulVecLin
  rw [← rank, rank_lap1 h] at hl
  rw [← rank] at h1
  omega

/-- **LAP-9** Every edge flow splits into a gradient, a curl and a harmonic flow. -/
theorem exists_hodge (h : B₁ * B₂ = 0) (c : E → ℝ) :
    ∃ x y, lap1 B₁ B₂ *ᵥ (c - B₁ᵀ *ᵥ x - B₂ *ᵥ y) = 0 := by
  have htop : LinearMap.range B₁ᵀ.mulVecLin ⊔ LinearMap.range B₂.mulVecLin ⊔
      LinearMap.ker (lap1 B₁ B₂).mulVecLin = ⊤ := by
    apply Submodule.eq_top_of_finrank_eq
    have h3 := Submodule.finrank_sup_add_finrank_inf_eq
      (LinearMap.range B₁ᵀ.mulVecLin ⊔ LinearMap.range B₂.mulVecLin)
      (LinearMap.ker (lap1 B₁ B₂).mulVecLin)
    have h2 := Submodule.finrank_sup_add_finrank_inf_eq (LinearMap.range B₁ᵀ.mulVecLin)
      (LinearMap.range B₂.mulVecLin)
    have hl := LinearMap.finrank_range_add_finrank_ker (lap1 B₁ B₂).mulVecLin
    rw [sup_inf_harm, finrank_bot, add_zero] at h3
    rw [grad_inf_curl h, finrank_bot, add_zero] at h2
    rw [← rank, rank_lap1 h] at hl
    have hg : Module.finrank ℝ (LinearMap.range B₁ᵀ.mulVecLin) = B₁.rank := by
      rw [← rank_transpose]; rfl
    have hc : Module.finrank ℝ (LinearMap.range B₂.mulVecLin) = B₂.rank := rfl
    omega
  have hc : c ∈ LinearMap.range B₁ᵀ.mulVecLin ⊔ LinearMap.range B₂.mulVecLin ⊔
      LinearMap.ker (lap1 B₁ B₂).mulVecLin := htop ▸ Submodule.mem_top
  obtain ⟨_, hgr, k, hk, rfl⟩ := Submodule.mem_sup.1 hc
  obtain ⟨_, ⟨x, rfl⟩, _, ⟨y, rfl⟩, rfl⟩ := Submodule.mem_sup.1 hgr
  refine ⟨x, y, ?_⟩
  rw [LinearMap.mem_ker, mulVecLin_apply] at hk
  simp only [mulVecLin_apply]
  have : B₁ᵀ *ᵥ x + B₂ *ᵥ y + k - B₁ᵀ *ᵥ x - B₂ *ᵥ y = k := by abel
  rw [this, hk]

/-! ### Orientation -/

variable [DecidableEq E] [DecidableEq T]

/-- **LAP-11** Reorienting the edges by signs `σ` and the triangles by `τ` conjugates `L₁` by the
involution `diag σ`. -/
theorem lap1_reorient (σ : E → ℝ) (τ : T → ℝ) (hτ : ∀ t, τ t * τ t = 1) :
    lap1 (B₁ * diagonal σ) (diagonal σ * B₂ * diagonal τ) =
      diagonal σ * lap1 B₁ B₂ * diagonal σ := by
  have hττ : diagonal τ * diagonal τ = 1 := by
    rw [diagonal_mul_diagonal, ← diagonal_one]
    exact congrArg diagonal (funext hτ)
  simp only [lap1, transpose_mul, diagonal_transpose, Matrix.mul_add, Matrix.add_mul,
    Matrix.mul_assoc]
  congr 1
  rw [← Matrix.mul_assoc (diagonal τ), hττ, Matrix.one_mul]

omit [Fintype V] in
/-- **LAP-11** A reoriented complex is still a complex. -/
theorem reorient_complex (h : B₁ * B₂ = 0) (σ : E → ℝ) (τ : T → ℝ) (hσ : ∀ e, σ e * σ e = 1) :
    B₁ * diagonal σ * (diagonal σ * B₂ * diagonal τ) = 0 := by
  have hσσ : diagonal σ * diagonal σ = 1 := by
    rw [diagonal_mul_diagonal, ← diagonal_one]
    exact congrArg diagonal (funext hσ)
  rw [Matrix.mul_assoc, ← Matrix.mul_assoc (diagonal σ), ← Matrix.mul_assoc (diagonal σ), hσσ,
    Matrix.one_mul, ← Matrix.mul_assoc, h, Matrix.zero_mul]

/-- **LAP-11** So the spectrum does not depend on the orientation. -/
theorem charpoly_reorient (σ : E → ℝ) (τ : T → ℝ) (hσ : ∀ e, σ e * σ e = 1)
    (hτ : ∀ t, τ t * τ t = 1) :
    (lap1 (B₁ * diagonal σ) (diagonal σ * B₂ * diagonal τ)).charpoly = (lap1 B₁ B₂).charpoly := by
  have hσσ : diagonal σ * diagonal σ = 1 := by
    rw [diagonal_mul_diagonal, ← diagonal_one]
    exact congrArg diagonal (funext hσ)
  let u : (Matrix E E ℝ)ˣ := ⟨diagonal σ, diagonal σ, hσσ, hσσ⟩
  have hinv : (u : Matrix E E ℝ)⁻¹ = diagonal σ := inv_eq_left_inv hσσ
  rw [lap1_reorient σ τ hτ, ← charpoly_units_conj u (lap1 B₁ B₂), hinv]

/-- **LAP-11** Nor does the dimension of the harmonic flows. -/
theorem finrank_harm_reorient (σ : E → ℝ) (τ : T → ℝ) (hσ : ∀ e, σ e * σ e = 1)
    (hτ : ∀ t, τ t * τ t = 1) :
    Module.finrank ℝ
        (LinearMap.ker (lap1 (B₁ * diagonal σ) (diagonal σ * B₂ * diagonal τ)).mulVecLin) =
      Module.finrank ℝ (LinearMap.ker (lap1 B₁ B₂).mulVecLin) := by
  have hdet : IsUnit (diagonal σ).det := by
    rw [det_diagonal]
    exact IsUnit.mk0 _ (Finset.prod_ne_zero_iff.2 fun e _ h0 ↦ by simpa [h0] using hσ e)
  have hr : (lap1 (B₁ * diagonal σ) (diagonal σ * B₂ * diagonal τ)).rank =
      (lap1 B₁ B₂).rank := by
    rw [lap1_reorient σ τ hτ, rank_mul_eq_left_of_isUnit_det _ _ hdet,
      rank_mul_eq_right_of_isUnit_det _ _ hdet]
  have h1 := LinearMap.finrank_range_add_finrank_ker
    (lap1 (B₁ * diagonal σ) (diagonal σ * B₂ * diagonal τ)).mulVecLin
  have h2 := LinearMap.finrank_range_add_finrank_ker (lap1 B₁ B₂).mulVecLin
  rw [← rank] at h1 h2
  omega

/-- **LAP-11** And the split carries over: reorienting a gradient, a curl and a harmonic flow
gives the reoriented complex's gradient, curl and harmonic flow. -/
theorem hodge_reorient (σ : E → ℝ) (τ : T → ℝ) (hσ : ∀ e, σ e * σ e = 1)
    (hτ : ∀ t, τ t * τ t = 1) (x : V → ℝ) (y : T → ℝ) {k : E → ℝ} (hk : lap1 B₁ B₂ *ᵥ k = 0) :
    diagonal σ *ᵥ (B₁ᵀ *ᵥ x) = (B₁ * diagonal σ)ᵀ *ᵥ x ∧
      diagonal σ *ᵥ (B₂ *ᵥ y) = (diagonal σ * B₂ * diagonal τ) *ᵥ (diagonal τ *ᵥ y) ∧
      lap1 (B₁ * diagonal σ) (diagonal σ * B₂ * diagonal τ) *ᵥ (diagonal σ *ᵥ k) = 0 := by
  have hττ : diagonal τ * diagonal τ = 1 := by
    rw [diagonal_mul_diagonal, ← diagonal_one]
    exact congrArg diagonal (funext hτ)
  refine ⟨?_, ?_, ?_⟩
  · rw [transpose_mul, diagonal_transpose, mulVec_mulVec]
  · rw [mulVec_mulVec, mulVec_mulVec, Matrix.mul_assoc, Matrix.mul_assoc, hττ, Matrix.mul_one]
  · have hσσ : diagonal σ * diagonal σ = 1 := by
      rw [diagonal_mul_diagonal, ← diagonal_one]
      exact congrArg diagonal (funext hσ)
    rw [lap1_reorient σ τ hτ, mulVec_mulVec, Matrix.mul_assoc, Matrix.mul_assoc, hσσ,
      Matrix.mul_one, ← mulVec_mulVec, hk, mulVec_zero]

end Hodge

/-! ### The flag complex's Betti number -/

/-- **LAP-10** On the flag complex of any graph, `dim ker L₁ + rank ∂₂ = dim ker ∂₁`. -/
theorem flag_finrank_harm {V : Type*} [LinearOrder V] [Fintype V] (G : SimpleGraph V)
    [DecidableRel G.Adj] :
    Module.finrank ℝ (LinearMap.ker (lap1 (d1 G ℝ) (d2 G ℝ)).mulVecLin) + (d2 G ℝ).rank =
      Module.finrank ℝ (LinearMap.ker (d1 G ℝ).mulVecLin) :=
  finrank_harm (d1_mul_d2 G ℝ)

end Palace.Hodge
