---
type: build-plan
id: bp-148
track: workflow
status: proposed
design_ref:
  - docs/design-notes/dn-typed-workflow-registry.md
contract: builder
write_scope:
  - CLAUDE.md
  - .claude/skills/checkpoint/SKILL.md
  - .claude/skills/context-economy/SKILL.md
  - .claude/skills/build-plan/SKILL.md
  - .claude/skills/delegate/SKILL.md
  - .claude/commands/resume.md
  - docs/templates/build-plan.md
  - tests/integration/test_registry_resume_drill.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 300k
  actual: null
depends_on: [bp-140, bp-146, bp-147]
parallelizable_with: [bp-144]
created: 2026-07-27
updated: 2026-07-27
links:
  - docs/design-notes/dn-typed-workflow-registry.md
  - docs/build-plans/bp-147/plan.md
  - .claude/skills/context-economy/SKILL.md
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — Resume-brief deprecation: the doctrine edits and the fresh-agent drill

## 0. Mode & provenance

Investigation and planning produced this plan during `/graduate` of
`dn-typed-workflow-registry` (ratified 2026-07-27); it graduates the note's license (v) —
"resume-brief deprecation — the skills/CLAUDE.md/scripts edits of §2.7's table" — **minus its
two blocked rows.** Implementation proceeds item-by-item on owner approval; the
`proposed → ready` blessing is the owner's alone.

⚑ **What this plan deliberately excludes, and why.** Note §2.7's table has ten rows. Three of
them name **ratified design notes** (`agent-workflow.md` §6/§9/§13,
`role-state-and-scoped-handoff.md`) and are marked "owner-ratified amendment" — those are
owner acts, never a builder's, and §3(1) says "Until each amendment lands, the text it
amends governs." Two more (`.claude/hooks/*` + `.claude/settings.json`;
`scripts/handoff.py`, `scripts/board.py`) are downstream of those amendments and are carried
by **bp-149** and **bp-150** respectively. This plan takes the rows that are licensed by
ratification alone and touch no ratified text: `CLAUDE.md`, four skills, the `/resume`
command, and the build-plan template.

## 1. Objective

Rewrite the note-taking doctrine so state lives on units and is read by query, delete the
resume-brief obligation, and prove the replacement with a fresh-agent drill.

## 2. Context manifest

