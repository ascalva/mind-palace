module

public import Palace.Spectral.Defs

/-!
# Signed balance: LAP-5 and LAP-6, the definitions

The definitions the laws of `Palace/Balance.lean` are stated over. With `Spec/Balance.lean`
they are what a reader checks against `docs/LAWS.md`: `lake comparator` ensures the library
proves exactly the statements there, so no other file can change what is proved.
-/

@[expose] public section

open Matrix Finset

namespace Palace

variable {V R : Type*} [Fintype V] [DecidableEq V]

/-- Balanced: a camp `sᵢ = ±1` for every vertex with `Aᵢⱼ sᵢ sⱼ ≥ 0` for every pair. -/
def Balanced [Ring R] [LinearOrder R] (A : Matrix V V R) : Prop :=
  ∃ s : V → R, (∀ i, s i = 1 ∨ s i = -1) ∧ ∀ i j, 0 ≤ A i j * s i * s j

/-! ### LAP-6: a triangle is frustrated iff it carries an odd number of negative edges -/

/-- The triangle with weights `a` on `0–1`, `b` on `1–2` and `c` on `0–2`. -/
def triangle [Ring R] (a b c : R) : Matrix (Fin 3) (Fin 3) R := !![0, a, c; a, 0, b; c, b, 0]

end Palace
