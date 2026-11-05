module

public import Palace.Door
public import PalaceTest.Attack
public meta import Palace.Door
public meta import PalaceTest.Attack

/-!
# Attacks on `Palace.Door`

The Plausible attacks and negative controls for the laws of `Palace/Door.lean`, on exact shadows:
rows over `Fin 4` from four bits, two or three identities, two digests, chains as lists, keys
unset (fresh states) except in `held`, a state holding a version under its key. The controls are
the laws' edges: an ingest that always appends a version is not idempotent, two commands on one
identity do not commute, an interleaving that lands them in the other order lands the other
chain, a run that writes its key first does not converge, nor one that writes it after the
plane's rows as the audit's defect 1 did (DOR-7), a schedule that swaps two versions of one note
lands the other chain (DOR-10), a command whose run is not a prefix of its own steps is never
repaired by a re-run (DOR-11), a run that writes its key first shows a reader that trusts the key
rows that are not there (DOR-12), a revert whose guard reads the key before an edit's lands the
edit alone (DOR-10's guard), two versions of one note stopped out of order do not converge
(DOR-11's hypothesis), and a serial run stopped inside a command does not converge when the
whole batch runs again (DOR-11 with repeated identities). They run when this module builds
(`lake test`).
-/

@[expose] public section

open Finset

namespace Palace.Door.Attack

/-- A set of rows from four bits. -/
def rowsOf (c : Fin 16) : Finset (Fin 4) := univ.filter fun i ↦ c.val.testBit i.val

/-- A source with two stages, an identity and a digest. -/
def src (c₁ c₂ : Fin 16) (d g : Fin 2) : Source (Fin 4) (Fin 2) (Fin 2) :=
  ⟨[rowsOf c₁, rowsOf c₂], d, g⟩

/-- A source with one stage: the attacks that quantify over two commands keep the variable count
within what Plausible's instance compilation affords. -/
def src1 (c : Fin 16) (d g : Fin 2) : Source (Fin 4) (Fin 2) (Fin 2) := ⟨[rowsOf c], d, g⟩

/-- A fresh state: rows from four bits, one chain per identity, no key set. -/
def st (c : Fin 16) (l₀ l₁ : List (Fin 2)) : State (Fin 4) (Fin 2) (Fin 2) :=
  ⟨rowsOf c, fun d ↦ if d = 0 then l₀ else l₁, fun _ ↦ none⟩

/-- Two states agree. -/
def same (a b : State (Fin 4) (Fin 2) (Fin 2)) : Bool :=
  a.rows == b.rows && a.chain 0 == b.chain 0 && a.chain 1 == b.chain 1
    && a.key 0 == b.key 0 && a.key 1 == b.key 1

/-- The wrong operation: it appends the digest whether or not it is the head, and never reads
the key. -/
def ingestBad (x : Source (Fin 4) (Fin 2) (Fin 2)) (s : State (Fin 4) (Fin 2) (Fin 2)) :
    State (Fin 4) (Fin 2) (Fin 2) :=
  ⟨s.rows ∪ x.rows, fun d ↦ if d = x.ident then s.chain d ++ [x.digest] else s.chain d, s.key⟩

/-- Even rows are atoms. -/
def isAtom (r : Fin 4) : Prop := r.val % 2 = 0

instance : DecidablePred isAtom := fun r ↦ inferInstanceAs (Decidable (r.val % 2 = 0))

/-- Three identities, for the batch attacks. -/
def src3 (c : Fin 16) (d : Fin 3) (g : Fin 2) : Source (Fin 4) (Fin 3) (Fin 2) := ⟨[rowsOf c], d, g⟩

/-- The empty fresh state on three identities. -/
def st3 : State (Fin 4) (Fin 3) (Fin 2) := ⟨∅, fun _ ↦ [], fun _ ↦ none⟩

/-- Two states on three identities agree. -/
def same3 (a b : State (Fin 4) (Fin 3) (Fin 2)) : Bool :=
  a.rows == b.rows && (List.finRange 3).all fun d ↦ a.chain d == b.chain d && a.key d == b.key d

/- DOR-2: ingestion is idempotent. -/
#eval survives (∀ (c₁ c₂ c : Fin 16) (d g : Fin 2) (l₀ l₁ : List (Fin 2)),
  same (ingest (src c₁ c₂ d g) (ingest (src c₁ c₂ d g) (st c l₀ l₁)))
    (ingest (src c₁ c₂ d g) (st c l₀ l₁)) = true) 245

/- Control: an operation that always appends a version is not. -/
#eval refuted (∀ (c₁ c₂ c : Fin 16) (d g : Fin 2) (l₀ l₁ : List (Fin 2)),
  same (ingestBad (src c₁ c₂ d g) (ingestBad (src c₁ c₂ d g) (st c l₀ l₁)))
    (ingestBad (src c₁ c₂ d g) (st c l₀ l₁)) = true) 246

