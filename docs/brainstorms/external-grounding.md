# external-grounding

**Origin — the root the whole arc grew from (owner, 2026-07-13).** This began from a concrete
engineering need, not philosophy: the owner wanted to use **Ouroboros itself** — the live daemon
+ reference store ([[ouroboros-naming]]), projected per-commit — as a way to *find references to
code*, so the **orchestrator and builders query a live, always-up-to-date self-index instead of
burning context searching for documents** (context-economy: cost is O(context × turns × tier)).
Everything below grew *outward* from that seed and serves one end — a richer, more precise live
index. The closing capsule (18:03) records the origin in full; read it first for the "why."

Owner raised two ideas mid-build-wave (2026-07-13, chat), seeking an honest read. Both are one
move under different guises: **ground the system's reasoning in externally-vetted truth rather
than model assertion.** Thread 1 grounds *computation* (a deterministic tool verifies the math
machinery); Thread 2 grounds *knowledge* (a curated strata of trusted literature supplies vetted
facts/theorems). Together they relieve fable as the single oracle for both correctness *and*
knowledge, and let a conclusion be **doubly-warranted** — a literature-grounded premise whose
computational instantiation is machine-verified. Natural extension of [[authorship-strata]];
routes into the `dn-core-query-protocol` fable-vet and answers finding-0062's reference-gap.

## 2026-07-13T17:24:39Z (captured)

