module

public import Mathlib.Data.List.Basic
public import Mathlib.Data.Option.Basic

/-!
# The code lineage reader: chain members and the ledger's versions (#50), the definitions

A model of `ops/code_lineage.py` at one path: the snapshots ledger's commits, each commit's first
parent and tree, the per-commit first-parent diffs (`commit_diffs`), and the loop that threads
them into the path's supersession chain (`supersession_chains`). The theorems are in
`Palace/Lineage.lean`.
-/

@[expose] public section

namespace Palace.Lineage

/-- A history: each commit's first parent (`none` at a root, whose diff is against the empty
tree) and its tree, the blob each path holds (`none` where the path is absent). -/
structure History (C P B : Type*) where
  /-- The first parent (`rev-parse c^@`, its head). -/
  parent : C → Option C
  /-- The tree: the blob at each path. -/
  tree : C → P → Option B

variable {C P B : Type*}

namespace History

/-- The blob at `p` before commit `c`: in its first parent's tree, none at a root. -/
def before (h : History C P B) (c : C) (p : P) : Option B := (h.parent c).bind (h.tree · p)

/-- `commit_diffs` at `p` in the ledger's order `L` (the `snapshots` rowid walk): one row
`(old_blob, new_blob)` for each commit whose blob at `p` differs from its first parent's, `none`
for git's absent blob (the code's `''`). -/
def rows [DecidableEq B] (h : History C P B) (L : List C) (p : P) : List (Option B × Option B) :=
  L.filterMap fun c ↦ if h.before c p = h.tree c p then none else some (h.before c p, h.tree c p)

/-- The ledger's versions at `p`: the blobs some ledger commit's tree holds there
(`ledger_versions`). -/
def Version (h : History C P B) (L : List C) (p : P) (b : B) : Prop :=
  ∃ c ∈ L, h.tree c p = some b

/-- HEAD's first-parent line, `fuel` commits deep at most (`rev-list --first-parent HEAD`). -/
def line (h : History C P B) : ℕ → C → List C
  | 0, _ => []
  | n + 1, c => c :: ((h.parent c).map (h.line n)).getD []

end History

/-- One row of `supersession_chains`' loop: while the chain is empty a row's old blob starts it,
then its new blob is appended unless the chain already ends there (adjacent repeats collapse). -/
def step [DecidableEq B] (chain : List B) (x : Option B × Option B) : List B :=
  let chain := if chain = [] then x.1.toList else chain
  match x.2 with
  | some n => if chain.getLast? = some n then chain else chain ++ [n]
  | none => chain

/-- The path's chain: the loop over its rows from the empty chain. -/
def thread [DecidableEq B] (rs : List (Option B × Option B)) : List B := rs.foldl step []

/-- `supersession_chains(db)[p]`. -/
def History.chain [DecidableEq B] (h : History C P B) (L : List C) (p : P) : List B :=
  thread (h.rows L p)

namespace Witness

/-- A side branch: `m1` (0), a side branch from it `s1` (1) and `s2` (3), main's `m2` (2), and the
merge (4) whose first parent is `m2`; each commit holds a blob of its own at the one path, and the
ledger lists them by commit date, `m1 s1 m2 s2 merge`. -/
def side : History (Fin 5) Unit (Fin 5) where
  parent c := match c.val with
    | 1 => some 0
    | 2 => some 0
    | 3 => some 1
    | 4 => some 2
    | _ => none
  tree c _ := some c

/-- The ledger's order. -/
def ledger : List (Fin 5) := [0, 1, 2, 3, 4]

end Witness

end Palace.Lineage
