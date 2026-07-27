---
type: journal
plan: bp-127
started: null
updated: 2026-07-26
---

# Journal — bp-127 (the fresh-agent test made executable: F1b, F1c, and the F2 drill)

Minted 2026-07-26 by `/graduate`, decomposing ratified `dn-role-state-and-scoped-handoff`
(blessed `c0abfd1`). Fourth and terminal of four (bp-124…bp-127). **Not started.**

## Pre-build notes for whoever picks this up

- ⚑ **READ bp-124's JOURNAL FIRST.** It records whether `next_action` proved derivable from the
  tree. **That is V1** (note §2.12). If it did not, the mechanical compare cannot cover field
  (2) and F2 degrades to judge-only — and **the plan must say so**, in this journal, in the
  harness's own output, and in a finding. Do not re-litigate it; do not loosen the compare until
  it passes. A test tuned until green cannot fail, which is the one thing a falsifier must do.
- ⚑ **THE DRILL'S OWN FALSIFIER IS THE FIRST THING TO BUILD, NOT THE LAST.** Put a fact **only**
  in a repo file outside the bundle and confirm the spawned agent reports `BLOCKED:` on it rather
  than answering. If it answers, the agent is reading the repo, the drill is testing nothing, and
  every future PASS manufactures false confidence — strictly worse than having no drill.
- ⚑ **The spawn mechanism is NOT grounded in the tree.** `scripts/orchestrator-launch.sh:47,89,91`
  shows `claude --model … --effort … --permission-mode …` — **interactive**. Nothing in the tree
  demonstrates a non-interactive one-shot, a no-history guarantee, or tool restriction, and
  §2.11 requires all three. Establish them empirically as Item 17's first act, record the finding
  as a MEASURED reading, and if a history-less bundle-restricted spawn is unachievable, **file a
  finding and ship Items 15–16 only.** Partial and honest beats complete and hollow.
- **F1a is NOT in this plan.** It is `scripts/handoff.py --check`, built in bp-124 and consumed by
  clause (e′) in bp-126. **Call it; never re-implement it.** Three copies of one check is the DRY
  defect the owner treats as a bug, and the whole point of F1a is that the gate and the drill are
  provably the same check.
- **The capsule marker may be undefined** (§3 Q1). The authoritative segment is "the latest
  capsule plus all entries after it" (note §2.8), but no capsule has ever been written. Read
  **bp-125's journal** for the marker it established; if it established none, define one, state it
  here, and file a `codebase` finding so the artifact and the lint cannot drift apart.
- **F1b's word boundary is load-bearing.** `\b[0-9a-f]{7,40}\b` — without `\b` the pattern matches
  hex letter runs inside ordinary words, the lint fires on legitimate narrative, and people learn
  to ignore it. Ids (`bp-110`, `finding-0227`, `oq-0051`) are **never** violations; they are the
  join key.
- **Be honest about F1b's tier.** It is tier 4 for the lintable class **only** (note residual R2).
  Its output and docstring must say so. An agent can still smuggle a count in prose — only review
  or the drill catches that.
- **F1c must use a REAL fresh worktree**, the `tests/integration/test_worktree_enforcement.py`
  pattern — not a mocked filesystem. A mock cannot falsify a claim about what exists in a
  checkout, which is the entire point of the test.
- **A `BLOCKED:` line whose answer is genuinely absent is a PASS with a defect report**, never a
  failure. The drill's job is to *find* under-specified state.
- **No skill edits, no CI wiring, no gate change.** Two documentation duties surface here — the
  drill's cadence and a checkpoint pointer — and both are **filed for the orchestrator**, because
  this plan does not hold `.claude/skills/**`.

## Owed at seal (orchestrator, not the builder)

- A `## Follow-through` block is required by clause (f) (`.claude/hooks/_lib.py:929-937`).
- ⚑ **V1's verdict, stated plainly**: did the mechanical JSON compare survive contact, or did F2
  degrade to judge-only? This is the note's explicit "the plan must say so" obligation.
- The **measured per-run cost** of one F2 drill. The note claims a cadence of "every `/triage`";
  if the cost makes that implausible, the cadence claim is not credible and needs a finding.
- The **spawn mechanism** actually used, as a MEASURED reading — so the next author does not
  rediscover it.
- Whether the seat artifacts were genuinely **present in a fresh worktree** (Item 16). If not,
  the note's §2.7 versioning ruling was never actually built and the finding routes to
  bp-124/bp-125.
- The drill's **cadence obligation** and the **checkpoint pointer** (§4) — filed here for the
  orchestrator to route into the skills, since this plan does not hold that surface.
- With this plan the note's §4 enablement is complete **except the owner's two hand-acts**:
  amendment A10 (finding-0233) and the first live session that resumes from `handoff.md` + the
  journal alone and says so (note §4(c)).

---

## 2026-07-27 — session start: grounding re-derived from primary sources

**Status line.** Worktree at base `origin/main`, dev extras synced. Every measurement this
session's prompt handed me has been **re-derived from the artifact itself** before use
(`the-unchecked-claim`: a claim resting on a prompt or a finding is unverified until re-derived).
Two of the three re-derivations changed what I will build.

