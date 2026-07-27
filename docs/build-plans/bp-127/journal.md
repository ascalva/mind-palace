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

---

## 2026-07-27 — Item 16 CLOSED: F1c, and the vacuous test that mutation caught

**Status line.** `tests/integration/test_handoff_availability.py`, 9 tests, green. The first
version of it was **vacuous** and only mutation revealed that.

**Completed.**

- A REAL `git worktree add --detach` checkout, cleaned up in a `finally`. Asserted: the three seat
  artifacts are present and non-empty (and `git ls-files` tracks them — the claim starts with
  "tracked"); the generator exits 0 rendering `queue: unavailable`; it creates no queue file under
  `--role` / `--json` / `--check`; the worktree has no `data/` and nothing in `.claude/state/` but
  its `.gitignore`.
- Asserted on the LIVE stdout path, never `--check` — finding-0236: `--check` exits 0 in a fresh
  worktree without reaching the queue at all, so F1c against it is green and proves nothing.

**⚑ THE FINDING OF THIS ITEM. The suite was testing HEAD, not the diff.** `git worktree add HEAD`
checks out the last **commit**, so running the checked-out `handoff.py` reports on HEAD and is
completely blind to the working tree. A five-mutant campaign — hard-code the queue pane, make the
degradation path raise, honour `CLAUDE_PROJECT_DIR`, resolve the seat from the CWD — came back
**0 caught / 5 survived, at "8 passed"**. Every mutation destroyed the property under test and the
suite reported success, because the mutated file was never the file being executed. This is
`finding-0249`'s shape exactly: green became evidence for green. **Reading the test would never
have found it** — it reads correctly.

Fixed three ways, and the campaign re-run gives **4 caught / 1 survived**:
1. The working tree's `handoff.py` / `board.py` / `_lib.py` are **overlaid** onto the checkout. The
   checkout supplies the tracked artifacts and the absence of runtime state; the working tree
   supplies the code whose behaviour is asserted. A guard test asserts the overlay actually
   happened — otherwise the overlay is itself a false-success surface.
2. `CLAUDE_PROJECT_DIR` is set to the MAIN checkout in the subprocess env — the literal
   `finding-0031` bleed, supplied deliberately instead of avoided.
3. The CWD is the worktree's PARENT, so anything resolved relative to `.` rather than to `ROOT`
   breaks visibly.
The surviving mutant (a read-write `sqlite3.connect`) is **not** equivalent and **not** a gap: it
is unreachable from this suite because `read_queue` returns before connecting when the file is
absent, and bp-124's `test_the_queue_is_opened_with_a_readonly_uri` catches it. Verified by running
that mutant against the unit suite rather than assuming it.

**Two deviations from the plan's literal wording, both strengthening, both flagged:**
- The worktree is built from **HEAD, not `origin/main`.** A test against `origin/main` passes no
  matter what the working tree contains — delete the seat on this branch and it still goes green.
  It also may not be fetched in a shallow clone. HEAD is what this checkout is about to publish.
- **`--check` is asserted to reach a DEFINITE verdict (rc 0 or 1), not rc 0.** Whether `handoff.md`
  is currently regenerated is the last committer's hygiene, and clause (e′) check 1 is where the
  note put that duty. Asserting rc 0 makes the suite red whenever a regen is owed — cry-wolf, and
  effectively CI wiring, which §9 excludes.

**⚑ TWO HAZARDS I HIT, both worth carrying forward.**
- **A mutation campaign can have side effects outside the file it mutates.** The N5 mutant
  (`seat_dir` resolved from the CWD) made `--write` in bp-124's unit suite write **fixture content
  into the real `docs/roles/orchestrator/handoff.md`**. The harness restored the mutated source in
  its `finally` and did not notice the collateral write. Caught by `git status`, restored from HEAD.
  Run campaigns on a clean tree and diff afterwards.
- **I composed a timestamp — while building the lint that detects composed timestamps.** I wrote
  `15:33Z` into two `readings.md` rows when `date -u` said `15:19Z`. Corrected before commit. The
  point is not the slip; it is that composing a plausible-looking value is the *default* behaviour
  even with the defect in full view, which is the strongest possible argument that finding-0243
  needs an executable check rather than a rule. It now has one.

**In-flight.** Item 17 (F2), starting with §3 Q3 empirically.

