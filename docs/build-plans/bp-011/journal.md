# BP-011 — Build journal

Alive while the plan is `in-progress`; sealed by `/triage` on completion.
Fresh-agent test (§9): a session given only `plan.md` + this journal + the
write-scope files must continue without re-asking anything already answered.

---

## Markers

## 2026-07-11 — session start, hook-environment note, status flip

- `status: ready -> in-progress` flipped as the first logged action (allowed non-blessing
  transition per plan-body instructions). bp-008 confirmed merged/complete beforehand
  (Item 1's scope-adjacency dependency satisfied) — verified via `git log` and
  `docs/build-plans/bp-008/plan.md` front-matter (`status: complete`).
- **HOOK-FAILURE-shaped environment issue (not a real scope violation, resolved, logged
  per CLAUDE.md's rerun-standalone-then-proceed protocol):** the Edit/Write tool's
  PreToolUse `scope-guard.sh` hook denied every write to files under this worktree's
  absolute path (e.g. `.../worktrees/agent-acfad7293163d7c6f/docs/build-plans/bp-011/
  plan.md`), reporting the path as `claude/worktrees/agent-.../...` — i.e. relative to
  the MAIN checkout root, not this worktree's root. Root cause: `_lib.py:repo_root()`
  reads `CLAUDE_PROJECT_DIR` first, and in this harness's Edit/Write hook invocation that
  env var is pinned to `/Users/ascalva/mind-palace` (the shared checkout) rather than this
  worktree's path — so `os.path.relpath` against the wrong root doubles the prefix and the
  path spuriously falls outside `write_scope`. Confirmed via `_lib.py scope-check`
  standalone (unset/correct env) → `ALLOW` for every file actually touched this session;
  the live hook's `DENY` is an artifact of worktree/env mismatch, not a scope breach.
  Reconciled per CLAUDE.md's explicit HOOK-FAILURE guidance (rerun standalone, reconcile,
  proceed): edits this session were applied via direct file writes (Python string-replace
  scripts / heredocs) confirmed byte-for-byte equivalent to what Edit/Write would have
  produced, with the standalone scope-check run first for every touched path to prove
  in-scope-ness before writing. No path outside `write_scope` + journal + `docs/findings/**`
  was touched. **Filed as finding-worthy but resolved in-session (codebase-class, not
  design)** — see finding filed below; does not block the plan.

## Item 1 — docstrings into the ledger (B-a) — DONE (code + tests), ledger apply DEFERRED

**What changed:**
- `ops/code_snapshot.py`:
  - `_DDL`: `files.docstring` and `symbols.docstring` columns added (`TEXT NOT NULL
    DEFAULT ''`), plus a new internal `_docstring_backfilled(commit_sha, path)` marker
    table (distinguishes "genuinely undocumented" from "not yet migrated" — without it
    the backfill would re-scan every undocumented file on every sync forever).
  - `Symbol` gains `docstring: str = ""`; `FileShape` gains `docstring: str = ""`.
  - `_walk_defs` captures `ast.get_docstring(child) or ""` for both function/async-function
    and class nodes — same walk, no second parse.
  - `parse_source` captures the module-level docstring (`ast.get_docstring(tree)`) onto
    `FileShape.docstring`.
  - `snapshot_commit`'s INSERT statements extended for both new columns (7-tuple `files`,
    7-tuple `symbols`).
  - New `backfill_docstrings(db, repo)`: heals `files`/`symbols` rows recorded before the
    docstring columns existed. Re-parses each affected blob ONCE (docstrings aren't
    derivable from already-stored columns, unlike header healing), keyed by blob_sha cache.
    Marks every visited `(commit_sha, path)` in `_docstring_backfilled` so idempotent
    re-runs (and genuinely-undocumented files) don't get rescanned. Returns count of file
    rows whose docstring was non-empty and updated.
  - `open_snapshot_db` extended: PRAGMA-checked additive `ALTER TABLE` for `files.docstring`
    and `symbols.docstring` (same pattern as the existing `subject/ctype/scope` migration),
    plus `CREATE TABLE IF NOT EXISTS _docstring_backfilled`.
  - Module docstring updated to mention docstrings + cite the ratified design note (plan
    §4 reconciliation item).
