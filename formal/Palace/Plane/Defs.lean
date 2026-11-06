module

public import Mathlib.Data.Finset.Sort
public import Mathlib.Data.Finset.Union
public import Mathlib.Data.Fintype.Basic
public import Mathlib.Order.Prod.Lex.Basic

/-!
# The shared plane: no-leak and noninterference (A3, A3.5), the definitions

The definitions the laws of `Palace/Plane.lean` are stated over. With `Spec/Plane.lean`
they are what a reader checks against `docs/LAWS.md`: `lake comparator` ensures the library
proves exactly the statements there, so no other file can change what is proved.
-/

@[expose] public section

open Finset

namespace Palace.Plane

/-- One row of `occ_<c>`: document `path`, at version `digest`, holds `atom` at `chunk`. The
primary key is `(path, digest, chunk)`; `row_id`, `title` and `landed_at` are payload no law here
reads. -/
@[ext]
structure Occ (P D A : Type*) where
  /-- The document (`path`). -/
  path : P
  /-- The document's version (`digest`). -/
  digest : D
  /-- The chunk's position in that version (`chunk_index`). -/
  chunk : ℕ
  /-- The atom the chunk holds. -/
  atom : A
  /-- Whether the row belongs to the document's head version (`current`). -/
  current : Bool
  deriving DecidableEq, Repr

/-- One row of `sup_<c>`: the head of `path` moved from `old` to `new`, where `none` is the code's
`''` (no version before, or retired). The log is kept in `seq` order. -/
structure Edge (P D : Type*) where
  /-- The document whose head moved. -/
  path : P
  /-- The head before the move; `none` when there was none. -/
  old : Option D
  /-- The head after the move; `none` when the document was retired. -/
  new : Option D
  deriving DecidableEq, Repr

/-- The plane: a relation and a supersession log per class, the atoms the shared table holds, and
the cached `held` and `held_ever` columns. Values of the cache off the table are never read. -/
@[ext]
structure State (K P D A : Type*) where
  /-- Each class's occupancy relation (`occ_<c>`). -/
  occ : K → Finset (Occ P D A)
  /-- Each class's supersession log (`sup_<c>`), in `seq` order. -/
  sup : K → List (Edge P D)
  /-- The atoms the shared table holds. -/
  table : Finset A
  /-- The cached `held` column: the classes with a current row holding the atom. -/
  held : A → Finset K
  /-- The cached `held_ever` column: the classes with any row holding the atom, superseded rows
    included. -/
  ever : A → Finset K

variable {K P D A : Type*}

/-- Does `o` hold `a`, counting superseded rows when `sup` (`include_superseded`)? -/
def Occ.holds (sup : Bool) (a : A) (o : Occ P D A) : Prop :=
  o.atom = a ∧ (sup = true ∨ o.current = true)

instance [DecidableEq A] (sup : Bool) (a : A) : DecidablePred (Occ.holds (P := P) (D := D) sup a) :=
  fun _ ↦ inferInstanceAs (Decidable (_ ∧ _))

/-- The cached column the prefilter reads: `held_ever` when `sup`, else `held`. -/
def cache (s : State K P D A) (sup : Bool) (a : A) : Finset K :=
  if sup then s.ever a else s.held a

section Truth

variable [Fintype K] [DecidableEq A]

/-- `_held_truth`: the classes whose relation holds `a` (currently, or ever when `sup`). -/
def truth (s : State K P D A) (sup : Bool) (a : A) : Finset K :=
  univ.filter fun c ↦ ∃ o ∈ s.occ c, o.holds sup a

/-- `held_drift() == []`: the cache agrees with the relations on every atom the table holds. -/
def Coherent (s : State K P D A) : Prop :=
  ∀ a ∈ s.table, ∀ sup, cache s sup a = truth s sup a

