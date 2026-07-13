# bp-019 journal

## 2026-07-12 — scrutiny addendum: the §6(f) warning path (orchestrator catch)

**Honest record: this was an orchestrator-scrutiny catch, not something this session found
itself.** Plan §6(f) pins "An unparseable non-null block ⇒ no observation + a WARNING in
the report — deterministic skip." I built `SelfSyncReport.warnings` but nothing ever
appended to it: `parse_cost_value` collapses null and unparseable-non-null to the same
`None`, so `_observations_for` could not tell them apart, and no test covered the path.
The pre-addendum suite was green while a pinned behavior was silently missing — the gap
only mattered at the report level (no stored row was ever wrong), which is exactly why the
tests didn't catch it.

Fix (minimal, inside existing write_scope):
- `parse_plan_cost_block` now records the affected keys under `_unparseable` — the
  distinction is only computable THERE, where the raw text is still in hand (`parsed is
  None and raw_value not in ("", "null")`). Return type simplified to `dict[str, Any]`
  (drops the `_subject_id` type-ignore hack too).
- `_observations_for` warns per skipped (path, key), format:
  `"unparseable non-null cost {key} at {sha[:12]} {path} — skipped, no observation"`.
  Deterministic and stably ordered: paths sorted (already, via `_changed_plan_files`),
  keys in `('estimate', 'actual')` order. Warnings belong to the projection ACT — a
  re-sync of an already-projected sha re-warns nothing (the sha is skipped before parsing).

Tests added (`tests/unit/test_self_sensor.py`, 24 total now):
- `test_unparseable_non_null_value_warns_and_skips` — bare prose (`estimate: measured
  later`) AND a nothing-usable mapping (`actual: { note: "tbd" }`) in one commit: zero
  observations, sha still marked projected, EXACTLY the two expected warning strings in
  order; a fresh sensor over the same repo reproduces the identical list (determinism);
  a re-sync warns nothing.
- `test_null_or_absent_cost_yields_no_observation_and_no_warning` — `null` and absent are
  silent by design (the §6(f) distinction).

Interpreter ratchet: fired red as designed on the source change; **re-pinned at 1.0.0**
(`6a5a7534…`) — a DECLARED REFACTOR, not a worldview bump: the projection map is
byte-identical (unparseable non-null yielded no observation before and after; only
report-side diagnostics were added; batch content hashes untouched). Decision recorded in
the `INTERPRETERS` comment.

Gate legs (per the orchestrator's instruction — full suite deliberately NOT re-run; the
prior 954/8/0 run stands, sibling gate in progress):
- `pytest -q tests/unit/test_self_sensor.py tests/unit/test_agent_observations.py
  tests/unit/test_interpreter_versions.py` → **41 passed**.
- `ruff check .` → All checks passed.
- `mypy core agents eval ops scheduler scripts` → clean, 173 files.
- `mypy` (argless) → tail `Found 69 errors in 20 files (checked 344 source files)` —
  baseline held.

## 2026-07-12 — GATE GREEN, session end (builder → orchestrator handoff)

Full gate swept, all five legs green:
- `uv run ruff check .` → All checks passed.
- `uv run mypy core agents eval ops scheduler scripts` → Success: no issues found in
  173 source files.
- `uv run mypy` (argless) → tail `Found 69 errors in 20 files (checked 344 source files)`
  — the pinned baseline, UNCHANGED by this plan's new tests.
- `uv run python -m ops.type_gate` → Tier-2 membership OK; bare-ignore scan OK.
- `uv run pytest -q` (full suite) → **954 passed, 8 skipped, 0 failed** (479.27s). No
  live-e2e flake re-run needed — clean on the first pass; the 8 skips are pre-existing
  conditional skips (marker-gated, e.g. live/podman axes), not new.

Falsifier evidence (independently re-verified directly against the built modules, beyond
the pytest suite, per the contract):
- **No-provenance-parameter sweep**: 15 public surfaces across
  `core.stores.agent_observations` (module functions + `AgentObservation`/
  `AgentObservationStore` methods) inspected via `inspect.signature` — zero accept
  `provenance`/`provenances_write`/`tier`/`label`. Same check on `AgentSensingHandoff.
  emit_batch`/`collect` — clean.
- **B-b idempotence falsifier**: a real fixture repo (`bp-999`, create+seal in one commit)
  synced twice — first sync landed 2 rows, second sync changed NOTHING (0 new rows, row
  count held at 2). Holds.
- **§2.6 safety-line proof**: `ops/self_sensor.py`'s only external-process calls are
  `subprocess.run(["git", ...])` (AST-verified: every `subprocess.run` call's argv[0] is
  the literal string `"git"`); no `open()`/network-module import anywhere in the file
  (`test_sensor_reads_only_git_and_config_paths`, AST-based, not substring-matched against
  prose). The sensor's only inputs are git subprocess output + config paths — no
  transcript/prompt access anywhere, structurally.

