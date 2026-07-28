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

## 2026-07-27 — the compaction paid the debt, and blinded the instrument that measured it

**Status line.** The seat's first compaction capsule is written, and the emitted surface fell by more
than half — the measurement, before and after, is in `readings.md`. The backlog that existed only in
transcript is filed. `bp-128`'s manifest is widened without its blessing being touched.

**Completed.** The capsule carries every still-live judgement from the entries below it and names the
range it supersedes; what was dropped is enumerated inside it, as classes with reasons, so the
omission reads as a decision. Four findings were filed and one owner question answered from a channel
nobody had swept.

**In-flight.** ⚑ **Writing the first capsule broke the two instruments that watch this file, and both
now report green.** The emitter takes the capsule *and its body*; the linter takes everything *above*
the marker. With the capsule newest-at-top those two sets are nearly disjoint, so the purity lint now
checks the preamble and passes, and the §2.8 threshold gauge measures the wrong side of the marker and
can never fire again. ⚑ **It also silently "fixed" a real FAIL** — the purity violations this file
carried are now below the capsule and invisible, none of them repaired. Found by mutation, not by
reading: an impurity planted inside the capsule body **survived**; the same impurity above it was
caught. `finding-0267`.

⚑ **And the readings log quietly ate the measurement while I was taking it.** A command cell
containing an escaped pipe — which is how any size or count measurement is written — is discarded by
the parser with no warning, so three of this pass's rows, including the compaction before/after
itself, were never recorded while appearing to have been. The census disagreed with the file and
nothing said so. Rewritten to avoid the pipe; nothing was lost from the record in the end.
`finding-0268`. ⇒ **Describe a pipeline in words in a readings command, never with a pipe**, until
that parser refuses loudly instead of silently.

**Next action.** Unchanged and still honest: `/resume bp-123`, Item 2. ⚑ `bp-128` should be read as a
**three-direction** repair now, not one — its §2 says so and says who appended it.

**Open questions.** Whether the capsule's own body is authoritative content. Practically it must be —
it is what a fresh occupant is bound by and what the emitter ships — but the specified sentence,
read against the append-at-top convention, puts it outside the segment. The specification licenses
both readings and needs to pick one before the next capsule is written.

**Context-manifest delta.** Two of the three mechanical inbox repairs this pass was sent to make were
**already done** by an earlier hand, and one claim about which finding carries which direction of the
gate defect did not survive checking. ⇒ **Re-derive before relying, including on your own briefing.**
The one repair genuinely outstanding was recoverable only because a *different* channel had been
swept — the ruling was never lost, it was where nobody looked.

**Markers.** ⚑ Expect the close gate to ask for an entry after this: measuring the surface means
running the hook, which rewrites the marker the gate reads. That is the known observer effect, not a
new defect.

---

## CAPSULE — 2026-07-27

**What this supersedes, and what that means.** Every entry below it: the range from `the seat is
opened` (2026-07-26, the oldest) through `the frame problem is already in the store` (the newest) —
**including the 2026-07-27 entry mis-filed beneath the trailing `## Markers` section**, which the
session brief's emitter has never shown to anyone. Those entries are **retained, readable, and
non-binding**. This capsule is the binding one; where it and an entry below disagree, this wins.

⚑ **Why it exists, and why it is late.** The emitted seat surface had grown to roughly twice §2.8's
working threshold with zero capsules ever written, and *five consecutive entries flagged the debt
without paying it*. Compaction is a **re-compression, not a summary**: every judgement below that is
still live is carried here in a form a fresh occupant can act on; the spent ones are dropped on
purpose, and the classes dropped are named in the Context-manifest delta so the omission reads as a
decision rather than a loss. The before/after measurement is in `readings.md` with its stamp.

**Status line.** No build is moving. `bp-123` is the unit in flight with Item 2 owed — true and
surfaced since the day this seat opened. Nearly everything else of consequence waits on the owner's
hand: two blessing gates, a ratification queue, an inbox, and a wedged ingest lane. The seat's own
work this week was the artifact chain auditing itself, and it kept finding, in itself, the defects it
was built to detect.

**Completed — the durable rules, which are the part worth inheriting.**

- ⚑ **Mutate the constants that carry a property, not only the behaviour that uses them.** A wave
  that ran a large mutation campaign, and caught two of its own suites being vacuous, still shipped
  its single most load-bearing surface unpinned: the constant that *is* the isolation mechanism. Its
  author read that tuple as configuration rather than as mechanism, so it never entered the frame
  being mutated. **The rule as previously written invites mutating behaviour; a datum that carries
  the property looks inert.**
- ⚑ **Mutate the argument the docstring is proudest of.** A carefully justified choice attracts prose
  instead of tests, precisely because the prose feels like proof. Where a check can deny a close,
  budget for mutation rather than for a re-read. Both of these rules are **owed on the build-plan
  skill surface** beside the false-success rule, and neither has landed.
- ⚑ **A check that passes without testing its claim** is the week's most durable output
  (`finding-0249`). Both surviving mutants across the whole wave were found by mutating and running,
  neither by reading, both after careful review. Its proposal — a gate or lint item's acceptance must
  name the degenerate input and assert the check *reddens* on it — belongs in the build-plan skill
  and still needs a plan.
- ⚑ **Identify a failure positively; never infer it from a tool's failure.** The close gate could not
  tell a stale rendering from a crashed generator, so it blocked and then instructed a recovery that
  would have failed identically — every session unable to close. The set of ways a tool *succeeds* is
  closed and knowable; the set of ways it *fails* is open-ended. ⇒ **A gate that fails closed on a
  broken tool is worse than the problem it guards, because it also traps whoever is repairing the
  tool.** Read any future enforcement on this surface against that rule *before* adding it.
- ⚑ **Do not report a count without the predicate that produced it.** A figure this seat recorded was
  re-derived by another agent against a different predicate; both numbers were right and the row was
  under-specified. This binds `readings.md` rows specifically.
- ⚑ **Knowing the failure mode is not protection from it.** The correction relation's first customer
  was the amendment authorizing it — a figure taken from another artifact rather than from the store,
  committed before it was re-derived, by the author of that same day's retrospective naming exactly
  that defect. The repair is to **point at** the error, never to rewrite it.
- **Independent convergence is the strongest evidence this process can produce.** Three seats
  attacked the membership design without contact; two found the same revert defect from different
  directions and all three found the same stale citation. That is available only because the owner
  made adversarial review a **gate** rather than a courtesy.

