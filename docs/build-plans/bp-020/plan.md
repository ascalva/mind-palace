---
type: build-plan
id: bp-020
status: in-progress
design_ref:
  - docs/design-notes/self-sensing.md # B-c: backfill over all sealed plans' graduation/seal commits; PD-d
contract: builder
write_scope:
  - "docs/build-plans/bp-013/plan.md" # the cost.actual annotation ONLY (Item 9) — one frontmatter block
  - "docs/build-plans/bp-020/**"
  - "docs/findings/**"
session_budget: 1
cost:
  estimate: { model: sonnet, tokens: 100k } # small: one annotation + a dry-run/live-run pair with crisp count checks
  actual: null
depends_on: [bp-019] # runs the sensor bp-019 builds
parallelizable_with: []
created: 2026-07-12
updated: 2026-07-12
links:
  - docs/build-plans/bp-013/journal.md # the partially-recoverable actuals (seal block, :263-265)
  - docs/brainstorms/cost-forecasting.md # the forecasting dataset this backfill seeds
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — B-c: the history backfill — the cost stream's first live observations

> **Every section below is required.** N/A is an accountability act.

## 0. Mode & provenance

Graduated 2026-07-12 from the **ratified** `dn-self-sensing` (§3.3 B-c; PD-d's backfill
default, supported by V3's measured feasibility). Investigation and planning produced
this; implementation proceeds item-by-item on owner approval. `proposed → ready` is the
owner's hand edit. Third and last plan of the family; the only one that touches live
stored data.

## 1. Objective

φ_self's first live run projects the full main history of build-plan cost facts into
the agent-observation store — verified dry-run-first, attested, with bp-013's
recoverable actuals annotated beforehand so the estimate/actual join covers every
sealed plan that has a complete cost record.

## 2. Context manifest

1. `docs/design-notes/self-sensing.md` §2.3 (S1 grain), §3.2 V3 (the measured
   inventory), §3.3 B-c, PD-d.
2. `docs/build-plans/bp-019/plan.md` §6(d,e,f) — the sensor contract this plan runs.
3. `docs/build-plans/bp-013/journal.md:263-265` — the seal's usage record (the
   annotation source, partial).
4. `docs/templates/build-plan.md:11-17` — the `cost:` block shape the annotation must
   match.
5. `ops/self_sensor.py` + `scripts/sense_self.py` (as landed by bp-019).

## 3. Investigation & grounding

