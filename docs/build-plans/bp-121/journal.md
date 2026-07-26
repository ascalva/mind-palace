---
type: journal
plan: bp-121
started: 2026-07-26
updated: 2026-07-26
---

# Journal — bp-121 (D2's interpreter probe goes platform-robust)

> ## ⚑ BUILD COMPLETE — do NOT `/resume` this plan
> Both items are built and the acceptance is **met on the authority that counts**: the remote
> `ratchet` job is **green on `e49a715`** — all five CI jobs green, `2096 passed, 0 failed`. That
> is the first green `main` since `0206043` (2026-07-25T16:59Z), ending **55+ consecutive red runs
> over ~14 hours**.
>
> The plan is left at `status: in-progress` deliberately. Flipping it to `complete` is the
> ORCHESTRATOR's single-writer duty and the seal is owed at `/triage` — a builder does not
> self-declare done.
>
> **What `/triage` owes:** flip bp-121 → `complete` + seal with `cost.actual` · close
> **finding-0211** (its re-entry condition is discharged verbatim, including "CI's ratchet job is
> green on the runner") · route **finding-0214** (filed this session) · note on **finding-0198**
> that its shim hand-off now covers three psutil accessors, not two · **finding-0212 is now
> actionable** — its remedy (compare the local gate against the authoritative host at seal time)
> has a live worked example in Checkpoint 2 · ⚑ **the deploy gate is unblocked**: `main` finally
> has an attestable green HEAD, so the owner-owed code-ingest deploy can proceed.

Session-53. Contract: `builder`. Ordering per §12: **Item 1 → Item 2**, strictly sequential —
though the *falsifier demo* Item 2 requires had to run against pre-change code, so the tests were
authored first, run RED, and only then was Item 1 applied. Both items' code is now in the tree.

---

## Checkpoint 1 — §2 manifest read, both items written, RED→GREEN demonstrated locally

### Status

Item 1 and Item 2 are **written and locally green** (37 passed, up from 32). The local gate is
clean on four of five legs. **Nothing is committed or pushed yet**, and — per §7 Item 1 — *the
acceptance is the remote `ratchet` run, not this local pass*. A local pass is precisely what hid
this bug for 55 consecutive runs.

### §2 manifest — read in order, and what it changed

All six sources read. Two things worth not re-deriving:

- **The line refs in §2 are accurate** (unlike bp-105's, which were stale): `_pid_alive:127`,
  `_CLOCK_SLACK_S:141`, `_process_identity:144-173`, `_supervisor_alive:176-222`.
- **Q2's unknown is no longer an inference — it is MEASURED.** The plan says *"the code does not
  settle the exact Linux string, and this plan must not guess it"*, and treats the remote run as
  the only authority. I did not guess: a local `podman` machine was already running with
  `ghcr.io/astral-sh/uv:python3.12-bookworm-slim` already pulled, so the failing platform was
  reproducible in ~30 s. See the measurement below. No host value is baked into a test regardless
  — the Linux shape is pinned as an injected fixture — but the diagnosis is now grounded.

### Measured on this host (the macOS half of the divergence)

```
psutil.Process(os.getpid()).name()  ->  'Python'
psutil.Process(os.getpid()).exe()   ->  '/opt/homebrew/.../Python.app/Contents/MacOS/Python'
                        basename    ->  'Python'          # so D2 is silent here either way
psutil.Process(1).name()            ->  'launchd'
psutil.Process(1).exe()             ->  '/sbin/launchd'   # ⚑ readable for a FOREIGN root owner
```

That last line settles §3's Q3 empirically rather than by docstring citation: `exe()` is readable
against a foreign owner on macOS, which is the deployed case post-migration. The switch does not
cost the guard anything on the platform that actually runs the daemon.

### ⚑⚑ Measured on Linux under podman — the bug REPRODUCED and the fix VERIFIED pre-push

finding-0211 *inferred* the Linux `name()` value ("a value containing no `python`") from the
failure plus D1's exclusion, and §3 Q2 forbids guessing it. It did not have to stay inferred. A
console script is just an executable file with a `#!…/python` shebang, and Linux sets `comm` from
the **script's** basename while `/proc/<pid>/exe` still points at the **interpreter** — so the
shape is reproducible without pytest, uv, or this repo. Run in
`ghcr.io/astral-sh/uv:python3.12-bookworm-slim` with real psutil installed, from an executable
named `pytest`:

```
psutil name() : 'pytest'                        # ⇒ D2 FIRES against a live interpreter — THE BUG
psutil exe()  : '/usr/local/bin/python3.12'
exe basename  : 'python3.12'                    # ⇒ D2 silent — THE FIX
```

For contrast, the same probe invoked as `python /tmp/probe.py` in the same image gives
`comm='python'` — which is why *only* the console-script invocation broke, and why nobody saw it
in a direct `python -m pytest` run.

**This closes finding-0211's one open unknown.** The diagnosis was right, the branch was D2, and
the replacement probe is now verified on the platform that was failing rather than only on the
platform that was passing. The remote `ratchet` run remains the formal acceptance (§7 Item 1), but
it is no longer the *only* evidence — which matters, because "we could not test the failing
platform" is the condition that let this survive 55 runs in the first place.

### Item 1 — what was built

`_process_identity` now returns *"the basename of the binary the process is executing"* rather
than *"the process's name"*. `exe()` first; `name()` retained as an explicit fallback when `exe()`
is unreadable **or empty**. The tuple shape and the injected-probe signature are unchanged (§6's
load-bearing constraint), so every pre-existing injected test compiles and passes untouched.

Three deliberate choices, each defensible against a reviewer:

1. **Basename, not the full path** — finding-0211's re-entry condition says basename, and it is
   the tighter probe: an interpreter under `~/python-projects/` would make the full-path test
   report *every* binary there as Python, and D2 could then never fire. That direction is the
   finding-0186 brick, not a safe default.
2. **The `name()` fallback is load-bearing, and I checked the direction before keeping it.** On
   Linux `/proc/<pid>/exe` is unreadable for a foreign owner while `name()` reads fine. Drop the
   fallback and a stale pid recycled onto `systemd` yields *ambiguity ⇒ refuse ⇒ refuse forever* —
   exactly the trap. Kept, and pinned by a test.
3. **Empty `exe()` is treated as unreadable, not as an answer.** psutil returns `''` (does not
   raise) when the executable cannot be determined; `Path('').name` is `''`, which contains no
   "python", so without the guard D2 would fire on every such process. Pinned by a mutation-
   discriminating test.

Local variable renamed `name` → `interpreter` in both functions, because after this change "name"
is the wrong word for what the string is — that mis-naming is arguably how the bug got written.

§4's two reconciliations are done: the D2 docstring gains a `⚑ warrant(finding-0211)` paragraph
stating that the *premise* stands and the *probe* was wrong (the existing `cmdline()` reasoning is
kept verbatim, not deleted), and the `:167-172` comment is preserved verbatim and extended.

### Item 2 — the pin, and the RED demo it requires

Five tests added, in a new block with a header explaining *why the gap existed*: every pre-existing
test **injects** `identity`, so not one of them ever reached `_process_identity`. The bug lived in
the un-driven function. The new tests drive the real probe against a faked `psutil.Process`,
patched as an attribute on the real module (the production import is lazy and inside the function
body, so the patch lands at call time).

⚑ **The falsifier demo, run before the fix** — exactly one test failed, and it reproduced the CI
failure's own assertion:

```
>       assert _probed(1234) is True
E       assert False is True
1 failed, 36 passed
```

`assert False is True` is verbatim what `test_this_very_process_reads_as_a_live_supervisor` prints
on the runner. The other four new tests passed pre-change by design — they pin branches (fallback,
empty-exe, double-denial, unconstructable), not the regression. Post-fix: **37 passed**.

Per §7 Item 2's oq-0017 rule, the demo never drove `launcher.start` (which writes rows and takes
the supervisor lock) — `_supervisor_alive` is called directly with `pid_alive` pinned.

The host-coupled `test_this_very_process_reads_as_a_live_supervisor` is **kept**, per the Item 2
invariant. It is the only thing that caught this.

### Local gate (four legs green, one running)

| leg | result |
|---|---|
| `ruff check .` | All checks passed |
| `scripts/check_imports.py` | OK |
| `mypy core agents eval ops scheduler scripts` | 0 errors (Tier-2 floor) |
| `mypy` (full, tests baseline) | **69** — the pinned baseline, see the snag below |
| `ops.type_gate` | membership OK · bare-ignore OK |
| CI-equivalent `pytest` tier | running at checkpoint time |

⚑ **Snag worth recording:** the bare `import psutil` in the test file pushed mypy to **70**, and
CI's type-gate hard-fails on `!= 69`. Fixed by carrying the same `# type: ignore[import-untyped]`
the launcher already carries. A green pytest would not have caught this — the type-gate is a
*separate* CI job, so a fix for a red `ratchet` could have shipped a red `type-gate` instead.

### In-flight

The CI-equivalent pytest tier (`-m 'not live and not podman and not needs_vault and not
needs_restic'`, with CI's single deselect) is running in the background. Nothing committed.

### Next action

1. Read the background pytest result. If not green, **stop** — §10.
2. Commit both files as one logical change (warrant finding-0211), then **push**.
3. `gh run list --workflow=ci --limit 1` and watch the `ratchet` **and** `type-gate` jobs. Green
   ratchet on the pushed HEAD is Item 1's acceptance; nothing else closes it.
4. If the remote still fails — or fails on only one or two of the three tests — **do not stack a
   second fix**. File a finding with the runner's actual values and stop (§10, and Item 1's
   falsifier).

### Open questions

None owner-level. Two things routed to the journal rather than raised:

- **finding-0198's hand-off stays open and untouched** (§9 non-goal). The probe grew a second
  psutil accessor (`exe()`), so the eventual shim move is now three accessors, not two. Worth
  noting on that finding at `/triage`; a builder may not edit an existing finding.
- **D1's `.replace(tzinfo=UTC)`** left alone per §11. Not observed misfiring; still latent.

### Context-manifest delta

- Read beyond the manifest: `pyproject.toml` (ruff `line-length = 100`, lint select `E,F,I,B,UP`)
  and `.claude/skills/checkpoint/SKILL.md`.
- Proved *not* needed: `core/typedshims/psutil.py` — deliberately not opened, since touching it is
  the §9 non-goal and reading it would only tempt the move.

---

## Checkpoint 2 — local gate closed; two unrelated reds run to ground and filed as finding-0214

### Status

The CI-equivalent tier finished: **2 failed, 2099 passed, 8 skipped, 21 deselected (13:00)**. Both
failures are **provably not mine**, and both are now filed. Item 1 and Item 2 are complete pending
the one acceptance that counts — the remote `ratchet` run on the pushed HEAD.

### The two reds, and why they are not bp-121's

```
FAILED tests/integration/test_selfmod.py::test_good_change_traverses_the_gate_and_is_kept
  assert 0.58 == 0.62
FAILED tests/integration/test_selfmod_cli.py::test_propose_list_show_history
  assert "0.62 -> 0.66" in "…dream_similarity_threshold: 0.58 -> 0.66  (tighten themes)"
```

One cause: both build a self-mod loop over the **merged live config** and assert a literal `0.62`,
the `defaults.toml` value — while the owner's oq-0024 enactment set σ to `0.58` in
`config/local.toml:47`, which is gitignored. CI has no `local.toml`, so CI is green on both.

⚑ **Verified by experiment, not by argument.** I `git stash`ed bp-121's two code files, re-ran
both tests against the pre-change tree, and got the identical two failures; then popped and
re-confirmed 37 passed. The claim "unrelated" is measured.

Filed as **finding-0214** (`codebase` → builder). Not fixed here: those files are outside
`write_scope`, and §10 names widening scope as a stop-and-file condition. The finding argues it is
finding-0212 **with the sign flipped** — 0212 is local-green/remote-red, this is
local-red/remote-green — and that the second is the more corrosive, because a gate that is red for
an unrelated reason is how a builder learns to shrug at "2 failed", which is precisely the habit
that let bp-105 seal over a red CI.

### The remote failure list, checked before pushing rather than after

`gh run view 30192104110 --log-failed` on `8086182`:

```
FAILED tests/unit/test_restart_trustworthy.py::test_this_very_process_reads_as_a_live_supervisor
FAILED …::test_start_refuses_over_a_live_supervisor_without_opening_a_run_or_sweeping
FAILED …::test_force_does_not_bypass_the_single_instance_gate
3 failed, 2088 passed, 13 skipped, 21 deselected in 90.74s
```

Exactly the three tests finding-0211 names, and **nothing else** — so no second defect is hiding
behind this one, and Item 1's falsifier ("fails on only one or two of the three") has a clean
baseline to be judged against. Note the runner is green on the two selfmod tests in the same run,
which independently corroborates finding-0214's diagnosis.

### Final local gate

| leg | result |
|---|---|
| `ruff check .` | All checks passed |
| `scripts/check_imports.py` | OK |
| `mypy core agents eval ops scheduler scripts` | 0 errors |
| `mypy` (full) | **69** — the pinned baseline |
| `ops.type_gate` | membership OK · bare-ignore OK |
| CI-equivalent `pytest` | 2099 passed · **2 failed, both finding-0214, both pre-existing** |
| `test_restart_trustworthy.py` | **37 passed** (was 32) |
| Linux under podman | bug reproduced, fix verified — see Checkpoint 1 |

### Next action

Commit the two code files + this journal + finding-0214, push, then watch **both** `ratchet` and
`type-gate` on the new HEAD. If ratchet is green, Item 1's acceptance is met and finding-0211
closes; the plan still goes to `/triage` for the `complete` flip and seal — a builder does not
self-declare done.

### Open questions

None owner-level. Carried to `/triage`: finding-0214 · finding-0198's hand-off now covers three
psutil accessors rather than two · oq-0024's gitignored enactment has a second consequence.

---

## Checkpoint 3 — SEAL. Remote acceptance MET: `ratchet` green on `e49a715`

### Status

`gh run watch 30192902613 --exit-status` → **success**, all five jobs:

```
✓ vault-axis 35s   ✓ gitleaks 9s   ✓ ratchet 1m52s   ✓ type-gate 27s   ✓ semgrep 28s
2096 passed, 13 skipped, 21 deselected in 92.76s
```

The arithmetic checks out exactly: the previous run was `3 failed, 2088 passed`; `2088 + 3` fixed
`+ 5` new = **2096**. So all three named failures went green and nothing else moved — which is
also the negative half of Item 1's falsifier ("fails on only one or two of the three"). It did not
partially fix; the diagnosis held.

Two commits, both pushed: `e79f337` (finding-0214) · `e49a715` (the build).

### Read-map

```
docs/findings/finding-0211.md:37: the diagnosis — D1 arithmetically excluded, D2 the branch
ops/lifecycle/launcher.py:175: THE FIX's warrant — why exe() over name(), and why basename
ops/lifecycle/launcher.py:183: the one line that was the bug: exe() basename, empty ⇒ None
ops/lifecycle/launcher.py:187: the name() fallback, and why it is load-bearing not defensive
ops/lifecycle/launcher.py:223: D2's docstring correction — premise stands, probe was wrong
ops/lifecycle/launcher.py:247: D2 itself, unchanged in meaning; only its input got honest
tests/unit/test_restart_trustworthy.py:201: why the gap existed — every prior test INJECTS
tests/unit/test_restart_trustworthy.py:214: _FakeProc — None means the accessor RAISES
tests/unit/test_restart_trustworthy.py:249: ⚑ the regression pin, run RED before the fix
tests/unit/test_restart_trustworthy.py:263: the fallback pin — systemd, the brick trap
tests/unit/test_restart_trustworthy.py:272: empty exe() ⇒ unreadable, mutation-discriminating
docs/findings/finding-0214.md:1: the incidental find — local-red/CI-green, 0212's mirror
```

Counted, not listed: the `interpreter` rename across both functions (mechanical), the two
remaining new tests (double-denial and unconstructable-process — branch coverage, not falsifiers),
and this journal.

## Follow-through

- **Built?** Yes, both items. Item 1: `_process_identity` reports the basename of the executed
  binary (`exe()` first, `name()` fallback, empty treated as unreadable). Item 2: five tests
  driving the real probe against a faked `psutil.Process`; the regression pin was demonstrated RED
  against the pre-change code and reproduced the runner's own `assert False is True`.
- **Wired / delivered (or why dormant)?** Delivered, and this one has no dormant switch — it is a
  correction to code already on the live path (`launcher.py:671`, inside `start()`), effective the
  moment it is on `main`. No flag, no config, nothing to enable.
- **Does a consumer use it?** Yes: `Launcher.start()` is the single production call site (verified
  by grep — nothing else in the tree calls either function). Its consumer is every `palace start`,
  including launchd's `KeepAlive` restarts.
- **Track state (what remains on this track)?** The `ops` track's open threads are unchanged by
  this plan and none are blocked by it: **finding-0198**'s shim move (now three accessors),
  **finding-0212**'s seal-vs-authoritative-gate duty, **finding-0214** (filed here), and §11's
  parked D1 timezone question. ⚑ What this *unblocks* is bigger than the track: `main` has an
  attestable green HEAD for the first time in ~14 h, so the owner-owed code-ingest deploy is no
  longer gated.
- **Opened a new track/finding?** One finding, **finding-0214** — two self-mod integration tests
  assert σ against the merged live config, so the owner's gitignored oq-0024 overlay makes them red
  locally and green on CI. Not a new track; `codebase`-routed, bounded, and out of this plan's
  `write_scope`.

### ⚑ Not claimed

This plan is **not deskchecked**, and DONE ≠ sealed. What is demonstrable: `palace start`'s
single-instance guard now answers correctly on both platforms, and CI is green. What has *not*
been exercised is the guard against a genuinely recycled pid on the live host — that remains, as
before this plan, covered by fixtures rather than by an observed incident.

## Markers
