module

public import Mathlib.Data.Finset.Insert
public import Mathlib.Logic.Function.Basic

/-!
# Two-phase ingestion: the model

dn-two-phase-ingestion, on top of the ingress's keyed model (`Palace/Ingress/Defs.lean`) and the
plane's (`Palace/Plane/Defs.lean`). The embedder produces one relation of the store, semantic
similarity; every other relation and the lexical index are functions of an item's bytes and the
graph alone. So an item is **complete without its vector**: the landing writes its structure (its
bytes, label, edges and lexical units, taken here as one value `S`, since the laws read it only
through functions of it) and its key, and no vector. The vector is a **derived field** of the
structure and the embedder's identity `E`: the plane's atom table holds a structure's vector under
an identity once embedded (`atom`, content addressed, so the same bytes are embedded once and a
superseded version's atom stays as history), and the plane's current occupancy of an item under
an identity (`mark`) is the drain's own idempotence key, naming the structure whose rows it landed.
An item is **derived** under `e` when its mark names its current structure, **pending** when it is
keyed and the mark does not. The embed step writes the atom first and the mark last, as the plane
inserts atoms before its occupancy transaction (PLN-4); the drain derives every keyed item; the
code's drain derives the pending ones. What a reader sees is the **field**: a derived item's
vector, `none` for a pending one.
-/

@[expose] public section

open Finset

namespace Palace.Derived

/-- The store as the two phases see it: the items whose key is written, each item's landed
structure, the atom table per embedder identity, and each item's mark per identity. -/
@[ext]
structure State (I S V E : Type*) where
  /-- The items whose idempotence key the landing wrote (ING-7's key): the complete items. -/
  keyed : Finset I
  /-- What the landing wrote for an item: bytes, label, edges and lexical units, as one value. -/
  struct : I → Option S
  /-- The plane's atoms: a structure's vector under an identity, once embedded. -/
  atom : E → S → Option V
  /-- The plane's current occupancy of an item under an identity: the structure whose rows the
  drain landed, its key. -/
  mark : I → E → Option S

variable {I S V E : Type*} [DecidableEq I] [DecidableEq S] [DecidableEq E]

/-- The landing, as one step of this model: the item's structure and its key (that the key is its
last write inside is `Palace.Ingress`'s ING-7). It writes no atom and moves no mark. -/
def land (i : I) (σ : S) (s : State I S V E) : State I S V E :=
  ⟨insert i s.keyed, Function.update s.struct i (some σ), s.atom, s.mark⟩

/-- An item is complete when its key is written (ING-19). -/
def complete (s : State I S V E) (i : I) : Prop := i ∈ s.keyed

/-- An item is pending under an identity when it is keyed and the drain's mark does not name
its current structure: no vector yet, or an older version's. -/
def pending (s : State I S V E) (e : E) (i : I) : Prop :=
  i ∈ s.keyed ∧ s.mark i e ≠ s.struct i

instance (s : State I S V E) (i : I) : Decidable (complete s i) :=
  inferInstanceAs (Decidable (i ∈ s.keyed))

instance (s : State I S V E) (e : E) (i : I) : Decidable (pending s e i) :=
  inferInstanceAs (Decidable (i ∈ s.keyed ∧ s.mark i e ≠ s.struct i))

/-- What a reader sees of an item under an identity: the vector of its current structure when the
drain's mark names that structure, and `none` otherwise, pending reported as such. -/
def field (s : State I S V E) (e : E) (i : I) : Option V :=
  if i ∈ s.keyed ∧ s.mark i e = s.struct i then (s.struct i).bind (s.atom e) else none

/-- The embed step's first write: the atom of the item's current structure under `e`, the
embedder `f` applied to the structure (content addressing: the same structure gets the same
vector). An item without a key is left alone. -/
def writeAtom (f : E → S → V) (e : E) (i : I) (s : State I S V E) : State I S V E :=
  if i ∈ s.keyed then
    ⟨s.keyed, s.struct,
     fun e' τ ↦ if e' = e ∧ s.struct i = some τ then some (f e τ) else s.atom e' τ, s.mark⟩
  else s

/-- The embed step's last write: the mark, naming the item's current structure under `e`. -/
def writeMark (e : E) (i : I) (s : State I S V E) : State I S V E :=
  if i ∈ s.keyed then
    ⟨s.keyed, s.struct, s.atom, fun j e' ↦ if j = i ∧ e' = e then s.struct i else s.mark j e'⟩
  else s

/-- One step of a run: a landing, an atom write, or a mark write. -/
inductive Step (I S E : Type*)
  | land (i : I) (σ : S)
  | atom (e : E) (i : I)
  | mark (e : E) (i : I)

/-- Apply one step under the embedder `f`. -/
def Step.apply (f : E → S → V) : Step I S E → State I S V E → State I S V E
  | .land i σ, s => Palace.Derived.land i σ s
  | .atom e i, s => writeAtom f e i s
  | .mark e i, s => writeMark e i s

/-- A run: steps in order. -/
def run (f : E → S → V) (w : List (Step I S E)) (s : State I S V E) : State I S V E :=
  w.foldl (fun s a ↦ a.apply f s) s

/-- One item's derivation as the drain does it: its atom, then its mark, the key last. -/
def derive (e : E) (i : I) : List (Step I S E) := [.atom e i, .mark e i]

/-- The control's order: the mark first. -/
def deriveKeyFirst (e : E) (i : I) : List (Step I S E) := [.mark e i, .atom e i]

/-- Whether a step is a landing. -/
def Step.isLand : Step I S E → Bool
  | .land _ _ => true
  | _ => false

/-- The identity an embed step writes under; a landing writes under none. -/
def Step.at : Step I S E → Option E
  | .land _ _ => none
  | .atom e _ => some e
  | .mark e _ => some e

/-- A run whose embed steps are all under `e`. -/
def AllAt (e : E) (w : List (Step I S E)) : Prop := ∀ a ∈ w, a.isLand = true ∨ a.at = some e

/-- The drain under `e`, pointwise: every keyed item's structure gets its atom and every keyed
item its mark. -/
def drain (f : E → S → V) (e : E) (s : State I S V E) : State I S V E :=
  ⟨s.keyed, s.struct,
   fun e' τ ↦ if e' = e ∧ ∃ j ∈ s.keyed, s.struct j = some τ then some (f e τ) else s.atom e' τ,
   fun j e' ↦ if e' = e ∧ j ∈ s.keyed then s.struct j else s.mark j e'⟩

/-- The code's drain under `e`: the pending items alone (`core/ingest/derive.py::pending`), each
derived; a derived item is not read again, as the UNCHANGED check skips a keyed one. -/
def codeDrain (f : E → S → V) (e : E) (s : State I S V E) : State I S V E :=
  ⟨s.keyed, s.struct,
   fun e' τ ↦ if e' = e ∧ ∃ j ∈ s.keyed, s.mark j e ≠ s.struct j ∧ s.struct j = some τ
     then some (f e τ) else s.atom e' τ,
   fun j e' ↦ if e' = e ∧ j ∈ s.keyed ∧ s.mark j e ≠ s.struct j then s.struct j else s.mark j e'⟩

/-- A state is sound under `e` when every derived item has the atom its mark promises: what the
key-last order keeps, and the mark-first order breaks. -/
def Sound (s : State I S V E) (e : E) : Prop :=
  ∀ i ∈ s.keyed, s.mark i e = s.struct i → ∀ σ, s.struct i = some σ → (s.atom e σ).isSome = true

/-- The atom table holds true images: every atom is the embedder's vector of its structure. -/
def Truthful (f : E → S → V) (s : State I S V E) : Prop :=
  ∀ e σ v, s.atom e σ = some v → v = f e σ

/-- The control's reading: an item's vector read straight from the atom table, with zero for a
missing one, no mark consulted and no pending reported. -/
def zeroRead (score : V → ℤ) (s : State I S V E) (e : E) (i : I) : ℤ :=
  ((s.struct i).bind (s.atom e)).elim 0 score

end Palace.Derived
