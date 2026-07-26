---
type: finding
id: finding-0192
status: routed
created: 2026-07-25
updated: 2026-07-26
links:
  - docs/audits/ops-wave-2026-07-25.md
  - tests/unit/test_store_cost_ratchet.py
  - ops/lifecycle/snapshot.py
ftype: discovery
origin_plan: orchestrator
route: orchestrator
resolution: routed — SPLIT: item A is a process rule (agent-writable, no gate); item B is a codebase residual with no owner
---

# Instrument blindness is a recurring defect class: three slices shipped meters that do not watch the route the fix uses

> **Triage 2026-07-26 (session-52) — still live; carries TWO unrelated items, so split it.**
> (i) `_CountingTable` (`tests/unit/test_store_cost_ratchet.py:117-131`) still wraps only
> `to_arrow`/`scan`/`search` with a passthrough `__getattr__` — so the shipped fix's
> `count_rows(where)` and `update(where, …)` are **still uncounted**, and the ratchets' green is
> carried by the semantic assertion at `:168`, not by the meter.
> (ii) There is **no scalar index on `source_path`** anywhere (`grep create_scalar_index|create_index|btree`
> over `core/ ops/` → zero hits), so `count_rows(where)` (`vectorstore.py:263-266`) is a server-side
> full scan unbounded by any test.
> The doctrine ask has **not** landed — the route-intersection rule appears only here and in
> `docs/audits/ops-wave-2026-07-25.md`.
> **Item A (process, cheap, no owner needed):** add it as a named rule in
> `.claude/skills/build-plan/SKILL.md` §7 — *enumerate the routes the meter watches vs the routes the
> fix uses; an empty intersection means the green measures absence* — corollary: a negative control
> must cover the **bypass**.
> **Item B (codebase):** the `count_rows(where)` O(N) residual needs a `source_path` scalar index or
> an explicit accepted-cost statement with a bound. Fold into the next store plan.

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
