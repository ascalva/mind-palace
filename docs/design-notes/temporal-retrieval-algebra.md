---
type: design-note
id: dn-temporal-retrieval-algebra
status: draft # draft → ratified → superseded.  draft→ratified is an OWNER-ONLY hand edit.
implementation: design-only # nothing built; states the fable-finalized results, licenses the graduation
created: 2026-07-14
updated: 2026-07-14
links:
  - docs/brainstorms/edge-dynamics-lane-b-fable-pass.md # the fable warrant this note states (whole; proofs live there)
  - docs/design-notes/edge-dynamics.md # ratified; this is its Lane B math home (§2.6 successor)
  - docs/design-notes/core-query-protocol.md # §2.5 temporal formalization; this note is its "math successor"
  - docs/design-notes/self-sensing.md # §2.4 inversion / interpreter-version coordinate (A7); B-a/B-b substrate
  - docs/design-notes/supersession-lifecycle.md # §4.5 depth re-anchoring; §7 rename identity (A6 prerequisite)
  - docs/design-notes/recursive-strata-amendment.md # γ^d, typed edge_budget, fibers vs dispositional
supersedes: null
superseded_by: null
warrant: docs/brainstorms/edge-dynamics-lane-b-fable-pass.md
---

# The temporal-retrieval algebra — the Lane B / §2.5 math, made theorem-grade

> Composed by the orchestrator (**Opus 4.8/xhigh**, 2026-07-14) from the **verified Fable
> pass** (`claude-fable-5`, tier owner-confirmed) captured in
> `docs/brainstorms/edge-dynamics-lane-b-fable-pass.md`. This note **states** the
> fable-finalized results and makes the design decisions they inform; the derivations and
> proofs live in the capsule (cited, not repeated) — the same "opus-drafted, fable-checked,
> owner-ratified" seam `dn-core-query-protocol` used.
>
> It is the **math successor** that `dn-core-query-protocol` §2.5 / Consequence 5 and
> `dn-edge-dynamics` §2.6 both call for: the formalized temporal algebra that serves *both*
> the retrieval protocol and edge-dynamics Lane B, in one place, cross-linked from each.
> `dn-edge-dynamics` is ratified/immutable — this note is its Lane B math home, **never an
> edit to it.**
>
> Ratification is a hand edit by the owner — no command performs it, `gate-guard` denies any
> agent attempt, and `/graduate` refuses this note until `status: ratified`. Every nontrivial
> result carries its fable grade (`[ESTABLISHED]`/`[DERIVED]`/`[SKETCH]`); trust-weight
> accordingly.

## 1. Purpose and scope

`dn-core-query-protocol` §2.5 stated the temporal results but marked their **formalization
Parked** for a fable session; its Parked table said *nothing in §2.2 is theorem-grade until the
normalization triple is pinned*. `dn-edge-dynamics` §2.6 named Lane B (the observed-side
dynamics) and deferred its math to a "Lane B math successor." This note is that successor. It
decides:

1. **The normalization triple, pinned** (§2.1) — the cost dictionary, directedness, and the
   `(β,z)` coupling, so the retrieval curve is theorem-grade (Theorem A1).
2. **The two mode-3 operators, formalized and re-ranked** (§2.2) — a correction to the note's
   "declare which": `π_active` (ledger-compression) is the *ambient default*; `σ_*`
   (correspondence-transport) is the *opt-in* temporal traversal.
3. **The five §2.5 results, made theorem-grade** (§2.3) — hypotheses stated, each graded proven
   or sketch.
4. **Three structural rulings the dynamics forces** (§2.4) — the separate citation complex and
   its home (A4); Hodge well-definedness on `E_geom ⊔ E_disp` (A5); temporal well-foundedness
   and its data prerequisite (A6).
5. **The load-bearing signal-vs-noise discriminator** (§2.5) — the apophenia guard lifted to
   the dynamics (A7); and **β\*** resolved from conjecture to theorem (§2.6 / A8).

**Out of scope, explicitly:** the retrieval *protocol architecture* (scope grammar, boundary
ruling, the reference agent) stays in `dn-core-query-protocol`; the *consumer* that reads this
dynamics (the weaving correlator) is the Track D charter; the *diachronic dreamer* ruling lives
in `dn-core-query-protocol` (Ruling B). This note is the **algebra**, not its clients. It builds
nothing — graduation follows ratification.

