# shared-vectors

## 2026-10-29

```capsule
topic: shared-vectors (content-addressed chunk vectors, supersession by reference set)
date: 2026-10-29

owner (verbatim): |
  "vector data needs to be stored efficiently, since ingesting/embedded tokens will be common,
  common words and phrases will occur, so it will actually be better and there SHOULD be a design
  doc somewhere outlining this direction: so if doc A and B both are composed of 10 vectors, and 5
  are the same, then A and B have pointers to those vectors in common, but if one of those changes
  in A, then a supersession edge from the doc is created to the updated doc with the new vector
  reference set, i believe that's loosely what the idea was"

state today (checked in code, 2026-10-29):
  - Rows carry their own vectors (LanceDB, one row per chunk). The curated importer skips a
    document whose text digest is stored, but its row ids include the source path, so the same
    passage in two documents is embedded and stored twice.
  - The code lanes already work the owner's way: content-addressed atoms plus membership edges
    (bp-153's D7 atom+membership rebuild; 17,508 memberships). Generalize that, don't invent anew.
  - FOUND, the note the owner remembers: docs/design-notes/vector-membership-store.md
    (dn-vector-membership-store, draft): one vector row per idea-atom, all occupancy in a
    membership relation (built for code: 4b5422a/48ba77d, bp-152; gauges n_doc, n_occ, |M|/|V|,
    embeds-avoided: 7211c1d; §4 "the frequency plane": n(v) counts and the corpus histogram as
    standing gauges). Its line 173 pins the opposite of the owner's newer ask below: "an atom
    never spans strata" (the PD-2 fence, carried as a test invariant).

direction (to design, then build):
  - A vector table keyed by (chunk content hash, embedder id): each unique chunk is embedded and
    stored once. A document version is an ordered reference set of chunk hashes (memberships).
  - An edit makes a new version that reuses every unchanged chunk's vector and adds a supersession
    edge old → new carrying the new reference set; nothing is deleted (archive, never delete).
  - Gains: a slightly edited note re-embeds only its changed chunks; versions and quoted or
    boilerplate passages cost nothing extra; a model change re-embeds unique chunks only.
  - Precision on "common words and phrases": vectors here are per chunk (a passage), not per
    token, so sharing pays for repeated passages and versions, not for common words. Per-token
    vectors would mean multi-vector (late-interaction) retrieval, where the state of the art
    compresses repeated token vectors with centroid codebooks (ColBERTv2 / PLAID residuals).
  - First step: measure the duplicate-chunk rate per store (vault, dialogue, curated, code).

owner (verbatim, later the same day): |
  "papers, dialogues, monologues can also reference the same vectors, that's how we connect the
  full stratum as well, common language use exists, and that's how we would also be able to run
  the statistical tests, like number of times a given token is used, a histogram, where a
  language-like histogram plot should appear, i think it's an exponential decay? where the most
  common words are sorted and the graph slowly dies out towards less common words/tokens?"
  - Conflict to resolve with the owner: cross-stratum atoms reverse dn-vector-membership-store's
    PD-2 fence (an atom never spans strata). A way to have both: the vector is shared, while
    provenance and access live on each membership, so curated rows stay unreadable from the
    mirror (the rule is enforced per membership, not per vector). Re-check the prefilter and
    sourceset arguments the fence protects before amending the note (owner-only ratification).
  - Math, corrected: word (and token) frequency by rank follows Zipf's law, a power law
    f(r) ∝ 1/r^s with s ≈ 1 (Zipf–Mandelbrot: 1/(r+b)^s), not an exponential decay. On log-log
    axes it is close to a straight line of slope ≈ -1, and its tail dies out far more slowly than
    an exponential would. Vocabulary growth follows Heaps' law, V(n) ∝ n^β with β ≈ 0.4–0.6. Fit
    the exponent by maximum likelihood with a goodness-of-fit test (Clauset, Shalizi & Newman,
    2009), not by least squares on the log-log plot.
  - Where it lives: sharing chunk vectors connects identical passages only. "Common language" is
    a token layer: a vocabulary with per-stratum counts (an inverted index). That layer gives the
    histogram and Zipf and Heaps statistics, lexical search beside dense search (hybrid
    retrieval), and cross-strata links through shared rare terms (IDF weighting; the Zipf head
    is mostly stopwords that carry little signal).
```
