---
type: finding
id: finding-0013
status: open
created: 2026-07-06
updated: 2026-07-06
links:
  - docs/design-notes/the-edge-model.md
  - docs/design-notes/recursive-strata.md
  - docs/design-notes/recursive-strata-amendment.md
  - docs/design-notes/build-plans/edge-and-supersession-build-plan.md
  - docs/design-notes/build-plans/sacred-boundary-build-plan.md
  - docs/audits/corpus-state-audit-2026-07.md
ftype: spec-defect
origin_plan: orchestrator
route: orchestrator
resolution: null
---

# finding-0013 — Edge / supersession notes and plans assert mechanisms the code realizes differently or not at all

## What
Five concrete note/plan ↔ code contradictions in the edge/supersession area, all
citation-verified in the 2026-07 audit:

1. **Assertion-authority "field" that isn't one.** `the-edge-model.md` §3 presents
   assertion authority as a per-edge typed field `{geometry, dreamer-proposed,
   verdict-certified}`. No such field or enum exists — the `Edge` dataclass
   (`core/stores/edges.py:61-72`) has none. Item 7 deliberately realized authority
   as **store-identity** (which store an edge lives in), not a dead enum.
2. **A cross-ref that is false to code.** `recursive-strata.md:45` cites supersession
   as "built as `SUPERSEDES`, `core/stores/edges.py`". The `SUPERSEDES` rel-type was
   **removed** (`core/stores/edges.py:33` "Do not re-add"). This is exactly the
   `recursive-strata-amendment.md` §1 fix — still unapplied.
3. **"EdgeStore refuses supersedes" overclaim.** `edge-and-supersession-build-plan.md`
   (lines 343, 525) and `core/complex/build.py:149` say the `EdgeStore`
   "forbids/refuses" a `supersedes` rel-type. It does not — `EdgeStore.add()`
   (`core/stores/edges.py:87-99`) accepts any `rel_type` string. The real protection
   is *no live writer* + *no `build_complex` handle* (sound, and tested at
   `tests/integration/test_edge_partition.py:89-95`) — but the "store refuses"
   phrasing is not literally true.
4. **Stale plan status.** `sacred-boundary-build-plan.md` (lines 3-7, 700-707)
   declares "Item 6 PLANNING ONLY / nothing implemented," but `core/stores/versions.py`
   exists and is wired (`core/ingest/sync.py:111`); `edges.py:30-33,122` and the
   later edge plan both treat Item 6 as landed.
5. **Stale tracking claim.** `docs/PROGRESS.md:984-986` states the `DERIVED_STRATUM`
   reservation was "undone; the enum has no such label," but `core/provenance.py:54`
   has it reserved.

## Why it matters
Items 1–3 are load-bearing partition claims (Invariant-2-adjacent). A note that says
"the store refuses X" while the store accepts X (the protection living elsewhere)
invites a future edit to rely on a guarantee that isn't there. Items 4–5 are stale
status/tracking that distorts the completion picture.

## Re-entry condition
Apply the `recursive-strata-amendment.md` edits (§1/§5); reconcile `the-edge-model.md`
§3 wording to store-identity; correct the "EdgeStore refuses" phrasing to
"no writer + no handle"; refresh the two stale status/tracking lines. (All are
denylisted design-note / owner-gated edits — surfaced here, not applied.)

## Routing
`spec-fidelity` → orchestrator. Note/plan-vs-code contradictions; several edits fall
on owner-only or denylisted surfaces.
