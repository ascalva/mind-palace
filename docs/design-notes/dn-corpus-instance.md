---
type: design-note
id: dn-corpus-instance
track: dynamics
status: draft                  # provenance description, never a gate; the merge is ratification
implementation: design-only    # nothing built, nothing ingested; the measurements are read-only and in a scratch directory
created: 2026-11-07
updated: 2026-11-07
links:
  - papers/2026-11-07-corpus-instance/paper.tex            # the article: the two theorems, the arithmetic, the staged protocol
  - docs/experiments/corpus-measurements-2026-11-07.md     # the measurements this note's arithmetic rests on
  - docs/design-notes/dn-scale-and-attribution.md          # SCL-1 to SCL-4: the thresholds, the loop, the attribution readings
  - docs/experiments/scale-study-2026-11-07.md             # where the gap and the Hodge split stabilized on a real citation graph
  - docs/design-notes/dn-graph-dynamics.md                 # DYN-4 to DYN-6: the modes, the quotient, the gap
  - docs/tracks/deployed-instances.md                      # DI-2: instance identity and the derived namespaces this instance lives in
  - docs/design-notes/dn-ingress.md                        # the ingress: one writer, embedding the serial stage, batches that converge
  - docs/design-notes/vector-membership-store.md           # the shared plane, float16 (A4), VEC-1 (A4.5)
  - docs/experiments/vector-quantization-2026-10-30.md     # what each vector code costs in recall, measured
  - docs/experiments/profile-2026-11-06.md                 # the latency baseline and the no-compiled-rewrite verdict
supersedes: null
superseded_by: null
warrant: null
---

# The corpus instance: a hundred gigabytes of open text, to study the store at scale

> Composed on the corpus session (Fable 5.1, 2026-11-07), on the standing direction that the
> design and its arithmetic come first and the build follows a licence given at the merge.
> Agent-drafted, filed `draft` on a branch; the merge is ratification. Nothing is built and
> nothing is ingested: `core/`, `eval/`, `config/` and every store are untouched; the samples
> were fetched into a scratch directory and measured there. Every nontrivial claim carries a
> grade: `[THEOREM]` is machine-checked and names its declaration; `[ESTABLISHED]` is a cited
> result's or a ratified note's; `[DERIVED]` is argued here from those; `[MEASURED]` is a figure
> from `docs/experiments/corpus-measurements-2026-11-07.md` or a read-only reading of the live
> stores; `[INFERENCE]` is a design call with a named falsifier; `[HYPOTHESIS]` is a claim the
> instance is built to test, with the measurement that tests it named. The article
> `papers/2026-11-07-corpus-instance/paper.tex` states the same theory and arithmetic with the
> references.

## 1. Purpose and scope

### 1.1 The question

The scale study measured a single citation graph and found where its macro quantities stop
fluctuating: the spectral gap of a dense core concentrates once the core holds one to two thousand
nodes with a minimum degree near `ln N`, and the Hodge split settles one to two decades of `N`
earlier. A private store of a few dozen notes is below those thresholds by orders of magnitude.
The question this note answers is how to build a store large and varied enough that the macro
behaviour of the knowledge system itself, not of one graph, can be studied: what context does for
answers as the corpus grows, where the system's constructs (cores, flows, scoped queries, the
attribution loop) earn their keep, and what the system costs per gigabyte.

The direction is that adding context is good, connected context and disparate trends both, and
that the design's job is to make that true in practice. Two pieces of theory say exactly when it is
true and what breaks it (§2); the design follows from them (§3 to §6).

### 1.2 Decisions

1. **The instance is `corpus`, a named instance under DI-2's derived namespaces (§3).** It
   touches nothing of the default instance; it has one writer, its own ledger, its own levers; every
   item lands labelled `observed` with its source and path as origin.
2. **The raw store is zstd-compressed text, and the budget is counted in text (§4.1).** A hundred
   gigabytes of UTF-8 text in the landing form compresses to 35 GB at `zstd -3` and 28 GB at `-19`
   on these sources. `[MEASURED]`
3. **A gigabyte of text is 1.3 million chunks, so full-precision vectors do not fit at 100 GB
   (§4.2).** At the chunker's 1,200 characters, 100 GB is 134 million chunks; float16 768-dimension
   vectors would take 206 GB, int8 103 GB, Matryoshka-256 float16 69 GB, int8 34 GB, a one-bit code
   13 GB. Under the 92 GB cap (117 GB free, 25 GB to be kept free) only the one-bit code fits at
   100 GB; full float16 fits up to 33 GB of text. `[MEASURED, DERIVED]`
4. **The graph and its indexes must be compact, not the live stores' shapes (§4.3).** The live
   plane costs 1,084 bytes an occupancy and the reference store 567 bytes an edge, with their
   indexes; at 134 million chunks and 1.8 billion edges that is a terabyte. Columnar edges (12 bytes)
   and item-grain occupancies with integer ids bring the graph to 31 GB. `[MEASURED, INFERENCE]`
5. **The embedder is the bottleneck, at 26 chunks a second; the daemon's job rate is not
   (§5).** Measured on this machine: 26 chunks/s on one stream at batch 64, 29 to 30 with more
   streams, at the cost of seconds of latency for every other caller. The daemon lands 12 jobs a
   minute; a job that carries a batch of two thousand items lands 10^7 items in a day, so the bulk
   path is a batched script through the ingress, not a faster queue. `[MEASURED, DERIVED]`
6. **Three stages, 1, 10 and 100 GB, each with the measurements it must produce (§6).** The 10 GB
   stage is the last at which exact float16 chunk vectors fit beside everything else, so it is
   where the coded options are measured against exact answers before the 100 GB stage commits to
   one. `[INFERENCE]`
7. **Six sources, every licence checked; two carry conditions the owner decides on (§7).**
   Wikipedia (CC BY-SA 4.0 and GFDL, dumps and a live edit stream), OpenAlex (CC0, snapshot and
   API), arXiv metadata (CC0, OAI-PMH), Project Gutenberg (public domain in the United States),
   Stack Exchange (CC BY-SA, the 2024-04-02 archive and the API; the later official dumps need an
   account and terms), Hacker News (the official API, no open licence on the content).
   `[ESTABLISHED, cited in §7]`
