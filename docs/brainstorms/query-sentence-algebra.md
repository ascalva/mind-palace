# Brainstorm — the query sentence algebra: verbs with nouns, adjectives and hypotheses

> Captured by the Lean-ladder session from owner chat (2026-11-04, Remote Control, Fable 5.1),
> while Phase 4 of the ladder closed MF-6. Three seeds in one sitting, near-verbatim below; each
> is the owner's, the chew is the session's. The seeds grew out of a question the session had
> answered a turn earlier: how the edge classes (supersession, reference, causal, distance) fit,
> and whether the query algebra sits on top of everything or the ladder mostly proves analysis
> methods.

## 2026-11-04 (lean-ladder session)

### Seed 1 — compose the verbs

Owner, near-verbatim: *"can't we use these verbs with nouns, and even adjectives? like composing
a sentence, can we compose verbs to describe a search more properly? i don't like that it seems
like a search, what i would commonly think of as a generic term, is just the base case here, to
me, the seems like it misses the point of all this machinery."*

### Seed 2 — a language, with a compiler

Owner, near-verbatim: *"i think both will need to happen together, letting both help guide the
design, theory/grammar language, and the proofs they sit on, once we have a proven out design,
then we begin the build, let's be ambitious. that's also why i once brought up looking into
compiler/optimization tools, the language consists of a grammar, like any other language, it must
be followed, set precedents, and optimize provided instructions into a search plan, and resolve
ambiguities."*

### Seed 3 — hypotheticals, and their responses

Owner, near-verbatim: *"could such a language support hypotheticals? that is, giving a set
assumption, followed by a query? like assume some type of connection exists between these two
topics, then how does this other relationship get impacted? or does the meaning change? given
some perturbation, how does the graph respond?"* And, on the session's first answer (an assumed
edge lowers every effective resistance, by Rayleigh): *"can't an assumption also increase
effective resistance? like, for example, assuming a contradiction? some paths increase in
resistance, some decrease."*

### The session's chew (offered to the design note, which decides)

- **What `core/query.py` has is a sentence of one word.** A query is `(verb, s)`: eight verbs,
  one scope each, admitted iff `req(verb) ⊑ grant`, its mode a corollary of the scope. SEARCH is
  the embedding Gram kernel's column at the query text, the generic point of the PSD cone
  (dn-core-query-protocol §2.2, the Moore–Aronszajn inversion). The machinery the owner means,
  the cone's `+`, `⊙` and congruences, the path semiring, the β-curve, the transports, is what
  the connectives, adjectives and chain nouns would compose; the verbs alone cannot reach it.
- **Nouns are sorts.** Region (a set of atoms), Field (a score per atom), Kernel (a PSD matrix),
  Metric, Relation (one move class), Chain, Witness. Each sort has the algebra its structure
  gives it and nothing else: kernels close under `and` (Schur) and `or` (sum) and `within`
  (congruence), not under `not` or `max`; a metric reaches the cone only through negative type;
  a Field becomes a Region only by a threshold or a top-`k`, the one lossy step.
- **Adjectives are masks and indices.** `within` a region, `as of` a cut (the index, never a
  letter: fiber-geometry §2.3-8), `via` a path language over `Σ_move` (the product automaton
  of fiber-geometry §2.3), `over` strata, `with` the dials (β, k, depth, direction).
- **The compiler is an evaluator of a rewriting system whose rules are theorems.** Parse,
  elaborate (defaults from a resolution ledger), check (sorts; the clause-wise scope check; the
  mode), plan (push masks to the leaves, flatten `and`/`or`, take columns instead of kernels at
  an anchor, rank last, compile `via` to the product walk, hoist the cut), execute, explain (the
  plan rides with the answer). Each rewrite is a proved identity, so plan and sentence denote
  the same thing by construction.
- **Precedents, two senses.** Operator precedence (adjectives tightest, then `and`, then `or`,
  then `then`; `not` only on regions) and resolution precedents: an ambiguity the owner resolves
  once is recorded with a default and a re-entry condition, like a parked decision, and the
  compiler applies it next time. What no precedent settles is refused with the readings listed,
  never resolved silently (the loud-failure rule of scoped-context-queries).
