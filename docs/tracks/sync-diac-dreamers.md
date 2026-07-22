---
type: track
slug: sync-diac-dreamers
title: Sync/diac dreamers — D-0 / D-1 / H-0 / H-1 / H-2
status: active
warrant: null
audit_refs: []
dod:
  - D-0 / D-1 / H-0 / H-1 / H-2 dispatch machinery sealed (bp-079 / 080 / 081 / 082)
  - the wire-or-accept-dormant decision resolved (finding-0141)
backlog_deskcheck: the sealed dispatch machinery + that it is NOT wired ([dream_rnd]=false, f-0141); decision owed — wire live, or accept dormant
links:
  - docs/design-notes/synchronic-diachronic-dreamer.md
  - docs/findings/finding-0141.md
---
# Track — Sync/diac dreamers (D-0 / D-1 / H-0 / H-1 / H-2)

The identity card for the synchronic/diachronic dreamers track. **Scope:** the
DreamCharter dispatch record, the materialization boundary, and the H-series dream
phases. Members are the artifacts declaring `track: sync-diac-dreamers` (the design
note + plans bp-079/080/081/082, all sealed).

**Definition of done:** the dispatch machinery is sealed AND the owner has made the
wire-or-accept-dormant decision (finding-0141) — sealing alone does not close this
track (the Q5 lesson: "sealed" was wrongly treated as terminal).

**Owed deskcheck (standing):** demo the sealed dispatch machinery and show that it is
NOT wired (`[dream_rnd]=false`, finding-0141); the decision owed is to wire it live or
accept it dormant.
