module

public import Palace.Growth.Defs
public import Mathlib.Analysis.SpecialFunctions.Log.Deriv
public import Mathlib.Analysis.Convex.SpecificFunctions.Basic
public import Mathlib.Algebra.Order.BigOperators.Group.List
public import Mathlib.Probability.StrongLaw
public import Mathlib.Probability.Distributions.Bernoulli
public import Mathlib.Probability.HasLaw

/-!
# The growth readout: GRW-1, and the design theorems GRW-2 to GRW-6

`eval/predictions/scoring.py`'s `growth` reports, per arm against the reference arm, the growth
of a proportional stake over the scored pairs: a thought experiment the scorer computes, nothing
that stakes anything (dn-prediction-ledger G8).

* GRW-1, the identity the code relies on: over any field the growth is the likelihood ratio
  `Π L(p_i, o_i) / Π L(r_i, o_i)`, and for proper pairs its log is the cumulative log-score
  advantage of the arm over the reference, the quantity the ledger already scores; the fractional
  stake coincides with it at `λ = 1`.
* GRW-2, the expectation: under a truth `q` the expected advantage of a pair is
  `KL(q‖r) − KL(q‖p)`, so growth is expected positive iff the forecast is closer to the truth than
  the reference is; the truthful forecast attains `KL(q‖r)`, every other forecast less (Gibbs).
* GRW-3, optimality: among the constant fractions on yes at reference `r` that keep both factors
  positive, the expected log growth under belief `p` is concave, its derivative vanishes at
  `(p − r)/(1 − r)`, which is the proportional stake, and that fraction is the maximizer, its
  growth `KL(p‖r)`, positive whenever `p ≠ r`; a negative fraction is the mirror stake on no.
* GRW-4, the path to `N×`: the holding reaches `N` times its start iff the cumulative advantage
  reaches `log N`; a pair's advantage is at most `log (1/margin)`, so at least `log N` over that
  bound pairs are needed; the expected cumulative advantage is the sum of the per-question
  expectations, so at a mean advantage `a` it reaches `log N` after `log N / a` questions.
* GRW-5, no ruin: every factor of a proper pair is positive, so the holding never reaches zero,
  and `k` adverse outcomes multiply it by at least the `k`-th power of the worst factor,
  `min (p/r) ((1 − p)/(1 − r))`, itself at least the margin.
* GRW-6, the time average: on one pair whose outcomes are independent and identically
  distributed, the time-average advantage converges almost surely to the expected one, by the
  strong law of large numbers; so a positive expected advantage grows the holding without bound
  almost surely, reaching every `N×`, and a negative one sends it to zero.

The statements the ledger cites are restated in `Spec/Growth.lean`; the rest are design theorems.
The shapes of GRW-3's domain (the fractions that keep both factors positive) and of GRW-6 (the
strong law over pairwise independent, identically distributed factors, then the two limits)
follow `unbalancedparentheses/lean-ergodicity` (Lean and Mathlib v4.35.0, Apache 2.0), whose
`kelly_optimal`, `kelly_growth_pos`, `time_average_growth_ae`, `ae_wealth_tendsto_zero` and
`ae_wealth_tendsto_atTop` state them for a bet with a gain `u` and a loss `d`; the definitions and
proofs here are our own, over the ledger's model of reference, forecast and outcome, where the
gain is `1/r − 1` and the loss is the stake.
-/

@[expose] public section

namespace Palace.Growth

variable {K : Type*}

/-! ## GRW-1 The identity -/

section Product

variable [Field K]

theorem growth_nil : growth ([] : List (Pair K × Bool)) = 1 := rfl

theorem growth_cons (s : Pair K × Bool) (l : List (Pair K × Bool)) :
    growth (s :: l) = factor s.1 s.2 * growth l := by
  simp [growth]

/-- Growth multiplies over consecutive runs of pairs. -/
theorem growth_append (l m : List (Pair K × Bool)) : growth (l ++ m) = growth l * growth m := by
  simp [growth, List.map_append, List.prod_append]

/-- **GRW-1** The product form, free of logs: over any field, the growth is the likelihood ratio
of the outcomes under the arm's forecasts and under the reference's. -/
theorem growth_eq_div (l : List (Pair K × Bool)) :
    growth l = (l.map fun s ↦ likelihood s.1.p s.2).prod /
      (l.map fun s ↦ likelihood s.1.r s.2).prod := by
  induction l with
  | nil => simp [growth]
  | cons s l ih =>
    rw [growth_cons, ih, factor, div_mul_div_comm]
    simp

/-- **GRW-1** The fractional stake at `λ = 1` is the proportional stake, so the identity holds of
the readout's full stake and of it alone. -/
theorem fractionalGrowth_one (l : List (Pair K × Bool)) : fractionalGrowth 1 l = growth l := by
  simp [fractionalGrowth, growth, fractional]

end Product

section Compl

variable [Ring K]

theorem likelihood_compl (p : K) (o : Bool) : likelihood (1 - p) (!o) = likelihood p o := by
  cases o <;> simp [likelihood]

end Compl

section Proper

variable [Field K] [LinearOrder K] [IsStrictOrderedRing K]

theorem likelihood_pos {p : K} (hp0 : 0 < p) (hp1 : p < 1) (o : Bool) : 0 < likelihood p o := by
  cases o <;> simp [likelihood, hp0, sub_pos.2 hp1]

theorem likelihood_le_one {p : K} (hp0 : 0 < p) (hp1 : p < 1) (o : Bool) : likelihood p o ≤ 1 := by
  cases o <;> simp [likelihood, hp1.le, hp0.le]

