import Mathlib.Algebra.Order.Field.Power
import Mathlib.Algebra.Order.Round
import Mathlib.Data.Int.Log
import Mathlib.Data.Rat.Floor
import Mathlib.Tactic.FieldSimp
import Mathlib.Tactic.GCongr
import Mathlib.Tactic.IntervalCases
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.Positivity
import Mathlib.Tactic.Ring
import Mathlib.Testing.Plausible.Sampleable
import Palace.Attack

/-!
# The binary64 rounding model: L3's substrate

Rung L3 of the Lean ladder (dn-mathematical-foundations §2.4) is the numerical bridge: claims about
what float64 arithmetic computes, checked against a model of IEEE 754 rounding, entered one claim at
a time. This file is the model. FloatSpec, the Flocq port the note names, pins an older Lean and
Mathlib than this package, and Mathlib's own `FP` module is deprecated without replacement, so the
model is written here, small, in Flocq's terms.

* `rne y` is the nearest integer to `y`, ties to even.
* `cexp x = max (⌊log₂ |x|⌋ − 52) (−1074)` is the exponent of `x`'s ulp: Flocq's FLT format with
  binary64's 53-bit significand and least subnormal `2⁻¹⁰⁷⁴`.
* `rn x = rne (x / 2^cexp x) · 2^cexp x` is round to nearest, ties to even, IEEE 754's default.

Overflow is not modeled, so `rn` is binary64's rounding below `2^1024`. Every basic operation of
IEEE 754 returns `rn` of its exact result: `a ⊕ b = rn (a + b)`, and likewise for `−`, `×`, `÷`.
For Lean's own `Float` that is a theorem (`Palace/FloatModel.lean`); the attacks below check it
against this machine's arithmetic.

The laws: `rn` fixes binary64 numbers, is monotone and odd, lands on binary64, and moves `x` by at
most half an ulp. On the grid of multiples of `2⁻¹⁰⁷⁴`, where every sum of binary64 numbers lies,
it moves `x` by at most `u|x|` with `u = 2⁻⁵³`, subnormals included.
-/

namespace Palace.Binary64

variable {K : Type*} [Field K] [LinearOrder K] [IsStrictOrderedRing K] [FloorRing K]

section Rne

/-- The nearest integer to `y`, ties to even: IEEE 754's default rounding of a significand. -/
def rne (y : K) : ℤ :=
  if Int.fract y < 1 / 2 then ⌊y⌋
  else if 1 / 2 < Int.fract y then ⌊y⌋ + 1
  else if ⌊y⌋ % 2 = 0 then ⌊y⌋ else ⌊y⌋ + 1

omit [IsStrictOrderedRing K] in
theorem fract_eq (y : K) : Int.fract y = y - ⌊y⌋ := rfl

@[simp] theorem rne_intCast (z : ℤ) : rne (z : K) = z := by
  simp [rne]

@[simp] theorem rne_zero : rne (0 : K) = 0 := by
  simpa using rne_intCast (K := K) 0

omit [IsStrictOrderedRing K] in
theorem floor_le_rne (y : K) : ⌊y⌋ ≤ rne y := by
  unfold rne; split_ifs <;> omega

omit [IsStrictOrderedRing K] in
theorem rne_le_floor_add_one (y : K) : rne y ≤ ⌊y⌋ + 1 := by
  unfold rne; split_ifs <;> omega

/-- `rne` moves its argument by at most a half. -/
theorem abs_sub_rne (y : K) : |y - rne y| ≤ 1 / 2 := by
  have h0 := Int.fract_nonneg y
  have h1 := Int.fract_lt_one y
  rw [fract_eq] at h0 h1
  rw [abs_le]
  unfold rne
  split_ifs with ha hb <;> rw [fract_eq] at * <;> push_cast <;> constructor <;> linarith

theorem rne_mono : Monotone (rne : K → ℤ) := by
  intro a b hab
  rcases (Int.floor_mono hab).lt_or_eq with hlt | heq
  · calc rne a ≤ ⌊a⌋ + 1 := rne_le_floor_add_one a
      _ ≤ ⌊b⌋ := hlt
      _ ≤ rne b := floor_le_rne b
  · have hf : Int.fract a ≤ Int.fract b := by
      rw [fract_eq, fract_eq, heq]; linarith
    unfold rne
    rw [heq]
    split_ifs <;> first | omega | (exfalso; linarith)

theorem rne_le_of_le {y : K} {z : ℤ} (h : y ≤ z) : rne y ≤ z :=
  (rne_mono h).trans_eq (rne_intCast z)

