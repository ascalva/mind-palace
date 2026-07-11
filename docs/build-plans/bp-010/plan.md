---
type: build-plan
id: bp-010
status: complete
design_ref:
  - docs/design-notes/agent-workflow.md # amendment A8 (pending owner paste — see §0)
contract: builder
write_scope:
  - ".claude/hooks/**"
  - "CLAUDE.md"
  - "docs/findings/**"
  - "docs/build-plans/bp-010/**"
session_budget: 1
depends_on: [] # gated on the A8 ratification paste, not on a plan (§0)
parallelizable_with: [bp-007] # disjoint scope: bp-007 never touches hooks/CLAUDE.md
created: 2026-07-11
updated: 2026-07-11
links:
  - docs/findings/finding-0025.md # the warrant; Corrections 1-3 are the spec
  - docs/inbox/proposed-amendment-A8.md # the paste awaiting the owner
supersedes: null
superseded_by: null
warrant: docs/findings/finding-0025.md
---

# Build Plan — A8: the status-aware design-note guard (draft-writable, blessed-immutable, laundering-proof)

> **Every section below is required.** N/A is an accountability act.

## 0. Mode & provenance

Implements amendment A8 (warrant finding-0025) — the same shape as bp-001/002/004: the
owner ratifies the amendment into `agent-workflow.md` BY HAND (paste delivered at
`docs/inbox/proposed-amendment-A8.md`), then this plan lands the mechanical consequence.
**The builder halts unless the A8 entry exists in `agent-workflow.md` §16** (front-matter
check at session start, bp-002 precedent). Readiness blessing is the owner's hand.

## 1. Objective

`docs/design-notes/**` leaves the location denylist and gains the status-aware guard:
draft notes agent-writable, ratified/superseded notes agent-immutable against Edit/Write
AND Bash, laundering-proof via HEAD-keyed Stop-side comparison — proven by a six-case
harness with non-vacuous controls.

## 2. Context manifest

1. `docs/findings/finding-0025.md` — the full spec: Corrections 1–3 ARE the design.
2. `.claude/hooks/_lib.py` — whole file (the only code surface).
3. `docs/design-notes/agent-workflow.md` §16 A8 entry (must exist; halt otherwise).
4. `docs/build-plans/bp-002/` + `bp-000/acceptance/` — the isolated-temp-repo harness
   pattern this plan's harness follows.
5. `CLAUDE.md` — the "Write discipline" digest line this plan updates.

## 3. Investigation & grounding

Grounded against live `_lib.py` 2026-07-11 (orchestrator pre-pass; builder re-confirms):

- **Q1 — where does the denylist apply pre-hoc?** `cmd_scope_check`, `_lib.py:288`; the
  denylist arm is step 1 at `:294-299`; the orchestrator posture (no active plan) ALLOWs
  everything non-denylisted at `:301-305` — which is exactly what makes draft notes
  writable for the orchestrator after A8, with no further change.
- **Q2 — the helpers exist as finding-0025 claims?** Yes: `status_of` at `:204` (on-disk
  front-matter, `_normalize_status`-hardened per A5); `is_design_note` at `:251`
  (excludes the bare directory).
- **Q3 — where does the post-hoc catch live?** `cmd_stop_audit` `:472`; the (b) branches
  filter `_changed_files()` against `DENYLIST` at `:508-510` (plan-active) and `:519`
  (orchestrator posture) — design-notes drop out of both when the entry is removed, so
  the HEAD-keyed check (Correction 2) must be added as a NEW session-universal clause,
  like (c).
- **Q4 — HEAD-status mechanism?** No `_head_status_of` exists; `_diff_text_head` (`:394`)
  and `_blessing_in_diff` (`:411`) establish the read-HEAD pattern
  (`git show HEAD:<path>` / `git diff HEAD`). The new helper parses front-matter from
  `git show HEAD:<path>` and normalizes with the SAME `_normalize_status` (A5 parity —
  comment-evasion hardening must apply to the HEAD read too, else laundering moves into
  the comment trick).