1. `docs/design-notes/dn-typed-workflow-registry.md` §2.7 in full — the diagnosis ("a
   hand-maintained cache of a derivable fact, written at the exact moment the agent is most
   depleted"), the replacement, "the journal narrows to judgement", and **the ten-row table
   of every artifact that must change**. Plus falsifier F6.
2. `CLAUDE.md` — the whole file; specifically the note-taking obligation and the
   resume-brief sentence (§2.7's table cites `:78`; **verify the line number before
   editing** — the file has changed since the note was written).
3. `.claude/skills/checkpoint/SKILL.md` — the whole file. Sections 1–6 of the journal entry
   become registry unit fields; the entry keeps judgement + markers.
4. `.claude/skills/context-economy/SKILL.md` — the whole file, **including its CORRECTION
   block** about the retired `.claude/state/` handoff file. §2.7 cites it as the precedent
   ("the repo has already walked this exact road once … replaced by *regenerate and commit*").
5. `.claude/commands/resume.md` — ⚑ the real `/resume` surface. **§2.7's table names
   `.claude/skills/resume/SKILL.md`, which does not exist** — see §3 Q1.
6. `.claude/skills/build-plan/SKILL.md` + `docs/templates/build-plan.md` — where `write_scope`
   gains its enforcement level.
7. `.claude/skills/delegate/SKILL.md` — "builders mint IDs/refs via the registry;
   push-before-spawn gains 'registry ref, not eyeballed ID'".
8. `docs/build-plans/bp-147/plan.md` §6.2 — `UnitState`, the typed fields this doctrine
   points at, and §6.5's `status` command.
9. `docs/build-plans/bp-146/plan.md` §6.3 — the enforcement level the template must carry.
10. `docs/build-plans/bp-148/journal.md`.

### DRY audit — does `core/` (or the wider tree) already have this?

- **The unit-state fields the doctrine points at?** `ops/registry/fold.py::UnitState`
  (bp-147 §6.2) and `scripts/registry.py status`. **The skills must reference the real
  command and the real field names**, not describe a parallel scheme. A skill that invents
  its own vocabulary for the same fields is documentation drift — the same defect class as a
  duplicated implementation, and the one this repo's derived views exist to avoid.
- **A precedent for retiring a hand-carried state file?** ⚑ **Yes, in this repo, and §2.7
  names it:** the `.claude/state/` handoff file, retired in `.claude/skills/context-economy/SKILL.md`'s
  CORRECTION block for being "outside git, mixing four kinds of fact with four freshness
  rules, freshness as a hand-authored act that every later commit re-armed" — replaced by
  *regenerate and commit*. The new text must **cite** that correction rather than re-argue
  it; the argument is already made and ratified in the tree.
- **The five follow-through questions?** `.claude/skills/checkpoint/SKILL.md:69-76`, now also
  a typed field (bp-147 §6.1). One source of truth: the skill keeps the prose form and gains
  a pointer to the typed form; it must not restate a *different* five.
- **`core/` audit:** N/A — this plan writes no code outside one test file.

## 3. Investigation & grounding

- **Q1 — does `.claude/skills/resume/SKILL.md` exist?** ⚑ **No.** Verified this pass:
  `ls .claude/skills/` yields `book build-plan checkpoint commit context-economy delegate
  finding graduate` — there is no `resume` skill. `/resume` is a **command**,
  `.claude/commands/resume.md`. §2.7's table row is therefore **inaccurate about the path**
  while correct about the artifact. ⇒ This plan edits `.claude/commands/resume.md` and
  records the discrepancy as a `spec-fidelity` finding (§10) so the note's table can be
  corrected by the owner at amendment time. **Do not create a `resume` skill** to make the
  note's text true — that is inventing an artifact to match a document.
- **Q2 — where is the resume-brief sentence in `CLAUDE.md`?** §2.7's table cites `:78`. The
  current text at that line reads: "Sessions are disposable, artifacts are not — end at
  unit boundaries with a resume brief (context-economy skill; owner rule 2026-07-11)."
  Verified this pass. The note licenses "a **one-sentence-scale** edit to `CLAUDE.md`"
  (§3(2)) — the resume-brief clause is deleted and the note-taking rule is re-pointed. ⚑
  `CLAUDE.md`'s own §5 thinness rule means this edit **removes more than it adds**; a
  multi-paragraph replacement would violate the file's constitution.
- **Q3 — what exactly replaces the brief?** §2.7, verbatim: "**The replacement is not a
  better brief — it is that nothing session-shaped needs handing off.** State distributes
  across *units of work*: each registry unit carries its open criteria, parked items with
  re-entry conditions, last landed commit, and linked findings — as typed fields, written at
  the semantic boundary where each fact is born (the moment of least depletion), not recalled
  at close. A fresh session reconstructs 'where was I' by query: *open units, their open
  criteria, their parked items, in dependency order*."
- **Q4 — what stays in the journal?** §2.7: "**The journal narrows to judgement.** … What
  remains is what no store can derive: the why, the surprises, the approaches discarded and
  the reason. Shorter, and the part that was actually valuable. The seat-journal purity rule
  (no shas, no counts, no statuses) already points exactly here — it becomes the rule for
  *every* journal."
- **Q5 — is the fresh-agent test deleted or moved?** **Moved, not deleted.**
  `agent-workflow.md` §9 defines it and is ratified — this plan cannot touch it. The
  checkpoint skill's version of the bar becomes: a fresh session given the **registry query
  plus the prose files** must continue without re-asking. That is F6, and Item 43 is the
  drill. The skill's text must be careful: the *bar* is unchanged, the *inputs* change.
- **Q6 — does anything mechanical read these files?** `tests/integration/test_deskcheck_gate.py`
  asserts the **hook's** clause-(f) behavior against literal `## Follow-through` text
  (`:249, :269-290`) — it reads journals, **not** the skill, and this plan changes no hook,
  so it stays green. Verified by grep: no test reads `CLAUDE.md` or any `SKILL.md`. ⇒ No
  retrofit pre-widening is required, but **run that test** as a regression check (§5).
- **Q7 — can the drill run before the hooks are retired?** Yes, and that is the point: the
  drill proves the *replacement* works while the *original* still stands. F6's own wording —
  "a fresh-agent drill — new session, registry + prose files only — cannot continue an
  in-flight unit without re-asking. The resume-brief replacement (§2.7) is then not yet real,
  **and the deprecation halts at the skills edit**" — anticipates exactly this ordering.
- **Q8 — what does the delegate skill gain?** §2.7's table: "builders mint IDs/refs via the
  registry; push-before-spawn gains 'registry ref, not eyeballed ID'". Grounded in the live
  defect the note names (§2.2): "Two parallel worktree builders *will* pick the same finding
  number." The existing push-before-spawning rule stays; the ID sentence is added beside it.

**Additional risks or questions surfaced during reading:**

- This plan edits the constitution-adjacent files every session loads. A wrong edit is paid
  on every turn forever. It is also the one plan in the family whose acceptance is hardest to
  make *runnable* — "the doctrine reads correctly" is a human judgement. Item 43's drill is
  the mechanical anchor; without it this plan would fail the graduate skill's own sizing
  heuristic ("acceptance criteria that are *runnable*").
- The skills describe a registry that is **not yet the enforcement substrate** (the hooks are
  still live until bp-149). Every edited sentence must be true **during the transition**, not
  only after it. Prefer "record unit state in the registry **and** keep the journal's
  judgement entry" over "instead of".

## 4. Reconciliation

- `CLAUDE.md:78` — "end at unit boundaries with a resume brief (context-economy skill; owner
  rule 2026-07-11)" → ⚑ **banner: correction.** The clause is deleted. Proposed diff:

  ```diff
  - Sessions are disposable, artifacts are not — end at unit boundaries with a resume
  - brief (context-economy skill; owner rule 2026-07-11).
  + Sessions are disposable, artifacts are not — end at unit boundaries, with the unit's
  + state submitted to the registry and a judgement entry in the journal (context-economy
  + skill; dn-typed-workflow-registry §2.7 supersedes the resume-brief rule of 2026-07-11).
  ```

  The superseded owner rule is **named**, not silently dropped — a correction is announced as
  a correction.
