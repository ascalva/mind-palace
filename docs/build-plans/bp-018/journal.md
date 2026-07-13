# bp-018 journal

## 2026-07-12 — session 1 start: setup, baselines, Q3 re-grep (builder)

**Status:** in-progress flipped (builder's flip); env synced (`uv sync --all-extras` —
worktree venv lacked dev extras); baselines pinned pre-change: `ruff check .` clean,
argless `uv run mypy` = **Found 69 errors in 20 files (checked 334 source files)** (the
pinned tail the gate must reproduce).

**Q3 re-grep at HEAD (plan §3 obligation):** callers of
`add_batch|is_projected|mark_projected` are `ops/code_sensor.py` (in scope),
`tests/unit/test_code_observations.py` (in scope), **and
`tests/unit/test_code_projection.py:111`** — `obs.is_projected(sha)` one-arg, a test
file the plan's Q3 inventory missed and write_scope omits. Not a §10 stop (test callers
are anticipated); it is a scope-grant gap. Resolution (finding-0047, spec-fidelity,
builder-resolves): honor §6(c) pins for `add_batch` (keyword-only required
`interpreter`) and `mark_projected` (required third arg) — their only callers are in
scope — and give `is_projected` alone `interpreter: str | None = None` where `None` =
"projected under ANY interpreter" (exactly the semantic that call site asserts). The
forgotten-arg hazard this default reopens is pinned shut by Item 4's bump→re-projects
acceptance test. Deviation annotated in code comment + finding.

Also checked: no existing test pins `_RESET_GUARD`/`reset_targets` (my Item 4 test will
be the first pin); `tests/unit/test_reference_extraction.py` constructs
`CodeSensor`+store but only via defaults — stays green untouched.

**Item 1 CLOSED** (commit `f8a2f95`): `INTERPRETER_VERSION = "1.0.0"` in
`ops/code_sensor.py` (§6(a) verbatim); `tests/unit/test_interpreter_versions.py` pins
`phi_code → ("1.0.0", 55e88303…)` over sources `(ops/code_sensor.py,
ops/code_snapshot.py)`; fingerprint = sha256 over (path, NUL, bytes, NUL) per file.
Acceptance run: 2 passed at HEAD; **falsifier-demo**: one appended byte →
`test_source_hash_matches_the_pin[phi_code]` RED (assertion message carries the
bump-or-re-pin instructions + the new hash); revert → green. Side-effect audit before
the demo: the test only reads file bytes + imports `ops.code_sensor` (regex compiles,
class defs — no store writes/network/subprocess); mutation restored from a scratchpad
backup, not `git checkout` (which would have eaten the Item 1 edit). Pre-commit gate:
ruff clean, argless mypy still 69 (335 files — new file adds zero), fast suite 838
passed / 7 skipped. NOTE for Items 3–4: every later edit to `ops/code_sensor.py`
re-reds the ratchet — each such commit re-pins the hash at 1.0.0 in the same commit,
journaled as a **declared refactor** (plumbing passes the version through; the batch
content φ_code emits is unchanged, so no worldview change — the same honesty argument
as §6(d)'s 1.0.0 backfill).

**Item 2 CLOSED** (commit `e4bf8a6`): `core/stores/observation_history.py` per §6(b) —
DDL verbatim; `archive` INSERT OR IGNORE on (store, identity_json, interpreter);
`chain` oldest-first by rowid (supersession only appends, so rowid IS generation
order), returns superseded rows verbatim; `count(store|None)`. Identity keys per
member in module registry `IDENTITY_KEYS = {"code": (commit_sha, path, qualname)}` —
the pinned 3-tuple archive shape carries rows not identity dicts, so the sidecar
extracts identity via the member's registered key columns (key-columns-only coupling,
lighter than the §11-rejected diff-grain coupling; bp-019 registers 'agent').
Acceptance: 9 passed — round-trip ordered, re-archive changes nothing (count + payload
pinned), per-member/family counts, unknown member = KeyError, **append-only pinned
structurally** (class-surface sweep: no delete/update/remove/…-shaped method; dunders
excluded — py3.13 dataclasses mint `__replace__`, a new-instance constructor, not a
row path), no-provenance-parameter sweep, open-helper path. Falsifier considered: an
API path that removes/mutates an archived row — none exists to call (swept), and a
second identical archive leaves count at 1. Ruff clean, argless mypy 69 (337 files),
fast suite 847 passed.

**finding-0047 FILED (spec-fidelity, route builder, resolved in-plan):** Q3's caller
inventory missed `tests/unit/test_code_projection.py:111` (`is_projected(sha)`
one-arg); write_scope omits that file. Resolution: `is_projected` alone gets
`interpreter: str | None = None` (None = ANY interpreter — the exact semantic that
call site asserts); `add_batch`/`mark_projected` keep the §6(c) pin verbatim. Hazard
guarded by Item 4's bump→re-projects test. Orchestrator may restore the pin at merge
per the finding's re-entry note.

