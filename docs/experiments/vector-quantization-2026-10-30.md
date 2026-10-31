---
type: experiment-report
experiment: vector-quantization
run: 1
status: complete
started: 2026-10-30
links:
  - eval/quantization_bench.py                           # the harness (this run's exact code)
  - docs/experiments/vector-quantization-2026-10-30.json # raw results: numbers only, no text
  - tests/unit/test_quantization_bench.py                # the instruments, pinned
  - docs/brainstorms/shared-vectors.md                   # the build plan; this is its step C
---

# Vector compression — run 1 (2026-10-30)

**Question.** Step C of the shared-vectors build plan: "int8, binary with float rescoring, IVF-PQ
and Matryoshka 256, each measured as recall@10 against float32 on the palace's own queries." The
vectors are most of the palace's bytes — 452.9 MB for the 147,417 paper atoms and 53.0 MB for the
17,256 code rows, float32 at 768 dimensions — so which lever, if any, keeps today's answers? One
measure throughout: of the ten results a query gets today (exact cosine over float32, which is what
`VectorStore.search` returns), the share it still gets. That is fidelity to today's answers, not
their relevance: whether today's answers are good is the embedder bench's question.

**Method.** `eval/quantization_bench.py`, read-only on the live stores, the stack up and the chat
model asleep.

- *Corpora.* Papers: every current atom once — the shared plane's unit, so a passage two papers
  share is one vector — read through `CURATED_READ`. Code: the physical rows a code search sees
  (`provenance = 'code' AND current`), through `CODE_READ`. Every vector is unit length.
- *Queries,* each family reported apart. **real**: every `palace_search` the Ambassador has issued
  — two by 2026-10-30, from OpenCode and Open WebUI, extracted read-only. **titles**: the 727 paper
  titles, the shape of a topical search. **owner**: the owner's 47 notes and turns (`MIRROR_READ`),
  asked of the papers. **self**: 500 stored vectors as queries with their own atom excluded — the
  palace's internal neighbour searches; 200 of them in the LanceDB sweep. **probes**: the 15 golden
  code probes. Query vectors come from the live embedder's own query path
  (`task: search result | query: …`).
- *Two engines.* numpy, flat over every vector: what each code throws away, with no index error
  mixed in. LanceDB 0.33.0 on a scratch copy: what production could serve — a float16 column, and
  IVF indexes over 384 partitions (√N; 131 for code).