8. **The open decisions are priced (§8), and the default that fits is one-bit codes at the chunk
   grain with exact rescoring by re-embedding the candidates' text.** `[INFERENCE, falsifier
   CIF-3]`

### 1.3 Out of scope

Any `core/`, `eval/` or `config/` change (the overlay in §3.1 is shown, not written); any
ingestion (the first fetch is licensed at the merge and follows the ingress's merge, #71); the
statistical-physics reading of the evolution (dn-graph-dynamics §5.4 stands as the hypothesis);
a new vector code in the store (the codes are measured in the 10 GB stage with the existing
bench, `eval/quantization_bench.py`, before any is built); redistribution of any source (the
instance reads and never republishes).

### 1.4 What is proved, what is cited, what is measured, what is open

Proved elsewhere and used here: SCL-1 to SCL-3 (`formal/Palace/Scale.lean`), DYN-4 to DYN-6
(`formal/Palace/Dynamics.lean`), VEC-1 (`formal/Palace/Cosine.lean`), ING-5, ING-9, ING-11
(`formal/Palace/Ingress.lean`). Cited: the chain rule and the nonnegativity of conditional mutual
information; the variance of a mean of correlated variables (Kish's design effect); the
concentration of random-graph spectra; the measured recall of each vector code on the live
corpus (2026-10-30). Derived here: the crowding lemma (§2.1) and the block-correlation form of the
effective count (§2.2). Measured here: the ratios of §4, the throughput of §5, the rates of §7.
Open, stated where it bites: the chunk rate of a Hacker News thread is taken from the Stack
Exchange rate (§4.1); the compact occupancy cost is a design target, not a measurement (§4.3);
the recall of a one-bit code with re-embedding has not been measured on these sources (§6, stage
2's first job).

## 2. The theory, stated precisely

### 2.1 CI-1 Information never hurts an ideal reasoner; finite retrieval crowds

Let `X` be what a question asks for, `Y` the context a reader has, `Z` context added. The chain
rule for mutual information gives `I(X; Y, Z) = I(X; Y) + I(X; Z | Y)`, and conditional mutual
information is nonnegative, so

```
I(X; Y, Z) ≥ I(X; Y),      equivalently      H(X | Y, Z) ≤ H(X | Y):
```

conditioning never increases entropy. A reader that uses the whole context optimally (the Bayes
decision on `(Y, Z)`) has expected loss no greater than on `Y` alone, for any bounded loss, because
the decision on `Y` is among the decisions available on `(Y, Z)`. `[ESTABLISHED: Cover and Thomas,
Theorems 2.5.2 and 2.6.5]` So added context, connected or disparate, cannot hurt an ideal reasoner;
if it hurts, the reasoner is not ideal, and the one way this system is not ideal is that it reads
through a finite retrieval.

**The crowding lemma.** Let a scorer `s` rank the items of a corpus and `R_k(C)` be the `k` best
of `C`. For `C ⊆ C'`,

```
R_k(C') ∩ C ⊆ R_k(C).
```

An item of `C` among the `k` best of `C'` is beaten by fewer than `k` items of `C'`, so by fewer than
`k` items of `C`, so it is among the `k` best of `C`. Hence for a relevant item `r ∈ C`,
`[r ∈ R_k(C')] ≤ [r ∈ R_k(C)]`: under a fixed scorer and a fixed budget, recall at `k` is
nonincreasing as the corpus grows, whatever is added. `[DERIVED; two lines, over any total order
with ties broken consistently]` The reader sees `R_k`, not `C`, so what it receives is
`I(X; R_k(C'))`, which can fall while `I(X; C')` rises; the difference is the crowding, and it is
the practical failure mode of added context: the relevant piece is pushed out of the window by
pieces that score above it and inform less.

The remedy is not less context but a budget that scales with the corpus: the ranking must select
from a structure, not from one flat list. The system has four such structures, and each is a
restriction of `C'` to a set `σ` that contains `r` and is sized by the question rather than by
the corpus, so the recall inside it is the recall of `|σ|`, not of `|C'|`:

- **scopes**, `over <source>` and `within <region>` (QSA-2: `within` is a congruence on kernels and
  pushes to the leaves), so a question asked of one source competes with that source's items;
- **cores**, the `k`-core of a community (the scale study's instrument: the gap concentrates on the
  6-core and 10-core and never on the whole component), so the dense part of a field is a scope
  with a stable spectrum;
- **flows**, the HodgeRank potential of a dated relation (DYN-3), which orders a community's items
  by who leads, a ranking that is not the scorer's and does not crowd with the corpus;
- **provenance per source**, the origin every item carries (ING-13), so a reader can ask of one
  source and the ledger can attribute to it (SCL-3).

`[DERIVED from the lemma and QSA-2, DYN-3, ING-13; the empirical question, the rate at which
unscoped recall falls with `N` on this corpus and whether the scoped recall is flat, is stage 1's
retrieval battery, §6]`

### 2.2 CI-2 The effective number of independent signals

Let `N` signals have unit variance and mean pairwise correlation `ρ̄ ∈ [0, 1]`. The variance of
their mean is `(1 + (N − 1) ρ̄) / N`, so the number of independent signals that would give the
same variance, the effective number, is

```
N_eff = N / (1 + (N − 1) ρ̄)  ≤  1 / ρ̄,      N_eff → 1 / ρ̄  as  N → ∞.
```

`[ESTABLISHED: Kish's design effect, 1 + (N − 1) ρ̄]` Within one correlated domain the count of
independent signals is capped near `1/ρ̄` whatever the number of signals. With `D` domains of `m`
signals each, correlation `ρ_w` within a domain and `ρ_b` between domains,

```
Var(mean) = [1 + (m − 1) ρ_w + m (D − 1) ρ_b] / (D m),
N_eff → D / (ρ_w + (D − 1) ρ_b)  as  m → ∞,
```

which is `D / ρ_w` when the domains are uncorrelated and `1 / ρ_w` when they are as correlated as
their members: the effective count grows with the number of domains exactly to the extent that the
domains are disparate. `[DERIVED; the sum of the covariance matrix's entries by blocks]`

Read through the thresholds of dn-scale-and-attribution: SCL-4's `K`, the number of independent
resolved units an effect needs, is bounded by `N_eff`, so a corpus of one domain cannot push `K`
past about `1/ρ̄` however large it grows, and the macro behaviour of the system (a difference
between arms at the bar) becomes visible only when `D / ρ_w` clears `K`. Varied sources are what
reach that regime, and the connections between domains, the bridging edges between communities of
different sources and the rises they share, are themselves the quantities to measure: `ρ_b` is
read off them. `[DERIVED from CI-2 and SCL-4]` A signal here is a community's activity series
(new items and edges per week, or the velocity of its centroid under DYN-1) at the instance's cuts;
`ρ_w` and `ρ_b` are its correlations within and across sources; `N_eff` is computed from them. The
hypothesis the instance tests is that `ρ_b` on these six sources is well below `ρ_w`.
`[HYPOTHESIS; checked by stage 1's bridge and rise measurements, falsifier CIF-2]`

