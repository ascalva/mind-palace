module

public import Palace.Snapshot
public import PalaceTest.Attack
public meta import Palace.Snapshot
public meta import PalaceTest.Attack

/-!
# Attacks on `Palace.Snapshot`

The Plausible attacks and negative controls for the laws of `Palace/Snapshot.lean`, on the
model's own definitions: stores of two chains over an alphabet of three events, each chain a
list; cuts from two naturals; keyed chains as lists of (key, value) over three keys; chains of
landings and retires from codes in `Fin 9`; grants from two bits and event filters and erasures
from three; reads-from relations as lists of edges between events of the two chains at positions
under four; a digest that reads a chain as a numeral in base four, which is collision free, and
one that adds, which is not. Beside the model the attacks carry one thing the library does not:
an executable resolver, the descent that lowers a frontier until no event inside it has a source
outside, tested against the definition of the greatest consistent cut by enumeration; and, for
the horizon, the positions a chain serves from ten bits, with the greatest consistent cut among
them found by enumeration. The controls are the readings a build must not take: a read at a cut
past the head, the store rewritten in place, generations without their closing stamp, a key's
state taken for unchanged whatever the delta writes, an event filter before the cut, an erasure
that deletes rows, a state served without the seal, the looser seal taken for a monotone one,
kept rows served without their sources, a frontier taken for a cut, an additive digest, a digest
over contents, the pruned store read under its horizon, a frontier lowered to the served
positions without the descent, the floor and the descent each run once in either order, a hole
that loses its key, a chain that others read lowered alone, and each law of growth, order and
composition with its hypothesis dropped or its sides exchanged. The served resolver is
executable here too: the floor and the descent alternated until nothing moves, tested against
the enumeration. So is the row filter: the rows no chain of sources leads outside the cut,
tested against every set of rows of the two chains that lies inside the cut and holds its own
sources; its controls are the filter without its closure, the prefix taken for the filtered
read, and a chain that follows a lowered chain read as asked. They run when this module builds
(`lake test`).
-/

@[expose] public section

namespace Palace.Snapshot.Attack

/-- A store of two chains. -/
def st {γ : Type} (a b : List γ) : Store (Fin 2) γ := fun k ↦ if k = 0 then a else b

/-- A cut of two chains. -/
def cu (m n : ℕ) : Cut (Fin 2) := fun k ↦ if k = 0 then m else n

/-- Two stores of two chains agree. -/
def same {γ : Type} [BEq γ] (s t : Store (Fin 2) γ) : Bool :=
  (List.finRange 2).all fun k ↦ s k == t k

/-- A grant from two bits: the chains it names. -/
def gr (g : Fin 4) (k : Fin 2) : Bool := g.val.testBit k.val

/-- An event filter, or an erasure, from three bits. -/
def pf (c : Fin 8) (a : Fin 3) : Bool := c.val.testBit a.val

/-- A landing or a retire from a code: the key from the residue, `none` (a retire) or a value
from the quotient. -/
def ev (n : Fin 9) : Fin 3 × Option (Fin 2) :=
  (⟨n.val % 3, Nat.mod_lt _ (by decide)⟩,
    match n.val / 3 with
    | 0 => none
    | 1 => some 0
    | _ => some 1)

/-- Generations without the closing stamp: every write a row that never dies. -/
def openRows (l : List (Fin 3 × Fin 3)) : List (Gen (Fin 3) (Fin 3)) :=
  l.zipIdx.map fun x ↦ ⟨x.1.1, x.1.2, x.2 + 1, none⟩

/-- A reads-from edge: the reader's chain and position, then the source's. -/
abbrev Edge := (Fin 2 × Fin 4) × (Fin 2 × Fin 4)

/-- Consistency, decided on a list of edges. -/
def cons (es : List Edge) (c : Cut (Fin 2)) : Bool :=
  es.all fun e ↦ !decide (e.1.2.val < c e.1.1) || decide (e.2.2.val < c e.2.1)

/-- A cut of two chains read off a pair: the descent holds values, not closures. -/
def at2 (c : ℕ × ℕ) (k : Fin 2) : ℕ := if k = 0 then c.1 else c.2

/-- One pass of the descent on one chain: its position lowered to the first event inside it
whose source lies outside the cut. -/
def lowerAt (es : List Edge) (c : ℕ × ℕ) (k : Fin 2) : ℕ :=
  es.foldl (fun n e ↦
    if e.1.1 = k ∧ e.1.2.val < n ∧ ¬e.2.2.val < at2 c e.2.1 then e.1.2.val else n) (at2 c k)

/-- One pass of the descent on both chains. -/
def lower (es : List Edge) (c : ℕ × ℕ) : ℕ × ℕ := (lowerAt es c 0, lowerAt es c 1)

/-- The executable resolver: the descent run from the frontier `(x, y)` until it can lower
nothing more, which is at most as many passes as the frontier has positions. -/
def resolve (es : List Edge) (x y : ℕ) : Cut (Fin 2) :=
  cu ((lower es)^[x + y] (x, y)).1 ((lower es)^[x + y] (x, y)).2

/-- The rows of a generational store as tuples, to compare two of them. -/
def rowsOf (rs : List (Gen (Fin 3) (Fin 3))) : List (Fin 3 × Fin 3 × ℕ × Option ℕ) :=
  rs.map fun r ↦ (r.key, r.val, r.born, r.died)

/-- The positions a chain serves, from ten bits: its empty prefix always, and of the positions
one to five those whose bit is set. -/
def sv (m : Fin 1024) (k : Fin 2) (p : ℕ) : Bool :=
  p == 0 || (decide (p ≤ 5) && m.val.testBit (5 * k.val + p - 1))

