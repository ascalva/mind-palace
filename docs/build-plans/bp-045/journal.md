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
