module

public import Palace.Binary64
public import Mathlib.Testing.Plausible.Sampleable
public import PalaceTest.Attack
public meta import Palace.Binary64
public meta import Mathlib.Testing.Plausible.Sampleable
public meta import PalaceTest.Attack

/-!
# Attacks on `Palace.Binary64`

The Plausible attacks and negative controls for the laws of `Palace/Binary64.lean`. They run
when this module builds (`lake test`); the library itself runs no code at build time.
-/

@[expose] public section

namespace Palace.Binary64

/-! ## Attacks: the model against this machine

The model is only as good as its agreement with the arithmetic it models. Lean's `Float` is the
host's binary64 (`a + b` compiles to C's `+`), so these attacks decode the hardware's result bit
for bit into `ℚ` and compare it with `rn` of the exact result: random sums whose operands' exponents
lie at most four apart, so that every rounding case occurs: exact, below and above the midpoint,
ties, the subnormal range, and a quarter built so that the sum rounds up into the next binade.
Then quotients of the same operands, and `k / n` for the naturals below `2^53` that `χ_s` divides.
Each control swaps in a nearby rounding rule, which this machine must refute.
-/

namespace Attack

open Plausible

/-- The exact value of a finite binary64 number, read off its bits; `none` for `±∞` and NaN. -/
def toRat? (f : Float) : Option ℚ :=
  let b := f.toBits.toNat
  let s : ℚ := if b / 2 ^ 63 = 1 then -1 else 1
  let e : ℕ := b / 2 ^ 52 % 2 ^ 11
  let m : ℕ := b % 2 ^ 52
  if e = 2047 then none
  else if e = 0 then some (s * m * 2 ^ (-1074 : ℤ))
  else some (s * (2 ^ 52 + m) * 2 ^ ((e : ℤ) - 1075))

/-- Two binary64 operands, as bits. -/
structure Pair where
  a : UInt64
  b : UInt64

instance : Repr Pair where
  reprPrec p _ := s!"{Float.ofBits p.a} {Float.ofBits p.b}"

instance : Shrinkable Pair := ⟨fun _ ↦ []⟩

/-- A random sign, biased exponent and significand; half the significands keep only their top
22 bits, so that sums are often exact or exact ties. -/
def genBits (e : Nat) : Gen UInt64 := do
  let s := (← Gen.choose Nat 0 1 (by omega)).1
  let m := (← Gen.choose Nat 0 (2 ^ 52 - 1) (by omega)).1
  let short := (← Gen.choose Nat 0 1 (by omega)).1
  let m := if short = 1 then m / 2 ^ 30 * 2 ^ 30 else m
  return UInt64.ofNat (s * 2 ^ 63 + e * 2 ^ 52 + m)

/-- Positive normal `a` and `b`, `b` one binade below `a`, whose exact sum is `(2^54 − 1 − j)` units
of `b`'s ulp: a 54-bit significand of all ones (a tie that rounds up into the next binade) for
`j = 0`, one that rounds exactly for `j = 1`, down for `j = 2`. -/
def genCarry : Gen Pair := do
  let e := (← Gen.choose Nat 2 2040 (by omega)).1
  let ma := (← Gen.choose Nat 0 (2 ^ 51 - 1) (by omega)).1
  let j := (← Gen.choose Nat 0 2 (by omega)).1
  let mb := 2 ^ 52 - 1 - 2 * ma - j
  return ⟨UInt64.ofNat (e * 2 ^ 52 + ma), UInt64.ofNat ((e - 1) * 2 ^ 52 + mb)⟩

/-- A quarter from `genCarry`; the rest with biased exponents at most four apart, half of them at
the bottom of the range (subnormals are biased exponent `0`), the others anywhere up to `2040`, so
that nothing overflows. -/
instance : Arbitrary Pair where
  arbitrary := do
    if (← Gen.choose Nat 0 3 (by omega)).1 = 0 then genCarry else
    let low := (← Gen.choose Nat 0 1 (by omega)).1
    let e₁ := (← Gen.choose Nat 0 (if low = 1 then 4 else 2040) (by split <;> omega)).1
    let d := (← Gen.choose Nat 0 8 (by omega)).1
    let e₂ := min 2040 (e₁ + d - 4)
    return ⟨← genBits e₁, ← genBits e₂⟩

/-- `op` on this machine agrees with `round` of the exact result `exact`. -/
def agrees (round : ℚ → ℚ) (op : Float → Float → Float) (exact : ℚ → ℚ → ℚ) (p : Pair) : Bool :=
  let a := Float.ofBits p.a
  let b := Float.ofBits p.b
  match toRat? a, toRat? b, toRat? (op a b) with
  | some x, some y, some z => decide (z = round (exact x y))
  | _, _, _ => false

/- The model: `a + b` is `rn (a + b)` on this machine. -/
#eval survives (∀ p : Pair, agrees rn (· + ·) (· + ·) p = true) 131

/- The model: `a / b` is `rn (a / b)`. Zero divisors are guarded off. -/
#eval survives (∀ p : Pair, (toRat? (Float.ofBits p.b) != some 0) = true →
  agrees rn (· / ·) (· / ·) p = true) 132

/-- A numerator and denominator `k ≤ n < 2^53`, as `χ_s = chain / n_s` divides them. -/
structure Ratio where
  k : Nat
  n : Nat
deriving Repr

instance : Shrinkable Ratio := ⟨fun _ ↦ []⟩

/-- Half the denominators below `2^53`, half below `2^16`; half the numerators near `n`. -/
instance : Arbitrary Ratio where
  arbitrary := do
    let big := (← Gen.choose Nat 0 1 (by omega)).1
    let n := (← Gen.choose Nat 1 (if big = 1 then 2 ^ 53 - 1 else 2 ^ 16) (by split <;> omega)).1
    let near := (← Gen.choose Nat 0 1 (by omega)).1
    let k := (← Gen.choose Nat 0 n (by omega)).1
    return ⟨if near = 1 then n - min n (k % 4) else k, n⟩

/-- `k.toFloat / n.toFloat` on this machine is `rn (k / n)`. -/
def ratioAgrees (r : Ratio) : Bool :=
  toRat? (r.k.toFloat / r.n.toFloat) == some (rn ((r.k : ℚ) / r.n))

/- The model on `χ_s`'s one division. -/
#eval survives (∀ r : Ratio, ratioAgrees r = true) 133

/-- Control, ties away from zero: Mathlib's `round` in place of `rne`. -/
def rnAway (x : ℚ) : ℚ := round (x / 2 ^ cexp x) * 2 ^ cexp x

/-- Control, 52 significand bits instead of 53. -/
def rn52 (x : ℚ) : ℚ := rne (x / 2 ^ (cexp x + 1)) * 2 ^ (cexp x + 1)

/-- Control, gradual underflow dropped: results below the least normal `2⁻¹⁰²²` flush to zero. -/
def rnFlush (x : ℚ) : ℚ := if |x| < 2 ^ (-1022 : ℤ) then 0 else rn x

#eval refuted (∀ p : Pair, agrees rnAway (· + ·) (· + ·) p = true) 134
#eval refuted (∀ p : Pair, agrees rn52 (· + ·) (· + ·) p = true) 135
#eval refuted (∀ p : Pair, agrees rnFlush (· + ·) (· + ·) p = true) 136

end Attack

end Palace.Binary64
