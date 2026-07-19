# Handoff automation — making seal → brief → (kill) → resume "just happen"

## 2026-07-19T21:24:10Z

```capsule
topic: handoff-automation
date: 2026-07-19

decisions:
  - Owner intent: the session handoff ceremony should "just happen" — the owner should
    never have to think about seal → brief → clear → resume. The bp-072 cockpit is the
    reading room; this closes the loop on the *leaving and re-entering* of sessions.
  - Usage bookkeeping is ALIGNED as-is — no new build wanted. What "usage automation"
    meant to the owner: the orchestrator KNOWS WHEN to run the one-off `/usage` probe
    (pre-spawn budget gate + at seal) and DOCUMENTS it (cost.actual). Judgment of
    when-and-what-to-record is the orchestrator's; scripts do not do everything. The
    scheduled/continuous ledger stays parked (see usage-automation.md), not wanted now.
  - The `resume` half is ALREADY automated: a bare session at root auto-loads
    `.claude/state/resume-brief.md` via the SessionStart hook (this is how session-34
    itself began). The owner runs nothing to re-enter.
  - `clear` is inherently owner/harness, NOT agent-automatable: an agent cannot clear
    its own context mid-turn. In practice it is kill-the-pane + reopen (cockpit.sh
    starts a fresh `claude`) or `/clear` — one keystroke, trivial. Not a build target.
  - The ONE weak link is the brief: it is authored-but-not-ENFORCED. So the handoff is
    habitual, not guaranteed. Chosen direction: a Stop-hook that refuses to close a
    session until a `resume-brief.md` fresher than the last handoff exists — mirroring
    the existing `journal-gate` that already guards per-plan journals. That single
    addition makes the whole loop guaranteed.
  - Enforcement is automated; authorship and re-entry are not, and that is deliberate —
    a handoff is a piece of writing whose job is to let a cold agent continue without
    re-asking (the fresh-agent test). Machine-checking "is this prose sufficient?" is
    not trusted yet; the hook checks that a fresh brief EXISTS, not that it is good.

parked:
  - decision: A cockpit keybind / `palace` verb that runs seal → brief as one motion.
    default: the orchestrator seals + writes the brief by hand at each unit boundary.
    re_entry: the manual seal ceremony proves annoying in real cockpit use → mint it.
  - decision: Scheduled/continuous usage ledger.
    default: self-serve `claude -p "/usage"` probe stands (orchestrator-triggered).
    re_entry: already parked in docs/brainstorms/usage-automation.md — its condition holds.

open_questions:
  - Freshness signal: `resume-brief.md` lives in `.claude/state/` which is GITIGNORED
    (never committed), so the journal-gate's "newer than the last commit" test does not
    transfer directly. Options: (a) mtime-vs-last-commit-time, (b) relocate the brief to
    a committed path, (c) a sentinel the seal writes. Must resolve before the hook.
  - Scope of enforcement: all sessions, or only orchestrator sessions? Builder sessions
    already have journal-gate; the brief is an orchestrator-specific artifact. Likely
    orchestrator-only, keyed on "bare session at root / no active-plan".
  - Artifact path: does a Stop-gate extension (it changes the enforcement contract,
    touches `.claude/hooks/**` — the machinery bp-072 deliberately excluded) warrant a
    design note, or is it a careful papercut like bp-072? Leaning: at least a light
    design note, because it is a new gate, not just a new script.
  - Interaction with delegated/worktree builders: does brief-enforcement fire in a
    worktree, or only the main checkout? (journal-gate is worktree-aware via _lib ROOT.)

next_steps:
  - Resolve the freshness-signal question (the gating design decision).
  - Decide the artifact route (design note vs papercut) and mint accordingly — the hook
    that enforces a fresh resume-brief on Stop, mirroring journal-gate.
  - Optional companion: the cockpit seal-motion keybind (parked above) if wanted alongside.

references:
  - docs/build-plans/bp-072/plan.md            # the cockpit this extends (COMPLETE)
  - .claude/hooks/                              # journal-gate — the enforcement pattern to mirror
  - .claude/state/resume-brief.md              # the artifact to enforce (NOTE: gitignored)
  - docs/brainstorms/usage-automation.md       # usage self-serve; scheduled ledger parked
  - .claude/skills/context-economy, .claude/skills/checkpoint  # the disposable-session discipline
```
