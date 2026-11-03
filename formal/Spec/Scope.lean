module

public import Palace.Scope.Defs

/-!
# The capability-scope algebra (CQ-scope), the statements

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

These are the laws of `Palace/Scope.lean` as the ledger cites them, each with its proof
left as `sorry`. `lake comparator` checks that the `Palace` library proves each one
exactly as stated here, from the standard axioms alone.
-/

@[expose] public section

open Finset

namespace Palace.CQ

/-! ## Σ: closure is a closure operator; `top` is not the top -/

section Sigma

/-- **SCO-1** `close S` is closed: the forest is one level deep. -/
theorem close_isDown (S : Finset Stratum) : IsDown (close S) :=
  sorry

/-- **SCO-1** Closure is idempotent. -/
theorem close_close (S : Finset Stratum) : close (close S) = close S :=
  sorry

/-- **SCO-1** Closed sets are closed under intersection. -/
theorem IsDown.inter {S T : Finset Stratum} (hS : IsDown S) (hT : IsDown T) : IsDown (S ∩ T) :=
  sorry

/-- **SCO-1** And under union. -/
theorem IsDown.union {S T : Finset Stratum} (hS : IsDown S) (hT : IsDown T) : IsDown (S ∪ T) :=
  sorry

/-- **SCO-1** `top()` omits `exhaust` and `hypothetical`, not only the denylist. -/
theorem top_eq : top = univ \ {.foundation, .hypothetical, .exhaust} :=
  sorry

end Sigma

/-! ## Windows: a preorder, with join the least upper bound and meet the greatest lower bound
among well-formed windows -/

namespace Window

/-- **SCO-2** The join of two windows is their least upper bound. -/
theorem join_le_iff {a b x : Window} : (a.join b).Le x ↔ a.Le x ∧ b.Le x :=
  sorry

/-- **SCO-2** So on valid windows the meet is the exact greatest lower bound: the constructor
refuses the one counterexample, an inverted interval. -/
theorem le_meet_iff_of_valid {x a b : Window} (hx : x.Valid) :
    x.Le (a.meet b) ↔ x.Le a ∧ x.Le b :=
  sorry

end Window

/-! ## Time scopes -/

namespace Time

/-- **SCO-4** Under an atlas, two covered clocks meet through the event level. -/
theorem meetVia_atlas (A : Atlas) {a b : Time} (hab : a.clock ≠ b.clock)
    (ha : A.has a.clock = true) (hb : A.has b.clock = true) :
    a.meetVia (some A) b = some (pullbackMeet A a b) :=
  sorry

/-- **SCO-4** The completion lies on `N`, so under neither input on another clock: why delegation,
which must stay under the parent, refuses it. -/
theorem pullbackMeet_not_le (A : Atlas) {a b : Time} (haN : a.clock ≠ .N) (hbN : b.clock ≠ .N) :
    ¬ (pullbackMeet A a b).Le a ∧ ¬ (pullbackMeet A a b).Le b :=
  sorry

end Time

/-! ## Scopes: delegation, its partiality, and the tier -/

namespace Scope

/-- **SCO-3** Monotone delegation: a meet that exists lies under both inputs, whatever atlas is
registered, since `Scope.meet` consults none. -/
theorem meet_le {a b m : Scope} (h : a.meet b = .ok m) : m.Le a ∧ m.Le b :=
  sorry

/-- **SCO-3** A meet that exists is the greatest lower bound among scopes with well-formed windows.
-/
theorem le_meet {a b m x : Scope} (h : a.meet b = .ok m) (hx : x.time.window.WF) (ha : x.Le a)
    (hb : x.Le b) : x.Le m :=
  sorry

/-- **SCO-3** Scopes on two clocks have no meet, atlas or not. -/
theorem meet_of_ne {a b : Scope} (h : a.time.clock ≠ b.time.clock) :
    a.meet b = .error .noCommonClock :=
  sorry

/-- **SCO-5** A meet carries the lesser tier of its inputs. -/
theorem meet_tier {a b m : Scope} (h : a.meet b = .ok m) : m.tier = min a.tier b.tier :=
  sorry

/-- **SCO-5** So does a join. -/
theorem join_tier {a b j : Scope} (h : a.join b = .ok j) : j.tier = min a.tier b.tier :=
  sorry

end Scope

namespace Expr

/-- **SCO-5** No laundering: a composition that exists carries exactly the least tier among its
leaves. -/
theorem tier_eval (e : Expr) {s : Scope} (h : e.eval = .ok s) :
    (∀ l ∈ e.leaves, s.tier ≤ l.tier) ∧ ∃ l ∈ e.leaves, s.tier = l.tier :=
  sorry

end Expr

/-! ## Firewalls and the zone law survive delegation -/

/-- **SCO-6** Admissibility survives every meet. -/
theorem admissible_meet {ιs : List (Finset Stratum)} {a b m : Scope} (h : a.meet b = .ok m)
    (ha : admissible ιs a) : admissible ιs m :=
  sorry

/-- **SCO-6** So does the zone law. -/
theorem zoneOk_meet {a b m : Scope} (h : a.meet b = .ok m) (ha : zoneOk a) : zoneOk m :=
  sorry

