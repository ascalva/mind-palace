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
* the cache is complete on `C`: no crash fell between a commit and `_refresh_held`. A drifted
  cache drops results (fail-closed), but `_refresh_held` rewrites a touched atom's whole held set,
  so an uncleared write that shares the atom restores them: `drift_interferes`;
* every path has one stratum, fixed in advance (A3.6): a landing whose path lives in another class
  is refused, and that refusal reads uncleared relations: `stratum_interferes`.

The model is exact and finite: classes, paths, digests and atoms are any finite or ordered types,
and a land carries one fiber (the code lands several in one transaction).

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

end Witness

end Palace.Plane