- `.claude/skills/context-economy/SKILL.md` (the CORRECTION block about `.claude/state/`) →
  **cross-ref: extension.** The new clearing-boundary text cites that block as the precedent
  rather than re-arguing it: same defect, one level up, same fix shape ("derive, don't carry").
- `.claude/skills/checkpoint/SKILL.md` sections 1–6 → ⚑ **banner: correction.** Sections
  1–4 (status line, completed, in-flight, next action) and 6 (context-manifest delta) become
  registry unit fields; sections 5 (open questions) and 7 (markers) and the judgement prose
  stay. The banner names this plan and note §2.7, and the five follow-through questions
  gain a pointer to `ops/registry/seal.py::FollowThrough` (bp-147 §6.1) as the typed form —
  **the prose form is not deleted**, because the hook's clause (f) still greps for it until
  bp-149.
- `docs/templates/build-plan.md` + `.claude/skills/build-plan/SKILL.md` → **cross-ref:
  extension.** `write_scope` gains an enforcement level (bp-146 §6.3), documented as an
  addition. ⚑ The **bare-glob rule stays exactly as written** — it is the bp-066 footgun and
  the template's warning must not be diluted by the new field.
- `.claude/commands/resume.md` → **cross-ref: extension** (and a `spec-fidelity` finding for
  the note's path error, §3 Q1).
- **No design note is edited.** `agent-workflow.md` §6/§9/§13 and
  `role-state-and-scoped-handoff.md` are the owner's to amend (§3(1) and §2.7's table).

## 5. Write scope

- `CLAUDE.md` — the one-sentence-scale edit (§4).
- `.claude/skills/checkpoint/SKILL.md` — the sections 1–6 split; judgement + markers stay.
- `.claude/skills/context-economy/SKILL.md` — the clearing boundary: "write the handoff pair"
  → "submit unit state; append judgement entry".
- `.claude/skills/build-plan/SKILL.md` + `docs/templates/build-plan.md` — `write_scope` gains
  its enforcement level.
