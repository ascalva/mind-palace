module

public import Palace.FloatModel.Defs
public import Mathlib.Tactic.LinearCombination
public import Palace.Roundoff

/-!
# Lean's `Float` rounds as `rn` does

Lean core gives `Float` a logical model (`Init/Data/Float/Model`, Lean v4.36.0-rc2). A `Float` is
a bit pattern; `unpack` reads it as a sign, a significand and an exponent; each operation computes
its exact result, rounds it once with a round bit and a sticky bit, and `pack`s it. `a + b` on
`Float` is defined as that model's addition, and a compiled program runs C's `+` in its place. This
file proves the model's arithmetic is `rn`:

* `roundWithAccuracy_spec`: core's rounding step returns `rn` of the exact value it is handed, in
  canonical form, whenever its input keeps at least binary64's 53 bits. The invariant is `Rep`: an
  extended significand represents a value when the significand is the value's floor and the round
  and sticky bits place the value against the midpoint. A right shift halves the represented
  value, and core's ties-to-even choice is `rne` of it.
* `unpack_pack`, `packable_unpack`: `pack` and `unpack` are inverse on canonical forms below
  `2^1024`, and every finite bit pattern unpacks to one.
* `val_add`, `val_mul`, `val_div`: for finite operands and a result below `2^1024`, Lean's `Float`
  `+`, `*` and `/` (by a nonzero divisor) return `rn` of the exact result. Division needs core's
  exponent estimate to leave 53 bits of quotient (`divCore_enough`), which it does for a canonical
  dividend.
* `val_toFloat`: `k.toFloat` is exact below `2^53`.
* `compare_eq`, `beq_eq_decide`, `le_iff_val_le`: on finite floats core's comparison compares
  values, so `==` and `≤` are exact.

So `Palace/Roundoff.lean`'s two claims hold of Lean's own `Float`: CND-6 as the code compares,
`k.toFloat / n.toFloat == 1` exactly when `k = n` and the quotient is `≤ 1`
(`toFloat_div_beq_one`, `toFloat_div_le_one`), and LAP-1 (`SumTree.val_evalF_agreement`). What
stays trusted is that the compiled C operators agree with the logical model; the attacks in
`PalaceTest/FloatModel.lean` test that on this machine.
-/

@[expose] public section

open Float.Model (UnpackedFloat Format totalExponent)

open Float.Model.UnpackedFloat (ExtendedMantissa Accuracy Sign)

namespace Palace.Binary64

variable {K : Type*} [Field K] [LinearOrder K] [IsStrictOrderedRing K] [FloorRing K]

section Rep

/-- An extended mantissa represents `y ≥ 0` when its mantissa is `⌊y⌋`, its round bit says
whether `y` reaches the midpoint `⌊y⌋ + ½`, and its sticky bit whether `y` is neither `⌊y⌋` nor
the midpoint. -/
structure Rep (em : ExtendedMantissa) (y : K) : Prop where
  le : (em.mantissa : K) ≤ y
  lt : y < em.mantissa + 1
  round : em.roundBit = decide ((em.mantissa : K) + 1 / 2 ≤ y)
  sticky : em.stickyBit = decide (y ≠ em.mantissa ∧ y ≠ em.mantissa + 1 / 2)

/-- The round and sticky bits are both clear exactly when the value is the mantissa itself. -/
theorem Rep.round_or_sticky {em : ExtendedMantissa} {y : K} (h : Rep em y) :
    (em.roundBit || em.stickyBit) = decide (y ≠ em.mantissa) := by
  have hle := h.le
  rw [h.round, h.sticky, ← Bool.decide_or]
  refine decide_eq_decide.2 ⟨?_, fun h1 ↦ ?_⟩
  · rintro (h1 | ⟨h1, -⟩)
    · intro h2; rw [h2] at h1; linarith
    · exact h1
  · by_cases h2 : y = em.mantissa + 1 / 2
    · exact Or.inl h2.ge
    · exact Or.inr ⟨h1, h2⟩

/-- Shifting right one bit halves the represented value. -/
theorem Rep.shiftRightOne {em : ExtendedMantissa} {y : K} (h : Rep em y) :
    Rep em.shiftRightOne (y / 2) := by
  have hor := h.round_or_sticky
  obtain ⟨hle, hlt, -, -⟩ := h
  obtain ⟨m, rb, sb⟩ := em
  dsimp only at hle hlt hor
  change Rep ⟨m / 2, m % 2 != 0, rb || sb⟩ (y / 2)
  have hm : (m : K) = 2 * ((m / 2 : ℕ) : K) + ((m % 2 : ℕ) : K) := by
    exact_mod_cast (Nat.div_add_mod m 2).symm
  refine ⟨?_, ?_, ?_, ?_⟩ <;> dsimp only
  · rcases Nat.mod_two_eq_zero_or_one m with hb | hb <;> rw [hb] at hm <;> push_cast at hm <;>
      linarith
  · rcases Nat.mod_two_eq_zero_or_one m with hb | hb <;> rw [hb] at hm <;> push_cast at hm <;>
      linarith
  · rcases Nat.mod_two_eq_zero_or_one m with hb | hb <;> rw [hb] at hm <;> push_cast at hm
    · rw [hb]
      exact (decide_eq_false fun h' ↦ by linarith).symm
    · rw [hb]
      exact (decide_eq_true (by linarith)).symm
  · rw [hor]
    refine decide_eq_decide.2 ?_
    rcases Nat.mod_two_eq_zero_or_one m with hb | hb <;> rw [hb] at hm <;> push_cast at hm
    · exact ⟨fun h1 ↦ ⟨fun h2 ↦ h1 (by linarith), fun h2 ↦ by linarith⟩,
        fun ⟨h1, _⟩ h2 ↦ h1 (by linarith)⟩
    · exact ⟨fun h1 ↦ ⟨fun h2 ↦ by linarith, fun h2 ↦ h1 (by linarith)⟩,
        fun ⟨_, h2⟩ h1 ↦ h2 (by linarith)⟩

/-- Shifting right `n` bits divides the represented value by `2^n`. -/
theorem Rep.shiftRight {em : ExtendedMantissa} {y : K} (h : Rep em y) (n : ℕ) :
    Rep (em >>> n) (y / 2 ^ n) := by
  induction n with
  | zero => rw [pow_zero, div_one]; exact h
  | succ n ih =>
    have := ih.shiftRightOne
    rw [div_div, ← pow_succ] at this
    exact this

omit [Field K] [LinearOrder K] [IsStrictOrderedRing K] [FloorRing K] in
@[simp] theorem ofMantissaAndAccuracy_mantissa (m : ℕ) (acc : Accuracy) :
    (ExtendedMantissa.ofMantissaAndAccuracy m acc).mantissa = m := by
  cases acc with
  | exact => rfl
  | inexact o => cases o <;> rfl

omit [Field K] [LinearOrder K] [IsStrictOrderedRing K] [FloorRing K] in
@[simp] theorem shiftRight_zero (em : ExtendedMantissa) : em >>> 0 = em := rfl

/-- An exact mantissa represents itself. -/
theorem rep_exact (m : ℕ) : Rep (ExtendedMantissa.ofMantissaAndAccuracy m .exact) (m : K) := by
  change Rep ⟨m, false, false⟩ (m : K)
  refine ⟨le_rfl, by dsimp only; linarith, ?_, ?_⟩ <;> dsimp only
  · exact (decide_eq_false fun h ↦ by linarith).symm
  · exact (decide_eq_false fun h ↦ h.1 rfl).symm

/-- Rounding an extended mantissa is `rne` of the value it represents. -/
theorem Rep.roundedMantissa_eq {em : ExtendedMantissa} {y : K} (h : Rep em y) :
    (em.roundedMantissa : ℤ) = rne y := by
  obtain ⟨hle, hlt, hr, hs⟩ := h
  obtain ⟨m, rb, sb⟩ := em
  dsimp only at hle hlt hr hs
  have hfl : ⌊y⌋ = m := Int.floor_eq_iff.2 ⟨by exact_mod_cast hle, by exact_mod_cast hlt⟩
  have hfr : Int.fract y = y - m := by rw [fract_eq, hfl, Int.cast_natCast]
  unfold rne
  rw [hfr, hfl]
  cases rb <;> cases sb
  · -- exact
    have h1 := decide_eq_false_iff_not.1 hr.symm
    have h2 := decide_eq_false_iff_not.1 hs.symm
    have hy : y = m := by by_contra h; exact h2 ⟨h, fun h' ↦ h1 h'.ge⟩
    have : y - m < 1 / 2 := by rw [hy]; norm_num
    simp only [this, ↓reduceIte]; rfl
  · -- below the midpoint
    have h1 := decide_eq_false_iff_not.1 hr.symm
    have : y - m < 1 / 2 := by linarith [not_le.1 h1]
    simp only [this, ↓reduceIte]; rfl
  · -- at the midpoint, ties to even
    have h1 := decide_eq_true_iff.1 hr.symm
    have h2 := decide_eq_false_iff_not.1 hs.symm
    have hy : y = m + 1 / 2 := by
      by_contra h; exact h2 ⟨fun h' ↦ by rw [h'] at h1; linarith, h⟩
    have ha : ¬ y - m < 1 / 2 := by rw [hy]; norm_num
    have hb : ¬ 1 / 2 < y - m := by rw [hy]; norm_num
    simp only [ha, hb, ↓reduceIte]
    change ((m + m % 2 : ℕ) : ℤ) = _
    rcases Nat.mod_two_eq_zero_or_one m with hm | hm
    · have : (m : ℤ) % 2 = 0 := by omega
      simp [hm, this]
    · have : ¬ (m : ℤ) % 2 = 0 := by omega
      simp [hm, this]
  · -- past the midpoint
    have h1 := decide_eq_true_iff.1 hr.symm
    have h2 := decide_eq_true_iff.1 hs.symm
    have ha : ¬ y - m < 1 / 2 := by linarith
    have hb : 1 / 2 < y - m := by
      rcases h1.lt_or_eq with h | h
      · linarith
      · exact absurd h.symm h2.2
    simp only [ha, hb, ↓reduceIte]
    change ((m + 1 : ℕ) : ℤ) = _
    push_cast; rfl

