# Journal — bp-103: widen the LanceDB typedshim so `supersede_source` becomes one in-place update

## Session 1 — 2026-07-25 (delegated builder, worktree `worktree-agent-a27140efc5365e8f4`)

### Checkpoint 0 — setup correction: the worktree was based BEHIND `main`

The worktree branch was created at `cb6f1fa` (the bp-103 `proposed→ready` blessing) — which
**predates the bp-100/101/102 seals**. So `core/stores/vectorstore.py` in the worktree was the
PRE-bp-100 version (no `_sql_str`, id-list `delete_source`), and `docs/findings/finding-0176.md`
did not exist at all. The plan's §2 manifest and my task both require the merged-bp-100 state.

`HEAD` was a strict ancestor of `main`, so the fix was a clean fast-forward, no authored content:

```
git merge --ff-only main      # cb6f1fa..ed72554
```

Now at `ed72554` (`seal(bp-100/101/102) records`). `_sql_str` is present at
`core/stores/vectorstore.py:71`; `finding-0176`, `tests/unit/test_store_cost_ratchet.py`, and
`tests/unit/test_vectorstore_supersede.py` are all present. **A fresh agent resuming this plan must
verify its base contains `_sql_str` before reading anything else.**

### Checkpoint 1 — grounding: finding-0176 re-verified empirically against the installed package

Plan §10 makes "the installed LanceDB does not behave as finding-0176 recorded" a stop-and-raise, so
the surface was re-probed on a throwaway temp store (`/tmp`, never `data/vectors.lance`) before a
line of code was written. **Every claim in the finding held.** Installed: `lancedb 0.33.0`,
CPython 3.13.14. Probe used a 188-row table: 137 rows on the nasty path `notes/it's a  café/π.md`,
1 decoy row on the shared-prefix path `notes/it`, 50 unrelated rows.

| Probe | Result |
|---|---|
| `search(None)` builder type | `LanceEmptyQueryBuilder` |
| `.where(pred).to_list()` with no `.limit()` | 137 rows (0.33 empty-query has no default cap) |
| **`.where(pred).limit(0).to_list()`** | **137 rows — `limit(0)` IS unlimited, confirmed** |
| `.select(["id","current"]).limit(0)` | 137 rows, keys exactly `['current','id']` — projection works |
| `.limit(0)` with no `select` | keys `['current','id','source_path','vector']` — vector still carried |
| `count_rows(pred)` positional **and** `count_rows(filter=pred)` | both `137` |
| `update(where, {"current": False})` | `UpdateResult(rows_updated=137, version=3)` |
| after update | `current=true` → 0, `current=false` → 137 (deep path fully updated, no truncation) |
| decoy `notes/it` after update | still `current=true` (prefix decoy untouched, `_sql_str` escaping holds) |
| total rows after update | 188 — **nothing deleted**, keep-and-link intact |

Signatures as recorded:
`update(where: Optional[str] = None, values: Optional[dict] = None, *, values_sql=None) -> UpdateResult`
· `count_rows(filter: Optional[str] = None) -> int`
· `search(query: Optional[...] = None, ...) -> LanceQueryBuilder`.

