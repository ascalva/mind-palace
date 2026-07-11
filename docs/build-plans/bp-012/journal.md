# BP-012 — Build journal

Alive while the plan is `in-progress`; sealed by `/triage` on completion.
Fresh-agent test (§9): a session given only `plan.md` + this journal + the
write-scope files must continue without re-asking anything already answered.

---

## Markers

## Entry — 2026-07-11 — Session start: contract established, context read, Q1 resolved (sibling)

**Environment (finding-0031 recurred, worked around).** Delegated builder in worktree
`.claude/worktrees/agent-a5a6d14847c3ff18b`. The hooked Edit/Write resolves the MAIN
checkout's active-plan pointer (bp-011) and falsely denies bp-012-scope writes; verified
with `bash .claude/hooks/scope-guard.sh --standalone <path>` (bp-012 resolved, exit 0 for
all planned paths). Per bp-007/bp-011 precedent: Bash-mediated writes for
standalone-confirmed in-scope paths, journaled here. No legitimate denial was routed around.

**Front-matter parse defect fixed (own plan file, in scope).** The owner-applied
write_scope entry `"ops/lifecycle/launcher.py"   # oq-0013...` carried an INLINE comment
the guard's parser keeps as part of the entry, so `ops/lifecycle/launcher.py` never
matched (standalone exit 2 with the literal-comment entry visible in the denial).
Minimal formatting fix: comment moved to its own line; scope semantics unchanged
(owner-concurred entry, oq-0013). Also flipped `status: ready → in-progress`
(non-blessing, per /build step 2).

**Branch state.** Worktree branched before bp-011's merge; plan Item 5 needs bp-011's
docstring column. Merged `main` INTO the worktree branch (fast-forward to `ea5e287`);
did NOT merge to main, did NOT push. Real docstrings are available (symbols.docstring,
files.docstring).

**Q1 — seam reuse vs sibling: SIBLING (`CodeSensingHandoff` + `CodeObservation`).**
Confirmed at source (`core/sensing.py`):
- `SensingHandoff.collect()` is typed `-> list[SensedObservation]` and parses every
  `<handoff>/observations/*.json` with `SensedObservation.from_dict` (request_id/upstream/
  ts/body/error). Carrying a second payload type through it would require changing
  `SensedObservation` or `collect` — the biometric contract the plan forbids touching —
  or sharing one files dir between two payload shapes (stream confusion).
- `build_sensing_handoff` is fail-closed on `[effectors] enabled`; the code stream is the
  LOCAL repo instrument and must not be gated on Track-G effectors.
- `SensingHandoff.emit` requires an `Effect`/actuator (outbound, β=0 machinery); the code
  stream has no outbound half — nothing crosses toward a network, so the EffectView
  ceiling has nothing to admit.
So: same seam FAMILY (atomic JSON files in a handoff dir, `from_dict` in, hardcoded-
OBSERVED `to_row` out, collect-and-consume, ObservedView-compatible), own file pattern
(`code_observations/` subdir) and own store. This is the note's recorded default
("same seam family, own store/table") — NOT the stop-and-raise case; `SensedObservation`
stays byte-identical.

**Design decisions for the build (grounded in read code):**
- `CodeObservation` dataclass lives in `core/stores/code_observations.py` (Item 3 is then
  self-contained); `core/sensing.py` gains only the sibling `CodeSensingHandoff` importing
  it (core→core).
