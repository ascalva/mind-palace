---
type: finding
id: finding-0245
status: open
created: 2026-07-27
updated: 2026-07-27
links:
  - docs/design-notes/role-state-and-scoped-handoff.md   # §2.8 compaction, §2.9 the artifact set
  - docs/brainstorms/context-load-as-a-feedback-loop.md  # the wave's warrant, and its baseline
  - docs/build-plans/bp-126/plan.md
  - .claude/hooks/session-brief.sh
  - docs/roles/orchestrator/journal.md
ftype: discovery
origin_plan: bp-126
route: orchestrator
resolution: null
---

# The cutover makes SessionStart 56% heavier, not lighter — measured at the moment of the swap,
# and the designed remedy (§2.8 compaction) has never been exercised

## What

`bp-126` Item 13 replaces the SessionStart emission of a 163-line resume brief with the
orchestrator seat's two halves. Measured on this branch by running the hook itself
(`bash .claude/hooks/session-brief.sh --standalone`, with and without the seat present, so the
difference isolates the seat surface from the rest of the brief):

| surface | lines | bytes |
|---|---|---|
| the retired brief, as archived (`docs/archive/resume-brief-final-2026-07-27.md` front matter) | 163 | 11,622 |
| `docs/roles/orchestrator/handoff.md` (DERIVED) | 74 | 4,800 |
| the seat journal's authoritative segment (NARRATIVE) | 212 | ~13,200 |
| **seat surface emitted at SessionStart** | **287** | **18,074** |
| **delta** | **+124 (+76%)** | **+6,452 (+56%)** |

The whole hook now emits 294 lines / 19,926 bytes in orchestrator posture, of which 7 lines are
the `SESSION BRIEF` block and the deskcheck line.

**The cause is not a defect in the implementation — it is that the designed bound has never been
applied.** §2.8 specifies compaction: at a `/triage` sweep, when the active segment exceeds a
working threshold (*"default ~300 lines, a number chosen to keep the resume read under one
screen-minute"*), a **compaction capsule** carries forward every still-live judgement and names
the range it supersedes. `grep -c '^## CAPSULE' docs/roles/orchestrator/journal.md` → **0**. The
seat journal has never been compacted; the file is 250 lines old and its active segment is 212,
i.e. **~70% of the way to the threshold after three entries and one day of life**.

## Why it matters

This wave's warrant is context load. `finding-0175` and the brief's own history are the argument:
it reached 568 lines, fired the stale gate 19 times in one session, and contradicted itself four
times while being edited to remove staleness. `docs/brainstorms/context-load-as-a-feedback-loop.md`
frames the whole thing as *the system's first measured feedback loop, with a baseline*.

So a cutover that lands a **56% larger** SessionStart payload, in the wave whose premise is that
the payload is the problem, must not go unstated. Three things follow:

1. **The trade is still favourable, and this finding does not argue against the cutover.** The
   brief was destructively rewritten, gitignored, historyless, hand-authored and provably
   self-contradicting; the seat is append-only, versioned, partly generated, and typed. Paying
   more bytes for an artifact with history is the trade the note makes knowingly. The point is
   that the trade should be **stated in measurements**, not asserted as an improvement.
2. **The growth curve is worse than the level.** The brief was bounded by destructive rewrite —
   ugly, but self-limiting. The seat journal is append-only, so it grows monotonically until
   something compacts it. A mechanism that has never run is not yet known to work.
3. **The compaction trigger has no owner in the loop.** §2.8 says "at a `/triage` sweep"; nothing
   measures the segment length, nothing surfaces it, and nothing blocks on it. Compare clause
   (e′), which is enforced structurally. The bound on the seat journal is, today, convention —
   the exact posture `MEMORY.md`'s "structural enforcement" rule warns about.

## What was done in `bp-126`, and what was not

Done: two lines of the emission were trimmed on their merits — the front matter and preamble are
skipped (they are not entries), and the trailing `## Markers` section is skipped (a mechanical
hook log, not judgement; it also carried the literal string `HOOK-FAILURE` into every brief). The
surface is posture-gated so builder worktrees receive none of it.

**Not done, deliberately:** no truncation, no line cap, no "latest N entries" heuristic. §2.8
pins compaction-by-supersession as *the* retention mechanism precisely so that bounding never
silently drops judgement, and a hook that truncated the segment would be a second, weaker
retention policy competing with the ratified one. Bounding this belongs at `/triage`, in the
artifact, not in the emission.

## Re-entry condition

**Re-enter at the next `/triage` after this merge.** Two concrete acts, either of which discharges
this finding:

- **(a)** Write the first `## CAPSULE — <date>` entry to `docs/roles/orchestrator/journal.md`,
  carrying forward every still-live judgement and naming the range it supersedes, then re-measure
  the seat surface with the same command used here. Discharged when the emitted segment is back
  at or below the retired brief's 163 lines. **This also exercises the capsule path for the first
  time** — which `bp-127`'s F1b lint depends on and which no artifact has yet produced (and note
  `finding-0242`'s trap: the capsule regex must be heading-anchored, because the preamble names
  the marker in prose).
- **(b)** Rule that the growth is acceptable and record the threshold that would change the
  answer — in which case the ask becomes a *measurement*, not a compaction: surface the active
  segment's line count somewhere an orchestrator sees it (the DERIVED pane is the natural home,
  and it is derivable from the artifact tree, so it does not violate the §2.9 purity pin).

⚑ Re-enter **immediately, ahead of `/triage`,** if the segment passes ~300 lines.

### ⚑ Addendum — this finding went stale in its own favour before the branch even merged

Re-measured at the branch tip, after the two further seat entries this build wrote (the audit
response and the `finding-0246` discovery), by the same method:

| | lines | bytes |
|---|---|---|
| seat surface at the seal | 287 | 18,074 |
| **seat surface at the tip** | **366** | **23,852** |
| against the retired brief | **+203 (+125%)** | **+12,230 (+105%)** |

The emitted segment is now **286 lines** and `grep -c '^## CAPSULE'` is still **0**. The ~300-line
threshold in §2.8 is therefore **roughly one entry away, at merge** — not two. The growth rate
this finding estimated (~70 lines per entry) held exactly, which is the part worth noting: the
curve is predictable, so the trigger date is predictable, and there is no reason to be surprised
by it. **The first capsule is owed at the first `/triage` after merge, not at the second.**

## Routing

`discovery` → **orchestrator**. Compaction is a `/triage` act on an artifact the orchestrator
owns; no owner input is required by either discharging form. The only part that could reach the
owner is (b)'s threshold ruling, and a default is already recorded in the note (~300 lines,
explicitly *"a knob, not an invariant"*).
