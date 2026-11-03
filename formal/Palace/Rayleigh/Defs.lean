module

public import Mathlib.Tactic.FinCases
public import Palace.Balance.Defs

/-!
# Rayleigh's monotonicity law: CND-2, the definitions

The definitions the laws of `Palace/Rayleigh.lean` are stated over. With `Spec/Rayleigh.lean`
they are what a reader checks against `docs/LAWS.md`: `lake comparator` ensures the library
proves exactly the statements there, so no other file can change what is proved.
-/

@[expose] public section

open Matrix Finset

namespace Palace

variable {V : Type*} [Fintype V] [DecidableEq V]

/-! ### Rayleigh's law for effective resistance -/

open Classical in
/-- The code's effective resistance (`_r_eff_matrix`): `R_eff` within a component, `∞` across. -/
noncomputable def resistance (A : Matrix V V ℝ) (hA : A.IsSymm) (i j : V) : WithTop ℝ :=
  if (support A).Reachable i j then ((rEff (lapPinv A hA) i j : ℝ) : WithTop ℝ) else ⊤

open Classical in
/-- The code's effective conductance (`_pair_conductance`): `1/R_eff` within a component and `0`
across; at a vertex itself `R_eff = 0`, and Lean's `0⁻¹ = 0` agrees with the code's `r > ε`
guard. -/
noncomputable def effConductance (A : Matrix V V ℝ) (hA : A.IsSymm) (i j : V) : ℝ :=
  if (support A).Reachable i j then (rEff (lapPinv A hA) i j)⁻¹ else 0

end Palace
