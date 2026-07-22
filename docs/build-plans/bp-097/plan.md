---
type: build-plan
id: bp-097
track: workflow
status: proposed
design_ref:
  - docs/design-notes/track-board-and-deskcheck-gate.md
contract: builder
write_scope:
  - docs/templates/deskcheck.md
  - docs/deskchecks/**
  - .claude/hooks/_lib.py
  - .claude/hooks/gate-guard.sh
  - .claude/skills/checkpoint/SKILL.md
  - .claude/skills/delegate/SKILL.md
  - tests/integration/test_deskcheck_gate.py
  - tests/integration/test_handoff_gate.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 250k
  actual: null
depends_on: []
parallelizable_with: []
created: 2026-07-21
updated: 2026-07-21
links:
  - docs/design-notes/track-board-and-deskcheck-gate.md
  - docs/findings/finding-0153.md
  - docs/findings/finding-0152.md
  - docs/design-notes/session-handoff-gate.md
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — WF-2: the deskcheck gate

> Every section below is required; an inapplicable one is `N/A — <reason>`.

## 0. Mode & provenance

Investigation and planning produced this plan (graduation of the ratified
`dn-track-board-and-deskcheck-gate`, §3's WF-2). Implementation proceeds
item-by-item on owner approval; authority-to-act (owner ruled "build before
bp-090") is separate from the proposed→ready blessing, which no agent flips.
This plan installs the **third owner-only gate** (the deskcheck verdict) and the
**seal follow-through tooth** — the enforcement WF-1's substrate is inert without.

## 1. Objective

Make a track's closure require the owner: a deskcheck is a typed artifact
(`docs/deskchecks/dc-NNN.md`) whose `verdict` flip to `approved`/`needs-work` is
denied to agents pre-hoc (gate-guard) and post-hoc (Stop clause (c)), and a
plan's seal must carry a `## Follow-through` block the Stop gate (new clause (f))
checks.

## 2. Context manifest

Read these, in order, before any work:

1. `docs/design-notes/track-board-and-deskcheck-gate.md` — the whole note; D3
   (the dc record + the third gate), D5 (seal follow-through + clause (f)), D6
   (clause (c) yields to an owner-staged blessing), D7 (P-WF1 hook-env probe).
2. `.claude/hooks/_lib.py` — the surfaces this plan extends, verbatim:
   - `cmd_gate_check` (`:421-439`) — the pre-hoc blessing denial (design-note
     ratified, plan ready). Deskcheck verdict denial joins it.
   - `cmd_gate_check_hook` (`:448-469`) — reads the intended status from edit blobs
     via `_status_in_text`; the deskcheck path reads `verdict:` analogously.
   - `is_design_note` (`:335`), `is_build_plan` (`:343`), `status_of` (`:246`),
     `_head_status_of` (`:254`) — the file-type + status helpers to mirror for
     deskchecks.
   - `_blessing_in_diff` (`:510-527`) + `_untracked_blessing` (`:551-569`) — the
     (c) post-hoc scanners; the verdict flip joins the transition set.
   - `cmd_stop_audit` (`:571-745`) — the (a)–(e) clause family; clause (f) is new,
     and the (c) reason string (`:663-669`) gains the yield posture.
3. `.claude/hooks/gate-guard.sh` — the PreToolUse wrapper (`:38-50`) that calls
   `_lib gate-check[-hook]`; fires on `Edit|Write|MultiEdit` broadly (the file-type
   gating is in the lib, not the matcher — so no settings.json change is needed to
   cover `docs/deskchecks/**`). Its header comment (`:6-7`) is stale after this
   plan and is corrected.
4. `.claude/skills/checkpoint/SKILL.md` — the journal contract; "Seal entries
   carry a read map" (`:37-45`) is the section the Follow-through block joins;
   "On the way out" (`:59-64`) lists what the Stop gate blocks on.
5. `.claude/skills/delegate/SKILL.md` — right-sizing the agent to verification
   complexity (`:28-`); the audit-right-sizing rule lands here.
6. `tests/integration/test_handoff_gate.py` — how `cmd_stop_audit` is exercised
   (subprocess `_lib.py stop-audit` with a fixture repo); the model for the new
   deskcheck-gate test and the reason (f) additions.
7. `docs/build-plans/bp-096/plan.md` §6 — the dc-record front-matter schema and
   the manifest schema WF-1 pins; this plan's template MUST match that schema
   exactly (board.py already parses it).

## 3. Investigation & grounding

- **Q1 — Does gate-guard already fire on `docs/deskchecks/**`?** Yes, mechanically:
  the hook matches `Edit|Write|MultiEdit` (`settings.json:20`) for all files, and
  `cmd_gate_check` returns ALLOW for non-note/non-plan files (`_lib.py:424-426`).
  So covering deskchecks is a **lib change only** (add a deskcheck branch); no
  settings.json edit. Confirmed: `gate-guard.sh` delegates entirely to
  `_lib gate-check[-hook]` (`:40-42`).
- **Q2 — How does the pre-hoc denial read the intended verdict?**
  `cmd_gate_check_hook` gathers the edit's blobs and runs `_status_in_text` to
  find `status:` (`:461-464`). The deskcheck path needs a sibling that reads
  `verdict:` from the blobs, then denies `pending → approved|needs-work` when the
  on-disk verdict is `pending` (mirror the `cur != new` shape of `:432-436`).
  **The code does not settle** whether `_status_in_text` also matches `verdict:` —
  it is named for `status`; the builder must add a `_verdict_in_text` (or
  generalize) rather than assume. Grounded as an explicit sub-task, not inferred.
- **Q3 — How does the post-hoc (c) scanner detect a verdict flip?**
  `_blessing_in_diff` (`:510-527`) walks the unified diff for `status:` lines on
  gate-guarded files and flags a blessing transition. The verdict flip is the same
  shape on `docs/deskchecks/*.md`: an added `verdict: approved|needs-work`. The
  builder extends the scanner (or adds a parallel `_verdict_in_diff`) and the
  `_untracked_blessing` from-nothing check (a dc minted directly at `approved`).
- **Q4 — Clause (f) detection mechanism (seal follow-through).** `cmd_stop_audit`
  already computes `_diff_text_head()` (build-plans + design-notes diff) and
  `journal_for(plan)`. Clause (f): scan the diff for a plan flipping to
  `status: complete` (mirror `_blessing_in_diff`'s per-file status parse); for each
  such plan, if `journal_for(plan)`'s **tail** lacks a `## Follow-through` header,
  BLOCK (the (a)-staleness grep-class, one more crude post-hoc check). Works in
  both postures: builder posture (active plan sealed) and orchestrator posture
  (the flip shows in the tracked diff). **The code does not settle** the exact
  "journal tail" window — the builder picks a bounded read (e.g. the last entry) and
  encodes it in the test.
- **Q5 — Does the (c) reason change risk reddening `test_handoff_gate.py`?** The
  (e) tests assert `"(e)" in out` / `startswith("BLOCK:")` (`:145-186`) — they do
  not pin the (c) string, so the D6 reword is safe. But this plan modifies
  `cmd_stop_audit` (the function those tests exercise) and adds clause (f), so
  `test_handoff_gate.py` is carried in `write_scope` per the retrofit rule, in case
  a fixture needs a `## Follow-through` block added to keep its seal fixtures green.
- **Q6 — P-WF1 hook-env probe (D7): does a hook see the running model id?** Not
  settled by reading — it is an *investigation item* (Item 7): a ≤5-minute check of
  whether the PreToolUse hook environment exposes the model id (env var / stdin
  JSON field). Journaled either way; if yes, note the structural upgrade path
  (gate-guard could refuse a non-Fable design-note creation); if no, the park (D7)
  stands and the journal says so.

**Additional risks surfaced during reading — a NEW clause-(b2) gap this very
session hit:** D6 teaches clause **(c)** to yield to an owner-staged *blessing*,
but clause **(b2)** ("blessed design notes modified vs HEAD", `_lib.py:634-645`)
has **no yield affordance**. The WF-1 track-backfill introduces a brand-new (b2)
trigger — the owner hand-editing ratified notes to add `track:` — and this session
thrashed on it identically to the finding-0152 blessing case (repeated Stop-gate
BLOCKs while the owner's edit sat uncommitted). This is folded into Item 4 as a
scope addition (see §7). `[ESTABLISHED — observed live this session, 2026-07-21]`

## 4. Reconciliation

- `.claude/hooks/_lib.py` `cmd_gate_check` — **[cross-ref: extension]**. Add a
  deskcheck branch denying `verdict: pending → approved|needs-work` by an agent
  edit, beside the two blessing branches. Additive; the two existing branches are
  untouched.
- `.claude/hooks/_lib.py` `_blessing_in_diff` / `cmd_stop_audit` (c) —
  **[cross-ref: extension]**. The verdict flip joins the (c) transition set
  (post-hoc), so a Bash-mediated flip past the pre-hoc guard is still caught.
- `.claude/hooks/_lib.py` `cmd_stop_audit` (c) reason (`:663-669`) —
  **[banner: correction]**. When the uncommitted diff is *exactly* the
  blessing/verdict shape in gate-guarded files, the reason becomes the D6 yield
  message: "owner blessing/verdict appears staged — if these flips are yours
  (agent), revert; if the owner's, say so once and YIELD (do not poll, do not
  re-ask)." Same block, corrected posture.
- `.claude/hooks/_lib.py` `cmd_stop_audit` — **[cross-ref: extension]**. New
  clause (f) joins (a)–(e): a plan sealed to `complete` this session whose journal
  tail lacks `## Follow-through` blocks close.
- `.claude/hooks/gate-guard.sh` header comment (`:6-7`, "Only fires on files under
  docs/design-notes/ and docs/build-plans/**/plan.md") — **[banner: correction]**:
  now also `docs/deskchecks/**`.