/-- The cache names every class of `C` that truly holds a table atom; it may be stale by excess
(a crash after a retire) but not by omission (a crash after a land). -/
def Complete (C : Finset K) (s : State K P D A) : Prop :=
  ∀ a ∈ s.table, ∀ sup, ∀ c ∈ C, c ∈ truth s sup a → c ∈ cache s sup a

instance [DecidableEq K] (s : State K P D A) : Decidable (Coherent s) :=
  inferInstanceAs (Decidable (∀ a ∈ s.table, ∀ sup, cache s sup a = truth s sup a))

instance [DecidableEq K] (C : Finset K) (s : State K P D A) : Decidable (Complete C s) :=
  inferInstanceAs (Decidable (∀ a ∈ s.table, ∀ sup, ∀ c ∈ C, c ∈ truth s sup a → c ∈ cache s sup a))

end Truth

/-- Two planes that differ at most in their caches: the same relations, logs and table. -/
def SameRel (s t : State K P D A) : Prop := s.occ = t.occ ∧ s.sup = t.sup ∧ s.table = t.table

/-! ### What a reader under `C` sees -/

section View

variable [DecidableEq A] [DecidableEq K]

/-- The prefilter (`array_has_any(held, C)`): table atoms whose cached classes meet `C`. -/
def prefilter (C : Finset K) (s : State K P D A) (sup : Bool) : Finset A :=
  s.table.filter fun a ↦ (cache s sup a ∩ C).Nonempty

/-- The cleared join's test (`_occupancies_of`): some relation of `C` holds `a`. -/
def cleared (C : Finset K) (s : State K P D A) (sup : Bool) (a : A) : Bool :=
  decide (∃ c ∈ C, ∃ o ∈ s.occ c, o.holds sup a)

/-- The atoms the cleared relations reference. -/
def refs (C : Finset K) (s : State K P D A) : Finset A :=
  C.biUnion fun c ↦ (s.occ c).image (·.atom)

/-- What a reader under `C` can see apart from search: the cleared relations and logs, and which
of their atoms the table holds. Every other read of `PlaneReader` (`occupancies`, `rows`,
`count`, `gauges`, `history`, `rank_frequency`, `has_digest`) is a function of it: its SQL names
only `self._tables`, computed from the clearance alone. -/
def view (C : Finset K) (s : State K P D A) :
    (K → Finset (Occ P D A) × List (Edge P D)) × Finset A :=
  (fun c ↦ if c ∈ C then (s.occ c, s.sup c) else (∅, []), s.table ∩ refs C s)

end View

/-! ### The write path's existence oracle (`SharedPlane.known`) -/

section Known

variable [DecidableEq A]

/-- `SharedPlane.known`: which of the named atoms the shared table holds, under any class. -/
def known (s : State K P D A) (S : Finset A) : Finset A := S.filter (· ∈ s.table)

/-- An atom the table holds that no row of any class references: dormant geometry, from a land
that crashed or was refused after its atom insert. -/
def Dormant (s : State K P D A) (a : A) : Prop := a ∈ s.table ∧ ∀ c, ∀ o ∈ s.occ c, o.atom ≠ a

variable [DecidableEq K]

/-- The bounded oracle: which of the named atoms a relation of `C` references and the table
holds, the view's own atoms. -/
def knownIn (C : Finset K) (s : State K P D A) (S : Finset A) : Finset A :=
  S.filter (· ∈ (view C s).2)

end Known

/-! ### Search: the window-widening loop over an exact nearest-neighbour search -/

section Widen

variable [DecidableEq A]

/-- `PlaneReader.search`'s loop, transcribed: ask for the `limit` nearest prefiltered atoms, keep
the ones not seen before that the cleared join holds (`T`), and widen the window ×4 until `k`
hits or the candidates run out. The Python loop has no `fuel`; `widen_eq` shows `|ps|` rounds
suffice. -/
def widen (nearest : ℕ → List A) (T : A → Bool) (k : ℕ) :
    ℕ → List A → List A → ℕ → List A
  | 0, _, hits, _ => hits.take k
  | fuel + 1, seen, hits, limit =>
    let cands := nearest limit
    let fresh := cands.filter fun a ↦ a ∉ seen
    let hits := hits ++ fresh.filter T
    if k ≤ hits.length ∨ cands.length < limit then hits.take k
    else widen nearest T k fuel (seen ++ fresh) hits (limit * 4)

