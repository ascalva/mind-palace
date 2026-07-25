---
type: finding
id: finding-0179
status: open
created: 2026-07-25
updated: 2026-07-25
links:
  - core/stores/vectorstore.py                         # count() is the ONLY metadata-only read
  - core/typedshims/lancedb.py                         # the Protocol that would carry count_rows(filter=…)
  - ops/code_snapshot.py                               # files(commit_sha, path) — nothing indexes (path, blob_sha)
  - scheduler/queue.py                                 # JobQueue has no windowed/aggregate reads
  - ops/lifecycle/snapshot.py                          # the consumer that had to work around both
  - docs/findings/finding-0169.md                      # the full-scan class this keeps out of status
ftype: spec-defect
origin_plan: bp-102
route: builder
resolution: null
---

# Two read surfaces have no cheap query, so the instrument that needs them had to route around

## What

bp-102 built the rate/budget block on `palace status` under a hard constraint: no figure may cost a
full store scan (its Item 2 falsifier — a status command that repeats finding-0169 one level up has
failed even if every number is right). Two read surfaces could not meet that constraint, and both
are outside bp-102's write scope, so the plan shipped around them. This is the hand-off.

### (a) `VectorStore` has exactly one cheap read

`count()` → LanceDB `count_rows()` is metadata-only (**measured 1.4–2.9 ms** over the real
22,621-row store). Every other read — `all_rows`, `rows_for_source`, `relabel_provenance` — goes
through `self._table().to_arrow().to_pylist()`, which materializes **every column including
`vector`**. That is the finding-0169 shape exactly.

So the figures bp-102 §7 Item 2 asked for — *"code versions embedded vs ledger target; `current`
true/false split"* — are **not reported**. They would need:

- `count_rows(filter: str | None = ...)` on the `VectorTable` Protocol in
  `core/typedshims/lancedb.py` (LanceDB supports it; the shim is deliberately narrow and does not
  declare it), and
- a method on `core/stores/vectorstore.py`, e.g.
  `counts_by(*, provenance=None, current=None) -> dict[str, int]`, plus a distinct-version count.

`core/stores/**` is bp-100's write scope, and `core/typedshims/` is in neither, so bp-102 could not
add them. `status` prints the row count and says plainly that coverage has no cheap reader, rather
than showing an expensive number or a fabricated one.

### (b) The code-snapshot ledger cannot answer its own target cheaply

`COUNT(DISTINCT path, blob_sha) FROM files` — the backfill's work-list size, and the denominator of
any coverage figure — **measured at 3.5 s**, consistently:

```
plan: SCAN files ; USE TEMP B-TREE FOR DISTINCT     -- 423,855 rows, 2.3 GB table
```

`files` is `PRIMARY KEY (commit_sha, path)`; nothing indexes `(path, blob_sha)`, and the table's
rows carry a `docstring TEXT` column, so the scan is wide as well as long. An index on
`files(path, blob_sha)` would make it an index-only count.

Note this is not only a status problem: `ops/code_lineage.py:ledger_versions` materializes the same
distinct set on **every backfill run**, and `launcher._code_backfill_incomplete` calls it at every
start to decide whether to enqueue a backfill — so the 3.5 s is already being paid on the daemon's
startup path, where nobody has measured it.

### (c) `JobQueue` has no windowed or aggregate reads

`depth()` and `counts()` are the whole aggregate surface; `list(state)` materializes every row with
its `payload`. Throughput-in-window, in-rate/out-rate, per-kind oldest age, and last-failure are
therefore issued as raw SQL from `ops/lifecycle/snapshot.py:read_queue_stats` over its own
`file:…?mode=ro` connection, against the `jobs` schema. bp-102 §2.6 pins that schema as the
sanctioned source and `scheduler/queue.py` is bp-101's write scope, so this was the correct move
for this plan — but it is duplicated schema knowledge, and two copies drift.

## Why it matters

- **(a) and (b) are why a real capability is missing.** "How much of the code corpus is actually
  embedded?" is the question the finding-0169 restart most needs answered, and it is the one figure
  the new status block cannot give. That gap is currently invisible except as a parenthetical.
- **(b) is a live cost on the startup path**, not only a reporting one. The catch-up probe pays it
  every `palace start`.
- **(c) is a DRY defect** by the owner's standing rule (duplicated code is a defect, not a nit): the
  `jobs` column names now appear in two modules. `read_queue_stats`'s queries are the natural
  content of a `JobQueue.stats(window)` method.

## Re-entry condition

- **(a)** at the next plan whose write scope includes `core/stores/vectorstore.py` (bp-100's lane).
  Add the filtered count to the shim + store; `ops/lifecycle/snapshot.py:read_store_stats` then
  grows `StoreStats` fields and `_report_snapshot` prints the coverage line. The
  `test_store_stats_carries_only_the_one_cheap_figure` contract test in
  `tests/unit/test_status_cost_bound.py` is the marker — it fails deliberately when the shape
  changes, forcing the cost question to be answered again.
- **(b)** at the next plan owning `ops/code_snapshot.py`: add
  `CREATE INDEX IF NOT EXISTS files_path_blob ON files(path, blob_sha)` and re-measure both this
  count and `_code_backfill_incomplete`.
- **(c)** at bp-101's merge, or the next plan owning `scheduler/queue.py`: lift `read_queue_stats`'s
  seven queries onto `JobQueue` and have `snapshot.py` call it. Behaviour-preserving; the existing
  cost assertions carry over unchanged.

None of the three blocks bp-102, and none blocks the restart.

## Routing

`codebase` → builder. No design question here — the shape of each fix is settled, only its write
scope is elsewhere. Related but distinct: bp-102 §11's `sweep_orphans` wiring, which is still open
because bp-101 had not merged when bp-102 was built.
