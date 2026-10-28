---
type: experiment-report
experiment: embedder-bench
run: 1
status: running
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
The σ transfer embeds the palace's own 38 L0 chunks and reports, per model, the cosine at the same
quantile of the 703 pair cosines where the reference model's σ = 0.58 and near-dup = 0.93 sit.

**Confounds, stated.** One run per model, back to back on one machine (no repeats, so no noise
band — the quality gaps that decide anything below are far larger than run-to-run noise in
deterministic embedding, but the throughput figures carry ordinary machine variance). A model-less
code-observe lane (git + SQLite, CPU) ran concurrently with the later candidates; it does not touch
the GPU, but it may have cost the throughput figures a few percent. The 8B ran first, alone.

## Results

| model | file | SciFact nDCG@10 | NFCorpus nDCG@10 | docs/s | peak RSS | dim |
|---|---|---|---|---|---|---|
| Qwen3-Embedding-8B (Q4_K_M) | 4.68 GB | 0.786 | **0.409** | 0.9 | 6.04 GB | 4096 |
| **EmbeddingGemma-2 (Q8_0)** | 0.31 GB | **0.849** | 0.367 | **24.3** | **0.57 GB** | 768 |
| Qwen3-Embedding-0.6B (Q8_0) | 0.64 GB | 0.701 | 0.360 | 12.6 | 1.72 GB | 1024 |
| Qwen3-VL-Embedding-2B (Q8_0) | 1.83 GB | _pending_ | | | | 2048 |
| Qwen3-Embedding-4B (Q4_K_M) — **incumbent** | 2.50 GB | _pending_ | | | | 2560 |

Recall@10 and the raw per-model pair cosines are in the JSON.

## Reading

_Pending the last two rows._
