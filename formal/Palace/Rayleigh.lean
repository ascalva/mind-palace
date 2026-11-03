module

public import Mathlib.Tactic.FinCases
public import Palace.Balance

/-!
# Rayleigh's monotonicity law: CND-2

`core/graph/conductance.py`'s reconnection rider (`reconnection_scan`) reads a rise in effective
conductance `1/R_eff` between two snapshots as a reconnection, and attributes it by reverting the
weight-increased edges one at a time (leave-one-out). Its null rests on Rayleigh's monotonicity
law, cited in the ledger as CND-2: adding weight never raises effective resistance, so "a
decay-only interval (no weight increased) yields no rise". Here the law is proved for the code's
own definitions: `R_eff = L⁺ᵢᵢ + L⁺ⱼⱼ − 2L⁺ᵢⱼ` within a component and `∞` across
(`_r_eff_matrix`), and the conductance `1/R_eff`, `0` across (`_pair_conductance`).

The proof is Thomson's principle in its finite form. For `v` fixed by `M M⁺`, every trial vector
has `2vᵀx − xᵀMx ≤ vᵀM⁺v`, with equality at `x = M⁺v`, so a larger `M` can only lower `vᵀM⁺v`.
That `M M⁺` fixes `v` needs no spectral argument: by the Penrose equations it fixes every vector
orthogonal to `ker M`, and `eᵢ − eⱼ` is orthogonal to `ker L` when `i` and `j` share a component
(LAP-3's reduction).

Leave-one-out, the rider's attribution: reverting an increased edge never raises conductance, and
with a single increased edge every rise confirms it. But a rise carried by two redundant new paths
confirms neither (`Witness.loo_confirms_nothing`): the rider then reports a genuine reconnection
with no bridging edge.
-/

@[expose] public section

open Matrix Finset

namespace Palace

variable {V : Type*} [Fintype V] [DecidableEq V]

/-! ### `M M⁺` fixes the vectors orthogonal to `ker M` -/

omit [Fintype V] [DecidableEq V] in
theorem transpose_eq_of_isHermitian {X : Matrix V V ℝ} (hX : X.IsHermitian) : Xᵀ = X := by
  rw [← conjTranspose_eq_transpose_of_trivial]
  exact hX

omit [DecidableEq V] in
/-- A symmetric matrix moves across the dot product. -/
theorem dotProduct_mulVec_symm {X : Matrix V V ℝ} (hX : X.IsHermitian) (x y : V → ℝ) :
    x ⬝ᵥ (X *ᵥ y) = (X *ᵥ x) ⬝ᵥ y := by
  rw [dotProduct_mulVec, ← mulVec_transpose, transpose_eq_of_isHermitian hX]

/-- `M M⁺` fixes every vector orthogonal to `ker M`, by the Penrose equations alone: the part `w`
of `v` it misses lies in `ker M` and is orthogonal to itself. -/
theorem mulVec_pinv_mulVec_of_orthogonal {M : Matrix V V ℝ} (hM : M.IsHermitian) {v : V → ℝ}
    (hv : ∀ x, M *ᵥ x = 0 → v ⬝ᵥ x = 0) : M *ᵥ (pinv M hM *ᵥ v) = v := by
  have hMP : M * pinv M hM * M = M := mul_pinv_mul hM
  have hcomm : M * pinv M hM = pinv M hM * M := mul_pinv_comm hM
  obtain ⟨w, hw⟩ : ∃ w, w = v - M *ᵥ (pinv M hM *ᵥ v) := ⟨_, rfl⟩
  have hMw : M *ᵥ w = 0 := by
    have : M * M * pinv M hM = M := by rw [Matrix.mul_assoc, hcomm, ← Matrix.mul_assoc, hMP]
    rw [hw, mulVec_sub, mulVec_mulVec, mulVec_mulVec, this, sub_self]
  have hsym : (M * pinv M hM).IsHermitian := by
    rw [IsHermitian, conjTranspose_mul, (isHermitian_pinv hM).eq, hM.eq, hcomm]
  have h1 : v ⬝ᵥ w = 0 := hv w hMw
  have h2 : (M *ᵥ (pinv M hM *ᵥ v)) ⬝ᵥ w = 0 := by
    rw [mulVec_mulVec, ← dotProduct_mulVec_symm hsym, hcomm, ← mulVec_mulVec, hMw, mulVec_zero,
      dotProduct_zero]
  have h3 : w ⬝ᵥ w = 0 := by
    have : w ⬝ᵥ w = v ⬝ᵥ w - (M *ᵥ (pinv M hM *ᵥ v)) ⬝ᵥ w := by
      conv_lhs => arg 1; rw [hw]
      rw [sub_dotProduct]
    rw [this, h1, h2, sub_zero]
  have h0 := dotProduct_self_eq_zero.1 h3
  rw [hw, sub_eq_zero] at h0
  exact h0.symm

/-! ### Thomson's principle and Rayleigh's law, for matrices -/

/-- **Thomson's principle**, the bound: for positive semidefinite `M` and `v` fixed by `M M⁺`,
every trial vector `x` has `2vᵀx − xᵀMx ≤ vᵀM⁺v`. -/
theorem thomson {M : Matrix V V ℝ} (hP : M.PosSemidef) {v : V → ℝ}
    (hv : M *ᵥ (pinv M hP.isHermitian *ᵥ v) = v) (x : V → ℝ) :
    2 * (v ⬝ᵥ x) - x ⬝ᵥ (M *ᵥ x) ≤ v ⬝ᵥ (pinv M hP.isHermitian *ᵥ v) := by
  set y := pinv M hP.isHermitian *ᵥ v
  have h := hP.dotProduct_mulVec_nonneg (x - y)
  rw [star_trivial, mulVec_sub, dotProduct_sub, sub_dotProduct, sub_dotProduct, hv] at h
  have e1 : y ⬝ᵥ (M *ᵥ x) = v ⬝ᵥ x := by rw [dotProduct_mulVec_symm hP.isHermitian, hv]
  have e2 : x ⬝ᵥ v = v ⬝ᵥ x := dotProduct_comm _ _
  have e3 : y ⬝ᵥ v = v ⬝ᵥ y := dotProduct_comm _ _
  linarith

/-- **Rayleigh's law**, for matrices: the larger positive semidefinite matrix has the smaller
`vᵀM⁺v`, for `v` fixed by both. -/
theorem dotProduct_pinv_anti {M M' : Matrix V V ℝ} (hP : M.PosSemidef) (hP' : M'.PosSemidef)
    (hle : (M' - M).PosSemidef) {v : V → ℝ} (hv : M *ᵥ (pinv M hP.isHermitian *ᵥ v) = v)
    (hv' : M' *ᵥ (pinv M' hP'.isHermitian *ᵥ v) = v) :
    v ⬝ᵥ (pinv M' hP'.isHermitian *ᵥ v) ≤ v ⬝ᵥ (pinv M hP.isHermitian *ᵥ v) := by
  set y := pinv M' hP'.isHermitian *ᵥ v
  have hb := thomson hP hv y
  have hd := hle.dotProduct_mulVec_nonneg y
  rw [star_trivial, sub_mulVec, dotProduct_sub, hv'] at hd
  have e : y ⬝ᵥ v = v ⬝ᵥ y := dotProduct_comm _ _
  linarith

/-! ### Rayleigh's law for effective resistance -/

theorem lap_sub_lap (A A' : Matrix V V ℝ) : lap A' - lap A = lap (A' - A) := by
  ext i j
  simp only [lap, Matrix.sub_apply, diagonal_apply, degree]
  split_ifs
  · simp only [Finset.sum_sub_distrib]
    ring
  · ring

omit [Fintype V] [DecidableEq V] in
/-- More weight keeps every edge of the support. -/
theorem support_mono {A A' : Matrix V V ℝ} (hw : ∀ i j, 0 ≤ A i j)
    (hle : ∀ i j, A i j ≤ A' i j) : support A ≤ support A' := by
  intro a b hab
  simp only [support, SimpleGraph.fromRel_adj] at hab ⊢
  refine ⟨hab.1, hab.2.imp (fun h ↦ ?_) (fun h ↦ ?_)⟩
  · exact ((lt_of_le_of_ne (hw a b) (Ne.symm h)).trans_le (hle a b)).ne'
  · exact ((lt_of_le_of_ne (hw b a) (Ne.symm h)).trans_le (hle b a)).ne'

/-- `eᵢ − eⱼ` is orthogonal to `ker L` when `i` and `j` share a component: kernel vectors are
constant on components (LAP-3's reduction). -/
theorem orthogonal_ker_lap {A : Matrix V V ℝ} (hA : A.IsSymm) (hw : ∀ i j, 0 ≤ A i j) {i j : V}
    (hr : (support A).Reachable i j) (x : V → ℝ) (hx : lap A *ᵥ x = 0) :
    (Pi.single i 1 - Pi.single j 1) ⬝ᵥ x = 0 := by
  have hc := (lap_mulVec_eq_zero_iff A hA hw x).1 hx
  have hij : x i = x j := eq_of_reachable (fun a b hab ↦ by
    simp only [support, SimpleGraph.fromRel_adj] at hab
    rcases hab.2 with h | h
    · exact hc a b h
    · exact (hc b a h).symm) hr
  simp [sub_dotProduct, single_dotProduct, hij]

/-- CND-1's form is the quadratic form at `eᵢ − eⱼ`. -/
theorem rEff_eq_dotProduct {X : Matrix V V ℝ} (hX : X.IsHermitian) (i j : V) :
    rEff X i j = (Pi.single i 1 - Pi.single j 1) ⬝ᵥ (X *ᵥ (Pi.single i 1 - Pi.single j 1)) := by
  have hs : X j i = X i j := by simpa using hX.apply i j
  simp only [rEff, mulVec_sub, mulVec_single_one, dotProduct_sub, sub_dotProduct,
    single_dotProduct, col_apply, one_mul]
  linarith

/-- **CND-2, Rayleigh's monotonicity law**: adding weight never raises the effective resistance
between two vertices of one component. -/
theorem rEff_anti {A A' : Matrix V V ℝ} (hA : A.IsSymm) (hA' : A'.IsSymm) (hw : ∀ i j, 0 ≤ A i j)
    (hle : ∀ i j, A i j ≤ A' i j) {i j : V} (hr : (support A).Reachable i j) :
    rEff (lapPinv A' hA') i j ≤ rEff (lapPinv A hA) i j := by
  have hw' : ∀ i j, 0 ≤ A' i j := fun i j ↦ (hw i j).trans (hle i j)
  have hP := posSemidef_lap A hA hw
  have hP' := posSemidef_lap A' hA' hw'
  have hD : (lap A' - lap A).PosSemidef := by
    rw [lap_sub_lap]
    exact posSemidef_lap _ (hA'.sub hA) fun i j ↦ sub_nonneg.2 (hle i j)
  have hr' := hr.mono (support_mono hw hle)
  rw [rEff_eq_dotProduct (isHermitian_lapPinv A' hA'),
    rEff_eq_dotProduct (isHermitian_lapPinv A hA)]
  exact dotProduct_pinv_anti hP hP' hD
    (mulVec_pinv_mulVec_of_orthogonal hP.isHermitian (orthogonal_ker_lap hA hw hr))
    (mulVec_pinv_mulVec_of_orthogonal hP'.isHermitian (orthogonal_ker_lap hA' hw' hr'))

/-- Between distinct vertices of one component the effective resistance is positive. -/
theorem rEff_pos {A : Matrix V V ℝ} (hA : A.IsSymm) (hw : ∀ i j, 0 ≤ A i j) {i j : V}
    (hr : (support A).Reachable i j) (hij : i ≠ j) : 0 < rEff (lapPinv A hA) i j := by
  have hP := posSemidef_lap A hA hw
  refine lt_of_le_of_ne (rEff_lapPinv_nonneg A hA hw i j) fun h0 ↦ ?_
  have hq : star (Pi.single i 1 - Pi.single j 1) ⬝ᵥ
      (lapPinv A hA *ᵥ (Pi.single i 1 - Pi.single j 1)) = 0 := by
    rw [star_trivial, ← rEff_eq_dotProduct (isHermitian_lapPinv A hA)]
    exact h0.symm
  have hz := (posSemidef_lapPinv A hA hw).dotProduct_mulVec_zero_iff.1 hq
  have hfix := mulVec_pinv_mulVec_of_orthogonal hP.isHermitian (orthogonal_ker_lap hA hw hr)
  rw [show pinv (lap A) hP.isHermitian = lapPinv A hA from rfl, hz, mulVec_zero] at hfix
  simpa [Pi.single_apply, hij] using congrFun hfix i

open Classical in
/-- The code's effective resistance (`_r_eff_matrix`): `R_eff` within a component, `∞` across. -/
noncomputable def resistance (A : Matrix V V ℝ) (hA : A.IsSymm) (i j : V) : WithTop ℝ :=
  if (support A).Reachable i j then ((rEff (lapPinv A hA) i j : ℝ) : WithTop ℝ) else ⊤

/-- **CND-2** Rayleigh's law with the code's `∞` across components. -/
theorem resistance_anti {A A' : Matrix V V ℝ} (hA : A.IsSymm) (hA' : A'.IsSymm)
    (hw : ∀ i j, 0 ≤ A i j) (hle : ∀ i j, A i j ≤ A' i j) (i j : V) :
    resistance A' hA' i j ≤ resistance A hA i j := by
  unfold resistance
  by_cases hr : (support A).Reachable i j
  · have hr' := hr.mono (support_mono hw hle)
    simp only [hr, hr', ↓reduceIte]
    exact WithTop.coe_le_coe.2 (rEff_anti hA hA' hw hle hr)
  · simp only [hr, ↓reduceIte]
    exact le_top

open Classical in
/-- The code's effective conductance (`_pair_conductance`): `1/R_eff` within a component and `0`
across; at a vertex itself `R_eff = 0`, and Lean's `0⁻¹ = 0` agrees with the code's `r > ε`
guard. -/
noncomputable def effConductance (A : Matrix V V ℝ) (hA : A.IsSymm) (i j : V) : ℝ :=
  if (support A).Reachable i j then (rEff (lapPinv A hA) i j)⁻¹ else 0

theorem effConductance_nonneg {A : Matrix V V ℝ} (hA : A.IsSymm) (hw : ∀ i j, 0 ≤ A i j)
    (i j : V) : 0 ≤ effConductance A hA i j := by
  unfold effConductance
  split_ifs
  · exact inv_nonneg.2 (rEff_lapPinv_nonneg A hA hw i j)
  · exact le_rfl

/-- **CND-2** Adding weight never lowers effective conductance. -/
theorem effConductance_mono {A A' : Matrix V V ℝ} (hA : A.IsSymm) (hA' : A'.IsSymm)
    (hw : ∀ i j, 0 ≤ A i j) (hle : ∀ i j, A i j ≤ A' i j) (i j : V) :
    effConductance A hA i j ≤ effConductance A' hA' i j := by
  have hw' : ∀ i j, 0 ≤ A' i j := fun i j ↦ (hw i j).trans (hle i j)
  by_cases hr : (support A).Reachable i j
  · have hr' := hr.mono (support_mono hw hle)
    unfold effConductance
    simp only [hr, hr', ↓reduceIte]
    by_cases hij : i = j
    · subst hij
      have h0 : ∀ X : Matrix V V ℝ, rEff X i i = 0 := fun X ↦ by simp only [rEff]; ring
      rw [h0, h0]
    · exact inv_anti₀ (rEff_pos hA' hw' hr' hij) (rEff_anti hA hA' hw hle hr)
  · have : effConductance A hA i j = 0 := by
      unfold effConductance
      simp only [hr, ↓reduceIte]
    rw [this]
    exact effConductance_nonneg hA' hw' i j

/-- **CND-2** A rise in effective conductance needs a weight-increased edge: with no weight
increased, no pair's conductance rises, `reconnection_scan`'s null. -/
theorem exists_increased_of_rise {A A' : Matrix V V ℝ} (hA : A.IsSymm) (hA' : A'.IsSymm)
    (hw' : ∀ i j, 0 ≤ A' i j) {p q : V}
    (h : effConductance A hA p q < effConductance A' hA' p q) : ∃ i j, A i j < A' i j := by
  by_contra hne
  simp only [not_exists, not_lt] at hne
  exact absurd (effConductance_mono hA' hA hw' hne p q) (not_le.2 h)

/-! ### Leave-one-out -/

/-- The rider's reversion of edge `a — b`: its before-weight set back into the after-matrix
(`w_loo[i, j] = w_loo[j, i] = w_before[i, j]`). -/
def revert (A A' : Matrix V V ℝ) (a b : V) : Matrix V V ℝ :=
  of fun i j ↦ if (i = a ∧ j = b) ∨ (i = b ∧ j = a) then A i j else A' i j

omit [Fintype V] in
theorem revert_isSymm {A A' : Matrix V V ℝ} (hA : A.IsSymm) (hA' : A'.IsSymm) (a b : V) :
    (revert A A' a b).IsSymm := by
  ext i j
  simp only [revert, transpose_apply, of_apply]
  have hc : ((j = a ∧ i = b) ∨ (j = b ∧ i = a)) ↔ ((i = a ∧ j = b) ∨ (i = b ∧ j = a)) := by tauto
  by_cases h : (i = a ∧ j = b) ∨ (i = b ∧ j = a)
  · simp only [hc.2 h, h, ↓reduceIte]
    exact hA.apply i j
  · simp only [mt hc.1 h, h, ↓reduceIte]
    exact hA'.apply i j

omit [Fintype V] in
theorem revert_nonneg {A A' : Matrix V V ℝ} (hw : ∀ i j, 0 ≤ A i j) (hw' : ∀ i j, 0 ≤ A' i j)
    (a b : V) (i j : V) : 0 ≤ revert A A' a b i j := by
  simp only [revert, of_apply]
  split_ifs
  · exact hw i j
  · exact hw' i j

/-- **Leave-one-out** A reversion never raises conductance: it only lowers an increased edge. -/
theorem effConductance_revert_le {A A' : Matrix V V ℝ} (hA : A.IsSymm) (hA' : A'.IsSymm)
    (hw : ∀ i j, 0 ≤ A i j) (hw' : ∀ i j, 0 ≤ A' i j) {a b : V} (hab : A a b ≤ A' a b)
    (p q : V) :
    effConductance (revert A A' a b) (revert_isSymm hA hA' a b) p q ≤
      effConductance A' hA' p q := by
  refine effConductance_mono _ hA' (revert_nonneg hw hw' a b) (fun i j ↦ ?_) p q
  simp only [revert, of_apply]
  split_ifs with h
  · rcases h with ⟨rfl, rfl⟩ | ⟨rfl, rfl⟩
    · exact hab
    · rw [hA.apply, hA'.apply]
      exact hab
  · exact le_rfl

/-- **Leave-one-out** With a single increased edge, every rise confirms it: reverting it brings
the conductance back to at most its before-value. -/
theorem effConductance_revert_single {A A' : Matrix V V ℝ} (hA : A.IsSymm) (hA' : A'.IsSymm)
    (hw : ∀ i j, 0 ≤ A i j) (hw' : ∀ i j, 0 ≤ A' i j) {a b : V}
    (hsingle : ∀ i j, ¬((i = a ∧ j = b) ∨ (i = b ∧ j = a)) → A' i j ≤ A i j) (p q : V) :
    effConductance (revert A A' a b) (revert_isSymm hA hA' a b) p q ≤ effConductance A hA p q := by
  refine effConductance_mono _ hA (revert_nonneg hw hw' a b) (fun i j ↦ ?_) p q
  simp only [revert, of_apply]
  split_ifs with h
  · exact le_rfl
  · exact hsingle i j h

namespace Witness

/-- The unit-weight edge `a — b` on three vertices. -/
def edge (a b : Fin 3) : Matrix (Fin 3) (Fin 3) ℝ :=
  of fun i j ↦ if (i = a ∧ j = b) ∨ (i = b ∧ j = a) then 1 else 0

theorem edge_isSymm (a b : Fin 3) : (edge a b).IsSymm := by
  ext i j
  simp only [edge, transpose_apply, of_apply]
  congr 1
  exact propext (by tauto)

theorem edge_nonneg (a b i j : Fin 3) : 0 ≤ edge a b i j := by
  simp only [edge, of_apply]
  split_ifs <;> norm_num

/-- Before: the edge `0 — 1`. -/
def before : Matrix (Fin 3) (Fin 3) ℝ := edge 0 1

/-- After: two new edges, `1 — 2` and `0 — 2`, each a way from `0` to `2` on its own. -/
def after : Matrix (Fin 3) (Fin 3) ℝ := edge 0 1 + edge 1 2 + edge 0 2

theorem before_isSymm : before.IsSymm := edge_isSymm 0 1

theorem after_isSymm : after.IsSymm :=
  ((edge_isSymm 0 1).add (edge_isSymm 1 2)).add (edge_isSymm 0 2)

theorem before_nonneg (i j : Fin 3) : 0 ≤ before i j := edge_nonneg 0 1 i j

theorem after_nonneg (i j : Fin 3) : 0 ≤ after i j := by
  simp only [after, Matrix.add_apply]
  linarith [edge_nonneg 0 1 i j, edge_nonneg 1 2 i j, edge_nonneg 0 2 i j]

/-- Before, `0` and `2` lie in different components. -/
theorem not_reachable_before : ¬(support before).Reachable 0 2 := by
  intro hr
  have := eq_of_reachable (f := fun v : Fin 3 ↦ decide (v = 2)) (fun a b hab ↦ by
    simp only [support, SimpleGraph.fromRel_adj, before, edge, of_apply] at hab
    fin_cases a <;> fin_cases b <;> simp_all) hr
  simp at this

/-- A positive weight is an edge of the support. -/
theorem reachable_of_pos {A : Matrix (Fin 3) (Fin 3) ℝ} {a b : Fin 3} (hab : a ≠ b)
    (h : 0 < A a b) : (support A).Reachable a b :=
  SimpleGraph.Adj.reachable (by
    simp only [support, SimpleGraph.fromRel_adj]
    exact ⟨hab, Or.inl h.ne'⟩)

/-- Reconnected `0` and `2` have positive conductance. -/
theorem effConductance_pos {A : Matrix (Fin 3) (Fin 3) ℝ} (hA : A.IsSymm)
    (hw : ∀ i j, 0 ≤ A i j) (hr : (support A).Reachable 0 2) : 0 < effConductance A hA 0 2 := by
  unfold effConductance
  simp only [hr, ↓reduceIte]
  exact inv_pos.2 (rEff_pos hA hw hr (by decide))

/-- **Leave-one-out can confirm nothing.** From `before` to `after`, `0` and `2` go from
different components to one: a genuine rise. Yet each new edge alone still joins them, so
reverting either leaves the rise in place, and the rider reports the reconnection with no
bridging edge. -/
theorem loo_confirms_nothing :
    effConductance before before_isSymm 0 2 < effConductance after after_isSymm 0 2 ∧
      ∀ a b, before a b < after a b →
        effConductance before before_isSymm 0 2 <
          effConductance (revert before after a b) (revert_isSymm before_isSymm after_isSymm a b)
            0 2 := by
  have h0 : effConductance before before_isSymm 0 2 = 0 := by
    unfold effConductance
    simp only [not_reachable_before, ↓reduceIte]
  refine ⟨h0 ▸ effConductance_pos after_isSymm after_nonneg
    (reachable_of_pos (by decide) (by simp [after, edge])), fun a b hab ↦ ?_⟩
  rw [h0]
  refine effConductance_pos _ (revert_nonneg before_nonneg after_nonneg a b) ?_
  simp only [before, after, edge, Matrix.add_apply, of_apply] at hab
  fin_cases a <;> fin_cases b <;> norm_num at hab
  · -- reverting `0 — 2` leaves the path `0 — 1 — 2`
    exact (reachable_of_pos (b := 1) (by decide) (by simp [revert, after, edge])).trans
      (reachable_of_pos (by decide) (by simp [revert, after, edge]))
  · -- reverting `1 — 2` leaves the edge `0 — 2`
    exact reachable_of_pos (by decide) (by simp [revert, after, edge])
  · exact (reachable_of_pos (b := 1) (by decide) (by simp [revert, after, edge])).trans
      (reachable_of_pos (by decide) (by simp [revert, after, edge]))
  · exact reachable_of_pos (by decide) (by simp [revert, after, edge])

end Witness

end Palace
