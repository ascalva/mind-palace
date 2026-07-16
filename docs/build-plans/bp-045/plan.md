---
type: build-plan
id: bp-045
alias: wire-snapshot-a2
status: complete
design_ref:
  - docs/design-notes/evaluation-harness.md
contract: builder
write_scope:
  # NOTE: no inline comments on globs — scope-guard does not strip them (finding-0085). Rationale §5.
  - core/dreaming/dreamer.py
  - tests/unit/test_build_dreamer_snapshots.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 60k
    rationale: >-
      A single additive wiring in `build_dreamer` (pass `snapshots=open_snapshot_store(cfg)` so the
      already-built `dream_v2` step-10 fires) + a focused test proving the phase7 path is bit-identical
      and no snapshot is written on a phase7 run. Trivial-mechanical, deterministic; smaller than
      bp-040's 90k. Calibrated ~60k opus. NO fable, NO xhigh. Self-driven ~0.5–0.8×. The milestone-
      critical slice of E5 ("E5(A2)") — the rest of E5 (CoherenceReport caller, adjudicator panel,
      effector_drift into reports) is a separate deferred plan (depends on E1+E4 built).
  actual:
    model: opus            # SELF-DRIVEN (orchestrator-as-builder, no delegation)
    tokens: ~13k           # APPROX (owner /usage; per-plan split of the shared $25.15/108.8k two-build delta)
    ratio: ~0.22           # ~13k / 60k est — well under (trivial-mechanical wiring; the tiny slice it was)
    dollars: ~3            # APPROX share of the $25.15 two-build session delta; ZERO credits drawn
    loc: "~10 added (1-line import extend + 1 kwarg + 3-line comment in build_dreamer) + 1 test file (~95)"
    # GREEN attested SEPARATELY (5-leg): ruff `.` PASS; mypy `core agents eval ops scheduler scripts`
    # == 0 (190 files); argless mypy == 69 UNCHANGED (the 1 test-only _RowSource→VectorStore arg-type
    # fixed with a cast, matching test_dream_v2's idiom); ops.type_gate OK; pytest -q -m 'not live'
    # == 1185 passed / 7 skipped / 9 deselected(live) / 0 failures (+2 new). Live dream-e2e deselected.
    # Falsifiers held: phase7 dream() writes no snapshot through the wired store; dream_v2 writes exactly
    # one; no [dream_rnd] disk flag touched; existing dreamer/dream_v2 suites green unmodified.
depends_on: []                          # open_snapshot_store already exists; no dep needed to build this
parallelizable_with:
  - bp-042
  - bp-043
  - bp-044
created: 2026-07-15
updated: 2026-07-15
started: 2026-07-15
completed: 2026-07-15
links:
  - docs/design-notes/evaluation-harness.md
  - core/dreaming/dreamer.py
  - core/complex/temporal.py
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — `wire-snapshot-a2` (bp-045): SnapshotStore into `build_dreamer` — the E5(A2) wiring

> **Every section below is required.** Inapplicable sections are marked `N/A — <reason>`.

## 0. Mode & provenance

Investigation and planning produced this plan; **implementation proceeds item-by-item on owner
approval**. Authority-to-act (owner ratified `dn-evaluation-harness` + directed graduation) is
separate from the readiness blessing (owner-only `proposed → ready`) — no agent flips readiness.

Graduated from ratified `dn-evaluation-harness` §3 **E5** — specifically the **E5(A2)** slice the
note sequences into the first overnight dual-dreamer A/B (*"SnapshotStore into `build_dreamer`
(per-run A2 rows)"*). The remaining E5 wirings (a live CoherenceReport replay-pair caller, the
adjudicator confidence panel into reports, `effector_drift` as a report-only axis) are **report
enrichments** that depend on E1+E4 being built — they are a separate, deferred plan, not this one.
Model **opus**; **no fable, no xhigh** (a settled, trivial-mechanical wiring). This plan is the
milestone-critical slice: without it, `dream_v2`'s step-10 structural snapshot never fires, so the
first A/B has no structural axes to render (the shadow runner logs them not-captured — bp-043 §12).

**The whole-plan falsifier:** the Phase-7 `dream()` path changes behavior, or a structural snapshot
is written during a Phase-7 run (which has no step-10). The wiring is additive and must be invisible
to the live cron path.

