# bp-128 — journal

## Pre-build notes for whoever picks this up

- ⚑ **This plan's own §7 Item 3 is the first use of the false-success rule** the owner agreed to on
  2026-07-27 (`docs/brainstorms/the-false-success-rule.md`). Do not soften it into "assert the
  compliant journal is green." The point is the **degenerate input reddens** — and Item 3's
  falsifier (run the new test against the *unfixed* clause; it must pass there) is what proves the
  test distinguishes the fix from its absence. If that falsifier fires, the test pins a constant.

- ⚑ **Fail-open is not a preference, it is the lesson bp-126 paid for twice.** Its first return was
  a clause keying on `rc == 1`, which Python also returns for any unhandled exception — a *crashing*
  generator read as *stale*, blocked, `--write` failed identically, and the close **wedged,
  including the session trying to fix it**. Three of six modes failed closed. Clause (f) is in the
  same file and its BLOCK is equally hard. Any indeterminate input must resolve to ALLOW.

- **The warrant was itself filed on a false premise, and says so.** `finding-0248` originally
  claimed §9 journals are newest-first. They are **oldest-first**. The conclusion survived and the
  true defect is *wider* than the wrong reason implied. Read the correction notice, not just the
  title — and note that the retraction is deliberate evidence in `finding-0249`, not an erratum.

- **§3 is genuinely open — three candidates, none pinned.** That is intentional, not an omission.
  Diff-derived (a) is the strongest on first read because `journal-gate` already computes a session
  diff, but ground it rather than inheriting my guess. Record why (c) is rejected instead of
  skipping it: a denylist of standing-section names rots the moment a template changes.

- **§4 reconciliation is a real risk, not a formality.** This fix makes previously-green journals
  red. Count them *before* Item 3, not after. If the number is large, that is §10 stop-and-raise —
  mass-editing journals to satisfy a newly-honest check is a decision the owner makes.

- **Ordering:** do not run concurrently with bp-127. Both touch Stop-gate behaviour and bp-127's F2
  drill exercises the close path clause (f) governs.

## Re-entry condition

None — the plan has never been started. `status: proposed`; the `proposed → ready` blessing is the
owner's hand alone.
