module

public import Palace.Format
public import Mathlib.Testing.Plausible.Sampleable
public import PalaceTest.Attack
public import PalaceTest.Binary64
public meta import Palace.Format
public meta import Mathlib.Testing.Plausible.Sampleable
public meta import PalaceTest.Attack
public meta import PalaceTest.Binary64

/-!
# Attacks on `Palace.Format`

The general rounding `rnf p emin` against this machine, at the two formats the vector store uses
besides binary64 (whose attacks, in `PalaceTest/Binary64.lean`, check `rn = rnf 53 (-1074)`).

* binary32: Lean's `Float.toFloat32` compiles to C's conversion of a `double` to a `float`, so
  these attacks decode the hardware's result bit for bit and compare it with `rn32` of the exact
  value, on random doubles in the normal range, in the subnormal range, at exact subnormal ties
  and at the carries into the next binade.
* binary16: Lean has no half-precision type, so the machine's results come in as a table:
  `table16` holds 234 doubles and the float16 bits the vector store's own write path gave them on
  this machine (lancedb 0.33.0: a list of Python floats landed in a `float16` column). The path
  rounds twice, to float32 and then to float16, and the table is checked against `rn16 ∘ rn32`;
  39 of its doubles lie so near a float16 tie that rounding once gives another result, which is
  the control that the table tells the two apart. `tests/property/test_float16_margin.py`
  checks that the machine still gives the table's results.

Each control swaps in a nearby rule (ties away from zero, a significand one bit short, flush to
zero, rounding once), which the machine must refute.
-/

@[expose] public section

namespace Palace.Format

namespace Attack

open Plausible Palace.Binary64.Attack

/-- The exact value of a finite binary32 number, read off its bits; `none` for `±∞` and NaN. -/
def toRat32? (f : Float32) : Option ℚ :=
  let b := f.toBits.toNat
  let s : ℚ := if b / 2 ^ 31 = 1 then -1 else 1
  let e : ℕ := b / 2 ^ 23 % 2 ^ 8
  let m : ℕ := b % 2 ^ 23
  if e = 255 then none
  else if e = 0 then some (s * m * 2 ^ (-149 : ℤ))
  else some (s * (2 ^ 23 + m) * 2 ^ ((e : ℤ) - 150))

/-- The exact value of a finite binary16 number, read off its bits; `none` for `±∞` and NaN. -/
def toRat16? (b : UInt16) : Option ℚ :=
  let b := b.toNat
  let s : ℚ := if b / 2 ^ 15 = 1 then -1 else 1
  let e : ℕ := b / 2 ^ 10 % 2 ^ 5
  let m : ℕ := b % 2 ^ 10
  if e = 31 then none
  else if e = 0 then some (s * m * 2 ^ (-24 : ℤ))
  else some (s * (2 ^ 10 + m) * 2 ^ ((e : ℤ) - 25))

/-- The binary64 bits of `n · 2^e`, for `0 < n < 2^53` and a result in binary64's normal range. -/
def bitsOf (n : ℕ) (e : ℤ) : UInt64 :=
  let l := Nat.log2 n
  UInt64.ofNat ((l + e + 1023).toNat * 2 ^ 52 + (n - 2 ^ l) * 2 ^ (52 - l))

/-- A binary64 operand, as bits. -/
structure Dbl where
  bits : UInt64

instance : Repr Dbl where
  reprPrec d _ := s!"{Float.ofBits d.bits}"

instance : Shrinkable Dbl := ⟨fun _ ↦ []⟩

