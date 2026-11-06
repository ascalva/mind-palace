module

public import Palace.Plane.Defs
public import Mathlib.Data.Finset.Sort
public import Mathlib.Data.Finset.Union
public import Mathlib.Data.Fintype.Basic
public import Mathlib.Order.Prod.Lex.Basic

/-!
# The shared plane: no-leak and noninterference (A3, A3.5)

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
-/

@[expose] public section

open Finset

namespace Palace.Plane

variable {K P D A : Type*}

section Truth

variable [Fintype K] [DecidableEq A]

theorem Coherent.complete {s : State K P D A} (h : Coherent s) (C : Finset K) : Complete C s :=
  fun a ha sup _ _ hc ↦ (h a ha sup).symm ▸ hc

end Truth

/-! ### What a reader under `C` sees -/

section View

variable [DecidableEq A] [DecidableEq K]

theorem occ_eq_of_view {C : Finset K} {s t : State K P D A} (h : view C s = view C t) {c : K}
    (hc : c ∈ C) : s.occ c = t.occ c := by
  have := congrFun (congrArg Prod.fst h) c
  simp only [view, hc, ↓reduceIte, Prod.mk.injEq] at this
  exact this.1

theorem sup_eq_of_view {C : Finset K} {s t : State K P D A} (h : view C s = view C t) {c : K}
    (hc : c ∈ C) : s.sup c = t.sup c := by
  have := congrFun (congrArg Prod.fst h) c
  simp only [view, hc, ↓reduceIte, Prod.mk.injEq] at this
  exact this.2

theorem refs_eq_of_view {C : Finset K} {s t : State K P D A} (h : view C s = view C t) :
    refs C s = refs C t :=
  Finset.biUnion_congr rfl fun c hc ↦ by rw [occ_eq_of_view h hc]

theorem cleared_eq_of_view {C : Finset K} {s t : State K P D A} (h : view C s = view C t)
    (sup : Bool) : cleared C s sup = cleared C t sup := by
  funext a
  have : (∃ c ∈ C, ∃ o ∈ s.occ c, o.holds sup a) ↔ ∃ c ∈ C, ∃ o ∈ t.occ c, o.holds sup a :=
    exists_congr fun c ↦ and_congr_right fun hc ↦ by rw [occ_eq_of_view h hc]
  simp only [cleared, this]

omit [DecidableEq K] in
theorem mem_refs_of_cleared {C : Finset K} {s : State K P D A} {sup : Bool} {a : A}
    (h : cleared C s sup a = true) : a ∈ refs C s := by
  simp only [cleared, decide_eq_true_eq] at h
  obtain ⟨c, hc, o, ho, rfl, -⟩ := h
  exact Finset.mem_biUnion.2 ⟨c, hc, Finset.mem_image.2 ⟨o, ho, rfl⟩⟩

/-- **PLN-3** With a cache complete on `C`, the prefilter loses nothing the cleared join would keep:
the search then ranks every atom a cleared relation holds. -/
theorem prefilter_cleared [Fintype K] {C : Finset K} {s : State K P D A} (hs : Complete C s)
    (sup : Bool) :
    (prefilter C s sup).filter (cleared C s sup ·) = s.table.filter (cleared C s sup ·) := by
  ext a
  simp only [prefilter, Finset.mem_filter]
  constructor
  · rintro ⟨⟨ha, -⟩, hcl⟩
    exact ⟨ha, hcl⟩
  · rintro ⟨ha, hcl⟩
    refine ⟨⟨ha, ?_⟩, hcl⟩
    simp only [cleared, decide_eq_true_eq] at hcl
    obtain ⟨c, hc, o, ho, hho⟩ := hcl
    exact ⟨c, Finset.mem_inter.2 ⟨hs a ha sup c hc
      (Finset.mem_filter.2 ⟨Finset.mem_univ _, o, ho, hho⟩), hc⟩⟩

theorem table_cleared_eq_of_view {C : Finset K} {s t : State K P D A} (hv : view C s = view C t)
    (sup : Bool) :
    s.table.filter (cleared C s sup ·) = t.table.filter (cleared C t sup ·) := by
  have h2 : s.table ∩ refs C s = t.table ∩ refs C t := congrArg Prod.snd hv
  rw [cleared_eq_of_view hv]
  ext a
  simp only [Finset.mem_filter, and_congr_left_iff]
  intro hcl
  have hs : a ∈ refs C s := refs_eq_of_view hv ▸ mem_refs_of_cleared hcl
  have ht : a ∈ refs C t := mem_refs_of_cleared hcl
  constructor
  · intro ha
    exact (Finset.mem_inter.1 (h2 ▸ Finset.mem_inter.2 ⟨ha, hs⟩)).1
  · intro ha
    exact (Finset.mem_inter.1 (h2.symm ▸ Finset.mem_inter.2 ⟨ha, ht⟩)).1

end View

/-! ### Search: the window-widening loop over an exact nearest-neighbour search -/

section Widen

variable [DecidableEq A]

omit [DecidableEq A] in
theorem take_eq_take_of_prefix {l₁ l₂ : List A} (h : l₁ <+: l₂) {k : ℕ} (hk : k ≤ l₁.length) :
    l₁.take k = l₂.take k := by
  rw [List.prefix_iff_eq_take.1 h, List.take_take, Nat.min_eq_left hk]

/-- With an exact search, the fresh candidates of a round are the next slice of the ranking. -/
theorem filter_not_mem_take {ps : List A} (hps : ps.Nodup) {m n : ℕ} (hmn : m ≤ n) :
    (ps.take n).filter (fun a ↦ a ∉ ps.take m) = (ps.take n).drop m := by
  have hsplit : ps.take m ++ (ps.take n).drop m = ps.take n := by
    conv_rhs => rw [← List.take_append_drop m (ps.take n)]
    rw [List.take_take, Nat.min_eq_left hmn]
  have hnd : (ps.take m ++ (ps.take n).drop m).Nodup := by
    rw [hsplit]
    exact hps.sublist (List.take_sublist _ _)
  conv_lhs => rw [← hsplit]
  rw [List.filter_append, List.filter_eq_nil_iff.2 (fun a ha ↦ by simpa using ha), List.nil_append,
    List.filter_eq_self]
  intro a ha
  have hdis := (List.nodup_append.1 hnd).2.2
  simpa using fun h ↦ hdis a h a ha rfl

theorem widen_take {ps : List A} (hps : ps.Nodup) (T : A → Bool) (k : ℕ) :
    ∀ fuel m limit, m < limit → ps.length ≤ fuel + m →
      widen (ps.take ·) T k fuel (ps.take m) ((ps.take m).filter T) limit =
        (ps.filter T).take k := by
  intro fuel
  induction fuel with
  | zero =>
    intro m limit _ hlen
    simp only [widen, List.take_of_length_le (by omega : ps.length ≤ m)]
  | succ fuel ih =>
    intro m limit hml hlen
    have hseen : ps.take m ++ (ps.take limit).drop m = ps.take limit := by
      conv_rhs => rw [← List.take_append_drop m (ps.take limit)]
      rw [List.take_take, Nat.min_eq_left hml.le]
    have hhits : (ps.take m).filter T ++ ((ps.take limit).drop m).filter T =
        (ps.take limit).filter T := by
      rw [← List.filter_append, hseen]
    simp only [widen, filter_not_mem_take hps hml.le, hhits, hseen]
    split_ifs with h
    · rcases h with h | h
      · exact take_eq_take_of_prefix ((List.take_prefix _ _).filter T) h
      · rw [List.length_take] at h
        rw [List.take_of_length_le (by omega : ps.length ≤ limit)]
    · exact ih limit (limit * 4) (by omega) (by omega)

/-- The loop returns the first `k` atoms of the exact ranking that the cleared join holds. -/
theorem widen_eq {ps : List A} (hps : ps.Nodup) (T : A → Bool) (k : ℕ) :
    widen (ps.take ·) T k ps.length [] [] k = (ps.filter T).take k := by
  rcases Nat.eq_zero_or_pos k with rfl | hk
  · cases h : ps.length <;> simp [widen]
  · simpa using widen_take hps T k ps.length 0 k hk (by omega)

end Widen

section Search

variable {Δ : Type*} [LinearOrder Δ] [LinearOrder A]

omit [LinearOrder Δ] [LinearOrder A] in
theorem key_injective (dist : A → Δ) : Function.Injective (key dist) := fun a b h ↦ by
  simpa [key] using congrArg (fun x ↦ (ofLex x).2) h

theorem mem_byDist {dist : A → Δ} {S : Finset A} {a : A} : a ∈ byDist dist S ↔ a ∈ S := by
  simp [byDist, key]

theorem byDist_pairwise (dist : A → Δ) (S : Finset A) :
    (byDist dist S).Pairwise fun a b ↦ key dist a < key dist b := by
  have hs := (Finset.sortedLT_sort (S.image (key dist))).pairwise
  rw [byDist, List.pairwise_map]
  refine hs.imp_of_mem fun {x y} hx hy hxy ↦ ?_
  rw [Finset.mem_sort, Finset.mem_image] at hx hy
  obtain ⟨a, -, rfl⟩ := hx
  obtain ⟨b, -, rfl⟩ := hy
  simpa [key] using hxy

theorem nodup_of_pairwise_key {dist : A → Δ} {l : List A}
    (hl : l.Pairwise fun a b ↦ key dist a < key dist b) : l.Nodup :=
  hl.imp fun {a b} h hab ↦ by subst hab; exact lt_irrefl _ h

theorem byDist_nodup (dist : A → Δ) (S : Finset A) : (byDist dist S).Nodup :=
  nodup_of_pairwise_key (byDist_pairwise dist S)

