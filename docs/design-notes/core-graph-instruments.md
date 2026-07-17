---
type: design-note
id: dn-core-graph-instruments
status: draft            # draft → ratified → superseded.  draft→ratified is an OWNER-ONLY hand edit.
implementation: bp-065 (mints on ratification)
created: 2026-07-17
updated: 2026-07-17
links:
  - docs/design-notes/connectivity-instruments.md   # RATIFIED — AMENDED here on PLACEMENT ONLY (§3:210 "All eval-side"); every mathematical decision stands
  - docs/findings/finding-0101.md                    # THE WARRANT — the tranche re-derives core/complex primitives in the harness
  - docs/findings/finding-0102.md                    # the adjacent boundary violation this note names but does NOT fold in (shadow.py)
  - docs/build-plans/bp-059/plan.md                  # complete (67b373d) — σ* math relocates, plan stays complete
  - docs/build-plans/bp-060/plan.md                  # built on branch worktree-agent-a1d5f2b78350b8586 (3c7421e, 88e73ca) — absorbed by bp-065
supersedes: null         # an AMENDMENT-BY-LINK, not a supersession: dn-connectivity-instruments stays ratified for the math
superseded_by: null
warrant: docs/findings/finding-0101.md
---

# Graph instruments live in core: the self-containment ruling

> Composed at **fable** (`claude-fable-5`/xhigh, 2026-07-17 session-26, owner-chartered in
> session: *"I do not agree with that machinery being outside of the core, and it feels silly
> that the core itself has to import it from the outside"* — the owner then selected the
> target architecture (recorded verbatim in §2 P2) and directed the reconciliation performed
> immediately). Filed as `draft`; ratification is owner-by-hand; `/graduate` refuses this
> note until ratified. **Design only; no build until bp-065 is blessed.**

## 1. Purpose and scope

Re-home the connectivity-instrument **mathematics** — σ*/MST, the (σ,t) conductance profile,
the churn change-of-measure, reconnection attribution, and (on re-mint) bridges and helix —
from `eval/harness/` into `core/`, and state the boundary principle that makes the placement
a rule rather than a taste. This note **amends `dn-connectivity-instruments` on placement
only** (its §3:210 pinned the tranche "All eval-side"); every mathematical decision in that
note — CN-2..CN-6, the signs-as-law churn measure, the grid discipline, the von-Luxburg
self-diagnostic, the leave-one-out attribution law (finding-0099) — **stands unchanged and
stays ratified there**. Out of scope: the readings-sink direction and `shadow.py`'s eval-logic
imports (named in §2 P6, parked / routed to finding-0102), the golden set (foundation
denylist), and any change to `core/complex/` itself (reused read-only).

## 2. Principles / decision

**P1 — Core self-containment.** `core/` never imports `eval/` for *mathematics*. The graph's
own vocabulary — distances, conductance, spectra, curvature, connectivity scales — is core
vocabulary: the peer of `MirrorGraph.degree`/`local_clustering` (`core/dreaming/graph.py:22-59`)
and of the existing `core/complex/` family (`laplacian.py:26`, `spectral.py:63,73`,
`cut.py:35,53,70`, `curvature.py:25,46`). What is eval's: *grading* — readings
(`EvalKey`/`Reading`), evidence fingerprints, gate falsifiers, drift baselines. Instruments
in eval **import** core math; the arrow never reverses. (Bright line #1 "sealed core" is
about *network egress* and is untouched either way — this principle is its sibling for
*conceptual* containment: the core describes itself in its own language.)

