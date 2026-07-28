---
type: build-plan
id: bp-149
track: workflow
status: proposed
design_ref:
  - docs/design-notes/dn-typed-workflow-registry.md
contract: builder
write_scope:
  - .claude/settings.json
  - .claude/hooks/**
  - .claude/state/**
  - tests/integration/test_deskcheck_gate.py
  - tests/integration/test_handoff_gate.py
  - tests/integration/test_worktree_enforcement.py
  - tests/integration/test_registry_retirement.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 450k
  actual: null
depends_on:
  - bp-143
  - bp-145
  - bp-146
  - bp-147
  - bp-148
  - bp-150
  - owner-amendment:agent-workflow-note
  - owner-amendment:autopilot-and-delegated-blessing-note
parallelizable_with: []
created: 2026-07-27
updated: 2026-07-27
links:
  - docs/design-notes/dn-typed-workflow-registry.md
  - docs/design-notes/agent-workflow.md
  - docs/design-notes/dn-autopilot-and-delegated-blessing.md
  - docs/build-plans/bp-146/plan.md
  - docs/build-plans/bp-147/plan.md
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — Staged hook retirement: one guarantee at a time, each behind its green parity test

## 0. Mode & provenance

Investigation and planning produced this plan during `/graduate` of
`dn-typed-workflow-registry` (ratified 2026-07-27); it graduates the note's license (iv),
"staged hook retirement, one guarantee at a time, each behind its parity test".
Implementation proceeds item-by-item on owner approval; the `proposed → ready` blessing is
the owner's alone.

## ⚑⚑ THIS PLAN IS BLOCKED ON OWNER AMENDMENTS. IT IS NOT STARTABLE.

Two **ratified** design notes name the hooks this plan removes as their enforcement
mechanisms. The registry note's §3(1) is explicit and binding:

> **Amendments, owner-ratified, to two ratified notes:** `dn-agent-workflow` (§6 hook
> contracts, §9 note-taking, §2/§10 gate wording — the registry becomes the named enforcement
> substrate) and `dn-autopilot-and-delegated-blessing` (the §2.5.3 recorded collisions:
> flip-executor mechanics and the hook-named enforcement layers). **Until each amendment
> lands, the text it amends governs and the corresponding hook stays.**

And §2.5.3 row 2:

> **Recorded collision:** the guarantee survives, the named mechanism does not; the ratified
> text must be amended by the owner before the hooks it names are removed. **Until then,
> those hooks stay in place (§3 sequencing).**

**Concretely, before `/build bp-149` may run, all of the following must be true:**

1. `docs/design-notes/agent-workflow.md` — §6 (the hook-contracts table), §9 (note-taking),
   and the §2/§10 gate wording — **amended by the owner**, naming the registry as the
   enforcement substrate. Verify by reading §6: if the table still lists `scope-guard`,
   `gate-guard`, `journal-gate`, `session-brief`, `staleness-nudge` as live contracts, the
   amendment has not landed.
2. `docs/design-notes/dn-autopilot-and-delegated-blessing.md` §2.3 — **amended by the
   owner** for the two §2.5.3 collisions (flip-executor mechanics; the hook-named pre-hoc /
   post-hoc layers, "gate-guard continues to deny…", "the Stop-gate clause (c) contract gains
   one narrow exception…").
3. Every §2.6 guarantee this plan retires has a **green** parity test from bp-146 / bp-147,
   and `ops/registry/schema.md`'s clause table (bp-147 Item 39) marks it `proved` — not
   `parked`, not `discharged-elsewhere-but-untested`. **Invariant 8:** "A hook is retired
   only after a registry-side test proves its guarantee's parity."

**If (1) or (2) has not landed, this plan does not start.** A builder that finds the
amendments missing must stop, say so, and file nothing but the observation — it must not
amend a ratified note (agent-immutable, A8), and it must not retire a hook the ratified text
still names. **Amending those notes is an owner hand edit; no agent performs it.**

## 1. Objective

Retire, one at a time and each only behind a green parity test, the five hooks whose
guarantees the registry now carries — leaving `compaction-marker` in place as the one
surviving hook.

## 2. Context manifest

1. `docs/design-notes/dn-typed-workflow-registry.md` §2.6 in full — the disposition table,
   the journal-gate clause map, the honest loss in the (a)/(b) family, **why
   `compaction-marker` stays**, and the `HOOK-FAILURE` / `OUROBOROS_HOOKS_OFF` escape-hatch
   spirit. Plus §3(1) sequencing, §2.9 invariant 8, falsifier F4.
2. `docs/design-notes/agent-workflow.md` §6 — ⚑ **read it to verify the amendment landed**
   (§0 precondition 1). Also §9, §2, §10.
3. `docs/design-notes/dn-autopilot-and-delegated-blessing.md` §2.3 — ⚑ **read it to verify
   the amendment landed** (§0 precondition 2).
4. `ops/registry/schema.md` — the clause table from bp-147 Item 39. ⚑ **This is the document
   that says which retirements are lawful.** A row not marked `proved` blocks its hook.
5. `.claude/settings.json` — the hook registrations, in full.
6. `.claude/hooks/_lib.py` — the whole file; specifically `cmd_scope_check` (`:431`),
   `cmd_gate_check` (`:480`), `cmd_stop_audit` (`:820`), `cmd_brief` (`:1090`),
   `cmd_staleness` (`:1146`), `cmd_marker` (`:1171`), and `main` (`:1188`).
7. `.claude/hooks/*.sh` — the six wrappers.
8. `tests/integration/test_deskcheck_gate.py`, `tests/integration/test_handoff_gate.py`,
   `tests/integration/test_worktree_enforcement.py` — ⚑ **the tests that pin the hooks'
   exact DENY/BLOCK surface.** They copy the real `_lib.py` into a fixture repo and assert on
   the output lines; retiring a hook reddens them, which is why they are in `write_scope`.
9. `docs/build-plans/bp-146/plan.md` §6 and `docs/build-plans/bp-147/plan.md` §6.3 — the
   registry-side replacements and the clause map as code contracts.
10. `docs/build-plans/bp-149/journal.md`.

### DRY audit — does `core/` (or the wider tree) already have this?

- **The replacements?** All built already: `ops/registry/land.py` (bp-146),
  `ops/registry/admission.py` (bp-145), `ops/registry/seal.py` + `fold.py` (bp-147),
  `ops/registry/export.py` + the ratchet (bp-142/143), `scripts/handoff.py`/`scripts/board.py`
  re-pointed (bp-150). ⚑ **This plan writes no new enforcement logic at all** — it removes
  registrations and code whose guarantee is already carried elsewhere, and updates the tests
  that pinned the removed surface. If this plan finds itself *implementing* a check, the
  parity work was incomplete and it must stop.
- **`compaction-marker`'s guarantee?** Nothing else carries it and nothing can (note §2.6:
  "A warrant cannot travel with a context window"). It stays.
- **`_lib.py`'s reusable primitives** (`parse_front_matter`, `glob_match`, `git_show_head`,
  `_split_front_matter`) are imported by `scripts/board.py`, `scripts/handoff.py`, and
  `ops/registry/**`. ⚑ **They must survive the retirement.** Deleting `_lib.py` wholesale
  would break three consumers; only the retired *clause* functions and the hook
  registrations go.
- **`core/` audit:** N/A — no code under `core/` is touched or duplicated.

## 3. Investigation & grounding

- **Q1 — which hooks go, and which stays?** Note §2.6's table: `gate-guard` **dissolved**;
  `journal-gate` **dissolved into queries + land-time admission**; `session-brief`
  **replaced by query**; `staleness-nudge` **dissolved**; `scope-guard` **moved to land-time
  admission, per-unit level**; `compaction-marker` **kept — the one surviving hook**.
- **Q2 — what is the staging order?** The note says "one guarantee at a time, each behind its
  parity test" (§3(3)) and "then retire hooks one at a time by hand-editing
  `.claude/settings.json` as each parity test goes green — the hook removals are themselves
  owner-visible diffs" (§4). ⚑ **Blast-radius order for removals is the reverse of the usual
  rule:** remove the *least* protective first. Pinned in §7: `staleness-nudge` (advisory
  only) → `session-brief` (no denial semantics) → `gate-guard` (dissolved: status is not
  file-resident) → `journal-gate` (six clauses) → `scope-guard` (the hard one, and the last
  to go).
- **Q3 — who edits `.claude/settings.json`?** Note §4 says "the owner turns it on in stages
  … by hand-editing `.claude/settings.json`". ⚑ **The code does not settle whether the
  removal edit is an owner act or a builder act.** Reading the surrounding text: §4's list is
  about *rollout*, and the same paragraph makes the owner's act the *decision* ("only after
  the corresponding parity test is green in CI"), while the note's §3 puts the edits "under
  plans". ⇒ **Default recorded (§11): the builder makes the removal edit, one hook per
  commit, each commit an owner-visible diff; the owner's control is the item-by-item
  approval at the `proposed → ready` gate and the ability to revert one commit.** If the
  owner reads §4 as reserving the file to his own hand, this plan's items become
  owner-executed and the builder's job is to prepare each diff — park and ask.
  ⚑ `.claude/settings.json` is **not** on the foundation denylist (`_lib.py:35-39` — only
  `CONSTITUTION.md`, `eval/golden/**`, `eval/golden.py`), so the guard permits it; the
  question is intent, not capability.
- **Q4 — does removing a hook remove its `_lib.py` code?** Not necessarily, and the safe
  default is **no**. `_lib.py` is imported by `scripts/board.py:34-38`,
  `scripts/handoff.py:57-61`, and `ops/registry/**` (bp-146). ⇒ Stage each retirement as
  **registration removal first** (the behavior change), and only then delete the now-unused
  clause function — with a grep proving no consumer remains. Two acts, two commits, so a
  revert is surgical.
- **Q5 — what about the escape hatch?** Note §2.6: "The `HOOK-FAILURE` /
  `OUROBOROS_HOOKS_OFF` escape-hatch spirit carries forward as §2.9's registry escape hatch —
  the property (the owner can always get out) is preserved under a new mechanism, not dropped
  with the old one." ⚑ Verified in the tree: `.claude/settings.json` currently sets
  `"env": {"OUROBOROS_HOOKS_OFF": "1"}`. **Before removing anything, record what that flag's
  current value implies about which hooks are actually live** — a retirement measured against
  hooks that were already off would prove nothing. This is Item 44's first act.
- **Q6 — which tests pin the removed surface?** Verified by grep this pass:
  `tests/integration/test_handoff_gate.py`, `tests/integration/test_worktree_enforcement.py`,
  and `tests/integration/test_deskcheck_gate.py` copy `_lib.py` into a throwaway repo and
  assert on `ALLOW` / `DENY:` / `BLOCK:` lines. They are in `write_scope` for exactly this
  reason (the retrofit rule: "carried because they pin the surface this plan moves").
  `tests/unit/test_capsule.py` and `tests/integration/test_reference_oracle.py` also touch
  `_lib` — **read them and confirm they use only the surviving parser primitives**; if either
  pins a retired clause, stop and widen via a finding, not by assumption.
- **Q7 — clause (e′) and the derived views.** `journal-gate`'s clause (e′) shells out to
  `scripts/handoff.py --check`. Retiring it requires the DERIVED half to have moved to a
  registry query — **bp-150** — which is itself gated on the owner's amendment to
  `role-state-and-scoped-handoff.md` (note §2.7's table). Hence `bp-150` in `depends_on`.
- **Q8 — the deskcheck gate.** `_lib.py:268 verdict_of` and `cmd_gate_check`'s third arm
  (`:508`) enforce the deskcheck verdict — **the third owner-only gate**, which the registry
  note §2.5.2 classifies as "semantically deep but *reversible*; default: owner-by-hand as
  today, **unsigned**". ⚑ The note's §2.6 table does **not** list a deskcheck disposition. ⇒
  **The deskcheck arm of `gate-guard` is NOT retired by this plan** unless the owner's
  amendment says otherwise. If retiring `gate-guard` would remove the deskcheck tooth as a
  side effect, that is a stop-and-raise (§10) — an unnamed guarantee must not be dropped
  because it shared a file with a named one.

**Additional risks or questions surfaced during reading:**

- This is the highest-consequence plan in the family: every item **reduces** enforcement. The
  only thing standing between it and a silent loss of a bright line is bp-147's clause table
  and bp-146's parity harness. Read them first, believe them only where they say `proved`.
- Removing a hook is trivially easy and its consequences are invisible until something slips
  through. Each item must therefore carry a **post-removal demonstration**: the registry-side
  check catching the exact case the removed hook caught, run after the removal, recorded in
  the journal.

## 4. Reconciliation

- `.claude/settings.json` — the five registrations → ⚑ **banner: correction**, one per
  commit. Each removal commit's message names the hook, the note §2.6 row, the parity test's
  node id, and the `schema.md` row marked `proved`. A removal commit that cannot cite all
  four is not lawful under invariant 8.
- `.claude/hooks/_lib.py` — retired clause functions → **banner: correction**, in a second
  commit per hook (§3 Q4), each preceded by a grep proving no consumer remains. `_lib.py`
  itself survives: `parse_front_matter`, `_scalar`, `_normalize_status`, `glob_match`,
  `matches_any`, `git_show_head`, `_split_front_matter`, `repo_root`, `rel`, and
  `cmd_marker` (for `compaction-marker`) all stay.
- `tests/integration/test_{deskcheck_gate,handoff_gate,worktree_enforcement}.py` →
  **banner: correction.** Each assertion pinning a retired tooth is either (a) re-pointed at
  the registry-side replacement, or (b) deleted **with a comment naming the note §2.6 row and
  the replacement test**. ⚑ A deleted assertion with no replacement named is a silently
  dropped guarantee — F4 in miniature.
- `docs/design-notes/agent-workflow.md` §6 and `dn-autopilot-and-delegated-blessing.md` §2.3
  → ⚑ **owner-ratified amendments, NOT this plan's edits.** They are preconditions (§0), not
  work items. The plan reads them to verify; it never writes them.

## 5. Write scope

- `.claude/settings.json` — remove five hook registrations, one per commit; keep
  `PreCompact`/`compaction-marker`; keep the `env`, `statusLine`, and `permissions` blocks
  (permissions entries for retired hooks may be pruned in the same commit as their hook).
- `.claude/hooks/**` — delete the five wrapper scripts and their `_lib.py` clause functions
  after the registrations are gone; **keep** `compaction-marker.sh` and every `_lib.py`
  primitive still imported by `scripts/` and `ops/registry/`.
- `.claude/state/**` — remove `active-plan` (clause (d)'s substrate) **only** after bp-147's
  registry field is proved and `/build`'s writer is re-pointed. ⚑ If `/build`
  (`.claude/commands/build.md`) still writes it, that file is **not** in scope — stop and
  raise.
- `tests/integration/test_deskcheck_gate.py`, `test_handoff_gate.py`,
  `test_worktree_enforcement.py` — carried because they pin the surface this plan moves.
- `tests/integration/test_registry_retirement.py` — the post-removal demonstrations.

**Deliberately OUT of scope:** ⚑ `docs/design-notes/**` — the two amendments are the owner's
and are preconditions, not work. `compaction-marker.sh` and its `_lib.py` support (the one
surviving hook). `ops/registry/**` and `scripts/**` (their work is done by bp-142…bp-148 and
bp-150; if this plan needs to change them, parity was incomplete — stop). `CLAUDE.md` and
`.claude/skills/**` (bp-148). `CONSTITUTION.md`, `eval/golden/**`, `eval/golden.py`.
`.claude/commands/build.md` (see the `.claude/state/**` caveat above).

## 6. Interfaces pinned inline

### 6.1 The disposition table (note §2.6, verbatim)

| hook | guarantee today | disposition |
|---|---|---|
| `gate-guard` (PreToolUse) | owner-only status flips denied pre-hoc | **dissolved.** Status is not file-resident; a flip is a signed event; a hand-edit is ratchet-caught drift |
| `journal-gate` (Stop) | no close on unfinished obligation — clauses (a)–(f) | **dissolved into queries + land-time admission** |
| `session-brief` (SessionStart) | orientation + close-audit baseline | **replaced by query.** Orientation is a registry read; no denial semantics remain |
| `staleness-nudge` (UserPromptSubmit) | derived views drifted | **dissolved.** Views derive from the store on read; there is nothing to go stale |
| `compaction-marker` (PreCompact) | post-compaction turn re-verifies vs journal | **kept — the one surviving hook.** |
| `scope-guard` (PreToolUse) | writes outside `write_scope` denied; foundation denylist | **moved to land-time admission, per-unit level** |

### 6.2 The current registrations (`.claude/settings.json`, verbatim — what is being removed)

```json
"hooks": {
  "SessionStart":     [{ "hooks": [{ "command": ".../session-brief.sh" }] }],
  "UserPromptSubmit": [{ "hooks": [{ "command": ".../staleness-nudge.sh" }] }],
  "PreToolUse":       [{ "matcher": "Edit|Write|MultiEdit",
                         "hooks": [{ "command": ".../scope-guard.sh" },
                                   { "command": ".../gate-guard.sh" }] }],
  "Stop":             [{ "hooks": [{ "command": ".../journal-gate.sh" }] }],
  "PreCompact":       [{ "hooks": [{ "command": ".../compaction-marker.sh" }] }]
}
```

⚑ **`PreCompact` / `compaction-marker` survives untouched.** The end state has exactly one
registration.

### 6.3 The lawfulness test for every removal (invariant 8, verbatim)

> 8. A hook is retired only after a registry-side test proves its guarantee's parity.

Operationally, a removal commit must cite: the hook, the §2.6 row, the parity test node id
(bp-146 Item 33 / bp-147 Item 37), and the `ops/registry/schema.md` row marked `proved`.

### 6.4 The foundation denylist survives the retirement (note §2.6, verbatim)

> The **foundation denylist** (`CONSTITUTION.md`, `eval/golden/**`, `eval/golden.py`) binds
> at admission for every unit at every level, and additionally stays covered by the CI
> ratchet, so it is enforced **twice** with neither enforcement on the write hot path.

⚑ At no point during the staging may the denylist be enforced **zero** times. Item 48 must
demonstrate it is enforced by `land()` **before** `scope-guard` is unregistered.

## 7. Items

### Item 44 — verify the preconditions, and baseline what is actually live

- **Objective:** prove the two amendments landed, the clause table says `proved`, and record
  which hooks are actually firing today.
- **Files:** `tests/integration/test_registry_retirement.py`
- **Acceptance test:** a test (or a recorded check) asserting: `agent-workflow.md` §6 no
  longer names the five hooks as live contracts; `dn-autopilot-and-delegated-blessing.md`
  §2.3 carries the amended flip/enforcement text; `ops/registry/schema.md`'s clause table has
  no row this plan retires marked other than `proved`. Plus a recorded reading of
  `OUROBOROS_HOOKS_OFF` and what it implies (§3 Q5).
- **Falsifier:** ⚑ **an amendment has not landed.** Then this plan is not startable, per §0
  and note §3(1). **Stop; report; retire nothing.** Do not "prepare" the removals in a
  branch — a prepared removal is one merge away from an unlawful one.
- **Invariant(s) it must not violate:** no ratified note is edited, ever.
- **Touches stored data?** No.
- **Parallelizable?** No.  **Depends on:** all of `depends_on`.

### Item 45 — retire `staleness-nudge` (advisory only)

- **Objective:** remove the `UserPromptSubmit` registration and the wrapper.
- **Files:** `.claude/settings.json`, `.claude/hooks/staleness-nudge.sh`,
  `.claude/hooks/_lib.py`, `tests/integration/test_registry_retirement.py`
- **Acceptance test:** the registration is gone; a session start/prompt produces no nudge;
  `uv run pytest -q -m 'not live and not podman and not needs_vault and not needs_restic'`
  green; the commit message cites the four lawfulness elements (§6.3).
- **Falsifier:** the derived views **do** go stale after removal — i.e. some view is not in
  fact derived-on-read. Demonstrate: mutate the tree, read a view, and confirm it reflects
  the change with no regeneration step. Note §2.6's claim is "Views derive from the store on
  read; there is nothing to go stale" — if a committed view still needs regeneration, the
  nudge was load-bearing and its removal is premature.
- **Invariant(s) it must not violate:** invariant 8.
- **Touches stored data?** No — but it **reduces enforcement**; that is this plan's blast
  radius throughout.
- **Parallelizable?** No.  **Depends on:** Item 44.

### Item 46 — retire `session-brief` (no denial semantics)

- **Objective:** remove the `SessionStart` registration; orientation comes from
  `uv run scripts/registry.py status`.
- **Files:** `.claude/settings.json`, `.claude/hooks/session-brief.sh`,
  `.claude/hooks/_lib.py`, `tests/integration/test_registry_retirement.py`
- **Acceptance test:** the registration is gone; `status` prints the same four facts the
  brief printed (plans by status, unswept findings count, open owner questions, the active
  worktree's plan) — assert each is present in the query output; suite green.
- **Falsifier:** ⚑ the brief's **close-audit baseline** (`.claude/state/session-baseline`,
  recorded at SessionStart) is still read by something. `agent-workflow.md` §6 records that
  "`session-baseline` survives only for the SessionStart brief's narration; enforcement does
  not read it" — verify by grep before removing, and if enforcement *does* read it, the
  removal is unsafe and must stop.
- **Invariant(s) it must not violate:** invariant 8.
- **Touches stored data?** Yes — removes `.claude/state/session-baseline` if unused. Grep
  first.
- **Parallelizable?** No.  **Depends on:** Item 45.

### Item 47 — retire `gate-guard`, minus the deskcheck arm

- **Objective:** remove the blessing-flip denial (dissolved: status is not file-resident and
  a hand-edit is ratchet-caught drift), **without** dropping the deskcheck verdict tooth.
- **Files:** `.claude/settings.json`, `.claude/hooks/gate-guard.sh`, `.claude/hooks/_lib.py`,
  `tests/integration/test_deskcheck_gate.py`,
  `tests/integration/test_registry_retirement.py`
- **Acceptance test:** post-removal demonstration — hand-edit a plan's `status:` to `ready`
  in a fixture checkout and show `uv run scripts/registry.py export --check` **red** naming
  that file; hand-edit a note to `ratified` and show the same; then show that a `→ratified`
  registry event without a signature is **rejected** (bp-145). The deskcheck verdict gate
  still denies (`test_deskcheck_gate.py`'s Item-2 assertions still pass).
- **Falsifier:** ⚑ **the deskcheck tooth disappears as a side effect** (§3 Q8). The registry
  note's §2.6 table names no deskcheck disposition, and §2.5.2 keeps the verdict
  "owner-by-hand as today, unsigned". An unnamed guarantee dropped because it shared a file
  with a named one is exactly F4. If the arm cannot be preserved, **stop**.
- **Invariant(s) it must not violate:** invariant 8; the third owner-only gate survives.
- **Touches stored data?** No.
- **Parallelizable?** No.  **Depends on:** Item 46, bp-143 Item 19, bp-145 Item 26.

### Item 48 — retire `scope-guard`, denylist proved first

- **Objective:** remove the pre-hoc write denial, having first demonstrated the foundation
  denylist is enforced by `land()`.
- **Files:** `.claude/settings.json`, `.claude/hooks/scope-guard.sh`,
  `.claude/hooks/_lib.py`, `tests/integration/test_worktree_enforcement.py`,
  `tests/integration/test_registry_retirement.py`
- **Acceptance test:** **in this order** — (1) demonstrate `land()` refusing a
  `CONSTITUTION.md` change and an out-of-scope path, with the exact offending diff; (2)
  *then* remove the registration; (3) re-demonstrate (1) still holds with the hook gone; (4)
  suite green. `test_worktree_enforcement.py`'s worktree-locality assertions are re-pointed
  at the registry's `active_in_checkout` (bp-147 Item 38) or deleted with a comment naming
  the replacement.
- **Falsifier:** ⚑ **the denylist is enforced zero times at any moment of the staging**
  (§6.4). Also: a mis-scoped write now reaches a commit that `land()` does not examine —
  i.e. the "landing" path is not actually on the route to consequence (bp-146 §3 Q3). If
  work can reach `main` without passing `land()`, the guarantee did not move, it evaporated.
- **Invariant(s) it must not violate:** invariant 8; the denylist binds at every level; the
  honest loss (the mid-flight signal) is **stated**, never claimed away.
- **Touches stored data?** No — but this is the single largest enforcement reduction in the
  family.
- **Parallelizable?** No.  **Depends on:** Item 47, bp-146 Item 33.

### Item 49 — retire `journal-gate`, clause by clause

- **Objective:** remove the Stop gate last, only after every clause row in `schema.md` reads
  `proved`.
- **Files:** `.claude/settings.json`, `.claude/hooks/journal-gate.sh`,
  `.claude/hooks/_lib.py`, `.claude/state/**`,
  `tests/integration/test_deskcheck_gate.py`, `tests/integration/test_handoff_gate.py`,
  `tests/integration/test_registry_retirement.py`
- **Acceptance test:** for **each** of clauses (a), (b), (b2), (c), (d), (e′), (f): a
  post-removal demonstration that the registry side refuses the case the clause refused,
  recorded in the journal with the command and its output. `.claude/state/active-plan` is
  removed only if `/build` no longer writes it (else stop, §5). Suite green;
  `.claude/settings.json` contains exactly one registration (`PreCompact`).
- **Falsifier:** ⚑ **F4** — "any row of §2.6's table whose hook is retired before a
  registry-side test proves the guarantee holds — or a post-retirement incident that today's
  hook would have caught and the registry did not." Clause (f) is the one to watch: it is
  now a schema requirement on the seal event, so demonstrate that a seal without the five
  answers is refused **at submission**, not merely warned about.
- **Invariant(s) it must not violate:** invariant 8 for every clause; `compaction-marker`
  untouched; the honest loss ("a session that never lands can leave a dirty tree that no gate
  ever examined") is recorded in the seal, not hidden.
- **Touches stored data?** Yes — removes `.claude/state/active-plan`. Verify `/build` first.
- **Parallelizable?** No.  **Depends on:** Item 48, bp-147 Item 39, bp-150.

## 8. Math carried explicitly

N/A — no mathematical object implemented. This plan removes registrations and code; its
obligation is parity evidence, discharged by bp-146/bp-147's tests and this plan's
post-removal demonstrations.

## 9. Non-goals

- ⚑ **No amendment to any ratified design note.** They are preconditions, owner hand edits.
- ⚑ **No `compaction-marker` change.** It is the one surviving hook (note §2.6).
- ⚑ **No deskcheck-gate retirement** (§3 Q8) — unnamed by the disposition table, and §2.5.2
  keeps the verdict owner-by-hand and unsigned.
- **No new enforcement logic.** If this plan must implement a check, parity was incomplete —
  stop.
- **No `_lib.py` deletion.** Its parser and matcher primitives have three live consumers.
- **No skills, template, or `CLAUDE.md` edit** — bp-148.
- **No `scripts/handoff.py` / `scripts/board.py` edit** — bp-150.
- **No change to `palace bless`** (`scripts/palace.py`) — the owner-operated flip is out of
  the note's scope and `tests/unit/test_bless.py` pins it.
- **No removal of the `OUROBOROS_HOOKS_OFF` escape-hatch spirit** — it carries forward as
  §2.9's registry hatch (note §2.6).

## 10. Stop-and-raise conditions

- ⚑ **Either owner amendment has not landed** (§0) — stop, report, retire nothing, prepare
  nothing.
- Any `schema.md` clause row is not `proved` — stop for that hook; continue only with hooks
  whose rows are.
- Retiring `gate-guard` would drop the deskcheck arm (§3 Q8) — stop.
- Work can reach `main` without passing `land()` (Item 48's falsifier) — stop; the guarantee
  did not move.
- `/build` still writes `.claude/state/active-plan` — stop before removing it;
  `.claude/commands/build.md` is out of scope.
- `tests/unit/test_capsule.py` or `tests/integration/test_reference_oracle.py` turns out to
  pin a retired clause (§3 Q6) — file a finding and stop; do not widen the scope by
  assumption.
- The owner reads §4 as reserving `.claude/settings.json` to his own hand (§3 Q3) — park the
  removal items, prepare the diffs, and continue with the test re-pointing.
- Any blessing this plan would have to perform — it must not.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| Who edits `.claude/settings.json` | **the builder**, one hook per commit, each an owner-visible diff; owner control is item-by-item approval + one-commit revert | owner-only edits — §4's "hand-editing" language reads as rollout narration, and a builder-prepared-but-unapplied diff is a merge away from an unlawful retirement anyway | The owner rules that §4 reserves the file; prerequisite: an owner ruling |
| Deleting retired `_lib.py` clause functions | **second commit per hook**, after a grep proves no consumer | deleting in the same commit — makes a revert unsurgical and risks breaking `scripts/board.py`/`handoff.py`/`ops/registry/**` | — (this is the recorded procedure, not a deferral) |
| The deskcheck arm of `gate-guard` | **kept** — unnamed by §2.6, and §2.5.2 keeps the verdict owner-by-hand and unsigned | retiring it with the rest — an unnamed guarantee dropped as a side effect is F4 | The owner's amendment names a deskcheck disposition |
| `.claude/state/session-baseline` | removed with `session-brief` **only if** grep shows no enforcement reads it | removing it blind — `agent-workflow.md` §6 says enforcement does not read it, but the code is the authority | Grep finds a consumer |
| `compaction-marker` retention | **kept** (the note's own parked row) | retiring it — "retiring it buys nothing (it clogs nothing) and loses a real guarantee" | Harness-level compaction hooks change, or the hook fires zero times over a measured month |

## 12. Dependency & ordering summary

**Within the plan.** Item 44 (verify preconditions; retire nothing) → Item 45
(`staleness-nudge`, advisory) → Item 46 (`session-brief`, no denial semantics) → Item 47
(`gate-guard`, minus the deskcheck arm) → Item 48 (`scope-guard`, denylist proved first) →
Item 49 (`journal-gate`, clause by clause). ⚑ **Blast-radius ordering is inverted from the
usual rule and deliberately so:** every item *reduces* enforcement, so the safest order is
least-protective-first, ending with the two guards that carry the bright lines. Each removal
is two commits (registration, then dead code), so any single step reverts cleanly.

**Across plans.** `depends_on` carries six plan ids **and two owner amendments**:
`owner-amendment:agent-workflow-note` (`docs/design-notes/agent-workflow.md` §6/§9/§2/§10)
and `owner-amendment:autopilot-and-delegated-blessing-note`
(`docs/design-notes/dn-autopilot-and-delegated-blessing.md` §2.3). Those two are **owner hand
edits to ratified notes**; no agent performs them, and until both land this plan is not
startable (note §3(1): "Until each amendment lands, the text it amends governs and the
corresponding hook stays"). `parallelizable_with: []` — it is the terminal plan of the
family and shares surfaces with nothing that could run beside it. `bp-138`/`bp-139` are
independent of this whole family (note §3(5)).