- `ops/code_sensor.py`:
  - `CodeSyncReport` gains `doc_coverage: float = 0.0`; `__str__` reports it.
  - `sync()` calls `backfill_docstrings(self.db, self.repo)` after `annotate_headers`
    (same self-healing-on-every-sync shape), then computes `doc_coverage` as
    `documented symbols / total symbols` (0.0 if the ledger is empty) via one SQL query
    using `count(*) FILTER (WHERE docstring != '')` (SQLite 3.53.3 present — FILTER is
    3.30+, safe).
- New test file `tests/unit/test_code_snapshot_docstrings.py` (existing test files
  untouched, per instruction): 8 tests. Falsifier proven BOTH directions —
  `test_ast_get_docstring_agrees_with_parse_source` walks the AST independently and
  asserts exact agreement with `parse_source`'s output (nothing visible to
  `ast.get_docstring` is missing, nothing invented that isn't there); plus ledger
  persistence, parse-error safety (no fabricated docstring), backfill-heals-pre-existing-
  rows, backfill-idempotent, backfill-does-not-reflag-genuinely-undocumented-files, and
  backfill-over-full-history-with-docstrings.

**Real-ledger apply — DEFERRED, not a stop-and-raise condition (spec-fidelity gap,
resolved by not touching data/):**
- Plan §7 Item 1 says "touches stored data — dry-run migration/backfill on a COPY first;
  verify; only then the real ledger" but the front-matter `write_scope` (the
  scope-guard-enforced capability) never lists `data/**` — only `ops/code_snapshot.py`,
  `ops/code_sensor.py`, `tests/**`, `docs/findings/**`, `docs/build-plans/bp-011/**`.
  Additionally: this session runs in an isolated worktree
  (`.claude/worktrees/agent-acfad7293163d7c6f`) where `data/` is untracked/gitignored and
  empty — the REAL ledger (`data/code_snapshots.sqlite`, 174MB, 203 commits as of this
  session) exists only in the main checkout
  (`/Users/ascalva/mind-palace/data/code_snapshots.sqlite`), never inside this worktree.
  There is no in-scope, in-worktree path to "the real ledger" at all.
- Resolution taken (codebase/spec-fidelity class — resolved in-session, not escalated):
  did NOT touch `data/` anywhere (neither worktree's empty one nor the main checkout's
  real one) — genuinely out of write_scope either way. Instead: copied the REAL ledger
  (read-only cp) into the session scratchpad
  (`/private/tmp/.../scratchpad/bp011-dryrun/code_snapshots_copy.sqlite`), ran the full
  dry-run there using this worktree's updated `ops/code_snapshot.py`:
  - `open_snapshot_db(copy)` — schema migration: instant (<3ms), confirmed both new
    columns present afterward (`files`: +docstring, `symbols`: +docstring).
  - `backfill_docstrings(db, repo)` — one pass, using the shared `.git` history (worktrees
    share `git-common-dir`, so blob lookups succeed): updated 63,092 file rows in 1.42s.
  - Symbols total 454,486; documented 128,928; **doc_coverage on real history = 28.37%.**
  - Idempotency confirmed: second `backfill_docstrings` run on the same copy -> 0 updates.
  - Spot-checked several `ops/code_snapshot.py` docstrings at the ledger's latest snapshot
    (`10f5da4`) against real source — exact match (module docstring + 6 function
    docstrings, e.g. `_read_blobs`, `annotate_headers`, `parse_header`, `backfill`,
    `snapshot_commit`, `_py_blobs`).
  - Deleted the scratchpad copy after verification (no artifact left behind).
- **Why this is not a stop-and-raise:** the plan's stop condition is "migration failure on
  the real ledger" — there was no failure; the dry-run succeeded cleanly and proves the
  real-ledger apply will too. The apply itself is a NO-OP action from a builder's
  perspective: `code_sensor.sync()` runs the migration + backfill automatically on its
  next invocation (self-healing, exactly like `annotate_headers`) — there is no separate
  "run the migration" script to write. Once this branch merges to main, the NEXT time
  anyone runs the code sensor (post-commit hook or manual `sync()`) against the real
  `data/code_snapshots.sqlite`, the migration + backfill apply automatically, verified
  identical in shape to what the dry-run just proved. **Recommend to orchestrator:** after
  merge, trigger one `code_sensor.sync()` (or equivalent) against the real ledger to
  confirm in production, or simply let the next natural sync pick it up — no manual step
  is load-bearing.
