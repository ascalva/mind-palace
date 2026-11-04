module

public import Mathlib.Algebra.Order.Chebyshev
public import Palace.Transport.Defs

/-!
# The transports along a supersession: σ_* and σ^*

The limits program's L3 (`docs/brainstorms/limits-of-the-algebra.md`), machine-checked:
temporal-retrieval-algebra §2.3 Result 5 pins the ledger's dilation to the pullback `σ^*` as
"always a contraction". Under a merge it is not: `‖σ^* f‖² = ∑_b |σ⁻¹ b| f_b²`, so the pullback
expands by `√(max fiber)`, and the merge of two notes into one doubles a cochain's energy. The
push-forward is its adjoint and has the same norm; under the inverse-fiber weight on the target
it contracts (TRN-4). The curvature `[d, τ]` of the superconnection `d + τ` is the cochain's drop
across exactly the severed citations, and vanishes iff every citation carries forward or collapses
(TRN-5, Results 1 and 2). The correction is the inner product: under
the fiber-weighted `⟨·,·⟩_σ` on the target, the pullback is an isometry — the weighted inner
product PD-b parked becomes the dilation's customer, exactly where Result 4 predicted it would.
These are design theorems (Palace and this file only; no Spec rows): no code transports cochains
yet.
-/

@[expose] public section

open Finset Matrix

namespace Palace.Transport

variable {A B : Type*} [Fintype A] [Fintype B] [DecidableEq B]

/-- TRN-1 The push-forward is the adjoint of the pullback: `⟨σ_* g, f⟩ = ⟨g, σ^* f⟩`. -/
theorem push_dotProduct (σ : A → B) (g : A → ℝ) (f : B → ℝ) :
    push σ g ⬝ᵥ f = g ⬝ᵥ pull σ f := by
  unfold push pull dotProduct
  simp only [sum_mul]
  rw [← sum_fiberwise (s := univ) (g := σ) (f := fun a ↦ g a * f (σ a))]
  refine sum_congr rfl fun b _ ↦ sum_congr rfl fun a ha ↦ ?_
  rw [(mem_filter.1 ha).2]

/-- TRN-2 The pullback's energy is the fiber-weighted energy: `‖σ^* f‖² = ∑_b |σ⁻¹ b| f_b²`. -/
theorem pull_dotProduct_self (σ : A → B) (f : B → ℝ) :
    pull σ f ⬝ᵥ pull σ f = wdot σ f f := by
  unfold pull wdot fiber dotProduct
  rw [← sum_fiberwise (s := univ) (g := σ) (f := fun a ↦ f (σ a) * f (σ a))]
  refine sum_congr rfl fun b _ ↦ ?_
  rw [sum_congr rfl fun a ha ↦ by rw [(mem_filter.1 ha).2], sum_const, nsmul_eq_mul]

/-- TRN-2 So the pullback expands by at most the widest merge: `‖σ^* f‖² ≤ (max fiber)·‖f‖²`. -/
theorem pull_dotProduct_self_le (σ : A → B) (f : B → ℝ) :
    pull σ f ⬝ᵥ pull σ f ≤ (maxFiber σ : ℝ) * (f ⬝ᵥ f) := by
  rw [pull_dotProduct_self]
  unfold wdot maxFiber dotProduct
  rw [mul_sum]
  refine sum_le_sum fun b _ ↦ ?_
  have hb : fiber σ b ≤ univ.sup (fiber σ) := le_sup (mem_univ b)
  have hsq : 0 ≤ f b * f b := mul_self_nonneg (f b)
  exact mul_le_mul_of_nonneg_right (by exact_mod_cast hb) hsq

