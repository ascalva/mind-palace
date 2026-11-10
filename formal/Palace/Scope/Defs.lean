module

public import Mathlib.Data.Finset.Card
public import Mathlib.Data.Finset.Union
public import Mathlib.Data.Fintype.Basic
public import Mathlib.Order.Basic

/-!
# The capability-scope algebra (CQ-scope), the definitions

The definitions the laws of `Palace/Scope.lean` are stated over. With `Spec/Scope.lean`
they are what a reader checks against `docs/LAWS.md`: `lake comparator` ensures the library
proves exactly the statements there, so no other file can change what is proved.
-/

@[expose] public section

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
  /-- The window's kind. -/
  kind : Kind
  /-- The lower bound. -/
  lo : Bound
  /-- The upper bound. -/
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

/-- `Window.__le__`. -/
def Le (a b : Window) : Prop :=
  a.kind = .empty ∨ b.kind = .all ∨ a = b ∨ (a.kind ≠ .all ∧ b.kind ≠ .empty ∧ Within a b)

/-- Well-formed: the int bounds of a window are not inverted. -/
def WF (w : Window) : Prop :=
  match w.ints with
  | some (l, h) => l ≤ h
  | none => True

/-- The shapes `Window.__post_init__` accepts: `∗` and `⊥` carry no bounds, a point has one bound,
and an int interval is not inverted. -/
def Valid (w : Window) : Prop :=
  ((w.kind = .all ∨ w.kind = .empty) → w.lo = .none ∧ w.hi = .none) ∧
    (w.kind = .point → w.lo = w.hi) ∧ (w.kind = .interval → w.WF)

end Window

/-- `TimeScope`. -/
structure Time where
  /-- The clock the window is read on. -/
  clock : Clock
  /-- The window on that clock. -/
  window : Window
  deriving DecidableEq, Repr

/-- A clock atlas (`ClockAtlas`): which clocks pull back to `N`, the pullback of a window as an
opaque token, the meet of two tokens (`none` when empty), and the token a window carries. -/
structure Atlas where
  /-- Whether a clock pulls back to `N`. -/
  has : Clock → Bool
  /-- The pullback of a window on a clock to `N`, as an opaque token. -/
  pullback : Clock → Window → ℕ
  /-- The meet of two tokens; `none` when it is empty. -/
  intersect : ℕ → ℕ → Option ℕ
  /-- The token a window carries, if any. -/
  token : Window → Option ℕ

namespace Time

/-- `_pullback_meet`: the event-level meet on `N`, its token wrapped as `[S, S]`. -/
def pullbackMeet (A : Atlas) (a b : Time) : Time :=
  ⟨.N, match A.intersect (A.pullback a.clock a.window) (A.pullback b.clock b.window) with
    | none => .empty
    | some t => .interval (.tok t) (.tok t)⟩

/-- `TimeScope.meet` under the registered atlas, `none` when none is registered; a `none` result
is `NoCommonClockError`. Two `N`-windows of which one carries a token meet as event sets. -/
def meetVia (A : Option Atlas) (a b : Time) : Option Time :=
  match A with
  | none => if a.clock = b.clock then some ⟨a.clock, a.window.meet b.window⟩ else none
  | some A =>
    if a.clock = b.clock then
      if a.clock = .N ∧ A.has .N = true ∧
          ((A.token a.window).isSome = true ∨ (A.token b.window).isSome = true) then
        some (pullbackMeet A a b)
      else some ⟨a.clock, a.window.meet b.window⟩
    else if A.has a.clock = true ∧ A.has b.clock = true then some (pullbackMeet A a b)
    else none

/-- `TimeScope.__le__`: false across clocks. -/
def Le (a b : Time) : Prop := a.clock = b.clock ∧ a.window.Le b.window

end Time

/-! ## A: authority, and the tier -/