end Widen

section Search

variable {Δ : Type*} [LinearOrder Δ] [LinearOrder A]

/-- The ranking key: distance to the query, then atom id. -/
def key (dist : A → Δ) (a : A) : Δ ×ₗ A := toLex (dist a, a)

/-- Exact nearest neighbours: the atoms of `S` in order of distance, ties broken by atom id. -/
def byDist (dist : A → Δ) (S : Finset A) : List A :=
  ((S.image (key dist)).sort).map fun x ↦ (ofLex x).2

variable [DecidableEq K] [DecidableEq P] [DecidableEq D]

/-- A hit's occupancies: every row of a cleared relation that holds the atom, with its class. -/
def hitOccs (C : Finset K) (s : State K P D A) (sup : Bool) (a : A) : Finset (K × Occ P D A) :=
  C.biUnion fun c ↦ ((s.occ c).filter (·.holds sup a)).image (c, ·)

/-- `PlaneReader.search`: the loop over the exact ranking of the prefiltered atoms, each hit with
its cleared occupancies. (The code's early return for `k ≤ 0` or no cleared class gives the same
`[]`.) -/
def search (dist : A → Δ) (C : Finset K) (s : State K P D A) (k : ℕ) (sup : Bool) :
    List (A × Finset (K × Occ P D A)) :=
  let ps := byDist dist (prefilter C s sup)
  (widen (ps.take ·) (cleared C s sup) k ps.length [] [] k).map fun a ↦ (a, hitOccs C s sup a)

end Search

/-! ### Writing: land, retire, purge and repair -/

/-- `o` with its `current` flag set to `b`. -/
def Occ.flag (o : Occ P D A) (b : Bool) : Occ P D A := { o with current := b }

/-- A document version to land in class `cls`: its chunks as `(chunk_index, atom)`. -/
structure Fiber (K P D A : Type*) where
  /-- The class the version lands in. -/
  cls : K
  /-- The document. -/
  path : P
  /-- The version. -/
  digest : D
  /-- Its chunks, as `(chunk_index, atom)`. -/
  chunks : List (ℕ × A)
  deriving DecidableEq, Repr

section Rows

variable [DecidableEq P] [DecidableEq D] [DecidableEq A]

/-- The flag reconciling gives a row of the path: current exactly at head `d`. -/
def headFlag (d : Option D) (o : Occ P D A) : Bool := decide (some o.digest = d)

/-- Reconcile path `p` to head `d`: its rows are current exactly at digest `d` (`none`: none of
them). The two `UPDATE`s that end `_write_fiber`, and `retire`'s one. -/
def reconcile (R : Finset (Occ P D A)) (p : P) (d : Option D) : Finset (Occ P D A) :=
  R.image fun o ↦ if o.path = p then o.flag (headFlag d o) else o

namespace Fiber

omit [DecidableEq P] [DecidableEq D] in
/-- The fiber's atoms (`wanted`). -/
def atoms (f : Fiber K P D A) : Finset A := (f.chunks.map Prod.snd).toFinset

/-- The fiber's rows, as `_write_fiber` inserts them. -/
def rows (f : Fiber K P D A) : Finset (Occ P D A) :=
  (f.chunks.map fun x ↦ (⟨f.path, f.digest, x.1, x.2, true⟩ : Occ P D A)).toFinset

end Fiber

/-- The rows of `f`'s version already in `R` (`existing` in `_write_fiber`). -/
def existing (R : Finset (Occ P D A)) (f : Fiber K P D A) : Finset (Occ P D A) :=
  R.filter fun o ↦ o.path = f.path ∧ o.digest = f.digest