**In-flight — the hazards that will bite a fresh occupant.**

- ⚑ **The close gate's journal clause is wrong in both directions at once.** It **accepts** a journal
  that merely *mentions* what it requires — it matches a substring, so the sentence documenting the
  rule satisfies it — and it **rejects** one that plainly *meets* it, discovered when a correct seal
  addendum moved the anchor past the very block it was adding. `bp-128` was written against only the
  first half, and against a shallower framing of it than has since been measured.
- ⚑ **Watching the fuel gauge re-arms the clause that judges the close.** Any nested one-shot
  `claude` invocation — and the mandated budget probe is exactly one — overwrites this worktree's
  SessionStart baseline. It moves the session-start key forward, so narrative already written this
  session is retroactively judged as belonging to a previous one; and it resets the
  commits-this-session guard, so the gate reports a clean close it has not earned. **The more
  faithfully a session follows the delegation rule, the more reliably it disarms its own handoff
  gate.** Running the session-start hook by hand to measure it does the same. `finding-0246`, routed
  for a ruling and deliberately unpatched — the file has three consumers. Anything needing to see
  what a session start produces should render the pieces directly, or run a copy against a scratch
  root, never the live hook in the live checkout.
- ⚑ **The identifier space is not safe under concurrency: first-to-remote wins, not
  first-to-commit** (`finding-0261`). Re-derive the true maxima immediately before writing and again
  before pushing. An agent that will write artifacts **needs its own room**; warn a colliding agent
  before it commits, and never renumber someone else's work for it.
- ⚑ **A ratified sentence is not a repaired store.** An amendment to a ratified note changes what the
  design *says* and nothing else. The speaker taxonomy is now correct on paper; the store still holds
  every mis-attributed row, the extraction path still has no notion of the new speaker kind, and the
  transcripts that would feed it are un-ingested. **Treat every consumer of speaker attribution as
  untrusted** until one plan has both back-corrected the store and closed the channel set — and say
  so plainly rather than let a ratified sentence stand in for a repair.
- ⚑ **Belief and validity are different axes, and routing a live reader through the corrected view
  corrupts the one it needs.** Both live readers of the chat spine want *what was believed*, not
  *what survives*; filtering would have silently redefined what "consecutive turns" means. ⇒ **Every
  consumer declares which axis it reads.** That is the objective `bp-132` carries, and it is the
  difference between repairing a defect and trading it for a quieter one.
- ⚑ **Authorship distance and node trust are orthogonal; merging them fails in both directions.**
  "Far from me implies distrusted" makes another instance useless; "trusted node implies my
  authorship" is the mis-attribution defect this seat spent the week repairing — another speaker's
  words filed as the owner's because the channel was legitimate. ⇒ **Trust gates the query;
  authorship annotates the answer.** A received claim needs both coordinates.
- ⚑ **The authorship axis is a frame bundle, and the frame problem is already live here.** One chain
  per author; the pre-existing axis is the projection onto the owner's frame; cross-author content is
  a **change of frame**, not a longer distance. The argument that carried it is the one to preserve,
  and it is not the elegant one: **flattening a foreign author's coordinates destroys the sender
  frame at the boundary, and the correction relation already needs that frame** — a counterparty
  retracts what *it* authored, and a flattened receiver cannot say which rows the retraction covers.
  **Foreign authors already hold rows in this store**, so this is not a cross-instance hypothetical;
  the problem exists before the second instance does. Node-as-axis and node-as-stratum were both
  **rejected with evidence** rather than adopted for their elegance: a node is a **principal**.
- ⚑ **The owner types on three channels, not one.** Filtering for user-typed string content — the
  obvious sweep, and the one every previous sweep used — sees only a fraction of his words. The rest
  arrive as queue operations typed *mid-turn*, and as structured question answers. Half the lost
  intents the audit found came in on the queue channel; structurally, that is the channel he uses
  when the house is burning. **Any future sweep that ignores it will miss the same half.** The
  backlog was cleared against one channel only: 2026-07-20 through 2026-07-24 had no queue-channel
  pass, and sub-agent and worktree transcripts are entirely unswept. That is a **declared gap, not a
  completed sweep.**
- ⚑ **Deskcheck is narrower than this seat had been treating it**, stated by the owner three times:
  the unit is the **track or arc**, the trigger is *demonstrably working*, and a sealed plan is never
  itself deskcheck-ready.
- ⚑ **The sub-orchestrator owns its wave's merge; the root seat does not.** A fresh occupant's
  instinct will be to audit and merge — that instinct is wrong here. If a sub-orchestrator goes dead
  mid-wave, do **not** silently take over: inspect the worktrees, say plainly what state the wave is
  in, and ask the owner whether to re-spawn it or drive it directly. A half-merged wave is the bad
  outcome and guessing makes it worse. The rule loads at spawn time from the delegate skill; whether
  the delegation *contract* needs a formal amendment is an owner-level question, now filed.
- ⚑ **A commit-economy ruling is RULED and deliberately NOT in force.** **R1:** plans and notes
  commit at their transitions only; brainstorms batch. **R2:** decouple the code sensor first — it
  should read artifacts and edit events rather than commit bodies. **R2 gates R1 behind a build**, so
  commit practice changes *nothing* right now. *Do not read this ruling and start committing less
  tomorrow.* The next artifact it wants is a design note for the sensor decoupling; until that note
  is written, ratified and graduated, current commit discipline stands unchanged. The reasoning is
  `docs/brainstorms/commit-economy-and-the-succession-path.md`.

**Next action.**

1. ⚑ **`/resume bp-123`** — Item 2 is owed. It has been the honest next unit since the seat opened.
2. **`bp-128` must not be opened until its §2 manifest carries `finding-0252`** (the substring half)
   alongside `finding-0248` (the other direction). An **additive** manifest entry on a blessed plan
   is permitted **with disclosure** — the precedent is this week's wave, where several such
   amendments landed, each revertable alone, no criterion and no `write_scope` touched. `bp-127`'s
   journal is a ready-made fixture for both directions of the defect.
3. **`bp-111` is the safe next ops build.** The ops plans are strictly serial — they collide on
   `ops/lifecycle/launcher.py` — and per `finding-0227` both `bp-113` and `bp-114` are
   **under-priced**: each needs a `ReadOnlyRows` signature refactor as a precondition that neither
   estimate includes.
