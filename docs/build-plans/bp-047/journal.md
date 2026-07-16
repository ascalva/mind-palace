# Journal — bp-047 `tuning-manifest`: the manifest + `scripts/tune.py` (E3a-2, the human control surface)

> The fresh-agent contract: a new session with only `plan.md` + this journal + the write-scope files
> must continue without re-asking. Checkpoint at every semantic boundary. Status flips are the
> orchestrator's, by hand.

## 2026-07-16 — GRADUATED (proposed), awaiting owner `proposed→ready` blessing

- Graduated by the orchestrator (opus, self-driven) from ratified `dn-evaluation-harness` §3 **E3a**,
  the **manifest half** only. E3a is the note's predicted 2-plan split: E3a-1 the sweep engine
  (bp-046, **RESERVED — parked on the σ-lever design fork**, see below), E3a-2 this plan.
- **Why this half graduated independently:** the manifest + CLI is a policy/schema layer over the
  BUILT lever registry (`ops/levers.LEVERS`) and the BUILT §14 loop (`ops/selfmod.SelfModLoop`) — it
  decides no lever's existence and calls no sweep. So it is independent of both E3a-1 and the σ-lever
  fork that parks E3a-1.
- **The σ-lever fork (why E3a-1/bp-046 is parked, not graduated):** grounding found the note's sweep
  example (`levers = { dream_similarity_threshold = "full" }`, §2.6/§2.9) cannot produce a meaningful
  curve against the BUILT `ShadowRunner`: the 4 registered levers all live in `[dreaming]`, but the
  runner computes from `[dream_rnd]` (`shadow.py:139,146,164`) and only *fingerprints* `[dreaming]`
  (`shadow.py:94-105`, which bp-043's own docstring flags as a placeholder "until E3 widens this").
  So varying any current lever changes the eval key but NOT the output → flat curves by construction.
  oq-0024's σ is `dreaming.similarity_threshold`=0.62 (a lever), but the runner's real knob is
  `dream_rnd.sigma` (unregistered). Resolving this (register `dream_rnd` knobs as levers? fix the
  runner to read `[dreaming]`? widen the sweep grammar?) is an owner design decision on the deliberate
  self-mod boundary → routed to the owner (finding + oq-0024). E3a-1 graduates once the fork is picked.
  **FORK RESOLVED 2026-07-16:** owner chose **register the `[dream_rnd]` knobs as levers** (finding-0087
  option 1). E3a-1 (bp-046) graduates against this next session (banked in the resume brief).
- **Grounding banked (all `path:line` in §3/§6 of the plan):** the registry is exactly 4 `[dreaming]`
  levers (`ops/levers.py:75-112`); `SelfModLoop.execute` writes the overlay + records prior for exact
  rollback + `refresh_config` (`ops/selfmod.py:129-140`); `--revert` is the rollback path but ONLY for
  an EXECUTED proposal (terminal states have no successor, `ops/ledger.py:50-55`); live values read via
  `_section_value` (`ops/selfmod.py:78-79`); `set` requires `[selfmod] enabled` but `show`/`history` are
  read-only. The `auto` mode + `apply_unattended` are E3b, out of scope.
- **Scope discipline:** greenfield except the manifest — §3/§4/§8 carry real N/A-or-cross-ref judgments
  (§4 is cross-reference-only; §8 N/A). All `ops/*` files are read-only dependencies, NOT in write_scope.
  The retrofit-pre-widen rule does not bite (no existing surface moved).
- **Next:** owner blesses `proposed→ready`; then delegate as a supervised builder (disjoint write_scope
  from bp-048/E6 → real parallel fan-out). Pre-flight budget gate first (est opus/200k).

## 2026-07-16 — BUILD (delegated builder, opus). Item 15 CLOSED; Item 16 in progress.

### Env note
Worktree needed `uv sync --all-extras` (dev deps absent at start). Argless `mypy` baseline = **69
errors** (confirmed pre-work).

### Item 15 — DONE
- `eval/harness/tuning.py`: `LeverPolicy`, `TuningManifest`, `load_manifest`, `resolved_fingerprint`.
  POLICY-ONLY (no value field; `range`/`kind` derived from `Lever` — single source of truth).
  - Unregistered manifest key → `UnregisteredLever` (fail-closed; a fixed point has no lever ctor).
  - `autonomy='auto'` → `AutoModeNotSupported` (E3b). Unknown keys (incl. auto-mode fields) →
    `ValueError`. Unknown autonomy value → `ValueError`.
  - Fingerprint = sha256 of sorted-key, whitespace-free JSON of `resolved()` over the WHOLE registry
    (order-insensitive; moves on any policy value OR registry bound change). Parked-decision form
    (sorted-key JSON of resolved policy, sha256) honored.
  - `resolved()` = per-lever {subsystem, autonomy, objective, kind, range:[lo,hi]} — POLICY +
    structure, never a live value → cannot shadow local.toml.
- `config/tuning.toml`: 4 levers, subsystem=dreaming, autonomy=propose, objective=f9_composite.
- `tests/unit/test_tuning_manifest.py`: 13 tests green.
- Legs green for Item 15: `pytest tests/unit/test_tuning_manifest.py` = 13 passed; ruff clean;
  `mypy core agents eval ops scheduler scripts` = Success.

### Item 16 — PLAN (in progress) — `scripts/tune.py`: show / set / history / --revert
- `show`: read-only (NO loop) — each lever's live value via `ops.selfmod._section_value(cfg, lever)`
  (Q3 pin) + bounds + manifest policy. Works with `[selfmod] enabled=false` (Q5).
- `set <lever> <value> [rationale]`: `loop.propose(...)` ONLY — prints proposal id + "awaits owner
  approval"; NEVER approves/executes (falsifier: self-approval / overlay-before-approval). Bounds
  fail-closed via `ProposedChange.resolve` before any ledger write.
- `history`: `ledger.all()` rendered by status (reuses the `_fmt` idiom).
- `--revert <id>`: EXECUTED → `overlay_restore(lever, prior_overlay, overlay_path)` +
  `ledger.mark_rolled_back(id, reason=...)` + `refresh_config()` (reuses built primitives;
  EXECUTED→ROLLED_BACK is a legal transition). VALIDATED/terminal → REFUSE (falsifier: mutating a
  VALIDATED status) and print the inverse `set` command to run. Requires `[selfmod] enabled`.
- **Design decision recorded (codebase, self-resolved):** no `loop.revert()` exists and
  `ops/selfmod.py` is read-only, so `--revert` orchestrates the SAME rollback primitives the loop's
  `validate` uses on gate-deny. Not reimplementing the gate (gate = the admit predicate); it is a
  deliberate, unconditional reversal. Q2 explicitly maps `--revert` → `overlay_restore`.

### Findings filed: none. §10 stop-and-raise: none — policy/value separation holds cleanly.
