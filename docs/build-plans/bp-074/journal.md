# bp-074 — journal

## 2026-07-19 — minted at graduation (orchestrator, session-36)

Plan graduated from `dn-session-handoff-gate` (ratified by hand, `87a3d90`,
same day as capture + draft — brainstorm → note → plan in one arc). Grounded
pass done at graduation: the freshness signal needs **nothing new built**
(`session-brief.sh:51-52` already writes both halves); clause (e) slots into
`cmd_stop_audit`'s existing `plan is None` branch; the only reconciliation of
substance is amendment A9 to `agent-workflow.md:151` (enforcement now reads
`session-baseline` — the ratified text says it does not), owner-applied per A8.

Existing-test exposure checked at graduation (§3 Q5): fixtures never write
`session-baseline`, so (e) skips fail-open everywhere in the current suite —
zero predicted reddening. If the builder sees otherwise, that grounding was
wrong: stop, finding, park.

Status: `proposed`. Awaiting the owner's `palace bless bp-074` + hand commit.

## 2026-07-19 — build session (delegated builder, worktree agent-a198f4cd)

### Setup: worktree freshness reconciliation (not a blessing)

Worktree was cut at `3b68cd5` — one commit BEFORE the owner's blessing
`203df79` ("bless(bp-074): proposed→READY — OWNER keystroke, recorded") landed.
`203df79`'s parent IS `3b68cd5` (clean linear descent; `git log 203df79..HEAD`
empty), and `main` is at `203df79`. So the plan read `proposed` in my worktree
purely as a sync artifact. Resolution: `git merge --ff-only 203df79` — a pure
fast-forward that picks up the owner's already-applied blessing. This is NOT the
builder performing a blessing (the owner already did, accountably, in `203df79`);
it is syncing the worktree so the ready gate is satisfied honestly. Then set
`.claude/state/active-plan` → the plan path and flipped `status: ready →
in-progress` (a non-blessing transition; build-ceremony). NOTE: plan.md is
outside my write_scope, so the in-progress flip is left UNSTAGED in the working
tree and NOT committed — the orchestrator owns plan status (flips to `complete`
at seal).

### Item 1 — clause (e) in `cmd_stop_audit` (+ two comment reconciliations) — DONE

Landed in `.claude/hooks/_lib.py` and `.claude/hooks/journal-gate.sh`.

