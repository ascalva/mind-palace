import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Data.List.Destutter
import Mathlib.Testing.Plausible.Sampleable
import Palace.Attack

/-!
# The membership relation: MEM-1, MEM-2, MEM-3, MEM-4, MEM-5

Statements of the ledger's membership laws (dn-mathematical-foundations §2.2, seed table I, and
the structure settled in §2.3.1), mirroring `core/stores/memberships.py`.

The relation is a finite partial function on coordinate space: the SQLite primary key
`(path, blob_sha, layer, chunk_index)` is a `Coord`, and everything else about an occupancy (its
atom and its two flags) is the value at that coordinate. Keying is therefore structural here: a
function has one value per coordinate, so two rows can never share a key. The family is exact
throughout, with no floats anywhere.
-/

open Finset

namespace Palace

/-- An occupancy's coordinates: the primary key `(path, blob_sha, layer, chunk_index)`. -/
structure Coord (P B L : Type*) where
  path : P
  blob : B
  layer : L
  chunk : ℕ
  deriving DecidableEq, Repr

/-- What sits at a coordinate: the atom (`content_id`) and the `current` and `tombstoned` flags. -/
structure Occupant (A : Type*) where
  atom : A
  current : Bool := false
  tombstoned : Bool := false
  deriving DecidableEq, Repr, Inhabited

/-- The membership relation `M`: a finite set of coordinates and the occupant at each. Values off
the support are never read. -/
@[ext]
structure Relation (P B L A : Type*) where
  support : Finset (Coord P B L)
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

omit [DecidableEq P] in
/-- **MEM-1** The atom projection is a multiset: an atom's multiplicity is its row count. -/
theorem count_atoms (v : A) :
    M.atoms.count v = (M.support.filter fun k ↦ (M.occ k).atom = v).card := by
  rw [atoms, Multiset.count_map, Finset.card_def, Finset.filter_val]
  congr 1
  exact Multiset.filter_congr fun k _ ↦ eq_comm

/-- **MEM-1** `n_doc ≤ n_occ`: each path holding `v` contributes at least one row. -/
theorem nDoc_le_nOcc (v : A) (currentOnly : Bool) :
    M.nDoc v currentOnly ≤ M.nOcc v currentOnly :=
  card_image_le

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

/-- **MEM-2** `Σ |fiber| = |M|`. -/
theorem sum_card_fiber : ∑ f ∈ M.versions, (M.fiber f).card = M.support.card :=
  (card_eq_sum_card_image version M.support).symm

/-- **MEM-2** Distinct versions have disjoint fibers. -/
theorem disjoint_fiber {f g : P × B} (h : f ≠ g) : Disjoint (M.fiber f) (M.fiber g) :=
  disjoint_filter.2 fun _ _ hf hg ↦ h (hf.symm.trans hg)

/-- **MEM-2** Every listed version has a non-empty fiber. -/
theorem fiber_nonempty {f : P × B} (h : f ∈ M.versions) : (M.fiber f).Nonempty := by
  obtain ⟨k, hk, rfl⟩ := mem_image.1 h
  exact ⟨k, mem_filter.2 ⟨hk, rfl⟩⟩

end Fibers

/-! ### MEM-4 and MEM-5: currency is reconciled on every landing -/

section Currency

variable [DecidableEq P] [DecidableEq B] [DecidableEq L]

/-- `reconcile_currency(path, head)`: on path `p`, exactly the rows of blob `h` are current;
every other path is untouched. -/
def reconcile (p : P) (h : B) : Relation P B L A where
  support := M.support
  occ k := if k.path = p then { M.occ k with current := decide (k.blob = h) } else M.occ k

omit [DecidableEq L] in
/-- On the reconciled path, a row is current iff its blob is the head. -/
theorem reconcile_current {p : P} {h : B} {k : Coord P B L} (hk : k.path = p) :
    ((M.reconcile p h).occ k).current = true ↔ k.blob = h := by
  simp [reconcile, hk]

omit [DecidableEq L] in
/-- Every other path is untouched. -/
theorem reconcile_of_ne {p : P} {h : B} {k : Coord P B L} (hk : k.path ≠ p) :
    (M.reconcile p h).occ k = M.occ k := by
  simp [reconcile, hk]

omit [DecidableEq L] in
/-- Reconciling twice is reconciling once: a converged re-land moves no flag. -/
theorem reconcile_reconcile (p : P) (h : B) :
    (M.reconcile p h).reconcile p h = M.reconcile p h := by
  ext k
  · rfl
  · by_cases hk : k.path = p <;> simp [reconcile, hk]

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

/-- The C1 bug's lander: it returns early when the version's fiber already exists. -/
def landShortCircuit (p : P) (h : B) (rows : List (Coord P B L × Occupant A)) :
    Relation P B L A :=
  if (p, h) ∈ M.versions then M else M.land p h rows

/-- Currency agrees with a head per path: a row is current iff its blob is its path's head. -/
def Coherent (head : P → Option B) : Prop :=
  ∀ k ∈ M.support, (M.occ k).current = true ↔ head k.path = some k.blob

