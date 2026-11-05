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
label), two roles (0 writes everywhere, 1 only at path 2), paths 0 and 1 in sources' spaces and path
2 free, sources that yield items at paths 1 and 2 and no longer have path 0. Each control is a
writer with one rule taken out: without R4 an item is stored at another path (DOR-14), without R8 a
composed value squats a source's path, without the namespace a role writes outside its prefix
(DOR-15), without R6's condition an identity is grafted from a path its source still has, without
R7's an item still in its source is retired (DOR-17), and a construction claimed to keep its inputs'
label is refuted (DOR-13). They run when this module builds (`lake test`).
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
  owned p := decide (p ≠ 2)
  yields i := decide (i.path ≠ 0)
  has p := decide (p ≠ 0)
  ofPath p := p

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
def nm (c : Fin 3) (q : Fin 3) : Naming (Fin 3) (Fin 3) :=
  match c with
  | 0 => .own
  | 1 => .prop q q
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

/-- R7 without its condition: any held path in the namespace may be retired. -/
def okRetireAny (r : Fin 2) (h : Held (Fin 3) (Fin 4) (Fin 3) (Fin 3)) (p : Fin 3) (k : Fin 2) :
    Bool :=
  (h p).isSome && tbl.ns r k p

/-- The writer without the namespace: a role stores anywhere. -/
def stepNoNs (h : Held (Fin 3) (Fin 4) (Fin 3) (Fin 3)) (p : Fin 3) (b : Fin 4) (k : Fin 2) :
    Held (Fin 3) (Fin 4) (Fin 3) (Fin 3) :=
  if tbl.accepts k 0 then landStore tbl h p .own (.make b) else h

/- DOR-13: a value's label is its item's under projections and observed otherwise, and its
origin is its item's path under projections and none otherwise. -/
#eval survives (∀ (isItem : Bool) (b : Fin 4) (l ip : Fin 3) (ws : List (Fin 2)),
  ((eval tbl.view tbl.observed (mk isItem b l ip ws)).label == (if isItem then l else 0)
    && (eval tbl.view tbl.observed (mk isItem b l ip ws)).origin
      == (if isItem then some ip else none)) = true) 273

/- Control, DOR-13: a construction does not keep the label of what it was built from. -/
#eval refuted (∀ (isItem : Bool) (b : Fin 4) (l ip : Fin 3) (ws : List (Fin 2)),
  ((eval tbl.view tbl.observed (mk isItem b l ip ws)).label == l) = true) 274

/- DOR-14: an admitted store whose label is not observed lands an item a source yields, at the
item's own path, with its label, its bytes under the views. -/
#eval survives (∀ (isItem : Bool) (b : Fin 4) (l ip p : Fin 3) (ws : List (Fin 2)) (k : Fin 2),
  okStore tbl 0 (fun _ ↦ none) p .own (mk isItem b l ip ws) k = true →
  (eval tbl.view tbl.observed (mk isItem b l ip ws)).label ≠ 0 →
  firewallOk p (mk isItem b l ip ws) = true) 275

/- Control, DOR-14: without R4, an authored item is stored at another path. -/
#eval refuted (∀ (isItem : Bool) (b : Fin 4) (l ip p : Fin 3) (ws : List (Fin 2)) (k : Fin 2),
  okStoreNoOrigin (fun _ ↦ none) p (mk isItem b l ip ws) k = true →
  (eval tbl.view tbl.observed (mk isItem b l ip ws)).label ≠ 0 →
  firewallOk p (mk isItem b l ip ws) = true) 276

/- DOR-17: an admitted store at a new path gives it its own identity, one read off the item
stored, or one held at a path its source no longer has, with the same bytes. -/
#eval survives (∀ (cs : List (Fin 9)) (p nc q : Fin 3) (b : Fin 4) (l : Fin 3),
  held cs p = none →
  okStore tbl 0 (held cs) p (nm nc q) (.item ⟨b, l, p⟩) 1 = true →
  (match landStore tbl (held cs) p (nm nc q) (.item ⟨b, l, p⟩) p with
    | some row => decide (row.ident = p)
        || (decide (nc = 1) && decide (q = p) && decide (row.ident = q))
        || (decide (nc = 2) && match held cs q with
            | some rq => decide (rq.bytes = b) && !tbl.has q && decide (row.ident = rq.ident)
            | none => false)
    | none => false) = true) 277