- **Q5 — DENYLIST mirrors elsewhere?** None. Checked 2026-07-11: no
  `.claude/settings*.json` entry; `gate-guard.sh:7` is a comment about scope, not a
  mirror; `CLAUDE.md` carries the human-readable digest line (updated by Item 14).
- **Q6 — deletion of a ratified note via Bash?** `_changed_files()` includes deletions
  (porcelain), and `git show HEAD:<path>` still yields `ratified` for a deleted file —
  the HEAD-keyed check therefore catches deletion for free. The harness must prove it
  (case c2).

**Additional risks or questions surfaced during reading:** the Stop-side check must skip
untracked NEW notes (HEAD status = nonexistent → legal draft creation) without letting a
Bash-minted note AT `status: ratified` through — that path is already covered by
`_untracked_blessing` (`:452`, A3); the harness includes the control (case f2).

## 4. Reconciliation

- `_lib.py` DENYLIST comment ("the sacred fixed points… the ratified design record") →
  **banner: correction** — the comment now names the status-aware split and cites A8.
- `CLAUDE.md` "A foundation denylist (`CONSTITUTION.md`, `docs/design-notes/**`,
  `eval/golden/**`) is never writable" → **correction carried by Item 14** — becomes the
  three-entry denylist + one-line status rule (safety-critical digest stays in-context
  per amendment A2's exemption).
- `agent-workflow.md` §5 row + §16 — **owner's paste** (Edit 3 of the amendment file);
  NOT this plan's surface; the builder verifies the paste landed, never performs it.

## 5. Write scope

Prose mirror: the hooks package (all changes in `_lib.py`; `.sh` wrappers only if a
comment needs truth), `CLAUDE.md` (one digest line), findings, this plan's dir (the
six-case harness lives in `docs/build-plans/bp-010/acceptance/`, bp-000 pattern — NOT
`tests/**`, which bp-007 owns concurrently). **Out of scope:** `docs/design-notes/**`
(still! the owner pastes the amendment; and until Item 12 lands, the denylist itself
still bars it — this plan modifies the guard while standing outside it),
`eval/golden*`, everything else.

## 6. Interfaces pinned inline

finding-0025's proposed rule (the spec, verbatim-condensed):

- Draft design notes → agent-writable (create new at `draft`; edit on-disk-`draft`),
  subject to normal plan write-scope.
- Ratified/superseded → agent-immutable: not content, not status, not deletion.
- `draft→ratified` transition → owner-only, unchanged (`cmd_gate_check`, `:322`).

Correction 1 (verbatim requirement): gate-guard ALLOWs when no status line is in the
write → the CONTENT guard lives in `cmd_scope_check`, at the point the denylist is
applied today.

Correction 2 (verbatim requirement): the Stop-side check must compare against the
target's status **at HEAD**, never the working tree (post-hoc, the tree already carries
the laundered value), exactly as `_blessing_in_diff` reads HEAD.

Current signatures (live, 2026-07-11): `status_of(path_rel) -> str | None` (`:204`);
`is_design_note(path_rel) -> bool` (`:251`); `cmd_scope_check(file_path) -> int`
(`:288`); `cmd_stop_audit(diff_file) -> int` (`:472`); `DENYLIST` list (`:32`).

## 7. Items

### Item 12 — the guard (pre-hoc + post-hoc)

- **Objective:** remove `"docs/design-notes/**"` from `DENYLIST`; add the status arm to
  `cmd_scope_check` (deny on-disk `ratified|superseded`; fall through for draft/new);
  add `_head_status_of()` + the session-universal Stop-side clause (flag any changed or
  deleted design note whose HEAD status is `ratified|superseded`).
- **Files:** `.claude/hooks/_lib.py`.
- **Acceptance test:** standalone hook invocations (the harness, Item 13) — plus the
  live Stop-gate of the building session itself passing with this very plan's files.
- **Falsifier:** any of the six harness cases failing; OR the laundering case passing
  pre-hoc but escaping the Stop audit (the exact hole Correction 2 exists to close).
