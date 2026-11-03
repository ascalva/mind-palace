module

public import Palace.Scope
public import PalaceTest.Attack
public meta import Palace.Scope
public meta import PalaceTest.Attack

/-!
# Attacks on `Palace.Scope`

The Plausible attacks and negative controls for the laws of `Palace/Scope.lean`. They run
when this module builds (`lake test`); the library itself runs no code at build time.
-/

@[expose] public section

open Finset

namespace Palace.CQ

/-! ## Attacks

Every law above was attacked before it was proved: windows as the code's constructors build them,
with int bounds in `[-3, 3]` or tokens, so that ties, degenerate and inverted intervals all occur;
raw windows of any shape; scopes over random strata, fibers, three clocks, such windows,
authorities, tiers and cuts. Each `refuted` line is a nearby false law and must be refuted. -/

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

/-- A window of any shape, as direct construction could build it before the constructor checks. -/
def raw (c : WCode) : Window :=
  ⟨match c.1.val with
    | 0 => .point
    | 1 => .interval
    | 2 => .all
    | _ => .empty, bnd c.2.1 c.2.2.1, bnd c.2.2.2.1 c.2.2.2.2⟩

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

-- On valid windows the meet is commutative and associative, on the nose.
#eval survives (∀ a b c : WCode, ((win a).Valid ∧ (win b).Valid ∧ (win c).Valid) →
  ((win a).meet (win b) = (win b).meet (win a) ∧
    ((win a).meet (win b)).meet (win c) = (win a).meet ((win b).meet (win c)))) 157

-- Control: commutativity over windows of any shape.
#eval refuted (∀ a b : WCode, (raw a).meet (raw b) = (raw b).meet (raw a)) 158

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

/-- The meet exists. -/
def okMeet (a b : Scope) : Bool :=
  match a.meet b with
  | .ok _ => true
  | .error _ => false

/-- The meet, where it exists, lies under both inputs. -/
def delegates (a b : Scope) : Bool :=
  match a.meet b with
  | .ok m => decide (m.Le a ∧ m.Le b)
  | .error _ => true

/-- The time meet under an atlas, where it exists, lies under both inputs. -/
def timeDelegates (A : Atlas) (a b : Time) : Bool :=
  match a.meetVia (some A) b with
  | some t => decide (t.Le a ∧ t.Le b)
  | none => true

-- Monotone delegation.
set_option synthInstance.maxSize 4096 in
#eval survives (∀ a b : SCode, ((scp a).Valid ∧ (scp b).Valid ∧ okMeet (scp a) (scp b)) →
  delegates (scp a) (scp b) = true) 159

-- Control: the atlas's time completion as a delegation.
set_option synthInstance.maxSize 4096 in
#eval refuted (∀ a b : SCode, timeDelegates Witness.anAtlas (scp a).time (scp b).time = true) 160

/-- The zone law holds of the meet, where it exists. -/
def zoneMeet (a b : Scope) : Bool :=
  match a.meet b with
  | .ok m => decide (zoneOk m)
  | .error _ => true

/-- The zone law holds of the join, where it exists. -/
def zoneJoin (a b : Scope) : Bool :=
  match a.join b with
  | .ok j => decide (zoneOk j)
  | .error _ => true

-- The zone law survives delegation.
set_option synthInstance.maxSize 4096 in
#eval survives (∀ a b : SCode, (zoneOk (scp a) ∧ okMeet (scp a) (scp b)) →
  zoneMeet (scp a) (scp b) = true) 161

-- Control: it does not survive join.
set_option synthInstance.maxSize 4096 in
#eval refuted (∀ a b : SCode, (zoneOk (scp a) ∧ zoneOk (scp b)) → zoneJoin (scp a) (scp b) = true)
  162

/-- The tier of `(a ⊓ b) ⊔ c`, where it exists, against the least or the greatest tier of the
three. -/
def tierOf (a b c : Scope) (least : Bool) : Bool :=
  match (Expr.join (.meet (.leaf a) (.leaf b)) (.leaf c)).eval with
  | .ok s => if least then decide (s.tier = min (min a.tier b.tier) c.tier)
    else decide (s.tier = max (max a.tier b.tier) c.tier)
  | .error _ => true

-- No laundering: a composition carries the least tier of its inputs.
set_option synthInstance.maxSize 4096 in
#eval survives (∀ a b c : SCode, (Expr.join (.meet (.leaf (scp a)) (.leaf (scp b)))
  (.leaf (scp c))).eval.toBool → tierOf (scp a) (scp b) (scp c) true = true) 163

-- Control: the greatest tier.
set_option synthInstance.maxSize 4096 in
#eval refuted (∀ a b c : SCode, (Expr.join (.meet (.leaf (scp a)) (.leaf (scp b)))
  (.leaf (scp c))).eval.toBool → tierOf (scp a) (scp b) (scp c) false = true) 164

-- Closure is idempotent and closed under refinement.
#eval survives (∀ l : List (Fin 15), let S := (l.map fun i ↦ Stratum.nth i.val).toFinset;
  close (close S) = close S ∧ IsDown (close S)) 165

-- Control: every named set is already closed.
#eval refuted (∀ l : List (Fin 15), let S := (l.map fun i ↦ Stratum.nth i.val).toFinset;
  close S = S) 166

/-- A strata name from a code. -/
def nm (i : Fin 6) : Name := match i.val with
  | 0 => .mirror
  | 1 => .dialogue
  | 2 => .interpreted
  | 3 => .curated
  | 4 => .observed
  | _ => .reference

/-- `required(search)` as it was, with the cut decided from the number of names. -/
def searchByNames (strata : List Stratum) : Except Err Scope :=
  mkScope strata ∅ .projectionEvent (.point anchor)
    (cut := if 1 < strata.length then some singleRead else none)

-- A search never slices, over any strata.
#eval survives (∀ l : List (Fin 15), ∀ h : Bool,
  isSlice (required .search (l.map fun i ↦ Stratum.nth i.val) h true) = false) 167

-- Control: the old rule, over each of the Ambassador's names alone.
#eval refuted (∀ i : Fin 6, isSlice (searchByNames (pick [nm i])) = false) 168

end Attack

end Palace.CQ