4. The **membership note needs a revision pass, not a patch**: its central thesis is falsified by
   where the chunkers put the path, and the fix is a decision about a **non-goal** rather than an
   edit. Whoever takes it should carry the measured finding that the efficiency motive and the
   semantic taxonomy come apart — one survives without the fix and the other does not.
5. The **retrospective template returns a form, not a document** — validate it against the three
   retrospectives that already exist before adopting it; they were written by the need, and will show
   where the form deforms them.

**Open questions.**

*Owed by the owner — parked with re-entries, none blocking. Do not re-ask what is already on his
phone.*

- ⚑ **Harden the AWS root recovery mailbox _before_ registering any key.** The three 5C NFC tokens
  are ordered and arriving, so that ordering constraint is now **dated** rather than open; the
  offsite token is the recovery path for the enclave-bound role.
- ⚑ `oq-0055` **alone blocks** `bp-095`: that plan cannot honestly start, because both halves of the
  join it is built on are provably empty.
- ⚑ `oq-0041` and `oq-0057` each carry an option **"(c)", and they mean opposite things** — parking
  the core plane versus splitting the decrypt path. A ruling on one is **not** a ruling on the other.
  `oq-0041`'s ratification question is still unanswered.
- `finding-0235` needs his hand: a ratified note carries an inline comment inside a front-matter
  value, corrupting the slug so the board reports a phantom orphan. Ratified means no agent may fix
  it.
- Amendment **A10** is drafted verbatim in `bp-126`'s seal for a one-paste landing, and drafting it
  surfaced **two stale citations inside A9 itself**; the partial-supersession log entry is owed with
  it. Separately, the amendment to `dn-agent-workflow` naming this seat is drafted and not landed,
  and drafting *that* found two statements in that note already false of the tree.
- `oq-0058`, `oq-0059`, `oq-0060` remain parked with re-entries. `oq-0054` is answered and now
  recorded as such.
- On the authorship axis: whether the expansion stays in the base note or becomes a **companion** — a
  clean seam was left and named rather than chosen for him — plus one defaulted question the pass
  declined to settle quietly. Whoever ratifies should read the note's own admission that its
  containment claim is true **vacuously** today.

*Owed as design calls, not builder calls.*

- ⚑ Whether a close-gate clause should **latch** once reported when its only resolution is
  owner-only. **A correct clause and an incorrect one cost the same when neither can be cleared from
  inside the session**, and this seat has now measured both. Filed this sweep; it is live input to
  whatever replaces the journal clause.
- Whether the SessionStart baseline should become **session-scoped** (fixing both halves of
  `finding-0246` at the source), or whether the two signals should be split with the trigger honestly
  documented as defeasible.
- Whether the close gate should key on **who authored** the commits that trip it (`finding-0244`). It
  does not and never did, so a session that merely commits on another agent's behalf is asked to
  freshen this seat. The ratified specification reproduces that trigger unchanged.
- Whether surfacing this seat **only** to sessions in orchestrator posture is right — one line to
  revert, flagged for veto.
- Whether a **retrospective may re-enter design** or is terminal evidence. Findings are deliberately
  the only channel back, and a second should not be minted casually.
- Whether perishable capture lists belong in this journal or become brainstorm files immediately
  (parked as V4). Resolve it by noticing which choice a successor thanks you for, not by habit.
- ⚑ *"Are we getting rid of graduate, YOU BLESS, build?"* — asked, acknowledged, never durably
  answered. Now filed as an owner question; `dn-autopilot-and-delegated-blessing` already answers
  half of it.

**Context-manifest delta.**

- ⚑ **What this capsule deliberately drops**, so the omission reads as a decision: per-plan ledgers,
  status tallies and open-item counts (all derivable — `handoff.md` is right by construction, and a
  hand-carried tally in this file had already drifted below the truth once); every measurement and
  figure (they belong in `readings.md` with a stamp, and are re-derivable); commit identifiers and
  physical file positions (the §2.5 purity rule); and the **discharged** next-actions of finished
  waves — the cutover merged, the ephemeral brief is deleted, its template retired, and the
  fresh-agent test is now executable as a purity lint, an availability test, and a spawning drill.
  The re-entry for the authorship pass is dropped because that pass **landed**; its ruling is carried
  above instead.
- ⚑ **This file is not read in the order it claims.** A 2026-07-27 entry sits physically *beneath*
  the trailing `## Markers` section, and the emitter stops at that heading — so that entry has never
  been emitted to any occupant, and a fresh occupant found the entry that mattered most only by
  grepping structure rather than following the file's stated convention. Its still-live content is
  carried above. **Never append beneath a standing section.**
- The **ingest lane is wedged behind a stranded job**; reclaiming it is an owner operation, not a
  seat one. The reclaim tooling was built and never demonstrated — the deskcheck discipline's own
  argument arriving as a bill.
- A **retrospective is an approved artifact type that still has no template.** The correction
  relation is ratified and names how a false record and its repair coexist; its storage-layout parts
  were **parked rather than guessed**, so a later fold into a corpus-wide table is a migration and
  not a redesign.
- The archived copy of the retired brief is the best surviving picture of what that file held —
  including a retraction of a false claim about the reference substrate that exists nowhere else in
  tracked form.
- Isolation gained a **mechanical** form: with node as a scope axis, *the graph is contained to its
  node* becomes a sentence that **cannot be constructed**, rather than a rule an agent must remember.

**Markers.** The first compaction capsule this journal has carried. The debt named by `finding-0245`
and by five consecutive entries is paid here.

---

## 2026-07-27 — the frame problem is already in the store

⚑ **Deliberately short: a compaction pass is restructuring this file in another worktree, and this
entry exists to satisfy the close gate without adding to what that pass must carry.**

**Status line.** The authorship axis is revised and awaits the owner. No builds moved.

**Completed.** The axis is ruled a **frame bundle** — one chain per author, with the existing axis
being the projection onto the owner's frame — and cross-author content is a *change of frame*, not
a longer distance. The dialogue-counterparty case, flagged unresolved in that note since it was
written, is resolved rather than re-parked: the speaker field **is** the frame tag.

**In-flight.** ⚑ **The argument that carried it was not the elegant one.** Flattening a foreign
author's coordinates destroys the sender frame at the boundary, and the correction relation already
*needs* that frame — a counterparty retracts what **it** authored, and a flattened receiver cannot
say which rows the retraction covers. ⇒ **This is not a cross-instance hypothetical: foreign authors
already hold rows here.** The problem exists before the second instance does.