```capsule
topic: external-grounding
date: 2026-07-13

frame:
  - Both ideas ground reasoning in EXTERNALLY-VETTED truth, not model assertion. Thread 1 grounds
    COMPUTATION (a checker verifies the math machinery); Thread 2 grounds KNOWLEDGE (curated
    literature supplies vetted facts/theorems). Together they relieve fable as the single oracle
    for correctness AND knowledge; a claim can be doubly-warranted (literature-grounded premise +
    machine-verified instantiation). This is the same trust move as CI attesting green, applied to
    the two ways a conclusion earns warrant beyond "a model said so."

thread_1_math_verification:
  decisions:
    - Adopt a deterministic math-verification tool so math correctness DECOUPLES from fable's
      scarce judgment. The model PROPOSES, a tool VERIFIES — the constitution's spine ("the model
      advises; code acts") applied to math.
    - OWNER FRAMING (2026-07-13, load-bearing): SymPy "is not proving the THEORY per se, it's
      proving the MACHINERY we are choosing to use." Names the object of proof precisely:
        * the THEORY = the modeling premise (e.g. "gamma^d is the right weighting for derivation
          depth", "this is the right normalization to impose") — stays owner/fable JUDGMENT;
        * the MACHINERY = the computational apparatus instantiating that premise (the normalization
          sums to 1, the identity holds, the series converges, the closed form is right) — THAT is
          what the checker proves.
      Sharper than "verifies computation not modeling": the checker attests the CHOSEN MACHINERY is
      sound; it never sanctions the choice itself.
    - Start with SymPy (Python-native, already in-stack, zero license, fully offline). Reserve a
      PROOF ASSISTANT (Lean 4 / mathlib, Coq, Isabelle/HOL) for the RARE load-bearing theorem an
      invariant rests on — formalization cost is real; don't pay it for routine identity/
      normalization/convergence checks a CAS handles cheaply.
  invariant_fit:
    - A math check is PURE COMPUTATION returning DATA (true/false, a simplified form) — a natural
      fit for Invariant 4 ("executed code returns data, never actions") and the sandbox.
    - HARD CONSTRAINT: LOCAL KERNEL ONLY. A network CAS (e.g. Wolfram Alpha API) violates
      Invariant 1 (sealed-core zero egress) AND Invariant 4. SymPy has no service at all — cleanest;
      a local Mathematica/Sage kernel is acceptable, a networked one is not.
  caveats:
    - AUGMENTS fable, never replaces it. Verified machinery on a wrong premise is a well-dressed
      wrong answer. The check raises warrant on the DERIVATION, not the PREMISE — do not let "the
      machinery checks out" masquerade as "the model is right."
    - The win is the DIVISION OF LABOUR: mechanical verification offloaded to a deterministic tool,
      so fable's scarce tokens go where only judgment works — the modeling choices.
  parked:
    - decision: where math-verification lives in the pipeline.
      default: a machine-checkable companion attached to the build-plan section 8 "Math carried
        explicitly" field (run like a test), with a standing "math gate" (analogous to type_gate /
        attestable-green) aggregating the companions.
      re_entry: the first math-bearing design note or plan that needs its math attested — prototype
        the section-8 companion + gate then; SymPy needs no design note to merely TRY.

thread_2_curated_strata_as_literature:
  decisions:
    - The CURATED strata is the home for TRUSTED EXTERNAL LITERATURE — math/physics/CS/engineering
      research, textbooks, papers, articles, vetted references — the substrate the system draws on
      to "form a specific connection using well-vetted literature" (owner). Answers finding-0062's
      reference-gap: the corpus today is all-INTERNAL (mirror + dialogue + code) with no principled
      home for external ground-truth knowledge.
    - Literature is a SECOND BEDROCK (K0), like the mirror — un-derived, high-warrant — but on a
      DISTINCT PROVENANCE AXIS. This forces a separation the internal-only taxonomy blurred:
      DERIVATION-DEPTH is NOT AUTHORITY. Literature is depth-0 AND high-authority AND not the
      owner's. So retrieval weight is not gamma^d over depth alone; it becomes
      depth x authority x domain-relevance.
    - Curation is HUMAN-GATED by design. "Well-vetted" makes this stratum behave like the golden
      set / CONSTITUTION ("the fixed points are sacred" — human-only, deliberate, logged), NOT like
      the freely-growing dialogue corpus. TRUST IS EARNED BY CURATION COST. Bar for entry:
      authoritative source + bridges a real gap the system actually has + owner-vetted. It grows
      only as fast as the owner curates — that constraint IS the point, not a limitation.
    - CITATION BECOMES WARRANT. A connection "owner-note <-> [Rudin, Principles, Thm 3.4]" is
      categorically more trustworthy than "owner-note <-> agent-brainstorm", and it is CITABLE
      (ties to the book skill's citation scheme). Literature-backed edges carry their citation as a
      first-class property.

owner_framing_subjective_vs_objective:
  - OWNER (2026-07-13): the author strata and the curated strata "serve different purposes, they
    strengthen arguments of DIFFERENT DOMAINS, but help bridge a gap on SUBJECTIVE vs OBJECTIVE
    knowledge and how they relate."
  - The two AUTHORED bedrocks are the system's DUAL GROUNDING:
      AUTHOR strata (mirror)      = ground truth ABOUT THE OWNER  -> subjective / personal
                                    authority; strengthens subjective-domain arguments.
      CURATED strata (literature) = ground truth ABOUT THE WORLD  -> objective / field-vetted
                                    authority; strengthens objective-domain arguments.
  - The CENTRAL design question is HOW THEY RELATE — the subjective/objective interface:
      * when the owner's subjective belief is GROUNDED BY (or CONTRADICTS) objective literature;
      * when objective literature is made PERSONALLY RELEVANT through the owner's subjective frame.
  - Proposed rule of thumb: subjective/personal questions -> the mirror wins; objective/factual
    questions -> the literature wins; a mirror<->literature CONTRADICTION is a HIGH-SIGNAL event to
    SURFACE, never to silently resolve — arguably one of the most valuable things this stratum
    unlocks (the system can flag "what you believe diverges from the vetted record here").
  - Scaffold (ANALOGY, not authority): Popper's Three Worlds maps cleanly — World 2 (subjective
    mental states) ~ the mirror; World 3 (objective knowledge: the content of theories, books,
    libraries) ~ the curated literature strata; the subjective<->objective RELATION is exactly the
    epistemology World 2/World 3 frames. Polanyi's "personal / tacit knowledge" names the
    subjective (mirror) side. Cited as a lens, not a proof.

connections:
  - finding-0068 (reference-graph kinds as a derivation gradient): this REFINES it — separates
    derivation-depth from authority; literature is a depth-0 HIGH-authority kind the pure-depth
    gradient did not have. The gamma^d weighting must generalize to depth x authority x relevance.
  - finding-0062 (reference-gap direction): Thread 2 ANSWERS it.
  - dn-core-query-protocol (drafted; fable-vet gated to Jul 17): Thread 2 feeds its kind vocabulary
    (sections 2.1 / 2.4 / 3.1). The vocab {code, mirror, dialogue, workflow} gains a 5th kind
    (reference / literature) — arguably the most important for the bridge-a-gap use case.
  - [[authorship-strata]]: this is its natural extension — author (subjective) vs curated
    (objective) as the two K0 bedrocks, distinguished by provenance axis, not depth.
  - Invariants 1 / 4 / 11: both threads fit. Literature ACQUISITION is a human/network/
    outside-the-core act at CURATION time; the vetted artifact then lives in the LOCAL corpus and
    the sealed core reasons over it offline — the corpus never transits a third party at query
    time (Invariant 11).
  - book skill citation scheme; build-plan section 8 "Math carried explicitly".

open_questions:
  - Taxonomy placement of literature: a second K0 on a distinct provenance axis (my read) vs a
    fully separate dimension — settle in the dn-core-query-protocol fable-vet.
  - The weighting FUNCTION once authority is decoupled from depth: what combines
    depth x authority x domain-relevance, and does it stay a gamma^d family?
  - Copyright / attribution of ingested third-party text (private local use is fine; every
    literature-backed edge should carry attribution — citation-as-warrant makes this cheap).
  - The mirror<->literature contradiction handler: surface-only, or a structured reconciliation
    protocol? (Surface-only is the safe default; reconciliation is a later design question.)

next_steps:
  - Route Thread 2 into the dn-core-query-protocol fable-vet (gated Jul 17) — bank this capsule
    against it; it directly informs the kind-vocabulary + the depth-vs-authority split.
  - Thread 1 is prototype-able SOONER (SymPy is sandbox-native, needs no design note to try); the
    only design-note question is WHERE verification lives (section-8 companion + math gate).
  - Consider a dedicated design note "external-grounding" once the fable-vet settles the kind
    vocabulary, unifying both threads under the doubly-warranted-claim frame.

references:
  - SymPy: Meurer A. et al., "SymPy: symbolic computing in Python", PeerJ Computer Science 3:e103
    (2017), doi:10.7717/peerj-cs.103 — the recommended Thread-1 CAS (offline, Python-native).
  - Lean 4 + mathlib: The mathlib Community, "The Lean mathematical library", CPP 2020 — proof
    assistant for the rare load-bearing theorem (leanprover.github.io).
  - Coq: The Coq Development Team (coq.inria.fr); Isabelle/HOL: Nipkow, Paulson & Wenzel,
    "Isabelle/HOL: A Proof Assistant for Higher-Order Logic", Springer LNCS 2283 (2002) —
    alternative proof assistants.
  - SageMath: The Sage Developers (sagemath.org) — a heavier CAS if SymPy is outgrown; use a LOCAL
    kernel only (Invariant 1).
  - Popper K., "Objective Knowledge: An Evolutionary Approach" (Oxford, 1972) — World 3 (objective
    knowledge as the content of theories and libraries) ~ the curated literature strata; World 2
    (subjective mental states) ~ the mirror.
  - Polanyi M., "Personal Knowledge: Towards a Post-Critical Philosophy" (Chicago, 1958) — tacit /
    personal knowledge ~ the author (mirror) strata.
```