- **Hypotheticals are a modality.** `assume Δ in s` evaluates `s` on the store perturbed in the
  `hypothetical` overlay stratum, which the scope algebra already has (`Stratum.hypothetical`,
  `internal_actor`'s staging, `E_STAGED`). A result under `assume` carries its assumptions in its
  type, `Hyp(Δ)`, as `Rate(κ)` carries its clock; it is never `Inv`. The response is the
  difference between the two evaluations. A grant must name the overlay; the Ambassador's does
  not, so hypotheticals are opt-in even for the fullest grant (`top()` omits the overlay).
- **The owner's correction is right and sharpens the response laws.** Rayleigh (CND-2) is a
  statement about adding conductance of the sign the form already has: an assumption that adds
  weight lowers every effective resistance, one that removes or weakens an edge raises every one
  along paths through it, by the same theorem read backwards. A contradiction is a negative edge:
  it adds `|δ| (e_u + e_v)(e_u + e_v)ᵀ` to the signed Laplacian, along the anti-alignment mode,
  lowers the cost of `u` and `v` disagreeing, moves aligned-mode quantities with no uniform sign,
  and lifts the zero mode exactly when it closes a frustrated cycle (LAP-5, LAP-6): the graph has
  no consistent sign potential any more. So the sign laws hold within a sign class; a mixed or
  signed assumption gets the exact rank-one response, Sherman–Morrison, per pair.
- **Which verbs lie about their noun.** `required()` types DIFFUSE, HYBRID and RELATED as
  `E = {F}`, citation-structural, while DIFFUSE and HYBRID walk the similarity backbone and
  RELATED walks the signed relation edges, which are in no move class of `Σ_move`. The noun makes
  that a type error the verb table hides. A `core/` matter, for the owner.

```capsule
topic: query-sentence-algebra
date: 2026-11-04

decisions:
  - The owner's seeds: a query composes verbs with nouns and adjectives into a sentence; the
    language has a grammar, a compiler that plans and optimizes, precedents, and ambiguity
    resolution; hypotheticals are sentences under an assumption, with the graph's response the
    question. Design and proofs proceed together; the build follows a proven design.
  - The frame the chew proposes (the design note decides): nouns are sorts with the algebra
    their structure gives; adjectives are masks and indices; connectives are the cone's and the
    semiring's operations; `assume` is a modality whose results are typed `Hyp(Δ)`; the planner's
    rewrites are theorems.

parked:
  - decision: the law-family prefix for the composition laws
    default: QSA (query sentence algebra) in the design note and the Lean docstrings, unbolded,
      with no ledger rows until code relies on a law
    re_entry: the owner rules the prefix when the first row lands, as with RSP
  - decision: the move class of RELATED's signed relation edges
    default: none; RELATED stays typed as the code types it
    re_entry: the owner rules whether the relation edges are a fifth letter, an overlay class
      like E_STAGED, or a reading of S with a sign

open_questions:
  - Does the natural-language front end (a model proposes a sentence, the compiler checks it)
    belong to the Ambassador, or to a `/context` skill that agents call?
  - Which assumptions are expressible: a signed weighted edge, a severed edge, a hypothetical
    supersession, a reweighting; and is a hypothetical supersession a change of `π_active` or a
    D-move in the overlay?

next_steps:
  - docs/design-notes/dn-query-sentence-algebra.md, drafted with its composition laws proved in
    formal/Palace/Sentence.lean (this session).
  - The falsifier battery: real palace questions where a composed sentence must beat flat
    search, scored against owner-endorsed answers at build time.

references:
  - docs/design-notes/core-query-protocol.md                 # §2.2 the one algebra; SEARCH as the generic point
  - docs/design-notes/capability-scope-algebra.md            # §2.4 a query is (verb, s); mode as a corollary of scope
  - docs/design-notes/fiber-geometry.md                      # §2.0 Σ_move; §2.3 the chain language and the product automaton
  - docs/design-notes/temporal-retrieval-algebra.md          # §2.1 the β-curve; §2.2 π_active, σ_*, σ^*; §2.6 β*
  - docs/brainstorms/fiber-chain-grammar.md                  # the chain as a sentence; verb licensing
  - docs/brainstorms/scoped-context-queries.md               # a question compiles to bounds; loud failure; the lessons loop
  - core/query.py                                            # the eight verbs, required(), mode_of
  - formal/Palace/Scope.lean                                 # the scope algebra, machine-checked
```
