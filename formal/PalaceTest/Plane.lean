module

public import Palace.Plane
public import PalaceTest.Attack
public meta import Palace.Plane
public meta import PalaceTest.Attack

/-!
# Attacks on `Palace.Plane`

The Plausible attacks and negative controls for the laws of `Palace/Plane.lean`. They run
when this module builds (`lake test`); the library itself runs no code at build time.
-/

@[expose] public section

open Finset

namespace Palace.Plane

/-! ## Attacks

Each law is attacked on random traces over small exact types: three classes, three paths (path
`p` lives at class `p`, so `κ = id`), two digests, four atoms, and a query that ties atoms often.
A raw write is decoded into a land (weighted three to one), a retire, a purge or a repair. Each
control states a nearby false law and must be refuted.
-/

namespace Attack

/-- The attacks' plane: classes, paths, digests and atoms. -/
abbrev St := State (Fin 3) (Fin 3) (Fin 2) (Fin 4)

/-- The attacks' writes. -/
abbrev Wr := Op (Fin 3) (Fin 3) (Fin 2) (Fin 4)

/-- A random write: tag, path, class, digest, first atom, further atoms. -/
abbrev Raw := Fin 6 × Fin 3 × Fin 3 × Fin 2 × Fin 4 × List (Fin 4)

/-- The fiber a raw write lands in class `c`: chunk `i` holds the `i`-th atom. -/
def fiberOf (c : Fin 3) (r : Raw) : Fiber (Fin 3) (Fin 3) (Fin 2) (Fin 4) :=
  ⟨c, r.2.1, r.2.2.2.1, (r.2.2.2.2.1 :: r.2.2.2.2.2).mapIdx fun i a ↦ (i, a)⟩

/-- Decode a raw write. With `strict`, lands and retires take the path's own class (`κ = id`);
without it, the raw class. -/
def decode (strict : Bool) (r : Raw) : Wr :=
  let c := if strict then r.2.1 else r.2.2.1
  match r.1.val with
  | 0 | 1 | 2 => .land (fiberOf c r)
  | 3 => .retire c r.2.1
  | 4 => .purge r.2.2.2.1
  | _ => .repair

/-- A query's distances: atoms tie often. -/
def dist (q : Fin 3) (a : Fin 4) : ℕ := a.val * (q.val + 1) % 3

/-- Run a trace with a given step, from the empty plane. -/
def runWith (st : Wr → St → St) (ops : List Wr) : St := ops.foldl (fun s op ↦ st op s) empty

/-- A clearance that leaves at least one class out, as the property test draws it: class `c`,
and the next one when `two`. -/
def clearance (c : Fin 3) (two : Bool) : Finset (Fin 3) := if two then {c, c + 1} else {c}

/-- Noninterference on one instance: the view and a search under `C`, after the trace and after
its visible writes alone. `leak` reads every class instead (the seeded leak). -/
def niHolds (st : Wr → St → St) (strict leak : Bool) (raws : List Raw) (C : Finset (Fin 3))
    (q : Fin 3) (k : Fin 4) (sup : Bool) : Bool :=
  let ops := raws.map (decode strict)
  let s := runWith st ops
  let t := runWith st (ops.filter (·.visible C))
  let R := if leak then Finset.univ else C
  decide (view C s = view C t) && decide (search (dist q) R s k sup = search (dist q) R t k sup)

/-- An instance worth counting: the trace has an uncleared write and the cleared search hits. -/
def nontrivial (raws : List Raw) (C : Finset (Fin 3)) (q : Fin 3) (k : Fin 4) (sup : Bool) :
    Bool :=
  let ops := raws.map (decode true)
  (ops.any fun op ↦ !op.visible C) && !(search (dist q) C (runWith step ops) k sup).isEmpty

/- A3.5: noninterference on random stratum-respecting traces, views and searches, counted only
where an uncleared write happened and the cleared search hits. -/
#eval survives (∀ raws : List Raw, ∀ c : Fin 3, ∀ two : Bool, ∀ q : Fin 3, ∀ k : Fin 4,
  ∀ sup : Bool, nontrivial raws (clearance c two) q k sup = true →
    niHolds step true false raws (clearance c two) q k sup = true) 81

/- Control, the stratum channel: lands and retires at arbitrary classes. -/
#eval refuted (∀ raws : List Raw, ∀ c : Fin 3, ∀ two : Bool, ∀ q : Fin 3, ∀ k : Fin 4,
  ∀ sup : Bool, niHolds step false false raws (clearance c two) q k sup = true) 82

/- Control, the seeded leak: a reader whose join reads every class. -/
#eval refuted (∀ raws : List Raw, ∀ c : Fin 3, ∀ two : Bool, ∀ q : Fin 3, ∀ k : Fin 4,
  ∀ sup : Bool, niHolds step true true raws (clearance c two) q k sup = true) 83

