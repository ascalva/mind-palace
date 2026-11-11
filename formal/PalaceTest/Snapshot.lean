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
outside, tested against the definition of the greatest consistent cut by enumeration. The
controls are the readings a build must not take: a read at a cut past the head, the store
rewritten in place, generations without their closing stamp, an event filter before the cut, an
erasure that deletes rows, a state served without the seal, the looser seal taken for a
monotone one, kept rows served without their sources, a frontier taken for a cut, an additive digest, a digest over contents. They run when
this module builds (`lake test`).
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

end Palace.Snapshot.Attack
