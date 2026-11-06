module

public import Palace.Binary64.Defs

/-!
# Binary formats of any precision: L3's substrate generalized, the definitions

The definitions the laws of `Palace/Format.lean` are stated over: `Palace/Binary64/Defs.lean`'s
rounding with the format's precision and least exponent as parameters, so binary16 and binary32
are instances beside binary64.
-/

@[expose] public section

namespace Palace.Format

open Palace.Binary64 (rne)

variable {K : Type*} [Field K] [LinearOrder K] [IsStrictOrderedRing K] [FloorRing K]

/-- The exponent of `x`'s ulp in the binary format with `p` significand bits whose least
subnormal is `2 ^ emin` (Flocq's FLT format): `⌊log₂ |x|⌋ − (p − 1)` in the normal range, and
`emin` below it. -/
def cexpf (p : ℕ) (emin : ℤ) (x : K) : ℤ := max (Int.log 2 |x| - ((p : ℤ) - 1)) emin

/-- Round to nearest, ties to even, onto that format, without overflow. -/
def rnf (p : ℕ) (emin : ℤ) (x : K) : K := rne (x / 2 ^ cexpf p emin x) * 2 ^ cexpf p emin x

/-- binary16 (IEEE 754 half precision): 11 significand bits, least subnormal `2⁻²⁴`, largest
finite number `65504`. -/
abbrev rn16 : K → K := rnf 11 (-24)

/-- binary32 (single precision): 24 significand bits, least subnormal `2⁻¹⁴⁹`. -/
abbrev rn32 : K → K := rnf 24 (-149)

end Palace.Format
