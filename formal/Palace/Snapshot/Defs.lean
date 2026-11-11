module

public import Mathlib.Data.List.Basic
public import Mathlib.Logic.Function.Basic
public import Mathlib.Order.Basic
public import Mathlib.Order.SetNotation

/-!
# The temporal snapshot: the model

dn-temporal-snapshot, on the clock's cuts (`Palace/Clock/Defs.lean`, CLK-2). A **store** is a
family of append chains: for every chain key the events appended to it, in order. The palace's
ledgers are such families (a document's versions, a session's turns, a class's landing log, the
attestations), and a chain only grows at its end. A **cut** is a prefix length for every chain,
the vector of per-chain positions of dn-global-event-clock §2.4. The **read at a cut** is the
prefix of every chain, the **read between two cuts** the events after the first and up to the
second, and a **derived view** at a cut is a derivation applied to the prefixes.

What is derived can be held three ways, and the model has each: recomputed from the prefix
(`stateAt`, the fold of a chain of keyed writes), journaled (the same fold continued from a
checkpoint over the events between two cuts, `foldAt`), or kept by generation (`gens`: one row
per write, valid from the cut that contains it up to the cut that contains the key's next write,
read by `genRead`). The store rewritten in place is `stateOf`, the fold of the whole chain, which
has no past. Retention drops the generations closed at or under a horizon (`prune`), after which
the store serves the cuts from the horizon on.

Two things are parameters of a read and no function of the cut, because they are the present's:
the asker's **grant** (`snapshot`: the chains it names and the events it may see named) and the
**erasure** (`visible`: the erased events masked; `redact`: the store with a hole at each, every
position kept; `servedAt`: a key retired after the cut is served at no earlier cut, with
`servedNow` the looser seal that a later landing lifts). The control for the erasure is
`compact`, an erasure that deletes rows and lets the later ones move up.

Events may read from events of other chains (`R k i k' j`: the `i`-th event of chain `k` reads
from the `j`-th of chain `k'`); a cut is **consistent** when every source of an event inside it is
inside it, and a frontier **resolves** to the greatest consistent cut under it, or, where a store
serves only some positions (those from its horizon on, and the empty prefix), to the greatest
consistent cut under it among the served positions (`ResolvesIn`). A cut is
**certified** by the digest of each chain's prefix under a chain digest (`chainDigest`, a fold),
and a later store **verifies** the certificate when its own prefixes have those digests. A store
that keeps a commitment beside each event (`committed`) can lose an event's content to an erasure
(`purge`) and keep every certificate.
-/

@[expose] public section

namespace Palace.Snapshot

/-- A store: a family of append chains, the events of each chain in the order they were
appended. -/
abbrev Store (K α : Type*) := K → List α

/-- A cut: a prefix length for every chain (dn-global-event-clock §2.4, the vector of per-chain
positions). -/
abbrev Cut (K : Type*) := K → ℕ

/-! ### Reads -/

section Reads

variable {K α β : Type*}

/-- The head cut: every chain whole. -/
def head (s : Store K α) : Cut K := fun k ↦ (s k).length

/-- The store grown by appending `t`, chain by chain. -/
def grow (s t : Store K α) : Store K α := fun k ↦ s k ++ t k