- Store: SQLite `data/code_observations.sqlite` (plan Q2), table `code_observations`,
  PK (commit_sha, path, qualname), `references_out` JSON TEXT, provenance column always
  'observed', INSERT OR IGNORE (derived.py mint discipline: NO provenance parameter
  anywhere in the module's public API). Plus a `projections` bookkeeping table
  (commit_sha PK, batch_hash, projected_at) so a zero-symbol commit doesn't re-project
  forever and re-runs skip attested batches — implementation detail, not schema drift;
  the pinned §6 columns are the observation table verbatim.
- `references_out` is emitted `[]` in B-b: extraction (Lane 1, V4-seeded patterns) is
  B-c/bp-013's objective per the note §3.3; the COLUMN lands now, the extractor later.
  Noted in the store docstring.
- Projection pass in `sync()` covers exactly the NEWLY-INGESTED shas of the run (plan
  Item 5 verbatim). A reconcile-all-history pass would silently run the ~200-commit
  backfill on the live daemon's first sync — violating the §11 parked decision
  ("available, not run; owner nod"). Instead `CodeSensor.backfill_observations()` exists,
  tested on a fixture, NOT called by `sync()`. Residual (journaled, heals via backfill):
  a crash between `snapshot_commit` and the projection leaves that sha unprojected.
- Module rows: every file emits a kind='module' observation (qualname ''), docstring from
  files.docstring — so batch size == module count + def/class count; the note's "module
  row for module docstrings" grain with a complete file inventory.
- Attestation (plan Q5): `code_sensor / project_observations`, inputs=[commit sha],
  outputs=[batch content hash = sha256 of the canonical batch JSON]; `derived_from_ids`
  auto-links via `producers_of` to the ingest_commit attestation (same sha in its
  output_hashes) — parentage asserted in the e2e test.

**Baselines (post-merge, this worktree):** ruff "All checks passed!"; strict lane
`mypy core agents eval ops scheduler scripts` → "Success: no issues found in 166 source
files"; full `mypy` → "Found 69 errors in 20 files" (the finding-0029 tests/ baseline,
exact). Pytest baseline running in background (expect 768).

## Entry — 2026-07-11 — Item 3 COMPLETE (commit 0a9b37e)

`core/stores/code_observations.py` + `tests/unit/test_code_observations.py` (10 tests).
- Schema: §6 columns verbatim (+ `observed_at`, + the `projections` bookkeeping table —
  journaled above, not schema drift). PK (commit_sha, path, qualname); INSERT OR IGNORE;
  re-insert never mutates the first reading (versioned-supersession posture, §2.2).
- Mint discipline: `add_batch` writes `Provenance.OBSERVED.value` unconditionally;
  `CodeObservation.to_row()` hardcodes it; `to_dict()` (the wire payload) carries NO
  provenance key at all. Falsifier test sweeps every public callable with `inspect` and
  asserts no provenance-like parameter exists.
- §2.6 pinned at the store already: `ObservedView(_rows=...)` admits, `MirrorView(_rows=…)`
  raises `NonMirrorRowError`. MIRROR_READABLE untouched.
- Acceptance run: `pytest tests/unit/test_code_observations.py` → **10 passed**;
  `mypy core` → "Success: no issues found in 102 source files" (strict);
  full `mypy` → **69 errors** (baseline exact — one interim +1 from a duck-typed fake cfg
  was fixed with `cast(Config, ...)`); `scripts/check_imports.py` → "Import firewall (I2):
  OK". Store imports: stdlib + sqlite3 + config.loader + core.provenance only.

