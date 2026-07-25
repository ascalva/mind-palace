---
type: finding
id: finding-0169
status: open
created: 2026-07-25
updated: 2026-07-25
links:
  - core/stores/vectorstore.py                         # supersede_source / rows_for_source — the defect
  - docs/findings/finding-0167.md                      # predicted the shape ("O(depth) re-land bound owed")
  - docs/findings/finding-0168.md                      # the membership store — the structural cure
  - docs/design-notes/temporal-code-corpus.md          # D2 keep-and-link: the design this cannot carry
  - docs/findings/finding-0165.md                      # background starvation — the amplifier
ftype: spec-defect
origin_plan: orchestrator
route: builder
resolution: null
---

# `supersede_source` is O(total store), not O(depth) — the history backfill cannot complete

## What

Measured live on run #35 (2026-07-25, first post-deploy backfill), not inferred.

`VectorStore.supersede_source()` (`core/stores/vectorstore.py:192`) implements keep-and-link as
**read → delete-whole-path → re-add**. The read is `rows_for_source()`, which does:

```python
return [r for r in self._table().to_arrow().to_pylist()   # ENTIRE TABLE, vectors included
        if r.get("source_path") == source_path]           # then filters in Python
```

`supersede_source` triggers that full materialization **twice** per call — once directly, once
inside `delete_source()`, which calls `rows_for_source()` again.

Measured cost at the time of failure:

| quantity | value |
|---|---|
| full `to_pylist()` (with vectors) | **11.7 s** / 22,621 rows × 2560 dims |
| materializations per superseded version | **2** |
| effective cost per version | **~23 s**, growing with total store size |
| `code_backfill` job 300240 | ran 02:30:12 → 03:45:02 UTC, **FAILED `TimeoutError`** at 74m50s |
| progress at death | **847 of ~1,542** distinct `(path, blob_sha)` versions |
| daemon CPU during the run | ~99% sustained, single core |
| `llama-server` CPU during the run | **0.3%** — almost none of the time was embedding |

The 99%-CPU-with-idle-embedder signature is the tell: the work is Arrow→Python marshalling of
vector columns, not inference. A `sample(1)` of the worker confirmed it — the hot stack is
`pyarrow ... Array_to_pylist → arrow::FixedSizeListArray::value_slice`, i.e. the embedding column.

## Why it matters

**The backfill cannot ever complete, and each retry is worse than the last.** The cost per version
scales with total rows in the store, and the store grows as the backfill lands versions. The
catch-up probe (`_code_backfill_incomplete`, `ops/lifecycle/launcher.py:395`) re-arms the job on
every daemon start, so the current behavior is a **livelock**: 75 minutes of pegged CPU per restart,
reaching a monotonically earlier point each time. This is not a slow job awaiting patience.

Second-order: `code_sync` uses the same path on every changed file, so ordinary operation degrades
as history accumulates — this is not confined to the backfill. Job 300246 (`code_sync`) was still
grinding in the same scan 10 minutes in when the daemon was brought down.

The keep-and-link **semantics are correct and proven** (8,619 `current=false` rows retained, not
deleted — dn-temporal-code-corpus D2 demonstrated on the real store). The defect is one method's
implementation, not the design.

## Why the design record under-specified it

dn-temporal-code-corpus D2 specified the *semantics* of keep-and-link and inherited the store's
existing "portable re-index idiom" (`relabel_provenance`'s delete-then-re-add) without bounding its
cost. That idiom is sound at note scale — tens of rows, one pass, one-off migration — and
pathological at history scale, where it runs per version against a table that grows monotonically.
finding-0167 flagged the shape ("`supersede_source` O(depth) re-land bound owed"); the measured
reality is worse, because the scan is not scoped to the path's depth at all — it is the whole table.

## The fix (builder-resolvable, one file)

1. Push the `source_path` filter into the query rather than filtering in Python.
2. One scan per `supersede_source`, not two — do not have `delete_source` re-scan.
3. Do **not** materialize the `vector` column when the operation only flips a boolean flag.
4. Prefer an in-place column update over delete-then-re-add if the LanceDB version supports it;
   the docstring's portability concern should be re-checked against the pinned version rather
   than assumed.
5. Add a ratchet that fails if a `supersede_source` call cost grows with unrelated store size —
   the structural enforcement, per the standing rule that a property is only real when a test
   proves it.

~~Also owed, separately: the job timeout knob that killed the backfill (~4,490 s) was not locatable
in `config/defaults.toml` or `scheduler/` during triage. It should be named, configurable, and
surfaced in status as elapsed-vs-budget.~~

**[banner: correction — 2026-07-25, by the bp-102 builder, measured]** **The knob was not locatable
because IT DOES NOT EXIST. There is no job-level timeout anywhere in the system.**
`Supervisor.tick` calls `handler(job)` **synchronously and unbounded**. What actually killed job
300240 was a **`socket.timeout` from one embed call** exceeding `[ollama] request_timeout_s = 120` —
raised from `urllib`'s socket read at the 74m50s mark. `TimeoutError('timed out')` is **not** a
`urllib.error.URLError` subclass, so it escaped `OllamaClient._post`'s `except URLError` un-wrapped
and propagated up as a raw job failure.

Two consequences, both larger than the original note:
1. **The "~75-minute job budget" never existed** — it was an artifact of when an embed call happened
   to hang. Every statement in this session's record that a wedged job "will exit at its own
   timeout" was **wrong**; a wedged job runs until something external stops it. That makes the
   owner-authorized `kill -9` of run #35 the *only* available exit, not a shortcut past a wait.
2. **finding-0171's option (b) changes from "tune" to "BUILD".** Worker-enforced job budgets are not
   a parameter to set; they are machinery that does not exist. oq-0035 should be re-read with that
   in mind.
Also surfaced: the un-wrapped `socket.timeout` is its own defect — `OllamaError` wrapping has a gap.

## Re-entry condition

The daemon stays **down** until the fix lands. `palace up` before then re-arms the probe and burns
another 75-minute cycle into the same wall. Re-entry: `supersede_source` cost is independent of
total store size (proven by the ratchet), then bring the daemon up and let the probe re-enqueue —
the job is idempotent and resumes from the 847 versions already landed.

## Routing

`codebase` → builder. The fix is mechanical and scoped to `core/stores/vectorstore.py`.

**Strengthens finding-0168.** The membership store makes vectors append-only and moves supersession
onto slot-lineages — under that model there is no re-land at all, so this class of defect cannot
recur. This finding is evidence for the f-0168 design pass, not an alternative to it: fix the method
now (cheap, unblocks the backfill), and let the membership rebuild retire the idiom entirely.
