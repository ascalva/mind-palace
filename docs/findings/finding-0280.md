---
type: finding
id: finding-0280
status: open
created: 2026-07-28
updated: 2026-07-28
links:
  - tests/integration/test_worktree_enforcement.py
  - docs/findings/finding-0276.md
ftype: design
origin_plan: orchestrator
route: orchestrator
resolution: null
---

# The worktree-enforcement tests fail in live checkouts and pass in CI — hermeticity contamination, or a live enforcement gap

## What

Measured 2026-07-28, on pristine main (an unrelated working diff stashed for the
experiment):

```
FAILED test_a_deny_cross_worktree            — worktree-A must NOT be able to write worktree-B's core/**
FAILED test_c_unsafe_direction_narrow_not_loosened — FAIL-CLOSED VIOLATION: a broad main-checkout pointer loosen…
FAILED test_d_no_pointer_is_no_plan_not_main_fallback — the foundation denylist must bind even with no active plan
3 failed, 5 passed
```

The same tests pass in CI's hermetic runner (they are in the green set of every green `ci`
run). Additional facts: the failure set varies with context — in a full-suite run the same
session, `test_a` passed while `test_c`/`test_d` failed (ordering- or state-dependent). The
live checkout carries untracked `.claude/state/` files CI never has (`active-plan` — empty,
`docket.md`, `session-baseline`); `CLAUDE_PROJECT_DIR` was **unset** in the failing shell,
ruling out the obvious finding-0031-style env bleed.

## Why it matters

These are not ordinary tests — they are the enforcement layer's own falsifiers, printing
FAIL-CLOSED VIOLATION in exactly the environment where enforcement is live. Two hypotheses,
sharply different in severity:

1. **Test-hermeticity defect** (benign-ish): the tests read the real checkout's untracked
   state and are contaminated by any live session. Then CI green is the true verdict, but
   the tests cannot be trusted locally — which also means a *real* future regression could
   hide inside the familiar local red.
2. **Live enforcement gap** (serious): the messages describe the hooks' actual behavior in
   the presence of a live session's state — a broad main-checkout pointer loosening scope,
   the foundation denylist not binding without an active plan. CI would never see this
   because CI never has session state. This is the shape finding-0276 warned about from the
   credential side: controls that hold in the clean room and not in the room where work
   happens.

## Proposed direction

Reproduce in a scrubbed temporary clone (no untracked state) — expect green; then add the
three state files back one at a time to identify the contamination channel. If any file
changes *hook behavior* rather than *test expectations*, escalate: that is an enforcement
hole, blocker-grade, and the fix belongs in the hooks, not the tests. Either way the tests
should build their own hermetic state fixture so local red means something again.
