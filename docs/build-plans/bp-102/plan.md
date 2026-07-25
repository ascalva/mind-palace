---
type: build-plan
id: bp-102
track: workflow
status: proposed
design_ref:
  - docs/design-notes/temporal-code-corpus.md
contract: builder
write_scope:
  - ops/lifecycle/launcher.py
  - ops/lifecycle/snapshot.py
  - config/defaults.toml
  - tests/unit/test_lifecycle*.py
  - tests/unit/test_status*.py
  - tests/unit/test_snapshot*.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 140k
  actual: null
depends_on: []
parallelizable_with:
  - bp-100
  - bp-101
created: 2026-07-25
updated: 2026-07-25
links:
  - docs/findings/finding-0172.md
  - docs/findings/finding-0171.md
  - docs/findings/finding-0169.md
  - docs/brainstorms/command-center.md
re_entry: null
supersedes: null
superseded_by: null
warrant: docs/findings/finding-0172.md
---

# Build Plan — bp-102: status tells the truth — liveness, failures, and rates (command center, Tier 1)

## 0. Mode & provenance

Corrective plan warranted by **finding-0172** (status reported a dead daemon as `RUNNING` and hid a
failed job) with the builder-resolvable half of **finding-0171** (`down` claimed success while the
process lived). This is **Tier 1 only** of the owner's command-center vision
(`docs/brainstorms/command-center.md`) — the rate/budget block on the existing `status` command. The
real-time TUI is Tier 2 and goes through capture → design note → adversarial panel → graduate; it is
explicitly NOT built here. Authority-to-act is the owner's instruction to plan tonight's build;
`proposed → ready` remains owner-only.

**Why this is worth doing before the restart:** it is the instrument that verifies bp-100. Without a
throughput and rate readout there is no way to tell a healthy backfill from tonight's wedged one.

## 1. Objective

Make `palace status` incapable of reporting a healthy system while it is failing — by adding a
liveness check, a failure surface, and the rate/budget quantities that every symptom of the
2026-07-25 incident actually lived in.

## 2. Context manifest

1. `ops/lifecycle/launcher.py` — whole file, but especially `status` (`:798`), `_report_snapshot`
   (`:826+`), `deploy` (`:591`) and its `_pid_alive(run.pid)` check (`:605`), `stop` (`:668`),
   `down`, and `_code_backfill_incomplete` (`:231`).
2. `ops/lifecycle/snapshot.py` — `build_status(...)`, the payload `_report_snapshot` renders.
   Every new datum should enter through this seam, not be printed ad hoc.
3. `docs/findings/finding-0172.md` — the two defects and the level-vs-derivative table.
4. `docs/findings/finding-0171.md` — the unbounded drain; **only** the honest-reporting half is in
   scope here.
5. `docs/brainstorms/command-center.md` — Tier 1 / Tier 2 split; build Tier 1 exactly.
6. `scheduler/queue.py` — read-only. `depth` (`:261`) and the `jobs` schema (`:62+`) are the source
   for throughput/rate queries. **Do not edit** (bp-101 owns it).
7. `config/defaults.toml` — where the job-timeout knob belongs (finding-0169 Q6: it was NOT
   locatable during triage).

**DRY audit — does this already exist?** `_pid_alive` exists and is used by `deploy`
(`ops/lifecycle/launcher.py:605`) — **reuse it; do not write a second liveness check.**
`build_status` (`ops/lifecycle/snapshot.py`) is the existing snapshot seam and already carries
`queue_depth`, health, patterns, activity — extend it rather than printing beside it. Before adding
any rate computation, check whether `core/ops_view.py` already exposes an activity-rate reader; the
ledger view feeds `activity` today.

## 3. Investigation & grounding

- **Q1 — Why did status print `RUNNING` for a dead pid?** `status` (`:798`) renders
  `"RUNNING" if r.active else …` (`:807`) straight from the run ledger, with no liveness test.
  `deploy` does test (`_pid_alive(run.pid)`, `:605`). The primitive exists; the reporting path
  simply does not call it.
- **Q2 — Where would failures surface?** `_report_snapshot` renders `build_status(...)`, which is
  passed `queue_depth=queue.depth()` (`:845`) — depth only. The queue's own `lifetime … failed`
  counter is printed by `palace queue`, not by `status`. **Nothing in the status path reads failure
  state at all.**
- **Q3 — Can throughput be computed cheaply?** Yes: `jobs` carries `finished_at` and `state`
  (`scheduler/queue.py:62+`), so "completed in the last N minutes" is one indexed COUNT. This was
  the single most diagnostic number available during the incident and existed nowhere.
- **Q4 — Where is the job timeout configured?** **Code does not settle this.** Greps of
  `config/defaults.toml` and `scheduler/` did not find it; the observed value was ~4,490 s
  (`code_backfill` job 300240 died at 74m50s). The builder MUST locate the actual mechanism before
  adding a knob — adding a second, unwired timeout constant would be worse than none.
