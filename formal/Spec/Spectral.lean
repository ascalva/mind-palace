module

public import Palace.Spectral.Defs

/-!
# The normalized Laplacian and the pseudo-inverse: LAP-4, L_sym PSD, L⁺, the statements

`L_sym = I − D^{-1/2} A D^{-1/2}` with the convention `D^{-1/2} := 0` at degree 0
(`core/kernel/complex/laplacian.py`, `laplacian_sym`), and the Moore–Penrose pseudo-inverse `L⁺`
that `core/graph/conductance.py` takes with `np.linalg.pinv` for effective resistance (CND-1).

These are the laws of `Palace/Spectral.lean` as the ledger cites them, each with its proof
left as `sorry`. `lake comparator` checks that the `Palace` library proves each one
exactly as stated here, from the standard axioms alone.
-/

@[expose] public section

open Matrix Finset Unitary

namespace Palace

variable {V R : Type*} [Fintype V] [DecidableEq V]

/-! ### `L_sym` -/

/-- **LAP-4** `Spec(L_sym) ⊆ [0, 2]`, for symmetric `A` with nonnegative entries: every eigenvalue
of the real symmetric `L_sym` has a real eigenvector, and lies in `[0, 2]`. -/
theorem lapSym_eigenvalue_mem_Icc (A : Matrix V V ℝ) (hA : A.IsSymm) (hw : ∀ i j, 0 ≤ A i j)
    {μ : ℝ} {x : V → ℝ} (hx : x ≠ 0) (h : lapSym A *ᵥ x = μ • x) : μ ∈ Set.Icc 0 2 :=
  sorry

/-- **LAP-4** The convention `D^{-1/2} := 0` at degree 0, pointwise: an isolated vertex's row of
`L_sym` is the identity row, so its indicator is an eigenvector of eigenvalue `1`, not `0`. -/
theorem lapSym_mulVec_single_of_degree_eq_zero (A : Matrix V V ℝ) {i : V}
    (hi : degree A i = 0) : lapSym A *ᵥ Pi.single i 1 = Pi.single i 1 :=
  sorry

/-! ### `L⁺` -/

/-- **CND-1** `L⁺` is symmetric, so the effective resistance is symmetric in its two ends. -/
theorem isHermitian_lapPinv (A : Matrix V V ℝ) (hA : A.IsSymm) : (lapPinv A hA).IsHermitian :=
  sorry

/-- **CND-1** `L⁺` is positive semidefinite, for symmetric `A` with nonnegative entries. -/
theorem posSemidef_lapPinv (A : Matrix V V ℝ) (hA : A.IsSymm) (hw : ∀ i j, 0 ≤ A i j) :
    (lapPinv A hA).PosSemidef :=
  sorry

/-- **CND-1** On `L⁺` (symmetric `A`, nonnegative entries) the effective resistance is a value of
its quadratic form, `(eᵢ − eⱼ)ᵀ L⁺ (eᵢ − eⱼ)`, so it is never negative. -/
theorem rEff_lapPinv_nonneg (A : Matrix V V ℝ) (hA : A.IsSymm) (hw : ∀ i j, 0 ≤ A i j)
    (i j : V) : 0 ≤ rEff (lapPinv A hA) i j :=
  sorry

end Palace
