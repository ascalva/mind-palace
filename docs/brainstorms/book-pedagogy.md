# Book pedagogy — the design manual as coherent story + soundness audit

## 2026-07-19T17:41:24Z

Origin: owner ↔ orchestrator chat during the bp-071 seal (session-31), reflecting on what the
`docs/book/` design manual and the scribe role must become. Captured into the artifact chain (not
left in Claude Code's harness memory) because it is project-native design guidance for the `book`
skill / a future book-pedagogy design note. Mirrored in Claude's feedback memory
`book-narrative-philosophy` (harness-side, shapes behavior); THIS is the palace-side record.

```capsule
decisions:
  - The book is COHERENT KNOWLEDGE TRANSFER THROUGH STORY, not a knowledge dump. Every concept earns
    its place by narrative arc:  motivation (why does this exist?) → prerequisites (what theory had
    to be in place first) → the idea → what it unlocks → why it matters to the whole. Strong
    intuition and visuals (TikZ) lead; the formalism follows the intuition, never precedes it. A
    reader should finish a chapter able to RE-DERIVE the motivation, not just recite the definition.
  - The scribe SYNTHESIZES a spine from the existing artifact chain, never invents: ratified design
    notes = theory; findings = the falsifiers / the "why"; docs/reference_material = math provenance;
    seal read-maps = concept-bearing intuition. Read-maps are the micro-version; the book scales it.
  - Generalization is RETROACTIVE on the narrative (structural debt ≠ factual debt). When a concept
    is re-grounded/generalized (e.g. dn-agent-taxonomy lifting sensor/query/integrator/dreamer into
    role-as-scope-signature), it changes the FRAMING and ORDERING of every earlier chapter that
    introduced a now-special-case — not just stale facts. Book debt therefore has two tiers:
    FACTUAL (a signature/number went stale → patch in place) and STRUCTURAL (an arc's framing is
    invalidated → recast). `/scribe` debt computation must flag structural debt on any
    generalization/supersession event, not only stale citations.
  - Do NOT foreshadow an unratified generalization backward — that leaks an idea backward through the
    gate. Each chapter is written as what was RATIFIED then; when the concept generalizes, the NEW
    chapter does the explicit lifting and earlier chapters get a FORWARD-POINTER, not a silent
    rewrite (mirroring how findings re-enter design through the same gate). The generalization moment
    is the best STORY beat — teach the abstraction by RELIVING its birth from the specific cases.
  - The scribe is also an AUDITOR (soundness-as-audit). Writing a well-founded argument for a
    construct is a PROOF OBLIGATION, so exposition under a soundness bar audits intuition ↔ construct.
    A chapter is a falsifiable claim that the two cohere; a chapter that cannot be written soundly is
    EVIDENCE of a defect (unmotivated construct, or intuition drifted from implementation). This is
    the third — and only systematic, written-down — drift check: tests audit code↔spec; the owner's
    conceptual questions audit his-model↔system; the scribe audits intuition↔construct.
  - Bounded authority (the scribe contract): it DETECTS incoherence and FILES A FINDING (routed
    through the same gate); it NEVER fixes the design and NEVER papers over a gap with elegant prose.
    A beautiful narrative that lies is the cardinal failure.
  - Anti-rationalization: a scribe optimizing for a compelling story will, unchecked, INVENT
    intuition — manufacture a clean "why" for a construct that exists for messy/historical reasons.
    "Well-founded" means every premise TRACES TO A RATIFIED ARTIFACT; the tell of a smuggled
    narrative axiom is a premise with nothing behind it in the chain. (Matches the owner's falsifier
    epistemics.)
  - Soundness is a proxy for whether an abstraction is EARNED: if the integrator can be narrated
    soundly as the SECOND instance of role-as-scope-signature (both instances tracing to landed
    code), the generalization is real; if it can only be narrated as "a thing we added," the
    abstraction is premature and its chapter should not exist yet. The book audits conceptual
    necessity, not just factual accuracy.
parked:
  - Formalize the two-tier book-debt model (factual vs structural) in the `book` skill's sync
    semantics. | re-entry: when book work resumes (post-Δ), decide whether this graduates into a
    book-pedagogy design note or is folded into the book skill directly.
open_questions:
  - Does structural debt want a machine-detectable signal (e.g. a design-note supersession/ratify
    event auto-marks downstream chapters), or is it a scribe-judgment call each sync?
  - How are forward-pointers represented in the LaTeX so an earlier chapter honestly flags "later
    generalized" without rewriting its own epistemic moment?
next_steps:
  - Hold the agent-taxonomy chapter until the taxonomy has generalized as far as it will for now
    (sensor + integrator landed; query + dreamer still ahead) — write the "birth of the abstraction"
    chapter ONCE, whole, after the arc completes.
  - Run `/scribe` after Δ (bp-073) lands to compute book debt against the sensor→integrator→
    re-measure arc as one coherent part.
references:
  - docs/design-notes/agent-taxonomy.md    # dn-agent-taxonomy — role-as-scope-signature (the generalization in question)
  - docs/findings/finding-0111.md          # the C-fiber re-ground — a worked example of "why" as narrative
  - .claude memory: book-narrative-philosophy  # harness-side mirror of this guidance
```

## 2026-07-20T21:28Z (session-39, fable — owner: rigor is part of the pedagogy)

Owner, near-verbatim: *"the textbook should also be rigorous when it needs to be; the book is also
about getting someone up to speed with the math and the code, although we should not shy away from
the math/equations; you can use pseudo code instead of real python code when needing to show a code
snippet."* Complements — does not soften — the 2026-07-19 narrative-first capsule: intuition still
leads, but where a construct warrants formal treatment, the formalism is given in full.

```capsule
topic: book-pedagogy
date: 2026-07-20

decisions:
  - RIGOR WHEN IT NEEDS TO BE: the narrative-first rule caps neither depth nor formality. The
    book's job includes bringing a reader genuinely up to speed on the math AND the code — full
    equations/derivations where the construct warrants them; never shy away from the math.
  - Snippets are PSEUDO-CODE, not verbatim Python: teach the algorithm's shape, not the repo's
    surface. (Orchestrator note: this also shrinks the FACTUAL tier of book debt — pseudo-code
    doesn't go stale with signature churn; only structural debt remains for those passages.)

next_steps:
  - Fold both rules into the book skill's voice/snippet conventions at the next /scribe touch.
  - Harness-side memory mirror (book-narrative-philosophy) updated this session.

references:
  - .claude memory: book-narrative-philosophy   # mirror updated 2026-07-20
```
