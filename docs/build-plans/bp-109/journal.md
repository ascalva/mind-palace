---
type: journal
plan: bp-109
started: 2026-07-26
updated: 2026-07-26
---

# Journal — bp-109 (the queue's ledger stops being trusted)

Newest entry first.

---

## SEAL — 2026-07-26 · all five items closed, gates green, two findings filed

**Status.** All five items are built and every named falsifier has been planted and observed to
redden. `jobs` carries a nullable `lease_expires_at`; `claim()` — proven by an AST ratchet to be the
queue's only RUNNING constructor — stamps it; `snapshot.py` derives orphanhood from it with no sweep
having run; a checkpointed row is no longer a collapse target (V6) and no longer carries a deadline
to lapse. The sweep's reclaim predicate is **unchanged**: a lapsed lease on a row this run owns is
reported, never reclaimed. Committed on `worktree-agent-a0dc706a1105eb7d8`, base `c78bca1`. NOT
pushed; plan NOT flipped to `complete` (both owner-side).

### Completed — per criterion, with evidence

**Item 1 — the additive column.** `_DDL:117` + one tuple appended to `_MIGRATIONS:145`; `_migrate`
untouched (the existing mechanism is reused, no second migration path).
- *Acceptance:* `test_queue_leases.py::test_opening_a_pre_change_file_adds_the_column_and_changes_no_row`
  builds a file with the verbatim pre-change DDL, digests **every pre-change column of every row**
  (not just the three bp-101 named), and asserts the digest is identical after the migration, plus
  `(id, state, created_at, attempts)` per row explicitly. `…is_a_no_op_on_every_later_open` opens
  three times. `…fresh_file_gets_the_column_from_the_ddl_not_the_migration` compares the DDL path
  against the ALTER path as column *sets* (the two produce different ordinals).
- *Falsifier (any pre-existing row differs) — ⚑ exercised on the REAL file:* dry-run against a
  **copy** of `/Users/ascalva/mind-palace/data/queue.sqlite` (62 MB, 302,010 rows). Copied first
  (`cp`), never opened for write in place; the original's mtime and column set are unchanged after
  the run (only `-shm` was touched, by a read-only `sqlite3` open — no db bytes).

  ```
  BEFORE rows=302010 counts={'done': 300242, 'failed': 1, 'queued': 1766, 'running': 1}
  BEFORE digest=5172deb6cb07d9dd044a463305c468e6732d62c1e1aedbeb000d01b4f9aae38c
  AFTER  rows=302010 counts={'done': 300242, 'failed': 1, 'queued': 1766, 'running': 1}
  AFTER  digest=5172deb6cb07d9dd044a463305c468e6732d62c1e1aedbeb000d01b4f9aae38c
  AFTER  columns=[… 'claimed_by_run', 'lease_expires_at']   # both ADDED, nothing else moved
  AFTER  lease NULL=302010 NOT-NULL=0
  AFTER  running=[(300246, 'code_sync', 'running', '2026-07-25T03:45:07', None, None)]
  STATUS orphaned_running=()        # ⚑ the live orphan is NOT reinterpreted by the migration
  DRY RUN: OK — history untouched, additive only
  ```

  Note the live file did not even have `claimed_by_run` yet (its daemon has not restarted since
  bp-101), so this dry-run exercised **both** migrations in sequence — the harder case.
- *Invariants:* additive-only ✓; `_MIGRATIONS` remains the single path ✓; the partial UNIQUE index
  is **not** created and the paragraph explaining why is preserved verbatim (`queue.py:137-141`) ✓.

**Item 2 — `claim()` stamps the deadline.** `queue.py:433-441`. `lease_expires_at = started_at +
job_budgets[kind]`, computed off the **same single clock read** as `started_at`, so
`deadline − started_at == budget` exactly (the test asserts that rather than a tolerance around
`datetime.now()`). NULL when the kind has no budget — which is every kind, because `job_budgets`
(`queue.py:296`) defaults empty.
- *Acceptance:* `test_claim_stamps_the_deadline_from_the_configured_budget` (exact 900 s delta +
  round-trip through `_row_to_job` on a fresh read),
  `test_a_kind_with_no_configured_budget_is_claimed_with_a_null_deadline`,
  `test_the_default_queue_stamps_no_deadline_at_all`.
