---
type: finding
id: finding-0039
status: promoted # 2026-07-12 — owner accepted oq-0017: side-effect-audit rule ratified into the build-plan skill (§7 falsifier bullet); PAT notice acknowledged
created: 2026-07-12
updated: 2026-07-12
links:
  - docs/build-plans/bp-016/plan.md
  - ops/ci_witness.py
  - tests/unit/test_ci_witness.py
ftype: discovery
origin_plan: bp-016
route: orchestrator
resolution: "Promoted via oq-0017 (owner accepts, 2026-07-12): the falsifier-demo side-effect audit is now pinned in .claude/skills/build-plan/SKILL.md §7 (warrant-linked here). Prompt-level mitigation continues in every delegation prompt. PAT-rotation notice delivered; parked Item-11c disposition unchanged."
---

# Falsifier-demo run against the pre-change module live-rotated the GitLab PAT

## What

bp-016 Item 7's falsifier-demo discipline ("run the new suite once against the
pre-change GitLab module and show the red") executed `test_rotate_is_guided_manual_rc1`
un-mocked. Against the NEW module that test is pure (GitHub `rotate()` is a
guided-manual print, rc 1 — Q7: no self-rotation endpoint exists). Against the OLD
module, `rotate()` is a LIVE action: it read the Keychain `gitlab-api` token, called
GitLab's `POST /personal_access_tokens/self/rotate`, and stored the new token
(2026-07-12, observed output: `token rotated (id 25599923, expires 2026-08-11) —
stored + attested`).

Damage assessment, done immediately:
- The rotation completed its fail-safe ordering end-to-end: verify-new → Keychain store
  → read-back compare → attest. The owner's GitLab token is VALID, expiry moved to
  2026-08-11; the old value is revoked server-side. Nothing is broken.
- No secret was printed, logged, or committed (output carries token id + expiry only).
- The `token_rotated` attestation landed in the WORKTREE-local, gitignored
  `data/attestations.sqlite` (fresh file created by the test run) — not the live
  system's store. Unsigned record (attestation signing not enabled in this env).

## Why it matters

An agent-initiated test run mutated a live credential — un-gated, as a side effect.
The rotation path itself is sanctioned and fail-safe, so the outcome is benign, but
the mechanism is a real hazard class: **the falsifier-demo discipline points a suite
at old code by design, and old code may hold live side-effecting functions.** A
less fail-safe side effect (a POST that plays a job, a dispatch, a write) would not
self-heal. The discipline should carry a side-effect audit step: before running any
suite against a pre-change module, enumerate the module's live-action functions and
mock/skip them for the demo run.

Also worth the owner knowing: the GitLab PAT in Keychain (`gitlab-api`) was rotated
2026-07-12 (id 25599923, expires 2026-08-11). The plan's parked decision "gitlab-api
token left in place; the owner revokes at Item 11c" is unchanged — there is simply a
newer value in the same Keychain slot.

## Re-entry condition

None parked — bp-016 work continues (the new module's `rotate()` is pure, so the
hazard dies for this module with Item 6/8). The routed question is process-level:
whether the checkpoint/build skills should pin a "side-effect audit before
falsifier-demo runs" rule.

## Routing

`design | direction` → orchestrator: a one-line amendment candidate for the
falsifier-demo discipline (side-effect audit before running suites against
pre-change modules), plus owner notice of the incidental PAT rotation.
