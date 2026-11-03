module

public import Palace.Rayleigh.Defs

/-!
# Rayleigh's monotonicity law: CND-2, the statements

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

These are the laws of `Palace/Rayleigh.lean` as the ledger cites them, each with its proof
left as `sorry`. `lake comparator` checks that the `Palace` library proves each one
exactly as stated here, from the standard axioms alone.
-/

@[expose] public section

open Matrix Finset

namespace Palace

variable {V : Type*} [Fintype V] [DecidableEq V]

/-! ### Rayleigh's law for effective resistance -/

/-- **CND-2, Rayleigh's monotonicity law**: adding weight never raises the effective resistance
between two vertices of one component. -/
theorem rEff_anti {A A' : Matrix V V ℝ} (hA : A.IsSymm) (hA' : A'.IsSymm) (hw : ∀ i j, 0 ≤ A i j)
    (hle : ∀ i j, A i j ≤ A' i j) {i j : V} (hr : (support A).Reachable i j) :
    rEff (lapPinv A' hA') i j ≤ rEff (lapPinv A hA) i j :=
  sorry

/-- **CND-2** Rayleigh's law with the code's `∞` across components. -/
theorem resistance_anti {A A' : Matrix V V ℝ} (hA : A.IsSymm) (hA' : A'.IsSymm)
    (hw : ∀ i j, 0 ≤ A i j) (hle : ∀ i j, A i j ≤ A' i j) (i j : V) :
    resistance A' hA' i j ≤ resistance A hA i j :=
  sorry

/-- **CND-2** Adding weight never lowers effective conductance. -/
theorem effConductance_mono {A A' : Matrix V V ℝ} (hA : A.IsSymm) (hA' : A'.IsSymm)
    (hw : ∀ i j, 0 ≤ A i j) (hle : ∀ i j, A i j ≤ A' i j) (i j : V) :
    effConductance A hA i j ≤ effConductance A' hA' i j :=
  sorry

/-- **CND-2** A rise in effective conductance needs a weight-increased edge: with no weight
increased, no pair's conductance rises, `reconnection_scan`'s null. -/
theorem exists_increased_of_rise {A A' : Matrix V V ℝ} (hA : A.IsSymm) (hA' : A'.IsSymm)
    (hw' : ∀ i j, 0 ≤ A' i j) {p q : V}
    (h : effConductance A hA p q < effConductance A' hA' p q) : ∃ i j, A i j < A' i j :=
  sorry

end Palace
