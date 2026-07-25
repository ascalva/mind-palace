---
type: finding
id: finding-0176
status: open
created: 2026-07-25
updated: 2026-07-25
links:
  - docs/build-plans/bp-100/plan.md                    # §2.6 mandates the shim; §5 write_scope omits it
  - core/typedshims/lancedb.py                         # the §2.5 boundary that must be widened
  - core/stores/vectorstore.py                         # the defect site — cannot be fully fixed without the above
  - docs/findings/finding-0169.md                      # the warrant bp-100 was written against
  - tests/unit/test_store_cost_ratchet.py              # the two xfail(strict) ratchets this unblocks
ftype: spec-defect
origin_plan: bp-100
route: builder
resolution: null
---

# bp-100 cannot reach its own objective inside its write_scope — the LanceDB typedshim is the fix, and it is not writable

## What

Q3 of bp-100 §3 is **resolved, in the affirmative**: the installed LanceDB *does* support an
in-place column update, and also a projected/filtered read. Verified empirically against the
installed package (not from documentation, and contradicting the `supersede_source` docstring):

```
lancedb 0.33.0     (pyproject.toml:12 pins lancedb>=0.10)
Table.update(where: str | None = None, values: dict | None = None, *,
             values_sql: dict[str, str] | None = None) -> UpdateResult
             # UpdateResult(rows_updated: int, version: int)
Table.count_rows(filter: str | None = None) -> int
Table.search(None) -> LanceEmptyQueryBuilder    # .where(pred) .select([cols]) .limit(0) .to_list()
```

Demonstrated on a throwaway temp store, with a `source_path` containing a single quote:

```
t.update(where="source_path = 'a''b.py' AND current = true", values={'current': False})
  -> UpdateResult(rows_updated=3, version=3)
rows after:  i0 current=False vector=[0.0, 0.5, 0.25]   # vectors byte-identical, untouched
t.search(None).where("source_path = 'a''b.py'").select(['id','current']).limit(0).to_list()
  -> [{'id': 'i0', ...}, {'id': 'i2', ...}, {'id': 'i4', ...}]      # limit(0) == unlimited
```

So `supersede_source` should be **one `update()` call**: zero Arrow→Python materializations, zero
vector marshalling, cost a function of the matched rows. That is exactly finding-0169's bound.

**The contradiction.** bp-100 §2 item 6 states: *"Any new LanceDB surface used here must pass
through [`core/typedshims/lancedb.py`], not around it."* All four surfaces above are new — the shim
today declares only `add / count_rows() / delete(pred) / to_arrow() / search(vector: list[float])`
and an `ArrowTable` exposing only `to_pylist()`. But bp-100 §5 write_scope is
`core/stores/vectorstore.py` + `tests/unit/test_vectorstore*.py` +
`tests/unit/test_store_cost_ratchet.py`. **The one file the fix requires is not writable.**

No honest in-scope substitute exists, and each rejected alternative was checked, not assumed:

* **pyarrow-level filter after `to_arrow()`** — the shim's `ArrowTable` Protocol declares only
  `to_pylist()`; `filter`/`select` are not on it. Same shim, same block.
* **KNN masquerade** — `search(sentinel_vector).where(pred, prefilter=True).limit(BIG)` *is*
  expressible today, but it silently truncates a path deeper than `BIG` (corrupting the amendment
  path, which reuses stored vectors), pollutes rows with `_distance`, and returns them in distance
  order. Worse engineering than the defect it fixes.
* **A local Protocol + `cast` in `vectorstore.py`** — precisely the "around it" §2.6 forbids.

## Why it matters

finding-0169's re-entry condition is *"`supersede_source` cost is independent of total store size
(proven by the ratchet), then bring the daemon up"*. Inside the given write_scope that condition
**cannot be met**. What bp-100 can land in scope is a genuine but partial 2x: two full-table
materializations per `supersede_source` become one, and `delete_source` becomes zero (a pushed-down
`source_path` predicate — no new surface needed, and incidentally the note-amendment hot path at
`core/ingest/index.py:87` too). The remaining term is still **O(total store)**, so the backfill's
wall moves out by 2x rather than away.

The two ratchets that encode the real bound are therefore committed as
`@pytest.mark.xfail(strict=True)` citing this finding. Strict is deliberate: when the pushdown lands
they XPASS and **fail** the suite, forcing the markers off. They are not skipped and not weakened.

