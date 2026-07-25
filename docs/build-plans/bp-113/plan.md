---
type: build-plan
id: bp-113
track: ops
status: proposed
design_ref:
  - docs/design-notes/dn-supervision-and-liveness.md
contract: builder
write_scope:
  - core/ingest/code_corpus.py
  - scheduler/code_sync.py
  - tests/unit/test_code_lane_split.py
  - tests/unit/test_code_corpus.py
  - tests/unit/test_code_sensor.py
  - tests/unit/test_code_ingest_wiring.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 250k
  actual: null
depends_on: [bp-110]
parallelizable_with: [bp-114]
created: 2026-07-25
updated: 2026-07-25
links:
  - docs/findings/finding-0165.md
  - docs/findings/finding-0169.md
  - docs/findings/finding-0188.md
re_entry: null
supersedes: null
superseded_by: null
warrant: docs/findings/finding-0165.md
---

# Build Plan — the code lanes compute out-of-process and land in the supervisor

## 0. Mode & provenance

The **first real lane migration**, graduated from `dn-supervision-and-liveness` §2.3 (the handler
survey) and §3's sequencing — *"longest-lane first (`code_backfill`, `code_sync`, `vault_sync` —
the uncapped three)."* It is a per-lane builder plan under bp-110's integrator: it consumes the
worker protocol and **defines none of it**.

⚑ **`code_sync` and `code_backfill` are ONE plan, not two, and the reason is structural.** Both
handlers route into the same driver and **share the same private method**: `sync()`
(`core/ingest/code_corpus.py:280-301`) and `backfill()` (`:309-338`) both call `_embed_and_land`
(`:267-278`), which is the exact embed→write fusion the split must break. Two plans over one
method cannot run in parallel and the second would inherit the first's half-finished refactor.
This is the kind of boundary the graduate skill exists to decide with the whole note in view.

Investigation and planning produced this; implementation proceeds item-by-item on owner approval.

## 1. Objective

The code corpus lanes compute their embeddings in a worker that holds no store writer, and every
row they produce is landed by the supervisor.

### 1.2 Non-goals (explicit — see §9)

Not the worker protocol (bp-110), not `vault_sync` (bp-114), not a change to what gets embedded or
how it is chunked. [INFERENCE] Not a change to the temporal-corpus semantics — `current=true/false`
keep-and-link (dn-temporal-code-corpus D2, `code_corpus.py:255-259`) is untouched; inferred from
this being an execution-model plan, not an ingest-semantics one.

## 2. Context manifest

Read in order, whole files before citing:

1. `docs/design-notes/dn-supervision-and-liveness.md` §2.3 (**the survey rows for `code_sync` and
   `code_backfill`, and the honest qualification about supersede→add**), §2.5, §2.10
2. `docs/build-plans/bp-110/plan.md` §6 — **the protocol, pinned; do not re-derive it**
3. `core/ingest/code_corpus.py` — **whole file, 356 lines.** `_embed_and_land` `:267-278`,
   `sync` `:280-301`, `seed` `:303-307`, `backfill` `:309-338`, `build_code_corpus_sync` `:341+`
4. `scheduler/code_sync.py` — the two handlers and their idempotence assertions (`:45`, `:53`)
5. `ops/lifecycle/launcher.py:455-480` — how both handlers are wired to **one** driver
6. `docs/findings/finding-0165.md` — the warrant: background starvation under a long job

**Does core already have this?** ⚑ `ambassador_task` is the in-repo reference shape and bp-110
proved the protocol on it (`scheduler/interface.py:53-59` returns data,
`scheduler/supervisor.py:94-95` lands it). Read that first — this plan is the same move applied to
a lane that actually writes
rows. Do not invent a second batching idiom.

## 3. Investigation & grounding  <!-- Part A -->

- **Q1 — where exactly is the interleave?** `_embed_and_land` (`code_corpus.py:267-278`): chunk
  (`:272`), **embed** (`:276`), build rows (`:277`), **`store.add`** (`:278`). One method, one
  file-version. The split is: return `rows`, let the supervisor call `add`. This is the smallest
  possible seam and it serves both lanes.
