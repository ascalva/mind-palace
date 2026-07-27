---
type: journal
plan: bp-125
started: 2026-07-27
updated: 2026-07-27
---

# Journal — bp-125 (migrate the live brief into the seat, and re-home its rules)

Minted 2026-07-26 by `/graduate`, decomposing ratified `dn-role-state-and-scoped-handoff`
(blessed `c0abfd1`). Second of four (bp-124…bp-127). **Not started.**

## Pre-build notes for whoever picks this up

- ⚑⚑ **THIS PLAN CANNOT RUN IN A WORKTREE.** Its input, `.claude/state/resume-brief.md`, is
  gitignored (`.claude/state/.gitignore` ignores `*`) and therefore **absent from every fresh
  checkout**. Measured 2026-07-26: the main checkout holds a 498-line / 36,701-byte brief; a
  fresh worktree of `origin/main` holds only `.claude/state/.gitignore`. **Run in the main
  checkout**, or have the orchestrator hand the file over before spawn and say so here. The note
  does not mention this; `docs/findings/finding-0234.md` correction (2) carries it.
- ⚑ **The brief has NO history.** It is gitignored and destructively overwritten — that is
  finding-0175's entire complaint. **Copy it to a scratch path outside the repo before touching
  anything.** A mis-step is unrecoverable.
- ⚑ **The irreversible risk is a wrong DERIVED drop.** A fact classified DERIVED but not actually
  rendered by `scripts/handoff.py` is destroyed, not deduplicated. Item 6's acceptance requires a
  **named replacement source** for every dropped fact, verified by running the generator. Do not
  take the classification on faith.
- **Do not delete anything.** Both `.claude/state/resume-brief.md` and
  `docs/templates/resume-brief.md` survive this plan; `session-brief.sh` still surfaces the
  brief; clause (e) still governs. That is the note's deliberately overlapping window (§4 stage
  (a)) and the double bookkeeping is accepted for its duration. Deleting here would strand
  clause (e) and deadlock every orchestrator close.
- **Do not re-point `session-brief.sh`.** The note's §3 sketch put the re-point in P1; its §4
  puts it at stage (b) with the deletion. §4 is followed — see finding-0234 correction (1). A
  re-point without the clause change means the orchestrator must keep writing a brief it can no
  longer see.
- ⚑ **Do not touch the per-plan journal contract.** Note §1.2 forbids it, and Stop-gate clause
  (f) greps the plan journal's tail for a **verbatim** `## Follow-through` header
  (`.claude/hooks/_lib.py:929-937`). A reworded checkpoint contract could redden every future
  seal. checkpoint gains a seat section; its per-plan text stays byte-identical except for the
  disambiguating edits named in §4.
- **context-economy has three brief references, not one:** the `:65-78` section **and** `:21`
  (the decision rule) **and** `:58-59` (the tier-declaration duty). Editing only the section
  leaves two live references to a soon-to-be-deleted artifact. The tier-declaration duty
  **survives verbatim** in its new home — the rule was never wrong, only its container.
- **A rule already living in `CLAUDE.md` is already home.** `uv run` discipline and the blessing
  gates are there; drop them from the brief rather than copying them into a skill. `CLAUDE.md`
  is deliberately out of `write_scope` — no criterion needs it.
- **Amendment A10 is not attempted here or anywhere in this family.** `agent-workflow.md` is
  ratified and `scope-guard` denies the write before write_scope is even consulted
  (`_lib.py:435-441`). See `docs/findings/finding-0233.md`. Draft the A10 text into this journal
  for the owner to land by hand; do not attempt the edit.

## Owed at seal (orchestrator, not the builder)

- A `## Follow-through` block is required by clause (f).
- The **rule → home** table from Item 9 and the **class census** from Item 6 are the audit trail
  of what was moved and what was dropped. They must survive in this journal, not only in a diff.
- The **capsule marker** question: bp-127's F1b lint scopes to "the latest capsule plus all
  entries after it." If this migration's first entry establishes a capsule marker, **state it
  explicitly here** — bp-127 reads this journal for it (its §3 Q1). If it does not, say that too.
- `finding-0175 → promoted` (Item 11) — confirm the unswept-findings count actually dropped;
  `open`/`routed` are the counted states (`.claude/hooks/_lib.py:971-973`).
- Collateral brief references in `docs/PROGRESS.md`, `docs/PARKING-LOT.md` and
  `docs/book/chapters/02-architecture.tex` are **out of role** for a builder — file them for the
  orchestrator sweep and the next `/scribe`.

---

## ⚑⚑ RE-ENTRY CONDITION ADDED BY THE ORCHESTRATOR AT MERGE — 2026-07-26

**THIS PLAN'S INPUT CHANGED WHILE IT WAS BEING PLANNED. Re-ground §3 before building.**

