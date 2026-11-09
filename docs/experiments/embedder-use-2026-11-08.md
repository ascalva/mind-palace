---
type: experiment-report
experiment: embedder-use
run: 1
status: complete                  # the protocol was committed before any comparison ran (f221f9b8)
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

### Summary

| experiment | verdict by the pre-declared rule | largest effect on a primary metric |
|---|---|---|
| 1 tokenization | T5 implemented (NFKC, casefold, marks inside) | none: rankings identical on the public sets, recall identical on the corpus |
| 2 chunk size | live budget stays (W recall undecided) | 2,400 characters: NFCorpus nDCG +0.021, W nDCG +0.031, half the vectors |
| 3 context | title in the template pays; late chunking does not | title: NFCorpus nDCG +0.038, SciFact +0.029; late: W recall -0.033 |
| 4 task prompt | keep "search result" | none better; fact checking worse on NFCorpus (-0.011) |
| 5 dimensions | 256 dimensions rescored recommended for the next stage | no loss on all three sets at a third of the resident bytes |
| 6 semantic edges | global 0.785 stays | calibrated rules and hubness corrections give fewer bridges per false positive |
| exploratory | dropping the title-only chunk | SciFact nDCG +0.033, NFCorpus +0.034, no embedding |

### Experiment 1: tokenization and Unicode

**Counts.** What each arm does to the terms of each collection's chunks (T0 is the tokenizer at
the base; "T0 terms merging" are T0 terms that become one term with another T0 term under the
arm; "occurrences changed" are T0 token occurrences whose term changes).

| collection | chunks (atoms) | arm | vocabulary | T0 terms merging (into) | occurrences changed |
|---|---|---|---|---|---|
| SciFact | 11,987 (11,986) | T0 | 38,466 | | |
| | | T2 NFC, casefold | 38,458 | 16 (8) | 76 |
| | | T4 NFKC, casefold | 38,449 | 32 (16) | 111 (0.009%) |
| | | T5 T4 with marks | 38,449 | 32 (16) | 111 |
| NFCorpus | 9,336 (9,228) | T0 | 28,425 | | |
| | | T2 | 28,419 | 12 (6) | 63 |
| | | T4 | 28,404 | 38 (19) | 138 (0.014%) |
| | | T5 | 28,404 | 38 (19) | 138 |
| corpus | 1,369,944 (1,338,585) | T0 | 1,053,985 | | |
| | | T1 NFC, lower | 1,053,761 | 142 (71) | 90 |
| | | T2 | 1,052,335 | 2,964 (1,465) | 25,492 |
| | | T3 NFKC, lower | 1,049,710 | 6,862 (3,066) | 36,263 |
| | | T4 | 1,049,534 | 7,211 (3,237) | 53,042 (0.028%) |
| | | T5 | 1,050,412 | 7,211 (3,237) | 53,042 |

The merged terms on the public sets are the forms a reader takes for one: `identiﬁed` and
`identified` (a ligature from PDF extraction), `µm` and `μm` (the micro sign and the Greek
letter), `ca²` and `ca2`, `h₂o₂` and `h2o2`, `ic₅₀` and `ic50`, `b₁₂` and `b12`. T5 has 878 more
terms than T4 on the corpus and 8,309 fewer token occurrences: words whose combining marks split
them under T4 are whole under T5. Atoms: no two distinct chunk texts coincide under NFC on any
collection; under NFKC, 24 of the corpus's 1,338,585 atoms coincide with another; 574 atoms are not
in NFC, 18,931 not in NFKC, and 2,086 hold a combining mark that NFC leaves in place. Content
hashes stay on the raw bytes, so these merges are reported, not made.

**Retrieval.** BM25 over the chunks, a document's score its best unit's.

