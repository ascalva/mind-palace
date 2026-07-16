# Retrieval & temporal scaling — search-engine optimizations and compression for a growing corpus-over-time

Seed brainstorm: can classic search-engine / knowledge-graph optimizations and compression
techniques refine the retrieval + storage infrastructure as the corpus grows in size AND in
snapshots over time. Owner-raised; captured from the session-20 discussion (2026-07-16).

## 2026-07-16T21:14:35Z

```capsule
framing: >
  Two distinct scaling axes, often conflated:
  (A) the O(N) corpus axis — the idea-vector index grows with corpus size;
  (B) the O(N × T) axis the owner sharpened — a TIME-SERIES of graphs (snapshots over commits),
      "the graph grows in size and the snapshots over time — that sounds like a lot of data."
  (B) is the bigger half and is a VERSIONING problem, not an embedding problem.

grounded_state:
  # what retrieval/storage actually does today (verified this session, not assumed)
  - retrieval is single-stage, dense-cosine-only, float32, UNCOMPRESSED — LanceDB flat/exhaustive
    scan (core/stores/vectorstore.py:142 `search(vector).metric("cosine").limit(k)`; no
    create_index anywhere in core; comment "Single-user corpus scale; filtered in Python").
  - NO ANN index, NO quantization, NO lexical/BM25 path, NO link-structure ranking prior.
    (`Authority` in the tree is capability-scope authority, NOT link-authority — do not conflate.)
  - snapshots are DERIVED, not materialized: core/temporal/complex.py:39 "a pure function of the
    store contents"; reference edges carry `commit_sha` as edge identity (:68-76), so a historical
    graph is reconstructed by FILTERING a commit-tagged append log — never stored as a full copy.
    vectorstore keeps only the CURRENT digest (:30). => storage is O(total edits), not O(N × T).
    This is already git's Merkle-DAG structural-sharing insight, implemented.
  - the store layer is append-only identity-keyed ledgers (observation_history.py:30,
    runledger.py:133); supersession exists as a LOGICAL relation (versions.py, recursion_ops.py)
    but there is NO physical compaction/prune/gc/retention/decimation in core — git's `gc` half is
    the gap.

decisions:
  - CAPTURE-ONLY seed (no design commitment yet). Ranked entry points if it graduates:
    1. compression cascade first (relieves the binding memory-ceiling constraint, lays coarse→fine rails);
    2. link-structure prior (most native — substrate already built);
    3. hybrid sparse+dense (biggest quality win).
  - the through-line worth keeping: several of these are LATENT in the architecture, not imports —
    centrality ↔ the eigen/harmonic (Hodge L₁) machinery; coarse→fine quantization ↔ the exact-oracle
    pattern (bp-050); the retrieval cache ↔ content-addressing; transitive reduction ↔ already parked
    in bp-051 §11. The roadmap is largely drawing out structure the repo already has.

axis_A_corpus_retrieval:
  # each pick chosen for payoff at SINGLE-USER scale (not raw QPS — flat cosine is fine until N is large)
  - COMPRESSION → memory-ceiling HEADROOM (≤2 resident models / ~20-24GB is the binding constraint,
    not speed): coarse→fine quantization cascade = binary/Hamming first pass (~32×, popcount) →
    int8 rerank (~4×, near-lossless) → exact float32 on final k. Deterministic (unlike approximate
    HNSW — the instruments dislike build-order nondeterminism); the exact float search becomes the
    ORACLE the quantized path is falsified against (recall@k), mirroring bp-050. PQ / LanceDB IVF-PQ
    is the escape hatch (index AND compression in one) — defer until N demands it.
  - LINK-STRUCTURE PRIOR (the "knowledge-graph optimization" Google is famous for): query-independent
    centrality / personalized-PageRank over reference_edges + the spine poset, seeded at the query's
    dense hits (spreading activation). Can be CAUSALLY weighted by the spine's ≼; centrality = leading
    eigenvector of an adjacency operator, conceptually continuous with the harmonic subspace of L₁.
    Pure code ⇒ "code acts" satisfied (no model in the ranking loop). Most native pick.
  - HYBRID SPARSE+DENSE (RRF): dense misses exact-token recall (proper nouns, IDs, rare terms, code
    identifiers) — a personal KB is full of them. Add BM25/lexical index, fuse by Reciprocal Rank
    Fusion. Biggest QUALITY jump; pure code; small new inverted-index store.
  - CONTENT-ADDRESSED RETRIEVAL CACHE (nearly free): memoize by (query_digest, corpus_digest, k,
    filters) — correct-by-construction (the key IS the content; zero staleness). Generalizes the eval
    store's spec_hash dedup.

axis_B_temporal_snapshot_scaling:
  # the versioning toolkit — what actually grows and isn't bounded yet
  - LOG COMPACTION: append-only logs grow forever; superseded events tombstoned but never physically
    leave. Fold superseded events into a compacted base + bounded tail (Kafka log-compaction /
    git-repack / LSM). `superseded_by` is the compaction predicate, already present.
  - MATERIALIZATION CACHE + INCREMENTAL VIEWS: on-demand `complex(commit=sha)` re-filters the whole
    edge log — slower as it grows. (a) content-addressed cache of computed views keyed by
    (commit_sha, corpus_digest), evict under the memory ceiling; (b) view(T+1) = view(T) + new events
    (Hodge-Laplacian rank-update, not from-scratch β₁). The explicit event log (spine) is what buys this.
  - TEMPORAL DECIMATION / logarithmic anchor ladder: instruments range over anchor PAIRS (O(T),
    cross-time O(T²) worst case). Keep per-commit resolution recent, coarsen with age (per-day/week/
    month) — Prometheus/RRDtool model — bounding the instrument anchor set to O(log T). Rarely need
    two-year-old history at per-commit grain.
  - TIME-SERIES COMPRESSION for derived numeric streams (drift gauges, coherence/velocity/eval
    readings per commit): Gorilla-style delta-of-delta + XOR float (~10×). Lean into the DuckDB
    analytical lane already being columnar (RLE/dictionary/bit-packing) — the SQLite(transactional
    chains)-vs-DuckDB(compressible derived bulk) split the spine audit distinguishes IS this routing.

keystone: >
  bp-051 (the spine, built + fixed this session) is the linchpin for axis B: it makes the implicit
  event-sourcing first-class (an explicit append-only (Ev, ≼) log). §11 already parks
  "transitive reduction persistence (recompute vs persist)" — the store-vs-recompute knob at the heart
  of compaction/incremental-views. The owner's concern is, in effect, the reason the spine exists;
  this work becomes a GC-series extension on the spine, NOT a rewrite.

parked:
  - ANN index (HNSW/IVF-PQ): premature at single-user scale + approximate (nondeterministic build)
    which the instruments dislike. RE-ENTRY: measured corpus N makes flat cosine latency unacceptable.
  - LLM query expansion / HyDE: model-in-loop, must be "advice" (local model, memory-ceiling cost);
    the pure-code analog is the personalized-PageRank spreading activation. RE-ENTRY: a retrieval-quality
    gap that structure+lexical can't close AND memory budget allows a resident reranker.
  - Matryoshka (truncatable-prefix) embeddings as a coarse→fine axis. RE-ENTRY: an embedder swap that
    supports it (corpus is single-scale chunk-grain today).
  - Near-duplicate collapse (SimHash/MinHash) — another compression, adjacent to the source-set relation.
    RE-ENTRY: measured near-dup density high enough to matter.

open_questions:
  - Which axis binds first in practice — corpus-N (retrieval latency / RAM) or snapshot-T (log growth /
    view-recompute cost)? Needs a measurement of current data/ growth rates before prioritizing.
  - Does the memory ceiling make embedding compression MANDATORY before more resident-model depth (Track H)?
  - Is a decimation policy safe against the erasure-invariance / determinism the instruments assume
    (coarsening old anchors changes what cross-time instruments can compute)?

next_steps:
  - measure: current data/ store sizes + per-commit growth (turns "a lot of data" into numbers → sets priority).
  - if legs: /graduate is NOT the path — this needs a design note first. Draft a design note
    (temporal-scaling: compaction + decimation + incremental views, on the spine) once wave 2/3 land and
    the spine's downstream (GC-2/GC-3) is stable, since that fixes the substrate this builds on.

references:
  - core/stores/vectorstore.py:30,142   # current flat cosine; current-digest-only
  - core/temporal/complex.py:39,68-76   # snapshots derived by commit_sha filter (not materialized)
  - core/stores/observation_history.py:30, runledger.py:133   # append-only ledger substrate
  - core/temporal/spine.py + docs/build-plans/bp-051 §11   # the event-log keystone + parked recompute/persist knob
  - core/recursion_ops.py, core/stores/versions.py   # supersession = the compaction predicate (logical, not physical)
```
