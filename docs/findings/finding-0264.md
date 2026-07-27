---
type: finding
id: finding-0264
status: open
created: 2026-07-27
updated: 2026-07-27
links:
  - docs/brainstorms/owner-intent-audit.md
  - .claude/skills/delegate/SKILL.md
  - docs/design-notes/dn-role-state-and-scoped-handoff.md
ftype: design
origin_plan: orchestrator
route: orchestrator
resolution: null
---

# The sub-orchestrator owns its wave's merge — a standing amendment to the delegation contract that is recorded nowhere

## What

On `2026-07-27T03:27:29Z` (session `61710eca`, row 1205, channel 1) the owner said:

> *"tell the sub-orchestrator to start spawning them as i bless them, sub-orchestrator will handle
> the merge and stand up its own auditor to review before merging, it manages the merge, not you"*

This is a **standing amendment to the delegation contract**, not a one-off instruction for one wave.
The prior rule — owner, 2026-07-11, and the `delegate` skill — is that the **orchestrator**
scrutinizes diffs pre-merge. He has now interposed a layer: the sub-orchestrator merges, and stands
up **its own** auditor.

The audit that recovered this (`docs/brainstorms/owner-intent-audit.md`, L-5) searched and found the
rule absent: `its own auditor` appears nowhere; `sub-orchestrator` appears only as narrative in
`docs/brainstorms/agent-interface-and-role-messaging.md` and in `finding-0235`, never as a rule.

`bp-125` has since written the operative half into the `delegate` skill, so it now loads at the
moment of use. **What remains open is whether the delegation _contract_ needs a formal amendment**,
and that is an owner-level call, not a builder's.

## Why it matters

⚑ **It was being obeyed purely from an agent's working memory.** When that agent's context ended,
the rule would have ended with it — which is precisely the failure class
`dn-role-state-and-scoped-handoff` was ratified to close. A rule that governs who may merge is a
gate-adjacent rule; carrying it in a transcript is the same defect the seat journal exists to fix.

⚑ **`[INFERENCE]` It raises a gate question nobody asked:** an auditor that a sub-orchestrator
spawns is **chosen by the thing it audits**. Independent convergence was the strongest evidence the
adversarial-panel process produced, and it was available only because the reviewers were
independent. A self-selected auditor does not obviously carry that property. This is flagged as an
inference drawn at audit time, not as something the owner said.

There is a second-order consequence already recorded in the seat journal: a fresh occupant's
instinct is to audit and merge, and that instinct is now **wrong** for a delegated wave. If a
sub-orchestrator dies mid-wave the correct move is to inspect the worktrees, say plainly what state
the wave is in, and ask the owner — never to silently take over. A half-merged wave is the bad
outcome.

## Re-entry condition

Reopens when the owner rules on either half: (a) whether the `delegate` skill entry is sufficient or
the delegation contract needs a formal, cited amendment; and (b) whether an auditor spawned by the
sub-orchestrator it audits satisfies the independence property the panel gate relies on. Until then
the operative rule stands as written in the `delegate` skill and is followed; nothing is blocked.

## Routing

`design` → the orchestrator. It is a candidate amendment to the `delegate` skill and to the
delegation contract, and skills are not a builder's surface. Batched to `owner-questions.md` only if
the owner's ruling on the independence half is wanted before the next delegated wave.