**`limit(0) == unlimited` is empirically confirmed** (plan §10's sharpest stop condition — cleared).
The 137-row deep path is deliberately >10, LanceDB's default vector-search cap.

### Checkpoint 2 — blast-radius survey before touching the shim

`core/typedshims/lancedb.py` has exactly **one** importer: `core/stores/vectorstore.py:22`
(`VectorTable, connect`). Two tests reach a store's `_db` handle directly:

* `tests/unit/test_vectorstore_supersede.py:196` — `pre._db.create_table(TABLE, schema=legacy).add(...)`
* `tests/integration/test_code_vector_isolation.py:109,123` — `store._db.create_table(...).add(...)`
  and `store2._db.list_tables().tables`

`tests/unit/test_code_corpus.py:288` uses raw `lancedb.connect` directly, bypassing the shim — it is
unaffected by anything here.

**The design consequence that is NOT obvious from the plan text.** The shim today is a *pure typing
facade*: `connect()` returns the raw object annotated as `VectorDB`; nothing is wrapped at runtime.
But `scan()` **has no counterpart on the raw `Table`** — it is `search(None)`. So Item 1's falsifier
("if `scan()` is not honest, the shim has failed its purpose") can only be met by a **real runtime
adapter**, which in turn means `open_table`/`create_table` must return adapted tables, which means
`connect()` must return an adapted DB. That is the shape finding-0176 sanctions ("implement it as a
tiny adapter in the shim") and plan §11 pins over the `search(None)`-leaking alternative.

The adapters are written out **explicitly**, not with `__getattr__` forwarding: a `__getattr__`
wrapper would launder `Any` straight back into the checked region, which is the exact thing the
module docstring says the shim exists to stop.

### Checkpoint 3 — Item 1 CLOSED (commit `2674d93`)

`core/typedshims/lancedb.py`: `UpdateResult` Protocol; `count_rows(filter)`, `update()`, `scan()`
on `VectorTable`; `select()` on `VectorQuery`. Plus the runtime `_DB`/`_Table` adapters that make
`scan()` exist. `connect()` returns `_DB(lancedb.connect(uri))`.

Adapter design choices, each load-bearing:

* **Explicit methods, no `__getattr__`.** A blind proxy would satisfy the Protocol structurally
  while re-laundering `Any` into the checked region. `test_the_adapter_exposes_the_declared_surface_and_nothing_else`
  asserts `compact_files` (real on the raw table, undeclared here) raises `AttributeError`.
* **`_DB` exists only so `open_table`/`create_table` return `_Table`.** Without it `VectorStore._table()`
  would return an adapter on the create branch and a raw table on the open branch — a bug that
  shows only on the *second* call.
* **`__slots__` on both**, so a typo'd attribute is an error rather than a silent new field.

New file `tests/unit/test_typedshim_lancedb.py`, 13 tests. Item 1's falsifier
("the widening leaks the raw overloads — a caller passes `None` to `search`") is itself a test:
`test_scan_is_honest_no_caller_passes_none_to_mean_no_vector` reads `inspect.signature` and fails
if anyone widens `search` to `list[float] | None`. The `limit(0) == unlimited` claim is pinned on a
137-row path (>> the default cap of 10) so version drift fails loudly.

Item 1 gate: `ruff` clean · `mypy core agents eval ops scheduler scripts` — 255 files, no issues ·
`ops.type_gate` OK · `scripts/check_imports.py` OK (§2.5 boundary intact) ·
`test_typedshim_lancedb.py` 13 passed · pre-existing store tests
(`test_vectorstore_supersede` + `test_store_cost_ratchet` + `test_code_corpus` +
`test_code_vector_isolation`) **33 passed, 2 xfailed** — the two ratchets still correctly xfail,
because the store itself has not changed yet. That is the proof Item 1 is genuinely additive.

### Checkpoint 4 — Items 2 + 3 built (one commit, per plan §12)

**`rows_for_source`** → `scan().where(source_path = …).limit(0).to_list()`, no `select()`
projection (the caller came for `vector`; the amendment path reuses those vectors instead of
re-embedding). Probed first: `scan().to_list()` rows are **byte-identical** to
`to_arrow().to_pylist()` rows — same keys, same Python types, `scan_row == arrow_row` is `True`,
vector elements are `float` both ways. So it is a genuine drop-in for `core/ingest/sync.py:117`.

**`supersede_source`** → `count_rows(where)` then, only if non-zero, `update(where, {"current": False})`.
`self._table()` is bound ONCE rather than called twice as in the §6 snippet — same semantics, one
fewer `list_tables()` + `open_table()` round trip; not a design deviation.

The §11 deviation from finding-0176 is honoured: the count comes from `count_rows`, **not** from
`UpdateResult.rows_updated`, because `pyproject.toml:12` pins `lancedb>=0.10` and older members of
that range returned `None`. `pyproject.toml` was not touched. The rationale is written into the
`supersede_source` docstring and into the `UpdateResult` Protocol docstring, so the next reader
does not "fix" it back.

Docstrings reconciled per plan §4: `rows_for_source` and `supersede_source` both carry
`[banner: correction]`; bp-100's `[cross-ref: extension]` (re-land retained-but-halved) is retired,
since the re-land is deleted entirely.

**Item 3 — the markers.** Both `xfail(strict=True)` markers removed. Ruff then flagged
`pytest imported but unused`, which is the mechanical confirmation that those two were the file's
last markers. A comment now stands where the import was, so re-introducing an xfail is a visible act.

### Checkpoint 5 — the two sharp falsifiers, and one I had to build the instrument to answer

**Item 2 falsifier (a) — the single quote.** Already covered by bp-100's
`test_a_path_with_a_quote_is_read_and_superseded_correctly` (`notes/it's a  café/π.md` against a
`notes/it` prefix decoy); it now exercises the pushed-down predicate rather than a Python filter,
and passes. Reinforced at the shim level by `test_scan_predicate_does_not_leak_into_a_prefix_neighbour`.

**Item 2 falsifier (b) — the deep path.** New:
`test_a_path_deeper_than_any_default_limit_is_fully_read_and_fully_flipped` — 137 rows on one path
(>> LanceDB's default cap of 10). Asserts the READ is not truncated, the count is not truncated,
**all** 137 flip, nothing is deleted, the neighbour is untouched, and a second call returns 0.
`limit(0) == unlimited` was confirmed empirically BEFORE any code was written (Checkpoint 1) — plan
§10's sharpest stop condition, cleared, not assumed.

**Item 3 falsifier — "the test was weakened rather than the code fixed."** This is where the real
work was. Re-reading the ratchets before touching the markers turned up a problem the plan does not
mention: **bp-100's meter counts only `to_arrow().to_pylist()`, and bp-103's pushdown reads through
`scan().…to_list()` — a route the meter cannot see at all.** Removing the markers against the old
instrument would have produced two green ratchets whose zero measured the meter's blindness as much
as the store's cost. So the instrument was widened (`tests/unit/test_store_cost_ratchet.py` is in
write_scope): a chainable `_CountingQuery` now counts `scan()`/`search()` reads onto the same
`rows`/`vector_floats` totals, with a separate `scan_reads` counter, and `materializations` keeps
its narrower "FULL-table Arrow pull" meaning. Both original assertions are **unchanged**; each
gained a trailing assertion pinning that the bound is now *zero*, not merely *equal* (equality
alone would also hold if both sides scanned everything — which is exactly the state finding-0169
measured). A second negative control, `test_the_instrument_also_sees_the_pushed_down_scan_route`,
proves the new counter is wired to a read that really happens.

**Mutation check — the ratchets are not theatre.** `git stash push -- core/stores/vectorstore.py`
(reverting the store to bp-100 HEAD while keeping the new tests), then re-run:

```
FAILED test_supersede_cost_is_independent_of_unrelated_store_size  - cost grows with unrelated store size: 4 rows at N=4, 204 rows at N=204
FAILED test_supersede_does_not_marshal_the_vector_column_of_unrelated_rows - assert 1632 == 32
FAILED test_rows_for_source_reads_only_that_paths_rows             - rows_for_source still pulls the whole table through Arrow
FAILED test_the_instrument_also_sees_the_pushed_down_scan_route    - the scan route is invisible to the meter
4 failed, 3 passed
```

The ratchets still measure the OLD bound and still fail against the OLD code. The marker removal is
therefore a consequence of the fix, not a substitute for it. Stash popped; 35/35 green again.

Also added `test_supersede_never_reads_or_rewrites_the_vector_column`: a table spy records which
columns each `update` NAMES, asserting exactly `[{"current"}]`. That is bp-103's structural
guarantee (the vector column is never read, so it cannot be re-derived or dropped) as distinct from
bp-100's byte-equality test — which is KEPT as the regression net the plan asks for.

### Checkpoint 6 — finding-0180 filed (`design` → orchestrator)

`docs/findings/finding-0180.md`. The pushed-down predicate NAMES the `current` column, so on a
pre-bp-099 store whose schema lacks it, `supersede_source` now RAISES where it used to return 0.
Verified empirically (`Schema error: No field named current`).

The old silence was the worse outcome and this is not a regression to undo: `code_corpus.sync`
supersedes BEFORE it adds, and the `add` that follows arms `_migrate_current_if_needed`, which
stamps every row `current=true` — so the old path left the superseded version AND the new HEAD both
current (silent D3 corruption) while reporting `superseded_rows=0`. Loud beats silent-and-wrong.

What is ROUTED, not resolved: whether the migrations should arm on `supersede_source` too. The
obvious fix re-imports finding-0169's own cost — `_migrate_current_if_needed` does a full
`to_arrow().to_pylist()` merely to *probe* the schema (`vectorstore.py:133`), ~11.7 s at live-store
scale, on every fresh instance. That trade is a design call, and the migrations are a §9 non-goal
and outside write_scope. Recorded behavior is pinned by
`test_supersede_on_an_unmigrated_pre_current_store_fails_loudly`, and
`test_rows_for_source_still_works_on_an_unmigrated_pre_current_store` pins that the READ is
schema-agnostic (it predicates on `source_path`, which every schema version has).

**Believed unreachable in production, but that belief is inferred, not measured**: finding-0169
records the backfill actually flipping rows through 847 of ~1,542 versions, which is only possible
on a store that already has the column. bp-103 deliberately did not open `data/vectors.lance`.
**The finding asks the restart checklist to confirm it once, cheaply.**

### Checkpoint 7 — finding-0181 filed (`codebase` → orchestrator), and Items 2+3 committed (`d30a22d`)

Landing Item 1 quietly falsified two written claims in `ops/lifecycle/snapshot.py` (bp-102's file,
merged one commit before this plan started, and OUT of bp-103's write_scope):

* `:293` — *"Anything wider (`all_rows`, `rows_for_source`, `search`, `to_arrow`) does a full
  `to_pylist()`"*. `rows_for_source` no longer does.
* `:310` — the `current=true/false` status split is parked because `count_rows(filter=…)` on the
  typedshim *"plus a method on `core/stores/vectorstore.py`"* are both missing. **The first half
  now exists** (Item 1). Only the store method remains, and it is ~5 lines.

I deliberately did NOT write that method, even though `core/stores/vectorstore.py` IS in my
write_scope. It is bp-102's parked deliverable; helping myself to another plan's criterion because
the file happens to be writable is the "route around the boundary" move the standing rule forbids.
Filed as finding-0181 with the candidate body, for an orchestrator scoping call.

The split matters more than a cosmetic status figure: it is the observable that says whether the
temporal corpus is working, on the very restart this plan unblocks.

Items 2+3 committed as **one** commit (`d30a22d`), per plan §12.

### Checkpoint 8 — gate results

Run as five SEPARATE legs (never `&&`-chained, so the argless-mypy baseline can be read):

| Leg | Result |
|---|---|
| `uv run ruff check .` | `All checks passed!` (exit 0) |
| `uv run mypy core agents eval ops scheduler scripts` | `Success: no issues found in 255 source files` (exit 0) |
| `uv run mypy` (argless) | `Found 69 errors in 20 files (checked 544 source files)` — **baseline 69, exactly** |
| `uv run python -m ops.type_gate` | Tier-2 membership OK · bare-ignore scan OK (exit 0) |
| `uv run pytest -q` (bare, as tasked) | `2 failed, 2031 passed, 15 skipped in 710.67s` — **both failures pre-existing / environmental, neither mine; each individually disproved below** |
| `uv run pytest -q --deselect …::test_core_imports_nothing_outside_core` (the documented green gate) | **`2032 passed, 15 skipped, 1 deselected in 533.88s`** — fully green, uncontended, no XPASS |

The argless leg initially read **71** — I had added two. Both were in the new
`test_supersede_never_reads_or_rewrites_the_vector_column` spy, whose `update` signature did not
match the `VectorTable` Protocol (`values: dict[str, Any] -> Any` vs
`values: Mapping[str, object] -> UpdateResult`). Fixed by making the spy structurally conform
rather than by widening the ignore — the honest fix, and it means the spy is checked against the
same Protocol the store calls. Back to 69.

Also run (not in the five legs, but the §2.5 invariant Item 1 claims):
`uv run python scripts/check_imports.py` → *"Import firewall (I2): OK — core imports no zone
(edge/cloud) or networking module"*.

**The two suite failures, each disproved rather than waved past.** A builder claiming "pre-existing"
without showing it is exactly the move the plan's Item 3 falsifier warns about, so both were made
to fail-or-pass on evidence:

1. `tests/unit/test_core_self_containment.py::test_core_imports_nothing_outside_core` — the
   red-by-design finding-0105 ratchet the documented green gate **deselects** (PROGRESS.md:4480:
   *"ONLY failure is `test_core_imports_nothing_outside_core` AND its count is monotone
   non-increasing"*). Its bar is the COUNT, so the count was measured on both sides:
   `git checkout ed72554 -- core/` (the plan's base) → **20 forbidden imports**; restored to
   `d30a22d` → **20**. Unchanged, as it must be — the 20 live in `core/dreaming/shadow.py`,
   `core/effect_proposal.py`, `core/factory/factory.py`, `core/ingest/code_corpus.py`,
   `core/interface.py`, `core/ops_view.py`, `core/reference_view.py`, `core/sensing.py`,
   `core/temporal/spine.py`, and **none in `core/stores/` or `core/typedshims/`**. Both files this
   plan touches import only `lancedb`, `pyarrow` and `core.*`.

2. `tests/e2e/test_scheduler_live.py::test_supervisor_dispatches_a_real_job` —
   `AssertionError: assert ''`, i.e. the live model returned empty. **Re-run in isolation once the
   other worktree's suite had finished: 1 passed in 112.93s.** It is a `pytest.mark.live` test that
   dispatches a real Ollama generation, and its own preamble comment names the failure mode:
   *"free any models left warm by prior live tests so Ollama isn't mid-swap … otherwise a cold
   generation can queue behind a load and time out."* Two suites were sharing one Ollama. This plan
   touches no model, no network and no scheduler.

**Operational note for a fresh agent.** The full-suite leg sat at 0.0% CPU for minutes. `sample`
showed the main thread parked in `sock_recv_into` → `poll` (a socket read), **not** in
`fcntl_flock_impl`, and no `/tmp/mp-live-ollama-*.lock` existed — a second suite was running on the
main worktree at 99.3% CPU for 20+ minutes and this one was queuing behind it at the live-model
HTTP layer rather than the file lock. Same wait, different mechanism. Not a hang, and nothing to do
with this plan's code (which touches no network).

### Checkpoint 9 — acceptance ledger and hand-off

| Plan item | Acceptance test | State |
|---|---|---|
| **Item 1** — widen the typedshim | mypy clean · `type_gate` passes · every pre-existing caller compiles unchanged | **MET** — 255 files clean; the shim's one importer (`core/stores/vectorstore.py`) needed no change for Item 1; store tests were 33 passed / 2 xfailed against the widened shim BEFORE the store moved, which is the proof it is additive |
| **Item 1 falsifier** — the raw overload leaks | `test_scan_is_honest_no_caller_passes_none_to_mean_no_vector` reads `inspect.signature` and fails if `search` is ever widened to accept `None`; `test_the_adapter_exposes_the_declared_surface_and_nothing_else` fails if the adapter becomes a blind proxy | **DID NOT FIRE** |
| **Item 2** — one in-place update | cost ratchet shows cost independent of unrelated store size · idempotence still green | **MET** — `supersede_source` is `count_rows` + `update`; measured cost is 0 rows / 0 materializations / 0 scans at every store size |
| **Item 2 falsifier (a)** — single quote | `test_a_path_with_a_quote_is_read_and_superseded_correctly` (`notes/it's a  café/π.md` vs `notes/it` decoy) | **DID NOT FIRE** |
| **Item 2 falsifier (b)** — deep path | `test_a_path_deeper_than_any_default_limit_is_fully_read_and_fully_flipped` (137 rows) + `limit(0)` confirmed unlimited empirically before coding | **DID NOT FIRE** |
| **Item 3** — retire the markers | full suite green with no XPASS | **MET** — both markers gone (proved by ruff flagging the now-unused `pytest` import); no xfail/xpass in the three touched files |
| **Item 3 falsifier** — ratchet weakened not fixed | mutation check: revert only `vectorstore.py`, keep the tests | **DID NOT FIRE** — 4 failures reappear, incl. both ratchets. Assertions unchanged; instrument *strengthened* |
| **§8 math** — O(1) materializations | `(rows, materializations, scan_reads) == (0, 0, 0)` at N=204 | **MET** — HEAD was 2, bp-100 reached 1, bp-103 reaches 0 |

**finding-0169's re-entry condition is met:** *"`supersede_source` cost is independent of total
store size (proven by the ratchet), then bring the daemon up."* Proven, by a ratchet that is now an
ordinary green test and that still fails against the old code.

**Hand-off to the orchestrator.**

* The daemon is still **down** and was never started, per the task frame. `data/vectors.lance` was
  never opened; every probe and test used `tmp_path` or `/tmp`.
* **Add one cheap check to the restart checklist** before `code_corpus.sync()` runs: confirm the
  live store's schema carries `current`. finding-0180 explains why (the new predicate names that
  column) and why it is believed already present but not measured.
* finding-0181 asks whether bp-102's now-half-unblocked `current=true/false` status split should be
  folded into a follow-up; either way two docstrings in `ops/lifecycle/snapshot.py` now assert a
  constraint that no longer holds.
* Plan status NOT flipped — the orchestrator's call on acceptance. `proposed→ready` and
  `draft→ratified` were never touched.

**Commits on `worktree-agent-a27140efc5365e8f4`** (branched from `ed72554`):

* `2674d93` `feat(typedshims): widen the LanceDB shim with update/filtered-count/select/scan` — Item 1
* `d30a22d` `perf(stores): supersede_source becomes one in-place update — the O(N) term is gone` — Items 2+3

**Status:** Items 1–3 COMPLETE and committed. Two findings filed (0180 `design`, 0181 `codebase`,
both routed to the orchestrator). Nothing parked, nothing blocked.
