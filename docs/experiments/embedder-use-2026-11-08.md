---
type: experiment-report
experiment: embedder-use
run: 1
status: pre-declared              # the protocol below was committed before any comparison ran
started: 2026-11-08
links:
  - docs/experiments/embedder-use-2026-11-08.json          # the numbers, as data (written with the results)
  - eval/embedder_use/                                      # the harness
  - docs/design-notes/dn-embedder-use.md                    # the findings and recommendations (with the results)
  - docs/experiments/two-phase-ingestion-2026-11-07.md      # the lexical, semantic and fused figures on SciFact this study starts from
  - docs/experiments/corpus-stage1-2026-11-07.md            # the corpus battery, its bridges and their null
  - docs/experiments/embedder-input-lengths-2026-11-08.md   # the chunks' lengths in the embedder's tokens
---

# How the store uses its embedder, and whether its tokens are consistent (2026-11-08)

**Question.** The embedder is the store's one learned, domain-free prior: it turns any text into
semantic structure without code written for one source. Six choices decide how much of it the store
uses: how the lexical index tokenizes (it does not normalize Unicode), how long a chunk is, whether
a chunk is embedded with its document's context, which task prompt a query carries, how many of
the vector's dimensions are kept, and how a semantic edge is thresholded. Each is measured here
against the live default, across the domains available, with every threshold set from the data.

This section was committed before any comparison ran. Results are added below it, and any change
to the protocol after that point is listed under "Deviations".

## Pre-declared protocol

### What every comparison shares

