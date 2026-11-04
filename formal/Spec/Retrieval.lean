module

public import Palace.Retrieval.Defs
public import Mathlib.LinearAlgebra.Matrix.PosDef
public import Mathlib.Analysis.SpecialFunctions.Log.Basic
public import Mathlib.Analysis.SpecialFunctions.Sqrt
public import Mathlib.Combinatorics.SimpleGraph.Connectivity.Connected

/-!
# The retrieval curve: RSP-1 to RSP-4, the statements

`core/query.py`'s `free_energy_distances` computes the β-curve of
`docs/design-notes/temporal-retrieval-algebra.md` §2.1 (Theorem A1):

* RSP-1: the walk sum is well posed under the γ-ceiling `z < 1`; `Z ≥ 0`, `z_ii ≥ 1`, and `z_ij > 0`
  exactly when `j` is reachable from `i`.
* RSP-2: `Z = G_β D` for the symmetric kernel `G_β = (D − z·w∘w^β)⁻¹`, positive definite for every
  β.
* RSP-3: `e^{−β d_ij} = G_ij / √(G_ii G_jj)`, so `e^{−β d}` is positive definite on a connected
  support for every β, and `K_struct = e^{−d}` at the default `β = 1`.
* RSP-4: the free energy is a quasi-metric and the code's symmetrized distance a pseudometric.

These are the theorems of `Palace/Retrieval.lean` as the ledger cites them, each with its proof
left as `sorry`. `lake comparator` checks that the `Palace` library proves each one exactly as
stated here, from the standard axioms alone.
-/

@[expose] public section

open Matrix

namespace Palace.Retrieval

variable {V : Type*} [Fintype V] [DecidableEq V]

section Curve

variable {w : Matrix V V ℝ} {β z : ℝ}
variable (hw0 : ∀ i j, 0 ≤ w i j) (hw1 : ∀ i j, w i j ≤ 1) (hβ : 0 ≤ β) (hz0 : 0 ≤ z)
  (hz1 : z < 1)
include hw0 hw1 hβ hz0 hz1

/-- **RSP-1** The walk sum is well posed: `I − W_β` is invertible, the γ-ceiling `z < 1` bounding
every row of `W_β` by `z`. -/
theorem det_one_sub_killedWalk_ne_zero : (1 - killedWalk w β z).det ≠ 0 := sorry

/-- **RSP-1** `Z = (I − W_β)⁻¹` is nonnegative. -/
theorem fundamental_nonneg (i j : V) : 0 ≤ fundamental w β z i j := sorry

/-- **RSP-1** `z_ii ≥ 1`. -/
theorem one_le_fundamental_self (i : V) : 1 ≤ fundamental w β z i i := sorry

/-- **RSP-1** `z_ij > 0` when `j` is reachable from `i` along edges of positive weight. -/
theorem fundamental_pos_of_reachable (hw : w.IsSymm) (hz : 0 < z) {i j : V}
    (h : (support w).Reachable i j) : 0 < fundamental w β z i j := sorry

/-- **RSP-1** `z_ij = 0` when `j` is not reachable from `i`. -/
theorem fundamental_eq_zero_of_not_reachable {i j : V} (h : ¬(support w).Reachable i j) :
    fundamental w β z i j = 0 := sorry

end Curve

section Kernel

variable {w : Matrix V V ℝ} {β z : ℝ}

/-- **RSP-2** Theorem A1's kernel is positive definite for every `β ≥ 0`. -/
theorem posDef_rspKernel (hw : w.IsSymm) (hw0 : ∀ i j, 0 ≤ w i j) (hw1 : ∀ i j, w i j ≤ 1)
    (hd : ∀ i, 0 < degree w i) (hβ : 0 ≤ β) (hz0 : 0 ≤ z) (hz1 : z < 1) :
    (rspKernel w β z).PosDef := sorry

/-- **RSP-2** `Z = G_β D`. -/
theorem fundamental_eq_rspKernel_mul (hd : ∀ i, 0 < degree w i) :
    fundamental w β z = rspKernel w β z * diagonal (degree w) := sorry

end Kernel

section Distance

variable {w : Matrix V V ℝ} {β z : ℝ}

