module

public import Palace.SnapshotAlgebra
public import PalaceTest.Attack
public import PalaceTest.Snapshot
public meta import Palace.SnapshotAlgebra
public meta import PalaceTest.Attack
public meta import PalaceTest.Snapshot

/-!
# Attacks on `Palace.SnapshotAlgebra`

The Plausible attacks and negative controls for the algebra of cuts, on the model's own
definitions and with the helpers of `PalaceTest/Snapshot.lean`: stores of two chains, cuts from
two naturals, keyed chains as lists of (key, value) over three keys, chains of landings and
retires from codes, grants from two bits and row tests and erasures from three. A set of rows is
built from a program, each step pushing what a cut holds or combining the two sets on top of the
stack, so the attacks draw sets of any shape. Beside the model the attacks carry an oracle the
library does not define: the set an expression names computed by list operations on what its
cuts hold, row by row, against which the lazy membership is tested. The controls are the
readings a build must not take: the read at the join taken for the read at the meet, a
difference taken for symmetric, a value taken to live on an interval as a row does, the rows
come taken for every row stored between two cuts, what some cut of a family holds taken for
what a range of positions holds, a composition through a cut outside the two, a count that
forgets the rows gone, the events between two cuts taken for the signed difference, sets
computed on values and not on rows, a set at cuts past the head taken for append invariant, the
closing stamps taken for part of what a cut held, a row's test applied before the generations
are computed, the two meanings of union taken for one, a set read without the grant's
restriction, an erasure that deletes rows, and a hole taken for a version. They run when this
module builds (`lake test`).
-/

@[expose] public section

namespace Palace.Snapshot.Attack

/-- A row as a tuple, its closing stamp included. -/
def rowT (r : Gen (Fin 3) (Fin 3)) : Fin 3 × Fin 3 × ℕ × Option ℕ := (r.key, r.val, r.born, r.died)

/-- One step of a program on a stack of sets: push what a cut holds, or combine the two sets on
top. -/
def stepSet {γ : Type} (op : Fin 4) (c : γ) (stack : List (Held γ)) : List (Held γ) :=
  match op.val, stack with
  | 1, q :: p :: rest => Held.union p q :: rest
  | 2, q :: p :: rest => Held.inter p q :: rest
  | 3, q :: p :: rest => Held.diff p q :: rest
  | _, stack => Held.cut c :: stack

/-- A set of rows from a program over the cuts of one chain: the top of the stack after at most
twelve steps. -/
def build (prog : List (Fin 4 × Fin 32)) : Held ℕ :=
  ((prog.take 12).foldl (fun stack i ↦ stepSet i.1 i.2.val stack) []).headD (Held.cut 0)

/-- The same with every cut at or under a position. -/
def buildAt (n : ℕ) (prog : List (Fin 4 × Fin 32)) : Held ℕ :=
  ((prog.take 12).foldl (fun stack i ↦ stepSet i.1 (min i.2.val n) stack) []).headD (Held.cut 0)

/-- A set of rows from a program over the cuts of a store of two chains. -/
def build2 (prog : List (Fin 4 × Fin 32 × Fin 32)) : Held (ℕ × ℕ) :=
  ((prog.take 12).foldl (fun stack i ↦ stepSet i.1 (i.2.1.val, i.2.2.val) stack) []).headD
    (Held.cut (0, 0))

/-- The oracle: the positions of the rows an expression names, by list operations on what its
cuts hold. -/
def bornsOf (rs : List (Gen (Fin 3) (Fin 3))) : Held ℕ → List ℕ
  | .cut c => (contentAt rs c).map Gen.born
  | .union p q => (bornsOf rs p ++ bornsOf rs q).eraseDups
  | .inter p q => (bornsOf rs p).filter fun n ↦ (bornsOf rs q).contains n
  | .diff p q => (bornsOf rs p).filter fun n ↦ !(bornsOf rs q).contains n

/-- The same operations on the (key, value) pairs the cuts hold and not on the rows. -/
def valsOf (rs : List (Gen (Fin 3) (Fin 3))) : Held ℕ → List (Fin 3 × Fin 3)
  | .cut c => (contentAt rs c).map fun r ↦ (r.key, r.val)
  | .union p q => (valsOf rs p ++ valsOf rs q).eraseDups
  | .inter p q => (valsOf rs p).filter fun n ↦ (valsOf rs q).contains n
  | .diff p q => (valsOf rs p).filter fun n ↦ !(valsOf rs q).contains n