end Rep

section Round

/-- `(m, e)` is binary64's canonical form of a nonzero finite number: normal, with a 53-bit
significand, or subnormal, at the least exponent. -/
def Canonical (m : ℕ) (e : ℤ) : Prop :=
  (2 ^ 52 ≤ m ∧ m < 2 ^ 53 ∧ -1074 ≤ e) ∨ (0 < m ∧ m < 2 ^ 52 ∧ e = -1074)

/-- An unpacked float is a zero, or finite in canonical form. -/
def Canon : UnpackedFloat → Prop
  | .zero _ => True
  | .finite _ m e _ => Canonical m e
  | _ => False

theorem targetExponent_eq (x : ℤ) :
    Format.binary64.targetExponent x = max (x - 53) (-1074) := by
  simp only [Format.targetExponent, Format.mantissaBits, Format.minExponent]
  norm_num

omit [FloorRing K] in
/-- `2^⌊log₂ m⌋ ≤ m`, as a power with an integer exponent. -/
theorem two_zpow_log2_le {m : ℕ} (hm : m ≠ 0) : (2 : K) ^ (m.log2 : ℤ) ≤ m := by
  rw [zpow_natCast]; exact_mod_cast Nat.log2_self_le hm

theorem totalExponent_eq (m : ℕ) (e : ℤ) : totalExponent m e = m.log2 + 1 + e := rfl

theorem shiftToTargetExponent_eq (m : ℕ) (e : ℤ) (acc : Accuracy) :
    UnpackedFloat.shiftToTargetExponent .binary64 m e acc =
      (ExtendedMantissa.ofMantissaAndAccuracy m acc >>>
        (max ((m.log2 : ℤ) + 1 + e - 53) (-1074) - e).toNat,
        e + (max ((m.log2 : ℤ) + 1 + e - 53) (-1074) - e).toNat) := by
  simp only [UnpackedFloat.shiftToTargetExponent, UnpackedFloat.shiftToExponent,
    targetExponent_eq, totalExponent_eq]

/-- **The bridge** The exact value `y · 2^e`, with `y ≥ 0` represented by `(m, acc)`, rounds to
`rn (y · 2^e)` in canonical form, provided `e` keeps at least the bits binary64 keeps: `e` at most
the target exponent. -/
theorem roundWithAccuracy_spec {s : Sign} {m : ℕ} {e : ℤ} {acc : Accuracy} {y : K}
    (hrep : Rep (ExtendedMantissa.ofMantissaAndAccuracy m acc) y)
    (he : e ≤ Format.binary64.targetExponent (totalExponent m e)) :
    value (UnpackedFloat.roundWithAccuracy .binary64 s m e acc) = sgn s * rn (y * 2 ^ e) ∧
      Canon (UnpackedFloat.roundWithAccuracy .binary64 s m e acc) := by
  rw [targetExponent_eq, totalExponent_eq] at he
  set t := max ((m.log2 : ℤ) + 1 + e - 53) (-1074) with ht
  have ht1 : (m.log2 : ℤ) + 1 + e - 53 ≤ t := le_max_left _ _
  have ht2 : -1074 ≤ t := le_max_right _ _
  obtain ⟨k, hk⟩ : ∃ k : ℕ, t - e = k := ⟨(t - e).toNat, by omega⟩
  have hy0 : 0 ≤ y := le_trans (Nat.cast_nonneg _) hrep.le
  set X := y * 2 ^ e with hX
  have hX0 : 0 ≤ X := by positivity
  -- the first shift, to the target exponent
  have hrep1 : Rep (ExtendedMantissa.ofMantissaAndAccuracy m acc >>> k) (X / 2 ^ t) := by
    have := hrep.shiftRight k
    convert this using 1
    rw [hX, show t = e + k by omega, zpow_add₀ two_ne_zero, zpow_natCast]
    field_simp
  set r := (ExtendedMantissa.ofMantissaAndAccuracy m acc >>> k).roundedMantissa with hr
  have hrne : (r : ℤ) = rne (X / 2 ^ t) := hrep1.roundedMantissa_eq
  -- `X` lies below the top of its binade
  have hXlt : X < 2 ^ ((m.log2 : ℤ) + 1 + e) := by
    have h2 : (m : K) + 1 ≤ 2 ^ ((m.log2 : ℤ) + 1) := by
      have : ((m + 1 : ℕ) : K) ≤ ((2 ^ (m.log2 + 1) : ℕ) : K) := by
        exact_mod_cast Nat.lt_log2_self
      push_cast at this
      rw [show ((m.log2 : ℤ) + 1) = ((m.log2 + 1 : ℕ) : ℤ) by push_cast; ring, zpow_natCast]
      exact this
    have hlt : y < m + 1 := by simpa using hrep.lt
    rw [hX, zpow_add₀ two_ne_zero]
    calc y * 2 ^ e < (m + 1) * 2 ^ e := by gcongr
      _ ≤ 2 ^ ((m.log2 : ℤ) + 1) * 2 ^ e := by gcongr
  -- so the rounded significand has at most 54 bits: `r ≤ 2^53`
  have hr53 : r ≤ 2 ^ 53 := by
    have : X / 2 ^ t ≤ ((2 ^ 53 : ℤ) : K) := by
      rw [div_le_iff₀ (zpow_pos two_pos _)]
      calc X ≤ 2 ^ ((m.log2 : ℤ) + 1 + e) := hXlt.le
        _ ≤ 2 ^ (53 + t) := zpow_le_zpow_right₀ one_le_two (by omega)
        _ = ((2 ^ 53 : ℤ) : K) * 2 ^ t := by
          rw [zpow_add₀ two_ne_zero]; norm_num
    have := rne_le_of_le this
    omega
  -- `t` is `X`'s ulp exponent, so `r · 2^t = rn X`
  have hrn : (r : K) * 2 ^ t = rn X := by
    rcases hX0.eq_or_lt with hX0 | hXpos
    · rw [← hX0, rn_zero]
      have : (r : ℤ) = 0 := by rw [hrne, ← hX0, zero_div, rne_zero]
      have : r = 0 := by omega
      simp [this]
    have hc : cexp X = t := by
      rw [cexp, abs_of_pos hXpos]
      rcases Nat.eq_zero_or_pos m with hm | hm
      · -- `y < 1`, and `e ≤ t` forces the least exponent
        subst hm
        simp only [Nat.log2_zero, Nat.cast_zero, zero_add] at ht ht1 he hXlt
        have hte : t = -1074 := by rw [ht]; omega
        have : Int.log 2 X < 1 + e :=
          (Int.lt_zpow_iff_log_lt (b := 2) (by norm_num) hXpos).1 (by simpa using hXlt)
        rw [hte]; exact max_eq_right (by omega)
      · have hlog : Int.log 2 X = m.log2 + e := by
          refine log_eq ?_ (by rw [show (m.log2 : ℤ) + e + 1 = m.log2 + 1 + e by ring]; exact hXlt)
          rw [hX, zpow_add₀ two_ne_zero]
          exact mul_le_mul_of_nonneg_right
            ((two_zpow_log2_le (by omega)).trans (by simpa using hrep.le)) (zpow_pos two_pos e).le
        rw [hlog, ht]; congr 1; ring
    rw [rn, hc, ← hrne]; push_cast; rfl
  -- the second shift: at most one bit, when rounding carried into the next binade
  have hfirst : UnpackedFloat.shiftToTargetExponent .binary64 m e acc =
      (ExtendedMantissa.ofMantissaAndAccuracy m acc >>> k, t) := by
    rw [shiftToTargetExponent_eq, ← ht, show (t - e).toNat = k by omega, show e + k = t by omega]
  simp only [UnpackedFloat.roundWithAccuracy, hfirst, ← hr, shiftToTargetExponent_eq]
  rcases (show r < 2 ^ 53 ∨ r = 2 ^ 53 by omega) with hlt | heq
  · -- no carry: the significand is `r` at exponent `t`
    have hlog : (r.log2 : ℤ) + 1 + t - 53 ≤ t := by
      rcases Nat.eq_zero_or_pos r with h0 | h0
      · rw [h0, Nat.log2_zero]; push_cast; omega
      · have := (Nat.log2_lt (n := r) (k := 53) (by omega)).2 hlt; omega
    have hk0 : (max ((r.log2 : ℤ) + 1 + t - 53) (-1074) - t).toNat = 0 := by omega
    simp only [hk0, Nat.cast_zero, add_zero, shiftRight_zero, ofMantissaAndAccuracy_mantissa]
    change value (if h : r = 0 then _ else _) = _ ∧ Canon (if h : r = 0 then _ else _)
    by_cases h0 : r = 0
    · simp only [h0, ↓reduceDIte]
      refine ⟨?_, trivial⟩
      rw [← hrn, h0]; simp [value]
    · simp only [h0, ↓reduceDIte]
      refine ⟨by rw [value, hrn], ?_⟩
      change Canonical r t
      rcases (show 2 ^ 52 ≤ r ∨ r < 2 ^ 52 by omega) with h52 | h52
      · exact Or.inl ⟨h52, hlt, ht2⟩
      · refine Or.inr ⟨by omega, h52, ?_⟩
        -- below `2^52` the target exponent must be the least one
        by_contra hne
        have htn : t = (m.log2 : ℤ) + 1 + e - 53 := by rw [ht] at hne ⊢; omega
        rcases Nat.eq_zero_or_pos m with hm | hm
        · subst hm; simp only [Nat.log2_zero, Nat.cast_zero, zero_add] at htn he; omega
        have hXge : (2 : K) ^ (t + 52) ≤ X := by
          rw [hX, htn, show (m.log2 : ℤ) + 1 + e - 53 + 52 = m.log2 + e by ring,
            zpow_add₀ two_ne_zero]
          exact mul_le_mul_of_nonneg_right
            ((two_zpow_log2_le (by omega)).trans (by simpa using hrep.le)) (zpow_pos two_pos e).le
        have : ((2 ^ 52 : ℤ) : K) ≤ X / 2 ^ t := by
          rw [le_div_iff₀ (zpow_pos two_pos _)]
          calc ((2 ^ 52 : ℤ) : K) * 2 ^ t = 2 ^ (t + 52) := by
                rw [zpow_add₀ two_ne_zero]; push_cast; ring
            _ ≤ X := hXge
        have := le_rne_of_le this
        omega
  · -- carry: `r = 2^53` shifts once more, to `2^52` at exponent `t + 1`
    have hlog : r.log2 = 53 := by rw [heq]; exact Nat.log2_two_pow
    have hk1 : (max ((r.log2 : ℤ) + 1 + t - 53) (-1074) - t).toNat = 1 := by rw [hlog]; omega
    simp only [hk1]
    have hM : (ExtendedMantissa.ofMantissaAndAccuracy r .exact >>> 1).mantissa = 2 ^ 52 := by
      change r / 2 = 2 ^ 52
      omega
    have hM0 : ¬ (ExtendedMantissa.ofMantissaAndAccuracy r .exact >>> 1).mantissa = 0 := by
      rw [hM]; norm_num
    simp only [hM0, ↓reduceDIte]
    refine ⟨?_, ?_⟩
    · rw [value, hM, ← hrn, heq]
      push_cast
      rw [zpow_add_one₀ two_ne_zero]; ring
    · change Canonical _ _
      rw [hM]
      exact Or.inl ⟨le_rfl, by norm_num, by omega⟩

