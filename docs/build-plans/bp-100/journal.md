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
per `supersede_source` → 1**, and **`delete_source` 1 → 0**. Commit `e22347a`.

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

### Items 2–3 · DONE to the scope ceiling (commit `e22347a`)

`core/stores/vectorstore.py`:

* **`_sql_str(value)`** — the escaping idiom, previously inline in `delete_source`, lifted to one
  module-level helper (plan §2's DRY audit asked exactly this). Used by `delete_source` and
  `delete(digest=…)`.
* **`delete_source`** — now `delete(f"source_path = {_sql_str(path)}")`. **Zero** materializations
  (was one full table). Same rows as the Python filter selected — same column — and strictly fewer
  in the one case they differ: an `id` is `{doc_id}:{chunk_hash}` and `doc_id` need not equal
  `source_path` (a rename, an `id::` property), so two paths CAN share an id and the old
  `id IN (…)` list could delete another path's row. That is now
  `test_delete_source_does_not_reach_rows_of_another_path`, **verified red at HEAD** (`git stash`
  demo: `assert (0 == 1)` — HEAD deleted both rows).
* **`supersede_source`** — one scan, not two. Unchanged semantics; the delete no longer re-scans to
  rebuild an id list its caller already holds.
* Docstrings carry `[banner: correction]` on `rows_for_source` (the "quoting hazard" premise was
  false — `delete_source` refuted it three lines below) and on `supersede_source` (the "no
  dependency on a LanceDB in-place `update`" claim is false at the pinned version), plus
  `[cross-ref: extension]` recording the retained-but-bounded idiom, exactly as plan §4 directs.

`tests/unit/test_vectorstore_supersede.py` (new, 11 tests) pins the semantics the cost work must
not disturb — this is the file that must stay green through the finding-0175 rewrite:

* `test_vectors_are_byte_identical_across_a_supersede` — **Item 3's falsifier, and the one that
  matters most.** Every row of the path, every float, exact equality before vs after; plus every
  non-`current` field unchanged. It did **not** fire.
* keep-and-link retention (nothing deleted, neighbours untouched); idempotence (2nd call returns 0,
  rows byte-identical); already-superseded rows carried through unchanged; no-ops on an unknown
  path and on a store with no table.
* **Item 2's falsifier** — `source_path = "notes/it's a  café/π.md"` (apostrophe + double space +
  non-ASCII) against a `notes/it` prefix decoy, through both `rows_for_source` and `delete_source`.
* the pre-bp-099 `_migrate_current_if_needed` path still works and supersedes normally afterwards.

Stop-and-raise conditions checked, none triggered except the write_scope one:

* vector-equality falsifier — did not fire.
* no consumer depends on `rows_for_source` returning the whole table (census above).
* cost still grows with N — but Q3 resolved to "in-place update IS available", so this is the
  write_scope block, not the "f-0168 must come first" branch the plan feared.

### Green gate (each leg run separately, never `&&`-chained)

```
uv run ruff check .                              → All checks passed!
uv run mypy core agents eval ops scheduler scripts → Success: no issues found in 255 source files
uv run mypy                                       → Found 69 errors in 20 files (checked 536)   [baseline 69 ✓]
uv run python -m ops.type_gate                    → Tier-2 membership: OK / Bare-ignore scan: OK
uv run python scripts/check_imports.py            → Import firewall (I2): OK
uv run pytest -q                                  → 1 failed, 1949 passed, 15 skipped,
                                                     2 xfailed in 1375.21s (0:22:55)
```

The one failure is `test_core_self_containment.py::test_core_imports_nothing_outside_core` — the
**RED-by-design** bp-066 ratchet (PROGRESS.md: *"'green' = the ONLY failure is
`test_core_imports_nothing_outside_core` AND its count is monotone non-increasing"*). Verified
non-increasing rather than assumed: violations at my base `150a190` = **21**, after my change =
**21**. None of the listed violations is `core/stores/vectorstore.py`; the change adds no import.
The `2 xfailed` are my two O(N) ratchets.

Note for a fresh agent: the full `pytest -q` blocks on `/tmp/mp-live-ollama-*.lock`, a cross-process
flock the live-model tests serialize on. With sibling builders (bp-101/bp-102) running their own
suites in parallel worktrees, it queues for tens of minutes at ~0% CPU. `sample <pid>` showing
`fcntl_flock_impl` is that queue, not a hang.

### Next actions for a fresh agent

1. If write_scope is widened to include `core/typedshims/lancedb.py`: apply the patch in
   finding-0175 §"The exact unblock", rewrite `supersede_source` to the single `update()` call,
   `rows_for_source` to `search(None).where(...)`, delete both `xfail` markers, re-run the gate.
2. If not: bp-100 lands as the 2x improvement above and the O(N) term stays; the daemon restart
   decision is the orchestrator's, but finding-0169's re-entry condition ("cost independent of total
   store size, proven by the ratchet") is **NOT met** by this session's work alone.
