---
type: finding
id: finding-0188
status: resolved
created: 2026-07-25
updated: 2026-07-25   # /triage session-49: DISCHARGED by bp-105 Item 1
links:
  - docs/audits/ops-wave-2026-07-25.md
  - ops/lifecycle/snapshot.py
  - scheduler/code_sync.py
  - tests/unit/test_status_incident_oracle.py
ftype: spec-defect
origin_plan: orchestrator
route: orchestrator
resolution: |
  DISCHARGED by bp-105 Item 1 (`2add267`). The design call this finding routed to the
  orchestrator (difference `vector_rows` vs add a per-job heartbeat) was settled at build
  time by grounding: every channel the plan listed was eliminated, and the discriminator
  built is the store's OWN FILESYSTEM CLOCK — a derivative, not a level, which is the
  finding-0172 defect this finding named. A healthy multi-hour backfill now reads
  `embedding: YES` and raises no flag; `⚠ WEDGED` fires only when embedding genuinely
  stops. Verified by mutation: 8 planted, 8 caught, including N1-N3 mutating each
  predicate to a permanent alarm (bp-105 journal, Checkpoint 3).
  The two bp-102 tests this finding named were ANNOTATED, not quietly deleted — including
  `test_a_running_row_under_a_LIVE_daemon_is_not_called_orphaned`, which had encoded the
  cry-wolf string as EXPECTED.
---

# The wedge detector cannot distinguish a healthy backfill from a wedged one — the plan's stated purpose

## What
bp-102 §0: "Without a throughput and rate readout there is no way to tell a healthy
backfill from tonight's wedged one." Both states were constructed and rendered; every
anomaly flag is IDENTICAL.

`stalled` (`snapshot.py:574`) and `wedged` (`:585`) both key on `done_in_window == 0`, a
job-BOUNDARY count. The failure mode is intra-job: `code_backfill_handler`
(`scheduler/code_sync.py:53`) makes one synchronous non-checkpointing call over 423,855
ledger rows and `Supervisor.tick` waits, so a HEALTHY multi-hour backfill emits zero
terminal transitions and trips every flag continuously.

The false-alarm guard cannot catch it: its "healthy" fixture has `depth == 0` and no
running row, so both predicates are unreachable by construction. Mutating `stalled` to a
permanent alarm passes all 9 tests. The build also encodes the false alarm as EXPECTED —
`test_a_running_row_under_a_LIVE_daemon_is_not_called_orphaned` asserts the cry-wolf
string is present.

## Why it matters
bp-102 §10 made this disqualifying on its own terms: "The false-alarm falsifier fires ->
STOP; an instrument that cries wolf will be ignored during the next incident." It fires,
and the build shipped.

Directly degrades restart checklist step 5 ("watch the rate — bp-102's block is the
instrument"): the re-enqueued backfill will trip every flag while perfectly healthy.

The fix is cheap and half-built: `store.vector_rows` is already read and printed as a
LEVEL. Differencing it across two samples is the discriminator — which means the build
repeated, for its single discriminating figure, the levels-not-derivatives defect that
finding-0172 is about. Orchestrator-routed: whether to difference `vector_rows` or add a
per-job heartbeat is a design call.
