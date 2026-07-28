---
type: finding
id: finding-0275
status: open
created: 2026-07-27
updated: 2026-07-27
links:
  - .claude/settings.json
  - .claude/hooks.disabled.json
  - tests/integration/test_worktree_enforcement.py
  - docs/design-notes/dn-typed-workflow-registry.md
  - docs/build-plans/bp-149/plan.md
ftype: spec-defect
origin_plan: orchestrator
route: orchestrator
resolution: null
---

# Disabling the hook layer removed the ONLY enforcement of the foundation denylist and cross-worktree scope — 3 tests correctly redden, and the redness is the signal, not the defect

## What

The owner ruled the agent-hook layer off on 2026-07-27 (*"just disable, I'm tired of fighting it"*),
implemented by removing the `hooks` key from `.claude/settings.json` and preserving it verbatim in
`.claude/hooks.disabled.json`.

**Measured consequence**, run both ways on the same tree:

```
env -u OUROBOROS_HOOKS_OFF  uv run pytest tests/integration/test_worktree_enforcement.py -q
  → 8 passed

OUROBOROS_HOOKS_OFF=1       uv run pytest tests/integration/test_worktree_enforcement.py -q
  → 3 failed, 5 passed
```

Failing: `test_a_deny_cross_worktree`, `test_c_unsafe_direction_narrow_not_loosened`,
`test_d_no_pointer_is_no_plan_not_main_fallback`.

⚑ **The assertion that fails at `test_worktree_enforcement.py:210` is the one proving
`CONSTITUTION.md` is not writable.** With `scope-guard` short-circuiting, it returns ALLOW for the
foundation denylist.

## Why it matters

**1. The tests are not broken. They are working.** They asserted a property; the property was
removed by deliberate ruling; they went red. That is precisely the `structural-enforcement`
standard this repo holds — a property is only real when something *proves* it — behaving correctly
in the negative direction. A test that stayed green here would have been the defect.

**2. What is actually unguarded is larger than three tests.** Verified this pass: CI
(`.github/workflows/ci.yml`) runs ruff, the import-firewall, the type gate, the vault axis, semgrep
and gitleaks — and **nothing** covering the foundation denylist, `write_scope`, or the owner-only
blessing gates. Those had exactly one enforcement mechanism and it is now off. Not degraded — absent.
Git history and pre-merge review are what remain.

**3. ⚑ The tempting fix is the defect class this repo keeps rediscovering.** Guarding these tests
with a skip-when-`OUROBOROS_HOOKS_OFF` marker would turn the gate green while the property stays
gone. That is `finding-0249`'s *"a check that passes without testing its claim"*, and it would be
self-inflicted at the exact moment the evidence was in hand. **Do not skip-guard them.**

## Disposition (owner-ruled 2026-07-27)

> *"leave them red and file finding, proceed"*

The local green gate carries **3 known-red tests** until stage (iv). This is a recorded acceptance
with a date and a clearing condition, not an oversight or a regression to be chased. CI is
unaffected — it does not read `.claude/settings.json` — so the redness is a local-gate signal only.

⚑ **The risk of the disposition, stated so it is not discovered later:** a permanently-red gate
erodes. Three expected failures become the number people stop reading, and the fourth failure hides
inside it. Whoever runs the gate must check the failures are *exactly* these three by name, not
merely that the count is three.

## Re-entry condition

**`bp-149` (staged hook retirement, stage (iv)).** These three tests are retired *with* the
mechanism they test, replaced by the registry-side parity tests `bp-149` requires before any
guarantee is released. The plan must not close while a guarantee is unproven on both sides.

Sooner partial clearing is available and worth taking if stage (iv) slips: the foundation denylist
is the highest-value half and could be re-asserted as a **CI ratchet** — independent of hooks,
outside the agent's reach, and the shape `dn-typed-workflow-registry` §2.6 already assumes when it
says the denylist "stays covered by the CI ratchet." ⚑ That assumption is **false today**; this
finding is also the record that it must be *built*, not cited.

## Routing

`spec-defect` → **orchestrator**. The defect is in the enforcement layer's coverage, not in any
plan's code. Two remedies, both orchestrator-owned: the `bp-149` parity tests (primary), and the CI
denylist ratchet (partial, sooner, and independently worth having since it survives any future hook
decision).
