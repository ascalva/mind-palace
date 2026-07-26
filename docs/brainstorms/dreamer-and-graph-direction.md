# Brainstorm — does the graph's temporal *direction* change the dreamer's role?

A design seed (owner, 2026-07-13), flagged for the **Jul-17 `dn-core-query-protocol` fable-vet** and
the **`edge-dynamics` Lane B** math successor. Rides on the math review — captured so it doesn't die
in a transcript (§ no decision lives only in a transcript).

## 2026-07-13 — capsule: the question + its grounding

**The owner's question.** "Does our re-interpretation of what a dream can be, or the fact that the
graph and edges change over time (edge fluctuations), which gives the graph a *direction* — does that
change the role of the dreamer? Riding on what fable says when the math is fully reviewed."

**Grounding — the dream data model as it stands (verified this session).**
- A dream is an `interpreted_artifacts` row in `data/derived.sqlite`: `kind=dream`,
  `provenance='interpreted'` (hardcoded), a markdown `summary` (framing → **Pattern** → **Tension**
  → **Open questions** → a deferring close), `subjects` (note titles), `data` (`grounded:true`,
  `check:[grounded-citations:pass, mirror-not-oracle:deferred, …]`, `cluster_size`), `derived_from`
  (source hashes), `attestation_id`. Every claim cites a `[[note]]`.
- Each dream ALSO writes a **`derives` hyperedge** (`provenance='interpreted'`): `head`=the dream,
  `tails`=the source notes — the attested lineage edge (G2 `derived_from` as a graph relation).
- **Both the artifact and the edge live as `interpreted` immediately** — the write is *ungated* but
  lands in a lane structurally firewalled from the mirror (`INTERPRETED ∉ MIRROR_READABLE`).
- **What's gated is disposition + promotion, not the write.** `verdict_dispositions.sqlite` records an
  owner **verdict** setting a disposition (`effect ∈ {endorse|retract|record}`) on an interpreted
  subject; crossing to *authored* goes through `promote(Derived[T], OwnerVerdict) → Authored[T]`
  (`core/provenance.py`, a deliberate `NotImplementedError` stub until the verdict taxonomy ratifies).
  "Content-addressed proposals that can never silently become beliefs."

**Terminology pinned (the owner asked; corrected against the design record).**
- **Fibers** = the geometric/grounding edges `E_geom` (cosine + citation), laid *deterministically by
  ingest* — the substrate retrieval + dreaming run over. (`the-edge-model.md` §2.)
- **Dispositional edges** = `E_disp`: edges carrying a verdict/disposition (endorse/retract/record/
  supersede); **time-directional**; excluded from the operator + the typed edge budget (which governs
  `E_geom` only). Total edge set = `E_geom ⊔ E_disp`.
- **Supersession ⊂ dispositional** — supersession is *one type* of dispositional edge (the `C→C′`
  "this replaces that"). "Dispositional" is the accurate umbrella; they are NOT synonyms.
- **Nodes** — the dreamer creates dream *artifacts* (technically new interpreted nodes — the `head` of
  each `derives` edge) + lineage edges to *existing* notes. It fabricates no new knowledge/corpus nodes.

**The direction already exists as a (parked) design object.**
- `edge-dynamics.md` — the 1-form lift, the Helmholtz/Hodge decomposition, the L₁ Fourier basis, the
  THREAD lens, the Lane A/B seam. This IS the graph-with-a-direction.
