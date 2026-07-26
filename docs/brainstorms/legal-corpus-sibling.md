# legal-corpus-sibling

A stripped-down sibling instance, pointed at real case law. Fun side project — and, less obviously,
the first chance to validate the instruments against a corpus that has **ground truth**.

## 2026-07-26T07:52:00Z

```capsule
topic: legal-corpus-sibling
date: 2026-07-26

decisions:
  - THE IDEA (owner, 2026-07-26, verbatim): "could that be worth a fun side project? can a smaller
    duplicate of ouroboros (different settings/toml config) that is stripped down in featureset, not in
    resources, could it ingest a set of legal documents, and see if you can coherently prop a well
    researched argument?"
    ⇒ Arrived directly out of the Kafka observation (`docs/brainstorms/process-weight.md`), and the
    connection is not a joke: the artifact chain already IS common law -- precedent, standing,
    contradiction resolution, errata that stay inspectable. Pointing the machinery at actual case law is
    the natural test of whether that structure was real or decorative.
  - ⚑⚑ THIS IS THE FIRST CORPUS WITH GROUND TRUTH, AND THAT IS THE WHOLE VALUE. Every claim the palace
    makes about structure -- supersession lineage, citation graphs, contradiction resolution, "later
    supersedes earlier and says so", covering-only relations -- is a LEGAL structure. And case law
    supplies each one with an EXTERNALLY KNOWN CORRECT ANSWER: precedent = the citation graph,
    overruling = supersession, distinguishing = partial supersession, holding vs dicta = claim typing.
    The owner ratifies falsifiers, not proofs; this is the first corpus where the falsifiers can
    actually fire.
  - ⚑⚑ AND IT ATTACKS THE MEASURED BLOCKER HEAD-ON. `oq-0031` is still open: *"Connectivity/sweep
    instruments can't discriminate at 13-doc corpus scale: grow the corpus, defer validation, or accept
    built-but-unvalidated"* (findings 0096/0097/0098). A legal corpus is thousands of documents with
    dense, real, richly-annotated citation structure. ⇒ It takes the "grow the corpus" option **without
    growing the owner's private self-map** -- which DECOUPLES "validate the math" from "mine my own
    brain", two goals that have been forcibly coupled until now. That is the strongest argument for
    doing this, and it is not a side project's argument.
    Same unlock for `dn-supersession-recovery-evaluation` ("can the dreamer rediscover known edges?"):
    against real overrulings it becomes a scored test instead of a synthetic one.
  - ⚑ WHAT IS LEFT AFTER STRIPPING IS THE INTERESTING PART -- IT IS NOT A SMALLER OUROBOROS, IT IS THE
    NON-OUROBORIC HALF. Strip the self-referential layer: φ_self over the cost stream, the code corpus,
    the chat/dialogue sensor, the authorship-distance axis, the drift gauge against its own
    constitution, the effector layer. What remains is ingest → chunk → embed → retrieve, the
    citation/reference sensor, the supersession lifecycle, the reasoning complex + connectivity
    instruments, the dreamer. ⇒ The sibling is therefore a **CONTROL GROUP**: the palace running on data
    it did not author, about which it has no stake and no memory. Everything that makes Ouroboros
    *Ouroboros* is exactly what gets removed -- which is a clean way to find out how much of the value
    lives in the self-reference and how much in the machinery.
  - ⚑⚑ "NOT STRIPPED IN RESOURCES" COLLIDES WITH NON-NEGOTIABLE #8, AND THE CONFLICT IS ALREADY
    MEASURED. The ceiling is ≤2 resident models / ~24 GB usable. Two instances = two embedders + two
    chat tiers. And the accounting is already known-broken in two ways corrected only this week:
    finding-0174 (the embedder is INVISIBLE to the loader, and costs **10.0 GB** under Ollama's default
    ctx, not the 2.5 GB filed) and finding-0199 (the ceiling can be breached on crash-restart while its
    guard reports OK). So a second instance is not a config question, it is a ceiling question.
    Three ways, in ascending order of how much they unlock:
      (a) run the sibling ONLY while the main daemon is down -- the same "grant a window" pattern
          oq-0043 proposes for the fiber survey's S rows. Free, immediate, serialized.
      (b) ⚑ WAIT FOR bp-116/bp-118 (the process manager + embedder cutover to a palace-owned
          `llama-server`), which make residency a kernel fact and could let ONE embedder serve both
          instances. ⇒ The sibling then becomes a genuine SECOND CONSUMER of the process manager --
          which is what makes that abstraction honest rather than speculative. This is the option that
          pays twice.
      (c) separate hardware / the already-deployed cloud tier. Cleanest isolation, most cost, and it
          gives up the "same machine, same models" comparability that makes the control group a control.
  - ⚑ "DIFFERENT SETTINGS/TOML" IS PROBABLY NOT SUFFICIENT -- AND FINDING THAT OUT IS ITSELF THE PAYOFF.
    Whether a second instance can be stood up by config ALONE is a sharp test of the config layer: are
    corpus paths, store paths, model lineup, vault location, `reset_targets()` and every feature flag
    genuinely config-driven, or are there hardcoded singletons? `palace` already has fresh-start and an
    explicit reset-target registry, so instance-awareness partially exists. ⇒ The attempt is a
    **MULTI-TENANCY AUDIT disguised as a side project**, and every hardcoded path it trips over is a
    finding worth having regardless of whether the legal experiment ever runs.
  - ⚑⚑ THE OUTPUT IS THE WEAKEST LINK, AND IT NEEDS A STRUCTURAL BAR, NOT A STYLISTIC ONE. "Coherently
    prop a well-researched argument" is dangerous as a success criterion, because an LLM will ALWAYS
    produce fluent legal-sounding prose. Fluency is not evidence. Falsifiers that are externally
    checkable, in ascending sharpness:
      1. Do the cited authorities EXIST? (trivially verifiable; catches fabrication)
      2. Are they APPOSITE -- does the cited case actually support the proposition it is cited for?
      3. ⚑⚑ **Does it ever rely on an OVERRULED holding?** This is the killer test: binary, externally
         checkable, and precisely what the supersession machinery claims to solve. **If the sibling
         cites overruled law as good law, the supersession layer is decorative.** No amount of coherent
         prose survives that.
      4. Does it surface a NON-OBVIOUS connection that keyword search over the same corpus does not?
         That is the only test that distinguishes the palace from grep, and it is the one the
         connectivity instruments exist to earn.
  - NON-GOAL, PINNED UP FRONT because a non-goal is load-bearing and fails silently forever if wrong
    (finding-0150): **this produces no usable legal advice.** Non-negotiable #7 names legal explicitly
    -- consequential advice defers, is honest about uncertainty, refuses dangerous specifics, and the
    decision is the owner's and a professional's. The sibling's outputs are INSTRUMENT MEASUREMENTS,
    never opinions, and it must never be positioned otherwise even to ourselves.

parked:
  - decision: which corpus, and is it cleanly licensed?
    default: US case law, which is public domain, with a bulk public source -- but ⚑ the specific
    source must be VERIFIED, never asserted from memory (the external-grounding gate). Candidates to
    check, not to trust: the Caselaw Access Project, CourtListener/RECAP, EUR-Lex for EU material.
    re_entry: a verified-sources pass before any ingest.
  - decision: how the second instance gets its resources (a)/(b)/(c) above.
    default: (a) for a first cheap probe -- daemon down, one window, small corpus slice -- then (b) as
    the real home once bp-116/bp-118 land, so the sibling becomes the process manager's second consumer.
    re_entry: bp-118's seal, or an owner-granted window.
  - decision: does the sibling get the DREAMER, or only retrieval + the instruments?
    default: instruments first, dreamer second. The instruments have externally-checkable answers; the
    dreamer's output would need adjudication, and adjudicating dream quality on foreign law is a much
    harder problem than measuring citation recall.
    re_entry: after the instrument validation produces numbers.

open_questions:
  - Is the sibling's corpus PRIVATE like the owner's, or public? If public, several of the palace's
    hardest constraints (NN-11, the vault, the sealed core's zero egress) are not being exercised at
    all -- so the control group validates the math but NOT the security architecture. Worth stating
    plainly rather than letting a green sibling imply more than it shows.
  - ⚑ Does the sibling's result transfer back? If the palace can argue over real common law, then it
    could argue over ITS OWN chain -- 210 findings, 48 questions, A1–A9 amendments, supersession
    lineages -- which is the same shape of corpus. That is a follow-on, not the goal, but it is the loop
    the Kafka observation was pointing at.
  - What is the smallest corpus slice that makes the connectivity instruments DISCRIMINATE? oq-0031
    says 13 docs cannot. Nobody knows the threshold; the sibling could find it cheaply by sweeping
    corpus size, which would retire oq-0031 with a number instead of a judgement.
  - Does this need a design note at all, or is it a spike? A spike with a written falsifier list may be
    the honest form -- and `dn-observed-stratum-spike` is the precedent for a spike-typed note.

next_steps:
  - Nothing is graduatable. The cheap, high-information first move is the MULTI-TENANCY AUDIT, which
    needs no corpus and no resources: attempt a second instance by config alone and file every
    hardcoded singleton it trips over. That is valuable whether or not the legal experiment proceeds.
  - Then a verified-sources pass on the corpus, then a spike with the four falsifiers above written
    down BEFORE any output is read -- because fluent prose is exactly what will tempt a post-hoc bar.

references:
  - docs/brainstorms/process-weight.md              # the Kafka observation this grew from
  - docs/inbox/owner-questions.md                   # oq-0031 (instruments can't discriminate at 13 docs)
  - docs/findings/finding-0174.md                   # the 10 GB embedder — the ceiling arithmetic
  - docs/findings/finding-0199.md                   # the ceiling breachable on crash-restart
  - docs/design-notes/supersession-recovery-evaluation.md  # "can the dreamer rediscover known edges?"
  - docs/design-notes/observed-stratum-spike.md     # the precedent for a spike-typed note
  - docs/BUILD-SPEC.md                              # NN-7 (consequential advice) · NN-8 (memory ceiling)
```

