---
type: journal
plan: bp-124
started: 2026-07-27
updated: 2026-07-27
---

# Journal — bp-124 (the orchestrator seat substrate and its handoff generator)

## 2026-07-27 — Item 4 closed: the coordinate check reaches findings and owner questions

**Status line.** F-WF1 now covers the two artifact classes `_build` never scanned, and **the no-op
falsifier did not fire** — the real board rendering is byte-identical before and after.

**Completed — Item 4.**
- `board._build` now appends `_finding_orphans(root, tracks)` and `_oq_orphans(root, tracks)` to
  the orphan list. A `track:` on a finding or an owner question that names no manifest is reported
  with the *same* message every other class uses (extracted as `board._orphan`, so the check reads
  identically however it is reached).
- **The falsifier, measured the only way it can honestly be measured:**
  `board_text(ROOT)` and `queue_text(ROOT)` captured **before** the Item 4 edit and compared
  **after** → `TRACKS render unchanged by Item 4: True`, `DESKCHECK render unchanged: True`,
  `queue_count unchanged: True`. The real tree carries exactly **one** orphan row before and after,
  and it is the pre-existing `finding-0235` phantom (a ratified note's `track:` value with an
  inline `#` comment glued into the slug). I did not touch it: the file is a **ratified** design
  note, agent-immutable under A8, and `finding-0235` records that the fix is an owner hand-edit.
- ⚑ **Why NOT against the committed `docs/TRACKS.md`:** that file is already stale by four rows
  (bp-124…bp-127, never regenerated after graduation + blessing). Comparing against it would have
  reported a false failure. See the previous entry's Markers.
- `board.py`'s CLI contract is unchanged: `--queue-count` still prints one integer (`5`, same as
  before), `--write` still writes exactly the two board files, the no-flag path still renders both
  views to stdout. `docs/TRACKS.md` / `docs/DESKCHECK-QUEUE.md` are **not** in write_scope and are
  untouched in the diff (`git status --short` on both → empty).
- Docstring line added verbatim from plan §4's reconciliation.
- Four new tests in `tests/unit/test_board.py`: an orphaned finding **and** an orphaned oq surface
  in the coordinate check; five findings and two oqs with **no** `track:` change the rendering by
  exactly nothing (the over-reach falsifier as a standing test); a finding/oq whose slug *resolves*
  is silent and does not become a lane row; and the scan surface returns plans that declare no
  track at all (which the board filters and a role-scoped handoff must not).

**Design note recorded — findings/oqs get their coordinate CHECKED, not ATTACHED.** They do not
become members of `Track.plans` / `Track.note_statuses` and do not appear as board cards. Two
reasons: the board's lanes render *units of work*, and the "(info) manifest `x` has no plan/note
members yet" line says **plan/note** literally, so a finding-only track would still be truthfully
described. The track-scoped *join* over all four artifact classes — which is what note §2.3 asks
for — is `scripts/handoff.py --track <slug>`, built in Item 2, and it reads the same scanners.

**Filed.** `docs/findings/finding-0237.md` (`codebase` → builder): `board.scan_oqs` and
`docket._scan_oqs` now each carry a copy of the `## oq-NNNN` header regex. Not fixed in place —
`scripts/docket.py` is outside this plan's write_scope, and having `board` import `docket` would
couple two peer scripts through a private name for one pattern. Re-entry is a plan holding both
files, or any change to the oq entry shape.

**In-flight.** Nothing. All five items are closed.

**Next action.** Run the six-leg local gate (each leg separately, output to a file), append the
readings, regenerate `handoff.md`, and seal.

**Open questions.** None.

**Context-manifest delta.** None beyond the earlier entries.

**Markers.** None.

## 2026-07-27 — Items 2, 3 and 5 closed: the generator, its queue pane, its structured answer

**Status line.** `scripts/handoff.py` renders every scope the contract pins; the idempotence pin
holds and **Item 2's falsifier did not fire** — but only because the queue pane and the age display
were moved off the committed artifact, which is a builder decision against a gap in the ratified
note and is filed as `finding-0236`.

