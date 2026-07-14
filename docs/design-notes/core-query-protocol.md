---
type: design-note
id: dn-core-query-protocol
status: draft # draft → ratified → superseded.  draft→ratified is an OWNER-ONLY hand edit.
implementation: design-only # nothing built; the reference substrate (reference_edges, 61k edges) exists but is code-anchored + agent-unreachable
created: 2026-07-13
updated: 2026-07-14
links:
  - docs/brainstorms/core-query-protocol.md # the graduate-ready arc (warrant): four threads + two opus sketches + the fable rigorous pass
  - docs/design-notes/edge-dynamics.md # the 1-form lift, Hodge/Helmholtz split, L₁ Fourier basis, THREAD lens, Lane A/B seam
  - docs/design-notes/recursive-strata-amendment.md # γ^d damping, typed edge_budget, fibers vs dispositional edges
  - docs/design-notes/supersession-lifecycle.md # what a dispositional (supersession) edge IS; §4.5 depth re-anchoring; §7 rename identity
  - docs/design-notes/the-sacred-boundary.md # the plane-crossing ruling §2.4 makes concrete
  - docs/design-notes/capability-evaluation-harness.md # the eval-harness home for the self-grading loop
  - docs/design-notes/observed-data-and-the-assistant-tier.md # the mirror firewall the scope model inherits
  - docs/findings/finding-0059.md # doc→doc blindness (the prerequisite this note surfaces)
  - docs/findings/finding-0061.md # the stale-baseline class the reference graph would guard
  - docs/findings/finding-0062.md # the direction finding this note graduates
  - docs/design-notes/temporal-retrieval-algebra.md # the math successor (§2.5 formalization; C5)
  - docs/brainstorms/edge-dynamics-lane-b-fable-pass.md # the 2026-07-14 fable finalization warrant
supersedes: null
superseded_by: null
warrant: docs/brainstorms/core-query-protocol.md
---

# The core-query protocol — retrieval as a scoped algebra over the strata

> Composed by the orchestrator (**Opus/xhigh**, 2026-07-13) from the graduate-ready
> `core-query-protocol` brainstorm; filed as `draft`. The brainstorm→design step is
> normally **fable-guarded** (owner rule); the owner relaxed the guard for THIS drafting
> because the tier-justifying work — the rigorous math — was already paid at fable
> (`claude-fable-5`, verified) and is captured in the brainstorm's 2026-07-13 capsules.
> This note therefore *states* the derived/established results and makes the design
> decisions they inform; it does not re-derive them. The remaining fable work is the
> formalization **shortlist** (§ Parked), not the whole note.
>
> **✓ Fable-vetted 2026-07-14** (`claude-fable-5`, tier owner-confirmed;
> `docs/brainstorms/edge-dynamics-lane-b-fable-pass.md`). The pass reviewed the design
> decisions — it **corrected** §2.4 (toward capability-dissolution) and re-ranked the §2.5
> operators, folded in below — pinned the Parked normalization triple (now in the math successor
> `dn-temporal-retrieval-algebra`), and ruled §4.5 and one-note-vs-two. This draft is now
> **ready for the owner's ratification review**. Opus-drafted, fable-checked, owner-ratified.
>
> Ratification is a hand edit by the owner — no command performs it, `gate-guard` denies
> any agent attempt, and `/graduate` refuses this note until `status: ratified`.

## 1. Purpose and scope

### 1.1 What this note decides

There is no single, typed way to *ask the core a question*. Every agent — the orchestrator,
the Ambassador, the sensors, and any future reader — reaches into the core through an
ad-hoc, bespoke interface, and the existing typed windows (`MirrorView`, `ObservedView`,
`OpsView`, `EffectView`) are partial, uncoordinated sentences of a language nobody has
written down. This note writes it down. It decides:

1. **The frame (§2.1):** every agent is a **capability-scoped client of the core**, not a
   distinct kind of thing. A client's identity is its *scope* — which strata it may touch,
   under which of `{read | read+propose | write}`. The orchestrator, the Ambassador, and a
   sensor differ only in scope.
2. **The algebra (§2.2):** the core's retrieval modes — **structural**, **semantic**,
   **temporal** — are three sentences in *one* query algebra, distinguished by *edge-class
   scope* `{F, D}` and *time-scope*. The fable pass established that structural and
   semantic retrieval are two regions of a single object (the PSD-kernel cone with a
   deformation curve through it); temporal retrieval is the transport between snapshots.
