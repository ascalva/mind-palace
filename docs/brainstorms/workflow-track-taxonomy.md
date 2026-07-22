# Workflow & track taxonomy — kinds of tracks, statuses, findings-as-tracks, stakes-based routing

Brainstorms on the shape of the workflow itself: what a track IS, the legitimate
statuses, whether findings are a track, and how findings route by stakes. Feeds the
next Fable design-pass amending dn-track-board-and-deskcheck-gate.

## 2026-07-22 18:49 UTC

```capsule
topic: workflow-track-taxonomy
date: 2026-07-22

decisions:
  - A DESKCHECK = "here it is, working as expected" — PROOF it works, it FINALIZES the track.
    A track is deskcheck-ready only if provably live+working, OR fully built with the only
    remaining step being the owner flipping it on. "Sealed / built with the potential to work"
    is NOT deskcheck-ready — it is work-owed. Never say "ready to deskcheck" on a mere seal.
  - WIRING is part of finishing: if it was worth building, it is worth wiring. The enable path
    (config schema + daemon/CLI, the ON switch) must EXIST as part of the deliverable, even if
    flagged off. The only legit "off" is WIRED-but-flag-off (owner-flippable), never unreachable.
  - "DORMANT-BY-DESIGN" is BANNED — it pretends a built-but-unwired thing is done.
  - "DEFERRED" is a LEGITIMATE track status: when we don't have all the answers, pause the track
    with a re-entry condition — honestly NOT done, an open/parked state (Track-G/effectors is
    deferred pending a design decision on whether/how to wire the effectors).
  - Design notes now carry a REQUIRED §4 "Wiring & enablement" (how it wires + what it takes to
    flip on; present even when a fix says `N/A — live on merge`).
  - NOTHING is currently deskcheck-ready — including the workflow track itself (still being defined).

parked:
  - decision: two KINDS of track — DELIVERABLE (has a DoD → wired → demonstrated → deskchecked →
      CLOSED) vs STANDING/PERMANENT (never closes; a continuous lane measured by throughput, not
      completion — e.g. findings, maybe ops/maintenance).
    default: today all tracks are treated as deliverable (the board renders one way).
    re_entry: the Fable design-pass decides the two kinds + how the board renders each (DoD-vs-flow).
  - decision: track STATUS vocabulary = {active, deferred, standing/permanent, closed}; board.py +
      dn-track-board-and-deskcheck-gate D2 replace the (banned) `dormant-by-design` phase with a
      `deferred` phase (open/paused, never deskcheck-owed) + a standing/permanent kind.
    default: board.py knows only active/dormant-by-design/... and mislabels `deferred` today.
    re_entry: finding-0159's board amendments are built.
  - decision: FINDINGS as a track (or lanes) — a finding is not only a routing slip but a WORK ITEM
      with a done-state. Category axis = ftype: bug (codebase/spec-defect) · structural
      (spec-defect/design) · worth-calling-out (discovery/direction) · handled-in-flight (resolved).
      A resolved finding = a HANDLED task in that lane.
    default: findings live flat in docs/findings/ with ftype + route, no track/lane view.
    re_entry: the design-pass decides whether findings become a standing track (one lane or per-category).
  - decision: THREE-TIER finding routing (the missing middle is the ORCHESTRATOR lane) —
      (1) BUILDER resolves in its zone; (2) ORCHESTRATOR handles LOW-STAKES findings (reversible AND
      mechanical AND within existing design AND no safety bright line) — logged, not silent (commit +
      finding record + report line, auditable); (3) OWNER decides high-stakes (design/taste/
      irreversible/safety). The moment any tier-2 condition fails, it is tier-3.
    default: today routing is binary (builder-resolves OR orchestrator-batches-to-owner); the
      orchestrator's autonomous-handle lane is de-facto (it fired on f-0156/0157/the φ_code
      attestations this session) but not formalized.
    re_entry: the design-pass formalizes the tier-2 boundary + the logging/audit requirement.

open_questions:
  - How does the board render a standing track (throughput: raised/handled/routed/promoted) vs a
    deliverable track (DoD/deskcheck)?
  - Exactly where is the tier-2 (orchestrator-handles) boundary, and what audit surface proves the
    autonomous lane isn't a black box?
  - Findings-as-track: one standing lane, or per-category lanes (bug / structural / callout /
    handled)? Do findings gain a `track:` key (P-WF5 was parked "optional")?
  - Does the deskcheck gate / board need a distinct treatment for standing vs deliverable tracks?

next_steps:
  - A FABLE design-pass to finalize this taxonomy — amend/extend dn-track-board-and-deskcheck-gate
    (the two track kinds, the {active/deferred/standing/closed} statuses, findings-as-track,
    three-tier routing), warrant-linked to finding-0159.
  - Then build finding-0159's amendments structurally (design-note §4-present gate; Follow-through
    "wired?" tightening; board.py: replace dormant phase with `deferred` + a standing kind; per-plan
    "deskcheck-pending" mislabel fix).
  - (Independent) bp-098 — the code-ingest enable path — bless + build.

references:
  - docs/findings/finding-0159.md (the ON-switch-is-finishing ruling + the 5 amendments)
  - docs/findings/finding-0141.md (the dreamers: built-not-wired precedent)
  - docs/design-notes/track-board-and-deskcheck-gate.md (the workflow note this amends)
  - docs/build-plans/bp-098/plan.md (the code-ingest enable path — the concrete instance)
  - memory: wiring-is-part-of-finishing, deskcheck-discipline (the durable rules)
```