/-- Every land of class 0 crashes between its commit and its cache step; nothing else does. -/
def stepDrift : Wr → St → St
  | .land f => if f.cls = 0 then landCrash f else land f
  | op => step op

/- Control, the drift channel: cleared lands that crash before their cache step. -/
#eval refuted (∀ raws : List Raw, ∀ two : Bool, ∀ q : Fin 3, ∀ k : Fin 4, ∀ sup : Bool,
  niHolds stepDrift true false raws (clearance 0 two) q k sup = true) 84

/-- A write, or what a crash partway through it leaves: `0` none, `1` after the transaction
(before the cache step), `2` after the atoms (before the transaction). -/
def stepCrash (crash : Fin 3) : Wr → St → St
  | .land f, s =>
    if crash = 0 then land f s else if crash = 1 then landCrash f s else insertAtoms f.atoms s
  | .retire c p, s =>
    if crash = 0 then retire c p s
    else if crash = 1 ∧ heads (s.occ c) p ≠ ∅ then retireCommit c p s else s
  | .purge d, s =>
    if crash = 0 then purge d s else if crash = 1 then purgeCommit d s else purgeAtoms d s
  | .repair, s => if crash = 0 then repair s else s

/-- The reader that trusts the cache: hits straight from the prefilter, no cleared join. -/
def searchTrust (q : Fin 3) (C : Finset (Fin 3)) (s : St) (k : ℕ) (sup : Bool) :
    List (Fin 4 × Finset (Fin 3 × Occ (Fin 3) (Fin 2) (Fin 4))) :=
  ((byDist (dist q) (prefilter C s sup)).take k).map fun a ↦ (a, hitOccs C s sup a)

/-- The plane after a trace in which any write may crash partway. -/
def runCrash (raws : List (Raw × Fin 3)) : St :=
  raws.foldl (fun s r ↦ stepCrash r.2 (decode true r.1) s) empty

/-- No-leak on one instance: every hit is a table atom with a cleared occupancy, and carries only
cleared rows that hold it. -/
def soundHolds (trust : Bool) (raws : List (Raw × Fin 3)) (C : Finset (Fin 3)) (q : Fin 3)
    (k : Fin 4) (sup : Bool) : Bool :=
  let s := runCrash raws
  let hits := if trust then searchTrust q C s k sup else search (dist q) C s k sup
  hits.all fun h ↦ decide (h.1 ∈ s.table ∧ h.2.Nonempty ∧
    ∀ x ∈ h.2, x.1 ∈ C ∧ x.2 ∈ s.occ x.1 ∧ x.2.holds sup h.1)

/- A3, no-leak under any cache: traces where any write may crash partway, counted where the
search hits. -/
#eval survives (∀ raws : List (Raw × Fin 3), ∀ c : Fin 3, ∀ two : Bool, ∀ q : Fin 3, ∀ k : Fin 4,
  ∀ sup : Bool, (search (dist q) (clearance c two) (runCrash raws) k sup).isEmpty = false →
    soundHolds false raws (clearance c two) q k sup = true) 85

/- Control, the reader that trusts the cache: a crash after a commit (here a re-derivation that
drops an atom) leaves an atom cached as held that no row holds. -/
#eval refuted (∀ raws : List (Raw × Fin 3), ∀ c : Fin 3, ∀ two : Bool, ∀ q : Fin 3, ∀ k : Fin 4,
  ∀ sup : Bool, soundHolds true raws (clearance c two) q k sup = true) 86

/-- `held_drift() == []`, decided. -/
def coherentB (s : St) : Bool :=
  decide (∀ a ∈ s.table, cache s false a = truth s false a ∧ cache s true a = truth s true a)

/-- `land` with a mutated `freed`: the old derivation's atoms left out. -/
def landMut (f : Fiber (Fin 3) (Fin 3) (Fin 2) (Fin 4)) (s : St) : St :=
  if Refused f s then insertAtoms f.atoms s
  else refresh (f.atoms ∪ ((s.occ f.cls).filter fun o ↦
      o.path = f.path ∧ o.current = true ∧ o.digest ≠ f.digest).image (·.atom))
    (commit f (insertAtoms f.atoms s))

/- The cache stays coherent along every trace. -/
#eval survives (∀ raws : List Raw, coherentB (runWith step (raws.map (decode true))) = true) 87

/- Control, the mutation: re-landing a version with a changed derivation strands a dropped atom's
cache. -/
#eval refuted (∀ raws : List Raw, coherentB (runWith (fun op ↦ match op with
  | .land f => landMut f
  | op => step op) (raws.map (decode true))) = true) 88

