module

public import Mathlib.Combinatorics.SimpleGraph.LapMatrix

/-!
# The Laplacian family: LAP-1, LAP-2, LAP-3, the definitions

The definitions the laws of `Palace/Laplacian.lean` are stated over. With `Spec/Laplacian.lean`
they are what a reader checks against `docs/LAWS.md`: `lake comparator` ensures the library
proves exactly the statements there, so no other file can change what is proved.
-/

@[expose] public section

open Matrix Finset

namespace Palace

variable {V R : Type*} [Fintype V] [DecidableEq V]

/-- The weighted degree: the row sums of `A` (`laplacian.py`, `_degree`). -/
def degree [AddCommMonoid R] (A : Matrix V V R) (i : V) : R := ∑ j, A i j

/-- The combinatorial Laplacian `L = D − A` (`laplacian.py`, `laplacian`). -/
def lap [Ring R] (A : Matrix V V R) : Matrix V V R := diagonal (degree A) - A

/-- The signed Laplacian `L̄ = D̄ − A`, `D̄ᵢᵢ = Σⱼ |Aᵢⱼ|` (`laplacian.py`, `signed_laplacian`). -/
def signedLap [Ring R] [LinearOrder R] (A : Matrix V V R) : Matrix V V R :=
  diagonal (fun i ↦ ∑ j, |A i j|) - A

/-- The support graph of a weight matrix: `i ~ j` iff `i ≠ j` and `Aᵢⱼ ≠ 0` or `Aⱼᵢ ≠ 0`. A
self-loop is no edge: its weight enters `D` and `A` alike and cancels in `L`. -/
def support [Zero R] (A : Matrix V V R) : SimpleGraph V :=
  SimpleGraph.fromRel fun i j ↦ A i j ≠ 0

end Palace
