---
type: track
slug: workflow
title: Workflow / tooling — the track board + the deskcheck gate
status: active
warrant: null
audit_refs: []
dod:
  - WF-1 the board substrate built (bp-096) — track coordinate, manifests, derived board
  - WF-2 the deskcheck gate built (bp-097) — the deskcheck record + verdict gate
  - the board enforced — derived TRACKS.md / DESKCHECK-QUEUE.md, owed-count surfaced (finding-0153)
backlog_deskcheck: null
links:
  - docs/design-notes/track-board-and-deskcheck-gate.md
  - docs/findings/finding-0153.md
---
# Track — Workflow / tooling (the track board + the deskcheck gate)

The identity card for the workflow track. **Scope:** make the tracks × phases board
and the deskcheck follow-through gate structural — the `track:` coordinate, the
`docs/tracks/` manifests, the derived board (`scripts/board.py`), and the deskcheck
verdict gate. Members are the artifacts declaring `track: workflow` (the design note
`track-board-and-deskcheck-gate` + plans bp-096/097).

**Definition of done:** WF-1 (the board substrate — this build) and WF-2 (the
deskcheck gate) land, and the board is enforced by derivation — TRACKS.md and
DESKCHECK-QUEUE.md are generated, and the owed-deskcheck count surfaces every session
(finding-0153).

**Owed deskcheck:** none standing yet — the workflow plans are in build; each enters
the deskcheck queue at its seal.
