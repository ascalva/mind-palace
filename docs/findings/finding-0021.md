---
type: finding
id: finding-0021
status: routed
ftype: discovery
origin_plan: null            # surfaced in owner–orchestrator design review of the archive-recommendation pass
route: orchestrator
created: 2026-07-06
updated: 2026-07-06
links:
  - docs/audits/archive-recommendation.md          # the episode
  - docs/audits/corpus-state-audit-2026-07-verification.md
  - docs/design-notes/supersession-lifecycle.md    # enriched at ratification (set-to-set partiality)
  - docs/design-notes/the-edge-model.md            # enriched at ratification (same)
  - docs/design-notes/founding-corpus.md           # enriched at ratification (three source classes; code label)
  - docs/design-notes/supersession-recovery-evaluation.md   # the design note this finding warrants (draft)
resolution: null
---

# finding-0021 — The archive pass was an unprompted dry run of the supersession lifecycle

## What happened

The corpus-maintenance pass (archive-recommendation, 2026-07-06) — an orchestrator
reading the design corpus plus two audits to recommend archive/supersede actions —
turned out to execute, end to end and without being designed to, the supersession
lifecycle this system specifies for its object corpus. It produced two accepted
supersession edges, seven documented negatives (high-overlap pairs judged additive,
not superseding), and en route reproduced several of the design's own predictions.
The reasoning it took is itself evidence about how supersession discovery works,
and it yields a labeled ground-truth set the system can be tested against.

## The reasoning steps, mapped to the machinery

1. **Candidate generation by subject overlap** — the pass shortlisted note pairs
   covering the same subsystem, then applied a 2-of-3 multi-signal threshold
   (chronology, overlap, external corroboration). That is the candidate score
   `s(C,D)` (edge-and-supersession plan, Item 10) in embryonic, binary-feature
   form: composite signals → threshold → shortlist → expensive reasoning only on
   the shortlist.
2. **The timestamp lie recurred, in a new domain.** Git "creation dates" proved to
   be commit-batch dates (seven notes share one timestamp; seven share another;
   the secrets/vault pair landed in a single commit). Batch commits flatten time
   exactly as batch ingest does (`founding-corpus.md §2.1`). The pass responded as
   the doctrine prescribes: refused to claim a chronology that isn't there, fell
   back to other signals, and said so. The founding requirement — owner-reconstructed
   dates as first-class, undated items refused — just received an independent
   demonstration of why it exists.
3. **Proposal, never assertion.** The recommendation ledger is the `proposed`
   state; the owner's by-hand `superseded_by` edit is the certification verdict.
   The Item-8 `proposed → certified` path and the blessing gate ran live — over
   blessed (owner-authored) content, with the enforcement layer structurally
   preventing the agent from applying the edge. The gates were exercised in
   exactly the Dreamer-proposal flow they were designed for, before the Dreamer
   exists.
4. **Orphan ≠ superseded.** `planar_graphs.md` (an archive question on orphan
   grounds, zero supersession signals) was routed to its own track (finding-0017)
   rather than forced into the supersession table — the disposition-authority
   distinction (removal-by-supersession vs removal-by-decay/prune are different
   authorities and must not share a channel), independently rediscovered.
5. **"Partial supersession" surfaced as a granularity artifact.** Both accepted
   edges are "partial — residual value, keep in place." The awkwardness is not in
   the relation; it is in the unit. A note is a bag of claims; document-level
   machinery can express "some claims overtaken, others stand" only as a lossy
   flag. See §Representation below.

## Representation clarifications (to enrich the edge/supersession notes at ratification)

**Fiber vs supersession, stated sharply.** A fiber is *binary, undirected,
monotone* — pure relatedness; lives in E_geom; feeds `L = D − A_geom`; only ever
adds connectivity. A supersession is *ternary(+), directed, non-monotone* —
(source, target, **warrant**); the warrant slot is what makes it a reasoning line
rather than a relatedness assertion; lives in E_disp, in stores the balance math
has no handle to; carries authority typing and a `proposed → certified` lifecycle;
and — what no fiber does — acts on the active projection (demotes). A supersession
is never *also* a fiber (the invariance falsifier: instrument results must be
unchanged under adding/removing any dispositional edge). The relatedness intuition
is nevertheless satisfied: the pre-existing geometric fibers between the pair are
what made it a candidate. Geometry carries relatedness; disposition carries
overruling; they never share a store.