/-- The greatest consistent cut under the frontier `(x, y)` among the served positions, by
enumeration: the pointwise maximum of every consistent cut of the grid under the frontier whose
two positions are served. -/
def bestIn (es : List Edge) (p : Fin 2 → ℕ → Bool) (x y : ℕ) : ℕ × ℕ :=
  (List.range 6).foldl (fun (acc : ℕ × ℕ) (u : ℕ) ↦
    (List.range 6).foldl (fun (acc : ℕ × ℕ) (v : ℕ) ↦
      if cons es (cu u v) && p 0 u && p 1 v && decide (u ≤ x) && decide (v ≤ y)
      then (max acc.1 u, max acc.2 v) else acc) acc) (0, 0)

/-- The greatest served position of a chain at or under a position: the frontier lowered to
what is served, before any descent. -/
def floorSv (p : Fin 2 → ℕ → Bool) (k : Fin 2) (x : ℕ) : ℕ :=
  (List.range (x + 1)).foldl (fun (n : ℕ) (q : ℕ) ↦ if p k q then q else n) 0

/-- One round of the served resolver: each chain lowered to the greatest position it serves at
or under its own, then one pass of the descent. -/
def roundIn (es : List Edge) (p : Fin 2 → ℕ → Bool) (c : ℕ × ℕ) : ℕ × ℕ :=
  lower es (floorSv p 0 c.1, floorSv p 1 c.2)

/-- The executable served resolver: the floor and the descent alternated from the frontier
`(x, y)` until nothing moves. A round that moves anything lowers a position, so that is at most
as many rounds as the frontier has positions. -/
def resolveIn (es : List Edge) (p : Fin 2 → ℕ → Bool) (x y : ℕ) : ℕ × ℕ :=
  (roundIn es p)^[x + y] (x, y)

/-- The edges whose source lies in chain 0: with them alone, no event reads chain 1. -/
def into0 (es : List Edge) : List Edge := es.filter fun e ↦ e.2.1 = 0

/-- Chain 0 serves every position and chain 1 the positions of the mask. -/
def sv1 (m : Fin 1024) (k : Fin 2) (q : ℕ) : Bool := k == 0 || sv m 1 q

/-- The edges of a store whose chain 1 is read by itself and by chain 0, and whose chain 0 is
read by itself alone, each chain's own references pointing backward: chain 0 follows chain 1. -/
def foll (es : List Edge) : List Edge :=
  es.filter fun e ↦ (e.1.1 = 0 || e.2.1 = 1) && (e.1.1 != e.2.1 || decide (e.2.2 ≤ e.1.2))

/-- The eight events of two chains of four positions. -/
def evs : List (Fin 2 × Fin 4) := (List.finRange 2).flatMap fun k ↦ (List.finRange 4).map (k, ·)

/-- One pass of the row filter: the rows with a source outside the cut or a source already
withheld. -/
def withholdStep (es : List Edge) (c : ℕ × ℕ) (w : List (Fin 2 × Fin 4)) :
    List (Fin 2 × Fin 4) :=
  evs.filter fun x ↦ es.any fun e ↦
    e.1 == x && (!decide (e.2.2.val < at2 c e.2.1) || w.contains e.2)

/-- The executable row filter: the rows inside the cut that no chain of sources leads outside
it, the pass run as many times as there are rows. -/
def keptRows (es : List Edge) (c : ℕ × ℕ) : List (Fin 2 × Fin 4) :=
  evs.filter fun x ↦
    decide (x.2.val < at2 c x.1) && !((withholdStep es c)^[8] []).contains x

/-- A set of rows from eight bits. -/
def rowSet (m : Fin 256) : List (Fin 2 × Fin 4) :=
  evs.filter fun x ↦ m.val.testBit (4 * x.1.val + x.2.val)

/-- A set of rows lies inside the cut and holds the sources of its rows. -/
def closedIn (es : List Edge) (c : ℕ × ℕ) (t : List (Fin 2 × Fin 4)) : Bool :=
  t.all (fun x ↦ decide (x.2.val < at2 c x.1))
    && es.all fun e ↦ !t.contains e.1 || t.contains e.2

/-- The rows whose own sources lie inside the cut: the filter without its closure. -/
def oneStep (es : List Edge) (c : ℕ × ℕ) : List (Fin 2 × Fin 4) :=
  evs.filter fun x ↦ decide (x.2.val < at2 c x.1)
    && es.all fun e ↦ !(e.1 == x) || decide (e.2.2.val < at2 c e.2.1)

/-- An erasure of keyed writes by their value. -/
def ek (e : Fin 8) (w : Fin 3 × Fin 3) : Bool := pf e w.2

