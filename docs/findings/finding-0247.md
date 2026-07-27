---
type: finding
id: finding-0247
status: open
created: 2026-07-27
updated: 2026-07-27
links:
  - docs/build-plans/bp-126/plan.md
  - docs/build-plans/bp-126/journal.md
  - docs/build-plans/bp-127/plan.md
  - docs/design-notes/role-state-and-scoped-handoff.md
  - docs/design-notes/session-handoff-gate.md
  - docs/findings/finding-0244.md
  - docs/findings/finding-0245.md
  - docs/findings/finding-0246.md
  - .claude/hooks/_lib.py
  - .claude/hooks/session-brief.sh
  - scripts/handoff.py
  - tests/integration/test_handoff_gate.py
ftype: discovery
origin_plan: orchestrator
route: orchestrator
resolution: null
---

# The independent pre-merge audit of bp-126 — the cutover holds, finding-0246's silencing half is
# confirmed PRE-EXISTING by execution, and one new fail-CLOSED path can wedge every orchestrator close

## What

An independent auditor (not the builder) stress-tested bp-126's delivered diff on branch
`worktree-agent-a7200bccdd41047b0` (3 commits on base `f9cfe4f`), read-only over the delivered
work. Every claim below marked **[EXEC]** was reproduced by running it; **[INSP]** means inspected
only. **Verdict: MERGE WITH CONDITIONS.** The cutover is correct, atomic, and better than the
clause it replaces on every axis measured. Two things are owed after merge, neither of them a
reason to hold the diff.

## 1. finding-0246 — reproduced without `claude -p`, and the halves separated

Driving SessionStart directly (`bash .claude/hooks/session-brief.sh --standalone`, which is
exactly what `.claude/settings.json` registers for that event) in throwaway repos. No nested
`claude` invocation was used anywhere in this audit.

**[EXEC] Failure 1 — silencing — reproduced against clause (e′):**

```
1. parent SessionStart      baseline: content=3fc8633d mtime=1785133101
2. close                    BLOCK: (e′) … journal.md carries no entry from this session …
3. nested SessionStart      baseline: content=9bba1279 mtime=1785133102
4. close (nothing else changed)   ALLOW
```

**[EXEC] Failure 1 is PRE-EXISTING — reproduced identically against the BASE commit's clause (e)**,
extracted verbatim from `f9cfe4f`:

```
2. close                    BLOCK: (e) … the resume brief is stale or missing …
3. nested SessionStart      baseline content reset to HEAD
4. close                    ALLOW      (brief mtime still epoch 1 — untouched)
```

The block was laundered, not satisfied, under **both** clauses. The builder's claim that the
silencing half predates bp-126 is **confirmed by execution**, not merely by reading.

**[EXEC] Failure 2 — spurious arming — reproduced, and it is genuinely new:** a journal entry
written honestly during the session, followed by a nested SessionStart and a later commit, blocks:
`ALLOW → BLOCK`, with the entry never having gone stale. **[INSP]** the base `_lib.py` reads
`session-baseline`'s *content* only (`grep getmtime` shows the three mtime reads are on plan
journals and the brief, never on the baseline), so (e) could be silenced but never spuriously
fired. Check 2's mtime key is what adds this path.

### Is it merge-blocking? No — and (e′) is strictly better than the clause it replaces.

| axis | clause (e) | clause (e′) |
|---|---|---|
| launderable by a nested SessionStart | **yes** [EXEC] | **yes, identically** [EXEC] — no worse |
| false positives | every post-write commit re-armed it: **108 raw / 99 fork-deduped firings over 8 days** (the measurement in `finding-0244`) | one new path (nested-probe-then-commit), and the re-arming class is **gone** [EXEC, mutation C] |
| dischargeable | circular — the demanded content cited commits that did not yet exist | one mechanical step, **converges** [EXEC] |

A gate that can be silenced by an ordinary agent action is a weak gate, and the "false assurance"
worry is real — but that assurance was already false before this diff, and merging does not make it
falser. Holding bp-126 would preserve the *worse* clause while fixing nothing. **Merge, and take
the fix as a follow-on plan.** The honest interim statement `finding-0246` asks for is correct and
should be recorded: *the session-handoff gate is defeated by any nested `claude` invocation in the
same worktree, and always has been.*

