module

public import Palace.Script
public import PalaceTest.Attack
public meta import Palace.Script
public meta import PalaceTest.Attack

/-!
# Attacks on `Palace.Script`

The Plausible attacks and negative controls for the laws of `Palace/Script.lean`, on exact shadows:
bytes `Fin 4`, labels `Fin 3` (0 the observed label, 1 an authored one, 2 a curated one), paths and
identities `Fin 3`, two views, two places (0 accepts only the authored label, 1 accepts every
label), two roles (0 writes everywhere, 1 only at path 2 and only retires at path 1), paths 0 and 1
in sources' spaces and path 2 free, sources that yield items at paths 1 and 2 and no longer have
path 0. Each control is a writer with one rule taken out: without R4 an item is stored at another
path (ING-14), without R8 a composed value squats a source's path, without the namespace a role
writes outside its prefix, a store that takes the retire-only namespace writes a path the role may
only retire, and the statement with one namespace fails once a role retires where it does not
write (ING-15), without R6's condition an identity is grafted from a path its source still has,
without R7's an item still in its source is retired (ING-17), and a construction claimed to keep
its inputs' label is refuted (ING-13). The Ambassador's inbox has a shadow of its own (§E13 of
dn-ingress-language): the owner's message, which its rule labels authored, and the reply, which it
labels observed; every authored row a store lands is the owner's message, and the two controls are
the bright line's premises taken out, a label a script claims and a reply labelled as the owner's.
They run when this module builds (`lake test`).
-/

@[expose] public section

namespace Palace.Script.Attack

/-- What the shadow's views do to bytes. -/
def view (w : Fin 2) (b : Fin 4) : Fin 4 := ⟨(b.val + w.val + 1) % 4, Nat.mod_lt _ (by decide)⟩

/-- The shadow's table. -/
def tbl : Table (Fin 4) (Fin 3) (Fin 3) (Fin 3) (Fin 2) (Fin 2) (Fin 2) where
  view := view
  observed := 0
  accepts k l := decide (k = 1) || decide (l = 1)
  ns r _ p := decide (r = 0) || decide (p = 2)
  rns r _ p := decide (r = 1) && decide (p = 1)
  owned p := decide (p ≠ 2)
  yields i := decide (i.path ≠ 0)
  has p := decide (p ≠ 0)
  ofPath p := p
  declares p i := decide (i.val = (p.val + 1) % 3)

/-- An expression: an item or a construction, under views, the first outermost. -/
def mk (isItem : Bool) (b : Fin 4) (l : Fin 3) (ip : Fin 3) (ws : List (Fin 2)) :
    Expr (Fin 4) (Fin 3) (Fin 3) (Fin 2) :=
  ws.foldr (fun w e ↦ .proj w e) (if isItem then .item ⟨b, l, ip⟩ else .make b)

/-- A writer's state from codes: path `j` holds nothing for code 0, else a row from the code. -/
def held (cs : List (Fin 9)) : Held (Fin 3) (Fin 4) (Fin 3) (Fin 3) := fun p ↦
  match cs[p.val]? with
  | some c => if c = 0 then none else
      some ⟨⟨c.val % 4, Nat.mod_lt _ (by decide)⟩, ⟨c.val % 3, Nat.mod_lt _ (by decide)⟩,
        ⟨(c.val + 1) % 3, Nat.mod_lt _ (by decide)⟩, c.val % 2 == 0, true⟩
  | none => none

/-- A naming from a code. -/
def nm (c : Fin 3) (q i : Fin 3) : Naming (Fin 3) (Fin 3) :=
  match c with
  | 0 => .own
  | 1 => .prop q i
  | 2 => .held q

/-- Two optional rows agree. -/
def same (a b : Option (Row (Fin 4) (Fin 3) (Fin 3))) : Bool :=
  match a, b with
  | some x, some y => x.bytes == y.bytes && x.label == y.label && x.ident == y.ident
      && x.sourced == y.sourced && x.active == y.active
  | none, none => true
  | _, _ => false

/-- The firewall's conclusion for a store at `p`: an item a source yields, at `p`, with the
value's label, the value's bytes its bytes under the views. -/
def firewallOk (p : Fin 3) (e : Expr (Fin 4) (Fin 3) (Fin 3) (Fin 2)) : Bool :=
  match e.root with
  | some i => tbl.yields i && decide (i.path = p)
      && decide (i.label = (eval tbl.view tbl.observed e).label)
      && decide ((eval tbl.view tbl.observed e).bytes = applyViews tbl.view e.views i.bytes)
  | none => false

