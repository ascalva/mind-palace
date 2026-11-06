module

public import Palace.Format.Defs
public import Palace.Binary64

/-!
# Binary formats of any precision: L3's substrate generalized

`Palace/Binary64.lean` fixes binary64's 53 significand bits and least subnormal `2⁻¹⁰⁷⁴`. Here
both are parameters: `rnf p emin` rounds to nearest, ties to even, onto the format with `p`
significand bits whose least subnormal is `2 ^ emin`, without overflow. binary64's `rn` is
`rnf 53 (-1074)` (`rn_eq_rnf`), so the attacks that check `rn` against this machine's float64
check the general definition at those parameters; `PalaceTest/Format.lean` checks it at binary32's
against this machine's float32 and at binary16's against this machine's float16.

The law the float16 entry needs: `rnf p emin` moves `x` by at most `2⁻ᵖ · max |x| 2^(emin+p−1)`,
the relative bound `2⁻ᵖ |x|` in the normal range and half the least subnormal's spacing below it.
-/

@[expose] public section

namespace Palace.Format

open Palace.Binary64 (rne abs_sub_rne rne_zero two_zpow_log_le)

variable {K : Type*} [Field K] [LinearOrder K] [IsStrictOrderedRing K] [FloorRing K]

omit [IsStrictOrderedRing K] in
/-- binary64's rounding is the general one at binary64's parameters. -/
theorem rn_eq_rnf (x : K) : Binary64.rn x = rnf 53 (-1074) x := by
  have h : Binary64.cexp x = cexpf 53 (-1074) x := by
    simp only [Binary64.cexp, cexpf]; norm_num
  simp only [Binary64.rn, rnf, h]

@[simp] theorem rnf_zero (p : ℕ) (emin : ℤ) : rnf p emin (0 : K) = 0 := by
  simp [rnf]

/-- `rnf` moves `x` by at most half an ulp. -/
theorem abs_rnf_sub_le_half_ulp (p : ℕ) (emin : ℤ) (x : K) :
    |rnf p emin x - x| ≤ 2 ^ cexpf p emin x / 2 := by
  have h2 : (0 : K) < 2 ^ cexpf p emin x := zpow_pos two_pos _
  have key : rnf p emin x - x =
      (rne (x / 2 ^ cexpf p emin x) - x / 2 ^ cexpf p emin x) * 2 ^ cexpf p emin x := by
    rw [rnf, sub_mul, div_mul_cancel₀ x h2.ne']
  rw [key, abs_mul, abs_of_pos h2, abs_sub_comm]
  have := abs_sub_rne (x / 2 ^ cexpf p emin x)
  calc |x / 2 ^ cexpf p emin x - rne (x / 2 ^ cexpf p emin x)| * 2 ^ cexpf p emin x
      ≤ 1 / 2 * 2 ^ cexpf p emin x := by gcongr
    _ = 2 ^ cexpf p emin x / 2 := by ring

/-- The error of rounding onto a format with `p` significand bits and least subnormal `2 ^ emin`:
at most `2⁻ᵖ |x|` in the normal range, and `2^(emin − 1)`, half the subnormal spacing, below it. -/
theorem abs_rnf_sub_le (p : ℕ) (emin : ℤ) (x : K) :
    |rnf p emin x - x| ≤ 2 ^ (-(p : ℤ)) * max |x| (2 ^ (emin + p - 1)) := by
  rcases eq_or_ne x 0 with rfl | hx
  · simp
  have hpos : (0 : K) < 2 ^ (-(p : ℤ)) := zpow_pos two_pos _
  refine (abs_rnf_sub_le_half_ulp p emin x).trans ?_
  rw [mul_max_of_nonneg _ _ hpos.le]
  rcases le_total (Int.log 2 |x| - ((p : ℤ) - 1)) emin with h | h
  · rw [cexpf, max_eq_right h]
    refine le_max_of_le_right (le_of_eq ?_)
    rw [← zpow_add₀ two_ne_zero, div_eq_iff two_ne_zero, ← zpow_add_one₀ two_ne_zero]
    ring_nf
  · rw [cexpf, max_eq_left h]
    refine le_max_of_le_left ?_
    calc (2 : K) ^ (Int.log 2 |x| - ((p : ℤ) - 1)) / 2
        = 2 ^ (-(p : ℤ)) * 2 ^ Int.log 2 |x| := by
          rw [← zpow_add₀ two_ne_zero, div_eq_iff two_ne_zero, ← zpow_add_one₀ two_ne_zero]
          ring_nf
      _ ≤ 2 ^ (-(p : ℤ)) * |x| := by gcongr; exact two_zpow_log_le (abs_pos.2 hx)

end Palace.Format
