module

public import Palace.Clock
public import PalaceTest.Attack
public meta import Palace.Clock
public meta import PalaceTest.Attack

/-!
# Attacks on `Palace.Clock`

The Plausible attacks and negative controls for the laws of `Palace/Clock.lean`. They run
when this module builds (`lake test`); the library itself runs no code at build time.
-/

@[expose] public section

open Relation

namespace Palace.Clock

/-! ## Attacks

On random generator graphs over `Fin 6`, with `≼` decided by Warshall's closure over arrays.
Proper time has no executable form (a supremum over chains); its reverse triangle is attacked on
the longest-path recursion a materialized `N` would run, over random DAGs. Each control states a
nearby false law and must be refuted.
-/

namespace Attack

/-- `≼` decided: Warshall's reflexive-transitive closure of the generator edges. -/
def reach (es : List (Fin 6 × Fin 6)) : Array (Array Bool) := Id.run do
  let mut r : Array (Array Bool) := Array.ofFn fun a : Fin 6 ↦ Array.ofFn fun b : Fin 6 ↦
    a == b || es.contains (a, b)
  for k in List.range 6 do
    r := Array.ofFn fun a : Fin 6 ↦ Array.ofFn fun b : Fin 6 ↦
      (r[a.val]!)[b.val]! || ((r[a.val]!)[k]! && (r[k]!)[b.val]!)
  return r

/-- Is `S` a down-set of the closure, and does the falsifier find no crossing edge? With
`outward`, the falsifier searches the wrong way: edges out of `S`. -/
def cutHolds (outward : Bool) (es : List (Fin 6 × Fin 6)) (ss : List (Fin 6)) : Bool :=
  let R := reach es
  let isCut := (List.finRange 6).all fun a ↦ (List.finRange 6).all fun b ↦
    !(R[a.val]!)[b.val]! || !ss.contains b || ss.contains a
  let crossed := es.any fun e ↦
    if outward then ss.contains e.1 && !ss.contains e.2 else ss.contains e.2 && !ss.contains e.1
  isCut == !crossed

/- §2.4: a set is a cut iff no generator edge reads into it from outside. -/
#eval survives (∀ es : List (Fin 6 × Fin 6), ∀ ss : List (Fin 6), cutHolds false es ss = true) 101

/- Control, the falsifier searching edges out of the set. -/
#eval refuted (∀ es : List (Fin 6 × Fin 6), ∀ ss : List (Fin 6), cutHolds true es ss = true) 102

/-- Ticks in `Fin 4`, compared by `≤`, or with `coarse` by `x / 2 ≤ y / 2` (not antisymmetric). -/
def tickLe (coarse : Bool) (x y : Fin 4) : Bool := if coarse then x.val / 2 ≤ y.val / 2 else x ≤ y

/-- C1 on the generator edges, for the clock read off `ps`. -/
def monoGen (coarse : Bool) (es : List (Fin 6 × Fin 6)) (ps : List (Fin 4)) : Bool :=
  (es.take 5).all fun e ↦ tickLe coarse (ps.getD e.1.val 0) (ps.getD e.2.val 0)

/-- C1 along the whole closure, and C2. -/
def clockHolds (coarse : Bool) (es : List (Fin 6 × Fin 6)) (ps : List (Fin 4)) : Bool :=
  let R := reach (es.take 5)
  let p (e : Fin 6) : Fin 4 := ps.getD e.val 0
  let rel (a b : Fin 6) : Bool := (R[a.val]!)[b.val]!
  ((List.finRange 6).all fun a ↦ (List.finRange 6).all fun b ↦
      !rel a b || tickLe coarse (p a) (p b)) &&
    (List.finRange 6).all fun a ↦ (List.finRange 6).all fun b ↦ (List.finRange 6).all fun c ↦
      !(rel a b && rel b c && p a == p c) || p b == p a

/- C1 on the generators gives C1 on `≼`, and C1 gives C2. -/
#eval survives (∀ es : List (Fin 6 × Fin 6), ∀ ps : List (Fin 4),
  monoGen false es ps = true → clockHolds false es ps = true) 103

/- Control, ticks compared by a preorder that is not antisymmetric: C1 without C2. -/
#eval refuted (∀ es : List (Fin 6 × Fin 6), ∀ ps : List (Fin 4),
  monoGen true es ps = true → clockHolds true es ps = true) 104

/-- In-store generator edges run forward: stores are `e % 2`, positions `e / 2`. -/
def forward (es : List (Fin 6 × Fin 6)) : List (Fin 6 × Fin 6) :=
  es.filter fun e ↦ e.1.val % 2 ≠ e.2.val % 2 ∨ e.1.val / 2 ≤ e.2.val / 2

