---
type: experiment-report
experiment: corpus-stage1
run: 1
status: complete (stage 1)
started: 2026-11-07
links:
  - docs/design-notes/dn-corpus-instance.md                # the design, its staged plan and stage 1's falsifiers
  - docs/experiments/corpus-measurements-2026-11-07.md     # the ratios, rates and yield policy this run used
  - docs/experiments/corpus-stage1-2026-11-07.json         # the numbers below, as data
  - docs/experiments/scale-study-2026-11-07.md             # the macro method reused here
  - papers/2026-11-07-corpus-stage1/paper.tex              # the article
  - eval/corpus/                                           # the harness that produced every table
---

# Corpus stage 1: about a gigabyte of open text in a named instance

**Question.** dn-corpus-instance §6 asks stage 1 two things: whether the sources connect, and
whether crowding is real at a million chunks; and it names the measurements that answer them and
the falsifiers that would say no. This report gives what was built, what was ingested, and every
measurement of the stage-1 table with its falsifier held or broken. The run was two-phase: every
item landed first with its label, its explicit relations and a lexical index, the structural
measurements ran on that, and the vectors were derived from the raw store in the background.

## Summary

- **Ingested**: six sources, 400,274 items, 1.02 GB of text, 1,369,944 chunks, in a named instance that shares no namespace with the live one. The structural phase landed every item in 0.6 s per thousand at the lander; the vectors follow from the raw store.
- **Macro**: the citation graph's 6-core and 10-core gaps settle by 5 x 10^4 nodes and its Hodge split a decade earlier (CIF-7, CIF-8 held); the hyperlink graph settles near 10^4; versions, replies and answers are forests with no core.
- **Bridges**: 106 community pairs across sources above a degree-preserving null (bar 40.9), 87 of them arXiv and OpenAlex, whose twins are one paper in two sources; without the twins 37 against 39.3, while arXiv and Stack Exchange (22), Hacker News and Wikipedia (10) and arXiv and Wikipedia (5) stand above their own pair's false positives (0, 0, 1.4).
- **Rises**: rho_w 0.116 within sources, rho_b 0.091 across them, at the shift null's 0.092; N_eff 9.3 (CIF-2 held on both clauses as designed).
- **Crowding**: lexical recall at ten falls with the corpus in 8 of 11 families, by up to 0.35; a source scope removes the fall other sources cause, but scoped recall still falls with the source's own growth in 6 families (CIF-9: first clause held, second broken, lexical arm).
- **Attribution**: the OpenAlex and arXiv twins share the value (Shapley 0.49 and 0.50) and neither is necessary (leave-one-out near 0): the SCL-3 redundancy witness (CIF-10 held).
- **Cost**: a sentence over the observed stratum builds its universe from the whole stratum and passes 6 GB near ten thousand items; its Python share is above 20% (CIF-11 broken).
- **Vectors**: 1,338,585 atoms embedded in 11.4 hours over four runs, no pause for the chat model, one text cut to fit the embedder (a 1,145-character chunk of 2,951 tokens), nothing pending at the battery. The semantic arm crowds harder than the lexical (recall falls in 9 of 11 families, by up to 0.30); fusing the two is at or above either in 8 of 11. The embedder as a source: Shapley 0.39, leave-one-out 0.006 beside the lexical index. CIF-9's second clause breaks in all three arms, CIF-10 holds in all three. Semantic bridges: 3,014 community pairs against a bar of 807 (792 without the twins). At the live store's sigma of 0.785 a chunk has 9 near chunks of other items in Wikipedia and about 10,700 in OpenAlex: the threshold does not carry across sources. The one-bit code keeps 0.79 of the exact top ten rescored at m = 40 (a warning for CIF-3 at stage 2); the compact occupancy row is 19.4 B (CIF-4 held) while the plane as built holds 734 B per occupancy.

## What was built

- `[ingestion.corpus]` (the config section) and `config/instances/corpus.toml` (the named
  instance `corpus`, everything under `instances/corpus/`).
- Stream sources and `items(h, batch: b)` in the ingress, `ingress/sync_corpus.palace`, and a
  batched landing that lands a plan of fresh stores a stage at a time with the key last
  (ING-5, ING-7, ING-9, ING-11; tested at four cut points and against the effect-by-effect
  landing).
- Two phases: a structural landing (raw object, attestation, key; no plane rows) and the vector
  backfill from the raw store (`index_from_raw`), which end where one landing ends (tested).
- A BM25 index of the landed chunks (`core/ingest/lexical.py`), the structural phase's lexical
  representation.
- Six edge readers (`edge/corpus/`), the runner and its embedder policy (`scripts/corpus.py`,
  `ops/corpus/embedder.py`), and the measurement harness (`eval/corpus/`).

## Isolation

Before anything was fetched or landed, `scripts/corpus.py isolation --live <main checkout>`
ran the loader's own check, `shared` over `namespaces_of`, every location compared by real path,
of the corpus instance against the default instance of this worktree, the bench instance
declared beside it, and the default instance of the live checkout (its two overlays read, nothing
written). All three lists of shared namespaces were empty. The control, a written path that is a
link into the live instance's `data/`, was found shared 16 times, once for each written
location under it, so the check has power. The instance root is
`<worktree>/instances/corpus`; the live store's data directory is the checkout's `data/`, which
nothing of this run opened. The runner proves isolation again before it writes, takes the
instance's own supervisor lock, and ran as processes started and stopped by hand; no LaunchAgent
was installed.

## Data

