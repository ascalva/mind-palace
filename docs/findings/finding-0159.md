---
type: finding
id: finding-0159
status: routed           # open → routed → resolved | promoted
created: 2026-07-22
updated: 2026-07-22
links:
  - docs/findings/finding-0141.md                    # the dreamers: built, flag-off, never wired — the precedent
  - docs/build-plans/bp-092/plan.md                  # code-ingest CI-1: lane built, no enable path
  - docs/design-notes/track-board-and-deskcheck-gate.md  # the Follow-through / deskcheck gate this would amend
  - docs/design-notes/agent-workflow.md              # the graduate scope rule this would amend
ftype: direction         # a workflow-discipline amendment — owner/orchestrator call
route: orchestrator
resolution: null
---

# The enable path (the ON switch) is part of finishing work — flag-off ≠ delivered

## What

Owner ruling (2026-07-22): **a capability shipped with no way to turn it on is missing
functionality, not "dormant by design."** The code-ingest wave (bp-092..094) shipped the code
embed lane — but `[code_ingest].enabled` was inert (the loader has no `CodeIngestConfig`, nothing
reads it), the `code_sync` scheduler KIND was never enqueued, and there was no `palace` seed
command. Flipping the flag did nothing; the only way to run the seed was a raw
`build_code_corpus_sync().seed()` Python call. The lane's *value* — code as a first-class
semantic source (finding-0146) — was therefore undeliverable by the sealed work alone.

This is the SAME shape as finding-0141 (the dreamers: sealed, `[dream_rnd]=false`, never wired).
The plans deferred the enable wiring as "a deliberate, owner-visible later step" (note §2.7) — but
that made the ON switch itself an *absent* artifact, not a flipped-off one.

## Why it matters

"Flag-off" is a legitimate SAFETY DEFAULT (don't auto-run a heavy/irreversible op on merge). It is
NOT a license to omit the enable mechanism. Safety-gating and wired-to-run are ORTHOGONAL: ship it
gated OFF, but ship the switch. Today the workflow's guards do not catch an absent switch:
- The Follow-through "wired/delivered?" question can be answered "dormant by design" with a warrant
  and pass — even when *there is no switch to flip*.
- Graduation treats the enable path as optionally deferrable, so a plan's `write_scope` need not
  include the config schema / daemon-CLI wiring that turns the capability on.

## Proposed amendment (owner/orchestrator)

Make "the ON switch exists" a first-class part of the definition of done:
1. **Graduate scope rule** (agent-workflow / graduate skill): a plan that ships a capability MUST
   carry its enable path in `write_scope` — the config-loader schema that reads the flag, and the
   daemon-enqueue / CLI that runs it (gated off is fine). Deferring the switch is under-scoping,
   flagged at graduation.
2. **Follow-through "wired?" tightened** (dn-track-board-and-deskcheck-gate D5): "wired/delivered"
   means *the ON switch is built and a consumer CAN reach it*, not "the code is present, flag off".
   "Dormant by design" passes only for a flipped-off-but-PRESENT switch with a warrant — never an
   absent one. The word "dormant" is interrogated every time (pairs with F-WF5).
3. **Design-note "Wiring & enablement" section** (owner rule 2026-07-22, ALREADY ACTIONED): every
   design note carries a required §4 stating *how it wires* + a *"what it takes to flip it on"*
   subsection — always present (a fix says `N/A — live on merge`; else the wire + enable steps).
   Added to `docs/templates/design-note.md` this session so the ON switch is designed, never
   deferred. The promotion step is making it a checked contract (a gate that a note lacks §4, or
   its §4 is empty of the required subsection), amending dn-agent-workflow.
4. **Deskcheck = proven-working, and the board mislabels it** (owner sharpening 2026-07-22): a
   deskcheck is "here it is, working as expected" — it FINALIZES a track and cannot be claimed
   while the track still needs work to run ([[deskcheck-discipline]] updated). Two fixes: (a)
   `board.py`'s phase function labels a *sealed plan* "deskcheck-pending" — misleading; a complete
   plan whose track still has open build/enable work should read "sealed" (track not yet
   deskcheck-ready), with "deskcheck-pending" reserved for a demonstrably-working track awaiting the
   owner verdict; (b) stop saying "ready to deskcheck" on a mere seal (say it only when the track
   works). This is the code-ingest case: sealed CI-1..3, but the wiring (bp-098) + the proving seed
   run are owed, so the track is work-owed, not deskcheck-owed.

## Routing

`direction` → orchestrator batches to the owner for the workflow-design amendment. Concrete
instance already actioned: the code-ingest enablement wiring graduated as **"Plan B"**
(CodeIngestConfig loader schema + daemon enqueue gated on `enabled` + a `palace code-seed`
command) 2026-07-22. Durable owner rule captured in memory (`wiring-is-part-of-finishing`).
Promotion path: an amendment to dn-agent-workflow / dn-track-board-and-deskcheck-gate at the
owner's gate, warrant-linked here, flips this to `promoted`.
