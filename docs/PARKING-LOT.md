# PARKING-LOT — the centralized parked-decision dependency registry

**What this is.** One place to see every *parked* decision, its *home* (the note/section it was
parked in), its *status*, what it *depends on*, and its *re-entry trigger* — so following a chain of
"this waits on that, which waits on the other" no longer means grepping lettered sections across a dozen
notes. Orchestrator-maintained (single-writer, like `docs/PROGRESS.md`).

**Maintenance discipline (binding).** Update this file whenever a decision is **parked** (add a row),
**unparked / implemented** (flip status, keep the row — the history is the value), or **its dependency
changes**. Do it at every `/triage` and at every graduation that touches a parked item. Each row's
`Home` is the authoritative source; this registry is the *index + the edges*, never a replacement for the
note's own reasoning.

**Can Ouroboros answer this instead? Not yet — and the gap is instructive.** bp-035's `ReferenceView`
queries the reference graph at **document grain** (`note-A → note-B`). Parked items live *below* that
grain (a *row* inside a note) and their dependencies are *prose* ("re-entry = TA-b's gate"), which the
sensor does **not** mint as edges. So this hand-maintained registry is **v0**. **v1** is to make parked
decisions *first-class typed entities* with minted `depends_on` edges — then a `DecisionView` (the next
resolution down from `ReferenceView`) answers "what does ML-a wait on?" live. v1 is a real graduation on
the reference/query arc; this file is its seed (the schema below is deliberately edge-first so it ports).

**Status legend.** `parked` (waiting on a trigger) · `active` (being worked) · `ready` (trigger met,
graduatable) · `built` (implemented) · `resolved` (a decision, settled — no build) · `open-owner`
(awaits an owner ruling) · `superseded`.

**Coverage.** SEEDED (2026-07-15) with the **query / edge-dynamics / magnetic / reference cluster**.
**SWEPT 2026-07-21 (session-39):** the **dreamer** track (SD-*, bp-079..082 BUILT), **inner/outer-core**
(ring, RATIFIED), **fiber-geometry** (FG-*, RATIFIED), **agentic-loop** (AL-*/PD-loop, RATIFIED), and the
**sensing/loop/curvature/grammar** cluster — see the session-39 sections below the seed cluster. Still
to harvest (`⋯`): older effectors/Track G rows, voice, secrets. Other clusters are swept incrementally
at `/triage`.

---

## Registry

`id` uses the note's native label where one exists (ML-a, TA-b, PD-c…); orchestrator-assigned ids
(CQ-*, DD-*, VF-*, R*) are marked. `→ X` in **Depends on** is another row's id; **(ext)** is a
non-decision condition (data accretion, an owner ruling, the Fable cap).

### Algebra — `core/temporal` / `dn-temporal-retrieval-algebra`
| id | item | home | status | depends on | re-entry / trigger |
|---|---|---|---|---|---|
| TA-d | `X_cite` module home = `core/temporal/` | TRA parked | **built** | — | (done: bp-032/033) |
| A7 | signal-vs-noise (apophenia) discriminator | TRA §2.5 | parked | — | any drift/dynamics lens ships → it is a *required component*, not optional |
| A8 | β\* (kernel-representability loss point) | TRA §2.6 | **resolved** | — | (theorem; computable, bp-026) |
| TA-a | weighted vs combinatorial inner products (the magnetic `L^{(q)}` upgrade) | TRA parked (= PD-b) | parked | → PD-b | the metric-coherence tier (Result 4) is built, OR PD-b's 2nd customer is proposed |
| TA-b | the `(β,z)` z-resolution dial | TRA parked | parked | (ext) a retrieval eval set | an eval set gives z a falsifier |
| TA-c | homotopy-coherent (diamond) superconnection `τ_k` | TRA parked | parked | → MAG-census | measured fork/merge **diamond frequency** warrants the rigor |
| CQ-wire | wire `core/temporal` **single-snapshot** (X_cite β₁ threads) into a live read surface = `TemporalView` | CQ §3 / TRA | **built** (bp-037 sealed `1a7be36`, 2026-07-15; live β₁=24 @ HEAD) | → TA-d (built) | (done) |
| CQ-wire-2 | wire `core/temporal` **two-snapshot** (`‖[d,τ]‖` citation-coherence, `σ_*`, poset `δ_D²=0`) into `TemporalView` | CQ §3 / TRA | **built** (bp-038 sealed, 2026-07-15; live ‖[d,τ]‖=0 flat 3797f8b→177b7fd) | → CQ-wire (bp-037, built) | (done). σ = restrict-to-common (§3 Q1). finding-0082 = VersionStore enumerator gap (poset scoped to corpus nodes). **`core/temporal` FULLY WIRED — "complete the algebra" DONE** |