- *Falsifier (a RUNNING row minted after this item with a NULL deadline where a budget exists):*
  MUT-5 below, plus `test_every_running_row_minted_under_an_interleaving_carries_a_deadline`
  (300 seeded ops, invariant re-checked over every row after **every** op).
- *Invariants:* the selection policy is byte-for-byte unchanged — the stamp is written after
  `chosen` is decided, and `test_the_selection_policy_is_unchanged_by_the_stamp` claims the same
  three jobs in the same order from a budgeted and an unbudgeted queue ✓. Nothing is *enforced*
  here ✓.

⚑ **No number was invented.** No budget is configured anywhere; the default is the empty mapping ⇒
NULL ⇒ today's behaviour. §11's parked row (re-entry: bp-112 lands escalation) and §3 Q7 forbid a
guess, and there is nothing to calibrate against (finding-0178). See finding-0225 for the enable
path. The only numeric constant added anywhere in production code is none.

**Item 3 — readers derive orphanhood instead of trusting `state`.**
- `queue.py:174` `deadline_lapsed(deadline, now)` — the ONE implementation of the polarity, imported
  by `snapshot.py:47` rather than re-derived, because two copies of "NULL ⇒ not expired" are two
  chances to invert it. `queue.py:221` `lease_expired(job, now)` = `state == RUNNING ∧ lapsed`:
  RUNNING stays *necessary*, stops being *sufficient*, and the state guard is structural insurance
  so a leftover deadline on a non-RUNNING row cannot manufacture an orphan.
- `snapshot.py:251` `QueueStats.orphaned_running` + `RunningJob.lease_expired` (`:158`).
- *Acceptance:* `test_an_elapsed_deadline_reads_as_orphaned_with_no_sweep_having_run` — **no
  `sweep_orphans` call appears in that test at all**, which is the inversion. Plus
  `test_a_deadline_still_in_the_future_is_not_orphaned`,
  `test_a_null_deadline_running_row_behaves_exactly_as_today`, and the sweep's run-id path still
  reclaiming independently (all 8 pre-existing sweep tests pass unedited).
- *Falsifier (deleting the sweep call leaves the suite green):* MUT-1 below, applied to the callee
  because `launcher.py` is out of scope. 13 tests redden.
- *Invariants:* `Supervisor.tick`'s RUNNING check untouched ✓ (never edited `supervisor.py`).
  An expired row is *reported*, never deleted ✓. The bp-102 ORPHANED render keeps working ✓ — and see
  the judgement call below for why no predicate was re-keyed.

