import Mathlib.Data.Finset.Card
import Mathlib.Data.Finset.Union
import Mathlib.Data.Fintype.Basic
import Mathlib.Order.Basic
import Palace.Attack

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

What the model shows:

* Σ and E meet and join by `∩` and `∪`, and A by the minimum and maximum on each chain. Closure
  under refinement is a closure operator whose closed sets are closed under both. `top()` is not
  their top: it omits `exhaust` and `hypothetical` as well as the denylist (`top_eq`).
* Windows are ordered by a preorder, not a partial order: `pt(1)` and `[1,1]` lie below each other.
  Join is the least upper bound of any two windows. Meet is a lower bound of any two, and the
  greatest one among well-formed windows only: an inverted interval lies under two disjoint
  windows but not under their meet. Absorption holds up to the preorder, not on the nose.
* Without an atlas, a scope meet that exists is the greatest lower bound, so delegation is
  monotone and the tier of any composition is the least tier among its inputs. The meet is partial
  for a second reason the note does not name: the result must pass the SLICE rule, and two valid
  scopes on one clock can meet to a multi-stratum point window without a cut (`meet_slices`).
* With a clock atlas registered (GC-4), a cross-clock meet always exists and lands on clock `N`.
  Since `⊑` is false across clocks, the delegated scope lies under neither input, for every atlas
  (`atlas_breaks_delegation`).
* Admissibility and the zone law (private reads ⊥ world reach) are downward closed and survive
  every meet, atlas or not; the zone law does not survive join. Its private set omits `exhaust`,
  the agent-side dialogue rows, so a grant reading them with world reach is admitted
  (`exhaust_zone_gap`). Today no record is readable under it, because `STRATUM_CLASSES` gives
  `exhaust` no class (`world_reach_reads_nothing`); a class for `exhaust` would open the gap.
* The Ambassador's `search` over the single stratum `reference` raises `SliceError`: its scope
  counts two strata after closure, but `required` decides the cut from the names before closure
  (`search_slices_iff`).

The model is exact. Window bounds are ints or opaque tokens compared by equality (Python's
`1.0 == 1` is outside it); edge fibers are the three letters every caller uses; the cut is an
opaque token. The transcription agrees with the Python on an enumeration of 234,321 results:
window and scope meets, joins and orders, constructions under the SLICE rule, the zone law, and
`required()` over the Ambassador's strata names (`formal/README.md`).
-/

open Finset

namespace Palace.CQ

/-! ## Σ: the stratum-refinement forest -/

/-- `Stratum`: the base strata, the refinement predicates below them, the `hypothetical` overlay
and the denylist `foundation`. -/
inductive Stratum
  | mirror | mirrorAuthored | curated | observed | ops | reference | referenceRepo | interpreted
  | world | dialogue | dialogueTranscript | dialogueArtifact | exhaust | hypothetical | foundation
  deriving DecidableEq, Repr

instance : Fintype Stratum :=
  Fintype.ofList (open Stratum in [mirror, mirrorAuthored, curated, observed, ops, reference,
    referenceRepo, interpreted, world, dialogue, dialogueTranscript, dialogueArtifact, exhaust,
    hypothetical, foundation])
    fun x ↦ by cases x <;> simp

namespace Stratum

/-- `_REFINES`: the stratum a refinement predicate sits below. -/
def parent : Stratum → Option Stratum
  | mirrorAuthored => some mirror
  | referenceRepo => some reference
  | dialogueTranscript | dialogueArtifact | exhaust => some dialogue
  | _ => none

/-- The forest is one level deep: no refinement refines a refinement. -/
theorem parent_parent : ∀ c p : Stratum, c.parent = some p → p.parent = none := by decide

/-- The strata in declaration order, for attacks. -/
def nth : ℕ → Stratum
  | 0 => mirror | 1 => mirrorAuthored | 2 => curated | 3 => observed | 4 => ops | 5 => reference
  | 6 => referenceRepo | 7 => interpreted | 8 => world | 9 => dialogue | 10 => dialogueTranscript
  | 11 => dialogueArtifact | 12 => exhaust | 13 => hypothetical | _ => foundation

end Stratum

/-- `_BASE_STRATA`: the roots of the forest, less the denylist and the overlay. -/
def base : Finset Stratum :=
  univ.filter fun s ↦ s.parent = none ∧ s ≠ .foundation ∧ s ≠ .hypothetical

/-- `_downward_close`: the named strata, and the refinements below each one except `exhaust`,
which enters a set only when named. -/
def close (S : Finset Stratum) : Finset Stratum :=
  S ∪ univ.filter fun c ↦ c ≠ .exhaust ∧ ∃ p ∈ S, c.parent = some p

/-- `StratumScope.top()`, documented as `R ∖ 𝔇`. -/
def top : Finset Stratum := close base

/-- Closed under refinement: every refinement below a member is a member, `exhaust` aside. -/
def IsDown (S : Finset Stratum) : Prop :=
  ∀ c p : Stratum, c ≠ .exhaust → c.parent = some p → p ∈ S → c ∈ S

instance (S : Finset Stratum) : Decidable (IsDown S) := by unfold IsDown; infer_instance

/-! ## E: the edge fibers -/

/-- The edge fibers: citation `F`, supersession `D`, causal-witnessed `C`. `EdgeScope` holds any
strings; its constructors and every caller use these three. -/
inductive Fiber
  | F | D | C
  deriving DecidableEq, Repr

instance : Fintype Fiber :=
  Fintype.ofList (open Fiber in [F, D, C])
    fun x ↦ by cases x <;> simp

/-! ## T: clocks and windows -/

/-- `Clock`: `N` is the global event clock, parked. -/
inductive Clock
  | N | Ns | commit | distinctSnapshot | projectionEvent | lastWrite | wall | now
  deriving DecidableEq, Repr

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

/-- A window bound: none, an int, or an opaque token (a commit SHA, an event set), compared only
by equality. -/
inductive Bound
  | none | int (z : ℤ) | tok (t : ℕ)
  deriving DecidableEq, Repr

/-- `WindowKind`. -/
inductive Kind
  | point | interval | all | empty
  deriving DecidableEq, Repr

