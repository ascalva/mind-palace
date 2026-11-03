module

public import Palace.FloatModel.Defs

/-!
# Lean's `Float` rounds as `rn` does, the statements

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

These are the laws of `Palace/FloatModel.lean` as the ledger cites them, each with its proof
left as `sorry`. `lake comparator` checks that the `Palace` library proves each one
exactly as stated here, from the standard axioms alone.
-/

@[expose] public section

open Float.Model (UnpackedFloat Format totalExponent)

open Float.Model.UnpackedFloat (ExtendedMantissa Accuracy Sign)

namespace Palace.Binary64

variable {K : Type*} [Field K] [LinearOrder K] [IsStrictOrderedRing K] [FloorRing K]

section LeanFloat

namespace SumTree

/-- **LAP-1 on Lean's `Float`** Two association orders, evaluated in Lean's float64, of the same at
most four nonzero nonnegative finite summands, agree within `4 · eps` of either result. -/
theorem val_evalF_agreement {t₁ t₂ : SumTree Float} (hp : t₁.leaves.Perm t₂.leaves)
    (ht : ∀ x ∈ t₂.leaves, x.isFinite ∧ 0 ≤ val (K := K) x)
    (h4 : (t₂.map (val (K := K))).nz ≤ 4) (hbig : (t₂.map (val (K := K))).exact ≤ 2 ^ 1000) :
    |val (K := K) t₁.evalF - val t₂.evalF| ≤ 4 * 2 ^ (-52 : ℤ) * val t₂.evalF :=
  sorry

end SumTree

end LeanFloat

/-- **CND-6 on Lean's `Float`, as the code compares** For `k ≤ n < 2^53`,
`k.toFloat / n.toFloat == 1` exactly when `k = n`. -/
theorem toFloat_div_beq_one {k n : ℕ} (hk : k ≤ n) (hn : n < 2 ^ 53) (h0 : 0 < n) :
    (k.toFloat / n.toFloat == 1) = decide (k = n) :=
  sorry

/-- **CND-6 on Lean's `Float`, as the code compares** For `k ≤ n < 2^53`,
`k.toFloat / n.toFloat ≤ 1`. -/
theorem toFloat_div_le_one {k n : ℕ} (hk : k ≤ n) (hn : n < 2 ^ 53) (h0 : 0 < n) :
    k.toFloat / n.toFloat ≤ 1 :=
  sorry

end Palace.Binary64