## 2. Principles / decision

### 2.1 The normalization triple — pinned (A1)

`[capsule A1]` The three under-pinned choices are settled:

- **(i) Cost dictionary — two dictionaries on orthogonal axes, not a competition.** `c = −log w`
  is the **walk** cost (canonical): the unique dictionary (up to affine reparam) under which the
  reference random walk's path affinity is `e^{−c(path)} = ∏ w`, the β→∞ tropical limit is the
  Viterbi path, and Maslov dequantization holds. `distance = 1 − sim` is the **Rips filtration
  scale** — a *different object*, on which the built `dim ker L₁ == ripser β₁` falsifier
  (`hodge.py`; `dn-edge-dynamics` §2.2) depends. **Neither is "the" cost; they parametrize
  orthogonal axes (walk-temperature vs topological-scale).** `[DERIVED]`
  - *Weight normalization sub-ruling:* citation weights normalize to `(0,1]` before `−log`.
    **Consequence:** on the *binary* citation graph every present edge costs 0, so the
    β-deformation is **degenerate (1a ≡ 1b)** — the `(β,z)` machinery earns its keep on the
    *weighted* similarity backbone and any future graded-fiber graph, **not** the raw binary
    doc→doc graph. `[DERIVED]`
- **(ii) Directedness — retrieval kernels symmetric; direction carried by modes 1a/3.** PSD
  kernels are symmetric, so Mode 1b (diffusion) and Mode 2 (semantic) use the **symmetrized
  fiber graph `A_F + A_Fᵀ`** (co-reference); direction lives in Mode 1a (reachability, the two
  transitive closures `A_F^*` / `(A_Fᵀ)^*`) and Mode 3 (temporal transport), which are
  semiring/operator objects and need no symmetrization. The **magnetic/Hermitian Laplacian
  `L^{(q)}`** is the named directed-*diffusion* upgrade (charge `q=0` recovers symmetric v1;
  `q>0` keeps direction in complex phase, stays Hermitian-PSD). Rejected: Chung's directed
  Laplacian (needs strong connectivity — citation graphs are DAGs) and naive `(A+Aᵀ)/2`
  (discards the co-citation distinction). This is `dn-edge-dynamics` PD-b's "combinatorial v1,
  weighted parked." `[DERIVED; RECOMMEND for v1]`
- **(iii) The `(β,z)` coupling — one canonical curve; z's bound IS the γ-ceiling.** The family
  `K(z,β) = (I − z A^{∘β})⁻¹` converges iff `z·ρ(A^{∘β}) < 1`. The canonical curve is the
  one-parameter RSP/free-energy family (β free, z slaved to the killed-walk normalization),
  endpoints β→∞ = shortest-path (1a), β→0 = commute-time/resistance (1b). **v1 exposes β only**
  (one dial spans the whole 1a↔1b unification; a second free dial has no falsifier until a
  retrieval eval set exists). The load-bearing tie: **`z·ρ(A^{∘β}) < 1` is the *same* spectral
  condition as Invariant-10's `γ^d` contraction** — the retrieval curve's convergence and the
  strata tower's boundedness are one spectral fact; z is bounded by the safety invariant that
  bounds the tower. `[ESTABLISHED (walk family): fable-2026-07-13; DERIVED (the tie)]`

**Theorem A1 (well-posedness of the retrieval curve).** `[DERIVED, capsule A1]` On a finite
fiber graph with weights in `(0,1]`, costs `c = −log w`, symmetrized backbone `A_F + A_Fᵀ`:
`K(β)` is a well-defined PSD kernel for all finite β>0, with `lim_{β→0} K(β) = (L_F)⁺`
(resistance) and `lim_{β→∞}` a tropical shortest-path *metric* that is generically **not** of
negative type (Schoenberg — the phase boundary, §2.6). The walk-sum converges iff
`z·ρ(A^{∘β}) < 1` (Invariant-10).

### 2.2 The two mode-3 operators — formalized and re-ranked (A2)

`[capsule A2]` A **correction** to `dn-core-query-protocol` §2.5 (which frames the two as peers a
temporal query must "declare which"): **they are not peers.**