/-- What is shown under the narrower of two grants and the larger of two erasures is the
restriction of what the wider grant is shown under the smaller erasure. -/
def shownNarrow (a b : List (Fin 3)) (m : ℕ) (g g' : Fin 4) (c c' e e' : Fin 8) : Bool :=
  same (shown (fun k ↦ (gr g k && gr g' k) = true) (fun x ↦ pf c x && pf c' x)
      (fun x ↦ pf e x || pf e' x) (st a b) (cu m m))
    (restrict (fun k ↦ (gr g k && gr g' k) = true)
      (fun x ↦ (pf c x && pf c' x) && !(pf e x || pf e' x))
      (shown (fun k ↦ gr g' k = true) (pf c') (pf e') (st a b) (cu m m)))

/-- A collision-free step: the chain read as a numeral in base four, digits one to three. -/
def step4 (h : ℕ) (a : Fin 3) : ℕ := 4 * h + a.val + 1

/-- The additive step, which forgets the order. -/
def stepAdd (h : ℕ) (a : Fin 3) : ℕ := h + a.val + 1

/-- A commitment of an event, and the step that digests commitments. -/
def commit3 (a : Fin 3) : ℕ := a.val + 1

/-- The step over commitments. -/
def stepC (h c : ℕ) : ℕ := 4 * h + c

/-- A step over contents, a hole digested as zero. -/
def stepO (h : ℕ) (o : Option (Fin 3)) : ℕ :=
  4 * h + match o with
    | none => 0
    | some a => a.val + 1

/-- Whether a store of two chains verifies a certificate, decided. -/
def verifies (z : Certificate (Fin 2) ℕ) (s : Store (Fin 2) (Fin 3)) : Bool :=
  (List.finRange 2).all fun k ↦
    decide (z.cut k ≤ (s k).length) && chainDigest step4 0 ((s k).take (z.cut k)) == z.digest k

/- SNP-1: a read at a cut inside the store is the same after any growth. -/
#eval survives (∀ (a b a' b' : List (Fin 3)) (m n : ℕ),
  same (readAt (grow (st a b) (st a' b')) (cu m n ⊓ head (st a b)))
    (readAt (st a b) (cu m n ⊓ head (st a b))) = true) 430

/- Control: a read at a cut past the head changes when the store grows. -/
#eval refuted (∀ (a b a' b' : List (Fin 3)) (m n : ℕ),
  same (readAt (grow (st a b) (st a' b')) (cu m n)) (readAt (st a b) (cu m n)) = true) 431

/- SNP-1: a read between two cuts, the later inside the store, is the same after any growth. -/
#eval survives (∀ (a b t : List (Fin 3)) (i m n : ℕ),
  same (readBetween (grow (st a b) (st t t)) (cu i i) (cu m n ⊓ head (st a b)))
    (readBetween (st a b) (cu i i) (cu m n ⊓ head (st a b))) = true) 432

/- SNP-2: the read at the meet of two cuts is a prefix of the read at either. -/
#eval survives (∀ (a b : List (Fin 3)) (m n i j : ℕ),
  (List.finRange 2).all (fun k ↦
    (readAt (st a b) (cu m n ⊓ cu i j) k).isPrefixOf (readAt (st a b) (cu i j) k)) = true) 433

/- Control: the read at one cut is not a prefix of the read at any other. -/
#eval refuted (∀ (a b : List (Fin 3)) (m n i j : ℕ),
  (List.finRange 2).all (fun k ↦
    (readAt (st a b) (cu m n) k).isPrefixOf (readAt (st a b) (cu i j) k)) = true) 434

/- SNP-2: a cut of a cut is the meet. -/
#eval survives (∀ (a b : List (Fin 3)) (m n i j : ℕ),
  same (readAt (readAt (st a b) (cu m n)) (cu i j)) (readAt (st a b) (cu i j ⊓ cu m n))
    = true) 435

/- SNP-3: the read at `a` followed by the read between `a` and `b` is the read at `b`. -/
#eval survives (∀ (a b : List (Fin 3)) (i j m n : ℕ),
  same (grow (readAt (st a b) (cu i j)) (readBetween (st a b) (cu i j) (cu (i + m) (j + n))))
    (readAt (st a b) (cu (i + m) (j + n))) = true) 436

/- Control: with the two cuts in any order it is not. -/
#eval refuted (∀ (a b : List (Fin 3)) (i j m n : ℕ),
  same (grow (readAt (st a b) (cu i j)) (readBetween (st a b) (cu i j) (cu m n)))
    (readAt (st a b) (cu m n)) = true) 437

/- SNP-3: two adjacent reads-between compose. -/
#eval survives (∀ (a b : List (Fin 3)) (i j m n : ℕ),
  same (grow (readBetween (st a b) (cu i j) (cu (i + m) (j + n)))
      (readBetween (st a b) (cu (i + m) (j + n)) (cu (i + m + n) (j + n + m))))
    (readBetween (st a b) (cu i j) (cu (i + m + n) (j + n + m))) = true) 438

/- SNP-3: a fold continued from a checkpoint over the delta is the fold of the prefix. -/
#eval survives (∀ (a b : List (Fin 3)) (i j m n : ℕ),
  (List.finRange 2).all (fun k ↦
    foldAt step4 (fun _ ↦ 0) (st a b) (cu (i + m) (j + n)) k
      == (readBetween (st a b) (cu i j) (cu (i + m) (j + n)) k).foldl step4
        (foldAt step4 (fun _ ↦ 0) (st a b) (cu i j) k)) = true) 439

/- SNP-4: the read at the head cut, and at any cut past it, is the store. -/
#eval survives (∀ (a b : List (Fin 3)) (m n : ℕ),
  (same (readAt (st a b) (head (st a b))) (st a b)
    && same (readAt (st a b) (head (st a b) + cu m n)) (st a b)) = true) 440

/- SNP-5: the generational store read at a cut is the state recomputed from the prefix. -/
#eval survives (∀ (l : List (Fin 3 × Fin 3)) (c : ℕ) (x : Fin 3),
  (genRead (gens l) c x == stateAt l c x) = true) 441

/- SNP-5: and the last write of the key inside the prefix. -/
#eval survives (∀ (l : List (Fin 3 × Fin 3)) (c : ℕ) (x : Fin 3),
  (lastWrite l c x == stateAt l c x) = true) 442

/- SNP-5: at most one generation of a key is alive at a cut. -/
#eval survives (∀ (l : List (Fin 3 × Fin 3)) (c : ℕ) (x : Fin 3),
  decide (((gens l).filter (selects c x)).length ≤ 1) = true) 443

/- Control: the store rewritten in place is not the state at a cut. -/
#eval refuted (∀ (l : List (Fin 3 × Fin 3)) (c : ℕ) (x : Fin 3),
  (stateOf l x == stateAt l c x) = true) 444

/- Control: generations without the closing stamp read the key's oldest write. -/
#eval refuted (∀ (l : List (Fin 3 × Fin 3)) (c : ℕ) (x : Fin 3),
  (genRead (openRows l) c x == stateAt l c x) = true) 445

