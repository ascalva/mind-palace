# commit-economy-and-the-succession-path

## 2026-07-27T04:10:00Z

```capsule
topic: commit-economy-and-the-succession-path
date: 2026-07-27
status: OWNER RULED — "move to succession plan" (2026-07-27). Scope AND ordering both pinned below.

seed (verbatim, 2026-07-27T02:44:42Z, session 61710eca row 974, queue channel): |
  "…we don't need to push every single build plan and design note, those become internal
  documents, and not for privacy reasons, but I don[']t [think] we need to commit every single time
  one of those documents is edited, that's why we can use ouroboros to find the succession path to
  prove: it would look like a more grounded way of proving internal documents, that eventually get
  graduated as code changes, feature additions, etc, no one's gonna read through our insanly large
  docs dir, starting to feel like overkill, we push every time a brainstorm is had? too much"

provenance: |
  LOST for ~1.5h and recovered by the owner-intent audit as L-1 — it arrived on the queue channel
  (typed mid-turn) riding behind "anyways, start minting build plans", and never got a turn of its
  own. The owner ruled on it immediately once surfaced. See [[owner-intent-audit]].
```

## THE CLAIM

Git is currently doing two jobs at once, and the ruling separates them:

| job | today | under the ruling |
|---|---|---|
| **durability** — the bytes survive | git | git (unchanged) |
| **proof of lineage** — *this* doc became *that* code | git history, read by a human | **ouroboros's retrieval — the succession path** |

⚑ **The load-bearing move is the second row.** The proposal is not "commit less to save effort" —
it is that **the system's own retrieval is a better proof of succession than the git trail**,
because it answers the question a human actually has (*what did this idea become?*) rather than the
question git answers (*what bytes changed at 03:14?*). Nobody reads a 5,600-line `PROGRESS.md` or a
docs dir this size; a succession query is read on demand and returns only the path.

## WHY THIS IS NOT A PROCESS NIT

`CLAUDE.md`'s artifact chain rests on *"no decision lives only in a transcript."* That premise is
about **durability**, and the ruling does not touch it — the files still exist. What the ruling
changes is **what git is asked to witness**. Those have been conflated because one mechanism served
both. Naming them apart is what makes the ruling coherent rather than a loosening.

## ⚑⚑ THE TENSION NOBODY HAS RAISED — this may decide the design

**The code sensor ingests commit bodies at commit time.** It is one of the corpus's richest inputs;
the feedback-loop baseline measured the ledger growing 1,204 → 1,230 in a single evening, *"most of
them my own prose about my own work"* ([[context-load-as-a-feedback-loop]], L5).

⇒ **Committing less means the corpus sees less of its own reasoning.** But the corpus is precisely
what the ruling nominates to *prove succession*. Taken naively, the proposal removes the evidence
that the substitute proof runs on.

`[INFERENCE]` This is not necessarily fatal, and there is an obvious repair: **decouple ingestion
from committing.** If the sensor read the artifacts themselves (and their edit events) rather than
commit bodies, the corpus would see *more*, not less — and the succession path would be built from
document lineage directly instead of from commit prose about it. That repair is unbuilt, unscoped,
and `[INFERENCE]` — the owner has not ruled on it. **It is the first thing to settle.**

## ⚑ THE DURABILITY QUESTION THIS OPENS

If a document is not committed, its only copy is a working file on one machine. Git is currently
also the **backup and the offsite**. A succession path proves *lineage*, not *survival* — an
un-pushed doc that the disk loses is gone, and the corpus's pointer to it dangles.

⇒ Any implementation needs an answer to *"what makes an uncommitted internal document durable?"*
Candidates, none ruled on: batch-commit at status transitions only; commit but do not **push**;
Syncthing/restic as the durability layer with git reserved for graduated code. `[INFERENCE]`

## ⚑⚑ RULED BY THE OWNER — 2026-07-27

**R1 — Scope: STATUS TRANSITIONS ONLY.** Plans and design notes commit at `draft→ratified`,
`proposed→ready`, and `→complete`. **Not** on every edit; journal checkpoints stop being a commit
each. Brainstorms **batch** rather than one commit per capture.

**R2 — Ordering: DECOUPLE THE SENSOR FIRST.** The code sensor is to read artifacts and their edit
events directly, rather than commit bodies, **before** committing is reduced. ⇒ The corpus ends up
seeing *more*, not less, and the succession path is built from document lineage instead of from
commit prose about it.

### ⚑ What R1 closes for free

Choosing the narrow scope **dissolves the two hardest open questions** rather than answering them —
worth recording, because a later revisit to the full retrieval-only variant re-opens both:

- **Durability is untouched.** Documents stay in git; git remains the backup and the offsite. The
  "what makes an uncommitted internal document durable?" problem does not arise.
- **The blessing gates keep their witness.** `draft→ratified` and `proposed→ready` are exactly the
  transitions that still commit, so an owner blessing is still evidenced by a commit and the
  constitution's two owner-only gates are unaffected.

### ⚑ The consequence to accept, stated plainly

**R2 gates R1 behind a build.** The docs-dir relief does not arrive until the sensor is decoupled —
which needs a design note, ratification, and graduation. Nothing about commit practice changes
before then. That is the owner's chosen ordering, not a scheduling accident.

## STILL OPEN

- **The sensor decoupling has no design note.** That is the next artifact, and it is the gate on
  everything else here. It must answer: what constitutes an *edit event*, how lineage is
  reconstructed without commit bodies, and how the succession path is queried.
- `[INFERENCE]` Whether **brainstorm batching** may proceed ahead of R2 as a carve-out — it is the
  one piece with almost no sensor coupling. Not ruled; do not assume.

## NOT DONE BY THIS CAPSULE

No practice changed. The live bp-125→127 wave continues committing under current rules — changing
commit discipline mid-wave would be applying a design change by side effect, which the chain
forbids. The natural boundary is **after bp-127 seals**.