## 2026-07-13T17:40:12Z (captured)

```capsule
topic: external-grounding
date: 2026-07-13
thread: citation-as-free-edge — the curated strata's INGRESS mechanism

owner_insight:
  - OWNER (2026-07-13): "the first way of curated text is determined by our own
    documentation: you just cited real articles when I asked you to apply references — in
    other words, we are relying on the fact that those references are accurate. So if you
    reference a construction, operation, theorem, a research article, etc., that seems like
    a good candidate for external curated data — a clear reference that forms an edge FOR
    FREE."
  - Self-referential proof-point: the capsule ABOVE already contains real citations (SymPy /
    Meurer 2017, Popper, Polanyi, mathlib). Those citations, sitting in a brainstorm, are
    THEMSELVES candidate edges into the curated strata. The system's own documentation is its
    first curation pipeline — dogfooding.

the_mechanism:
  - The curated strata does NOT have to be hand-built. Every citation already embedded in the
    corpus (design notes, findings, brainstorms) IS a corpus->literature edge waiting to be
    EXTRACTED. Same pattern as the dialogue layer: we don't author edges, we extract them from
    what's already written.
  - CONCRETE SUBSTRATE — this is already half-built: bp-026's doc->doc extractor (phi_doc)
    already parses front-matter design_ref/links, inline note-citations, and wikilinks into
    reference_edges. EXTENDING it to EXTERNAL citations (DOIs, arXiv ids, "Thm X.Y in [Author,
    Title]", article references) makes the curated strata grow from our own writing at ZERO
    marginal curation cost. The reference is the edge; the edge is free.

trust_is_the_catch (owner named the vulnerability):
  - "We are relying on the fact that those references are accurate." LLM-authored citations are
    notoriously hallucination-prone (fabricated papers, wrong theorem numbers, misattribution).
    So a free edge carries a TRUST DEBT: it is only as good as its verification.
  - This is an ARGUMENT FOR the verification layer (Thread 1), not against the idea — and it is
    where the two threads MEET. An external citation is a CHECKABLE claim about the objective
    world (does the DOI resolve? does the source exist? does the theorem say what we claim?) —
    unlike a subjective belief, which is not falsifiable this way. Objective knowledge is
    vettable BY DEFINITION; that is what makes the curated strata curatable at all.
  - So the edge has a MATURITY GRADIENT: asserted (an agent wrote the citation) -> verified
    (source confirmed to exist / say what we claim) -> ingested (the actual content curated +
    embeddable). "A good CANDIDATE for external curated data" (owner's exact word) — a
    candidate, promoted to curated by verification. Free edge = coverage; verification = trust;
    you need BOTH, or the strata fills with plausible-but-wrong citations (the exact opposite of
    "well-vetted").

node_lifecycle:
  - A cited-but-not-yet-ingested reference is a PLACEHOLDER node — exactly like a wikilink to a
    not-yet-written note (the memory system already does this: "a [[name]] that doesn't match an
    existing memory yet is fine; it marks something worth writing later"). The external ref node
    starts "referenced" and matures to "curated" when the real source is ingested.
  - The corpus's own citations therefore become a WORKLIST for curation: extract all external
    references -> that IS the queue of what to vet + ingest next. Curation becomes demand-driven
    (we curate what we actually cite) rather than a boil-the-ocean library build.

symmetry:
  - This mirrors the mirror<->literature contradiction detector (prior capsule): both are "does
    our internal representation match the objective record?" checks. There, the owner's belief vs
    the vetted source. Here, the agent's citation vs the actual source. Same objective-grounding
    move, two applications.

transitive_citation_expansion (owner, 2026-07-13):
  - The recursion: an external document WE reference has its OWN references to further external
    articles/documents — so THOSE are candidates for more curated documents. The strata grows not
    only from our corpus's citations but from the BIBLIOGRAPHIES of the sources we curate. Each
    ingested source's reference list IS the worklist of next candidates.
  - This is academic CITATION-GRAPH crawling / snowball sampling (backward-citation chasing): the
    frontier expands one hop per ingestion, and it makes the curated strata a genuine GRAPH with
    literature->literature edges, not a flat set. The graph structure itself becomes signal —
    co-citation, bibliographic coupling, high in-degree = foundational/authoritative. (Prior art:
    Semantic Scholar, Connected Papers, citation-network analysis; snowball sampling in systematic
    reviews.)
  - BOUNDING IS THE DISCIPLINE. Uncontrolled, the transitive frontier IS all of science
    (everything cites everything). The finding-0068 gamma^d discount REUSES here beautifully:
    citation-distance is a derivation-depth-like axis, so a source d hops from our corpus carries
    weight gamma^d — relevance decays with citation hops, damping the crawl naturally. Promotion
    stays DEMAND-DRIVEN (verify+ingest a 2nd-level ref only when our reasoning needs it, or the
    owner curates it): the frontier is vast, the ingested core stays small.
  - TRUST INVERSION worth noting: a 2nd-level citation made by a CURATED SOURCE (a peer-reviewed
    textbook's bibliography) is a HIGHER-trust candidate than our own agent-authored citation — the
    citing source was itself vetted. So WHO made the citation weights its candidacy: agent-asserted
    -> verify hard; curated-source-asserted -> stronger prior. Verification still gates; the prior
    differs.

decisions:
  - The curated strata's PRIMARY ingress is citation-extraction from our own corpus, not manual
    library import. A clear external reference (theorem / construction / operation / article) in
    any note is a candidate corpus->literature edge, extracted for free by an extended phi_doc.
  - Every such edge is born UNVERIFIED (state: asserted); it is a candidate, not a curated fact,
    until a verification step confirms the source. Warrant on the edge = source authority x
    verification state.

open_questions:
  - Citation-extraction grammar: what external-reference forms does phi_doc recognize (DOI, arXiv,
    ISBN, "Author, Title (Year)", "Thm N in X")? Start narrow (DOI / arXiv / explicit Title+Year)?
  - The verification step: fully manual (owner confirms), or a bounded automated check (DOI
    resolves, arXiv id exists) that still never fetches content into the sealed core (Invariant 1 —
    resolution is an edge/, outside-core act, like literature acquisition)?
  - Does an unverified citation edge participate in retrieval at all, or only after promotion? (Lean
    conservative: unverified edges are visible-but-flagged, never load-bearing.)

next_steps:
  - Fold into the dn-core-query-protocol fable-vet: the `reference`/`literature` kind needs a
    verification-state on its edges (asserted / verified / ingested), and phi_doc's citation
    grammar is the ingress. Bank against the Jul-17 fable pass.
  - A future plan (post-vet) extends bp-026's phi_doc extractor to external citations, emitting
    `reference`-kind edges in the `asserted` state — the free-edge harvest. Verification + ingest
    is a separate, owner-paced stage.

references:
  - bp-026 / phi_doc doc->doc extractor (docs/build-plans/bp-026/) — the concrete substrate this
    extends; already parses internal citations + wikilinks into reference_edges.
  - The memory-system placeholder-link convention (unresolved [[name]] is valid) — the model for a
    cited-but-not-ingested placeholder node.
```

