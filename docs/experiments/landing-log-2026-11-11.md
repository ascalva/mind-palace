---
type: experiment-report
experiment: landing-log
runs: 2
status: complete
started: 2026-11-11
links:
  - docs/design-notes/dn-temporal-snapshot.md          # the design these figures test (§3.2, §4, §11; stage SN-1)
  - docs/experiments/landing-log-2026-11-11.json       # both runs, every figure below
  - eval/landing_log_bench.py                          # the harness
  - core/stores/landings.py                            # what is measured
  - docs/experiments/two-phase-ingestion-2026-11-07.md # a lazy landing's cost, the overhead's scale
---

# The landing log, measured on the corpus instance's catalog (2026-11-11)

**Question.** What does stage SN-1's landing log cost at a corpus's size: the migration that
writes its genesis, the bytes a row takes, the time it adds to a key's write, and the time each of
its reads takes? And does the genesis hold the catalog exactly? The design note measured the log
on a synthetic fixture only (§11); these are the figures of the code as built, on a copy of a real
catalog.

## Method

Two runs of `eval/landing_log_bench.py` with its defaults (`--batch 10000 --rounds 5
--repeat 200 --seed 11`), each on its own copy-on-write clone (`cp -c`) of the corpus instance's
catalog file with its `-wal` and `-shm`, made in a scratch directory; the original was never
opened. The harness migrates the clone in place under a random secret made for the run and
dropped with it.

- **The catalog.** 400,274 rows, every one `observed` and active, so the genesis is one chain of
  400,276 rows: the `genesis`, a `store` a path in path order, the `horizon`. No identity differs
  from its path and no path is tombstoned, so the identity index and the closing index stay empty.
  A path is 28.6 characters on average and a title 63.8.
- **The migration.** The first open with the log, timed whole: the tables, their indexes and the
  genesis in one transaction. The bytes are the file's, with the write-ahead log checkpointed into
  it, before and after, and each table's and index's from SQLite's `dbstat`.
- **The check.** The chain verified from its first row, every commitment and every hash
  recomputed; the fold of the log compared with the catalog row by row.
- **The writes.** Batches of 10,000 catalog writes, each batch one transaction, as a landing
  batch writes its keys (`deferred()`): first new paths, then new versions of paths the catalog
  holds. Each batch runs with the log and with the log's appending switched off on the same file
  (a patch of `LandingLog.store`), the order alternated over five rounds; the figure is the
  median over the rounds of the time a write takes.
- **The reads.** On the chain: `state_at` of one path at the middle cut and `history_at` at the
  head, the 200 paths drawn from the catalog; `read_at` of the first 1,000 positions and
  `read_between` of 1,000 positions from 200 random starts; `head`; the keyed hash of a path
  alone; and `heads_at` at a tenth of the chain, at its middle and at its head, five times each,
  with the same predicate counted in SQL, the walk without the rows built.
- **The machine.** Apple M2 Pro, 12 cores, 32 GB, macOS 27.0.1, Python 3.15.2, SQLite 3.54.1, with
  other work running: the one-minute load average was 2.3 at the first run's start, 8.3 between
  the two runs, which another process raised, and 7.2 at the second's end. Medians with their
  ranges over the repetitions; the two runs are given side by side.

## Results

| measurement | run 1 | run 2 |
|---|---|---|
| the migration, 400,276 rows of genesis | 6.22 s | 6.33 s |
| the file, before and after | 162.7 MB, 334.1 MB | 162.7 MB, 334.1 MB |
| bytes a row of the log, from the file's growth | 429.2 | 429.2 |
| of which the table, the key index | 381.3, 47.1 | 381.3, 47.1 |
| `verify`: every commitment and hash of the chain | 3.07 s | 3.05 s |
| the fold of the log against the catalog | equal, 2.83 s | equal, 2.85 s |
| `head` | 2.4 µs | 2.5 µs |
| the keyed hash of a path | 1.6 µs | 1.6 µs |
| `state_at`, one path at the middle cut | 14.3 µs (8.2 to 160) | 14.8 µs (8.5 to 133) |
| `history_at`, one path at the head | 15.7 µs | 14.7 µs |
| `read_at`, 1,000 positions | 3.28 ms | 3.26 ms |
| `read_between`, 1,000 positions | 3.44 ms | 3.42 ms |
| `heads_at` at a tenth (40,026 rows) | 151 ms | 152 ms |
| `heads_at` at the middle (200,137 rows) | 790 ms | 799 ms |
| `heads_at` at the head (400,274 rows) | 1.62 s | 1.61 s |
| the same three walks counted in SQL | 5.6, 26.3, 56.5 ms | 5.9, 26.3, 54.3 ms |
| a write of a new path: with the log, without | 48.9, 6.8 µs | 49.0, 6.8 µs |
| a write of a new version of a held path: with, without | 106.5, 37.9 µs | 106.0, 41.2 µs |
| every chain verifies after the 200,000 writes | yes | yes |

## Reading

- **The genesis holds the catalog.** The fold of the 400,276 rows equals the catalog's 400,274
  rows in both runs, and the chain verifies. The migration takes six seconds once, on the first
  open of the build with the log.
- **A row is 429 bytes,** against the fixture's 434 where the identity is the path (§4.3): the
  table's row is 381 bytes against 374, its titles far longer (63.8 characters against under
  twelve) and its paths shorter (28.6 against 37), and the key index is the same 47 bytes. The
  fixture's closing index, 13 bytes, is empty here, since a genesis of active paths closes no row.
  The log doubles the catalog's file, 162.7 MB to 334.1 MB; it holds paths, digests and titles,
  which the catalog holds already.
- **The log adds 42 µs to a new path's write and 65 to 69 µs to a new version's,** the second
  writing a closing stamp as well. A lazy landing took 31 ms an item on the two-phase record (32.0
  items a second, `docs/experiments/two-phase-ingestion-2026-11-07.md`), so the log is between
  0.1 and 0.2 percent of a landing.
- **A read of one path is 14 to 16 µs** through the key index, of which the keyed hash is 1.6.
- **Every head at the head is 1.6 s,** past the tenth of a second §4.2 allows. The walk itself is
  54 to 57 ms in SQL, 0.14 µs an event, under the fixture's quarter of a microsecond; the rest is
  building 400,274 rows in Python. A corpus chain is over §4.2's 250,000 events from the start,
  which is why SN-4 keeps heads at recorded cuts for such a chain (SN-c); nothing reads every head
  yet.
- **A planner's choice, found here.** The first run of the harness took about 40 ms a landing:
  the update that writes the previous row's closing stamp took the primary key and walked the
  chain, as the fixture's seek did when the planner took the primary key (§4.1). The statement
  now names the key index, as the reads did already, and a test asks the plan of every statement
  by path to name it (`tests/property/test_landing_log.py`). The figures above are after the fix.

## Not measured

A whole landing batch through the writer with the log against without it (the overhead above is
the catalog's writes alone, and nothing else in a landing changed); a purge on the corpus's size,
whose emptying of a digest's rows reads the whole log, since the log has no index by digest; a
catalog of several classes, or one whose identities differ from their paths; and every read at a
cut that SN-2 and later stages build.