theorem le_rne_of_le {y : K} {z : ℤ} (h : (z : K) ≤ y) : z ≤ rne y :=
  (rne_intCast z).symm.trans_le (rne_mono h)

/-- Below `z + ½`, `rne` stays at most `z`. -/
theorem rne_le_of_lt_add_half {y : K} {z : ℤ} (h : y < z + 1 / 2) : rne y ≤ z := by
  have hfy := Int.floor_le y
  rcases lt_or_ge ⌊y⌋ z with hz | hz
  · exact (rne_le_floor_add_one y).trans (by omega)
  · have hz' : (z : K) ≤ ⌊y⌋ := by exact_mod_cast hz
    have : ⌊y⌋ < z + 1 := by
      have : (⌊y⌋ : K) < z + 1 := by linarith
      exact_mod_cast this
    have hfz : ⌊y⌋ = z := by omega
    have hlt : Int.fract y < 1 / 2 := by rw [fract_eq, hfz]; linarith
    unfold rne
    simp only [hlt, ↓reduceIte, hfz, le_refl]

/-- Within half below `z + ½`, `rne` is `z`. -/
theorem rne_of_lt_half {y : K} {z : ℤ} (h1 : (z : K) ≤ y) (h2 : y < z + 1 / 2) : rne y = z :=
  le_antisymm (rne_le_of_lt_add_half h2) (le_rne_of_le h1)

/-- Past the midpoint `z + ½`, `rne` is `z + 1`. -/
theorem rne_of_gt_half {y : K} {z : ℤ} (h1 : (z : K) + 1 / 2 < y) (h2 : y < z + 1) :
    rne y = z + 1 := by
  have hf : ⌊y⌋ = z := Int.floor_eq_iff.2 ⟨by linarith, h2⟩
  have ha : ¬ Int.fract y < 1 / 2 := by rw [fract_eq, hf]; linarith
  have hb : 1 / 2 < Int.fract y := by rw [fract_eq, hf]; linarith
  unfold rne
  simp only [ha, hb, ↓reduceIte, hf]

/-- At a tie above an odd `z`, `rne` goes up to the even `z + 1`. -/
theorem rne_tie_odd {z : ℤ} (hz : z % 2 = 1) : rne ((z : K) + 1 / 2) = z + 1 := by
  have hf : ⌊(z : K) + 1 / 2⌋ = z := Int.floor_eq_iff.2 ⟨by linarith, by linarith⟩
  have ha : ¬ Int.fract ((z : K) + 1 / 2) < 1 / 2 := by rw [fract_eq, hf]; simp
  have hb : ¬ 1 / 2 < Int.fract ((z : K) + 1 / 2) := by rw [fract_eq, hf]; simp
  have hc : ¬ z % 2 = 0 := by omega
  unfold rne
  simp only [ha, hb, hc, ↓reduceIte, hf]

/-- `rne` is odd: ties to even is symmetric under negation. -/
theorem rne_neg (y : K) : rne (-y) = -rne y := by
  rcases eq_or_ne (Int.fract y) 0 with h | h
  · have hy : y = ⌊y⌋ := by rw [fract_eq] at h; linarith
    rw [hy, ← Int.cast_neg, rne_intCast, rne_intCast]
  · have hf := Int.fract_neg h
    have hfl : ⌊-y⌋ = -⌊y⌋ - 1 := by
      have : ((⌊-y⌋ : ℤ) : K) = -⌊y⌋ - 1 := by
        rw [fract_eq, fract_eq] at hf; linarith
      exact_mod_cast this
    unfold rne
    rw [hf, hfl]
    split_ifs <;> first | omega | (exfalso; linarith)

omit [IsStrictOrderedRing K] in
theorem rne_nonneg {y : K} (h : 0 ≤ y) : 0 ≤ rne y :=
  (Int.floor_nonneg.2 h).trans (floor_le_rne y)

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

/-- `x` lies on the grid of multiples of `2⁻¹⁰⁷⁴`, which holds every binary64 number and every sum
of them. -/
def OnGrid (x : K) : Prop := ∃ z : ℤ, x = z * 2 ^ (-1074 : ℤ)

theorem two_zpow_log_le {x : K} (hx : 0 < x) : (2 : K) ^ Int.log 2 x ≤ x := by
  simpa using Int.zpow_log_le_self (b := 2) (by norm_num) hx

theorem lt_two_zpow_log_add_one (x : K) : x < (2 : K) ^ (Int.log 2 x + 1) := by
  simpa using Int.lt_zpow_succ_log_self (b := 2) (by norm_num) x

