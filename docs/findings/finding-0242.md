---
type: finding
id: finding-0242
status: open
created: 2026-07-27
updated: 2026-07-27
links:
  - docs/build-plans/bp-125/plan.md
  - docs/build-plans/bp-125/journal.md
  - docs/build-plans/bp-126/plan.md
  - docs/build-plans/bp-127/plan.md
  - docs/design-notes/role-state-and-scoped-handoff.md
  - docs/findings/finding-0239.md
  - docs/findings/finding-0240.md
  - docs/findings/finding-0241.md
  - docs/roles/orchestrator/journal.md
  - docs/roles/orchestrator/readings.md
  - .claude/skills/delegate/SKILL.md
  - .claude/skills/context-economy/SKILL.md
  - .claude/skills/checkpoint/SKILL.md
ftype: discovery
origin_plan: orchestrator
route: orchestrator
resolution: null
---

# The independent pre-merge audit of bp-125 — no content was lost, every "already home" claim
# verifies, and the migration's own bookkeeping (read map, warrant, readings order) is what broke

## What

An independent auditor (not the builder) stress-tested bp-125's delivered diff on branch
`worktree-agent-a9e53bdb393ebbb13` (7 commits on base `7ad779a`) before merge. This is the audit
record: what was verified **by execution**, what was verified **by inspection only**, and what
could **not be closed**. Verdict: **MERGE WITH CONDITIONS** — no defect below destroys content or
blocks the merge; every condition is a post-merge or pre-next-build act.

⚑ **The audit had an advantage the builder's own seal could not give it.** Both of the builder's
snapshots of the gitignored input survived in the session scratchpad, and their sha256 digests
match the two pinned in `finding-0241` exactly. The migration's *input* was therefore available to
the auditor as data, not as testimony — so the loss questions were answered by diffing the source
against the destination rather than by reading the census.

### Verified BY EXECUTION

**1. The gate, each leg run separately with output redirected to a file, never piped.**

| leg | observed | rc |
|---|---|---|
| `uv run ruff check .` | All checks passed! | 0 |
| `uv run python scripts/check_imports.py` | Import firewall (I2) OK; worker boundary (tier 4) OK | 0 |
| `uv run mypy core agents eval ops scheduler scripts` | Success: no issues found in **261** source files — floor holds at 0 | 0 |
| `uv run mypy` (ARGLESS) | **Found 69 errors in 20 files (checked 559 source files)** — exactly the pinned baseline | 1 |
| `uv run python -m ops.type_gate` | Tier-2 membership OK; bare-ignore scan OK; one parked non-fatal shim report (finding-0223) | 0 |
| `uv run pytest -q` | **2 failed, 2301 passed, 15 skipped, 12 warnings in 309.75s** | 1 |

The two failures are `tests/e2e/test_dream_v2_live.py::test_dream_v2_synthesizes_grounded_themes_live`
(finding-0226) and `tests/unit/test_core_self_containment.py::test_core_imports_nothing_outside_core`
(finding-0103). `tests/e2e/test_scheduler_live.py` passed. **No regression. The diff is markdown-only
and the suite did not move.**

**2. Scope is exactly clean.** All eleven changed paths are inside `docs/roles/**`, the four named
`.claude/skills/*/SKILL.md`, the plan's own journal, or new `docs/findings/**`. `.claude/skills/commit/SKILL.md`
was in `write_scope` and is **genuinely untouched** (no diff, no commit touches it). The worktree
contains no `.claude/state/resume-brief.md` at all — only `.gitignore` and `session-baseline` — so
the read-only-input invariant held by construction. The live file in the main checkout still hashes
to `e8860173…`, the builder's own snapshot-2 digest: **the builder never wrote to it.** No design
note, `CLAUDE.md`, `PROGRESS.md`, `PARKING-LOT.md` or `owner-questions.md` was touched. The only
`status:` transitions in the whole diff are `finding-0175` `routed → promoted` (Item 11) and the
three new findings' own front matter. **`bp-125/plan.md` still reads `status: in-progress`; no
blessing was performed.**

**3. The handoff is generated and converges in one step.** `uv run scripts/handoff.py --role
orchestrator --check` → **rc 0, "up to date"** at the branch tip. A subsequent `--write` rewrote the
file byte-identically (`git status --short` empty afterwards). Not stale, not re-arming.