/-- Did `f`'s derivation change (`existing != set(f.chunks)`)? -/
def Changed (R : Finset (Occ P D A)) (f : Fiber K P D A) : Prop :=
  (existing R f).image (fun o ↦ (o.chunk, o.atom)) ≠ f.chunks.toFinset

instance (R : Finset (Occ P D A)) (f : Fiber K P D A) : Decidable (Changed R f) :=
  inferInstanceAs (Decidable (_ ≠ _))

/-- The rows before reconciling: the fiber's rows replace its old derivation when it changed. -/
def replaced (R : Finset (Occ P D A)) (f : Fiber K P D A) : Finset (Occ P D A) :=
  if Changed R f then R \ existing R f ∪ f.rows else R

/-- `_write_fiber` on class `f.cls`'s relation. The inserted rows' `current = was_head` is
overwritten by the reconcile, so the model inserts them current. -/
def writeRel (R : Finset (Occ P D A)) (f : Fiber K P D A) : Finset (Occ P D A) :=
  reconcile (replaced R f) f.path (some f.digest)

/-- `freed`: the atoms of the path's other current version, and of the old derivation when it
changed (`freed |= {a for _, a, _ in existing}`). -/
def freed (R : Finset (Occ P D A)) (f : Fiber K P D A) : Finset A :=
  (R.filter fun o ↦ o.path = f.path ∧ o.current = true ∧ o.digest ≠ f.digest).image (·.atom) ∪
    if Changed R f then (existing R f).image (·.atom) else ∅

/-- The atoms `land` refreshes: `wanted ∪ freed`. -/
def landAffected (R : Finset (Occ P D A)) (f : Fiber K P D A) : Finset A :=
  f.atoms ∪ freed R f

end Rows

section Write

variable [DecidableEq P] [LinearOrder D] [DecidableEq A] [Fintype K] [DecidableEq K]

/-- `_refresh_held`: rewrite the cached columns of the listed table atoms from the relations. -/
def refresh (S : Finset A) (s : State K P D A) : State K P D A :=
  { s with
    held := fun a ↦ if a ∈ S ∧ a ∈ s.table then truth s false a else s.held a
    ever := fun a ↦ if a ∈ S ∧ a ∈ s.table then truth s true a else s.ever a }

/-- D8, atoms first: the table gains the atoms it lacks, each with an empty cache. -/
def insertAtoms (S : Finset A) (s : State K P D A) : State K P D A :=
  { s with
    table := s.table ∪ S
    held := fun a ↦ if a ∈ s.table then s.held a else ∅
    ever := fun a ↦ if a ∈ s.table then s.ever a else ∅ }

/-- The heads of path `p` in `R`: the digests of its current rows. -/
def heads (R : Finset (Occ P D A)) (p : P) : Finset D :=
  (R.filter fun o ↦ o.path = p ∧ o.current = true).image (·.digest)

/-- The edge `_write_fiber` appends when the head changes: from `heads[0]`, or `''`. -/
def landEdges (R : Finset (Occ P D A)) (f : Fiber K P D A) : List (Edge P D) :=
  if heads R f.path = {f.digest} then []
  else [⟨f.path, (heads R f.path).sort.head?, some f.digest⟩]

/-- `land`'s transaction: write the fiber and append its edge, without the cache step. -/
def commit (f : Fiber K P D A) (s : State K P D A) : State K P D A :=
  { s with
    occ := Function.update s.occ f.cls (writeRel (s.occ f.cls) f)
    sup := Function.update s.sup f.cls (s.sup f.cls ++ landEdges (s.occ f.cls) f) }

/-- `StratumConflict`: `f.path` is already a document of another class. -/
def Elsewhere (f : Fiber K P D A) (s : State K P D A) : Prop :=
  ∃ c, c ≠ f.cls ∧ ∃ o ∈ s.occ c, o.path = f.path

instance (f : Fiber K P D A) (s : State K P D A) : Decidable (Elsewhere f s) :=
  inferInstanceAs (Decidable (∃ _, _))