## 2026-07-13T17:50:34Z (captured)

```capsule
topic: external-grounding
date: 2026-07-13
thread: ratification is the promotion gate — WHEN a citation becomes curated

owner_insight:
  - OWNER (2026-07-13): "When we discuss math and technical reasoning, we reach for references —
    we ground our logic to prove its SOUNDNESS upon external reference. The second we reference
    that doc in our documentation, we've MOVED FORWARD with that external idea's utility. Once the
    DESIGN DOC IS RATIFIED, its utility is being REALIZED — which is a good time to INGEST the
    external curated document."

the_gate:
  - ANSWERS the prior capsule's open question ("what is the demand signal for promotion?"). The
    demand signal is RATIFICATION. The vast candidate frontier is filtered to the EARNED CORE by
    the artifact chain's existing owner-only blessing gate (draft -> ratified).
  - Promotion gradient mapped onto the artifact chain:
      cited in brainstorm / DRAFT note  -> `asserted` candidate (free edge, tentative, weak)
      cited in a RATIFIED design note    -> PROMOTE: verify + ingest -> `curated` (load-bearing)
    Ratification is the moment the owner BLESSES an argument that DEPENDS ON the reference; the
    reference's utility is now realized in a ratified artifact, so its curation is EARNED.
  - Demand-driven promotion with a crisp, PRE-EXISTING gate — no new human ceremony. Ratification
    is already the deliberate, logged, owner-by-hand act (CLAUDE.md: draft->ratified is never done
    in-session — the blessing fence). The reference ingestion RIDES that same act: a note's
    ratification and its load-bearing references' curation become ONE coordinated blessing.

convergence_of_both_threads:
  - A math/technical argument in a design note is grounded TWO ways: (a) its cited theorems /
    constructions — Thread 2, curated at ratification; (b) its computational machinery — Thread 1,
    SymPy-attested. RATIFICATION is where BOTH lock in: the references verified+ingested, the
    machinery checked. The gate seals a DOUBLY-WARRANTED technical argument — reference-grounded
    AND machine-checked (the frame's doubly-warranted claim, finally realized at a concrete gate).
  - So ratification stops being merely "the owner agrees" and becomes "the argument's full warrant
    is SEALED": premises grounded in vetted literature, machinery verified sound.

refinement (load-bearing vs contextual):
  - Not every citation in a ratified note is equally load-bearing. The SOUNDNESS-BEARING refs (the
    argument's validity depends on them — "ground our logic to prove its soundness") are the
    priority ingests; "see also" / related-work mentions can stay `asserted` candidates. Demand =
    LOAD-BEARING, not merely mentioned — else a 40-item related-work list forces 40 ingestions.

seed_set:
  - A FORWARD rule (new ratifications trigger curation), but the CURRENT corpus's already-ratified
    notes' citations are the initial curation WORKLIST — dn-self-sensing and the other ratified
    notes; their load-bearing references seed the curated strata's first fill.

decisions:
  - The promotion gate from `asserted` candidate -> `curated`/ingested is RATIFICATION of the
    design note that cites the reference load-bearingly. Curation rides the existing owner-only
    draft->ratified blessing; it is part of what the owner blesses.
  - At ratification, a note's load-bearing external references are VERIFIED then INGESTED, and its
    computational machinery is ATTESTED (Thread 1). Ratification seals a doubly-warranted argument.

open_questions:
  - Marking load-bearing vs contextual citations (an explicit split, e.g. `grounds:` vs `see-also:`
    in note front-matter, so the gate knows which refs to ingest)?
  - Does ratification-triggered ingestion stay fully owner-manual, or does the gate PRESENT the
    load-bearing refs for one-click owner confirmation (human-in-the-loop on curation, per the
    golden-set-like trust posture)?

references:
  - CLAUDE.md artifact chain (brainstorm -> design note draft->ratified -> build plan -> ...) — the
    ratified gate this rides; draft->ratified is owner-by-hand, never in-session (the blessing
    fence), which is exactly why it is the right curation trigger.
```