- `.claude/skills/checkpoint/SKILL.md` — **[cross-ref: extension]**. A new "Seal
  entries answer follow-through" note beside the read-map section: the SEAL entry
  carries a `## Follow-through` block (five questions, D5).
- `.claude/skills/delegate/SKILL.md` — **[cross-ref: extension]**. The
  audit-right-sizing rule (risk-proportional audit, D2/§0-Q of the note).

## 5. Write scope

- `docs/templates/deskcheck.md` — the new dc template (schema per bp-096 §6).
- `docs/deskchecks/**` — the new record directory (seed a `.gitkeep` or a short
  `README.md` explaining the dir; no dc records authored — those are owner sessions).
- `.claude/hooks/_lib.py` — the gate-check deskcheck branch + the (c) verdict
  extension + the (c) yield message + new clause (f) + the (b2) yield affordance.
- `.claude/hooks/gate-guard.sh` — the stale-comment correction only.
- `.claude/skills/checkpoint/SKILL.md`, `.claude/skills/delegate/SKILL.md` — the
  two skill edits (§4).
- `tests/integration/test_deskcheck_gate.py` — new: verdict pre/post-hoc denial +
  clause (f) coverage.
- `tests/integration/test_handoff_gate.py` — carried (retrofit rule, Q5): the
  builder may need to add a `## Follow-through` block to seal fixtures.

