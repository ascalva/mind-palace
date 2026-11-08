module

public import Palace.Derived
public import PalaceTest.Attack
public meta import Palace.Derived
public meta import PalaceTest.Attack

/-!
# Attacks on `Palace.Derived`

The Plausible attacks and negative controls for the laws of `Palace/Derived.lean`, on exact
shadows: two items, two structures, two vectors and two embedder identities, every one `Fin 2`;
the keyed set from two bits, the structures from a code in `Fin 9` (none or either structure per
item), the atom table and the marks from codes in `Fin 81` (none or either vector, or none or
either structure, per cell), the embedder from a code in `Fin 16`; a run from a list of codes in
`Fin 12`, each an atom write, a mark write or a landing. The controls are the laws' edges: a run
with a landing in it changes what a structural query reads; the mark-first order leaves an
unsound state the code's drain never repairs; two derivations of one item in the two orders are
one state, which a landing of the same item between them is not; and reading a pending vector as
zero gives an answer the embedding changes (ING-21). They run when this module builds
(`lake test`).
-/

@[expose] public section

open Finset

namespace Palace.Derived.Attack

/-- `none`, `some 0` or `some 1`, from a number's residue. -/
def opt3 (n : ℕ) : Option (Fin 2) :=
  match n % 3 with
  | 0 => none
  | 1 => some 0
  | _ => some 1

/-- A set of items from two bits. -/
def keyedOf (k : Fin 4) : Finset (Fin 2) :=
  let s : Finset (Fin 2) := if k.val.testBit 0 then {0} else ∅
  if k.val.testBit 1 then insert 1 s else s

/-- Each item's structure from a code in base three. -/
def structOf (c : Fin 9) : Fin 2 → Option (Fin 2) := fun i ↦ opt3 (c.val / 3 ^ i.val)

/-- Four cells of `none`, `some 0` or `some 1` from a code in base three. -/
def cellsOf (c : Fin 81) : Fin 2 → Fin 2 → Option (Fin 2) :=
  fun x y ↦ opt3 (c.val / 3 ^ (2 * x.val + y.val))

/-- An embedder from four bits: a structure's vector under each identity. -/
def fOf (c : Fin 16) : Fin 2 → Fin 2 → Fin 2 :=
  fun e σ ↦ if c.val.testBit (2 * e.val + σ.val) then 1 else 0

/-- A state from codes. -/
def st (k : Fin 4) (c : Fin 9) (a m : Fin 81) : State (Fin 2) (Fin 2) (Fin 2) (Fin 2) :=
  ⟨keyedOf k, structOf c, cellsOf a, cellsOf m⟩

/-- A fresh state: items and structures, no atom and no mark; sound and truthful under any
embedder. -/
def fresh (k : Fin 4) (c : Fin 9) : State (Fin 2) (Fin 2) (Fin 2) (Fin 2) :=
  ⟨keyedOf k, structOf c, fun _ _ ↦ none, fun _ _ ↦ none⟩

/-- A step from a code: an atom write (0 to 3), a mark write (4 to 7) or a landing (8 to 11). -/
def stepOf (n : Fin 12) : Step (Fin 2) (Fin 2) (Fin 2) :=
  if h : n.val < 4 then .atom ⟨n.val / 2, by omega⟩ ⟨n.val % 2, by omega⟩
  else if h' : n.val < 8 then .mark ⟨(n.val - 4) / 2, by omega⟩ ⟨(n.val - 4) % 2, by omega⟩
  else .land ⟨(n.val - 8) / 2, by omega⟩ ⟨(n.val - 8) % 2, by omega⟩

/-- An embed step from a code: an atom write (0 to 3) or a mark write (4 to 7), never a landing. -/
def embedStepOf (n : Fin 8) : Step (Fin 2) (Fin 2) (Fin 2) :=
  if h : n.val < 4 then .atom ⟨n.val / 2, by omega⟩ ⟨n.val % 2, by omega⟩
  else .mark ⟨(n.val - 4) / 2, by omega⟩ ⟨(n.val - 4) % 2, by omega⟩

