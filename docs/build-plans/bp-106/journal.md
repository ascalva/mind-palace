# Journal — bp-106 (the boundary shim is real: quarantine psutil, make the one-file rule enforceable)

Worktree builder, branched from `origin/main` @ **`c78bca1`** (`bless(bp-116, bp-117, bp-118,
bp-119): proposed → ready`). Branch `worktree-agent-a5fe8978f35262932`. Contract: **builder**.

---

## Checkpoint 0 — ⚑ THE TARGET MOVED: the plan describes a two-accessor probe that is now three

Read the §2 manifest in order (all ten entries; refs below are what they actually say, not what the
plan predicted). One thing dominates everything that follows:

**bp-106 was authored 2026-07-25. `e49a715` (`build(bp-121): D2 probes the executed interpreter,
not the argv0 name`, TODAY) rewrote the very function this plan moves.** Two consequences the plan
cannot know:

1. `_process_identity` reads **THREE** psutil accessors, not two: `create_time()`, **`exe()`** and
   `name()`. §6's pinned interface (two functions, `process_create_time` + `process_name`) and §9's
   non-goal ("no widening beyond **the two** accessors") are both stale by exactly one accessor.
   Resolved as a [banner: correction], not a silent rewrite — see Checkpoint 1.
2. That commit ALSO added a raw `psutil` import to `tests/unit/test_restart_trustworthy.py:21`,
   which makes §3 Q3's census ("**Two**, and only two" violations) wrong. That is a §10 STOP
   condition and it is the substance of Checkpoint 3.

### Read-map (what each manifest entry actually establishes)

| Entry | Anchor | What it settles |
|---|---|---|
| finding-0198 | `docs/findings/finding-0198.md:71-81` | the OPEN hand-off; "a mechanical move, one plan, no behaviour change" |
| psutil shim | `core/typedshims/psutil.py:1-45` (pre-edit) | destination + the `loadavg_1m` Optional idiom that §3 Q5 cites as precedent |
| lancedb shim | `core/typedshims/lancedb.py:112-186` | the adapter precedent; "spell every method out rather than forwarding through `__getattr__`" |
| lancedb shim test | `tests/unit/test_typedshim_lancedb.py:170-210` | the "HONEST, not a laundering proxy" framing + the `__getattr__`/`compact_files` falsifier shape |
| launcher | `ops/lifecycle/launcher.py:127-249` | `_pid_alive`, `_CLOCK_SLACK_S=5.0`, `_process_identity` (**three** accessors), `_supervisor_alive` D1/D2 |
| type_gate | `ops/type_gate.py` (231 lines) | `_EXCLUDED_DIRS`, `_imported_roots`, `_checked_region_files`, two `*Violation` dataclasses, `main()`'s print-then-`0/1` |
| design note §2.5 | `docs/design-notes/type-system-as-core-audit.md:190-194` | boundary wrappers; candidates `duckdb`/`lancedb`/`scikit-network`/`psutil` |
| pyproject | `pyproject.toml:149-157` | shimmed = lancedb/sknetwork/psutil; `watchdog`+`hvac` keep `ignore_missing_imports`; **duckdb absent → §3 Q2 confirmed** |
| test_code_corpus | `tests/unit/test_code_corpus.py:274-292` | the legitimate exemption: `raw.create_table(TABLE, data=legacy)` builds a pre-bp-099 no-`current` table the shim cannot model |
| bp-105 journal | Checkpoints 1–2 | why D1 and D2 both exist; D2 is load-bearing because D1 is silent on a pid recycled onto a long-lived process |

Two extra facts measured, not assumed:

- **`[tool.mypy].files` = `["core", "agents", "config", "eval", "ops", "scheduler", "scripts",
  "tests"]`** (`pyproject.toml:160`). `tests` IS in the checked region — so §11's "tests in scope:
  Yes" is not merely a preference, it is what the checked region already means here. This closes off
  "scope the new scan to the checked region" as an escape from Checkpoint 3's conflict.
- **CI already runs the gate**: `.github/workflows/ci.yml:80` and `.gitlab-ci.yml:128` both invoke
  `uv run python -m ops.type_gate`. §7 Item 4's "verify, do not edit" — verified, not edited.

