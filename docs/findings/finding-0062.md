---
type: finding
id: finding-0062
status: routed
created: 2026-07-13
updated: 2026-07-13
links:
  - docs/brainstorms/core-query-protocol.md # the full thread this finding registers
  - docs/findings/finding-0059.md # doc→doc blindness instance
  - docs/findings/finding-0061.md # the stale-baseline class a reference graph would guard
  - core/stores/reference_edges.py # the live substrate (61k edges)
ftype: direction
origin_plan: orchestrator
route: orchestrator
resolution: null
---

# No standard query protocol / agent-facing surface over the core's strata — the reference graph is live but unreachable and code-anchored

## What

Three connected gaps, surfaced in the 2026-07-13 chat (full thread + math in
`docs/brainstorms/core-query-protocol.md`):

1. **The reference substrate is live but agent-unreachable.** `data/reference_edges.sqlite`
   holds ~61,380 edges, indexed on `corpus_ref`/`code_path`/`commit_sha`, with `ref_type`
   and `source_line` — a "where/how-many references to doc X" answer is one query away. But
   nothing exposes it to a workflow agent: the store's API is minimal (`all`, `for_commit`,
   `count`), and the store lives in the sealed core's `data/`, on the far side of the
   sacred boundary from the build-time plane.
2. **It is code-anchored.** Only `corpus_to_code`/`code_to_corpus` edges exist; there is no
   `corpus_to_corpus` (doc→doc) edge — a plan's `design_ref` citing a note, a finding's
   `links`/`[[name]]`. That doc→doc edge is exactly the finding-0059 blindness (a note's
   stale count cited by two plans, invisible) and the finding-0061 class.
3. **The deeper gap: no shared query protocol.** Every agent (orchestrator, ambassador,
   sensors, a proposed reference agent) is a *scoped client of the core* speaking an ad-hoc
   interface. The existing `MirrorView/ObservedView/OpsView/EffectView` are partial,
   capability-scoped windows — the seed of a **typed core-query algebra** that does not yet
   exist as one language. A deterministic **single-stratum query server** (no model,
   one stratum, lateral edges only) falls out as its simplest, cheapest, fully-attestable
   sentence.

## Why it matters

The reference graph would retire a whole *class* of agent friction (findings 0059, 0061 —
stale-baseline / find-the-file toil) by making "who cites this, and where" a lookup instead
of a re-grep an agent has to *think* about. It also dogfoods a capability Ouroboros already
builds live. But reaching it from the build-time plane is a **sacred-boundary** question
(plane-crossing), and doing it well means designing the query protocol and its capability
scopes — not bolting on a one-off accessor. This is design work, not a builder task.

## Re-entry condition

**Fable-guarded (owner rule, 2026-07-13).** The brainstorm → design-note pass is fable-tier
work — open architecture, unpinned interfaces, a cross-plane boundary ruling, and a math
framing (the time→gradient/harmonic collapse) that feeds `edge-dynamics` Lane B — and must
NOT be drafted at opus/sonnet. Re-entry: the owner opens a fable design session over
`docs/brainstorms/core-query-protocol.md`; it likely graduates TWO notes (an architecture
note: the core-query protocol + client-scope model; a math note / Lane B feed). Optionally,
the **doc→doc extractor** may be split out as a small independent plan to retire the
finding-0059/0061 class before the full protocol is designed — the owner's call at the
design pass.

## Routing

`direction` → orchestrator (architecture/design direction). Non-blocking; nothing in the
queue depends on it. It waits for owner appetite and a fable session; this finding flips
`→ promoted` when the design note(s) are drafted and ratified.
