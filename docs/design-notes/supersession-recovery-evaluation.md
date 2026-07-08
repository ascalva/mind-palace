---
type: design-note
id: dn-supersession-recovery-evaluation
status: draft
created: 2026-07-06
updated: 2026-07-06
links:
  - docs/findings/finding-0021.md                  # warrant: the episode + ground truth
  - docs/audits/archive-recommendation.md          # source of the labeled set
  - docs/design-notes/supersession-lifecycle.md
  - docs/design-notes/the-edge-model.md
  - docs/design-notes/dream-phase-rnd-charter.md   # the flag-gated lane this runs in
  - docs/design-notes/dreamer-quality-suite-evaluation.md  # the harness family this joins
  - docs/design-notes/holistic-testing-and-emergent-behavior.md
supersedes: null
warrant: docs/findings/finding-0021.md
---

# Supersession Recovery Evaluation: Can the Dreamer Rediscover Known Edges?

## 1. Purpose and scope

A falsifiable, automatable test of the supersession-candidate machinery, using
ground truth the system produced about itself. The corpus-maintenance pass of
2026-07-06 (finding-0021) yielded two owner-accepted supersession edges and seven
documented high-overlap negatives across the design-note corpus. The test: given
that corpus **with all supersession information scrubbed**, does the Dreamer
propose the same (or defensibly similar) edges — and, harder, does it correctly
*decline* to propose edges for the additive pairs?

The test built itself: the labeled set was produced by real reasoning over real
documents, with rationales, and the owner's certify/decline decisions are the
verdicts. What this note adds is the machinery to run it repeatably: the scrubbed
fixture, the machine-readable answer key, the protocol (two conditions, leak
control), scoring, and harness wiring.

Out of scope: unparking Item 10 (Ollivier-Ricci scoring — its re-entry conditions
stand and v1 needs no curvature); Track L (this is a fixed-corpus offline eval,
not longitudinal); any ratification or status change to the notes under test.

## 2. Why this test is worth having

- **Clear expectations, self-derived.** Two positives with a difficulty gradient
  (one easy: all signals present; one hard: no chronology — same commit batch),
  seven negatives whose *extends-vs-supersedes* discrimination is the genuinely
  hard judgment. Expectations are written down before any run.
- **It tests the designed pipeline shape** — cheap candidate generation over the
  graph, expensive interpreter reasoning only on the shortlist, proposals (never
  assertions) compared against verdicts — on the smallest real corpus available.
- **The answer key grows organically.** Every future owner-certified supersession
  appends a labeled case; the eval compounds with use instead of rotting.

## 3. The fixture: a scrubbed corpus snapshot

A frozen copy of the design/research corpus with the answer removed. Construction
(mechanical; a build-plan deliverable):

1. **Copy** `docs/design-notes/**` and `docs/research/**` at a pinned ref into the
   fixture directory.
2. **Scrub supersession information** from the copies:
   - front-matter `supersedes`, `superseded_by`, `warrant` fields → removed;
   - `status: superseded` → `status: draft` in the copy;
   - prose self-declarations — "⚠️ PARTIALLY SUPERSEDED", "Supersedes …",
     "superseded by …" lines and equivalent markers → removed (the scrub list is
     a maintained pattern file, not a one-off grep);
   - cross-references that *name the relation* (e.g. "this note replaces X") →
     removed; ordinary topical cross-references stay (they are legitimate fibers).
3. **Exclude entirely** (never enter the fixture): `docs/audits/**` (both audit
   reports and the archive-recommendation contain the full answer),
   `docs/findings/**` (0021 and others state the answers), this note itself, and
   any PROGRESS/CHANGELOG material describing the supersessions.
4. **Freeze.** The fixture is a pinned snapshot with a recorded source ref —
   golden-set *discipline* (frozen, versioned, never casually edited) but **not**
   in `eval/golden/**`, which is denylisted and owned by a different suite. Home:
   its own fixture path (e.g. `eval/supersession_recovery/fixture/`), decided at
   graduation.

**Leak control is a test, not a hope:** an automated pre-run check greps the
fixture for every pattern in the scrub list and for the known answer strings
(note-pair names in supersession phrasing); a hit fails the run before the
Dreamer sees anything. A blind test with a leaky fixture is worse than no test —
it returns confident, vacuous green.

## 4. The answer key

Machine-readable (JSON/YAML), versioned beside the fixture:

- **Positives** — each: source note id, target note id, direction, expected
  granularity ("partial — subset of claims" vs "full"), the signal profile it
  should be discoverable from (the hard case must be findable *without*
  chronology), and the certifying verdict reference.
- **Negatives** — each: the pair, the expected non-edge, and the rationale class
  (`extends` / `complementary` / `amendment-pending` / `orphan`) — because *why*
  a pair is not a supersession is part of what a correct proposal channel must
  articulate.
- **Append protocol** — each future owner-certified supersession (and each
  owner-declined proposal) appends a case with its verdict link. The key is a
  growing record of certified ground truth, not a static file.

