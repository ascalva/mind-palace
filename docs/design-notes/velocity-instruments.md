---
type: design-note
id: dn-velocity-instruments
status: draft            # draft → ratified → superseded.  draft→ratified is an OWNER-ONLY hand edit.
implementation: design-only # nothing built; two instruments are measurement-class and buildable on ratification
created: 2026-07-15
updated: 2026-07-15
links:
  - docs/brainstorms/velocity-and-clocks-fable-pass.md # THE WARRANT — X1–X3 + V1–V6 with grades
  - docs/brainstorms/edge-dynamics-vector-field.md # the owner thread (the six novel_objects) this formalizes
  - docs/design-notes/edge-dynamics.md # ratified; the R-ladder + inversion (§2.5) this note's X2 sharpens
  - docs/design-notes/temporal-retrieval-algebra.md # R4 (kernel non-flatness), R6 (contraction), A7 (apophenia)
  - docs/design-notes/temporal-geometry-and-drives.md # the sibling note (clocks/geometry/drives; drafted same day)
  - docs/design-notes/capability-scope-algebra.md # Inv/Rate(κ) typing the instruments carry
  - docs/design-notes/core-query-protocol.md # §2.7 the diachronic interpreter these instruments feed
supersedes: null
superseded_by: null
warrant: docs/brainstorms/velocity-and-clocks-fable-pass.md
---

# Velocity instruments — the diachronic measurement catalog, typed and gated

> Composed at **fable** (`claude-fable-5`, 2026-07-15, usage tokens) from the same session's
> rigorous pass (`velocity-and-clocks-fable-pass.md`, Parts X and V); the fable guard is
> satisfied in-session. This note states the decisions; derivations and refutations live in the
> pass. It makes the vector-field program **concrete**: the typing rules every velocity object
> obeys, the two instruments buildable **now** (measurement-class), and the R-gated catalog
> pinned precisely enough that each later graduation needs no new design. Ratification is a hand
> edit by the owner; `/graduate` refuses this note until `status: ratified`.

## 1. Purpose and scope

`edge-dynamics-vector-field.md` generated six `novel_objects`, all ungraded. The fable pass
graded them (several refuted-and-repaired). This note decides: **(§2.1)** the three typing
rules; **(§2.2)** the two measurement-class instruments and their v1 pins; **(§2.3)** the
R-gated catalog with repairs baked in. Out of scope: the clocks/geometry/drives frame (sibling
`dn-temporal-geometry`); the diachronic dreamer itself (DD-1 consumes these instruments; its
charter and its uuid-identity hard prerequisite are unchanged); anything touching a model, the
network, or back-action — every instrument here is deterministic, read-only, and
erasure-invariant.

## 2. Principles / decision

### 2.1 The typing rules (bind every object below and every future velocity instrument)

1. **X1 — the velocity 1-cochain is `Rate(κ)` on the common restriction.** `Δw` is defined only
   on edges present at both anchors (the bp-038 `_restrict` pattern lifted to weights); **edge
   birth and death are separate axes, never folded into a derivative**; the clock κ is declared
   and part of the type. An undeclared-clock velocity is ill-typed.
2. **X2 — exact one-step differences are measurement-class.** The R-ladder gates **fits**
   (splines, spectra, operators) — interpretations of the record; the record's own increments
   are measurements, like β₁ and ‖[d,τ]‖ (bp-038 shipped a two-snapshot instrument with no R1
   clearance, correctly). Consequence: §2.2's instruments need no sample-depth gate. Anything
   claiming a *trajectory* (a trend, a derivative-as-function, a forecast) stays R1-gated.
3. **X3 — dedup is type-directed.** `Inv` instruments may anchor on distinct-snapshot clocks;
   `Rate` instruments must not silently dedup — a plateau is data for a rate.

### 2.2 The two measurement-class instruments (buildable on ratification)

**(a) The harmonic-subspace rotation — the metric complement of ‖[d,τ]‖.** Between two
commit-anchored citation snapshots, restricted to common nodes: the **principal angles** between
`ker L₁(X_n|common)` and `ker L₁(X_{n+1}|common)`. It measures how the *thread structure
reorients* even when the thread *count* (β₁) and the severing count (‖[d,τ]‖) are unchanged —
TRA Result 4 (chain maps transport homology, not kernels) made measurable. Pins:

- **Substrate: `X_cite`** — embedder-independent, exact, deterministic (the A7 primary-signal
  rule: the citation complex is the invariant floor). A similarity-backbone variant is *named*
  (richer, weighted) but is INTERPRETED-class and interpreter-version-controlled per A7 —
  deferred (VI-c).
