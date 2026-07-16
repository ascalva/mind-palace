---
type: finding
id: finding-0088
status: resolved
created: 2026-07-16
updated: 2026-07-16
resolution: >
  Orchestrator merge-scrutiny fix (bp-046, 2026-07-16): made the two hardcoded per-lever
  assertions in test_shipped_manifest_loads_and_covers_every_lever registry-faithful —
  `pol.subsystem == LEVERS[name].section` (matching its sibling default-policy test) and
  `pol.objective in {"f9_composite", None}`. Full non-live suite green (1264 passed). The
  parked sub-question (whether config/tuning.toml should gain an explicit
  [tuning.dream_rnd_sigma] block) stays deferred per bp-046 §9 (default policy, no edit).
links:
  - docs/build-plans/bp-046/plan.md
  - tests/unit/test_tuning_manifest.py
  - config/tuning.toml
  - eval/harness/tuning.py
  - ops/levers.py
ftype: spec-fidelity
origin_plan: bp-046 (sweep-levers, Item 12)
route: orchestrator
---

# bp-046's write_scope omits a retrofit surface: registering a `[dream_rnd]` lever reddens a bp-047 manifest test

## What
Item 12 registers `dream_rnd_sigma` (section `dream_rnd`) in `ops/levers._LEVERS`, growing the
registry 4→5. This is correct and matches the plan. But a bp-047 test — NOT in bp-046's write_scope
— hardcodes an assumption the widening breaks:

`tests/unit/test_tuning_manifest.py::test_shipped_manifest_loads_and_covers_every_lever` iterates
`for name in LEVERS` and asserts, for EVERY lever:
- `pol.subsystem == "dreaming"`  ← fails: the new lever's default subsystem is its section,
  `dream_rnd` (`eval/harness/tuning.py:99`, `subsystem = str(body.get("subsystem", lever.section))`).
- `pol.objective == "f9_composite"` ← would also fail: the shipped `config/tuning.toml` declares no
  `[tuning.dream_rnd_sigma]` block, so the auto-fill (`tuning.py:175-181`) gives `objective=None`.

The manifest MECHANISM behaves exactly as bp-046 §9 predicted ("a new lever simply gains a default-
`propose` policy there, no edit needed") — `load_manifest()` cleanly auto-fills the new lever with
`subsystem=dream_rnd, autonomy=propose, objective=None`. The gap is purely that the bp-047 test
froze a snapshot of the registry (all-`[dreaming]`, all-`f9_composite`) as if it were an invariant.

## Impact
- Green-gate leg 5 (full non-live suite) has exactly ONE failure: this test. Legs 1–4 pass; the two
  in-scope retrofit test files (`test_levers.py`, `test_shadow_runner.py`) are green including the
  new falsifier-killer assertions. Suite otherwise green (1263 passed, 1 failed, 10 skipped).
- bp-046's Item-12 code + its own tests are complete and correct; this is strictly a write_scope
  omission (the plan should have carried `tests/unit/test_tuning_manifest.py` as a retrofit surface,
  the same way it carried the other two).

## Why the builder can't resolve it in-scope
The fix lives in files outside bp-046's four-file write_scope
(`tests/unit/test_tuning_manifest.py`, and possibly `config/tuning.toml`). scope-guard denies both;
per CLAUDE.md a denial is filed as a finding, never routed around.

## Recommended resolution (minimal, registry-faithful)
Make the over-strict assertion faithful to the registry rather than a frozen snapshot. In
`test_shipped_manifest_loads_and_covers_every_lever`, replace the two hardcoded per-lever assertions
with registry-derived ones, e.g.:
- `assert pol.subsystem == LEVERS[name].section` (this is exactly what `test_missing_file_...`
  already asserts, line 47 — so the shipped-manifest test should agree), and
- gate the `objective == "f9_composite"` assertion to only the levers the shipped `tuning.toml`
  explicitly declares (the four `[dreaming]` ones), OR relax it to
  `pol.objective in {"f9_composite", None}`.

This keeps the test meaningful (it still proves the shipped manifest loads and covers the whole
registry) without freezing the registry's section/objective composition.

## Open sub-question for the orchestrator/owner (parked, does NOT block the recommended test fix)
Should `config/tuning.toml` gain an explicit `[tuning.dream_rnd_sigma]` block, and if so with what
`subsystem`/`objective`? bp-046 §9 says NO (default policy, no edit). The default `subsystem=dream_rnd`
is semantically correct and keeps the two σ knobs distinct (the `[dreaming]` live-path σ vs the
`[dream_rnd]` shadow-lane σ — see finding-0087's fork and the new lever's description). The
`objective` the first σ-sweep optimizes is a bp-049 concern (the sweep spec supplies it); leaving it
`None` here is consistent with the plan. Recorded so the resolver chooses deliberately rather than by
the test's stale default.

## Routing
`spec-fidelity`, route → orchestrator. The orchestrator either widens a follow-up's scope to correct
the bp-047 test (recommended above) or authorizes the edit during bp-046 merge scrutiny. bp-046's
own item is complete; this finding parks only the "full non-live suite green" acceptance criterion,
with re-entry condition: the manifest test is made registry-faithful.
