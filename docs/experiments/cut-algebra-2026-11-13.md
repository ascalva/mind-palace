---
type: experiment-report
experiment: cut-algebra
runs: 2
status: complete
started: 2026-11-13
links:
  - docs/design-notes/dn-temporal-snapshot.md          # the design these figures test (§4.2, §4.4, §11; stage SN-1b)
  - docs/experiments/cut-algebra-2026-11-13.json       # both runs, every figure below
  - eval/cut_algebra_bench.py                          # the harness
  - core/stores/cuts.py                                # what is measured
  - docs/experiments/landing-log-2026-11-11.md         # SN-1's figures on the same catalog
---

# The algebra of cuts, measured on the corpus instance's catalog (2026-11-13)

**Question.** Stage SN-1b replaces the read of every head at a cut, which built a row in Python a
head, with the contents of the cut: a set of versions named by a predicate on a row's position
and its closing stamp, read as a count or as columns. What does reading every head cost now on
the corpus chain of 400,274 heads, against SN-1's rows and against SNF-6's bar of a tenth of a
second? Does the signed difference of two cuts cost what changed between them, and what does it
cost against two reads of every head and a set difference? And what do the operations over a
family of cuts cost? The design measured these on synthetic chains only (dn-temporal-snapshot
§11); these are the figures of the code as built, on a copy of a real catalog. What the stage
delivers is the cut as a value, the contents of a cut and their algebra over the landing log,
and the cut tool's handler with its registration for the Ambassador. It is not yet the graph:
edges and graph mathematics at a cut arrive with SN-4.

## Method

Two runs of `eval/cut_algebra_bench.py` with its defaults (`--history 200000 --repeat 5 --batch
10000 --seed 13`), the harness at `4e94b442` and the engine at `b210db03`, each on its own
copy-on-write clone (`cp -c`) of the corpus instance's catalog file with its `-wal` and `-shm`,
made in a scratch directory; the original was never opened. The harness migrates the clone in
place under a random secret made for the run and dropped with it, as SN-1's harness does.

- **The catalog.** 400,274 rows, every one `observed` and active, so the genesis is one chain of
  400,276 rows: the `genesis`, a `store` a path, the `horizon`.
- **Every head.** At the head of the genesis, before any history, and again after it: SN-1's
  `heads_at`, a `Landing` built in Python a head (called at the harness's commit, before the
  contents replaced it); the contents of the cut counted, one statement that builds no row; and
  the contents read as columns, one buffer a column, the three a head is named by (its position,
  its path's key, its digest) and the eight a listing reads (the chain, the position, the key,
  the path, the identity, the digest, the title, the version). That the columns hold the rows'
  positions, keys and digests in order is checked.
- **A history.** 200,000 catalog writes after the genesis, through `record` and `tombstone` in
  batches of 10,000, in a shuffled order: a new version of a held path for 100,000 of them, a
  retire of another held path for 50,000, a new path for 50,000. Each appends one row, so the
  chain then ends at position 600,276, with 400,274 heads again.
- **The signed difference.** From the head less 1, 1,000 and 100,000 positions, from the horizon
  (the whole history) and from the bottom (every position), to the head: its counts of the paths
  removed, added and replaced (one statement), its two sizes (one statement), each side read as
  three columns, and both sides read and sorted by path into the three classes; against two
  reads of every head as SN-1 made them and a set difference of their rows. The difference's
  sides are checked equal to the set differences.
- **A family.** Ten cuts spread evenly from the horizon to the head: the count at each, walked
  by the differences between neighbours, against ten counts; what persisted through all; what
  existed in any; the sizes of the pairwise differences, checked against the hundred
  differences; and what persisted from the horizon to the head.
- **The plans.** `EXPLAIN QUERY PLAN` of the statements of what the head holds and of the rows
  come and gone over the last thousand positions.
- **The machine.** Apple M2 Pro, 12 cores, 32 GB, macOS 27.0.1, Python 3.15.2, SQLite 3.54.1,
  NumPy 2.5.4, with other work running: the one-minute load average was 2.6 and 3.0 at the starts
  of the two runs, 2.9 and 4.0 before their histories, and 3.0 and 2.3 at their ends. Medians
  with their ranges over five repetitions; the two runs side by side.

## Results

| measurement | run 1 | run 2 |
|---|---|---|
| the migration, 400,276 rows of genesis | 7.45 s | 6.87 s |
| every head at the genesis's head, 400,274: SN-1's rows | 1.79 s (1.76 to 1.95), 4.46 µs a head | 1.74 s (1.71 to 1.89), 4.34 µs a head |
| the same, counted | 66.5 ms (66.1 to 66.7), 0.166 µs an event | 66.2 ms (65.5 to 67.4), 0.165 µs an event |
| the same, three columns | 224 ms (219 to 229), 0.56 µs a head | 219 ms (216 to 230), 0.55 µs a head |
| the same, eight columns | 433 ms (423 to 457) | 437 ms (432 to 442) |
| the columns hold the rows | yes | yes |
| the history, 200,000 writes | 24.9 s | 25.1 s |
| every head after it, 400,274 over 600,276 events: SN-1's rows | 1.82 s | 1.86 s |
| the same, counted | 89.8 ms, 0.150 µs an event | 95.4 ms (89.4 to 102.5), 0.159 µs an event |
| the same, three columns | 241 ms | 236 ms |
| the same, eight columns | 442 ms | 440 ms |

The signed difference ending at the head (position 600,276), in milliseconds, run 1 and run 2:

| from | paths removed, added, replaced | counts | sizes | rows come, as columns | rows gone, as columns | sorted | two reads of every head and a set difference |
|---|---|---|---|---|---|---|---|
| 600,275 (1 position) | 1, 0, 0 | 0.02, 0.02 | 0.01, 0.01 | 0.02, 0.02 | 0.02, 0.02 | 0.08, 0.08 | 3,728, 3,670 |
| 599,276 (1,000) | 248, 224, 528 | 2.46, 2.54 | 1.62, 1.74 | 0.37, 0.39 | 1.87, 2.04 | 2.74, 2.91 | 3,742, 3,684 |
| 500,276 (100,000) | 24,995, 25,010, 49,995 | 305, 279 | 201, 184 | 42.8, 42.4 | 238, 218 | 362, 318 | 3,787, 3,655 |
| 400,276 (the history, 200,000) | 50,000, 50,000, 100,000 | 604, 560 | 412, 373 | 89.7, 83.1 | 463, 448 | 682, 657 | 3,812, 3,634 |
| 0 (every position, 600,276) | 0, 400,274, 0 | 147, 144 | 105, 102 | 260, 238 | 0.01, 0.01 | 448, 398 | 1,879, 1,783 |

Every side equalled the baseline's set difference in both runs. A family of ten cuts from the
horizon to the head (positions 400,276, 422,498, …, 600,276), in milliseconds:

| measurement | run 1 | run 2 | result |
|---|---|---|---|
| the count at each cut, walked by the differences | 487 (463 to 508) | 435 (430 to 444) | the ten counts, equal to the counts read |
| ten counts | 834 (809 to 838) | 790 (778 to 806) | |
| what persisted through all | 64.1 | 64.8 | 250,274 versions |
| what existed in any | 98.5 | 99.6 | 550,274 versions |
| the sizes of the pairwise differences | 319 | 315 | equal to the hundred differences' sizes |
| what persisted from the horizon to the head | 66.5 | 63.2 | 250,274 versions |

The plans, the same in both runs: what the head holds is `SEARCH landings USING PRIMARY KEY
(chain=? AND seq<?)`; the rows come, `SEARCH landings USING PRIMARY KEY (chain=? AND seq>? AND
seq<?)`; the rows gone, `SEARCH landings USING INDEX landings_closed (chain=? AND closed_at>? AND
closed_at<?)`. The planner chose each with no hint: the statements bound each side by the
intervals, and the bounds are what it takes.

## Reading

- **Every head, counted, passes the bar.** 66 ms for 400,274 heads, 0.17 µs an event walked and
  no row built, against 1.74 to 1.79 s for SN-1's rows: 27 times faster. After the history the
  count walks 600,276 events in 90 to 95 ms, 0.15 to 0.16 µs an event, so a count passes a tenth
  of a second up to about 600,000 events.
- **Every head as columns does not, at this size.** Three columns take 219 to 224 ms, 8 times
  faster than the rows and twice the bar. Beyond the walk a head costs 0.39 µs as three columns
  and 4.2 µs as a row. So three columns pass the bar near 180,000 heads on a chain whose events
  are its heads, and fewer where a chain has closed many rows, since the walk is over events. That
  is the size §4.2 left to this measurement (D30); the corpus chain is over it, and a reader of
  every head of it reads them once and walks the differences, or reads heads kept at a recorded
  cut (SN-c).
- **A difference costs what changed.** 0.02 ms for one position, 2.5 ms for a thousand, 0.3 s
  for 100,000 and 0.6 s for the whole history of 200,000, against 3.6 to 3.8 s for two reads of
  every head and a set difference, whatever the span. From the bottom, where everything the head
  holds has come, the counts take 0.14 to 0.15 s and the baseline 1.8 to 1.9 s, one of its two
  reads being empty.
- **The rows gone cost more a row than the rows come.** The rows come are one run of the primary
  key, 0.57 µs a row at 100,000 positions; the rows gone are found on `landings_closed` and each is
  then read from the table by its position, 2.9 to 3.2 µs a row. Both grow with what changed and
  not with what is held.
- **A family.** Walking the count by the differences took 0.43 to 0.49 s for ten cuts against 0.79
  to 0.83 s for ten counts: one prefix and then what changed between neighbours. What persisted
  through ten cuts reads two positions a chain, one walk of the prefix at the least, 64 ms, the
  same as from the horizon to the head; what existed walks the prefix at the greatest; and the
  pairwise table reads what existed once and counts it into the table, 0.32 s, where a hundred
  differences would each walk what changed between two cuts.
- **The laws held on the corpus's sizes.** Every side of every difference was the set difference
  of the baseline's rows, the walked counts were the counts read, the pairwise table was the
  hundred differences' sizes, and the columns were the rows.

The review of SN-1b, after these runs, repaired the engine and the tool (dn-temporal-snapshot
§12, SN-1b). No statement the harness times changed: the symmetric difference, now one node
whose statement names each operand once, is not among them, and neither is the walk that finds
a chain's horizon, now made once a call for each chain.

## Not measured

A class of several chains, or several classes (the corpus is one chain of one class), and so a
difference between two cuts neither of which is under the other; holes, since the history purged
nothing and every count of holes was 0; the walk that finds a chain's horizon for a position
named under the head, which the tool makes and the harness does not; the tool's answers through
the server; and anything SN-4 reads at a cut: the nodes' parts, the edges by species and the
graph's mathematics.