/- Control, DOR-17: without R6's condition, an identity is grafted from a path its source still
has. -/
#eval refuted (∀ (cs : List (Fin 9)) (p q : Fin 3) (b : Fin 4),
  held cs p = none → (resolveGraft (held cs) b p (.held q)).isSome = true →
  (match held cs q with | some _ => !tbl.has q | none => true) = true) 278

/- DOR-17: an admitted retire of content that came from a source is of a path its source no
longer has. -/
#eval survives (∀ (cs : List (Fin 9)) (p : Fin 3) (k r : Fin 2),
  okRetire tbl r (held cs) p k = true →
  (match held cs p with | some row => !row.sourced || !tbl.has p | none => true) = true) 279

/- Control, DOR-17: without R7's condition, an item still in its source is retired. -/
#eval refuted (∀ (cs : List (Fin 9)) (p : Fin 3) (k r : Fin 2),
  okRetireAny r (held cs) p k = true →
  (match held cs p with | some row => !row.sourced || !tbl.has p | none => true) = true) 280

/- DOR-15: a one-effect plan changes a path only at its own path, in the role's namespace. -/
#eval survives (∀ (cs : List (Fin 9)) (c : Bool) (p : Fin 3) (b : Fin 4) (k r : Fin 2),
  (List.finRange 3).all (fun q ↦
    same (landPlan tbl r [if c then .store p .own (.make b) k else .retire p k] (held cs) q)
      (held cs q)
    || (decide (q = p) && tbl.ns r k q)) = true) 281

/- Control, DOR-15: a writer without the namespace lets a role store outside its prefix. -/
#eval refuted (∀ (cs : List (Fin 9)) (p : Fin 3) (b : Fin 4) (k r : Fin 2),
  (List.finRange 3).all (fun q ↦
    same ((if r = 0 then landPlan tbl r [.store p .own (.make b) k] (held cs)
           else stepNoNs (held cs) p b k) q) (held cs q)
    || (decide (q = p) && tbl.ns r k q)) = true) 282

/- DOR-17: a store at a path in a source's space lands an item a source yields, at that path. -/
#eval survives (∀ (isItem : Bool) (b : Fin 4) (l ip p : Fin 3) (ws : List (Fin 2)) (k : Fin 2),
  okStore tbl 0 (fun _ ↦ none) p .own (mk isItem b l ip ws) k = true → tbl.owned p = true →
  (match (mk isItem b l ip ws).root with
    | some i => tbl.yields i && decide (i.path = p)
    | none => false) = true) 283

/- Control, DOR-17: without R8, a composed value squats a source's path. -/
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

/- DOR-18: a value's label is in its expression's type's label set. -/
#eval survives (∀ (isItem : Bool) (b : Fin 4) (pick : Bool) (ip : Fin 3) (ws : List (Fin 2)),
  decide ((eval tbl.view tbl.observed (mkTyped isItem b pick ip ws)).label
    ∈ labelsOf srcLabels tbl.observed (mkTyped isItem b pick ip ws)) = true) 285

/- Control, DOR-18: a type rule that gives a construction no label is unsound. -/
#eval refuted (∀ (isItem : Bool) (b : Fin 4) (pick : Bool) (ip : Fin 3) (ws : List (Fin 2)),
  decide ((eval tbl.view tbl.observed (mkTyped isItem b pick ip ws)).label
    ∈ (if isItem then labelsOf srcLabels tbl.observed (mkTyped isItem b pick ip ws)
       else (∅ : Finset (Fin 3)))) = true) 286

end Palace.Script.Attack
