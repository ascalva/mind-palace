module

public import Palace.Balance
public import PalaceTest.Spectral
public meta import Palace.Balance
public meta import PalaceTest.Spectral

/-!
# Attacks on `Palace.Balance`

The Plausible attacks and negative controls for the laws of `Palace/Balance.lean`. They run
when this module builds (`lake test`); the library itself runs no code at build time.
-/

@[expose] public section

open Matrix Finset

namespace Palace

/-! ## Attacks

On `Fin 5` over ℚ. `BalancedB` is decided by trying all 32 camp assignments, and it is the same
predicate as `Balanced` (`balanced_iff_balancedB`). `λ_min(L̄) = 0` is read as `L̄` singular
(`L̄` is positive semidefinite, so a zero-energy vector is a kernel vector), decided by the exact
Gauss–Jordan shadow of the `L⁺` attacks.
-/

namespace Attack

/- Decide `BalancedB` one quantifier at a time; instance search does not find the nesting. -/
instance {n : ℕ} (A : Matrix (Fin n) (Fin n) ℚ) : Decidable (BalancedB A) :=
  have (b : Fin n → Bool) (i : Fin n) :
      Decidable (∀ j, 0 ≤ A i j * camp (b i) * camp (b j)) := inferInstance
  have (b : Fin n → Bool) : Decidable (∀ i j, 0 ≤ A i j * camp (b i) * camp (b j)) :=
    Nat.decidableForallFin _
  Fintype.decidableExistsFintype

/-- `L̄` is singular. -/
def singular (A : Matrix (Fin 5) (Fin 5) ℚ) : Bool := (invR (rows (signedLap A))).isNone

/-- The support is connected. -/
def connected (A : Matrix (Fin 5) (Fin 5) ℚ) : Bool := ((reach A)[0]!).all id

/-- A balanced signed graph by construction: nonnegative weights, signed by camps. -/
def balancedOf (es : List (Fin 5 × Fin 5 × ℕ)) (bs : List Bool) : Matrix (Fin 5) (Fin 5) ℚ :=
  fun i j ↦ ofEdges (nonneg es) i j * camp (bs.getD i true) * camp (bs.getD j true)

/- LAP-6: a triangle with nonzero weights is balanced iff the product of its signs is positive
(stated positively; Plausible cannot test a negation inside an `↔`). -/
#eval survives (∀ a b c : ℤ, a ≠ 0 → b ≠ 0 → c ≠ 0 →
  (BalancedB (triangle (a : ℚ) b c) ↔ 0 < a * b * c)) 51

/- LAP-6 control: a balanced triangle has no negative edge (two negative edges are balanced). -/
#eval refuted (∀ a b c : ℤ, a ≠ 0 → b ≠ 0 → c ≠ 0 →
  BalancedB (triangle (a : ℚ) b c) → 0 < min a (min b c)) 52

/- LAP-5 on a connected support: `L̄` singular iff balanced. -/
#eval survives (∀ es : List (Fin 5 × Fin 5 × ℤ),
  connected (ofEdges es) = true → (singular (ofEdges es) = true ↔ BalancedB (ofEdges es))) 53

/- LAP-5 on graphs balanced by construction: connected ones are singular. -/
#eval survives (∀ es : List (Fin 5 × Fin 5 × ℕ), ∀ bs : List Bool,
  connected (balancedOf es bs) = true → singular (balancedOf es bs) = true) 54

/- LAP-5 control, the global reading without connectivity (an isolated vertex or a balanced
component makes `L̄` singular while frustration sits elsewhere). -/
#eval refuted (∀ es : List (Fin 5 × Fin 5 × ℤ),
  (singular (ofEdges es) = true ↔ BalancedB (ofEdges es))) 55

end Attack

end Palace
