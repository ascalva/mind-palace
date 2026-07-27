---
type: finding
id: finding-0251
status: open
created: 2026-07-27
updated: 2026-07-27
links:
  - docs/roles/orchestrator/journal.md              # the artifact — its newest entry sits below the standing trailer
  - docs/design-notes/role-state-and-scoped-handoff.md  # §2.5 purity rule, §2.8 authority rule
  - docs/findings/finding-0248.md                   # the same defect shape in clause (f), one artifact over
  - docs/findings/finding-0249.md                   # the vacuous-pass class
  - docs/build-plans/bp-127/plan.md                 # Item 15 (F1b) lints exactly this segment
ftype: codebase
origin_plan: orchestrator
route: orchestrator
resolution: null
---

# The seat journal's NEWEST entry is physically last, below the standing trailer — the ordering contract is documented but unenforced, and the misplaced entry carries the file's only purity violations

## What

`docs/roles/orchestrator/journal.md` states its own ordering contract in its preamble:
*"Append-only: entries are added at the top, never deleted and never rewritten in place."*
Its six dated entries obey that, newest first.

**The seventh — the newest, and the one written specifically to hand the wave off — does not.**
It was appended at the **bottom of the file**, below the `## Markers` standing trailer, in the
position the file's own contract designates as *oldest*.

Two consequences compound, and a third is measured below.

**(1) The documented read path meets it last.** A successor told "entries are added at the top"
reads top-down and encounters six entries of completed-wave narrative before reaching the one
entry that says what to do next. This finding exists because a fresh sub-orchestrator found that
entry only by grepping the file's heading structure first — not by following the stated path.

**(2) The first capsule will silently demote it to history.** §2.8's authority rule is
**temporal**: the authoritative segment is the latest capsule plus every entry *newer* than it,
which in a newest-first file is the capsule plus everything **physically above** it. The seat
journal's own preamble renders that correctly (*"the latest such heading plus every entry above
it; everything below it is history"*). The first `## CAPSULE` is **owed at the next `/triage`**
and will be written at the top. At that moment this entry — the handoff for an un-started plan,
the four pinned manifest corrections, the owner queue, the 568-line measurement — falls **below**
the capsule and becomes non-binding history, without anyone deciding that it should.

**(3) It carries the file's only §2.5 purity violations.** MEASURED on the live file
(465 lines, `\b[0-9a-f]{7,40}\b`, word-bounded):

| what | count | where |
|---|---|---|
| `^## CAPSULE` headings (anchored) | **0** | — |
| lines containing `## CAPSULE` unanchored | **4** | 32, 173, 427, 441 |
| word-bounded hex tokens | **6** | **2 lines, both inside the misplaced entry** |
| `status:`-transition phrases | **0** | — |

Every hex token in the file is in that one entry: one commit sha on one line, five on another.
The other six entries are clean. The rule was obeyed everywhere except in the entry that also
broke the ordering rule — the same act of writing in the plan-journal idiom (oldest-first,
shas allowed) inside a seat journal that uses neither.

## Why it matters

This is `finding-0248`'s defect one artifact over, and it is worth stating in that form:
**a check or a reader that keys on physical position mis-identifies the newest entry whenever a
file carries trailing standing sections.** finding-0248 found it in clause (f), which audits plan
journals. Here the *artifact itself* — the seat journal, the thing the whole handoff family exists
to make trustworthy — has the same shape, and nothing enforces its stated ordering.

It is also a live `finding-0249` instance waiting to happen. `bp-127` Item 15 (F1b) lints "the
live journal's authoritative segment → **PASS**". Today, with zero capsules, the whole file is
authoritative, so a correct F1b **FAILS on this file with exactly 6 hits**. Two wrong resolutions
are available and both are worse than the defect:

- **Narrow the pattern until the live journal passes.** That is the tuned-until-green test the
  plan's own falsifier forbids. The pattern is right; the artifact is non-compliant.
- **Read §2.8's "after" physically** — `segment = lines[capsule_index:]` — which inverts the lint
  so it checks history and ignores the live narrative. That resolution makes the live file pass
  *and* makes the lint permanently vacuous. It is the more dangerous of the two precisely because
  it produces green.

⚑ The measured row above is also the first hard evidence for `bp-127` manifest entry 11: an
**unanchored** `## CAPSULE` grep finds **4** matches on a file with **0** capsules. Anchoring is
not a style preference here; unanchored, the lint would scope itself to a 24-line tail (last
match, line 441) or a 434-line tail (first match, line 32) and report success either way.

## What is NOT claimed

- **Not that the entry's content is wrong.** It is the most useful single artifact in the seat and
  every one of its claims that this session checked held up. The defect is placement and idiom,
  not judgement.
- **Not that its author was careless.** Plan journals in this repo *are* oldest-first, and shas in
  a plan journal are ordinary. The seat journal inverts both conventions, and nothing at write time
  says so — which is the actual gap.
- **Not that the fix is "move the entry".** Moving it is a rewrite-in-place, which the append-only
  discipline (`finding-0164`/`0168`, keep-and-link) forbids. The repair shape is an appended
  corrective entry at the top that carries the judgement forward and names what it supersedes —
  i.e. the same shape as a capsule — not a silent relocation.

## Re-entry condition

`bp-127` holds `docs/roles/**` and builds the lint that would have caught this. It inherits this
finding as context for Item 15: **its acceptance for "the live journal" must be stated as the
measured verdict, not as `PASS`.** If the builder cannot both keep the pattern honest and turn the
live file green within its scope, the honest outcome is a red live-journal reading recorded in
`readings.md` plus this finding left open — never a narrowed pattern.

The ordering half (an entry landing below the trailer with nothing objecting) is an enforcement
gap of the same class the `/triage` capsule sweep will hit first. It routes to the orchestrator.

## Routing

`codebase` → the builder resolves and annotates. Filed by the sub-orchestrator that found it
while reading the seat cold; retained here rather than repaired in place, because the repair is
an append-only judgement call and the measurement is the durable part.