## 1. Objective

Wire `snapshots=open_snapshot_store(config)` into `build_dreamer` so a Dreamer it constructs carries
the structural-snapshot store, letting `dream_v2`'s already-built step-10 (`self.snapshots.write(
compute_snapshot(...))`) fire and record the A2 axes — with the live Phase-7 `dream()` path
bit-identical and no flag flipped.

## 2. Context manifest

Read whole, in order:

1. `docs/design-notes/evaluation-harness.md` — **§2.3** catalog **row 6** (structural snapshot axes:
   *"built, unwired — SnapshotStore not passed by `build_dreamer`; written only in `dream_v2`" →
   "WIRE (§3 E5); per-run rows"*), **§3 E5**, **§2.9** (the A2 axes are first-class in the A/B — the
   topological dreamer measured in β₀/Fiedler/frustration/curvature/SBM/conductance/H₁).
2. `core/dreaming/dreamer.py` — `Dreamer.snapshots: SnapshotStore | None = None` (`:101`);
   `dream_v2` step 10 (`:242-247`: `if self.snapshots is not None: self.snapshots.write(
   compute_snapshot(ctx.complex, distances=ctx.distances, ...))`); **`build_dreamer`** (`:265-285`)
   — the constructor that today omits `snapshots=` (and `edge_store=`). The import of `SnapshotStore,
   compute_snapshot` is already present (`:27`).
3. `core/complex/temporal.py` — `open_snapshot_store(config) -> SnapshotStore` (`:203`, path =
   `cfg.paths.derived_store.parent / "structural.duckdb"`, `:208`); `SnapshotStore.write` (`:159`),
   `.count()` (`:170`), `.latest_structural()` (the harness's read path, bp-043 Q6). Constructing a
   `SnapshotStore` opens/creates its DuckDB file (`__post_init__` — `:152-157`).
4. `docs/build-plans/bp-043/plan.md` §3 Q6 + §12 — the consumer: the ShadowRunner builds its Dreamer
   via `build_dreamer` and reads `latest_structural()` to write keyed `structural_axes.*` readings.

## 3. Investigation & grounding

- **Q1 — Is `build_dreamer` the reason A2 rows never appear? YES / confirmed.** `build_dreamer`
  (`dreamer.py:277-285`) constructs `Dreamer(store=..., synthesize=..., derived=..., threshold=...,
  min_cluster_size=..., max_clusters=..., attestor=...)` — **`snapshots=` is absent**, so it defaults
  `None` (`:101`), so `dream_v2` step-10's `if self.snapshots is not None` (`:243`) is always false.
  The note's catalog row-6 claim ("SnapshotStore not passed by `build_dreamer`") holds exactly.
- **Q2 — Does the Phase-7 `dream()` path ever touch `self.snapshots`? NO.** `dream()` (`:126-165`)
  has no snapshot write — step-10 is `dream_v2`-only (`:242`). So passing `snapshots=` cannot change
  `dream()` output; a Phase-7 run writes no structural row. This is the whole-plan falsifier's basis.
- **Q3 — Side effect of always-wiring: an empty `structural.duckdb` created on every `build_dreamer`.**
  `open_snapshot_store` constructs a `SnapshotStore`, whose `__post_init__` `mkdir`s the parent and
  `duckdb.connect`s the file (`temporal.py:152-157`) — so every `build_dreamer` call now opens (and,
  first time, creates) `data/structural.duckdb`, even for a Phase-7-only live loop. **The code does
  not force a choice here — this plan settles it:** always-wire (accept the created file + a held
  DuckDB connection; the file IS the harness's structural store, and Phase-7 simply never writes to
  it). The lazy-open alternative (a factory the Dreamer calls only inside step-10) is heavier and
  parked (§11). If the held connection is found to contend with the live loop, STOP and file a
  `codebase` finding (§10).

**Additional risks surfaced during reading:** `edge_store=` is ALSO omitted by `build_dreamer`
(`:100`) — wiring it is the H8 typed-edges seam, **out of scope** (a different instrument; this plan
is A2 only). Touching it would widen blast radius into the tension lens; §9 non-goal.

## 4. Reconciliation

- **`core/dreaming/dreamer.py::build_dreamer` — EXTENDED (cross-reference-on-extension), NOT a
  correction.** Nothing is wrong; the note (§2.3 row 6, §3 E5) asks to *wire* an already-built,
  currently-unpassed argument. Proposed diff: add one keyword to the `Dreamer(...)` construction —
  `snapshots=open_snapshot_store(cfg)` — and import `open_snapshot_store` (the module is already
  imported at `:27`; add the factory to that import). A one-line comment cross-references catalog
  row 6 / §3 E5. **No other line of `build_dreamer` changes; `dream()`/`dream_v2` bodies are
  untouched.**
- **`dn-evaluation-harness` frontmatter (`not-built`) + catalog row 6 ("built, unwired") become
  stale on build** — batched to `owner-questions.md` on completion (bp-039 pattern). Additive only.

## 5. Write scope

- `core/dreaming/dreamer.py` — Item 11 only: `build_dreamer` passes `snapshots=` + the factory
  import. No behavior change to `dream()`/`dream_v2` bodies; the `edge_store=` omission is left as-is.
- `tests/unit/test_build_dreamer_snapshots.py` — **NEW**: the wiring + no-phase7-write + bit-identical
  proof.

**Deliberately OUT of scope:** `edge_store=` wiring (the H8 typed-edges seam — a different
instrument, §9); the other three E5 wirings (CoherenceReport caller / adjudicator panel /
effector_drift into reports — the deferred E5-rest plan, depends on E1+E4); flipping `[dream_rnd]
enabled` (bp-041, owner-gated); `core/complex/temporal.py` (SnapshotStore is consumed unchanged — no
schema touch, bp-043 Q6); the eval store / run ledger (bp-042/bp-043); `eval/golden/**`,
`CONSTITUTION.md` (denylist); every design note (immutable, A8).

## 6. Interfaces pinned inline

```python
# core/dreaming/dreamer.py — the ONLY change (Item 11). Current build_dreamer tail (:277-285):
#     return Dreamer(
#         store=open_vector_store(cfg),
#         synthesize=lambda messages: server.chat(tier, messages),
#         derived=open_derived_store(cfg),
#         threshold=dcfg.similarity_threshold,
#         min_cluster_size=dcfg.min_cluster_size,
#         max_clusters=dcfg.max_clusters,
#         attestor=build_attestor(cfg),
#     )
# PROPOSED: import open_snapshot_store (extend the existing :27 import) and add ONE kwarg:
#         attestor=build_attestor(cfg),
#         snapshots=open_snapshot_store(cfg),   # wire the A2 structural store (catalog row 6, §3 E5);
#                                               # dream_v2 step-10 fires, dream() never touches it.

# Consumed unchanged (core/complex/temporal.py):
def open_snapshot_store(config: "Config | None" = None) -> "SnapshotStore": ...   # :203
# dream_v2 step 10 (dreamer.py:242-247) — ALREADY built, becomes reachable once snapshots is set:
#     if self.snapshots is not None:
#         self.snapshots.write(compute_snapshot(ctx.complex, distances=ctx.distances,
#             sbm_k_max=rnd.sbm_k_max, hole_min_persistence=rnd.hole_min_persistence))
```

## 7. Items

### Item 11 — wire `snapshots=` into `build_dreamer`
- **Objective:** `build_dreamer` constructs its `Dreamer` with `snapshots=open_snapshot_store(cfg)`
  (+ the factory import); `dream()`/`dream_v2` bodies untouched.
- **Files:** `core/dreaming/dreamer.py`, `tests/unit/test_build_dreamer_snapshots.py`.
- **Acceptance test:** `build_dreamer(cfg).snapshots is not None` and points at
  `cfg.paths.derived_store.parent / "structural.duckdb"`; a `dream_v2` run through a
  build_dreamer-constructed Dreamer (dream_rnd enabled in-process, fake synthesizer) increments
  `snapshots.count()` by 1; a Phase-7 `dream()` run writes **no** structural row (`count()`
  unchanged) and its returned themes are unchanged from the pre-wiring behavior; the `[dream_rnd]`
  disk flag is untouched; `mypy` 0; the existing dreamer test suite passes unmodified.
- **Falsifier:** a Phase-7 `dream()` run writes a structural snapshot (it has no step-10 — a write
  means the wiring leaked into the wrong path), OR any existing dreamer test needs modification to
  stay green (the change was not purely additive), OR `build_dreamer` now raises/hangs when
  `structural.duckdb`'s directory is read-only (the store open became load-bearing at construction in
  a way that breaks the live loop — §3 Q3 STOP condition).
- **Invariant(s) it must not violate:** the live Phase-7 cron path is bit-identical (the whole-plan
  falsifier); no flag flipped; `dream_v2` remains gated `[dream_rnd] enabled` (this only wires the
  store, it does not enable the pipeline); the Dreamer stays model-free except its one synthesis seam.
- **Touches stored data?** Yes — constructing the store creates/opens `data/structural.duckdb`
  (empty until a `dream_v2` run). The test uses a tmp derived-store parent, never the live path.
  **Parallelizable?** Yes — `parallelizable_with: [bp-042, bp-043, bp-044]` (disjoint write scope).

## 8. Math carried explicitly

`N/A — no mathematical object implemented.` The A2 axes (β₀, Fiedler, frustration, Forman curvature,
conductance, harmonic persistence) are **already built** in `compute_snapshot` /
`core/complex/temporal.py`; their three-clause field-guide entries live with that instrument
(catalog row 6). This plan only makes the existing computation *reachable* by wiring its store.

## 9. Non-goals

- **No `edge_store=` wiring** — the H8 typed-edges seam is a different instrument; wiring it widens
  blast radius into the tension lens (§3 risk). A2 only.
- **No CoherenceReport / adjudicator-panel / effector_drift wiring** — the E5-rest report
  enrichments; a separate deferred plan (depends on E1+E4 built).
- **No `[dream_rnd]` flag flip** — wiring the store does not enable `dream_v2`; going live is bp-041.
- **No SnapshotStore schema change** — the store is consumed unchanged; per-run A2 attribution lives
  in the eval store's key (bp-043 Q6), not a new snapshot column.

## 10. Stop-and-raise conditions

- A held `structural.duckdb` DuckDB connection from `build_dreamer` contends with / slows the live
  loop → **STOP, file a `codebase` finding** (§3 Q3): switch to lazy-open (§11) rather than accept a
  live-path regression.
- Passing `snapshots=` changes a Phase-7 `dream()` result or requires editing an existing dreamer
  test → **STOP, file a `codebase` finding**: the wiring must be purely additive and invisible to the
  live path (the whole-plan falsifier).
- Any blessing flip → **must not**.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| When to open the snapshot store | always-wire at `build_dreamer` (accept an empty `structural.duckdb` + a held conn; Phase-7 never writes it) | lazy-open inside step-10 (rejected: heavier; a Dreamer field would become a factory, changing the frozen shape) | the held connection is shown to contend with the live loop (§10) |
| `edge_store=` wiring | out of scope — A2 only | wire both here (rejected: the H8 tension-lens seam is a distinct instrument, wider blast radius) | the tension-lens / typed-edges instrument graduates |

## 12. Dependency & ordering summary

One item, one file changed + one test. `depends_on: []` — `open_snapshot_store` already exists, so
this builds standalone (even before E1). `parallelizable_with: [bp-042, bp-043, bp-044]` (disjoint
write scope — `core/dreaming/dreamer.py` here, touched by no other tranche plan).

**Cross-plan:** this is the E5(A2) slice the milestone A/B needs. bp-043's ShadowRunner constructs
its Dreamer via `build_dreamer` (+`dataclasses.replace` to point `derived` at a scratch store),
inheriting this snapshot wiring, then reads `SnapshotStore.latest_structural()` to write keyed
`structural_axes.*` readings into the E1 eval store (bp-043 §3 Q6). If this plan has NOT landed, the
runner logs the A2 axes as not-captured (no silent cap). Build order for the milestone: this is
buildable first/parallel; the A/B needs **E1 + E2 + E5(A2)/this + E4**. The E5-rest plan (CoherenceReport
caller, adjudicator panel, effector_drift) graduates later. Recorded in `docs/PARKING-LOT.md`.