### ⚑ Can bp-127 be built next? Yes for Items 15/16; F2 needs one mechanical containment first.

**[INSP]** bp-127 §3 Q3 grounds the F2 spawn as the CLI *"invoked in-tree"*; Item 17's acceptance
spawns a live agent and appends a MEASURED row to `readings.md`. An in-tree spawn fires SessionStart
in the same worktree, so **running F2 as currently specified would silently launder the gate** for
the session running it — and a drill that disarms the gate it is validating produces a green result
that means nothing. `finding-0246`'s re-entry condition is therefore correct as written.

It does **not** need the design ruling first. F1b (Item 15) and F1c (Item 16) are untouched by this
and are the plan's own stated prerequisites for F2. The cheapest sufficient containment for F2 is
mechanical and needs no note change: **snapshot `.claude/state/session-baseline` (content *and*
mtime) before the spawn and restore it after** — `handoff_drill.py` already owns the spawn, so this
is local to the harness. Candidates worth checking but not verified here: spawning with the child's
cwd/`CLAUDE_PROJECT_DIR` outside the repo, or with SessionStart hooks disabled. Add the containment
as an explicit Item 17 invariant and F2 is safe to build before the (a)/(b) ruling lands.

## 2. ⚑ NEW — the fail-open invariant is not fully met: a crashing generator wedges every close

This is the one defect the seal does not mention, and it is mine, not the builder's.

`_handoff_is_stale` returns `proc.returncode == 1` `[.claude/hooks/_lib.py]`. **Python exits 1 on
any unhandled exception**, which is therefore indistinguishable from the generator's "STALE" signal.

**[EXEC]** in a throwaway repo, each with a genuinely stale rendering:

| generator failure | generator rc | `stop-audit` | correct? |
|---|---|---|---|
| `scripts/handoff.py` absent | 2 | **ALLOW** | ✅ fail-open |
| usage error (`sys.exit(2)`) | 2 | **ALLOW** | ✅ fail-open |
| hangs (60 s vs the 30 s timeout) | timeout | **ALLOW** | ✅ fail-open |
| `ImportError` (e.g. `scripts/board.py` renamed — `handoff.py` imports it) | 1 | **BLOCK** | ❌ **fail-CLOSED** |
| `RuntimeError` | 1 | **BLOCK** | ❌ **fail-CLOSED** |
| `SyntaxError` | 1 | **BLOCK** | ❌ **fail-CLOSED** |

**[EXEC] And the session is wedged**, because the instructed recovery fails the same way:

```
close                         BLOCK: (e′) … handoff.md is stale — run `… --write`, commit …
instructed recovery --write   rc=1   (the generator is broken; it cannot write either)
close again                   BLOCK  (identical)
```

**[EXEC]** a Stop `BLOCK` is a hard deny — `journal-gate.sh:46` exits 2. So a broken generator
blocks **every orchestrator close, repo-wide**, citing a reason that is false and instructing a
recovery that cannot work. That is the same shape as the deadlock the plan's §0 exists to prevent,
arriving through a different door.

Three things bound the severity, and they are why this is a condition and not a veto:

- **[EXEC] Malformed artifacts do NOT trigger it.** `handoff.py` parses front matter with a
  hand-rolled parser, not a YAML library: unparseable front matter, tab-indented YAML, and a
  list-valued front matter all return rc 1 *legitimately* (the rendering really did change) and
  `--write` fixes them. The trigger is a broken **generator**, not broken **input**.
- The generator is stdlib-only and covered by `tests/unit/test_handoff.py`.
- A human recovers trivially (fix, or delete `scripts/handoff.py`, which fails open).

**The plan's own Item 12 invariant is nonetheless not met**: *"fail-open on … any generator error —
enforcement never crashes a close."* The fix is one line — key on the sentinel the generator already
prints rather than on the bare exit code, e.g. require `proc.returncode == 1` **and** a `STALE`
marker on stderr, or have `--check` emit a machine-readable verdict. **[EXEC]** the docstring's
claim that *"an import error"* fails open is factually wrong and should be corrected with the code.

