# process-weight

Is the artifact chain a legal system? The owner's Kafka observation, what is actually load-bearing
about it, and the one test that separates law from ceremony.

## 2026-07-26T07:35:00Z

```capsule
topic: process-weight
date: 2026-07-26

decisions:
  - THE OBSERVATION (owner, 2026-07-26, verbatim): "sometimes this all feels like a kafka-esque
    bureaucratic legal system, where we have documents that preceed others, resolve contradictions,
    standings are held, most of the times our discussions is on how to disambiguate the idea."
    ⇒ Recorded as a first-class critique OF THE PROCESS LAYER, not an aside. The process layer has no
    other channel: findings critique the code, owner-questions ask for rulings, and nothing critiques
    the chain itself. That absence is itself a finding-shaped gap.
  - IT IS ACCURATE, AND THE SCALE IS MEASURABLE. As of this sweep: 210 findings · 48 owner questions ·
    amendments A1–A9 · three owner-only gates · a foundation denylist · one-way status machines on four
    artifact types · supersession chains with standing errata · 14 capsules on a single topic. The
    ratio of writing-about-work to work is real and nobody has ever measured it.
  - ⚑ BUT THE KAFKA DIAGNOSIS MISNAMES THE MECHANISM, AND THE DIFFERENCE IS OPERATIONAL, NOT
    FLATTERING. Kafka's bureaucracy has three properties: it is AUTHORLESS (no one chose it), it is
    UNAPPEALABLE (no one can repeal it), and it is PURPOSELESS (it serves no outcome). This chain has
    none of those: every gate has a named warrant finding, every amendment has a date and a ratifier,
    and any of it dies in one owner edit. What it actually resembles is COMMON LAW -- precedent,
    standing, contradiction resolution, and errata that stay inspectable rather than being quietly
    overwritten. That form was not chosen for ceremony; it is what a record must look like to stay
    reviewable BY SOMEONE WHO WAS NOT THERE.
  - ⚑⚑ AND THE ROOT CAUSE IS ONE ARCHITECTURAL CHOICE, NOT A TASTE FOR PROCESS: SESSIONS ARE
    DISPOSABLE AND CONTEXT DIES. In an ordinary codebase, disambiguation lives in a person's head for
    months and never gets written. Here it CANNOT -- the worker is amnesiac by construction, so an
    unwritten disambiguation is a lost one, and will be re-litigated at full cost by the next session.
    The artifact chain is therefore not overhead layered on the work; it is the MEMORY SUBSTRATE the
    work requires. ⇒ The weight is the price of disposability, and it is the same trade the project
    already accepted deliberately ("sessions are disposable, artifacts are not"). Kafka's clerks
    remember everything and demand the forms anyway. That is the distinction.
  - ⚑⚑ THAT SAID, THERE IS A GENUINE PATHOLOGY HERE, AND THIS SWEEP FOUND FOUR CASES OF IT. The
    failure mode is not "too much process" -- it is PROCESS ARTIFACTS THAT NO MECHANISM READS. Those
    are not law; they are forms filed into a drawer nobody opens, which is exactly the Kafkaesque part
    and is a bug class rather than a mood:
      · `scripts/board.py` parses `audit_refs` and nothing consumes it (finding-0208).
      · The "non-goals carry [INFERENCE]" rule has no home -- not in the template, not in any skill;
        it survives only in memory and hand-copied plan lines (finding-0150).
      · The builder-routed finding lane has no mechanism that ever closes it: 23 of 23 were mis-stated,
        13 orphaned and 10 fixed-but-still-open (finding-0209).
      · `docs/PROGRESS.md` is 12 completed plans behind; the checkpoint duty lapsed silently around
        session-43 and nothing noticed.
    Each is a rule that was WRITTEN and never WIRED -- the process-layer form of the project's own
    standing complaint that flag-off is not done.
  - ⚑ SO THE TEST, AND IT IS THE PROJECT'S OWN RULE POINTED AT ITSELF: **for every process artifact,
    name its reader.** A human who reads it at a decision point, or a script that consumes it. No
    reader ⇒ delete it, or wire it. "Structural enforcement, not convention" has been applied to code
    for months and never once to the chain that governs the code. Applied here it would have caught all
    four cases above, and it converts "is this too bureaucratic?" from a matter of taste into a
    question with an answer.
  - ⚑ THE DISAMBIGUATION RATIO IS A SIGNAL ABOUT THE ARTIFACTS, NOT ABOUT THE DOMAIN. If most
    discussion is disambiguation, the artifacts are under-specifying at capture time, or the vocabulary
    is bad. There is now a proven instance: `ftype` has TWO DISJOINT VOCABULARIES (finding-0193, batched
    this sweep as oq-0047) -- the process manufactured its own ambiguity, and every finding filed since
    has paid a small disambiguation tax for it. That is not the domain being hard; that is a defect.
  - HONEST SELF-CRITICISM, SAME SWEEP: this triage produced ELEVEN new owner questions. Every one is a
    form for the owner to fill. That is defensible only where the silent default is genuinely worse
    than the ask -- and for several of the eleven, the default is fine and the question is closer to
    ceremony than to a gate. A batch is not free just because each item is non-blocking.

parked:
  - decision: does the process layer get its own critique channel, or does `ftype` gain a `process`
    value so this class is filable as a finding?
    default: the latter -- a new artifact type would add weight to answer a complaint about weight,
    which is self-refuting. But it collides with oq-0047, so it must wait for that ruling.
    re_entry: oq-0047's answer.
  - decision: is the reader test enforced, or advisory?
    default: enforced where it is cheap -- a derived check that every declared field in a template has
    at least one consumer, in the same family as the orphan register finding-0209 asks for.
    re_entry: the workflow-taxonomy design pass.

open_questions:
  - What IS the healthy ratio of chain-work to build-work, and is it currently above it? Nothing
    measures this. The cost ledger measures token spend per plan but nothing measures spend per
    ARTIFACT TYPE, so "triage is expensive" is a feeling rather than a figure.
  - Would a smaller vocabulary genuinely reduce disambiguation, or just move it? oq-0047's option (c)
    (route on `route:` alone, let `ftype` be prose) is the minimal-vocabulary bet and would be the
    first real test of that hypothesis.
  - Is there any artifact type that could be RETIRED outright rather than trimmed? The chain has only
    ever grown. Nothing has ever been removed from it, which is itself suspicious.

next_steps:
  - No design note yet -- this needs the reader-test audit run first, so that any note is written
    against a measured list of unread artifacts rather than an impression.
  - Cheap and immediate: the four cases above are all filed. Wiring them is the concrete answer to the
    complaint, and it shrinks the chain rather than documenting it further.

references:
  - docs/findings/finding-0209.md          # the builder lane nothing ever closes (filed this sweep)
  - docs/findings/finding-0208.md          # audit_refs: parsed, never read
  - docs/findings/finding-0150.md          # a rule written and never wired
  - docs/findings/finding-0193.md          # the process manufacturing its own ambiguity → oq-0047
  - docs/design-notes/agent-workflow.md    # the chain being critiqued (ratified)
  - .claude/skills/context-economy/SKILL.md # "sessions are disposable, artifacts are not" -- the trade
```