- *Controls.* float32 against itself: 1.000 (the harness). LanceDB flat against numpy: 1.000 in
  every family (the ground truth is the engine's own answer). IVF_FLAT separates partition error
  from quantization error. For Matryoshka: the first 256 dimensions against the last 256, a random
  256-coordinate subset and a random orthonormal projection, with each 256-block's share of the
  variance.
- *Statistics.* Mean recall@10 with a bootstrap 95% interval (2,000 resamples, families of 20 or
  more queries), the share of queries that lose nothing, the worst query, and whether the first hit
  survives. The arithmetic is pinned by `tests/unit/test_quantization_bench.py`.

## Papers — numpy, flat: what each code keeps

| Scheme | Bytes/vector | MB | titles (727) | owner (47) | self (500) | real (2) |
|---|---:|---:|---|---|---|---:|
| float32 (control) | 3,072 | 452.9 | 1.000 | 1.000 | 1.000 | 1.00 |
| **float16** | 1,536 | 226.4 | **0.999** [0.998–0.999] | **1.000** | **0.999** [0.998–1.000] | 1.00 |
| **int8** | 768 | 113.2 | **0.993** [0.991–0.995] | **0.989** [0.981–0.998] | **0.991** [0.988–0.993] | 1.00 |
| int8 → rescore ×2 | 768 | 113.2 | 1.000 | 1.000 | 1.000 | 1.00 |
| binary (sign bits) | 96 | 14.2 | 0.599 [0.585–0.612] | 0.168 [0.128–0.215] | 0.468 [0.452–0.484] | 0.20 |
| binary → rescore ×4 | 96 | 14.2 | 0.826 | 0.319 | 0.728 | 0.45 |
| binary → rescore ×32 | 96 | 14.2 | 0.958 [0.951–0.964] | 0.625 [0.560–0.692] | 0.939 [0.931–0.947] | 0.85 |
| binary, centred → rescore ×16 | 96 | 14.2 | 0.962 | 0.619 | 0.950 | 0.85 |
| Matryoshka 512 | 2,048 | 301.9 | 0.886 [0.880–0.892] | 0.702 [0.662–0.738] | 0.859 | 0.75 |
| **Matryoshka 256** | 1,024 | 151.0 | **0.757** [0.746–0.768] | **0.462** [0.408–0.513] | **0.689** [0.676–0.703] | 0.45 |
| Matryoshka 256 → rescore ×4 | 1,024 | 151.0 | 0.964 | 0.779 [0.730–0.826] | 0.947 | 0.80 |
| Matryoshka 128 | 512 | 75.5 | 0.504 | 0.126 | 0.434 | 0.10 |
| last 256 dimensions (control) | 1,024 | 151.0 | 0.675 | 0.264 | 0.584 | 0.45 |
| random 256 coordinates (control) | 1,024 | 151.0 | 0.666 | 0.221 | 0.590 | 0.30 |
| random projection 256 (control) | 1,024 | 151.0 | 0.655 | 0.262 | 0.580 | 0.20 |

Share of the corpus variance by 256-dimension block: **0.462 · 0.296 · 0.242** (0.333 each if
spread evenly). A rescored scheme keeps its short code resident but reads 10·N float32 vectors per
query from disk, so the float32 column stays.

## Papers — LanceDB 0.33.0: what production could serve

| Configuration | Bytes/vector | p50 ms | titles | owner | self (200) | real |
|---|---:|---:|---|---|---|---:|
| flat float32 (today) | 3,072 (453.9 MB on disk) | 32.4 | 1.000 | 1.000 | 1.000 | 1.00 |
| **flat float16** | **1,536 (227.5 MB on disk)** | **19.7** | **1.000** [0.999–1.000] | **1.000** | **1.000** | 1.00 |
| IVF_FLAT, nprobes 8 | +3,082 | 1.4 | 0.704 | 0.534 | 0.728 | 0.90 |
| IVF_FLAT, nprobes 32 | +3,082 | 2.9 | 0.871 [0.858–0.884] | 0.791 [0.743–0.838] | 0.922 | 1.00 |
| IVF_FLAT, nprobes 128 | +3,082 | 8.4 | 0.971 [0.965–0.977] | 0.985 [0.972–0.996] | 0.996 | 1.00 |
| IVF_SQ (int8), nprobes 32 | +778 | 1.4 | 0.850 | 0.800 | 0.905 | 0.95 |
| IVF_SQ (int8), nprobes 128 | +778 | 2.9 | 0.949 | 0.930 | 0.966 | 0.95 |
| IVF_PQ/96, nprobes 32, refine ×5 | +112 | 5.3 | 0.844 | 0.674 | 0.906 | 0.90 |
| IVF_PQ/96, nprobes 128, refine ×5 | +112 | 16.9 | 0.937 | 0.728 | 0.966 | 0.90 |
| IVF_PQ/48, nprobes 32, refine ×5 | +64 | 3.0 | 0.806 | 0.474 | 0.813 | 0.40 |
| IVF_RQ 1-bit, nprobes 32 | +114 | 1.4 | 0.738 | 0.474 | 0.737 | 0.55 |
| IVF_RQ 1-bit, nprobes 32, refine ×5 | +114 | 1.9 | 0.870 [0.856–0.882] | 0.747 [0.687–0.804] | 0.911 | 0.85 |
| IVF_RQ 1-bit, nprobes 128, refine ×5 | +114 | 3.3 | 0.965 [0.959–0.970] | 0.862 [0.817–0.906] | 0.988 | 0.90 |
| IVF_RQ 8-bit (default), nprobes 32, ± refine | +786 | 4.2–4.8 | 0.034 | 0.062 | 0.033 | 0.00 |
| IVF_RQ 8-bit, dot metric, nprobes 32 | +786 | 4.2 | 0.041 | 0.036 | 0.031 | 0.05 |

"+" marks an index kept beside the float32 column, never instead of it: every IVF configuration
adds bytes, and refinement reads the float32 vectors back. The full sweep (p95, build times, every
nprobes/refine pair) is in the JSON.

## Code — 17,256 rows, 53.0 MB

| | probes (15) | self (500 / 200) | |
|---|---|---|---|
| float16, numpy · LanceDB flat | 1.000 · 1.000 | 1.000 · 1.000 | 26.6 MB on disk against 53.1; 4.5 ms against 6.5 |
| int8 | 0.993 | 0.998 | |
| binary → rescore ×4 · ×8 · ×16 | 0.920 · 0.993 · 1.000 | 0.974 · 0.992 · 0.997 | |
| Matryoshka 256 (last / random / projection) | 0.793 (0.700 / 0.653 / 0.707) | 0.866 (0.820 / 0.809 / 0.814) | variance 0.452 · 0.304 · 0.244 |
| IVF_FLAT, nprobes 32 | 1.000 | 0.994 | |
| IVF_RQ 1-bit, nprobes 32, refine ×5 | 0.993 | 0.993 | |

## Findings

1. **float16 is free.** recall@10 0.999–1.000 in every family and both engines, at half the bytes
   (227.5 MB on disk against 453.9 MB for the paper vectors, measured on LanceDB's own files; 26.6
   against 53.1 MB for code), and flat search gets faster, not slower: 19.7 ms against 32.4 ms p50
   (half the memory to stream). LanceDB searches a float16 column with float32 queries natively.
   The one lever here that trades nothing.
2. **int8 costs about one result in a hundred.** 0.989–0.993; 89–93% of queries lose nothing and
   none loses more than one of its ten. Rescoring 20 int8 candidates in float32 restores 1.000, but
   that keeps the float32 column, so the bytes come back. LanceDB 0.33.0 holds int8 only as an
   index beside the float32 column (IVF_SQ); stored as the column itself, int8 is not searchable.
3. **Sign-bit binary is too lossy for this model; 1-bit RaBitQ is not.** Plain sign codes keep
   17–60% of the top ten (and the first hit for 4% of the owner's queries); rescoring 320
   candidates still loses over a third of the owner family. Centring the bits helps a little.
   LanceDB's RaBitQ (IVF_RQ, 1 bit) estimates distances far better than Hamming does: refined ×5 it
   tracks IVF_FLAT at the same nprobes on titles (0.870 against 0.871 at 32; 0.965 against 0.971 at
   128), so nearly all of its loss there is partition error, not the code. The owner's queries are
   where the 1-bit code still costs (0.862 against 0.985 at 128).
4. **Matryoshka: the training is partly there; truncation still loses too much.** The first 256
   dimensions carry 46% of the variance and beat the last 256, a random 256 and a random projection
   by 0.08–0.11 (titles, self) and 0.20–0.24 (owner) — the Matryoshka signature: EmbeddingGemma-2
   kept some of v1's training. But 256 dimensions keep 76% of the titles' top ten and 46% of the
   owner's; 512 keeps 89% and 70%. Rescoring 40 candidates at 768 lifts 256 to 0.95–0.96 for titles
   and self, 0.78 for the owner, and needs the full vectors again.
5. **IVF buys speed the palace does not need yet.** Partitions alone (IVF_FLAT) keep 0.79–0.92 at
   nprobes 32 (8% of the corpus) and 0.97–1.00 at 128, at 2.9 and 8.4 ms against 32.4 ms flat —
   or 19.7 ms flat in float16. At 147k vectors exact search is fast enough beside a 27B model's
   answer, and every IVF index adds bytes rather than saving them. Compression inside the index only
   stacks loss on the partition error: PQ refined reaches 0.94 at nprobes 128 and 16.9 ms, slower
   than flat float16 and less faithful.
6. **The owner's queries are the hardest family everywhere.** Notes about the palace and a life,
   asked of mathematics papers, land in a flat neighbourhood: their nearest papers are nearly tied,
   so small errors reorder them. Every lossy scheme loses most there (sign bits 0.17, Matryoshka 256
   0.46, PQ/48 refined 0.47). Judged on titles alone, a lossy scheme looks 1.5 to 3.6 times as
   faithful as it is for the owner.
7. **IVF_RQ at LanceDB 0.33.0's default of 8 bits is broken on these vectors.** recall@10 0.03–0.06
   on papers and 0.11–0.14 on code, under cosine and dot alike; refinement changes nothing; the
   unrefined cosine distances come back negative (−0.47 measured), which a cosine distance cannot
   be. The same index at 1 bit works on the same vectors, and at 8 bits it worked on 64-dimensional
   synthetic data. The bench keeps the 8-bit rows so a newer LanceDB can be checked against them.
8. **Code is easier than papers.** Its vectors sit further apart: sign bits rescored ×8 keep 0.99,
   and IVF_FLAT at nprobes 32 keeps 0.99–1.00.

## What this decides — the owner's call

- **Recommended: store the vector column as float16.** Lossless on every measure here, half the
  bytes (papers 454 → 227 MB, code 53 → 27 MB on disk), faster flat search. It is a schema change
  (`vector` as `list<float16>[768]` for both the plane's atoms and the physical code rows) and a
  one-time rewrite of both stores, built beside the live ones, verified and swapped by rename as
  A3's migration was — an amendment to dn-vector-membership-store and a build of its own.
- **Not now:** sign-bit binary, PQ and Matryoshka truncation cost too much of the owner's queries;
  int8 is not storable as LanceDB 0.33.0's searchable column, so it would save no disk.
- **Later:** an index — IVF_FLAT, or 1-bit IVF_RQ refined — when the paper store is an order of
  magnitude larger and flat search stops being fast enough. Re-measure then with this bench.

## Caveats

- recall@10 against today measures fidelity, not relevance. A compressed vector can return
  different passages that are just as good; the embedder bench's labelled sets are the instrument
  for that question.
- The palace's own queries are still two. titles, owner and self bracket them as proxies; the owner
  family is small (47) and its intervals are wide.
- LanceDB's k-means is unseeded, so IVF rows move by a few points from one build to the next (the
  owner family at IVF_FLAT nprobes 32 measured 0.815, 0.843 and 0.791 in three builds). numpy rows
  are deterministic (seed 20261030).
- Latency: one client, warm, on ouroboros with the stack up and the 27B asleep; p50 here, p95 in
  the JSON.
- One IVF build logged empty k-means sub-clusters (2 of 16): near-duplicate passages, benign.

## Reproduce

In the live checkout — its gitignored `config/ouroboros.toml` selects the embedder and `data/`
holds the stores; elsewhere the bench refuses rather than open an empty store:

    uv run python -m eval.quantization_bench

About six minutes and 5.4 GB at peak. Query vectors are cached in
`data/eval/quantization-queries.json`; the real queries are read from `data/eval/palace-queries.json`
(both gitignored: they carry the owner's words).
