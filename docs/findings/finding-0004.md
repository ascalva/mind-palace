---
type: finding
id: finding-0004
status: resolved
created: 2026-07-05
updated: 2026-07-05
links:
  - .claude/settings.local.json
  - .claude/hooks/_lib.py
  - docs/design-notes/agent-workflow.md
  - docs/build-plans/bp-002/plan.md
ftype: discovery
origin_plan: bp-001
route: orchestrator
resolution: "Owner chose option (a): gitignore `.claude/settings.local.json` (per-machine permission cache, not shared config). Landed in `.gitignore` at commit 868ed17 (the bp-001 commit) and the file is untracked out of the index; reinforced by a machine-global ignore (`~/.config/git/ignore`). No `_lib.py` change is needed — `git status --porcelain -uall` (cmd_stop_audit (b)) and `git ls-files --others --exclude-standard` (the A3 (c) scan) both omit ignored paths, so the file's permission-cache churn never reaches the audit's working-tree diff. Locked by docs/build-plans/bp-002/acceptance/run.sh (0004 before/after): a *tracked* settings.local.json modification trips (b) (rc=2, names it) — the finding's original state — while after the committed untrack+gitignore the same churn is clean (rc=0). Resolves rather than promotes: the operative fix is repo hygiene, not a design change (agent-workflow.md §6/§16 A3 merely records the ambient-path-exclusion principle, warrant-linked here alongside finding-0005)."
---

# Stop-gate (b) flags harness-managed `.claude/settings.local.json`

## What
During bp-001, the Stop-gate scope audit (§6b) would flag
`.claude/settings.local.json` as an out-of-scope worktree change. The file is
**tracked** (not gitignored) and is written by Claude Code's permission system,
which auto-persists a `Bash(...)` allow-rule each time a new command is approved.
Two entries were appended this session — for the `_lib.py` import check and the
bp-001 acceptance run — neither of which is a bp-001 deliverable, and the file is
(correctly) outside bp-001's `write_scope`.

## Why it matters
This is not specific to bp-001. In steady state, **any** builder session that runs
a newly-approved Bash command mid-build will have the permission system mutate a
tracked, out-of-scope file — tripping the (b) audit through no fault of the
builder. It is the same class as finding-0003: the audit is behaving exactly to
spec (an out-of-scope tracked change *is* present), but the change is machine
bookkeeping, not a builder write. Left as-is it produces a spurious close-block on
otherwise-clean sessions and muddies the "clean delta" signal the audit exists to
give. `spec-fidelity`-adjacent but it bears on usability → routes to the owner.

## Re-entry condition
Owner picks a resolution (below), or a real builder session outside bootstrap hits
this block. Until then the default holds: the file is surfaced, not touched; the
owner reconciles at commit (as with any §12 out-of-scope state).

## Options (owner/orchestrator to decide)
- **(a) Gitignore `.claude/settings.local.json`** (standard practice — it is a
  per-machine local permission cache, not shared config). Then it never enters the
  audit and its churn stops mattering. *Requires committing its removal from the
  index once; a one-line `.gitignore` add — both outside bp-001 scope.* Recommended.
- **(b) Exempt harness-managed paths in the (b) audit** — add
  `.claude/settings.local.json` (and siblings) to an audit-ignore list in
  `_lib.py.cmd_stop_audit`, parallel to how `.claude/state/**` is already gitignored
  and invisible. Keeps the file tracked but stops it blocking. Trade-off: a real
  out-of-scope write to that path would also be ignored (low risk — it is not a
  foundation file).
- **(c) Do nothing** — rely on the §12 surface-and-reconcile protocol every session.
  Correct but noisy; each session close reports a benign block.

Recommendation: **(a)** — gitignore it; it is local-machine state by nature. **Not
blocking** — bp-001's deltas, findings, and harness are complete; this is the
reflection loop reporting on the machinery, exactly as finding-0002/0003 did.

## Routing
`discovery` → `route: orchestrator`. A design-changing fix (audit-exempt list)
would mint an `agent-workflow.md` amendment warrant-linked here; the (a) gitignore
path is a one-line repo-hygiene change needing no spec edit. Both are outside
bp-001's `write_scope` (`.gitignore`, `.claude/settings.local.json`), so this must
route out rather than resolve in-plan.

## Resolution — resolved (2026-07-05, via bp-002)
The owner took option **(a)**: gitignore the file. `.claude/settings.local.json` is a
per-machine permission cache Claude Code rewrites whenever a new `Bash(...)` rule is
approved — local-machine state by nature, not shared config. It is listed in
`.gitignore` (committed `868ed17`, the bp-001 commit) and is untracked out of the
index, so it is now genuinely ambient: neither a scope target nor a blessing surface.

No code change was required. Both sides of the audit already honor ignore rules —
`git status --porcelain -uall` (the (b) scope check) and `git ls-files --others
--exclude-standard` (the A3 (c) untracked scan) omit ignored paths — so removing the
file from the index is the whole fix. This is exactly the "diff must judge exactly the
set it is responsible for" principle §6 records (the ambient-path-exclusion paragraph,
warrant-linked here): untracked-inclusive where a Bash write could smuggle a blessing
past, and blind to paths that are legitimately none of the audit's business.

Guarded by `docs/build-plans/bp-002/acceptance/run.sh` (the 0004 before/after check):
while the file is *tracked* and out-of-scope, a mid-build permission-cache write trips
the (b) audit (rc=2, names it) — the state this finding reported; after the committed
untrack + gitignore, the identical churn closes clean (rc=0). This `discovery`
resolves rather than promotes: the owner-chosen fix is repo hygiene needing no spec
edit (as this finding anticipated), while its warrant-sibling finding-0005 carries the
actual enforcement-contract change in A3. Status → `resolved`.
