# bp-154 — journal

## SEAL — 2026-08-05 — all five items landed; gate recorded; PR opened for the owner's merge

**Status.** The supervisor has a power axis. Items 1–5 are complete on
`build/bp-154-power-axis` (5 commits, `3e0713f`..`cf8d24e`); the full local gate is recorded
below; the one hard pin held (the power rule is its own predicate) and the composition falsifier
was executed rather than asserted.

### Completed, per acceptance criterion

- **Item 1 — the `Power` sensor** (`3e0713f`). `scheduler/power.py`, mirroring `presence.py`: an
  injectable probe over `pmset -g batt`, a floor, and `assume_discharging_when_unknown = True`.
  All four paths to `None` are tested (absent tool, failed/hung exec, unreadable output, a probe
  that RAISES). 22 unit tests, no subprocess among them.
  *Non-vacuity:* every fail-closed assertion also asserts the probe was consulted (a call log), so
  none of them could pass against a sensor that never looks; and
  `test_the_fail_closed_default_is_what_makes_that_true` flips the field to prove the default is
  load-bearing rather than incidental.
- **Item 2 — `power_blocked_tiers()`** (`8f83561`), landed **inert**: `tick` untouched, so no
  dispatch decision changed. `blocked_tiers()` is asserted byte-identical across all four
  presence × power combinations, and a source-shape test pins that each predicate reads its own
  sensor and no other's.
  *Non-vacuity:* the source test asserts `self.power.` IS findable elsewhere in the class, so its
  absence from `blocked_tiers`'s body is evidence and not a search that matches nothing.
- **Item 3 — composed at the ONE claim site** (`007324a`). One term added to the union at
  `supervisor.py`; nothing else.
  *Non-vacuity:* the composition test asserts, before claiming, that the foreground gate is open,
  the model rule unarmed, and the floor unreached (55%) — so the power term is provably the only
  rule that can refuse. **The falsifier was executed:** deleting `| self.power_blocked_tiers()`
  reds exactly `test_a_heavy_job_is_NOT_claimed_while_discharging_and_IS_once_back_on_AC`
  (1 failed, 52 passed) while every sensor and predicate test stays green — the finding-0187 shape
  caught in the act.
- **Item 4 — the floor** (`b687031`). `tick` refuses **before** `claim` below the floor, so no
  RUNNING row is minted; the test asserts the clean close as the next run experiences it
  (`sweep_orphans` → nothing requeued, nothing failed).
  *Non-vacuity:* the floor test enqueues a **light**-tier job, so the discharging shed provably
  does not cover it — the test cannot pass on Item 3's behaviour. Deleting the floor branch reds
  four tests. The "must not spin hot" falsifier is executable: a counting probe proves a ten-tick
  drain request costs exactly ONE battery reading.
- **Item 5 — the carried surface** (`cf8d24e`). Six test files construct a real `Supervisor`; all
  six now inject a power sensor.
  *Non-vacuity:* proven necessary, not assumed — with the probe forced unreadable (the CI runner's
  condition: `ubuntu-latest`, no `pmset`), `test_cron_jobs_are_gated_during_foreground_then_run_in
  _a_trough` fails `assert trough.run() == 2` with 0. With the injections in place under the same
  simulation, the whole model-free tier is green but for the three known-red worktree tests.

### The gate (each leg run separately; counts exactly as observed)

| leg | result |
|---|---|
| `uv run ruff check .` | exit 0 — All checks passed |
| `uv run mypy core agents eval ops scheduler scripts` | exit 0 — no issues in 263 source files |
| `uv run mypy` (argless) | exit 1 — **69 errors in 20 files** (the expected baseline; none in the new files) |
| `uv run python -m ops.type_gate` | exit 0 — membership OK, bare-ignore OK, one pre-existing parked `psutil` report |
| `uv run pytest -q` | exit 1 — **5 failed, 2463 passed, 15 skipped** in 278 s |

