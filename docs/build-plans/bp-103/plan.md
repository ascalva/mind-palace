---
type: build-plan
id: bp-103
track: ops
status: proposed
design_ref:
  - docs/design-notes/temporal-code-corpus.md
contract: builder
write_scope:
  - core/typedshims/lancedb.py
  - core/stores/vectorstore.py
  - tests/unit/test_store_cost_ratchet.py
  - tests/unit/test_vectorstore*.py
  - tests/unit/test_typedshim*.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 80k
  actual: null
depends_on:
  - bp-100
parallelizable_with:
  - bp-102
created: 2026-07-25
updated: 2026-07-25
links:
  - docs/findings/finding-0176.md
  - docs/findings/finding-0169.md
  - docs/build-plans/bp-100/plan.md
  - docs/build-plans/bp-100/journal.md
re_entry: null
supersedes: null
superseded_by: null
warrant: docs/findings/finding-0176.md
---

# Build Plan — bp-103: widen the LanceDB typedshim so `supersede_source` becomes one in-place update

## 0. Mode & provenance

**Successor to bp-100, not a supersession of it.** bp-100 delivered real work (a `delete_source`
predicate pushdown, one scan instead of two, a latent data-loss fix, and the cost ratchets) and then
**stopped at a capability boundary rather than crossing it** — its own §2.6 mandates that new LanceDB
surface pass through the typedshim, and §5 did not make that shim writable. The builder filed
finding-0176 carrying the complete patch and three rejected alternatives.

The successor route was the **owner's call** (2026-07-25): *"I also lean successor plan, adds more
rich history, and documents the resolution."* Widening a blessed `write_scope` in place would have
erased the reason the boundary was hit; a successor records it. Authority-to-act is that instruction;
`proposed → ready` remains owner-only.

**This plan is what actually meets finding-0169's re-entry condition** and therefore unblocks the
daemon restart. bp-100 alone moved the wall out ~2×; it did not remove it.

## 1. Objective

Make `supersede_source` a single in-place `update()` — zero Arrow→Python materializations, zero
vector marshalling — by widening `core/typedshims/lancedb.py` with the surface that requires.

## 2. Context manifest

Read in order:

1. `docs/findings/finding-0176.md` — **whole file.** It contains the verified API surface, the exact
   shim patch, the exact `vectorstore.py` bodies, the three rejected alternatives, and the version
   caveat. This plan is its execution.
2. `core/typedshims/lancedb.py` — the §2.5 boundary. Note its own docstring: *"each addition should
   arrive with the call that needs it."* This plan is that call.
3. `core/stores/vectorstore.py` — **at merged-bp-100 state**, which introduces `_sql_str` and the
   pushed-down `delete_source`. Do NOT read the pre-bp-100 version.
4. `tests/unit/test_store_cost_ratchet.py` — the two `xfail(strict=True)` ratchets this plan turns
   green (and which will then FAIL as XPASS until the markers come off).
5. `docs/findings/finding-0169.md` — the warrant behind the warrant; its re-entry condition is the
   acceptance bar for the whole ops restart.

**DRY audit.** `_sql_str` already exists (bp-100) — reuse it, do not write a second escaper. The
predicate-pushdown idiom already exists in `search()`. The shim already declares
`add/count_rows/delete/to_arrow/search`; this is an **additive widening**, not a rewrite.

## 3. Investigation & grounding

- **Q1 — Does the pinned LanceDB support in-place update?** YES, verified empirically by the bp-100
  builder against the installed package (not documentation): `lancedb 0.33.0`,
  `Table.update(where, values) -> UpdateResult(rows_updated, version)`, demonstrated on a temp store
  with a single-quoted path, vectors byte-identical after. See finding-0176.
- **Q2 — Why can this not be done in `vectorstore.py` alone?** The shim declares only
  `add/count_rows()/delete(pred)/to_arrow()/search(vector: list[float])`, and its `ArrowTable`
  Protocol exposes only `to_pylist()`. All four needed surfaces are new. Three alternatives were
  checked and rejected: pyarrow-level filter (not on the Protocol), KNN masquerade with a sentinel
  vector (silently truncates deep paths, pollutes with `_distance`, distance-orders results), and a
  local Protocol + `cast` (precisely the "around it" §2.6 forbids).
- **Q3 — ⚑ Version-pin caveat.** `pyproject.toml:12` pins `lancedb>=0.10`, but `UpdateResult` is the
  0.33 return shape — **older versions in that range returned `None` from `update()`.** `pyproject.toml`
  is in NO plan's write_scope. **Code does not settle which is preferable; this plan takes the
  portable route** (see §7 Item 2): derive the count from a filtered `count_rows(where)` *before* the
  update. One filtered count, no materialization, and the pin stays honest.
