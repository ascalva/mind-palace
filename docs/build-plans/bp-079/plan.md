---
type: build-plan
id: bp-079
track: sync-diac-dreamers
status: complete
design_ref:
  - docs/design-notes/synchronic-diachronic-dreamer.md
contract: builder
write_scope:
  - core/dreaming/charter.py
  - core/dreaming/evaluate.py
  - tests/unit/test_dream_charter.py
  - tests/unit/test_materialization_boundary.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 200k
  actual:
    model: opus            # claude-opus-4-8, tier verified on return
    tokens: 164590
    tool_calls: 101
    duration_min: 17
    ratio: 0.82            # well-pinned plan (interfaces copied inline); under estimate
    session_delta: "session ~70%→~82% (30% remainder, pre-1:20am-ET reset)"
depends_on: []
parallelizable_with: [bp-081]
created: 2026-07-21
updated: 2026-07-21
links:
  - docs/design-notes/synchronic-diachronic-dreamer.md
  - docs/design-notes/agent-taxonomy.md
  - docs/design-notes/capability-scope-algebra.md
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — D-0: the DreamCharter dispatch record + the materialization boundary

> Graduated from ratified `dn-synchronic-diachronic-dreamer` (§2.2 SD-2, §2.4 SD-4) at
> `44bbeec`. Every section required; N/A is a judgment on the record.

## 0. Mode & provenance

Investigation and planning produced this; implementation proceeds item-by-item on owner
approval. The owner's instruction to graduate ("see the track through", session-39) is
authority-to-plan; the `proposed → ready` readiness blessing is owner-only, by hand. No agent
flips readiness.

## 1. Objective

A dream dispatch is a typed `DreamCharter` — (scope grant, instrument grant ⊆ `INSTRUMENT_MAX`,
budget, gauge) — whose only store-touching act is one `force`/estimate seam guarded by an
estimate-then-force refusal gate.

## 2. Context manifest

1. `docs/design-notes/synchronic-diachronic-dreamer.md` — §2.0 (DRY table: what exists), §2.1
   (the grant decomposition), §2.2 (the record, verbatim), §2.4 (laws L1–L3, the closed-evaluator
   condition), falsifiers F-SD4a/F-SD4b. The whole design; this plan reads no design elsewhere.
2. `core/agent_scope.py` — `dreamer_scope` (:143-158) and `assert_conforms` (:191-215): the role
   constructor and the conformance check the charter composes. Read whole.
3. `core/factory/roles.py` — the ceiling pattern (:24-40): capability = `scope ∩ MAX`, refuse at
   construction. The `INSTRUMENT_MAX` grant reuses this shape verbatim.
4. `core/scope.py` — meet/delegation (:538-549), admissibility (:603-624), SLICE (:527-536),
   point windows (:248-250). The algebra the charter is a client of; read the cited regions.
5. `core/mirror.py` — `RowSource` (:54-60) + project-and-validate (:86-101): the pattern the
   force seam generalizes.
6. `docs/design-notes/capability-scope-algebra.md` — the lattice vocabulary (skim §2.1–2.4).

## 3. Investigation & grounding

- **Q1 — do the constructors this composes exist as cited?** Yes — verified on disk 2026-07-20
  by the design pass and re-cited here: `dreamer_scope` `core/agent_scope.py:143-158`;
  `assert_conforms` `core/agent_scope.py:191-215`; the ceiling pattern
  `core/factory/roles.py:24-40`; meet `core/scope.py:538-549`; `admissible`/`req_admissible`
  `core/scope.py:603-624`. The builder re-verifies each at its HEAD before writing.
- **Q2 — is there an existing dispatch/charter type to extend rather than create?** No — the
  DRY audit (note §2.0) found the four role constructors and the ceiling pattern but no record
  binding scope grant + instrument grant + budget + gauge; the record is one of the note's four
  genuinely-new things (N1). Greenfield modules; composition of built parts.
