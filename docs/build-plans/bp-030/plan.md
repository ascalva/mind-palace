---
type: build-plan
id: bp-030
status: complete
design_ref:
  - docs/brainstorms/lifecycle-cli-overhaul.md
contract: builder
write_scope:
  - scripts/palace.py
  - ops/lifecycle/launcher.py
  - config/loader.py
  - config/defaults.toml
  - edge/monitor/**
  - scripts/monitor.py
  - tests/integration/test_lifecycle.py
  - tests/integration/test_lifecycle_control.py
  - tests/integration/test_status_report.py
  - tests/unit/test_monitor_server.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 300k
  actual:
    model: opus            # self-driven, high effort, single-lane (0 subagents on the bp-030 portion;
                           # the session's one Explore subagent was for the later bp-035 graduation)
    tokens: ~95k           # bp-030 build share (est). Whole-session non-cache = ~161k (20.1k in +
                           # 140.8k out, + 18.7m cache read / 457.4k cache write). The session bundled
                           # bp-030 (all 3 items + 2 full pytest runs + verification) then the bp-035
                           # graduation + reference research (~65k incl. the 54k Explore) — bp-030 ≈ 60%.
    ratio: ~0.32           # ~95k / 300k — well UNDER estimate: read-heavy, cache-warm, no delegation,
                           # the monitor removal was a clean deletion (grep-confirmed, no surprises).
    dollars: ~10           # of the $17.36 whole-session total (opus $17.35 + haiku $0.0006); bp-030 ≈ 60%
    session_delta: "session meter 14% used (resets 12:10am ET); bp-030 the bulk of it"
    week_delta: "85% -> 86% (+1pp) over the whole session; bp-030 share ~+0.6pp; resets Jul 17 8pm ET"
    # Credits UNCHANGED at 89% ($89.59/$100) — the session was weekly/subscription-covered, NOT billed
    # to credits (same pattern as bp-034/bp-036). Binding meter is the WEEKLY (86%). Fable now 100% capped.
depends_on: []
parallelizable_with: []
created: 2026-07-13
updated: 2026-07-14
completed: 2026-07-14
links:
  - docs/brainstorms/lifecycle-cli-overhaul.md
  - docs/findings/finding-0066.md
  - ops/lifecycle/com.mind-palace.palace.plist
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — the lifecycle CLI: control + dead-dashboard removal + richer status

> **Every section below is required.** Inapplicable sections are marked `N/A — <reason>`.

## 0. Mode & provenance

Authored directly from `docs/brainstorms/lifecycle-cli-overhaul.md` (2026-07-13) + finding-0066 —
concrete ops/infra, no ratified design note / fable-vet needed. The DIAGNOSTIC subcommand is a
SEPARATE plan (bp-031, fully scoped in the brainstorm); this plan is the operational-control +
cleanup + status unit. `proposed → ready` is owner-only, by hand.

**Invariant-adjacent (opus/high, scrutinized).** `ops/lifecycle/launcher.py` is the seal/supervisor
boundary; the monitor removal deletes Zone-B (`edge/`) code. Nothing here loosens an invariant — it
removes a dormant network-facing component and adds read-only control/reporting.

## 1. Objective

Three things: (1) add **KeepAlive-aware `down`/`up`/`restart`** so "maintenance down" ≠ "operational
stop" (finding-0066); (2) **remove the dead edge-monitor/dashboard** (never worked; owner will redo
it from scratch later) — cleanly, preserving the status-snapshot data it fed; (3) **enrich `status`**
to surface real system state by reusing that snapshot.

## 2. Context manifest

Read whole, in order:

1. `scripts/palace.py` — the CLI dispatch (`{start|stop|status|reset|deploy}` → `build_launcher()`); `seal()` (Inv 1) runs first. New subcommands mount here.
2. `ops/lifecycle/launcher.py` — `Launcher` (`.start/.stop/.status/.reset/.deploy`); the monitor child spawn (`:238-244`, guarded by `cfg.monitor.enabled`), the snapshot write (`:225,234` — `build_status`/`write_status`), the plist-install check (`:445`).
3. `ops/lifecycle/com.mind-palace.palace.plist` — `KeepAlive=true`, `RunAtLoad=true`, LaunchAgent `gui/$uid`, `bootout`/`bootstrap` commands in its header comment (the exact incantations `down`/`up` wrap).
4. `ops/lifecycle/snapshot.py` — `build_status(*, ops_view, dreams_view, queue_depth, run, …) -> dict` + `write_status(path, data)`. **`build_status` already assembles the rich status dict** — Item 3 reuses it. **KEPT** (repurposed), not deleted.
5. `ops/lifecycle/children.py` + `tests/unit/test_children.py` — the child-supervision primitive. **The monitor is its ONLY caller** (`launcher.py:242`). After the monitor is removed it is caller-less; **KEEP it dormant + tested** (the future dashboard redo re-uses it — avoid churn). Do NOT delete.
6. `config/loader.py` (`MonitorConfig`, `Config.monitor`) + `config/defaults.toml` `[monitor]` — removed with the monitor.
7. `edge/monitor/{server,page,__init__}.py` + `scripts/monitor.py` — the dashboard code + its launcher entry. Deleted.
8. `tests/integration/test_lifecycle.py` — the existing lifecycle test home; extend it (or the two new files) for the new commands.

## 3. Investigation & grounding

- **Q1 — Why isn't `stop` enough for maintenance?** Under `KeepAlive=true`, launchd restarts the process after any exit — so `palace stop` (SIGTERM drain) is immediately relaunched. A true "down" must `launchctl bootout gui/$uid/com.mind-palace.palace`; "up" is `bootstrap`. The plist header documents both. The code settles this (the plist + the KeepAlive semantics).
- **Q2 — Is the monitor wired live?** `[monitor] enabled=false` (`defaults.toml`); the launcher only spawns it inside `if cfg.monitor.enabled:` (`:238`). So it is dormant — safe to remove without touching the running daemon's behavior. The code settles this.
- **Q3 — What must survive the monitor removal?** `build_status` (`snapshot.py`) assembles queue depth / run / dreams views — the exact data `status` should show. Preserve it; drop only the monitor-path `write_status` call + the child spawn. The code settles this.
- **Q4 — Does anything else spawn children?** No — `Child`/`children.py` is imported ONLY for the monitor (`launcher.py:242`). So the child model goes dormant (kept, not deleted — Q Context #5).
- **Q5 — What does `status` show today?** Preflight + recent runs (`launcher.status()`). Item 3 adds the `build_status` payload + the running-code-vs-HEAD gap (compare the live run's `commit_sha` from the ledger to `git rev-parse HEAD`).

**Additional risks:** `down`/`up` shell out to `launchctl` (like `deploy` already cycles the run) — guard the not-installed-as-LaunchAgent case (fall back to the plain `stop`/`start` path + a clear message). `bootout` when already down, or `bootstrap` when already up, must be idempotent (report state, don't error).

## 4. Reconciliation

- The monitor was built (Track-B edge monitor) but never worked and is `enabled=false`. Removing it is a **deletion of dormant code**, not a design change — the owner will redo the dashboard from scratch later (brainstorm). `[cross-ref: removal]` no invariant depends on it; `snapshot.build_status` (its data source) is retained for `status`.
- `deploy` already wraps a launchd run-cycle — `restart` reuses that mechanics WITHOUT the deploy gate (no tests/HEAD promotion; a plain down→up). Do not fold `restart` into `deploy` or weaken `deploy`'s gate.

## 5. Write scope

Front-matter: `scripts/palace.py` (subcommand mounts), `ops/lifecycle/launcher.py` (down/up/restart
methods + status enrichment + drop the monitor spawn), `config/{loader,defaults}` (remove
`MonitorConfig`/`[monitor]`), `edge/monitor/**` + `scripts/monitor.py` (delete), and the four test
files (`test_lifecycle{,_control}.py`, `test_status_report.py`, and `test_monitor_server.py` — the
last added by owner grant 2026-07-14 per finding-0075, deleted with the monitor it covered).
**Deliberately OUT of scope:** `ops/lifecycle/snapshot.py` (KEPT unchanged — reused) and
`ops/lifecycle/children.py` + `test_children.py` (KEPT dormant); the plist itself (the install/bootout
commands are read, not rewritten); the diagnostic (bp-031); every store, design note, and the
denylist.

## 6. Interfaces pinned inline

```python
# scripts/palace.py — dispatch; add down/up/restart to the cmd chain (seal() still runs first)
#   USAGE = "usage: palace.py {start|stop|down|up|restart|status|reset|deploy} [--force] …"

# ops/lifecycle/launcher.py — new methods (return an int exit code, like start/stop/status):
#   def down(self) -> int:     # launchctl bootout gui/$uid/<label>  (idempotent; not-installed → message)
#   def up(self) -> int:       # launchctl bootstrap gui/$uid/<plist> (idempotent)
#   def restart(self) -> int:  # down → up  (plain cycle; NOT the deploy gate)

# ops/lifecycle/snapshot.py — REUSED unchanged (do not edit):
def build_status(*, ops_view, dreams_view, queue_depth: int, run=None, ...) -> dict: ...
#   → Item 3 calls this + pretty-prints to the terminal; adds running_commit vs `git rev-parse HEAD`.

# The launchd label + plist path (from the plist / launcher.py:445):
#   LABEL = "com.mind-palace.palace"; PLIST = ~/Library/LaunchAgents/com.mind-palace.palace.plist
#   DOMAIN = f"gui/{os.getuid()}"
```

## 7. Items

### Item 1 — `down` / `up` / `restart` (KeepAlive-aware control)
- **Objective:** `palace down` boots the LaunchAgent out (maintenance — stays down past KeepAlive); `up` bootstraps it back; `restart` is down→up. Idempotent; graceful when not installed as an agent.
- **Files:** `scripts/palace.py` (dispatch + USAGE), `ops/lifecycle/launcher.py` (`down`/`up`/`restart`).
- **Acceptance test:** with a FAKE launchctl runner (inject the subprocess call), `down` issues `bootout gui/<uid>/com.mind-palace.palace` and returns 0; `up` issues `bootstrap gui/<uid> <plist>`; `restart` issues both in order; a second `down` (already out) reports "already down" and returns 0 (idempotent); not-installed-as-agent falls back with a clear message, non-zero only on real failure.
- **Falsifier:** `down` leaves the agent able to be KeepAlive-restarted (used `stop`/SIGTERM instead of `bootout`); OR `restart` silently promotes onto HEAD (must NOT — that's `deploy`).
- **Invariant(s):** none loosened; `seal()` still runs first (Inv 1). Read/40control only.
- **Touches stored data?** No.  **Parallelizable?** No (shares palace.py/launcher with 2,3).

### Item 2 — Remove the dead edge monitor
- **Objective:** delete the dormant dashboard end-to-end; keep the snapshot data + the child primitive.
- **Files:** delete `edge/monitor/**`, `scripts/monitor.py`; remove `MonitorConfig` + the `Config.monitor` field (`config/loader.py`) + `[monitor]` (`config/defaults.toml`); remove the monitor child-spawn + the monitor-path `write_status` call from `launcher.py`. KEEP `snapshot.build_status`, `children.py`, `test_children.py`.
- **Acceptance test:** `grep`-style assertion (or import check) that nothing under `core/edge/ops/scheduler` imports `edge.monitor`/`MonitorConfig`; `load_config()` succeeds with no `[monitor]` section and no `.monitor` attribute; the launcher starts with no monitor branch; the full suite stays green (the removed monitor tests, if any, are deleted with it).
- **Falsifier:** a dangling import of `edge.monitor`/`cfg.monitor` remains (red import/mypy); OR `build_status`/`children.py` were deleted (they must survive).
- **Invariant(s):** Inv 2 unaffected (removing a Zone-B component); the import-firewall still passes.
- **Touches stored data?** No (the monitor `status_path` JSON under `data/` is regenerable/ignorable).  **Parallelizable?** No.

### Item 3 — Enrich `status`
- **Objective:** `palace status` shows preflight + recent runs (today) PLUS the `build_status` payload — run state (pid/commit/clean/recovery), **running-code-vs-HEAD gap**, queue depth, watcher/ingestion freshness, last dream, resident models/RAM headroom, drift — read-only, fast.
- **Files:** `ops/lifecycle/launcher.py` (`status()` renders `build_status(...)` + the HEAD gap).
- **Acceptance test:** `status()` output (captured) includes the run's commit + a "running X behind HEAD Y" line when the live run's ledger `commit_sha` ≠ `git rev-parse HEAD`; includes queue depth + last-dream + resident-model lines from `build_status`; returns 0; makes no writes (a read-only assertion).
- **Falsifier:** `status` mutates any store/file; OR it fabricates a field `build_status` doesn't provide (every shown datum must trace to `build_status`/the ledger/git).
- **Invariant(s):** read-only (Inv 4 flavor — reports data, takes no action).
- **Touches stored data?** No.  **Depends on:** Item 2 (build_status is the retained seam).

## 8. Math carried explicitly

**N/A — no mathematical object.** Ops/CLI control + reporting.

## 9. Non-goals

- **No diagnostic subcommand** — that is bp-031 (the thorough integrity sweep), fully scoped in the brainstorm.
- **No new dashboard** — removal only; the owner redoes it from scratch later.
- **No change to `deploy`'s gate**, the plist, `snapshot.build_status`, or `children.py`'s behavior.
- **No scheduler/dream/store changes** — `status` only READS them.

## 10. Stop-and-raise conditions

- Removing the monitor reveals a NON-monitor importer of `edge.monitor`/`MonitorConfig`/`children.py` → **file a `codebase` finding**, keep the shared piece, narrow the deletion.
- `launchctl bootout/bootstrap` semantics differ on the owner's macOS from the plist header → default to the documented incantation, guard failures with a clear message, file a `codebase` finding; never leave the agent in an unknown state.
- Any blessing flip → must not.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives | Re-entry |
|---|---|---|---|
| `children.py` after the monitor goes caller-less | KEEP dormant + tested (future dashboard reuses it) | delete now (rejected: churn — re-add later) | the dashboard redo |
| `restart` semantics | plain down→up cycle | a deploy-style HEAD promotion (rejected: that IS `deploy`, gated) | — |
| The monitor `status_path` JSON under `data/` | stop writing it (monitor gone); leave any stale file (gitignored) | keep writing for a future dashboard (deferred) | the dashboard redo |

## 12. Dependency & ordering summary

Blast-radius order: **Item 2** (removal — clears the surface) → **Item 1** (control, additive) ∥
**Item 3** (status, reuses the retained `build_status`). 3 depends on 2 (the retained seam). All three
share `scripts/palace.py` + `launcher.py` → one session, not parallel. Model: opus (invariant-adjacent
launcher + a Zone-B deletion; falsifiers need judgment). `depends_on: []`. **bp-031 (diagnostic)
follows**, reusing this plan's enriched `status`/`build_status` seam.
