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
writes its genesis, the bytes a row takes, the time SN-1 adds to a key's write against the write
before it, and the time each of its reads takes? And does the genesis hold the catalog exactly?
The design note measured the log on a synthetic fixture only (§11); these are the figures of the
code as built, on a copy of a real catalog.

## Method

Two runs of `eval/landing_log_bench.py` (at `08d4d506`, the code at `88ef0781`) with its defaults
(`--batch 10000 --rounds 5 --repeat 200 --seed 11`) and `--fresh 30000,100000`, each on its own
copy-on-write clone (`cp -c`) of the corpus instance's catalog file with its `-wal` and `-shm`,
made in a scratch directory; the original was never opened. The harness migrates the clone in
place under a random secret made for the run and dropped with it.

- **The catalog.** 400,274 rows, every one `observed` and active, so the genesis is one chain of
  400,276 rows: the `genesis`, a `store` a path in path order, the `horizon`. No identity differs
  from its path and no path is tombstoned, so the identity index and the closing index stay empty.
  A path is 28.6 characters on average and a title 63.8.
- **The migration.** The first open with the log, timed whole: the tables, their indexes and the
  genesis in one transaction. The bytes are the file's, with the write-ahead log checkpointed into
  it, before and after, and each table's and index's from SQLite's `dbstat`.
- **The check.** The chain verified from its first row, every commitment and every hash
  recomputed; the fold of the log compared with the catalog row by row.
- **The writes.** Batches of 10,000 catalog writes, each batch one transaction, as a landing batch
  writes its keys (`deferred()`): first new paths, then new versions of paths the catalog holds.
  Each batch is timed three ways on the same file, the order turned each round over five rounds:
  `record` as built; the same with the log's appending switched off (a patch of
  `LandingLog.store`), which keeps what SN-1 added around the log, the read of the path's row
  before the write, the explicit transaction and each write's savepoint; and the write as
  `record` made it before SN-1 (`f969904e`), the upsert alone. The figure is the median over the
  rounds of the time a write takes. The third is what SN-1 is measured against, and it runs on
  the migrated file, whose `vault_files` table and indexes are the ones an unmigrated file has.
- **The reads.** On the chain: `state_at` of one path at the middle cut and `history_at` at the
  head, the 200 paths drawn from the catalog; `read_at` of the first 1,000 positions and
  `read_between` of 1,000 positions from 200 random starts; `head`; the keyed hash of a path
  alone; and `heads_at` at a tenth of the chain, at its middle and at its head, five times each,
  with the same predicate counted in SQL, the walk without the rows built.
- **Every head of a smaller chain.** After the copy, a new catalog of 30,000 paths and then one of
  100,000, one class, landed through `record` in batches, with paths and titles of the corpus's
  lengths: `heads_at` at the head and the walk counted in SQL, five times each.
- **The machine.** Apple M2 Pro, 12 cores, 32 GB, macOS 27.0.1, Python 3.15.2, SQLite 3.54.1, with
  other work running: the one-minute load average was 3.9 at the first run's start, 3.6 between
  the runs and 2.7 at the second's end, and the second run's smaller chains were read at 2.8. The
  harness peaked at 688 and 692 MB resident. Medians with their ranges over the repetitions; the
  two runs are given side by side.

## Results

| measurement | run 1 | run 2 |
|---|---|---|
| the migration, 400,276 rows of genesis | 6.73 s | 6.71 s |
| the file, before and after | 162.7 MB, 334.1 MB | 162.7 MB, 334.1 MB |
| bytes a row of the log, from the file's growth | 429.2 | 429.2 |
| of which the table, the key index | 381.3, 47.1 | 381.3, 47.1 |
| `verify`: every commitment and hash of the chain | 3.08 s | 3.07 s |
| the fold of the log against the catalog | equal, 2.90 s | equal, 2.93 s |
| `head` | 2.5 µs | 2.5 µs |
| the keyed hash of a path | 1.6 µs | 1.7 µs |
| `state_at`, one path at the middle cut | 13.7 µs (8.6 to 130) | 16.5 µs (8.5 to 166) |
| `history_at`, one path at the head | 15.5 µs | 18.9 µs |
| `read_at`, 1,000 positions | 3.18 ms | 3.19 ms |
| `read_between`, 1,000 positions | 3.35 ms | 3.37 ms |
| `heads_at` at a tenth (40,026 rows) | 151 ms | 150 ms |
| `heads_at` at the middle (200,137 rows) | 790 ms | 789 ms |
| `heads_at` at the head (400,274 rows) | 1.62 s | 1.62 s |
| the same three walks counted in SQL | 5.6, 29.0, 59.5 ms | 5.8, 30.1, 59.1 ms |
| `heads_at`, a chain of 30,000 paths, at its head | 112 ms (walk 4.1 ms) | 111 ms (walk 4.7 ms) |
| `heads_at`, a chain of 100,000 paths, at its head | 374 ms (walk 15.1 ms) | 376 ms (walk 15.4 ms) |
| a write of a new path: as built, the log's rows off, before SN-1 | 55.7, 10.5, 4.7 µs | 57.4, 10.4, 4.6 µs |
| a write of a new version of a held path: the same | 120.3, 46.0, 34.5 µs | 119.1, 45.0, 34.7 µs |
| every chain verifies after the 300,000 writes | yes | yes |

