---
type: finding
id: finding-0171
status: routed
created: 2026-07-25
updated: 2026-07-25
links:
  - ops/lifecycle/launcher.py                          # deploy/stop/down — the graceful-drain contract
  - docs/findings/finding-0169.md                      # the pathological job that exposed the gap
  - CONSTITUTION.md                                    # the model advises, code acts — shutdown is code's job
ftype: spec-defect
origin_plan: orchestrator
route: orchestrator
resolution: "oq-0035 RULED 2026-07-25 — (c) both. Design half lands in dn-supervision-and-liveness (ratified); build half awaits /graduate."
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
  **[banner: correction — 2026-07-25, bp-102 builder]** This option was written as if a budget
  existed and merely needed enforcing at shutdown. **It does not: `Supervisor.tick` calls
  `handler(job)` synchronously and unbounded, and there is NO job-level timeout anywhere.** The
  ~75-minute figure this finding cites was a `socket.timeout` on one embed call
  (`[ollama] request_timeout_s = 120`), escaping `OllamaClient._post`'s `except URLError` because
  `TimeoutError` is not a `URLError` subclass. So (b) is **build**, not tune — and the projection in
  §What that the wedged process would "exit at its own ~75-minute timeout, ~57 minutes away" was
  **false**: nothing would have stopped it. The `kill -9` was the only exit, not an impatient one.
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

## Owner ruling — 2026-07-25 (oq-0035)

**(c) BOTH.** Verbatim: *"I like (c), feels like the most robust approach."*

- **(b) worker-enforced job budgets = the real fix.** Per finding-0178 there is no job timeout to
  tune — this is a BUILD. It becomes enforceable only once the handler stops owning the
  supervisor's thread (`dn-supervision-and-liveness` §2.2/§2.5): you cannot bound a synchronous
  in-process call from outside it.
- **(a) bounded SIGTERM → N → SIGKILL = the fail-safe behind it**, aimed **only at the WORKER,
  never the supervisor**. Killing the supervisor is what the lease/dead-man design makes
  unnecessary, and it is what would lose the landing step.

⚑ **This finding's stated crux has dissolved.** The question framed the trade as *"whether an
interrupted store write is acceptable"* — data integrity against a shutdown guarantee. The ratified
note's I1 survey (all 11 registered kinds) found **no handler is irreducibly write-interleaved**,
and `ambassador_task` (`scheduler/interface.py:53-59`) **already** computes-then-returns while the
supervisor lands the result (`scheduler/supervisor.py:94-95`). Under the compute/land split nothing
interrupts a write: a computation is interrupted and nothing is landed. Single-writer gets
*stronger* — landing becomes a short atomic step the supervisor owns rather than an hours-long span
it delegates. The `supersede_source` delete→add window this finding worried about closes
structurally rather than being accepted as a cost.

**Open, and NOT a gate on the ruling — V3:** does Ollama abandon its work when its HTTP client
dies? If not, killing the worker stops the *accounting* but not the *burn* — the drain completes
and the daemon exits (what this finding asked for), while consumption continues on the Ollama side
until that call returns. Unmeasured. It is a direct argument for NEW NOTE 2 (llama.cpp-direct),
where cancellation becomes ours to hold rather than to ask about. See also finding-0199.

**Status:** the DESIGN half is discharged by `dn-supervision-and-liveness` (ratified `3945d9f`).
The BUILD half is owed and arrives via `/graduate` on that note — it is OPS-4's design half.
The honest-reporting half shipped separately in bp-102 Item 3.
