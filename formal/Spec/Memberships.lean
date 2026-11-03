module

public import Palace.Memberships.Defs

/-!
# The membership relation: MEM-1, MEM-2, MEM-3, MEM-4, MEM-5, the statements

Statements of the ledger's membership laws (dn-mathematical-foundations §2.2, seed table I, and
the structure settled in §2.3.1), mirroring `core/stores/memberships.py`.

The relation is a finite partial function on coordinate space: the SQLite primary key
`(path, blob_sha, layer, chunk_index)` is a `Coord`, and everything else about an occupancy (its
atom and its two flags) is the value at that coordinate. Keying is therefore structural here: a
function has one value per coordinate, so two rows can never share a key. The family is exact
throughout, with no floats anywhere.

These are the laws of `Palace/Memberships.lean` as the ledger cites them, each with its proof
left as `sorry`. `lake comparator` checks that the `Palace` library proves each one
exactly as stated here, from the standard axioms alone.
-/

@[expose] public section

open Finset

namespace Palace

namespace Relation

variable {P B L A : Type*} (M : Relation P B L A)

/-! ### MEM-1: the atom projection is a multiset, and `n_doc ≤ n_occ` -/

section Counts

variable [DecidableEq P] [DecidableEq A]

omit [DecidableEq P] in
/-- **MEM-1** The atom projection is a multiset: an atom's multiplicity is its row count. -/
theorem count_atoms (v : A) :
    M.atoms.count v = (M.support.filter fun k ↦ (M.occ k).atom = v).card :=
  sorry

/-- **MEM-1** `n_doc ≤ n_occ`: each path holding `v` contributes at least one row. -/
theorem nDoc_le_nOcc (v : A) (currentOnly : Bool) :
    M.nDoc v currentOnly ≤ M.nOcc v currentOnly :=
  sorry

end Counts

/-! ### MEM-2: the version fibers partition `M` -/

section Fibers

variable [DecidableEq P] [DecidableEq B]

/-- **MEM-2** `Σ |fiber| = |M|`. -/
theorem sum_card_fiber : ∑ f ∈ M.versions, (M.fiber f).card = M.support.card :=
  sorry

/-- **MEM-2** Distinct versions have disjoint fibers. -/
theorem disjoint_fiber {f g : P × B} (h : f ≠ g) : Disjoint (M.fiber f) (M.fiber g) :=
  sorry

/-- **MEM-2** Every listed version has a non-empty fiber. -/
theorem fiber_nonempty {f : P × B} (h : f ∈ M.versions) : (M.fiber f).Nonempty :=
  sorry

end Fibers

/-! ### MEM-4 and MEM-5: currency is reconciled on every landing -/

section Currency

variable [DecidableEq P] [DecidableEq B] [DecidableEq L]

omit [DecidableEq P] [DecidableEq B] [DecidableEq L] in
/-- **MEM-5** Coherent currency selects at most one fiber per path. -/
theorem Coherent.blob_eq {head : P → Option B} (hc : M.Coherent head) {k k' : Coord P B L}
    (hk : k ∈ M.support) (hk' : k' ∈ M.support) (hp : k.path = k'.path)
    (c : (M.occ k).current = true) (c' : (M.occ k').current = true) : k.blob = k'.blob :=
  sorry

/-- **MEM-4** Landing keeps currency coherent with the newest head, whatever was landed before:
re-landing an old blob (a revert) makes it current again. -/
theorem Coherent.land {head : P → Option B} (hc : M.Coherent head) {p : P} {h : B}
    {rows : List (Coord P B L × Occupant A)} (hrows : ∀ r ∈ rows, r.1.path = p) :
    (M.land p h rows).Coherent (Function.update head p (some h)) :=
  sorry

omit [DecidableEq B] [DecidableEq L] in
/-- **MEM-5** `current_any(v) ⇔ n_doc(v, t) > 0`. -/
theorem currentAny_iff [DecidableEq A] (v : A) : M.currentAny v ↔ 0 < M.nDoc v :=
  sorry

end Currency

end Relation

/-! ### MEM-3: slot runs are the adjacent-collapse run-length encoding -/

section Runs

variable {A : Type*} [DecidableEq A]

/-- **MEM-3** `|edges| = |runs| − 1`. -/
theorem length_edges (s : List A) : (edges s).length = (runs s).length - 1 :=
  sorry

/-- **MEM-3** The two ends of an edge differ. -/
theorem fst_ne_snd_of_mem_edges {s : List A} {e : A × A} (he : e ∈ edges s) : e.1 ≠ e.2 :=
  sorry

/-- **MEM-3** A revert stays visible: `A → B → A` is three runs and two edges. -/
theorem runs_revert {a b : A} (h : a ≠ b) : runs [a, b, a] = [a, b, a] :=
  sorry

/-- **MEM-3** Adjacent collapse, counted: a non-empty sequence has one more run than changes. -/
theorem length_runs {s : List A} (hs : s ≠ []) : (runs s).length = changes s + 1 :=
  sorry

/-- **MEM-3** One edge per change of occupant. -/
theorem length_edges_eq_changes (s : List A) : (edges s).length = changes s :=
  sorry

end Runs

end Palace
