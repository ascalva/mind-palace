---
type: finding
id: finding-0171
status: open
created: 2026-07-25
updated: 2026-07-25
links:
  - ops/lifecycle/launcher.py                          # deploy/stop/down — the graceful-drain contract
  - docs/findings/finding-0169.md                      # the pathological job that exposed the gap
  - CONSTITUTION.md                                    # the model advises, code acts — shutdown is code's job
ftype: spec-defect
origin_plan: orchestrator
route: orchestrator
resolution: null
---

# Graceful shutdown has no bound — `down` could not bring the system down

## What

The lifecycle contract stops the daemon by SIGTERM → **drain at the job boundary** → exit. This is
correct discipline and is what makes `deploy` safe. But the drain has **no time bound and no
escalation**: if the in-flight job does not reach a boundary, the shutdown never completes.

Observed 2026-07-25, run #35, with `code_sync` job 300246 wedged in the finding-0169 scan:

```
$ palace down
down: booted out com.mind-palace.palace — stays down past KeepAlive. `palace up` to bring it back.

$ ps -o pid=,stat=,etime=,time=,%cpu= -p 96950
  96950  R  01:33:02  19:46.36  96.3          ← still alive, still pegged
$ launchctl print gui/501/com.mind-palace.palace
  active count = 1                            ← bootout pending on process exit
```

`down` returned success and reported the service booted out. The launchd *job* was unloaded; the
**process kept running at 96% CPU**, and would have kept running until the job's own ~75-minute
timeout fired (projected 05:00 UTC, ~57 minutes after the shutdown command). The owner's shutdown
command could not stop the system. Resolution required `kill -9` with owner authorization.

## Why it matters

This is a **safety property, not a performance one**, and it is the most serious of the five
findings from this incident.

- The graceful-drain contract silently assumes jobs terminate promptly. Nothing enforces that
  assumption, and one pathological job voids it.
- `deploy` shares this path (`self.stop()` before waiting for the successor run). A deploy issued
  while a wedged job is running will hang the same way, then report `deploy: TIMED OUT` — a
  confusing symptom for an unrelated cause.
- The only remedy available to the owner was SIGKILL, which is precisely the thing the graceful
  design exists to avoid. A shutdown path whose fallback is the ungraceful kill has not eliminated
  the ungraceful kill; it has hidden it behind a command that claims success.
- `down` **returning success while the process lives** is the part to fix first: whatever the
  escalation policy, the command must not report a state it has not achieved.

## The design question (owner input wanted)

The fix is not purely mechanical — it is a policy choice about what the system owes a wedged job:

- **(a) Bounded drain with escalation.** SIGTERM → wait N seconds → SIGKILL, N configurable, the
  escalation logged and surfaced. Simple, conventional, guarantees termination. Cost: a killed job
  may lose in-flight work (here, `supersede_source`'s `delete → add` window can drop one path's
  rows — recoverable by re-embed from git, but genuine loss).
- **(b) Worker-enforced job budgets.** Each job carries a wall-clock budget the *worker* enforces
  from outside, so no job can exceed it and the drain boundary is always reachable. Stronger — it
  fixes the class rather than the shutdown symptom — but needs a cancellation seam in the handlers.
- **(c) Both**: (b) as the real fix, (a) as the fail-safe behind it.

My recommendation is (c), with `down` reporting honestly in the interim. But the escalation
deadline, and whether an interrupted store write is acceptable, are the owner's calls — they trade
a data-integrity risk against an availability guarantee, which is exactly the kind of decision
that routes here rather than to a builder.

## Re-entry condition

Not blocking the finding-0169/0170 fix — the daemon is already down and stays down. Re-entry: at
the owner's answer on (a)/(b)/(c), which should be batched into `owner-questions.md`. Until then
the interim mitigation is knowledge, not code: **`down` may not stop a wedged daemon; check
`ps` before trusting it.**

## Routing

`design` → orchestrator. Batch the (a)/(b)/(c) choice to `owner-questions.md`. The honest-reporting
half of the fix (`down` must not claim success while the process lives) is builder-resolvable
without waiting on that answer and can be split off.