Two findings filed and resolved in-session (both spec-fidelity, builder-resolved per the
routing rule, both flagged for orchestrator awareness):
- **finding-0057**: `core/stores/observation_history.py`'s `IDENTITY_KEYS` dict lacks the
  `"agent"` entry its own comments anticipate — bp-019's write_scope never granted that
  file. Resolved via an in-test monkeypatch registration (exercises the real
  `archive()`/`chain()` code paths); recommend a tiny follow-up one-line grant before
  bp-020's backfill depends on it for real.
- **finding-0058**: plan §6(e)'s pinned `rev-list`/`diff-tree` command text omitted
  `--first-parent` (rev-list) and `--root` (diff-tree), contradicting the plan's own §3
  risk-analysis prose and root-commit requirement — both verified empirically against
  throwaway fixture repos and fixed in `ops/self_sensor.py` with inline documentation.

All four items (5, 6, 7, 8) complete, in commit order: `f6b94ba` (Item 5,
AgentObservationStore), `c0322e1` (Item 6, AgentSensingHandoff), `4ec7b9b` (Item 7,
self_sensor.py), `e48c56e` (Item 8, wiring). Plan status left `in-progress` for the
orchestrator to scrutinize, merge, and seal — not touched further by this session.

Non-goals honored: no consumer reads `ObservedView` here; only the `cost` stream is
projected; the live backfill over real history is untouched (bp-020's, deliberately); no
transcript parsing anywhere; `MIRROR_READABLE`/the mirror/the dreamer untouched (confirmed
by `git diff --stat` since baseline — no file outside write_scope was touched, and
`core/stores/observation_history.py`/`core/mirror.py` were read-only throughout).

Session ends here at this unit boundary (all §7 items closed, gate green) — a fresh
resume, if needed, has everything above plus the plan + write-scope files.

## 2026-07-12 — Item 8 complete: wiring (hook line, driver script, reset entry)

Wrote `scripts/sense_self.py` mirroring `scripts/snapshot_code.py` exactly: prints
`build_self_sensor().sync()`, exits 0.

Appended the hook line to `.githooks/post-commit` per §6(g), BYTE-IDENTICAL to the pinned
text: `$RUN scripts/sense_self.py 2>&1 || echo "self-sensor sync failed (non-blocking; next
sync heals)"`. Also updated the header comment (the §4-licensed reconciliation extension —
"header mentions both sensors") to name both `ops/code_sensor.py` and `ops/self_sensor.py`.
Diff is exactly the header-comment update + one appended invocation line; the branch guard
and code-sensor line are unchanged (confirmed by diff).

Added the ONE `reset_targets()` list entry + comment to `ops/lifecycle/launcher.py` per
§6(h): `p.data_dir / "agent_observations.sqlite"`, citing dn-self-sensing §2.5 (readings
corpus-class; history rides the guarded sidecar). Confirmed `agent_observations.sqlite` is
NOT in `_RESET_GUARD` and `observation_history.sqlite` already is (shared across both
family members, unaffected by this addition). Diff is exactly one list entry + comment.

Item 8 tests added to `tests/unit/test_self_sensor.py` (5 new, 22 total in the file): the
driver script parses clean and mirrors the mold's shape; the hook body with a poisoned
`$RUN` still exits 0 for BOTH sensor lines (non-blocking, tested directly via `sh -c`); the
real `.githooks/post-commit` contains both pinned lines with the branch guard upstream of
both; `reset_targets()` lists `agent_observations.sqlite` and refuses
`observation_history.sqlite` (mirroring `test_code_sensor.py`'s existing equivalent test);
a non-main branch commit's hook-guard exits before reaching either sensor invocation
(verified against a real throwaway repo on a non-main branch).

Gate: `uv run pytest -q tests/unit/test_self_sensor.py` → **22 passed**.
`uv run pytest -q tests/unit/test_code_sensor.py` → **7 passed** (existing reset test
unaffected by the new launcher entry). `ruff check` / `mypy` clean on
`scripts/sense_self.py` and `ops/lifecycle/launcher.py`.

All four items (5-8) of bp-019 are now code-complete. Next: the full gate sweep (ruff repo-
wide, mypy full + argless, `ops.type_gate`, `pytest -q` full suite) before handing back to
the orchestrator.

## 2026-07-12 — Item 7 complete: φ_self v1.0.0 (`ops/self_sensor.py`)

Wrote `ops/self_sensor.py` per §6(d,e,f): `INTERPRETER_VERSION = "1.0.0"`, `SelfSensor`
(repo/store/handoff/attestor/history/branch handles, mirroring `CodeSensor`'s shape),
`SelfSyncReport`, the stdlib-only `cost:` block parser (`parse_plan_cost_block`,
`parse_cost_value`, `normalize_tokens`, `_strip_trailing_comment`,
`_split_top_level_commas`), and `build_self_sensor()`.

**finding-0058 filed and RESOLVED in-session (spec-fidelity):** the plan's §6(e) pinned
command text (`rev-list --reverse <branch> -- .../plan.md`, `diff-tree --first-parent -m
sha`) contradicts its own §3 risk-analysis prose and root-commit requirement. Verified
empirically against throwaway fixture repos: (1) a BARE `rev-list` (no `--first-parent`)
includes branch-side merge-source commits as candidates — exactly the double-candidacy
the design's §3 prose rules out — so `sync()` now runs `rev-list --first-parent --reverse`;
(2) `diff-tree --first-parent -m sha` (no `--root`) emits NOTHING for a root commit, so
`_changed_plan_files()` now adds `--root` (a verified no-op for every non-root commit).
Both are documented inline at the call sites with the empirical verification noted.

Real-fixture-repo test suite (`tests/unit/test_self_sensor.py`, 17 tests): root commit (all
facts new), estimate/actual landing at their own commits, in-place edit as a new-commit
observation, a REAL merge commit (first-parent semantics, `--no-ff`), re-sync adds zero
rows, a zero-fact (no cost-block) commit marked-not-rescanned, token normalization table
(`350k`→350000, `1.2m`→1200000, bare int, unparseable→None), trailing-comment stripping
against the REAL `docs/build-plans/bp-011/plan.md` text (not a synthetic copy), attestation
(`project_agent_observations`, pinned input/output hashes), the named falsifier (second
projection of the same commit changes nothing — row count AND attestation count), and the
statelessness falsifier (AST-walk: the only `subprocess.run` calls have literal `"git"` as
argv[0]; no `open`/network-module import anywhere in the file).

Sanity-checked the parser against ALL 23 real `docs/build-plans/*/plan.md` files (not just
bp-011) — no crashes, sane output on every shape seen in the corpus: `null` fields,
multi-line comment blocks between `estimate:`/`actual:` (bp-013), extra unnamed keys
(`builder_tokens`, `tokens_item8`, `note: "..."` with embedded punctuation), non-numeric
`tokens` values (`unmeasured`, `unknown`).

Added the `phi_self` (version, source-hash) ratchet pair to
`tests/unit/test_interpreter_versions.py` (bp-018's pattern): sha256 over
`ops/self_sensor.py` alone (single source file, unlike φ_code's two-file pin).

Gate: `uv run pytest -q tests/unit/test_self_sensor.py tests/unit/test_agent_observations.py
tests/unit/test_sensing_transport.py tests/unit/test_interpreter_versions.py
tests/unit/test_code_projection.py tests/unit/test_code_sensor.py` → **55 passed**.
`uv run mypy ops/self_sensor.py core/stores/agent_observations.py core/sensing.py` →
clean. `ruff check` clean on all touched files.

Next: Item 8 — `scripts/sense_self.py`, the `.githooks/post-commit` line, the
`reset_targets()` entry, reconciliation banners.

## 2026-07-12 — Item 6 complete: `AgentSensingHandoff` seam sibling

Appended `AgentSensingHandoff`/`AGENT_OBSERVATIONS` to `core/sensing.py` per §6(c),
verbatim-mirroring `CodeSensingHandoff`'s shape (own subdir `agent_observations/`, atomic
emit_batch/collect, consume-and-heal). One import line added at the top (`from
core.stores.agent_observations import AgentObservation` + the `batch_content_hash`
alias) — confirmed against the bp-012 precedent commit (`a1df6da`) that this is the
established shape (import at top + block appended at bottom), not a falsifier violation;
`git diff core/sensing.py` shows ONLY insertions (0 deletions) — the biometric and code
contracts are byte-identical.

Wrote the Item 6 transport tests in `tests/unit/test_sensing_transport.py`: emit→collect
round-trip, consume-by-default + second-collect-empty, uncollected-batch heals on next
collect (a "crash" simulation via a fresh handoff instance), batch-hash determinism across
re-emission order, own-subdirectory isolation (never touches the sibling dirs), and the
named falsifier check (existing `SensingHandoff`/`CodeSensingHandoff` surfaces unchanged,
three classes structurally distinct — Q1 restated).

Gate: `uv run pytest -q tests/unit/test_sensing_transport.py` → **7 passed**. Also rechecked
the full sensing-adjacent suite (`test_code_projection.py`, `test_code_sensor.py`,
`test_reference_extraction.py`, `test_agent_observations.py`,
`test_sensing_transport.py`) → **42 passed**, confirming the append caused no regression.
`ruff check core/sensing.py tests/unit/test_sensing_transport.py` clean.

Next: Item 7, `ops/self_sensor.py` (φ_self v1.0.0) + its fixture-repo test suite +
the interpreter-version ratchet pair.

## 2026-07-12 — Item 5 complete: `AgentObservationStore`

Wrote `core/stores/agent_observations.py` mirroring `code_observations.py` exactly per
§6(a,b): `AgentObservation` (commit_sha, stream, subject_id, key, payload — no provenance
field), `AgentObservationStore.add_batch`/`is_projected`/`mark_projected`/`all_rows`/
`rows_for`/`count`/`chain_for`, module-local `batch_content_hash` sorted on
`(commit_sha, stream, subject_id, key)`, `open_agent_observation_store()` →
`data/agent_observations.sqlite`.

**finding-0057 filed (spec-fidelity, routed to builder/self, resolved in-session):**
`core/stores/observation_history.py`'s `IDENTITY_KEYS` dict lacks an `"agent"` entry (the
file's own comments at `:13,48,62` say bp-019 registers it, but bp-019's write_scope never
granted that file — confirmed DENY via `scope-guard.sh --standalone`). Resolution: did NOT
touch the out-of-scope file; `tests/unit/test_agent_observations.py` registers
`IDENTITY_KEYS["agent"]` via an autouse `monkeypatch` fixture so the supersession/chain
tests exercise the REAL `ObservationHistoryStore.archive()`/`chain()` code paths end-to-end.
Flagged for the orchestrator: a tiny follow-up (or an amendment to this plan's write_scope)
should land the real one-line dict entry in the shipped file before bp-020's backfill
depends on it for real.

Wrote `tests/unit/test_agent_observations.py` (13 tests, mirroring
`test_code_observations.py`'s shape): idempotence, bumped-interpreter archive+chain,
missing-history raise, same-interpreter-readd never touches history, the no-provenance-
parameter sweep (Item 5's named falsifier), observed-minting, ObservedView admits /
MirrorView refuses (§2.6), projection-mark idempotence, batch-hash determinism, open-helper.

Gate: `uv run pytest -q tests/unit/test_agent_observations.py` → **13 passed**. (Needed
`uv sync --extra dev` first — pytest is an optional dev dep, not in the base env by
default in this worktree; a one-time setup step, not a finding.)

Next: Item 6, the `AgentSensingHandoff` sibling appended to `core/sensing.py` + its
transport tests.

## 2026-07-12 — build session start (builder)

Status flipped `ready → in-progress` (mine to do; the two blessing gates —
`draft→ratified`, `proposed→ready` — are owner-only and untouched). Worktree-local
`.claude/state/active-plan` = `bp-019`. Read CLAUDE.md, plan.md in full, checkpoint/
commit/finding skills, and every §2 context-manifest file: `code_observations.py`
(mold, full), `core/sensing.py` (whole file, sibling banner `:285-292`,
`CodeSensingHandoff` `:297-349`), `ops/code_sensor.py` (sensor mold, `_project`
`:212-237`), `observation_history.py` (sidecar, `IDENTITY_KEYS` already has the
bp-019 comment at `:64` — `'agent'` not yet registered, that's mine to add),
`.githooks/post-commit`, `launcher.py:496-529` (`reset_targets()`), build-plan
template + skill, bp-011 plan (cost block fixture). Also read: `core/provenance.py`
(Provenance enum, MIRROR_READABLE), `core/attestation/attestor.py` (`Attestor.emit`
signature matches plan §6(d) verbatim), `scripts/snapshot_code.py` (driver-script
mold), existing test files `test_code_observations.py` / `test_sensing_transport.py`
/ `test_interpreter_versions.py` (the exact test-shape mold). No manifest gaps found
— everything needed was either in §2 or one hop from it (attestor/provenance, which
the mold files already import).

finding IDs start at finding-0057 (0052-0056 reserved for bp-022, parallel/disjoint).

Next: Item 5, `core/stores/agent_observations.py` + its test suite, mirroring
`code_observations.py` exactly per §6(a,b).

## 2026-07-12 — minted at graduation (orchestrator, Fable/xhigh)

Plan created `proposed` by /graduate over the ratified `dn-self-sensing` (B-b: store +
seam sibling + φ_self over the cost stream). Grounding verified in-session: the
sibling-precedent banner (`core/sensing.py:285-292`), the no-outbound-half reasoning
(`:306-312`), the post-commit hook wiring (`.githooks/post-commit`, `core.hooksPath`),
V4's SQLite confirmation (`CONVENTIONS.md:15-18`), V3's parse feasibility (4 pairs, 3
estimate-only, 11 pre-rule). First-parent diff grain pinned (§6(e)); v1 payload
worldview recorded (§6(f)). No code written. Awaiting the owner's `proposed → ready`
hand edit; depends on bp-018.
