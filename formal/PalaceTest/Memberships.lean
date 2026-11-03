module

public import Palace.Memberships
public import Mathlib.Testing.Plausible.Sampleable
public import PalaceTest.Attack
public meta import Palace.Memberships
public meta import Mathlib.Testing.Plausible.Sampleable
public meta import PalaceTest.Attack

/-!
# Attacks on `Palace.Memberships`

The Plausible attacks and negative controls for the laws of `Palace/Memberships.lean`. They run
when this module builds (`lake test`); the library itself runs no code at build time.
-/

@[expose] public section

open Finset

namespace Palace

/-! ## Attacks

Each law is attacked on small exact instances: paths, blobs and layers in `Fin 2`, chunks below 3
and atoms in `Fin 3`. Relations are built from random row lists through `write`, so a repeated
coordinate is ignored as `INSERT OR IGNORE` ignores it; landings run over random histories; runs
over random occupant sequences. Each control states a nearby false law and must be refuted.
-/

namespace Attack

/-- The relation the attacks draw: four small coordinate types. -/
abbrev Rel := Relation (Fin 2) (Fin 2) (Fin 2) (Fin 3)

/-- The empty relation. -/
def empty : Rel := ⟨∅, fun _ ↦ default⟩

/-- A relation from random rows `((path, blob, layer, chunk), (atom, current, tombstoned))`. -/
def ofRows (rows : List ((Fin 2 × Fin 2 × Fin 2 × Fin 3) × (Fin 3 × Bool × Bool))) : Rel :=
  empty.write (rows.map fun r ↦
    (⟨r.1.1, r.1.2.1, r.1.2.2.1, r.1.2.2.2⟩, ⟨r.2.1, r.2.2.1, r.2.2.2⟩))

/- MEM-1: `n_doc ≤ n_occ`, current-only and lifetime. -/
#eval survives (∀ rows : List ((Fin 2 × Fin 2 × Fin 2 × Fin 3) × (Fin 3 × Bool × Bool)),
  ∀ v : Fin 3, ∀ c : Bool, (ofRows rows).nDoc v c ≤ (ofRows rows).nOcc v c) 21

/- MEM-1 control, the set reading: one row per document. -/
#eval refuted (∀ rows : List ((Fin 2 × Fin 2 × Fin 2 × Fin 3) × (Fin 3 × Bool × Bool)),
  ∀ v : Fin 3, (ofRows rows).nOcc v false ≤ (ofRows rows).nDoc v false) 22

/- MEM-2: the fibers' sizes sum to `|M|`. -/
#eval survives (∀ rows : List ((Fin 2 × Fin 2 × Fin 2 × Fin 3) × (Fin 3 × Bool × Bool)),
  ∑ f ∈ (ofRows rows).versions, ((ofRows rows).fiber f).card = (ofRows rows).support.card) 23

/- MEM-2 control, fibers keyed by blob alone: a rename shares a blob across two paths. -/
#eval refuted (∀ rows : List ((Fin 2 × Fin 2 × Fin 2 × Fin 3) × (Fin 3 × Bool × Bool)),
  (ofRows rows).versions.card = ((ofRows rows).support.image (·.blob)).card) 24

/- MEM-5: `current_any(v) ⇔ n_doc(v, t) > 0`. -/
#eval survives (∀ rows : List ((Fin 2 × Fin 2 × Fin 2 × Fin 3) × (Fin 3 × Bool × Bool)),
  ∀ v : Fin 3, (ofRows rows).currentAny v ↔ 0 < (ofRows rows).nDoc v) 25

/- MEM-5 control, the lifetime count in place of the current one. -/
#eval refuted (∀ rows : List ((Fin 2 × Fin 2 × Fin 2 × Fin 3) × (Fin 3 × Bool × Bool)),
  ∀ v : Fin 3, (ofRows rows).currentAny v ↔ 0 < (ofRows rows).nDoc v false) 26

/-- A version's fiber as the derivation emits it: two chunks whose atoms depend on the version. -/
def fiberRows (p b : Fin 2) : List (Coord (Fin 2) (Fin 2) (Fin 2) × Occupant (Fin 3)) :=
  [(⟨p, b, 0, 0⟩, ⟨⟨b.val, by omega⟩, false, false⟩),
   (⟨p, b, 1, 1⟩, ⟨⟨p.val + 1, by omega⟩, false, false⟩)]

/-- Land a history of versions `(path, blob)` in order, from the empty relation. -/
def landAll (land : Rel → Fin 2 → Fin 2 → List (Coord (Fin 2) (Fin 2) (Fin 2) × Occupant (Fin 3)) →
    Rel) (hist : List (Fin 2 × Fin 2)) : Rel :=
  hist.foldl (fun M v ↦ land M v.1 v.2 (fiberRows v.1 v.2)) empty

/-- The newest blob landed on each path. -/
def heads (hist : List (Fin 2 × Fin 2)) (p : Fin 2) : Option (Fin 2) :=
  ((hist.filter (·.1 = p)).getLast?).map (·.2)

/- MEM-4: after any history, currency agrees with each path's newest landing (reverts included). -/
#eval survives (∀ hist : List (Fin 2 × Fin 2),
  (landAll (fun M p h rows ↦ M.land p h rows) hist).Coherent (heads hist)) 27

/- MEM-4 control, the C1 lander: skipping reconciliation on an existing fiber. -/
#eval refuted (∀ hist : List (Fin 2 × Fin 2),
  (landAll (fun M p h rows ↦ M.landShortCircuit p h rows) hist).Coherent (heads hist)) 28

/-- `slot_runs`' loop, transcribed: append an occupant unless it equals the last one kept. -/
def slotRunsLoop (s : List (Fin 3)) : List (Fin 3) :=
  s.foldl (fun seq x ↦ if seq.getLast? = some x then seq else seq ++ [x]) []

/- MEM-3: `runs` is what the Python loop computes. -/
#eval survives (∀ s : List (Fin 3), runs s = slotRunsLoop s) 29

/- MEM-3: one edge per change of occupant, and the ends of every edge differ (checked over every
edge, not sampled). -/
#eval survives (∀ s : List (Fin 3),
  (edges s).length = changes s ∧ (edges s).all (fun e ↦ e.1 ≠ e.2) = true) 30

/- MEM-3 control, distinct collapse: a revert would vanish. -/
#eval refuted (∀ s : List (Fin 3), s ≠ [] → s.dedup.length = changes s + 1) 31

end Attack

end Palace