/-- Two states agree, cell by cell. -/
def same (s t : State (Fin 2) (Fin 2) (Fin 2) (Fin 2)) : Bool :=
  s.keyed == t.keyed && (List.finRange 2).all (fun i ↦ s.struct i == t.struct i)
    && (List.finRange 2).all (fun e ↦ (List.finRange 2).all fun σ ↦ s.atom e σ == t.atom e σ)
    && (List.finRange 2).all (fun i ↦ (List.finRange 2).all fun e ↦ s.mark i e == t.mark i e)

/-- Two states agree on what the landing writes: the keys and the structures. -/
def sameStructure (s t : State (Fin 2) (Fin 2) (Fin 2) (Fin 2)) : Bool :=
  s.keyed == t.keyed && (List.finRange 2).all fun i ↦ s.struct i == t.struct i

/-- Two states' fields under an identity agree. -/
def sameField (e : Fin 2) (s t : State (Fin 2) (Fin 2) (Fin 2) (Fin 2)) : Bool :=
  (List.finRange 2).all fun i ↦ field s e i == field t e i

/-- Soundness, decided. -/
def sound (s : State (Fin 2) (Fin 2) (Fin 2) (Fin 2)) (e : Fin 2) : Bool :=
  (List.finRange 2).all fun i ↦
    !(decide (i ∈ s.keyed)) || !(s.mark i e == s.struct i) ||
      match s.struct i with
      | some σ => (s.atom e σ).isSome
      | none => true

/-- Truthfulness, decided. -/
def truthful (f : Fin 2 → Fin 2 → Fin 2) (s : State (Fin 2) (Fin 2) (Fin 2) (Fin 2)) : Bool :=
  (List.finRange 2).all fun e ↦ (List.finRange 2).all fun σ ↦
    match s.atom e σ with
    | some v => v == f e σ
    | none => true

/-- A score on vectors: `1` for the first, `2` for the second, never zero. -/
def score (v : Fin 2) : ℤ := v.val + 1

/-- A step as the drain runs it: an embed step becomes the item's whole key-last derivation, a
landing stays a landing. -/
def keyLast : Step (Fin 2) (Fin 2) (Fin 2) → List (Step (Fin 2) (Fin 2) (Fin 2))
  | .atom e i => derive e i
  | .mark e i => derive e i
  | .land i σ => [.land i σ]

/-- The state a key-last run of coded steps reaches from a fresh state. -/
def reached (fc : Fin 16) (k : Fin 4) (c : Fin 9) (w : List (Fin 12)) :
    State (Fin 2) (Fin 2) (Fin 2) (Fin 2) :=
  run (fOf fc) ((w.map stepOf).flatMap keyLast) (fresh k c)

/-- The state a key-last run of coded embed steps reaches from a fresh state. -/
def reachedEmbed (fc : Fin 16) (k : Fin 4) (c : Fin 9) (w : List (Fin 8)) :
    State (Fin 2) (Fin 2) (Fin 2) (Fin 2) :=
  run (fOf fc) ((w.map embedStepOf).flatMap keyLast) (fresh k c)

/-- Whether a field that reports a vector reports the structure's image, decided. -/
def fieldOk (f : Fin 2 → Fin 2 → Fin 2) (c : Fin 9) (s : State (Fin 2) (Fin 2) (Fin 2) (Fin 2))
    (e i : Fin 2) : Bool :=
  match field s e i with
  | some v => (structOf c i).map (f e) == some v
  | none => true