/-- `Window`: a kind and two bounds. The constructors below build every window the code makes. -/
structure Window where
  kind : Kind
  lo : Bound
  hi : Bound
  deriving DecidableEq, Repr

namespace Window

/-- `Window.point(a)`. -/
def point (a : Bound) : Window := ⟨.point, a, a⟩

/-- `Window.interval(a, b)`. -/
def interval (a b : Bound) : Window := ⟨.interval, a, b⟩

/-- `Window.all()`: `∗`. -/
def all : Window := ⟨.all, .none, .none⟩

/-- `Window.empty()`: `⊥`. -/
def empty : Window := ⟨.empty, .none, .none⟩

/-- Both bounds, when both are ints; `_orderable` holds of two windows that both have them. -/
def ints (w : Window) : Option (ℤ × ℤ) :=
  match w.lo, w.hi with
  | .int l, .int h => some (l, h)
  | _, _ => none

/-- The window the int branches build from `lo ≤ hi`: a point when the bounds agree. -/
def span (lo hi : ℤ) : Window := if lo = hi then point (.int lo) else interval (.int lo) (.int hi)

/-- `Window.meet`: `∗` is the identity and `⊥` absorbs; equal windows meet to themselves; int
windows intersect; other unequal windows meet to `⊥`. -/
def meet (a b : Window) : Window :=
  if a.kind = .empty ∨ b.kind = .empty then empty
  else if a.kind = .all then b
  else if b.kind = .all then a
  else if a = b then a
  else
    match a.ints, b.ints with
    | some (al, ah), some (bl, bh) =>
      if min ah bh < max al bl then empty else span (max al bl) (min ah bh)
    | _, _ => empty

/-- `Window.join`: `⊥` is the identity and `∗` absorbs; equal windows join to themselves; int
windows join to their hull; other unequal windows widen to `∗`. -/
def join (a b : Window) : Window :=
  if a.kind = .all ∨ b.kind = .all then all
  else if a.kind = .empty then b
  else if b.kind = .empty then a
  else if a = b then a
  else
    match a.ints, b.ints with
    | some (al, ah), some (bl, bh) => span (min al bl) (max ah bh)
    | _, _ => all

/-- Containment of int bounds: `a`'s lie within `b`'s. -/
def Within (a b : Window) : Prop :=
  match a.ints, b.ints with
  | some (al, ah), some (bl, bh) => bl ≤ al ∧ ah ≤ bh
  | _, _ => False

instance (a b : Window) : Decidable (Within a b) := by
  unfold Within; split <;> infer_instance

/-- `Window.__le__`. -/
def Le (a b : Window) : Prop :=
  a.kind = .empty ∨ b.kind = .all ∨ a = b ∨ (a.kind ≠ .all ∧ b.kind ≠ .empty ∧ Within a b)

instance (a b : Window) : Decidable (Le a b) := by unfold Le; infer_instance

/-- Well-formed: the int bounds of a window are not inverted. -/
def WF (w : Window) : Prop :=
  match w.ints with
  | some (l, h) => l ≤ h
  | none => True

instance (w : Window) : Decidable (WF w) := by unfold WF; split <;> infer_instance

end Window

/-- `TimeScope`. -/
structure Time where
  clock : Clock
  window : Window
  deriving DecidableEq, Repr

/-- A clock atlas (`ClockAtlas`): which clocks pull back to `N`, the pullback of a window as an
opaque token, and the meet of two tokens, `none` when empty. -/
structure Atlas where
  has : Clock → Bool
  pullback : Clock → Window → ℕ
  intersect : ℕ → ℕ → Option ℕ

namespace Time

/-- `TimeScope.meet` under the registered atlas, `none` when none is registered; a `none` result
is `NoCommonClockError`. -/
def meetVia (A : Option Atlas) (a b : Time) : Option Time :=
  if a.clock = b.clock then some ⟨a.clock, a.window.meet b.window⟩
  else
    match A with
    | some A =>
      if A.has a.clock ∧ A.has b.clock then
        some ⟨.N, match A.intersect (A.pullback a.clock a.window) (A.pullback b.clock b.window) with
          | none => .empty
          | some t => .interval (.tok t) (.tok t)⟩
      else none
    | none => none

/-- `TimeScope.__le__`: false across clocks. -/
def Le (a b : Time) : Prop := a.clock = b.clock ∧ a.window.Le b.window

instance (a b : Time) : Decidable (Le a b) := by unfold Le; infer_instance

end Time

/-! ## A: authority, and the tier -/

/-- `A = P × W_Σ × W_world`: privilege (`READ < READ_PROPOSE`), the projection-write bit, and world
reach (`NONE < SENSING < REVERSIBLE < IRREVERSIBLE`). `__post_init__`'s check that `W_Σ` is a bit is
the type `Fin 2`. -/
structure Authority where
  privilege : Fin 2
  storeWrite : Fin 2
  world : Fin 4
  deriving DecidableEq, Repr

namespace Authority

/-- `Authority.meet`: the minimum on each chain. -/
def meet (a b : Authority) : Authority :=
  ⟨min a.privilege b.privilege, min a.storeWrite b.storeWrite, min a.world b.world⟩

/-- `Authority.join`: the maximum on each chain. -/
def join (a b : Authority) : Authority :=
  ⟨max a.privilege b.privilege, max a.storeWrite b.storeWrite, max a.world b.world⟩

/-- `Authority.__le__`. -/
def Le (a b : Authority) : Prop :=
  a.privilege ≤ b.privilege ∧ a.storeWrite ≤ b.storeWrite ∧ a.world ≤ b.world

instance (a b : Authority) : Decidable (Le a b) := by unfold Le; infer_instance

end Authority

/-! ## The scope -/

/-- `Scope`: the four coordinates, the tier (`CONVENTION < STATIC_GUARD < STRUCTURAL`), and the
explicit cut, an opaque token. Tier and cut are outside `==` and `⊑`. -/
structure Scope where
  sigma : Finset Stratum
  edges : Finset Fiber
  time : Time
  authority : Authority
  tier : Fin 3
  cut : Option ℕ
  deriving DecidableEq