/- SNP-1: the generational store read at a cut inside the chain is the same after growth. -/
#eval survives (∀ (l t : List (Fin 3 × Fin 3)) (c : ℕ) (x : Fin 3),
  (genRead (gens (l ++ t)) (min c l.length) x == genRead (gens l) (min c l.length) x)
    = true) 446

/- SNP-3: the state at a later cut is the state at an earlier cut with the writes between. -/
#eval survives (∀ (l : List (Fin 3 × Fin 3)) (a d : ℕ),
  (List.finRange 3).all (fun x ↦
    stateAt l (a + d) x == ((l.take (a + d)).drop a).foldl
      (fun (m : Fin 3 → Option (Fin 3)) (e : Fin 3 × Fin 3) ↦ Function.update m e.1 (some e.2))
      (stateAt l a) x) = true) 447

/- SNP-3: an event read at the later cut was read at the earlier cut or lies in the delta. -/
#eval survives (∀ (a b : List (Fin 3)) (i j m n : ℕ),
  (List.finRange 2).all (fun k ↦
    (readAt (st a b) (cu (i + m) (j + n)) k).all fun x ↦
      (readAt (st a b) (cu i j) k).contains x
        || (readBetween (st a b) (cu i j) (cu (i + m) (j + n)) k).contains x) = true) 475

/- SNP-3: a key the writes between two cuts do not name has the same state at both. -/
#eval survives (∀ (l : List (Fin 3 × Fin 3)) (a d : ℕ) (x : Fin 3),
  (((l.take (a + d)).drop a).any (fun e ↦ e.1 == x)
    || stateAt l (a + d) x == stateAt l a x) = true) 476

/- Control: a key's state at two cuts is not the same whatever the delta writes. -/
#eval refuted (∀ (l : List (Fin 3 × Fin 3)) (a d : ℕ) (x : Fin 3),
  (stateAt l (a + d) x == stateAt l a x) = true) 477

/- SNP-6: a narrower grant's snapshot is the restriction of a wider one's. -/
#eval survives (∀ (a b : List (Fin 3)) (m : ℕ) (g g' : Fin 4) (c c' : Fin 8),
  same (snapshot (fun k ↦ (gr g k && gr g' k) = true) (fun x ↦ pf c x && pf c' x) (st a b)
      (cu m m))
    (restrict (fun k ↦ (gr g k && gr g' k) = true) (fun x ↦ pf c x && pf c' x)
      (snapshot (fun k ↦ gr g' k = true) (pf c') (st a b) (cu m m))) = true) 448

/- Control: an event filter applied before the cut is not the snapshot. -/
#eval refuted (∀ (a b : List (Fin 3)) (m n : ℕ) (g : Fin 4) (c : Fin 8),
  same (readAt (restrict (fun k ↦ gr g k = true) (pf c) (st a b)) (cu m n))
    (snapshot (fun k ↦ gr g k = true) (pf c) (st a b) (cu m n)) = true) 449

/- SNP-6: a snapshot reads only the chains the grant names, and the cut on them. -/
#eval survives (∀ (a b b' : List (Fin 3)) (m n n' : ℕ) (c : Fin 8),
  same (snapshot (fun k ↦ k = 0) (pf c) (st a b) (cu m n))
    (snapshot (fun k ↦ k = 0) (pf c) (st a b') (cu m n')) = true) 450

/- Control: a hidden event before the cut changes the snapshot, though every admitted event
is the same: positions count what an event filter hides. -/
#eval refuted (∀ (a b : List (Fin 3)) (m n : ℕ),
  same (snapshot (fun _ ↦ True) (fun x ↦ x != 0) (st a b) (cu m n))
    (snapshot (fun _ ↦ True) (fun x ↦ x != 0) (st (0 :: a) b) (cu m n)) = true) 451

/- SNP-7: no erased event is visible at any cut. -/
#eval survives (∀ (a b : List (Fin 3)) (m n : ℕ) (e : Fin 8),
  (List.finRange 2).all (fun k ↦
    (visible (pf e) (st a b) (cu m n) k).all fun x ↦ !pf e x) = true) 452

/- SNP-7: the store with holes keeps every position, and reading it commutes with the cut. -/
#eval survives (∀ (a b : List (Fin 3)) (m n : ℕ) (e : Fin 8),
  (same (readAt (redact (pf e) (st a b)) (cu m n)) (redact (pf e) (readAt (st a b) (cu m n)))
    && (List.finRange 2).all fun k ↦
      head (redact (pf e) (st a b)) k == head (st a b) k) = true) 453

/- SNP-7: what is visible is the store with holes read at the cut, the holes dropped. -/
#eval survives (∀ (a b : List (Fin 3)) (m n : ℕ) (e : Fin 8),
  (List.finRange 2).all (fun k ↦ visible (pf e) (st a b) (cu m n) k
    == (readAt (redact (pf e) (st a b)) (cu m n) k).reduceOption) = true) 454

/- Control: after an erasure that deletes rows, a read at a cut holds events from after it. -/
#eval refuted (∀ (a b : List (Fin 3)) (m n : ℕ) (e : Fin 8),
  (List.finRange 2).all (fun k ↦ (readAt (compact (pf e) (st a b)) (cu m n) k).all fun x ↦
    (readAt (st a b) (cu m n) k).contains x) = true) 455

/- SNP-7: once the chain retires a key, no cut before the retire serves it. -/
#eval survives (∀ (l t : List (Fin 9)) (c : ℕ) (x : Fin 3),
  (servedAt (l.map ev ++ (x, none) :: t.map ev) (min c l.length) x == none) = true) 456

/- SNP-7: growth of the chain changes a served value only by removing it. -/
#eval survives (∀ (l t : List (Fin 9)) (c : ℕ) (x : Fin 3),
  ((servedAt (l.map ev ++ t.map ev) (min c l.length) x).isNone
    || servedAt (l.map ev ++ t.map ev) (min c l.length) x
      == servedAt (l.map ev) (min c l.length) x) = true) 457

