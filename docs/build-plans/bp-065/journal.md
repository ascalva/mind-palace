# Journal — bp-065 (core-graph-rehome)

In-session orchestrator self-build, fable/xhigh (owner-directed, session-26). Minted on
ratification of dn-core-graph-instruments; blessed ready by owner hand (recorded `7f75fa9`).

## 2026-07-17 — item 1 COMPLETE: core/graph/sigma_star.py + thin connectivity + boundary teeth

- **Manifest formatting repair (pre-item):** scope-guard parses write_scope entries LITERALLY —
  my inline YAML comments made 5 paths unmatchable (Write denied, correctly). Moved the comments
  to a block above the list; the blessed capability is byte-identical. Not a scope change.
- **The split:** `core/graph/sigma_star.py` takes the MATH verbatim (CrossingEdgeError, ConnIndex,
  SigmaStar, MaxSpanningForest, build_max_spanning_tree, _tree_path_bottleneck, _grid_snap,
  _SNAP_EPS, sigma_star, pairwise_sigma_star, cut_fingerprint, acquire_mirror_cut,
  _MIRROR_STRATUM). `eval/harness/connectivity.py` keeps the INSTRUMENT (ConnEvidence, ConnResult,
  _aggregate, _corpus_ref, _spec_hash, run_connectivity, METRIC_*, _INSTRUMENT/_TYPE_TAG) +
  re-exports every moved name under `__all__` (P5). Code moved byte-identical; only docstrings
  updated for placement. `run_connectivity` keeps a deferred `MirrorGraph` import (build-time only).
- **Import surfaces verified pre-move** (grep, journal-worthy): the ONLY importers of connectivity
  anywhere are its two bp-059 test files + the harvest tests; every cross-file import is a public
  name (no private leaks). Re-export set = exactly the moved publics.
- **One surprise + fix:** `core.graph.sigma_star` is ambiguous as an ATTRIBUTE — the package
  __init__ re-exports the *function* sigma_star, which shadows the same-named submodule (PEP-328
  getattr binding). `from core.graph.sigma_star import X` is unaffected (sys.modules path); the
  boundary test addresses the modules via importlib. Documented in the test.
- **Acceptance RUN:** `uv run pytest tests/unit/test_connectivity.py
  tests/quality/test_connectivity_sigma_star.py tests/unit/test_graph_boundary.py -q` →
  **19 passed** (bp-059 suites UNCHANGED — zero edits, out of write_scope by design). ruff clean;
  `mypy core agents eval ops scheduler scripts` → 214 files clean. Boundary teeth green:
  P1 no-eval-import (static AST, package-own files — NOT the closure; spine's P6 sink is tolerated),
  Law-C4 no-clock, P5 is-identity on all 9 re-exports.
- **NEXT:** item 2 — conductance harvest (core/graph/conductance.py from scratchpad bp060-harvest/,
  `_laplacian` → core.complex adapter `_dense_laplacian`), eval wrapper, tests + the ONE retarget
  (`_CONDUCTANCE_SRC`), L-equivalence tooth, __init__ extension.

## 2026-07-17 — item 2 COMPLETE: conductance harvested onto the ONE Laplacian + thin wrapper

- **The split:** `core/graph/conductance.py` takes the MATH verbatim from the harvest (branch
  commits 3c7421e+88e73ca via the scratchpad snapshot): churn_weight (signs-as-law), profile family,
  χ_s/depth-budget, reconnection scan (finding-0099 weight-increased attribution). **`_laplacian`
  DELETED** → `_dense_laplacian` adapter routing through `core.complex.laplacian.laplacian`
  (csr-wrap at the boundary, densify for eigh/pinv). `eval/harness/conductance.py` is NEW and thin:
  ConductanceEvidence (+t_grid pin), ConductanceResult, keying/aggregate, run_conductance,
  re-exports under __all__. Tests harvested with the ONE sanctioned retarget
  (`_CONDUCTANCE_SRC → core/graph/conductance.py`) — the AST teeth follow the math they guard.
- **OWNER MID-BUILD DIRECTIVE (honored):** core modules carry the OBJECT/INVARIANT/ENFORCED
  family header (29 precedents; `velocity_view.py` the nearest — an instrument family). The eval
  originals had none (eval convention differs); all three core/graph files now carry it. A real
  correct-treatment gap the move initially missed.
- **MEASURED NUMERICS FINDING (journal-grade, not a plan finding):** the routed Laplacian's
  OFF-DIAGONAL is EXACTLY equal to the direct dense construction; the DIAGONAL (degrees) differs by
  ~1 ulp (2.22e-16 at degree 1.8) — NumPy's unrolled multi-accumulator dense sum vs SciPy's
  sequential nonzero sum: float REASSOCIATION of the same values. My staged claim "exact at fixture
  scale (n<128 ⇒ sequential)" was WRONG (NumPy unrolls even at n=7). The P4 tooth is therefore:
  off-diag exact + degrees ≤ 4·eps·max-degree + VALUE-level R_eff invariance (rtol 1e-10; an L_sym
  substitution fails at O(1)). This is the plan §7 item-2 "identical profile values" criterion
  made float-honest.
- **Package-attribute shadowing (carried from item 1):** `core.graph.sigma_star`-as-attribute is
  the function; modules addressed via importlib in tests.
- **Acceptance RUN:** unit+quality conductance suites + boundary + bp-059 suites → **54 passed**.
  ruff clean; mypy targeted 216 files clean. Sign-law AST, THRESH-dict AST, Law-C4 no-clock,
  edit-rise attribution, decay-null, degeneracy-always-present: all green against the CORE file.
- **NEXT:** item 3 — full 5-leg gate (argless == 69 the watch item; 3 new test files must add 0),
  then seal + ledger (bp-060 → superseded is already recorded; PROGRESS + status flip on green).
