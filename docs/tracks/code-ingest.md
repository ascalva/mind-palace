---
type: track
slug: code-ingest
title: Code-ingest — the code embed + retrieval pipeline
status: active
warrant: null
audit_refs: []
dod:
  - CI-1 embed lane (code + docstrings + comments), Provenance.CODE (bp-092)
  - CI-2 retrieval / geometry proof (bp-093)
  - CI-3 reference resolvers + inherits/calls edges (bp-094)
  - CI-4 the S↔F lens (bp-095)
  - integrator densification (finding-0151) — design-pass, FABLE, after the build plans
backlog_deskcheck: null
links:
  - docs/design-notes/code-ingest-pipeline.md
  - docs/findings/finding-0151.md
---
# Track — Code-ingest (the code embed + retrieval pipeline)

The identity card for the code-ingest track. **Scope:** make code a first-class
semantic source — embedded (source + docstrings + comments), retrievable, and wired
into the reference/geometry machinery. Members are the artifacts declaring
`track: code-ingest` (the design note `code-ingest-pipeline` + plans bp-092..095).

**Definition of done** (a deskcheck evaluates against this): the four CI plans land
(embed lane → retrieval proof → reference resolvers → S↔F lens) AND the integrator
densification design item (finding-0151) is resolved — a FABLE design-pass owed after
the build plans, so the deskcheck cannot pass while it is open.

**Owed deskcheck:** none standing yet — the build plans are still `ready`/in build;
each enters the deskcheck queue at its seal (`build → audit → deskcheck`).
