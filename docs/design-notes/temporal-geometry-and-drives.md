---
type: design-note
id: dn-temporal-geometry
status: draft            # draft → ratified → superseded.  draft→ratified is an OWNER-ONLY hand edit.
implementation: design-only # nothing built; states the fable-formalized time-index, geometry, and drive results
created: 2026-07-15
updated: 2026-07-15
links:
  - docs/brainstorms/velocity-and-clocks-fable-pass.md # THE WARRANT — T1–T6 (+ X1–X3) with grades
  - docs/brainstorms/temporal-clocks-and-strata.md # the owner thread (all three capsules) this formalizes
  - docs/design-notes/temporal-retrieval-algebra.md # ratified; this note is its time-index/geometry extension home
  - docs/design-notes/capability-scope-algebra.md # T = clock+window, SLICE rule, Inv/Rate(κ) (drafted same day)
  - docs/design-notes/edge-dynamics.md # the R-ladder + inversion this note's gates inherit
  - docs/design-notes/magnetic-laplacian.md # rate-as-current → the magnetic operator (parked link, ML-*)
  - docs/findings/finding-0083.md # the §2.5 gloss erratum this note carries (promoted)
supersedes: null
superseded_by: null
warrant: docs/brainstorms/velocity-and-clocks-fable-pass.md
---

# Temporal geometry and the drives — clocks, curvature, and what keeps the corpus alive

> Composed at **fable** (`claude-fable-5`, 2026-07-15, usage tokens) from the same session's
> rigorous pass (`velocity-and-clocks-fable-pass.md`, Parts X and T); the brainstorm→design
> fable guard is satisfied in-session. This note **states** results; derivations, grades, and
> refutations live in the pass. It is the **extension home** for `dn-temporal-retrieval-algebra`
> (ratified, never edited — the same pattern by which TRA extended `dn-edge-dynamics`): the
> time-index formalization TRA's anchor question left open, the geometric layer above it, and
> the corrected energy picture. Ratification is a hand edit by the owner; `gate-guard` denies
> any agent attempt; `/graduate` refuses this note until `status: ratified`.

## 1. Purpose and scope

TRA formalized the temporal *operators* (`σ_*`/`σ^*`/`π_active`) but left the **time-index**
itself informal (what an anchor is; which clock a rate is measured against). The owner's
temporal-clocks thread (2026-07-15) supplied the missing frame; the fable pass formalized it.
This note decides:

1. **The time-index (§2.1):** the ledger is a causal set; proper time is exact; anchors are
   cuts; every instrument declares its clock.
2. **The corrected energy picture (§2.2):** two prime movers, one belief-injection channel —
   the finding-0083 erratum, in its sharpened form, plus heat death and the corpus-temperature
   formula.
3. **The velocity-conformal geometry (§2.3):** churn as a refractive index; geodesic retrieval;
   the first concrete instrument.
4. **The locally-clocked superconnection (§2.4):** defined, with its reduction theorem; the
   unification candidate.

**Out of scope:** the velocity *instrument catalog* (X1–X3, V1–V6 — the sibling note
`dn-velocity-instruments` licenses those builds); the scope type system (`dn-capability-scope`);
any TRA re-statement (its six results stand; only the §2.5 *gloss* is corrected, via
finding-0083). Every empirical program here keeps its data gate — this note makes the *design*
concrete, not the sample depth.

## 2. Principles / decision

### 2.1 The time-index: the ledger is a causal set, and proper time is exact here

- **The event trajectory is the causal order** (op-seq / per-store sequences — the Sz.-Nagy
  dilation space read as an index). A **clock** is a monotone coarsening of it; the hierarchy
  (global `N` ⪰ per-stratum `N_s`; `N` ⪰ commit ⪰ distinct-snapshot; wall-time exogenous) and
  the window/anchor machinery are as typed in `dn-capability-scope` §2.1 (T = clock + window).
- **Proper time = per-stratum event count, exactly.** Because each stratum's store is totally
  ordered, longest-chain length equals event count — the causal-set construction is an
  *identity* in this system, not an approximation. Cross-stratum durations (once a unified
  partial order is materialized, CS-a/CS-b) are longest chains between **cuts** (antichains);
  the commit SHA is today's consistent cut for repo-backed strata. `[pass T1]`
