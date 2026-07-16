---
type: finding
id: finding-0095
status: resolved            # builder-resolved (spec-fidelity); annotated here + in the bp-055 journal.
created: 2026-07-16
updated: 2026-07-16
links:
  - docs/build-plans/bp-055/plan.md                     # GC-3: certified cuts (this plan)
  - docs/design-notes/global-event-clock.md             # §2.4 (the three certificates), §2.7 (Σ-gating)
  - core/temporal/spine.py                              # _STRATUM_CERTIFICATES + cut_at composition
  - scheduler/queue.py                                 # JobQueue.counts()/depth() — the trough observable
ftype: spec-fidelity
origin_plan: bp-055
route: builder
resolution: >
  Resolved in-plan. The note §2.4 names the three certificates (commit / trough-quiescent /
  handoff-empty) and states a FULL cross-strata cut composes all three, but does not pin the exact
  per-stratum requirement map. Resolved, grounded: mirror→{COMMIT} (the ratified _CUT_CLOCKS case,
  the commit SHA IS the cut for repo-backed strata); ops+interpreted→{TROUGH, HANDOFF} (core stores
  written by scheduler jobs that can incorporate in-flight edge observations — the cut crosses the
  core↔edge boundary); eval→{TROUGH} (internal, no edge dependency). The full four-stratum cut then
  composes exactly {COMMIT, TROUGH, HANDOFF} — the note's "commit ∧ trough-empty ∧ handoff-empty".
  A SECOND under-specification (the note's §10 stop-and-raise contingency) resolved WITHOUT a park:
  the scheduler DOES expose a readable quiescence fact (`JobQueue.counts()`), so the trough
  certificate ships (its fact injected as `TroughState`, never fabricated).
---

# GC-3's stratum→certificate map: the note pins the three certificates and the full-cut composition, but not the exact per-stratum requirement — resolved grounded in §2.4/§2.7

## What
Plan bp-055 §6 pins `Spine.cut_at(*, strata: frozenset[str]) -> CertifiedCut` and §8 says
"Composition: certificates for all strata whose stores intersect the frontier." The design note
§2.4 GC-N3 names the three certificates and states a FULL cross-strata cut composes
`commit ∧ trough-empty ∧ handoff-empty`. What is NOT pinned anywhere is the **exact map from each
stratum to the certificate(s) that certify it** — the composition rule `cut_at` must apply for a
strata SUBSET (e.g. a cut over `{ops}` alone, or `{mirror, eval}`).

Two facts constrain it:
- The note ties each certificate to an OBSERVABLE, not a stratum, directly: commit ↔ repo snapshot;
  trough ↔ the scheduler-owned core queue; handoff ↔ the edge↔core file handoff.
- The spine's stratum tags (`_STRATUM`) are `mirror` (versions/catalog), `ops` (runledger/
  attestations), `interpreted` (edges/derived), `eval` (eval results).

## Why it matters
Left unstated, a builder could (a) require ALL three certificates for ANY cut (over-strict — a
single-stratum mirror cut would need a trough fact it has no causal reason to), or (b) require only
one per cut (unsound — a cut over `ops` would skip the handoff certificate even though edge
observations flow into ops). Either mis-certifies. The cross-strata dreamer (G3) reads at certified
frontiers, so the map is a load-bearing interface it will depend on.

## Resolution (builder, spec-fidelity — implemented in this plan)
`core/temporal/spine.py` `_STRATUM_CERTIFICATES`, grounded in §2.4:

| stratum | stores | required certificate(s) | why |
|---|---|---|---|
| `mirror` | versions, catalog | `{COMMIT}` | the repo-backed corpus; the commit SHA IS the cut (ratified `_CUT_CLOCKS`, `core/scope.py:450`) |
| `ops` | runledger, attestations | `{TROUGH, HANDOFF}` | scheduler-written core stores that can incorporate in-flight edge observations — the cut crosses core↔edge |
| `interpreted` | edges, derived | `{TROUGH, HANDOFF}` | core-derived by scheduler jobs, same edge-flow dependency |
| `eval` | eval results | `{TROUGH}` | internal scheduler jobs, no edge dependency |

`cut_at(strata)` unions the required certificates across the requested strata and refuses if any is
unsourced or its observable is not quiescent. The full four-stratum cut composes exactly
`{COMMIT, TROUGH, HANDOFF}` — a consistency check against the note's stated full-cut shape.

The certificate SOURCES are injected (`CutSources`, additive to `Spine.derive`) and each comes from
its named observable, never wall-time:
- COMMIT — an injected commit SHA (core never shells to git, §2.10; cf. finding-0094).
- TROUGH — the scheduler's OWN `JobQueue.counts()` fact, passed as `TroughState` (core cannot import
  `scheduler` — it would cycle; scheduler imports core widely). Quiescent ⇔ no QUEUED and no RUNNING.
- HANDOFF — a filesystem listing of the sensing handoff's `requests/` + `observations/` dirs (dir
  names MIRRORED, not imported, per the §2.1 zone-boundary discipline). Empty ⇒ certifies.

## The §10 contingency, resolved WITHOUT a park
Plan §10 / task §10: "if the scheduler exposes no readable quiescence fact → file a codebase finding
and PARK the trough certificate." It DOES expose one — `JobQueue.counts()` / `depth()` /
`list(RUNNING)` read the single-writer queue cleanly. So the trough certificate ships alongside
commit and handoff; nothing is parked. (This finding is the reserved 0095, used for the map
resolution above rather than a quiescence park.)

## Re-entry condition
If a future consumer needs a DIFFERENT stratum→certificate binding (e.g. a new stratum, or a store
that gains an edge-flow dependency the table above does not capture), extend `_STRATUM_CERTIFICATES`
— the composition machinery is table-driven and additive. Recorded so the map is a deliberate,
inspectable interface rather than an accident of first-writer choice.

## Routing
`spec-fidelity` → builder-resolved, annotated here + in the bp-055 journal; work continued. No
design-note change (the note anticipates certified cuts and the three observables; the per-stratum
map is a faithful, table-driven realization of §2.4's composition rule).
