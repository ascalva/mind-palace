---
type: finding
id: finding-0250
status: open
created: 2026-07-27
updated: 2026-07-27
links:
  - docs/build-plans/bp-126/plan.md
  - docs/build-plans/bp-126/journal.md
  - docs/findings/finding-0247.md
  - docs/design-notes/role-state-and-scoped-handoff.md
  - .claude/hooks/_lib.py
  - scripts/handoff.py
  - tests/integration/test_handoff_gate.py
ftype: discovery
origin_plan: orchestrator
route: orchestrator
resolution: null
---

# The focused re-audit of `a62e5f1` — the fix holds under every probe, the spoofing hazard is
# REAL and not a phantom, and the seat qualifier that defeats it is pinned by no behavioural test

## What

A second independent auditor (not the builder, not the author of `finding-0247`) re-audited
**only** the surgical fix `a62e5f1` on branch `worktree-agent-a7200bccdd41047b0` — the response to
the merge-blocking defect `finding-0247` raised, in which clause (e′) check 1 could not tell a
**stale** generator from a **crashing** one and therefore wedged the close. The bp-126 audit itself
was not repeated. Read-only over the delivered work throughout; every mutation and every induced
failure ran against a **scratch mirror** of the tree under `scratchpad/mirror`, never the worktree
(`git status --short` is empty at the end of this audit, as it was at the start). No nested
`claude -p` was invoked anywhere (`finding-0246`).

Claims marked **[EXEC]** were reproduced by running them; **[INSP]** means inspected only.

**Verdict: MERGE WITH CONDITIONS.** The fix is correct, and it is correct for the reasons its
author gives. One condition is owed — a coverage gap in the *tests*, not a defect in the *code*,
which no delivered test would catch and which this finding hands over closed-form.

## 1. ⚑ The spoofing property is REAL — both halves, by execution

