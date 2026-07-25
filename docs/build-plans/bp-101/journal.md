---
type: journal
plan: bp-101
created: 2026-07-25
updated: 2026-07-25
---

# Journal — bp-101 (queue hygiene: coalescing + orphan reclaim)

Worktree: `/Users/ascalva/mind-palace/.claude/worktrees/agent-ae5e897949632a574` (branch `main`
inside the worktree). Daemon is DELIBERATELY DOWN for this build — never start it.

## Grounding read (done)

Read in §2 order: `scheduler/queue.py` (whole), finding-0170, finding-0173, `scheduler/chat_sync.py`,
`ops/lifecycle/launcher.py` (read-only, start path + `Components`), finding-0165. Plus every
`enqueue()` call site (`scheduler/{cron,interface,code_sync,vault_sync,chat_sync}.py`),
`scheduler/router.py` kind tables, `ops/lifecycle/runs.py` (the run ledger the `claimed_by_run`
column points at), and `core/interface.py:57` (`CoreInbox.process_once`, for the `ambassador` kind).

### Facts established before writing code

- The run identity that `claimed_by_run` references is `ops/lifecycle/runs.py` `runs.id`
  (INTEGER AUTOINCREMENT) — the same `#N` the launcher prints (`launcher.py:490`). A freshly-opened
  run id is therefore strictly greater than any id stamped on a pre-existing row: **no pre-existing
  row can carry the new run's id.** This is what makes the start-of-run sweep safe.
- `Components.queue` (`launcher.py:220`) is a `QueueLike` Protocol declaring only `close()`. The
  wiring hand-off therefore needs the Protocol widened by one line as well as the call — recorded in
  the hand-off finding, NOT done here (bp-102 owns that file).
- The plan §6 pins the reclaim idiom as `requeue_deferred` (`:213`); the method is actually named
  **`revive_deferred`**. Line number and body match — a naming slip in the plan, not a code defect.
  Followed the code.
- **The module header at `:3` was ALREADY wrong before this plan.** `checkpoint()` (`:221`) sets
  `state = QUEUED` from RUNNING, so a `RUNNING→QUEUED` edge already existed, and `revive_deferred`
  adds `DEFERRED→QUEUED`; neither appears in the stated
  `QUEUED→RUNNING→DONE/FAILED/DEFERRED`. §4's "banner: correction" therefore applies to more than
  the new edge — the header is rewritten to state the whole machine.

### Kind-by-kind collapsibility classification (Q2 / parked decision 3)

One frozenset `_IDEMPOTENT_KINDS` serves BOTH the coalescing test and the orphan-reclaim test,
because both rest on the same property: *the handler is a full re-derivation that is safe to run
twice and carries no distinguishing payload*. A kind qualifies only when its handler docstring or
body establishes that; unknown ⇒ NOT collapsible (plan §11 default).

| kind | handler | evidence | collapsible / requeue-on-orphan |
|---|---|---|---|
| `chat_sync` | `scheduler/chat_sync.py:40` `sensor.sync()` | docstring `:48` "idempotent + growth-aware (an unchanged session is skipped)"; no payload | YES |
| `vault_sync` | `scheduler/vault_sync.py:31` `sync.rescan()` | docstring `:39` "duplicate jobs are harmless because `rescan()` is idempotent"; no payload | YES |
| `code_sync` | `scheduler/code_sync.py:37` `sync.sync()` | docstring `:45` "idempotent + blob-sha keyed (an unchanged file re-embeds nothing)"; no payload | YES |
| `code_backfill` | `scheduler/code_sync.py:53` | docstring `:53` "idempotent — already-embedded digests are skipped"; `capture_commit_diffs` is keyed by commit; no payload | YES |
| `chat_events` | `scheduler/cron.py:106` `projector.project()` | docstring `:114` "incremental (a session is skipped when its transcript digest is unchanged) and idempotent"; no payload | YES |
| `integrate` | `scheduler/cron.py:126` `integrator.integrate()` | docstring `:136` "incremental … and idempotent"; no payload | YES |
| `dream` | `scheduler/cron.py:50` `dreamer.dream()` | model-driven synthesis; each pass MINTS new claims into the run ledger. No idempotence claimed anywhere | NO |
| `curate` | `scheduler/cron.py:58` `curator.curate()` | model-driven; emits findings per pass. No idempotence claimed | NO |
| `shadow` | `scheduler/cron.py:82` `runner.run()` | returns two FRESH ledger run ids per call (`core/stores/runledger.py:136` mints a uuid) — provably not idempotent | NO |
| `research` | `scheduler/cron.py:147` | payload-bearing (`criteria`, `conversation`, `topic`); drives the airlock. Not idempotent | NO |
| `ambassador_task` | `scheduler/interface.py:53` | payload-bearing (`query`, `conversation`); a model answer per call | NO |
| `ambassador` | `scheduler/interface.py:45` `inbox.process_once()` | `core/interface.py:57` drains ALL pending and consumes each file, so a re-run IS safe — but it is the REACTIVE conversational front door and was never part of the observed stacking. Excluded **conservatively**: exclusion can only cost one extra no-op row, inclusion could reshape front-door latency | NO (deliberate) |
| anything else (incl. test kinds `x`,`y`,`k`,`ping`,`librarian`) | — | unknown | NO (default) |

