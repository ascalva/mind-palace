# formal

Rung L1 of the Lean ladder (`docs/design-notes/dn-mathematical-foundations.md` §2.4): statements of
the ledger's laws as Lean specs over exact arithmetic, each attacked by Plausible before anyone
proves it. A sibling lake package with zero import coupling with `core/` in either direction: Lean
states and proves laws over ℚ and ℝ, Hypothesis tests the floats in Python, and the law id joins
the two. Rung L3 enters one claim at a time: float64 claims proved over a model of binary64
rounding that is itself attacked against this machine's arithmetic.

## Layout

- `Palace/Laplacian.lean`: LAP-1, LAP-2 and LAP-3 (`core/kernel/complex/laplacian.py`), with their
  attacks and controls at the end.
- `Palace/Memberships.lean`: the membership relation (`core/stores/memberships.py`) as a finite
  partial function on coordinate space, and MEM-1 to MEM-5.
- `Palace/Spectral.lean`: `L_sym` and LAP-4 (`laplacian_sym`), and the pseudo-inverse `L⁺` that
  `core/graph/conductance.py` takes for effective resistance (CND-1).
- `Palace/Balance.lean`: signed balance, LAP-5 and LAP-6 (`core/kernel/complex/balance.py`).
- `Palace/Cut.lean`: conductance, CUT-1 (`core/complex/cut.py`).
- `Palace/Curvature.lean`: Forman curvature, CRV-1 and CRV-2, and CRV-3, the emission rule of
  `most_negative_edges` that the Dreamer's bridge lens reads (`core/kernel/complex/curvature.py`).
- `Palace/Clock.lean`: the clock laws of the global event clock (`global-event-clock.md` §2.3,
  §2.4): C1 and C2, cuts and their certificates, and proper time (GC-N6).
- `Palace/Heat.lean`: the heat kernel `e^{−tL}` and the diffusion distance, CND-4
  (`core/graph/conductance.py`).
- `Palace/Rayleigh.lean`: Rayleigh's monotonicity law, CND-2, and the leave-one-out attribution of
  the reconnection rider (`core/graph/conductance.py`, `reconnection_scan`).
- `Palace/Binary64.lean`: rung L3's substrate, a model of IEEE 754 binary64 rounding to nearest,
  ties to even (`rn`), its laws, and attacks that check it bit for bit against this machine's
  float64.
- `Palace/FloatModel.lean`: the bridge from Lean core's logical model of `Float` to `rn`: Lean's
  `Float` `+`, `*`, `/` and `Nat.toFloat` round as `rn` does, so the two entries hold of Lean's own
  `Float`; its attacks check the compiled C operators against that logical model.
- `Palace/Roundoff.lean`: two L3 entries over the model: CND-6's exact comparisons of `chi_s` with
  `1.0`, and LAP-1's route agreement between two association orders of a degree sum.
- `Palace/Plane.lean`: the shared prose plane (`core/stores/plane.py`, A3): no-leak, noninterference
  (A3.5), the search loop, the `held` cache and purge (A3.7).
- `Palace/Attack.lean`: `survives` and `refuted`, which run Plausible with a fixed seed and count
  the instances that passed their guards.
- `Audit.lean`: lists the axioms behind every `Palace` declaration and fails on anything beyond
  `propext`, `Classical.choice`, `Quot.sound` and `sorryAx`.
- `sorry-budget`: the ratchet. The count of `sorry` must equal it; it only goes down.
- `check.sh`: the local gate. It builds (which runs the attacks), checks the budget, greps for
  `axiom`, `admit` and `native_decide`, and runs the audit.

## Laws