### Query protocol — `dn-core-query-protocol`
| id | item | home | status | depends on | re-entry / trigger |
|---|---|---|---|---|---|
| CQ-ref | the reference read surface (`ReferenceView`, Mode 1) | CQ §2.3/§3.2 | **built** | — | (done: bp-035) |
| CQ-selfgrade | self-grading grep-oracle | CQ §2.6 | **built** | → CQ-ref | (done: bp-035 Item 3) |
| CQ-align | the alignment instrument (project `K_sem` onto the structural spectral manifold) | CQ §2.6 | parked | → CQ-ref, (ext) embedding Gram | the §2.6 second measurable is wanted |
| CQ-twin | build-time repo-derived reference twin | CQ §2.4 | **ready** | — (owner ruled YES) | graduate when the build-plane bookkeeping need bites (findings 0059/0061) |
| CQ-scope | **the capability-scope type system (the UNIFIED QUERY LANGUAGE)** — all Views as instances of one bounded-lattice scope algebra | CQ §2.1 | ✅ **BUILT — `bp-039` COMPLETE** (ratified `3f5591d`, graduated + built same session 2026-07-15; 5-leg gate green, pytest 1177) | — (done; follow-ons parked below) | **`core/scope.py` SHIPPED** — `Scope=(Σ,E,T,A)` lattice (meet/join/⊑), `WorldReach` NONE-floor (reconciled the note's `NONE<SENSING` vs code's `ReversibilityClass`, bridge ops-side), partial clock T-meet (raises on no common clock), firewall ideals, SLICE rule, `req()` as a `SCOPE` DECLARATION on all five Views (bit-identical reads held), Inv/Rate markers. finding-0084 (spec-fidelity) resolved. Parked follow-ons: `factory.grant` wiring (behavior change), N materialization (CS-a), sensor write-dual (CS-c), ObservedView/DreamsView scope |
| CQ-mode1b | Mode-1b soft diffusion + the `K_struct ⊙ K_sem` hybrid | CQ §2.2; **re-warranted** `velocity-and-clocks-fable-pass` T6 | parked (T6, owner coda 2026-07-15: this is the INTRINSIC retrieval geometry — cosine is only the local metric; K(β) at finite β = the honest geodesic; the T3 J-weighted α-deformation extends it) | → CQ-ref, (ext) kernel machinery | a ranking customer + eval set (unchanged) |

### Diachronic dreamer — `dn-core-query-protocol` §2.7 / Lane B
| id | item | home | status | depends on | re-entry / trigger |
|---|---|---|---|---|---|
| DD-1 | **diachronic interpreter — corpus-structural tier** (over `X_cite`, mirror-safe) | CQ §2.7 | **ready** | → TA-d (built), → A7, → CQ-wire | owner-directed (roadmap #3); the lens contract + A7 discriminator |
| DD-2 | diachronic interpreter — observed-plane WEAVING tier (= Track D charter, = Lane B) | CQ §2.7 / ED §2.6 | parked | → SS-substrate, (ext) sample depth, → TrackD | all three Lane-B gates (ED §2.6) |
| TrackD | the weaving-consumer charter (a design pass) | ED §2.6 | parked | → SS-substrate | its own design pass is drafted + ratified |

### Edge dynamics — `dn-edge-dynamics` (Lane A degree-1 lift + the R-ladder)
| id | item | home | status | depends on | re-entry / trigger |
|---|---|---|---|---|---|
| L-a | `hodge.py` degree-1 lift (∂₁/∂₂, L₁, Hodge split, harmonic + L₁ eigenbasis) | ED §3.1 | **built** | — | (hodge.py exists; reused by `core/temporal`) |
| L-b | the `THREAD` harmonic lens | ED §3.1 | parked? | → L-a | Lane A graduation (verify built-state at /triage) |
| L-c | degree-1 invariants in `temporal.py` snapshots | ED §3.1 | parked? | → L-a | Lane A graduation (verify) |
| PD-a | 2-simplices beyond 3-cliques / **the sheaf-Laplacian** (= FG-a) | ED §4 · dn-fiber-geometry FG-5 | parked | → G-A survey (M1/M2) | **CUSTOMER APPEARED 2026-07-21** (three-fiber bundle); re-entry SHARPENED to FG-5's 3 measured conditions (M1 skeleton overlap + non-degenerate class populations · M2 nonzero cut-stable cross-class structure · a consumer the independent per-class runs can't answer). A sheaf w/ coord-projection restrictions is **block-diagonal = zero coupling content** — stays parked until measured; default = per-class runs + scalar cross-stats |
| PD-b | weighted L₁ (strength inner products) | ED §4 | parked | — | harmonic reps too delocalized to narrate, OR the metric tier (→ TA-a), OR **FG-g** (Hodge readings consumed quantitatively for transport attribution — dn-fiber-geometry §2.1-3 named it a customer) |
| PD-c | **Ollivier directed-walk Ricci** | ED §4 / MAG §2.6 | parked | → Forman-vs-churn reads (M5/M7) | **CUSTOMER-CANDIDATE APPEARED 2026-07-21** (clock-curvature metric curvature; dn-fiber-geometry registers it) — but the ladder is honored: **Forman (built) runs FIRST** (M5/M7); Ollivier builds only if transport-contraction is demonstrably needed after those reads |
| PD-e | first potential V for gradient-flow fits (Dirichlet default) | ED §4 | parked | → R4 | R4 entry |
| PD-f | THREAD claim narration weighting | ED §4 | parked | → L-b | dreamer-quality evidence it needs distinct adjudication |
| R1 | splines/GP per edge series → measured momentum `p` (the velocity 1-cochain ẇ) | ED §2.5 | parked | (ext) sample depth | enough points per series for honest CV |
| R2 | Lomb–Scargle spectra (temporal Fourier, irregular sampling) | ED §2.5 | parked | → R1 | R1 residuals warrant it |
| R3 | Koopman/DMD — the evolution operator (predict G_{t+1}; coherent modes) | ED §2.5 | parked | → R2 | many snapshots; R2 stationarity evidence |
| R4 | learned action (gradient-flow ẇ≈−∇V; the "Hamiltonian of the graph") | ED §2.5 | parked | → R3 | the ladder below is green + deep |
| PD-d | per-rung sample thresholds | ED §4 | parked | — | each rung's entry gate (its own owner-visible act) |