Nothing here was guessed: every YES cites a docstring that asserts idempotence in the handler's own
module. The one judgement call is `ambassador`, recorded above as deliberately conservative.

### Layering note (DRY)

`_IDEMPOTENT_KINDS` holds the kind names as string LITERALS in `scheduler/queue.py`, not imports of
`CHAT_SYNC_KIND` / `CODE_SYNC_KIND` / … — those modules import `scheduler.queue`, so importing them
back would be a cycle. The duplication is made structural instead of conventional by
`tests/unit/test_queue_coalescing.py::test_idempotent_kind_literals_match_the_kind_constants`, which
imports both sides and asserts equality. If a kind constant is ever renamed, that test fails.

## Item 1 — `claimed_by_run` + idempotent migration — DONE

`scheduler/queue.py`: `claimed_by_run INTEGER` added to `_DDL` (fresh files) **and** to
`_MIGRATIONS` (existing files), applied by `_migrate()` from `__post_init__`. `_migrate` reads
`PRAGMA table_info(jobs)` and issues only the missing `ALTER TABLE … ADD COLUMN` — no UPDATE, no
DROP, no rewrite, so it is idempotent by construction. `Job` gained the field (defaulted `None`,
so every existing constructor call still type-checks); `claim()` now stamps
`claimed_by_run = self.active_run_id`, which is `None` for every caller that does not set it.
Also added `CREATE INDEX IF NOT EXISTS jobs_coalesce ON jobs (state, kind, id)` for the coalescing
lookup.

### DRY-RUN AGAINST A COPY OF THE LIVE FILE — the Item 1 gate, PASSED

Script: `<scratch>/dryrun_migration.py`. It `cp`s `/Users/ascalva/mind-palace/data/queue.sqlite`
(+`-wal`/`-shm`) to scratch and only ever opens the COPY. The live file was never opened by this
build; the daemon stayed down throughout.

| | BEFORE | AFTER open #1 | AFTER open #2 |
|---|---|---|---|
| total rows | 302,010 | 302,010 | 302,010 |
| states | done 300,242 / failed 1 / queued 1,766 / running 1 | identical | identical |
| queued kinds | vault_sync 882, chat_sync 882, dream 1, curate 1 | identical | identical |
| running rows | `{id 300246, code_sync, started 2026-07-25T03:45:07}` | identical | identical |
| id range | 1 … 302,010 | identical | identical |
| sha256 of every row's `(id, state, created_at)` | `1ddc2c9c…9ad3d4` | **same** | **same** |
| columns | 14 | 15 (`+claimed_by_run`) | 15 |
| indexes | `jobs_ready` | `jobs_coalesce`, `jobs_ready` | identical |

All seven falsifier checks PASS, including "every pre-existing row has `claimed_by_run` NULL".
**The falsifier did not fire: no pre-existing row's `id`, `state` or `created_at` changed.**

Two things the dry-run settled that reading alone could not:

1. The live duplicate count is **882 + 882 + dream + curate = 1,766** (finding-0170 records
   883/883; it was counting slightly later or including the running row). Numbers now measured.
