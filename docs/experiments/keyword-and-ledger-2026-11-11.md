---
type: experiment-report
experiment: keyword-and-ledger
runs: 3
status: complete
started: 2026-11-11
links:
  - docs/experiments/keyword-and-ledger-2026-11-11.json     # the numbers below, as data
  - eval/stress_battery.py                                  # the harness that produced every table
  - docs/design-notes/dn-two-phase-ingestion.md             # the lexical index (D1, D2, §7.1)
  - docs/experiments/corpus-stage1-2026-11-07.md            # the instance measured
  - papers/2026-11-11-keyword-and-ledger/paper.tex          # the article
---

# Keyword search and ledger lookups on the corpus instance, before and after (2026-11-11)

**Question.** On the corpus instance at stage 1, a keyword query took seconds to tens of seconds
and the producers of one digest about two and a half seconds. Do kept per-class statistics with
one scoring statement, and a ledger table keyed by output hash, remove those costs, at what price
for a landing, and with exactly the answers the store gave before? Nothing here touched an
instance: every number is from copy-on-write clones of the corpus instance's data directory.

## Method

The harness is `eval/stress_battery.py`. It never opens the instance's files for writing: each
part clones what it needs with `cp -c` into a scratch directory, and a part that writes gets fresh
clones a run. The source was the corpus instance's data at stage 1: 400,274 items; 1,369,944
lexical units, every one current and observed; 117,975,818 postings; 387,838 attestations, every
one a `capture` naming one output hash.

Three runs, the same command and source:

1. **before**, main at f969904e (the change's parent; its tree extracted with `git archive`, its
   environment synced from the same lock file), every part;
2. **after**, the branch at 2bedbcf1, every part;
3. **after, final**, the branch at f1a1f49c, the keyword and ledger parts again: between the two
   the sum's per-term aggregates became filtered (`FILTER (WHERE ...)` in place of a `CASE`) and
   the ledger's lookups stopped sorting the hashes they are asked; the landing, the single
   landing and the control exercise no changed line, so their after figures are run 2's.

The parts:

- **keyword**: 16 title queries, the ten of the earlier study's subset (its query ids 0, 3, 6, 8,
  11, 14, 17, 20, 23 and 25, named L0 to L25 here) and six drawn independently (S0 to S5), from 1
  to 19 distinct terms and from 32 to 6,503,751 postings, named by their sizes and never by their
  text. `search(text, k=10)` with the class filter the store always applies
  (`classes=[observed]`) and with none; the store's call shape, `scores(text,
  classes=[observed], paths=P)` and `search(..., paths=P)`, with P 400 random item paths, for
  five queries. Warm: one process, the first pass reported apart, then three passes, each query's
  median. Fresh process: three repetitions, a new process each, for three queries.
- **ledger**: `producers_of`, and `already_attested` and `attested_by` through
  `core/ingest/landing.py`, for five digests the ledger holds and two it does not, the first call
  apart then five; `producers_by_output` and `attested_batch` for 2,000 held and 50 absent digests.
- **landing**: 2,000 synthetic items through `Writer.land`, batched and lazy (the corpus runner's
  call), three consecutive batches in a fresh process, three processes, each on fresh clones of the
  lexical store, the catalog, the ledger, the versions and the vector directory. A synthetic item
  is a real corpus item (a seeded draw) with one first line naming the run and the item: a new
  digest, a real item's text, chunks and terms. **single**: three items effect by effect
  (`batch=False`), the path of every lane but the corpus runner's.
- **pending**: `derive.pending` over the clones, the first call apart then three. No line of the
  change reads it: it is the control for the machine between the runs.
- **not run**: the whole-stratum load of a sentence admitting the dialogue stratum, which needs
  tens of gigabytes on the whole corpus.

Conditions: Apple M2 Pro, 12 cores, 32 GB, shared with other work. The one-minute load average is
read beside every timing (the ranges below), BLAS is capped at four threads, and every process
ends itself above 3.8 GB resident. Python 3.15.2, SQLite 3.54.1. The corpus's lexical file
predates the store's record of its tokenizer, so every run opens it with LEGACY's, which made it;
under the current tokenizer the store refuses it until it is re-derived.

## Results

Every answer the battery took before the change is the answer it took after it, scores compared
as the bits of their doubles: the 65 it keeps (the four keyword shapes' top tens with their
scores and the path scores, 42; the producer sets and lists, 23), and the six fresh processes'
answers, which equal the warm ones.

### Keyword search

| shape (warm medians) | before | after | load, before / after |
|---|---|---|---|
| title query, class filter, median of 16 (min-max) | 14.2 s (1.47-33.4 s) | 1.20 s (0.1 ms-5.87 s) | 2.8-7.4 / 2.2-11.3 |
| title query, no filter, median of 16 | 9.42 s (0.98-23.2 s) | 1.16 s (0.1 ms-5.70 s) | 2.0-3.2 / 2.5-5.6 |
| the store's shape, `scores`, 400 paths, median of 5 | 5.47 s (1.22-18.9 s) | 5.5 ms (1.9-12.1 ms) | 1.9-4.5 / 2.5 |
| the store's shape, `search`, 400 paths, median of 5 | 8.43 s (2.33-15.7 s) | 4.6 ms (1.8-11.1 ms) | 3.1-4.2 / 2.5 |

Per query (seconds, each query's warm median; the path shapes' after columns in milliseconds):

| query | terms | postings | class filter, before | after | no filter, before | after | `scores` with paths, before | after (ms) | `search` with paths, before | after (ms) |
|---|---|---|---|---|---|---|---|---|---|---|
| L0 | 1 | 108 | 1.7 | 0.0001 | 0.976 | 0.0001 | 1.22 | 1.9 | 2.69 | 1.8 |
| L3 | 2 | 26,949 | 5.69 | 0.0215 | 1.81 | 0.0228 |  |  |  |  |
| L6 | 2 | 191,032 | 5.95 | 0.158 | 2.1 | 0.164 | 2.25 | 2.9 | 2.33 | 2.6 |
| L8 | 10 | 498,437 | 18.5 | 0.607 | 9.31 | 0.587 |  |  |  |  |
| L11 | 5 | 1,337,195 | 9.3 | 1.02 | 6.26 | 0.976 | 5.47 | 5.5 | 8.43 | 4.6 |
| L14 | 10 | 1,860,446 | 17 | 1.8 | 11.1 | 1.75 |  |  |  |  |
| L17 | 7 | 2,671,741 | 13.8 | 2.05 | 9.53 | 1.99 | 7.63 | 7.6 | 15.4 | 6.6 |
| L20 | 9 | 3,801,316 | 17.8 | 2.86 | 12 | 2.77 |  |  |  |  |
| L23 | 14 | 4,966,503 | 25 | 4.15 | 17.2 | 4.01 | 18.9 | 12.1 | 15.7 | 11.1 |
| L25 | 19 | 6,503,751 | 33.4 | 5.87 | 23.2 | 5.7 |  |  |  |  |
| S0 | 1 | 32 | 1.47 | 0.0001 | 1.02 | 0.0001 |  |  |  |  |
| S1 | 3 | 1,224,831 | 6.25 | 0.824 | 4.67 | 0.787 |  |  |  |  |
| S2 | 4 | 890,406 | 7.05 | 0.7 | 4.81 | 0.667 |  |  |  |  |
| S3 | 9 | 1,378,417 | 14.6 | 1.38 | 9.68 | 1.34 |  |  |  |  |
| S4 | 12 | 3,283,060 | 21 | 2.8 | 14.3 | 2.75 |  |  |  |  |
| S5 | 17 | 3,338,954 | 27.4 | 3.42 | 18.7 | 3.36 |  |  |  |  |

The fresh process, three repetitions a query (class filter, then the store's `scores` shape):

| query | before | after | peak resident, before / after |
|---|---|---|---|
| L0, class filter | 1.46-1.61 s | 0.5 ms | 71 / 69 MB |
| L11, class filter | 9.09-10.9 s | 0.92-0.94 s | 447 / 73 MB |
| L23, class filter | 24.1-24.4 s | 3.95-3.97 s | 468 / 74 MB |
| L0, `scores` with 400 paths | 1.21-1.22 s | 2.8-4.4 ms | 71 / 71 MB |
| L11, `scores` with 400 paths | 5.45-5.46 s | 6.7-8.5 ms | 71 / 71 MB |
| L23, `scores` with 400 paths | 15.1-15.2 s | 15.3-15.6 ms | 71 / 70 MB |

The class-filtered queries of the final run met a load of 6.7 to 11.3 from another job for their
second half (L17 to S5); the unfiltered shape, which scores the same units here (every unit is
observed), ran at 2.5 to 5.6 and gives 1.16 s against 1.20 s. A free query still reads every
posting of its terms: its time follows them, about 0.9 µs a posting (5.87 s for L25's 6.5
million), and the cost of a term no longer depends on the units it is not in. The memory of a
free query fell with the Python dictionary of every scored unit, which the statement no longer
builds.

### The ledger

| lookup (warm medians) | before | after |
|---|---|---|
| `producers_of`, one digest (7 digests, 2 absent) | 2.47 s | 7 µs (first call 10 µs) |
| `already_attested` through the landing | 2.48 s | 8 µs |
| `attested_by` through the landing | 2.48 s | 8 µs |
| `producers_by_output`, 2,050 digests | 304 ms | 5.9 ms |
| `attested_batch`, 2,050 digests | 305 ms | 6.0 ms |

Load 2.1-3.2 before, 2.5-3.7 after.

### The landing

| 2,000 items a batch, three processes | before | after |
|---|---|---|
| batches 1 and 2, seconds, median (min-max) | 10.40 (10.04-11.32) | 10.64 (9.16-11.04) |
| items a second, batches 1 and 2, median | 192 | 188 |
| the lexical stage (`land_many`), batches 1 and 2 | 8.83 s (8.52-9.82) | 9.38 s (7.85-9.80) |
| the ledger's lookup for the batch (`producers_by_output`) | 0.30-0.74 s | 5-9 ms |
| the batch's 2,000 appends | 0.05-0.06 s | 0.11 s |
| batch 0, seconds, median | 16.96 | 11.87 |
| peak resident | 373-376 MB | 374-378 MB |
| load | 2.2-2.8 | 3.4-6.3 |
| three items effect by effect | 23.1 s (7.7 s an item) | 0.082 s (0.027 s an item) |

The units landed are the same in both runs, batch for batch (5,438 to 7,626). The statistics'
upkeep sits inside the lexical stage: its median rose 0.55 s, at a load one to four higher, which
is within the spread of the stage itself; the ledger's lookup saved 0.3 s to 0.7 s a batch, and
the trigger's rows added 27 µs an append. Batch 0 is not comparable: after the change the first
open counted the statistics, which read the file, so batch 0 met a file the cache held. Effect by
effect, the three passes over the ledger an item were 99.4% of the time; they are now seeks.

### The control and the migrations

`derive.pending`, untouched by the change, took 2.24 s warm before and 2.33 s after (first calls
7.40 s and 5.79 s, the clone's file cache cold), so the two runs met the same machine within 4%.
The first call's 7.40 s on a cold file matches the 7.2 s the stage-1 record has for it, where 2.0
to 2.3 s were measured warm.

A store from before the change migrates on its first open, once. Counting the lexical statistics
of the 1,369,944 units took 114.5 to 121.6 s (six opens of fresh clones, cold files) and added
29.6 MB to the 4.61 GB file (`term_stats`, 1,053,985 rows). The ledger's table took 1.8 to 2.7 s
and added 64.4 MB to the 313 MB file, 166 B a record.

## What the code showed

- SQLite 3.54.1's `sum()` and `total()` compensate their rounding, so a sum they take over the
  same values in the same order is not the store's left-to-right sum (1 + 2^-53 + 2^-53 gives
  1 + 2^-52 against 1). The statement writes the sum out in the terms' order, each term the unit
  lacks adding 0.0, which leaves a positive double as it is; with that the scores are identical,
  where a statement that sums with `sum()` is not.
- Without planner statistics, the paths shape was driven from the class's index and visited every
  current unit of the class for each path; the statement names `units_path`.
- SQLite parses `a + b + ...` as a tree as deep as its terms and refuses a depth over 1,000, so
  the written-out sum stops at 500 terms; a longer query's weights are read out of the statement
  in the terms' order and summed in Python.
- The statement replaced in `producers_by_output` filled a temporary table, which in the ledger's
  transaction mode opened a transaction that kept a shared lock on the file after the call; the
  lookups now only read.
- An attestation sorts its output hashes and does not remove repeats, so the side table keeps one
  row for each element (its position in the key), and `producers_by_output` lists a record once
  for each time it names a hash, as before.
- Kept by row triggers instead of in the landing's transaction, the statistics would need one
  upsert a posting of each unit whose currency moves (86 a unit on average here) rather than one
  a distinct (term, class) pair of the batch; the upkeep is batched in the transaction, and only
  the guard is a trigger.

## Caveats

- One run before and one after (the final keyword and ledger parts a third), on a machine shared
  with other work; read the load beside each figure. The landing's after run met a load one to
  four higher than its before run.
- The corpus holds one class, so the clearance rule's sums are over one row here; the generated
  stores of the property tests hold four.
- Every file was in the cache but for each part's first query on a fresh clone; a file larger than
  memory was not measured.
- The corpus's lexical file is LEGACY's; the current tokenizer re-derives it before it scores it,
  and that re-derivation lands every unit again (with its statistics).
- Not run: the whole-stratum load of a sentence admitting the dialogue stratum.

## Reproduce

    uv run python -m eval.stress_battery --source <the instance's data directory> \
        --scratch <a scratch directory> --out <record.json> --queries <titles.json> \
        --tokenizer legacy --passes 3 --fresh 3 --fresh-qids L0,L11,L23 \
        --path-qids L0,L6,L11,L17,L23 --runs 3

`<titles.json>` is a JSON list of `{"qid", "text"}`; without it the battery draws titles from the
store. The before run used main's tree at f969904e with this harness beside it.