/-- **SCO-6** So under any table that gives `world`, the denylist and the overlay no class,
`STRATUM_CLASSES` among them, a world-reaching scope the zone law admits is cleared for no class.
Naming `exhaust` no longer escapes this, whatever classes `exhaust` is given. -/
theorem world_reach_reads_nothing (tbl : Stratum → Finset Prov)
    (htbl : tbl .world = ∅ ∧ tbl .foundation = ∅ ∧ tbl .hypothetical = ∅) {s : Scope}
    (hz : zoneOk s) (hw : s.authority.world ≠ 0) : classesOf tbl s.sigma = ∅ :=
  sorry

/-! ## The query engine -/

/-- **SCO-7** A grant's meet lies under both grants, plane by plane. -/
theorem grantMeet_le {g h : List Scope} {m : Scope} (hm : m ∈ grantMeet g h) :
    (∃ a ∈ g, m.Le a) ∧ ∃ b ∈ h, m.Le b :=
  sorry

/-- **SCO-7** So `InadmissibleGrant` never fires on the meet of a grant. -/
theorem grantMeet_grantOk {g h : List Scope} (hg : GrantOk g) : GrantOk (grantMeet g h) :=
  sorry

/-- **SCO-7** And whatever the meet of two grants admits, each grant admits. -/
theorem admits_of_grantMeet {g h : List Scope} {r : Scope} (hr : admits (grantMeet g h) r) :
    admits g r ∧ admits h r :=
  sorry

/-- **SCO-8** A search never raises `SliceError`, over any strata, with or without history: the
single-read cut is set exactly when the closed strata number more than one. -/
theorem search_never_slices (strata : List Stratum) (history authored : Bool) :
    isSlice (required .search strata history authored) = false :=
  sorry

/-- **SCO-8** In particular the Ambassador's search over `reference` alone builds, carries the cut,
and the Ambassador's grant admits it. -/
theorem search_reference (authored : Bool) :
    let r : Scope :=
      ⟨close {.reference}, ∅, ⟨.projectionEvent, .point anchor⟩, ⟨0, 0, 0⟩, 1, some singleRead⟩
    required .search [.reference] false authored = .ok r ∧ admits ambassador r :=
  sorry

/-! ## Witnesses: what the model found, and what the fixes changed -/

namespace Witness

open Window

/-- **SCO-2** `pt(1)` and `[1,1]` lie below each other, yet differ: `⊑` on windows is a preorder. -/
theorem window_not_antisymm :
    (point (.int 1)).Le (interval (.int 1) (.int 1)) ∧
      (interval (.int 1) (.int 1)).Le (point (.int 1)) ∧
      point (.int 1) ≠ interval (.int 1) (.int 1) :=
  sorry

/-- **SCO-3** Both are valid and share a clock, yet have no meet: the windows meet at the point `5`,
over two strata, with no cut. `Grant.meet` now skips the pair. -/
theorem meet_slices : sliceA.Valid ∧ sliceB.Valid ∧ sliceA.meet sliceB = .error .slice ∧
    grantMeet [sliceA] [sliceB] = [] :=
  sorry

/-- **SCO-3** Their meet keeps the point and so the owner's cut; it used to drop the cut and slice.
-/
theorem meet_keeps_one_sided_cut :
    pointGrant.meet ledgerTemplate = .ok pointGrant ∧ pointGrant.Valid :=
  sorry

/-- **SCO-6** `Grant` refuses it now, like the same grant over its sibling `dialogue_transcript`;
with `PRIVATE_STRATA` derived from `top()`, which omits `exhaust`, it was accepted. -/
theorem exhaust_refused : ¬ GrantOk [exhaustReach] ∧
    ¬ GrantOk [⟨close {.dialogueTranscript}, ∅, ⟨.Ns, .all⟩, ⟨0, 0, 3⟩, 1, none⟩] :=
  sorry

/-- **SCO-6** The zone law does not survive join. -/
theorem zone_join_fails : zoneOk worldOnly ∧ zoneOk mirrorRead ∧
    worldOnly.join mirrorRead =
      .ok ⟨{.world, .mirrorAuthored}, ∅, ⟨.N, .all⟩, ⟨0, 0, 1⟩, 1, none⟩ ∧
    ¬ zoneOk ⟨{.world, .mirrorAuthored}, ∅, ⟨.N, .all⟩, ⟨0, 0, 1⟩, 1, none⟩ :=
  sorry

/-- **SCO-4** Under the atlas the time meet completes on `N`, under neither input; delegation
refuses the pair. It used to complete it and mint a child under neither parent. -/
theorem atlas_delegation :
    commitParent.time.meetVia (some anAtlas) nsTemplate.time =
        some (Time.pullbackMeet anAtlas commitParent.time nsTemplate.time) ∧
      ¬ (Time.pullbackMeet anAtlas commitParent.time nsTemplate.time).Le commitParent.time ∧
      ¬ (Time.pullbackMeet anAtlas commitParent.time nsTemplate.time).Le nsTemplate.time ∧
      commitParent.meet nsTemplate = .error .noCommonClock :=
  sorry

end Witness

end Palace.CQ
