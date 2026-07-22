---
type: build-plan
id: bp-087
track: agentic-loop
status: complete
design_ref:
  - docs/design-notes/agentic-loop.md
contract: builder
write_scope:
  - docs/findings/**
session_budget: 1
cost:
  estimate:
    model: fable
    tokens: 90k
  actual:
    model: sonnet          # re-tiered fable→sonnet at spawn (read-only measurement, no reasoning depth); tier verified via completion usage
    tokens: 98195
    tool_calls: 87
    duration_min: 9
    ratio: 1.09            # vs the 90k estimate — well-pinned; M-6c honestly deferred, not forced
    session_delta: "drew the weekly all-models pool (61%→ ~+small); ran parallel with bp-085 G-A"
depends_on: []
parallelizable_with: [bp-083, bp-084, bp-085, bp-086, bp-088]
created: 2026-07-21
updated: 2026-07-21
links:
  - docs/design-notes/agentic-loop.md
  - core/integrator.py
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — AL-2: the M-3 / M-6 readings (C-coverage + gap-instrument baselines)

> Graduated from ratified `dn-agentic-loop` §2.8 / §3 (AL-2). Read-only: run the C-coverage gauge
> and record the gap-instrument baselines the note left "owed" (M-3 "reading not yet taken"; M-6
> "owed — record once before any steering heuristic is even sketched"). No code written beyond the
> findings artifact; every reading is a *delta anchor* for the next pass. This is a measurement
> session — it arguably rides pre-ratification.

## 0. Mode & provenance

Investigation and planning produced this; implementation proceeds item-by-item on owner approval.
`proposed → ready` stays owner-only. Read-only over the live `data/` stores. The readings land as a
finding (builder-writable) and in the session journal; the orchestrator checkpoints the baselines
into PROGRESS afterward (PROGRESS is orchestrator single-writer — the builder never edits it).

## 1. Objective

Take and record the two owed baselines from §2.8 — **M-3** (C-coverage: the fraction of integrable
D-events that produced a C-witness, via the built gauge) and **M-6** (gap-instrument baselines:
hole count/persistence, doc_coverage, drift profile vs anchor) — as a dated finding, so the next
pass measures deltas rather than absolutes and PD-3's precondition is on the record.

## 2. Context manifest

Read whole, in order:

1. `docs/design-notes/agentic-loop.md` §2.8 — the baseline table (M-1…M-7, the 2026-07-21 values
   already taken) and the two owed rows M-3 / M-6; the "no plan may skip the M-row it depends on"
   rule.
2. `core/integrator.py:78-118` — `coverage()` (`:82`), `CoverageGauge` (`:97`), `coverage_gauge(
   events, edges)` (`:117`): the C-coverage instrument as a standing view over the L1 + edge stores.
3. `core/complex/topology.py:104` — `long_lived_holes(D, *, min_persistence)` (the hole lens);
   `eval/drift.py` (A1 drift gauge); the φ_code doc_coverage plane.
4. `docs/design-notes/agentic-loop.md` §2.6 G-A/G-C — context for what the baselines gate (the
   probe loop's steering, PD-3).

## 3. Investigation & grounding

Touches existing code by READING/RUNNING it only. Grounded at HEAD (`d08da37`): `coverage()`
(`integrator.py:82`), `coverage_gauge` (`:117`), and `long_lived_holes` (`topology.py:104`) all
present; `eval/drift.py` and `eval/effector_drift.py` present.

- **Q1 — can C-coverage be read without a write?** Yes — `coverage_gauge(events, edges)` builds a
  standing view over the L1 action log (`ChatEventStore`) and the minted `CausalEdgeStore`; both
  are opened read-only. The reading is `gauge.coverage()`, a float.
- **Q2 — what are the M-6 instruments' read entry points?** hole lens: `long_lived_holes` over the
  σ-graph's persistence diagram; doc_coverage: the φ_code plane's coverage read; drift: `eval/drift.py`
  A1 vs the anchor. The code does not settle whether each is runnable standalone over live `data/`
  without a harness fixture — Item 15 probes and records "read: X" or "instrument-blocked: <why>".
- **Q3 — live-store safety.** All reads are over `data/` read-only; no write handle is opened. If
  any instrument requires a write (e.g. to materialize a spine), that is a **finding**, not a
  workaround — record the block, do not write.

**Additional risks:** stale/empty stores giving a misleading zero — the reading must record the
store populations alongside each ratio (the note's §2.8 pattern), so a "0.0 coverage" is
distinguishable from "no D-events yet".

## 4. Reconciliation

N/A — nothing corrected or extended in committed code. The plan records readings; it edits no
ratified text and no source.

## 5. Write scope

`docs/findings/**` only — the readings land as a dated finding (and in the session journal, which
is always writable). Deliberately OUT of scope: `core/**` and `eval/**` (read-only — run existing
instruments, write none), `docs/PROGRESS.md` (orchestrator single-writer), every store.

## 6. Interfaces pinned inline

```python
# core/integrator.py:82,117
class CoverageGauge:
    def coverage(self) -> float: ...                       # fraction of integrable D-events with a C-witness
def coverage_gauge(events: ChatEventStore, edges: CausalEdgeStore) -> CoverageGauge: ...
# core/complex/topology.py:104
def long_lived_holes(D: np.ndarray, *, min_persistence: float) -> list[Hole]: ...
```
The §2.8 baseline shape (copied so no design is inferred): each row = `measurement | value |
instrument`; a reading records the value AND the underlying populations (e.g. "coverage = X over
N integrable D-events, M C-edges").

## 7. Items

### Item 15 — take M-3 and M-6, record as a finding
- **Objective:** run `coverage_gauge(...).coverage()` over live stores (M-3) and the three
  gap-instrument reads (M-6: hole count/persistence, doc_coverage, drift-vs-anchor), and write the
  values + populations + CN-1 index into a dated finding.
- **Files:** `docs/findings/finding-0143.md` (or next free id).
- **Acceptance test:** the finding records M-3's coverage float with its populations, and M-6's
  three reads (each a value or an explicit "instrument-blocked: <reason>"), dated 2026-07-21+, each
  carrying its index; it names PD-3's precondition as now satisfied (M-6 on the record).
- **Falsifier:** a "0.0" or "null" recorded without its population context (indistinguishable from
  a real-zero vs no-data) — malformed.
- **Invariant(s):** no store write; no `core/**` or `eval/**` edit; PROGRESS untouched.
- **Touches stored data?** Reads only. **Parallelizable?** Yes. **Depends on:** none.

## 8. Math carried explicitly

- **C-coverage = |integrable D-events with a C-witness| / |integrable D-events|** — *measures:* how
  much of the supersession fabric the integrator has witnessed. *valid when:* "integrable" is the
  gauge's own definition (do not redefine). *fails its keep if:* recorded without the denominator
  (a bare ratio hides an empty corpus).

## 9. Non-goals

No steering heuristic (PD-3 — parked until charters are owner-wired AND these baselines exist; this
plan only *records* the precondition). No instrument change. No write to any store, `core/`, `eval/`,
or PROGRESS. No new module.

## 10. Stop-and-raise conditions

- An M-6 instrument needs a write (e.g. materialize a spine) to read ⇒ **stop** that row, record
  "instrument-blocked: needs write", file it — never open a write handle to force a read.
- A coverage read that requires the daemon running / stores the session can't reach read-only ⇒
  record "deferred: needs live daemon", continue the other rows.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| PD-3 curiosity/steering heuristic | surfacing only; not designed | design a steering policy now (scheduling ahead of the R&D flag) | owner wires the R&D flag + a charter entry point AND these M-6 baselines are recorded (this plan) |

## 12. Dependency & ordering summary

Single item, no dependencies; parallelizable with every other plan in this graduation (write scope
is `docs/findings/**` + journal only). Blast radius: read-only sensing. Owner steer (session-40
brief): this and G-A (bp-085) are the **priority** graduations — they generate the data the parked
questions need.
