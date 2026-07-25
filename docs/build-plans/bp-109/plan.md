---
type: build-plan
id: bp-109
track: ops
status: proposed
design_ref:
  - docs/design-notes/dn-supervision-and-liveness.md
contract: builder
write_scope:
  - scheduler/queue.py
  - ops/lifecycle/snapshot.py
  - tests/unit/test_queue_leases.py
  - tests/unit/test_queue_coalescing.py
  - tests/unit/test_queue_orphan_sweep.py
  - tests/unit/test_restart_trustworthy.py
  - tests/integration/test_lifecycle.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 180k
  actual: null
depends_on: [bp-108]
parallelizable_with: [bp-115]
created: 2026-07-25
updated: 2026-07-25
links:
  - docs/findings/finding-0187.md
  - docs/findings/finding-0173.md
  - docs/findings/finding-0170.md
re_entry: null
supersedes: null
superseded_by: null
warrant: docs/findings/finding-0187.md
---

# Build Plan — a RUNNING row carries its own deadline, and a checkpointed row stops being swallowed

## 0. Mode & provenance

Graduated from `dn-supervision-and-liveness` §2.6 (leased RUNNING rows — the third of the note's
three small independent pieces) with **V6** folded in, because V6's fix is a change to the same
coalesce path in the same file and it **blocks every later plan** (§2.5 disqualifies batch-yield
until it is pinned). Investigation and planning produced this; implementation proceeds
item-by-item on owner approval.

## 1. Objective

The queue's `state` column stops being something a reader has to trust: a RUNNING row is
orphaned *by definition* once its deadline passes, and a checkpointed QUEUED row is no longer a
valid collapse target.

### 1.2 Non-goals (explicit — see §9)

Not the partial UNIQUE index (§9), not a retry/backoff policy, not the worker protocol. [INFERENCE]
Also not a change to what `attempts` means or to terminal-state semantics — inferred from
`dn-supervision-and-liveness` §1.2's "NOT a retry / dead-letter / backoff policy redesign", which
is itself marked `[INFERENCE]` in the note. Read both at the gate.

## 2. Context manifest

Read in order, whole files before citing:

1. `docs/design-notes/dn-supervision-and-liveness.md` §2.6 (the "Leased RUNNING rows" bullet and
   the five-target table's first row), §2.10, **V6** — the content spec
2. `docs/findings/finding-0187.md` — the warrant: deleting bp-105's sweep call left 85/85 green
3. `docs/findings/finding-0173.md` — why `claimed_by_run` exists; the sweep's safety argument
4. `scheduler/queue.py` — **whole file, 448 lines.** The DDL `:94-114`, `_MIGRATIONS` `:127-129`,
   `enqueue`/coalesce `:232-279`, `claim` `:292-324`, `sweep_orphans` `:350-394`,
   `checkpoint` `:396-403`
5. `ops/lifecycle/snapshot.py:91-117,157-265` — `run_state`, `QueueStats` and the anomaly
   predicates that read RUNNING rows
6. `docs/build-plans/bp-105/journal.md` Checkpoint 1 — why the checkpoint/coalescing collision
   disqualified cooperative batching as a channel

**Does core already have this?** The additive-migration mechanism already exists and must be
**reused, not re-invented**: `_migrate` (`queue.py:132-140`) reads `PRAGMA table_info` and applies
only missing `ALTER TABLE … ADD COLUMN` statements. A new column is **one tuple appended to
`_MIGRATIONS`** plus its line in `_DDL`. Do not write a second migration path.

## 3. Investigation & grounding  <!-- Part A -->

- **Q1 — is `claim()` really the only RUNNING constructor?** **Yes.** `queue.py:318-322` is the
  only statement in the file that sets `state = RUNNING`; `sweep_orphans` (`:385-389`) and
  `checkpoint` (`:400-402`) only move rows *out* of RUNNING. That single-constructor fact is what
  licenses the note's tier-2 claim; it is verified, not assumed.
- **Q2 — V6: is the checkpoint/coalescing collision real?** ⚑ **CONFIRMED BY READING — it needs no
  measurement.** `checkpoint()` sets `state = QUEUED` while leaving the `checkpoint` token on the
  row (`queue.py:400-402`). The coalesce lookup keys on
  `state = ? AND kind = ? AND payload IS ? AND tier = ? AND num_ctx = ?` (`queue.py:262-264`) and
  **does not mention the `checkpoint` column at all**. So a fresh `enqueue("code_backfill", …)`
  with a matching payload returns the *checkpointed, partially-advanced* row (`:271`) instead of
  inserting. The caller believes a full re-derivation is queued; what is queued is a resume from
  mid-pass. bp-105 Checkpoint 1's reading is correct.
- **Q3 — what does the fix cost?** One extra clause in the lookup. The correct form is
  `AND checkpoint IS NULL`, which can only ever *create* a row, never drop one — the same
  conservative direction `enqueue`'s docstring already commits to (`:257`: "errs toward an extra
  row, never a lost job").
- **Q4 — can SQLite make an undeadlined RUNNING row uninhabitable (tier 1)?** **No.** `_migrate`
  is `ALTER TABLE … ADD COLUMN` only (`:132-140`), and SQLite cannot add a `CHECK` constraint to
  an existing table without a full table rewrite, which `:117-120` forbids outright (300k+ lifetime
  rows, never recreated). The note claims tier 2 + tier 4 for exactly this reason; the claim is
  correct and must not be inflated in the code comments.
- **Q5 — who reads `state == RUNNING` today, and would they all be corrected?** Three readers:
  `snapshot.py`'s `QueueStats`/predicates (`:157-265`), the sweep's own SELECT (`queue.py:374-378`),
  and `Supervisor.tick`'s post-handler check (`scheduler/supervisor.py:94`). **The third must NOT
  change** — it asks "did the handler checkpoint-yield?", a question about the row's *state*, not
  about liveness, and re-keying it on a deadline would break cooperative yielding. Item 3 changes
  the first two only.
- **Q6 — what is the deadline's clock?** **The code does not settle this.** Every timestamp in
  the queue is a wall-clock ISO string truncated to seconds (`_utcnow`, `queue.py:142-143`), and
  `_effective_priority` already does wall-clock arithmetic over `created_at` (`:287`). Consistency
  argues for wall-clock; correctness under a clock jump argues for monotonic. **§11 parks this
  with wall-clock as the default** (it must be readable by a *separate* process — `status` — which
  a monotonic clock cannot support), and names the exposure.
- **Q7 — what deadline value?** **The code does not settle this either, and it must not be
  guessed.** No job budget exists anywhere today (finding-0178; `launcher.py:1158-1160` prints
  "(no enforced job budget)"), and the live `code_backfill` lane legitimately runs for hours. A
  deadline shorter than an honest long job is the cry-wolf disqualifier (bp-102 §10). §11 parks
  the value and §6 pins the shape that keeps it safe: **the column is nullable, and NULL means
  "no deadline" — which reads exactly as today.**

**Additional risks or questions surfaced during reading:**

- ⚑ **The live queue file holds 1,766 duplicate QUEUED rows** (`queue.py:122-126`). The migration
  must be safe against that — it is, being additive — but the builder must **not** take the
  opportunity to add the partial UNIQUE index the same comment describes: it would raise on open
  and make the daemon unstartable until the duplicates are cleared. §9 makes this an explicit
  non-goal.
- Every existing RUNNING row (including live orphan 300246) will have `lease_expires_at IS NULL`
  after the migration. The derived reader must therefore treat NULL as *not expired*, or the
  migration itself would mass-orphan the queue's history on first open.
- `tests/unit/test_restart_trustworthy.py` and `tests/integration/test_lifecycle.py` are carried
  because bp-108 also edits them and they assert on sweep/row shape — see §12 on why this plan is
  **sequenced after** bp-108 rather than parallel to it.

## 4. Reconciliation  <!-- Part B -->

- **`scheduler/queue.py:117-126`** — the `_MIGRATIONS` comment block, currently describing exactly
  one migration and one deliberately-omitted index → **cross-ref: extension.** Add the new column
  to the block's prose in the same voice, and **preserve verbatim** the paragraph explaining why
  the partial UNIQUE index is still not created. Do not rewrite that paragraph; it is a live
  operational constraint, not stale commentary.
- **`scheduler/queue.py:235-257`** — `enqueue`'s docstring enumerates "Three properties make the
  collapse safe to reason about" → **banner: correction.** The list is now incomplete: a
  checkpointed row was a collapse target and should not have been. Add a fourth property naming
  the exclusion, and say plainly that this corrects a defect (bp-105 CP1 / V6) rather than adding
  a feature.
- **`scheduler/queue.py:350-371`** — `sweep_orphans`'s docstring argues its safety from run-id
  ordering → **cross-ref: extension.** The deadline is a *second, independent* reason a row is
  reclaimable. Extend the argument; do not replace it — finding-0173's reasoning still holds and
  is what protects rows this run actually claimed.

## 5. Write scope

`scheduler/queue.py` is the whole production surface for Items 1–2 and 4.
`ops/lifecycle/snapshot.py` carries Item 3's derived readers only. `tests/unit/test_queue_leases.py`
is new. `tests/unit/test_queue_coalescing.py` and `tests/unit/test_queue_orphan_sweep.py` are
**carried because they pin the surface this plan moves** — the first asserts the exact collapse
key, the second the exact sweep behaviour. `tests/unit/test_restart_trustworthy.py` and
`tests/integration/test_lifecycle.py` are carried for the same reason at one remove (they assert
sweep results and row shape).

Deliberately OUT of scope: `scheduler/supervisor.py` (§3 Q5 — its RUNNING check is a different
question and must not move), `ops/lifecycle/launcher.py` (bp-108 and bp-111 own it), the live
`data/queue.sqlite` (never edited by hand), and every foundation-denylist file.

## 6. Interfaces pinned inline

**The migration — exact shape, appended to the existing tuple** (`scheduler/queue.py:127-129`):

```python
_MIGRATIONS: tuple[tuple[str, str], ...] = (
    ("claimed_by_run", "ALTER TABLE jobs ADD COLUMN claimed_by_run INTEGER"),
    ("lease_expires_at", "ALTER TABLE jobs ADD COLUMN lease_expires_at TEXT"),   # NEW
)
```

⚑ **Nullable, and NULL means "no deadline".** Every pre-existing row — including the live orphan
300246 — gets NULL on first open. A reader that treats NULL as *expired* would mass-orphan the
queue's entire history at migration time. This is the single most dangerous mistake available in
this plan.

**The derived reader — the whole point of the mechanism:**

```python
def lease_expired(job: Job, now: datetime) -> bool:
    """True iff this row's claim has demonstrably lapsed. NULL deadline ⇒ False (today's
    behaviour, and every row written before this column existed). The orphan question stops
    being "did someone remember to sweep?" and becomes a property of the row."""
```

**The coalesce lookup's exact current form** (`scheduler/queue.py:261-265`) — Item 4 adds one
clause and nothing else:

```python
                waiting = self._conn.execute(
                    "SELECT id, priority FROM jobs WHERE state = ? AND kind = ? AND payload IS ? "
                    "AND tier = ? AND num_ctx = ? ORDER BY id LIMIT 1",
                    [QUEUED, kind, blob, tier, num_ctx],
                ).fetchone()
```

**`claim()`'s exact current UPDATE** (`scheduler/queue.py:318-322`) — Item 2 stamps the deadline
here, in the one place a RUNNING row is ever constructed:

```python
            self._conn.execute(
                "UPDATE jobs SET state = ?, started_at = ?, attempts = attempts + 1, "
                "claimed_by_run = ? WHERE id = ?",
                [RUNNING, _utcnow(), self.active_run_id, chosen.id],
            )
```

**The timestamp helper, reused not re-invented** (`scheduler/queue.py:142-143`):

```python
def _utcnow() -> str:
    return datetime.now(UTC).replace(tzinfo=None).isoformat(timespec="seconds")
```

## 7. Items

Blast radius: schema (additive, reversible by ignoring the column) → the single constructor →
derived readers → the coalesce correction → the ratchet.

### Item 1 — the additive column

- **Objective:** `jobs` carries `lease_expires_at`, and an existing queue file is extended, never
  rewritten.
- **Files:** `scheduler/queue.py`, `tests/unit/test_queue_leases.py`
- **Acceptance test:** open a queue file written by the pre-change code (fixture built by
  constructing with the old `_DDL`), assert the column appears, that **no row's `id`, `state`,
  `created_at` or `attempts` changed**, and that opening twice is a no-op.
- **Falsifier:** *any pre-existing row differs after the migration.* `data/queue.sqlite` carries
  300k+ lifetime rows and is never recreated — a migration that touches one of them is
  unrecoverable.
- **Invariant(s) it must not violate:** additive-only; `_MIGRATIONS` remains the single migration
  path; the partial UNIQUE index is **not** created (§9).
- **Touches stored data?** ⚑ **Yes — schema on the live queue.** Require a dry-run against a
  **copy** of `data/queue.sqlite` before the change is considered done, and record the row counts
  before/after in the journal.
- **Parallelizable?** No. **Depends on:** none.

### Item 2 — `claim()` stamps the deadline

- **Objective:** every RUNNING row minted from now on carries a deadline.
- **Files:** `scheduler/queue.py`, `tests/unit/test_queue_leases.py`
- **Acceptance test:** a claimed job has `lease_expires_at` set to `now + budget(kind)`; a job
  claimed with no configured budget has NULL; the value round-trips through `_row_to_job`.
- **Falsifier:** *a RUNNING row exists with a NULL deadline that was minted after this item.* That
  is the tier-2 claim failing at its only constructor.
- **Invariant(s) it must not violate:** `claim()`'s selection policy (effective priority →
  swap-avoidance → FIFO, `:313-317`) is byte-for-byte unchanged; the deadline is stamped, never
  *enforced* here (enforcement is bp-111's escalation, and a queue that kills its own jobs would
  be the ledger written by the actor it must record — the class §2.8 names).