**P2 — The home (owner-selected architecture, 2026-07-17).** A new package **`core/graph/`**
holds the σ/temporal connectivity instruments over `MirrorGraph` + `Spine`:

    core/
      complex/          (UNCHANGED: laplacian, spectral, cut, curvature — the ReasoningComplex math)
      graph/            NEW — the σ-connectivity instruments
        sigma_star.py     (σ*/MST + grid-snap + ConnIndex + acquire_mirror_cut — from bp-059's eval module)
        conductance.py    ((σ,t) profiles + churn measure + χ_s + reconnection — from bp-060's build)
        bridges.py        (bp-061 re-mint), helix.py (bp-062 re-mint)
    eval/harness/
      connectivity.py   → thin instrument: run_connectivity + ConnEvidence + readings; imports core.graph
      conductance.py    → thin instrument: run_conductance + readings; imports core.graph

Dependency arrow: `eval → core.graph → {core.complex, core.temporal, core.dreaming}`. Not
`core/complex/` extensions: the σ-graph instruments are a distinct conceptual object from the
ReasoningComplex (companion III), even though both derive their adjacency from the same
cosine-over-notes source (`core/complex/build.py:62,108` vs `MirrorGraph.sim`) — folding them
together was considered and rejected at selection.

**P3 — One Laplacian.** The combinatorial Laplacian comes from
`core/complex/laplacian.py:26` (`laplacian`, L = D − A, weighted row-sum degrees). The dense
re-derivation in bp-060's build (`conductance.py:223 _laplacian`) is **deleted in the move**;
bp-059's module never built one. `MirrorGraph`'s dense `np.ndarray` weights wrap to
`sp.csr_matrix` at the call boundary and L densifies for `eigh`/`pinv` (corpus scale is
small — finding-0096); the matrix is *identical* either path, and bp-065 pins that with an
explicit equivalence test against the harvested implementation's values.

**P4 — No silent metric change (the rigor clause).** Reuse is bounded by object identity,
not by name resemblance:
- `core/complex/spectral.py:73 diffusion_map` is the **L_sym** (normalized) diffusion
  geometry — bottom eigenvectors of I − D^{-1/2}AD^{-1/2}, heat-scaled. bp-060's finite-t
  distances are the heat kernel **exp(−tL) of the combinatorial L** (full spectrum,
  `conductance.py:265`). These coincide only on degree-regular graphs; on the real corpus
  they are *different metrics*, and the von-Luxburg degeneracy diagnostic is calibrated
  against R_eff over the *same* L used for the commute distances. Forcing one implementation
  onto the other would silently change every profile value. **Ruling:** `core/graph/
  conductance.py` computes its finite-t heat-kernel distances over `core/complex`'s L (no
  primitive for this exists — it is new instrument math, not duplication); `diffusion_map`
  stays as-is; the relationship is a documented cross-reference, not a unification.
- `core/complex/cut.py:35 conductance(A, S)` is **set (Cheeger) conductance Φ(S)**; the
  instrument's pairwise **effective resistance R_eff(a,b) = (e_a−e_b)ᵀL⁺(e_a−e_b)** is a
  two-point object (commute time = vol·R_eff). Related through the same electrical network,
  not the same function. Both stand, cross-referenced in both docstrings.

**P5 — The eval boundary (compatibility contract).** `eval/harness/connectivity.py` and
`eval/harness/conductance.py` become thin instruments: entry points (`run_*`), `ConnEvidence`
+ fingerprints, keyed idempotent readings, gate coupling. They **re-export** every relocated
name, so bp-061/062's §6-pinned imports and every existing test resolve unchanged until the
re-mint — the acceptance proof that the move is behavior-preserving is that bp-059's test
suites pass **without edits**. (The one sanctioned test edit class: bp-060's sign-law
grep/AST tests retarget their scanned path from `eval/harness/conductance.py` to
`core/graph/conductance.py` — the *tooth* moves with the math it guards.)

**P6 — The boundary audit, ruled on in full** (so this note decides the whole surface, not
one file):
- `core/temporal/spine.py:97`, `core/dreaming/shadow.py:59-260`, `core/ops_view.py:43`
  import `eval.harness.store` / `eval.drift` types as a **readings sink** — core *writing
  its measurements out*. Tolerated (a sink, not math), **parked** with re-entry below.
- `core/dreaming/shadow.py:50-58` imports `eval.drift` **logic** (`drift_from_report`,
  `load_drift_config`) and `eval.golden` — a true P1 violation in the other direction (or a
  mis-homed instrument living in core; the symmetric question). **Not folded into this
  change** — routed to finding-0102, its own reconciliation lane.
- **Standing rule for future graduations:** new graph/spectral/temporal mathematics
  graduates into `core/` (`core/graph/` or `core/complex/` per object); `eval/` gets
  wrappers. A plan that homes new math in `eval/` must cite an explicit owner exception.

**Structural invariant (the permanent tooth).** `from eval`/`import eval` never appears
under `core/graph/` — pinned by a unit test that walks the package's imports, shipped in
bp-065 and never removed. The falsifier is one line of grep.

## 3. Consequences

- **bp-065 (`core-graph-rehome`) mints on ratification** and executes the move in one
  gated landing: create `core/graph/`; relocate bp-059's math out of
  `eval/harness/connectivity.py` (re-exports in place); harvest bp-060's built work from
  branch `worktree-agent-a1d5f2b78350b8586` (`3c7421e` items 4-5, `88e73ca` item 6;
  snapshot in session scratchpad) into `core/graph/conductance.py` + thin
  `eval/harness/conductance.py`; delete the duplicate `_laplacian`; add the boundary test +
  the P3 equivalence test; retarget the sign-law tests; full 5-leg gate (argless mypy == 69).
- **bp-060 → `superseded`** (superseded_by bp-065, warrant finding-0101) at bp-065 mint;
  its branch is preserved unmerged (the eval-homed full implementation never lands on main).
  Its builder's math — including the finding-0099 edit-rise attribution — ships via bp-065.
- **bp-059 stays `complete`** (history is fact); its module thins to a wrapper, every
  import path preserved.
- **bp-061/062 → superseded + re-minted** against `core/graph/{bridges,helix}.py` homes
  after bp-065 lands (their §6-§8 math carries over verbatim; write_scopes change; owner
  re-blesses the re-mints). Until then they are held (oq-0030).
- **The chat lane (bp-064) is untouched** and proceeds independently.

## Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| readings-sink direction (core→`eval.harness.store`) | tolerated as a sink | invert now (relocate the store core-side) — a store move mid-reconciliation compounds risk | the sink grows logic, or the owner charters the full inversion |
| `shadow.py` eval-logic imports | finding-0102, own lane | fold into bp-065 — different subsystem, different question (mis-homed instrument vs mis-homed math) | owner appetite post-bp-065 |
| tests relocation to mirror new homes | tests stay in place (re-exports keep them green) | move now — churns the argless-mypy baseline for zero behavior | next test-hygiene sweep |
| `core/graph/` vs folding into `core/complex/` | separate package (owner-selected) | extend complex/ directly — conflates the σ-temporal graph with the ReasoningComplex kx | a later unification note if the two objects converge |

## Cross-references

Owner ruling + architecture selection: session-26, 2026-07-17 (AskUserQuestion, option "New
core/graph/, reuse core/complex" — preview recorded in §2 P2). Warrant: finding-0101 (the
duplication evidence: `core/complex/{laplacian:26, spectral:63-73, cut:35-70, curvature:25-46,
build:62-108}` vs `eval/harness/connectivity.py@67b373d` and bp-060's
`conductance.py:223,265`). Amended note: `dn-connectivity-instruments` (ratified; §3:210).
Adjacent: finding-0102 (`core/dreaming/shadow.py:50-58`). Suite baseline at drafting:
1498p/10s on main `7cc0975` + working tree; argless mypy 69.
