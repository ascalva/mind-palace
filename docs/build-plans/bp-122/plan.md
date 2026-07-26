---
type: build-plan
id: bp-122
track: ops
status: ready
design_ref: []
contract: builder
write_scope:
  - tests/integration/test_selfmod.py
  - tests/integration/test_selfmod_cli.py
session_budget: 1
cost:
  estimate:
    model: sonnet
    tokens: 30k
  actual: null
depends_on: []
parallelizable_with: [bp-123]
created: 2026-07-26
updated: 2026-07-26
links:
  - docs/findings/finding-0214.md
  - docs/findings/finding-0212.md
re_entry: null
supersedes: null
superseded_by: null
warrant: docs/findings/finding-0214.md
---

# Build Plan — make the two self-mod tests hermetic, so the deploy gate stops lying

## 0. Mode & provenance

Investigation complete and recorded in `finding-0214` (filed and escalated to `blocker` this
session, `e79f337` + `532921f`). The defect was found incidentally while running bp-121's pre-push
gate and its cause is measured, not inferred. Authority to act is the owner's instruction
2026-07-26 (*"I give you permission to exercise the quick fix to address the tests"*); the
readiness blessing (`proposed → ready`) remains the owner's, by hand.

## 1. Objective

Make `tests/integration/test_selfmod.py` and `tests/integration/test_selfmod_cli.py` assert against
a σ they pin themselves rather than whatever the machine's config overlay currently holds, so the
deploy gate is green on the owner's machine and red only for real regressions.

## 2. Context manifest

Read in this order, whole files before citing:

1. `docs/findings/finding-0214.md` — the diagnosis and the deploy consequence; do not re-derive.
2. `tests/integration/test_selfmod.py` — `_cfg` (`:35-42`), `_loop` (`:45-51`), `_change`
   (`:54`), and the failing assertion at `:76`. Note `_cfg` already does the exact
   `dataclasses.replace` move this fix needs, one field over.
3. `tests/integration/test_selfmod_cli.py` — `_loop` (`:25-33`) and the failing assertion at
   `:38`. Same shape, less structure: the config is built inline rather than via a `_cfg` helper.
4. `core/kernel/config/loader.py:117-121` — `DreamingConfig`, a frozen dataclass with
   `similarity_threshold: float`. This is what gets `replace`d.
5. `config/local.toml` — READ ONLY, and read it to understand why 0.58 is there
   (owner ruling oq-0024). It is the owner's tuning and this plan does not touch it.
6. `ops/lifecycle/launcher.py:586-597` — `gate_cmd`, so it is concrete that this plan's acceptance
   *is* the deploy gate's fifth condition and not merely a tidier test file.

## 3. Investigation & grounding

- **Q1 — what exactly fails?** Two assertions, one cause:
  `test_selfmod.py:76` (`p.current_value == 0.62` → got `0.58`) and `test_selfmod_cli.py:38`
  (`"0.62 -> 0.66" in out` → got `"0.58 -> 0.66"`).
- **Q2 — why does the value reach the test at all?** Both fixtures call `get_config()`, the merged
  chain (`defaults.toml` → `levers.toml` → `local.toml`). `local.toml:47` sets
  `[dreaming] similarity_threshold = 0.58`. `SelfModLoop.propose` reads the lever's *current* value
  from that config, so `current_value` is the machine's σ, not the repo's.
- **Q3 — is it bp-121's?** No, and this was settled by experiment: bp-121's diff was stashed, both
  failures reproduced identically, then popped and re-confirmed. The remote runner is green on both
  tests in the same run that failed on bp-121's three.
