---
type: build-plan
id: bp-080
track: sync-diac-dreamers
status: complete
design_ref:
  - docs/design-notes/synchronic-diachronic-dreamer.md
contract: builder
write_scope:
  - core/graph/census.py
  - core/dreaming/interpreters.py
  - tests/unit/test_census.py
  - tests/unit/test_census_lens.py
  - tests/integration/test_structural_panel.py
  - tests/integration/test_dream_rnd.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 250k
  actual:
    model: opus            # claude-opus-4-8, tier verified on return
    tokens: 176636
    tool_calls: 75
    duration_min: 18
    ratio: 0.71            # well-pinned; under estimate
    session_delta: "fresh post-reset pool; ran parallel with bp-081"
depends_on: [bp-079]
parallelizable_with: []
created: 2026-07-21
updated: 2026-07-21
links:
  - docs/design-notes/synchronic-diachronic-dreamer.md
  - docs/design-notes/magnetic-laplacian.md
  - docs/design-notes/temporal-retrieval-algebra.md
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — D-1: the ARROW-READ synchronic dispatch (the clock-free v1)

> Graduated from ratified `dn-synchronic-diachronic-dreamer` (§2.8 SD-8, §2.9 SD-9 as ADOPTED at
> ratification `44bbeec`, §3 D-1). The census computation rides the already-licensed Thread-C
> sweep (TRA §3 item 2 + ML §3 item 2) — no new census license is created here.

## 0. Mode & provenance

Investigation and planning produced this; implementation proceeds item-by-item on owner
approval. The oq-0021 ADMIT ruling was adopted by the owner's ratification (bless `44bbeec`);
this plan implements it as ruled. `proposed → ready` stays owner-only.

## 1. Objective

A synchronic dispatch whose census sense surfaces witnessed, arrow-literal claims (closed
influence loops, revision-effort asymmetries, reach-backs) through the structural panel behind
the R&D flag — and emits nothing when the census is empty.

## 2. Context manifest

1. `docs/design-notes/synchronic-diachronic-dreamer.md` — §2.3 (census-only directional sense;
   the flux-language prohibition), §2.8 (the ARROW-READ, verbatim), §2.9 (the ADOPTED
   vocabulary: records-not-causes, gauge-immune, silence-over-filler), F-SD9.
2. `docs/design-notes/magnetic-laplacian.md` — §2.4–2.5 (what the census measures: the
   gradedness defect, retro-citations), §2.7 (the census earns a v1 needing no operator; ML-b
   gauge caution), the F1–F5 falsifier inventory (ready-made fixtures).
3. `core/dreaming/interpreters.py` — whole file: the panel's lens pattern (thin adapter), claim
   kinds `BRIDGE/THEME/HOLE/THREAD` (:58-62), the evidence discipline the census lens joins.
4. `core/graph/composed.py` — the assembly surface the census reads over.
5. `core/temporal/spine.py` (:159-274) — certified cuts; every reading anchors one.
6. `core/dreaming/rnd.py` (:31-40) — `require_rnd_enabled`, the flag boundary this lands behind.
7. `tests/integration/test_structural_panel.py`, `tests/integration/test_dream_rnd.py` — the
   panel surface this plan extends; carried in write_scope because they pin it.
8. `docs/build-plans/bp-079/plan.md` — the DreamCharter this dispatch is an instance of.

## 3. Investigation & grounding