---

## Checkpoint 1 — Items 1 + 2 DONE: the move is proven behaviour-identical over 151 shapes

### Item 1 — `core/typedshims/psutil.py` grows **three** accessors

`process_create_time`, `process_exe_name`, `process_name`. Each reads one accessor, each absorbs
every failure as `None` per §3 Q5, each carries the `# noqa: BLE001` warrant §6 asks for.

**[banner: correction] on §6 and §9 — three, not two.** §9's non-goal is *"no widening of the psutil
shim beyond the two accessors"*, whose intent is plainly "do not bolt on extras beyond what the
launcher reads" (it names the four it means to protect: `cpu_percent`, `loadavg_1m`,
`virtual_memory`, `process_rss`). The launcher reads three raw accessors as of `e49a715`, so three
move. Nothing beyond the moved set was added. The plan's *intent* is honored exactly; its *count* is
a pre-bp-121 artefact.

Two semantics that are easy to "tidy" into a bug, so both are pinned in docstrings:

- `process_exe_name` folds **empty → None** (`Path(str(exe())).name or None`). psutil returns `''`,
  not an exception, when a process's executable is undeterminable; `''` must reach the launcher's
  fallback, not be taken as an answer.
- `process_name` deliberately does **NOT** fold empty → None. It is the last probe, so `''` there is
  a real answer that D2 reads as "not a Python interpreter". Folding it would convert a disproof
  into ambiguity, and ambiguity REFUSES (finding-0186) — a behaviour change wearing a tidy-up's
  clothes. This asymmetry is inherited verbatim from the pre-move code (`or None` on the exe branch,
  bare `str()` on the name branch) and is the single subtlest thing in the diff.

Also amended the module docstring per §4: the scope is the whole **repo**, not only `core/` (bp-105's
violation was in `ops/`), and the rule was **aspirational until bp-106** — stated as a
`[banner: correction]`, not silently rewritten.

### Item 2 — the launcher composes; `import psutil` is gone from `ops/`

```
$ grep -rn -E '^\s*(import|from)\s+psutil\b' ops/
NONE — quarantine restored
```

`_process_identity` is now four lines of composition. The `exe()`-then-`name()` **order** and the
fallback stayed in the launcher rather than moving into the shim, deliberately: the order is a **D2
policy** decision (which probe answers "is this a Python interpreter?") and belongs beside
`_supervisor_alive`'s reasoning, while the shim states psutil *facts*. Every line of the
finding-0211 warrant survives — restructured into a three-bullet ⚑ block that says, in terms, that
reversing the order re-breaks Linux CI and dropping the fallback re-opens finding-0186's brick trap.
The `(create_time_epoch, interpreter_name)` tuple contract and the "basename of the binary the
process is EXECUTING, deliberately not the process's name" docstring are unchanged.

The one warrant that was DELETED is the right one to delete: bp-105's
`warrant(finding-0198)` paragraph justifying the raw touch. §4 calls for exactly this — *"the
comment must not survive as a fossil justifying a condition that no longer exists."*

### Proof that D1/D2 semantics did not move

Three independent lines of evidence, because "the tests pass" is the weakest of them:

1. **`tests/unit/test_restart_trustworthy.py` → 37 passed, file byte-untouched.** Item 2's stated
   acceptance. `git status` shows no entry for it. Five of the 37 drive the REAL probe against a
   faked `psutil.Process` (`_fake_psutil` patches `Process` on the real psutil module object, so the
   patch lands through the shim's module-attribute lookup exactly as it did through the launcher's).
   §7 Item 2 says "all 24 tests"; bp-121 grew the file to 37. All 37 pass.
2. **A differential run of the pre-move body against the post-move composition over 151 process
   shapes: 0 divergences.** The old body was pasted verbatim from `c78bca1` and both were driven
   over the cross-product of `created ∈ {epoch, 0.0, RAISES}` × `exe ∈ {linux-venv-python,
   macos-framework-Python, /sbin/launchd, "", "/", bare-name, RAISES}` × `name ∈ {pytest, Python,
   python3.13, launchd, systemd, "", RAISES}`, plus constructor-raises, plus the real host at pid 1 /
   self / a dead pid. This covers the four branches no injected-tuple test can reach *and* the two
   platform shapes the host cannot have. Real-host readings after the move:
   `pid 1 -> (1783586210.11, 'launchd')`, self -> `(…, 'python3.13')`, dead -> `(None, None)`.