- **Q2 — ⚑ does the compute half need the store?** **Yes, for READS, and this is the load-bearing
  constraint.** `sync()` reads `self.store.all_rows(provenances={Provenance.CODE})` (`:283`) to
  compute `present_pd`; `backfill()` does the same (`:321`). bp-110 §6 pins the resolution — the
  worker gets a **read-only facade**, never the writable store. This plan **consumes** that
  decision and must not re-litigate it; if the facade is missing or leaks, that is a bp-110 defect
  (§10).
- **Q3 — are there writes in the compute half besides `add`?** ⚑ **Yes — `supersede_source`.**
  `sync()` calls `self.store.supersede_source(p)` twice: for vanished files (`:293`) and before
  re-landing a changed file (`:298`). Both are writes inside the compute loop. **They must move
  into the landing step**, which is exactly what §2.3's honest qualification anticipates: *"a kill
  between them leaves a path with no `current=true` version until the next idempotent pass. Same
  remedy, same structural closure."* The batch must therefore carry the supersede intent **and**
  the rows, so the supervisor performs both in one landing.
- **Q4 — does `code_backfill` write anywhere else?** **Yes, and the note names it as "then diff
  capture".** The handler is wired with a second store: `code_backfill_handler(code_driver,
  code_snapshots_db, code_driver.repo)` (`launcher.py:479`), where `code_snapshots_db` is
  `data/code_snapshots.sqlite` (`:456`). The builder must read `scheduler/code_sync.py` to
  establish whether the diff capture is interleaved with the embedding loop or terminal to it —
  **the code does not settle this from `code_corpus.py` alone.** If it is interleaved, it is a
  second seam in this lane and §10 applies.
- **Q5 — is a batch boundary safe here?** **Yes, by the lanes' own idempotence.** Both kinds are in
  `_IDEMPOTENT_KINDS` (`scheduler/queue.py:71-72`) and both handler modules assert why
  (`code_sync.py:45` "idempotent + blob-sha keyed"; `:53` "idempotent — already-embedded digests
  are skipped"). A batch that is computed but never landed costs re-computation, never
  correctness. **This is why the code lanes go first.**
- **Q6 — how big is a batch?** **Not settled by reading.** `backfill` iterates `todo` — a list of
  `(path, blob_sha)` version pairs, ~1,542 versions on the live system. The natural unit is
  *N file-versions per batch*, but N must satisfy bp-112's batch deadline and bp-110's V2
  serialization cost. Item 1 measures; §11 parks the value.
- **Q7 — does the `seed` path need anything?** `seed()` (`:303-307`) is literally `return
  self.sync()`, so it inherits the split for free. Confirm, do not duplicate.

**Additional risks or questions surfaced during reading:**

- ⚑ **This is the lane that produced finding-0169** (the 96% CPU wedge) and finding-0188 (the wedge
  detector's ceiling). It is the highest-value lane to migrate and the highest-risk one to get
  wrong: it writes the code corpus, which is a large fraction of `data/vectors.lance`.
- `store.add`'s return is a row count that both reports use (`report.embedded_rows`). Under the
  split the count is only known **after** landing, so the report must be assembled by the
  supervisor's lander, not by the compute half. A compute half that predicts the count is
  reporting a belief — the class this whole wave exists to remove.
- Test files: `tests/unit/test_code_corpus.py` is carried (bp-106's journal records it builds a
  pre-bp-099 legacy table at `:280` — **do not disturb that test**, it is the migration under
  test). The builder must grep `CodeCorpusSync` and `code_sync_handler` before editing; the three
  carried files are the known set, not a proven-complete one.

## 4. Reconciliation  <!-- Part B -->

- **`core/ingest/code_corpus.py:318`** — `backfill`'s docstring already claims *"Store writes stay
  on the caller (the supervisor handler), single-writer kept."* → **banner: correction.** That is
  **not true today**: `_embed_and_land` calls `self.store.add` at `:278`, inside the driver. The
  docstring describes the intended architecture, and this plan is what makes it true. Say so
  explicitly — a docstring that was aspirational and is now accurate deserves the correction
  banner, precisely because a reader could have trusted it.
- **`core/ingest/code_corpus.py:267-271`** — `_embed_and_land`'s name and docstring
  (*"Derive → embed → land one file version's rows"*) → **banner: correction.** It stops landing.
  Rename it to say what it does (it derives and embeds) and move `land` to the supervisor side; a
  method named `_embed_and_land` that does not land is the worst of both.
- **`docs/findings/finding-0165.md`** → **cross-ref: extension.** The batch unit is this finding's
  structural home (§1.1 of the note), but starvation only *closes* once the fairness half is
  observable. Record the evidence in the journal; the orchestrator closes it at seal, not the
  builder.

## 5. Write scope

`core/ingest/code_corpus.py` is the driver (compute half) and `scheduler/code_sync.py` the handler
registration + lander. `tests/unit/test_code_lane_split.py` is new. The three remaining test files
are **carried because they pin the surface this plan moves** — `CodeCorpusSync`'s methods and the
handlers' return shapes.

⚑ Deliberately OUT of scope: `scheduler/worker.py` and `scheduler/supervisor.py` — **bp-110 owns
the protocol and this plan must not extend it.** A lane that needs a protocol change is a
`spec-defect` against bp-110 (§10), not a widening here; that discipline is the entire point of
having an integrator plan. Also out: `core/ingest/sync.py` / `index.py` (bp-114 — and bp-113 and
bp-114 are parallel worktrees, so touching them would be a live conflict),
`core/stores/vectorstore.py`, and every foundation-denylist file.

## 6. Interfaces pinned inline

**The protocol — copied from bp-110 §6, verbatim. Do not go read it; do not re-derive it.**

```python
@dataclass(frozen=True)
class Batch:
    rows: tuple[dict[str, Any], ...]
    token: str | None
    items_done: int

