---
type: finding
id: finding-0163
status: routed           # open → routed → resolved | promoted
created: 2026-07-22
updated: 2026-07-22
links:
  - docs/design-notes/code-ingest-pipeline.md          # PD-B (§637), §548 HEAD-only, §430-460 D-fiber/supersession
  - docs/findings/finding-0151.md                      # the integrator — this is its FOUNDATION, not a sibling
  - docs/findings/finding-0146.md                      # code is a first-class semantic source
  - core/kernel/temporal/acquire.py                           # supersession_poset — the machinery, ready but unwired to code
  - core/kernel/temporal/boundary.py                          # poset_from_chains — accepts per-path blob chains
ftype: direction         # reopens a ratified design decision (PD-B) — owner-ruled
origin_plan: orchestrator
route: orchestrator      # feeds the Fable integrator design pass (finding-0151)
resolution: null
---

# PD-B reversed: the code corpus must embed HISTORY — supersession edges (and the whole causal graph) require it

## Owner ruling (2026-07-22)

The embed lane must **embed the full code history**, not HEAD-only. dn-code-ingest-pipeline PD-B /
§548 ("HEAD-only, no historical backfill; history is carried structurally by D; embedding every
historical blob multiplies cost for no named consumer") is **reversed**. Two grounds, both decisive:

1. **The cost premise is false on the data.** The snapshot ledger has **1,542 distinct
   `(path, blob_sha)` code versions** across **977 commits** (403,482 file-rows are almost all
   unchanged repeats). That is ~6× the ~257 HEAD files the current seed already embeds — trivial,
   not a "multiply cost." (Even a generous 10× undercount is thousands, not millions; the
   observation plane alone is 3.76M rows.)
2. **You cannot add the causal edges if the history isn't represented (the real reason).** The whole
   product is *a graph that evolves over time*. The integrator's causal path is
   `conversation → commit → code-change`, and the **code-change terminus IS a supersession edge**
   `blob(v) → blob(v+1)`. A supersession edge needs both endpoints to be **nodes in the graph**.
   HEAD-only leaves every "before" version as a bare blob-sha in the ledger — structurally present,
   semantically absent — so there is nothing for the integrator's edges to land on. HEAD-only does
   not weaken the integrator; it makes it **impossible**. This is exactly the "named temporal-semantic
   consumer" PD-B's own re-entry condition asked for — and it's the core purpose, not an edge case.

Corollary (was defended wrongly by the orchestrator, now corrected): the "embed lane = current-view
retrieval instrument, D-chain stays structural" framing under-served the system. The snapshot is not
the graph.

## The corrected design (one coherent program = the integrator, finding-0151)

1. **Backfill-embed the ~1,542 historical `(path, blob_sha)` versions** — each becomes a semantic
   node. Reuses the existing seed path per version; keyed by blob_sha (already the `digest`).
2. **Flip the incremental sync from delete+replace → keep-and-link.** Today `code_sync` /
   `CodeCorpusSync.sync()` is digest-keyed **delete + re-add** — on a blob change it *deletes* the
   old version's vectors (`core/ingest/code_corpus.py`), destroying the supersession endpoints as
   code evolves. It must instead **retain every version** and add the edge. This is the load-bearing
   store-model change.
3. **Mint the supersession D-edges** `blob(v) → blob(v+1)` as real graph edges over the embedded
   versions. The temporal machinery is already built and described in the note as "ready, a reader
   wiring, no new machinery": `supersession_poset` (`core/kernel/temporal/acquire.py`), `poset_from_chains`
   (`core/kernel/temporal/boundary.py`) — waiting for exactly this consumer.
4. **The integrator composes** `C-fiber (conversation→commit) ∘ D-edge (commit→code-change)`
   (finding-0151's ComposedGraph) so the causal chain is a traversable path.

## Why it matters

This is the difference between "search current code semantically" and "the evolving self-map we are
actually building." Without it, the integrator (finding-0151) has no code-change nodes to terminate
on, the C-fiber stays thin (finding-0141), and "which conversation caused which code change over
time" — the founding use case — is unanswerable.

## Open questions for the design pass (Fable, folds into finding-0151)

- **Store growth model.** Keep-every-version is unbounded over time (by design). Size it; a pruning
  or cold-tier policy may be wanted eventually (not now — 1,542 is tiny).
- **Does this generalize to the NOTE corpus?** If the temporal-evolving-graph is the model, do notes
  also need version retention + supersession edges (today they may also delete+replace)? Or is
  code-first correct? Decide the scope.
- **Edge representation.** Supersession as a vector-store relation vs a separate graph store; how it
  composes with the C-fiber and the existing `sourceset` group-by-digest relation.
- **Interpreter/embedder version as the SECOND D-axis** (note §2.5b) — historical re-embedding must
  not conflate content-supersession with worldview-supersession.

## Re-entry / next step

This is now the **foundation of the finding-0151 integrator design pass** (Fable, unblocked — the
build tracks have landed). That pass should absorb this: capture → design note (superseding
dn-code-ingest-pipeline PD-B / §548) → owner ratify → graduate → build. The current HEAD seed is NOT
wasted — HEAD is one of the 1,542 versions; backfill is additive. Nothing blocks; but item 2
(delete+replace) means every new code commit is currently discarding a supersession endpoint, so the
sync-model fix wants to land before heavy code churn accumulates.

## Routing

`direction`, owner-ruled → **orchestrator → the Fable integrator design pass**. A design-note
supersession of PD-B/§548 warrant-linked here; then graduate the backfill + keep-and-link + D-edge
+ composition as the integrator program's build plans.
