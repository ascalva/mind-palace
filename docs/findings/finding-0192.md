---
type: finding
id: finding-0192
status: open
created: 2026-07-25
updated: 2026-07-25
links:
  - docs/audits/ops-wave-2026-07-25.md
  - tests/unit/test_store_cost_ratchet.py
  - ops/lifecycle/snapshot.py
ftype: discovery
origin_plan: orchestrator
route: orchestrator
resolution: null
---

# Instrument blindness is a recurring defect class: three slices shipped meters that do not watch the route the fix uses

## What
Three of five slices shipped an instrument blind to the thing it certifies:

bp-100 — `_instrument` hooks only `VectorStore._table()`. A mutant keeping a byte-identical
O(N) scan but reaching the table via `self._db.open_table(TABLE)` turns both ratchets GREEN
with the defect intact. What saved bp-100 was strict-xfail markers XPASSing — an ACCIDENTAL
net. Closed properly by bp-103; verified at HEAD.

bp-102 — the wedge detector (finding-0188).

bp-103 — the cost ratchet counts `to_pylist()` and `scan()/search()`, but the shipped fix
uses `count_rows(where)` + `update(where, values)`, which fall through
`_CountingTable.__getattr__` UNCOUNTED. The green is satisfied by any implementation
avoiding the old routes, including one that does nothing. What closes the hole is an
assertion in a helper (`_cost_of_supersede`), not the ratchet — and the plan never named
that as the guard.

## Why it matters
This is the same defect class three builds running, and it is exactly what the wave's own
adversarial question was written to catch. It needs to become doctrine rather than be
rediscovered per-slice.

Operational form for the standing auditor brief: enumerate the routes the meter watches;
enumerate the routes the fix uses; if the intersection is empty, the green measures
absence, not correctness. Corollary for BUILDERS: a negative control must cover the
BYPASS, not the hooked path.

Residual on bp-103 worth noting: the objective is "cost independent of N", but only the
Python-marshalling term is measured. `count_rows(where)` on an unindexed `source_path` is a
server-side full scan — O(N) in Rust, unbounded by any test.