The five reds are the three known-red classes and nothing else: the finding-0103
core-self-containment ratchet, `tests/e2e/test_dream_v2_live.py`, and three
`tests/integration/test_worktree_enforcement.py` cases (issue #13/finding-0280 — green in CI).
⚑ `tests/e2e/test_scheduler_live.py` — in write scope, and the known flake — **passed** in the
gate run. It had failed in an earlier full run of this session, on `assert captured["text"].strip()`
with `sup.run() == 1` and `state == DONE` already passing: the job dispatched and the live model
returned an empty string. Not a power refusal (a refusal fails the `run() == 1` line one assertion
earlier), and it now carries an injected on-AC sensor.

### Decisions taken in-build, with their warrant

- **Unknown PERCENTAGE does not halt** (`halt_when_percent_unknown = False`, a named field, not an
  omission). Fail-closed on the *discharging* question costs the heavy lanes — A1.2's rule, and the
  degradation §10 already calls "safe but useless". Fail-closed on the *floor* refuses every tier,
  so a host with no battery to read (a desktop, CI, any non-macOS worker) would dispatch nothing
  ever: the guard against an outage would BE the outage. The knob exists, defaulted off, asserted in
  both positions.
- **The hold is the absence of dispatch, not a process exit** — a deviation from A1's parked
  hold-for-AC default, filed as **#40** with its evidence rather than taken silently:
  `ThrottleInterval` is 10 s and every respawn pays preflight's uncosted ~120 s Ollama probe
  (finding-0195), so a restart loop at the floor would spend the very reserve the floor protects.
  `ops/lifecycle/launcher.py` is also outside this plan's write_scope.
- **Write-scope overrun, flagged not hidden:** `tests/integration/test_cron.py`,
  `test_research_cron.py` and `test_chat_sensor_wiring.py` are not in §5's list. §5 anticipated the
  repair class but enumerated three files where the real set is six. The PR body says so.
- **The daemon can read `pmset` where it runs** (stop-and-raise condition 4, checked): `/usr/bin/
  pmset` is `-rwxr-xr-x root:wheel`, `-g batt` needs no privilege, and neither plist overrides PATH,
  so launchd's default PATH reaches it. Verified by reading the plists and the binary's mode, not by
  executing inside the daemon — recorded as such.

### Nothing was reached for that the plan says to stop on

`HEAVY_TIERS` was read, never reshaped; `tests/integrity/test_shadow_isolation.py` is untouched and
green. `scheduler/presence.py` is untouched. No cancellation of an in-flight job exists anywhere in
the diff. No status field, no blessing, no `deploy`, no fixed point.

### Next action

The owner's review of the PR. On merge, `#12` closes (the PR body carries the unbackticked keyword)
and `#40` remains parked with its re-entry condition.

### Open questions

- **#40** (`type:direction`, `route:orchestrator`, `parked`) — the process-level clean stop is
  unwired; re-entry is a fifth incident showing the idling daemon itself drains below the floor, or
  someone wiring a power reading into `status` display (A1.3's parked decision).

### Context-manifest delta

Read beyond §2's manifest, all load-bearing: `scheduler/queue.py` (what "the ledger" is at the
supervisor's altitude — `claim` mints the only RUNNING row, `sweep_orphans` is what "clean" means to
the next run), `ops/lifecycle/runs.py` + `launcher.py:660-860` (recovery mode is the RUN ledger's,
not the queue's — the distinction Item 4's honest claim rests on), `.github/workflows/ci.yml` (the
runner is `ubuntu-latest`, which is what makes the fail-closed default a test-repair obligation),
both launchd plists (PATH and `ThrottleInterval`), `tests/integrity/test_shadow_isolation.py:90-107`
(the tripwire, confirmed untouched). `docs/findings/finding-0279.md` was NOT read — the frozen
evidence it holds is carried verbatim in Amendment A1, which was.

```read-map
docs/design-notes/dn-supervision-and-liveness.md:668: A1.1 — the one hard pin: the power axis is its OWN predicate, never folded into blocked_tiers()
docs/design-notes/dn-supervision-and-liveness.md:684: A1.2 — the fail-closed idiom borrowed from Presence, and the floor's "clean stop, never a death"
docs/design-notes/dn-supervision-and-liveness.md:711: A1.4 — tier 5 with a tier-4 test, and the honest limit: bounds what is STARTED, not what is running
scheduler/power.py:139: the fail-closed default — an unreadable battery is discharging (A1.7's named falsifier, made a field so it is executable)
scheduler/power.py:147: the ONE named asymmetry: unknown percent does not halt every tier, or the guard against an outage becomes one
scheduler/power.py:167: below_floor — on AC is never below the floor at any percentage; the comparison is <=, and why
scheduler/power.py:106: the probe: shutil.which guard + explicit timeout + (OSError, SubprocessError) — three paths to None, none to a crash
scheduler/supervisor.py:186: power_blocked_tiers — the third sibling; HEAVY_TIERS read, never reshaped; tier claimed honestly
scheduler/supervisor.py:245: THE FLOOR, sitting BEFORE claim — that placement is the whole content of "close the ledger clean"
scheduler/supervisor.py:251: the ONE claim site: the union gains one term and nothing else changes
tests/unit/test_power.py:79: ⚑ the plan's most important test — None yields the restrictive answer, with the probe proven consulted
tests/unit/test_power.py:107: the inversion executed: flipping the default turns the unreadable case into "fine", so the default is load-bearing
tests/integration/test_supervisor.py:503: ⚑ the tier-4 composition test — deleting the union term reds exactly this and nothing else
tests/integration/test_supervisor.py:561: the floor's clean close, asserted as the next run sees it (light tier, so the shed provably does not cover it)
tests/integration/test_supervisor.py:633: the "must not spin hot" falsifier: ten ticks cost one battery reading
tests/integration/test_supervisor.py:470: the foreground gate is byte-identical under all four presence × power combinations
```

## Follow-through
- **Built?** Yes — sensor, predicate, composition, floor, and the repaired test surface. Five
  commits, each item separately reviewable; Items 2 and 3 deliberately split so "inert" and "now
  consumed" are distinct diffs.
- **Wired / delivered (or why dormant)?** Wired, and ON by default with no flag: `Supervisor.power`
  is `field(default_factory=Power)`, so `launcher.py:521` and `scripts/watch.py:95` get the guard
  with no edit — the ON switch is not a follow-up. What is NOT wired, deliberately and filed as
  **#40**: the process-level clean stop (the launcher is out of write_scope, and a KeepAlive restart
  loop would out-drain the idle hold).