/-- `s'` extends `s`: every chain of `s` is a prefix of its chain in `s'`, which is all an
append-only store can do. -/
def Extends (s s' : Store K α) : Prop := ∀ k, s k <+: s' k

/-- The read at a cut: the prefix of every chain. -/
def readAt (s : Store K α) (c : Cut K) : Store K α := fun k ↦ (s k).take (c k)

/-- The read between two cuts: the events after `a` and up to `b`, chain by chain. -/
def readBetween (s : Store K α) (a b : Cut K) : Store K α :=
  fun k ↦ ((s k).take (b k)).drop (a k)

/-- A derived view at a cut: the derivation applied to the prefixes. -/
def view (D : Store K α → β) (s : Store K α) (c : Cut K) : β := D (readAt s c)

/-- The reader that ignores the cut: the derivation applied to the whole store, which is what a
verb reads of a store that keeps no past. -/
def present (D : Store K α → β) : Store K α → Cut K → β := fun s _ ↦ D s

/-- A reader of a store at a cut is append invariant when no growth of the store changes what it
reads at a cut inside the store. -/
def AppendInvariant (F : Store K α → Cut K → β) : Prop :=
  ∀ s t c, c ≤ head s → F (grow s t) c = F s c

/-- A reader reads only the prefixes when what it reads at a cut inside the store is what it
reads of the prefixes alone. -/
def PrefixOnly (F : Store K α → Cut K → β) : Prop :=
  ∀ s c, c ≤ head s → F s c = F (readAt s c) c

/-- A journaled view: every chain's prefix folded by a step function from the chain's start
value. A job that keeps such a state and a checkpoint continues the fold over the events between
its checkpoint and a later cut. -/
def foldAt (f : β → α → β) (init : K → β) (s : Store K α) (c : Cut K) : K → β :=
  fun k ↦ ((s k).take (c k)).foldl f (init k)

end Reads

/-! ### A derived store, three ways -/

section Generations

variable {κ β : Type*}

/-- The store rewritten in place: after a chain of keyed writes, each key's last value. It is
the fold of the whole chain, so it has no past. -/
def stateOf [DecidableEq κ] (l : List (κ × β)) : κ → Option β :=
  l.foldl (fun m e ↦ Function.update m e.1 (some e.2)) fun _ ↦ none

/-- The state at a cut, recomputed from the chain's prefix. -/
def stateAt [DecidableEq κ] (l : List (κ × β)) (c : ℕ) : κ → Option β := stateOf (l.take c)

/-- The state at a cut read off the chain by one seek: the last write of the key inside the
prefix. -/
def lastWrite [DecidableEq κ] (l : List (κ × β)) (c : ℕ) (x : κ) : Option β :=
  ((l.take c).reverse.find? fun e ↦ decide (e.1 = x)).map Prod.snd

/-- A generation: one write of a key, valid from the cut `born` up to, and not at, the cut
`died`. -/
structure Gen (κ β : Type*) where
  /-- The key written. -/
  key : κ
  /-- The value written. -/
  val : β
  /-- The first cut that contains the write. -/
  born : ℕ
  /-- The first cut that contains the key's next write; `none` while the row is the key's
  head. -/
  died : Option ℕ

/-- A generation is alive at a cut from its birth up to, and not at, its death. -/
def Gen.aliveAt (r : Gen κ β) (c : ℕ) : Bool :=
  decide (r.born ≤ c) && r.died.all fun d ↦ decide (c < d)

/-- Close a row at position `p` when it is the open row of the key `x`; any other row is left
as it is. The closing stamp is the one field ever written after a row is appended, and it is a
function of the rows: the position of the key's next write. -/
def closeAt [DecidableEq κ] (x : κ) (p : ℕ) (r : Gen κ β) : Gen κ β :=
  if r.key = x ∧ r.died = none then { r with died := some p } else r

/-- One landing in the generational store, at position `p`: the key's open row is closed at `p`
and the write's own row opens there. -/
def landGen [DecidableEq κ] (rs : List (Gen κ β)) (p : ℕ) (e : κ × β) : List (Gen κ β) :=
  rs.map (closeAt e.1 p) ++ [⟨e.1, e.2, p, none⟩]

/-- The generational store of a chain given newest first: the write over `n` older ones lands at
position `n + 1`, the first cut that contains it. -/
def gensRev [DecidableEq κ] : List (κ × β) → List (Gen κ β)
  | [] => []
  | e :: older => landGen (gensRev older) (older.length + 1) e

/-- The generational store after a chain of keyed writes. -/
def gens [DecidableEq κ] (l : List (κ × β)) : List (Gen κ β) := gensRev l.reverse

/-- What a read of the generational store selects: the rows of the key alive at the cut. -/
def selects [DecidableEq κ] (c : ℕ) (x : κ) (r : Gen κ β) : Bool :=
  decide (r.key = x) && r.aliveAt c

/-- The read of the generational store at a cut: the value of the key's row alive there. -/
def genRead [DecidableEq κ] (rs : List (Gen κ β)) (c : ℕ) (x : κ) : Option β :=
  (rs.find? (selects c x)).map Gen.val

/-- Retention by a horizon: the generations kept are those whose closing stamp, if any, lies past
the horizon. A row closed at or under the horizon is alive at no cut from the horizon on. -/
def prune (h : ℕ) (rs : List (Gen κ β)) : List (Gen κ β) :=
  rs.filter fun r ↦ r.died.all fun d ↦ decide (h < d)

/-- A key is sealed at a cut when the chain retires it after the cut: a retire, the write of
`none`, among the events the cut does not contain. -/
def sealedAt [DecidableEq κ] (l : List (κ × Option β)) (c : ℕ) (x : κ) : Bool :=
  (l.drop c).any fun e ↦ decide (e.1 = x) && e.2.isNone

/-- What a chain of landings and retires serves of a key at a cut: nothing when the key is
sealed there, else the value the key held at the cut, if it was live. The seal is read off the
whole chain, the present, and no prefix of it. -/
def servedAt [DecidableEq κ] (l : List (κ × Option β)) (c : ℕ) (x : κ) : Option β :=
  if sealedAt l c x then none else (stateAt l c x).join

/-- The looser seal: a key is withheld at every cut exactly while it is not live at the head, so
a key landed again after its retire is served again at the cuts before the retire. -/
def servedNow [DecidableEq κ] (l : List (κ × Option β)) (c : ℕ) (x : κ) : Option β :=
  if ((stateOf l x).join).isNone then none else (stateAt l c x).join

end Generations

/-! ### The grant and the erasure, the present's -/

section Present

variable {K α β C : Type*}

/-- A family of chains restricted to the chains `G` names and, within them, to the events `p`
admits. -/
def restrict (G : K → Prop) [DecidablePred G] (p : α → Bool) (t : Store K α) : Store K α :=
  fun k ↦ if G k then (t k).filter p else []

/-- What a grant reads of a store at a cut: the chains it names, each read at the cut and kept to
the events it may see named. The grant is no function of the cut: it is the asker's now. -/
def snapshot (G : K → Prop) [DecidablePred G] (p : α → Bool) (s : Store K α) (c : Cut K) :
    Store K α :=
  restrict G p (readAt s c)

/-- The store with every erased event replaced by a hole: the erasure keeps every position. -/
def redact (E : α → Bool) (s : Store K α) : Store K (Option α) :=
  fun k ↦ (s k).map fun a ↦ if E a then none else some a

/-- What is visible at a cut once `E` is erased: the prefixes without the erased events. The
erasure is no function of the cut either. -/
def visible (E : α → Bool) (s : Store K α) (c : Cut K) : Store K α :=
  fun k ↦ ((s k).take (c k)).filter fun a ↦ !E a

/-- The control: an erasure that deletes the rows, so that the later ones move up. -/
def compact (E : α → Bool) (s : Store K α) : Store K α :=
  fun k ↦ (s k).filter fun a ↦ !E a

/-- The kept derived rows that may be served once `E` is erased: those none of whose sources is
erased. A row is its sources and its value. -/
def serve (E : α → Bool) (rows : List (List α × β)) : List (List α × β) :=
  rows.filter fun r ↦ r.1.all fun a ↦ !E a

/-- A store that keeps a commitment beside each event: the pair of the event's commitment and
its content. -/
def committed (commit : α → C) (s : Store K α) : Store K (C × Option α) :=
  fun k ↦ (s k).map fun a ↦ (commit a, some a)

/-- The erasure on a committed store: the content of every erased event goes, its commitment
and its position stay. -/
def purge (E : α → Bool) (t : Store K (C × Option α)) : Store K (C × Option α) :=
  fun k ↦ (t k).map fun x ↦ (x.1, x.2.filter fun a ↦ !E a)

/-- The commitments of a committed store, chain by chain: what a certificate digests. -/
def commitments (t : Store K (C × Option α)) : Store K C := fun k ↦ (t k).map Prod.fst

/-- The contents of a committed store, chain by chain, a hole where an event was erased: what a
reader reads. -/
def contents (t : Store K (C × Option α)) : Store K (Option α) := fun k ↦ (t k).map Prod.snd

end Present

/-! ### Consistent cuts -/

section Consistency

variable {K : Type*}

/-- A cut is consistent for the reads-from relation `R` (`R k i k' j`: the `i`-th event of chain
`k` reads from the `j`-th event of chain `k'`) when every source of an event inside the cut is
inside it: no fact whose sources lie after the cut. -/
def Consistent (R : K → ℕ → K → ℕ → Prop) (c : Cut K) : Prop :=
  ∀ k i k' j, R k i k' j → i < c k → j < c k'

/-- The generator edges of the clock on events as (chain, index) pairs: an earlier event of a
chain is before a later one (g1), and a source is before its reader (g2). -/
def generator (R : K → ℕ → K → ℕ → Prop) (a b : K × ℕ) : Prop :=
  (a.1 = b.1 ∧ a.2 < b.2) ∨ R b.1 b.2 a.1 a.2

/-- The positions of chain `k` that some consistent cut under the frontier `f` reaches. -/
def reached (R : K → ℕ → K → ℕ → Prop) (f : Cut K) (k : K) : Set ℕ :=
  {n | ∃ d, Consistent R d ∧ d ≤ f ∧ d k = n}

/-- The cut `c` resolves the frontier `f`: it is the greatest consistent cut under `f`. A name
(a commit, a certificate, a wall time looked up in the bookmarks) selects a frontier; the read is
at the cut that resolves it. -/
def Resolves (R : K → ℕ → K → ℕ → Prop) (f c : Cut K) : Prop :=
  Consistent R c ∧ c ≤ f ∧ ∀ d, Consistent R d → d ≤ f → d ≤ c

/-- The positions of chain `k` that some consistent cut under the frontier `f`, every position
of which its chain serves, reaches. -/
def reachedIn (R : K → ℕ → K → ℕ → Prop) (S : K → Set ℕ) (f : Cut K) (k : K) : Set ℕ :=
  {n | ∃ d, Consistent R d ∧ (∀ k', d k' ∈ S k') ∧ d ≤ f ∧ d k = n}

/-- The cut `c` resolves the frontier `f` among the positions the chains serve: `S k` is the set
of positions at which the store of chain `k` can be read exactly (every position from its horizon
on, and the empty prefix), and `c` is the greatest consistent cut under `f` every position of
which is served. It is the cut a read is taken at when the cut asked cannot be served whole. -/
def ResolvesIn (R : K → ℕ → K → ℕ → Prop) (S : K → Set ℕ) (f c : Cut K) : Prop :=
  Consistent R c ∧ (∀ k, c k ∈ S k) ∧ c ≤ f ∧
    ∀ d, Consistent R d → (∀ k, d k ∈ S k) → d ≤ f → d ≤ c

end Consistency

/-! ### Certified cuts -/

section Certified

variable {K α H : Type*}

/-- The digest of a chain's prefix: the fold of a step function from a seed, the shape of a hash
chain. -/
def chainDigest (step : H → α → H) (h₀ : H) (l : List α) : H := l.foldl step h₀

/-- A step function is collision free when it is injective in the pair of the digest so far and
the event: the property a cryptographic hash is used for. -/
def CollisionFree (step : H → α → H) : Prop :=
  ∀ h a h' a', step h a = step h' a' → h = h' ∧ a = a'

/-- A certificate of a cut: the cut and the digest of every chain's prefix at it. -/
structure Certificate (K H : Type*) where
  /-- The cut certified. -/
  cut : Cut K
  /-- The digest of each chain's prefix at the cut. -/
  digest : K → H

/-- The certificate of a cut of a store. -/
def certify (step : H → α → H) (h₀ : H) (s : Store K α) (c : Cut K) : Certificate K H :=
  ⟨c, fun k ↦ chainDigest step h₀ ((s k).take (c k))⟩

/-- A store verifies a certificate when the cut lies inside it and its own prefixes at the cut
have the certified digests. -/
def Verifies (step : H → α → H) (h₀ : H) (z : Certificate K H) (s : Store K α) : Prop :=
  z.cut ≤ head s ∧ ∀ k, chainDigest step h₀ ((s k).take (z.cut k)) = z.digest k

end Certified

end Palace.Snapshot
