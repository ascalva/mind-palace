# Journal — bp-046 `sweep-levers` (E3a-1a: the σ-fork resolution)

Alive at graduation (2026-07-16). Status `proposed` — awaits owner `proposed → ready` blessing.

## Fresh-agent orientation
This plan is the fork-resolution half of E3a-1, warranted by finding-0087 (owner resolved the σ-lever
fork 2026-07-16: register the `[dream_rnd]` knobs as levers). Read `plan.md` in full, then the §2 context
manifest IN ORDER. The one item (12) does two coupled things that MUST land together:
1. register `dream_rnd_sigma` in `ops/levers._LEVERS` (the knob the shadow runner actually reads for the
   dream_v2 mirror graph — `shadow.py:139-146` reads `dream_rnd.sigma`, NOT `dreaming.similarity_threshold`);
2. widen `core/dreaming/shadow.py:_config_fingerprint` to hash the live value of every REGISTERED lever
   (derive the set from `ops.levers.LEVERS`, key `"<section>.<key>"`) so a σ-sweep gives distinct cell keys.

The whole point: today a σ-sweep would (a) not move dream_v2 (it reads an unregistered knob) and (b)
collide every eval-store cell on one `config_fingerprint` (`store.py:100-104` `put` skips present keys).
Item 12 kills both. The named falsifier is the collision test — two Configs differing only in
`dream_rnd.sigma` must yield DIFFERENT fingerprints.

## Retrofit awareness
`tests/unit/test_levers.py` (registry contents) and `tests/unit/test_shadow_runner.py:88-91` (the
`config_fingerprint` assertions) are in `write_scope` because this plan widens the surfaces they pin. The
`len(fingerprints) == 1` assertion still HOLDS (both pipelines share one cfg → one fingerprint per run);
only its comment rationale updates.

## Open at graduation
- Bound `[0.55, 0.75]` for `dream_rnd_sigma` is the reviewable choice (matches the dreaming σ + bp-040) —
  owner blesses at proposed→ready.
- Registering ONLY σ (not the broader `[dream_rnd]` knobs) is deliberate (§11) — minimal reviewable diff.

## Checkpoints

### 2026-07-16 — Item 12 built; 4/5 green-gate legs pass; leg 5 parked on finding-0088

**What landed (all four write_scope files):**
1. `ops/levers.py` — registered `dream_rnd_sigma` (section `dream_rnd`, key `sigma`, FLOAT,
   `[0.55, 0.75]`) after `dream_max_clusters`. Registry now 4→5. Description names the lane
   distinction (shadow dream_v2 reads `dream_rnd.sigma`; distinct from `dream_similarity_threshold`
   which drives the live Phase-7 path).
2. `core/dreaming/shadow.py` — `_config_fingerprint` now takes the whole `Config` and hashes the
   live value of EVERY registered lever, DERIVED FROM `ops.levers.LEVERS` (the load-bearing line:
   `{f"{lever.section}.{lever.key}": getattr(getattr(config, lever.section), lever.key) for lever in
   LEVERS.values()}`), keyed `"<section>.<key>"`. NOT a hardcoded list — so bp-049 widening the
   registry moves this key with no second edit here (the plan's critical falsifier guard). Call site
   `:136` now passes `cfg` (was `cfg.dreaming`). Docstring rewritten. Removed the now-unused
   `DreamingConfig` from the TYPE_CHECKING import. `getattr` fails loud (AttributeError) if a lever's
   section/key doesn't resolve — no silent skip (stop-and-raise #1 path; did not trigger, all levers
   resolve, guaranteed by the pre-existing `test_every_lever_points_at_a_real_numeric_config_knob`).
3. `tests/unit/test_levers.py` — +2 tests: `test_registry_has_five_levers_including_dream_rnd_sigma`
   (count 5, section/key/kind/bounds, distinctness from the dreaming σ) and
   `test_dream_rnd_sigma_bounds_are_fail_closed` (`.validate(0.80)` raises, `.validate(0.62)==0.62`).
4. `tests/unit/test_shadow_runner.py` — updated the stale `len(fingerprints)==1` rationale comment
   (still HOLDS; only its basis widened), and +1 test
   `test_config_fingerprint_moves_with_registered_sigma_only`: two Configs differing only in
   `dream_rnd.sigma` (0.60 vs 0.62) → DIFFERENT fingerprints; two differing only in the UNREGISTERED
   `dream_rnd.min_degree` (2 vs 3) → SAME fingerprint. The two falsifier-killers, both green.

**Import safety verified:** `shadow.py` importing `ops.levers` is safe — the import firewall
(`tests/integrity/test_import_firewall.py`) forbids only zone (edge/cloud) + network imports, and
`test_shadow_isolation.py` forbids only `core.stores.derived`. `ops.levers` is a pure data module
(no core/network deps, no cycle). Used a local import inside `_config_fingerprint`.

**Green gate (each leg run separately):**
- Leg 1 `ruff check .` → PASS (fixed two E501 in the new test comments).
- Leg 2 `mypy core agents eval ops scheduler scripts` → PASS, 0 errors (199 files).
- Leg 3 argless `mypy` → 69 errors (baseline HELD exactly).
- Leg 4 `ops.type_gate` → PASS (tier-2 membership OK, bare-ignore scan OK).
- Leg 5 `pytest -q -m 'not live'` → 1263 passed, **1 FAILED**, 10 skipped, 9 deselected. The single
  failure is OUT OF SCOPE and documented in **finding-0088** (spec-fidelity):
  `tests/unit/test_tuning_manifest.py::test_shipped_manifest_loads_and_covers_every_lever` hardcodes
  `pol.subsystem == "dreaming"` (and `objective == "f9_composite"`) for EVERY lever — an assumption
  the correct `[dream_rnd]`-section lever breaks. That test is a bp-047 file, not in bp-046's
  write_scope; scope-guard denies the fix. The manifest MECHANISM works exactly as plan §9 predicted
  (auto-fills the new lever with `subsystem=dream_rnd, propose, objective=None`). The two in-scope
  retrofit test files are fully green (16 passed together).

**PARKED criterion:** "full non-live suite green" (leg 5). Re-entry condition: the manifest test in
`tests/unit/test_tuning_manifest.py` is made registry-faithful (assert `pol.subsystem ==
LEVERS[name].section`; gate/relax the objective assertion) — see finding-0088 for the minimal diff.
The orchestrator resolves this (widen a follow-up's scope, or edit during merge scrutiny).

**Stored-data note (plan §7):** this changes the VALUE of `config_fingerprint` written into eval-store
rows going forward — a keyed identity shift, not a migration. Pre-bp-046 rows keep their narrow key;
post-bp-046 runs get the wider key. Expected — exactly why the σ-sweep is a fresh keyed series.

**Blessings:** none performed (no `proposed→ready` / `draft→ratified`). finding-0088 is `open`,
routed to orchestrator.