| source | what | how | items | text (MB) | zstd -3 | chunks | chunks per MB |
|---|---|---|---|---|---|---|---|
| Wikipedia | English articles, a link-connected sample from network-science and computing seeds | MediaWiki API, 50 pages a request, 1 s apart | 11,414 | 398.0 | 2.86 | 488,999 | 1,229 |
| OpenAlex | works with abstracts, topics T10064, T10720, T11273, T12592 and part of T11252 | keyless API, date slices, basic paging | 145,029 | 171.1 | 3.28 | 266,149 | 1,556 |
| arXiv | records of physics.soc-ph, cs.SI, nlin.AO, and the arXiv records of the OpenAlex works that name one | arXiv's query API, 3 s apart | 41,659 | 50.9 | 3.16 | 81,889 | 1,609 |
| Stack Exchange | cstheory and cs whole, datascience to the budget, from the 2024-04-02 dump | archive.org, bsdtar | 163,503 | 170.2 | 2.97 | 239,270 | 1,406 |
| Project Gutenberg | 338 English science texts by Library of Congress class | catalogue, then gutenberg.pglaf.org, 2 s apart | 338 | 108.1 | 3.03 | 125,379 | 1,159 |
| Hacker News | the most recent three weeks whole, then stories of 2012 to 2024 sampled uniformly; each story with its reply tree, one thread an item | the official API: ids walked down from the newest, then drawn uniformly in 2012 to 2024's id range; 12 connections, at most 80 requests a second | 38,331 | 120.1 | 2.71 | 168,258 | 1,402 |
| **total** | | | **400,274** | **1018.4** | **2.96** | **1,369,944** | **1,345** |

D-2 was decided during the run: Hacker News is included through its official API, held
locally and never republished, so the mix is the design's own rescaled into 1 GB: Wikipedia 35%,
OpenAlex 24%, Stack Exchange 15%, Hacker News 12%, Gutenberg 9.5%, arXiv 4.5%. Wikipedia, Stack
Exchange, Gutenberg and arXiv reached or passed their share (they were sized before the decision,
on the proportions without Hacker News). OpenAlex stopped at 171 of its 240 MB when the keyless
API's daily budget (0.10 USD, a thousand requests, shared by the IP address) was spent; its
remainder needs the next day's budget or an API key, which is an account (D-5). Hacker News first walked item ids down from the newest (15,362 threads, 47 MB, the last three weeks), which put it outside every dated window the rises read; the rest of its budget went to threads drawn uniformly among the stories of 2012 to 2024 (an item id drawn at random in the window's range, kept when it is a live story, with its whole reply tree): 22,969 threads, 73 MB. Its text is held locally and never republished; only aggregate measurements leave the instance.

## Results

The macro quantities, the bridges and rises, the lexical arm and the cost needed no vector and ran as soon as the structural phase landed every item (the lexical arm again once Hacker News landed); the three arms, the semantic bridges, the codes, the BEIR control, the footprint and the final cost probe ran once every vector was in. In the battery's tables the arm keyed `both` is the lexical and semantic arms fused by reciprocal rank (the article's fused arm).

### Macro quantities

**arxiv.version**: 16,620 edges, 33,240 nodes in 16,620 components, the largest 2 nodes: no component reaches the ladder's first rung (300), so no macro quantity is defined.

**hackernews.reply** (343,930 edges)

| cut N | edges | mean deg | min deg / ln N | gamma | 6-core n | 6-core gamma | 10-core n | grad | curl | harm | Hodge on n |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 59 | 58 | 2.0 | 0.24 | 0.0270 | 0 | n/a | 0 | 1.000 | 0.000 | 0.000 | 59 |
| 204 | 203 | 2.0 | 0.19 | 0.0080 | 0 | n/a | 0 | 1.000 | 0.000 | 0.000 | 204 |
| 204 | 203 | 2.0 | 0.19 | 0.0080 | 0 | n/a | 0 | 1.000 | 0.000 | 0.000 | 204 |
| 411 | 410 | 2.0 | 0.17 | 0.0033 | 0 | n/a | 0 | 1.000 | 0.000 | 0.000 | 411 |
| 443 | 442 | 2.0 | 0.16 | 0.0032 | 0 | n/a | 0 | 1.000 | 0.000 | 0.000 | 443 |
| 776 | 775 | 2.0 | 0.15 | 0.0023 | 0 | n/a | 0 | 1.000 | 0.000 | 0.000 | 776 |
| 1,904 | 1,903 | 2.0 | 0.13 | 0.0009 | 0 | n/a | 0 | 1.000 | 0.000 | 0.000 | 1,904 |

| reading | full | 3-core | 6-core | 10-core |
|---|---|---|---|---|
| N* of gamma | n/a | n/a | n/a | n/a |
| N* of gap2 | n/a | n/a | n/a | n/a |
| N* of gap3 | n/a | n/a | n/a | n/a |
| N* of gap4 | n/a | n/a | n/a | n/a |
| N* of the Hodge widths (grad, curl, harm) | 59, n/a, n/a | | | |

**openalex.citation** (1,118,912 edges)

| cut N | edges | mean deg | min deg / ln N | gamma | 6-core n | 6-core gamma | 10-core n | grad | curl | harm | Hodge on n |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 236 | 506 | 4.3 | 0.18 | 0.0275 | 13 | 0.7420 | 0 | 0.875 | 0.096 | 0.029 | 236 |
| 886 | 2,217 | 5.0 | 0.15 | 0.0166 | 85 | 0.0325 | 0 | 0.859 | 0.108 | 0.033 | 886 |
| 2,890 | 9,561 | 6.6 | 0.12 | 0.0031 | 633 | 0.0185 | 0 | 0.820 | 0.130 | 0.050 | 2,890 |
| 9,788 | 44,563 | 9.1 | 0.11 | 0.0042 | 3,770 | 0.0052 | 1,057 | 0.790 | 0.161 | 0.049 | 9,788 |
| 29,854 | 208,787 | 14.0 | 0.10 | 0.0130 | 16,021 | 0.0134 | 8,930 | 0.822 | 0.134 | 0.043 | 14,449 |
| 99,341 | 1,038,866 | 20.9 | 0.09 | 0.0143 | 66,583 | 0.0196 | 47,805 | 0.847 | 0.086 | 0.067 | 18,495 |
| 107,497 | 1,115,464 | 20.8 | 0.09 | 0.0103 | 71,413 | 0.0194 | 51,208 | 0.852 | 0.087 | 0.061 | 19,571 |

| reading | full | 3-core | 6-core | 10-core |
|---|---|---|---|---|
| N* of gamma | 27850 | 74331 | 51262 | 28912 |
| N* of gap2 | n/a | n/a | n/a | 37710 |
| N* of gap3 | n/a | n/a | n/a | n/a |
| N* of gap4 | n/a | n/a | n/a | n/a |
| N* of the Hodge widths (grad, curl, harm) | 236, 2890, 9788 | | | |

