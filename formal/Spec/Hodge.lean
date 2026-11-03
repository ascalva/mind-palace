module

public import Palace.Hodge.Defs

/-!
# The Hodge 1-Laplacian: LAP-7 to LAP-11, the statements

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

These are the laws of `Palace/Hodge.lean` as the ledger cites them, each with its proof
left as `sorry`. `lake comparator` checks that the `Palace` library proves each one
exactly as stated here, from the standard axioms alone.
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
theorem d1_mul_d2 (R : Type*) [Ring R] : d1 G R * d2 G R = 0 :=
  sorry

end Complex

/-! ### The Hodge Laplacian of any complex -/

section Hodge

variable {V E T : Type*} [Fintype V] [Fintype E] [Fintype T]

variable (B₁ : Matrix V E ℝ) (B₂ : Matrix E T ℝ)

/-- **LAP-8** The energy of an edge flow: `cᵀ L₁ c = ‖∂₁ c‖² + ‖∂₂ᵀ c‖²`. -/
theorem dotProduct_lap1 (c : E → ℝ) :
    c ⬝ᵥ lap1 B₁ B₂ *ᵥ c = (B₁ *ᵥ c) ⬝ᵥ (B₁ *ᵥ c) + (B₂ᵀ *ᵥ c) ⬝ᵥ (B₂ᵀ *ᵥ c) :=
  sorry

omit [Fintype E] in
/-- **LAP-8** `L₁` is positive semidefinite. -/
theorem posSemidef_lap1 [Finite E] : (lap1 B₁ B₂).PosSemidef :=
  sorry

/-- **LAP-8** A flow is harmonic exactly when it is a cycle and a cocycle. -/
theorem lap1_mulVec_eq_zero_iff (c : E → ℝ) :
    lap1 B₁ B₂ *ᵥ c = 0 ↔ B₁ *ᵥ c = 0 ∧ B₂ᵀ *ᵥ c = 0 :=
  sorry

variable {B₁ B₂}

/-- **LAP-9** Gradients and curls are orthogonal. -/
theorem grad_dot_curl (h : B₁ * B₂ = 0) (x : V → ℝ) (y : T → ℝ) :
    (B₁ᵀ *ᵥ x) ⬝ᵥ (B₂ *ᵥ y) = 0 :=
  sorry

/-- **LAP-9** Harmonic flows are orthogonal to gradients. -/
theorem grad_dot_harm {k : E → ℝ} (hk : lap1 B₁ B₂ *ᵥ k = 0) (x : V → ℝ) :
    (B₁ᵀ *ᵥ x) ⬝ᵥ k = 0 :=
  sorry

/-- **LAP-9** And to curls. -/
theorem curl_dot_harm {k : E → ℝ} (hk : lap1 B₁ B₂ *ᵥ k = 0) (y : T → ℝ) :
    (B₂ *ᵥ y) ⬝ᵥ k = 0 :=
  sorry