/-- **RSP-3** `e^{−β d_ij} = G_ij / √(G_ii G_jj)` on a pair with `z_ij > 0`. -/
theorem exp_neg_mul_feDist (hw : w.IsSymm) (hw0 : ∀ i j, 0 ≤ w i j) (hw1 : ∀ i j, w i j ≤ 1)
    (hd : ∀ i, 0 < degree w i) (hβ : 0 < β) (hz0 : 0 ≤ z) (hz1 : z < 1) {i j : V}
    (hij : 0 < fundamental w β z i j) :
    Real.exp (-(β * feDist w β z i j)) =
      rspKernel w β z i j / Real.sqrt (rspKernel w β z i i * rspKernel w β z j j) := sorry

/-- **RSP-3** On a connected support `e^{−β d}` is positive definite for every `β > 0`. -/
theorem posDef_exp_neg_mul_feDist (hw : w.IsSymm) (hw0 : ∀ i j, 0 ≤ w i j)
    (hw1 : ∀ i j, w i j ≤ 1) (hd : ∀ i, 0 < degree w i) (hβ : 0 < β) (hz : 0 < z) (hz1 : z < 1)
    (hc : (support w).Connected) :
    (of fun i j ↦ Real.exp (-(β * feDist w β z i j))).PosDef := sorry

/-- **RSP-3** At the code's default `β = 1`, `K_struct = e^{−d}` is positive definite on a
connected support. -/
theorem posDef_kStruct (hw : w.IsSymm) (hw0 : ∀ i j, 0 ≤ w i j) (hw1 : ∀ i j, w i j ≤ 1)
    (hd : ∀ i, 0 < degree w i) (hz : 0 < z) (hz1 : z < 1) (hc : (support w).Connected) :
    (of fun i j ↦ Real.exp (-feDist w 1 z i j)).PosDef := sorry

/-- **RSP-4** `φ_ii = 0`. -/
theorem freeEnergy_self (hw0 : ∀ i j, 0 ≤ w i j) (hw1 : ∀ i j, w i j ≤ 1) (hβ : 0 ≤ β)
    (hz0 : 0 ≤ z) (hz1 : z < 1) (i : V) : freeEnergy w β z i i = 0 := sorry

/-- **RSP-4** `φ_ij ≥ 0`. -/
theorem freeEnergy_nonneg (hw0 : ∀ i j, 0 ≤ w i j) (hw1 : ∀ i j, w i j ≤ 1) (hβ : 0 < β)
    (hz0 : 0 ≤ z) (hz1 : z < 1) (i j : V) : 0 ≤ freeEnergy w β z i j := sorry

/-- **RSP-4** The triangle inequality of the free energy. -/
theorem freeEnergy_triangle (hw0 : ∀ i j, 0 ≤ w i j) (hw1 : ∀ i j, w i j ≤ 1) (hβ : 0 < β)
    (hz0 : 0 ≤ z) (hz1 : z < 1) {i j k : V} (hij : 0 < fundamental w β z i j)
    (hjk : 0 < fundamental w β z j k) :
    freeEnergy w β z i k ≤ freeEnergy w β z i j + freeEnergy w β z j k := sorry

/-- **RSP-4** The distance vanishes on the diagonal and is nonnegative. -/
theorem feDist_self_and_nonneg (hw0 : ∀ i j, 0 ≤ w i j) (hw1 : ∀ i j, w i j ≤ 1) (hβ : 0 < β)
    (hz0 : 0 ≤ z) (hz1 : z < 1) (i j : V) :
    feDist w β z i i = 0 ∧ 0 ≤ feDist w β z i j := sorry

/-- **RSP-4** The code's symmetrized distance satisfies the triangle inequality on a connected
support. -/
theorem feDist_triangle (hw : w.IsSymm) (hw0 : ∀ i j, 0 ≤ w i j) (hw1 : ∀ i j, w i j ≤ 1)
    (hβ : 0 < β) (hz : 0 < z) (hz1 : z < 1) (hc : (support w).Connected) (i j k : V) :
    feDist w β z i k ≤ feDist w β z i j + feDist w β z j k := sorry

end Distance

end Palace.Retrieval