/- The search loop returns the first `k` held atoms of the exact ranking. -/
#eval survives (∀ ps : List (Fin 8), ∀ mask : List Bool, ∀ k : Fin 6,
  widen (ps.dedup.take ·) (fun a ↦ mask.getD a.val false) k ps.dedup.length [] [] k =
    (ps.dedup.filter fun a ↦ mask.getD a.val false).take k) 89

/-- The loop without its `seen` set. -/
def widenNoSeen (nearest : ℕ → List (Fin 8)) (T : Fin 8 → Bool) (k : ℕ) :
    ℕ → List (Fin 8) → ℕ → List (Fin 8)
  | 0, hits, _ => hits.take k
  | fuel + 1, hits, limit =>
    let cands := nearest limit
    let hits := hits ++ cands.filter T
    if k ≤ hits.length ∨ cands.length < limit then hits.take k
    else widenNoSeen nearest T k fuel hits (limit * 4)

/- Control, no `seen` set: a widened window counts its first hits twice. -/
#eval refuted (∀ ps : List (Fin 8), ∀ mask : List Bool, ∀ k : Fin 6,
  widenNoSeen (ps.dedup.take ·) (fun a ↦ mask.getD a.val false) k ps.dedup.length [] k =
    (ps.dedup.filter fun a ↦ mask.getD a.val false).take k) 90