**Item 3 CLOSED** (commit `33d4dc9`): store per §6(c,d,e) + §4 reconciliations
(mark_projected comment now describes mechanics; module docstring gained the
ledger-half cross-ref; boundary header updated). Acceptance runs: (i) same-version
re-add `(0,0)`, count unchanged; (ii) bump → `(0,1)`, current row 2.0.0, history
count 1, `chain_for` = [(1.0.0, v1), (2.0.0, v2)] oldest→current; (iii) history=None
superseding write raises `MissingHistoryError`, standing row untouched; (iv) pre-B-a
fixture heals (rows/marks preserved, interpreter backfilled 1.0.0, marks readable
version-keyed) AND half-migrated fixture (leftover `projections_v2` + old table)
heals with re-open idempotent (marks==1, no dupes); (v) **live-copy migration**:
backup-API copy of MAIN checkout's store (read-only URI open, only to copy) →
PRE rows=259813 marks=85, POST rows=259813 marks=85, payload spot-check verbatim,
all interpreters 1.0.0, re-open idempotent — no row lost/altered, no stop condition.
Falsifier (B-a, inverted) pinned by test: bumped re-projection neither mutates
in place (old generation archived, readable) nor is ignored (new reading lands).
Sensor call sites updated mechanically (interpreter kwarg + 3-arg mark;
`is_projected` version pass-through deliberately left to Item 4); ratchet re-pinned
`f1eff4bf…` at 1.0.0 = declared refactor (batch content byte-identical). All 46
affected-suite tests green incl. untouched out-of-scope `test_code_projection.py`
(finding-0047 resolution holding). Ruff clean; argless mypy 69 (337 files); fast
suite 852 passed.

**Item 4 CLOSED** (commit `f087695`): sensor holds the history handle (7th, wired in
`build_code_sensor`); `_project` and `backfill_observations` are version-keyed
end-to-end; `_RESET_GUARD` gained exactly `"observation_history.sqlite"` + its
split-naming comment — launcher diff audited: the one granted line, nothing else
(no stop condition). Acceptance test (falsifier inverted): monkeypatch-bump 2.0.0 →
`sync().projected == 0` (Q5 invariant: newly-ingested only) then
`backfill_observations() == 2` (NOT zero — the version key is live), `obs.count()`
unchanged (latest-per-identity), all rows 2.0.0, `hist.count("code") == 6` (every
generation archived), both worldviews' marks readable, `chain_for` = [1.0.0, 2.0.0],
re-run idempotent; `reset_targets()` lists `code_observations.sqlite` and excludes
the sidecar which sits in `_RESET_GUARD` (first test pin of the guard). Attestation
shape untouched (§6(g)). Ratchet re-pinned `8832e5b3…` at 1.0.0 (declared refactor —
batch content byte-identical). Ruff clean; argless mypy 69 (337 files); fast suite
854 passed. Affected suites 48 passed incl. untouched `test_code_projection.py`.

**GATE RUN (verbatim, journaled tails):**
1. `uv run ruff check .` → `All checks passed!`
2. `uv run mypy core agents eval ops scheduler scripts` → `Success: no issues found
   in 169 source files`
3. `uv run mypy` (argless) → **`Found 69 errors in 20 files (checked 337 source
   files)`** — equals the pinned baseline exactly (69; file count 334→337 = the three
   new files, zero new errors). NOTE: at the pinned baseline this step exits 1, so the
   verbatim `&&` chain can never reach steps 4–5 — the check is tail EQUALITY; steps
   4–5 were run immediately after, same env, no intervening edits.
4. `uv run python -m ops.type_gate` → `Tier-2 membership: OK` + `Bare-ignore scan: OK`
5. `uv run pytest -q` (full) → `2 failed, 867 passed, 8 skipped in 569.72s`. The two:
   `test_scheduler_live.py::test_supervisor_dispatches_a_real_job` (the documented
   finding-0046 flake) and `test_dream_v2_live.py::test_dream_v2_synthesizes_
   grounded_themes_live` (Ollama `/api/embed` HTTP death under full-suite load —
   diff-unrelated; dream/embed path untouched, stratum has no consumer). **Re-run of
   both in isolation: `2 passed in 437.81s`** — green, journaled per the gate rule.
   finding-0048 filed (discovery/codebase, route builder, resolved): second member of
   the finding-0046 live-contention class; recommends folding into the known-flake
   note. Gate: GREEN with the documented re-run.

**Session seal state:** Items 1–4 all closed; findings 0047 (spec-fidelity, resolved
in-plan) + 0048 (discovery, resolved by evidence); plan stays `in-progress` — the
orchestrator scrutinizes, merges, seals. Branch `worktree-agent-aba2c7c44a097ec42`,
tree clean at write time; commits: f8a2f95 (I1), e4bf8a6 (I2), 37d3d63 (docs),
33d4dc9 (I3), 40695e7 (docs), f087695 (I4), 627bdca (docs), + this entry's commit.
Fresh-agent test: plan + this journal + write-scope files suffice — nothing mid-motion,
no open questions, no parked criteria.

