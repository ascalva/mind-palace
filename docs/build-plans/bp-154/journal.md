# bp-154 — journal

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
