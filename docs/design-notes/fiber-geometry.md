---
type: design-note
id: dn-fiber-geometry
track: fiber-geometry
status: ratified               # draft → ratified → superseded.  draft→ratified is an OWNER-ONLY hand edit.
implementation: design-only # nothing built; decides layers/rulings/measurements, licenses one survey
created: 2026-07-21
updated: 2026-07-21
links:
  - docs/brainstorms/edge-dynamics-vector-field.md   # WARRANT — three fields, the coupling, the sheaf question (PD-a's candidate customer)
  - docs/brainstorms/fiber-chain-grammar.md          # WARRANT — the language over the fiber alphabet; chain-as-sentence semantics
  - docs/brainstorms/clock-curvature.md              # WARRANT — metric distortion, phase model, path-invariance map, vocabulary ruling
  - docs/design-notes/edge-dynamics.md               # RATIFIED — §2.2 Hodge, §2.5 R-ladder/inversion, PD-a/PD-b/PD-c (extended, never edited)
  - docs/design-notes/magnetic-laplacian.md          # RATIFIED — §2.2 Hasse triangle-freeness, §2.3 refutation, §2.6 ledger, ML-a/ML-d (honored)
  - docs/design-notes/capability-scope-algebra.md    # RATIFIED — E at :65; mode-as-corollary-of-scope (§2.4) — the S-letter's capability home
  - docs/design-notes/agent-taxonomy.md              # RATIFIED — §2.2 grounding law (E_proven ∪ E_sim); fiber C; F = citation (:206-210)
  - docs/design-notes/connectivity-instruments.md    # RATIFIED — CN-1..7; CN-4 sign law; CN-5 running meet; CN-7 label-setting
  - docs/design-notes/velocity-instruments.md        # RATIFIED — X1–X3 typing; VI-b alive/stale holes; the V2 POD repair
  - docs/design-notes/synchronic-diachronic-dreamer.md  # RATIFIED — §2.4 laziness laws, §2.8 arrow-read, §2.9 oq-0021, F-SD9
  - docs/design-notes/temporal-retrieval-algebra.md  # RATIFIED — [d,τ], TA-c (unclosed), §2.5 contraction
  - docs/findings/finding-0140.md                    # filed by this pass — the fiber-letter collision in the 2026-07-21 brainstorm layer
supersedes: null
superseded_by: null
warrant: docs/brainstorms/edge-dynamics-vector-field.md
---

# Fiber geometry — one typed graph, three layers: grammar, geometry, dynamics

