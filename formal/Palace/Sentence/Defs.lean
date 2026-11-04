module

public import Palace.Scope.Defs
public import Palace.Balance.Defs
public import Mathlib.LinearAlgebra.Matrix.Hadamard

/-!
# The query sentence algebra, the definitions

`docs/design-notes/dn-query-sentence-algebra.md` makes a query a sentence: nouns (regions, fields,
kernels, chains), adjectives (`within`, `as of`, `via`), verbs (the operators of `core/query.py`),
connectives (`and`, `or`, `then`) and one modality (`assume`). This file defines the finite
algebra the laws are stated over, before any code parses a sentence:

* the nouns a clause evaluates to, and the adjectives on them: a region's indicator, `within` on a
  field and on a kernel, the field a kernel assigns to an anchor, the threshold and the top-`k`;
* a sentence's syntax over abstract clauses, the scopes it requires (one per clause, the overlay
  stratum added under `assume`), the strata it reads, the assumptions in force, and an evaluation
  model parametric in the clause evaluators;
* the move alphabet `Σ_move = {S, F, D, C}` (fiber-geometry §2.0), chains over a typed graph, a
  deterministic automaton over the moves, the product walk, and the set `E` as an automaton;
* a hypothetical edge on a weight matrix, and the vector its Laplacian update lies along.

`core/query.py`'s `mode_of` is transcribed as `modeOf`.
-/

@[expose] public section

open Matrix Finset

namespace Palace.Query

/-! ## Nouns: regions, fields and kernels -/

section Nouns

variable {V R : Type*} [Fintype V] [DecidableEq V]

/-- A region's indicator. -/
def ind [Zero R] [One R] (S : Finset V) : V → R := fun i ↦ if i ∈ S then 1 else 0

/-- `within S` on a field: the field, zero outside the region. -/
def maskF [Zero R] (S : Finset V) (f : V → R) : V → R := fun i ↦ if i ∈ S then f i else 0

/-- `within S` on a kernel: the kernel, zero outside `S × S`. -/
def mask [Zero R] (S : Finset V) (K : Matrix V V R) : Matrix V V R :=
  of fun i j ↦ if i ∈ S ∧ j ∈ S then K i j else 0

/-- The field a kernel assigns to an anchor `a`: its column at `a`, `K e_a`. -/
def fieldAt (K : Matrix V V R) (a : V) : V → R := fun j ↦ K j a

/-- `thresh t f`: everything the field scores at least `t`. -/
def thresh [LinearOrder R] (t : R) (f : V → R) : Finset V := univ.filter fun i ↦ t ≤ f i

/-- `topk k f`: every vertex that fewer than `k` vertices beat strictly, so ties are kept. -/
def topk [LinearOrder R] (k : ℕ) (f : V → R) : Finset V :=
  univ.filter fun i ↦ (univ.filter fun j ↦ f i < f j).card < k

end Nouns

/-! ## Hypothetical edges on weights -/

section Hyp

variable {V R : Type*} [Fintype V] [DecidableEq V]

/-- The weights with one assumed undirected edge of weight `δ` between `u` and `v`: added to a
present edge, or a new edge where there was none. A negative `δ` on a present edge weakens it. -/
def assumeEdge [Add R] [Zero R] (A : Matrix V V R) (u v : V) (δ : R) : Matrix V V R :=
  of fun i j ↦ A i j + if (i = u ∧ j = v) ∨ (i = v ∧ j = u) then δ else 0

/-- `e_u − σ e_v`: the difference of two vertices for `σ = 1`, their sum for `σ = −1`. -/
def dvec [Ring R] (u v : V) (σ : R) : V → R :=
  fun i ↦ (if i = u then 1 else 0) - σ * (if i = v then 1 else 0)

end Hyp

/-! ## Modes (`core/query.py`, `mode_of`) -/

/-- The four modes. -/
inductive Mode
  | semantic | structural | temporal | causal
  deriving DecidableEq, Repr

/-- `mode_of`: `C ∈ E` is causal; `D ∈ E` or a window that is not a point is temporal; `E = {F}`
is structural; the rest is semantic. -/
def modeOf (s : CQ.Scope) : Mode :=
  if CQ.Fiber.C ∈ s.edges then .causal
  else if CQ.Fiber.D ∈ s.edges ∨ s.time.window.kind ≠ .point then .temporal
  else if s.edges = {CQ.Fiber.F} then .structural
  else .semantic