/-- The writer without R4: content with an origin may land anywhere. -/
def okStoreNoOrigin (h : Held (Fin 3) (Fin 4) (Fin 3) (Fin 3)) (p : Fin 3)
    (e : Expr (Fin 4) (Fin 3) (Fin 3) (Fin 2)) (k : Fin 2) : Bool :=
  (match e.root with | some i => tbl.yields i | none => true)
    && tbl.accepts k (eval tbl.view tbl.observed e).label && tbl.ns 0 k p
    && (!tbl.owned p || (eval tbl.view tbl.observed e).origin.isSome)
    && (match h p with
        | some row => decide (row.label = (eval tbl.view tbl.observed e).label)
        | none => true)

/-- The writer without R8: a path in a source's space takes any content. -/
def okStoreNoOwner (p : Fin 3) (e : Expr (Fin 4) (Fin 3) (Fin 3) (Fin 2)) (k : Fin 2) : Bool :=
  (match e.root with | some i => tbl.yields i | none => true)
    && tbl.accepts k (eval tbl.view tbl.observed e).label && tbl.ns 0 k p
    && (match (eval tbl.view tbl.observed e).origin with | some a => decide (a = p) | none => true)

/-- R6 without its condition: an identity may be taken from any held path with the same bytes. -/
def resolveGraft (h : Held (Fin 3) (Fin 4) (Fin 3) (Fin 3)) (b : Fin 4) (p : Fin 3) :
    Naming (Fin 3) (Fin 3) → Option (Fin 3)
  | .own => some p
  | .prop _ i => some i
  | .held q => match h q with
    | some r => if r.bytes = b then some r.ident else none
    | none => none

/-- R6 without the declaration: a store takes any identity read off the item it stores. -/
def resolveUndeclared (origin : Option (Fin 3)) : Naming (Fin 3) (Fin 3) → Option (Fin 3)
  | .prop src i => if origin = some src then some i else none
  | _ => none

/-- The writer without the namespace: R3 skipped, every other rule kept. -/
def okStoreNoNs (h : Held (Fin 3) (Fin 4) (Fin 3) (Fin 3)) (p : Fin 3)
    (e : Expr (Fin 4) (Fin 3) (Fin 3) (Fin 2)) (k : Fin 2) : Bool :=
  (match e.root with | some i => tbl.yields i | none => true)
    && tbl.accepts k (eval tbl.view tbl.observed e).label
    && (match (eval tbl.view tbl.observed e).origin with | some a => decide (a = p) | none => true)
    && (!tbl.owned p || (eval tbl.view tbl.observed e).origin.isSome)
    && (match h p with
        | some row => decide (row.label = (eval tbl.view tbl.observed e).label)
        | none => true)

/-- The writer whose stores take the retire-only namespace as well as the write one. -/
def okStoreRetireNs (r : Fin 2) (h : Held (Fin 3) (Fin 4) (Fin 3) (Fin 3)) (p : Fin 3)
    (e : Expr (Fin 4) (Fin 3) (Fin 3) (Fin 2)) (k : Fin 2) : Bool :=
  (match e.root with | some i => tbl.yields i | none => true)
    && tbl.accepts k (eval tbl.view tbl.observed e).label && (tbl.ns r k p || tbl.rns r k p)
    && (match (eval tbl.view tbl.observed e).origin with | some a => decide (a = p) | none => true)
    && (!tbl.owned p || (eval tbl.view tbl.observed e).origin.isSome)
    && (match h p with
        | some row => decide (row.label = (eval tbl.view tbl.observed e).label)
        | none => true)

/-- R7 without its condition: any held path in the namespace may be retired. -/
def okRetireAny (r : Fin 2) (h : Held (Fin 3) (Fin 4) (Fin 3) (Fin 3)) (p : Fin 3) (k : Fin 2) :
    Bool :=
  (h p).isSome && tbl.ns r k p

/- ING-13: a value's label is its item's under projections and observed otherwise, and its
origin is its item's path under projections and none otherwise. -/
#eval survives (∀ (isItem : Bool) (b : Fin 4) (l ip : Fin 3) (ws : List (Fin 2)),
  ((eval tbl.view tbl.observed (mk isItem b l ip ws)).label == (if isItem then l else 0)
    && (eval tbl.view tbl.observed (mk isItem b l ip ws)).origin
      == (if isItem then some ip else none)) = true) 273

