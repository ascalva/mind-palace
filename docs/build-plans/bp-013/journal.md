# BP-013 — Build journal

Alive while the plan is `in-progress`; sealed by `/triage` on completion.
Fresh-agent test (§9): a session given only `plan.md` + this journal + the
write-scope files must continue without re-asking anything already answered.

---

## Markers

## Entry — 2026-07-11 — Session start: contract, branch sync, scope correction, Q-decisions

**Contract.** Delegated builder, worktree `.claude/worktrees/agent-a80bc7f9344a9a5af`,
branch `worktree-agent-a80bc7f9344a9a5af`. Active-plan pointer set to bp-013; plan
`status: ready → in-progress` flipped + committed (`a1d9fc6`, non-blessing, /build step 2).
Runner-budget rule in force: NO `git push` at any point; commit locally only; the
orchestrator scrutinizes + merges. All acceptance local via `uv run`.

**Scope correction (coordinator, mid-session).** The task prompt initially said
`ops/lifecycle/launcher.py` was added to write_scope (oq-0013 extension). The coordinator
CORRECTED this: the amendment was made on main AFTER this worktree branched and has been
REVERTED there — launcher.py is NOT in bp-013's scope for this session. My transient
plan-file write_scope amendment was reverted before any commit; committed scope is exactly:
`core/stores/reference_edges.py`, `ops/code_sensor.py`, `tests/**`, `docs/findings/**`,
`docs/build-plans/bp-013/**`.

**PARKED — reset-registration for `reference_edges.sqlite` (Q4).** The store is
corpus-layer and should join `reset_targets()` (same as bp-012's
`code_observations.sqlite`), but `ops/lifecycle/launcher.py` is out of this worktree's
scope — the ORCHESTRATOR registers it post-merge (owner-concurred oq-0013 extension; a
known follow-up, not a defect — per coordinator instruction, no finding filed).
Consequence: the reset-test sidecar seed is also NOT extended here (it would fail without
the launcher line); the orchestrator's post-merge registration should extend
`test_reset_wipes_corpus_but_never_the_vault_raft`'s seed with
`"reference_edges.sqlite"` additively, exactly the bp-012 Item 4 shape.

**Branch state.** Worktree branched at `e576c7d`, BEFORE bp-012's merge; bp-013 depends
on bp-012 (`core/stores/code_observations.py`, `project_observations`). Merged `main`
(`88cf58c`, bp-012 seal) INTO this branch — clean merge, no conflicts. Did NOT merge to
main, did NOT push.

**Q-decisions (plan §3 defaults, confirmed at source):**
- **Q1 (why a new store):** confirmed — `build_complex(view, *, edges=None, derived=None,
  sim_floor=...)` has no parameter for a second edge store; the isolation is by
  construction. Docstring carries the rationale + the §4 reconciliation sentence (the
  balance math holds no handle to this store; the 2026-07-10 standing fact stays true).
- **Q2 (corpus endpoint identity): path for ALL targets this session.** Confirmed at
  source: design notes/findings/brainstorms are NOT in the vault catalog (`docs/**` is
  repo content, not vault content — `VaultCatalog` keys by vault `source_path`), so no
  digest is resolvable for ANY target bp-011's validated patterns produce (targets are
  repo-relative `.md`/`.py`/config paths). The Q2 default's digest-for-vault-notes branch
  is therefore VACUOUS for Lane 1 today: recorded as `target_kind` on the edge
  (`"path"` now; `"digest"` reserved for when a vault-note target becomes resolvable).
  No catalog change needed — the §10 stop-and-raise (Q2 needs catalog changes) does NOT
  fire.
- **Q3 (symmetry):** directed as extracted, no auto-symmetrize; consumers symmetrize on
  read. Recorded in the store docstring.
- **Q4:** corpus-layer reset target — PARKED to orchestrator (above).

**Patterns kept vs dropped (bp-011 inventory `ranked_patterns_for_bp013`, precision bar):**
- KEEP `note-citation` (code→corpus, 100%), `path-mention` (code→corpus, 100%),
  `path-mention` (corpus→code, 100%).
- DROP `wikilink` (code→corpus, 0% — prose about [[...]] syntax, not links) and
  `symbol-mention` (corpus→code, 20% — stdlib-shaped tokens, filenames-with-dots,
  compound path.symbol needs its own pattern). Both are below the measured bar; Lane 1 is
  precision-first (a wrong deterministic edge is worse than a missing one). The Item 7
  falsifier test asserts no edge is ever minted with these types.