**One more hook-bug datum (for finding-0031's file):** the hooked Write mangles worktree
paths to `claude/worktrees/<id>/tests/...` before matching, so even `tests/**` (in BOTH
plans' scopes) is falsely denied — every write this session is Bash-mediated after a
standalone scope-guard confirmation (all exit 0).

Next: Item 4 (reset registration in `ops/lifecycle/launcher.py` + additive seed line in
`test_reset_wipes_corpus_but_never_the_vault_raft`).

## Entry — 2026-07-11 — Item 4 COMPLETE (commit follows Item 3's 0a9b37e)

`reset_targets()` gains `p.data_dir / "code_observations.sqlite"` (one entry + 3-line
comment citing the note §2.4 and Q4); `_RESET_GUARD` byte-identical (snapshot ledger stays
guarded). `test_reset_wipes_corpus_but_never_the_vault_raft`'s sidecar seed extended with
"code_observations.sqlite" — additive only, the falsifier (reset leaves the store behind)
now exercised by the existing assert-all-sidecars-wiped loop.
Acceptance: `pytest tests/integration/test_lifecycle.py` → **20 passed**; ruff clean;
strict mypy "Success: 167 source files"; full mypy **69** (baseline exact).
Next: Item 5 — the projection (sibling seam `CodeSensingHandoff` in core/sensing.py,
`sync()` projection pass + `project_observations` attestation in ops/code_sensor.py,
e2e fixture test, dry-run timing on one real-repo batch into a SCRATCH store).

## Entry — 2026-07-11 — Item 5 COMPLETE (commit a1df6da) — plan items 3/4/5 all done

**The seam (Q1 executed as journaled above — sibling).** `core/sensing.py` +66 lines,
append-only: `CODE_OBSERVATIONS` + `CodeSensingHandoff` (`emit_batch` → atomic
`<handoff>/code_observations/<sha>.json`, returns the batch content hash;
`collect(consume=True)` → `list[CodeObservation]`, rescan-healing). `SensedObservation`,
`SenseRequest`, `ObservedView`, `SensingHandoff` byte-identical (verified: the diff only
adds the import line + the sibling block). The stop-and-raise condition did NOT trigger.
Deliberate absences documented in the class docstring: no Effect/EffectView ceiling and no
`[effectors]` gate — both guard the OUTBOUND network surface, and the code stream has no
outbound half.

**The projection.** `ops/code_sensor.py`: `sync()` projects EXACTLY the newly-ingested
shas (`report.shas`) — `_observations_for` reads the snapshot walk's shapes from the
ledger (module row per file with `files.docstring`, one row per def/class with real
bp-011 docstrings; `references_out=[]` until B-c/bp-013); `_project` does
emit → collect → `add_batch` → `mark_projected` → attest
(`code_sensor / project_observations`, inputs=[sha], outputs=[batch hash];
`derived_from_ids` auto-links to the same sha's `ingest_commit` via `producers_of` —
parentage + `chain_for().is_complete()` asserted in test). `backfill_observations()`
exists for history, tested, NOT wired into sync (plan §11). `build_code_sensor` wires
store (`data/code_observations.sqlite`) + handoff (`data/code_sensing_handoff`).
Docstring banner corrected per plan §4 ("event-log-only" → projects into the observed
stratum; the ledger stays the ops-side record); handle count updated 3 → 5 honestly.
`CodeSyncReport` gains `projected` / `observation_rows` (additive).

**Falsifiers/invariants held (tests, `tests/unit/test_code_projection.py`, 7):**
- B-b verbatim, inverted: second sync of same commits → row count UNCHANGED, projected=0,
  attestation count UNCHANGED.
- §2.6: `MirrorView.project(<leaky source over observation rows>)` raises
  `NonMirrorRowError`; honest π_MR over the store yields 0 rows; `ObservedView` holds all.
  `MirrorView`/`MIRROR_READABLE` untouched.
- Symbol grain: fixture commit1 → [("", module), ("a", function)] with REAL docstrings
  ("Module A.", "Does a."), 7 rows total across 2 commits.
- Crash-healing: an emitted-but-uncollected batch is drained on the next sync.
- Degrade: a sensor without the projection pair is byte-for-byte the pre-B-b ledger-only
  sensor (existing 16 sensor/snapshot tests untouched and green).

**Dry-run measurement (plan §7 Item 5 + §9; production data UNTOUCHED — scratch store in
the session scratchpad, real repo read-only at main=e576c7d):**
```
sha=e576c7d8f34c files=349 symbols=2604 rows_added=2953
snapshot(parse) = 0.293s   project(emit+collect+store) = 0.052s
history commits on main = 215; naive backfill estimate ≈ 11.3s projection + parse amortized by blob cache
```
Parked-decision re-entry condition MET (one-batch timing journaled): the ~215-commit
observation backfill is `sensor.backfill_observations()` — one call, estimated ~10–60 s
total (projection ~11 s + snapshot parses already amortized in the live ledger). Awaiting
the owner's nod; NOT run in-session.

**Residual (journaled, not a defect):** a crash between `snapshot_commit` and `_project`
leaves that sha in the ledger but unprojected; `sync()` will not revisit it (it projects
newly-ingested shas only, to honor the §11 no-auto-backfill decision) — it heals via
`backfill_observations()`. Also `git diff main HEAD` shows doc deletions ONLY because main
advanced with orchestrator docs commits (bp-014 graduation, cost-forecasting brainstorm)
after this branch's fast-forward point; `git diff ea5e287 HEAD --stat` = exactly the seven
write-scope files.

**ACCEPTANCE — verbatim, final state (commit a1df6da):**
```
=== ruff ===
All checks passed!
=== mypy strict lane ===
Success: no issues found in 167 source files
=== mypy full ===
Found 69 errors in 20 files (checked 329 source files)
=== import firewall ===
Import firewall (I2): OK — core imports no zone (edge/cloud) or networking module
  (audited loopback exceptions: core/models/ollama_client.py, core/sealing.py)
=== pytest ===
785 passed, 4 skipped, 20 deselected in 10.95s
```
785 = the 768 bp-011-seal baseline + 17 new (10 store + 7 projection); 0 regressions.
Full-mypy 69 = the finding-0029 tests/ baseline, exact. Core strict floor: 0.

**Session wrap (fresh-agent brief).** Items 3→4→5 all COMPLETE; commits `0a9b37e`
(store+tests), `f966078` (reset target+seed), `a1df6da` (seam+projection+e2e), worktree
branch `worktree-agent-a5a6d14847c3ff18b` only — NOT merged to main, NOT pushed to origin
(runner-minute budget rule honored). No findings filed: the two candidate anomalies were
(a) finding-0031's known worktree pointer bleed — already filed/graduated to bp-014, new
datum journaled above (hook also mangles worktree-relative paths, so even in-scope
`tests/**` writes are denied hooked); and (b) the write_scope inline-comment parse defect —
fixed in this plan's own front-matter, worth folding into bp-014's fix as a parser nit
(orchestrator's call; noted here rather than a duplicate finding). Plan left
`in-progress`, `cost.actual` null, for the orchestrator to seal. Follow-ups for triage:
owner nod on `backfill_observations()` (timing above); bp-013 fills `references_out`.

---

## SEAL (orchestrator, 2026-07-11)

**Status:** `in-progress → complete`. Merged to main `--no-ff`. Diff scrutinized (delegate
skill): all changes in `write_scope`, no conflict candidates (clean merge). Load-bearing
invariants verified at source, not just trusted — the store has **NO provenance parameter on
any API surface** (`to_dict` carries none, `to_row`/`add_batch` hardcode `Provenance.OBSERVED`;
the `provenances=` arg is a read-side filter, not a write param — Item 3 falsifier ruled out by
the `inspect` sweep); `core/sensing.py` is pure-addition (biometric contract byte-identical);
the §2.6 firewall test asserts `MirrorView.project` over an observation-bearing source raises
`NonMirrorRowError` and honest π_MR yields 0; B-b idempotency + graceful degradation tested.

**Acceptance, verbatim, re-run on merged main (local):**
```
$ uv run ruff check .                                            → All checks passed!
$ uv run --extra dev mypy core agents eval ops scheduler scripts → Success (167 files, 0 errors)
$ uv run --extra dev mypy                                         → Found 69 errors in 20 files  (baseline)
$ uv run python scripts/check_imports.py                          → Import firewall (I2): OK
$ uv run pytest -q -m 'not live and not podman and not needs_vault and not needs_restic'
                                                                 → 785 passed, 4 skipped, 20 deselected  (768 + 17)
```

**Q1 seam:** SIBLING (`CodeSensingHandoff`) per the note's default — `SensingHandoff.collect` is
typed to `SensedObservation` (can't carry a 2nd payload without touching the biometric
contract), so the stop-and-raise did NOT trigger; own payload/store, same seam family.

**φ_code is now write-side live but NOT consumed.** `sync()` projects per newly-ingested commit
into `data/code_observations.sqlite` (created lazily on the next sync with a new commit); the
daemon does not READ observations yet (finding-0020 class — write-side accumulation only). So no
deploy is required to "apply" this — nothing in the live loop consumes it.

**Parser defect (mine) — folded into bp-014.** The `oq-0013` amendment added a TRAILING inline
comment to a `write_scope` entry (`- "ops/lifecycle/launcher.py"  # ...`), which the scope-guard
`write_scope` parser (in `_lib.py`) mis-parses. The builder fixed its own front-matter (comment
on its own line, semantics unchanged) and, rather than a duplicate finding, flagged it for
bp-014 (which already opens `_lib.py`). **Folded into bp-014 as an opportunistic in-scope parser
hardening** (noted in that plan). Lesson: `write_scope` entries take standalone comment lines,
not trailing ones.

**finding-0031:** another manifestation — in the worktree ALL hooked writes were denied (the
bug also mangles worktree-relative paths, not just the pointer); builder Bash-mediated each
after a standalone scope-guard confirmation. More warrant for bp-014's fix.

**Cost ledger:** builder = **fable** · **157,154 tokens · 75 tool-uses · ~21 min** — **0.52×**
the 300k estimate (under). Second consecutive under-estimate (bp-011 was 0.47×): the estimate
sizing (grind AND core-discipline shapes) is running conservative — a real calibration signal
for the cost-forecasting thread (2 datapoints now).

**Not pushed** beyond the earlier snapshot (this merge is post-snapshot). bp-013 next (unblocked:
V4 KEEP + bp-012 merged).