/-- `A = P × W_Σ × W_world`: privilege (`READ < READ_PROPOSE`), the projection-write bit, and world
reach (`NONE < SENSING < REVERSIBLE < IRREVERSIBLE`). `__post_init__`'s check that `W_Σ` is a bit is
the type `Fin 2`. -/
structure Authority where
  /-- The privilege: `READ` (0) or `READ_PROPOSE` (1). -/
  privilege : Fin 2
  /-- The projection-write bit `W_Σ`. -/
  storeWrite : Fin 2
  /-- World reach: `NONE`, `SENSING`, `REVERSIBLE` or `IRREVERSIBLE` (0 to 3). -/
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

end Authority

/-! ## The scope -/

/-- `Scope`: the four coordinates, the tier (`CONVENTION < STATIC_GUARD < STRUCTURAL`), and the
explicit cut, an opaque token. Tier and cut are outside `==` and `⊑`. -/
structure Scope where
  /-- `Σ`: the strata the scope reads. -/
  sigma : Finset Stratum
  /-- `E`: the edge fibers the scope reaches. -/
  edges : Finset Fiber
  /-- `T`: the clock and window. -/
  time : Time
  /-- `A`: the authority. -/
  authority : Authority
  /-- The tier: `CONVENTION`, `STATIC_GUARD` or `STRUCTURAL` (0 to 2). -/
  tier : Fin 3
  /-- The explicit cut, an opaque token. -/
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

/-- The constructor: `SliceError` when the SLICE rule fires. -/
def build (s : Scope) : Except Err Scope := if s.Slices then .error .slice else .ok s

/-- `_meet_cut`: the cut both carry; else the one a single side carries, if the meet kept that
side's window; else none. -/
def meetCut (a b : Scope) (w : Window) : Option ℕ :=
  if a.cut = b.cut then a.cut
  else if b.cut = none ∧ w = a.time.window then a.cut
  else if a.cut = none ∧ w = b.time.window then b.cut
  else none

/-- `Scope.meet`, delegation: componentwise meets on one clock, the least tier, and the cut
`meetCut` keeps. Across clocks it raises `NoCommonClockError` whatever atlas is registered. -/
def meet (a b : Scope) : Except Err Scope :=
  if a.time.clock = b.time.clock then
    build ⟨a.sigma ∩ b.sigma, a.edges ∩ b.edges,
      ⟨a.time.clock, a.time.window.meet b.time.window⟩, a.authority.meet b.authority,
      min a.tier b.tier, meetCut a b (a.time.window.meet b.time.window)⟩
  else .error .noCommonClock

/-- `Scope.join`: componentwise joins on one clock; across clocks, `NoCommonClockError`. -/
def join (a b : Scope) : Except Err Scope :=
  if a.time.clock = b.time.clock then
    build ⟨a.sigma ∪ b.sigma, a.edges ∪ b.edges, ⟨a.time.clock, a.time.window.join b.time.window⟩,
      a.authority.join b.authority, min a.tier b.tier, if a.cut = b.cut then a.cut else none⟩
  else .error .noCommonClock

/-- `Scope.__le__`: the four coordinates only. -/
def Le (a b : Scope) : Prop :=
  a.sigma ⊆ b.sigma ∧ a.edges ⊆ b.edges ∧ a.time.Le b.time ∧ a.authority.Le b.authority

end Scope

/-! ## Firewalls and the zone law -/

/-- `Ideal.excludes`: `s` names no stratum of the ideal. -/
def excludes (ι : Finset Stratum) (s : Scope) : Prop := Disjoint s.sigma ι

/-- `admissible`: every firewall ideal is excluded. -/
def admissible (ιs : List (Finset Stratum)) (s : Scope) : Prop := ∀ ι ∈ ιs, excludes ι s

/-- `DENYLIST_IDEAL`. -/
def denylist : Finset Stratum := {.foundation}