- Bare-filename path-mentions (the bp-011 "basename-lookup fallback" recommendation):
  the extractor stores the target AS WRITTEN (deterministic, no proximity judgment at
  extraction time — resolution heuristics are a consumer concern; anything requiring
  directory-proximity disambiguation is judgment, which Lane 1 must not exercise).
  Journaled as the conservative reading of "use as-is; add basename-lookup fallback":
  the fallback recommendation is about a CONSUMER resolving bare names, and baking a
  proximity tiebreak into the extractor would push it below determinism. Kept simple.

## Entry — 2026-07-11 — Item 6 COMPLETE — the reference-edge store

`core/stores/reference_edges.py` + `tests/unit/test_reference_edges.py` (9 tests).
- Schema: `reference_edges` table — edge_id (content-derived over (direction, ref_type,
  code endpoint, corpus endpoint, source_line) — the plan-pinned identity: source/target
  ARE the typed endpoints, direction orients them), direction, ref_type, commit_sha,
  code_path, qualname, corpus_ref, corpus_kind, source_line, created_at (not identity).
  INSERT OR IGNORE = append-only + idempotent; first reading wins, never mutated (tested).
- Type vocabulary: `REF_TYPES` = the §2.3 shape verbatim (note-citation | path-mention |
  symbol-mention | design-ref). `wikilink` is NOT in the vocabulary — unrepresentable at
  mint (ValueError, tested). symbol-mention/design-ref are representable (schema domain)
  but the EXTRACTOR never mints them (precision gate lives in ops/code_sensor.py — Item 7).
- No sign, no weight, no provenance column: a fact record, not a balance input — nothing
  here can be assembled into an adjacency.
- Docstring carries: Q1 rationale (cross-stratum endpoints; 𝔎|_MR authored-only;
  EdgeStore feeds A_signed; deliberately no build_complex parameter — the versions.py
  separation pattern), the §4 reconciliation sentence (the 2026-07-10 standing fact
  remains TRUE — the balance math holds no handle to this store), Q2/Q3/Q4, and the B-c
  falsifier verbatim.
- Item 6 falsifier grep-asserted: `test_no_import_path_from_core_complex_to_this_store`
  scans `core/complex/**/*.py` for the string `reference_edges` — must stay empty.
- `open_reference_edge_store` → `data/reference_edges.sqlite` (sibling convention).
- Acceptance: 9 passed; ruff clean; `mypy core` strict → "Success: no issues found in
  103 source files".
- Hook note: Edit/Write tools worked normally this session (no finding-0031 denial so
  far — no Bash-mediated write workaround needed).

## Entry — 2026-07-11 — Item 7 COMPLETE — extraction at projection time

`ops/code_sensor.py` + `tests/unit/test_reference_extraction.py` (8 tests) +
`docs/findings/finding-0036.md`.
- `extract_references(docstring, source_line)` — the Lane-1 docstring pass: bp-011's
  probe regexes VERBATIM (`v4_reference_scan.py` — the measured precision belongs to
  those expressions; rewriting them would orphan the measurement). Validated patterns
  only; exact duplicates collapse deterministically (first wins). source_line = the
  docstring owner's line (module = 1, probe convention; symbols.lineno now selected in
  `_observations_for`'s SQL).
- `VALIDATED_PATTERNS` = {(code_to_corpus, note-citation), (code_to_corpus,
  path-mention), (corpus_to_code, path-mention)} — the three 100%-precision entries of
  `ranked_patterns_for_bp013`. DROPPED below the bar: wikilink (0%), symbol-mention
  (20%). The Item 7 falsifier is test-pinned: the fixture PLANTS a [[wikilink]] and
  dotted symbol-mentions and asserts no edge carries them and every minted edge's
  (direction, ref_type) ∈ VALIDATED_PATTERNS.
- **Spec-fidelity resolution (finding-0036, resolved in-session):** Item 7's
  "populates references_out and mints the corresponding edges" literally covers only
  code→corpus, but the pinned pattern set includes corpus_to_code/path-mention (rank 2,
  100%, 211/364 edges — the finding-0021 corroboration direction) and no other item
  extracts it. Implemented BOTH directions in the same attested pass: corpus→code scans
  the commit's OWN tree (`git show sha:path`, deterministic §2.2 — not the working tree)
  over docs/design-notes|findings|brainstorms with the probe regex. Reversal seam if the
  orchestrator prefers the literal reading: delete `_corpus_reference_edges` + its call.