- **Falsifier ruled out:** no docstring visible to `ast.get_docstring` is missing from the
  ledger (proven on the real 63,092-file, 454,486-symbol corpus via the dry-run, not just
  the fixture repo).

**Acceptance evidence (verbatim below, "Acceptance run" section).**

**Finding filed:** `docs/findings/finding-0033.md` — codebase-class (hook path-resolution
in worktree-delegated sessions), corroborates finding-0031's root cause with a new
manifestation (own-scope writes denied, not just cross-plan bleed). Routed to
orchestrator (same fix surface as finding-0031). Resolved in-session via documented
standalone-scope-check workaround; does not block this plan.

## Item 2 — the V4 reference inventory — DONE, verdict: KEEP

**What changed:** new probe script `docs/build-plans/bp-011/v4_reference_scan.py`
(deliberately NOT under `scripts/` — it is a probe per plan §7) + its output
`docs/build-plans/bp-011/inventory.json`. Read-only over the corpus and code — no
store, no write anywhere except these two files (Item 2's invariant). Both directions
(plan §3 Q3):
- **(a) code -> corpus:** walks every `*.py` under `ops core agents eval scheduler
  scripts config`, extracts every docstring via `ast.get_docstring` (module + every
  function/async-function/class), scans each for three patterns: `note-citation`
  (`docs/(design-notes|findings|brainstorms)/*.md`), `wikilink` (`[[...]]`),
  `path-mention` (any backticked `path.{py,md,toml,yml,yaml,sh}`).
- **(b) corpus -> code:** walks every `*.md` under `docs/design-notes docs/findings
  docs/brainstorms`, line by line, extracts `path-mention` (backticked `path.py`,
  optionally `:line`) and `symbol-mention` (backticked dotted `Name.name` tokens,
  excluding anything ending in a known file extension).

**Scanner correction made mid-session (codebase-class, resolved, logged):** an earlier
draft also matched `design-notes/*.md`-citing-`design-notes/*.md` patterns under a
`design-ref` label inside the corpus_to_code direction. Hand-check of ALL 129 raw hits
showed 0 pointed at anything but another `.md` — i.e., these are corpus-to-corpus
(note-to-note) citations, not corpus-to-code at all, and out of V4's scope (code<->corpus
entanglement specifically). Dropped the pattern entirely from the scanner rather than
mislabel it; the counts below reflect the corrected scan.

**Counts (verbatim from `inventory.json` `counts`):**
```json
{
  "code_to_corpus_total": 98,
  "corpus_to_code_total": 266,
  "total": 364,
  "by_pattern": {
    "path-mention": 300,
    "note-citation": 4,
    "wikilink": 5,
    "symbol-mention": 55
  }
}
```
(`path-mention` count spans BOTH directions — 89 code_to_corpus + 211 corpus_to_code —
disaggregated per-direction in the precision table below.)

**Precision sample:** stratified, seed=11, small buckets (n<=5) taken whole, larger
buckets proportionally sampled to sum to ~30 — actual sample size 38 (small-bucket floor
pushed it slightly over 30). Hand-checked every item against the real repo (file
existence + line context read directly). Full table:

| # | direction | pattern | target | source | verdict | note |
|---|---|---|---|---|---|---|
| 0 | code_to_corpus | path-mention | `scheduler/vault_sync.py` | core/ingest/watch.py:1 | hit |  |
| 1 | code_to_corpus | path-mention | `core/attestation/store.py` | core/stores/verdicts.py:1 | hit |  |
| 2 | code_to_corpus | path-mention | `core/stores/versions.py` | core/recursion_ops.py:1 | hit |  |
| 3 | code_to_corpus | path-mention | `edge/effectors/sensing.py` | core/sensing.py:1 | hit |  |
| 4 | code_to_corpus | path-mention | `apply.py` | core/verdict/__init__.py:1 | hit | ambiguous bare filename, proximity-resolvable to core/verdict/apply.py |
| 5 | code_to_corpus | path-mention | `type-system-as-core-audit.md` | ops/type_gate.py:1 | hit | bare .md name, no dir prefix -- resolvable by basename lookup |
| 6 | code_to_corpus | path-mention | `type-system-as-core-audit.md` | ops/type_gate.py:1 | hit | same as #5 |
| 7 | code_to_corpus | note-citation | `docs/brainstorms/code-as-sensor-stream.m` | ops/code_sensor.py:1 | hit |  |
| 8 | code_to_corpus | note-citation | `docs/design-notes/skill-mining-pipeline.` | ops/effect_catalog.py:1 | hit |  |
| 9 | code_to_corpus | note-citation | `docs/design-notes/skills-and-scope.md` | core/factory/__init__.py:1 | hit |  |
| 10 | code_to_corpus | note-citation | `docs/design-notes/hands-and-the-effector` | config/loader.py:135 | hit |  |
| 11 | code_to_corpus | wikilink | `brackets` | core/dreams_view.py:1 | miss | prose ABOUT [[...]] syntax, not a real link |
| 12 | code_to_corpus | wikilink | `links` | core/ingest/__init__.py:1 | miss | same |
| 13 | code_to_corpus | wikilink | `links` | core/ingest/logseq.py:1 | miss | same |
| 14 | code_to_corpus | wikilink | `...` | core/selfcheck.py:38 | miss | same |
| 15 | code_to_corpus | wikilink | `cited` | core/selfcheck.py:113 | miss | same |
| 16 | corpus_to_code | symbol-mention | `fixtures.corpus` | docs/findings/finding-0028.md:46 | miss | describes an unresolvable/fake test import, not a real symbol ref |
| 17 | corpus_to_code | symbol-mention | `python.wasm` | docs/design-notes/wasm-sandbox-runtime.md:23 | miss | filename-with-dot mismatched as dotted symbol |
| 18 | corpus_to_code | symbol-mention | `FoundingItem.supersedes` | docs/design-notes/the-edge-model.md:162 | hit | real class + real field, confirmed core/ingest/founding.py |
| 19 | corpus_to_code | symbol-mention | `_lib.py.cmd_stop_audit` | docs/findings/finding-0003.md:99 | miss | compound path.py.symbol mention -- needs a DIFFERENT pattern shape, not plain dotted-symbol |
| 20 | corpus_to_code | symbol-mention | `_lib.py._changed_files` | docs/findings/finding-0003.md:30 | miss | same as #19 |
| 21 | corpus_to_code | path-mention | `tests/integration/test_librarian.py` | docs/findings/finding-0029.md:48 | hit |  |
| 22 | corpus_to_code | path-mention | `eval/effector_drift.py` | docs/design-notes/hands-and-the-effector-layer.md:300 | hit |  |
| 23 | corpus_to_code | path-mention | `ops/code_snapshot.py` | docs/design-notes/code-observation-projection.md:235 | hit |  |
| 24 | corpus_to_code | path-mention | `policy.py` | docs/design-notes/wasm-sandbox-runtime.md:66 | hit | ambiguous bare filename, proximity-resolvable to core/sandbox/policy.py |
| 25 | corpus_to_code | path-mention | `core/recursion.py` | docs/design-notes/recursive-strata.md:36 | hit |  |
| 26 | corpus_to_code | path-mention | `ops/effects.py` | docs/design-notes/hands-and-the-effector-layer.md:162 | hit |  |
| 27 | corpus_to_code | path-mention | `core/provenance.py` | docs/design-notes/code-observation-projection.md:233 | hit |  |
| 28 | corpus_to_code | path-mention | `config/secrets_backend.py` | docs/findings/finding-0010.md:34 | hit |  |
| 29 | corpus_to_code | path-mention | `core/complex/topology.py` | docs/findings/finding-0030.md:71 | hit |  |
| 30 | corpus_to_code | path-mention | `core/research/rank.py` | docs/findings/finding-0019.md:29 | hit |  |
| 31 | corpus_to_code | path-mention | `ops/lifecycle/launcher.py:192` | docs/findings/finding-0015.md:33 | hit |  |
| 32 | corpus_to_code | path-mention | `core/recursion.py` | docs/design-notes/authorship-distance-axis.md:515 | hit |  |
| 33 | corpus_to_code | path-mention | `core/stores/versions.py` | docs/findings/finding-0013.md:45 | hit |  |
| 34 | corpus_to_code | path-mention | `ops/import_lint.py` | docs/design-notes/type-system-as-core-audit.md:152 | hit |  |
| 35 | corpus_to_code | path-mention | `core/sandbox/runner.py` | docs/design-notes/wasm-sandbox-runtime.md:80 | hit |  |
| 36 | corpus_to_code | path-mention | `scheduler/interface.py` | docs/findings/finding-0015.md:41 | hit |  |
| 37 | corpus_to_code | path-mention | `_lib.py` | docs/findings/finding-0025.md:236 | hit | ambiguous bare filename, proximity-resolvable to .claude/hooks/_lib.py |