## Reading

- **The genesis holds the catalog.** The fold of the 400,276 rows equals the catalog's 400,274
  rows in both runs, and the chain verifies. The migration takes under seven seconds once, on the
  first open of the build with the log.
- **A row is 429 bytes,** against the fixture's 434 where the identity is the path (§4.3): the
  table's row is 381 bytes against 374, its titles far longer (63.8 characters against under
  twelve) and its paths shorter (28.6 against 37), and the key index is the same 47 bytes. The
  fixture's closing index, 13 bytes, is empty here, since a genesis of active paths closes no row.
  The log doubles the catalog's file, 162.7 MB to 334.1 MB; it holds paths, digests and titles,
  which the catalog holds already.
- **SN-1 adds 51 to 53 µs to a new path's write and 84 to 86 µs to a new version's,** against the
  write before it (4.6 to 4.7 and 34.5 to 34.7 µs). The log's rows are 45 to 47 and 74 of them, a
  new version's writing the previous row's closing stamp as well; the rest, about 6 and 11 µs, is
  the read of the path's row before the write, the explicit transaction and the write's
  savepoint. A lazy landing took 31 ms an item on the two-phase record (32.0 items a second,
  `docs/experiments/two-phase-ingestion-2026-11-07.md`), so SN-1 is between 0.16 and 0.28 percent
  of a landing. A landing in the vault's place also reads its version chain's current version once
  more, to pass it to the key (`core/ingest/writer.py:417-418`); the corpus's place keeps no
  version chain, and that read was not measured.
- **A read of one path is 14 to 19 µs** through the key index, of which the keyed hash is 1.6.
- **Every head costs what building the answer costs.** The walk is 0.14 to 0.15 µs an event in
  SQL; building the rows in Python is 3.5 to 3.9 µs a head returned beyond it, on the corpus's
  chain at a tenth, the middle and the head and on the smaller chains alike. So the read from the
  log alone passes §4.2's tenth of a second near 27,000 heads: a chain of 30,002 events takes 0.11
  s, far under the 250,000 events §4.2 set as the threshold for kept heads, which is the first
  condition of SNF-6, met. Kept heads at a recorded cut shorten the walk and not the building, so
  they do not remove this cost. Nothing reads every head yet; before SN-4 builds on it, SN-c
  re-enters, and whether the threshold moves or the read changes is open (dn-temporal-snapshot
  §4.2, §11).
- **A planner's choice, found here.** The first run of the harness took about 40 ms a landing:
  the update that writes the previous row's closing stamp took the primary key and walked the
  chain, as the fixture's seek did when the planner took the primary key (§4.1). The statement
  now names the key index, as the reads did already, and a test asks the plan of every statement
  by path to name it (`tests/property/test_landing_log.py`). The figures above are after the fix.
- **A savepoint's journal, found here.** Each write in a batch is a savepoint since review, so
  that a write that fails leaves neither of its rows when the batch's caller goes on. Two earlier
  runs of the same harness, at load 3.9 and 4.4, measured a new path's write at 105 and 108 µs
  with the log and 36 and 32 µs with its rows off: SQLite kept each savepoint's journal in a
  temporary file. The catalog's connection now keeps its temporary store in memory, and the
  savepoint costs about 6 µs a write. Those runs are in the JSON, under
  `savepoint_journal_in_a_file`.
- **The control.** The record first gave the log's cost as the write with the log against the
  write with its rows switched off, 42 µs and 65 to 69 µs: that is what the log's rows add, and it
  left out the read of the row before the write and the transaction SN-1 added around them. The
  third arm, the write before SN-1, is the control for SN-1's cost.

## Not measured

A whole landing batch through the writer with the log against without it (the writes above are
the catalog's alone, and a vault landing also reads its version chain once more); a purge on the
corpus's size, whose emptying of a digest's rows walks the whole log twice, for the digest and for
the names of the paths it empties, since the log has no index by either; a catalog of several
classes, or one whose identities differ from their paths; and every read at a cut that SN-2 and
later stages build.
