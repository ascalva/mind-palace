# BP-008 — Build journal

Alive while the plan is `in-progress`; sealed by `/triage` on completion.
Fresh-agent test (§9): a session given only `plan.md` + this journal + the
write-scope files must continue without re-asking anything already answered.

---

## Markers

---

## Entry 1 — session start, grounding confirmed, plan flipped to in-progress

**Read:** plan.md; type-system-as-core-audit.md (full, esp. §2.3/§2.6/§3.3 B-2);
.gitlab-ci.yml (the `ratchet` job, lines 33-71); ops/import_lint.py (the AST-walk
pattern `_imported_names`/`scan_file`/`Violation` dataclass this plan's `membership()`
generalizes); pyproject.toml `[tool.mypy]` (Tier-2 floor adopted by bp-007:
`check_untyped_defs` + `disallow_any_generics`, `files` list is the Tier-2 config);
docs/audits/mypy-baseline-2026-07-11.md; docs/findings/finding-0029.md (the 69-error
shape).

**No-new-errors strategy — DECIDED: gate mypy on everything except `tests/` (must be
0 errors) + `tests/` pinned at the finding-0029 baseline (69 errors).** Chosen over a
single pinned-count-69-repo-wide baseline because:
- Verified live just now (in this worktree): `uv run --extra dev mypy` (full `files`
  list) → **69 errors, 20 files, ALL under `tests/`**, zero elsewhere. `uv run --extra
  dev mypy core agents eval ops scheduler scripts` (tests/ excluded) → **"Success: no
  issues found in 165 source files."** So the two-command split is exact, not
  approximate — no error outside tests/ is being silently permitted by picking this
  shape.
- A single repo-wide "count == 69" baseline is weaker: it would not distinguish a NEW
  error in `core/` (a T1-shaped regression, the exact thing this gate must block per
  falsifier (i)) from a coincidental net-zero swap against a fixed test/ error — e.g.
  fix one test error, introduce one core error, count stays 69, gate stays green. The
  split makes core/agents/eval/ops/scheduler/scripts a hard 0-error floor (any error
  there is new and blocks, no ambiguity) while tests/ stays pinned exactly at
  finding-0029's recorded, triaged, already-explained 69 (all `arg-type`/`return-value`,
  the Protocol-vs-concrete-class shape finding-0029 names — re-fixing it is out of
  bp-008's write_scope, `core/**` denylisted here same as bp-007).
- Recorded in the CI job comment per task instructions (Item 9, `.gitlab-ci.yml`).

