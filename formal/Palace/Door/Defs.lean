module

public import Mathlib.Data.Finset.Card
public import Mathlib.Data.Finset.SDiff
public import Mathlib.Data.List.Perm.Basic
public import Palace.Sentence.Defs

/-!
# The door: the model

Ingestion as the sentence `do …` (dn-ingest-door). A source is what the door derives from it, by
stage: the rows each stage adds to the append-only stores (the raw object, the chunks, the atoms
with their vectors, the occupancies), the identity whose version chain it extends and the digest
of the version it lands. All are functions of the source, which is content addressing. A store
state is the rows the stores hold, each identity's chain of digests, the one ordered thing in the
system, and each identity's **key**: the catalog's digest for it, which the UNCHANGED check reads
and which the landing order writes last. The operation lands nothing when the key already names
the digest; otherwise it adds the rows, extends the chain and sets the key. A run is a list of
steps, so a command's own order, and the interleaving of several commands' stages, can be stated.
-/

@[expose] public section

open Finset

namespace Palace.Door

/-- A source: the rows it adds, by stage; the identity whose chain it extends; its digest. -/
structure Source (R D G : Type*) where
  /-- The rows each stage adds: the raw object, the chunks, the atoms, the occupancies. -/
  stages : List (Finset R)
  /-- The identity whose version chain the command extends. -/
  ident : D
  /-- The digest of the version it lands. -/
  digest : G

/-- A store state: the rows the append-only stores hold, each identity's chain, and each
identity's key, the catalog's digest for it, the idempotence key. -/
@[ext]
structure State (R D G : Type*) where
  /-- The rows the append-only stores hold. -/
  rows : Finset R
  /-- Each identity's chain of version digests, the one ordered thing. -/
  chain : D → List G
  /-- Each identity's key: the digest the catalog holds for it, read by the UNCHANGED check. -/
  key : D → Option G

variable {R D G : Type*} [DecidableEq R] [DecidableEq D] [DecidableEq G]

/-- The rows a source adds, all stages together. -/
def Source.rows (x : Source R D G) : Finset R := x.stages.foldr (· ∪ ·) ∅

/-- Append a digest to a chain unless it is already the head: the version store records a
version only on a change (`core/ingest/landing.py::record_version_if_new`); a revert to older
bytes still appends, since the head differs (ingest-identity-and-amendment §4A C1). -/
def appendIfNew (c : List G) (g : G) : List G := if c.getLast? = some g then c else c ++ [g]

/-- The landing, unguarded: the rows are added, the chain is extended, the key is set. -/
def land (x : Source R D G) (s : State R D G) : State R D G :=
  ⟨s.rows ∪ x.rows,
   fun d ↦ if d = x.ident then appendIfNew (s.chain d) x.digest else s.chain d,
   fun d ↦ if d = x.ident then some x.digest else s.key d⟩

/-- The operation: the UNCHANGED check reads the key, and a command whose key already names its
digest lands nothing; otherwise it lands. -/
def ingest (x : Source R D G) (s : State R D G) : State R D G :=
  if s.key x.ident = some x.digest then s else land x s

/-- A batch of commands, landed in list order. -/
def batch (l : List (Source R D G)) (s : State R D G) : State R D G :=
  l.foldl (fun s x ↦ ingest x s) s

/-- A command is fresh at a state when its key does not name its digest: the check lets it run. -/
def Fresh (x : Source R D G) (s : State R D G) : Prop := s.key x.ident ≠ some x.digest

/-- A state is sound for a command when a key naming its digest implies its rows are held: what
the landing order guarantees, since the key is the last write. -/
def Sound (x : Source R D G) (s : State R D G) : Prop :=
  s.key x.ident = some x.digest → x.rows ⊆ s.rows

/-- One step of a run: a stage's rows, the landing of a version on an identity's chain, or the
writing of an identity's key. -/
inductive Step (R D G : Type*)
  | rows (t : Finset R)
  | land (d : D) (g : G)
  | key (d : D) (g : G)

/-- Apply one step. -/
def Step.apply : Step R D G → State R D G → State R D G
  | .rows t, s => ⟨s.rows ∪ t, s.chain, s.key⟩
  | .land d g, s => ⟨s.rows, fun e ↦ if e = d then appendIfNew (s.chain e) g else s.chain e, s.key⟩
  | .key d g, s => ⟨s.rows, s.chain, fun e ↦ if e = d then some g else s.key e⟩

/-- A run: steps in order. -/
def run (w : List (Step R D G)) (s : State R D G) : State R D G :=
  w.foldl (fun s a ↦ a.apply s) s

/-- A command's steps in the landing order: its stages' rows, its landing, and its key last
(dn-ingest-door D1). -/
def Source.steps (x : Source R D G) : List (Step R D G) :=
  x.stages.map Step.rows ++ [Step.land x.ident x.digest, Step.key x.ident x.digest]