end Round

section Pack

/-- An unpacked float `pack` stores and `unpack` gives back: a zero, or finite in canonical form
below the overflow threshold `2^1024`. -/
def Packable : UnpackedFloat → Prop
  | .zero _ => True
  | .finite _ m e _ => Canonical m e ∧ e < 972
  | _ => False

theorem Sign.ofBitVec_toBitVec (s : Sign) : Sign.ofBitVec s.toBitVec = s := by
  cases s <;> rfl

@[simp] theorem unpackSign_packComponents {sign : Sign} {exponent : BitVec 11}
    {mantissa : BitVec 52} :
    UnpackedFloat.unpackSign (UnpackedFloat.packComponents .binary64 sign exponent mantissa) =
      sign.toBitVec := by
  rw [← BitVec.toNat_inj]
  have he := exponent.isLt
  have hm := mantissa.isLt
  have hs := sign.toBitVec.isLt
  simp only [UnpackedFloat.unpackSign, UnpackedFloat.packComponents, BitVec.extractLsb'_toNat,
    BitVec.toNat_append_eq_mul_add, Nat.shiftRight_eq_div_pow] at he hm hs ⊢
  norm_num at he hm hs ⊢
  omega

theorem exponentBias_eq : (Format.binary64.exponentBias : ℤ) = 1023 := by
  simp [Format.exponentBias]

theorem mantissaBitsWithoutImplicit_eq :
    (Format.binary64.mantissaBitsWithoutImplicit : ℤ) = 52 := rfl

