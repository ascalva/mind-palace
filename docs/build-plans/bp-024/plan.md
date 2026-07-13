---
type: build-plan
id: bp-024
status: ready
design_ref:
  - docs/findings/finding-0051.md # findings-driven enforcement hardening — no design-note graduation (§0)
contract: builder
write_scope:
  - ".claude/hooks/_lib.py"                          # the (d) cross-checkout bleed check in cmd_stop_audit ONLY
  - "tests/integration/test_worktree_enforcement.py" # the falsifier test
  - "docs/build-plans/bp-024/**"
  - "docs/findings/**"
session_budget: 1
cost:
  estimate: { model: sonnet, tokens: 60k } # one bounded check + one integration test; spec pinned verbatim §6
  actual: null
depends_on: []
parallelizable_with: []
created: 2026-07-12
updated: 2026-07-12
links:
  - docs/findings/finding-0051.md # the observed bleed (bp-022 spawn)
  - docs/findings/finding-0031.md # the parent class (CLAUDE_PROJECT_DIR = main for worktree agents)
re_entry: null
supersedes: null
superseded_by: null
warrant: finding-0051
---

# Build Plan — flag the cross-checkout state bleed at the Stop gate (finding-0051 fix 2)

> **Every section below is required.** N/A is an accountability act.

## 0. Mode & provenance

Triage-promoted (third /triage, 2026-07-12) from finding-0051 fix 2, NOT a design-note
graduation: an enforcement-hardening rider on the existing journal-gate audit, spec pinned
verbatim below so a sonnet builder follows it without inferring design. `warrant:
finding-0051`. Investigation and planning produced this; implementation proceeds on owner
approval. `proposed → ready` is the owner's hand edit. **Blast radius is enforcement**
(§7 invariants) — the falsifier is a crisp reproduce-the-bleed test, which is why the
pre-ruling sized it to sonnet under a fully-pinned spec.

## 1. Objective

`cmd_stop_audit` gains a check `(d)` that BLOCKS a worktree session's close when the MAIN
checkout's `.claude/state/active-plan` carries THIS worktree's own active plan — the exact
finding-0051 bleed signature — so a builder that Bash-wrote main's pointer must clear it
before Stop, closing the one gap the pre-hoc guards structurally cannot (Bash writes to an
absolute cross-checkout path).

## 2. Context manifest

1. `docs/findings/finding-0051.md` — the observed bleed: bp-022's builder set both its own
   worktree pointer (correct) AND main's `.claude/state/active-plan ← "bp-022"`.
2. `docs/findings/finding-0031.md` — the root class: `CLAUDE_PROJECT_DIR` resolves to the
   MAIN checkout for worktree-isolated agents, so `$CLAUDE_PROJECT_DIR`-anchored Bash
   writes reach main from inside a worktree.
3. `.claude/hooks/_lib.py:554-668` — `cmd_stop_audit`; checks (a)/(b)/(b2)/(c) are the
   pattern the new (d) extends. `:62-80` `repo_root()` and `:280-300` `active_plan_path()`
   — how ROOT and the worktree pointer are resolved.
4. `.claude/hooks/journal-gate.sh:11-29` — the `_CWD_TOP` (worktree) vs `_ENV_TOP`
   (`CLAUDE_PROJECT_DIR` = main) resolution the check reuses to name the main checkout.
5. `tests/integration/test_worktree_enforcement.py` — where the falsifier test lands.

## 3. Investigation & grounding

- **Q1 — why can't this be denied pre-hoc?** `scope-guard` intercepts Edit/Write, not
  Bash; a `printf … > /main/.claude/state/active-plan` is a Bash write to an absolute path
  and is invisible to the pre-hoc guard (finding-0051 §"Why it matters"). Only a post-hoc
  Stop audit sees the effect. `_lib.py:554` `cmd_stop_audit` is that audit.
