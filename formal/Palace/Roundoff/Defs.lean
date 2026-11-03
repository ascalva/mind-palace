module

public import Mathlib.Algebra.BigOperators.Group.List.Basic
public import Palace.Binary64.Defs

/-!
# Two float64 claims of the laws ledger, machine-checked: CND-6 and LAP-1, the definitions

The definitions the laws of `Palace/Roundoff.lean` are stated over. With `Spec/Roundoff.lean`
they are what a reader checks against `docs/LAWS.md`: `lake comparator` ensures the library
proves exactly the statements there, so no other file can change what is proved.
-/

@[expose] public section

namespace Palace.Binary64

variable {K : Type*} [Field K] [LinearOrder K] [IsStrictOrderedRing K] [FloorRing K]

section Reassoc

/-- A summation order: a binary tree over the summands, each node one rounded addition. -/
inductive SumTree (K : Type*) where
  | leaf (x : K)
  | node (l r : SumTree K)

namespace SumTree

/-- The exact sum. -/
def exact : SumTree K → K
  | leaf x => x
  | node l r => l.exact + r.exact

/-- The float64 sum, rounding after each addition. -/
def fl : SumTree K → K
  | leaf x => x
  | node l r => rn (l.fl + r.fl)

/-- The summands, left to right. -/
def leaves : SumTree K → List K
  | leaf x => [x]
  | node l r => l.leaves ++ r.leaves

/-- The number of nonzero summands. -/
def nz (t : SumTree K) : ℕ := (t.leaves.filter (· ≠ 0)).length

/-- `n` more additions of `x` onto the order `s`, one at a time. -/
def chain (s : SumTree K) (x : K) : ℕ → SumTree K
  | 0 => s
  | n + 1 => node (chain s x n) (leaf x)

/-- The witness's summands: `1 + 2u`, an odd point of the grid near `1`, then `3u` and six
`u`. Low: the `3u` first and then the `u`s, one at a time; every tie goes down. -/
def low : SumTree K := chain (node (leaf (1 + 2 * u)) (leaf (3 * u))) u 6

/-- High: the `u`s first, two of the pairs summed before they are added, and the `3u` late;
three ties go up. -/
def high : SumTree K :=
  node (node (node (node (node (leaf (1 + 2 * u)) (leaf u)) (node (leaf u) (leaf u))) (leaf u))
    (leaf (3 * u))) (node (leaf u) (leaf u))

end SumTree

end Reassoc

end Palace.Binary64