| set (queries) | arm | recall@10 | nDCG@10 | primary against T0: mean (95% interval), Holm p, verdict |
|---|---|---|---|---|
| SciFact (300) | T0 | 0.766 | 0.649 | reference |
| | T1 to T5 | 0.766 | 0.649 | nDCG +0.000 (identical ranking for every query), no worse |
| | T6 S stemmer | 0.777 | 0.661 | nDCG +0.012 (+0.001, +0.024), p 0.237, no worse |
| NFCorpus (323) | T0 | 0.150 | 0.302 | reference |
| | T1 to T5 | 0.150 | 0.302 | nDCG +0.000 (identical ranking for every query), no worse |
| | T6 | 0.154 | 0.316 | nDCG +0.014 (+0.006, +0.022), p 0.005, better |
| corpus battery (4,714) | T0 | 0.874 | 0.749 | reference |
| | T1 | 0.874 | 0.748 | recall +0.000 (every query equal), no worse |
| | T2 | 0.874 | 0.751 | recall +0.000; nDCG +0.003 (-0.001, +0.006), p 0.685 |
| | T3, T4 | 0.874 | 0.749 | recall +0.000; nDCG +0.000 |
| | T5 | 0.874 | 0.748 | recall +0.000; nDCG -0.000 (-0.004, +0.003), p 1.000 |
| | T6 | 0.871 | 0.746 | recall -0.002 (-0.005, +0.000), p 0.578, no worse |

**Verdict.** No normalizing arm is worse than T0 on any primary metric, so the pre-declared rule
implements T5 (NFKC, `casefold`, marks inside a token); the falsifier (every NFKC arm worse
somewhere) did not occur. The retrieval figures cannot tell the arms apart: these sets are
English, and the words normalization merges are rare (0.009% to 0.028% of occurrences). The
stemmer (informational, English only) helps BM25 on the two medical and scientific sets and
not on the corpus battery, whose questions are titles and names; it is not adopted.

### Experiment 2: chunk size

Each arm against C1200 (mean paired difference, 95% interval, verdict; Holm over the seven arms).
Vectors are distinct chunk inputs; tokens are what embedding the arm's chunks takes.

| arm | NFCorpus nDCG@10 | against C1200 | W link recall@10 | against C1200 | W link nDCG@10 | against C1200 | vectors NFCorpus / W | tokens W (M) |
|---|---|---|---|---|---|---|---|---|
| C600 | 0.327 | +0.001 (-0.009, +0.011) no worse | 0.565 | -0.038 (-0.062, -0.013) worse | 0.441 | -0.022 worse | 14,213 / 47,446 | 5.48 |
| C1200 | 0.326 | reference | 0.602 | reference | 0.464 | reference | 9,228 / 25,398 | 5.29 |
| C2400 | 0.347 | +0.021 (+0.009, +0.034) better | 0.601 | -0.001 (-0.021, +0.020) undecided | 0.495 | +0.031 better | 3,866 / 11,943 | 5.10 |
| C4800 | 0.354 | +0.028 (+0.015, +0.042) better | 0.598 | -0.005 (-0.027, +0.018) undecided | 0.486 | +0.022 better | 3,611 / 5,572 | 4.96 |
| K128 | 0.326 | +0.001 (-0.009, +0.011) no worse | 0.587 | -0.015 (-0.039, +0.008) undecided | 0.446 | -0.018 worse | 14,237 / 46,223 | 5.44 |
| K256 | 0.322 | -0.004 (-0.010, +0.002) no worse | 0.605 | +0.002 (-0.017, +0.021) undecided | 0.469 | +0.006 no worse | 8,934 / 24,644 | 5.28 |
| K512 | 0.346 | +0.021 (+0.008, +0.033) better | 0.604 | +0.002 (-0.018, +0.022) undecided | 0.485 | +0.021 better | 4,086 / 11,570 | 5.10 |
| K1024 | 0.354 | +0.028 (+0.015, +0.042) better | 0.610 | +0.008 (-0.017, +0.032) undecided | 0.484 | +0.020 better | 3,613 / 5,434 | 4.96 |