Initial contents: the two positives and seven negatives enumerated in
finding-0021, verbatim from the archive-recommendation evidence.

## 5. Protocol

Two conditions, run in the `dream_rnd` flag-gated lane (the R&D charter's lane —
no live-path change):

- **Condition D (declared)** — the unscrubbed corpus. A comprehension sanity
  check only: with the declarations present, the pipeline should trivially
  recover the positives. Failure here means the plumbing is broken, not the
  reasoning. Never reported as a recovery result.
- **Condition B (blind)** — the scrubbed fixture. The experiment. Pipeline:
  ingest fixture → candidate generation (fiber-substrate overlap; instrument
  scores optional and off by default in v1) → interpreter panel reasons over each
  shortlisted pair with full text → emits **proposed** supersessions with typed
  warrants → compared against the answer key. Proposals only; nothing is applied;
  no store outside the eval sandbox is touched.

Determinism honesty: the interpreter step is an LLM; run-to-run variance is
real. Report over k runs (k small, e.g. 3–5) with per-case agreement, not a
single pass/fail — a case the panel finds in 1 of 5 runs is a different fact
from one it finds in 5 of 5.

## 6. Scoring and falsifiers

- **Recovery:** per-positive — found / missed, with direction correctness and
  (if claim-level machinery exists by then) subset overlap against the expected
  partial scope. The hard positive (secrets/vault) is the headline number.
- **Discrimination:** per-negative — correctly declined / falsely proposed. This
  is the score that matters most; overlap-heavy additive pairs are exactly where
  a naive candidate machine over-fires.
- **Falsifiers (per the field-guide discipline):**
  - proposing supersession for any of the seven additive pairs → the candidate
    machinery cannot distinguish *extends* from *supersedes* as designed;
  - missing **both** positives in every run → no recovery signal at this scale
    (recorded as such, with re-entry — not as terminal failure; n=2 is
    calibration, not validation);
  - Condition B scoring **identical** to Condition D on the positives *with the
    leak check somehow green* → suspect a leak the pattern file missed; audit the
    fixture before believing the result.
- A null or messy result is recorded "no signal at this scale," re-entry: the
  answer key reaching N certified cases (N set at graduation).

## 7. Harness wiring

This joins the existing evaluation family, not Track L:

- Runs offline, against the frozen fixture, in CI or on demand — the
  dreamer-quality-suite tier (CI-only is the honest current state of that suite,
  per the corpus audit) and/or the holistic-testing *emergent* tier, which is
  currently empty and whose intended shape this matches (behavioral expectation
  over a whole subsystem, not a unit assertion).
- Test entry point produces: the leak-check result, per-condition per-case table,
  k-run agreement, and the headline (hard-positive recovery; negative
  discrimination rate).
- No dependency on Track L, the shadow runner, or verdict-taxonomy ratification —
  this is precisely the evaluation that can run *before* those exist, on
  self-knowledge ground truth.

## 8. Math carried

N/A in v1 beyond what exists — candidate generation uses the fiber substrate
(embedding overlap) already in the store; instrument-scored candidates (signed
Laplacian frustration, curvature) are a v2 lever whose re-entry is Item 10's,
unchanged. The set-to-set supersession representation this test's key anticipates
(partial = proper subset of a note's claims) is finding-0021's enrichment to the
edge-model/supersession notes, ratified there, not here.

## 9. Non-goals

- Does not unpark Item 10 or touch its re-entry conditions.
- Does not ratify, supersede, or edit any note under test (the fixture is a copy).
- Does not validate the Dreamer generally — it calibrates one capability
  (supersession discovery) against n=2+7 labeled cases, and says so.
- Does not enter Track L or the live daemon; `dream_rnd` lane only.

## 10. Open questions (to settle at graduation)

- **Q1** — fixture home and freeze mechanics (`eval/supersession_recovery/` vs a
  fixtures tree; how the pinned ref is recorded and verified).
- **Q2** — candidate-generation v1: pure embedding-overlap threshold, or include
  the cheap combinatorial instruments already built? (Default recorded: overlap
  only; instruments are a v2 ablation.)
- **Q3** — k (runs per condition) and the agreement threshold for "found."
- **Q4** — whether Condition B also ingests a scrubbed copy of the *musings*
  once the founding corpus lands — the owner's original hope: connections found
  between musings and design notes, not just design-note pairs. (Default: v2,
  after founding; the design-note-only v1 stands alone.)

## 11. Parked decisions

| Decision | Default recorded | Re-entry condition |
|---|---|---|
| Instrument-scored candidates (curvature/frustration in `s(C,D)`) | Overlap-only v1 | Item 10's own re-entry (Track L live + verdict taxonomy ratified) |
| Claim-level (set-to-set) scoring of partial supersessions | Note-level pairs in v1 | Founding-corpus Q3 resolved to decomposed claims + claim-level store support |
| Musings in the blind corpus | Design notes + research only | Founding corpus ingested with reconstructed dates |
