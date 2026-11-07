module

public import Mathlib.Analysis.SpecialFunctions.Log.Basic

/-!
# The growth readout: GRW-1, the definitions

The definitions the laws of `Palace/Growth.lean` are stated over, mirroring
`eval/predictions/scoring.py`'s `growth`: the proportional stake the scorer computes as a thought
experiment against a reference arm, on the ledger's scored pairs. With `Spec/Growth.lean` they
are what a reader checks against `docs/LAWS.md`: `lake comparator` ensures the library proves
exactly the statements there, so no other file can change what is proved.

A scored pair is a reference probability `r` and a forecast `p` that a yes/no question resolves
yes, with its outcome `o`. The proportional stake multiplies its holding by `p/r` on yes and by
`(1 − p)/(1 − r)` on no: the stake that moves the fraction of the holding on yes from `r` to `p`.
The thought experiment's own quantities (the expectation under a truth `q`, the constant-fraction
stakes, the worst factor) are defined here too, so that the design theorems of
`Palace/Growth.lean` are stated over the one model.
-/

@[expose] public section

namespace Palace.Growth

/-- One scored pair's two probabilities of yes: the reference's `r` and the arm's forecast `p`. -/
structure Pair (K : Type*) where
  /-- The reference arm's probability of yes. -/
  r : K
  /-- The arm's forecast of yes. -/
  p : K

variable {K : Type*}

/-- The probability a forecast `p` gives the outcome `o`: `p` on yes, `1 − p` on no. -/
def likelihood [Ring K] (p : K) (o : Bool) : K := if o then p else 1 - p

/-- The proportional stake's factor on one pair: `p/r` on yes, `(1 − p)/(1 − r)` on no. -/
def factor [Field K] (x : Pair K) (o : Bool) : K := likelihood x.p o / likelihood x.r o

/-- The stake's growth over a sequence of scored pairs with their outcomes: the product of the
factors, what `scoring.py`'s `growth` computes at the full stake. -/
def growth [Field K] (l : List (Pair K × Bool)) : K := (l.map fun s ↦ factor s.1 s.2).prod

/-- The holding after the sequence, from `w0`. -/
def holding [Field K] (w0 : K) (l : List (Pair K × Bool)) : K := w0 * growth l

/-- The fractional stake `λ`: the factor `1 + λ (F − 1)` for each full-stake factor `F`, the
cautious practice the readout also reports; `λ = 1` is the proportional stake. -/
def fractional [Field K] (lam : K) (x : Pair K) (o : Bool) : K := 1 + lam * (factor x o - 1)

/-- The fractional stake's growth over a sequence. -/
def fractionalGrowth [Field K] (lam : K) (l : List (Pair K × Bool)) : K :=
  (l.map fun s ↦ fractional lam s.1 s.2).prod

/-- The log score of a forecast `p` on the outcome `o`, as the ledger scores it: `log p` on yes,
`log (1 − p)` on no (`scoring.py`'s `log_loss` is its negative). -/
noncomputable def logScore (p : ℝ) (o : Bool) : ℝ := Real.log (likelihood p o)

/-- The arm's log-score advantage over the reference on one pair. -/
noncomputable def advantage (x : Pair ℝ) (o : Bool) : ℝ := logScore x.p o - logScore x.r o

/-- The cumulative advantage over a sequence: the quantity the ledger's two mean log scores
already measure, summed. -/
noncomputable def cumulative (l : List (Pair ℝ × Bool)) : ℝ :=
  (l.map fun s ↦ advantage s.1 s.2).sum

/-- A proper pair: both probabilities strictly between `0` and `1`, as the clipped probabilities
the log score reads are. -/
def Pair.Proper [Field K] [LinearOrder K] (x : Pair K) : Prop :=
  0 < x.r ∧ x.r < 1 ∧ 0 < x.p ∧ x.p < 1

/-- The margin of a pair: the smallest of `p`, `1 − p`, `r` and `1 − r`. -/
def margin [Field K] [LinearOrder K] (x : Pair K) : K :=
  min (min x.p (1 - x.p)) (min x.r (1 - x.r))

/-- The worst factor of a pair: the smaller of its two, the one its adverse outcome applies. -/
def worstFactor [Field K] [LinearOrder K] (x : Pair K) : K :=
  min (factor x true) (factor x false)

/-! ## The thought experiment's expectation -/

/-- The expected advantage of one pair when its outcome is yes with probability `q`. -/
noncomputable def expectedAdvantage (q : ℝ) (x : Pair ℝ) : ℝ :=
  q * advantage x true + (1 - q) * advantage x false

/-- The binary Kullback–Leibler divergence of the truth `q` from a forecast `p`,
`q log (q/p) + (1 − q) log ((1 − q)/(1 − p))`, with Lean's `log 0 = 0` giving `0 log 0 = 0`.
Mathlib's `InformationTheory.klDiv` is the divergence of one measure from another; this is its
value on two Bernoulli laws, written out, which is all the thought experiment needs. -/
noncomputable def klBin (q p : ℝ) : ℝ :=
  q * Real.log (q / p) + (1 - q) * Real.log ((1 - q) / (1 - p))

/-- A question of the thought experiment: a scored pair with the probability `q` that its outcome
is yes. -/
structure Question where
  /-- The scored pair: the reference's probability and the arm's forecast. -/
  pair : Pair ℝ
  /-- The probability that the outcome is yes. -/
  q : ℝ

/-- The expectation of a function of the outcomes when each question's outcome is yes with its
own probability, independently of the others: the tree of the two outcomes of the first question,
each weighted, over the rest. -/
noncomputable def expect : List Question → (List Bool → ℝ) → ℝ
  | [], f => f []
  | x :: xs, f =>
    x.q * expect xs (fun os ↦ f (true :: os)) + (1 - x.q) * expect xs (fun os ↦ f (false :: os))

/-- The cumulative advantage of a sequence of questions on a list of outcomes. -/
noncomputable def cumulativeOn (xs : List Question) (os : List Bool) : ℝ :=
  cumulative (List.zip (xs.map Question.pair) os)

/-! ## The constant-fraction stakes -/

/-- A constant fraction `f` of the holding staked on yes at reference `r`: the factor
`1 + f (1/r − 1)` on yes and `1 − f` on no. The mirror stake on no is `stakeYes (1 − r) f` on the
negated outcome. -/
noncomputable def stakeYes (r f : ℝ) (o : Bool) : ℝ := if o then 1 + f * (1 / r - 1) else 1 - f

/-- The expected log growth of the fraction `f` on yes at reference `r` under belief `p`. -/
noncomputable def expectedLogGrowth (p r f : ℝ) : ℝ :=
  p * Real.log (1 + f * (1 / r - 1)) + (1 - p) * Real.log (1 - f)

/-- The proportional fraction on yes, `(p − r)/(1 − r)`: the one whose factors are the
proportional stake's. -/
noncomputable def proportionalFraction (p r : ℝ) : ℝ := (p - r) / (1 - r)

end Palace.Growth
