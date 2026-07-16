# bp-054 journal — `Res[T]`/`res_under` + `sigma_persistence.*`/`structural_axes.*` registry rows

Builder: delegated (worktree `agent-a892dee83fb5be5ad`, branch `worktree-agent-a892dee83fb5be5ad`).
Plan: `docs/build-plans/bp-054/plan.md` (FB-2). Design refs (RATIFIED, cited never edited):
`dn-resolution-result-typing` §2.2 Rule SCALE; `dn-sigma-fibers` §2.4.4.

## Environment note (session start)
The worktree was branched from **4b3ace7** (pre-bp-050-merge) — `eval/harness/fibers.py` was
absent, which the plan depends on (name agreement, the "69" mypy count, the full suite). My
branch had **zero unique commits**, so I fast-forwarded `worktree-agent-a892dee83fb5be5ad` to
current `main` (**97239b8**) with `git merge --ff-only main`. This brought in bp-050 (fibers),
bp-051, bp-052 as legitimately-merged main state. No merge-to-main; only my feature branch moved.
fibers.py now present; scope.py/registry.py/shadow.py/temporal.py identical to the notes I read.

## Sourced metric names (the finding-0086 falsifier — grounded, not restrung)
- **sigma_persistence.\*** — `eval/harness/fibers.py:75-79` exports importable NAME CONSTANTS:
  `METRIC_MEAN="sigma_persistence.mean"`, `METRIC_P50="sigma_persistence.p50"`,
  `METRIC_MAX="sigma_persistence.max"`, `METRIC_FRAC_GE_STRONG="sigma_persistence.frac_ge_strong"`,
  `METRIC_N_CLAIMS="sigma_persistence.n_claims"`. type_tag `"Res(sigma)"` (fibers `_TYPE_TAG`).
- **structural_axes.\*** — `core/dreaming/shadow.py:232-243` writes `structural_axes.{axis}` where
  `axis` iterates `structural.items()`; `structural = SnapshotStore.latest_structural()`
  (`core/complex/temporal.py:188-197`) → returns exactly `{"frustration", "min_conductance"}`
  (mirrors `StructuralSnapshot.structural_axes()` at `temporal.py:82-86`). So the two written names
  are **`structural_axes.frustration`** and **`structural_axes.min_conductance`** — matching
  finding-0086's cited examples. type_tag `"Inv"`, guardrail_eligible False (they feed drift's A2
  axes; they are not themselves a guardrail).

## Plan
1. core/scope.py — add `ResParam` + `Res[T]` + `res_under` + `res_comparable` at the bottom,
   mirroring Inv/Rate/rate_under (:586-619). Additive only; nothing above line 619 changes.
2. eval/harness/registry.py — register the 5 sigma_persistence.* rows (Res(sigma)) + the 2
   structural_axes.* rows (Inv, guardrail_eligible=False). Import fibers' name constants for
   agreement — pending a circular-import check (registry→fibers→shadow→registry).
3. tests/unit/test_scope_res.py + test_registry_res.py.

## Item 1 — Res[T] + res_under + res_comparable (core/scope.py) — DONE
Added `ResParam` (frozen: name/lo/hi/grid) + `Res[T]` (frozen, `value` + REQUIRED `param`) +
`res_under[T]` (checked constructor, `param` keyword-only) + `res_comparable` (π-identical only)
at the BOTTOM of core/scope.py (after `rate_under`, :619), mirroring the Inv/Rate pattern exactly.
Added `Any` to the `typing` import (the only change above the block; pure additive). PEP-695 generics
used (`class Res[T]`, `def res_under[T]`). π is required structurally — a π-less `Res` is a TypeError,
exactly as a clockless `Rate` is.
- **Additive guarantee (the cardinal falsifier): HELD.** `git diff core/scope.py` = exactly two
  hunks: the import line (+`Any`) and the appended block (all `+`, nothing above touched).
  `tests/unit/test_scope.py` passes **UNCHANGED (28 passed)**. Bit-identical Inv/Rate/meet/join.