The fix's most subtle choice is the **seat qualifier**: `HANDOFF_STALE_SIGNATURE =
f"{SEAT_ROLE}/handoff.md: STALE"` rather than a bare `": STALE"`. The claimed hazard is that a
generator raising *at its own staleness `print`* echoes that line's **source** in the traceback,
and the source contains the f-string template `{dest.relative_to(ROOT)}: STALE` — so a bare probe
would be spoofed **by the exact failure class the fix exists to handle**.

Constructed realistically rather than by string injection: `dest` is made to fall outside `ROOT`
immediately before the print, so `dest.relative_to(ROOT)` raises `ValueError` **while evaluating
the staleness print**. The print statement's own source is byte-untouched — that is the point.

**[EXEC] The premise holds.** The crash exits **1** (like a genuine stale render) and its output is:

```
  File ".../scripts/handoff.py", line 457, in main
    print(f"{dest.relative_to(ROOT)}: STALE — regenerate with "
             ~~~~~~~~~~~~~~~~^^^^^^
ValueError: '/audit-nowhere/handoff.md' is not in the subpath of '/.../main'
```

`": STALE"` present: **True**.  `"orchestrator/handoff.md: STALE"` present: **False**.

**[EXEC] (a) A bare `": STALE"` probe IS spoofed.** Same scenario, only the signature narrowed:

```
BLOCK: (e′) commits landed this session and docs/roles/orchestrator/handoff.md is stale — run …
```

The wedge is reproduced exactly: a *crash* read as *staleness*, blocking a close whose instructed
recovery (`--write`) fails identically. This is **not a phantom** — the qualifier is load-bearing.

**[EXEC] (b) The delivered seat-qualified signature is NOT spoofed.** Same scenario, unmodified
hook: **`ALLOW`**, with `(e′)` absent from the output. The fix resists the one attack that the
naive form of itself would have introduced.

## 2. [EXEC] The eight modes, re-measured independently — including a REAL timeout

Throwaway repo, seat genuinely stale and check 2 pre-satisfied, so only check 1 can decide:

| mode | `--check` rc | clause (e′) check 1 |
|---|---|---|
| genuine stale (control) | 1 | **CLOSED — blocks** ✅ |
| ImportError | 1 | OPEN — allows ✅ |
| RuntimeError | 1 | OPEN — allows ✅ |
| SyntaxError | 1 | OPEN — allows ✅ |
| **crash AT the staleness print** (mine, not in the builder's matrix) | 1 | OPEN — allows ✅ |
| usage / scope error (`ROLE_REGISTRY` no longer carries the seat) | 2 | OPEN — allows ✅ |
| absent generator | 2 | OPEN — allows ✅ |
| up to date (control) | 0 | OPEN — allows ✅ |

**⚑ The timeout is genuinely wired, not merely asserted.** The builder's evidence was arithmetic
(120 s = a 90 s hang + the hook's 30 s). Re-measured directly instead: the delivered `timeout=` was
read out of the hook (**30**), a generator hanging **45 s** was installed, and the close was driven.
**Elapsed 30.1 s → `ALLOW`.** The hang was cut off at the delivered timeout and fell into the
fail-open arm. The arithmetic claim is upgraded to a measurement.

## 3. [EXEC] The `except Exception` arm is genuinely driven — it reddens three ways

`test_e_prime_fails_open_when_the_subprocess_cannot_be_LAUNCHED` monkeypatches `subprocess.run` to
raise `OSError` / `TimeoutError` / `MemoryError`. It is a real driver of the branch, not a
decoration — proven by mutation rather than by reading:

| mutation of the arm | result |
|---|---|
| inverted (`return True`) | **CAUGHT** — that test reddens |
| removed (narrowed to `except ZeroDivisionError`, so the exception propagates) | **CAUGHT** |
| narrowed to `except subprocess.TimeoutExpired` only | **CAUGHT** |

The auditor's surviving mutation **N1 is genuinely closed**. The safety net the whole fix leans on
is now proven.

## 4. [EXEC] Mutation campaign — the builder's 6 re-run, plus 7 of mine

All against the **delivered 18 tests**, on the scratch mirror, each reverted after.

| mutant | verdict | reddens |
|---|---|---|
| N1 except-arm inverted | CAUGHT | the launch-failure test |
| N1b except-arm removed | CAUGHT | the launch-failure test |
| N2 widen to `rc != 0` (drops the pin AND the signature) | CAUGHT | 4 — the crash tests + absent-generator |
| N3 drop the signature, keep `rc == 1` (the original defect) | CAUGHT | 3 — all three crash tests |
| N4 bare `": STALE"` **constant** | CAUGHT | the signature-contract test |
| C check 2 keyed to `last_commit` | CAUGHT | the session-start test |
| **A1 [mine]** surgical widen to `rc != 0`, signature KEPT | *survived* | — (see below) |
| **A2 [mine]** bare `": STALE"` **at the use site**, constant untouched | ***SURVIVED*** | — ⚑ |
| **A3 [mine]** match **stdout only** | CAUGHT | 3 — all three real-generator BLOCK tests |
| **A4 [mine]** match **stderr only** | *survived* | — (see below) |
| **A5 [mine]** signature loses `": STALE"`, keeps the seat path | CAUGHT | the signature-contract test |
| **A6 [mine]** except arm narrowed to `TimeoutExpired` | CAUGHT | the launch-failure test |
| **D1 [mine]** the **generator** rewords its staleness message | CAUGHT | 4 (see §5) |

The builder's "5 of 5" is confirmed and extended to **10 of 13 caught**. The three survivors are
diagnosed rather than merely counted:

**A1 and A4 are equivalent mutants — no defect, no gap worth closing.** [EXEC] A1's eight-mode
matrix is byte-identical to the delivered one: an rc-2 output never carries the signature, so the
`!= 1` pin is defence-in-depth that the signature check already provides. A4 is equivalent against
today's generator, which writes the staleness line to stderr; A3 being **caught** is what proves
the stderr half is the load-bearing one. The "both streams" choice is forward-looking by design and
cannot be pinned without mutating the generator, which is out of this plan's `write_scope`.

**⚑ A2 is a real coverage gap, and it is the one that matters.** Moving the bare probe to the *use
site* while leaving the constant intact **survives all 18 delivered tests**. N4 catches the bare
signature only through a literal identity assert (`assert sig == "orchestrator/handoff.md: STALE"`)
— a string-equality check on a constant, not a behavioural proof. The three delivered crash tests
use ImportError / RuntimeError / SyntaxError, whose tracebacks contain **no** `": STALE"` at all, so
none of them can distinguish a bare probe from a qualified one. **The single most subtle design
choice in the fix — the one the docstring, the commit message and the journal each devote a
paragraph to — is defended by no behavioural test.** [EXEC] Applying A2 and running the probe from
§1 reproduces the wedge (`BLOCK`) and reddens immediately: the gap is exactly one test wide.

## 5. [EXEC] The degradation story — both halves, verified

The fix rests on an observable contract because `scripts/handoff.py` is outside bp-126's
`write_scope`. Rewording the generator's staleness message (bp-124 style) must be **safe** and
**loud**. Both were driven:

* **SAFE.** Reworded message, seat *genuinely* stale, `--check` still exits **1** — the gate
  **`ALLOW`s**. It degrades to fail-open, never to a mis-block and never to a crash.
* **LOUD.** The same rewording reddens **four** tests, three of which drive the real generator:
  `test_e_prime_blocks_on_a_stale_derived_rendering`,
  `test_e_prime_blocks_when_the_work_itself_moved_the_rendering`,
  `test_e_prime_converges_in_exactly_one_step`, and
  `test_the_staleness_signature_is_what_the_real_generator_actually_renders`.

The docstring names only the first of those four; the coupling is in fact pinned four ways. The
"safe **and** loud" claim is the honest one, and it is met.

## 6. [EXEC] Gate arithmetic — every figure independently reproduced

| leg | claimed | measured here |
|---|---|---|
| `uv run ruff check .` | rc 0 | **rc 0**, "All checks passed!" |
| gate suite | 13 → 18 passed | **18 passed** (5.95 s). Parent `1b7fc89` has **13** test functions and no parametrize; the tip has **16**, one parametrized ×3 → 15 + 3 = **18** ✅ |
| `uv run pytest -q` | 2 failed / 2313 passed / 15 skipped | **2 failed / 2313 passed / 15 skipped** in 276.09 s |
| the two failures | the usual pair | `test_core_imports_nothing_outside_core` (finding-0103) and `test_dream_v2_synthesizes_grounded_themes_live` (finding-0226) — **exactly those two** |
| `test_scheduler_live` | known flake, passed | **passed** |
| suite delta | 2308 → 2313 | **+5**, exactly the gate suite's 13 → 18 ✅ |

**Both (e′) checks pass on the merits, and the gate is genuinely ARMED** — not silenced.
[EXEC] `session-baseline` content is `1b7fc89` while HEAD is `a62e5f1`, so the trigger predicate
fires and the checks are really evaluated. Check 1: `uv run scripts/handoff.py --role orchestrator
--check` → **rc 0**, "up to date". Check 2: seat journal mtime `1785134541` ≥ baseline mtime
`1785134274` → fresh. Neither passes vacuously.

**[EXEC] Clause (f) is no longer vacuous.** The journal's `## Follow-through` move is real: the
last non-exempt `## ` header is at line 575, `## Follow-through` at 588, and
`_journal_tail_has_followthrough("docs/build-plans/bp-126/journal.md")` returns **True** off the
header itself rather than off a backticked prose mention.

## 7. Scope — clean, with two paths beyond the enumeration

[EXEC] `a62e5f1` touches **8** files: `.claude/hooks/_lib.py`, `tests/integration/
test_handoff_gate.py`, `docs/build-plans/bp-126/journal.md`, `docs/roles/orchestrator/{handoff,
journal,readings}.md` — all expected — **plus `docs/findings/finding-0244.md` and
`finding-0245.md`**, which the enumeration did not name. Both are findings *this branch itself
authored* (created in `69f8c1f`), both changes are addendum/sharpening only with no `status`, no
`route` and no `ftype` movement, and `docs/findings/**` is writable to every builder by contract
(CLAUDE.md Roles; `_lib.py` allows it wholesale in the (b) audit). **Permitted, but named here so
the enumeration and the diff agree.**

* **No plan `status:` flip** — `bp-126/plan.md` is untouched and still `in-progress`. ✅
* **No design-note edit.** ✅
* **`.claude/state/resume-brief.md` untouched** — it is gitignored and untracked (`git ls-files
  --error-unmatch` fails; no commit in any ref ever touched it), and it is absent from this
  commit's file list. The withheld deletion is still the orchestrator's to perform by hand. ✅
* `docs/roles/orchestrator/handoff.md` moved, but as a **regeneration** (open-findings count
  35 → 36), consistent with `--check` returning rc 0 at the tip. ✅

## So what

**MERGE WITH CONDITIONS.** Nothing here is pre-merge blocking. The fix does what it claims, for the
reasons it claims, and the claims survived every probe an independent auditor could aim at them —
including one (the crash-at-the-print) that the builder reasoned about correctly but never actually
ran, and one (the timeout) whose evidence was arithmetic and is now a measurement.

**Condition 1 (owed, one test wide).** Add a **behavioural** pin for the seat qualifier. The
delivered suite proves the constant's *spelling* but never its *consequence*, and mutant A2
survives because of it. The test is written and passing; it belongs in
`tests/integration/test_handoff_gate.py` beside the crash tests:

> arm the fixture stale, rewrite the fixture's `scripts/handoff.py` so that `dest` falls outside
> `ROOT` immediately before the staleness `print` (`ValueError` raised *at* the print, source line
> echoed verbatim in the traceback), assert the crash exits 1 **and** its combined output contains
> `": STALE"` but **not** `HANDOFF_STALE_SIGNATURE`, then assert the close is **`ALLOW`**.

That single test converts A2 from a survivor into a catch and makes the paragraph the docstring
spends on the qualifier falsifiable instead of merely persuasive.

**Condition 2 (cheap, optional).** The commit message and journal both say "a mutation proves that
widening is caught". Precisely, mutation N2 drops the rc pin *and* the signature together; the
**isolated** widening (A1) is an equivalent mutant and survives. The claim is true of the code and
imprecise about the evidence. Worth a one-line correction if the journal is touched again — not
worth a commit of its own.

**The transferable lesson, seconded.** The seat journal's entry for this build already says it:
*two of the three defects in bp-126 were found by mutating working code and re-running, never by
reading it.* This re-audit adds a third data point of the same shape — A2 is invisible to review
(the code reads correctly, the constant is right, the docstring is right) and obvious to a mutant.
**Where a gate can deny a close, budget for mutation, and mutate the argument the docstring is
proudest of.**
