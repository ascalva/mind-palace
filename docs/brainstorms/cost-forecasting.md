# cost-forecasting

Owner direction (2026-07-11, chat): cost tracking should grow into FORECASTING — "like
real JIRA with epics, features, and stories, we can optimize based on estimated cost and
based on models used."

## 2026-07-11T19:30:00Z (captured)

```capsule
topic: cost-forecasting
date: 2026-07-11

decisions:
  - Actuals first (already ruled): every delegated build's measured usage (tokens, tool
    calls, duration, model) is recorded in its SEAL entry (delegate + context-economy
    skills, encoded 2026-07-11).

open_questions:
  - Estimates: should the build-plan template gain an estimated-cost field (tokens by
    tier) set at graduation, so seals produce estimate-vs-actual calibration?
  - Hierarchy mapping: design note ≈ epic; build plan ≈ story; item ≈ task. Does the
    forecast roll up at the note level (what did the type plane COST end to end)?
  - Model-mix optimization: with per-plan actuals by model tier, choose the cheapest
    tier whose falsifier-pass rate holds — measurable after ~2 weeks of seals.
  - Reporting surface: /triage monthly cost table? The site's what's-new? PROGRESS?

parked:
  - decision: template change (estimated-cost field)
    default: seals-only actuals accumulate; no template change yet
    re_entry: two weeks of seal data exist, or the next /graduate wants to estimate

next_steps:
  - Accumulate seal actuals (bp-008 onward — first seal under the rule).
  - At re-entry: propose the template field + a tiny cost report generator (reads seals).

references:
  - .claude/skills/context-economy/SKILL.md
  - .claude/skills/delegate/SKILL.md
```
