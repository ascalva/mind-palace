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

## 2026-07-25 — the split view: metrics on the left, an ORIENTED agent on the right

```capsule
topic: command-center (the agent pane)
date: 2026-07-25 (session-44, ~02:30)

warrant (owner, verbatim): "another thought for the ops side, the command center, it would be useful
to be able to switch to a similar view, left view is metrics and relevant logs, the right is claude,
with the last claude orchestrator conversation as part of its context, so it understands the latest
changes, and if it needs to be looking out for something"

⚑ HALF OF THIS ALREADY EXISTS — the ask is largely a LAYOUT + CONTEXT change, not a new system.
  `scripts/cockpit.sh` already builds exactly these two halves, just in DIFFERENT WINDOWS:
    · `desk` window, split -h: pane 0 = the docket in nvim (reading), pane 1 = the Claude
      orchestrator (`orchestrator-launch.sh`, :98/:100), focus left on pane 0 (:102)
    · `ops` window: `palace status` + `tail -n 40 -F data/logs/palace.out.log` (:104-105)
  ⇒ The ask = a THIRD window (or a re-layout) putting `ops` and the Claude pane SIDE BY SIDE, plus
    the context pre-load. That is cheap — tmux plumbing in a file the palace already owns — and it
    is a far smaller lift than a bespoke TUI. Tier 2's rendering work stays valuable; this is about
    WHERE it renders and WHO is sitting next to it.

⚑ THE CONTEXT-LOADING PROBLEM IS ALREADY SOLVED — by the artifact chain, not by transcript replay.
  "the last claude orchestrator conversation as part of its context" does NOT need raw transcript
  injection (expensive, unbounded, and the transcript is exhaust not artifact). The palace already
  produces the designed answer: **`.claude/state/resume-brief.md`** — the session handoff, written
  at every semantic boundary and held to the FRESH-AGENT TEST (a new session with only plan +
  journal + brief must continue without re-asking). Plus the journals, the open findings, and
  DESKCHECK-QUEUE/owner-questions.
  ⇒ The agent pane should boot from the ARTIFACTS, not the chat log. That is the whole reason the
    handoff gate exists. Raw transcripts are the fallback for what the brief failed to capture —
    and if that happens often, the brief is the defect, not the loader.

⚑⚑ THE DEEPEST PART OF THE ASK — "if it needs to be looking out for something" — IS A WATCHLIST,
  AND IT CLOSES THE DETECTION-LAG LOOP.
  The session that made a change is the one that knows what to expect of it. Tonight: "watch the
  RATE, not the depth"; "the backfill ETA should CONVERGE, not diverge"; "current=false rows should
  climb". None of that was written anywhere a machine could check — it lived in the conversation.
  ⇒ A watchlist is a **DECLARED EXPECTATION handed from the session that made the change to the
    instrument that watches the result.** Which is precisely the reconciliation-audit 2026-07-25
    thesis: *you cannot catch an inconsistency without first having made a consistency claim.* The
    agent pane is where those claims get authored, and the metrics pane is where they get checked.
  ⇒ CONCRETE SHAPE: the orchestrator writes a small typed watchlist as part of its handoff (beside
    the resume brief) — predicate + expected direction + re-entry. The instrument evaluates it. This
    is the missing FIRST LINK of the refinement cycle (f-0172 / reconciliation-audit): it moves the
    trigger from "the owner happened to look" to "the claim the last session made is now false."

⚑ COST ARCHITECTURE — DO NOT LET THE AGENT POLL. (This is f-0170's lesson, one level up.)
  An always-on agent watching a dashboard burns tokens continuously and, worse, becomes load on the
  system it observes — exactly the feedback loop f-0170 recorded (the chat watcher watching the
  agent's own transcripts). The correct shape is **cheap deterministic detector, expensive
  interpreter ON DEMAND**: the metrics pane computes the anomaly predicates (already in Tier 2's
  scope — "anomaly should be a first-class rendering state, not something the reader infers") and
  only ESCALATES to the agent when one fires.
  ⇒ NOTE THE PATTERN, third instance tonight: Bloom-as-negative-filter in front of an exact store;
    SIFT's cheap detector before the expensive descriptor; and now a cheap predicate before the
    expensive interpreter. **Cheap-detector/expensive-interpreter is a recurring architecture in
    this system** — worth stating as a design principle in the ops note rather than rediscovering it
    a fourth time.

link, not a decision: this is plausibly where the OPS SECTOR EXPERT lives (dn-sector-experts, draft)
  — a standing expert whose sector is the running system, spawned from artifacts rather than
  resident, answering with grounded and challengeable claims. Do not fuse the two notes; record the
  seam and let the sector-experts pass decide whether the command center's agent pane IS that
  expert's residence.

open questions:
  - Watchlist as a typed artifact: where does it live (beside the resume brief? a `docs/` artifact?
    the queue?), what is its schema, and who retires an entry — the author, the instrument, or the
    owner?
  - Does the agent pane get WRITE authority (file a finding when a watch fires) or is it read-only
    advisory? "The model advises, code acts" says advisory by default; filing a finding is arguably
    still advice. Needs a ruling, not an assumption.
  - tmux re-layout vs a real TUI: is the split-window version enough to test the idea before Tier 2
    builds anything bespoke? (Almost certainly yes — and it would be a MEASURED premise instead of
    an assumed one, which is this session's recurring lesson.)
  - Which plane does the agent pane run in (`PLANE=ascalva` vs `workflow`)? It reads ops state and
    may file findings — the plane split has security consequences the panel should vet.
```