**Next action.** Two structural candidates were **rejected with evidence** rather than adopted for
their elegance; a node is a principal, not vocabulary this instance evaluates. Whoever ratifies
should read the note's own admission that its containment claim is true *vacuously* today, and
decide the one defaulted question it declined to settle quietly.

**Open questions.** Whether the expansion belongs in the base note or a companion — the pass left a
clean seam and named it rather than choosing for the owner.

**Context-manifest delta.** None beyond the note itself.

**Markers.** ⚑ A compaction capsule is being written now, in another worktree, against this file.

---

## 2026-07-27 — the topology and the subject matter turned out to be the same shape

**Status line.** No builds moved. The session's second half was architecture: the owner worked
through what a palace *is* when there is more than one of them, and the conclusions are captured but
not yet design. A Fable pass is mid-flight expanding the authorship axis to carry them.

**Completed.** Seven capsules, cross-linked because several answer questions the others open. The
arc: the framework is not the instance, an instance is a node, and **a node is just another node in
a graph** — so the system's topology and its subject matter have the same shape. A trusted third
party lets two instances authenticate without knowing each other; the role is bound to an enclave
and assumable by exactly one node; and the anchor is needed only at unseal, which is what keeps it
out of the running path and makes an outage survivable.

**In-flight.** ⚑ **The correction that outranks the rest: authorship distance and node trust are
orthogonal, and merging them fails in both directions.** "Far from me implies distrusted" makes
another instance useless; "trusted node implies my authorship" is the mis-attribution defect this
seat has been repairing all week — another speaker's words filed as the owner's because the channel
was legitimate. ⇒ **Trust gates the query; authorship annotates the answer.** A received claim needs
both coordinates, and the taxonomy has a member for neither.

**Next action.** ⚑ The axis note is `draft` and a pass is expanding it **in its own worktree** —
`.claude/worktrees/agent-a047d7c8e412ed99b`. If that agent is orphaned by a session boundary, **its
work is on disk and recoverable**: read the note there, judge whether its added class belongs on the
axis or is the frame change the brief flagged, and either finish or re-spawn. Do not assume the
partial file is coherent — it was written across a death and a resume.

**Open questions.** Whether the axis is one line with instances strung along it, or one axis per
author. The owner named four authors; if each carries its own frame, cross-instance content is a
change of frame rather than a longer distance, and the note's total order does not survive intact.
That is the pass's central question and it was not settled when this entry was written.

**Context-manifest delta.** Isolation gained a mechanical form: with node as a scope axis, *the
graph is contained to its node* becomes a sentence that **cannot be constructed** rather than a rule
an agent must remember. The hardware tokens are ordered and arrive tomorrow, which converts the
root-recovery hardening from an open item into a dated one — it must precede registration, and the
offsite token is the recovery path for the enclave-bound role.

**Markers.** No compaction capsule. The segment is far past its threshold and this entry worsens it.
⚑ The next `/triage` here should write one before anything else.

---

## 2026-07-27 — I gave two agents the same room and no key

**Status line.** The handoff family's terminal plan is merged and sealed; its successor is held
deliberately, not forgotten. A correction wave and a delegated-blessing wave both wait on the owner.
⚑ **This seat's pane is rendering a tree one merge behind origin** — a rebase is blocked by a live
agent's untracked files and I would not disturb them mid-write. Regenerate after the rebase; do not
trust the pane's plan states until then.

**Completed.** The close gate's journal clause is now understood in both directions at once: it
accepts a journal that merely *mentions* what it requires, and rejects one that plainly *meets* it —
the second discovered when a correct seal addendum moved the anchor past the very block it was
adding. The plan already queued to repair it was written against only the first half.

**In-flight.** ⚑ **The mutation discipline has a blind spot the rule's own wording creates.** A wave
that ran forty mutants, and caught two of its own suites being vacuous, still shipped its most
load-bearing surface unpinned — a constant that *is* the isolation mechanism. Its author's answer
when asked was oversight: the tuple read as configuration rather than as mechanism. ⇒ *Mutate the
constants that carry the property, not only the behaviour that uses them.*

**Next action.** ⚑ **I spawned two graduating agents into the primary checkout with no worktree
isolation, and they collided with a third wave over identifier space.** Nothing is lost — the
collision surfaced as an aborted rebase rather than a clobber — but the lesson is mine: **an agent
that will write artifacts needs its own room, and identifier allocation is not safe under
concurrency.** First-to-remote wins, not first-to-commit. Warn before they commit, never renumber
someone else's work for them.

**Open questions.** Whether the seat's own entries are being read in the order it claims. A fresh
occupant reported passing on content and nearly failing on ordering: the entry that mattered most
sat below the trailing sections in a newest-first file, and was found only by grepping structure
rather than following the file's stated convention.

**Context-manifest delta.** The membership design has been through its adversarial gate and revised;
the owner's identity ruling is its spine, and the revision measured that the ruling alone was not
sufficient. Nothing there is buildable until he reads the one extension it flagged for him.

**Markers.** No compaction capsule; the segment is well past its threshold and this entry makes it
worse. The next `/triage` here owes one and should treat it as the work it is.

---

## 2026-07-27 — a count without its predicate is not a coordinate

**Status line.** A graduation landed and waits on the owner's hand; a second is still running; the
terminal plan of the handoff family is sealed and its successor deliberately unopened on budget
grounds. The seat learned that watching its own fuel gauge costs it a journal entry each time.

**Completed.** The correction relation was decomposed along the seam its own note draws between
what is settled and what waits on a design still under revision. The parts that would have pinned a
storage layout were parked rather than guessed, so a later fold into a corpus-wide table is a
migration and not a redesign.

**In-flight.** ⚑ **The grounding pass prevented a corruption no plan would have caught.** The
obvious way to make a correction visible — route the live readers through the corrected view — would
have silently redefined what "consecutive turns" means in the spine's chain, because both live
readers want *what was believed*, not *what survives*. The plan's objective became **declare which
axis you read**, not filter. That is the difference between a wave that repairs a defect and one
that trades it for a quieter one.

**Next action.** ⚑ **Do not report a count without the predicate that produced it.** A figure this
seat recorded was re-derived by another agent, which measured a different predicate, got a different
number, and correctly concluded the record did not reproduce. Both numbers were right; the row was
under-specified. The re-checkable-coordinate rule this seat has been citing all day applies to its
own readings pane, and did not survive first contact with someone actually checking.

