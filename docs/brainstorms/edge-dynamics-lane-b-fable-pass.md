# Edge-dynamics Lane B / temporal-retrieval algebra — the fable finalization pass

> **Fable session capsule** (`claude-fable-5`, verified tier; 2026-07-14). Durable *working
> material* (a brainstorm), **not** a design note — nothing here flips a status, edits a
> ratified note, or blesses a transition. This is the fable warrant §1.3 of
> `dn-core-query-protocol` asks for: finalize the parked/provisional frontier, make the §2.5
> stated results theorem-grade, settle the design rulings, and answer the diachronic-dreamer
> question. It vets and, where warranted, **corrects** the opus draft.
>
> **Scope discipline.** I produce DESIGN REASONING. I do not touch `edge-dynamics.md`
> (ratified, A8-immutable), the foundation denylist, or any status. Owner-reserved calls are
> surfaced as explicit **OWNER DECISION** items. Every nontrivial claim is labeled
> `[ESTABLISHED: cite]` / `[DERIVED: from X]` / `[INFERENCE]` / `[ANALOGY]`.
>
> **Honesty on prior work.** The core algebra + temporal results were established by a prior
> verified fable pass (captured in `docs/brainstorms/core-query-protocol.md`, 2026-07-13
> capsules). I do **not** re-derive them; I finalize the parked items, tighten hypotheses to
> theorem grade, and rule the design questions. Where I reuse a prior result I cite it as
> `[ESTABLISHED: fable-2026-07-13]`.
>
> **Material substrate update (load-bearing, changes several caveats).** `bp-026` is
> **COMPLETE and SEALED** (`docs/build-plans/bp-026/plan.md: status: complete`;
> `core/stores/reference_edges.py` schema v2; `ops/code_sensor.py` `_corpus_to_corpus_edges`).
> The doc→doc citation gap (finding-0059/0061/0062) that both the note and the prior fable
> capsule treated as OPEN is **now closed for authored notes** (`design-ref` + `note-citation`
> patterns; build-plan `design_ref` targets are the residual gap per PROGRESS 2026-07-13). So
> the `[d,τ]` flatness, the F2-violation count, and the β* sweep on the *citation* metric are
> **no longer "untestable today"** for the authored-note citation graph. I revise that register
> below.

---

## 0. Executive map (what this pass concludes)

- **A (temporal algebra).** The normalization triple is pinned: `c=−log w` is the *walk*
  cost (canonical), `1−sim` is the orthogonal *filtration* scale (keep both); retrieval
  kernels live on the symmetrized fiber graph `A_F+A_Fᵀ` (v1) with the magnetic Laplacian as
  the PD-b upgrade; the canonical (β,z) curve is the one-parameter RSP family with z slaved,
  and **z's convergence bound is literally Invariant-10's γ-ceiling.** The two mode-3 operators
  are formalized and — a correction — **are not peers**: `π_active` (ledger-compression) is the
  ambient default, `σ_*` (correspondence-transport) is the opt-in temporal traversal. The §2.5
  results are made theorem-grade with hypotheses stated; the diachronic signal-vs-noise
  discriminator (rider 3, LOAD-BEARING) is resolved *with the inversion's own machinery*; **β\*
  is resolved from conjecture to a theorem-with-graph-constant.**
- **B (diachronic dreamer).** Ruling: **a DISTINCT diachronic interpreter, not a second mode**
  of the synchronic dreamer — the codebase already left the temporal-shaped hole (`change_point`
  deferred seam), and the Lane A/B firewall forces the split.
