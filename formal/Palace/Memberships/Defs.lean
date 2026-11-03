module

public import Mathlib.Algebra.BigOperators.Group.Finset.Basic
public import Mathlib.Data.List.Destutter

/-!
# The membership relation: MEM-1, MEM-2, MEM-3, MEM-4, MEM-5, the definitions

The definitions the laws of `Palace/Memberships.lean` are stated over. With `Spec/Memberships.lean`
they are what a reader checks against `docs/LAWS.md`: `lake comparator` ensures the library
proves exactly the statements there, so no other file can change what is proved.
-/

@[expose] public section

open Finset

namespace Palace

/-- An occupancy's coordinates: the primary key `(path, blob_sha, layer, chunk_index)`. -/
structure Coord (P B L : Type*) where
  /-- The document's path (`path`). A rename is a new fiber over the same atoms. -/
  path : P
  /-- The version's identity, its git blob (`blob_sha`). -/
  blob : B
  /-- The reading (`layer`): `code_ast`, `code_text` or `codedoc`. -/
  layer : L
  /-- The position in the reading's chunk list (`chunk_index`), so two identical windows stay two
    rows. -/
  chunk : ℕ
  deriving DecidableEq, Repr

/-- What sits at a coordinate: the atom (`content_id`) and the `current` and `tombstoned` flags. -/
structure Occupant (A : Type*) where
  /-- The atom held here (`content_id`). -/
  atom : A
  /-- Whether the row is the path's head projection (`current`). -/
  current : Bool := false
  /-- Whether the atom was purged and the row records its hole (`tombstoned`). -/
  tombstoned : Bool := false
  deriving DecidableEq, Repr, Inhabited

/-- The membership relation `M`: a finite set of coordinates and the occupant at each. Values off
the support are never read. -/
@[ext]
structure Relation (P B L A : Type*) where
  /-- The coordinates in the relation: its primary keys. -/
  support : Finset (Coord P B L)
  /-- The occupant at each coordinate, read only on the support. -/
  occ : Coord P B L → Occupant A

namespace Relation

variable {P B L A : Type*} (M : Relation P B L A)

/-! ### MEM-1: the atom projection is a multiset, and `n_doc ≤ n_occ` -/

section Counts

variable [DecidableEq P] [DecidableEq A]

/-- The occupancies of atom `v` that the counts read: never tombstoned, and current when
`currentOnly` (the `current_only` argument of `n_doc` and `n_occ`). -/
def holding (v : A) (currentOnly : Bool) : Finset (Coord P B L) :=
  M.support.filter fun k ↦ (M.occ k).atom = v ∧ (M.occ k).tombstoned = false ∧
    (currentOnly = true → (M.occ k).current = true)

/-- `n_occ(v)`: the membership rows holding `v`, the multiset reading. -/
def nOcc (v : A) (currentOnly : Bool := true) : ℕ := (M.holding v currentOnly).card

/-- `n_doc(v)`: the distinct paths holding `v`, the document-frequency reading. -/
def nDoc (v : A) (currentOnly : Bool := true) : ℕ :=
  ((M.holding v currentOnly).image (·.path)).card

/-- The atom projection: one atom per row, with multiplicity. -/
def atoms : Multiset A := M.support.val.map fun k ↦ (M.occ k).atom

end Counts

/-! ### MEM-2: the version fibers partition `M` -/

section Fibers

variable [DecidableEq P] [DecidableEq B]

/-- The version a coordinate belongs to: `(path, blob_sha)`. -/
def version (k : Coord P B L) : P × B := (k.path, k.blob)

/-- The fiber `M(path, blob_sha)`: every occupancy of one version. -/
def fiber (f : P × B) : Finset (Coord P B L) := M.support.filter fun k ↦ version k = f

/-- The versions that have a fiber. -/
def versions : Finset (P × B) := M.support.image version

end Fibers

/-! ### MEM-4 and MEM-5: currency is reconciled on every landing -/

section Currency

variable [DecidableEq P] [DecidableEq B] [DecidableEq L]

/-- `reconcile_currency(path, head)`: on path `p`, exactly the rows of blob `h` are current;
every other path is untouched. -/
def reconcile (p : P) (h : B) : Relation P B L A where
  support := M.support
  occ k := if k.path = p then { M.occ k with current := decide (k.blob = h) } else M.occ k

/-- `write_fiber`'s `INSERT OR IGNORE`: a coordinate already present keeps its occupant, and the
first listed row wins for a new one. -/
def write (rows : List (Coord P B L × Occupant A)) : Relation P B L A where
  support := M.support ∪ (rows.map Prod.fst).toFinset
  occ k := if k ∈ M.support then M.occ k
    else ((rows.find? fun r ↦ decide (r.1 = k)).map Prod.snd).getD (M.occ k)

/-- Landing a version (D2 steps 3 and 4): write its fiber, then reconcile currency, every time,
including when the write added nothing. -/
def land (p : P) (h : B) (rows : List (Coord P B L × Occupant A)) : Relation P B L A :=
  (M.write rows).reconcile p h

/-- Currency agrees with a head per path: a row is current iff its blob is its path's head. -/
def Coherent (head : P → Option B) : Prop :=
  ∀ k ∈ M.support, (M.occ k).current = true ↔ head k.path = some k.blob

/-- `current_any(v)`: some current, un-tombstoned occupancy holds `v`. This is what the lance
`current` column caches and `repair_current_any` rebuilds from this store. -/
def currentAny (v : A) : Prop :=
  ∃ k ∈ M.support, (M.occ k).atom = v ∧ (M.occ k).tombstoned = false ∧ (M.occ k).current = true

end Currency

end Relation

/-! ### MEM-3: slot runs are the adjacent-collapse run-length encoding -/

section Runs

variable {A : Type*} [DecidableEq A]

/-- The runs (`slot_runs`): adjacent equal occupants collapsed, never distinct ones. -/
def runs (s : List A) : List A := s.destutter (· ≠ ·)

/-- The supersession edges (`slot_edges`): consecutive runs. -/
def edges (s : List A) : List (A × A) := (runs s).zip (runs s).tail

/-- The places where the sequence changes occupant. -/
def changes (s : List A) : ℕ := ((s.zip s.tail).filter fun p ↦ p.1 ≠ p.2).length

end Runs

end Palace