theorem log_eq {x : K} {l : ℤ} (h1 : (2 : K) ^ l ≤ x) (h2 : x < 2 ^ (l + 1)) : Int.log 2 x = l := by
  have hx : 0 < x := (zpow_pos two_pos l).trans_le h1
  have a := (Int.zpow_le_iff_le_log (b := 2) (by norm_num) hx).1 (by simpa using h1)
  have b := (Int.lt_zpow_iff_log_lt (b := 2) (by norm_num) hx).1 (by simpa using h2)
  omega

omit [LinearOrder K] [IsStrictOrderedRing K] [FloorRing K] in
theorem two_zpow_natCast (k : ℕ) : (2 : K) ^ (k : ℤ) = ((2 ^ k : ℤ) : K) := by
  rw [zpow_natCast]; push_cast; rfl

omit [IsStrictOrderedRing K] in
theorem le_cexp (x : K) : -1074 ≤ cexp x := le_max_right _ _

omit [IsStrictOrderedRing K] in
theorem cexp_neg (x : K) : cexp (-x) = cexp x := by
  rw [cexp, cexp, abs_neg]

@[simp] theorem rn_zero : rn (0 : K) = 0 := by
  simp [rn]

/-- `rn` fixes every multiple of `x`'s ulp. -/
theorem rn_eq_self {x : K} {z : ℤ} (h : x = z * 2 ^ cexp x) : rn x = x := by
  rw [rn, (div_eq_iff (zpow_ne_zero _ two_ne_zero)).2 h, rne_intCast]
  exact h.symm

/-- `rn` fixes binary64 numbers. -/
theorem rn_isFloat {x : K} (hx : IsFloat x) : rn x = x := by
  obtain ⟨m, e, hm, he, rfl⟩ := hx
  rcases eq_or_ne m 0 with rfl | hm0
  · simp
  have hle : cexp ((m : K) * 2 ^ e) ≤ e := by
    refine max_le ?_ he
    have hpos : 0 < |(m : K) * 2 ^ e| :=
      abs_pos.2 (mul_ne_zero (Int.cast_ne_zero.2 hm0) (zpow_ne_zero _ two_ne_zero))
    have hlt : |(m : K) * 2 ^ e| < (2 : K) ^ (53 + e) := by
      rw [abs_mul, abs_of_pos (show (0 : K) < 2 ^ e from zpow_pos two_pos e),
        zpow_add₀ two_ne_zero]
      gcongr
      have h1 : ((|m| : ℤ) : K) < ((2 ^ 53 : ℤ) : K) := by exact_mod_cast hm
      norm_num at h1 ⊢
      exact h1
    have := (Int.lt_zpow_iff_log_lt (b := 2) (by norm_num) hpos).1 (by simpa using hlt)
    omega
  generalize hc : cexp ((m : K) * 2 ^ e) = c at hle
  obtain ⟨k, hk⟩ := Int.eq_ofNat_of_zero_le (sub_nonneg.2 hle)
  refine rn_eq_self (z := m * 2 ^ k) ?_
  rw [hc, show e = k + c by omega, zpow_add₀ two_ne_zero, two_zpow_natCast]
  push_cast; ring

theorem rn_one : rn (1 : K) = 1 :=
  rn_isFloat ⟨1, 0, by norm_num, by norm_num, by simp⟩

