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

## 2026-07-17 — item 3 checkpoint: legs 1–4 ATTESTED, leg 5 in flight, amendment chain closed

- **Gate legs 1–4 run separately, all green:** ruff full-tree ✓ · mypy targeted (216 files) ✓ ·
  **argless mypy tail == 69** (451 files checked; the 3 new test files added 0 — the watch item
  held) · type_gate Tier-2 + bare-ignore OK. **Leg 5 (full pytest) running in background** — item 3
  completes ONLY on its green; no status flip before.
- **Design-artifact chain fully closed mid-gate:** the owner hand-pasted the amendment banner into
  ratified `dn-connectivity-instruments` (agent-immutable A8 — the edit is the owner's); recorded
  `4e95480`, mirroring the bless-record precedent. The full accountable chain: note drafted
  `5394ddf` → owner-ratified (recorded `0d05001`) → track amended `3df5bcc` → bp-065 blessed
  (recorded `7f75fa9`) → items 1–2 built `2e362e9`+`53289bf` → source note banner `4e95480`.
- **REMAINING for item 3:** leg-5 green → flip bp-065 in-progress→complete + seal cost.actual
  (fable in-session; /usage relay pending for dollar/delta fields) → PROGRESS checkpoint →
  push to origin. Fresh-agent note: if this session dies, resume = check the background pytest
  output (b18wdjb9b), then execute exactly that list; ALL code work is committed.

## 2026-07-17 — SECOND AUDIT (owner-directed): fidelity + math + design-match + house style

- **Part 1 — AST move-fidelity (mechanical):** every top-level def of bp-059's original module and
  bp-060's harvest located across the new files and compared via docstring-stripped ast.dump.
  Result after fixes: **zero unsanctioned discrepancies** (33+35 defs IDENTICAL). The two sanctioned
  CHANGED (`_r_eff_matrix`, `_diffusion_distances`) were diffed line-level: ONLY the
  `_laplacian → _dense_laplacian` call swap + docstring wording. **Two real deviations found+fixed:**
  both retyped `run_*` wrappers had deferred the `MirrorGraph` import into the function body
  (originals import at module top) — behaviorally identical, but unsanctioned drift; restored.
- **Part 2 — independent math audit (first-principles oracles, live modules): ALL PASS** —
  maximin ≡ MST-bottleneck (brute force over ALL simple paths, 30 seeded random graphs, every
  pair); ultrametric inequality; R_eff circuit laws EXACT (single edge 1/w, series 1/w₁+1/w₂,
  triangle 2/(3w)); Rayleigh monotonicity (30 trials, every pair); finite-t distances ≡
  ‖expm(−tL)(e_i−e_j)‖ vs scipy.linalg.expm directly (the eigendecomposition is correct);
  sign law numeric (+lat conducts / −seq impedes / zero-churn ⇒ cos^α EXACTLY); conductance
  monotone under σ-loosening; dense-graph degeneracy corr high (von Luxburg direction);
  __all__ resolves everywhere.
- **Part 3 — design-match:** P1 tooth green; P2 layout = the owner-selected preview; P3 no other
  Laplacian derivation anywhere in scope (grep); P4/P6 core/complex + shadow/spine/ops_view
  UNTOUCHED all session (git); P5 full structural fidelity + bp-059 tests byte-untouched (git);
  all 32 carried test functions present incl. edit-rise/decay-null/idempotency/degeneracy
  falsifiers; zero stale math-home references. **One honest one-sided item:** P4 says Φ(S)/R_eff
  are "cross-referenced in both docstrings" — the core/graph side carries it; the RECIPROCAL line
  in `core/complex/cut.py` is NOT added (the note's own §1 puts core/complex out of scope; a
  trivial follow-up sweep or owner hand-line closes it). Recorded, not silently dropped.
- **Part 4 — house style:** OBJECT/INVARIANT/ENFORCED family headers on all three core files
  (velocity_view exemplar shape); `# ── section ──` rules; ≤100-col (ruff config) clean; `__all__`
  house-idiomatic (core/agent.py + 3 core __init__ precedents); import order (ruff) clean; r-strings
  where math symbols appear; test headers carry the plan-ref style.
- **Gate hygiene:** the first leg-5 run went green (1552-outcome tree) but STARTED before the two
  fidelity fixes — stale by discipline. Legs 1–4 re-run + a FRESH leg 5 on the final tree follow.

## 2026-07-17 — audit closed: fixes committed, final battery green, fresh leg 5 in flight

- Audit code fixes landed: import restoration (audit finding) + ruff isort reflow (`ccffcb4`).
  Post-fix fidelity re-check: **zero unsanctioned discrepancies** across all 68 moved defs.
- Owner asked about the `# re-export (core.graph.…)` tags: answered in-session — the P5 seam made
  visible (alias vs owned name; is-identity-pinned; F401-intentional; transitional until the
  bp-061/062 re-mints import core.graph directly). No artifact change needed.
- Final targeted battery on the audited tree: **54 passed**. Legs 1–4 re-attested (argless == 69).
- **Fresh leg 5 (full suite) running on the FINAL tree** (task bg8ewhcrs) — the earlier green
  (1538p/8s, 9:28) attested the pre-fix tree; discipline demands the final tree's own attestation.
- REMAINING on green: flip in-progress→complete + seal (fable in-session; /usage relay still
  pending for dollar/delta fields) → PROGRESS → push. All code committed through `ccffcb4`.

## 2026-07-17 — THE CLEAN BREAK (owner-directed): no wrappers, harness is a plain consumer

- **Owner ruling:** the re-export aliases were unnecessary ceremony — the eval modules should be
  plain instrument code that IMPORTS the core instruments, not wrappers. Approved widening
  write_scope by bp-059's two test files (the note §11 "tests relocation" re-entry, owner-invoked).
- **Executed:** dropped both `__all__` blocks + every alias import from `eval/harness/
  {connectivity,conductance}.py`; each now imports from `core.graph` ONLY the names its body uses
  (connectivity drops CrossingEdgeError+sigma_star; conductance drops chi_s+churn_weight+
  effective_conductance+reconnection_scan — all were re-export-only). Repointed all four test
  files' MATH imports to `core.graph.{sigma_star,conductance}`, leaving INSTRUMENT names
  (ConnEvidence/METRIC_*/run_*) sourced from eval. Deleted the two now-moot `is`-identity
  re-export teeth from test_graph_boundary.py (no re-exports left to drift); P1 no-eval, Law-C4,
  and the L-equivalence/R_eff-invariance teeth all remain.
- **Census before trimming (safety):** grep confirmed NO star-imports and NO production importers
  of the relocated names — only the 4 test files (+ conductance's intra-eval ConnEvidence). Nothing
  outside test scope could break.
- **End state:** no wrappers anywhere. `core.graph` owns the math; `eval/harness` is a plain
  consumer that owns the lab-notebook (evidence pins, keying, aggregate readings). Arrow strictly
  `eval → core.graph → core.complex`.
- **Gate:** ruff full-tree clean (isort --fix on the 4 tests) · mypy targeted 216 · **argless == 69**
  · type_gate OK · targeted battery 52p (was 54 — the 2 deleted re-export teeth). Full leg 5 next.

## 2026-07-17 — bp-065 COMPLETE + SEALED

- **Full-suite leg 5 on the clean-break tree: 1536 passed / 8 skipped** (1536 = the 1538 pre-clean-
  break minus the 2 deleted re-export identity teeth — exactly expected). All 5 legs green on the
  final tree (ruff · mypy targeted 216 · argless 69 · type_gate · pytest).
- Status in-progress→complete (non-blessing). cost.actual sealed: mixed tier fable→opus (owner
  switched mid-build), tokens/dollars/deltas pending the /usage relay; merged direct on main
  552f885→084739d; scope_notes record the audit + clean break shipped beyond the staged plan.
- **The reconciliation is DONE.** core/graph owns the σ*/conductance math (on core/complex's one
  Laplacian); eval/harness is a plain consumer (no wrappers). Arrow eval → core.graph → core.complex.
  bp-060 superseded, its build preserved on branch + shipped here behavior-frozen.
- Active-plan pointer cleared → orchestrator posture. OWED (orchestrator, now unblocked): the
  cross-session MEMORY note (core-self-containment; scope-guard blocked it mid-builder-contract),
  PROGRESS checkpoint, push to origin. Follow-ons: finding-0102 (shadow.py eval-logic) + the
  store-inversion are the remaining "core self-contained" work; bp-061/062 re-mint against core/graph.