/- ING-19: a landing writes no atom and no mark, and the landed item is keyed. -/
#eval survives (∀ (k : Fin 4) (c : Fin 9) (a m : Fin 81) (i σ : Fin 2),
  ((List.finRange 2).all (fun e ↦ (List.finRange 2).all fun τ ↦
      (land i σ (st k c a m)).atom e τ == (st k c a m).atom e τ)
    && (List.finRange 2).all (fun j ↦ (List.finRange 2).all fun e ↦
      (land i σ (st k c a m)).mark j e == (st k c a m).mark j e)
    && decide (i ∈ (land i σ (st k c a m)).keyed)) = true) 374

/- ING-19: the drain changes neither the keys nor the structures. -/
#eval survives (∀ (k : Fin 4) (c : Fin 9) (a m : Fin 81) (fc : Fin 16) (e : Fin 2),
  sameStructure (drain (fOf fc) e (st k c a m)) (st k c a m) = true) 375

/- ING-19: the drain under one identity leaves the other identity's atoms and marks alone. -/
#eval survives (∀ (k : Fin 4) (c : Fin 9) (a m : Fin 81) (fc : Fin 16) (e : Fin 2),
  ((List.finRange 2).all (fun τ ↦
      (drain (fOf fc) e (st k c a m)).atom (e + 1) τ == (st k c a m).atom (e + 1) τ)
    && (List.finRange 2).all fun j ↦
      (drain (fOf fc) e (st k c a m)).mark j (e + 1) == (st k c a m).mark j (e + 1)) = true) 376

/- ING-21: a structural query answers the same after any run of embed steps. -/
#eval survives (∀ (k : Fin 4) (c : Fin 9) (a m : Fin 81) (fc : Fin 16) (w : List (Fin 8)),
  sameStructure (run (fOf fc) (w.map embedStepOf) (st k c a m)) (st k c a m) = true) 377

/- Control: a run with a landing in it changes what a structural query reads. -/
#eval refuted (∀ (k : Fin 4) (c : Fin 9) (a m : Fin 81) (fc : Fin 16) (w : List (Fin 12)),
  sameStructure (run (fOf fc) (w.map stepOf) (st k c a m)) (st k c a m) = true) 378

/- ING-20: an item's derivation is idempotent. -/
#eval survives (∀ (k : Fin 4) (c : Fin 9) (a m : Fin 81) (fc : Fin 16) (e i : Fin 2),
  same (run (fOf fc) (derive e i) (run (fOf fc) (derive e i) (st k c a m)))
    (run (fOf fc) (derive e i) (st k c a m)) = true) 379

/- ING-20: two items' derivations commute. -/
#eval survives (∀ (k : Fin 4) (c : Fin 9) (a m : Fin 81) (fc : Fin 16) (e i : Fin 2),
  same (run (fOf fc) (derive e i ++ derive e (i + 1)) (st k c a m))
    (run (fOf fc) (derive e (i + 1) ++ derive e i) (st k c a m)) = true) 380

/- ING-20: an item's derivation commutes with a later landing of the other item (the landed
structure is drawn with the identity, to keep the instance within Plausible's compiler). -/
#eval survives (∀ (k : Fin 4) (c : Fin 9) (a m : Fin 81) (fc : Fin 16) (e i : Fin 2),
  same (run (fOf fc) (derive e i ++ [.land (i + 1) e]) (st k c a m))
    (run (fOf fc) ([.land (i + 1) e] ++ derive e i) (st k c a m)) = true) 381

/- Control: a landing of the same item does not commute with its derivation, when it changes
the structure. -/
#eval refuted (∀ (k : Fin 4) (c : Fin 9) (a m : Fin 81) (fc : Fin 16) (e i : Fin 2),
  same (run (fOf fc) (derive e i ++ [.land i e]) (st k c a m))
    (run (fOf fc) ([.land i e] ++ derive e i) (st k c a m)) = true) 382

