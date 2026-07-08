---
type: design-note
id: dn-founding-corpus
status: draft
implementation: built-wired   # corpus-audit 2026-07 verification
created: 2026-07-04
updated: 2026-07-04
links: []
supersedes: null
superseded_by: null
warrant: null
---

# Founding Corpus Construction

**Status:** DRAFT — pending codebase reconciliation and owner ratification
**Origin:** Design dialogue, July 2026
**Boundary:** Inbound channel — ingestion (origin case). Governed by the sacred-
boundary principle (`the-sacred-boundary.md`): what goes to the core is sacred,
and the founding write is the first and most consequential ingestion.
**Reconciles with:** `live-adoption-and-longitudinal-harness.md` (control corpus),
`ingest-identity-and-amendment.md` and `dialogue-ingest-and-recursion.md` (the
ingest path this must share), `recursive-strata.md`.

---

## 1. "Train" is the wrong verb — kill it

The verb collapses two categorically different operations:

- **Ingest** — dialogues enter as authored strata; changes the **graph**; fully
  governed by every existing invariant (provenance layer, supersession, typed
  strata, verdict gate).
- **ML fine-tuning** — gradient / weight updates; changes the **reasoner
  itself**; **categorically outside** the safety story, because every guarantee
  is a property of the architecture wrapped around a *fixed* model. Fine-tuning
  the Dreamer on the dialogues is the ultimate provenance laundering: the musings
  become base-model priors — permanent, with no supersession edge and no depth
  field, because they are no longer *in the graph* but *in the substrate*, which
  the provenance layer cannot track.

**Decision:** the founding corpus is **corpus curation / founding-condition
authoring**, not model training. The weights never move. If fine-tuning was ever
the intent, that is a different project with a different threat model and none of
these invariants defend it — flag, do not proceed under this document.

## 2. A founding corpus is not steady-state ingest

It is a hand-selected batch, authored across a long past, injected **at once** as
the graph's initial condition. Three problems follow, each a provenance question
in disguise.

### 2.1 The timestamp lie
Stamping the whole batch "today" collapses months or years of thought —
including musings that *supersede each other* — into simultaneous peers, baking
the contradiction-density artifact (from `ingest-identity-and-amendment.md` and
`dialogue-ingest-and-recursion.md`) into the initial condition. Curation is
therefore a **sequencing-and-supersession task**: reconstruct the partial order
of the owner's own thought (what came first, what revised what, what still
stands). The corpus must be a **dated, supersession-linked sequence**, not a bag,
even though it is ingested in one sitting.

### 2.2 Invisible selection bias
The boundary "my musings, not the code-build discussions" cuts **correctly** —
build-session dialogues are about *how to construct the system*, and admitting
them to the object-level graph is a category error (the system studying its own
scaffolding as knowledge). Keep the boundary. But acknowledge the second-order
effect: a graph founded on resolved, coherent, already-reconciled musings has
founding density, initial cluster structure, and first frustrations that are
artifacts of *what was included*, not of external ground truth. A legitimate
design choice, made explicit rather than left invisible.

### 2.3 The founding corpus cannot be the control corpus
Track L needs a frozen control to measure drift against. A hand-curated founding
set is the **most** biased possible yardstick — a deliberately coherent worldview
— so measuring evolution against it makes "drift" and "the graph developing views
the owner happens to hold" inseparable, confounding every longitudinal curve. The
control must be something **not** curated for coherence. The curation act and the
control-corpus act must be kept **mechanically distinct**.

## 3. What it actually is

Authoring the initial condition: hand-placing the first stratum, in reconstructed
chronological-and-supersession order, from a deliberately bounded slice of
thought, with full knowledge that the founding selection biases everything
downstream and therefore cannot double as the yardstick. Fully inside the safety
model **as long as it is ingest and not fine-tuning**.

## 4. Open question (requires reading the code)

- **Q3.** What is the **unit** of the curated corpus — a whole dialogue as one
  authored artifact, or a dialogue decomposed into claims-with-warrants at
  ingest? Cite whether steady-state ingest is operation-emitting or
  document-emitting today. Founding and steady-state ingest **must** share a path
  or the provenance model fractures at the origin; identify any place a separate
  founding path would cause that fracture.

## 5. Reconciliation

Interacts with the control-corpus requirement in
`live-adoption-and-longitudinal-harness.md`, the "train verb collapse" learning,
and `recursive-strata.md`. Builder to propose cross-references or partially-
superseded banners per repository discipline.