## 2026-07-13T17:53:57Z (captured)

```capsule
topic: external-grounding
date: 2026-07-13
thread: THE LARGEST LOOP — curated strata as cross-strata connective tissue; the complete warrant circuit

owner_realization:
  - OWNER (2026-07-13): "This closes an even larger loop. Even as we brainstorm, design, and build,
    we are ALSO actively ingesting externally-validated, more OBJECTIVE data — and it connects to
    the rest: to DIALOGUE (brainstorms and design), to the OBSERVED (the code that implements the
    idea), and to my AUTHORED strata (the origin, via intuition)."

the_insight:
  - The curated (objective) strata is NOT a silo — it is CONNECTIVE TISSUE threading through the
    entire existing graph. It links to every other kind:
      curated <-> authored/mirror : the owner's subjective intuition is the ORIGIN; the literature
                                    GROUNDS/validates (or contradicts) it. Subjective spark meets
                                    objective confirmation. (The mirror<->literature relation from
                                    the earlier capsule lives on this edge.)
      curated <-> dialogue        : the citation lives in the brainstorm/design note that reaches
                                    for it to prove soundness — the ingress edge.
      curated <-> observed (code) : the external idea is REALIZED in code; a theorem/construction
                                    cited in a design note is implemented in a module. The literature
                                    node connects forward to the code that instantiates it, and the
                                    code back to the external truth it implements.
  - THE BUILD PROCESS IS A CURATION PROCESS. Ingesting objective knowledge is not a separate
    activity — it is a BYPRODUCT of doing the work: brainstorm reaches for a reference, design
    grounds on it, ratification ingests it, code realizes it. The corpus grows in OBJECTIVE
    knowledge automatically as a function of building. A FLYWHEEL: the more the system works, the
    more externally-grounded it becomes.

the_design_note_is_the_join:
  - The curated<->code edge is TRANSITIVE THROUGH the dialogue/workflow layers: the design note
    cites the external ref AND is the design_ref of the build plan that produces the code. So the
    NOTE is the hub where authored-intuition, objective-literature, and code-realization all meet.
    (bp-026's phi_doc already extracts doc->doc + doc->code; extending it to external refs makes the
    note the convergence point of ALL strata.)
  - This is WHY ratification is the promotion gate (prior capsule): the note is the JOIN across all
    strata, so blessing it seals the whole cross-strata circuit at once.

the_complete_warrant_circuit:
  - An idea's life becomes fully traceable across the subjective/objective divide:
      authored intuition (subjective ORIGIN, K0)
        -> dialogue (brainstorm/design: reasoned, grounded in literature)
        -> curated (objective external validation, K0', ingested at ratification)
        -> observed (code: the realization)
        -> workflow (the plans/journals of building it)
    Every stratum connects; the curated layer is what makes the circuit CLOSE WITH OBJECTIVE
    WARRANT. Without it the chain is intuition->discussion->code — all internal, self-referential.
    WITH it, the chain is ANCHORED to externally-validated truth at the design stage: conclusions
    trace from a subjective spark, through objective literature, to concrete running code.

what_the_system_IS (reframing):
  - The mind-palace is not only a MIRROR of one mind (subjective) nor only a SENSOR of its own code
    (observed) — with the curated strata it becomes a BRIDGE from the owner's subjective intuition
    to the world's objective validated knowledge, realized in code. The five kinds + their
    cross-connections ARE the system; curated was the missing piece that lets subjective and
    objective knowledge RELATE, and it turns out to connect to everything.

connections:
  - finding-0068 gamma^d gradient: now governs signal flow across the WHOLE cross-strata graph;
    curated is a high-authority K0 anchor any layer can reach (weight = depth x authority x
    relevance x citation-distance).
  - dn-core-query-protocol fable-vet: this is the UNIFYING FRAME the kind-vocabulary serves — the 5
    kinds are not a flat set but a connected graph with the design note as the join.
  - bp-026 phi_doc (doc->doc + doc->code extractor): the substrate for the curated<->code edge via
    the note.

next_steps:
  - Carry this whole arc into the dn-core-query-protocol fable-vet as THE FRAME: curated strata =
    objective connective tissue; the design note = cross-strata join; ratification = the circuit
    seal. The kind vocabulary + weighting must express CROSS-STRATA edges, not just intra-kind ones.
```

