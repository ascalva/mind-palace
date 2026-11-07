module

public import Mathlib.Data.Fintype.Perm
public import Palace.Dynamics.Defs

/-!
# Scale and attribution: the definitions

The objects of `docs/design-notes/dn-scale-and-attribution.md` and what `Palace/Scale.lean` is
stated over: the time average of a field under an operator over a window of steps (the estimate
of a macro observable from consecutive readings), and attribution over a finite set of sources: a
game (the evaluation score of each configuration of sources), an ordering of the sources, the
marginal contribution of a source to the sources before it, the Shapley value as the average over
every ordering, the four axioms an attribution may satisfy, the unanimity games and the Harsanyi
dividends that decompose every game, and the leave-one-out attribution the ledger's ablation arms
read. No code computes any of them yet.
-/

@[expose] public section

open Matrix Finset

namespace Palace.Scale

/-! ### SCL-1 The time average over a window -/

section Window

variable {V K : Type*} [Fintype V] [DecidableEq V] [Field K]

/-- The time average of a field under an operator over a window of `T` steps,
`(1/T) Σ_{n<T} N^n x`: the estimate of a macro observable from `T` consecutive readings of the
diffusion started at `x`. -/
def timeAverage (N : Matrix V V K) (T : ℕ) (x : V → K) : V → K :=
  (1 / (T : K)) • ∑ n ∈ range T, N ^ n *ᵥ x

end Window

/-! ### SCL-3 Attribution over a finite set of sources -/

section Attribution

variable {α K : Type*} [Fintype α] [DecidableEq α]

/-- An ordering of the sources: a bijection with `Fin n`, the position of each source. -/
abbrev Ordering (α : Type*) [Fintype α] := α ≃ Fin (Fintype.card α)

/-- The sources ordered before `i` by `σ`. -/
def pred (σ : Ordering α) (i : α) : Finset α := univ.filter fun j ↦ σ j < σ i

/-- The marginal contribution of the source `i` to the configuration `S`: the change in the
score when `i` is added. -/
def marginal [Sub K] (v : Finset α → K) (S : Finset α) (i : α) : K := v (insert i S) - v S

/-- The Shapley value of the source `i` under the score `v`: the average, over every ordering of
the sources, of the marginal contribution of `i` to the sources ordered before it. -/
def shapley [Field K] (v : Finset α → K) (i : α) : K :=
  (∑ σ : Ordering α, marginal v (pred σ i) i) / (Fintype.card α).factorial

/-- An attribution: a value per source for every score. -/
abbrev Attribution (α K : Type*) := (Finset α → K) → α → K

/-- Efficiency: the values sum to what the full set of sources adds over none of them. -/
def Efficient [AddCommMonoid K] [Sub K] (ψ : Attribution α K) : Prop :=
  ∀ v, ∑ i, ψ v i = v univ - v ∅

/-- Null player: a source that changes no score is attributed nothing. -/
def NullPlayer [Zero K] (ψ : Attribution α K) : Prop :=
  ∀ v i, (∀ S, v (insert i S) = v S) → ψ v i = 0

/-- Symmetry: two sources that add the same to every configuration holding neither are
attributed the same. -/
def Symmetric (ψ : Attribution α K) : Prop :=
  ∀ v i j, (∀ S, i ∉ S → j ∉ S → v (insert i S) = v (insert j S)) → ψ v i = ψ v j

/-- Additivity: the attribution of a sum of scores is the sum of the attributions. -/
def Additive [Add K] (ψ : Attribution α K) : Prop :=
  ∀ v w, ψ (v + w) = ψ v + ψ w

/-- The unanimity game of `T`: a score of `1` to every configuration holding all of `T`. -/
def unanimity [Zero K] [One K] (T : Finset α) : Finset α → K := fun S ↦ if T ⊆ S then 1 else 0

/-- The Harsanyi dividend of `v` at `T`, `Σ_{S ⊆ T} (−1)^{|T| − |S|} v S`: the coefficient of
the unanimity game of `T` in the decomposition of `v`. -/
def harsanyi [Ring K] (v : Finset α → K) (T : Finset α) : K :=
  ∑ S ∈ T.powerset, (-1) ^ (T.card - S.card) * v S

/-- Leave-one-out: the drop in the score when `i` alone is removed from the full set, the
attribution an ablation arm reads. -/
def loo [Sub K] (v : Finset α → K) (i : α) : K := v univ - v (univ.erase i)

end Attribution

end Palace.Scale
