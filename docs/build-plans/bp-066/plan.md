---
type: build-plan
id: bp-066
alias: core-self-containment-enforcement
status: complete
design_ref:
  - CONVENTIONS.md                                 # the standing engineering-practice doc this AMENDS (the two rules land here)
  - docs/findings/finding-0103.md                  # THE WARRANT — the full audit + the owner's strict ruling
contract: builder
write_scope:
  - "tests/unit/test_core_self_containment.py"     # NEW — the red enforcement test
  - "CONVENTIONS.md"                               # Rule 1 (DRY, §Language & style) + Rule 2 (self-containment, §Trust boundaries)
  - ".claude/skills/build-plan/SKILL.md"           # the manifest-audit process step (DRY's non-hook enforcement)
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 40k
  actual:
    model: opus                                    # in-session self-build (session-27); no delegation
    tokens: ~45k                                   # approx; manifest reads + test + ruff reflow iterations
    ratio: ~1.1                                    # ≈ estimate — a well-pinned §7 (text carried verbatim)
    dollars: pending /usage relay                  # OWED — closes with the bp-063/065 relay
    session_delta: pending /usage relay
    week_delta: pending /usage relay
    note: >-
      The only non-trivial surprise was a plan-front-matter defect (unquoted write_scope entries with
      inline comments → scope-guard denied every in-scope write); fixed by quoting. Suite wall-clock
      (931s) was machine contention from stacked concurrent runs, not the change.
depends_on: []
parallelizable_with: []
supersedes: null
superseded_by: null
warrant: docs/findings/finding-0103.md
created: 2026-07-17
updated: 2026-07-17                                 # session-27: ready→in-progress (build start)
re_entry: null
---

# Build Plan — enforce core self-containment (loud, red today) + write the DRY + boundary rules

## 0. Mode & provenance — OWNER-DIRECTED enforcement
Not graduated from a design note — **owner-directed in-session (2026-07-17)**, warranted by
finding-0103. The "design" is the principle itself, written into `CONVENTIONS.md` (the standing
engineering-practice doc). Owner rulings pinned: (a) **core is SACRED** — its dependency surface is exactly the Python
stdlib + **pinned, side-effect-free third-party libraries** (numpy, scipy, …; `uv.lock`
authoritative) + `core` itself, and **nothing first-party outside `core/`** — period, config
included, no wiggle room. Core is the processing unit; everything else (config, eval, ops, agents,
edge, scheduler) is machinery *around* it, and first-party code core reaches for is a **liability**
(mutable, side-effecting, coupling the sacred to the machinery's churn — the opposite of a pinned
lib); (b) enforce **immediately, RED today** — a loud failure now, never a silent allowlist or
"handle later"; (c) DROP the eval-example parenthetical from the rule text (the rule is absolute, not
eval-specific). Cleanup of the 106 violations is a SEPARATE program (config-split + 16 inversions,
finding-0103) — **NOT this plan**; this plan lands the enforcement and the docs only.

## 1. Objective
A permanently-present unit test that FAILS today, loudly enumerating every `core/** → sibling`
import (106 at authoring), and can only go green when all are gone (a ratchet); plus the two rules
written into `CONVENTIONS.md` (DRY; core self-containment) and the DRY manifest-audit step added to
the build-plan skill.

## 2. Context manifest (read in order)
1. `docs/findings/finding-0103.md` — the audit (106 imports; config 90 / ops 8 / eval 7 / agents 1)
   and the strict ruling. The list this test must reproduce.
