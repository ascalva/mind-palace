---
type: finding
id: finding-0005
status: routed
created: 2026-07-05
updated: 2026-07-05
links:
  - .claude/hooks/_lib.py
  - .claude/hooks/gate-guard.sh
  - docs/design-notes/agent-workflow.md
ftype: discovery
origin_plan: bp-001
route: orchestrator
resolution: null
---

# A Bash-minted build plan created directly at `status: ready` escapes every gate

## What
Surfaced by bp-001's adversarial verification of the blessing machinery. A build
plan **created fresh** (untracked, brand-new file) already carrying
`status: ready` — via **Bash** rather than Edit/Write — is caught by *no* gate:

- `gate-guard` is PreToolUse on `Edit|Write|MultiEdit` only; a `printf > plan.md`
  never triggers it (the known Bash-write escape, parked §14).
- Stop-gate **(c)** scans `git diff HEAD -- docs/design-notes docs/build-plans`.
  A brand-new **untracked** file is absent from `git diff HEAD`, so the blessing
  line is invisible to (c) — even after A1 correctly re-anchored (c) to HEAD.
  A1's fix addresses a *flip of an existing committed artifact*; a *fresh-at-ready
  creation* is a different shape and slips through.
- Stop-gate **(b)** lists the untracked file (`-uall`) but only flags it as an
  *out-of-scope* write. If the plan's own `plandir` is inside the active
  `write_scope` (it is, for that plan's builder) the file is **allowed**; and in
  orchestrator posture (no active plan) the write-scope check does not run at all.
  Either way (b) never recognizes it as a *blessing*.

Design **notes** are safe here only incidentally — `docs/design-notes/**` is on the
foundation denylist, so a Bash-created `status: ratified` note is caught by (b) as
a foundation-file modification. Build plans are **not** denylisted, so the
`proposed → ready` half of the owner-only blessing invariant (§10) has a hole on
the Bash path.

## Why it matters
`§10` states the two blessing gates are "mechanically enforced, not steered" — a
bright line built as a hard constraint. For `proposed → ready` that guarantee is
only as strong as the union of gate-guard (Edit path) and the Stop-gate (Bash
backstop). This finding shows the backstop misses the fresh-at-ready-via-Bash case,
so an agent could self-bless a plan to `ready` and close clean. Low frequency
(requires the Bash path *and* a new-file creation) but it touches a security-plane
invariant, so it should not sit silent. Same class as finding-0003: adversarial
review of the machinery reporting a real gap.

## Re-entry condition
Owner picks a resolution, or a real session is observed minting a `ready` plan via
Bash. Until then the default holds: gate-guard + the current Stop-gate cover the
Edit path and the flip-of-existing-artifact path; the fresh-Bash-creation path is
a documented known gap.

## Options (owner/orchestrator to decide)
- **(a) Extend the (c) detector to be untracked-inclusive** — symmetric to A1's own
  (b) fix. In addition to `git diff HEAD`, scan the new/untracked plan.md and
  design-note files (`git ls-files --others --exclude-standard` under
  `docs/build-plans/*/plan.md` and `docs/design-notes/*.md`) and flag any whose
  on-disk front-matter carries a blessed status. Closes the hole where it was
  opened; a one-plan `_lib.py` change. Recommended.
- **(b) Add `docs/build-plans/**` shape to a blessing-aware denylist facet** — heavier
  and over-broad (build plans legitimately churn non-status fields); rejected in
  favor of (a).
- **(c) Accept as covered by §14's parked "pre-hoc Bash write-pattern denial"** — but
  §14's re-entry is "Stop-gate audit catches ≥ 1 real escape," and here the
  Stop-gate audit is precisely what misses it, so leaning on §14 is unsound.

Recommendation: **(a)**. **Not blocking** — orthogonal to bp-001's A1/A2 deltas
(which are complete and verified); this is the reflection loop reporting a gap the
verification pass found in the wider blessing machinery.

## Routing
`discovery` → `route: orchestrator`. Option (a) is a pure code refinement to
`_lib.py` (a one-session builder plan, no spec edit). If the owner wants the
enforcement contract itself tightened, that mints an `agent-workflow.md` §6c/§10
amendment warrant-linked here. Outside bp-001's delta scope either way.