**Deliberately OUT of scope:** WF-1's surfaces (`board.py`, `session-brief.sh`,
`triage.md`, templates for build-plan/design-note, `docs/tracks/**`, the board
files); the two existing blessing gates (unchanged — D3 adds a *third*, it does
not touch them); scope-guard semantics; the foundation denylist; authoring any
actual `dc-NNN` record (owner sessions off the queue). `_lib.py` is shared with no
other active plan — WF-1 deliberately keeps its brief injection Bash-side.

## 6. Interfaces pinned inline

**Deskcheck record front matter (this template MUST match bp-096 §6 verbatim so
`board.py` parses it) — from the note D3:**
```
---
type: deskcheck
id: dc-NNN
track: <slug>
date: <date>
items: [<plan ids>]
audit_refs: [<finding ids>]
verdict: pending          # pending | approved | needs-work  — flip is OWNER-ONLY, by hand
send_back: null           # <phase> only when verdict: needs-work
links: []
---
# Deskcheck — <track title>
## What was built
## How (the demo script, or the honest current state)
## Surprises
## What is NOT done
```
The agent prepares the whole bundle and leaves `verdict: pending`. The flip is the
owner's hand (the blessing ceremony: lazygit; the agent pre-loads the commit
message; **never polls** — D6).

**`cmd_gate_check` blessing branches to mirror (`_lib.py:432-436`, verbatim):**
```
if dn and new_status == "ratified" and cur != "ratified":
    print(f"DENY: {reason}Design-note ratification ({cur or 'new'}→ratified) on '{fp}' denied.")
    return 0
if bp and new_status == "ready" and cur != "ready":
    print(f"DENY: {reason}Plan readiness ({cur or 'new'}→ready) on '{fp}' denied.")
    return 0
```
The deskcheck branch is the same shape on a `verdict:` transition
(`pending → approved|needs-work`), with `is_deskcheck(fp)` (new, mirroring
`is_design_note`) and the verdict read from the file / edit blobs.