### Magnetic Laplacian — `dn-magnetic-laplacian`
| id | item | home | status | depends on | re-entry / trigger |
|---|---|---|---|---|---|
| MAG-census | arrow-aware **combinatorial** census (SCC/directed-cycles, unbalanced diamonds, retro-citations) | MAG §3 item 2 | **ran (one-off 2026-07-15)** | — (licensed, rides Thread-C) | permanent-lens deferred → DD-1, or a cleaner per-commit census |
| ML-a | the magnetic **operator** build `L^{(q)}` | MAG ML-a | parked (3 gates; ANY one) | gate(i) → TA-b **and** → ML-c · gate(ii) → MAG-census insufficient · gate(iii) → MAG-census shows cycles/diamonds COMMON | **census ran → gate(iii) NOT met** (cycles inflated, retro 8.5% modest) |
| ML-b | the **spectral** census (eigenvector localization; soft cycles) | MAG ML-b | parked | → ML-a gate(ii) | the combinatorial lens proves insufficient |
| ML-c | the phase→score dictionary (directed-diffusion ranking) | MAG ML-c | parked | (ext) a retrieval eval set (= TA-b) | an eval set exists |
| ML-d | magnetic Weitzenböck / flux-aware Forman | MAG ML-d | parked | (ext) a curvature customer + Q1 obstruction addressed | **the three-directed-fibers reading was DECLINED as a customer 2026-07-21** (dn-fiber-geometry FG-5: non-commutativity is monoid-level — no structure group, no fiber space) — park stands, NO customer registered |
| MAG-own2 | dream-narration vocabulary for the arrow-aware census (= **oq-0021**) | MAG owner-dec-2 | ✅ **RESOLVED 2026-07-21** | — | owner ratified **ADMIT** via `dn-synchronic-diachronic-dreamer` §2.9 (bless `44bbeec`); BUILT as bp-080's census lens (records-not-causes; F-SD9 battery); `dn-fiber-geometry` sharpens it to a positive verb-licensing table |
| MAG-own3 | covering-only `supersedes:` as a checked A6 invariant | MAG owner-dec-3 | **open-owner** | — | owner ruling (rec: adopt; near-zero cost; keeps the Hasse DAG triangle-free) |