ComputeHandler = Callable[[Job, "WorkerContext"], "Iterator[Batch]"]
Lander = Callable[[Job, Batch], None]
```

**The method being split — its exact current form** (`core/ingest/code_corpus.py:267-278`):

```python
    def _embed_and_land(self, path: str, blob_sha: str, source: str, *,
                        current: bool = True) -> int:
        chunks = derive_code_chunks(path, source,
                                    max_chars=self.max_chars, overlap_chars=self.overlap_chars)
        if not chunks:
            return 0
        vectors = self.embedder.embed_documents([c.text for c in chunks])
        rows = code_rows(path, blob_sha, chunks, vectors, current=current)
        return self.store.add(rows)
```

**⚑ The batch must carry the supersede intent, not just rows** (§3 Q3). `sync()` supersedes before
adding, and both halves must land together or a path is left with no `current=true` version:

```python
# The landing step performs BOTH, in this order, for every element of the batch:
#   1. store.supersede_source(path)   # prior version -> current=false   (code_corpus.py:298)
#   2. store.add(rows)                # land the new version            (code_corpus.py:278)
# Interrupting between them is the window §2.3 names. Under the split the supervisor owns both
# and signals act at landing BOUNDARIES, so the window closes structurally.
```

**The idempotence guarantee this lane rests on** (`scheduler/queue.py:58-59`):

```
  code_sync     scheduler/code_sync.py:45   "idempotent + blob-sha keyed"
  code_backfill scheduler/code_sync.py:53   "idempotent — already-embedded digests are skipped"