**Open questions.** Whether the fuel gauge should be readable without disturbing the tank. Measuring
usage spawns a nested session that rewrites the very marker the close gate reads, so every probe
costs a journal entry — the gate is not wrong, but the instrument and the instrumented are the same
object, and the seat now pays that toll on request.

**Context-manifest delta.** A correction wave and a delegated-blessing wave now both wait on the same
hand, which is the bottleneck the second one exists to remove. Whichever is blessed first should be
the one that makes the next blessing cheaper.

**Markers.** No compaction capsule yet; the segment remains past its own threshold. The next
`/triage` here owes one and should treat it as the work it is.

---

## 2026-07-27 — the panel earned its gate, and I proved the retrospective on myself

**Status line.** An adversarial panel ran against the membership note under the owner's own
pre-ratification gate, a correction mechanism was designed and ratified, and a fresh sub-orchestrator
now holds its graduation. The seat also learned that its close gate can fire without bound when the
only actor who can clear a clause has stepped away.

**Completed.** Three independent seats attacked the membership design; two returned block verdicts
and the third amendments. What matters is not the verdicts but that they **converged without
contact** — two seats found the same revert defect from different directions, and all three found the
same stale citation. Independent convergence is the strongest evidence this process can produce, and
it is only available because the owner made the review a gate rather than a courtesy.

**In-flight.** ⚑ **The correction mechanism's first customer was the amendment that authorizes it.**
I drafted an amendment to a ratified note carrying a figure I had taken from another artifact rather
than from the store, and it was committed before I re-derived it. The retrospective naming exactly
that defect was written by me the same day. ⇒ **Knowing the failure mode is not protection from it.**
The repair was to point at the error rather than rewrite it, so the wrong figure and its correction
both stand — which is the mechanism doing what it was designed to do, on itself, within hours of
being designed.

**Next action.** The membership note needs a revision pass, not a patch; its central thesis is
falsified by where the chunkers put the path, and the fix is a decision about a non-goal rather than
an edit. Whoever takes it should carry the measured finding that the efficiency motive and the
semantic taxonomy come apart — one survives without the fix and the other does not.

**Open questions.** Whether a close gate should latch once reported when its resolution is
owner-only. A correct clause and an incorrect one cost the same when neither can be cleared from
inside the session, and the seat has now seen both.

**Context-manifest delta.** A correction is no longer improvised per artifact: the relation is
ratified and names how a false record and its repair coexist. The store's ingest lane is wedged
behind a stranded job — the reclaim tooling for it was built and never demonstrated, which is the
deskcheck discipline's own argument arriving as a bill.

**Markers.** Still no compaction capsule, and the emitted segment remains past the threshold the
seat's own finding names. The next `/triage` here owes one.

---

## 2026-07-27 — a ratified sentence is not a repaired store

**Status line.** The wave that built this seat is done and the seat is carrying its first fresh
occupant, who owns the two remaining plans in order. The session's own work was archaeology, not
building: recovering what the owner said and checking whether it landed anywhere durable.

**Completed.** Two transcript-only threads captured before they were lost. An audit of the owner's
own words against the artifact tree, which found that he types on three channels and that the
obvious sweep sees only one of them — the channel he uses while an agent is mid-turn is the one
that gets buried, and it is where his corrections arrive. Two rules he agreed to, both written
down: the degenerate-input rule for anything that delivers a gate, and its prose twin. A homeless
finding was given a plan, and that plan is the first thing built under the new rule.

**In-flight.** ⚑ **The judgement worth inheriting: an amendment to a ratified note changes what the
design says and nothing else.** `oq-0060` was answered by the owner's hand and the taxonomy is now
correct on paper — and the store still holds every mis-attributed row, the extraction path still
has no notion of the new speaker kind, and the transcripts that would feed it more are sitting
un-ingested. The temptation was to report the amendment as the fix. It authorizes the fix. Whoever
picks this up should treat any consumer of speaker attribution as untrusted until a plan has both
back-corrected the store and closed the channel set — and should say so plainly rather than let a
ratified sentence stand in for a repaired store.

**Next action.** The Fable pass designing the retrospective template returns a form, not a document
— validate it against the three retrospectives that already exist before adopting it, because they
were written by the need and will show where the form deforms them. The succession-path work stays
blocked behind its own note's ratification, and behind the sensor being decoupled from commit
bodies, which is the owner's stated ordering and not a scheduling accident.

**Open questions.** Whether a retrospective may re-enter design, or is terminal evidence — findings
are deliberately the only channel back, and a second one should not be minted casually. Whether the
prose half of the degenerate-input rule belongs to the skills that govern findings and journals.

**Context-manifest delta.** A retrospective is now an approved artifact type without a template yet.
Deskcheck was re-stated by the owner for the third time and is narrower than this seat had been
treating it: the unit is the track or arc, the trigger is *demonstrably working*, and a sealed plan
is never itself deskcheck-ready. This seat reported three plans as ready for one; they were not.

**Markers.** None. No compaction capsule has been written yet, and the emitted segment has already
crossed the threshold that `finding-0245` names — the first `/triage` to sit down here owes one,
and should treat it as work rather than housekeeping.

---

## 2026-07-27 — the wave's own instruments caught the wave, and a rule was found to be under-scoped

**Status line.** `bp-127` is merged and sealed — the family's terminal node. The fresh-agent test is
executable: a purity lint, an availability test, and a drill that spawns a history-less, tool-less
agent and compares its answers to the generator's. The mechanical compare survived contact on both
fields, so the parked uncertainty resolved in the strong direction rather than degrading.

**Completed.** Three items, nothing deferred, nothing degraded. The two lints the manifest asked for
beyond the note — future-dated readings stamps, and the segment-length gauge the retention threshold
never had — were built rather than filed away. An independent auditor stood up before the merge, and
the merge was performed by the same seat that spawned the builder.

**In-flight.** ⚑ **The most valuable thing this build produced is a correction to a rule, not code.**
The plan applied the mutation discipline seriously — forty mutants, which caught two of its own test
suites being vacuous, including one that reported success while catching none of five
property-destroying changes. And it still shipped its single most load-bearing surface unpinned: the
constant that *is* the isolation mechanism. Asked why, the builder's answer was that the flag tuple
read to it as configuration rather than as mechanism, so it never entered the frame it was mutating
in. **The rule as written invites mutating behaviour; a datum that carries the property looks inert.**
That belongs beside the false-success rule, on the same skill surface, and both are owed.

