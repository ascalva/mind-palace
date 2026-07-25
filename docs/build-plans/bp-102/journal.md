---
type: journal
plan: bp-102
started: 2026-07-25
---

# Journal — bp-102: status tells the truth

## Session 1 (2026-07-25) — grounding

Worktree: `.claude/worktrees/agent-a577c8c239ead29da`, branch `main` (worktree-local).
Daemon is DELIBERATELY DOWN. Nothing in this session starts it; every probe below is read-only
(`file:…?mode=ro` URIs and metadata-only store reads).

### Context read (§2 manifest, in order)

`ops/lifecycle/launcher.py` (whole), `ops/lifecycle/snapshot.py`, finding-0172, finding-0171,
`docs/brainstorms/command-center.md`, `scheduler/queue.py` (read-only), `config/defaults.toml`.
Plus, for grounding: `core/ops_view.py`, `ops/lifecycle/runs.py`, `ops/lifecycle/preflight.py`,
`core/stores/vectorstore.py`, `core/typedshims/lancedb.py`, `scheduler/supervisor.py`,
`core/models/ollama_client.py`, `ops/code_lineage.py`.

### Q4 — RESOLVED, and the answer kills the config half

**There is no job-level timeout anywhere in the system.** Greps of `scheduler/`, `ops/`, `config/`
and the code-ingest path find no per-job deadline, no `signal.alarm`, no wall-clock budget:

- `scheduler/supervisor.py:63 tick()` calls `handler(job)` synchronously with no bound.
- The only enforced timeouts are socket-level, in `[ollama]`: `request_timeout_s = 120`
  (control plane + `embed`) and `generation_timeout_s = 600` (chat).

The observed failure, read out of the live queue (read-only):

```
300240 | code_backfill | failed | started 2026-07-25T02:30:12 | finished 2026-07-25T03:45:02
       | TimeoutError('timed out')
```

`TimeoutError('timed out')` is `socket.timeout` — raised from `urllib`'s socket read, which is
**not** a `URLError` subclass, so it escapes `OllamaClient._post`'s `except urllib.error.URLError`
un-wrapped and propagates to `Supervisor.tick`'s blanket `except Exception → queue.fail(repr(e))`.

⇒ The 4,490 s (74 m 50 s) was **total job elapsed, not a budget**. The job died because ONE embed
call exceeded `request_timeout_s = 120`. The triage's "~75-minute job timeout" was an inference from
the elapsed time; no such mechanism exists.

**Consequence for Item 3:** adding a `job_timeout_s` knob to `config/defaults.toml` would be exactly
the "second, unwired constant" the falsifier forbids — nothing would read it, because enforcing a
job budget is oq-0035 / finding-0171(b), an explicitly out-of-scope owner decision. Per §10
stop-and-raise: **config half DROPPED, `config/defaults.toml` unchanged, finding filed**
(finding-0175), honest-reporting half kept. The "budget fraction" of §8 is therefore reported as
elapsed with an explicit "no enforced job budget" — the honest instrument, not a fabricated ratio.

Also NOT added: a `[status]` window knob. `core/config/loader.py` is schema'd and drops unknown
sections and is outside this write_scope, so such a key would be inert — same defect. `W` is a
documented module constant (`snapshot.STATUS_WINDOW_MINUTES = 20.0`, §11 default), exposed as the
injectable `Launcher.status_window_minutes` field.

NB finding numbering: `finding-0174` was already taken (the memory-ceiling/embedder-accounting
finding, filed by the orchestrator this same session), so this plan's findings are **0175** and
**0176**. bp-100/bp-101 are building in parallel worktrees and cannot see these files — a number
collision at merge is possible and is the orchestrator's to reconcile.

### Q6 / the Item-2 falsifier — measured, not asserted

Cost probes against the REAL production stores (read-only), before writing any code:

Measured against the REAL production stores, final shipped shape:

| read | cost (repeated runs) | queries | rows materialized |
|---|---|---|---|
| `read_queue_stats` over the 302,010-row `jobs` table | 63.6 / 64.3 / 66.5 ms | 7 | **13** |
| `read_store_stats` → `VectorStore.count()`, 22,621 rows | 1.2 / 1.5 / 3.6 ms | — | 0 (metadata) |

⇒ **≈ 68 ms and 13 rows added to `status`, independent of table size.** Full `status()` against the
real data dir measures ~1.35 s wall clock, of which the overwhelming majority is the pre-existing
preflight (Ollama probe + Constitution fingerprint + vault glob).

**Two figures the plan asked for are NOT reported, each for a MEASURED reason:**