/- Control: the state at the cut, without the seal, serves a key retired since. -/
#eval refuted (∀ (l t : List (Fin 9)) (c : ℕ) (x : Fin 3),
  ((stateAt (l.map ev ++ t.map ev) (min c l.length) x).join
    == servedAt (l.map ev ++ t.map ev) (min c l.length) x) = true) 458

/- SNP-7: the looser seal serves everything the stricter one serves. -/
#eval survives (∀ (l : List (Fin 9)) (c : ℕ) (x : Fin 3),
  ((servedAt (l.map ev) c x).isNone || servedAt (l.map ev) c x == servedNow (l.map ev) c x)
    = true) 473

/- Control: under the looser seal growth does not only remove: a landing after a retire
brings the key's past back. -/
#eval refuted (∀ (l t : List (Fin 9)) (c : ℕ) (x : Fin 3),
  ((servedNow (l.map ev ++ t.map ev) (min c l.length) x).isNone
    || servedNow (l.map ev ++ t.map ev) (min c l.length) x
      == servedNow (l.map ev) (min c l.length) x) = true) 474

/- SNP-7: a served kept row has no erased source. -/
#eval survives (∀ (rows : List (List (Fin 3) × Fin 2)) (e : Fin 8),
  (serve (pf e) rows).all (fun r ↦ r.1.all fun a ↦ !pf e a) = true) 459

/- Control: the kept rows served as they are hold erased sources. -/
#eval refuted (∀ (rows : List (List (Fin 3) × Fin 2)) (e : Fin 8),
  rows.all (fun r ↦ r.1.all fun a ↦ !pf e a) = true) 460

/- SNP-8: the resolver's cut is consistent, lies under the frontier, and is above every
consistent cut under the frontier (all thirty-six of the grid). -/
#eval survives (∀ (es : List Edge) (x y : Fin 6),
  (cons es (resolve es x.val y.val)
    && decide (resolve es x.val y.val ≤ cu x.val y.val)
    && (List.range 6).all fun u ↦ (List.range 6).all fun v ↦
      !(cons es (cu u v) && decide (cu u v ≤ cu x.val y.val))
        || decide (cu u v ≤ resolve es x.val y.val)) = true) 461

/- Control: the frontier itself is not always consistent. -/
#eval refuted (∀ (es : List Edge) (x y : Fin 6), cons es (cu x.val y.val) = true) 462

/- SNP-8: the meet and the join of two consistent cuts are consistent. -/
#eval survives (∀ (es : List Edge) (x y u v : Fin 6),
  (cons es (resolve es x.val y.val ⊓ resolve es u.val v.val)
    && cons es (resolve es x.val y.val ⊔ resolve es u.val v.val)) = true) 463

/- Control: a consistent cut advanced by one position on a chain is not always consistent. -/
#eval refuted (∀ (es : List Edge) (x y : Fin 6),
  cons es (resolve es x.val y.val + cu 1 0) = true) 464

/- SNP-8: resolution is monotone in the frontier. -/
#eval survives (∀ (es : List Edge) (x y u v : Fin 6),
  decide (resolve es (min x.val u.val) (min y.val v.val) ≤ resolve es x.val y.val)
    = true) 465

/- SNP-9: the certificate of a cut of a store verifies on the store grown. -/
#eval survives (∀ (a b a' b' : List (Fin 3)) (m n : ℕ),
  verifies (certify step4 0 (st a b) (cu m n ⊓ head (st a b))) (grow (st a b) (st a' b'))
    = true) 466

/- SNP-9: under the collision-free step a chain and its reverse have one digest only when
they are one chain. -/
#eval survives (∀ (l : List (Fin 3)),
  (l.reverse == l || chainDigest step4 0 l.reverse != chainDigest step4 0 l) = true) 467

/- Control: under the additive step a chain and its reverse always have one digest. -/
#eval refuted (∀ (l : List (Fin 3)),
  (l.reverse == l || chainDigest stepAdd 0 l.reverse != chainDigest stepAdd 0 l) = true) 468

/- SNP-9: the digest at a later cut is the digest at an earlier cut continued over the
delta. -/
#eval survives (∀ (a b : List (Fin 3)) (i j m n : ℕ),
  (List.finRange 2).all (fun k ↦
    (certify step4 0 (st a b) (cu (i + m) (j + n))).digest k
      == chainDigest step4 ((certify step4 0 (st a b) (cu i j)).digest k)
        (readBetween (st a b) (cu i j) (cu (i + m) (j + n)) k)) = true) 469

/- SNP-9: the meet and the join of two certified cuts are certified from the certificates. -/
#eval survives (∀ (a b : List (Fin 3)) (i j m n : ℕ),
  (List.finRange 2).all (fun k ↦
    ((certify step4 0 (st a b) (cu i j ⊓ cu m n)).digest k
      == if cu i j k ≤ cu m n k then (certify step4 0 (st a b) (cu i j)).digest k
        else (certify step4 0 (st a b) (cu m n)).digest k)
    && (certify step4 0 (st a b) (cu i j ⊔ cu m n)).digest k
      == if cu i j k ≤ cu m n k then (certify step4 0 (st a b) (cu m n)).digest k
        else (certify step4 0 (st a b) (cu i j)).digest k) = true) 470

/- SNP-9: an erasure on a committed store keeps the certificate over its commitments, and
what a reader reads is the store with holes. -/
#eval survives (∀ (a b : List (Fin 3)) (m n : ℕ) (e : Fin 8),
  ((List.finRange 2).all (fun k ↦
      (certify stepC 0 (commitments (purge (pf e) (committed commit3 (st a b)))) (cu m n)).digest k
        == (certify stepC 0 (commitments (committed commit3 (st a b))) (cu m n)).digest k)
    && same (contents (purge (pf e) (committed commit3 (st a b)))) (redact (pf e) (st a b)))
    = true) 471