- Endpoint details: `:line` suffixes on corpus→code mentions are STRIPPED from the typed
  code endpoint (an endpoint is a path, not a path:line); targets otherwise stored AS
  WRITTEN (bare filenames unresolved — consumer-side judgment, journaled at session
  start). corpus_kind='path' everywhere (Q2 — no vault-note target is resolvable today).
- Attestation: WITHIN `project_observations`, no new kind (test-pinned: attestation
  action set is exactly {ingest_commit, project_observations}). The batch content hash
  now covers references_out (it rides `to_dict()`); the corpus→code half is not in the
  hash but is deterministically re-derivable from the sha (journaled, acceptable — the
  attestation covers the action, output identity unchanged in shape from bp-012/Q5).
- Idempotency: minting is gated by `_project`'s is_projected short-circuit AND the
  store's content identity — re-sync mints 0 (tested); `backfill_observations()` mints
  for unprojected history (tested); a sensor without the reference store degrades to
  exact B-b behavior (tested; bp-012's 17 existing projection/observation tests pass
  UNCHANGED — no existing test edited).
- Consequence journaled: commits already projected by bp-012 (marked in `projections`)
  will never retro-mint edges — same versioned-re-interpretation posture as
  references_out itself; history enters via backfill (PD-d, owner nod) or a future
  φ_code re-projection design. Also: `core/stores/code_observations.py`'s docstring
  line "references_out ... is emitted EMPTY by B-b; the extractor is B-c / bp-013"
  is now historical on its trailing clause — that file is OUT of bp-013's write_scope,
  so left untouched; flagging for the orchestrator (one-line doc touch-up at merge, or
  leave — the sentence is still true as written about B-b itself).
- `build_code_sensor` wires `reference_edges=open_reference_edge_store(cfg)`; module
  docstring updated (six handles; Lane-1 paragraph).