/- Control, ING-13: a construction does not keep the label of what it was built from. -/
#eval refuted (∀ (isItem : Bool) (b : Fin 4) (l ip : Fin 3) (ws : List (Fin 2)),
  ((eval tbl.view tbl.observed (mk isItem b l ip ws)).label == l) = true) 274

/- ING-14: an admitted store whose label is not observed lands an item a source yields, at the
item's own path, with its label, its bytes under the views. -/
#eval survives (∀ (isItem : Bool) (b : Fin 4) (l ip p : Fin 3) (ws : List (Fin 2)) (k : Fin 2),
  okStore tbl 0 (fun _ ↦ none) p .own (mk isItem b l ip ws) k = true →
  (eval tbl.view tbl.observed (mk isItem b l ip ws)).label ≠ 0 →
  firewallOk p (mk isItem b l ip ws) = true) 275

/- Control, ING-14: without R4, an authored item is stored at another path. -/
#eval refuted (∀ (isItem : Bool) (b : Fin 4) (l ip p : Fin 3) (ws : List (Fin 2)) (k : Fin 2),
  okStoreNoOrigin (fun _ ↦ none) p (mk isItem b l ip ws) k = true →
  (eval tbl.view tbl.observed (mk isItem b l ip ws)).label ≠ 0 →
  firewallOk p (mk isItem b l ip ws) = true) 276

/- ING-17: an admitted store at a new path gives it its own identity, the one the item stored
declares, or one held at a path its source no longer has, with the same bytes. -/
#eval survives (∀ (cs : List (Fin 9)) (p nc q i : Fin 3) (b : Fin 4),
  held cs p = none →
  okStore tbl 0 (held cs) p (nm nc q i) (.item ⟨b, 1, p⟩) 1 = true →
  (match landStore tbl (held cs) p (nm nc q i) (.item ⟨b, 1, p⟩) p with
    | some row => decide (row.ident = p)
        || (decide (nc = 1) && decide (q = p) && tbl.declares q i && decide (row.ident = i))
        || (decide (nc = 2) && match held cs q with
            | some rq => decide (rq.bytes = b) && !tbl.has q && decide (row.ident = rq.ident)
            | none => false)
    | none => false) = true) 277

/- Control, ING-17: without R6's condition, an identity is grafted from a path its source still
has. -/
#eval refuted (∀ (cs : List (Fin 9)) (p q : Fin 3) (b : Fin 4),
  held cs p = none → (resolveGraft (held cs) b p (.held q)).isSome = true →
  (match held cs q with | some _ => !tbl.has q | none => true) = true) 278

/- Control, ING-17: without the declaration, a store takes an identity its item does not declare
(the second form's audit: any field of an item, a `ref::`, grafted a note onto another's chain). -/
#eval refuted (∀ (p i : Fin 3),
  (resolveUndeclared (some p) (.prop p i)).isSome = true → tbl.declares p i = true) 287

/- ING-17: an admitted retire of content that came from a source is of a path its source no
longer has. -/
#eval survives (∀ (cs : List (Fin 9)) (p : Fin 3) (k r : Fin 2),
  okRetire tbl r (held cs) p k = true →
  (match held cs p with | some row => !row.sourced || !tbl.has p | none => true) = true) 279

/- Control, ING-17: without R7's condition, an item still in its source is retired. -/
#eval refuted (∀ (cs : List (Fin 9)) (p : Fin 3) (k r : Fin 2),
  okRetireAny r (held cs) p k = true →
  (match held cs p with | some row => !row.sourced || !tbl.has p | none => true) = true) 280

/-- A one-effect plan: a store of a construction, or a retire, at a path. -/
def one (c : Bool) (p : Fin 3) (b : Fin 4) (k : Fin 2) :
    Effect (Fin 4) (Fin 3) (Fin 3) (Fin 3) (Fin 2) (Fin 2) :=
  if c then .store p .own (.make b) k else .retire p k

/- ING-15: a one-effect plan changes a path only at its own path, in the role's namespace for the
effect: its write namespace for a store, its write or retire-only one for a retire. -/
#eval survives (∀ (cs : List (Fin 9)) (c : Bool) (p : Fin 3) (b : Fin 4) (k r : Fin 2),
  (List.finRange 3).all (fun q ↦
    same (landPlan tbl r [one c p b k] (held cs) q) (held cs q)
    || (decide (q = p) && inNamespace tbl r (one c p b k))) = true) 281