2. **finding-0170's suggested partial UNIQUE index cannot be created.** `CREATE UNIQUE INDEX …
   ON jobs (kind, payload) WHERE state='queued'` would raise on open against a file holding 882
   identical `chat_sync` rows — i.e. it would make the daemon *unstartable*. Coalescing is
   therefore enforced in `enqueue`, with the structural index deferred until the restart clears
   the duplicates. Recorded as a comment beside `_MIGRATIONS` so the next reader does not re-try it.

Tests: `tests/unit/test_queue_migration.py` (6) — builds a file with the verbatim PRE-CHANGE DDL,
opens it with current code, compares the same `(id, state, created_at)` digest; plus
open-three-times idempotence, fresh-file DDL path, the stamp/no-stamp split, and old-writer /
new-reader interoperation.

## Item 2 — `sweep_orphans` — DONE

`JobQueue.sweep_orphans(active_run_id) -> OrphanSweep`, sitting beside `revive_deferred` and
following its UPDATE-over-a-state-class shape (split in two only because the two kind classes land
in different states). Idempotent kinds → `QUEUED` with `started_at`/`claimed_by_run` cleared;
everything else → `FAILED` via the existing `self.fail()` with
`error = "orphaned by unclean exit of run #N"` (`#?` when the owning run predates the column).
`created_at` and `attempts` are deliberately untouched: aging is measured from the former (Q3) and
the dead run really did consume the latter.

The safety argument (in the docstring, because it is the whole point):

1. Run ids are `AUTOINCREMENT` (`ops/lifecycle/runs.py:28`), so a freshly-opened run's id cannot
   already be on any row.
2. The guard is **positive**: reclaim only when `claimed_by_run != active_run_id`. A row this run
   claimed carries the stamp and is never touched. A NULL stamp is reclaimable precisely because
   no live run can have written one.

The sweep also ADOPTS `active_run_id` into the handle, so every later `claim()` stamps. That is
what makes the guard real rather than nominal, and it keeps the wiring to one line.

**Falsifier tested and NOT fired:** `test_a_job_the_live_run_is_never_reclaimed` puts a live-run-
owned `code_sync` RUNNING row beside a dead-run-owned `code_sync` RUNNING row (same kind, so kind
cannot mask the bug) and asserts only the dead one moves. 8 tests in
`tests/unit/test_queue_orphan_sweep.py`, including the job-300246 acceptance fixture, terminal
rows never examined, sweep-twice idempotence, and age preservation.

## Item 3 — enqueue coalescing — DONE

`enqueue` gained a pre-INSERT lookup for kinds in `_IDEMPOTENT_KINDS`: the oldest matching QUEUED
row (`ORDER BY id LIMIT 1`) is returned instead of inserting. Contract preserved — it still returns
a `Job`, so `launcher.code_backfill`'s `job.id` print keeps working.

Three decisions worth carrying:

- **Match key = `(kind, payload)` plus `tier` and `num_ctx`.** The plan pins `(kind, payload)`;
  adding tier/num_ctx is a strictly NARROWER key, so it can only ever create a row, never drop
  one. Routing is deterministic per kind today so it never fires — it is there so a future
  re-route cannot fold a job into a row planned for a different model load. `payload IS ?` (not
  `=`) so NULL matches NULL.
- **Only QUEUED rows collapse.** RUNNING/DONE/FAILED/DEFERRED never absorb a request — the
  falsifier case (a `code_backfill` requested while one is running) is tested directly.
- **First row wins, and a collapse may PROMOTE but never demote.** Keeping the first row preserves
  aging (Q3); if the incoming request is more urgent than the waiting row, the waiting row's
  `priority` is improved (its `created_at` still stands), so a collapse cannot silently downgrade
  urgency. This is the one behaviour beyond the plan's letter; it is strictly in the direction of
  "never lose work".

Payload matching is on the stored JSON text, so key-order-different dicts do not collapse — errs
toward an extra row, never a lost job. Noted in the docstring.

9 tests in `tests/unit/test_queue_coalescing.py`, including the 1,000-enqueue acceptance test
(→ exactly 1 row) and the literals-match-constants structural check.

## Reconciliation (§4) — done

- `enqueue` docstring: coalescing contract + which kinds collapse, citing finding-0170 (extension).
- `claim` docstring: a startup sweep now precedes claiming, so `running` rows are trustworthy —
  and explicitly, that this is only true if `sweep_orphans` was called (extension).
- Module header `:2-5`: rewritten as the WHOLE state machine (forward edges + all three return
  edges + terminality), not just the new one — see the pre-existing error noted above (correction).