3. **The archetype (§2.3):** the simplest well-typed client — a **deterministic,
   single-stratum, no-model reference agent** (the read-side dual of a sensor) — as the
   first thing to build and the proof the frame is right.
4. **The boundary ruling (§2.4):** whether, and how, the *build-time* plane may query the
   *live daemon's* reference stratum. Ruling: **as a capability scope, not a special case.**
5. **The self-grading loop (§2.6):** the reference agent is testable from day one against a
   deterministic oracle, which also *continuously measures sensor fidelity*.

### 1.2 What is out of scope

Implementation (this note is `design-only`); the rigorous *proofs* (they live in the
brainstorm's fable capsule — this note cites results, it does not prove them); the full
formalization of the algebra (the normalization triple and friends — Parked, fable work);
and any build (that follows ratification → `/graduate`). This note also does **not** touch
the Ambassador's or Librarian's semantic-RAG machinery — those are heavy clients of the
same protocol, not redefined here.

### 1.3 Provenance, and what fable must finalize (be honest)

The reason these decisions can be made at opus *at all* is the **verified fable pass**
(`claude-fable-5`, uninterrupted; captured in the brainstorm's 2026-07-13 capsule). Without
it, §2.2 would be conjecture and this note could not responsibly decide anything. So the
attribution is load-bearing: **the fable worker is the warrant for the calls made here.** In
that spirit, the honest split of this note — what is settled vs what a fable pass must
finalize before the owner ratifies:

**Fable-grounded (decide on these):** the §2.2 algebra results (the β-deformation with
modes 1a/1b as endpoints; the kernel-cone unification of 1b & 2; the Mercer inversion — mode
2 as the cone's generic point; the Schoenberg phase transition) and the §2.5 temporal results
(the bicomplex ⟺ F1∧F2 reduction; the localized `[d,τ]` obstruction; the superconnection
curvature; the ledger-as-dilation; the γ-contraction). These carry the fable pass's own
`[ESTABLISHED]`/`[DERIVED]` labels; the *decisions* resting on them (§2.2's "three modes are
one algebra"; §2.5's design consequences) are sound.

**Opus-provisional — ✓ FINALIZED by the 2026-07-14 fable pass**
(`docs/brainstorms/edge-dynamics-lane-b-fable-pass.md`). Resolutions: **(1)** §2.4 → *corrected*
to capability-dissolution (a local repo-derived twin, not a sealed-store read) — §2.4; **(2)** §2.1
scope grammar → the *bounded lattice* — §2.1; **(3)** surface shapes → `ReferenceView` library
object + the two mode-3 operators named/re-ranked — §2.5; **(4)** the normalization triple →
*pinned* in `dn-temporal-retrieval-algebra` §2.1; **(5)** §4.5 → *ruled: promotion re-anchors
depth*, and one-note-vs-two → *three notes* (this + the math successor + the Track D charter) — see
Parked. The original opus-provisional list is retained below as the record of what fable was asked
to settle:

1. **§2.4 the sacred-boundary ruling** — an opus *design judgment* touching an invariant
   boundary. It is the single highest-stakes call in the note and wants fable + owner scrutiny,
   not opus's say-so.
2. **§2.1 the exact scope grammar** — the specific tuple/primitives are opus synthesis; the
   formal type system (what a scope *is*, how it composes, how it enforces the boundary) is
   fable-grade design.
3. **§2.3/§2.5 surface shapes** — reference agent as `ReferenceView` (library) vs addressable
   service; the naming/typing of the two mode-3 operators. Proposed at opus, not settled.
4. **The Parked normalization triple** (cost dictionary, directedness, `(β,z)` coupling) —
   the fable pass was explicit: *nothing in §2.2 is theorem-grade until these are pinned.*
5. **The Parked `§4.5` dichotomy** (promotion re-anchoring) and **one-note-vs-two**.
6. **Literature verification — ✅ RESOLVED (web check, 2026-07-13; NOT a fable task).** The
   fable pass flagged its citations as *from memory*; a sonnet+web pass verified all nine
   against primary sources: **7 CONFIRMED · 2 PARTIAL · 0 REFUTED**. Confirmed as cited:
   RSP/free-energy distances (Saerens–Yen–Fouss–Achbany 2009; two-limit **free-energy**
   distance Kivimäki–Shimbo–Saerens 2013), Chebotarev forest metrics (2011, on the 1997
   matrix-forest theorem), Schur product (Schur 1911), Schoenberg negative-type (1938 — year
   correct), Sz.-Nagy dilation (1953), Maslov dequantization (Litvinov survey 2005), Quillen
   superconnection (1985). **Two corrections applied/owed:** (a) **Mercer → Moore–Aronszajn
   1950** — the general "every PSD kernel is an inner product" fact is the RKHS/Moore–Aronszajn
   construction, *not* Mercer's theorem (compact-domain eigenfunction expansion); the §2.2 "Mercer
   inversion" should read "Moore–Aronszajn inversion" (substantive — fixed inline at §2.2). (b)
   **p-resistances** (Alamgir **&** von Luxburg — two authors, NIPS 2011): the span is
   shortest-path (p=1) → resistance (p=2) → **cut/connectivity** (p→∞), not "resistance" at the
   high end (minor — for the successor note / book chapter). This is the first dogfood of the
   `external-grounding` "verify a citation before trusting it" principle — a real
   confident-but-wrong attribution caught cheaply. The fable session no longer owns this item.
7. **The balance-isolation reconciliation.** `core/stores/reference_edges.py` is
   **deliberately balance-isolated** — `core/complex/**` never imports it, `build_complex` has
   no parameter for it, and `tests/integration/test_reference_edge_isolation.py` proves
   bit-identically that no instrument result changes when reference edges are added/removed.
   So the reference store's citation edges are **NOT** the "fibers" `hodge.py` builds its
   complex from (that is the *similarity backbone* `A = cosine_adjacency(emb)`). This is
   exactly the fable pass's "two structural graphs" caveat: the retrieval/algebra §2.2 uses the
   *citation* fiber graph; the built Hodge object uses the *similarity* graph. Using citation
   edges for the §2.5 math (the bicomplex test) means constructing a **separate** citation
   complex — which does not violate the isolation invariant (it never feeds `A_signed`/the
   balance math) but is a distinct, deliberate construction the fable session must specify.

Everything in this list is why the note is `draft`, not why it is wrong — it is a faithful map
of the opus/fable seam so the fable session knows exactly where to spend.

## 2. Principles / decision

### 2.1 Agents are capability-scoped clients of one protocol

**Decision.** Model every core-reader as a client whose type is a **capability scope**

```
scope = ( strata it may touch , edge-classes {F, D} , time-scope , {read | read+propose | write} )
```

The differences we treat as "kinds of agent" are differences of scope:

| Client | Strata | Edges | Time | Authority | Model? |
|---|---|---|---|---|---|
| Reference agent (§2.3) | one | `F` | none | read | **no** |
| Librarian / Ambassador | mirror + curated + ops | — | — | read + propose | yes |
| Sensor (write-side dual) | one | — | stamps | **write** (projects) | no |
| Orchestrator | build-plane artifacts | — | — | read + propose + write (scoped) | yes |

The existing Views are the **partial seed** of this language — each is already a typed,
capability-scoped window onto one plane. This note's frame unifies them: a View is a
*declared scope*; a query is a *sentence within it*. The invariant that makes the frame
safe is that **scope is the access-control primitive** — the sacred boundary (§2.4), the
mirror firewall, and `read+propose≠write` are all expressed as scope, never as ad-hoc
special cases in each client.

**The scope algebra is a bounded lattice (fable-grade, C2).** A scope is a 4-tuple
`s = (Σ, E, T, A)`: `Σ ⊆ Strata`; `E ⊆ {F, D}`; `T ∈ {now} ∪ {[t₀,t₁]} ∪ {ledger}` (`now` applies
`π_active`, `ledger` is the dilation space — §2.5); `A ∈ {read < read+propose < write}`. Composition
is a bounded lattice:

- **Meet** `s₁ ⊓ s₂ = (Σ₁∩Σ₂, E₁∩E₂, T₁∩T₂, min(A₁,A₂))` — the **safe** composition; a delegated
  sub-agent receives the *meet* of its own and its parent's scope.
- **Join** `s₁ ⊔ s₂ = (∪,∪,∪,max)` — a **widening**, **not** freely grantable: a scope widens only by
  an authority that already holds the wider scope (**monotone delegation** — you cannot delegate
  more than you have). *This lattice law IS non-negotiable #6* ("minted agents can't exceed their
  template's scope or a pre-declared max") — the constitutional rule and the lattice law are one
  statement.
- **⊥** `= (∅,∅,∅,read)` (no access); **⊤** = full core — and **even ⊤ honors the foundation
  denylist** (`CONSTITUTION.md`, `eval/golden/**`) as a hard forbidden region in every writable `Σ`.

**Enforcement is structural, not by convention.** Each client is *constructed* with a scope; a
query is a well-typed sentence whose required capability must be `⊑` the granted scope; ill-scoped
queries are **unrepresentable** (a constructor error) — exactly as `MirrorView` makes a non-authored
read unrepresentable. The existing Views are the partial instances: `MirrorView ≈ (mirror-authored,
F, now, read)`, `ObservedView ≈ (observed, *, *, read)`, `EffectView ≈ (—, —, —, write-under-gate)`.
Firewalls are **forbidden-region ideals checked by meet**: the mirror firewall is any scope whose
`Σ` includes mirror-*payload* meeting to ⊥ for non-mirror clients; **`D`-exclusion is a type
constraint** — a mode-1 grounding query is *typed* `E = {F}` and cannot name `D` (the "infinite cost
on `D`" is now a type); **C1 is a stratum refinement** `reference_repo ⊂ reference`.

### 2.2 The three retrieval modes are one algebra

The core's graph carries **typed edges**: **fibers** `F` (citations/warrants; budgeted
lateral or cross-stratum) and **dispositional** `D` (supersession; time-directional). Over
the cochain complex `C⁰ —d₀→ C¹ —d₁→ C²` (the 1-form lift of `edge-dynamics.md`), retrieval
is a query against these edges, and the mode is fixed by *which edge-class you scope to* and
*whether you keep the time axis*:

- **Mode 1 — structural** (fibers, one stratum, **no time**). Retrieval by *connectivity*.
  It **bifurcates**: (1a) hard reachability in the Boolean/tropical `(min,+)` **path
  semiring**; (1b) soft diffusion — the graph **heat kernel** `e^{-tL_F}` / Green's function
  `(L_F)⁺` — a PSD kernel. Deterministic, no model.
- **Mode 2 — semantic** (the embedding Gram kernel `K_sem`). Retrieval by *similarity*.
  Model-mediated (this is the Librarian's retrieval).
- **Mode 3 — temporal** (traverse `D` across snapshots). The transport *between* the static
  pictures. This is where provenance/history queries live.

**The unification (fable-established; proofs in the brainstorm capsule, cite before a book
uses them):**

- **Modes 1a and 1b are the two ends of one deformation.** A single free-energy /
  randomized-shortest-path family `K(β)` (with an inverse-temperature `β` on edge costs
  `c = −log w`) has **1a = β→∞** (tropical shortest-path/Viterbi) and **1b = β→0**
  (diffusion/resistance) as its endpoints, with `O(1/β)` convergence. The endpoint
  degeneration is **Maslov dequantization** of the path semiring — 1a is the *same* Kleene
  closure as 1b, at the degenerate boundary. `[ESTABLISHED: RSP/free-energy distances;
  Chebotarev; p-resistances. DERIVED: the O(1/β) bound.]`
- **Modes 1b and 2 are two points in the PSD-kernel cone**, whose algebra is `+`, convex
  mixing, and Hadamard `⊙` (Schur). Hybrid retrieval is *an operation in the cone*:
  `K_struct ⊙ K_sem` = "cited **and** semantically near." `[ESTABLISHED: Schur product.]`
- **The correct taxonomy (the fable inversion):** since *every* PSD kernel is some
  embedding's Gram (**Moore–Aronszajn 1950** — the RKHS/feature-map fact; *not* Mercer,
  whose theorem is the narrower compact-domain eigenfunction expansion — corrected per
  §1.3 item 6), **mode 2 is the generic point of the cone**; **mode 1b is its
  thin graph-spectral locus** `𝔉(L) = {f(L)}`; **mode 1a is the tropical boundary** of a
  curve inside that locus. A learned embedding is **on the cone always, on the structural
  curve generically never** — unless it is (an ambient rotation of) a *spectral* embedding
  (diffusion maps / Laplacian eigenmaps). `[DERIVED, Props 2–4.]`
- **A phase transition at `β=∞`:** finite `β` gives an honest kernel; the `β=∞` limit is a
  *metric* that is generically **not of negative type**, so it does **not** re-enter the
  cone (Schoenberg). Inner-product retrieval degenerates into idempotent, winner-take-all
  metric retrieval exactly at the tropical boundary. `[ESTABLISHED: Schoenberg 1938.]`

**Decision.** The query protocol's surface is *"declare edge-class scope `{F, D}` and
time-scope; the mode — hence the admissible algebra — follows."* The system's invariants are
**algebraic constraints on that algebra, not side rules**: `D`-exclusion (the grounding walk
never traverses supersession) is an *infinite-cost assignment* on `D`; the γ^d strata ceiling
is a *Boltzmann factor in depth* (`γ^d = e^{-d·log(1/γ)}`); orientation gauge-invariance makes
the static family gauge-invariant for free. Retrieval and the safety invariants are one object
read under different scopes.

### 2.3 The reference agent — the archetype, and the first build

**Decision.** Build, first, the **deterministic single-stratum reference agent**: given a
target, return its connected set over fibers `F`, at fixed time, with `ref_type` and
`source_line`. It is the *read-side dual of a sensor* — as deterministic and attestable as a
sensor's projection, but serving queries instead of writing them. Because it touches **one
stratum, lateral edges only, no time**, it needs **none** of the Ambassador's machinery: no
model, no cross-stratum budget, no firewall composition, no hallucination surface. It is the
simplest well-typed sentence of §2.1 — `read(one stratum, F, no time)` — and shipping it is
the proof the whole frame holds.

This is **structural pseudo-RAG**: the "R" of RAG (retrieval by connectivity) without the
"AG," a primitive that can *feed* generation (hand its set to the Librarian for
citation-aware retrieval) but stands alone for the agent-bookkeeping need that motivated this
whole line (findings 0059/0061: agents re-grepping for "who cites this" that they should be
able to *look up*).

### 2.4 The sacred-boundary ruling

The reference stratum (`data/reference_edges.sqlite`, ~61k edges) lives in the sealed core;
"make it useful for *us*" means the **build-time plane** querying the **live daemon's**
stratum — a plane crossing (`the-sacred-boundary.md`).

**Ruling (fable-corrected 2026-07-14; owner ratifies).** The opus draft exposed the stratum "as a
capability scope, not a special case" — right in *direction*, but one step short of
`the-sacred-boundary` §3's own dissolution test (*"keep moving the boundary until the permission is
unnecessary"*). The fable pass corrects the **mechanism** from a scoped cross-boundary *read* to a
**local repo-derived twin** — and sharpens the predicate. `[capsule C1; VERIFIED
reference_edges.py:117–129 (no payload column), :61–63 (vault-digest reservation, empty to date)]`

1. **The schema fact holds.** `reference_edges.sqlite` stores only structure — `edge_id, commit_sha,
   endpoints (kind/ref/detail), ref_type, source_line` — **no payload, no note text, no
   embeddings.** So "corpus-structural, not the mirror's contents" is true at the schema level.
2. **Information-equivalence to repo-grep is decisive.** For edges over `docs/**` + code, the
   citation graph is **derivable from the repo the build-time plane already holds** — that is
   literally what the §2.6 self-grading oracle does (repo-grep at HEAD). A build-time reference
   query over in-repo edges adds **zero** information the plane cannot already compute.
3. **The residual the opus ruling missed — vault-backed edges.** `reference_edges.py:61–63` reserves
   `detail = digest` for vault-note targets (private notes not in the repo). None exist today
   (`detail=''` in every minted edge), but a *future* vault-citation edge would leak private-note
   citation structure, which is **not** repo-derivable. So the predicate tightens from "structural
   metadata" to **"repo-derivable edges only (both endpoints in `docs/**`+code, never
   vault-backed)."**
4. **The correction — dissolve the crossing, don't scope it.** The build-time plane **rebuilds the
   identical reference index locally** from the repo (deterministic `φ_doc`/`φ_code`) —
   bit-identical to the sealed store for in-repo edges, and **structurally incapable of seeing
   vault-backed edges** (they are not in the repo). **Ruling: the build-time plane queries a LOCAL
   repo-derived twin, never a handle into the live sealed store.** This (a) dissolves the
   plane-crossing (no sealed-store handle — faithful to non-negotiables #1/#2), (b) is
   information-equivalent for in-repo edges, (c) cannot leak vault structure by construction. The
   "duplicates the sensor" objection dissolves: determinism makes the twin free, and the §2.6
   grep-oracle is the *continuous proof* that the twin ≡ the sealed store for in-repo edges.
5. **In-core clients are unaffected.** The Ambassador / dreamer legitimately live inside the core;
   their read of the live reference stratum is *not* a crossing. The correction re-homes only the
   *build-time* plane's access.

This keeps the boundary a *property of the type system* (§2.1) — `reference_repo ⊂ reference`, the
repo-derivable sub-stratum — rather than a rule each caller must remember.

> **OWNER RULING (2026-07-14): YES.** The *repo-derivable* citation graph may be queried by a
> delegated/worktree build-time context — it is already `grep`-able, so the twin is
> information-equivalent (convenience, not exposure). C1 is settled.

### 2.5 The temporal layer and the invariants (stated; formalization Parked)

Supersession is a **connection** on the bundle of retrieval cones, acting on kernels by
congruence `K ↦ σ_* K σ_*ᵀ` (PSD-preserving). The fable pass established:

- **The temporal complex is well-founded.** Supersession is acyclic (op-seq is a strict
  order) ⇒ a poset ⇒ its nerve gives `δ_D² = 0`. `[ESTABLISHED, with hypotheses: transitive
  closure is taken; rename-stable identity is a data prerequisite — §7 of supersession-lifecycle.]`
- **"Is space×time a bicomplex?" = "is supersession functorial over citations?"** It holds
  **iff** (F1) each transport is simplicial — *a revised note's citations carry forward; the
  one killer is a severed citation* — **and** (F2) the transports compose. The obstruction
  `[d, τ]` is supported **exactly on severed citations**, weighted by the potential drop — so
  the "citation-coherence" score *is* `‖[d,τ]‖`. Its rigorous home is a **Quillen
  superconnection** whose curvature is `[d,τ]`; **non-flatness is the first obstruction, not a
  dead end** (homotopy-repairable if the class is exact). `[DERIVED.]`
- **Topological ⊊ metric coherence.** Even perfect functoriality transports *homology* (the
  THREAD lens's objects have a well-defined temporal life) but not *kernels* — kernel-flatness
  additionally needs `σ` weight-compatible (isometric). `[DERIVED.]`
- **The transport is not unitary; the ledger is its dilation.** Revision creates, destroys,
  and merges, so the active-view transport is a contraction — and by Sz.-Nagy the append-only
  **ledger is its isometric dilation**: *"revision destroys structure in the active view; the
  ledger is the space in which nothing was ever destroyed."* Under confidence weighting the
  transport is a **strict γ-contraction except at owner promotions** — *the owner is the only
  energy source in the dynamics.* `[DERIVED, contingent on supersession-lifecycle §4.5 —
  Parked.]`

**Design consequence (fable-corrected, C3/A2).** The two mode-3 operators are **not peers a query
"declares which."** `π_active` (ledger-compression) is the **ambient default** — the operator form
of `D`-exclusion, applied to *every* non-temporal query (scope `T = now`), a contraction that
destroys superseded content. `σ_*` (`transport_forward`, follow `D` to successors) and its
merge-safe adjoint `σ^*` (`transport_back`) are the **opt-in** temporal traversal a query declares
(`T = window, E ∋ D, direction ∈ {forward = σ_*, backward = σ^*}`). Their formalization — types,
composition, which invariants each preserves, and the well-foundedness prerequisite (rename-stable
identity — a data risk today, `supersession-lifecycle` §7 / `sync.py:77`) — is made theorem-grade in
the math successor `dn-temporal-retrieval-algebra` §2.2, §2.4.

### 2.6 The self-grading loop (Thread C)

**Decision.** The reference agent ships with a **deterministic self-grading harness**
(`capability-evaluation-harness.md`): query → check against an **independent repo-grep oracle
at HEAD** → score → record. Because reference lookup is deterministic, the judge has *free,
correct* ground truth — a differential test against an oracle, **stronger** than an LLM-judge —
and every query self-labels, so the eval set bootstraps itself.

Three disciplines are load-bearing:

1. **The oracle is repo-grep, not the store** — else it is circular. Grep-vs-store tests
   whether the stored graph matches *reality*, which turns finding-0059/0061's staleness
   anxiety into a **monitored sensor-fidelity number**. *(A hand-run demo over the live 61k-edge
   store already caught it: code-side recall ~5/7 — two stale files; doc→doc recall 0/16.)*
2. **Golden-set firewall.** Auto-accumulated query→oracle pairs are a *candidate* eval set,
   **never** the frozen sacred golden set (Constitution §9 — human-only, deliberate, logged).
3. The record may itself become an **observation stream** (a `φ_ref`, dual to `φ_self`) —
   Ouroboros measuring its own reference accuracy over time.

The fable pass added a fourth measurable: the **alignment instrument** — project `K_sem` onto
the structural spectral manifold and report the energy fraction (how graph-explainable the
embedding is) and its spectral filter shape. Deterministic, gauge-invariant, Thread-C-gradable.

### 2.7 The diachronic interpreter (Ruling B)

**Decision (fable, 2026-07-14).** The temporal structure — the graph's *direction/velocity*, not
only its state — enters the dreamer path as a **DISTINCT diachronic interpreter, not a second mode**
of the synchronic dreamer. `[capsule B; grounds in interpreters.py:64,269; edge-dynamics §2.1;
provenance.py]`

- **Different input domain forces it.** The synchronic dreamer reads `G_MR` — one MirrorView
  snapshot, authored-only, embedder-mediated. The diachronic reader needs a *sequence* of snapshots
  + `X_cite` + the supersession/version chains. The lens signature *extends* `φ_i : G_MR → 2^K` to a
  temporal-context input — a contract extension, not a mode flag.
- **The codebase already left the temporal-shaped hole** — `change_point` is a *registered but
  deferred* seam (`interpreters.py:64,269`) that returns nothing rather than fake a trend because
  "MirrorView does not yet carry a per-note temporal axis." The diachronic interpreter unblocks it
  by reading a *different* substrate, not by bolting time onto MirrorView. **The architecture
  anticipated the split.**
- **The Lane A/B firewall forbids folding it in** (`edge-dynamics` §2.1: "Lane A never touches the
  mirror-side dream path"). A reader of the *dynamics* is Lane B / correlator-class.
- **Two tiers.** A **corpus-structural** tier over `X_cite` (who-cites-what, mirror-safe per C1) can
  ship earlier; the **weaving through observed planes** (cost/documentation/scope) is the Lane-B
  tier = the **Track D charter**.
- **The lens contract still binds** (either tier): `Claim(statement, support ⊆ authored notes)`,
  model-free (the §9 deterministic floor), no in-lens adjudication (R1 adjudicates), lands
  INTERPRETED (the `derives` hyperedge, `provenance='interpreted'`, INTERPRETED ∉ MIRROR_READABLE),
  **zero back-action**, erasure-invariant, verdict/promotion-gated via `core/provenance.py`
  (`promote()` — owner verdict only; a drift claim can never silently become a belief). Admissibility
  additionally requires the **A7 signal-vs-noise discriminator** (`dn-temporal-retrieval-algebra`
  §2.5) — else it reads embedding noise as drift.

**The recursion resolved.** The dreamer once surfaced, from the owner's own notes, "should the
founding corpus be a fixed anchor, or is its transformation the phenomenon to track?" The diachronic
interpreter *tracks the transformation of corpus structure* and PROPOSES (INTERPRETED) readings of
it — **while the founding corpus itself stays a fixed anchor** (non-negotiable #9: fixed points are
never auto-modified). The instrument tracks the drift; it never touches the fixed point.

## 3. Consequences — what this note licenses (on ratification)

1. **The doc→doc reference extractor** (a small build plan) — parse `design_ref:`, `links:`,
   `[[name]]`, and `path:line` citations across `docs/**` into `corpus_to_corpus` edges. It is
   **cross-warranted**: finding-0059/0061 (agent bookkeeping) *and* the math test — the fable
   pass showed every empirical claim in §2.5 (flatness, F2 violations, diamond holonomy, the
   citation-side alignment) is **blocked on these edges**. It is the concrete unblocker for both
   halves and the recommended *first* graduation from this note.
2. **The reference query surface** (§2.3) — a `ReferenceView` and/or an addressable reference
   agent; and the **capability-scope type system** (§2.1) it is the first client of.
3. **The boundary scope grammar** (§2.4) — the machinery that expresses `the-sacred-boundary`
   as a scope rather than a special case.
4. **The self-grading harness + the alignment instrument** (§2.6) as Thread-C measurables.
5. **The math successor `dn-temporal-retrieval-algebra`** (NOW DRAFTED, 2026-07-14) carries the
   formalized algebra — the normalization triple, the `σ_*`/`π_active` operators, the five §2.5
   results theorem-grade, `X_cite`, the A7 discriminator, β\*. This note keeps the math as *stated
   results*; the successor makes them theorem-grade. The **Track D weaving-consumer charter** (the
   diachronic reader's Lane-B tier, §2.7) is the third note.

This note builds nothing itself. Its first plan is the doc→doc extractor; the reference agent
and the protocol type system follow.

## Parked decisions

| Decision | Default recorded | Re-entry condition |
|---|---|---|
| The normalization triple (cost dictionary; directedness; `(β,z)`) | ✓ **RESOLVED** (fable): `c=−log w` is the walk cost, `1−sim` the orthogonal Rips scale; symmetrized backbone + magnetic-Laplacian upgrade; z's bound IS the γ-ceiling — `dn-temporal-retrieval-algebra` §2.1 | — (settled) |
| One note or two | ✓ **RESOLVED → THREE notes** (fable C5): this (architecture) + `dn-temporal-retrieval-algebra` (math) + the Track D charter; never an edit to ratified `edge-dynamics` | — (settled) |
| `supersession-lifecycle §4.5` — does promotion re-anchor stratum depth? | ✓ **RULED (fable C4): promotion RE-ANCHORS depth** (the *contractive-except-at-owner-verdicts* branch) — the dynamics forces it: unconditional contraction makes the corpus a pure dissipator, so the owner verdict must be the only energy source (non-negotiables #3/#5/#9). **OWNER RULING (2026-07-14):** re-anchor to **shallowest-derived** (keeps the derived/authored firewall; not authored-K₀ depth-0) | settled; the graduating plan implements it |
| Weighted vs combinatorial inner products (PD-b, inherited from `edge-dynamics`) | combinatorial (v1); the metric tier of §2.5 is a second customer — `dn-temporal-retrieval-algebra` TA-a | when the metric-coherence tier is built |
| The two mode-3 operators (ledger-compression vs correspondence) | ✓ **RESOLVED (fable C3/A2): NOT peers** — `π_active` is the ambient default (`T=now`); `σ_*`/`σ^*` are the opt-in temporal traversal — `dn-temporal-retrieval-algebra` §2.2 | the protocol type-system plan (naming lands) |
| Where kernel-representability is lost along the curve (`β*`) | ✓ **RESOLVED (fable A8): β\* finite iff `d_∞` is not of negative type** (generic on sparse cyclic citation graphs); the RSP *kernel* stays PSD — only the *distance* loses negative-type. Now computable (bp-026) | a Thread-C β-sweep on the citation metric |

## Cross-references

- `docs/brainstorms/core-query-protocol.md` — the warrant; all four threads, the two opus
  formalization sketches, and the **fable rigorous pass** (2026-07-13 capsules) with the full
  derivations and literature this note summarizes.
- `docs/design-notes/edge-dynamics.md` — the 1-form lift, the Helmholtz/Hodge decomposition
  (`P_grad + P_harm + P_curl = I`), `L₁` as the Fourier basis, the THREAD lens (`P_harm`), the
  Lane A/B seam. The math successor extends its Lane B.
- `docs/design-notes/temporal-retrieval-algebra.md` — **the math successor** (drafted 2026-07-14):
  the normalization triple, the `σ_*`/`π_active` operators, the §2.5 results theorem-grade, `X_cite`,
  the A7 discriminator, β\*. This note's §2.2/§2.4/§2.5/Parked defer to it.
- `docs/brainstorms/edge-dynamics-lane-b-fable-pass.md` — the **2026-07-14 fable warrant**: the full
  derivations, grades, and rejected alternatives behind the C1–C5 rulings and Ruling B folded in here.
- `docs/design-notes/recursive-strata-amendment.md` — `γ^d` (Invariant 10), the typed
  `edge_budget` (grounding/lateral/cross-stratum), fibers vs dispositional edges.
- `docs/design-notes/supersession-lifecycle.md` — the dispositional edge; §4.5 (the Parked
  dichotomy); §7 (rename identity — the data prerequisite for §2.5's flatness measurements).
- `docs/design-notes/the-sacred-boundary.md` — the plane-crossing the §2.4 scope ruling draws.
- `docs/design-notes/capability-evaluation-harness.md` — the home for §2.6.
- `docs/design-notes/observed-data-and-the-assistant-tier.md` — the mirror firewall §2.1/§2.4
  inherit.
- `docs/findings/finding-0059.md`, `finding-0061.md` — the bookkeeping warrant (doc→doc
  blindness; stale-baseline class); `finding-0062.md` — the direction finding this note graduates.
- `core/stores/reference_edges.py` — the live substrate (61k edges) + its minimal query API;
  the Views `core/mirror.py`, `core/sensing.py`, `core/ops_view.py`, `ops/effects.py`;
  `core/librarian/librarian.py` (the semantic-RAG client); `core/complex/hodge.py` (the built
  degree-1 Hodge object the algebra sits over).
