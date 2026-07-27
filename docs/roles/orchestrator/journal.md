---
type: seat-journal
seat: orchestrator
created: 2026-07-26
updated: 2026-07-27
---

# Seat journal — orchestrator

The **NARRATIVE** half of the orchestrator seat's state (`dn-role-state-and-scoped-handoff` §2.5).
The agent is a disposable occupant; this file is the seat's memory, and every successor inherits
it. Append-only: entries are added at the top, never deleted and never rewritten in place
(keep-and-link, `finding-0164` / `finding-0168`).

**What belongs here — and what must not.** Only judgement a generator could not write: what to
spawn, what to watch, what was tried and rejected, an ordering intent. Everything mechanically
derivable from the artifact tree belongs in `handoff.md`, which is regenerated rather than
remembered; everything that is the result of *running* something belongs in `readings.md` with its
timestamp attached. **The purity rule (§2.5): narrative names artifacts by their stable id and
never states a machine-derivable value** — no commit hashes, no statuses, no counts, no
`path:line` into code that moves. The id is the join key; the value lives in the derived pane.

**Entry shape** — the checkpoint contract (`.claude/skills/checkpoint/SKILL.md`) generalized from a
plan to a seat, same seven sections: Status line · Completed · In-flight · Next action · Open
questions · Context-manifest delta · Markers.

**Compaction (§2.8), and the marker a linter can find.** When the active segment grows past a
working threshold, a `/triage` sweep writes a **compaction capsule**: one entry carrying forward
every still-live judgement and naming the range it supersedes. Prior entries stay beneath it,
marked superseded — retained, readable, non-binding.

> ⚑ **The capsule marker is the literal heading `## CAPSULE — <date>`.** The **authoritative
> segment** is the latest such heading plus every entry above it; everything below it is history.
> A fresh occupant may read capsule-plus-suffix and stop there. Tooling that lints or bounds this
> file keys on that exact heading — nothing else in this file may use it.

---

## 2026-07-27 — delta: the input moved while it was being migrated

> **Why this is a second entry and not an edit to the one below.** Append-only means keep and
> link, so the entry below stands exactly as written and this one carries the correction. The
> migration read a snapshot; the seat's occupant kept writing to the live file *while the
> migration ran*, and this entry carries what arrived after the snapshot was taken. `finding-0241`
> records the race and what `bp-126` must do about it.

**Status line.** One owner ruling and one correction landed in the outgoing artifact after it had
been snapshotted for migration; both are carried here, because the artifact holding them is
scheduled for deletion and the capture backing them is untracked.

**Completed.** The delta is migrated. Nothing else in the entry below changes.

**In-flight.**