### Vector-field candidates — `docs/brainstorms/edge-dynamics-vector-field.md` (~mine, fable-grade)
| id | item | home | status | depends on | re-entry / trigger |
|---|---|---|---|---|---|
| VF-covar | velocity-covariance (the corrected Q1: `cos(ẇ_i,ẇ_j)` matrix eigenmodes; market-beta split) | brainstorm; **formalized** `velocity-and-clocks-fable-pass` V2 | parked (formalized 2026-07-15: eigenmodes = **POD, not Koopman** — non-normal transport; legitimate as DMD's spatial half; compositional-closure caveat pinned) | → R1 | R1 series exist |
| VF-velhodge | velocity Hodge decomposition | brainstorm; **formalized** pass V1; **note DRAFTED** `dn-velocity-instruments` §2.2 | **note-drafted** (the two measurement-class instruments — harmonic-subspace rotation on X_cite + alive/stale hole discriminator — are the note's §3.1 licensed plan; pins: Inv-typed, A7-bound, honest seams, falsifiers named) | → owner ratifies `dn-velocity-instruments` | ratification → /graduate the pair; R1 (series half, unchanged) |
| VF-jointspec | joint space×time spectrum (L₁ modes × Lomb–Scargle) | brainstorm; **formalized** pass V3 | parked (formalized: track eigenSPACE projections, not eigenvectors — determinism repair) | → R2, → R3 | R2/R3 land |
| VF-duality | distant-correlation ⟺ low-graph-frequency | brainstorm; **formalized** pass V4 | parked (formalized: HALF a theorem — forward holds, converse REFUTED; the cheap test stands) | → VF-covar, → L-a | VF-covar built |
| VF-residual | prediction-residual = live creative signal | brainstorm; **formalized** pass V6 | parked (formalized: Kalman innovations; by TRA R6 supported on injection events; **provenance-decomposable r_owner + r_dreamer by construction** — demon-vs-source now a specified experiment; attribution design rides DD-1's charter) | → R3, → R4 | the evolution operator is fit |

### Evaluation harness — `dn-evaluation-harness` (ratified 2026-07-15; §3 E1–E8 + parked EH-a…EH-k)
| id | item | home | status | depends on | re-entry / trigger |
|---|---|---|---|---|---|
| EH-milestone1 | the first overnight dual-dreamer A/B (single-config) | note §2.9/§3 | **graduated 2026-07-15** → bp-042 (E1) + bp-043 (E2) + bp-044 (E4) + bp-045 (E5(A2)), all `proposed` | → owner blesses the 4 plans `proposed→ready` | owner bless → /build (order bp-042→bp-045→bp-043→bp-044) |
| EH-E3a | sweep engine, propose-mode (σ-grid, admissibility, `TuningProposal`) | note §2.6 / §3 E3a | parked — deferred tranche | → E1 built (pin against the store's *built* surface) | bp-042 lands → graduate E3a |
| EH-E3b | bounded auto-apply (per-lever `autonomy`, derived `SAFE_LEVERS`, cooldowns, rollback) | note §2.6 / §3 E3b | parked — deferred tranche | → E3a propose-mode has produced owner-blessed sets | trust the loop before arming it |
| EH-E5rest | CoherenceReport replay-pair caller + adjudicator confidence panel + effector_drift report-only axis | note §3 E5 (rows 8/11/7) | parked — deferred tranche (the report enrichments; E5(A2) already graduated as bp-045) | → E1 + E4 built | bp-042 + bp-044 land → graduate E5-rest |
| EH-E6 | review REPL + probes (verdict store already built) | note §3 E6 / Track L L2 | parked — deferred tranche | → E2 (claims to judge) | bp-043 lands + owner wants the L2 loop |
| EH-E7 | longitudinal metrics + F4 + Θ-calibration; `tests/longitudinal/` tenant | note §3 E7 / Track L L5 | parked — deferred tranche | → weeks of E2/E6 data; EH-e (4 wks) | verdicts accrue → the `precision@review` upgrade (EH-c) |
| EH-E8 | capability batteries (instance #1 first; P1 codegraph its own plan) | note §3 E8 / capability annex §5 | parked — deferred tranche | → E1 + P1–P4 prereqs; EH-h (RAG corpus) | E1 lands + battery prereqs met |
| EH-c | headline objective `f9_composite` → `precision@review` | note §2.6 / parked EH-c | parked | → L2 verdict count ≥ floor (set at E7 graduation) | E7 sets the floor, verdicts cross it |
| EH-e | Θ auto-calibration (propose from p99 healthy variance) | note parked EH-e | parked | → 4 weeks of longitudinal curves (E7) | 4 wks accrue → harness proposes, owner blesses in baseline.json |
| bp-041 | wire dream_v2 LIVE, replacing Phase-7 | resume-brief / PROGRESS | **reserved** (not authored) | → owner sees the first A/B report | milestone-1 built + run + owner reads the σ/A2 report |
| bp-040 | `sweep.dreamer-sigma-ab` (the σ-grid A/B) | bp-040 (subsumed) | parked — re-derives under E3a, never standalone | → E3a (sweep engine) | E3a graduates → this is its first sweep spec |
| (align) | dn-velocity-instruments RotationReport + alive/stale discriminator = catalog rows 9–10 | `dn-velocity-instruments` §3.1 | parked — align with E5/catalog at graduation | → ratified (it is) + E5-rest graduation | fold into the E5-rest / catalog graduation |
| (align) | dn-temporal-geometry demon-vs-source = catalog row 12 | `dn-temporal-geometry` §2.2 | parked — R3/R4-gated | → R3/R4 series + owner gate | the harness hosts the protocol; the *run* is owner-gated |

### Dreamer — `dn-synchronic-diachronic-dreamer` (RATIFIED 2026-07-20; bp-079..082 BUILT + sealed 2026-07-21)
| id | item | home | status | depends on | re-entry / trigger |
|---|---|---|---|---|---|
| bp-079 | D-0 DreamCharter + materialization boundary | dreamer §2.2/§2.4 | **built** (01e006b) | — | (done) |
| bp-080 | D-1 arrow-read census + panel lens | dreamer §2.8/§2.9 | **built** (cdedfab) | → bp-079 | (done; census EMPTY on live corpus — fixtures carry) |
| bp-081 | H-0+H-1 HYPOTHETICAL stratum + staging + overlay + sweep | dreamer §2.6 | **built** (8be3c98) | — | (done; BUILT DARK) |
| bp-082 | H-2 influence (integer+smooth) + conditioning law | dreamer §2.7 | **built** (3979291) | → bp-079,bp-081 | (done; BUILT DARK) |
| SD-a | diachronic EXECUTION (interval-window dispatches) | dreamer §2.8 | parked | (ext) graph-at-a-past-cut graduates | `graph-at-a-past-cut` family graduates **AND** D-1 sealed (finding-0126 RESOLVED the stale "G3 materializes" — the substrate GC-3 is already built) |
| SD-b | past-cut dispatch build (ANCHORED→RETRO/ARCHIVAL) | dreamer §2.1/§2.5 | parked | → SD-a seam | `graph-at-a-past-cut` graduates its instrument note (HistoricalRowSource adapter) |
| SD-c | persistent/incremental σ-graph (delta-log adjacency) | dreamer §2.5 | parked | (ext) cost | a measured projection/cut-sweep cost crosses a stated budget on the grown corpus |
| SD-d | expired staging: tombstone vs hard delete | dreamer §2.6 | parked | (ext) growth | staging growth is measured material (owner call — hard delete admissible-by-design for this one store) |
| SD-e | edit/removal overlays ("what if this were gone") | dreamer §2.7 | parked | — | a real removal counterfactual needs it (its own pass — opposite one-sided law) |
| SD-f | spectral influence (eigenvector localization over the overlay) | dreamer §2.7 | parked | → P8(sknetwork) | P8 (inner-outer P7) resolves AND F-SD7a shows the perturbation family needs the finer instrument |
| SD-g | structural (v3) closed-evaluator enforcement | dreamer §2.4 | parked | → inner-outer P1 | F-SD4b fires, or "provably effect-free" needed (= inner-outer-core P1) |
| SD-h | per-dispatch σ/resolution defaults | dreamer §2 | parked | → FB-3 | the σ-fiber tier gate validates tiers |
| finding-0130 | staging-sweep scheduler WIRING | bp-081 Item 10 | parked (builder-lane) | (ext) owner turns HYPOTHETICAL live | a future "make the subspace live" plan wires `run_sweep` as a pinned trough job (Track-G build-dark pattern). ⚑ the WHOLE H-family is flag-off/not-wired |

### Inner/outer core — `dn-inner-outer-core` (RATIFIED 2026-07-21)
| id | item | home | status | depends on | re-entry / trigger |
|---|---|---|---|---|---|
| M0 | the born-green ring (`core/rings.py` + `tests/unit/test_inner_ring.py`) | note §2.4/§3 | ✅ **ready to /graduate** | — | ratified → /graduate (recompute the fixed point at HEAD; Appendix A is expectation not authority; F5) |
| S1 | temporal-math↔persistence splits (+7 → 36-member ring) | note §2.6b | ✅ **ready to /graduate** | → M0 | ratified (owner fired P8) → /graduate (bp-065/sigma_star shape; DRY-audit integrator/recursion_ops persistence) |
| P1 | v3 effect-free predicate (base further ∖ sqlite3) | note P1 | parked | — | a consumer needs "inner ⇒ effect-free" (F1 fires) OR hypothetical-subspace wants provably-effect-free isolation (= SD-g) |
| P2 | two-sided layout (`core/machinery/` for outer) | note P2 | parked | → M2 | recurring misplacement/confusion in review during M2 |
| P7 | sknetwork/ripser dep decision (spectral/topology → inner) | note P7 | parked | — | the subspace/instrument program needs spectral math inside the ring (= SD-f/FG-h chain) |
| M2/M3 | physical migration waves (K1/K2/K3) → the flip | note §2.7 | parked | → M0 + per-wave stability | begins after ratify + per-wave stability (≥2 sealed plans, no open inversion); M3 flip gated on outer ratchet **0** |
| (P3–P6, P8, P9) | computation-extract · headers · TYPE_CHECKING exempt · librarian name · (P8 temporal RESOLVED→S1) · P9 store-typed vocab (chat_events/dreams_view) | note P3–P9 | parked / P8 resolved | — | per each note row (2nd consumer / reviewer friction / own pass) |

### Fiber geometry — `dn-fiber-geometry` (RATIFIED 2026-07-21)
| id | item | home | status | depends on | re-entry / trigger |
|---|---|---|---|---|---|
| G-A | the read-only **M1–M10 measure-first survey** | note §2.6/§3 | ✅ **ready to /graduate** | — | ratified → /graduate (eval-side, read-only; **nulls are results**; several rows expected null on thin C) — the DATA the other FG parks hang from |
| G-C | verb-licensing narration check (positive F-SD9) | note §3 | ✅ **ready to /graduate** | → bp-080 lens | rider-sized; after the census lens surface exists |
| G-B | the mismatch lens (S↔C / S↔F densities) | note §3 | parked (conditional) | → G-A M2 | G-A's M2 shows signal |
| FG-a | sheaf/bundle Laplacian | note §2.5 | parked | → G-A M1/M2 | (= PD-a row above — 3 measured conditions) |
| FG-b | hop-priced (−log-product) functional beside σ* | note §2.4 | parked | → M8 (=oq-0024) | M8 shows material divergence AND product-optimal predicts endorsed chains better |
| FG-d | CS-x: the E coordinate SET → LANGUAGE (fiber-chain grammar) | note §2.3 / `fiber-chain-grammar.md` | parked | — | the **explainable-retrieval (generate) instrument** graduates as the consumer (E stays a set until then) |
| FG-e | learned grammar (route 3) | note §2.3 | parked | (ext) endorsed-chain corpus | corpus at validating size + held-out arm in place |
| FG-f | CN-4 magnitude calibration by volatility exposure (clock-curvature) | note §2.4 | parked | → M6/M7 | M6/M7 land AND the owner performs the CN-4 owner-visible lever act (magnitudes shipped 0 = inert) |
| FG-h | the horizon/decoupling instrument (clock-curvature) | note §2.4 | parked | → FG-b, M7 | FG-b resolved for the product functional AND M7 shows the phase transition |
| finding-0140 | the S/F/D/C move alphabet | note §2.0 | ✅ **PROMOTED** (ratified) | — | (done) |

### Agentic loop — `dn-agentic-loop` (RATIFIED 2026-07-21)
| id | item | home | status | depends on | re-entry / trigger |
|---|---|---|---|---|---|
| AL-1 | the two (Σ,E,T,A) actor-profile constructors + the zone-ideal test (gap G-D) | note §2.3/§3 | ✅ **ready to /graduate** | — | ratified → /graduate (~1 small session; the zone exclusion becomes a ratchet) |
| AL-2 | read-only C-coverage + gap-instrument baselines | note §2.8/§3 | ✅ **ready to /graduate** | — | ratified → /graduate (read-only; generates the gap-signal data PD-3 needs) |
| AL-3 | exhaust⊂dialogue refinement + default-grant-exclusion test + the `origin(e)` derived view | note §2.4b/§3 | ✅ **ready to /graduate** | — | ratified → /graduate (the exhaust stratum as a refinement; provenance spine as a VIEW not a store; F-AL6/F-AL7) |
| PD-1 | the self-authored provenance class + `w(a_self)` weight | note §2.4 / `dn-authorship-distance-axis` | parked (open-owner) | → authorship-axis gate | the authorship-distance-axis note's class is defined + owner-gated (the exhaust trust-weight; the one missing entry in the trust ledger) |
| PD-3 | the curiosity / gap-steering heuristic (self-steering attention) | note §2.5 | parked | → R&D flag, → M-6 | owner wires the R&D flag (`dream_rnd`) **AND** gap-instrument baselines (AL-2/M-6) exist |
| PD-7 | "informed-by" return edges (graph-grain loop reading) | note §2.4b | parked | — | loop-reading at graph grain demonstrated necessary AND clears the apophenia bar (witnessed deterministic orientation record only) |
| PD-8 | producer-parameterized refinement / edge-of-edges endpoint kind | note §2.4b | parked | — | a grant must include agent A's exhaust while excluding B's, OR a consumer needs created-edge row grain |
| finding-0141 | internal probe loop built-not-wired (was "LIVE") | note §2.2/§2.6 G-A | ✅ **RESOLVED** (ratified) | — | (record fixed; the *gap* G-A persists — internal loop goes live when owner wires the R&D flag) |

### Sensing / reference — session-39 brainstorms (pre-design; measure-first)
| id | item | home | status | depends on | re-entry / trigger |
|---|---|---|---|---|---|
| ref-sensor | the reference SENSOR (keep X_cite / F fresh; passive, `ops/`) | `reference-integrator.md` | brainstorm | (ext) staleness gap | **MEASURE the staleness gap first** (refs-in-tree vs latest-commit edge set — G-F says 893,991 rows vs ~hundreds current); then a small pass. Extractor EXISTS (code_sensor + note-ingest) — schedule+reconcile, DON'T reinvent |
| coverage | bare-prose `docs/…` path-ref extraction coverage | `reference-integrator.md` | brainstorm | — | verify the extractor picks up prose paths (not just front-matter/wikilink/inline) — fix BEFORE the keeper |
| active/passive | active vs passive sensing taxonomy | `reference-integrator.md` / `agent-causal-loop.md` | **resolved (no new axis)** | — | reconciled to sensing/acting hands + observed stratum (dn-agentic-loop) — no work |

### External conditions (not decisions — the roots the chains hang from)
- **(ext) sample depth** — data accretion over commits; the root of the whole R-ladder + every VF-*.
  The corpus is YOUNG (2026-07-15 census: 234 distinct doc→doc pairs / 113 nodes) — likely below R1's
  honest-CV threshold today.
- **(ext) a retrieval eval set** — roots TA-b, ML-c, CQ-mode1b. Note CQ-selfgrade (bp-035's oracle)
  *bootstraps* a structural eval set; a *directed-ranking* eval set is a further step.
- **(ext) Fable weekly cap** — resets **Jul 17 8pm ET** (currently 100% used). **Largely
  discharged early**: CQ-scope AND every VF-* formalization AND the temporal-clocks fable items
  (T1 causal-set, T2 locally-clocked superconnection def+reduction, T3 conformal repairs, T4
  driven-dissipative, T5 unification candidate) all cleared 2026-07-15 on **usage credits**
  (`cq-scope-fable-pass.md` + `velocity-and-clocks-fable-pass.md`). Remaining genuinely
  fable-gated: T2's full gauge theory + T5's proof — but both are DATA-gated first (version
  depth), so no fable unit is currently blocked on the cap.
- **SS-substrate** — `dn-self-sensing` B-a (interpreter-version supersession) + B-b (`AgentObservationStore`
  + φ_self). Roots DD-2 / Lane B. (Build-state to verify at /triage.)
- **(ext) the measure-first battery M1–M10** (= dn-fiber-geometry §2.6 = the **G-A survey**) — the DATA
  root most session-39 parks hang from: PD-a (M1/M2), PD-c (M5/M7), FG-b (M8), FG-f (M6/M7), FG-h (M7),
  the grammar's route-3 (M10). Read-only, built instruments; **RUN IT before formalizing anything**. (new 2026-07-21)
- **(ext) the C-fiber is thin / the live census is EMPTY** — bp-080 seal: the arrow-source stores were
  unmaterialized at build; ~4,084 C-edges exist but census read empty. **Several battery rows expected
  NULL today** (census, S↔C mismatch) — a null PARKS the machinery it gates (the point of measure-first). (new 2026-07-21)
- **(ext) the R&D flag `dream_rnd enabled=false`** (finding-0141) — roots the internal probe loop going
  LIVE (bp-079/082 are built-not-wired) **and** PD-3 (gap-steering). Owner wires it — a deliberate, gated act. (new 2026-07-21)
- **(ext) max effector tier = NONE** (finding-0011) — roots the EXTERNAL acting loop; the hands
  (acting/sensing) are built-DARK. The external sense-back also needs the Track-D correlator (design-only). (new 2026-07-21)
- **(ext) oq-0024 σ-sweep** (the owed run) — roots FG-b (M8) + the census/CN-4 calibration; **un-blocked,
  execution not design** — a strong un-gated next-exec that feeds the measure-first battery. (new 2026-07-21)

---

## Dependency graph (the chains, read top-down = "unlocks")

```
(ext) sample depth ──► R1 ──► R2 ──► R3 ──► R4 ──► PD-e
                        │       │      │
                        │       │      └──► VF-residual (+ R4)
                        │       └──► VF-jointspec ;  R3 also ─► VF-jointspec
                        └──► VF-covar ──► VF-duality
                        └──► VF-velhodge  (also ◄─ L-a)

(ext) retrieval eval set ──► TA-b ─┐
                             ML-c ─┴──► ML-a gate(i) ──► ML-a ──► ML-b (via gate ii)
MAG-census (RAN) ──────────────────► ML-a gate(ii)/(iii)   [gate iii NOT met 2026-07-15]
MAG-census ────────────────────────► DD-1 ;  MAG-census ─► TA-c (diamond frequency)

TA-d / core-temporal (BUILT) ──► CQ-wire (bp-037: β₁ TemporalView) ──► CQ-wire-2 (‖[d,τ]‖) ──► DD-1 ──► DD-2 (+ SS-substrate + TrackD)
                                        └──► (the algebra's first live consumer)
L-a (BUILT) ──► L-b ──► PD-f ;  L-a ──► L-c ;  L-a ──► PD-c (+ a Ricci rung)

CQ-ref (BUILT, bp-035) ──► CQ-align ; ──► CQ-mode1b ; ──► CQ-twin (parallel, owner-ruled)
CQ-scope (FORMALIZED 2026-07-15, fable on usage credits) ──► owner ratifies dn-capability-scope ──► the scope-layer build
VF-* (ALL FORMALIZED 2026-07-15, same fable session) ──► **dn-velocity-instruments DRAFTED** ──► owner
   ratifies ──► ONE plan now (the measurement-class pair, X2) + R-gated catalog graduates per gate
temporal-clocks T1–T6 (+ §2.5 erratum, finding-0083 PROMOTED) ──► **dn-temporal-geometry DRAFTED** ──►
   owner ratifies ──► clock-declaration obligation + J/Φ diagnostic (R1-gated) + dreamer-alone protocol
```

**Reading it:** almost the entire *dynamics/velocity* half hangs off one external root — **sample depth**
(the R-ladder) — which the young corpus likely hasn't cleared. The *magnetic operator* half hangs off a
**retrieval eval set** + the **census** (ran; gate iii not met). The *reference/query* half is the only
one with roots already satisfied (`core/temporal` + `ReferenceView` are built) — which is why the owner's
roadmap starts there.

**Session-39 chains (2026-07-21) — the newly-ratified cluster:**
```
3 notes RATIFIED (fbea48d) ──► /graduate:
  dn-inner-outer-core ─► M0 (born-green ring) ─► S1 (temporal splits +7) ─► M2 waves ─► M3 flip (◄ ratchet 0)
  dn-fiber-geometry   ─► G-A survey (M1–M10, read-only) ─┬─► M1/M2 ─► PD-a (sheaf, else per-class runs)
                                                          ├─► M5/M7 ─► PD-c (Forman first, then Ollivier)
                                                          ├─► M8 (= oq-0024) ─► FG-b ─► FG-h
                                                          └─► M10 ─► FG-d (E set→language) ◄─ explainable-retrieval consumer
  dn-agentic-loop     ─► AL-1 (profiles+G-D test) · AL-2 (C-coverage baselines) ─► PD-3 (◄ R&D flag)
                                                    · AL-3 (exhaust⊂dialogue + origin() view)
                        PD-1 (self-authored class) ◄─ authorship-axis gate (owner)

BUILT-DARK (flag-off): the whole dreamer H-family (staging/overlay/influence/conditioning) ─► finding-0130
  sweep-wiring + census live-read ◄─ (ext) owner turns HYPOTHETICAL live
INTERNAL loop live · PD-3 steering ◄─ (ext) dream_rnd flag (finding-0141) ;  EXTERNAL loop ◄─ tier NONE (finding-0011) + Track-D correlator
MOST FG/curvature parks ◄─ (ext) the M1–M10 battery (G-A) ;  the corpus is thin (C empty) ─► many rows expected NULL
```

**Reading the session-39 half:** the roots are now **owner ratify (done)** → **the read-only
measurement plans (G-A, AL-2)**, which are the DATA sources nearly every fresh park hangs from —
so graduating *those first* unblocks the most. The build parks (M0/S1/AL-1) are additive/born-green.
The loop parks (PD-1/PD-3, the external loop) hang off owner-gated flags (R&D flag, effector tier,
authorship-axis) — deliberately dormant, one owner act away each.

---

## Owner roadmap (2026-07-15) — sequenced onto the graph

The owner directed, in order: **(1) complete the algebra → (2) create (if possible) a unified query
language → (3) the diachronic dreamer tier**, and RULED (2026-07-15) the concrete session sequencing:

- **SESSION N+1 — build the algebra = `CQ-wire`.** "Complete the algebra" is settled = **wire the BUILT
  `core/temporal` (X_cite + operators: β₁ threads, `‖[d,τ]‖` citation-coherence) into its first live
  consumer** — it is built but wired to nothing (only tests import it). Opus, **no fable** needed. The
  *gated* upgrades (TA-a magnetic, TA-c diamond, the metric-coherence tier Result 4) are NOT part of
  this — they stay parked behind their eval-set / sample-depth / census-evidence triggers.
  → **GRADUATED 2026-07-15**: the built surface bifurcates by data shape, so `CQ-wire` split into
  **`bp-037`** (single-snapshot — β₁ threads via a commit-anchored `TemporalView`, `proposed`, awaits
  owner bless) + **`CQ-wire-2`** (two-snapshot `‖[d,τ]‖` coherence, gated on bp-037 so its upstream
  interface is built-not-inferred; open σ-resolution design settles in its own grounded pass). The
  owner may override at the bless gate and ask for both halves in one session.
- **SESSION N+2 — a FABLE session = `CQ-scope`** (the §2.1 capability-scope type system — all Views as
  one bounded-lattice scope algebra = the unified query language). Design largely settled in CQ §2.1
  (fable-vetted); the fable session formalizes + the build follows.
  → **DONE 2026-07-15** (early — ran on **usage credits**, owner-directed, not waiting for the Jul-17
  reset): fable pass `brainstorms/cq-scope-fable-pass.md` (S1–S8) + **`dn-capability-scope` drafted**.
  Awaits owner ratification; then `/graduate` mints the one scope-layer build plan (Opus, no fable).
- **SESSION N+3+ — the diachronic dreamer = `DD-1`** (corpus-structural tier over X_cite). **Depends on
  `CQ-wire`** (consumes the wired algebra) + `A7` + the lens contract → naturally follows the algebra
  build. `DD-2` (observed-plane weaving / Track D) waits on the self-sensing substrate + sample depth.

Dependency-soundness: **1 → 3 is a true edge** (`CQ-wire ► DD-1`); **2 is a home, not a hard blocker**
for 3 (DD-1 could ship as a lens then re-home into the scope algebra). The owner's order holds.