/-- The purge laws on one instance: no dangling row, no row or edge naming the digest, nothing
the digest held left unreferenced, and re-running finishes a purge interrupted after its atoms. -/
def purgeHolds (pg : Fin 2 → St → St) (raws : List Raw) (d : Fin 2) : Bool :=
  let s := runWith step (raws.map (decode true))
  let s' := pg d s
  let s'' := purge d (purgeAtoms d s)
  decide (WF s') &&
    decide (∀ c, (∀ o ∈ s'.occ c, o.digest ≠ d) ∧
      ∀ e ∈ s'.sup c, e.old ≠ some d ∧ e.new ≠ some d) &&
    decide (∀ a ∈ byDigest d s, a ∈ s'.table → ∃ c, ∃ o ∈ s'.occ c, o.atom = a) &&
    decide (s''.occ = s'.occ ∧ s''.sup = s'.sup ∧ s''.table = s'.table ∧ s''.held = s'.held ∧
      s''.ever = s'.ever)

/- A3.7: purge, on random planes and digests. -/
#eval survives (∀ raws : List Raw, ∀ d : Fin 2, purgeHolds purge raws d = true) 91

/-- A purge that frees every atom the digest held, without the still-held check. -/
def purgeAll (d : Fin 2) (s : St) : St :=
  refresh (stillHeld d s) { purgeCommit d s with table := s.table \ byDigest d s }

/- Control, no still-held check: a purge frees an atom another row still holds. -/
#eval refuted (∀ raws : List Raw, ∀ d : Fin 2, purgeHolds purgeAll raws d = true) 92

/-! ### Crash points of a land (PLN-4, dn-ingest-door §9 item 7) -/

/-- A write in the code's order, or what a crash partway through it leaves: `0` none, `1` after a
land's transaction (or its rollback) or a retire's or a purge's, `2` before a land's transaction,
its atoms and its cache's additions written. With `old`, a land writes its cache last
(`landCrash`). A purge interrupted after its atom delete is left out: until it runs again it leaves
rows pointing at nothing (PLN-5). -/
def stepCrashAdd (old : Bool) (crash : Fin 3) : Wr → St → St
  | .land f, s =>
    if crash = 0 then land f s
    else if crash = 1 then (if old then landCrash f s else landAddCommit f s)
    else (if old then insertAtoms f.atoms s else landAdd f s)
  | .retire c p, s =>
    if crash = 0 then retire c p s
    else if crash = 1 ∧ heads (s.occ c) p ≠ ∅ then retireCommit c p s else s
  | .purge d, s => if crash = 0 then purge d s else purgeCommit d s
  | .repair, s => if crash = 0 then repair s else s

/-- The cache after a trace of writes, any of which may crash partway, is complete on every
class. -/
def completeAfter (old : Bool) (raws : List (Raw × Fin 3)) : Bool :=
  decide (Complete univ (raws.foldl (fun s r ↦ stepCrashAdd old r.2 (decode true r.1) s) empty))

/- PLN-4: with a land's cache additions written before its transaction, the cache stays complete
through traces in which any write may crash partway. -/
#eval survives (∀ raws : List (Raw × Fin 3), completeAfter false raws = true) 314

/- Control, the cache written last: a land that crashes after its transaction leaves an atom
whose cache misses the class of its new row. -/
#eval refuted (∀ raws : List (Raw × Fin 3), completeAfter true raws = true) 315

/-- A relabel of class `o` to class `n`, or what a crash partway through it leaves: `0` none, `1`
after its transaction (after its rollback, on a clash), `2` before it. With `old`, the cache is
written last; otherwise the additions come first. -/
def relabelAt (old : Bool) (o n : Fin 3) (crash : Fin 3) (s : St) : St :=
  if o = n then s
  else if crash = 0 then relabel o n s
  else
    let t := if old then s else addRelabel o n s
    if crash = 1 ∧ ¬Clash o n s then relabelCommit o n t else t

/-- The cache after a random trace and a relabel that may crash partway is complete. -/
def relabelComplete (old : Bool) (raws : List Raw) (o n crash : Fin 3) : Bool :=
  decide (Complete univ (relabelAt old o n crash (runWith step (raws.map (decode true)))))

/- PLN-4: with a relabel's additions first, the cache stays complete at its crash points. -/
#eval survives (∀ raws : List Raw, ∀ o n crash : Fin 3, relabelComplete false raws o n crash = true)
  316

/- Control, the cache written last: a relabel that crashes after its transaction leaves the moved
atoms without their new class. -/
#eval refuted (∀ raws : List Raw, ∀ o n crash : Fin 3, relabelComplete true raws o n crash = true)
  317

/-! ### The chunk-key migration (#37) -/

/-- A random physical row: id, document (`3` is none, a shed atom row), text, lane. -/
abbrev RawPhys := Fin 4 × Fin 4 × Fin 3 × Bool

/-- The row a raw one decodes to; its id is below 4. -/
def physOf (r : RawPhys) : Phys (Fin 3) ℕ (Fin 3) :=
  ⟨r.1.val, if h : r.2.1.val < 3 then some ⟨r.2.1.val, h⟩ else none, r.2.2.1, r.2.2.2⟩

/-- A doc-scoped key, injective and from 10 up, so it never meets a raw id. -/
def keyOf (p : Option (Fin 3)) (t : Fin 3) : ℕ := 10 + 4 * p.elim 0 (·.val + 1) + t.val

/-- The migration's laws on one set of physical rows: the rows outside the note lane kept, every
note record under its key, every row's document, text and lane kept, and a second run idle. -/
def rekeyHolds (rk : Finset (Phys (Fin 3) ℕ (Fin 3)) → Finset (Phys (Fin 3) ℕ (Fin 3)))
    (raws : List RawPhys) : Bool :=
  let ps := (raws.map physOf).toFinset
  let qs := rk ps
  decide (qs.filter (fun r ↦ ¬r.Note) = ps.filter (fun r ↦ ¬r.Note)) &&
    decide (∀ r ∈ qs, r.Note → r.id = keyOf r.path r.text) &&
    decide (qs.image Phys.content = ps.image Phys.content) && decide (rk qs = qs)

/- PLN-6: the scoped re-key on random physical rows of both lanes, shed atoms among them. -/
#eval survives (∀ raws : List RawPhys,
  rekeyHolds (fun ps ↦ ps.image (Phys.rekey keyOf)) raws = true) 311

/- Control, `rekey_store` as it was: every record under the note lane's key, the shed atoms not
read, so not landed again. -/
#eval refuted (∀ raws : List RawPhys, rekeyHolds (fun ps ↦
  (ps.filter fun r ↦ r.path.isSome = true).image fun r ↦ { r with id := keyOf r.path r.text })
  raws = true) 312

/-- The fibers `all_rows()` regroups the plane's current rows into, as `store.add` lands them: one
per class, path and current digest, its chunks in order. -/
def currentFibers (s : St) : List (Fiber (Fin 3) (Fin 3) (Fin 2) (Fin 4)) :=
  (List.finRange 3).flatMap fun c ↦ (List.finRange 3).flatMap fun p ↦
    (List.finRange 2).filterMap fun d ↦
      let rows := (s.occ c).filter fun o ↦ o.path = p ∧ o.digest = d ∧ o.current = true
      if rows.Nonempty then
        some ⟨c, p, d, (List.range 6).filterMap fun i ↦
          ((List.finRange 4).find? fun a ↦ decide (⟨p, d, i, a, true⟩ ∈ rows)).map (i, ·)⟩
      else none

/-- What a reader under `C` sees after the unscoped re-key's `reset()` and re-landing, against
what it saw before. -/
def resetHolds (raws : List Raw) (C : Finset (Fin 3)) : Bool :=
  let s := runWith step (raws.map (decode true))
  decide (view C (runWith step ((currentFibers s).map .land)) = view C s)

/- Control, the unscoped re-key's plane: re-landing the current rows from the empty plane keeps
every reader's view. -/
#eval refuted (∀ raws : List Raw, ∀ c : Fin 3, ∀ two : Bool,
  resetHolds raws (clearance c two) = true) 313

end Attack

end Palace.Plane