## 2026-07-26T14:40:00Z

```capsule
topic: legal-corpus-sibling
date: 2026-07-26

decisions:
  - THE OVERLAY RENAME IS THE FIRST MULTI-TENANCY MOVE, AND THE OWNER SAID SO OUT LOUD. Verbatim:
    "stop using local.toml, it will be ouroboros.toml" ... "and also, this is how we get our test
    mind-palace instance that is specialized in common law to test".
    ⇒ The rename is NOT cosmetic. `local.toml` names a MACHINE; `ouroboros.toml` names an INSTANCE.
    That is the conceptual half of multi-tenancy, and it costs one line (`loader.py:29`). A common-law
    sibling then reads its own overlay under the same convention. Carried by bp-123 (blessed `ready`,
    2026-07-26).
  - ⚑ THE PARKED QUESTION IN bp-123 §11 IS THE ONE THIS ANSWERS -- fixed filename vs instance-DERIVED
    name. bp-123 ships the fixed name deliberately, because deriving it requires deciding WHERE
    instance identity comes from (env var? hostname? CLI flag? a committed instance.toml?), and that is
    a design question, not a build detail. The rename makes the seam VISIBLE; the lookup is the sibling
    plan's job. bp-123 was not re-scoped after blessing.
  - This tightens the note's own next_steps: the MULTI-TENANCY AUDIT ("can a second instance stand up by
    config alone?") now has a concrete first finding waiting for it -- every hardcoded path that assumes
    one instance. bp-123's guard is the first such singleton made explicit rather than implicit.

parked:
  - decision: how a second instance's overlay name is resolved
    default: fixed `ouroboros.toml` (bp-123). A sibling would need a resolution mechanism that does not
      exist yet, and inventing one ahead of the audit is the mechanism-before-measurement mistake.
    re_entry: the multi-tenancy audit runs, OR a common-law sibling is actually stood up -- whichever
      first. At that point this is the audit's first real requirement, not a hypothetical.

open_questions:
  - Does the sibling share the embedder process or run its own? NN-8 (memory ceiling, <=2 resident
    models, ~20-24 GB) makes two embedders a breach, and finding-0174 already measured the embedder at
    10.0 GB under Ollama. Sharing implies the process manager (bp-116/bp-118) is a PREREQUISITE, not an
    optimization -- the sibling becomes its second consumer.
  - Does instance identity belong in a COMMITTED file (so the repo knows what instances exist) or a
    gitignored one (so an instance is purely local state)? The answer decides whether "what instances
    exist" is auditable.

next_steps:
  - Build bp-123 (in flight, 2026-07-26). Its fail-loud guard is the template for how every other
    single-instance assumption should announce itself rather than silently mis-resolve.
  - THEN the multi-tenancy audit, with bp-123's guard as the first entry in its findings list.

references:
  - docs/build-plans/bp-123/plan.md                 # the rename + fail-loud migration guard
  - core/kernel/config/loader.py                    # :29 the one operative line
  - docs/brainstorms/process-weight.md              # the Kafka observation this all grew from
  - docs/findings/finding-0174.md                   # embedder = 10.0 GB; the two-instance ceiling
```