**Completed — the re-derivation, with labels.**

- `[GROUNDED docs/roles/orchestrator/journal.md:32-35]` **The capsule marker is settled**, and the
  plan's §3 Q1 is stale. The seat journal's own preamble pins it: *"The capsule marker is the
  literal heading `## CAPSULE — <date>`. The **authoritative segment** is the latest such heading
  plus every entry above it; everything below it is history. … Tooling that lints or bounds this
  file keys on that exact heading — nothing else in this file may use it."* No marker needs
  defining and no `codebase` finding is owed for drift; bp-125 defined it in the artifact.
- `[GROUNDED docs/roles/orchestrator/journal.md:12-13]` The file is **newest-first**
  (*"entries are added at the top"*). Combined with the line above: **the authoritative segment is
  the capsule heading plus everything physically ABOVE it.** The plan's §6 pin (*"the latest
  capsule plus all entries **after** it"*) is TEMPORAL, and reading it physically inverts the lint
  so it checks history and ignores live narrative — while producing green. Both directions get a
  fixture.
- `[DERIVED, re-measured]` on the live seat journal, 465 lines: `^## CAPSULE` anchored = **0**;
  `## CAPSULE` unanchored = **4** (lines 32, 173, 427, 441); word-bounded `\b[0-9a-f]{7,40}\b` =
  **6** on 2 lines (409, 424); `status:`-transition phrases = **0**. Independently reproduces
  finding-0251's table. Anchoring is load-bearing, not stylistic.
- `[DERIVED, re-measured]` **finding-0243 recurred and is wider than filed.** A `git blame
  --line-porcelain` sweep of `readings.md` comparing each row's timestamp against the
  committer-time of the commit that introduced it: **10 future-dated rows of 38**, in TWO commits
  — six in bp-124's seed (up to 55 min ahead) and **four more, previously unrecorded, in bp-126's
  seal** (up to 16 min ahead). The defect recurred one wave after it was found. The lint is real
  and it reddens on the live artifact.
- `[GROUNDED .claude/state/ listing; .claude/hooks/_lib.py:1034-1042]` ⚑ **In a fresh worktree
  `.claude/state/session-baseline` does not exist**, and the gate reads its absence as
  `baseline = ""` → clause (e′) skipped entirely (fail-open). This EXTENDS manifest entry 13's
  containment recipe: `cp -p` aside/back is undefined when the file is absent, and a spawn that
  CREATES it cannot be undone by copying anything back. The correct snapshot is
  `(exists?, content, mtime)` and the correct restoration of a previously-absent file is
  **unlink**, not rewrite.

**In-flight.** Item 15 (F1b + the two instruments), starting now.

**Next action.** Write `authoritative_segment` / `lint_narrative` / the readings lint into
`scripts/handoff.py` as a `--lint` mode, then `tests/unit/test_handoff_purity.py`.

**Open questions.** None blocking. Two decisions taken and recorded below under Markers.

**Context-manifest delta.** §3 Q1 is **stale** — the marker is settled in the artifact (above), so
its "define one and file a finding" branch is dead. §2 entry 12's finding-0243 is **understated**
— 10 rows, not 6, across two commits.

**Markers.**
- **F1b's home = `scripts/handoff.py --lint`** (the §11 coin-flip, resolved): one entry point for
  the handoff machinery, beside `--check` (F1a), and the CI leg the note anticipates has something
  to call.
- **The segment line count (manifest entry 14) goes in `--json` + the LIVE render only, NOT the
  committed rendering.** Reason: the committed `handoff.md` is the subject of clause (e′) check 1,
  and embedding a value that changes on every seat-journal append would make every narrative entry
  arm the staleness check. `--json` is tree-pure and byte-stable but uncommitted, so the threshold
  becomes readable at zero cost to the idempotence pin.

---

## 2026-07-27 — Item 15 CLOSED: F1b, the readings lint, and the threshold instrument

**Status line.** Item 15 delivered as `scripts/handoff.py --lint` plus
`tests/unit/test_handoff_purity.py` (59 tests). Both lints redden on the live artifacts, by
measurement, and neither pattern was narrowed to make an artifact pass.

**Completed.**

- **F1b** — `authoritative_segment` / `lint_narrative` / `Violation` / `LintResult`. The segment is
  the capsule heading plus everything physically ABOVE it (the direction pin, above). No capsule ⇒
  the whole file, which is the normal day-one state (finding-0242a). Marker anchored `^## CAPSULE`.
- **The future-dated readings lint** (manifest entry 12) — `blame_readings` (the only impure part;
  `git blame --line-porcelain`) + `future_dated` (pure). ⚑ **Built, not deferred.**
- **The threshold instrument** (manifest entry 14) — `journal_segment_lines`, surfaced in the LIVE
  render (with an ⚑ OVER flag past `SEGMENT_THRESHOLD = 300`) and as `journal_segment_lines` in
  `--json`. finding-0245's threshold is now read by an instrument instead of by hand.