/-- Is `land` refused: a stratum conflict, or a path with two heads ("run repair")? -/
def Refused (f : Fiber K P D A) (s : State K P D A) : Prop :=
  Elsewhere f s ∨ 1 < (heads (s.occ f.cls) f.path).card

instance (f : Fiber K P D A) (s : State K P D A) : Decidable (Refused f s) :=
  inferInstanceAs (Decidable (_ ∨ _))

/-- `SharedPlane.land` of one fiber: atoms first; when refused, the transaction rolls back and the
new atoms stay dormant; else commit, then refresh the cache of `wanted ∪ freed`. -/
def land (f : Fiber K P D A) (s : State K P D A) : State K P D A :=
  if Refused f s then insertAtoms f.atoms s
  else refresh (landAffected (s.occ f.cls) f) (commit f (insertAtoms f.atoms s))

/-- What a crash between `land`'s commit and its `_refresh_held` leaves, with the cache written
last (the order before PLN-4's crash points were proved). -/
def landCrash (f : Fiber K P D A) (s : State K P D A) : State K P D A :=
  if Refused f s then insertAtoms f.atoms s else commit f (insertAtoms f.atoms s)

/-- The cache's additions (`SharedPlane.land`, before its transaction): every atom of the fiber
names the fiber's class in both columns. -/
def addCache (f : Fiber K P D A) (s : State K P D A) : State K P D A :=
  { s with
    held := fun a ↦ if a ∈ f.atoms ∧ a ∈ s.table then insert f.cls (s.held a) else s.held a
    ever := fun a ↦ if a ∈ f.atoms ∧ a ∈ s.table then insert f.cls (s.ever a) else s.ever a }

/-- What a crash before `land`'s transaction leaves, as the code writes it: the atoms the table
lacks, and the cache's additions. -/
def landAdd (f : Fiber K P D A) (s : State K P D A) : State K P D A :=
  addCache f (insertAtoms f.atoms s)

/-- What a crash after `land`'s transaction leaves (after its rollback, when refused), as the code
writes it: the additions stand, the removals are not yet written. -/
def landAddCommit (f : Fiber K P D A) (s : State K P D A) : State K P D A :=
  if Refused f s then landAdd f s else commit f (landAdd f s)

/-- `relabel`'s refusal (`StratumConflict`): a path of `old` is also a path of `new`. -/
def Clash (old new : K) (s : State K P D A) : Prop :=
  ∃ o ∈ s.occ old, ∃ o' ∈ s.occ new, o.path = o'.path

instance (old new : K) (s : State K P D A) : Decidable (Clash old new s) :=
  inferInstanceAs (Decidable (∃ _ ∈ _, _))

/-- The atoms `old`'s rows hold, current or superseded: what `relabel` refreshes. -/
def relabeled (old : K) (s : State K P D A) : Finset A := (s.occ old).image (·.atom)

/-- `relabel`'s transaction: `old`'s rows and edges move to `new`, and `old`'s relation and log
end empty. -/
def relabelCommit (old new : K) (s : State K P D A) : State K P D A :=
  { s with
    occ := Function.update (Function.update s.occ new (s.occ new ∪ s.occ old)) old ∅
    sup := Function.update (Function.update s.sup new (s.sup new ++ s.sup old)) old [] }

/-- `SharedPlane.relabel old new`, the one deliberate move between strata: refused on a clash,
else the transaction, then the cache of every atom `old`'s rows held. -/
def relabel (old new : K) (s : State K P D A) : State K P D A :=
  if old = new ∨ Clash old new s then s else refresh (relabeled old s) (relabelCommit old new s)

/-- The relabel's cache additions, before its transaction: every atom `old`'s rows hold names
`new` in both columns. -/
def addRelabel (old new : K) (s : State K P D A) : State K P D A :=
  { s with
    held := fun a ↦ if a ∈ relabeled old s ∧ a ∈ s.table then insert new (s.held a) else s.held a
    ever := fun a ↦ if a ∈ relabeled old s ∧ a ∈ s.table then insert new (s.ever a) else s.ever a }

/-- The atoms of `p`'s current rows in class `c`: what `retire` unsets and refreshes. -/
def retired (c : K) (p : P) (s : State K P D A) : Finset A :=
  ((s.occ c).filter fun o ↦ o.path = p ∧ o.current = true).image (·.atom)

/-- `retire`'s transaction: unset the path's current rows, append `head → ''` per head. -/
def retireCommit (c : K) (p : P) (s : State K P D A) : State K P D A :=
  { s with
    occ := Function.update s.occ c (reconcile (s.occ c) p none)
    sup := Function.update s.sup c
      (s.sup c ++ (heads (s.occ c) p).sort.map fun h ↦ ⟨p, some h, none⟩) }

/-- `SharedPlane.retire` of path `p` in class `c` (the class `class_of` finds). -/
def retire (c : K) (p : P) (s : State K P D A) : State K P D A :=
  if heads (s.occ c) p = ∅ then s else refresh (retired c p s) (retireCommit c p s)

/-- The atoms the rows of digest `d` hold, in every class (`held_by_digest`). -/
def byDigest (d : D) (s : State K P D A) : Finset A :=
  univ.biUnion fun c ↦ ((s.occ c).filter (·.digest = d)).image (·.atom)

/-- Of those, the atoms a row of another digest also holds (`still_held`). -/
def stillHeld (d : D) (s : State K P D A) : Finset A :=
  (byDigest d s).filter fun a ↦ ∃ c, ∃ o ∈ s.occ c, o.atom = a ∧ o.digest ≠ d

/-- The atoms `purge` deletes: those only `d`'s rows hold (`freed`). -/
def purged (d : D) (s : State K P D A) : Finset A := byDigest d s \ stillHeld d s

/-- `purge` without its cache step: the freed atoms deleted, then every row and edge naming `d`,
in every class. -/
def purgeCommit (d : D) (s : State K P D A) : State K P D A where
  occ c := (s.occ c).filter (·.digest ≠ d)
  sup c := (s.sup c).filter fun e ↦ e.old ≠ some d ∧ e.new ≠ some d
  table := s.table \ purged d s
  held := s.held
  ever := s.ever

/-- `SharedPlane.purge` of digest `d` (A3.7, privacy outranks lineage): the atoms only `d`'s rows
hold go first, then every row and edge naming `d`; the cache of the atoms still held is
refreshed. -/
def purge (d : D) (s : State K P D A) : State K P D A :=
  refresh (stillHeld d s) (purgeCommit d s)

/-- What a crash between `purge`'s atom delete and its transaction leaves: rows pointing at
deleted atoms, never private text with nothing pointing at it. -/
def purgeAtoms (d : D) (s : State K P D A) : State K P D A :=
  { s with table := s.table \ purged d s }

/-- `SharedPlane.repair` (R3): rebuild the cache of every table atom from the relations. -/
def repair (s : State K P D A) : State K P D A := refresh s.table s

/-! #### The cache stays coherent -/

omit [Fintype K] [DecidableEq P] [LinearOrder D] [DecidableEq A] [DecidableEq K] in
/-- No occupancy points at an atom the table lacks: no purge was interrupted. -/
def WF (s : State K P D A) : Prop := ∀ c, ∀ o ∈ s.occ c, o.atom ∈ s.table

omit [Fintype K] [DecidableEq P] [LinearOrder D] [DecidableEq A] [DecidableEq K] in
/-- Every row of class `c` is a document of the stratum `κ` assigns its path (A3.6, a source
lives at one stratum). -/
def Partitioned (κ : P → K) (s : State K P D A) : Prop := ∀ c, ∀ o ∈ s.occ c, κ o.path = c

end Write

/-! ### Noninterference over traces (A3.5) -/

/-- The plane's writes, one fiber per `land`. -/
inductive Op (K P D A : Type*)
  | land (f : Fiber K P D A)
  | retire (c : K) (p : P)
  | purge (d : D)
  | repair
  deriving DecidableEq, Repr

/-- May a reader under `C` be influenced by the write: one to a cleared class, or the owner's
plane-wide purge and repair? -/
def Op.visible [DecidableEq K] (C : Finset K) : Op K P D A → Bool
  | .land f => decide (f.cls ∈ C)
  | .retire c _ => decide (c ∈ C)
  | .purge _ => true
  | .repair => true

/-- The write keeps every path at the one stratum `κ` assigns it (A3.6). -/
def Op.Respects (κ : P → K) : Op K P D A → Prop
  | .land f => κ f.path = f.cls
  | .retire c p => κ p = c
  | .purge _ => True
  | .repair => True

/-- The empty plane. -/
def empty : State K P D A := ⟨fun _ ↦ ∅, fun _ ↦ [], ∅, fun _ ↦ ∅, fun _ ↦ ∅⟩

section Trace

variable [DecidableEq P] [LinearOrder D] [DecidableEq A] [Fintype K] [DecidableEq K]

/-- One write. -/
def step : Op K P D A → State K P D A → State K P D A
  | .land f => land f
  | .retire c p => retire c p
  | .purge d => purge d
  | .repair => repair

/-- A trace of writes, oldest first. -/
def run (ops : List (Op K P D A)) (s : State K P D A) : State K P D A :=
  ops.foldl (fun s op ↦ step op s) s

/-- What every trace of stratum-respecting writes keeps: a coherent cache, no dangling row, every
path at its stratum. -/
structure Good (κ : P → K) (s : State K P D A) : Prop where
  coherent : Coherent s
  wf : WF s
  part : Partitioned κ s

end Trace

/-! ### The store around the plane, and the chunk-key migration (#37)

`rekey_store` (`core/ingest/index.py`) moved the derived index off the `{digest}:{chunk_index}`
key to the doc-scoped key `(source_path, chunk_hash)`. As it was written it read `all_rows()`,
called `reset()` and added the rows back, which drops what `all_rows()` does not return. The store
here is the plane and the physical rows beside its atoms, enough to say what a re-key must keep. -/

/-- A row of the store's physical table other than the plane's atoms: a **record**, a row of a
document (`path = some p`: a code row of the per-version model before D1, or a note row of a table
that predates the plane), or a **shed code atom** (`path = none`, `is_code_atom_row`), a row the
membership relation names by its id. `note` marks a row of a plane class, the note lane's; a CODE
row has `note = false`. -/
structure Phys (P I T : Type*) where
  /-- The row's id (`id`). -/
  id : I
  /-- The row's document (`source_path`); `none` on a shed atom row. -/
  path : Option P
  /-- The row's text (`text`). -/
  text : T
  /-- Whether the row's class is a plane class, the note lane's. -/
  note : Bool
  deriving DecidableEq, Repr

namespace Phys

variable {I T : Type*}

/-- A note record, a row the migration re-keys: a row of a plane class with a document. -/
def Note (r : Phys P I T) : Prop := r.note = true ∧ r.path.isSome = true

instance (r : Phys P I T) : Decidable r.Note := inferInstanceAs (Decidable (_ ∧ _))

/-- What a re-key must keep of a row: its document, its text and its lane, all but its id. -/
def content (r : Phys P I T) : Option P × T × Bool := (r.path, r.text, r.note)

/-- `_row_new_id` on one row: a note record takes its doc-scoped key `(source_path, chunk_hash)`,
computed from its own document and text; every other row is left as it is. `key none` is the key
from an empty path (`chunk_point_id("", …)`). -/
def rekey (key : Option P → T → I) (r : Phys P I T) : Phys P I T :=
  if r.Note then { r with id := key r.path r.text } else r

end Phys

/-- The store (`VectorStore`): the plane, and the physical rows beside its atoms. -/
structure Store (K P D A I T : Type*) where
  /-- The plane. -/
  plane : State K P D A
  /-- The physical rows that are not the plane's atoms. -/
  phys : Finset (Phys P I T)

namespace Store

variable {I T : Type*} [DecidableEq P] [DecidableEq I] [DecidableEq T]

/-- The scoped re-key, `rekey_store` as fixed: every note record takes its key in place, and no
other row, and nothing of the plane, is read or written. A plane row's id (`row_id`) is payload
that `Occ` does not carry, so the code's update of it in place leaves the plane's state as it is. -/
def rekey (key : Option P → T → I) (s : Store K P D A I T) : Store K P D A I T :=
  { s with phys := s.phys.image (Phys.rekey key) }

variable [LinearOrder D] [DecidableEq A] [Fintype K] [DecidableEq K]

/-- `rekey_store` as it was, after the shed-atom guard (bp-152 Item 3): `all_rows()` reads every
record, note and code alike, and the plane's current rows; `reset()` drops the table and the
plane's relations; and `add` lands them again, every record under the note lane's key and the
plane's rows as the fibers `fs` they regroup into, from the empty plane. A shed atom row is not
read, so it is not landed again. -/
def rekeyReset (key : Option P → T → I) (fs : List (Fiber K P D A)) (s : Store K P D A I T) :
    Store K P D A I T :=
  ⟨run (fs.map Op.land) empty,
    (s.phys.filter fun r ↦ r.path.isSome = true).image fun r ↦ { r with id := key r.path r.text }⟩

/-- The same before the guard: the shed atom rows are read too, and re-keyed from an empty path. -/
def rekeyResetUnguarded (key : Option P → T → I) (fs : List (Fiber K P D A))
    (s : Store K P D A I T) : Store K P D A I T :=
  ⟨run (fs.map Op.land) empty, s.phys.image fun r ↦ { r with id := key r.path r.text }⟩

end Store

/-! ### Where the hypotheses bite -/

namespace Witness

/-- A cleared fiber (class 0, path 0) and an uncleared one (class 1, path 1) sharing atom 0. -/
def fx : Fiber (Fin 2) (Fin 2) (Fin 1) (Fin 1) := ⟨0, 0, 0, [(0, 0)]⟩

/-- The uncleared fiber. -/
def fy : Fiber (Fin 2) (Fin 2) (Fin 1) (Fin 1) := ⟨1, 1, 0, [(0, 0)]⟩

/-- The cleared land, crashed between its commit and its `_refresh_held`. -/
def drifted : State (Fin 2) (Fin 2) (Fin 1) (Fin 1) := landCrash fx empty

/-- A note's first version (class 0, path 0, digest 0), holding atom 0. -/
def va : Fiber (Fin 1) (Fin 1) (Fin 2) (Fin 2) := ⟨0, 0, 0, [(0, 0)]⟩

/-- Its second version (digest 1), holding atom 1. -/
def vb : Fiber (Fin 1) (Fin 1) (Fin 2) (Fin 2) := ⟨0, 0, 1, [(0, 1)]⟩

/-- A store whose note was edited once (its first version superseded, an edge for each landing),
beside two shed code atoms of one text (ids 0 and 3, two layers' readings of one body) and two
code records of one document with one text (ids 1 and 2, two layers). -/
def edited : Store (Fin 1) (Fin 1) (Fin 2) (Fin 2) ℕ (Fin 2) :=
  ⟨run [.land va, .land vb] empty,
    {⟨0, none, 0, false⟩, ⟨3, none, 0, false⟩, ⟨1, some 0, 1, false⟩, ⟨2, some 0, 1, false⟩}⟩

/-- Class 0's one note, holding atom 0. -/
def moved : State (Fin 2) (Fin 1) (Fin 1) (Fin 1) := land ⟨0, 0, 0, [(0, 0)]⟩ empty

end Witness

end Palace.Plane
