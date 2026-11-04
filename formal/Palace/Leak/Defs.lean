module

public import Palace.Retrieval.Defs

/-!
# The leaky support: the definitions

RSP-5 is one-sided because the support's walk keeps the graph's degrees. When the census that
supplies them is truncated — `k` nearest units per node — a degree is under-counted by the weight
`ℓ i` that leaked past the cut, and the walk over-estimates every transition out of `i` by
`d_i / (d_i − ℓ_i)`. The limits program's L5 (`docs/brainstorms/limits-of-the-algebra.md`) asks
what that costs; `Palace/Leak.lean` answers: a step of killing. The definitions are the leaky walk
and its nearness.
-/

@[expose] public section

open Matrix Finset

namespace Palace.Retrieval

variable {V : Type*} [Fintype V]

/-- The killed walk with the degrees under-counted by a leak `ℓ`: what the support runs when its
census missed weight `ℓ i` at `i` (`free_energy_distances(weights_S, degrees=census)`). -/
noncomputable def leakyWalk (w : Matrix V V ℝ) (ℓ : V → ℝ) (β z : ℝ) : Matrix V V ℝ :=
  of fun i j ↦ z * (w i j / (degree w i - ℓ i)) * w i j ^ β

variable [DecidableEq V]

/-- The nearness on the support `S` under the leaky walk. -/
noncomputable def nearnessLeaky (w : Matrix V V ℝ) (ℓ : V → ℝ) (S : Finset V) (β z : ℝ)
    (i j : V) : ℝ :=
  (1 - restrict (leakyWalk w ℓ β z) S)⁻¹ i j / (1 - restrict (leakyWalk w ℓ β z) S)⁻¹ j j

end Palace.Retrieval