**stackexchange.answer**: 89,378 edges, 147,398 nodes in 58,020 components, the largest 93 nodes: no component reaches the ladder's first rung (300), so no macro quantity is defined.

**stackexchange.link** (13,410 edges)

| cut N | edges | mean deg | min deg / ln N | gamma | 6-core n | 6-core gamma | 10-core n | grad | curl | harm | Hodge on n |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 70 | 71 | 2.0 | 0.23 | 0.0063 | 0 | n/a | 0 | 0.995 | 0.005 | 0.000 | 70 |
| 253 | 295 | 2.3 | 0.18 | 0.0030 | 0 | n/a | 0 | 0.957 | 0.033 | 0.009 | 253 |
| 576 | 676 | 2.3 | 0.16 | 0.0026 | 0 | n/a | 0 | 0.956 | 0.027 | 0.017 | 576 |
| 2,923 | 3,568 | 2.4 | 0.12 | 0.0012 | 0 | n/a | 0 | 0.960 | 0.029 | 0.011 | 2,923 |
| 4,489 | 5,485 | 2.4 | 0.12 | 0.0010 | 0 | n/a | 0 | 0.961 | 0.028 | 0.011 | 4,489 |

| reading | full | 3-core | 6-core | 10-core |
|---|---|---|---|---|
| N* of gamma | n/a | n/a | n/a | n/a |
| N* of gap2 | n/a | n/a | n/a | n/a |
| N* of gap3 | n/a | n/a | n/a | n/a |
| N* of gap4 | n/a | n/a | n/a | n/a |
| N* of the Hodge widths (grad, curl, harm) | 70, n/a, n/a | | | |

**stackexchange.version**: 126,752 edges, 195,277 nodes in 68,525 components, the largest 84 nodes: no component reaches the ladder's first rung (300), so no macro quantity is defined.

**wikipedia.hyperlink** (784,737 edges)

| cut N | edges | mean deg | min deg / ln N | gamma | 6-core n | 6-core gamma | 10-core n | grad | curl | harm | Hodge on n |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 302 | 1,119 | 7.4 | 0.17 | 0.0991 | 72 | 0.1811 | 0 | 0.440 | 0.331 | 0.229 | 302 |
| 1,000 | 8,988 | 18.0 | 0.14 | 0.0971 | 936 | 0.0968 | 623 | 0.350 | 0.493 | 0.157 | 1,000 |
| 3,031 | 77,832 | 51.4 | 0.25 | 0.1203 | 3,028 | 0.1203 | 3,017 | 0.284 | 0.680 | 0.036 | 3,031 |
| 10,002 | 548,987 | 109.8 | 0.33 | 0.1067 | 10,000 | 0.1067 | 9,998 | 0.205 | 0.777 | 0.019 | 7,394 |
| 11,414 | 693,196 | 121.5 | 0.32 | 0.1075 | 11,413 | 0.1075 | 11,411 | 0.210 | 0.772 | 0.018 | 7,509 |

| reading | full | 3-core | 6-core | 10-core |
|---|---|---|---|---|
| N* of gamma | 8502 | 8502 | 8500 | 8496 |
| N* of gap2 | 8502 | 8502 | 8500 | 8496 |
| N* of gap3 | 9702 | 9701 | 8500 | 9696 |
| N* of gap4 | n/a | n/a | n/a | n/a |
| N* of the Hodge widths (grad, curl, harm) | 302, 302, n/a | | | |

### Bridges