- Module docstring: a paragraph naming both hygiene properties and pointing at `_IDEMPOTENT_KINDS`.

## Green gate

Run separately, never `&&`-chained. Results verbatim in the seal report.

- `uv run ruff check .` → `All checks passed!`
- `uv run mypy core agents eval ops scheduler scripts` → `Success: no issues found in 255 source files`
- `uv run mypy` → `Found 69 errors in 20 files (checked 537 source files)` — **baseline 69 held**
- `uv run python -m ops.type_gate` → both checks OK
- `uv run pytest -q --deselect tests/unit/test_core_self_containment.py::test_core_imports_nothing_outside_core`
  → `1958 passed, 15 skipped, 1 deselected in 1446.00s (0:24:05)` — **green, no regressions**
  (the 24-minute wall clock is contention: bp-100/bp-102 builders were running the suite in
  parallel worktrees on the same machine)

Targeted first: the three new files alone = `23 passed in 17.02s`.

## Commits (worktree branch `worktree-agent-ae5e897949632a574`)

- `e292446` `feat(scheduler): make the job queue bounded and self-healing (bp-101)` —
  `scheduler/queue.py` + the three test files. Deliberately ONE commit, not three: items 2 and 3
  both require item 1's column, so per-item commits could not stand alone, and they share one file
  and one classification table. The body enumerates the three parts.
- Journal + finding-0177 follow as a docs commit (no Co-Authored-By, per the trailer policy).

## Findings filed

- **finding-0177** — the orphan sweep is built but has no caller; the two-line wiring owed in
  `ops/lifecycle/launcher.py` (widen `QueueLike`, call `sweep_orphans(run.id)` after
  `components_factory` and before `enqueue_catchup`), spelled out as a diff for bp-102. Filed
  because `launcher.py` is deliberately out of write_scope and the switch must not be lost.
  (Id chosen as the next free number; bp-100/bp-102 builders run in parallel worktrees, so the
  orchestrator may need to renumber on merge.)

## Progress

- [x] Grounding + classification
- [x] Item 1 — `claimed_by_run` column + idempotent migration (dry-run PASSED against a copy)
- [x] Item 2 — `sweep_orphans` (falsifier tested, did not fire)
- [x] Item 3 — enqueue coalescing (falsifier tested, did not fire)
- [x] Hand-off finding (finding-0177)
- [x] Green gate — all five legs run SEPARATELY, all pass
- [x] Commits

## Post-build verification: the live queue file is provably untouched

Checked read-only (`file:…?mode=ro`) after all work and all five gate legs:

- schema is still the **14-column pre-change** shape — `claimed_by_run` is NOT there, i.e. the
  migration has never run against the live file;
- state histogram `done 300242 / failed 1 / queued 1766 / running 1` — unchanged;
- sha256 over every row's `(id, state, created_at)` = `1ddc2c9c…9ad3d4`, **identical to the
  dry-run's BEFORE digest**;
- `queue.sqlite` mtime still `Jul 25 00:07`, `-wal` still 0 bytes.

Job 300246 is still sitting in `running`, as it should be — it is reclaimed by the wiring in
finding-0177, not by this build.

## What a fresh agent needs to know to continue

1. **Nothing in bp-101 is outstanding except the wiring in finding-0177**, which is out of this
   plan's write_scope by design. The three items are complete, tested, and green.
2. The live queue is **untouched**. The daemon must stay DOWN; nothing here started it. The 1,766
   duplicates and job 300246 are still on disk — clearing them is a RESTART step (plan §9), and
   job 300246 will be reclaimed automatically the moment finding-0177's wiring lands.
3. **Do not add the partial UNIQUE index** finding-0170 suggests until those duplicates are gone;
   it would make `palace up` fail. See the comment beside `_MIGRATIONS`.
4. If a new job kind is added, decide its `_IDEMPOTENT_KINDS` membership from its HANDLER, not from
   convenience; unknown ⇒ leave it out. `tests/unit/test_queue_coalescing.py::
   test_idempotent_kind_literals_match_the_kind_constants` will fail if a kind constant is renamed
   without updating the literal.
5. Not addressed and not in scope: finding-0165 (background starvation / long-job slicing) and
   finding-0171 (job budgets, owner decision pending). The lease/heartbeat alternative to run-id
   ownership stays parked per plan §11 — it catches a HUNG worker, which run-id ownership does not.
