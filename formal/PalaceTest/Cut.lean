module

public import Palace.Cut
public import Mathlib.Testing.Plausible.Sampleable
public import PalaceTest.Laplacian
public meta import Palace.Cut
public meta import Mathlib.Testing.Plausible.Sampleable
public meta import PalaceTest.Laplacian

/-!
# Attacks on `Palace.Cut`

The Plausible attacks and negative controls for the laws of `Palace/Cut.lean`. They run
when this module builds (`lake test`); the library itself runs no code at build time.
-/

@[expose] public section

open Matrix Finset

namespace Palace

/-! ## Attacks

On `Fin 5` over ℚ, with `S` drawn as a list of vertices, so the empty set and the whole vertex set
both occur and the conventions are exercised. -/

namespace Attack

/- CUT-1: `Φ(S) ∈ [0, 1]` on symmetric nonnegative weights. -/
#eval survives (∀ es : List (Fin 5 × Fin 5 × ℕ), ∀ ss : List (Fin 5),
  0 ≤ conductance (ofEdges (nonneg es)) ss.toFinset ∧
    conductance (ofEdges (nonneg es)) ss.toFinset ≤ 1) 61

/- CUT-1: `Φ(S) = 0` iff no weight crosses. -/
#eval survives (∀ es : List (Fin 5 × Fin 5 × ℕ), ∀ ss : List (Fin 5),
  (conductance (ofEdges (nonneg es)) ss.toFinset = 0 ↔
    boundary (ofEdges (nonneg es)) ss.toFinset = 0)) 62

/- CUT-1 control: asymmetric weights, where `w(∂S)` can exceed `vol S̄`. -/
#eval refuted (∀ es : List (Fin 5 × Fin 5 × ℕ), ∀ ss : List (Fin 5),
  conductance (ofArcs (nonneg es)) ss.toFinset ≤ 1) 63

end Attack

end Palace