/-- **LAP-9** The split is unique: two splits of one flow agree part by part. -/
theorem hodge_unique (h : B₁ * B₂ = 0) {x x' : V → ℝ} {y y' : T → ℝ} {k k' : E → ℝ}
    (hk : lap1 B₁ B₂ *ᵥ k = 0) (hk' : lap1 B₁ B₂ *ᵥ k' = 0)
    (he : B₁ᵀ *ᵥ x + B₂ *ᵥ y + k = B₁ᵀ *ᵥ x' + B₂ *ᵥ y' + k') :
    B₁ᵀ *ᵥ x = B₁ᵀ *ᵥ x' ∧ B₂ *ᵥ y = B₂ *ᵥ y' ∧ k = k' :=
  sorry

/-- **LAP-10** `dim ker L₁ + rank ∂₂ = dim ker ∂₁`: the harmonic flows count the first Betti
number, `dim ker ∂₁ − dim im ∂₂`. -/
theorem finrank_harm (h : B₁ * B₂ = 0) :
    Module.finrank ℝ (LinearMap.ker (lap1 B₁ B₂).mulVecLin) + B₂.rank =
      Module.finrank ℝ (LinearMap.ker B₁.mulVecLin) :=
  sorry

/-- **LAP-9** Every edge flow splits into a gradient, a curl and a harmonic flow. -/
theorem exists_hodge (h : B₁ * B₂ = 0) (c : E → ℝ) :
    ∃ x y, lap1 B₁ B₂ *ᵥ (c - B₁ᵀ *ᵥ x - B₂ *ᵥ y) = 0 :=
  sorry

/-! ### Orientation -/

variable [DecidableEq E] [DecidableEq T]

/-- **LAP-11** Reorienting the edges by signs `σ` and the triangles by `τ` conjugates `L₁` by the
involution `diag σ`. -/
theorem lap1_reorient (σ : E → ℝ) (τ : T → ℝ) (hτ : ∀ t, τ t * τ t = 1) :
    lap1 (B₁ * diagonal σ) (diagonal σ * B₂ * diagonal τ) =
      diagonal σ * lap1 B₁ B₂ * diagonal σ :=
  sorry

omit [Fintype V] in
/-- **LAP-11** A reoriented complex is still a complex. -/
theorem reorient_complex (h : B₁ * B₂ = 0) (σ : E → ℝ) (τ : T → ℝ) (hσ : ∀ e, σ e * σ e = 1) :
    B₁ * diagonal σ * (diagonal σ * B₂ * diagonal τ) = 0 :=
  sorry

/-- **LAP-11** So the spectrum does not depend on the orientation. -/
theorem charpoly_reorient (σ : E → ℝ) (τ : T → ℝ) (hσ : ∀ e, σ e * σ e = 1)
    (hτ : ∀ t, τ t * τ t = 1) :
    (lap1 (B₁ * diagonal σ) (diagonal σ * B₂ * diagonal τ)).charpoly = (lap1 B₁ B₂).charpoly :=
  sorry

/-- **LAP-11** Nor does the dimension of the harmonic flows. -/
theorem finrank_harm_reorient (σ : E → ℝ) (τ : T → ℝ) (hσ : ∀ e, σ e * σ e = 1)
    (hτ : ∀ t, τ t * τ t = 1) :
    Module.finrank ℝ
        (LinearMap.ker (lap1 (B₁ * diagonal σ) (diagonal σ * B₂ * diagonal τ)).mulVecLin) =
      Module.finrank ℝ (LinearMap.ker (lap1 B₁ B₂).mulVecLin) :=
  sorry

/-- **LAP-11** And the split carries over: reorienting a gradient, a curl and a harmonic flow
gives the reoriented complex's gradient, curl and harmonic flow. -/
theorem hodge_reorient (σ : E → ℝ) (τ : T → ℝ) (hσ : ∀ e, σ e * σ e = 1)
    (hτ : ∀ t, τ t * τ t = 1) (x : V → ℝ) (y : T → ℝ) {k : E → ℝ} (hk : lap1 B₁ B₂ *ᵥ k = 0) :
    diagonal σ *ᵥ (B₁ᵀ *ᵥ x) = (B₁ * diagonal σ)ᵀ *ᵥ x ∧
      diagonal σ *ᵥ (B₂ *ᵥ y) = (diagonal σ * B₂ * diagonal τ) *ᵥ (diagonal τ *ᵥ y) ∧
      lap1 (B₁ * diagonal σ) (diagonal σ * B₂ * diagonal τ) *ᵥ (diagonal σ *ᵥ k) = 0 :=
  sorry

end Hodge

/-! ### The flag complex's Betti number -/

/-- **LAP-10** On the flag complex of any graph, `dim ker L₁ + rank ∂₂ = dim ker ∂₁`. -/
theorem flag_finrank_harm {V : Type*} [LinearOrder V] [Fintype V] (G : SimpleGraph V)
    [DecidableRel G.Adj] :
    Module.finrank ℝ (LinearMap.ker (lap1 (d1 G ℝ) (d2 G ℝ)).mulVecLin) + (d2 G ℝ).rank =
      Module.finrank ℝ (LinearMap.ker (d1 G ℝ).mulVecLin) :=
  sorry

end Palace.Hodge