- **`π_active` — ledger-compression.** Orthogonal projection onto the not-yet-superseded
  subspace; a **contraction** (`‖Π‖≤1`), **idempotent**, **not** a chain map, **does not compose
  functorially**. It is the operator form of the `D`-exclusion invariant, applied to **every**
  non-temporal query. **It is the ambient default (`T = now`)** — destroys superseded content.
- **`σ_*` — correspondence-transport** (and its adjoint `σ^*`, pullback). A **chain map**
  `C^•(X_n) → C^•(X_{n+1})`, degree 0, covariant *iff F1 holds*; preserves homology/threads,
  preserves kernels only if σ is isometric; composes (F2); **retains** superseded content (points
  forward, keeps lineage). **It is the opt-in temporal traversal** a query declares
  (`T = window, E ∋ D, direction ∈ {forward = σ_*, backward = σ^*}`).

The one canonical composite is the **active-view transport** `T_active = π_active ∘ σ_* ∘ ι`
(embed active into ledger, transport, compress back) — the contraction whose Sz.-Nagy dilation is
`σ_*` on the full ledger (§2.3 Result 4). Naming/typing is fixed by `dn-core-query-protocol` C3.

### 2.3 The §2.5 results — theorem-grade (A3)

Let `X_n` be the citation complex at time n (§2.4), supersession `D` inducing note-correspondence
`σ`. `[capsule A3]`

1. **Bicomplex ⟺ (F1 ∧ F2). PROVEN (mod. hypotheses).** Hypotheses: (H0) supersession a strict
   partial order (acyclic); (H1) rename-stable identity (§2.4 / A6); (H2) transitive closure
   taken. Then `δ_D² = 0` from H0 (poset ⇒ nerve ⇒ coboundary²=0); the cross-relation
   `dδ_D = ±δ_D d` ⟺ each σ a chain map ⟺ **F1** (simpliciality — *a revised note's citations
   carry forward; the killer is a severed citation*); with citation coefficients `δ_D²=0` also
   needs **F2** (composition — a *failable* data-integrity invariant). `[ESTABLISHED + DERIVED]`
2. **`[d,τ]` supported exactly on severed citations. PROVEN (tight).** `([d,τ]φ)(u,v) =
   (φ(σv) − φ(σu)) · 𝟙[{σu,σv} ∉ X_{n+1}]` — so `‖[d,τ]‖` **is** the weighted citation-carry-
   forward failure count, not a proxy. **Now computable on the authored-note citation graph
   (bp-026 complete).** `[DERIVED, full computation]`
3. **Quillen superconnection with curvature `[d,τ]`. PROVEN on the linear time chain; SKETCH for
   fork/merge diamonds.** `𝔸 = d + τ`, `𝔸² = [d,τ] + τ²`; **τ²-coherence ⟺ F2**, then `𝔸² =
   [d,τ]` is the curvature and **flat ⟺ bicomplex ⟺ F1**. Non-flatness is the *first* obstruction,
   not a dead end: if the class `[[d,τ]]` is exact (`= [d,h]`) the corrected differential
   `d+τ+h` is flat — the true invariant is the class, not the cochain. The diamond case needs the
   homotopy-coherent (twisted-complex, Bondal–Kapranov / Block) version with higher `τ_k` — a
   **sketch**, deferred pending measured diamond frequency (Parked). **Two curvature layers stay
   distinct — do NOT merge in a note:** (i) the superconnection `[d,τ]` on a linear chain; (ii)
   diamond holonomy; and neither is the *static* Forman–Ricci curvature (`curvature.py`). *Same
   word, different tensors.* `[ESTABLISHED frame: Quillen 1985; DERIVED identification]`
4. **Topological ⊊ metric coherence. PROVEN.** `σ_* d = d σ_*` (F1) does **not** give
   `σ_* δ = δ σ_*` (needs σ isometric): chain maps transport *homology* (threads gain a temporal
   life) but not *kernels*. Kernel-flatness ⊋ bicomplex-flatness — where PD-b (weighted inner
   products) becomes a customer. `[DERIVED]`
5. **Ledger = Sz.-Nagy isometric dilation of the active-view transport. PROVEN (merge wrinkle
   resolved).** `T_active` is a contraction; by Sz.-Nagy the isometric dilation is the concrete
   append-only ledger embedding `H_n ↪ H_{n+1}`. **Merge resolution:** `σ_*` (pushforward) is only
   a partial isometry when supersession is merge-free; **pin the canonical dilation to the
   pullback `σ^*`** (always a contraction), which removes the merge caveat cleanly — *"revision
   destroys structure in the active view; the ledger is the space in which nothing was
   destroyed"* is then a theorem. `[ESTABLISHED: Sz.-Nagy 1953; DERIVED identification]`