1. *Distinct code versions embedded* and the `current=true/false` split. `VectorStore`'s only cheap
   read is `count()`; `all_rows`/`rows_for_source`/`relabel_provenance` all do a full
   `to_arrow().to_pylist()`, materializing `vector` — the finding-0169 shape. The metadata-only
   reader needs `count_rows(filter=…)` on `core/typedshims/lancedb.py` + a method on
   `core/stores/vectorstore.py`, **both outside this write_scope**.
2. *The ledger target* (`COUNT(DISTINCT path, blob_sha)` over `code_snapshots.sqlite`). This was
   implemented, then **removed after measurement**: an early probe with the system python read
   188 ms, but under `uv run` it measures **3.42 / 3.48 / 3.61 / 3.64 s**, consistently. The plan:
   `SCAN files` + `USE TEMP B-TREE FOR DISTINCT` over 423,855 rows of a 2.3 GB table (rows carry a
   `docstring` column); `files` is `PRIMARY KEY (commit_sha, path)`, so nothing indexes the pair.
   That is a full scan, and Item 2's falsifier disqualifies it. **The lesson: measure with the real
   runner against the real store — the first number was wrong by 20×.**

Both are finding-0176. `status` prints the vector row count and states plainly that code-version
coverage has no metadata-only reader, rather than showing an expensive or fabricated figure.

Side discovery recorded in finding-0176: that same 3.5 s `DISTINCT` is already paid on the DAEMON
STARTUP path — `launcher._code_backfill_incomplete` → `ops/code_lineage.py:ledger_versions` — where
nobody has measured it.

### DRY audit

- `_pid_alive` (`launcher.py:93`) is the ONE liveness primitive. `snapshot.run_state()` takes it as
  an **injected** callable — no second implementation, and no launcher→snapshot import cycle.
- `core/ops_view.py` has **no** activity-rate reader (only counts + `recent_actions`); telemetry
  records only `queue.depth` / `model.load_seconds`, and only *after a job finishes* — so during a
  wedge the series is silent. Rates therefore come from the `jobs` table directly, as §2.6 pins.
- `JobQueue` exposes no windowed/aggregate reads and `scheduler/queue.py` is bp-101's (DENIED), so
  `snapshot.read_queue_stats()` opens its own `mode=ro` connection against the schema the plan
  pins at `scheduler/queue.py:62+`. Hand-off noted in finding-0176 (these belong on `JobQueue`).
- `sweep_orphans` (§11) does **not** exist in this tree — bp-101 has not merged. Wiring deferred;
  it stays a one-line addition at the merge.

## Session 1 — Item 1 + Item 2 + Item 3 landed

Commits on the worktree branch (see `git log`):

1. `feat(snapshot): liveness, rate/budget and failure readers for status` —
   `ops/lifecycle/snapshot.py`.
2. `feat(launcher): status reports liveness, rates, failures; honest down/stop` —
   `ops/lifecycle/launcher.py`.
3. `test(lifecycle): incident-fixture oracle + cost bounds for the status block` — unit tests.

### What landed

**`ops/lifecycle/snapshot.py`** (all additions pure or read-only):
- `STATUS_WINDOW_MINUTES = 20.0` — W (§11 default; justification below).
- `run_state(run, *, pid_alive)` — pure; `RUNNING` / `DEAD (stale ledger row)` / `clean` /
  `UNCLEAN` / `none`, returns `(state, alive|None)`.
- `read_queue_stats(path, *, now, window_minutes, max_kinds)` → `QueueStats` with
  `RunningJob` / `QueuedKind` / `JobFailure` records, `in_rate_per_min` / `out_rate_per_min` /
  `net_rate_per_min`, and the anomaly predicates `stalled` / `wedged` / `failure_in_window`.
  Carries `rows_read` and `queries` so the cost bound is testable. Missing db ⇒ empty stats,
  never creates the file.
- `read_store_stats(*, vector_store)` → `StoreStats(vector_rows)`; ONE field, deliberately —
  see the measurement above and finding-0176.
- `humanize_seconds` — `4490.0` → `1h14m50s`; rounding a budget away is how a 74-minute job reads
  as fine.
- `build_status(...)` extended with keyword-only `liveness` / `queue_stats` / `store_stats` /
  `embedder`; still pure, still JSON-serializable, existing callers unchanged.