## 3. Where it lives

### 3.1 A named instance

The instance's id is `corpus`. Under DI-2 everything it holds is derived from that id and disjoint
from the default instance by construction: its root is `instances/corpus/` (gitignored, one
directory to mount or archive), its stores, spool, lock and levers under it, its Keychain items
`corpus.<name>`, its launchd labels `com.mind-palace.corpus.<role>`, its exhaust lane inside its
root. It declares no vault, no transcripts and no code agent, so it reads none of the default
instance's sources; the loader refuses an overlay that could reach anything another instance
writes, and the property test over generated ids checks the invariant. `[ESTABLISHED: DI-2,
`tests/property/test_instance_namespaces.py`]` The overlay, shown here and written at the build:

```toml
# config/instances/corpus.toml: the open-corpus instance (dn-corpus-instance).
[instance]
id = "corpus"

[runtime]
embedding_backend = "llamacpp"
ports = { embedding = 8081 }        # the stack's embedder; the daemon of the default instance uses it too

[embedding]
model = "embeddinggemma-2"
dim = 768
query_template = "task: search result | query: {text}"
document_template = "title: none | text: {text}"

[dreaming]
similarity_threshold = 0.785
scheduled = false                   # nothing interprets this corpus on a schedule

[ingestion.vault]
enabled = false                     # no vault, no transcripts, no code: the sources below are declared
[ingestion.transcripts]
enabled = false
[ingestion.code]
enabled = false

[ingestion.corpus]                  # the sources of §7, each a line of the ingress's table (§5.2)
root = "instances/corpus/sources"   # dumps and stream checkpoints land here, under the instance's root
```

The `[ingestion.corpus]` section does not exist in the schema today; it is the one config change
the build adds (§5.2), and the loader drops unknown sections, so until it exists the instance has
no sources and ingests nothing. `[INFERENCE, falsifier CIF-5]`

### 3.2 One writer, one label, one origin each

The instance has one writer, its supervisor, and every surface writes a request its daemon
enqueues (dn-ingress D3). Every item lands through a script of the ingress language under the
label its source's rule gives, and that rule is the same for all six sources: `observed`. A public
corpus is nobody's authored stratum; what distinguishes an item is its **origin**, the source name
and the item's path (`corpus/wikipedia/<page id>`, `corpus/openalex/<work id>`, …), which the
value carries and no expression can change (ING-13). So the store can say of every chunk which
source it came from and at which identity, the scoped queries of §2.1 can restrict to a source,
and the attribution of §6 can ablate one. A version of an item (a Wikipedia revision, an arXiv
`v2`, an edited answer) is a new version on the identity's chain, never a new identity (ING-7 as
the ingress keeps it). `[DERIVED from ING-13, ING-14, ING-7]`

What the instance never does: write the default instance's levers, strata or ledger (SAF-5 of
dn-scale-and-attribution); read its vault, transcripts or code; land an item without its origin;
redistribute a source. Its ledger (dn-prediction-ledger) is its own, under its root, with its own
anchored head.

### 3.3 The disk

The instance shares the machine's one disk with the default instance. 117 GB are free; the rule
is that 25 GB stay free; so the instance's whole footprint, raw, vectors, graph, indexes and
spool, is capped at **92 GB**, below the 100 GB dataset budget. Every figure in §4 is read against
92. `[MEASURED: `df`, 2026-11-07]`

## 4. Storage arithmetic

### 4.1 Raw text

The unit is a byte of UTF-8 text in the landing form: the prose of an item with markup removed,
a title prepended, metadata beside it as JSON. Measured on the samples
(`corpus-measurements-2026-11-07`):

| source | mean item | zstd -3 | zstd -19 | chunks per MB | mean chunk |
|---|---|---|---|---|---|
| Wikipedia, prose | 22.5 kB | 2.77 | 3.59 | 1,217 | 964 chars |
| Stack Exchange, posts | 1.4 kB | 2.95 | 3.64 | 1,313 | 830 |
| OpenAlex, title and abstract | 1.6 kB | 3.08 | 3.94 | 1,578 | 704 |
| arXiv, title and abstract | 1.5 kB | 2.93 | 3.58 | 1,728 | 649 |
| Hacker News, one comment an item | 0.25 kB | 2.65 | 3.00 | 4,212 | 240 |
| Project Gutenberg, books | 932 kB | 2.83 | 3.67 | 1,129 | 1,018 |

