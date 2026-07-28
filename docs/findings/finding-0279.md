---
type: finding
id: finding-0279
status: open
created: 2026-07-28
updated: 2026-07-28
links:
  - docs/brainstorms/supervision-and-liveness.md
  - docs/brainstorms/the-distributed-ecosystem.md
  - docs/runbook.md
ftype: design
origin_plan: orchestrator
route: orchestrator
resolution: null
---

# Energy is an unmodeled resource axis: two battery emergencies in four days, one fatal to the daemon

## What

Two events, same species, measured:

1. **2026-07-24 ~23:20 EDT (fatal).** The v1.18.0 deploy went out at 22:29 on a battery
   already discharging. `pmset` health log: capacity 10% at 23:27, **2% at 23:31, 1% at
   23:41 — AC attached at 1%**. Under critical-battery throttling the embedder starved:
   `code_backfill` timed out at 23:18, `code_sync` then hung on a dead embedder, and run
   #35's daemon died in the same window (the machine itself never went down — uptime spans
   the event; the precise kill signal is unrecoverable, the unified log has rotated). No
   supervisor existed; the daemon stayed dead **three days** and the queue accumulated 1,766
   jobs.

2. **2026-07-28 ~02:17–04:59 UTC (survived).** AC unplugged unnoticed at 100% during the
   revival; the entire backlog drain — embedder at 98–100% CPU, Podman peaking 60%+, a
   2,400-test suite — ran on battery. **100% → 8% in 2h40m**; the owner plugged in at 8%.
   Zero casualties this time: launchd KeepAlive underneath, and luck. A sampler script
   (`/tmp/mind-palace-battery-watch.sh`, planted 2026-07-26 by a prior session) recorded the
   whole arc at 5-minute resolution.

Battery hardware is healthy (Condition Normal, 95% max capacity, 124 cycles): the drain is
load, not degradation. The palace's compute profile is simply beyond what this laptop's
power envelope assumed.

## Why it matters

NN-8 already encodes the principle — *the scheduler refuses breaching work* — but only the
memory axis is modeled. The daemon will happily run its heaviest sustained compute on a
discharging battery it cannot see, and the failure mode is not graceful: critical-battery
throttling starves the embedder first, which wedges the very lanes with no enforced job
budget, and the death is unclean (recovery mode + stale ledger + three lost days).

## Proposed direction

Small and pattern-matching: health/preflight already samples memory headroom — add power
state (`pmset -g batt` on macOS; per-body-class sensors later, per the ecosystem thread).
On `discharging`: shed embedder-bound lanes (drain-slow mode). Below ~20%: close the ledger
clean and hold scheduling for AC — a deliberate, recoverable pause instead of an unclean
death. Promote the /tmp sampler to a real telemetry sensor. The resource model grows an
axis; the refusal machinery already exists.
