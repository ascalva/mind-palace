---
type: build-plan
id: bp-125
track: workflow
status: proposed
design_ref:
  - docs/design-notes/role-state-and-scoped-handoff.md
contract: builder
write_scope:
  - docs/roles/**
  - .claude/skills/checkpoint/SKILL.md
  - .claude/skills/context-economy/SKILL.md
  - .claude/skills/commit/SKILL.md
  - .claude/skills/delegate/SKILL.md
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 400k
  actual: null
depends_on:
  - bp-124
parallelizable_with: []
created: 2026-07-26
updated: 2026-07-26
links:
  - docs/design-notes/role-state-and-scoped-handoff.md
  - docs/findings/finding-0175.md
  - docs/findings/finding-0234.md
  - .claude/skills/context-economy/SKILL.md
  - .claude/skills/checkpoint/SKILL.md
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — migrate the live brief into the seat, and re-home its rules

> **Every section below is required.** A section that does not apply is marked
> `N/A — <one-line reason>`, never silently omitted.

## 0. Mode & provenance

Investigation and planning produced this plan; implementation proceeds item-by-item on
owner approval. It graduates `dn-role-state-and-scoped-handoff` §2.5 (the four-way split
applied to real content), §2.8 (append-only retention), and the migration clause of §2.9.

Authority-to-act is separate from the readiness blessing. **This plan is `proposed`; no
agent flips it to `ready`.**

**⚑ EXECUTION MODE — this plan cannot run in a worktree.** Its principal input,
`.claude/state/resume-brief.md`, is gitignored (`.claude/state/.gitignore` ignores `*`) and
therefore **absent from every fresh checkout**. Verified 2026-07-26: the main checkout holds
a 498-line / 36,701-byte brief, while a fresh worktree of `origin/main` holds only
`.claude/state/.gitignore` and nothing else. See §3 Q1 and `finding-0234` correction (2).
**Run this plan in the main checkout**, or have the orchestrator copy the brief into the
worktree *before* spawn and say so in the journal. Discovering this mid-session is a lost
session; it is stated here so it cannot be.

**This plan changes no gate and deletes nothing.** Clause (e) still governs, the brief is
still written and still auto-surfaced, and `docs/templates/resume-brief.md` still exists.
That is the note's deliberately overlapping window (§4 stage (a)) and its accepted cost is
double bookkeeping until bp-126 lands.

## 1. Objective

Move the live resume brief's genuinely non-derivable content into the orchestrator seat —
narrative into `journal.md`, readings into `readings.md`, durable rules out to the skills
that load them at the moment of use — leaving every derivable fact to the generator.

## 2. Context manifest

Read exactly these, in order, before any work:

1. `docs/design-notes/role-state-and-scoped-handoff.md` — the ratified decision, whole.
   §2.2 (the census and its method), §2.5 (**the four-way split — this plan's classifier**),
   §2.8 (append-only + compaction capsules), §2.9 (what retires and what replaces it).
2. `.claude/state/resume-brief.md` — **the artifact being migrated.** Read whole; it is the
   input. (Main checkout only — see §0.)
3. `docs/roles/orchestrator/journal.md` and `readings.md` — bp-124's output; the
   destinations. Read before appending so the append-only discipline is visible.
4. `.claude/skills/checkpoint/SKILL.md` — the journal contract being generalized to seats.
   Read whole; §"Required sections" and §"The fresh-agent test" are the text this plan
   extends.
5. `.claude/skills/context-economy/SKILL.md` — read whole; §"The resume brief — location,
   lifecycle, schema (finding-0035)" at `:65-78` is the section being replaced.
6. `.claude/skills/commit/SKILL.md` and `.claude/skills/delegate/SKILL.md` — the receiving
   homes for the brief's git and worktree rules respectively. Read to place each rule where
   it already belongs rather than inventing a section.
7. `docs/findings/finding-0175.md` — the warrant. It flips to `promoted` in Item 5.
8. `docs/findings/finding-0234.md` — the graduation-time corrections; correction (2) is
   this plan's execution-mode constraint.

**Does `core/` already implement this? (the DRY audit.)** N/A in the algorithmic sense —
this plan implements no algorithm, primitive, or mathematical object. It is a content
migration plus prose edits to four skill files. The DRY question it *does* answer is the
inverse one and it is the plan's whole point: the brief currently **duplicates** facts the
artifact tree already owns (statuses, counts, hashes), and the migration's rule is
**single-home, multi-render** — a fact wanted in two scopes lives in the lower one and is
*rendered* into the higher one, never copied (note §2.3).

## 3. Investigation & grounding  <!-- Part A -->

- **Q1 — Is the brief reachable from a worktree builder?** **No.**
  `.claude/state/.gitignore` ignores `*` with a single `!.gitignore` exception, and its own
  comment states the intent: *"Regenerable, per-worktree, never shared"*
  `[GROUNDED .claude/state/.gitignore]`. Measured 2026-07-26: main checkout
  `.claude/state/` holds `.gitignore`, `docket.md`, `resume-brief.md` (498 lines, 36,701
  bytes), `session-baseline`; a fresh worktree of `origin/main` holds `.gitignore` **only**.
  The note's §3 sketch assigns the migration to a build plan without noting that no worktree
  builder can perform it. Carried as `finding-0234` correction (2) and as §0's execution-mode
  constraint.

- **Q2 — Is the note's census still accurate against the live artifact?** **Partly, and the
  drift is itself evidence.** The note records the brief as *"405 lines as read"* on
  2026-07-26 and explicitly flags size as "a session-instantaneous reading, not a property"
  (§2.2, echoing finding-0175's triage correction). Measured at graduation the same day: 498
  lines. The class *proportions* (~33% tree-derivable, ~7% execution-derived, ~44%
  judgement, ~11% rules) are the note's `[DERIVED]` reading and **must be re-derived by the
  builder against the live file**, not assumed. The note's own estimate of genuinely
  non-derivable content is "on the order of 80–100 lines of 405."

- **Q3 — What exactly does the brief's rule section contain, and where does each rule go?**
  The brief's `## STANDING RULES` section is described by its template as *"the
  session-invariant constraints: push/deploy policy, CI-observation mechanics, trailer
  policy, `uv run` discipline, blessing gates"* `[GROUNDED docs/templates/resume-brief.md:39-43]`.
  **The code does not settle the destination of each individual rule** — no artifact maps
  rule→skill. What settles it: reading each rule and asking which skill is *already loaded at
  the moment that rule binds* (the note's own RULES criterion: "a rule loads at the moment of
  use or it does not hold"). The four plausible homes are in §5; the mapping is Item 3's
  deliverable and must be recorded as an explicit table, not left implicit.
  `uv run` discipline and the blessing gates already live in `CLAUDE.md` — which is
  **deliberately out of scope** (§5), so a rule whose only correct home is `CLAUDE.md` is
  *already home* and is dropped from the brief rather than moved.

- **Q4 — Is the RULES-eviction claim supported?** Yes, by the note's own evidence: the
  `git add -A` / `-F -` rules *"held once moved into the commit skill and failed repeatedly
  while they lived in the brief"* (note §2.5, grounding the capture at
  `docs/brainstorms/role-state-and-scoped-handoff.md:62-65`). Independently visible in the
  tree: the commit skill is the live home of the staging discipline, and the repo's own
  memory records `git add -A` as banned by owner rule.

- **Q5 — What does the context-economy skill currently claim, verbatim, that this plan must
  reconcile?** `[GROUNDED .claude/skills/context-economy/SKILL.md:65-78]` — quoted in full in
  §4. Two further passages *also* reference the brief and must not be missed: `:21` (the
  decision rule tells a session to "write a resume brief … and recommend the owner clear")
  and `:58-59` ("Each resume brief MUST end with the next session's recommended `/model` +
  `/effort`"). A reconciliation that edits only the `:65-78` section leaves two live
  references to a soon-to-be-deleted artifact.

- **Q6 — Does the checkpoint skill need a *change* or an *addition*?** An addition. Its
  contract is written for `docs/build-plans/<id>/journal.md` and the note's §1.2 is explicit
  that the **per-plan journal contract is not changed** — the note *generalizes* the contract
  to seats without touching the plan instance of it. So checkpoint gains a seat-journal
  section; its existing sections stay byte-identical except where they say "the journal" and
  must now say which journal.

- **Q7 — Can this plan land amendment A10 to `dn-agent-workflow`?** **No.** `agent-workflow.md`
  carries `status: ratified` and `scope-guard` denies any agent write to a ratified note
  *before* the write-scope check even runs `[GROUNDED .claude/hooks/_lib.py:435-441]`; the
  Stop-gate (b2) clause blocks the Bash path against HEAD status
  `[GROUNDED .claude/hooks/_lib.py:797-824]`. The note's §1.1 states the amendment "lands via
  a build plan after ratification," which enforcement forbids. Carried as `finding-0233`;
  A10 is an owner hand-act and appears in this family only as a parked decision (§11).

- **Q8 — Does flipping `finding-0175` to `promoted` need a write_scope entry?** No —
  `docs/findings/**` is always writable by any builder and need not be listed
  (build-plan skill, §Front-matter fields). It is named in §5 prose for legibility only.

**Additional risks or questions surfaced during reading:**

- The brief is **read-and-classify** work over ~500 lines of dense prose, and the classifier
  is judgement (the note's §2.2 census could not be produced mechanically). This is the
  session's real cost, not the file edits.
- The migration is **lossy by design** for one class: tree-derivable facts are *dropped*,
  not moved, because the generator reproduces them. Dropping is correct; the risk is
  dropping something that only *looks* derivable. The falsifier for that is Item 4.

## 4. Reconciliation  <!-- Part B -->

- `.claude/skills/context-economy/SKILL.md:65-78` — currently:

  > *"## The resume brief — location, lifecycle, schema (finding-0035)*
  > *— **Location:** `.claude/state/resume-brief.md` — ephemeral, gitignored, the fast path.*
  > *`docs/PROGRESS.md` stays the committed durable backstop (portable across machines).*
  > *— **Lifecycle:** the orchestrator WRITES it at every clearing boundary (the self-rewrite
  > step); `session-brief.sh` auto-surfaces it … the next session consumes it and REWRITES it
  > at its own boundary.*
  > *— **Schema — seven required sections, in order** (template: `docs/templates/resume-brief.md`) …"*

  → **[banner: correction]**. The section is replaced by *"## The handoff pair — the seat's
  DERIVED rendering + its NARRATIVE segment (dn-role-state-and-scoped-handoff §2.9)"*, opening
  with an explicit correction banner naming what changed and why: the destructively-overwritten
  ephemeral brief is superseded by a tracked, append-only seat journal plus a generated
  rendering; the seven-section schema is superseded by the checkpoint contract's entry shape;
  the self-rewrite instruction is superseded by "regenerate and commit." **Not a quiet edit** —
  the banner states that a prior ratified discipline was replaced, so a reader of the diff sees
  a correction rather than a drift.

- `.claude/skills/context-economy/SKILL.md:21` and `:58-59` — the two collateral references
  (§3 Q5). → **[cross-ref: extension]**: each is re-pointed to the handoff pair, and `:58-59`'s
  tier-declaration duty is preserved verbatim in its new home (the duty survives; only its
  container changes). This is an extension, not a correction — the rule itself was never wrong.

- `.claude/skills/checkpoint/SKILL.md` — currently opens *"The journal is the deliverable of
  the note-taking obligation: it makes context disposable. `docs/build-plans/<id>/journal.md`,
  alive while `in-progress`, sealed by `/triage` on completion."*
  → **[cross-ref: extension]**: a new section, *"## The seat journal — the same contract, one
  scope up,"* stating that `docs/roles/<role>/journal.md` uses the **same entry shape and the
  same semantic-boundary triggers**, adds compaction capsules (§2.8), and adds the NARRATIVE
  purity rule. The existing per-plan text is **not** rewritten — note §1.2 forbids changing the
  per-plan journal contract.

- `docs/templates/resume-brief.md` — **not touched by this plan.** It is quoted in §3 Q3 as
  evidence of what the rules section contains, and it is retired by bp-126, in the same diff
  as the brief's deletion. Retiring it here would leave `session-brief.sh` and clause (e)
  pointing at a template that no longer exists.

- `docs/design-notes/role-state-and-scoped-handoff.md` and `docs/design-notes/agent-workflow.md`
  — **no edit, ever.** Both are ratified and agent-immutable (A8). Corrections travel as
  findings (`finding-0233`, `finding-0234`).

## 5. Write scope

Front-matter globs, mirrored with rationale (bare globs in the front matter — no inline
comments, per finding-0085):

- `docs/roles/**` — the migration's destination: the seat journal's first authoritative
  entry and the seeded readings log.
- `.claude/skills/checkpoint/SKILL.md` — gains the seat-journal instance of the contract
  (§4).
- `.claude/skills/context-economy/SKILL.md` — the resume-brief section is replaced by the
  handoff-pair mechanics, plus the two collateral references (§3 Q5).
- `.claude/skills/commit/SKILL.md` — a receiving home for any git/staging rule evicted from
  the brief (§3 Q3/Q4). Carried because Item 3's acceptance is "every durable rule has
  exactly one home"; if a rule's home is this file and it is not in scope, that criterion is
  unbuildable.
- `.claude/skills/delegate/SKILL.md` — the receiving home for worktree/spawn rules
  (push-before-spawning, tier verification, budget gate) evicted from the brief. Carried for
  the same reason.

**Deliberately OUT of scope, and why:**

- `.claude/state/resume-brief.md` — **read-only input.** This plan does not delete, truncate,
  or rewrite it. It keeps being maintained during the overlapping window; bp-126 deletes it.
- `docs/templates/resume-brief.md` — retired by bp-126, in the same diff as the deletion.
- `.claude/hooks/**` — **no gate change.** Clause (e) still governs and `session-brief.sh`
  still surfaces the brief. bp-126 holds this surface; no two plans hold it at once.
- `scripts/**` — the generator is bp-124's; nothing here changes it.
- `CLAUDE.md` — the workflow constitution. Some brief rules (`uv run` discipline, the
  blessing gates) already live there; they are therefore *already home* and are simply
  dropped from the brief. Editing the constitution is not licensed by this design note and
  is not needed by any criterion.
- `docs/design-notes/**` — ratified, agent-immutable (A8). Amendment A10 is an owner act
  (finding-0233).
- `docs/PROGRESS.md`, `docs/PARKING-LOT.md`, `docs/inbox/owner-questions.md` — orchestrator
  single-writer surfaces and explicit non-goals of the note (§1.2). They reference the brief
  and will keep doing so; that is accepted, not a defect this plan fixes.
- `docs/book/chapters/02-architecture.tex` — references the brief; it is a scribe surface
  and becomes book debt, not builder work.
- `docs/findings/**` — **always writable** by any builder and not listed by convention;
  Item 5 uses it to flip `finding-0175` to `promoted`.

## 6. Interfaces pinned inline

**The four-way classifier (note §2.5) — the migration's decision procedure, verbatim:**

| class | definition | freshness semantics | destination |
|---|---|---|---|
| **DERIVED** | pure function of the artifact tree | regenerate; staleness impossible by construction | **dropped** — the generator reproduces it |
| **MEASURED** | result of running something (suite, `/usage`, daemon probe) | a timestamped reading; **age displayed, never hidden** | `docs/roles/orchestrator/readings.md` |
| **NARRATIVE** | judgement no generator can write | append-only; freshness = "an entry exists for this session" | `docs/roles/orchestrator/journal.md` |
| **RULES** | durable discipline | **not handoff state at all** — a rule loads at the moment of use or it does not hold | skills, hooks, templates |

**The NARRATIVE purity rule (note §2.5), verbatim — the migration's hardest constraint:**
narrative *"refers to artifacts by stable id (`bp-110`, `finding-0227`, `oq-0051`) and never
states a machine-derivable value — no commit hashes, no plan statuses, no counts, no
`path:line` into volatile code. The derivable value lives in the DERIVED pane; the id is the
join key."* Enforcement is honest tier 4 for the lintable class only (word-bounded
`[0-9a-f]{7,40}`; `status:`-transition phrasing) and review-grade for the rest.

**The MEASURED row shape (note §2.5):** append-only `(timestamp, command, one-line result)`
lines; the DERIVED pane renders the latest reading per command **with its age** —
`suite: 2 failed / 2276 passed (18h ago)` — so a stale reading advertises itself.

**The checkpoint entry shape (`.claude/skills/checkpoint/SKILL.md`, verbatim) — the seat
journal uses the same seven sections, newest entry first:**

```
1. Status line — one sentence, the current truth.
2. Completed — per criterion, with commit refs.
3. In-flight — what is mid-motion and its exact state.
4. Next action — single and concrete enough to execute without thought.
5. Open questions — typed and routed (or finding-linked).
6. Context-manifest delta — files read beyond the manifest; files that proved irrelevant.
7. Markers — mechanical lines appended by hooks (compactions, audits, HOOK-FAILUREs).
```

**Compaction — the retention rule (note §2.8), verbatim in its load-bearing part:**
seat journals and readings logs are **append-only** in the finding-0164/0168 sense — *keep
and link, never delete and replace*. Compaction is a **capsule**: one entry carrying forward
every still-live judgement (open watch-items, standing traps, in-flight intent) and naming
the range it supersedes; prior entries are **retained beneath it, marked superseded**. The
**authority rule**: after compaction the authoritative narrative is *"the latest capsule plus
all entries after it"* — everything before is history: readable, ingestable, lag-measurable,
and **non-binding**. Threshold default ~300 lines of active segment — *"a knob, not an
invariant."*

**The seven sections being retired** (`docs/templates/resume-brief.md`, for the classifier's
input map): 1 session tier · 2 in-flight · 3 then-queue · 4 design-tier deferrals · 5
standing rules · 6 open desk · 7 the self-rewrite instruction. Their fates:
1 → narrative (tier recommendation) + derived where derivable · 2 → **narrative, the
load-bearing one** · 3 → narrative · 4 → narrative · 5 → **RULES, evicted to skills** ·
6 → **derived** (the generator reads `docs/inbox/owner-questions.md`) · 7 → **deleted**, its
mechanics replaced by clause (e′) and "regenerate and commit."

**What retires and what does not (note §2.9), pinned so the boundary is unmistakable:**
this plan moves content; **bp-126** deletes `.claude/state/resume-brief.md` and
`docs/templates/resume-brief.md` and re-points `session-brief.sh`. `docs/PROGRESS.md` is
untouched by both (note §1.2).

## 7. Items

Ordered by blast radius: read-only classification → append-only writes → edits to live
contract files → an existing finding's status.

### Item 6 — classify the live brief against the four-way split

- **Objective:** produce the census: every line of the live brief assigned to exactly one of
  DERIVED / MEASURED / NARRATIVE / RULES, with the derivable ones marked for **drop**.
- **Files:** `docs/roles/orchestrator/journal.md` (the classification table is recorded in
  the migration entry itself — it is the audit trail of what was dropped and why)
- **Acceptance test:** the journal entry carries a class-by-class table with line counts
  summing to the live brief's line count, and a **named** list of every fact dropped as
  DERIVED together with the generator field that now supplies it. Re-running
  `uv run scripts/handoff.py --role orchestrator` shows each dropped fact present in the
  rendering.
- **Falsifier:** a fact classified DERIVED that the generator does **not** in fact render.
  That is content destruction masquerading as deduplication — the single worst outcome of
  this plan — and it means either the classification or bp-124's generator is wrong. Stop
  and reconcile before writing anything.
- **Invariant(s) it must not violate:** nothing is dropped without a named replacement
  source; the live brief is **not modified** (read-only input).
- **Touches stored data?** No — but it reads the only copy of an unversioned artifact.
  **Take a working copy first** (`cp` to a scratch path outside the repo) so a mis-step
  cannot destroy the input; the brief has no history to recover from — that is finding-0175's
  whole complaint.
- **Parallelizable?** No.  **Depends on:** bp-124 (the destination artifacts must exist).

### Item 7 — write the seat journal's first authoritative entry

- **Objective:** the genuinely non-derivable judgement — uncaptured owner exchanges, traps
  noticed, queue ordering, in-flight intent — lands as the seat journal's first authoritative
  entry, obeying the purity rule.
- **Files:** `docs/roles/orchestrator/journal.md`
- **Acceptance test:** the entry carries the seven checkpoint sections; `grep -Ec '\b[0-9a-f]{7,40}\b'`
  over the authoritative segment returns **0**; a grep for `status:`-transition phrasing
  returns 0; and the entry passes the fresh-agent bar by inspection — a reader with only
  `handoff.md` + this entry can name the unit in flight and the single next action.
- **Falsifier:** the entry cannot be written without a commit hash, a plan status, or a count
  — i.e. the judgement genuinely depends on a derived value. If observed, the purity rule is
  too strict for real narrative and the note's §2.5 residual R2 is understated: file a
  `spec-defect` finding rather than smuggling the value in words ("the sha ending in 4b2").
- **Invariant(s) it must not violate:** append-only — the entry is *added*, never a rewrite;
  NARRATIVE purity; single-home — no fact is copied that the generator renders.
- **Touches stored data?** No.
- **Parallelizable?** No.  **Depends on:** Item 6.

### Item 8 — seed the readings log

- **Objective:** the brief's execution-derived facts (suite results, `/usage` figures, daemon
  probes) become timestamped MEASURED rows.
- **Files:** `docs/roles/orchestrator/readings.md`
- **Acceptance test:** every reading is a `(timestamp, command, one-line result)` row; each
  timestamp is the reading's **own** time (or, where the brief did not record one, explicitly
  marked unknown rather than invented); `uv run scripts/handoff.py --role orchestrator`
  renders the latest reading per command **with its age**.
- **Falsifier:** a reading whose timestamp had to be invented to satisfy the row shape. A
  fabricated timestamp is worse than an absent one — it makes a stale reading impersonate a
  current fact, the exact failure the age-display rule exists to prevent. Mark unknown
  instead, and if the shape cannot express "unknown," that is a `spec-defect` against §2.5.
- **Invariant(s) it must not violate:** append-only; age displayed, never hidden; **MEASURED
  is never gated** — no criterion here may imply a freshness requirement on readings.
- **Touches stored data?** No.
- **Parallelizable?** Yes — independent of Item 7.  **Depends on:** Item 6.

### Item 9 — evict the rules to the skills that load them

- **Objective:** every durable rule in the brief lands in exactly one skill file, and the
  brief-as-rule-carrier is finished.
- **Files:** `.claude/skills/commit/SKILL.md`, `.claude/skills/delegate/SKILL.md`,
  `.claude/skills/context-economy/SKILL.md`, `docs/roles/orchestrator/journal.md`
- **Acceptance test:** the journal entry carries a **rule → home** table with one row per
  durable rule found; for each row, the rule's text is greppable in exactly one skill file
  (or is marked *already home* with the file that already carries it, e.g. `CLAUDE.md`); no
  rule is left with home = "the brief."
- **Falsifier:** a rule with **no** correct skill home — one that binds at no identifiable
  moment of use. That would falsify the note's RULES criterion ("a rule loads at the moment
  of use or it does not hold") and means the category is not exhaustive. File a finding; do
  not invent a "misc rules" section, which would recreate the brief inside a skill.
- **Invariant(s) it must not violate:** exactly one home per rule (no duplication — the owner
  treats duplicated content as a defect); a rule already living in `CLAUDE.md` is *already
  home* and is **not** copied into a skill; no skill gains a rule the brief did not carry.
- **Touches stored data?** No.
- **Parallelizable?** No.  **Depends on:** Item 6.

### Item 10 — the contract updates: checkpoint gains the seat, context-economy loses the brief

- **Objective:** the two skills state the new discipline, with a correction banner where a
  prior discipline is replaced.
- **Files:** `.claude/skills/checkpoint/SKILL.md`, `.claude/skills/context-economy/SKILL.md`
- **Acceptance test:** checkpoint carries a seat-journal section naming
  `docs/roles/<role>/journal.md`, the same seven-section entry shape, compaction capsules,
  and the purity rule — **and its per-plan text is otherwise byte-identical** (`git diff`
  shows additions plus only the disambiguating edits named in §4). context-economy's
  `:65-78` section is replaced under an explicit correction banner, and
  `grep -c 'resume-brief\|resume brief' .claude/skills/context-economy/SKILL.md` returns
  **0**.
- **Falsifier:** the per-plan journal contract changed. Note §1.2 forbids it explicitly
  ("NOT a change to the per-plan journal contract … clauses (a)/(f) unchanged"), and clause
  (f) greps the plan journal's tail for a verbatim `## Follow-through` header
  `[GROUNDED .claude/hooks/_lib.py:929-937]` — a reworded checkpoint contract could redden
  every future seal. If the diff touches the per-plan sections beyond disambiguation, revert.
- **Invariant(s) it must not violate:** the verbatim `## Follow-through` header and the
  five follow-through questions survive untouched; the read-map block spec survives
  untouched; the tier-declaration duty from `:58-59` survives in its new home.
- **Touches stored data?** No.
- **Parallelizable?** No.  **Depends on:** Item 9 (context-economy also receives evicted
  rules, so both edits to that file happen together).

### Item 11 — close the warrant

- **Objective:** `finding-0175` flips `routed → promoted`, its direction having landed in the
  ratified note.
- **Files:** `docs/findings/finding-0175.md` (always writable; not a `write_scope` entry)
- **Acceptance test:** the finding's front matter reads `status: promoted`, `resolution`
  names `docs/design-notes/role-state-and-scoped-handoff.md` as the note that promoted it,
  and `updated:` is today. `uv run scripts/docket.py --count` is unchanged (findings are not
  docket rows), and the session-brief's unswept-findings count drops by one
  (`open`/`routed` are the counted states `[GROUNDED .claude/hooks/_lib.py:971-973]`).
- **Falsifier:** the unswept count does **not** drop — meaning `promoted` is not recognized
  as terminal by the counter, and the flip is cosmetic. Check the counter's state list before
  claiming the criterion.
- **Invariant(s) it must not violate:** the finding's body is **not** rewritten — its wrong
  table cells are already corrected by its own 2026-07-26 triage banner, which stays as the
  record of the correction (keep-and-link, never delete-and-replace).
- **Touches stored data?** No.
- **Parallelizable?** Yes.  **Depends on:** none.

## 8. Math carried explicitly

N/A — no mathematical object is implemented. This plan performs a content classification and
prose edits; the only formal structure is the four-way partition of §6, whose correctness
condition (every line lands in exactly one class, and DERIVED drops have a named replacement
source) is Item 6's acceptance criterion rather than a mathematical claim.

## 9. Non-goals

- **No deletion.** `.claude/state/resume-brief.md` and `docs/templates/resume-brief.md` both
  survive this plan. Deleting either here would strand clause (e), which still demands a
  fresh brief, and `session-brief.sh`, which still reads one.
- **No gate change.** Clause (e) is untouched; `.claude/hooks/**` is not in scope.
- **No re-point.** `session-brief.sh` still surfaces the brief. (The note's §3 sketch put the
  re-point in P1; its §4 puts it at stage (b) with the deletion. §4 is followed — see
  `finding-0234` correction (1).)
- **No amendment.** A10 is an owner hand-act (finding-0233); §11 parks it.
- **No PROGRESS.md redesign**, no owner-queue change, no `docs/PARKING-LOT.md` edit — all
  explicit non-goals of the note (§1.2), all of which will keep referencing the brief.
- **No back-fill of legacy text.** Purity linting is scoped to entries written from the
  migration forward; nothing historical is rewritten (the readmap precedent, note §2.11 F1b).
- **No compaction.** The first authoritative entry is the first entry; there is nothing yet
  to compact. The ~300-line threshold is a knob for later (§11).
- **No new generator work.** If the rendering is missing a field the migration needs, that is
  a finding against bp-124, not an edit here (`scripts/**` is out of scope).
- **No relocation of the standing rules' *content*.** This plan moves the *category*; each
  rule's move is its own reviewed diff line, and a rule already living in `CLAUDE.md` stays
  there (note §1.2).

## 10. Stop-and-raise conditions

- **⚑ The brief is not present** (a worktree checkout, §0/§3 Q1) — **STOP before anything
  else.** Do not reconstruct it from memory, from `docs/PROGRESS.md`, or from git history;
  it has none. Say so, and have the orchestrator either re-run the plan in the main checkout
  or hand the file over. This is the plan's first check, not a mid-session discovery.
- **A DERIVED drop has no replacement in the rendering** (Item 6's falsifier) — STOP. This is
  the irreversible risk in the plan: the brief has no history, so a wrongly-dropped fact is
  gone. Reconcile before writing.
- **A rule has no skill home** (Item 9's falsifier) — file a finding and park that rule with
  a re-entry condition; do not invent a catch-all section.
- **The per-plan journal contract would have to change** (Item 10's falsifier) — STOP. Note
  §1.2 forbids it and clause (f) greps a verbatim header; a reworded contract could redden
  every future seal.
- **A criterion needs a file outside §5** — file a `codebase` finding naming file and
  criterion; never route around `scope-guard`.
- **An edit to a ratified design note is implied** — never perform it. `scope-guard` denies
  it pre-hoc `[GROUNDED .claude/hooks/_lib.py:435-441]` and the Stop gate blocks the Bash path
  `[GROUNDED .claude/hooks/_lib.py:797-824]`. Route a finding.
- **A blessing is implied** — never perform it. This plan stays `proposed`; A10 stays owner-only.
- **An owner-level question arises** — park that criterion with a re-entry condition and
  proceed with the rest. Never block on the owner.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| **Amendment A10 to `dn-agent-workflow`** (note §1.1, §3) | **Not attempted by any plan in this family.** The exact A10 text is drafted into this plan's journal so the owner can land it by hand in one paste. | (a) A builder edits `agent-workflow.md` — **impossible**: `scope-guard` denies a ratified note pre-hoc `[_lib.py:435-441]`; (b) Bash-write it — blocked post-hoc by (b2) `[_lib.py:797-824]` and would be laundering; (c) supersede the whole note — disproportionate for a lettered amendment. | The owner lands A10 by hand (same class as a blessing). Prerequisite: bp-126 merged, so the amendment describes a clause that actually exists. Warrant: `finding-0233`. |
| **V2 — is the ~300-line compaction threshold right?** (note §2.12) | ~300 lines of active segment; explicitly "a knob, not an invariant." No evidence exists either way. | Picking a measured number now — rejected: there is nothing to measure until the seat journal has been used. | The **first three compactions** are the measurement (the note's own words). Prerequisite: three real compactions recorded. |
| **V4 — do perishable capture lists belong in the seat journal?** (note §2.12) | The seat journal doubles as their home; §2.3's single-home rule already forbids duplicating them elsewhere. | Immediately promoting each to a brainstorm file (standing capture authority) — rejected as a rule: it would turn every passing note into an artifact. | The first weeks of use. If capture lists dominate the journal's active segment, promote them and record it as a finding. |
| **PROGRESS.md as a rendering of the seat journal** (note Parked decisions) | Unchanged, hand-maintained. Explicit non-goal (§1.2). | Deriving it now — rejected: PROGRESS has its own measured debt and its own consumers; coupling would fail the one-honest-read bar (the M2/K1 lesson, finding-0148). | After four weeks of seat-journal use, if PROGRESS checkpoints are observed to be restatements of journal capsules, propose the derivation in a follow-on note. |
| **The brief's collateral references in `docs/PROGRESS.md`, `docs/PARKING-LOT.md`, `docs/book/`** | Left in place; they become stale references to a deleted artifact after bp-126. | Fixing them here — rejected: PROGRESS/PARKING-LOT are orchestrator single-writer surfaces and `docs/book/` is a scribe surface; a builder editing them breaches the role split. | Orchestrator sweep at the next `/triage`; `docs/book/` at the next `/scribe` as book debt. |

## 12. Dependency & ordering summary

**Within this plan:** Item 6 → {Item 7, Item 8, Item 9}; Item 9 → Item 10. Item 11 is
independent and may run at any point. Blast-radius phase order: Item 6 (read + classify,
writes only an audit table) → Items 7/8 (append-only writes to brand-new artifacts) →
Items 9/10 (edits to **live contract files** that every session loads — the highest blast
radius here, because a wrong checkpoint edit can redden every future seal) → Item 11 (a
single front-matter flip).

**Across the family:**

```
bp-124  substrate + generator
   │
   └─→ bp-125 (this)  migration + skill contracts   — ⚑ MAIN CHECKOUT ONLY
          │
          └─→ bp-126  the atomic cutover            — clause (e′) + re-point + retirement
                 │
                 └─→ bp-127  the executable falsifier (F1b, F1c, F2)
```

- **Depends on bp-124** — the seat artifacts must exist before content lands in them.
- **bp-126 depends on this plan** — the cutover deletes the brief, so the content must
  already be migrated or it is destroyed with no history to recover it. **Load-bearing.**
- **⚑ Mutual exclusion on `.claude/hooks/**`:** this plan does not hold it (deliberately —
  see §5). bp-126 does, and no other builder may hold it while bp-126 runs (note §3).
- **Parallelizable with:** nothing in this family (all four touch `docs/roles/**`). Disjoint
  from the live ops wave: no `ready`/`in-progress` plan (bp-111…bp-119, bp-123) carries any
  `.claude/skills/**` or `docs/roles/**` glob `[GROUNDED, scanned 2026-07-26]`.
- **Execution-mode edge (not a dependency but binding):** this plan runs in the **main
  checkout**. The delegate skill's default — a worktree branched from `origin/main` — is
  wrong for this one plan, and the reason is structural, not preference (§3 Q1).
