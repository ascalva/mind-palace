module

public import Palace.Balance.Defs

/-!
# Signed balance: LAP-5 and LAP-6, the statements

Statements of the ledger's balance laws (dn-mathematical-foundations §2.2, seed table II),
mirroring `core/kernel/complex/balance.py`. A signed graph is balanced when its vertices split into
two camps, every positive edge inside a camp and every negative edge across.

These are the laws of `Palace/Balance.lean` as the ledger cites them, each with its proof
left as `sorry`. `lake comparator` checks that the `Palace` library proves each one
exactly as stated here, from the standard axioms alone.
-/

@[expose] public section

open Matrix Finset

namespace Palace

variable {V R : Type*} [Fintype V] [DecidableEq V]

/-! ### LAP-6: a triangle is frustrated iff it carries an odd number of negative edges -/

/-- **LAP-6** A triangle with nonzero weights is frustrated (not balanced) iff the product of its
signs is negative, which is the test `frustrated_triangles` runs. -/
theorem not_balanced_triangle_iff [Field R] [LinearOrder R] [IsStrictOrderedRing R] {a b c : R}
    (ha : a ≠ 0) (hb : b ≠ 0) (hc : c ≠ 0) : ¬ Balanced (triangle a b c) ↔ a * b * c < 0 :=
  sorry

/-- **LAP-6** In the ledger's words: frustrated iff the count of negative edges is odd. -/
theorem not_balanced_triangle_iff_odd [Field R] [LinearOrder R] [IsStrictOrderedRing R]
    {a b c : R} (ha : a ≠ 0) (hb : b ≠ 0) (hc : c ≠ 0) :
    ¬ Balanced (triangle a b c) ↔
      Odd ((if a < 0 then 1 else 0) + (if b < 0 then 1 else 0) + (if c < 0 then 1 else 0) : ℕ) :=
  sorry

/-! ### LAP-5: `λ_min(L̄) = 0` iff balanced, on a connected support -/

/-- **LAP-5** Hou and Kunegis, on a connected support: `L̄` has a nonzero vector of zero energy (so
its smallest eigenvalue is `0`, `L̄` being positive semidefinite) iff the signed graph is
balanced. -/
theorem zero_energy_iff_balanced (A : Matrix V V ℝ) (hA : A.IsSymm) (hc : (support A).Connected) :
    (∃ x ≠ 0, x ⬝ᵥ (signedLap A *ᵥ x) = 0) ↔ Balanced A :=
  sorry

end Palace