**Partial supersession is exact over a subset, not fuzzy.** The primitive is a
directed **set-to-set** relation with warrant: ({source claims}, {target claims},
warrant). The classic three-place (C, C′, w) is the singleton case. "Partially
superseded note" = the source set is a proper subset of the note's claims; the
complement stays active. Nothing fuzzy exists at claim granularity; the fuzziness
appears only when projecting to note granularity, because the note is a bag and
the flag is a lossy aggregate of exact subset relations. The coboundary spine
carries the set-to-set form natively (a typed directed hyperedge); no new
mathematics. This is direct evidence on founding-corpus **Q3**: decomposed claims
make partiality representable; whole-document units force the lossy flag the
archive pass had to resort to.

## Founding-corpus enrichment (three source classes)

The founding corpus comprises three classes, each with a distinct handling:

- **Musings** — `authored-solo`, owner-reconstructed dates (the manifest path).
- **Design notes / documentation** — authored, but batch-committed: their git
  dates are the timestamp lie (demonstrated above); they need reconstructed dates
  too, not commit dates.
- **Source code** — not owner belief but builder-produced *reality*. In the
  episode it served as the **external corroboration stream** — the arbiter that
  turned weak overlap candidates into strong ones (which design is actually
  built). Code plays, for the self-knowledge stratum, the role Track L verdicts
  play for the object corpus. This argues for a distinct provenance label (not
  `authored-solo`) — an open sub-question to settle at founding-corpus
  ratification, recorded here, not decided here.

## Design lesson for `s(C,D)`

Overlap + chronology alone produced weak candidates; overlap + **external
corroboration** produced strong ones (and chronology failed entirely within
commit batches). The candidate score wants an external-evidence feature; for the
object corpus that stream is Track L verdicts (and, parked, observed zones).
Carry into Item 10 when it unparks.

## The ground-truth set (labeled, with a difficulty gradient)

Positives (2):
- `ambassador-interpretation-and-flow` → superseded by `ambassador-as-reasoning-agent`
  — the easy case (all three signals; self-declared).
- `secrets-management-evolution` → superseded by `vault-runtime-auth` — the hard
  case (no chronology signal — same commit; requires overlap + external
  corroboration alone).

Negatives (7, each high-overlap but additive — the discrimination that matters is
*extends vs supersedes*): `nervous-system-and-ambassador` (uniquely owns unbuilt
§1/§2); `observed-data` ↔ `observed-iot` (extension pair); the dream-R&D family
(additive, flag-off); `holistic-testing` ↔ `test-organization` (complementary);
`recursive-strata-amendment` (pending unapplied patch — an amendment, not a
supersession); the sacred-boundary reconciliation set; `attestation-layer`
(extends, not supersedes).

Every future owner-certified supersession appends to this key organically — the
answer set grows as verdicts land.

## Honest boundaries

- The episode's reader (Claude, whole-document comprehension) has economics the
  system cannot afford at corpus scale — which is *why* the design is
  instruments-shortlist-then-interpreter. The episode validates the reasoning
  shape, not the cost profile.
- Self-declaration ("Supersedes…") was a usable heuristic here only because the
  design notes predate the machinery; in the object system it is a first-class
  authored operation and the heuristic dissolves.
- n=2 positives is a **calibration case, not validation**. A null result is "no
  signal at this scale," with re-entry as the certified-supersession set grows.
- **The answer key is written into the corpus** (self-declarations; the audit
  artifacts). Any test must scrub and exclude, or the result is vacuous — this is
  the load-bearing requirement of the test design note.

## Disposition

Routed → orchestrator. This finding warrants, at the already-pending ratification
passes (no new amendments minted now, no parked decision unparked):

1. The set-to-set/partiality formulation → `the-edge-model.md` and
   `supersession-lifecycle.md` enrichment at their ratification.
2. The three-source-class structure + the code-provenance-label sub-question →
   `founding-corpus.md` enrichment at its ratification (bears on Q3).
3. The external-corroboration feature → Item 10's `s(C,D)` when its re-entry
   conditions are met (Track L live + verdict taxonomy ratified — unchanged).
4. **A new design note** (draft): `supersession-recovery-evaluation.md` — the
   blind-recovery test, its scrubbed-corpus fixture, machine-readable answer key,
   and harness wiring. That note carries the test; this finding carries the
   evidence.

Item 10 remains parked. This episode is precisely the kind of promising connection
the restraint discipline exists for: captured, routed, not chased.
