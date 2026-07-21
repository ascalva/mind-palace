# bp-080 journal

## 2026-07-21T02:40Z — minted at graduation (session-39, orchestrator)

Plan minted `proposed` from ratified `dn-synchronic-diachronic-dreamer` (§2.8/§2.9 as adopted at
`44bbeec`, D-1). No build session yet. Grounding note carried from graduation: the Thread-C
census sweep is licensed but NOT built (grep-verified) — Item 4 is its first implementation.
Carries the owner's narrative-delta A/B observation item (2026-07-21 capsule). Depends on
bp-079. Awaiting owner blessing.

## 2026-07-21 — Item 4 CLOSED: the census reader (builder, worktree)

Built `core/graph/census.py` — the arrow-aware combinatorial census, Item 4's first
implementation of the licensed-but-unbuilt Thread-C sweep (Q1 confirmed at HEAD:
`grep -rln "census|Thread-C" core/ eval/ ops/ scripts/ tests/` → only `charter.py`'s
`Instrument.CENSUS` name; no reader existed).

**Design decisions (grounded at HEAD):**
- **Pure-core / injected** (the `composed.py` + `evaluate.py` pattern). The reader reads NO
  store: input is an explicit directed `Arc` set (the arrow layer over the composed
  assembly's nodes — `composed.py` carries the *undirected* σ-layer; arrows come from
  `reference_edges` X_cite + `versions` supersession) plus a `FirstAuthorship` rank map, both
  INJECTED. Imports ONLY stdlib + `core.temporal.spine.CertifiedCut` (both pure-core) → NO new
  core→sibling import → finding-0103 ratchet UNCHANGED. Adapting the live
  `ReferenceEdgeStore`/`VersionStore` at a cut is a LATER plan's call (§2.8 "likely empty
  today"); here fixtures carry the load.
- **ComposedGraph is undirected** (verified: symmetric `sim` matrix, `neighbors` order-only) so
  the census CANNOT get direction from it — the census reads its own directed arc layer over
  the same node set. Documented in the module banner.
- Three witnessed families, each combinatorial/gauge-immune (ML §2.7b): `influence_loops`
  (elementary directed cycles, canonicalized to min-node start — one claim per cycle),
  `revision_asymmetries` (unbalanced diamonds — two interior-disjoint S→T paths of differing
  length; "branch took 3 revisions where sibling took 1"), `reach_backs` (citation arc A→B
  where rank(B) > rank(A), B younger — a revision-mediated backflow; only `kind="citation"`
  arcs; missing endpoint rank ⇒ no claim, the honest seam). `rank` is a chain position, never
  wall-clock (Law C4). A `DEFAULT_MAX_LEN=12` guard bounds enumeration (documented, never binds
  on the empty/tiny real corpus).
- Claim-kind granularity = per-shape (plan §11 parked default), so adjudication keeps per-shape
  signal. Every `CensusClaim` carries `members` (authored refs → panel `support`), `witness`
  (arc ids / authorship evidence — exactness), `detail`. `census()` returns a `CensusReading`
  that RECORDS its `CertifiedCut` anchor (Item 4 acceptance); empty ⇒ empty reading (silence).

**Acceptance (tests/unit/test_census.py, 13 tests GREEN):** planted 3-cycle / 2-cycle,
unbalanced vs balanced diamond, reach-back vs forward-citation vs unwitnessed-endpoint vs
supersession, arrowless control ⇒ zero claims, empty ⇒ silent, determinism across reversed input
order, cut recorded. Falsifier covered: every claim asserts its exact witness (not just a count);
determinism pinned; zero on control.

Next: Item 5 (census lens on the panel, behind `require_rnd_enabled`, §2.9 vocabulary).

## 2026-07-21 — Items 5 & 6 CLOSED: the census lens + F-SD9 battery + A/B (builder)

