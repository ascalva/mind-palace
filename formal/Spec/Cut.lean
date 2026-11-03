module

public import Palace.Cut.Defs

/-!
# Conductance: CUT-1, the statements

`Φ(S) = w(∂S) / min(vol S, vol S̄)` with the conventions of `core/complex/cut.py`, `conductance`
(dn-mathematical-foundations §2.2, seed table III): `0` when `S` is empty or everything, and `0`
when either side has zero volume.

These are the laws of `Palace/Cut.lean` as the ledger cites them, each with its proof
left as `sorry`. `lake comparator` checks that the `Palace` library proves each one
exactly as stated here, from the standard axioms alone.
-/

@[expose] public section

open Matrix Finset

namespace Palace

variable {V R : Type*} [Fintype V] [DecidableEq V]

section Bounds

variable [Field R] [LinearOrder R] [IsStrictOrderedRing R]

/-- **CUT-1** `Φ(S) ∈ [0, 1]` for symmetric `A` with nonnegative entries, degenerate `S`
included. -/
theorem conductance_mem_Icc (A : Matrix V V R) (hA : A.IsSymm) (hw : ∀ i j, 0 ≤ A i j)
    (S : Finset V) : conductance A S ∈ Set.Icc 0 1 :=
  sorry

/-- **CUT-1** `Φ(S) = 0` iff no weight crosses from `S` to the rest (the docstring's "0 ⇔ S is
disconnected from the rest"), under the code's conventions. -/
theorem conductance_eq_zero_iff (A : Matrix V V R) (hA : A.IsSymm) (hw : ∀ i j, 0 ≤ A i j)
    (S : Finset V) : conductance A S = 0 ↔ boundary A S = 0 :=
  sorry

end Bounds

end Palace