- **C (opus-provisional).** The §2.4 sacred-boundary ruling is **CORRECTED toward
  capability-dissolution** (repo-derivability; a local twin, not a sealed-store read) — the
  single highest-stakes call, and the opus judgment was one step short of the-sacred-boundary's
  own dissolution test. The scope grammar is made fable-grade (a bounded lattice; meet=safe
  composition; monotone delegation = non-negotiable #6). §4.5 is **RULED: promotion re-anchors
  depth** (the dynamics forces it if the owner is to be the only energy source). **One note or
  two: TWO** (a math successor + the Track D charter; never an edit to ratified edge-dynamics).
- **D (Track D charter).** Chartered with a **fourth entry gate added**: the A7 discriminator
  must be implemented and enforced, or the weaving consumer is an apophenia engine.

---

## A. THE TEMPORAL-ALGEBRA FORMALIZATION

### A1. The normalization triple — pinned, with a theorem of well-posedness

The prior fable pass was explicit: *nothing in §2.2 is theorem-grade until the cost dictionary,
directedness, and (β,z) coupling are pinned.* I pin all three.

**(i) The cost dictionary — a TWO-DICTIONARY ruling, not a competition.**
The apparent choice `c=−log w` vs `c=1−sim` dissolves once one sees the two live on *orthogonal
axes*:

- **Walk axis → `c = −log w` (canonical, pin it).** `[DERIVED: from the RSP/free-energy
  construction, ESTABLISHED: fable-2026-07-13 Prop 1]` This is the *unique* dictionary (up to
  affine reparam) under which (a) the reference random walk's path affinity is `e^{−c(path)} =
  ∏ w` (multiplicative→additive bridge via −log), (b) the β→∞ tropical limit is the walk's
  max-likelihood/Viterbi path, and (c) Maslov dequantization holds — `S_β` is `(+,×)`-isomorphic
  for finite β, degenerating to `(min,+)` only at β=∞. `c=1−sim` fails all three: `Σ(1−sim)`
  along a path is not `−log∏sim`, and `e^{−β(1−sim)}` is not the walk affinity.
- **Filtration axis → `distance = 1−sim` (keep it, it is a DIFFERENT object).**
  `[ESTABLISHED: hodge.py:8–12; topology.py Rips]` This is the Vietoris–Rips *scale* parameter,
  not an edge cost in a walk. The whole Rips↔flag consistency (`dim ker L₁` == ripser β₁,
  edge-dynamics §2.2 falsifier) depends on it. Conflating the two would break the built
  falsifier. **The two dictionaries parametrize orthogonal axes: walk-temperature vs
  topological-scale. Neither is "the" cost; they answer different questions.**

  Weight normalization sub-ruling `[DERIVED]`: citation weights must be normalized to `(0,1]`
  before `−log` (a present binary citation → `w=1` → `c=0`; a raw multiplicity `count>1` →
  `−log(count)<0` is ill-formed). **Consequence worth stating: on the *binary* citation graph
  every present edge costs 0, so the β-deformation is DEGENERATE (1a≡1b — all paths cost 0).**
  The (β,z) machinery earns its keep on the *weighted* similarity backbone and on any future
  graded-fiber graph (multiplicity/recency/strength), not on the raw binary doc→doc graph. This
  sharpens where the algebra is non-trivial.

**(ii) Directedness — retrieval kernels are symmetric; direction is carried by modes 1a/3.**
Citations and supersession are directed; PSD kernels are inherently symmetric. Ruling `[DERIVED;
RECOMMEND for v1]`:

- **Mode 1a (hard reachability) and Mode 3 (temporal transport) are natively DIRECTED** — they
  are semiring/operator objects (path closure `A_F^*`, transfer operator), not kernels, so they
  need no symmetrization and *direction is their whole content*. The two transitive closures
  `A_F^*` (who this cites) and `(A_Fᵀ)^*` (who cites this) are the directed reachability answers.
- **Mode 1b (soft diffusion, PSD) and Mode 2 (semantic) use the SYMMETRIZED fiber graph
  `A_F+A_Fᵀ`** (co-reference: co-cited-or-mutually-citing). A PSD "what is structurally near s"
  is a symmetric question; direction lives in the modes that are about *reaching*, not
  *nearness*. **The magnetic/Hermitian Laplacian `L^{(q)}` is the named upgrade** (directed
  *diffusion*, PD-b's "second customer") — charge `q=0` recovers the symmetric v1 exactly, `q>0`
  retains direction in complex phase while staying Hermitian-PSD. Rejected: Chung's directed
  Laplacian (needs strong connectivity; citation graphs are DAGs — fails); naive `(A+Aᵀ)/2`
  (discards the co-citation/coupling distinction the magnetic phase keeps). This matches
  edge-dynamics' "combinatorial v1, weighted parked (PD-b)."

**(iii) The (β,z) coupling — one canonical curve; z's bound IS the γ-ceiling.**
`[ESTABLISHED: fable-2026-07-13 walk-family; DERIVED: the coupling ruling]` The family is
two-dial: `K(z,β)=(I−zA^{∘β})⁻¹=Σ_walks z^{|γ|}e^{−βℓ(γ)}`, converging iff `z·ρ(A^{∘β})<1`.
Ruling: **the canonical curve is the one-parameter RSP/free-energy family — β free, z slaved to
the absorbing/killed-walk normalization** (in RSP there is a single temperature θ=β and the
walk-length is not independently damped; convergence comes from the killed structure). Endpoints:
β→∞ = shortest-path (1a), β→0 = commute-time/resistance (1b). The `(β,z)` *plane* is the richer
object — z is a second **resolution knob** (short-walk locality vs long-walk global structure),
the retrieval analog of diffusion-time `t`. **v1 exposes β only** (one dial spans the whole
1a↔1b unification; a second free dial has no falsifier until a retrieval eval set exists —
"no retune off one point"). The (β,z) plane is parked as a resolution axis.

- **The load-bearing tie `[ESTABLISHED: fable-2026-07-13]`:** the convergence condition
  `z·ρ(A^{∘β})<1` is *the same spectral condition* as Invariant-10's γ^d contraction
  (`ρ<1 ⇒ Kleene closure exists ⇒ bounded strata tower`). **The retrieval curve's convergence
  and the strata tower's boundedness are one spectral fact.** The retrieval normalization is
  therefore not free design — z is bounded by the safety invariant that bounds the tower.

**Theorem A1 (well-posedness of the retrieval curve).** `[DERIVED, assembling ESTABLISHED
pieces under the pinned dictionary]` On a finite fiber graph with weights normalized to `(0,1]`,
costs `c=−log w`, and the symmetrized backbone `A_F+A_Fᵀ`: `K(β)` is a well-defined PSD kernel
for all finite β>0, with `lim_{β→0}K(β)=(L_F)⁺` (resistance/commute-time) and `lim_{β→∞}` a
tropical shortest-path *metric* that is generically NOT of negative type (Schoenberg — the phase
boundary, A8). The walk-sum converges iff `z·ρ(A^{∘β})<1` — Invariant-10. *The contribution is
not new mathematics; it is pinning the dictionary so the established interpolation is valid, and
identifying the convergence bound with the γ-ceiling.*

### A2. The two mode-3 operators — formalized, typed, and RE-RANKED (a correction)

Let `X_n` be the citation complex at time n (A4), `C^•(X_n)` its cochains. Supersession `D`
induces a note-correspondence `σ` (P at time n ↦ P′ at n+1).

**Operator σ_* — correspondence-transport (the connection / parallel transport).**
- Def: pushforward `(σ_*φ)(v')=Σ_{σ(v)=v'}φ(v)`; its adjoint is the pullback
  `(σ^*ψ)(v)=ψ(σv)`.
- Type: a **chain map** `C^•(X_n)→C^•(X_{n+1})`, degree 0, covariant — *iff F1 holds* (A3).
- Preserves: **homology/threads** (transports β₁; harmonic classes get a temporal life) if
  simplicial (F1). Does NOT preserve kernels/metric unless σ is weight-compatible/isometric —
  the two-tier result (A3 Result 3'). Retains superseded content (points *forward*, keeps
  lineage).
- Composition law: `σ_{n→n+2}=σ_{n+1→n+2}∘σ_{n→n+1}` (F2).
- Query: "follow this note/thread forward to its successor" — provenance-forward, evolution.

**Operator π_active — ledger-compression (the reduction to the active view).**
- Def: orthogonal projection `Π=P_active` onto the not-yet-superseded subspace of the ledger.
- Type: a **contraction** (‖Π‖≤1), **idempotent** (`Π²=Π`), NOT a chain map. It is the
  compression of the ledger isometry (A3 Result 4). Destroys superseded content (irreversible).
- Composition law: **does NOT compose functorially** — `Π T^n Π ≠ (ΠTΠ)^n` unless the active
  subspace is ledger-invariant (Sz.-Nagy). *This non-composition is exactly why mode 3 needs the
  ledger:* the active-view dynamics is non-Markovian/has memory, so the honest object is the
  dilation, not the compression.
- Query: "the active view as-of time n, superseded content excluded" — snapshot/state.

**THE CORRECTION (surfaced for the note).** `[DERIVED]` The note (§2.5, Parked table) frames the
two as peers a temporal query must "declare which." They are **not peers.** `π_active` is the
**ambient default** — the active view IS the ledger with superseded content compressed out, i.e.
`π_active` is the operator form of the D-exclusion invariant, applied to *every* non-temporal
query (scope `T=now`). `σ_*` is the **opt-in** deliberate forward-traversal of D (scope
`T=window, E∋D, direction=forward`). So the ruling should read: **`π_active` is always-on
(the default `T=now`); `σ_*`/`σ^*` are what a *temporal* query opts into.** This is cleaner than
"declare which" and is the naming C3 adopts.

**The one canonical composite `[DERIVED]`:** the active-view transport is
`T_active = π_active ∘ σ_* ∘ ι` (embed active into ledger, transport, compress back). This
composite is the contraction whose Sz.-Nagy dilation is `σ_*` on the full ledger (A3 Result 4).

| operator | type | homology | kernel/metric | superseded content | composes functorially | query scope |
|---|---|---|---|---|---|---|
| `σ_*` transport | chain map (F1) | preserves (F1) | preserves iff σ isometric | retains (lineage fwd) | yes (F2) | opt-in temporal |
| `π_active` compression | orthogonal proj / contraction | does NOT preserve | contracts (‖·‖≤1) | destroys (active) | no | ambient default (`T=now`) |

### A3. The §2.5 results — made theorem-grade (hypotheses stated; proven vs sketched)

**Result 1 — Bicomplex ⟺ (F1 ∧ F2). GRADE: PROVEN (modulo stated hypotheses).**
Hypotheses: (H0) supersession is a strict partial order via op-seq (acyclic); (H1) rename-stable
identity (supersession-lifecycle §7 — else lineage forks); (H2) transitive closure is taken as a
definition. Claims:
- `δ_D²=0` follows from H0: poset ⇒ nerve/order-complex ⇒ coboundary²=0.
  `[ESTABLISHED: fable-2026-07-13]`
- The cross-relation `dδ_D=±δ_D d` ⟺ each `σ` is a chain map ⟺ **F1** (simpliciality); the ± is
  Koszul sign bookkeeping. `[ESTABLISHED: simplicial maps induce chain maps]`
- With citation-complex coefficients, `δ_D²=0` additionally needs **F2** (composition:
  `σ_{P→P″}=σ_{P′→P″}∘σ_{P→P′}`) — definitional for version lineage, a *failable* data-integrity
  invariant for claim-level `supersede` ops. `[DERIVED: fable-2026-07-13]`
- So `(C^{p,q},d,δ_D)` is a bicomplex **iff F1 ∧ F2.** The content is the *identification* of F1
  with simpliciality and the localization (Result 2).

**Result 2 — `[d,τ]` supported exactly on severed citations. GRADE: PROVEN (tight).**
`[DERIVED, full computation]` For `τ=σ_*`, on an edge `(u,v)` of `X_n`:
`(dσ_*φ)(u,v)=φ(σv)−φ(σu)` on ALL edges; `(σ_* dφ)(u,v)=(dφ)(σu,σv)=φ(σv)−φ(σu)` **only where
`(σu,σv)` is an edge of `X_{n+1}`.** The difference is
`([d,τ]φ)(u,v)=(φ(σv)−φ(σu))·𝟙[{σu,σv}∉X_{n+1}]` — supported **exactly on severed citations**,
weighted by the potential drop. Hence `‖[d,τ]‖` **IS** the (weighted) citation-carry-forward
failure count, not a proxy. **Now COMPUTABLE on the authored-note citation graph (bp-026).**

**Result 3 — Quillen superconnection with curvature `[d,τ]`. GRADE: PROVEN on the linear time
chain; SKETCH+CITE for fork/merge diamonds.** `[ESTABLISHED frame: Quillen 1985; DERIVED
identification]` On the total complex over a *linear* time chain, `𝔸=d+τ` is a superconnection and
`𝔸²=d²+(dτ+τd)+τ²=[d,τ]+τ²`. **τ²-coherence ⟺ F2** (the two-step composites `σ_{n+1→n+2}σ_{n→n+1}`
must cohere; F2 is exactly that), and then `𝔸²=[d,τ]` = the curvature; **flat ⟺ bicomplex** ⟺ F1.
Homotopy-repair / exact-class condition: non-flatness is the *first* obstruction, not a dead end
— if `[[d,τ]]∈H¹(Hom(C(X_n),C(X_{n+1})))` is **exact** (`[d,τ]=[d,h]` for a homotopy `h∈Hom⁰`),
the corrected differential `d+τ+h` is flat; the true invariant is the *class* `[[d,τ]]`, not the
cochain. The fork/merge (diamond) case needs the homotopy-coherent version
(Bondal–Kapranov twisted complexes / Block dg-modules / Bousfield–Kan homotopy colimit) with
higher `τ_k`; this remains a sketch. **Two distinct curvature layers stay distinct (do NOT merge
in a note):** (i) the superconnection `[d,τ]` on a linear chain; (ii) diamond holonomy on
fork/merge diamonds — and neither is the *static* Forman–Ricci curvature (`curvature.py`), which
is of the static fiber geometry. *Same word, different tensors* `[ANALOGY-demotion:
fable-2026-07-13]`.

**Result 3' — Topological ⊊ metric coherence. GRADE: PROVEN.** `[DERIVED: fable-2026-07-13]`
`σ_*d=dσ_*` (F1) does NOT give `σ_*δ=δσ_*` (adjoints flip variance; needs σ weight-compatible /
isometric). Chain maps transport homology (threads have a temporal life) but not kernels.
Kernel-flatness ⊋ bicomplex-flatness — exactly where PD-b (weighted inner products) becomes a
customer.

**Result 4 — Ledger = Sz.-Nagy isometric dilation of the active-view transport. GRADE: PROVEN
(with the merge wrinkle resolved).** Hypotheses: append-only op-seq store, distinct-ops-
orthonormal convention; active view = a subspace; active transport `T_active=π_active σ_* ι`.
`T_active` is a contraction; by Sz.-Nagy every contraction is the compression of an isometry, and
here the isometric dilation is **concrete — the append-only ledger embedding `H_n↪H_{n+1}`.**
`[ESTABLISHED: Sz.-Nagy 1953; DERIVED identification: fable-2026-07-13]` **Merge resolution
(new):** `σ_*` (pushforward) is a partial isometry *only* if supersession is merge-free
(`‖σ_*‖=√max-fiber>1` under merges). **Pin the canonical dilation to the PULLBACK `σ^*`, which
is always a contraction** (co-isometry of `σ_*`); the ledger isometry dilates it. This removes
the merge caveat cleanly: *"revision destroys structure in the active view; the ledger is the
space in which nothing was destroyed"* is a theorem with the pullback as the active-view
transport.

**Result 5 — strict γ-contraction except at owner promotions. GRADE: PROVEN CONDITIONAL on the
C4 ruling (which this pass makes).** Hypotheses: (a) depth `d` rises monotonically along a
revision thread (I4, mint-time); (b) confidence weight `γ^d·g` (Invariant 10); (c) transport
raises d by ≥1. Then on confidence-weighted cochains `‖σ_* x‖_w ≤ γ‖x‖_w` — a strict
γ-contraction — **except** where an owner promotion *re-anchors* depth `d→d₀` (shallow), which
multiplies the weight by `γ^{d₀−d}>1` (energy injection). `[DERIVED: fable-2026-07-13, contingent
on §4.5]` **The only operation that injects energy is the owner verdict** — "the owner is the only
energy source in the dynamics." This is not merely elegant: **C4 (below) rules that promotion
re-anchors depth *precisely because* the dynamics otherwise has no energy source** and would
flatline. So Result 5 becomes an unconditional theorem once C4 lands.

### A4. Balance-isolation reconciliation — a SEPARATE citation complex, in a SEPARATE home

`[DERIVED; VERIFIED: reference_edges.py:1–83, test_reference_edge_isolation.py]`
The §2.5 temporal math is over a **citation** complex; `hodge.py` builds on the **similarity**
backbone `A=cosine_adjacency(emb)`. These are the two-structural-graphs caveat. Reconciliation:

- **Build a distinct citation complex `X_cite` from `reference_edges.sqlite`** (now doc→doc-live,
  bp-026). Its 0-cells are notes, 1-cells are `corpus_to_corpus` citation edges, and — for the
  bicomplex test — the D-arrows are supersession/version chains. `X_cite` is
  **embedder-independent by construction** (deterministic φ_doc/φ_code parse, no model) — which
  is the whole hinge of the A7 signal-vs-noise discriminator.
- **Isolation is preserved — but with a NEW architectural constraint the fable pass surfaces.**
  The invariant is (a) no instrument result changes when reference edges are added/removed, and
  (b) **`core/complex/**` never imports `reference_edges` (grep-asserted in the isolation
  test).** Therefore **the `X_cite`/temporal module MUST live OUTSIDE `core/complex/`** — else the
  grep-assertion fires. Proposed home: a new `core/temporal/` (or `core/query/`) package that
  *reads* `ReferenceEdgeStore` and *never* touches `A_signed`/`build_complex`. `[DERIVED — this
  is a concrete constraint for the graduating plan; naming it now prevents a builder from
  reflexively putting the citation complex in core/complex/ and reddening the isolation test.]`
- This is edge-dynamics §2.7's "shared mathematics, never shared state" applied one level up:
  two complexes (similarity for static Lane A, citation for temporal), two homes, one
  methodology. The balance math holds no handle to reference_edges; now neither does the
  temporal math reach *into* core/complex/. **Confirmed: it does not violate
  `test_reference_edge_isolation.py`.**

### A5. Hodge/Helmholtz well-definedness on E_geom ⊔ E_disp (dreamer-seed rider 1)

**Question:** is "direction" a genuine gradient/curl-free object, or a metaphor over noise?
**Ruling `[DERIVED, grounded in supersession-lifecycle §1 acyclicity + edge-dynamics §2.2 +
the Thread-B time-collapse capsule]`:**

1. **Do NOT run a single Hodge decomposition over the mixed set E_geom ⊔ E_disp.** E_disp is
   directed/acyclic (a DAG); E_geom is undirected geometry. A single `L₁` over the union would
   (a) conflate two incompatible metrics and (b) let supersession edges into balance-adjacent
   math — violating the E_disp-exclusion invariant (recursive-strata-amendment §2). It is a type
   error, not a decomposition.
2. **The two edge types map onto the two SIDES of Helmholtz — this is the real content.** The
   Thread-B result: the gradient part of an edge 1-form has a scalar potential φ; if φ is a
   time/depth coordinate, its gradient IS time-direction. **E_disp (supersession, a DAG with a
   depth potential) is intrinsically `d₀(depth)` — pure gradient, curl-free, harmonic-free —
   *because* supersession is acyclic (a DAG ⇒ a consistent topological-order potential exists ⇒
   gradient-representable).** E_geom's **harmonic threads (ker L₁)** are, by definition, the part
   with NO potential — the time-INVARIANT structure.
3. **Therefore "direction" is a GENUINE gradient object — not a metaphor — precisely on the
   acyclic dispositional edges**, guaranteed by supersession-acyclicity. It would become
   metaphor-over-noise only if read off (i) the *harmonic* part of E_geom (which has no
   potential) or (ii) a *cyclic* edge set (no consistent potential). The diachronic reader reads
   the E_disp gradient (direction) and the *change* in E_geom's harmonic content across snapshots
   (mode-3 `σ_*`), **never a mixed `L₁`.** Well-posed.

### A6. Temporal-complex well-foundedness beyond acyclicity (rider 2)

`[DERIVED / ESTABLISHED as hypotheses]` Beyond `δ_D²=0` (acyclicity), a genuinely well-founded
temporal complex needs:
1. **Rename-stable identity** (supersession-lifecycle §7): `doc_id=source_path` forks lineage on
   rename → spurious disconnected components. **DATA PREREQUISITE, currently AT RISK in the
   codebase** (the note parks it). This is the one condition not yet met; it gates the diachronic
   reader (B).
2. **F2 as a checked invariant** (composition coherence) — needed for the transitive closure /
   the twisted-complex higher structure, not just for `δ_D²=0`.
3. **No-op re-saves logged as occurrences, not versions** (supersession-lifecycle §7) — else the
   complex accretes spurious identity-arrows. Already handled in the design.
4. **The op-seq WELL-ORDER (stronger than acyclic).** op-seq ∈ ℕ ⇒ the supersession order is
   *well-founded* (every non-empty subset has a minimal element), not merely acyclic — this is
   what makes induction over revision threads terminate. `[DERIVED — this is the "beyond
   acyclicity" the rider asks for: acyclic ⇏ well-founded in general; the ℕ-valued op-seq gives
   well-foundedness for free.]`

### A7. Signal vs noise, one level up — THE LOAD-BEARING discriminator (rider 3)

**The problem:** separate genuine *evolution* (a fiber strengthens because a related note was
added) from *artifact* (a fiber shifts because the embedder was re-run). A diachronic reader that
cannot separate these interprets drift that isn't there — apophenia lifted to the dynamics.

**Resolution — with the INVERSION's own machinery, no new mechanism `[DERIVED, grounded in
self-sensing §2.4 + edge-dynamics §2.5 R1/R2 + reference_edges embedder-independence]`:**

- **The discrete record is content-addressed and exact; the embedding is an INTERPRETED,
  versioned object** (the inversion). So the two change-sources are separated by the
  **interpreter-version coordinate** that self-sensing §2.4 *already mandates*:
  - **Genuine evolution = Δ(content-addressed record) at FIXED interpreter version.**
  - **Artifact = Δ(INTERPRETED object) across interpreter versions at FIXED content** — i.e. a
    re-embed is **a supersession event in the interpreter-version chain** (self-sensing §2.4:
    "the supersession chain is the fossil record of the changing self-model"). It is *already*
    tagged, versioned, attributable. Nothing new is needed to detect it.
- **The embedder-invariant FLOOR is `X_cite`.** The citation complex changes ONLY when content
  changes (deterministic parse, no model) — 100% embedder-independent. So the diachronic reader's
  **primary** signal must be `X_cite` dynamics (`σ_*` transport, `‖[d,τ]‖` over real supersession
  events); the similarity-backbone dynamics is **secondary** and must be interpreter-version-
  controlled.
- **The falsifiable discriminator (the apophenia guard, lifted):** decompose a temporal edge
  change as `Δedge = Δ_content + Δ_interpreter`, where `Δ_interpreter` is measured by re-embedding
  the *old* snapshot's content under the *new* embedder (content held fixed). **A drift/direction
  claim is admissible only when `‖Δ_content‖ ≫ ‖Δ_interpreter‖` — the change must survive holding
  the interpreter fixed.** If the shift is explained by the re-embed alone, the reader emits
  **nothing** (edge-dynamics' honest-seam pattern, `change_point` precedent). Equivalently, in the
  inversion's rule R2: **the exact discrete invariants (β₁ of X_cite, `dim ker L₁`, the
  content-addressed node/edge set) are the FALSIFIERS for the continuous drift reading — a drift
  claim that moves no exact discrete invariant is embedding noise.** This closes rider 3 with the
  inversion's own falsifier discipline; it is the ADDED Track-D entry gate (D, gate 4).

### A8. β* — resolved from conjecture to a theorem-with-graph-constant

`[DERIVED, via continuity of β↦d_β + closedness of the negative-type cone + Schoenberg]` The prior
capsule conjectured β* finite on sparse citation graphs. Resolution:

- Negative-type is a **closed** condition (the negative-type metrics form a closed convex cone,
  stable under pointwise limits). The free-energy distance `d_β` deforms *continuously* from the
  resistance metric (β→0, which IS negative-type — resistance distance is squared-Euclidean) to
  the shortest-path metric (β→∞).
- **Theorem:** `β* := sup{β≥0 : d_β is of negative type}` is **finite iff the shortest-path metric
  `d_∞` is NOT of negative type.** Proof: if all large β were negative-type, closedness would
  force the limit `d_∞` negative-type — contradiction. So `d_∞` not-negative-type ⇒ β* < ∞, and
  for β>β* the metric-kernel `e^{−s d_β}` is not PSD (kernel-*representability of the distance* is
  lost).
- **When is `d_∞` not negative-type?** Whenever the graph contains an isometric cycle `C_{≥4}`
  (e.g. `C_4`'s shortest-path metric is not of negative type) — **generic for any sparse citation
  graph with cyclic citation structure.** Trees / block graphs are the negative-type exception
  (β*=∞), matching the prior capsule.
- **A required sharpening the note must adopt `[DERIVED]`:** distinguish two "kernel" notions.
  **For all finite β the RSP KERNEL `K(β)` is PSD** (an honest kernel). What is lost at β* is only
  the ability to realize the free-energy *DISTANCE* `d_β` as a Hilbert-space metric via
  `e^{−s d_β}` (Schoenberg negative-type). The phase transition is about the *metric's*
  negative-type, **not** the RSP kernel's PSD-ness. Conflating them would be a real error in a
  successor note.
- The **exact** β* is graph-dependent and computable by the prior capsule's sweep
  (sweep β, watch `λ_min(e^{−d_β})`) — **now runnable on the authored-note citation metric
  (bp-026)**; its *finiteness* is now proven, not conjectured.

### A-register — the "untestable today" list is REVISED (bp-026)

`[VERIFIED: bp-026 complete]` Now computable on the **authored-note** citation graph: `‖[d,τ]‖`
flatness over real supersession events; the F2-violation count; diamond holonomy; the
negative-type β* sweep on the citation metric; the citation-side alignment of `K_sem`. **Still
blocked:** build-plan `design_ref` targets (the residual doc→doc gap per PROGRESS 2026-07-13) —
so supersession/citation coverage over the *build-plane* artifacts is incomplete. **Still
correctly deferred:** anything needing the versioned edge-strength series (self-sensing B-a/B-b,
not yet built). The math no longer merely "doubles the warrant for the extractor" — the extractor
LANDED; the math is now an empirical program that can start on authored notes.

---

## B. THE DIACHRONIC-DREAMER RULING

**Does the temporal/Hodge structure support the dreamer reading the graph's direction/velocity,
not only its state?** YES — but *only* with the A7 discriminator in force (A5 makes "direction" a
genuine gradient object on the acyclic E_disp; A7 keeps it from reading embedding noise; A6 names
the well-foundedness prerequisite).

**RULING B: a DISTINCT DIACHRONIC INTERPRETER, not a second mode of the synchronic dreamer.**
`[DERIVED design ruling; grounds in interpreters.py:1–33, 28–29; edge-dynamics §2.1; provenance.py;
dreamer-direction grounding]`

1. **Different input domain.** The synchronic dreamer (`interpreters.py`) reads `G_MR` — ONE
   MirrorView snapshot, authored-only, embedder-mediated. The diachronic reader needs a
   *sequence* of snapshots + `X_cite` + supersession/version chains. The lens signature must
   **generalize** `φ_i : G_MR → 2^K` to a temporal-context input — a contract *extension*, not a
   mode flag.
2. **The codebase already left the temporal-shaped hole.** `change_point` is a *registered but
   DEFERRED* seam that "returns nothing rather than fake a trend" because "MirrorView does not yet
   carry a per-note temporal axis" (`interpreters.py:28–29`). The diachronic interpreter is what
   unblocks that seam — by reading a *different* substrate, not by bolting time onto MirrorView.
   **The architecture anticipated this split.** `[ESTABLISHED — strongest single argument.]`
3. **The Lane A/B firewall forces the split.** edge-dynamics §2.1: "Lane A never reads observed
   data; Lane B never touches the mirror-side dream path." A reader of the *dynamics* is Lane B /
   correlator-class (reads `ObservedView`, emits INTERPRETED, dreamer-proposed authority). Folding
   it into the mirror dreamer would cross the firewall.
4. **Two tiers (a needed refinement).** `X_cite` over authored notes is **corpus-structural**
   (who-cites-what), the very class §2.4/C1 rules mirror-safe — so a *mirror-safe X_cite-dynamics
   tier* can ship earlier. The *weaving through observed planes* (cost/documentation/scope) is
   the Lane-B tier = the Track D charter (D). **The diachronic interpreter has a corpus-structural
   tier (earlier) and a Lane-B weaving tier (Track D, gated).**
5. **Lens contract still binds (either tier):** `Claim(statement, support ⊆ authored notes)`,
   model-free (§9 deterministic floor), no in-lens adjudication (R1 adjudicates), lands INTERPRETED
   (the `derives` hyperedge, `provenance='interpreted'`, INTERPRETED ∉ MIRROR_READABLE), zero
   back-action, erasure-invariant, verdict/promotion-gated via `core/provenance.py` (`promote()`
   stub — owner verdict only; a drift claim can NEVER silently become a belief).

**Rejected — a second mode of the same dreamer:** it would (a) force MirrorView to carry a
temporal axis (breaking the single-snapshot contract the `change_point` deferral protects),
(b) risk crossing the Lane A/B firewall, (c) conflate two input domains under one signature.
Named and rejected.

**The recursion resolved.** The dreamer already surfaced, from the owner's own notes, "should the
founding corpus be a fixed anchor, or is its transformation the phenomenon to track?" — and the
owner asks whether the dreamer should *become* that instrument. My ruling makes it concrete: **the
diachronic interpreter tracks the *transformation of corpus STRUCTURE* (`X_cite` dynamics,
supersession) and PROPOSES (INTERPRETED) readings of it — but the founding corpus itself stays a
fixed anchor** (non-negotiable #9: fixed points are never auto-modified; owner-only). The
instrument tracks the drift; it never touches the fixed point. `[DERIVED — clean resolution of the
recursion via non-negotiable #9 + the back-action line.]`

---

## C. THE §1.3 OPUS-PROVISIONAL FINALIZATIONS

### C1. §2.4 sacred-boundary ruling — CORRECTED toward capability-DISSOLUTION (highest stakes)

The opus ruling: expose the reference stratum "as a capability scope, not a special case";
permitted `read(reference, F, {ref_type,source_line,path})`, denied node payloads / observed
exhaust / content-leaking D-traversal. **My vet: right in spirit, but one step short of
the-sacred-boundary's own test. I correct it.** `[DERIVED; VERIFIED: reference_edges.py schema
(no content column), :62–63 vault-digest reservation; the-sacred-boundary §3]`

1. **The schema-level claim is CORRECT.** `reference_edges.sqlite` holds only
   `edge_id, commit_sha, endpoints (path/qualname/ref/detail), ref_type, source_line` — **no
   payload, no note text, no embeddings.** It is pure structure. ✓ So "corpus-structural, not the
   mirror's contents" holds at the schema level.
2. **The DECISIVE argument the opus draft underweights — information-equivalence to repo-grep.**
   For edges over `docs/**` + code, the citation graph is **derivable from the repo the build-time
   plane already holds** (that is literally what the §2.6 self-grading oracle does — repo-grep at
   HEAD). So a build-time reference query over in-repo edges adds **zero** information the plane
   cannot already compute. The grep-oracle *is* the proof of information-equivalence.
3. **The RESIDUAL the opus ruling misses — vault-backed edges.** `reference_edges.py:62–63`
   reserves `detail=digest` for **vault-note targets** (private notes NOT in the repo). Today
   none exist (every minted edge is over the repo, `detail=''`). But a *future* vault-citation
   edge would leak the citation structure of private notes — which is NOT repo-derivable. So the
   permitted-scope predicate must be tightened from "structural metadata" to
   **"repo-derivable edges only (both endpoints in `docs/**`+code, never vault-backed)."** This is
   a strictly cleaner test — it is the plane-crossing test made concrete: *the build-time plane may
   read exactly what it could already compute from the repo it holds.*
4. **THE CORRECTION — dissolve the crossing, do not scope it.** the-sacred-boundary §3: *"If a
   design still requires the dangerous permission, the boundary is in the wrong place. Keep moving
   the boundary until the permission is unnecessary."* The opus ruling *grants* a scoped read into
   the live daemon's sealed store. But the read is **unnecessary**: the build-time plane can
   **rebuild the identical reference index locally** from the repo (deterministic φ_doc/φ_code) —
   bit-identical to the sealed store for in-repo edges, and **structurally incapable of seeing
   vault-backed edges** (they're not in the repo). **Ruling: the build-time plane queries a LOCAL
   repo-derived twin, never a handle into the live sealed store.** This (a) dissolves the
   plane-crossing (no sealed-store handle — faithful to non-negotiables #1/#2), (b) is
   information-equivalent for in-repo edges, (c) cannot leak vault structure by construction. The
   "duplicates the sensor" objection (the brainstorm's rejected alternative) *dissolves*, because
   determinism makes the twin free and **self-verifying — the §2.6 grep-oracle is exactly the
   continuous proof that the twin ≡ the sealed store for in-repo edges.** The workflow gets full
   dogfooding AND zero crossing.
5. **In-CORE clients are unaffected.** The Ambassador / dreamer legitimately live inside the core;
   their read of the live reference stratum is *not* a crossing. The correction re-homes only the
   *build-time* plane's access.

**Net:** CONFIRM the opus direction (scope, not special-case) but CORRECT the mechanism from
"scoped cross-boundary read" to "local repo-derived twin (capability-dissolution)," and SHARPEN
the predicate to "repo-derivable only." → **OWNER DECISION (low-stakes residual):** does the owner
accept even the repo-derivable citation graph being queryable by a delegated/worktree build-time
context, given it is already `grep`-able? (Recommendation: yes — information-equivalent; the twin
adds convenience, not exposure.)

### C2. §2.1 the scope grammar — made fable-grade (a bounded lattice)

`[DERIVED; grounds in MirrorView/ObservedView constructor-enforcement; non-negotiable #6;
CLAUDE.md write-discipline]` A scope is a 4-tuple `s=(Σ,E,T,A)`:
- `Σ ⊆ Strata` (mirror, curated, observed, ops, reference[_repo], build-plane, …);
- `E ⊆ {F,D}` (fibers, dispositional);
- `T ∈ {now} ∪ {[t₀,t₁]} ∪ {ledger}` (active snapshot / window / dilation space) — `now` applies
  `π_active`, `ledger` is the dilation (A2/A4);
- `A ∈ {read < read+propose < write}`, a total order.

**Composition = a bounded LATTICE:**
- **Meet** `s₁⊓s₂ = (Σ₁∩Σ₂, E₁∩E₂, T₁∩T₂, min(A₁,A₂))` — the safe composition; a delegated
  sub-agent gets the **meet** of its own and its parent's scope.
- **Join** `s₁⊔s₂ = (∪,∪,∪,max)` — a *widening*. **NOT freely grantable:** a scope can be widened
  only by an authority that already HOLDS the wider scope (**monotone delegation** — you cannot
  delegate more than you have). *This law IS non-negotiable #6* ("minted agents can't exceed their
  template's scope or a pre-declared max"). `[DERIVED — the constitutional rule and the lattice law
  are the same statement.]`
- **⊥** `=(∅,∅,∅,read)` (no access); **⊤** = full-core, and **even ⊤ respects the foundation
  denylist** (`CONSTITUTION.md`, `eval/golden/**`) — a hard forbidden region in every writable Σ.

**Structural enforcement (not by convention):**
- Each client is **constructed** with a scope; a query is a well-typed sentence whose required
  capability must be `⊑` the client's granted scope; ill-scoped queries are **unrepresentable** (a
  type/constructor error) — exactly as `MirrorView` makes a non-authored read unrepresentable.
  **The existing Views ARE the partial instances:** `MirrorView ≈ (mirror-authored, F, now, read)`,
  `ObservedView ≈ (observed, *, *, read)`, `EffectView ≈ (—, —, —, write-to-world-under-gate)`. The
  grammar is their common generalization; the constructor-enforcement they already have is the
  boundary mechanism.
- **Firewalls = forbidden-region ideals checked by meet.** Mirror firewall: any scope whose Σ
  includes mirror-*payload* meets to ⊥ for non-mirror clients. **D-exclusion = a TYPE constraint:**
  a mode-1 grounding query is *typed* `E={F}` and cannot name `D` (the fable capsule's "infinite
  cost on D," now a type — D-exclusion is `E={F}` being the only well-typed grounding scope). **C1
  = a stratum refinement** `reference_repo ⊂ reference` (repo-derivable sub-stratum only for the
  build-plane).

This is fable-grade: a bounded lattice; meet = safe composition; join = widening-requires-holding;
constructor-enforcement makes ill-scoped queries unrepresentable; forbidden ideals encode the
firewalls; monotone delegation = non-negotiable #6; the denylist = a hard ⊥ even ⊤ honors.

### C3. §2.3/§2.5 surface shapes

- **ReferenceView (library object), NOT an addressable service — v1.** `[DERIVED, forced by C1]`
  Consistency with the existing library-object Views; the scope grammar makes a View a
  scope-parametrized handle (`ReferenceView ≈ (reference_repo, F, now, read)`); and **C1 forces
  it** — the build-time plane holds a LOCAL repo-derived index, so a `ReferenceView` over that
  local twin is a library object with no daemon handle. A cross-process *service* would
  re-introduce the very crossing C1 dissolved. The addressable-service shape is the parked upgrade
  for the *in-core* clients (Ambassador/dreamer over the live stratum) — a runtime concern, not the
  build-time archetype.
- **Naming/typing the two mode-3 operators (from A2):**
  - `π_active` — **the active-view projection** (ledger-compression), the **ambient default**
    (`T=now`); it is the operator form of D-exclusion, applied to every non-temporal query.
  - `σ_*` — **`transport_forward`** (follow D to successors), the opt-in temporal operator; and
    `σ^*` — **`transport_back`** (pull from predecessors), the merge-safe contraction (A4).
  - **Typing ruling:** `T=now` silently applies `π_active`; a temporal query opts into transport
    by declaring `T=window, E∋D, direction∈{forward=σ_*, backward=σ^*}`. (This is the A2 correction
    over the note's "declare which": `π_active` is not a peer to declare — it is the default.)

### C4. §4.5 dichotomy — RULED: promotion RE-ANCHORS depth

`[DERIVED design ruling; the dynamics (A3 Result 5) + non-negotiables #3/#5/#9 jointly force it]`
**RULING: a `promote` verdict re-anchors the claim's stratum depth (raises the γ^d ceiling) — the
contractive-except-at-owner-verdicts branch.** Justification:

1. **The dynamics leaves no other option if the corpus is not to flatline.** Unconditional
   contraction ⇒ every trajectory decays to zero ⇒ the system is a pure dissipator ⇒ *no* insight
   can ever rise ⇒ the corpus asymptotically forgets. A knowledge system needs an energy source,
   and the constitution says the owner is the only legitimate one. So the owner verdict **must** be
   the energy injection — i.e. promotion re-anchors depth. (Result 5 becomes an unconditional
   theorem under this ruling.)
2. **Constitution-aligned.** "The owner is the only energy source in the dynamics" is exactly
   non-negotiables #3/#5/#9 (self-reference cannot amplify itself; only a human verdict lifts).
   Unconditional contraction would make the owner verdict *powerless* to rescue a genuinely good
   late-reached claim — misaligned with owner sovereignty over promotion.
3. **Clean semantic justification.** On promotion, the claim's authority-source *changes* from its
   derivation (depth = derivation-distance proxy) to the owner verdict. So its depth *should*
   re-anchor to the verdict, not stay pinned to the birth cycle — anchoring a blessed claim's
   authority to how many cycles it took to reach is the bug.

**Rejected (unconditional contraction):** makes the system a pure dissipator, permanently damps
genuine deep insight, renders the owner verdict unable to rescue late-reached truth. Named,
rejected.

**OWNER DECISION (residual):** *how far* does re-anchoring go? Recommendation `[INFERENCE]`:
re-anchor to the **shallowest DERIVED level** (promoted-derived / `DERIVED_STRATUM`), NOT to
authored-K₀ depth 0 — because a promoted derived claim is owner-*blessed* but still derived-origin
(`provenance.py: DERIVED_STRATUM` — "trusted as to ORIGIN … untrusted as to TRUTH … NEVER
mirror-readable"). This lifts the γ^d cap (energy injected) while keeping the derived/authored
firewall intact (promotion is authority-lift, never a masquerade as owner-authored). The exact d₀
is owner taste.

### C5. One note or two — DECIDED: TWO successors; the algebra does NOT fold into edge-dynamics

`[DERIVED design ruling]`
1. **edge-dynamics is RATIFIED (A8-immutable) — "fold into Lane B" is not actually available**
   without *superseding* the ratified note (a heavy owner act). The formalized algebra must enter
   as a NEW note regardless.
2. **Distinct subject / distinct firewall side.** Lane A = static Hodge on the *similarity*
   backbone (mirror-side, snapshot). The temporal algebra = the *citation*-complex dynamics (A4, a
   different graph, a different home) + the retrieval curve (neither Lane A nor B — the
   core-query-protocol's own math) + mode-3 transport. The prior capsule's explicit instruction —
   "same word, different tensors; a design note must not merge the sections" (static Forman–Ricci
   vs temporal `[d,τ]`) — is a direct DON'T-MERGE.
3. **The full split is THREE notes:** (1) `dn-core-query-protocol` (**architecture** — already
   drafted; absorbs the diachronic-reader **ruling B**, the scope grammar **C2**, the boundary
   **C1**); (2) a **math successor** (proposed `dn-temporal-retrieval-algebra`, serving *both*
   core-query-protocol §2.5 and edge-dynamics Lane B — absorbs **A1–A8**); (3) the **Track D
   weaving-consumer charter** (edge-dynamics §2.6 already says "a separate note the owner ratifies"
   — absorbs **D**). The math successor is a NEW file, cross-linked as Lane B's math home, **never
   an edit to ratified edge-dynamics.**

---

## D. THE TRACK D WEAVING-CONSUMER CHARTER (charter, not license — stays gated)

`[ESTABLISHED: edge-dynamics §2.6, §2.1; self-sensing §5; supersession-lifecycle §3; provenance.py;
DERIVED: gate 4]`

- **READS:** `ObservedView` (cost φ_self, documentation, scope-of-change/churn planes), the
  versioned edge-strength series (self-sensing B-a chains), the supersession/version chains
  (ledger), and — the corpus-structural tier (B) — `X_cite` (repo-derivable, mirror-safe, C1). It
  reads the **dynamics** (trajectories), **NEVER** the mirror-side dream path, authored payload, or
  `MIRROR_READABLE` rows.
- **EMITS:** INTERPRETED proposals **only** (`Claim(statement, support ⊆ authored notes)`,
  dreamer-proposed authority) — each a `derives` hyperedge, `provenance='interpreted'`, INTERPRETED
  ∉ MIRROR_READABLE, verdict/promotion-gated to ever become authored (`core/provenance.py`
  `promote()` — owner verdict only). Claims are diachronic ("this thread consolidates across
  cost+documentation planes"; "this fiber is strengthening — content-addressed, survived the A7
  discriminator"). **Zero back-action; erasure-invariant.**
- **ADJUDICATION:** the SAME R1 adjudicator as the synchronic panel (no self-blessing);
  diagnostic / mirror-not-oracle. A proposal touching *blessed* content routes through the
  supersession-lifecycle §3 blessing gate (owner verdict to demote/supersede). A weaving claim is
  INTERPRETED — it stays in the dream lane, never side-channels into the artifact chain as a
  design/direction finding.
- **ENTRY GATES — the §2.6 three + the §2.5 ladder R1 + the A7 discriminator (fourth, added):**
  1. **Substrate exists** — self-sensing B-a + B-b built and attested; the observed planes
     accumulate.
  2. **Sample depth clears the rung** — §2.5 ladder; **first rung is R1** (smoothing splines/GP per
     edge series → measured momentum `p`), **not R4** (learned action). No Hamiltonian on five
     commits.
  3. **Track D design pass drafts the charter** as a separate owner-ratified note; §2.5 discipline
     binds by reference.
  4. **[ADDED by this fable pass] The A7 signal-vs-noise discriminator is implemented and
     enforced** — the consumer subtracts interpreter-artifact (re-embed) drift, reads only
     content-addressed / exact-invariant-moving evolution, and **returns nothing on
     interpreter-artifact-dominated change** (honest-seam, lifted). **Without this gate the weaving
     consumer is an apophenia engine.** This is the pass's material addition to §2.6.
- **First-rung deliverable & razor:** R1 splines over the observed edge-strength series → the phase
  point `(q,p)`. Three-clause razor: *measures* whether threads genuinely weave across observed
  planes; *valid when* the A7 discriminator holds and the trajectory clears R1; *fails its keep if*
  the weave is embedding noise or no cross-plane thread has persistence. **Charter grants no build**
  until all four gates are green and the owner ratifies the charter note.

---

## OWNER-DECISION items (surfaced, not resolved)

1. **C1 residual (low stakes):** accept the repo-derivable citation graph being queryable by a
   delegated/worktree build-time context, given it is already `grep`-able? (Rec: yes.)
2. **C4 residual:** the re-anchoring depth `d₀` on promotion — shallowest-derived (rec) vs
   all-the-way-to-K₀-depth-0. Taste + firewall call.
3. **A1(ii) upgrade timing:** adopt the magnetic Laplacian `L^{(q)}` (directed diffusion) — this is
   PD-b's "second customer"; when does directed *diffusion* (not just directed reachability) earn
   the weighted-inner-product tier?
4. **B / A6 prerequisite:** the diachronic reader depends on **rename-stable identity**
   (supersession-lifecycle §7, currently `doc_id=source_path`, at risk). Owner call on prioritizing
   the uuid-stable-identity work before the diachronic reader graduates.
5. **The evolution study** (edge-dynamics §5, self-sensing §5 open q): does it formally adopt the
   phase-space axis (q from snapshots, measured p from B-a chains) and the epistemology axis? Owner
   call at the math-successor's ratification.

## Open questions / what a follow-up pass needs

- **Empirical (now unblocked, bp-026):** run the `‖[d,τ]‖` flatness, the F2-violation count, and
  the β* sweep on the **authored-note** citation metric; these were "untestable today" and are not
  anymore. A Thread-C sweep can start.
- **Build-plane coverage gap:** build-plan `design_ref` targets are still doc→doc-blind (PROGRESS
  2026-07-13) — the supersession/citation math over the *build-plane* is incomplete until that
  residual extractor lands.
- **Architectural constraint for graduation (A4):** the `X_cite`/temporal module must live OUTSIDE
  `core/complex/` (the isolation grep) — a builder must not reflexively home it there.
- **The homotopy-coherent (diamond) superconnection** (A3 Result 3) is a sketch+cite, not proven;
  a follow-up could make the twisted-complex `τ_k` structure rigorous if fork/merge supersession
  diamonds turn out common on the real corpus (measure diamond frequency first).
- **The (β,z) plane's resolution axis** (A1 iii) is parked; it re-enters when a retrieval eval set
  gives z a falsifier.