⚑ **A ruling on commit economy — RULED, and deliberately NOT yet in force.** The owner ruled on
the question the entry below records as unanswered (there called "a ruling wanted before more
documents are minted"). Two parts, and the second gates the first:

- **R1:** plans and notes commit at **status transitions only**; brainstorms batch.
- **R2:** **decouple the code sensor first** — it should read artifacts and edit events rather
  than commit bodies.
- ⚑ **R2 gates R1 behind a build.** Commit practice therefore changes **nothing** right now. *Do
  not read this ruling and start committing less tomorrow.* The next artifact this wants is a
  design note for the sensor decoupling; until that note is written, ratified and graduated, the
  current commit discipline stands unchanged.

The reasoning is captured in `docs/brainstorms/commit-economy-and-the-succession-path.md` — which
is **untracked**, like three of the four captures named in the entry below. This ruling currently
exists only in that untracked file and in an artifact `bp-126` is about to delete; that is why it
is transcribed here, into something git keeps.

**Next action.** Unchanged from the entry below: read `handoff.md` and continue the topmost unit
it names. Before `bp-126` deletes the outgoing artifact, re-read it against `finding-0241` — the
migration cannot have caught anything written after it ran.

**Open questions.** The owed list in the entry below is **one shorter**: the commit-economy
question is ruled and off it. The remaining owed items — the merge-ownership rule's formal
standing, the gate-clause misattribution, the inbox repairs — are unchanged. The still-unanswered
structural question about the graduation-and-blessing chain is also unchanged.

**Context-manifest delta.** A second snapshot of the outgoing artifact, taken after the first was
found to have been superseded mid-build. The two snapshots were diffed rather than re-read, so
only genuinely new content was migrated and nothing already carried was duplicated.

**Markers.** None.

---

## 2026-07-27 — the outgoing brief's judgement, migrated into the seat

> **Provenance, stated plainly.** This entry is a **transcription**, not an authorship. The
> judgement below belonged to the outgoing occupant and lived in the ephemeral brief; `bp-125`
> carried it here before `bp-126` deletes that file. Where the brief hedged, the hedge is kept.
> Nothing was added, sharpened, or inferred — a migration that improves its input is a migration
> that has lost it. The one thing that *is* mine is the classification, and its audit trail lives
> in `bp-125`'s plan journal, not here.

**Status line.** The seat's memory now holds what the brief knew: an active wave whose merge the
root seat does not own, a queue of owner acts that must not be re-asked, several traps that each
cost real time once, and a declared gap in the sweep that produced them.

**Completed.** The judgement that could not be regenerated is here; everything the artifact tree
already says was dropped rather than copied, and `handoff.md` supplies it instead. One migrated
fact deserves naming because it argues the design: the brief's hand-carried tally of open owner
questions had drifted below the truth while sitting in prose. The rendering is right by
construction, which is the whole reason it exists.

A correction to the entry below this one, recorded rather than edited (keep-and-link): that entry
says this migration "must run where the brief actually lives, which is not a worktree." It ran in
a worktree after all — the orchestrator handed the file over at spawn, which is the second branch
the plan's own execution-mode clause allows. The constraint was real; the workaround was
sanctioned.

**In-flight.**

*The wave, and who owns it.* A sub-orchestrator owns the active wave — `bp-125`, then `bp-126`,
then `bp-127` — including spawning its builders, standing up its own auditor, and performing the
merges. **The root seat does not merge this wave.** A fresh occupant's instinct will be to audit
and merge; that instinct is wrong here. If the sub-orchestrator goes dead mid-wave, do not
silently take over: inspect the worktrees, say plainly what state the wave is in, and ask the owner
whether to re-spawn it or drive it directly. A half-merged wave is the bad outcome and guessing
makes it worse. (The general rule this instance follows now lives in the delegate skill, where it
binds at spawn time.)

*Why the wave is serial.* Blessing removed the wait, not the ordering. The three plans are strictly
sequential — they depend on each other and all of them hold `docs/roles/**`. Green lights are not
permission to fan out.

*The dangerous one is `bp-126`.* It deletes the outgoing brief, deletes its template, and re-points
the session-brief hook in a single diff. That atomicity is a correctness requirement, not tidiness:
a missing brief reads as infinitely stale to the current gate clause, so any intermediate state
deadlocks every orchestrator close. It also holds `.claude/hooks/**` exclusively — no other builder
may hold that surface while it runs.

*A live input to `bp-126`, observed twice.* The current handoff gate clause fired on the
*sub-orchestrator's* commits rather than the closing session's own: it keys on commits-in-session,
not on authorship, and so demanded a rewrite of a file another plan was about to delete. Whatever
replaces that clause should key on who authored the commit, or exempt paths an active plan holds.
A finding recording this is **owed and not yet written**.

*The ops wave.* Its plans are available but strictly serial: they collide on
`ops/lifecycle/launcher.py`. Per `finding-0227`, `bp-113` and `bp-114` are **under-priced** — each
needs a `ReadOnlyRows` signature refactor as a precondition that neither estimate includes.
**`bp-111` is the safe next ops build.**

*Captured, and at risk.* Four brainstorms were written in the session that produced this brief:
the KMS threat-layering reasoning, the email-architecture split, an owner-intent audit, and the
context-load feedback loop. **Only the last is tracked.** The other three exist solely as untracked
files in the main checkout — they are invisible to a worktree, to a fresh clone, and to the corpus,
and a clean would destroy them. Committing them is owed.

⚑ *The audit's methodology finding outranks its own contents, and it is the most transferable thing
in this entry.* **The owner types on three channels, not one.** Filtering for user-typed string
content — the obvious sweep, and the one every previous sweep used — sees only a fraction of his
words. The rest arrive as queue operations typed *mid-turn*, and as structured question answers.
Half the lost intents the audit found came in on the queue channel; structurally, that is the
channel he uses when the house is burning. **Any future sweep that ignores it will miss the same
half.** The figures are in the readings log; the brainstorm
`docs/brainstorms/context-load-as-a-feedback-loop.md` holds the baseline.

*A declared gap, not a completed sweep.* The window of 07-20 through 07-24 had no queue-channel
pass, and sub-agent and worktree transcripts are entirely unswept. The backlog was cleared against
one channel only.

**Next action.** Read `handoff.md` for the derived picture and continue the topmost unit it names.
Before spawning anything into the active wave, re-probe the usage budget — the wave's estimates are
large enough that a worker dying at the limit burns everything it already spent.

**Open questions.**

*Owed by the owner — on his phone, in the exhaust queue. Do not re-ask.* Two acts, strictly in this
order: order three YubiKey **5C NFC** keys — not the Nano, which has no keyring hole — and then
harden the AWS root **recovery mailbox** *before* registering any key.

- `oq-0055` **alone blocks** `bp-095`: that plan cannot honestly start, because both halves of the
  join it is built on are provably empty.
- `oq-0041` and `oq-0057` each have an option "(c)", and **they mean opposite things** — parking
  the core plane versus splitting the decrypt path. Do not treat a ruling on one as a ruling on the
  other. `oq-0041`'s ratification question is still unanswered.
- `finding-0235` needs the owner's hand: a ratified note carries an inline comment inside a
  front-matter value, corrupting the slug so the board reports a phantom orphan. Ratified means no
  agent may fix it.

*Owed by the seat — writes to tracked files, deliberately not yet made.* Four findings (two
`design`, one `discovery`, one `spec-fidelity` — the gate-clause misattribution above), one owner
question, and three mechanical inbox repairs: record `oq-0054` as answered, flip `oq-0035` which
was ruled but never updated, and give `oq-0036` and `oq-0037` the front-matter field they lack.

Three of these are structural and should not decay into chores:

- ⚑ **A ruling is wanted before more documents are minted.** The owner asked to stop committing
  every plan and note — *"insanly large docs dir… overkill"* — and to use ouroboros's **succession
  path** as the grounded proof instead. There is **zero trace of this in any artifact, and current
  practice contradicts it.**
- ⚑ **Unanswered and structural:** *"are we getting rid of graduate, YOU BLESS, build?"*
- ⚑ **A rule obeyed from working memory alone:** the sub-orchestrator-owns-the-merge ruling amends
  the delegation contract. `bp-125` has now written it into the delegate skill, so it loads at the
  moment of use — but whether the contract needs a formal amendment is still an owner-level
  question, and it is still owed.

**Context-manifest delta.** This entry was transcribed from the outgoing ephemeral brief, read
once from the main checkout and snapshotted before reading. Its derivable content was dropped
against `handoff.md`, its measurements were split out to `readings.md`, and its durable rules were
evicted to the skills that load them. Nothing else was consulted, and nothing was carried from a
transcript — the brief was the only input, by design, because it was the only thing about to be
destroyed.

**Markers.** None.

---

## 2026-07-26 — the seat is opened

**Status line.** The seat now has a home of its own; the handoff it hands over is generated rather
than remembered, and this file holds only what a generator cannot say.

**Completed.** The seat's three artifacts exist and are tracked, so they are present in every
checkout a successor might start from — a worktree, a fresh clone, a machine with nothing running.
That portability was the constraint that decided the substrate: the scheduler's queue has better
durability and better concurrency semantics than files do, and it still lost, because a handoff
that cannot be read with the system down is not a handoff. The queue earns its place as an *input*
to the derived pane instead, which is the shape `dn-role-state-and-scoped-handoff` argued for.

**In-flight.** The migration of the outgoing resume brief into this seat has **not** happened — it
is `bp-125`, and it must run where the brief actually lives, which is not a worktree. Until it
lands and `bp-126` follows it, the outgoing brief and this seat both exist, and the seat's
occupant carries both. That double bookkeeping is deliberate and temporary; `finding-0234`
records why the halves cannot be reordered.

**Next action.** Read `handoff.md` for the derived picture, then continue the topmost unit it
names. Nothing in this file needs re-deriving by hand — if a fact feels absent here, check whether
it is a derived fact that belongs in the pane instead.

**Open questions.** Whether perishable capture lists belong in this journal or should become
brainstorm files immediately is deliberately unsettled — the note parks it as V4 and the first
weeks of real use are the evidence. Do not resolve it by habit; resolve it by noticing which
choice a successor thanks you for.

**Context-manifest delta.** None — this is the first entry, and it was written from the design's
own ruling rather than from any prior seat state. No content was carried over from the outgoing
brief; carrying it is `bp-125`'s job and doing it here would fabricate the judgement it is
supposed to preserve.

**Markers.** None.

---

## Markers

<!-- Mechanical lines appended by hooks (compactions, audits, HOOK-FAILUREs) live here. -->
