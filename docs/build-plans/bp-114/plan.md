---
type: build-plan
id: bp-114
track: ops
status: proposed
design_ref:
  - docs/design-notes/dn-supervision-and-liveness.md
contract: builder
write_scope:
  - core/ingest/sync.py
  - core/ingest/index.py
  - scheduler/vault_sync.py
  - tests/unit/test_vault_lane_split.py
  - tests/integration/test_vault_sync.py
  - tests/integration/test_vault_sync_wiring.py
  - tests/integration/test_index_keying.py
  - tests/integration/test_version_history.py
  - tests/integration/test_rename_identity.py
  - tests/integration/test_mint_ids.py
  - tests/integration/test_body_only_embedding.py
  - tests/integration/test_purge_raw.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 300k
  actual: null
depends_on: [bp-110]
parallelizable_with: [bp-113]
created: 2026-07-25
updated: 2026-07-25
links:
  - docs/design-notes/ingest-identity-and-amendment.md
  - docs/findings/finding-0165.md
re_entry: null
supersedes: null
superseded_by: null
warrant: docs/findings/finding-0165.md
---

# Build Plan — the vault lane computes out-of-process; its five-store landing becomes one step

## 0. Mode & provenance

The second lane migration, graduated from `dn-supervision-and-liveness` §2.3 — the survey row
*"`vault_sync` | raw.add → parse+embed → 5-store landing | splittable; landing = 5 short writes"* —
and its **honest qualification**, which this plan is bound to honour rather than quietly improve:

> *"`vault_sync`'s landing is a five-store ordered sequence per note, including an internal
> delete→add window (`core/ingest/index.py:87-88`, "atomically-ish"). The split does not make that
> window atomic — it moves it into a supervisor-owned landing step that is never interrupted at
> SIGTERM (signals act at landing boundaries). Recoverable today (re-derivable from raw),
> structural after the split."*

⚑ **This is the most consequential lane and the widest retrofit surface in the wave** — eight
existing integration test files pin `VaultSync`/`index_amendment` behaviour, because vault ingest
carries note *identity* (doc_id binding, rename continuity, version chains), not just vectors.

Investigation and planning produced this; implementation proceeds item-by-item on owner approval.

## 1. Objective

`vault_sync` computes parsing and embedding in a worker that holds no store writer, and its
five-store per-note landing happens as one uninterrupted supervisor-owned step.

### 1.2 Non-goals (explicit — see §9)

Not the worker protocol (bp-110), not the code lanes (bp-113). **Not making the delete→add window
transactionally atomic** — the note explicitly says the split does not do that, and a builder who
"fixes" it here is changing store semantics under an execution-model plan. [INFERENCE] Not a change
to chunk-level amendment, doc_id resolution, or version-chain semantics
(`ingest-identity-and-amendment.md` §4) — inferred from this being an execution-model plan.

## 2. Context manifest

Read in order, whole files before citing:

1. `docs/design-notes/dn-supervision-and-liveness.md` §2.3 (**the `vault_sync` row, the routes
   list, and the honest qualification quoted above**), §2.5, §2.10
2. `docs/build-plans/bp-110/plan.md` §6 — **the protocol, pinned; do not re-derive it**
3. `docs/build-plans/bp-113/plan.md` — the sibling lane; read its §6 landing-order pin so the two
   lanes land in the same idiom rather than inventing two
4. `core/ingest/sync.py` — **whole file, 200 lines.** `sync_path` `:83-136`, `handle_deleted`
   `:138-144`, `rescan` `:146-180`
5. `core/ingest/index.py` — **whole file, 145 lines.** `index_amendment` `:68-89`
6. `scheduler/vault_sync.py:30-42` — the handler; `rescan()` is the whole body
7. `docs/design-notes/ingest-identity-and-amendment.md` §4 — the semantics that must not move

**Does core already have this?** bp-113 will have migrated the code lanes first (or be doing so in
parallel) using the same protocol. ⚑ **Read its landing idiom and match it.** Two lanes inventing
two batching idioms for one protocol is the DRY defect this wave is most likely to produce.

## 3. Investigation & grounding  <!-- Part A -->

- **Q1 — what is the compute half?** Per note: `parse_note` (`sync.py:90`), `ingest_note`
  (`:92`), and the embed inside `index_amendment` (`core/ingest/index.py:82-84`). The long span is
  the embed; everything else is parsing.