**Clause (c) reason today (`_lib.py:663-669`) — the string the D6 posture
rewrites when the diff is exactly the staged-blessing/verdict shape:**
```
f"(c) uncommitted blessing transition vs HEAD: {bless}. Blessing is "
f"owner-manual (§10) — commit it (then it is accountable) or revert "
f"the Bash-mediated flip."
```

**Clause (b2) today (`_lib.py:640-645`) — gains the same yield affordance:** when
the only modification to a ratified/superseded note is **additive front matter**
(e.g. a `track:` line — no change to body or to `status`), the reason adds the D6
posture: "if this metadata edit is the owner's staged hand, commit it (accountable)
and say so once; do not thrash." (Detection: the note's per-file diff adds only
front-matter `key: value` lines and changes no existing line — a narrow, crude
shape check; if unsure, fall back to today's hard block.) This closes the gap §3
surfaced. Keep it conservative — a false yield must never let a *body* edit pass.

**The five Follow-through questions (D5) — the block clause (f) greps for:**
```
## Follow-through
- **Built?** …
- **Wired / delivered (or why dormant)?** …
- **Does a consumer use it?** …
- **Track state (what remains on this track)?** …
- **Opened a new track/finding?** …
```

## 7. Items

### Item 1 — the deskcheck template + record directory
- **Objective:** a typed dc artifact exists to instantiate; the record dir exists.
- **Files:** `docs/templates/deskcheck.md`, `docs/deskchecks/README.md` (or
  `.gitkeep`).
- **Acceptance test:** `docs/templates/deskcheck.md` parses via
  `parse_front_matter` with `type: deskcheck` and every field in §6 (verdict
  defaulting to `pending`); `docs/deskchecks/` exists and is tracked.
- **Falsifier:** the template's front matter diverges from bp-096 §6's schema ⇒
  `board.py` can't parse a real dc's verdict later (schema drift between the two
  plans).
- **Invariant(s):** schema matches bp-096 §6 exactly; `verdict: pending` is the
  only agent-legal starting value.
- **Touches stored data?** No.  **Parallelizable?** Yes.  **Depends on:** none.

### Item 2 — pre-hoc verdict denial (gate-guard / cmd_gate_check)
- **Objective:** an agent Edit/Write that flips a dc `verdict` off `pending` is
  denied before it lands.
- **Files:** `.claude/hooks/_lib.py` (`is_deskcheck` + `cmd_gate_check` branch +
  `cmd_gate_check_hook` verdict read), `.claude/hooks/gate-guard.sh` (comment).
- **Acceptance test:** `bash .claude/hooks/gate-guard.sh --standalone
  docs/deskchecks/dc-001.md approved` prints `DENY:` (given an on-disk
  `verdict: pending`); `... pending` prints ALLOW; a design-note/plan blessing
  still denies (no regression). Covered in `test_deskcheck_gate.py`.
- **Falsifier:** an agent-authored edit changes a dc verdict and the gate allows it
  (F-WF3, pre-hoc half) ⇒ the branch or the verdict-read is wrong.
- **Invariant(s):** the two existing blessing branches are untouched; fail-open,
  fail-loud preserved.
- **Touches stored data?** No.  **Parallelizable?** No (shares `_lib.py`).
  **Depends on:** Item 1 (needs a dc shape to test).