- **Q4 — Does this collide with the parallel plans?** No. bp-101 owns `scheduler/**`, bp-102 owns
  `ops/**` + `config/**`. Verify at spawn time that bp-100 has merged (this plan depends on it).

## 4. Reconciliation

- `core/typedshims/lancedb.py` — **cross-ref: extension.** Additive Protocol widening; every existing
  caller is unaffected. The shim's docstring already sanctions the pattern; cite finding-0176.
- `core/stores/vectorstore.py` `supersede_source` — **banner: correction.** bp-100 left a
  `[cross-ref: extension]` noting the re-land was retained but bounded. That note becomes wrong: the
  re-land is **deleted entirely**. Replace it with a correction banner recording that the docstring's
  original portability claim ("no dependency on a LanceDB in-place `update`") was false at the pinned
  version, warrant finding-0176.
- `tests/unit/test_store_cost_ratchet.py` — the `xfail(strict=True)` markers must be **removed in the
  same commit** as the fix. Leaving them turns a passing fix into a suite failure by design.

## 5. Write scope

- `core/typedshims/lancedb.py` — the widening (`UpdateResult`, `update`, filtered `count_rows`,
  `scan()`/projection on the query Protocol).
- `core/stores/vectorstore.py` — `rows_for_source` and `supersede_source` only.
- `tests/unit/test_store_cost_ratchet.py` — drop the two `xfail` markers.
- `tests/unit/test_vectorstore*.py`, `tests/unit/test_typedshim*.py` — coverage.

Deliberately OUT: **`pyproject.toml`** (the pin stays untouched — §7 Item 2 takes the portable
route instead), `core/ingest/**`, `scheduler/**` (bp-101), `ops/**` (bp-102), design notes, the
foundation denylist. The live store at `data/vectors.lance` is never touched; temp stores only.

## 6. Interfaces pinned inline

The verified installed surface (finding-0176, empirical):

```
lancedb 0.33.0
Table.update(where: str | None = None, values: dict | None = None, *,
             values_sql: dict[str, str] | None = None) -> UpdateResult
             # UpdateResult(rows_updated: int, version: int)
Table.count_rows(filter: str | None = None) -> int
Table.search(None) -> LanceEmptyQueryBuilder   # .where(pred) .select([cols]) .limit(0) .to_list()
                                               # NOTE: limit(0) == UNLIMITED
```

The shim patch (copy verbatim; `scan()` is `search(None)` named honestly, absorbing the overload
rather than leaking it):

```python
class UpdateResult(Protocol):
    rows_updated: int
    version: int

class VectorQuery(Protocol):
    def metric(self, name: str) -> VectorQuery: ...
    def where(self, predicate: str, *, prefilter: bool = ...) -> VectorQuery: ...
    def select(self, columns: Sequence[str]) -> VectorQuery: ...
    def limit(self, k: int) -> VectorQuery: ...
    def to_list(self) -> list[Row]: ...

class VectorTable(Protocol):
    def add(self, rows: Sequence[Mapping[str, object]]) -> None: ...
    def count_rows(self, filter: str | None = ...) -> int: ...
    def delete(self, predicate: str) -> None: ...
    def update(self, where: str, values: Mapping[str, object]) -> UpdateResult: ...
    def to_arrow(self) -> ArrowTable: ...
    def scan(self) -> VectorQuery: ...
```

