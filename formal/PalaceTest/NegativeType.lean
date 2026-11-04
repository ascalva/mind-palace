module

public import Palace.NegativeType
public import PalaceTest.Attack
public meta import Palace.NegativeType
public meta import PalaceTest.Attack

/-!
# Attacks on `Palace.NegativeType`

The Plausible attacks and negative controls for `Palace/NegativeType.lean`, run on its exact
shadow over ℚ on `Fin 5`: the form `Σ x_i x_j d_ij` of a vector summing to zero, the last entry
set to make the sum zero. They run when this module builds (`lake test`).
-/

@[expose] public section

open Finset

namespace Palace.NegativeType.Attack

/-- A vector on `Fin 5` summing to zero: four entries from a list, the fifth their negated sum. -/
def zeroSum (xs : List ℤ) : Fin 5 → ℚ := fun i ↦
  if i.val < 4 then xs.getD i.val 0 else -((List.range 4).map fun k ↦ (xs.getD k 0 : ℚ)).sum

/-- The form a vector reads off a distance, over ℚ. -/
def formQ (x : Fin 5 → ℚ) (d : Fin 5 → Fin 5 → ℚ) : ℚ := ∑ i, ∑ j, x i * x j * d i j

/- A squared line metric is of negative type. -/
#eval survives (∀ fs xs : List ℤ,
  formQ (zeroSum xs) (fun i j ↦ ((fs.getD i.val 0 : ℚ) - fs.getD j.val 0) ^ 2) ≤ 0) 216

/- Control: `K₂,₃`'s shortest-path metric is not. -/
#eval refuted (∀ xs : List ℤ, formQ (zeroSum xs) (fun i j ↦ (k23Dist i j : ℚ)) ≤ 0) 217

/- `C₅`'s metric is of negative type (its five vertices). -/
#eval survives (∀ xs : List ℤ, formQ (zeroSum xs) (fun i j ↦ (cycDist 5 i j : ℚ)) ≤ 0) 218

end Palace.NegativeType.Attack