### Item 3 — post-hoc verdict audit + the D6 yield message (clause (c))
- **Objective:** a Bash-mediated verdict flip is caught at Stop; the (c) message
  teaches the owner-staged yield.
- **Files:** `.claude/hooks/_lib.py` (`_blessing_in_diff`/`_verdict_in_diff`,
  `_untracked_blessing`, the (c) reason string).
- **Acceptance test:** in a fixture repo, a Bash-written `verdict: approved` on a
  tracked dc ⇒ `_lib.py stop-audit` BLOCKs citing (c); the reason contains the
  yield posture ("if the owner's, say so once and YIELD"). A committed verdict
  self-clears (HEAD-keyed). Covered in `test_deskcheck_gate.py`.
- **Falsifier:** the board shows a track CLOSED with no approved dc on disk, or a
  Bash verdict flip passes Stop (F-WF3, post-hoc half) ⇒ the gate is decorative.
- **Invariant(s):** committed-blessing-self-clears (A1) preserved; the yield
  reword never *weakens* the block — it still BLOCKs, only the guidance changes.
- **Touches stored data?** No.  **Parallelizable?** No.  **Depends on:** Item 2.

### Item 4 — clause (f) seal follow-through + the (b2) owner-staged yield
- **Objective:** a seal to `complete` without a `## Follow-through` block blocks
  close; and clause (b2) yields to an owner-staged additive-metadata edit of a
  ratified note (the gap §3 surfaced).
- **Files:** `.claude/hooks/_lib.py` (new clause (f) in `cmd_stop_audit`; the
  (b2) yield affordance), `tests/integration/test_handoff_gate.py` (fixture seal
  gains a Follow-through block if needed).
- **Acceptance test:** a fixture plan flipped to `complete` with a journal lacking
  `## Follow-through` ⇒ `_lib.py stop-audit` BLOCKs citing (f); adding the block
  clears it. A ratified note with only an added front-matter `track:` line ⇒ the
  (b2) reason carries the yield posture (still BLOCK until committed, but guides
  yield not thrash); a ratified-note **body** edit still hard-blocks with no yield.
  `test_handoff_gate.py`'s (e) tests stay green.
- **Falsifier:** a sealed plan passes the gate with a present-but-empty
  Follow-through block (F-WF5) ⇒ the grep-class check is too weak (tighten to
  per-question tokens or accept the residual, documented). OR: a (b2) yield lets a
  body edit of a ratified note pass ⇒ the shape check is unsafe, revert to hard block.
- **Invariant(s):** clause (f) is additive to (a)–(e); the (b2) yield NEVER permits
  a non-additive edit; both are post-hoc grep-class (crude, honest).
- **Touches stored data?** No.  **Parallelizable?** No.  **Depends on:** Item 3
  (same function region).

### Item 5 — checkpoint skill: the Follow-through seal shape
- **Objective:** the seal contract requires the five-question block.
- **Files:** `.claude/skills/checkpoint/SKILL.md`.
- **Acceptance test:** the skill's seal section documents `## Follow-through` with
  the five questions (D5), so a builder writing a SEAL entry knows to include it;
  the shape matches clause (f)'s grep.
- **Falsifier:** the documented block and clause (f)'s expected header disagree ⇒
  a compliant seal still trips the gate.
- **Invariant(s):** the read-map seal requirement is preserved; the block is
  additive to the existing seal shape.
- **Touches stored data?** No.  **Parallelizable?** Yes.  **Depends on:** none.

### Item 6 — delegate skill: audit right-sizing
- **Objective:** the risk-proportional audit rule is recorded (delegated/lower-tier
  build ⇒ independent Opus audit; supervised same-tier merge ⇒ merge scrutiny IS
  the audit, recorded as such).
- **Files:** `.claude/skills/delegate/SKILL.md`.
- **Acceptance test:** the skill contains the rule, phrased so `board.py`'s
  "audit: present/owed" flag (fed by manifest `audit_refs`) has a documented basis.