| law | statement | status |
|---|---|---|
| LAP-1 | `L·1 = 0` for every `A` | proved; attack survived 500 instances |
| LAP-2 | `xᵀLx ≥ 0` and `L` PSD, for symmetric `A ≥ 0` | proved; attack survived 500 |
| LAP-2 | `xᵀL̄x ≥ 0` for symmetric `A` of any sign | proved; attack survived 500 |
| LAP-3 | `dim ker L` = components of the support, for symmetric `A ≥ 0` | proved; attacks survived 221 and 252 non-constant kernel cases |
| MEM-1 | the atom projection is a multiset (multiplicity = row count); `n_doc ≤ n_occ` | proved; attack survived 500 |
| MEM-2 | the version fibers are disjoint, non-empty, and their sizes sum to `\|M\|` | proved; attack survived 500 |
| MEM-3 | runs are the adjacent-collapse encoding: one edge per change of occupant, `\|edges\| = \|runs\| − 1`, edge ends differ, a revert stays visible | proved; attacks survived 500 each, one of them against a transcription of `slot_runs`' loop |
| MEM-4 | landing reconciles currency every time, so it agrees with each path's newest landing, reverts included | proved; attack survived 500 landing histories |
| MEM-5 | coherent currency selects one fiber per path; `current_any(v) ⇔ n_doc(v) > 0` | proved; attack survived 500 |
| `L_sym` PSD | for symmetric `A ≥ 0` | proved; attacked through the identities under LAP-4 |
| LAP-4 | eigenvalues of `L_sym` lie in `[0, 2]`; an isolated vertex has an identity row (eigenvalue 1); `L_sym` annihilates `D^{1/2}·1` | proved; its two identities survived 500 each |
| `L⁺` | the Moore–Penrose inverse (all four Penrose equations), symmetric, PSD for symmetric `A ≥ 0` | proved; shadow attack survived 500 |
| CND-1 | `R_eff = L⁺ᵢᵢ + L⁺ⱼⱼ − 2L⁺ᵢⱼ ≥ 0` | proved; inside the shadow attack |
| LAP-5 | on a connected support, `L̄` has a zero-energy vector (`λ_min = 0`) iff the signed graph is balanced; without connectivity it fails, which is why `signed_spectrum` takes the max over components | proved, with a witness for the failure; attacks survived 468 and 470 connected cases |
| LAP-6 | a triangle is frustrated iff the product of its signs is negative, iff it has an odd number of negative edges | proved; attack survived 495 |
| CUT-1 | `Φ(S) ∈ [0, 1]` for symmetric `A ≥ 0`, and `Φ(S) = 0` iff no weight crosses, under the code's conventions for a degenerate `S` | proved; attacks survived 500 each |
| CRV-1 | `Ric_F(u, v) = 4 − deg u − deg v + 3·\|N(u) ∩ N(v)\|` on the support | the definition; agrees with the code's `B @ B` computation on 500 graphs |
| CRV-2 | two cliques and a bridge: `Ric_F(bridge) = 4 − 2n` for cliques of `n` vertices, the strict unique minimum, negative exactly from `n = 3` | proved for every `n`; checked on every edge for `n` from 1 to 8 |
| CRV-3 | `most_negative_edges` emits the edges with `κ ≤ 0`, or, when every edge is positive, only those at the minimum, never the whole graph; in strictly increasing `(κ, i, j)` order; the `top_k` smallest candidates, `min(top_k, \|candidates\|)` of them, each `top_k` a prefix of the next | proved; attack survived 500 random graphs against a transcription of the code |
| CRV-2, CRV-3 | on two cliques and a bridge the bridge lens emits exactly the bridge, for every clique size and every `top_k ≥ 1`: by the `κ ≤ 0` rule from two vertices per clique, by the minimum rule for one | proved |
| C1, C2 | a clock monotone along `≼` (C1) into a partial order has convex fibers (C2), so C2 adds nothing to C1; C1 needs checking only on the generator edges | proved, with witnesses that C2 needs antisymmetric ticks and does not give C1; attack survived 472 |
| cuts | a set is a cut (a down-set of `≼`) iff no generator edge reads into it from outside; cuts are closed under ∩ and ∪; a frontier cut needs only its cross-store edges checked; certificates compose by the pointwise minimum and maximum of their frontiers | proved; attacks survived 500 each |
| GC-N6 | proper time, the longest chain, is 0 at a point, at least 1 across a strict step, finite on a finite `N`, satisfies `τ(a, b) + τ(b, c) ≤ τ(a, c)` for `a ≤ b ≤ c`, and is bounded by the tick difference of any strictly monotone clock | proved; the reverse triangle survived 500 random DAGs on the longest-path recursion |
| CND-4 | `H_t = e^{−tL}` is symmetric, `H_0 = 1`, `H_{s+t} = H_s H_t`; the code's `d_t = √(G_ii + G_jj − 2G_ij)` with `G = H_{2t}` is the Euclidean distance between `H_t eᵢ` and `H_t eⱼ`, so a metric that separates every two vertices for every `t`, across components too; for symmetric `A ≥ 0`, `d_t` is non-increasing in `t` | proved; its two exact steps survived 500 each |
| CND-2 | Rayleigh's law: adding weight never raises effective resistance (`∞` across components) nor lowers effective conductance (`0` across), so a rise needs a weight-increased edge; through Thomson's principle, `2vᵀx − xᵀMx ≤ vᵀM⁺v` for `v` fixed by `M M⁺`, which by the Penrose equations alone is every `v` orthogonal to `ker M` | proved; attack survived 500 |
| leave-one-out | reverting an increased edge never raises conductance; with a single increased edge every rise confirms it; a rise carried by two redundant new paths confirms neither | proved, with a witness; attack survived 500 |
| bridge | Lean's `Float` `+`, `*` and `/` (nonzero divisor) return `rn` of the exact result, for finite operands and results below `2^1024`, and `k.toFloat` is exact below `2^53`: core's logical model of `Float` rounds as `rn` does | proved; the compiled C operators matched the logical model bit for bit on 500 sums, 500 products and 500 quotients |
| CND-6 (Lean `Float`) | `k.toFloat / n.toFloat` is exactly `1` iff `k = n`, for `k ≤ n < 2^53` | proved over Lean's `Float` |
| LAP-1 (Lean `Float`) | two association orders, summed in Lean's `Float`, of the same at most four nonzero nonnegative finite summands (exact sum at most `2^1000`) agree within `4·eps` of either result | proved over Lean's `Float` |
| A3 no-leak | every search hit under `C` is a table atom with a cleared occupancy and carries only rows of classes in `C` that hold it, under any cache: `PlaneHit`'s checks never fire on the plane's own reads | proved; attack survived 484 traces in which any write may crash partway |
| search | `PlaneReader.search`'s widening loop returns the first `k` atoms of the exact ranking that a cleared relation holds; `\|ps\|` rounds suffice | proved; attack survived 500 |
| cache | land, retire, purge and repair keep `held`/`held_ever` coherent: `wanted ∪ freed` covers every row a land touches | proved; attack survived 500 traces |
| A3.5 | noninterference: after any trace of writes that keep each path at one stratum, a reader under `C` sees, in its view and in every search, what it would see after the cleared writes, purges and repairs alone | proved by unwinding, under the hypotheses below; attack survived 480 traces with an uncleared write and a cleared hit |
| `rn` | binary64 rounding to nearest, ties to even, without overflow: it fixes binary64 numbers, is monotone and odd, lands on binary64, and moves `x` by at most half an ulp; on the grid of multiples of `2⁻¹⁰⁷⁴` (every sum of two binary64 numbers), by at most `u\|x\|`, `u = 2⁻⁵³`, subnormals included | the model; on this machine it matched 500 sums, 500 quotients and 500 quotients `k / n` bit for bit |
| CND-6 (float64) | `chi_s = rn(chain / n_s)` is `1.0` exactly when the chain spans the stratum, for every `n_s < 2^54`, and not at `2^54`; `chi_s ≤ 1` for every `n_s`, and `chi_s > 0` up to `2^1074` | proved over `rn`, with the witness; on this machine it survived 500 |
| LAP-1 (float64) | two association orders of the same at most four nonzero nonnegative binary64 summands agree within `4·eps` of either result, so the boundary test's route-agreement bound holds on every row of its fixtures; at eight summands two orders differ by five ulps, beyond the bound | proved over `rn`, with the witness; on this machine it survived 340 rows that reassociate |
| A3.7 | after `purge(d)` no row or edge names `d`; every atom `d`'s rows held is deleted or still held; no atom another row holds is freed; re-running finishes a purge interrupted after its atom delete | proved; attack survived 500 |