W's 600 title questions find their article in the first ten under every arm (recall 1.000; K128
0.998); their nDCG@10 falls at C600 and K128 (-0.033, -0.031, worse) and is no worse elsewhere.
The median chunk takes 151 tokens at C1200 on NFCorpus and 210 on W, 334 and 435 at C2400.

**Verdict.** No arm passes the pre-declared rule, so the live budget stays: the budgets of 2,400
characters and more, and of 512 tokens and more, are *better* on NFCorpus's nDCG@10 and on W's
nDCG@10 with half to a fifth of the vectors, but W's recall@10, its primary metric, is undecided
(every interval holds 0 and reaches below the -0.01 margin). Budgets below the live one are worse
on W. Counting the budget in the embedder's tokens instead of characters changes nothing at a
matched size (K512 against C2400, K1024 against C4800).

### Experiment 3: the chunk's context

| arm | SciFact nDCG@10 | against N | NFCorpus nDCG@10 | against N | W link recall@10 | against N | W link nDCG@10 | tokens SciFact / W (M) |
|---|---|---|---|---|---|---|---|---|
| N | 0.792 | reference | 0.326 | reference | 0.602 | reference | 0.464 | 1.89 / 5.29 |
| T, title | 0.821 | +0.029 (+0.011, +0.047) better | 0.364 | +0.038 (+0.025, +0.052) better | 0.593 | -0.009 (-0.029, +0.010) undecided | 0.481 (+0.017, better) | 2.11 / 5.34 |
| L, late | 0.839 | +0.047 (+0.028, +0.066) better | 0.342 | +0.016 (+0.004, +0.029) better | 0.570 | -0.033 (-0.057, -0.009) worse | 0.450 (-0.014) | 1.65 / 5.31 |
| LT, late, title | 0.824 | +0.032 (+0.008, +0.056) better | 0.340 | +0.015 (-0.001, +0.031) no worse | 0.557 | -0.045 (-0.071, -0.019) worse | 0.436 (-0.028, worse) | 1.74 / 5.32 |
| L1, late pooling alone | 0.832 | +0.040 (+0.022, +0.057) better | 0.356 | +0.030 (+0.017, +0.043) better | 0.590 | -0.012 (-0.028, +0.003) undecided | 0.458 (-0.006) | 1.45 / 5.29 |

SciFact's recall@10 is 0.884 (N), 0.907 (T), 0.926 (L), 0.920 (L1); W's title questions keep
recall 1.000 under every arm, their nDCG@10 +0.005 under T (better), -0.011 and -0.015 under L
and LT (worse). Late chunking embeds W's 600 articles in 2,620 windows of at most 2,048 tokens.

**Verdict.** T pays: *better* on both public sets, *worse* on none (W's recall undecided, its
nDCG better). L and LT do not: *worse* on W's recall. The control L1 (each chunk alone, its
vector the mean of its own tokens, the template's and the special tokens left out) gives most of
L's gain on SciFact and more than L on NFCorpus, so on these short documents what helps is
leaving the template out of the mean, not the other chunks in view; on W, the long documents,
the other chunks in view cost recall (L -0.033 against L1 -0.012). On one-chunk documents the
late and independent vectors agree at a median cosine of 0.992 (SciFact) and 0.990 (NFCorpus).

### Experiment 4: the query's task prompt

| prompt | SciFact nDCG@10 | against search result | NFCorpus nDCG@10 | against search result | W link recall@10 | against search result |
|---|---|---|---|---|---|---|
| search result | 0.792 | reference | 0.326 | reference | 0.602 | reference |
| question answering | 0.795 | +0.003 (-0.006, +0.012) no worse | 0.330 | +0.005 (-0.001, +0.010) no worse | 0.602 | -0.000 (-0.016, +0.016) undecided |
| fact checking | 0.784 | -0.008 (-0.023, +0.008) undecided | 0.314 | -0.011 (-0.019, -0.003) worse | 0.599 | -0.003 (-0.023, +0.017) undecided |