/- Control: a digest over the contents does not survive an erasure. -/
#eval refuted (∀ (a b : List (Fin 3)) (m n : ℕ) (e : Fin 8),
  (List.finRange 2).all (fun k ↦
    chainDigest stepO 0 ((contents (purge (pf e) (committed commit3 (st a b))) k).take (cu m n k))
      == chainDigest stepO 0 ((contents (committed commit3 (st a b)) k).take (cu m n k)))
    = true) 472

/- SNP-10: the generational store pruned at a horizon reads, at every cut from the horizon on,
the state recomputed from the whole prefix. -/
#eval survives (∀ (l : List (Fin 3 × Fin 3)) (h d : ℕ) (x : Fin 3),
  (genRead (prune h (gens l)) (h + d) x == stateAt l (h + d) x) = true) 478

/- SNP-10: at any cut the pruned store returns nothing or the value the key held there. -/
#eval survives (∀ (l : List (Fin 3 × Fin 3)) (h c : ℕ) (x : Fin 3),
  ((genRead (prune h (gens l)) c x).isNone
    || genRead (prune h (gens l)) c x == stateAt l c x) = true) 479

/- Control: the pruned store read at a cut under its horizon is not the state at the cut. -/
#eval refuted (∀ (l : List (Fin 3 × Fin 3)) (h c : ℕ) (x : Fin 3),
  (genRead (prune h (gens l)) c x == stateAt l c x) = true) 480

/- SNP-10: pruning at two horizons is pruning at the later one. -/
#eval survives (∀ (l : List (Fin 3 × Fin 3)) (h h' : ℕ),
  (rowsOf (prune h (prune h' (gens l))) == rowsOf (prune (max h h') (gens l))) = true) 481

/- SNP-10: among the served positions the greatest consistent cut under a frontier exists: the
pointwise maximum of every consistent served cut under the frontier (all thirty-six of the grid)
is consistent and served. -/
#eval survives (∀ (es : List Edge) (m : Fin 1024) (x y : Fin 6),
  (cons es (at2 (bestIn es (sv m) x.val y.val))
    && sv m 0 (bestIn es (sv m) x.val y.val).1
    && sv m 1 (bestIn es (sv m) x.val y.val).2) = true) 482

/- Control: the frontier lowered to the served positions, without the descent, is not always
consistent. -/
#eval refuted (∀ (es : List Edge) (m : Fin 1024) (x y : Fin 6),
  cons es (cu (floorSv (sv m) 0 x.val) (floorSv (sv m) 1 y.val)) = true) 483

/- SNP-10: the cut read lies under the resolution of the frontier, and under the frontier
lowered to the served positions. -/
#eval survives (∀ (es : List Edge) (m : Fin 1024) (x y : Fin 6),
  (decide (at2 (bestIn es (sv m) x.val y.val) ≤ resolve es x.val y.val)
    && decide ((bestIn es (sv m) x.val y.val).1 ≤ floorSv (sv m) 0 x.val)
    && decide ((bestIn es (sv m) x.val y.val).2 ≤ floorSv (sv m) 1 y.val)) = true) 484

/- SNP-10: the cut read rises with what is served. -/
#eval survives (∀ (es : List Edge) (m m' : Fin 1024) (x y : Fin 6),
  decide (at2 (bestIn es (fun k p ↦ sv m k p && sv m' k p) x.val y.val)
    ≤ at2 (bestIn es (sv m) x.val y.val)) = true) 485

/- SNP-10: when every position is served the cut read is the resolution of the frontier. -/
#eval survives (∀ (es : List Edge) (x y : Fin 6),
  (List.finRange 2).all (fun k ↦
    at2 (bestIn es (fun _ _ ↦ true) x.val y.val) k == resolve es x.val y.val k) = true) 486

/- SNP-10: the served resolver, the floor and the descent alternated until nothing moves,
returns the greatest consistent served cut under the frontier. -/
#eval survives (∀ (es : List Edge) (m : Fin 1024) (x y : Fin 6),
  (resolveIn es (sv m) x.val y.val == bestIn es (sv m) x.val y.val) = true) 492

/- Control: the floor once and then the descent alone does not: the descent leaves the served
positions. -/
#eval refuted (∀ (es : List Edge) (m : Fin 1024) (x y : Fin 6),
  (List.finRange 2).all (fun k ↦
    resolve es (floorSv (sv m) 0 x.val) (floorSv (sv m) 1 y.val) k
      == at2 (bestIn es (sv m) x.val y.val) k) = true) 493

/- Control: nor the descent and then the floor once: the floor breaks consistency again. -/
#eval refuted (∀ (es : List Edge) (m : Fin 1024) (x y : Fin 6),
  ((floorSv (sv m) 0 (resolve es x.val y.val 0), floorSv (sv m) 1 (resolve es x.val y.val 1))
    == bestIn es (sv m) x.val y.val) = true) 494

/- SNP-7: on a keyed chain whose holes keep their keys, the read of a key at a cut is its last
write at or under the cut, a hole when that write is erased, and the three reads agree. -/
#eval survives (∀ (l : List (Fin 3 × Fin 3)) (e : Fin 8) (c : ℕ) (x : Fin 3),
  (stateAt (holes (ek e) l) c x
      == (stateAt l c x).map (fun v ↦ if pf e v then none else some v)
    && genRead (gens (holes (ek e) l)) c x == stateAt (holes (ek e) l) c x
    && lastWrite (holes (ek e) l) c x == stateAt (holes (ek e) l) c x) = true) 495

/- Control: a seek over the rows of the prefix that kept their key returns a superseded
version where the head is a hole. -/
#eval refuted (∀ (l : List (Fin 3 × Fin 3)) (e : Fin 8) (c : ℕ) (x : Fin 3),
  ((stateOf ((l.take c).filter fun w ↦ !ek e w) x).map some
    == stateAt (holes (ek e) l) c x) = true) 496

