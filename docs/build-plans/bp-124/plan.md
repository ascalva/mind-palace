---
type: build-plan
id: bp-124
track: workflow
status: proposed
design_ref:
  - docs/design-notes/role-state-and-scoped-handoff.md
contract: builder
write_scope:
  - scripts/handoff.py
  - scripts/board.py
  - tests/unit/test_handoff.py
  - tests/unit/test_board.py
  - docs/roles/**
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 450k
  actual: null
depends_on: []
parallelizable_with: []
created: 2026-07-26
updated: 2026-07-26
links:
  - docs/design-notes/role-state-and-scoped-handoff.md
  - docs/findings/finding-0175.md
  - docs/findings/finding-0234.md
  - scripts/board.py
  - scripts/docket.py
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — the orchestrator seat substrate and its handoff generator

> **Every section below is required.** A section that does not apply is marked
> `N/A — <one-line reason>`, never silently omitted.

## 0. Mode & provenance

Investigation and planning produced this plan; implementation proceeds item-by-item on
owner approval. It graduates `dn-role-state-and-scoped-handoff` (ratified 2026-07-26,
`c0abfd1`) §2.3, §2.5, §2.6, §2.9 and the F1a falsifier of §2.11.

Authority-to-act (the owner's instruction to build) is separate from the readiness
blessing. **This plan is `proposed`. No agent flips it to `ready`** — `gate-guard` denies
the Edit path and the Stop-gate (c) audit catches a Bash-mediated flip.

**This is the zero-blast-radius plan of the family.** It adds new files and extends one
generator; it changes **no** gate, deletes **nothing**, and leaves
`.claude/state/resume-brief.md`, `.claude/hooks/_lib.py` clause (e), and
`.claude/hooks/session-brief.sh` exactly as they are. The seat artifacts it creates sit
beside the current brief during the note's deliberately overlapping window (§4 of the
note, stage (a)); double bookkeeping for that duration is accepted by design.

## 1. Objective

Create the orchestrator seat's three tracked artifacts (`docs/roles/orchestrator/{journal,readings,handoff}.md`)
and the deterministic, idempotent generator that renders the DERIVED one — with a
read-only queue pane that degrades gracefully when `data/queue.sqlite` is absent.

## 2. Context manifest

Read exactly these, in order, before any work:

1. `docs/design-notes/role-state-and-scoped-handoff.md` — the ratified decision, whole.
   §2.3 (scope taxonomy), §2.5 (the four-way split), §2.6 (files-as-source ruling),
   §2.9 (the artifact set + generator contract + **the idempotence pin**), §2.11 F1a.
2. `scripts/board.py` — the generator being extended and the scan machinery being reused.
   Read whole (455 lines); its `_scan_manifests` / `_attach_plans` / `_attach_notes` /
   `_build` are this plan's reuse targets.
3. `scripts/docket.py` — the cannot-drift falsifier's origin and the second precedent for
   "repo-workflow tooling: reuse `_lib`'s parser, never import `core`."
4. `tests/unit/test_board.py` — the house test shape for a derived view (idempotence,
   row width, no-core AST guard). This plan's new test file mirrors it.
5. `.claude/hooks/_lib.py` — **only** `parse_front_matter` / `_normalize_status` /
   `read_front_matter` (the reused parser). Do not modify this file; it is out of scope.
6. `ops/lifecycle/snapshot.py:318-348` — `read_queue_stats`, the read-only-SQLite
   precedent (`file:…?mode=ro`, missing-file returns `exists=False` rather than raising).
7. `docs/findings/finding-0234.md` — the three graduation-time corrections to the note
   that this plan carries; Item 4 exists because of correction (3).

**Does `core/` already implement this? (the DRY audit.)** No — and it must not. This is
repo-workflow tooling, the same class as `scripts/board.py` and `scripts/docket.py`, both
of which state explicitly that they "never import `core`"
`[GROUNDED scripts/board.py:12-13; scripts/docket.py:15-16]`. The front-matter parser is
the one thing that would otherwise be re-derived, and it is **reused** from
`.claude/hooks/_lib.py` exactly as both siblings do `[GROUNDED scripts/board.py:28-33]`.
No mathematical object and no core primitive is introduced. The queue read reuses the
`read_queue_stats` *shape* (`file:…?mode=ro` URI, missing file is not an error) rather
than importing it — see §3 Q5 for why that call is grounded as a shape, not a dependency.

## 3. Investigation & grounding  <!-- Part A -->

- **Q1 — Where does the generator live: a `board.py` subcommand or a sibling script?**
  The note leaves this "a graduation-time call" (§2.9). **Ruling: a sibling
  `scripts/handoff.py` that imports `board`.** Grounded: `board.py`'s CLI is positional
  substring matching, not argparse — `if "--queue-count" in argv` / `if "--write" in argv`
  `[GROUNDED scripts/board.py:439-442]` — and its `--write` writes **both** board files
  unconditionally `[GROUNDED scripts/board.py:443-445]`. Adding `--role/--track/--plan`
  alongside would overload one `--write` flag across two derived views with different
  cadences and different write targets, and would make `board.py --write` ambiguous. A
  sibling keeps `board.py --write`'s contract byte-identical while reusing its scan
  functions by import. Its module-level `def`s are importable as-is; `board.ROOT` derives
  from `board.__file__` so an import from `scripts/` resolves correctly
  `[GROUNDED scripts/board.py:26]`.

- **Q2 — Does the idempotence pin hold against the existing generators?**
  Yes, and `board.py` is the proof: it embeds no timestamp and no HEAD sha, and
  `tests/unit/test_board.py` already asserts two renders over an unchanged tree are
  byte-equal `[GROUNDED tests/unit/test_board.py:1-8]`. The pin (§2.9) is therefore not a
  new discipline, it is the existing one restated as a hard requirement for this artifact.

- **Q3 — Is `scripts/handoff.py` automatically enrolled in the type gate?**
  Yes. `[tool.mypy] files = ["core", "agents", "config", "eval", "ops", "scheduler",
  "scripts", "tests"]` `[GROUNDED pyproject.toml:128]` — directory-level, so a new file
  under `scripts/` and a new file under `tests/` are both covered with **no `pyproject.toml`
  edit**. This is why `pyproject.toml` is deliberately absent from §5.

- **Q4 — Does the new code need enrolment in `ops/import_lint.py`'s `NETWORK_ALLOWLIST`?**
  No. That allowlist governs modules under `core/` importing networking primitives
  `[GROUNDED ops/import_lint.py:57,96]`. `scripts/handoff.py` is neither under `core/` nor
  networked. No registry edit is required for any acceptance criterion here.

- **Q5 — Can the generator reuse `ops.lifecycle.snapshot.read_queue_stats` directly?**
  **The code does not settle this, and the plan does not force it.** `read_queue_stats`
  has the right read-only posture — `sqlite3.connect(f"file:{path}?mode=ro", uri=True)`
  and `if not path.exists(): return _EMPTY_QUEUE_STATS`
  `[GROUNDED ops/lifecycle/snapshot.py:334-338]` — but importing it drags `ops.lifecycle`
  (and its `datetime`/`QueueStats` surface) into a script whose two siblings deliberately
  import nothing but stdlib + `_lib`. Which side of that trade is right depends on whether
  `ops` counts as "outside repo-workflow tooling," and **no artifact rules on it**. What
  would settle it: the DRY audit's own question asked of `ops` — if a second workflow
  script ever needs queue stats, the shared home is `ops`, and the import is correct; until
  then it is one 6-line read. **Decision for this plan: implement the read inline in
  `handoff.py` with the same `mode=ro` URI and missing-file-is-not-an-error posture, and
  record in the journal that the import was considered and why it was declined.** If the
  builder finds the inline read exceeds ~15 lines, that is the signal to import instead —
  file a `codebase` finding and switch.

- **Q6 — Does the existing orphan check really cover findings and owner questions "for
  free," as the note's §2.3 asserts?** **No — the note is wrong, and reading settles it.**
  `board.py`'s scan surface is exactly four globs: `docs/tracks/*.md`,
  `docs/build-plans/*/plan.md`, `docs/design-notes/*.md`, `docs/deskchecks/*.md`
  `[GROUNDED scripts/board.py:136,162,188,203]`. Findings and `docs/inbox/owner-questions.md`
  are **never scanned**, so a `track:` key added to a finding gets no orphan coverage at
  all. This is corrected here (Item 4) rather than inherited silently — warrant
  `finding-0234` correction (3).

- **Q7 — Does `docs/roles/` collide with anything?** No. The directory does not exist
  `[GROUNDED: `ls docs/roles` → No such file or directory, 2026-07-26]`, no glob in
  `scripts/board.py` or `scripts/docket.py` reaches it, and it is not on the foundation
  denylist (`DENYLIST = ["CONSTITUTION.md", "eval/golden/**", "eval/golden.py"]`)
  `[GROUNDED .claude/hooks/_lib.py:35-39]`.

- **Q8 — What is the current seat state the first `handoff.md` must render?**
  `[GROUNDED, 2026-07-26]` plans bp-000…bp-123 exist; `bp-123` is `in-progress`,
  bp-111/112/113/114/116/117/118/119 are `ready`, the rest complete/superseded; ten track
  manifests under `docs/tracks/`; 232 findings. The rendering is a pure function of that
  tree — the builder must not hand-write any of it.

**Additional risks or questions surfaced during reading:**

- `board.py` currently has **no argparse**. Item 4 extends its scan surface but must not
  change its CLI: `--queue-count` and `--write` behavior stay byte-identical, which
  `tests/unit/test_board.py` already pins.
- The `track:` key on findings is **optional and not back-filled**. No existing finding
  gains one in this plan; the generator and the orphan check must both treat "no `track:`"
  as normal, not as an orphan.

## 4. Reconciliation  <!-- Part B -->

- `scripts/board.py:2-13` (module docstring) — currently: *"It renders BOTH board files
  from front matter + the `docs/tracks/<slug>.md` manifests + any deskcheck records"*.
  → **[cross-ref: extension]**: the docstring gains a line naming the widened coordinate
  surface and the sibling that reuses its scanners — *"Coordinate integrity (F-WF1) now
  also covers findings and owner questions that declare a `track:` (bp-124,
  dn-role-state-and-scoped-handoff §2.3). `scripts/handoff.py` reuses these scan functions;
  its own renderings are its concern, not this module's."* No behavior of the existing two
  renderings is replaced.

- `docs/design-notes/role-state-and-scoped-handoff.md:196-197` — currently asserts *"the
  existing orphan check covers the new members for free."* → **[banner: correction]**, and
  the correction is **not** made in the note (ratified notes are agent-immutable, A8
  `[GROUNDED .claude/hooks/_lib.py:435-441]`). It is carried by `docs/findings/finding-0234.md`
  correction (3) and discharged by Item 4 of this plan. The builder must not edit the note.

- Nothing else is corrected. `scripts/docket.py`, `.claude/hooks/_lib.py`,
  `.claude/hooks/session-brief.sh` and every skill are untouched by this plan.

## 5. Write scope

Front-matter globs, mirrored here with rationale (the front-matter entries are **bare
globs** — no inline comments, per finding-0085 / the bp-066 footgun):

- `scripts/handoff.py` — the new generator. The plan's principal deliverable.
- `scripts/board.py` — **carried because Item 4 extends its scan surface.** The orphan
  check must reach findings and owner questions (§3 Q6); that is an edit to this file, not
  to the sibling.
- `tests/unit/test_handoff.py` — the new generator's tests (F1a idempotence, `--check`,
  queue degradation, no-core AST guard, row width).
- `tests/unit/test_board.py` — **carried because it pins the surface this plan moves.**
  It asserts the coordinate-check rendering and the orphan messages
  `[GROUNDED tests/unit/test_board.py:1-8]`; Item 4 adds member classes to that rendering,
  so these assertions must be extended in the same session or they redden.
- `docs/roles/**` — the seat artifact trio. A new directory; nothing pre-exists here.

**Deliberately OUT of scope, and why:**

- `.claude/hooks/_lib.py` and `.claude/hooks/session-brief.sh` — **no gate change in this
  plan.** Clause (e) keeps governing and the brief keeps being auto-surfaced. bp-126 owns
  both files; two plans must never hold `.claude/hooks/**` at once (§12).
- `.claude/state/resume-brief.md`, `docs/templates/resume-brief.md` — the retirement is
  bp-126's atomic diff, not this plan's.
- `.claude/skills/**` — the contract updates are bp-125's.
- `pyproject.toml` — **not needed**: `scripts` and `tests` are already in
  `[tool.mypy] files` (§3 Q3). Adding it would be scope with no criterion behind it.
- `docs/design-notes/**` — ratified notes are agent-immutable (A8); the note's errors are
  carried by findings, never by an edit.
- `docs/PROGRESS.md`, `docs/inbox/owner-questions.md` — orchestrator single-writer
  surfaces and explicit non-goals of the design note (§1.2).
- `docs/tracks/workflow.md` — this plan declares `track: workflow`, whose manifest already
  exists, so no orphan is created. Extending that manifest's DoD is an orchestrator act,
  not a builder's, and no acceptance criterion here depends on it.

## 6. Interfaces pinned inline

**The reused front-matter parser** — `scripts/board.py:28-33`, copied verbatim; the new
script uses the identical import block:

```python
ROOT = Path(__file__).resolve().parent.parent

# Reuse the artifact front-matter machinery — never re-derive it (plan §2 DRY audit).
sys.path.insert(0, str(ROOT / ".claude" / "hooks"))
from _lib import (  # type: ignore[import-not-found]  # noqa: E402
    _normalize_status,
    parse_front_matter,
)
```

**The generated banner convention** — `scripts/board.py:39`:

```python
GENERATED_BANNER = "<!-- GENERATED by scripts/board.py — do not hand-edit -->"
```

`handoff.py` defines its own, naming **its own** path:
`"<!-- GENERATED by scripts/handoff.py — do not hand-edit -->"`.

**The row-width rule** — `scripts/board.py:35-37,90-97`, verbatim:

```python
MAX_ROW = 190

def _cap(row: str, width: int = MAX_ROW) -> str:
    """Cap a rendered table row at ``width`` chars, truncating the content with an ellipsis
    while preserving the trailing ` |` cell border (owner ≤190 rule)."""
    if len(row) <= width:
        return row
    tail = " |"
    keep = width - len(tail) - 1  # room for the ellipsis
    return row[:keep].rstrip() + "…" + tail
```

**Reusable scan surface from `board`** (import, do not re-derive) —
`scripts/board.py:134,158,185,201,216,227,248,416`:

```python
def _scan_manifests(root: Path) -> dict[str, Track]: ...
def _attach_plans(root: Path, tracks: dict[str, Track]) -> list[str]: ...
def _attach_notes(root: Path, tracks: dict[str, Track]) -> list[str]: ...
def _scan_deskchecks(root: Path) -> list[DeskCheck]: ...
def plan_phase(status: str) -> str: ...
def track_phase(t: Track, dcs: list[DeskCheck]) -> str: ...
def is_owed(t: Track, dcs: list[DeskCheck]) -> bool: ...
def _build(root: Path) -> tuple[dict[str, Track], list[DeskCheck], list[str]]: ...
```

**The read-only queue open** — the posture to copy, `ops/lifecycle/snapshot.py:334-338`:

```python
    if not path.exists():
        return _EMPTY_QUEUE_STATS
    ...
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
```

Two properties are load-bearing and must both hold in `handoff.py`: the `mode=ro` URI
(so the generator can **never** create or mutate `queue.sqlite`), and missing-file-is-a-
value-not-an-exception.

**The generator contract (pinned from note §2.9 — this is the spec, not a pointer):**

```
scripts/handoff.py --role orchestrator --write   # writes docs/roles/orchestrator/handoff.md
scripts/handoff.py --role orchestrator --check   # regenerate to temp, byte-compare; exit 0 == identical
scripts/handoff.py --role orchestrator --json    # the structured answer, to stdout
scripts/handoff.py --track <slug>                # render to STDOUT only — no standing file
scripts/handoff.py --plan <id>                   # render to STDOUT only — no standing file
```

- **Inputs:** the artifact tree (plan / note / finding / owner-question front matter and
  statuses), `docs/roles/orchestrator/readings.md`, and — when present — a read-only open
  of `data/queue.sqlite`.
- **THE IDEMPOTENCE PIN (load-bearing, note §2.9):** the rendering is a pure function of
  the artifact tree **excluding itself**, and embeds **no HEAD sha and no generation
  timestamp**. Readings carry their own timestamps as data. Therefore
  regenerate-then-commit converges in one step: after the regen commit, regeneration is
  byte-identical. *A rendering that embedded HEAD or `now()` would have no fixed point and
  would re-arm any freshness gate forever.* This is why hashes leave the handoff: a tracked
  artifact never needs to cite its own tree's commits — `git log` is already that view.
- **Standing files exist for the `role` scope only.** `--track` and `--plan` render to
  stdout, so there is no fleet of generated files to go unregenerated.

**The MEASURED row shape (note §2.5):** append-only `(timestamp, command, one-line result)`
lines. The DERIVED pane renders the **latest reading per command with its age** — e.g.
`suite: 2 failed / 2276 passed (18h ago)` — so a stale reading advertises itself instead of
impersonating a current fact. MEASURED is never gated (note §2.10 check 3).

**The four-way split the artifacts encode (note §2.5):** DERIVED = pure function of the
tree, staleness impossible by construction → `handoff.md`. MEASURED = result of running
something, age displayed never hidden → `readings.md`. NARRATIVE = judgement no generator
can write, append-only → `journal.md`. RULES = durable discipline, **not handoff state at
all** — it lives in a skill/hook or it does not hold.

**The NARRATIVE purity rule (note §2.5) — the journal this plan creates must already obey
it:** narrative refers to artifacts by stable id (`bp-110`, `finding-0227`, `oq-0051`) and
**never states a machine-derivable value** — no commit hashes, no plan statuses, no counts,
no `path:line` into volatile code. The derivable value lives in the DERIVED pane; the id is
the join key.

**Scope identity (note §2.3):** a scope is a pair `(kind, id)` where `kind ∈ {role, plan,
track}` and the id **must resolve to an artifact already on disk** — never a free string.
`role` ids come from a closed registry, initially exactly `orchestrator` and `scheduler`;
`scheduler` gets **no narrative artifact** (the daemon writes no prose). `queue` is not a
scope kind. `topic` is not a fourth kind — it is the existing `track` coordinate.

## 7. Items

Ordered by blast radius: read-only sensing → new files → edits to an existing generator.

### Item 1 — the seat directory and its two hand-authored artifacts

- **Objective:** create `docs/roles/orchestrator/journal.md` and `readings.md` as tracked,
  append-only artifacts with a bootstrap entry each.
- **Files:** `docs/roles/orchestrator/journal.md`, `docs/roles/orchestrator/readings.md`
- **Acceptance test:** both files exist, are tracked (`git ls-files` lists them), and
  `journal.md`'s single entry carries the seven checkpoint sections (Status line /
  Completed / In-flight / Next action / Open questions / Context-manifest delta / Markers).
  A grep for word-bounded `[0-9a-f]{7,40}` over `journal.md` returns **zero** matches.
- **Falsifier:** the bootstrap entry cannot be written without naming a commit sha, a plan
  status, or a count — i.e. the purity rule (§6) is unsatisfiable for a real entry. If that
  is observed, the four-way split is wrong at its NARRATIVE boundary and the note's §2.5 is
  falsified; file a `spec-defect` finding and stop rather than writing an impure entry.
- **Invariant(s) it must not violate:** append-only (nothing is ever deleted or rewritten
  in place); NARRATIVE purity; **this is not the brief migration** — the live brief is not
  read, not copied, and not touched (that is bp-125).
- **Touches stored data?** No — new files only, no store, no queue write.
- **Parallelizable?** No.  **Depends on:** none.

### Item 2 — `scripts/handoff.py`: the deterministic rendering with the idempotence pin

- **Objective:** the generator renders `--role orchestrator` to `handoff.md`, and `--track`
  / `--plan` to stdout, as a pure function of the tree excluding itself.
- **Files:** `scripts/handoff.py`, `docs/roles/orchestrator/handoff.md`,
  `tests/unit/test_handoff.py`
- **Acceptance test:** `uv run scripts/handoff.py --role orchestrator --write` twice over an
  unchanged tree produces a **byte-identical** file both times; the committed file equals a
  fresh render; every rendered table row is ≤190 chars; the file carries the GENERATED
  banner; `grep -E '\b[0-9a-f]{7,40}\b'` over the rendering returns **zero** matches and the
  rendering contains no generation timestamp. `uv run pytest tests/unit/test_handoff.py`
  green.
- **Falsifier:** two consecutive renders over an unchanged tree differ. That is the
  idempotence pin broken, and it means clause (e′) (bp-126) could never be discharged — the
  gate would re-arm forever, which is precisely the defect this design exists to remove.
  Equally falsifying: a render that changes when only `handoff.md` itself changed (the
  "excluding itself" clause violated).
- **Invariant(s) it must not violate:** no HEAD sha, no `now()`, no wall-clock anywhere in
  the rendering; imports stdlib + `_lib` + `board` only, never `core`; `board.py --write`
  and `board.py --queue-count` behavior unchanged.
- **Touches stored data?** No.
- **Parallelizable?** No.  **Depends on:** Item 1.

### Item 3 — the queue pane: read-only, degrading to `queue: unavailable in this checkout`

- **Objective:** render queue depth / RUNNING rows / lease status when `data/queue.sqlite`
  is present, and a legible unavailable line when it is not.
- **Files:** `scripts/handoff.py`, `tests/unit/test_handoff.py`
- **Acceptance test:** with no `data/queue.sqlite`, the generator **exits 0** and the
  rendering contains `queue: unavailable in this checkout` (this is the mechanical half of
  F1c, note §2.11); with a fixture queue present, the pane renders its rows. A test asserts
  the connection string used is a `file:…?mode=ro` URI. Running the generator against a
  fixture directory that contains **no** `queue.sqlite` leaves no `queue.sqlite` behind
  afterwards.
- **Falsifier:** the generator raises, exits non-zero, or **creates** `data/queue.sqlite`
  when the file is absent. Creating it would breach the single-writer model
  `[GROUNDED scheduler/queue.py:17-18]` and is the exact regression
  `read_queue_stats` was written to fix `[GROUNDED ops/lifecycle/snapshot.py:324-327]`.
- **Invariant(s) it must not violate:** single-writer — the generator opens read-only and
  never creates, migrates, or mutates the queue; a missing queue is a **value**, never an
  exception; the queue is an *input*, never the substrate (note §2.6).
- **Touches stored data?** Reads `data/queue.sqlite` read-only when present; writes never.
  **Dry-run first:** before the first run against the real path, confirm on a copy that a
  `mode=ro` open of a **non-existent** path does not create it.
- **Parallelizable?** No.  **Depends on:** Item 2.
- **⚑ Parked dependency:** V3 (note §2.12) — see §11. Contention with the live
  supervisor's WAL is *expected* to be absent but is **not tested**; this item ships behind
  that parked decision and its re-entry condition.

### Item 4 — extend the coordinate check to findings and owner questions

- **Objective:** make the note's §2.3 claim true rather than assumed: a `track:` on a
  finding or an owner question is covered by the F-WF1 orphan check.
- **Files:** `scripts/board.py`, `tests/unit/test_board.py`
- **Acceptance test:** a fixture finding carrying `track: nonexistent-slug` appears in the
  board's "Coordinate check (orphans)" section; a finding with **no** `track:` key appears
  nowhere and is not an orphan; `uv run scripts/board.py --queue-count` and
  `uv run scripts/board.py --write` produce byte-identical output to before over an
  unchanged tree. `uv run pytest tests/unit/test_board.py` green.
- **Falsifier:** the existing board rendering changes for the current tree. No finding or
  owner question carries a `track:` today, so a correct extension is a **no-op on the real
  tree** — any diff in `docs/TRACKS.md` beyond the docstring is evidence the scan is
  over-reaching (e.g. treating an absent key as an orphan), which would flood the
  coordinate check with 232 false orphans.
- **Invariant(s) it must not violate:** `board.py`'s CLI contract is unchanged
  (`--queue-count` prints one integer; `--write` writes exactly the same two files);
  absent `track:` is normal, never an orphan; **no existing finding is back-filled** with a
  `track:` key by this plan.
- **Touches stored data?** No.
- **Parallelizable?** Yes — independent of Items 1–3.  **Depends on:** none.

### Item 5 — the structured answer (`--json`), the F2 compare's other half

- **Objective:** emit the generator's own answer to the drill's probe questions as JSON, so
  the behavioral drill (bp-127) has a mechanical ground truth to compare against.
- **Files:** `scripts/handoff.py`, `tests/unit/test_handoff.py`
- **Acceptance test:** `uv run scripts/handoff.py --role orchestrator --json` emits parseable
  JSON containing at least the fields `unit_in_flight` and `next_action`; the values are
  derived from the tree (not hand-set); two consecutive invocations over an unchanged tree
  emit byte-identical JSON.
- **Falsifier:** `next_action` cannot be derived from the tree at all and can only be
  hand-written. That is V1 landing early (note §2.12) — it means the F2 JSON compare will
  not survive contact, and bp-127's drill degrades to judge-only. **Record it in the journal
  and file a `spec-defect` finding rather than faking a derivable field**; the item still
  ships `unit_in_flight`, which is derivable.
- **Invariant(s) it must not violate:** the JSON is a *view of the same computation* as the
  rendering — it must never disagree with `handoff.md`; the idempotence pin applies to it
  identically (no timestamp, no sha).
- **Touches stored data?** No.
- **Parallelizable?** No.  **Depends on:** Item 2.

## 8. Math carried explicitly

N/A — no mathematical object is implemented. The generator is a deterministic rendering
function over front matter; the only formal property it carries is idempotence
(`render(tree) == render(tree)` and `render` is independent of its own output), which is
stated as the §6 idempotence pin and tested as Item 2's acceptance, not as a mathematical
object needing a field-guide entry.

## 9. Non-goals

- **No gate change.** Clause (e) in `.claude/hooks/_lib.py:892-920` is untouched and keeps
  governing. Clause (e′) is bp-126.
- **No retirement.** `.claude/state/resume-brief.md` and `docs/templates/resume-brief.md`
  both survive this plan intact; `session-brief.sh` still auto-surfaces the brief.
- **No migration.** The live brief's content is not read, classified, or moved here. That
  is bp-125, and it is a separate plan partly because it cannot run in a worktree at all
  (finding-0234 correction (2)).
- **No skill edits.** checkpoint and context-economy keep their current text until bp-125.
- **No amendment.** A10 to `dn-agent-workflow` is not attempted — it is unbuildable by any
  agent (finding-0233).
- **No back-fill.** No existing finding or owner question gains a `track:` key.
- **No `scheduler` seat artifacts.** The scheduler's state is already typed and durable in
  `data/queue.sqlite`; it gets **no narrative artifact** (note §2.4).
- **No new corpus-ingestion machinery.** Tracking the artifacts makes them visible to the
  existing repo ingest; nothing ingestion-specific is built (note §1.2).
- **No seat-occupancy lock.** The `claim()`/lease analogy is deliberately not built.
- **No PROGRESS.md redesign** and no change to `docs/inbox/owner-questions.md`.

## 10. Stop-and-raise conditions

- **The idempotence pin cannot be satisfied** (Item 2's falsifier fires) — STOP. Every
  downstream plan rests on it; a non-idempotent rendering makes clause (e′) unsatisfiable
  forever. File a `spec-defect` finding against the note's §2.9 and park.
- **The queue open creates or mutates `data/queue.sqlite`** — STOP immediately. That is a
  breach of the single-writer model, a blast-radius surprise on live data.
- **Item 4's no-op falsifier fires** (the real `docs/TRACKS.md` changes beyond the
  docstring) — STOP and re-derive; do not commit a board rendering churned by 232 false
  orphans.
- **A criterion needs a file outside §5** — file a `codebase` finding naming the file and
  the criterion; **never route around `scope-guard`**. A denial means narrow the scope or
  file a finding.
- **A blessing is implied** — never perform it. This plan stays `proposed` until the owner's
  hand moves it; the A10 amendment is likewise an owner act (finding-0233).
- **The note appears wrong on a further point** — file a finding, cite `path:line`, and
  continue. **Do not edit `docs/design-notes/role-state-and-scoped-handoff.md`**: it is
  ratified, and `scope-guard` denies the write pre-hoc
  `[GROUNDED .claude/hooks/_lib.py:435-441]`.
- **An owner-level question arises** — park that criterion with a re-entry condition and
  proceed with the rest. Never block on the owner.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| **V3 — read-only SQLite vs the live supervisor's WAL** (note §2.12) | Ship the read-only pane; document that non-contention is **expected, not tested** ("expected" is not a test — the note says so). | (a) Test it now — needs a live supervisor under load in CI, which no harness provides; (b) drop the pane — loses the note's whole "queue as input" ruling. | A single observed `SQLITE_BUSY` / lock error from the generator, **or** a supervisor stall coincident with a generator run. Prerequisite: the daemon running under real load while the generator is invoked. Until then the pane ships and the risk is named here, not hidden. |
| **Generator home: sibling script vs `board.py` subcommand** | Sibling `scripts/handoff.py` importing `board` (§3 Q1). | A `board.py` subcommand — rejected: `board.py`'s `--write` writes both board files unconditionally `[scripts/board.py:443-445]` and its CLI is substring matching, not argparse, so a shared `--write` would be ambiguous across two views with different cadences. | A third derived view needing the same scan functions, at which point the shared scan machinery earns extraction into a module both import. |
| **Reuse `ops.lifecycle.snapshot.read_queue_stats` vs an inline read** | Inline read in `handoff.py`, matching the `mode=ro` posture (§3 Q5). | Importing `ops.lifecycle` — rejected for now: both sibling scripts import stdlib + `_lib` only, and no artifact rules on whether `ops` is inside that boundary. | The inline read exceeding ~15 lines, **or** a second workflow script needing queue stats. Prerequisite: a `codebase` finding recording which. |
| **Multi-track membership (`track:` list-valued)** | Single-valued, per the board convention (note Parked decisions). | List-valued — rejected: changes the board's coordinate semantics for every artifact type at once. | A real artifact that genuinely belongs to two tracks, named in a finding. |
| **`readings.md` schema tightening** (typed commands, machine-parsed results) | Freeform `(timestamp, command, result)` lines. | A typed schema now — rejected: no consumer exists yet, so the schema would be guessed. | The command-center note wanting to consume readings mechanically. |

## 12. Dependency & ordering summary

**Within this plan:** Item 1 → Item 2 → {Item 3, Item 5}. Item 4 is independent of all of
them and may be done first or last (it touches a different file entirely). Blast-radius
phase order: Item 1 (new files, no behavior) → Item 2 (new script) → Item 3 (read-only
external input) → Item 5 (new output mode) → Item 4 (edit to a live generator; last
because it is the only item that can change an already-committed rendering).

**Across the family** (`dn-role-state-and-scoped-handoff` graduates to four plans):

```
bp-124 (this)  substrate + generator      — no gate change, no deletion
   │
   ├─→ bp-125  migration + skill contracts — MAIN CHECKOUT ONLY (finding-0234)
   │      │
   │      └─→ bp-126  the atomic cutover  — clause (e′) + re-point + retirement
   │                    │
   └────────────────────┴─→ bp-127  the executable falsifier (F1b, F1c, F2)
```

- **bp-125 depends on bp-124** — the seat artifacts must exist before content migrates into
  them.
- **bp-126 depends on bp-125** — the cutover deletes the brief, so the brief's content must
  already be migrated or it is destroyed. This edge is **load-bearing**, not stylistic.
- **bp-127 depends on bp-126** — F1b lints the *migrated* authoritative segment, and F1c
  asserts the post-cutover checkout.
- **⚑ Mutual exclusion on `.claude/hooks/**`:** this plan does not hold it. bp-126 does, and
  **no other builder may hold `.claude/hooks/**` while bp-126 runs** (note §3). Verified at
  graduation: no `ready` or `in-progress` plan (bp-111…bp-119, bp-123) carries
  `.claude/hooks/**`, `scripts/board.py`, or `session-brief.sh` in its `write_scope`
  `[GROUNDED, scanned 2026-07-26]`, so bp-124 is safe to run concurrently with the live ops
  wave.
- **Parallelizable with:** any ops-track plan (disjoint write scope). **Not** parallelizable
  with bp-125/126/127 — all four touch `docs/roles/**`.