**⚑ The one real design collision, and how it was settled.** §2.9 pins the rendering as *a pure
function of the artifact tree* and, in the same breath, lists a read of `data/queue.sqlite` among
its inputs and an *age* beside each reading. `data/queue.sqlite` is not the artifact tree: it is
gitignored, absent from every worktree, and mutated continuously by a live supervisor. Queue counts
in the committed file would make two regenerations of an *unchanged tree* differ — Item 2's
falsifier, fired by the daemon rather than by any work — and would re-arm bp-126's clause (e′)
forever, which is the exact circularity this design exists to remove. An age is the same defect: a
clock read in an artifact that must have a fixed point. **Resolution:** one computation, two view
modes (`handoff._View.live`). `--write` / `--check` / `--json` render **tree-pure** (queue → a
pointer line; readings → their own timestamps, which §2.9 calls "data"); a bare `--role/--track/
--plan` renders **live** to stdout (the real probe; `queue: unavailable in this checkout` when the
file is absent; `18h ago` beside a reading). Every written acceptance criterion of Items 2/3/5 is
still discharged, because Item 3's lines and F1c both live on the stdout path. Full argument,
and the instructions bp-126/bp-127 need, are in `docs/findings/finding-0236.md`.

**Completed — Item 2 (`scripts/handoff.py`).**
- `uv run scripts/handoff.py --role orchestrator --write` twice over an unchanged tree → `cmp`
  reports **byte-identical** (3695 bytes). `--check` → `docs/roles/orchestrator/handoff.md: up to
  date`, rc 0.
- *Excluding itself*: appending garbage to `handoff.md` and re-rendering reproduces the reference
  byte-for-byte — the generator never reads its own output (nothing globs `docs/roles/**`).
- `grep -nEo '\b[0-9a-f]{7,40}\b'` over the rendering → **no matches** (rc 1). No generation
  timestamp: the only timestamp in the file is a reading's own, carried from `readings.md`.
- Widest rendered table row: **119** chars (`board.MAX_ROW` is 190). Capping reuses `board._cap`.
- Generator home per §3 Q1: a sibling importing `board`. `board.py`'s CLI and both its renderings
  are untouched by this item.

**Completed — Item 3 (the queue pane).**
- Absent queue: `handoff.main(["--role","orchestrator"])` → rc **0**, output contains
  `queue: unavailable in this checkout`, and **no `data/queue.sqlite` exists afterwards**
  (asserted in `test_absent_queue_degrades_and_creates_nothing`; also true of the real run in this
  worktree, which has no `data/` directory at all).
- Present queue (fixture): `queue: depth 2 · running 1` + a `RUNNING 3 · dream · lease …` row.
- The connection string is asserted to be exactly `file:{path}?mode=ro`
  (`test_the_queue_is_opened_with_a_readonly_uri`, a spy over `handoff.sqlite3.connect`).
- The **dry-run the plan asks for is now a standing test**: a `mode=ro` open of a *missing* path
  raises `sqlite3.OperationalError` and leaves no file behind — proof the generator is
  structurally incapable of creating the queue, not merely careful not to.
- A file that exists but is not a database degrades to `queue: present but unreadable — …`
  rather than raising.
- **§3 Q5, answered: the inline read is 13 body lines** (`read_queue`, plus two module-level SQL
  constants) — **under the ~15-line threshold**, so the `ops.lifecycle.snapshot` import does NOT
  earn its place and no `codebase` finding is owed on that point. Importing it was also blocked
  independently: Item 2's invariant pins handoff's imports to stdlib + `_lib` + `board`.
- V3 stays parked exactly as §11 records it: no test pretends to exercise WAL contention.

**Completed — Item 5 (`--json`).**
- `uv run scripts/handoff.py --role orchestrator --json` on the real tree emits
  `{"blocking_unknowns": [], "next_action": "/resume bp-123", "scope": "role:orchestrator",
  "unit_in_flight": "bp-123", "unit_title": "…"}`; two invocations `diff` clean.
- **⚑ V1 — `next_action` IS DERIVABLE. It was never hand-written.** See the dedicated note below;
  bp-127's mechanical compare survives.
- The JSON and the document are two views of one call to `derive()`, and a test asserts the
  document literally contains the JSON's `next_action` and `unit_in_flight` strings, so they
  cannot drift apart.

