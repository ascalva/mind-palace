module

public import Palace.Heat.Defs
public import Palace.Hodge.Defs
public import Palace.Retrieval.Defs
public import Palace.Spectral.Defs
public import Palace.Transport.Defs

/-!
# The dynamics of an evolving graph: the definitions

The objects of `docs/design-notes/dn-graph-dynamics.md` and what `Palace/Dynamics.lean` is stated
over: a value's velocity over a window of cuts (a 0-cochain per pair of cuts), an edge flow's
weighted divergence, its least-squares potential and residual (HodgeRank), the Neumann partial sums
and the ripple of a shock (the resolvent on a relation), the modes of a symmetric operator and the
projection onto some of them, and the quotient of a graph by a partition. No code computes any of
them yet; `diffuse` computes the resolvent of the killed walk, and the Hodge projectors exist in
`core/kernel/complex/hodge.py` at unit weights.
-/

@[expose] public section

open Matrix Finset

namespace Palace.Dynamics

/-! ### A value's versions and its velocity -/

/-- The velocity of a field over a window of cuts, `x c₁ − x c₀`: the displacement of every
identity's value (a number, an embedding) from the version alive at `c₀` to the one alive at
`c₁`, a 0-cochain per pair of cuts. The identity is the box; `x c v` is what the box points at
in the cut `c`. -/
def velocity {V E : Type*} [AddCommGroup E] (x : ℕ → V → E) (c₀ c₁ : ℕ) : V → E :=
  fun v ↦ x c₁ v - x c₀ v

/-! ### Edge flows and their potentials -/

section Flow

variable {V E : Type*} [Fintype V] [Fintype E] [DecidableEq V] [DecidableEq E]

/-- The weighted inner product on edges, `⟨a, b⟩_w = Σ_e w_e a_e b_e`. -/
def wdotE (w a b : E → ℝ) : ℝ := ∑ e, w e * (a e * b e)

/-- The weighted divergence of a flow, `div_w Y = ∂₁ (w ∘ Y)`: the net weighted outflow at each
vertex. -/
def divergence (B₁ : Matrix V E ℝ) (w Y : E → ℝ) : V → ℝ := B₁ *ᵥ (w * Y)

/-- The weighted graph Laplacian `L_w = ∂₁ W ∂₁ᵀ`, the down term of the Hodge Laplacian with the
edge weights `w` as the inner product on edges. -/
def weightedLap (B₁ : Matrix V E ℝ) (w : E → ℝ) : Matrix V V ℝ := B₁ * diagonal w * B₁ᵀ

omit [Fintype V] [DecidableEq V] in
/-- `L_w` is symmetric. -/
theorem isHermitian_weightedLap (B₁ : Matrix V E ℝ) (w : E → ℝ) :
    (weightedLap B₁ w).IsHermitian := by
  rw [IsHermitian, conjTranspose_eq_transpose_of_trivial]
  simp [weightedLap, transpose_mul, diagonal_transpose, Matrix.mul_assoc]

/-- HodgeRank's potential, `s = L_w⁺ div_w Y`: the least-squares potential of the flow `Y`. -/
noncomputable def potential (B₁ : Matrix V E ℝ) (w Y : E → ℝ) : V → ℝ :=
  pinv (weightedLap B₁ w) (isHermitian_weightedLap B₁ w) *ᵥ divergence B₁ w Y

/-- The residual `Y − ∂₁ᵀ s`: the flow less the gradient of its potential, the part no potential
explains (the curl and harmonic parts together). -/
noncomputable def residual (B₁ : Matrix V E ℝ) (w Y : E → ℝ) : E → ℝ :=
  Y - B₁ᵀ *ᵥ potential B₁ w Y

end Flow

/-! ### The resolvent and the ripple -/

section Resolvent

variable {V : Type*} [Fintype V] [DecidableEq V]

/-- The Neumann partial sum `Σ_{k<n} M^k`: the walks of fewer than `n` steps. -/
def neumann {R : Type*} [Semiring R] (M : Matrix V V R) (n : ℕ) : Matrix V V R :=
  ∑ k ∈ range n, M ^ k

/-- The ripple of a shock `δ` along the relation `A` with damping `z`: the resolvent applied to
the shock, `(1 − zA)⁻¹ δ`, the shock after every number of steps, each step damped by `z`. -/
noncomputable def ripple (A : Matrix V V ℝ) (z : ℝ) (δ : V → ℝ) : V → ℝ := (1 - z • A)⁻¹ *ᵥ δ

end Resolvent

/-! ### The modes of a symmetric operator -/

section Modes

variable {V : Type*} [Fintype V] [DecidableEq V] {M : Matrix V V ℝ}

/-- The eigenvector `φ_j` of a real symmetric matrix, as a vector. -/
noncomputable def mode (hM : M.IsHermitian) (j : V) : V → ℝ := WithLp.ofLp (hM.eigenvectorBasis j)

/-- The projection of `f` onto the modes in `S`, `Σ_{j ∈ S} ⟨φ_j, f⟩ φ_j`: the macro variables
when `S` holds the low modes. -/
noncomputable def modeProj (hM : M.IsHermitian) (S : Finset V) (f : V → ℝ) : V → ℝ :=
  ∑ j ∈ S, (f ⬝ᵥ mode hM j) • mode hM j

end Modes

/-! ### Coarse-graining by a partition -/

section Coarse

variable {V B : Type*} [Fintype V] [Fintype B] [DecidableEq B]

/-- The indicator of a partition `π : V → B`: `P v b = 1` when `v` lies in the block `b`. -/
def indicator {R : Type*} [Zero R] [One R] (π : V → B) : Matrix V B R :=
  of fun v b ↦ if π v = b then 1 else 0

/-- The quotient of a weight matrix by a partition, `A_π = Pᵀ A P`: the weight between two blocks
is the total weight between their members. -/
def quot {R : Type*} [NonAssocSemiring R] (π : V → B) (A : Matrix V V R) : Matrix B B R :=
  (indicator π)ᵀ * A * indicator π

end Coarse

end Palace.Dynamics
