# Journal — bp-066 (core-self-containment-enforcement)

(minted 2026-07-17, session-26; owner-directed enforcement, warrant finding-0103. The red enforcement
test is the deliverable — the suite goes RED at 106 by design.)

---

## session-27 (2026-07-17) — build start, OPUS, in-session builder contract

**Setup.** active-plan → `docs/build-plans/bp-066/plan.md`; status `ready → in-progress`.

**Pre-build defect fixed (plan front-matter).** The write_scope entries were UNQUOTED with inline
`# comments`. `_lib.py:_scalar` only strips a trailing `#` comment from a *quoted* scalar (L206–218,
oq-0013 shape) — so scope-guard was matching each path *with its comment glued on*, denying every
write in scope. Fix: quoted the three write_scope entries. No widening — the intended three paths are
unchanged; the parser can now see them. (Process note for future plans: **write_scope entries with
inline comments MUST be quoted.**)

### Item 1 — the red enforcement test ✅ (red by design)
`tests/unit/test_core_self_containment.py` written. Structure:
- `_first_party_siblings()` — DYNAMIC forbidden set = top-level dirs with `__init__.py` minus `core`
  → {agents, config, edge, eval, ops, scheduler} at authoring. New sibling auto-forbidden.
- `_core_sibling_imports()` — AST scan of `core/**`; `ast.Import` + `ast.ImportFrom` with `level==0`
  only (relative = intra-core, never flagged); root = first dotted segment; flag if in forbidden set.
- `test_core_imports_nothing_outside_core` — the ratchet; raises `AssertionError` with a banner
  (INTENTIONAL RED, finding-0103, "do NOT weaken — fix the imports") + count + full `file:lineno →
  root` enumeration.
- Two helper guards (both PASS): scanner sees the known set (config/eval/ops/agents ⊆ forbidden,
  core ∉); relative + intra-core imports NOT flagged.

**Acceptance MET.** `uv run pytest tests/unit/test_core_self_containment.py -q` → **1 failed, 2
passed**. The one failure is `test_core_imports_nothing_outside_core`, banner states **106** forbidden
imports (config 90 / ops 8 / eval 7 / agents 1 — reproduced independently, matches finding-0103
exactly, 49 files). ruff `All checks passed`; mypy `Success`.

**Falsifiers checked:** test does NOT pass today (scanner sees the 106 ✓); a relative/intra-core
import is NOT flagged (dedicated guard ✓); the forbidden set is computed dynamically, not hard-coded
(guard asserts membership, not a literal list ✓).

### Item 2 — the two CONVENTIONS.md rules ✅
- **DRY** in §Language & style: reuse before re-implement; a duplicated implementation is a *defect*
  (two copies drift); search `core/` first; enforced by process + review, not a hook. Cross-refs
  §Trust boundaries + finding-0101/0103.
- **Self-containment** in §Trust boundaries: core is SACRED; deps = stdlib + pinned side-effect-free
  3p (`uv.lock`) + core; NOTHING first-party outside `core/` (config/eval/ops/agents/edge/scheduler
  are machinery *around* core); arrow `everything → core`; template "core computes/returns pure data,
  machinery calls core". **NO eval-example parenthetical** (owner correction honored — the rule is
  absolute, not eval-scoped). Cross-refs the DRY rule + the enforcement test.

### Item 3 — the manifest-audit step in build-plan skill §2 ✅
`.claude/skills/build-plan/SKILL.md` §2 gained the required "does `core/` already implement this?"
audit for any plan introducing an algorithm/primitive — `core/` first, reuse over re-derive, citing
the bp-060/finding-0101 miss. Worded as MUST, not optional.

### Acceptance — ALL MET
- Full suite: **1 failed, 1538 passed, 8 skipped** — the sole failure is the intentional
  `test_core_imports_nothing_outside_core` (red at 106). Two-part green check ✓.
- Argless mypy: **69** (baseline held — the new test adds no type errors). ruff clean.
- Non-goals honored: touched ONLY the three write_scope files; no edit to `core/**`, `config/**`,
  `eval/**`, `ops/**`, `agents/**`, `CLAUDE.md`, or the denylist. No allowlist/xfail/skip.

**Deliverable committed `748c946`** (`test(core): enforce self-containment — red at 106 + …`).

### SEAL — bp-066 COMPLETE (session-27, 2026-07-17)
Status → complete. cost.actual recorded (dollar/session/week deltas OWED, fold into the pending
bp-063/065 /usage relay). Downstream now unblocked: **bp-067** (config-split, drops red 106→16),
**bp-068+** (the 16 machinery inversions → green). This test is the ratchet those are measured
against. ⚠️ The suite is RED-by-design until then; "green" = only-this-test-fails + count monotone
non-increasing.
