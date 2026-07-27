---
type: build-plan
id: bp-135
track: workflow
status: ready
design_ref:
  - docs/design-notes/dn-autopilot-and-delegated-blessing.md
contract: builder
write_scope:
  - docs/templates/audit-record.md
  - scripts/audit_record.py
  - tests/unit/test_audit_record.py
  - scripts/board.py
  - tests/unit/test_board.py
  - docs/TRACKS.md
  - docs/DESKCHECK-QUEUE.md
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 200k
  actual: null
depends_on: []
parallelizable_with: [bp-136, bp-137]
created: 2026-07-27
updated: 2026-07-27
links:
  - docs/build-plans/bp-120/plan.md
  - docs/findings/finding-0208.md
  - docs/audits/ops-wave-2026-07-25.md
  - docs/brainstorms/the-false-success-rule.md
re_entry: null
supersedes: null
superseded_by: null
warrant: docs/findings/finding-0208.md
---

# Build Plan — AP2: the reviewer's seat leaves a record — the audit pair as a typed artifact the board actually consumes

## 0. Mode & provenance

**Graduated from `dn-autopilot-and-delegated-blessing` §2.5 and §2.7(3)** (`status: ratified`).
Investigation and planning produced this; implementation proceeds item-by-item on owner approval.
The `proposed → ready` blessing is the owner's and is not performed in any session.

⚑ **The bootstrap wrinkle, stated plainly so no future reader thinks the gate was circumvented.**
This plan and its four siblings (`bp-136`–`bp-139`) build the machinery of *delegated* blessing.
They are themselves blessed **by the owner's hand, at the keyboard, in the ordinary way** — there
is no grant, no capsule, and no code for them, because the mechanism that would issue one does not
exist yet. That is not a loophole; it is the only possible order. After this wave the mechanism
carries itself; before it, nothing does.

⚑ **This plan is first in the wave by design, and the design note is why.** §2.3's grant removes
the owner from the reviewer seat. §2.5's audit pair, §2.6's halt list and §2.7's trail are what
occupy that seat in his place. A wave that shipped the grant first would delegate blessing with
**nothing standing where the owner stood**. The seat is filled here (`bp-135`), in `bp-136`
(the halt list) and in `bp-137` (eligibility); only then does `bp-138` build the grant's
cryptography — and its `depends_on` names all three so the order cannot be taken out of the plans
by a scheduling accident.

## 1. Objective

Gate A and Gate B verdicts become typed, machine-checkable audit records, and a track or
deskcheck whose `audit_refs` is empty or unresolvable reads "audit: owed" in **code** rather than
in prose.

## 2. Context manifest

Read in this order, whole files before citing:

1. `docs/design-notes/dn-autopilot-and-delegated-blessing.md` — **§2.5 whole** (the two gates,
   count, independence, cold-read, dissent semantics, "silence is not a pass"), **§2.7(3)** (audit
   records filed in `docs/audits/`, dissents additionally as findings, both named in the deskcheck
   entry's `audit_refs`), and **§2.9 invariant 7** (ambiguity resolves toward halting). The
   authority for everything below.
2. `docs/audits/ops-wave-2026-07-25.md` — the **only** existing machine-parseable audit record and
   the format this plan generalizes. Read its front matter (`:1-15`), its `## Verdicts` table
   (`:24-36`), and the two-axis ruling at `:175-177`.
3. `docs/findings/finding-0208.md` — `ftype: spec-defect`, `route: builder`, **open**: `board.py`'s
   `audit_refs` is parsed and discarded. This plan is its resolution and carries it as `warrant`.
   ⚑ Its cited line numbers (`scripts/board.py:123,142,150`) are **stale**; the live sites are
   `:128`, `:147`, `:155` (§3 Q2).
4. `scripts/board.py` — whole. The consumer being changed, and the front-matter-reuse precedent
   this plan follows (`:33-38`).
5. `tests/unit/test_board.py` — whole. 17 existing tests; four of them pin surfaces this plan
   moves (§5, §3 Q4).
6. `docs/brainstorms/the-false-success-rule.md:17-31` — the degenerate-input obligation. ⚑ Every
   item below delivers a **gate or audit**, so this rule applies to all four.
7. `.claude/skills/delegate/SKILL.md:41-60` — audit right-sizing (D2) and the sentence this plan
   makes true: *"an un-recorded audit reads as \"audit: owed\" on the board."*
8. `docs/templates/deskcheck.md` — read-only here. It declares `audit_refs` at `:7`; whether the
   field's authoritative home is the track manifest or the deskcheck record is **parked** (§11).

**DRY audit — does `core/` already have this?** (owner rule: the manifest must ask.) **No, and
nothing outside `core/` does either.** There is no audit-record type, no `docs/templates/audit-*`,
and no validator for any `docs/audits/` file — the directory holds six documents in five different
shapes (§3 Q1). What this plan must **not** re-derive is front-matter parsing: `scripts/board.py:33-38`
already reuses `_lib.parse_front_matter` / `_lib._normalize_status` from `.claude/hooks/_lib.py` by
`sys.path` insertion, with the comment *"Reuse the artifact front-matter machinery — never
re-derive it (plan §2 DRY audit)."* `scripts/audit_record.py` reuses the same, the same way.
`core/research/curate.py:73`'s `parse_frontmatter` is a **different** parser for research
manifests and is not reusable here (`board.py:17` forbids importing `core`, structurally asserted
by `tests/unit/test_board.py:282`).

## 3. Investigation & grounding

- **Q1 — is there an existing audit-record type or template to extend?** **No template; one
  instance.** `docs/templates/` holds seven files and none is an audit template (`build-plan.md`,
  `capsule.md`, `design-note.md`, `deskcheck.md`, `finding.md`, `intent-capsule.md`,
  `retrospective.md`). `docs/audits/` holds six documents, of which **only**
  `docs/audits/ops-wave-2026-07-25.md:1-15` carries YAML front matter; the other five open with an
  H1 plus bolded prose metadata (`docs/audits/prompt-integrity-audit.md:1-3` is representative).
  So this plan **creates** the type and generalizes the one machine-readable instance; it does not
  retrofit the other five (§9).
- **Q2 — what does `board.py` do with `audit_refs` today?** **Parses it and drops it.** Three
  sites: `scripts/board.py:128` (`audit_refs: list[str]` on the `Track` dataclass), `:147`
  (`audit = [str(x) for x in (fm.get("audit_refs") or []) if not _is_absent(x)]`), `:155`
  (`audit_refs=audit,`). It is never rendered, and neither `plan_phase` (`:298-306`),
  `track_phase` (`:309-327`) nor `is_owed` (`:330-335`) reads it. Populated in exactly one
  manifest, `docs/tracks/ops.md:7-8`; the other ten declare `audit_refs: []`.
- **Q3 — how is `docs/DESKCHECK-QUEUE.md` produced and parsed?** **Produced by `render_queue`
  (`scripts/board.py:445-494`), written at `:530`; parsed by nothing, anywhere.** It is pure
  output with a generated banner at line 1. Its single table's headers are, verbatim
  (`docs/DESKCHECK-QUEUE.md:11-12`):
  `| # | track | what to demo (working / true state) + surprise | verdict |`.
  Rows are emitted at `scripts/board.py:468-470`. ⚑ Consequence: adding an `audit` column is a
  change to the **renderer**, not to a parser, and `docs/DESKCHECK-QUEUE.md` must be in
  `write_scope` because the acceptance regenerates it (§5).
- **Q4 — which existing tests pin surfaces this plan moves?** Four, all in
  `tests/unit/test_board.py`: the idempotence test (`:99`), the ≤190-char row-width test (`:106`,
  against `MAX_ROW` at `scripts/board.py:42`), the queue owed/unowed membership test (`:133`), and
  `--write` emits both files + byte-equal re-render (`:212-226`). Adding a column to the queue
  table moves all four. `tests/unit/test_board.py:40` and `:238` construct `Track` with
  `audit_refs=[]`, so the dataclass signature is pinned there too. **All are carried in
  `write_scope`.**
- **Q5 — does a new `scripts/` file need registering anywhere for the gate legs to pass?** **No
  for mypy, yes for the import discipline.** `pyproject.toml:128` sets
  `files = ["core", "agents", "config", "eval", "ops", "scheduler", "scripts", "tests"]` — whole
  directories, so a new file is enrolled on creation, and CI runs `scripts` as a **Tier-2 hard
  floor: 0 errors** (`.github/workflows/ci.yml:71`). `scripts/check_imports.py` constrains `core/`
  and the worker boundary only (`scripts/check_imports.py:2-11`), **not** `scripts/`. The
  stdlib-only convention for repo tooling is enforced **per script by its own AST test** and by
  nothing else — `tests/unit/test_exhaust_report.py:163-179`, `tests/unit/test_capsule.py:414-431`.
  A new script gets no import discipline unless this plan writes its AST test. Item 6 writes it.
- **Q6 — what verdict vocabulary is authoritative?** The **two-axis** form ruled at
  `docs/audits/ops-wave-2026-07-25.md:175-177`: *"**Adopt the two-axis verdict:
  `artifact: clean|concerns|serious` × `record: accurate|overstated|misleading`.**"* ⚑ The
  ops-wave's own Verdicts table (`:28`) uses a value — `disclosed-partial` — that is **not** in
  that ruled vocabulary. The code does not settle which wins; this plan takes the **ruled
  vocabulary** as authoritative and treats the divergence as a documented drift in the one
  historical instance, which it does not edit (§4, §9).
- **Q7 — does a new skill or template need registering in `.claude/settings.json`?** **No.**
  `grep -n 'skill' .claude/settings.json` returns nothing; the eight directories under
  `.claude/skills/` are discovered by directory. (Relevant to `bp-136`, recorded here because the
  question was answered by the same grep.)

**Additional risks or questions surfaced during reading:**

⚑ **`docs/deskchecks/` contains only `README.md` — zero `dc-NNN` records exist.** So
`_scan_deskchecks` (`scripts/board.py:283-294`) returns `[]` today and **no track can compute to
`CLOSED`**. This means the "audit: present" path this plan adds has **no live data to exercise
it** on the real tree — every real track will render `audit: owed` except `ops`, the one manifest
with a populated `audit_refs` (`docs/tracks/ops.md:7-8`). The acceptance is therefore written
against **fixtures**, not against the live tree, and Item 8's falsifier is exactly the risk that a
fixture-only check is measuring the fixture (§7).

⚑ **`docs/tracks/workflow.md`'s stated scope does not cover autopilot.** Its `dod` lists WF-1/WF-2
(the board substrate and the deskcheck gate) and its prose scopes it to *"the tracks × phases board
and the deskcheck follow-through gate"*. The ratified note nevertheless declares `track: workflow`
(`dn-autopilot-and-delegated-blessing.md:4`, and its cross-references name
`docs/tracks/workflow.md` as *"the track manifest this note's `track:` coordinate names"*). This
plan therefore uses `track: workflow` — the note's own coordinate — and does **not** edit the
manifest to match. Parked (§11 row 1): a manifest whose DoD omits the work filed against it is a
board defect owed at deskcheck, not a scope-widening a builder should take.

## 4. Reconciliation

- `scripts/board.py:128,147,155` — `audit_refs` parsed into `Track.audit_refs` and never read →
  **[banner: correction]**. This is the defect `finding-0208` names and this plan's `warrant`.
  The correction is announced as one: `scripts/board.py`'s module docstring gains a line naming
  finding-0208 and stating that `audit_refs` is now **consumed** by `render_queue`, and the
  finding's `resolution` field is set to point at this plan. Not a quiet edit.
  ⚑ finding-0208's own line citations (`:123,142,150`) are stale by five lines; the builder
  updates them in the finding while resolving it, and says so in the journal.

- `docs/audits/ops-wave-2026-07-25.md:28` — the record-axis value `disclosed-partial`, which is
  absent from the vocabulary ruled at `:175-177` → **[cross-ref: extension]**. The historical
  audit is **not edited** (it is a record of what was found on a date, and rewriting a record to
  match a later schema is exactly the laundering A8 exists to prevent). Instead
  `docs/templates/audit-record.md` carries a one-line note that the vocabulary was ruled at
  `ops-wave-2026-07-25.md:175-177`, that the same document predates its own ruling in one cell,
  and that new records use the ruled set only.

- `docs/audits/ops-wave-2026-07-25.md:1-15` — the front matter this plan generalizes →
  **[cross-ref: extension]**. The new template's front matter is a **superset**, adding the fields
  §2.5/§2.7 require and the ops-wave predates (`gate`, `capsule_hash`, `auditor_context`,
  `unverified`, `dissent_finding`). The existing document is left exactly as it is; the template
  names it as the ancestor instance.

## 5. Write scope

Seven paths. Two new, five carried.

- `docs/templates/audit-record.md` — **new**. The typed record.
- `scripts/audit_record.py` — **new**. `validate` and `gates`, stdlib + `_lib` reuse only.
- `tests/unit/test_audit_record.py` — **new**. The falsifiers and the degenerate inputs, executable.
- `scripts/board.py` — **changed**. `audit_refs` becomes a consumed field (Item 8).
- `tests/unit/test_board.py` — **carried because it pins the surface this plan moves.** Four tests
  assert the queue table's exact shape and the `Track` constructor (§3 Q4); adding a column
  reddens them, and the builder must edit them. This is the retrofit pre-widening the graduate
  skill requires — without it the guard denies the builder a file its own acceptance needs.
- `docs/TRACKS.md` and `docs/DESKCHECK-QUEUE.md` — **carried because acceptance regenerates them.**
  `tests/unit/test_board.py:212-226` runs `--write`, which writes both (`scripts/board.py:530`),
  and any real `uv run scripts/board.py --write` after the renderer changes will rewrite both in
  the working tree. Both are `<!-- GENERATED … do not hand-edit -->` files: the builder regenerates
  them, never hand-edits them.

**Deliberately OUT of scope** — a denial here means file a finding, never widen by hand:

- `docs/audits/**` — the six historical documents are records of what was found on a date. This
  plan writes a *template* and a *validator*; it retrofits no existing audit (§4, §9).
- `docs/templates/deskcheck.md` and `docs/tracks/*.md` — whether `audit_refs`' authoritative home
  is the track manifest, the deskcheck record, or both is unsettled by `finding-0208:68-70` and is
  parked (§11 row 2). This plan consumes the field wherever `board.py` already reads it and moves
  neither declaration.
- `.claude/hooks/**` — no gate, no hook, no `settings.json`. The enforcement questions are
  `oq-0036`'s and are parked.
- `docs/design-notes/**` — ratified notes are agent-immutable (A8). The foundation denylist
  (`CONSTITUTION.md`, `eval/golden/**`, `eval/golden.py`) binds regardless of write_scope.

**Acceptance-reachability check** (findings 0177/0191/0204 — run before blessing):

| item | files its acceptance must modify | all in §5? |
|---|---|---|
| 5 | `docs/templates/audit-record.md`; `tests/unit/test_audit_record.py` | ✓ |
| 6 | `scripts/audit_record.py`; `tests/unit/test_audit_record.py` | ✓ |
| 7 | `scripts/audit_record.py`; `tests/unit/test_audit_record.py` | ✓ |
| 8 | `scripts/board.py`; `tests/unit/test_board.py`; `docs/TRACKS.md`; `docs/DESKCHECK-QUEUE.md` | ✓ |

Non-obvious targets checked, per the graduate skill's list: **no protocol member** is added to an
out-of-scope class; **no allowlist/registry enrollment** is required (`pyproject.toml:128` covers
`scripts/` by directory, `.claude/settings.json` registers no skills or templates — §3 Q5/Q7);
**tests outside this plan's own test file that ask the changed surface a question** were grepped —
`tests/unit/test_board.py` is the only one, and it is carried. `tests/unit/test_handoff.py` and
`tests/integration/test_handoff_gate.py` exercise `board` **indirectly** (via `scripts/handoff.py`,
which imports `board.scan_*` at `scripts/handoff.py:54-58`); neither asserts the queue table's
column shape, so neither is carried — ⚑ **if either reddens, that is a manifest defect: file a
`spec-fidelity` finding and stop, do not widen by hand.**

## 6. Interfaces pinned inline

**The two gates — §2.5's table, copied verbatim so the builder infers nothing:**

| gate | when | inputs (cold-read) | adversarial to | question |
|---|---|---|---|---|
| **A — intent fidelity** | pre-build, gates the `ready` flip | capsule + plan | intent drift; the 0203/0204 classes | "find how this plan exceeds or misreads the capsule" |
| **B — mechanism** | post-build, before terminal state | capsule + plan + diff | theatre; acceptance-passes-while-objective-fails | the ops-wave question, verbatim |

**The ops-wave question, verbatim** (`docs/audits/ops-wave-2026-07-25.md:21-22`):
*find a way the acceptance test passes while the objective fails.*

**The ruled verdict vocabulary** (`docs/audits/ops-wave-2026-07-25.md:175-177`, verbatim):
*"**Adopt the two-axis verdict: `artifact: clean|concerns|serious` × `record: accurate|overstated|misleading`.**"*

**§2.5's dissent semantics, verbatim** (`dn-autopilot-and-delegated-blessing.md:373-384`):

> **Gate A dissent:** pre-build, the plan is unblessed working material — the builder may revise
> and resubmit to a **fresh** Gate-A auditor. If the dissent is intent-level (the capsule itself is
> ambiguous or the ask is misunderstood), the run halts to the owner: remediating intent unattended
> is goal origination (non-goal 3).
> **Gate B dissent:** a mechanism CONCERNS permits **one** remediation cycle, re-audited by a fresh
> auditor — never the one who dissented, which would grade its own remediation ask. A second
> CONCERNS, or any intent-level CONCERNS (work exceeds the capsule), halts. Autopilot never
> adjudicates its own audit.
> **Verdicts are artifacts** (§2.7): a dissent is filed as a finding + audit record either way, so
> a halted run leaves the same trail a completed one does. Mutation-verification applies where a
> runnable acceptance exists; where none does, the auditor must state explicitly what it could not
> verify — silence is not a pass.

**The audit-record front matter — DEFINED HERE** (the note names the fields in prose; no schema
exists). Every key is required; `null` is never a legal value for a required key.

```yaml
---
type: audit
id: audit-<plan-id>-<gate>          # e.g. audit-bp-141-a  — unique, greppable
created: <YYYY-MM-DD>
gate: A | B                          # §2.5's two gates; exactly these two letters
plan: <bp-NNN>                       # the plan audited
capsule_hash: <64 lowercase hex>     # the capsule this run is bound to (invariant 3)
base: <sha>..<sha>                   # the diff range read (Gate B); <sha> alone for Gate A
method: cold-read                    # §2.5 independence; free text after the literal prefix
auditor_context: fresh-session       # fresh-session | <why not>  — §2.5 independence
verdict:
  artifact: clean | concerns | serious
  record: accurate | overstated | misleading
unverified:                          # REQUIRED list. Empty ONLY when every claim was run.
  - <what this auditor could NOT verify, and why>
dissent_finding: <finding-NNNN | null>   # non-null iff verdict.artifact != clean
links: []
---
```

**Body sections, all required** (mirroring the N/A discipline of the build-plan template):
`## What I read` · `## The adversarial question` (the verbatim question for this gate) ·
`## Findings` · `## What I could not verify` · `## Verdict`.

**The "silence is not a pass" rule, made mechanical** — §2.5's last clause becomes:
`verdict.artifact == "clean"` **requires** either at least one runnable acceptance actually
executed (recorded in the body) **or** a non-empty `unverified` list. A record claiming `clean`
with an empty `unverified` and no executed acceptance is **invalid**, not clean.

**CLI surface — DEFINED HERE:**

```
uv run scripts/audit_record.py validate <record-file>
    -> exit 0 iff the front matter is complete and legal AND every required body
       section is present AND the silence-is-not-a-pass rule holds
    -> exit 1 with one diagnostic line per violation, naming the field or the rule
uv run scripts/audit_record.py gates <plan-id> [--audits-dir <dir>]
    -> exit 0 iff EXACTLY the two records gate:A and gate:B exist for <plan-id>,
       both individually valid, with DISTINCT `id`s and the same `capsule_hash`
    -> exit 1 naming which gate is missing, duplicated, invalid, or hash-divergent
```

**Reuse, not re-derivation** (`scripts/board.py:33-38`, the pattern to copy verbatim):

```python
sys.path.insert(0, str(ROOT / ".claude" / "hooks"))
from _lib import _normalize_status, parse_front_matter  # type: ignore[import-not-found]  # noqa: E402
```

⚑ `_lib.parse_front_matter` is a **YAML subset** parser (`.claude/hooks/_lib.py:180-215`): scalars
and simple block/flow lists only. It does **not** parse the nested `verdict:` mapping above. The
builder therefore reads `verdict.artifact` / `verdict.record` as the **flat keys**
`verdict_artifact:` and `verdict_record:` in the front matter, or extends nothing and uses two
flat keys from the start. **Pinned decision: use two flat keys** — `verdict_artifact:` and
`verdict_record:` — and drop the nested form from the template above. Re-deriving a YAML parser to
support nesting is forbidden (CONVENTIONS.md:10, DRY).

**Board rendering — the exact change:** `render_queue` (`scripts/board.py:445-494`) gains one
column. New header, replacing `docs/DESKCHECK-QUEUE.md:11-12`:

```
| # | track | what to demo (working / true state) + surprise | audit | verdict |
|---|---|---|---|---|
```

The `audit` cell is `present` iff `Track.audit_refs` is non-empty **and every ref resolves to an
existing file under the repo root**; otherwise `owed`. Row width stays ≤ `MAX_ROW`
(`scripts/board.py:42`, 190) — `_cap` (`:95-102`) already enforces it and
`tests/unit/test_board.py:106` already tests it.

## 7. Items

Ordered by blast radius: inert template → pure validator → cross-artifact reader → the one item
that changes a live generated surface. Item numbering continues the family (`bp-120` used 1–4).

### Item 5 — `docs/templates/audit-record.md`, the typed record

- **Objective:** the audit record exists as a fillable template carrying exactly the §6 front
  matter and the five required body sections.
- **Files:** `docs/templates/audit-record.md`, `tests/unit/test_audit_record.py`
- **Acceptance test:** `uv run pytest tests/unit/test_audit_record.py -q` green on: the file
  exists and parses; `parse_front_matter` returns every §6 key; all five body headings present;
  the ops-wave ancestor and the `disclosed-partial` divergence are named in the template (§4).
- **Falsifier:** a genuine Gate-B audit of a real plan cannot be expressed in these fields without
  inventing one — the schema is modelling the ops-wave document rather than the note's two gates,
  and §6 is wrong. (Drill it: express `docs/audits/ops-wave-2026-07-25.md`'s bp-103 row in the
  template and name every field that has nowhere to go.)
- **Degenerate input (false-success rule):** the **unfilled template itself**. A validator that
  checks "every key is present" passes on a template whose every value is a `<placeholder>`.
  Item 6's acceptance asserts `validate` **reddens** on `docs/templates/audit-record.md` — exactly
  the boundary `capsule.py` already holds (`tests/unit/test_capsule.py:124`).
- **Invariant(s) it must not violate:** it edits no file under `docs/audits/` (§4). It is a
  template, not a record: it has no `id` that could be mistaken for a real audit.
- **Touches stored data?** No.
- **Parallelizable?** yes  **Depends on:** none

### Item 6 — `validate`: the schema, and "silence is not a pass"

- **Objective:** a malformed or vacuously-clean audit record is rejected mechanically rather than
  by reviewer attention.
- **Files:** `scripts/audit_record.py`, `tests/unit/test_audit_record.py`
- **Acceptance test:** `uv run pytest tests/unit/test_audit_record.py -q` green, covering `validate`
  exiting 1 with a naming diagnostic for each of: a missing required key; `gate: C`; a
  `verdict_artifact` outside `clean|concerns|serious`; a `verdict_record` outside
  `accurate|overstated|misleading`; a `capsule_hash` that is not 64 lowercase hex; a missing body
  section; `verdict_artifact: concerns` with `dissent_finding: null`; and — the silence rule —
  `verdict_artifact: clean` with `unverified: []` and no executed acceptance recorded. Exit 0 on a
  well-formed fixture.
- **Falsifier:** a record a human auditor would call *useless* passes `validate` — e.g. every
  required section present but each one word long. Then the schema is measuring presence, not
  content, and §2.5's "silence is not a pass" needs a different proxy than field occupancy.
- **Degenerate input (false-success rule):** **the unfilled template** (Item 5) and **a record
  whose `unverified` list contains the placeholder string**. Assert `validate` reddens on both. A
  validator that treats `<what this auditor could NOT verify, and why>` as a filled entry is
  passing the check without testing its claim.
- **⚑ Mutation obligation** (`the-false-success-rule.md:52-65`; `finding-0249` — both surviving
  mutants that wave were found by mutating and running, neither by reading): the silence rule is
  load-bearing, so the builder must run at least these three mutants against the new tests and
  record the result in the journal: (m1) drop the `unverified`-non-empty clause; (m2) invert the
  `dissent_finding` requirement; (m3) accept any string for `gate`. Every mutant must be caught by
  a named test; a surviving mutant is a test defect to fix, not a note to write.
- **Invariant(s) it must not violate:** stdlib + `_lib` reuse only — it imports no `core`, no
  `config`, and **no `os`, no `subprocess`** (the `finding-0207` discipline: absent those two
  there is no route to an environment variable or the `security` CLI). Asserted by an AST test in
  the same file, modelled on `tests/unit/test_capsule.py:414-431`.
- **Touches stored data?** No.
- **Parallelizable?** no  **Depends on:** Item 5

### Item 7 — `gates`: a run has exactly two records, from two auditors, on one capsule

- **Objective:** §2.5's *"minimum two audit passes per run, always distinct agent instances"*
  becomes a check rather than a hope.
- **Files:** `scripts/audit_record.py`, `tests/unit/test_audit_record.py`
- **Acceptance test:** against fixtures — exit 0 for a directory holding exactly one valid
  `gate: A` and one valid `gate: B` record for the plan, sharing a `capsule_hash` and carrying
  distinct `id`s; exit 1, naming the reason, for each of: only Gate A present; only Gate B
  present; two Gate-A records; the two records carrying **different** `capsule_hash` values (the
  plan was re-capsuled between gates — invariant 3 broken); a present-but-invalid record.
- **Falsifier:** `gates` returns 0 for a plan whose two records were written by the **same**
  auditor. Independence is §2.5's load-bearing property and `id` distinctness is a weak proxy for
  it; if the check cannot tell, say so in the record rather than implying it was checked. ⚑ The
  builder must state in the journal what `gates` does **not** prove — a file cannot testify to the
  session that wrote it.
- **Degenerate input (false-success rule):** **an empty audits directory.** A check phrased as
  "no record is invalid" or "all found records are clean" returns 0 over the empty set — passing
  without testing its claim, on the exact input that means *no audit happened at all*. Assert
  `gates` **reddens** on an empty directory, and on a directory holding records for a *different*
  plan id only.
- **Invariant(s) it must not violate:** read-only with respect to `docs/audits/` — this tool never
  writes a record. Invariant 7: an undetermined answer is a failure, never a pass.
- **Touches stored data?** No.
- **Parallelizable?** no  **Depends on:** Item 6

### Item 8 — `board.py` consumes `audit_refs` (resolves finding-0208)

- **Objective:** the board states "audit: owed" in code, so the delegate skill's sentence
  (`.claude/skills/delegate/SKILL.md:58-60`) becomes a claim some code makes.
- **Files:** `scripts/board.py`, `tests/unit/test_board.py`, `docs/TRACKS.md`,
  `docs/DESKCHECK-QUEUE.md`
- **Acceptance test:** `uv run pytest tests/unit/test_board.py -q` green with the four moved tests
  updated (§3 Q4) plus new ones: the queue table renders the §6 header; a track with
  `audit_refs: []` renders `owed`; a track whose refs all resolve renders `present`; rows stay
  ≤190 chars; `--write` is byte-idempotent on a second run. Then `uv run scripts/board.py --write`
  on the real tree regenerates `docs/TRACKS.md` and `docs/DESKCHECK-QUEUE.md` and `git diff` shows
  **only** the new column.
- **Falsifier:** every real track renders `owed` and none ever renders `present`, so the column
  carries no information on the live tree. ⚑ This is **expected today** and is the honest reading,
  not a bug: `docs/tracks/ops.md:7-8` is the only manifest with a populated `audit_refs` and
  `docs/deskchecks/` holds zero records (§3, additional risks). The falsifier fires only if `ops`
  *also* renders `owed` — which would mean the resolution check is broken, not that the data is
  sparse. The builder records the live census in the journal either way.
- **Degenerate input (false-success rule):** **`audit_refs: ["docs/audits/does-not-exist.md"]`.**
  A check phrased as "the list is non-empty" renders `present` for an audit that was never
  written — passing without testing its claim, and the failure mode is a board that reports an
  audit exists because someone typed a filename. Assert the cell reddens to `owed` on an
  unresolvable ref. (`CONSTITUTION.md` §III.1: *"A cited identifier that does not resolve is a
  failure."*)
- **⚑ Mutation obligation:** the resolution check is load-bearing — mutate it to `len(refs) > 0`
  and assert a named test reddens.
- **Invariant(s) it must not violate:** `board.py` remains derived-only and imports no `core`
  (`tests/unit/test_board.py:282`). `docs/TRACKS.md` and `docs/DESKCHECK-QUEUE.md` are
  **regenerated, never hand-edited** — both carry the generated banner.
- **Touches stored data?** No.
- **Parallelizable?** no  **Depends on:** Item 6

## 8. Math carried explicitly

`N/A — no mathematical object implemented.` The record is a schema and the board cell is a
predicate over file existence; neither is a measure, an estimator, or a geometric object. The
wave's one mathematical object — the HMAC commitment — is `bp-138` §8.

## 9. Non-goals

Explicitly NOT in this plan, so a builder does not helpfully overreach:

1. **No autopilot runs anything.** This plan builds the *record* the audit leaves, not the
   spawning of auditors, not the supervisor. Spawning is `bp-136`'s skill.
2. **No retrofit of the six existing `docs/audits/` documents.** They are records of what was
   found on a date; rewriting a record to satisfy a later schema is the laundering A8 exists to
   prevent (§4). New records only.
3. **No edit to `docs/templates/deskcheck.md` or any `docs/tracks/*.md`.** Where `audit_refs`
   authoritatively lives is unsettled (`finding-0208:68-70`) and parked (§11 row 2).
4. **No hook, no gate, no `.claude/**` change.** The Stop-gate questions are `oq-0036`'s.
5. **No grant, no capsule hashing, no secret, no HMAC** — `bp-138`, and it is the only plan in
   this wave that reasons about a secret at all.
6. **No `docs/tracks/workflow.md` DoD update** to mention autopilot, though its current DoD does
   not cover this work (§3). Parked (§11 row 1). [INFERENCE — that a track manifest's DoD is the
   owner's to widen at deskcheck rather than a builder's to edit mid-wave. If the owner would
   rather the manifest track its real membership continuously, that is a one-line follow-up.]
7. **No new `ftype`/route vocabulary work**, though `oq-0047` ruled ftype the routing axis
   (`docs/inbox/owner-questions.md:1653`) and nothing reads it. That implementation is its own
   plan; `bp-136` consumes the conservative reading §2.4 already licenses.

## 10. Stop-and-raise conditions

STOP and surface rather than proceed if:

- `tests/unit/test_handoff.py` or `tests/integration/test_handoff_gate.py` reddens — they exercise
  `board` indirectly and are **deliberately not** in `write_scope` (§5). That is a manifest defect:
  file a `spec-fidelity` finding, park the criterion, continue the rest. **Never widen the scope by
  hand and never route around a `scope-guard` denial**; a second denial on the same target means
  the plan is mis-scoped.
- the two-axis verdict vocabulary proves unable to express a real audit outcome (Item 5's
  falsifier) — that contradicts the ruling at `ops-wave-2026-07-25.md:175-177` and is a
  `spec-defect` routed to the orchestrator, not a value to quietly add.
- any criterion appears to need a file outside §5 — finding, park, continue.
- a `HOOK-FAILURE` line appears — enforcement did not apply. Rerun the named hook standalone
  (`bash .claude/hooks/<name>.sh --standalone …`), reconcile, and say so in the journal before
  continuing.
- **any change would put a blessing flip, a secret, or an MFA code within reach of this code.**
  Nothing in this plan touches any of the three. If an item appears to need one, that is not a
  design choice to make — stop and raise it.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| `docs/tracks/workflow.md`'s DoD does not cover autopilot, yet the ratified note declares `track: workflow` | Use the note's coordinate (`workflow`) and leave the manifest alone | *Mint `docs/tracks/autopilot.md`* — rejected: contradicts the ratified note's own `track:` field, and a coordinate the note does not name is a board orphan. *Edit the manifest's DoD* — rejected: a track's DoD is the deskcheck's yardstick; a builder widening it mid-wave moves the goalposts it will be judged against | The owner widens the manifest (or splits the track) at the workflow track's deskcheck |
| Whether `audit_refs`' authoritative home is the track manifest, the deskcheck record, or both | Consume it where `board.py` already reads it — the **track manifest** — and change no declaration | *Move it to the deskcheck record only* — rejected: `docs/deskchecks/` holds zero records, so the field would have no live carrier at all. *Populate both* — rejected: two homes drift, which is the DRY defect the owner grades as a defect not a nit | `finding-0208:68-70` is settled by the owner, or the first `dc-NNN` deskcheck record is written |
| Whether `gates` should prove auditor **independence** rather than merely distinct `id`s | Check distinct `id` + shared `capsule_hash`, and state in the record what is *not* proven | *Require a session/worktree fingerprint* — rejected: nothing in the repo records one, and inventing an unverifiable field is theatre. *Drop the check* — rejected: distinct ids catch the copy-paste case, which is the realistic failure | A run produces two records from one auditor and the check misses it — then the fingerprint earns its cost |
| Whether `validate` should be wired into CI | Not wired — a standalone tool the supervisor and the deskcheck call | *Add a CI leg* — rejected: `dn-autopilot-and-delegated-blessing.md:102` puts *"CI enforcement of the grant schema"* explicitly out of scope, and the same reasoning covers the audit schema | The mechanism has survived contact (§3(5) of the note) and the owner asks for it |

## 12. Dependency & ordering summary

**Within the plan:** Item 5 is independent. Items 6 → 7 (`gates` composes `validate`). Item 8
depends on Item 6 only for the resolution helper and is otherwise separable. Blast-radius order is
the item order: inert template → pure validator → read-only cross-artifact check → the one item
that rewrites two generated files. Nothing is irreversible; every effect is `git checkout`-able,
which is §2.8's reversibility property holding for this plan trivially.

**Across the wave** (`dn-autopilot-and-delegated-blessing`, minted 2026-07-27):

- **`bp-120` — AP1, the intent capsule.** `complete`. The only plan minted before today.
- **`bp-135` (this plan) — AP2, the audit pair as a record.** No dependencies. Fills the
  reviewer's seat.
- **`bp-136` — AP3, the halt list H1–H8 + the supervisor's operating skill.** `parallelizable_with`
  this plan: disjoint write_scope.
- **`bp-137` — AP4, the P1–P5 eligibility predicate.** `parallelizable_with` both: disjoint
  write_scope.
- **`bp-138` — AP5, the grant's pure core.** ⚑ `depends_on: [bp-135, bp-136, bp-137]` — **not a
  technical dependency; the ordering constraint made structural.** `bp-138` is pure cryptography
  and could compile on an empty tree. It is gated behind all three seat-filling plans so that the
  wave cannot be built in an order where grant machinery exists before the machinery that occupies
  the seat the grant vacates.
- **`bp-139` — AP6, the ON switch.** `depends_on: [bp-138]`.

**Un-minted and why** (the enumeration this note's own history proves is load-bearing):

- **AP-actor — the verifier as an actor** (secret source, invocation boundary, the `proposed→ready`
  flip, writing the grant record). **PARKED on `oq-0037`** (`finding-0207`: nothing mechanises
  *"the model never sees the secret"*), whose ruling is *"deferred to a Fable design pass"*, and
  now additionally on **`finding-0262`** (no bound on verification attempts). Not minted.
- **AP-posthoc — the Stop-gate/journal-gate grant-record rule.** **PARKED on `oq-0036`**
  (`finding-0206`: clause (c) has no committed-flip block to be an exception to, and cannot tell
  the owner's hand-flip from a forgery). Same Fable pass. Not minted.
- **AP-const — the one-sentence `CLAUDE.md:62` edit** (§3(2)). **PARKED on the owner's hand:**
  §3(1) amends `dn-agent-workflow`, which is `status: ratified` and therefore agent-immutable
  under A8, so that amendment is the owner's, not a build item — and the `CLAUDE.md` sentence
  points at it, so it must not land first. Not minted.

**Blessing-round recommendation** (the ordering constraint applied to the gate itself): bless
`bp-135`/`bp-136`/`bp-137` as one round; bless `bp-138`/`bp-139` only once the first three are
`complete`. `depends_on` already enforces the build order; staging the blessing means the seat is
demonstrably occupied before the grant's cryptography is even authorized to exist.