/-! ## Sentences: clauses, connectives and the modality -/

/-- A clause, one verb with its nouns, abstracted to the scope the verb requires (`required`) and
the strata its evaluator reads. That `reads ⊆ req.sigma` is the typing invariant a build keeps. -/
structure Clause where
  /-- The scope the clause requires. -/
  req : CQ.Scope
  /-- The strata its evaluator reads. -/
  reads : Finset CQ.Stratum

/-- A sentence over clauses, with regions `Rg` for `within` and hypotheses `H` for `assume`. -/
inductive Sentence (Rg H : Type*)
  | clause (c : Clause)
  | and (s t : Sentence Rg H)
  | or (s t : Sentence Rg H)
  | seq (s t : Sentence Rg H)
  | within (r : Rg) (s : Sentence Rg H)
  | assume (h : H) (s : Sentence Rg H)

/-- The overlay stratum added to a required scope: what `assume` asks of a grant. -/
def withOverlay (r : CQ.Scope) : CQ.Scope := { r with sigma := insert .hypothetical r.sigma }

namespace Sentence

variable {Rg H : Type*}

/-- The scopes a sentence requires: one per clause, each with the overlay under `assume`. -/
def reqs : Sentence Rg H → List CQ.Scope
  | clause c => [c.req]
  | and s t | or s t | seq s t => s.reqs ++ t.reqs
  | within _ s => s.reqs
  | assume _ s => s.reqs.map withOverlay

/-- Admissible under a grant: every required scope lies under some granted plane. -/
def Admissible (g : List CQ.Scope) (s : Sentence Rg H) : Prop := ∀ r ∈ s.reqs, CQ.admits g r

/-- The assumptions in force. A result is `Inv` when there are none and `Hyp` of them otherwise. -/
def hyps : Sentence Rg H → List H
  | clause _ => []
  | and s t | or s t | seq s t => s.hyps ++ t.hyps
  | within _ s => s.hyps
  | assume h s => h :: s.hyps

/-- A result that depends on no assumption. -/
def IsInv (s : Sentence Rg H) : Prop := s.hyps = []

/-- The clauses, in order. -/
def clauses : Sentence Rg H → List Clause
  | clause c => [c]
  | and s t | or s t | seq s t => s.clauses ++ t.clauses
  | within _ s | assume _ s => s.clauses

/-- The strata an evaluation reads: each clause's, and the overlay once under the modality. -/
def reads : Bool → Sentence Rg H → Finset CQ.Stratum
  | ov, clause c => if ov then insert .hypothetical c.reads else c.reads
  | ov, and s t | ov, or s t | ov, seq s t => s.reads ov ∪ t.reads ov
  | ov, within _ s => s.reads ov
  | _, assume _ s => s.reads true

end Sentence

/-- A store: data per stratum. -/
abbrev Store (D : Type*) := CQ.Stratum → D

/-- An evaluation model: clause evaluators (told whether they run under the modality, when they
read the overlay too), the connectives, the adjectives and the perturbations. -/
structure Model (Rg H D R : Type*) where
  /-- A clause's evaluator. -/
  clause : Clause → Bool → Store D → R
  /-- `and`. -/
  and : R → R → R
  /-- `or`. -/
  or : R → R → R
  /-- `then`. -/
  seq : R → R → R
  /-- `within`. -/
  within : Rg → R → R
  /-- `assume`: the perturbation a hypothesis makes to the store. -/
  perturb : H → Store D → Store D

namespace Model

variable {Rg H D R : Type*}

/-- A perturbation writes the overlay alone, from what the overlay held. -/
def Overlay (M : Model Rg H D R) : Prop :=
  (∀ h (σ : Store D) s, s ≠ CQ.Stratum.hypothetical → M.perturb h σ s = σ s) ∧
    ∀ h (σ τ : Store D), σ .hypothetical = τ .hypothetical →
      M.perturb h σ .hypothetical = M.perturb h τ .hypothetical

/-- Each clause evaluator reads its declared strata, and the overlay when under the modality. -/
def Local (M : Model Rg H D R) : Prop :=
  ∀ c (ov : Bool) (σ τ : Store D), (∀ s ∈ c.reads, σ s = τ s) →
    (ov = true → σ .hypothetical = τ .hypothetical) → M.clause c ov σ = M.clause c ov τ