3. **`_supervisor_alive` was not edited at all** — only its injected default's body moved. Its
   signature (both probes injected, the shape tests depend on), `_CLOCK_SLACK_S = 5.0`, D1's
   `created > opened + _CLOCK_SLACK_S`, and D2's `"python" not in interpreter.lower()` are
   character-identical. `git diff` confirms the hunk boundaries stop above it.

**One consequence recorded, not fixed:** `test_restart_trustworthy.py:237-239`'s docstring now says
*"`_process_identity` imports psutil lazily inside its own body (warrant finding-0198)"*, which after
the move describes the shim rather than the launcher. The mechanism it relies on (attribute lookup at
call time) is unchanged and the test passes; the *prose* is one hop stale. That file is deliberately
out of `write_scope` (§5) and Item 2's acceptance requires it untouched, so this is owed to `/triage`,
not performed here. Filed as part of **finding-0223**.

Gates so far: `ruff` clean on both files; `mypy core ops` → *Success: no issues found in 187 source
files*.

### Mutation testing — the four semantics that must not move, each proven to be GUARDED

"The tests pass" only means something if the tests would fail. Each load-bearing behaviour was
inverted in the source, the two relevant files re-run, then restored (backup outside the repo;
`git diff --stat` identical before and after, and the baseline returns to 54 passed):

| Mutation | Result | Guard that fired |
|---|---|---|
| M1 — drop `or None` from `process_exe_name` (empty exe becomes an answer) | **3 failed** | the empty-exe pins in both files |
| M2 — add `or None` to `process_name` (empty name folded to None) | **1 failed** | `test_an_empty_name_is_preserved_as_empty_NOT_folded_to_None` |
| M3 — REVERSE the order: `name()` first, `exe()` as fallback | **1 failed** | `test_a_console_script_invocation_still_reads_as_a_python_interpreter` — i.e. the Linux-CI regression |
| M4 — DROP the `name()` fallback entirely | **1 failed** | `test_an_unreadable_exe_falls_back_to_the_invocation_name` — i.e. finding-0186's brick trap |

M3 and M4 are the two failure modes the delegation brief singled out, and both are now held by a
test rather than by a comment. M2 is the one that would have looked like a tidy-up.

---

## Checkpoint 2 — Item 3 DONE: the shim is no longer the only untested boundary wrapper (§3 Q6)

`tests/unit/test_typedshim_psutil.py`, **17 tests**, modelled on `test_typedshim_lancedb.py` and
covering everything §7 Item 3 asks: real values for self; `None` (not an exception) for a dead pid;
readability for the **root-owned foreign process** pid 1 (the deployed `ouroboros` case); and the
honesty property — the declared surface is the whole surface, no `__getattr__`, no raw psutil
attribute reachable.

Three deliberate choices worth recording:

- **Item 1's falsifier is parametrized over all three accessors and over BOTH failure modes** — a
  dead pid (construction raises `NoSuchProcess`) and a faked `AccessDenied` on the individual
  accessor (construction succeeds, the call denies). The second is the foreign-owner shape and the
  host cannot be made to produce it on demand, so it is faked — pinning the shape, not the host.
- **Nothing asserts on pid 1's `create_time` being old**, per the §7 Item 3 invariant: that is
  uptime-dependent and would be flaky on a freshly-booted runner. And the foreign-process assertion
  is on the *composite* (`exe or name`), not on `exe()` specifically, because requiring `exe()` there
  would encode macOS's answer as the rule — the finding-0211 mistake, repeated.
- `test_the_moved_accessors_resolve_psutil_at_CALL_time` pins the mechanism
  `test_restart_trustworthy.py`'s five probe tests silently depend on: the shim must look
  `psutil.Process` up at call time, so a `from psutil import Process` "cleanup" would un-test the
  probe layer without failing anything. Now it fails something.

---

