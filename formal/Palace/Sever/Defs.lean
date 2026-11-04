module

public import Palace.Sentence.Defs

/-!
# The sever horizon: the definitions

`assume sever S a b` is the rank-one update `L ↦ L − w (e_a − e_b)(e_a − e_b)ᵀ` (QSA-9), and the
pseudo-inverse's exact response is Sherman–Morrison with the denominator `1 − w·R_eff(a, b)`. The
laws of `Palace/Sever.lean` show the denominator never goes negative: the single edge on its own
has resistance `1/w`, and the rest of the graph can only lower it (the limits program's L1,
`docs/brainstorms/limits-of-the-algebra.md`). The one definition is the single-edge graph.
-/

@[expose] public section

open Matrix Finset

namespace Palace.Sever

variable {V : Type*} [DecidableEq V]

/-- The graph of one edge `a ~ b` of weight `w`, every other vertex isolated: the hypothetical
edge laid on the empty graph. -/
def single (a b : V) (w : ℝ) : Matrix V V ℝ := Query.assumeEdge 0 a b w

/-- `a ~ b` is the only edge across some cut: `a` on one side, `b` on the other, every other
pair across it unconnected — the edge is a bridge, and severing it disconnects. -/
def IsBridgeCut (A : Matrix V V ℝ) (a b : V) : Prop :=
  ∃ S : Finset V, a ∈ S ∧ b ∉ S ∧ ∀ i ∈ S, ∀ j ∉ S, (i = a ∧ j = b) ∨ A i j = 0

end Palace.Sever
