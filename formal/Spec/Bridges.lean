module

public import Palace.Bridges.Defs

/-!
# Bridges between the families: BRG-1 to BRG-6, the statements

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

These are the bridges of `Palace/Bridges.lean` as the ledger cites them, each with its proof
left as `sorry`. `lake comparator` checks that the `Palace` library proves each one exactly as
stated here, from the standard axioms alone.
-/

@[expose] public section

open Relation Matrix

namespace Palace.Bridges

/-! ## BRG-1 and BRG-2: the Laplacian is the Hodge complex's vertex end -/

section Complex

open Palace.Hodge Finset

variable {V : Type*} [LinearOrder V] [Fintype V] (G : SimpleGraph V) [DecidableRel G.Adj]

/-- **BRG-1** The vertex end of the Hodge complex is the graph Laplacian: `∂₁ ∂₁ᵀ = D − A`,
Mathlib's `lapMatrix`, over any commutative ring. -/
theorem d1_mul_transpose (R : Type*) [CommRing R] :
    d1 G R * (d1 G R)ᵀ = G.lapMatrix R :=
  sorry

/-- **BRG-1** So it is `lap` of the 0/1 adjacency, the Laplacian of LAP-1 to LAP-3. -/
theorem d1_mul_transpose_eq_lap (R : Type*) [CommRing R] :
    d1 G R * (d1 G R)ᵀ = lap (G.adjMatrix R) :=
  sorry

/-- **BRG-2** The components are the cokernel of `∂₁`: their number and `∂₁`'s rank make up the
vertices (LAP-3, read on `∂₁ ∂₁ᵀ` by BRG-1). -/
theorem card_components_add_rank :
    Fintype.card G.ConnectedComponent + (d1 G ℝ).rank = Fintype.card V :=
  sorry

/-- **BRG-2** Euler and Poincaré on the flag complex: `|V| − |E| + |T| = b₀ − b₁ + b₂`, with `b₀`
the components (LAP-3), `b₁` the harmonic flows (LAP-10) and `b₂` the 2-cycles, `ker ∂₂`. -/
theorem euler_poincare :
    (Fintype.card V : ℤ) - Fintype.card (Edge G) + Fintype.card (Tri G) =
      Fintype.card G.ConnectedComponent -
        Module.finrank ℝ (LinearMap.ker (lap1 (d1 G ℝ) (d2 G ℝ)).mulVecLin) +
        Module.finrank ℝ (LinearMap.ker (d2 G ℝ).mulVecLin) :=
  sorry

end Complex

/-! ## BRG-3: Thomson's principle on flows -/

section Thomson

variable {V E : Type*} [Fintype V] [DecidableEq V] [Fintype E]

/-- **BRG-3** Thomson's principle, on flows. For an incidence `B` and a demand `v` that `M M⁺`
fixes, `M = B Bᵀ`, every flow meeting the demand, `B f = v`, has energy at least `vᵀ M⁺ v`: the
value whose potentials `thomson` bounds from the other side, Rayleigh's law compares, and CND-1
reads as the effective resistance. -/
theorem energy_ge (B : Matrix V E ℝ) (hM : (B * Bᵀ).IsHermitian) {v : V → ℝ}
    (hv : (B * Bᵀ) *ᵥ (pinv (B * Bᵀ) hM *ᵥ v) = v) {f : E → ℝ} (hf : B *ᵥ f = v) :
    v ⬝ᵥ (pinv (B * Bᵀ) hM *ᵥ v) ≤ f ⬝ᵥ f :=
  sorry

/-- **BRG-3** The gradient flow `Bᵀ M⁺ v`, the gradient of the potential `M⁺ v`, meets the demand
with exactly that energy. -/
theorem gradient_flow (B : Matrix V E ℝ) (hM : (B * Bᵀ).IsHermitian) {v : V → ℝ}
    (hv : (B * Bᵀ) *ᵥ (pinv (B * Bᵀ) hM *ᵥ v) = v) :
    B *ᵥ (Bᵀ *ᵥ (pinv (B * Bᵀ) hM *ᵥ v)) = v ∧
      (Bᵀ *ᵥ (pinv (B * Bᵀ) hM *ᵥ v)) ⬝ᵥ (Bᵀ *ᵥ (pinv (B * Bᵀ) hM *ᵥ v)) =
        v ⬝ᵥ (pinv (B * Bᵀ) hM *ᵥ v) :=
  sorry