The target store bodies (adapted for Q3's portable count — note the deviation from the finding):

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
    flipped = self._table().count_rows(where)      # portable: do NOT rely on UpdateResult (Q3)
    if flipped:
        self._table().update(where, {"current": False})
    return flipped
```

**Contract unchanged from bp-100:** returns rows flipped `current=true → false`; superseded rows are
RETAINED; already-superseded rows untouched; a path with nothing current is a no-op returning 0.

## 7. Items

Blast-radius order: the boundary widening (additive, no behavior change) → the store rewrite → the
ratchet markers.

### Item 1 — Widen the typedshim

- **Objective:** the Protocols in §6 exist and typecheck; no existing caller changes.
- **Files:** `core/typedshims/lancedb.py`, `tests/unit/test_typedshim*.py`.
- **Acceptance test:** `uv run mypy core agents eval ops scheduler scripts` clean; `ops.type_gate`
  passes; every pre-existing shim caller compiles unchanged.
- **Falsifier:** the widening leaks the raw package's overloads into callers — e.g. a caller has to
  pass `None` to `search` to mean "scan". If `scan()` is not honest, the shim has failed its purpose.
- **Invariants:** §2.5 boundary intact — `core` still imports no zone/networking module
  (`scripts/check_imports.py`).
- **Touches stored data?** No. **Parallelizable?** No (gates Item 2). **Depends on:** bp-100 merged.

### Item 2 — `supersede_source` becomes one in-place update

- **Objective:** zero materializations; the flip never reads the `vector` column.
- **Files:** `core/stores/vectorstore.py`, `tests/unit/test_vectorstore*.py`.
- **Acceptance test:** the cost ratchet shows cost independent of unrelated store size; idempotence
  test (second call returns 0, rows unchanged) still green.
- **Falsifier:** ⚑ **a path containing a single quote, or deeper than any implicit limit, is
  mis-updated.** Test `"notes/it's a  café/π.md"` against a `notes/it` prefix decoy, and a path with
  more rows than any default `limit`. (`limit(0)` means unlimited — if that is wrong, deep paths
  silently under-update, which is worse than the original defect.)
- **Invariants:** keep-and-link semantics; **vectors are never read, therefore cannot be re-derived
  or dropped** — a strictly stronger guarantee than bp-100 Item 3's equality assertion, which should
  be kept anyway as a regression net.
- **Touches stored data?** No — temp stores only. **Depends on:** Item 1.

### Item 3 — Retire the `xfail(strict=True)` markers

- **Objective:** the two ratchets pass as ordinary tests, in the same commit as Item 2.
- **Files:** `tests/unit/test_store_cost_ratchet.py`.
- **Acceptance test:** full suite green with no XPASS.
- **Falsifier:** a marker is removed while its ratchet still measures the OLD bound — i.e. the test
  was weakened to pass rather than the code fixed. Re-read each assertion before touching the marker.
- **Invariants:** the ratchets keep asserting on counted materializations, never wall-clock.
- **Touches stored data?** No. **Depends on:** Item 2.

## 8. Math carried explicitly

- **Cost of `supersede_source`** — *measures:* rows/columns materialized per call as a function of
  (rows for the path `d`, total rows `N`). *valid when:* the predicate pushdown and in-place update
  are exact. *fails its keep if:* measured cost still grows with `N` at fixed `d`. Target after this
  plan: **O(1) materializations** (the update is server-side); bp-100 reached 1, HEAD was 2.

## 9. Non-goals

- **Not** the membership store (finding-0168) — this is the bridge, not the destination.
- **Not** `pyproject.toml` / the version pin (Q3 takes the portable route deliberately).
- **Not** the daemon restart, the backfill, or clearing the queue — those are orchestrator actions
  after all merges.
- **Not** other `vectorstore.py` methods (`all_rows`'s vector projection stays a follow-up finding).

## 10. Stop-and-raise conditions

- The installed LanceDB does not behave as finding-0176 recorded (version drift since it was
  written) → STOP, re-verify empirically, file a finding. **Do not adapt silently.**
- `limit(0)` turns out NOT to mean unlimited → STOP; deep-path truncation is a corpus-integrity risk.
- Widening the shim would require reaching outside `core/typedshims/lancedb.py` → STOP and file.
- The Item 3 falsifier fires (a ratchet was weakened rather than the code fixed) → STOP.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| Count source for the return value | `count_rows(where)` before update (portable) | Trust `UpdateResult.rows_updated` — 0.33-only; the `>=0.10` pin admits versions returning `None` | The pin floor is raised in a plan that owns `pyproject.toml` |
| `scan()` vs widening `search` to accept `None` | `scan()` — keeps store intent readable | Widen `search`; leaks the raw overload the shim exists to absorb | Reviewer prefers the other on merge |
| `all_rows` vector projection | Out of scope | Fix here (widens beyond the blocker) | Follow-up finding after the restart |

## 12. Dependency & ordering summary

Sequential: **Item 1 → Item 2 → Item 3**, all three ideally in one commit for Items 2–3 (the marker
removal must not lag the fix).

Across plans: **`depends_on: bp-100`** — this plan edits `vectorstore.py` at its post-bp-100 state and
reuses `_sql_str`. `parallelizable_with: bp-102` (disjoint: `ops/**` vs `core/**`). bp-101 has already
returned. **This is the plan that satisfies finding-0169's re-entry condition and therefore gates
`palace up`** — the restart checklist runs only after this merges.