**Next action.** Probe the agent CLI's `--help` for a non-interactive, history-less, tool-restricted
spawn — with `session-baseline` containment around it (snapshot exists/content/mtime; restore, or
UNLINK if it was absent).

**Open questions.** None blocking.

**Context-manifest delta.** None.

**Markers.**
- The overlay pattern (checkout for artifacts, working tree for code) is reusable by any future
  test that runs repo tooling inside a generated checkout. Anything of that shape that does NOT
  overlay is reporting on HEAD.

---

## 2026-07-27 — Item 17 CLOSED, and the plan is COMPLETE (all three items shipped)

**Status line.** F2 ships **whole**, not degraded. §3 Q3 resolved by measurement, V1 resolved in
the strong direction, the isolation falsifier demonstrated red *and* green, and 14 of 14 mutants
caught. One measured result changed the design mid-item and is filed as `finding-0254`.

**⚑ §3 Q3 — the spawn mechanism, MEASURED, not assumed.** The plan called this "this plan's single
largest unknown" and its stop-and-raise was to ship Items 15–16 only if a history-less,
bundle-restricted spawn could not be achieved. It can. `claude --help`, run once under containment,
shows all three requirements exist as flags:

| §2.11 requirement | flag | the CLI's own words |
|---|---|---|
| non-interactive one-shot | `-p` / `--print` | "Print response and exit" |
| tools disabled | `--tools ""` | "Use \"\" to disable all tools" |
| no conversation history | `--safe-mode` + `--no-session-persistence` | "CLAUDE.md, skills, plugins, hooks, MCP … disabled"; "sessions will not be saved to disk and cannot be resumed" |

`--strict-mcp-config` is added so no ambient MCP server can smuggle a capability back in. No
approximation was needed and no stop-and-raise fired.

⚑ `--safe-mode` disabling **hooks** also means `SessionStart` never fires, which is a *structural*
answer to the finding-0246/0247 laundering hazard. I kept the snapshot/restore invariant anyway:
an invariant that depends on one flag's current meaning is not an invariant.

**⚑ The falsifier: built first, and demonstrated in BOTH directions.** The plan required proving
the agent cannot read outside the bundle rather than assuming it. Two probes, matched, same prompt:

- **tools ON** → returned the **real** nonce, correctly attributed. **tools OFF** → did not.
  ⇒ `--tools ""` is a *structural* barrier and `nonce in reply` provably discriminates.
- ⚑ **An earlier version of this probe proved nothing and was discarded.** Phrased *"using ONLY the
  bundle"*, it was answered `BLOCKED:` **even with tools enabled** — the agent obeyed the
  instruction instead of using its capability. That version tested the agent's *obedience*, not its
  *capability*, and would have passed identically against a fully-tooled agent. Naming it here
  because a reviewer should know the first attempt was the vacuous one.

**⚑ The result that changed the design: `finding-0254`.** In the tools-OFF probe the agent did
**not** emit `BLOCKED:`. It printed a **fabricated** `Bash(command: "grep -rn …")` block with a `⎿`
result line and reported a value from `./token.env` — a file that does not exist. So a tool-less
agent under pressure may hallucinate rather than report a blocking unknown. The harness now carries
`_FABRICATED_TOOL_RE`: a reply containing tool-call syntax is **refused rather than scored**
(INDETERMINATE, not PASS and not FAIL), because an answer not derived from the bundle should not be
compared at all. The guard is **syntactic** and therefore catches the observed mode only — a bare
confident wrong answer is still indistinguishable from a right one except by the compare. Said
plainly in the finding rather than overclaimed.

**⚑ V1's verdict, stated plainly (the note's explicit "the plan must say so" obligation):**
**The mechanical JSON compare SURVIVED contact, on BOTH fields. F2 did NOT degrade to judge-only.**
The first live run matched `unit_in_flight` **and** `next_action` exactly. `next_action` is derived
from artifact state via `handoff.derive` / `_LADDER`, never stored (finding-0238 §V1), and the
agent returned the rendered form verbatim. The only allowance is `_canon` — backticks, quotes,
whitespace, case — a **representation** allowance, and mutation proves it did not become a
loosening: a compare relaxed to substring matching is now CAUGHT.