Related, from the mutation battery below: the `except Exception: return False` fail-open branch is
**never exercised by the suite** — mutating it to `return True` reddens nothing. The two belong in
one follow-on fix, together with `finding-0246`.

## 3. What was verified and held

**[EXEC] Clause (e′) correctness, driven by hand in a throwaway repo** (independent of the delivered
suite): stale rendering → `BLOCK` naming `handoff.md` and `--write`; `--write` + commit → `ALLOW`;
`--check` rc 0; a third close → still `ALLOW`. **One-step convergence holds. Item 12's falsifier did
not fire.**

**[EXEC] The mutation battery — 8 mutants against a scratch copy of the hooks; the delivered tree
was never written.** All four of the builder's reproduce as reported, and the new test is real:

| mutant | result | reddens |
|---|---|---|
| A — check 1 never stale | CAUGHT | 3 tests |
| B — (e′) fires in builder posture | CAUGHT | `test_silent_under_active_plan` |
| **C — check 2 keyed to `last_commit` (the re-arming bug)** | **CAUGHT** | **exactly `test_e_prime_check_2_is_keyed_to_session_start_not_to_the_last_commit`** |
| D — missing seat journal treated as fresh | CAUGHT | `…_seat_journal_is_missing` |
| N1 (auditor) — fail CLOSED on a generator exception | ***SURVIVED*** | — (see §2) |
| N2 (auditor) — any non-zero exit read as stale | CAUGHT | `…_fails_open_when_the_generator_is_absent` |
| N3 (auditor) — check 2 boundary `>=` → `>` | CAUGHT | the session-start test |
| N4 (auditor) — check 2 reads `readings.md` (MEASURED) | CAUGHT | 5 tests |

The added test is **not** vacuous: it is the sole discriminator for mutant C, and it also catches the
`>=`/`>` boundary. Only the untested exception branch survives.

**[EXEC] Atomicity.** `git log` per path: `.claude/hooks/_lib.py`, `.claude/hooks/session-brief.sh`,
`tests/integration/test_handoff_gate.py` and `docs/templates/resume-brief.md` each carry **exactly
one** commit on this branch — `aaff6ef` — which lists the template as a tracked `D`. No intermediate
state exists in the history.

**[EXEC] The deadlock, reproduced independently.** A throwaway repo carrying the base commit's clause
(e) with a full seat and no brief blocks on close and stays blocked; only re-creating the artifact
clears it (§1 above is the same harness). The ordering mattered.

**[EXEC] Item 13, four legs.** Seat present → rc 0, rendering + segment emitted, **stderr empty, 0
`HOOK-FAILURE`**. Seat absent (the falsifier) → rc 0, 8 lines, stderr empty, **0 `HOOK-FAILURE` —
the falsifier did not fire**. Builder posture → seat suppressed, rc 0. `active-plan` absent entirely
→ orchestrator posture, seat emitted, rc 0. The `## Markers` fix holds: `grep -c HOOK-FAILURE` over
the emitted segment is **0**.

**[EXEC] The regression contract: 6 → 13, none dropped.** `git show f9cfe4f:…| grep -c '^def test_'`
= **6**; at HEAD = **13**. Mapping confirmed against the delivered bodies — (3)/(5)/(6) verbatim as
posture invariants; (1) split into a stale-rendering case and a journal-predates-session-start case;
(2) → missing seat journal; (4) → fresh-both; plus 7 new (the lifelike work-moved-the-rendering
case, the session-start key, the MEASURED negative, convergence, and two fail-open cases). **No case
was weakened into a tautology** — every one asserts a specific decision line and, where it allows,
also asserts `(e′)` is absent from the output.