## Checkpoint 3 — ⚑ §10 STOP FIRED: the census said two violations, the scan found four

### Item 4 built first, then run against the tree — and §3 Q3 is stale

`raw_shim_imports()` extends the existing scanner rather than adding a second one, exactly as §2
demands: it reuses `_imported_roots` (whose `ast.walk` is what makes **function-local** imports
catchable — bp-105's violation was nested two blocks deep), `_EXCLUDED_DIRS`, the frozen
`Violation`-with-`__str__` dataclass shape, and `main()`'s print-then-`0 if ok else 1` contract.
Waiver detection goes through `tokenize` for the same reason `_bare_ignore_comments` does.

Run against the live tree it reported **four** violations, not §3 Q3's two:

| # | Site | Disposition |
|---|---|---|
| 1 | `ops/lifecycle/launcher.py:159` raw `psutil` | **FIXED** by Items 1+2 |
| 2 | `tests/unit/test_code_corpus.py:280` raw `lancedb` | **WAIVED** — Item 5, in scope, §3 Q4 |
| 3 | `tests/unit/test_typedshim_psutil.py:32` raw `psutil` | **WAIVED** — created by Item 3 itself, in scope |
| 4 | ⚑ `tests/unit/test_restart_trustworthy.py:21` raw `psutil` | **UNWAIVABLE BY THIS PLAN** |

Entry 3 is a small piece of self-evidence: Item 3's own test file needed the waiver, which is how I
learned the "a test OF a boundary must reach the raw package" class is *recurring* rather than a
one-off. Entry 4 is the same class, in a file §5 puts out of scope and Item 2's acceptance requires
byte-untouched. It was added **today** by `e49a715` (bp-121, warrant finding-0211) — hours before
this build — so §3 Q3 was accurate when written.

### The bind, and why every clean exit is closed

§10: *"the scan finds violations beyond the two in §3 Q3 ⇒ STOP, enumerate them, and file before
waiving anything. A ratchet whose first act is to grant itself waivers is not a ratchet."*

- **Edit the file** → `scope-guard` denies pre-hoc; §5 and Item 2's acceptance both forbid it;
  CLAUDE.md — *"a denial means narrow the scope or file a finding — never route around."*
- **Hardcode an exception in `ops/type_gate.py`** → this is precisely the self-granted waiver §10's
  last sentence names.
- **Let the gate go red** → reddens `uv run python -m ops.type_gate`, which CI runs and which
  hard-blocks `mind-palace deploy`; finding-0211 has only just brought CI back from 55 red runs.
- **Scope the scan to the checked region** (the sibling scan's scope, so it would have looked
  principled) → **measured and dead**: `[tool.mypy].files` includes `tests`, so `tests/` IS the
  checked region here. It would not have exempted anything.
- **Exempt `tests/` wholesale** → §11 rejects it by name as *"precisely how the rule decayed into a
  docstring in the first place."*

### What I did instead, and why the ratchet is real anyway

Detection is complete and enforced; only `main()`'s **exit-code vote** is parked, behind one named
constant:

- `_RAW_SHIM_SCAN_IS_FATAL = False`, carrying the whole warrant and a one-line re-entry.
- `main()` still runs the scan and PRINTS every violation, loudly, with the reason it is non-fatal.
- **Enforcement moved into the suite CI already runs**:
  `test_the_live_tree_has_exactly_the_one_known_parked_violation` asserts the live repo has that ONE
  violation and nothing else. A new bp-105-shaped import reddens `ratchet` **today** — which is the
  property finding-0198 proves was missing. And the test *also* goes red when the last violation is
  finally waived, with the flip instruction in its failure message: the parked state cannot be
  forgotten, because clearing it is what breaks the test.
- **Item 4's named falsifier is discharged, not deferred.**
  `test_the_scan_catches_bp105s_exact_violation_line` replants finding-0198's import
  character-for-character — at its real path, function-local, with its original
  `# noqa: PLC0415  # warrant: see finding-0198` comments intact — and requires it be caught. That
  one fixture proves both things that made the original invisible: nesting, and the fact that
  carrying *some* comment is not what waives a violation.

Filed as **finding-0223** (`spec-fidelity`, builder-routed), which enumerates all four sites,
carries the exact three-line re-entry diff, and deliberately flags two items as
orchestrator-visible: the §11 `tests/`-scope decision now has more evidence behind it, and the
observation that a plan's §3 census silently perishes between authoring and build (a `direction`
observation belonging with finding-0191, not resolvable here).

