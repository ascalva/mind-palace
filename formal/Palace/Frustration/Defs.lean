module

public import Palace.Laplacian.Defs

/-!
# The frustration lift: the definitions

A contradiction among the relation edges lifts the zero mode of the signed Laplacian `L̄` (LAP-5,
`zero_energy_iff_balanced`). How far: the limits program's L4
(`docs/brainstorms/limits-of-the-algebra.md`) bounds the lift by the frustrated weight of the best
switching, and `Palace/Frustration.lean` proves the identity behind the bound. The one definition
is that weight.
-/

@[expose] public section

open Matrix Finset

namespace Palace.Frustration

variable {V : Type*} [Fintype V]

/-- The frustrated weight of a signing `s ∈ {±1}^V`, over ordered pairs: `(|Aᵢⱼ| − Aᵢⱼ sᵢ sⱼ) / 2`
is `|Aᵢⱼ|` where the edge's sign disagrees with `sᵢ sⱼ` and `0` where it agrees — twice the
weight of the frustrated edges counted once. The frustration index is its least value over the
signings. -/
noncomputable def frustrated (A : Matrix V V ℝ) (s : V → ℝ) : ℝ :=
  ∑ i, ∑ j, (|A i j| - A i j * s i * s j) / 2

end Palace.Frustration