/-- A quarter each: doubles in binary32's normal range whose 29 bits below a binary32 significand
are zero, a tie, just off a tie, or random; doubles in binary32's subnormal range; odd multiples
of `2⁻¹⁵⁰`, the subnormal ties; and 26-bit significands of all ones or nearly, which round up
into the next binade or stay below it. -/
instance : Arbitrary Dbl where
  arbitrary := do
    let s := (← Gen.choose Nat 0 1 (by omega)).1 * 2 ^ 63
    match (← Gen.choose Nat 0 3 (by omega)).1 with
    | 0 =>
      let e := (← Gen.choose Nat (1023 - 126) (1023 + 126) (by omega)).1
      let top := (← Gen.choose Nat 0 (2 ^ 23 - 1) (by omega)).1
      let r := (← Gen.choose Nat 0 (2 ^ 29 - 1) (by omega)).1
      let low := match (← Gen.choose Nat 0 4 (by omega)).1 with
        | 0 => 0 | 1 => 2 ^ 28 | 2 => 2 ^ 28 + 1 | 3 => 2 ^ 28 - 1 | _ => r
      return ⟨UInt64.ofNat (s + e * 2 ^ 52 + top * 2 ^ 29 + low)⟩
    | 1 =>
      let e := (← Gen.choose Nat (1023 - 152) (1023 - 127) (by omega)).1
      let m := (← Gen.choose Nat 0 (2 ^ 52 - 1) (by omega)).1
      return ⟨UInt64.ofNat (s + e * 2 ^ 52 + m)⟩
    | 2 =>
      let m := (← Gen.choose Nat 0 (2 ^ 23 - 1) (by omega)).1
      return ⟨UInt64.ofNat s + bitsOf (2 * m + 1) (-150)⟩
    | _ =>
      let j := (← Gen.choose Nat 1 3 (by omega)).1
      let e := (← Gen.choose Nat 0 250 (by omega)).1
      return ⟨UInt64.ofNat s + bitsOf (2 ^ 26 - j) ((e : ℤ) - 175)⟩

/-- This machine's conversion of `d` to binary32 agrees with `round` of its exact value. -/
def agrees32 (round : ℚ → ℚ) (d : Dbl) : Bool :=
  let a := Float.ofBits d.bits
  match toRat? a, toRat32? a.toFloat32 with
  | some x, some y => decide (y = round x)
  | _, _ => false

/- The model: converting a double to binary32 on this machine is `rn32`. -/
#eval survives (∀ d : Dbl, agrees32 rn32 d = true) 300
/-- Control, ties away from zero. -/
def rnAway (p : ℕ) (emin : ℤ) (x : ℚ) : ℚ := round (x / 2 ^ cexpf p emin x) * 2 ^ cexpf p emin x

/-- Control, gradual underflow dropped: below the least normal binary32 number, zero. -/
def rn32Flush (x : ℚ) : ℚ := if |x| < 2 ^ (-126 : ℤ) then 0 else rn32 x