/-- A chain of at most twenty-four keyed writes. -/
def ch (l : List (Fin 3 × Fin 3)) : List (Fin 3 × Fin 3) := l.take 24

/-- A chain in which no key is written twice: the key is the position. -/
def once (vals : List (Fin 3)) : List (ℕ × Fin 3) := (vals.take 24).zipIdx.map fun x ↦ (x.2, x.1)

/-- A chain of at most twenty-four landings and retires. -/
def chv (l : List (Fin 9)) : List (Fin 3 × Option (Fin 2)) := (l.take 24).map ev

/-- The generations of two chains, as a store of rows. -/
def rows2 (a b : List (Fin 3 × Fin 3)) : Fin 2 → List (Gen (Fin 3) (Fin 3)) :=
  fun k ↦ if k = 0 then gens (ch a) else gens (ch b)

/-- Two stores of rows agree, stamps included. -/
def sameRows (s t : Store (Fin 2) (Gen (Fin 3) (Fin 3))) : Bool :=
  (List.finRange 2).all fun k ↦ (s k).map rowT == (t k).map rowT

/-- A family of at most six positions. -/
def fam (F : List (Fin 28)) : List ℕ := (F.take 6).map fun c ↦ c.val

/-- The least of a family of positions. -/
def least (c : ℕ) (F : List ℕ) : ℕ := F.foldl min c

/-- The greatest of a family of positions. -/
def greatest (c : ℕ) (F : List ℕ) : ℕ := F.foldl max c

/- SNP-11: the read at the join of two cuts is, chain by chain, the later of the two reads, and
the read at their meet the earlier. -/
#eval survives (∀ (a b : List (Fin 3)) (m n i j : ℕ),
  (List.finRange 2).all (fun k ↦
    (readAt (st a b) (cu m n ⊔ cu i j) k
        == if cu m n k ≤ cu i j k then readAt (st a b) (cu i j) k else readAt (st a b) (cu m n) k)
      && readAt (st a b) (cu m n ⊓ cu i j) k
        == if cu m n k ≤ cu i j k then readAt (st a b) (cu m n) k else readAt (st a b) (cu i j) k)
    = true) 529

/- Control: the read at the join is not the read at the meet. -/
#eval refuted (∀ (a b : List (Fin 3)) (m n i j : ℕ),
  same (readAt (st a b) (cu m n ⊔ cu i j)) (readAt (st a b) (cu m n ⊓ cu i j)) = true) 530

/- SNP-11: the difference of two cuts on positions is the read between them from their meet and
to their join, and the symmetric difference is, on each chain, one of the two differences. -/
#eval survives (∀ (a b : List (Fin 3)) (m n i j : ℕ),
  (same (readBetween (st a b) (cu m n ⊓ cu i j) (cu i j)) (readBetween (st a b) (cu m n) (cu i j))
    && same (readBetween (st a b) (cu m n) (cu m n ⊔ cu i j))
      (readBetween (st a b) (cu m n) (cu i j))
    && (List.finRange 2).all fun k ↦
      readBetween (st a b) (cu m n ⊓ cu i j) (cu m n ⊔ cu i j) k
        == readBetween (st a b) (cu m n) (cu i j) k ++ readBetween (st a b) (cu i j) (cu m n) k)
    = true) 531

/- Control: the difference of two cuts is not symmetric. -/
#eval refuted (∀ (a b : List (Fin 3)) (m n i j : ℕ),
  same (readBetween (st a b) (cu m n) (cu i j)) (readBetween (st a b) (cu i j) (cu m n))
    = true) 532

/- SNP-11: the meet distributes over the join and absorbs it, on the reads; and the difference
is a function of the two reads. -/
#eval survives (∀ (a b : List (Fin 3)) (m n i j u v : ℕ),
  (same (readAt (st a b) (cu m n ⊓ (cu i j ⊔ cu u v)))
      (readAt (st a b) (cu m n ⊓ cu i j ⊔ cu m n ⊓ cu u v))
    && same (readAt (st a b) (cu m n ⊔ cu m n ⊓ cu i j)) (readAt (st a b) (cu m n))
    && same (readBetween (st a b) (cu m n) (cu i j))
      (combine (fun x y k ↦ (y k).drop (x k).length) (st a b) (cu m n) (cu i j))) = true) 533

