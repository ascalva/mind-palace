---
type: finding
id: finding-0124
status: resolved
created: 2026-07-20
updated: 2026-07-20
links:
  - scripts/verify_planes.py                        # the host-dependent verdict (fixed)
  - tests/unit/test_plane_migration.py              # the two portability bugs (fixed)
  - docs/build-plans/bp-078/plan.md                 # the sealed plan these shipped in
  - docs/findings/finding-0038.md                   # kin: "green locally" ≠ CI green
re_entry: null
ftype: spec-defect
origin_plan: bp-078
route: orchestrator
resolution: >
  Two portability defects in bp-078's verifier, both fixed here. (1) verify_planes.check_lane
  decided PENDING-vs-FAIL by resolving the lane's owner uid to a NAME via real pwd and testing
  membership in a hardcoded {ascalva} set — green on the owner's Mac (uid→"ascalva"), FAIL on Linux
  CI (runner uid→a non-"ascalva" name). Now the split reads the three role uids from the PROBE (fake
  in tests, real in prod) via _is_role_uid: a lane owned by a role account other than expected =
  FAIL, anything else = PENDING — identical on any OS. (2) the exhaust/reports ratchet skipped only
  on "user absent", unlike the vault/data ratchets which also skip on "lane not yet chowned"; once §1
  created the users but §8 (chown) stayed parked, it enforced prematurely and reddened locally. Fixed
  to key on the lane's real ownership. Full 6-leg gate green; CI confirmed on the follow-up run.
---

# bp-078's plane verifier was not OS-portable — CI (Linux) red since the seal while the owner's macOS gate stayed green

## What
Owner-reported (2026-07-20): GitHub Actions `ci` had been failing since the bp-078 seal push
(`c5920d5`). Two defects, both invisible to the local (macOS) gate the builder and orchestrator ran:

1. **Host-dependent PENDING/FAIL** (`test_partial_migration_is_not_a_false_green`). The lane owner
   check resolved `owner.uid` to a username via real `pwd.getpwuid` and tested it against
   `_UNMIGRATED_OWNERS = {"ascalva"}`. On the owner's Mac a human-owned lane resolves to `ascalva`
   (in the set → PENDING, correct); on the CI Linux runner it resolves to a non-`ascalva` name (not
   in the set → **FAIL**). The verdict of a fixture-based test thus depended on the host's user db.
2. **A ratchet that enforced on a partial migration** (`test_ratchet_exhaust_reports_owned_by_work`).
   Its skip predicate keyed only on "ouroboros-work exists", unlike the sibling vault/data ratchets
   which also skip on "lane not yet chowned to the target". After the live migration did §1 (create
   users) but parked §8 (chown, per finding-0123), the user existed while `exhaust/reports` was still
   ascalva-owned, so the ratchet enforced `st_uid == work` and reddened the local suite.

## Why it matters
A trust gate that is green on the author's machine and red on CI is worse than a red one: it hides a
real portability defect behind a passing local run (kin to `finding-0038`). And a self-configuring
ratchet that mis-scores the *partial*-migration state (now a long-lived state, since the core plane
is parked on finding-0123) reddens the suite for a system that is behaving exactly as intended.

## Root cause
The verifier's verdict logic reached around its own injectable `SystemProbe` to the real host user
db (`pwd`) for the human/role distinction, so a fixture test wasn't actually hermetic. And one
ratchet's skip predicate was written inconsistently with its siblings. Neither the builder's gate nor
the orchestrator's re-run caught it because **both ran on macOS**; CI runs Linux — the exact
`finding-0038` gap ("green locally" is not the attestable gate).

## Fix (this commit)
- `verify_planes._is_role_uid(probe, uid)` decides FAIL (wrong role account) vs PENDING (human / not
  migrated) from the PROBE's role uids — never the host user db. `_looks_unmigrated`/`_UNMIGRATED_OWNERS`
  deleted. The test now asserts PENDING for an arbitrary non-role uid (`424242`, the CI-runner case)
  AND FAIL for a wrong-role owner — reproducing the CI condition deterministically on any OS.
- The exhaust/reports ratchet now skips on `st_uid != work` like the vault/data ratchets — SKIP until
  §8 chowns it, so a partial migration never reddens the suite.

## Routing
`spec-defect` → orchestrator; resolved in-repo. Lesson (re-affirming finding-0038): a verifier that
runs in CI must be host-independent, and its acceptance must be checked on the CI OS, not only the
author's — local-green is necessary, not sufficient.