bp-125 migrates the live resume brief's non-derivable content into the seat. It was graduated
against a **568-line** `.claude/state/resume-brief.md`. While this graduation was in flight, the
orchestrator **cleared and rewrote that brief to 83 lines** on the owner's instruction
(*"clear the handoff right now"*), restructuring it into the four panes this note's own design
prescribes — DERIVED / MEASURED / NARRATIVE / RULES-elsewhere.

**Consequence for the builder:** §3's grounding describes a document that no longer exists. Any
line count, section name, or content census in this plan must be **re-taken against the live file**
before Item 1. Do not trust a quoted figure.

**The work is smaller, not different.** The narrative/readings/rules separation this plan performs
by hand has largely been done once already, manually — so the migration is now closer to
"formalize an existing structure" than "impose one on prose." That is a scope *reduction*, and the
`cost.estimate` is now likely high. Record the actual at seal; do not tune the estimate now
(the estimate/actual gap is the forecasting dataset).

⚑ **This is finding-0191's exact shape** — *a plan's §3 census silently perished between authoring
and build* — arriving again, **caused by the orchestrator**, in the same session it was cited as a
known hazard. It is recorded here rather than only in the merge commit because the builder reads
the journal, not the merge log.

---

## 2026-07-27 — Item 6 closed: the brief re-grounded and classified

**Status line.** The live brief was snapshotted, re-measured against every figure this plan quotes
(all three were stale), and classified line-by-line into the four-way split; the census sums
exactly to the file's length and every DERIVED drop has a named replacement source.

**Completed.**

*Item 6 — classify the live brief against the four-way split.*

⚑ **The plan ran in a WORKTREE, not the main checkout.** §0 and §10's first stop-and-raise
condition demand the main checkout because the brief is gitignored and absent from a fresh
checkout. The orchestrator discharged that condition the sanctioned way — §0's second branch, *"or
have the orchestrator copy the brief into the worktree before spawn and say so in the journal"* —
by handing over the absolute path to the live file in the main checkout. **Step 0 was to snapshot
it outside the repo before reading anything**, per the pre-build note: the brief has no history and
a mis-step is unrecoverable.

Base commit verified `7ad779a`, as the delegation stated.

Snapshot, taken before any other act:

```
     122    8196 …/scratchpad/resume-brief.SNAPSHOT.md
0a5bbfb28b829ed1a7203fd568f97d146415a31c9cb713309ec137f3bd547057
```

**All work below is against the snapshot, never the live file.** The live file was opened once, to
copy it, and never again — my session and the orchestrator's are concurrent and it is rewritten
under load.

### The three stale figures — every one of them, confirmed

