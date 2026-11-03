module

public import Palace.Scope.Defs
public import Mathlib.Data.Finset.Card
public import Mathlib.Data.Finset.Union
public import Mathlib.Data.Fintype.Basic
public import Mathlib.Order.Basic

/-!
# The capability-scope algebra (CQ-scope)

Statements of the scope algebra's laws (dn-capability-scope §2.1, §2.2), mirroring
`core/kernel/scope.py`, the query engine's grants in `core/query.py`, the role signatures of
`core/kernel/agent_scope.py`, and the strata-to-classes table of `core/kernel/clearance.py`.

A scope is `s = (Σ, E, T, A)`: a set of strata closed under refinement, a set of edge fibers, a
clock with a window, and three chains of authority. Meet is safe composition: a delegated agent
receives `meet(parent, template)`, and `scope.py` promises `meet(parent, template) ⊑ parent`
always (non-negotiable #6). The enforcement tier rides beside the four coordinates and composes
by minimum, so that a convention-tier grant cannot launder through a structural wrapper.

What the model shows, against the code as fixed on this branch:

* Σ and E meet and join by `∩` and `∪`, and A by the minimum and maximum on each chain. Closure
  under refinement is a closure operator whose closed sets are closed under both. `top()` is not
  their top: it omits `exhaust` and `hypothetical` as well as the denylist (`top_eq`).
* Windows are ordered by a preorder, not a partial order: `pt(1)` and `[1,1]` lie below each other.
  Join is the least upper bound of any two windows. Meet is a lower bound of any two and the
  greatest among well-formed ones; the one counterexample, an inverted interval, the constructor
  now refuses (`le_meet_iff_of_valid`). Absorption holds up to the preorder, not on the nose.
* Delegation is monotone: a scope meet that exists lies under both inputs and is their greatest
  lower bound, and any composition carries exactly the least tier of its inputs. `Scope.meet`
  consults no clock atlas: the atlas completes the time meet on `N`, under neither input
  (`pullbackMeet_not_le`), so a delegation through it would not be monotone. The meet is partial
  across clocks and where the result trips the SLICE rule (`meet_slices`); `Grant.meet` skips both,
  and a cut only one side carries survives when the meet keeps that side's window.
* Admissibility and the zone law (private reads ⊥ world reach) are downward closed and survive
  every meet; the zone law does not survive join. Its private set includes `exhaust`, so a
  world-reaching scope it admits names only `world`, the denylist and the overlay, and is cleared
  for no class (`world_reach_reads_nothing`).
* A search never slices, over any strata (`search_never_slices`): the single-read cut follows the
  closed strata, so the Ambassador's search over `reference` alone builds and is admitted.

The model is exact. Window bounds are ints or opaque tokens compared by equality (Python's
`1.0 == 1` is outside it); edge fibers are the three letters every caller uses; the cut is an
opaque token. The transcription agrees with the Python on an enumeration of 234,321 results:
window and scope meets, joins and orders, constructions under the SLICE rule, the zone law, and
`required()` over the Ambassador's strata names (`formal/README.md`).
-/

@[expose] public section

open Finset

namespace Palace.CQ

/-- An equality test on `Except` that `decide` can unfold. Batteries derives one, but the module
system does not expose its body to importers, so `decide` cannot reduce it. -/
instance instDecidableEqExcept {ε α : Type*} [DecidableEq ε] [DecidableEq α] :
    DecidableEq (Except ε α)
  | .error a, .error b => decidable_of_iff (a = b) (by simp)
  | .ok a, .ok b => decidable_of_iff (a = b) (by simp)
  | .error _, .ok _ => isFalse (by simp)
  | .ok _, .error _ => isFalse (by simp)

/-! ## Σ: the stratum-refinement forest -/

namespace Stratum

/-- The forest is one level deep: no refinement refines a refinement. -/
theorem parent_parent : ∀ c p : Stratum, c.parent = some p → p.parent = none := by decide

/-- The strata in declaration order, for attacks. -/
def nth : ℕ → Stratum
  | 0 => mirror | 1 => mirrorAuthored | 2 => curated | 3 => observed | 4 => ops | 5 => reference
  | 6 => referenceRepo | 7 => interpreted | 8 => world | 9 => dialogue | 10 => dialogueTranscript
  | 11 => dialogueArtifact | 12 => exhaust | 13 => hypothetical | _ => foundation

end Stratum

instance (S : Finset Stratum) : Decidable (IsDown S) := by unfold IsDown; infer_instance

/-! ## T: clocks and windows -/

instance : Fintype Clock :=
  Fintype.ofList
    (open Clock in [N, Ns, commit, distinctSnapshot, projectionEvent, lastWrite, wall, now])
    fun x ↦ by cases x <;> simp

namespace Clock

/-- `_finer_or_equal`: `N` refines every clock, a commit refines its distinct snapshots. -/
def FinerOrEq (a b : Clock) : Prop := a = b ∨ a = N ∨ (a = commit ∧ b = distinctSnapshot)

instance : DecidableRel FinerOrEq := fun _ _ ↦ by unfold FinerOrEq; infer_instance

/-- `common_refinement`: the finer of two comparable clocks, unless that is the parked `N`. -/
def commonRefinement (a b : Clock) : Option Clock :=
  if FinerOrEq a b then (if a = N then none else some a)
  else if FinerOrEq b a then (if b = N then none else some b) else none

/-- A common refinement refines both clocks, and it is never the parked `N`. -/
theorem commonRefinement_spec :
    ∀ a b c : Clock, commonRefinement a b = some c → FinerOrEq c a ∧ FinerOrEq c b ∧ c ≠ N := by
  decide

end Clock

namespace Window

instance (a b : Window) : Decidable (Within a b) := by
  unfold Within; split <;> infer_instance

instance (a b : Window) : Decidable (Le a b) := by unfold Le; infer_instance

instance (w : Window) : Decidable (WF w) := by unfold WF; split <;> infer_instance

instance (w : Window) : Decidable (Valid w) := by unfold Valid; infer_instance

end Window

namespace Time

instance (a b : Time) : Decidable (Le a b) := by unfold Le; infer_instance

end Time

/-! ## A: authority, and the tier -/

namespace Authority

instance (a b : Authority) : Decidable (Le a b) := by unfold Le; infer_instance

end Authority

/-! ## The scope -/

namespace Scope

instance (s : Scope) : Decidable (Valid s) := by unfold Valid; infer_instance

instance (a b : Scope) : Decidable (Le a b) := by unfold Le; infer_instance

end Scope

/-! ## Firewalls and the zone law -/

instance (s : Scope) : Decidable (zoneOk s) := by unfold zoneOk; infer_instance

/-! ## The query engine: grants and required scopes (`core/query.py`) -/

instance (ιs : List (Finset Stratum)) (s : Scope) : Decidable (admissible ιs s) := by
  unfold admissible excludes; infer_instance

instance (g : List Scope) : Decidable (GrantOk g) := by unfold GrantOk; infer_instance

instance (g : List Scope) (r : Scope) : Decidable (admits g r) := by unfold admits; infer_instance

/-- The strata names the Ambassador's MCP tools accept (`agents/ambassador/mcp.py`). -/
inductive Name
  | mirror | dialogue | interpreted | curated | observed | reference
  deriving DecidableEq, Repr

instance : Fintype Name :=
  Fintype.ofList (open Name in [mirror, dialogue, interpreted, curated, observed, reference])
    fun x ↦ by cases x <;> simp

/-- `_strata`'s table. -/
def Name.stratum : Name → Stratum
  | .mirror => .mirrorAuthored
  | .dialogue => .dialogueTranscript
  | .interpreted => .interpreted
  | .curated => .curated
  | .observed => .observed
  | .reference => .reference

/-- `_strata`: the picked names, or mirror and dialogue when none are given. -/
def pick (names : List Name) : List Stratum :=
  (if names = [] then [.mirror, .dialogue] else names).map Name.stratum

/-! ## Roles (`core/kernel/agent_scope.py`) -/

/-- `sensor_scope`: one stratum, no edges, its event clock, the projection-write bit. -/
def sensor (s : Stratum) : Scope := ⟨close {s}, ∅, ⟨.Ns, .all⟩, ⟨0, 1, 0⟩, 1, none⟩

/-- `query_scope`: read-only over the strata named, every edge class, the ledger. -/
def query (S : Finset Stratum) : Scope := ⟨close S, univ, ⟨.N, .all⟩, ⟨0, 0, 0⟩, 1, none⟩

/-- `dreamer_scope`: the strata named, every edge class, the ledger, the projection-write bit. -/
def dreamer (S : Finset Stratum) : Scope := ⟨close S, univ, ⟨.N, .all⟩, ⟨0, 1, 0⟩, 1, none⟩

/-- `internal_actor` (IA): broad private read, propose, no world reach; the overlay when staging. -/
def internalActor (S : Finset Stratum) (hypothetical : Bool) : Scope :=
  ⟨if hypothetical then insert .hypothetical (close S) else close S, univ, ⟨.commit, .all⟩,
    ⟨1, 1, 0⟩, 1, none⟩

/-- `external_proposer` (EA-p): propose-only over the strata named, no world reach. -/
def externalProposer (S : Finset Stratum) : Scope :=
  ⟨close S, univ, ⟨.N, .all⟩, ⟨1, 0, 0⟩, 1, none⟩

/-- `external_executor` (EA-x): no stratum at all, world reach `reach`. -/
def externalExecutor (reach : Fin 4) : Scope := ⟨∅, ∅, ⟨.now, .all⟩, ⟨0, 0, reach⟩, 1, none⟩

/-- A store handle an agent holds (`Handle`). -/
structure Handle where
  /-- The stratum the handle reads. -/
  stratum : Stratum
  /-- Whether it writes that stratum's projection. -/
  writesStratum : Bool
  /-- The edge fiber it writes, if any. -/
  writesFiber : Option Fiber

/-- `assert_conforms` passes: every handle stays inside the declared scope. -/
def Conforms (s : Scope) (hs : List Handle) : Prop :=
  ∀ h ∈ hs, h.stratum ∈ s.sigma ∧ (h.writesStratum = true → 1 ≤ s.authority.storeWrite) ∧
    ∀ f, h.writesFiber = some f → f ∈ s.edges

/-! ## Clearances (`core/kernel/clearance.py`) -/

instance : Fintype Prov :=
  Fintype.ofList (open Prov in
    [authoredSolo, authoredDialogue, curated, interpreted, derivedStratum, observed, code])
    fun x ↦ by cases x <;> simp

/-- `STRATUM_CLASSES`: the classes a stratum's rows carry; an absent stratum names none. -/
def stratumClasses : Stratum → Finset Prov
  | .mirror | .mirrorAuthored => {.authoredSolo, .authoredDialogue}
  | .curated => {.curated}
  | .interpreted => {.interpreted}
  | .observed => {.observed}
  | .dialogue | .dialogueTranscript => {.observed, .authoredDialogue}
  | .reference | .referenceRepo => {.code}
  | _ => ∅

/-! ## Σ: closure is a closure operator; `top` is not the top -/

section Sigma

theorem mem_close {S : Finset Stratum} {c : Stratum} :
    c ∈ close S ↔ c ∈ S ∨ (c ≠ .exhaust ∧ ∃ p ∈ S, c.parent = some p) := by
  simp [close]

theorem subset_close (S : Finset Stratum) : S ⊆ close S := subset_union_left

theorem close_mono {S T : Finset Stratum} (h : S ⊆ T) : close S ⊆ close T := by
  intro c hc
  rcases mem_close.1 hc with hc | ⟨hx, p, hp, hcp⟩
  · exact mem_close.2 (Or.inl (h hc))
  · exact mem_close.2 (Or.inr ⟨hx, p, h hp, hcp⟩)

theorem isDown_iff {S : Finset Stratum} : IsDown S ↔ close S = S := by
  refine ⟨fun h ↦ Subset.antisymm (fun c hc ↦ ?_) (subset_close S), fun h c p hx hcp hp ↦ ?_⟩
  · rcases mem_close.1 hc with hc | ⟨hx, p, hp, hcp⟩
    · exact hc
    · exact h c p hx hcp hp
  · rw [← h]
    exact mem_close.2 (Or.inr ⟨hx, p, hp, hcp⟩)

/-- **SCO-1** `close S` is closed: the forest is one level deep. -/
theorem close_isDown (S : Finset Stratum) : IsDown (close S) := by
  intro c p hx hcp hp
  rcases mem_close.1 hp with hp | ⟨_, q, _, hpq⟩
  · exact mem_close.2 (Or.inr ⟨hx, p, hp, hcp⟩)
  · simp [Stratum.parent_parent c p hcp] at hpq

/-- **SCO-1** Closure is idempotent. -/
theorem close_close (S : Finset Stratum) : close (close S) = close S :=
  isDown_iff.1 (close_isDown S)

/-- `close S` is the least closed set containing `S`. -/
theorem close_subset {S T : Finset Stratum} (hST : S ⊆ T) (hT : IsDown T) : close S ⊆ T :=
  (close_mono hST).trans (isDown_iff.1 hT).le

/-- **SCO-1** Closed sets are closed under intersection. -/
theorem IsDown.inter {S T : Finset Stratum} (hS : IsDown S) (hT : IsDown T) : IsDown (S ∩ T) :=
  fun c p hx hcp hp ↦
    mem_inter.2 ⟨hS c p hx hcp (mem_inter.1 hp).1, hT c p hx hcp (mem_inter.1 hp).2⟩

/-- **SCO-1** And under union. -/
theorem IsDown.union {S T : Finset Stratum} (hS : IsDown S) (hT : IsDown T) : IsDown (S ∪ T) := by
  intro c p hx hcp hp
  rcases mem_union.1 hp with hp | hp
  · exact mem_union_left _ (hS c p hx hcp hp)
  · exact mem_union_right _ (hT c p hx hcp hp)

/-- **SCO-1** `top()` omits `exhaust` and `hypothetical`, not only the denylist. -/
theorem top_eq : top = univ \ {.foundation, .hypothetical, .exhaust} := by decide

/-- So `top()` is not the top of the closed sets: a set naming `exhaust` or `hypothetical` lies
outside it. -/
theorem not_close_subset_top : ¬ close {.exhaust} ⊆ top ∧ ¬ close {.hypothetical} ⊆ top := by
  decide

/-- `PRIVATE_STRATA` is every stratum but `world`, the denylist and the overlay; `exhaust` is in. -/
theorem privateStrata_eq : privateStrata = univ \ {.world, .foundation, .hypothetical} := by
  decide

end Sigma

/-! ## Windows: a preorder, with join the least upper bound and meet the greatest lower bound
among well-formed windows -/

namespace Window

theorem within_iff {a b : Window} : Within a b ↔
    ∃ al ah bl bh, a.ints = some (al, ah) ∧ b.ints = some (bl, bh) ∧ bl ≤ al ∧ ah ≤ bh := by
  unfold Within
  split
  · rename_i al ah bl bh ha hb
    simp [ha, hb]
  · rename_i h
    simp only [false_iff, not_exists, not_and]
    intro al ah bl bh ha hb _
    exact (h al ah bl bh ha hb).elim

theorem ints_span (lo hi : ℤ) : (span lo hi).ints = some (lo, hi) := by
  unfold span
  split_ifs with h
  · simp [ints, point, h]
  · simp [ints, interval]

theorem span_kind (lo hi : ℤ) : (span lo hi).kind ≠ .all ∧ (span lo hi).kind ≠ .empty := by
  unfold span
  split_ifs <;> simp [point, interval]

theorem Le.refl (a : Window) : a.Le a := Or.inr (Or.inr (Or.inl rfl))

theorem Within.trans {a b c : Window} (hab : Within a b) (hbc : Within b c) : Within a c := by
  obtain ⟨al, ah, bl, bh, ha, hb, h1, h2⟩ := within_iff.1 hab
  obtain ⟨bl', bh', cl, ch, hb', hc, h3, h4⟩ := within_iff.1 hbc
  simp only [hb, Option.some.injEq, Prod.mk.injEq] at hb'
  exact within_iff.2 ⟨al, ah, cl, ch, ha, hc, by omega, by omega⟩

theorem Le.trans {a b c : Window} (hab : a.Le b) (hbc : b.Le c) : a.Le c := by
  rcases hab with ha | hb | rfl | ⟨ha, hb, hw⟩
  · exact Or.inl ha
  · rcases hbc with hb' | hc | rfl | ⟨hb', -, -⟩
    · exact absurd (hb.symm.trans hb') (by decide)
    · exact Or.inr (Or.inl hc)
    · exact Or.inr (Or.inl hb)
    · exact absurd hb hb'
  · exact hbc
  · rcases hbc with hb' | hc | rfl | ⟨-, hc, hw'⟩
    · exact absurd hb' hb
    · exact Or.inr (Or.inl hc)
    · exact Or.inr (Or.inr (Or.inr ⟨ha, hb, hw⟩))
    · exact Or.inr (Or.inr (Or.inr ⟨ha, hc, hw.trans hw'⟩))

instance : Preorder Window where
  le := Le
  le_refl := Le.refl
  le_trans _ _ _ := Le.trans

theorem kind_of_le_empty {x a : Window} (h : x.Le a) (ha : a.kind = .empty) : x.kind = .empty := by
  rcases h with h | h | rfl | ⟨-, h, -⟩
  · exact h
  · exact absurd (h.symm.trans ha) (by decide)
  · exact ha
  · exact absurd ha h

theorem kind_of_all_le {a x : Window} (h : a.Le x) (ha : a.kind = .all) : x.kind = .all := by
  rcases h with h | h | rfl | ⟨h, -, -⟩
  · exact absurd (ha.symm.trans h) (by decide)
  · exact h
  · exact ha
  · exact absurd ha h

theorem ints_of_within {a b : Window} (h : Within a b) :
    (∃ al ah, a.ints = some (al, ah)) ∧ ∃ bl bh, b.ints = some (bl, bh) := by
  obtain ⟨al, ah, bl, bh, ha, hb, -⟩ := within_iff.1 h
  exact ⟨⟨al, ah, ha⟩, bl, bh, hb⟩

/-- The meet lies under its left argument, for every pair of windows. -/
theorem meet_le_left (a b : Window) : (a.meet b).Le a := by
  unfold meet
  split_ifs with h1 h2 h3 h4
  · exact Or.inl rfl
  · exact Or.inr (Or.inl h2)
  · exact Le.refl a
  · exact Le.refl a
  · simp only [not_or] at h1
    split
    · rename_i al ah bl bh ha hb
      split_ifs
      · exact Or.inl rfl
      · exact Or.inr (Or.inr (Or.inr ⟨(span_kind _ _).1, h1.1,
          within_iff.2 ⟨_, _, _, _, ints_span _ _, ha, le_max_left _ _, min_le_left _ _⟩⟩))
    · exact Or.inl rfl

/-- The meet lies under its right argument, for every pair of windows. -/
theorem meet_le_right (a b : Window) : (a.meet b).Le b := by
  unfold meet
  split_ifs with h1 h2 h3 h4
  · exact Or.inl rfl
  · exact Le.refl b
  · exact Or.inr (Or.inl h3)
  · exact h4 ▸ Le.refl a
  · simp only [not_or] at h1
    split
    · rename_i al ah bl bh ha hb
      split_ifs
      · exact Or.inl rfl
      · exact Or.inr (Or.inr (Or.inr ⟨(span_kind _ _).1, h1.2,
          within_iff.2 ⟨_, _, _, _, ints_span _ _, hb, le_max_right _ _, min_le_right _ _⟩⟩))
    · exact Or.inl rfl

/-- Among well-formed windows, the meet is the greatest lower bound. -/
theorem le_meet {x a b : Window} (hx : x.WF) (ha : x.Le a) (hb : x.Le b) : x.Le (a.meet b) := by
  unfold meet
  split_ifs with h1 h2 h3 h4
  · rcases h1 with h1 | h1
    · exact Or.inl (kind_of_le_empty ha h1)
    · exact Or.inl (kind_of_le_empty hb h1)
  · exact hb
  · exact ha
  · exact ha
  · simp only [not_or] at h1
    split
    · rename_i al ah bl bh hai hbi
      split_ifs with h5
      · -- the int windows are disjoint: only an empty window lies under both
        refine Or.inl ?_
        rcases ha with hx' | hak | rfl | ⟨-, -, hxa⟩
        · exact hx'
        · exact absurd hak h2
        · rcases hb with hx' | hbk | hab | ⟨-, -, hab⟩
          · exact hx'
          · exact absurd hbk h3
          · exact absurd hab h4
          · obtain ⟨al', ah', bl', bh', ha', hb', h6, h7⟩ := within_iff.1 hab
            simp only [hai, hbi, Option.some.injEq, Prod.mk.injEq] at ha' hb'
            obtain ⟨rfl, rfl⟩ := ha'
            obtain ⟨rfl, rfl⟩ := hb'
            simp only [WF, hai] at hx
            omega
        · rcases hb with hx' | hbk | rfl | ⟨-, -, hxb⟩
          · exact hx'
          · exact absurd hbk h3
          · obtain ⟨bl', bh', al', ah', hb', ha', h6, h7⟩ := within_iff.1 hxa
            simp only [hai, hbi, Option.some.injEq, Prod.mk.injEq] at ha' hb'
            obtain ⟨rfl, rfl⟩ := ha'
            obtain ⟨rfl, rfl⟩ := hb'
            simp only [WF, hbi] at hx
            omega
          · obtain ⟨xl, xh, al', ah', hxi, ha', h6, h7⟩ := within_iff.1 hxa
            obtain ⟨xl', xh', bl', bh', hxi', hb', h8, h9⟩ := within_iff.1 hxb
            simp only [hai, hbi, hxi, Option.some.injEq, Prod.mk.injEq] at ha' hb' hxi'
            obtain ⟨rfl, rfl⟩ := ha'
            obtain ⟨rfl, rfl⟩ := hb'
            obtain ⟨rfl, rfl⟩ := hxi'
            simp only [WF, hxi] at hx
            omega
      · -- they overlap: the meet is the int window `[max, min]`
        have hm := ints_span (max al bl) (min ah bh)
        rcases ha with hx' | hak | rfl | ⟨hxk, -, hxa⟩
        · exact Or.inl hx'
        · exact absurd hak h2
        · rcases hb with hx' | hbk | hab | ⟨-, -, hab⟩
          · exact Or.inl hx'
          · exact absurd hbk h3
          · exact absurd hab h4
          · obtain ⟨al', ah', bl', bh', ha', hb', h6, h7⟩ := within_iff.1 hab
            simp only [hai, hbi, Option.some.injEq, Prod.mk.injEq] at ha' hb'
            obtain ⟨rfl, rfl⟩ := ha'
            obtain ⟨rfl, rfl⟩ := hb'
            exact Or.inr (Or.inr (Or.inr ⟨h2, (span_kind _ _).2,
              within_iff.2 ⟨_, _, _, _, hai, hm, by omega, by omega⟩⟩))
        · rcases hb with hx' | hbk | rfl | ⟨-, -, hxb⟩
          · exact Or.inl hx'
          · exact absurd hbk h3
          · obtain ⟨bl', bh', al', ah', hb', ha', h6, h7⟩ := within_iff.1 hxa
            simp only [hai, hbi, Option.some.injEq, Prod.mk.injEq] at ha' hb'
            obtain ⟨rfl, rfl⟩ := ha'
            obtain ⟨rfl, rfl⟩ := hb'
            exact Or.inr (Or.inr (Or.inr ⟨h3, (span_kind _ _).2,
              within_iff.2 ⟨_, _, _, _, hbi, hm, by omega, by omega⟩⟩))
          · obtain ⟨xl, xh, al', ah', hxi, ha', h6, h7⟩ := within_iff.1 hxa
            obtain ⟨xl', xh', bl', bh', hxi', hb', h8, h9⟩ := within_iff.1 hxb
            simp only [hai, hbi, hxi, Option.some.injEq, Prod.mk.injEq] at ha' hb' hxi'
            obtain ⟨rfl, rfl⟩ := ha'
            obtain ⟨rfl, rfl⟩ := hb'
            obtain ⟨rfl, rfl⟩ := hxi'
            exact Or.inr (Or.inr (Or.inr ⟨hxk, (span_kind _ _).2,
              within_iff.2 ⟨_, _, _, _, hxi, hm, by omega, by omega⟩⟩))
    · -- not both int-bounded: only an empty window lies under both
      rename_i hn
      refine Or.inl ?_
      rcases ha with hx' | hak | rfl | ⟨-, -, hxa⟩
      · exact hx'
      · exact absurd hak h2
      · rcases hb with hx' | hbk | hab | ⟨-, -, hab⟩
        · exact hx'
        · exact absurd hbk h3
        · exact absurd hab h4
        · obtain ⟨⟨al, ah, ha'⟩, bl, bh, hb'⟩ := ints_of_within hab
          exact absurd (hn al ah bl bh ha' hb') id
      · rcases hb with hx' | hbk | rfl | ⟨-, -, hxb⟩
        · exact hx'
        · exact absurd hbk h3
        · obtain ⟨⟨bl, bh, hb'⟩, al, ah, ha'⟩ := ints_of_within hxa
          exact absurd (hn al ah bl bh ha' hb') id
        · obtain ⟨-, al, ah, ha'⟩ := ints_of_within hxa
          obtain ⟨-, bl, bh, hb'⟩ := ints_of_within hxb
          exact absurd (hn al ah bl bh ha' hb') id

/-- The join lies over its left argument. -/
theorem le_join_left (a b : Window) : a.Le (a.join b) := by
  unfold join
  split_ifs with h1 h2 h3 h4
  · exact Or.inr (Or.inl rfl)
  · exact Or.inl h2
  · exact Le.refl a
  · exact Le.refl a
  · simp only [not_or] at h1
    split
    · rename_i al ah bl bh ha hb
      exact Or.inr (Or.inr (Or.inr ⟨h1.1, (span_kind _ _).2,
        within_iff.2 ⟨_, _, _, _, ha, ints_span _ _, min_le_left _ _, le_max_left _ _⟩⟩))
    · exact Or.inr (Or.inl rfl)

/-- The join lies over its right argument. -/
theorem le_join_right (a b : Window) : b.Le (a.join b) := by
  unfold join
  split_ifs with h1 h2 h3 h4
  · exact Or.inr (Or.inl rfl)
  · exact Le.refl b
  · exact Or.inl h3
  · exact h4 ▸ Le.refl a
  · simp only [not_or] at h1
    split
    · rename_i al ah bl bh ha hb
      exact Or.inr (Or.inr (Or.inr ⟨h1.2, (span_kind _ _).2,
        within_iff.2 ⟨_, _, _, _, hb, ints_span _ _, min_le_right _ _, le_max_right _ _⟩⟩))
    · exact Or.inr (Or.inl rfl)

/-- The join lies under every common upper bound: it is the least upper bound of any two
windows, well-formed or not. -/
theorem join_le {a b x : Window} (ha : a.Le x) (hb : b.Le x) : (a.join b).Le x := by
  unfold join
  split_ifs with h1 h2 h3 h4
  · rcases h1 with h1 | h1
    · exact Or.inr (Or.inl (kind_of_all_le ha h1))
    · exact Or.inr (Or.inl (kind_of_all_le hb h1))
  · exact hb
  · exact ha
  · exact ha
  · simp only [not_or] at h1
    split
    · rename_i al ah bl bh hai hbi
      have hm := ints_span (min al bl) (max ah bh)
      rcases ha with hae | hxk | rfl | ⟨-, hxk, hax⟩
      · exact absurd hae h2
      · exact Or.inr (Or.inl hxk)
      · rcases hb with hbe | hxk | hba | ⟨-, -, hba⟩
        · exact absurd hbe h3
        · exact Or.inr (Or.inl hxk)
        · exact absurd hba.symm h4
        · obtain ⟨bl', bh', al', ah', hb', ha', h6, h7⟩ := within_iff.1 hba
          simp only [hai, hbi, Option.some.injEq, Prod.mk.injEq] at ha' hb'
          obtain ⟨rfl, rfl⟩ := ha'
          obtain ⟨rfl, rfl⟩ := hb'
          exact Or.inr (Or.inr (Or.inr ⟨(span_kind _ _).1, h2,
            within_iff.2 ⟨_, _, _, _, hm, hai, by omega, by omega⟩⟩))
      · rcases hb with hbe | hxk' | rfl | ⟨-, -, hbx⟩
        · exact absurd hbe h3
        · exact Or.inr (Or.inl hxk')
        · obtain ⟨al', ah', bl', bh', ha', hb', h6, h7⟩ := within_iff.1 hax
          simp only [hai, hbi, Option.some.injEq, Prod.mk.injEq] at ha' hb'
          obtain ⟨rfl, rfl⟩ := ha'
          obtain ⟨rfl, rfl⟩ := hb'
          exact Or.inr (Or.inr (Or.inr ⟨(span_kind _ _).1, h3,
            within_iff.2 ⟨_, _, _, _, hm, hbi, by omega, by omega⟩⟩))
        · obtain ⟨al', ah', xl, xh, ha', hxi, h6, h7⟩ := within_iff.1 hax
          obtain ⟨bl', bh', xl', xh', hb', hxi', h8, h9⟩ := within_iff.1 hbx
          simp only [hai, hbi, hxi, Option.some.injEq, Prod.mk.injEq] at ha' hb' hxi'
          obtain ⟨rfl, rfl⟩ := ha'
          obtain ⟨rfl, rfl⟩ := hb'
          obtain ⟨rfl, rfl⟩ := hxi'
          exact Or.inr (Or.inr (Or.inr ⟨(span_kind _ _).1, hxk,
            within_iff.2 ⟨_, _, _, _, hm, hxi, by omega, by omega⟩⟩))
    · -- not both int-bounded: the join widens to `∗`, so `x` must be `∗`
      rename_i hn
      refine Or.inr (Or.inl ?_)
      rcases ha with hae | hxk | rfl | ⟨-, -, hax⟩
      · exact absurd hae h2
      · exact hxk
      · rcases hb with hbe | hxk | hba | ⟨-, -, hba⟩
        · exact absurd hbe h3
        · exact hxk
        · exact absurd hba.symm h4
        · obtain ⟨⟨bl, bh, hb'⟩, al, ah, ha'⟩ := ints_of_within hba
          exact absurd (hn al ah bl bh ha' hb') id
      · rcases hb with hbe | hxk | rfl | ⟨-, -, hbx⟩
        · exact absurd hbe h3
        · exact hxk
        · obtain ⟨⟨al, ah, ha'⟩, bl, bh, hb'⟩ := ints_of_within hax
          exact absurd (hn al ah bl bh ha' hb') id
        · obtain ⟨⟨al, ah, ha'⟩, -⟩ := ints_of_within hax
          obtain ⟨⟨bl, bh, hb'⟩, -⟩ := ints_of_within hbx
          exact absurd (hn al ah bl bh ha' hb') id

/-- **SCO-2** The join of two windows is their least upper bound. -/
theorem join_le_iff {a b x : Window} : (a.join b).Le x ↔ a.Le x ∧ b.Le x :=
  ⟨fun h ↦ ⟨(le_join_left a b).trans h, (le_join_right a b).trans h⟩, fun h ↦ join_le h.1 h.2⟩

theorem le_meet_iff {x a b : Window} (hx : x.WF) : x.Le (a.meet b) ↔ x.Le a ∧ x.Le b :=
  ⟨fun h ↦ ⟨h.trans (meet_le_left a b), h.trans (meet_le_right a b)⟩,
    fun h ↦ le_meet hx h.1 h.2⟩

/-- The meet of well-formed windows is well-formed. -/
theorem wf_meet {a b : Window} (ha : a.WF) (hb : b.WF) : (a.meet b).WF := by
  unfold meet
  split_ifs
  · simp [WF, ints, empty]
  · exact hb
  · exact ha
  · exact ha
  · split
    · split_ifs with h
      · simp [WF, ints, empty]
      · simp only [WF, ints_span]
        omega
    · simp [WF, ints, empty]

/-- Absorption holds up to the preorder on well-formed windows. -/
theorem absorb {a b : Window} (ha : a.WF) : (a.meet (a.join b)).Le a ∧ a.Le (a.meet (a.join b)) :=
  ⟨meet_le_left _ _, le_meet ha (Le.refl a) (le_join_left a b)⟩

theorem Valid.wf {w : Window} (h : w.Valid) : w.WF := by
  rcases w with ⟨k, lo, hi⟩
  obtain ⟨h1, h2, h3⟩ := h
  cases k with
  | point =>
    obtain rfl : lo = hi := h2 rfl
    cases lo <;> simp [WF, ints]
  | interval => exact h3 rfl
  | all =>
    obtain ⟨rfl, rfl⟩ := h1 (Or.inl rfl)
    simp [WF, ints]
  | empty =>
    obtain ⟨rfl, rfl⟩ := h1 (Or.inr rfl)
    simp [WF, ints]

theorem span_valid {lo hi : ℤ} (h : lo ≤ hi) : (span lo hi).Valid := by
  unfold span
  split_ifs <;> simp_all [Valid, point, interval, WF, ints]

theorem valid_empty : empty.Valid := by simp [Valid, empty]

theorem valid_all : all.Valid := by simp [Valid, all]

/-- The meet of two valid windows is valid: the algebra never builds what the constructor
refuses. -/
theorem valid_meet {a b : Window} (ha : a.Valid) (hb : b.Valid) : (a.meet b).Valid := by
  unfold meet
  split_ifs
  · exact valid_empty
  · exact hb
  · exact ha
  · exact ha
  · split
    · split_ifs with h
      · exact valid_empty
      · exact span_valid (by omega)
    · exact valid_empty

/-- The join of two valid windows is valid. -/
theorem valid_join {a b : Window} (ha : a.Valid) (hb : b.Valid) : (a.join b).Valid := by
  unfold join
  split_ifs
  · exact valid_all
  · exact hb
  · exact ha
  · exact ha
  · split
    · rename_i al ah bl bh hai _
      have := ha.wf
      simp only [WF, hai] at this
      exact span_valid (by omega)
    · exact valid_all

/-- **SCO-2** So on valid windows the meet is the exact greatest lower bound: the constructor
refuses the one counterexample, an inverted interval. -/
theorem le_meet_iff_of_valid {x a b : Window} (hx : x.Valid) :
    x.Le (a.meet b) ↔ x.Le a ∧ x.Le b :=
  le_meet_iff hx.wf

end Window

/-! ## Time scopes -/

namespace Time

theorem meetVia_none {a b : Time} :
    a.meetVia none b =
      if a.clock = b.clock then some ⟨a.clock, a.window.meet b.window⟩ else none := by
  unfold meetVia
  split_ifs <;> rfl

theorem Le.trans {a b c : Time} (hab : a.Le b) (hbc : b.Le c) : a.Le c :=
  ⟨hab.1.trans hbc.1, hab.2.trans hbc.2⟩

theorem meet_le {a b t : Time} (h : a.meetVia none b = some t) : t.Le a ∧ t.Le b := by
  rw [meetVia_none] at h
  split_ifs at h with hc
  cases h
  exact ⟨⟨rfl, Window.meet_le_left _ _⟩, ⟨hc, Window.meet_le_right _ _⟩⟩

theorem le_meet {a b t x : Time} (h : a.meetVia none b = some t) (hx : x.window.WF)
    (ha : x.Le a) (hb : x.Le b) : x.Le t := by
  rw [meetVia_none] at h
  split_ifs at h with hc
  cases h
  exact ⟨ha.1, Window.le_meet hx ha.2 hb.2⟩

/-- **SCO-4** Under an atlas, two covered clocks meet through the event level. -/
theorem meetVia_atlas (A : Atlas) {a b : Time} (hab : a.clock ≠ b.clock)
    (ha : A.has a.clock = true) (hb : A.has b.clock = true) :
    a.meetVia (some A) b = some (pullbackMeet A a b) := by
  simp [meetVia, hab, ha, hb]

/-- **SCO-4** The completion lies on `N`, so under neither input on another clock: why delegation,
which must stay under the parent, refuses it. -/
theorem pullbackMeet_not_le (A : Atlas) {a b : Time} (haN : a.clock ≠ .N) (hbN : b.clock ≠ .N) :
    ¬ (pullbackMeet A a b).Le a ∧ ¬ (pullbackMeet A a b).Le b :=
  ⟨fun h ↦ haN h.1.symm, fun h ↦ hbN h.1.symm⟩

end Time

/-! ## Authority -/

namespace Authority

theorem meet_le_left (a b : Authority) : (a.meet b).Le a :=
  ⟨min_le_left _ _, min_le_left _ _, min_le_left _ _⟩

theorem meet_le_right (a b : Authority) : (a.meet b).Le b :=
  ⟨min_le_right _ _, min_le_right _ _, min_le_right _ _⟩

theorem le_meet {x a b : Authority} (ha : x.Le a) (hb : x.Le b) : x.Le (a.meet b) :=
  ⟨le_min ha.1 hb.1, le_min ha.2.1 hb.2.1, le_min ha.2.2 hb.2.2⟩

theorem Le.trans {a b c : Authority} (hab : a.Le b) (hbc : b.Le c) : a.Le c :=
  ⟨hab.1.trans hbc.1, hab.2.1.trans hbc.2.1, hab.2.2.trans hbc.2.2⟩

theorem le_join_left (a b : Authority) : a.Le (a.join b) :=
  ⟨le_max_left _ _, le_max_left _ _, le_max_left _ _⟩

theorem le_join_right (a b : Authority) : b.Le (a.join b) :=
  ⟨le_max_right _ _, le_max_right _ _, le_max_right _ _⟩

theorem join_le {a b x : Authority} (ha : a.Le x) (hb : b.Le x) : (a.join b).Le x :=
  ⟨max_le ha.1 hb.1, max_le ha.2.1 hb.2.1, max_le ha.2.2 hb.2.2⟩

end Authority

/-! ## Scopes: delegation, its partiality, and the tier -/

namespace Scope

theorem Le.trans {a b c : Scope} (hab : a.Le b) (hbc : b.Le c) : a.Le c :=
  ⟨hab.1.trans hbc.1, hab.2.1.trans hbc.2.1, hab.2.2.1.trans hbc.2.2.1, hab.2.2.2.trans hbc.2.2.2⟩

theorem build_ok {s m : Scope} : s.build = .ok m ↔ ¬ s.Slices ∧ s = m := by
  unfold build
  split_ifs with h <;> simp [h]

/-- What a meet that exists returns. -/
theorem meet_ok {a b m : Scope} (h : a.meet b = .ok m) : a.time.clock = b.time.clock ∧
    ¬ m.Slices ∧ m = ⟨a.sigma ∩ b.sigma, a.edges ∩ b.edges,
      ⟨a.time.clock, a.time.window.meet b.time.window⟩, a.authority.meet b.authority,
      min a.tier b.tier, meetCut a b (a.time.window.meet b.time.window)⟩ := by
  by_cases hc : a.time.clock = b.time.clock
  · simp only [meet, hc, ↓reduceIte] at h
    obtain ⟨hs, rfl⟩ := build_ok.1 h
    exact ⟨hc, hs, by rw [hc]⟩
  · simp [meet, hc] at h

/-- **SCO-3** Monotone delegation: a meet that exists lies under both inputs, whatever atlas is
registered, since `Scope.meet` consults none. -/
theorem meet_le {a b m : Scope} (h : a.meet b = .ok m) : m.Le a ∧ m.Le b := by
  obtain ⟨hc, -, rfl⟩ := meet_ok h
  exact ⟨⟨inter_subset_left, inter_subset_left, ⟨rfl, Window.meet_le_left _ _⟩,
      Authority.meet_le_left _ _⟩,
    ⟨inter_subset_right, inter_subset_right, ⟨hc, Window.meet_le_right _ _⟩,
      Authority.meet_le_right _ _⟩⟩

/-- **SCO-3** A meet that exists is the greatest lower bound among scopes with well-formed windows.
-/
theorem le_meet {a b m x : Scope} (h : a.meet b = .ok m) (hx : x.time.window.WF) (ha : x.Le a)
    (hb : x.Le b) : x.Le m := by
  obtain ⟨-, -, rfl⟩ := meet_ok h
  exact ⟨subset_inter ha.1 hb.1, subset_inter ha.2.1 hb.2.1,
    ⟨ha.2.2.1.1, Window.le_meet hx ha.2.2.1.2 hb.2.2.1.2⟩, Authority.le_meet ha.2.2.2 hb.2.2.2⟩

/-- **SCO-3** Scopes on two clocks have no meet, atlas or not. -/
theorem meet_of_ne {a b : Scope} (h : a.time.clock ≠ b.time.clock) :
    a.meet b = .error .noCommonClock := by
  simp [meet, h]

/-- **SCO-5** A meet carries the lesser tier of its inputs. -/
theorem meet_tier {a b m : Scope} (h : a.meet b = .ok m) : m.tier = min a.tier b.tier := by
  obtain ⟨-, -, rfl⟩ := meet_ok h
  rfl

/-- What a join that exists returns. -/
theorem join_ok {a b j : Scope} (h : a.join b = .ok j) : a.time.clock = b.time.clock ∧
    j = ⟨a.sigma ∪ b.sigma, a.edges ∪ b.edges, ⟨a.time.clock, a.time.window.join b.time.window⟩,
      a.authority.join b.authority, min a.tier b.tier, if a.cut = b.cut then a.cut else none⟩ := by
  by_cases hc : a.time.clock = b.time.clock
  · simp only [join, hc, ↓reduceIte] at h
    obtain ⟨-, rfl⟩ := build_ok.1 h
    exact ⟨hc, by rw [hc]⟩
  · simp [join, hc] at h

/-- A join that exists is the least upper bound. -/
theorem join_le_iff {a b j x : Scope} (h : a.join b = .ok j) : j.Le x ↔ a.Le x ∧ b.Le x := by
  obtain ⟨hc, rfl⟩ := join_ok h
  constructor
  · rintro ⟨hσ, he, ⟨htc, htw⟩, hA⟩
    rw [Window.join_le_iff] at htw
    exact ⟨⟨subset_union_left.trans hσ, subset_union_left.trans he, ⟨htc, htw.1⟩,
        (Authority.le_join_left _ _).trans hA⟩,
      ⟨subset_union_right.trans hσ, subset_union_right.trans he, ⟨hc ▸ htc, htw.2⟩,
        (Authority.le_join_right _ _).trans hA⟩⟩
  · rintro ⟨⟨hσa, hea, ⟨hca, hwa⟩, hAa⟩, ⟨hσb, heb, ⟨-, hwb⟩, hAb⟩⟩
    exact ⟨union_subset hσa hσb, union_subset hea heb, ⟨hca, Window.join_le hwa hwb⟩,
      Authority.join_le hAa hAb⟩

/-- **SCO-5** So does a join. -/
theorem join_tier {a b j : Scope} (h : a.join b = .ok j) : j.tier = min a.tier b.tier := by
  obtain ⟨-, rfl⟩ := join_ok h
  rfl

end Scope

namespace Expr

/-- **SCO-5** No laundering: a composition that exists carries exactly the least tier among its
leaves. -/
theorem tier_eval (e : Expr) {s : Scope} (h : e.eval = .ok s) :
    (∀ l ∈ e.leaves, s.tier ≤ l.tier) ∧ ∃ l ∈ e.leaves, s.tier = l.tier := by
  induction e generalizing s with
  | leaf t =>
    simp only [eval, Except.ok.injEq] at h
    subst h
    simp [leaves]
  | meet e f ihe ihf | join e f ihe ihf =>
    simp only [eval] at h
    cases he : e.eval with
    | error _ => simp [he, Except.bind] at h
    | ok a =>
      cases hf : f.eval with
      | error _ => simp [he, hf, Except.bind] at h
      | ok b =>
        simp only [he, hf, Except.bind] at h
        first
          | rw [Scope.meet_tier h]
          | rw [Scope.join_tier h]
        obtain ⟨hae, la, hla, hla'⟩ := ihe he
        obtain ⟨hbf, lb, hlb, hlb'⟩ := ihf hf
        refine ⟨fun l hl ↦ ?_, ?_⟩
        · rcases List.mem_append.1 hl with hl | hl
          · exact (min_le_left _ _).trans (hae l hl)
          · exact (min_le_right _ _).trans (hbf l hl)
        · rcases le_total a.tier b.tier with hab | hab
          · exact ⟨la, List.mem_append_left _ hla, (min_eq_left hab).trans hla'⟩
          · exact ⟨lb, List.mem_append_right _ hlb, (min_eq_right hab).trans hlb'⟩

end Expr

/-! ## Firewalls and the zone law survive delegation -/

theorem admissible_of_subset {ιs : List (Finset Stratum)} {s t : Scope} (h : s.sigma ⊆ t.sigma)
    (ht : admissible ιs t) : admissible ιs s :=
  fun ι hι ↦ (ht ι hι).mono_left h

/-- **SCO-6** Admissibility survives every meet. -/
theorem admissible_meet {ιs : List (Finset Stratum)} {a b m : Scope} (h : a.meet b = .ok m)
    (ha : admissible ιs a) : admissible ιs m := by
  obtain ⟨-, -, rfl⟩ := Scope.meet_ok h
  exact admissible_of_subset inter_subset_left ha

theorem zoneOk_of_le {s t : Scope} (hσ : s.sigma ⊆ t.sigma)
    (hw : s.authority.world ≤ t.authority.world) (ht : zoneOk t) : zoneOk s := by
  rcases ht with ht | ht
  · exact Or.inl (ht.mono_left hσ)
  · exact Or.inr (le_antisymm (ht ▸ hw) (Fin.zero_le _))

/-- **SCO-6** So does the zone law. -/
theorem zoneOk_meet {a b m : Scope} (h : a.meet b = .ok m) (ha : zoneOk a) : zoneOk m := by
  obtain ⟨-, -, rfl⟩ := Scope.meet_ok h
  exact zoneOk_of_le inter_subset_left (min_le_left _ _) ha

/-- A zone-admissible scope with world reach names only strata outside the private set: `world`,
the denylist and the overlay. -/
theorem sigma_of_world_reach {s : Scope} (hz : zoneOk s) (hw : s.authority.world ≠ 0) :
    s.sigma ⊆ {.world, .foundation, .hypothetical} := by
  rcases hz with hz | hz
  · intro x hx
    have hx' := disjoint_left.1 hz hx
    rw [privateStrata_eq] at hx'
    simp only [mem_sdiff, mem_univ, true_and, not_not] at hx'
    exact hx'
  · exact absurd hz hw

/-- `STRATUM_CLASSES` gives those three strata no class. -/
theorem stratumClasses_outside :
    stratumClasses .world = ∅ ∧ stratumClasses .foundation = ∅ ∧
      stratumClasses .hypothetical = ∅ := by decide

/-- **SCO-6** So under any table that gives `world`, the denylist and the overlay no class,
`STRATUM_CLASSES` among them, a world-reaching scope the zone law admits is cleared for no class.
Naming `exhaust` no longer escapes this, whatever classes `exhaust` is given. -/
theorem world_reach_reads_nothing (tbl : Stratum → Finset Prov)
    (htbl : tbl .world = ∅ ∧ tbl .foundation = ∅ ∧ tbl .hypothetical = ∅) {s : Scope}
    (hz : zoneOk s) (hw : s.authority.world ≠ 0) : classesOf tbl s.sigma = ∅ := by
  refine eq_empty_of_forall_notMem fun c hc ↦ ?_
  obtain ⟨x, hx, hcx⟩ := mem_biUnion.1 hc
  have hx' := sigma_of_world_reach hz hw hx
  simp only [mem_insert, mem_singleton] at hx'
  rcases hx' with rfl | rfl | rfl
  · simp [htbl.1] at hcx
  · simp [htbl.2.1] at hcx
  · simp [htbl.2.2] at hcx

/-! ## The query engine -/

theorem mem_grantMeet {g h : List Scope} {m : Scope} (hm : m ∈ grantMeet g h) :
    ∃ a ∈ g, ∃ b ∈ h, a.meet b = .ok m := by
  obtain ⟨r, hr, hrm⟩ := List.mem_filterMap.1 hm
  obtain ⟨a, ha, hr⟩ := List.mem_flatMap.1 hr
  obtain ⟨b, hb, rfl⟩ := List.mem_map.1 hr
  refine ⟨a, ha, b, hb, ?_⟩
  split at hrm
  · simp_all
  · simp at hrm

/-- **SCO-7** A grant's meet lies under both grants, plane by plane. -/
theorem grantMeet_le {g h : List Scope} {m : Scope} (hm : m ∈ grantMeet g h) :
    (∃ a ∈ g, m.Le a) ∧ ∃ b ∈ h, m.Le b := by
  obtain ⟨a, ha, b, hb, hab⟩ := mem_grantMeet hm
  exact ⟨⟨a, ha, (Scope.meet_le hab).1⟩, b, hb, (Scope.meet_le hab).2⟩

/-- **SCO-7** So `InadmissibleGrant` never fires on the meet of a grant. -/
theorem grantMeet_grantOk {g h : List Scope} (hg : GrantOk g) : GrantOk (grantMeet g h) := by
  intro m hm
  obtain ⟨a, ha, b, -, hab⟩ := mem_grantMeet hm
  exact ⟨admissible_meet hab (hg a ha).1, zoneOk_meet hab (hg a ha).2⟩

/-- **SCO-7** And whatever the meet of two grants admits, each grant admits. -/
theorem admits_of_grantMeet {g h : List Scope} {r : Scope} (hr : admits (grantMeet g h) r) :
    admits g r ∧ admits h r := by
  obtain ⟨m, hm, hrm⟩ := hr
  obtain ⟨⟨a, ha, hma⟩, b, hb, hmb⟩ := grantMeet_le hm
  exact ⟨⟨a, ha, hrm.trans hma⟩, b, hb, hrm.trans hmb⟩

/-- **SCO-8** A search never raises `SliceError`, over any strata, with or without history: the
single-read cut is set exactly when the closed strata number more than one. -/
theorem search_never_slices (strata : List Stratum) (history authored : Bool) :
    isSlice (required .search strata history authored) = false := by
  simp only [required, mkScope, Scope.build, Scope.Slices]
  split_ifs <;> simp_all [isSlice]

/-- **SCO-8** In particular the Ambassador's search over `reference` alone builds, carries the cut,
and the Ambassador's grant admits it. -/
theorem search_reference (authored : Bool) :
    let r : Scope :=
      ⟨close {.reference}, ∅, ⟨.projectionEvent, .point anchor⟩, ⟨0, 0, 0⟩, 1, some singleRead⟩
    required .search [.reference] false authored = .ok r ∧ admits ambassador r := by
  revert authored
  decide

/-- With history it builds too, and is admitted. -/
theorem search_reference_history (authored : Bool) :
    let r : Scope :=
      ⟨close {.reference}, {.D}, ⟨.projectionEvent, .all⟩, ⟨0, 0, 0⟩, 1, some singleRead⟩
    required .search [.reference] true authored = .ok r ∧ admits ambassador r := by
  revert authored
  decide

/-! ## Roles and conformance -/

/-- Every role is zone-admissible by construction, at any strata and any executor reach. -/
theorem roles_zoneOk (S : Finset Stratum) (s : Stratum) (hyp : Bool) (r : Fin 4) :
    zoneOk (sensor s) ∧ zoneOk (query S) ∧ zoneOk (dreamer S) ∧ zoneOk (internalActor S hyp) ∧
      zoneOk (externalProposer S) ∧ zoneOk (externalExecutor r) :=
  ⟨Or.inr rfl, Or.inr rfl, Or.inr rfl, Or.inr rfl, Or.inr rfl, Or.inl (disjoint_empty_left _)⟩

theorem Conforms.mono {s t : Scope} {hs : List Handle} (h : Conforms s hs) (hσ : s.sigma ⊆ t.sigma)
    (hw : s.authority.storeWrite ≤ t.authority.storeWrite) (he : s.edges ⊆ t.edges) :
    Conforms t hs := fun x hx ↦
  ⟨hσ (h x hx).1, fun hw' ↦ ((h x hx).2.1 hw').trans hw, fun f hf ↦ he ((h x hx).2.2 f hf)⟩

/-- An agent that conforms to its delegated scope conforms to the parent's. -/
theorem Conforms.of_meet {a b m : Scope} {hs : List Handle} (h : a.meet b = .ok m)
    (hc : Conforms m hs) : Conforms a hs :=
  have hle := (Scope.meet_le h).1
  hc.mono hle.1 hle.2.2.2.2.1 hle.2.1

/-! ## Clearances -/

theorem classesOf_mono (tbl : Stratum → Finset Prov) {S T : Finset Stratum} (h : S ⊆ T) :
    classesOf tbl S ⊆ classesOf tbl T :=
  biUnion_subset_biUnion_of_subset_left _ h

theorem classesOf_union (tbl : Stratum → Finset Prov) (S T : Finset Stratum) :
    classesOf tbl (S ∪ T) = classesOf tbl S ∪ classesOf tbl T :=
  union_biUnion

/-- A delegated scope's clearance lies within both parents' clearances. -/
theorem classesOf_meet {a b m : Scope} (h : a.meet b = .ok m) :
    classesOf stratumClasses m.sigma ⊆
      classesOf stratumClasses a.sigma ∩ classesOf stratumClasses b.sigma :=
  subset_inter (classesOf_mono _ (Scope.meet_le h).1.1) (classesOf_mono _ (Scope.meet_le h).2.1)

/-! ## Witnesses: what the model found, and what the fixes changed -/

namespace Witness

open Window

/-- **SCO-2** `pt(1)` and `[1,1]` lie below each other, yet differ: `⊑` on windows is a preorder. -/
theorem window_not_antisymm :
    (point (.int 1)).Le (interval (.int 1) (.int 1)) ∧
      (interval (.int 1) (.int 1)).Le (point (.int 1)) ∧
      point (.int 1) ≠ interval (.int 1) (.int 1) := by decide

/-- Absorption fails on the nose: `[1,1] ⊓ ([1,1] ⊔ pt(5)) = pt(1)`. -/
theorem absorption_fails :
    (interval (.int 1) (.int 1)).meet ((interval (.int 1) (.int 1)).join (point (.int 5))) =
      point (.int 1) := by decide

/-- The inverted interval `[6,2]` lies under `[0,3]` and `[5,10]`, but not under their meet `⊥`;
the window constructor now refuses it. -/
theorem meet_not_glb :
    (interval (.int 6) (.int 2)).Le (interval (.int 0) (.int 3)) ∧
      (interval (.int 6) (.int 2)).Le (interval (.int 5) (.int 10)) ∧
      ¬ (interval (.int 6) (.int 2)).Le
        ((interval (.int 0) (.int 3)).meet (interval (.int 5) (.int 10))) ∧
      ¬ (interval (.int 6) (.int 2)).Valid := by decide

/-- **SCO-3** Both are valid and share a clock, yet have no meet: the windows meet at the point `5`,
over two strata, with no cut. `Grant.meet` now skips the pair. -/
theorem meet_slices : sliceA.Valid ∧ sliceB.Valid ∧ sliceA.meet sliceB = .error .slice ∧
    grantMeet [sliceA] [sliceB] = [] := by decide

/-- **SCO-3** Their meet keeps the point and so the owner's cut; it used to drop the cut and slice.
-/
theorem meet_keeps_one_sided_cut :
    pointGrant.meet ledgerTemplate = .ok pointGrant ∧ pointGrant.Valid := by decide

/-- **SCO-6** `Grant` refuses it now, like the same grant over its sibling `dialogue_transcript`;
with `PRIVATE_STRATA` derived from `top()`, which omits `exhaust`, it was accepted. -/
theorem exhaust_refused : ¬ GrantOk [exhaustReach] ∧
    ¬ GrantOk [⟨close {.dialogueTranscript}, ∅, ⟨.Ns, .all⟩, ⟨0, 0, 3⟩, 1, none⟩] := by decide

/-- **SCO-6** The zone law does not survive join. -/
theorem zone_join_fails : zoneOk worldOnly ∧ zoneOk mirrorRead ∧
    worldOnly.join mirrorRead =
      .ok ⟨{.world, .mirrorAuthored}, ∅, ⟨.N, .all⟩, ⟨0, 0, 1⟩, 1, none⟩ ∧
    ¬ zoneOk ⟨{.world, .mirrorAuthored}, ∅, ⟨.N, .all⟩, ⟨0, 0, 1⟩, 1, none⟩ := by decide

/-- A delegated clearance can be strictly narrower than the meet of the parents' clearances:
`observed` and `dialogue` share no stratum, yet both carry observed rows. -/
theorem classesOf_meet_strict :
    classesOf stratumClasses ({.observed} ∩ {.dialogue}) = ∅ ∧
      classesOf stratumClasses {.observed} ∩ classesOf stratumClasses {.dialogue} =
        {.observed} := by
  decide

/-- **SCO-4** Under the atlas the time meet completes on `N`, under neither input; delegation
refuses the pair. It used to complete it and mint a child under neither parent. -/
theorem atlas_delegation :
    commitParent.time.meetVia (some anAtlas) nsTemplate.time =
        some (Time.pullbackMeet anAtlas commitParent.time nsTemplate.time) ∧
      ¬ (Time.pullbackMeet anAtlas commitParent.time nsTemplate.time).Le commitParent.time ∧
      ¬ (Time.pullbackMeet anAtlas commitParent.time nsTemplate.time).Le nsTemplate.time ∧
      commitParent.meet nsTemplate = .error .noCommonClock := by decide

end Witness

end Palace.CQ