/- SNP-11: the join and the meet of two cuts read as asked are consistent and served, so they
are read as asked. The cuts are the greatest consistent served cuts under two frontiers. -/
#eval survives (∀ (es : List Edge) (m : Fin 1024) (x y u v : Fin 6),
  (cons es (at2 (bestIn es (sv m) x.val y.val) ⊔ at2 (bestIn es (sv m) u.val v.val))
    && cons es (at2 (bestIn es (sv m) x.val y.val) ⊓ at2 (bestIn es (sv m) u.val v.val))
    && (List.finRange 2).all fun k ↦
      sv m k ((at2 (bestIn es (sv m) x.val y.val) ⊔ at2 (bestIn es (sv m) u.val v.val)) k)
        && sv m k ((at2 (bestIn es (sv m) x.val y.val) ⊓ at2 (bestIn es (sv m) u.val v.val)) k))
    = true) 534

/- Control: the join of a cut read as asked with a frontier is not always consistent. -/
#eval refuted (∀ (es : List Edge) (m : Fin 1024) (x y u v : Fin 6),
  cons es (at2 (bestIn es (sv m) x.val y.val) ⊔ cu u.val v.val) = true) 535

/- SNP-12: a row alive at two cuts is alive at every cut between them. -/
#eval survives (∀ (l : List (Fin 3 × Fin 3)) (a : Fin 12) (d e : Fin 8),
  (gens (ch l)).all (fun r ↦
    !(r.aliveAt a.val && r.aliveAt (a.val + d.val + e.val)) || r.aliveAt (a.val + d.val))
    = true) 536

/- Control: a value has no interval. A key that holds one value at two cuts does not always hold
it between them. -/
#eval refuted (∀ (l : List (Fin 3 × Fin 3)) (a : Fin 12) (d e : Fin 8) (x : Fin 3),
  (stateAt (ch l) a.val x != stateAt (ch l) (a.val + d.val + e.val) x
    || stateAt (ch l) (a.val + d.val) x == stateAt (ch l) a.val x) = true) 537

/- SNP-12: the three range reads. What the later cut holds and the earlier does not is the rows
stored after the earlier and alive at the later; what the earlier holds and the later does not,
the rows alive at the earlier and closed at or under the later; what both hold, the rows stored
at or under the earlier and not closed at or under the later. -/
#eval survives (∀ (l : List (Fin 3 × Fin 3)) (a d : Fin 14),
  (gens (ch l)).all (fun r ↦
    ((r.aliveAt (a.val + d.val) && !r.aliveAt a.val)
        == (decide (a.val < r.born) && r.aliveAt (a.val + d.val)))
      && ((r.aliveAt a.val && !r.aliveAt (a.val + d.val))
        == (r.aliveAt a.val && r.died.any fun x ↦ decide (x ≤ a.val + d.val)))
      && (r.aliveAt a.val && r.aliveAt (a.val + d.val))
        == (decide (r.born ≤ a.val) && r.died.all fun x ↦ decide (a.val + d.val < x)))
    = true) 538

/- Control: the rows the later cut holds and the earlier does not are not every row stored
between the two: some were closed before the later cut. -/
#eval refuted (∀ (l : List (Fin 3 × Fin 3)) (a d : Fin 14),
  (gens (ch l)).all (fun r ↦
    (r.aliveAt (a.val + d.val) && !r.aliveAt a.val)
      == (decide (a.val < r.born) && decide (r.born ≤ a.val + d.val))) = true) 539