Two readings. Prose compresses 2.7 to 3.1 times at `zstd -3` and 3.6 to 3.9 at `-19`; the design
stores raw text at `-3` (fast, 400 MB/s on this machine's class) and keeps `-19` as the lever that
buys a fifth back when the cap bites. A short item costs a whole chunk, so comments taken one at a
time make 4,200 chunks per MB; the design takes a Hacker News **thread** as the item, each comment
a block (the chunker is block-aware), and sizes it at the Stack Exchange rate, an assumption the 1
GB stage measures. `[MEASURED; the thread rate an INFERENCE, falsifier CIF-1]`

**The 100 GB mix.** The sources' sizes (§7) admit many mixes; this one spends the budget where the
instruments need it, with dated graphs and version chains in every source but one:

| source | text GB | what it is | chunks (M) | zstd -3 GB | zstd -19 GB |
|---|---|---|---|---|---|
| Wikipedia | 35.0 | every article's current prose (about 30 GB) and a 5 GB subset of revision histories | 42.6 | 12.6 | 9.7 |
| OpenAlex | 24.0 | 15 M works with abstracts: Mathematics and Computer Science entire, Physics sampled | 37.9 | 7.8 | 6.1 |
| Stack Exchange | 15.0 | math, physics, stats, cs, mathoverflow: posts, comments, edit history | 19.7 | 5.1 | 4.1 |
| Hacker News | 12.0 | every item, as threads | 15.8 | 4.5 | 4.0 |
| Project Gutenberg | 9.5 | 10,000 English texts | 10.7 | 3.4 | 2.6 |
| arXiv | 4.5 | every record's title and abstract, with its versions | 7.1 | 1.5 | 1.1 |
| **total** | **100.0** | | **134.4** | **34.9** | **27.7** |

So a hundred gigabytes of text is 134 million chunks and 35 GB of raw store. `[MEASURED ratios,
DERIVED mix]`

### 4.2 Vectors

Each chunk is one vector of the embedder's 768 dimensions. The bytes per vector, and what each
option costs in retrieval quality on the live corpus (recall at 10 against exact float32,
`vector-quantization-2026-10-30`, the titles, owner and self families):

| option | bytes | at 1 GB (1.3 M) | at 10 GB (13.4 M) | at 100 GB (134 M) | what it keeps of the exact top ten |
|---|---|---|---|---|---|
| float16, 768 | 1,536 | 2.1 GB | 20.5 GB | 206 GB | 0.999 to 1.000; VEC-1 bounds the cosine error at `4.884e-4` and certifies a top `k` whose margin exceeds `2(betaStore + betaQuery + γ)`, which the live store did for 54% of its queries `[THEOREM, MEASURED]` |
| int8, 768 | 768 | 1.0 | 10.3 | 103 | 0.989 to 0.993, one result in a hundred lost; not a searchable column in LanceDB 0.33, only an index beside the float column |
| float16, 256 (Matryoshka) | 512 | 0.7 | 6.8 | 69 | 0.46 to 0.76 (the first 256 dimensions carry 46% of the variance); 0.78 to 0.96 rescored from full vectors |
| int8, 256 (Matryoshka) | 256 | 0.3 | 3.4 | 34 | not measured; at most the row above |
| one-bit code, 768 bits | 96 | 0.1 | 1.3 | 13 | sign bits 0.17 to 0.60, 0.63 to 0.96 rescored from full vectors at ×32; the RaBitQ one-bit index 0.86 to 0.97 refined at ×5, nprobes 128 |

Under the 92 GB cap, with the raw store and the graph of §4.3 beside them, the footprints at 100 GB
are:

| configuration at the chunk grain | raw + vectors + graph + ids + index | fits in 92 GB |
|---|---|---|
| float16 768 | 35 + 206 + 31 + 6 + 1 = 280 GB | no |
| int8 768 | 35 + 103 + 31 + 6 + 1 = 177 GB | no |
| float16 256 | 35 + 69 + 31 + 6 + 1 = 142 GB | no |
| int8 256 | 35 + 34 + 31 + 6 + 1 = 108 GB | no |
| one-bit code | 35 + 13 + 31 + 6 + 1 = 86 GB | yes |
| float16 768 at the item grain only (36 M items) | 35 + 56 + 31 = 122 GB | no |

And the largest corpus each option admits, per gigabyte of text (raw 0.35, graph 0.31, ids 0.06,
index 0.01, plus the vectors):

| option | GB of footprint per GB of text | text that fits in 92 GB |
|---|---|---|
| float16 768 | 2.80 | 33 GB |
| int8 768 | 1.77 | 52 GB |
| float16 256 | 1.42 | 65 GB |
| int8 256 | 1.08 | 85 GB |
| one-bit code | 0.86 | 106 GB |

The reading: exact chunk vectors fit up to a third of the way; at 100 GB the vector plane must be a
code, and the only code that fits is the one-bit one, whose unrescored recall is the worst
measured. What makes it usable is that the raw text is on disk: the top `m` candidates by code can
be **re-embedded** at query time and rescored exactly, at `m / 26` seconds (1.5 s for `m = 40`,
§5.1), with no full-precision column kept. The VEC-1 certificate then applies to the rescored
list exactly as to a float16 store. That is the design's default (D-1, §8), and the recall it
keeps on these sources is stage 2's first measurement, against exact answers that still fit
there. `[DERIVED; the recall of codes with re-embedding is OPEN, falsifier CIF-3]`

### 4.3 The graph and its indexes

The live stores' bytes per row, read read-only: a curated Lance row 2,215 B (the float16 vector
1,536 and 679 for the text column and ids), a plane occupancy 1,084 B with its three indexes, a
reference edge 567 B with its five, a membership 385 B. `[MEASURED]` At the corpus's counts, 36
million items and about 1.8 billion dated in-corpus edges (Wikipedia 7.3 M articles at about 150
article links each, OpenAlex 15 M works at 40 in-corpus references, Hacker News 5 M threads at 9
replies, Stack Exchange 6 M posts at 2.5, arXiv 3 M at 1.5 versions), the live shapes do not
scale:

| component | unit | count | as today | compact |
|---|---|---|---|---|
| chunk rows in Lance beside the vector | 679 B with the text duplicated; 48 B as ids and offsets into the raw item | 134 M | 91 GB | 6.5 GB |
| plane occupancies | 1,084 B at the chunk grain; 120 B at the item grain with integer ids and one index | 134 M / 36 M | 146 GB | 4 GB |
| edges | 567 B as `reference_edges` rows; 12 B as sorted columnar triples (two int32 ids, one int32 date) | 1.75 G | 994 GB | 21 GB |
| versions | 120 B a row | 47 M | 6 GB | 6 GB |
| the IVF partition index over coded chunks | 8 B a chunk | 134 M | | 1 GB |

The compact column is the design: the chunk text is not duplicated into Lance (the raw store
holds it, compressed; a chunk is `(item digest, start, end)`), occupancies are at the item grain
(the chunk index is the Lance row's), edges are columnar per source and per cut and are loaded
as sparse matrices for the spectra, and only the quotient graph between communities (DYN-5) and
the derived backbone land in the palace's relation stores. 31 GB, against 1.1 TB. The 120 B
occupancy is a target, not a measurement; the 1 GB stage measures it (§6). `[INFERENCE,
falsifier CIF-4]`

### 4.4 The footprint, summarized

| stage | text | raw (zstd -3) | vectors | graph and indexes | total | of 92 GB |
|---|---|---|---|---|---|---|
| 1 GB | 1 GB | 0.35 GB | float16 768: 2.1 GB (exact); every code beside it for the bench: +1.5 GB | 0.4 GB | 4.4 GB | 5% |
| 10 GB | 10 GB | 3.5 GB | float16 768: 20.5 GB (exact); the one-bit code beside it: +1.3 GB | 3.8 GB | 29 GB | 32% |
| 100 GB | 100 GB | 35 GB (28 at -19) | one-bit code: 13 GB; no full column | 38 GB | 86 GB (79 at -19) | 93% (86%) |

The 100 GB stage sits at the cap; `zstd -19` is the lever that restores 7 GB of headroom, and the
spool, logs and the ledger are counted in the graph-and-indexes column's slack. `[DERIVED]`

## 5. Throughput, and the bulk path through the ingress

### 5.1 The embedder

Measured against the stack's embedder on port 8081 with the chat model idle (checked before every
configuration), 3,000 chunks of 973 characters and 240 tokens on average:

| batch | streams | chunks/s | tokens/s | another caller's probe |
|---|---|---|---|---|
| 8 | 1 | 21.4 | 5,300 | 0.60 s (23 ms idle) |
| 32 | 1 | 23.4 | 5,900 | 1.23 s |
| 64 | 1 | 26.1 | 6,200 | 1.84 s |
| 32 | 2 | 28.9 | 6,800 | 1.65 s |
| 32 | 4 | 30.4 | 6,800 | 4.32 s |
| 64 | 4 | 29.0 | 6,750 | 8.45 s |

