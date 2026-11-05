module

public import Mathlib.Algebra.Order.Chebyshev
public import Mathlib.Tactic.Ring
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
Result 5 is true where the versions store puts it: along a merge-free supersession the pullback is
a contraction (`pull_dotProduct_self_le_self_of_injective`), and `core/stores/versions.py` refuses
to merge two lineages. Result 6 — the strict γ-contraction of confidence-weighted cochains, the
owner's promotion the only energy source — is exact under the depth-weighted inner product
`⟨f, g⟩_{γ,d} = ∑ γ^{d b} f_b g_b` (TRN-6 to TRN-8): a merge-free step one level deeper contracts
the energy by exactly `γ`, a merge keeps the contraction iff `γ · (max fiber) ≤ 1`, and a
promotion `k` levels shallower injects `γ^{-k}`. These are design theorems (Palace and this file
only; no Spec rows): no code transports cochains yet.
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

omit [DecidableEq B] in
/-- TRN-2 On a merge-free supersession the pullback IS a contraction, `‖σ^* f‖² ≤ ‖f‖²`: Result 5
holds exactly where the versions store puts it — lineages that never merge (the store's refusal
of a merge, `RekeyRefusedError`, is this theorem's hypothesis). -/
theorem pull_dotProduct_self_le_self_of_injective {σ : A → B} (hσ : Function.Injective σ)
    (f : B → ℝ) : pull σ f ⬝ᵥ pull σ f ≤ f ⬝ᵥ f := by
  classical
  rw [pull_dotProduct_self]
  unfold wdot dotProduct
  refine sum_le_sum fun b _ ↦ ?_
  have h1 : fiber σ b ≤ 1 := by
    unfold fiber
    exact Finset.card_le_one.2 fun a ha a' ha' ↦
      hσ ((mem_filter.1 ha).2.trans (mem_filter.1 ha').2.symm)
  have h1' : (fiber σ b : ℝ) ≤ 1 := by exact_mod_cast h1
  exact mul_le_of_le_one_left (mul_self_nonneg (f b)) h1'

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

/-! ### TRN-6 to TRN-8 Result 6: the γ-contraction, and the owner as the only energy source -/

omit [Fintype B] in
/-- Along a merge-free supersession the push-forward reads the source at the preimage. -/
theorem push_apply_of_injective {σ : A → B} (hσ : Function.Injective σ) (g : A → ℝ) (a : A) :
    push σ g (σ a) = g a := by
  unfold push
  have : univ.filter (fun a' ↦ σ a' = σ a) = {a} := by
    ext a'
    simp [hσ.eq_iff]
  rw [this, sum_singleton]

omit [Fintype B] in
/-- Off the image of `σ`, the push-forward is zero: nothing was superseded into that note. -/
theorem push_apply_of_not_mem_range {σ : A → B} (g : A → ℝ) {b : B} (hb : b ∉ Set.range σ) :
    push σ g b = 0 := by
  unfold push
  refine sum_eq_zero fun a ha ↦ absurd ⟨a, (mem_filter.1 ha).2⟩ hb

/-- TRN-6 The transport formula: along a merge-free supersession, the push-forward's confidence
energy on the target is the source's with every note weighed at its new depth,
`‖σ_* g‖²_{γ,d'} = ∑_a γ^{d'(σ a)} g_a²`. -/
theorem wdotDepth_push_of_injective {σ : A → B} (hσ : Function.Injective σ) (γ : ℝ) (d' : B → ℕ)
    (g : A → ℝ) :
    wdotDepth γ d' (push σ g) (push σ g) = ∑ a, γ ^ d' (σ a) * (g a * g a) := by
  unfold wdotDepth
  rw [← sum_subset (subset_univ (univ.image σ)) ?_]
  · rw [sum_image fun a _ b _ h ↦ hσ h]
    refine sum_congr rfl fun a _ ↦ ?_
    rw [push_apply_of_injective hσ]
  · intro b _ hb
    simp only [mem_image, mem_univ, true_and, not_exists] at hb
    rw [push_apply_of_not_mem_range (σ := σ) g fun ⟨a, ha⟩ ↦ hb a ha]
    simp

/-- TRN-6 Result 6's γ-contraction: a machine supersession — merge-free, every successor one
level deeper — contracts the confidence energy by exactly `γ`,
`‖σ_* g‖²_{γ,d'} = γ · ‖g‖²_{γ,d}`. -/
theorem wdotDepth_push_eq_mul {σ : A → B} (hσ : Function.Injective σ) (γ : ℝ) (d : A → ℕ)
    (d' : B → ℕ) (hd : ∀ a, d' (σ a) = d a + 1) (g : A → ℝ) :
    wdotDepth γ d' (push σ g) (push σ g) = γ * wdotDepth γ d g g := by
  rw [wdotDepth_push_of_injective hσ]
  unfold wdotDepth
  rw [mul_sum]
  refine sum_congr rfl fun a _ ↦ ?_
  rw [hd a, pow_succ]
  ring

/-- TRN-7 With merges the contraction survives up to the widest fiber: when every successor is
one level deeper, `‖σ_* g‖²_{γ,d'} ≤ γ · (max fiber) · ‖g‖²_{γ,d}` — Cauchy–Schwarz on each
fiber — so a merge of `m` notes keeps Result 6's contraction iff `γ · m ≤ 1`: at the default
`γ = 1/2`, a two-way merge is the horizon. -/
theorem wdotDepth_push_le (σ : A → B) {γ : ℝ} (hγ : 0 ≤ γ) (d : A → ℕ) (d' : B → ℕ)
    (hd : ∀ a, d' (σ a) = d a + 1) (g : A → ℝ) :
    wdotDepth γ d' (push σ g) (push σ g) ≤ γ * maxFiber σ * wdotDepth γ d g g := by
  unfold wdotDepth
  calc ∑ b, γ ^ d' b * (push σ g b * push σ g b)
      ≤ ∑ b, (maxFiber σ : ℝ) *
          ∑ a ∈ univ.filter (fun a ↦ σ a = b), γ ^ d' (σ a) * (g a * g a) := by
        refine sum_le_sum fun b _ ↦ ?_
        unfold push
        have hpow : 0 ≤ γ ^ d' b := pow_nonneg hγ _
        have hcard : ((univ.filter (fun a ↦ σ a = b)).card : ℝ) ≤ maxFiber σ := by
          exact_mod_cast le_sup (f := fiber σ) (mem_univ b)
        have hcs := sq_sum_le_card_mul_sum_sq (s := univ.filter (fun a ↦ σ a = b)) (f := g)
        have hsum : ∑ a ∈ univ.filter (fun a ↦ σ a = b), γ ^ d' (σ a) * (g a * g a)
            = γ ^ d' b * ∑ a ∈ univ.filter (fun a ↦ σ a = b), g a ^ 2 := by
          rw [mul_sum]
          refine sum_congr rfl fun a ha ↦ ?_
          rw [(mem_filter.1 ha).2, sq]
        have hs : 0 ≤ ∑ a ∈ univ.filter (fun a ↦ σ a = b), g a ^ 2 :=
          sum_nonneg fun a _ ↦ sq_nonneg _
        rw [hsum, ← sq]
        calc γ ^ d' b * (∑ a ∈ univ.filter (fun a ↦ σ a = b), g a) ^ 2
            ≤ γ ^ d' b * (((univ.filter (fun a ↦ σ a = b)).card : ℝ)
                * ∑ a ∈ univ.filter (fun a ↦ σ a = b), g a ^ 2) :=
              mul_le_mul_of_nonneg_left hcs hpow
          _ = ((univ.filter (fun a ↦ σ a = b)).card : ℝ)
                * (γ ^ d' b * ∑ a ∈ univ.filter (fun a ↦ σ a = b), g a ^ 2) := by ring
          _ ≤ (maxFiber σ : ℝ) * (γ ^ d' b * ∑ a ∈ univ.filter (fun a ↦ σ a = b), g a ^ 2) :=
              mul_le_mul_of_nonneg_right hcard (mul_nonneg hpow hs)
    _ = (maxFiber σ : ℝ) * ∑ a, γ ^ d' (σ a) * (g a * g a) := by
        rw [← mul_sum, sum_fiberwise (s := univ) (g := σ) (f := fun a ↦ γ ^ d' (σ a) * (g a * g a))]
    _ = γ * maxFiber σ * ∑ a, γ ^ d a * (g a * g a) := by
        rw [mul_sum, mul_sum]
        refine sum_congr rfl fun a _ ↦ ?_
        rw [hd a, pow_succ]
        ring

/-- TRN-8 The owner is the only energy source (Result 6's exception, made exact): along a
merge-free supersession whose every successor is re-anchored `k` levels shallower — an owner
promotion — the confidence energy is multiplied by `γ^{-k}`, `‖σ_* g‖²_{γ,d'} = γ⁻¹^k · ‖g‖²_{γ,d}`,
an injection (`γ⁻¹^k > 1` for `γ < 1`, `k ≥ 1`) no machine step can produce. -/
theorem wdotDepth_push_eq_promotion {σ : A → B} (hσ : Function.Injective σ) {γ : ℝ} (hγ : 0 < γ)
    (d : A → ℕ) (d' : B → ℕ) (k : ℕ) (hd : ∀ a, d' (σ a) + k = d a) (g : A → ℝ) :
    wdotDepth γ d' (push σ g) (push σ g) = γ⁻¹ ^ k * wdotDepth γ d g g := by
  rw [wdotDepth_push_of_injective hσ]
  unfold wdotDepth
  rw [mul_sum]
  refine sum_congr rfl fun a _ ↦ ?_
  have hk : γ ^ k ≠ 0 := pow_ne_zero k hγ.ne'
  rw [← hd a, pow_add, inv_pow]
  calc γ ^ d' (σ a) * (g a * g a)
      = (γ ^ k)⁻¹ * γ ^ k * (γ ^ d' (σ a) * (g a * g a)) := by rw [inv_mul_cancel₀ hk, one_mul]
    _ = (γ ^ k)⁻¹ * (γ ^ d' (σ a) * γ ^ k * (g a * g a)) := by ring

/-- TRN-8 The injection is real: a promotion by at least one level, at any `γ < 1`, multiplies
the energy by more than one. -/
theorem one_lt_inv_pow_of_lt_one {γ : ℝ} (hγ : 0 < γ) (hγ1 : γ < 1) {k : ℕ} (hk : k ≠ 0) :
    1 < γ⁻¹ ^ k :=
  one_lt_pow₀ ((one_lt_inv₀ hγ).2 hγ1) hk

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