/- SNP-12: a row is alive at every cut of a family exactly when it is alive at the least and at
the greatest, and at some position of a range exactly when it was stored by the end of the range
and not closed by its start. -/
#eval survives (∀ (l : List (Fin 3 × Fin 3)) (c : Fin 28) (F : List (Fin 28)),
  (gens (ch l)).all (fun r ↦
    ((c.val :: fam F).all (fun d ↦ r.aliveAt d)
        == (r.aliveAt (least c.val (fam F)) && r.aliveAt (greatest c.val (fam F))))
      && (List.range (greatest c.val (fam F) + 1)).any
          (fun d ↦ decide (least c.val (fam F) ≤ d) && r.aliveAt d)
        == (decide (r.born ≤ greatest c.val (fam F))
          && r.died.all fun x ↦ decide (least c.val (fam F) < x))) = true) 540

/- Control: what some cut of a family holds is not what the range between its least and its
greatest cut holds: a row stored and closed between two cuts of the family is alive at none. -/
#eval refuted (∀ (l : List (Fin 3 × Fin 3)) (c : Fin 28) (F : List (Fin 28)),
  (gens (ch l)).all (fun r ↦
    (c.val :: fam F).any (fun d ↦ r.aliveAt d)
      == (decide (r.born ≤ greatest c.val (fam F))
        && r.died.all fun x ↦ decide (least c.val (fam F) < x))) = true) 541

/- SNP-12: what a cut holds is each key's state at the cut, once; and a row records the chain's
event at its position, with its closing stamp past it. -/
#eval survives (∀ (l : List (Fin 3 × Fin 3)) (c : Fin 28) (x : Fin 3),
  (((contentAt (gens (ch l)) c.val).filter fun r ↦ r.key == x).map Gen.val
      == (stateAt (ch l) c.val x).toList
    && (gens (ch l)).all fun r ↦
      (ch l)[r.born - 1]? == some (r.key, r.val) && r.died.all fun d ↦ decide (r.born < d))
    = true) 542

/- SNP-13: the signed difference applied gives the later contents, and differences compose
along cuts in order. -/
#eval survives (∀ (l : List (Fin 3 × Fin 3)) (a : Fin 12) (d e : Fin 8),
  (gens (ch l)).all (fun r ↦
    ((Held.cut (a.val + d.val)).has id r
        == (((Held.cut a.val).diff (Held.gone a.val (a.val + d.val))).union
          (Held.come a.val (a.val + d.val))).has id r)
      && ((Held.come a.val (a.val + d.val + e.val)).has id r
        == (((Held.come a.val (a.val + d.val)).diff
            (Held.gone (a.val + d.val) (a.val + d.val + e.val))).union
          (Held.come (a.val + d.val) (a.val + d.val + e.val))).has id r)
      && (Held.gone a.val (a.val + d.val + e.val)).has id r
        == ((Held.gone a.val (a.val + d.val)).union
          ((Held.gone (a.val + d.val) (a.val + d.val + e.val)).diff
            (Held.come a.val (a.val + d.val)))).has id r) = true) 543

/- Control: through a cut that does not lie between the two, differences do not compose. -/
#eval refuted (∀ (l : List (Fin 3 × Fin 3)) (a b c : Fin 28),
  (gens (ch l)).all (fun r ↦
    (Held.come a.val c.val).has id r
      == (((Held.come a.val b.val).diff (Held.gone b.val c.val)).union
        (Held.come b.val c.val)).has id r) = true) 544

/- SNP-13: the count walks the signed difference, between any two cuts, and the sizes of the
differences obey the triangle inequality. -/
#eval survives (∀ (l : List (Fin 3 × Fin 3)) (a b c : Fin 28),
  (((Held.cut b.val).rows id (gens (ch l))).length
        + ((Held.gone a.val b.val).rows id (gens (ch l))).length
      == ((Held.cut a.val).rows id (gens (ch l))).length
        + ((Held.come a.val b.val).rows id (gens (ch l))).length
    && decide (((Held.gone a.val c.val).rows id (gens (ch l))).length
      ≤ ((Held.gone a.val b.val).rows id (gens (ch l))).length
        + ((Held.gone b.val c.val).rows id (gens (ch l))).length)) = true) 545

/- Control: the count of the later cut is not the count of the earlier with the rows come: the
rows gone are subtracted. -/
#eval refuted (∀ (l : List (Fin 3 × Fin 3)) (a d : Fin 14),
  (((Held.cut (a.val + d.val)).rows id (gens (ch l))).length
    == ((Held.cut a.val).rows id (gens (ch l))).length
      + ((Held.come a.val (a.val + d.val)).rows id (gens (ch l))).length) = true) 546

