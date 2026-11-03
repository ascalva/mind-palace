module

public import Palace.Bridges.Defs
public import Mathlib.Order.UpperLower.CompleteLattice
public import Palace.Clock
public import Palace.Hodge
public import Palace.Laplacian
public import Palace.Plane
public import Palace.Rayleigh
public import Palace.Scope

/-!
# Bridges between the families: BRG-1 to BRG-6

Theorems that join two families' structures, so that a fact proved in one serves the other:

* BRG-1: the Laplacian of `Palace/Laplacian.lean` on a graph's 0/1 adjacency is `∂₁ ∂₁ᵀ`, the
  vertex end of the Hodge complex of `Palace/Hodge.lean`.
* BRG-2: on the flag complex, the Euler characteristic `|V| − |E| + |T|` is the number of
  components (LAP-3's nullity) less the first Betti number (LAP-10's harmonic dimension) plus the
  second: Euler and Poincaré, from the two families' laws.
* BRG-3: Thomson's principle of `Palace/Rayleigh.lean`, read on edge flows: for `M = B Bᵀ`, every
  flow meeting a demand has energy at least `vᵀ M⁺ v`, and the gradient flow `Bᵀ M⁺ v` attains it.
  On a graph, by BRG-1, the effective resistance is the least energy of a unit flow.
* BRG-4: the clock's cuts and scope's refinement-closed strata are both the lower sets of a
  reachability preorder, Mathlib's `LowerSet`s, a completely distributive lattice.
* BRG-5: delegation cannot leak through the plane: a delegated scope's clearance lies within its
  parent's, and the plane's noninterference holds of it.
* BRG-6: Forman's curvature of `Palace/Curvature.lean` is the Weitzenböck term of `L₁`, the
  diagonal entry less the absolute values of the rest of the row: the curvature is read off the
  Hodge Laplacian of `Palace/Hodge.lean`.
-/

@[expose] public section

open Relation Matrix

namespace Palace.Bridges

/-! ## BRG-1 and BRG-2: the Laplacian is the Hodge complex's vertex end -/

section Complex

open Palace.Hodge Finset

variable {V : Type*} [LinearOrder V] [Fintype V] (G : SimpleGraph V) [DecidableRel G.Adj]

/-- The entries of `∂₁ ∂₁ᵀ`, as a sum over ordered pairs. -/
theorem d1_mul_transpose_apply (R : Type*) [CommRing R] (v w : V) :
    (d1 G R * (d1 G R)ᵀ) v w = ∑ p : V × V with p.1 < p.2 ∧ G.Adj p.1 p.2,
      ((if v = p.2 then 1 else 0) - (if v = p.1 then 1 else 0)) *
      ((if w = p.2 then 1 else 0) - (if w = p.1 then (1 : R) else 0)) := by
  rw [Matrix.mul_apply]
  simp only [transpose_apply, d1, Pi.sub_apply, Pi.single_apply]
  exact (Finset.sum_subtype _ (fun p ↦ by simp) (fun p : V × V ↦
    ((if v = p.2 then 1 else 0) - (if v = p.1 then 1 else 0)) *
      ((if w = p.2 then 1 else 0) - (if w = p.1 then (1 : R) else 0)))).symm