/-- What a scope operation raises: `NoCommonClockError` or `SliceError`. -/
inductive Err
  | noCommonClock | slice
  deriving DecidableEq, Repr

namespace Scope

/-- The SLICE rule of `__post_init__` fires: a multi-stratum point window, on a clock that is not a
cut clock, without a cut. -/
def Slices (s : Scope) : Prop :=
  1 < s.sigma.card ∧ s.time.window.kind = .point ∧ s.time.clock ≠ .commit ∧ s.cut = none

instance (s : Scope) : Decidable (Slices s) := by unfold Slices; infer_instance

/-- A scope the code can construct. -/
def Valid (s : Scope) : Prop := ¬ s.Slices

instance (s : Scope) : Decidable (Valid s) := by unfold Valid; infer_instance

/-- The constructor: `SliceError` when the SLICE rule fires. -/
def build (s : Scope) : Except Err Scope := if s.Slices then .error .slice else .ok s

/-- `Scope.meet` under the registered atlas: componentwise meets, the least tier, and the cut the
two share. -/
def meetVia (A : Option Atlas) (a b : Scope) : Except Err Scope :=
  match a.time.meetVia A b.time with
  | none => .error .noCommonClock
  | some t =>
    build ⟨a.sigma ∩ b.sigma, a.edges ∩ b.edges, t, a.authority.meet b.authority,
      min a.tier b.tier, if a.cut = b.cut then a.cut else none⟩

/-- `Scope.meet` with no atlas registered, the default. -/
def meet (a b : Scope) : Except Err Scope := meetVia none a b

/-- `Scope.join`: componentwise joins on one clock; across clocks, `NoCommonClockError`. -/
def join (a b : Scope) : Except Err Scope :=
  if a.time.clock = b.time.clock then
    build ⟨a.sigma ∪ b.sigma, a.edges ∪ b.edges, ⟨a.time.clock, a.time.window.join b.time.window⟩,
      a.authority.join b.authority, min a.tier b.tier, if a.cut = b.cut then a.cut else none⟩
  else .error .noCommonClock

/-- `Scope.__le__`: the four coordinates only. -/
def Le (a b : Scope) : Prop :=
  a.sigma ⊆ b.sigma ∧ a.edges ⊆ b.edges ∧ a.time.Le b.time ∧ a.authority.Le b.authority

instance (a b : Scope) : Decidable (Le a b) := by unfold Le; infer_instance

end Scope

/-! ## Firewalls and the zone law -/

/-- `Ideal.excludes`: `s` names no stratum of the ideal. -/
def excludes (ι : Finset Stratum) (s : Scope) : Prop := Disjoint s.sigma ι

/-- `admissible`: every firewall ideal is excluded. -/
def admissible (ιs : List (Finset Stratum)) (s : Scope) : Prop := ∀ ι ∈ ιs, excludes ι s

/-- `DENYLIST_IDEAL`. -/
def denylist : Finset Stratum := {.foundation}

/-- `PRIVATE_STRATA`: the closure of every base stratum but `world`. -/
def privateStrata : Finset Stratum := close (base.erase .world)

/-- `zone_admissible`: a scope that reads a private stratum has no world reach. -/
def zoneOk (s : Scope) : Prop := Disjoint s.sigma privateStrata ∨ s.authority.world = 0

instance (s : Scope) : Decidable (zoneOk s) := by unfold zoneOk; infer_instance

/-! ## The query engine: grants and required scopes (`core/query.py`) -/

/-- `Grant.__post_init__` accepts a list of scopes: each one admissible and zone-admissible. -/
def GrantOk (g : List Scope) : Prop := ∀ s ∈ g, admissible [denylist] s ∧ zoneOk s

/-- `Grant.admits`: the required scope lies under one of the granted scopes. -/
def admits (g : List Scope) (r : Scope) : Prop := ∃ s ∈ g, r.Le s

instance (ιs : List (Finset Stratum)) (s : Scope) : Decidable (admissible ιs s) := by
  unfold admissible excludes; infer_instance

instance (g : List Scope) : Decidable (GrantOk g) := by unfold GrantOk; infer_instance

instance (g : List Scope) (r : Scope) : Decidable (admits g r) := by unfold admits; infer_instance

/-- Whether a result is a `SliceError`. -/
def isSlice : Except Err Scope → Bool
  | .error .slice => true
  | _ => false

/-- `Grant.meet`: the pairwise meets that exist, skipping cross-clock pairs. A `SliceError` is not
caught, so it escapes. -/
def grantMeet (g h : List Scope) : Except Err (List Scope) :=
  let rs := g.flatMap fun a ↦ h.map fun b ↦ a.meet b
  if rs.any isSlice then .error .slice
  else .ok (rs.filterMap fun r ↦ match r with
    | .ok m => some m
    | .error _ => none)

/-- The query verbs. -/
inductive Verb
  | search | reach | diffuse | hybrid | related | history | origin | capture
  deriving DecidableEq, Repr

/-- `ANCHOR`, the unbound point anchor, as a token; and the `"single-read"` cut. -/
def anchor : Bound := .tok 0

/-- The cut `"single-read"`. -/
def singleRead : ℕ := 0

/-- `core.query.scope(...)`, at tier `STATIC_GUARD`, with no world reach. -/
def mkScope (strata : List Stratum) (fibers : Finset Fiber) (clock : Clock) (w : Window)
    (propose write : Bool := false) (cut : Option ℕ := none) : Except Err Scope :=
  Scope.build ⟨close strata.toFinset, fibers, ⟨clock, w⟩,
    ⟨if propose then 1 else 0, if write then 1 else 0, 0⟩, 1, cut⟩