**⚑ V1 (note §2.12) — the answer bp-127 needs, stated plainly.** **`next_action` proved DERIVABLE
from the artifact tree.** It is a three-rung ladder over plan statuses, computed in
`handoff.derive` / `handoff._LADDER`: an `in-progress` plan (lowest id) → `/resume <id>`; else a
`ready` plan (lowest id) → `/build <id>`; else `/triage`. For a `plan` scope the plan's own status
decides (`complete` → deskcheck owed, `proposed` → owner blessing owed, …). Nothing is hand-set,
and the emitted form is a **bare command string** (`"/resume bp-123"`) chosen specifically to make
a string compare viable. **bp-127's F2 JSON compare therefore survives contact — it does not
degrade to judge-only.** Two honesty caveats for that plan: (a) the ladder encodes a *policy*
(in-flight beats available; owner-only gates are never an agent's next action), so an agent that
answers "bless bp-124" instead of "/resume bp-123" is disagreeing with the policy, not with the
tree — the compare tests conformance to the ladder, which is what makes it mechanical; (b)
`unit_in_flight` is a bare id (`"bp-123"` / `"none"`), so compare on the id and treat the title as
non-normative prose.

**In-flight.** Item 4 — the coordinate check over findings and owner questions.

**Next action.** Extend `board._build`'s orphan surface to `docs/findings/*.md` and
`docs/inbox/owner-questions.md` using the already-added `board.scan_findings` / `board.scan_oqs`,
add the docstring line from plan §4, extend `tests/unit/test_board.py`, then re-run the byte-
identity check below.

**Open questions.** None blocking. `finding-0236` is filed and routed to the orchestrator.

**Context-manifest delta.** No new reads beyond the previous entry's list.

**Markers.**
- ⚑ **`docs/TRACKS.md` is ALREADY STALE in the committed tree, and it was stale before I touched
  anything.** A fresh `board.board_text()` at the pre-refactor commit differs from the committed
  file by exactly **four added rows** — bp-124, bp-125, bp-126, bp-127 — because the graduation and
  blessing commits never regenerated the board. `docs/TRACKS.md` is **not** in this plan's
  write_scope, so it is deliberately left alone; the orchestrator should run
  `uv run scripts/board.py --write` after the merge. **Consequence for Item 4's falsifier:** it
  must be measured as *render-before == render-after*, never as *render == the committed file*,
  or a pre-existing staleness would masquerade as this plan's regression.
- **The `board.py` scan refactor is proven output-neutral.** `scan_plans` / `scan_notes` were
  extracted so `handoff.py` can reuse them (§4's docstring promise); the post-refactor
  `board_text(ROOT)` is byte-identical to the pre-refactor one (captured by `git stash`, compared,
  confirmed `True`). `scan_findings` / `scan_oqs` were added in the same pass but are not yet
  wired into `_build` — that wiring is Item 4, so the board's behavior is still unchanged.

## 2026-07-27 — Item 1 closed: the seat directory and its two hand-authored artifacts

**Status line.** `docs/roles/orchestrator/{journal,readings}.md` exist, are tracked, and the
NARRATIVE purity rule survived contact — Item 1's falsifier did **not** fire.

**Completed — Item 1.**
- `docs/roles/orchestrator/journal.md` — bootstrap entry carrying all seven checkpoint sections
  (Status line / Completed / In-flight / Next action / Open questions / Context-manifest delta /
  Markers). Acceptance grep `grep -nEo '\b[0-9a-f]{7,40}\b'` over the file → **no matches**
  (exit 1). The entry names `bp-125`, `bp-126`, `finding-0234` by id and states no status, no
  count, no sha, no `path:line`.
- `docs/roles/orchestrator/readings.md` — the MEASURED log, one bootstrap row
  (`uv sync --frozen --extra dev`). Row shape `| timestamp | command | result |` as a markdown
  table, chosen so the DERIVED pane can take "latest row per command" by *file order* (append-only)
  without parsing timestamps — see the Item 2 note below on why that matters for idempotence.
- **Item 1's falsifier (a real entry is unwritable without a derivable value) did not fire.** The
  entry is genuine seat judgement — why files beat the queue as substrate, why the migration is
  deliberately not here, what V4 asks of the first weeks of use. The purity rule cost nothing.

**⚑ Decision recorded — the compaction-capsule marker (bp-127 F1b needs this).** The seat journal's
header pins the marker as the literal heading **`## CAPSULE — <date>`**, and defines the
authoritative segment as *the latest such heading plus every entry above it* (entries are newest-
first in this file, so "after the capsule" in §2.8's newest-last phrasing is "above it" here).
Nothing else in the file uses that heading. bp-127's F1b lint should key on exactly that string.

**In-flight.** Item 2 — `scripts/handoff.py`.

**Next action.** Write `scripts/handoff.py`: argparse CLI per plan §6, importing `board`'s scan
functions and `_cap`/`MAX_ROW`, rendering the `role` scope tree-pure.

**Open questions.** One, carried into Item 2 and 3 — see the next entry: the idempotence pin says
the rendering is a pure function of *the artifact tree*, and `data/queue.sqlite` is not the
artifact tree. Resolution is recorded at Item 3.

**Context-manifest delta.** Read beyond the manifest: `docs/findings/finding-0235.md` (filed after
this plan was written; it bears directly on Item 4 — a corrupted `track:` value in a ratified note
already produces a phantom orphan, so the pre-existing board rendering is *wrong* in a way Item 4
must not accidentally "fix" or worsen), `.claude/hooks/_lib.py:169-244` (the parser's exact
scalar/`#` semantics), `scheduler/queue.py` state constants (lowercase `queued`/`running`, and
`lease_expires_at`), `pyproject.toml` `[tool.mypy]` (confirmed `scripts`+`tests` enrolled; no edit
needed), `docs/inbox/owner-questions.md` (entry shape — `- key: value` bullets under a
`## oq-NNNN` heading, *not* per-question front matter; that decides how Item 4 reads a `track:`
off an owner question).

**Markers.** Base check: this worktree branched from `ac83ca3`, one commit *ahead* of the expected
`dd2fa3f`; the delta is only the bp-125/126/127 readiness blessings, which touch no file in this
plan's scope. `.claude/state/active-plan` is **absent** in this worktree, so `scope-guard` is in
orchestrator posture (denylist only) — write_scope is self-enforced here and audited post-hoc by
the Stop gate.

Minted 2026-07-26 by `/graduate`, decomposing ratified `dn-role-state-and-scoped-handoff`
(blessed `c0abfd1`) in one context into a **four**-plan family (bp-124…bp-127). The note's §3
sketched two; the graduation departed from it — the reasons are in `docs/findings/finding-0234.md`
and in each plan's §12. **Not started.**

## Pre-build notes for whoever picks this up

- ⚑ **This is the zero-blast-radius plan of the family. Keep it that way.** No gate change, no
  deletion, no skill edit, no migration. If a criterion seems to want one, it belongs to bp-125,
  bp-126, or bp-127 — file a finding rather than reaching.
- ⚑ **The idempotence pin is the family's keystone.** A rendering that embeds a HEAD sha or a
  `now()` has no fixed point and would re-arm clause (e′) forever — the current brief's
  circularity, mechanized. If Item 2's falsifier fires (two renders differ), **stop**: bp-126
  cannot be built on top of it.
- **The generator home was ruled at graduation**, not left open: a sibling `scripts/handoff.py`
  importing `board`, because `board.py`'s CLI is substring matching (`if "--write" in argv`) and
  its `--write` writes **both** board files unconditionally (`scripts/board.py:439-445`). §3 Q1
  carries the grounding; §11 carries the re-entry condition.
- **The note's §2.3 claim that the orphan check covers findings/oqs "for free" is FALSE.**
  `board.py` scans exactly four globs — `docs/tracks/*.md`, `docs/build-plans/*/plan.md`,
  `docs/design-notes/*.md`, `docs/deskchecks/*.md` (`:136,162,188,203`). Findings and
  `docs/inbox/owner-questions.md` are never scanned. Item 4 makes the claim true; that is why
  `scripts/board.py` and `tests/unit/test_board.py` are in `write_scope`.
- **Item 4's falsifier is a no-op check.** No finding or oq carries a `track:` today, so a correct
  extension changes **nothing** in `docs/TRACKS.md` beyond the docstring. Any other diff means
  the scan treats an absent key as an orphan — which would flood the coordinate check with 232
  false rows.
- **`pyproject.toml` is deliberately not in scope.** `[tool.mypy] files` already lists `scripts`
  and `tests` (`pyproject.toml:128`), so new files there are enrolled automatically. Do not add
  an entry with no criterion behind it.
- **V3 is parked, not resolved** (§11): read-only SQLite vs the live supervisor's WAL. The pane
  ships; non-contention is *expected*, never tested. Do not write a test that pretends otherwise.
- **The queue open must never create `data/queue.sqlite`.** Use the `file:…?mode=ro` URI form and
  prove absence-after-run in a test. Creating it breaches the single-writer model
  (`scheduler/queue.py:17-18`).

## Owed at seal (orchestrator, not the builder)

- A `## Follow-through` block is required by Stop-gate clause (f) (`.claude/hooks/_lib.py:929-937`).
- Record whether `next_action` proved **derivable** from the tree (Item 5). **bp-127 reads this
  journal to decide V1** — if the field could only be hand-written, say so plainly here; that is
  V1 landing early and bp-127's drill degrades to judge-only.
- Record whether the inline queue read stayed under ~15 lines (§3 Q5); if not, the
  `ops.lifecycle.snapshot` import earns its place and a `codebase` finding should say so.

---

## SEAL — 2026-07-27: all five items closed; the pin holds and V1 lands positive

> Entry order in this file: the three per-item entries above are newest-first under the H1; this
> SEAL is at the **tail**, where `_journal_tail_has_followthrough` looks for it.

**Status line.** bp-124 is built and verified. The orchestrator seat has its three artifacts,
`scripts/handoff.py` renders every scope the contract pins, the coordinate check reaches findings
and owner questions, and **no falsifier in the plan fired**. The plan's `status:` is deliberately
left at `ready` — flipping it is the orchestrator's act on merge, not a builder's.

**What was built, against each acceptance criterion.**

| item | criterion | evidence |
|---|---|---|
| 1 | seat artifacts exist, tracked, seven sections, zero hex | both files committed; `grep -nEo '\b[0-9a-f]{7,40}\b'` → rc 1, no matches |
| 2 | two `--write` runs byte-identical; committed == fresh; rows ≤190; banner; no sha/timestamp | `cmp` clean over two runs; `--check` rc 0; widest row **190 chars** exactly (194 *bytes* — `_cap` counts characters, as `test_board` always has); banner first line |
| 3 | absent queue → rc 0 + `queue: unavailable in this checkout`; fixture queue renders rows; `mode=ro` asserted; nothing left behind | four tests, incl. a standing proof that a `mode=ro` open of a missing path **raises** rather than creating |
| 4 | orphaned finding/oq surface; absent `track:` is not an orphan; board CLI + rendering unchanged | render captured before the edit, compared after → **byte-identical**; `--queue-count` still `5` |
| 5 | `--json` parseable, `unit_in_flight` + `next_action` tree-derived, byte-stable | two invocations `diff` clean; both fields fall out of `derive()`; a test pins doc↔JSON agreement |

**Gate — every leg run separately, output to a file, not piped.**

| leg | result |
|---|---|
| `uv run ruff check .` | **All checks passed** (rc 0) |
| `uv run python scripts/check_imports.py` | **OK** — import firewall + worker boundary (rc 0) |
| `uv run mypy core agents eval ops scheduler scripts` | **Success: no issues found in 261 source files** — floor 0 (rc 0) |
| `uv run mypy` (argless) | **Found 69 errors in 20 files (checked 559)** — exactly the recorded baseline; **none in `scripts/handoff.py`, `scripts/board.py`, or either new test file** |
| `uv run python -m ops.type_gate` | **OK** (rc 0); one parked non-fatal shim report (finding-0223), unchanged |
| `uv run pytest -q` | **2 failed, 2301 passed, 15 skipped** in 356s |

⚑ **The exact failure count, stated so no one has to re-derive it: TWO, and both pre-existing.**
`tests/unit/test_core_self_containment.py::test_core_imports_nothing_outside_core` (the
finding-0103 ratchet) and `tests/e2e/test_dream_v2_live.py::test_dream_v2_synthesizes_grounded_
themes_live` (finding-0226). Neither is in CI or the deploy gate; neither is touched by this diff.
The third known-fragile one, `tests/e2e/test_scheduler_live.py`, **passed** this run.

**Answers the family is waiting on.**

1. **⚑ V1 (note §2.12) — `next_action` IS DERIVABLE from the artifact tree. It was never
   hand-written.** `handoff.derive` walks `_LADDER`: an `in-progress` plan (lowest id) →
   `/resume <id>`; else a `ready` plan (lowest id) → `/build <id>`; else `/triage`. A `plan` scope
   answers from its own status. The emitted value is a **bare command string** chosen to make a
   mechanical compare viable. **bp-127's F2 JSON compare survives contact and does NOT degrade to
   judge-only.** Two caveats for that plan, so it is not surprised: (a) the ladder encodes a
   *policy* — in-flight beats available, and an owner-only gate is never an agent's next action —
   so a disagreeing answer is disagreeing with the policy, not with the tree; (b) compare
   `unit_in_flight` as a bare id (`"bp-123"` / `"none"`) and treat `unit_title` as non-normative.
2. **The inline queue read is 13 body lines** (`read_queue`, plus two module-level SQL constants) —
   **under §3 Q5's ~15-line threshold**, so the `ops.lifecycle.snapshot` import does not earn its
   place and **no `codebase` finding is owed on that question**. It was independently blocked
   anyway: Item 2's invariant pins handoff's imports to stdlib + `_lib` + `board`.
3. **⚑ The compaction-capsule marker is `## CAPSULE — <date>`**, pinned in
   `docs/roles/orchestrator/journal.md:32`. The **authoritative segment** is the latest such
   heading plus every entry **above** it (that file is newest-first, so §2.8's "entries after the
   capsule" reads as "above" there). Nothing else in that file uses the heading. **bp-127's F1b
   lint should key on exactly that string.**
4. **⚑ bp-126 must not re-implement `--check`.** The committed rendering is tree-pure by
   construction and the live queue/age panes are stdout-only — see `finding-0236` for why that was
   forced, and what would break if the probe were moved back into `--write`.

**Findings filed.**
- `docs/findings/finding-0236.md` (`spec-defect` → orchestrator): the queue pane and the age
  display cannot live in the committed rendering without breaking the idempotence pin; how bp-124
  resolved it and what bp-126/bp-127 must do.
- `docs/findings/finding-0237.md` (`codebase` → builder): `board.scan_oqs` and `docket._scan_oqs`
  now each carry the `## oq-NNNN` header regex; not fixable inside this write_scope.

**Left for the orchestrator (not builder acts, deliberately not done).**
- **`docs/TRACKS.md` is stale by four rows** (bp-124…bp-127) — pre-existing, from the graduation
  and blessing commits. Run `uv run scripts/board.py --write` after the merge. It is outside this
  plan's write_scope and is untouched in the diff.
- `docs/roles/orchestrator/handoff.md` will need one regeneration after the merge, because the
  merge changes plan statuses. By the pin, that regeneration converges in exactly one step.
- The plan `status:` flip and the `docs/DESKCHECK-QUEUE.md` row.

**In-flight.** Nothing.

**Next action.** Merge review. Nothing in this plan is left half-done.

**Open questions.** None blocking; both findings are routed.

**Context-manifest delta.** Consolidated from the per-item entries: `docs/findings/finding-0235.md`
(filed after the plan was written; it explains the single pre-existing orphan row Item 4 must not
disturb), `.claude/hooks/_lib.py:169-244` (the parser's `#`-handling — the reason Item 4 must NOT
strip comments from a `track:` value), `.claude/hooks/_lib.py:710-718` + `:925-937` (clause (f)'s
tail semantics, which is why this SEAL sits at the file's end), `scheduler/queue.py` state
constants (lowercase), `pyproject.toml` `[tool.mypy]` (confirmed enrolment; no edit), and
`docs/inbox/owner-questions.md`'s entry shape. Nothing in the manifest proved irrelevant.

```read-map
docs/findings/finding-0236.md:1: THE design decision of this plan — the queue pane and the age display cannot sit in the committed rendering without breaking the idempotence pin; read before bp-126
scripts/handoff.py:20: the two-view resolution stated at the top of the module — why --write/--check/--json are tree-pure and a bare render is live
scripts/handoff.py:79: _LADDER — the whole of `next_action`, and therefore the whole of V1's answer
scripts/handoff.py:202: read_queue — 13 lines, `file:…?mode=ro`, missing-file-is-a-value; the single-writer boundary in code
scripts/handoff.py:244: derive() — the one computation both the document and the JSON are views of
scripts/handoff.py:290: render() — the section set; note the `view.live` branches at the queue and readings panes
scripts/board.py:12: the docstring line plan §4 required — the widened coordinate surface and the sibling that reuses these scanners
scripts/board.py:163: _orphan() — one phrasing for the F-WF1 message across all four artifact classes
scripts/board.py:174: scan_plans/scan_notes/scan_findings/scan_oqs — the shared scan surface; output-neutral extraction, proven by byte-compare
scripts/board.py:263: _finding_orphans / _oq_orphans — Item 4 proper; the "absent track: is normal" clause is the load-bearing line
scripts/board.py:498: _build — where the two new orphan sources join, and the comment on why findings are CHECKED not ATTACHED
docs/roles/orchestrator/journal.md:32: the compaction-capsule marker bp-127's F1b lint must key on
tests/unit/test_handoff.py:95: the idempotence falsifier — two renders byte-equal
tests/unit/test_handoff.py:102: the "excluding itself" half of the pin
tests/unit/test_handoff.py:209: F1c — absent queue exits 0 and creates nothing
tests/unit/test_handoff.py:233: the connection string is asserted to be mode=ro
tests/unit/test_handoff.py:248: proof that a mode=ro open of a missing path RAISES rather than creating it
tests/unit/test_handoff.py:290: the doc and the JSON cannot drift apart
tests/unit/test_board.py:153: Item 4's positive case — an orphaned finding AND an orphaned oq surface
tests/unit/test_board.py:166: Item 4's falsifier as a standing test — artifacts with no `track:` change the rendering by nothing
```

## Follow-through
- **Built?** Yes, all five items. `docs/roles/orchestrator/{journal,readings,handoff}.md`,
  `scripts/handoff.py` (the generator, all five CLI forms), the `scripts/board.py` scan-surface
  extraction plus the findings/oq coordinate check, and 24 + 4 new tests. Gate green on every leg;
  the only two suite failures are the two pre-existing ones named above.
- **Wired / delivered (or why dormant)?** Wired as far as this plan is permitted to wire it, and
  no further **by design**. The generator is runnable today (`uv run scripts/handoff.py --role
  orchestrator --write|--check|--json`) and the artifacts are tracked, so they are present in
  every checkout. It is **not** yet on any gate or hook: clause (e′) is bp-126's atomic diff, and
  `session-brief.sh` still surfaces the old brief. That is this plan's stated overlapping window
  (§0), not an unfinished switch — the ON switch for *this* deliverable is the CLI, and it exists.
- **Does a consumer use it?** Not yet — and that is the honest answer. Today's consumer is a human
  running the command. The mechanical consumers are bp-126 (clause (e′) calls `--check`) and
  bp-127 (F1a/F1b/F1c and the F2 drill compare against `--json`). Both are `ready` and both read
  this journal, which is why the four answers above are stated flatly rather than hedged. The old
  resume brief is still the live handoff surface until bp-125 and bp-126 land.
- **Track state (what remains on this track)?** `workflow`. bp-124 done; **bp-125** (migrate the
  brief — MAIN CHECKOUT ONLY, finding-0234), then **bp-126** (the cutover: clause (e′), the
  re-point, the deletion), then **bp-127** (F1b/F1c/F2). The dependency edges are load-bearing:
  bp-126 deletes the brief, so bp-125 must have migrated it first. bp-095, bp-111…bp-119 remain
  `ready` on other tracks and are unaffected — none holds `.claude/hooks/**` or `scripts/board.py`.
- **Opened a new track/finding?** No new track. Two findings: `finding-0236` (`spec-defect` →
  orchestrator — the idempotence/queue collision, with bp-126 and bp-127 instructions) and
  `finding-0237` (`codebase` → builder — the duplicated oq header regex). `finding-0234` and
  `finding-0235` both remain open and are unaffected by this diff; `finding-0235`'s phantom orphan
  is the one row Item 4 deliberately left in place, since fixing it is an owner hand-edit on a
  ratified note.