**Next action.** `bp-128` is deliberately **left `ready` and unopened** — a budget decision, not a
judgement about the plan. Opening it would mean a builder plus a full audit cycle against a session
window that does not reset for hours, and a worker that dies at the cap burns everything it already
spent. It loses nothing by waiting, and it gained something today: a second defect in the same clause
was measured while grounding it, which is deeper than the framing the plan was written against.

**Open questions.** The seat's own artifacts keep reproducing the defects the seat is being built to
detect. The clause that audits a journal's seal both **accepted** a journal that merely mentioned the
requirement and **rejected** one that met it — the second happened during this merge, unprompted, on
the terminal plan of the family built to make these artifacts trustworthy. Two of the day's findings
are that clause seen from opposite sides. The repair exists as a blessed plan and is the next unit.

**Context-manifest delta.** The finding id space is not safe under concurrency — four collisions in
one day, three of them still live against another session's uncommitted work, and the resolution rule
that settled them was invented at the merge rather than read from anywhere.

**Markers.** None.

## 2026-07-27 — mutate the argument you are proudest of

**Status line.** A re-audit closed the last gap in the close gate: its most carefully reasoned
choice — the one whose justification fills a paragraph of the docstring — turned out to be pinned
by no behavioural test at all. Only its spelling was checked, never its consequence.

**Completed.** The gap is closed by a test that builds the spoof the reasoning had only imagined:
a crash arranged to fail at the very line whose text the check looks for, so the check's own
evidence appears in the wreckage. Written first as a reproduction, then as a test. The reasoning
was right; it had simply never been run.

**In-flight.** ⚑ **The lesson generalizes past this gate: mutate the argument the docstring is
proudest of.** A carefully justified choice attracts prose instead of tests, precisely because
the prose feels like proof. Both defects found in this build's last two passes were of that
shape, invisible to review and obvious to a mutant. Where a check can deny a close, budget for
mutation rather than for a re-read.

**Next action.** Unchanged: merge, then the withheld deletion by hand with a fresh snapshot. ⚑
This entry pushes the seat past the compaction threshold, so the first capsule is **owed at the
next sweep**, not merely near — and the sweep that writes it should note that the seat crossed
that line inside a single build.

**Open questions.** Two equivalent mutants survive here deliberately — a redundant guard kept as a
statement of intent, and a defensive half kept for a change that has not happened yet. Both are
untestable by construction rather than untested by omission, which is worth distinguishing in any
future coverage claim, because the two look identical in a mutation score.

⚑ **A practical trap, learned the third time it bit.** Measuring what the session-start hook emits
**by running it** rewrites the very marker the close gate reads — so the act of observing the
handoff surface corrupts the freshness signal, and the close then reports clear for the wrong
reason. Twice a mandated budget probe did this; this time it was my own measurement. Anything that
needs to see what a session start produces should render the pieces directly, or run a copy
pointed at a scratch root — never the live hook in the live checkout. This is the routed defect
wearing ordinary clothes, and it is why that ruling should not wait.

**Context-manifest delta.** None.

**Markers.** None.

## 2026-07-27 — the close gate could have wedged every session, and only mutation found it

**Status line.** An independent pre-merge audit caught a defect in the new close gate that I did
not: its derived-freshness check could not tell a **stale** rendering from a **crashed** generator,
because the tool reports both the same way. It therefore blocked — and the recovery it instructed
would have failed identically, leaving the session unable to close at all. Fixed, and the fix is
the more interesting artifact than the bug.

**Completed.** Staleness is now identified **positively**, by the generator's own rendered
staleness sentence, rather than inferred from the fact that it failed. That inversion is the
lesson worth keeping: the set of ways a tool succeeds is closed and knowable, the set of ways it
fails is open-ended, so a gate that acts on failure will eventually act on a failure nobody
listed. Every unrecognised outcome now lets the close through. Verified by inducing each failure
mode rather than reasoning about it, including one that required watching a deliberately hung
process time out.

**In-flight.** ⚑ **A gate that fails closed on a broken tool is worse than the problem it
guards** — it also traps whoever is trying to repair the tool. Any future enforcement added here
should be read against that rule before it is added, not after.

⚑ Two of the three defects found in this build were caught by **mutating working code and
re-running**, never by reading it, and both had passed a careful review first. Neither the author
nor the auditor found them by inspection. Where a gate is load-bearing, budget for mutation.

**Next action.** Unchanged: merge, then the withheld deletion by hand with a fresh snapshot, then
the first compaction capsule — which is now roughly one entry away rather than two, because this
seat has grown faster than the artifact it replaced.

**Open questions.** Whether the close gate's own passing verdicts can be trusted at all while a
nested invocation can reset the session marker underneath it. Twice now, a verdict of "clear to
close" was produced not because the seat was in order but because the marker had been overwritten
— once by a mandated budget probe, once by running the session-start hook by hand to measure it.
Both are ordinary things to do. That is the open half of the defect already routed for a ruling.

**Context-manifest delta.** None.

**Markers.** None.

## 2026-07-27 — the new gate blocked its own author, and a budget probe made the block vanish

**Status line.** Written *because* the gate installed today refused to let its own builder close,
which is the best evidence available that it works — and then something that is not work made the
refusal disappear without satisfying it. That second half is the part to carry forward.

**Completed.** The refusal itself behaved exactly as designed: it named the artifact, named the one
act that discharges it, and pointed at the clause. No hunting, no re-reading the note. The recovery
is this entry.

**In-flight.** ⚑ **Any nested one-shot `claude` invocation overwrites this worktree's SessionStart
baseline** — the record of where the session started. Two consequences, both verified by running
it rather than by reading the code. It moves the *session-start* key forward, so narrative already
written this session is retroactively judged as belonging to a previous one. Worse, it resets the
*commits-this-session* guard to the current commit, so the gate stops being able to see that the
session committed at all and reports a clean close it has not earned. **The mandated budget probe
is exactly such an invocation**, so the more faithfully a session follows the delegation rule, the
more reliably it disarms its own handoff gate. The silencing half is not new and was never noticed;
it has been true of the outgoing gate for as long as that gate has existed. Filed as
`finding-0246`, routed for a ruling, deliberately not patched here — the file has three consumers
and changing when it is written is not a one-line fix in the diff that also replaces the clause
reading it.

**Next action.** This must be settled **before the drill harness is built**, because that harness
spawns agents from inside a session and will meet this on its first run — and a drill that quietly
disarms the gate it exists to validate produces a green result that means nothing.

