---
type: build-plan
id: bp-095
track: code-ingest
status: ready
design_ref:
  - docs/design-notes/code-ingest-pipeline.md
contract: builder
write_scope:
  - eval/harness/**
  - eval/code_sf_lens.py
  - tests/unit/test_code_sf*.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 120k
  actual: null
depends_on:
  - bp-092
  - bp-093
  - bp-094
parallelizable_with: []
created: 2026-07-21
updated: 2026-07-21
links:
  - docs/design-notes/code-ingest-pipeline.md
  - docs/design-notes/fiber-geometry.md
re_entry: "M-C4 verdict = informative (bp-093 journal) — if degenerate, this plan is superseded by a finding, never built"
supersedes: null
superseded_by: null
warrant: docs/findings/finding-0146.md
---

# Build Plan — CI-4: the S↔F code↔design lens (M-C7, read-only survey)

> **Every section below is required.** N/A is an accountability act.

## 0. Mode & provenance

Graduated 2026-07-21 from ratified `dn-code-ingest-pipeline` §3 CI-4 with its DOUBLE gate
minted into front matter: `depends_on` bp-092+bp-093+bp-094 AND the `re_entry` condition —
**bp-093's M-C4 verdict must read "informative."** If M-C4 is degenerate, this plan is
flipped `superseded` on a finding (F-CI4 / PD-C re-entry), never built. Minted now anyway
so the program's tail is visible (completion-claims honesty — no un-minted stage hiding
behind a "wave complete").

## 1. Objective

First read of the S↔F mismatch instrument for the code↔design pair: undocumented-realization
and drift counts (M-C7) as a census-adjacent, read-only, records-not-causes survey.

## 2. Context manifest

1. `dn-code-ingest-pipeline` §2.4 (the two mismatch readings), §2.8 M-C7, F-CI4.
2. `dn-fiber-geometry` §2.2 (the S↔F mismatch definition; the one-sidedness caveat),
   §2.6 M2 (the mismatch-density protocol this instantiates for the code pair).
3. `core/graph/composed.py` (`edge_classes` attribution) + the reference store's resolved
   F-edges (bp-094's product).
4. bp-093's journal — the M-C4 verdict (the gate) + the cosine-distribution baselines.

## 3. Investigation & grounding

- **Q1 — both halves exist by the time this runs:** S spans code↔docs once bp-092 seeds
  (computed, kernel-side — `dn-fiber-geometry` §2.0: S is computed, not recorded); F-edges
  code↔corpus are bp-094's resolved mints. The lens is a join + threshold read, no new
  machinery.
- **Q2 — the two readings (note §2.4, verbatim):** *resemblance without citation* (high
  cosine, no F-edge) = undocumented realization; *citation without resemblance* (F-edge,
  low cosine) = drift. Working σ from bp-093's distributions, recorded per reading (CN-1
  index discipline).
- **Code does not settle:** the surfacing surface (census panel vs a standalone eval
  report) — default: eval-side report only; census-panel entry is a later oq-0021-shaped
  vocabulary ruling, not this plan's.

**Additional risks:** an empty/thin first read is LIKELY (young F-edge population) — a null
parks the lens as vocabulary (the note's own grading), files the finding, seals the plan.

## 4. Reconciliation

N/A — nothing corrected or extended; a pure consumer of sealed surfaces.

## 5. Write scope

Eval-side only; read-only against every store. OUT: core/**, ops/**, all stores, the
census/dreamer surfaces (no narration wiring — records-not-causes discipline; surfacing
beyond the eval report is explicitly not licensed).

## 6. Interfaces pinned inline

- **Reading protocol:** for each (code chunk, note chunk) pair above/below the working σ:
  join against resolved F-edges (code↔corpus, all four corpus-target ref_types); emit the
  two mismatch sets with witnesses (paths, edge ids, cosines, the σ and cut used).
- **Honest-seam law:** zero claims when either population is empty; silence never narrated
  as structure (`dn-fiber-geometry` §2.6 falsifier discipline, inherited verbatim).

## 7. Items

### Item 1 — the lens + the M-C7 first read (read-only)

- **Objective:** implement the join/threshold reading; run it at a certified cut; record
  both mismatch tables with witnesses in the journal + an eval report.
- **Files:** `eval/code_sf_lens.py`, `eval/harness/**`, tests, journal.
- **Acceptance test:** reproducible run (pinned σ, cut, embedder version); every emitted
  claim carries its witness tuple; empty-population fixture emits zero claims.
- **Falsifier:** a claim without a witness, causal phrasing in any output, or claims from
  an empty population ⇒ the lens violates the records-not-causes discipline — fails review.
- **Invariant(s):** read-only everywhere; mirror untouched (code rows reached via explicit
  CODE-inclusive provenance sets, never MIRROR_READABLE).
- **Touches stored data?** no. **Parallelizable?** n/a. **Depends on:** the front-matter
  gates.

## 8. Math carried explicitly

- **S↔F mismatch densities (code↔design)** — *measures:* disagreement between computed
  similarity and recorded citation across the code/doc boundary. *valid when:* one embedder
  version; F-population non-trivial; σ pinned and reported. *fails its keep if:* readings
  are all-null across cuts once F-edges exist in volume — then the lens parks as vocabulary
  (a finding, per the note's grading), not a tuned instrument.

## 9. Non-goals

No census/narration wiring. No thresholds tuned to manufacture signal. No correlator work.
No new edges minted from lens output (readings are readings).

## 10. Stop-and-raise conditions

The M-C4 gate unread or degenerate (do not start; flip per `re_entry`). Any pressure to
surface into the dreamer/census without the vocabulary ruling. Anything requiring a write
outside eval.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| census-panel surfacing of the two readings | eval report only | panel entry now (needs the oq-0021-shape vocabulary ruling) | the owner's ruling at a later /triage |

## 12. Dependency & ordering summary

Last of the CI family: after bp-092 (S over code), bp-094 (resolved F), bp-093 (the M-C4
gate + σ baselines). Single item. With this sealed — or superseded on a degenerate M-C4 —
the CI program's four stages are all DISPOSED; nothing un-minted remains behind it.
