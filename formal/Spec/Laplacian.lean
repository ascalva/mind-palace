module

public import Palace.Laplacian.Defs

/-!
# The Laplacian family: LAP-1, LAP-2, LAP-3, the statements

Statements of the ledger's first Laplacian laws (dn-mathematical-foundations §2.2, seed table),
mirroring `core/kernel/complex/laplacian.py`. `A` is any square matrix over a ring; the Python
builds it from a sparse adjacency and allows self-loops, so nothing here assumes a zero diagonal.

These are the laws of `Palace/Laplacian.lean` as the ledger cites them, each with its proof
left as `sorry`. `lake comparator` checks that the `Palace` library proves each one
exactly as stated here, from the standard axioms alone.
-/

@[expose] public section

open Matrix Finset

namespace Palace

variable {V R : Type*} [Fintype V] [DecidableEq V]

/-- **LAP-1** `L·1 = 0`, for every `A`: no symmetry, sign or weight condition is needed. -/
theorem lap_mulVec_one [Ring R] (A : Matrix V V R) : lap A *ᵥ 1 = 0 :=
  sorry

/-- **LAP-2** `xᵀLx ≥ 0` for symmetric `A` with nonnegative entries. -/
theorem dotProduct_lap_nonneg [CommRing R] [LinearOrder R] [IsStrictOrderedRing R]
    (A : Matrix V V R) (hA : A.IsSymm) (hw : ∀ i j, 0 ≤ A i j) (x : V → R) :
    0 ≤ x ⬝ᵥ (lap A *ᵥ x) :=
  sorry

/-- **LAP-2** as a matrix statement: `L` is positive semidefinite. -/
theorem posSemidef_lap [Field R] [LinearOrder R] [IsStrictOrderedRing R] [StarRing R]
    [TrivialStar R] (A : Matrix V V R) (hA : A.IsSymm) (hw : ∀ i j, 0 ≤ A i j) :
    (lap A).PosSemidef :=
  sorry

/-- **LAP-2** for the signed Laplacian: `xᵀL̄x ≥ 0` for every symmetric `A`, of any sign. -/
theorem dotProduct_signedLap_nonneg [CommRing R] [LinearOrder R] [IsStrictOrderedRing R]
    (A : Matrix V V R) (hA : A.IsSymm) (x : V → R) :
    0 ≤ x ⬝ᵥ (signedLap A *ᵥ x) :=
  sorry

/-- **LAP-2** on the binarized support: Mathlib's lemma, in one line. -/
theorem posSemidef_lap_adjMatrix (G : SimpleGraph V) [DecidableRel G.Adj] :
    (lap (G.adjMatrix ℝ)).PosSemidef :=
  sorry

/-- **LAP-3** on the binarized support: `dim ker L` is the number of connected components
(Mathlib's lemma, in one line). -/
theorem card_components_eq_nullity_adjMatrix (G : SimpleGraph V) [DecidableRel G.Adj] :
    Fintype.card G.ConnectedComponent =
      Module.finrank ℝ (LinearMap.ker (lap (G.adjMatrix ℝ)).toLin') :=
  sorry

/-- **LAP-3** weighted: for symmetric `A` with nonnegative entries, `dim ker L` is the number of
connected components of the support graph. -/
theorem card_components_eq_nullity (A : Matrix V V ℝ) (hA : A.IsSymm) (hw : ∀ i j, 0 ≤ A i j)
    [DecidableRel (support A).Adj] :
    Fintype.card (support A).ConnectedComponent =
      Module.finrank ℝ (LinearMap.ker (lap A).toLin') :=
  sorry

end Palace
