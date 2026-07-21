---
type: finding
id: finding-0126
status: open
created: 2026-07-20
updated: 2026-07-20
links:
  - docs/design-notes/agent-taxonomy.md               # the park whose stated blocker is stale ("diachronic dreamer — blocked on certified cuts (G3)")
  - docs/design-notes/global-event-clock.md           # GC-3 — the named blocker
  - docs/design-notes/cross-strata-dreamer.md         # its gate G3 ("cut discipline") — likewise satisfied on the substrate side
  - docs/design-notes/synchronic-diachronic-dreamer.md  # §2.8 — the park honored with the re-entry restated
  - core/temporal/spine.py                            # the built certificate machinery (bp-055)
ftype: discovery
origin_plan: orchestrator          # session-39 dispatched fable design pass (dn-synchronic-diachronic-dreamer)
route: orchestrator                # design
resolution: null
---

# The diachronic dreamer's stated blocker (certified cuts / G3) is built; the park's re-entry needs restating

## What

`dn-agent-taxonomy` (ratified 2026-07-18) parks the diachronic dreamer as "blocked on certified
cuts (`global-event-clock` G3)" with re-entry "G3 materializes." Grounding the
synchronic/diachronic design pass against the code shows that blocker is **already satisfied**:
GC-3 shipped with the temporal quartet (bp-055, sealed 2026-07-17) —
`core/temporal/spine.py:159-274` holds `CertifiedCut` (frontier vector + certificates), the three
certificate classes {COMMIT, TROUGH-quiescent, HANDOFF-empty}, per-stratum certificate
composition, and refusal-not-fabrication semantics. `dn-connectivity-instruments` (ratified
2026-07-17) already lists certified cuts among "the substrate, all built."
`dn-cross-strata-dreamer`'s gate G3 ("the cut discipline: CS-a or per-stratum-anchor design")
is likewise substrate-satisfied: `dn-global-event-clock` is ratified and GC-3 shipped.

The park itself does NOT dissolve — what actually remains before diachronic execution is:
(i) the interval-window instrument family (the memory curve and companions,
`docs/brainstorms/graph-at-a-past-cut.md` — designed at brainstorm grade, not yet graduated or
built); (ii) a harness lane for interval-window per-grant A/B; (iii) owner sequencing. But the
park's *stated* re-entry condition ("G3 materializes") has already fired, so as written it can
no longer gate anything.

## Why it matters

A park whose re-entry condition is already true is a silent unpark waiting to be claimed — a
future plan could cite "G3 materialized" as license for diachronic execution while the real
prerequisites (interval instruments, the harness lane) are absent. The re-entry must name the
actual remaining gates. `dn-agent-taxonomy` is ratified/A8 (agent-immutable), so the correction
rides this finding + the draft note, never an edit to the ratified text.

## Re-entry condition

`dn-synchronic-diachronic-dreamer` §2.8 / SD-a records the restated re-entry: the owner unparks
diachronic execution after (a) the `graph-at-a-past-cut` instrument family graduates through its
own design note, AND (b) the synchronic dispatcher (its plan D-1) is sealed. This finding closes
when the owner either ratifies that note (adopting the restated re-entry) or rules a different
re-entry at triage.

## Routing

`design` → orchestrator. No owner action needed before the dn-synchronic-diachronic-dreamer
ratification review; the ruling there subsumes this. If that note is rejected, batch to
`owner-questions.md` as its own question (the stale re-entry survives the note's rejection).
