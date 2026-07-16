---
type: build-plan
id: bp-052
alias: velocity-pair
status: proposed
design_ref:
  - docs/design-notes/velocity-instruments.md   # RATIFIED 2026-07-15 — §2.2 (a) RotationReport + (b) alive/stale; §2.1 X1–X3 typing; §3.1 licenses exactly this plan
contract: builder
write_scope:
  - core/temporal_view.py
  - core/velocity_view.py
  - tests/unit/test_rotation_report.py
  - tests/unit/test_alive_stale.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 180k
depends_on: []
parallelizable_with: [bp-050, bp-051]
created: 2026-07-16
updated: 2026-07-16
links:
  - docs/design-notes/temporal-retrieval-algebra.md   # R4 — what (a) measures; §2.5 A7 — the discriminator binding (b)
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — the velocity measurement pair: RotationReport + the alive/stale hole discriminator

## 0. Mode & provenance
Graduated from RATIFIED `dn-velocity-instruments` (§3.1: "ONE build plan now: the
measurement-class pair"). Every pin below is the note's §2.2 verbatim — this plan adds NO design;
X2 says measurement-class instruments need no sample-depth gate, which is why this ships now.

## 1. Objective
(a) A `RotationReport` beside `CoherenceReport` in `core/temporal_view.py`: principal angles
between `ker L₁(X_cite,n|common)` and `ker L₁(X_cite,n+1|common)` at two commit anchors.
(b) A thin `core/velocity_view.py`: the global alive/stale harmonic-velocity energy
`‖P_harm(Δw)‖` (+ per-eigenspace split) over the mirror-side weighted backbone's common
restriction, interpreter-version-guarded (A7).

## 2. Context manifest (read in order)
1. `docs/design-notes/velocity-instruments.md` §2.1–§2.2 (WHOLE — every pin), §2.4.
2. `core/temporal_view.py` (whole) — `CoherenceReport`'s two-anchor factory shape + the
   `_restrict`-to-common pattern (a) mirrors; the shared `_resolve_default_commit`.
3. `core/temporal/complex.py` — `X_cite` assembly (the (a) substrate).
4. `core/complex/hodge.py` — the projectors `P_harm` (b) consumes; `dim ker L₁` (the built
   falsifier surface).
5. `docs/design-notes/temporal-retrieval-algebra.md` §2.5 — A7 (the (b) guard, verbatim).

## 3. Investigation & grounding
- **(a) is `Inv`** (subspace geometry on two anchors' event sets — no clock division); anchors
  are commit points (the built cut clock). **(b) is `Inv`** per window pair; the `Rate(κ)`
  versions are VI-a parked (bp-053's N_s later gives them clocks — NOT this plan).
- **(b)'s A7 guard:** `Δw` computed at a FIXED interpreter version; a version boundary inside
  the window ⇒ emit NOTHING (an empty report with the reason recorded — the honest seam).
- **Both read-only, deterministic, model-free, erasure-invariant** — the instrument definition.

## 4. Reconciliation
None expected. If `hodge.py`'s projector surface differs from the note's assumption → a
`codebase` finding + adapt in-scope (the projectors are read-only dependencies).

## 5. Write scope
The four files in frontmatter. **OUT:** `core/complex/**` (read-only — the isolation invariant:
never import `reference_edges` from inside it, and this plan does not touch it), stores,
`eval/**`, denylist.

## 6. Interfaces pinned inline
```python
# (a) — extends core/temporal_view.py, the CoherenceReport factory shape mirrored
@dataclass(frozen=True)
class RotationReport:
    anchor_a: str; anchor_b: str            # commit SHAs (both recorded — Inv carries its anchors)
    n_common: int
    beta1_a: int; beta1_b: int
    principal_angles: tuple[float, ...]     # radians, ascending; () when beta1 == 0 at either anchor
    empty_reason: str | None                # the honest seam — never fabricated geometry

# (b) — core/velocity_view.py (thin; consumes hodge projectors on the common restriction)
@dataclass(frozen=True)
class AliveStaleReport:
    anchor_a: str; anchor_b: str
    interpreter_version: str                # FIXED across the window or the report is empty
    harmonic_energy: float                  # ‖P_harm(Δw)‖
    gradient_energy: float; curl_energy: float
    empty_reason: str | None
```

## 7. Items
### Item 1 — RotationReport
- **Acceptance:** `uv run pytest tests/unit/test_rotation_report.py -q` green: identical
  snapshots ⇒ all angles 0; β₁=0 at either anchor ⇒ empty report with reason (no fabricated
  geometry); angles agree with an independent SVD computation on the same bases (the note's
  falsifier, implemented as a test with its own SVD path); deterministic run-to-run.
- **Falsifier:** any nonzero angle on identical snapshots; geometry emitted at β₁=0.
### Item 2 — the alive/stale energy
- **Acceptance:** `uv run pytest tests/unit/test_alive_stale.py -q` green: β₁=0 ⇒ zero claims/
  empty; a synthetic pair with weights changed ONLY along gradient directions ⇒ harmonic energy
  ≈ 0 (tolerance pinned in-test); the three Hodge components orthogonal within tolerance on
  every evaluated pair; a version boundary inside the window ⇒ empty report with reason.
- **Falsifier:** harmonic energy from gradient-only change; a reading emitted across an
  interpreter-version boundary (the A7 violation — the exact apophenia leak this instrument
  exists to refuse).

## 8. Math carried explicitly
Principal angles: θ_i from SVD of `Q_a^T Q_b` (orthonormal bases of the two kernels restricted
to common cells); the report never divides by a clock (Inv). Energy split: `Δw = P_grad Δw +
P_curl Δw + P_harm Δw` (built projectors); alive = sustained `‖P_harm(Δw)‖ > 0`. Three clauses
per instrument live in the note §2.2 — the tests above ARE the falsifier clauses.

## 9. Non-goals
No Rate versions (VI-a), no per-hole localization (VI-b — waits on the THREAD lens), no
similarity-backbone rotation variant (VI-c), no store surface, no model, no spine dependency.

## 10. Stop-and-raise
`hodge.py` projectors not exposing what (b) needs → finding + stop that item (do not reach into
`core/complex` internals beyond its public surface). Any blessing: never.

## 11. Parked decisions
Inherited verbatim: VI-a/VI-b/VI-c (the note's table) — none re-opened here.

## 12. Dependency & ordering
No dependencies; parallel with bp-050/bp-051 (disjoint scopes). Feeds DD-1's charter (named
inputs) and the demon-vs-source protocol (V6, later). Blast radius: additive read-only — lowest.