omit [DecidableEq P] [DecidableEq B] [DecidableEq L] in
/-- **MEM-5** Coherent currency selects at most one fiber per path. -/
theorem Coherent.blob_eq {head : P → Option B} (hc : M.Coherent head) {k k' : Coord P B L}
    (hk : k ∈ M.support) (hk' : k' ∈ M.support) (hp : k.path = k'.path)
    (c : (M.occ k).current = true) (c' : (M.occ k').current = true) : k.blob = k'.blob := by
  have e := (hc k hk).1 c
  have e' := (hc k' hk').1 c'
  rw [hp, e'] at e
  exact (Option.some.inj e).symm

/-- **MEM-4** Landing keeps currency coherent with the newest head, whatever was landed before:
re-landing an old blob (a revert) makes it current again. -/
theorem Coherent.land {head : P → Option B} (hc : M.Coherent head) {p : P} {h : B}
    {rows : List (Coord P B L × Occupant A)} (hrows : ∀ r ∈ rows, r.1.path = p) :
    (M.land p h rows).Coherent (Function.update head p (some h)) := by
  intro k hk
  by_cases hp : k.path = p
  · rw [Relation.land, reconcile_current _ hp, hp, Function.update_self, Option.some_inj, eq_comm]
  · rw [Relation.land, reconcile_of_ne _ hp, Function.update_of_ne hp]
    have hkM : k ∈ M.support := by
      rcases mem_union.1 hk with h | h
      · exact h
      · obtain ⟨r, hr, rfl⟩ := List.mem_map.1 (List.mem_toFinset.1 h)
        exact absurd (hrows r hr) hp
    simp only [write, hkM, ↓reduceIte]
    exact hc k hkM

/-- `current_any(v)`: some current, un-tombstoned occupancy holds `v`. This is what the lance
`current` column caches and `repair_current_any` rebuilds from this store. -/
def currentAny (v : A) : Prop :=
  ∃ k ∈ M.support, (M.occ k).atom = v ∧ (M.occ k).tombstoned = false ∧ (M.occ k).current = true

instance [DecidableEq A] (v : A) : Decidable (M.currentAny v) := by
  unfold currentAny; infer_instance

instance (head : P → Option B) : Decidable (M.Coherent head) := by
  unfold Coherent; infer_instance

omit [DecidableEq B] [DecidableEq L] in
/-- **MEM-5** `current_any(v) ⇔ n_doc(v, t) > 0`. -/
theorem currentAny_iff [DecidableEq A] (v : A) : M.currentAny v ↔ 0 < M.nDoc v := by
  simp [currentAny, nDoc, holding, Finset.card_pos, Finset.Nonempty]

end Currency

end Relation

/-! ### MEM-3: slot runs are the adjacent-collapse run-length encoding -/

section Runs

variable {A : Type*} [DecidableEq A]

/-- A slot's occupant sequence along a first-parent chain: for each blob in order, the slot's
occupants in that version (`occupants b`, in chunk order). `slot_runs` reads exactly this. -/
def chainSequence {B : Type*} (occupants : B → List A) (chain : List B) : List A :=
  chain.flatMap occupants

/-- The runs (`slot_runs`): adjacent equal occupants collapsed, never distinct ones. -/
def runs (s : List A) : List A := s.destutter (· ≠ ·)

/-- The supersession edges (`slot_edges`): consecutive runs. -/
def edges (s : List A) : List (A × A) := (runs s).zip (runs s).tail

/-- The places where the sequence changes occupant. -/
def changes (s : List A) : ℕ := ((s.zip s.tail).filter fun p ↦ p.1 ≠ p.2).length

/-- **MEM-3** `|edges| = |runs| − 1`. -/
theorem length_edges (s : List A) : (edges s).length = (runs s).length - 1 := by
  simp [edges, List.length_zip, List.length_tail]

omit [DecidableEq A] in
/-- Consecutive elements of a chain are related. -/
theorem rel_of_mem_zip_tail {R : A → A → Prop} :
    ∀ {l : List A}, l.IsChain R → ∀ {e : A × A}, e ∈ l.zip l.tail → R e.1 e.2
  | [], _, _, he => by simp at he
  | [_], _, _, he => by simp at he
  | a :: b :: l, h, e, he => by
    rw [List.tail_cons, List.zip_cons_cons, List.mem_cons] at he
    rcases he with rfl | he
    · exact (List.isChain_cons_cons.1 h).1
    · exact rel_of_mem_zip_tail (List.isChain_cons_cons.1 h).2 he

/-- **MEM-3** The two ends of an edge differ. -/
theorem fst_ne_snd_of_mem_edges {s : List A} {e : A × A} (he : e ∈ edges s) : e.1 ≠ e.2 :=
  rel_of_mem_zip_tail (List.isChain_destutter (· ≠ ·) s) he

/-- **MEM-3** A revert stays visible: `A → B → A` is three runs and two edges. -/
theorem runs_revert {a b : A} (h : a ≠ b) : runs [a, b, a] = [a, b, a] := by
  simp [runs, List.destutter, List.destutter', h, Ne.symm h]

theorem length_destutter' (a : A) :
    ∀ l : List A, (l.destutter' (· ≠ ·) a).length = changes (a :: l) + 1
  | [] => by simp [changes]
  | b :: l => by
    by_cases hab : a = b
    · subst hab
      rw [List.destutter'_cons, ite_eq_right (not_not.2 rfl), length_destutter' a l]
      simp [changes]
    · rw [List.destutter'_cons, ite_eq_left hab, List.length_cons, length_destutter' b l]
      simp [changes, hab]

/-- **MEM-3** Adjacent collapse, counted: a non-empty sequence has one more run than changes. -/
theorem length_runs {s : List A} (hs : s ≠ []) : (runs s).length = changes s + 1 := by
  obtain ⟨a, l, rfl⟩ := List.exists_cons_of_ne_nil hs
  rw [runs, List.destutter_cons', length_destutter']

/-- **MEM-3** One edge per change of occupant. -/
theorem length_edges_eq_changes (s : List A) : (edges s).length = changes s := by
  rcases eq_or_ne s [] with rfl | hs
  · simp [edges, runs, changes]
  · rw [length_edges, length_runs hs, Nat.add_sub_cancel]

end Runs

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
