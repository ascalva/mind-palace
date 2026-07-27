---
type: build-plan
id: bp-127
track: workflow
status: ready
design_ref:
  - docs/design-notes/role-state-and-scoped-handoff.md
contract: builder
write_scope:
  - scripts/handoff_drill.py
  - scripts/handoff.py
  - tests/unit/test_handoff.py
  - tests/unit/test_handoff_purity.py
  - tests/integration/test_handoff_availability.py
  - docs/roles/**
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 550k
  actual: null
depends_on:
  - bp-124
  - bp-126
parallelizable_with: []
created: 2026-07-26
updated: 2026-07-26
links:
  - docs/design-notes/role-state-and-scoped-handoff.md
  - docs/findings/finding-0175.md
  - .claude/skills/checkpoint/SKILL.md
  - .claude/skills/context-economy/SKILL.md
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — the fresh-agent test made executable: F1b, F1c, and the F2 drill

> **Every section below is required.** A section that does not apply is marked
> `N/A — <one-line reason>`, never silently omitted.

## 0. Mode & provenance

Investigation and planning produced this plan; implementation proceeds item-by-item on
owner approval. It graduates `dn-role-state-and-scoped-handoff` §2.11 — the executable
falsifier — minus F1a, which is the generator's own `--check` and lands in bp-124.

Authority-to-act is separate from the readiness blessing. **This plan is `proposed`; no
agent flips it to `ready`.**

**This plan is where the family's central claim becomes falsifiable.** Everything before it
asserts that the handoff pair carries what a successor needs; this plan makes that assertion
*fail on schedule, in a worktree, at grind-tier cost, where it is a red line instead of a lost
session* (note §2.11). It is also the plan most likely to discover it cannot fully deliver —
**V1 is live here**, and the honest outcome may be a weaker drill than the note sketched.

## 1. Objective

Make the fresh-agent test executable: a purity lint over the seat journal's authoritative
segment (F1b), an availability test in a real fresh worktree with no daemon (F1c), and a
behavioral drill that spawns a history-less agent on the scope bundle and mechanically
compares its answers to the generator's (F2).

## 2. Context manifest

Read exactly these, in order, before any work:

1. `docs/design-notes/role-state-and-scoped-handoff.md` — the ratified decision, whole.
   **§2.11 is this plan's specification** (F1a/b/c and F2's probe protocol, pass/fail rule,
   and cadence); §2.12 V1 is the parked uncertainty that governs Item 17; §2.5's purity rule
   is what F1b lints; §2.8's authority rule defines "authoritative segment."
2. `.claude/skills/checkpoint/SKILL.md` — as updated by bp-125. §"The fresh-agent test" is the
   prose bar this plan makes executable; the seat-journal section defines the segment.
3. `.claude/skills/context-economy/SKILL.md` — as updated by bp-125. The **grind row** of the
   session-typing table is the tier F2's spawned agent must use (note §2.11: "a cheap-tier
   agent (grind row of the context-economy table)").
4. `scripts/handoff.py` — bp-124's generator. Its `--check` (F1a, already built), its `--json`
   structured answer (the compare's ground truth), and its `--track` / `--plan` stdout
   renderings (two of F2's three bundles).
5. `tests/unit/test_board.py` and `tests/unit/test_handoff.py` — the house shapes for a
   derived-view test and for an AST/no-core guard.
6. `tests/integration/test_worktree_enforcement.py` — the house pattern for a test that builds
   a **real** throwaway git repo and runs tooling inside it. F1c needs that shape, not a mock.
7. `scripts/orchestrator-launch.sh:40-91` — the only in-tree precedent for invoking the agent
   CLI (`claude --model … --effort … --permission-mode …`). Read for the flag forms; note what
   it does **not** demonstrate (§3 Q3).
8. `docs/findings/finding-0234.md` — the graduation-time corrections carried by this family.

**Does `core/` already implement this? (the DRY audit.)** No, and it must not. F1b is a regex
lint over markdown; F1c is an integration test; F2 is a harness that spawns a process and
compares JSON. None is a mathematical object or a reusable primitive, and all three are
repo-workflow tooling — the `scripts/board.py` / `scripts/docket.py` class, which states it
"never imports `core`" `[GROUNDED scripts/board.py:12-13]`. The **reuse** obligations that do
bind: F1a already exists as `scripts/handoff.py --check` (bp-124) and must be **called**, never
re-implemented — clause (e′) and F1a and this plan must all be the same one check
`[GROUNDED docs/design-notes/role-state-and-scoped-handoff.md §2.11 F1a: "this is also clause
(e′) check 1"]`. The judge is an **A/B against the last passing baseline**, per
CONVENTIONS §Testing — never a cold score.

## 3. Investigation & grounding  <!-- Part A -->

- **Q1 — What exactly is "the authoritative segment" F1b lints?** Note §2.8's authority rule:
  *"after compaction, the authoritative narrative is the latest capsule plus all entries after
  it. Everything before the capsule is history — readable, ingestable, lag-measurable, and
  non-binding."* So the segment is `[last compaction capsule … EOF]`, and a journal with **no**
  capsule yet is wholly authoritative. **The code does not settle the capsule's syntactic
  marker** — no capsule has ever been written, and bp-125's migration writes a first entry, not
  a capsule. What would settle it: bp-125's journal, which is the first artifact to define the
  entry shape in practice. **This plan must read that file and adopt whatever marker it
  established, or — if bp-125 left the marker undefined — define one, state it in the journal,
  and file a `codebase` finding so the two artifacts do not drift.**

- **Q2 — What precisely does F1b lint for?** Note §2.11: *"zero word-bounded
  `[0-9a-f]{7,40}` tokens and zero `status:`-transition phrases in the seat journal's
  authoritative segment; hit = FAIL. Scoped to entries post-migration; legacy text is not
  back-filled (the readmap precedent)."* Two honest limits, both stated in the note and
  neither to be overclaimed: the lint is **tier 4 for the lintable class only**, and R2 records
  that an agent can still smuggle a count in prose, which "only review or the §2.11 drill
  catches." The word-boundary requirement is load-bearing: without `\b` the pattern matches
  inside ordinary words (`deadbeef` in prose, or any run of hex letters), which would make the
  lint fire on legitimate narrative and train people to ignore it.

- **Q3 — How does the F2 harness spawn a history-less, read-only agent?**
  **The code does not settle this, and it is this plan's single largest unknown.** Grounded:
  the CLI is invoked in-tree as `claude --model "$MODEL" --effort "$EFFORT" --permission-mode
  "$PERM"` `[GROUNDED scripts/orchestrator-launch.sh:47,89,91]`, and headless auth via
  `CLAUDE_CODE_OAUTH_TOKEN` is an established pattern `[GROUNDED scripts/orchestrator-launch.sh:19,54-64]`.
  **Not** grounded anywhere in the tree: a **non-interactive one-shot** invocation, a way to
  guarantee **no conversation history**, and a way to restrict the spawned agent to the bundle
  with **tools disabled or read-only** — all three of which §2.11 requires ("no conversation
  history … Nothing else; tools disabled or read-only"). What would settle it: the agent CLI's
  own `--help` for the print/one-shot and tool-restriction flags, run once and recorded as a
  MEASURED reading. **The builder must establish this before writing the harness** — Item 17's
  first act — and if a history-less read-only spawn is not achievable, that is a finding, not
  an approximation. A drill whose agent can read the whole repo is not a fresh-agent test; it
  tests nothing.

- **Q4 — Is the F2 pass/fail rule fully mechanical?** No — deliberately, and the note is
  precise about which half is which. Mechanical: *"(1) and (2) must match the generator's own
  structured answer (the generator emits the expected fields as JSON alongside the rendering —
  a string/field compare, fully mechanical)."* Subjective: *"any `BLOCKED:` line whose answer a
  judge locates inside the bundle … the one genuinely subjective check, run as a model-judge
  A/B against the last passing baseline per CONVENTIONS §Testing, never scored cold."* And the
  asymmetry that makes the drill useful rather than merely strict: *"A `BLOCKED:` line whose
  answer is genuinely absent is a **pass with a defect report** — the drill found
  under-specified state, which is its job."*

- **Q5 — Is V1 already answerable from the tree?** Not fully. V1 asks whether *"the single next
  action"* resists canonical form (note §2.12). bp-124 Item 5 builds `--json` with
  `unit_in_flight` and `next_action`, and its own falsifier is precisely V1 landing early. By
  the time this plan runs, bp-124's journal either records that `next_action` is derivable or
  records that it is not. **Read that journal first**; do not re-litigate. If it is not
  derivable, Item 17 ships the degraded form and **says so in the plan's journal and in the
  harness's own output** — the note requires that the plan say so, not that it quietly weaken.

- **Q6 — What environment does F1c actually require?** Note §2.11 F1c: *"in a fresh worktree of
  `origin/main` with no daemon running, the generator must exit 0, rendering `queue:
  unavailable` rather than erroring, and the committed journal + rendering must be present
  (tracked ⇒ present in every checkout). This is the §2.6 hard constraint as a test, run in the
  environment that motivated it."* Grounded that this is a real condition and not a
  hypothetical: a fresh worktree's `.claude/state/` contains only `.gitignore`, and `data/` is
  not in the tree, so `data/queue.sqlite` genuinely does not exist there (verified 2026-07-26).
  The house pattern for building a real throwaway repo and running tooling in it is
  `tests/integration/test_worktree_enforcement.py`.

- **Q7 — Where is the drill's result recorded?** Note §2.11: *"Result recorded as a MEASURED
  reading (the drill is itself execution-derived)"* — i.e. an appended
  `(timestamp, command, one-line result)` row in `docs/roles/orchestrator/readings.md`, whose
  age the DERIVED pane then displays. **Cadence:** *"every `/triage`, and mandatorily in any
  build plan that touches the handoff machinery."* The cadence obligation is documentation, and
  its home is a skill — **out of this plan's scope** (bp-125 owns the skills); the builder
  records the obligation in its journal and files it for the orchestrator, rather than editing a
  skill it does not hold.

**Additional risks or questions surfaced during reading:**

- **F2 costs real tokens on every run.** The note prices it at grind tier deliberately. A drill
  that is expensive is a drill that gets skipped; if the spawn cannot be made cheap, its cadence
  claim ("every `/triage`") is not credible and that is worth a finding.
- **`scripts/handoff.py` is in this plan's write scope**, which means bp-124's tests can redden.
  `tests/unit/test_handoff.py` is carried for exactly that reason (§5).
- The three F-items are independently valuable. If F2 fails entirely, F1b and F1c still ship
  and the plan is a partial success, not a failure — the item ordering reflects that.

## 4. Reconciliation  <!-- Part B -->

- `docs/design-notes/role-state-and-scoped-handoff.md:452-453` — the note states the fresh-agent
  bar *"exists as prose"* `[GROUNDED .claude/skills/checkpoint/SKILL.md:70-75]` and is *"made
  executable"* here. → **[cross-ref: extension]**: the drill **extends** the prose bar; it does
  not replace it. The checkpoint skill's fresh-agent paragraph stays authoritative for the
  per-plan case and gains a pointer to the drill for the seat case. **That pointer is bp-125's
  edit, not this plan's** (`.claude/skills/**` is out of scope, §5) — the builder files the
  one-line addition for the orchestrator to route rather than making it.

- `scripts/handoff.py` — if Item 17 needs a change to the `--json` field set for the compare to
  work, that is an **extension** of bp-124's contract, not a correction of it. →
  **[cross-ref: extension]**: any field added is documented in the script's docstring as
  "added for the F2 compare (bp-127)", and `tests/unit/test_handoff.py` gains the assertion. If
  instead a bp-124 field turns out to be **wrong**, that is a correction and it carries a
  `codebase` finding naming bp-124 — never a quiet redefinition of a merged plan's output.

- **Nothing else is corrected.** `.claude/hooks/**` is untouched (bp-126 owns it and clause (e′)
  already calls F1a); the skills are untouched (bp-125 owns them); the ratified notes are
  agent-immutable (A8) and their errors travel as findings.

## 5. Write scope

Front-matter globs, mirrored with rationale (bare globs in the front matter — no inline
comments, per finding-0085):

- `scripts/handoff_drill.py` — the F2 harness. New file.
- `scripts/handoff.py` — carried because F1b's lint may land as a `--lint` mode on the
  generator (one entry point for the handoff machinery), and because Item 17 may need to extend
  the `--json` field set for the compare (§4). If neither proves necessary the file is simply
  not touched.
- `tests/unit/test_handoff.py` — **carried because it pins the surface this plan may move.**
  It asserts `--json`'s shape and the generator's CLI (bp-124 Item 5); adding a `--lint` mode or
  a JSON field reddens it, and it is outside a naïve "new files only" scope.
- `tests/unit/test_handoff_purity.py` — F1b's tests. New file.
- `tests/integration/test_handoff_availability.py` — F1c. New file; integration-marked because
  it builds a real throwaway repo.
- `docs/roles/**` — the drill's result is recorded as a MEASURED reading in
  `readings.md` (§3 Q7), and F1b/F2 read the seat journal as their subject.

**Deliberately OUT of scope, and why:**

- `.claude/hooks/**` — bp-126's, and already merged by the time this runs. Clause (e′) already
  calls F1a; this plan adds no gate and changes no clause. **Two plans must never hold
  `.claude/hooks/**`.**
- `.claude/skills/**` — bp-125's. Two documentation duties surface here (the drill's cadence,
  §3 Q7; the checkpoint pointer, §4) and **both are filed for the orchestrator rather than
  edited**, precisely because this plan does not hold that surface.
- `scripts/board.py` — untouched; nothing here changes the board.
- `docs/design-notes/**` — ratified, agent-immutable (A8). V1's outcome is recorded in the
  journal and as a finding, never as an edit to the note.
- `pyproject.toml` — **not needed**: `scripts` and `tests` are already in `[tool.mypy] files`
  `[GROUNDED pyproject.toml:128]`, so all four new/changed files are enrolled automatically.
- `docs/PROGRESS.md`, `docs/inbox/owner-questions.md` — orchestrator single-writer surfaces.
- `docs/findings/**` — always writable, not listed by convention. Expect to use it: V1's
  resolution and any `BLOCKED:`-line defect report are findings.

## 6. Interfaces pinned inline

**F1b — the purity lint (note §2.11, verbatim):**

> *"**F1b purity lint:** zero word-bounded `[0-9a-f]{7,40}` tokens and zero `status:`-transition
> phrases in the seat journal's authoritative segment (capsule + suffix); hit = FAIL. Scoped to
> entries post-migration; legacy text is not back-filled (the readmap precedent)."*

The rule it enforces (note §2.5, verbatim): *"narrative refers to artifacts by stable id
(`bp-110`, `finding-0227`, `oq-0051`) and never states a machine-derivable value — no commit
hashes, no plan statuses, no counts, no `path:line` into volatile code. The derivable value
lives in the DERIVED pane; the id is the join key."*

**The authoritative segment (note §2.8, verbatim):** *"after compaction, the authoritative
narrative is **the latest capsule plus all entries after it**. Everything before the capsule is
history — readable, ingestable, lag-measurable, and *non-binding*: a fresh agent reads capsule +
suffix and may stop there."*

**F1c — availability (note §2.11, verbatim):**

> *"**F1c availability:** in a **fresh worktree of `origin/main` with no daemon running**, the
> generator must exit 0, rendering `queue: unavailable` rather than erroring, and the committed
> journal + rendering must be present (tracked ⇒ present in every checkout). This is the §2.6
> hard constraint as a test, run in the environment that motivated it."*

The constraint it tests (note §2.6): **the handoff must be readable with no running system.**
Fresh worktrees have no `data/queue.sqlite` at all — `data/` is not in the tree — so "the daemon
being down is survivable for SQLite, but the file not being *present* is not."

**F2 — the behavioral drill (note §2.11, verbatim; this is the spec, not a summary):**

> - **Spawn:** a cheap-tier agent (grind row of the context-economy table) in a fresh worktree
>   from `origin/main`, no daemon, **no conversation history**.
> - **Inputs, exactly:** the scope bundle — for `role:orchestrator`: `handoff.md` + the
>   journal's authoritative segment; for `plan:<id>`: `plan.md` + its journal (the classic test,
>   now also drilled); for `track:<slug>`: the on-demand track rendering. Nothing else; tools
>   disabled or read-only.
> - **Probe protocol:** the agent must output (1) the unit currently in flight, (2) the single
>   concrete next action, (3) every blocking unknown as a literal `BLOCKED: <question>` line.
> - **Observable pass/fail:** (1) and (2) must match the generator's own structured answer (the
>   generator emits the expected fields as JSON alongside the rendering — a string/field
>   compare, fully mechanical). **FAIL** on: any mismatch; OR any `BLOCKED:` line whose answer a
>   judge locates *inside the bundle* (the "re-asks something already answered" clause — the one
>   genuinely subjective check, run as a model-judge A/B against the last passing baseline per
>   CONVENTIONS §Testing, never scored cold). A `BLOCKED:` line whose answer is genuinely absent
>   is a **pass with a defect report** — the drill found under-specified state, which is its job.
> - **Cadence:** every `/triage`, and mandatorily in any build plan that touches the handoff
>   machinery. Result recorded as a MEASURED reading (the drill is itself execution-derived).

**The grounded CLI invocation form `[scripts/orchestrator-launch.sh:47,89,91]`:**

```bash
exec claude --model "$MODEL" --effort "$EFFORT" --permission-mode "$PERM"
```

⚑ **This is interactive.** A non-interactive one-shot, a no-history guarantee, and tool
restriction are **not** demonstrated anywhere in the tree — see §3 Q3. Establish them first.

**The MEASURED row shape (note §2.5):** append-only `(timestamp, command, one-line result)`;
the DERIVED pane renders the latest reading per command **with its age**.

**V1, verbatim (note §2.12) — the parked uncertainty that governs Item 17:**

> *"**V1:** Does the F2 JSON-answer compare survive contact with real renderings, or does 'the
> single next action' resist canonical form? If it resists, F2 degrades to judge-only — weaker,
> and the plan that builds the drill must say so. (Blocks §2.11 acceptance criteria.)"*

**Why the drill exists at all (note §2.11), the sentence to keep in view:** *"a broken handoff
is invisible until a real session fails; F2 makes the failure happen on schedule, in a worktree,
at grind-tier cost, where it is a red line instead of a lost session."*

## 7. Items

Ordered by blast radius: a pure-function lint → a read-only integration test → a harness that
spawns a real agent and spends real tokens.

### Item 15 — F1b: the narrative purity lint

- **Objective:** a lint that fails when the seat journal's authoritative segment contains a
  machine-derivable value of the lintable class.
- **Files:** `scripts/handoff.py` (a `--lint` mode) or a function in `scripts/handoff_drill.py`;
  `tests/unit/test_handoff_purity.py`
- **Acceptance test:** `uv run pytest tests/unit/test_handoff_purity.py` green, covering: a
  fixture segment containing `a1b2c3d` (7 hex, word-bounded) → **FAIL**; a segment containing
  `bp-110` and `finding-0227` → **PASS** (ids are the join key, explicitly allowed); a segment
  containing a `status:` transition phrase → **FAIL**; text **before** a compaction capsule
  containing hashes → **PASS** (history is not back-filled); and the **live**
  `docs/roles/orchestrator/journal.md` authoritative segment → **PASS**.
- **Falsifier:** the lint fires on the live journal's legitimate narrative — i.e. real judgement
  cannot be written without tripping it. That means the pattern is too broad (most likely the
  `\b` boundary is missing, so hex letters inside ordinary words match) and the lint would train
  people to ignore it, which is worse than no lint. Tune or narrow; do not add a suppression
  comment convention, which would make the rule optional.
- **Invariant(s) it must not violate:** ids (`bp-`, `finding-`, `oq-`) are **never** violations;
  history before the last capsule is out of scope; the lint is honest about its tier — its
  output and docstring must say it covers the lintable class only (R2), never claim general
  purity.
- **Touches stored data?** No.
- **Parallelizable?** Yes.  **Depends on:** bp-125 (a migrated journal to lint), §3 Q1 (the
  capsule marker).

### Item 16 — F1c: availability in a fresh worktree with no daemon

- **Objective:** prove the §2.6 hard constraint in the environment that motivated it — a
  checkout with no `data/`, no daemon, and no `.claude/state/` beyond `.gitignore`.
- **Files:** `tests/integration/test_handoff_availability.py`
- **Acceptance test:** `uv run pytest tests/integration/test_handoff_availability.py` green: in
  a **fresh worktree of `origin/main`** with no daemon, `scripts/handoff.py --role orchestrator`
  **exits 0**; its output contains `queue: unavailable`; `docs/roles/orchestrator/journal.md`
  and `handoff.md` are both **present** (the tracked ⇒ present-in-every-checkout claim); and no
  `data/queue.sqlite` exists in that worktree **before or after** the run.
- **Falsifier:** the generator exits non-zero, raises, or **creates** `data/queue.sqlite` in the
  fresh worktree. Creating it would breach the single-writer model
  `[GROUNDED scheduler/queue.py:17-18]`. Equally falsifying: the seat artifacts are **absent**
  in the fresh worktree, which would mean they were never actually tracked — the entire §2.7
  versioning ruling silently unbuilt.
- **Invariant(s) it must not violate:** the test uses a **real** worktree (the
  `test_worktree_enforcement.py` pattern), not a mocked filesystem — a mock cannot falsify a
  claim about what exists in a checkout; the test never starts the daemon; it leaves no
  artifacts behind.
- **Touches stored data?** No — it asserts the **absence** of a queue file and must not create
  one.
- **Parallelizable?** Yes — independent of Item 15.  **Depends on:** bp-124, bp-126.

### Item 17 — F2: the fresh-agent drill harness

- **Objective:** a runnable drill that spawns a history-less, read-only agent on a scope bundle
  and mechanically compares its answers to the generator's.
- **Files:** `scripts/handoff_drill.py`, `scripts/handoff.py` (only if the `--json` field set
  needs extending), `tests/unit/test_handoff.py`, `docs/roles/orchestrator/readings.md`
- **Acceptance test:** `uv run scripts/handoff_drill.py --scope role:orchestrator` (a) builds
  the bundle from `handoff.md` + the journal's authoritative segment and **nothing else**;
  (b) spawns a grind-tier agent with no conversation history and read-only/disabled tools;
  (c) parses the three probe outputs; (d) compares fields (1) and (2) against
  `handoff.py --json`; (e) exits **0** on match with zero in-bundle-answerable `BLOCKED:` lines,
  **non-zero** on a mismatch, and **0 with a printed defect report** on a genuinely-absent
  `BLOCKED:` answer; (f) appends the result as a MEASURED row to `readings.md`. A unit test
  covers the parse/compare/exit-code logic against **recorded** agent output (no spawn), so the
  logic is testable without spending tokens.
- **Falsifier:** ⚑ **the spawned agent can read outside the bundle.** Verify positively, not by
  assumption: put a fact **only** in a repo file outside the bundle and confirm the agent
  reports `BLOCKED:` on it rather than answering. If it answers, the drill is not a fresh-agent
  test — it is testing the repo, and every future PASS is meaningless. Second falsifier: `(2)`
  never matches because `next_action` has no canonical form — that is **V1 landing**, and the
  plan must **say so** (§11), degrading to judge-only rather than loosening the compare until it
  passes.
- **Invariant(s) it must not violate:** the judge is an **A/B against the last passing
  baseline**, never a cold score (CONVENTIONS §Testing); a genuinely-absent answer is a **pass
  with a defect report**, never a failure — the drill's job is to *find* under-specified state;
  the drill **never writes** to the bundle it is testing; it never starts the daemon.
- **Touches stored data?** Appends one MEASURED row to `readings.md` (append-only, reversible).
  It also **spends real tokens on every run** — the blast radius here is budget, not data.
  **Dry-run first:** exercise the full pipeline against recorded output before the first live
  spawn.
- **Parallelizable?** No.  **Depends on:** Items 15 and 16 (both are cheap and prove the bundle
  is well-formed before a spawn is paid for), bp-124 Item 5 (`--json`), bp-126.

## 8. Math carried explicitly

N/A — no mathematical object is implemented. The plan builds two lints and a test harness. The
one quasi-formal notion, "the authoritative segment" (`[last capsule … EOF]`, note §2.8), is a
text-range definition pinned verbatim in §6 rather than a mathematical object with validity
assumptions; its correctness condition is Item 15's fixture set, not a field-guide entry.

## 9. Non-goals

- **No F1a.** The cannot-drift check is `scripts/handoff.py --check`, built in bp-124 and
  consumed by clause (e′) in bp-126. This plan **calls** it and must not re-implement it — three
  copies of one check is exactly the DRY defect the owner treats as a bug.
- **No gate change.** `.claude/hooks/**` is out of scope; the drill is invoked by a human or by
  `/triage`, never by a hook. Wiring the drill into the Stop gate is not licensed by the note.
- **No skill edits.** The cadence obligation (§3 Q7) and the checkpoint pointer (§4) are
  **filed for the orchestrator**, not made here.
- **No CI wiring.** The note says F1 is "available to CI"; making it a CI leg is a separate,
  reviewed change to the gate's composition.
- **No back-fill.** Legacy narrative before the migration is never linted or rewritten (the
  readmap precedent).
- **No judge-quality scoring.** The gate guarantees existence, freshness, and one lintable
  purity class — **never that the prose is good** (note §1.2). The judge answers exactly one
  question: is this `BLOCKED:` line's answer inside the bundle?
- **No plan/track drill bundles beyond what `--scope` supports.** `plan:<id>` and `track:<slug>`
  bundles are specified in §6 and should be supported if cheap, but `role:orchestrator` is the
  only one whose acceptance is required here.
- **No design-note edit** to record V1's outcome — that is a finding (A8).

## 10. Stop-and-raise conditions

- **⚑ A history-less, bundle-restricted spawn cannot be achieved** (§3 Q3) — **STOP and file a
  finding.** Do **not** ship a drill whose agent can read the repo: it would report PASS forever
  while testing nothing, which is worse than having no drill, because it manufactures
  confidence. Items 15 and 16 still ship; the plan closes partial and honest.
- **⚑ V1 lands — `next_action` has no canonical form** — do **not** loosen the compare until it
  passes. Degrade to judge-only, **say so** in the plan's journal, in the harness's own output,
  and in a finding (the note requires the plan to say so). A compare weakened until it passes is
  a test that cannot fail.
- **F1b fires on the live journal's legitimate narrative** (Item 15's falsifier) — stop and
  narrow the pattern; a lint that cries wolf gets suppressed and then the rule is gone.
- **The seat artifacts are absent in a fresh worktree** (Item 16's falsifier) — STOP. That
  falsifies the note's §2.7 versioning ruling and means bp-124/125 did not actually track them.
  File a `spec-defect` finding against whichever plan owned it.
- **The drill's per-run cost makes its stated cadence implausible** — record the measured cost
  and file a finding rather than quietly assuming `/triage` will run it.
- **The capsule marker is undefined** (§3 Q1) — define one, state it in the journal, and file a
  `codebase` finding so bp-125's artifact and this lint cannot drift apart.
- **A criterion needs a file outside §5** — file a `codebase` finding naming file and criterion;
  never route around `scope-guard`.
- **An edit to a ratified design note is implied** — never perform it
  `[GROUNDED .claude/hooks/_lib.py:435-441]`. Route a finding.
- **A blessing is implied** — never perform it.
- **An owner-level question arises** — park the criterion with a re-entry condition and continue
  with the rest. Never block on the owner.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| **⚑ V1 — does the JSON-answer compare survive contact?** (note §2.12; **blocks Item 17's acceptance**) | Ship the mechanical compare on `unit_in_flight`; if `next_action` resists canonical form, **degrade F2 to judge-only for that field and state the degradation** in the journal, in the harness output, and in a finding. | (a) Loosen the compare (fuzzy match, substring) until it passes — rejected: a test tuned until green cannot fail, and that is the one thing a falsifier must be able to do; (b) drop field (2) silently — rejected: the note explicitly requires the plan to *say so*. | bp-124's journal already records whether `next_action` proved derivable (§3 Q5) — **read it before starting**. Re-entry after: three real drill runs showing whether the mechanical compare holds. |
| **The spawn mechanism** (§3 Q3) | Not pinned; established empirically as Item 17's first act and recorded as a MEASURED reading. | Assuming a flag exists — rejected: nothing in the tree demonstrates a non-interactive, history-less, tool-restricted spawn, and assuming it is how a drill silently tests nothing. | The CLI's own `--help`, run once and recorded. If no such mode exists, the harness is blocked and that is a finding, not a workaround. |
| **F1b's home: a `--lint` mode on `handoff.py` vs a drill-local function** | Not pinned. Both are in scope; pick the one that keeps a single entry point for the handoff machinery. | Neither is rejected — this is a genuine implementation coin-flip with no design consequence, recorded so it is a decision rather than an accident. | A second consumer of the lint (e.g. a CI leg), which would settle it toward `handoff.py --lint`. |
| **Wiring F1 into CI** | Not done here (§9). | Doing it now — rejected: the local CI gate's composition is its own reviewed change, and the note only says F1 is "available to CI." | The drill proving stable over three `/triage` cycles. |
| **The compaction-capsule marker** (§3 Q1) | Adopt whatever bp-125's migration established; if undefined, define one and file a finding. | Inventing a marker unilaterally without filing — rejected: two artifacts would define the segment differently and the lint would silently mis-scope. | bp-125's journal, read at session start. |
| **`plan:` and `track:` drill bundles** | Supported if cheap; only `role:orchestrator` acceptance is required. | Requiring all three — rejected: it triples the spawn cost of an already token-expensive drill before its value is demonstrated. | The role drill proving useful over three cycles. |

## 12. Dependency & ordering summary

**Within this plan:** Item 15 ∥ Item 16 (independent; different files, different subjects) →
Item 17. Blast-radius phase order: a pure-function lint over text (Item 15) → a read-only
integration test asserting absences (Item 16) → a harness that **spawns a real agent and spends
real tokens** (Item 17), last because it is the only item with an external effect and the only
one whose feasibility is genuinely unknown.

**Across the family:**

```
bp-124  substrate + generator          (F1a lands here as --check)
   └─→ bp-125  migration + skills      (MAIN CHECKOUT ONLY)
          └─→ bp-126  the atomic cutover
                 └─→ bp-127 (this)  F1b, F1c, F2
```

- **Depends on bp-124** — Item 17 consumes `--json`; Item 16 exercises the generator.
- **Depends on bp-126** — Item 16 asserts the **post-cutover** checkout, and F1b lints the
  authoritative segment the new clause (e′) keys on. (bp-125 is a transitive dependency through
  bp-126; it is not listed in `depends_on` because bp-126 already requires it, and Item 15 needs
  the migrated journal that bp-125 produced.)
- **This plan is the family's terminal node.** After it, the note's §4 enablement is complete
  except the owner's two hand-acts: amendment A10 (finding-0233) and the first live
  resume-from-`handoff.md` session (note §4(c)).
- **⚑ Mutual exclusion:** this plan does **not** hold `.claude/hooks/**`; bp-126 does, and must
  be merged before this starts. No other builder may hold `scripts/handoff.py` concurrently —
  it is in this plan's scope and bp-124's.
- **Parallelizable with:** nothing in this family (all four touch `docs/roles/**`; three touch
  `scripts/handoff.py` or its tests). Disjoint from the live ops wave as scanned 2026-07-26.