/- DOR-3: commands on distinct identities commute. -/
#eval survives (∀ (c₁ c₂ c : Fin 16) (g g' : Fin 2) (l₀ l₁ : List (Fin 2)),
  same (ingest (src1 c₁ 0 g) (ingest (src1 c₂ 1 g') (st c l₀ l₁)))
    (ingest (src1 c₂ 1 g') (ingest (src1 c₁ 0 g) (st c l₀ l₁))) = true) 247

/- Control, DOR-8: on one identity the two orders give two chains. -/
#eval refuted (∀ (c₁ c₂ c : Fin 16) (g g' : Fin 2) (l₀ l₁ : List (Fin 2)),
  same (ingest (src1 c₁ 0 g) (ingest (src1 c₂ 0 g') (st c l₀ l₁)))
    (ingest (src1 c₂ 0 g') (ingest (src1 c₁ 0 g) (st c l₀ l₁))) = true) 248

/- DOR-7: with the key last, a run interrupted after any step converges under re-run. -/
#eval survives (∀ (k : Fin 5) (c₁ c₂ c : Fin 16) (d g : Fin 2) (l₀ : List (Fin 2)),
  same (ingest (src c₁ c₂ d g) (run ((src c₁ c₂ d g).steps.take k.val) (st c l₀ [])))
    (ingest (src c₁ c₂ d g) (st c l₀ [])) = true) 249

/- Control, DOR-7: with the key first, a run interrupted after it is never repaired. -/
#eval refuted (∀ (c₁ c₂ c : Fin 16) (d g : Fin 2) (l₀ : List (Fin 2)),
  same (ingest (src c₁ c₂ d g) (run ((src c₁ c₂ d g).stepsKeyFirst.take 1) (st c l₀ [])))
    (ingest (src c₁ c₂ d g) (st c l₀ [])) = true) 254

/- DOR-6: the receipt is complete and its digest is the chain's head. -/
#eval survives (∀ (c₁ c₂ c : Fin 16) (d g : Fin 2) (l₀ l₁ : List (Fin 2)),
  ((ingest (src c₁ c₂ d g) (st c l₀ l₁)).rows == (st c l₀ l₁).rows ∪ (receipt (src c₁ c₂ d g)).rows
    && ((ingest (src c₁ c₂ d g) (st c l₀ l₁)).chain d).getLast? == some g) = true) 250

/- DOR-5: a re-ingest embeds nothing. -/
#eval survives (∀ (c₁ c₂ c : Fin 16) (d g : Fin 2) (l₀ l₁ : List (Fin 2)),
  embeds isAtom (src c₁ c₂ d g) (ingest (src c₁ c₂ d g) (st c l₀ l₁)) = 0) 251

/- DOR-5: two commands sharing an atom pay for it once. -/
#eval survives (∀ (c₁ c₂ c : Fin 16) (g g' : Fin 2) (l₀ l₁ : List (Fin 2)),
  embeds isAtom (src1 c₁ 0 g) (st c l₀ l₁)
      + embeds isAtom (src1 c₂ 1 g') (ingest (src1 c₁ 0 g) (st c l₀ l₁))
    = (atomsOf isAtom (rowsOf c₁ ∪ rowsOf c₂) \ rowsOf c).card) 255

/- DOR-9: an interleaving of two commands' steps on distinct identities lands the batch: the
first command's rows, the whole second command, then the first command's landing and key. -/
#eval survives (∀ (c₁ c₂ c : Fin 16) (g g' : Fin 2) (l₀ l₁ : List (Fin 2)),
  same (run ((src1 c₁ 0 g).steps.take 1 ++ (src1 c₂ 1 g').steps
      ++ (src1 c₁ 0 g).steps.drop 1) (st c l₀ l₁))
    (batch [src1 c₁ 0 g, src1 c₂ 1 g'] (st c l₀ l₁)) = true) 252

/- Control: the same interleaving on one identity lands the other order's chain. -/
#eval refuted (∀ (c₁ c₂ c : Fin 16) (g g' : Fin 2) (l₀ l₁ : List (Fin 2)),
  same (run ((src1 c₁ 0 g).steps.take 1 ++ (src1 c₂ 0 g').steps
      ++ (src1 c₁ 0 g).steps.drop 1) (st c l₀ l₁))
    (batch [src1 c₁ 0 g, src1 c₂ 0 g'] (st c l₀ l₁)) = true) 253

/- DOR-3: three commands on three identities, in any of the six orders, land one state. -/
#eval survives (∀ (c₁ c₂ c₃ : Fin 16) (g₁ g₂ g₃ : Fin 2) (i : Fin 6),
  same3 (batch (([src3 c₁ 0 g₁, src3 c₂ 1 g₂, src3 c₃ 2 g₃].permutations).getD i.val []) st3)
    (batch [src3 c₁ 0 g₁, src3 c₂ 1 g₂, src3 c₃ 2 g₃] st3) = true) 256

/- DOR-3: a batch on distinct identities, run again, lands nothing. -/
#eval survives (∀ (c₁ c₂ c₃ : Fin 16) (g₁ g₂ g₃ : Fin 2),
  same3 (batch [src3 c₁ 0 g₁, src3 c₂ 1 g₂, src3 c₃ 2 g₃]
      (batch [src3 c₁ 0 g₁, src3 c₂ 1 g₂, src3 c₃ 2 g₃] st3))
    (batch [src3 c₁ 0 g₁, src3 c₂ 1 g₂, src3 c₃ 2 g₃] st3) = true) 257

/- DOR-10: two versions of one note and another note; a schedule that keeps each identity's
order (the other note first, the second version's rows before the first version lands, then the
second version's landing and key) lands the batch, when each command is fresh at its turn. -/
#eval survives (∀ (c₁ c₂ c₃ : Fin 16) (g g' g'' : Fin 2) (l₀ : List (Fin 2)),
  g ≠ g'' →
  same (run ((src1 c₂ 1 g').steps ++ (src1 c₃ 0 g'').steps.take 1 ++ (src1 c₁ 0 g).steps
      ++ (src1 c₃ 0 g'').steps.drop 1) (st 0 l₀ []))
    (batch [src1 c₁ 0 g, src1 c₂ 1 g', src1 c₃ 0 g''] (st 0 l₀ [])) = true) 258

/- Control, DOR-10: the same steps with the two versions' order swapped land the other chain. -/
#eval refuted (∀ (c₁ c₂ c₃ : Fin 16) (g g' g'' : Fin 2) (l₀ : List (Fin 2)),
  g ≠ g'' →
  same (run ((src1 c₂ 1 g').steps ++ (src1 c₃ 0 g'').steps ++ (src1 c₁ 0 g).steps)
      (st 0 l₀ []))
    (batch [src1 c₁ 0 g, src1 c₂ 1 g', src1 c₃ 0 g''] (st 0 l₀ [])) = true) 259

/- DOR-11: two commands on distinct identities, each stopped after a prefix of its own steps, in
the other order: the batch run again lands the uninterrupted batch. -/
#eval survives (∀ (k₁ k₂ : Fin 4) (c₁ c₂ : Fin 16) (g g' : Fin 2) (l₀ : List (Fin 2)),
  same (batch [src1 c₁ 0 g, src1 c₂ 1 g']
      (run ((src1 c₂ 1 g').steps.take k₂.val ++ (src1 c₁ 0 g).steps.take k₁.val) (st 0 l₀ [])))
    (batch [src1 c₁ 0 g, src1 c₂ 1 g'] (st 0 l₀ [])) = true) 260

/- Control, DOR-11: a command whose run is not a prefix of its own steps (its key without its
rows) beside a whole one is never repaired by the re-run. -/
#eval refuted (∀ (c₁ c₂ : Fin 16) (g g' : Fin 2) (l₀ : List (Fin 2)),
  same (batch [src1 c₁ 0 g, src1 c₂ 1 g']
      (run ((src1 c₁ 0 g).stepsKeyFirst.take 1 ++ (src1 c₂ 1 g').steps) (st 0 l₀ [])))
    (batch [src1 c₁ 0 g, src1 c₂ 1 g'] (st 0 l₀ [])) = true) 261

/-- A state is sound for a command: a key naming its digest finds its rows held (decided). -/
def sound (x : Source (Fin 4) (Fin 2) (Fin 2)) (t : State (Fin 4) (Fin 2) (Fin 2)) : Bool :=
  t.key x.ident != some x.digest || decide (x.rows ⊆ t.rows)

/- DOR-12: a key-last run stopped after any step is sound for its command: a reader that trusts
the key sees the version whole or not at all. -/
#eval survives (∀ (k : Fin 5) (c₁ c₂ c : Fin 16) (d g : Fin 2) (l₀ : List (Fin 2)),
  sound (src c₁ c₂ d g) (run ((src c₁ c₂ d g).steps.take k.val) (st c l₀ [])) = true) 262

/- Control, DOR-12: with the key first, a reader that trusts the key sees rows that are not
there. -/
#eval refuted (∀ (c₁ c₂ c : Fin 16) (d g : Fin 2) (l₀ : List (Fin 2)),
  sound (src c₁ c₂ d g) (run ((src c₁ c₂ d g).stepsKeyFirst.take 1) (st c l₀ [])) = true) 263

/- DOR-12: two commands on distinct identities stopped at any prefixes, in the other order: both
are sound. -/
#eval survives (∀ (k₁ k₂ : Fin 4) (c₁ c₂ : Fin 16) (g g' : Fin 2) (l₀ : List (Fin 2)),
  (sound (src1 c₁ 0 g)
      (run ((src1 c₂ 1 g').steps.take k₂.val ++ (src1 c₁ 0 g).steps.take k₁.val) (st 0 l₀ []))
    && sound (src1 c₂ 1 g')
      (run ((src1 c₂ 1 g').steps.take k₂.val ++ (src1 c₁ 0 g).steps.take k₁.val) (st 0 l₀ [])))
    = true) 264

/-- A state holding version `g` of identity 0, its key naming it, the chain `l₀` then `g`. -/
def held (c : Fin 16) (l₀ : List (Fin 2)) (g : Fin 2) : State (Fin 4) (Fin 2) (Fin 2) :=
  ⟨rowsOf c, fun d ↦ if d = 0 then l₀ ++ [g] else [], fun d ↦ if d = 0 then some g else none⟩

/- DOR-7 in the code's order: a run stopped after any two of a command's steps but its key, in
either order, converges under re-run. -/
#eval survives (∀ (i j : Fin 3) (c₁ c₂ : Fin 16) (d g : Fin 2) (l₀ : List (Fin 2)),
  same (ingest (src c₁ c₂ d g) (run [(src c₁ c₂ d g).steps.getD j.val (Step.rows ∅),
                                     (src c₁ c₂ d g).steps.getD i.val (Step.rows ∅)] (st 0 l₀ [])))
    (ingest (src c₁ c₂ d g) (st 0 l₀ [])) = true) 265

/- DOR-10 from a held version: an edit and a revert of one note, the revert's rows first, the edit
whole, then the revert's landing and key; the model's steps carry no guard, and this schedule
lands the batch. -/
#eval survives (∀ (c₁ c₂ c : Fin 16) (g g' : Fin 2) (l₀ : List (Fin 2)),
  g ≠ g' →
  same (run ((src1 c₂ 0 g).steps.take 1 ++ (src1 c₁ 0 g').steps ++ (src1 c₂ 0 g).steps.drop 1)
      (held c l₀ g))
    (batch [src1 c₁ 0 g', src1 c₂ 0 g] (held c l₀ g)) = true) 266

/- Control, DOR-10: the same two commands with the revert's guard read before the edit's key: it
finds its own digest, skips, and the note ends at the edit. -/
#eval refuted (∀ (c₁ c₂ c : Fin 16) (g g' : Fin 2) (l₀ : List (Fin 2)),
  g ≠ g' →
  same (batch [src1 c₁ 0 g'] (ingest (src1 c₂ 0 g) (held c l₀ g)))
    (batch [src1 c₁ 0 g', src1 c₂ 0 g] (held c l₀ g)) = true) 267

/- Control, DOR-11: two versions of one note, the second run whole before the first starts: the
batch run again lands a chain the uninterrupted batch never would. -/
#eval refuted (∀ (c₁ c₂ : Fin 16) (g g' : Fin 2) (l₀ : List (Fin 2)),
  g ≠ g' →
  same (batch [src1 c₁ 0 g, src1 c₂ 0 g'] (run (src1 c₂ 0 g').steps (st 0 l₀ [])))
    (batch [src1 c₁ 0 g, src1 c₂ 0 g'] (st 0 l₀ [])) = true) 268

/- Control, DOR-7 in the audit's defect 1's own order: the plane's rows, then the key, the run
interrupted there; the steps after the key never run again. -/
#eval refuted (∀ (c₁ c₂ c : Fin 16) (d g : Fin 2) (l₀ : List (Fin 2)),
  same (ingest (src c₁ c₂ d g)
      (run ((src c₁ c₂ d g).steps.take 1 ++ [Step.key d g]) (st c l₀ [])))
    (ingest (src c₁ c₂ d g) (st c l₀ [])) = true) 269

/- DOR-10 with the guard: from a held version, an edit, the same edit again with other rows (keyed
at its turn, so the guard skips it) and another note; a schedule of the steps of the two that
land, the other note between the edit's rows and its landing, lands the whole list. -/
#eval survives (∀ (c₁ c₂ c₃ : Fin 16) (g g' g'' : Fin 2) (l₀ : List (Fin 2)),
  g ≠ g' →
  same (run ((src1 c₁ 0 g').steps.take 1 ++ (src1 c₃ 1 g'').steps ++ (src1 c₁ 0 g').steps.drop 1)
      (held 0 l₀ g))
    (batch [src1 c₁ 0 g', src1 c₂ 0 g', src1 c₃ 1 g''] (held 0 l₀ g)) = true) 270

/- DOR-11 with repeated identities: one note edited, edited back and edited again, in order, the
run stopped inside the third; running the third again alone lands the uninterrupted batch. -/
#eval survives (∀ (k : Fin 4) (c₁ c₂ c₃ : Fin 16) (g g' : Fin 2) (l₀ : List (Fin 2)),
  g ≠ g' →
  same (batch [src1 c₃ 0 g]
      (run ((src1 c₁ 0 g).steps ++ (src1 c₂ 0 g').steps ++ (src1 c₃ 0 g).steps.take k.val)
        (st 0 l₀ [])))
    (batch [src1 c₁ 0 g, src1 c₂ 0 g', src1 c₃ 0 g] (st 0 l₀ [])) = true) 271

/- Control, DOR-11: the same run stopped after the third's landing, the whole batch run again: the
first command finds the second's key and lands again. -/
#eval refuted (∀ (c₁ c₂ c₃ : Fin 16) (g g' : Fin 2) (l₀ : List (Fin 2)),
  g ≠ g' →
  same (batch [src1 c₁ 0 g, src1 c₂ 0 g', src1 c₃ 0 g]
      (run ((src1 c₁ 0 g).steps ++ (src1 c₂ 0 g').steps ++ (src1 c₃ 0 g).steps.take 2)
        (st 0 l₀ [])))
    (batch [src1 c₁ 0 g, src1 c₂ 0 g', src1 c₃ 0 g] (st 0 l₀ [])) = true) 272

end Palace.Door.Attack