- `.claude/skills/delegate/SKILL.md` — registry refs, not eyeballed IDs.
- `.claude/commands/resume.md` — resumes from a registry query + prose files.
- `tests/integration/test_registry_resume_drill.py` — the F6 drill.

**Deliberately OUT of scope:** ⚑ `docs/design-notes/**` — three rows of §2.7's table are
owner-ratified amendments and are **not** this plan's (`agent-workflow.md`,
`role-state-and-scoped-handoff.md`). `.claude/hooks/**` and `.claude/settings.json`
(bp-149). `scripts/handoff.py`, `scripts/board.py` (bp-150, itself gated on the role-state
amendment). `CONSTITUTION.md`, `eval/golden/**`, `eval/golden.py` (foundation denylist).
`.claude/skills/graduate/SKILL.md` and `.claude/skills/finding/SKILL.md` — **not named by
§2.7's table**; leaving them alone is deliberate, not an oversight.

**Retrofit check.** No test reads `CLAUDE.md` or any `SKILL.md` (grep, this pass). The only
adjacent mechanical surface is `tests/integration/test_deskcheck_gate.py`, which asserts the
**hook's** clause-(f) behavior against literal journal text and is unaffected because no hook
changes — **run it anyway** as a regression check and record the result.

## 6. Interfaces pinned inline

### 6.1 What the doctrine points at (bp-147 §6.2, verbatim — the skills must use these names)

```python
@dataclass(frozen=True)
class UnitState:
    unit_ref: str
    status: str
    open_criteria: list[str]
    parked: list[tuple[str, str]]            # (what, re-entry condition) — re-entry REQUIRED
    last_landed_commit: str | None
    linked_findings: list[str]
    active_in_checkout: str | None
    judgement_entry_at: str | None
```

```
uv run scripts/registry.py status [<unit-ref>]     # the orientation read
uv run scripts/registry.py query --status in-progress
```

### 6.2 The replacement doctrine (note §2.7, verbatim — the text to render into skills)

> State distributes across *units of work*: each registry unit carries its open criteria,
> parked items with re-entry conditions, last landed commit, and linked findings — as typed
> fields, written at the semantic boundary where each fact is born (the moment of least
> depletion), not recalled at close. A fresh session reconstructs "where was I" by query:
> *open units, their open criteria, their parked items, in dependency order*.

> **The journal narrows to judgement.** … What remains is what no store can derive: the why,
> the surprises, the approaches discarded and the reason. Shorter, and the part that was
> actually valuable. The seat-journal purity rule (no shas, no counts, no statuses) already
> points exactly here — it becomes the rule for *every* journal.

### 6.3 The enforcement level for the template (bp-146 §6.3, verbatim)

```
LEVELS = ("a", "b");  DEFAULT_LEVEL = "a"
```

> per-unit, not global — `write_scope` becomes an enforcement *level* declared at graduation.
> Default level = (a). Level (b) for units whose blast radius the delegation rubric already
> scores full-strength (enforcement surfaces, core invariants, migrations).

Template addition (front matter), and ⚑ **the bare-glob rule is untouched**:

```yaml
write_scope:              # exact globs — the capability; enforced by scope-guard.
                          # NO inline comment on an ENTRY: per-path rationale goes in §5.
  - <path/glob>
scope_level: a            # a = land-time admission (default) | b = worktree-as-scope
```

### 6.4 F6, verbatim (the falsifier this plan must run)

> **F6 (resume by query):** a fresh-agent drill — new session, registry + prose files only —
> cannot continue an in-flight unit without re-asking. The resume-brief replacement (§2.7) is
> then not yet real, and the deprecation halts at the skills edit.

## 7. Items

### Item 40 — the `CLAUDE.md` sentence, and the checkpoint skill's split

- **Objective:** the resume-brief obligation is gone from the constitution and the journal
  contract narrows to judgement.
- **Files:** `CLAUDE.md`, `.claude/skills/checkpoint/SKILL.md`
- **Acceptance test:** `grep -rn "resume brief\|resume-brief" CLAUDE.md .claude/skills/` returns
  **only** the correction banner's reference to the superseded rule; `CLAUDE.md`'s line count
  does not increase; the checkpoint skill still contains the verbatim
  `## Follow-through` block and the five questions (the hook still greps for them).