**explicit**: 1,942,168 edges, 30,720 across sources (share 0.016, the null's 0.531); 106 community pairs over the null against a false-positive bar of 40.9; CIF-2 (bridges) held.

| source pair | edges | bridges | the null's false positives (mean, bar) |
|---|---|---|---|
| arxiv-hackernews | 9 | 0 | 0.0, 0.0 |
| arxiv-openalex | 27,397 | 87 | 0.8, 2.5 |
| arxiv-stackexchange | 463 | 10 | 3.4, 6.4 |
| arxiv-wikipedia | 195 | 0 | 2.1, 4.2 |
| gutenberg-wikipedia | 1 | 0 | 0.0, 0.0 |
| hackernews-openalex | 0 | 0 | 0.3, 1.2 |
| hackernews-wikipedia | 283 | 9 | 0.0, 0.0 |
| openalex-stackexchange | 295 | 0 | 7.9, 11.7 |
| openalex-wikipedia | 287 | 0 | 0.0, 0.0 |
| stackexchange-wikipedia | 1,790 | 0 | 19.8, 27.1 |

**explicit_without_twins**: 1,914,771 edges, 3,323 across sources (share 0.002, the null's 0.526); 37 community pairs over the null against a false-positive bar of 39.3; CIF-2 (bridges) broken.

| source pair | edges | bridges | the null's false positives (mean, bar) |
|---|---|---|---|
| arxiv-hackernews | 9 | 0 | 0.0, 0.0 |
| arxiv-stackexchange | 463 | 22 | 0.0, 0.0 |
| arxiv-wikipedia | 195 | 5 | 0.4, 1.4 |
| gutenberg-wikipedia | 1 | 0 | 0.0, 0.0 |
| hackernews-openalex | 0 | 0 | 0.1, 0.7 |
| hackernews-wikipedia | 283 | 10 | 0.0, 0.0 |
| openalex-stackexchange | 295 | 0 | 8.5, 13.2 |
| openalex-wikipedia | 287 | 0 | 0.0, 0.0 |
| stackexchange-wikipedia | 1,790 | 0 | 16.9, 27.3 |

**with_semantic**: 5,015,370 edges, 673,153 across sources (share 0.134, the null's 0.689); 3014 community pairs over the null against a false-positive bar of 806.9; CIF-2 (bridges) held.

| source pair | edges | bridges | the null's false positives (mean, bar) |
|---|---|---|---|
| arxiv-gutenberg | 672 | 24 | 1.3, 3.5 |
| arxiv-hackernews | 12,018 | 268 | 60.9, 70.6 |
| arxiv-openalex | 412,262 | 131 | 1.7, 4.8 |
| arxiv-stackexchange | 22,017 | 161 | 85.8, 98.9 |
| arxiv-wikipedia | 9,066 | 43 | 5.3, 8.3 |
| gutenberg-hackernews | 2,113 | 147 | 0.6, 1.6 |
| gutenberg-openalex | 184 | 0 | 0.0, 0.0 |
| gutenberg-stackexchange | 909 | 29 | 2.1, 4.5 |
| gutenberg-wikipedia | 3,218 | 9 | 0.0, 0.0 |
| hackernews-openalex | 12,045 | 190 | 199.5, 232.4 |
| hackernews-stackexchange | 37,592 | 1244 | 206.5, 237.2 |
| hackernews-wikipedia | 21,745 | 601 | 133.6, 155.2 |
| openalex-stackexchange | 101,817 | 61 | 14.0, 21.9 |
| openalex-wikipedia | 10,264 | 0 | 0.0, 0.0 |
| stackexchange-wikipedia | 27,231 | 106 | 34.7, 49.3 |

**with_semantic_without_twins**: 4,987,973 edges, 645,756 across sources (share 0.129, the null's 0.689); 3014 community pairs over the null against a false-positive bar of 791.9; CIF-2 (bridges) held.

| source pair | edges | bridges | the null's false positives (mean, bar) |
|---|---|---|---|
| arxiv-gutenberg | 672 | 24 | 0.7, 2.0 |
| arxiv-hackernews | 12,018 | 276 | 60.0, 76.0 |
| arxiv-openalex | 384,865 | 125 | 1.8, 3.5 |
| arxiv-stackexchange | 22,017 | 168 | 80.0, 101.3 |
| arxiv-wikipedia | 9,066 | 43 | 4.5, 8.1 |
| gutenberg-hackernews | 2,113 | 148 | 1.0, 3.0 |
| gutenberg-openalex | 184 | 0 | 0.0, 0.0 |
| gutenberg-stackexchange | 909 | 26 | 2.8, 6.6 |
| gutenberg-wikipedia | 3,218 | 9 | 0.1, 0.7 |
| hackernews-openalex | 12,045 | 195 | 203.6, 229.8 |
| hackernews-stackexchange | 37,592 | 1236 | 211.2, 234.4 |
| hackernews-wikipedia | 21,745 | 603 | 140.1, 171.2 |
| openalex-stackexchange | 101,817 | 61 | 15.0, 25.1 |
| openalex-wikipedia | 10,264 | 0 | 0.0, 0.0 |
| stackexchange-wikipedia | 27,231 | 100 | 33.6, 42.0 |

**semantic chunk pairs**: of 20,000 chunks drawn at random, the chunks of other items at cosine 0.785 or more, per asking chunk, by the asking chunk's source (rows) and the answering chunk's (columns).

| asking | wikipedia | openalex | arxiv | stackexchange | gutenberg | hackernews |
|---|---|---|---|---|---|---|
| wikipedia | 6.29 | 1.49 | 0.37 | 0.50 | 0.61 | 0.06 |
| openalex | 2.38 | 8245.60 | 2263.34 | 184.60 | 0.02 | 4.26 |
| arxiv | 1.81 | 6784.89 | 2205.71 | 120.09 | 0.04 | 4.74 |
| stackexchange | 1.26 | 180.00 | 39.36 | 663.19 | 0.12 | 1.52 |
| gutenberg | 2.79 | 0.01 | 0.02 | 0.15 | 189.43 | 0.07 |
| hackernews | 0.18 | 6.21 | 2.64 | 1.90 | 0.15 | 17.96 |

### Shared rises

| reading | value |
|---|---|
| communities (sources) | 71 (6) |
| rho_w (95% band) | 0.116 (0.108, 0.120) |
| rho_b (95% band) | 0.091 (0.089, 0.093) |
| at lag 0: rho_w, rho_b | 0.066, 0.037 |
| the circular-shift null (band) | 0.094, 0.092 (0.091, 0.096) |
| N_eff at m = 11.8, and its limit | 9.30, 10.51 |

### Retrieval battery, lexical arm

| arm: family | n | unscoped 1% | 10% | 100% | fall (95% CI) | scoped 1% | 100% | fall (95% CI) | pending |
|---|---|---|---|---|---|---|---|---|---|
| lexical:cite:wikipedia->paper | 333 | 0.913 | 0.868 | 0.811 | 0.102 (0.072, 0.135) | 0.916 | 0.823 | 0.093 (0.063, 0.126) | 0 |
| lexical:link:hackernews->wikipedia | 210 | 0.276 | 0.238 | 0.143 | 0.133 (0.090, 0.181) | 0.329 | 0.195 | 0.133 (0.086, 0.181) | 0 |
| lexical:link:stackexchange->wikipedia | 333 | 0.532 | 0.399 | 0.186 | 0.345 (0.297, 0.399) | 0.631 | 0.559 | 0.072 (0.045, 0.102) | 0 |
| lexical:titles:arxiv | 500 | 1.000 | 1.000 | 0.990 | 0.010 (0.002, 0.020) | 1.000 | 0.998 | 0.002 (0.000, 0.006) | 0 |
| lexical:titles:gutenberg | 338 | 0.988 | 0.988 | 0.970 | 0.018 (0.006, 0.033) | 0.988 | 0.988 | 0.000 (0.000, 0.000) | 0 |
| lexical:titles:hackernews | 500 | 1.000 | 1.000 | 0.994 | 0.006 (0.000, 0.014) | 1.000 | 0.998 | 0.002 (0.000, 0.006) | 0 |
| lexical:titles:openalex | 500 | 0.978 | 0.972 | 0.952 | 0.026 (0.014, 0.040) | 0.980 | 0.958 | 0.022 (0.010, 0.036) | 0 |
| lexical:titles:stackexchange | 500 | 0.996 | 0.986 | 0.958 | 0.038 (0.022, 0.056) | 0.996 | 0.962 | 0.034 (0.020, 0.052) | 0 |
| lexical:titles:wikipedia | 500 | 1.000 | 0.998 | 0.970 | 0.030 (0.016, 0.046) | 1.000 | 0.984 | 0.016 (0.006, 0.028) | 0 |
| lexical:twins:arxiv->openalex | 500 | 0.996 | 0.996 | 0.996 | 0.000 (0.000, 0.000) | 0.998 | 0.996 | 0.002 (0.000, 0.006) | 0 |
| lexical:twins:openalex->arxiv | 500 | 0.992 | 0.992 | 0.992 | 0.000 (0.000, 0.000) | 0.992 | 0.992 | 0.000 (0.000, 0.000) | 0 |

*lexical, all (2838 questions, v(N) = 0.973)*: wikipedia Shapley 0.171, LOO 0.169 (p 0.000); openalex Shapley 0.208, LOO 0.138 (p 0.000); arxiv Shapley 0.133, LOO 0.063 (p 0.000); stackexchange Shapley 0.169, LOO 0.168 (p 0.000); gutenberg Shapley 0.116, LOO 0.115 (p 0.000); hackernews Shapley 0.175, LOO 0.175 (p 0.000)

*lexical, twinned (397 questions, v(N) = 0.987)*: wikipedia Shapley 0.000, LOO 0.000 (p 1.000); openalex Shapley 0.492, LOO -0.005 (p 1.000); arxiv Shapley 0.497, LOO 0.000 (p 1.000); stackexchange Shapley -0.001, LOO -0.003 (p 1.000); gutenberg Shapley 0.000, LOO 0.000 (p 1.000); hackernews Shapley 0.000, LOO 0.000 (p 1.000)

CIF-10 (lexical): held.

### Retrieval battery, three arms

| arm: family | n | unscoped 1% | 10% | 100% | fall (95% CI) | scoped 1% | 100% | fall (95% CI) | pending |
|---|---|---|---|---|---|---|---|---|---|
| both:cite:wikipedia->paper | 333 | 0.916 | 0.898 | 0.811 | 0.105 (0.072, 0.138) | 0.916 | 0.835 | 0.081 (0.054, 0.111) | 0 |
| both:link:hackernews->wikipedia | 210 | 0.286 | 0.248 | 0.181 | 0.105 (0.062, 0.152) | 0.410 | 0.248 | 0.162 (0.110, 0.214) | 0 |
| both:link:stackexchange->wikipedia | 333 | 0.547 | 0.396 | 0.165 | 0.381 (0.330, 0.432) | 0.721 | 0.670 | 0.051 (0.027, 0.078) | 0 |
| both:titles:arxiv | 500 | 1.000 | 0.998 | 0.978 | 0.022 (0.010, 0.036) | 1.000 | 0.990 | 0.010 (0.002, 0.020) | 0 |
| both:titles:gutenberg | 338 | 0.988 | 0.985 | 0.982 | 0.006 (0.000, 0.015) | 0.988 | 0.988 | 0.000 (0.000, 0.000) | 0 |
| both:titles:hackernews | 500 | 1.000 | 1.000 | 0.998 | 0.002 (0.000, 0.006) | 1.000 | 0.998 | 0.002 (0.000, 0.006) | 0 |
| both:titles:openalex | 500 | 0.998 | 0.986 | 0.954 | 0.044 (0.028, 0.064) | 0.998 | 0.962 | 0.036 (0.020, 0.054) | 0 |
| both:titles:stackexchange | 500 | 0.998 | 0.996 | 0.980 | 0.018 (0.006, 0.032) | 1.000 | 0.986 | 0.014 (0.006, 0.026) | 0 |
| both:titles:wikipedia | 500 | 1.000 | 0.998 | 0.994 | 0.006 (0.000, 0.014) | 1.000 | 1.000 | 0.000 (0.000, 0.000) | 0 |
| both:twins:arxiv->openalex | 500 | 0.996 | 0.996 | 0.996 | 0.000 (0.000, 0.000) | 0.998 | 0.996 | 0.002 (0.000, 0.006) | 0 |
| both:twins:openalex->arxiv | 500 | 0.992 | 0.992 | 0.990 | 0.002 (0.000, 0.006) | 0.994 | 0.990 | 0.004 (0.000, 0.010) | 0 |
| lexical:cite:wikipedia->paper | 333 | 0.913 | 0.868 | 0.811 | 0.102 (0.072, 0.135) | 0.916 | 0.823 | 0.093 (0.063, 0.123) | 0 |
| lexical:link:hackernews->wikipedia | 210 | 0.276 | 0.238 | 0.143 | 0.133 (0.090, 0.186) | 0.329 | 0.195 | 0.133 (0.090, 0.176) | 0 |
| lexical:link:stackexchange->wikipedia | 333 | 0.532 | 0.399 | 0.186 | 0.345 (0.297, 0.396) | 0.631 | 0.559 | 0.072 (0.045, 0.099) | 0 |
| lexical:titles:arxiv | 500 | 1.000 | 1.000 | 0.990 | 0.010 (0.002, 0.020) | 1.000 | 0.998 | 0.002 (0.000, 0.006) | 0 |
| lexical:titles:gutenberg | 338 | 0.988 | 0.988 | 0.970 | 0.018 (0.006, 0.033) | 0.988 | 0.988 | 0.000 (0.000, 0.000) | 0 |
| lexical:titles:hackernews | 500 | 1.000 | 1.000 | 0.994 | 0.006 (0.000, 0.014) | 1.000 | 0.998 | 0.002 (0.000, 0.006) | 0 |
| lexical:titles:openalex | 500 | 0.978 | 0.972 | 0.952 | 0.026 (0.012, 0.042) | 0.980 | 0.958 | 0.022 (0.010, 0.036) | 0 |
| lexical:titles:stackexchange | 500 | 0.996 | 0.986 | 0.958 | 0.038 (0.022, 0.056) | 0.996 | 0.962 | 0.034 (0.020, 0.050) | 0 |
| lexical:titles:wikipedia | 500 | 1.000 | 0.998 | 0.970 | 0.030 (0.016, 0.046) | 1.000 | 0.984 | 0.016 (0.006, 0.028) | 0 |
| lexical:twins:arxiv->openalex | 500 | 0.996 | 0.996 | 0.996 | 0.000 (0.000, 0.000) | 0.998 | 0.996 | 0.002 (0.000, 0.006) | 0 |
| lexical:twins:openalex->arxiv | 500 | 0.992 | 0.992 | 0.992 | 0.000 (0.000, 0.000) | 0.992 | 0.992 | 0.000 (0.000, 0.000) | 0 |
| semantic:cite:wikipedia->paper | 333 | 0.874 | 0.796 | 0.625 | 0.249 (0.204, 0.297) | 0.865 | 0.637 | 0.228 (0.186, 0.273) | 0 |
| semantic:link:hackernews->wikipedia | 210 | 0.248 | 0.210 | 0.176 | 0.071 (0.038, 0.110) | 0.400 | 0.229 | 0.171 (0.124, 0.224) | 0 |
| semantic:link:stackexchange->wikipedia | 333 | 0.366 | 0.210 | 0.063 | 0.303 (0.255, 0.354) | 0.739 | 0.661 | 0.078 (0.051, 0.108) | 0 |
| semantic:titles:arxiv | 500 | 0.984 | 0.964 | 0.860 | 0.124 (0.094, 0.154) | 0.988 | 0.920 | 0.068 (0.046, 0.090) | 0 |
| semantic:titles:gutenberg | 338 | 0.973 | 0.964 | 0.941 | 0.033 (0.015, 0.053) | 0.979 | 0.979 | 0.000 (0.000, 0.000) | 0 |
| semantic:titles:hackernews | 500 | 0.998 | 0.996 | 0.990 | 0.008 (0.002, 0.018) | 1.000 | 0.990 | 0.010 (0.002, 0.020) | 0 |
| semantic:titles:openalex | 500 | 0.968 | 0.940 | 0.866 | 0.102 (0.076, 0.130) | 0.972 | 0.870 | 0.102 (0.076, 0.130) | 0 |
| semantic:titles:stackexchange | 500 | 0.996 | 0.986 | 0.954 | 0.042 (0.024, 0.062) | 1.000 | 0.974 | 0.026 (0.014, 0.040) | 0 |
| semantic:titles:wikipedia | 500 | 0.994 | 0.990 | 0.952 | 0.042 (0.026, 0.060) | 1.000 | 1.000 | 0.000 (0.000, 0.000) | 0 |
| semantic:twins:arxiv->openalex | 500 | 0.998 | 0.996 | 0.996 | 0.002 (0.000, 0.006) | 0.998 | 0.996 | 0.002 (0.000, 0.006) | 0 |
| semantic:twins:openalex->arxiv | 500 | 0.990 | 0.990 | 0.988 | 0.002 (0.000, 0.006) | 0.992 | 0.988 | 0.004 (0.000, 0.010) | 0 |

*lexical, all (2838 questions, v(N) = 0.973)*: wikipedia Shapley 0.171, LOO 0.169 (p 0.000); openalex Shapley 0.208, LOO 0.138 (p 0.000); arxiv Shapley 0.133, LOO 0.063 (p 0.000); stackexchange Shapley 0.169, LOO 0.168 (p 0.000); gutenberg Shapley 0.116, LOO 0.115 (p 0.000); hackernews Shapley 0.175, LOO 0.175 (p 0.000)

*lexical, twinned (397 questions, v(N) = 0.987)*: wikipedia Shapley 0.000, LOO 0.000 (p 1.000); openalex Shapley 0.492, LOO -0.005 (p 1.000); arxiv Shapley 0.497, LOO 0.000 (p 1.000); stackexchange Shapley -0.001, LOO -0.003 (p 1.000); gutenberg Shapley 0.000, LOO 0.000 (p 1.000); hackernews Shapley 0.000, LOO 0.000 (p 1.000)

CIF-10 (lexical): held.

*semantic, all (2838 questions, v(N) = 0.927)*: wikipedia Shapley 0.172, LOO 0.167 (p 0.000); openalex Shapley 0.178, LOO 0.111 (p 0.000); arxiv Shapley 0.121, LOO 0.057 (p 0.000); stackexchange Shapley 0.169, LOO 0.168 (p 0.000); gutenberg Shapley 0.114, LOO 0.112 (p 0.000); hackernews Shapley 0.173, LOO 0.172 (p 0.000)

*semantic, twinned (397 questions, v(N) = 0.849)*: wikipedia Shapley 0.000, LOO 0.000 (p 1.000); openalex Shapley 0.398, LOO -0.048 (p 0.003); arxiv Shapley 0.451, LOO 0.005 (p 1.000); stackexchange Shapley 0.000, LOO 0.000 (p 1.000); gutenberg Shapley 0.000, LOO 0.000 (p 1.000); hackernews Shapley 0.000, LOO 0.000 (p 1.000)

CIF-10 (semantic): held.

*both, all (2838 questions, v(N) = 0.982)*: wikipedia Shapley 0.176, LOO 0.175 (p 0.000); openalex Shapley 0.207, LOO 0.138 (p 0.000); arxiv Shapley 0.132, LOO 0.063 (p 0.000); stackexchange Shapley 0.173, LOO 0.173 (p 0.000); gutenberg Shapley 0.117, LOO 0.117 (p 0.000); hackernews Shapley 0.176, LOO 0.175 (p 0.000)

*both, twinned (397 questions, v(N) = 0.975)*: wikipedia Shapley 0.000, LOO 0.000 (p 1.000); openalex Shapley 0.480, LOO -0.008 (p 1.000); arxiv Shapley 0.493, LOO 0.005 (p 1.000); stackexchange Shapley 0.002, LOO 0.005 (p 1.000); gutenberg Shapley 0.000, LOO 0.000 (p 1.000); hackernews Shapley 0.000, LOO 0.000 (p 1.000)

CIF-10 (both): held.

| family | lexical | semantic | both | LOO of the embedder | Shapley of the embedder |
|---|---|---|---|---|---|
| cite:wikipedia->paper | 0.811 | 0.625 | 0.811 | 0.000 | 0.312 |
| link:hackernews->wikipedia | 0.143 | 0.176 | 0.181 | 0.038 | 0.107 |
| link:stackexchange->wikipedia | 0.186 | 0.063 | 0.165 | -0.021 | 0.021 |
| titles:arxiv | 0.990 | 0.860 | 0.978 | -0.012 | 0.424 |
| titles:gutenberg | 0.970 | 0.941 | 0.982 | 0.012 | 0.476 |
| titles:hackernews | 0.994 | 0.990 | 0.998 | 0.004 | 0.497 |
| titles:openalex | 0.952 | 0.866 | 0.954 | 0.002 | 0.434 |
| titles:stackexchange | 0.958 | 0.954 | 0.980 | 0.022 | 0.488 |
| titles:wikipedia | 0.970 | 0.952 | 0.994 | 0.024 | 0.488 |
| twins:arxiv->openalex | 0.996 | 0.996 | 0.996 | 0.000 | 0.498 |
| twins:openalex->arxiv | 0.992 | 0.988 | 0.990 | -0.002 | 0.493 |

### Cost against N

| lexical units | median query (ms) | matrix bytes |
|---|---|---|
| 13,699 | 0.208 | 13,130,520 |
| 41,098 | 0.554 | 32,079,080 |
| 136,994 | 1.645 | 98,092,256 |
| 410,983 | 5.065 | 286,934,048 |
| 1,369,944 | 16.389 | 946,879,224 |

| sentence | items | chunks | wall (s) | peak RSS (MB) | Python share | note |
|---|---|---|---|---|---|---|
| `reach S from` | 1,000 | 3,923 | 1.55 | 680 | 0.57 |  |
| `top 10 diffuse S from` | 1,000 | 3,923 | 1.55 | 713 | 0.55 |  |
| `top 10 near` | 1,000 | 3,923 | 1.59 | 679 | 0.54 |  |
| `walk from` | 1,000 | 3,923 | 1.54 | 673 | 0.59 |  |
| `reach S from` | 3,000 | 10,106 | 2.17 | 1,158 | 0.59 |  |
| `top 10 diffuse S from` | 3,000 | 10,106 | 2.31 | 1,554 | 0.56 |  |
| `top 10 near` | 3,000 | 10,106 | 2.14 | 1,123 | 0.57 |  |
| `walk from` | 3,000 | 10,106 | 2.08 | 1,159 | 0.59 |  |
| `reach S from` | 10,000 | 34,917 | 5.92 | 4,699 | 0.64 |  |
| `top 10 diffuse S from` | 10,000 | 34,917 | n/a | n/a | n/a | rss above 6.0 GB |
| `top 10 near` | 10,000 | 34,917 | 5.20 | 4,283 | 0.58 |  |
| `walk from` | 10,000 | 34,917 | 6.08 | 4,695 | 0.65 |  |

### Codes for stage 2

1,338,585 atoms of 768 dimensions; the preview is recall at 10 against exact float16 search on 500 title queries, flat and rescored exactly from each code's top 40.

| code | bytes a vector | flat | rescored |
|---|---|---|---|
| int8_768 | 768.0 | 0.990 | 1.000 |
| f16_256 | 512.0 | 0.745 | 0.977 |
| int8_256 | 256.0 | 0.744 | 0.976 |
| bits_768 | 96.0 | 0.514 | 0.788 |

### The BEIR control

| set | documents | queries | nDCG at 10 | recall at 10 | recall at 10 among the corpus's atoms |
|---|---|---|---|---|---|
| scifact | 5,183 | 300 | 0.848 | 0.932 | 0.877 |
| nfcorpus | 3,633 | 323 | 0.355 | 0.174 | 0.108 |

### Footprint

| store | bytes on disk |
|---|---|
| instance | 12,203,798,528 |
| sources_dumps_and_streams | 3,997,171,712 |
| raw_store | 2,189,189,120 |
| vectors_lance | 3,400,683,520 |
| plane_sqlite | 1,006,698,496 |
| catalog | 167,837,696 |
| attestations | 318,832,640 |
| edges | 30,330,880 |
| codes | 0 |

Plane occupancy (live shape): 733.6 B; compact item-grain row: 19.4 B; largest columnar edge: 12.07 B.



## The vector phase

The vector phase derived every landed item's plane rows from the raw store: 1,338,585 atoms embedded in 11.4 hours of the runner's time, 32.7 a second, with four requests of 32 texts in flight and 0 pauses for the chat model, over 4 runs (the first 92,385 items landed with their vectors, then backfills before and after Hacker News landed). One Hacker News chunk tokenized to 2,951 tokens, past the embedder's physical batch of 2,048: the server refuses such an input instead of truncating it, since a chunk's budget of 1,200 characters does not bound its tokens for symbols or another script, so the runner now sends a refused batch's texts one at a time and cuts a text that alone does not fit to the longest prefix the server takes (1 cut). Until an item's rows landed, a query that needed its vector reported it pending; at the battery's run 0 questions were pending. The battery's semantic and fused arms are in the three-arm battery below and the embedder's attribution as a source in the attribution paragraph above.

With each item's ten nearest items above sigma = 0.785 added to the item graph (3,073,202 semantic edges, 642,433 of them across sources), 3,014 community pairs stand above the null against a bar of 806.9; without the twins and the 27,295 twin pairs among the semantic edges, 3,014 against 791.9. Of 20,000 chunks drawn at random, the chunks of other items at cosine 0.785 or more number, per chunk, 9 for Wikipedia, 29 for Hacker News, 192 for Gutenberg, 885 for Stack Exchange, 9,117 for arXiv, 10,700 for OpenAlex: the live store's threshold, set on its own notes, does not carry across sources, and a semantic edge means a different thing in each.

On the embedder bench's public sets SciFact scores nDCG@10 0.848 (the bench measured 0.849) and recall@10 0.932, 0.877 when the corpus's atoms compete with the set's documents; NFCorpus scores nDCG@10 0.355 (the bench measured 0.367) and recall@10 0.174, 0.108 when the corpus's atoms compete with the set's documents.

(the codes' table is in the results above)

The plane as built holds 734 B per occupancy (its live shape, with text keys and the fiber's columns); the design's compact row, one integer row an item version, measures 19.4 B against its 120 B target and the falsifier's 300 B.

## Falsifiers

| id | what would falsify (dn-corpus-instance) | stage 1 |
|---|---|---|
| CIF-1 | Hacker News threads chunk above 2,000 chunks per MB | held (1,402 chunks per MB) |
| CIF-2 | bridges at or below the null; or rho_b inside rho_w's band | held: explicit bridges above the null (106 community pairs against a false-positive bar of 40.9); without the twins, 37 against 39.3 in all, while arxiv-stackexchange (22 against 0.0), hackernews-wikipedia (10 against 0.0), arxiv-wikipedia (5 against 1.4) stand above their own pair's false positives; with the semantic edges 3014 against 806.9; rho_b 0.091 below rho_w's band (0.108, 0.120), at the shift null's 0.092 |
| CIF-4 | a compact occupancy row above 300 B, or an edge above 24 B | edges held (12.1 B per edge); occupancy rows held (19.4 B a compact row) |
| CIF-5 | a write outside the instance, or a read of the default instance's sources | held (the isolation proof: no shared namespace, by real path, with a control) |
| CIF-6 | a batch interrupted and re-run lands a different state | held (four cut points tested; two real kills mid-batch, one attestation a digest) |
| CIF-7 | a 6-core or 10-core gap width that never falls under 10% by N = 10^5 | held for citations (6-core 51,262, 10-core 28,912) and hyperlinks (8,500); no core in answers, replies, versions or post links |
| CIF-8 | the harmonic fraction still moving where gamma has settled | held for citations (harmonic 9,788, gamma 27,850); broken by a hair for hyperlinks (harmonic width 0.103 at the last cut, 7,509 nodes) |
| CIF-9 | unscoped recall flat in N; or scoped recall falling with the source's own N | lexical: unscoped recall falls in 8 of 11 families (first clause held); scoped recall falls with the source's own growth in 6 (second clause broken: Hacker News links, Wikipedia citations, Stack Exchange links, Stack Exchange titles, OpenAlex titles, Wikipedia titles); semantic: unscoped recall falls in 9 of 11 families (first clause held); scoped recall falls with the source's own growth in 7 (second clause broken: Wikipedia citations, Hacker News links, OpenAlex titles, Stack Exchange links, arXiv titles, Stack Exchange titles, Hacker News titles); fused: unscoped recall falls in 6 of 11 families (first clause held); scoped recall falls with the source's own growth in 6 (second clause broken: Hacker News links, Wikipedia citations, Stack Exchange links, OpenAlex titles, Stack Exchange titles, arXiv titles) |
| CIF-10 | leave-one-out at the bar for both twins | lexical: held (Shapley 0.49 and 0.50, leave-one-out -0.01 and 0.00); semantic: held (Shapley 0.40 and 0.45, leave-one-out -0.05 and 0.01); fused: held (Shapley 0.48 and 0.49, leave-one-out -0.01 and 0.01) |
| CIF-11 | a Python share above 20% on a sentence | broken (Python share 54 to 65% at 1,000 to 10,000 items, waits excluded) |

## Deviations from the brief

- OpenAlex is 171 MB, not 240: the keyless API's daily budget (above).
- Attribution is read on the retrieval battery's value, not on the ledger's generators. The
  design's attribution row names the ledger's link, version and confirmation generators, whose
  value is a configuration's log-score advantage on forecasts it makes at a cut; the generators,
  their resolvers and the forecasting arms are not built in the repository, and a forecasting
  arm per configuration needs a protocol written before its first prediction. Here `v(S)` is the
  share of a family's questions answered (the answer or its twin in the first ten) with only the
  sources in `S` present, the same arms (the full set, each source left out, and every subset for
  the exact Shapley value over six players), and the same redundancy witness (the OpenAlex and
  arXiv twins).
- arXiv came through arXiv's query API, not OAI-PMH: on 2026-11-07 the OAI-PMH endpoint
  (`export.arxiv.org/oai2`, which redirects to `oaipmh.arxiv.org/oai`) answered neither a
  category set nor a one-day datestamp window inside its gateway's three-minute first-byte limit
  (503 each time, five attempts over an hour). The API is arXiv's own, under the same metadata
  terms (CC0) and the same three-second interval; it gives a record's first and latest versions,
  not the dates between, so the version chains have two dated ends. The OAI-PMH reader is kept
  (`edge/corpus/arxiv.py --oai`).
- Wikipedia links resolve by exact title, so a link through a redirect is not an edge; page
  creation is interpolated from page ids through 160 first-revision anchors.
- The Hodge split of a dense graph is measured on a node subsample (60,000 edges at most), and
  the bootstrap of a cut above 40,000 nodes (100,000 for a core) is not run; each table says
  where these bounds apply.

## Disk

Free space before the run 116 GiB, after it 99 GiB; the instance holds 14 GB: the readers' dumps, pages and streams 3.7 GB, the raw store 2.0 GB, the plane 4.1 GB with its index 1.0 GB, the codes for stage 2 2.1 GB, the lexical index 0.9 GB, the results 0.2 GB. The floor of 25 GB free was never approached.

## Reproduce

    MIND_PALACE_OVERLAY=config/instances/corpus.toml uv run python scripts/corpus.py isolation --live <checkout>
    ... scripts/corpus.py fetch <source> [--budget-mb N]          # each of the six
    ... scripts/corpus.py ingest --structural                     # phase 1: keys, raw, attestations
    ... scripts/corpus.py lexical                                 # the BM25 index
    ... uv run python -m eval.corpus.stage1 edges | macro | rises | bridges --explicit-only | arms --lexical-only | lexcost
    ... scripts/corpus.py embed --streams 4 --embed-batch 32      # phase 2: the vectors
    ... uv run python -m eval.corpus.stage1 bridges | arms | battery --codes --beir | footprint
    ... uv run python -m eval.corpus.cost probe --scratch 1000 3000 10000
    ... uv run python -m eval.corpus.report                        # the tables

The results are JSON under `instances/corpus/results/`; the numbers in this report are in
`docs/experiments/corpus-stage1-2026-11-07.json`.
