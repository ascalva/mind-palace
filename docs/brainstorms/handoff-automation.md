# Handoff automation — making seal → brief → (kill) → resume "just happen"

## 2026-07-19T21:24:10Z

```capsule
topic: handoff-automation
date: 2026-07-19

decisions:
  - Owner intent: the session handoff ceremony should "just happen" — the owner should
    never have to think about seal → brief → clear → resume. The bp-072 cockpit is the
    reading room; this closes the loop on the *leaving and re-entering* of sessions.
  - Usage bookkeeping is ALIGNED as-is — no new build wanted. What "usage automation"
    meant to the owner: the orchestrator KNOWS WHEN to run the one-off `/usage` probe
    (pre-spawn budget gate + at seal) and DOCUMENTS it (cost.actual). Judgment of
    when-and-what-to-record is the orchestrator's; scripts do not do everything. The
    scheduled/continuous ledger stays parked (see usage-automation.md), not wanted now.
  - The `resume` half is ALREADY automated: a bare session at root auto-loads
    `.claude/state/resume-brief.md` via the SessionStart hook (this is how session-34
    itself began). The owner runs nothing to re-enter.
  - `clear` is inherently owner/harness, NOT agent-automatable: an agent cannot clear
    its own context mid-turn. In practice it is kill-the-pane + reopen (cockpit.sh
    starts a fresh `claude`) or `/clear` — one keystroke, trivial. Not a build target.
  - The ONE weak link is the brief: it is authored-but-not-ENFORCED. So the handoff is
    habitual, not guaranteed. Chosen direction: a Stop-hook that refuses to close a
    session until a `resume-brief.md` fresher than the last handoff exists — mirroring
    the existing `journal-gate` that already guards per-plan journals. That single
    addition makes the whole loop guaranteed.
  - Enforcement is automated; authorship and re-entry are not, and that is deliberate —
    a handoff is a piece of writing whose job is to let a cold agent continue without
    re-asking (the fresh-agent test). Machine-checking "is this prose sufficient?" is
    not trusted yet; the hook checks that a fresh brief EXISTS, not that it is good.

parked:
  - decision: A cockpit keybind / `palace` verb that runs seal → brief as one motion.
    default: the orchestrator seals + writes the brief by hand at each unit boundary.
    re_entry: the manual seal ceremony proves annoying in real cockpit use → mint it.
  - decision: Scheduled/continuous usage ledger.
    default: self-serve `claude -p "/usage"` probe stands (orchestrator-triggered).
    re_entry: already parked in docs/brainstorms/usage-automation.md — its condition holds.

open_questions:
  - Freshness signal: `resume-brief.md` lives in `.claude/state/` which is GITIGNORED
    (never committed), so the journal-gate's "newer than the last commit" test does not
    transfer directly. Options: (a) mtime-vs-last-commit-time, (b) relocate the brief to
    a committed path, (c) a sentinel the seal writes. Must resolve before the hook.
  - Scope of enforcement: all sessions, or only orchestrator sessions? Builder sessions
    already have journal-gate; the brief is an orchestrator-specific artifact. Likely
    orchestrator-only, keyed on "bare session at root / no active-plan".
  - Artifact path: does a Stop-gate extension (it changes the enforcement contract,
    touches `.claude/hooks/**` — the machinery bp-072 deliberately excluded) warrant a
    design note, or is it a careful papercut like bp-072? Leaning: at least a light
    design note, because it is a new gate, not just a new script.
  - Interaction with delegated/worktree builders: does brief-enforcement fire in a
    worktree, or only the main checkout? (journal-gate is worktree-aware via _lib ROOT.)

next_steps:
  - Resolve the freshness-signal question (the gating design decision).
  - Decide the artifact route (design note vs papercut) and mint accordingly — the hook
    that enforces a fresh resume-brief on Stop, mirroring journal-gate.
  - Optional companion: the cockpit seal-motion keybind (parked above) if wanted alongside.

references:
  - docs/build-plans/bp-072/plan.md            # the cockpit this extends (COMPLETE)
  - .claude/hooks/                              # journal-gate — the enforcement pattern to mirror
  - .claude/state/resume-brief.md              # the artifact to enforce (NOTE: gitignored)
  - docs/brainstorms/usage-automation.md       # usage self-serve; scheduled ledger parked
  - .claude/skills/context-economy, .claude/skills/checkpoint  # the disposable-session discipline
```

## 2026-07-26T03:50:00Z

```capsule
topic: handoff-automation
date: 2026-07-26

decisions:
  - GROUNDING PASS for the finding-0175 redesign (the FORMAT half). Captured here because it
    was produced by a delegated read-only pass and otherwise existed ONLY in the resume
    brief -- which the owner then authorized wiping. Every claim below is path:line grounded.
    The ENFORCEMENT half (dn-session-handoff-gate, this file's earlier capsule) is BUILT and
    ratified; nothing below contradicts it.
  - ⚑ THE CENTRAL CONTRADICTION THE NEW NOTE MUST RESOLVE, NOT STRADDLE.
    docs/design-notes/session-handoff-gate.md:83-84 (RATIFIED) commits verbatim: "No new
    sentinel; no relocation of the brief into the committed tree." finding-0175 direction #4
    wants the opposite ("Ingested into the corpus").
    ⚑ PROPOSED RESOLUTION satisfying BOTH: the append-only typed EVENT LOG lives in a
    COMMITTED path, while the RESUME BRIEF stays a gitignored DERIVED view at its current
    path. The ratified commitment is about THE BRIEF; it says nothing about a new committed
    artifact. The gate keeps keying on the brief's mtime, untouched.
  - ⚑ THE TRIPWIRE -- any redesign that stops writing the exact current path SILENTLY
    DISABLES the handoff gate. Clause (e) keys on
    os.path.getmtime(".claude/state/resume-brief.md") at .claude/hooks/_lib.py:909, guarded
    by head_sha != content(session-baseline) at :908; the baseline is written by
    .claude/hooks/session-brief.sh:65 (NOT :52, as both session-handoff-gate.md:156 and
    agent-workflow.md:324 claim).
  - DERIVED != COMMITTED IS ALREADY ESTABLISHED HERE. scripts/docket.py:200 writes
    .claude/state/docket.md, which is gitignored (.claude/state/.gitignore is a blanket `*`
    + `!.gitignore`). So finding-0175's table row asserting derived views are "in git:
    committed" is WRONG for docket.md -- true only for TRACKS/DESKCHECK-QUEUE. Correct it in
    the note.
  - TENSION TO NAME HONESTLY: .claude/state/.gitignore:1-3 declares the directory
    "Regenerable, per-worktree, never shared" -- directly in tension with retained history.
    An event log probably does NOT belong in .claude/state/.
  - THE DERIVED-VIEW CONTRACT TO COPY: stdout-first, --write second; a machine banner
    ("GENERATED by scripts/board.py -- do not hand-edit", board.py:39); a footer restating
    the contract. Falsifier stated INLINE, verbatim (docket.py:4-6): "NO persisted state, so
    it cannot drift (the falsifier)". board.py:5 names its own falsifier F-WF2.
  - ⚑ WORKFLOW SCRIPTS MAY NOT IMPORT `core` (docket.py:16, board.py:13). Core's append-only
    implementations are therefore PATTERNS TO TRANSPOSE, never modules to call:
      * core/stores/versions.py:33-35 -- SHARPEST precedent: current = max(version_seq),
        supersession = the consecutive-seq relation, BOTH DERIVED, never stored. Refuses
        lineage merges at :146; ":158 -- Append-only history is never merged."
      * core/stores/vectorstore.py:221 supersede_source -- the keep-and-link `current` flag,
        which finding-0164 names as the template.
      * core/stores/chat_events.py:12-24 -- typed ordered append-only events, STRUCTURAL REFS
        ONLY, no prose column. Closest analog to "typed state events".
  - "SLOT-LINEAGE" IS A PRINCIPLE NAME, NOT CODE -- grep finds it only at
    docs/findings/finding-0168.md:84. Its implemented realization is the `current` flag. Do
    not go looking for a module.
  - THE BRIEF'S OBLIGATION IS NOT IN agent-workflow.md. It lives at CLAUDE.md:78 and
    .claude/skills/context-economy/SKILL.md:65-77, which pins a SEVEN-section schema; while
    docs/templates/resume-brief.md carries EIGHT headed blocks. Pre-existing drift between
    skill and template.
  - NEXT AMENDMENT LETTER IS A10. There is NO A7 (the log jumps A6 -> A8); A9 ends at
    agent-workflow.md:327. A9 is also the precedent that a DESIGN NOTE, not a finding, may
    warrant an amendment. Front-matter drift: the `amendments:` block (:21-31) never got A9.
  - CITATION ROT FOUND IN RATIFIED NOTES (a warrant for the typed-reference-standard thread
    in owner-cockpit.md): session-handoff-gate.md:58 cites _lib.py:617 (actually :899); :155
    cites :571-708 (actually :757-890); :156 and agent-workflow.md:324 cite
    session-brief.sh:52 (actually :65).

parked:
  - decision: where the committed event log lives.
    default: NOT .claude/state/ (blanket-gitignored, declared per-worktree and never shared).
    re_entry: the design note; decide alongside the key-slot location question from
    autopilot-mode.md 03:05Z, which has the same repo-global-vs-per-worktree shape.

open_questions:
  - Does the seven-section schema (SKILL.md:65-77) survive the redesign, or is it replaced by
    a derived rendering? If derived, the schema stops being prose discipline and becomes the
    renderer -- which is the point, but it means the skill text must change too.
  - dn-session-handoff-gate parks "brief-quality checking" with re-entry "recurring
    fresh-but-useless briefs observed at resume time" (:142-145). Session-51 arguably MET
    that condition: the brief reached 45 KB and grew THREE duplicate/contradictory
    "FIRST ACTION" headers in one session. Worth citing as the re-entry trigger.

next_steps:
  - Write the design note (draft; A10 on dn-agent-workflow). It is design-note-first and NOT
    graduatable (finding-0175's own routing).

references:
  - docs/findings/finding-0175.md                    # the warrant
  - docs/design-notes/session-handoff-gate.md        # the ratified ENFORCEMENT half
  - scripts/docket.py, scripts/board.py              # the derived-view precedents
  - docs/brainstorms/command-center.md               # :121-133 the watchlist, "beside the brief"
```
