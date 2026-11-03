module

public import Mathlib.Tactic.LinearCombination
public import Palace.Roundoff.Defs

/-!
# Lean's `Float` rounds as `rn` does, the definitions

The definitions the laws of `Palace/FloatModel.lean` are stated over. With `Spec/FloatModel.lean`
they are what a reader checks against `docs/LAWS.md`: `lake comparator` ensures the library
proves exactly the statements there, so no other file can change what is proved.
-/

@[expose] public section

open Float.Model (UnpackedFloat Format totalExponent)

open Float.Model.UnpackedFloat (ExtendedMantissa Accuracy Sign)

namespace Palace.Binary64

variable {K : Type*} [Field K] [LinearOrder K] [IsStrictOrderedRing K] [FloorRing K]

section Round

/-- `±1` for a sign. -/
def sgn : Sign → K
  | .positive => 1
  | .negative => -1

/-- The value of an unpacked float: `±m · 2^e`, and `0` for a zero (and, as junk, for `±∞` and
NaN). -/
def value : UnpackedFloat → K
  | .finite s m e _ => sgn s * (m * 2 ^ e)
  | _ => 0

end Round

section LeanFloat

/-- The value of a Lean `Float`: what its bits encode, `0` for `±∞` and NaN. -/
def val (f : Float) : K := value f.toModel.unpack

namespace SumTree

/-- The order with its summands mapped. -/
def map {α β : Type*} (f : α → β) : SumTree α → SumTree β
  | .leaf x => .leaf (f x)
  | .node l r => .node (l.map f) (r.map f)

/-- The order evaluated in Lean's `Float`, one `Float` addition per node. -/
def evalF : SumTree Float → Float
  | .leaf x => x
  | .node l r => l.evalF + r.evalF

end SumTree

end LeanFloat

end Palace.Binary64