- **Type: `Inv`** (a subspace-geometry value on the two anchors' event sets; no clock division).
- **Home: extends `core/temporal_view.py`** — a `RotationReport` beside `CoherenceReport`, same
  two-anchor factory shape, no new store surface.
- **Falsifiers:** identical snapshots ⇒ all angles 0; β₁ = 0 at either anchor ⇒ empty report
  (honest seam, no fabricated geometry); the principal angles must agree with an independent
  SVD-based computation on the same bases; determinism run-to-run.

**(b) The alive/stale hole discriminator.** A hole (β₁ class) whose carrying cycle shows
sustained harmonic velocity is being *actively orbited* (unconverged, alive); one with
`P_harm(Δw) ≈ 0` is *abandoned structure*. This replaces the brainstorm's near-tautological
falsifier (pass V1) with a real claim type for the hole/THREAD lens family. Pins:

- **Substrate: the mirror-side weighted backbone** (Lane A — holes live there), so A7 binds:
  `Δw` is computed at a **fixed interpreter version** (genuine evolution = Δ(record) at fixed
  embedder); a version boundary inside the window voids the reading (emit nothing).
- **v1 is global:** the harmonic-velocity energy `‖P_harm(Δw)‖` (and its per-eigenspace split),
  using the built `hodge.py` projectors on the common restriction. **Per-hole localization
  joins when the THREAD lens (L-b) lands** — the localization machinery is L-b's carrying-cycle
  extraction, not re-derived here (VI-b).
- **Type: `Inv`** per window pair (an energy on the common restriction); a *rate* version would
  be `Rate(κ)` and is deliberately not v1.
- **Falsifiers:** β₁ = 0 ⇒ zero claims (honest seam); a synthetic pair with weights changed
  only on gradient directions ⇒ zero harmonic-velocity energy; orthogonality of the three
  components within tolerance on every evaluated pair.

### 2.3 The R-gated catalog (definitions pinned; graduate as each gate opens)

| object | the pinned form (repairs baked in) | gate |
|---|---|---|
| velocity covariance (V2) | eigenmodes are **POD, not Koopman** (the transport is order-upper-triangular ⇒ non-normal; the two differ exactly when supersession is active); legitimate as **DMD's spatial half**; market-beta split = the rank-1 case; standing hypothesis: **no compositional closure on `w`** (else anti-correlations are Aitchison artifacts, not substitution) | R1 |
| joint space×time spectrum (V3) | project onto **eigenSPACES, not eigenvectors** (degeneracy ⇒ determinism repair); "a thread that pulses" = the harmonic-subspace projection with a significant Lomb–Scargle peak | R2 |
| distance–frequency duality (V4) | **half a theorem**: dominant low-frequency mode ⇒ long-range correlation; the converse is refuted (delocalized ≠ low-frequency). Ship as the cheap two-sided measurement, never as an iff | VF-covar built |
| transverse stability (V5) | the real-part spectrum of the fitted evolution operator (Lyapunov/Floquet); the Hodge-complement reading is deleted (it was V1 restated) | R3 |
| the innovation residual (V6) | Kalman-innovations frame; by TRA R6 the residual is supported on injection events (conditional on estimator consistency); **provenance-decomposable by construction** — `r = r_owner + r_dreamer` from the event tags, no blind separation; the nested hierarchy: β-split (rank-1) ⊂ DMD (rank-k) ⊂ R4; birth/death events are structurally the unmodeled part | R3/R4; the **attribution design** rides DD-1's charter now |

### 2.4 What the instruments feed

The diachronic interpreter (CQ §2.7, DD-1) is the consumer: §2.2's pair gives its
corpus-structural tier exact, embedder-free diachronic signals **before** any R-rung opens, and
V6's provenance-decomposed innovation is the formal substrate for the demon-vs-source experiment
(`dn-temporal-geometry` §2.2). The lens contract binds unchanged: claims land INTERPRETED,
owner-gated promotion, zero back-action, the A7 discriminator required for any drift claim.

## 3. Consequences — what this note licenses (on ratification)

1. **ONE build plan now:** the measurement-class pair (§2.2) — extend `core/temporal_view.py`
   with the rotation report; a small `core/complex/`-consuming reader for the global
   alive/stale energy (exact home pinned at graduation; candidates: beside the hodge module's
   consumers or a thin `core/velocity_view.py`). Deterministic, no model, no store mutation;
   pytest + the §2.2 falsifiers as acceptance.
2. **The R-gated catalog** graduates per gate with zero new design (the pins in §2.3 are the
   design); each lands as its own small plan.
3. **DD-1's charter** inherits V6's attribution design and §2.2's signals as named inputs.
4. **The book** gains the velocity-instruments chapter debt (with the POD/Koopman and duality
   corrections — the refutations are part of the record).

## Parked decisions

| id | decision | default recorded | re-entry condition |
|---|---|---|---|
| VI-a | the Rate(κ) versions of §2.2 (per-clock rates rather than per-window energies) | Inv-only v1 | a consumer needs a rate; the clock is declared per X1 |
| VI-b | per-hole localization of the alive/stale discriminator | global energy v1 | the THREAD lens (L-b) lands (carrying-cycle extraction) |
| VI-c | the similarity-backbone (weighted) rotation variant | X_cite-only v1 (embedder-free floor) | an interpreter-version-controlled consumer wants the metric-rich variant (A7 machinery in place) |
| VI-d | the compositional-closure check as a standing assertion | stated hypothesis in V2's plan | VF-covar graduates (the check ships with it) |
| VI-e | V4's empirical form (which modes carry long-range correlation) | unmeasured | VF-covar built + R1 series |

## Cross-references

- `docs/brainstorms/velocity-and-clocks-fable-pass.md` — **the warrant** (X1–X3, V1–V6; grades,
  refutations, and the flagged externals: Schmid 2010, Rowley 2009, Kalman 1960, Aitchison 1986
  — verify before a book cites).
- `docs/brainstorms/edge-dynamics-vector-field.md` — the owner thread; the census
  (234 pairs/113 nodes) whose youth motivates the measurement-class-first sequencing.
- `docs/design-notes/edge-dynamics.md` §2.5 — the ladder + inversion; X2 is its sharpening
  (fits gated, measurements free), stated here because the ratified note is never edited.
- `docs/design-notes/temporal-retrieval-algebra.md` — R4 (what instrument (a) measures), R6
  (what V6 leans on), §2.5 A7 (the discriminator binding (b) and every drift claim).
- `docs/design-notes/temporal-geometry-and-drives.md` — the sibling: clocks/geometry/drives;
  consumes V6 for the demon-vs-source experiment.
- code: `core/temporal_view.py` (the extension home for (a)); `core/complex/hodge.py` (the
  projectors (b) consumes); `core/temporal/complex.py` (`X_cite`); `core/dreaming/interpreters.py`
  (the lens contract DD-1 inherits).