/- Control, ING-15: with a retire-only namespace, the statement with one namespace fails: a role
retires a path it does not write (the Ambassador retiring the first form's row). -/
#eval refuted (∀ (cs : List (Fin 9)) (p : Fin 3) (k r : Fin 2),
  (List.finRange 3).all (fun q ↦
    same (landPlan tbl r [.retire p k] (held cs) q) (held cs q)
    || (decide (q = p) && tbl.ns r k q)) = true) 368

/- ING-15: a one-effect plan that leaves an active row it changed stored there, in the role's
write namespace for the store's place, so a retire-only prefix takes no store. -/
#eval survives (∀ (cs : List (Fin 9)) (c : Bool) (p : Fin 3) (b : Fin 4) (l : Fin 3) (k r : Fin 2),
  (List.finRange 3).all (fun q ↦
    match landPlan tbl r [if c then .store p .own (.item ⟨b, l, p⟩) k else .retire p k]
        (held cs) q with
    | some row => !row.active || same (some row) (held cs q)
        || (c && decide (q = p) && tbl.ns r k q)
    | none => true) = true) 369

/- Control, ING-15: a writer without the namespace, every other rule kept, lets a role store an
item at its own path outside the role's prefix. -/
#eval refuted (∀ (cs : List (Fin 9)) (p : Fin 3) (b : Fin 4) (l : Fin 3) (k r : Fin 2),
  okStoreNoNs (held cs) p (.item ⟨b, l, p⟩) k = true → tbl.ns r k p = true) 282

/- Control, ING-15: a writer whose stores take the retire-only namespace too lets a role store an
item at a path it may only retire. -/
#eval refuted (∀ (cs : List (Fin 9)) (p : Fin 3) (b : Fin 4) (l : Fin 3) (k r : Fin 2),
  okStoreRetireNs r (held cs) p (.item ⟨b, l, p⟩) k = true → tbl.ns r k p = true) 370

/- ING-17: a store at a path in a source's space lands an item a source yields, at that path. -/
#eval survives (∀ (isItem : Bool) (b : Fin 4) (l ip p : Fin 3) (ws : List (Fin 2)) (k : Fin 2),
  okStore tbl 0 (fun _ ↦ none) p .own (mk isItem b l ip ws) k = true → tbl.owned p = true →
  (match (mk isItem b l ip ws).root with
    | some i => tbl.yields i && decide (i.path = p)
    | none => false) = true) 283

/- Control, ING-17: without R8, a composed value squats a source's path. -/
#eval refuted (∀ (isItem : Bool) (b : Fin 4) (l ip p : Fin 3) (ws : List (Fin 2)) (k : Fin 2),
  okStoreNoOwner p (mk isItem b l ip ws) k = true → tbl.owned p = true →
  (match (mk isItem b l ip ws).root with
    | some i => tbl.yields i && decide (i.path = p)
    | none => false) = true) 284

/-- The shadow's sources' label sets: path 0's source may give labels 0 or 1, the others only 2,
and an item takes the first of its source's labels the code allows. -/
def srcLabels (i : Item (Fin 4) (Fin 3) (Fin 3)) : Finset (Fin 3) :=
  if i.path = 0 then {0, 1} else {2}

/-- An item whose label its source's rule may give. -/
def mkTyped (isItem : Bool) (b : Fin 4) (pick : Bool) (ip : Fin 3) (ws : List (Fin 2)) :
    Expr (Fin 4) (Fin 3) (Fin 3) (Fin 2) :=
  mk isItem b (if ip = 0 then (if pick then 1 else 0) else 2) ip ws

/- ING-18: a value's label is in its expression's type's label set. -/
#eval survives (∀ (isItem : Bool) (b : Fin 4) (pick : Bool) (ip : Fin 3) (ws : List (Fin 2)),
  decide ((eval tbl.view tbl.observed (mkTyped isItem b pick ip ws)).label
    ∈ labelsOf srcLabels tbl.observed (mkTyped isItem b pick ip ws)) = true) 285

/- Control, ING-18: a type rule that gives a construction no label is unsound. -/
#eval refuted (∀ (isItem : Bool) (b : Fin 4) (pick : Bool) (ip : Fin 3) (ws : List (Fin 2)),
  decide ((eval tbl.view tbl.observed (mkTyped isItem b pick ip ws)).label
    ∈ (if isItem then labelsOf srcLabels tbl.observed (mkTyped isItem b pick ip ws)
       else (∅ : Finset (Fin 3)))) = true) 286

