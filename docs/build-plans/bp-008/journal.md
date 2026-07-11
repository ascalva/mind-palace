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
