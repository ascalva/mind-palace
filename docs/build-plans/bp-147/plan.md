---
type: build-plan
id: bp-147
track: workflow
status: proposed
design_ref:
  - docs/design-notes/dn-typed-workflow-registry.md
contract: builder
write_scope:
  - ops/registry/**
  - scripts/registry.py
  - tests/unit/test_registry_seal.py
  - tests/integration/test_registry_clause_parity.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 450k
  actual: null
depends_on: [bp-140, bp-142, bp-146]
parallelizable_with: [bp-144]
created: 2026-07-27
updated: 2026-07-27
links:
  - docs/design-notes/dn-typed-workflow-registry.md
  - docs/design-notes/agent-workflow.md
  - .claude/hooks/journal-gate.sh
  - .claude/skills/checkpoint/SKILL.md
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — The journal-gate clause map made real: typed seal, land-time judgement, unit state

## 0. Mode & provenance

Investigation and planning produced this plan during `/graduate` of
`dn-typed-workflow-registry` (ratified 2026-07-27). Like bp-146 it is a **capability half**
of license (iv): it builds the registry-side replacements for `journal-gate`'s six clauses
and the per-clause parity tests, and it **retires nothing**. Implementation proceeds
item-by-item on owner approval; the `proposed → ready` blessing is the owner's alone.

The note's invariant 8 is the reason this plan exists as a separate, unblocked unit: "A hook
is retired only after a registry-side test proves its guarantee's parity." The proof is
built here; the retirement is bp-149, which waits on the owner's amendments.

## 1. Objective

Implement each `journal-gate` clause as a registry-side guarantee — a typed seal event, a
land-time judgement requirement, unit-resident state, and a HEAD-keyed ratified content hash
— each with a parity test against the live hook.

## 2. Context manifest

1. `docs/design-notes/dn-typed-workflow-registry.md` §2.6 — **the journal-gate clause map
   table in full** (clauses a, b, b2, c, d, e′, f), the "honest loss in the (a)/(b) family",
   and why `compaction-marker` stays. Plus §2.7 (what the journal narrows to) and §2.9
   invariants 1 and 8, falsifier F4.
2. `.claude/hooks/journal-gate.sh` and `.claude/hooks/_lib.py:820-1089` (`cmd_stop_audit`) —
   ⚑ **the guarantees being replicated, read in full.** Every clause's exact condition and
   exact refusal message.
3. `.claude/hooks/_lib.py:724-747` (`_journal_tail_has_followthrough`) — clause (f) as it
   stands: "Header-presence only: the grep-class tooth (F-WF5's accepted residual — the
   block's completeness is the deskcheck's job, not this crude check's)." The note §2.6 says
   this becomes "a **typed field on the seal event** — submission refuses a seal without the
   five answers; grep upgraded to schema."
4. `.claude/skills/checkpoint/SKILL.md:63-83` — **the five follow-through questions,
   verbatim**, and the rule that the header must be exact.
5. `.claude/hooks/_lib.py:748-819` (`_handoff_is_stale`) + `_lib.py:40-53` (`SEAT_ROLE`,
   `HANDOFF_STALE_SIGNATURE`) — clause (e′), and the recorded reason it shells out to the one
   implementation rather than re-deriving the compare (finding-0236).
6. `.claude/hooks/_lib.py:316-336` (`active_plan_path`) — clause (d)'s substrate,
   `.claude/state/active-plan`.
7. `.claude/hooks/_lib.py:587-653` (`_blessing_in_diff`, `_untracked_blessing`) — clause (c).
8. `docs/build-plans/bp-146/plan.md` §6 — `land()`, `LandVerdict`, the enforcement level.
   Clauses (a) and (b) are land-time in the registry world, so they build on this.
9. `docs/design-notes/agent-workflow.md` §6 and §9 — the hook contract and the journal
   contract. ⚑ Read to know what parity means; **do not edit** (ratified, owner-amended).
10. `docs/build-plans/bp-147/journal.md`.

### DRY audit — does `core/` (or the wider tree) already have this?

- **Every clause's current implementation?** `.claude/hooks/_lib.py` — `cmd_stop_audit`
  (`:820`), `_journal_tail_has_followthrough` (`:724`), `_handoff_is_stale` (`:748`),
  `_blessing_in_diff` (`:587`), `_untracked_blessing` (`:632`), `_changed_files` (`:546`),
  `_diff_text_head` (`:567`), `git_show_head` (`:281`), `_head_status_of` (`:297`).
  ⚑ **The parity harness imports and runs these; it does not re-implement them.** Where a
  registry-side replacement needs the same primitive (e.g. `git_show_head` for clause b2),
  **import it** — the same rule bp-146 applies to `glob_match`.
- **Land-time scope admission?** `ops/registry/land.py` (bp-146). Clauses (a) and (b) attach
  to it; do not write a second diff-vs-scope check.
- **The derived-rendering compare for clause (e′)?** `scripts/handoff.py --check`, and
  `_lib.py:748-819` records at length *why* it shells out to that one implementation rather
  than re-deriving the compare (finding-0236: tree-pure vs live rendering). **The registry
  must respect that reasoning**: a registry query that answered "is the handoff stale" by
  re-deriving the render would reintroduce the (e) circularity. §3 Q4.
- **`core/` audit:** core owns nothing about journals, sessions, or git and must not.

## 3. Investigation & grounding

- **Q1 — what are the five follow-through answers, verbatim?** From
  `.claude/skills/checkpoint/SKILL.md:69-76`:

  ```
  ## Follow-through
  - **Built?** …
  - **Wired / delivered (or why dormant)?** …
  - **Does a consumer use it?** …
  - **Track state (what remains on this track)?** …
  - **Opened a new track/finding?** …
  ```

  Clause (f) today is header-presence only (`_lib.py:724-747`, "the grep-class tooth"). The
  note upgrades it: "submission refuses a seal without the five answers; grep upgraded to
  schema." ⇒ Five **required non-empty** typed fields (§6.1).
- **Q2 — does the registry judge *completeness* of the five answers?** No. The current
  implementation records that "the block's completeness is the deskcheck's job, not this
  crude check's" (`_lib.py:724-733`), and the owner's deskcheck-discipline rule says the
  owner has final say. ⇒ The schema requires each field to be **present and non-empty**; it
  does not grade them. Anything more would be a model judging its own work, which
  CONVENTIONS §Testing forbids ("the agent that made a change never grades it").
- **Q3 — where does the judgement entry requirement bite?** Note §2.6 clause (a): "land/seal
  submission *requires* the unit's judgement entry; unlanded staleness costs nothing landing
  won't demand." ⇒ `land()` and `seal` both require a judgement entry newer than the unit's
  last recorded commit. The honest loss is stated in the note and must be restated in
  `schema.md`: "Stop fires at session close; land-time admission fires at landing. A session
  that never lands can leave a dirty tree that no gate ever examined."
- **Q4 — can clause (e′) become a query?** ⚑ **Only its DERIVED half, and only after bp-148.**
  Note §2.6: "(e′) session-handoff freshness | handoff `--check` + seat-journal mtime |
  DERIVED rendering becomes a registry query; the NARRATIVE demand moves into land/seal like
  (a)." The DERIVED rendering is `scripts/handoff.py`, and **re-pointing it at the registry
  is bp-148's row of note §2.7's table**, not this plan's. ⇒ This plan implements the
  NARRATIVE half (the seat's judgement demand, folded into land/seal) and writes a parity
  test for it; the DERIVED half's parity test is **parked with a re-entry condition of
  bp-148 landing** (§11). Never block on it — park the criterion and continue (CLAUDE.md).
- **Q5 — clause (d), cross-checkout state bleed.** Note §2.6: "dissolves with its substrate:
  `active-plan` becomes a registry ref; no per-checkout state file remains." The substrate is
  `.claude/state/active-plan`, read by `_lib.py:316 active_plan_path` and written by
  `/build`. ⇒ This plan adds the registry-side representation (an `active` unit per checkout,
  queryable) **without removing the file** — `.claude/` is not in `write_scope` and `/build`
  still writes it. Removal is bp-149's.
- **Q6 — clause (c), uncommitted/untracked blessing flips.** Note §2.6: "unrepresentable: a
  blessing exists only as an accepted event; bytes in a file are not a blessing." ⇒ There is
  **nothing to build** for clause (c) beyond the parity *test* — bp-145's admission gate is
  what makes it unrepresentable, and bp-143's ratchet is what turns a hand-edited file into
  drift. Item 37's parity test asserts exactly that, and records that clause (c) is discharged
  by bp-143 + bp-145 rather than by this plan. Being honest about which plan discharges a
  clause is what makes bp-149's retirement decision auditable.
- **Q7 — clause (b2), ratified-note immutability.** Note §2.6: "ratified content hash is
  registry state; the ratchet reddens on divergence; laundering has no target." ⇒ The unit's
  `content_hash` for a ratified entity becomes registry state at its `→ratified` event
  (bp-144's `to_content_hash`, bp-145's admission). This plan adds the *check*: a landing
  whose diff touches a ratified entity whose body hash no longer matches the registry's is
  refused. Note the interaction with bp-144 §6.5: the hash covers **body only**, so a front
  matter rewrite by the export does not trip it. Verify that in the landed code.
- **Q8 — is `compaction-marker` in scope?** **No.** Note §2.6: "**kept — the one surviving
  hook.** … Compaction is a context-window event — invisible to any store, existing only at
  the instant it happens. A warrant cannot travel with a context window." No parity test is
  owed for it, and it must not be touched.
- **Q9 — retrofit surface.** This plan adds a required-field rule to `sealed` events, which
  bp-140 §6.6 currently accepts as given ("Accept and store the payload as given"). Any
  bp-140/bp-141 test submitting a `sealed` event without the five fields will start failing.
  `grep -rn "sealed" tests/` before starting; those files are **not** in this plan's
  `write_scope` (§10).

**Additional risks or questions surfaced during reading:**

- Six clauses is a lot for one session. The mitigation is that three of them (c, d, b2) are
  largely *assertions about other plans' work* rather than new machinery, and (e′)'s DERIVED
  half is parked. If the session runs long, the seam to stop at is after Item 37 — the
  parity harness — leaving Item 39's documentation for a resume.
- The parity harness runs the real Stop-gate audit. ⚑ **Side-effect audit (build-plan skill,
  warrant finding-0039 / oq-0017):** `cmd_stop_audit` (`_lib.py:820`) shells out to `git`
  (read-only: `status`, `diff`, `show`, `ls-files`) and to `scripts/handoff.py --check`
  (tree-pure per `_lib.py:748-760`, which explicitly does **not** read the live queue), and
  appends a marker line to a journal on the HOOK-FAILURE path. ⇒ **The journal-append path is
  a live write** and must be neutralized for demo runs by pointing the harness at a fixture
  repo root, not the real worktree. Do not skip this audit.

## 4. Reconciliation

- `ops/registry/store.py`'s `sealed` handling (bp-140 §6.6: "Accept and store the payload as
  given") → ⚑ **banner: correction.** A `sealed` event now **requires** the five
  follow-through fields, non-empty. The docstring gains a banner naming this plan, the note
  §2.6 clause (f) row, and `.claude/skills/checkpoint/SKILL.md:63-76` as the source of the
  five questions.
- `ops/registry/land.py` (bp-146) → **cross-ref: extension.** `land()` gains the clause (a)
  judgement requirement and the clause (b2) ratified-content check. The existing three arms
  are unchanged; the docstring lists the new ones with their clause letters so bp-149 can
  read the map directly off the code.
- `.claude/hooks/_lib.py` → **cross-ref only, in `ops/registry/schema.md`**, not in `_lib.py`
  itself (it is not in `write_scope`). `schema.md` gains a clause-by-clause table: clause →
  today's implementation (`path:line`) → registry-side replacement → parity test → **which
  plan discharges it**.
- **No design note is edited.** `agent-workflow.md` §6/§9 amendments are the owner's
  (note §3(1)), and this plan does not touch them.

## 5. Write scope

- `ops/registry/**` — `seal.py` (the typed seal event), edits to `land.py` (clauses a, b2),
  `fold.py` (unit state: open criteria, parked items with re-entry, last landed commit,
  linked findings, active-per-checkout), `store.py` (the `sealed` narrowing), `schema.md`.
- `scripts/registry.py` — `seal`, and `status` (the unit-state read that replaces the
  session-brief's orientation).
- `tests/unit/test_registry_seal.py` — the typed seal and unit-state fields.
- `tests/integration/test_registry_clause_parity.py` — the per-clause parity harness.

**Deliberately OUT of scope:** ⚑ **every hook and `.claude/settings.json`** — nothing is
retired, nothing unregistered. `.claude/state/**` (clause d's file stays; `/build` writes
it). `.claude/skills/**`, `CLAUDE.md`, `docs/templates/**` (the journal-narrowing edits are
bp-148's rows of note §2.7's table). `scripts/handoff.py`, `scripts/board.py` (bp-148).
`.claude/hooks/_lib.py` (imported, never edited). `docs/design-notes/**`. The foundation
denylist. bp-140/bp-141/bp-145 test files (§10).

**Retrofit check.** `grep -rn "sealed\|Follow-through" tests/ ops/` before starting — the
`sealed` narrowing (§3 Q9) is the one surface this plan moves. Any test outside this plan's
scope that submits a bare `sealed` event is a stop-and-raise, not a scope widening.

## 6. Interfaces pinned inline

### 6.1 The typed seal event (clause f: "grep upgraded to schema")

```python
# ops/registry/seal.py
@dataclass(frozen=True)
class FollowThrough:
    """The five questions, verbatim from .claude/skills/checkpoint/SKILL.md:69-76. Each is
    REQUIRED and must be non-empty. The registry does NOT grade the answers — completeness
    is the deskcheck's job (the _lib.py:724-733 posture, preserved), and 'built but NOT
    wired' is a valid, expected answer."""
    built: str                     # "Built?"
    wired_or_delivered: str        # "Wired / delivered (or why dormant)?"
    consumer_uses_it: str          # "Does a consumer use it?"
    track_state: str               # "Track state (what remains on this track)?"
    opened_new_track_or_finding: str  # "Opened a new track/finding?"

    def __post_init__(self) -> None:
        missing = [f for f in fields(self) if not str(getattr(self, f.name)).strip()]
        if missing:
            raise ValueError(
                "a seal requires all five follow-through answers (design note §2.6 clause "
                "(f); checkpoint skill): missing " + ", ".join(f.name for f in missing))
```

⚑ A `sealed` event without a `FollowThrough` is **rejected at submission** — this is the
"grep upgraded to schema" the note asks for. `_lib.py`'s grep tooth stays in place until
bp-149; the two coexist deliberately during the transition.

### 6.2 Unit state — what replaces the resume brief's derivable half

```python
# ops/registry/fold.py  (extended)
@dataclass(frozen=True)
class UnitState:
    """Note §2.7: 'each registry unit carries its open criteria, parked items with re-entry
    conditions, last landed commit, and linked findings — as typed fields, written at the
    semantic boundary where each fact is born (the moment of least depletion), not recalled
    at close.'"""
    unit_ref: str
    status: str
    open_criteria: list[str]                 # item ids not yet closed
    parked: list[tuple[str, str]]            # (what, re-entry condition) — re-entry REQUIRED
    last_landed_commit: str | None
    linked_findings: list[str]
    active_in_checkout: str | None           # clause (d): the ref, not a per-checkout file
    judgement_entry_at: str | None           # clause (a): when the last judgement entry landed
```

⚑ A `parked` item without a re-entry condition is **rejected** (bp-140 §6.6 already enforces
this on the `parked` event; `UnitState` never surfaces one without it). The greppable
"parked ⇒ re-entry" gate becomes a type.

### 6.3 The clause map, as code contracts

```python
# ops/registry/land.py  (extended — see §4 cross-ref)
# clause (a)  journal staleness vs last commit
#             -> land/seal REQUIRE a judgement entry newer than last_landed_commit.
#             HONEST LOSS (note §2.6): Stop fires at session close; this fires at landing.
#             A session that never lands can leave a dirty tree no gate examined. Backstops:
#             the CI ratchet (bp-142) and the disposability of an unlanded worktree.
# clause (b)  out-of-scope worktree changes   -> bp-146's land() arms (iii)/(iv). No new code.
# clause (b2) ratified-note immutability      -> a landing touching a ratified entity whose
#             BODY hash (bp-144 §6.5) differs from the registry's recorded content_hash is
#             refused. Front-matter rewrites by the export do NOT trip it, by construction.
# clause (c)  uncommitted/untracked blessing  -> UNREPRESENTABLE. Discharged by bp-145
#             (admission) + bp-143 (the ratchet turns a hand-edit into drift). Test only.
# clause (d)  cross-checkout state bleed      -> UnitState.active_in_checkout. The
#             .claude/state/active-plan FILE still exists and is still written by /build;
#             bp-149 removes it.
# clause (e') handoff freshness               -> NARRATIVE half here (judgement at land/seal);
#             DERIVED half PARKED until bp-148 re-points scripts/handoff.py (§11).
# clause (f)  seal follow-through             -> FollowThrough, §6.1.
```

### 6.4 What the note says about `compaction-marker` (verbatim — do not touch it)

> **`compaction-marker` — why it stays.** The owner's complaint is that hooks *deny on the
> hot path*. This hook never denies … Compaction is a context-window event — invisible to any
> store, existing only at the instant it happens. A warrant cannot travel with a context
> window. Retiring it buys nothing (it clogs nothing) and loses a real guarantee. One hook,
> read-only, fail-open, is the honest residue of the interception model.

### 6.5 CLI

```
uv run scripts/registry.py seal <unit-ref> --built ... --wired ... --consumer ... \
                                           --track-state ... --opened ...
uv run scripts/registry.py status [<unit-ref>]      # UnitState; the orientation read
uv run scripts/registry.py land <unit-ref>          # now also enforces clauses (a) and (b2)
```

### 6.6 Invariants

1. No event is ever mutated or deleted; corrections are events.
8. A hook is retired only after a registry-side test proves its guarantee's parity.
- **This plan's own:** every clause in §2.6's table is either (i) implemented with a parity
  test, or (ii) explicitly recorded as discharged by a named other plan, or (iii) explicitly
  parked with a re-entry condition. **No clause is silently dropped** — that is the note's
  own framing of the table as "the completeness checklist."

## 7. Items

### Item 34 — the typed seal

- **Objective:** `FollowThrough` + a `sealed` event that cannot be submitted without all five
  answers.
- **Files:** `ops/registry/seal.py`, `ops/registry/store.py`,
  `tests/unit/test_registry_seal.py`
- **Acceptance test:** `uv run pytest tests/unit/test_registry_seal.py -q` green: a seal with
  all five non-empty fields submits; each field blanked in turn raises with that field named;
  whitespace-only is treated as empty.
- **Falsifier:** the registry starts **grading** an answer (e.g. rejecting "built but NOT
  wired"). That is a model judging work, which CONVENTIONS §Testing forbids and which would
  make honest answers costlier than dishonest ones — the exact incentive the
  completion-claims-honesty rule exists to prevent.
- **Invariant(s) it must not violate:** invariant 1; the deskcheck remains the owner's.
- **Touches stored data?** Yes (registry store only).
- **Parallelizable?** No.  **Depends on:** bp-140.

### Item 35 — unit state: open criteria, parked items, last landed commit, findings

- **Objective:** `UnitState` as typed fields folded from events, replacing the resume brief's
  derivable half.
- **Files:** `ops/registry/fold.py`, `scripts/registry.py`,
  `tests/unit/test_registry_seal.py`
- **Acceptance test:** for a synthetic unit with three closed and two open criteria, one
  parked item, two findings and a landed commit, `uv run scripts/registry.py status <ref>`
  prints all of it; a `parked` without a re-entry condition never appears (it was rejected at
  submission).
- **Falsifier:** ⚑ the state is **cached** rather than folded — i.e. a field is written once
  and read back rather than derived from events. That would recreate the resume brief's
  structural defect one layer down ("a hand-maintained cache of a derivable fact", §2.7), and
  the whole diagnosis of §2.7 would apply to the replacement.
- **Invariant(s) it must not violate:** the fold is pure and read-only.
- **Touches stored data?** No (read path).
- **Parallelizable?** Yes.  **Depends on:** Item 34.

### Item 36 — clauses (a) and (b2) on `land()`

- **Objective:** `land()` refuses without a fresh judgement entry, and refuses a diff that
  moves a ratified entity's body.
- **Files:** `ops/registry/land.py`, `tests/unit/test_registry_seal.py`
- **Acceptance test:** a unit whose last judgement entry predates its last landed commit is
  refused with clause (a) named; a diff editing a ratified note's **body** is refused with
  clause (b2) named; a diff editing only its **front matter** is **admitted** (the export's
  job) — assert all three.
- **Falsifier:** ⚑ clause (b2) trips on an export-driven front-matter rewrite. The ratchet
  and the immutability check would then be in permanent conflict — every `export --write`
  would look like a laundering attempt — and bp-144 §6.5's body-only hash decision would be
  wrong.
- **Invariant(s) it must not violate:** ratified/superseded notes stay agent-immutable
  (A8); `land` writes nothing.
- **Touches stored data?** No.
- **Parallelizable?** No.  **Depends on:** Item 35, bp-146 Item 31.

### Item 37 — the per-clause parity harness

- **Objective:** for each clause the hook enforces, a test showing the registry side refuses
  the same case — or an explicit record of which other plan discharges it.
- **Files:** `tests/integration/test_registry_clause_parity.py`
- **Acceptance test:** `uv run pytest tests/integration/test_registry_clause_parity.py -q`
  green, with **one named test per clause** (a, b, b2, c, d, e′-narrative, f) — each either
  asserting agreement with `bash .claude/hooks/journal-gate.sh --standalone …` on a fixture
  repo, or `pytest.skip` with a reason naming the discharging plan (c → bp-143 + bp-145) or
  the parking condition (e′-derived → bp-148). A clause with **no** test and **no** recorded
  reason fails the suite.
- **Falsifier:** ⚑ **F4's precondition** — "any row of §2.6's table whose hook is retired
  before a registry-side test proves the guarantee holds." Concretely here: a clause where
  the hook refuses and the registry admits. Any such case means bp-149 must not retire that
  hook, and the seal must say so.
- **Invariant(s) it must not violate:** invariant 8. ⚑ **Side-effect audit before the demo
  runs** (§3 risks): `cmd_stop_audit` is read-only over git but **appends a marker line to a
  journal on the HOOK-FAILURE path** — run the harness against a fixture repo root, never the
  real worktree. Record the audit.
- **Touches stored data?** No — fixture repos under `tmp_path`.
- **Parallelizable?** No.  **Depends on:** Items 34, 35, 36.

### Item 38 — clause (d): the active unit as a ref, file untouched

- **Objective:** `UnitState.active_in_checkout` answers "which unit is active here" from the
  registry, while `.claude/state/active-plan` keeps working.
- **Files:** `ops/registry/fold.py`, `scripts/registry.py`,
  `tests/unit/test_registry_seal.py`
- **Acceptance test:** two synthetic checkouts each mark a different unit active; a query
  from one never returns the other's; `_lib.py:316 active_plan_path` is **unaffected** (run
  its existing tests, still green).
- **Falsifier:** the registry's answer and `.claude/state/active-plan` disagree while both
  are in use. During the transition **both** are live, and a disagreement is a cross-checkout
  bleed of exactly the kind clause (d) exists to prevent — surface it rather than picking a
  winner.
- **Invariant(s) it must not violate:** `.claude/` is not written by this plan.
- **Touches stored data?** Yes (registry store only).
- **Parallelizable?** Yes.  **Depends on:** Item 35.

### Item 39 — `schema.md`: the clause map, with discharge attribution

- **Objective:** a table a bp-149 builder can read to decide, per hook, whether retirement is
  lawful.
- **Files:** `ops/registry/schema.md`
- **Acceptance test:** the table has one row per clause with: today's implementation
  (`path:line`), the registry-side replacement, the parity test's node id, **which plan
  discharges it**, and its current status (proved | discharged-elsewhere | parked). A test
  asserts every clause letter from note §2.6 appears exactly once.
- **Falsifier:** a clause is marked "proved" whose parity test is a `skip`. That is the
  completion-claims-honesty failure in miniature, and it is the specific way bp-149 could be
  led into an unlawful retirement.
- **Invariant(s) it must not violate:** invariant 8; the honest-loss statement for the (a)/(b)
  family must appear verbatim.
- **Touches stored data?** No.
- **Parallelizable?** Yes.  **Depends on:** Item 37.

## 8. Math carried explicitly

N/A — no mathematical object implemented. The clause map is a correspondence between two
enforcement mechanisms; its obligation is the parity harness (Item 37), not a field-guide
entry.

## 9. Non-goals

- ⚑ **No hook retired, edited, or unregistered.** `.claude/settings.json` untouched. Both
  enforcement layers run simultaneously during the transition, by design.
- ⚑ **No `compaction-marker` change** — it is the one surviving hook (§6.4).
- **No `.claude/state/` change** — clause (d)'s file stays; `/build` still writes it.
- **No skill, template, or `CLAUDE.md` edit** — the journal-narrowing and the resume-brief
  deletion are bp-148's rows of note §2.7's table.
- **No `scripts/handoff.py` or `scripts/board.py` change** — bp-148. Clause (e′)'s DERIVED
  half is parked until then.
- **No grading of follow-through answers** (§3 Q2).
- **No `_lib.py` edit** — imported only.
- **No new dependency.**

## 10. Stop-and-raise conditions

- A bp-140/bp-141/bp-145 test submits a bare `sealed` event and must change (§3 Q9) — file a
  finding and stop; those files are outside this `write_scope`.
- Item 36's falsifier trips (clause b2 fires on an export-driven front-matter rewrite) —
  **stop**; that is a contradiction between bp-142's ratchet and bp-144's hash definition,
  and it is an owner-level design question.
- Any parity case where the hook refuses and the registry admits (Item 37) — **stop and
  report prominently**. bp-149 must not retire that hook; invariant 8 says so.
- The session runs long — stop after Item 37 (the harness), leaving Item 39 for a resume
  (§3 risks). Do **not** compress the parity work to fit.
- Any temptation to edit a hook "just to test" — stop; use `--standalone` against a fixture
  repo root.
- Any blessing this plan would have to perform — it must not.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| Clause (e′) DERIVED-half parity | **parked** — only the NARRATIVE half is built here | building it now — it needs `scripts/handoff.py` re-pointed at the registry, which is bp-148's row of §2.7's table, and re-deriving the compare here would reintroduce the (e) circularity finding-0236 records | **bp-148 lands** and `handoff.py` derives from the registry |
| Grading follow-through answers | not graded; presence + non-empty only | grading — a model judging its own work (CONVENTIONS §Testing) and an incentive against honest "built but NOT wired" answers | The owner asks for a stricter schema |
| `.claude/state/active-plan` removal | kept; registry field added alongside | removing it now — `/build` writes it and `.claude/` is out of scope; removal is a retirement act | bp-149 |
| Journal-entry-level registry rows | not built — one entity per journal file (bp-143 §11) | per-entry rows — the note gives no schema and inventing one is the infer-design defect | bp-148 needs entry-level rows for the judgement narrowing |

## 12. Dependency & ordering summary

**Within the plan.** Item 34 (typed seal, writes the registry) → Item 35 (pure fold) →
Item 36 (pure verdict) → Item 37 (the parity harness) → Item 39 (documentation); Item 38 is
parallel with 36–37. Blast radius stays inside `ops/registry/**` and the registry's own
store; nothing in this plan writes a repo artifact, a hook, or a skill.

**Across plans.** `depends_on: [bp-140, bp-142, bp-146]` — the store, the ratchet surface,
and `land()`. Clause (c)'s discharge belongs to **bp-143 + bp-145**, which is why Item 37
records attribution rather than asserting it. `parallelizable_with: [bp-144]` (disjoint
scope). **bp-149 depends on this plan** — its `schema.md` table (Item 39) is the document a
bp-149 builder reads to decide whether each retirement is lawful. `bp-138`/`bp-139` are
independent of this whole family (note §3(5)).