Throughput saturates near 30 chunks/s; a second stream buys 11%, four buy 16%, and every stream
adds its queue to the latency another caller sees, which is the default instance's daemon and
the reader at the chat model. The design embeds on **one stream at batch 64, 26 chunks/s**, and
yields: a bulk batch is not started while the embedder has a request from another principal in
flight, and the instance's own queries wait their turn. `[MEASURED; the yielding rule an
INFERENCE]`

The compute at each stage, at 26 chunks/s:

| stage | chunks | embedder time | at 30/s | re-embedding 40 candidates a query |
|---|---|---|---|---|
| 1 GB | 1.3 M | 14 h | 12 h | 1.5 s |
| 10 GB | 13.4 M | 143 h, 6 days | 5 days | 1.5 s |
| 100 GB | 134 M | 1,430 h, 60 days | 52 days | 1.5 s |

Sixty days of the embedder is the price of the chunk grain at 100 GB on this machine, and it is
the same price for every vector option, because a code is derived from the full vector. The
embedder sleeps after 60 s idle and shares Metal with the 27B chat model, which has been measured
to run out of Metal memory under load; so the bulk path runs when the chat model is asleep and
stops when it wakes, and the 60 days are calendar weeks at the hours the machine is otherwise
idle. The alternatives are the owner's (D-4, §8). Compression and chunking are not on the critical
path: `zstd -3` runs at hundreds of MB/s and the chunker at tens of MB/s, minutes per stage.
`[MEASURED, DERIVED]`

### 5.2 The bulk path

The daemon's job rate, read from its queue, is 720 an hour, 12 a minute (27,398 `vault_sync` jobs
of 0.07 s over 38 hours): the tick's cadence, not the writer's ceiling. A path that enqueued one
item per job would land 10^7 items in 580 days; the bulk path makes a job a batch. `[MEASURED]`

Each source is a line of the ingress's table (dn-ingress-language E2): a structured source with
a location under the instance's root, a format, an item rule (which records are items and the
template of an item's path), a label rule (`observed`, one class), a **refresh** (an edge process
the runtime runs before the first read) and a **cursor** (the field whose newest value is
recorded once a plan that read the source has landed). The refresh is the only process that
touches the network, and it is an edge process of the instance: it fetches a dump part or drains
a stream into the source's directory and writes batches of items as files the daemon trusts
(E2's handoff rules: the daemon's account, no links, under the cap). The script is one per
source and the same shape for all six:

```
# ingress/sync_corpus.palace: one batch of a corpus source, observed, under its own origin.
param name, batch
for it in items(source("corpus/" + name), batch: batch) {
    store it.content in "observed" at "corpus/" + name + "/" + it.id
}
```

`items(h, batch: b)` is the one addition the language needs: the next `b` items past the
source's cursor, so a plan is bounded in gas (E10) and lands as one command of the keyed model.
A batch of 2,000 items is about 2,700 chunks, 100 s of the embedder, one transaction; by ING-9
and ING-11 batches on distinct identities land in any order and converge under re-run after any
interruption, and by ING-5 a re-fetched item whose text the plane holds embeds nothing, which is
what makes a daily stream drain idempotent. At 2,000 items a job, 10^7 items are 5,000 jobs, 7
hours at the tick's rate, and the embedder, not the queue, is what the jobs wait on. The
compute half (acquire, derive) is the refresh and the chunker, pure per source; the land half
(address, embed, land) is the supervisor's, in batches (dn-ingress D4). `[DERIVED from ING-5,
ING-9, ING-11 and E2; the `batch:` argument an INFERENCE, falsifier CIF-6]`

What this costs the ingress: one reading function's argument, one config section (§3.1), and six
refresh processes under `edge/`. The scripts themselves are six lines each. The daily drains:
the Wikipedia edit stream at 3.2 edits a second (280,000 a day, of which the subset's pages are a
few hundred), Hacker News at 10,000 items a day, the Stack Exchange sites at a few hundred posts
a day, arXiv at about 2,000 records a day across all sets, OpenAlex's quarterly snapshot; a
day's drain is under 50,000 chunks, half an hour of the embedder. `[MEASURED rates]`

## 6. The staged plan

Every stage is a dated extension of the one before (growing is adding cuts, not replacing the
corpus, dn-scale-and-attribution §5), and every stage produces the same families of measurement
against `N`, so the curves are read across three decades. The method for the macro quantities is
the scale study's (`eval/scale/`): yearly cuts, the smallest twenty eigenvalues of the normalized
Laplacian by shift-invert ARPACK with a minimum-degree ordering, node and edge bootstrap widths,
the 10% crossing, the `k`-cores, the Hodge split of the dated flow by LSMR on the clique
complex. It ran at `N = 33,000` in minutes; the corpus's graphs are measured **per source and
per community** at that scale, and the whole is read on the quotient graph of the communities
(DYN-5: exact on block fields, the gap never lowered), never on 36 million nodes at once.

### Stage 1: 1 GB (about 170 MB a source, 1.3 M chunks, 14 h of embedding)

Everything exact: float16 768 chunk vectors (2.1 GB) and every code beside them for the bench.
The configuration is the live one, so every answer has a VEC-1 certificate where its margin
allows.

| measurement | what it produces | what would falsify the expectation |
|---|---|---|
| macro quantities against `N`, per source | `γ`, the first four eigengaps, `d_min`, the `k`-core crossings and the Hodge split at yearly cuts, with bootstrap widths; six curves, one per relation kind (hyperlinks, citations, replies, answers, versions, none) | **CIF-7**: a source whose 6-core or 10-core gap width never falls under 10% by `N = 10^5`; then the concentration law's shape depends on the relation kind and the scale study's threshold is the citation graph's alone |
| the Hodge split's earlier settling | per source, the `N` at which gradient, curl and harmonic widths cross 10%, against the `N` for `γ` | **CIF-8**: a source whose harmonic fraction keeps moving at an `N` where `γ` has settled |
| cross-source bridges | the count and share of edges whose ends lie in communities of different sources (explicit: Wikipedia citations of arXiv and DOI works, Hacker News and Stack Exchange links to Wikipedia and arXiv, the OpenAlex–arXiv twins; semantic: chunk pairs across sources above `σ`), against a degree-preserving rewiring null | **CIF-2**: bridges at or below the null's count; then the sources are disconnected at this scale and the premise of CI-2's `ρ_b ≪ ρ_w` fails here |
| shared rises | per community, a weekly series of new items and edges; `ρ_w` within a source, `ρ_b` across, at lags 0 to 8 weeks; `N_eff` by CI-2 | **CIF-2** again: `ρ_b` within the bootstrap band of `ρ_w` |
| the retrieval battery | per source, 500 held-out items' titles as queries (the quantization bench's shape); cross-source, the labelled twins (an arXiv abstract to its OpenAlex record, a Wikipedia citation to its paper, a Hacker News story to its target) as queries with a known answer; the BEIR pair of the embedder bench as a fixed external control; recall at 10 unscoped and `over <source>`, at 1 GB and again at every later stage | **CIF-9**: unscoped recall flat in `N` across the stages, so crowding is not the failure mode at these scales; or scoped recall falling with the source's own `N`, so the scope is not the remedy |
| attribution | the ledger's generators (link, version, confirmation) over the six sources with the ablation arms and the Shapley reading; the OpenAlex–arXiv pair as the redundancy witness of SCL-3 (`loo ≈ 0` for each, Shapley near a half each) | **CIF-10**: leave-one-out at the bar for both twins; then they are not redundant on this corpus and SCL-3's reading has no witness here |
| cost and latency against `N` | `near`, `diffuse`, `reach` and `walk` at the profile's method (median of unprofiled runs, cProfile split, compiled share), the plane's occupancy bytes per item measured against the 120 B target, ingestion seconds per 1,000 items at the lander | **CIF-4**: an occupancy row above 300 B with integer ids; **CIF-11**: a Python share above 20% on any sentence (the profile's verdict, no compiled rewrite, holds while the share stays under it) |

### Stage 2: 10 GB (13.4 M chunks, 6 days of embedding, 29 GB on disk)

The last stage at which exact float16 chunk vectors fit beside everything else; so it decides
stage 3's vector plane. Everything of stage 1 again, with these added:

| measurement | what it produces | what would falsify the expectation |
|---|---|---|
| codes against exact answers | recall at 10 of int8, Matryoshka-256 float16 and int8, and the one-bit code, each unrescored and rescored by re-embedding the top `m` candidates (`m` = 20, 40, 80), against the float16 exact top ten, on the stage-1 battery; the certified share by VEC-1 on the rescored lists; the query latency of each | **CIF-3**: the one-bit code rescored at `m ≤ 80` below 0.95 on the titles and twins families; then the 100 GB default (D-1) is withdrawn and the owner chooses between a smaller corpus and more disk |
| an index | flat float16 search time at 13 M rows (the quantization note's 19.7 ms at 147 k scales linearly to about 1.8 s) against IVF at nprobes 32 and 128; the `N` at which flat search stops being fast enough beside a chat model's answer | **CIF-12**: IVF at nprobes 128 below 0.95 recall on the twins; then the index costs more than it saves and the design pays the flat scan or reads per source |
| the thresholds on the quotient | the quotient graph of the communities across sources: its `γ`, its eigengaps and its Hodge split, against the finest community's; whether a relaxation-time spacing of the ledger's rounds (SA-c) is weeks or months | **CIF-13**: a quotient gap below the finest community's (DYN-5 says it cannot be; a float instance that is, is an L3 finding) |
| attribution at power | SCL-4's `K` from the pilot's spread, and whether the rounds the stage affords reach it; the first growth readout | **CIF-14**: `K` beyond the rounds a year of weekly cuts affords; then the loop needs more questions per cut, which the cluster rule bounds |
| the compiled-rewrite verdict | the profile's six operations at 13 M rows, with the Python share; the spectral runs' wall time per community size | **CIF-11** as above |

### Stage 3: 100 GB (134 M chunks, 60 days of embedding, 86 GB on disk)

The configuration D-1 chose at stage 2: the one-bit code at the chunk grain, exact rescoring by
re-embedding, no full column; raw at `zstd -3` with `-19` in reserve; the compact graph. The full
catalogue and the daily drains, with the ledger's rounds spaced by the relaxation time stage 2
measured. Everything of stages 1 and 2 again, read now across three decades of `N`, with these
added:

| measurement | what it produces | what would falsify the expectation |
|---|---|---|
| macro behaviour against `N` across the decades | the six per-source curves and the quotient's, 1 GB to 100 GB: where each quantity's width crossed 10%, in `N` and in `d_min / ln N`, against the scale study's 1,000 to 2,000 and 0.9 to 1.3 | **CIF-7** at the last decade |
| the effective count | `N_eff` by CI-2 from the measured `ρ_w`, `ρ_b` over all six sources, and whether SCL-4's `K` is reached by the resolved rounds | **CIF-2**: `N_eff` at 100 GB no larger than at 10 GB; then adding text within the same six domains adds no independent signal, which CI-2 predicts, and only a seventh domain would |
| the crowding curve | unscoped and scoped recall over three decades on the same battery; the `N` at which unscoped recall on the twins falls under 0.5 | **CIF-9** |
| attribution of the six sources | the Shapley reading with its standard error at the protocol's `m`, the leave-one-out reading per source, and where they disagree, named as redundancy | **CIF-10**; **SAF-3** of the sibling note |
| the daily cost | chunks a day the drains bring, embedder minutes a day, disk growth a week against the cap; the date the cap is reached at the measured rate | **CIF-15**: growth past 1 GB a week on disk; then the drains are capped by source and the oldest versions of the history subset are retired first |

### What the stages are for, in one line each

Stage 1 says whether the sources connect and whether crowding is real at a million chunks; stage
2 says what a code costs against exact answers and settles the vector plane; stage 3 says whether
the macro quantities, the effective count and the attribution behave across three decades as CI-1,
CI-2 and the scale study predict.

## 7. The source catalogue

Every licence and term below was read on 2026-11-07; the citations are in the article. Sizes
are the sources' own counts or the measured ratios of §4 applied to them.

| source | licence and terms | size | update mechanism | what it exercises |
|---|---|---|---|---|
| **Wikipedia**, English, current article text and a subset of revision histories | text under CC BY-SA 4.0 and the GFDL (`dumps.wikimedia.org/legal.html`); the Wikimedia Foundation Terms of Use take precedence; some content is fair-use and is excluded at the item level where marked; automated clients must send a descriptive User-Agent with contact information (the User-Agent policy) or are refused | 7,260,766 articles (`Special:Statistics`); the current-articles multistream dump 27.0 GB bz2 (2026-11-07 listing), over 105 GB of XML, about 30 to 40 GB of prose by the measured ratio; the full history "multiple terabytes" uncompressed, in 7z parts (the first, 794 pages, 94 MB 7z against 2.6 GB bz2) | dump: `pages-articles-multistream` with its index, parts fetched by byte range; history: `pages-meta-history` parts for the chosen page ranges; stream: EventStreams `recentchange` and `revision-create` over SSE at `stream.wikimedia.org/v2/stream/`, resumable by `Last-Event-ID`, 3.2 English edits a second measured | the hyperlink graph (about 150 article links an article), version chains with dates on every page (the supersession and version generators), a velocity with many generations, bridges to arXiv and DOI works through citation templates |
| **OpenAlex**, works with abstracts, selected fields | CC0 1.0 (`LICENSE.txt` at the bucket root, "our data is CC0"); the snapshot is free, no account; the API is 10 requests a second without a key, cursor paging past the first page needs a free key (an account), a daily budget in dollars | 464,765,485 works in the 2026-10-14 jsonl manifest, 675.3 GB gzipped in 1,898 part files (1,453 B a record); 168.7 M works with abstracts, of which Mathematics 2.3 M, Computer Science 8.4 M, Physics and Astronomy 20.6 M (API counts) | snapshot: quarterly on the second Wednesday of January, April, July and October, on `s3://openalex/data/jsonl/works/`, parts by `updated_date`, streamed through a field filter and discarded (675 GB of transfer, nothing stored but the selection); API: the `works` endpoint for the daily delta by `from_updated_date` | the dated citation graph the scale study measured (135 references a work on average, 93% with at least one), topics as a partition (DYN-5), the OpenAlex–arXiv twin as SCL-3's redundancy witness |
| **arXiv**, metadata with abstracts | descriptive metadata including abstracts under CC0 1.0 (the API terms of use); e-prints themselves are not, and are not fetched; legacy APIs at most one request every three seconds on one connection | more than three million articles (arXiv's own figure); 3 M records at 1.5 kB are 4.5 GB of text | OAI-PMH at `oaipmh.arxiv.org/oai` (and the `export.arxiv.org/oai2` mirror, which answered when the primary timed out), `metadataPrefix=arXiv` with versions and licence per record, sets by group, archive and category, incremental by `from`, resumption tokens that expire daily; about 2,000 records a day | version chains with dates and no citations (the version generator alone), a nightly feed the loop registers from round by round |
| **Hacker News** | the official API (Firebase, `github.com/HackerNews/API`, documentation under the MIT licence) has no rate limit and no stated terms on the content; the Algolia search API allows 10,000 requests an hour an IP; Y Combinator's terms grant the content's licence to Y Combinator and no third party, and forbid scraping the site; the API is not the site, and the content carries no open licence | 50,408,507 items (`maxitem`); 9,300 comments and 850 stories a day measured; about 12 GB of text as threads | `maxitem` and `updates` on the Firebase API for the delta; `search_by_date` on Algolia for backfill, 1,000 items a request | a reply tree with minutes of latency, the fastest-moving source; links to Wikipedia and arXiv as explicit bridges; the thread as an item whose comments are blocks |
| **Stack Exchange**, math, physics, stats, cs, mathoverflow | user content under CC BY-SA (2.5 before 2011-04-08, 3.0 to 2018-05-02, 4.0 since), attribution to the question and the author required; the 2024-04-02 archive on `archive.org/details/stackexchange` is CC BY-SA 4.0 with no login; dumps after it are downloaded from a logged-in profile under terms that admit personal use and projects that do not train a large language model and reserve refusal on redistribution for that purpose; the API is 300 requests a day anonymous, 10,000 with a registered key, with a `backoff` field to honour (a violation was refused during the measurements) | per-site 7z archives of 2024-04-02: math 3.4 GB, physics 695.5 MB, stats 568.9 MB, mathoverflow 486.8 MB, cs 124.9 MB; the sites today: math 1.70 M questions, 2.24 M answers, 9.48 M comments; physics 249 k, 368 k, 1.63 M; stats 220 k, 220 k, 1.10 M; mathoverflow 169 k, 202 k, 1.11 M; cs 50 k, 59 k, 270 k; about 15 GB of text with edit history | dump: the 2024-04-02 archives (Posts, PostHistory, Comments, PostLinks); stream: the API's `questions`, `answers` and `comments` by `fromdate`, a few hundred a day across the five sites | answers and comments as a dated relation, edits as version chains (PostHistory), duplicate links as a second relation, the question-and-answer form the retrieval battery's queries come in |
| **Project Gutenberg**, English texts | public domain in the United States (the permission policy); the trademark may be kept or stripped for non-commercial use; a few thousand copyrighted items carry their own licences and are excluded by the catalogue's rights field; the main site is for human users, bulk access through the `robot/harvest` URL with a two-second wait or a mirror, and no more than about a hundred files a day from the main site | 79,712 catalogue rows, 78,461 texts, 63,115 in English (`pg_catalog.csv`); the sample's books 0.93 MB of text each, so 10,000 texts are about 9.5 GB | the catalogue CSV (public domain) for the selection, the harvest URL or an rsync mirror for the files; new texts arrive at tens a day and old ones are re-edited, which the catalogue's dates carry | long documents (a thousand chunks a book) with no dated relation and no evolution of interest: the null for the velocity instruments and the control for the cores (a book's chunk graph has a trivial core); bridges to Wikipedia articles about the works |