/- ING-20: the drain is idempotent, and leaves nothing keyed pending. -/
#eval survives (∀ (k : Fin 4) (c : Fin 9) (a m : Fin 81) (fc : Fin 16) (e : Fin 2),
  (same (drain (fOf fc) e (drain (fOf fc) e (st k c a m))) (drain (fOf fc) e (st k c a m))
    && (List.finRange 2).all fun i ↦ !decide (pending (drain (fOf fc) e (st k c a m)) e i))
    = true) 383

/- ING-20: after the drain every keyed item's field is its structure's image. -/
#eval survives (∀ (k : Fin 4) (c : Fin 9) (a m : Fin 81) (fc : Fin 16) (e : Fin 2),
  (List.finRange 2).all (fun i ↦ field (drain (fOf fc) e (st k c a m)) e i
    == if i ∈ keyedOf k then (structOf c i).map (fOf fc e) else none) = true) 384

/- ING-20: from any interleaving of landings and embed steps, the drain's field is the field of
the landings alone followed by the drain. -/
#eval survives (∀ (k : Fin 4) (c : Fin 9) (a m : Fin 81) (fc : Fin 16) (e : Fin 2)
    (w : List (Fin 12)),
  sameField e (drain (fOf fc) e (run (fOf fc) (w.map stepOf) (st k c a m)))
    (drain (fOf fc) e (run (fOf fc) ((w.map stepOf).filter Step.isLand) (st k c a m))) = true) 385

/- ING-20: a fresh state is sound and truthful, every key-last run keeps it so, and from there
the code's drain reaches the drain's field. -/
#eval survives (∀ (k : Fin 4) (c : Fin 9) (fc : Fin 16) (e : Fin 2) (w : List (Fin 12)),
  (sound (reached fc k c w) e && truthful (fOf fc) (reached fc k c w)
    && sameField e (codeDrain (fOf fc) e (reached fc k c w))
      (drain (fOf fc) e (reached fc k c w))) = true) 386

/- ING-20: every prefix of the key-last derivation keeps soundness. -/
#eval survives (∀ (k : Fin 4) (c : Fin 9) (fc : Fin 16) (e i : Fin 2) (n : Fin 3)
    (w : List (Fin 8)),
  sound (run (fOf fc) ((derive e i).take n.val) (reachedEmbed fc k c w)) e = true) 387

/- Control: the mark-first order, interrupted after the mark, is unsound. -/
#eval refuted (∀ (k : Fin 4) (c : Fin 9) (fc : Fin 16) (e i : Fin 2),
  sound (run (fOf fc) ((deriveKeyFirst e i).take 1) (fresh k c)) e = true) 388

/- Control: after the mark-first order, interrupted after the mark, the code's drain does not
reach the drain's field. -/
#eval refuted (∀ (k : Fin 4) (c : Fin 9) (fc : Fin 16) (e i : Fin 2),
  sameField e (codeDrain (fOf fc) e (run (fOf fc) ((deriveKeyFirst e i).take 1) (fresh k c)))
    (drain (fOf fc) e (fresh k c)) = true) 389

/- ING-21: a pending item's field is `none`. -/
#eval survives (∀ (k : Fin 4) (c : Fin 9) (a m : Fin 81) (e i : Fin 2),
  decide (pending (st k c a m) e i) = true → (field (st k c a m) e i == none) = true) 390

/- ING-21: on a truthful state, a field that reports a vector reports the structure's image. -/
#eval survives (∀ (k : Fin 4) (c : Fin 9) (a m : Fin 81) (fc : Fin 16) (e i : Fin 2),
  truthful (fOf fc) (st k c a m) = true → fieldOk (fOf fc) c (st k c a m) e i = true) 391

/- Control: reading a pending vector as zero gives an answer the embedding changes. -/
#eval refuted (∀ (k : Fin 4) (c : Fin 9) (fc : Fin 16) (e i : Fin 2),
  zeroRead score (run (fOf fc) (derive e i) (fresh k c)) e i
    = zeroRead score (fresh k c) e i) 392

end Palace.Derived.Attack