/-- `rn` moves `x` by at most half an ulp. -/
theorem abs_rn_sub_le (x : K) : |rn x - x| ≤ 2 ^ cexp x / 2 := by
  have h2 : (0 : K) < 2 ^ cexp x := zpow_pos two_pos _
  have key : rn x - x = (rne (x / 2 ^ cexp x) - x / 2 ^ cexp x) * 2 ^ cexp x := by
    rw [rn, sub_mul, div_mul_cancel₀ x h2.ne']
  rw [key, abs_mul, abs_of_pos h2, abs_sub_comm]
  have := abs_sub_rne (x / 2 ^ cexp x)
  calc |x / 2 ^ cexp x - rne (x / 2 ^ cexp x)| * 2 ^ cexp x ≤ 1 / 2 * 2 ^ cexp x := by gcongr
    _ = 2 ^ cexp x / 2 := by ring

/-- In the normal range the error is relative: at most `u|x|`. -/
theorem abs_rn_sub_le_of_normal {x : K} (hx : x ≠ 0) (h : -1074 ≤ Int.log 2 |x| - 52) :
    |rn x - x| ≤ u * |x| := by
  have hc : cexp x = Int.log 2 |x| - 52 := by rw [cexp, max_eq_left h]
  have hlog := two_zpow_log_le (abs_pos.2 hx)
  calc |rn x - x| ≤ 2 ^ cexp x / 2 := abs_rn_sub_le x
    _ = u * 2 ^ Int.log 2 |x| := by
      rw [hc, u, ← zpow_add₀ two_ne_zero,
        show Int.log 2 |x| - 52 = -53 + Int.log 2 |x| + 1 by ring, zpow_add_one₀ two_ne_zero]
      ring
    _ ≤ u * |x| := by gcongr

/-- `rn` is odd. -/
theorem rn_neg (x : K) : rn (-x) = -rn x := by
  rw [rn, rn, cexp_neg, neg_div, rne_neg]; push_cast; ring

theorem rn_nonneg {x : K} (hx : 0 ≤ x) : 0 ≤ rn x := by
  rw [rn]
  have := rne_nonneg (div_nonneg hx (zpow_pos two_pos (cexp x)).le)
  positivity

theorem rn_nonpos {x : K} (hx : x ≤ 0) : rn x ≤ 0 := by
  have := rn_nonneg (neg_nonneg.2 hx)
  rw [rn_neg] at this; linarith

/-- Below `2^L`, with `L` above `x`'s binade and its ulp exponent, `rn x` stays at most `2^L`. -/
theorem rn_le_two_zpow {x : K} {L : ℤ} (hL : Int.log 2 x < L) (hc : cexp x ≤ L) :
    rn x ≤ 2 ^ L := by
  have hx : x < 2 ^ L :=
    (lt_two_zpow_log_add_one x).trans_le (zpow_le_zpow_right₀ one_le_two (by omega))
  obtain ⟨k, hk⟩ := Int.eq_ofNat_of_zero_le (sub_nonneg.2 hc)
  have h2L : (2 : K) ^ L = ((2 ^ k : ℤ) : K) * 2 ^ cexp x := by
    rw [← two_zpow_natCast, ← zpow_add₀ two_ne_zero, ← hk]; ring_nf
  have hy : x / 2 ^ cexp x ≤ ((2 ^ k : ℤ) : K) := by
    rw [div_le_iff₀ (zpow_pos two_pos _), ← h2L]; exact hx.le
  rw [rn, h2L]
  gcongr
  exact_mod_cast rne_le_of_le hy

/-- In the normal range, `rn y` is at least the bottom `2^⌊log₂ y⌋` of `y`'s binade. -/
theorem two_zpow_log_le_rn {y : K} (hy : 0 < y) (hc : cexp y = Int.log 2 y - 52) :
    2 ^ Int.log 2 y ≤ rn y := by
  have h2 : (2 : K) ^ Int.log 2 y = ((2 ^ 52 : ℤ) : K) * 2 ^ cexp y := by
    rw [hc, ← two_zpow_natCast, ← zpow_add₀ two_ne_zero]; ring_nf
  have hle : ((2 ^ 52 : ℤ) : K) ≤ y / 2 ^ cexp y := by
    rw [le_div_iff₀ (zpow_pos two_pos _), ← h2]; exact two_zpow_log_le hy
  rw [rn, h2]
  gcongr
  exact_mod_cast le_rne_of_le hle

theorem rn_le_rn_of_nonneg {x y : K} (hx : 0 ≤ x) (hxy : x ≤ y) : rn x ≤ rn y := by
  rcases hx.eq_or_lt with rfl | hx
  · rw [rn_zero]; exact rn_nonneg hxy
  have hy := hx.trans_le hxy
  have hlog : Int.log 2 x ≤ Int.log 2 y := Int.log_mono_right hx hxy
  have hcx : cexp x = max (Int.log 2 x - 52) (-1074) := by rw [cexp, abs_of_pos hx]
  have hcy : cexp y = max (Int.log 2 y - 52) (-1074) := by rw [cexp, abs_of_pos hy]
  have hc : cexp x ≤ cexp y := by rw [hcx, hcy]; exact max_le_max (by omega) le_rfl
  rcases hc.eq_or_lt with hc | hc
  · rw [rn, rn, hc]
    gcongr
    exact_mod_cast rne_mono (div_le_div_of_nonneg_right hxy (zpow_pos two_pos _).le)
  · -- `y`'s binade lies above `x`'s: `rn x ≤ 2 ^ ⌊log₂ y⌋ ≤ rn y`
    have hx1 := le_cexp x
    have hx2 : Int.log 2 x - 52 ≤ cexp x := by rw [hcx]; exact le_max_left _ _
    have hny : cexp y = Int.log 2 y - 52 := by
      rw [hcy] at hc ⊢
      exact max_eq_left (by by_contra h; rw [max_eq_right (by omega)] at hc; omega)
    rw [hny] at hc
    exact (rn_le_two_zpow (by omega) (by omega)).trans (two_zpow_log_le_rn hy hny)

/-- `rn` is monotone. -/
theorem rn_mono : Monotone (rn : K → K) := by
  intro x y hxy
  rcases le_total 0 x with hx | hx
  · exact rn_le_rn_of_nonneg hx hxy
  rcases le_total 0 y with hy | hy
  · exact (rn_nonpos hx).trans (rn_nonneg hy)
  · have := rn_le_rn_of_nonneg (neg_nonneg.2 hy) (neg_le_neg hxy)
    rw [rn_neg, rn_neg] at this; linarith

/-- `rn` lands on binary64. -/
theorem isFloat_rn (x : K) : IsFloat (rn x) := by
  rw [rn]
  have hc : Int.log 2 |x| - 52 ≤ cexp x := le_max_left _ _
  have hy : |x / 2 ^ cexp x| < 2 ^ (53 : ℤ) := by
    rw [abs_div, abs_of_pos (show (0 : K) < 2 ^ cexp x from zpow_pos two_pos _),
      div_lt_iff₀ (zpow_pos two_pos _), ← zpow_add₀ two_ne_zero]
    exact (lt_two_zpow_log_add_one |x|).trans_le (zpow_le_zpow_right₀ one_le_two (by omega))
  rw [abs_lt] at hy
  have hb : |rne (x / 2 ^ cexp x)| ≤ 2 ^ 53 := by
    rw [abs_le]
    constructor
    · exact le_rne_of_le (by push_cast; norm_num at hy ⊢; linarith)
    · exact rne_le_of_le (by push_cast; norm_num at hy ⊢; linarith)
  rcases hb.lt_or_eq with hb | hb
  · exact ⟨_, cexp x, hb, le_cexp x, rfl⟩
  · have h2 : (2 : ℤ) ∣ rne (x / 2 ^ cexp x) := by
      rcases abs_eq (by norm_num) |>.1 hb with h | h <;> rw [h] <;> norm_num
    refine ⟨rne (x / 2 ^ cexp x) / 2, cexp x + 1, ?_, by have := le_cexp x; omega, ?_⟩
    · rcases abs_eq (by norm_num) |>.1 hb with h | h <;> rw [h] <;> norm_num
    · rw [Int.cast_div h2 (by norm_num), zpow_add_one₀ two_ne_zero]
      push_cast; ring

omit [IsStrictOrderedRing K] in
theorem IsFloat.onGrid {x : K} (hx : IsFloat x) : OnGrid x := by
  obtain ⟨m, e, -, he, rfl⟩ := hx
  obtain ⟨k, hk⟩ := Int.eq_ofNat_of_zero_le (sub_nonneg.2 he)
  refine ⟨m * 2 ^ k, ?_⟩
  rw [show e = k + -1074 by omega, zpow_add₀ two_ne_zero, two_zpow_natCast]
  push_cast; ring

omit [LinearOrder K] [IsStrictOrderedRing K] [FloorRing K] in
theorem OnGrid.add {x y : K} (hx : OnGrid x) (hy : OnGrid y) : OnGrid (x + y) := by
  obtain ⟨a, rfl⟩ := hx
  obtain ⟨b, rfl⟩ := hy
  exact ⟨a + b, by push_cast; ring⟩

/-- On the grid of multiples of `2⁻¹⁰⁷⁴`, so for every sum of two binary64 numbers, the error is
relative, subnormals included: there the sum is itself a binary64 number. -/
theorem abs_rn_sub_le_of_onGrid {x : K} (hx : OnGrid x) : |rn x - x| ≤ u * |x| := by
  rcases eq_or_ne x 0 with rfl | h0
  · simp
  by_cases h : -1074 ≤ Int.log 2 |x| - 52
  · exact abs_rn_sub_le_of_normal h0 h
  · have hc : cexp x = -1074 := max_eq_right (by omega)
    obtain ⟨z, hz⟩ := hx
    rw [rn_eq_self (z := z) (by rw [hc]; exact hz), sub_self, abs_zero]
    positivity

/-- `rn` inside the binade `[2^l, 2^(l+1))` of the normal range, where the grid spacing is
`2^(l − 52)`. -/
theorem rn_of_binade {x : K} {l : ℤ} (h1 : (2 : K) ^ l ≤ x) (h2 : x < 2 ^ (l + 1))
    (hl : -1074 ≤ l - 52) : rn x = rne (x / 2 ^ (l - 52)) * 2 ^ (l - 52) := by
  have hx : 0 < x := (zpow_pos two_pos l).trans_le h1
  rw [rn, cexp, abs_of_pos hx, log_eq h1 h2, max_eq_left hl]

end Rn

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