> Composed at **fable** (`claude-fable-5`, 2026-07-21, session-39 dispatched design pass — the
> owner's directed synthesis over the four open threads). Filed as `draft`; ratification is an
> owner-only hand edit; `/graduate` refuses this note until `status: ratified`. **Design only; no
> build is authorized beyond the read-only survey named in §3.** Every nontrivial claim carries a
> grade (`[ESTABLISHED]`/`[DERIVED]`/`[INFERENCE]`/`[ANALOGY]`, the house discipline from
> `dn-magnetic-laplacian`); external-literature claims are flagged `[FROM MEMORY]` for the
> external-grounding gate. Ratified notes are cited, never edited (A8). Code claims were verified
> on disk this session (worktree at `8be3c98`).

## 1. Purpose and scope

Four threads accumulated without a synthesis: (1) *three vector fields, one per fiber*, their
coupling, and the sheaf/bundle-Laplacian question (`edge-dynamics-vector-field.md`, the PD-a
candidate customer); (2) *the fiber-chain grammar* — a language of admissible chains, and the
chain-as-sentence semantics (`fiber-chain-grammar.md`); (3) *clock curvature* — churn distorting
the routing metric, the hot/cold phase model, the GR framing (`clock-curvature.md`); (4) the
ratified **edge-dynamics track** they all extend (`dn-edge-dynamics`: Hodge, the R-ladder, the
inversion; PD-a and PD-c parked "awaiting a customer").

This note decides: the canonical alphabet and the fiber ledger (§2.0); the unifying structure
and exactly how strong it is (§2.1); the fields, made honest per class (§2.2); the grammar
layer (§2.3); the clock-curvature ruling the owner asked for — dead end or load-bearing (§2.4);
the operator decision — sheaf vs independent runs, made a *measured* decision (§2.5); the
consolidated measure-first battery (§2.6); and the reconciliation with every ratified note
touched (§2.7, plus rulings inline).

**Out of scope, explicitly:** relitigating the ML-a operator deferral (ratified; honored
verbatim); any change to `sigma_star`/`conductance`/`composed` machinery (their designs are
ratified; this note calibrates and consumes); the Track-D correlator charter; diachronic
execution (SD-a's park stands); any build beyond §3's read-only survey.

## 2. Principles / decisions

### 2.0 FG-0 — the fiber ledger, and the canonical move alphabet (vocabulary hygiene first)

The house now uses "fiber" in **four distinct senses**, and the 2026-07-21 brainstorm layer
additionally used the letter **F for two different edge classes**. Both must be pinned before
any coupling/grammar/curvature claim is well-posed (the same prophylactic move as the
flux≠Ricci ledger, ML §2.6).

**The four senses of "fiber" (ledger — none is the others):**

| sense | object | home |
|---|---|---|
| edge-class fiber | `E ⊆ {F, D, C}` — dispositional edge classes in a scope grant | `core/scope.py:155-188`; dn-agent-taxonomy §2.5 |
| σ-fiber | a claim's persistence fiber across the σ-filtration (`ClaimFiber`) | dn-sigma-fibers; `eval/harness/fibers.py` |
| projection fiber | layer tissue `φ_i⁻¹` — a derived record's source records | dn-agent-taxonomy (:155-167), fibrational, re-derivable |
| bundle fiber | the stalk of a candidate sheaf/bundle over the shared node set | the PD-a object this note rules on (§2.5) |

**The letter collision, resolved (finding-0140).** The ratified/built alphabet is:
**F = citation/warrant** edges (`core/scope.py:158` — "F = citation, D = supersession,
C = causal-witnessed"; dn-agent-taxonomy :206-210; ReferenceView's grant is `E={F}` over
`X_cite`). The three 2026-07-21 brainstorm capsules instead used F for **similarity** ("w_F
(similarity strengths)"; "F is dense, ~undirected, cosine-weighted"; "F*·(C|D)" glossed as
"similarity hops"). Similarity is **not an E-fiber at all** in the ratified algebra: cosine
edges are computed from the embedding kernel, and semantic reading is licensed by
*kernel-carrying Σ*, not by an E letter (dn-capability-scope §2.4 — "mode is a corollary of
scope"). `[DERIVED — from the ratified mode table + the built EdgeScope]`

**Decision (FG-0): the canonical chain-move alphabet is Σ_move = {S, F, D, C}**, four move
types over one node set at a certified cut:

| letter | edge class | structure | provenance | live population (2026-07-21, honest) |
|---|---|---|---|---|
| **S** | similarity (`E_sim`) | dense, undirected, weighted (cosine) | **computed** (kernel; embedder-versioned, A7) | real — the σ-graph, the MST/conductance substrate |
| **F** | citation (`X_cite`) | sparse, directed | **recorded** (`reference_edges`, commit-keyed) | real — ~234 distinct doc→doc pairs at the July census; grown since |
| **D** | supersession | sparse, directed, acyclic (Hasse) | **recorded** (versions; append-only) | real — the version chains; the event clock's residue |
| **C** | causal-witnessed (`E_proven`) | sparse, directed, witnessed, weight 1.0 | **recorded + proven** (integrator; `composed.py:70`) | **thin** — witnessed co-production only (`eval/harness/re_measure.py`); the live census read came back empty (bp-080 seal) |

The capability projection: the scope algebra's `E` covers the *recorded* sub-alphabet
{F, D, C} unchanged (`capability-scope-algebra.md:65` extended additively by dn-agent-taxonomy);
S-moves are capability-licensed by kernel-in-Σ. Nothing in the ratified algebra changes; the
brainstorm claims re-read under this alphabet (the "F↔C mismatch field" is the **S↔C** mismatch
field, etc. — corrected throughout below). The staged overlay class (`E_STAGED`,
`composed.py:53`) is an overlay of these classes, not a fifth letter.

*Falsifier:* an artifact after this note using an alphabet letter against this table (in
particular F-for-similarity) is malformed and gets corrected at review, not accommodated.

### 2.1 FG-1 — the unifying structure: three layers over one typed graph (the thesis, graded)

**The common substrate is real and singular:** one node set at a certified cut, four edge
classes (§2.0). The four threads are not four objects; they are **three layers of readings of
this one object**, plus the discipline that binds them:

- **Layer 0 — GRAMMAR (membership; hard; discrete).** Which move-sequences are *well-formed*:
  the language L over Σ_move (§2.3). Boolean, order-aware, capability ∩ epistemics.
- **Layer 1 — GEOMETRY (ranking; soft; the weights as state).** The edge weights w define the
  metric/measure structure: σ* (bottleneck ultrametric), the (σ,t) conductance profile,
  Forman/Ollivier curvature, the CN-4 change-of-measure. Ranking among admissible chains is a
  variational problem over this geometry (§2.4).
- **Layer 2 — DYNAMICS (evolution; the weights' change on the D-clock).** Velocities, minting
  intensities, the R-ladder's fitted operators — the trajectory of the Layer-1 state, with the
  D-fiber's event stream as the clock (§2.2). Feeds back into Layer 1 exactly once, through
  CN-4's churn exponent (the thermal term).

They compose as **constrained optimization: prune to L, then rank the survivors** — the
brainstorm's membership/ranking split, adopted. `[DERIVED]` And the composition is not new
architecture; the ratified instruments already implement its special cases:

- **CN-5's running scope-meet IS the commutative special case of the product-automaton walk.**
  The running meet is a finite-semilattice state carried along the path; "meet stays
  admissible" is a regular condition whose automaton states are scope values and whose
  transitions are meets. The general grammar replaces the semilattice by an arbitrary finite
  automaton — the meet's *commutativity* is exactly what the `[d,τ]` non-commutativity
  (ML §2.3) says is too coarse for order-aware admissibility. `[DERIVED]`
- **CN-7's label-setting over (node, accumulated-scope) states generalizes verbatim to
  (node, automaton-state).** Dominance pruning weakens from order-dominance (scopes only
  narrow) to exact-state coincidence, which is the standard regular-path-query evaluation
  `[FROM MEMORY — Mendelzon–Wood; RPQ product construction]`; soundness/completeness of
  label-setting over the finite product is unchanged. Design directive: when CN-5/CN-7
  graduate to a build, the composability state should be typed as the general automaton state
  from day one, with the scope-meet as its first instance — one build, both layers.

**The bridge between Layer 1 and Layer 2 — stated precisely, because the tempting version is a
category slip.** The candidate spine "gradient = conductive = the ranking metric" conflates two
roles of w. Honest version:

1. **w plays two roles: metric and complex.** As *metric/measure*, w is what conductance and
   curvature are functionals **of**. As *complex*, w's support carries cochains — flows,
   velocities `ẇ` — which the Hodge machinery (edge-dynamics §2.2, built `core/complex/hodge.py`)
   decomposes **over** it. The state is the geometry; the fields are its change and its flows.
2. **Where "gradient = conductive" is exactly true:** for transport. The energy-minimizing
   current flow between two nodes satisfies the cycle law `i = W·d₀φ` — it is a weighted-gradient
   flow, and its cycle-space (curl ⊕ harmonic) component vanishes in the resistance-weighted
   inner product (Thomson/Dirichlet principle `[ESTABLISHED — FROM MEMORY; verify]`). So **all
   through-put between endpoints is carried by the (weighted) gradient subspace; circulation
   transports nothing** — which is the precise content of "the harmonic part is the conductivity
   deficit": circulation in a strength or velocity field is structure no node potential
   explains, and it moves nothing between endpoints. `[DERIVED, given the flagged principle]`
3. **The caveat that names a PD-b customer:** the built `hodge.py` projectors use the
   *combinatorial* (unweighted) inner product (PD-b parked, edge-dynamics §4). The exact
   transport identification of (2) lives in the **weighted** inner product. If the survey's
   Hodge readings (§2.6 M4) are consumed quantitatively for conductance attribution, that is
   PD-b's re-entry ("harmonic representatives too delocalized" generalized to "the unweighted
   split misattributes transport"). Until then the combinatorial split remains the licensed
   instrument, read qualitatively.

**How strongly the unification holds — the honest grade.** As a *layer decomposition with
shared substrate and shared clock*: `[DERIVED]` — every claim above reduces to ratified
machinery or direct computation. As anything stronger — one operator, one functor, a gauge
structure spanning the classes — **not established and, on two sub-claims, refuted or
declined** (§2.5: sheaf coupling unproven and currently contentless; ML-d: no structure group
exists). The unification is a *reading discipline*, not yet a *theorem*; stating it more
strongly than this would be the apophenia the house rules exist to catch.

### 2.2 FG-2 — the fields, made honest: per-class Hodge, and the velocity asymmetry

**Per-class Hodge status (the brainstorm's "the §2.2 machinery applies three times" is
over-symmetric; the true table):**

| class | complex | Hodge status |
|---|---|---|
| S | flag complex of the σ-backbone (built, `hodge.py:1-28`) | **full three-way split** — the only class with a genuine curl term today |
| D | Hasse DAG | **curl ≡ 0, provably** — three mutually adjacent covering nodes force a shortcut or a cycle, so the skeleton is triangle-free (ML §2.2 `[DERIVED]` there); the two-term split `C¹ = im d₀ᵀ ⊕ ker L₁` holds vacuously. Rider reused: a *nonzero* D-triangle count is a **data-integrity violation** of covering-only supersession (ML owner decision 3) — the survey's M3 doubles as that check. |
| F | flag complex of `X_cite`'s undirected support | plain (q=0) Hodge is fine — the magnetic parity obstruction (ML §2.2) blocks only q≠0; triangle density is an empirical question (M3) |
| C | flag complex of `E_proven`'s support | expected near-triangle-free at current population; measure, never assume (M3) |

So "three Hodge decompositions for free" is honestly: **one full (S), one provably degenerate
(D), two empirical (F, C)** — and the S-sheet carries nearly all the geometric content today.

**The velocity asymmetry — stronger than the brainstorm stated.** `[DERIVED from store
semantics]` S is the only *continuum* field: cosine weights move continuously (under revision
re-embeds, at fixed embedder version per A7). D, F, and C are **counting processes**: their
edges are unweighted-or-constant records (supersession arcs; citations; `PROVEN_WEIGHT = 1.0`,
`composed.py:70`) that are *minted*, not modulated. Their natural "velocity" is a **minting
intensity** — a `Rate(κ)` density per region (Rule CLOCK binds; an undeclared-clock rate is
ill-typed, dn-capability-scope §2.3, dn-velocity-instruments X1), not an edge-derivative.
Consequently the "three coupled vector fields" picture resolves to: **one continuum field (S)
modulated by marked point processes (F/C minting, D events), with the D-process as the clock**
— which is the brainstorm's own asymmetry intuition ("D carries time"), made type-level.

**The generative coupling becomes measurable, and it is a Layer-2 object.** "S seeds C/F
formation; a D-event reshapes S" are **conditional-intensity statements**: e.g. does C/F-minting
intensity concentrate on high-cosine pairs (S seeds C), and is `E[Δw_S | D-event at an
endpoint]` nonzero (revision moves local similarity)? Both are measurable with built
instruments plus the version/reference stores (§2.6 M2/M6) — and note for §2.5: this coupling
is a coupling of *evolution*, which **no static one-snapshot operator can see**. `[DERIVED]`

**The mismatch fields, corrected and defined.** On the composed assembly (`edge_classes`
retains per-class attribution precisely for this):
- **S↔C mismatch** — C-edges whose endpoint cosine falls below the working σ: *causation
  without resemblance*, the non-obvious dependency. One-sided by construction (S is dense;
  "S without C" is uninformative). `[DERIVED definition; cheap now]`
- **S↔F mismatch** — citations without resemblance: cross-domain import, the same shape one
  class over. `[DERIVED definition]`
- Distinguish both from clock-curvature's **metric mismatch** (effective chain distance ÷
  embedding distance, §2.4): that compares two *metrics on the same pairs*; these compare two
  *edge classes*. Same "two measures diverge and the divergence is the signal" rhyme, different
  objects — do not fuse them into one instrument.

**No new velocity objects.** The brainstorm's sloshing/harmonic-velocity falsifier is already
ratified in its correct form as VI-b (the alive/stale hole discriminator,
dn-velocity-instruments §2.2b — `‖P_harm(Δw)‖` on the common restriction, A7-pinned); the
covariance/Koopman family is already repaired and R-gated there (V2: POD not Koopman). This
note adds **zero** velocity instruments (DRY) — it only ties them to the alphabet: VI-b is an
S-field reading; the rotation instrument (VI-a) is an F-field reading.

### 2.3 FG-3 — the grammar: the membership layer, decided

1. **The object.** L ⊆ Σ_move* is a language of admissible fiber signatures; admissibility of a
   chain is membership of its signature; frontier pruning is the **viable-prefix** (dead-state)
   test on the product automaton. Regular is the default class; the lazy prune is then exactly
   the L4 materialization-boundary pattern (dn-synchronic-diachronic-dreamer §2.4): the
   automaton state is the compact certificate, kin to the σ*/MST certificate. Non-regular rules
   are parked (FG-c) until a genuine soundness rule provably needs counting.
   `[FROM MEMORY — RPQ/product-automaton; Angluin L*/RPNI for the learned route]`
2. **Hard vs soft — the line, ruled.** A constraint is **hard** (belongs in L) iff violating it
   makes the narrated chain **false** — an unwitnessed or mis-verbed claim; **soft** (belongs in
   ranking) iff violating it makes the chain merely **weak**. False-vs-weak is the criterion.
   It reproduces the known cases: verb licensing and grounding termination are hard; hop count,
   conductance, volatility exposure are soft. `[DERIVED from the ratified records-not-causes
   ruling, dreamer note §2.9]`
3. **The verb-licensing table (total over Σ_move; the positive form of F-SD9):**
   S → "resembles"; F → "cites/references"; D → "revised/superseded"; C → "produced/led to
   (witnessed record)"; the T-anchor modality → "as of ⟨cut⟩". Composite: a C-chain braided
   with forward D/time — the helix (CN-6) — licenses "recurring/spiraling" narration. A verb
   above a move's row (causal language on S or F) is **false**, not just disfavored — the hard
   class per (2). This sharpens F-SD9's causal-phrasing check from a negative grep into a
   positive per-move licensing check. `[DERIVED]`
4. **The grounding production, corrected in two ways.** The ratified law (grounding terminates
   in authored evidence or declared hypothesis, never prior interpretation — dreamer note
   §2.7-4) is a **node-class co-safety condition** — a condition on where the walk's support
   bottoms out, regular over the (move, node-class)-labeled alphabet. The brainstorm's rendering
   `F*·(C|D)` is (a) mislettered — its "F" is S — and (b) one candidate automaton *model* of the
   law, not the law itself; whether a citation into authored ground (an F-move) is an admissible
   terminal is genuinely open (§5). Grade the specific production `S*·(C|D|F?)`:
   `[INFERENCE — a v1 axiom candidate, to be validated against endorsed chains]`; the law it
   renders: ratified.
5. **The semantics — chain = explanation = corpus-relative proof, with its honest limit.** A
   narrated explanation IS the witnessed path it found; it is **sound relative to the records**:
   every C-move cites a witnessed production record, every D-move a supersession row, and a
   plausible-sounding reason with no such path is *rejectable mechanically*. That is the
   anti-hallucination property, and it is real. `[DERIVED]` The limit, stated so the claim
   stays honest: path existence certifies the *records*, not world-truth (a C-edge witnesses a
   recorded production, not a law of nature — oq-0021's distinction at chain grain), and it is
   **necessary, not sufficient** for a good explanation — many admissible paths exist; ranking
   (Layer 1) picks; and a valid path can still mislead (e.g. crossing a superseded node at an
   ANCHORED read without narrating its D-context — a narration obligation, §5). Parse
   (audit a stated reason) and generate (explainable retrieval) are both licensed *directions*;
   generate is the cleaner first target because its falsifier is crisp (the emitted path either
   exists with the claimed types or does not).
6. **Construction — ruled: hybrid, in this order.** v1 is a **small authored automaton**
   (route 1) whose productions carry type-theoretic justification where the fibers' own
   semantics force them (route 2 — e.g. a D-move is only well-typed along one identity's
   version chain: a typing fact of the versions store, not a preference). The learned route (3)
   is **parked on data**: it needs the endorsed-chain corpus (census + dreamer exhaust +
   owner endorsements) and the held-out validation arm — apophenia discipline. Route 2 as a
   *derivation of the whole grammar* from a fiber category is attractive and unproven; kept as
   an open question, not a dependency.
7. **The capability question (CS-x) — ruled: E stays a set; no extension now.** The honest
   audit: neither bp-080's census walks (fiber-pure enumerations) nor bp-082's influence
   attribution needs language-constrained walking — there is **no concrete consumer yet**, so
   per the capability-scope discipline the set→language generalization does not land. The first
   real consumer is the **generate direction** (explainable retrieval = CN-7's build + the
   automaton state, per §2.1's design directive); when that graduates, the CS-x extension
   lands with it, S-moves licensed by kernel-in-Σ and recorded moves by E. Until then the
   grammar is designed vocabulary with a named consumer, exactly the posture the parks require.
8. **Anchor encoding — ruled.** A temporal reference that *sets the reading frame*
   ("yesterday" = read at cut c) compiles to the **index** (CN-1: every reading carries its
   cut; the anchor is scope-side, dreamer note §2.1), not to a letter; a temporal reference
   that *traverses lineage* ("the note this superseded") compiles to **D-moves**. Normal form:
   anchor-as-index, D-as-letters. `[DERIVED from the ratified index discipline]`

### 2.4 FG-4 — the clock-curvature ruling: NOT a dead end — it is Layer 1, and half of it is already built as CN-4

The owner asked for an honest ruling. **Ruling: load-bearing core, analogy-grade shell, one
refused limb.** The core survives because it lands on built machinery; the shell is kept only
as vocabulary.

**(a) The phase model is CN-4's sign law, rediscovered phenomenologically — and it supplies the
missing calibration principle. `[DERIVED]`** Verified in code: the churn-weighted measure
`w = cos^α · exp(s_lat·a_lat − s_seq·a_seq)` (`conductance.py:47,109-127`) already carries the
two opposing couplings **as structural law** (D1 retired: series/sequential churn impedes,
lateral churn conducts — signs are law, only magnitudes tune), with magnitudes **shipped at 0**
(`CONDUCTANCE_THRESH`, `:91-95`) — the thermal coupling is *built but inert*. The dying-cluster
model maps exactly: hot = high a_seq (impedes; route around); cold-dense = low a_seq with
density conducting in parallel (Rayleigh; route through — the "annealed crystal"); the net is
the measured per-region ratio (χ_s), not a stance — precisely CN-4's ratified posture. What the
brainstorm genuinely **adds** is the calibration principle for turning the magnitudes on:
**per-hop cost = volatility exposure** — accumulated revision risk of the hop's endpoints over
the chain's use-window. Corollaries: `PROVEN_WEIGHT = 1.0` becomes *earned* rather than fiat
(C-edges are immutable records ⇒ ≈ zero exposure — the principle the composed plan's "Δ-phase
calibrates" park was waiting for); "chain proper time = volatility exposure" is a `Rate`-typed
chain functional and must carry its clock (Rule CLOCK — the type system catches exactly the
sloppiness this model risks).

**(b) The routing/functional claim stands beside σ\*, as parked — now with its deciding
measurement scheduled. `[DERIVED reduction; empirical question open]`** Multiplicative per-hop
attenuation ⇒ max-product path = shortest path under −log w `[ESTABLISHED reduction]`; the
built σ* is bottleneck (`sigma_star.py` — verified, no hop pricing). Whether hop-pricing
*refines* or merely *complements* the ratified functional is exactly the σ-sweep divergence
question (oq-0024 + M8): do bottleneck-optimal and product-optimal chains diverge on the real
corpus, and which predicts endorsed chains? No silent change to ratified machinery either way
(the clock-curvature park honored).

**(c) The D-fiber is the thermometer — adopted as the temperature field's definition.
`[DERIVED]`** Local clock rate := D-event (supersession) minting rate per region per declared
clock. This is a fiber read, not a new sensor; M6 checks it reproduces the churn statistics
CN-4's a_seq consumes (if yes, the temperature field needs no new machinery at all).

**(d) The mismatch observable is adopted; the GR shell is graded `[ANALOGY]` and kept only as
vocabulary.** The **metric-mismatch field** — effective chain distance (Layer-1 metric, σ*/
conductance/−log-product) ÷ ambient embedding distance — is well-defined, computable from built
instruments, and is *the* curvature observable of this thread: where it gradients, the
effective geometry deviates from the ambient one, and churn is the candidate source (M5/M7
test it). `[DERIVED definition]` The surrounding GR language — lensing, photon spheres,
Einstein-loop — is `[ANALOGY]`: pedagogically apt (the optical–mechanical equivalence
`[FROM MEMORY — verify before the book cites]` even makes the refraction and curvature tellings
one formalism), but it licenses no instrument beyond the mismatch field, and the **chronometry
inversion** (GR mass slows proper time; here "mass" is a *fast* clock) must accompany every
teaching use. The **conductivity-horizon threshold** (a churn level beyond which
through-conductivity collapses while internal cohesion holds) is `[INFERENCE]` — a genuine,
falsifiable prediction of the multiplicative functional, testable only after (b)'s calibration;
it graduates from prediction to instrument only if M7's phase scan shows the transition.

**(e) Plasticity — the refusal re-recorded.** Routing-builds-the-medium has no mechanism today
and gets none here: structure enters only via dreamer exhaust through the ratified admission
gates or owner authorship; Hebbian reinforcement stays **refused** (bright line 5). The
annealing/self-limiting-hub consequence is `[INFERENCE]`, observable longitudinally only after
the exhaust loop exists (Track D territory).

**How it relates back (the owner's actual question):** clock-curvature *is* the geometry layer
of §2.1 — the metric its distortions bend is the ranking geometry over exactly the chains the
grammar admits; the temperature sourcing the distortion is the D-fiber's minting intensity —
the same clock Layer 2's velocities are measured in and the helix spirals on. It is not a
detour from the fiber/field/grammar structure; it is that structure's middle layer. What does
**not** unify is named: the GR shell (vocabulary), the plasticity mechanism (absent, gated),
the horizon (prediction, not instrument).

### 2.5 FG-5 — the operator decision: three independent runs + scalar cross-statistics; PD-a stays parked with a sharpened, measurable re-entry

**The block-diagonality fact that decides the default. `[DERIVED — direct computation; sheaf
formalism per Hansen–Ghrist, FROM MEMORY]`** Model the "three surfaces glued along the shared
node set" as a cellular sheaf: node stalks ℝ^(classes at the node), one ℝ edge stalk per edge,
restriction maps = coordinate projections onto the edge's class. Then the coboundary decomposes
class-wise and the sheaf Laplacian is **block-diagonal: L_sheaf = ⊕_X L_X — the direct sum of
the per-class Laplacians, with zero coupling content.** Cross-class coupling exists **iff some
restriction map mixes class coordinates** — and no principled mixing map exists today: there is
no ratified answer to "what linear map converts a node's S-value into its C-value." A sheaf
operator built now would be either block-diagonal (three independent runs wearing a heavier
formalism) or parameterized by invented mixing maps (apophenia by construction).

**The dynamical-coupling distinction (the brainstorm's conflation, named).** The *real*
coupling the vector-field thread found — S seeds C/F minting; D-events reshape S — is a
coupling of **evolution** (Layer 2, conditional intensities across the D-clock), which a
static one-snapshot operator cannot represent at all (§2.2). "The coupling is the new physics,
therefore PD-a" conflated dynamical coupling with cohomological coupling. The right first
instruments for the real coupling are the scalar cross-class statistics, not an operator.

**Decision (FG-5):** the licensed configuration is **per-class Hodge/Laplacian runs (per
§2.2's honesty table) + scalar cross-class statistics** (mismatch densities; cross-class
correlation of per-class gradient potentials on shared nodes; conditional minting intensities).
**PD-a stays parked**, its re-entry *sharpened from "a design pass grounds the choice" to three
measured conditions, all required:*

1. **Support:** the pairwise skeleton overlap (M1) and class populations are non-degenerate —
   at current C-population (thin; live census empty at bp-080's seal) a coupled operator is
   infrastructure-ahead-of-need, the exact alternative ML-a's ledger already rejected;
2. **Content:** a measured, cut-stable, significantly nonzero cross-class structure exists
   (M2's potential correlations / mismatch structure) — this measured structure *is* the only
   legitimate restriction-map data a sheaf Laplacian could carry;
3. **Customer:** a consumer question is exhibited that the independent runs + scalar
   statistics demonstrably cannot answer.

The bundle-vs-sheaf sub-question is answered by M1 in passing: high skeleton overlap ⇒ one
base, rank-k bundle (lighter); low overlap (expected — S dense, F/D/C sparse and different) ⇒
the sheaf formalism is the technically correct object *if* re-entry ever fires. Either way the
choice is downstream of the same measurement, which is why it is not made now.

**ML-d ruled: NOT a customer; the non-abelian reading is declined. `[DERIVED]`** A gauge
structure needs a structure group G acting on a fiber space with G-valued edge transport. The
fiber alphabet's non-commutativity is **monoid-level** (word order in composition) — there is
no G, no fiber vector space it acts on, and no cross-class transport to carry it. The genuine
non-abelian object in the house remains the `[d,τ]` operator holonomy (TA-c — unclosed, and
provably not closable by abelian/spectral gadgets, ML §2.3); calling three directed edge
classes "a non-abelian gauge field" would be that section's category error reborn one floor
up. ML-d's park (curvature customer AND obstruction addressed) stands with **no customer
registered by this note**. ML-a is untouched.

### 2.6 FG-6 — the measure-first battery (consolidated; all on built instruments; nulls are results)

Every formalization above that is not `[DERIVED]` from ratified text gates on a measurement.
The battery, consolidated from all three threads (each row: what, instrument, what it gates).
Honesty first: **several rows are expected null or thin on today's corpus** (C thin; live
census empty; endorsed-chain corpus barely exists). A null *parks* the machinery it gates —
that is the point of running the battery before building anything.

| id | measurement | instruments (built) | gates |
|---|---|---|---|
| M1 | S/F/D/C skeleton overlap (pairwise support Jaccard on shared nodes) + per-class population census | `composed.py` assembly + `reference_edges` + versions | PD-a re-entry cond. 1; bundle-vs-sheaf |
| M2 | mismatch densities (S↔C, S↔F) + cross-class gradient-potential correlation + conditional minting intensities (does C/F minting concentrate on high-cos pairs; E[Δw_S \| D-event]) | `composed.edge_classes`, `hodge.py` potentials, version store | PD-a re-entry cond. 2; §2.2's generative-coupling claims |
| M3 | per-class triangle census (D: MUST be 0 — covering-only integrity, ML owner decision 3; F, C: empirical) | `hodge.flag_triangles` per class | §2.2's Hodge honesty table; the D data-integrity check |
| M4 | S-field Hodge split (gradient/curl/harmonic energy fractions); harmonic-velocity via VI-b when two A7-clean cuts exist | `hodge.py`; VI-b when built | the deficit reading (§2.1-2); PD-b's potential customer |
| M5 | Forman-vs-churn: `forman()` on the σ-graph conditioned on per-region D-minting rate — the sign question (clique-positive vs hub-negative) | `curvature.py:25-43` + versions | the routing story's sign (§2.4b); PD-c's eventual customer case |
| M6 | thermometer check: D-minting rate per region vs the churn statistics CN-4's a_seq consumes; per-region χ_s | versions + `conductance.chi_s` | §2.4c; CN-4 magnitude calibration |
| M7 | dead-vs-live cluster three-field signature: (D-rate, S-velocity coherence, C/F density) on known-finished arcs vs live ones; the metric-mismatch field across both | all of the above | the phase model (§2.4a); the horizon prediction's first look |
| M8 | σ-sweep (oq-0024, the owed run) + bottleneck-vs-product chain divergence, scored against endorsed chains where any exist | `sigma_star` + `conductance` | the functional question (§2.4b) |
| M9 | R1 sample-depth recheck on the grown corpus (per-edge series counts) | reference/version stores | the velocity/spectral tier's gate (unchanged, re-checked) |
| M10 | which fiber signatures appear in endorsed/census chains | `census.py` + dreamer exhaust | grammar calibration (route 3's data; the S*·(C\|D\|F?) production) |

*Falsifier discipline for the battery itself:* every reading carries its CN-1 index tuple and
grid; a reading emitted without its index, or a conclusion drawn from an expected-null row's
absence of data (silence narrated as structure), is malformed.

### 2.7 FG-7 — reconciliation: every touched note, ruled (no silent absorption; A8 — no ratified text edited)

| note | ruling | content |
|---|---|---|
| `dn-edge-dynamics` (ratified) | **EXTEND** | §2.2 Hodge applied per-class under §2.2's honesty table; the inversion (§2.5) binds every continuous object here. **PD-a**: park stands, re-entry *sharpened* to FG-5's three measured conditions. **PD-b**: gains a named potential customer (§2.1-3). **PD-c**: clock-curvature is the registered customer-candidate, but the ladder is honored — Forman (built) runs first (M5/M7); Ollivier builds only if transport-contraction semantics are demonstrably needed after those reads. |
| `dn-magnetic-laplacian` (ratified) | **EXTEND** | ML-a deferral honored, not relitigated. ML-d: this note **declines** to register the three-directed-fibers reading as a customer (FG-5's ruling); the park stands unweakened. §2.2's triangle-freeness and owner-decision-3 rider are consumed by M3. The flux≠Ricci ledger gains this note's kin entries (fiber ledger §2.0; metric-mismatch vs class-mismatch §2.2). |
| `dn-capability-scope` (ratified) | **EXTEND** | E remains a set (§2.3-7): no CS-x extension without its consumer; the S-letter's capability is kernel-in-Σ per its own §2.4. `Inv`/`Rate` typing does load-bearing work here (§2.2 velocities; §2.4a proper time). |
| `dn-agent-taxonomy` (ratified) | **EXTEND** | The fiber letters are pinned to its §2.5 semantics (F = citation); the grounding law (§2.2 there) is the source of the composed assembly this note measures over. |
| `dn-connectivity-instruments` (ratified) | **EXTEND** | CN-4 gains its calibration principle (volatility exposure, §2.4a — magnitudes still move only by the owner-visible act its own text requires); CN-5/CN-7 identified as the commutative special case / the generalization seam (§2.1); CN-6's helix is the (C ∥ D) braid the sentence semantics narrates (§2.3-3). |
| `dn-velocity-instruments` (ratified) | **EXTEND** | X1–X3 bind every Layer-2 object here; VI-b is the harmonic-velocity falsifier's ratified home (no duplicate object minted); the alphabet ties VI-a→F, VI-b→S. |
| `dn-synchronic-diachronic-dreamer` (ratified) | **EXTEND** | The verb-licensing table (§2.3-3) sharpens §2.9/F-SD9 into positive form; the grammar's lazy prune is an L4 instance; the future explain-path instrument would enter as a dispatch-record instrument grant, nothing bespoke. |
| `dn-temporal-retrieval-algebra` (ratified) | **EXTEND** | TA-c remains unclosed and untouched; the grammar's order-sensitivity is the language-layer expression of the same non-commutativity, not a closure of it. |
| the three warrant brainstorms | **CONSUMED, with corrections** | The alphabet correction (finding-0140) re-reads their claims per §2.0; the sheaf enthusiasm is resolved to FG-5's measured parking; the phase model to §2.4's CN-4 grounding. |

## 3. Consequences — what graduates, what parks (session-sized; preempts nothing)

Sequencing constraint honored: everything queues behind the in-flight and already-sequenced
work (bp-082; the dreamer builds' remaining items); the battery is read-only and cheap.

- **G-A — the fiber-geometry survey (ONE session-sized, read-only plan): M1–M8.** Eval-side
  readings only; no core writes; every reading CN-1-indexed. This plan is the gate for
  everything else in this note, and its nulls are findings, not failures. (M9/M10 ride along
  where the stores make them free.)
- **G-B (conditional on G-A's M2 showing signal) — the mismatch lens:** S↔C / S↔F densities as
  a census-adjacent structural-panel claim family, honest-seam (zero claims when C is empty),
  records-not-causes vocabulary ("witnessed production without resemblance" — fact, not
  inference).
- **G-C (small, independent) — the verb-licensing check:** the §2.3-3 table as a positive
  per-move narration audit on the census lens surface — the F-SD9 sharpening; a rider-sized
  plan.
- **Explicitly NOT licensed:** the grammar *build* (automaton + product walk — waits for the
  explainable-retrieval consumer and M10's data); the sheaf/bundle operator (FG-5's three
  conditions); Ollivier (behind the Forman reads); the horizon scan (behind functional
  calibration); the velocity/spectral tier (M9's gate); any plasticity mechanism (Track D,
  admission-gated); ML-a/ML-d (unchanged).

## 4. Parked decisions

| id | decision | default recorded | re-entry condition |
|---|---|---|---|
| FG-a | the sheaf/bundle Laplacian (= PD-a, sharpened) | per-class runs + scalar cross-statistics | FG-5's three conditions, all measured true |
| FG-b | hop-priced (−log-product) functional beside/inside σ* | bottleneck σ* stands; no silent change | M8 shows material divergence AND product-optimal better predicts endorsed chains |
| FG-c | non-regular language class for L | regular (product-automaton lazy prune) | a genuine soundness rule proven non-regular |
| FG-d | CS-x: E set → language | E stays a set | the explainable-retrieval (generate) instrument graduates as the consumer |
| FG-e | learned grammar (route 3) | authored v1 (routes 1+2) | endorsed-chain corpus at validating size + held-out arm in place |
| FG-f | CN-4 magnitude calibration by volatility exposure | magnitudes stay 0 (shipped inert) | M6/M7 land AND the owner performs the separate owner-visible lever act CN-4 requires |
| FG-g | weighted Hodge inner product (= PD-b customer) | combinatorial split, read qualitatively | Hodge readings consumed quantitatively for transport attribution (§2.1-3) |
| FG-h | the horizon/decoupling instrument | prediction only, `[INFERENCE]` | FG-b resolved for the product functional AND M7 shows the phase transition |

## 5. Open questions

- **Is F an admissible grounding terminal?** A citation lands on authored ground but is not a
  *proven* production — does `S*·(C|D)` extend to `S*·(C|D|F)`? (M10's endorsed-chain data
  informs; owner taste finishes.)
- **The superseded-node narration obligation:** should a chain crossing a node superseded at
  the read's cut be *hard*-required to include the D-context, or is that a soft narration
  rule? (The false-vs-weak criterion genuinely wavers here — the strongest candidate for a new
  hard production beyond grounding.)
- **Membership-at-cut as typing:** are move endpoints' existence-at-the-anchor checks part of L
  (hard) or of the reading's legality (the CN-1 index)? Current lean: index-side, like the
  anchor itself (§2.3-8) — but the counterfactual overlay (E_STAGED) may force it into the
  grammar when staged nodes enter chains.
- **Does the S-field's harmonic-velocity coincide with open holes per-fiber** (the parked
  velocity-Hodge falsifier, now VI-b's per-hole localization question) — L-b's carrying-cycle
  machinery decides where that lives.
- **Chronometric inversion, used or unused:** is there a palace phenomenon where fast-clock
  regions redshift *as destinations* while appreciating *as media* (clock-curvature's
  destination/medium decoupling) — two observables or one? (M7 can produce the first split
  reading.)

## Cross-references

**Code (verified on disk this session, worktree @ `8be3c98`):** `core/scope.py:24-25,155-188`
(E ⊆ {F,D,C}; F = citation — the alphabet anchor) · `core/graph/composed.py:51-56,70,134`
(E_SIM/E_PROVEN/E_STAGED; PROVEN_WEIGHT = 1.0; max-flatten) · `core/graph/conductance.py:47,
91-95,109-127,453` (the CN-4 weight; magnitudes shipped 0; signs as law; the decay-only null) ·
`core/graph/sigma_star.py` (bottleneck semantics — no hop pricing) · `core/graph/census.py`
(the three witnessed families; records-not-causes) · `core/complex/hodge.py:1-28` (flag
complex; three-way split; unweighted inner product) · `core/complex/curvature.py:25-43`
(Forman, built) · `core/temporal/superconnection.py` ([d,τ] on severed citations) ·
`eval/harness/re_measure.py:150-197` (the live E_proven source — witnessed co-production).

**Design:** dn-edge-dynamics §2.2/§2.5/PD-a..c · dn-magnetic-laplacian §2.2/§2.3/§2.6/§2.7,
ML-a..d, owner decision 3 · dn-capability-scope §2.1 (:65)/§2.3/§2.4 · dn-agent-taxonomy
§2.2/§2.5 (:155-167, :206-210) · dn-connectivity-instruments CN-1..CN-7 · dn-velocity-
instruments §2.1–2.3 · dn-synchronic-diachronic-dreamer §2.1/§2.4/§2.8/§2.9/F-SD9 ·
dn-temporal-retrieval-algebra §2.3/TA-c · dn-sigma-fibers (the σ-fiber sense) ·
dn-recursive-dreaming-bounded-by-grounding (the grounding law's home, as sharpened by the
dreamer note §2.7-4) · finding-0140 (the letter collision) · oq-0021 (adopted; §2.3-3 sharpens)
· oq-0024 (M8 is the owed run) · bp-080/bp-081 seals (census built; live read empty) · bp-082
(in flight; unpreempted).

**External claims flagged `[FROM MEMORY]` for the external-grounding sweep before any book
chapter cites them:** regular path queries / product-automaton evaluation (Mendelzon–Wood);
grammatical inference (Angluin L*, RPNI); Thomson/Dirichlet principle (energy-minimizing flows
are cycle-free); cellular-sheaf Laplacians (Hansen–Ghrist); the optical–mechanical analogy
(weak-field lensing ≡ refractive index); POD/DMD/Koopman distinctions (already flagged in
dn-velocity-instruments); von Luxburg degeneracy (already grounded in CN-3's warrant).
