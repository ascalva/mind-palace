module

public import Palace.Leak.Defs
public import Palace.Retrieval

/-!
# The leaky support: a leak of `ε` costs a step of killing

The limits program's L5 (`docs/brainstorms/limits-of-the-algebra.md`) conjectured that a census
leaking a fraction `ε` of every degree costs the support's nearness a factor `(1+ε)^{2·depth}`.
The exact answer is simpler and uniform in the depth. With every degree under-counted by at most
the fraction `ε/(1+ε)` — `d_i ≤ (1+ε)(d_i − ℓ_i)` — the leaky walk lies entrywise under the
graph's walk at killing `(1+ε)·z`, because an under-counted degree is exactly a hotter transition
(LEAK-1, `leakyWalk_le`); RSP-5's monotonicity then puts the leaky support's nearness at `z` under
the full graph's nearness at `(1+ε)·z`, whenever `(1+ε)·z < 1` (LEAK-2). The cost of a leak is a
reparametrization of the killing, and the support singularity is where `(1+ε)·z` reaches `1`:
past it the support's walk no longer converges and its answer is not bounded by the graph's at
any temperature. Design theorems (Palace only, no Spec rows): the code's census notes how many
papers were truncated, not yet how much weight leaked.
-/

@[expose] public section

open Matrix Finset

namespace Palace.Retrieval

variable {V : Type*} [Fintype V] [DecidableEq V] {w : Matrix V V ℝ} {ℓ : V → ℝ} {β z ε : ℝ}

omit [DecidableEq V] in
/-- The leaky walk is nonnegative when the leak leaves every degree nonnegative. -/
theorem leakyWalk_nonneg (hw0 : ∀ i j, 0 ≤ w i j) (hz : 0 ≤ z) (hd : ∀ i, 0 ≤ degree w i - ℓ i)
    (i j : V) : 0 ≤ leakyWalk w ℓ β z i j := by
  simp only [leakyWalk, of_apply]
  exact mul_nonneg (mul_nonneg hz (div_nonneg (hw0 i j) (hd i))) (Real.rpow_nonneg (hw0 i j) β)

omit [DecidableEq V] in
/-- A leak of at most the fraction `ε/(1+ε)` leaves every degree nonnegative. -/
theorem sub_leak_nonneg (hw0 : ∀ i j, 0 ≤ w i j) (hε : 0 ≤ ε)
    (hleak : ∀ i, degree w i ≤ (1 + ε) * (degree w i - ℓ i)) (i : V) :
    0 ≤ degree w i - ℓ i := by
  have hdeg : 0 ≤ degree w i := sum_nonneg fun b _ ↦ hw0 i b
  by_contra h
  push Not at h
  nlinarith [hleak i, hdeg, hε]

omit [DecidableEq V] in
/-- LEAK-1 The leaky walk lies under the walk at killing `(1+ε)·z`: an under-counted degree is a
hotter transition, by at most the factor `1+ε`. -/
theorem leakyWalk_le (hw0 : ∀ i j, 0 ≤ w i j) (hz : 0 ≤ z) (hε : 0 ≤ ε) (hℓ : ∀ i, 0 ≤ ℓ i)
    (hleak : ∀ i, degree w i ≤ (1 + ε) * (degree w i - ℓ i)) (i j : V) :
    leakyWalk w ℓ β z i j ≤ killedWalk w β ((1 + ε) * z) i j := by
  simp only [leakyWalk, killedWalk, of_apply]
  have hdeg : 0 ≤ degree w i := sum_nonneg fun b _ ↦ hw0 i b
  have hd0 : 0 ≤ degree w i - ℓ i := sub_leak_nonneg hw0 hε hleak i
  have hpow : 0 ≤ w i j ^ β := Real.rpow_nonneg (hw0 i j) β
  rcases hd0.lt_or_eq with hdℓ | hd
  · have hdpos : 0 < degree w i := by linarith [hℓ i]
    refine mul_le_mul_of_nonneg_right ?_ hpow
    have e : (1 + ε) * z * (w i j / degree w i) = z * ((1 + ε) * w i j / degree w i) := by ring
    rw [e]
    refine mul_le_mul_of_nonneg_left ?_ hz
    rw [div_le_div_iff₀ hdℓ hdpos]
    nlinarith [mul_le_mul_of_nonneg_left (hleak i) (hw0 i j)]
  · rw [← hd, div_zero, mul_zero, zero_mul]
    exact mul_nonneg (mul_nonneg (mul_nonneg (by linarith) hz) (div_nonneg (hw0 i j) hdeg)) hpow

/-- LEAK-2 A leak of `ε` costs a step of killing: the leaky support's nearness at `z` is at most
the full graph's nearness at `(1+ε)·z` — uniform in the depth of the walk, and the support
singularity is `(1+ε)·z = 1`. -/
theorem nearnessLeaky_le_nearness (hw0 : ∀ i j, 0 ≤ w i j) (hw1 : ∀ i j, w i j ≤ 1) (hβ : 0 ≤ β)
    (hz0 : 0 ≤ z) (hε : 0 ≤ ε) (hz1 : (1 + ε) * z < 1) (hℓ : ∀ i, 0 ≤ ℓ i)
    (hleak : ∀ i, degree w i ≤ (1 + ε) * (degree w i - ℓ i)) (S : Finset V) (i j : V) :
    nearnessLeaky w ℓ S β z i j ≤ nearness w β ((1 + ε) * z) i j := by
  have hz0' : 0 ≤ (1 + ε) * z := mul_nonneg (by linarith) hz0
  have hM : ∀ a b, 0 ≤ killedWalk w β ((1 + ε) * z) a b := killedWalk_nonneg hw0 hz0'
  have hrow : ∀ a, ∑ b, killedWalk w β ((1 + ε) * z) a b ≤ (1 + ε) * z :=
    sum_killedWalk_le hw0 hw1 hβ hz0'
  have hL : ∀ a b, 0 ≤ leakyWalk w ℓ β z a b :=
    leakyWalk_nonneg hw0 hz0 (sub_leak_nonneg hw0 hε hleak)
  have hM' : ∀ a b, 0 ≤ restrict (leakyWalk w ℓ β z) S a b := restrict_nonneg hL S
  have hle : ∀ a b, restrict (leakyWalk w ℓ β z) S a b ≤ killedWalk w β ((1 + ε) * z) a b :=
    fun a b ↦ (restrict_le hL S a b).trans (leakyWalk_le hw0 hz0 hε hℓ hleak a b)
  have hrow' : ∀ a, ∑ b, restrict (leakyWalk w ℓ β z) S a b ≤ (1 + ε) * z :=
    fun a ↦ (sum_le_sum fun b _ ↦ hle a b).trans (hrow a)
  have key := inv_ratio_mono hM' hrow' hz1 hM hrow hle i j
  have hdd : 0 < (1 - killedWalk w β ((1 + ε) * z))⁻¹ j j :=
    zero_lt_one.trans_le (one_le_inv_apply_self hM hrow hz1 j)
  have hdd' : 0 < (1 - restrict (leakyWalk w ℓ β z) S)⁻¹ j j :=
    zero_lt_one.trans_le (one_le_inv_apply_self hM' hrow' hz1 j)
  unfold nearnessLeaky nearness fundamental
  rw [div_le_div_iff₀ hdd' hdd]
  exact key

end Palace.Retrieval