/-- `unpack` inverts `pack` on what `pack` stores. -/
theorem unpack_pack {f : UnpackedFloat} (hf : Packable f) :
    UnpackedFloat.unpack .binary64 (UnpackedFloat.pack .binary64 f) = f := by
  match f, hf with
  | .zero s, _ =>
    simp [UnpackedFloat.pack, UnpackedFloat.packedZero, UnpackedFloat.unpack,
      Sign.ofBitVec_toBitVec]
  | .finite s m e hm, ⟨hc, he⟩ =>
    have he0 : -1074 ≤ e := by rcases hc with ⟨-, -, h⟩ | ⟨-, -, h⟩ <;> omega
    obtain ⟨b, hb⟩ : ∃ b : ℕ, e + 1075 = b := ⟨(e + 1075).toNat, by omega⟩
    have hbias : (e + (Format.binary64.exponentBias : ℤ) +
        (Format.binary64.mantissaBitsWithoutImplicit : ℤ)).toNat = b := by
      rw [exponentBias_eq, mantissaBitsWithoutImplicit_eq]; omega
    have hx : ¬ 2 ^ Format.binary64.exponentBits ≤ b + 1 := by change ¬ 2 ^ 11 ≤ b + 1; omega
    rcases hc with ⟨h1, h2, h3⟩ | ⟨h1, h2, h3⟩
    · -- normal: biased exponent `e + 1075` in `[1, 2046]`, the implicit bit dropped
      have hlog : m.log2 = 52 := (Nat.log2_eq_iff (by omega)).2 ⟨h1, h2⟩
      have hn : m.log2 + 1 = Format.binary64.mantissaBits := by rw [hlog]; rfl
      have hpack : UnpackedFloat.pack .binary64 (.finite s m e hm) =
          UnpackedFloat.packComponents .binary64 s (BitVec.ofNat 11 b) (BitVec.ofNat 52 m) := by
        simp only [UnpackedFloat.pack, hbias, hx, hn, ↓reduceIte]
      have hne1 : ¬ BitVec.ofNat 11 b = -1#11 := by
        rw [← BitVec.toNat_inj, BitVec.toNat_ofNat, BitVec.neg_one_eq_allOnes,
          BitVec.toNat_allOnes]
        omega
      have hne0 : ¬ BitVec.ofNat 11 b = 0#11 := by
        rw [← BitVec.toNat_inj, BitVec.toNat_ofNat, BitVec.toNat_ofNat]; omega
      rw [hpack]
      unfold UnpackedFloat.unpack
      simp only [UnpackedFloat.unpackMantissa_packComponents,
        UnpackedFloat.unpackExponent_packComponents, unpackSign_packComponents,
        Sign.ofBitVec_toBitVec, hne1, hne0, ↓reduceIte, UnpackedFloat.finite.injEq, true_and]
      constructor
      · rw [BitVec.toNat_append_eq_mul_add, BitVec.toNat_ofNat, BitVec.toNat_ofNat]; omega
      · rw [BitVec.toNat_ofNat, exponentBias_eq, mantissaBitsWithoutImplicit_eq]; omega
    · -- subnormal: exponent field `0`, the significand stored as is
      have hlog : m.log2 < 52 := (Nat.log2_lt (by omega)).2 h2
      have hn : ¬ m.log2 + 1 = Format.binary64.mantissaBits := by
        change ¬ m.log2 + 1 = 1 + 52; omega
      have hpack : UnpackedFloat.pack .binary64 (.finite s m e hm) =
          UnpackedFloat.packComponents .binary64 s 0#11 (BitVec.ofNat 52 m) := by
        simp only [UnpackedFloat.pack, hbias, hx, hn, ↓reduceIte]
      have hm0 : ¬ BitVec.ofNat 52 m = 0#52 := by
        rw [← BitVec.toNat_inj, BitVec.toNat_ofNat, BitVec.toNat_ofNat]; omega
      have hz : ¬ (0#11 : BitVec 11) = -1#11 := by decide
      rw [hpack]
      unfold UnpackedFloat.unpack
      simp only [UnpackedFloat.unpackMantissa_packComponents,
        UnpackedFloat.unpackExponent_packComponents, unpackSign_packComponents,
        Sign.ofBitVec_toBitVec, hz, hm0, ↓reduceIte, ↓reduceDIte, UnpackedFloat.finite.injEq,
        true_and]
      constructor
      · rw [BitVec.toNat_ofNat]; omega
      · rw [exponentBias_eq, mantissaBitsWithoutImplicit_eq]; simp; omega

/-- What `unpack` reads off finite bits is packable. -/
theorem packable_unpack (b : BitVec 64) (h : (UnpackedFloat.unpack .binary64 b).isFinite) :
    Packable (UnpackedFloat.unpack .binary64 b) := by
  generalize hE : UnpackedFloat.unpackExponent (spec := .binary64) b = E
  generalize hM : UnpackedFloat.unpackMantissa (spec := .binary64) b = M
  have hEl : E.toNat < 2048 := E.isLt
  have hMl : M.toNat < 2 ^ 52 := M.isLt
  revert h
  unfold UnpackedFloat.unpack
  simp only [hE, hM]
  by_cases h1 : E = -1#11
  · simp only [h1, ↓reduceIte]
    split <;> simp [UnpackedFloat.isFinite]
  have hE1 : E.toNat < 2047 := by
    rw [← BitVec.toNat_inj, BitVec.neg_one_eq_allOnes, BitVec.toNat_allOnes] at h1
    simp only at h1; omega
  by_cases h2 : E = 0#11
  · by_cases h3 : M = 0#52
    · simp only [h2, h3, ↓reduceIte, ↓reduceDIte]; intro; trivial
    · simp only [h2, h3, ↓reduceIte, ↓reduceDIte]
      intro
      have hM0 : M.toNat ≠ 0 := fun h ↦ h3 (BitVec.eq_of_toNat_eq (by simpa using h))
      refine ⟨Or.inr ⟨by omega, hMl, ?_⟩, ?_⟩ <;>
        rw [exponentBias_eq, mantissaBitsWithoutImplicit_eq] <;> subst h2 <;> simp
  · simp only [h1, h2, ↓reduceIte]
    intro
    have hE0 : 1 ≤ E.toNat := by
      rw [← BitVec.toNat_inj, BitVec.toNat_ofNat] at h2; simp only at h2; omega
    refine ⟨Or.inl ⟨?_, ?_, ?_⟩, ?_⟩
    · rw [BitVec.toNat_append_eq_mul_add]; simp
    · rw [BitVec.toNat_append_eq_mul_add]; simp only [BitVec.toNat_ofNat]; omega
    · rw [exponentBias_eq, mantissaBitsWithoutImplicit_eq]; omega
    · rw [exponentBias_eq, mantissaBitsWithoutImplicit_eq]; omega

end Pack

section Ops

omit [LinearOrder K] [IsStrictOrderedRing K] [FloorRing K] in
theorem sgn_apply (s : Sign) (n : ℤ) : ((s.apply n : ℤ) : K) = sgn s * n := by
  cases s <;> simp [Sign.apply, sgn]

omit [LinearOrder K] [IsStrictOrderedRing K] [FloorRing K] in
theorem sgn_mul (s₁ s₂ : Sign) : sgn (s₁ * s₂) = (sgn s₁ * sgn s₂ : K) := by
  cases s₁ <;> cases s₂
  · change sgn .positive = _; simp [sgn]
  · change sgn .negative = _; simp [sgn]
  · change sgn .negative = _; simp [sgn]
  · change sgn .positive = _; simp [sgn]

omit [LinearOrder K] [IsStrictOrderedRing K] [FloorRing K] in
theorem sgn_div (s₁ s₂ : Sign) : sgn (s₁ / s₂) = (sgn s₁ * sgn s₂ : K) := by
  cases s₁ <;> cases s₂
  · change sgn .positive = _; simp [sgn]
  · change sgn .negative = _; simp [sgn]
  · change sgn .negative = _; simp [sgn]
  · change sgn .positive = _; simp [sgn]

/-- `±rn x = rn (±x)`. -/
theorem sgn_mul_rn (s : Sign) (x : K) : sgn s * rn x = rn (sgn s * x) := by
  cases s <;> simp [sgn, rn_neg]

omit [LinearOrder K] [IsStrictOrderedRing K] [FloorRing K] in
/-- A packable float's value is a binary64 number. -/
theorem isFloat_value {f : UnpackedFloat} (hf : Packable f) : IsFloat (value f : K) := by
  match f, hf with
  | .zero _, _ => exact ⟨0, -1074, by norm_num, le_rfl, by simp [value]⟩
  | .finite s m e _, ⟨hc, _⟩ =>
    have hm : m < 2 ^ 53 := by rcases hc with ⟨-, h, -⟩ | ⟨-, h, -⟩ <;> omega
    have he : -1074 ≤ e := by rcases hc with ⟨-, -, h⟩ | ⟨-, -, h⟩ <;> omega
    refine ⟨s.apply m, e, ?_, he, ?_⟩
    · cases s <;> simp only [Sign.apply, abs_neg, Nat.abs_cast] <;> exact_mod_cast hm
    · rw [sgn_apply]; simp [value]; ring

/-- A canonical float below `2^1024` is packable. -/
theorem packable_of_canon {f : UnpackedFloat} (hc : Canon f) (hv : |(value f : K)| < 2 ^ 1024) :
    Packable f := by
  match f, hc with
  | .zero _, _ => trivial
  | .finite s m e hm, hc =>
    refine ⟨hc, ?_⟩
    rcases hc with ⟨h1, -, -⟩ | ⟨-, -, h⟩
    · by_contra he
      have : (2 : K) ^ (1024 : ℤ) ≤ |value (.finite s m e hm)| := by
        have hs : |(sgn s : K)| = 1 := by cases s <;> simp [sgn]
        rw [value, abs_mul, hs, one_mul, abs_of_nonneg (by positivity)]
        calc (2 : K) ^ (1024 : ℤ) = 2 ^ (52 : ℤ) * 2 ^ (972 : ℤ) := by
              rw [← zpow_add₀ two_ne_zero]; norm_num
          _ ≤ m * 2 ^ e := by
            gcongr
            · exact_mod_cast (show ((2 ^ 52 : ℕ) : K) ≤ m by exact_mod_cast h1)
            · exact one_le_two
            · omega
      rw [show (2 : K) ^ 1024 = 2 ^ (1024 : ℤ) by norm_num] at hv
      linarith
    · omega

theorem log2_mul_two_pow {m : ℕ} (hm : 0 < m) (k : ℕ) : (m * 2 ^ k).log2 = m.log2 + k := by
  rw [Nat.log2_eq_iff (by positivity)]
  have h1 := Nat.log2_self_le (n := m) (by omega)
  have h2 := Nat.lt_log2_self (n := m)
  constructor
  · rw [pow_add]; exact Nat.mul_le_mul_right _ h1
  · rw [show m.log2 + k + 1 = m.log2 + 1 + k by ring, pow_add]
    exact Nat.mul_lt_mul_of_pos_right h2 (by positivity)

/-- `round` gives `rn` of `m · 2^e` with the sign applied, in canonical form. -/
theorem round_spec (s : Sign) {m : ℕ} (hm : 0 < m) (e : ℤ) :
    value (UnpackedFloat.round .binary64 s m e) = sgn s * rn ((m : K) * 2 ^ e) ∧
      Canon (UnpackedFloat.round .binary64 s m e) := by
  set t := Format.binary64.targetExponent (totalExponent m e) with ht
  obtain ⟨k, hk⟩ : ∃ k : ℕ, (e - t).toNat = k := ⟨_, rfl⟩
  have hround : UnpackedFloat.round .binary64 s m e =
      UnpackedFloat.roundWithAccuracy .binary64 s (m * 2 ^ k) (e - k) .exact := by
    simp only [UnpackedFloat.round, UnpackedFloat.decreaseExponent, ← ht, hk, Nat.shiftLeft_eq]
  have htot : totalExponent (m * 2 ^ k) (e - k) = totalExponent m e := by
    rw [totalExponent_eq, totalExponent_eq, log2_mul_two_pow hm]; push_cast; ring
  have hval : ((m * 2 ^ k : ℕ) : K) * 2 ^ (e - k) = m * 2 ^ e := by
    push_cast
    rw [zpow_sub₀ two_ne_zero, zpow_natCast]
    field_simp
  rw [hround]
  have := roundWithAccuracy_spec (s := s) (e := e - k) (rep_exact (K := K) (m * 2 ^ k))
    (by rw [htot, ← ht]; omega)
  rwa [hval] at this

/-- `normalize` gives `rn` of `M · 2^e`, in canonical form. -/
theorem normalize_spec (M e : ℤ) (zs : Sign) :
    value (UnpackedFloat.normalize .binary64 M e zs) = rn ((M : K) * 2 ^ e) ∧
      Canon (UnpackedFloat.normalize .binary64 M e zs) := by
  rcases lt_trichotomy M 0 with h | h | h
  · simp only [UnpackedFloat.normalize, Int.compare_eq_lt.mpr h]
    have := round_spec (K := K) .negative (m := (-M).toNat) (by omega) e
    refine ⟨?_, this.2⟩
    rw [this.1, sgn_mul_rn]
    congr 1
    simp only [sgn]
    rw [show (((-M).toNat : ℕ) : K) = -M by
      rw [show (((-M).toNat : ℕ) : K) = (((-M).toNat : ℤ) : K) by push_cast; rfl,
        Int.toNat_of_nonneg (by omega)]; push_cast; ring]
    ring
  · subst h
    simp only [UnpackedFloat.normalize, Int.compare_eq_eq.mpr rfl]
    exact ⟨by simp [value], trivial⟩
  · simp only [UnpackedFloat.normalize, Int.compare_eq_gt.mpr h]
    have := round_spec (K := K) .positive (m := M.toNat) (by omega) e
    refine ⟨?_, this.2⟩
    rw [this.1]
    simp only [sgn, one_mul]
    rw [show ((M.toNat : ℕ) : K) = M by
      rw [show ((M.toNat : ℕ) : K) = ((M.toNat : ℤ) : K) by push_cast; rfl,
        Int.toNat_of_nonneg (by omega)]]

end Ops

section Arith

omit [FloorRing K] in
theorem two_pow_toNat_mul {a b : ℤ} (h : b ≤ a) : (2 : K) ^ (a - b).toNat * 2 ^ b = 2 ^ a := by
  rw [← zpow_natCast, ← zpow_add₀ two_ne_zero, Int.toNat_of_nonneg (by omega)]; ring_nf

/-- `add` gives `rn` of the exact sum, in canonical form. -/
theorem add_spec {x y : UnpackedFloat} (hx : Packable x) (hy : Packable y) :
    value (UnpackedFloat.add .binary64 x y) = rn ((value x : K) + value y) ∧
      Canon (UnpackedFloat.add .binary64 x y) := by
  match x, y, hx, hy with
  | .zero s₁, .zero s₂, _, _ =>
    simp only [UnpackedFloat.add]
    split <;> exact ⟨by simp [value], trivial⟩
  | .zero s₁, .finite s₂ m₂ e₂ h₂, _, hy =>
    simp only [UnpackedFloat.add]
    refine ⟨?_, hy.1⟩
    rw [show value (.zero s₁) = (0 : K) from rfl, zero_add, rn_isFloat (isFloat_value hy)]
  | .finite s₁ m₁ e₁ h₁, .zero s₂, hx, _ =>
    simp only [UnpackedFloat.add]
    refine ⟨?_, hx.1⟩
    rw [show value (.zero s₂) = (0 : K) from rfl, add_zero, rn_isFloat (isFloat_value hx)]
  | .finite s₁ m₁ e₁ h₁, .finite s₂ m₂ e₂ h₂, _, _ =>
    simp only [UnpackedFloat.add, UnpackedFloat.decreaseExponent, Nat.shiftLeft_eq]
    refine ⟨?_, (normalize_spec (K := K) _ _ _).2⟩
    rw [(normalize_spec (K := K) _ _ _).1]
    congr 1
    simp only [value, Int.cast_add, sgn_apply]
    push_cast
    rw [add_mul, mul_assoc, mul_assoc, mul_assoc, mul_assoc,
      two_pow_toNat_mul (min_le_left e₁ e₂), two_pow_toNat_mul (min_le_right e₁ e₂)]

/-- `mul` gives `rn` of the exact product, in canonical form. -/
theorem mul_spec {x y : UnpackedFloat} (hx : Packable x) (hy : Packable y) :
    value (UnpackedFloat.mul .binary64 x y) = rn ((value x : K) * value y) ∧
      Canon (UnpackedFloat.mul .binary64 x y) := by
  match x, y, hx, hy with
  | .zero s₁, .zero s₂, _, _ => exact ⟨by simp [UnpackedFloat.mul, value], trivial⟩
  | .zero s₁, .finite s₂ m₂ e₂ h₂, _, _ => exact ⟨by simp [UnpackedFloat.mul, value], trivial⟩
  | .finite s₁ m₁ e₁ h₁, .zero s₂, _, _ => exact ⟨by simp [UnpackedFloat.mul, value], trivial⟩
  | .finite s₁ m₁ e₁ h₁, .finite s₂ m₂ e₂ h₂, ⟨hc₁, _⟩, ⟨hc₂, _⟩ =>
    simp only [UnpackedFloat.mul]
    have he : e₁ + e₂ ≤ Format.binary64.targetExponent (totalExponent (m₁ * m₂) (e₁ + e₂)) := by
      rw [targetExponent_eq, totalExponent_eq]
      by_cases hbig : 2 ^ 52 ≤ m₁ * m₂
      · have := (Nat.le_log2 (n := m₁ * m₂) (by positivity)).2 hbig
        exact le_max_of_le_left (by omega)
      · -- both subnormal
        have h1 : e₁ = -1074 := by
          rcases hc₁ with ⟨h, -, -⟩ | ⟨-, -, h⟩
          · exact absurd (h.trans (Nat.le_mul_of_pos_right _ h₂)) hbig
          · exact h
        have h2 : e₂ = -1074 := by
          rcases hc₂ with ⟨h, -, -⟩ | ⟨-, -, h⟩
          · exact absurd (h.trans (Nat.le_mul_of_pos_left _ h₁)) hbig
          · exact h
        exact le_max_of_le_right (by omega)
    obtain ⟨hv, hc⟩ := roundWithAccuracy_spec (s := s₁ * s₂) (rep_exact (K := K) (m₁ * m₂)) he
    refine ⟨?_, hc⟩
    rw [hv, sgn_mul_rn]
    congr 1
    simp only [value, sgn_mul]
    push_cast
    rw [zpow_add₀ two_ne_zero]; ring

end Arith

section LeanFloat

theorem packable_toModel {a : Float} (ha : a.isFinite) : Packable a.toModel.unpack :=
  packable_unpack _ ha

omit [LinearOrder K] [IsStrictOrderedRing K] [FloorRing K] in
theorem val_ofModel_pack {f : UnpackedFloat} (hf : Packable f) :
    val (K := K) (Float.ofModel (Float.Model.pack f)) = value f := by
  change value (UnpackedFloat.unpack .binary64 (UInt64.ofBitVec _).toBitVec) = _
  rw [UInt64.toBitVec_ofBitVec, unpack_pack hf]

theorem isFinite_ofModel_pack {f : UnpackedFloat} (hf : Packable f) :
    (Float.ofModel (Float.Model.pack f)).isFinite := by
  change (UnpackedFloat.unpack .binary64 (UInt64.ofBitVec _).toBitVec).isFinite
  rw [UInt64.toBitVec_ofBitVec, unpack_pack hf]
  match f, hf with
  | .zero _, _ => rfl
  | .finite .., _ => rfl

/-- **The bridge, `+`** Lean's `Float` addition is `rn` of the exact sum, below overflow. -/
theorem val_add {a b : Float} (ha : a.isFinite) (hb : b.isFinite)
    (hov : |rn (val a + val b : K)| < 2 ^ 1024) :
    val (a + b) = rn (val a + val b : K) ∧ (a + b).isFinite := by
  obtain ⟨hv, hc⟩ := add_spec (K := K) (packable_toModel ha) (packable_toModel hb)
  have hp := packable_of_canon hc (by rw [hv]; exact hov)
  exact ⟨(val_ofModel_pack hp).trans hv, isFinite_ofModel_pack hp⟩

/-- **The bridge, `*`** Lean's `Float` multiplication is `rn` of the exact product, below
overflow. -/
theorem val_mul {a b : Float} (ha : a.isFinite) (hb : b.isFinite)
    (hov : |rn (val a * val b : K)| < 2 ^ 1024) :
    val (a * b) = rn (val a * val b : K) ∧ (a * b).isFinite := by
  obtain ⟨hv, hc⟩ := mul_spec (K := K) (packable_toModel ha) (packable_toModel hb)
  have hp := packable_of_canon hc (by rw [hv]; exact hov)
  exact ⟨(val_ofModel_pack hp).trans hv, isFinite_ofModel_pack hp⟩

section Div

/-- `divCore`'s quotient and accuracy represent the exact quotient `M / d`. -/
theorem rep_div (M d : ℕ) (hd : 0 < d) :
    Rep (ExtendedMantissa.ofMantissaAndAccuracy (M / d)
      (UnpackedFloat.accuracyOfFraction (M % d) d)) ((M : K) / d) := by
  have hdK : (0 : K) < d := by exact_mod_cast hd
  have hsplit : (M : K) / d = ((M / d : ℕ) : K) + ((M % d : ℕ) : K) / d := by
    have h : ((d * (M / d) + M % d : ℕ) : K) = M := by exact_mod_cast Nat.div_add_mod M d
    push_cast at h
    field_simp
    linarith
  have hrd : M % d < d := Nat.mod_lt _ hd
  generalize M / d = q at hsplit ⊢
  generalize M % d = r at hsplit hrd ⊢
  rw [hsplit]
  have hrK : (r : K) / d < 1 := by rw [div_lt_one hdK]; exact_mod_cast hrd
  have hr0 : 0 ≤ (r : K) / d := by positivity
  have hhalf : (1 : K) / 2 ≤ r / d ↔ d ≤ 2 * r := by
    rw [le_div_iff₀ hdK]
    constructor
    · intro h; exact_mod_cast (show (d : K) ≤ 2 * r by linarith)
    · intro h; have : (d : K) ≤ 2 * r := by exact_mod_cast h
      linarith
  have hhalf' : (r : K) / d = 1 / 2 ↔ 2 * r = d := by
    rw [div_eq_iff hdK.ne']
    constructor
    · intro h; exact_mod_cast (show (2 * r : K) = d by linarith)
    · intro h; have : (2 * r : K) = d := by exact_mod_cast h
      linarith
  have hzero : (r : K) / d = 0 ↔ r = 0 := by
    rw [div_eq_zero_iff]; simp [hdK.ne']
  unfold UnpackedFloat.accuracyOfFraction
  by_cases h0 : r = 0
  · subst h0
    simp only [↓reduceIte, Nat.cast_zero, zero_div, add_zero]
    exact rep_exact q
  · simp only [h0, ↓reduceIte]
    have hne : (r : K) / d ≠ 0 := fun h ↦ h0 (hzero.1 h)
    rcases lt_trichotomy (2 * r) d with h | h | h
    · rw [Nat.compare_eq_lt.mpr h]
      change Rep ⟨q, false, true⟩ _
      refine ⟨le_add_of_nonneg_right hr0, by dsimp only; linarith, ?_, ?_⟩ <;> dsimp only
      · refine (decide_eq_false fun h' ↦ ?_).symm
        have := hhalf.1 (by linarith); omega
      · refine (decide_eq_true ⟨fun h' ↦ hne (by linarith), fun h' ↦ ?_⟩).symm
        have := hhalf'.1 (by linarith); omega
    · rw [Nat.compare_eq_eq.mpr h]
      change Rep ⟨q, true, false⟩ _
      refine ⟨le_add_of_nonneg_right hr0, by dsimp only; linarith, ?_, ?_⟩ <;> dsimp only
      · exact (decide_eq_true (by linarith [hhalf.2 h.ge])).symm
      · refine (decide_eq_false fun ⟨_, h2⟩ ↦ h2 ?_).symm
        rw [hhalf'.2 h]
    · rw [Nat.compare_eq_gt.mpr h]
      change Rep ⟨q, true, true⟩ _
      refine ⟨le_add_of_nonneg_right hr0, by dsimp only; linarith, ?_, ?_⟩ <;> dsimp only
      · exact (decide_eq_true (by linarith [hhalf.2 h.le])).symm
      · refine (decide_eq_true ⟨fun h' ↦ hne (by linarith), fun h' ↦ ?_⟩).symm
        have := hhalf'.1 (by linarith); omega

/-- `divCore` keeps the bits binary64 keeps: its exponent is at most the target exponent of its
quotient, for a dividend significand below `2^53`. -/
theorem divCore_enough {m₁ m₂ : ℕ} (hm₁ : m₁ < 2 ^ 53) (h₁ : 0 < m₁) (h₂ : 0 < m₂) (e₁ e₂ : ℤ) :
    min (e₁ - e₂) (Format.binary64.targetExponent (totalExponent m₁ e₁ - totalExponent m₂ e₂)) ≤
      Format.binary64.targetExponent (totalExponent
        (m₁ * 2 ^ (e₁ - e₂ - min (e₁ - e₂) (Format.binary64.targetExponent
          (totalExponent m₁ e₁ - totalExponent m₂ e₂))).toNat / m₂)
        (min (e₁ - e₂) (Format.binary64.targetExponent
          (totalExponent m₁ e₁ - totalExponent m₂ e₂)))) := by
  simp only [targetExponent_eq, totalExponent_eq]
  set a := m₁.log2
  set b := m₂.log2
  have ha : a ≤ 52 := by have := (Nat.log2_lt (n := m₁) (k := 53) (by omega)).2 hm₁; omega
  generalize hT : min (e₁ - e₂) (max ((a : ℤ) + 1 + e₁ - (b + 1 + e₂) - 53) (-1074)) = T
  by_cases hTl : T ≤ -1074
  · exact le_max_of_le_right hTl
  -- in the normal range: `T = a − b + e₁ − e₂ − 53`, and the quotient has 53 bits
  have hTe : T = (a : ℤ) - b + e₁ - e₂ - 53 := by
    have := not_le.1 hTl
    rw [← hT] at this ⊢; omega
  have hk : (e₁ - e₂ - T).toNat = 53 + b - a := by omega
  rw [hk]
  apply le_max_of_le_left
  have hq : 2 ^ 52 ≤ m₁ * 2 ^ (53 + b - a) / m₂ := by
    rw [Nat.le_div_iff_mul_le h₂]
    have h1 : m₂ < 2 ^ (b + 1) := Nat.lt_log2_self
    have h2 : 2 ^ a ≤ m₁ := Nat.log2_self_le (by omega)
    calc 2 ^ 52 * m₂ ≤ 2 ^ 52 * 2 ^ (b + 1) := Nat.mul_le_mul_left _ h1.le
      _ = 2 ^ a * 2 ^ (53 + b - a) := by rw [← pow_add, ← pow_add]; congr 1; omega
      _ ≤ m₁ * 2 ^ (53 + b - a) := Nat.mul_le_mul_right _ h2
  have := (Nat.le_log2 (n := m₁ * 2 ^ (53 + b - a) / m₂) (by omega)).2 hq
  omega

/-- `div` gives `rn` of the exact quotient, in canonical form, for a nonzero divisor. -/
theorem div_spec {x y : UnpackedFloat} (hx : Packable x) (hy : Packable y)
    (hy0 : (value y : K) ≠ 0) :
    value (UnpackedFloat.div .binary64 x y) = rn ((value x : K) / value y) ∧
      Canon (UnpackedFloat.div .binary64 x y) := by
  match x, y, hx, hy with
  | .zero _, .zero _, _, _ => exact absurd rfl hy0
  | .finite .., .zero _, _, _ => exact absurd rfl hy0
  | .zero s₁, .finite s₂ m₂ e₂ h₂, _, _ =>
    exact ⟨by simp [UnpackedFloat.div, value], trivial⟩
  | .finite s₁ m₁ e₁ h₁, .finite s₂ m₂ e₂ h₂, ⟨hc₁, _⟩, _ =>
    have hm₁ : m₁ < 2 ^ 53 := by rcases hc₁ with ⟨-, h, -⟩ | ⟨-, h, -⟩ <;> omega
    simp only [UnpackedFloat.div, UnpackedFloat.divCore, Nat.shiftLeft_eq]
    generalize hT : min (e₁ - e₂) (Format.binary64.targetExponent
      (totalExponent m₁ e₁ - totalExponent m₂ e₂)) = T
    have henough := divCore_enough hm₁ h₁ h₂ e₁ e₂
    rw [hT] at henough
    obtain ⟨hv, hc⟩ := roundWithAccuracy_spec (s := s₁ / s₂)
      (rep_div (K := K) (m₁ * 2 ^ (e₁ - e₂ - T).toNat) m₂ h₂) henough
    refine ⟨?_, hc⟩
    have hTle : T ≤ e₁ - e₂ := by rw [← hT]; exact min_le_left _ _
    rw [hv, sgn_mul_rn]
    congr 1
    simp only [value, sgn_div]
    push_cast
    have h2 : (2 : K) ^ (e₁ - e₂ - T).toNat * 2 ^ T = 2 ^ e₁ / 2 ^ e₂ := by
      rw [two_pow_toNat_mul hTle, zpow_sub₀ two_ne_zero]
    have hm₂ : (m₂ : K) ≠ 0 := by exact_mod_cast h₂.ne'
    have hs₂ : (sgn s₂ : K) * sgn s₂ = 1 := by cases s₂ <;> simp [sgn]
    have hs₂' : (sgn s₂ : K) ≠ 0 := by cases s₂ <;> simp [sgn]
    rw [show (m₁ : K) * 2 ^ (e₁ - e₂ - T).toNat / m₂ * 2 ^ T =
      m₁ / m₂ * (2 ^ (e₁ - e₂ - T).toNat * 2 ^ T) by ring, h2]
    have h2e₂ : (2 : K) ^ e₂ ≠ 0 := zpow_ne_zero _ two_ne_zero
    field_simp
    linear_combination (sgn s₁ : K) * hs₂

end Div

/-- **The bridge, `/`** Lean's `Float` division is `rn` of the exact quotient, for a finite
nonzero divisor, below overflow. -/
theorem val_div {a b : Float} (ha : a.isFinite) (hb : b.isFinite) (hb0 : val b ≠ (0 : K))
    (hov : |rn (val a / val b : K)| < 2 ^ 1024) :
    val (a / b) = rn (val a / val b : K) ∧ (a / b).isFinite := by
  obtain ⟨hv, hc⟩ := div_spec (K := K) (packable_toModel ha) (packable_toModel hb) hb0
  have hp := packable_of_canon hc (by rw [hv]; exact hov)
  exact ⟨(val_ofModel_pack hp).trans hv, isFinite_ofModel_pack hp⟩

/-- `1.0`'s bits unpack to `2^52 · 2⁻⁵²`. -/
theorem unpack_one :
    UnpackedFloat.unpack .binary64 (0x3FF0000000000000 : UInt64).toBitVec =
      .finite .positive (2 ^ 52) (-52) (by positivity) := by
  have h1 : UnpackedFloat.unpackExponent (spec := .binary64)
      (0x3FF0000000000000 : UInt64).toBitVec = 1023#11 := by decide
  have h2 : UnpackedFloat.unpackMantissa (spec := .binary64)
      (0x3FF0000000000000 : UInt64).toBitVec = 0#52 := by decide
  have h3 : UnpackedFloat.unpackSign (spec := .binary64)
      (0x3FF0000000000000 : UInt64).toBitVec = 0#1 := by decide
  unfold UnpackedFloat.unpack
  simp only [h1, h2, h3]
  have h4 : ¬ (1023#11 : BitVec 11) = -1#11 := by decide
  have h5 : ¬ (1023#11 : BitVec 11) = 0#11 := by decide
  simp only [h4, h5, ↓reduceIte, UnpackedFloat.finite.injEq]
  refine ⟨rfl, by decide, ?_⟩
  rw [exponentBias_eq, mantissaBitsWithoutImplicit_eq]; rfl

omit [IsStrictOrderedRing K] in
theorem val_ofBits_one : val (K := K) (Float.ofBits 0x3FF0000000000000) = 1 ∧
    (Float.ofBits 0x3FF0000000000000).isFinite := by
  have hp : Packable (UnpackedFloat.unpack .binary64 (0x3FF0000000000000 : UInt64).toBitVec) := by
    rw [unpack_one]; exact ⟨Or.inl ⟨le_rfl, by norm_num, by norm_num⟩, by norm_num⟩
  refine ⟨(val_ofModel_pack hp).trans ?_, isFinite_ofModel_pack hp⟩
  rw [unpack_one]; norm_num [value, sgn]

/-- `k.toFloat` is exact below `2^53`: `UInt64.toFloat` rounds `k`, then multiplies by `1.0`. -/
theorem val_toFloat {k : ℕ} (hk : k < 2 ^ 53) :
    val (K := K) k.toFloat = k ∧ k.toFloat.isFinite := by
  have hfast : k.toFloat = k.toUInt64.toFloat * Float.ofBits 0x3FF0000000000000 := by
    change Float.ofScientific k false 0 = _
    simp only [Float.ofScientific, show k < 2 ^ 53 ∧ 0 ≤ 22 from ⟨hk, by norm_num⟩]
    rfl
  have hn : k.toUInt64.toNat = k := UInt64.toNat_ofNat_of_lt' (by unfold UInt64.size; omega)
  have hkf : IsFloat (k : K) :=
    ⟨k, 0, by rw [Nat.abs_cast]; exact_mod_cast hk, by norm_num, by simp⟩
  have hk1024 : |(k : K)| < 2 ^ 1024 := by
    rw [abs_of_nonneg (by positivity)]
    calc (k : K) < 2 ^ 53 := by exact_mod_cast hk
      _ ≤ 2 ^ 1024 := pow_le_pow_right₀ one_le_two (by norm_num)
  -- `UInt64.toFloat k = rn k = k`
  obtain ⟨hv, hc⟩ := normalize_spec (K := K) (k.toUInt64.toNat : ℤ) 0 .positive
  replace hv : value (UnpackedFloat.normalize .binary64 (k.toUInt64.toNat : ℤ) 0 .positive) =
      (k : K) := by
    rw [hv, hn, zpow_zero, mul_one]; push_cast; exact rn_isFloat hkf
  have hp := packable_of_canon hc (by rw [hv]; exact hk1024)
  have hu : val (K := K) k.toUInt64.toFloat = k := (val_ofModel_pack hp).trans hv
  have hfu : k.toUInt64.toFloat.isFinite := isFinite_ofModel_pack hp
  obtain ⟨h1, hf1⟩ := val_ofBits_one (K := K)
  rw [hfast]
  obtain ⟨hv', hf'⟩ := val_mul hfu hf1 (by rw [hu, h1, mul_one, rn_isFloat hkf]; exact hk1024)
  rw [hu, h1, mul_one, rn_isFloat hkf] at hv'
  exact ⟨hv', hf'⟩

/-- **CND-6 on Lean's `Float`** `k.toFloat / n.toFloat` is exactly `1` when `k = n` and only
then, for `k ≤ n < 2^53`: `rn_div_eq_one_iff`, for Lean's own float64 division. -/
theorem val_toFloat_div_eq_one_iff {k n : ℕ} (hk : k ≤ n) (hn : n < 2 ^ 53) (h0 : 0 < n) :
    val (K := K) (k.toFloat / n.toFloat) = 1 ↔ k = n := by
  obtain ⟨hvk, hfk⟩ := val_toFloat (K := K) (lt_of_le_of_lt hk hn)
  obtain ⟨hvn, hfn⟩ := val_toFloat (K := K) hn
  have hov : |rn ((k : K) / n)| < 2 ^ 1024 := by
    rw [abs_of_nonneg (rn_nonneg (by positivity))]
    exact (rn_div_le_one hk).trans_lt (one_lt_pow₀ one_lt_two (by norm_num))
  obtain ⟨hv, -⟩ := val_div hfk hfn (by rw [hvn]; exact_mod_cast h0.ne')
    (by rw [hvk, hvn]; exact hov)
  rw [hv, hvk, hvn]
  exact rn_div_eq_one_iff hk (by omega) h0

namespace SumTree

omit [Field K] [LinearOrder K] [IsStrictOrderedRing K] [FloorRing K] in
theorem leaves_map {α : Type*} (f : α → K) (t : SumTree α) :
    (t.map f).leaves = t.leaves.map f := by
  induction t with
  | leaf x => rfl
  | node l r ihl ihr => simp [map, leaves, ihl, ihr]

/-- A float64 sum of nonnegative finite `Float`s, with at most four nonzero summands and an exact
sum at most `2^1000`, is `fl` of their values: no node overflows. -/
theorem val_evalF {t : SumTree Float}
    (ht : ∀ x ∈ t.leaves, x.isFinite ∧ 0 ≤ val (K := K) x)
    (h4 : (t.map (val (K := K))).nz ≤ 4) (hbig : (t.map (val (K := K))).exact ≤ 2 ^ 1000) :
    val (K := K) t.evalF = (t.map (val (K := K))).fl ∧ t.evalF.isFinite := by
  induction t with
  | leaf x => exact ⟨rfl, (ht x (by simp [leaves])).1⟩
  | node l r ihl ihr =>
    have hl : ∀ x ∈ l.leaves, x.isFinite ∧ 0 ≤ val (K := K) x :=
      fun x hx ↦ ht x (by simp [leaves, hx])
    have hr : ∀ x ∈ r.leaves, x.isFinite ∧ 0 ≤ val (K := K) x :=
      fun x hx ↦ ht x (by simp [leaves, hx])
    have hnz := nz_node (l.map (val (K := K))) (r.map (val (K := K)))
    have hEl : 0 ≤ (l.map (val (K := K))).exact := by
      rw [exact_eq_sum, leaves_map]
      exact List.sum_nonneg fun y hy ↦ by
        obtain ⟨x, hx, rfl⟩ := List.mem_map.1 hy; exact (hl x hx).2
    have hEr : 0 ≤ (r.map (val (K := K))).exact := by
      rw [exact_eq_sum, leaves_map]
      exact List.sum_nonneg fun y hy ↦ by
        obtain ⟨x, hx, rfl⟩ := List.mem_map.1 hy; exact (hr x hx).2
    have hsum : (map (val (K := K)) (node l r)).exact =
        (l.map (val (K := K))).exact + (r.map (val (K := K))).exact := rfl
    obtain ⟨vl, fl'⟩ := ihl hl (by simp only [map] at h4; omega)
      ((le_add_of_nonneg_right hEr).trans (hsum ▸ hbig))
    obtain ⟨vr, fr'⟩ := ihr hr (by simp only [map] at h4; omega)
      ((le_add_of_nonneg_left hEl).trans (hsum ▸ hbig))
    -- the node's float64 sum stays below `(1 + u)^3 · 2^1000`, far from overflow
    set T := map (val (K := K)) (node l r) with hT
    have hleaf : ∀ y ∈ T.leaves, 0 ≤ y ∧ IsFloat y := by
      intro y hy
      rw [hT, leaves_map] at hy
      obtain ⟨x, hx, rfl⟩ := List.mem_map.1 hy
      exact ⟨(ht x hx).2, isFloat_value (packable_toModel (ht x hx).1)⟩
    obtain ⟨-, hup⟩ := envelope T hleaf
    have hfl0 : 0 ≤ T.fl := fl_nonneg fun y hy ↦ (hleaf y hy).1
    have hE0 : 0 ≤ T.exact := exact_nonneg fun y hy ↦ (hleaf y hy).1
    have hov : |rn (val (K := K) l.evalF + val r.evalF)| < 2 ^ 1024 := by
      rw [vl, vr]
      change |T.fl| < 2 ^ 1024
      rw [abs_of_nonneg hfl0]
      have hpow : (1 + (u : K)) ^ (T.nz - 1) ≤ 2 := by
        calc (1 + (u : K)) ^ (T.nz - 1) ≤ (1 + u) ^ 3 :=
              pow_le_pow_right₀ (by have : (0 : K) ≤ u := by positivity
                                    linarith) (by omega)
          _ ≤ 2 := by norm_num [u]
      calc T.fl ≤ (1 + u) ^ (T.nz - 1) * T.exact := hup
        _ ≤ 2 * 2 ^ 1000 := mul_le_mul hpow hbig hE0 (by norm_num)
        _ = 2 ^ 1001 := (pow_succ' (2 : K) 1000).symm
        _ < 2 ^ 1024 := pow_lt_pow_right₀ one_lt_two (by norm_num)
    obtain ⟨hv, hf⟩ := val_add fl' fr' hov
    exact ⟨by rw [evalF, hv, vl, vr]; rfl, hf⟩

/-- **LAP-1 on Lean's `Float`** Two association orders, evaluated in Lean's float64, of the same at
most four nonzero nonnegative finite summands, agree within `4 · eps` of either result. -/
theorem val_evalF_agreement {t₁ t₂ : SumTree Float} (hp : t₁.leaves.Perm t₂.leaves)
    (ht : ∀ x ∈ t₂.leaves, x.isFinite ∧ 0 ≤ val (K := K) x)
    (h4 : (t₂.map (val (K := K))).nz ≤ 4) (hbig : (t₂.map (val (K := K))).exact ≤ 2 ^ 1000) :
    |val (K := K) t₁.evalF - val t₂.evalF| ≤ 4 * 2 ^ (-52 : ℤ) * val t₂.evalF := by
  have hpm : (t₁.map (val (K := K))).leaves.Perm (t₂.map (val (K := K))).leaves := by
    rw [leaves_map, leaves_map]; exact hp.map _
  have ht₁ : ∀ x ∈ t₁.leaves, x.isFinite ∧ 0 ≤ val (K := K) x := fun x hx ↦ ht x (hp.subset hx)
  have hnz : (t₁.map (val (K := K))).nz = (t₂.map (val (K := K))).nz := (hpm.filter _).length_eq
  have hS : (t₁.map (val (K := K))).exact = (t₂.map (val (K := K))).exact := by
    rw [exact_eq_sum, exact_eq_sum, hpm.sum_eq]
  rw [(val_evalF ht₁ (hnz ▸ h4) (hS ▸ hbig)).1, (val_evalF ht h4 hbig).1]
  refine agreement hpm (fun y hy ↦ ?_) h4
  rw [leaves_map] at hy
  obtain ⟨x, hx, rfl⟩ := List.mem_map.1 hy
  exact ⟨(ht x hx).2, isFloat_value (packable_toModel (ht x hx).1)⟩

end SumTree

end LeanFloat

section Compare

/-- A canonical form in a higher binade has the larger value. -/
theorem lt_of_exponent_lt {m₁ m₂ : ℕ} {e₁ e₂ : ℤ} (h₁ : Canonical m₁ e₁) (h₂ : Canonical m₂ e₂)
    (he : e₁ < e₂) : (m₁ : K) * 2 ^ e₁ < m₂ * 2 ^ e₂ := by
  have hm₁ : m₁ < 2 ^ 53 := by rcases h₁ with ⟨-, h, -⟩ | ⟨-, h, -⟩ <;> omega
  have he₁ : -1074 ≤ e₁ := by rcases h₁ with ⟨-, -, h⟩ | ⟨-, -, h⟩ <;> omega
  have hm₂ : 2 ^ 52 ≤ m₂ := by
    rcases h₂ with ⟨h, -, -⟩ | ⟨-, -, h⟩
    · exact h
    · omega
  have c₁ : (m₁ : K) < 2 ^ (53 : ℤ) := by
    rw [show (2 : K) ^ (53 : ℤ) = ((2 ^ 53 : ℕ) : K) by norm_num]; exact_mod_cast hm₁
  have c₂ : (2 : K) ^ (52 : ℤ) ≤ m₂ := by
    rw [show (2 : K) ^ (52 : ℤ) = ((2 ^ 52 : ℕ) : K) by norm_num]; exact_mod_cast hm₂
  calc (m₁ : K) * 2 ^ e₁ < 2 ^ (53 : ℤ) * 2 ^ e₁ := by gcongr
    _ = 2 ^ (52 : ℤ) * 2 ^ (e₁ + 1) := by
      rw [← zpow_add₀ two_ne_zero, ← zpow_add₀ two_ne_zero]; ring_nf
    _ ≤ 2 ^ (52 : ℤ) * 2 ^ e₂ := by
      gcongr
      · exact one_le_two
      · omega
    _ ≤ m₂ * 2 ^ e₂ := by gcongr

/-- On canonical forms, comparing `(e, m)` lexicographically compares values. -/
theorem compare_canonical {m₁ m₂ : ℕ} {e₁ e₂ : ℤ} (h₁ : Canonical m₁ e₁)
    (h₂ : Canonical m₂ e₂) :
    (compare e₁ e₂).then (compare m₁ m₂) = compare ((m₁ : K) * 2 ^ e₁) ((m₂ : K) * 2 ^ e₂) := by
  rcases lt_trichotomy e₁ e₂ with he | rfl | he
  · rw [Int.compare_eq_lt.mpr he]
    exact (compare_lt_iff_lt.2 (lt_of_exponent_lt h₁ h₂ he)).symm
  · rw [Int.compare_eq_eq.mpr rfl]
    change compare m₁ m₂ = _
    rcases lt_trichotomy m₁ m₂ with hm | rfl | hm
    · rw [Nat.compare_eq_lt.mpr hm]
      exact (compare_lt_iff_lt.2 (by gcongr)).symm
    · rw [Nat.compare_eq_eq.mpr rfl]; exact (compare_eq_iff_eq.2 rfl).symm
    · rw [Nat.compare_eq_gt.mpr hm]
      exact (compare_gt_iff_gt.2 (by gcongr)).symm
  · rw [Int.compare_eq_gt.mpr he]
    exact (compare_gt_iff_gt.2 (lt_of_exponent_lt h₂ h₁ he)).symm

omit [FloorRing K] in
theorem compare_neg_neg (x y : K) : compare (-x) (-y) = (compare x y).swap := by
  rcases lt_trichotomy x y with h | rfl | h
  · rw [compare_lt_iff_lt.2 h, compare_gt_iff_gt.2 (neg_lt_neg h)]; rfl
  · rw [compare_eq_iff_eq.2 rfl, compare_eq_iff_eq.2 rfl]; rfl
  · rw [compare_gt_iff_gt.2 h, compare_lt_iff_lt.2 (neg_lt_neg h)]; rfl

/-- **Comparisons are exact** On finite floats, core's `compare` compares their values. -/
theorem compare_eq {a b : UnpackedFloat} (ha : Packable a) (hb : Packable b) :
    a.compare b = some (compare (value a : K) (value b)) := by
  have pos : ∀ {m : ℕ} {e : ℤ}, 0 < m → (0 : K) < m * 2 ^ e := fun hm ↦ by positivity
  match a, b, ha, hb with
  | .zero _, .zero _, _, _ =>
    exact congrArg some (compare_eq_iff_eq.2 rfl).symm
  | .zero _, .finite .positive m e h, _, _ =>
    exact congrArg some (compare_lt_iff_lt.2 (by simpa [value, sgn] using pos (e := e) h)).symm
  | .zero _, .finite .negative m e h, _, _ =>
    exact congrArg some (compare_gt_iff_gt.2 (by simpa [value, sgn] using pos (e := e) h)).symm
  | .finite .positive m e h, .zero _, _, _ =>
    exact congrArg some (compare_gt_iff_gt.2 (by simpa [value, sgn] using pos (e := e) h)).symm
  | .finite .negative m e h, .zero _, _, _ =>
    exact congrArg some (compare_lt_iff_lt.2 (by simpa [value, sgn] using pos (e := e) h)).symm
  | .finite .positive m₁ e₁ h₁, .finite .negative m₂ e₂ h₂, _, _ =>
    refine congrArg some (compare_gt_iff_gt.2 ?_).symm
    have := pos (e := e₁) h₁; have := pos (e := e₂) h₂
    simp only [value, sgn]; linarith
  | .finite .negative m₁ e₁ h₁, .finite .positive m₂ e₂ h₂, _, _ =>
    refine congrArg some (compare_lt_iff_lt.2 ?_).symm
    have := pos (e := e₁) h₁; have := pos (e := e₂) h₂
    simp only [value, sgn]; linarith
  | .finite .positive m₁ e₁ h₁, .finite .positive m₂ e₂ h₂, ⟨hc₁, _⟩, ⟨hc₂, _⟩ =>
    refine congrArg some ?_
    rw [compare_canonical (K := K) hc₁ hc₂]
    simp only [value, sgn, one_mul]
  | .finite .negative m₁ e₁ h₁, .finite .negative m₂ e₂ h₂, ⟨hc₁, _⟩, ⟨hc₂, _⟩ =>
    refine congrArg some ?_
    rw [compare_canonical (K := K) hc₁ hc₂]
    simp only [value, sgn, neg_one_mul, compare_neg_neg]

/-- **Comparisons are exact** On finite `Float`s, `==` is equality of values. -/
theorem beq_eq_decide {a b : Float} (ha : a.isFinite) (hb : b.isFinite) :
    (a == b) = decide (val (K := K) a = val b) := by
  change (a.toModel.unpack.compare b.toModel.unpack == some .eq) = _
  rw [compare_eq (K := K) (packable_toModel ha) (packable_toModel hb), Bool.eq_iff_iff]
  simp only [beq_iff_eq, Option.some.injEq, compare_eq_iff_eq, decide_eq_true_eq]
  rfl

/-- **Comparisons are exact** On finite `Float`s, `≤` is the order of values. -/
theorem le_iff_val_le {a b : Float} (ha : a.isFinite) (hb : b.isFinite) :
    a ≤ b ↔ val (K := K) a ≤ val b := by
  change (a.toModel.unpack.compare b.toModel.unpack).any (·.isLE) = true ↔ _
  rw [compare_eq (K := K) (packable_toModel ha) (packable_toModel hb)]
  change (compare (val (K := K) a) (val b)).isLE = true ↔ _
  rcases lt_trichotomy (val (K := K) a) (val b) with h | h | h
  · rw [compare_lt_iff_lt.2 h]; simp [h.le]
  · rw [compare_eq_iff_eq.2 h]; simp [h]
  · rw [compare_gt_iff_gt.2 h]; simp [not_le.2 h]

end Compare

/-- **CND-6 on Lean's `Float`, as the code compares** For `k ≤ n < 2^53`,
`k.toFloat / n.toFloat == 1` exactly when `k = n`. -/
theorem toFloat_div_beq_one {k n : ℕ} (hk : k ≤ n) (hn : n < 2 ^ 53) (h0 : 0 < n) :
    (k.toFloat / n.toFloat == 1) = decide (k = n) := by
  obtain ⟨hvk, hfk⟩ := val_toFloat (K := ℚ) (lt_of_le_of_lt hk hn)
  obtain ⟨hvn, hfn⟩ := val_toFloat (K := ℚ) hn
  obtain ⟨hv1, hf1⟩ := val_toFloat (K := ℚ) (k := 1) (by norm_num)
  have hov : |rn ((k : ℚ) / n)| < 2 ^ 1024 := by
    rw [abs_of_nonneg (rn_nonneg (by positivity))]
    exact (rn_div_le_one hk).trans_lt (one_lt_pow₀ one_lt_two (by norm_num))
  obtain ⟨hv, hf⟩ := val_div hfk hfn (by rw [hvn]; exact_mod_cast h0.ne')
    (by rw [hvk, hvn]; exact hov)
  rw [show (1 : Float) = (1 : ℕ).toFloat from rfl, beq_eq_decide (K := ℚ) hf hf1, hv1, hv, hvk,
    hvn]
  exact decide_eq_decide.2 (by push_cast; exact rn_div_eq_one_iff hk (by omega) h0)

/-- **CND-6 on Lean's `Float`, as the code compares** For `k ≤ n < 2^53`,
`k.toFloat / n.toFloat ≤ 1`. -/
theorem toFloat_div_le_one {k n : ℕ} (hk : k ≤ n) (hn : n < 2 ^ 53) (h0 : 0 < n) :
    k.toFloat / n.toFloat ≤ 1 := by
  obtain ⟨hvk, hfk⟩ := val_toFloat (K := ℚ) (lt_of_le_of_lt hk hn)
  obtain ⟨hvn, hfn⟩ := val_toFloat (K := ℚ) hn
  obtain ⟨hv1, hf1⟩ := val_toFloat (K := ℚ) (k := 1) (by norm_num)
  have hov : |rn ((k : ℚ) / n)| < 2 ^ 1024 := by
    rw [abs_of_nonneg (rn_nonneg (by positivity))]
    exact (rn_div_le_one hk).trans_lt (one_lt_pow₀ one_lt_two (by norm_num))
  obtain ⟨hv, hf⟩ := val_div hfk hfn (by rw [hvn]; exact_mod_cast h0.ne')
    (by rw [hvk, hvn]; exact hov)
  rw [show (1 : Float) = (1 : ℕ).toFloat from rfl, le_iff_val_le (K := ℚ) hf hf1, hv1, hv, hvk,
    hvn]
  push_cast
  exact rn_div_le_one hk

end Palace.Binary64