/-- `required(verb)`: the least scope a sentence needs. `search` decides its cut from the length of
the strata it is given, before closure. -/
def required (v : Verb) (strata : List Stratum) (history authored : Bool) : Except Err Scope :=
  match v with
  | .search =>
    mkScope strata (if history then {.D} else ∅) .projectionEvent
      (if history then .all else .point anchor)
      (cut := if 1 < strata.length then some singleRead else none)
  | .diffuse | .hybrid | .related => mkScope [.mirrorAuthored] {.F} .projectionEvent (.point anchor)
  | .reach => mkScope [.reference] {.F} .commit (.point anchor)
  | .history => mkScope [.mirrorAuthored] {.D} .Ns .all
  | .origin => mkScope [.reference, .dialogueTranscript] {.C} .commit (.point anchor)
  | .capture =>
    mkScope [if authored then .dialogueTranscript else .observed] ∅ .projectionEvent
      (.point anchor) (write := true)

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

/-- The Ambassador's grant `AMBASSADOR`: three planes, one per clock. -/
def ambassador : List Scope :=
  [⟨close {.mirror, .curated, .interpreted, .dialogue, .observed, .reference}, {.F, .D},
      ⟨.projectionEvent, .all⟩, ⟨1, 1, 0⟩, 1, none⟩,
    ⟨close {.reference, .dialogue}, {.F, .C}, ⟨.commit, .all⟩, ⟨1, 0, 0⟩, 1, none⟩,
    ⟨close {.mirror}, {.D}, ⟨.Ns, .all⟩, ⟨0, 0, 0⟩, 1, none⟩]

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
  stratum : Stratum
  writesStratum : Bool
  writesFiber : Option Fiber

/-- `assert_conforms` passes: every handle stays inside the declared scope. -/
def Conforms (s : Scope) (hs : List Handle) : Prop :=
  ∀ h ∈ hs, h.stratum ∈ s.sigma ∧ (h.writesStratum = true → 1 ≤ s.authority.storeWrite) ∧
    ∀ f, h.writesFiber = some f → f ∈ s.edges

/-! ## Clearances (`core/kernel/clearance.py`) -/

/-- `Provenance`: the record classes. -/
inductive Prov
  | authoredSolo | authoredDialogue | curated | interpreted | derivedStratum | observed | code
  deriving DecidableEq, Repr

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

/-- `classes_of`, and `clearance_of` on a scope's Σ, under a table of classes. -/
def classesOf (tbl : Stratum → Finset Prov) (S : Finset Stratum) : Finset Prov := S.biUnion tbl


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

/-- `close S` is closed: the forest is one level deep. -/
theorem close_isDown (S : Finset Stratum) : IsDown (close S) := by
  intro c p hx hcp hp
  rcases mem_close.1 hp with hp | ⟨_, q, _, hpq⟩
  · exact mem_close.2 (Or.inr ⟨hx, p, hp, hcp⟩)
  · simp [Stratum.parent_parent c p hcp] at hpq

theorem close_close (S : Finset Stratum) : close (close S) = close S :=
  isDown_iff.1 (close_isDown S)

/-- `close S` is the least closed set containing `S`. -/
theorem close_subset {S T : Finset Stratum} (hST : S ⊆ T) (hT : IsDown T) : close S ⊆ T :=
  (close_mono hST).trans (isDown_iff.1 hT).le

theorem IsDown.inter {S T : Finset Stratum} (hS : IsDown S) (hT : IsDown T) : IsDown (S ∩ T) :=
  fun c p hx hcp hp ↦
    mem_inter.2 ⟨hS c p hx hcp (mem_inter.1 hp).1, hT c p hx hcp (mem_inter.1 hp).2⟩

theorem IsDown.union {S T : Finset Stratum} (hS : IsDown S) (hT : IsDown T) : IsDown (S ∪ T) := by
  intro c p hx hcp hp
  rcases mem_union.1 hp with hp | hp
  · exact mem_union_left _ (hS c p hx hcp hp)
  · exact mem_union_right _ (hT c p hx hcp hp)

/-- `top()` omits `exhaust` and `hypothetical`, not only the denylist. -/
theorem top_eq : top = univ \ {.foundation, .hypothetical, .exhaust} := by decide

/-- So `top()` is not the top of the closed sets: a set naming `exhaust` or `hypothetical` lies
outside it. -/
theorem not_close_subset_top : ¬ close {.exhaust} ⊆ top ∧ ¬ close {.hypothetical} ⊆ top := by
  decide

/-- `PRIVATE_STRATA` is every stratum but `world`, the denylist, the overlay, and `exhaust`. -/
theorem privateStrata_eq :
    privateStrata = univ \ {.world, .foundation, .hypothetical, .exhaust} := by decide

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

/-- Under an atlas, two covered clocks meet on `N`. -/
theorem meetVia_atlas (A : Atlas) {a b : Time} (hab : a.clock ≠ b.clock) (ha : A.has a.clock = true)
    (hb : A.has b.clock = true) : ∃ t, a.meetVia (some A) b = some t ∧ t.clock = .N ∧
      t.window.kind ≠ .point := by
  refine ⟨⟨.N, match A.intersect (A.pullback a.clock a.window) (A.pullback b.clock b.window) with
    | none => .empty
    | some t => .interval (.tok t) (.tok t)⟩, ?_, rfl, ?_⟩
  · simp [meetVia, hab, ha, hb]
  · dsimp only
    split <;> simp [Window.empty, Window.interval]

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
theorem meetVia_ok {A : Option Atlas} {a b m : Scope} (h : a.meetVia A b = .ok m) :
    ∃ t, a.time.meetVia A b.time = some t ∧ ¬ m.Slices ∧
      m = ⟨a.sigma ∩ b.sigma, a.edges ∩ b.edges, t, a.authority.meet b.authority,
        min a.tier b.tier, if a.cut = b.cut then a.cut else none⟩ := by
  unfold meetVia at h
  split at h
  · simp at h
  · rename_i t ht
    obtain ⟨hs, rfl⟩ := build_ok.1 h
    exact ⟨t, ht, hs, rfl⟩

/-- Monotone delegation: a meet that exists lies under both inputs. -/
theorem meet_le {a b m : Scope} (h : a.meet b = .ok m) : m.Le a ∧ m.Le b := by
  obtain ⟨t, ht, -, rfl⟩ := meetVia_ok h
  obtain ⟨hta, htb⟩ := Time.meet_le ht
  exact ⟨⟨inter_subset_left, inter_subset_left, hta, Authority.meet_le_left _ _⟩,
    ⟨inter_subset_right, inter_subset_right, htb, Authority.meet_le_right _ _⟩⟩

