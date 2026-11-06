module

public import Palace.Plane.Defs

/-!
# The shared plane: no-leak and noninterference (A3, A3.5), the statements

Statements of the shared prose plane's information-flow laws (dn-vector-membership-store
Amendment A3), mirroring `core/stores/plane.py`: atoms stored once in a shared table, the occupancy
relation partitioned by provenance class (`occ_<c>`, `sup_<c>`), and the `held`/`held_ever`
prefilter cache that search narrows by before the cleared join decides.

The plane's header claims two things. No-leak: a read under clearance `C` returns only records of
classes in `C`. Noninterference (A3.5, Goguen and Meseguer 1982): mutating `M_c` for `c ∉ C`
changes no `C`-read. Here the first holds under any cache, and the second is proved for traces in
Rushby's unwinding form (1992), under hypotheses the code does not state:

* the atom table is content-addressed: an atom's text and vector are a function of its id, so the
  distance to a query is `dist a` (the property test's embedder is deterministic);
* nearest-neighbour search is exact, with ties broken by atom id (the test's in-memory table).
  LanceDB breaks exact ties by physical row order, and `set_held` rewrites a row to the end, so an
  uncleared write that touches one of two tied cleared atoms can swap them across the cut
  (measured on lancedb 0.33.0; no exact vector ties among the live prose atoms on 2026-11-01);
* the cache is complete on `C`. With the cache written last, a crash between a commit and
  `_refresh_held` drifted it: a drifted cache drops results (fail-closed), but `_refresh_held`
  rewrites a touched atom's whole held set, so an uncleared write that shares the atom restores
  them, `drift_interferes`. A land now writes its cache's additions first, so no crash of a land
  leaves the cache incomplete (the crash points below);
* every path has one stratum, fixed in advance (A3.6): a landing whose path lives in another class
  is refused, and that refusal reads uncleared relations: `stratum_interferes`.

The model is exact and finite: classes, paths, digests and atoms are any finite or ordered types,
and a land carries one fiber (the code lands several in one transaction).

The store around the plane (PLN-6, #37) adds the physical rows beside its atoms: records of either
lane, and the shed code atoms the membership relation names. A plane row's id is payload `Occ` does
not carry, so the scoped re-key, which writes ids only, leaves the plane's state as it is. The
unscoped form is stated over the lands it makes from the empty plane, the fibers that its read of
the current rows regroups into passed in (`fs`).

These are the laws of `Palace/Plane.lean` as the ledger cites them, each with its proof
left as `sorry`. `lake comparator` checks that the `Palace` library proves each one
exactly as stated here, from the standard axioms alone.
-/

@[expose] public section

open Finset

namespace Palace.Plane

variable {K P D A : Type*}

/-! ### The prefilter -/

section View

variable [DecidableEq A] [DecidableEq K]

/-- **PLN-3** With a cache complete on `C`, the prefilter loses nothing the cleared join would keep:
the search then ranks every atom a cleared relation holds. -/
theorem prefilter_cleared [Fintype K] {C : Finset K} {s : State K P D A} (hs : Complete C s)
    (sup : Bool) :
    (prefilter C s sup).filter (cleared C s sup ·) = s.table.filter (cleared C s sup ·) :=
  sorry

end View

/-! ### Search: the window-widening loop over an exact nearest-neighbour search -/

section Search

variable {Δ : Type*} [LinearOrder Δ] [LinearOrder A]

variable [DecidableEq K] [DecidableEq P] [DecidableEq D]

/-- **PLN-3** The search loop returns the first `k` atoms of the exact ranking among those the cache
prefilters and a cleared relation holds (all of them, when the cache is complete on `C`:
`prefilter_cleared`). -/
theorem search_eq (dist : A → Δ) (C : Finset K) (s : State K P D A) (k : ℕ) (sup : Bool) :
    search dist C s k sup = ((byDist dist ((prefilter C s sup).filter (cleared C s sup ·))).take
      k).map fun a ↦ (a, hitOccs C s sup a) :=
  sorry

/-- **PLN-1, no-leak** (A3), under any cache: every hit is a table atom, has a cleared occupancy,
and carries only rows of cleared classes that hold it, so `PlaneHit`'s sealed constructor never
raises on the plane's own reads. A stale cache can drop hits, never add one. -/
theorem search_sound {dist : A → Δ} {C : Finset K} {s : State K P D A} {k : ℕ} {sup : Bool}
    {a : A} {os : Finset (K × Occ P D A)} (h : (a, os) ∈ search dist C s k sup) :
    a ∈ s.table ∧ os.Nonempty ∧ ∀ x ∈ os, x.1 ∈ C ∧ x.2 ∈ s.occ x.1 ∧ x.2.holds sup a :=
  sorry

end Search

/-! ### Writing: land, retire, purge and repair -/

section Write

variable [DecidableEq P] [LinearOrder D] [DecidableEq A] [Fintype K] [DecidableEq K]

/-! #### The cache stays coherent -/

/-- **PLN-4** A land keeps the `held` cache coherent. -/
theorem coherent_land {f : Fiber K P D A} {s : State K P D A} (hc : Coherent s) (hw : WF s) :
    Coherent (land f s) :=
  sorry

/-- **PLN-4** So does a retire. -/
theorem coherent_retire {c : K} {p : P} {s : State K P D A} (hc : Coherent s) :
    Coherent (retire c p s) :=
  sorry

omit [DecidableEq P] [DecidableEq K] in
/-- **PLN-4** So does a purge. -/
theorem coherent_purge {d : D} {s : State K P D A} (hc : Coherent s) : Coherent (purge d s) :=
  sorry

omit [DecidableEq P] [LinearOrder D] [DecidableEq K] in
/-- **PLN-4** And `repair` makes any cache coherent. -/
theorem coherent_repair (s : State K P D A) : Coherent (repair s) :=
  sorry

/-! #### Purge (A3.7) -/

omit [DecidableEq P] [DecidableEq K] in
/-- **PLN-5** After a purge no row and no edge names the digest. -/
theorem purge_clears (d : D) (s : State K P D A) (c : K) :
    (∀ o ∈ (purge d s).occ c, o.digest ≠ d) ∧
      ∀ e ∈ (purge d s).sup c, e.old ≠ some d ∧ e.new ≠ some d :=
  sorry

omit [DecidableEq P] [DecidableEq K] in
/-- **PLN-5** Nothing private lingers: every atom the digest's rows held is deleted, or a remaining
row still holds it. -/
theorem purge_no_orphan {d : D} {s : State K P D A} {a : A} (ha : a ∈ byDigest d s)
    (ht : a ∈ (purge d s).table) : ∃ c, ∃ o ∈ (purge d s).occ c, o.atom = a :=
  sorry

omit [DecidableEq P] [DecidableEq K] in
/-- **PLN-5** Re-running the purge finishes one a crash interrupted after its atom delete. -/
theorem purge_purgeAtoms (d : D) (s : State K P D A) : purge d (purgeAtoms d s) = purge d s :=
  sorry

end Write

/-! ### Noninterference over traces (A3.5) -/

section Trace

variable [DecidableEq P] [LinearOrder D] [DecidableEq A] [Fintype K] [DecidableEq K]

/-- **PLN-2, noninterference** (A3.5), in Goguen and Meseguer's form, by Rushby's unwinding: after
any trace of writes that keep each path at its stratum, a reader under `C` sees what it would have
seen had only the cleared writes, the purges and the repairs happened. -/
theorem noninterference {κ : P → K} {C : Finset K} :
    ∀ (ops : List (Op K P D A)) {s t : State K P D A}, Good κ s → Good κ t →
      view C s = view C t → (∀ op ∈ ops, op.Respects κ) →
      view C (run ops s) = view C (run (ops.filter (·.visible C)) t) :=
  sorry

end Trace

section Search

variable {Δ : Type*} [LinearOrder Δ] [DecidableEq P] [LinearOrder D] [LinearOrder A] [Fintype K]
  [DecidableEq K]

/-- **PLN-2, noninterference for search**: the same, for every search under `C`. -/
theorem noninterference_search (dist : A → Δ) {κ : P → K} {C : Finset K}
    (ops : List (Op K P D A)) {s : State K P D A} (hs : Good κ s)
    (hops : ∀ op ∈ ops, op.Respects κ) (k : ℕ) (sup : Bool) :
    search dist C (run ops s) k sup = search dist C (run (ops.filter (·.visible C)) s) k sup :=
  sorry

end Search

/-! ### Crash points of a land (PLN-4, dn-ingest-door §9 item 7) -/

section Crash

variable [DecidableEq P] [LinearOrder D] [DecidableEq A] [Fintype K] [DecidableEq K]

omit [DecidableEq P] [LinearOrder D] in
/-- **PLN-4** A crash before a land's transaction, with the atoms and the cache's additions
written, leaves the cache complete on every class, from a complete one with no dangling row. -/
theorem complete_landAdd {f : Fiber K P D A} {s : State K P D A} (hc : Complete univ s)
    (hw : WF s) : Complete univ (landAdd f s) :=
  sorry

/-- **PLN-4** So does a crash after the transaction (or after its rollback, when refused): every
atom the transaction gave a row names the row's class already. -/
theorem complete_landAddCommit {f : Fiber K P D A} {s : State K P D A} (hc : Complete univ s)
    (hw : WF s) : Complete univ (landAddCommit f s) :=
  sorry

/-- **PLN-4** A land written in the code's order, the cache's additions first and its removals
last, ends where `land` does, so every law about `land` holds of it. -/
theorem land_of_landAdd {f : Fiber K P D A} {s : State K P D A} (hr : ¬Refused f s) :
    refresh (landAffected (s.occ f.cls) f) (commit f (landAdd f s)) = land f s :=
  sorry

/-- **PLN-4** A refused land whose additions are taken back after the rollback ends where `land`
does, from a coherent plane with no dangling row. -/
theorem land_of_landAdd_refused {f : Fiber K P D A} {s : State K P D A} (hc : Coherent s)
    (hw : WF s) (hr : Refused f s) : refresh f.atoms (landAdd f s) = land f s :=
  sorry

end Crash

section CrashSearch

variable {Δ : Type*} [LinearOrder Δ] [DecidableEq P] [LinearOrder D] [LinearOrder A] [Fintype K]
  [DecidableEq K]

/-- **PLN-4** A cache is read for what it covers and nothing else: two planes that differ only in
their caches, both complete and with no dangling row, answer every search alike after any trace
of writes, so excess entries are invisible to every reader, now and later. -/
theorem search_run_of_sameRel (dist : A → Δ) {C : Finset K} (ops : List (Op K P D A))
    {s t : State K P D A} (h : SameRel s t) (hs : Complete univ s) (hws : WF s)
    (ht : Complete univ t) (hwt : WF t) (k : ℕ) (sup : Bool) :
    search dist C (run ops s) k sup = search dist C (run ops t) k sup :=
  sorry

/-- **PLN-4** A land that writes its cache's additions first can crash after its transaction with
no reader the wiser: from a coherent plane with no dangling row, every search after any trace
answers as it would had the land finished. -/
theorem search_after_crash (dist : A → Δ) {C : Finset K} (ops : List (Op K P D A))
    {f : Fiber K P D A} {s : State K P D A} (hc : Coherent s) (hw : WF s) (k : ℕ) (sup : Bool) :
    search dist C (run ops (landAddCommit f s)) k sup =
      search dist C (run ops (land f s)) k sup :=
  sorry

end CrashSearch

/-! ### The chunk-key migration (#37) -/

namespace Store

variable {I T : Type*} [DecidableEq P] [DecidableEq I] [DecidableEq T]

/-- **PLN-6** The scoped re-key (`rekey_store`, the chunk-key migration, #37) moves only the ids of
note records. It leaves the plane's state as it is (its relations up to their row ids, its logs,
its table and its cache); it keeps every row outside the note lane, the shed code atoms the
membership relation names and the code records; it gives every note record its doc-scoped key;
and it keeps every row's document, text and lane, so a row is lost only by merging with another
of the same document and text (§3). -/
theorem rekey_keeps (key : Option P → T → I) (s : Store K P D A I T) :
    (s.rekey key).plane = s.plane ∧
      (s.rekey key).phys.filter (fun r ↦ ¬r.Note) = s.phys.filter (fun r ↦ ¬r.Note) ∧
      (∀ r ∈ (s.rekey key).phys, r.Note → r.id = key r.path r.text) ∧
      (s.rekey key).phys.image Phys.content = s.phys.image Phys.content :=
  sorry

/-- **PLN-6** What the plane's laws need kept: from a state `Good κ` holds of (a coherent cache,
no dangling row, every path at one stratum, the hypotheses of PLN-2 and of PLN-4's land), the
re-key leaves a state it holds of, with the same view under every clearance; with the plane's
state unchanged, every search answers as before and PLN-1 to PLN-5 hold after it as before. -/
theorem rekey_good [DecidableEq A] [Fintype K] [DecidableEq K] {κ : P → K}
    (key : Option P → T → I) {s : Store K P D A I T} (hs : Good κ s.plane) :
    Good κ (s.rekey key).plane ∧ ∀ C, view C (s.rekey key).plane = view C s.plane :=
  sorry

/-- **PLN-6** Re-running the re-key changes nothing. -/
theorem rekey_idem (key : Option P → T → I) (s : Store K P D A I T) :
    (s.rekey key).rekey key = s.rekey key :=
  sorry

variable [LinearOrder D] [DecidableEq A] [Fintype K] [DecidableEq K]

/-- **PLN-6, the unscoped form.** `reset()` and adding back what `all_rows()` returns leaves no
shed atom row, whatever the store held: every code atom the membership relation names is gone. -/
theorem rekeyReset_drops_atoms (key : Option P → T → I) (fs : List (Fiber K P D A))
    (s : Store K P D A I T) : ∀ r ∈ (s.rekeyReset key fs).phys, r.path.isSome = true :=
  sorry

end Store

/-! ### Where the hypotheses bite -/

namespace Witness

/-- **PLN-2, the cache-drift channel.** After the crash, the cleared document's atom has an empty
cache and search under `{0}` misses it (fail-closed). The uncleared land leaves the cleared view
alone, yet it refreshes the shared atom's whole held set, and the hit comes back: an uncleared write
changed a cleared read. Noninterference needs a cache complete on `C`. -/
theorem drift_interferes :
    view {0} (land fy drifted) = view {0} drifted ∧
      search (fun _ ↦ (0 : ℕ)) {0} drifted 1 false = [] ∧
      search (fun _ ↦ (0 : ℕ)) {0} (land fy drifted) 1 false ≠ [] :=
  sorry

/-- **PLN-2, the stratum channel.** Path 0 lands in class 1, then in class 0. The cleared land is
refused because the uncleared one holds the path, so the cleared view differs from the trace without
the uncleared write. Noninterference needs every path at one stratum fixed in advance. -/
theorem stratum_interferes :
    view {0} (run [.land ⟨1, 0, 0, [(0, 0)]⟩, .land ⟨0, 0, 0, [(0, 0)]⟩]
        (empty : State (Fin 2) (Fin 2) (Fin 1) (Fin 1))) ≠
      view {0} (run ([.land ⟨1, 0, 0, [(0, 0)]⟩, .land ⟨0, 0, 0, [(0, 0)]⟩].filter
        (·.visible {0})) (empty : State (Fin 2) (Fin 2) (Fin 1) (Fin 1))) :=
  sorry

/-- **PLN-6, the unscoped form drops the history.** `all_rows()` returns the plane's current rows,
which regroup into the note's second version alone (`vb`); after `reset()` and adding them back,
the reader under `{0}` no longer sees the first version's rows or the edge that superseded it,
whatever the key. The scoped re-key leaves the view as it is. -/
theorem rekeyReset_drops_history (key : Option (Fin 1) → Fin 2 → ℕ) :
    view {0} (edited.rekeyReset key [vb]).plane ≠ view {0} edited.plane ∧
      view {0} (edited.rekey key).plane = view {0} edited.plane :=
  sorry

/-- **PLN-6, the unscoped form merges rows.** The note lane's key, given to code records, merges two
layers' records of one document and one text into one row; before the guard, it merges the two
shed atoms of one text too, both their ids gone, whatever the key. The scoped re-key keeps all four
rows. -/
theorem rekeyReset_merges (key : Option (Fin 1) → Fin 2 → ℕ) :
    (edited.rekeyReset key [vb]).phys.card = 1 ∧
      ((edited.rekeyResetUnguarded key [vb]).phys.filter fun r ↦ r.path = none).card = 1 ∧
      edited.phys.card = 4 ∧ (edited.rekey key).phys = edited.phys :=
  sorry


/-- **PLN-4, what a re-run does not do** (dn-ingest-door §9 item 7). The note's second version
crashes after its transaction, and landing it again leaves the first version's atom cached as held,
which no current row holds: the re-run refreshes the atoms it lands and frees, and the first run's
freed atoms are neither. The cache stays stale by excess, complete all the same, until `repair`. -/
theorem rerun_keeps_excess :
    ¬Coherent (land vb (landAddCommit vb (land va empty))) ∧
      Complete univ (land vb (landAddCommit vb (land va empty))) ∧
      Coherent (repair (land vb (landAddCommit vb (land va empty)))) :=
  sorry

end Witness

end Palace.Plane