/-- The Ambassador's inbox (dn-ingress-language §E13): path 1 holds the owner's message, which the
source labels authored (1); path 2 the reply, which it labels observed (0); both lie in the source's
space. Path 0 is the Ambassador's own prefix, in a place that takes the authored label, as
`dialogue` does. Every role writes every path, so only the labels and the paths stand between a
script and the owner's row. -/
def inbox : Table (Fin 4) (Fin 3) (Fin 3) (Fin 3) (Fin 2) (Fin 2) (Fin 2) where
  view := view
  observed := 0
  accepts _ l := decide (l ≠ 2)
  ns _ _ _ := true
  rns _ _ _ := false
  owned p := decide (p ≠ 0)
  yields i := (decide (i.path = 1) && decide (i.label = 1))
    || (decide (i.path = 2) && decide (i.label = 0))
  has _ := true
  ofPath p := p
  declares _ _ := false

/-- The owner's message: an item the inbox yields at path 1, with the authored label, and a
value's bytes its bytes under the views. -/
def owners (T : Table (Fin 4) (Fin 3) (Fin 3) (Fin 3) (Fin 2) (Fin 2) (Fin 2))
    (e : Expr (Fin 4) (Fin 3) (Fin 3) (Fin 2)) : Bool :=
  match e.root with
  | some i => T.yields i && decide (i.path = 1) && decide (i.label = 1)
      && decide ((eval T.view T.observed e).bytes = applyViews T.view e.views i.bytes)
  | none => false

/- ING-14 on the inbox: every authored row one store lands, by any role, of any expression, at any
path, is the owner's message at its own path. -/
#eval survives (∀ (isItem : Bool) (b : Fin 4) (l ip p : Fin 3) (ws : List (Fin 2)) (r : Fin 2),
  (match landPlan inbox r [.store p .own (mk isItem b l ip ws) 0] (fun _ ↦ none) p with
   | some row => decide (row.label ≠ 1) || (decide (p = 1) && owners inbox (mk isItem b l ip ws))
   | none => true) = true) 371

/-- What a writer would take if a script could claim a label for what it composes (no expression
can, ING-13): a construction carries the claimed label. -/
def evalClaim (claim : Fin 3) :
    Expr (Fin 4) (Fin 3) (Fin 3) (Fin 2) → Content (Fin 4) (Fin 3) (Fin 3)
  | .item i => ⟨i.bytes, i.label, some i.path⟩
  | .proj w e => ⟨view w (evalClaim claim e).bytes, (evalClaim claim e).label,
      (evalClaim claim e).origin⟩
  | .make b => ⟨b, claim, none⟩

/-- The inbox's writer over claimed labels, every rule of `okStore` kept on a path new to it. -/
def okStoreClaim (claim : Fin 3) (p : Fin 3) (e : Expr (Fin 4) (Fin 3) (Fin 3) (Fin 2)) : Bool :=
  (match e.root with | some i => inbox.yields i | none => true)
    && inbox.accepts 0 (evalClaim claim e).label
    && (match (evalClaim claim e).origin with | some a => decide (a = p) | none => true)
    && (!inbox.owned p || (evalClaim claim e).origin.isSome)

/- Control, ING-13 on the inbox: if a script could claim a label, the Ambassador's text would land
as the owner's at its own prefix, where no source's path and no origin stand in the way. -/
#eval refuted (∀ (claim : Fin 3) (isItem : Bool) (b : Fin 4) (l ip p : Fin 3) (ws : List (Fin 2)),
  okStoreClaim claim p (mk isItem b l ip ws) = true →
  (evalClaim claim (mk isItem b l ip ws)).label = 1 →
  (decide (p = 1) && owners inbox (mk isItem b l ip ws)) = true) 372

/-- The inbox with its rule mutated: the reply labelled as the owner's. -/
def mislabelled : Table (Fin 4) (Fin 3) (Fin 3) (Fin 3) (Fin 2) (Fin 2) (Fin 2) :=
  { inbox with
    yields := fun i ↦ (decide (i.path = 1) || decide (i.path = 2)) && decide (i.label = 1) }

/- Control, ING-14 on the inbox: the firewall holds of the source's rule, whatever it is; a rule
that labels the reply authored lands the reply as the owner's, at the reply's path. -/
#eval refuted (∀ (isItem : Bool) (b : Fin 4) (l ip p : Fin 3) (ws : List (Fin 2)) (r : Fin 2),
  (match landPlan mislabelled r [.store p .own (mk isItem b l ip ws) 0] (fun _ ↦ none) p with
   | some row => decide (row.label ≠ 1) || decide (p = 1)
   | none => true) = true) 373

end Palace.Script.Attack
