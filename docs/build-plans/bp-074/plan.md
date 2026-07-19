---
type: build-plan
id: bp-074
status: ready
design_ref:
  - docs/design-notes/session-handoff-gate.md
contract: builder
write_scope:
  - .claude/hooks/_lib.py
  - .claude/hooks/journal-gate.sh
  - tests/integration/**
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 120k
  actual: null
depends_on: []
parallelizable_with: []
created: 2026-07-19
updated: 2026-07-19
links:
  - docs/brainstorms/handoff-automation.md
  - docs/design-notes/agent-workflow.md
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — Stop-audit clause (e): the session-handoff gate

> **Every section below is required.** A section that does not apply is marked
> `N/A — <one-line reason>`, never silently omitted.

## 0. Mode & provenance

Graduated 2026-07-19 from `dn-session-handoff-gate` (ratified `87a3d90`) by a
grounded planning pass: investigation and planning produced this; implementation
proceeds item-by-item on owner approval. Authority-to-act is the owner's
blessing at `proposed → ready` (`palace bless bp-074` + hand commit); no agent
flips readiness.

## 1. Objective

The Stop audit refuses to close an orchestrator session that committed work but
left `.claude/state/resume-brief.md` stale — clause (e) in `cmd_stop_audit`.

## 2. Context manifest

1. `docs/build-plans/bp-074/plan.md` — this plan, whole.
2. `docs/design-notes/session-handoff-gate.md` — the ratified decision; §2 is
   the contract this plan implements verbatim.
3. `.claude/hooks/_lib.py` — the audit to extend; read `cmd_stop_audit`
   (`:571-707`) and `active_plan_path` (`:280-296`) whole.
4. `.claude/hooks/journal-gate.sh` — the Stop wrapper (unchanged in logic; its
   header comment gains (e)).
5. `.claude/hooks/session-brief.sh` — writes both halves of the freshness
   signal (`:46-52`); read-only context, not in write_scope.
6. `tests/integration/test_worktree_enforcement.py` — the fixture pattern to
   mirror (invoke `_lib.py stop-audit` in fixture repos with
   `CLAUDE_PROJECT_DIR` set).
7. `docs/design-notes/agent-workflow.md` §6 + amendments (`:280-286`) —
   read-only; the A9 text Item 3 drafts amends it (owner-applied).

## 3. Investigation & grounding

- **Q1 — where does clause (e) insert?** After (d) (`_lib.py:681-701`), before
  the reasons emit (`:703-707`). `cmd_stop_audit` is a reasons-accumulator;
  every clause appends a prefixed string and the tail prints
  `BLOCK: ...`/`ALLOW` — `_lib.py:571-707`.
- **Q2 — how is "orchestrator posture" detected?** `active_plan_path()` returns
  `None` for a missing **or empty** pointer (`_lib.py:286-296`; the empty-file
  case is pinned by `test_d_no_pointer_is_no_plan_not_main_fallback`,
  `tests/integration/test_worktree_enforcement.py:192`). The existing
  `plan is None` branch is `_lib.py:617`.
- **Q3 — is the freshness signal really written every session?**
  `session-brief.sh:51-52` writes `git rev-parse HEAD` into
  `.claude/state/session-baseline` on every SessionStart; the hook is
  registered matcher-less (`.claude/settings.json:4-10`), so it fires for all
  session sources. The resume/clear rewrite porosity is accepted in the note
  (§2.6, third bullet).
- **Q4 — how to get last-commit time?** The exact pattern exists at
  `_lib.py:580-591` (clause (a)): `git log -1 --format=%ct`, `last_commit = 0`
  on failure, and every use guarded by `if last_commit and ...` (empty-repo
  safe). Reuse it — do not re-implement (owner DRY rule); hoisting the
  fetch so (a) and (e) share one subprocess call is the preferred shape.
- **Q5 — do existing tests redden?** No. The only stop-audit tests are in
  `test_worktree_enforcement.py`; its fixtures create `.claude/state/` with
  `active-plan` pointers only — **no fixture writes `session-baseline`**
  (`two_worktrees` at `:106-120`, `bleed_fixture` at `:227+`). With the
  baseline missing, (e) skips fail-open (note §2.5), so the MAIN-checkout
  orchestrator-posture cases (`test_d`, bleed controls) still print `ALLOW`.
  Worktree cases run with a plan active → (e) silent. Carried in write_scope
  anyway because it pins the audit surface this plan extends.
- **Q6 — does enforcement read `session-baseline` today?** No — deliberately:
  `_lib.py:645-646` ("retained solely for the SessionStart brief's narration
  and is deliberately not consulted here") and agent-workflow §6c
  ("`session-baseline` survives only for the SessionStart brief's narration;
  enforcement does not read it", `:151`). Clause (e) makes enforcement its
  second consumer — a **correction to ratified text**, carried as amendment A9
  (Item 3), never a quiet edit. The next free amendment number is A9
  (ledger runs A1–A8, `agent-workflow.md:280-286`; A7 exists as a proposal,
  oq-0003).

**Additional risks or questions surfaced during reading:** after (e) lands, the
orchestrator session that *built* it is unaffected (builder sessions carry an
active plan), but the **next orchestrator close after any commit will block
until a fresh brief exists — including the seal session of this very plan.**
That is the designed behavior, not a bug; the builder's journal must warn the
sealing orchestrator.

## 4. Reconciliation

- `docs/design-notes/agent-workflow.md:151` — "``session-baseline`` survives
  only for the SessionStart brief's narration; enforcement does not read it."
  → **banner: correction (amendment A9, owner-applied)**: A9 records that (e)
  consults the baseline (content = commits-this-session guard; the brief's
  mtime is compared to last-commit time), scoped to orchestrator posture;
  §6's journal-gate table row (`:143`, which still enumerates only (a)–(c))
  stays untouched — amendments append, per A1–A8 precedent. The note is
  `ratified` and A8-immutable, so the builder EMITS the exact A9 text (Item 3);
  the owner applies and commits it by hand.
- `_lib.py:645-646` — the "deliberately not consulted here" comment → **code
  correction carried by Item 1** (called out, not slipped in): the comment is
  updated to name (e) as the baseline's second consumer, citing
  dn-session-handoff-gate.
- `.claude/hooks/journal-gate.sh:2-7` — header enumerates (a)–(c) → **cross-ref:
  extension**: header sentence gains "(e) with no plan active: commits landed
  this session but the resume brief is stale" (in write_scope, Item 1).

## 5. Write scope

`.claude/hooks/_lib.py` (the clause + the :645 comment correction),
`.claude/hooks/journal-gate.sh` (header comment only — no logic change),
`tests/integration/**` (new `test_handoff_gate.py`;
`test_worktree_enforcement.py` carried because it pins the stop-audit surface
this plan extends — findings 0071/0072 rule).

Deliberately OUT: `docs/design-notes/agent-workflow.md` (ratified,
A8-immutable — A9 is owner-applied), `session-brief.sh` (the signal it writes
is already sufficient), `CLAUDE.md` (not licensed by the note),
`.claude/state/**` (runtime, gitignored), the foundation denylist as always.

## 6. Interfaces pinned inline

The block condition (dn-session-handoff-gate §2.2, verbatim):

```
BLOCK  iff  HEAD ≠ content(.claude/state/session-baseline)     # commits happened THIS session
       and  mtime(.claude/state/resume-brief.md) < last-commit time (git log -1 %ct)
```

with: missing `resume-brief.md` = infinitely stale (blocks whenever commits
happened); missing/unreadable `session-baseline` = skip, fail-open (§2.5);
clause guarded by `plan is None`.

Baseline writer (`session-brief.sh:52`) — content is `git rev-parse HEAD`
output, one hex line plus newline; strip before comparing:

```bash
git -C "$ROOT" rev-parse HEAD > "$ROOT/.claude/state/session-baseline" 2>/dev/null || true
```

Orchestrator detection (`_lib.py:286-296`): `active_plan_path() -> str | None`,
`None` on missing/unreadable/empty pointer.

Last-commit fetch to reuse (`_lib.py:580-591`):

```python
last_commit = int(subprocess.run(["git", "log", "-1", "--format=%ct"],
    capture_output=True, text=True, cwd=ROOT, check=True).stdout.strip() or "0")
# ... except Exception: last_commit = 0 ; every use guarded: if last_commit and ...
```

Decision emit contract (`_lib.py:703-707`): append to `reasons`, prefixed
`"(e) "`; the tail prints `BLOCK: `+joined reasons or `ALLOW`, exit 0. The .sh
wrapper maps `BLOCK:` → exit 2 with the reason on stderr
(`journal-gate.sh:42-45`). The (e) reason text must instruct the fix — write
`.claude/state/resume-brief.md` per the context-economy skill — because the
block reason IS the automation (note §2.2).

Test-fixture invocation pattern (`test_worktree_enforcement.py:263-282`):
run `python3 <fixture>/.claude/hooks/_lib.py stop-audit` with
`CLAUDE_PROJECT_DIR` in env; assert on `ALLOW`/`BLOCK:` prefix of stdout.

## 7. Items

### Item 1 — clause (e) in `cmd_stop_audit` (+ the two comment reconciliations)

- **Objective:** implement the pinned block condition inside the `plan is None`
  path, fail-open on missing baseline, reusing the (a) last-commit fetch.
- **Files:** `.claude/hooks/_lib.py`, `.claude/hooks/journal-gate.sh` (header
  comment).
- **Acceptance test:** in a scratch fixture repo (no active plan): baseline ≠
  HEAD + missing brief → `stop-audit` prints `BLOCK:` containing `(e)`;
  `touch` a brief newer than the last commit → `ALLOW`; delete
  `session-baseline` → `ALLOW`. Full suite green
  (`uv run pytest` green gate) — zero existing-test reddening (§3 Q5).
- **Falsifier:** any `test_worktree_enforcement.py` case reddens (Q5 grounding
  was wrong), or (e) fires with a plan active / on a no-commit session
  (scope key or commits-guard implemented wrong).
- **Invariant(s) it must not violate:** clauses (a)–(d) byte-identical in
  behavior; fail-open fail-loud posture; exit-code contract of the wrapper;
  no new subprocess beyond the shared last-commit fetch.
- **Touches stored data?** No.
- **Parallelizable?** No. **Depends on:** none.

### Item 2 — integration tests: `tests/integration/test_handoff_gate.py`

- **Objective:** pin (e)'s six behaviors from the note as regression tests in
  the established fixture pattern.
- **Files:** `tests/integration/test_handoff_gate.py` (new).
- **Acceptance test:** six cases pass — (1) block on commits+stale-brief,
  (2) block on commits+missing-brief, (3) allow on no-commits (baseline ==
  HEAD, brief stale), (4) allow on fresh brief (mtime > last commit),
  (5) fail-open allow on missing baseline, (6) silent under an active plan
  (a worktree fixture with pointer set and a deliberately stale brief still
  decides by (a)–(d) only). `uv run pytest tests/integration/ -q` green.
- **Falsifier:** a case cannot be expressed without modifying
  `session-brief.sh` or adding hooks to the fixture — would reveal the signal
  design does not stand alone; file a `spec-defect` finding and park.
- **Invariant(s) it must not violate:** fixtures self-contained under
  `tmp_path`; no test reads the real repo's `.claude/state/**`.
- **Touches stored data?** No.
- **Parallelizable?** No. **Depends on:** Item 1.

### Item 3 — emit amendment A9 text (owner-applied) + journal warning

- **Objective:** draft the exact A9 amendment text (correction to
  `agent-workflow.md:151` + the (e) enumeration entry, warrant: this plan's
  design_ref) into the journal as a copy-pasteable block, and record the §3
  "next orchestrator close will block" warning for the sealing session.
- **Files:** `docs/build-plans/bp-074/journal.md` (auto-granted).
- **Acceptance test:** the journal contains a fenced block headed `A9 —` whose
  claims match the landed code's behavior line-for-line; the orchestrator can
  load it into the owner's paste buffer unmodified.
- **Falsifier:** the A9 text asserts behavior the landed clause does not have
  (e.g. claims a baseline-mtime comparison — the design uses last-commit time).
- **Invariant(s) it must not violate:** A8 — the builder never edits
  `agent-workflow.md`; the amendment is applied and committed by the owner.
- **Touches stored data?** No.
- **Parallelizable?** Yes (after Item 1). **Depends on:** Item 1.

## 8. Math carried explicitly

N/A — no mathematical object implemented (an mtime/epoch comparison is not one).

## 9. Non-goals

- No brief-*quality* checking (parked in the note; existence+freshness only).
- No cockpit seal-motion keybind (parked in the note).
- No change to `session-brief.sh` — the signal is already written.
- No new hook script and no new Stop entry — (e) rides `journal-gate.sh`.
- No edit to `agent-workflow.md` or `CLAUDE.md` by the builder.
- No enforcement for commit-less sessions (accepted porosity, note §2.6).

## 10. Stop-and-raise conditions

- Any blessing the builder would have to perform — including applying A9 —
  stop; it is owner-only.
- An existing enforcement test reddens beyond §3 Q5's prediction — stop, file
  a `spec-defect` finding (the grounding was wrong), park the item.
- The fixture pattern cannot express a case without touching out-of-scope
  files — `spec-defect` finding, park (Item 2 falsifier).
- Owner-level question → park the criterion with a re-entry condition and
  continue; never block on the owner.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| Cockpit seal-motion keybind | Manual ceremony at unit boundaries | `palace` verb now (premature — ceremony not yet felt in real use) | Manual seal→brief proves annoying in cockpit use (note, parked) |
| Brief-quality checking | Existence+freshness only | LLM/heuristic prose judge (not trusted; note §1) | Fresh-but-useless briefs observed at resume — fresh-agent test fails despite gate passing |
| Commit-less-session enforcement | Not enforceable; discipline covers | Blocking every close (would spam pure-chat sessions) | A mechanical "meaningful uncommitted work" signal emerges |

## 12. Dependency & ordering summary

Item 1 → Item 2 (tests exercise the landed clause); Item 3 after Item 1
(text must match landed behavior), parallel with Item 2. Single session,
blast radius uniformly low (one enforcement-lib clause + tests + journal
text; no stored data, no external effects). No cross-plan dependencies; not
parallelizable with other plans (touches the shared enforcement lib every
worktree inherits).