/- SNP-13: the rows of a signed difference sort by key: each row gone is removed or the first of
a replaced pair and not both, each row come is added or the second of one, and the two rows of a
pair share their key. -/
#eval survives (∀ (l : List (Fin 3 × Fin 3)) (a b : Fin 28),
  (((Held.gone a.val b.val).rows id (gens (ch l))).all (fun r ↦
      ((removedOf ((Held.gone a.val b.val).rows id (gens (ch l)))
          ((Held.come a.val b.val).rows id (gens (ch l)))).any fun x ↦ x.born == r.born)
        != (replacedOf ((Held.gone a.val b.val).rows id (gens (ch l)))
          ((Held.come a.val b.val).rows id (gens (ch l)))).any fun x ↦ x.1.born == r.born)
    && ((Held.come a.val b.val).rows id (gens (ch l))).all (fun r ↦
      ((addedOf ((Held.gone a.val b.val).rows id (gens (ch l)))
          ((Held.come a.val b.val).rows id (gens (ch l)))).any fun x ↦ x.born == r.born)
        != (replacedOf ((Held.gone a.val b.val).rows id (gens (ch l)))
          ((Held.come a.val b.val).rows id (gens (ch l)))).any fun x ↦ x.2.born == r.born)
    && (replacedOf ((Held.gone a.val b.val).rows id (gens (ch l)))
      ((Held.come a.val b.val).rows id (gens (ch l)))).all fun x ↦ x.1.key == x.2.key)
    = true) 547

/- SNP-13: every row of the signed difference belongs to a key the events between the two cuts
name. -/
#eval survives (∀ (l : List (Fin 3 × Fin 3)) (a d : Fin 14),
  ((Held.gone a.val (a.val + d.val)).rows id (gens (ch l))
      ++ (Held.come a.val (a.val + d.val)).rows id (gens (ch l))).all
    (fun r ↦ ((((ch l).take (a.val + d.val)).drop a.val).map Prod.fst).contains r.key)
    = true) 548

/- Control: the events between two cuts are not the signed difference. On a chain of landings
and retires a key the events name does not always have a version on either side. -/
#eval refuted (∀ (l : List (Fin 9)) (a d : Fin 14),
  (((chv l).take (a.val + d.val)).drop a.val).all (fun e ↦
    ((Held.gone a.val (a.val + d.val)).rows id ((gens (chv l)).filter Gen.isVersion)
      ++ (Held.come a.val (a.val + d.val)).rows id ((gens (chv l)).filter Gen.isVersion)).any
        fun r ↦ r.key == e.1) = true) 549

/- SNP-17: a retire is a removal. When a key holds a version at one cut and its last event at
another is a retire, the version's row is gone between the two and no row of the key that came
carries a version. -/
#eval survives (∀ (l : List (Fin 9)) (a b : Fin 28) (x : Fin 3),
  ((stateAt (chv l) a.val x).join.isSome && stateAt (chv l) b.val x == some none) = true →
    (((Held.gone a.val b.val).rows id (gens (chv l))).any
        (fun r ↦ r.key == x && r.val == (stateAt (chv l) a.val x).join)
      && ((Held.come a.val b.val).rows id (gens (chv l))).all
        fun r ↦ r.key != x || r.val.isNone) = true) 550

/- SNP-14: a set read lazily is the set computed by list operations on what its cuts hold. -/
#eval survives (∀ (l : List (Fin 3 × Fin 3)) (prog : List (Fin 4 × Fin 32)),
  (gens (ch l)).all (fun r ↦
    (build prog).has id r == (bornsOf (gens (ch l)) (build prog)).contains r.born) = true) 551

/- Control: the same operations on the values the cuts hold are another thing: a key that
returns to a value has two rows and one value. -/
#eval refuted (∀ (l : List (Fin 3 × Fin 3)) (prog : List (Fin 4 × Fin 32)),
  (gens (ch l)).all (fun r ↦
    (build prog).has id r == (valsOf (gens (ch l)) (build prog)).contains (r.key, r.val))
    = true) 552

