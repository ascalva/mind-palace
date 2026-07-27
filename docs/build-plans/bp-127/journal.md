---
type: journal
plan: bp-127
started: null
updated: 2026-07-26
---

# Journal — bp-127 (the fresh-agent test made executable: F1b, F1c, and the F2 drill)

Minted 2026-07-26 by `/graduate`, decomposing ratified `dn-role-state-and-scoped-handoff`
(blessed `c0abfd1`). Fourth and terminal of four (bp-124…bp-127). **Not started.**

## Pre-build notes for whoever picks this up

- ⚑ **READ bp-124's JOURNAL FIRST.** It records whether `next_action` proved derivable from the
  tree. **That is V1** (note §2.12). If it did not, the mechanical compare cannot cover field
  (2) and F2 degrades to judge-only — and **the plan must say so**, in this journal, in the
  harness's own output, and in a finding. Do not re-litigate it; do not loosen the compare until
  it passes. A test tuned until green cannot fail, which is the one thing a falsifier must do.
- ⚑ **THE DRILL'S OWN FALSIFIER IS THE FIRST THING TO BUILD, NOT THE LAST.** Put a fact **only**
  in a repo file outside the bundle and confirm the spawned agent reports `BLOCKED:` on it rather
  than answering. If it answers, the agent is reading the repo, the drill is testing nothing, and
  every future PASS manufactures false confidence — strictly worse than having no drill.
- ⚑ **The spawn mechanism is NOT grounded in the tree.** `scripts/orchestrator-launch.sh:47,89,91`
  shows `claude --model … --effort … --permission-mode …` — **interactive**. Nothing in the tree
  demonstrates a non-interactive one-shot, a no-history guarantee, or tool restriction, and
  §2.11 requires all three. Establish them empirically as Item 17's first act, record the finding
  as a MEASURED reading, and if a history-less bundle-restricted spawn is unachievable, **file a
  finding and ship Items 15–16 only.** Partial and honest beats complete and hollow.
- **F1a is NOT in this plan.** It is `scripts/handoff.py --check`, built in bp-124 and consumed by
  clause (e′) in bp-126. **Call it; never re-implement it.** Three copies of one check is the DRY
  defect the owner treats as a bug, and the whole point of F1a is that the gate and the drill are
  provably the same check.
- **The capsule marker may be undefined** (§3 Q1). The authoritative segment is "the latest
  capsule plus all entries after it" (note §2.8), but no capsule has ever been written. Read
  **bp-125's journal** for the marker it established; if it established none, define one, state it
  here, and file a `codebase` finding so the artifact and the lint cannot drift apart.
- **F1b's word boundary is load-bearing.** `\b[0-9a-f]{7,40}\b` — without `\b` the pattern matches
  hex letter runs inside ordinary words, the lint fires on legitimate narrative, and people learn
  to ignore it. Ids (`bp-110`, `finding-0227`, `oq-0051`) are **never** violations; they are the
  join key.
- **Be honest about F1b's tier.** It is tier 4 for the lintable class **only** (note residual R2).
  Its output and docstring must say so. An agent can still smuggle a count in prose — only review
  or the drill catches that.
- **F1c must use a REAL fresh worktree**, the `tests/integration/test_worktree_enforcement.py`
  pattern — not a mocked filesystem. A mock cannot falsify a claim about what exists in a
  checkout, which is the entire point of the test.
- **A `BLOCKED:` line whose answer is genuinely absent is a PASS with a defect report**, never a
  failure. The drill's job is to *find* under-specified state.
- **No skill edits, no CI wiring, no gate change.** Two documentation duties surface here — the
  drill's cadence and a checkpoint pointer — and both are **filed for the orchestrator**, because
  this plan does not hold `.claude/skills/**`.

## Owed at seal (orchestrator, not the builder)

- A `## Follow-through` block is required by clause (f) (`.claude/hooks/_lib.py:929-937`).
- ⚑ **V1's verdict, stated plainly**: did the mechanical JSON compare survive contact, or did F2
  degrade to judge-only? This is the note's explicit "the plan must say so" obligation.
- The **measured per-run cost** of one F2 drill. The note claims a cadence of "every `/triage`";
  if the cost makes that implausible, the cadence claim is not credible and needs a finding.
- The **spawn mechanism** actually used, as a MEASURED reading — so the next author does not
  rediscover it.
- Whether the seat artifacts were genuinely **present in a fresh worktree** (Item 16). If not,
  the note's §2.7 versioning ruling was never actually built and the finding routes to
  bp-124/bp-125.
- The drill's **cadence obligation** and the **checkpoint pointer** (§4) — filed here for the
  orchestrator to route into the skills, since this plan does not hold that surface.
- With this plan the note's §4 enablement is complete **except the owner's two hand-acts**:
  amendment A10 (finding-0233) and the first live session that resumes from `handoff.md` + the
  journal alone and says so (note §4(c)).