6. **Strict γ-contraction except at owner promotions. PROVEN, conditional on the §4.5 ruling
   (`dn-core-query-protocol` C4).** On confidence-weighted cochains `‖σ_* x‖_w ≤ γ‖x‖_w` — a
   strict γ-contraction — **except** where an owner promotion re-anchors depth (multiplying the
   weight by `γ^{d₀−d} > 1`: energy injection). **The only operation that injects energy is the
   owner verdict** — *"the owner is the only energy source in the dynamics."* Becomes
   unconditional once C4 lands (which rules that promotion re-anchors depth precisely so the
   dynamics has an energy source). `[DERIVED, contingent on §4.5]`

**The built falsifier binds this note too:** every continuous/algebraic claim above must
reproduce the exact discrete invariants (β₁ of `X_cite`, `dim ker L₁`, the content-addressed
edge set) within tolerance at the sample times — the inversion's Rule 2 (§2.7).

### 2.4 The citation complex, its home, and Hodge on the typed edge set (A4–A6)

- **A separate citation complex `X_cite`, in a separate home.** `[DERIVED; VERIFIED
  reference_edges.py:117–129 (no payload column), test_reference_edge_isolation.py]` The §2.3 math
  is over a **citation** complex; `hodge.py` builds on the **similarity** backbone
  `A = cosine_adjacency(emb)`. `X_cite` is built from `reference_edges.sqlite` (doc→doc-live,
  bp-026): 0-cells notes, 1-cells `corpus_to_corpus` citation edges, D-arrows the
  supersession/version chains. It is **embedder-independent by construction** (deterministic
  parse, no model) — the hinge of the A7 discriminator (§2.5). **Architectural constraint (surfaced
  by the fable pass, load-bearing for graduation):** because the isolation invariant grep-asserts
  that `core/complex/**` never imports `reference_edges`, the `X_cite`/temporal module **MUST live
  OUTSIDE `core/complex/`** — proposed `core/temporal/` (or `core/query/`), which *reads*
  `ReferenceEdgeStore` and never touches `A_signed`/`build_complex`. This is `dn-edge-dynamics`
  §2.7's "shared mathematics, never shared state" one level up: two complexes, two homes, one
  methodology. **Confirmed it does not violate `test_reference_edge_isolation.py`.**
- **Hodge on `E_geom ⊔ E_disp` — do NOT mix (A5).** `[DERIVED]` `E_disp` is directed/acyclic (a
  DAG); `E_geom` is undirected geometry. A single `L₁` over the union is a **type error** (conflates
  incompatible metrics; lets supersession into balance-adjacent math — violates the `E_disp`-
  exclusion invariant). The two edge types map onto the two **sides of Helmholtz**: `E_disp`
  (acyclic ⇒ a consistent depth potential exists) is **pure gradient / `d₀(depth)` — curl-free,
  harmonic-free**; `E_geom`'s **harmonic threads (ker L₁)** are the part with **no** potential
  (the time-*invariant* structure). **So "direction" is a genuine gradient object precisely on the
  acyclic dispositional edges** — metaphor-over-noise only if read off the harmonic part of
  `E_geom`, or off a cyclic set. The diachronic reader reads the `E_disp` gradient and the *change*
  in `E_geom`'s harmonic content across snapshots (`σ_*`), **never a mixed `L₁`.**
- **Well-foundedness beyond acyclicity (A6).** `[DERIVED]` Beyond `δ_D²=0`, a well-founded temporal
  complex needs: **(1) rename-stable identity** (`supersession-lifecycle` §7 — `doc_id=source_path`
  forks lineage on rename; a **data prerequisite currently AT RISK** — `sync.py:77,84`; this gates
  the diachronic reader — see the OWNER DECISION below); (2) **F2 as a checked invariant**; (3)
  no-op re-saves logged as occurrences, not versions; (4) the **op-seq well-order** (`op-seq ∈ ℕ`
  ⇒ well-founded, strictly stronger than acyclic — what makes induction over revision threads
  terminate).

### 2.5 The signal-vs-noise discriminator — the apophenia guard, lifted (A7)