/-- `PRIVATE_STRATA`: every base stratum but `world`, with every refinement below one, named or
not, `exhaust` included. -/
def privateStrata : Finset Stratum := univ.filter fun s ↦ s.parent.getD s ∈ base.erase .world

/-- `zone_admissible`: a scope that reads a private stratum has no world reach. -/
def zoneOk (s : Scope) : Prop := Disjoint s.sigma privateStrata ∨ s.authority.world = 0

/-! ## The query engine: grants and required scopes (`core/query.py`) -/

/-- `Grant.__post_init__` accepts a list of scopes: each one admissible and zone-admissible. -/
def GrantOk (g : List Scope) : Prop := ∀ s ∈ g, admissible [denylist] s ∧ zoneOk s

/-- `Grant.admits`: the required scope lies under one of the granted scopes. -/
def admits (g : List Scope) (r : Scope) : Prop := ∃ s ∈ g, r.Le s

/-- Whether a result is a `SliceError`. -/
def isSlice : Except Err Scope → Bool
  | .error .slice => true
  | _ => false

/-- `Grant.meet`: the pairwise meets that exist, skipping a pair that raises either error. -/
def grantMeet (g h : List Scope) : List Scope :=
  (g.flatMap fun a ↦ h.map fun b ↦ a.meet b).filterMap fun r ↦ match r with
    | .ok m => some m
    | .error _ => none

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

/-- `required(verb)`: the least scope a sentence needs. `search` sets the single-read cut when
its strata, closed, number more than one. -/
def required (v : Verb) (strata : List Stratum) (history authored : Bool) : Except Err Scope :=
  match v with
  | .search =>
    mkScope strata (if history then {.D} else ∅) .projectionEvent
      (if history then .all else .point anchor)
      (cut := if 1 < (close strata.toFinset).card then some singleRead else none)
  | .diffuse | .hybrid | .related => mkScope [.mirrorAuthored] {.F} .projectionEvent (.point anchor)
  | .reach => mkScope [.reference] {.F} .commit (.point anchor)
  | .history => mkScope [.mirrorAuthored] {.D} .Ns .all
  | .origin => mkScope [.reference, .dialogueTranscript] {.C} .commit (.point anchor)
  | .capture =>
    mkScope [if authored then .dialogueTranscript else .observed] ∅ .projectionEvent
      (.point anchor) (write := true)

/-- The Ambassador's grant `AMBASSADOR`: three planes, one per clock. -/
def ambassador : List Scope :=
  [⟨close {.mirror, .curated, .interpreted, .dialogue, .observed, .reference}, {.F, .D},
      ⟨.projectionEvent, .all⟩, ⟨1, 1, 0⟩, 1, none⟩,
    ⟨close {.reference, .dialogue}, {.F, .C}, ⟨.commit, .all⟩, ⟨1, 0, 0⟩, 1, none⟩,
    ⟨close {.mirror}, {.D}, ⟨.Ns, .all⟩, ⟨0, 0, 0⟩, 1, none⟩]

/-- A plane with the hypothetical overlay named: `Σ ∪ {hypothetical}` — the overlay has nothing
below it, so naming it closes nothing further — and every other coordinate as it was. -/
def Scope.nameOverlay (p : Scope) : Scope := { p with sigma := insert .hypothetical p.sigma }

/-- `with_overlay` (`core/query.py`): a grant with the overlay named on every plane — what the
owner grants a client to evaluate `assume` sentences (dn-query-sentence-algebra §4 d). -/
def overlayGrant (g : List Scope) : List Scope := g.map Scope.nameOverlay

/-- `AMBASSADOR_OVERLAY`: the Ambassador's three planes, each naming the overlay — the owner's
grant of 2026-11-04 to the sentence surfaces. -/
def ambassadorOverlay : List Scope := overlayGrant ambassador

