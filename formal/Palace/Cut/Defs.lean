module

public import Palace.Laplacian.Defs

/-!
# Conductance: CUT-1, the definitions

The definitions the laws of `Palace/Cut.lean` are stated over. With `Spec/Cut.lean`
they are what a reader checks against `docs/LAWS.md`: `lake comparator` ensures the library
proves exactly the statements there, so no other file can change what is proved.
-/

@[expose] public section

open Matrix Finset

namespace Palace

variable {V R : Type*} [Fintype V] [DecidableEq V]

/-- `vol S`: the weighted degree summed over `S` (`A[members].sum()`). -/
def vol [AddCommMonoid R] (A : Matrix V V R) (S : Finset V) : R := ∑ i ∈ S, degree A i

/-- `w(∂S)`: the weight from `S` to the rest (`A[members][:, ~members].sum()`). -/
def boundary [AddCommMonoid R] (A : Matrix V V R) (S : Finset V) : R := ∑ i ∈ S, ∑ j ∈ Sᶜ, A i j

/-- `conductance`, with the code's conventions for a degenerate `S`. -/
def conductance [Field R] [LinearOrder R] (A : Matrix V V R) (S : Finset V) : R :=
  if S = ∅ ∨ S = univ then 0
  else if vol A S = 0 ∨ vol A Sᶜ = 0 then 0
  else boundary A S / min (vol A S) (vol A Sᶜ)

end Palace