`[DERIVED; grounds in self-sensing §2.4 + edge-dynamics §2.5 R1/R2 + reference-edge embedder-
independence]` **The load-bearing result.** Separate genuine *evolution* (a fiber strengthens
because a related note was added) from *artifact* (a fiber shifts because the embedder was
re-run), or a diachronic reader interprets drift that isn't there.

- The discrete record is content-addressed/exact; the embedding is an **INTERPRETED, versioned**
  object (the inversion). So the two change-sources separate by the **interpreter-version
  coordinate self-sensing §2.4 already mandates**: *genuine evolution* = Δ(record) at **fixed**
  interpreter version; *artifact* = Δ(interpreted object) across interpreter versions at **fixed**
  content — i.e. **a re-embed is a supersession event in the interpreter-version chain**, already
  tagged and attributable. Nothing new is needed to *detect* it.
- The **embedder-invariant floor is `X_cite`** (changes only when content changes) — so the
  diachronic reader's **primary** signal is `X_cite` dynamics; similarity-backbone dynamics is
  **secondary** and must be interpreter-version-controlled.
- **The falsifiable discriminator:** decompose `Δedge = Δ_content + Δ_interpreter`, where
  `Δ_interpreter` is measured by re-embedding the *old* snapshot's content under the *new*
  embedder (content fixed). **A drift/direction claim is admissible only when
  `‖Δ_content‖ ≫ ‖Δ_interpreter‖`.** Equivalently (inversion Rule 2): the exact discrete
  invariants are the falsifiers — *a drift claim that moves no exact discrete invariant is
  embedding noise* — and the reader emits **nothing** (the `change_point` honest-seam). This is the
  fourth Track D entry gate (charter note; without it the weaving consumer is an apophenia engine).

### 2.6 β\* — a theorem, not a conjecture (A8)

`[DERIVED, via continuity of β↦d_β + closedness of the negative-type cone + Schoenberg]`
`β* := sup{β ≥ 0 : d_β is of negative type}` is **finite iff the shortest-path metric `d_∞` is
NOT of negative type** (closedness of the negative-type cone forces the limit; contradiction
otherwise). `d_∞` fails negative-type whenever the graph has an isometric cycle `C_{≥4}` — generic
for any sparse citation graph with cyclic structure; trees/block graphs are the `β*=∞` exception
(matching the prior conjecture). **Required sharpening (a real error to avoid in a successor):**
distinguish the two "kernel" notions — **for all finite β the RSP kernel `K(β)` is PSD**; what is
lost at β\* is only realizing the free-energy *distance* `d_β` as a Hilbert metric via
`e^{−s d_β}` (Schoenberg). The phase transition is about the **metric's** negative-type, **not**
the RSP kernel's PSD-ness. The exact β\* is graph-dependent and computable by the capsule's sweep
— **now runnable on the authored-note citation metric (bp-026)**; its *finiteness* is now proven.

### 2.7 What is inherited, unchanged

The **inversion** (`dn-edge-dynamics` §2.5) binds every result here: the discrete record is the
reality; each continuous/fitted object (RSP kernel, β-curve, spline trajectory, fitted transport)
is an **INTERPRETED, versioned** worldview, superseding at its identity key when the method
changes, **falsified against the exact discrete invariants** at the sample times, and **gated on
sample count** (the R1→R4 ladder). Nothing here moves the data boundary (`𝔎|_MR` authored-only;
cross-stratum edges stay out of `A_geom`/`build_complex`), touches a model, reaches the network,
or introduces back-action.

## 3. Consequences — what this note licenses (on ratification)

1. **The `core/temporal/` (or `core/query/`) module** — `X_cite` assembly from
   `ReferenceEdgeStore`, `∂`/`δ_D`, the `σ_*`/`σ^*`/`π_active` operators, `‖[d,τ]‖`, outside
   `core/complex/`. Deterministic, sparse, no model/network/store-mutation. *Falsifier: it imports
   `reference_edges` from inside `core/complex/` (reddens the isolation grep), or a computed
   invariant differs run-to-run on the same commits, or `dim ker L₁`/β₁ of `X_cite` disagrees with
   an independent ripser computation.*
2. **The empirical Thread-C sweep** (now unblocked on authored notes, bp-026): `‖[d,τ]‖` flatness
   over real supersession events, the F2-violation count, diamond frequency, the β\* sweep on the
   citation metric — a measurement program, each result INTERPRETED-class per §2.7.