**4. NARRATIVE purity has a green baseline over the WHOLE seat journal.**
`grep -Ec '\b[0-9a-f]{7,40}\b' docs/roles/orchestrator/journal.md` → **0**, and a status-transition
phrasing sweep → **0**, across all 250 lines including the preamble and all three entries.

**5. The delegate correction is TRUE, verified live rather than accepted.** `claude -p "/usage"`
was run as a one-shot from a directory outside the repo: **rc 0**, and it printed the session, week
(all-models) and week (Fable) figures directly, with no owner in the loop. The claim the diff
removes — *"no query API … the agent cannot run slash commands"* — is false as written. A repo-wide
grep for that phrasing and its neighbours finds **no other live copy**: the only two hits are the
deliberately-recorded superseded quote inside the corrected bullet itself, and bp-125's journal
quoting it. **One copy existed; one copy was fixed. The DRY concern does not apply here.**

**6. Item 11's substance is real but its stated acceptance does not hold at the tip.** The flip is
genuine (`routed → promoted`, with a `resolution` naming the ratified note and preserving the prior
text). `promoted` is genuinely terminal — `_lib.py` counts only `st in ("open", "routed")`. But the
unswept count, measured over `docs/findings/**` at three commits:

```
7ad779a (base)  112      31f95e2 (the Item 11 commit)  111      HEAD  112
```

