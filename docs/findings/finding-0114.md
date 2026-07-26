---
type: finding
id: finding-0114
status: routed
created: 2026-07-19
updated: 2026-07-26
links:
  - scripts/                                       # the drawer that has drifted
  - CONVENTIONS.md                                 # §Language / package-boundary practice
ftype: discovery         # blocker | spec-defect | question | discovery
origin_plan: bp-072
route: orchestrator      # direction — repo organization; owner's call, not a builder edit
resolution: routed → owner (oq-0038); re-measured 38 files / 4077 LOC
---

# `scripts/` has drifted into three drawers under one label — a tidy is worth considering

> **Triage 2026-07-26 (session-52) — batched to `oq-0038`.** Still live and larger than filed:
> `scripts/` now holds **38 files / 4077 LOC** (was 34 / ~2.8k). No `archive/` subdir exists; every
> named drawer-2 one-off (`migrate_chunk_keys.py`, `migrate_provenance_split.py`,
> `reembed_bodyonly.py`, `purge_raw.py`, `ingest*.py`, `snapshot_code.py`) and every drawer-3 harness
> (`experiment.py`, `review.py`, `tune.py`, `sweep.py`, `report.py`, `verdict.py`, `fibers.py`,
> `eval.py`) is still in place. `CONVENTIONS.md` states no `scripts/` vs `eval/` boundary.

## What
Surfaced by the owner mid-bp-072 ("the scripts dir is getting overly crowded"). `scripts/`
holds **34 files / ~2.8k LOC** that fall into three distinct kinds:

1. **Durable entrypoints / CLIs** (the healthy core of `scripts/`): `palace.py`, `cockpit.sh`,
   `docket.py`, `readmap.py`, `run_with_secrets.sh`, `keep-awake.sh`, `build_sandbox_image.sh`,
   `mint_ids.py`, `supersede.py`, `sandbox.py`, `talk.py`, `watch.py`, `sense_self.py`.
2. **Spent one-offs / migrations** (ran once, now archaeology): `migrate_chunk_keys.py`,
   `migrate_provenance_split.py`, `reembed_bodyonly.py`, `purge_raw.py`, `ingest.py`,
   `ingest_founding.py`, `ingest_self_knowledge.py`, `snapshot_code.py`.
3. **Eval-flavored harnesses** (substantial; arguably misfiled): `experiment.py` (250L),
   `review.py` (278L), `tune.py` (187L), `sweep.py`, `report.py`, `verdict.py`, `fibers.py`,
   `eval.py`.

## Why it matters
Two of the three drawers are drift, not design:
- Drawer 2 is dead weight — git preserves the history, so an `archive/` subdir or outright
  deletion loses nothing and de-clutters the working surface.
- Drawer 3 arguably violates the owner's own package-boundary principle (math→core,
  notebook→eval; core self-containment cuts both ways): a tuning/experiment/eval harness reads
  like an `eval/` citizen, not a repo-utility one-off. Moving them would sharpen the same
  boundary the `test_core_self_containment` ratchet enforces from the other side.
- Not urgent — nothing is broken; this is hygiene, and any move touches `eval/` (outside every
  current plan's write_scope), so it wants its own small plan, not a mid-build detour.

## Re-entry condition
N/A — no bp-072 criterion is parked on this (the 4 files bp-072 adds are all drawer-1
entrypoints; the build is unaffected). This is a standing direction item for the orchestrator
to weigh: capture as a brainstorm → a `scripts/` tidy plan (archive drawer 2; relocate drawer 3
into `eval/` if the owner agrees the boundary applies), or close as won't-do if the flat drawer
is preferred.

## Routing
`direction` → orchestrator. Owner's call on whether the package boundary applies to the eval
harnesses and whether the spent migrations are archived vs deleted. No design-note change is
implied unless the owner wants the `scripts/` vs `eval/` boundary written into CONVENTIONS.