- **Q1 — what should the backfill find (V3's measured baseline)?** 4 complete
  estimate/actual pairs (bp-011 0.47×, bp-012 0.52×, bp-014 0.29×, bp-015 0.26×),
  3 estimate-only (incl. bp-013), 11 pre-rule plans with no cost block (bp-000..010 —
  zero rows, zero errors). Post-Item-9 the expectation becomes **5 pairs** (bp-013
  joins, flagged partial). bp-016..020's own estimates land as observations at their
  landing commits too — the count assertion uses ≥, not ==, because history keeps
  moving.
- **Q2 — are bp-013's actuals recoverable?** PARTIALLY:
  `docs/build-plans/bp-013/journal.md:263-265` records the seal — "Items 6-7 … usage
  NOT captured (no completion notification recorded — a ledger gap to avoid next
  time). Item 8 + finding renumber: resume builder, **opus, 54,048 tokens**, …". The
  honest annotation is the recorded partial with an explicit partial marker (§6(a)) —
  never a reconstructed guess. The code does not settle the Items-6-7 number; nothing
  can (it was never recorded).
- **Q3 — is annotating a sealed plan's cost block legitimate?** Yes: `cost.actual` is
  BY DESIGN "filled at SEAL from the completion notification"
  (`docs/templates/build-plan.md:15-17`) — the fill was owed and missed (the journal
  itself calls it a ledger gap). This is late ledger discipline, not history rewriting:
  the plan's sections, items, and seal text are untouched; the fact lands at a new
  commit, which is exactly the grain φ_self records (bp-019 §3 Q3 — an edited fact is
  a new observation at its landing commit, honestly timestamped).
- **Q4 — dry-run mechanics?** The sensor takes injected store/handoff handles (bp-019
  §6(d) dataclass fields) — a dry-run is `SelfSensor` wired to tmp/:memory: stores
  over the REAL repo, reporting counts without touching `data/`. No new tooling needed.

**Additional risks surfaced during reading:** the live run writes
`data/agent_observations.sqlite` on THIS machine — the builder must run it from the
MAIN checkout's repo path? No: the sensor reads git history (identical in a worktree)
but `data/` paths anchor to config; the LIVE run is therefore executed by the
ORCHESTRATOR at seal from the main checkout (builders never touch the main checkout —
finding-0031), with the builder delivering the verified dry-run + the exact command.
Pinned in Items 10–11.

## 4. Reconciliation

- `docs/build-plans/bp-013/plan.md` front-matter `actual: null` → **[banner:
  correction]** carried by Item 9: the null was a missed seal fill (the journal's own
  "ledger gap" admission); corrected with the recorded partial + marker comment. No
  other line of bp-013 changes.

## 5. Write scope

In: bp-013's plan front-matter cost block (one edit), own plan dir, findings. Out,
deliberately: ALL code (this plan runs bp-019's tooling, changes none of it); every
other sealed plan (their cost blocks are either complete or honestly pre-rule); the
live `data/` stores (the live run is orchestrator-executed at seal, Q4/§3 risks);
design notes; the foundation denylist.

## 6. Interfaces pinned inline

**(a) The bp-013 annotation (Item 9, exact target state):**

```yaml
cost:
  estimate: { model: opus, tokens: 200k } # (existing line — UNTOUCHED, whatever it says)
  actual: { model: opus, tokens: 54048, tool_calls: null, duration_min: null } # PARTIAL — Item 8 + finding-renumber session only; the Items 6-7 session was never captured (journal :263-265, the recorded ledger gap). Late seal-fill, 2026-07-12.
```

(The builder copies the REAL existing estimate line verbatim; only `actual:` changes.
The `# PARTIAL …` comment is the honesty marker — payload consumers see it via `raw`.)

**(b) The dry-run harness (Item 10):** `SelfSensor` with tmp-path store + handoff +
`history=None`, real repo, real branch `main`; report printed. No attestor (a dry-run
must not enter the attestation chain).

**(c) The live command (Item 11, orchestrator-executed at seal, main checkout):**

```
uv run scripts/sense_self.py
```

followed by the verification queries (sqlite3 CLI, read-only): total rows; rows per
key; the estimate/actual join per subject_id — expected ≥5 complete pairs incl.
bp-013 (Q1).

## 7. Items

_(family numbering continues from bp-019)_

### Item 9 — bp-013's late seal-fill (the recorded partial)

- **Objective:** `cost.actual` per §6(a); nothing else in the file changes.
- **Files:** `docs/build-plans/bp-013/plan.md`
- **Acceptance test:** `git diff` shows exactly one changed line (+ comment); the
  bp-019 parser (unit-invoked on the edited text) yields
  `{model: 'opus', tokens: 54048, raw: …}` for `(bp-013, actual)`.
- **Falsifier:** any invented number (tool_calls/duration for the uncaptured session,
  or a "corrected" total) — the annotation must carry ONLY what the journal recorded.
- **Invariant(s):** sealed-plan content untouched beyond the one block; the journal is
  not edited (it is the source, and it is sealed).
- **Touches stored data?** no
- **Parallelizable?** yes **Depends on:** none

### Item 10 — the dry-run inventory (counts before writes)

- **Objective:** run §6(b) over full main history; journal the per-plan fact table and
  assert it against Q1's baseline.
- **Files:** `docs/build-plans/bp-020/journal.md` (the inventory table)
- **Acceptance test:** dry-run report shows: ≥5 complete estimate/actual pairs
  (post-Item-9, bp-013 included); bp-000..010 contribute zero rows and zero errors;
  zero parse warnings; re-running the dry-run yields identical counts (determinism).
- **Falsifier:** the note's B-c falsifier — a sealed plan with a complete cost block
  yields no estimate/actual join; or any parse warning (V3 said the corpus is clean —
  a warning means the parser regressed or a plan drifted; file the finding either way).
- **Invariant(s):** no write outside tmp paths; no attestation emitted.
- **Touches stored data?** no (that is the point)
- **Parallelizable?** no **Depends on:** Item 9 (the join count includes bp-013),
  bp-019 complete

### Item 11 — the live backfill (orchestrator-executed at seal)

- **Objective:** the first real projection: §6(c) from the main checkout, then the
  verification queries; counts must equal Item 10's dry-run exactly (same HEAD).
- **Files:** `docs/build-plans/bp-020/journal.md` (the live counts + the first join
  table — the stratum's first real contents, worth recording)
- **Acceptance test:** live row count == dry-run count at the same HEAD; every
  projected sha has a `project_agent_observations` attestation; a SECOND
  `uv run scripts/sense_self.py` adds zero rows (idempotence live, not just in tests).
- **Falsifier:** live counts diverge from the dry-run at identical HEAD (the sensor is
  not deterministic, or the dry-run harness lied); or the second run adds rows.
- **Invariant(s):** builders never touch the main checkout (the run is the
  orchestrator's at seal — the builder's deliverable is the verified dry-run and the
  exact command); the store's reset semantics stay as bp-019 wired them.
- **Touches stored data?** YES — the plan's only such item; the Item 10 dry-run is the
  mandated verification pass, and the store is corpus-class (a wrong write is
  recoverable by wipe + re-projection, recorded for proportionality).
- **Parallelizable?** no **Depends on:** Item 10

## 8. Math carried explicitly

N/A — no mathematical object implemented (the estimate/actual ratio lives in the
journal's inventory table as plain division; the calibration methodology explicitly
refuses modeling at n≈5 — dn-self-sensing §2.7).

## 9. Non-goals

Any retune of estimation practice from the joined data (n≈5; the no-retune-off-one-
point discipline generalizes); the report generator (parked, `cost-forecasting.md`);
annotating any plan other than bp-013 (others are complete or honestly pre-rule);
adding streams; touching code; wiring any consumer.

## 10. Stop-and-raise conditions

The dry-run surfaces a parse warning or a missing join Q1 predicted present (finding
first — the discrepancy is data about either the parser or the corpus; never "fix" a
plan file to make the sensor happy beyond the licensed Item 9); bp-013's journal seal
turns out to say something other than Q2 quotes at the builder's HEAD (re-ground, do
not improvise); the live run (orchestrator's) diverges from the dry-run (stop, wipe
per corpus-class semantics, re-investigate before re-running).

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
| --- | --- | --- | --- |
| bp-013's unrecoverable Items-6-7 usage | absent forever; the partial is marked, never estimated | reconstruct from context length/turn counts (a guess entering a measurement stream poisons the calibration set) | never — the gap IS the datum (ledger discipline made visible) |
| backfill depth | full main history (PD-d default; V3: parse trivial, corpus clean) | seal-commits-only (misses estimate landings; the estimate/actual time-coordinate split is the schema's point) | never — decided by the ratified grain |
| who runs the live write | orchestrator at seal, main checkout | builder-in-worktree (config-anchored `data/` paths + finding-0031's pointer-bleed class make builder-side live writes the wrong pattern) | a future sandboxed data-runner exists |

## 12. Dependency & ordering summary

Item 9 → Item 10 → Item 11; strictly serial, blast-radius ascending (one-line docs
edit → read-only dry-run → the single live write). Cross-plan: **depends_on bp-019**
(and transitively bp-018). After Item 11 the stratum is live: every future main commit
self-projects incrementally via the hook, and the family's remaining licensed work is
exhausted — consumers require a new design pass (dn-self-sensing §1.2).
