---
type: finding
id: finding-0072
status: resolved
created: 2026-07-13
updated: 2026-07-13
resolution: >
  Owner authorized (2026-07-13, in-session) the orchestrator to add the four
  tests/integration/* acceptance-test paths to bp-029's write_scope; the edit landed and
  the Items 27–30 acceptance tests were authored + run green. Same class as finding-0071;
  the standing fix (enforce the test-path check at /graduate) is recorded and still owed.
links:
  - docs/build-plans/bp-029/plan.md
  - docs/findings/finding-0071.md
ftype: spec-defect
origin_plan: bp-029
route: orchestrator
---

# bp-029 write_scope omits the §7 test paths (blocks acceptance) — a recurrence of finding-0071

## What

bp-029's `write_scope` is `cloud/fetcher/**`, `core/research/**`,
`core/stores/curated_store.py`, `config/**`, `docs/reference_material/**` (plus the
auto-granted plan file, its `journal.md`, and `docs/findings/**`). It lists **no test
paths**. Every §7 item (27/28/29/30) mandates a unit/integration **acceptance test**, and
`scope-guard` allows writes only under `write_scope` (+ plan/journal/findings) — so any write
under `tests/**` is DENIED. As written, the acceptance tests cannot be authored; the build
blocks on exactly the gap finding-0071 hit for bp-028.

This is the graduation-check the resume brief called out ("write_scope must list its test
paths … a graduation must include every file the §7 acceptance tests write, or the build
blocks. Check this at /graduate") — missed for bp-029 as well.

The tests the items call for (matching sibling layout: `tests/integration/test_fetcher.py`,
`test_vectorstore.py`, `test_research_*.py`):

- `tests/integration/test_fetcher_fulltext.py` — Item 27 (open-access full-text fetch; fake `http_fetch`)
- `tests/integration/test_curated_store.py` — Item 28 (separate curated store; gitignore + round-trip)
- `tests/integration/test_research_persist.py` — Item 29 (licence-gated chunk→embed→curated; fake embedder)
- `tests/integration/test_curate_manifest.py` — Item 30 (end-to-end 27→30 on temp manifests; the dangling-claim guard)

## Why it matters

The build's core deliverable (the EMBED tail, invariant-adjacent: Inv 2/11 + the licence
gate) must not land untested. Correcting `write_scope` is a capability-surface change to an
owner-blessed, invariant-adjacent plan — owner-gated per the finding-0071 ruling ("never route
around" a scope denial; the orchestrator does not silently expand its own capability). All
NON-test changes are in scope and proceed; only test authoring is blocked pending the paths.

## Resolution (pending)

Owner hand-adds the four `tests/integration/*` paths above to bp-029's `write_scope`
(the finding-0071 pattern). Then the acceptance tests for Items 27–30 are authored and the
build completes. Standing fix already recorded: enforce the test-path check at /graduate so
this class does not recur a third time.