- `core-query-protocol.md` §2 splits edges into geometric `G` (lateral) and **dispositional `D`
  (supersession; time-directional)** over the cochain complex `C⁰ —d₀→ C¹ —d₁→ C²`; §2.5 defines a
  **Mode 3 — temporal** retrieval ("the transport between static snapshots") and states the temporal
  complex is well-founded (supersession acyclic; the THREAD lens's objects have a temporal life) — but
  marks the **formalization Parked** for the fable session. That parked formalization is the "when fable
  reviews the math" the owner names.

## The claim — a role expansion, not a cosmetic tweak

Today's split: **temporal is a query mode** (Mode 3, the Librarian) and the **dreamer is a synchronic
pattern-reader** over the geometric fibers (themes/findings/structural features of the graph *as it is
now*). The seed asks: **move the temporal structure from a query-mode into a dreaming-subject.** If so,
the dreamer's role expands from

- *"what patterns are present?"* (synchronic, over `G`) → also
- *"where is the graph **moving** — which threads consolidate vs. dissolve, what's being superseded,
  what's the drift direction?"* (diachronic, over `D` across snapshots).

The dreamer would interpret the graph's **velocity**, not only its **state** — the natural deepening of
the Track-H frontier ("summarizing structure → reasoning over it" becomes "reasoning over its
*evolution*"). Open sub-question: is that a **second dreamer mode**, or a **distinct diachronic
interpreter** alongside the synchronic one?

**The recursion worth noting.** The dreamer already surfaced, from the owner's OWN notes, the tension
"should the founding corpus be a fixed anchor, or is its degradation/transformation the actual
phenomenon to track?" The owner now asks whether the dreamer should *become the instrument that tracks
that transformation.* The design question and the owner's private intuition are the same question.

## What it rides on (fable-gated — do NOT resolve here)

1. **Hodge/Helmholtz well-definedness** on this edge set — is "direction" a genuine gradient/curl-free
   object, or a metaphor over noise?
2. **Temporal-complex well-foundedness** beyond the stated supersession-acyclicity (§2.5 formalization
   Parked).
3. **Signal vs. noise, one level up** — a fiber that strengthens because a related note was added is
   *evolution*; one that shifts because the embedder was re-run is *noise*. The math must separate them,
   or a diachronic dreamer interprets drift that isn't there (the apophenia guard, lifted to the
   dynamics).

Until Lane B is ruled on, "the graph has a direction the dreamer can read" is a **promising structure,
not a validated capability** — the same posture as the dreams themselves today.

## Routing

- **Explicit question for the Jul-17 fable-vet:** does the temporal/Hodge structure support the dreamer
  reading the graph's direction, and if so — second dreamer mode, or a distinct diachronic interpreter?
- Home of the formalized answer: the `edge-dynamics` **Lane B** math successor (core-query-protocol
  §2.5's parked temporal algebra). Re-entry: the first plan that needs the temporal operator built.
- Not a build. A design seed for the frontier.

## 2026-07-26T16:30:00Z — what a dreamer IS (owner refinement)

```capsule
topic: dreamer-and-graph-direction
date: 2026-07-26

decisions:
  - THE OWNER'S DEFINITION (2026-07-26, verbatim): "the dreamers are the tool through which the system
    is better able to understand itself, it analysis the appropriate strata subset/set/layers such that
    it can form an opinion/belief from what exists".
    ⇒ Three load-bearing words, and each already has machinery behind it:
      · "APPROPRIATE STRATA SUBSET" is **Σ** — the scope grammar's first coordinate (which material),
        alongside E (which relations), T (as of when), A (with what power). So "choosing the right
        subset" is not a heuristic the dreamer improvises; it is a GRANT, already typed.
      · "OPINION/BELIEF" — deliberately not *knowledge*. A belief is defeasible, revisable, and can be
        wrong without the system being broken. That is the correct epistemic status for a dream output
        and it is why an adjudicator exists rather than an oracle.
      · "FROM WHAT EXISTS" — the constraint that separates a belief from a confabulation.
  - ⚑ "FROM WHAT EXISTS" IS EXACTLY WHAT §2.7's CONDITIONING LAW ENFORCES, and the owner's phrasing and
    the ratified law turn out to be the same sentence. The law exists to stop **hypothesis laundering
    through dream exhaust** (`dn-synchronic-diachronic-dreamer` §2.7, which EXTENDS
    `dn-recursive-dreaming-bounded-by-grounding`'s four safety rules with a fifth). A belief conditioned
    on prior dream output is a belief formed from what does *not* exist. So the difference between an
    opinion and a confabulation is not the reasoning quality — it is whether the substrate was real.
    That is a structural property, checkable, and already law.
  - ⚑ CONSEQUENCE FOR THE CALIBRATION LEDGER (see `prediction-market-sensor-fusion.md`): if a dreamer
    forms a *belief*, then scoring it is BELIEF REVISION, not grading. The ledger should record the
    belief, the strata it was formed over (its Σ), and what a later cut revealed — because a belief that
    was wrong *given its Σ* is a different failure from one that was wrong because its Σ was too narrow.
    ⚑ Those two are the interesting signal and a single scalar score destroys the distinction. "The more
    you know, the better the view gets" is precisely the claim that widening Σ improves the belief — so
    the ledger MUST carry Σ, or it cannot test the project's own thesis.
  - And the ledger must stay READ-ONLY with respect to dreamer inputs, or it becomes a laundering
    channel itself — the fifth safety rule applied to the instrument that grades it.

open_questions:
  - Does the existing adjudicator (`core/dreaming/adjudicator.py`) already record enough to reconstruct
    a belief's Σ after the fact? If yes, the ledger is a read over existing state rather than new
    bookkeeping. ⚑ Check before designing storage.
  - Is there a difference between "understand itself" and "understand its corpus"? The corpus is the
    owner's self-map, so a dreamer forming beliefs about it is forming beliefs about HIM — which is the
    same seam `acting-as-the-owner.md` raises, one layer down and without any world-facing risk.

next_steps:
  - No build. This refines the ledger's SHAPE (carry Σ, record revision, stay read-only) before anything
    is written, which is the cheap moment to get it right.

references:
  - docs/design-notes/synchronic-diachronic-dreamer.md   # §2.7 the conditioning law — "from what exists", as law
  - docs/design-notes/recursive-dreaming-bounded-by-grounding.md  # the four safety rules the fifth extends
  - core/dreaming/adjudicator.py                         # does it already record Σ?
  - docs/brainstorms/prediction-market-sensor-fusion.md  # the ledger this reshapes
  - docs/brainstorms/acting-as-the-owner.md              # beliefs about the corpus are beliefs about him
```

### 2026-07-26T16:40:00Z — the VOICE of a belief (owner illustration)

```capsule
topic: dreamer-and-graph-direction
date: 2026-07-26

decisions:
  - THE OWNER ILLUSTRATED THE OUTPUT SHAPE, verbatim: *"I think this will happen, I think I see this
    pattern in the data that is becoming relevant in problem solving, ... etc"*.
    ⇒ Not a throwaway — it is a specification of REGISTER, and register is a design decision here rather
    than a styling one. Four properties are visible in that one sentence:
      · FIRST PERSON AND HEDGED -- "I think", twice. The output asserts a belief and marks it as one.
        An unhedged dream output would misrepresent its own epistemic status (see the prior capsule:
        opinion, not knowledge).
      · FORWARD-LOOKING -- "this will happen". A claim with a future truth value, i.e. SCORABLE. The
        register and the calibration ledger are the same requirement seen from two sides.
      · EVIDENCE-INDEXED -- "I see this pattern in the data". The belief points at its substrate, which
        is what makes "from what exists" auditable rather than merely asserted.
      · ⚑ RELEVANCE-INDEXED TO A CURRENT PROBLEM -- "becoming relevant in problem solving". This is the
        most easily-missed clause and possibly the most important: the belief is not free-floating, it is
        surfaced BECAUSE it bears on something live. A dreamer that emits true-but-inert beliefs fails
        `process-weight.md`'s test (NAME THE READER) even when every belief is correct.
  - ⚑ CONSEQUENCE: "becoming relevant" implies a COUPLING between belief formation and whatever the
    system currently has in hand. That is a retrieval/salience relation, and it is a different object
    from the belief itself. Worth naming before it gets built implicitly: a belief has a Σ (what it was
    formed over) AND an occasion (what made it worth saying now). The ledger records the first; the
    second decides whether it is ever surfaced at all.

open_questions:
  - Is "becoming relevant" a property the system can compute, or does it require knowing the owner's
    current problem? If the latter, it needs an input the dreamer does not have today — and that input
    is suspiciously close to the ambassador thread's inbound channel
    (`ambassador-thread-and-the-afk-loop.md`). Two ideas from the same day may share a dependency.
  - Does an unhedged rendering already exist anywhere in the dream surface? If dream output is currently
    presented as fact rather than belief, that is a register defect with epistemic consequences, and it
    is checkable today against `core/dreaming/` and the exhaust renderers.

references:
  - docs/brainstorms/process-weight.md                  # NAME THE READER — the test an inert belief fails
  - docs/brainstorms/prediction-market-sensor-fusion.md # the ledger; register and scorability are one requirement
  - docs/brainstorms/ambassador-thread-and-the-afk-loop.md  # the possible source of "current problem"
```