- **Falsifier:** ⚑ the edit makes a sentence that is **false during the transition** — e.g.
  "status lives only in the registry" while `gate-guard` still reads the file and the tree is
  still authoritative. Read every edited sentence as if the hooks are still live, because
  they are. A doctrine that describes the end state as if it were the present state is how an
  agent gets told to do something the guards will deny.
- **Invariant(s) it must not violate:** `CLAUDE.md`'s thinness rule (§5) — this edit removes
  more than it adds; the fresh-agent **bar** is unchanged, only its inputs.
- **Touches stored data?** No.
- **Parallelizable?** No.  **Depends on:** bp-147 Item 35.

### Item 41 — context-economy and `/resume`

- **Objective:** the clearing boundary and the resume path point at the registry query.
- **Files:** `.claude/skills/context-economy/SKILL.md`, `.claude/commands/resume.md`
- **Acceptance test:** the context-economy skill's clearing-boundary section names
  `uv run scripts/registry.py status` and cites its own `.claude/state/` CORRECTION block as
  the precedent; `.claude/commands/resume.md` names the query plus the prose files as the
  resume inputs; `grep -c "handoff pair" .claude/skills/context-economy/SKILL.md` is 0 or
  only inside the correction banner.
- **Falsifier:** the new text re-argues the derive-don't-carry case from scratch instead of
  citing the existing CORRECTION block. Two independent arguments for one rule drift; the
  repo already made this argument once and ratified it.
- **Invariant(s) it must not violate:** every sentence true during the transition.
- **Touches stored data?** No.
- **Parallelizable?** Yes.  **Depends on:** Item 40.

### Item 42 — the template's enforcement level, and the delegate skill's refs

- **Objective:** `write_scope` gains `scope_level`; delegation mints refs instead of
  eyeballing IDs.
- **Files:** `docs/templates/build-plan.md`, `.claude/skills/build-plan/SKILL.md`,
  `.claude/skills/delegate/SKILL.md`
- **Acceptance test:** the template's front matter carries `scope_level: a` with the two
  values documented; `.claude/hooks/_lib.py:parse_front_matter` parses the amended template
  without error (run it: `python3 .claude/hooks/_lib.py` in its standalone mode, or a
  one-liner import); the delegate skill states "registry ref, not eyeballed ID" beside the
  existing push-before-spawn rule.
- **Falsifier:** ⚑ the template edit breaks front-matter parsing, or dilutes the bare-glob
  warning. Either would be a self-inflicted version of the bp-066 footgun — the template is
  what every future plan is minted from, so a defect here is systemic rather than local.
- **Invariant(s) it must not violate:** the bare-glob rule stays verbatim; the template's
  thirteen required sections stay.
- **Touches stored data?** No — but the template is the source of every future plan, so treat
  it as high blast radius and diff it carefully.
- **Parallelizable?** Yes.  **Depends on:** bp-146 Item 32.

### Item 43 — the F6 fresh-agent drill

- **Objective:** demonstrate that a fresh session can continue an in-flight unit from the
  registry query plus prose files alone.
- **Files:** `tests/integration/test_registry_resume_drill.py`
- **Acceptance test:** the test builds a synthetic in-flight unit (three closed criteria, two
  open, one parked with a re-entry condition, two linked findings, a landed commit), then
  asserts that `uv run scripts/registry.py status <ref>` output **contains every fact a
  resuming agent needs**: each open criterion, each parked item **with** its re-entry
  condition, the last landed commit, and each linked finding. A missing fact fails the test
  naming it.