- **Every temporal instrument declares its clock and its invariance class** — `Inv` (depends
  only on the window's event set) or `Rate(κ)` (carries its clock in its type). Deduplication
  is type-directed: `Inv` may use distinct-snapshot; `Rate` must use the declared raw clock —
  a plateau is data for a rate. `[pass X1/X3; enforced by the dn-capability-scope build once
  ratified]`
- **The relativity reading, bounded:** relativity-of-simultaneity across strata is real
  (vector-clock form; no canonical cross-stratum "now" absent a cut); the SR/GR *metric* shell
  stays evocative only (preferred frame; no boost group; no wave equation — see §2.3's ẅ
  refutation).

### 2.2 The energy picture, corrected: two prime movers, one belief channel (finding-0083)

- **The erratum.** TRA §2.3 R6's theorem stands unweakened; its gloss "the owner is the only
  energy source" is corrected to: **the owner is the only source into the BELIEF view (via the
  promotion gate); the autonomous dreamer is a continuous second prime mover driving the
  INTERPRETED layer** — dreaming is necessary, not decorative. Sharpened form `[pass T4]`: a
  **one-way-coupled two-layer skew-product** — the dreamer drives upstairs (interpreted), the
  gate samples downstairs (belief), and in the belief dynamics the dreamer appears only as a
  modulation of the single promotion channel's rate and quality.
- **Heat death is a theorem, not a metaphor:** without injections the γ-contraction converges
  geometrically to a fixed point (Banach); `|ẇ| → 0`; the geometry of §2.3 goes flat. The
  system's own γ names its cooling rate.
- **The corpus temperature.** For stochastic injections through a contraction, steady-state
  variance solves the discrete Lyapunov equation; in the scalar caricature
  **σ² = q/(1 − γ²)** — injection variance over dissipation. This is the promised
  fluctuation-dissipation-flavored relation: a *quantitative* definition of "a healthy,
  fluctuating corpus," measurable once R1 series exist.
- **Demon vs source is an experiment now:** the dreamer is a genuine source iff its
  provenance-tagged innovation (`dn-velocity-instruments` §2.3 V6) stays positive over a
  dreamer-alone run on a frozen corpus; a demon's innovation decays as it exhausts deposited
  gradients. The run protocol is licensed by §3; executing it is owner-gated (live dreamer).

### 2.3 The velocity-conformal geometry: churn is a refractive index; retrieval distance is a geodesic

- **The source is the rate of CHANGE** `|ẇ|` (churn — revision/supersession included), typed
  `Rate(κ)`: **the geometry is clock-relative; declare κ** (v1: per-event `N_corpus`; wall-time
  the alternative for physical-tempo questions). v1 placement: node-aggregated
  `J(v) = Σ_{e∋v} |ẇ_e|`. `[pass T3]`
- **The potential auto-centers:** `Φ = L⁺J` annihilates the uniform part (`L⁺𝟙 = 0`) — a global
  rate change is pure gauge; only activity *contrast* curves. The owner's "uniform rate is
  flat" is a property of the built operator, no construction needed.