- **Q2 — how is "the main checkout" named from inside the worktree?** The journal-gate hook
  already computes `_ENV_TOP` = realpath'd `CLAUDE_PROJECT_DIR` = the main checkout, and
  `_CWD_TOP` = the worktree toplevel; they DIFFER exactly when running in a worktree
  (`journal-gate.sh:22-28`). In `_lib.py`, `repo_root()` (`:62`) reads the same
  `CLAUDE_PROJECT_DIR`. The check reads main's pointer at `<CLAUDE_PROJECT_DIR>/.claude/
  state/active-plan` and compares to this session's `active_plan_path()`.
- **Q3 — what is the false-positive-free signature?** finding-0051 shows the bleed is the
  builder copying ITS OWN plan id into main's pointer ("MAIN ← 'bp-022'" where bp-022 was
  the worktree's plan). So the zero-false-positive predicate is: running in a worktree
  (CWD-top ≠ env-top) AND main's `active-plan` is non-empty AND it resolves to the SAME
  plan as this worktree's `active_plan_path()`. An orchestrator legitimately holding a
  *different* main-checkout plan (non-standard, but possible) does not trip it.
- **Q4 — is the check purely read-only?** YES — it stats/reads main's pointer file; it
  never writes cross-checkout (the builder must clear its own bleed, per the block reason).

**Additional risks surfaced during reading:** the check must fail-open on any error
(unreadable main pointer, absent `CLAUDE_PROJECT_DIR`) — an enforcement check that crashes
is worse than one that misses (journal-gate is fail-open/fail-loud, `.sh:10`). It must be
byte-identical when NOT in a worktree (env-top == cwd-top) — pure addition, guarded by the
worktree predicate.

## 4. Reconciliation

- `.claude/hooks/_lib.py` `cmd_stop_audit` — extends, does not alter, checks (a)-(c).
  **[cross-ref: extension]**: the new `(d)` appends a reason under the same `reasons` list
  and the existing `BLOCK: …` join; every prior check's behavior is unchanged (the block is
  additive). Present as the §6 diff.

## 5. Write scope

In: `.claude/hooks/_lib.py` — the `(d)` block inside `cmd_stop_audit` ONLY (plus a small
private helper if cleaner); the integration test; own plan dir; findings. Out,
deliberately: `journal-gate.sh` (no change — the `.sh` already resolves ROOT worktree-aware
and calls `stop-audit`; the logic is all in `_lib.py`); every other hook; `scope-guard`
(pre-hoc is structurally unable to see Bash writes — not the fix site); design notes; the
foundation denylist.

## 6. Interfaces pinned inline

**(a) The `(d)` check — appended in `cmd_stop_audit` after the (c)/A3 blocks, before the
`if reasons:` join (`_lib.py:663`):**

```python
    # (d) cross-checkout state bleed (warrant finding-0051) -> worktree sessions only.
    # A worktree builder must never write the MAIN checkout's .claude/state/**; the
    # pre-hoc guard can't see the Bash write, so flag it at Stop. Signature (zero false
    # positives, §3 Q3): running in a worktree AND main's active-plan resolves to THIS
    # worktree's own plan. Read-only; fail-open on any error (enforcement never crashes).
    try:
        env_top = os.environ.get("CLAUDE_PROJECT_DIR")
        cwd_top = _cwd_worktree_top()          # realpath'd git toplevel of CWD, or None
        if env_top and cwd_top and os.path.realpath(env_top) != cwd_top and plan is not None:
            main_ptr = os.path.join(os.path.realpath(env_top), ".claude", "state", "active-plan")
            with open(main_ptr, encoding="utf-8") as fh:
                main_val = fh.read().strip()
            if main_val and _same_plan(main_val, plan):   # normalize bare-id vs path
                reasons.append(
                    "(d) cross-checkout state bleed: the MAIN checkout's active-plan "
                    f"points to this worktree's plan ('{main_val}'). A worktree builder "
                    "never writes the main checkout's .claude/state/** (finding-0051). "
                    f"Clear it: printf '' > {main_ptr}"
                )
    except Exception:
        pass   # fail-open, fail-loud is the .sh's job; a missing/unreadable pointer never blocks