- **Falsifier:** the rule contradicts the note's D2 audit reading ⇒ realign.
- **Invariant(s):** the gates never loosen (delegate skill's standing rule).
- **Touches stored data?** No.  **Parallelizable?** Yes.  **Depends on:** none.

### Item 7 — P-WF1 hook-env probe (≤5 min, journaled either way)
- **Objective:** determine whether the PreToolUse hook environment exposes the
  running model id (the re-entry condition for structural model-per-phase, D7).
- **Files:** none (investigation; the finding is the journal entry).
- **Acceptance test:** the journal records the answer with evidence (the env var /
  stdin field checked). If yes: note the upgrade path (gate-guard could refuse a
  non-Fable design-note *creation*). If no: the P-WF1 park stands and the journal
  says so explicitly.
- **Falsifier:** the probe is skipped or answered without evidence ⇒ D7's re-entry
  condition stays unresolved (the note flagged this as `[INFERENCE]` deliberately).
- **Invariant(s):** no code shipped from the probe in this plan (it decides whether
  a *future* plan is warranted).
- **Touches stored data?** No.  **Parallelizable?** Yes.  **Depends on:** none.

## 8. Math carried explicitly

N/A — no mathematical object implemented (gate logic + templates + skill prose).

## 9. Non-goals

- No change to the two existing blessing gates (draft→ratified, proposed→ready) —
  D3 adds a *third* verdict gate; it does not touch the two.
- No scope-guard / denylist / bright-line change.
- No board UI, no generator (WF-1/bp-096 owns those); no authoring of real dc
  records (owner sessions off the queue).
- No full authorship-attribution machinery for working-tree flips (P-WF2) — the
  D6 message + behavioral rule + the narrow (b2) shape-check is the proportional
  fix; true attribution stays parked.

## 10. Stop-and-raise conditions

- The (b2) yield shape-check cannot be made *safe* (any risk it lets a body edit of
  a ratified note pass) ⇒ do NOT ship the yield; keep today's hard block and file a
  finding routing P-WF2 (true attribution).
- Clause (f)'s grep proves too weak to be meaningful even at per-question tokens ⇒
  record the residual honestly (the deskcheck itself is the backstop; the gate only
  forces the writing) rather than over-engineer.
- Any need to touch a blessing gate, scope-guard, or a ratified note's *content*
  ⇒ STOP (spec boundary; file a finding).
- The P-WF1 probe surfaces that the model id IS available ⇒ do not build the
  structural gate here; journal the path and let the owner graduate a new plan.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| True authorship attribution for working-tree flips (P-WF2) | D6 message + behavioral rule + narrow (b2) shape-check | session-write tracking is machinery beyond the measured waste | F-WF6 fires (thrash recurs despite the message) |
| Structural model-per-phase enforcement (P-WF1) | procedural (banner + usage verify + board visibility) | asserting a hook can read the model id, unverified | Item 7's probe finds a model id available to hooks |
| Auto-drafting dc bundles from journals/reports (P-WF4) | agent drafts by hand from the seal + phone report | premature before a few deskchecks measure the bottleneck | drafting measured as the bottleneck |
| Clause (f) strength | grep for `## Follow-through` header | per-question token checks now = over-fitting a crude tooth | F-WF5 fires (an empty block passes and misleads) |

## 12. Dependency & ordering summary

- **Blast-radius order:** Item 1 (new template + dir — greenfield) → Items 5, 6, 7
  (skill prose + a read-only probe — process surface) → Items 2 → 3 → 4 (the
  `_lib.py` enforcement, highest radius, built in sequence because they share the
  gate-check / stop-audit regions). Ship the template first so the gate has a shape
  to test.
- **Edges:** 2→3→4 are a chain (same `_lib.py` regions); 1 precedes 2 (test needs a
  dc shape); 5, 6, 7 are independent and parallelizable within the session.
- **Cross-plan:** independent of **bp-096 (WF-1)** — disjoint `write_scope`; the dc
  schema is pinned identically in both (§6 here == bp-096 §6) so the two can't
  drift. **Must NOT run concurrently with bp-090** (the note §3; also both
  hooks/skills-tree). Owner blesses proposed→ready item-by-item; the verdict gate
  this installs is itself owner-only thereafter.