```

**The report shape the lander must assemble** (`CodeSyncReport` fields used today):
`changed_files`, `unchanged_files`, `deleted_files`, `superseded_rows`, `embedded_rows`,
`parse_failures`. ⚑ `embedded_rows` and `superseded_rows` are **landing** counts and may only be
filled from the supervisor's side (§3, additional risks).

## 7. Items

Blast radius: measurement → the pure compute half → the lander → the second lane → wiring.

### Item 1 — measure the batch unit

- **Objective:** N (file-versions per batch) is chosen from numbers, against bp-112's deadline.
- **Files:** none (scratchpad; results in `journal.md`)
- **Acceptance test:** journal records, for the real repo: per-file-version embed time
  (distribution, not mean), serialized batch size at several N, and the largest N whose p95 batch
  time fits comfortably inside the proposed `batch_deadline_s`.
- **Falsifier:** ⚑ *no N satisfies both the deadline and a sane serialization cost* — e.g. a single
  large file's version exceeds the batch deadline on its own. Then the batch unit is the wrong
  grain for this lane and that is a design question, not a tuning one.
- **Invariant(s):** read-only; nothing landed.
- **Touches stored data?** No. **Parallelizable?** No. **Depends on:** none.

### Item 2 — the compute half returns rows

- **Objective:** `CodeCorpusSync` can produce batches without holding a store writer.
- **Files:** `core/ingest/code_corpus.py`, `tests/unit/test_code_lane_split.py`
- **Acceptance test:** the compute path yields `Batch`es carrying rows **and** supersede intents,
  given only a read-only rows facade and an embedder; a unit test constructs it with **no writable
  store at all** and it still computes correctly.
- **Falsifier:** ⚑ *the compute half can still be constructed with a writable store and silently
  use it.* The test that matters is the one that withholds the writer — if the code works either
  way, nothing was restricted and §2.3's tier-2 claim is decoration.
- **Invariant(s) it must not violate:** chunking, embedding and `code_rows` are byte-for-byte
  unchanged — this plan moves *where* work happens, never *what is computed*. The
  `current=true/false` keep-and-link semantics (D2) hold.
- **Touches stored data?** No. **Parallelizable?** No. **Depends on:** Item 1.

### Item 3 — the lander, and `code_sync` migrated

- **Objective:** `code_sync` runs under `worker_mode = "subprocess"` with identical results.
- **Files:** `scheduler/code_sync.py`, `tests/unit/test_code_lane_split.py`, carried tests
- **Acceptance test:** ⚑ **the parallel-run proof** (§4 of the note): the same repo state synced
  under `inproc` and `subprocess` produces **identical rows** in a scratch store and identical
  report figures. Supersede and add happen in one landing per file-version.
- **Falsifier:** ⚑ *the two modes produce different rows or different counts.* Diff the stores, not
  the reports — a report is a summary and can agree while the rows differ.
- **Invariant(s) it must not violate:** single-writer (the supervisor is the only writer); the
  supersede→add pair is never split across a landing boundary; `seed()` (`:303-307`) still works
  via `sync()` with no duplicated logic.
- **Touches stored data?** ⚑ **Yes.** Require the parallel run against a **scratch** store, with
  a row-level diff, before any run against `data/`.
- **Parallelizable?** No. **Depends on:** Item 2.

### Item 4 — `code_backfill` migrated

- **Objective:** the longest lane in the system computes out-of-process.
- **Files:** `scheduler/code_sync.py`, `core/ingest/code_corpus.py`, carried tests
- **Acceptance test:** a backfill over a bounded slice of ledger versions yields the same rows in
  both modes; a batch boundary mid-backfill resumes correctly from its token; the diff-capture side
  (§3 Q4) is unchanged in behaviour.
- **Falsifier:** ⚑ *a resumed backfill re-embeds work it already landed*, or *skips versions*.
  Idempotence makes re-embedding merely wasteful, but **skipping is silent data loss** in the one
  store that cannot be rebuilt from git — assert version-set equality, not just row counts.
- **Invariant(s) it must not violate:** already-embedded `(path, digest)` pairs are still skipped
  at zero embeds (`:323`); `current` is still `head.get(path) == blob_sha` (`:334`); parse failures
  still embed and are still counted (`:331-332`).
- **Touches stored data?** ⚑ **Yes**, and this is the largest write path in the system. Scratch
  store, row diff, then a bounded live slice — never a full live backfill as the first real run.
- **Parallelizable?** No. **Depends on:** Item 3.

### Item 5 — fairness, observed

- **Objective:** finding-0165's starvation claim gets a measurement.
- **Files:** `tests/unit/test_code_lane_split.py`
- **Acceptance test:** with a long backfill in flight under `subprocess` mode, a queued job in
  another lane is claimed and completed **between batches** — asserted, not eyeballed. Record the
  achieved interleave in the journal.
- **Falsifier:** ⚑ *no other-lane job runs until the backfill finishes.* Then the batch is not
  actually the fairness unit and finding-0165 is unclosed — which the note's §2.10 anticipates for
  a different reason (the single-model-in-flight rule serializing model lanes). Record which cause
  applies; do not report the finding closed.
- **Invariant(s) it must not violate:** the single-model-in-flight rule (bp-110 Item 4) still
  holds — fairness may not be bought by breaching the ceiling.
- **Touches stored data?** No. **Parallelizable?** No. **Depends on:** Item 4.

## 8. Math carried explicitly

N/A — no mathematical object. The embeddings are computed by the unchanged embedder; this plan
moves the process boundary, not the function. ⚑ **If any vector value changes, that is a defect,
not a design choice** — and it would be a `dn-local-model-runtime` §2.5 equivalence-gate concern
(vectors from two provenances in one store, undetectable by any existing instrument).

## 9. Non-goals

- **No protocol change.** bp-110 owns it; a lane needing more is a `spec-defect` (§10).
- **No `vault_sync`** — bp-114, running in parallel.
- **No change to chunking, embedding, `code_rows`, or D2 keep-and-link semantics.**
- **No change to `_IDEMPOTENT_KINDS`** — both lanes are already members and the membership comment
  warns never to widen it by assumption (`scheduler/queue.py:53-66`).
- **No full live backfill** as an acceptance run (§7 Item 4).
- **No touching `tests/unit/test_code_corpus.py:280`'s legacy-table construction** — bp-106 records
  it as a legitimate pre-bp-099 fixture; it is the migration under test.

## 10. Stop-and-raise conditions

- ⚑ **bp-110's read-only facade is missing or leaks the writable handle** ⇒ **STOP** and file a
  `spec-defect` against bp-110. Do not build a lane-local workaround; that is the finding-0191
  failure being repeated inside the plan structure designed to prevent it.
- ⚑ **The lane needs a protocol change** (e.g. the batch must carry something `Batch` cannot
  express) ⇒ **STOP and file.** Extending the protocol from a lane plan is exactly how a seam
  becomes ungoverned.
- ⚑ **Item 4's falsifier fires — a resumed backfill skips versions** ⇒ **STOP immediately.** Silent
  omission in `data/vectors.lance` is undetectable afterwards and unrecoverable from git.
- **The diff capture turns out to be interleaved with embedding** (§3 Q4) ⇒ raise: it is a second
  seam in this lane and may deserve its own item or its own plan.
- **Item 1's falsifier fires** (no workable N) ⇒ park the criterion with the measurements, file,
  and continue with `code_sync` (whose per-item work is smaller) while `code_backfill` waits.
- Any blessing transition — never.

## 11. Parked decisions

| Decision | Default recorded | Re-entry condition |
|---|---|---|
| batch size N | measured in Item 1 | a lane exceeds the batch deadline |
| report assembly | supervisor-side, from landings | a caller needs a pre-landing estimate |
| diff capture's home | stays where it is | §3 Q4 finds it interleaved |
| `seed`'s path | inherits `sync()` unchanged | never — duplicating it is the defect |

**Rejected alternatives, per row:**

- **Batch size.** Rejected: *one file-version per batch* — maximal fairness and simplest resume,
  but pays the IPC round-trip per file across ~1,542 versions. Rejected: *the whole todo list* —
  that is today's behaviour with extra steps and no deadline can bound it.
- **Report assembly.** Rejected: *the compute half predicts counts* — a predicted landing count is
  a belief reported as a measurement, the exact class this wave removes.
- **Diff capture.** Rejected: *move it into the worker now* — premature until §3 Q4 is answered by
  reading `scheduler/code_sync.py`.

## 12. Dependency & ordering summary

Items strictly linear: **1 → 2 → 3 → 4 → 5.** `code_sync` (Item 3) before `code_backfill`
(Item 4) despite the note's "longest lane first" sequencing — the note orders *lanes across plans*,
and within this plan `sync()` is the smaller surface that proves the lander, after which `backfill`
is a second consumer of a proven path. Getting the biggest write path in the system wrong is the
costliest mistake available here.

**`depends_on: [bp-110]`** — the protocol. Transitively after bp-108/bp-109.
**`parallelizable_with: [bp-114]`** — genuinely disjoint: this plan owns
`core/ingest/code_corpus.py` + `scheduler/code_sync.py`; bp-114 owns `core/ingest/sync.py` +
`core/ingest/index.py` +
`scheduler/vault_sync.py`. Their test files are disjoint too. This is the *only* real parallel pair
in the supervision wave, and it exists because the integrator plan took the seam files out of both.