/- Control: a seek over the chain with its holes deleted returns a version from after the
cut. -/
#eval refuted (∀ (l : List (Fin 3 × Fin 3)) (e : Fin 8) (c : ℕ) (x : Fin 3),
  ((lastWrite (l.filter fun w ↦ !ek e w) c x).map some
    == stateAt (holes (ek e) l) c x) = true) 497

/- SNP-10: a chain that no event reads is lowered alone. From a consistent frontier, with
chain 0 serving every position, the cut read is the frontier with chain 1 at the greatest
position it serves. -/
#eval survives (∀ (es : List Edge) (m : Fin 1024) (x y : Fin 6),
  (bestIn (into0 es) (sv1 m) (resolve (into0 es) x.val y.val 0) (resolve (into0 es) x.val y.val 1)
    == (resolve (into0 es) x.val y.val 0,
      floorSv (sv1 m) 1 (resolve (into0 es) x.val y.val 1))) = true) 498

/- Control: when events may read chain 1, lowering it alone is not the cut read. -/
#eval refuted (∀ (es : List Edge) (m : Fin 1024) (x y : Fin 6),
  (bestIn es (sv1 m) (resolve es x.val y.val 0) (resolve es x.val y.val 1)
    == (resolve es x.val y.val 0, floorSv (sv1 m) 1 (resolve es x.val y.val 1))) = true) 499

/- SNP-6, SNP-7: under a narrower grant and a larger erasure, what is shown is the restriction
of what the wider grant is shown under the smaller erasure. -/
#eval survives (∀ (a b : List (Fin 3)) (m : ℕ) (g g' : Fin 4) (c c' e e' : Fin 8),
  shownNarrow a b m g g' c c' e e' = true) 509

/- SNP-7: and it holds no erased event. -/
#eval survives (∀ (a b : List (Fin 3)) (m n : ℕ) (g : Fin 4) (c e : Fin 8),
  (List.finRange 2).all (fun k ↦
    (shown (fun k ↦ gr g k = true) (pf c) (pf e) (st a b) (cu m n) k).all fun x ↦ !pf e x)
    = true) 511

/- Control: under a smaller erasure the narrower grant is shown more than that restriction. -/
#eval refuted (∀ (a b : List (Fin 3)) (m : ℕ) (g g' : Fin 4) (c c' e e' : Fin 8),
  same (shown (fun k ↦ (gr g k && gr g' k) = true) (fun x ↦ pf c x && pf c' x) (pf e) (st a b)
      (cu m m))
    (restrict (fun k ↦ (gr g k && gr g' k) = true) (fun x ↦ (pf c x && pf c' x) && !pf e x)
      (shown (fun k ↦ gr g' k = true) (pf c') (fun x ↦ pf e x || pf e' x) (st a b) (cu m m)))
    = true) 510

/- SNP-7: the history served of a key at a cut ends at the value served there, and after a
retire of the key it holds no version landed before the retire. -/
#eval survives (∀ (l t : List (Fin 9)) (c : ℕ) (x : Fin 3),
  ((historyAt (l.map ev) c x).getLast? == servedAt (l.map ev) c x
    && historyAt (l.map ev ++ (x, none) :: t.map ev) (l.length + 1 + c) x
      == if sealedAt (l.map ev ++ (x, none) :: t.map ev) (l.length + 1 + c) x then []
        else sinceRetire ((t.map ev).take c) x) = true) 512

/- Control: the versions of a key inside the cut, without the seal, hold versions landed
before a retire. -/
#eval refuted (∀ (l : List (Fin 9)) (c : ℕ) (x : Fin 3),
  (((l.map ev).take c).filterMap (fun e ↦ if e.1 = x then e.2 else none)
    == historyAt (l.map ev) c x) = true) 513

/- Control for 432: a read between two cuts, the later past the head, changes with growth. -/
#eval refuted (∀ (a b t : List (Fin 3)) (i m n : ℕ),
  same (readBetween (grow (st a b) (st t t)) (cu i i) (cu m n))
    (readBetween (st a b) (cu i i) (cu m n)) = true) 487

/- Control for 446: the generational store read at a cut past the old head changes with
growth. -/
#eval refuted (∀ (l t : List (Fin 3 × Fin 3)) (c : ℕ) (x : Fin 3),
  (genRead (gens (l ++ t)) c x == genRead (gens l) c x) = true) 488

/- Control for 466: the certificate of a cut past the head does not verify on the store
grown. -/
#eval refuted (∀ (a b a' b' : List (Fin 3)) (m n : ℕ),
  verifies (certify step4 0 (st a b) (cu m n)) (grow (st a b) (st a' b')) = true) 489

/- Control for 465: resolution does not fall as the frontier rises. -/
#eval refuted (∀ (es : List Edge) (x y u v : Fin 6),
  decide (resolve es x.val y.val ≤ resolve es (min x.val u.val) (min y.val v.val))
    = true) 490

/- Control for 481: pruning at two horizons is not pruning at the earlier one. -/
#eval refuted (∀ (l : List (Fin 3 × Fin 3)) (h h' : ℕ),
  (rowsOf (prune h (prune h' (gens l))) == rowsOf (prune (min h h') (gens l))) = true) 491

/- Control for 435: a cut of a cut is not the join. -/
#eval refuted (∀ (a b : List (Fin 3)) (m n i j : ℕ),
  same (readAt (readAt (st a b) (cu m n)) (cu i j)) (readAt (st a b) (cu i j ⊔ cu m n))
    = true) 500

/- Control for 440: the read at a cut that is not the head is not the store. -/
#eval refuted (∀ (a b : List (Fin 3)) (m n : ℕ),
  same (readAt (st a b) (cu m n)) (st a b) = true) 501