/-- **BRG-1** The vertex end of the Hodge complex is the graph Laplacian: `∂₁ ∂₁ᵀ = D − A`,
Mathlib's `lapMatrix`, over any commutative ring. -/
theorem d1_mul_transpose (R : Type*) [CommRing R] :
    d1 G R * (d1 G R)ᵀ = G.lapMatrix R := by
  ext v w
  rw [d1_mul_transpose_apply, SimpleGraph.lapMatrix, SimpleGraph.degMatrix, Matrix.sub_apply,
    diagonal_apply, SimpleGraph.adjMatrix_apply, Finset.sum_filter, Fintype.sum_prod_type]
  by_cases hvw : v = w
  · subst hvw
    simp only [G.irrefl, ↓reduceIte, sub_zero]
    rw [SimpleGraph.degree_eq_sum_if_adj (G := G) (R := R) v]
    -- `(δ_y − δ_x)² = δ_y + δ_x` on an edge `x < y`: each edge counts once at each end
    have h (x y : V) : (if x < y ∧ G.Adj x y then
        ((if v = y then (1 : R) else 0) - if v = x then 1 else 0) *
          ((if v = y then 1 else 0) - if v = x then 1 else 0) else 0) =
        (if v = y then (if x < v ∧ G.Adj x v then 1 else 0) else 0) +
        (if v = x then (if v < y ∧ G.Adj v y then 1 else 0) else 0) := by
      by_cases hy : v = y <;> by_cases hx : v = x <;> subst_vars <;> split_ifs <;> simp_all
    simp only [h, Finset.sum_add_distrib, Finset.sum_ite_irrel, Finset.sum_const_zero,
      Finset.sum_ite_eq, Finset.mem_univ, ite_true]
    rw [← Finset.sum_add_distrib]
    refine Finset.sum_congr rfl fun u _ ↦ ?_
    by_cases hvu : G.Adj v u
    · rcases lt_or_gt_of_ne (G.ne_of_adj hvu) with h' | h'
      · simp [hvu, h', hvu.symm, h'.not_gt]
      · simp [hvu, h', hvu.symm, h'.not_gt]
    · have huv : ¬G.Adj u v := fun h ↦ hvu h.symm
      simp [hvu, huv]
  · simp only [hvw, ↓reduceIte, zero_sub]
    -- off the diagonal only the edge between `v` and `w` contributes, once, with sign `−1`
    have h (x y : V) : (if x < y ∧ G.Adj x y then
        ((if v = y then (1 : R) else 0) - if v = x then 1 else 0) *
          ((if w = y then 1 else 0) - if w = x then 1 else 0) else 0) =
        -((if v = y then (if w = x then (if x < y ∧ G.Adj x y then 1 else 0) else 0) else 0) +
          (if w = y then (if v = x then (if x < y ∧ G.Adj x y then 1 else 0) else 0) else 0)) := by
      by_cases hy : v = y <;> by_cases hx : v = x <;> by_cases hwy : w = y <;>
        by_cases hwx : w = x <;> subst_vars <;> split_ifs <;> simp_all
    simp only [h, Finset.sum_neg_distrib, Finset.sum_add_distrib, Finset.sum_ite_eq,
      Finset.mem_univ, ite_true]
    congr 1
    by_cases hvw' : G.Adj v w
    · rcases lt_or_gt_of_ne hvw with h' | h'
      · simp [hvw', h', hvw'.symm, h'.not_gt]
      · simp [hvw', h', hvw'.symm, h'.not_gt]
    · have hwv : ¬G.Adj w v := fun h ↦ hvw' h.symm
      simp [hvw', hwv]

/-- **BRG-1** So it is `lap` of the 0/1 adjacency, the Laplacian of LAP-1 to LAP-3. -/
theorem d1_mul_transpose_eq_lap (R : Type*) [CommRing R] :
    d1 G R * (d1 G R)ᵀ = lap (G.adjMatrix R) :=
  (d1_mul_transpose G R).trans (lap_adjMatrix G).symm

/-- **BRG-2** The components are the cokernel of `∂₁`: their number and `∂₁`'s rank make up the
vertices (LAP-3, read on `∂₁ ∂₁ᵀ` by BRG-1). -/
theorem card_components_add_rank :
    Fintype.card G.ConnectedComponent + (d1 G ℝ).rank = Fintype.card V := by
  have hc := card_components_eq_nullity_adjMatrix G
  rw [← d1_mul_transpose_eq_lap] at hc
  have hn := LinearMap.finrank_range_add_finrank_ker (d1 G ℝ * (d1 G ℝ)ᵀ).mulVecLin
  rw [Module.finrank_fintype_fun_eq_card] at hn
  have hr := Matrix.rank_self_mul_transpose (d1 G ℝ)
  rw [Matrix.rank] at hr
  rw [hc, ← hr]
  exact (add_comm _ _).trans hn

/-- **BRG-2** Euler and Poincaré on the flag complex: `|V| − |E| + |T| = b₀ − b₁ + b₂`, with `b₀`
the components (LAP-3), `b₁` the harmonic flows (LAP-10) and `b₂` the 2-cycles, `ker ∂₂`. -/
theorem euler_poincare :
    (Fintype.card V : ℤ) - Fintype.card (Edge G) + Fintype.card (Tri G) =
      Fintype.card G.ConnectedComponent -
        Module.finrank ℝ (LinearMap.ker (lap1 (d1 G ℝ) (d2 G ℝ)).mulVecLin) +
        Module.finrank ℝ (LinearMap.ker (d2 G ℝ).mulVecLin) := by
  have hc := card_components_add_rank G
  have hh := flag_finrank_harm G
  have h1 := LinearMap.finrank_range_add_finrank_ker (d1 G ℝ).mulVecLin
  have h2 := LinearMap.finrank_range_add_finrank_ker (d2 G ℝ).mulVecLin
  simp only [Module.finrank_fintype_fun_eq_card] at h1 h2
  simp only [Matrix.rank] at hc hh
  omega

end Complex

/-! ## BRG-3: Thomson's principle on flows -/

section Thomson

variable {V E : Type*} [Fintype V] [DecidableEq V] [Fintype E]

omit [DecidableEq V] in
theorem dotProduct_transpose_mulVec (B : Matrix V E ℝ) (f : E → ℝ) (y : V → ℝ) :
    f ⬝ᵥ (Bᵀ *ᵥ y) = (B *ᵥ f) ⬝ᵥ y := by
  rw [dotProduct_mulVec, vecMul_transpose]

/-- The energy `‖f − g‖²` of a flow's distance from the gradient flow, by the demand. -/
theorem energy_sub_gradient (B : Matrix V E ℝ) (hM : (B * Bᵀ).IsHermitian) {v : V → ℝ}
    (hv : (B * Bᵀ) *ᵥ (pinv (B * Bᵀ) hM *ᵥ v) = v) {f : E → ℝ} (hf : B *ᵥ f = v) :
    (f - Bᵀ *ᵥ (pinv (B * Bᵀ) hM *ᵥ v)) ⬝ᵥ (f - Bᵀ *ᵥ (pinv (B * Bᵀ) hM *ᵥ v)) =
      f ⬝ᵥ f - v ⬝ᵥ (pinv (B * Bᵀ) hM *ᵥ v) := by
  set y := pinv (B * Bᵀ) hM *ᵥ v
  have hfg : f ⬝ᵥ (Bᵀ *ᵥ y) = v ⬝ᵥ y := by rw [dotProduct_transpose_mulVec, hf]
  have hgg : (Bᵀ *ᵥ y) ⬝ᵥ (Bᵀ *ᵥ y) = v ⬝ᵥ y := by
    rw [dotProduct_transpose_mulVec, mulVec_mulVec, hv]
  rw [sub_dotProduct, dotProduct_sub, dotProduct_sub, dotProduct_comm (Bᵀ *ᵥ y) f, hfg, hgg]
  ring

/-- **BRG-3** Thomson's principle, on flows. For an incidence `B` and a demand `v` that `M M⁺`
fixes, `M = B Bᵀ`, every flow meeting the demand, `B f = v`, has energy at least `vᵀ M⁺ v`: the
value whose potentials `thomson` bounds from the other side, Rayleigh's law compares, and CND-1
reads as the effective resistance. -/
theorem energy_ge (B : Matrix V E ℝ) (hM : (B * Bᵀ).IsHermitian) {v : V → ℝ}
    (hv : (B * Bᵀ) *ᵥ (pinv (B * Bᵀ) hM *ᵥ v) = v) {f : E → ℝ} (hf : B *ᵥ f = v) :
    v ⬝ᵥ (pinv (B * Bᵀ) hM *ᵥ v) ≤ f ⬝ᵥ f := by
  have h := energy_sub_gradient B hM hv hf
  have h0 : 0 ≤ (f - Bᵀ *ᵥ (pinv (B * Bᵀ) hM *ᵥ v)) ⬝ᵥ (f - Bᵀ *ᵥ (pinv (B * Bᵀ) hM *ᵥ v)) :=
    Finset.sum_nonneg fun _ _ ↦ mul_self_nonneg _
  linarith

/-- **BRG-3** The gradient flow `Bᵀ M⁺ v`, the gradient of the potential `M⁺ v`, meets the demand
with exactly that energy. -/
theorem gradient_flow (B : Matrix V E ℝ) (hM : (B * Bᵀ).IsHermitian) {v : V → ℝ}
    (hv : (B * Bᵀ) *ᵥ (pinv (B * Bᵀ) hM *ᵥ v) = v) :
    B *ᵥ (Bᵀ *ᵥ (pinv (B * Bᵀ) hM *ᵥ v)) = v ∧
      (Bᵀ *ᵥ (pinv (B * Bᵀ) hM *ᵥ v)) ⬝ᵥ (Bᵀ *ᵥ (pinv (B * Bᵀ) hM *ᵥ v)) =
        v ⬝ᵥ (pinv (B * Bᵀ) hM *ᵥ v) := by
  refine ⟨by rw [mulVec_mulVec, hv], ?_⟩
  rw [dotProduct_transpose_mulVec, mulVec_mulVec, hv]

/-- **BRG-3** And it is the only flow meeting the demand with that energy: the energy minimizer is
the gradient part, the projection of `Palace/Hodge.lean`'s split. -/
theorem energy_eq_iff (B : Matrix V E ℝ) (hM : (B * Bᵀ).IsHermitian) {v : V → ℝ}
    (hv : (B * Bᵀ) *ᵥ (pinv (B * Bᵀ) hM *ᵥ v) = v) {f : E → ℝ} (hf : B *ᵥ f = v) :
    f ⬝ᵥ f = v ⬝ᵥ (pinv (B * Bᵀ) hM *ᵥ v) ↔ f = Bᵀ *ᵥ (pinv (B * Bᵀ) hM *ᵥ v) := by
  rw [← sub_eq_zero (a := f), ← dotProduct_self_eq_zero, energy_sub_gradient B hM hv hf,
    sub_eq_zero]

end Thomson

/-! ### Thomson's principle on a graph -/

section ThomsonGraph

open Palace.Hodge

variable {V : Type*} [LinearOrder V] [Fintype V] (G : SimpleGraph V) [DecidableRel G.Adj]

theorem pinv_congr {M N : Matrix V V ℝ} (h : M = N) (hM : M.IsHermitian) (hN : N.IsHermitian) :
    pinv M hM = pinv N hN := by
  subst h; rfl

/-- `rEff` is the quadratic form of a symmetric matrix on `δ_j − δ_i`. -/
theorem rEff_eq_dotProduct {X : Matrix V V ℝ} (hX : X.IsSymm) (i j : V) :
    rEff X i j =
      (Pi.single j 1 - Pi.single i 1) ⬝ᵥ (X *ᵥ (Pi.single j 1 - Pi.single i 1)) := by
  have hji : X j i = X i j := by simpa using congrFun (congrFun hX.eq i) j
  simp only [rEff, mulVec_sub, mulVec_single_one, sub_dotProduct, dotProduct_sub,
    single_one_dotProduct, col_apply, hji]
  ring

/-- **BRG-3** On a graph, by BRG-1: the effective resistance between `i` and `j` (CND-1) is at
most the energy of every unit flow from `i` to `j` along the edges, when the demand can be met,
and the gradient flow attains it (`gradient_flow`). -/
theorem rEff_le_energy {i j : V}
    (hv : lap (G.adjMatrix ℝ) *ᵥ (lapPinv (G.adjMatrix ℝ) G.isSymm_adjMatrix *ᵥ
      (Pi.single j 1 - Pi.single i 1)) = Pi.single j 1 - Pi.single i 1)
    {f : Edge G → ℝ} (hf : d1 G ℝ *ᵥ f = Pi.single j 1 - Pi.single i 1) :
    rEff (lapPinv (G.adjMatrix ℝ) G.isSymm_adjMatrix) i j ≤ f ⬝ᵥ f := by
  have hL := d1_mul_transpose_eq_lap G ℝ
  have hM : (d1 G ℝ * (d1 G ℝ)ᵀ).IsHermitian := by
    rw [hL]; exact isHermitian_lap _ G.isSymm_adjMatrix
  have hp : pinv (d1 G ℝ * (d1 G ℝ)ᵀ) hM = lapPinv (G.adjMatrix ℝ) G.isSymm_adjMatrix :=
    pinv_congr hL _ _
  have hsymm : (lapPinv (G.adjMatrix ℝ) G.isSymm_adjMatrix).IsSymm := by
    have := (posSemidef_lapPinv (G.adjMatrix ℝ) G.isSymm_adjMatrix fun a b ↦ by
      rw [SimpleGraph.adjMatrix_apply]; split_ifs <;> norm_num).isHermitian
    rwa [IsHermitian, conjTranspose_eq_transpose_of_trivial] at this
  rw [rEff_eq_dotProduct hsymm, ← hp]
  exact energy_ge (d1 G ℝ) hM (by rw [hp, hL]; exact hv) hf

end ThomsonGraph

/-! ## BRG-4: cuts and refinement-closed strata are lower sets -/

section LowerSets

/-- **BRG-4** A cut of the clock is a lower set of `≼`, reachability along the generators, so the
cuts carry the lattice of Mathlib's `LowerSet`s. -/
theorem isCut_iff_isLowerSet {E : Type*} (g : E → E → Prop) (S : Set E) :
    Clock.IsCut g S ↔ @IsLowerSet E (reach g).toLE S :=
  ⟨fun h _ _ hba ha ↦ h _ _ hba ha, fun h _ _ hab hb ↦ h hab hb⟩

/-- **BRG-4** A set of strata closed under refinement is a cut of the refinement relation: scope's
`Σ` and the clock's cuts are one structure. -/
theorem isDown_iff_isCut (S : Finset CQ.Stratum) :
    CQ.IsDown S ↔ Clock.IsCut Refines (↑S : Set CQ.Stratum) := by
  rw [Clock.isCut_iff_not_crossed, Clock.Crossed, CQ.IsDown]
  simp only [Refines, Finset.mem_coe, not_exists, not_and, not_not]
  exact ⟨fun h c p hcp hp ↦ h c p hcp.1 hcp.2 hp, fun h c p hc hcp hp ↦ h c p ⟨hc, hcp⟩ hp⟩

/-- **BRG-4** So the refinement-closed sets of strata are lower sets too. -/
theorem isDown_iff_isLowerSet (S : Finset CQ.Stratum) :
    CQ.IsDown S ↔ @IsLowerSet CQ.Stratum (reach Refines).toLE ↑S :=
  (isDown_iff_isCut S).trans (isCut_iff_isLowerSet Refines _)

end LowerSets

/-! ## BRG-5: delegation cannot leak through the plane -/

section Delegation

variable {P D A : Type*} [DecidableEq P] [LinearOrder D] [DecidableEq A]

omit [DecidableEq P] [LinearOrder D] in
/-- A reader cleared for fewer classes cannot tell apart what a reader cleared for more cannot. -/
theorem view_anti {K : Type*} [DecidableEq K] {C C' : Finset K} (h : C' ⊆ C)
    {s t : Plane.State K P D A} (hv : Plane.view C s = Plane.view C t) :
    Plane.view C' s = Plane.view C' t := by
  simp only [Plane.view, Prod.mk.injEq] at hv ⊢
  obtain ⟨hrel, htab⟩ := hv
  have hct : ∀ c ∈ C, s.occ c = t.occ c ∧ s.sup c = t.sup c := fun c hc ↦ by
    simpa [hc] using congrFun hrel c
  have hrefs : Plane.refs C' s = Plane.refs C' t :=
    Finset.biUnion_congr rfl fun c hc ↦ by rw [(hct c (h hc)).1]
  have hsub (u : Plane.State K P D A) : Plane.refs C' u ⊆ Plane.refs C u :=
    Finset.biUnion_subset_biUnion_of_subset_left _ h
  refine ⟨funext fun c ↦ ?_, ?_⟩
  · by_cases hc : c ∈ C'
    · simp [hc, (hct c (h hc)).1, (hct c (h hc)).2]
    · simp [hc]
  · calc s.table ∩ Plane.refs C' s = s.table ∩ Plane.refs C s ∩ Plane.refs C' s := by
          rw [Finset.inter_assoc, Finset.inter_eq_right.2 (hsub s)]
      _ = t.table ∩ Plane.refs C t ∩ Plane.refs C' t := by rw [htab, hrefs]
      _ = t.table ∩ Plane.refs C' t := by
          rw [Finset.inter_assoc, Finset.inter_eq_right.2 (hsub t)]

/-- **BRG-5** Delegation cannot leak through the plane. A delegated scope, the meet of a parent's
and a template's, is cleared for no class its parent is not; states its parent cannot tell apart,
it cannot either; and after any trace of writes that keep each path at its stratum, it reads what
it would have read had only the writes it is cleared for, the purges and the repairs happened. -/
theorem delegation_noninterference {parent template m : CQ.Scope}
    (hm : parent.meet template = .ok m) (κ : P → CQ.Prov) :
    CQ.classesOf CQ.stratumClasses m.sigma ⊆ CQ.classesOf CQ.stratumClasses parent.sigma ∧
    (∀ s t : Plane.State CQ.Prov P D A,
      Plane.view (CQ.classesOf CQ.stratumClasses parent.sigma) s =
        Plane.view (CQ.classesOf CQ.stratumClasses parent.sigma) t →
      Plane.view (CQ.classesOf CQ.stratumClasses m.sigma) s =
        Plane.view (CQ.classesOf CQ.stratumClasses m.sigma) t) ∧
    ∀ (ops : List (Plane.Op CQ.Prov P D A)) {s t : Plane.State CQ.Prov P D A},
      Plane.Good κ s → Plane.Good κ t →
      Plane.view (CQ.classesOf CQ.stratumClasses m.sigma) s =
        Plane.view (CQ.classesOf CQ.stratumClasses m.sigma) t →
      (∀ op ∈ ops, op.Respects κ) →
      Plane.view (CQ.classesOf CQ.stratumClasses m.sigma) (Plane.run ops s) =
        Plane.view (CQ.classesOf CQ.stratumClasses m.sigma)
          (Plane.run (ops.filter (·.visible (CQ.classesOf CQ.stratumClasses m.sigma))) t) := by
  have hsub := (CQ.classesOf_meet hm).trans Finset.inter_subset_left
  exact ⟨hsub, fun s t hv ↦ view_anti hsub hv,
    fun ops _ _ hs ht hv hops ↦ Plane.noninterference ops hs ht hv hops⟩

end Delegation

/-! ## BRG-6: Forman's curvature is the Weitzenböck term of `L₁` -/

section Weitzenbock

open Palace.Hodge Finset

variable {V : Type*} [LinearOrder V] [Fintype V] {G : SimpleGraph V} [DecidableRel G.Adj]

/-- A sum over the flag complex's edges, as a sum over ordered pairs of vertices. -/
theorem sum_edge {M : Type*} [AddCommMonoid M] (f : Edge G → M) :
    ∑ e, f e = ∑ k, ∑ l, if h : k < l ∧ G.Adj k l then f ⟨(k, l), h⟩ else 0 := by
  let g (p : V × V) : M := if h : p.1 < p.2 ∧ G.Adj p.1 p.2 then f ⟨p, h⟩ else 0
  calc ∑ e, f e = ∑ e : Edge G, g e.1 := Finset.sum_congr rfl fun e _ ↦
        (dite_eq_left (t := fun h ↦ f ⟨e.1, h⟩) e.2).symm
    _ = ∑ p ∈ univ.filter fun p : V × V ↦ p.1 < p.2 ∧ G.Adj p.1 p.2, g p :=
        (Finset.sum_subtype _ (fun p ↦ by simp) g).symm
    _ = ∑ p, g p := Finset.sum_filter_of_ne fun p _ hp ↦ by
        by_contra h; exact hp (dite_eq_right h)
    _ = _ := Fintype.sum_prod_type g

/-- A sum over the flag complex's triangles, as a sum over ordered triples of vertices. -/
theorem sum_tri {M : Type*} [AddCommMonoid M] (f : V × V × V → M) :
    ∑ t : Tri G, f t.1 = ∑ a, ∑ b, ∑ c,
      if a < b ∧ b < c ∧ G.Adj a b ∧ G.Adj b c ∧ G.Adj a c then f (a, b, c) else 0 := by
  rw [← Finset.sum_subtype (univ.filter fun t : V × V × V ↦ t.1 < t.2.1 ∧ t.2.1 < t.2.2 ∧
    G.Adj t.1 t.2.1 ∧ G.Adj t.2.1 t.2.2 ∧ G.Adj t.1 t.2.2) (fun t ↦ by simp) f,
    Finset.sum_filter, Fintype.sum_prod_type]
  simp only [Fintype.sum_prod_type]

/-- The triangles on `ij` are counted by the common neighbours of its ends. -/
theorem card_common (i j : V) : ((G.neighborFinset i ∩ G.neighborFinset j).card : ℤ) =
    ∑ w, if G.Adj i w ∧ G.Adj j w then 1 else 0 := by
  rw [← Finset.natCast_card_filter]
  congr 2
  ext w
  simp

omit [DecidableRel G.Adj] in
/-- The entries of `∂₁ᵀ ∂₁`: `e_ij · e_kl = [j = l] − [j = k] − [i = l] + [i = k]`. -/
theorem transpose_mul_d1_apply (e e' : Edge G) :
    ((d1 G ℤ)ᵀ * d1 G ℤ) e e' =
      (if e.1.2 = e'.1.2 then 1 else 0) - (if e.1.2 = e'.1.1 then 1 else 0) -
        (if e.1.1 = e'.1.2 then 1 else 0) + (if e.1.1 = e'.1.1 then 1 else 0) := by
  simp only [Matrix.mul_apply, transpose_apply, d1, Pi.sub_apply, Pi.single_apply, sub_mul,
    mul_sub, ite_mul, one_mul, zero_mul, Finset.sum_sub_distrib, Finset.sum_ite_eq',
    Finset.mem_univ, ite_true]
  ring

omit [Fintype V] [DecidableRel G.Adj] in
/-- `∂₂`'s entries, read off the ends: `e` is the triangle's edge `jk`, `ik` or `ij`. -/
theorem d2_apply (e : Edge G) (t : Tri G) :
    d2 G ℤ e t = (if e.1 = (t.1.2.1, t.1.2.2) then 1 else 0) -
      (if e.1 = (t.1.1, t.1.2.2) then 1 else 0) + (if e.1 = (t.1.1, t.1.2.1) then 1 else 0) := by
  simp [d2, edgeJK, edgeIK, edgeIJ, Subtype.ext_iff]

/-- A sum over the triangles weighted by `∂₂`'s entries on `e = ij` is a sum over the third
vertex `w`: the triangle `wij` with sign `+`, `iwj` with `−` and `ijw` with `+`. -/
theorem sum_d2_mul (e : Edge G) (f : V × V × V → ℤ) :
    ∑ t : Tri G, d2 G ℤ e t * f t.1 =
      ∑ w, ((if w < e.1.1 ∧ G.Adj w e.1.1 ∧ G.Adj w e.1.2 then f (w, e.1.1, e.1.2) else 0) -
        (if e.1.1 < w ∧ w < e.1.2 ∧ G.Adj e.1.1 w ∧ G.Adj w e.1.2 then f (e.1.1, w, e.1.2)
          else 0) +
        (if e.1.2 < w ∧ G.Adj e.1.2 w ∧ G.Adj e.1.1 w then f (e.1.1, e.1.2, w) else 0)) := by
  obtain ⟨⟨i, j⟩, hij, hadj⟩ := e
  simp only [d2_apply]
  refine (sum_tri (G := G) fun p ↦ ((if (i, j) = (p.2.1, p.2.2) then 1 else 0) -
    (if (i, j) = (p.1, p.2.2) then 1 else 0) + (if (i, j) = (p.1, p.2.1) then 1 else 0)) *
      f p).trans ?_
  -- `e` is one edge of the triangle `abc`, which pins two of its vertices to `i` and `j`
  have h (a b c : V) : (if a < b ∧ b < c ∧ G.Adj a b ∧ G.Adj b c ∧ G.Adj a c then
      ((if (i, j) = (b, c) then (1 : ℤ) else 0) - (if (i, j) = (a, c) then 1 else 0) +
        (if (i, j) = (a, b) then 1 else 0)) * f (a, b, c) else 0) =
      (if i = b then if j = c then
        (if a < i ∧ G.Adj a i ∧ G.Adj a j then f (a, i, j) else 0) else 0 else 0) -
      (if i = a then if j = c then
        (if i < b ∧ b < j ∧ G.Adj i b ∧ G.Adj b j then f (i, b, j) else 0) else 0 else 0) +
      (if i = a then if j = b then
        (if j < c ∧ G.Adj j c ∧ G.Adj i c then f (i, j, c) else 0) else 0 else 0) := by
    by_cases hb : i = b <;> by_cases hc : j = c <;> by_cases ha : i = a <;>
      by_cases hb' : j = b <;> subst_vars <;> simp_all [neg_ite]
  simp only [h, Finset.sum_add_distrib, Finset.sum_sub_distrib, Finset.sum_ite_irrel,
    Finset.sum_const_zero, Finset.sum_ite_eq, Finset.mem_univ, ite_true]

/-- The entries of `∂₂ ∂₂ᵀ`, as a sum over the third vertex of the triangles on `e`. -/
theorem d2_mul_transpose_apply (e e' : Edge G) :
    (d2 G ℤ * (d2 G ℤ)ᵀ) e e' = ∑ w,
      ((if w < e.1.1 ∧ G.Adj w e.1.1 ∧ G.Adj w e.1.2 then
          (if e'.1 = (e.1.1, e.1.2) then 1 else 0) - (if e'.1 = (w, e.1.2) then 1 else 0) +
            (if e'.1 = (w, e.1.1) then 1 else 0) else 0) -
        (if e.1.1 < w ∧ w < e.1.2 ∧ G.Adj e.1.1 w ∧ G.Adj w e.1.2 then
          (if e'.1 = (w, e.1.2) then 1 else 0) - (if e'.1 = (e.1.1, e.1.2) then 1 else 0) +
            (if e'.1 = (e.1.1, w) then 1 else 0) else 0) +
        (if e.1.2 < w ∧ G.Adj e.1.2 w ∧ G.Adj e.1.1 w then
          (if e'.1 = (e.1.2, w) then 1 else 0) - (if e'.1 = (e.1.1, w) then 1 else 0) +
            (if e'.1 = (e.1.1, e.1.2) then 1 else 0) else 0)) := by
  rw [Matrix.mul_apply]
  simp only [transpose_apply, d2_apply e']
  exact sum_d2_mul e fun p ↦ (if e'.1 = (p.2.1, p.2.2) then 1 else 0) -
    (if e'.1 = (p.1, p.2.2) then 1 else 0) + (if e'.1 = (p.1, p.2.1) then 1 else 0)

/-- `L₁`'s diagonal: `2` from the ends, and one for each triangle on the edge. -/
theorem lap1_apply_self (e : Edge G) :
    lap1 (d1 G ℤ) (d2 G ℤ) e e =
      2 + ((G.neighborFinset e.1.1 ∩ G.neighborFinset e.1.2).card : ℤ) := by
  rw [lap1, Matrix.add_apply, transpose_mul_d1_apply, d2_mul_transpose_apply]
  obtain ⟨⟨i, j⟩, hij, hadj⟩ := e
  dsimp only at hij hadj ⊢
  -- each common neighbour `w` closes one triangle on `ij`, whichever side of `i` and `j` it lies
  have h (w : V) : ((if w < i ∧ G.Adj w i ∧ G.Adj w j then
          (if (i, j) = (i, j) then (1 : ℤ) else 0) - (if (i, j) = (w, j) then 1 else 0) +
            (if (i, j) = (w, i) then 1 else 0) else 0) -
        (if i < w ∧ w < j ∧ G.Adj i w ∧ G.Adj w j then
          (if (i, j) = (w, j) then 1 else 0) - (if (i, j) = (i, j) then 1 else 0) +
            (if (i, j) = (i, w) then 1 else 0) else 0) +
        (if j < w ∧ G.Adj j w ∧ G.Adj i w then
          (if (i, j) = (j, w) then 1 else 0) - (if (i, j) = (i, w) then 1 else 0) +
            (if (i, j) = (i, j) then 1 else 0) else 0)) =
      if G.Adj i w ∧ G.Adj j w then 1 else 0 := by
    rcases lt_trichotomy w i with hw | rfl | hw
    · simp [hw, hw.ne', hw.not_gt, (hw.trans hij).not_gt, G.adj_comm]
    · simp
    · rcases lt_trichotomy w j with hw' | rfl | hw'
      · simp [hw, hw', hw.ne, hw'.ne', hw.not_gt, hw'.not_gt, neg_ite, G.adj_comm]
      · simp [G.adj_comm]
      · simp [hw', hw'.ne, hw.not_gt, hw'.not_gt, and_comm, G.adj_comm]
  rw [card_common, Finset.sum_congr rfl fun w _ ↦ h w]
  simp [hij.ne, hij.ne']

/-- Off the diagonal, the triangles' part: a triangle on `e` and `e'` gives `−1` where they meet
tail to tail or head to head, and `+1` where one's head is the other's tail. -/
theorem d2_mul_transpose_apply_of_ne {e e' : Edge G} (h : e ≠ e') :
    (d2 G ℤ * (d2 G ℤ)ᵀ) e e' =
      -(if e'.1.2 = e.1.2 ∧ G.Adj e.1.1 e'.1.1 then 1 else 0) -
        (if e'.1.1 = e.1.1 ∧ G.Adj e.1.2 e'.1.2 then 1 else 0) +
        (if e'.1.2 = e.1.1 ∧ G.Adj e'.1.1 e.1.2 then 1 else 0) +
        (if e'.1.1 = e.1.2 ∧ G.Adj e.1.1 e'.1.2 then 1 else 0) := by
  rw [d2_mul_transpose_apply]
  obtain ⟨⟨i, j⟩, hij, hadj⟩ := e
  obtain ⟨⟨k, l⟩, hkl, hadj'⟩ := e'
  dsimp only at hij hadj hkl hadj' ⊢
  have hne : ¬(k = i ∧ l = j) := fun ⟨h1, h2⟩ ↦ h (by subst h1 h2; rfl)
  -- only the triangles whose third vertex is `k` or `l` count
  rw [Fintype.sum_eq_add k l hkl.ne fun w hw ↦ by
    simp [hne, Ne.symm hw.1, Ne.symm hw.2]]
  rcases eq_or_ne l j with rfl | hlj
  · have hki : k ≠ i := fun h' ↦ hne ⟨h', rfl⟩
    rcases lt_or_gt_of_ne hki with hk | hk
    · simp [hk, hkl, hadj', hki, hij.ne', hkl.ne, hkl.ne', hk.not_gt, G.adj_comm, neg_ite]
    · simp [hk, hkl, hadj', hki, hij.ne', hkl.ne, hkl.ne', hk.not_gt, G.adj_comm]
  rcases eq_or_ne l i with rfl | hli
  · simp [hkl, hadj', hij.ne, hkl.ne, hkl.ne', (hkl.trans hij).ne, hij.not_gt, G.adj_comm]
  rcases eq_or_ne k i with rfl | hki
  · rcases lt_or_gt_of_ne hlj with hl | hl
    · simp [hl, hkl, hadj', hlj, hli, hij.ne, hkl.ne, hl.not_gt, G.adj_comm]
    · simp [hl, hkl, hadj', hlj, hli, hij.ne, hkl.ne, hl.not_gt, G.adj_comm, neg_ite]
  rcases eq_or_ne k j with rfl | hkj
  · simp [hkl, hadj', hlj, hli, hki, hkl.ne, hij.not_gt, G.adj_comm]
  · simp [hlj, hli, hki, hkj, hkl.ne, hkl.ne']

/-- Off the diagonal, `|L₁ e e'|` is `1` when `e = ij` and `e' = kl` share an end and their other
ends are not adjacent, and `0` otherwise: on a triangle the two parts cancel exactly. -/
theorem abs_lap1_apply_of_ne {e e' : Edge G} (h : e ≠ e') :
    |lap1 (d1 G ℤ) (d2 G ℤ) e e'| =
      (if e'.1.2 = e.1.2 ∧ ¬G.Adj e.1.1 e'.1.1 then 1 else 0) +
      (if e'.1.1 = e.1.1 ∧ ¬G.Adj e.1.2 e'.1.2 then 1 else 0) +
      (if e'.1.2 = e.1.1 ∧ ¬G.Adj e'.1.1 e.1.2 then 1 else 0) +
      (if e'.1.1 = e.1.2 ∧ ¬G.Adj e.1.1 e'.1.2 then 1 else 0) := by
  rw [lap1, Matrix.add_apply, transpose_mul_d1_apply, d2_mul_transpose_apply_of_ne h]
  obtain ⟨⟨i, j⟩, hij, hadj⟩ := e
  obtain ⟨⟨k, l⟩, hkl, hadj'⟩ := e'
  dsimp only at hij hadj hkl hadj' ⊢
  have hne : ¬(k = i ∧ l = j) := fun ⟨h1, h2⟩ ↦ h (by subst h1 h2; rfl)
  rcases eq_or_ne l j with rfl | hlj
  · have hki : k ≠ i := fun h' ↦ hne ⟨h', rfl⟩
    by_cases ha : G.Adj i k <;> simp [ha, hki, hki.symm, hkl.ne, hkl.ne', hij.ne, hij.ne']
  rcases eq_or_ne l i with rfl | hli
  · by_cases ha : G.Adj k j <;>
      simp [ha, hkl.ne, hkl.ne', hij.ne, hij.ne', (hkl.trans hij).ne, (hkl.trans hij).ne']
  rcases eq_or_ne k i with rfl | hki
  · by_cases ha : G.Adj j l <;> simp [ha, hlj, hlj.symm, hli, hli.symm, hij.ne, hij.ne']
  rcases eq_or_ne k j with rfl | hkj
  · by_cases ha : G.Adj i l <;> simp [ha, hlj, hlj.symm, hli, hli.symm, hki, hij.ne]
  · simp [hlj, hlj.symm, hli, hli.symm, hki, hki.symm, hkj, hkj.symm]

/-- **BRG-6** Forman's augmented curvature of an edge, `4 − deg i − deg j + 3·|△(i, j)|` (CRV-1),
is the Weitzenböck term of the Hodge Laplacian `L₁` on the flag complex (LAP-8):
`L₁ e e − Σ_{e' ≠ e} |L₁ e e'|`. The diagonal is `2 + |△|`; off it, the down and up adjacencies
cancel exactly between edges that share a triangle, and each other edge at an end counts once. -/
theorem forman_eq_weitzenbock (e : Edge G) :
    forman G e.1.1 e.1.2 = weitzenbock (lap1 (d1 G ℤ) (d2 G ℤ)) e := by
  rw [weitzenbock, lap1_apply_self, Finset.filter_ne', Finset.sum_congr rfl fun e' he' ↦
    abs_lap1_apply_of_ne (Finset.ne_of_mem_erase he').symm,
    Finset.sum_erase_eq_sub (Finset.mem_univ e), sum_edge]
  obtain ⟨⟨i, j⟩, hij, hadj⟩ := e
  dsimp only at hij hadj ⊢
  -- each edge `kl` counts at the end it shares with `ij`
  have hk (k l : V) : (if _ : k < l ∧ G.Adj k l then
      (if l = j ∧ ¬G.Adj i k then (1 : ℤ) else 0) + (if k = i ∧ ¬G.Adj j l then 1 else 0) +
        (if l = i ∧ ¬G.Adj k j then 1 else 0) + (if k = j ∧ ¬G.Adj i l then 1 else 0) else 0) =
      (if l = j then if k < j ∧ G.Adj k j ∧ ¬G.Adj i k then 1 else 0 else 0) +
      (if k = i then if i < l ∧ G.Adj i l ∧ ¬G.Adj j l then 1 else 0 else 0) +
      (if l = i then if k < i ∧ G.Adj k i ∧ ¬G.Adj k j then 1 else 0 else 0) +
      (if k = j then if j < l ∧ G.Adj j l ∧ ¬G.Adj i l then 1 else 0 else 0) := by
    by_cases h1 : l = j <;> by_cases h2 : k = i <;> by_cases h3 : l = i <;>
      by_cases h4 : k = j <;> simp_all [ite_and, hij.not_gt]
  simp only [hk, Finset.sum_add_distrib, Finset.sum_ite_irrel, Finset.sum_const_zero,
    Finset.sum_ite_eq', Finset.mem_univ, ite_true]
  -- the edges at `j` other than `ij` whose far end misses `i`, and likewise at `i`
  have hj (w : V) : (if w < j ∧ G.Adj w j ∧ ¬G.Adj i w then (1 : ℤ) else 0) +
      (if j < w ∧ G.Adj j w ∧ ¬G.Adj i w then 1 else 0) =
      (if G.Adj j w then 1 else 0) - (if G.Adj i w ∧ G.Adj j w then 1 else 0) := by
    by_cases hb : G.Adj j w
    · rcases lt_or_gt_of_ne (G.ne_of_adj hb).symm with hw | hw <;>
        by_cases ha : G.Adj i w <;> simp [hw, hw.not_gt, ha, hb, hb.symm]
    · simp [hb, G.adj_comm w j]
  have hi (w : V) : (if i < w ∧ G.Adj i w ∧ ¬G.Adj j w then (1 : ℤ) else 0) +
      (if w < i ∧ G.Adj w i ∧ ¬G.Adj w j then 1 else 0) =
      (if G.Adj i w then 1 else 0) - (if G.Adj i w ∧ G.Adj j w then 1 else 0) := by
    by_cases ha : G.Adj i w
    · rcases lt_or_gt_of_ne (G.ne_of_adj ha) with hw | hw <;>
        by_cases hb : G.Adj j w <;> simp [hw, hw.not_gt, ha, hb, ha.symm, G.adj_comm w j]
    · simp [ha, G.adj_comm w i]
  have hsum := Finset.sum_congr rfl fun w (_ : w ∈ univ) ↦ congrArg₂ (· + ·) (hj w) (hi w)
  simp only [Finset.sum_add_distrib, Finset.sum_sub_distrib] at hsum
  rw [forman, SimpleGraph.degree_eq_sum_if_adj (G := G) (R := ℤ) i,
    SimpleGraph.degree_eq_sum_if_adj (G := G) (R := ℤ) j, card_common]
  simp only [G.irrefl, hij.ne, hij.ne', not_false_eq_true, and_true, false_and, ↓reduceIte]
  linarith

end Weitzenbock

end Palace.Bridges