/- SNP-14: a set whose cuts lie inside the chain holds, after any growth of the chain, the
events it held. -/
#eval survives (∀ (l t : List (Fin 3 × Fin 3)) (prog : List (Fin 4 × Fin 32)),
  (((buildAt (ch l).length prog).rows id (gens (ch l ++ ch t))).map Gen.event
    == ((buildAt (ch l).length prog).rows id (gens (ch l))).map Gen.event) = true) 553

/- Control: a set that names a cut past the head changes when the chain grows. -/
#eval refuted (∀ (l t : List (Fin 3 × Fin 3)) (prog : List (Fin 4 × Fin 32)),
  (((build prog).rows id (gens (ch l ++ ch t))).map Gen.event
    == ((build prog).rows id (gens (ch l))).map Gen.event) = true) 554

/- Control: the closing stamps are not part of what a set held: growth writes them. -/
#eval refuted (∀ (l t : List (Fin 3 × Fin 3)) (prog : List (Fin 4 × Fin 32)),
  (((buildAt (ch l).length prog).rows id (gens (ch l ++ ch t))).map rowT
    == ((buildAt (ch l).length prog).rows id (gens (ch l))).map rowT) = true) 555

/- SNP-14: a set whose cuts lie at or under a cut reads the prefix at that cut; a row's own
test commutes with it; every row in it is alive at a cut it names. -/
#eval survives (∀ (l : List (Fin 3 × Fin 3)) (c : Fin 28) (e : Fin 8)
    (prog : List (Fin 4 × Fin 32)),
  (((buildAt (min c.val (ch l).length) prog).rows id (gens (ch l))).map Gen.event
      == ((buildAt (min c.val (ch l).length) prog).rows id
        (gens ((ch l).take (min c.val (ch l).length)))).map Gen.event
    && (((build prog).rows id (gens (ch l))).filter fun r ↦ pf e r.val).map rowT
      == ((build prog).rows id ((gens (ch l)).filter fun r ↦ pf e r.val)).map rowT
    && ((build prog).rows id (gens (ch l))).all fun r ↦
      (build prog).atoms.any fun a ↦ r.aliveAt a) = true) 556

/- SNP-14: what every cut of a family holds, what some cut holds, and in how many cuts a row is
alive. -/
#eval survives (∀ (l : List (Fin 3 × Fin 3)) (c : Fin 28) (F : List (Fin 28)),
  (gens (ch l)).all (fun r ↦
    ((Held.all c.val (fam F)).has id r == (c.val :: fam F).all fun d ↦ r.aliveAt d)
      && ((Held.any c.val (fam F)).has id r == (c.val :: fam F).any fun d ↦ r.aliveAt d)
      && ((Held.all c.val (fam F)).has id r
        == (Held.kept (least c.val (fam F)) (greatest c.val (fam F))).has id r)
      && decide (0 < countIn (c.val :: fam F) r) == (Held.any c.val (fam F)).has id r
      && decide (countIn (c.val :: fam F) r = (fam F).length + 1)
        == (Held.all c.val (fam F)).has id r) = true) 557

/- Control: a row's test applied to the chain before its generations are computed is not the
test applied to what a cut holds: the positions move. -/
#eval refuted (∀ (l : List (Fin 3 × Fin 3)) (c : Fin 28) (e : Fin 8),
  ((contentAt (gens ((ch l).filter fun w ↦ pf e w.2)) c.val).map (fun r ↦ (r.key, r.val))
    == ((contentAt (gens (ch l)) c.val).filter fun r ↦ pf e r.val).map fun r ↦ (r.key, r.val))
    = true) 558

/- SNP-15: on a chain in which no row is ever closed the contents follow the positions: the join
holds what either cut holds and the meet what both hold. -/
#eval survives (∀ (vals : List (Fin 3)) (a b : Fin 28),
  (gens (once vals)).all (fun r ↦
    (r.aliveAt (a.val ⊔ b.val) == (r.aliveAt a.val || r.aliveAt b.val))
      && r.aliveAt (a.val ⊓ b.val) == (r.aliveAt a.val && r.aliveAt b.val)) = true) 559