## The exact unblock

Widen bp-100's write_scope (or a successor plan's) by one path — `core/typedshims/lancedb.py` — and
apply this patch. It collides with no parallel plan: bp-101 owns `scheduler/**`, bp-102 owns
`ops/**` + `config/**`. It is additive; every existing caller is unaffected. The shim's own
docstring invites exactly this: *"each addition should arrive with the call that needs it."*

```python
class UpdateResult(Protocol):
    """Result of `Table.update` — rows matched-and-written, and the new table version."""
    rows_updated: int
    version: int


class ArrowTable(Protocol):
    def to_pylist(self) -> list[Row]: ...


class VectorQuery(Protocol):
    def metric(self, name: str) -> VectorQuery: ...
    def where(self, predicate: str, *, prefilter: bool = ...) -> VectorQuery: ...
    def select(self, columns: Sequence[str]) -> VectorQuery: ...      # + column projection
    def limit(self, k: int) -> VectorQuery: ...                       # 0 == unlimited
    def to_list(self) -> list[Row]: ...


class VectorTable(Protocol):
    def add(self, rows: Sequence[Mapping[str, object]]) -> None: ...
    def count_rows(self, filter: str | None = ...) -> int: ...        # + filtered count
    def delete(self, predicate: str) -> None: ...
    def update(self, where: str, values: Mapping[str, object]) -> UpdateResult: ...   # + in place
    def to_arrow(self) -> ArrowTable: ...
    def scan(self) -> VectorQuery: ...                                # + `search(None)`, named honestly
```

`scan()` has no direct LanceDB counterpart — it is `search(None)`, whose `None` overload the shim
should absorb rather than leak. Implement it as a tiny adapter in the shim (the shim is the place
where the raw package's overloads are made honest), or widen `search` to
`search(self, vector: list[float] | None) -> VectorQuery` and call `search(None)` from the store —
either is fine; the first keeps the store's intent readable.

With that in place, `core/stores/vectorstore.py` becomes:

```python
def rows_for_source(self, source_path: str) -> list[dict[str, Any]]:
    if TABLE not in self._db.list_tables().tables:
        return []
    return [dict(r) for r in
            self._table().scan().where(f"source_path = {_sql_str(source_path)}").limit(0).to_list()]

def supersede_source(self, source_path: str) -> int:
    if TABLE not in self._db.list_tables().tables:
        return 0
    where = f"source_path = {_sql_str(source_path)} AND current = true"
    return self._table().update(where, {"current": False}).rows_updated
```

— one predicate, no read, no re-land, vectors never touched by construction (which is a *stronger*
guarantee than the vector-equality test bp-100 Item 3 asks for: the bytes are never read, so they
cannot be re-derived or dropped). Both `xfail(strict=True)` markers in
`tests/unit/test_store_cost_ratchet.py` then come off in the same commit.

Caveat to check when it lands: `UpdateResult` is the 0.33 return shape; older `lancedb` in the
`>=0.10` range returned `None` from `update()`. Either raise the floor pin in `pyproject.toml`
(out of bp-100's scope too — `pyproject.toml` is not in any of the three plans' write_scope), or
derive the count from `count_rows(where)` *before* the update, which costs one filtered count and
no materialization. The latter keeps the pin honest and is what a portable implementation should do.

## Re-entry condition

An orchestrator decision on write_scope. Either:

1. **Widen** — add `core/typedshims/lancedb.py` (and, for the pin caveat, optionally
   `pyproject.toml`) to bp-100's write_scope and re-enter Items 2–3 of the plan; the patch above is
   the whole change and the ratchets are already written and already red. Then finding-0169's
   re-entry condition is met and the daemon restart is unblocked; or
2. **Split** — accept bp-100's in-scope 2x as landed, and mint a successor plan owning the shim.
   The daemon then stays down (finding-0169's re-entry condition is not met), or comes up knowing
   the backfill will still wall — at ~2x further in, which does not obviously finish 1,542 versions.

## Routing

`spec-fidelity` → builder. The design question (Q3) is *answered*; nothing here needs the owner.
What is needed is a capability the builder cannot grant itself: one more path in write_scope. Filed
rather than routed around, per the standing rule that a denial means narrow or file, never work
around.