/-- A meet that exists is the greatest lower bound among scopes with well-formed windows. -/
theorem le_meet {a b m x : Scope} (h : a.meet b = .ok m) (hx : x.time.window.WF) (ha : x.Le a)
    (hb : x.Le b) : x.Le m := by
  obtain ⟨t, ht, -, rfl⟩ := meetVia_ok h
  exact ⟨subset_inter ha.1 hb.1, subset_inter ha.2.1 hb.2.1, Time.le_meet ht hx ha.2.2.1 hb.2.2.1,
    Authority.le_meet ha.2.2.2 hb.2.2.2⟩

/-- Without an atlas, scopes on two clocks have no meet. -/
theorem meet_of_ne {a b : Scope} (h : a.time.clock ≠ b.time.clock) :
    a.meet b = .error .noCommonClock := by
  simp [meet, meetVia, Time.meetVia_none, h]

/-- With an atlas, scopes on two covered clocks always meet, on `N`; the SLICE rule never fires,
since the window is never a point. -/
theorem meetVia_atlas (A : Atlas) {a b : Scope} (hab : a.time.clock ≠ b.time.clock)
    (ha : A.has a.time.clock = true) (hb : A.has b.time.clock = true) :
    ∃ m, a.meetVia (some A) b = .ok m ∧ m.time.clock = .N := by
  obtain ⟨t, ht, htN, htp⟩ := Time.meetVia_atlas A hab ha hb
  refine ⟨⟨a.sigma ∩ b.sigma, a.edges ∩ b.edges, t, a.authority.meet b.authority,
    min a.tier b.tier, if a.cut = b.cut then a.cut else none⟩, ?_, htN⟩
  unfold meetVia
  rw [ht]
  exact build_ok.2 ⟨fun h ↦ htp h.2.1, rfl⟩

/-- So under any atlas, delegation across two covered clocks other than `N` is not monotone: the
delegated scope lies under neither input, because `⊑` is false across clocks. -/
theorem atlas_breaks_delegation (A : Atlas) {a b : Scope} (hab : a.time.clock ≠ b.time.clock)
    (ha : A.has a.time.clock = true) (hb : A.has b.time.clock = true) (haN : a.time.clock ≠ .N)
    (hbN : b.time.clock ≠ .N) : ∃ m, a.meetVia (some A) b = .ok m ∧ ¬ m.Le a ∧ ¬ m.Le b := by
  obtain ⟨m, hm, hmN⟩ := meetVia_atlas A hab ha hb
  exact ⟨m, hm, fun h ↦ haN (hmN ▸ h.2.2.1.1).symm, fun h ↦ hbN (hmN ▸ h.2.2.1.1).symm⟩

theorem meetVia_tier {A : Option Atlas} {a b m : Scope} (h : a.meetVia A b = .ok m) :
    m.tier = min a.tier b.tier := by
  obtain ⟨t, -, -, rfl⟩ := meetVia_ok h
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

theorem join_tier {a b j : Scope} (h : a.join b = .ok j) : j.tier = min a.tier b.tier := by
  obtain ⟨-, rfl⟩ := join_ok h
  rfl

end Scope

/-- A composition of scopes: leaves, meets and joins, as a dreamer's scope expression builds. -/
inductive Expr
  | leaf (s : Scope)
  | meet (e f : Expr)
  | join (e f : Expr)

namespace Expr

/-- Evaluate left to right, as Python does; the first error escapes. -/
def eval (A : Option Atlas) : Expr → Except Err Scope
  | leaf s => .ok s
  | meet e f => (e.eval A).bind fun a ↦ (f.eval A).bind fun b ↦ a.meetVia A b
  | join e f => (e.eval A).bind fun a ↦ (f.eval A).bind fun b ↦ a.join b

/-- The scopes an expression composes. -/
def leaves : Expr → List Scope
  | leaf s => [s]
  | meet e f | join e f => e.leaves ++ f.leaves

/-- No laundering: a composition that exists carries exactly the least tier among its leaves. -/
theorem tier_eval (A : Option Atlas) (e : Expr) {s : Scope} (h : e.eval A = .ok s) :
    (∀ l ∈ e.leaves, s.tier ≤ l.tier) ∧ ∃ l ∈ e.leaves, s.tier = l.tier := by
  induction e generalizing s with
  | leaf t =>
    simp only [eval, Except.ok.injEq] at h
    subst h
    simp [leaves]
  | meet e f ihe ihf | join e f ihe ihf =>
    simp only [eval] at h
    cases he : e.eval A with
    | error _ => simp [he, Except.bind] at h
    | ok a =>
      cases hf : f.eval A with
      | error _ => simp [he, hf, Except.bind] at h
      | ok b =>
        simp only [he, hf, Except.bind] at h
        first
          | rw [Scope.meetVia_tier h]
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

/-! ## Firewalls and the zone law survive delegation, atlas or not -/

theorem admissible_of_subset {ιs : List (Finset Stratum)} {s t : Scope} (h : s.sigma ⊆ t.sigma)
    (ht : admissible ιs t) : admissible ιs s :=
  fun ι hι ↦ (ht ι hι).mono_left h

theorem admissible_meetVia {A : Option Atlas} {ιs : List (Finset Stratum)} {a b m : Scope}
    (h : a.meetVia A b = .ok m) (ha : admissible ιs a) : admissible ιs m := by
  obtain ⟨t, -, -, rfl⟩ := Scope.meetVia_ok h
  exact admissible_of_subset inter_subset_left ha

theorem zoneOk_of_le {s t : Scope} (hσ : s.sigma ⊆ t.sigma)
    (hw : s.authority.world ≤ t.authority.world) (ht : zoneOk t) : zoneOk s := by
  rcases ht with ht | ht
  · exact Or.inl (ht.mono_left hσ)
  · exact Or.inr (le_antisymm (ht ▸ hw) (Fin.zero_le _))