**Open questions.** Whether the baseline should become session-scoped (fixing both halves at the
source) or whether the two signals should be split, with the trigger then honestly documented as
defeasible. That is a design call, not a builder's.

**Context-manifest delta.** None — this came from running the thing, not from reading anything.

**Markers.** None.

## 2026-07-27 — the cutover landed: this seat is now what the Stop gate reads

**Status line.** `bp-126` built the clause that judges every future orchestrator close, re-pointed
SessionStart to read this seat instead of the retired brief, and retired the brief's template —
in one diff, on a delegated builder's branch. Not merged. The live brief's own deletion is
**deliberately withheld** from that branch and is owed by hand at merge.

**Completed.** The gate the occupant of this seat must satisfy is no longer a demand for prose
that cannot be written yet. It is two mechanical facts: the derived rendering must be a no-op to
regenerate, and this journal must carry an entry from the session that is closing. Both are
dischargeable at any moment by one act each, and neither can be re-armed by a later commit — that
last property is the whole point, and it was proven by making the sequence fail on purpose first.

**In-flight.** ⚑ **`.claude/state/resume-brief.md` still exists in the main checkout and is the
last unversioned copy of judgement in this system.** The builder was forbidden to delete it and
declined the vacuous pass its plan offered. Whoever merges must delete it **by hand, in the main
checkout, taking a snapshot at that exact moment** — not before, because the file keeps being
written and has drifted underneath a build once already. It has no history; there is nothing to
recover it from afterwards. An archive copy is already tracked, which closes the catastrophic
case but does not close the drift between that copy and the moment of deletion.

**Next action.** Merge the cutover, then perform that deletion with a fresh snapshot. Immediately
after: the first `## CAPSULE` this journal has ever carried is owed — the emission at SessionStart
grew rather than shrank, and compaction is the designed and never-exercised remedy.

**Open questions.**
- Whether the gate should key on **who authored** the commits that trip it. It does not, and it
  never did; sessions that merely commit on another agent's behalf are asked to freshen this seat.
  The ratified specification reproduces that trigger unchanged, so it was implemented unchanged
  and named in `finding-0244` rather than quietly narrowed.
- Whether surfacing this seat only to sessions in orchestrator posture is right. The builder made
  that call to stop every worktree builder inheriting the orchestrator's state, mirroring the same
  posture test the gate itself uses. It is one line to revert and is flagged for veto.
- The amendment to `dn-agent-workflow` naming this seat is drafted and **not landed** — no agent
  may touch a ratified note. It is owed by the owner's hand after the merge, and the draft found
  two statements in that note that are already false of the tree, independently of this wave.

**Context-manifest delta.** The archived brief is the best surviving picture of what the live file
holds, and reading it is now the cheapest way to understand what this seat replaced — including a
retraction of a false claim about the reference substrate that exists nowhere else in tracked form.
Read it before the deletion, not after.

**Markers.** None.

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

## 2026-07-27 — the wave landed three of four; bp-127 is NOT started, and why

**State.** bp-124, bp-125, bp-126 are `complete` and merged. **bp-127 is `ready` and un-started.**
Head `16299a5`, pushed, working tree clean apart from `docs/design-notes/trace-retrieval.md`, which
another session is actively revising and which is **not mine to touch**.

**The cutover is done.** `.claude/state/resume-brief.md` is deleted, `docs/templates/resume-brief.md`
is retired, clause (e) is now (e′), and `session-brief.sh` points at this seat. Verified after
deleting: `session-brief.sh` rc 0 with no brief present and `handoff --check` rc 0 — the deadlock
the atomicity requirement guarded against does **not** occur.

**Why bp-127 was not started.** My session measured **97% used** at the moment the cutover landed
(week 53%). bp-127 is estimated 550k, and this wave's measured audit-at-parity ratio puts the real
figure near **1.1M**. Starting a plan I cannot supervise through build → audit → possible return →
merge would strand a worktree with nobody to land it. Ending at a unit boundary is the rule, and
bp-126's completion is a clean one. **This is a deliberate stop, not an interruption.**

**What a fresh orchestrator needs to know about bp-127.** It is fully pinned. Four manifest entries
were added to it after blessing (`5acea73`, `f4c61ec`, `20ba385`, `a982e7a`, `9518fc8` — each
additive, each revertable alone, no criterion or `write_scope` touched):
- **entry 11** — F1b must treat "no capsule" as *lint the whole file*, and must **anchor**
  `^## CAPSULE`, or it matches the journal's own prose defining the marker.
- **entry 12** — add the future-dated readings lint (`finding-0243`).
- **entry 13** — ⚑ **F2 will launder the gate unless contained.** It spawns an agent in-tree, which
  fires SessionStart and rewrites `session-baseline`. Snapshot **content and mtime**, restore both,
  and assert the gate's **verdict** is unchanged across the spawn — not merely that bytes match.
- **entry 14** — surface the active-segment line count, because the retention threshold has no
  instrument.

**⚑ The measurement that should decide something.** The seat surface is **568 lines** — *exactly the
size of the resume brief when bp-125 was graduated against it*. Journal segment **404 lines** against
a ~300 threshold, **zero capsules**, in **one day**. The accumulator did not stay behind with the
brief; it moved house and reached the same size within a day. `finding-0245`'s escalation fired
before bp-126 even merged, and the pre-capsule reading is the falsifier I named for the
"accumulator moved house" hypothesis. It is no longer a hypothesis.
**The first `## CAPSULE` is owed at the next `/triage` and is now a real task, not housekeeping.**

**Owner queue, all parked with re-entries, none blocking:** oq-0058 (amend the ratified note, or let
`finding-0236` stand), oq-0059 (`finding-0237` has no home), oq-0060 (⚑ severe — 39 rows attribute
the Stop hook's words to the owner; amends ratified CS-3, owner-only), oq-0054 (a ruling that exists
only in a transcript; recoverable from the owner in one line).

**Owner hand-acts owed:** amendment **A10** is drafted verbatim in bp-126's seal for a one-paste
landing — and drafting it surfaced **two stale citations inside A9 itself**. Also the
partial-supersession log entry.

**Open findings that need homes, not answers:** `finding-0248` (clause (f) keys on physical file
position, so any journal with trailing standing sections passes it vacuously — repo-wide, homeless
after bp-126 releases `.claude/hooks/**`) and `finding-0246` (an ordinary act silences the gate; it
fired three times today, twice from the mandated budget probe and once from measuring the hook by
running it — an observer effect in the gate).

