---
type: build-plan
id: bp-101
track: ops
status: complete
design_ref:
  - docs/design-notes/temporal-code-corpus.md
contract: builder
write_scope:
  - scheduler/queue.py
  - tests/unit/test_queue*.py
  - tests/unit/test_scheduler*.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 110k
  actual:
    model: opus              # claude-opus-5, single delegated builder in a worktree, session-44
    tokens: 144k             # harness-measured (144,200); 89 tool calls; 36.7 min wall
    ratio: 1.31              # vs 110k — inflated by the live-queue dry-run, which was worth every token
    session_delta: one delegated builder; all 3 items closed, both falsifiers held, 23 new tests
    notes: >-
      Falsified its own warrant: finding-0170's proposed partial UNIQUE INDEX cannot be created —
      it raises against the 882 identical queued rows and would make the daemon UNSTARTABLE.
      Banner-corrected f-0170 (58919fc); coalescing enforced in enqueue instead, index deferred
      until the restart clears duplicates. Also corrected the counts (882+882+1+1 = 1,766, not
      883/883) and found the module header's state machine was ALREADY wrong (checkpoint() has
      always driven RUNNING→QUEUED). Deviations surfaced not hidden: match key adds tier/num_ctx
      (strictly narrower ⇒ can only create a row, never drop one); collapse promotes priority,
      never demotes; `ambassador` excluded conservatively with reasoning. Builder finding
      renumbered 0175→0177 at integration (three-way id collision). Its hand-off — the sweep had
      no caller — was closed by the orchestrator integration commit be225fd.
    week_delta: +4%          # weekly 2%→6% across the 3-builder wave spawn→seal (resets Jul 31)
depends_on: []
parallelizable_with:
  - bp-100
  - bp-102
created: 2026-07-25
updated: 2026-07-25
links:
  - docs/findings/finding-0170.md
  - docs/findings/finding-0173.md
  - docs/findings/finding-0165.md
re_entry: null
supersedes: null
superseded_by: null
warrant: docs/findings/finding-0170.md
---

# Build Plan — bp-101: queue hygiene — enqueue coalescing and orphaned-job reclaim

## 0. Mode & provenance

Corrective plan warranted by **finding-0170** (no enqueue coalescing) and **finding-0173** (killed
workers orphan their `running` rows) — both measured during the 2026-07-25 incident, not inferred.
Authority-to-act is the owner's instruction to plan tonight's build; `proposed → ready` remains
owner-only and is not performed here.

## 1. Objective

Make the queue bounded under a busy worker (idempotent jobs coalesce instead of stacking) and
self-healing after an unclean exit (orphaned `running` rows are reclaimed, not stranded).

## 2. Context manifest

1. `scheduler/queue.py` — whole file. The schema (`:62+`), `enqueue` (`:144`), `claim` (`:172`),
   `_effective_priority` (`:158`), `_finish`/`fail` (`:198-201`), `requeue_deferred` (`:213`),
   `depth` (`:261`). The DEFERRED→QUEUED requeue at `:213-216` is the closest existing idiom to the
   orphan sweep — read it before writing a second one.
2. `docs/findings/finding-0170.md` — the coalescing defect and its measurements (13 → 1,766).
3. `docs/findings/finding-0173.md` — the orphan defect; job 300246 is the live example.
4. `scheduler/chat_sync.py` — `build_chat_watcher` / `_on_change` (`:56-77`), the unconditional
   enqueue call site, and the `[chat]` debounce/poll config it honors.
5. `ops/lifecycle/launcher.py` — read ONLY to find where the supervisor starts and what would call
   a startup sweep. **Do not edit it** (bp-102 owns that file).
6. `docs/findings/finding-0165.md` — background starvation; this plan reduces its blast radius but
   does not fix it.

**DRY audit — does the queue already implement this?** Partially, and it must be reused:
`requeue_deferred` (`:213`) is already a state-sweeping UPDATE over a state class — the orphan
sweep is the same shape and should follow it rather than inventing a parallel mechanism. There is
**no** existing dedup/coalescing anywhere in `scheduler/`; that half is genuinely new. Check
`core/` for an existing idempotency-key helper before writing one.

## 3. Investigation & grounding

- **Q1 — Is `enqueue` really unconditional?** Yes. `scheduler/queue.py:144-156` is a bare INSERT
  under a lock, with no SELECT and no uniqueness constraint. The table (`:62+`) declares no unique
  index on `(kind, state)`.
- **Q2 — Which kinds are safe to coalesce?** Observed stacking: `chat_sync` (883) and `vault_sync`
  (883), both idempotent full re-syncs. **Code does not settle the general answer** — the builder
  must enumerate every `enqueue` call site and classify each kind as collapsible or not, and MUST
  key on `(kind, payload)` rather than `kind` alone, or a payload-bearing job could be silently
  dropped. Where a kind's idempotency is not evident from its handler, treat it as NOT collapsible.