- **Q1 — does the Thread-C census sweep exist in code?** **No** — `grep -rln "census|Thread-C"
  eval/ ops/ scripts/` returns nothing (verified at graduation, `44bbeec`). The LICENSE exists
  (TRA §3 item 2; ML §3 item 2 — "the census rides the already-licensed Thread-C sweep, no new
  license"); the computation does not. This plan builds the census reader as the licensed
  computation's first implementation. Item 1 is therefore real work, not consumption.
- **Q2 — where does the panel accept a new lens?** `core/dreaming/interpreters.py` — the panel
  is the two-generation lens registry (":15-31"); claim-kind constants at :58-62; a census lens
  is a new thin adapter beside `bridge`/`hole`/`theme`/`thread`. The integration tests
  `test_structural_panel.py` / `test_dream_rnd.py` pin the panel's surface — carried in
  write_scope (retrofit rule).
- **Q3 — what data does the census read?** Citation edges (`X_cite`, via
  `ReferenceEdgeStore` — `core/complex/temporal.py` builds the citation complex per-commit) and
  supersession chains (`VersionStore` history). The builder confirms exact read paths at HEAD;
  reads are acquisition-side (outer ring, permanently — note §2.3 table) and anchor a certified
  cut.
- **Q4 — is the R&D flag wiring touched?** No — `require_rnd_enabled`
  (`core/dreaming/rnd.py:31-40`) already gates every new dispatch mode until the owner wires it;
  this plan lands BEHIND it and changes no wiring.

**Additional risks or questions surfaced during reading:** the census is "likely empty on
today's corpus" (note §2.8) — the fixtures carry the load; the owner-operational σ-sweep
(oq-0024) + a first live Thread-C run would turn that guess into a measurement (out of scope
here, noted §9).

## 4. Reconciliation

- `core/dreaming/interpreters.py` (claim kinds :58-62) — the panel gains census claim kind(s)
  beside the existing four → **cross-ref: extension**: the new constants cite note §2.9 and this
  plan; no existing lens or kind changes. The two carried integration tests extend with the
  census cases; no existing assertion weakens.

## 5. Write scope

New: `core/graph/census.py` (the combinatorial reader) + its unit tests + the lens's unit tests.
Carried existing: `core/dreaming/interpreters.py` (the lens registration + claim kinds — the one
surface this plan extends) and `tests/integration/test_structural_panel.py` /
`tests/integration/test_dream_rnd.py` — carried because they pin the panel surface this plan
moves. Deliberately OUT: `core/dreaming/rnd.py` (flag wiring untouched, Q4), the adjudicator,
every store module, `eval/` (the harness lane is not this plan), all design notes.

## 6. Interfaces pinned inline

- **The claim family (note §2.8, binding):** three claim shapes, each witnessed by
  construction — *influence loop* ("A cites B cites C cites A", witness = the edge set);
  *revision-effort asymmetry* ("this branch took three revisions where its sibling took one",
  witness = the chain positions); *reach-back* ("this note re-cites something younger than its
  own first authorship", witness = edge + both timestamps' chain evidence). Every claim carries
  edge sets / commit SHAs.
- **The vocabulary (§2.9, ADOPTED — binding):** (a) equal-citizen on the structural panel,
  adjudication unchanged; (b) records-not-causes — never "B shaped your thinking on A";
  direction narrated as time's residue; (c) gauge-immune quantities only — no spectral/flux
  phrasing exists in the lens; (d) empty census ⇒ ZERO claims (silence, never filler).
- **Legality (note §2.8):** synchronic only — point window at one certified cut; no rates
  without a declared clock (Rule CLOCK, `core/scope.py:666-675`); the dispatch is a
  `DreamCharter` (bp-079) whose instrument grant names the census handle.
- **Honest seam (note §2.3):** the census is exact, deterministic, gauge-immune; it emits
  nothing when empty; no ML-a gate-(ii) argument is made by this plan — if a dispatch
  demonstrably needs graded direction, that demonstration goes to the owner as a finding, and
  the operator is never designed in.

## 7. Items

### Item 4 — the census reader (continue family numbering from bp-079)

- **Objective:** exact combinatorial invariants over the composed assembly at a certified cut.
- **Files:** `core/graph/census.py`, `tests/unit/test_census.py`
- **Acceptance test:** on planted fixtures — a directed 3-cycle, an unbalanced diamond, a
  retro-citation — the reader enumerates each with its exact witness; on an arrowless control
  it returns empty; deterministic across runs; anchored cut recorded in every reading.
- **Falsifier:** any census output without a verifiable witness, or nondeterminism across two
  runs at the same cut (the census's whole claim is exactness).
- **Invariant(s):** read-only; no new license semantics (rides Thread-C as licensed); no
  spectral machinery imported (ML-a honored).
- **Touches stored data?** No (reads only; fixtures in unit tests).
- **Parallelizable?** Yes (with Item 5's scaffolding). **Depends on:** none in this plan.

### Item 5 — the census lens on the panel

- **Objective:** census claims join the structural panel behind the R&D flag, in the §2.9
  vocabulary.
- **Files:** `core/dreaming/interpreters.py`, `tests/unit/test_census_lens.py`,
  `tests/integration/test_structural_panel.py`, `tests/integration/test_dream_rnd.py`
- **Acceptance test:** the lens renders each fixture claim arrow-literally with its witness
  inline; a grep of the lens's vocabulary strings finds no causal phrasing ("influenced",
  "shaped", "led to") and no flux/spectral terms; panel adjudication over the extended kind set
  passes the carried integration tests; everything sits behind `require_rnd_enabled`.
- **Falsifier:** F-SD9 — a claim phrased as causation, a claim without a witness, or any claim
  emitted on the arrowless control.
- **Invariant(s):** existing lenses and claim kinds unchanged; interpreted-only output law
  binds; no wiring change to the R&D flag.
- **Touches stored data?** No.
- **Parallelizable?** No. **Depends on:** Item 4, bp-079 (the charter it dispatches as).

### Item 6 — the F-SD9 battery + the narrative-delta A/B (owner observation item)

- **Objective:** the ruling's falsifier as a permanent test; the live narrative delta surfaced
  to the owner.
- **Files:** `tests/unit/test_census_lens.py` (battery), plus an exhaust-lane report artifact
  (out-of-repo output; no repo file beyond the tests)
- **Acceptance test:** the full battery green — planted structures each surfaced with correct
  witness, zero claims on control; THEN one with/without-census A/B over the real corpus (same
  dispatch, same cut, admission toggled) rendered as a short comparison and placed on the
  exhaust lane for the owner (owner ask, 2026-07-21 capsule — an observation item, not a gate:
  the A/B's content does not block sealing).
- **Falsifier:** the A/B shows census claims crowding out or degrading existing panel claims —
  not a seal-blocker, but files a finding for the owner (the §2.9 re-rule path).
- **Invariant(s):** the A/B reads only; no surfacing of conditioned/hypothetical content (none
  exists yet — H-plans are later).
- **Touches stored data?** No.
- **Parallelizable?** No. **Depends on:** Items 4–5.

## 8. Math carried explicitly

- **The census invariants (directed cycles, unbalanced diamonds, reach-backs)** — *measures:*
  exact directed structure in the citation/supersession record — time's residue, enumerated
  with witnesses. *valid when:* computed over the composed assembly at one certified cut;
  combinatorial (gauge-immune by construction, ML §2.7b). *fails its keep if:* a claim lacks a
  reproducible witness, or the enumeration differs across runs at the same cut, or claims
  appear on an arrowless control.

## 9. Non-goals

No diachronic execution (SD-a parked; re-entry in finding-0126); no past-cut/RETRO dispatch
(SD-b); no magnetic operator or spectral direction (ML-a ratified; no gate-(ii) argument here);
no R&D flag wiring; no harness per-grant lane (dn-evaluation-harness's own track); not the
σ-sweep run (oq-0024 — owner-operational; its measurement is welcome input but gates nothing).

## 10. Stop-and-raise conditions

The census read path demands a store surface that doesn't exist (Q3 wrong) → spec-defect
finding, park; the panel's adjudicator needs modification beyond registering a kind →
stop-and-raise (adjudicator is out of scope); any pressure toward causal phrasing to make
narration "read better" → stop; that pressure IS the F-SD9 anti-pattern; a blessing → never.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| graded/"soft" direction ranking | census enumeration only | spectral ranking now (gauge-dependent phases; ML-b apophenia risk; deferral ratified) | a dispatch demonstrably needs it → the finding IS the ML-a gate-(ii) argument, owner rules |
| census claim kind granularity | one kind per claim shape (loop/asymmetry/reach-back) | a single CENSUS kind (loses per-shape adjudication signal) | adjudication data shows the split is noise |
| live Thread-C sweep scheduling | on-demand at dispatch | a standing scheduled sweep (no consumer for standing readings yet) | D-1 sealed + the owner wants continuous census telemetry |

## 12. Dependency & ordering summary

Items 4→5→6 (4 parallelizable with 5's scaffolding; 6 last). Depends on bp-079 (the charter).
All reversible-write tier; the only carried existing surface is the panel file + its two
pinning integration tests. Family sequencing: behind bp-069/070/071 and M0/S1 at the owner's
blessing; the owner-operational sweeps (oq-0024, first Thread-C run) are welcome before or
alongside — they gate nothing.