**Verdict.** The store keeps one prompt: fact checking is not better on SciFact, whose claims
are its task, and question answering is not better on NFCorpus. No prompt moves W.

### Experiment 5: dimensions

| arm | bytes resident | SciFact nDCG@10 | against D768 | NFCorpus nDCG@10 | against D768 | corpus recall@10 | against D768 |
|---|---|---|---|---|---|---|---|
| D768 | 1,536 | 0.792 | reference | 0.326 | reference | 0.822 | reference |
| D512 | 1,024 | 0.791 | -0.001 no worse | 0.326 | +0.001 no worse | 0.823 | +0.001 no worse |
| D512 rescored | 1,024 | 0.792 | +0.000 no worse | 0.326 | +0.000 no worse | 0.822 | -0.000 no worse |
| D256 | 512 | 0.788 | -0.004 (-0.018, +0.011) undecided | 0.312 | -0.014 worse | 0.819 | -0.003 no worse |
| D256 rescored | 512 | 0.792 | +0.000 no worse | 0.325 | -0.001 (-0.003, +0.001) no worse | 0.822 | -0.000 (-0.001, +0.000) no worse |
| D128 | 256 | 0.718 | -0.074 worse | 0.249 | -0.077 worse | 0.790 | -0.032 worse |
| D128 rescored | 256 | 0.785 | -0.007 undecided | 0.309 | -0.016 worse | 0.813 | -0.009 worse |

Rescored arms read the full float16 vector (1,536 bytes) of their 50 candidates from disk. The
corpus battery's semantic arm runs over the plane's 1,338,585 atoms as stored, with the query
vectors stage 1 embedded for its 4,714 questions.

**Verdict.** D256 rescored is *no worse* than D768 on all three primary metrics, so truncation to
256 dimensions with float16 rescoring of 50 candidates is recommended for the next stage: a third
of the resident bytes. Flat truncation to 256 already loses on NFCorpus, and 128 dimensions lose
everywhere, rescored or not.

### Experiment 6: semantic edges

Items: the 400,274 corpus items, each the mean of its chunk vectors. In the 10-nearest digraph the
in-degree's skewness is 21.4, the largest in-degree 3,071, and 9.1% of items are no item's
neighbour (hubness). The thresholds the data set: one global median of the cosine to the 10th
nearest, 0.865; per source, 0.808 (Hacker News) to 0.948 (Gutenberg), Wikipedia 0.890, OpenAlex
0.887, arXiv 0.883, Stack Exchange 0.848. Every one is above 0.785, so G gives nearly every item
its 10 nearest.

Without the twins (the explicit graph alone: 37 bridges against a bar of 39.3):

| rule | semantic edges | bridges | false-positive bar | excess ratio | source pairs above their own bar | degree, largest source mean over smallest | degree skewness |
|---|---|---|---|---|---|---|---|
| G, 0.785 | 3,302,152 | 3,030 | 798.4 | 3.79 | 12 | 2.3 | 23.0 |
| GQ, global median | 1,908,304 | 664 | 183.2 | 3.62 | 8 | 10.8 | 10.2 |
| SQ, per-source medians | 1,973,267 | 1,448 | 540.0 | 2.68 | 9 | 2.0 | 16.2 |
| M, mutual 10 nearest | 642,246 | 125 | 148.8 | 0.84 | 3 | 2.5 | 0.8 |
| C, CSLS | 407,441 | 79 | 100.8 | 0.78 | 3 | 2.5 | 1.2 |

With the twins the readings are within a few bridges of these (G 3,044 against 821.6).

