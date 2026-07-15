---
type: finding
id: finding-0082
status: resolved
created: 2026-07-15
updated: 2026-07-15
links:
  - core/stores/versions.py
  - core/temporal_view.py
  - docs/build-plans/bp-038/plan.md
ftype: discovery
origin_plan: bp-038
route: builder
resolution: >-
  Resolved-in-place in bp-038 (builder, codebase): `supersession_wellfounded` was narrowed to
  require an EXPLICIT `doc_ids` argument rather than a store-wide enumerator — the missing
  `VersionStore` doc_id enumerator is not needed for the well-foundedness check as built. Swept to
  resolved at /triage 2026-07-15 (status field lagged the in-plan resolution).
---

# `VersionStore` has no doc_id enumerator — `supersession_wellfounded` can't scan "all versioned docs"

## What
`core/stores/versions.py` exposes only per-`doc_id` reads (`current`, `history`, `supersessions`),
plus `count()` and `migrate_rekey_doc_id` — **no method to enumerate the distinct `doc_id`s in the
store** (no `doc_ids()` / `all()` / `SELECT DISTINCT doc_id`). bp-038's `supersession_wellfounded`
(the poset `δ_D²=0` health read) needs a doc_id LIST to build the poset, so the plan's envisioned
`doc_ids=None → all versioned docs` scope is not reachable without either editing `versions.py` (out
of bp-038's write_scope) or reaching its private `_conn` (breaks the encapsulation discipline
`ReferenceView`/`TemporalView` establish — the scope guard treats `_conn` as unreachable).

## Why it matters
The whole VALUE of the poset well-foundedness check is catching a supersession **cycle** (a rename
that forked a version chain — the bp-031 gap). A cycle lives in *some* doc's chain, so detecting it
requires scanning *every* versioned doc. Without an enumerator, `supersession_wellfounded` can only
check an explicitly-supplied `doc_ids` list — so the convenience factory
`open_supersession_wellfounded` scopes to the **anchor's corpus nodes** (docs currently participating
in citations; `doc_id == source_path`, bp-031), which (a) couples the poset axis to the citation axis
and (b) MISSES any versioned doc that is not a current citation endpoint (e.g. a deleted doc whose
chain still carries a defect). The health check is therefore partial.

## Re-entry condition
Not parked (this is a `discovery`, resolved-in-place for bp-038 by narrowing to explicit `doc_ids` +
the corpus-node-scoped factory). Re-open for a follow-on when a **full-corpus** supersession health
scan is wanted: add a read-only `VersionStore.doc_ids() -> list[str]` (`SELECT DISTINCT doc_id`) —
an **owner-gated write to `versions.py`** (a store surface) — then `supersession_wellfounded(doc_ids=
None)` can default to all versioned docs, decoupling it from the citation axis.

## Routing
`codebase` → the builder resolved in bp-038: `supersession_wellfounded` requires explicit `doc_ids`
(no all-docs default); `open_supersession_wellfounded` scopes to the anchor's corpus nodes. Recorded
here + in the bp-038 journal + `core/temporal_view.py` docstrings. The `VersionStore.doc_ids()`
addition is a small future plan (store-surface write, owner-gated) — not part of bp-038.
