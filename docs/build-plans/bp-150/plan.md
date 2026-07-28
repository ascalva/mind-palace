---
type: build-plan
id: bp-150
track: workflow
status: proposed
design_ref:
  - docs/design-notes/dn-typed-workflow-registry.md
contract: builder
write_scope:
  - scripts/handoff.py
  - scripts/board.py
  - scripts/handoff_drill.py
  - ops/registry/**
  - docs/TRACKS.md
  - docs/DESKCHECK-QUEUE.md
  - docs/roles/orchestrator/handoff.md
  - tests/unit/test_handoff.py
  - tests/unit/test_handoff_purity.py
  - tests/unit/test_board.py
  - tests/integration/test_handoff_availability.py
  - tests/integration/test_handoff_gate.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 450k
  actual: null
depends_on:
  - bp-140
  - bp-142
  - bp-147
  - owner-amendment:role-state-and-scoped-handoff-note
parallelizable_with: []
created: 2026-07-27
updated: 2026-07-27
links:
  - docs/design-notes/dn-typed-workflow-registry.md
  - docs/design-notes/role-state-and-scoped-handoff.md
  - scripts/handoff.py
  - scripts/board.py
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — The derived views re-pointed: `board.py` and `handoff.py` derive from the registry

## 0. Mode & provenance

Investigation and planning produced this plan during `/graduate` of
`dn-typed-workflow-registry` (ratified 2026-07-27). It graduates the two **scripts** rows of
the note's §2.7 table, which license (v) names ("the skills/CLAUDE.md/**scripts** edits of
§2.7's table"). Implementation proceeds item-by-item on owner approval; the
`proposed → ready` blessing is the owner's alone.

## ⚑⚑ THIS PLAN IS BLOCKED ON AN OWNER AMENDMENT. IT IS NOT STARTABLE.

Note §2.7's table, verbatim:

> | `docs/design-notes/dn-role-state-and-scoped-handoff.md` | DERIVED rendering becomes a
> registry query; NARRATIVE/MEASURED unchanged — **owner-ratified amendment** |

That note is **ratified and agent-immutable**, and its §2.6 (D4) decides the opposite of what
this plan implements: *"the substrate: files as source; the queue as an input, never the
source."* Re-pointing the DERIVED rendering at a SQLite registry changes the source of truth
that D4 fixes. ⇒ **Before `/build bp-150` may run, the owner must have amended
`docs/design-notes/role-state-and-scoped-handoff.md`** (§2.6 D4, §2.9 D7's generator
contract, and §2.10 D8's clause-(e′) specification) to name the registry as the DERIVED
source. Verify by reading D4: if it still says "files as source", the amendment has not
landed and this plan does not start.

⚑ The note's live filename is `docs/design-notes/role-state-and-scoped-handoff.md` — the
registry note's table writes it as `dn-role-state-and-scoped-handoff.md`, which **does not
exist**. Record this as a `spec-fidelity` finding (§10); do not create a file to match.

## 1. Objective

Re-point the two derived views — `scripts/board.py`'s artifact scan and `scripts/handoff.py`'s
DERIVED pane — at registry queries, preserving both generators' idempotence pin and their
`--check` contracts byte-for-byte.

## 2. Context manifest

1. `docs/design-notes/dn-typed-workflow-registry.md` §2.7 (the table row: "`scripts/handoff.py`,
   `scripts/board.py` — re-pointed to derive from the registry (board.py's artifact scan is
   subsumed by a query; handoff.py keeps only live-pane rendering)"), §2.3 (the export pin),
   §2.6's clause (e′) row, §2.9 invariant 5, falsifier F2.
2. `docs/design-notes/role-state-and-scoped-handoff.md` — ⚑ **read §2.6 (D4), §2.9 (D7, the
   generator contract), §2.10 (D8, clause (e′) and the by-construction claim), §2.11 (the
   fresh-agent drill) to verify the amendment landed** (§0 precondition).
3. `scripts/handoff.py` — the whole file. Especially `:18-40` (THE IDEMPOTENCE PIN and its
   two consequences: the queue is an input not the tree; an age is a clock read), `:41-43`
   (the never-imports-`core` stance), `:57-61` (the `_lib`/`board` reuse), `:63`
   (`GENERATED_BANNER`), `:65-76` (the role registry, queue pointer strings).
4. `scripts/board.py` — the whole file. Especially `:1-45` (the derived-view stance,
   `MAX_ROW`, `GENERATED_BANNER`) and `:139-233` (the scanners this plan subsumes).
5. `.claude/hooks/_lib.py:748-819` (`_handoff_is_stale`) — ⚑ **clause (e′) shells out to
   `scripts/handoff.py --check`, and the docstring records exactly why** (finding-0236:
   tree-pure vs live rendering, and the (e) circularity that re-deriving the compare would
   reintroduce). **The `--check` contract must survive this plan unchanged**, because the
   hook is still live until bp-149.
6. `docs/build-plans/bp-142/plan.md` §6 — the export, the snapshot, the idempotence pin as
   this family implements it.
7. `docs/build-plans/bp-147/plan.md` §6.2 — `UnitState`, the fields a re-pointed view reads.
8. `scripts/handoff_drill.py:1-14` — the F2 fresh-agent drill for the seat, which consumes
   the generator's structured answer.
9. `docs/build-plans/bp-150/journal.md`.

### DRY audit — does `core/` (or the wider tree) already have this?

- **The scanners being subsumed?** `scripts/board.py:174-233` (`scan_plans`, `scan_notes`,
  `scan_findings`, `scan_oqs`, `_scan_deskchecks`). ⚑ **They are not deleted — they are
  demoted to a fallback.** Invariant 5 requires every read path to degrade to the tree, and
  the tree scan *is* that fallback (bp-141 §6.4 built the pattern). Deleting them would
  make the derived views fail closed on an unavailable store — F3.
- **The registry query?** `ops/registry/fold.py::query` / `UnitState` (bp-140, bp-147).
  Import it; do not write view-specific SQL.
- **The idempotence pin?** `scripts/handoff.py:18-27` — the canonical statement, already
  copied once by `ops/registry/export.py` (bp-142 §4). ⚑ **This plan must not create a third
  statement of the rule**; it keeps handoff.py's and cites it.
- **A byte-compare `--check`?** Both generators already have one. Preserve, do not rewrite.
- **`core/` audit:** `scripts/handoff.py:41-43` records "never imports `core`". ⚑ That stance
  is a **stdlib-purity** choice for a zero-dependency renderer, which the registry note
  §2.4.3 says explicitly "does not generalize" — but it also gives no reason to break it
  here. ⇒ These scripts import `ops.registry`, which imports `core.attestation.crypto` only
  on the signing path. Verify the import graph stays free of heavy core imports at render
  time (§3 Q4); if it does not, that is a real regression in a script the Stop gate shells
  out to.

## 3. Investigation & grounding

- **Q1 — what exactly moves?** §2.7's table row: "board.py's artifact scan is **subsumed by a
  query**; handoff.py **keeps only live-pane rendering**." So: `board.py` reads the registry
  instead of walking `docs/`; `handoff.py` stops re-deriving artifact state and renders the
  live pane (queue depth, ages) plus the registry's answer.
- **Q2 — what must NOT change?** Three contracts, each grounded:
  - **The idempotence pin** (`scripts/handoff.py:18-27`): "the *committed* rendering is a
    pure function of the artifact tree EXCLUDING ITSELF, and embeds **no HEAD sha and no
    generation timestamp**." After the re-point it becomes a pure function of the **registry
    snapshot** excluding itself — same property, new input. F2 still applies.
  - **`--check`'s byte-compare semantics** — clause (e′) shells out to it (`_lib.py:748-819`)
    and `journal-gate` is still live until bp-149.
  - **The tree-pure / live split** (`scripts/handoff.py:25-36`): `--write`/`--check`/`--json`
    render TREE-PURE; a bare `--role` renders LIVE. finding-0236's whole point is that
    comparing against the tree-pure render keeps the gate computed off the **work**, not off
    the **daemon**. A registry read must land on the tree-pure side only if the registry is
    itself work-driven — which it is (events are appended by work) — but the **queue** stays
    an input, never the source (role-state note D4's surviving half).
- **Q3 — availability.** `scripts/handoff.py:29-36` already establishes the posture: "no
  queue file is a VALUE (`queue: unavailable in this checkout`), never an exception." ⇒ An
  unavailable **registry** must be the same: a value, with the fallback to the tree scan, and
  the rendering says which source it used. `tests/integration/test_handoff_availability.py`
  exists precisely to pin this and is in `write_scope`.
- **Q4 — import cost.** `handoff.py` is shelled out to by the Stop gate on every session
  close. If importing `ops.registry` transitively drags in `cryptography`, `numpy`, or
  LanceDB, the gate gets slower on every close. ⇒ Verify the import graph
  (`python -X importtime`) and, if needed, import the signing path lazily. **The code does
  not settle this today** — measure, do not assume.
- **Q5 — the generated outputs.** `docs/TRACKS.md`, `docs/DESKCHECK-QUEUE.md`, and
  `docs/roles/orchestrator/handoff.md` are generated (`GENERATED_BANNER`,
  `scripts/board.py:45`, `scripts/handoff.py:63`). Re-pointing regenerates them, and the
  regenerated bytes must be committed or the freshness gate is armed. They are in
  `write_scope` for that reason. ⚑ **If the re-point changes their bytes at all, that is a
  result to inspect, not to accept** — a pure re-point of the *source* with the same data
  should produce identical output. A diff means the registry and the tree disagree, which is
  bp-143's ratchet's business.
- **Q6 — the fresh-agent drill.** `scripts/handoff_drill.py` "hands a **scope bundle and
  nothing else** to a history-less, tool-less agent … and compares its answers to the
  generator's own structured answer." After the re-point, the generator's structured answer
  comes from the registry, so the drill exercises the new path for free. Keep it working;
  it is the seat-level analogue of F6.
- **Q7 — filename discrepancy.** `docs/design-notes/dn-role-state-and-scoped-handoff.md`
  (as §2.7's table and the registry note's `links` write it) does not exist; the file is
  `docs/design-notes/role-state-and-scoped-handoff.md`. Verified by `ls` this pass. File a
  `spec-fidelity` finding; do not create a file.

**Additional risks or questions surfaced during reading:**

- This plan touches the two scripts the Stop gate and the session brief depend on, while
  those hooks are still live. A bug here blocks every session close in the repo. Every item
  must be verified by actually running the generator and the gate, not only by unit tests.
- `board.py`'s scanners double as the recovery-import inputs (bp-141/143). Demoting them to a
  fallback must not change their signatures — three consumers rely on them.

## 4. Reconciliation

- `scripts/handoff.py:18-40` (THE IDEMPOTENCE PIN and its two consequences) → ⚑ **banner:
  correction**, minimal. The pin's *input* changes from "the artifact tree excluding itself"
  to "the registry snapshot excluding itself"; the *property* is unchanged. The banner names
  this plan, the registry note §2.7 and §2.3, and states that the queue remains an input and
  an age remains a clock read. **Do not rewrite the pin's argument** — it is the canonical
  statement and `ops/registry/export.py` already cites it.
- `scripts/handoff.py:38-43` ("Front-matter parsing is REUSED from `.claude/hooks/_lib.py`
  and the artifact scanners from `scripts/board.py` … and never imports `core`") →
  **banner: correction.** The scanners become the *fallback* path; the module now also
  imports `ops.registry`. The banner must state that the never-imports-`core` line is
  superseded in letter (an indirect import exists on the signing path only) and preserved in
  spirit (render-time imports stay light — §3 Q4), citing the registry note §2.4.3's
  directionality ruling.
- `scripts/board.py:1-22` (the derived-view stance and the `--write` contract) →
  **banner: correction**: the artifact scan is subsumed by a registry query, with the tree
  scan retained as the invariant-5 fallback.
- `tests/unit/test_handoff_purity.py`, `tests/unit/test_board.py`,
  `tests/unit/test_handoff.py`, `tests/integration/test_handoff_availability.py` →
  **banner: correction** where an assertion pins the tree as the source. Each changed
  assertion carries a comment naming this plan and what replaced it. ⚑ **Purity assertions
  must be strengthened, not weakened** — the pin still holds, over a new input.
- `docs/design-notes/role-state-and-scoped-handoff.md` → ⚑ **owner-ratified amendment, NOT
  this plan's edit.** It is a precondition (§0).

## 5. Write scope

- `scripts/board.py` — registry query as the primary source; tree scan retained as fallback;
  scanner signatures unchanged.
- `scripts/handoff.py` — DERIVED pane from the registry; live pane unchanged; the pin, the
  tree-pure/live split, and `--check` preserved.
- `scripts/handoff_drill.py` — kept working against the new structured answer.
- `ops/registry/**` — any query shape the views need (e.g. a board-oriented projection), so
  the views never write view-specific SQL.
- `docs/TRACKS.md`, `docs/DESKCHECK-QUEUE.md`, `docs/roles/orchestrator/handoff.md` — the
  regenerated committed outputs (§3 Q5).
- `tests/unit/test_board.py`, `tests/unit/test_handoff.py`, `tests/unit/test_handoff_purity.py`,
  `tests/integration/test_handoff_availability.py`, `tests/integration/test_handoff_gate.py`
  — carried because they pin the surface this plan moves (the retrofit rule).

⚑ The front-matter list is authoritative and every entry there is a bare glob (no inline
comments — the bp-066 footgun). If the prose above and the front matter ever disagree, the
front matter wins and a finding records the prose error.

**Deliberately OUT of scope:** `docs/design-notes/**` (the amendment is the owner's, and is a
precondition). `.claude/hooks/**` and `.claude/settings.json` (bp-149 — and clause (e′) is
still live during this plan, which is why `--check` must not change). `CLAUDE.md` and
`.claude/skills/**` (bp-148). `scripts/docket.py` (not named by §2.7's table). The foundation
denylist. `docs/PROGRESS.md` and every non-generated artifact.

## 6. Interfaces pinned inline

### 6.1 The idempotence pin (`scripts/handoff.py:18-27`, verbatim — preserved, input changed)

> ⚑ THE IDEMPOTENCE PIN (§2.9, load-bearing for the whole family). The *committed* rendering
> is a pure function of the artifact tree EXCLUDING ITSELF, and embeds **no HEAD sha and no
> generation timestamp**. So regenerate-then-commit converges in one step, and a freshness
> gate that compares the regeneration against the committed file can be discharged by one
> mechanical command instead of re-arming forever. A rendering that embedded HEAD or `now()`
> would have no fixed point — the defect this design exists to remove, mechanized.

### 6.2 The tree-pure / live split (`scripts/handoff.py:25-36`, verbatim — preserved)

> `--write` / `--check` / `--json` render in TREE-PURE mode while a bare `--role` renders LIVE
> (`_View.live`) … **The queue is an input, not the tree.** `data/queue.sqlite` is gitignored
> runtime state that a live supervisor mutates continuously … So the live queue pane is stdout
> only; the committed rendering carries a pointer to it. Availability degrades gracefully
> either way: no queue file is a VALUE (`queue: unavailable in this checkout`), never an
> exception. … **An age is a clock read.**

### 6.3 Clause (e′)'s contract with `handoff.py` (`.claude/hooks/_lib.py:50-53`, verbatim)

```python
# Clause (e′) check 1's positive staleness signature — the substring the generator renders when
# the committed handoff genuinely differs from a fresh render. Exported (not underscore-private)
# because it is a CONTRACT with `scripts/handoff.py`, and because the gate test asserts on it.
HANDOFF_STALE_SIGNATURE = f"{SEAT_ROLE}/handoff.md: STALE"
```

⚑ This string and `--check`'s exit-code semantics are a **contract with a live hook**. They
must survive this plan byte-identically.

### 6.4 The fallback rule (invariant 5, note §2.9(1), verbatim)

> **Reads never block.** Substrate-level (WAL, §2.8), plus a rule: every read path has a
> fallback to the *export* — the working tree's certified frontmatter is a complete,
> always-readable projection of current state. A reader that cannot open the store reads the
> tree and says so.

⇒ `board.py` and `handoff.py` keep their tree scanners as the fallback and **say which
source they used**. The committed rendering must be **identical** under either source when
the two agree — otherwise the pin has two fixed points, which is no fixed point.

### 6.5 The registry read (bp-147 §6.2, verbatim — the fields the views consume)

```python
@dataclass(frozen=True)
class UnitState:
    unit_ref: str
    status: str
    open_criteria: list[str]
    parked: list[tuple[str, str]]
    last_landed_commit: str | None
    linked_findings: list[str]
    active_in_checkout: str | None
    judgement_entry_at: str | None
```

## 7. Items

### Item 50 — verify the precondition; measure the import cost

- **Objective:** prove the role-state amendment landed, and measure what importing
  `ops.registry` costs a generator the Stop gate shells out to.
- **Files:** `tests/unit/test_handoff_purity.py` (a recorded measurement helper is fine here;
  no production file changes yet)
- **Acceptance test:** a recorded reading of `role-state-and-scoped-handoff.md` §2.6 D4
  showing the registry named as the DERIVED source; plus `python -X importtime -c "import
  ops.registry"` timings recorded in the journal, with a stated budget.
- **Falsifier:** ⚑ **the amendment has not landed** (§0). Then this plan is not startable —
  stop, report, change nothing. Secondarily: the import cost exceeds the stated budget, in
  which case the signing path must be lazily imported before any item proceeds.
- **Invariant(s) it must not violate:** no ratified note is edited, ever.
- **Touches stored data?** No.
- **Parallelizable?** No.  **Depends on:** all of `depends_on`.

### Item 51 — `board.py`: registry query primary, tree scan fallback

- **Objective:** the board derives from the registry, degrading to the tree scan, with
  identical output either way.
- **Files:** `scripts/board.py`, `ops/registry/**`, `tests/unit/test_board.py`
- **Acceptance test:** `uv run scripts/board.py --write` produces `docs/TRACKS.md` and
  `docs/DESKCHECK-QUEUE.md` **byte-identical** to the committed versions when the registry
  and the tree agree; with `OUROBOROS_REGISTRY` pointed at an unreadable path, the same
  command produces the **same bytes** via the fallback and reports the source used;
  `uv run pytest tests/unit/test_board.py -q` green.
- **Falsifier:** ⚑ the two sources produce **different bytes**. The pin then has two fixed
  points, which is no fixed point, and the freshness gate re-arms depending on store
  availability — the exact defect §2.7's diagnosis describes, resurrected.
- **Invariant(s) it must not violate:** invariant 5 (reads degrade, never fail closed); the
  scanner signatures are unchanged (three consumers).
- **Touches stored data?** Yes — regenerates two committed files. Dry-run first (bare
  `scripts/board.py` renders to stdout).
- **Parallelizable?** No.  **Depends on:** Item 50.

### Item 52 — `handoff.py`: DERIVED from the registry, pin and `--check` preserved

- **Objective:** the seat's DERIVED pane comes from the registry; the pin, the tree-pure/live
  split, and `--check`'s contract are untouched.
- **Files:** `scripts/handoff.py`, `docs/roles/orchestrator/handoff.md`,
  `tests/unit/test_handoff.py`, `tests/unit/test_handoff_purity.py`
- **Acceptance test:** `uv run scripts/handoff.py --role orchestrator --check` exits 0 against
  the committed file; two consecutive `--write` runs leave the tree unchanged; the purity
  test still proves no HEAD sha, no wall clock, no queue read in the committed rendering;
  `bash .claude/hooks/journal-gate.sh --standalone` (clause e′) behaves exactly as before —
  and `HANDOFF_STALE_SIGNATURE` still appears when the file genuinely differs.
- **Falsifier:** ⚑ **clause (e′) breaks or changes behavior.** `journal-gate` is still live
  (bp-149 has not run), so a changed `--check` contract blocks every session close in the
  repo. Prove it end-to-end against a fixture repo, not by reading the code.
  ⚑ **Side-effect audit before that demo run** (build-plan skill, warrant finding-0039 /
  oq-0017): `cmd_stop_audit` appends a marker line to a journal on the HOOK-FAILURE path —
  run against a fixture repo root, never the real worktree. Record the audit.
- **Invariant(s) it must not violate:** the idempotence pin; the tree-pure/live split; the
  queue stays an input, never the source; an age stays a clock read (live pane only).
- **Touches stored data?** Yes — regenerates the committed handoff. Dry-run first.
- **Parallelizable?** No.  **Depends on:** Item 51.

### Item 53 — availability, and the fresh-agent drill

- **Objective:** an unavailable registry degrades gracefully and says so; the seat drill still
  passes.
- **Files:** `scripts/handoff_drill.py`, `tests/integration/test_handoff_availability.py`,
  `tests/integration/test_handoff_gate.py`
- **Acceptance test:** with the registry unreadable **and** with it locked by a second
  process, `--role orchestrator` renders, names the fallback source, and never raises;
  `uv run scripts/handoff_drill.py --verify-isolation` passes; the gate test is green.
- **Falsifier:** ⚑ **F3 (the new deadlock)** at the view layer — "any read blocks on the
  store, or an outage prevents an agent from continuing ordinary work." A generator the Stop
  gate shells out to that hangs on a locked registry would wedge every session close, which
  is precisely the hook defect this design exists to remove, reproduced.
- **Invariant(s) it must not violate:** invariant 5; the drill's isolation property.
- **Touches stored data?** No.
- **Parallelizable?** Yes.  **Depends on:** Item 52.

## 8. Math carried explicitly

N/A — no mathematical object implemented. The idempotence pin is a fixed-point property of a
rendering function; it earns its place through Items 51/52's falsifiers, and its canonical
statement already lives at `scripts/handoff.py:18-27`.

## 9. Non-goals

- ⚑ **No design-note edit.** The role-state amendment is the owner's and is a precondition.
- ⚑ **No hook change.** `journal-gate` clause (e′) is still live and its contract with
  `handoff.py --check` must survive byte-identically. bp-149 retires it, later.
- **No deletion of the tree scanners** — they are the invariant-5 fallback and the
  recovery-import inputs (bp-141/143). Signatures unchanged.
- **No new statement of the idempotence pin** — cite the one at `scripts/handoff.py:18-27`.
- **No `scripts/docket.py` change** — not named by §2.7's table.
- **No skills, `CLAUDE.md`, or template edit** — bp-148.
- **No file created to match a wrong path** in the note's table (§3 Q7) — file the finding.
- **No new dependency.**

## 10. Stop-and-raise conditions

- ⚑ **The role-state amendment has not landed** (§0, Item 50) — stop, report, change nothing.
- The import cost of `ops.registry` exceeds the stated budget (§3 Q4) and cannot be fixed by
  lazy imports — park the affected items and report; slowing every session close is not an
  acceptable side effect of a view re-point.
- Registry-sourced and tree-sourced renderings differ (Item 51's falsifier) — stop; that is
  bp-143's ratchet's business, and re-pointing on divergent data would hide it.
- Clause (e′) behavior changes at all (Item 52's falsifier) — revert immediately.
- The filename discrepancy (§3 Q7) — file a `spec-fidelity` finding and continue.
- Any blessing this plan would have to perform — it must not.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| Tree scanners after the re-point | **retained as the invariant-5 fallback**, signatures unchanged | deleting them — the views would fail closed on an unavailable store (F3) and bp-141/143 would lose their import inputs | The export becomes the sole certified fallback and the scanners have no consumer |
| `ops.registry` import cost in a hot-path script | measured against a stated budget; lazy-import the signing path if needed | ignoring it — `handoff.py` is shelled out to on every session close by a live hook | The measurement exceeds budget; prerequisite: Item 50's timings |
| `scripts/docket.py` | untouched — not named by §2.7's table | re-pointing it too — scope creep into a file the design did not name | A build wave shows it re-deriving state the registry owns |
| Which source the committed rendering names | the rendering states its source **only in the live pane**, never in the committed bytes | putting it in the committed bytes — it would vary with store availability and break the pin | The owner wants provenance in the committed file; prerequisite: a way to keep it constant |

## 12. Dependency & ordering summary

**Within the plan.** Item 50 (verify the precondition; measure; change nothing) → Item 51
(`board.py`, regenerates two committed files) → Item 52 (`handoff.py`, regenerates one and
touches a live hook's contract) → Item 53 (availability + drill). Blast radius rises through
the plan and peaks at Item 52, which is the only item that can break every session close in
the repo — hence its end-to-end falsifier against a fixture repo.

**Across plans.** `depends_on` carries three plan ids **and one owner amendment**:
`owner-amendment:role-state-and-scoped-handoff-note`
(`docs/design-notes/role-state-and-scoped-handoff.md` §2.6 D4, §2.9 D7, §2.10 D8) — an owner
hand edit to a ratified note that no agent performs. Until it lands this plan is not
startable. **bp-149 depends on this plan**: retiring `journal-gate` means retiring clause
(e′), and (e′)'s DERIVED half only moves once these two generators derive from the registry.
`parallelizable_with: []` — it shares `ops/registry/**` with the rest of the family and
touches generators every session depends on. `bp-138`/`bp-139` are independent of this whole
family (note §3(5)).