/-- Is the frontier cut a cut, decided on the closure? -/
def frontierIsCut (es : List (Fin 6 × Fin 6)) (f : Fin 2 → ℕ) : Bool :=
  let R := reach es
  let inS (e : Fin 6) : Bool := decide (e.val / 2 < f ⟨e.val % 2, by omega⟩)
  (List.finRange 6).all fun a ↦ (List.finRange 6).all fun b ↦
    !(R[a.val]!)[b.val]! || !inS b || inS a

/-- The frontier criterion (cross-store edges only) agrees with the closure, and consistent
frontiers compose by pointwise minimum and maximum. -/
def frontierHolds (es : List (Fin 6 × Fin 6)) (f0 f1 g0 g1 : Fin 4) : Bool :=
  let es := forward es
  let f : Fin 2 → ℕ := fun s ↦ if s = 0 then f0 else f1
  let f' : Fin 2 → ℕ := fun s ↦ if s = 0 then g0 else g1
  let inS (e : Fin 6) : Bool := decide (e.val / 2 < f ⟨e.val % 2, by omega⟩)
  let cross := (es.filter fun e ↦ e.1.val % 2 ≠ e.2.val % 2).all fun e ↦ !inS e.2 || inS e.1
  (frontierIsCut es f == cross) &&
    (!(frontierIsCut es f && frontierIsCut es f') ||
      (frontierIsCut es (f ⊓ f') && frontierIsCut es (f ⊔ f')))

/- §2.4: frontier cuts, their criterion and their composition. -/
#eval survives (∀ es : List (Fin 6 × Fin 6), ∀ f0 f1 g0 g1 : Fin 4,
  frontierHolds es f0 f1 g0 g1 = true) 105

/-- Longest chains in the DAG `es` (edges `i → j` with `i < j`), `-1` where `a ⋠ b`: the
recursion over `a` from the top. -/
def longest (es : List (Fin 6 × Fin 6)) : Array (Array Int) := Id.run do
  let dag := es.filter fun e ↦ e.1 < e.2
  let R := reach dag
  let mut t : Array (Array Int) := Array.replicate 6 (Array.replicate 6 (-1))
  for a' in List.range 6 do
    let a := 5 - a'
    for b in List.range 6 do
      let v : Int := if a == b then 0 else
        (List.range 6).foldl (fun acc c ↦
          if (dag.any fun e ↦ e.1.val == a && e.2.val == c) && (R[c]!)[b]! && 0 ≤ (t[c]!)[b]! then
            max acc ((t[c]!)[b]! + 1)
          else acc) (-1)
      t := t.set! a ((t[a]!).set! b v)
  return t

/-- The reverse triangle on one DAG; `forward` asks the ordinary triangle instead. -/
def triangleHolds (forward : Bool) (es : List (Fin 6 × Fin 6)) : Bool :=
  let t := longest es
  let lp (a b : Fin 6) : Int := (t[a.val]!)[b.val]!
  (List.finRange 6).all fun a ↦ (List.finRange 6).all fun b ↦ (List.finRange 6).all fun c ↦
    !(0 ≤ lp a b && 0 ≤ lp b c) ||
      if forward then lp a c ≤ lp a b + lp b c else lp a b + lp b c ≤ lp a c

/- GC-N6: proper time's reverse triangle inequality, on the longest-path recursion. -/
#eval survives (∀ es : List (Fin 6 × Fin 6), triangleHolds false es = true) 106

/- Control, the ordinary triangle inequality: a long detour beats the path through `b`. -/
#eval refuted (∀ es : List (Fin 6 × Fin 6), triangleHolds true es = true) 107

/-- Does no pair of distinct events reach each other in the closure? -/
def antisymmHolds (es : List (Fin 6 × Fin 6)) : Bool :=
  let R := reach es
  (List.finRange 6).all fun a ↦ (List.finRange 6).all fun b ↦
    a == b || !((R[a.val]!)[b.val]! && (R[b.val]!)[a.val]!)

/- CLK-4: forward generator edges, acyclic by construction, give an antisymmetric closure. -/
#eval survives (∀ es : List (Fin 6 × Fin 6),
  antisymmHolds (es.filter fun e ↦ e.1 < e.2) = true) 179

/- CLK-4 control: keep the backward edges, and a cycle makes two events reach each other. -/
#eval refuted (∀ es : List (Fin 6 × Fin 6), antisymmHolds es = true) 180

end Attack

end Palace.Clock