/-- Every factor of a proper pair is positive. -/
theorem factor_pos {x : Pair K} (hx : x.Proper) (o : Bool) : 0 < factor x o :=
  div_pos (likelihood_pos hx.2.2.1 hx.2.2.2 o) (likelihood_pos hx.1 hx.2.1 o)

/-- GRW-5: the growth over proper pairs is positive. -/
theorem growth_pos {l : List (Pair K × Bool)} (h : ∀ s ∈ l, s.1.Proper) : 0 < growth l :=
  List.prod_pos fun _ hy ↦ by
    obtain ⟨s, hs, rfl⟩ := List.mem_map.1 hy
    exact factor_pos (h s hs) s.2

/-- GRW-5: from a positive start the holding never reaches zero. -/
theorem holding_pos {w0 : K} (hw : 0 < w0) {l : List (Pair K × Bool)} (h : ∀ s ∈ l, s.1.Proper) :
    0 < holding w0 l :=
  mul_pos hw (growth_pos h)

omit [IsStrictOrderedRing K] in
/-- The worst factor, written out. -/
theorem worstFactor_eq (x : Pair K) :
    worstFactor x = min (x.p / x.r) ((1 - x.p) / (1 - x.r)) := by
  simp [worstFactor, factor, likelihood]

omit [IsStrictOrderedRing K] in
theorem worstFactor_le (x : Pair K) (o : Bool) : worstFactor x ≤ factor x o := by
  cases o
  · exact min_le_right _ _
  · exact min_le_left _ _

theorem worstFactor_pos {x : Pair K} (hx : x.Proper) : 0 < worstFactor x :=
  lt_min (factor_pos hx true) (factor_pos hx false)

/-- The margin is positive on a proper pair. -/
theorem margin_pos {x : Pair K} (hx : x.Proper) : 0 < margin x :=
  lt_min (lt_min hx.2.2.1 (sub_pos.2 hx.2.2.2)) (lt_min hx.1 (sub_pos.2 hx.2.1))

omit [IsStrictOrderedRing K] in
theorem margin_le_likelihood_p {x : Pair K} (o : Bool) : margin x ≤ likelihood x.p o := by
  cases o
  · exact (min_le_left _ _).trans (min_le_right _ _)
  · exact (min_le_left _ _).trans (min_le_left _ _)

omit [IsStrictOrderedRing K] in
theorem margin_le_likelihood_r {x : Pair K} (o : Bool) : margin x ≤ likelihood x.r o := by
  cases o
  · exact (min_le_right _ _).trans (min_le_right _ _)
  · exact (min_le_right _ _).trans (min_le_left _ _)

/-- GRW-4: a factor lies between the margin and its reciprocal. -/
theorem factor_mem {x : Pair K} (hx : x.Proper) (o : Bool) :
    margin x ≤ factor x o ∧ factor x o ≤ 1 / margin x := by
  have hr := likelihood_pos hx.1 hx.2.1 o
  have hm := margin_pos hx
  constructor
  · rw [factor, le_div_iff₀ hr]
    calc margin x * likelihood x.r o ≤ margin x * 1 :=
          mul_le_mul_of_nonneg_left (likelihood_le_one hx.1 hx.2.1 o) hm.le
      _ = margin x := mul_one _
      _ ≤ likelihood x.p o := margin_le_likelihood_p o
  · rw [factor, div_le_div_iff₀ hr hm, one_mul]
    calc likelihood x.p o * margin x ≤ 1 * margin x :=
          mul_le_mul_of_nonneg_right (likelihood_le_one hx.2.2.1 hx.2.2.2 o) hm.le
      _ = margin x := one_mul _
      _ ≤ likelihood x.r o := margin_le_likelihood_r o

/-- GRW-5: the worst factor is at least the margin. -/
theorem margin_le_worstFactor {x : Pair K} (hx : x.Proper) : margin x ≤ worstFactor x :=
  le_min (factor_mem hx true).1 (factor_mem hx false).1

