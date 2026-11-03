module

public import Mathlib.Algebra.Order.Field.Power
public import Mathlib.Algebra.Order.Round
public import Mathlib.Algebra.Order.Floor.Defs
public import Mathlib.Algebra.Ring.CharZero
public import Mathlib.Order.Lattice
public import Mathlib.Data.Int.Log
public import Mathlib.Data.Rat.Floor
public import Mathlib.Tactic.FieldSimp
public import Mathlib.Tactic.GCongr
public import Mathlib.Tactic.IntervalCases
public import Mathlib.Tactic.Linarith
public import Mathlib.Tactic.Positivity
public import Mathlib.Tactic.Ring

/-!
# The binary64 rounding model: L3's substrate, the definitions

The definitions the laws of `Palace/Binary64.lean` are stated over. With `Spec/Binary64.lean`
they are what a reader checks against `docs/LAWS.md`: `lake comparator` ensures the library
proves exactly the statements there, so no other file can change what is proved.
-/

@[expose] public section

namespace Palace.Binary64

variable {K : Type*} [Field K] [LinearOrder K] [IsStrictOrderedRing K] [FloorRing K]

section Rne

/-- The nearest integer to `y`, ties to even: IEEE 754's default rounding of a significand. -/
def rne (y : K) : ℤ :=
  if Int.fract y < 1 / 2 then ⌊y⌋
  else if 1 / 2 < Int.fract y then ⌊y⌋ + 1
  else if ⌊y⌋ % 2 = 0 then ⌊y⌋ else ⌊y⌋ + 1

end Rne

section Rn

/-- The exponent of `x`'s ulp (Flocq's FLT format with binary64's parameters): `⌊log₂ |x|⌋ − 52`,
which leaves 53 significand bits, in the normal range, and `−1074`, the least subnormal's exponent,
below it. -/
def cexp (x : K) : ℤ := max (Int.log 2 |x| - 52) (-1074)

/-- Round to nearest, ties to even, onto the binary64 grid: IEEE 754's default rounding, without
overflow. -/
def rn (x : K) : K := rne (x / 2 ^ cexp x) * 2 ^ cexp x

/-- The unit roundoff `u = 2⁻⁵³`: half the gap between `1` and the next binary64 number. -/
abbrev u : K := 2 ^ (-53 : ℤ)

/-- `x` is a binary64 number, the overflow bound aside: `m · 2^e` with `|m| < 2^53` and
`e ≥ −1074`. -/
def IsFloat (x : K) : Prop := ∃ m e : ℤ, |m| < 2 ^ 53 ∧ -1074 ≤ e ∧ x = m * 2 ^ e

end Rn

end Palace.Binary64
