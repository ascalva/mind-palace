# The command center — real-time, deep instrumentation of Ouroboros

Brainstorms on replacing `palace status` with a live TUI that shows the *true, deep* metrics of the
running system and how they ladder up to the macro state. Warrant: finding-0172 — a 90-minute
incident that `status` never once indicated. Feeds a Fable design-pass → its own track.

## 2026-07-25 — the night status said everything was fine

```capsule
topic: command-center
date: 2026-07-25 (session-44, the post-deploy incident)

warrant (owner, verbatim): "can you quickly integrate this type of view into status, I feel like
it doesn't give me enough information, or maybe it should be the command center, it should be a
tui that is updating in real time with informative, detailed, and useful metrics on the state of
ouroboros, the true, deep, metrics and how they tie into the macro"

the incident that motivated it (all measured, 2026-07-25 02:29–04:07 UTC, run #35):
  - `code_backfill` ran 74m50s at ~99% CPU and died on a TimeoutError, reaching 847 of ~1,542
    versions. Root cause: `supersede_source` is O(total store) — two full-table `to_pylist()`
    materializations (11.7s each, vectors included) per superseded version. (finding-0169)
  - The queue grew 13 → 1,766 while the worker was pinned; 883 `chat_sync` + 883 `vault_sync`,
    all idempotent duplicates, because `enqueue()` has no coalescing. (finding-0170)
  - `palace down` returned success while the process kept running at 96% CPU — the graceful drain
    waits on a job boundary a wedged job never reaches. Required SIGKILL. (finding-0171)
  - After the kill, `status` still printed `RUNNING` for a dead pid. (finding-0172)
  - The killed worker orphaned its `running` job row; no lease, no reclaim. (finding-0173)
  - Through all of it the owner checked `status` repeatedly. It showed six green checkmarks and a
    queue-depth integer. It never indicated a problem.

THE CENTRAL INSIGHT (the design principle to build on):
  **`status` reports LEVELS; every symptom of the incident was a RATE or a BUDGET.**
  A count cannot be wrong — it is just a number that is true. A rate can be wrong, and that is
  exactly what makes it informative. The instrument was not inaccurate; it was measuring the
  wrong class of quantity.

    level shown              | derivative that mattered
    -------------------------|------------------------------------------------
    queue depth: 1714        | growing ~2/min with ZERO drain
    code_backfill running    | 74 of its 75-minute budget spent
    lifetime: 300,239 done   | unchanged for an hour = zero throughput
    (absent)                 | 99% CPU with 0.3% embedder = wrong kind of work
    (absent)                 | 847/1542 with a DIVERGING ETA
    (absent)                 | 1 job failed 15 minutes ago
    running HEAD             | the process was dead

  Corollary: the most diagnostic single number available all night — "jobs completed in the last
  20 minutes" — costs one SQL query and did not exist anywhere in the system.

design directions (to be sharpened in the Fable pass):
  - Two tiers, deliberately separated. TIER 1 is a rate/budget block bolted onto `status` — cheap,
    unblocks the finding-0169 fix by being the instrument that verifies it. TIER 2 is the real
    command center and is a DESIGN question, not a coding task.
  - The Tier-2 question is not "which numbers?" but "what IS the macro state of Ouroboros?"
    Candidate macro axes, each of which deep metrics must ladder up to:
      · corpus completeness   — versions embedded vs ledger, per lane; coverage %, honest gaps
      · history realized      — supersession edges resolved; current/superseded split; f-0168's
                                n(v) membership frequency + the Zipf histogram as a language gauge
      · causal density        — E_proven vs E_composed by evidence grade (integrator's coverage
                                gauge); the "which conversation wrote this?" answer rate
      · drift & integrity     — drift axes, constitution anchor, the reconciliation-audit map
      · headroom              — memory ceiling (≤2 resident, ~20–24 GB), queue in-vs-out, worker
                                saturation, cost/budget burn
      · liveness & honesty    — is it actually up; what failed; what is stuck; what is stale
  - Every panel should show a level AND its derivative, and every bounded thing should show
    elapsed-vs-budget rather than elapsed alone. That is the lesson generalized into a layout rule.
  - Anomaly should be a first-class rendering state, not something the reader infers: zero
    throughput with a non-empty queue, a diverging ETA, a job past 80% of budget, CPU high with the
    embedder idle — these are computable predicates and should be surfaced as such.
  - The observer is inside the system (finding-0170): agent activity feeds the chat watcher, so the
    TUI must not itself become load. Read-only, sampled, and ideally reading the same stores rather
    than triggering work.

open questions:
  - TUI framework and whether it lives in `ops/` (unsealed, may reach the network for nothing) or
    is a pure local reader over the stores.
  - Refresh cadence vs cost — a 1s refresh that full-scans lance is the finding-0169 mistake again.
  - Does this subsume `palace status`, or sit beside it as `palace top` / `palace cockpit`?
  - Relationship to the existing cockpit tmux session (`scripts/cockpit.sh` already reserves an
    `ops` window running `status` + a log tail — the natural home).
  - Does the reconciliation-audit's decision→enforcement map belong here as a panel? (Two
    instruments aimed at the same worry: "is the tower actually standing?")

sequencing: Tier 1 rides with the finding-0169/0170/0173 fix restart — it is how we verify that fix.
Tier 2 goes capture → design note → plan through the normal gate, and per the standing 2026-07-23
ruling it gets an adversarial expert-panel pass (systems + core at minimum) before ratification.
```