| source | claimed | actual | delta |
|---|---|---|---|
| plan §0 ("Verified 2026-07-26") | 498 lines / 36,701 bytes | 122 lines / 8,196 bytes | −376 lines |
| plan §3 Q2 (the note's census base) | 405 lines | 122 lines | −283 lines |
| journal re-entry condition | 568 → cleared to 83 lines | 122 lines | +39 since the clear |

Not one figure in this plan's §3 survived contact with the artifact. The re-entry condition was
right that they were stale and *itself* went stale in the same day — the file has been written
twice more since the clear. **No quoted figure was carried forward**; every number below is
re-measured. This is finding-0191's shape a third time in one wave, and its lesson is now
mechanical rather than cautionary: a plan that quotes a size for a gitignored file is quoting a
reading, not a property.

### The re-grounded §3 census (Item 6's deliverable — sums to 122)

| class | lines | share | line numbers |
|---|---|---|---|
| structural (blank + headings) | 39 | 32.0% | 29 blank, 10 headings |
| **DERIVED** (dropped) | 5 | 4.1% | 12, 20, 21, 68, 69 |
| **MEASURED** | 1 | 0.8% | 34 |
| **NARRATIVE** | 50 | 41.0% | 8–10, 26–31, 39–44, 59–62, 70, 74–87, 91–103, 115–117, 119–122 |
| **RULES** | 27 | 22.1% | 5–6, 14–16, 23–24, 33, 35, 48–58, 63–64, 107–109, 113–114 |
| **total** | **122** | **100%** | verified by script: sum == wc -l |

Mixed lines are assigned their **dominant** class and their minority content is recorded
separately below, so nothing is lost to a rounding decision.

### What the census means — the hand-restructure already did the DERIVED eviction

Set beside the note's §2.2 census of the 405-line reading, the shape has changed radically, and
the change is evidence *for* the design rather than drift against it:

| class | note §2.2 (405 lines) | this reading (122 lines) |
|---|---|---|
| tree-derivable | ~33% | **4.1%** |
| execution-derived | ~7% | 0.8% |
| judgement | ~44% | 41.0% |
| durable rules | ~11% | **22.1%** |
| headers/blank | ~4% | 32.0% |

The DERIVED share **collapsed by a factor of eight** because the orchestrator's hand-restructure
replaced the hash lists, status tables and finding/oq digests with a five-line `## STATE —
regenerate, do not trust this snapshot` block that names the *commands* instead of their output.
That is §2.5's DERIVED rule applied by hand, and it worked: the pane that used to hold ~135 lines
of rotting facts now holds one instruction. The RULES and structural shares rose because the
absolute counts barely moved while the denominator fell — the rules are the residue that a manual
compaction cannot evict, because they have nowhere to go until *this* plan gives them one.

**The orchestrator's judgement that "the work is smaller, not different" is confirmed and can be
sharpened:** the DERIVED half of the migration was already done by hand; what remained was the
RULES eviction (which needs write access to four skills, so no manual pass could have done it) and
the NARRATIVE transcription. That is why the estimate is high, and it is recorded at seal rather
than tuned.

### Every DERIVED fact dropped, with the source that now supplies it

⚑ Item 6's falsifier is *"a fact classified DERIVED that the generator does not in fact render."*
It **fires literally, on the sha subclass**, and the reconciliation is `finding-0239`: the design
note §2.9 excludes shas from the rendering **on purpose** and names `git log` as their replacement
view. The DERIVED class therefore has two replacement sources, not one. Verified fact by fact:

| # | dropped fact | line | replacement source | verified |
|---|---|---|---|---|
| 1 | HEAD sha in the title | 1 | `git log --oneline -1` | §2.9 pin — never rendered, by design |
| 2 | sub-orchestrator "alive as of" sha | 10 | `git log` | same |
| 3 | bp-124 is complete | 12 | handoff → `Status tally: complete 108 …` | YES — rendered |
| 4 | bp-124 merge + seal shas | 12 | `git log` | §2.9 pin |
| 5 | finding-0238 exists | 12 | handoff → `Open findings` most-recent list | YES — rendered |
| 6 | bp-125/126/127 statuses | 20 | handoff → `Units of work` table | YES — rendered |
| 7 | the two blessing shas | 20 | `git log` | §2.9 pin |
| 8 | deskchecks owed | 69 | handoff → `Deskchecks owed` (5 rows) | YES — rendered |
| 9 | open owner-question count ("~25") | 69 | handoff → `answer (open owner questions): 31` | YES — **and the brief's figure had rotted by six** |
| 10 | ops wave bp-111…bp-119 available | 70 | handoff → `Units of work` table | YES — rendered |
| 11 | oq-0035 ruled but still open | 92–93 | handoff → `Awaiting the owner` count | YES — as a count, not per-question |
| 12 | the sha attached to that ruling | 93 | `git log` | §2.9 pin |
| 13 | the regenerate-command list | 68 | handoff's own GENERATED banner | YES — the instruction is the artifact |

**Nothing was dropped to memory, to prose, or to nothing.** Item 6's substantive invariant —
*nothing is dropped without a named replacement source* — holds for all thirteen. Fact 9 is the
migration paying for itself immediately: the hand-carried count was six low, and the rendering is
right by construction.

**Completed.** Item 6's acceptance is discharged: the census table sums to the live brief's line
count (122, verified by script, not by hand), and every DERIVED drop is named with its replacement
source and checked against a live run of the generator.

**In-flight.** Nothing mid-motion. Items 7–11 are untouched; no destination file has been written
yet. `handoff.md` is currently **converged** — `--check` exits 0 at `7ad779a`, measured before any
edit — so any staleness from here is mine to fix, and it is fixed LAST, after every other artifact
write, per the delegation's ordering constraint.

**Next action.** Item 7: append the migrated NARRATIVE to `docs/roles/orchestrator/journal.md` as
a new entry ABOVE bp-124's `## 2026-07-26 — the seat is opened`, obeying the purity rule (the
whole file is the authoritative segment — no `## CAPSULE — <date>` marker exists yet, so the F1b
scope is the entire file, and it currently lints clean at zero hex tokens).

**Open questions.** Two, both filed and both `spec-fidelity`, both resolved by me and not routed:
- `finding-0239` — Item 6's acceptance names one replacement source; the design names two, the
  second being `git log`. Resolved: census records the source per fact.
- `finding-0240` — Item 6 files the census in the seat journal, whose purity lint (Item 7) forbids
  exactly the sha list that makes it an audit trail. Jointly unsatisfiable. Resolved: the audit
  trail lands **here**, in the plan journal, which this journal's own "Owed at seal" section
  already demands.

**Context-manifest delta.**
- Read beyond the manifest: `scripts/handoff.py` (whole — needed to verify DERIVED drops actually
  render, which no other artifact could tell me), `.claude/hooks/_lib.py:920-943` (clause (f)'s
  tail grep — to place entries so the seal lands in the tail) and `:955-984` (the unswept counter's
  state list, for Item 11's falsifier), `docs/roles/orchestrator/handoff.md` (bp-124's render).
- Proved irrelevant: nothing. The manifest was accurate; only its *figures* were stale.
- ⚑ Not in the manifest and load-bearing: `docs/roles/orchestrator/journal.md` and `readings.md`
  already carry bp-124's content, so Items 7 and 8 are **appends, not creations**. The plan's verbs
  ("write the first entry", "seed the log") predate bp-124's merge.

**Markers.** None.