theorem zoneOk_meetVia {A : Option Atlas} {a b m : Scope} (h : a.meetVia A b = .ok m)
    (ha : zoneOk a) : zoneOk m := by
  obtain ⟨t, -, -, rfl⟩ := Scope.meetVia_ok h
  exact zoneOk_of_le inter_subset_left (min_le_left _ _) ha

/-- Every stratum outside the private set names no class in `STRATUM_CLASSES`. -/
theorem stratumClasses_of_not_private :
    ∀ x : Stratum, x ∉ privateStrata → stratumClasses x = ∅ := by decide

/-- A zone-admissible scope with world reach is cleared for no class. -/
theorem world_reach_reads_nothing {s : Scope} (hz : zoneOk s) (hw : s.authority.world ≠ 0) :
    classesOf stratumClasses s.sigma = ∅ := by
  rcases hz with hz | hz
  · refine eq_empty_of_forall_notMem fun c hc ↦ ?_
    obtain ⟨x, hx, hcx⟩ := mem_biUnion.1 hc
    rw [stratumClasses_of_not_private x (disjoint_left.1 hz hx)] at hcx
    exact notMem_empty c hcx
  · exact absurd hz hw

/-! ## The query engine -/

theorem grantMeet_ok {g h out : List Scope} (hm : grantMeet g h = .ok out) :
    ∀ m ∈ out, ∃ a ∈ g, ∃ b ∈ h, a.meet b = .ok m := by
  dsimp only [grantMeet] at hm
  split_ifs at hm
  simp only [Except.ok.injEq] at hm
  subst hm
  intro m hm
  obtain ⟨r, hr, hrm⟩ := List.mem_filterMap.1 hm
  obtain ⟨a, ha, hr⟩ := List.mem_flatMap.1 hr
  obtain ⟨b, hb, rfl⟩ := List.mem_map.1 hr
  refine ⟨a, ha, b, hb, ?_⟩
  split at hrm
  · simp_all
  · simp at hrm

/-- A grant's meet that exists lies under both grants, plane by plane. -/
theorem grantMeet_le {g h out : List Scope} (hm : grantMeet g h = .ok out) :
    ∀ m ∈ out, (∃ a ∈ g, m.Le a) ∧ ∃ b ∈ h, m.Le b := by
  intro m hm'
  obtain ⟨a, ha, b, hb, hab⟩ := grantMeet_ok hm m hm'
  exact ⟨⟨a, ha, (Scope.meet_le hab).1⟩, b, hb, (Scope.meet_le hab).2⟩

/-- So `InadmissibleGrant` never fires on the meet of a grant. -/
theorem grantMeet_grantOk {g h out : List Scope} (hg : GrantOk g) (hm : grantMeet g h = .ok out) :
    GrantOk out := by
  intro m hm'
  obtain ⟨a, ha, b, -, hab⟩ := grantMeet_ok hm m hm'
  exact ⟨admissible_meetVia hab (hg a ha).1, zoneOk_meetVia hab (hg a ha).2⟩

/-- And whatever the meet of two grants admits, each grant admits. -/
theorem admits_of_grantMeet {g h out : List Scope} {r : Scope} (hm : grantMeet g h = .ok out)
    (hr : admits out r) : admits g r ∧ admits h r := by
  obtain ⟨m, hm', hrm⟩ := hr
  obtain ⟨⟨a, ha, hma⟩, b, hb, hmb⟩ := grantMeet_le hm m hm'
  exact ⟨⟨a, ha, hrm.trans hma⟩, b, hb, hrm.trans hmb⟩