- **Touches stored data?** Yes (new column values only). **Parallelizable?** No. **Depends on:**
  Item 1.

### Item 3 — readers derive orphanhood instead of trusting `state`

- **Objective:** the sweep becomes a lazy reap over a derived view rather than a call someone must
  remember to make.
- **Files:** `scheduler/queue.py`, `ops/lifecycle/snapshot.py`, carried test files
- **Acceptance test:** a RUNNING row with an elapsed deadline reads as orphaned from
  `snapshot.py`'s stats **with no sweep having run**; `sweep_orphans` still reclaims by
  `claimed_by_run` as well (both reasons, independently sufficient); a NULL-deadline RUNNING row
  behaves exactly as today.
- **Falsifier:** ⚑ *deleting the sweep call still leaves the suite green.* This is finding-0187's
  literal failure and this plan's warrant. Plant that mutation; if it does not redden, the derived
  reader is not actually being consulted and nothing has changed.
- **Invariant(s) it must not violate:** `Supervisor.tick`'s RUNNING check (`supervisor.py:94`) is
  **not** touched (§3 Q5); an expired-deadline row is *reported* orphaned, never silently deleted;
  the ORPHANED render bp-102 added keeps working.
- **Touches stored data?** No (read path). **Parallelizable?** No. **Depends on:** Item 2.