**Cost, and the cadence claim.** One full drill = **$0.1833** (one drill spawn + one judge spawn),
8.6 s wall. `--verify-isolation` = **$0.0115**. The note claims a cadence of "every `/triage`"; at
eighteen cents a run that is entirely credible, so **no finding is owed** on the cadence — the
"expensive drills get skipped" risk the plan flagged did not materialise.

**Mutation: 14 mutants, 14 caught, 0 survivors.** Pass 1 had one survivor and it was the important
one: **a compare loosened to substring matching survived**, because every negative case I had
written differed from the right answer rather than *containing* it. `/resume bp-123 and then
/triage` contains the right answer and is the wrong answer — §2.11 asks for "the **single**
concrete next action". Three superstring cases now pin it.

**Where the harness knowingly falls short — `finding-0253`.** CONVENTIONS §Testing and §2.11 both
require the judge to be an **A/B against the last passing baseline, never scored cold**. This
harness has **no stored baseline**: one would be a fourth standing seat artifact and note §2.9
enumerates exactly three. Instead the judge must **quote the bundle verbatim** and the harness
verifies the quote is a literal substring — so a hallucinated PRESENT is caught by code. That is
stronger than a cold score against *fabrication* and weaker than an A/B against *drift*. Filed with
three options rather than silently adopted.

**`finding-0255`** records a third thing worth the owner's eye: for a `role` scope the bundle
contains `handoff.md`, which literally renders "The answer" — so the mechanical half is largely a
staleness check that duplicates F1a, and the drill's unique value at that scope is the defect
report. It is a genuine derivation test for `plan:` and `track:` scopes.

**Test placement.** The drill's 30 unit tests live in `tests/unit/test_handoff.py` because that is
the file §7 Item 17 lists; `tests/unit/test_handoff_drill.py` is not in `write_scope` and creating
it would have required routing a finding rather than routing around `scope-guard`.

**In-flight.** Nothing. All three items are closed.

**Next action.** The sub-orchestrator's audit, then the two status flips (both owner/orchestrator
acts — this builder performed neither).

**Open questions.** None blocking. Three `design` findings are routed to the orchestrator
(`finding-0253`, `finding-0254`, `finding-0255`); none blocks the plan and each carries a concrete
re-entry condition.

**Context-manifest delta.** §3 Q3 and §11's "spawn mechanism" row are both **settled by
measurement** and recorded as MEASURED readings. §11's V1 row resolves to "the compare holds".
§3 Q1's "the marker may be undefined" branch was already dead (the artifact defines it).

**Markers.**
- The drill spends real tokens. `--replay FILE` runs the whole parse/compare pipeline against a
  recorded reply with **no spawn**, which is how its logic should be changed and tested.
- `handoff_drill.py` imports `handoff` for `authoritative_segment` and `answer_json` rather than
  re-deriving them. That inherits finding-0238's `sys.path`/`eval`-shadowing hazard; it is accepted
  because this is a leaf CLI nothing needing `eval` imports, and the full suite is green.

## Follow-through

- **Built?** Yes, all three items. **F1b** + the future-dated readings lint + the segment gauge as
  `scripts/handoff.py --lint` (59 tests). **F1c** as `tests/integration/test_handoff_availability.py`
  (9 tests, mutation-hardened after the first version proved vacuous). **F2** as
  `scripts/handoff_drill.py` with 30 unit tests that spend no tokens. Gate green: ruff clean,
  import firewall clean, mypy floor 0 in 262 files, argless mypy at exactly the pinned 69/20,
  type_gate clean, pytest 3 failed / 2419 passed / 15 skipped — the two known live failures plus
  the finding-0219 scheduler flake, which passed on an isolated re-run.
- **Wired / delivered (or why dormant)?** Wired as far as this plan is licensed to wire it. Both
  lints and the drill are runnable commands with real verdicts, and the drill has been **run live**
  and its result recorded as a MEASURED reading. Deliberately **not** wired into CI or into any
  hook — §9 excludes both, and the cadence obligation ("every `/triage`") is documentation whose
  home is a skill this plan does not hold. **That cadence line is owed to the orchestrator**, along
  with the checkpoint-skill pointer (§4).
- **Does a consumer use it?** F1a's consumer is clause (e′), unchanged. F1b/F1c/F2 have **no
  automatic consumer yet, by design** — the drill is invoked by a human or by `/triage`, never by a
  hook (§9). The first real consumer is the `/triage` cadence, which is bp-125's surface.
