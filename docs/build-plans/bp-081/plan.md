---
type: build-plan
id: bp-081
track: sync-diac-dreamers
status: complete
design_ref:
  - docs/design-notes/synchronic-diachronic-dreamer.md
contract: builder
write_scope:
  - core/scope.py
  - core/stores/staging.py
  - core/graph/composed.py
  - ops/staging_sweep.py
  - tests/unit/test_scope.py
  - tests/unit/test_scope_laws.py
  - tests/unit/test_staging_store.py
  - tests/unit/test_composed_graph.py
  - tests/unit/test_staging_sweep.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 250k
  actual:
    model: opus            # claude-opus-4-8, tier verified on return
    tokens: 217049
    tool_calls: 100
    duration_min: 23
    ratio: 0.87            # well-pinned; under estimate; filed finding-0130 (Q3 park)
    session_delta: "fresh post-reset pool; ran parallel with bp-080"
depends_on: []
parallelizable_with: [bp-079]
created: 2026-07-21
updated: 2026-07-21
links:
  - docs/design-notes/synchronic-diachronic-dreamer.md
  - docs/brainstorms/hypothetical-subspace.md
  - docs/design-notes/global-event-clock.md
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — H-0 + H-1: the HYPOTHETICAL stratum and its staging substrate

> Graduated from ratified `dn-synchronic-diachronic-dreamer` (§2.6 SD-6; §3 H-0 + H-1 — H-0 is
> the note's own "small rider," carried here as Item 7). The laundering-proof invariant is the
> plan's spine: **no promotion path exists from HYPOTHETICAL to anything.**

## 0. Mode & provenance

Investigation and planning produced this; implementation proceeds item-by-item on owner
approval. `proposed → ready` stays owner-only, by hand.

## 1. Objective

Staged hypotheses live only in a TTL'd, append-only staging store, are visible only under a
grant naming `HYPOTHETICAL`, overlay the durable graph at the composed-assembly seam, and
expire by generation sweep.

## 2. Context manifest

1. `docs/design-notes/synchronic-diachronic-dreamer.md` — §2.6 (all four rulings, verbatim: the
   stratum, the TTL clock, admission/expiry, structural isolation), §2.5 (cuts as pointers),
   SD-d (tombstone default), §2.11 (constraints table).
2. `core/scope.py` — `Stratum` (:55-74), SLICE (:527-536), `admissible`/`req_admissible`
   (:603-624), the ideals. The enum element lands here; the laws must keep holding.
3. `docs/build-plans/bp-070/plan.md` — the DIALOGUE-stratum precedent (enum + laws tests, no
   store schema change elsewhere) this rider is shaped on.
4. `core/graph/composed.py` — whole file: the assembly surface (explicit node set × edge union,
   per-class attribution) the overlay reuses; its guard test pins the surface.
5. `core/mirror.py` (:86-101) — the structural rejection that makes "staged data in the mirror"
   unrepresentable; the isolation battery asserts against it.
6. `core/temporal/spine.py` (:159-274) — certified cuts; the composed read carries cut AND
   generation.
7. `docs/brainstorms/graph-at-a-past-cut.md` — D8 (the interval-valued, ambiguity-widening
   wall→generation resolver posture the sweep reuses).

## 3. Investigation & grounding

- **Q1 — the enum's law surface.** `Stratum` lives at `core/scope.py:55-74`; the bp-070-D1
  precedent added DIALOGUE as enum + lattice-law tests with no store schema change elsewhere.
  The builder greps the scope law tests (`tests/unit/test_scope*.py`) for stratum-set
  assertions that enumerate members — every such test extends for the new element (carried in
  write_scope for exactly this).
- **Q2 — does the composed surface accept a second node/edge class?** Yes by design —
  `core/graph/composed.py` is an explicit node set × edge union with per-class attribution
  (`edge_classes`, E_SIM/E_PROVEN constants) presented through the MirrorGraph surface; a
  staged overlay is a third class at assembly, not a store merge. The guard test
  (`tests/unit/test_composed_graph.py`) pins single-class reproduction — carried because the
  class set extends.
- **Q3 — where does the expiry sweep register?** The code does not settle this at graduation
  (the trough-tier job registration seam was not read); the builder cites the scheduler's job
  registration point at HEAD before wiring, and if registration requires touching scheduler
  internals outside write_scope, STOPS and files the finding rather than widening scope. The
  sweep module itself (`ops/staging_sweep.py`) is machinery-side regardless.
- **Q4 — MirrorView rejection.** `core/mirror.py:86-94` rejects any non-MIRROR_READABLE row at
  construction — staged rows are unrepresentable provided HYPOTHETICAL is never added to
  `MIRROR_READABLE`. This plan does not touch `MIRROR_READABLE` (note §1 out-of-scope pin); the
  isolation battery asserts the rejection concretely.

**Additional risks or questions surfaced during reading:** none beyond Q3 (bounded: stop-and-
raise, never widen).

## 4. Reconciliation

- `core/scope.py` `Stratum` — gains one element → **cross-ref: extension** citing note §2.6-1;
  no existing element or law changes; the multi-stratum SLICE discipline now also covers the
  composed counterfactual read (cut ∧ generation), which the new tests assert.
- `core/graph/composed.py` — the class set gains a staged class → **cross-ref: extension**
  citing note §2.6-4; single- and two-class behavior reproduces bit-identically (the existing
  guard test keeps passing unmodified assertions).

## 5. Write scope

`core/scope.py` carried ONLY for the additive enum element and its law tests (the algebra's
operators are out of bounds — any operator change is a spec-defect finding). New:
`core/stores/staging.py` (append-only, generation-clocked), `ops/staging_sweep.py` (trough-tier
expiry), their unit tests. Carried: `tests/unit/test_scope.py` + `tests/unit/test_scope_laws.py`
(pin the stratum member set), `tests/unit/test_composed_graph.py` (pins the class-set surface).
Deliberately OUT: `MIRROR_READABLE` and `core/mirror.py` (isolation asserts against them,
never edits), every durable store writer, the vectorstore/derived stores, `core/dreaming/*`,
the scheduler package (Q3 — stop-and-raise if wiring demands it), all design notes.

## 6. Interfaces pinned inline

- **The stratum (note §2.6-1, binding):** ONE additive `Stratum` element `HYPOTHETICAL`; staged
  items carry their *would-be* stratum/provenance as ROW DATA (stratum ≠ provenance); default
  grants exclude it; flat and grouped retrieval never see it; a read including staged rows is
  constructible only under a grant naming HYPOTHETICAL; the composed read
  `{…, HYPOTHETICAL}` is multi-stratum by construction ⇒ SLICE fires ⇒ it must carry the
  durable side's certified cut AND the subspace generation.
- **The clock (note §2.6-2, binding):** admission and expiry are staging-store append events on
  its own chain — a per-stratum clock `N_hyp` whose ticks are generations; wall-denominated
  TTLs resolve to generations at sweep time via the interval-valued, ambiguity-widening
  resolver posture (D8); wall never orders anything (Law C4); every reading pins its
  generation.
- **Admission (note §2.6-3, THE laundering-proof invariant):** there is NO promotion path from
  HYPOTHETICAL to anything. No API, no flag, no sweep disposition may move a staged row into a
  durable store. A hypothesis enters the corpus only as everything does: the owner authors it,
  or its real source ingests through the normal pipeline.
- **Isolation (note §2.6-4, binding):** staged rows live only in the staging store; durable
  writers have no hypothetical class to write; `MirrorView` rejects at construction
  (`core/mirror.py:86-94`); the overlay is a class at the `composed.py` assembly, never a store
  merge; a grant with HYPOTHETICAL beside mirror strata is an interpreted-tier dispatch under
  the cross-strata regime (I6 verbatim).

## 7. Items

### Item 7 — H-0: the HYPOTHETICAL stratum element (the rider)

- **Objective:** the enum element + lattice-law + ideal/admissibility coverage. Additive only.
- **Files:** `core/scope.py`, `tests/unit/test_scope.py`, `tests/unit/test_scope_laws.py`
- **Acceptance test:** all existing scope-law tests green with the extended member set; new
  cases — default grants exclude HYPOTHETICAL; a multi-stratum read including it demands SLICE;
  `req_admissible` fails a composed read whose grant omits it; 𝔇-subtraction unaffected.
- **Falsifier:** any existing law test that must weaken an assertion to pass — the element was
  not additive; stop and file.
- **Invariant(s):** no operator/semantics change in `core/scope.py`; `MIRROR_READABLE`
  untouched.
- **Touches stored data?** No.
- **Parallelizable?** No (everything below reads it). **Depends on:** none.

### Item 8 — the staging store

- **Objective:** append-only staged rows with generations; would-be stratum/provenance as data.
- **Files:** `core/stores/staging.py`, `tests/unit/test_staging_store.py`
- **Acceptance test:** append advances the generation chain; rows carry would-be
  stratum/provenance + content digests; reads are generation-addressed; **no method exists
  whose signature could write a staged row to any durable store** (asserted by API surface
  scan in the test); tombstone on expiry per SD-d default.
- **Falsifier:** any code path (however named) that copies a staged row into a durable store —
  the no-promotion invariant is the plan's spine; its violation is an immediate stop.
- **Invariant(s):** append-only; generations monotone; the store is sqlite-backed machinery
  (outer ring — rings classify imports, not roles).
- **Touches stored data?** Yes — a NEW store file only; dry-run first per template rule; no
  durable store is opened for write by any test.
- **Parallelizable?** With Item 9. **Depends on:** Item 7.

### Item 9 — the overlay at the composed assembly

- **Objective:** graph ∪ subspace as a staged class at assembly; math fed unchanged.
- **Files:** `core/graph/composed.py`, `tests/unit/test_composed_graph.py`
- **Acceptance test:** a staged overlay presents through the same MirrorGraph surface; per-class
  attribution retains the staged class; a staged-free composition reproduces existing behavior
  bit-identically (the existing guard assertions unmodified); σ*/conductance run over the
  composed result unchanged.
- **Falsifier:** any change to an existing guard-test assertion; any staged row reaching the
  assembly without a HYPOTHETICAL-naming grant (must be unconstructable — `req_admissible`).
- **Invariant(s):** assembly-not-merge; the math consumers (`sigma_star`, `conductance`) are
  not edited.
- **Touches stored data?** No.
- **Parallelizable?** With Item 8. **Depends on:** Item 7.

### Item 10 — the expiry sweep + the isolation battery

- **Objective:** trough-tier generation sweep; the §2.6 isolation tests as a permanent battery.
- **Files:** `ops/staging_sweep.py`, `tests/unit/test_staging_sweep.py`
- **Acceptance test:** the sweep advances the generation and removes expired items from every
  readable view (tombstone); wall→generation resolution is interval-valued and
  ambiguity-widening (D8 posture); the battery — durable stores scan to zero staged rows after
  any staged dispatch fixture; `MirrorView` + staged row raises; cut-less composed read
  unconstructable.
- **Falsifier:** an expired item visible in any readable view after sweep; a wall timestamp
  used to ORDER anything (Law C4 violation).
- **Invariant(s):** sweep is machinery-side (ops), read/tombstone-only on the staging store;
  registration does not touch scheduler internals (Q3 — stop-and-raise otherwise).
- **Touches stored data?** Yes — staging store only; dry-run mode first.
- **Parallelizable?** No. **Depends on:** Items 8–9.

## 8. Math carried explicitly

N/A — no new mathematical object: the stratum joins an existing lattice whose laws are the
existing test surface (extended, not changed); generations are bookkeeping; the overlay feeds
existing math unchanged (bp-082 carries the influence math).

## 9. Non-goals

No influence computation or conditioning law (bp-082); no dreamer dispatch over the overlay
(bp-082, gated); no `MIRROR_READABLE` change ever; no hard-delete disposition (SD-d parked —
plan-level call with the owner when staging growth is measured); no edit/removal overlays
(SD-e); no persistent σ-graph representation (SD-c — the L2 boundary contains it).

## 10. Stop-and-raise conditions

Sweep registration demands scheduler-internal edits (Q3) → finding + park Item 10's wiring,
land the sweep as a callable; any existing scope-law test that would need weakening (Item 7
falsifier) → spec-defect finding; ANY path that would move a staged row durable-ward → stop
immediately, file, do not implement a "gated" version (the gate is that none exists); a
blessing → never.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| tombstone vs hard delete (SD-d) | tombstone | hard delete now (append-only discipline; cheap at scale; admissibility-by-design noted honestly in the note) | staging growth measured material — owner call at that plan |
| sweep scheduling tier | trough-tier housekeeping | inline-at-read expiry (couples read latency to housekeeping; hides the clock) | sweep lag measurably stales readable views |
| staging store engine | sqlite (the store-layer house pattern) | in-memory only (loses reproducible reading records past process life) | none foreseen |

## 12. Dependency & ordering summary

Item 7 first (everything reads the element); Items 8–9 parallel (store ∥ assembly); Item 10
last (sweep + battery). Blast radius: additive enum → new store → assembly extension → sweep
(the only expiring writer). `parallelizable_with: bp-079` (disjoint write_scope; bp-080 touches
neither of these surfaces but is sequenced after bp-079 anyway). bp-082 depends on this plan
whole. Family sequencing: behind bp-069/070/071 + M0/S1 at the owner's blessing.