3. **The retrieval curve `K(β)`** as the core-query-protocol's structural retrieval implementation
   (β-dial only in v1), with z bounded by Invariant-10.
4. **`dn-core-query-protocol` and `dn-edge-dynamics` Lane B** both cite this note as their math
   home (cross-links, no edits to the ratified edge-dynamics note).

## Parked decisions

| id | decision | default recorded | re-entry condition |
| --- | --- | --- | --- |
| TA-a | weighted vs combinatorial inner products (inherits `dn-edge-dynamics` PD-b) | combinatorial v1; the magnetic Laplacian `L^{(q)}` is the directed-diffusion upgrade | the metric-coherence tier (Result 4) is built, or PD-b's second customer is proposed |
| TA-b | the `(β,z)` plane's second (resolution) dial | β-only in v1 (no falsifier for z until a retrieval eval set) | a retrieval eval set gives z a falsifier |
| TA-c | the homotopy-coherent (diamond) superconnection | linear-chain superconnection proven; diamonds a sketch+cite | measured fork/merge diamond frequency warrants the twisted-complex `τ_k` rigor |
| TA-d | `X_cite` module home | `core/temporal/` (or `core/query/`), outside `core/complex/` | the graduating plan pins the package name |
| TA-e | build-plane citation coverage | authored-note citations only (bp-026); build-plan `design_ref` targets still doc→doc-blind | the residual `design_ref` extractor lands |

## Open questions / OWNER DECISIONS

- **OWNER DECISION — rename-stable identity priority (A6).** The diachronic reader (and Result 1
  H1, β\* over lineage) **requires** rename-stable note identity, but the codebase keys on
  `source_path` (forks lineage on rename — `supersession-lifecycle` §7, `sync.py:77`). Should the
  uuid-stable-identity work be prioritized **before** the diachronic reader graduates?
  *(Orchestrator rec: yes — it is a hard prerequisite, not an optimization.)*
- **OWNER DECISION — magnetic-Laplacian timing (A1 ii / TA-a).** When does directed *diffusion*
  (`L^{(q)}`, not just directed reachability) earn the weighted-inner-product tier? *(Rec: defer;
  parked cleanly with PD-b.)*
- **OWNER DECISION — the evolution study's axes** (`dn-edge-dynamics` §5, `self-sensing` §5 open
  q). Does the evolution study formally adopt the **phase-space axis** (q from snapshots, measured
  p from B-a chains) and the **epistemology axis**, alongside economics? *(Your taste call at this
  note's ratification.)*
- Diamond-superconnection rigor (TA-c) and the z-resolution dial (TA-b) re-enter per their gates.

## Cross-references

- `docs/brainstorms/edge-dynamics-lane-b-fable-pass.md` — the **warrant**: the full fable
  derivations (A1–A8), grades, and rejected alternatives this note summarizes.
- `docs/design-notes/edge-dynamics.md` — ratified; the 1-form lift, the ladder + inversion, §2.6
  Lane B (this note is its math home); the built `hodge.py` degree-1 object.
- `docs/design-notes/core-query-protocol.md` — §2.2 the algebra, §2.5 the temporal results this
  note formalizes, C1–C5 (the protocol-side rulings), the two mode-3 operators' naming (C3).
- `docs/design-notes/self-sensing.md` — §2.4 the inversion / interpreter-version coordinate (A7),
  the B-a/B-b substrate the observed-side dynamics wait on.
- `docs/design-notes/supersession-lifecycle.md` — §4.5 (the depth re-anchoring dichotomy, ruled in
  core-query-protocol C4), §7 (rename identity — the A6 data prerequisite).
- `docs/design-notes/recursive-strata-amendment.md` — `γ^d` (Invariant 10; the z-bound tie), the
  typed `edge_budget`, fibers vs dispositional edges.
- code: `core/complex/hodge.py` (similarity-backbone Hodge; the falsifier), `core/complex/{laplacian,
  topology,spectral,curvature}.py`, `core/stores/reference_edges.py` (the `X_cite` substrate; schema
  v2, no payload), `tests/integration/test_reference_edge_isolation.py` (the isolation invariant),
  `core/ingest/sync.py` (`source_path` identity — the A6 risk).
