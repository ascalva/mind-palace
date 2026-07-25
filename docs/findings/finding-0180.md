---
type: finding
id: finding-0180
status: open
created: 2026-07-25
updated: 2026-07-25
links:
  - docs/build-plans/bp-103/plan.md                    # §6 pins the body this finding annotates
  - core/stores/vectorstore.py                         # supersede_source / _migrate_current_if_needed
  - core/ingest/code_corpus.py                         # sync() supersedes BEFORE it adds
  - docs/findings/finding-0176.md                      # the patch bp-103 executed
  - docs/findings/finding-0169.md                      # the O(N) bound the migration probe re-imports
  - tests/unit/test_vectorstore_supersede.py           # pins the recorded behavior
ftype: design
origin_plan: bp-103
route: orchestrator
resolution: null
---

# The schema migrations arm only on `add()` — and after bp-103, `supersede_source` reaches a column they may not have created yet

## What

bp-103 replaced `VectorStore.supersede_source`'s read-delete-re-add body with one pushed-down
predicate (finding-0176, plan §6):

```python
where = f"source_path = {_sql_str(source_path)} AND current = true"
flipped = table.count_rows(where)
if flipped:
    table.update(where, {"current": False})
```

That predicate **names the `current` column**. On a store whose schema predates bp-099 it does not
exist, and LanceDB raises:

```
RuntimeError: lance error: Invalid user input: Schema error: No field named current.
```

(verified empirically on a temp store, lancedb 0.33.0). The two additive migrations that create
that column — `_migrate_layer_if_needed` and `_migrate_current_if_needed` — arm **only from
`add()`**, once per `VectorStore` instance. And `core/ingest/code_corpus.py:293,298` calls
`supersede_source` **before** the `add` inside `_embed_and_land`. So on an unmigrated store, the
first thing `sync()` does now raises.

**The old body did not raise — and that was worse.** It materialized the table, computed
`sum(1 for r in rows if r.get("current"))`, found no such key, and returned a clean `0`. Then
`_embed_and_land` → `store.add(...)` armed `_migrate_current_if_needed`, which stamps **every**
existing row `current=true` — including the version that should have just been superseded. Net
result: the old version and the new HEAD both `current=true`, i.e. silent corruption of the D3
current-view, reported to the caller as `superseded_rows=0`. bp-103 converts a silent wrong answer
into a loud failure. That is an improvement, and it is pinned by
`test_supersede_on_an_unmigrated_pre_current_store_fails_loudly`.

## Why it matters

Three reasons this is routed rather than settled in-plan:

1. **It is a design call about where migrations arm, not a bug in bp-103.** The obvious "fix" —
   call `self._migrate_current_if_needed()` at the top of `supersede_source` — would re-import
   exactly the cost finding-0169 exists to remove. Look at the migration's own body: even on an
   ALREADY-migrated store it does a full `to_arrow().to_pylist()` just to *check* the schema
   (`vectorstore.py:133`). That is one full O(N) materialization — 11.7 s at the live store's
   22,621 rows × 2560 dims, per finding-0169's own measurement — paid on the first
   `supersede_source` of every fresh instance. Trading a loud failure on a legacy store for an
   11-second scan on every healthy one is not a trade a builder should make unilaterally.

2. **The migration probe is O(N) regardless, and nobody has costed it.** Independently of the above:
   `add()` pays *two* such probes (layer + current) on the first call per instance. In the
   `code_backfill` job that is once per process, not per version — so it is not the wedge
   finding-0169 diagnosed — but it is still a full-table Arrow materialization at process start,
   on the same hot store, for a question (`is the `current` column present?`) that a schema read
   answers in O(1). The typedshim now has the surface to do it properly (`scan().limit(1)`, or a
   one-line `schema` accessor). This is cheap to fix and out of bp-103's write_scope
   (`_migrate_*` are "other `vectorstore.py` methods", plan §9 non-goal).

3. **Reachability is believed nil, but that belief is inferred, not measured.** The live store is
   almost certainly already migrated: bp-099 shipped `current`, and finding-0169 records the
   backfill actually flipping rows through 847 of ~1,542 versions, which is only possible on a
   store that has the column. bp-103 deliberately did **not** open `data/vectors.lance` to confirm
   (temp stores only, per its own §5), so this is reasoning, not evidence. **The restart checklist
   is the natural place to check it once, cheaply.**

## Options

| Option | Cost | Consequence |
|---|---|---|
| **A. Leave as landed** (loud failure) | zero | Correct for every migrated store; a legacy store fails at `sync()` with a legible schema error instead of corrupting silently. Recorded default. |
| **B. Arm the migration in `supersede_source`** | one full O(N) materialization per instance | Legacy stores self-heal, but every healthy store pays finding-0169's scan again on a cold path. |
| **C. Make the schema probe O(1) first, then B** | small, and independently worthwhile | Removes the reason B is expensive: the probe stops being a full scan, so arming it anywhere becomes cheap. Also removes the two probes `add()` already pays. |

C is the option that makes the question go away rather than trading one cost for another, and it is
useful on its own merits (#2 above) — but it is a change to the migration machinery, which is
outside bp-103's write_scope and outside its non-goals (§9).

## Re-entry condition

An orchestrator/owner decision, batched — **not a blocker for bp-103 or for the daemon restart**,
provided the restart checklist adds one cheap confirmation: that the live store's schema carries
`current`. If it does (expected), option A is already correct in production and C is a follow-up
build. If it does *not*, the restart must migrate before `code_corpus.sync()` runs, and C becomes
prerequisite rather than follow-up.

## Routing

`design` → orchestrator. Nothing here blocks the plan's acceptance criteria: bp-103's items are
complete, its ratchets are green, and the recorded behavior is tested. What is routed is the
question of **where schema migrations should arm and what a schema probe should cost** — a design
question the builder is explicitly forbidden from resolving, parked with the criterion it touches
rather than blocking on it.