/- Control for 438: two adjacent reads-between do not compose in the other order. -/
#eval refuted (∀ (a b : List (Fin 3)) (i j m n : ℕ),
  same (grow (readBetween (st a b) (cu (i + m) (j + n)) (cu (i + m + n) (j + n + m)))
      (readBetween (st a b) (cu i j) (cu (i + m) (j + n))))
    (readBetween (st a b) (cu i j) (cu (i + m + n) (j + n + m))) = true) 502

/- Control for 439 and 469: the fold at a later cut is not the fold at the earlier one: the
delta counts. -/
#eval refuted (∀ (a b : List (Fin 3)) (i j m n : ℕ),
  (List.finRange 2).all (fun k ↦
    (certify step4 0 (st a b) (cu (i + m) (j + n))).digest k
      == (certify step4 0 (st a b) (cu i j)).digest k) = true) 503

/- Control for 470: the meet of two certified cuts does not take, chain by chain, the later
digest. -/
#eval refuted (∀ (a b : List (Fin 3)) (i j m n : ℕ),
  (List.finRange 2).all (fun k ↦
    (certify step4 0 (st a b) (cu i j ⊓ cu m n)).digest k
      == if cu i j k ≤ cu m n k then (certify step4 0 (st a b) (cu m n)).digest k
        else (certify step4 0 (st a b) (cu i j)).digest k) = true) 504

/- Control for 447 and 475: an event read at the later cut was not always read at the
earlier. -/
#eval refuted (∀ (a b : List (Fin 3)) (i j m n : ℕ),
  (List.finRange 2).all (fun k ↦
    decide ((readAt (st a b) (cu (i + m) (j + n)) k).length
      ≤ (readAt (st a b) (cu i j) k).length)) = true) 505

/- Control for 484: the cut read does not always reach the frontier lowered to the served
positions. -/
#eval refuted (∀ (es : List Edge) (m : Fin 1024) (x y : Fin 6),
  (decide (floorSv (sv m) 0 x.val ≤ (bestIn es (sv m) x.val y.val).1)
    && decide (floorSv (sv m) 1 y.val ≤ (bestIn es (sv m) x.val y.val).2)) = true) 506

/- Control for 485: the cut read does not rise when less is served. -/
#eval refuted (∀ (es : List Edge) (m m' : Fin 1024) (x y : Fin 6),
  decide (at2 (bestIn es (sv m) x.val y.val)
    ≤ at2 (bestIn es (fun k p ↦ sv m k p && sv m' k p) x.val y.val)) = true) 507

/- Control for 486: when not every position is served the cut read is not the resolution of
the frontier. -/
#eval refuted (∀ (es : List Edge) (m : Fin 1024) (x y : Fin 6),
  (List.finRange 2).all (fun k ↦
    at2 (bestIn es (sv m) x.val y.val) k == resolve es x.val y.val k) = true) 508

/- SNP-8: the filtered read is closed, and it is the greatest closed set of rows inside the
cut: every such set lies in it. -/
#eval survives (∀ (es : List Edge) (x y : Fin 6) (m : Fin 256),
  (closedIn es (x.val, y.val) (keptRows es (x.val, y.val))
    && (!closedIn es (x.val, y.val) (rowSet m)
      || (rowSet m).all fun r ↦ (keptRows es (x.val, y.val)).contains r)) = true) 514

/- SNP-2: a row kept at a cut is kept at every later cut. -/
#eval survives (∀ (es : List Edge) (x y u v : Fin 6),
  ((keptRows es (min x.val u.val, min y.val v.val)).all fun r ↦
    (keptRows es (x.val, y.val)).contains r) = true) 515

/- SNP-8: at a consistent cut the filter withholds nothing. -/
#eval survives (∀ (es : List Edge) (x y : Fin 6),
  (keptRows es (resolve es x.val y.val 0, resolve es x.val y.val 1)
    == evs.filter fun r ↦ decide (r.2.val < resolve es x.val y.val r.1)) = true) 516

/- Control: the rows whose own sources lie inside the cut are not closed: a row is withheld
through a source that is withheld. -/
#eval refuted (∀ (es : List Edge) (x y : Fin 6),
  closedIn es (x.val, y.val) (oneStep es (x.val, y.val)) = true) 517

/- Control: at a cut that is not consistent the prefix is not the filtered read. -/
#eval refuted (∀ (es : List Edge) (x y : Fin 6),
  (keptRows es (x.val, y.val) == evs.filter fun r ↦ decide (r.2.val < at2 (x.val, y.val) r.1))
    = true) 518

/- SNP-10: a chain that reads a lowered chain follows it. Chain 1 is read by itself and by
chain 0, chain 0 by itself alone. From a consistent frontier the cut read has chain 1 at the
greatest position it serves and chain 0 at the first of its events that reads chain 1 past
that position. -/
#eval survives (∀ (es : List Edge) (m : Fin 1024) (x y : Fin 6),
  (bestIn (foll es) (sv1 m) (resolve (foll es) x.val y.val 0) (resolve (foll es) x.val y.val 1)
    == (lowerAt (foll es) (resolve (foll es) x.val y.val 0,
        floorSv (sv1 m) 1 (resolve (foll es) x.val y.val 1)) 0,
      floorSv (sv1 m) 1 (resolve (foll es) x.val y.val 1))) = true) 519

/- Control: the chain that follows is not read as asked. -/
#eval refuted (∀ (es : List Edge) (m : Fin 1024) (x y : Fin 6),
  (bestIn (foll es) (sv1 m) (resolve (foll es) x.val y.val 0) (resolve (foll es) x.val y.val 1)
    == (resolve (foll es) x.val y.val 0,
      floorSv (sv1 m) 1 (resolve (foll es) x.val y.val 1))) = true) 520

end Palace.Snapshot.Attack
