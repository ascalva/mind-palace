---
type: build-plan
id: bp-065
alias: core-graph-rehome
status: proposed
design_ref:
  - docs/design-notes/core-graph-instruments.md      # the placement ruling (P1-P6) this executes
  - docs/design-notes/connectivity-instruments.md    # RATIFIED — the MATH (CN-2/3/4) — unchanged, amended on placement only
contract: builder
write_scope:
  - core/graph/__init__.py
  - core/graph/sigma_star.py
  - core/graph/conductance.py
  - eval/harness/connectivity.py                     # thin-ify + re-exports (the ONE existing file edited)
  - eval/harness/conductance.py                      # NEW thin wrapper
  - tests/unit/test_conductance.py                   # harvested from bp-060's branch
  - tests/quality/test_conductance_reconnection.py   # harvested (builder's filename kept)
  - tests/unit/test_graph_boundary.py                # NEW — the P1 import-boundary + P3 equivalence teeth
session_budget: 1
cost:
  estimate:
    model: fable          # owner-directed session tier (in-session self-build, session-26)
    tokens: 90k
  actual: null
depends_on: [bp-059]
parallelizable_with: []
supersedes: bp-060        # the eval-homed conductance plan — its built math ships HERE (branch preserved)
superseded_by: null
warrant: docs/findings/finding-0101.md
created: 2026-07-17
updated: 2026-07-17
links:
  - docs/findings/finding-0101.md                    # the duplication evidence
  - docs/build-plans/bp-060/plan.md                  # absorbed; its §7 items 4-6 acceptance criteria carry over
re_entry: null
---

# Build Plan — re-home the connectivity math into `core/graph/` (dn-core-graph-instruments P1-P5)

## 0. Mode & provenance
Graduated from `dn-core-graph-instruments` (owner-ratified; warrant finding-0101). In-session
orchestrator self-build at fable (owner-directed, session-26). **A relocation + thin-ification,
not a re-design:** every mathematical decision is pinned by `dn-connectivity-instruments`
(unchanged) and by bp-060's built+tested implementation (branch
`worktree-agent-a1d5f2b78350b8586`, commits `3c7421e` + `88e73ca`; snapshot in session
scratchpad `bp060-harvest/`). Where this plan and the harvested code disagree, the harvested
code's *behavior* wins (P4: no silent metric change) and the discrepancy is journaled.

