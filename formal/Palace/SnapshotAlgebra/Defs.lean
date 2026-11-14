module

public import Palace.Snapshot.Defs
public import Mathlib.Order.Sublattice

/-!
# The algebra of cuts: the model

dn-temporal-snapshot §4.4, on the model of `Palace/Snapshot/Defs.lean`. A cut is a value, one
position a chain, and it stands for what the store held as of it; nothing is read until an
operation needs it. Two kinds of operation act on cuts.

**On positions.** The cuts inside a store are a lattice under the pointwise meet and join, with
the empty cut at the bottom and the head at the top (`cutsIn`); the result of a meet or a join is
a cut again, and the difference of two cuts is the events between them (`readBetween`, from the
model of the reads).

**On contents.** A chain of keyed writes kept by generation (`gens`) has one row a write, alive
from the cut that contains it up to the cut that contains its key's next write. What a cut holds
is the rows alive at it (`contentAt`). A set of rows is named and not read: `Held` is an
expression over the contents of cuts, closed under union, intersection and difference, and it has
no complement, so every set it names lies inside the contents of the cuts it names. Whether a row
is in the set is a function of the row's position and its closing stamp alone (`Held.has`); the
rows are read when the set is materialized (`Held.rows`), chain by chain for a store
(`Held.across`). The signed difference of two cuts is two such sets, what the first holds and the
second does not and the converse (`Held.gone`, `Held.come`), sorted by key into the rows removed,
added and replaced (`removedOf`, `addedOf`, `replacedOf`). A family of cuts gives what every cut
of it holds, what some cut holds and in how many a row is alive (`Held.all`, `Held.any`,
`countIn`).

A row that carries no version, the tombstone of a retire or the hole an erasure leaves, is a row
whose value is `none`: it closes the row before it and is in no cut's versions (`versionsAt`).

An operator reads a cut through one interface: a function of one cut's read (`view`, in the model
of the reads), of two (`combine`), a measure at each cut of a family (`series`) and a fold over
one (`foldOver`).
-/

@[expose] public section

namespace Palace.Snapshot

/-! ### What a cut holds -/

section Held

variable {κ β γ : Type*}

/-- The event a row records: its key, its value and its position. The closing stamp is left out:
it is the one field written after the row, and it is a function of the rows. -/
def Gen.event (r : Gen κ β) : κ × β × ℕ := (r.key, r.val, r.born)

/-- A row is well formed when its closing stamp, if it has one, lies past its position: it is
alive at one cut at least. -/
def Gen.Proper (r : Gen κ β) : Prop := ∀ d, r.died = some d → r.born < d

/-- What a cut holds on one chain: the rows alive at it, every key at once. -/
def contentAt (rs : List (Gen κ β)) (c : ℕ) : List (Gen κ β) := rs.filter fun r ↦ r.aliveAt c

/-- A set of rows, named and not read: the contents of a cut, or the union, the intersection or
the difference of two such sets. There is no complement: a set lies inside the contents of the
cuts it names. `γ` is what names a cut, a position on one chain or a cut of a store. -/
inductive Held (γ : Type*) where
  /-- What the cut holds. -/
  | cut (c : γ) : Held γ
  /-- What either set holds. -/
  | union (p q : Held γ) : Held γ
  /-- What both sets hold. -/
  | inter (p q : Held γ) : Held γ
  /-- What the first set holds and the second does not. -/
  | diff (p q : Held γ) : Held γ

namespace Held

/-- Whether a row is in the set, on the chain where the cut named `c` stands at `pos c`. It
reads the row's position and its closing stamp and nothing else. -/
def has (pos : γ → ℕ) : Held γ → Gen κ β → Bool
  | cut c, r => r.aliveAt (pos c)
  | union p q, r => p.has pos r || q.has pos r
  | inter p q, r => p.has pos r && q.has pos r
  | diff p q, r => p.has pos r && !q.has pos r

/-- The cuts a set names. -/
def atoms : Held γ → List γ
  | cut c => [c]
  | union p q => p.atoms ++ q.atoms
  | inter p q => p.atoms ++ q.atoms
  | diff p q => p.atoms ++ q.atoms

/-- The set read on one chain: the rows of the chain that are in it. -/
def rows (pos : γ → ℕ) (e : Held γ) (rs : List (Gen κ β)) : List (Gen κ β) :=
  rs.filter (e.has pos)

/-- The set read on a store, chain by chain, each chain at the cuts' positions on it. -/
def across {K : Type*} (pos : γ → Cut K) (e : Held γ) (R : K → List (Gen κ β)) :
    Store K (Gen κ β) :=
  fun k ↦ (R k).filter (e.has fun c ↦ pos c k)