- **Geodesic retrieval (the owner's closing question, pass T6).** Cosine is the **local
  metric**, not the distance (`1 − cos` fails the triangle inequality; `arccos` is the
  spherical geodesic — even flat cosine retrieval uses the chord of a geodesic). The honest
  distance is the **`K(β)` family at finite β** (TRA A1) — the smeared geodesic that stays in
  the kernel cone (the β* theorem excludes the brittle β→∞ pure-geodesic limit). The activity
  potential **conformally deforms** that geometry: geodesics bend through churn regions by
  Fermat's principle — the corpus's refractive index is `Φ`. Coherence check: **`L⁺` appears
  twice** (it solves the potential AND is the β→0 metric's Green's function) — the operator
  that bends the geometry measures distance in it.
- **The first instrument:** activity-for-density substitution in the diffusion-maps
  α-normalization — `K_J = K/(J(x)J(y))^α` — with α=0 recovering the undeformed geometry, so
  the deformation is a *dialed hypothesis* (the attract/repel sign and the clock coupling
  `f(Φ)` stay empirical). Gated on the J field (R1).
- **Refuted, and staying refuted until an equation exists:** the `ẅ`/radiation reading has no
  formal home — no metric signature, no finite propagation speed, no wave equation. `ẇ` sources
  a quasi-static deformation per window; "corpus gravitational waves" is vocabulary.
- **Distances are slice-anchored:** a distance is `Inv` relative to a cut; cross-anchor
  comparison is a `σ_*` transport question, never a subtraction of numbers from different
  slices.

### 2.4 The locally-clocked superconnection, and the one-curvature candidate

- **Defined `[pass T2]`:** in the version bundle, a **clock field** `n : V → ℕ` advances each
  note by its own step count; it is **admissible iff its target is a consistent cut** (the
  SLICE rule as an admissibility condition). The locally-clocked transport `τ(n)` carries edges
  onto the target cut; **curvature = holonomy** of composing sheared transports around a loop
  crossing regions of different clock rate.
- **Reduction theorem:** constant `n ≡ 1` recovers exactly the built two-snapshot `[d,τ]` —
  the generalization is conservative. **Gauge fact:** the uniform part of a clock field sources
  nothing; only contrast can produce holonomy.
- **The unification candidate `[pass T5, SKETCH]`:** let Φ conformally weight the citation
  coboundary (`d_Φ = e^{−Φ} d e^{Φ}`) and form `𝔸_Φ = d_Φ + τ`: its curvature carries both the
  severing obstruction (recovering ‖[d,τ]‖ at constant Φ) and the churn–transport coupling.
  One object, two faces — *related, never conflated* with static Forman curvature.
- **Honestly data-gated:** version chains are almost all length ≤ 1 today; the shear has
  nothing to shear. The full gauge theory and the T5 proof re-enter on per-note version depth.

## 3. Consequences — what this note licenses (on ratification)

1. **The finding-0083 erratum is formally lodged** — this note is the correction's home; the
   ratified TRA text is untouched; any future TRA supersession applies it from the warrant.
2. **The clock-declaration obligation** binds every future temporal instrument (κ + `Inv`/`Rate`
   in its plan §7 acceptance); the `dn-capability-scope` build enforces it structurally.
3. **The J/Φ diagnostic** (compute `J`, `Φ = L⁺J`, report top-contrast regions; the α-deformed
   diffusion as its retrieval-facing form) — one small plan, **gated on R1** (the J field needs
   series). Definitions are pinned; graduation at gate-open needs no new design.
4. **The dreamer-alone experiment protocol** (demon-vs-source, §2.2) — an eval-harness item;
   the *run* is owner-gated.
5. **CQ-mode1b is re-warranted** as the intrinsic retrieval geometry (§2.3); its gates are
   unchanged (a ranking customer + eval set).
6. **The book** gains the chapter debt: clocks/causal set, the conformal geometry, the drives.

## Parked decisions

| id | decision | default recorded | re-entry condition |
|---|---|---|---|
| TG-a | T2's full gauge theory (clock-field equivalence; holonomy group; diamonds) | definition + reduction banked; SKETCH beyond | per-note version depth (chains ≫ 1) |
| TG-b | T5's proof (𝔸_Φ as THE unifying curvature) | candidate named; SKETCH | TG-a + the J field exists |
| TG-c | the coupling `f(Φ)` and the attract/repel sign | posited/measured, no principle selects | the J/Φ diagnostic runs on a grown corpus (R1) |
| TG-d | which order of change sources geometry (`ẇ` vs `ẅ`) | `ẇ` (induction regime); `ẅ` refuted absent a wave equation | someone exhibits a corpus wave equation (none expected) |
| TG-e | a continuum / hydrodynamic limit of the discrete geometry | discrete only; kernel-smoothing gives fields without a limit | corpus density supports honest coarse-graining |
| TG-f | the magnetic Laplacian as the rate-as-current operator | noted (ML-* link); not adopted | ML-a's own gates |

## Cross-references

- `docs/brainstorms/velocity-and-clocks-fable-pass.md` — **the warrant**: grades, derivations,
  refutations (X1–X3, T1–T6), and the externals flagged `[FROM MEMORY — verify]` (BLMS 1987;
  Coifman–Lafon 2006; Kalman 1960; + the CQ-scope pass batch) — verify before a book cites.
- `docs/brainstorms/temporal-clocks-and-strata.md` — the owner thread (clock thesis; curvature
  progression density→addition→CHANGE; dreaming-is-necessary).
- `docs/design-notes/temporal-retrieval-algebra.md` — ratified; R5/R6 (dilation, γ-contraction)
  are the load-bearing inputs to §2.2; §2.6 β* to §2.3. This note extends, never edits.
- `docs/design-notes/capability-scope-algebra.md` — T = clock+window, SLICE, `Inv`/`Rate(κ)`
  (the typing §2.1 consumes); drafted the same session.
- `docs/design-notes/velocity-instruments.md` — the sibling note: ẇ's typing (X1) and the
  instrument catalog (V1–V6), incl. V6's provenance-decomposed innovation that §2.2's
  experiment consumes.
- `docs/findings/finding-0083.md` — the promoted erratum warrant.
- code: `core/temporal/superconnection.py` (`[d,τ]` — §2.4's reduction target);
  `core/complex/laplacian.py`/`hodge.py` (`L⁺`, the projectors); `core/stores/versions.py` +
  `ops/lifecycle/runs.py` (the per-store total orders behind §2.1's exactness).