**Context-manifest delta:** read beyond the manifest: `tests/unit/test_code_projection.py`
(the finding-0047 caller), `tests/unit/test_reference_extraction.py` (constructor-only
consumer, stayed green untouched), `ops/type_gate.py` + `pyproject.toml` mypy config
(baseline mechanics), `ops/lifecycle/launcher.py:243-268` (Launcher dataclass shape for
the stub-cfg reset test), `docs/templates/finding.md`. Proved irrelevant: none.

## 2026-07-12 — minted at graduation (orchestrator, Fable/xhigh)

Plan created `proposed` by /graduate over the ratified `dn-self-sensing` (B-a; V2's
version-identity design; the owner's ledger-class reset ruling pinned as the
sidecar-file mechanism, §11). Grounding verified in-session: the degenerate
`is_projected(sha)` no-op path (`ops/code_sensor.py:207-208`), the promise-comment at
`code_observations.py:205-207`, `_RESET_GUARD` at `launcher.py:77-78`, sole-caller
check (Q3). No code written. Awaiting the owner's `proposed → ready` hand edit.

---

## 2026-07-12 — ORCHESTRATOR: main merged in, scrutiny PASS, gate re-run in flight

**Status:** builder reported complete (8 commits, head `d313cef`); orchestrator
supervision underway in this worktree.

- **`git merge main` clean (`3445172`)** — main had moved 78deaf6→9e2c5c5 after spawn
  (triage sweep, oq-0017 enactment, bp-021 merge+seal, spawn amendments, finding-0051);
  zero file overlap with this plan's diff; plan.md front-matter line-merged cleanly
  (main's parallelizable_with amendment + branch's status flip, different lines).
- **Scrutiny (full diff vs `78deaf6`): PASS.**
  - Launcher audit: `_RESET_GUARD` gains EXACTLY one tuple entry + its comment —
    the oq-0013-precedent grant honored to the letter.
  - §6(d,e) migrations: healing-on-open via PRAGMA column checks; copy-rename in one
    transaction; leftover `projections_v2` dropped and redone — idempotent in both
    crash windows. Archive-BEFORE-replace ordering means a crash between the two can
    only duplicate an archive attempt (INSERT OR IGNORE absorbs), never lose a
    generation (the two stores commit on separate connections; verified the ordering).
  - §6(c) add_batch: all three cases exact; MissingHistoryError on history=None
    supersede; main table latest-per-identity by construction; default reads untouched.
  - §6(b) sidecar: append-only STRUCTURAL (no delete/update surface, test-swept);
    pinned archive() tuple shape exact; IDENTITY_KEYS registry is a light, documented
    coupling (key columns only — honest adaptation, bp-019 registers 'agent').
  - §6(a,g): INTERPRETER_VERSION + ratchet comment verbatim; attestation emission
    shape unchanged; sync() newly-ingested-only preserved (Q5).
  - **finding-0047 deviation ACCEPTED at scrutiny:** `is_projected`'s
    `interpreter: str | None = None` (None = any generation) — the semantics the
    out-of-scope caller (tests/unit/test_code_projection.py:111) actually asserts;
    the forgotten-arg hazard is pinned by Item 4's bump→re-projects test. Restoring
    the §6(c) pin verbatim would require an out-of-scope test edit at merge for zero
    semantic gain. finding-0048 (second live-flake class member) noted for /triage
    fold into the 0046 known-flake note.
  - Scope: 12 files, all in write_scope; no secrets; plan.md diff = status flip only.
- **Gate re-run (orchestrator, post-merge):** ruff clean · mypy scoped clean (170
  files) · **argless mypy = 69 = baseline** (339 source files) · type_gate OK ·
  pytest leg IN FLIGHT (background br7kijy0m; contending with bp-022's gate suite —
  0046/0048 flake classes may need the isolation re-run).

**Next action:** on pytest green (with any flake re-runs journaled) — merge to main
(watch the post-commit hook's sensor sync exercise the LIVE store migration), push,
witness `check` on the merge sha, seal (cost.actual: fable ~194,279 tok / 104 calls /
~44 min = 0.78× of 250k), then spawn bp-019.

**Gate pytest leg CLOSED (orchestrator, 2026-07-12):** post-merge full suite 908 passed /
8 skipped / 3 failed — all three live-e2e (scheduler = finding-0046, research_live +
semantic_search_live same load class; the run overlapped bp-022's gate suite 18 min).
Re-runs: semantic_search green in the first partial re-run; scheduler + research_live
**2 passed in 126 s truly uncontended** (verified zero pytest processes machine-wide
first). Five-part gate GREEN in full. Merging to main.