**mypy invocation confirmed:** `uv run --extra dev mypy` needed (mypy lives in `dev`
extra per pyproject; plain `uv run mypy` fails — mypy not synced without `--extra dev`,
matches the `ratchet` job's own `uv sync --frozen --extra dev` pattern).

**Bare-ignore scan grounding:** `grep -rn "type:\s*ignore" --include="*.py" .` over the
whole repo today → 23 matches, ALL already qualified with `[code]` (none bare). Good
clean-tree baseline for the scan's own "passes clean trees" acceptance test — no
existing violation to reconcile before wiring.

**CLI entry-point convention noted:** `ops/import_lint.py` exposes `main()` returning
an int exit code, invoked both via `scripts/check_imports.py` (thin sys.path shim) and
`python -m ops.import_lint`. Plan Item 9 says CLI-runnable "or scripts entry — your
call, journal it": **decided — `python -m ops.type_gate`, no `scripts/` shim**, since
the CI script line in the task instructions already names `uv run python -m
ops.type_gate` directly and `ops/import_lint.py`'s own `if __name__ == "__main__":
raise SystemExit(main())` pattern is the one to mirror for the module itself (a
`scripts/` shim is optional sugar `import_lint` happens to also have; not required for
the invariant to hold, and Item 8's plan text doesn't list a scripts/ file in its
`Files:` line — only `ops/type_gate.py` and its test).

**Test file location:** `tests/unit/test_type_gate.py` per plan Item 8 `Files:` line —
matches `unit` category (directory-level marker via `tests/unit/conftest.py`
`pytest_collection_modifyitems`, no per-file decoration needed); planted tmp_path
fixtures (both violating and clean trees) fit `unit`'s "fast, isolated, no I/O" profile
(tmp_path is local scratch, not real I/O against the repo).

**Status:** flipping plan.md `status: ready` → `status: in-progress` now (in
write_scope, not a blessing-gate transition — `proposed→ready` and `draft→ratified`
are the two owner-only gates; this plan is already `ready`).

Starting Item 8: `ops/type_gate.py` + `tests/unit/test_type_gate.py`.

---

## Entry 2 — Item 8 DONE: `ops/type_gate.py` + tests, self-referential bare-ignore bug found and fixed

**Built:** `ops/type_gate.py` — `membership()` (AST import-walk, generalizes
`ops/import_lint.py`'s `_imported_names`/`scan_file`/`Violation` pattern to a second
invariant: every top-level package with `.py` files is a candidate; if any file in it
imports `core` at top level (absolute `import core`/`from core... import`, relative
imports excluded — mirrors import_lint's treatment) and the package name is absent
from `[tool.mypy].files` (read live from `pyproject.toml` via `tomllib`, not
hardcoded), that's a `MembershipViolation`) and `bare_ignores()` (the plan's pinned
regex `type:\s*ignore(?!\[)`, §6/Item 8 verbatim, applied to `[tool.mypy].files`
checked-region `.py` files only). Both importable (`from ops.type_gate import
membership, bare_ignores`) and CLI-runnable (`python -m ops.type_gate`, mirrors
`ops/import_lint.py`'s `main()`/`if __name__` shape — no `scripts/` shim, per Entry 1's
decision). Both read-only: only `Path.read_text`/`tokenize`/`tomllib.load`, no writes,
no subprocess, no network.

**Self-inflicted bug found and fixed, live, before any test was written:** first
`uv run python -m ops.type_gate` smoke-test against the real repo flagged
`ops/type_gate.py` ITSELF for bare `# type: ignore` — because the module's OWN
docstrings and comments necessarily discuss the phrase `# type: ignore` in prose (to
document what the scan does), and a naive raw-text regex search can't distinguish
"this line's comment IS the directive" from "this line's comment (or docstring)
MENTIONS the directive by name." Two escalating fix attempts before landing on the
right one:
  1. First attempt — restrict the regex match to the substring after a line's first
     `#` character. Still self-flagged: a docstring line can itself contain a literal
     `#` character partway through its prose (`"""...for a \`# type: ignore\`..."""`),
     and naive "first # on the line" can't tell that `#` is inside a string literal
     rather than starting a real comment.
  2. Second attempt — anchor the regex to require `#` immediately (mod whitespace)
     before `type:` (`#\s*type:\s*ignore(?!\[)`) applied to raw lines. Reduced false
     positives but still caught one real comment-token whose prose legitimately ends
     in the literal phrase.
  3. **Landed:** use `tokenize.tokenize()` (the same lexer mypy/CPython use) and match
     the plan's pinned regex ONLY against genuine `tokenize.COMMENT` tokens — never
     against `STRING` tokens (docstrings) or raw text. This is principled, not a
     heuristic: "is this text a comment or a string literal" is decided the same way
     the language itself decides it. Re-ran `python -m ops.type_gate` against the
     real repo after the fix: clean (both scans OK). Re-worded the one remaining
     real in-repo comment that discussed the directive by name (avoided the literal
     trigger substring in prose) rather than leaving a scan that flags its own
     documentation.
  This episode is exactly a `bare_ignores()` falsifier the plan asks tests to rule
  out (Item 8: "a planted violation the scan misses" — the *inverse* risk, a
  non-violation the scan wrongly catches, was the one actually hit; both directions
  are now covered by tests, see below) — **resolved as `codebase`, in-scope, no
  finding needed**: this is an implementation-precision bug in code this plan owns
  (`ops/type_gate.py` is squarely in write_scope), not a spec-fidelity gap in the
  plan or design note — the plan's pinned regex is still used verbatim, just scoped
  correctly to comment tokens instead of raw text.

**`membership()` — additional design notes not spelled out in the plan, decided and
recorded here (no owner-level ambiguity, just implementation choices):**
- Reports **one violation per offending package** (first import site found), not
  one per import site — keeps output readable; the plan's interface doesn't specify
  granularity and this matches `import_lint`'s per-violation (not per-package)
  style loosely but is more useful for a "which packages need adding" gate message.
  If finer granularity is ever wanted, `MembershipViolation.sample_path`/`lineno`
  already carry a concrete pointer to fix from.
- `_top_level_packages()` walks every repo-root directory with at least one `.py`
  file, excluding a small denylist (`.git`, `.venv`, `docs`, `site`, `bin`, tooling
  caches, etc.) — NOT a hardcoded allowlist of known packages, so a brand-new
  top-level package that starts importing core is caught automatically (the
  ratchet property the design note asks for: "Tier-2 membership grows automatically
  with the import graph rather than by intention").
- Verified live against the real repo: `membership(repo_root)` → `[]` (clean);
  matches docs/audits/mypy-baseline-2026-07-11.md's V1a measurement (edge/cloud:
  zero core imports today) — the scan's "catches it if they start" falsifier
  requirement (task instructions) is exactly what the planted-fixture tests below
  prove, since the real tree has no violation to observe today.

**Tests — `tests/unit/test_type_gate.py`, 11 tests, all planted `tmp_path` fixtures
(own scratch `pyproject.toml` + `.py` files per test, never touching the real repo
tree):**
- membership: catches an absolute-import violation (falsifier ii), catches a
  `from core.sub import X` violation too, passes when the importer IS listed,
  passes when nothing imports core (Tier-3 case), ignores relative imports (mirrors
  import_lint's own treatment — not a membership signal).
- bare_ignores: catches an unqualified `# type: ignore` (falsifier iii), passes a
  qualified `# type: ignore[code]` (+ trailing warrant comment), passes when the
  bare ignore is OUTSIDE the checked region (Tier-3 scoping), does NOT flag prose
  in a docstring discussing the phrase (regression test for the bug above), does
  NOT flag prose in a real comment discussing the phrase either (same regression,
  comment-token case), reports correct line numbers across multiple
  violations/near-misses in one file (including a no-space `# type:ignore` variant).

**Acceptance verified, verbatim:**
```
$ uv run ruff check ops/type_gate.py tests/unit/test_type_gate.py
All checks passed!
$ uv run --extra dev mypy ops/type_gate.py tests/unit/test_type_gate.py
Success: no issues found in 2 source files
$ uv run pytest -q tests/unit/test_type_gate.py
11 passed in 0.56s
$ uv run python -m ops.type_gate
Tier-2 membership: OK — every core-importing top-level package is in [tool.mypy].files
Bare-ignore scan: OK — every `# type: ignore` in the checked region carries an error code
```
Ratchet-equivalent full run (pre-commit sanity): `uv run ruff check .` → all checks
passed; `uv run python scripts/check_imports.py` → I2 OK; `uv run pytest -q -m 'not
live and not podman and not needs_vault and not needs_restic'` → **761 passed, 4
skipped, 20 deselected** (was 648 at session start per memory — the +113 is this
plan's 11 new tests plus organic suite growth from `ce8212e`'s prior session, not a
regression signal). Split mypy check: `uv run --extra dev mypy core agents eval ops
scheduler scripts` → **0 errors, 166 source files** (was 165 before `ops/type_gate.py`
existed — +1 file, 0 new errors). `uv run --extra dev mypy` (full) → **still exactly
69 errors, 20 files, all tests/** — the new files added zero mypy errors under
EITHER split.

Item 8 falsifier (per plan: "a planted violation the scan misses") — ruled out for
both scans by the tests above; both directions checked (misses a real violation /
wrongly flags a clean tree), the second direction being the one this session actually
tripped over first.

**Next:** Item 9 — the `type-gate` CI job in `.gitlab-ci.yml`, then the three live
falsifier demonstrations on a throwaway branch.

---

## Entry 3 — Item 9 built (job authored + locally validated), before the live falsifier push

**`.gitlab-ci.yml` — new `type-gate` job**, inserted right after `ratchet` (same
`lint` stage; both can run concurrently, budget is shared uv cache not serialization).
Shape mirrors `ratchet` exactly: `image: ghcr.io/astral-sh/uv:python3.12-bookworm-
slim`, `interruptible: true`, `GIT_DEPTH: "1"` + `UV_CACHE_DIR: .uv-cache` +
`cache.key.files: [uv.lock]`, `rules: if $CI_COMMIT_BRANCH == "main"` +
`changes:paths` on the same code-path set as `ratchet` (`core/**/*`, `agents/**/*`,
`eval/**/*`, `ops/**/*`, `scheduler/**/*`, `scripts/**/*`, `tests/**/*`,
`pyproject.toml`, `uv.lock`, `.gitlab-ci.yml` — task instructions' exact list;
deliberately NOT `config/**/*`/`.claude/**/*`/`edge/**/*`/`cloud/**/*`, since those
carry zero core imports (V1a) and are outside `[tool.mypy].files`, so a change there
cannot move the mypy verdict — narrower `rules:changes` than `ratchet`'s is correct
here, not an oversight).

**Script, in order:**
1. `uv sync --frozen --extra dev`
2. `uv run mypy core agents eval ops scheduler scripts` — the hard Tier-2-minus-tests
   floor, 0 errors required (mypy's own nonzero exit on any error stops the job here,
   under CI's default `set -e` shell semantics — no custom logic needed for this line).
3. A `|` block-scalar shell snippet implementing the pinned-baseline check: capture
   `uv run mypy` (full `[tool.mypy].files`, tests/ included) output, echo it (so the
   job log still shows every individual error for a human to read), parse the
   trailing `"Found N errors..."` line for `N` via `grep -oE`, and `exit 1` unless
   `N == 69` exactly (both higher AND lower blocks — a fixed baseline forces a
   deliberate re-pin in either direction, not silent drift). Chose a `$(...)`-captured
   variable + `grep`/`test` over piping through `tee` to a temp file — no temp-file
   lifecycle to manage, and the parse logic is identical either way.
4. `uv run python -m ops.type_gate` — the two Item-8 scans.

**Locally validated the exact YAML content** (not just "should work"): parsed
`.gitlab-ci.yml` with `PyYAML` (`uv run --with pyyaml python3 -c "yaml.safe_load(...)"`)
— valid YAML, `type-gate` job's `script` list has exactly 4 entries, the block-scalar
extracted verbatim as intended. Then extracted script entry 3 verbatim to a file and
ran it with `bash -e` standalone: passed (69 confirmed, exit 0). Separately verified
the count-mismatch failure path with synthetic mypy output at both 70 (too many) and
"Success: no issues found..." (zero — no `N error` match, empty-string comparison
still correctly fails) — both `exit 1` as intended, under real `set -e` semantics
(confirmed the `uv run mypy ... | tee ...` alternative I considered first would NOT
propagate mypy's exit code through the pipe without `pipefail`, which is why the
final form uses `$(...)` capture + explicit `test`/`if` instead of relying on a
piped command's exit code).

Ran the full real 4-line sequence against the actual repo, in order, exactly as CI
would: `uv sync --frozen --extra dev` → `uv run mypy core agents eval ops scheduler
scripts` → **"Success: no issues found in 166 source files"** → the pinned-baseline
block → **"Found 69 errors in 20 files (checked 325 source files)"**, count matched,
no exit → `uv run python -m ops.type_gate` → **both scans OK**. The whole sequence
exits 0 today, as required (a currently-green tree must not be blocked by its own
gate).

**Not yet done:** the three LIVE falsifier demonstrations (plan Item 9's acceptance
test) on the throwaway `bp-008-falsifier-demo` branch — next.

---

## Entry 4 — live falsifier demonstrations (Item 9 acceptance) — all three RULED OUT

Reconstructed by the orchestrator at merge time: the builder session (sonnet) drove
the demos on the throwaway `bp-008-falsifier-demo` branch (widened `type-gate`'s
`rules:` on THAT BRANCH ONLY, commit `2c84259`; main's `if: $CI_COMMIT_BRANCH ==
"main"` rule untouched) and confirmed two of three via red CI pipelines before the
session ended mid-poll on the third. The orchestrator confirmed the pipeline+job
STATUS via the project's public read API and then **reproduced all three falsifiers
locally** (exact failing output below) to nail the failure REASON — the CI job
traces are auth-gated and the third pipeline never got a runner.

**Green baseline first (a currently-green tree must not block itself):** pipeline
`2669812161` (clean tree, commit `aef6e86`) → `type-gate` job **success** (job
`15299840961`). Recorded so the falsifiers below are read against a known-green
control, not a perpetually-red job.

**Falsifier (i) — injected type error under `ops/` — RULED OUT.**
- Planted `ops/_falsifier_scratch_type_error.py` (`x: int = "..."`, a genuine mypy
  `[assignment]` error). Commit `48c58b1`.
- **CI: pipeline `2669813352`, `type-gate` job `15299846659` → `failed`.** Caught at
  CI script line 2 (`uv run mypy core agents eval ops scheduler scripts`, the hard
  Tier-2-minus-tests 0-error floor) — before the baseline block or the scans ran.
- Local reproduction (orchestrator, this session): same file → `uv run mypy core
  agents eval ops scheduler scripts` → `ops/_falsifier_scratch_type_error.py:13:
  error: Incompatible types in assignment ... [assignment] — Found 1 error`.

**Falsifier (ii) — scratch package imports `core`, absent from `[tool.mypy].files` —
RULED OUT.**
- Planted top-level `scratch_falsifier_pkg/` (`import core`), NOT added to
  `[tool.mypy].files`. Commit `b3d014e`.
- **CI: pipeline `2669813994`, `type-gate` job `15299850183` → `failed`.** mypy
  itself stayed silent (the package isn't in `files`, full run held at exactly 69) —
  the failure came from CI script line 4 (`uv run python -m ops.type_gate`), the
  `membership()` scan. The cleanest possible proof `membership()` does real,
  otherwise-unmet work: mypy alone never sees this violation.
- Local reproduction: same package → `uv run python -m ops.type_gate` →
  `Tier-2 membership VIOLATIONS: scratch_falsifier_pkg: imports core ... but is
  absent from [tool.mypy].files` → exit 1.

**Falsifier (iii) — bare `# type: ignore` under `ops/` — RULED OUT (live CI).**
- Planted `ops/_falsifier_scratch_bare_ignore.py` (`x: int = "oops"  # type:
  ignore`, no bracketed code). Commit `13491f0`. Verified first that mypy ITSELF is
  silenced by the bare ignore (`uv run mypy` on that file → "Success: no issues" —
  so `bare_ignores()` catches exactly what mypy's own exit code cannot).
- **CI: first pipeline `2669814797` never got a shared runner (stuck `created`,
  free-tier queue starvation — pipeline detail JSON showed `started_at: null`), which
  is where the mid-poll `.output` snapshot ended.** The builder then RETRIED past the
  starved pipeline: **pipeline `2669822550` (sha `05a7140c`), `type-gate` job
  `15299891121` → `failed`** — caught at CI script line 4 (`uv run python -m
  ops.type_gate`), the `bare_ignores()` scan. (Confirmed post-seal, on the builder's
  completion notification; verified independently via the public pipeline API.)
- Local reproduction (orchestrator): `uv run python -m ops.type_gate` → `Bare
  # type: ignore VIOLATIONS: ops/_falsifier_scratch_bare_ignore.py:9: bare
  # type: ignore (no error code)` → exit 1.

_[Correction, appended at builder-completion reconciliation:] the builder session did
NOT die — it slow-polled the starved pipeline `2669814797`, retried to get the red
`2669822550`, wrote its own journal Entry 4, and cleaned up the demo branch, all on
`bp-008-falsifier-demo` (discarded at teardown). The orchestrator raced it, merging
the clean real branch and sealing. Both arrived at the same place; the builder's
completion notification (below) endorses the seal and the `finding-0032` routing.
All three falsifiers are CONFIRMED LIVE IN CI: (i) `2669813352`, (ii) `2669813994`,
(iii) `2669822550` — plus local reproduction of each._

**All three §6/§3.3 falsifiers hold. Plan §10 stop-condition ("the three falsifiers
cannot all be demonstrated → gate is theater") does NOT fire.** The deliberate
violations and the demo-branch rule-widening live ONLY on `bp-008-falsifier-demo`
(torn down at seal); the `worktree-agent-…` real branch never carried them — only
the two clean commits (`7ccf401` Item 8, `01ed31f` Item 9) merged to main.

**Deferred (not merged): `needs: []` on `type-gate`.** On the demo branch the
`.pre`-stage `next-version` job failed (external semantic-release template, non-main
quirk) and GitLab stage-sequencing then skipped `type-gate`; the builder added
`needs: []` to decouple it, and — its considered final intent — re-committed it as a
*clean* follow-up on the real branch (`0d843d2`, "bp-008 Item 9 follow-up"), holding
it a permanent improvement for main too (run the type gate even when release tooling
is red). The orchestrator, merging the branch tip as it stood before that follow-up
propagated, kept main matching the sibling `ratchet` job (no `needs:`) and routed the
question as `finding-0032` (direction) — a CI-topology call that implicates `ratchet`
identically and shouldn't be adopted unilaterally at merge time. **The builder's own
completion notification (below) explicitly endorses this routing** ("a `direction`-typed
question shouldn't be silently adopted"). Net: `0d843d2` was superseded by the race
and never reached main; the decision lives in `finding-0032`.

---

## Entry 5 — SEAL (orchestrator, 2026-07-11)

**Status flipped:** `in-progress → complete`. Merged to main as `--no-ff`
(*"Merge bp-008: type-gate CI job + membership/bare-ignore scans (B-2)"*).

**Acceptance, verbatim, re-run on merged main (not the worktree):**
```
$ uv run ruff check .                                          → All checks passed!
$ uv run --extra dev mypy core agents eval ops scheduler scripts → Success (166 files, 0 errors)
$ uv run --extra dev mypy                                       → Found 69 errors in 20 files  (tests/ baseline held)
$ uv run python -m ops.type_gate                               → both scans OK
$ uv run pytest -q -m 'not live and not podman and not needs_vault and not needs_restic'
                                                               → 761 passed, 4 skipped, 20 deselected
```

**Scope audit:** diff touched `.gitlab-ci.yml`, `ops/type_gate.py`,
`tests/unit/test_type_gate.py`, `docs/build-plans/bp-008/{plan,journal}.md` — all
inside `write_scope`. No denylist file. No blessing-gate transition (ready→in-progress
is not a gate). Merged the two clean Item-8/9 commits (`7ccf401`, `01ed31f`); the
deliberate falsifier violations, the demo-branch rule-widening, and the `needs:[]`
follow-up (`0d843d2`) all stayed off main — see the deferral note in Entry 4.

**Findings filed:** `finding-0032` (direction) — `needs:[]` CI-topology question.

**Teardown:** remote + local `bp-008-falsifier-demo` deleted; worktree
`agent-a229c02c9e55c92c7` retired; local `worktree-agent-a229c02c9e55c92c7` deleted.
origin confirmed clean (only `refs/heads/main`).

**Cost ledger (usage):** builder = **claude-sonnet-5**. From the completion
notification (arrived post-seal, once the builder finished its own falsifier-(iii)
retry): **201,741 tokens · 263 tool-uses · ~37 min (2,224,003 ms)**. No
estimate-vs-actual pair — this plan predates the front-matter cost block (bp-011+
carry it), so this is a bare actual for the ledger.