- **Q2 — what is the landing half, exactly?** Five ordered writes per note, in this order:
  `store.delete_source` + `store.add` (fused inside `index_amendment`, `index.py:87-88`),
  `catalog.record` (`sync.py:119`), `attestor.emit` (`:123`), `version_store.record` (`:135`).
  The note's route list matches the code.
- **Q3 — ⚑ `raw.add` is a WRITE inside the compute half. Where does it go?** **The code does not
  settle this.** `ingest_note(parsed, self.raw, …)` (`sync.py:92-93`) writes the content-addressed
  archive *and* returns the `record` (chunks) the rest of the function needs. The note calls it
  *"idempotent archive, pre-compute"* but does not say which side owns it. **§11 records the
  default: the supervisor performs `raw.add` before dispatch**, because (a) it is short and
  idempotent, (b) it is content-addressed so a repeat is a no-op, (c) raw is the sacred substrate
  and handing a worker a `RawStore` writer would breach the capability restriction for the one
  store that must never be lost. The worker then receives the parsed record. **If that shape does
  not work, it is a §10 raise** — do not hand the worker a raw writer as a convenience.
- **Q4 — what reads does the compute half need?** Two: `self.catalog.get(source_path)` (`:96`) for
  the unchanged-content early return, and `self.store.rows_for_source(source_path)` (`:117`) for
  vector reuse. Both are reads ⇒ bp-110's read-only facade covers them. **Vector reuse is not
  optional**: `index_amendment` reuses the vectors of unchanged chunks (`index.py:77,85`), which is
  what keeps a frequently-edited note from re-embedding wholesale. A split that loses the reuse
  read would silently multiply embedding cost.
- **Q5 — is `index_amendment` splittable?** **Yes, cleanly.** `:77-86` is pure computation
  (hash, dedup, embed only new chunks); `:87-88` is the write pair. The natural signature change
  is: return `rows` plus the `(embedded, reused)` counts, and let the caller write. That leaves
  `index.py`'s hard part — canonical-chunk dedup and vector reuse — exactly where it is.
- **Q6 — what is the batch unit here?** **One note.** Unlike the code lanes there is no natural
  sub-note unit: the five-store landing is per-note and the delete→add pair must not straddle a
  boundary. `rescan()` (`sync.py:146-180`) iterates notes, so N notes per batch is the knob.
- **Q7 — is a batch boundary safe?** Yes, by the lane's own idempotence: `vault_sync` is in
  `_IDEMPOTENT_KINDS` (`scheduler/queue.py:71-72`) and `scheduler/vault_sync.py:39` asserts
  *"duplicate jobs are harmless because `rescan()` is idempotent."* An unlanded batch costs
  re-computation, not correctness.
- **Q8 — what does `handle_deleted` do?** `catalog.tombstone` + `store.delete_source`
  (`sync.py:142-143`) — pure landing, no compute. It stays supervisor-side entirely.

**Additional risks or questions surfaced during reading:**

- ⚑ **Eight integration test files pin this surface** and all are pre-widened into `write_scope`:
  `test_vault_sync`, `test_vault_sync_wiring`, `test_index_keying`, `test_version_history`,
  `test_rename_identity`, `test_mint_ids`, `test_body_only_embedding`, `test_purge_raw`. They
  assert *identity* properties — a rename continuing a version chain, a doc_id bound at first
  bind only, unchanged chunks keeping their point ids. **A weakened assertion in any of them is
  invisible and permanent.** Diff every edit and justify each in the journal.
- The `rename_by_digest` map (`sync.py:84,108-111`) is built by `rescan` and passed into
  `sync_path`. It is cross-note state within a pass, so it must be computed before batching or
  carried in the worker context — batching per note must not break rename detection.
- `attestor.emit` (`:120-124`) writes the attestation chain leaf. It is a landing write and must
  stay with the others; an attestation emitted for a note whose rows were never landed is a lying
  provenance record.

## 4. Reconciliation  <!-- Part B -->

- **`core/ingest/index.py:70-76`** — `index_amendment`'s docstring, *"…and replace the note's
  projection under its stable `source_path`. Returns `(embedded, reused)`."* → **banner:
  correction.** It stops replacing anything; it computes rows and counts. Rename it or say plainly
  that landing moved to the caller, and **keep the note about vector reuse verbatim** — that is the
  §4 gap this function closes and it is easy to lose in a refactor.
