---
type: experiment-report
experiment: two-phase-ingestion
runs: 3
status: complete
started: 2026-11-07
links:
  - docs/design-notes/dn-two-phase-ingestion.md             # the design these figures test (§6)
  - docs/experiments/two-phase-ingestion-2026-11-07.json    # run 1: the battery, the attribution
  - docs/experiments/two-phase-ingestion-2026-11-08-control.json  # run 2: landing and drain, idle
  - docs/experiments/two-phase-ingestion-2026-11-08-lag.json  # run 3: the lag, drained at once
  - eval/two_phase_bench.py                                 # the harness
  - docs/experiments/corpus-measurements-2026-11-07.md      # the embedder's throughput the batch policy rests on
  - docs/design-notes/dn-scale-and-attribution.md           # SCL-3: the Shapley reading of a source
---

# Two-phase ingestion, measured (2026-11-07)

**Question.** What does landing an item cost without the embedder against with it; how long
after its key does an item's vector arrive under the drain; what do the lexical index, the
embedder and the two together retrieve on a public control set, and so what is the embedder's
attribution as a source; and is VEC-1's certificate the same reading before and after the drain
completes? Nothing here touched a live instance: the harness builds a scratch palace in a
temporary root and removes it.

## Method

Three runs of `eval/two_phase_bench.py`:

1. `--out docs/experiments/two-phase-ingestion-2026-11-07.json`, every phase, on 2026-11-07 to
   08. Its retrieval figures are used as they are, since a ranking does not depend on timing; its
   timings are not used, because another ingest's backfill shared the embedder for all of it
   (below).
2. `--phases landing --out docs/experiments/two-phase-ingestion-2026-11-08-control.json`, the
   timings alone on an idle machine, in the order lazy, the drain, synchronous, lazy again, so
   drift shows as a gap between the two lazy runs.
3. `--phases lag --out docs/experiments/two-phase-ingestion-2026-11-08-lag.json`, a lazy landing
   drained at once, for the lag.

- **The control set.** SciFact as distributed in BEIR, read from the local parquet files the
  embedder bench reads (`~/models/bench-data/scifact`): 5,183 abstracts, each written as a markdown
  item of its title and text cut at 1,200 characters, so that every item is one chunk and the
  embedder's work is a known count; the 300 test claims with graded relevance as the queries.
- **The scratch palace.** A temporary root with its own vault, raw store, vector store and plane,
  catalog, versions, attestations, edges and lexical index; the configuration is the committed
  defaults with the paths moved under the root, the stack's embedder (EmbeddingGemma-2 Q8_0, 768
  dimensions, llama-server on port 8081, shared with whatever else is embedding on the machine) and
  `[embedding] lazy` set per palace. The items land in ten requests of the ingress language
  (`do sync_vault`), 519 items each, through the writer, as the daemon lands them.
- **Landing.** Once lazily (no vector; raw object, lexical units, version, attestation, key) and
  once synchronously (the embedder before the key), on two palaces; wall time over the ten
  requests, items and chunks a second.
- **The drain and the lag.** The drain runs on the lazy palace in two halves, one stream, batch 64,
  a group of 64 landed in one plane transaction; the catalog's `record` is wrapped to timestamp
  each item's key and the drain reports each group's paths once their rows are current, so the lag
  from key to vector is per item. A third drain checks that nothing is left and nothing embedded.
- **The battery.** For each query, three rankings of the items by document: lexical (the BM25
  index's top units, deduplicated by document), semantic (the plane's nearest rows under the
  mirror clearance), and both (reciprocal rank fusion, `c = 60`); recall@10 and nDCG@10 (graded
  qrels). At 50% drained the semantic arm reads the vectors that exist, and `near`'s rule adds the
  lexical ranking over the pending items, fused by rank. The embedder's attribution is the Shapley
  value over the two sources with `v(∅) = 0` and the leave-one-out reading `v({L, E}) − v({L})`,
  with the paired standard error over queries.
- **The certificate.** `search_ranked(k = 10)` for every query at 0%, 50% and 100% drained; the
  share of reads whose margin certifies the top 10, and the median gap.
- **Contention.** In runs 2 and 3 the embedder's `/slots` is sampled every five seconds through
  each phase, with the one-minute load average at its start and end. The harness's own requests
  hold at most one slot in a landing (none when lazy), so a sample above that is another caller;
  the drain's batches spread over the server's slots, so a drain's samples cannot tell. Run 1
  probed the slots only before (0 busy) and after (4 busy).

## Results