/-- GRW-5: `k` outcomes in a row multiply the holding by at least the `k`-th power of any
bound below their worst factors. -/
theorem pow_le_growth {m : K} (hm : 0 ≤ m) {l : List (Pair K × Bool)}
    (h : ∀ s ∈ l, m ≤ worstFactor s.1) : m ^ l.length ≤ growth l := by
  induction l with
  | nil => simp [growth]
  | cons s l ih =>
    have hs : m ≤ factor s.1 s.2 := (h s (List.mem_cons_self ..)).trans (worstFactor_le _ _)
    have hl : m ^ l.length ≤ growth l := ih fun t ht ↦ h t (List.mem_cons_of_mem _ ht)
    rw [growth_cons, List.length_cons, pow_succ']
    exact mul_le_mul hs hl (pow_nonneg hm _) (hm.trans hs)

end Proper

section Log

/-- The log of a proper pair's factor is its advantage. -/
theorem log_factor {x : Pair ℝ} (hx : x.Proper) (o : Bool) :
    Real.log (factor x o) = advantage x o := by
  rw [factor, advantage, logScore, logScore,
    Real.log_div (likelihood_pos hx.2.2.1 hx.2.2.2 o).ne' (likelihood_pos hx.1 hx.2.1 o).ne']

theorem cumulative_nil : cumulative [] = 0 := rfl

theorem cumulative_cons (s : Pair ℝ × Bool) (l : List (Pair ℝ × Bool)) :
    cumulative (s :: l) = advantage s.1 s.2 + cumulative l := by
  simp [cumulative]

/-- **GRW-1** The identity: over proper pairs, the log of the growth is the cumulative log-score
advantage of the arm over the reference. -/
theorem log_growth {l : List (Pair ℝ × Bool)} (h : ∀ s ∈ l, s.1.Proper) :
    Real.log (growth l) = cumulative l := by
  induction l with
  | nil => simp [growth, cumulative]
  | cons s l ih =>
    have hs := h s (List.mem_cons_self ..)
    have hl : ∀ t ∈ l, t.1.Proper := fun t ht ↦ h t (List.mem_cons_of_mem _ ht)
    rw [growth_cons, Real.log_mul (factor_pos hs s.2).ne' (growth_pos hl).ne', log_factor hs,
      ih hl, cumulative_cons]

/-- **GRW-1** The holding is the start times the exponential of the cumulative advantage. -/
theorem holding_eq (w0 : ℝ) {l : List (Pair ℝ × Bool)} (h : ∀ s ∈ l, s.1.Proper) :
    holding w0 l = w0 * Real.exp (cumulative l) := by
  rw [holding, ← log_growth h, Real.exp_log (growth_pos h)]

end Log

/-! ## GRW-4 The path to `N×` -/

section Path

/-- GRW-4: the holding reaches `N` times its start iff the cumulative advantage reaches `log N`. -/
theorem holding_ge_iff {w0 N : ℝ} (hw : 0 < w0) (hN : 0 < N) {l : List (Pair ℝ × Bool)}
    (h : ∀ s ∈ l, s.1.Proper) : N * w0 ≤ holding w0 l ↔ Real.log N ≤ cumulative l := by
  rw [holding_eq w0 h, mul_comm N w0, mul_le_mul_iff_right₀ hw, Real.log_le_iff_le_exp hN]

/-- GRW-4: a pair's advantage, either way, is at most the log of the reciprocal of its margin. -/
theorem abs_advantage_le {x : Pair ℝ} (hx : x.Proper) (o : Bool) :
    |advantage x o| ≤ Real.log (1 / margin x) := by
  have hm := margin_pos hx
  have hp := likelihood_pos hx.2.2.1 hx.2.2.2 o
  have hr := likelihood_pos hx.1 hx.2.1 o
  have hp1 : Real.log (likelihood x.p o) ≤ 0 :=
    Real.log_nonpos hp.le (likelihood_le_one hx.2.2.1 hx.2.2.2 o)
  have hr1 : Real.log (likelihood x.r o) ≤ 0 :=
    Real.log_nonpos hr.le (likelihood_le_one hx.1 hx.2.1 o)
  have hpm : Real.log (margin x) ≤ Real.log (likelihood x.p o) :=
    Real.log_le_log hm (margin_le_likelihood_p o)
  have hrm : Real.log (margin x) ≤ Real.log (likelihood x.r o) :=
    Real.log_le_log hm (margin_le_likelihood_r o)
  rw [one_div, Real.log_inv, advantage, logScore, logScore, abs_sub_le_iff]
  constructor <;> linarith

/-- GRW-4: the cumulative advantage of `T` pairs is at most `T` times a bound on each. -/
theorem cumulative_le {B : ℝ} {l : List (Pair ℝ × Bool)} (h : ∀ s ∈ l, advantage s.1 s.2 ≤ B) :
    cumulative l ≤ l.length * B := by
  induction l with
  | nil => simp [cumulative]
  | cons s l ih =>
    have hs := h s (List.mem_cons_self ..)
    have hl := ih fun t ht ↦ h t (List.mem_cons_of_mem _ ht)
    rw [cumulative_cons, List.length_cons]
    push_cast
    linarith

/-- GRW-4: with every pair's advantage at most `B > 0`, reaching `log N` takes at least
`log N / B` pairs. -/
theorem length_ge_of_cumulative {B N : ℝ} (hB : 0 < B) {l : List (Pair ℝ × Bool)}
    (h : ∀ s ∈ l, advantage s.1 s.2 ≤ B) (hN : Real.log N ≤ cumulative l) :
    Real.log N / B ≤ l.length := by
  rw [div_le_iff₀ hB]
  exact hN.trans (cumulative_le h)

/-- The weights of each question's two outcomes sum to one, so a constant passes through the
expectation. -/
theorem expect_const_add (xs : List Question) (c : ℝ) (g : List Bool → ℝ) :
    expect xs (fun os ↦ c + g os) = c + expect xs g := by
  induction xs generalizing g with
  | nil => simp [expect]
  | cons x xs ih =>
    simp only [expect]
    rw [ih, ih]
    ring

theorem cumulativeOn_cons (x : Question) (xs : List Question) (o : Bool) (os : List Bool) :
    cumulativeOn (x :: xs) (o :: os) = advantage x.pair o + cumulativeOn xs os := by
  simp [cumulativeOn, cumulative]

/-- GRW-4: the expected cumulative advantage is the sum of the questions' expected advantages. -/
theorem expect_cumulativeOn (xs : List Question) :
    expect xs (cumulativeOn xs) = (xs.map fun x ↦ expectedAdvantage x.q x.pair).sum := by
  induction xs with
  | nil => simp [expect, cumulativeOn, cumulative]
  | cons x xs ih =>
    simp only [expect, cumulativeOn_cons, expect_const_add, ih, List.map_cons, List.sum_cons,
      expectedAdvantage]
    ring

/-- GRW-4: at a mean expected advantage `a > 0` per question, the expected cumulative advantage
reaches `log N` iff there are at least `log N / a` questions. -/
theorem expect_ge_iff {a N : ℝ} (ha : 0 < a) {xs : List Question}
    (hmean : (xs.map fun x ↦ expectedAdvantage x.q x.pair).sum = xs.length * a) :
    Real.log N ≤ expect xs (cumulativeOn xs) ↔ Real.log N / a ≤ xs.length := by
  rw [expect_cumulativeOn, hmean, div_le_iff₀ ha]

end Path

/-! ## GRW-2 The expectation -/

section Expectation

/-- `KL(q‖q) = 0`. -/
theorem klBin_self (q : ℝ) : klBin q q = 0 := by
  unfold klBin
  rcases eq_or_ne q 0 with rfl | hq
  · simp
  rcases eq_or_ne (1 - q) 0 with h1 | h1
  · simp [h1, div_self hq]
  simp [div_self hq, div_self h1]

/-- GRW-2: the expected advantage under a truth `q` is `KL(q‖r) − KL(q‖p)`. -/
theorem expectedAdvantage_eq {x : Pair ℝ} (hx : x.Proper) {q : ℝ} :
    expectedAdvantage q x = klBin q x.r - klBin q x.p := by
  obtain ⟨hr0, hr1, hp0, hp1⟩ := hx
  have hr1' : 1 - x.r ≠ 0 := (sub_pos.2 hr1).ne'
  have hp1' : 1 - x.p ≠ 0 := (sub_pos.2 hp1).ne'
  unfold expectedAdvantage klBin advantage logScore likelihood
  simp only [Bool.false_eq_true, ↓reduceIte]
  rcases eq_or_ne q 0 with rfl | hq
  · simp only [zero_mul, zero_add, sub_zero]
    rw [Real.log_div one_ne_zero hr1', Real.log_div one_ne_zero hp1']
    ring
  rcases eq_or_ne (1 - q) 0 with h1 | h1
  · rw [h1]
    simp only [zero_mul, add_zero]
    rw [Real.log_div hq hr0.ne', Real.log_div hq hp0.ne']
    ring
  rw [Real.log_div hq hr0.ne', Real.log_div hq hp0.ne', Real.log_div h1 hr1', Real.log_div h1 hp1']
  ring

/-- GRW-2: growth is expected positive iff the forecast is closer to the truth than the reference
is, in the binary divergence. -/
theorem expectedAdvantage_pos_iff {x : Pair ℝ} (hx : x.Proper) {q : ℝ} :
    0 < expectedAdvantage q x ↔ klBin q x.p < klBin q x.r := by
  rw [expectedAdvantage_eq hx, sub_pos]

/-- Gibbs' inequality for two Bernoulli laws: `KL(q‖p) ≥ 0`, with equality only at `p = q`. -/
theorem klBin_nonneg {q p : ℝ} (hq0 : 0 ≤ q) (hq1 : q ≤ 1) (hp0 : 0 < p) (hp1 : p < 1) :
    0 ≤ klBin q p := by
  unfold klBin
  have hp1' : 0 < 1 - p := sub_pos.2 hp1
  rcases eq_or_lt_of_le hq0 with rfl | hq0'
  · simp only [zero_mul, zero_add, sub_zero, one_mul]
    exact Real.log_nonneg ((one_le_div hp1').2 (by linarith))
  rcases eq_or_lt_of_le hq1 with rfl | hq1'
  · simp only [sub_self, zero_mul, add_zero, one_mul]
    exact Real.log_nonneg ((one_le_div hp0).2 hp1.le)
  have h1q : 0 < 1 - q := sub_pos.2 hq1'
  have e1 : Real.log (q / p) = -Real.log (p / q) := by rw [← Real.log_inv, inv_div]
  have e2 : Real.log ((1 - q) / (1 - p)) = -Real.log ((1 - p) / (1 - q)) := by
    rw [← Real.log_inv, inv_div]
  have b1 := mul_le_mul_of_nonneg_left (Real.log_le_sub_one_of_pos (div_pos hp0 hq0')) hq0'.le
  have b2 := mul_le_mul_of_nonneg_left
    (Real.log_le_sub_one_of_pos (div_pos hp1' h1q)) h1q.le
  have key : q * (p / q - 1) + (1 - q) * ((1 - p) / (1 - q) - 1) = 0 := by
    field_simp
    ring
  rw [e1, e2]
  linarith

/-- The strict half of Gibbs: a forecast other than the truth has positive divergence. -/
theorem klBin_pos {q p : ℝ} (hq0 : 0 ≤ q) (hq1 : q ≤ 1) (hp0 : 0 < p) (hp1 : p < 1)
    (hne : q ≠ p) : 0 < klBin q p := by
  unfold klBin
  have hp1' : 0 < 1 - p := sub_pos.2 hp1
  rcases eq_or_lt_of_le hq0 with rfl | hq0'
  · simp only [zero_mul, zero_add, sub_zero, one_mul]
    exact Real.log_pos ((one_lt_div hp1').2 (by linarith))
  rcases eq_or_lt_of_le hq1 with rfl | hq1'
  · simp only [sub_self, zero_mul, add_zero, one_mul]
    exact Real.log_pos ((one_lt_div hp0).2 hp1)
  have h1q : 0 < 1 - q := sub_pos.2 hq1'
  have e1 : Real.log (q / p) = -Real.log (p / q) := by rw [← Real.log_inv, inv_div]
  have e2 : Real.log ((1 - q) / (1 - p)) = -Real.log ((1 - p) / (1 - q)) := by
    rw [← Real.log_inv, inv_div]
  have hne' : p / q ≠ 1 := fun h ↦ hne ((div_eq_one_iff_eq hq0'.ne').1 h).symm
  have b1 := mul_lt_mul_of_pos_left (Real.log_lt_sub_one_of_pos (div_pos hp0 hq0') hne') hq0'
  have b2 := mul_le_mul_of_nonneg_left
    (Real.log_le_sub_one_of_pos (div_pos hp1' h1q)) h1q.le
  have key : q * (p / q - 1) + (1 - q) * ((1 - p) / (1 - q) - 1) = 0 := by
    field_simp
    ring
  rw [e1, e2]
  linarith

/-- GRW-2: no forecast is expected to grow faster than the truth, which attains `KL(q‖r)`. -/
theorem expectedAdvantage_le {x : Pair ℝ} (hx : x.Proper) {q : ℝ} (hq0 : 0 ≤ q) (hq1 : q ≤ 1) :
    expectedAdvantage q x ≤ klBin q x.r := by
  rw [expectedAdvantage_eq hx]
  linarith [klBin_nonneg hq0 hq1 hx.2.2.1 hx.2.2.2]

/-- GRW-2: the truthful forecast attains `KL(q‖r)`. -/
theorem expectedAdvantage_truth {x : Pair ℝ} (hx : x.Proper) :
    expectedAdvantage x.p x = klBin x.p x.r := by
  rw [expectedAdvantage_eq hx, klBin_self, sub_zero]

/-- GRW-2: every other forecast is expected to grow strictly slower than the truth. -/
theorem expectedAdvantage_lt {x : Pair ℝ} (hx : x.Proper) {q : ℝ} (hq0 : 0 ≤ q) (hq1 : q ≤ 1)
    (hne : q ≠ x.p) : expectedAdvantage q x < klBin q x.r := by
  rw [expectedAdvantage_eq hx]
  linarith [klBin_pos hq0 hq1 hx.2.2.1 hx.2.2.2 hne]

end Expectation

/-! ## GRW-3 Optimality among constant fractions -/

section Fraction

variable {p r f : ℝ}

/-- At the proportional fraction the factor on yes is `p/r`. -/
theorem one_add_proportional (hr0 : 0 < r) (hr1 : r < 1) :
    1 + proportionalFraction p r * (1 / r - 1) = p / r := by
  have hr1' : 1 - r ≠ 0 := (sub_pos.2 hr1).ne'
  unfold proportionalFraction
  field_simp
  ring

/-- At the proportional fraction the factor on no is `(1 − p)/(1 − r)`. -/
theorem one_sub_proportional (hr1 : r < 1) :
    1 - proportionalFraction p r = (1 - p) / (1 - r) := by
  have hr1' : 1 - r ≠ 0 := (sub_pos.2 hr1).ne'
  unfold proportionalFraction
  field_simp
  ring

/-- GRW-3: at the proportional fraction, the constant-fraction stake's factors are the
proportional stake's. -/
theorem stakeYes_proportional (hr0 : 0 < r) (hr1 : r < 1) (o : Bool) :
    stakeYes r (proportionalFraction p r) o = factor ⟨r, p⟩ o := by
  cases o <;> simp only [stakeYes, factor, likelihood, Bool.false_eq_true, ↓reduceIte]
  · exact one_sub_proportional hr1
  · exact one_add_proportional hr0 hr1

/-- The proportional fraction keeps both factors positive, for a proper pair. -/
theorem proportionalFraction_factors_pos (hr0 : 0 < r) (hr1 : r < 1) (hp0 : 0 < p)
    (hp1 : p < 1) :
    0 < 1 + proportionalFraction p r * (1 / r - 1) ∧ 0 < 1 - proportionalFraction p r := by
  rw [one_add_proportional hr0 hr1, one_sub_proportional hr1]
  exact ⟨div_pos hp0 hr0, div_pos (sub_pos.2 hp1) (sub_pos.2 hr1)⟩

/-- The proportional fraction lies in `[0, 1)` when the forecast is at least the reference and
below certainty: a stake on yes. -/
theorem proportionalFraction_mem (hr1 : r < 1) (hrp : r ≤ p) (hp1 : p < 1) :
    proportionalFraction p r ∈ Set.Ico 0 1 :=
  ⟨div_nonneg (sub_nonneg.2 hrp) (sub_nonneg.2 hr1.le),
    (div_lt_one (sub_pos.2 hr1)).2 (by linarith)⟩

/-- Below the reference the proportional fraction is negative: a stake on no. -/
theorem proportionalFraction_neg (hr1 : r < 1) (hpr : p < r) : proportionalFraction p r < 0 :=
  div_neg_of_neg_of_pos (sub_neg.2 hpr) (sub_pos.2 hr1)

/-- GRW-3: the expected log growth at the proportional fraction is the divergence of the belief
from the reference, `KL(p‖r)`. -/
theorem expectedLogGrowth_proportional (hr0 : 0 < r) (hr1 : r < 1) :
    expectedLogGrowth p r (proportionalFraction p r) = klBin p r := by
  rw [expectedLogGrowth, one_add_proportional hr0 hr1, one_sub_proportional hr1, klBin]

/-- GRW-3: with an edge, a belief other than the reference, the proportional stake's expected
log growth is positive. -/
theorem expectedLogGrowth_proportional_pos (hr0 : 0 < r) (hr1 : r < 1) (hp0 : 0 ≤ p)
    (hp1 : p ≤ 1) (hne : p ≠ r) : 0 < expectedLogGrowth p r (proportionalFraction p r) := by
  rw [expectedLogGrowth_proportional hr0 hr1]
  exact klBin_pos hp0 hp1 hr0 hr1 hne

/-- GRW-3, the maximizer: among the constant fractions on yes that keep both factors positive,
the expected log growth under belief `p` is largest at the proportional fraction. The domain is
the one `lean-ergodicity`'s `kelly_optimal` uses; a fraction of `1` or more is ruin on a no
(`stakeYes_one_false`), which the log does not represent, and a negative fraction is the mirror
stake on no (`expectedLogGrowth_mirror`). -/
theorem expectedLogGrowth_le (hr0 : 0 < r) (hr1 : r < 1) (hp0 : 0 < p) (hp1 : p < 1)
    (hY : 0 < 1 + f * (1 / r - 1)) (hN : 0 < 1 - f) :
    expectedLogGrowth p r f ≤ expectedLogGrowth p r (proportionalFraction p r) := by
  have h1p : 0 < 1 - p := sub_pos.2 hp1
  have h1r : 0 < 1 - r := sub_pos.2 hr1
  have hY' : 0 < p / r := div_pos hp0 hr0
  have hN' : 0 < (1 - p) / (1 - r) := div_pos h1p h1r
  rw [expectedLogGrowth_proportional hr0 hr1, klBin, expectedLogGrowth]
  have b1 : p * (Real.log (1 + f * (1 / r - 1)) - Real.log (p / r)) ≤
      p * ((1 + f * (1 / r - 1)) / (p / r) - 1) := by
    rw [← Real.log_div hY.ne' hY'.ne']
    exact mul_le_mul_of_nonneg_left (Real.log_le_sub_one_of_pos (div_pos hY hY')) hp0.le
  have b2 : (1 - p) * (Real.log (1 - f) - Real.log ((1 - p) / (1 - r))) ≤
      (1 - p) * ((1 - f) / ((1 - p) / (1 - r)) - 1) := by
    rw [← Real.log_div hN.ne' hN'.ne']
    exact mul_le_mul_of_nonneg_left (Real.log_le_sub_one_of_pos (div_pos hN hN')) h1p.le
  have key : p * ((1 + f * (1 / r - 1)) / (p / r) - 1) +
      (1 - p) * ((1 - f) / ((1 - p) / (1 - r)) - 1) = 0 := by
    field_simp
    ring
  linarith

/-- GRW-3, the boundary: the whole holding on yes is lost on a no. -/
theorem stakeYes_one_false (r : ℝ) : stakeYes r 1 false = 0 := by
  simp [stakeYes]

/-- GRW-3, the derivative in `f`, wherever neither factor vanishes. -/
theorem hasDerivAt_expectedLogGrowth (hY : 1 + f * (1 / r - 1) ≠ 0) (hN : 1 - f ≠ 0) :
    HasDerivAt (expectedLogGrowth p r)
      (p * ((1 / r - 1) / (1 + f * (1 / r - 1))) + (1 - p) * (-1 / (1 - f))) f := by
  have d1 : HasDerivAt (fun y : ℝ ↦ 1 + y * (1 / r - 1)) (1 / r - 1) f := by
    simpa using ((hasDerivAt_id f).mul_const (1 / r - 1)).const_add 1
  have d2 : HasDerivAt (fun y : ℝ ↦ 1 - y) (-1) f := by
    simpa using (hasDerivAt_id f).const_sub 1
  exact ((d1.log hY).const_mul p).add ((d2.log hN).const_mul (1 - p))

/-- GRW-3, the derivative's zero: at the proportional fraction the derivative vanishes. -/
theorem hasDerivAt_expectedLogGrowth_proportional (hr0 : 0 < r) (hr1 : r < 1) (hp0 : 0 < p)
    (hp1 : p < 1) : HasDerivAt (expectedLogGrowth p r) 0 (proportionalFraction p r) := by
  have h1p : 1 - p ≠ 0 := (sub_pos.2 hp1).ne'
  have h1r : 1 - r ≠ 0 := (sub_pos.2 hr1).ne'
  obtain ⟨hY, hN⟩ := proportionalFraction_factors_pos hr0 hr1 hp0 hp1
  refine (hasDerivAt_expectedLogGrowth hY.ne' hN.ne').congr_deriv ?_
  rw [one_add_proportional hr0 hr1, one_sub_proportional hr1]
  field_simp
  ring

/-- Where both factors are positive: the open interval `(−r/(1 − r), 1)`. -/
theorem factors_pos_of_mem (hr0 : 0 < r) (hr1 : r < 1) (hf : f ∈ Set.Ioo (-(r / (1 - r))) 1) :
    0 < 1 + f * (1 / r - 1) ∧ 0 < 1 - f := by
  have h1r : 0 < 1 - r := sub_pos.2 hr1
  have hlo : -r < f * (1 - r) := by
    have := hf.1
    rwa [← neg_div, div_lt_iff₀ h1r] at this
  refine ⟨?_, sub_pos.2 hf.2⟩
  have e : 1 + f * (1 / r - 1) = (r + f * (1 - r)) / r := by
    field_simp
  rw [e]
  exact div_pos (by linarith) hr0

/-- GRW-3, concavity: the expected log growth is concave in the fraction where both factors are
positive, for any belief `p ∈ [0, 1]` and reference `r ∈ (0, 1)`. -/
theorem concaveOn_expectedLogGrowth (hp0 : 0 ≤ p) (hp1 : p ≤ 1) (hr0 : 0 < r) (hr1 : r < 1) :
    ConcaveOn ℝ (Set.Ioo (-(r / (1 - r))) 1) (expectedLogGrowth p r) := by
  have hlog := strictConcaveOn_log_Ioi.concaveOn
  refine ⟨convex_Ioo _ _, fun x hx y hy a b ha0 hb0 hab ↦ ?_⟩
  obtain ⟨hYx, hNx⟩ := factors_pos_of_mem hr0 hr1 hx
  obtain ⟨hYy, hNy⟩ := factors_pos_of_mem hr0 hr1 hy
  have h1 := hlog.2 (Set.mem_Ioi.2 hYx) (Set.mem_Ioi.2 hYy) ha0 hb0 hab
  have h2 := hlog.2 (Set.mem_Ioi.2 hNx) (Set.mem_Ioi.2 hNy) ha0 hb0 hab
  simp only [smul_eq_mul] at h1 h2 ⊢
  have e1 : a * (1 + x * (1 / r - 1)) + b * (1 + y * (1 / r - 1)) =
      1 + (a * x + b * y) * (1 / r - 1) := by linear_combination hab
  have e2 : a * (1 - x) + b * (1 - y) = 1 - (a * x + b * y) := by linear_combination hab
  rw [e1] at h1
  rw [e2] at h2
  simp only [expectedLogGrowth]
  have c1 := mul_le_mul_of_nonneg_left h1 hp0
  have c2 := mul_le_mul_of_nonneg_left h2 (sub_nonneg.2 hp1)
  linarith

/-- The mirror stake on no at fraction `f`, `stakeYes (1 − r) f` on the negated outcome, is the
stake on yes at the negative fraction `−f r/(1 − r)`. -/
theorem stakeYes_mirror (hr0 : 0 < r) (hr1 : r < 1) (o : Bool) :
    stakeYes (1 - r) f (!o) = stakeYes r (-(f * r / (1 - r))) o := by
  have h1r : 1 - r ≠ 0 := (sub_pos.2 hr1).ne'
  cases o <;> simp only [stakeYes, Bool.not_false, Bool.not_true, Bool.false_eq_true, ↓reduceIte]
  · field_simp
    ring
  · field_simp
    ring

/-- The mirror stake's expected log growth is the yes-stake's at the negative fraction. -/
theorem expectedLogGrowth_mirror (hr0 : 0 < r) (hr1 : r < 1) :
    expectedLogGrowth (1 - p) (1 - r) f = expectedLogGrowth p r (-(f * r / (1 - r))) := by
  have h1r : 1 - r ≠ 0 := (sub_pos.2 hr1).ne'
  have e1 : 1 + -(f * r / (1 - r)) * (1 / r - 1) = 1 - f := by
    field_simp
    ring
  have e2 : 1 + f * (1 / (1 - r) - 1) = 1 - -(f * r / (1 - r)) := by
    field_simp
    ring
  rw [expectedLogGrowth, expectedLogGrowth, e1, e2, sub_sub_cancel]
  ring

theorem proportionalFraction_mirror : proportionalFraction (1 - p) (1 - r) = (r - p) / r := by
  unfold proportionalFraction
  congr 1 <;> ring

/-- GRW-3, the mirror: below the reference the stake on no at the fraction `(r − p)/r` is the
maximizer among the mirror stakes that keep both factors positive, and its factors are the
proportional stake's. -/
theorem expectedLogGrowth_mirror_le (hr0 : 0 < r) (hr1 : r < 1) (hp0 : 0 < p) (hp1 : p < 1)
    (hY : 0 < 1 + f * (1 / (1 - r) - 1)) (hN : 0 < 1 - f) :
    expectedLogGrowth (1 - p) (1 - r) f ≤
      expectedLogGrowth (1 - p) (1 - r) (proportionalFraction (1 - p) (1 - r)) :=
  expectedLogGrowth_le (by linarith) (by linarith) (by linarith) (by linarith) hY hN

/-- The mirror stake at its proportional fraction has the proportional stake's factors. -/
theorem stakeYes_mirror_proportional (hr0 : 0 < r) (hr1 : r < 1) (o : Bool) :
    stakeYes (1 - r) (proportionalFraction (1 - p) (1 - r)) (!o) = factor ⟨r, p⟩ o := by
  rw [stakeYes_proportional (by linarith) (by linarith), factor, factor, likelihood_compl,
    likelihood_compl]

end Fraction

/-! ## GRW-6 The time average -/

section TimeAverage

open MeasureTheory ProbabilityTheory Filter Topology unitInterval Function

/-- The sequence of one pair `x` with the first `n` outcomes of `o`. -/
def upTo (x : Pair ℝ) (o : ℕ → Bool) (n : ℕ) : List (Pair ℝ × Bool) :=
  (List.range n).map fun i ↦ (x, o i)

theorem cumulative_upTo (x : Pair ℝ) (o : ℕ → Bool) (n : ℕ) :
    cumulative (upTo x o n) = ∑ i ∈ Finset.range n, advantage x (o i) := by
  induction n with
  | zero => simp [upTo, cumulative]
  | succ n ih =>
    rw [upTo, List.range_succ, List.map_append, cumulative, List.map_append, List.sum_append,
      Finset.sum_range_succ, ← ih]
    simp [upTo, cumulative]

theorem upTo_proper {x : Pair ℝ} (hx : x.Proper) (o : ℕ → Bool) (n : ℕ) :
    ∀ s ∈ upTo x o n, s.1.Proper := by
  intro s hs
  obtain ⟨i, -, rfl⟩ := List.mem_map.1 hs
  exact hx

/-- A sequence whose average tends to a positive number tends to `+∞`
(`lean-ergodicity`'s `tendsto_atTop_of_div_tendsto_pos`). -/
theorem tendsto_atTop_of_div_tendsto_pos {a : ℕ → ℝ} {c : ℝ} (hc : 0 < c)
    (h : Tendsto (fun n : ℕ ↦ a n / n) atTop (𝓝 c)) : Tendsto a atTop atTop := by
  refine (h.pos_mul_atTop hc tendsto_natCast_atTop_atTop).congr' ?_
  filter_upwards [eventually_ne_atTop 0] with n hn
  have : (n : ℝ) ≠ 0 := by exact_mod_cast hn
  field_simp

/-- A sequence whose average tends to a negative number tends to `−∞`. -/
theorem tendsto_atBot_of_div_tendsto_neg {a : ℕ → ℝ} {c : ℝ} (hc : c < 0)
    (h : Tendsto (fun n : ℕ ↦ a n / n) atTop (𝓝 c)) : Tendsto a atTop atBot := by
  refine (h.neg_mul_atTop hc tendsto_natCast_atTop_atTop).congr' ?_
  filter_upwards [eventually_ne_atTop 0] with n hn
  have : (n : ℝ) ≠ 0 := by exact_mod_cast hn
  field_simp

variable {Ω : Type*} [MeasurableSpace Ω] {μ : Measure Ω} {q : I}

/-- GRW-6: on one pair whose outcomes are pairwise independent and each yes with probability
`q`, the time-average advantage converges almost surely to the expected advantage, by the strong
law of large numbers. This is the stationary case, one question type repeated; the ledger's
questions differ, and the strong law for independent summands that are not identically
distributed is the next rung. -/
theorem time_average_advantage_ae (x : Pair ℝ) (o : ℕ → Ω → Bool)
    (hlaw : ∀ i, HasLaw (o i) (bernoulliMeasure true false q) μ)
    (hindep : Pairwise fun i j ↦ IndepFun (o i) (o j) μ) :
    ∀ᵐ ω ∂μ, Tendsto (fun n : ℕ ↦ cumulative (upTo x (fun i ↦ o i ω) n) / n) atTop
      (𝓝 (expectedAdvantage q x)) := by
  have hm : Measurable (advantage x) := measurable_of_finite _
  set X : ℕ → Ω → ℝ := fun i ↦ advantage x ∘ o i with hX
  have hint : Integrable (X 0) μ :=
    (hlaw 0).integrable_comp (f := advantage x) (integrable_bernoulliMeasure _ _ _ _)
  have hind : Pairwise ((· ⟂ᵢ[μ] ·) on X) := fun i j hij ↦ (hindep hij).comp hm hm
  have hid : ∀ i, IdentDistrib (X i) (X 0) μ μ := fun i ↦
    (⟨(hlaw i).aemeasurable, (hlaw 0).aemeasurable, by rw [(hlaw i).map_eq, (hlaw 0).map_eq]⟩ :
      IdentDistrib (o i) (o 0) μ μ).comp hm
  have hexp : μ[X 0] = expectedAdvantage q x := by
    rw [hX, (hlaw 0).integral_comp (f := advantage x) hm.aestronglyMeasurable,
      integral_bernoulliMeasure, expectedAdvantage]
    simp [smul_eq_mul]
  have := strong_law_ae_real X hint hind hid
  rw [hexp] at this
  filter_upwards [this] with ω hω
  simpa [hX, cumulative_upTo] using hω

/-- GRW-6: with a positive expected advantage the holding grows without bound almost surely, so
it reaches `N` times its start for every `N`: the path exists. -/
theorem holding_tendsto_atTop_ae {x : Pair ℝ} (hx : x.Proper) {w0 : ℝ} (hw : 0 < w0)
    (o : ℕ → Ω → Bool) (hlaw : ∀ i, HasLaw (o i) (bernoulliMeasure true false q) μ)
    (hindep : Pairwise fun i j ↦ IndepFun (o i) (o j) μ) (hpos : 0 < expectedAdvantage q x) :
    ∀ᵐ ω ∂μ, Tendsto (fun n : ℕ ↦ holding w0 (upTo x (fun i ↦ o i ω) n)) atTop atTop := by
  filter_upwards [time_average_advantage_ae x o hlaw hindep] with ω hω
  have hlog := tendsto_atTop_of_div_tendsto_pos hpos hω
  have hexp := (Real.tendsto_exp_atTop.comp hlog).const_mul_atTop hw
  refine hexp.congr fun n ↦ ?_
  rw [holding_eq w0 (upTo_proper hx _ n)]
  rfl

/-- GRW-6: with a negative expected advantage the holding tends to zero almost surely. -/
theorem holding_tendsto_zero_ae {x : Pair ℝ} (hx : x.Proper) (w0 : ℝ) (o : ℕ → Ω → Bool)
    (hlaw : ∀ i, HasLaw (o i) (bernoulliMeasure true false q) μ)
    (hindep : Pairwise fun i j ↦ IndepFun (o i) (o j) μ) (hneg : expectedAdvantage q x < 0) :
    ∀ᵐ ω ∂μ, Tendsto (fun n : ℕ ↦ holding w0 (upTo x (fun i ↦ o i ω) n)) atTop (𝓝 0) := by
  filter_upwards [time_average_advantage_ae x o hlaw hindep] with ω hω
  have hlog := tendsto_atBot_of_div_tendsto_neg hneg hω
  have hexp := (Real.tendsto_exp_atBot.comp hlog).const_mul w0
  rw [mul_zero] at hexp
  refine hexp.congr fun n ↦ ?_
  rw [holding_eq w0 (upTo_proper hx _ n)]
  rfl

end TimeAverage

end Palace.Growth