**Verdict.** The global 0.785 stays: no calibrated rule has a higher excess ratio or as many
source pairs above their own bar. The per-source thresholds even out the degrees across sources
(2.0 against 2.3 for G and 10.8 for the global median) but find fewer bridges per false
positive. The two corrections for hubness remove nearly all of it (degree skewness 0.8 and 1.2
against 23.0) and with it the bridges: below the null, as the explicit graph alone is. The excess
of semantic bridges over the null at stage 1 is carried by the hub edges.

At the chunk grain, the title-only atoms (a chunk that is its item's title alone) of OpenAlex and
arXiv have 19,242 and 15,779 atoms of other items above 0.785 on average, against 8,944 and 7,209
for their other atoms (Wikipedia 11.8, Stack Exchange 915, Gutenberg 220, Hacker News 28 for body
atoms).

### The title-only chunk (an exploratory arm)

The live chunker emits an item's title as a chunk of its own when the first paragraph does not
fit beside it, then carries the whole title into the next chunk as its overlap. On these sets
that is 3,490 of SciFact's 11,987 chunks (29%), 2,860 of NFCorpus's 9,336 (31%), and in the corpus
84,002 of 1,369,944 (6.1%): 61,845 of OpenAlex's 266,149 chunks and 21,458 of arXiv's 81,889,
almost none elsewhere. Arm Nd drops every chunk carried whole into the next one, from N's cached
vectors (no embedding):

| set | chunks dropped | recall@10 against N | nDCG@10 against N |
|---|---|---|---|
| SciFact | 3,137 of 11,987 | +0.034 (+0.013, +0.054) better | +0.033 (+0.017, +0.049) better |
| NFCorpus | 2,802 of 9,336 | +0.009 (-0.004, +0.023) no worse | +0.034 (+0.020, +0.048) better |
| W link | 9 of 25,399 | +0.009 (-0.000, +0.018) no worse | +0.005 (+0.002, +0.009) better |
| W title | | +0.000 | +0.003 (+0.000, +0.006) better |

### Measurement conditions

The stack's embedder took one stream of 64 texts a request: 629 requests (39,950 texts) for
NFCorpus's chunk budgets, 2,782 (176,874 texts, one input cut to fit) for W's, 922 for the title
arms and 58 for the query prompts. Before 327 of NFCorpus's 629 requests (17:32 to 18:13 on
2026-11-08) a slot of the server was busy; whose, the run cannot say, since the sampler of the
server's TCP connections started at 18:14. From then to 22:12 a slot was busy before 6 of 3,762
requests, and the sampler, every two seconds, saw no client but the study's own processes. The
late-chunking server ran beside the stack's on the same GPU. No timing is reported as a result;
rankings do not depend on load.

## Deviations

- **A reference arm, TA, in experiment 1.** Stage 1's corpus index was built on its branch by an
  ASCII tokenizer (`[0-9a-z]+`), not the Unicode one at this base; its exact vocabulary (926,483
  terms) is reproduced by TA. Against T0 on the corpus battery TA loses recall@10 (-0.002, -0.003
  to -0.000, worse: OpenAlex titles 0.968 to 0.952, Stack Exchange titles 0.962 to 0.958). It is a
  reference, not a candidate.
- **A control arm, L1, in experiment 3,** added before the context comparison was read: each chunk
  through the pooling-none server alone, its vector the mean of its own tokens. It separates what
  late chunking changes in the pooled set (the template's and the special tokens left out) from
  what it changes in context (the other chunks in view).
- **An exploratory arm, Nd,** after the counts showed the title-only chunks: the live chunks
  without the ones carried whole into the next, read from N's cached vectors. It was not
  pre-declared, so its verdicts are exploratory.
- **A descriptive check in experiment 6:** the chunk-grain neighbours above 0.785 of title-only
  atoms against other atoms, for a sample of each source's items (same-item atoms included, at most
  a few an item).
- Experiment 1's corpus reading ran over every chunk, not a subsample; experiment 5's used the
  query vectors stage 1 embedded for the same questions (their texts hash to the same cache file);
  the optional stemmer arm T6 ran.