#eval refuted (∀ d : Dbl, agrees32 (rnAway 24 (-149)) d = true) 301
#eval refuted (∀ d : Dbl, agrees32 (rnf 23 (-149)) d = true) 302
#eval refuted (∀ d : Dbl, agrees32 rn32Flush d = true) 303
/-- This machine's float16: doubles, as bits, and the float16 bits the vector store's write path
gave them (lancedb 0.33.0, a list of Python floats landed in a `float16` column, 2026-11-05). -/
def table16 : List (UInt64 × UInt16) := [
  (0x407F5BC1C0000000, 0x5FD7), (0x40D8AA9640000000, 0x762B), (0xC022EB0380000000, 0xC8BB),
  (0xBF23AE7FE0000000, 0x88EC), (0xC07DA712E0000000, 0xDF6A), (0xBFDD9F1E60000000, 0xB768),
  (0x400982E3C0000000, 0x4261), (0xBFB56267A0000000, 0xAD59), (0xBFC4143500000000, 0xB105),
  (0x403D30E6A0000000, 0x4F4C), (0xC0ADAD57E0000000, 0xEB6B), (0xBF17CB1360000000, 0x85F3),
  (0x40602E4220000000, 0x580C), (0xC0C1C27CE0000000, 0xF071), (0x3FC49F75A0000000, 0x3128),
  (0x3F4B9C08A0000000, 0x12E7), (0xBFE6B0E640000000, 0xB9AC), (0x3F7DE4FEA0000000, 0x1F79),
  (0x3FD5EED7C0000000, 0x357C), (0xC04F6326C0000000, 0xD3D9), (0xBF733FF240000000, 0x9CD0),
  (0xC09DB68700000000, 0xE76E), (0xBF3C4DBD60000000, 0x8F13), (0xC0E9CE23C0000000, 0xFA74),
  (0x3F398C9380000000, 0x0E63), (0x4077FEFFA0000000, 0x5E00), (0x3F70BFFF80000000, 0x1C30),
  (0x4035893020000000, 0x4D62), (0x3FBF63F700000000, 0x2FD9), (0x3FE548DA00000000, 0x3952),
  (0xBF7D1CFEC0000000, 0x9F47), (0xC01583E080000000, 0xC561), (0x3EEE0A7920000000, 0x00F0),
  (0x3E931D8E80000000, 0x0005), (0xBEA1253D60000000, 0x8009), (0x3EF4436380000000, 0x0144),
  (0x3EFEB34320000000, 0x01EB), (0xBF05277400000000, 0x82A5), (0x3EE95271C0000000, 0x00CB),
  (0xBF09136B20000000, 0x8322), (0x3F06779860000000, 0x02CF), (0xBF0B7F9100000000, 0x8370),
  (0xBF03529CE0000000, 0x826A), (0xBEE43BE5E0000000, 0x80A2), (0x3F06FC3860000000, 0x02E0),
  (0x3EE0B506A0000000, 0x0086), (0xBEDA0DDF60000000, 0x8068), (0x3F044E9020000000, 0x028A),
  (0xBEF75371C0000000, 0x8175), (0x3F0170F240000000, 0x022E), (0x3F0FE675A0000000, 0x03FD),
  (0xBEF64BDDA0000000, 0x8165), (0x3F0EAF09A0000000, 0x03D6), (0x3F0E11C020000000, 0x03C2),
  (0xBF0C867200000000, 0x8391), (0x3EB203EAC0000000, 0x0012), (0xC0476E0000000000, 0xD1DC),
  (0x3FFBA20000000000, 0x3EE8), (0xC068860000000000, 0xDA22), (0xC0AB060000000000, 0xEAC2),
  (0xBF9F4E0000000000, 0xA7D4), (0x40438A0000000000, 0x50E2), (0x4073CA0000000000, 0x5CF2),
  (0xC0A7EE0000000000, 0xE9FC), (0xBF41CE0000000000, 0x9074), (0xC074660000000000, 0xDD1A),
  (0xBFB23A0000000000, 0xAC8E), (0x40140E0000000000, 0x4504), (0xBF5EA20000000000, 0x97A8),
  (0x40BF920000000000, 0x6FE4), (0x40A44E0000000000, 0x6914), (0x405E620000000000, 0x5798),
  (0x3F226A0000000000, 0x089A), (0xBF353A0000000000, 0x8D4E), (0x3FBF320000000000, 0x2FCC),
  (0xBF8BC60000000000, 0xA2F2), (0xBF695E0000000000, 0x9A58), (0xBF429E0000000000, 0x90A8),
  (0xBFEDF60000000000, 0xBB7E), (0x40BFA60000000000, 0x6FEA), (0xBF8E220000000000, 0xA388),
  (0x40B2260000000000, 0x6C8A), (0x3F5B2A0000000000, 0x16CA), (0x3F95C60000000000, 0x2572),
  (0x408F6A0000000000, 0x63DA), (0x402ABE0000000000, 0x4AB0), (0xC026A20000000000, 0xC9A8),
  (0xC0A20A0000000000, 0xE882), (0x3F0E2C0000000000, 0x03C6), (0x3EFFE80000000000, 0x01FE),
  (0x3F0F1C0000000000, 0x03E4), (0x3F089C0000000000, 0x0314), (0x3F09D40000000000, 0x033A),
  (0x3F03740000000000, 0x026E), (0x3EF7D80000000000, 0x017E), (0x3F08AC0000000000, 0x0316),
  (0x3FCFFE83A0000000, 0x3400), (0x3F2FFEEFA0000000, 0x0C00), (0x40BFFE87E0000000, 0x7000),
  (0x3F2FFE74C0000000, 0x0C00), (0x409FFEC680000000, 0x6800), (0x402FFE0780000000, 0x4C00),
  (0x3F6FFE2CC0000000, 0x1C00), (0x407FFE8040000000, 0x6000), (0x3FDFFEECE0000000, 0x3800),
  (0x3F9FFEBA60000000, 0x2800), (0x408FFEE240000000, 0x6400), (0x401FFEB9C0000000, 0x4800),
  (0x40DFFE1420000000, 0x7800), (0x3FDFFE11A0000000, 0x3800), (0x409FFE0B40000000, 0x6800),
  (0x3F5FFE0B60000000, 0x1800), (0x0000000000000000, 0x0000), (0x8000000000000000, 0x8000),
  (0x40EFFC0000000000, 0x7BFF), (0x40EFFDE000000000, 0x7BFF), (0x3E70000000000000, 0x0001),
  (0x3E60000000000000, 0x0000), (0x3E68000000000000, 0x0001), (0x3F10000000000000, 0x0400),
  (0x3FF0000000000000, 0x3C00), (0x3FF0020000000000, 0x3C00), (0xBF3415FFFFEBEA00, 0x8D06),
  (0x3F2B65FFFC934000, 0x0ADA), (0xBF40BE000085F000, 0x9030), (0x405DA5FFFFFF8968, 0x576A),
  (0x3F3725FFFD1B4000, 0x0DCA), (0xBF6C660000007198, 0x9B1A), (0xBF5E4E000000F270, 0x9794),
  (0x4084A5FFFFD6B400, 0x612A), (0xC024C9FFFFFF59B0, 0xC932), (0x40144DFFFFFF5D90, 0x4514),
  (0xC0B831FFFFFE7CE0, 0xEE0C), (0xC0C9FDFFFFFF3010, 0xF280), (0xC0C005FFFF7FD000, 0xF002),
  (0xBF59520000019520, 0x9654), (0x3FC30E000000261C, 0x30C4), (0xBF9AC5FFFFCA7400, 0xA6B2),
  (0xC09AEA00001AEA00, 0xE6BA), (0xBF493600000326C0, 0x924E), (0xBFF43DFFFFFFD784, 0xBD10),
  (0x3FD33A00000133A0, 0x34CE), (0xBF492DFFF9B48000, 0x924C), (0x40D651FFFD35C000, 0x7594),
  (0xC07C6E00001C6E00, 0xDF1C), (0xC0D14DFFFFBAC800, 0xF454), (0xC021ADFFFFDCA400, 0xC86C),
  (0xC040FDFFFEF02000, 0xD040), (0xBF65720000002AE4, 0x995C), (0xBF38260006098000, 0x8E0A),
  (0x40467600002CEC00, 0x519E), (0xC0DB99FFFFC8CC00, 0xF6E6), (0x405E620000F31000, 0x5798),
  (0x3F4231FFFFFEDCE0, 0x108C), (0xC01ACA0000359400, 0xC6B2), (0x40BF96000003F2C0, 0x6FE6),
  (0x40C221FFFFF6EF00, 0x7088), (0x40C1020000002204, 0x7040), (0xBF8D29FFFF8B5800, 0xA34A),
  (0xC0AAC5FFFFFFCA74, 0xEAB2), (0x3F7C1A0000038340, 0x1F06), (0x404DB1FFFFC49C00, 0x536C),
  (0x3F7F85FFFFE07A00, 0x1FE2), (0xBF7BE9FFFF905800, 0x9EFA), (0x4053DA0000009ED0, 0x54F6),
  (0xBFF38DFFFF639000, 0xBCE4), (0x4061960000119600, 0x5866), (0xC097B5FFFFFF4250, 0xE5EE),
  (0xC0847DFFFFFAE080, 0xE120), (0xC0BBF1FFFFC81C00, 0xEEFC), (0xBF47E2000005F880, 0x91F8),
  (0xC0567E000000B3F0, 0xD5A0), (0x4074F5FFFFFD6140, 0x5D3E), (0xBFE301FFFFFFB3F8, 0xB8C0),
  (0x403205FFFFFF6FD0, 0x4C82), (0xC059560006558000, 0xD656), (0xC0063DFFFFFFD384, 0xC190),
  (0x40193DFFFCD84000, 0x4650), (0xC0B0460000008230, 0xEC12), (0xBF36A20000002D44, 0x8DA8),
  (0x3FDF6A0003ED4000, 0x37DA), (0x4013EDFFFFF60900, 0x44FC), (0xC074EA0000014EA0, 0xDD3A),
  (0x3F40AA0000008550, 0x102A), (0x405359FFFFFFB298, 0x54D6), (0xC0B3020000009810, 0xECC0),
  (0x3E652F4A77510903, 0x0001), (0xBED4CD3E25EA6A40, 0x8053), (0xBE82F9A0216FF42A, 0x8002),
  (0x40407E332B2115A6, 0x5020), (0xBEBA47EB9F7EDDC8, 0x801A), (0x40ED6B103881BF59, 0x7B5B),
  (0xC0D37FEAD653D6DB, 0xF4E0), (0xC0A685D2E4FC80FD, 0xE9A1), (0x402081BE6BBB1921, 0x4820),
  (0x4043E8CBB2CD88D8, 0x50FA), (0x3FF265001D19B9BD, 0x3C99), (0xC09D8116F33656EB, 0xE760),
  (0x3EC9E9182041CD2A, 0x0034), (0xBEB051D2B5BFB427, 0x8010), (0x40C7AC1F70F3C321, 0x71EB),
  (0x40C852A31100AC1A, 0x7215), (0x3EDC6DDBA49D3524, 0x0072), (0x3F79B87873C257B0, 0x1E6E),
  (0x3EE2EB404B868448, 0x0097), (0xC007FAA78C2EBD87, 0xC1FF), (0x3EEFBA572B749AAF, 0x00FE),
  (0x3F70C7D02ED2C709, 0x1C32), (0xBFA181B61AED7CC5, 0xA860), (0x3F061296C549EDE6, 0x02C2),
  (0x3F0F2119B39000B6, 0x03E4), (0x3EB21BC1BD62E24B, 0x0012), (0xBFC1636088220606, 0xB059),
  (0x3F3F413AF8BB8AE8, 0x0FD0), (0x40CE5493B25F57B5, 0x7395), (0xC050C9A79DF5D8F6, 0xD432),
  (0xBE91D8682FDF4779, 0x8004), (0x3EAE8583876FC871, 0x000F), (0x3EC81900A8EFC5CA, 0x0030),
  (0x40D391ED4814F612, 0x74E4), (0xBE792AB90D63581A, 0x8002), (0xBFF533D0D7CEC4CA, 0xBD4D),
  (0x3FEE30D35EA79244, 0x3B8C), (0xC0E40250B8EA9532, 0xF901), (0xBF86C69CDA3714A6, 0xA1B2),
  (0x3FB2F307D5A70A5B, 0x2CBD), (0x4045B8E29E28B4ED, 0x516E), (0xC0A61E328F774DCF, 0xE988),
  (0x3F556CD790DCD814, 0x155B), (0xBF54332BE967914E, 0x950D), (0xBF805A765F303167, 0xA017),
  (0xC0335A2C78FC54F8, 0xCCD7), (0x3E9A50878931F46F, 0x0007), (0xBF2FA8A708A1E720, 0x8BEA)]