/-- The guest's grant `GUEST`: the Ambassador's first two planes over the strata a guest reads
(the dialogue, the reference stratum, the curated papers, the observed records), read-only, with
no world reach; `grant_for` resolves the role `guest` to it (`core/ingest/ingress.py`). -/
def guest : List Scope :=
  [⟨close {.dialogue, .reference, .curated, .observed}, {.F, .D}, ⟨.projectionEvent, .all⟩,
      ⟨0, 0, 0⟩, 1, none⟩,
    ⟨close {.reference, .dialogue}, {.F, .C}, ⟨.commit, .all⟩, ⟨0, 0, 0⟩, 1, none⟩]

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

/-! ## Scopes: delegation, its partiality, and the tier -/

/-- A composition of scopes: leaves, meets and joins, as a dreamer's scope expression builds. -/
inductive Expr
  | leaf (s : Scope)
  | meet (e f : Expr)
  | join (e f : Expr)

namespace Expr

/-- Evaluate left to right, as Python does; the first error escapes. -/
def eval : Expr → Except Err Scope
  | leaf s => .ok s
  | meet e f => e.eval.bind fun a ↦ f.eval.bind fun b ↦ a.meet b
  | join e f => e.eval.bind fun a ↦ f.eval.bind fun b ↦ a.join b

/-- The scopes an expression composes. -/
def leaves : Expr → List Scope
  | leaf s => [s]
  | meet e f | join e f => e.leaves ++ f.leaves

end Expr

/-! ## Witnesses: what the model found, and what the fixes changed -/

namespace Witness

open Window

/-- A read of two strata on `N_s` over `[1,5]`, with no cut. -/
def sliceA : Scope :=
  ⟨{.mirrorAuthored, .curated}, ∅, ⟨.Ns, .interval (.int 1) (.int 5)⟩, ⟨0, 0, 0⟩, 1, none⟩

/-- The same over `[5,9]`. -/
def sliceB : Scope :=
  ⟨{.mirrorAuthored, .curated}, ∅, ⟨.Ns, .interval (.int 5) (.int 9)⟩, ⟨0, 0, 0⟩, 1, none⟩

/-- An owner's point grant with a cut, over two strata on `N`. -/
def pointGrant : Scope :=
  ⟨close {.ops, .reference}, univ, ⟨.N, .point (.tok 5)⟩, ⟨0, 0, 0⟩, 1, some 5⟩

/-- A dreamer template on the ledger, with no cut. -/
def ledgerTemplate : Scope := ⟨close {.ops, .reference}, univ, ⟨.N, .all⟩, ⟨0, 0, 0⟩, 1, none⟩

/-- A grant that reads only agent exhaust, with irreversible world reach. -/
def exhaustReach : Scope := ⟨close {.exhaust}, ∅, ⟨.Ns, .all⟩, ⟨0, 0, 3⟩, 1, none⟩

/-- World reach over `world` alone, and a private read with none, on one clock. -/
def worldOnly : Scope := ⟨{.world}, ∅, ⟨.N, .all⟩, ⟨0, 0, 1⟩, 1, none⟩

/-- A private read with no world reach. -/
def mirrorRead : Scope := ⟨{.mirrorAuthored}, ∅, ⟨.N, .all⟩, ⟨0, 0, 0⟩, 1, none⟩

/-- An atlas covering every clock but wall time and the live present. -/
def anAtlas : Atlas :=
  ⟨fun c ↦ decide (c ≠ .wall ∧ c ≠ .now), fun _ _ ↦ 1, fun x y ↦ if x = y then some x else none,
    fun _ ↦ none⟩

/-- A parent on `commit` and a template on `N_s`, as the Python probe measured. -/
def commitParent : Scope := ⟨{.curated}, univ, ⟨.commit, .all⟩, ⟨0, 0, 0⟩, 1, none⟩

/-- The template on `N_s`. -/
def nsTemplate : Scope := ⟨{.curated}, univ, ⟨.Ns, .all⟩, ⟨0, 0, 0⟩, 1, none⟩

end Witness

end Palace.CQ
