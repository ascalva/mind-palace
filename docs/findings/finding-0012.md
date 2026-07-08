---
type: finding
id: finding-0012
status: routed
created: 2026-07-06
updated: 2026-07-08
links:
  - docs/design-notes/dialogue-ingest-and-recursion.md
  - docs/design-notes/supersession-lifecycle.md
  - docs/design-notes/recursive-strata.md
  - docs/audits/corpus-state-audit-2026-07.md
ftype: discovery
origin_plan: orchestrator
route: orchestrator
resolution: null
---

# finding-0012 — The supersession / dialogue-recursion dynamics are specified but wholly dormant

> **Triage 2026-07-08 (/triage):** routed → orchestrator. **Parked pending the forward build (Item 8** — blessing gate + `proposed → certified` + disposition authority + an active-projection consumer of `superseded()`) — normal roadmap sequencing, not a discrete owner question. Its cheaper "annotate the three notes as dormant-pending-Item-8" alternative folds into `owner-questions.md` **oq-0007**. Re-entry per §Re-entry condition below.

## What
Three DRAFT notes specify machinery that is unreachable from any live entry point:

- **Dialogue operation vocabulary** (`dialogue-ingest-and-recursion.md` §4):
  `core/recursion_ops.py` (`apply_operations`, `Supersede`/`AttachDefeater`/
  `RecordWarrant`, `ClaimOpStore`) exists and is tested (`tests/integration/test_dialogue_ops.py`)
  but has **zero non-test callers**; the injected `DialogueAnalyzer` defaults to a
  no-op (`core/recursion_ops.py:102-123`). The wired dialogue path
  (`DialogueCapture.capture`, `core/ingest/dialogue.py:60-64`) only stores the
  message as `authored-dialogue` and emits no operations.
- **Supersession certification layer** (`supersession-lifecycle.md` §2/§3/§6): the
  `proposed → certified` states, the blessing gate, disposition-authority recording,
  and the candidate score `s(C,D)` have **no code at all**.
- **Retrieval demotion**: `core/stores/versions.py` (VersionStore) and
  `core/stores/authored_supersession.py` are write-only in the live system —
  `core/ingest/sync.py:111` writes versions and `scripts/ingest_founding.py` writes
  authored-historical supersessions, but **no live consumer reads `superseded()` /
  `supersessions()` to demote content from the active retrieval projection**.
  `docs/PROGRESS.md:1547` concedes: "nothing demotes from retrieval yet."

PROGRESS tracks this as "Item 8 — Next" (`:1451`, `:1543-1549`).

## Why it matters
The note prose and tracking language read as though dialogue corrections and
supersession flow at ingest time. They do not. The system captures enhanced
provenance (versions, claim-ops, authored-historical links) but acts on **none** of
it in retrieval — a reader could reasonably assume an active supersession pipeline
that does not exist. The git trail corroborates unresolved design here
(`43eb3db` "Added supersession edges, but stop to re-consider type overload").

## Re-entry condition
Item 8 lands (blessing gate + `proposed → certified` + disposition authority + an
active-projection consumer of `superseded()`), OR the three notes are annotated
"specified, dormant-pending-Item-8" so no reader assumes corrections flow today.

## Routing
`direction` → orchestrator. A present-but-not-wired subsystem the tracking record
implies is active; owner rules on Item-8 sequencing.