**[EXEC] Scope.** Eleven changed paths, all inside the plan's §5 or the always-writable finding
surface. **Nothing** touched `scripts/handoff.py`, `.claude/skills/**`, `.claude/settings.json`,
`CLAUDE.md`, `docs/design-notes/**`, `docs/PROGRESS.md` or `docs/inbox/**`. `bp-126/plan.md` is
**not in the diff** — `status:` still reads `in-progress`. No design note was edited; A10 is
**drafted in the journal, not landed**. `_lib.py` shows four hunks and no fifth.

**[EXEC] The withheld deletion is genuinely withheld.** `.claude/state/` in this worktree contains
only `.gitignore` and a `session-baseline`; `resume-brief.md` was never present, never written and
never removed. The journal states the live half is withheld and **declines the plan's vacuous pass**;
the seal's acceptance table marks it *"⚑ NOT CLAIMED — WITHHELD … owed at merge"*. Nowhere does the
seal claim that criterion passed. The **template** deletion is a real tracked `D`.

**[EXEC] The gate, each leg separately, redirected to a file:**

| leg | rc | observed |
|---|---|---|
| `uv run ruff check .` | 0 | clean |
| `uv run python scripts/check_imports.py` | 0 | clean |
| `uv run mypy core agents eval ops scheduler scripts` | 0 | Success: no issues found in **261** source files |
| `uv run mypy` (ARGLESS) | 1 | **Found 69 errors in 20 files (checked 559 source files)** — exactly the baseline |
| `uv run python -m ops.type_gate` | 0 | clean |
| `uv run pytest -q` | 1 | **2 failed, 2308 passed, 15 skipped, 12 warnings in 299.63s** |

The two failures are the two expected pre-existing ones and nothing else:
`test_core_imports_nothing_outside_core` (finding-0103) and
`test_dream_v2_synthesizes_grounded_themes_live` (finding-0226). `test_scheduler_live.py` passed.
**The arithmetic checks: 2301 → 2308 = +7, exactly the gate suite's 6 → 13.** No other test moved.

**[EXEC] §3 Q2's performance decision is sound.** Re-measured, 9 warm runs each on the real tree:
`handoff.py --check` min 130.4 / **median 135.4** / max 174.6 ms (builder: 130.5 / 137.0 / 143.2 over
7 runs); base `stop-audit` (clause (e)) min 84.2 / **median 87.4** / max 93.9 ms (builder: 84.8 /
85.2 / 91.4). Independently confirmed. One framing note the seal understates: the *per-close* Stop
cost goes **87 → 225 ms median**, a 2.6× increase, paid only in orchestrator posture with commits
landed. The added ~137 ms is well inside the plan's "few hundred ms" threshold, so the subprocess
choice stands — but the honest number is the 225 ms close, not the 137 ms spawn.

## 4. On finding-0244 — declining to narrow the trigger was CORRECT

The builder was right, and for the right reason. §2.10 of a **ratified** note pins the trigger
verbatim; narrowing it is the same class of unilateral act as the widening §9 forbids, and
`finding-0244` names the divergence instead of burying it. That is the artifact chain working.