- **Q5 — What does `down` currently return?** It reports success on the launchd bootout, before the
  process has exited. Observed 2026-07-25: `down` printed its success line while pid 96950 kept
  running at 96% CPU and `launchctl print` showed `active count = 1` pending. The escalation POLICY
  is an owner decision (finding-0171); **honest reporting is not** and is in scope.
- **Q6 — Does adding store reads to status risk repeating finding-0169?** Yes, directly. A status
  block that full-scans `vectors.lance` on every invocation is the same mistake one level up. Any
  store-derived figure must be metadata-only and must never materialize the `vector` column.

**Additional risks surfaced:** `status` must remain safe to run while the daemon is DOWN (it is the
first thing anyone runs after an incident) and must never enqueue work or mutate state.

## 4. Reconciliation

- `ops/lifecycle/launcher.py:807` — `state = ("RUNNING" if r.active else …)` → **banner:
  correction.** Liveness must be checked; a ledger-active run whose pid is dead renders as
  `RUNNING?` / `DEAD (stale ledger row)`, never plain `RUNNING`.
- `ops/lifecycle/launcher.py` `down`/`stop` success strings → **banner: correction.** They must not
  assert a state they have not observed. Report what was requested and what was verified, and say
  plainly when the process is still alive.
- `_report_snapshot` docstring ("queue depth, health/RAM headroom, drift, dream + tidy-suggestion
  counts, action activity") → **cross-ref: extension** for the new rate/budget/failure fields.

## 5. Write scope

- `ops/lifecycle/launcher.py` — status rendering, liveness, honest `down`/`stop` reporting; and the
  supervisor-start call to bp-101's `sweep_orphans` if that plan has merged (see §12).
- `ops/lifecycle/snapshot.py` — the `build_status` payload extension.
- `config/defaults.toml` — the job-timeout knob (Q4), if and only if the mechanism is located.
- Matching tests.

Deliberately OUT of scope: `scheduler/queue.py` (bp-101), `core/stores/**` (bp-100), any TUI
framework or new command (Tier 2), and the escalation policy for finding-0171.

## 6. Interfaces pinned inline

```python
def status(self) -> int:                                        # ops/lifecycle/launcher.py:798
    print("preflight:"); print(self.preflight_fn(self.cfg).render())
    runs = self.runs.recent(5)
    ...
    for r in runs:
        state = ("RUNNING" if r.active else ("clean" if r.clean_shutdown else "UNCLEAN"))
        rec = " [recovery]" if r.recovery else ""
        print(f"  #{r.id} {r.commit_sha[:12]}{' (dirty)' if r.dirty else ''} "
              f"started {r.started_at} — {state}{rec}")
    live = self.runs.last()
    ...
    self._report_snapshot(live)
    return 0
```

The liveness primitive to REUSE (from `deploy`, `:605`):

```python
if run is None or not run.active or not _pid_alive(run.pid):
```

The snapshot seam (`_report_snapshot`, `:845`):

```python
data = build_status(ops_view=ops_view, dreams_view=dreams_view, queue_depth=depth,
                    run=run, mem_available_gb=mem_gb)
```

Queue states available for rate queries (`scheduler/queue.py:39`, read-only here):

```python
QUEUED, RUNNING, DONE, FAILED, DEFERRED = "queued", "running", "done", "failed", "deferred"
```

**The incident's ground truth, as the acceptance oracle** — status must have made these visible:

| shown then | true then |
|---|---|
| `queue depth: 1714` | growing ~2/min, **zero drain** |
| `code_backfill running` | **74 of 75** min of budget spent |
| `lifetime: 300,239 done` | unchanged for an hour ⇒ **zero throughput** |
| (absent) | 1 job failed 15 min earlier |
| `running HEAD` | **the process was dead** |

## 7. Items

Blast-radius order: read-only truthfulness → read-only derived metrics → config.

### Item 1 — Liveness and failure truth

- **Objective:** `status` never reports `RUNNING` for a dead pid, and always surfaces failure state.
- **Files:** `ops/lifecycle/launcher.py`, `ops/lifecycle/snapshot.py`, tests.
- **Acceptance test:** With a ledger row marked active whose pid does not exist, `status` renders a
  dead/stale state and a non-zero exit-worthy warning; with a failed job in the last N, status
  prints count + last failure kind/error/time.
- **Falsifier:** A genuinely live daemon is reported as dead — a false alarm is as corrosive to
  trust as the false green. Test against a live-pid fixture.
- **Invariants:** `status` remains read-only, safe with the daemon down, and enqueues nothing.
- **Touches stored data?** No — reads only.
- **Parallelizable?** No (gates Item 2). **Depends on:** none.

### Item 2 — The rate/budget block

- **Objective:** Status reports derivatives, not just levels: jobs completed in the last N minutes;
  queue in-rate vs out-rate; per-kind oldest age; running job elapsed vs its timeout budget; code
  versions embedded vs ledger target; `current=true/false` split; embedder-active indicator.
- **Files:** `ops/lifecycle/snapshot.py` (payload), `ops/lifecycle/launcher.py` (render), tests.
- **Acceptance test:** A fixture reproducing the incident state (1,700 queued, 3 done in 20 min, one
  running job at 98% of budget, a failed job) renders every row of §6's ground-truth table with a
  visibly anomalous reading.
- **Falsifier:** Running `status` costs more than a small constant — e.g. it full-scans
  `vectors.lance` or materializes the `vector` column (Q6). Assert an upper bound on rows/columns
  read; a status command that repeats finding-0169 one level up has failed even if every number is
  right.
- **Invariants:** No store mutation; no work enqueued; must not require the daemon to be up.
- **Touches stored data?** No.
- **Parallelizable?** No. **Depends on:** Item 1.

### Item 3 — Honest `down`/`stop`, and the job-timeout knob

- **Objective:** `down`/`stop` report only what they verified; the job timeout is a named,
  documented config value.
- **Files:** `ops/lifecycle/launcher.py`, `config/defaults.toml`, tests.
- **Acceptance test:** With a process that ignores SIGTERM, `down` reports that the process is STILL
  ALIVE and names it (pid, elapsed), rather than printing an unqualified success line. The timeout
  knob appears in `defaults.toml` with a comment and is read by the mechanism located in Q4.
- **Falsifier:** The knob is added but nothing reads it — a second, decorative constant beside the
  real one. Prove the wiring by changing the value and observing the behavior change.
- **Invariants:** No escalation/SIGKILL behavior is added — that is the owner's pending decision
  (finding-0171). This item changes REPORTING only.
- **Touches stored data?** No.
- **Parallelizable?** Yes (independent of Items 1–2). **Depends on:** none.

## 8. Math carried explicitly

- **Throughput** — *measures:* terminal job transitions per unit time (`count(state ∈ {done,failed})
  with finished_at > now − W`). *valid when:* the queue is the sole execution path and `finished_at`
  is written on every terminal transition. *fails its keep if:* it reads non-zero while the worker
  is provably wedged — i.e. it fails to distinguish tonight's state from a healthy one.
- **Queue net rate** — *measures:* `d(depth)/dt` as in-rate minus out-rate over window `W`.
  *valid when:* `W` is long enough to smooth burst enqueues (debounce is 0.5 s) and short enough to
  react within an incident. *fails its keep if:* the chosen `W` renders tonight's sustained
  +2/min-with-zero-drain as unremarkable.
- **Budget fraction** — *measures:* running job elapsed ÷ its timeout. *valid when:* the timeout is
  the actual enforced one (Q4). *fails its keep if:* it cannot be computed because no knob is
  wired — in which case Item 3 has not really landed.

## 9. Non-goals

- **Not** the Tier-2 TUI, any new command, or a refresh loop. Tier 1 enriches the existing `status`.
- **Not** the finding-0171 escalation policy (SIGTERM→SIGKILL, job budgets) — owner decision pending.
- **Not** alerting, notification, or anything that acts. Status observes; it never intervenes.
- **Not** the macro-axis metrics from the capture (causal density, drift ladder, Zipf/n(v)) — those
  need the Tier-2 design pass.
- **Not** edits to `scheduler/queue.py` or `core/stores/**`.

## 10. Stop-and-raise conditions

- Q4 cannot be resolved (the timeout mechanism is not locatable) → do NOT invent a knob; drop Item 3's
  config half, file a finding, keep the honest-reporting half.
- Any new status figure requires a full store scan and cannot be made metadata-only → STOP; adding a
  finding-0169-shaped cost to the diagnostic tool is disqualifying.
- The false-alarm falsifier (Item 1) fires → STOP; an instrument that cries wolf will be ignored
  during the next incident, which is exactly when it must be believed.
- Any temptation to build Tier 2 because "it's nearly the same code" → STOP; Tier 2 is gated.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| Window `W` for rates | Builder picks; default 20 min, justified in the journal | 1 min (too noisy against a 0.5 s debounce); 1 h (would have read "normal" for most of tonight) | Tier-2 design pass makes `W` configurable per panel |
| Anomaly rendering | Plain flagged lines (`⚠`) beside each figure | Colour/TUI affordances — Tier 2 territory | Tier-2 design note ratified |
| Where the orphan sweep is wired | Wire bp-101's `sweep_orphans` at supervisor start IF bp-101 merged first; else leave the hand-off finding open | Wiring a method that does not exist yet (breaks the tree) | bp-101 merged — then this is a one-line addition here |
| Exit code on unhealthy | Keep `return 0` (status is a report, not a check) | Non-zero on anomaly — would break any script treating status as a liveness probe | An explicit `palace check` is designed |

## 12. Dependency & ordering summary

Within the plan: **Item 1 → Item 2**; **Item 3 is independent** and may go first if the builder
prefers to resolve Q4 early.

Across plans: no hard dependency; `parallelizable_with` bp-100 and bp-101 (disjoint write scopes —
`ops/**` + `config/**` here). **Soft ordering:** if bp-101 merges first, this plan also wires
`sweep_orphans` at supervisor start (§11) — otherwise that wiring stays an open finding for the
merge. Recommended real-world sequence: bp-100 (unblocks) → bp-101 + bp-102 → restart checklist →
`palace up` with this plan's rate block as the instrument that verifies bp-100's fix.
