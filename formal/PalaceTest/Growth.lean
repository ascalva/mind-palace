module

public import Palace.Growth
public import PalaceTest.Attack
public meta import Palace.Growth
public meta import PalaceTest.Attack

/-!
# Attacks on `Palace.Growth`

The Plausible attacks and negative controls for the laws of `Palace/Growth.lean`, on exact
shadows over ℚ: a pair's two probabilities are `(a + 1)/(a + b + 2)` and `(c + 1)/(c + d + 2)`
from naturals, so every pair is proper, and a sequence is a list of such pairs with outcomes.
The logs do not run, so GRW-1 is attacked in its product form, the likelihood ratio, GRW-3 on the
algebra of its maximizer (the constant-fraction stake at the proportional fraction has the
proportional stake's factors), GRW-4 on a factor's bounds and GRW-5 on positivity and the power of
the worst factor. The controls are the natural mistakes: a growth read without the reference, the
half stake claimed to satisfy the identity, the fraction `p` itself ("stake your probability")
claimed to be the proportional stake, a factor bounded by `1/r` alone, and the leveraged stake
`λ = 2`, which can lose everything and more. They run when this module builds (`lake test`).
-/

@[expose] public section

namespace Palace.Growth.Attack

/-- A proper pair from four naturals: `r = (a + 1)/(a + b + 2)`, `p = (c + 1)/(c + d + 2)`. -/
def mkPair (a b c d : ℕ) : Pair ℚ :=
  ⟨((a : ℚ) + 1) / ((a : ℚ) + b + 2), ((c : ℚ) + 1) / ((c : ℚ) + d + 2)⟩

/-- A sequence of scored pairs with outcomes, from a list of codes. -/
def seq (l : List (ℕ × ℕ × ℕ × ℕ × Bool)) : List (Pair ℚ × Bool) :=
  l.map fun s ↦ (mkPair s.1 s.2.1 s.2.2.1 s.2.2.2.1, s.2.2.2.2)

/-- The constant-fraction stake on yes, over ℚ: `1 + f (1/r − 1)` on yes, `1 − f` on no. -/
def stakeQ (r f : ℚ) (o : Bool) : ℚ := if o then 1 + f * (1 / r - 1) else 1 - f

/-- The proportional fraction over ℚ. -/
def fracQ (p r : ℚ) : ℚ := (p - r) / (1 - r)

/-- The least worst factor over a sequence, `1` on the empty one. -/
def floorOf (l : List (Pair ℚ × Bool)) : ℚ := (l.map fun s ↦ worstFactor s.1).foldr min 1

/- GRW-1: the growth is the likelihood ratio. -/
#eval survives (∀ l : List (ℕ × ℕ × ℕ × ℕ × Bool),
  growth (seq l) = ((seq l).map fun s ↦ likelihood s.1.p s.2).prod /
    ((seq l).map fun s ↦ likelihood s.1.r s.2).prod) 320

/- GRW-1, without the division: the growth times the reference's likelihood is the arm's. -/
#eval survives (∀ l : List (ℕ × ℕ × ℕ × ℕ × Bool),
  growth (seq l) * ((seq l).map fun s ↦ likelihood s.1.r s.2).prod =
    ((seq l).map fun s ↦ likelihood s.1.p s.2).prod) 321

/- GRW-1 control: a reference-free reading, the arm's likelihood alone. -/
#eval refuted (∀ l : List (ℕ × ℕ × ℕ × ℕ × Bool),
  growth (seq l) = ((seq l).map fun s ↦ likelihood s.1.p s.2).prod) 322

/- GRW-1 control: the half stake does not satisfy the identity. -/
#eval refuted (∀ l : List (ℕ × ℕ × ℕ × ℕ × Bool),
  fractionalGrowth (1 / 2) (seq l) = growth (seq l)) 323

/- GRW-3: at the proportional fraction the constant-fraction stake's factors are the
proportional stake's, on either outcome. -/
#eval survives (∀ a b c d : ℕ, ∀ o : Bool,
  stakeQ (mkPair a b c d).r (fracQ (mkPair a b c d).p (mkPair a b c d).r) o =
    factor (mkPair a b c d) o) 324

/- GRW-3 control: the fraction `p` itself is not the proportional stake. -/
#eval refuted (∀ a b c d : ℕ, ∀ o : Bool,
  stakeQ (mkPair a b c d).r (mkPair a b c d).p o = factor (mkPair a b c d) o) 325

/- GRW-4: a factor lies between the margin and its reciprocal. -/
#eval survives (∀ a b c d : ℕ, ∀ o : Bool,
  margin (mkPair a b c d) ≤ factor (mkPair a b c d) o ∧
    factor (mkPair a b c d) o ≤ 1 / margin (mkPair a b c d)) 326

/- GRW-4 control: `1/r` alone does not bound a factor. -/
#eval refuted (∀ a b c d : ℕ, ∀ o : Bool,
  factor (mkPair a b c d) o ≤ 1 / (mkPair a b c d).r) 327

/- GRW-5: the growth is positive, and at least the power of the least worst factor. -/
#eval survives (∀ l : List (ℕ × ℕ × ℕ × ℕ × Bool),
  0 < growth (seq l) ∧ floorOf (seq l) ^ (seq l).length ≤ growth (seq l)) 328

/- GRW-5 control: the leveraged stake `λ = 2` is not always positive. -/
#eval refuted (∀ l : List (ℕ × ℕ × ℕ × ℕ × Bool), 0 < fractionalGrowth 2 (seq l)) 329

end Palace.Growth.Attack
