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

**Coverage.** SEEDED (2026-07-15) with the **query / edge-dynamics / magnetic / reference cluster** —
the tangle currently in play. Other clusters (effectors/Track G, dreaming, sensing, secrets, voice,
etc.) are swept in incrementally at `/triage`; a `⋯` at the end of a section marks "more to harvest."

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
| CQ-scope | **the capability-scope type system (the UNIFIED QUERY LANGUAGE)** — all Views as instances of one bounded-lattice scope algebra | CQ §2.1 | parked | (ext) Fable (fable-grade design) | owner-directed (roadmap #2); formalize post-Fable-reset, then build |
| CQ-mode1b | Mode-1b soft diffusion + the `K_struct ⊙ K_sem` hybrid | CQ §2.2 | parked | → CQ-ref, (ext) kernel machinery | a ranking customer + eval set |

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
| PD-a | 2-simplices beyond 3-cliques | ED §4 | parked | — | the sheaf/general-transport design pass |
| PD-b | weighted L₁ (strength inner products) | ED §4 | parked | — | harmonic reps too delocalized to narrate, OR the metric tier (→ TA-a) |
| PD-c | **Ollivier directed-walk Ricci (the true "directed Ricci")** | ED §4 / MAG §2.6 | parked | → L-a, (ext) a P5 rung needing it | Lane A lands AND a Ricci-flow rung needs the principled form |
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
| ML-d | magnetic Weitzenböck / flux-aware Forman | MAG ML-d | parked | (ext) a curvature customer + Q1 obstruction addressed | both appear |
| MAG-own2 | dream-narration vocabulary for the arrow-aware census | MAG owner-dec-2 | **open-owner** | → DD-1 | owner taste ruling (at a lens plan) |
| MAG-own3 | covering-only `supersedes:` as a checked A6 invariant | MAG owner-dec-3 | **open-owner** | — | owner ruling (rec: adopt; near-zero cost; keeps the Hasse DAG triangle-free) |

### Vector-field candidates — `docs/brainstorms/edge-dynamics-vector-field.md` (~mine, fable-grade)
| id | item | home | status | depends on | re-entry / trigger |
|---|---|---|---|---|---|
| VF-covar | velocity-covariance / Koopman-lite (the corrected Q1: `cos(ẇ_i,ẇ_j)` matrix eigenmodes; market-beta split) | brainstorm | parked | → R1, (ext) Fable | R1 series exist + a Fable pass to formalize |
| VF-velhodge | velocity Hodge decomposition (harmonic-velocity = change orbiting an unstated gap) | brainstorm | parked | → R1, → L-a, (ext) Fable | R1 + Fable |
| VF-jointspec | joint space×time spectrum (L₁ modes × Lomb–Scargle) | brainstorm | parked | → R2, → R3 | R2/R3 land |
| VF-duality | distant-correlation ⟺ low-graph-frequency | brainstorm | parked | → VF-covar, → L-a | VF-covar built |
| VF-residual | prediction-residual = live creative signal (autonomous predicts dissipation; owner is the forcing term) | brainstorm | parked | → R3, → R4 | the evolution operator is fit |

### External conditions (not decisions — the roots the chains hang from)
- **(ext) sample depth** — data accretion over commits; the root of the whole R-ladder + every VF-*.
  The corpus is YOUNG (2026-07-15 census: 234 distinct doc→doc pairs / 113 nodes) — likely below R1's
  honest-CV threshold today.
- **(ext) a retrieval eval set** — roots TA-b, ML-c, CQ-mode1b. Note CQ-selfgrade (bp-035's oracle)
  *bootstraps* a structural eval set; a *directed-ranking* eval set is a further step.
- **(ext) Fable weekly cap** — resets **Jul 17 8pm ET** (currently 100% used). Gates the *formalization*
  of CQ-scope + every VF-*.
- **SS-substrate** — `dn-self-sensing` B-a (interpreter-version supersession) + B-b (`AgentObservationStore`
  + φ_self). Roots DD-2 / Lane B. (Build-state to verify at /triage.)

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
(ext) Fable reset ──► CQ-scope (unified query language) ;  ──► every VF-* formalization
```

**Reading it:** almost the entire *dynamics/velocity* half hangs off one external root — **sample depth**
(the R-ladder) — which the young corpus likely hasn't cleared. The *magnetic operator* half hangs off a
**retrieval eval set** + the **census** (ran; gate iii not met). The *reference/query* half is the only
one with roots already satisfied (`core/temporal` + `ReferenceView` are built) — which is why the owner's
roadmap starts there.

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
  one bounded-lattice scope algebra = the unified query language). Correctly placed **after the Jul-17
  Fable reset** (Fable is 100% capped until then). Design largely settled in CQ §2.1 (fable-vetted); the
  fable session formalizes + the build follows.
- **SESSION N+3+ — the diachronic dreamer = `DD-1`** (corpus-structural tier over X_cite). **Depends on
  `CQ-wire`** (consumes the wired algebra) + `A7` + the lens contract → naturally follows the algebra
  build. `DD-2` (observed-plane weaving / Track D) waits on the self-sensing substrate + sample depth.

Dependency-soundness: **1 → 3 is a true edge** (`CQ-wire ► DD-1`); **2 is a home, not a hard blocker**
for 3 (DD-1 could ship as a lens then re-home into the scope algebra). The owner's order holds.