- **Does a consumer use it?** Yes — the union at the one claim site is the consumer, and deleting
  the term reds a test. That is the whole point of Item 3 existing separately from Item 2.
- **Track state (what remains on this track)?** `dn-supervision-and-liveness` Amendment A1 is fully
  implemented by this plan; A1.3's preflight *display* of power state was never in scope and stays
  parked (§11). The note's main body is untouched by this build — §2.5's non-blocking dispatch and
  finding-0178's in-flight bounding remain open and are explicitly NOT this. The plan protects
  bp-153's rebuild, which is the reason to land it before bp-153 Item 3 runs.
- **Opened a new track/finding?** One issue: **#40** (`type:direction`, `route:orchestrator`,
  `parked`, with its re-entry condition). No new track.

**Ready to deskcheck.** The honest demonstration is: unplug the machine and watch a synthesis-tier
job stay QUEUED while the light lanes drain, then plug in and watch it go — the code path is exactly
what the tests exercise, but a deskcheck on real hardware is what proves the *probe* reads what we
think it reads on the live daemon.

## Pre-build notes for whoever picks this up

- ⚑⚑ **The power rule gets its OWN predicate. This is the one hard pin.** Do not fold it into
  `blocked_tiers()`. The code states the rule and the reason in its own words
  (`scheduler/supervisor.py:131-134`): *"THE FOREGROUND GATE, and nothing else. Deliberately not
  extended with the single-model-in-flight rule (bp-110 §7 Item 4's invariant: 'the foreground gate
  keeps its meaning and is not overloaded') — two different reasons to refuse a tier, conflated into
  one predicate, is how a reader later cannot tell which rule refused a job."* `model_blocked_tiers()`
  (`:137`) is the precedent for a sibling. Yours is the third. Three predicates, three questions.

- ⚑⚑ **Fail CLOSED. This is the single most important test in the plan.** Copy the idiom from
  `presence.py:49,56-59` — `assume_present_when_unknown: bool = True`, so a `None` probe returns the
  *restrictive* answer. Yours is `assume_discharging_when_unknown = True`. An unreadable battery
  means discharging. The failure being designed against is the machine dying; a sensor that fails
  open re-creates it precisely when the system is least healthy. Also handle a probe that *raises* —
  an exception escaping into dispatch is a new crash path, not a guard.

- ⚑ **A guard nobody calls is not a guard — the finding-0187 shape.** The standing proof in this
  note's own §0: deleting bp-105's sweep call left **85/85 green**. That is why Items 2 and 3 are
  separate, and why Item 3's acceptance is specifically that **deleting the new term from the union
  at `supervisor.py:177` must redden a test.** If it doesn't, the predicate is decorative. Test the
  composition, not just the predicate.

- ⚑ **Read `HEAVY_TIERS`; never reshape it.** `tests/integrity/test_shadow_isolation.py:96-107`
  imports it and asserts `shadow_job.tier in HEAVY_TIERS`. That file is deliberately **out of write
  scope**: if it reddens, you reshaped the tier set instead of adding a predicate, and the approach
  is wrong. Stop — do not edit the test to fit.

- ⚑ **Never kill an in-flight job.** This plan bounds what is *started*, not what is running
  (Amendment A1.4's honest limit, recorded rather than hidden). Jul 24's `code_backfill` was already
  in flight when the throttle hit — so yes, this design would not have prevented that one outright,
  and that is stated in the amendment. In-flight bounding is finding-0178's job-timeout machinery.
  If you reach for cancellation, file and stop.

- ⚑ **The sensor lives in `scheduler/`, not preflight.** Issue #12's own direction text says
  "health/preflight reads `pmset -g batt`" and **A1.3 amends it**: preflight runs in the *caller's*
  environment, not the daemon's — open issue #19 is the standing proof (`status` reports
  `sandbox: present` while every live run booted with it off). A power gate there would report
  whoever typed `palace status`. Refusal binds where dispatch happens.

- ⚑ **"Embedder-bound lanes" is parked with a default, not left to taste.** Default selector is the
  existing `HEAVY_TIERS`, so there is **one** shed vocabulary rather than two. If you conclude
  `load_key` is the right selector, that is a re-entry condition (§11), not a judgment call to make
  mid-build.

- ⚑ **Don't let the hold-for-AC branch drain the battery it protects.** Default is: close the ledger
  clean and stop; launchd KeepAlive restarts and re-evaluates. An in-process sleep/wait loop holds a
  supervisor lock while doing nothing. And the clean close is the *point* — if the stop leaves a
  stale `running` row, you have reproduced the Aug 1 recovery run you were preventing.

- **Item 1 needs no hardware.** The probe is injectable exactly like `idle_probe`. No `pmset`
  subprocess in unit tests, and the real probe must not run at import time.

- **Tier honesty:** claim **tier 5 with a tier-4 test**, identical to what §2.7 claims for the
  memory ceiling. Power is a sampled reading of the physical world; tier 1 is unreachable and
  claiming it is the overclaim the enforcement ladder names as *the* foot-gun.

- **This plan protects bp-153.** That rebuild is a long sliced job, and the Jul 24 wedge it must
  route around was itself caused by a battery drain. Landing this before bp-153 Item 3 runs is cheap
  insurance — different track, disjoint scope, safe to run in parallel with bp-151..153.

- **Context:** three emergencies (Jul 24 fatal, Jul 28 caught, Aug 1 fatal). Battery hardware is
  healthy — Condition Normal, 95% max capacity, 128 cycles, re-measured 2026-08-05. The drain is
  load. The scheduler is the defect.
