---
type: finding
id: finding-0238
status: open
created: 2026-07-27
updated: 2026-07-27
links:
  - docs/build-plans/bp-124/plan.md
  - docs/build-plans/bp-124/journal.md
  - docs/build-plans/bp-126/plan.md
  - docs/build-plans/bp-127/plan.md
  - docs/design-notes/role-state-and-scoped-handoff.md
  - docs/findings/finding-0236.md
  - docs/findings/finding-0237.md
  - scripts/handoff.py
  - scripts/board.py
  - tests/unit/test_handoff.py
  - tests/unit/test_board.py
ftype: discovery
origin_plan: orchestrator
route: orchestrator
resolution: null
---

# The independent pre-merge audit of bp-124 — the idempotence keystone holds under adversarial
# test, and the family's real risk is that finding-0236's resolution is invisible to bp-126/127

## What

An independent auditor (not the builder) stress-tested bp-124's delivered diff on branch
`worktree-agent-a3c6ca5992db17dfc` (4 commits on base `ac83ca3`) before merge. This is the audit
record: what was verified **by execution**, what was verified **by inspection only**, and what
could **not be closed**. Verdict: **MERGE WITH CONDITIONS** — no defect in the delivered diff is
merge-blocking; every condition below is a post-merge or pre-next-build act.

### Verified BY EXECUTION (re-run independently, not accepted from the seal)

All generator runs were performed against a **pristine `git archive HEAD` export in a scratch
directory outside the repo**, so the builder's worktree was never written to. That export has no
`.git` directory at all and sits at a different absolute path — which is itself the proof that the
rendering derives nothing from git or from its own location.

