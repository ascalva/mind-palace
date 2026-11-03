module

public import Palace.Rayleigh
public import PalaceTest.Balance
public meta import Palace.Rayleigh
public meta import PalaceTest.Balance

/-!
# Attacks on `Palace.Rayleigh`

The Plausible attacks and negative controls for the laws of `Palace/Rayleigh.lean`. They run
when this module builds (`lake test`); the library itself runs no code at build time.
-/

@[expose] public section

open Matrix Finset

namespace Palace

/-! ## Attacks

Over ℚ on `Fin 5`, effective resistance is read off the exact shadow `(L + P)⁻¹ − P` of `L⁺`
(whose four Penrose equations `Palace/Spectral.lean` attacks), with components by Warshall's
closure, and conductance follows the code: `1/R_eff` within a component, `0` across. Weights are
random nonnegative edge lists. Each control states a nearby false law and must be refuted.
-/

namespace Attack

/-- Every pair's effective conductance on the shadow, the code's way. -/
def conductances (A : Matrix (Fin 5) (Fin 5) ℚ) : Option (Fin 5 → Fin 5 → ℚ) :=
  let P := projR A
  match invR (addR (rows (lap A)) P) with
  | none => none
  | some Y =>
    let X := subR Y P
    let r := reach A
    some fun p q ↦
      let R := entry X p p + entry X q q - 2 * entry X p q
      if (r[p.val]!)[q.val]! && decide (0 < R) then 1 / R else 0

/-- Rayleigh on one instance: after adding the nonnegative weights `D`, no pair's conductance is
lower. With `reversed`, the false converse: none is higher. -/
def rayleighHolds (reversed : Bool) (A D : Matrix (Fin 5) (Fin 5) ℚ) : Bool :=
  match conductances A, conductances (A + D) with
  | some c, some c' => (List.finRange 5).all fun p ↦ (List.finRange 5).all fun q ↦
      if reversed then decide (c' p q ≤ c p q) else decide (c p q ≤ c' p q)
  | _, _ => false

/- CND-2: adding weight never lowers conductance, on every pair. -/
#eval survives (∀ es ds : List (Fin 5 × Fin 5 × ℕ),
  rayleighHolds false (ofEdges (nonneg es)) (ofEdges (nonneg ds)) = true) 121

/- Control, the law reversed: adding weight never raises conductance. -/
#eval refuted (∀ es ds : List (Fin 5 × Fin 5 × ℕ),
  rayleighHolds true (ofEdges (nonneg es)) (ofEdges (nonneg ds)) = true) 122

/-- Leave-one-out on one instance, before `A` and after `A'`: no reversion of an increased edge
raises conductance, and with a single increased edge every rise confirms it. With `complete`, the
false claim that every rise confirms some increased edge. -/
def looHolds (complete : Bool) (A A' : Matrix (Fin 5) (Fin 5) ℚ) : Bool :=
  let inc := (List.finRange 5).flatMap fun i ↦
    ((List.finRange 5).filter fun j ↦ i < j && decide (A i j < A' i j)).map (i, ·)
  let revertQ (a b : Fin 5) : Matrix (Fin 5) (Fin 5) ℚ := fun i j ↦
    if (i = a ∧ j = b) ∨ (i = b ∧ j = a) then A i j else A' i j
  match conductances A, conductances A' with
  | some c, some c' =>
    let loo := inc.filterMap fun e ↦ conductances (revertQ e.1 e.2)
    (loo.length == inc.length) &&
      (List.finRange 5).all fun p ↦ (List.finRange 5).all fun q ↦
        let rise := decide (c p q < c' p q)
        let confirmed := loo.any fun cl ↦ decide (cl p q ≤ c p q)
        if complete then !rise || confirmed
        else (loo.all fun cl ↦ decide (cl p q ≤ c' p q)) &&
          (!(rise && inc.length == 1) || confirmed)
  | _, _ => false

/- Leave-one-out: reversions never raise conductance, and a single increased edge confirms every
rise. -/
#eval survives (∀ es fs : List (Fin 5 × Fin 5 × ℕ),
  looHolds false (ofEdges (nonneg es)) (ofEdges (nonneg fs)) = true) 123

/- Control, completeness: every rise confirms some increased edge. Two redundant new paths
confirm neither. -/
#eval refuted (∀ es fs : List (Fin 5 × Fin 5 × ℕ),
  looHolds true (ofEdges (nonneg es)) (ofEdges (nonneg fs)) = true) 124

end Attack

end Palace