### Item 4 — V6: a checkpointed row is not a collapse target

- **Objective:** enqueueing an idempotent kind while a checkpointed row waits inserts a fresh job
  instead of returning a half-advanced one.
- **Files:** `scheduler/queue.py`, `tests/unit/test_queue_coalescing.py`
- **Acceptance test:** checkpoint a `code_backfill` row (so it is QUEUED with a non-NULL token),
  then `enqueue` the same kind+payload: a **new** row is returned, and the checkpointed row is
  untouched. Every existing coalescing test still passes unedited.
- **Falsifier:** ⚑ *the checkpointed row is returned.* That is the defect verbatim — the caller's
  request for a full re-derivation is silently answered with a resume.
- **Invariant(s) it must not violate:** the fix may only *create* rows, never drop one; the
  first-row-wins and `created_at`-preservation properties (`:250-254`) are unchanged; the priority
  promotion on collapse still works.
- **Touches stored data?** No. **Parallelizable?** Yes (independent of Items 1–3).
  **Depends on:** none.

### Item 5 — the ratchet the tier-4 claim rests on

- **Objective:** "no RUNNING row lacks a deadline" is proven by a test, not asserted in a comment.
- **Files:** `tests/unit/test_queue_leases.py`
- **Acceptance test:** a property/scan test asserting (a) that `claim()` is the only site in
  `scheduler/queue.py` setting `state = RUNNING` — an AST or source scan, so a *new* constructor
  added later fails the gate; and (b) that after an arbitrary interleaving of enqueue/claim/
  checkpoint/sweep, every RUNNING row minted in the test has a deadline.