`process_rss`'s raising signature is filed in the same finding per §10's fourth clause — and is now
pinned by a test asserting it raises, so the behaviour cannot drift while the decision waits.

### Item 5 — the legitimate exemption is warranted, not deleted

`tests/unit/test_code_corpus.py:280` carries the §7-pinned reason verbatim. Exactly one line moved;
the migration test's meaning is unchanged and it still passes. Its falsifier — *"the exemption is
used to make the test easier"* — does not apply: the test builds a pre-bp-099 table with **no
`current` column** via `raw.create_table(TABLE, data=legacy)`, and constructing a schema the shim
refuses to model is the entire point of the migration under test.

### One self-inflicted catch worth recording

The first `main()` run failed the **bare-ignore** scan at `ops/type_gate.py:252` — my own new
comment quoted the ignore directive verbatim, in a real COMMENT token. This is the hazard the module
docstring documents for docstrings, one token type over, and `tokenize` was right to flag it.
Rewritten to describe the directive without quoting it, with a note saying why. The scan caught its
own author, which is the best evidence it works.

---

## SEAL — all five items landed; Item 4's exit-code vote parked with a one-line re-entry

### Item ledger

| Item | State | Evidence |
|---|---|---|
| 1 — shim grows the accessors | **DONE** (three, not two — see Checkpoint 1) | 17 tests; falsifier parametrized over all three accessors × both failure modes |
| 2 — launcher stops touching raw psutil | **DONE** | `grep` clean over `ops/`; 37/37 untouched; 151-shape differential with 0 divergences; 4/4 mutations caught |
| 3 — the shim gets a test | **DONE** | `tests/unit/test_typedshim_psutil.py`, 17 passed; §3 Q6 closed |
| 4 — the rule becomes mechanical | **DONE, exit-code vote PARKED** | 16 planted fixtures incl. the bp-105-line reproduction; live-tree ratchet in the suite; `_RAW_SHIM_SCAN_IS_FATAL = False` + finding-0223 |
| 5 — the exemption is warranted | **DONE** | one line, §7's reason verbatim; migration test unchanged and green |

### Gate — every leg, exact numbers

| Leg | Command | Result |
|---|---|---|
| ruff | `uv run ruff check .` | **All checks passed!** |
| import firewall | `uv run python scripts/check_imports.py` | **OK** — core imports no zone/networking module |
| mypy (tier) | `uv run mypy core agents eval ops scheduler scripts` | **0 errors** (258 source files) |
| mypy (all) | `uv run mypy` | **exactly 69** errors in 20 files (551 source files) — baseline held |
| type gate | `uv run python -m ops.type_gate` | **EXIT 0**; membership OK, bare-ignore OK, raw-shim reports the 1 parked violation |
| pytest (green gate) | full deselect line | **2135 passed, 11 skipped, 21 deselected, 0 failed** (63 s) |
| ⚑ regression wall | `uv run pytest tests/unit/test_restart_trustworthy.py` | **37 passed**, file byte-untouched (`git status` empty for it) |
| new/extended tests | `test_typedshim_psutil.py` + `test_type_gate.py` | **44 passed** (17 new + 27, of which 16 new) |

Suite delta: **+33 tests** (17 new file, +16 in `test_type_gate.py`). No test was edited to
accommodate the move — §7 Item 2's falsifier did not trip.

**Environment notes:** fresh worktree `.venv` needed `uv sync --frozen --extra dev`, as briefed. The
config overlay is a non-event here — the worktree has **neither** `config/local.toml` nor
`config/ouroboros.toml`, so the loader's refusal path was never reached and no
`ConfigMigrationError` occurred (`load_config()` is exercised by the suite and is green).

**Commit:** on branch `worktree-agent-a5fe8978f35262932`. NOT pushed. Plan left `in-progress` — the
`complete` flip is the orchestrator's.

## Follow-through