## 2026-07-13T18:03:19Z (captured)

```capsule
topic: external-grounding
date: 2026-07-13
thread: ORIGIN + ANCHOR — Ouroboros as a live self-index to cut context cost (the seed the whole arc grew from)

the_seed (owner — the practical motivation, captured last but it is the ROOT):
  - OWNER (2026-07-13): this entire discussion "stemmed from me wanting to use the OUROBOROS ITSELF
    as a way of finding references to code, which would be used by the ORCH or BUILDERS to cut down
    on the CONTEXT COST associated with trying to find documents. The system is a LIVE, ALWAYS
    UP-TO-DATE INDEX."
  - The philosophical arc (external grounding, curated strata, the cross-strata warrant circuit)
    grew OUTWARD from this concrete engineering need. It all serves the same end: a richer, more
    precise live index. Recorded last; it is the root.

the_mechanism:
  - Ouroboros (the live daemon + evolving corpus + reference store) already IS the index: the v2
    reference_edges graph (~188k edges — code<->corpus, doc->doc, doc->code) + code_observations,
    PROJECTED PER-COMMIT by the post-commit hook. It tracks HEAD continuously — that is the "always
    up-to-date" property, no staleness, unlike a static doc search.
  - THE USE CASE: instead of an agent GREPPING/READING to find "what code implements X" or "what
    note discusses Y" (expensive — context-economy: cost is O(context x turns x tier)), it QUERIES
    the graph, gets the precise pointers, and reads ONLY those. Search-by-context-burn is replaced
    by lookup-against-a-precomputed-live-index. This is a first-class CONTEXT-ECONOMY tool, not only
    an epistemics project.
  - This IS dn-core-query-protocol's core purpose: agents as SCOPED CLIENTS of a core-query algebra
    over the live index (three retrieval modes). The reference taxonomy (finding-0068) + the kind
    vocabulary (the fable-vet) matter BECAUSE they determine what you can query for — better kinds
    -> more precise queries -> more context saved.

why_the_arc_serves_the_seed:
  - The index is only as useful as its edges are correct and its node-kinds are right, so the
    taxonomy work is not academic — it is what makes the queries precise. The CURATED strata extends
    the index to a whole new queryable class (external literature): an agent can pull "the theorem
    this code implements" or "the paper that grounds this approach" from the SAME live index, so the
    context-cost win extends from internal code/docs to external knowledge.
  - The cross-strata warrant circuit (prior capsule) is what a query TRAVERSES: it can walk
    authored -> dialogue -> curated -> code and return a whole grounded chain as POINTERS, not prose
    — the agent reconstructs context by reading pointers, not by searching.

decisions:
  - The NORTH STAR is a LIVE SELF-INDEX that orch/builders query to cut context cost — the primary,
    near-term, buildable utility. The external-grounding synthesis is in service of it (richer index).
  - Freshness is guaranteed STRUCTURALLY by per-commit projection (the post-commit hook), not by a
    re-index chore — "always up to date" is a property of the substrate, already live on v2.

near_term_vs_frontier (honest separation):
  - NEAR-TERM, index-first win — does NOT need the fable-vet OR the curated strata: a query surface
    the orch/builders call to resolve "references to code/docs for X" against the LIVE v2 graph
    (which exists now, ~188k edges, per-commit). That is the context-cost tool the owner actually
    wants, buildable today.
  - FRONTIER — the curated strata + cross-strata edges + verification/ratification gates make that
    index RICHER and externally-grounded later; they route through the dn-core-query-protocol
    fable-vet (gated Jul 17). Do not let the frontier block the near-term index win.

references:
  - [[ouroboros-naming]] — Ouroboros = the LIVE system (daemon + evolving corpus), distinct from the
    mind-palace framework; this is that live system used as an index OF ITSELF.
  - context-economy skill — cost is O(context x turns x tier); a live index returning pointers is the
    structural answer to search-by-context-burn.
  - bp-026 / reference_edges v2 (~188k edges, per-commit projection) — the index substrate, live now.
  - dn-core-query-protocol (drafted) — the query algebra over the index; agents as scoped clients.
```