- **Q3 — Does anything depend on duplicate jobs existing?** Anti-starvation aging
  (`_effective_priority`, `:158`) ages a job by `created_at`. Collapsing to the FIRST occurrence
  preserves aging correctly; collapsing to the LAST would reset the clock and could starve a job
  that a busy period keeps refreshing. **Prefer keeping the existing row.**
- **Q4 — How is an orphan identified?** Today: only heuristically, by "state = running while no
  worker lives". There is **no `claimed_by_run` column** and no lease/heartbeat — `jobs` has no
  column tying a row to the run that claimed it. Adding one makes the sweep exact instead of
  inferential; that is the recommended path, and it is a schema migration (additive).
- **Q5 — What is the live orphan?** Job **300246** (`code_sync`, started `2026-07-25T03:45:07`),
  stranded by the owner-authorized `kill -9` of run #35. It is the acceptance fixture: after this
  plan, a sweep must reclaim or fail it explicitly.
- **Q6 — Where does the sweep run?** At supervisor start, before the first `claim()`. The wiring
  call site is in `ops/lifecycle/launcher.py`, which this plan MAY NOT WRITE. **Expose the sweep as
  a public method on `JobQueue` and file the one-line wiring as a finding for bp-102** (or the
  merge), rather than reaching outside write_scope. (Wiring-is-part-of-finishing applies: flag this
  explicitly at seal so the switch is not left unbuilt.)

**Additional risks surfaced:** the additive schema migration must be idempotent and must not break a
queue file written by the pre-change code — `data/queue.sqlite` holds 300k+ lifetime rows on the
live system and is NOT to be recreated.

## 4. Reconciliation

- `scheduler/queue.py:144` `enqueue` — no prose claims uniqueness, so this is an **extension**, not
  a correction: **cross-ref** the new coalescing contract in the method docstring, citing
  finding-0170, and state explicitly which kinds collapse.
- `scheduler/queue.py:172` `claim` docstring (§13 policy) — **cross-ref: extension** noting that a
  startup sweep now precedes claiming, so `running` rows are trustworthy.
- The module header (`:3`) describes the lifecycle as `QUEUED→RUNNING→DONE/FAILED/DEFERRED` —
  **banner: correction** if the sweep introduces a reclaim edge (`RUNNING→QUEUED`); the stated
  state machine would otherwise be wrong.

## 5. Write scope

- `scheduler/queue.py` — coalescing, the sweep, the additive schema column.
- `tests/unit/test_queue*.py`, `tests/unit/test_scheduler*.py` — coverage.

Deliberately OUT of scope: `ops/lifecycle/launcher.py` (bp-102 owns it — the sweep's wiring is
handed over as a finding), `core/stores/**` (bp-100), `scheduler/chat_sync.py` and the other
handlers (call sites are correct; the fix belongs in the queue), the live `data/queue.sqlite`
(clearing the 1,766 duplicates is a RESTART step, not a code change).

## 6. Interfaces pinned inline

```python
QUEUED, RUNNING, DONE, FAILED, DEFERRED = "queued", "running", "done", "failed", "deferred"  # :39

CREATE TABLE IF NOT EXISTS jobs (            # :62 — columns referenced below
    ... kind, tier, num_ctx, priority, state, payload, created_at,
        started_at, finished_at, error, checkpoint, attempts ... )

def enqueue(self, kind: str, tier: str, num_ctx: int, *,                      # :144
            priority: int = PRIORITY_DEFAULT,
            payload: dict[str, Any] | None = None) -> Job:
    with self._lock:
        cur = self._conn.execute(
            "INSERT INTO jobs (kind, tier, num_ctx, priority, state, payload, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            [kind, tier, num_ctx, priority, QUEUED,
             json.dumps(payload) if payload else None, _utcnow()])
        ...
        return self.get(cur.lastrowid)

def requeue_deferred(self) -> int:                                            # :213 — the idiom to follow
    "UPDATE jobs SET state = ?, error = NULL WHERE state = ?", [QUEUED, DEFERRED]
```

**Contract that must not change:** `enqueue` returns a `Job`. When a call coalesces onto an existing
row it must still return a `Job` (the existing one) — callers such as `launcher.code_backfill`
(`ops/lifecycle/launcher.py:737`) print `job.id`, so returning `None` would break them.

## 7. Items

Blast-radius order: schema (additive, reversible) → read-side sweep → write-side coalescing.

### Item 1 — Additive `claimed_by_run` column + idempotent migration

- **Objective:** A job row records which run claimed it, so orphan detection is exact.
- **Files:** `scheduler/queue.py`, `tests/unit/test_queue*.py`.
- **Acceptance test:** Opening a queue file written by the pre-change schema adds the column and
  preserves every existing row and state; running twice is a no-op.