/-- Of the strata the Ambassador's tools accept, a search without history raises `SliceError` for
exactly one choice: `reference` alone, whose closure holds two strata while `required` counts
one name. -/
theorem search_slices_iff (names : List Name) (authored : Bool) :
    isSlice (required .search (pick names) false authored) = true ↔ names = [.reference] := by
  rcases names with _ | ⟨n, _ | ⟨n', rest⟩⟩
  · revert authored
    decide
  · revert authored
    cases n <;> decide
  · have : 1 < (pick (n :: n' :: rest)).length := by simp [pick]
    simp [required, mkScope, Scope.build, Scope.Slices, isSlice, this]

/-- With history the same search builds, and the Ambassador's grant admits it. -/
theorem search_reference_history (authored : Bool) :
    let r : Scope := ⟨close {.reference}, {.D}, ⟨.projectionEvent, .all⟩, ⟨0, 0, 0⟩, 1, none⟩
    required .search [.reference] true authored = .ok r ∧ admits ambassador r := by
  revert authored
  decide

/-- A search over `reference` that carried the single-read cut would be admitted too. -/
theorem search_reference_with_cut :
    admits ambassador ⟨close {.reference}, ∅, ⟨.projectionEvent, .point anchor⟩, ⟨0, 0, 0⟩, 1,
      some singleRead⟩ := by decide

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


/-! ## Witnesses: the measured failures, reproduced by the model -/

namespace Witness

open Window

/-- `pt(1)` and `[1,1]` lie below each other, yet differ: `⊑` on windows is not antisymmetric. -/
theorem window_not_antisymm :
    (point (.int 1)).Le (interval (.int 1) (.int 1)) ∧
      (interval (.int 1) (.int 1)).Le (point (.int 1)) ∧
      point (.int 1) ≠ interval (.int 1) (.int 1) := by decide

/-- Absorption fails on the nose: `[1,1] ⊓ ([1,1] ⊔ pt(5)) = pt(1)`. -/
theorem absorption_fails :
    (interval (.int 1) (.int 1)).meet ((interval (.int 1) (.int 1)).join (point (.int 5))) =
      point (.int 1) := by decide

/-- The inverted interval `[6,2]` lies under `[0,3]` and `[5,10]`, but not under their meet `⊥`. -/
theorem meet_not_glb :
    (interval (.int 6) (.int 2)).Le (interval (.int 0) (.int 3)) ∧
      (interval (.int 6) (.int 2)).Le (interval (.int 5) (.int 10)) ∧
      ¬ (interval (.int 6) (.int 2)).Le
        ((interval (.int 0) (.int 3)).meet (interval (.int 5) (.int 10))) := by decide

/-- A read of two strata on `N_s` over `[1,5]`, with no cut. -/
def sliceA : Scope :=
  ⟨{.mirrorAuthored, .curated}, ∅, ⟨.Ns, .interval (.int 1) (.int 5)⟩, ⟨0, 0, 0⟩, 1, none⟩

/-- The same over `[5,9]`. -/
def sliceB : Scope :=
  ⟨{.mirrorAuthored, .curated}, ∅, ⟨.Ns, .interval (.int 5) (.int 9)⟩, ⟨0, 0, 0⟩, 1, none⟩

/-- Both are valid and share a clock, yet their meet raises `SliceError`: the windows meet at the
point `5`, over two strata, with no cut. `Grant.meet` does not catch it. -/
theorem meet_slices : sliceA.Valid ∧ sliceB.Valid ∧ sliceA.meet sliceB = .error .slice ∧
    grantMeet [sliceA] [sliceB] = .error .slice := by decide

/-- A grant that reads only agent exhaust, with irreversible world reach. -/
def exhaustReach : Scope := ⟨close {.exhaust}, ∅, ⟨.Ns, .all⟩, ⟨0, 0, 3⟩, 1, none⟩

/-- `Grant` accepts it, because `exhaust` is outside the private set; the same grant over its
sibling `dialogue_transcript` is refused. -/
theorem exhaust_zone_gap : GrantOk [exhaustReach] ∧
    ¬ GrantOk [⟨close {.dialogueTranscript}, ∅, ⟨.Ns, .all⟩, ⟨0, 0, 3⟩, 1, none⟩] := by decide

/-- Give `exhaust` its parent's classes, and the same grant is cleared for private records. -/
theorem exhaust_gap_opens :
    classesOf (fun s ↦ if s = .exhaust then stratumClasses .dialogue else stratumClasses s)
      exhaustReach.sigma = {.observed, .authoredDialogue} := by decide

/-- World reach over `world` alone, and a private read with none, on one clock. -/
def worldOnly : Scope := ⟨{.world}, ∅, ⟨.N, .all⟩, ⟨0, 0, 1⟩, 1, none⟩

/-- A private read with no world reach. -/
def mirrorRead : Scope := ⟨{.mirrorAuthored}, ∅, ⟨.N, .all⟩, ⟨0, 0, 0⟩, 1, none⟩

/-- The zone law does not survive join. -/
theorem zone_join_fails : zoneOk worldOnly ∧ zoneOk mirrorRead ∧
    worldOnly.join mirrorRead =
      .ok ⟨{.world, .mirrorAuthored}, ∅, ⟨.N, .all⟩, ⟨0, 0, 1⟩, 1, none⟩ ∧
    ¬ zoneOk ⟨{.world, .mirrorAuthored}, ∅, ⟨.N, .all⟩, ⟨0, 0, 1⟩, 1, none⟩ := by decide

/-- The Ambassador's search over `reference` alone raises `SliceError`. -/
theorem search_reference_slices : required .search [.reference] false true = .error .slice := by
  decide

/-- A delegated clearance can be strictly narrower than the meet of the parents' clearances:
`observed` and `dialogue` share no stratum, yet both carry observed rows. -/
theorem classesOf_meet_strict :
    classesOf stratumClasses ({.observed} ∩ {.dialogue}) = ∅ ∧
      classesOf stratumClasses {.observed} ∩ classesOf stratumClasses {.dialogue} =
        {.observed} := by
  decide

/-- An atlas covering every clock but wall time and the live present. -/
def anAtlas : Atlas :=
  ⟨fun c ↦ decide (c ≠ .wall ∧ c ≠ .now), fun _ _ ↦ 1, fun x y ↦ if x = y then some x else none⟩

/-- The delegation the Python probe measured: a parent on `commit`, a template on `N_s`. Under the
atlas the child exists and lies under neither. -/
theorem atlas_delegation :
    ∃ m, (⟨{.curated}, univ, ⟨.commit, .all⟩, ⟨0, 0, 0⟩, 1, none⟩ : Scope).meetVia (some anAtlas)
      ⟨{.curated}, univ, ⟨.Ns, .all⟩, ⟨0, 0, 0⟩, 1, none⟩ = .ok m ∧
      ¬ m.Le ⟨{.curated}, univ, ⟨.commit, .all⟩, ⟨0, 0, 0⟩, 1, none⟩ ∧
      ¬ m.Le ⟨{.curated}, univ, ⟨.Ns, .all⟩, ⟨0, 0, 0⟩, 1, none⟩ :=
  Scope.atlas_breaks_delegation anAtlas (by decide) (by decide) (by decide) (by decide) (by decide)

end Witness

/-! ## Attacks

Every law above was attacked before it was proved: windows as the code's constructors build them,
with int bounds in `[-3, 3]` or tokens, so that ties, degenerate and inverted intervals all occur;
scopes over random strata, fibers, three clocks, such windows, authorities, tiers and cuts. Each
`refuted` line is a nearby false law and must be refuted. -/

namespace Attack

/-- A bound from a code: an int in `[-3, 3]`, or a token. -/
def bnd (t : Bool) (z : Fin 7) : Bound := if t then .tok z.val else .int (z.val - 3)

/-- A window code: the kind, then two bound codes. -/
abbrev WCode := Fin 4 × Bool × Fin 7 × Bool × Fin 7

/-- The window a code builds, by the code's own constructors. -/
def win (c : WCode) : Window :=
  match c.1.val with
  | 0 => .point (bnd c.2.1 c.2.2.1)
  | 1 => .interval (bnd c.2.1 c.2.2.1) (bnd c.2.2.2.1 c.2.2.2.2)
  | 2 => .all
  | _ => .empty

-- The preorder.
#eval survives (∀ a b c : WCode, (win a).Le (win b) → (win b).Le (win c) → (win a).Le (win c)) 151

-- Control: antisymmetry.
#eval refuted (∀ a b : WCode, (win a).Le (win b) → (win b).Le (win a) → win a = win b) 152

-- The meet is the greatest lower bound among well-formed windows (the empty window aside, which
-- lies under everything).
#eval survives (∀ x a b : WCode, ((win x).WF ∧ (win x).kind ≠ .empty ∧ (win x).Le (win a) ∧
  (win x).Le (win b)) → (win x).Le ((win a).meet (win b))) 153