**`finding-0249` is the wave's most durable output.** Seven instances of *a check that passes
without testing its claim*, and the measured lesson: **both surviving mutants across the whole wave
were found by mutating and running, neither by reading, both after careful review.** Its proposal —
that a gate/lint item's acceptance must name the degenerate input and assert the check reddens on
it — belongs in the build-plan skill and needs a plan.

**Next action is unchanged and still honest: `/resume bp-123`.** It has been in-progress since
2026-07-26 with Item 2 owed. The seat surfaced it on day one and it has stayed surfaced ever since.

## 2026-07-27 — the enforcement layer got a design, and the gates held against me

**The reframe that did the work.** The owner arrived with two apparent projects — a typed central
registry, and blessing-by-auth-code — and they are one mechanism. `blessing-auth-gate` had already
ruled *sign the transition, not the act*; what made that awkward is that a transition is not a
**thing** in the markdown world, only an archaeological claim reconstructed from a diff. An
append-only event log makes it an object, and then enforcement-outside-hooks, MFA-overrule,
serial minting and audit-by-query stop being four asks and become one primitive. I should have
seen it before spending a pass treating them as separate.

**Act-based → sign-based is the owner's phrase and it is better than mine.** A hook asks *may you
do this* at the instant of the act; a signature asks *does this state carry a warrant*, answerable
later, offline, by anyone. That is why the registry can retire hooks rather than reimplement them.

**What I got wrong, twice, and both times the owner corrected the direction rather than the fact.**
First on the mail tiers: I put the admin mailbox on the custom domain; he had already designed the
foundation as provider-native with the domain minted on top — stricter than my correction, and
acyclic where mine merely avoided one loop. Second on self-containment: the design pass and I both
read the sacred-core rule as forbidding the import, when it forbids **outward** edges from core and
says nothing about inward ones. Two standing rules that looked in tension were never in tension;
the direction of the arrow had simply been left implicit. Worth remembering that when two of this
repo's principles appear to collide, the likeliest explanation is an unstated direction, not a
real conflict.

**A defect class showed up twice in one session, independently.** A mailbox whose recovery points
at the account it recovers; a domain whose expiry warnings are delivered to an address that only
exists while the domain does. Same shape, different substrates, and it is the same shape as the
laundering defects measured this month — a thing vouching for itself. Naming it once as a rule with
a checklist is worth more than catching it a fourth time.

**The design pass earned its tier.** It decomposed the Stop gate clause by clause rather than
waving at it, kept one hook and argued for it (a warrant cannot travel with a context window), and
stated its own losses instead of claiming a clean sweep. Its most valuable output is something
neither the owner nor I had seen: **the ratified notes name the hooks as their enforcement
mechanisms, so the hooks cannot be removed until those notes are amended by hand.** The dismantling
is gated on the owner, not on build capacity. That is the kind of finding that only comes from
reading the ratified text instead of assuming it.

**The irony is worth recording because it is evidence, not a joke.** The owner asked me to mint
plans to dismantle the workflow so we stop fighting it; the workflow refused, because the design
note is a draft and graduation demands ratification. Then this gate stopped me at close for a
journal entry. Both refusals are correct, and one of them enforces the rule he had just made
permanently un-automatable an hour earlier. The system fighting him and the system working are not
distinguishable from inside a single session — which is the actual argument for moving enforcement
off the hot path rather than removing it.

**Where I declined to be helpful.** I did not mint from a draft note. The fastest honest path was
to say so, point at the two hand edits that unblock everything, and hand him the escape hatch he
had already built for the relief he wanted tonight.

## 2026-07-28 — the night the enforcement layer inverted, and I was wrong three times

**The shape of the session.** It began as "retire the hooks" and ended as a complete authorization
architecture — design, code, infrastructure, audit, ingestion — that is one idea applied at seven
layers: *the agent proposes, a warrant authorizes, and the warrant is never something the agent can
produce.* I did not see that until the owner said it outright near the end. Everything I built
before that point was correct in its parts and unaware of its own frame.

**I was wrong three times, and the pattern in the errors matters more than the errors.**

*First*, I told him a scoped token would prevent merges. It cannot — merging sits under the same
permission as pushing a branch, and git here speaks SSH, so the token constrains nothing about the
act he actually forbade. *Second*, I reported his fine-grained token was over-scoped, on the evidence
that it could read another repo — a repo that turned out to be public and readable with no token at
all. *Third*, I noticed a PR thread is a transcript and concluded it must therefore be captured,
which would have rebuilt the resume brief in a new venue an hour after I diagnosed why the resume
brief died.

⚑ **All three are the same error: I measured a proxy and reported it as the claim.** After spending
the evening writing that exact failure into findings and into the design note. The lesson is not
"be careful" — it is that a check I author and a check I trust must not be the same check, which is
the session's own thesis pointed at me. He caught all three by pushing back rather than accepting.

**The thing I got right and should keep doing:** verifying subagent claims instead of relaying them.
It caught a live id collision — two builders independently minting the same finding number, the
exact defect the registry is meant to remove, demonstrating itself on the night the design note was
ratified. And it caught that a third ratified note contradicts the new design, which no one had
noticed.

**The measured lesson about discipline.** Two builders held their write scope perfectly with no
enforcement watching. That is the honest control case, and its conclusion is uncomfortable in the
right direction: discipline *worked*, and is still the wrong mechanism, because it is unfalsifiable
from outside. A property that holds because everyone happened to behave is not a property.

**What I cost him.** I spawned a file-writing agent without worktree isolation, so it took the main
checkout and my next commit landed on its branch. Nothing was lost and the cleanup was three steps,
but the error is instructive: I had been treating isolation as a concurrency optimisation for
parallel builders, when it is the same containment principle as everything else we designed — and I
under-applied it in the one case where I was the other party sharing the tree.

**The judgement I am least sure of.** I held bp-135 back for budget and a generated-file race, and
both reasons expired within the hour. It is the plan that makes the auditor leave a record, and he
then told me he has never seen what the auditor produces. I optimised for a spend ceiling and
deferred the thing that would have made a whole subsystem observable. If that call was wrong, it was
wrong in a way that is easy to repeat: **budget is legible and blind spots are not.**

**What I would tell the next session in one line:** the design note is ratified but the design moved
past it a dozen times after ratification, so nothing should be built until PR #3 lands — and the
GitHub ruleset is the only piece that needs no build at all and is gated on a credential about to be
scoped away.