- **`core/ingest/index.py:87`** — the comment *"replace the projection atomically-ish"* →
  **banner: correction.** After the split the pair is still not atomic, but it is now inside a
  supervisor-owned landing step that signals never interrupt. Say exactly that, and **do not
  upgrade the claim to "atomic"** — the note is explicit that the split does not make it atomic
  (§1.2 here, §2.3 there). Overclaiming here would be the note's named foot-gun in one word.
- **`core/ingest/sync.py:83-89`** — `sync_path`'s docstring → **cross-ref: extension.** It gains a
  compute/land distinction; the amendment semantics it describes are unchanged.
- **`docs/design-notes/ingest-identity-and-amendment.md`** → **cross-ref only, NOT edited.** It is
  a ratified design note and therefore agent-immutable (CLAUDE.md, A8). Its semantics are preserved
  by this plan, not amended; record that in the journal.

## 5. Write scope

`core/ingest/sync.py` and `core/ingest/index.py` are the compute/land split;
`scheduler/vault_sync.py` is the handler + lander. `tests/unit/test_vault_lane_split.py` is new.
The eight integration files are **carried because they pin the surface this plan moves** — they
assert identity semantics over `VaultSync`/`index_amendment`, and changing either function's
signature reds them.

⚑ Deliberately OUT of scope: `scheduler/worker.py` and `scheduler/supervisor.py` — **bp-110 owns
the protocol**; a lane needing a protocol change files a `spec-defect` (§10). Also out:
`core/ingest/code_corpus.py` and `scheduler/code_sync.py` (**bp-113 is running in parallel** —
touching them is a live merge conflict), `core/kernel/stores/rawstore.py`, `core/ingest/purge.py`,
`docs/design-notes/**`, and every foundation-denylist file.

## 6. Interfaces pinned inline

**The protocol — copied from bp-110 §6, verbatim.**

```python
@dataclass(frozen=True)
class Batch:
    rows: tuple[dict[str, Any], ...]
    token: str | None
    items_done: int

ComputeHandler = Callable[[Job, "WorkerContext"], "Iterator[Batch]"]
Lander = Callable[[Job, Batch], None]
```

**⚑ The five-store landing order — this exact sequence, per note, in one uninterrupted step:**

```
1. store.delete_source(source_path)        core/ingest/index.py:87
2. store.add(rows)                         core/ingest/index.py:88
3. catalog.record(source_path, digest, title, doc_id=…)   core/ingest/sync.py:119
4. attestor.emit(agent_role="vault_watcher", action="ingest_note",
                 input_hashes=[digest], output_hashes=[digest])   core/ingest/sync.py:120-124
5. version_store.record(catalog.doc_id_for(source_path), digest)  core/ingest/sync.py:134-135
```

⚑ **Step 5 must stay AFTER step 3.** `sync.py:131-133` says why, and it is easy to lose when
reordering: *"Resolved AFTER `catalog.record` above, so the row (and its doc_id) exists."*

**The function being split — its exact current form** (`core/ingest/index.py:68-89`):

```python
def index_amendment(record: IngestRecord, existing_rows: list[dict[str, Any]], embedder: Embedder,
                    store: VectorStore) -> tuple[int, int]:
    vec_by_hash = {text_hash(r["text"]): r["vector"] for r in existing_rows}
    canonical: dict[str, Chunk] = {}
    for c in record.chunks:
        canonical.setdefault(c.content_hash, c)          # one point per canonical chunk (§3)
    to_embed = [c for h, c in canonical.items() if h not in vec_by_hash]
    fresh = dict(zip((c.content_hash for c in to_embed),
                     embedder.embed_documents([c.text for c in to_embed]), strict=True)) \
        if to_embed else {}
    rows = [_chunk_row(record, c, vec_by_hash[h] if h in vec_by_hash else fresh[h])
            for h, c in canonical.items()]
    store.delete_source(record.source_path)              # replace the projection atomically-ish
    store.add(rows)
    return len(to_embed), len(canonical) - len(to_embed)
```

The split is at the blank line that should exist between `rows = [...]` and `store.delete_source`:
everything above is compute, the last three lines are landing. **`vec_by_hash` reuse (`:77`, `:85`)
must survive the split** — see §3 Q4.

**The identity semantics that must not move** (`core/ingest/sync.py:100-104`): doc_id is resolved
**at first bind only** (`prev is None`), preferring an existing `id::` property, else a renamed
predecessor's carried doc_id. An already-bound note keeps its identity.

## 7. Items

Blast radius: read-only measurement → compute/land split of the pure function → the lander →
wiring → fairness.

### Item 1 — measure the batch unit and the reuse rate

