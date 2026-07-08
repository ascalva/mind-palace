---
type: finding
id: finding-0017
status: routed
created: 2026-07-06
updated: 2026-07-08
links:
  - docs/research/planar_graphs.md
  - docs/research/un-represent-ability.md
  - docs/README.md
  - docs/audits/corpus-state-audit-2026-07.md
ftype: discovery
origin_plan: orchestrator
route: orchestrator
resolution: null
---

# finding-0017 — docs/research/planar_graphs.md is an uncatalogued orphan; both research surveys are statusless

> **Triage 2026-07-08 (/triage):** routed → orchestrator. Corpus-hygiene owner call (catalogue-as-background-ref vs prune; optional front-matter on both surveys) batched to `owner-questions.md` **oq-0009**. Re-entry per §Re-entry condition below.

## What
`docs/research/planar_graphs.md` is an external survey with no implementation target
(grep for `planar|kuratowski|genus|planariz|fary|boyer|myrvold` across
`core/ eval/ ops/ edge/ scripts/ tests/` returns 0), is **not catalogued in
`docs/README.md`** (which lists the other two research notes), and is unreferenced by
any note or code. Its "topology" framing collides in name with `core/complex/topology.py`,
which implements a *different* body of math — persistent homology / Vietoris–Rips
(`topology.py:59`), not planar-graph drawing. Separately, both research surveys
(`planar_graphs.md` and `un-represent-ability.md`) are statusless — no front-matter —
unlike the ratified/draft design notes.

## Why it matters
An orphan reference doc with a name-colliding subject invites a future reader (or
agent) to assume `core/complex/` realizes planar-graph theory (it does not). Low
severity — corpus hygiene — but the naming collision is a genuine trip hazard given
how central `core/complex/` is.

## Re-entry condition
Owner catalogues `planar_graphs.md` in `docs/README.md` with an explicit "background
reference, not a spec" line (as `un-represent-ability.md` already carries), or prunes
it; optionally adds minimal front-matter to both surveys for uniform note headers.

## Routing
`discovery` (reference/direction) → orchestrator. Corpus-hygiene; owner decides
catalogue-or-prune.
