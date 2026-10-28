---
type: experiment-report
experiment: embedder-bench
run: 1
status: complete
started: 2026-10-28
links:
  - eval/embedder_bench.py                          # the harness (this run's exact code)
  - docs/experiments/embedder-bench-2026-10-28.json # raw results, incl. the palace pair cosines
  - docs/audits/restart-readiness-2026-10-28.md     # why the embedder is under review
---

# Embedder benchmark — run 1 (2026-10-28)

**Question.** The owner asked to "upgrade and benchmark the new embedder". Ouroboros has run
Qwen3-Embedding-4B since June; newer candidates exist, and since the move to llama.cpp the embedder
shares the GPU with the 27B chat model (a Metal OOM was measured the same day with both resident).
So "better" has three axes, all measured: retrieval quality, ingest throughput, and resident memory.

**Method.** Each candidate GGUF is served alone by `llama-server --embedding` on :8082 (`-c 8192
-np 4 -ub 2048 -fa on`, all layers on Metal), then stopped. Two public BEIR sets, read from local
parquet: **SciFact** (5,183 abstracts, 300 test claims) and **NFCorpus** (3,633 documents, 323 test
questions); documents cut at 2,000 characters for every candidate alike; graded qrels; nDCG@10 and
Recall@10; each model in its documented prompt format (Qwen: `Instruct: …\nQuery:…` on queries,
plain documents; EmbeddingGemma: `task: … | query: …` and `title: … | text: …`). Throughput is
documents/s while embedding the corpora; memory is the server's peak RSS (sampled every 0.5 s).
The σ transfer embeds the palace's own 64 L0 chunks and reports, per model, the cosine at the same
quantile of the 2,016 pair cosines where the reference model's σ = 0.58 and near-dup = 0.93 sit.

**Confounds, stated.** One run per model, back to back on one machine (no repeats, so no noise
band — the quality gaps that decide anything below are far larger than run-to-run noise in
deterministic embedding, but the throughput figures carry ordinary machine variance). A model-less
code-observe lane (git + SQLite, CPU) ran concurrently with the later candidates — through about
60% of the 4B's run — and the deterministic test tier ran during its last half hour; neither touches
the GPU, but they may have cost the throughput figures a few percent. The 8B ran first, alone, in an
earlier invocation, so its row is from that run's log and is not in the JSON.

## Results

| model | file | SciFact nDCG@10 | NFCorpus nDCG@10 | SciFact R@10 | NFCorpus R@10 | docs/s | peak RSS | dim |
|---|---|---|---|---|---|---|---|---|
| Qwen3-Embedding-8B (Q4_K_M) | 4.68 GB | 0.786 | **0.409** | — | — | 0.9 | 6.04 GB | 4096 |
| Qwen3-Embedding-4B (Q4_K_M) — **incumbent** | 2.50 GB | 0.778 | 0.406 | 0.912 | **0.196** | 1.7 | 3.82 GB | 2560 |
| **EmbeddingGemma-2 (Q8_0)** | 0.31 GB | **0.849** | 0.367 | **0.929** | 0.183 | **24.3** | **0.57 GB** | 768 |
| Qwen3-VL-Embedding-2B (Q8_0) | 1.83 GB | 0.732 | 0.328 | 0.871 | 0.172 | 4.6 | 2.91 GB | 2048 |
| Qwen3-Embedding-0.6B (Q8_0) | 0.64 GB | 0.701 | 0.360 | 0.843 | 0.170 | 12.6 | 1.72 GB | 1024 |

The raw per-model pair cosines are in the JSON.

**σ transfer on the palace's own pairs** (reference: the incumbent 4B; matched by quantile):

| model | cosine at σ = 0.58 (top 5.85%, 118 pairs) | at near-dup 0.93 (top 7 pairs) |
|---|---|---|
| Qwen3-Embedding-4B | 0.577 | gap 0.797 – 0.939 |
| EmbeddingGemma-2 | 0.785 | gap 0.891 – 0.971 |
| Qwen3-VL-Embedding-2B | 0.688 | 0.867 |
| Qwen3-Embedding-0.6B | 0.555 | 0.782 |

The near-dup column needs the gap, not the harness's quantile point: in both the 4B and Gemma the
same 7 pairs sit above a wide gap (7 of 7 shared), so the quantile lands on the 8th pair, below the
gap. Any threshold inside the gap selects the same 7; 0.93 sits inside Gemma's gap too, with the
same margin either side (0.04). At σ the two models agree on 86 of their top-118 pairs (73%).
Gemma's cosines run higher overall (median pair 0.655 against 0.314), which is why σ moves up; the
4B's σ bound [0.55, 0.75] maps to [0.772, 0.867] by the same quantiles.

## Reading

- **Quality is a split decision between the two front-runners.** EmbeddingGemma-2 beats the
  incumbent on SciFact by 0.071 nDCG@10 and loses on NFCorpus by 0.039; mean nDCG@10 0.608 against
  0.592. Recall@10 splits the same way. The 8B is best on NFCorpus by a hair (0.409 vs 0.406) and
  worse than Gemma on SciFact; the 0.6B and VL-2B trail on both.
- **Cost is not close.** Gemma embeds 14× faster than the 4B (24.3 vs 1.7 docs/s) in a sixth of
  the memory (0.57 vs 3.82 GB) with vectors a third the size. That is the measured Metal-OOM hazard
  (27B + 4B resident) mostly gone, re-embeds in minutes instead of hours, and a wake-on-demand
  that is cheap.
- **On the palace's own notes** the two models agree on the near-duplicates exactly and on about
  three quarters of the σ-backbone, so a switch changes which themes form at the margin, not the
  core.
- **Recommendation: switch to EmbeddingGemma-2** with σ = 0.785 (quantile-matched, interim until
  the pre-registered σ sweep, oq-0024 / bp-046), near-dup 0.93 (unchanged, inside Gemma's gap) and
  the σ lever bound moved to [0.772, 0.867]. The NFCorpus loss is the price; if retrieval over the
  owner's notes turns out to look more like NFCorpus (broad questions, many relevant notes) than
  SciFact, the 4B stays one config edit away.