- **Objective:** N (notes per batch) is chosen from numbers, and the vector-reuse rate is recorded
  so a regression in it is detectable.
- **Files:** none (scratchpad; results in `journal.md`)
- **Acceptance test:** journal records, over the real vault: per-note parse+embed time
  distribution, serialized batch size at several N, the largest N whose p95 fits inside
  `batch_deadline_s`, **and the current embedded-vs-reused chunk ratio from a full `rescan()`**.
- **Falsifier:** *no N fits the deadline* — e.g. a single large note exceeds it alone.
- **Invariant(s):** read-only; a `rescan()` on an unchanged vault is a no-op by construction
  (`sync.py:147-149`), so this measurement lands nothing.
- **Touches stored data?** No (an unchanged rescan writes nothing). **Parallelizable?** No.
  **Depends on:** none.

### Item 2 — `index_amendment` computes; it does not land

- **Objective:** the embed/dedup/reuse logic is separable from the two store writes.
- **Files:** `core/ingest/index.py`, `tests/unit/test_vault_lane_split.py`
- **Acceptance test:** the compute form returns rows + `(embedded, reused)` given
  `existing_rows` and an embedder, with **no store argument at all**; a landing function performs
  `delete_source` then `add`. Every existing caller produces byte-identical rows to today.
- **Falsifier:** ⚑ *the reuse rate changes.* Compare against Item 1's recorded ratio. If a
  refactor loses `vec_by_hash`, every edited note re-embeds wholesale — the cost regression is
  large, silent, and would look like "the embedder got slower".
- **Invariant(s) it must not violate:** canonical-chunk dedup (`:78-80`), one point per canonical
  chunk, and stable point ids for unchanged chunks — the §4 property the whole function exists for.
- **Touches stored data?** No. **Parallelizable?** No. **Depends on:** Item 1.

### Item 3 — `sync_path` splits, and the landing is one step

- **Objective:** parse+embed happen in the worker; all five writes happen in the supervisor, in
  order, uninterrupted.
- **Files:** `core/ingest/sync.py`, `tests/unit/test_vault_lane_split.py`, carried tests
- **Acceptance test:** ⚑ **the parallel-run proof**: the same vault synced under `inproc` and
  `subprocess` produces **identical rows, identical catalog entries, identical attestation records
  and identical version chains** in a scratch data dir. All eight carried integration files pass.
- **Falsifier:** ⚑ *an attestation or version row exists for a note whose vectors were not landed.*
  A landing that is partially applied produces a lying provenance chain — worse than no chain,
  because it will be trusted. Assert the five writes are all-or-nothing per note.
- **Invariant(s) it must not violate:** the landing order of §6, **including step 5 after step 3**;
  doc_id resolution at first bind only; rename continuity via `rename_by_digest`; `handle_deleted`
  stays landing-only.
- **Touches stored data?** ⚑ **Yes — five stores.** Scratch data dir + full comparison before any
  run against `data/`.
- **Parallelizable?** No. **Depends on:** Item 2.

### Item 4 — `raw.add` lands on the supervisor side

- **Objective:** the sacred substrate is never written by a worker.
- **Files:** `core/ingest/sync.py`, `scheduler/vault_sync.py`, carried tests
- **Acceptance test:** the worker is constructed with **no `RawStore` writer** and the lane still
  works; `raw.add` happens before dispatch and is idempotent under repeat (content-addressed, so a
  re-dispatch after a killed batch re-archives nothing).
- **Falsifier:** ⚑ *the worker holds a raw writer.* Raw is the substrate everything else is
  re-derivable from; it is the one store whose loss is unrecoverable, and it is exactly the store
  the capability restriction should protect most.
- **Invariant(s) it must not violate:** `parse_note` → `ingest_note` ordering and the record's
  chunk content are unchanged; a note whose content is unchanged still short-circuits at `:97-98`
  without re-archiving.
- **Touches stored data?** Yes (raw archive). **Parallelizable?** No. **Depends on:** Item 3.

### Item 5 — fairness, observed

- **Objective:** a long vault rescan does not starve other lanes.
- **Files:** `tests/unit/test_vault_lane_split.py`
- **Acceptance test:** with a multi-batch rescan in flight under `subprocess` mode, a queued job in
  another lane is claimed and completed between batches — asserted, and the achieved interleave
  recorded in the journal.
- **Falsifier:** *no other-lane job runs until the rescan finishes.* Record whether the cause is
  the batch unit or the single-model-in-flight rule (bp-110 Item 4) and do **not** report
  finding-0165 closed without saying which.