- Acceptance: 8 passed (+ bp-012's 17 unchanged); ruff clean; `mypy core ops` strict →
  "Success: no issues found in 130 source files".

## Entry — 2026-07-11 — finding-0035 → finding-0036 renumber (collision with main)

The worktree's Item-7 spec-fidelity finding was `finding-0035`, but main sealed a DIFFERENT
`finding-0035` (`fb23c48` — the orchestrator self-resume-prompt practice) after this worktree
branched. To avoid an add/add merge conflict at the orchestrator's merge, `git mv
docs/findings/finding-0035.md docs/findings/finding-0036.md`; front-matter `id:` bumped to
`finding-0036` (the H1 is descriptive, carries no number); both journal references to the
BUILDER's finding updated to 0036. `grep -rn finding-0035 docs/` is now empty (no ref to
main's meaning here). Committed `bc28dea` (no Co-Authored-By — a mechanical renumber).

## Entry — 2026-07-11 — Item 8 COMPLETE — bit-identical reference-edge isolation proof (B-c falsifier automated)

`tests/integration/test_reference_edge_isolation.py` (2 tests) — the structural twin of
`test_edge_partition.py`, specialized to the Lane-1 reference-edge store. Item 8 is the B-c
falsifier automated forever (plan §6, verbatim): *"any instrument result changes when reference
edges are added or removed."*

**What the test asserts.**
- `test_reference_edges_never_reach_the_balance_math`: builds the SAME two-theme MirrorView the
  edge-partition mirror uses (8 authored nodes p0–p3 / s0–s3, seeded rng(0), identical fixture),
  runs the FULL instrument stack via a `measure()` closure — `frustration(kx.A_signed)` (balance
  λ + frustrated triangles), `forman(kx.A)` (curvature), `cluster_notes(note_centroids(...),
  threshold=0.5)` (clustering) — snapshots (lam0, tris0, curv0, cl0); then POPULATES the reference
  store; re-`measure()`s; asserts every result bit-identical (`lam0 == pytest.approx(lam1)` — the
  only approx, matching the mirror; `tris0/curv0/cl0 == …` exact). An EdgeStore CONTRADICT(p0,s0)
  is planted first so `A_signed` carries real frustration to move IF the store leaked.
- `test_build_complex_has_no_handle_to_the_reference_edge_store`: structural, bp-013-specific —
  `set(inspect.signature(build_complex).parameters) == {"view","edges","derived","sim_floor"}`.
  There is NOWHERE to pass a `ReferenceEdgeStore`, so it cannot reach `A_signed` by construction
  (the mirror asserts the same set for the E_disp stores; this one is named for THIS store, a
  forever-green guard).

**How the with/without difference is REAL (the actual edges planted).** Between the two
`measure()` calls the test opens a real `ReferenceEdgeStore(tmp_path/"reference_edges.sqlite")`
and `add_batch`es four `ReferenceEdge.mint(...)` rows whose CORPUS endpoints ARE node digests of
the complex (so if the store were reachable, THESE rows over THESE nodes are exactly what would
move an instrument): `code_to_corpus/note-citation → p0`, `code_to_corpus/path-mention → s0`,
`corpus_to_code/path-mention → p1`, `corpus_to_code/path-mention → s3` (both directions, the
validated ref_types). The difference is proven real, not assumed: `assert added == 4`,
`assert ref_store.count() == 4`, and `assert {e.corpus_ref for e in ref_store.all()} <=
set(node_digests)` — the store REALLY has rows over the complex's own nodes (the mirror asserts
`versions.count() == 1`; this is its analogue with the stronger endpoint-overlap assertion).

**Result: the isolation proof PASSES.** All instrument results are bit-identical WITH and WITHOUT
the populated store. No B-c falsification (plan §10 stop-and-raise did NOT fire).

**core/complex/** + core/stores/edges.py are UNTOUCHED** — Item 8 is test-only, which is the
point. `git diff --stat main...HEAD -- core/complex/ core/stores/edges.py` is EMPTY. Full stat:
```
 core/stores/reference_edges.py          | 233 +++++
 docs/build-plans/bp-013/journal.md      | (this entry)
 docs/build-plans/bp-013/plan.md         |   2 +-
 docs/findings/finding-0036.md           |  55 +++
 ops/code_sensor.py                      | 154 +++--
 tests/unit/test_reference_edges.py      | 134 +++  (Item 6 + the mypy-baseline fix below)
 tests/unit/test_reference_extraction.py | 198 +++
 tests/integration/test_reference_edge_isolation.py  (Item 8, new)
```

**Codebase fix folded in (in-scope, `tests/**`).** Item 6's `test_reference_edges.py:27` had a
bare `kw: dict = dict(...)` — a `[type-arg]` error that pushed the WHOLE-TREE mypy baseline from
finding-0029's 69 to 70. Fixed to `kw: dict[str, Any]` (`dict[str, object]` was tried first but
its `**kw` unpack into `mint`'s typed params added two `[arg-type]` errors → net worse;
`dict[str, Any]` unpacks cleanly). Whole-tree mypy back to exactly **69**. Not a finding — a
one-line type annotation on an in-scope test file, resolved and annotated (codebase class).

**Acceptance — verbatim command output.**
- `uv run pytest tests/integration/test_reference_edge_isolation.py -v`:
  ```
  tests/integration/test_reference_edge_isolation.py::test_reference_edges_never_reach_the_balance_math PASSED [ 50%]
  tests/integration/test_reference_edge_isolation.py::test_build_complex_has_no_handle_to_the_reference_edge_store PASSED [100%]
  ============================== 2 passed in 0.82s ===============================
  ```
- `uv run pytest -q -m 'not live and not podman and not needs_vault and not needs_restic'`:
  `804 passed, 4 skipped, 20 deselected in 23.52s` (resume brief expected ~785; actual **804**
  after Items 6+7's unit tests and Item 8's 2 integration tests all landed).
- `uv run ruff check .`: `All checks passed!`
- `uv run mypy core agents eval ops scheduler scripts`: `Success: no issues found in 168 source files` (strict floor, 0 errors).
- `uv run mypy` (whole `[tool.mypy].files`, incl `tests/`): `Found 69 errors in 20 files (checked 333 source files)` — matches finding-0029 baseline exactly.
- `uv run python scripts/check_imports.py`: `Import firewall (I2): OK` (Invariant-2 green).

Plan left `in-progress` — the completion flip is the orchestrator's /triage seal, not a builder
step. NOT pushed (runner-budget rule); Item 8 commit is local for the orchestrator to merge.