The binarized forms (0/1 adjacency) reduce to Mathlib's `SimpleGraph.posSemidef_lapMatrix` and
`card_connectedComponent_eq_finrank_ker_toLin'_lapMatrix` in one line each.

Each attack has a control, a nearby false law that must be refuted. Plausible refutes the LAP-1
and LAP-2 controls within 10 to 52 instances. It did not refute LAP-3 without `A ≥ 0` or without
symmetry in 215 to 396 tested instances, because a counterexample needs weights that cancel at
every vertex. Both hypotheses are shown to be needed by proved witnesses instead
(`lap_kernel_needs_nonneg`, `lap_kernel_needs_symm`).

The membership controls are the store's known wrong readings, each refuted within 12 to 35
instances: one row per document (the set reading), fibers keyed by blob alone (a rename shares a
blob across two paths), the lifetime count in place of the current one, distinct collapse in place
of adjacent collapse (`[2, 0, 2]`), and the C1 lander that skips reconciliation when a fiber
exists, refuted on the history `[(0, 0), (0, 1), (0, 0)]`: a revert on one path.

`L_sym` and `L⁺` have no executable form here (square roots; a spectral decomposition over ℝ), so
their laws are attacked where they are exact. `L_sym`'s rest on two identities over any
commutative ring, attacked over ℚ with arbitrary weights and scalings. `L⁺`'s are attacked on the
shadow `(L + P)⁻¹ − P` over ℚ, with `P` the projector onto the component indicators; the attack
checks all four Penrose equations on it, so a passing shadow is the Moore–Penrose inverse itself.
Its control, the connected-graph formula `(L + J/n)⁻¹ − J/n` applied to every graph, fails on the
first disconnected one.