- **Three exit codes, and the third is the point.** 0 clean / 1 violation / **3 indeterminate**. A
  check that could not RUN must never be indistinguishable from one that ran and found nothing —
  an unreadable journal, an empty segment, an absent readings log, and a non-repo all land on 3.

**The degenerate inputs, named and asserted to redden** (the false-success rule):

| # | degenerate input | a wrong lint says | asserted behaviour |
|---|---|---|---|
| D1 | the same hex token above vs below one capsule | green either way | FAIL above, PASS below |
| D2 | `## CAPSULE` in quoted/indented prose | scopes to a fragment, green | segment unbounded, FAIL |
| D3 | an empty / capsule-only segment | "0 violations" = clean | INDETERMINATE (rc 3) |
| D4 | a hex run inside an ordinary word | fires, cries wolf | PASS |
| D5 | no readings log / no git | "0 future-dated rows" | INDETERMINATE (rc 3) |

**Mutation campaign — 21 mutants, 20 caught, 1 survivor.** Pass 1 exposed **four** survivors and
two of them were real. (a) The anchoring guard was **self-masking**: `CAPSULE_RE.match` anchors on
its own, so deleting the `^` changed nothing observable — fixed by pinning the CONSTANT's own
behaviour, and the COMBINED mutant (unanchored *and* `.search`) is now caught. (b) The status
patterns had no cry-wolf negative, so widening either side survived — fixed with four negative
cases. A third survivor was **not applicable**: the row-detection predicate existed in TWO copies
(`read_readings` and `_row_stamp`), which is the DRY defect the owner treats as a bug; factored to
one `row_cells` and the mutant is now caught. The sole survivor, `.match`→`.search` with `^` kept,
is **equivalent** — verified exhaustively over a case set, `re.MULTILINE` unset.

⚑ **A harness hazard worth carrying forward:** a mutant with the SAME BYTE LENGTH as the original
(`start=1` → `start=0`) collides with CPython's pyc cache key (mtime-seconds + size), so a restored
file can be served as stale mutant bytecode. It cost one confusing red. Run mutation campaigns with
`PYTHONDONTWRITEBYTECODE=1`; pass 3 re-ran cache-safe and reproduced 20/1 exactly.

**⚑ The live verdict, stated as a measurement rather than a wish.**
`uv run scripts/handoff.py --role orchestrator --lint` → **rc 1**. Journal: **6 hex violations**
(2 lines), 0 status phrases, 465-line segment, 0 capsules. Readings: **9 of 40 committed rows
future-dated**, across two commits. The plan's Item 15 acceptance says the live journal's segment
must **PASS**; that acceptance is **falsified by measurement** and I did not resolve it by
narrowing anything. The two available green-making moves were both refused:
1. **Narrow the pattern** — the tuned-until-green test the plan's own falsifier forbids.
2. **Write the first `## CAPSULE` at the top**, which would demote all seven entries to history and
   turn the lint green instantly. ⚑ This is the SAME defect one level up — narrowing the *segment*
   instead of the *pattern* — and it is worse, because it would silently demote the handoff entry
   the sub-orchestrator is relying on. The first capsule is owed at a `/triage` (finding-0251), by
   the seat's occupant, as a judgement — not as a side effect of a builder making its own lint pass.
I also did **not** append a corrective entry to the seat journal. I hold `docs/roles/**` and could
have; the reason not to is that the repair finding-0251 describes is a **capsule-shaped judgement
about what is still live**, which is exactly the judgement a builder in a worktree is not the one to
make. The measurement is the durable part and it is now recorded in `readings.md`.

**The suite deliberately does NOT assert the live file is clean.** It asserts what is true and
stable: the lint answers for the real artifact, its answer is non-vacuous, its segment covers the
whole file while no capsule exists, and the live file's **status-phrase** class IS clean. A
mis-anchored or direction-inverted implementation trips the non-vacuity assertion.

**In-flight.** Item 16 (F1c) next.

**Next action.** Write `tests/integration/test_handoff_availability.py` — a real fresh worktree,
`--role orchestrator` exits 0 with `queue: unavailable`, seat artifacts present, no queue file
created.

**Open questions.** None blocking. finding-0251 stays **open** — its ordering half and the capsule
repair are the orchestrator's, and Item 15 did not close it.

**Context-manifest delta.** Manifest entries 12 and 14 are BUILT here, not deferred — no finding is
owed for either. Entry 12's finding-0243 is understated: 10 raw future-dated rows (9 past a
one-minute stamp-precision allowance), across two commits, not 6 in one.

**Markers.**
- `STAMP_PRECISION_SECONDS = 60` is a **representation allowance**, not a tuned threshold: rows
  carry minute precision, so an honestly-read stamp can round up to a minute ahead. It is argued
  from the format and is outcome-independent — the live leads run to 55 minutes and stay red.
- The English "X to Y" status form is deliberately **not** matched (`to` collides with ordinary
  judgement). Recorded in `LINT_TIER` and in a test, so it reads as a decision, not an oversight.
