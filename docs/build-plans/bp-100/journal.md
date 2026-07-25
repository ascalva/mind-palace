# Journal — bp-100

## Session 1 (2026-07-25, delegated builder, worktree `agent-aaabb0a78deff0e28`)

### Orientation

Read in manifest order: plan, `core/stores/vectorstore.py`, finding-0169, `core/ingest/code_corpus.py`,
`core/typedshims/lancedb.py`. Grepped every consumer of `rows_for_source` / `delete_source` /
`all_rows` / `supersede_source` across the repo.

**Consumer census (plan Item 2 invariant: "verify by grepping consumers before narrowing any
projection")**

| method | consumers | columns actually read |
|---|---|---|
| `rows_for_source` | `core/ingest/sync.py:117` → `index_amendment` (`core/ingest/index.py:77`) | `text` AND **`vector`** — the amendment reuses stored vectors instead of re-embedding |
| `delete_source` | `core/ingest/sync.py:143` (`handle_deleted`), `core/ingest/index.py:87` (every note amendment) | none — it only needs the rows gone |
| `supersede_source` | `core/ingest/code_corpus.py:293,298` | none externally; internally needs every column to re-land |
| `all_rows` | ~40 call sites (mirror, dreamer, curator, sourceset, code lane, launcher probe, eval harness) | varies; `vector` is read by the mirror/dreamer |

**Conclusion:** `rows_for_source` must keep returning the `vector` column (finding: no consumer
depends on it returning the whole *table*, so the plan's second stop-and-raise condition is NOT
triggered). `delete_source` needs no columns at all — it can become a pure predicate.

### Q3 — RESOLVED: LanceDB **does** support an in-place column update

The `supersede_source` docstring's claim ("no dependency on a LanceDB in-place `update`") is
**false at the installed version**. Verified empirically, not from docs:

```
lancedb 0.33.0   (pyproject pins lancedb>=0.10)   pyarrow 24.0.0
Table.update(where=None, values=None, *, values_sql=None) -> UpdateResult
  UpdateResult(rows_updated=3, version=3)
```

Run against a throwaway temp store with a `source_path` containing a single quote:

```
t.update(where="source_path = 'a''b.py' AND current = true", values={'current': False})
  -> UpdateResult(rows_updated=3, version=3)
vectors after:  i0 -> [0.0, 0.5, 0.25]   (byte-identical, untouched)
```

Also verified available and useful, same version:

* `Table.count_rows(filter: str | None)` — filtered count, no materialization.
* `Table.search(None)` → `LanceEmptyQueryBuilder` with `.where(pred)`, `.select([cols])`,
  `.limit(0)` (= unlimited), `.to_list()` / `.to_arrow()` — i.e. a **projected, filtered read**:
  exactly the "push the filter down, don't materialize the vector column" primitive the plan wants.

So the correct implementation is: `supersede_source` = **one `update()` call, zero
materializations, zero vector marshalling**; `rows_for_source` = `search(None).where(...)` with the
full projection; `delete_source` = a `source_path` predicate.

### BLOCKER — the fix needs `core/typedshims/lancedb.py`, which is outside write_scope

`update`, `count_rows(filter=...)`, `search(None)`, and `.select(...)` are all **new LanceDB
surface**. Plan §2 item 6 is explicit: "Any new LanceDB surface used here must pass through
[`core/typedshims/lancedb.py`], not around it." But §5 write_scope lists only
`core/stores/vectorstore.py` + two test paths. The shim is not writable to me, and there is no
honest in-scope substitute:

* the shim's `ArrowTable` Protocol exposes only `to_pylist()` — no `filter`/`select`, so a
  pyarrow-level projection is not expressible either;
* `VectorTable.search(vector: list[float])` requires a vector, so a metadata read would have to
  masquerade as a KNN query with a sentinel vector and a guessed `limit` — silent truncation on a
  deep path, `_distance` pollution, distance-ordered results. Rejected: that is worse engineering
  than the defect.
* declaring the extra Protocol methods locally in `vectorstore.py` + `cast` is precisely the "around
  it" the plan forbids.

Per the plan's stop-and-raise ("Any temptation to widen scope… file a finding, do not edit") and the
delegation brief ("STOP and raise if you would need to write outside write_scope"): **filed
finding-0175** with the exact 4-line shim patch and the exact `vectorstore.py` body it unblocks, so
the unblock is copy-paste for whoever owns the widened scope. I did **not** edit the shim.

### What landed instead

Everything the existing shim surface allows, which is real but partial: **2 full materializations
per `supersede_source` → 1**, and **`delete_source` 1 → 0**.

### Item 1 — the cost ratchet · DONE, proven RED at HEAD

`tests/unit/test_store_cost_ratchet.py` (new). Instrument = a counting proxy wrapped around
`VectorStore._table()` that records every `to_arrow().to_pylist()`: call count, rows marshalled,
and float values pulled out of the `vector` column. **No wall-clock anywhere** (the brief's
anti-flake requirement). Temp stores only; `data/vectors.lance` never opened.

Falsifier discharged — against **unmodified HEAD**, `pytest --runxfail`:

```
FAILED test_supersede_cost_is_independent_of_unrelated_store_size
FAILED test_supersede_does_not_marshal_the_vector_column_of_unrelated_rows
FAILED test_supersede_makes_at_most_one_full_materialization
       AssertionError: 2 full materializations per supersede_source (sizes=[29, 29])
FAILED test_delete_source_needs_no_full_materialization
       AssertionError: delete_source scanned [29] rows to build an id list
4 failed, 1 passed in 1.59s
```

The 1 pass is the deliberate **negative control** (`test_the_instrument_actually_sees_a_full_scan`)
— it proves the proxy is wired to something real, so a green ratchet cannot mean "instrument
broken".

The two O(N)-bound ratchets carry `@pytest.mark.xfail(strict=True)` citing finding-0175, because
they cannot go green without the shim. **strict=True is the point**: the day the pushdown lands they
XPASS and fail the suite, forcing the marker off. They are not skipped, not deleted, not weakened.

### Next actions for a fresh agent

1. If write_scope is widened to include `core/typedshims/lancedb.py`: apply the patch in
   finding-0175 §"The exact unblock", rewrite `supersede_source` to the single `update()` call,
   `rows_for_source` to `search(None).where(...)`, delete both `xfail` markers, re-run the gate.
2. If not: bp-100 lands as the 2x improvement above and the O(N) term stays; the daemon restart
   decision is the orchestrator's, but finding-0169's re-entry condition ("cost independent of total
   store size, proven by the ratchet") is **NOT met** by this session's work alone.
