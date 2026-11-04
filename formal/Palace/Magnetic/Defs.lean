module

public import Palace.Laplacian.Defs
public import Mathlib.Analysis.SpecialFunctions.Complex.Log
public import Mathlib.Combinatorics.SimpleGraph.Connectivity.Connected

/-!
# The magnetic Laplacian: the definitions

The operator of `docs/design-notes/magnetic-laplacian.md` §2.1 and what its results are stated
over: a U(1) connection given by real phases `θ`, its parallel transport `e^{iθ(u,v)}`, the
magnetic adjacency and Laplacian, holonomy and circulation along walks, the gauge transform,
and the twisted coboundaries of §2.2. No code builds the operator (the note defers its build);
its `θ = 0` fiber is `laplacian.py`'s `laplacian` and its fiber with phase `π` on the negative
entries is `signed_laplacian`, which is BRG-7.

Conventions. `H^θ_{uv} = w_{uv} e^{iθ(u,v)}` and `L^θ = D − H^θ`, as in the note's §2.1, so
`x* L^θ x` sums `w_{uv} |x_u − e^{iθ(u,v)} x_v|²`. The note's §2.2 coboundary, `x_v − e^{iθ(u,v)}
x_u`, transports the other way: its energy is `L^{−θ}`, the conjugate operator, with the same
spectrum (`Palace/Magnetic.lean`, `two_mul_dotProduct_magLap_neg_eq`).
-/

@[expose] public section

open Matrix Complex

namespace Palace.Magnetic

variable {V : Type*}

/-- Parallel transport along the ordered pair `(u, v)` of the connection with phases `θ`,
`e^{iθ(u,v)}`. -/
noncomputable def transport (θ : V → V → ℝ) (u v : V) : ℂ := exp (θ u v * I)

/-- A U(1) connection: transport back along a pair undoes transport along it,
`e^{iθ(v,u)} = conj e^{iθ(u,v)}`, so the phases are antisymmetric modulo `2π`. -/
def IsConnection (θ : V → V → ℝ) : Prop := ∀ u v, transport θ v u = star (transport θ u v)

/-- The connection shifted by the coboundary of `ψ`, `θ + d₀ψ` with `(d₀ψ)(u,v) = ψ_v − ψ_u`:
what the gauge transform `x_u ↦ e^{iψ_u} x_u` does to the phases. -/
def gauge (θ : V → V → ℝ) (ψ : V → ℝ) (u v : V) : ℝ := θ u v + (ψ v - ψ u)

/-- The direction of the ordered pair `(u, v)` in a digraph `a`, `a(u,v) − a(v,u)`: `1` with the
arrow, `−1` against it, `0` for a reciprocal pair or no edge. -/
def arrow (a : V → V → Prop) [DecidableRel a] (u v : V) : ℤ :=
  (if a u v then 1 else 0) - (if a v u then 1 else 0)

/-- The charge-`q` phase of a digraph, `θ^{(q)}(u,v) = 2πq·(a(u,v) − a(v,u))` (§2.1). -/
noncomputable def chargePhase (a : V → V → Prop) [DecidableRel a] (q : ℝ) (u v : V) : ℝ :=
  2 * Real.pi * q * arrow a u v

/-- The phase that reads a signed matrix as a connection: `π` on a negative entry, else `0`. -/
noncomputable def signPhase (A : Matrix V V ℝ) (u v : V) : ℝ :=
  if A u v < 0 then Real.pi else 0

/-- The twisted coboundary of §2.2, `(d₀^θ x)(u,v) = x_v − e^{iθ(u,v)} x_u`. -/
noncomputable def d0 (θ : V → V → ℝ) (x : V → ℂ) (u v : V) : ℂ := x v - transport θ u v * x u

/-- The twisted coboundary on edge values of §2.2, each value carried to the triangle's top vertex
`k`: `(d₁^θ y)(ijk) = y(j,k) − y(i,k) + e^{iθ(j,k)} y(i,j)`. -/
noncomputable def d1 (θ : V → V → ℝ) (y : V → V → ℂ) (i j k : V) : ℂ :=
  y j k - y i k + transport θ j k * y i j

/-- Loop-trivial: on every self-loop of nonzero weight the transport is `1`. A loop with transport
`−1`, a negative self-loop, is frustrated by itself, and no walk of a simple graph sees it. -/
def LoopTrivial (w : V → V → ℝ) (θ : V → V → ℝ) : Prop := ∀ u, w u u ≠ 0 → transport θ u u = 1

/-- The holonomy of the triangle `(i, j, k)`, `e^{iF(ijk)}` with `F(ijk) = θ(i,j) + θ(j,k) +
θ(k,i)` the flux through it. -/
noncomputable def triHolonomy (θ : V → V → ℝ) (i j k : V) : ℂ :=
  transport θ i j * transport θ j k * transport θ k i

section Walks

variable {G : SimpleGraph V}

/-- The holonomy of `θ` along a walk: the product of the transports of its steps. -/
noncomputable def holonomy (θ : V → V → ℝ) {u v : V} (p : G.Walk u v) : ℂ :=
  (p.darts.map fun d ↦ transport θ d.fst d.snd).prod

/-- The circulation of a walk in the digraph `a`: its steps with the arrow less its steps
against it (§2.1, "the elementary invariant"). -/
def circulation (a : V → V → Prop) [DecidableRel a] {u v : V} (p : G.Walk u v) : ℤ :=
  (p.darts.map fun d ↦ arrow a d.fst d.snd).sum

variable (G)

/-- Flux-trivial on `G`: every closed walk has holonomy `1`, the flux of every cycle `≡ 0` modulo
`2π`. -/
def FluxTrivial (θ : V → V → ℝ) : Prop := ∀ u (p : G.Walk u u), holonomy θ p = 1

/-- Gauge-trivial on `G`: on every edge, `θ` is a coboundary modulo `2π`. -/
def GaugeTrivial (θ : V → V → ℝ) : Prop :=
  ∃ ψ : V → ℝ, ∀ ⦃u v⦄, G.Adj u v → transport θ u v = exp ((ψ v - ψ u : ℝ) * I)

end Walks

variable [Fintype V] [DecidableEq V]

/-- The magnetic adjacency, `H^θ_{uv} = w_{uv} e^{iθ(u,v)}` (§2.1). -/
noncomputable def magAdj (w : Matrix V V ℝ) (θ : V → V → ℝ) : Matrix V V ℂ :=
  of fun u v ↦ (w u v : ℂ) * transport θ u v

/-- The magnetic Laplacian `L^θ = D − H^θ`, `D` the weighted degree of `w` (§2.1). -/
noncomputable def magLap (w : Matrix V V ℝ) (θ : V → V → ℝ) : Matrix V V ℂ :=
  diagonal (fun u ↦ ((degree w u : ℝ) : ℂ)) - magAdj w θ

/-- The gauge transform `x_u ↦ e^{iψ_u} x_u`, a diagonal unitary. -/
noncomputable def gaugeMatrix (ψ : V → ℝ) : Matrix V V ℂ := diagonal fun u ↦ exp (ψ u * I)

end Palace.Magnetic