**Item 5 — the census lens (`core/dreaming/interpreters.py`).** Added three panel method
constants (`CENSUS_LOOP`/`CENSUS_ASYMMETRY`/`CENSUS_REACH_BACK` — one per shape, §11 default) +
`census_lens(reading, cfg)` mapping `CensusClaim`→panel `Claim`: `support` = authored member refs
(so grounding treats a census claim like any lens), witness + anchored cut ride in `data`,
statement rendered arrow-literally in the §2.9 verbatim vocabulary (`"… cites … — a closed
influence loop (witness: …)"`, `"this branch took N revisions where its sibling took M — a
revision-effort asymmetry"`, `"… re-cites …, younger than its own first authorship — a
revision-mediated backflow"`). Extended `collect_claims`/`run_panel` with an OPTIONAL
`census: CensusReading | None = None` — equal-citizen when supplied, byte-for-byte the old panel
when absent (retrofit inert by default). Added `run_census_lens(reading, *, config)` gated on
`require_rnd_enabled` (lands BEHIND the flag; NO R&D wiring changed — `core/dreaming/rnd.py`
untouched). NOTE: `core/dreaming/__init__.py` is OUT of write_scope, so the new entry points are
NOT re-exported there — tests import from `core.dreaming.interpreters` directly (as the existing
integration tests already do). Adjudicator UNTOUCHED (out of scope) — it is method-agnostic;
census claims flow through and rank because support = authored refs (proven in
test_dream_rnd::test_census_claims_adjudicate_equal_citizen, grounding == 1.0).

**Item 6 — the F-SD9 battery + narrative-delta A/B.** `tests/unit/test_census_lens.py` battery:
each planted structure (3-cycle / unbalanced diamond / retro-citation) surfaces with its EXACT
witness; arrowless control ⇒ ZERO census claims; a grep of every rendered statement finds NO
causal verb (`influenced`/`shaped`/`led to`/`caused`/`because`/…) and NO flux/spectral term
(`flux`/`spectral`/`eigen`/`gauge`/`phase`/…). "influence loop" (the endorsed §2.9-b NOUN) is
allowed — only the causal VERB "influenced" is banned; test encodes that distinction.

A/B observation (NOT a gate): the corpus's directed-arc sources (`reference_edges.sqlite`,
`versions.sqlite`) are NOT materialized on this worktree, and per §2.8 the census is "likely empty
on today's corpus". So the live A/B (same view, same cut, admission toggled) shows the census
EMPTY ⇒ panel byte-IDENTICAL with vs without admission ⇒ ZERO census claims, no crowding-out or
degradation of existing panel claims. F-SD9 non-trigger; no finding warranted. Report on the
exhaust lane at `scratchpad/bp-080-item6-ab.txt` (out-of-repo per plan; no repo file). The planted
fixtures carry the correctness load, as the plan anticipated.

**Acceptance:** tests/unit/test_census_lens.py + tests/integration/test_structural_panel.py +
tests/integration/test_dream_rnd.py all GREEN (30 tests). Full CI gate next.

**Scope/ratchet:** census.py imports only stdlib + `core.temporal.spine` (both pure-core); no new
core→sibling import ⇒ finding-0103 ratchet UNCHANGED. All writes within write_scope.

## 2026-07-21 — CI gate GREEN, ready for orchestrator merge (builder)

Full local CI gate, all green:
- `ruff check .` → All checks passed!
- `check_imports.py` → Import firewall (I2): OK
- `mypy` (census.py + interpreters.py Tier-1 + 4 new/changed test files) → Success: no issues (6 files)
- `ops.type_gate` → Tier-2 membership OK; bare-ignore scan OK
- pytest green gate (deselecting the two finding-0103/0105 nodes) → **1732 passed, 11 skipped,
  21 deselected** (0 failures). bp-080's 43 tests all green.
- finding-0103 ratchet: 22 violations, NONE from census.py/interpreters.py/graph — **UNCHANGED**.

No findings filed (0127-0129 unused): every §6 pin held at HEAD; no store surface was missing
(Q3 confirmed — reads are injected, not live-wired here); the adjudicator needed no change; the
census is empty on the live corpus (arc-source stores unmaterialized) exactly as §2.8 predicted,
so the A/B is a non-event, not a re-rule. No parked criteria. Committed on the worktree branch;
NOT merged (orchestrator is single-writer).
