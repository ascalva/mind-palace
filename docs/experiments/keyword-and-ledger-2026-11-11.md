---
type: experiment-report
experiment: keyword-and-ledger
runs: 5
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

The harness is `eval/stress_battery.py`. It never opens the instance's files for writing. It
clones what it needs with `cp -c` into a scratch directory and first prepares a source of its
own: clones of the stores, the lexical index and the ledger opened once by the code under test,
which is where a store from before the change is migrated, once, timed with the load beside it.
Every part then clones the prepared files again, so each part of each code starts from files the
cache has not read, and a part that writes gets fresh clones a run. The source was the corpus
instance's data at stage 1: 400,274 items; 1,369,944 lexical units, every one current and
observed; 117,975,818 postings; 387,838 attestations, every one a `capture` naming one output
hash.

Two runs, the same command and source:

1. **before** (run 4), main at f969904e (the change's parent; its tree extracted with `git
   archive`, its environment synced from the same lock file, this harness beside it), every part;
2. **after** (run 5), the branch at b61c0ca0, every part. The branch's later commits change code
   on one path no run took: a migration that fails for a reason other than another connection's
   lock is rolled back and the store answers as before the change, where at b61c0ca0 the open
   and every query raised unless the file was read-only.

Three earlier runs (1 to 3), with an earlier version of the harness, are at the end of this
record and in the JSON: they gave the same answers, and where their figures differ the reason is
stated there.

The parts:

- **keyword**: 16 title queries, ten from the query set of an earlier, unpublished study of the
  stores (named L0 to L25 by their places in it) and six drawn independently (S0 to S5), from 1
  to 19 distinct terms and from 32 to 6,503,751 postings, named by their sizes and never by their
  text. `search(text, k=10)` with the class filter the store always applies
  (`classes=[observed]`) and with none; the store's call shape, `scores(text,
  classes=[observed], paths=P)` and `search(..., paths=P)`, with P 400 random item paths, for
  five queries. Warm: one process, the first pass reported apart, then five passes, each query's
  median, every pass's wall time, processor time and load kept. Fresh process: three
  repetitions, a new process each, for three queries.
- **ledger**: `producers_of`, and `already_attested` and `attested_by` through
  `core/ingest/landing.py`, for five digests the ledger holds and two it does not, the first call
  apart then five; `producers_by_output` and `attested_batch` for 2,000 held and 50 absent digests.
- **landing**: synthetic items through `Writer.land`, batched and lazy (the corpus runner's call),
  in three fresh processes, each on fresh clones of the lexical store, the catalog, the ledger,
  the versions and the vector directory: three batches of 2,000 new items, then a batch landing
  the third batch's 2,000 paths again with other bytes, which replaces every unit that batch made
  current. The statistics' upkeep (`LexicalStore._keep`) is timed on its own where the code has
  one, and the kept class statistics are checked against a count after the four batches. A
  synthetic item is a real corpus item (a seeded draw) with one first line naming the run and the
  item: a new digest, a real item's text, chunks and terms. **single**: three items effect by
  effect (`batch=False`), the path of every lane but the corpus runner's.
- **pending**: `derive.pending` over the clones, the first call apart then five. No line of the
  change reads it: it is the control for the machine between the runs.
- **concurrent**: a lexical file from before the change (the source's own, not the prepared one)
  opened by one process and, 5 s later, by a second that asks one query (L0, class filter): what a
  reader meets while the first open migrates the file.
- **not run**, each named in the JSON with its reason: the whole-stratum load of a sentence
  admitting the dialogue stratum (tens of gigabytes on the whole corpus; the stage-1 record has
  4.3 to 4.7 GB at 10,000 items); the test that a commit's cut holds a citation edge (the corpus
  instance has no citation store); and the pending mask of a sentence's nodes (empty when nothing
  is pending, and `derive.pending` finds 0 items here).

Conditions: Apple M2 Pro, 12 cores, 32 GB, shared with other work. The one-minute load average is
read beside every timing (the ranges below are of that field), BLAS is capped at four threads,
and every process ends itself above 3.8 GB resident. Python 3.15.2, SQLite 3.54.1. The corpus's
lexical file predates the store's record of its tokenizer, so every run opens it with LEGACY's,
which made it; under the current tokenizer the store refuses it until it is re-derived.

## Results

Every answer the battery took before the change is the answer it took after it, scores compared
as the bits of their doubles: the 65 it keeps (the four keyword shapes' top tens with their
scores and the path scores, 42; the producer sets and lists, 23), the 18 fresh processes'
answers, which equal the warm ones, and the concurrent part's answer. The three earlier runs gave
the same 65.

### Keyword search

| shape (warm medians) | before | after | load, before / after |
|---|---|---|---|
| title query, class filter, median of 16 (min-max) | 14.4 s (1.49-34.1 s) | 1.20 s (0.08 ms-6.17 s) | 3.0-5.6 / 2.7-3.8 |
| title query, no filter, median of 16 | 9.58 s (0.97-23.3 s) | 1.16 s (0.07 ms-5.78 s) | 2.2-5.0 / 2.7-3.7 |
| the store's shape, `scores`, 400 paths, median of 5 | 5.41 s (1.19-15.1 s) | 5.9 ms (1.9-12.4 ms) | 2.2-3.0 / 2.8 |
| the store's shape, `search`, 400 paths, median of 5 | 5.39 s (1.20-15.0 s) | 4.7 ms (1.8-11.5 ms) | 1.9-2.6 / 2.8 |

Per query (each query's warm median in seconds, the before columns with the range of their five
passes; the path shapes' after columns in milliseconds):

| query | terms | postings | class filter, before | after | no filter, before | after | `scores` with paths, before | after (ms) | `search` with paths, before | after (ms) |
|---|---|---|---|---|---|---|---|---|---|---|
| L0 | 1 | 108 | 1.50 (1.49-1.52) | 0.0001 | 0.969 (0.966-0.986) | 0.0001 | 1.19 (1.18-1.22) | 1.9 | 1.20 (1.20-1.21) | 1.8 |
| L3 | 2 | 26,949 | 2.92 (2.91-2.93) | 0.0223 | 1.85 (1.81-1.86) | 0.0221 |  |  |  |  |
| L6 | 2 | 191,032 | 3.36 (3.34-3.38) | 0.165 | 2.12 (2.11-2.16) | 0.169 | 2.25 (2.24-2.29) | 3.2 | 2.25 (2.24-2.26) | 2.7 |
| L8 | 10 | 498,437 | 15.1 (15.1-15.2) | 0.631 | 9.94 (9.54-10.1) | 0.608 |  |  |  |  |
| L11 | 5 | 1,337,195 | 9.54 (9.23-9.71) | 1.04 | 6.30 (6.22-6.58) | 0.994 | 5.41 (5.39-5.43) | 5.9 | 5.39 (5.37-5.43) | 4.7 |
| L14 | 10 | 1,860,446 | 17.5 (17.4-17.5) | 1.84 | 11.4 (11.3-11.4) | 1.77 |  |  |  |  |
| L17 | 7 | 2,671,741 | 13.7 (13.4-13.9) | 2.08 | 9.52 (9.49-9.57) | 1.99 | 7.61 (7.59-7.61) | 7.7 | 7.61 (7.60-7.71) | 6.7 |
| L20 | 9 | 3,801,316 | 26.1 (17.9-33.1) | 2.89 | 12.1 (12.1-12.1) | 2.77 |  |  |  |  |
| L23 | 14 | 4,966,503 | 32.3 (30.0-38.6) | 4.22 | 17.3 (17.3-17.3) | 4.02 | 15.1 (15.0-15.1) | 12.4 | 15.0 (15.0-15.1) | 11.5 |
| L25 | 19 | 6,503,751 | 34.1 (33.9-34.4) | 6.17 | 23.3 (23.2-23.7) | 5.78 |  |  |  |  |
| S0 | 1 | 32 | 1.49 (1.45-1.50) | 0.0001 | 0.990 (0.985-0.999) | 0.0001 |  |  |  |  |
| S1 | 3 | 1,224,831 | 6.37 (6.34-6.41) | 0.880 | 4.55 (4.52-4.62) | 0.789 |  |  |  |  |
| S2 | 4 | 890,406 | 7.14 (7.07-7.21) | 0.707 | 4.81 (4.78-4.82) | 0.669 |  |  |  |  |
| S3 | 9 | 1,378,417 | 15.2 (15.0-15.5) | 1.37 | 9.65 (9.63-9.65) | 1.33 |  |  |  |  |
| S4 | 12 | 3,283,060 | 20.8 (20.5-26.0) | 2.95 | 14.3 (14.2-14.3) | 2.79 |  |  |  |  |
| S5 | 17 | 3,338,954 | 27.8 (27.6-28.7) | 3.49 | 18.6 (18.6-18.7) | 3.42 |  |  |  |  |

The fresh process, three repetitions a query (class filter, then the store's `scores` shape):

| query | before | after | peak resident, before / after |
|---|---|---|---|
| L0, class filter | 1.41-1.43 s | 0.50-0.53 ms | 70-71 / 68 MB |
| L11, class filter | 8.77-8.85 s | 0.95-0.96 s | 447-448 / 72-73 MB |
| L23, class filter | 24.0-24.2 s | 4.03-4.04 s | 468-469 / 73 MB |
| L0, `scores` with 400 paths | 1.19-1.21 s | 2.8-3.0 ms | 70-72 / 70-71 MB |
| L11, `scores` with 400 paths | 5.40-5.42 s | 6.9-7.2 ms | 71 / 71 MB |
| L23, `scores` with 400 paths | 15.0-15.1 s | 14.1-14.3 ms | 71 / 71 MB |

A single pass can stray from its query's median, and the load average does not show when. Of the
before run's 210 warm passes of 0.1 s or more, two took 1.2 times their query's median or more (at
most 1.27 times), and ten took 1.1 to 1.75 times their own processor time, every one under the
class filter (L20, L23 and S4) at one-minute loads of 3.1 to 5.6: those passes waited. The medians
of L20 and L23 under the class filter (26.1 s and 32.3 s) carry the waits; the medians of their
processor times are 18.9 s and 26.8 s. The after run's 130 passes of 0.1 s or more were all within
1.08 times their medians, and none waited.

A free query still reads every posting of its terms: its time follows them, under 1 µs a posting
(6.17 s for L25's 6.5 million under the class filter), and the cost of a term no longer depends on
the units it is not in. The memory of a free query fell with the Python dictionary of every scored
unit, which the statement no longer builds; the paths shape's memory did not move.

### The ledger

| lookup (warm medians) | before | after |
|---|---|---|
| `producers_of`, one digest (7 digests, 2 absent) | 2.43 s | 8.2 µs (first calls 0.27-0.55 ms) |
| `already_attested` through the landing | 2.40 s | 8.5 µs |
| `attested_by` through the landing | 2.42 s | 8.1 µs |
| `producers_by_output`, 2,050 digests | 292 ms | 6.4 ms (first call 295 ms) |
| `attested_batch`, 2,050 digests | 290 ms | 6.5 ms |

Load 1.9-3.6 before, 2.9 after. The first calls after the change read the table from a file the
cache had not read: a digest's first seek took 0.27 to 0.55 ms, and the first batch 295 ms, as
long as the pass over the records it replaced; from the second call the batch takes 6.4 ms.

### The landing

| three processes, each 3 batches of 2,000 new items, then 1 replacing the third's | before | after |
|---|---|---|
| batches 1 and 2, seconds, median (min-max) | 10.45 (9.41-11.50) | 11.13 (9.75-12.15) |
| items a second, batches 1 and 2, median | 192 | 180 |
| the lexical stage (`land_many`), batches 1 and 2 | 8.97 s (7.98-10.01) | 9.78 s (8.36-10.86) |
| the upkeep (`_keep`), batches 1 and 2 |  | 0.39 s (0.30-0.53), 3.1-4.8% of the batch |
| the replacing batch, seconds, median (min-max) | 9.88 (8.95-10.19) | 10.93 (10.81-11.61) |
| its lexical stage | 8.29 s (7.44-8.66) | 9.63 s (9.51-10.30) |
| its upkeep |  | 0.76 s (0.74-0.85), 6.9-7.3% of the batch |
| batch 0, seconds, median (min-max) | 17.13 (15.74-17.30) | 18.26 (16.87-19.02) |
| the ledger's lookup for a batch (`producers_by_output`) | 0.30-0.42 s (batch 0: 0.68-0.75 s) | 24-88 ms (batch 0: 0.21-0.23 s) |
| a batch's 2,000 appends | 0.050-0.059 s | 0.11-0.14 s (batch 0: 0.17-0.19 s) |
| kept class statistics against a count after the four batches |  | equal in 3 of 3 processes |
| peak resident | 374-380 MB | 366 MB |
| load | 2.1-3.1 | 2.7-3.9 |
| three items effect by effect | 22.8 s (7.6 s an item) | 0.48 s (0.16 s an item) |

The units landed are the same in both runs, batch for batch (5,438 to 7,626 a batch of new items;
a replacing batch writes 6,584 to 7,371 and moves the currency of twice as many). The landing
costs more after the change: a batch of new items 0.69 s at the median (7%), a replacing batch
1.04 s (11%), batch 0 1.12 s (7%), at a one-minute load 0.5 to 1 higher. Item for item (the same
items in the same process number on each code), the lexical stage rose 0.4 to 1.3 s for five of
the six batches of new items and fell 0.9 s for the sixth, and rose 1.3 to 2.1 s for the three
replacing batches. The upkeep, timed on its own, is 0.30 to 0.53 s a batch of new items and 0.74
to 0.85 s a replacing batch, which moves the statistics for the units it supersedes as well as
for those it makes current; the trigger's rows add 28 to 43 µs an append (56 to 73 µs in a
process's first batch, the table not yet read); the ledger's lookup saves 0.23 to 0.52 s a batch.
The rest of the lexical stage's rise is not attributed: the upkeep's timer covers its statements,
not the commit that writes the pages they changed, and the after run met the higher load. Effect
by effect, the nine passes over the ledger were 99.4% of the time (22.7 s); after the change the
ledger's lookups take 2 ms of the 0.48 s, on files the cache had not read.

### The control

`derive.pending`, untouched by the change, took 2.19 s warm before (2.17-2.21) and 2.22 s after
(2.15-2.31), and 7.54 s and 7.47 s at its first call, each on a clone of the prepared files the
cache had not read (after the change the prepared file was migrated already, so the part's open
read nothing). The two runs met the same machine within 2%, at one-minute loads of 2.1 to 2.3
before and 3.6 to 3.8 after.

### The migrations

A store from before the change migrates on its first open, once. Counting the lexical statistics
of the 1,369,944 units took 126.0 s in run 5's prepare step (a clone the cache had not read,
one-minute load 2.0) and added 29.6 MB to the 4.61 GB file (`term_stats`, 1,053,985 rows); the
concurrent part's first open counted them in 119.3 s (load 3.8). The ledger's table took 2.68 s
(load 3.0) and added 64.4 MB to the 313 MB file, 166 B a record. The earlier runs' migrations
are below, with their loads.

### A reader while the first open migrates

| the concurrent part | before | after |
|---|---|---|
| the first process's open | 1.1 ms (nothing to migrate) | 119.3 s (the count) |
| the second process's open, 5 s later | 0.66 ms | 0.47 ms |
| its query (L0, class filter) | 16.7 s | 1.37 s |
| one-minute load | 2.3-2.5 | 3.7-3.8 |

After the change the second process opened at once while the first held the write lock, counted
its query's statistics from the units (the store had none counted yet), and answered as the code
before did: the same answer as the keyword part's, in 1.37 s, while the first process's count was
reading the file. Before the change the same query met a file nobody was reading and took 16.7 s.
The first open or query that finds the lock free and the statistics not counted counts them, in
that call, which on the corpus takes the two minutes above. A writer that opens the store during
the count waits for the write lock, as any write does, up to the store's 30 s timeout, and fails
after it (not measured here).

### The filtered aggregate against `CASE`

The statement's per-term aggregate, `max(r.c) FILTER (WHERE r.i = j)`, against the form it
replaced, `max(CASE WHEN r.i = j THEN r.c END)`, the statement otherwise the same: one process on
one clone of run 5's migrated file, the 14 queries of two terms or more under the class filter,
five rounds, the order of the two forms alternating by round and query, after one pass a query to
read the file. Medians of the five rounds, at one-minute loads of 2.7 to 4.3:

| query | terms | `CASE` | `FILTER` | faster |
|---|---|---|---|---|
| L3 | 2 | 24.8 ms | 22.7 ms | 8.6% |
| L6 | 2 | 0.185 s | 0.170 s | 8.4% |
| S1 | 3 | 0.985 s | 0.824 s | 16.3% |
| S2 | 4 | 0.878 s | 0.694 s | 20.9% |
| L11 | 5 | 1.36 s | 1.02 s | 25.0% |
| L17 | 7 | 2.54 s | 2.06 s | 18.7% |
| L20 | 9 | 3.49 s | 2.89 s | 17.0% |
| S3 | 9 | 1.85 s | 1.35 s | 27.0% |
| L8 | 10 | 0.846 s | 0.611 s | 27.9% |
| L14 | 10 | 2.49 s | 1.80 s | 27.7% |
| S4 | 12 | 3.68 s | 2.85 s | 22.6% |
| L23 | 14 | 5.24 s | 4.16 s | 20.6% |
| S5 | 17 | 4.73 s | 3.46 s | 26.7% |
| L25 | 19 | 7.51 s | 5.89 s | 21.6% |

The answers of the two forms are identical. The filtered form is 17 to 28% faster on the nine
titles of seven terms or more, 16 to 25% on those of three to five, and 8 to 9% on the two of two
terms.

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
  transaction mode opened a transaction that kept a shared lock on the ledger file (rollback
  journal mode) after the call; the lookups now only read.
- An attestation sorts its output hashes and does not remove repeats, so the side table keeps one
  row for each element (its position in the key), and `producers_by_output` lists a record once
  for each time it names a hash, as before.
- Kept by row triggers instead of in the landing's transaction, the statistics would need one
  upsert a posting of each unit whose currency moves (86 a unit on average here) rather than one
  a distinct (term, class) pair of the batch; the upkeep is batched in the transaction, and only
  the guard is a trigger.
- A migration that waits for the write lock makes every other process that opens the store during
  the count wait out the busy timeout and fail, readers included. The first version of this change
  did, and its record did not say so. The count now does not wait; a reader opens at once and
  counts its query's statistics from the units until the count is done.
- A migration is a write that an open and a query make, where main's open writes nothing, so no
  failure of it may stop a reader. At b61c0ca0 only the lock and a read-only file were caught: a
  full file made the open and every query raise (the tests that now hold this set SQLite's page
  limit at the file's size, and fail at b61c0ca0). Every failure is now rolled back, and the
  store answers from its units, the ledger from its records, until a later query finds the lock
  free or, for any other failure, until it is opened again.
- In main's code `search` and `scores` with paths run the same computation (`_score_units` over
  the paths' units) and differ only by a sort of the scored units or a map to their paths, so
  their before times are the same work.

## Caveats

- One run before and one after on a machine shared with other work, and three earlier runs with
  an earlier harness; read the load beside each figure. A pass can wait at an ordinary load, which
  the load average does not show: the figures are medians of five passes, and the JSON keeps every
  pass with its processor time.
- The landing's after run met a one-minute load 0.5 to 1 higher than its before run, and part of
  the lexical stage's rise is not attributed.
- The corpus holds one class, so the clearance rule's sums are over one row here; the generated
  stores of the property tests hold four.
- Every part starts on files the cache has not read, and the figures are warm medians beside each
  part's first call; a file larger than memory was not measured.
- The corpus's lexical file is LEGACY's; the current tokenizer re-derives it before it scores it,
  and that re-derivation lands every unit again (with its statistics).
- Not run: the whole-stratum load of a sentence admitting the dialogue stratum, the cut test of a
  citation sentence and the pending mask (each with its reason above).

## The earlier runs (1 to 3)

The first version of this record rested on three runs of an earlier version of the battery: three
warm passes a query, no processor time, and no prepared source, so the branch's parts ran on a
lexical file that its first open had just read whole while it counted the statistics.

1. main at f969904e, every part;
2. the branch at 2bedbcf1, every part;
3. the branch at f1a1f49c (the tree of b37d02e9, made again when the subject of an earlier commit
   was reworded), the keyword and ledger parts again. Between runs 2 and 3 the sum's per-term
   aggregates became filtered, and the ledger's lookups stopped sorting the hashes they are asked
   for.

The five runs gave the same 65 answers. The JSON keeps the earlier runs' figures under
`earlier_runs`. What did not hold, or was stated wrongly:

- Run 1's `search` with paths took a median of 8.43 s (2.33 to 15.7 s) over the five queries and
  its `scores` with paths 5.47 s. In main's code the two are the same computation, and run 4 gives
  5.39 s and 5.41 s. Run 1's passes of the `search` shape spread widely at one-minute loads of 3.1
  to 4.2: L0 1.25 to 3.59 s, L11 6.32 to 12.56 s, L17 14.9 to 17.8 s after a first call of 7.71 s.
  Run 4's passes of the same queries stay within 2% of their medians. Run 1 kept no processor
  time, so whether its slow passes waited cannot be told.
- Run 1's class-filtered L3 took 5.55 to 5.86 s in each of its four calls; run 4's took 2.91 to
  2.93 s.
- Run 2's landing met files its first open had just read; the upkeep was not timed and no batch
  replaced versions. Its record put the upkeep within the spread of the lexical stage (9.38 s
  against 8.83 s for batches 1 and 2, at a load one to four higher) and called a batched landing
  unchanged within its spread. Runs 4 and 5 time the upkeep and find the landing slower (above).
- The record said the landing, the single landing and the control exercised no line changed
  between runs 2 and 3, so their after figures were run 2's. They reach one: the ledger's lookups
  no longer sort the hashes they are asked for. The answers cannot change (the lookups return sets
  and sorted lists), and the sort it dropped takes 0.24 ms for 2,050 hashes.
- Run 2's control took its first call (5.79 s) on a file the migration had just read, not on a
  cold one. The record also set run 1's first call (7.40 s) beside a 7.2 s it attributed to the
  stage-1 record, which holds no time for the pending set; that comparison is dropped.
- Load ranges the record labelled one-minute were not all one-minute. Run 3's ledger part ran at a
  one-minute load of 2.65 (the record gave 2.5 to 3.7, the five- and fifteen-minute fields mixed
  in); the pending set's one-minute loads were 2.3 to 2.6 before and 3.2 to 3.4 after, and the
  single landing's 2.4 and 3.3 to 3.4 (the record gave the spread of one reading's three fields).
  Run 3's class-filtered pass met a one-minute load of 6.0 to 11.3 for its second half (L17 to
  S5); the record gave 6.7, the lowest first reading.
- The record gave the ledger lookups the first call apart then five passes; they had three.
- The record and the article gave the filtered aggregate as 6 to 27% faster than the `CASE` form
  on the long titles. No run recorded that figure; the interleaved comparison above is the
  measurement.
- The six lexical migrations of runs 2 and 3 took 114.5 to 121.6 s at one-minute loads of 2.38 to
  4.86, the ledger's six 1.82 to 2.67 s at 2.65 to 4.86 (the loads read when each part or process
  began; the JSON has each).

## Reproduce

    uv run python -m eval.stress_battery --source <the instance's data directory> \
        --scratch <a scratch directory> --out <record.json> --queries <titles.json> \
        --tokenizer legacy --passes 5 --fresh 3 --fresh-qids L0,L11,L23 \
        --path-qids L0,L6,L11,L17,L23 --runs 3

`<titles.json>` is a JSON list of `{"qid", "text"}`; without it the battery draws titles from the
store. The before run used main's tree at f969904e with this harness beside it. The comparison of
the two aggregates is a scratch script, not committed: on one clone of the migrated file it
rewrites the statement's aggregates on the store's connection and alternates the two forms by
round and query.
