---
type: design-note
id: dn-dreaming-on-curated-graphs
status: draft
implementation: not-built   # corpus-audit 2026-07 verification
created: 2026-06-26
updated: 2026-07-01
links: []
supersedes: null
superseded_by: null
warrant: null
---

# Design note — Dream R5: curated-graph dreaming + cross-graph resonance

*Family tag → family 5 (the reasoning complex) over a family 1 label: dreaming on the curated graph (curated ∉ MIRROR_READABLE — the firewall holds) + cross-graph resonance. R&D, flag OFF. See [`../NOTATION.md`](../NOTATION.md).*

**Status:** dream R&D extension **R5**, **feature-flag OFF**. Extends
`dream-phase-rnd-charter.md` and reuses R0 (interpreter panel) + R1 (adjudicator). Build only
after R0/R1 are solid and in a deliberate R&D session. Does not change the main build.

## The idea
Apply the dream interpreter panel to a **curated** corpus — a book, or a body of literature the
owner reads and values — to surface its themes, philosophy, and human-condition threads; then
compute how those relate to the owner's **authored** core. "Books I read and like reflect my
views" — true, but they reflect them as *curated* signal (the owner's **selection** of others'
words), **not** as the owner's authored voice. The design must preserve that distinction.

## Firewall — the load-bearing rule
A book is `curated`, and `curated ∉ MIRROR_READABLE`. Therefore:
- The book lives in its **own graph / store**, **never merged into the authored mirror.**
- The introspective mirror dreamer never reads it. The curated corpus gets its **own dreamer
  instance over a curated view** (a `CuratedView`, analogous to `MirrorView` but over the
  curated provenance set).
- The same in-graph safety rules apply: grounding terminates in the curated corpus's own nodes;
  confidence decays with depth; outputs are `interpreted`.

## The interesting operation — cross-graph resonance
After running the panel on each graph independently:
1. Curated panel → **curated theme-clusters** (centroids $\bar{c}^{\,\text{cur}}_j$, each with the
   book's own supporting passages).
2. Mirror panel → **authored theme-clusters** (centroids $\bar{c}^{\,\text{auth}}_i$).
3. **Resonance** = cross-graph similarity in the shared embedding space:
   $$\mathrm{res}(i,j)=\cos\!\big(\bar{c}^{\,\text{auth}}_i,\ \bar{c}^{\,\text{cur}}_j\big),$$
   surfaced as the top resonant pairs — *where the owner's reading and writing rhyme*.

**Resonance output is `interpreted`-only and read-only across graphs.** It does **not** merge the
book into the authored mirror; the mirror's content is unchanged; a highlighted passage never
becomes something the owner "wrote." Resonance is a *lens on the relationship*, not a claim that
the book explains the owner (mirror-not-oracle).

## Why it's worth it
It lets the assistant grapple with a book — extract meaning, philosophy, the human condition —
and show how it relates to the owner's core **without conflating the two voices.** The firewall
is what makes this safe to do rather than a contamination.

## Build (R5, flag OFF)
- Add a `CuratedView` (the curated analog of `MirrorView`); a curated `DerivedStore` namespace
  for curated dreams (still `interpreted` provenance).
- Reuse the R0 panel + R1 adjudicator over the curated view.
- Add the `resonance(authored_clusters, curated_clusters)` operation (pure cosine over centroids),
  output `interpreted`, surfaced to the owner, never written to the mirror.
- Tests: curated dream never reads authored nodes and vice versa; resonance never mutates the
  authored mirror; curated dreams are `interpreted`-only.

## Open questions
- Resonance threshold / how many pairs to surface.
- Per-book vs whole-curated-corpus graphs (likely per-source, then resonance across the union).
- Whether curated dreams are ever shown alongside authored dreams (yes, but clearly labeled by
  provenance — never blended).
