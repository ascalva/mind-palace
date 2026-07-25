---
type: finding
id: finding-0175
status: open
created: 2026-07-25
updated: 2026-07-25
links:
  - .claude/state/resume-brief.md                      # the artifact (gitignored — not in the tree)
  - scripts/docket.py                                  # the DERIVED-view precedent, with its falsifier
  - scripts/board.py                                   # the other derived view (TRACKS/DESKCHECK-QUEUE)
  - docs/findings/finding-0164.md                      # ALL ingest paths keep-and-link, never delete+replace
  - docs/findings/finding-0168.md                      # the vector plane is APPEND-ONLY
  - docs/design-notes/agent-workflow.md                # the handoff gate this artifact serves
ftype: spec-defect
origin_plan: orchestrator
route: orchestrator
resolution: null
---

# The resume brief is the last destructively-overwritten artifact in a system that has outlawed destructive overwrite

## What

**Owner, 2026-07-25:** *"I've come to realize that the handoff brief might be a limitation for you,
and it's continuously overwritten."*

Measured this session:

| property | `.claude/state/resume-brief.md` | `docket.md` / `TRACKS.md` / `DESKCHECK-QUEUE.md` |
|---|---|---|
| produced by | hand, by the orchestrator | **derived** (`docket.py`, `board.py --write`) |
| on update | **destructive overwrite** | recomputed from the artifact tree |
| can drift from source | **yes, silently** | **no — that is `docket.py`'s stated falsifier** |
| history | **none** | regenerable at any commit |
| size | **49,311 bytes** and growing within one session | ~9 KB, bounded by what is actually owed |
| in git | **NO — gitignored** | committed |
| in the corpus | **NO** | yes |

`scripts/docket.py`'s own docstring states the principle the brief violates: *"A DERIVED view,
recomputed from the artifact tree on every run: **NO persisted state, so it cannot drift (the
falsifier)**."* The brief is the only session-state artifact that is neither derived nor versioned.

## Why it matters

1. **It violates, at the session layer, the exact discipline the corpus now enforces.** finding-0164
   ruled that ALL ingest paths keep-and-link and never delete+replace; finding-0168 made the vector
   plane append-only with purge as the single owner-gated exception. The brief delete-and-replaces
   its entire contents on every update. **The system outlawed destructive overwrite everywhere
   except in the artifact that describes what the system is doing.**
2. **History is destroyed, so "what did we believe at 02:00?" is unanswerable.** Every superseded
   understanding — including wrong ones we later corrected — is gone. Tonight produced at least four
   corrections that would be worth replaying (the memory-ceiling claim, the co-residency claim, the
   Bloom-filter direction, "deploy is blocked on the seed"). None survive.
3. **⚑ IT BLOCKS THE THING THE OWNER JUST ASKED FOR.** Same message: *"we will need to also measure
   lag."* Detection lag = (claim made at T1) → (claim falsified at T2). **An append-only, timestamped
   state log IS the substrate that makes that computable**; a continuously-overwritten file makes it
   permanently unmeasurable. The reconciliation-audit's central model cannot become self-measuring
   while its input destroys itself.
4. **It is gitignored, so the palace is blind to its own session state.** A system that ingests its
   own code, transcripts, findings, and exhaust cannot see the one document that says what it is
   currently doing. Ouroboros does not eat this tail.
5. **Unbounded growth is a live context cost.** 49 KB re-read on every resume, growing with every
   semantic boundary, mixing four tiers in one flat document (live state · carry-forward · archive ·
   watchlist). The fresh-agent test is met by *volume* rather than by *structure* — which works until
   it doesn't, and degrades quietly on the way.

## The direction (owner-granted latitude, not yet designed)

**Owner, same message:** *"I'll allow you to develop a new system/format of update current state, I
guess similar to what we're doing with ouroboros."*

Apply the palace's own model to its session layer. Sketch only — this needs a design pass, and the
sketch must not be mistaken for a decision:

- **Append-only typed state events** at semantic boundaries, never a rewritten blob.
- **A derived current-state view** computed from those events plus the artifact tree — the
  `docket.py`/`board.py` pattern, with the same cannot-drift falsifier. Never hand-edited.
- **Supersession, not deletion** — a state entry that stops being true is superseded and retained,
  exactly as slot-lineages do for chunks (f-0168 addendum 1).
- **Ingested into the corpus** — it is arguably the highest-density record the system produces.
- **The watchlist as a first-class component** (see `docs/brainstorms/command-center.md`,
  2026-07-25): declared expectations are state, and they are what makes lag measurable.

## Re-entry condition

Not blocking anything: the current brief works, and bp-100/101/102 are in flight against it. Do NOT
build this while builders are running — it would change the handoff contract mid-wave. Re-entry: the
three builds merge and seal, THEN a design pass (it is workflow-layer, so it amends
`dn-agent-workflow` and belongs with the queued workflow-taxonomy pass rather than standing alone).

## Routing

`design` → orchestrator. It amends the agent-workflow design note (the handoff gate), so it goes
through the design pass + adversarial panel like any other note — **including this one's own
sketch, which is a proposal and not a ruling.** The owner has granted latitude to develop the
format; that grant is authority to DESIGN it, not to skip the gate.