- **Invariant(s) it must not violate:** the single-model-in-flight rule still holds.
- **Touches stored data?** No. **Parallelizable?** No. **Depends on:** Item 4.

## 8. Math carried explicitly

N/A — no mathematical object. Chunk hashing and vector reuse are content-addressing, not
statistics. ⚑ **If any vector value changes, that is a defect** — and it is the
`dn-local-model-runtime` §2.5 hazard (two provenances in one store, detected by nothing).

## 9. Non-goals

- **No protocol change** — bp-110 owns it (§10).
- **No transactional atomicity for delete→add.** The note says the split does not deliver it
  (§1.2). Claiming otherwise is the overclaiming foot-gun.
- **No change to identity semantics** — doc_id binding, rename continuity, version chains,
  chunk-level amendment.
- **No change to the raw store, the purge path, or tombstoning.**
- **No touching the code lanes** — bp-113 owns them and runs in parallel.
- **No edit to `ingest-identity-and-amendment.md`** — ratified ⇒ agent-immutable.

## 10. Stop-and-raise conditions

- ⚑ **§3 Q3's default does not work** — the supervisor cannot perform `raw.add` before dispatch
  without duplicating parse work ⇒ **STOP and raise.** Do **not** hand the worker a raw writer as
  a convenience; that is the one store whose capability restriction matters most.
- ⚑ **The five writes cannot be made all-or-nothing per note** ⇒ **STOP.** A partially applied
  landing produces a lying attestation chain, and attestations are the provenance substrate.
- ⚑ **bp-110's read-only facade is missing or leaks** ⇒ STOP and file a `spec-defect` against
  bp-110 (do not build a lane-local workaround).
- **The lane needs a protocol change** ⇒ STOP and file against bp-110.
- **Item 2's falsifier fires — the reuse rate drops** ⇒ STOP. A silent cost multiplier on every
  note edit is a regression that would be diagnosed months later as an embedder problem.
- **Any of the eight carried tests cannot be made green without weakening an assertion** ⇒ STOP
  and file. These assert *identity*, and a weakened identity property is unrecoverable.
- Any blessing transition — never.

## 11. Parked decisions

| Decision | Default recorded | Re-entry condition |
|---|---|---|
| where `raw.add` runs | supervisor, before dispatch | §10 if it forces duplicate parsing |
| batch size N (notes) | measured in Item 1 | a note exceeds the batch deadline alone |
| `rename_by_digest` | computed once per pass, in worker context | renames break across batches |
| delete→add atomicity | unchanged; not made atomic | a store-level transaction becomes available |

**Rejected alternatives, per row:**

- **`raw.add`.** Rejected: *the worker archives* — it hands a writer for the sacred substrate to
  the least-trusted process in the design. Rejected: *skip archiving until landing* — the record's
  chunks come out of `ingest_note`, so the compute half would have to re-derive them, and a raw
  write after a successful embed inverts the "raw first" ordering the pipeline relies on.
- **Batch size.** Rejected: *one note per batch* — maximal fairness, but the IPC round-trip per
  note across a large vault. Rejected: *the whole rescan* — today's behaviour, unbounded.
- **`rename_by_digest`.** Rejected: *recompute per batch* — a rename whose old and new paths land
  in different batches would fork the version chain, which is exactly what bp-031 built this map to
  prevent.
- **Atomicity.** Rejected: *wrap the pair in a store transaction* — out of scope, changes store
  semantics under an execution-model plan, and the note explicitly declines it.

## 12. Dependency & ordering summary

Items strictly linear: **1 → 2 → 3 → 4 → 5.**

**`depends_on: [bp-110]`** — the protocol. Transitively after bp-108/bp-109.
**`parallelizable_with: [bp-113]`** — disjoint production files (`core/ingest/sync.py` +
`index.py` + `scheduler/vault_sync.py` here; `code_corpus.py` + `code_sync.py` there) and disjoint
test files. ⚑ **Verified disjoint, not assumed**: the one file that could have collided is
`core/ingest/index.py`, and the code lanes do not use `index_amendment` — they use `code_rows` +
`store.add` directly (`core/ingest/code_corpus.py:277-278`).

Sequenced **after** bp-113 in the note's stated order (longest lane first), but the two may run
concurrently as worktrees. If they do, ⚑ **read bp-113's landed landing idiom before writing this
one** (§2) — two idioms for one protocol is the DRY defect this pair is most exposed to, and it
is the kind that only shows up at merge.
