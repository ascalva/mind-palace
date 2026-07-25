---
type: finding
id: finding-0172
status: open
created: 2026-07-25
updated: 2026-07-25
links:
  - ops/lifecycle/launcher.py                          # status — the reporting surface
  - docs/brainstorms/command-center.md                 # the owner's TUI vision this warrants
  - docs/findings/finding-0169.md                      # the incident status failed to surface
  - docs/findings/finding-0173.md                      # the orphaned running row status believes
ftype: discovery
origin_plan: orchestrator
route: builder
resolution: null
---

# `palace status` reports state, but every symptom of a live incident was a rate

## What

Two distinct defects, found by watching `status` fail to describe an incident happening underneath
it (2026-07-25, run #35).

**(1) It reported a dead daemon as `RUNNING`.** After `kill -9` of pid 96950, with no palace process
alive and the launchd service gone from the `gui/501` domain, `status` still printed:

```
#35 5c2222924874 started 2026-07-25T02:29:11 — RUNNING
running HEAD (5c2222924874).
```

It reads the run ledger without a liveness check. `deploy` does check (`_pid_alive(run.pid)`,
`ops/lifecycle/launcher.py:605`), so the primitive exists and the reporting path simply does not
use it. **`status` is the one command an operator trusts to answer "is it up?", and it can answer
wrongly.**

**(2) It showed six green checkmarks fifteen minutes after a job failed.** The `code_backfill` job
died at 03:45:02 UTC with `TimeoutError`; the queue's own lifetime counter moved `0 failed → 1
failed`. `status` displayed no failure, no error, and no indication that anything had gone wrong.

## Why it matters — the generalization

Every symptom of the incident was a **derivative or a budget**, and `status` reports only levels:

| what status said | what was true |
|---|---|
| `queue depth: 1714` | growing ~2/min with **zero drain** |
| `code_backfill running` | **74 of its 75-minute** budget spent |
| `lifetime: 300,239 done` | *identical an hour earlier* — **zero throughput for an hour** |
| (not shown) | 99% CPU with a **0.3% embedder** — the wrong kind of work |
| (not shown) | 847/1,542 versions with a **diverging** ETA |
| (not shown) | 1 job failed 15 minutes ago |
| `running HEAD` | the process was dead |

A count cannot be wrong; a rate can. The owner checked `status` repeatedly through a 90-minute
incident and it never once indicated a problem — not because any field was false (except the
liveness lie), but because the informative quantities were absent. This is the concrete warrant for
the owner's command-center ask (`docs/brainstorms/command-center.md`, captured same session):
*"a TUI updating in real time with informative, detailed, useful metrics… the true, deep metrics
and how they tie into the macro."*

## The fix — two tiers

**Tier 1 (builder, small, now).** Enrich `status`:
- liveness check on the reported run — never print `RUNNING` for a dead pid;
- failure surface: count + last failure kind/error/time;
- throughput: jobs completed in the last N minutes (a zero here is the single most diagnostic
  number available and costs one query);
- queue in-rate vs out-rate, and per-kind oldest age;
- running job: elapsed vs its timeout budget;
- store: rows, distinct code versions vs ledger target, `current=true/false` split;
- embedder-active indicator (embed calls in the last N minutes).

**Tier 2 (design).** The real-time command center is a design question, not a coding task — what
*is* the macro state of Ouroboros (corpus coverage, supersession realized, causal-edge density,
drift, memory-ceiling headroom), and how do the deep metrics ladder up to it? That goes
capture → design note → plan through the normal gate. The capture exists; the note is owed.

## Re-entry condition

Tier 1 rides with the finding-0169/0170 restart — it is the instrument for verifying that fix, so
building it first is the cheaper order. Tier 2 re-enters at the owner's ratification of the
command-center design note.

## Routing

`codebase` → builder for Tier 1. Tier 2 is design and routes through the capture already filed;
this finding is its warrant.