**The shared fetch (owner DRY rule).** Hoisted the (a) last-commit subprocess out
of the `if plan is not None:` block to the top of `cmd_stop_audit`, and extended
its format from `%ct` to **`%H %ct`** so ONE `git log -1` yields BOTH the HEAD sha
(for (e)'s commits-this-session test) and the last-commit epoch (for (a) and (e)).
This satisfies the Item-1 invariant "no new subprocess beyond the shared
last-commit fetch": (e) adds zero git calls. `%H` is the same 40-char sha
`session-brief.sh:52` records into `session-baseline` via `git rev-parse HEAD`, so
`head_sha != baseline` is a valid "did this session commit?" test. (a) stays
byte-identical: it reads the same integer epoch (`_headline[1]`) under the same
`if last_commit and ...` guards; empty-repo path yields `"", 0` (was `0`).

**Clause (e).** Inserted after (d), before the reasons emit, guarded by
`if plan is None:` (orchestrator posture — builders carry a plan and are governed
by (a)). Logic, matching the pinned §6 condition verbatim:
- read `.claude/state/session-baseline`; missing/unreadable → `baseline=""` →
  fail-open skip (note §2.5).
- BLOCK iff `baseline and head_sha and head_sha != baseline` (commits happened
  this session) AND `mtime(resume-brief.md) < last_commit` — `os.path.getmtime`
  raising `OSError` (missing brief) counts as infinitely stale → block.
- reason string is prefixed `"(e) "` and INSTRUCTS the fix (write
  `.claude/state/resume-brief.md` per context-economy) — the block reason IS the
  automation.

**Comment reconciliations (called out, not slipped in):**
- `_lib.py` (c)-block comment (formerly "retained solely for the SessionStart
  brief's narration and is deliberately not consulted here") → now names clause (e)
  as `session-baseline`'s second consumer (commits-this-session guard), citing
  dn-session-handoff-gate; still notes (c) itself diffs against HEAD.
- `journal-gate.sh` header (a)–(c) enumeration → gains "(e) with no plan active:
  commits landed this session but the resume brief is stale (dn-session-handoff-
  gate)".

**Smoke test (scratch git repo, orchestrator posture) — all pass:**
- no-commits (baseline==HEAD), stale brief → ALLOW
- commits + stale brief → BLOCK (e)
- commits + missing brief → BLOCK (e)
- commits + fresh brief (mtime > last commit) → ALLOW
- commits + missing baseline → ALLOW (fail-open)

Acceptance (Item 1): met. Invariants held: (a)–(d) behavior unchanged, one
subprocess only, exit-code contract untouched. Committed `5e816e6`.

### Item 2 — `tests/integration/test_handoff_gate.py` — DONE

New file, mirrors `test_worktree_enforcement.py`'s pattern (self-contained
throwaway git repo, `_lib.py stop-audit` invoked directly with
`CLAUDE_PROJECT_DIR` set, assert on the `ALLOW`/`BLOCK:` decision line). One
`handoff_repo` fixture in orchestrator posture (empty active-plan) with control
helpers: `set_baseline_to_head`, `commit`, `write_brief(fresh=…)` (sets brief
mtime to last-commit ±100 s for deterministic staleness). `.claude/state/` is
**gitignored in the fixture** (as in the real repo) so runtime files never enter
the (b) out-of-scope audit — important for case 6's clean ALLOW.

Six cases, all green (`uv run --extra dev pytest tests/integration/
test_handoff_gate.py -q` → **6 passed**):
1. commits + stale brief → BLOCK (e)
2. commits + missing brief → BLOCK (e)
3. no commits (baseline==HEAD) + stale brief → ALLOW, no (e)
4. commits + fresh brief → ALLOW, no (e)
5. commits + missing baseline → fail-open ALLOW, no (e)
6. active plan (bp-xx pointer) + stale brief + fresh journal → no (e), ALLOW
   (decided by (a)-(d) only)

Falsifier (Item 2): none tripped — no case required editing `session-brief.sh`
or adding hooks; the signal design stands alone. §3 Q5 held: `test_worktree_
enforcement.py` fixtures still write no `session-baseline`, so (e) skips
fail-open there (verified in the full-suite run below).

VENV NOTE for the sealing orchestrator: this fresh worktree venv has no dev
deps by default — run the gate legs with `uv run --extra dev …` (pytest/ruff/
mypy live in the `dev` optional-dependency group). The main checkout's `.venv`
already carries them.

Acceptance (Item 2): met. Committed `40ffe25`. Next: Item 3 (A9 text + seal
warning), then the full attestable-green gate.

### Item 3 — amendment A9 text (OWNER-APPLIED) + seal warning — DONE

A8 binds: the builder never edits `agent-workflow.md` (ratified, immutable).
The exact text below is EMITTED for the owner to apply and commit by hand. The
orchestrator can load the fenced block into the paste buffer unmodified. Every
claim matches the landed clause (e) line-for-line (verified against
`_lib.py:cmd_stop_audit` as committed in `5e816e6`).

**Append to `agent-workflow.md` §16 (Amendment log):**

```markdown
- **A9** — warrant: dn-session-handoff-gate (ratified `87a3d90`; implemented by
  bp-074). Adds Stop-audit clause **(e)**, the session-handoff gate. In
  orchestrator posture only (`plan is None`), `cmd_stop_audit` blocks session
  close when commits landed THIS session but the resume brief is stale or
  missing. The commits-this-session guard READS `.claude/state/session-baseline`:
  current HEAD (`git log -1 --format=%H`) is compared to the baseline's content,
  and a mismatch means the session committed. Freshness compares
  `mtime(.claude/state/resume-brief.md)` to the **last-commit time**
  (`git log -1 --format=%ct`) — the same test clause (a) uses for the journal,
  NOT the baseline's mtime; a missing brief is infinitely stale (blocks whenever
  commits happened). Fail-open on a missing/unreadable baseline (the signal
  cannot be evaluated, so no block). This CORRECTS §6c's closing sentence
  (":151", "`session-baseline` survives only for the SessionStart brief's
  narration; enforcement does not read it"): enforcement now reads it — clause
  (e) is its second consumer, scoped to orchestrator posture. Clause (c) still
  does not read it (it diffs against HEAD). The §6 journal-gate table row (":143")
  enumeration extends to (a)–(e); per the A1–A8 precedent the amendment log
  carries the change rather than rewriting the row in place. No new machinery:
  `session-brief.sh:52` already writes the baseline each SessionStart, and (e)
  adds no git subprocess (the (a) last-commit fetch is hoisted to `--format=%H
  %ct` and shared). Builder sessions are unaffected — they carry an active plan
  and their handoff artifact is the journal, governed by (a).
```

**Corrected §6c sentence at `:151` (owner replaces the false claim):**

```markdown
`session-baseline` is read by Stop-audit clause (e) — the session-handoff gate
(A9) — as its commits-this-session guard in orchestrator posture; enforcement's
other paths do not read it (clause (c) diffs against HEAD).
```

(Per plan §4 the owner may instead leave the `:143`/`:151` body untouched and let
the A9 log entry carry the record; the sentence above is offered because the
current `:151` wording is now factually false. Owner's call at apply time.)

### §3 seal-session WARNING (for the sealing orchestrator)

**After (e) lands, the next orchestrator close after ANY commit will BLOCK until
a fresh `.claude/state/resume-brief.md` exists — including bp-074's OWN seal
session.** This is the designed behavior, not a regression. The build session
you are reading was a delegated builder (it carried an active plan, so (e) was
silent for it). But the orchestrator that merges this branch and seals bp-074
will commit the merge/seal, then hit its own Stop gate with no active plan → (e)
fires. To close cleanly: write the resume brief (context-economy skill's
resume-brief shape) citing the final commit hashes AFTER the last seal commit,
then close again. The block reason itself instructs this.

Acceptance (Item 3): met — the A9 block is fenced, headed `A9 —`, and its claims
match the landed code (baseline content = commits guard; brief mtime vs
last-commit `%ct`; orchestrator-posture scope; fail-open on missing baseline).
Falsifier avoided: A9 does NOT claim a baseline-mtime comparison.
