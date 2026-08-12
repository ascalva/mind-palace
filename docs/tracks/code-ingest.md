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
  - CI-wiring the ENABLE path — CodeIngestConfig + daemon enqueue + `palace code-seed` (bp-098, warrant finding-0159)
  - the seed run PROVES it works — code is actually embedded + retrievable (not just built); owner-visible run
  - integrator densification (finding-0151) — design-pass, FABLE, after the build plans
backlog_deskcheck: "The vector-membership arc (dn-vector-membership-store; bp-151 → bp-155 → bp-152 → bp-153, all merged) is READY TO DESKCHECK on bp-153's merge. Demo: `palace code-rebuild --dry-run` reporting the measured factor at the live cut (2.280x over 1,663 versions: 52,200 chunks vs 22,897 atoms, 15,186-atom carry-forward seed); the standing `|M|/|V|` gauge reproducing it after a run; the re-homed incompleteness probe reading fibers instead of the shed `('','')` tuple. NOTE the live rebuild itself has NOT run — it is owner-gated behind the deploy (issue #39), so the deskcheck is of the machinery + the measurement, and the arc is not closed until the live run lands. The REST of the code-ingest track (bp-095, the seed run, integrator densification) remains work-owed, not deskcheck-owed."
links:
  - docs/design-notes/code-ingest-pipeline.md
  - docs/findings/finding-0151.md
  - docs/findings/finding-0159.md
  - docs/build-plans/bp-098/plan.md
---
# Track — Code-ingest (the code embed + retrieval pipeline)

The identity card for the code-ingest track. **Scope:** make code a first-class
semantic source — embedded (source + docstrings + comments), retrievable, and wired
into the reference/geometry machinery. Members are the artifacts declaring
`track: code-ingest` (the design note `code-ingest-pipeline` + plans bp-092..095).

**Definition of done** (a deskcheck evaluates against this): the four CI plans land AND the
**enable wiring** (bp-098 — the ON switch, finding-0159) is built AND the **seed run proves it
actually works** (code demonstrably embedded + retrievable, not merely built — an owner-visible
run) AND the integrator densification (finding-0151) is resolved. A deskcheck is "here it is,
working as expected" ([[deskcheck-discipline]]); this track cannot be deskchecked while it only
*could* work.

**Owed:** WORK, not a deskcheck. bp-092/093/094 are sealed but the track is still in **build/enable**
— bp-095 (gated on M-C4), bp-098 (the wiring), the seed run, and integrator densification remain.
It becomes deskcheck-ready only once it demonstrably ingests code. Do NOT surface this as
"deskcheck-owed" until then; surface it as work-owed.

**One ARC inside the track is deskcheck-ready** (bp-153, 2026-08-12): the vector-membership store —
`dn-vector-membership-store`, plans bp-151 → bp-155 → bp-152 → bp-153 — is a complete three-plan
family whose machinery and measurement can be shown working. It is carried in
`backlog_deskcheck` above rather than by flipping the track's phase, precisely because the rest of
the track is still work-owed and a track-level flip would over-claim. ⚑ The arc's own closing act,
the LIVE rebuild, has not run: it is owner-gated behind the deploy (issue #39). So the deskcheck is
of the machinery + the measured baseline, and the arc is not closed until the live run lands.