/-- A list ranked by the key, with the members of `S`, is `byDist S`. -/
theorem eq_byDist {dist : A → Δ} {S : Finset A} {l : List A}
    (hl : l.Pairwise fun a b ↦ key dist a < key dist b) (h : ∀ a, a ∈ l ↔ a ∈ S) :
    l = byDist dist S := by
  have hnd : l.Nodup := nodup_of_pairwise_key hl
  refine List.Perm.eq_of_pairwise (fun a b _ _ hab hba ↦ absurd (hab.trans hba) (lt_irrefl _))
    hl (byDist_pairwise dist S) ((List.perm_ext_iff_of_nodup hnd (byDist_nodup dist S)).2 ?_)
  intro a
  rw [h, mem_byDist]

theorem byDist_filter (dist : A → Δ) (S : Finset A) (p : A → Bool) :
    (byDist dist S).filter p = byDist dist (S.filter (p ·)) :=
  eq_byDist ((byDist_pairwise dist S).filter p) fun a ↦ by simp [mem_byDist]

variable [DecidableEq K] [DecidableEq P] [DecidableEq D]

/-- **PLN-3** The search loop returns the first `k` atoms of the exact ranking among those the cache
prefilters and a cleared relation holds (all of them, when the cache is complete on `C`:
`prefilter_cleared`). -/
theorem search_eq (dist : A → Δ) (C : Finset K) (s : State K P D A) (k : ℕ) (sup : Bool) :
    search dist C s k sup = ((byDist dist ((prefilter C s sup).filter (cleared C s sup ·))).take
      k).map fun a ↦ (a, hitOccs C s sup a) := by
  simp only [search, widen_eq (byDist_nodup _ _), byDist_filter]

/-- **PLN-1, no-leak** (A3), under any cache: every hit is a table atom, has a cleared occupancy,
and carries only rows of cleared classes that hold it, so `PlaneHit`'s sealed constructor never
raises on the plane's own reads. A stale cache can drop hits, never add one. -/
theorem search_sound {dist : A → Δ} {C : Finset K} {s : State K P D A} {k : ℕ} {sup : Bool}
    {a : A} {os : Finset (K × Occ P D A)} (h : (a, os) ∈ search dist C s k sup) :
    a ∈ s.table ∧ os.Nonempty ∧ ∀ x ∈ os, x.1 ∈ C ∧ x.2 ∈ s.occ x.1 ∧ x.2.holds sup a := by
  rw [search_eq, List.mem_map] at h
  obtain ⟨b, hb, hba⟩ := h
  simp only [Prod.mk.injEq] at hba
  obtain ⟨rfl, rfl⟩ := hba
  have hb' := mem_byDist.1 (List.mem_of_mem_take hb)
  simp only [prefilter, Finset.mem_filter, cleared, decide_eq_true_eq] at hb'
  obtain ⟨⟨htab, -⟩, c, hc, o, ho, hho⟩ := hb'
  refine ⟨htab, ⟨(c, o), ?_⟩, fun x hx ↦ ?_⟩
  · simp only [hitOccs, Finset.mem_biUnion, Finset.mem_image, Finset.mem_filter]
    exact ⟨c, hc, o, ⟨ho, hho⟩, rfl⟩
  · simp only [hitOccs, Finset.mem_biUnion, Finset.mem_image, Finset.mem_filter] at hx
    obtain ⟨c, hc, o, ⟨ho, hho⟩, rfl⟩ := hx
    exact ⟨hc, ho, hho⟩

theorem hitOccs_eq_of_view {C : Finset K} {s t : State K P D A} (h : view C s = view C t)
    (sup : Bool) : hitOccs C s sup = hitOccs C t sup := by
  funext a
  exact Finset.biUnion_congr rfl fun c hc ↦ by rw [occ_eq_of_view h hc]

/-- **Output consistency** (the read half of noninterference): two planes with the same view
under `C`, and caches complete on `C`, answer every search under `C` identically. -/
theorem search_congr [Fintype K] (dist : A → Δ) {C : Finset K} {s t : State K P D A}
    (hv : view C s = view C t) (hs : Complete C s) (ht : Complete C t) (k : ℕ) (sup : Bool) :
    search dist C s k sup = search dist C t k sup := by
  rw [search_eq, search_eq, prefilter_cleared hs, prefilter_cleared ht,
    table_cleared_eq_of_view hv, hitOccs_eq_of_view hv]

end Search

/-! ### Writing: land, retire, purge and repair -/

namespace Occ

@[simp] theorem flag_path (o : Occ P D A) (b : Bool) : (o.flag b).path = o.path := rfl

@[simp] theorem flag_digest (o : Occ P D A) (b : Bool) : (o.flag b).digest = o.digest := rfl

@[simp] theorem flag_chunk (o : Occ P D A) (b : Bool) : (o.flag b).chunk = o.chunk := rfl

@[simp] theorem flag_atom (o : Occ P D A) (b : Bool) : (o.flag b).atom = o.atom := rfl

@[simp] theorem flag_current (o : Occ P D A) (b : Bool) : (o.flag b).current = b := rfl