-- Control: the same without well-formedness.
#eval refuted (∀ x a b : WCode, ((win x).kind ≠ .empty ∧ (win x).Le (win a) ∧
  (win x).Le (win b)) → (win x).Le ((win a).meet (win b))) 154

-- The join is the least upper bound of any two windows.
#eval survives (∀ x a b : WCode, decide (((win a).join (win b)).Le (win x)) =
  (decide ((win a).Le (win x)) && decide ((win b).Le (win x)))) 155

-- Control: the meet in its place.
#eval refuted (∀ x a b : WCode, decide (((win a).meet (win b)).Le (win x)) =
  (decide ((win a).Le (win x)) && decide ((win b).Le (win x)))) 156

/-- One of the three clocks the attacks draw. -/
def clk (i : Fin 3) : Clock := match i.val with
  | 0 => .N
  | 1 => .Ns
  | _ => .commit

/-- A fiber from a code. -/
def fib (i : Fin 3) : Fiber := match i.val with
  | 0 => .F
  | 1 => .D
  | _ => .C

/-- A scope code: strata to close, fibers, a clock, a window, an authority, a tier, a cut. -/
abbrev SCode :=
  List (Fin 15) × List (Fin 3) × Fin 3 × WCode × (Fin 2 × Fin 2 × Fin 4) × Fin 3 × Fin 3

/-- The scope a code builds. -/
def scp (c : SCode) : Scope :=
  let (σ, es, k, w, (p, sw, wr), t, cu) := c
  ⟨close (σ.map fun i ↦ Stratum.nth i.val).toFinset, (es.map fib).toFinset, ⟨clk k, win w⟩,
    ⟨p, sw, wr⟩, t, if cu.val = 0 then none else some cu.val⟩

/-- The meet under an atlas exists. -/
def okMeet (A : Option Atlas) (a b : Scope) : Bool :=
  match a.meetVia A b with
  | .ok _ => true
  | .error _ => false

/-- The meet, where it exists, lies under both inputs. -/
def delegates (A : Option Atlas) (a b : Scope) : Bool :=
  match a.meetVia A b with
  | .ok m => decide (m.Le a ∧ m.Le b)
  | .error _ => true

-- Monotone delegation, with no atlas.
set_option synthInstance.maxSize 4096 in
#eval survives (∀ a b : SCode, ((scp a).Valid ∧ (scp b).Valid ∧ okMeet none (scp a) (scp b)) →
  delegates none (scp a) (scp b) = true) 157

-- Control: the same under an atlas.
set_option synthInstance.maxSize 4096 in
#eval refuted (∀ a b : SCode, ((scp a).Valid ∧ (scp b).Valid ∧
  okMeet (some Witness.anAtlas) (scp a) (scp b)) →
  delegates (some Witness.anAtlas) (scp a) (scp b) = true) 158

/-- The zone law holds of the meet, where it exists. -/
def zoneMeet (A : Option Atlas) (a b : Scope) : Bool :=
  match a.meetVia A b with
  | .ok m => decide (zoneOk m)
  | .error _ => true

/-- The zone law holds of the join, where it exists. -/
def zoneJoin (a b : Scope) : Bool :=
  match a.join b with
  | .ok j => decide (zoneOk j)
  | .error _ => true

-- The zone law survives delegation, even under an atlas.
set_option synthInstance.maxSize 4096 in
#eval survives (∀ a b : SCode, (zoneOk (scp a) ∧ okMeet (some Witness.anAtlas) (scp a) (scp b)) →
  zoneMeet (some Witness.anAtlas) (scp a) (scp b) = true) 159

-- Control: it does not survive join.
set_option synthInstance.maxSize 4096 in
#eval refuted (∀ a b : SCode, (zoneOk (scp a) ∧ zoneOk (scp b)) → zoneJoin (scp a) (scp b) = true)
  160

/-- The tier of `(a ⊓ b) ⊔ c`, where it exists, against the least tier of the three. -/
def tierOf (a b c : Scope) (least : Bool) : Bool :=
  match (Expr.join (.meet (.leaf a) (.leaf b)) (.leaf c)).eval none with
  | .ok s => if least then decide (s.tier = min (min a.tier b.tier) c.tier)
    else decide (s.tier = max (max a.tier b.tier) c.tier)
  | .error _ => true

-- No laundering: a composition carries the least tier of its inputs.
set_option synthInstance.maxSize 4096 in
#eval survives (∀ a b c : SCode, (Expr.join (.meet (.leaf (scp a)) (.leaf (scp b)))
  (.leaf (scp c))).eval none |>.toBool → tierOf (scp a) (scp b) (scp c) true = true) 161

-- Control: the greatest tier.
set_option synthInstance.maxSize 4096 in
#eval refuted (∀ a b c : SCode, (Expr.join (.meet (.leaf (scp a)) (.leaf (scp b)))
  (.leaf (scp c))).eval none |>.toBool → tierOf (scp a) (scp b) (scp c) false = true) 162

-- Closure is idempotent and closed under refinement.
#eval survives (∀ l : List (Fin 15), let S := (l.map fun i ↦ Stratum.nth i.val).toFinset;
  close (close S) = close S ∧ IsDown (close S)) 163

-- Control: every named set is already closed.
#eval refuted (∀ l : List (Fin 15), let S := (l.map fun i ↦ Stratum.nth i.val).toFinset;
  close S = S) 164

/-- A strata name from a code. -/
def nm (i : Fin 6) : Name := match i.val with
  | 0 => .mirror
  | 1 => .dialogue
  | 2 => .interpreted
  | 3 => .curated
  | 4 => .observed
  | _ => .reference

-- A search without history slices exactly when `reference` is the one name.
#eval survives (∀ l : List (Fin 6), isSlice (required .search (pick (l.map nm)) false true) =
  decide (l.map nm = [.reference])) 165

-- Control: it never slices.
#eval refuted (∀ l : List (Fin 6), isSlice (required .search (pick (l.map nm)) false true) = false)
  166

end Attack

end Palace.CQ