- **Invariant(s):** `CONSTITUTION.md`/`eval/golden*` denials unchanged; `cmd_gate_check`
  transition denials unchanged; A5 normalization applied to HEAD reads.
- **Touches stored data?** no **Parallelizable?** no **Depends on:** the A8 paste (§0)

### Item 13 — the six-case harness (non-vacuous controls)

- **Objective:** `docs/build-plans/bp-010/acceptance/run.sh` — isolated temp repos
  (bp-002 pattern), each case asserting BOTH the deny and its control:
  (a) draft-note Edit ALLOWS; (b) ratified body-only Edit DENIES pre-hoc;
  (c1) Bash body-only edit of ratified BLOCKS at Stop; (c2) Bash DELETION of ratified
  BLOCKS at Stop; (d) laundering (ratified→draft) DENIES pre-hoc AND its Bash form
  BLOCKS at Stop; (e) new-note-at-draft creation ALLOWS; (f1) `CONSTITUTION.md` +
  `eval/golden/*` still DENY; (f2) Bash-minted untracked note at `status: ratified`
  still BLOCKS (A3 regression).
- **Files:** `docs/build-plans/bp-010/acceptance/*`.
- **Acceptance test:** `run.sh` exits 0 with a per-case PASS table.
- **Falsifier:** a case that passes with the guard REVERTED (vacuous test) — the harness
  must fail against pre-A8 `_lib.py`, proven once in the journal.
- **Invariant(s):** harness never touches the real repo's stores or notes.
- **Touches stored data?** no **Parallelizable?** with Item 12 (TDD order encouraged)
  **Depends on:** none

### Item 14 — the digest surfaces

- **Objective:** `CLAUDE.md` write-discipline line → three-entry denylist + status rule;
  `_lib.py` DENYLIST comment banner per §4.
- **Files:** `CLAUDE.md`, `.claude/hooks/_lib.py` (comment only).
- **Acceptance test:** grep shows no `docs/design-notes/**` in any denylist text outside
  the §16 history; ratchet green.
- **Falsifier:** a stale digest line telling future sessions the old rule (the
  finding-0013 class of defect).
- **Invariant(s):** CLAUDE.md thinness (net line count ±2).
- **Touches stored data?** no **Parallelizable?** no **Depends on:** Item 12

## 8. Math carried explicitly

N/A — no mathematical object implemented (a guard predicate over a two-value status set).

## 9. Non-goals

A7 (oq-0003, separate warrant); relaxing anything for `CONSTITUTION.md`/`eval/golden*`;
gate-guard changes; write access for any agent to ratified content by any path; the
research-note schema (oq-0010).

## 10. Stop-and-raise conditions

The §16 A8 entry is absent (halt at start — the license is the paste); any harness case
requires weakening `_untracked_blessing` or `cmd_gate_check` (spec-defect finding, stop);
the six cases cannot all pass simultaneously (the two-layer design is contradictory
somewhere — finding, stop).

## 11. Parked decisions

| Decision                                   | Default recorded                                                                              | Rejected alternatives (why)                                                           | Re-entry condition                           |
| ------------------------------------------ | --------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- | -------------------------------------------- |
| draft-note writes for BUILDERS under plans | allowed only when the plan's write_scope grants a design-notes path (normal capability rules) | blanket builder access (over-broad; the orchestrator is the note-drafting role)       | a ratified workflow change to builder duties |
| Stop-side check scope                      | design notes only                                                                             | extending HEAD-keyed immutability to eval/golden (already absolute-denied; redundant) | golden-set ever leaves the hard denylist     |

## 12. Dependency & ordering summary

Owner paste (A8 into the spec) → bless this plan → Item 13 ∥ Item 12 → Item 14.
Parallelizable with bp-007 (disjoint scope). After completion: finding-0025 →
`promoted`; oq-0011 swept; `docs/inbox/proposed-amendment-A8.md` deleted;
future note-drafting happens directly in `docs/design-notes/` at `draft`.
