# role-state-and-scoped-handoff

## 2026-07-26T00:00:00Z

```capsule
topic: role-state-and-scoped-handoff
date: 2026-07-26

seed: |
  Owner, correcting the orchestrator's misreading of "routed to that builder's state": "I meant the
  ROLE's state, orchestrators come and go, but the state stays and is managed by every succeeding
  agent, assuming the role."

  Then, authorising the work: "commence the design/build/audit for fixing the resume handoff bug,
  and not just fix it, rewrite it entirely, make it robust, and states can be scoped to a specific
  queue/topic/role, that is how handoffs can be performed efficiently, and you could even use the
  scheduler's queue."

⚑ the reframe, and it is the load-bearing idea: |
  The agent is a disposable OCCUPANT of a persistent SEAT. What survives is the seat's state, and
  every successor inherits it. The system already does this in three places without ever naming it:

    orchestrator  ->  .claude/state/resume-brief.md  +  docs/PROGRESS.md
    scheduler     ->  data/queue.sqlite  (survives every restart; genuinely durable role state)
    plan work     ->  docs/build-plans/<id>/journal.md

  finding-0175 has been displaced ELEVEN times because it kept being framed as "the brief has a
  format problem" — a chore. The real statement is **ROLE STATE IS UNTYPED**, which is a design
  question and is writable. The reframe is what unblocks the note.

⚑ singleton vs plural roles — the distinction that makes scoping work: |
  - SINGLETON roles (orchestrator, scheduler): exactly one at a time, single-writer of named files.
    A role-scoped state and a role inbox are both well-defined. `orchestrator@` has one seat.
  - PLURAL roles (builders): several run concurrently on different plans. There is NO "the builder",
    so a builder-role inbox has no well-defined delivery target. Their state belongs to the PLAN,
    not the role — which is exactly why the journal is per-plan.
  ⇒ Addressing that works: role for singletons (`orchestrator@`, `scheduler@`), ARTIFACT for plural
  work (`bp-110@`). This also settles the earlier role-email thread's ambiguity.

the defect being fixed, stated precisely:
  - ⚑ A CIRCULAR DEPENDENCY IS BAKED INTO THE FORMAT. The brief must cite final commit hashes, but
    commits land after it is written, so it is stale the moment anything else happens. Clause (e)
    fired ELEVEN times in session-54 alone; session-52 rewrote its brief five times; session-53 four.
    That is not carelessness — the format demands a fact it cannot yet contain.
  - It is ~400 lines, paid on every session start, and it MIXES perishable state with durable rules.
    The rules rot in place: on 2026-07-26 it wrongly claimed bp-111..119 still needed blessing (done
    days earlier) and that the gate had ONE expected failure (it had two).
  - ⚑ Orchestrator role state is SPLIT across a gitignored file and a git-tracked one with no stated
    rule about what belongs where. That is how the brief came to assert things PROGRESS.md would
    have contradicted. It is also the only role state that is not versioned, while every plural-role
    journal is.
  - It is GLOBAL, not scoped: a builder resuming bp-110 must read a 400-line orchestrator brief that
    is ~95% irrelevant to it.

⚑ the three-way split that dissolves the circularity: |
    DERIVED   (generated, always true)  hashes, plan statuses, finding/deskcheck counts, in-flight
                                        agents, the gate reading. `scripts/board.py` already does
                                        exactly this for TRACKS.md / DESKCHECK-QUEUE.md, which are
                                        DERIVED and never hand-edited. Same pattern, wider scope.
    NARRATIVE (hand-written judgement)  what I was thinking, what to watch out for, what I would do
                                        next, which traps are live. The part no generator can write.
    RULES     (not here at all)         durable discipline belongs in skills/hooks that load AT THE
                                        MOMENT OF USE. Proven: the `git add -A` and `-F -` rules
                                        moved into the commit skill and have held since; the same
                                        rules failed repeatedly while they lived in this brief.

  ⇒ Clause (e) becomes satisfiable BY CONSTRUCTION: the derived half regenerates after the last
  commit, so it can never lag it. Only the narrative half is hand-written, and it contains no
  machine-derivable fact to go stale.

on using the scheduler's queue — genuinely attractive, with one hard constraint:
  - It already has durability, ordering, claim/lease semantics (bp-109), checkpointing and a tested
    state machine over 302,010 real rows. The ambassador capture independently reached the same
    place: "the scheduler already owns a job queue; a message is a job."
  - ⚑ BUT: THE HANDOFF MUST BE READABLE WITH NO RUNNING SYSTEM. A fresh agent, a fresh worktree, a
    crashed daemon, or a machine where the daemon is simply DOWN (as it is right now — deploy gate
    1) must still be able to resume. A handoff that lives only in SQLite is unreadable exactly when
    it is most needed. The current plain file survives all of those.
  - ⇒ Likely resolution: the queue (or any structured store) is the SOURCE; a generated file is the
    RENDERING; the rendering is what the fresh-agent test reads. Availability under failure is the
    requirement the queue does not by itself satisfy.

⚑ the falsifier, and it already exists as a stated bar: |
  The CHECKPOINT skill's fresh-agent test — "a new session with only plan + journal + write-scope
  files must continue without re-asking." Make it executable: spawn a genuinely fresh agent with
  ONLY the generated handoff and see whether it continues without asking. That is a real acceptance
  criterion rather than a subjective read of whether the prose seems good.
  ⚑ A broken handoff is INVISIBLE until a session fails, which is why this needs a falsifier and
  not an eyeball.

open_questions:
  - What is the scope key? `role:orchestrator` · `plan:bp-110` · `topic:secrets-custody`? Topics
    cross-cut plans (the KMS work spans oq-0041/0057, findings 0232, and a future note), which is
    exactly the case a per-plan journal handles badly today.
  - Does role state become VERSIONED? The brief is deliberately gitignored, but it is the only role
    state that is not — and the split is currently unstated rather than decided.
  - Does this subsume the resume brief, PROGRESS.md, and the owner queue as three renderings of one
    scoped store, or do they stay separate artifacts with separate lifecycles?
  - Retention: a journal grows forever. Does role state compact, and if so what is authoritative
    after compaction?

next_steps:
  - A DESIGN NOTE (`draft`) — this is design-tier work; the owner ratifies by hand.
  - Then `/graduate` into plans (`proposed`), owner blessing, build, and a recorded audit.
  - ⚑ Neither blessing gate can be crossed by an agent, so "commence design/build/audit" resolves
    to: capture (done) -> draft the note -> OWNER RATIFIES -> graduate -> OWNER BLESSES -> build.
```