The count **did** drop at the commit that flipped it, and then rose again when `finding-0241` was
filed as `open` two commits later. Item 11's acceptance sentence ("the unswept-findings count drops
by one") is therefore **not observably satisfied at the branch tip**, and the journal records no
measured figure for it at all — only the seal's assertion. The falsifier's *reason* ("`promoted` is
not recognized as terminal … the flip is cosmetic") is disproven; the criterion as literally worded
is not met. This is the plan's own §3 Q2 lesson landing on the plan: it wrote an *instantaneous
reading* as an acceptance test.

**7. The seal's read map is broken in two independent ways.**
`uv run scripts/readmap.py bp-125` exits **1** — *"no structured read-map block (legacy prose seal?)"*
— because the block is fenced with a bare ` ``` ` under a `### Read map` heading instead of the
` ```read-map ` info string the tool's `_BLOCK` regex requires. The sibling plan did it correctly:
`readmap.py bp-124` exits **0** and emits eight quickfix lines. Separately, **five of the eight
`path:line` targets point at the wrong place**, checked one by one:

| cited | labelled | actually at that line | correct line |
|---|---|---|---|
| `journal.md:41` | the migrated NARRATIVE | the *delta* entry's blockquote | 89 |
| `journal.md:11` | the delta entry | the file preamble | 39 |
| `finding-0241.md:36` | the digest pin | mid-prose in "What" | 62 |
| `delegate/SKILL.md:186` | sub-orchestrator owns its merges | end of the pytest-count block | 201 |
| `bp-125/journal.md:88` | the re-grounded census | the re-entry condition's closing line | 143 |

Correct: `delegate/SKILL.md:113`, `context-economy/SKILL.md:68`, `checkpoint/SKILL.md:79`. The two
seat-journal entries look **transposed**. A read map is a `:cfile` walk for the reviewer; half of
this one lands in the wrong paragraph, and the tool refuses to emit it at all.

**8. The readings log lost its ordering invariant, and the rendered pane is consequently not the
latest.** `readings.md` states *"Append-only, newest at the bottom"*, and `handoff.latest_per_command`
documents its own contract as `"Newest" is LAST-IN-FILE, not [max timestamp]`. bp-125 appended six
gate rows **below** bp-124's, two of which are **older** than the rows they now shadow:

| command | pre-existing row | appended below it | pane now shows |
|---|---|---|---|
| `uv run pytest -q` | 04:56Z (356s) | 04:53Z (234s) | **04:53Z — 3 min stale** |
| `uv run python -m ops.type_gate` | 04:49Z | 04:44Z | **04:44Z — 5 min stale** |

Benign today (both readings say the same thing), but the file's stated invariant is broken and the
pane labelled *"latest per command"* is not showing the latest. The next out-of-order append is not
guaranteed to be benign. Item 8's acceptance tested row *shape*, not monotonicity, so no criterion
caught it.

**9. A fresh measurement was taken and not recorded.** The seal's `cost.actual` reports
`week_delta 43% → 46%` with *"the 46% probed at seal"*, and the R4 correction says *"Verified live
at this seal: `claude -p "/usage"` returned the figures."* That probe is **absent from
`readings.md`** — the only `/usage` row is the migrated one, timestamped `unknown`. The artifact
whose entire purpose is "a reading you took, with its age" was handed a fresh timestamped reading
and did not receive it, while advertising an unknown-age one in its place.

**10. Absence was proven; coherence was not (Item 10).** `grep -c 'resume-brief\|resume brief'`
returns **0** in both contract skills, as required. But `grep -n '\bbrief\b'` finds a survivor:
`.claude/skills/context-economy/SKILL.md:66` — *"notice it at the next boundary and say so in **the
brief**."* Its antecedent was deleted in the same diff; the paragraph it closes now opens *"Each
seat-journal entry written at a clearing boundary MUST…"*. **A dangling reference that the
acceptance grep was structurally unable to see.** One word; but it is exactly the failure mode
"absence ≠ coherence" names.

### The six-rule claim, one by one — the highest-risk item

⚑ **First, the arithmetic is wrong.** The seal states *"Eleven durable rules were found. **Six**
were already home and were dropped rather than copied."* Its own table lists **four** rows marked
*already home* (R4, R7, R8, R9) — six are `MOVED`, one is `REPLACED`. 6 + 1 + 4 = 11. The "six" is a
miscount, and it propagated into the merge brief. The number of rules dropped on an "already home"
claim is **four**, three of which were dropped outright (R7, R8, R9) and one of which was corrected
in place (R4). All four verify:

**R7 — `git merge` does not accept `-F -`. → `commit/SKILL.md`. GENUINELY HOME.**
Source (brief:55): *"`git merge` does not accept `-F -` (unlike `git commit`). Write the message to
a file."* Destination `commit/SKILL.md:61-62`: *"⚑ Note `git merge` does **not** accept `-F -`:
write the message to the scratchpad and pass `git merge -F <file>`."* Equivalent and **stronger** —
the destination names the working flag form, which the source did not. ✔

**R8 — `git add -A` banned; stage by name; `git commit -F -` with a quoted heredoc. →
`commit/SKILL.md`. GENUINELY HOME, and materially richer.**
Source (brief:56-58) carries five clauses: `git add -A`/`git add .` banned · stage by name ·
`git status --short` first · `git commit -F -` with a **quoted** heredoc · zsh eats backticks inside
`-m` and commit bodies are not repairable because the code sensor ingests them at commit time.
Destination carries **all five** across `:34-47` (the heredoc rule, the zsh mechanism, the
not-repairable-by-amend consequence, the twice-in-session-53 provenance) and `:48-60` (the ban,
unconditional and with its reason, stage-by-name, `git status --short` first, and a **STOP** rule
the source did not have: a file you did not touch appearing in status is probably an owner
hand-edit). Nothing was lost; the destination is the fuller statement. ✔

**R9 — a lettered amendment to a ratified note is agent-impossible. → `CLAUDE.md` A8. HOME, but
the seal names only half of its home.**
`CLAUDE.md:69-70` carries the **general** rule (*"`ratified`/`superseded` are agent-immutable
(HEAD-keyed, laundering-proof)"*) and it loads every turn — the amendment case follows from it.
What `CLAUDE.md` does **not** carry is the operationally useful corollary the brief spelled out:
that `scope-guard` returns *before* the write-scope check, so listing the note in `write_scope`
does not rescue the edit. That corollary is not lost — it is in **`docs/findings/finding-0233.md`**,
tracked, `open`, routed to the owner, which states verbatim *"a lettered amendment to a ratified
note is an owner hand-act"* and grounds it at `_lib.py:435-441`. **Verdict: home, in two tracked
files rather than the one the seal named.** No loss; a mis-attribution in the table. ✔

**R4 — re-probe the budget before every spawn; refuse a spawn that cannot finish. → `delegate`.
GENUINELY HOME, and the one place the migration paid for itself.**
Source (brief:33-35). Destination `delegate/SKILL.md`: *"a worker that dies at the usage limit
mid-run, burning the tokens it already spent for nothing"* (`:109-110`, matching the source's
closing sentence); *"**Spawn only if `padded_estimate ≲ available`.** Otherwise: downsize the tier,
split the task into budget-sized units, or defer — **never start a worker that can't finish**"*
(`:128-129`, the refusal, stated more precisely than the source); and, **added by this diff**,
*"Re-probe before EVERY spawn, not once per session"* (`:121-122`) plus the self-serve probe
correction (`:112-120`), which this audit verified by running the command. ✔

⚑ **The one thing genuinely dropped without a replacement source is not a rule.** Brief line 33 also
carried *"The four plans estimate **≈1.9M tokens** before auditors."* The line was classified RULES
(dominant class), and the seal promises that *"minority content is recorded separately below"* — it
is not. `git grep` for `1.9M`, `1,900,000` and `≈1.9` over the whole branch returns **nothing**. The
figure is recomputable by summing `cost.estimate.tokens` across bp-124…bp-127, so it is recoverable
and defensibly DERIVED — but no generator renders it and the census does not list it, so it is a
drop with no named replacement. **Small, recoverable, and the only one I found in 122 lines.**

The remaining seven rules were checked as *moved*, not dropped, and each is greppable in exactly one
skill: R1/R2 (`delegate:201-222`), R3 (`delegate:139-143`), R5 (`delegate:178-186`), R6
(`delegate:188-192`), R10 (`context-economy:120-131`), R11 (replaced by "regenerate and commit",
`context-economy:94-98`). All 27 RULES-classified lines of the census map onto R1–R11 with none
left over. **No rule was left with home = "the brief."**

### Judgement on the fired falsifier (Item 6) — LEGITIMATE, and Item 6 IS discharged

The escape is **written into the design, not invented after the fact** — but not into the plan.
Item 6's acceptance says *"Re-running `uv run scripts/handoff.py --role orchestrator` shows each
dropped fact present in the rendering"* and its falsifier says *"a fact classified DERIVED that the
generator does not in fact render."* Read literally, that fires on every commit sha, and it fires
**unavoidably**: the ratified note's §2.9 idempotence pin *forbids* the generator from rendering a
sha and names `git log` as the replacement view. The plan's acceptance sentence is a **narrower
paraphrase of the note it graduates**, and the note outranks it. That is not a builder talking past
its falsifier; that is a builder catching that its plan's paraphrase contradicts its warrant.

Two things make me willing to call it discharged rather than waved through:

- The plan's own **Invariant** line for Item 6 states the substantive test in the form that
  survives: *"nothing is dropped without a named replacement source."* Not "the rendering" — *a
  named source*. The falsifier is the narrow sentence; the invariant is the honest one, and it is in
  the same item.
- The census names a source **per fact** and confines them to a closed set of two. I checked all
  thirteen against the rendered `handoff.md`: the eight marked *"YES — rendered"* are each present
  (status tally, Units-of-work table, Open-findings list, Deskchecks-owed rows, the open-owner-question
  count), and the five marked `git log` are exactly the shas §2.9 excludes. Row 11 (`oq-0035` ruled
  but still open) renders only as an aggregate count — the builder said so honestly — and the
  specific fact survives in the seat journal's narrative anyway.

**Item 6 is genuinely discharged.** The correct statement of it is "discharged against the ratified
note's §2.9, not against the plan's literal falsifier sentence," and `finding-0239` says exactly
that, with a re-entry note telling any future plan to reword the sentence.

**`finding-0240`, briefly: also legitimate.** The conflict is arithmetic, not stylistic — Item 6
names `docs/roles/orchestrator/journal.md` in its *Files* field, Item 7 requires zero word-bounded
hex over that same file, and a *named* list of dropped shas is made of word-bounded hex. Jointly
unsatisfiable in one file. Item 7's falsifier **pre-authorises this exact move** (*"file a
`spec-defect` finding rather than smuggling the value in words"*), and the plan journal was already
designated as the census's home by the plan's own *"Owed at seal"* section. Verified both halves:
seat journal returns 0 hex; the plan journal carries the full census and the rule→home table.

### Judgement on finding-0241 — the race is real, the migration is faithful and COMPLETE

I did not take this from the seal. Both snapshots survive in the session scratchpad and their
digests match the two pinned in the finding (`0a5bbfb2…` / `e8860173…`); the live file in the main
checkout still hashes to snapshot-2. I diffed them myself. The 122→125 delta is **four hunks**, and
every one is accounted for:

1. the title's HEAD sha — DERIVED, correctly dropped;
2. the wave's status line (`ready` → `in-progress` with a builder) — DERIVED, correctly dropped;
3. **the commit-economy ruling, +5 lines** — migrated;
4. the L-1 paragraph deleted and the owed-findings count decremented — handled as a correction.

**The ruling transcribes faithfully.** Every clause of the source survives in
`docs/roles/orchestrator/journal.md:55-70`: R1 (*plans/notes commit at status transitions only;
brainstorms batch*), R2 (*decouple the code sensor first — read artifacts and edit events, not
commit bodies*), the gating relation (*R2 gates R1 behind a build*), the standing consequence
(*commit practice changes nothing right now*), the explicit warning (*do not read this ruling and
start committing less tomorrow*), and the next artifact (*a design note for the sensor
decoupling*). Nothing added, nothing sharpened, nothing dropped. Hunk 4 is handled append-only and
correctly — the delta entry says *"the owed list in the entry below is one shorter"* rather than
editing the entry below. **Nothing in the delta is unaccounted for.**

I also confirmed the finding's premise independently: `git ls-files docs/brainstorms/` shows
`commit-economy-and-the-succession-path.md` is **untracked**, while
`context-load-as-a-feedback-loop.md` is tracked. Had the delta not been caught, the ruling's only
copy would have been an untracked file and a file bp-126 deletes. **That is a genuine save.**

**The finding's ask of bp-126 is concrete — with one hole.** *"If the file's digest at cutover
matches snapshot 2, nothing new arrived and the deletion is safe; if it does not, the difference is
unmigrated content and must be carried."* That is mechanical and checkable, and the re-entry
condition names both discharging forms. But the digests pin snapshots that live **only in a session
scratchpad outside the repo**, which is disposable. So if the digest does *not* match at cutover,
bp-126 can **detect** that content arrived and **cannot compute the diff** — the file is gitignored
and was never tracked, so there is no `git show` to fall back on. The instruction is a tripwire, not
a recovery.

### Verified BY INSPECTION ONLY

- **The no-capsule consequence is confirmed, with a trap bp-127 must not step in.**
  `grep -c '^## CAPSULE'` over `docs/roles/orchestrator/journal.md` → **0**; the whole file is the
  authoritative segment, and it lints clean (0 hex, 0 status phrasing) as a whole-file baseline. ⚑
  But an **unanchored** `grep '## CAPSULE'` matches **line 32** — the preamble's own prose defining
  the marker, inside backticks in a blockquote. The preamble says *"nothing else in this file may
  use it"* while itself using it. F1b must key on a heading-anchored match (`^## CAPSULE`), or it
  will find a capsule on day one and lint only the two entries above line 32.
- **The per-plan journal contract survived (Item 10's falsifier did not fire).** The verbatim
  `## Follow-through` header is present and unmodified (`checkpoint/SKILL.md:63`), the five
  questions are unchanged, the read-map block spec is unchanged, and the tier-declaration duty
  survives in its new home. bp-125's own journal carries `## Follow-through` at its tail, so clause
  (f) will pass when the orchestrator seals it. The two edits to per-plan prose (the opener and the
  fresh-agent test) are the disambiguations §4 licensed and preserve the plan bundle exactly.
- **Coherence read of the two contract skills, end to end.** Both read as complete contracts.
  Beyond the dangling *"the brief"* at `context-economy:66`, two softer holes: (a)
  `context-economy:115-118` describes the cutover window without ever **naming** the artifact a
  session must still write at close — a fresh orchestrator between this merge and bp-126 learns
  that something is owed and not what; the Stop-gate block message and `session-brief.sh` still
  name it, so the hole is bounded and temporary; (b) `checkpoint`'s new opener says *"everything
  below applies to both unless a section names one"*, after which two `## Seal entries …` sections
  and `## On the way out` describe clause (f) — a reader could conclude a seat journal needs a
  Follow-through block. It does not (clause (f) greps plan journals only), but nothing says so.
- The three new findings are correctly typed and routed: `spec-defect` → `builder` for the two the
  builder settled against code and spec (which the routing rule's own parenthetical licenses),
  `spec-defect` → `orchestrator` for the one that changes another plan's acceptance. All three
  carry re-entry conditions.
- The A10 draft is drafted, not attempted; `agent-workflow.md` is untouched.

### Did anything land that the seal did not mention?

I diffed the branch rather than trusting the summary. **No unmentioned file, no unmentioned commit.**
What the seal *asserts* but does not evidence, or gets wrong, is items 6, 7, 8, 9 and the six/four
miscount above. Nothing landed that shouldn't have.

## Why it matters

The plan's irreversible risk was content loss on a historyless file, and that risk did not
materialise: every "already home" claim verifies at its destination, the destination is usually the
stronger statement, and the one genuine drop is a recomputable token estimate. The migration also
caught a live owner ruling that would otherwise have left the system entirely — which is a better
outcome than the plan was written to expect.

What broke is the *bookkeeping around* the migration, and its shape is consistent: **five of the six
defects are instantaneous readings recorded as though they were properties** — a warrant measured at
one commit and asserted at another, line numbers captured before the file settled, readings appended
without checking they were the newest, a fresh probe taken and not written down. That is the same
defect class the whole design note exists to end, arriving inside the plan that implements it.

## The conditions (each concrete and checkable)

**None require a change to the delivered diff before merge.**

1. **Post-merge, one commit to `docs/build-plans/bp-125/journal.md`:** re-fence the read-map block
   as ` ```read-map ` and correct the five wrong line targets (table above). Checkable:
   `uv run scripts/readmap.py bp-125` exits **0** and its eight lines land on the labelled content.
2. **Post-merge, `docs/roles/orchestrator/readings.md`:** append the seal-time `claude -p "/usage"`
   probe as a properly timestamped row, and either re-order the two out-of-sequence gate rows or add
   a line to the preamble stating that the log is per-append and not globally sorted. Checkable: the
   `pytest`/`type_gate` rows the pane renders are the newest by timestamp, not merely the last.
   Regenerate the handoff after; by the idempotence pin it converges in one step.
3. **Post-merge, `.claude/skills/context-economy/SKILL.md:66`:** replace *"say so in the brief"*
   with *"say so in the entry"*. Checkable: `grep -c '\bbrief\b'` over that file returns 1 (the
   `session-brief` hook reference at `:118`, which is correct).
4. **Item 11's warrant — record the honest figure.** Either restate it as *"112 → 111 at the flip;
   112 at the tip, because `finding-0241` was filed"* in the seal, or accept that a count criterion
   over a growing directory cannot be an acceptance test. The substance (`promoted` is terminal) is
   verified in this finding and needs nothing further.
5. **Before bp-126 is built:** `finding-0241`'s diff-before-delete must become an acceptance
   criterion, **and bp-126's first act must be to copy the live brief to a tracked path** (its own
   plan journal is sufficient) *before* deleting it. A digest pinned to a disposable scratchpad
   detects a delta it cannot resolve. Checkable: `grep -c finding-0241 docs/build-plans/bp-126/plan.md` > 0
   and the plan carries a snapshot-into-the-repo step.
6. **Before bp-127 is built:** F1b's capsule detection must be **heading-anchored** (`^## CAPSULE`).
   `docs/roles/orchestrator/journal.md:32` contains the literal marker string in prose and an
   unanchored grep matches it. Checkable: F1b's own test includes a fixture whose preamble mentions
   the marker in prose and is still linted whole.
7. **Optional, low cost:** correct the seal's *"Six were already home"* to four, and add a sentence
   to `checkpoint/SKILL.md` stating that the seal sections and clause (f) bind the plan instance
   only.

## Re-entry condition

Not blocking; bp-125 is merge-ready. **Re-entry:** (a) if `uv run scripts/readmap.py bp-125` still
exits 1 at the next `/triage`, condition 1 is unfulfilled and this finding is the warrant; (b) at
bp-126's build, if the plan opens without a snapshot-into-the-repo step, stop and add it — the
digest pin alone is insufficient; (c) at bp-127's build, if F1b's capsule regex is unanchored, stop;
(d) if a future readings append is observed to shadow a newer row with an older one on a command
whose verdicts *differ*, condition 2 has become load-bearing and the log needs a sort or a guard.

## Routing

`discovery` → **orchestrator**. The verification half is closed and needs no one. The open half is
four post-merge repair commits inside surfaces the orchestrator already owns, plus two acceptance
edits to already-blessed plans (bp-126, bp-127) — orchestrator acts; no owner input is required by
any condition here.