- **Q4 — how wide is the blast radius?** ⚑ **59 test files call `get_config()`/`load_config()`**,
  so the *pattern* is everywhere. But only these two fail, because only these two compare a live
  config value against a hard-coded literal. Two neighbours that look like they should fail and do
  not, and are therefore **out of scope and must be left alone**:
  `tests/integration/test_levers_overlay.py:41` (asserts σ == 0.62 as "the shipped default" — it
  builds its own config dir) and `tests/integration/test_tune_cli.py:155` (deliberately reads the
  live chain to prove `show` does not parse TOML directly — reading live is that test's *point*).
- **Q5 — is pinning the fixture the right fix, or should the assertion read the config?** Pin the
  fixture. Making the assertion read `cfg.dreaming.similarity_threshold` would make it tautological
  — it would pass for every value including a broken one, which is a false green, and this repo has
  two open findings about exactly that failure mode (0212, 0213).

**Risk surfaced during reading:** the obvious minimal edit — change `0.62` to `0.58` — is the
*wrong* fix and would be an easy one to make under time pressure. It re-breaks the moment the owner
retunes σ again (which oq-0024 explicitly says will happen: the σ-sweep harness replaces this
guess), and it breaks CI, where there is no overlay and σ is 0.62. §7's falsifier is written
specifically to kill that fix.

## 4. Reconciliation

- `tests/integration/test_selfmod.py:35-42` — `_cfg`'s docstring-free `dataclasses.replace` on
  `selfmod` → **[cross-ref: extension]**: extend the same call to pin `dreaming`, and add a short
  comment naming finding-0214 so the next reader knows the pin is load-bearing rather than
  decorative. Do not restructure the helper.
- `tests/integration/test_selfmod_cli.py:25-33` — `_loop` builds config inline in two statements
  → **[banner: correction]**: it needs the same pin. Prefer keeping it inline (matching this file's
  existing style) over importing the sibling file's `_cfg` — cross-importing between test modules
  would couple two suites that are deliberately independent.

## 5. Write scope

Two test files, and only their config fixtures plus the two assertions that read σ. Nothing else in
either file is touched — in particular the rollback, boiling-frog, master-switch and unattended
tests in `test_selfmod.py` are out of bounds, as is every `cmd_*` assertion in the CLI file beyond
the σ render.

Deliberately **out of scope**: `config/local.toml` (the owner's tuning — the whole point is that a
test must not care what it says); `config/defaults.toml`; `core/kernel/config/loader.py` (bp-123's
territory); `tests/integration/test_levers_overlay.py` and `test_tune_cli.py` (Q4 — they pass, and
one of them reads live *on purpose*); the other 57 `get_config()` callers; `ops/lifecycle/launcher.py`
(adding a deselect to `gate_cmd` would hide this, exactly as a CI deselect would have hidden
finding-0211); the foundation denylist.

## 6. Interfaces pinned inline

Current, `tests/integration/test_selfmod.py`:

```python
def _cfg(*, enabled=True, unattended=False):
    cfg = get_config()
    return dataclasses.replace(
        cfg,
        selfmod=dataclasses.replace(
            cfg.selfmod, enabled=enabled, unattended_enabled=unattended
        ),
    )
```

`DreamingConfig` is a frozen dataclass (`core/kernel/config/loader.py:117-121`), so the pin is the
same idiom already in use:

```python
_SIGMA = 0.62        # ⚑ the pinned σ these tests assert against — see the falsifier

    return dataclasses.replace(
        cfg,
        selfmod=dataclasses.replace(...),
        dreaming=dataclasses.replace(cfg.dreaming, similarity_threshold=_SIGMA),
    )
```

⚑ **`_SIGMA` must be used in BOTH the fixture and the assertions** — a module constant is the
point, not a style preference. A literal `0.62` left in the assertion while the fixture pins
`_SIGMA` re-creates the same two-places-one-fact defect one layer in, and the next σ retune
resurrects this bug. The same applies independently in the CLI file, whose assertion is a formatted
string (`f"{_SIGMA} -> 0.66"` or equivalent) rather than a float comparison.

## 7. Items

### Item 1 — pin σ in both fixtures and assert against the pin

- **Objective:** both files construct their `SelfModLoop` over a config whose
  `dreaming.similarity_threshold` is a value the test chose, and both assertions reference that same
  value by name.
- **Files:** `tests/integration/test_selfmod.py`, `tests/integration/test_selfmod_cli.py`
- **Acceptance test:** `uv run pytest tests/integration/test_selfmod.py
  tests/integration/test_selfmod_cli.py -q` → green **with `config/local.toml` still holding
  `similarity_threshold = 0.58`**. ⚑ Green with the overlay absent proves nothing; the overlay's
  presence is the test condition. Then the real acceptance: the deploy gate command itself —
  `uv run pytest -q -m 'not live and not podman and not needs_vault and not needs_restic'
  --deselect 'tests/unit/test_core_self_containment.py::test_core_imports_nothing_outside_core'`
  → **0 failed**.
- **Falsifier:** temporarily set `[dreaming] similarity_threshold` in `config/local.toml` to a
  **third** value (e.g. `0.60`), re-run both files, and they must still be green — then restore
  0.58 exactly. A fix that special-cases 0.58, or that changes the literal `0.62` to `0.58`, fails
  this and must be rejected. ⚑ Restoring the owner's file byte-for-byte is part of the item, not an
  afterthought: it holds his oq-0024 ruling and its rationale.
- **Invariant(s) it must not violate:** the assertions must stay *substantive* — comparing
  `current_value` to `cfg.dreaming.similarity_threshold` would pass for any value and is a false
  green (Q5). The remaining tests in both files keep passing unchanged. No test is deselected,
  skipped, or `xfail`ed.
- **Touches stored data?** No.
- **Parallelizable?** No (single item).  **Depends on:** none.

## 8. Math carried explicitly

N/A — no mathematical object implemented. σ appears only as an opaque config value; the plan
changes where the test *gets* it, never what it means.

## 9. Non-goals

- **Not** editing `config/local.toml` beyond the falsifier's temporary flip-and-restore. The σ value
  is the owner's ruling (oq-0024) and reverting it to make a test pass would be fixing the wrong
  side of the seam.
- **Not** renaming `local.toml` → `ouroboros.toml` — that is **bp-123**, and it must not ride a
  blocker fix (the standing rule: a mechanical move and a behaviour change go in separate plans).
- **Not** auditing the other 57 `get_config()` callers. If a sweep is warranted it is its own plan;
  this one clears a live deploy gate.
- **Not** adding a `--deselect` to `gate_cmd`, nor reaching for `deploy --skip-tests`. Both restore
  a green board while leaving the gate unable to tell a real regression from a config overlay —
  and `--skip-tests` additionally drops the ci-witness, so it would discard bp-121's whole result.
- **Not** fixing finding-0212 (the seal-attests-the-local-gate duty). Orchestrator-routed, no code.

## 10. Stop-and-raise conditions

- The deploy gate is still red after Item 1 with something *other* than these two tests → **stop**
  and file a finding with the failing node. It means the local gate has a third divergence from CI
  that nobody has recorded, which is a bigger fact than this plan.
- The falsifier's third-value run goes red → the fix is not hermetic. **Stop**; do not paper over it
  by choosing a value that happens to work.
- `config/local.toml` cannot be restored byte-for-byte after the falsifier → **stop immediately**
  and say so. That file holds an owner ruling and is not in version control; a lost overlay is
  unrecoverable from the repo.
- Any temptation to widen `write_scope` (especially into `loader.py` or `gate_cmd`) → file a finding.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| Whether the other 57 live-config-reading tests need the same treatment | Leave them; only these two compare live config to a literal, and two neighbours read live *deliberately* | Sweep all 59 now (unbounded, and would touch tests whose live read is the point) | A third such false red appears, or a `get_config()`-in-tests lint is proposed |
| Whether a hook/lint should forbid asserting a literal against live config | No — not proposed here | Add one now (a rule this repo has one data point for; premature) | A second instance, which would make it a pattern |
| σ's pinned value in the fixtures | `0.62`, matching `defaults.toml` and both current assertions | A neutral value like `0.60` (gratuitous churn in the assertions, and 0.62 is what the tests were written against) | `defaults.toml`'s σ changes — then the pin is a deliberate, visible edit rather than a silent read |

## 12. Dependency & ordering summary

One item, one sitting. Depends on nothing; `parallelizable_with: [bp-123]` because their write
scopes are disjoint (tests vs loader/config). Blast radius is minimal and test-only — no production
code, no stored data, no external effects. What it unblocks is the **fifth deploy gate**, which is
the last thing standing between the owner and the code-ingest deploy once the daemon is up.