- **Retrieval.** Items are chunked; every chunk is embedded with the document template; a query
  is embedded with the query template; a document's score is its best chunk's cosine, and
  documents are ranked by it (the plane's own reading, at the document grain). Exact cosine over
  float32 vectors as the server returns them, unless an arm says otherwise.
- **The live defaults (the reference arm).** Chunks of at most 1,200 characters with 150 of
  overlap (`core/kernel/ingest/chunk.py`); document template `title: none | text: {text}`; query
  template `task: search result | query: {text}`; 768 dimensions; EmbeddingGemma-2 Q8_0 served by
  llama-server on 127.0.0.1:8081.
- **Metrics.** recall@10 (the share of a query's relevant documents in its first ten) and nDCG@10
  (gain `2^rel - 1`, BEIR's graded relevance; binary for the corpus's questions), both at the
  document level. Every arm also reports the vectors it stores (distinct chunk texts, the plane's
  atoms) and their bytes at float16.
- **The paired test.** For each query, the arm's score minus the reference arm's. The repository's
  sign-flip test (`eval/predictions/scoring.py::cluster_signflip`, each query its own cluster,
  20,000 random sign vectors, seed 0) gives the mean difference, its 95% interval by inverting the
  test, and a two-sided p. Holm's adjustment runs over the arms of one experiment on one data set
  and metric.
- **Decision words.** An arm is *better* when its Holm-adjusted p is below 0.05 with a positive
  mean; *worse* when below 0.05 with a negative mean; *no worse* when its interval's lower end is
  at or above -0.01 (a margin on recall@10 and nDCG@10, absolute).
- **The embedder is shared** with the working instance: one stream of 64 texts a request, the
  server's length fit (`core/ingest/embed.py::embed_fitting`) on every request, the server's slots
  sampled every five seconds through every embedding phase (`eval/two_phase_bench.py::
  Contention`) and probed before every request. No timing is reported as a result unless it was
  measured with no other caller; costs are reported in tokens embedded, which do not depend on
  load.

### Data

- **SciFact** (BEIR): 5,183 abstracts, the 300 test claims with graded relevance.
- **NFCorpus** (BEIR): 3,633 documents, the 323 test queries with graded relevance.
- Both are read from local parquet files (`~/models/bench-data`), each document written as an item
  `{title}\n\n{text}` (the corpus readers' form).
- **W, a long-document subsample of the corpus instance** (read only): the Wikipedia articles that
  are gold for the corpus battery's two link families (stage 1's question generator, 500 a family,
  seed 0: 543 questions, 442 articles), plus Wikipedia articles drawn at random (seed 0) to 600
  articles in all, chunked from their landed bytes as the landing chunks them. Queries: the 543 link
  questions (primary) and the 600 pooled articles' titles (secondary).
- **The corpus battery**: all 400,274 items of the corpus instance and stage 1's 4,714 questions
  in 11 families, read only.

### Experiment 1: tokenization and Unicode

- **Arms.** T0, the current tokenizer (maximal runs of letters and digits of `text.lower()`, no
  normalization); T1 NFC then `lower()`; T2 NFC then `casefold()`; T3 NFKC then `lower()`; T4 NFKC
  then `casefold()`; T5, T4 with combining marks continuing a token (a run starts with a letter or
  digit and continues with letters, digits and marks). An optional arm T6 adds a suffix-stripping
  stemmer of three rules (Harman's S stemmer), no new dependency.
- **Counts.** Per arm and collection (SciFact, NFCorpus, every chunk of the corpus instance): the
  vocabulary, the T0 terms that merge with another T0 term, the token occurrences that change, and
  the atoms (distinct chunk texts) that coincide under NFC and under NFKC. Content hashes are not
  changed by this experiment; the atom counts say what normalizing them would merge.
- **Retrieval.** BM25 (the store's `k1 = 1.2`, `b = 0.75`) over the chunk units, a document's
  score its best unit's. SciFact and NFCorpus with the live chunks; the corpus battery's lexical
  arm over every chunk of the instance, unscoped, every question.
- **Primary metrics.** nDCG@10 on SciFact and NFCorpus; recall@10 on the corpus battery (all
  questions pooled). Each arm against T0.
- **Decision rule.** Normalization is a correctness property: one text in two normal forms must
  give one set of terms. The implemented tokenizer is the most normalizing arm, in the order T5,
  T4, T3, T2, T1, that is not *worse* than T0 on any primary metric.
- **Falsifier.** If every NFKC arm is *worse* than T0 on some primary metric, compatibility
  folding is not free, and the fix is canonical equivalence alone (the best NFC arm).

### Experiment 2: chunk size

- **Arms.** Character budgets C600, C1200 (the reference), C2400, C4800, each with an overlap of
  one eighth (75, 150, 300, 600 characters), by the live chunker; token budgets K128, K256, K512,
  K1024 with an overlap of one eighth (16, 32, 64, 128 tokens): the same block-aware greedy packing,
  lengths counted in the embedder's own tokens (the server's `/tokenize`), an oversized block split
  at token boundaries.
- **Data.** NFCorpus and W (SciFact's documents are mostly one or two chunks at every budget).
- **Primary metrics.** nDCG@10 on NFCorpus; recall@10 on W's link questions. Each arm against
  C1200, with the vectors and bytes each stores and the tokens each embeds.
- **Falsifier.** The live budget stays unless some arm is *no worse* on both primary metrics
  while storing fewer vectors, or *better* on one and *no worse* on the other.

### Experiment 3: the chunk's context

- **Arms.** N, the reference (`title: none`, each chunk embedded alone); T, the document template
  with the item's title (`title: {title} | text: {text}`), each chunk alone; L, late chunking
  (Günther et al. 2024): the document embedded once and each chunk's vector the mean of its own
  tokens' embeddings, through a second llama-server started for this run with `--pooling none` on
  port 8093 and stopped after it; LT (secondary), late chunking with the title. All at C1200.
- **Late chunking, fixed before the run.** The document is the chunker's own text (its blocks
  joined as the chunker joins them), so every chunk is a span of it; a document longer than one
  window is embedded in windows of at most 2,048 tokens (the live server's slot), the template and
  the special tokens included, consecutive windows overlapping by 256 tokens; each token's vector
  is taken from the window in which it lies farthest from the window's ends; a chunk's vector is
  the mean over the tokens whose characters fall in its span, normalized.
- **Data.** SciFact, NFCorpus, W.
- **Primary metrics.** nDCG@10 on SciFact and NFCorpus; recall@10 on W's link questions. Each arm
  against N.
- **Falsifier.** An arm pays only if it is *better* than N on at least one primary metric and
  *worse* on none.

### Experiment 4: the query's task prompt

- **Arms.** `task: search result | query: {text}` (the reference), `task: question answering |
  query: {text}`, `task: fact checking | query: {text}`; documents as the reference arm of
  experiment 3.
- **Data.** SciFact, NFCorpus, W (link and title questions).
- **Primary metrics.** nDCG@10 on SciFact and NFCorpus; recall@10 on W's link questions.
- **Falsifier.** The store keeps one prompt unless an alternative is *better* on the set whose
  task it names (fact checking on SciFact, question answering on NFCorpus) and *worse* on none.

### Experiment 5: dimensions

- **Arms.** D768 (the reference), D512, D256, D128: the first D coordinates of every stored and
  query vector, renormalized, stored at float16. Flat: exact cosine at D. Rescored: the 50 best
  chunks at D, rescored with the full 768-dimension float16 vectors.
- **Data.** SciFact and NFCorpus (the reference arm's vectors); the corpus battery's semantic arm
  over the plane's 1,338,585 float16 atoms, unscoped, every question, the query vectors stage 1
  embedded for these questions with the live template.
- **Primary metrics.** nDCG@10 on SciFact and NFCorpus; recall@10 on the corpus battery. Bytes:
  `2D` per vector resident; rescored adds the full vector on disk (1,536 bytes), read for the
  candidates only.
- **Falsifier.** Truncation is recommended for the next stage only if D256 rescored is *no worse*
  than D768 on all three primary metrics.

### Experiment 6: semantic edges

- **Items.** Every corpus item with vectors, as stage 1's bridges read them: the mean of its chunk
  vectors, unit length. Each item's 50 nearest other items by exact cosine.
- **Rules.** G, stage 1's: each item's at most 10 nearest above the global 0.785. GQ, a global
  quantile control: one threshold, the median over all items of the cosine to the 10th nearest.
  SQ, per-source quantiles: for each source, the median over its items of the cosine to the 10th
  nearest; an item's at most 10 nearest above its own source's threshold. M, mutual nearest
  neighbours: an edge when each item is among the other's 10 nearest. C, CSLS (Conneau et al.
  2018): `2 cos(x, y) - r(x) - r(y)` with `r` the mean cosine to the 10 nearest; each item's at most
  10 best by CSLS among its 50 nearest, kept when the score is positive.
- **Scoring.** Stage 1's bridge reading: the explicit graph (item-local relations dropped, as at
  stage 1's final run) with each rule's semantic edges, community pairs across sources joined by
  more edges than the configuration null gives them, against the false-positive bar (null draws
  scored against the other draws, 20 draws, z = 3, at least 3 edges); with and without the
  OpenAlex and arXiv twins. Per source pair, its bridges against its own false positives.
- **Primary metrics.** Without the twins: the excess ratio (bridges over the false-positive bar)
  and the number of source pairs whose bridges exceed their own pair's bar. Secondary: semantic
  edges per item by source (the ratio of the largest source mean to the smallest), and hubness
  (the skewness of each item's in-degree in the 10-nearest digraph, and in each rule's graph).
- **Falsifier.** The global 0.785 stays unless a calibrated rule (GQ, SQ, M or C) has a higher
  excess ratio than G and at least as many source pairs above their own bar.

### Ranking the recommendations

Each change that passes its rule is ranked by gain per cost: the gain is its mean improvement on
its primary metrics; the cost is what adopting it re-derives (every vector of a store, the lexical
index alone, or nothing), in tokens and in the stores' current sizes. No live default is changed
by this study; each recommendation states its re-embedding cost.

## Results

(Added after the runs.)

## Deviations

(Any change to the protocol after this commit, with its reason.)