Dropped: nothing outright. Two sources carry conditions the owner decides on (D-2, D-3 in §8):
Hacker News, whose content has no open licence though its API is official and unlimited; and
Stack Exchange's post-2024 official dumps, which need the owner's account and acceptance of
terms. Both default to the path that needs no account: the official API for Hacker News, read
and held locally and never republished; the 2024-04-02 archive and the API for Stack Exchange.
`[ESTABLISHED: the terms as read; the verdicts INFERENCE]`

## 8. The decisions for the owner, priced

| id | decision | default | the price of the default | the alternatives, priced |
|---|---|---|---|---|
| D-1 | the vector plane at 100 GB | one-bit codes at the chunk grain, exact rescoring by re-embedding the top 40, no full column; 86 GB on disk | 1.5 s a query for the rescoring (against 20 ms today); recall of the rescored list to be measured at stage 2 and withdrawn by CIF-3 | stop at 33 GB of text with exact float16 vectors (every answer certifiable by VEC-1, a third of the catalogue, six domains still); or an external disk (exact at 100 GB is 280 GB: a 1 TB drive, and the 25 GB rule moot); or int8-256 up to 85 GB of text (recall unmeasured) |
| D-2 | Hacker News | included through the official API, held locally, never republished | the one source with no open licence on its content; the fastest-moving source and the thread grain depend on it | drop it: 12 GB and 16 M chunks returned to the other sources; the reply tree and the minutes-scale velocity lost; five domains in CI-2 instead of six |
| D-3 | Stack Exchange's dumps | the 2024-04-02 archive (CC BY-SA 4.0, no account) plus the anonymous API for the delta | two and a half years of posts arrive through the API at 300 requests a day, about 30,000 posts a day of backfill, months for math | the owner's account and the current official dumps under their terms (personal use, no LLM training: compatible with this use); or a registered API key (10,000 requests a day) |
| D-4 | the embedder's sixty days at 100 GB | this machine, one stream, at idle hours | sixty days of calendar at the hours the chat model sleeps; the vectors are keyed by content and embedder (MEM-8), so a pause loses nothing | a second machine embedding the same model (the vectors are portable; the plane is keyed by `(model, dim)`); or the item grain only, 36 M vectors, 16 days, no chunk-level retrieval for long items; or 2,400-character chunks, half the count, a different retrieval unit (the σ sweep's precedent) |
| D-5 | OpenAlex access | the quarterly snapshot streamed through a field filter, no account, 675 GB of transfer a quarter | a quarter's staleness between snapshots; 675 GB of transfer each time (a few hours at 50 MB/s) | a free API key (an account with an email) for cursor paging and the daily delta at 30 requests a second |
| D-6 | the Wikipedia history subset | 5 GB of text: the revisions of the pages in the communities the other sources bridge to, sampled monthly | a tenth of the Wikipedia budget on versions rather than new articles | the full history of fewer pages (a thousand pages, every revision, the velocity at its finest grain); or none, and the version generator runs on arXiv and Stack Exchange alone |
| D-7 | the raw compression level | `zstd -3`, 35 GB at 100 GB | 7 GB that `-19` would save, at ten times the compressor's time (minutes, not hours) | `-19` from the start |

