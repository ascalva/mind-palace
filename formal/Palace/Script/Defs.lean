module

public import Palace.Door.Defs

/-!
# The door's language: the model

The second form of the door (dn-door-language): the language is generic, the ingestion paths are
its scripts, and the palace, like an operating system, decides what a script may open and write
and the label of everything it stores. A script's value is a plan of effects; what the laws need
of it is where each stored value came from. A value that can be stored is **content**: bytes, a
label and an origin. An expression is, as far as labels go, an item a source yields, a
projection of an expression by a view (a field, an element, a reader's parse), or a construction
(a literal, a parameter, anything composed), and its value carries the item's label and path
under projections, and the observed label and no origin otherwise (§E3). The writer holds, at
each path, a row: bytes, label, identity, whether its content came from a source, whether it is
active. It admits a store or a retire by the note's rules R2 to R7 against the palace's table
and the cut, and lands a plan effect by effect, a refused effect landing nothing.
-/

@[expose] public section

namespace Palace.Script

/-- An item a source yields at the cut: its bytes, the label the source's rule gives it, and its
path. Items come only from the palace's sources; no expression makes one. -/
structure Item (B L P : Type*) where
  /-- The item's bytes. -/
  bytes : B
  /-- The label the source's rule gives it. -/
  label : L
  /-- The item's path, where the stores name it. -/
  path : P

/-- A value a script can store: its bytes, its label, and its origin, the path of the item it
projects, if it projects one. -/
structure Content (B L P : Type*) where
  /-- The bytes. -/
  bytes : B
  /-- The label, the palace's. -/
  label : L
  /-- The path of the item the value projects, if any. -/
  origin : Option P

/-- The forms of an expression that matter to a label. -/
inductive Expr (B L P W : Type*) where
  /-- An item a source yields. -/
  | item (i : Item B L P)
  /-- A projection by a view: a field, an element, a reader's parse. -/
  | proj (w : W) (e : Expr B L P W)
  /-- Any other construction, with the bytes it computes: a literal, a parameter, a
  concatenation, a slice, anything composed. -/
  | make (b : B)

variable {B L P I W K Rl : Type*}

/-- Views applied to bytes, the first outermost. -/
def applyViews (view : W → B → B) : List W → B → B
  | [], b => b
  | w :: ws, b => view w (applyViews view ws b)

namespace Expr

/-- The item under an expression's projections; none for a construction. -/
def root : Expr B L P W → Option (Item B L P)
  | item i => some i
  | proj _ e => e.root
  | make _ => none

/-- An expression's views, the outermost first. -/
def views : Expr B L P W → List W
  | item _ => []
  | proj w e => w :: e.views
  | make _ => []

end Expr

/-- The value of an expression, as far as labels go: an item's bytes, label and path; a
projection's view of its operand, with the operand's label and origin; a construction's bytes,
observed, with no origin (dn-door-language §E3). -/
def eval (view : W → B → B) (observed : L) : Expr B L P W → Content B L P
  | .item i => ⟨i.bytes, i.label, some i.path⟩
  | .proj w e => ⟨view w (eval view observed e).bytes, (eval view observed e).label,
      (eval view observed e).origin⟩
  | .make b => ⟨b, observed, none⟩

/-- The label set an expression's type carries (dn-door-language §E12): an item's is the set its
source's rule may give, a projection's is its operand's, a construction's is the observed label
alone. Inference unifies two sets by their union, so an inferred set contains this one. -/
def labelsOf [DecidableEq L] (srcLabels : Item B L P → Finset L) (observed : L) :
    Expr B L P W → Finset L
  | .item i => srcLabels i
  | .proj _ e => labelsOf srcLabels observed e
  | .make _ => {observed}

/-- A row the writer holds at a path: the bytes, the label, the identity (the version chain it
extends), whether its content came from a source, and whether it is active. -/
structure Row (B L I : Type*) where
  /-- The bytes. -/
  bytes : B
  /-- The label. -/
  label : L
  /-- The identity. -/
  ident : I
  /-- Whether the content came from a source (had an origin). -/
  sourced : Bool
  /-- Whether the row is active (not retired). -/
  active : Bool

/-- How a store names the identity of a path new to the writer. -/
inductive Naming (P I : Type*) where
  /-- The path's own identity. -/
  | own
  /-- An identity read off the item at a path: a note's `id::`. -/
  | prop (src : P) (i : I)
  /-- The identity held at another path: a rename. -/
  | held (q : P)

/-- An effect of a plan. -/
inductive Effect (B L P I W K : Type*) where
  /-- Store an expression's value at a path, naming its identity, in a place. -/
  | store (p : P) (n : Naming P I) (e : Expr B L P W) (k : K)
  /-- Retire a path in a place. -/
  | retire (p : P) (k : K)

/-- The path an effect writes. -/
def Effect.path : Effect B L P I W K → P
  | .store p _ _ _ => p
  | .retire p _ => p

/-- The place an effect writes. -/
def Effect.place : Effect B L P I W K → K
  | .store _ _ _ k => k
  | .retire _ k => k

/-- The palace's table and the cut, as the writer sees them: the readers' views, the observed
label, the classes each place accepts, each role's namespace in each place, the paths that
belong to a source, the items the sources yield, whether a source still has a path, and a path's
own identity. -/
structure Table (B L P I W K Rl : Type*) where
  /-- What a view does to bytes. -/
  view : W → B → B
  /-- The label of anything a script composes. -/
  observed : L
  /-- Whether a place accepts a label (the kernel's `STRATUM_CLASSES`). -/
  accepts : K → L → Bool
  /-- Whether a role may write a path of a place (its prefixes). -/
  ns : Rl → K → P → Bool
  /-- Whether a path lies in a source's own space (the vault's root, a reader's prefix). -/
  owned : P → Bool
  /-- Whether the sources yield an item at the cut. -/
  yields : Item B L P → Bool
  /-- Whether a source still has a path at the cut. -/
  has : P → Bool
  /-- A path's own identity. -/
  ofPath : P → I

/-- The writer's state: a row, or nothing, at each path. -/
abbrev Held (P B L I : Type*) := P → Option (Row B L I)

variable [DecidableEq B] [DecidableEq P]

/-- The identity a store gives a path new to the writer, when its naming is admitted (R6): the
path's own; one read off the very item stored; or one held at a path its source no longer has,
holding the same bytes. -/
def resolve (T : Table B L P I W K Rl) (h : Held P B L I) (c : Content B L P) (p : P) :
    Naming P I → Option I
  | .own => some (T.ofPath p)
  | .prop src i => if c.origin = some src then some i else none
  | .held q => match h q with
    | some r => if r.bytes = c.bytes ∧ T.has q = false then some r.ident else none
    | none => none

variable [DecidableEq L]

/-- The writer admits a store (R2 to R6, R8): the items under it are the sources', its place
accepts its label, its path is in the role's namespace, content with an origin lands at its
origin, a path in a source's space takes only content with an origin, a held path keeps its
label, and a new path's identity is admitted. -/
def okStore (T : Table B L P I W K Rl) (r : Rl) (h : Held P B L I) (p : P) (n : Naming P I)
    (e : Expr B L P W) (k : K) : Bool :=
  (match e.root with | some i => T.yields i | none => true)
    && T.accepts k (eval T.view T.observed e).label && T.ns r k p
    && (match (eval T.view T.observed e).origin with | some a => decide (a = p) | none => true)
    && (!T.owned p || (eval T.view T.observed e).origin.isSome)
    && (match h p with
        | some row => decide (row.label = (eval T.view T.observed e).label)
        | none => (resolve T h (eval T.view T.observed e) p n).isSome)

/-- The landing of a store: the row at its path, active, with the held identity if the path is
held and the resolved one if it is new. -/
def landStore (T : Table B L P I W K Rl) (h : Held P B L I) (p : P) (n : Naming P I)
    (e : Expr B L P W) : Held P B L I :=
  Function.update h p (some ⟨(eval T.view T.observed e).bytes, (eval T.view T.observed e).label,
    (match h p with
      | some row => row.ident
      | none => (resolve T h (eval T.view T.observed e) p n).getD (T.ofPath p)),
    (eval T.view T.observed e).origin.isSome, true⟩)

/-- The writer admits a retire (R7): the path is held and in the role's namespace, and if its
content came from a source, the source no longer has it. -/
def okRetire (T : Table B L P I W K Rl) (r : Rl) (h : Held P B L I) (p : P) (k : K) : Bool :=
  match h p with
  | some row => T.ns r k p && (!row.sourced || !T.has p)
  | none => false

/-- The landing of a retire: the row kept, inactive. -/
def landRetire (h : Held P B L I) (p : P) : Held P B L I :=
  Function.update h p ((h p).map fun row ↦ { row with active := false })

/-- One effect: landed if the writer admits it; refused otherwise, landing nothing, and the
plan goes on. -/
def step (T : Table B L P I W K Rl) (r : Rl) (h : Held P B L I) :
    Effect B L P I W K → Held P B L I
  | .store p n e k => if okStore T r h p n e k then landStore T h p n e else h
  | .retire p k => if okRetire T r h p k then landRetire h p else h

/-- A plan, landed effect by effect. -/
def landPlan (T : Table B L P I W K Rl) (r : Rl) (plan : List (Effect B L P I W K))
    (h : Held P B L I) : Held P B L I :=
  plan.foldl (step T r) h

/-- A store as the first form's command (`Palace/Door/Defs.lean`): the rows the place indexes its
bytes into, its path as the identity the key is held for, the digest of its bytes. -/
def toSource {R G : Type*} (rowsOf : B → List (Finset R)) (dig : B → G) (p : P) (b : B) :
    Door.Source R P G :=
  ⟨rowsOf b, p, dig b⟩

end Palace.Script