/-- **BRG-3** And it is the only flow meeting the demand with that energy: the energy minimizer is
the gradient part, the projection of `Palace/Hodge.lean`'s split. -/
theorem energy_eq_iff (B : Matrix V E ℝ) (hM : (B * Bᵀ).IsHermitian) {v : V → ℝ}
    (hv : (B * Bᵀ) *ᵥ (pinv (B * Bᵀ) hM *ᵥ v) = v) {f : E → ℝ} (hf : B *ᵥ f = v) :
    f ⬝ᵥ f = v ⬝ᵥ (pinv (B * Bᵀ) hM *ᵥ v) ↔ f = Bᵀ *ᵥ (pinv (B * Bᵀ) hM *ᵥ v) :=
  sorry

end Thomson

/-! ### Thomson's principle on a graph -/

section ThomsonGraph

open Palace.Hodge

variable {V : Type*} [LinearOrder V] [Fintype V] (G : SimpleGraph V) [DecidableRel G.Adj]

/-- **BRG-3** On a graph, by BRG-1: the effective resistance between `i` and `j` (CND-1) is at
most the energy of every unit flow from `i` to `j` along the edges, when the demand can be met,
and the gradient flow attains it (`gradient_flow`). -/
theorem rEff_le_energy {i j : V}
    (hv : lap (G.adjMatrix ℝ) *ᵥ (lapPinv (G.adjMatrix ℝ) G.isSymm_adjMatrix *ᵥ
      (Pi.single j 1 - Pi.single i 1)) = Pi.single j 1 - Pi.single i 1)
    {f : Edge G → ℝ} (hf : d1 G ℝ *ᵥ f = Pi.single j 1 - Pi.single i 1) :
    rEff (lapPinv (G.adjMatrix ℝ) G.isSymm_adjMatrix) i j ≤ f ⬝ᵥ f :=
  sorry

end ThomsonGraph

/-! ## BRG-4: cuts and refinement-closed strata are lower sets -/

section LowerSets

/-- **BRG-4** A cut of the clock is a lower set of `≼`, reachability along the generators, so the
cuts carry the lattice of Mathlib's `LowerSet`s. -/
theorem isCut_iff_isLowerSet {E : Type*} (g : E → E → Prop) (S : Set E) :
    Clock.IsCut g S ↔ @IsLowerSet E (reach g).toLE S :=
  sorry

/-- **BRG-4** A set of strata closed under refinement is a cut of the refinement relation: scope's
`Σ` and the clock's cuts are one structure. -/
theorem isDown_iff_isCut (S : Finset CQ.Stratum) :
    CQ.IsDown S ↔ Clock.IsCut Refines (↑S : Set CQ.Stratum) :=
  sorry

/-- **BRG-4** So the refinement-closed sets of strata are lower sets too. -/
theorem isDown_iff_isLowerSet (S : Finset CQ.Stratum) :
    CQ.IsDown S ↔ @IsLowerSet CQ.Stratum (reach Refines).toLE ↑S :=
  sorry

end LowerSets

/-! ## BRG-5: delegation cannot leak through the plane -/

section Delegation

variable {P D A : Type*} [DecidableEq P] [LinearOrder D] [DecidableEq A]

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
          (Plane.run (ops.filter (·.visible (CQ.classesOf CQ.stratumClasses m.sigma))) t) :=
  sorry

end Delegation

/-! ## BRG-6: Forman's curvature is the Weitzenböck term of `L₁` -/

section Weitzenbock

open Palace.Hodge Finset

variable {V : Type*} [LinearOrder V] [Fintype V] {G : SimpleGraph V} [DecidableRel G.Adj]

/-- **BRG-6** Forman's augmented curvature of an edge, `4 − deg i − deg j + 3·|△(i, j)|` (CRV-1),
is the Weitzenböck term of the Hodge Laplacian `L₁` on the flag complex (LAP-8):
`L₁ e e − Σ_{e' ≠ e} |L₁ e e'|`. The diagonal is `2 + |△|`; off it, the down and up adjacencies
cancel exactly between edges that share a triangle, and each other edge at an end counts once. -/
theorem forman_eq_weitzenbock (e : Edge G) :
    forman G e.1.1 e.1.2 = weitzenbock (lap1 (d1 G ℤ) (d2 G ℤ)) e :=
  sorry

end Weitzenbock

end Palace.Bridges