## Parked decisions

| id | decision | default recorded | re-entry condition |
|---|---|---|---|
| CI-a | the chunk size for the corpus | the live chunker's 1,200 / 150 | the σ sweep's result, or D-4's halving |
| CI-b | the community partition the quotient reads | OpenAlex topics where a source has them, Louvain over the per-source relation where it does not | a partition the sorts cannot name (GD-d) |
| CI-c | the rescoring `m` | 40 | stage 2's recall curve against `m` |
| CI-d | the ledger's round spacing | one relaxation time of the quotient (SA-c) | a quotient whose `γ` drifts across cuts by more than its band |
| CI-e | the mix of §4.1 | as tabled | a source whose licence changes, or D-2 and D-3 |

## Falsifiers

- **CIF-1 (the thread rate):** Hacker News threads chunk at more than 2,000 chunks per MB. Then
  its 12 GB is 24 M chunks, not 16 M, and the vectors' line in §4.4 grows by 1 GB.
- **CIF-2 (the sources do not connect):** cross-source bridges at or below the rewiring null, or
  `ρ_b` within the bootstrap band of `ρ_w`. Then CI-2 gives no gain from these six domains at this
  scale, and the catalogue needs domains that connect.
- **CIF-3 (the code does not rescore):** the one-bit code rescored by re-embedding at `m ≤ 80`
  keeps under 0.95 of the exact top ten on the titles and twins families at stage 2. Then D-1's
  default is withdrawn.
