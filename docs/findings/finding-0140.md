---
type: finding
id: finding-0140
status: promoted
created: 2026-07-21
updated: 2026-07-21
links:
  - docs/brainstorms/edge-dynamics-vector-field.md   # "w_F (similarity strengths)" — the mislabel
  - docs/brainstorms/fiber-chain-grammar.md          # "F*·(C|D)" glossed as similarity hops
  - docs/brainstorms/clock-curvature.md              # "F-edges carry churn-dependent exposure" (similarity intended)
  - docs/design-notes/fiber-geometry.md              # §2.0 FG-0 — the resolution (S/F/D/C move alphabet)
  - docs/design-notes/agent-taxonomy.md              # the ratified semantics: F = citation (:206-210)
ftype: discovery
origin_plan: orchestrator            # session-39 dispatched fable design pass (fiber-geometry)
route: orchestrator                  # design
resolution: null
---

# The fiber letter F means "citation" in the ratified algebra but "similarity" in the 2026-07-21 brainstorm layer

## What

The ratified/built alphabet pins **F = citation/warrant** edges (`core/scope.py:158` — "F =
citation, D = supersession, C = causal-witnessed"; dn-agent-taxonomy §2.5; ReferenceView's grant
is `E={F}` over `X_cite`). Similarity is **not an E-fiber at all**: cosine edges are computed
from the embedding kernel, and semantic reading is licensed by kernel-carrying Σ
(dn-capability-scope §2.4), with `E_sim` a distinct assembly class beside `E_proven`
(`core/graph/composed.py:51-52`).

The three 2026-07-21 session-39 brainstorm capsules consistently use **F for similarity**:
"w_F (similarity strengths)" and "F is dense, ~undirected, cosine-weighted"
(`edge-dynamics-vector-field.md`); "F*·(C|D) — any run of similarity hops"
(`fiber-chain-grammar.md`); "F-edges carry churn-dependent exposure"
(`clock-curvature.md`, path-invariance capsule). Consequently several brainstorm claims are
mistyped as written: the "F↔C mismatch field" is the **S↔C** (similarity-vs-causal) mismatch;
the "three vector fields" are really S plus the recorded classes; and ratified
dn-velocity-instruments already keeps the two substrates carefully apart (X_cite = the
invariant floor; the similarity backbone = INTERPRETED-class per A7) — the brainstorms' merge
runs against that ratified separation.

## Why it matters

A future design or build pass grounding on the brainstorm capsules verbatim would compute the
wrong object (e.g. a "w_F velocity" on X_cite when the claim meant cosine drift, or a mismatch
lens comparing citation-vs-causal when the payload is similarity-vs-causal). The collision also
silently under-counts the edge classes (four durable classes, not three), which changes the
sheaf/bundle operator question dn-fiber-geometry §2.5 rules on.

## Re-entry condition

Resolved by `dn-fiber-geometry` §2.0 (FG-0): the canonical chain-move alphabet is
**Σ_move = {S, F, D, C}** with S = similarity (kernel-licensed, not an E letter) and F =
citation (unchanged ratified semantics). On that note's ratification this finding flips to
`promoted`; until then, any reader of the three capsules applies the FG-0 re-reading. No
brainstorm text is edited (capsules are records); the correction lives here and in FG-0.

## Routing

`design` → orchestrator. No owner decision required beyond ratifying dn-fiber-geometry (FG-0
is definitional hygiene, not a taste call); flagged so /triage annotates the capsules' readers
rather than the capsules.

## Triage annotation (2026-07-21, session-39 /triage)
Routed → orchestrator (design/discovery). This is a promotion candidate: the resolution is
already authored as `dn-fiber-geometry` §2.0 (FG-0 — the canonical Σ_move={S,F,D,C} alphabet),
which is warrant-linked here. On the owner's ratification of `dn-fiber-geometry`, this finding
flips `routed → promoted`. No separate owner question — the fix rides that one ratify decision.
Until then the three warrant brainstorms keep their as-written (mislettered) text; the note
re-reads them, per A8 (never edit a ratified/consumed artifact silently).

## Resolution (2026-07-21) — PROMOTED on ratification
`dn-fiber-geometry` ratified by the owner (bless `fbea48d`), adopting §2.0 FG-0 (the canonical
`Σ_move = {S, F, D, C}` alphabet). The alphabet correction is now ratified design; the three
warrant brainstorms are re-read under it (never edited — A8). Finding closed as `promoted`.
