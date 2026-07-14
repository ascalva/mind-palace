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