2. `CONVENTIONS.md` §Language & style (~L5-11) + §Trust boundaries (~L44-48) — the two homes; the
   existing siblings the new rules sit beside (`core/` has no network-reachable import; "keep modules
   small and single-purpose").
3. `.claude/skills/build-plan/SKILL.md` §2 (the context-manifest section, ~L39) — where the
   "does core already implement this?" audit step is added (DRY's process enforcement).
4. The scan logic in finding-0103's investigation (an `ast` walk of `core/**` ImportFrom/Import,
   flagging any root that is a first-party top-level package ≠ `core`).

## 3. Investigation & grounding
Done (finding-0103): the forbidden set = every repo top-level Python **package** (a dir with a
top-level `__init__.py`) except `core` — computed DYNAMICALLY so a new sibling package is
auto-forbidden, never a hard-coded list that rots. Current members that appear in core imports:
`config`, `ops`, `eval`, `agents`. `level>0` (relative) imports are always intra-core → never
flagged. Stdlib/third-party roots are not repo packages → never flagged.

## 4. Reconciliation
`CONVENTIONS.md` is amended, not superseded — the two rules are additive bullets in existing
sections. No design-note edit (this is engineering practice, the owner-directed amendment surface).

## 5. Write scope
The three files in front-matter. **OUT:** all of `core/**`, `config/**`, `eval/**`, `ops/**`,
`agents/**` (the CLEANUP that makes the test pass is later plans — this plan must NOT touch them);
`CLAUDE.md` (a possible one-line pointer is deferred to the owner, §11); the foundation denylist.

## 6. Interfaces pinned inline
```python
# tests/unit/test_core_self_containment.py
def _first_party_siblings() -> set[str]:
    """Repo top-level packages (dir with a top-level __init__.py) except 'core' — DYNAMIC, so a new
    sibling package is forbidden the moment it exists, never a hard-coded list."""
def _core_sibling_imports() -> list[tuple[str, int, str]]:
    """(file, lineno, imported-root) for every core/** import whose root is a first-party sibling.
    ast.Import + ast.ImportFrom with level == 0 only (relative imports are intra-core)."""
def test_core_imports_nothing_outside_core() -> None:
    """OWNER RULING (2026-07-17, finding-0103): core/ is the processing unit; it imports NOTHING
    from the project outside core/ — config included, no wiggle room. This test is RED BY DESIGN
    until the cleanup program (config-split + 16 inversions) completes — a loud ratchet, never an
    allowlist. A NEW core→sibling import makes it redder; a fix makes it greener; zero ⇒ green."""
    # assert violations == [] with a message: the count + every (file:lineno → root), and a banner
    # naming finding-0103 + "INTENTIONAL red — do NOT weaken this test; fix the imports."
```

## 7. Items
### Item 1 — the red enforcement test  (blast: adds a deliberately-failing test)
- **Objective:** `tests/unit/test_core_self_containment.py` — the dynamic scan + the ratchet assert.
- **Acceptance test:** `uv run pytest tests/unit/test_core_self_containment.py -q` **FAILS** (red by
  design) with a message that (a) states the count (**106** at authoring), (b) lists every
  `file:lineno → root`, (c) banners it as INTENTIONAL (owner ruling, finding-0103) with "do not
  weaken; fix the imports." A helper-level check confirms the scanner finds the known set
  (config/ops/eval/agents present; a `core→core` or relative import NOT flagged). `ruff`/`mypy`
  clean on the file.
- **Falsifier:** the test PASSES today (the scanner is broken — it must see the 106); a relative
  (`level>0`) or intra-`core` import flagged as a violation; a hard-coded forbidden list instead of
  the dynamic top-level-package computation.
- **Invariant(s):** dynamic forbidden set (new siblings auto-caught); ratchet (monotone — only a
  real fix reduces the count); loud (full enumeration, not just a count).
- **Touches stored data?** No.  **Parallelizable?** No.

### Item 2 — the two rules in CONVENTIONS.md  (blast: doc)
- **Objective:** Rule 1 (DRY) in §Language & style; Rule 2 (self-containment) in §Trust boundaries.
- **Acceptance test:** `CONVENTIONS.md` §Language & style carries the DRY bullet (reuse before
  re-implement; a duplicated implementation is a defect not a nit; drift rationale); §Trust
  boundaries carries the self-containment bullet — stated as **sacredness + the two allowed inputs**:
  *core is SACRED and self-contained; its only dependencies are the stdlib and pinned,
  side-effect-free third-party libraries (`uv.lock` authoritative) — it imports NOTHING first-party
  outside `core/` (config/eval/ops/agents/edge/scheduler are machinery around core; first-party code
  core reaches for is a liability). The arrow is `everything → core`, never the reverse; core never
  re-implements what it already has. Template: core computes and returns pure data; the machinery
  calls core, records, grades, runs.* **NO eval-example parenthetical** (owner correction — the rule
  is absolute). Each cross-references the other + finding-0103.
- **Falsifier:** the self-containment bullet scoped to eval only, or carrying the dropped paren; the
  DRY bullet absent from §Language & style; the rules stating a wiggle-room exception.
- **Invariant(s):** the rules are absolute as ruled; sit beside their existing siblings.
- **Touches stored data?** No.  **Parallelizable?** No.

### Item 3 — the DRY manifest-audit step in the build-plan skill  (blast: skill)
- **Objective:** the §2 context-manifest guidance gains a required "does `core/` already implement
  this?" audit step for math/algorithm-bearing plans (the process defense the bp-060 manifest lacked).
- **Acceptance test:** `.claude/skills/build-plan/SKILL.md` §2 states that a plan introducing an
  algorithm/primitive MUST include, in its manifest, an audit for an existing implementation
  (`core/` first) — reuse over re-derive (DRY, non-hook-enforceable), citing finding-0101/0103.
- **Falsifier:** the step absent, or worded as optional.
- **Invariant(s):** DRY's enforcement is process (this step) + review, never a hook.
- **Touches stored data?** No.  **Parallelizable?** No.

## 8. Math carried explicitly
N/A — no mathematical object. A static import-graph invariant + two prose rules.

## 9. Non-goals
NO cleanup of any violation (config-split, the 16 inversions — later plans, finding-0103). NO edit to
`core/**`, `config/**`, `eval/**`, `ops/**`, `agents/**`. NO CLAUDE.md edit (§11). NO weakening of the
test to make the suite green (the red is the deliverable). NO allowlist / xfail / skip (owner: loud,
not silent).

## 10. Stop-and-raise conditions
- The scanner cannot distinguish intra-core/relative imports from sibling imports → STOP, fix the
  `level`/root logic (a false positive would make the ratchet dishonest).
- Any pressure to allowlist/xfail the known 106 "so the suite is green" → STOP; that is the exact
  silent-handle-later the owner forbade. The red stands.
- Any blessing: never.

## 11. Parked decisions
| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| CLAUDE.md pointer to the rule | none (rule lives in CONVENTIONS only) | a one-line CLAUDE.md digest line — bloats the thin always-loaded file for an engineering (not safety) rule | owner wants it in the always-loaded steer |
| test red vs a green "progress" variant | RED (owner directive) | assert count ≤ N ratchet that's "green" at 106 | never — the owner chose loud red |

## 12. Dependency & ordering summary
No upstream dependency. Items 1→2→3 independent (any order); grouped for one commit. **Downstream:**
the cleanup program — config-split (bp-067 candidate) drops the red from 106→16; the 16 inversions
(bp-068+) drive it to green. This test is the ratchet those plans are measured against.