⚑ **Judgement call, recorded because it is a deliberate omission.** `wedged` / `stalled` /
`embedding` were left alone (`snapshot.py:251`'s docstring carries the reason). Every way of folding
orphanhood into them makes an existing flag **quieter** — excluding an orphan from `wedged`'s
`running` test, or from `youngest_running_elapsed_s`'s min, both let a state that flags today go
unflagged — and the render that would carry the orphan reason instead (`launcher.py:1271-1285`,
keyed on daemon liveness) is out of this plan's write_scope. Trading one loud imprecise flag for one
silent precise one is a false green: the failure this track exists to remove. So `orphaned_running`
is strictly NEW information and the sharpening waits for the render (bp-111 owns it).

**Item 4 — V6: a checkpointed row is not a collapse target.** One clause, `queue.py:359`, plus the
fourth property in `enqueue`'s docstring (`:343`), written as a **correction** per §4.
- *Acceptance:* `test_queue_coalescing.py::test_a_checkpointed_row_is_not_a_collapse_target` (:170) —
  a new row is returned, the checkpointed row keeps its cursor, its state AND its priority, and depth
  goes to 2; `…two_checkpointed_rows_do_not_collapse_onto_each_other` shows the exclusion holds for N
  resumes while the fresh row is still a target itself. **All 10 pre-existing coalescing tests pass
  unedited.**
- *Falsifier (the checkpointed row is returned):* MUT-4 below.
- *Invariants:* the fix can only CREATE a row ✓ (`AND checkpoint IS NULL` strictly narrows the
  lookup); first-row-wins, `created_at` preservation and priority promotion all still asserted by
  their original tests ✓.

**Item 5 — the ratchet the tier-4 claim rests on.** `test_queue_leases.py:488` `running_writers()`
parses `scheduler/queue.py`, walks the WHOLE module (`ast.walk`, so nested defs are included),
resolves each hit to its innermost enclosing function via a parent map, and flags a call as a RUNNING
constructor iff its SQL writes the `state` column **anywhere in the SET clause** (regex, not a prefix
match) AND the call binds `RUNNING` (constant or literal).
- *Acceptance:* `test_claim_is_the_only_constructor_of_a_running_row` → `== {"claim"}`. Part (b) is
  `test_every_running_row_minted_under_an_interleaving_carries_a_deadline`.
- *Falsifier (a second writer leaves the ratchet green):* planted **five ways**, all permanently
  asserted by `test_the_ratchet_reddens_on_a_planted_second_writer` — a plain second method, `state`
  in **second position** in the SET clause, a **function-local** writer inside a nested helper (the
  bp-106 Item 4 hole, and the invariant §7 Item 5 names), the raw `"running"` literal, and an INSERT
  that mints RUNNING outright. Plus MUT-6 against the real file.
  `test_the_ratchet_does_not_fire_on_a_reader_or_on_another_state` pins the other direction so the
  ratchet is not the kind that fires on everything and gets deleted.

**The lease's liveness rule** (not a numbered item; the property that makes the title's second half
true). *A lease lives exactly as long as the claim that minted it.* `claim` sets it; `checkpoint`
(`:557`), `defer` (`:459`), `revive_deferred` and the sweep's requeue (`:535`) all clear it. So **no
QUEUED or DEFERRED row ever carries a deadline** —
`test_no_waiting_or_deferred_row_ever_carries_a_deadline` walks all four edges and then scans every
row. Terminal rows keep theirs as the historical bound of the claim (inert: `lease_expired` requires
RUNNING). This is what makes a checkpointed row stop being an orphan, and it also buys the property
§2.10 demands: because each re-claim re-stamps, a **yielding** lane's deadline is per-BATCH, not
per-job-elapsed (`test_a_re_claim_after_a_checkpoint_gets_a_fresh_deadline`).

### ⚑ The stop-and-raise I did not take, and why

