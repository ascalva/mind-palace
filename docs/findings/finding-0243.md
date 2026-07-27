---
type: finding
id: finding-0243
status: open
created: 2026-07-27
updated: 2026-07-27
links:
  - docs/roles/orchestrator/readings.md                  # the artifact carrying the bad timestamps
  - docs/build-plans/bp-124/journal.md                   # the plan that wrote them
  - docs/build-plans/bp-125/plan.md                      # Item 8, whose falsifier names this exact failure
  - docs/build-plans/bp-127/plan.md                      # F1b's home — the natural place for a lint
  - docs/design-notes/role-state-and-scoped-handoff.md   # §2.5 MEASURED — "age displayed, never hidden"
  - scripts/handoff.py                                   # latest_per_command: last-in-file, by contract
ftype: discovery
origin_plan: bp-125
route: orchestrator
resolution: null
---

# The seat's first MEASURED rows carry timestamps 56 minutes ahead of the commit that wrote them

## What

`docs/roles/orchestrator/readings.md` was seeded by `bp-124` with seven rows stamped
`2026-07-27T03:36Z` through `T04:56Z`. The commit that introduced them landed at **04:00Z**:

```
7f918b6  2026-07-27T03:38Z   feat(bp-124): open the orchestrator seat …
f9f333a  2026-07-27T04:00Z   docs(bp-124): seal — the gate as MEASURED rows …   <- introduced the rows
```

A row claiming `04:56Z` was committed at `04:00Z`. **Four of the seven rows are stamped after the
commit that contains them**, the latest by 56 minutes. A reading cannot postdate its own commit, so
those stamps were not read from a clock.

This surfaced during `bp-125`, whose own gate rows (`04:41Z`–`04:53Z`, committed `04:55Z`) are
internally consistent and were taken with `date -u`. Appending them put genuinely-later readings
*below* earlier-stamped ones, which is what made the discrepancy visible: the log stopped being
monotonic in timestamp.

## Why it matters

**1. It is the exact failure `bp-125` Item 8's falsifier names.** That falsifier reads: *"a reading
whose timestamp had to be invented to satisfy the row shape. A fabricated timestamp is worse than an
absent one — it makes a stale reading impersonate a current fact, the exact failure the age-display
rule exists to prevent."* The falsifier was written for the migration and did not fire there —
`bp-125` marked two genuinely-unknown stamps as `unknown`. It fired one artifact over, on the seed
data, where nothing was checking.

**2. It silently degrades the pane's headline feature.** The whole point of the MEASURED class is
`age displayed, never hidden` — *"suite: 2 failed / 2301 passed (18h ago)"*. `_age()` computes that
age from the row's stamp against the wall clock. A stamp ahead of real time renders a **negative or
near-zero age**, so the stalest thing in the pane advertises itself as the freshest. That is
precisely the impersonation the design exists to prevent, arriving through the front door.

**3. The generator is robust to it, which is why it went unnoticed.** `latest_per_command` selects
**last-in-file**, not max-timestamp, on the stated ground that *"the log is append-only, so file
order already is chronological order."* That assumption is now false in this file, and the
robustness masks it: the pane picks the right row for the wrong reason. A future consumer that sorts
by timestamp — the `readings.md` schema tightening already parked in the note's Parked decisions —
would pick the stale rows.

## What was NOT done, and why

**`bp-124`'s rows were not corrected.** They are another plan's record, and the log is append-only
in the `finding-0164` / `finding-0168` sense: keep and link, never delete and replace. Rewriting
seven rows to make a graph look tidy would destroy the only evidence this finding rests on.
`bp-125` instead appended fresh rows with `date -u`-verified stamps and recorded the discrepancy in
the file's own preamble, so the next reader meets the caveat before the data.

## Options for the orchestrator

1. **Lint it in `bp-127`** (cheapest, and F1b is already opening that file): reject a reading whose
   timestamp is in the future relative to the commit that adds it, or simply relative to `now`. A
   future-dated reading is *always* wrong and needs no judgement to detect.
2. **State the rule in the readings preamble** — a stamp is read from `date -u` at the moment of the
   run, never composed. Cheap, but it is a convention, and this repo's own record is that a
   convention you wrote down is not enforcement.
3. **Do nothing beyond the caveat.** Defensible while the log is short and the generator is
   order-based — but the parked schema tightening would make it load-bearing later.

Option 1 is recommended: the check is mechanical, the failure is unambiguous, and `bp-127` is
already the plan that touches this artifact's linting.

## Re-entry condition

Resolved when either a lint lands (option 1) or the orchestrator records a decision to accept the
caveat. Not blocking: no current consumer is misled, because the generator selects by file order.

## Routing

`discovery` → **orchestrator**. It concerns a merged plan's output that `bp-125` may not rewrite,
and the remedy is a scope decision for `bp-127` rather than a builder's fix.