- **Track state (what remains on this track)?** bp-127 is the family's terminal node. With it, the
  note's §4 enablement is complete **except the owner's two hand-acts**: amendment A10
  (finding-0233), and the first live session that resumes from `handoff.md` + the journal alone and
  says so (note §4(c)). Ready to deskcheck.
- **Opened a new track/finding?** Three findings, all `design`, all routed to the orchestrator:
  **finding-0253** (the judge is quote-verified, not baseline-A/B'd),
  **finding-0254** (a tool-less agent may fabricate rather than report a blocking unknown),
  **finding-0255** (F2's mechanical half is near-tautological for a role scope).
  **finding-0251 stays OPEN** — F1b measures the defect it describes but does not repair it, and
  the repair is a capsule-shaped judgement for the seat's occupant, not a builder in a worktree.
  No new track.

---

## 2026-07-27 — seal addendum: the plan-scope drill, and the final gate

**Status line.** Two things landed after the Item 17 commit: a live `plan:` scope drill that
settles `finding-0255` on its own terms, and the seal gate run.

**⚑ The plan-scope drill FAILED, and the failure is the most informative result of the session.**
`--scope plan:bp-127`, $0.2679, 51 s:

| | the agent (given `plan.md` + this journal) | the generator (`--json`) |
|---|---|---|
| `unit_in_flight` | `none` | `bp-127` |
| `next_action` | "the sub-orchestrator's audit, then the two status flips" | `/resume bp-127` |

**The agent was not wrong.** It read this journal's own words — *"In-flight. Nothing. All three
items are closed."* The generator read the plan's front matter, still `status: in-progress`,
because the flip is the orchestrator's act and a builder must never perform it. Two conclusions:

1. **The plan-scope compare is a GENUINE derivation test** — not tautological like the role scope
   (finding-0255), and it produced a real disagreement on its first run. That is the drill earning
   its keep.
2. ⚑ **The mechanical compare disagrees with a *correct* reader whenever narrative and status
   legitimately diverge**, and that window is not rare: it is exactly the interval between a
   builder sealing and the orchestrator flipping — which is *precisely when* §2.11's mandatory
   cadence fires ("mandatorily in any build plan that touches the handoff machinery"). Recorded as
   an addendum to `finding-0255` with two candidate resolutions, neither built: both touch
   `handoff.derive`'s ladder, which is bp-124's contract and a design call.

⚑ I did **not** "fix" this by loosening the compare or by editing the journal to agree with the
front matter. Either would be the tuned-until-green move. The FAIL is a true reading of a real
divergence and it is recorded as one.

**The gate, on the committed tree, each leg run separately and read:**

| leg | observed |
|---|---|
| `uv run ruff check .` | All checks passed (rc 0) |
| `uv run python scripts/check_imports.py` | OK (rc 0) — firewall + worker boundary clean |
| `uv run mypy core agents eval ops scheduler scripts` | Success: no issues in **262** source files (floor 0) |
| `uv run mypy` (argless) | **69 errors in 20 files** of 562 checked — exactly the pinned tests/ baseline, rc 1 by design |
| `uv run python -m ops.type_gate` | OK (rc 0); the parked finding-0223 shim report unchanged |
| `uv run pytest -q` | **2 failed / 2420 passed / 15 skipped** in 273.95s |

The two failures are the two known live ones (finding-0103 ratchet; finding-0226 dream-v2 live).
⚑ **An earlier full run showed THREE**, the third being `test_scheduler_live.py::test_supervisor_dispatches_a_real_job`; it passed on an isolated re-run and passed again in the seal run, confirming
the finding-0219 flake rather than a regression. Reported as observed both times, not as remembered.
Baseline 2313 → 2420 is exactly this plan's new tests.

**⚑ Containment, proved by a real creation event.** The `/usage` probe (plain `claude -p`, hooks
enabled) **did create** `.claude/state/session-baseline` in this worktree, where it had been
absent. The wrapper unlinked it and the Stop gate's verdict was `ALLOW` before and `ALLOW` after.
That is live confirmation of both halves: finding-0246/0247's hazard is real, and the absent-file
case genuinely needs an **unlink** — which the `cp -p` recipe cannot express.

**Next action.** Nothing. Awaiting the sub-orchestrator's audit and the two status flips.
