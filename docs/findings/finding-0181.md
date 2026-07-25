---
type: finding
id: finding-0181
status: open
created: 2026-07-25
updated: 2026-07-25
links:
  - ops/lifecycle/snapshot.py                          # the stale docstring + the parked figures
  - core/typedshims/lancedb.py                         # `count_rows(filter)` now exists (bp-103)
  - core/stores/vectorstore.py                         # rows_for_source no longer full-scans
  - docs/build-plans/bp-102/plan.md                    # whose Item 2 parked the figures
  - docs/build-plans/bp-103/plan.md                    # which landed half the missing capability
ftype: codebase
origin_plan: bp-103
route: orchestrator
resolution: null
---

# bp-103 half-lifted a blocker bp-102 parked — and left two of bp-102's docstring claims false

## What

`ops/lifecycle/snapshot.py` records, carefully and with measurements, why two corpus figures are
absent from `status`. Both statements were true when written and are now false:

1. **`_CountableStore`'s docstring (`:293`)** — *"Anything wider (`all_rows`, `rows_for_source`,
   `search`, `to_arrow`) does a full `to_pylist()` that materializes the `vector` column — the
   finding-0169 mistake, one level up."* As of bp-103, **`rows_for_source` does not**: it pushes
   the `source_path` predicate down through `scan().where(…).limit(0)`, so it marshals only the
   matched path's rows. Pinned by `test_rows_for_source_reads_only_that_paths_rows`
   (4 rows read out of 204). The list is right about `all_rows`, `search` and `to_arrow`; it is
   now wrong about `rows_for_source`.

2. **`StoreStats`'s docstring (`:308-312`)** — the **`current=true/false` split** and **distinct
   code versions embedded** are parked because *"The metadata-only reader would be
   `count_rows(filter=…)` on `core/typedshims/lancedb.py` plus a method on
   `core/stores/vectorstore.py` — both outside bp-102's write scope."* **The first half now
   exists.** bp-103 Item 1 added `count_rows(filter: str | None = ...)` to the `VectorTable`
   Protocol and to the runtime adapter, tested by `test_count_rows_filters_server_side`. Only the
   `VectorStore` method remains.

Neither is a defect in either plan — each was an honest statement of a real boundary at the time,
and bp-103 moved the boundary. But a stale reason-for-absence is worse than no comment: the next
reader takes it as a current constraint and re-parks a figure that is now cheap.

## Why it matters

The `current=true/false` split is not a cosmetic status figure. It is **the observable that says
whether the temporal corpus is actually working** — how much of the code history has been
superseded-and-retained versus how much is HEAD. bp-103 exists to unblock the backfill that
produces exactly that history; being unable to *see* the split while it runs is a poor position
from which to judge the restart. And the cost objection has evaporated: a filtered `count_rows`
reads fragment metadata, the same class of read as the `count()` that snapshot already permits
(measured at 5 ms over the real 22,621-row store).

The residual work is roughly one method:

```python
def count_current(self, *, current: bool = True) -> int:
    """Metadata-only: how many rows are (or are not) part of a HEAD projection."""
    if TABLE not in self._db.list_tables().tables:
        return 0
    return self._table().count_rows(f"current = {'true' if current else 'false'}")
```

plus widening `_CountableStore` and one `StoreStats` field. bp-103 deliberately did **not** write
it: `core/stores/**` is in bp-103's write_scope, but this figure is *bp-102's deliverable*, and
helping myself to another plan's parked criterion because the file happens to be writable is
precisely the "route around the boundary" move the standing rule forbids. Filed instead.

## Re-entry condition

An orchestrator decision at seal: either fold the correction + the new method into a small
follow-up plan (it is one method, one Protocol line, one field, and two docstring edits), or
correct the two docstrings alone so they stop asserting a constraint that no longer holds. The
docstring correction should happen either way, and it belongs to whoever owns `ops/**` next.

## Routing

`codebase` → orchestrator. Ordinarily a builder resolves a `codebase` finding in place; here the
files are outside bp-103's write_scope (`ops/**` is bp-102's) and the substantive half is another
plan's parked criterion, so the resolution is a scoping decision rather than an edit.
