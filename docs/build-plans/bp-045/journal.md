# Journal — bp-045 `wire-snapshot-a2`: SnapshotStore into build_dreamer (the E5(A2) wiring)

> The fresh-agent contract: a new session with only `plan.md` + this journal + the write-scope files
> must continue without re-asking. Checkpoint at every semantic boundary. Status flips are the
> orchestrator's, by hand.

## 2026-07-15 — GRADUATED (proposed), awaiting owner `proposed→ready` blessing

- Graduated by the orchestrator (opus, self-driven) from ratified `dn-evaluation-harness` §3 **E5**,
  the **E5(A2)** slice only — the milestone-critical wiring the first A/B needs. The rest of E5
  (CoherenceReport live caller, adjudicator confidence panel → reports, effector_drift → report-only
  axis) is a SEPARATE deferred plan: those are report enrichments that depend on E1+E4 being BUILT,
  not milestone-critical. Kept E5(A2) standalone (not folded into bp-043) so it can build first/parallel
  and to avoid renumbering bp-044's items.
- **Grounding done in-session** (direct reads). Key facts:
  - `build_dreamer` (`dreamer.py:277-285`) omits `snapshots=` → defaults `None` (`:101`) → `dream_v2`
    step-10 (`:242-247`, `if self.snapshots is not None`) never fires. That is EXACTLY why the A2 rows
    never appear (catalog row 6). The fix is ONE kwarg + the factory import (already-imported module :27).
  - Phase-7 `dream()` (`:126-165`) has no snapshot write (step-10 is dream_v2-only) → passing `snapshots=`
    cannot change `dream()`; a phase7 run writes no structural row. That is the whole-plan falsifier.
  - Side effect (Q3): `open_snapshot_store` opens/creates `data/structural.duckdb` at construction
    (`__post_init__` mkdir+connect). Every `build_dreamer` now opens it, even for a phase7-only live loop.
    Settled: ALWAYS-WIRE (accept the empty file + held conn; phase7 never writes it); lazy-open parked;
    STOP+finding if the held conn contends with the live loop.
  - `edge_store=` is ALSO omitted — the H8 tension-lens seam, explicitly OUT of scope (§9).
- **Scope:** ONE item (Item 11) — wire `snapshots=` + test (bit-identical phase7, no-write-on-phase7,
  count-increments-on-dream_v2, flag untouched).
- **Cost estimate:** opus 60k (trivial-mechanical additive wiring + one focused test). Self-driven
  ~0.5–0.8×. No fable, no xhigh.
- **Not started** — `proposed`. `depends_on: []`; `parallelizable_with: [bp-042, bp-043, bp-044]`.
  Buildable first (open_snapshot_store already exists). bp-043's ShadowRunner inherits this wiring via
  `build_dreamer`+`replace`, then reads `latest_structural()` → keyed eval-store readings (bp-043 Q6).
  Owner blesses `proposed→ready`, then `/build bp-045` (a good tiny first build — cheap even at week 95%).

## 2026-07-15 — BUILT + 5-leg gate GREEN (Item 11 done; awaiting orchestrator seal)

- Owner blessed bp-045 `proposed→ready` (committed `fc52eb9`); orchestrator flipped `ready→in-progress`
  + stripped the write_scope inline comment (finding-0085 owed cleanup) — committed `749485b`.
- **Item 11 DONE — the wiring.** `core/dreaming/dreamer.py`: extended the `:27` import with
  `open_snapshot_store`; `build_dreamer` now passes `snapshots=open_snapshot_store(cfg)` (one kwarg +
  a 3-line comment). `dream()`/`dream_v2` bodies untouched.
- **Test `tests/unit/test_build_dreamer_snapshots.py` — 2 tests PASS:**
  1. build_dreamer wires a SnapshotStore at `derived_store.parent/structural.duckdb`, `count()==0` fresh.
  2. THROUGH build_dreamer's wired store: Phase-7 `dream()` writes NO snapshot (count unchanged — the
     whole-plan falsifier), then `dream_v2` step-10 fires and records exactly one (`count()==before+1`).
     Uses the planted R0/R1 shape + a fake `_CountingSynth` (no live model), dream_rnd enabled in-process.
- **5-LEG GREEN GATE (SEPARATELY):** ruff `.` PASS; mypy `core agents eval ops scheduler scripts` == 0
  (190 files); argless mypy == **69** UNCHANGED (the tooth HELD — the 1 test-only `_RowSource`→`VectorStore`
  arg-type error was fixed with a `cast`, matching test_dream_v2's idiom); ops.type_gate OK; pytest
  `-m 'not live'` == **1185 passed / 7 skipped / 9 deselected(live)** / 0 failures (+2 new; the dreaming
  integration suite exercising the wired step-10 is green). Live dream-e2e deselected (Ollama/slow).
- **Falsifiers held:** phase7 dream() writes no structural row through the wired store; no `[dream_rnd]`
  disk flag touched (enabled in-process only); existing dreamer/dream_v2 suites green unmodified.
- **Next:** commit (Co-Authored-By — code); orchestrator flips `in-progress→complete` + seals; then
  session wrap (PROGRESS + resume-brief; /usage backfill of both plans' cost.actual).