The third batch's controls: LAP-5's global reading, without connectivity, is refuted on a negative
self-loop beside isolated vertices (singular, not balanced); LAP-6 as "a balanced triangle has no
negative edge" fails on two negative edges; CUT-1 on asymmetric weights exceeds 1; CRV-1 on
asymmetric weights no longer matches the code; and CRV-2 with the test's threshold, negative from
`n = 4`, fails at `n = 3`, where the bridge is already `−2`. A mutation of CRV-1's triangle
coefficient from 3 to 2 leaves every CRV-2 proof intact (no triangle runs through the bridge) and
is caught only by the attack against the code.

The plane's noninterference (A3.5) holds under four hypotheses the plane's header does not
state. Each is stated in `Palace/Plane.lean`, and the two the model can break have proved
witnesses:

- Search is exact, with ties broken by atom id. LanceDB breaks exact distance ties by physical row
  order, and `set_held` rewrites a row to the end. So an uncleared write that changes a tied
  cleared atom's held set can swap two tied atoms across the cut (measured on lancedb 0.33.0).
  On 2026-11-01 no two live prose atoms shared a vector (72 in `vectors.lance`, 147,417 in
  `research_curated.lance`), so a tie needs a float coincidence today.
- The table is content-addressed: an atom's text and vector are a function of its id. The first
  writer's vector is the one stored, so this asks for a deterministic embedder.
- The cache is complete on `C`. A crash between a land's commit and `_refresh_held` leaves the
  atom's cache empty and a cleared search misses it (fail-closed). `_refresh_held` rewrites a
  touched atom's whole held set, so an uncleared land that shares the atom brings the hit back
  (`drift_interferes`). `repair()` restores completeness.
- Every path lives at one stratum fixed in advance (A3.6). A land whose path another class holds
  is refused, and that check reads the uncleared relations: an uncleared document at a path makes
  a cleared land of the same path fail (`stratum_interferes`).