1. **The idempotence pin (Item 2's falsifier — did not fire).**
   - Two `--write` passes over an unchanged tree → `cmp` byte-identical.
   - `--check` against the pristine HEAD export → rc 0, "up to date": **the committed
     `docs/roles/orchestrator/handoff.md` equals a fresh render at HEAD**, not merely in a fixture.
   - **No clock:** with `handoff.datetime` replaced by an object that raises on any attribute
     access, the tree-pure render completes unchanged; the same probe run against the **live**
     render *does* raise — so the probe is non-vacuous, not a tautology.
   - **No sqlite:** with `handoff.sqlite3.connect` replaced by a raiser, the tree-pure render
     completes unchanged.
   - **No HEAD / no git:** the export contains no `.git` and rendered byte-identically to the
     committed file. `grep -nEo '\b[0-9a-f]{7,40}\b'` over the rendering → rc 1, no matches.
   - **No environment leak:** identical bytes under changed `TZ` (Pacific/Kiritimati), `LANG`,
     `LC_ALL`, `HOME`, `USER`, and `cwd`; identical across `PYTHONHASHSEED` 0/1/12345/99999.
   - **Excluding itself, by a method other than the builder's:** the rendering is identical across
     four states of its own output file — absent, empty, 500 lines of unrelated garbage, and its
     own content. Every glob in `board.py` is `sorted()` and none reaches `docs/roles/**`.
   - Widest rendered table row: **190 characters** (194 bytes — `_cap` counts characters). No row
     exceeds `board.MAX_ROW`.

2. **⚑ The keystone question — clause (e′) is DEFUSED, not re-armed.** A populated
   `data/queue.sqlite` (2 queued, 1 running with a lease) was planted beside the pristine export
   and `--write` re-run: the committed artifact is **byte-identical to the no-queue render**, and
   `--check` still exits 0. `--json` is likewise identical with and without the queue. **Nothing
   daemon-derived reaches the committed artifact**, so a mutating supervisor cannot re-arm bp-126's
   check 1. This is the single property the whole family rests on and it holds.

3. **The queue never creates `data/queue.sqlite`.** The connection string is exactly
   `f"file:{path}?mode=ro"` with `uri=True` (`scripts/handoff.py:216`), matching the §6 pin. A bare
   `--role orchestrator` run in the real worktree (which has no `queue.sqlite`) printed
   `queue: unavailable in this checkout`, exited 0, and left no queue file. The test that proves
   absence-after-run **genuinely raises**: mutating `read_queue` to create the file on a miss is
   caught by `test_absent_queue_degrades_and_creates_nothing`, and mutating the URI to a plain
   `sqlite3.connect(str(path))` is caught by `test_the_queue_is_opened_with_a_readonly_uri`.

4. **Item 4's no-op falsifier, isolated more sharply than the seal isolated it.** The **base**
   `scripts/board.py` (from `ac83ca3`) and the **HEAD** `scripts/board.py` were both executed
   against the **same HEAD tree**: `board_text` and `queue_text` are byte-identical and
   `queue_count` is 5 for both. That isolates the code change from the tree change, which
   render-before/render-after cannot. The extension is a genuine no-op on the real tree.

5. **The stale-`TRACKS.md` story is true and pre-existing.** `docs/TRACKS.md` at HEAD differs from
   a fresh render by exactly **four added rows** — bp-124, bp-125, bp-126, bp-127 — and those rows
   are produced identically by the base code, so the staleness predates this diff (it dates from
   the graduation and blessing commits, which never regenerated the board). Render-before /
   render-after was therefore the **correct** substitute for the plan's literal falsifier, not a
   weaker test that hides a diff; comparing against the committed file would have reported a false
   failure. `docs/TRACKS.md` is untouched by this diff.

6. **The one orphan row is the known phantom.** The real tree carries exactly one orphan, from the
   **design note** `scored-beliefs-and-earned-entitlement` whose `track:` value has an inline `#`
   comment glued into the slug — `finding-0235`, whose fix is an owner hand-edit on a ratified
   note. Findings and owner questions contribute **zero** orphans: 210 findings and 57 owner
   questions scanned, none carrying a `track:` key. Nothing new.

7. **V1 — `next_action` is genuinely derivable; bp-127's premise is sound.** `handoff.derive`
   walks `_LADDER` over plan statuses read from front matter; nothing stores or reads a written
   answer. Confirmed adversarially: hard-coding `next_action` is caught by
   `test_next_action_and_unit_are_derived_from_the_tree`, and reversing the ladder's rung order is
   caught by that test **and** by the JSON test. bp-127's mechanical JSON compare survives.

8. **Scope.** All ten changed paths are inside `write_scope`, the plan's own journal, or new
   `docs/findings/**`. **Zero** deletions; **zero** lines removed from any test file (no erosion of
   the existing regression contract). The `scan_plans`/`scan_notes` extraction in `board.py` is
   behaviour-preserving (proven in (4)) and is warranted by §4's reuse promise. `plan.md` is
   untouched and `status:` is still `ready` — the builder performed no blessing.

9. **The gate, each leg run separately with output redirected to a file (never piped):**

| leg | observed |
|---|---|
| `uv run ruff check .` | All checks passed — rc 0 |
| `uv run python scripts/check_imports.py` | OK — import firewall + worker boundary — rc 0 |
| `uv run mypy core agents eval ops scheduler scripts` | Success: no issues found in **261** source files — rc 0, floor 0 |
| `uv run mypy` (argless) | **Found 69 errors in 20 files (checked 559 source files)** — exactly the baseline; **zero** in the four changed files |
| `uv run python -m ops.type_gate` | OK — rc 0; the one parked non-fatal shim report (finding-0223) unchanged |
| `uv run pytest -q` | **3 failed, 2300 passed, 15 skipped** in 304.93s |

The three failures are `test_core_imports_nothing_outside_core` (the finding-0103 ratchet),
`tests/e2e/test_dream_v2_live.py` (finding-0226) and `tests/e2e/test_scheduler_live.py` (the
known flake, which passed in the builder's run and failed in this one — hence 2300 passed here vs
the seal's 2301). **No new failure. Nothing in the diff regressed the suite.** The two new test
files run 41 tests, all green in 1.26s.

### Verified BY ADVERSARIAL MUTATION (do the tests actually redden?)

25 behaviour-breaking mutations were applied to a **scratch copy** of `handoff.py` / `board.py`
outside the repo and the delivered tests re-run against each. **19 of 25 were caught.** (An
initial pass was contaminated by stale `.pyc` reuse — mutate and restore within the same second
defeats CPython's mtime+size cache check; the definitive run disabled bytecode writing and purged
`__pycache__` between mutants. Recording this because a green mutation run is worthless if the
harness is what is being measured.)

Caught, among others: live queue in the committed render; a generation timestamp in the render;
a read-write queue open; a queue created on a miss; the render reading its own prior content; a
hand-written `next_action`; a reversed ladder; the row-width cap dropped; absent `track:` treated
as an orphan; findings/oqs dropped from the orphan surface; `--check` always reporting up to date;
`--write` minting a seat directory; a track scope leaking other tracks' plans; readings taken
first-in-file instead of last.

**Six survivors — the vacuous corners, all in display or secondary fields, none load-bearing for
the family:**

- `GENERATED_BANNER` set to `""` survives. `assert text.startswith(handoff.GENERATED_BANNER)` is
  **tautological in the constant**: emptying the banner cannot fail it. The plan's Item 2 criterion
  "the file carries the GENERATED banner" is therefore not actually falsifiable by this test. The
  pre-existing `test_board.py::test_generated_banner_present` has the identical shape, so this is
  inherited house style rather than a new lapse — but it is a genuine vacuous pass.
- `--json`'s `scope` field and `unit_title` field can each be corrupted with nothing objecting;
  `test_json_never_disagrees_with_the_document` pins only `next_action` and `unit_in_flight`.
  Low impact: those two are precisely the fields bp-127 compares, and the seal already tells
  bp-127 to treat `unit_title` as non-normative.
- The `status == open` filters for the findings pane and the owner-questions pane are untested —
  counting closed artifacts as open survives. The fixture has no closed finding.
- The `blocking: true` filter is untested for the negative case — treating every owner question as
  blocking survives, because the fixture's only non-blocking oq is also `answered` and is filtered
  out one step earlier. On the real tree that regression would render 29 `BLOCKED:` lines.

### Verified BY INSPECTION ONLY (not exercised)

- V3 (read-only SQLite vs the live supervisor's WAL) remains parked exactly as plan §11 records.
  No test pretends to exercise it and this audit did not either — it needs a daemon under load.
- The `## CAPSULE — <date>` marker is pinned in `docs/roles/orchestrator/journal.md:32` and is
  used nowhere else in that file, so bp-127's F1b lint key is sound. Not executed (F1b is bp-127).
- `docs/roles/orchestrator/{journal,readings,handoff}.md` are all tracked; the seat journal's
  bootstrap entry carries all seven checkpoint sections and `grep -nEo '\b[0-9a-f]{7,40}\b'`
  returns rc 1 over both hand-authored files. NARRATIVE purity survived contact.
- `finding-0236` is typed `spec-defect` → `orchestrator` and `finding-0237` `codebase` →
  `builder`; both types are in the taxonomy and both routes match the constitution's routing rule.
  Both carry re-entry conditions.

### ⚑ Could NOT be closed — the audit's real finding

**1. finding-0236's resolution is binding on bp-126 and bp-127, and neither plan can see it.**
This is the material risk, and it is not in the delivered diff — it is in what happens next.

The builder's two-view split (`--write`/`--check`/`--json` tree-pure; a bare render live) is the
right call and is proven correct above. But it makes two sentences of the **ratified** note false
of the shipped code: §2.5's *"the DERIVED pane renders the latest reading per command **with its
age**"* (the committed pane shows the reading's timestamp, not an age) and §2.9's listing of a
`data/queue.sqlite` read among the inputs to the committed rendering (it is not one). bp-126 and
bp-127 were **blessed against the note's text**, before this resolution existed. Neither plan's §2
context manifest names `finding-0236`.

The concrete failure mode is not hypothetical. Note §2.11 F1c says *"the generator must exit 0,
rendering `queue: unavailable`"*. A bp-127 builder reading only its plan and the note would
reasonably assert F1c against `--check` — which exits 0 in a fresh worktree **without ever
touching the queue path**. That is a green test that proves nothing, in the one plan whose entire
purpose is to make the fresh-agent test executable. F1c must be asserted against the **bare**
`uv run scripts/handoff.py --role orchestrator` stdout render.

Judgement asked for plainly: **a finding was the right instrument and is correctly typed and
routed, but a finding alone is not a sufficient terminal state here**, because its content now
functions as an instruction to two already-blessed plans rather than as a record for a future
sweep. It does not block this merge. It does block building bp-127 safely.

**2. Two of bp-124's own written criteria are discharged on a path the plan did not contemplate.**
Item 3's acceptance ("the rendering contains `queue: unavailable in this checkout`") and Item 2's
invariant ("no wall-clock anywhere in the rendering") were written for **one** rendering. The
builder shipped two. Item 3's line lands on the stdout path (verified by execution); the live path
does read the clock. Both are literally satisfiable, both were flagged by the builder rather than
buried, and the purpose behind each — a fixed point for the committed artifact — is preserved. An
owner ruling would settle whether the note or the code is the thing that moves.

**3. finding-0237's fix has no home.** The duplicated `## oq-NNNN` header regex was *introduced*
by this diff (`board.scan_oqs` is new; `docket._scan_oqs` pre-existed). Under the owner's DRY
strictness that is a defect rather than a nit, and the builder was right that it could not be
fixed inside this `write_scope`. But **no `ready` plan holds `scripts/docket.py`**, so nothing
currently schedules the dedup and the re-entry condition may never fire on its own.

### Minor, reported for completeness (none merge-blocking)

- `scripts/handoff.py:56` mutates global `sys.path` at import time (`sys.path.insert(0, ROOT /
  "scripts")`), and `scripts/eval.py` shadows the `eval` **package**. Confirmed by execution:
  after `import handoff`, `import eval` resolves to `scripts/eval.py` and `import eval.golden`
  raises `ModuleNotFoundError`. Latent today — `tests/unit/test_board.py` already performed the
  same insert before this diff and the full suite is green — but **bp-127's F2 harness will import
  `handoff`** and should import it late, or in a subprocess.
- Nothing in the suite asserts that the **real** committed `handoff.md` is up to date; drift would
  be invisible until bp-126 installs clause (e′). It is up to date today (verified).
- The rendering depends on `readings.md`, so appending a reading *after* regenerating re-arms
  clause (e′)'s check 1 once. It still converges in one step, and the builder's own seal commit
  already demonstrates the right order (readings and handoff in one commit) — but bp-126 should
  state the ordering so a future session does not read a second firing as a re-armed gate.
- The seal reports the inline queue read as "13 body lines"; it is **14** (16 counting the two
  module-level SQL constants) against §3 Q5's "~15" threshold. Immaterial — Item 2's import
  invariant forbids the `ops.lifecycle` import independently — but the figure is stated, so the
  correct figure is recorded here.
- Plan §6 pinned `_attach_plans` / `_attach_notes` as the import surface; the builder instead
  extracted new `scan_plans` / `scan_notes`. A deviation from a pinned interface, but the pinned
  functions return orphan lists rather than artifacts and could not have served, the change is
  proven behaviour-preserving, and §11 already names the extraction re-entry.

## Why it matters

A clean bill of health is what the merge rides on, and the builder's own green gate is not the
audit. The keystone property — that nothing daemon-derived reaches the committed artifact — was
the one thing that could have shipped green and destroyed bp-126, and it is now proven by
execution against a planted live queue rather than asserted by a fixture. Conversely the family's
real exposure turned out not to be in the code at all: a correct builder decision recorded only in
a finding, while the two plans it binds were blessed against the older text, is exactly the
"green build that breaks the next plan" shape this audit existed to look for.

## The conditions (each concrete and checkable)

**None require a change to the delivered diff.**

1. **Before bp-127 is built:** `docs/findings/finding-0236.md` must appear in bp-127's §2 context
   manifest, and F1c must be written against the bare `uv run scripts/handoff.py --role
   orchestrator` stdout render — never `--check`, which passes vacuously without touching the
   queue path. Checkable: `grep -c finding-0236 docs/build-plans/bp-127/plan.md` > 0.
2. **Before bp-126 is built:** same manifest entry in bp-126, plus a line stating that clause (e′)
   check 1 shells out to `--check` and must not re-implement the compare over a live render.
   Checkable: `grep -c finding-0236 docs/build-plans/bp-126/plan.md` > 0.
3. **Owner ruling owed (not blocking):** §2.5's "with its age" and §2.9's queue-read-as-input are
   now false of the committed artifact. Either amend the note by hand — the same sitting as A10
   (finding-0233) and finding-0235's slug fix — or accept finding-0236 as the standing correction.
   Record which.
4. **Post-merge, orchestrator:** run `uv run scripts/board.py --write` (`docs/TRACKS.md` is stale
   by four rows, pre-existing) and, after the bp-124 `ready → complete` flip,
   `uv run scripts/handoff.py --role orchestrator --write`. By the pin, that converges in one step.
5. **finding-0237:** give the dedup a home — a plan whose `write_scope` covers both
   `scripts/board.py` and `scripts/docket.py` — or record the decision to let it stand.
6. **Optional, test hardening (a two-line change each, no design in it):** assert the banner's
   literal text rather than the constant; add a closed finding and an open non-blocking owner
   question to `_fixture` so the `status`/`blocking` filters stop passing vacuously.

## Re-entry condition

Not blocking; bp-124 is merge-ready. **Re-entry:** (a) at bp-126's or bp-127's build, if either
plan is opened without `finding-0236` in its context manifest — stop and add it, this finding is
the warrant; (b) if clause (e′) is observed to fire twice after a regen commit, re-read the
readings-ordering note above before suspecting the pin; (c) if any of the six surviving mutants
becomes load-bearing (e.g. bp-127 decides to compare `--json`'s `scope` field), the corresponding
test gap must close first.

## Routing

`discovery` → **orchestrator**. The verification half is closed and needs no one; the open half is
a design-record decision (amend the note or let finding-0236 carry it) and two plan-manifest edits
on already-blessed plans — orchestrator acts, with the note amendment owner-only by hand.