- **Falsifier:** Any pre-existing row's `state`, `created_at`, or `id` changes across the
  migration — the migration is rewriting history rather than extending the schema.
- **Invariants:** `data/queue.sqlite` is never recreated; lifetime counters unchanged.
- **Touches stored data?** **Yes — schema.** Dry-run against a COPY of the live queue file before
  any real open, and report row counts before/after.
- **Parallelizable?** No (gates Item 2). **Depends on:** none.

### Item 2 — Orphan sweep

- **Objective:** `JobQueue.sweep_orphans(active_run_id)` reclaims `running` rows whose owning run is
  not the live one: idempotent kinds → `QUEUED`; others → `FAILED` with
  `error = "orphaned by unclean exit of run #N"`.
- **Files:** `scheduler/queue.py`, tests.
- **Acceptance test:** A fixture reproducing job 300246 (a `running` row with a dead owning run) is
  reclaimed; a genuinely running job owned by the live run is NOT touched.
- **Falsifier:** The sweep reclaims a job that a live worker is actively running — producing double
  execution. Test explicitly with a live-run-owned `running` row present.
- **Invariants:** Never touch `done`/`failed` rows; the state machine documented in the module
  header stays accurate (update it — see §4).
- **Touches stored data?** Yes, in tests only (temp queues). The live sweep happens at restart.
- **Parallelizable?** No. **Depends on:** Item 1.
- **Hand-off:** the supervisor-start wiring lives in `ops/lifecycle/launcher.py` (out of scope) —
  file a finding at seal so the switch is built, not merely available (Q6).

### Item 3 — Enqueue coalescing

- **Objective:** For kinds classified collapsible, `enqueue` returns the existing QUEUED job instead
  of inserting a duplicate.
- **Files:** `scheduler/queue.py`, tests.
- **Acceptance test:** 1,000 successive `enqueue("chat_sync", …)` calls with no drain produce
  exactly ONE queued row; a payload-bearing kind with distinct payloads produces distinct rows.
- **Falsifier:** A job that SHOULD have run is dropped — e.g. a `code_backfill` enqueued while one
  is `running` (not `queued`) silently vanishes, so the follow-up never happens. Test the
  running-not-queued case explicitly; collapsing must consider only QUEUED rows.
- **Invariants:** aging preserved (keep the FIRST row, per Q3); `enqueue` still returns a `Job`;
  non-collapsible kinds behave exactly as today.
- **Touches stored data?** No.
- **Parallelizable?** No. **Depends on:** Item 1 (schema settled first).

## 8. Math carried explicitly

N/A — no mathematical object implemented. (The queue's anti-starvation aging is existing math this
plan preserves rather than introduces; Q3 records the constraint it imposes.)

## 9. Non-goals

- **Not** finding-0165 (background starvation / tier scheduling). This shrinks its blast radius; it
  does not fix priority inversion.
- **Not** job budgets or the drain bound (finding-0171 — owner decision pending, see oq).
- **Not** clearing the live 1,766 duplicates — that is a restart step, not code.
- **Not** touching watcher debounce/poll config; the fix belongs in the queue, not the sensors.
- **Not** wiring the sweep into the supervisor (out of write_scope — handed over as a finding).

## 10. Stop-and-raise conditions

- Any kind's idempotency cannot be established from its handler → do NOT collapse it; record the
  classification in the journal and, if the ambiguity is load-bearing, file a finding.
- The dry-run of Item 1 against a copy of the live queue shows any row mutation → STOP.
- The double-execution falsifier (Item 2) fires → STOP; a reclaim that races a live worker is worse
  than the orphan it fixes.
- Temptation to edit `ops/lifecycle/launcher.py` to wire the sweep → STOP, file the finding.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| Lease/heartbeat vs run-id ownership | Run-id ownership (Item 1) | Full lease + heartbeat — stronger (catches a HUNG worker, not just a dead one) but needs a cancellation seam that does not exist yet | Owner's answer on finding-0171 (job budgets); design them together then |
| Collapse to first vs last occurrence | First (preserves aging, Q3) | Last — resets `created_at`, can starve a job during sustained load | If a kind is found where freshness matters more than aging |
| Which kinds collapse | Builder classifies from handlers; unknown ⇒ NOT collapsible | Blanket-collapse all background kinds (risks silently dropping payload-bearing work) | A payload-bearing kind is later shown safe |

## 12. Dependency & ordering summary

Sequential: **Item 1 → Item 2, Item 1 → Item 3.** Items 2 and 3 are independent of each other and
may be done in either order once the schema lands.

Across plans: no dependencies; `parallelizable_with` bp-100 and bp-102 (disjoint write scopes —
`scheduler/**` here). Not the restart blocker (that is bp-100), but **required before `palace up`**
so the restart does not immediately re-accumulate duplicates and does not start with a phantom
running job.