| quantity | measured |
|---|---|
| landing without the embedder (lazy), control: seconds, items/s; again at the end | 162.16, 32.0; 161.93, 32.0 |
| landing with the embedder (synchronous), control: seconds, items/s | 3466.39, 1.50 |
| ratio of landing times, synchronous over the mean lazy | 21.4 |
| seconds per request of 519 items, lazy (first, last); synchronous (first, last) | 2.2, 32.5; 67.0, 651.4 |
| the drain, control: chunks, seconds, chunks/s; a second drain embeds | 5183, 201.27, 25.8; 0 (run 1) |
| lag from key to vector, drained at once (lag run): p50, p90, max, mean (s) | 217.81, 230.64, 233.34, 211.95 |
| contention through the control: another caller's share of slot samples (lazy, sync, lazy); load average, highest | [0.0, 0.0, 0.0]; 11.2 |
| run 1, while another ingest's backfill shared the embedder: synchronous items/s; ratio; drain chunks/s | 0.33; 91.3; 10.5 |
| battery at 0% drained, recall@10: lexical, semantic, both, near's rule | 0.7549, 0.0, 0.7549, 0.7549 |
| battery at 50% drained, recall@10: lexical, semantic, both, near's rule | 0.7549, 0.5439, 0.8328, 0.8545 |
| battery at 100% drained, recall@10 / nDCG@10: lexical, semantic, both | 0.7549, 0.9263, 0.9289 / 0.6367, 0.836, 0.7546 |
| standard error of recall@10 at 100%: lexical, semantic, both | 0.0242, 0.0149, 0.0144 |
| attribution at recall@10: Shapley embedder, Shapley lexical, leave-one-out embedder (se) | 0.5501, 0.3787, 0.174 (0.0219) |
| queries the embedder helps / hurts / leaves the same (recall@10, both against lexical) | 60 / 2 / 238 |
| attribution at nDCG@10: Shapley embedder, Shapley lexical, leave-one-out embedder | 0.4769, 0.2777, 0.1179 |
| VEC-1 certified share at 0% / 50% / 100% drained (median gap, bound) | 1.0 / 0.42 / 0.4433 (0.001293, 0.001577) |

**Reading.** Landing without the embedder took 162 s for the 5,183 items, and with it 3,466 s: a
ratio of 21, against the design's falsifier of 10 (TP-7 survives). Both landings slow as the store
grows, the lazy one from 2.2 to 32.5 s a request and the synchronous one from 67 to 651 s, where
every item is its own embedding request and its own plane transaction. The drain then derived the
vectors at 25.8 chunks a second, the embedder's measured rate, and a second drain embedded
nothing. Drained at once after the landing, an item's vector arrived 218 s after its key at the
median and 233 s at most. The lexical index alone reached 0.755 recall@10, the embedder alone
0.926 and the two fused 0.929; the embedder's leave-one-out value is 0.174 with a standard error
of 0.022, so on SciFact the prior buys about a sixth of recall@10 over the bytes (TP-6 survives).
With half the items drained, the semantic arm alone fell to 0.544 and `near`'s rule, the lexical
index over the pending items, kept 0.855. The certified share was 0.42 at half drained and 0.44
at full, so it does not fall as the drain completes (TP-8 survives); at 0% every read was empty
and nothing was claimed.

The one-minute load average reached 11.2 during the synchronous landing: its plane writes are
multithreaded, and around 17:20Z another session ran a lint, a type check and one test file. The
per-request times rise smoothly through it (50 to 73 s more a request), with no step.

## Caveats

- One collection, items cut at one chunk, one run a figure; read to one significant figure.
- Run 1's timings are contended and are reported only as such: another ingest's vector backfill
  held the same embedder through the whole run (from 01:00Z to 12:33Z in three sessions, by its
  runner's gate log, which probes every five minutes), and its structural measurements shared the
  CPU from about 07:55Z to 08:05Z. Run 1 started at 07:55Z and ended at 12:30Z; its probe of the
  slots at the start (0 busy) caught a moment between two of the backfill's batches. Its landing
  ratio was also computed from rates rounded to a tenth (30.3 / 0.3 = 101); from the seconds it
  is 91. The harness now samples the slots through every phase and computes the ratio from the
  seconds.
- The lag was measured with every item landed before the drain started, the worst case for the
  maximum and a fair one for the median; a steady arrival spreads it to a group's drain time. Run
  1's lag (median 631 s) also counted the battery run between the landing and the drain, an
  artifact of the harness's order; run 3 drains at once.
- The lazy landing's cost includes the attestation lookup, which scans the ledger (a pass per
  store), the known quadratic term of the landing; it is the same in both arms.
- The semantic arm's query template is the store's (`task: search result | query: {text}`), not
  SciFact's fact-checking instruction; the embedder bench of 2026-10-28 measured the model with
  the task instruction on items cut at 2,000 characters, so its figures are not these.