/-- What exactly one of two sets holds. -/
def symm (p q : Held γ) : Held γ := union (diff p q) (diff q p)

/-- The rows the cut `a` holds and the cut `b` does not: one side of the signed difference. -/
def gone (a b : γ) : Held γ := diff (cut a) (cut b)

/-- The rows the cut `b` holds and the cut `a` does not: the other side. -/
def come (a b : γ) : Held γ := diff (cut b) (cut a)

/-- The rows both cuts hold. -/
def kept (a b : γ) : Held γ := inter (cut a) (cut b)

/-- What every cut of a family holds, the family given as one cut and the rest. -/
def all (c : γ) (F : List γ) : Held γ := F.foldl (fun e d ↦ inter e (cut d)) (cut c)

/-- What some cut of a family holds. -/
def any (c : γ) (F : List γ) : Held γ := F.foldl (fun e d ↦ union e (cut d)) (cut c)

end Held

/-- In how many cuts of a family a row is alive. -/
def countIn (F : List ℕ) (r : Gen κ β) : ℕ := F.countP fun c ↦ r.aliveAt c

/-- A row that carries a version: a landing, and no tombstone and no hole. -/
def Gen.isVersion (r : Gen κ (Option β)) : Bool := r.val.isSome

/-- The versions a cut holds on a chain of landings, tombstones and holes: the rows alive at the
cut that carry one. -/
def versionsAt (rs : List (Gen κ (Option β))) (c : ℕ) : List (Gen κ (Option β)) :=
  (contentAt rs c).filter Gen.isVersion

/-- The rows of the first side of a signed difference whose key has no row on the second: the
keys removed. -/
def removedOf [DecidableEq κ] (gone come : List (Gen κ β)) : List (Gen κ β) :=
  gone.filter fun r ↦ !come.any fun r' ↦ decide (r'.key = r.key)

/-- The rows of the second side whose key has no row on the first: the keys added. -/
def addedOf [DecidableEq κ] (gone come : List (Gen κ β)) : List (Gen κ β) :=
  come.filter fun r' ↦ !gone.any fun r ↦ decide (r.key = r'.key)

/-- The pairs of a row of the first side and the row of its key on the second: the keys whose
row was replaced by another. -/
def replacedOf [DecidableEq κ] (gone come : List (Gen κ β)) : List (Gen κ β × Gen κ β) :=
  gone.filterMap fun r ↦ (come.find? fun r' ↦ decide (r'.key = r.key)).map fun r' ↦ (r, r')

end Held

/-! ### The positions, and the interface an operator reads through -/

section Interface

variable {K α β : Type*}

/-- The cuts inside a store, as a sublattice of the cuts: closed under the pointwise meet and
join, with the empty cut at the bottom and the head at the top. -/
def cutsIn (s : Store K α) : Sublattice (Cut K) where
  carrier := {c | c ≤ head s}
  supClosed' := fun a ha b hb ↦ show a ⊔ b ≤ head s from sup_le ha hb
  infClosed' := fun a ha b _ ↦ show a ⊓ b ≤ head s from le_trans inf_le_left ha

/-- The cuts every position of which its chain serves, as a sublattice of the cuts, whatever the
chains serve: on one chain the meet and the join of two positions are each one of the two. -/
def servedCuts (S : K → Set ℕ) : Sublattice (Cut K) where
  carrier := {c | ∀ k, c k ∈ S k}
  supClosed' := fun a ha b hb k ↦ show a k ⊔ b k ∈ S k from
    (le_total (a k) (b k)).elim (fun h ↦ (sup_of_le_right h).symm ▸ hb k)
      fun h ↦ (sup_of_le_left h).symm ▸ ha k
  infClosed' := fun a ha b hb k ↦ show a k ⊓ b k ∈ S k from
    (le_total (a k) (b k)).elim (fun h ↦ (inf_of_le_left h).symm ▸ ha k)
      fun h ↦ (inf_of_le_right h).symm ▸ hb k

/-- A function of two cuts' reads: the form a difference, a velocity and every comparison of two
cuts take. -/
def combine (f : Store K α → Store K α → β) (s : Store K α) (a b : Cut K) : β :=
  f (readAt s a) (readAt s b)

/-- A measure at each cut of a family: a derived view, cut by cut. -/
def series (D : Store K α → β) (s : Store K α) (F : List (Cut K)) : List β := F.map (view D s)

/-- A fold over the cuts of a family, each read in its turn. -/
def foldOver (g : β → Store K α → β) (init : β) (s : Store K α) (F : List (Cut K)) : β :=
  F.foldl (fun acc c ↦ g acc (readAt s c)) init

end Interface

end Palace.Snapshot
