---
type: finding
id: finding-0178
status: open
created: 2026-07-25
updated: 2026-07-25
links:
  - scheduler/supervisor.py                            # tick() — the unbounded synchronous handler call
  - core/models/ollama_client.py                       # _post — the socket timeout that actually fired
  - config/defaults.toml                               # [ollama] request_timeout_s = 120, the only real bound
  - docs/findings/finding-0171.md                      # the escalation-policy question this re-frames
  - docs/findings/finding-0169.md                      # the incident whose "75-minute budget" was inferred
  - docs/build-plans/bp-102/plan.md                    # Q4, and the knob this finding cancels
ftype: discovery
origin_plan: bp-102
route: orchestrator
resolution: null
---

# There is no job timeout — the "~75-minute budget" never existed, and one socket timeout is doing its job

## What

bp-102 Q4 asked where the job timeout is configured, having failed to find it during triage. The
answer, established from code and from the live queue: **there is no job-level timeout anywhere in
the system.** Nothing in `scheduler/`, `ops/` or `config/` bounds a job's wall clock — no deadline,
no `signal.alarm`, no watchdog. `Supervisor.tick` (`scheduler/supervisor.py:63`) calls
`handler(job)` synchronously and waits as long as the handler takes.

What actually killed `code_backfill` job 300240, read out of `data/queue.sqlite`:

```
300240 | code_backfill | failed
       | started 2026-07-25T02:30:12 | finished 2026-07-25T03:45:02
       | TimeoutError('timed out')
```

`TimeoutError('timed out')` is `socket.timeout`. It is raised from `urllib`'s socket read and is
**not** a `urllib.error.URLError` subclass, so it escapes `OllamaClient._post`'s
`except urllib.error.URLError` un-wrapped (it never becomes an `OllamaError`) and propagates to
`tick`'s blanket `except Exception → queue.fail(repr(e))`.

So the chain is: **one embed call exceeded `[ollama] request_timeout_s = 120`, after the job had
already been running 74m50s.** The 4,490 s was *elapsed*, not a budget. The "~75-minute job
timeout" in the finding-0169 triage — and in bp-102 §3 Q4 and §8's "budget fraction" — is an
inference from that elapsed time, and it is wrong.

## Why it matters

**1. It cancels a knob that would have been decorative.** bp-102 Item 3 was to add the timeout to
`config/defaults.toml`. Under the plan's own falsifier ("the knob is added but nothing reads it")
that would have been a defect: nothing would read it, because *enforcing* a job budget is
finding-0171 option (b) — an open owner decision, explicitly out of bp-102's scope. The config half
was therefore dropped and `config/defaults.toml` is unchanged. `status` reports a running job's
elapsed with an explicit "no enforced job budget" rather than inventing a denominator.

**2. It sharpens finding-0171.** Option (b), "worker-enforced job budgets", is not a hardening of
an existing mechanism — it is a *new* one. There is nothing to tune, only something to build. And
option (a)'s premise is now firmer: without (b) there is genuinely no upper bound on a drain, so
`down` can wait forever. That is not a hypothetical; it is what 2026-07-25 was.

**3. The real bound is in the wrong place and is silent about it.** The only thing that terminates
a pathological job today is a *per-call socket timeout* on the embedder. That means:

- a job that wedges without calling Ollama (a pure-CPU scan — precisely finding-0169's
  `supersede_source`) has **no** terminating condition at all; it ran 74 minutes only because it
  happened to call `embed` periodically;
- the failure surfaces as a bare `TimeoutError('timed out')` with no job kind, no phase, no URL —
  the least informative possible message for the single most confusing failure of that night. It
  reads as "a job timed out" when it means "one HTTP request to a local server timed out";
- because `socket.timeout` is not a `URLError`, `OllamaError` — the type built precisely to make
  Ollama failures legible — never fires for a timeout. Every other Ollama failure is wrapped; this
  one, the most common under load, is not.

## Re-entry condition

Batches with finding-0171's (a)/(b)/(c) question, which it re-frames: the owner is choosing whether
to *build* a job-budget mechanism, not whether to configure one. Two builder-resolvable pieces can
be split off independently of that answer, in whatever plan owns `core/models/ollama_client.py`:

1. catch `TimeoutError`/`OSError` alongside `urllib.error.URLError` in `_post`/`_get` and raise
   `OllamaError` with the path and the timeout value, so a timeout is legible where it happens;
2. have the supervisor record the job kind and elapsed on failure, so `queue.error` says which job
   died after how long.

Neither prejudges the escalation policy.

## Routing

`design` → orchestrator, batched with finding-0171 (same owner decision; this changes what the
decision is *about*). The two mechanical pieces above are `codebase` and can be routed to a builder
at any time.
