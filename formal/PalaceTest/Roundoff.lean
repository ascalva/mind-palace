module

public import Palace.Roundoff
public import PalaceTest.Binary64
public meta import Palace.Roundoff
public meta import PalaceTest.Binary64

/-!
# Attacks on `Palace.Roundoff`

The Plausible attacks and negative controls for the laws of `Palace/Roundoff.lean`. They run
when this module builds (`lake test`); the library itself runs no code at build time.
-/

@[expose] public section

namespace Palace.Binary64

/-! ## Attacks: both claims on this machine

The theorems hold over the model; these run the same statements in this machine's binary64. LAP-1:
rows of one to four nonnegative weights, summed left to right, right to left and pairwise, agree
within `4 · eps` of each result. The control draws eleven summands, `1` and ten copies of one `t`
between a quarter and a half ulp of `1`, absorbed one at a time or gathered first, and must break
the bound. CND-6: `k / n == 1.0` exactly
when `k = n`, below `2^53`. The control asks the same of binary32, whose 24-bit significand rounds
`(n − 1)/n` to `1` from `n ≈ 2^24` on.
-/

namespace Attack

open Plausible

/-- A degree's nonzero weights, as bits. -/
structure Row where
  w : List UInt64

instance : Repr Row where
  reprPrec r _ := repr (r.w.map Float.ofBits)

instance : Shrinkable Row := ⟨fun _ ↦ []⟩

/-- One to four weights with random significands, within eight binades of `1` or, one time in
eight, subnormal. -/
instance : Arbitrary Row where
  arbitrary := do
    let k := (← Gen.choose Nat 1 4 (by omega)).1
    let w ← (List.range k).mapM fun _ ↦ do
      let sub := (← Gen.choose Nat 0 7 (by omega)).1
      let e := (← Gen.choose Nat 1015 1031 (by omega)).1
      let m := (← Gen.choose Nat 0 (2 ^ 52 - 1) (by omega)).1
      return UInt64.ofNat ((if sub = 0 then 0 else e) * 2 ^ 52 + m)
    return ⟨w⟩

/-- Pairwise summation of up to four summands. -/
def pairwise : List Float → Float
  | [a, b, c, d] => (a + b) + (c + d)
  | [a, b, c] => (a + b) + c
  | xs => xs.foldl (· + ·) 0

/-- The row summed left to right, right to left and pairwise, as exact values. -/
def sums (r : Row) : List ℚ :=
  let xs := r.w.map Float.ofBits
  [xs.foldl (· + ·) 0, xs.foldr (· + ·) 0, pairwise xs].filterMap toRat?

/-- The orders do not all agree: the row reassociates. -/
def reassociates (r : Row) : Bool :=
  (sums r).any fun a ↦ (sums r).any (· != a)

/-- The three orders agree pairwise within `4 · eps` of each result. -/
def agreeWithin (r : Row) : Bool :=
  (sums r).length == 3 &&
    (sums r).all fun a ↦ (sums r).all fun b ↦ decide (|a - b| ≤ 4 * 2 ^ (-52 : ℤ) * b)

/- LAP-1: up to four summands, three orders, counting only rows that reassociate. -/
#eval survives (∀ r : Row, reassociates r = true → agreeWithin r = true) 137

/-- One `t` in `[2⁻⁵⁴, 2⁻⁵³)`, as bits. -/
structure Small where
  t : UInt64

instance : Repr Small := ⟨fun w _ ↦ repr (Float.ofBits w.t)⟩

instance : Shrinkable Small := ⟨fun _ ↦ []⟩

instance : Arbitrary Small where
  arbitrary := do
    let m := (← Gen.choose Nat 0 (2 ^ 52 - 1) (by omega)).1
    return ⟨UInt64.ofNat (969 * 2 ^ 52 + m)⟩

/-- `1` and ten `t`s, absorbed one at a time and gathered first, agree within the test's bound. -/
def elevenAgree (w : Small) : Bool :=
  let t := Float.ofBits w.t
  let absorbed := (List.replicate 10 t).foldl (· + ·) 1
  let gathered := 1 + (List.replicate 9 t).foldl (· + ·) t
  match toRat? absorbed, toRat? gathered with
  | some a, some b => decide (|a - b| ≤ 4 * 2 ^ (-52 : ℤ) * max 1 (max a b))
  | _, _ => false

/- Control, eleven summands absorbed one at a time or gathered first. -/
#eval refuted (∀ w : Small, elevenAgree w = true) 138

/-- The witness of `lap1_fails` on this machine: from `1 + 2u`, the low order gives `1 + 4u` and
the high order `1 + 14u`. -/
def lap1Witness : Bool :=
  let u : Float := 1 / 9007199254740992
  let b : Float := 1 + 2 * u
  let low := (List.replicate 6 u).foldl (· + ·) (b + 3 * u)
  let high := ((((b + u) + (u + u)) + u) + 3 * u) + (u + u)
  toRat? low == some (1 + 4 * 2 ^ (-53 : ℤ)) && toRat? high == some (1 + 14 * 2 ^ (-53 : ℤ))

#eval show Lean.CoreM Unit from do
  unless lap1Witness do throwError "the LAP-1 witness does not reproduce on this machine"
  Lean.logInfo "the LAP-1 witness reproduces on this machine"

/- CND-6: `k / n == 1.0` exactly when `k = n`, for `k ≤ n < 2^53`. -/
#eval survives (∀ r : Ratio, (r.k.toFloat / r.n.toFloat == 1) = (r.k == r.n)) 139

/- Control, the same law in binary32. -/
#eval refuted (∀ r : Ratio, (r.k.toFloat32 / r.n.toFloat32 == 1) = (r.k == r.n)) 140

end Attack

end Palace.Binary64
