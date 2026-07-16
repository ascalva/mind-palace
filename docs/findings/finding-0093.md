---
type: finding
id: finding-0093
status: open
created: 2026-07-16
updated: 2026-07-16
links:
  - docs/build-plans/bp-054/plan.md
  - eval/harness/registry.py
  - eval/harness/fibers.py
  - core/dreaming/shadow.py
  - tests/unit/test_registry_res.py
ftype: spec-fidelity
origin_plan: bp-054
route: builder
resolution: builder-resolved (annotated; literals + machine-checked agreement test)
---

# bp-054 Item 2 pins "import FB-1's name constants into the registry" — but that closes a circular import

## What
The plan (Item 2 acceptance, §6) and the build brief pin: register `sigma_persistence.*` by
**importing** FB-1's exported name constants (`METRIC_MEAN … METRIC_N_CLAIMS` from
`eval/harness/fibers.py`), "don't restring them". Doing that literally — a module-scope
`from eval.harness.fibers import …` in `eval/harness/registry.py` — closes an import cycle:

```
eval.harness.registry  →  eval.harness.fibers  →  core.dreaming.shadow  →  eval.harness.registry
                          (fibers.py:52)          (shadow.py:58: from eval.harness import registry)
```

`registry` currently has NO edge to `fibers`; the two back edges (`fibers→shadow`, `shadow→registry`)
both live in **read-only bp-050 files**, so the cycle cannot be broken by restructuring the importers.

## Why it matters (demonstrated, not hypothesized)
With the import added, resolution succeeds only when `registry` is the FIRST module imported. When
`fibers` or `shadow` is the entry point (both realistic — `scripts/fibers.py`, the dreaming pipeline,
pytest collection order), Python raises at import time:

```
ImportError: cannot import name 'METRIC_FRAC_GE_STRONG' from partially initialized module
'eval.harness.fibers' (most likely due to a circular import)
```

Placing the import at the bottom of `registry.py` (after every symbol is defined) fixes the
`registry`-first order but NOT the `fibers`-first / `shadow`-first orders — the partially-initialized
`fibers` module still lacks its `METRIC_*` constants at the moment `registry` tries to import them.
An import-time failure of the metric registry is a hard boot failure of the eval harness.

## Resolution (builder-resolved, this session)
Register the five `sigma_persistence.*` names as **exact literal strings** in `registry.py` (keeping
`register`/`get`/`REGISTRY` eager, cycle-free, and semantically identical to the existing `_BUILT`
set), and **machine-enforce name agreement** in `tests/unit/test_registry_res.py`:
`test_sigma_persistence_family_resolves_as_res_sigma` imports the FB-1 constants and calls
`registry.get(METRIC_*)` for each — a fail-closed `get`, so any future drift between FB-1's writes and
the registry's literals raises `KeyError` and fails CI. The finding-0086 failure class (a name written
but not resolvable) stays foreclosed — enforced by test rather than by an unsafe import edge. This is
functionally equivalent to "import don't restring" for the concern the pin protects (no silent drift),
without introducing a fragile boot-order dependency.

`structural_axes.*` needs no such workaround — shadow writes those names as string literals (no
exported constant), so the registry matches the literals directly and the test derives the expected
names from `StructuralSnapshot.structural_axes()` (the writer's own source of truth).

## Routing
`spec-fidelity`, builder-resolved + annotated — no design decision owed, not a blocker. Flagged so the
orchestrator can, if desired, batch a later tidy: export the two `structural_axes` axis names as
constants beside the axis dict in `core/complex/temporal.py`, and/or relocate FB-1's `METRIC_*`
constants into a cycle-free leaf module so a future registry could import them safely. Neither is owed
by bp-054.