## 1. Objective
`core/graph/` exists and owns the σ-connectivity mathematics (σ*/MST + ConnIndex +
acquire_mirror_cut; the (σ,t) conductance profile family + churn measure + χ_s + reconnection
attribution), built on `core/complex/laplacian.py`'s single Laplacian; `eval/harness/
{connectivity,conductance}.py` are thin instruments (readings, evidence, entry points) that
import it; the P1 boundary is pinned by a permanent test; the full 5-leg gate is green with
argless mypy == 69 and bp-059's test files passing **unchanged**.

## 2. Context manifest (read in order)
1. `docs/design-notes/core-graph-instruments.md` — WHOLE (P1-P6 are the contract).
2. `eval/harness/connectivity.py` @ main — the bp-059 module to split: math out
   (`build_max_spanning_tree`, `sigma_star`, `_tree_path_bottleneck`, `_grid_snap`,
   `ConnIndex`, `acquire_mirror_cut`), instrument stays (`ConnEvidence`, `run_connectivity`,
   readings, fingerprints).
3. Scratchpad `bp060-harvest/conductance.py` (== branch `88e73ca` working state) — the
   implementation to split: math out (`ConductanceProfile`, `ReconnectionEvent`,
   `CONDUCTANCE_THRESH`, `churn_weight`, `sigma_t_profile`, `reconnection_scan`, χ_s +
   depth-budget helpers), instrument stays (`run_conductance`, readings/evidence). Its
   `_laplacian` (line ~223) is DELETED → `core/complex/laplacian.laplacian`.
4. `core/complex/laplacian.py:21-33` — `_degree` (weighted row sums), `laplacian` (csr in).
5. `bp060-harvest/{test_conductance.py, test_conductance_reconnection.py, journal.md}` —
   the tests to land (sign-law grep tests retarget to `core/graph/conductance.py`) + the
   builder's journal (context for any surprise).
6. bp-060's plan §7 (items 4-6) — the acceptance criteria + falsifiers, which carry over
   verbatim to the harvested tests.

## 3. Investigation & grounding
Done pre-plan (session-26 audit): the ratified note pinned "All eval-side" (§3:210 —
amended); `core/complex` has the Laplacian (weighted, combinatorial) but NOT: pairwise R_eff,
finite-t heat-kernel distances over combinatorial L, σ-grid machinery — those are new math
and belong in `core/graph` (P4). `diffusion_map` (L_sym) is a sibling geometry — do NOT
substitute it. bp-060's branch state: items 4-6 committed, final 5-leg attestation never run
(builder stopped) — THIS plan's gate is the attestation.

## 4. Reconciliation
- `eval/harness/connectivity.py` re-exports every moved name → bp-061/062 §6 pins and
  bp-059's tests resolve unchanged (P5). Zero edits to `tests/*connectivity*` — structural
  compat proof (they are OUT of write_scope).
- `core/complex/**` untouched (read-only reuse); cross-references added only in the NEW
  modules' docstrings (Φ(S) vs R_eff; diffusion_map vs finite-t heat kernel).

## 5. Write scope
Front-matter list exactly. **OUT:** `core/complex/**`, `tests/unit/test_connectivity*.py`
(must pass unchanged — the tooth), `core/dreaming/**`, `core/temporal/**`, `eval/harness/
{store,gate,fibers}.py`, `ops/**`, foundation denylist.

## 6. Interfaces pinned inline
```python
# core/graph/sigma_star.py — MOVED VERBATIM from eval/harness/connectivity.py (signatures frozen):
#   ConnIndex, acquire_mirror_cut(spine), build_max_spanning_tree, sigma_star(forest,a,b,*,grid)
# core/graph/conductance.py — MOVED from harvest (signatures frozen):
#   CONDUCTANCE_THRESH, ConductanceProfile, ReconnectionEvent,
#   churn_weight(sim_uv,a_lat,a_seq,thresh), sigma_t_profile(graph,*,sigma_grid,t_grid,thresh),
#   reconnection_scan(before,after,*,proper_time_gap)
#   — Laplacian obtained as: L = core.complex.laplacian.laplacian(sp.csr_matrix(W)).toarray()
# eval/harness/connectivity.py — KEEPS ConnEvidence, run_connectivity; re-exports the moved names.
# eval/harness/conductance.py — NEW: run_conductance + readings; re-exports the moved names.
```

## 7. Items
### Item 1 — `core/graph/` + sigma_star relocation + connectivity thin-ify  (blast: move, behavior-frozen)
- **Acceptance:** `uv run pytest tests/unit/test_connectivity.py tests/unit/test_connectivity_sigma_star.py -q`
  green with ZERO edits to those files; `tests/unit/test_graph_boundary.py` green: (a) no
  `eval` module in `core.graph`'s recursive import closure, (b) every re-exported name is
  the same object (`is`-identity) via both paths.
- **Falsifier:** any `from eval` under `core/graph/`; a connectivity test needing an edit;
  a re-export drifting from the core object.

### Item 2 — conductance harvest + one-Laplacian + thin wrapper  (blast: additive + the L swap)
- **Acceptance:** harvested unit + quality suites green with sign-law greps retargeted to
  `core/graph/conductance.py`; the P3 equivalence test green: `core.complex.laplacian` path
  produces the IDENTICAL L (allclose, atol=0) and identical profile values vs the harvested
  `_laplacian` on a fixture graph (the harvested function is inlined in the TEST as the
  reference oracle, then absent from core/graph); bp-060 §7 falsifiers all still enforced
  (edit-rise attribution, decay-null, degeneracy_diag always present, signs-as-law).
- **Falsifier:** any profile value changed by the move (silent metric change — P4 violated);
  the sign-law tooth grepping a stale path (guarding nothing); `_laplacian` surviving in core/graph.

### Item 3 — full gate + ledger  (blast: none)
- **Acceptance:** 5 legs separately: ruff · mypy targeted · argless mypy tail == 69 ·
  type_gate · pytest full (≥1498p equivalent + the new suites). Journal complete
  (fresh-agent test). PROGRESS + seal by orchestrator.

## 8. Math carried explicitly
Inherited verbatim from bp-060 §8 (R_eff/profile validity, weighted-Rayleigh attribution
law, finite-t diffusion, χ_s, churn measure) — no new mathematical object is introduced by
this plan; its own tooth is P3/P4 *invariance*: the move changes no computed value.

## 9. Non-goals
No bridges/helix (re-mints, post-landing). No `core/complex` edits. No readings-store move
(parked). No shadow.py work (finding-0102). No new metrics, grids, or thresholds. No
metric-name registration (bp-059 deferral stands).

## 10. Stop-and-raise
- The harvested implementation fails its own tests pre-move → STOP, journal, diagnose on the
  branch first (the move must start from green).
- The equivalence test shows the core/complex L differs from the harvested one → STOP (a
  real math discrepancy, not a refactor issue) — file a `math` finding.
- Any blessing: never.

## 11. Parked decisions
Inherits dn-core-graph-instruments' table (readings-sink, shadow.py, tests relocation) +
bp-060 §11 (real-corpus reconnection partial; a_• convention; magnitudes-as-levers; grain).

## 12. Ordering
Items 1 → 2 → 3 strictly. Downstream: bp-061/062 re-mints build on `core/graph/`; bp-064
(chat lane) independent.
