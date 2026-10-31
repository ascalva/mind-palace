# formal

Rung L1 of the Lean ladder (`docs/design-notes/dn-mathematical-foundations.md` §2.4): statements of
the ledger's laws as Lean specs over exact arithmetic, each attacked by Plausible before anyone
proves it. A sibling lake package with zero import coupling with `core/` in either direction: Lean
states and proves laws over ℚ and ℝ, Hypothesis tests the floats in Python, and the law id joins
the two.

## Layout

- `Palace/Laplacian.lean`: LAP-1, LAP-2 and LAP-3 (`core/kernel/complex/laplacian.py`), with their
  attacks and controls at the end.
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

The binarized forms (0/1 adjacency) reduce to Mathlib's `SimpleGraph.posSemidef_lapMatrix` and
`card_connectedComponent_eq_finrank_ker_toLin'_lapMatrix` in one line each.

Each attack has a control that drops one hypothesis and must be refuted. Plausible refutes the
LAP-1 and LAP-2 controls within 10 to 52 instances. It did not refute LAP-3 without `A ≥ 0` or
without symmetry in 215 to 396 tested instances, because a counterexample needs weights that cancel
at every vertex. Both hypotheses are shown to be needed by proved witnesses instead
(`lap_kernel_needs_nonneg`, `lap_kernel_needs_symm`).

## Build

The toolchain is pinned in `lean-toolchain` (elan resolves it); Mathlib is pinned in
`lake-manifest.json`. On a fresh checkout, fetch the Mathlib cache first (several GB), then run the
gate:

```sh
lake exe cache get
./check.sh
```
