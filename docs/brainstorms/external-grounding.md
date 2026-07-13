# external-grounding

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
