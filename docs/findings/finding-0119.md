---
type: finding
id: finding-0119
status: open
created: 2026-07-20
updated: 2026-07-20
links:
  - CLAUDE.md                                          # "two blessing gates are owner-only, by hand"
  - docs/design-notes/agent-workflow.md                # the workflow constitution this bears on
  - .claude/hooks/_lib.py                              # cmd_stop_audit (c) / _untracked_blessing / gate-check
  - .claude/hooks/gate-guard.sh                        # pre-hoc blessing-transition denial
  - docs/design-notes/session-handoff-gate.md          # the Stop-gate family this extends
re_entry: null
ftype: discovery
origin_plan: orchestrator
route: orchestrator
resolution: null
---

# The mint→bless→commit handoff is clumsy — an untracked bless welds two actors' commits into one un-committable state

## What
Observed live this session (session-37, re-graduating bp-076 → bp-078). The normal
blessing sequence is **two commits by two actors, in order**:

1. orchestrator commits the plan at `status: proposed` (the *mint*);
2. owner runs the ceremony and hand-commits the `proposed → ready` diff (the *bless*).

The gates assume that order structurally: `gate-guard` denies an agent flipping
status (pre-hoc); the Stop-gate `_untracked_blessing` (`_lib.py:551`) treats an
**untracked file already at `ready`** as a "blessing from nothing" and blocks close;
a *committed* blessing "self-clears" because it is accountable to its commit author
(`_lib.py:647-669`).

This session the order **collapsed**: the owner blessed (hand-edited `status: ready`
on disk) **before** the orchestrator had committed the `proposed` mint. The observable
consequences, each a papercut:

- **The mint and the bless welded into one untracked state.** bp-078 exists only as
  an untracked file at `ready` — there is no committed `proposed` predecessor, so the
  bless is not a clean tracked diff but a from-nothing creation.
- **No clean single-actor path to commit it.** The orchestrator cannot commit "the
  mint at proposed" (disk says `ready`, and reverting the owner's hand-edit is
  disallowed). The owner can commit it, but as an *entire new file*, not the small
  `proposed → ready` diff the lazygit ceremony is built around.
- **The "commit everything else, I'll bless-commit the plan" dance.** The orchestrator
  had to partial-commit (the capture + the bp-076 supersession) while manually
  excluding the untracked plan dir — a single `git add -A` would have laundered the
  blessing. The safe path depended on the agent remembering to stage by explicit path.
- **A cross-actor Stop-gate stall.** After the agent's commits, the Stop-gate clause
  (c) correctly flags bp-078 as an untracked blessing — but the agent *cannot* clear
  it (committing = laundering; reverting = destroying the owner's bless). It clears
  only when the *other* actor (the owner) commits. The gate fires on a state that is
  correct-and-pending, not wrong.

## Why it matters
None of this is a correctness bug — every gate did its job and the sacred boundary
held. But the friction is a recurring tax on the single most important handoff in the
system (the owner's authorization edge), and friction on a safety ceremony is where
mistakes get made: the one place a tired agent could `git add -A` and launder a
blessing is exactly this seam. A ceremony that is clumsy under normal, interleaved use
invites a shortcut that defeats it.

## Root cause — an impedance mismatch between two models of "blessing"
- **Git's model:** a blessing is a *diff* (`proposed → ready`) on a *tracked* file,
  accountable to its commit author.
- **The filesystem reality:** status lives in front-matter the owner hand-edits at any
  moment, decoupled from commit boundaries. The owner blesses *when he reads it* —
  which may be before the mint is committed.

Nothing forces the mint to be committed before the bless can be applied. When the
owner blesses an uncommitted mint, the two acts collapse into one untracked
from-nothing blessing that no clean single-actor path can commit.

## Candidate refinements (for the owner to weigh — this touches the sacred ceremony)
1. **Graduation always commits the `proposed` mint immediately** (orchestrator
   discipline, possibly a workflow amendment). Then the owner's bless is *forever* a
   clean 1-line tracked diff — the normal, gate-friendly path — and the collapse is
   impossible at the source. Cheapest fix; changes only *when* the mint is committed.
2. **Make `palace bless <id>` the single atomic ceremony.** One command: verify the
   plan is `proposed` (mint-and-stage it if untracked), flip to `ready`, stage ONLY
   that plan, hand the commit to the owner to sign. Ordering can't collapse because the
   mint-if-needed + flip + stage are one step. (`palace bless` is already referenced in
   prior briefs — this hardens it against the untracked-at-`ready` case and makes it the
   sole path.)
3. **A `commit-nonbless` staging helper** so "commit everything else" is not a manual
   landmine — stage all changes EXCEPT untracked/uncommitted blessing transitions, so
   the agent structurally *cannot* launder even with a fat-fingered `add`.
4. **(Rejected-leaning) teach the Stop-gate to downgrade** a same-session
   owner-present untracked-ready plan from block to reminder. Fragile — the gate can't
   read intent, and weakening a safety gate to paper over an ordering bug is the wrong
   direction. Prefer fixing the order (1) over softening the gate.

Recommendation: **(1) + (2)** — graduation commits the mint so the bless is always a
tracked diff, and `palace bless` becomes the one atomic owner path. Together they
dissolve the collapse rather than detect it.

## Re-entry condition
N/A (not parked — a standing discovery awaiting an owner ruling at /triage). If the
owner elects a refinement, it graduates: option 1 → an `agent-workflow.md` amendment
(warrant = this finding); option 2/3 → a small build plan for the `palace` CLI. This
finding then flips to `promoted`.

## Routing
`discovery`, `route: orchestrator`. It bears on the owner-sacred blessing ceremony, so
it needs owner input — batch to `owner-questions.md` at the next /triage with the four
candidates above; the recommended (1)+(2) is a design amendment / small CLI build, both
warrant-linked here.