/-- The key first, then the rest: the extreme of the audit's defect 1, which wrote the key after
the plane's rows and before the attestation and the version row. -/
def Source.stepsKeyFirst (x : Source R D G) : List (Step R D G) :=
  Step.key x.ident x.digest :: (x.stages.map Step.rows ++ [Step.land x.ident x.digest])

/-- The identity a step writes, if it lands or keys one. -/
def Step.ident : Step R D G → Option D
  | .rows _ => none
  | .land d _ => some d
  | .key d _ => some d

/-- Two steps conflict when both land, or both key, one identity: the only pairs that do not
commute. -/
def Step.Conflicts : Step R D G → Step R D G → Prop
  | .land d _, .land e _ => d = e
  | .key d _, .key e _ => d = e
  | _, _ => False

/-- The steps of a list of commands, in list order. -/
def stepsOf (l : List (Source R D G)) : List (Step R D G) := l.flatMap Source.steps

/-- The class of a step: two steps conflict exactly when they share one, the landings on one
identity or the keys of one identity; a stage's rows have none and conflict with nothing. -/
def Step.cls : Step R D G → Option (Bool × D)
  | .rows _ => none
  | .land d _ => some (false, d)
  | .key d _ => some (true, d)

/-- Each command is fresh at its turn of the serial order, so the guard lets every one run. With
repeated identities a command whose digest is its identity's key at its turn is not fresh: the
queue's guard skips it, and the serial order it would have joined is the list without it. -/
def FreshAlong : List (Source R D G) → State R D G → Prop
  | [], _ => True
  | x :: l, s => Fresh x s ∧ FreshAlong l (land x s)

/-- The commands of a list that land when it runs in order: those fresh at their turn. The guard
skips the others, so the batch is theirs (`batch_landsOf`), and they are fresh along their own
order (`freshAlong_landsOf`). -/
def landsOf : List (Source R D G) → State R D G → List (Source R D G)
  | [], _ => []
  | x :: l, s => if s.key x.ident = some x.digest then landsOf l s else x :: landsOf l (land x s)

/-- What a batch's run has done when it stops: each command a prefix of its own steps, `k x` of
them, the commands' order being the list's (any other order of the same steps is a permutation
of this one). -/
def prefixesOf (k : Source R D G → ℕ) (l : List (Source R D G)) : List (Step R D G) :=
  l.flatMap fun x ↦ x.steps.take (k x)

/-- What the door reports after landing: the rows the command adds, the identity, the digest;
a function of the source, as the attestation's output hashes are. -/
structure Receipt (R D G : Type*) where
  /-- The rows the command added. -/
  rows : Finset R
  /-- The identity whose chain it extended. -/
  ident : D
  /-- The digest it landed, the chain's new head. -/
  digest : G

/-- The receipt of a command. -/
def receipt (x : Source R D G) : Receipt R D G := ⟨x.rows, x.ident, x.digest⟩

/-- The atoms among a set of rows: the texts the plane holds once each (the shared plane A3). -/
def atomsOf (IsAtom : R → Prop) [DecidablePred IsAtom] (t : Finset R) : Finset R :=
  t.filter IsAtom

/-- The embeds a command costs: the atoms it adds that the plane does not hold. -/
def embeds (IsAtom : R → Prop) [DecidablePred IsAtom] (x : Source R D G) (s : State R D G) : ℕ :=
  (atomsOf IsAtom x.rows \ s.rows).card

/-- The embeds a batch costs, command by command, each on the state the previous ones left. -/
def embedsBatch (IsAtom : R → Prop) [DecidablePred IsAtom] :
    List (Source R D G) → State R D G → ℕ
  | [], _ => 0
  | x :: l, s => embeds IsAtom x s + embedsBatch IsAtom l (ingest x s)

/-- The rows of a batch, all commands together. -/
def rowsOf (l : List (Source R D G)) : Finset R := l.foldr (fun x acc ↦ x.rows ∪ acc) ∅

/-- A command clause of the sentence model: one that requires the projection-write bit
(`capability-scope-algebra` §2.2, `Authority.storeWrite`). By the convention of
`core/sentence/types.py::_command_clause`, the clause's `sigma` is the set of strata the command
writes, closed downward, and its clock is the stratum's; the model states nothing more about
which strata a command writes than that. -/
def IsCommand (c : Palace.Query.Clause) : Prop := c.req.authority.storeWrite = 1

/-- The scope `_command_clause` requires of a command writing `strata` at `clock`: the write
bit, no fibers, the point window at the anchor. -/
def commandScope (strata : Finset CQ.Stratum) (clock : CQ.Clock) : CQ.Scope :=
  ⟨CQ.close strata, ∅, ⟨clock, .point CQ.anchor⟩, ⟨0, 1, 0⟩, 1, none⟩

end Palace.Door
