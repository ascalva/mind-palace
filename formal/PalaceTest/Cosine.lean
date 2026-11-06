module

public import Palace.Cosine
public import Mathlib.Testing.Plausible.Sampleable
public import PalaceTest.Attack
public meta import Palace.Cosine
public meta import Mathlib.Testing.Plausible.Sampleable
public meta import PalaceTest.Attack

/-!
# Attacks on `Palace.Cosine`

The parts of VEC-1 with an exact instance, attacked over `ℚ`: the coordinate bound of binary16
rounding, on rationals from far below the least subnormal to `2¹⁶`, and the margin certificate,
on six scores perturbed within `β`. The cosine bounds take square roots and have no exact
instance; `tests/property/test_float16_margin.py` attacks them in float64.
-/

@[expose] public section

namespace Palace.Cosine

namespace Attack

open Plausible Palace.Format

/-- A rational `m · 2^e` at binary16's scale: `|m| < 2^24`, `e` from `−50` to `−8`. -/
structure Num where
  m : ℤ
  e : ℤ

instance : Repr Num where
  reprPrec x _ := s!"{x.m} * 2^{x.e}"

instance : Shrinkable Num := ⟨fun _ ↦ []⟩

instance : Arbitrary Num where
  arbitrary := do
    let s := (← Gen.choose Nat 0 1 (by omega)).1
    let m := (← Gen.choose Nat 0 (2 ^ 24 - 1) (by omega)).1
    let e := (← Gen.choose Nat 0 42 (by omega)).1
    return ⟨(if s = 1 then -1 else 1) * (m : ℤ), (e : ℤ) - 50⟩

/-- The value `m · 2^e`. -/
def Num.val (x : Num) : ℚ := x.m * 2 ^ x.e

/-- `|rn16 x − x| ≤ c · max |x| floor`. -/
def coordBound (c floor : ℚ) (x : ℚ) : Bool := decide (|rn16 x - x| ≤ c * max |x| floor)

/- VEC-1's coordinate bound, `2⁻¹¹ · max |x| 2⁻¹⁴`. -/
#eval survives (∀ x : Num, coordBound (2 ^ (-11 : ℤ)) (2 ^ (-14 : ℤ)) x.val = true) 304
/- Controls: the relative bound alone fails below the normal range; half the bound fails at
ties near the bottom of a binade. -/
#eval refuted (∀ x : Num, coordBound (2 ^ (-11 : ℤ)) 0 x.val = true) 305
#eval refuted (∀ x : Num, coordBound (2 ^ (-12 : ℤ)) (2 ^ (-14 : ℤ)) x.val = true) 306
/-- Six scores in tenths, a perturbation of each in halves of `β`, `β` in twentieths, and the size
`k` of the top set. -/
structure Ranking where
  s : List ℚ
  δ : List ℚ
  β : ℚ
  k : ℕ

instance : Repr Ranking where
  reprPrec r _ := s!"s {r.s}, δ {r.δ}, β {r.β}, k {r.k}"

instance : Shrinkable Ranking := ⟨fun _ ↦ []⟩

instance : Arbitrary Ranking where
  arbitrary := do
    let mut s : List ℚ := []
    let mut δ : List ℚ := []
    for _ in List.range 6 do
      s := s ++ [((← Gen.choose Nat 0 10 (by omega)).1 : ℚ) / 10]
      δ := δ ++ [(((← Gen.choose Nat 0 4 (by omega)).1 : ℚ) - 2) / 2]
    let β := ((← Gen.choose Nat 1 10 (by omega)).1 : ℚ) / 20
    let k := (← Gen.choose Nat 1 5 (by omega)).1
    return ⟨s, δ, β, k⟩

/-- The scores, the true scores `t = s + β δ` (within `β` of `s`), and the top `k` of `s` by
score, ties to the lower index, with the rest. -/
def Ranking.score (r : Ranking) (i : ℕ) : ℚ := r.s.getD i 0

def Ranking.truth (r : Ranking) (i : ℕ) : ℚ := r.score i + r.β * r.δ.getD i 0

def Ranking.order (r : Ranking) : List ℕ :=
  (List.range 6).mergeSort fun i j ↦
    decide (r.score j < r.score i) || (decide (r.score i = r.score j) && decide (i ≤ j))

/-- Every member of the top `k` beats every other score by more than `c · β`. -/
def Ranking.margin (c : ℚ) (r : Ranking) : Bool :=
  (r.order.take r.k).all fun i ↦ (r.order.drop r.k).all fun j ↦
    decide (r.score j + c * r.β < r.score i)

/-- Under the true scores every member of the top `k` still beats every other. -/
def Ranking.stays (r : Ranking) : Bool :=
  (r.order.take r.k).all fun i ↦ (r.order.drop r.k).all fun j ↦
    decide (r.truth j < r.truth i)

/- VEC-1's certificate: a margin over `2β` keeps the top set. -/
#eval survives (∀ r : Ranking, r.margin 2 = true → r.stays = true) 307
/- Control: a margin over `β` alone does not. -/
#eval refuted (∀ r : Ranking, r.margin 1 = true → r.stays = true) 308
end Attack

end Palace.Cosine