- **Q3 — what is `INSTRUMENT_MAX`'s member type?** The code does not settle this (no instrument
  registry exists); the note pins the shape only — named tool handles over evaluators, granted as
  a set, resolved at mint (§2.2-2). The builder defines the handle enum/registry in
  `charter.py` with σ*/MST, conductance-profile, census, persistence as the initial members, and
  files a finding if a member demands machinery beyond a name-to-callable binding.
- **Q4 — where does the estimate read store stats from?** The code does not settle a stats
  surface; L3 requires metadata-only reads (chain counts, node counts, grid sizes). The builder
  implements the estimate over an injected stats provider (a Protocol, counting-fake-testable)
  and does NOT wire a live stats source — wiring is a later plan's call.

**Additional risks or questions surfaced during reading:** none beyond Q3/Q4, both bounded above.

## 4. Reconciliation

N/A — nothing corrected or extended: both modules are new files; no existing behavior, doc, or
test changes. (The existing dreamer path is untouched by design — note §3 D-0: "no behavior
change to any existing dreamer path.")

## 5. Write scope

Two new modules — `core/dreaming/charter.py` (the record, the instrument ceiling, budget, gauge)
and `core/dreaming/evaluate.py` (the estimate/force seam) — plus their two new test files.
Deliberately OUT: every existing `core/dreaming/*` module (no dreamer/pipeline change), all
stores (the seam is tested against counting fakes, no live reads), `core/scope.py` and
`core/agent_scope.py` (clients never edit the algebra), all design notes, the foundation
denylist. No existing test file is carried because no existing surface moves (§4).

## 6. Interfaces pinned inline

- **The record (note §2.2, binding):** `DreamCharter` binds
  1. scope grant = `meet(owner_grant, dreamer_scope(strata))` — the meet is
     `core/scope.py:538-549`; output authority stays the role's `(READ, W_Σ=1, NONE)`;
  2. instrument grant ⊆ `INSTRUMENT_MAX`, resolved at construction, refuse-not-clamp on excess
     (the `core/factory/roles.py:24-40` shape: `capability = scope ∩ MAX`, a skill never widens
     — here: an instrument set never widens);
  3. budget = the L3 cost-model parameters (node/edge ceilings, eigensolve dimension cap, walk
     budget);
  4. gauge ∈ {ANCHORED, RETRO, ARCHIVAL}, default ANCHORED; RETRO/ARCHIVAL constructible but
     inert (their dispatch paths are SD-b, parked — constructing one raises `NotImplementedError`
     with the park named).
- **The seam (note §2.4 L2/L3, binding):** `force(grant, cut[, generation]) -> readings` is the
  ONLY store-touching call; every force is preceded by
  `estimate(expression) -> CostEstimate` computed from metadata only; refusal is
  machinery-side and reports `"refused at estimate: <budget>, <est>"` — quantified.
- **Conformance (note §2.2, binding):** the dispatch's handle inventory passes the existing
  `assert_conforms` (`core/agent_scope.py:191-215`); a store handle not derivable from the
  evaluator is a `ConformanceError`; an instrument handle outside the grant is unconstructable.
- **Legality for free (note §2.1):** a multi-stratum point read demands its cut (SLICE,
  `core/scope.py:527-536`); the charter never re-implements legality — it composes
  `admissible`/`req_admissible` (`core/scope.py:603-624`).

## 7. Items

### Item 1 — the DreamCharter type + the instrument ceiling

- **Objective:** the typed record with structural refusal at construction.
- **Files:** `core/dreaming/charter.py`, `tests/unit/test_dream_charter.py`
- **Acceptance test:** constructing a charter with an instrument outside `INSTRUMENT_MAX` raises
  at construction; the grant is the meet (asserted against `core/scope.py` meet on fixtures);
  gauge defaults ANCHORED; RETRO/ARCHIVAL construct-but-refuse with the SD-b park named.
- **Falsifier:** any code path that clamps (silently narrows) an over-ceiling instrument set
  instead of refusing — clamping is the ceiling pattern's named anti-shape.
- **Invariant(s):** output authority remains `(READ, W_Σ=1, NONE)`; 𝔇 stays subtracted from
  every grant (`⊤_Σ = R ∖ 𝔇`); no store import in `charter.py`.
- **Touches stored data?** No.
- **Parallelizable?** No. **Depends on:** none.

### Item 2 — the estimate/force seam (L1/L2)

- **Objective:** one materialization boundary; composition is symbolic.
- **Files:** `core/dreaming/evaluate.py`, `tests/unit/test_materialization_boundary.py`
- **Acceptance test:** a counting `RowSource` fake proves composing k scope expressions performs
  ZERO reads (L1); exactly one read burst occurs at `force` (L2); the dispatch's handle
  inventory passes `assert_conforms`; a red-team charter holding a direct store handle raises
  `ConformanceError`.
- **Falsifier:** F-SD4b — a row obtained with no corresponding force event (the lazy-view=
  capability unification is theater; report and separate the mechanisms).
- **Invariant(s):** the evaluator is the dispatch's only store-touching capability (the
  closed-evaluator condition, guard tier — honestly labelled in the test's docstring).
- **Touches stored data?** No (fakes only).
- **Parallelizable?** No. **Depends on:** Item 1.

### Item 3 — the refusal gate (L3)

- **Objective:** estimate-then-force; over-budget refuses before any row read.
- **Files:** `core/dreaming/evaluate.py`, `tests/unit/test_materialization_boundary.py`
- **Acceptance test:** an over-budget estimate refuses with zero row reads (counting fake) and
  the refusal message carries both budget and estimate, quantified.
- **Falsifier:** F-SD4a — any ceiling breach reached through a forced view without a prior
  estimate event (the gate is decorative).
- **Invariant(s):** estimate is pure data computed core-side from metadata; refusal is
  machinery-side (the model advises / code acts split, note §2.4 L3).
- **Touches stored data?** No.
- **Parallelizable?** No. **Depends on:** Item 2.

## 8. Math carried explicitly

N/A — no mathematical object implemented: the estimate is metadata arithmetic; the instruments
the charter grants are built elsewhere and consumed by later plans (bp-080/bp-082 carry their
math).

## 9. Non-goals

No dispatch of any actual dream (D-1's job); no census, no overlay, no staging (bp-080/081/082);
no live stats wiring (Q4); no change to any existing dreamer path, the mirror pipeline, or the
R&D flag wiring; no RETRO/ARCHIVAL execution (SD-b parked); no structural (v3) closed-evaluator
enforcement (SD-g parked — guard tier only, labelled).

## 10. Stop-and-raise conditions

An instrument member demanding more than a name-to-callable binding (Q3) → finding, park the
member, continue; any need to edit `core/scope.py`/`core/agent_scope.py` → spec-defect finding,
never edit; a blessing the builder would have to perform → stop; write_scope denial → narrow or
finding, never route around.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| structural closed-evaluator (v3) | guard-tier conformance, honestly labelled | structural now (no consumer needs "provably effect-free"; dn-inner-outer-core P1 owns that trigger) | F-SD4b fires, or P1's re-entry (SD-g) |
| live stats provider wiring | injected Protocol, fakes only | wire live now (couples this plan to store internals; no consumer yet) | the first live dispatch plan (bp-080 seal) names its stats source |
| RETRO/ARCHIVAL dispatch paths | construct-but-refuse with park named | omit the gauge field (loses the declared-descriptor discipline) | SD-b — `graph-at-a-past-cut` graduates |

## 12. Dependency & ordering summary

Items 1→2→3, strictly sequential, all reversible-write tier (new files + tests only). No
dependency on any other plan in this family; `parallelizable_with: bp-081` (disjoint
write_scope). bp-080 and bp-082 depend on this plan. Family sequencing: queues behind the
already-sequenced lead work (bp-069/070/071; inner-outer-core M0/S1 when minted) — the owner
sequences at the `proposed → ready` blessing.