The plane's controls: lands and retires at arbitrary classes (the stratum channel) are refuted
within 26 instances, a reader whose join reads every class (the property test's seeded leak)
within 11, cleared lands that crash before their cache step within 36, a reader that trusts the
cache in place of the cleared join within 106, `freed` without the old derivation's atoms within
17, the search loop without its `seen` set within 25 (`[0, 0]`), and a purge without its
still-held check within 10.

Outside the model: `relabel` and `reset` (each moves or forgets whole classes, a visible act for
any clearance it names), a land of several fibers in one transaction, and `known()`, which tells
the write path whether the shared table holds an atom of any class, the deduplication side channel
of Harnik, Pinkas and Shulman-Peleg (2010). Only ingest calls it (`core/ingest/index.py`).

The dreamer laws. C2, convex fibers, is not a law of its own: any clock monotone along `≼` into
partially ordered ticks has them, so a property test of C2 can fail only where one of C1 fails,
unless the ticks are compared by a preorder that is not antisymmetric. Proper time and the heat
kernel have no executable form (a supremum over chains; the exponential of a matrix): proper
time's reverse triangle is attacked on the longest-path recursion a materialized `N` would run,
and CND-4 on its two exact steps, the Gram identity for the square of a symmetric matrix and the
triangle inequality of the Gram distance of a positive semidefinite one. The controls: CRV-3
without its minimum rule is refuted within 6 instances (a lone positive edge emits nothing) and
with ties broken by `(κ, j, i)` within 50; the cut falsifier searching edges out of the set within
16; C1 into ticks compared by a preorder that is not antisymmetric within 74; the ordinary triangle
inequality for proper time within 103 (a detour longer than the path through `b`); the Gram
identity for a non-symmetric matrix within 10, and the Gram triangle for an indefinite one within
10.

Rayleigh's law (CND-2) has the same exact shadow as `L⁺`. Its reversal, that adding weight never
raises conductance, is refuted within 5 instances. Leave-one-out completeness, that every rise
confirms some increased edge, is refuted within 29, on a cycle of new edges, and fails in general
(`Witness.loo_confirms_nothing`): when the new edges are redundant, `reconnection_scan` reports a
genuine reconnection with no bridging edge. Its docstring's "never a guess" holds, but an empty
attribution does not mean the rise is spurious.

Rung L3 (§2.4) enters per claim. Its substrate, `Palace/Binary64.lean`, is written here in
Flocq's terms: FloatSpec, the Flocq port issue #48 names, pins Lean v4.34.0-rc2, an older Mathlib
and cslib (checked 2026-11-01), and Mathlib's own `FP` module is deprecated without replacement.
The model's fit to real arithmetic is attacked, not assumed. Lean's `Float` is the host's binary64,
so each attack decodes the hardware's result bit for bit and compares it with `rn` of the exact
result. Of the 500 sums seed 131 draws, 313 are exact, 120 are ties, 67 round elsewhere, 25 land in
the subnormal range and 42 round up into the next binade. Its controls, ties away from zero, a
52-bit significand and flush to zero, are each refuted by the second instance.

Lean v4.36 gives `Float` a logical model in core: bit patterns, unpacked into a sign, a
significand and an exponent, with each operation rounding its exact result once through a round
bit and a sticky bit. `Palace/FloatModel.lean` proves that model's `+`, `*` and `/` are `rn`. The
proof turns on one invariant: an extended significand represents a value when it is the value's
floor and its two bits place the value against the midpoint. A right shift halves the represented
value, and core's ties-to-even choice is `rne` of it. Division also needs core's exponent estimate
to leave 53 bits of quotient, which it does for a canonical dividend. With the bridge, both entries
are theorems about Lean's `Float`, and the trust left is that the compiled C operators agree with
the logical model. That is attacked on this machine. Its control, `+` checked against the model's
`-`, is refuted on its first instance.

The two entries settle claims §2.5 makes about float64:

- CND-6. §2.5 says `(n−1)/n` rounds strictly below `1.0` "for realistic N_s". That holds for every
  `N_s < 2^54` (about 1.8·10¹⁶) and fails at `2^54`, where `1 − 2⁻⁵⁴` ties and rounds to the even
  `1.0` (`rn_div_two_pow_54`). Python divides two ints by rounding their exact quotient once (it
  matched `fractions.Fraction` on 200,000 random pairs of up to 80 bits), so `chi_s` is
  `rn(chain / n_s)`. The control, the same law in binary32, is refuted on its first instance.
- LAP-1. The route-agreement bound is a theorem for rows of at most four nonzero weights; every
  fixture row has at most three. It fails at eight (`lap1_fails`, reproduced on this machine). From
  `1 + 2u`, adding `3u` and then six `u` one at a time loses every tie and ends at `1 + 4u`; pairing
  them first wins three ties and ends at `1 + 14u`. For five to seven summands it is open, but an
  exhaustive search over every association order of one summand near `1` and the rest small
  multiples of `u/2` found no counterexample. Measured with NumPy 2.5.4 and SciPy 1.18.1 on
  2026-11-01, the two routes in the test first break the bound on a star of 37 weights, `1` and 36
  copies of a weight just under `2⁻⁵³`, by five ulps. Random rows of 8 to 3,000 weights in
  `[0.3, 1]` reached at most 0.66 of the bound. So the bound holds for short rows and for weights
  of modest range, not by construction. The control, eleven summands absorbed one at a time or
  gathered first, is refuted within 4 instances.

## Build

The toolchain is pinned in `lean-toolchain` (elan resolves it); Mathlib is pinned in
`lake-manifest.json`. On a fresh checkout, fetch the Mathlib cache first (several GB), then run the
gate:

```sh
lake exe cache get
./check.sh
```