Two auditor's notes. (a) The DRY objection is the weakest of the three reasons given — `%an`/`%ae`
fits in the existing `git log -1 --format=…` string at zero extra cost, and the finding says so
itself; the load-bearing reason is (1), the ratified spec. Do not let (3) carry weight it cannot
hold if this is revisited. (b) The finding's own split is the right ruling frame: for **check 1**
authorship blindness is arguably not a bug at all (a merge really does stale the rendering, and the
seat's occupant is the right party to regenerate it); for **check 2** it is, because it invites the
hollow ceremonial entry §2.5 exists to prevent. A ruling that narrows check 2 alone would cost one
format-string character and close the live half. **Not a defect being waved through.**

## 5. On finding-0245 — the measurement is accurate, and already stale

**[EXEC]** verified at the commit where it was taken: the seat surface at `aaff6ef` is **287 lines /
17,980 bytes** (reported: 287 / 18,074 — the byte delta is my reconstruction's header line), against
the archive's pinned `source_lines: 163` / `source_bytes: 11622`. The +124 / +56% figures are
correct.

**⚑ But the surface has grown twice more on this same branch:** 287 → 331 (`69f8c1f`) → **366 lines
/ 23,758 bytes at HEAD** — **+203 lines / +105%** over the retired brief, all within one build. The
authoritative segment alone is **286 lines** and `grep -c '^## CAPSULE'` is **0**. finding-0245's own
escalation trigger — *"re-enter immediately if the segment passes ~300, roughly two more entries
away"* — is **one entry away at merge**, not two. Its point 2 ("the growth curve is worse than the
level") is the finding's real content, and this branch demonstrates it rather than predicting it.
Is +56% acceptable for what (e′) buys? Yes — versioned and append-only beats historyless and
self-contradicting. Is the *trajectory* acceptable? No, and the first `/triage` capsule should not
wait.

## 6. Two smaller things the seal did not surface

- **[INSP] The SessionStart surface is now posture-gated**, which nothing in the note or the plan
  asked for. The builder flagged it for veto in both the commit message and the journal, it is one
  line, it preserves a property the gitignored brief had by accident, and it makes SessionStart
  symmetric with the clause that judges the close. **[EXEC]** an absent `active-plan` file (a fresh
  clone) is treated as orchestrator posture, matching `plan is None`. Sound, but it is Alberto's
  call, not the builder's — it is listed here so the choice is made rather than inherited.
- **[EXEC] `handoff.md` is derived-consistent at HEAD** (`--check` rc 0), so the branch is clean.
  Merging will move plan statuses and re-arm check 1 once — the documented one-step regeneration.
  The seal's "next action" list already says this.

## Verdict

**MERGE WITH CONDITIONS.** Conditions, each concrete and checkable:

1. **At merge, by hand:** delete `.claude/state/resume-brief.md` in the main checkout, taking a
   fresh snapshot at that moment and diffing it against
   `docs/archive/resume-brief-final-2026-07-27.md`; carry any delta into the seat journal in the
   same commit. *Checkable: the file is gone and the diff is recorded.* Item 14's live half is
   **open against bp-126** until this is done.
2. **Before `bp-127` Item 17 (F2) is built:** add a `session-baseline` snapshot/restore (content
   **and** mtime) around the drill's spawn as an explicit Item 17 invariant. *Checkable: run the
   drill, then confirm `session-baseline` is byte-identical and mtime-identical to before.* F1b and
   F1c (Items 15/16) need nothing and may start now.
3. **Follow-on plan, with `finding-0246`:** make `_handoff_is_stale` distinguish "stale" from
   "crashed" — a generator exception must not read as stale. *Checkable: a `handoff.py` that raises
   yields `ALLOW`, and mutating the `except` branch to `return True` reddens a test.* Correct the
   docstring's false "an import error → fail open" claim in the same change.
4. **At the first `/triage` after merge:** write the first `## CAPSULE` (finding-0245). *Checkable:
   `grep -c '^## CAPSULE'` ≥ 1 and the emitted segment is back at or below 163 lines.*
5. **Owner hand-acts, unchanged:** land A10 (drafted in the journal) and the
   `dn-session-handoff-gate` §2.2–2.3 partial-supersession log entry.

Nothing in conditions 2–5 needs to happen before the merge button.

## What could not be closed

- **The real-world firing rate of (e′)** cannot be known pre-merge. `finding-0244`'s re-entry (b) is
  the right instrument and the pre-cutover baseline is pinned (108 raw / 99 deduped / 8 days /
  16 sessions / peak 36). Any claim that the cutover worked must beat that number.
- **Whether a Claude Code sub-agent (as opposed to a nested `claude -p`) also fires SessionStart**
  was not tested — testing it would have required spawning one, which is the very act that corrupts
  the state under audit. Condition 2's snapshot/restore is written to be agnostic to the answer.
- **`docs/roles/**` content quality** (does the handoff pair actually orient a fresh session?) was
  read, not drilled. That is precisely what `bp-127`'s F2 exists to answer, and it cannot be
  answered before F2 runs.

## Routing

`discovery` → **orchestrator**. It is a merge decision plus four follow-on acts, all of which the
orchestrator owns or schedules; only the posture-gating question in §6 is Alberto's, and it is a
one-line revert either way.
