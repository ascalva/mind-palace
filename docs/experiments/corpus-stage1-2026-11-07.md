---
type: experiment-report
experiment: corpus-stage1
run: 1
status: structure complete; vectors landing
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
- Five edge readers (`edge/corpus/`), the runner and its embedder policy (`scripts/corpus.py`,
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
| OpenAlex | works with abstracts, topics T10064, T10720, T11273, T12592 and part of T11252 | keyless API, date slices, basic paging | 145,029 | 171.3 | 3.28 | 266,149 | 1,554 |
| arXiv | records of physics.soc-ph, cs.SI, nlin.AO, and the arXiv records of the OpenAlex works that name one | arXiv's query API, 3 s apart | 41,659 | 50.9 | 3.16 | 81,889 | 1,609 |
| Stack Exchange | cstheory and cs whole, datascience to the budget, from the 2024-04-02 dump | archive.org, bsdtar | 163,503 | 170.2 | 2.97 | 239,270 | 1,406 |
| Project Gutenberg | 338 English science texts by Library of Congress class | catalogue, then gutenberg.pglaf.org, 2 s apart | 338 | 108.1 | 3.03 | 125,379 | 1,159 |
| **total** | | | **361,943** | **898.5** | **2.99** | **1,201,686** | **1,337** |

D-2 was decided during the run: Hacker News is included through its official API, held
locally and never republished, so the mix is the design's own rescaled into 1 GB: Wikipedia 35%,
OpenAlex 24%, Stack Exchange 15%, Hacker News 12%, Gutenberg 9.5%, arXiv 4.5%. Wikipedia, Stack
Exchange, Gutenberg and arXiv reached or passed their share (they were sized before the decision,
on the proportions without Hacker News). OpenAlex stopped at 171 of its 240 MB when the keyless
API's daily budget (0.10 USD, a thousand requests, shared by the IP address) was spent; its
remainder needs the next day's budget or an API key, which is an account (D-5). Hacker News is
being fetched (120 MB of threads) and lands in the structural phase when its reader finishes.

## Results: structure

These need no vector and ran as soon as the structural phase landed every item.

### Macro quantities

**arxiv.version**: 16,620 edges, 33,240 nodes in 16,620 components, the largest 2 nodes: no component reaches the ladder's first rung (300), so no macro quantity is defined.

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

**explicit**: 1,941,876 edges, 30,428 across sources (share 0.016, the null's 0.531); 99 community pairs over the null against a false-positive bar of 46.5; CIF-2 (bridges) held.

| source pair | edges | bridges |
|---|---|---|
| arxiv-openalex | 27,397 | 88 |
| arxiv-stackexchange | 463 | 11 |
| arxiv-wikipedia | 195 | 0 |
| gutenberg-wikipedia | 1 | 0 |
| openalex-stackexchange | 295 | 0 |
| openalex-wikipedia | 287 | 0 |
| stackexchange-wikipedia | 1,790 | 0 |

### Shared rises

| reading | value |
|---|---|
| communities (sources) | 53 (5) |
| rho_w (95% band) | 0.122 (0.111, 0.127) |
| rho_b (95% band) | 0.092 (0.089, 0.096) |
| at lag 0: rho_w, rho_b | 0.070, 0.040 |
| the circular-shift null (band) | 0.094, 0.092 (0.091, 0.096) |
| N_eff at m = 10.6, and its limit | 8.71, 10.17 |

### Retrieval battery, lexical arm

| arm: family | n | unscoped 1% | 10% | 100% | fall (95% CI) | scoped 1% | 100% | fall (95% CI) | pending |
|---|---|---|---|---|---|---|---|---|---|
| lexical:cite:wikipedia->paper | 333 | 0.913 | 0.868 | 0.811 | 0.102 (0.072, 0.135) | 0.919 | 0.823 | 0.096 (0.066, 0.129) | 0 |
| lexical:link:stackexchange->wikipedia | 333 | 0.544 | 0.396 | 0.183 | 0.360 (0.309, 0.411) | 0.655 | 0.547 | 0.108 (0.075, 0.144) | 0 |
| lexical:titles:arxiv | 500 | 1.000 | 1.000 | 0.990 | 0.010 (0.002, 0.020) | 1.000 | 0.998 | 0.002 (0.000, 0.006) | 0 |
| lexical:titles:gutenberg | 338 | 0.988 | 0.985 | 0.970 | 0.018 (0.006, 0.033) | 0.988 | 0.988 | 0.000 (0.000, 0.000) | 0 |
| lexical:titles:openalex | 500 | 0.978 | 0.972 | 0.952 | 0.026 (0.014, 0.040) | 0.980 | 0.958 | 0.022 (0.010, 0.036) | 0 |
| lexical:titles:stackexchange | 500 | 0.996 | 0.986 | 0.954 | 0.042 (0.026, 0.060) | 0.996 | 0.960 | 0.036 (0.022, 0.054) | 0 |
| lexical:titles:wikipedia | 500 | 1.000 | 1.000 | 0.972 | 0.028 (0.014, 0.044) | 1.000 | 0.984 | 0.016 (0.006, 0.028) | 0 |
| lexical:twins:arxiv->openalex | 500 | 0.992 | 0.992 | 0.988 | 0.004 (0.000, 0.010) | 0.992 | 0.992 | 0.000 (0.000, 0.000) | 0 |
| lexical:twins:openalex->arxiv | 500 | 0.994 | 0.992 | 0.992 | 0.002 (0.000, 0.006) | 0.994 | 0.992 | 0.002 (0.000, 0.006) | 0 |

*lexical, all (2338 questions, v(N) = 0.967)*: wikipedia Shapley 0.208, LOO 0.206 (p 0.000); openalex Shapley 0.252, LOO 0.167 (p 0.000); arxiv Shapley 0.161, LOO 0.077 (p 0.000); stackexchange Shapley 0.204, LOO 0.203 (p 0.000); gutenberg Shapley 0.141, LOO 0.140 (p 0.000)

*lexical, twinned (397 questions, v(N) = 0.987)*: wikipedia Shapley 0.000, LOO 0.000 (p 1.000); openalex Shapley 0.492, LOO -0.005 (p 1.000); arxiv Shapley 0.497, LOO 0.000 (p 1.000); stackexchange Shapley -0.001, LOO -0.003 (p 1.000); gutenberg Shapley 0.000, LOO 0.000 (p 1.000)

CIF-10 (lexical): held.

### Cost against N

| lexical units | median query (ms) | matrix bytes |
|---|---|---|
| 12,017 | 0.191 | 11,451,156 |
| 36,051 | 0.483 | 27,731,124 |
| 120,169 | 1.5 | 84,322,372 |
| 360,506 | 4.359 | 246,831,524 |
| 1,201,686 | 14.193 | 814,863,324 |

| sentence | items | chunks | wall (s) | peak RSS (MB) | Python share | note |
|---|---|---|---|---|---|---|
| `top 10 near` | 12,897 | 34,428 | 7.46 | 5,661 | 0.78 |  |
| `top 10 diffuse S from` | 12,897 | 34,428 | n/a | n/a | n/a | rss above 6.0 GB |
| `reach S from` | 12,897 | 34,428 | n/a | n/a | n/a | rss above 6.0 GB |
| `top 10 near` | 1,000 | 3,012 | 2.77 | 333 | 0.96 |  |
| `top 10 diffuse S from` | 1,000 | 3,012 | 0.29 | 382 | 0.52 |  |
| `reach S from` | 1,000 | 3,012 | 0.26 | 333 | 0.56 |  |
| `top 10 near` | 3,000 | 7,620 | 2.72 | 724 | 0.90 |  |
| `top 10 diffuse S from` | 3,000 | 7,620 | 1.12 | 1,267 | 0.45 |  |
| `reach S from` | 3,000 | 7,620 | 0.77 | 781 | 0.68 |  |
| `top 10 near` | 10,000 | 25,316 | 6.84 | 3,683 | 0.82 |  |
| `top 10 diffuse S from` | 10,000 | 25,316 | n/a | n/a | n/a | rss above 6.0 GB |
| `reach S from` | 10,000 | 25,316 | 4.75 | 4,477 | 0.77 |  |



## Results: vectors

The vector phase (`scripts/corpus.py embed --streams 4 --embed-batch 32`) derives each landed item's plane rows from the raw store at about 35 chunks a second, pausing while the chat model serves. It is in progress. Until an item's rows land, a query that needs its vector reports it pending: the battery's semantic arm counts such questions apart, and a sentence over the observed stratum says how many landed items it could not rank (`core/sentence/universe.py`). When the phase completes this section gives the battery three ways (lexical, semantic, both by reciprocal rank fusion), the embedder's attribution as a source, the semantic bridges, the BEIR control, the codes written for stage 2 with their preview, the plane's bytes per occupancy and the sentences' cost with the embedder idle.

## Falsifiers

| id | what would falsify (dn-corpus-instance) | stage 1 |
|---|---|---|
| CIF-1 | Hacker News threads chunk above 2,000 chunks per MB | pending: Hacker News is being fetched (D-2 decided during the run) |
| CIF-2 | bridges at or below the rewiring null; or rho_b inside the band of rho_w | held so far: 99 explicit community-pair bridges against a false-positive bar of 46.5; rho_b 0.092 below rho_w's band (0.111, 0.127), and at the circular-shift null's level (0.092); semantic bridges pending |
| CIF-4 | a compact occupancy row above 300 B, or an edge above 24 B | edges held (12.0 B per edge on every relation of more than a thousand edges); occupancy pending the plane's completion |
| CIF-5 | a write outside `instances/corpus/`, or a read of the default instance's sources | held: the isolation proof above; every reader, the runner and the harness write under the instance's root |
| CIF-6 | a batch interrupted and re-run lands a different state | held: tested at four cut points against an uninterrupted landing; in the run, two kills mid-batch and resumption left one attestation per digest (349,795 for 349,795 digests) and no key without one |
| CIF-7 | a 6-core or 10-core gap width that never falls under 10% by N = 10^5 | held for citations (6-core 51,262, 10-core 28,912) and hyperlinks (5,703, 9,697); answers, versions and post links have no 6-core, so the falsifier has nothing to read there |
| CIF-8 | a harmonic fraction still moving where gamma has settled | held for citations (harmonic width under 10% from 9,788, gamma from 27,850); broken by a hair for hyperlinks (harmonic fraction 0.018, its width 0.103 on a 7,509-node subsample, where gamma has settled at 8,502) |
| CIF-9 | unscoped recall flat in N; or scoped recall falling with the source's own N | lexical arm: the first clause held (unscoped recall falls in 7 of 9 families, by up to 0.36); the second broken for the citation, Stack Exchange, OpenAlex and Wikipedia title families (scoped recall falls by 0.02 to 0.10 with the source's own growth); semantic arm pending |
| CIF-10 | leave-one-out at the bar for both twins | lexical arm: held (Shapley 0.49 and 0.50, leave-one-out 0.00 and -0.01, Holm p = 1); semantic arm pending |
| CIF-11 | a Python share above 20% on any sentence | broken: 52 to 96% on `near`, `diffuse` and `reach` over the observed stratum at 1,000 to 10,000 items (preliminary: the embedder was busy; the final probe excludes its wait) |

## Deviations from the brief

- OpenAlex is 171 MB, not 273: the keyless API's daily budget (above).
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

Free space before the run 116 GiB, now 108 GiB; the instance holds 7.9 GB so far (the dumps and pages the readers keep, the streams, the raw store, the lexical index, the plane in progress). The final footprint follows the vector phase.

## Reproduce

    MIND_PALACE_OVERLAY=config/instances/corpus.toml uv run python scripts/corpus.py isolation --live <checkout>
    ... scripts/corpus.py fetch <source> [--budget-mb N]          # each of the five
    ... scripts/corpus.py ingest --structural                     # phase 1: keys, raw, attestations
    ... scripts/corpus.py lexical                                 # the BM25 index
    ... uv run python -m eval.corpus.stage1 edges | macro | rises | bridges --explicit-only | arms --lexical-only | lexcost
    ... scripts/corpus.py embed --streams 4 --embed-batch 32      # phase 2: the vectors
    ... uv run python -m eval.corpus.stage1 bridges | arms | battery --codes --beir | footprint
    ... uv run python -m eval.corpus.cost probe --scratch 1000 3000 10000
    ... uv run python -m eval.corpus.report                        # the tables

The results are JSON under `instances/corpus/results/`; the numbers in this report are in
`docs/experiments/corpus-stage1-2026-11-07.json`.