- **Falsifier:** ⚑ **F6** — "a fresh-agent drill … cannot continue an in-flight unit without
  re-asking." The mechanical proxy above is necessary but not sufficient; the **honest**
  falsifier is a real drill: run an actual fresh session against a real in-flight unit with
  only the query + prose, and record in the journal whether it had to ask something already
  answered. If it did, **the deprecation halts at the skills edit** (F6's own wording) and
  bp-149 must not proceed on the resume-brief rows. Record the drill's transcript summary,
  not a claim.
- **Invariant(s) it must not violate:** the drill must not consult a journal's status
  sections — that would be testing the thing being deprecated.
- **Touches stored data?** No — synthetic unit in a scratch store.
- **Parallelizable?** No.  **Depends on:** Items 40, 41, bp-147 Item 35.

## 8. Math carried explicitly

N/A — no mathematical object implemented. This plan edits doctrine and adds one drill.

## 9. Non-goals

- ⚑ **No design-note edit.** Three rows of §2.7's table are owner-ratified amendments
  (`agent-workflow.md` §6/§9/§13; `role-state-and-scoped-handoff.md`). Not this plan's, not
  any builder's.
- ⚑ **No hook change, no `.claude/settings.json` change** — bp-149, blocked.
- ⚑ **No `scripts/handoff.py` / `scripts/board.py` change** — bp-150, itself gated on the
  role-state amendment.
- **No new `resume` skill** to make §2.7's path true (§3 Q1). File the finding instead.
- **No deletion of the prose `## Follow-through` block** from the checkpoint skill — the
  hook's clause (f) still greps for it until bp-149.
- **No expansion of `CLAUDE.md`.** The note licenses a one-sentence-scale edit; the file's
  own §5 thinness rule binds.
- **No change to the fresh-agent bar** — only its inputs (§3 Q5).
- **No new dependency.**

## 10. Stop-and-raise conditions

- Any edited sentence would be **false during the transition** (Item 40's falsifier) — stop,
  rewrite to be true in both states, or park that row.
- The `/resume` path discrepancy (§3 Q1) — file a `spec-fidelity` finding naming
  `.claude/skills/resume/SKILL.md` (does not exist) vs `.claude/commands/resume.md` (does),
  and continue. Do **not** create the skill.
- Item 43's honest drill fails — **stop and report**: F6's own wording halts the deprecation
  at the skills edit, and bp-149 must not proceed on these rows.
- The template edit breaks front-matter parsing — revert immediately; every future plan is
  minted from it.
- An owner-level question about doctrine wording — park the criterion with a re-entry
  condition and continue the others; never block on the owner.
- Any blessing this plan would have to perform — it must not.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| `.claude/skills/resume/SKILL.md` | **not created**; `.claude/commands/resume.md` edited instead; a `spec-fidelity` finding records the note's path error | creating the skill — inventing an artifact to make a document true, backwards | The owner amends §2.7's table, or decides `/resume` deserves a skill |
| Journal sections 1–4 and 6 | **narrowed**, not deleted from the skill: the skill records that these facts now live as unit fields and that a journal entry need not repeat them | deleting the sections outright — the hooks still read journals until bp-149, and a journal that suddenly lacks a status line would trip clause (a) | bp-149 retires `journal-gate` |
| Whether `graduate`/`finding`/`commit` skills need edits | **no edit** — not named by §2.7's table | editing them anyway — scope creep into files the design did not name | A build wave shows one of them still teaches the resume-brief pattern |
| The honest F6 drill's evidence form | a recorded transcript summary in the journal, not an automated assertion | asserting it in a test — "a fresh agent did not have to ask" is not machine-checkable, and pretending it is would be the completion-claims defect | An owner ruling on what evidence suffices |

## 12. Dependency & ordering summary

**Within the plan.** Item 40 (the constitution and the journal contract) → Item 41
(context-economy + `/resume`) and Item 42 (template + delegate, parallel) → Item 43 (the
drill). Blast-radius order is inverted from the usual, deliberately: the highest-leverage
file (`CLAUDE.md`, loaded every session) is edited **first and smallest**, so a mistake is
caught by the very next session rather than after four more files have moved.

**Across plans.** `depends_on: [bp-140, bp-146, bp-147]` — the doctrine can only point at
fields that exist (`UnitState`, `scope_level`). `parallelizable_with: [bp-144]` (disjoint
scope). **bp-149 depends on this plan** — retiring `journal-gate` while the checkpoint skill
still demands the old sections would leave the doctrine describing a gate that no longer
exists. **bp-150** (the derived views) is independent of this plan's files but shares the
same §2.7 table and is gated on the role-state amendment. `bp-138`/`bp-139` are independent
of this whole family (note §3(5)).