`sweep_orphans`'s reclaim predicate is **byte-for-byte unchanged**: `state = RUNNING AND
(claimed_by_run IS NULL OR claimed_by_run != ?)`. §4 says the deadline is "a second, independent
reason a row is **reclaimable**" and §3 Q5 lists the sweep's SELECT among what Item 3 changes; §9 says
"no enforcement of the deadline" and §7 Item 3 says an expired row is "*reported* orphaned, never
silently deleted". Those cannot all hold: the only rows a deadline could *add* to the sweep's
population are rows stamped by the live run — and a lapsed lease is not evidence the holder is dead
(a hung-but-alive worker has exactly that shape), so reclaiming them is the double-execution
falsifier finding-0173/0186 fence. I built the reading every invariant supports — the stamp is an
absolute **veto** — and changed the sweep's SELECT in the only way that is safe: it now reads every
RUNNING row so the same pass can **report** what it must not touch (`OrphanSweep.lease_expired`,
rendered "reported, NOT reclaimed"; `total` still counts only what MOVED, so the existing
`OrphanSweep(...)` equality assertions pass unedited). Filed **finding-0224** for the design ruling.
Three new tests fence the widening and MUT-7 proves they bite.

### Planted mutations — every one reddens

| # | mutation | result |
|---|---|---|
| MUT-1 | the sweep call does nothing (`JobQueue.sweep_orphans → OrphanSweep()`, patched at runtime) | **13 failed** across `test_restart_trustworthy` + `test_queue_orphan_sweep` + `test_queue_leases` |
| MUT-2 | `deadline_lapsed` always False — the derived reader inert | **7 failed** |
| MUT-3 | ⚑ `deadline is None → True` — the mass-orphan polarity inversion | **6 failed**, incl. the legacy-row test |
| MUT-4 | `AND checkpoint IS NULL` removed | **2 failed** |
| MUT-5 | `claim` stamps no deadline | **4 failed** |
| MUT-6 | a **function-local** second `state = RUNNING` writer, `state` second in the SET clause | **1 failed** — `assert {'_mut6', 'claim'} == {'claim'}` |
| MUT-7 | ⚑ the reclaim predicate widened by the deadline (the §4-literal reading) | **3 failed** — the three new sweep-safety tests |

MUT-1 was applied to the **callee at runtime**, not by editing `ops/lifecycle/launcher.py:748`: that
file is out of write_scope and a concurrent builder (bp-106) owns it. Neutering `sweep_orphans` is
observationally identical to deleting the call (no reclaim, no adoption) and required no repo edit.
MUT-2..7 are edits to in-scope files, applied and reverted one at a time; `grep -n "MUT-"` over the
tree is empty and the diff is clean.

### Gate — every leg, exact numbers

| leg | result |
|---|---|
| `uv run ruff check .` | **All checks passed** (one E501 found and fixed first) |
| `uv run python scripts/check_imports.py` | **OK** — core imports no zone/networking module |
| `uv run mypy core agents eval ops scheduler scripts` | **0 errors**, 258 source files |
| `uv run mypy` | **exactly 69 errors** in 20 files, 551 source files (baseline held) |
| `uv run python -m ops.type_gate` | **OK** — Tier-2 membership OK, bare-ignore scan OK |
| `uv run pytest -q -m 'not live…' --deselect …` | **2132 passed, 11 skipped, 21 deselected, 0 failed** |

Queue-test counts specifically: `test_queue_leases.py` **25 (new file)** ·
`test_queue_orphan_sweep.py` **11** (8 → 11, +3) · `test_queue_coalescing.py` **12** (10 → 12, +2) ·
`test_queue_migration.py` **5** (unchanged, unedited) · `test_restart_trustworthy.py` **37**
(unchanged, unedited — bp-108's sweep-vs-claim ORDERING assertions all pass:
`test_start_sweeps_a_stranded_row_against_a_real_queue`,
`test_the_swept_row_is_reclaimed_before_it_can_be_claimed_by_this_run`,
`test_the_lock_is_held_before_the_sweep_and_released_after_shutdown`).

Config: the worktree has neither `config/local.toml` nor `config/ouroboros.toml`; `load_config()`
returns cleanly — **no `ConfigMigrationError`**, nothing to work around.

### In-flight

Nothing. Every item closed; the tree is clean apart from the commit.

### Next action

Owner-side only: review the diff, then flip `bp-109` `in-progress → complete` and push. The plan is
**ready to deskcheck** — the observable is `palace status` over a queue whose daemon has restarted
since this landed (RUNNING rows will still show no deadline until a budget is configured, which is
finding-0225's hand-off, so the honest deskcheck is the dry-run evidence above plus
`OrphanSweep.render()`'s new clause).

### Open questions

- **finding-0224** (`spec-fidelity` → orchestrator) — §4's "reclaimable" vs §9's "no enforcement".
  Built the safe reading, fenced the other with three tests. Not blocking; re-entry is bp-112's
  graduation, which must state whether the live-run veto is permanent (a) or conditional on an
  independent liveness fact (b) that the queue's schema cannot currently supply.
- **finding-0225** (`question` → builder) — `job_budgets` is the enable path and nothing fills it: no
  `[scheduler]` config section exists and `config/**` + `launcher.py` are out of write_scope.
  Built-but-unwired, deliberately: the *value* is §11-parked on bp-112, and wiring a path to a value
  nobody may set yet would ship an inert knob (bp-102's dropped job-timeout knob, finding-0174).
- Ids 0224 **and** 0225 were both taken this session; a concurrent builder may also have been told
  "next free id: 0224" — worth a look at seal.

### Context-manifest delta

Read beyond the §2 manifest, all load-bearing:
- `tests/unit/test_status_cost_bound.py` — **decided a design point.** Its
  `test_every_queue_statement_is_bounded` requires every statement `read_queue_stats` issues to be an
  aggregate or carry a `LIMIT`, which **rules out a `PRAGMA table_info` probe** for the new column.
  Hence the `try/except sqlite3.OperationalError` fallback at `snapshot.py:362`, with the legacy
  projection *derived* from the new one (`.replace`) so the two cannot drift. Its `MAX_ROWS_READ = 24`
  and the no-`payload`/`result`/`checkpoint` projection rule also constrain the added column; both
  re-asserted in `test_the_status_read_stays_bounded_and_read_only_over_the_new_column`.
- `tests/unit/test_status_incident_oracle.py`, `tests/unit/test_restart_trustworthy.py:509` — both
  build **legacy-shaped** queue files (no lease column) and call `read_queue_stats`, which is what
  makes that fallback load-bearing for the *existing* suite, not only for the live file.
- `tests/unit/test_queue_migration.py` — not in write_scope and not edited; its pre-change DDL is the
  model for the new file's `_PRE_CHANGE_DDL` (which differs: it includes `claimed_by_run`).
- `scheduler/supervisor.py:63-107` — read ONLY, to confirm §3 Q5 (`tick`'s RUNNING check must not
  move) and that `defer` is called on an already-RUNNING row (it is — the ceiling path), which is why
  `defer` clears the lease. Not edited.
- `ops/lifecycle/launcher.py:77-95,748,1271-1297` — read ONLY, to confirm (a) `SweepLike` needs just
  `.render()` so the new `OrphanSweep` field breaks nothing, and (b) the ORPHANED render keys on
  daemon liveness, which is what makes quieting a predicate a regression. **Not edited.**
- `ops/import_lint.py` — checked that `ops → scheduler` is permitted (the firewall constrains `core/`
  only) before importing `deadline_lapsed` into `snapshot.py`; `edge/` reads the JSON snapshot, not
  the module, so no zone is widened.

Proved irrelevant: `scripts/palace.py` reads only state counts, so the new column does not reach it.

### Read map

```read-map
docs/findings/finding-0224.md:1: the §4-vs-§9 ambiguity — the sweep's reclaim set was NOT widened, and why
docs/findings/finding-0225.md:1: the ON switch stops at job_budgets — the hand-off, not a defect
scheduler/queue.py:129: the _MIGRATIONS comment — ⚑ NULL means "no deadline", never "expired"
scheduler/queue.py:174: deadline_lapsed — the ONE polarity rule, imported not re-derived
scheduler/queue.py:221: lease_expired — RUNNING is necessary, no longer sufficient
scheduler/queue.py:433: claim stamps the deadline off the same clock read as started_at
scheduler/queue.py:493: the sweep's extended argument — the live-run stamp is an absolute VETO
scheduler/queue.py:519: the reclaim predicate, unchanged; the lapsed set is REPORTED beside it
scheduler/queue.py:549: checkpoint clears the lease — why a checkpointed row stops being an orphan
scheduler/queue.py:343: enqueue's fourth property, written as a correction (V6)
ops/lifecycle/snapshot.py:251: orphaned_running — and why no anomaly predicate was re-keyed
ops/lifecycle/snapshot.py:362: the read-only fallback for a pre-migration file (a PRAGMA is barred)
tests/unit/test_queue_orphan_sweep.py:167: the falsifier that matters — a live worker's checkpointed row
tests/unit/test_queue_orphan_sweep.py:209: a lapsed deadline moves no row across the reclaim line
tests/unit/test_queue_leases.py:180: ⚑ the polarity falsifier — 302k legacy rows must not mass-orphan
tests/unit/test_queue_leases.py:329: orphaned with NO sweep having run — the inversion itself
tests/unit/test_queue_leases.py:488: running_writers — the tier-4 AST ratchet
tests/unit/test_queue_leases.py:560: the ratchet's own falsifier, five planted writers
tests/unit/test_queue_coalescing.py:170: V6's falsifier — the checkpointed row must not be returned
```

+30 tests across three files (25 new in `test_queue_leases.py`, +3 sweep, +2 coalescing); 9 worth
reading, listed above. Mechanical coverage counted, not listed.

## Follow-through
- **Built?** Yes, all five items. `lease_expires_at` on `jobs` (additive, dry-run-verified against a
  copy of the real 302,010-row file), stamped by `claim()` (the sole RUNNING constructor, now proven
  by an AST ratchet rather than asserted), derived as orphanhood by `snapshot.py` with no sweep having
  run, cleared on every edge that ends a claim, and V6's one-clause coalesce correction. The sweep's
  reclaim set is deliberately unchanged.
- **Wired / delivered (or why dormant)?** Partly, and the split is honest. **Wired and live now:** the
  migration (runs on every open), the derived reader (`status` computes it today), the lease clearing,
  V6's fix, and `OrphanSweep.lease_expired` — which reaches a real render, since the launcher already
  prints `sweep.render()` at start. **Dormant by design:** the deadline *values*. `job_budgets` is
  empty and no config key reaches it, so every claim stamps NULL and the system behaves exactly as
  before. That is §11's parked default (re-entry: bp-112), not an oversight — §3 Q7 forbids inventing
  a number and nothing exists to calibrate against. The missing config path is **finding-0225**, filed
  rather than silently left.
- **Does a consumer use it?** Yes for three of the four surfaces: `read_queue_stats` (hence `status`)
  consumes `lease_expires_at`; the launcher's start banner consumes the sweep's new clause via
  `render()`; `enqueue` consumes the V6 clause on every idempotent enqueue.
  `QueueStats.orphaned_running` has **no render consumer yet** — deliberately, because every way of
  wiring it into an existing anomaly flag makes that flag quieter, and the render is bp-111's
  write_scope (reason recorded at `snapshot.py:251`).
- **Track state (what remains on this track)?** `dn-supervision-and-liveness` §2.6 named three small
  independent pieces: the supervisor lock and the `run(max_ticks=K)` drain landed in bp-108; **leased
  RUNNING rows is this plan** — so all three of the note's independent pieces are now in. Remaining on
  the note: the compute/land worker split (§2.5, lane-by-lane, longest lane first), the supervisor
  **lease** (§2.6's second mechanism — needs the split's unblocked loop, and V9's measured ttl), and
  bounded escalation (§2.10 (a) / bp-112, which is also where the deadline stops being decorative).
  V6 is now discharged, which was the gate blocking any batch-yield protocol — **bp-110 is
  unblocked**. V1–V5 and V7–V9 remain open.
- **Opened a new track/finding?** Two findings, no new track. **finding-0224** (spec-fidelity →
  orchestrator): §4 calls the lease a reason a row is *reclaimable* while §9 forbids enforcing it;
  built the safe reading, fenced the widening with three tests + MUT-7, and the design must rule on
  whether the live-run veto is permanent before bp-112 acts on a deadline. **finding-0225** (question
  → builder): the enable path for `job_budgets` needs a schema'd `[scheduler]` section, which is
  outside this write_scope; recorded so the next plan reuses the field instead of adding a second
  budget source.

---

## Checkpoint 4 — 2026-07-26 · all seven mutations planted, all redden

Table kept in the seal above. MUT-1 needed the runtime-patch route because `launcher.py` is out of
write_scope and bp-106 is editing it concurrently; MUT-2..7 were in-scope edits, applied and reverted
one at a time, and `grep "MUT-"` over the tree is now empty.

## Checkpoint 3 — 2026-07-26 · Items 4 + 5 closed

V6's clause is one narrowing conjunct (`AND checkpoint IS NULL`) and all 10 pre-existing coalescing
tests pass unedited. The Item 5 ratchet resolves each `state = RUNNING` write to its innermost
enclosing function, so a nested-helper writer is caught — the hole bp-106 Item 4 records. The first
draft of `test_two_checkpointed_rows_do_not_collapse_onto_each_other` was wrong (it assumed `claim()`
would pick the row just enqueued, but a checkpointed row returns to QUEUED and wins on FIFO);
rewritten to assert the exclusion directly, which is a tighter statement of the same property.

## Checkpoint 2 — 2026-07-26 · Items 1–3 closed; the dry-run is the load-bearing evidence

The dry-run against a copy of the live file is in the seal. Two things it settled that reading could
not: the live file lacks `claimed_by_run` too (so both migrations ran, and the digest still matched),
and job 300246 comes through with a NULL deadline and does **not** read as lease-orphaned — the
polarity falsifier, checked on the real data rather than on a fixture.

Design point forced by an out-of-scope test: `read_queue_stats` may not issue a `PRAGMA` (every
statement must be an aggregate or carry a `LIMIT`, per
`test_status_cost_bound.py::test_every_queue_statement_is_bounded`), so tolerating a pre-migration
file is a `try/except OperationalError` with the legacy projection derived from the new one. That
fallback is load-bearing for the *existing* suite, not only for the live file: two out-of-scope test
modules build legacy-shaped queue files and call this reader.

## Checkpoint 1 — 2026-07-26 · manifest read, base confirmed, the ambiguity found before writing code

Base `c78bca1` (= `origin/main`), branch `worktree-agent-a0dc706a1105eb7d8`, `uv sync --frozen --extra
dev` done. bp-108's lock + bounded drain are present in the tree and were built on, not
reimplemented.

Read the §2 manifest in order. §3's Q1 (claim is the only RUNNING constructor) and Q2 (the
checkpoint/coalescing collision) were both re-verified by reading before any edit: `queue.py`'s only
`state = RUNNING` write was in `claim`, and the coalesce key genuinely did not mention `checkpoint`.

The one thing reading changed: §4's "a second, independent reason a row is **reclaimable**" cannot be
implemented literally without making a live run's own row reclaimable on a lapsed lease, which is the
double-execution falsifier and is forbidden by §9. Resolved conservatively (veto preserved, lapse
reported) and filed as finding-0224 rather than choosing silently — see the seal.

---

# Pre-build notes (minted 2026-07-25 by `/graduate`, retained verbatim)

Minted 2026-07-25 (session-48) by `/graduate`, decomposing both ratified ops notes
(`dn-supervision-and-liveness` and `dn-local-model-runtime`) in one context.

- ⚑ **V6 needed no measurement — it is confirmed by reading.** `checkpoint()` leaves the token on
  a QUEUED row (`queue.py:400-402`) and the coalesce lookup never mentions the `checkpoint` column
  (`queue.py:262-264`). Item 4 is a one-clause fix and it BLOCKS bp-110.
  → **Confirmed and fixed.** `queue.py:359`.
- ⚑ **NULL means "no deadline", and every pre-existing row gets NULL.** A reader that treats NULL
  as expired mass-orphans 300k+ rows of history at migration time. This is the single most
  dangerous mistake available in this plan (§6).
  → **Held, and proven on the real data.** One implementation (`deadline_lapsed`), imported by both
  readers; MUT-3 inverts it and reddens 6 tests; the dry-run shows 302,010 NULLs and zero orphans.
- **Do NOT add the partial UNIQUE index.** `queue.py:122-126` explains why: the live file holds
  1,766 duplicate queued rows and `CREATE UNIQUE INDEX` would make the daemon unstartable.
  → **Not added.** The paragraph is preserved verbatim at `queue.py:137-141`; the dry-run re-confirms
  1,766 queued rows are still there.
- **Item 3 and Item 5 both require a PLANTED MUTATION to prove they work.** finding-0187's standing
  proof is that deleting bp-105's sweep call left 85/85 green. If your mutation does not redden the
  suite, you have shipped a guard whose absence is invisible — worse than shipping nothing.
  → **Seven planted, all redden.** See the seal's table; Item 5's five are permanent parametrized
  tests, not a one-off.

## Owed at seal (orchestrator, not the builder)

Findings referenced in §4 Reconciliation are cross-referenced, never edited — a builder may not
edit an existing finding. Record closure evidence here for the orchestrator to apply at seal.

- **finding-0187** (already `resolved` by bp-105) — this plan's warrant. Its ratchet still holds:
  `test_restart_trustworthy.py` drives `Launcher.start()` against a real `JobQueue` and all 37 tests
  pass unedited, and MUT-1 (the sweep neutered) reddens 13 tests. No flip needed; noted as intact.
- **finding-0173** (already `resolved`) — its "a lease/heartbeat column would be stronger still, and
  it pairs naturally with finding-0171's job-budget enforcement; consider designing them together"
  tail is what this plan builds. The column exists; the *enforcement* half is still open and is now
  tracked by finding-0225 (the enable path) and finding-0224 (what enforcement may do).
- **finding-0170** — the partial UNIQUE index remains uncreated and the reason is unchanged (1,766
  duplicate queued rows on the live file, re-measured this session). Still parked, §11 row 4.

## Markers
