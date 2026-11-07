module

public import Palace.Growth.Defs

/-!
# The growth readout: GRW-1, the statements

`eval/predictions/scoring.py`'s `growth` reports, per arm against the reference arm, the growth of
a proportional stake over the scored pairs, `p/r` on yes and `(1 − p)/(1 − r)` on no, and relies
on the identity that this growth is the exponential of the cumulative log-score advantage of the
arm over the reference, the quantity the ledger already scores.

These are the theorems of `Palace/Growth.lean` as the ledger cites them, each with its proof left
as `sorry`. `lake comparator` checks that the `Palace` library proves each one exactly as stated
here, from the standard axioms alone. The design theorems GRW-2 to GRW-5 (the expectation under a
truth, optimality among constant fractions, the path to `N×`, no ruin) have no statements here:
no code relies on them.
-/

@[expose] public section

namespace Palace.Growth

variable {K : Type*}

section Product

variable [Field K]

/-- **GRW-1** The product form, free of logs: over any field, the growth is the likelihood ratio
of the outcomes under the arm's forecasts and under the reference's. -/
theorem growth_eq_div (l : List (Pair K × Bool)) :
    growth l = (l.map fun s ↦ likelihood s.1.p s.2).prod /
      (l.map fun s ↦ likelihood s.1.r s.2).prod :=
  sorry

/-- **GRW-1** The fractional stake at `λ = 1` is the proportional stake, so the identity holds of
the readout's full stake and of it alone. -/
theorem fractionalGrowth_one (l : List (Pair K × Bool)) : fractionalGrowth 1 l = growth l :=
  sorry

end Product

section Log

/-- **GRW-1** The identity: over proper pairs, the log of the growth is the cumulative log-score
advantage of the arm over the reference. -/
theorem log_growth {l : List (Pair ℝ × Bool)} (h : ∀ s ∈ l, s.1.Proper) :
    Real.log (growth l) = cumulative l :=
  sorry

/-- **GRW-1** The holding is the start times the exponential of the cumulative advantage. -/
theorem holding_eq (w0 : ℝ) {l : List (Pair ℝ × Bool)} (h : ∀ s ∈ l, s.1.Proper) :
    holding w0 l = w0 * Real.exp (cumulative l) :=
  sorry

end Log

end Palace.Growth