**A predicate that had to be re-derived, not assumed.** `stalled` was first written as
`depth > 0 and (done + failed) == 0`. The oracle caught it: at the *exact* instant the owner
sampled the incident (03:45:07) a job had failed five seconds earlier, so that definition would
have gone QUIET at precisely the moment it needed to fire. It is now keyed on **completions**
(`done_in_window == 0`); `out_rate` still counts both, because both leave the queue and it must
stay an honest d(depth)/dt term. Same for `wedged`.

**One flag added beyond the plan's list**, because the real render demanded it: a RUNNING job row
with no live daemon is marked `⚠ ORPHANED` (finding-0173's orphan). Without it, run #35's dead
`code_sync` row shows an ever-growing "elapsed 2h41m" that reads as work in progress — the same
false-green shape as the RUNNING banner, one level down. Guarded against false alarm by
`test_a_running_row_under_a_LIVE_daemon_is_not_called_orphaned`.

**`ops/lifecycle/launcher.py`**:
- `status()` renders per-run liveness and refuses to print `running HEAD` for a dead pid — it
  prints the stale-ledger warning instead.
- `_report_snapshot()` renders the rate/budget/failure/store/embedder block; opens nothing that
  does not already exist (no lance dir creation, no `queue.sqlite` creation) — status is now
  strictly read-only, where before it CREATED `queue.sqlite` via `JobQueue(...)`.
- `stop()` checks liveness first, then reports what it *sent*, not what it achieved.
- `down()` observes for `stop_verify_s` (default 5 s) and returns 1 + a STILL-ALIVE line naming
  pid/run/elapsed when the process outlives the bootout. `restart()` refuses to `up` in that case
  (double-instance guard). **No SIGKILL, no escalation, no job-budget enforcement.**

### W = 20 min, justified (§11)

The 0.5 s chat debounce bursts ~2 enqueues/min; 1 min of that window is noise. 1 h would have
read "normal" for most of the incident (the wedge began at 02:30 and `status` was consulted from
~03:00). 20 min is ≥ 40× the debounce and < ¼ of the incident, and at the moment of the owner's
03:45 check it reads 0 done / 1 failed against 1,714 queued — unmistakably anomalous.

### Acceptance oracle (§6) — every row rendered anomalous

`tests/unit/test_status_incident_oracle.py` builds a queue fixture reproducing the incident and
asserts, row by row:

| §6 ground truth | rendered |
|---|---|
| depth 1714, ~2/min in, zero drain | `in 2.0/min · out 0.1/min · net +2.0/min` + `⚠ ZERO DRAIN (0 completed)` |
| `code_backfill running`, budget spent | `running: #… elapsed 1h14m55s (no enforced job budget)` + `⚠` |
| lifetime unchanged ⇒ zero throughput | `throughput: 0 done, 1 failed in the last 20 min` + `⚠` |
| (absent) 1 job failed 15 min earlier | `last failure: #300240 code_backfill 5s ago — TimeoutError('timed out')` + `⚠` |
| `running HEAD` while the process was dead | `DEAD (stale ledger row)` + no `running HEAD` line + `⚠ ORPHANED` |

The fixture is generated RELATIVE to an anchor, so the same rows drive both the fixed-clock unit
assertions and the end-to-end `status` render against the wall clock — **no clock is stubbed** in
the end-to-end path, which is what makes it a real render rather than a mock of one.

**Verified against the live incident, read-only** (the daemon stayed down; ledger/queue opened
`mode=ro`). `status` over the real `data/` now prints:

```
  #35 5c2222924874 started 2026-07-25T02:29:11 — DEAD (stale ledger row) (pid 96950)
⚠ run #35 is marked active in the run ledger but pid 96950 is NOT alive — the daemon is DOWN …
  queue depth: 1766   (in 0.0/min · out 0.0/min · net +0.0/min over 20 min)  ⚠ ZERO DRAIN (0 completed)
  throughput: 0 done, 0 failed in the last 20 min  ⚠ nothing completed
  running: #300246 code_sync — elapsed 2h41m50s (no enforced job budget)  ⚠ ORPHANED — no live daemon owns this row
  waiting: curate 1, oldest 3h56m50s · … · chat_sync 882, oldest 3h56m45s · vault_sync 882, …
  last failure: #300240 code_backfill 2h41m55s ago — TimeoutError('timed out')
  lifetime: 300242 done · 1 failed · 1766 queued · 1 running
  store: 22,621 vector rows (code-version coverage has no metadata-only reader — not shown)
  embedder: qwen3-embedding:4b NOT resident
```

Before this plan the same state printed `RUNNING`, `running HEAD (5c2222924874)`, and
`queue depth: 1766` with six green checkmarks.

### Cost bound (Item 2 falsifier) — asserted mechanically

`tests/unit/test_status_cost_bound.py`:
- a 10,000-row and a 100-row `jobs` table produce the **same** `queries` (7) and the same
  `rows_read` (≤ 24) — a cost that does not move with the table cannot be a scan;
- every SQL statement actually executed is captured and asserted to (a) never `SELECT *`, (b) never
  project `payload`/`result`/`checkpoint` (the unbounded columns), and (c) be either an aggregate
  or `LIMIT`-ed. Asserted on the executed SQL, not on source text;
- a spy `VectorStore` proves `count()` is called at most once and `all_rows` / `rows_for_source` /
  `search` / `to_arrow` **zero** times;
- `StoreStats` is pinned to exactly one field, so re-adding an expensive figure has to be a
  deliberate edit to that contract rather than a quiet extra line in the renderer;
- `read_queue_stats` never creates a missing db, and its `mode=ro` connection refuses writes.

### False-alarm falsifier (Item 1) — tested both directions

`tests/unit/test_lifecycle_liveness.py`: a live pid (`os.getpid()`) renders `RUNNING` and prints
`running HEAD`; a pid that is alive but owned by another user (`PermissionError` from
`os.kill(pid, 0)`) still renders `RUNNING` — `_pid_alive` returns True there, which matters for the
`ouroboros` system-daemon principal (dn-plane-principals). Only `ProcessLookupError` ⇒ dead.

Known residual (documented, not fixed here): **pid reuse** would read a recycled pid as alive — a
false GREEN, not a false alarm, and no worse than today's unconditional `RUNNING`.

### Item 3 falsifier — inverted, honestly

The plan's falsifier was "the knob exists but nothing reads it — prove wiring by changing the value
and observing behavior change." Since the knob was dropped, the equivalent proof was applied to the
thing that DID land: `stop_verify_s` is a real `Launcher` field, and the shutdown tests drive it
at 0.5 s and 5.0 s and observe the two different outcomes (STILL ALIVE vs verified-exited) against
a real subprocess. Nothing decorative was added.

`tests/unit/test_lifecycle_honest_shutdown.py` uses a live child that **ignores SIGTERM** as the
wedged daemon. `test_down_does_not_escalate` records every `os.kill` with a non-zero signal during
`down()` and asserts the list is EMPTY — the no-escalation invariant is proven, not just promised.

Test artefact worth knowing: an unreaped child of the test process lingers as a ZOMBIE, and
`os.kill(zombie, 0)` succeeds — so `_pid_alive` (correctly) still says alive. The tests spawn a
reaper thread to reproduce launchd's reaping. The system is unaffected; the daemon's parent is
launchd.

### Findings filed

- `docs/findings/finding-0175.md` — Q4: no job-level timeout exists; the ~4,490 s was elapsed, and
  the real bound is a per-CALL `[ollama] request_timeout_s` socket timeout that also escapes
  `OllamaError` (because `socket.timeout` is not a `URLError`). Routes to the orchestrator: it
  re-frames finding-0171's option (b) from "tune a mechanism" to "build one", and carries two
  builder-resolvable pieces that do not prejudge the owner's answer.
- `docs/findings/finding-0176.md` — three hand-offs, all outside this write_scope: metadata-only
  vector-store readers (bp-100's lane), an index on `files(path, blob_sha)` (which also costs the
  daemon 3.5 s on every start), and windowed aggregate reads on `JobQueue` (bp-101's lane).

### Not done, deliberately

- `config/defaults.toml` — untouched (Q4; see above). **The plan's write_scope entry for it is
  unused.**
- `sweep_orphans` wiring — bp-101 unmerged; `scheduler/queue.py` in this tree has no such method.
  Stays the one-line addition at the merge (§11).
- Tier 2 (TUI), any new command, alerting, macro-axis metrics — §9 non-goals. Nothing here
  refreshes, acts, or notifies.

### Green gate (each leg run separately)

```
uv run ruff check .                                → All checks passed!
uv run mypy core agents eval ops scheduler scripts → Success: no issues found in 255 source files
uv run mypy                                        → Found 69 errors in 20 files   (== baseline)
uv run python -m ops.type_gate                     → Tier-2 membership: OK / Bare-ignore scan: OK
uv run python scripts/check_imports.py             → Import firewall (I2): OK
uv run pytest -q                                   → (see below)
```

### Fresh-agent re-entry

Everything in this plan is landed and committed on the worktree branch. If a successor picks this
up: the only open items are the three hand-offs in finding-0176 and the `sweep_orphans` wiring,
none of which is bp-102's to do. Do NOT start the daemon.
