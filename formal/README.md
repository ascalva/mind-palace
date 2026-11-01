# formal

Rung L1 of the Lean ladder (`docs/design-notes/dn-mathematical-foundations.md` §2.4): statements of
the ledger's laws as Lean specs over exact arithmetic, each attacked by Plausible before anyone
proves it. A sibling lake package with zero import coupling with `core/` in either direction: Lean
states and proves laws over ℚ and ℝ, Hypothesis tests the floats in Python, and the law id joins
the two.

## Layout

- `Palace/Laplacian.lean`: LAP-1, LAP-2 and LAP-3 (`core/kernel/complex/laplacian.py`), with their
  attacks and controls at the end.
- `Palace/Memberships.lean`: the membership relation (`core/stores/memberships.py`) as a finite
  partial function on coordinate space, and MEM-1 to MEM-5.
- `Palace/Spectral.lean`: `L_sym` and LAP-4 (`laplacian_sym`), and the pseudo-inverse `L⁺` that
  `core/graph/conductance.py` takes for effective resistance (CND-1).
- `Palace/Balance.lean`: signed balance, LAP-5 and LAP-6 (`core/kernel/complex/balance.py`).
- `Palace/Cut.lean`: conductance, CUT-1 (`core/complex/cut.py`).
- `Palace/Curvature.lean`: Forman curvature, CRV-1 and CRV-2 (`core/kernel/complex/curvature.py`).
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

## Build

The toolchain is pinned in `lean-toolchain` (elan resolves it); Mathlib is pinned in
`lake-manifest.json`. On a fresh checkout, fetch the Mathlib cache first (several GB), then run the
gate:

```sh
lake exe cache get
./check.sh
```