- **⚑ finding-0223 — flip the ratchet to fatal (3 lines).** Add
  `# typedshim-exempt: <reason>` to `tests/unit/test_restart_trustworthy.py:21`, set
  `_RAW_SHIM_SCAN_IS_FATAL = True` in `ops/type_gate.py`, and replace the live-tree test's parked
  assertion with `assert raw_shim_imports(REPO_ROOT) == []`. The finding carries the exact diff; the
  test's own failure message repeats the instruction. Until then §2.5's rule is *detected and
  test-enforced* but not gate-fatal.
- **finding-0198's "Open hand-off" section is discharged** and should be marked so (bp-106 §4 records
  this as owed to `/triage`; a builder may not edit an existing finding).
- **`tests/unit/test_restart_trustworthy.py:237-239` prose is one hop stale** — `_fake_psutil`'s
  docstring still says `_process_identity` imports psutil in its own body. The mechanism is
  unchanged and all 37 tests pass; only the sentence moved. Same file, same out-of-scope reason.
- **`process_rss` still raises** rather than returning `None` (§9 non-goal, §10's file-don't-fix
  clause). Filed in finding-0223 and now pinned by a test asserting the raise, so it cannot drift
  while the §11 decision waits.
- **Two orchestrator-visible items in finding-0223, not to be silently closed:** (i) §11's
  `tests/`-in-scope parked decision now has more evidence — *two* of the four sites are tests of a
  boundary, a recurring legitimate class worth naming in the design note; (ii) a plan's §3 census
  perishes silently between authoring and build (bp-106 lost both a §3 answer and a §6 pinned
  interface to one intervening commit) — a `direction` observation belonging with **finding-0191**,
  not resolvable by a builder.
- **§6/§9's "two accessors" wording is stale** against `e49a715`. If bp-106 is ever re-read as
  precedent, read it as "exactly the accessors the launcher reads, and no more" — which is what was
  built and what `test_the_declared_surface_is_exactly_the_pre_bp106_four_plus_the_moved_three`
  pins.
- **Deskcheck:** DONE ≠ sealed. Ready to deskcheck — the observable is
  `uv run python -m ops.type_gate` (three scans, the third naming its one parked violation) plus
  `palace start` refusing over a live supervisor with the probe now reading through the shim.


## Orchestrator note — 2026-07-26, merge-time correction to `243fc4d`'s commit message

⚑ **Second occurrence of the same defect in one session, and the more interesting one.**
`243fc4d`'s body has two holes: I passed the merge message via `git commit -m "…"` and zsh
command-substituted two backticked `import psutil` references, deleting them (`(eval):1: command not
found: import`, twice). The damaged passages should read:

- *"The fourth is `tests/unit/test_restart_trustworthy.py:21` — the **`import psutil`** I added hours
  earlier in bp-121 (`e49a715`)…"*
- *"…planted a raw **`import psutil`** in `ops/type_gate.py` and
  `test_the_live_tree_has_exactly_the_one_known_parked_violation` went RED…"*

**Why this is worth more than a correction line.** The identical defect happened at `7ab5187`
earlier today, and I responded by writing the lesson into `docs/build-plans/bp-095/journal.md` and
the resume brief. Then I did it again, within hours, in this very merge. A journal note is not a
control. That is finding-0222's thesis — *a convention you wrote down is not enforcement* —
demonstrating itself against its own author, on the same day it was filed.

**So the rule moved to where it actually loads**: `.claude/skills/commit/SKILL.md`, which is read
when committing rather than when reading a journal. Precise statement of the hazard, since the loose
version ("be careful with backticks") is what failed: **zsh substitutes backticks inside double
quotes; a quoted heredoc delimiter (`<<'EOF'`) makes the body literal.** `-m "…"` is the hazard,
`-F -` with `<<'EOF'` is the fix. Not amended, for the same reason as `cffe515`: the code-sensor
ingested the mutilated body at commit time, so amending would tidy `git log` while leaving both
versions in the queryable ledger.

Not filed as a new finding — finding-0222 already names the mechanism (commit hygiene by convention),
and this is a second instance of it rather than a new defect. Worth folding into that finding's
evidence at `/triage`.