```

`_cwd_worktree_top()` and `_same_plan(a, b)` are the existing resolution logic factored
out: the former is the realpath'd `git rev-parse --show-toplevel` of the CWD (already
computed in `repo_root()` at `:62-80` and in the `.sh` at `:22`); the latter normalizes a
bare id (`"bp-022"`) or a `docs/build-plans/<id>/plan.md` path on both sides before
comparing (mirroring `active_plan_path()`'s `:296-299` normalization). The builder may
inline these rather than add helpers if that reads cleaner against the existing code — the
pinned BEHAVIOR is what binds, not the factoring.

**(b) The falsifier test (Item 14), shape:**

```python
# tests/integration/test_worktree_enforcement.py
def test_stop_audit_flags_main_checkout_pointer_bleed(tmp_path, monkeypatch):
    # Build a fake main checkout + a worktree; set BOTH active-plan pointers to the same
    # plan id (the bleed). Run cmd_stop_audit from the worktree with CLAUDE_PROJECT_DIR
    # set to main. Assert the output contains "(d) cross-checkout state bleed".
    # Control 1: main's pointer EMPTY -> no (d) reason.
    # Control 2: main's pointer names a DIFFERENT plan -> no (d) reason (zero false positive).
    # Control 3: NOT in a worktree (env-top == cwd-top) -> byte-identical, no (d) reason.
```

## 7. Items

_(numbering continues the global sequence)_

### Item 14 — the (d) cross-checkout bleed check + its falsifier test

- **Objective:** add §6(a) to `cmd_stop_audit` and §6(b)'s test; the bleed blocks a
  worktree Stop, the three controls do not.
- **Files:** `.claude/hooks/_lib.py`, `tests/integration/test_worktree_enforcement.py`
- **Acceptance test:** `uv run pytest -q tests/integration/test_worktree_enforcement.py`
  green including the new test (bleed → `(d)` present; all three controls → absent);
  `python3 .claude/hooks/_lib.py stop-audit` still `ALLOW`s a clean root session
  (byte-identical no-worktree path).
- **Falsifier:** the check blocks a legitimate session — main's pointer names a *different*
  plan, or the session is not in a worktree (env-top == cwd-top), yet `(d)` fires; or it
  writes cross-checkout instead of only reading (it must never clear main's pointer itself).
- **Invariant(s):** checks (a)/(b)/(b2)/(c) behavior byte-identical; fail-open on any error
  (never crash the Stop gate); no cross-checkout WRITE from the check; no new dependency.
- **Touches stored data?** no
- **Parallelizable?** no (single item)  **Depends on:** none

## 8. Math carried explicitly

N/A — a string-equality guard, no mathematical object.

## 9. Non-goals

Pre-hoc denial of the Bash write (structurally impossible — Q1; the $PWD-anchored spawn
prompt stays the primary control); auto-clearing main's pointer from the check (the builder
clears its own bleed — a read-only audit never writes cross-checkout); touching
`journal-gate.sh`, `scope-guard`, or `CLAUDE_PROJECT_DIR` resolution; the finding-0031
hook-resolution fix (already landed, bp-014).

## 10. Stop-and-raise conditions

If grounding shows `repo_root()`/`active_plan_path()` no longer resolve as §3 describes
(the hook layer changed under this plan), STOP and re-ground — do not build against a stale
read of `_lib.py`. If the zero-false-positive predicate (Q3) cannot be met because
`active_plan_path()` and main's raw pointer normalize differently, file a finding rather
than loosening the predicate to "any non-empty main pointer" (that variant is the §11
rejected alternative, owner's call).

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
| --- | --- | --- | --- |
| bleed predicate | main's pointer == THIS worktree's plan (zero false positives, §3 Q3) | flag ANY non-empty main pointer from a worktree (stricter, but false-positives if the orchestrator legitimately builds a *different* plan in main — non-standard yet possible) | the owner prefers strictness, or the equality normalization proves unreliable (§10 → finding) |
| enforcement point | Stop-gate post-hoc flag (all logic in `_lib.py`) | a PostToolUse Bash hook parsing commands for cross-checkout paths (brittle string-matching on arbitrary Bash; higher false-positive surface) | a pre-execution interception becomes necessary (a bleed that a post-hoc flag cannot catch appears) |

## 12. Dependency & ordering summary

Single item (Item 14); no intra-plan ordering. No cross-plan dependency — disjoint from
every code/test plan (touches only `_lib.py`'s audit + one integration test). Blast radius
is enforcement, contained by the fail-open posture and the crisp falsifier. After Item 14,
finding-0051 flips `→ promoted`; the $PWD-anchored spawn prompt remains the pre-hoc primary
control, with this check the post-hoc backstop for the residual Bash path.