/- Control: on a chain where keys are written again they do not: what either cut holds is more
than what the join holds. -/
#eval refuted (∀ (l : List (Fin 3 × Fin 3)) (a b : Fin 28),
  (gens (ch l)).all (fun r ↦
    r.aliveAt (a.val ⊔ b.val) == (r.aliveAt a.val || r.aliveAt b.val)) = true) 560

/- SNP-15: on any chain, what either cut holds is what the join holds with the rows closed
between the meet and the join, and what both hold is what the meet and the join both hold. -/
#eval survives (∀ (l : List (Fin 3 × Fin 3)) (a b : Fin 28),
  (gens (ch l)).all (fun r ↦
    ((r.aliveAt a.val || r.aliveAt b.val)
        == (r.aliveAt (a.val ⊔ b.val)
          || (r.aliveAt (a.val ⊓ b.val) && !r.aliveAt (a.val ⊔ b.val))))
      && (r.aliveAt a.val && r.aliveAt b.val)
        == (r.aliveAt (a.val ⊓ b.val) && r.aliveAt (a.val ⊔ b.val))) = true) 561

/- SNP-16: every set commutes with the grant's restriction, and under a grant that names one
chain it reads that chain and the cuts' positions on it and nothing else. -/
#eval survives (∀ (a b b' : List (Fin 3 × Fin 3)) (g : Fin 4) (c : Fin 8) (n : ℕ)
    (prog : List (Fin 4 × Fin 32 × Fin 32)),
  (sameRows
      ((build2 prog).across (fun x ↦ cu x.1 x.2)
        (restrict (fun k ↦ gr g k = true) (fun r ↦ pf c r.val) (rows2 a b)))
      (restrict (fun k ↦ gr g k = true) (fun r ↦ pf c r.val)
        ((build2 prog).across (fun x ↦ cu x.1 x.2) (rows2 a b)))
    && sameRows
      (restrict (fun k ↦ k = 0) (fun r ↦ pf c r.val)
        ((build2 prog).across (fun x ↦ cu x.1 x.2) (rows2 a b)))
      (restrict (fun k ↦ k = 0) (fun r ↦ pf c r.val)
        ((build2 prog).across (fun x ↦ cu x.1 (x.2 + n)) (rows2 a b')))) = true) 562

/- Control: without the grant's restriction a set reads the other chain. -/
#eval refuted (∀ (a b b' : List (Fin 3 × Fin 3)) (prog : List (Fin 4 × Fin 32 × Fin 32)),
  sameRows ((build2 prog).across (fun x ↦ cu x.1 x.2) (rows2 a b))
    ((build2 prog).across (fun x ↦ cu x.1 x.2) (rows2 a b')) = true) 563

/- SNP-17: an erasure takes its own rows out of every set and changes no other. The versions a
set holds on the chain with holes carry no erased value, and they are the rows it holds on the
chain, less the erased ones, at the positions they had. -/
#eval survives (∀ (l : List (Fin 3 × Fin 3)) (e : Fin 8) (prog : List (Fin 4 × Fin 32)),
  ((((build prog).rows id (gens (holes (ek e) (ch l)))).filter Gen.isVersion).map Gen.event
      == (((build prog).rows id (gens (ch l))).filter fun r ↦ !pf e r.val).map
        (fun r ↦ (r.key, some r.val, r.born))
    && (((build prog).rows id (gens (holes (ek e) (ch l)))).filter Gen.isVersion).all
      fun r ↦ r.val.all fun v ↦ !pf e v) = true) 564

/- Control: an erasure that deletes the rows moves the later ones up, and a set then holds
another thing. -/
#eval refuted (∀ (l : List (Fin 3 × Fin 3)) (e : Fin 8) (prog : List (Fin 4 × Fin 32)),
  (((build prog).rows id (gens ((ch l).filter fun w ↦ !ek e w))).map Gen.event
    == (((build prog).rows id (gens (ch l))).filter fun r ↦ !pf e r.val).map Gen.event)
    = true) 565

/- Control: a hole is no version. The rows alive at a cut of a chain with holes are not all
versions. -/
#eval refuted (∀ (l : List (Fin 3 × Fin 3)) (e : Fin 8) (c : Fin 28),
  (contentAt (gens (holes (ek e) (ch l))) c.val).all (fun r ↦ r.isVersion) = true) 566

end Palace.Snapshot.Attack