/-- TRN-2 And it is attained: the merge of two notes into one doubles the energy of the
constant cochain — the pullback is NOT a contraction (Result 5's claim, refuted). -/
theorem pull_not_contraction :
    ∃ f : Fin 1 → ℝ, f ⬝ᵥ f < pull merge2 f ⬝ᵥ pull merge2 f := by
  refine ⟨fun _ ↦ 1, ?_⟩
  simp [pull, dotProduct]

/-- TRN-3 The correction: under the fiber-weighted inner product on the target, the pullback
is an isometry, `‖σ^* f‖² = ‖f‖²_σ` — the dilation's inner product is read off the merge. -/
theorem pull_isometry_wdot (σ : A → B) (f : B → ℝ) :
    pull σ f ⬝ᵥ pull σ f = wdot σ f f :=
  pull_dotProduct_self σ f

/-- TRN-3 The counting inner product is an isometry for `σ^*` exactly when nothing merges and
nothing is left behind: every fiber is one note. -/
theorem pull_isometry_iff (σ : A → B) :
    (∀ f : B → ℝ, pull σ f ⬝ᵥ pull σ f = f ⬝ᵥ f) ↔ ∀ b, fiber σ b = 1 := by
  constructor
  · intro h b
    have := h (fun c ↦ if c = b then 1 else 0)
    rw [pull_dotProduct_self] at this
    unfold wdot dotProduct at this
    simp only [mul_ite, mul_one, mul_zero, sum_ite_eq', mem_univ, ite_true] at this
    exact_mod_cast this
  · intro h f
    rw [pull_dotProduct_self]
    unfold wdot dotProduct
    simp [h]

/-- TRN-4 The push-forward is a contraction under the inverse-fiber-weighted inner product on
the target, `‖σ_* g‖²_{1/σ} ≤ ‖g‖²`: Cauchy–Schwarz on each fiber. The dual of TRN-3, and the
inner product under which Result 6's γ-contraction reads once supersessions merge. -/
theorem push_wdotInv_le (σ : A → B) (g : A → ℝ) :
    wdotInv σ (push σ g) (push σ g) ≤ g ⬝ᵥ g := by
  unfold wdotInv push fiber dotProduct
  rw [← sum_fiberwise (s := univ) (g := σ) (f := fun a ↦ g a * g a)]
  refine sum_le_sum fun b _ ↦ ?_
  set F := univ.filter (fun a ↦ σ a = b) with hF
  rcases Nat.eq_zero_or_pos F.card with h0 | hpos
  · rw [Finset.card_eq_zero] at h0
    simp [h0]
  · have hc : (0 : ℝ) < F.card := by exact_mod_cast hpos
    rw [inv_mul_le_iff₀ hc, ← sq]
    calc (∑ a ∈ F, g a) ^ 2 ≤ F.card * ∑ a ∈ F, g a ^ 2 := sq_sum_le_card_mul_sum_sq
      _ = F.card * ∑ a ∈ F, g a * g a := by simp [sq]

/-! ### TRN-5 The curvature of the superconnection lives on the severed citations -/

omit [Fintype A] [Fintype B] [DecidableEq B] in
/-- TRN-5 `[d, τ]φ (u, v) = (φ (σ v) − φ (σ u)) · 𝟙[σ u → σ v severed]` (temporal-retrieval §2.3
Result 2): the curvature is the drop of the cochain across exactly the citations that did not
carry forward — the weighted carry-forward failure count, not a proxy for it. -/
theorem curvature_eq (σ : A → B) (X' : B → B → Prop) [DecidableRel X'] (φ : B → ℝ) (u v : A) :
    curvature σ X' φ u v = if X' (σ u) (σ v) then 0 else φ (σ v) - φ (σ u) := by
  unfold curvature coboundary pullEdge
  split_ifs <;> simp

omit [Fintype A] [Fintype B] [DecidableEq B] in
/-- TRN-5 The superconnection is flat on the source's citations iff every one carries forward or
collapses: `[d, τ] = 0` on `X` iff for every `u → v` in `X`, `σ u = σ v` or `σ u → σ v` is in
`X'` — Result 1's F1, the chain-map condition, read on the edges. -/
theorem curvature_eq_zero_iff (σ : A → B) (X : A → A → Prop) (X' : B → B → Prop)
    [DecidableRel X'] :
    (∀ φ : B → ℝ, ∀ u v, X u v → curvature σ X' φ u v = 0) ↔
      ∀ u v, X u v → σ u = σ v ∨ X' (σ u) (σ v) := by
  classical
  constructor
  · intro h u v huv
    by_contra hc
    push Not at hc
    have := h (fun b ↦ if b = σ v then 1 else 0) u v huv
    rw [curvature_eq] at this
    simp [hc.1, hc.2] at this
  · intro h φ u v huv
    rw [curvature_eq]
    rcases h u v huv with heq | hX'
    · simp [heq]
    · simp [hX']

end Palace.Transport