/-- How many of the table's entries `round` reproduces. -/
def table16Agreements (round : ℚ → ℚ) : ℕ :=
  (table16.filter fun (a, h) ↦
    match toRat? (Float.ofBits a), toRat16? h with
    | some x, some y => decide (y = round x)
    | _, _ => false).length

/-- The table attack: every entry agrees with `round`, or, for a control, some entry does not. -/
def tableCheck (name : String) (round : ℚ → ℚ) (control : Bool) : Lean.CoreM PUnit := do
  let n := table16Agreements round
  let total := table16.length
  if control then
    if n < total then
      Lean.logInfo m!"control refuted, as it must be: {name} disagrees with {total - n} of {total}"
    else Lean.throwError m!"negative control {name} agrees with all {total} entries"
  else
    if n = total then Lean.logInfo m!"attack survived: {name} agrees with all {total} entries"
    else Lean.throwError m!"{name} disagrees with {total - n} of {total} entries"

/- The model: the store's write path is `rn16 ∘ rn32`, bit for bit. -/
#eval tableCheck "rn16 ∘ rn32" (fun x ↦ rn16 (rn32 x)) false

/-- Control, flush to zero: below the least normal binary16 number, zero. -/
def rn16Flush (x : ℚ) : ℚ := if |x| < 2 ^ (-14 : ℤ) then 0 else rn16 x

#eval tableCheck "rounding once, rn16" rn16 true
#eval tableCheck "ties away from zero" (fun x ↦ rnAway 11 (-24) (rn32 x)) true
#eval tableCheck "ten significand bits" (fun x ↦ rnf 10 (-24) (rn32 x)) true
#eval tableCheck "flush to zero" (fun x ↦ rn16Flush (rn32 x)) true

end Attack

end Palace.Format