- **Falsifier:** ⚑ *adding a second `state = RUNNING` writer elsewhere in the file leaves the
  ratchet green.* Plant exactly that mutation. bp-106's warrant is the same species — a rule with
  no mechanical enforcement is not a rule (`ops/type_gate` had no `typedshims` scan, which is how
  bp-105's raw import passed every gate).
- **Invariant(s) it must not violate:** the scan must catch a **function-local** writer, not only
  a module-level one — bp-106's Item 4 records that a module-level-only AST walk reproduces the
  hole exactly.
- **Touches stored data?** No. **Parallelizable?** No. **Depends on:** Items 1–2.

## 8. Math carried explicitly

N/A — no mathematical object. The deadline is a timestamp comparison; the existing anti-starvation
aging (`_effective_priority`, `queue.py:281-290`) is untouched by this plan.

## 9. Non-goals

- ⚑ **No partial UNIQUE index on `(kind, payload) WHERE state = 'queued'`.** `queue.py:122-126`
  records why: the live file holds 1,766 duplicate queued rows, so `CREATE UNIQUE INDEX` raises on
  open and **makes the daemon unstartable**. It becomes available only after the restart clears
  them. Do not take the opportunity.
- **No enforcement of the deadline.** Stamping is here; killing is bp-112. A queue that terminates
  its own jobs is the class §2.8 names.
- **No retry / backoff / dead-letter policy** (`dn-supervision-and-liveness` §1.2).
- **No change to `Supervisor.tick`** (§3 Q5).
- **No table rewrite, ever** — additive columns only (`queue.py:117-120`).
- **No new migration mechanism** — `_MIGRATIONS` + `_migrate` already exist.

## 10. Stop-and-raise conditions

- ⚑ **The dry-run against a copy of the live queue shows any pre-existing row changed** ⇒ **STOP.**
  That is Item 1's falsifier on the one file that cannot be rebuilt from git.
- **A sane default deadline cannot be chosen without cry-wolfing the multi-hour lanes** ⇒ park
  the criterion (leave the column NULL-by-default, which is exactly today's behaviour), file the
  question, continue. Never block on the owner. **Do not invent a number**: §3 Q7 records that no
  budget exists anywhere today to calibrate against.
- **Item 3's or Item 5's planted mutation does not redden the suite** ⇒ STOP and file. A guard
  whose deletion is invisible is finding-0187 again, and shipping it would be worse than shipping
  nothing, because it would be *believed*.
- **A carried test cannot be made green without weakening an assertion** ⇒ STOP and file.
- Any blessing transition — never.

## 11. Parked decisions

| Decision | Default recorded | Re-entry condition |
|---|---|---|
| deadline clock | wall-clock ISO, as `_utcnow` | a clock-jump orphaning is observed |
| default budget per kind | NULL (no deadline) | bp-112 lands escalation |
| where the reap happens | lazy, at read | reads become hot |
| partial UNIQUE index | not created | the restart clears the 1,766 duplicates |

**Rejected alternatives, per row:**

- **Deadline clock.** Rejected: *`time.monotonic`* — strictly more correct across a clock jump,
  but monotonic values are **meaningless across processes**, and `status` reads this column from a
  different process than the supervisor that wrote it. That is disqualifying, not a preference.
  The exposure (a backwards clock step makes deadlines look further away) is accepted and named.
- **Default budget.** Rejected: *a per-kind number now* — §3 Q7: there is no measurement to
  calibrate against and a short deadline kills a healthy 14-hour backfill on schedule (bp-102 §10).
  Rejected: *one global budget* — the lanes differ by four orders of magnitude in honest runtime.
- **Reap location.** Rejected: *a background reaper thread* — it would be a second actor writing
  the ledger it must record, the class the note names, and it needs the loop the worker split has
  not yet unblocked. Rejected: *reap inside `claim()`* — makes the hot path do write work.
- **Partial UNIQUE index.** Rejected: *create it now* — bricks the daemon (§9). This row is
  recorded so the option is not lost when the duplicates clear.

## 12. Dependency & ordering summary

Items: **1 → 2 → 3 → 5**, with **4 independent** (a one-clause fix to a different method).

⚑ **`depends_on: [bp-108]`, and the reason is a test-file collision, not a code dependency.**
Nothing in this plan needs bp-108's lock. But both plans carry
`tests/unit/test_restart_trustworthy.py` and `tests/integration/test_lifecycle.py` — bp-108
because `start()`'s preconditions change, this plan because sweep results and row shape change.
Two worktrees editing those files concurrently is exactly the finding-0191 shape the note orders
graduation to resolve, so they are **sequenced instead of parallelized**. Parallel with **bp-115**
(disjoint: `core/models/` + `core/ingest/embed.py`).

**bp-110 depends on this plan** and the reason is substantive: `dn-supervision-and-liveness` §2.5
disqualifies cooperative batching until V6 is pinned, so Item 4 must land before any batch-yield
protocol exists.