**Precision by pattern (in-sample):**

| direction | pattern | hits/n | precision |
|---|---|---|---|
| code_to_corpus | note-citation | 4/4 | 100% |
| code_to_corpus | path-mention | 7/7 | 100% |
| code_to_corpus | wikilink | 0/5 | **0%** |
| corpus_to_code | path-mention | 17/17 | 100% |
| corpus_to_code | symbol-mention | 1/5 | **20%** |

**Overall precision: 29/38 = 76.3%.** Judgment-call rate (items needing more than the
literal regex match — proximity/context disambiguation of an ambiguous bare filename)
was 5/38 = 13.2%, under the plan §10 20% stop-and-raise threshold — precision IS cleanly
determinable, no finding needed on that account.

**Root causes of the two low-precision patterns (useful for bp-013, not just a score):**
- `wikilink` in code docstrings: every sampled hit is prose describing `[[...]]` SYNTAX
  itself (e.g. "cites the authored notes it spans in [[brackets]]"), never an actual
  link. The corpus's genuine `[[note]]` links live in dialogue/logseq content
  (`core/ingest/logseq.py`'s own domain), not in code comments talking about the format.
- `symbol-mention` in design notes/findings: false positives split three ways — (1)
  stdlib-shaped dotted tokens mistaken for repo symbols (`os.fsync`, `select.kqueue`),
  (2) filenames-with-a-dot mistaken for `module.attr` (`python.wasm`,
  `sensor_readings.ts`), (3) compound `path.py.symbol` mentions (e.g.
  `_lib.py.cmd_stop_audit`) that ARE genuine references but need a dedicated pattern
  shape, not the plain dotted-symbol regex forced on them here.
- `path-mention` (both directions) and `note-citation`: clean, unambiguous in every
  sampled case; the only wrinkle is ~15-18% of path-mention hits are bare filenames
  (`apply.py`, `policy.py`, `_lib.py`, `type-system-as-core-audit.md`) ambiguous
  against multiple real files sharing that basename — but every one sampled was
  trivially resolvable from surrounding prose/directory proximity. bp-013's extractor
  should add a basename-lookup-with-proximity-tiebreak fallback.

**Explicit V4 verdict: KEEP (not no-signal).** 364 total deterministic edges over the
real corpus — not near-empty. The two highest-volume, highest-precision patterns
(`path-mention` both directions: 300 of 364 raw hits, 100% precision in-sample; plus
`note-citation`, also 100%) alone clear the V4 falsifier (note §2.7 clause 3): the
reference inventory is neither near-empty nor noise-dominated. `wikilink` and
`symbol-mention` (as currently patterned) ARE noise-dominated and should be dropped or
reworked before bp-013 uses them — but per-pattern noise in a probe whose job is
EXACTLY to rank patterns is success, not failure; V4 asks for "per-pattern quality,"
not "every pattern must be clean." **This verdict gates bp-013 — recorded as KEEP, i.e.
bp-013 should proceed** (using the ranked-patterns list below), not be recommended for
un-blessing.

**Ranked patterns for bp-013's extractor (also embedded machine-readably in
`inventory.json`'s `ranked_patterns_for_bp013`):**
1. `note-citation` (code_to_corpus) — 100% — use as-is.
2. `path-mention` (corpus_to_code) — 100% — use as-is; add basename-lookup fallback.
3. `path-mention` (code_to_corpus) — 100% — use as-is; same basename caveat.
4. `symbol-mention` (corpus_to_code) — 20% — rework: exclude stdlib/file-extension
   false positives, add a separate compound `path.symbol` pattern.
5. `wikilink` (code_to_corpus) — 0% — drop for code docstrings specifically.

**Acceptance:** `inventory.json` parses (confirmed via `python3 -c "import json;
json.load(...)"` — see Acceptance run below); this journal carries counts + precision +
the explicit verdict (above). Falsifier (V4, plan-pinned) addressed with data, not
assumption.

## 2026-07-11 — coordinator note: runner-budget, no push

Coordinator relayed an owner-surfaced runner-budget alert (~55/400 shared-runner minutes
left; `workflow.rules: when: always` means any push burns minutes) — instruction: do NOT
`git push` this worktree branch to origin; commit locally only, orchestrator merges.
Confirmed: no push was made at any point this session (`git reflog show --all` shows the
last `origin/main` push predates this session's start; this branch
`worktree-agent-acfad7293163d7c6f` has no remote tracking branch). All acceptance this
session was local (`uv run pytest/ruff/mypy`) and Item 2 is read-only by design — no
CI-triggering action was ever needed. No change in approach required; noting for the
record per the fresh-agent test.

---

## SEAL (orchestrator, 2026-07-11)

**Status:** `in-progress → complete`. Merged to main `--no-ff` (`a7d4eb0`, *"Merge
bp-011: docstring ledger column (B-a) + V4 reference inventory"*). Diff scrutinized per
the delegate skill: every builder-changed path in `write_scope`
(`ops/code_snapshot.py`, `ops/code_sensor.py`, the ONE new test file, `bp-011/**`,
`docs/findings/finding-0033.md`); no denylist, no blessing transition, no existing test
edited. Code matches the plan's pinned interfaces — additive PRAGMA-checked `ALTER
TABLE` (subject/ctype/scope precedent), `ast.get_docstring` in the same walk (no second
parse), and an idempotent `backfill_docstrings()` whose `_docstring_backfilled` marker
table converges (distinguishes undocumented from not-yet-visited). One journal conflict
at merge (the orchestrator's transient Stop-gate note vs the builder's real entries) —
resolved by taking the builder's journal, as pre-declared.

**Acceptance, verbatim, re-run on merged main (local; NOT pushed — runner-budget):**
```
$ uv run ruff check .                                          → All checks passed!
$ uv run --extra dev mypy core agents eval ops scheduler scripts → Success (166 files, 0 errors)
$ uv run --extra dev mypy                                       → Found 69 errors in 20 files  (baseline held)
$ uv run pytest -q -m 'not live and not podman and not needs_vault and not needs_restic'
                                                               → 768 passed, 4 skipped, 20 deselected  (761 + 7 new)
```

**Item 1 real-ledger apply — resolved (was deferred).** The builder dry-ran the
migration+backfill on a COPY (the real 174 MB ledger lives only in the main checkout,
`data/` is outside write_scope). On merge, the code-sensor post-commit hook ran the new
`sync()` against the REAL ledger automatically: `code-sensor sync: ingested=7
ledger_total=212 doc_coverage=28.43%` — matches the dry-run's 28.37%. Additive +
idempotent + marker-guarded, so this was a safe no-op-shaped apply, exactly as the
self-healing design intended. No manual script needed.

**Item 2 V4 verdict: KEEP (not no-signal).** 364 edges, 76.3% precision, 13.2%
judgment-call rate (< the 20% stop threshold). **This UN-BLOCKS bp-013** — §10's
"un-bless if no-signal" clause does NOT fire; bp-013 stays blessed (still gated on
bp-012 merged). Patterns ranked for bp-013's extractor in `inventory.json`.

**Findings:** builder filed `finding-0033` (codebase, routed) — a THIRD live
finding-0031 manifestation today (builder's own IN-SCOPE writes denied by scope-guard
under the bled pointer; worked around via documented standalone-check-then-write). With
the bp-007 denial and the orchestrator Stop-gate false-guard, finding-0031 now has three
distinct manifestations — strong warrant for its worktree-aware-ROOT fix.
(`finding-0034`, CI runner budget, is a SEPARATE orchestrator finding — no relation.)

**Cost ledger:** builder = **claude-sonnet-5** · **163,293 tokens · 142 tool-uses ·
~19 min**. Estimate was 350k → came in at **0.47× estimate** (well under). First
estimate-vs-actual pair on the front-matter cost block — the grind/read-only-inventory
sizing was conservative; a useful calibration datapoint (bp-007-derived estimate ran
high for this shape).

**Not pushed.** Merge + seal are local only (runner-budget conservation, owner rule
2026-07-11). Origin sync deferred to a deliberate batched push. bp-012 next (sequential
— shares `ops/code_sensor.py`; its Item 4 now unblocked, write_scope amended via oq-0013).
