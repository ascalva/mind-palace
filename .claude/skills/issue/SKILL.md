---
name: issue
description: How ANY agent files and tends a GitHub issue — findings, questions, investigations, and standing rulings are issues now (atomic numbering ended finding-id collisions); the label taxonomy (type/route/track/parked), park-with-re-entry, and the promotion path into design-note PRs.
---

# Filing an issue — standard operating procedure

Since 2026-07-28, discoveries do not become `docs/findings/` files and owner questions do
not go into an inbox file — **they become GitHub issues**. Atomic numbering ends the
finding-id collision plague; labels carry the typing and routing; the owner peers through
the same glass he merges through. `docs/findings/` and `docs/inbox/owner-questions.md` are
frozen history.

## File it

`gh issue create --title "<crisp claim, not a category>" --label <labels> --body-file -`

**Title** states the finding itself ("the embedder starves under critical battery"), never
a vague topic. **Body** is the old finding discipline, unchanged in substance: what was
observed (with evidence — paths, measurements, run ids), why it matters, the proposed
direction if one exists, and every id glossed inline. Cite frozen findings by path when
relevant.

## The label taxonomy

- **Type** (exactly one): `type:question` (needs a decision, typically the owner's) ·
  `type:investigation` (something to establish or falsify) · `type:defect` (the record or
  the code is wrong) · `type:direction` (building revealed something that bears on design)
  · `type:ruling` (records a standing owner ruling — filed closed, it IS the record) ·
  `type:blocker` (work cannot proceed and nothing can be parked — rare).
- **Route** (exactly one): `route:owner` · `route:orchestrator` · `route:builder`. The old
  rule survives: settle what you can against code and spec (`route:builder`, then close
  with the resolution); escalate design/math/direction to `route:orchestrator`; only what
  genuinely needs the owner gets `route:owner`.
- **Track**: `track:<slug>` — mint lazily on first use, one per issue where clear, none
  where ambiguous.
- **`parked`**: legal ONLY if the body carries the exact re-entry condition that reopens
  it. A parked issue without one is disallowed — same law as ever.

## Never block, never collide

Park criteria with re-entry and proceed — an unanswered `type:question` never stalls work
(carry a stated default-if-unanswered). Never mint a finding-id or edit `docs/findings/`;
the counter is GitHub's now.

## Promotion and closure

A `type:direction`/`type:defect` that changes design promotes the same way as ever, through
the gate: a **design-note proposal PR** warrant-linked to the issue. The PR body says
`closes #N`; the owner's merge is simultaneously the ratification and the resolution. For
everything else: close with the resolution in a comment (link or text) — a closed issue
with no stated resolution is a false green. Related: the **pr** skill (the door), CLAUDE.md
§Routing.