- **CIF-4 (the compact graph is not compact):** an occupancy row above 300 B or an edge above 24 B
  measured at stage 1. Then §4.3's 31 GB is 60 or more and the cap bites at 100 GB.
- **CIF-5 (the instance reaches outside):** a write under anything but `instances/corpus/`, or a
  read of the default instance's sources. SAF-5; the loader's refusal is the guard.
- **CIF-6 (a batch does not converge):** a batch interrupted and re-run that lands a different
  state. ING-11 says it cannot; a difference is a transcription defect in the lander.
- **CIF-7, CIF-8 (the thresholds mispredict on another relation kind):** stated in §6.
- **CIF-9 (crowding is not the failure mode):** unscoped recall flat across three decades of `N`.
- **CIF-10 (no redundancy witness):** both twins necessary by leave-one-out.
- **CIF-11 (the verdict flips):** a sentence whose Python share exceeds 20% at 13 M rows.
- **CIF-12 to CIF-15:** stated in §6.

## Open questions

- Which partition is the quotient's at the chunk grain, where a source's relation is on items and
  the chunks of one item are one block by construction: the item's community, or a clustering of
  the chunks' vectors?
- The re-embedding rescoring makes a query's cost depend on `m` and on the embedder's queue; should
  the sentence algebra carry `m` as a dial beside `beta`, or the precedent fix it?
- A Hacker News thread is an item whose blocks arrive over hours; is the thread's version chain
  one version a drain, or one per comment?
- Does the effective count's `ρ_b` need the lag structure (a rise in arXiv a month before one in
  Hacker News is a bridge in time), and is the right reading the cross-correlation at the best lag
  or the Hodge potential of the lead-lag flow?

## Cross-references

**Formal (cited):** `formal/Palace/Scale.lean` (SCL-1 to SCL-3), `formal/Palace/Dynamics.lean`
(DYN-1, DYN-3 to DYN-6), `formal/Palace/Cosine.lean` (VEC-1: `abs_cosine_round16_sub_le`,
`top_eq_of_margin`, `top_unchanged`), `formal/Palace/Ingress.lean` (ING-5, ING-9, ING-11, ING-13).

**Code (read, unchanged):** `core/kernel/ingest/chunk.py` (the chunker the counts use);
`core/stores/vectorstore.py` (the Lance schema, float16); `core/stores/plane.py` (the occupancy
DDL); `core/stores/reference_edges.py` (the edge DDL); `core/kernel/config/loader.py`
(`InstanceConfig`, `namespaces_of`); `eval/scale/` (the macro method); `eval/quantization_bench.py`
(the codes' bench); `eval/predictions/` (the ledger and its scorer); `scheduler/queue.py` (the
job rate was read from its table).

**Design:** dn-scale-and-attribution §2 to §6, SA-a to SA-e, SAF-1 to SAF-6; dn-graph-dynamics
§4, §5, DYN-5; dn-prediction-ledger G1 to G8; dn-ingress D3 to D5; dn-ingress-language E2, E3,
E8, E10, ING-13; vector-membership-store A4, A4.5; docs/tracks/deployed-instances.md DI-2;
docs/experiments/scale-study-2026-11-07.md; docs/experiments/vector-quantization-2026-10-30.md;
docs/experiments/profile-2026-11-06.md; docs/experiments/embedder-bench-2026-10-28.md;
`papers/2026-11-07-corpus-instance/paper.tex` (the article, with the references).