/-- Evaluation. `assume h s` evaluates `s` under the modality, on the perturbed store. -/
def eval (M : Model Rg H D R) : Bool → Sentence Rg H → Store D → R
  | ov, .clause c, σ => M.clause c ov σ
  | ov, .and s t, σ => M.and (M.eval ov s σ) (M.eval ov t σ)
  | ov, .or s t, σ => M.or (M.eval ov s σ) (M.eval ov t σ)
  | ov, .seq s t, σ => M.seq (M.eval ov s σ) (M.eval ov t σ)
  | ov, .within r s, σ => M.within r (M.eval ov s σ)
  | _, .assume h s, σ => M.eval true s (M.perturb h σ)

end Model

/-! ## Chains: the move alphabet and the admissible language -/

/-- The canonical move alphabet (fiber-geometry §2.0): similarity, citation, supersession, causal
witness. -/
inductive Move
  | S | F | D | C
  deriving DecidableEq, Repr

instance : Fintype Move :=
  Fintype.ofList [.S, .F, .D, .C] fun x ↦ by cases x <;> simp

/-- A typed graph: which moves run from which vertex to which. -/
structure TGraph (V : Type*) where
  /-- The edges, by move. -/
  edge : Move → V → V → Bool

/-- A deterministic automaton over the moves. -/
structure Auto (Q : Type*) where
  /-- The start state. -/
  start : Q
  /-- The transition. -/
  step : Q → Move → Q
  /-- The accepting states. -/
  accept : Q → Bool

namespace Auto

variable {Q : Type*}

/-- Run a word from a state. -/
def run (A : Auto Q) : Q → List Move → Q
  | q, [] => q
  | q, m :: w => A.run (A.step q m) w

/-- The language: words run from the start to an accepting state. -/
def Accepts (A : Auto Q) (w : List Move) : Prop := A.accept (A.run A.start w) = true

/-- A live state: some word is accepted from it. The viable-prefix test. -/
def Live (A : Auto Q) (q : Q) : Prop := ∃ w, A.accept (A.run q w) = true

instance (A : Auto Q) (w : List Move) : Decidable (A.Accepts w) :=
  inferInstanceAs (Decidable (_ = true))

end Auto

/-- The set `E` as the one-state automaton accepting `E*`: today's `E ⊆ {F, D, C}`. -/
def ofSet (E : Finset Move) : Auto Bool := ⟨true, fun q m ↦ q && decide (m ∈ E), id⟩

/-- The grounding production `S* · (C | D)` (fiber-geometry §2.3-4): state `0` reads resemblance,
`1` is grounded, `2` is dead. -/
def grounding : Auto (Fin 3) :=
  ⟨0, fun q m ↦
    match q.val, m with
    | 0, .S => 0
    | 0, .C => 1
    | 0, .D => 1
    | _, _ => 2,
    fun q ↦ decide (q = 1)⟩

variable {V Q : Type*} [DecidableEq V] [DecidableEq Q]

/-- A chain from `u`: the moves taken and the vertices reached, each step an edge of its move. -/
def chainOk (G : TGraph V) : V → List (Move × V) → Bool
  | _, [] => true
  | u, (m, v) :: rest => G.edge m u v && chainOk G v rest

/-- The fiber signature of a chain: its word. -/
def signature (c : List (Move × V)) : List Move := c.map Prod.fst

/-- Admissible under a language: a chain whose signature the automaton accepts. -/
def Admissible (G : TGraph V) (A : Auto Q) (u : V) (c : List (Move × V)) : Prop :=
  chainOk G u c = true ∧ A.Accepts (signature c)

instance (G : TGraph V) (A : Auto Q) (u : V) (c : List (Move × V)) :
    Decidable (Admissible G A u c) :=
  inferInstanceAs (Decidable (_ ∧ _))

/-- The product walk: the chain and the automaton step together, from a pair to a pair. -/
def prodOk (G : TGraph V) (A : Auto Q) : V × Q → List (Move × V) → V × Q → Bool
  | p, [], p' => decide (p = p')
  | (u, q), (m, v) :: rest, p' => G.edge m u v && prodOk G A (v, A.step q m) rest p'

/-- One graph has every edge of another. -/
def TGraph.Le (G G' : TGraph V) : Prop := ∀ m u v, G.edge m u v = true → G'.edge m u v = true

/-- Assume a move: the graph with one more edge. -/
def TGraph.assume (G : TGraph V) (m : Move) (a b : V) : TGraph V :=
  ⟨fun m' u v ↦ G.edge m' u v || decide (m' = m ∧ u = a ∧ v = b)⟩

end Palace.Query
