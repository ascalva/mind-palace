---
type: finding
id: finding-0175
status: promoted
created: 2026-07-25
updated: 2026-07-27
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
resolution: promoted into docs/design-notes/role-state-and-scoped-handoff.md (ratified 2026-07-26), which carries this finding as its `warrant:`. Its append-only direction lands in §2.7 (the seat is versioned, the sitting is not) and §2.8 (compaction by supersession capsule, keep-and-link); the migration of the live artifact is bp-125. Prior state, kept for the record — "routed — durable claims hold; TWO table cells are factually wrong and the bp-100/101/102 gate has OPENED"
---

# The resume brief is the last destructively-overwritten artifact in a system that has outlawed destructive overwrite

> **Triage 2026-07-26 (session-52) — claims hold; the comparison table has two wrong cells.** The
> durable defect is real: the brief is hand-produced, destructively overwritten, historyless, and
> gitignored (`.claude/state/.gitignore:5`), consumed by `session-brief.sh:39,46` and demanded by
> `_lib.py:909-917`. No append-only state log exists.
> **⚑ WRONG ROWS — fix before the design note quotes this table:**
> 1. **`docket.md`** is listed `in git: yes` / `in the corpus: yes`. **Both false.**
>    `docs/inbox/docket.md` does not exist; `docket.py --write` targets `.claude/state/docket.md`
>    (`scripts/docket.py:20`), which the same `*` ignore rule covers. It is derived-but-**un**versioned.
> 2. **`size: 49,311 bytes`** is a session-instantaneous reading, not a property (the brief is 9,363
>    bytes right now). Say *"unbounded within a session"* instead.
> **The honest framing:** *derived* and *versioned* are two **independent** axes. `TRACKS.md` and
> `DESKCHECK-QUEUE.md` are genuinely both (GENERATED banners **and** `git ls-files`); the brief fails
> both; `docket.md` fails only the second. Split the table into two columns.
> **⚑ The gate has OPENED:** the re-entry *"do NOT build while builders run; bp-100/101/102 must merge
> first"* is **satisfied** — all three are `complete`. Record that rather than leaving a stale
> precondition standing. The note amends **ratified** `dn-agent-workflow`, so it must be a new or
> superseding note, never an edit.

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