- `tests/unit/test_scope_res.py` — 7 tests green (π-less TypeError; frozen/hashable; round-trip;
  comparable iff π identical; refused across distinct range/grid/name).

## Item 2 — registry rows (eval/harness/registry.py) — DONE
Registered 5 `sigma_persistence.*` rows (type_tag `"Res(sigma)"`, source `row15-sigma-fibers`,
comparability = plan §6 pin, regression, guardrail_eligible=False) + 2 `structural_axes.*` rows
(`structural_axes.frustration`, `structural_axes.min_conductance`; type_tag `"Inv"`, source
`row6-structural-axes`, comparability "same fixture / same pipeline; A2 axes over the scratch
snapshot", regression, guardrail_eligible=False). Widened the `type_tag` field comment to include
`"Res(<param>)"` (plan §4; a comment inside write_scope). No existing row moved.
- `tests/unit/test_registry_res.py` — 5 tests green.

### finding-0093 filed (spec-fidelity, builder-resolved) — the circular-import blocker
The plan pins "import FB-1's constants into registry, don't restring". Doing so closes
`registry → fibers → shadow → registry` (both back edges in read-only bp-050 files) — DEMONSTRATED to
raise a partially-initialized-module ImportError whenever fibers/shadow is the import entry point (a
hard boot failure of the eval harness). Bottom-placing the import fixes only registry-first order.
RESOLVED: exact literal names in registry (eager, cycle-free) + **machine-checked agreement** in
test_registry_res.py, which IMPORTS the FB-1 `METRIC_*` constants and calls fail-closed
`registry.get(...)` on each — any name drift fails CI. Foreclosed the finding-0086 class by test, not
by an unsafe import. `docs/findings/finding-0093.md`.

### finding-0086 RESOLUTION RECORD (orchestrator flips → resolved at merge)
The `structural_axes.*` readings shadow.py writes (`structural_axes.frustration`,
`structural_axes.min_conductance` — the two `latest_structural()` / `StructuralSnapshot.
structural_axes()` keys) are now REGISTERED here as `type_tag="Inv"`, `guardrail_eligible=False`,
`source_instrument="row6-structural-axes"` — exactly the durable fix owed in finding-0086's own
resolution note (source_instrument = catalog row 6 / core/complex/temporal.py). A report that
fail-closed-resolves every metric via `registry.get(...)` now resolves them. **I do NOT flip the
finding — the orchestrator flips finding-0086 → resolved at merge (this note is the resolution
record).**

## Environment caveat for a fresh agent
The venv needs the `dev` extra: `uv sync --extra dev` (pytest/ruff/mypy live there). The worktree was
fast-forwarded to main (97239b8) at start — see the top note.

## GREEN GATE — all 5 legs pass (run separately, never &&-chained)
1. `uv run ruff check .` → All checks passed!
2. `uv run mypy core agents eval ops scheduler scripts` → Success: no issues found in 205 source files
3. `uv run mypy` (argless, exits 1 by design) → **Found 69 errors in 20 files** (== target 69; my
   test files add ZERO type errors)
4. `uv run python -m ops.type_gate` → Tier-2 membership OK; bare-ignore scan OK
5. `uv run pytest -q -m 'not live'` → **1348 passed, 10 skipped, 9 deselected**
Plus the additive proof: `uv run pytest tests/unit/test_scope.py -q` → 28 passed (UNCHANGED).

## Status: COMPLETE — ready for orchestrator review + merge
Commit on branch `worktree-agent-a892dee83fb5be5ad`. Orchestrator: flip finding-0086 → resolved;
finding-0093 is builder-resolved (annotated). No blessing performed; ratified notes untouched
(dn-capability-scope §2.3 stamp is the owner's, not this builder's).