@[simp] theorem flag_flag (o : Occ P D A) (b b' : Bool) : (o.flag b).flag b' = o.flag b' := rfl

@[simp] theorem flag_self (o : Occ P D A) : o.flag o.current = o := rfl

end Occ

/-- When no current row of the path holds `o`'s atom, `o` is a row of `R` exactly when it is not
current and a row matching it up to the flag is. -/
theorem mem_iff_of_not_current {R : Finset (Occ P D A)} {o : Occ P D A}
    (h : o.flag true ∉ R) : (o.current = false ∧ ∃ b, o.flag b ∈ R) ↔ o ∈ R := by
  constructor
  · rintro ⟨hc, b, hb⟩
    cases b
    · simpa [← hc] using hb
    · exact absurd hb h
  · intro ho
    cases hc : o.current
    · exact ⟨rfl, false, by simpa [← hc] using ho⟩
    · exact absurd (by simpa [← hc] using ho) h

section Rows

variable [DecidableEq P] [DecidableEq D] [DecidableEq A]

omit [DecidableEq P] [DecidableEq A] in
@[simp] theorem headFlag_none (o : Occ P D A) : headFlag none o = false := by simp [headFlag]

omit [DecidableEq P] [DecidableEq A] in
@[simp] theorem headFlag_some (d : D) (o : Occ P D A) :
    headFlag (some d) o = decide (o.digest = d) := by simp [headFlag]

omit [DecidableEq P] [DecidableEq A] in
@[simp] theorem headFlag_flag (d : Option D) (o : Occ P D A) (b : Bool) :
    headFlag d (o.flag b) = headFlag d o := rfl

theorem mem_reconcile {R : Finset (Occ P D A)} {p : P} {d : Option D} {o : Occ P D A} :
    o ∈ reconcile R p d ↔
      if o.path = p then o.current = headFlag d o ∧ ∃ b, o.flag b ∈ R else o ∈ R := by
  simp only [reconcile, Finset.mem_image]
  constructor
  · rintro ⟨q, hq, rfl⟩
    by_cases hqp : q.path = p
    · simp only [hqp, ↓reduceIte, Occ.flag_path, Occ.flag_current, headFlag_flag, Occ.flag_flag,
        true_and]
      exact ⟨q.current, by simpa using hq⟩
    · simpa [hqp] using hq
  · intro h
    by_cases hp : o.path = p
    · simp only [hp, ↓reduceIte] at h
      obtain ⟨hc, b, hb⟩ := h
      refine ⟨o.flag b, hb, ?_⟩
      simp only [Occ.flag_path, hp, ↓reduceIte, Occ.flag_flag, headFlag_flag, ← hc, Occ.flag_self]
    · simp only [hp, ↓reduceIte] at h
      exact ⟨o, h, by simp [hp]⟩

/-- Reconciling keeps every row's atom, path, digest and chunk; only `current` moves. -/
theorem exists_of_mem_reconcile {R : Finset (Occ P D A)} {p : P} {d : Option D} {o : Occ P D A}
    (h : o ∈ reconcile R p d) : ∃ b, o.flag b ∈ R := by
  rw [mem_reconcile] at h
  split_ifs at h
  · exact h.2
  · exact ⟨o.current, by simpa using h⟩

/-- Reconciling to no head (`retire`) leaves alone every row whose atom no current row of the path
holds. -/
theorem mem_reconcile_none_iff {R : Finset (Occ P D A)} {p : P} {o : Occ P D A}
    (ho : o.atom ∉ (R.filter fun o ↦ o.path = p ∧ o.current = true).image (·.atom)) :
    o ∈ reconcile R p none ↔ o ∈ R := by
  rw [mem_reconcile]
  split_ifs with hp
  · rw [headFlag_none]
    refine mem_iff_of_not_current fun h ↦ ho (Finset.mem_image.2 ⟨o.flag true, ?_, rfl⟩)
    exact Finset.mem_filter.2 ⟨h, by simpa using hp, rfl⟩
  · rfl

namespace Fiber

omit [DecidableEq P] [DecidableEq D] in
theorem mem_atoms {f : Fiber K P D A} {a : A} : a ∈ f.atoms ↔ ∃ i, (i, a) ∈ f.chunks := by
  simp [atoms]

theorem mem_rows {f : Fiber K P D A} {o : Occ P D A} (h : o ∈ f.rows) :
    o.path = f.path ∧ o.digest = f.digest ∧ o.atom ∈ f.atoms := by
  simp only [rows, List.mem_toFinset, List.mem_map] at h
  obtain ⟨⟨i, a⟩, hx, rfl⟩ := h
  exact ⟨rfl, rfl, mem_atoms.2 ⟨i, hx⟩⟩

end Fiber

theorem mem_replaced_of_ne {R : Finset (Occ P D A)} {f : Fiber K P D A} {o : Occ P D A}
    (h : ¬(o.path = f.path ∧ o.digest = f.digest)) : o ∈ replaced R f ↔ o ∈ R := by
  unfold replaced
  split_ifs
  · simp only [Finset.mem_union, Finset.mem_sdiff, existing, Finset.mem_filter]
    constructor
    · rintro (⟨ho, -⟩ | ho)
      · exact ho
      · exact absurd ⟨(Fiber.mem_rows ho).1, (Fiber.mem_rows ho).2.1⟩ h
    · exact fun ho ↦ Or.inl ⟨ho, fun hh ↦ h hh.2⟩
  · rfl

/-- `wanted ∪ freed` covers every row `_write_fiber` touches: a row whose atom it misses is in the
relation after the write exactly when it was before. So refreshing those atoms keeps the cache
coherent. -/
theorem mem_writeRel_iff {R : Finset (Occ P D A)} {f : Fiber K P D A} {o : Occ P D A}
    (ho : o.atom ∉ landAffected R f) : o ∈ writeRel R f ↔ o ∈ R := by
  have hw : o.atom ∉ f.atoms := fun h ↦ ho (Finset.mem_union_left _ h)
  have hf : o.atom ∉ freed R f := fun h ↦ ho (Finset.mem_union_right _ h)
  -- no row of `f`'s version holds the atom, before the write or after it
  have hold : ∀ q ∈ R, q.atom = o.atom → q.path = f.path → q.digest = f.digest → False := by
    intro q hq ha hp hd
    by_cases hc : Changed R f
    · refine hf (Finset.mem_union_right _ ?_)
      simp only [hc, ↓reduceIte]
      exact Finset.mem_image.2 ⟨q, Finset.mem_filter.2 ⟨hq, hp, hd⟩, ha⟩
    · have : (q.chunk, q.atom) ∈ f.chunks.toFinset := by
        rw [← not_not.1 hc]
        exact Finset.mem_image.2 ⟨q, Finset.mem_filter.2 ⟨hq, hp, hd⟩, rfl⟩
      exact hw (Fiber.mem_atoms.2 ⟨q.chunk, ha ▸ List.mem_toFinset.1 this⟩)
  have hnew : ∀ q ∈ replaced R f, q.atom = o.atom → q.path = f.path → q.digest = f.digest →
      False := by
    intro q hq ha hp hd
    unfold replaced at hq
    split_ifs at hq
    · rcases Finset.mem_union.1 hq with hq | hq
      · exact (Finset.mem_sdiff.1 hq).2 (Finset.mem_filter.2 ⟨(Finset.mem_sdiff.1 hq).1, hp, hd⟩)
      · exact hw (ha ▸ (Fiber.mem_rows hq).2.2)
    · exact hold q hq ha hp hd
  rw [writeRel, mem_reconcile]
  split_ifs with hp
  · by_cases hd : o.digest = f.digest
    · refine iff_of_false ?_ fun hR ↦ hold o hR rfl hp hd
      rintro ⟨-, b, hb⟩
      exact hnew _ hb rfl hp hd
    · -- another version of the path: no current row of it holds the atom
      have hcur : o.flag true ∉ R := fun hR ↦ hf (Finset.mem_union_left _
        (Finset.mem_image.2 ⟨o.flag true, Finset.mem_filter.2 ⟨hR, hp, rfl, hd⟩, rfl⟩))
      have hrep : ∀ b, o.flag b ∈ replaced R f ↔ o.flag b ∈ R := fun b ↦
        mem_replaced_of_ne fun h ↦ hd h.2
      simp only [headFlag_some, hd, decide_false, hrep]
      exact mem_iff_of_not_current hcur
  · exact mem_replaced_of_ne fun h ↦ hp h.1

/-- Every row after the write is one of `f`'s, or has the atom and path of a row before it. -/
theorem exists_of_mem_writeRel {R : Finset (Occ P D A)} {f : Fiber K P D A} {o : Occ P D A}
    (h : o ∈ writeRel R f) :
    (o.path = f.path ∧ o.atom ∈ f.atoms) ∨ ∃ q ∈ R, q.atom = o.atom ∧ q.path = o.path := by
  obtain ⟨b, hb⟩ := exists_of_mem_reconcile h
  unfold replaced at hb
  split_ifs at hb
  · rcases Finset.mem_union.1 hb with hb | hb
    · exact Or.inr ⟨o.flag b, (Finset.mem_sdiff.1 hb).1, rfl, rfl⟩
    · have := Fiber.mem_rows hb
      exact Or.inl ⟨by simpa using this.1, by simpa using this.2.2⟩
  · exact Or.inr ⟨o.flag b, hb, rfl, rfl⟩

end Rows

section Write

variable [DecidableEq P] [LinearOrder D] [DecidableEq A] [Fintype K] [DecidableEq K]

/-! #### The cache stays coherent -/

omit [DecidableEq P] [LinearOrder D] [DecidableEq K] in
@[simp] theorem refresh_occ (S : Finset A) (s : State K P D A) : (refresh S s).occ = s.occ := rfl

omit [DecidableEq P] [LinearOrder D] [DecidableEq K] in
@[simp] theorem refresh_sup (S : Finset A) (s : State K P D A) : (refresh S s).sup = s.sup := rfl

omit [DecidableEq P] [LinearOrder D] [DecidableEq K] in
@[simp] theorem refresh_table (S : Finset A) (s : State K P D A) :
    (refresh S s).table = s.table := rfl

omit [DecidableEq P] [LinearOrder D] [DecidableEq K] in
theorem truth_refresh (S : Finset A) (s : State K P D A) : truth (refresh S s) = truth s := rfl

omit [DecidableEq P] [LinearOrder D] [DecidableEq K] in
theorem cache_refresh (S : Finset A) (s : State K P D A) (sup : Bool) (a : A) :
    cache (refresh S s) sup a =
      if a ∈ S ∧ a ∈ s.table then truth s sup a else cache s sup a := by
  cases sup <;> simp only [cache, refresh, Bool.false_eq_true, ↓reduceIte]

omit [DecidableEq P] [LinearOrder D] [DecidableEq K] in
theorem truth_congr {s t : State K P D A} {a : A}
    (h : ∀ c, ∀ o : Occ P D A, o.atom = a → (o ∈ s.occ c ↔ o ∈ t.occ c)) (sup : Bool) :
    truth s sup a = truth t sup a := by
  ext c
  simp only [truth, Finset.mem_filter, Finset.mem_univ, true_and]
  exact exists_congr fun o ↦ and_congr_left fun hh ↦ h c o hh.1

omit [DecidableEq P] [LinearOrder D] [DecidableEq K] in
instance (s : State K P D A) : Decidable (WF s) :=
  inferInstanceAs (Decidable (∀ c, ∀ o ∈ s.occ c, o.atom ∈ s.table))

omit [DecidableEq P] [LinearOrder D] [DecidableEq K] in
theorem truth_eq_empty {s : State K P D A} (hw : WF s) {a : A} (ha : a ∉ s.table) (sup : Bool) :
    truth s sup a = ∅ := by
  ext c
  simp only [truth, Finset.mem_filter, Finset.mem_univ, true_and, Finset.notMem_empty,
    iff_false, not_exists, not_and]
  intro o ho hh
  exact ha (hh.1 ▸ hw c o ho)

omit [DecidableEq P] [LinearOrder D] [DecidableEq K] in
theorem coherent_refresh {S : Finset A} {s : State K P D A}
    (h : ∀ a ∈ s.table, a ∉ S → ∀ sup, cache s sup a = truth s sup a) :
    Coherent (refresh S s) := by
  intro a ha sup
  rw [refresh_table] at ha
  rw [cache_refresh, truth_refresh]
  split_ifs with hS
  · rfl
  · exact h a ha (fun h ↦ hS ⟨h, ha⟩) sup

omit [DecidableEq P] [LinearOrder D] [DecidableEq K] in
theorem coherent_insertAtoms {S : Finset A} {s : State K P D A} (hc : Coherent s) (hw : WF s) :
    Coherent (insertAtoms S s) := by
  intro a _ sup
  have ht : truth (insertAtoms S s) sup a = truth s sup a := rfl
  rw [ht]
  by_cases has : a ∈ s.table
  · have := hc a has sup
    cases sup <;> simpa [cache, insertAtoms, has] using this
  · rw [truth_eq_empty hw has]
    cases sup <;> simp [cache, insertAtoms, has]

theorem truth_commit {f : Fiber K P D A} {s : State K P D A} {a : A}
    (ha : a ∉ landAffected (s.occ f.cls) f) (sup : Bool) :
    truth (commit f s) sup a = truth s sup a := by
  refine truth_congr (fun c o hoa ↦ ?_) sup
  by_cases hc : c = f.cls
  · subst hc
    simp only [commit, Function.update_self]
    exact mem_writeRel_iff (hoa ▸ ha)
  · simp only [commit, Function.update_of_ne hc]

/-- **PLN-4** A land keeps the `held` cache coherent. -/
theorem coherent_land {f : Fiber K P D A} {s : State K P D A} (hc : Coherent s) (hw : WF s) :
    Coherent (land f s) := by
  unfold land
  split_ifs
  · exact coherent_insertAtoms hc hw
  · refine coherent_refresh fun a ha haff sup ↦ ?_
    have has : a ∈ s.table := by
      have : a ∈ s.table ∪ f.atoms := ha
      rcases Finset.mem_union.1 this with h | h
      · exact h
      · exact absurd (Finset.mem_union_left _ h) haff
    have hcache : cache (commit f (insertAtoms f.atoms s)) sup a = cache s sup a := by
      cases sup <;> simp [cache, commit, insertAtoms, has]
    rw [hcache, truth_commit (s := insertAtoms f.atoms s) haff]
    exact hc a has sup

theorem wf_land {f : Fiber K P D A} {s : State K P D A} (hw : WF s) : WF (land f s) := by
  unfold land
  split_ifs
  · exact fun c o ho ↦ Finset.mem_union_left _ (hw c o ho)
  · intro c o ho
    simp only [refresh_occ, refresh_table, commit, insertAtoms] at ho ⊢
    by_cases hc : c = f.cls
    · subst hc
      rw [Function.update_self] at ho
      rcases exists_of_mem_writeRel ho with ⟨-, h⟩ | ⟨q, hq, hqa, -⟩
      · exact Finset.mem_union_right _ h
      · exact Finset.mem_union_left _ (hqa ▸ hw _ q hq)
    · rw [Function.update_of_ne hc] at ho
      exact Finset.mem_union_left _ (hw c o ho)

theorem partitioned_land {κ : P → K} {f : Fiber K P D A} {s : State K P D A}
    (hp : Partitioned κ s) (hf : κ f.path = f.cls) : Partitioned κ (land f s) := by
  unfold land
  split_ifs
  · exact hp
  · intro c o ho
    simp only [refresh_occ, commit, insertAtoms] at ho
    by_cases hc : c = f.cls
    · subst hc
      rw [Function.update_self] at ho
      rcases exists_of_mem_writeRel ho with ⟨h, -⟩ | ⟨q, hq, -, hqp⟩
      · rw [h, hf]
      · rw [← hqp]
        exact hp _ q hq
    · rw [Function.update_of_ne hc] at ho
      exact hp c o ho

/-- **PLN-4** So does a retire. -/
theorem coherent_retire {c : K} {p : P} {s : State K P D A} (hc : Coherent s) :
    Coherent (retire c p s) := by
  unfold retire
  split_ifs
  · exact hc
  · refine coherent_refresh fun a ha haff sup ↦ ?_
    have ht : truth (retireCommit c p s) sup a = truth s sup a := by
      refine truth_congr (fun c' o hoa ↦ ?_) sup
      by_cases hc' : c' = c
      · subst hc'
        simp only [retireCommit, Function.update_self]
        exact mem_reconcile_none_iff (hoa ▸ haff)
      · simp only [retireCommit, Function.update_of_ne hc']
    rw [ht]
    exact hc a ha sup

theorem wf_retire {c : K} {p : P} {s : State K P D A} (hw : WF s) : WF (retire c p s) := by
  unfold retire
  split_ifs
  · exact hw
  · intro c' o ho
    simp only [refresh_occ, refresh_table, retireCommit] at ho ⊢
    by_cases hc' : c' = c
    · subst hc'
      rw [Function.update_self] at ho
      obtain ⟨b, hb⟩ := exists_of_mem_reconcile ho
      simpa using hw _ _ hb
    · rw [Function.update_of_ne hc'] at ho
      exact hw c' o ho

theorem partitioned_retire {κ : P → K} {c : K} {p : P} {s : State K P D A}
    (hp : Partitioned κ s) : Partitioned κ (retire c p s) := by
  unfold retire
  split_ifs
  · exact hp
  · intro c' o ho
    simp only [refresh_occ, retireCommit] at ho
    by_cases hc' : c' = c
    · subst hc'
      rw [Function.update_self] at ho
      obtain ⟨b, hb⟩ := exists_of_mem_reconcile ho
      simpa using hp _ _ hb
    · rw [Function.update_of_ne hc'] at ho
      exact hp c' o ho

omit [DecidableEq P] [DecidableEq K] in
theorem mem_byDigest {d : D} {s : State K P D A} {a : A} :
    a ∈ byDigest d s ↔ ∃ c, ∃ o ∈ s.occ c, o.digest = d ∧ o.atom = a := by
  simp [byDigest, and_assoc]

omit [DecidableEq P] [DecidableEq K] in
/-- An atom a row of another digest holds is not purged. -/
theorem not_mem_purged {d : D} {s : State K P D A} {c : K} {o : Occ P D A} (ho : o ∈ s.occ c)
    (hd : o.digest ≠ d) : o.atom ∉ purged d s := by
  intro h
  obtain ⟨hb, hs⟩ := Finset.mem_sdiff.1 h
  exact hs (Finset.mem_filter.2 ⟨hb, c, o, ho, rfl, hd⟩)

omit [DecidableEq P] [DecidableEq K] in
/-- **PLN-4** So does a purge. -/
theorem coherent_purge {d : D} {s : State K P D A} (hc : Coherent s) : Coherent (purge d s) := by
  refine coherent_refresh fun a ha haff sup ↦ ?_
  have ha' : a ∈ s.table ∧ a ∉ purged d s := Finset.mem_sdiff.1 ha
  have hnot : a ∉ byDigest d s := fun h ↦ ha'.2 (Finset.mem_sdiff.2 ⟨h, haff⟩)
  have ht : truth (purgeCommit d s) sup a = truth s sup a := by
    refine truth_congr (fun c o hoa ↦ ?_) sup
    simp only [purgeCommit, Finset.mem_filter, and_iff_left_iff_imp]
    intro ho hd
    exact hnot (mem_byDigest.2 ⟨c, o, ho, hd, hoa⟩)
  rw [ht]
  exact hc a ha'.1 sup

omit [DecidableEq P] [DecidableEq K] in
theorem wf_purge {d : D} {s : State K P D A} (hw : WF s) : WF (purge d s) := by
  intro c o ho
  simp only [purge, refresh_occ, refresh_table, purgeCommit, Finset.mem_filter] at ho ⊢
  exact Finset.mem_sdiff.2 ⟨hw c o ho.1, not_mem_purged ho.1 ho.2⟩

omit [DecidableEq P] [DecidableEq K] in
theorem partitioned_purge {κ : P → K} {d : D} {s : State K P D A} (hp : Partitioned κ s) :
    Partitioned κ (purge d s) := by
  intro c o ho
  simp only [purge, refresh_occ, purgeCommit, Finset.mem_filter] at ho
  exact hp c o ho.1

omit [DecidableEq P] [LinearOrder D] [DecidableEq K] in
/-- **PLN-4** And `repair` makes any cache coherent. -/
theorem coherent_repair (s : State K P D A) : Coherent (repair s) :=
  coherent_refresh fun _ ha haff ↦ absurd ha haff

/-! #### Purge (A3.7) -/

omit [DecidableEq P] [DecidableEq K] in
/-- **PLN-5** After a purge no row and no edge names the digest. -/
theorem purge_clears (d : D) (s : State K P D A) (c : K) :
    (∀ o ∈ (purge d s).occ c, o.digest ≠ d) ∧
      ∀ e ∈ (purge d s).sup c, e.old ≠ some d ∧ e.new ≠ some d := by
  constructor
  · intro o ho
    simp only [purge, refresh_occ, purgeCommit, Finset.mem_filter] at ho
    exact ho.2
  · intro e he
    simp only [purge, refresh_sup, purgeCommit, List.mem_filter, decide_eq_true_eq] at he
    exact he.2

omit [DecidableEq P] [DecidableEq K] in
/-- **PLN-5** Nothing private lingers: every atom the digest's rows held is deleted, or a remaining
row still holds it. -/
theorem purge_no_orphan {d : D} {s : State K P D A} {a : A} (ha : a ∈ byDigest d s)
    (ht : a ∈ (purge d s).table) : ∃ c, ∃ o ∈ (purge d s).occ c, o.atom = a := by
  simp only [purge, refresh_table, refresh_occ, purgeCommit] at ht ⊢
  have hs : a ∈ stillHeld d s := by
    by_contra h
    exact (Finset.mem_sdiff.1 ht).2 (Finset.mem_sdiff.2 ⟨ha, h⟩)
  obtain ⟨c, o, ho, hoa, hd⟩ := (Finset.mem_filter.1 hs).2
  exact ⟨c, o, Finset.mem_filter.2 ⟨ho, hd⟩, hoa⟩

omit [DecidableEq P] [DecidableEq K] in
/-- **PLN-5** Re-running the purge finishes one a crash interrupted after its atom delete. -/
theorem purge_purgeAtoms (d : D) (s : State K P D A) : purge d (purgeAtoms d s) = purge d s := by
  have hc : purgeCommit d (purgeAtoms d s) = purgeCommit d s := by
    ext1
    · rfl
    · rfl
    · exact sdiff_idem
    · rfl
    · rfl
  simp only [purge, hc]
  rfl

end Write

/-! ### Noninterference over traces (A3.5) -/

section Trace

variable [DecidableEq P] [LinearOrder D] [DecidableEq A] [Fintype K] [DecidableEq K]

@[simp] theorem run_nil (s : State K P D A) : run [] s = s := rfl

@[simp] theorem run_cons (op : Op K P D A) (ops : List (Op K P D A)) (s : State K P D A) :
    run (op :: ops) s = run ops (step op s) := rfl

omit [DecidableEq P] [LinearOrder D] [DecidableEq K] in
theorem good_empty (κ : P → K) : Good κ (empty : State K P D A) where
  coherent _ h := absurd h (Finset.notMem_empty _)
  wf _ _ h := absurd h (Finset.notMem_empty _)
  part _ _ h := absurd h (Finset.notMem_empty _)

theorem wf_step {op : Op K P D A} {s : State K P D A} (hw : WF s) : WF (step op s) := by
  cases op with
  | land f => exact wf_land hw
  | retire c p => exact wf_retire hw
  | purge d => exact wf_purge hw
  | repair => exact hw

theorem good_step {κ : P → K} {op : Op K P D A} {s : State K P D A} (hs : Good κ s)
    (hop : op.Respects κ) : Good κ (step op s) := by
  cases op with
  | land f => exact ⟨coherent_land hs.coherent hs.wf, wf_land hs.wf, partitioned_land hs.part hop⟩
  | retire c p => exact ⟨coherent_retire hs.coherent, wf_retire hs.wf, partitioned_retire hs.part⟩
  | purge d => exact ⟨coherent_purge hs.coherent, wf_purge hs.wf, partitioned_purge hs.part⟩
  | repair => exact ⟨coherent_repair s, hs.wf, hs.part⟩

theorem good_run {κ : P → K} {ops : List (Op K P D A)} {s : State K P D A} (hs : Good κ s)
    (hops : ∀ op ∈ ops, op.Respects κ) : Good κ (run ops s) := by
  induction ops generalizing s with
  | nil => exact hs
  | cons op ops ih =>
    exact ih (good_step hs (hops op (by simp))) fun o ho ↦ hops o (by simp [ho])

theorem land_occ (f : Fiber K P D A) (s : State K P D A) (c : K) :
    (land f s).occ c =
      if c = f.cls ∧ ¬Refused f s then writeRel (s.occ f.cls) f else s.occ c := by
  by_cases hr : Refused f s
  · simp [land, hr, insertAtoms]
  · by_cases hc : c = f.cls
    · subst hc
      simp [land, hr, commit, insertAtoms]
    · simp [land, hr, hc, commit, insertAtoms]

theorem land_sup (f : Fiber K P D A) (s : State K P D A) (c : K) :
    (land f s).sup c =
      if c = f.cls ∧ ¬Refused f s then s.sup f.cls ++ landEdges (s.occ f.cls) f else s.sup c := by
  by_cases hr : Refused f s
  · simp [land, hr, insertAtoms]
  · by_cases hc : c = f.cls
    · subst hc
      simp [land, hr, commit, insertAtoms]
    · simp [land, hr, hc, commit, insertAtoms]

theorem retire_occ (c' : K) (p : P) (s : State K P D A) (c : K) :
    (retire c' p s).occ c =
      if c = c' ∧ heads (s.occ c') p ≠ ∅ then reconcile (s.occ c') p none else s.occ c := by
  by_cases h : heads (s.occ c') p = ∅
  · simp [retire, h]
  · by_cases hc : c = c'
    · subst hc
      simp [retire, h, retireCommit]
    · simp [retire, h, hc, retireCommit]

theorem retire_sup (c' : K) (p : P) (s : State K P D A) (c : K) :
    (retire c' p s).sup c =
      if c = c' ∧ heads (s.occ c') p ≠ ∅ then
        s.sup c' ++ (heads (s.occ c') p).sort.map fun h ↦ ⟨p, some h, none⟩
      else s.sup c := by
  by_cases h : heads (s.occ c') p = ∅
  · simp [retire, h]
  · by_cases hc : c = c'
    · subst hc
      simp [retire, h, retireCommit]
    · simp [retire, h, hc, retireCommit]

omit [DecidableEq P] [LinearOrder D] [Fintype K] [DecidableEq K] in
theorem refs_subset {C : Finset K} {s : State K P D A} (hw : WF s) : refs C s ⊆ s.table := by
  intro a ha
  obtain ⟨c, -, ha⟩ := Finset.mem_biUnion.1 ha
  obtain ⟨o, ho, rfl⟩ := Finset.mem_image.1 ha
  exact hw c o ho

omit [DecidableEq P] [LinearOrder D] [Fintype K] in
/-- Without dangling rows, the view is the cleared relations and logs. -/
theorem view_eq_of {C : Finset K} {s t : State K P D A} (hs : WF s) (ht : WF t)
    (hocc : ∀ c ∈ C, s.occ c = t.occ c) (hsup : ∀ c ∈ C, s.sup c = t.sup c) :
    view C s = view C t := by
  have hrefs : refs C s = refs C t := Finset.biUnion_congr rfl fun c hc ↦ by rw [hocc c hc]
  simp only [view, Prod.mk.injEq]
  refine ⟨funext fun c ↦ ?_, ?_⟩
  · split_ifs with hc
    · rw [hocc c hc, hsup c hc]
    · rfl
  · rw [Finset.inter_eq_right.2 (refs_subset hs), Finset.inter_eq_right.2 (refs_subset ht), hrefs]

/-- **Local respect**: a write to an uncleared class leaves the view alone. -/
theorem view_step_invisible {C : Finset K} {op : Op K P D A} {s : State K P D A} (hw : WF s)
    (hv : op.visible C = false) : view C (step op s) = view C s := by
  cases op with
  | land f =>
    have hne : ∀ c ∈ C, c ≠ f.cls := fun c hc h ↦ by simp [Op.visible, ← h, hc] at hv
    exact view_eq_of (wf_step hw) hw (fun c hc ↦ by simp [step, land_occ, hne c hc])
      (fun c hc ↦ by simp [step, land_sup, hne c hc])
  | retire c' p =>
    have hne : ∀ c ∈ C, c ≠ c' := fun c hc h ↦ by simp [Op.visible, ← h, hc] at hv
    exact view_eq_of (wf_step hw) hw (fun c hc ↦ by simp [step, retire_occ, hne c hc])
      (fun c hc ↦ by simp [step, retire_sup, hne c hc])
  | purge d => simp [Op.visible] at hv
  | repair => simp [Op.visible] at hv

omit [DecidableEq P] [LinearOrder D] [DecidableEq A] [Fintype K] [DecidableEq K] in
/-- A stratum-respecting fiber never meets a stratum conflict. -/
theorem not_elsewhere {κ : P → K} {f : Fiber K P D A} {s : State K P D A} (hp : Partitioned κ s)
    (hf : κ f.path = f.cls) : ¬Elsewhere f s := by
  rintro ⟨c, hc, o, ho, hop⟩
  exact hc (by rw [← hp c o ho, hop, hf])

/-- **Step consistency**: a visible write takes planes with one view to planes with one view. -/
theorem view_step_congr {κ : P → K} {C : Finset K} {op : Op K P D A} {s t : State K P D A}
    (hs : Good κ s) (ht : Good κ t) (hop : op.Respects κ) (hv : view C s = view C t)
    (hvis : op.visible C = true) : view C (step op s) = view C (step op t) := by
  have hocc : ∀ c ∈ C, s.occ c = t.occ c := fun c hc ↦ occ_eq_of_view hv hc
  have hsup : ∀ c ∈ C, s.sup c = t.sup c := fun c hc ↦ sup_eq_of_view hv hc
  refine view_eq_of (wf_step hs.wf) (wf_step ht.wf) (fun c hc ↦ ?_) (fun c hc ↦ ?_)
  · cases op with
    | land f =>
      have hf : f.cls ∈ C := by simpa [Op.visible] using hvis
      have hR : Refused f s ↔ Refused f t := by
        simp only [Refused, not_elsewhere hs.part hop, not_elsewhere ht.part hop, false_or,
          hocc _ hf]
      simp only [step, land_occ, hR, hocc _ hf, hocc c hc]
    | retire c' p =>
      have hc' : c' ∈ C := by simpa [Op.visible] using hvis
      simp only [step, retire_occ, hocc _ hc', hocc c hc]
    | purge d => simp only [step, purge, refresh_occ, purgeCommit, hocc c hc]
    | repair => simp only [step, repair, refresh_occ, hocc c hc]
  · cases op with
    | land f =>
      have hf : f.cls ∈ C := by simpa [Op.visible] using hvis
      have hR : Refused f s ↔ Refused f t := by
        simp only [Refused, not_elsewhere hs.part hop, not_elsewhere ht.part hop, false_or,
          hocc _ hf]
      simp only [step, land_sup, hR, hocc _ hf, hsup _ hf, hsup c hc]
    | retire c' p =>
      have hc' : c' ∈ C := by simpa [Op.visible] using hvis
      simp only [step, retire_sup, hocc _ hc', hsup _ hc', hsup c hc]
    | purge d => simp only [step, purge, refresh_sup, purgeCommit, hsup c hc]
    | repair => simp only [step, repair, refresh_sup, hsup c hc]

/-- **PLN-2, noninterference** (A3.5), in Goguen and Meseguer's form, by Rushby's unwinding: after
any trace of writes that keep each path at its stratum, a reader under `C` sees what it would have
seen had only the cleared writes, the purges and the repairs happened. -/
theorem noninterference {κ : P → K} {C : Finset K} :
    ∀ (ops : List (Op K P D A)) {s t : State K P D A}, Good κ s → Good κ t →
      view C s = view C t → (∀ op ∈ ops, op.Respects κ) →
      view C (run ops s) = view C (run (ops.filter (·.visible C)) t)
  | [], _, _, _, _, hv, _ => hv
  | op :: ops, s, t, hs, ht, hv, hops => by
    have hop := hops op (by simp)
    have hrest : ∀ o ∈ ops, o.Respects κ := fun o ho ↦ hops o (by simp [ho])
    cases hvis : op.visible C
    · simp only [run_cons, List.filter_cons, hvis, Bool.false_eq_true, ↓reduceIte]
      exact noninterference ops (good_step hs hop) ht
        ((view_step_invisible hs.wf hvis).trans hv) hrest
    · simp only [run_cons, List.filter_cons, hvis, ↓reduceIte]
      exact noninterference ops (good_step hs hop) (good_step ht hop)
        (view_step_congr hs ht hop hv hvis) hrest

end Trace

section Search

variable {Δ : Type*} [LinearOrder Δ] [DecidableEq P] [LinearOrder D] [LinearOrder A] [Fintype K]
  [DecidableEq K]

/-- **PLN-2, noninterference for search**: the same, for every search under `C`. -/
theorem noninterference_search (dist : A → Δ) {κ : P → K} {C : Finset K}
    (ops : List (Op K P D A)) {s : State K P D A} (hs : Good κ s)
    (hops : ∀ op ∈ ops, op.Respects κ) (k : ℕ) (sup : Bool) :
    search dist C (run ops s) k sup = search dist C (run (ops.filter (·.visible C)) s) k sup :=
  search_congr dist (noninterference ops hs hs rfl hops) ((good_run hs hops).coherent.complete C)
    ((good_run hs fun op ho ↦ hops op (List.mem_of_mem_filter ho)).coherent.complete C) k sup

end Search

/-! ### Crash points of a land (PLN-4, dn-ingest-door §9 item 7)

The code now writes a land's cache additions before its transaction and its removals after it, so
a crash at any point leaves the cache stale only by excess. Excess is invisible to every reader:
two planes whose caches are complete and which differ only in them answer every search alike, now
and after any trace of writes. -/

section Crash

variable [DecidableEq P] [LinearOrder D] [DecidableEq A] [Fintype K] [DecidableEq K]

omit [DecidableEq P] [LinearOrder D] [Fintype K] in
@[simp] theorem addCache_occ (f : Fiber K P D A) (s : State K P D A) :
    (addCache f s).occ = s.occ := rfl

omit [DecidableEq P] [LinearOrder D] [Fintype K] in
@[simp] theorem addCache_sup (f : Fiber K P D A) (s : State K P D A) :
    (addCache f s).sup = s.sup := rfl

omit [DecidableEq P] [LinearOrder D] [Fintype K] in
@[simp] theorem addCache_table (f : Fiber K P D A) (s : State K P D A) :
    (addCache f s).table = s.table := rfl

omit [DecidableEq P] [LinearOrder D] [Fintype K] in
theorem cache_addCache (f : Fiber K P D A) (s : State K P D A) (sup : Bool) (a : A) :
    cache (addCache f s) sup a =
      if a ∈ f.atoms ∧ a ∈ s.table then insert f.cls (cache s sup a) else cache s sup a := by
  cases sup <;> simp only [cache, addCache, Bool.false_eq_true, ↓reduceIte]

omit [DecidableEq P] [LinearOrder D] [DecidableEq K] in
theorem complete_refresh {C : Finset K} {S : Finset A} {s : State K P D A} (h : Complete C s) :
    Complete C (refresh S s) := by
  intro a ha sup c hc hct
  rw [refresh_table] at ha
  rw [truth_refresh] at hct
  rw [cache_refresh]
  split_ifs with hS
  · exact hct
  · exact h a ha sup c hc hct

omit [Fintype K] [DecidableEq K] in
/-- A row a fiber's write leaves whose atom is none of the fiber's was in the relation before, up to
its flag, and was there, flag and all, if it is current. -/
theorem mem_of_mem_writeRel {R : Finset (Occ P D A)} {f : Fiber K P D A} {o : Occ P D A}
    (h : o ∈ writeRel R f) (ha : o.atom ∉ f.atoms) :
    (∃ b, o.flag b ∈ R) ∧ (o.current = true → o ∈ R) := by
  have hrep : ∀ b, o.flag b ∈ replaced R f → o.flag b ∈ R := by
    intro b hb
    unfold replaced at hb
    split_ifs at hb
    · rcases Finset.mem_union.1 hb with hb | hb
      · exact (Finset.mem_sdiff.1 hb).1
      · exact absurd (by simpa using (Fiber.mem_rows hb).2.2) ha
    · exact hb
  rw [writeRel, mem_reconcile] at h
  split_ifs at h with hp
  · obtain ⟨hc, b, hb⟩ := h
    refine ⟨⟨b, hrep b hb⟩, fun hcur ↦ ?_⟩
    have hd : o.digest = f.digest := by simpa [headFlag, hcur] using hc.symm
    have hR := hrep b hb
    by_cases hch : Changed R f
    · unfold replaced at hb
      simp only [hch, ↓reduceIte, Finset.mem_union, Finset.mem_sdiff, existing,
        Finset.mem_filter, Occ.flag_path, Occ.flag_digest] at hb
      rcases hb with ⟨-, hne⟩ | hb
      · exact absurd ⟨hR, hp, hd⟩ hne
      · exact absurd (by simpa using (Fiber.mem_rows hb).2.2) ha
    · have : ((o.flag b).chunk, (o.flag b).atom) ∈ f.chunks.toFinset := by
        rw [← not_not.1 hch]
        exact Finset.mem_image.2 ⟨o.flag b, Finset.mem_filter.2 ⟨hR, hp, hd⟩, rfl⟩
      exact absurd (Fiber.mem_atoms.2 ⟨o.chunk, by simpa using List.mem_toFinset.1 this⟩) ha
  · have ho := (mem_replaced_of_ne (fun hh ↦ hp hh.1)).1 h
    exact ⟨⟨o.current, by simpa using ho⟩, fun _ ↦ ho⟩

theorem truth_commit_sub {f : Fiber K P D A} {s : State K P D A} {sup : Bool} {a : A} {c : K}
    (h : c ∈ truth (commit f s) sup a) : c ∈ truth s sup a ∨ (c = f.cls ∧ a ∈ f.atoms) := by
  simp only [truth, Finset.mem_filter, Finset.mem_univ, true_and] at h ⊢
  obtain ⟨o, ho, hh⟩ := h
  by_cases hc : c = f.cls
  · subst hc
    simp only [commit, Function.update_self] at ho
    by_cases ha : a ∈ f.atoms
    · exact Or.inr ⟨rfl, ha⟩
    · have ha' : o.atom ∉ f.atoms := hh.1 ▸ ha
      obtain ⟨⟨b, hb⟩, hcur⟩ := mem_of_mem_writeRel ho ha'
      left
      rcases hh with ⟨hoa, hs | hcu⟩
      · exact ⟨o.flag b, hb, by simp [Occ.holds, hoa, hs]⟩
      · exact ⟨o, hcur hcu, hoa, Or.inr hcu⟩
  · simp only [commit, Function.update_of_ne hc] at ho
    exact Or.inl ⟨o, ho, hh⟩

omit [DecidableEq P] [LinearOrder D] in
/-- **PLN-4** A crash before a land's transaction, with the atoms and the cache's additions
written, leaves the cache complete on every class, from a complete one with no dangling row. -/
theorem complete_landAdd {f : Fiber K P D A} {s : State K P D A} (hc : Complete univ s)
    (hw : WF s) : Complete univ (landAdd f s) := by
  intro a ha sup c _ hct
  have ht : truth (landAdd f s) sup a = truth s sup a := rfl
  rw [ht] at hct
  have has : a ∈ s.table := by
    by_contra h
    simp [truth_eq_empty hw h] at hct
  have hca : c ∈ cache s sup a := hc a has sup c (Finset.mem_univ _) hct
  rw [landAdd, cache_addCache]
  have hi : cache (insertAtoms f.atoms s) sup a = cache s sup a := by
    cases sup <;> simp [cache, insertAtoms, has]
  split_ifs
  · exact Finset.mem_insert_of_mem (hi ▸ hca)
  · exact hi ▸ hca

/-- **PLN-4** So does a crash after the transaction (or after its rollback, when refused): every
atom the transaction gave a row names the row's class already. -/
theorem complete_landAddCommit {f : Fiber K P D A} {s : State K P D A} (hc : Complete univ s)
    (hw : WF s) : Complete univ (landAddCommit f s) := by
  unfold landAddCommit
  split_ifs
  · exact complete_landAdd hc hw
  · intro a ha sup c _ hct
    have hc' := complete_landAdd (f := f) hc hw
    have hcache : cache (commit f (landAdd f s)) sup a = cache (landAdd f s) sup a := by
      cases sup <;> rfl
    rw [hcache]
    rcases truth_commit_sub hct with h | ⟨rfl, haf⟩
    · exact hc' a ha sup c (Finset.mem_univ _) h
    · have hat : a ∈ (insertAtoms f.atoms s).table := Finset.mem_union_right _ haf
      rw [landAdd, cache_addCache]
      simp [haf, hat]

omit [DecidableEq P] [LinearOrder D] [DecidableEq K] in
theorem refresh_eq_of {S : Finset A} {s t : State K P D A} (ho : s.occ = t.occ)
    (hs : s.sup = t.sup) (htab : s.table = t.table)
    (hh : ∀ a, ¬(a ∈ S ∧ a ∈ s.table) → s.held a = t.held a)
    (he : ∀ a, ¬(a ∈ S ∧ a ∈ s.table) → s.ever a = t.ever a) : refresh S s = refresh S t := by
  have ht : truth s = truth t := by
    funext sup a
    simp only [truth, ho]
  ext1
  · exact ho
  · exact hs
  · exact htab
  · funext a
    simp only [refresh, ht, ← htab]
    split_ifs with h
    · rfl
    · exact hh a h
  · funext a
    simp only [refresh, ht, ← htab]
    split_ifs with h
    · rfl
    · exact he a h

/-- **PLN-4** A land written in the code's order, the cache's additions first and its removals
last, ends where `land` does, so every law about `land` holds of it. -/
theorem land_of_landAdd {f : Fiber K P D A} {s : State K P D A} (hr : ¬Refused f s) :
    refresh (landAffected (s.occ f.cls) f) (commit f (landAdd f s)) = land f s := by
  have hS : ∀ a, ¬(a ∈ landAffected (s.occ f.cls) f ∧ a ∈ (insertAtoms f.atoms s).table) →
      ¬(a ∈ f.atoms ∧ a ∈ (insertAtoms f.atoms s).table) :=
    fun a h h' ↦ h ⟨Finset.mem_union_left _ h'.1, h'.2⟩
  simp only [land, hr, ↓reduceIte]
  refine refresh_eq_of rfl rfl rfl (fun a h ↦ ?_) (fun a h ↦ ?_)
  · change (addCache f (insertAtoms f.atoms s)).held a = (insertAtoms f.atoms s).held a
    simp only [addCache, hS a h, ↓reduceIte]
  · change (addCache f (insertAtoms f.atoms s)).ever a = (insertAtoms f.atoms s).ever a
    simp only [addCache, hS a h, ↓reduceIte]

/-- **PLN-4** A refused land whose additions are taken back after the rollback ends where `land`
does, from a coherent plane with no dangling row. -/
theorem land_of_landAdd_refused {f : Fiber K P D A} {s : State K P D A} (hc : Coherent s)
    (hw : WF s) (hr : Refused f s) : refresh f.atoms (landAdd f s) = land f s := by
  have key : ∀ sup a, truth s sup a = cache (insertAtoms f.atoms s) sup a := by
    intro sup a
    by_cases has : a ∈ s.table
    · rw [← hc a has sup]
      cases sup <;> simp [cache, insertAtoms, has]
    · rw [truth_eq_empty hw has]
      cases sup <;> simp [cache, insertAtoms, has]
  have ht : truth (landAdd f s) = truth s := rfl
  simp only [land, hr, ↓reduceIte]
  ext1
  · rfl
  · rfl
  · rfl
  · funext a
    change (if a ∈ f.atoms ∧ a ∈ (insertAtoms f.atoms s).table then truth (landAdd f s) false a
      else (addCache f (insertAtoms f.atoms s)).held a) = (insertAtoms f.atoms s).held a
    rw [ht]
    by_cases h : a ∈ f.atoms ∧ a ∈ (insertAtoms f.atoms s).table
    · simp only [h, and_self, ↓reduceIte]
      exact key false a
    · simp only [h, ↓reduceIte, addCache]
  · funext a
    change (if a ∈ f.atoms ∧ a ∈ (insertAtoms f.atoms s).table then truth (landAdd f s) true a
      else (addCache f (insertAtoms f.atoms s)).ever a) = (insertAtoms f.atoms s).ever a
    rw [ht]
    by_cases h : a ∈ f.atoms ∧ a ∈ (insertAtoms f.atoms s).table
    · simp only [h, and_self, ↓reduceIte]
      exact key true a
    · simp only [h, ↓reduceIte, addCache]

omit [DecidableEq P] [LinearOrder D] [DecidableEq K] in
theorem Complete.mono {C : Finset K} {s : State K P D A} (h : Complete univ s) : Complete C s :=
  fun a ha sup c _ hc ↦ h a ha sup c (Finset.mem_univ c) hc

omit [DecidableEq P] [LinearOrder D] [DecidableEq K] in
theorem complete_insertAtoms {S : Finset A} {s : State K P D A} (hc : Complete univ s)
    (hw : WF s) : Complete univ (insertAtoms S s) := by
  intro a _ sup c _ hct
  have ht : truth (insertAtoms S s) sup a = truth s sup a := rfl
  rw [ht] at hct
  have has : a ∈ s.table := by
    by_contra h
    simp [truth_eq_empty hw h] at hct
  have hi : cache (insertAtoms S s) sup a = cache s sup a := by
    cases sup <;> simp [cache, insertAtoms, has]
  rw [hi]
  exact hc a has sup c (Finset.mem_univ _) hct

theorem complete_land {f : Fiber K P D A} {s : State K P D A} (hc : Complete univ s) (hw : WF s) :
    Complete univ (land f s) := by
  unfold land
  split_ifs with hr
  · exact complete_insertAtoms hc hw
  · intro a ha sup c _ hct
    rw [refresh_table] at ha
    rw [truth_refresh] at hct
    rw [cache_refresh]
    split_ifs with hS
    · exact hct
    · have haff : a ∉ landAffected (s.occ f.cls) f := fun h ↦ hS ⟨h, ha⟩
      rw [truth_commit (s := insertAtoms f.atoms s) haff] at hct
      have hcache : cache (commit f (insertAtoms f.atoms s)) sup a =
          cache (insertAtoms f.atoms s) sup a := by
        cases sup <;> rfl
      rw [hcache]
      exact complete_insertAtoms hc hw a ha sup c (Finset.mem_univ _) hct

theorem complete_retireCommit {c : K} {p : P} {s : State K P D A} (h : Complete univ s) :
    Complete univ (retireCommit c p s) := by
  intro a ha sup c' _ hct
  have hcs : c' ∈ truth s sup a := by
    simp only [truth, Finset.mem_filter, Finset.mem_univ, true_and] at hct ⊢
    obtain ⟨o, ho, hh⟩ := hct
    by_cases hc : c' = c
    · subst hc
      simp only [retireCommit, Function.update_self] at ho
      rw [mem_reconcile] at ho
      split_ifs at ho with hp
      · obtain ⟨hcur, b, hb⟩ := ho
        refine ⟨o.flag b, hb, hh.1, ?_⟩
        rcases hh with ⟨-, hs | hcu⟩
        · exact Or.inl hs
        · rw [headFlag_none] at hcur
          rw [hcur] at hcu
          exact absurd hcu Bool.false_ne_true
      · exact ⟨o, ho, hh⟩
    · simp only [retireCommit, Function.update_of_ne hc] at ho
      exact ⟨o, ho, hh⟩
  exact h a ha sup c' (Finset.mem_univ _) hcs

omit [DecidableEq P] [DecidableEq K] in
theorem complete_purgeCommit {d : D} {s : State K P D A} (h : Complete univ s) :
    Complete univ (purgeCommit d s) := by
  intro a ha sup c _ hct
  have hocc : ∀ c, (purgeCommit d s).occ c = (s.occ c).filter (·.digest ≠ d) := fun _ ↦ rfl
  have hcs : c ∈ truth s sup a := by
    simp only [truth, Finset.mem_filter, Finset.mem_univ, true_and, hocc] at hct ⊢
    obtain ⟨o, ⟨ho, -⟩, hh⟩ := hct
    exact ⟨o, ho, hh⟩
  have hcache : cache (purgeCommit d s) sup a = cache s sup a := by
    cases sup <;> rfl
  rw [hcache]
  exact h a (Finset.mem_sdiff.1 ha).1 sup c (Finset.mem_univ _) hcs

omit [DecidableEq P] [DecidableEq K] in
theorem complete_purgeAtoms {d : D} {s : State K P D A} (h : Complete univ s) :
    Complete univ (purgeAtoms d s) :=
  fun a ha sup c hc hct ↦ h a (Finset.mem_sdiff.1 ha).1 sup c hc hct

theorem complete_step {op : Op K P D A} {s : State K P D A} (hc : Complete univ s) (hw : WF s) :
    Complete univ (step op s) := by
  cases op with
  | land f => exact complete_land hc hw
  | retire c p =>
    simp only [step, retire]
    split_ifs
    · exact hc
    · exact complete_refresh (complete_retireCommit hc)
  | purge d => exact complete_refresh (complete_purgeCommit hc)
  | repair => exact complete_refresh hc

theorem complete_run {ops : List (Op K P D A)} {s : State K P D A} (hc : Complete univ s)
    (hw : WF s) : Complete univ (run ops s) ∧ WF (run ops s) := by
  induction ops generalizing s with
  | nil => exact ⟨hc, hw⟩
  | cons op ops ih => exact ih (complete_step hc hw) (wf_step hw)

omit [DecidableEq P] [LinearOrder D] [Fintype K] in
theorem view_eq_of_sameRel {C : Finset K} {s t : State K P D A} (h : SameRel s t) :
    view C s = view C t := by
  obtain ⟨ho, hs, ht⟩ := h
  simp only [view, refs, ho, hs, ht]

theorem sameRel_step {op : Op K P D A} {s t : State K P D A} (h : SameRel s t) :
    SameRel (step op s) (step op t) := by
  obtain ⟨ho, hs, ht⟩ := h
  have hR : ∀ f : Fiber K P D A, Refused f s ↔ Refused f t := fun f ↦ by
    simp only [Refused, Elsewhere, heads, ho]
  cases op with
  | land f =>
    refine ⟨funext fun c ↦ ?_, funext fun c ↦ ?_, ?_⟩
    · simp only [step, land_occ, hR, ho]
    · simp only [step, land_sup, hR, ho, hs]
    · simp only [step, land, hR]
      split_ifs <;> simp only [insertAtoms, refresh_table, commit, ht]
  | retire c p =>
    refine ⟨funext fun c' ↦ ?_, funext fun c' ↦ ?_, ?_⟩
    · simp only [step, retire_occ, ho]
    · simp only [step, retire_sup, ho, hs]
    · simp only [step, retire, ho]
      split_ifs <;> simp only [refresh_table, retireCommit, ht]
  | purge d =>
    have hp : purged d s = purged d t := by simp only [purged, stillHeld, byDigest, ho]
    refine ⟨?_, ?_, ?_⟩
    · simp only [step, purge, refresh_occ, purgeCommit, ho]
    · simp only [step, purge, refresh_sup, purgeCommit, hs]
    · simp only [step, purge, refresh_table, purgeCommit, ht, hp]
  | repair => exact ⟨ho, hs, ht⟩

theorem run_sameRel {ops : List (Op K P D A)} {s t : State K P D A} (h : SameRel s t) :
    SameRel (run ops s) (run ops t) := by
  induction ops generalizing s t with
  | nil => exact h
  | cons op ops ih => exact ih (sameRel_step h)

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
  search_congr dist (view_eq_of_sameRel (run_sameRel h)) (complete_run hs hws).1.mono
    (complete_run ht hwt).1.mono k sup

/-- **PLN-4** A land that writes its cache's additions first can crash after its transaction with
no reader the wiser: from a coherent plane with no dangling row, every search after any trace
answers as it would had the land finished. -/
theorem search_after_crash (dist : A → Δ) {C : Finset K} (ops : List (Op K P D A))
    {f : Fiber K P D A} {s : State K P D A} (hc : Coherent s) (hw : WF s) (k : ℕ) (sup : Bool) :
    search dist C (run ops (landAddCommit f s)) k sup =
      search dist C (run ops (land f s)) k sup := by
  have hrel : SameRel (landAddCommit f s) (land f s) := by
    unfold landAddCommit
    split_ifs with hr
    · simp only [land, hr, ↓reduceIte]
      exact ⟨rfl, rfl, rfl⟩
    · rw [← land_of_landAdd hr]
      exact ⟨rfl, rfl, rfl⟩
  have hwc : WF (landAddCommit f s) := by
    have := wf_land (f := f) hw
    obtain ⟨ho, -, ht⟩ := hrel
    intro c o hoc
    rw [ht]
    exact this c o (ho ▸ hoc)
  exact search_run_of_sameRel dist ops hrel (complete_landAddCommit (hc.complete univ) hw) hwc
    ((coherent_land hc hw).complete univ) (wf_land hw) k sup

end CrashSearch

/-! ### The chunk-key migration (#37) -/

namespace Phys

variable {I T : Type*}

@[simp] theorem rekey_path (key : Option P → T → I) (r : Phys P I T) :
    (r.rekey key).path = r.path := by
  unfold rekey
  split_ifs <;> rfl

@[simp] theorem rekey_text (key : Option P → T → I) (r : Phys P I T) :
    (r.rekey key).text = r.text := by
  unfold rekey
  split_ifs <;> rfl

@[simp] theorem rekey_note (key : Option P → T → I) (r : Phys P I T) :
    (r.rekey key).note = r.note := by
  unfold rekey
  split_ifs <;> rfl

theorem note_rekey {key : Option P → T → I} {r : Phys P I T} : (r.rekey key).Note ↔ r.Note := by
  simp only [Note, rekey_path, rekey_note]

theorem rekey_of_not_note {key : Option P → T → I} {r : Phys P I T} (h : ¬r.Note) :
    r.rekey key = r := by
  simp only [rekey, h, ↓reduceIte]

theorem id_rekey_of_note {key : Option P → T → I} {r : Phys P I T} (h : r.Note) :
    (r.rekey key).id = key r.path r.text := by
  simp only [rekey, h, ↓reduceIte]

theorem content_rekey (key : Option P → T → I) (r : Phys P I T) :
    (r.rekey key).content = r.content := by
  simp only [content, rekey_path, rekey_text, rekey_note]

theorem rekey_rekey (key : Option P → T → I) (r : Phys P I T) :
    (r.rekey key).rekey key = r.rekey key := by
  by_cases h : r.Note
  · have e : r.rekey key = { r with id := key r.path r.text } := by
      simp only [rekey, h, ↓reduceIte]
    have h' : ({ r with id := key r.path r.text } : Phys P I T).Note := e ▸ note_rekey.2 h
    rw [e]
    simp only [rekey, h', ↓reduceIte]
  · rw [rekey_of_not_note h, rekey_of_not_note h]

end Phys

namespace Store

variable {I T : Type*} [DecidableEq P] [DecidableEq I] [DecidableEq T]

theorem rekey_plane (key : Option P → T → I) (s : Store K P D A I T) :
    (s.rekey key).plane = s.plane := rfl

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
      (s.rekey key).phys.image Phys.content = s.phys.image Phys.content := by
  refine ⟨rfl, ?_, ?_, ?_⟩
  · ext r
    simp only [rekey, Finset.mem_filter, Finset.mem_image]
    constructor
    · rintro ⟨⟨q, hq, rfl⟩, hn⟩
      have hqn : ¬q.Note := fun h ↦ hn (Phys.note_rekey.2 h)
      rw [Phys.rekey_of_not_note hqn]
      exact ⟨hq, hqn⟩
    · rintro ⟨hr, hn⟩
      exact ⟨⟨r, hr, Phys.rekey_of_not_note hn⟩, hn⟩
  · intro r hr hn
    obtain ⟨q, -, rfl⟩ := Finset.mem_image.1 hr
    rw [Phys.id_rekey_of_note (Phys.note_rekey.1 hn), Phys.rekey_path, Phys.rekey_text]
  · simp only [rekey, Finset.image_image]
    congr 1
    funext r
    exact Phys.content_rekey key r

/-- **PLN-6** What the plane's laws need kept: from a state `Good κ` holds of (a coherent cache,
no dangling row, every path at one stratum, the hypotheses of PLN-2 and of PLN-4's land), the
re-key leaves a state it holds of, with the same view under every clearance; with the plane's
state unchanged, every search answers as before and PLN-1 to PLN-5 hold after it as before. -/
theorem rekey_good [DecidableEq A] [Fintype K] [DecidableEq K] {κ : P → K}
    (key : Option P → T → I) {s : Store K P D A I T} (hs : Good κ s.plane) :
    Good κ (s.rekey key).plane ∧ ∀ C, view C (s.rekey key).plane = view C s.plane :=
  ⟨hs, fun _ ↦ rfl⟩

/-- **PLN-6** Re-running the re-key changes nothing. -/
theorem rekey_idem (key : Option P → T → I) (s : Store K P D A I T) :
    (s.rekey key).rekey key = s.rekey key := by
  have h : (s.phys.image (Phys.rekey key)).image (Phys.rekey key) =
      s.phys.image (Phys.rekey key) := by
    rw [Finset.image_image]
    congr 1
    funext r
    exact Phys.rekey_rekey key r
  simp only [rekey, h]

variable [LinearOrder D] [DecidableEq A] [Fintype K] [DecidableEq K]

/-- **PLN-6, the unscoped form.** `reset()` and adding back what `all_rows()` returns leaves no
shed atom row, whatever the store held: every code atom the membership relation names is gone. -/
theorem rekeyReset_drops_atoms (key : Option P → T → I) (fs : List (Fiber K P D A))
    (s : Store K P D A I T) : ∀ r ∈ (s.rekeyReset key fs).phys, r.path.isSome = true := by
  intro r hr
  obtain ⟨q, hq, rfl⟩ := Finset.mem_image.1 hr
  exact (Finset.mem_filter.1 hq).2

end Store

/-! ### Where the hypotheses bite -/

namespace Witness

theorem wf_drifted : WF drifted := by decide

/-- **PLN-2, the cache-drift channel.** After the crash, the cleared document's atom has an empty
cache and search under `{0}` misses it (fail-closed). The uncleared land leaves the cleared view
alone, yet it refreshes the shared atom's whole held set, and the hit comes back: an uncleared write
changed a cleared read. Noninterference needs a cache complete on `C`. -/
theorem drift_interferes :
    view {0} (land fy drifted) = view {0} drifted ∧
      search (fun _ ↦ (0 : ℕ)) {0} drifted 1 false = [] ∧
      search (fun _ ↦ (0 : ℕ)) {0} (land fy drifted) 1 false ≠ [] := by
  refine ⟨view_step_invisible (op := .land fy) wf_drifted (by decide), ?_, ?_⟩
  · have h : (prefilter {0} drifted false).filter (cleared {0} drifted false ·) = ∅ := by decide
    simp [search_eq, h, byDist]
  · have h : (prefilter {0} (land fy drifted) false).filter
        (cleared {0} (land fy drifted) false ·) = {0} := by decide
    simp [search_eq, h, byDist]

/-- **PLN-2, the stratum channel.** Path 0 lands in class 1, then in class 0. The cleared land is
refused because the uncleared one holds the path, so the cleared view differs from the trace without
the uncleared write. Noninterference needs every path at one stratum fixed in advance. -/
theorem stratum_interferes :
    view {0} (run [.land ⟨1, 0, 0, [(0, 0)]⟩, .land ⟨0, 0, 0, [(0, 0)]⟩]
        (empty : State (Fin 2) (Fin 2) (Fin 1) (Fin 1))) ≠
      view {0} (run ([.land ⟨1, 0, 0, [(0, 0)]⟩, .land ⟨0, 0, 0, [(0, 0)]⟩].filter
        (·.visible {0})) (empty : State (Fin 2) (Fin 2) (Fin 1) (Fin 1))) := by
  intro h
  have h0 := occ_eq_of_view h (c := 0) (by decide)
  revert h0
  decide

/-- **PLN-6, the unscoped form drops the history.** `all_rows()` returns the plane's current rows,
which regroup into the note's second version alone (`vb`); after `reset()` and adding them back,
the reader under `{0}` no longer sees the first version's rows or the edge that superseded it,
whatever the key. The scoped re-key leaves the view as it is. -/
theorem rekeyReset_drops_history (key : Option (Fin 1) → Fin 2 → ℕ) :
    view {0} (edited.rekeyReset key [vb]).plane ≠ view {0} edited.plane ∧
      view {0} (edited.rekey key).plane = view {0} edited.plane := by
  refine ⟨fun h ↦ ?_, rfl⟩
  have h0 := occ_eq_of_view h (c := 0) (by decide)
  change (run [.land vb] empty).occ 0 = edited.plane.occ 0 at h0
  revert h0
  decide

/-- **PLN-6, the unscoped form merges rows.** The note lane's key, given to code records, merges two
layers' records of one document and one text into one row; before the guard, it merges the two
shed atoms of one text too, both their ids gone, whatever the key. The scoped re-key keeps all four
rows. -/
theorem rekeyReset_merges (key : Option (Fin 1) → Fin 2 → ℕ) :
    (edited.rekeyReset key [vb]).phys.card = 1 ∧
      ((edited.rekeyResetUnguarded key [vb]).phys.filter fun r ↦ r.path = none).card = 1 ∧
      edited.phys.card = 4 ∧ (edited.rekey key).phys = edited.phys := by
  have hrec : (edited.phys.filter fun r ↦ r.path.isSome = true) =
      {⟨1, some 0, 1, false⟩, ⟨2, some 0, 1, false⟩} := by decide
  have hnote : ∀ r ∈ edited.phys, ¬r.Note := by decide
  refine ⟨?_, ?_, by decide, ?_⟩
  · simp [Store.rekeyReset, hrec]
  · have hall : edited.phys =
        {⟨0, none, 0, false⟩, ⟨3, none, 0, false⟩, ⟨1, some 0, 1, false⟩, ⟨2, some 0, 1, false⟩} :=
      rfl
    simp [Store.rekeyResetUnguarded, hall, Finset.filter_insert]
  · change edited.phys.image (Phys.rekey key) = edited.phys
    conv_rhs => rw [← Finset.image_id (s := edited.phys)]
    exact Finset.image_congr fun r hr ↦ Phys.rekey_of_not_note (hnote r hr)

/-- **PLN-4, what a re-run does not do** (dn-ingest-door §9 item 7). The note's second version
crashes after its transaction, and landing it again leaves the first version's atom cached as held,
which no current row holds: the re-run refreshes the atoms it lands and frees, and the first run's
freed atoms are neither. The cache stays stale by excess, complete all the same, until `repair`. -/
theorem rerun_keeps_excess :
    ¬Coherent (land vb (landAddCommit vb (land va empty))) ∧
      Complete univ (land vb (landAddCommit vb (land va empty))) ∧
      Coherent (repair (land vb (landAddCommit vb (land va empty)))) := by
  decide

end Witness

end Palace.Plane
