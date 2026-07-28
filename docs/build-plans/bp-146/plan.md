---
type: build-plan
id: bp-146
track: workflow
status: proposed
design_ref:
  - docs/design-notes/dn-typed-workflow-registry.md
contract: builder
write_scope:
  - ops/registry/**
  - scripts/registry.py
  - tests/unit/test_registry_land.py
  - tests/integration/test_registry_scope_parity.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 400k
  actual: null
depends_on: [bp-140]
parallelizable_with: [bp-144]
created: 2026-07-27
updated: 2026-07-27
links:
  - docs/design-notes/dn-typed-workflow-registry.md
  - docs/design-notes/agent-workflow.md
  - .claude/hooks/scope-guard.sh
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — Land-time admission: `write_scope` as a per-unit enforcement level

## 0. Mode & provenance

Investigation and planning produced this plan during `/graduate` of
`dn-typed-workflow-registry` (ratified 2026-07-27). It is the **capability half** of the
note's license (iv): it builds the registry-side replacement for `scope-guard`'s guarantee
and the parity test that proves it, and it **retires nothing**. Implementation proceeds
item-by-item on owner approval; the `proposed → ready` blessing is the owner's alone.

⚑ **Why this is a separate, unblocked plan.** The note's §3(1) says the hooks named by
`dn-agent-workflow` §6 stay until the owner amends that note. Building the replacement is
*not* removing the original — a guarantee may be proved in parallel before it is relied on
("a guarantee is retired only when a registry-side test proves parity", §2.6). So this plan
can start the moment bp-140 lands, and bp-149 — which does the removing — waits on the
owner. Splitting them is what keeps the owner's amendment off this plan's critical path.

## 1. Objective

Give the registry a `land` operation that admits a unit's diff only if every changed path is
inside that unit's declared `write_scope` and outside the foundation denylist, with the
enforcement level (a) or (b) declared per unit at graduation.

## 2. Context manifest

1. `docs/design-notes/dn-typed-workflow-registry.md` §2.6 in full — the disposition table,
   the journal-gate clause map, "**`write_scope` — an enforcement level, not a global
   choice**", the honest loss in the (a)/(b) family, and falsifier F7.
2. `.claude/hooks/scope-guard.sh` and `.claude/hooks/_lib.py:431-478` (`cmd_scope_check`) —
   ⚑ **the guarantee being replicated, read in full.** Pre-hoc denial on `file_path`, the
   `DENYLIST` arm (`:437`), the design-note status arm (`:453`), the write_scope arm
   (`:472`).
3. `.claude/hooks/_lib.py:126-181` — `_seg_match`, `glob_match`, `matches_any`. **The one
   glob matcher.** The `**`/`*`/`?` semantics `scope-guard` enforces today live here and
   nowhere else; parity means *this* matcher, not a re-derived one.
4. `.claude/hooks/_lib.py:35-39` — `DENYLIST`, verbatim.
5. `.claude/hooks/_lib.py:316-363` — `active_plan_path`, `_normalize_plan_ref`,
   `plan_write_scope` — how a plan's scope is resolved today.
6. `.claude/hooks/_lib.py:546-566` (`_changed_files`) — the untracked-inclusive diff
   (`git status --porcelain -uall`) and *why* it must be untracked-inclusive
   (`agent-workflow.md` §6, "Clarification on (b)", warrant finding-0003).
7. `docs/design-notes/agent-workflow.md` §6 — the hook contracts table and the two
   clarifications. ⚑ Read it to know exactly what parity means and what this plan must not
   claim to have replaced.
8. `docs/build-plans/bp-140/plan.md` §6 — the store, `Event`, the fold, the CLI.
9. `docs/build-plans/bp-146/journal.md`.

### DRY audit — does `core/` (or the wider tree) already have this?

⚑ This plan is a **parity** plan, so the DRY audit is not optional garnish — reusing the
existing primitives is the only way parity can be *proved* rather than *argued*.

- **A glob matcher with `**`/`*`/`?` semantics?** **Yes — `.claude/hooks/_lib.py:150
  glob_match`**, with `_seg_match` at `:126` and `matches_any` at `:176`. ⚑ **Import it; do
  not use `fnmatch`, `pathlib.PurePath.match`, or a hand-rolled matcher.** Each of those has
  different `**` semantics, and a parity test against a *different* matcher proves nothing —
  it proves the new thing agrees with itself. `scripts/board.py:34-38` and
  `scripts/handoff.py:57-61` show the sys.path idiom for importing `_lib` from `ops/`-side
  tooling; follow it exactly.
- **The foundation denylist?** **Yes — `_lib.py:35-39 DENYLIST`. Import the constant.** A
  copied literal would drift the moment the denylist changes, and this is a bright line
  (NN-9, the fixed points are sacred).
- **An untracked-inclusive changed-file scan?** **Yes — `_lib.py:546 _changed_files`**, whose
  `-uall` requirement is warranted by finding-0003 and documented in `agent-workflow.md` §6.
  Import it. A `git diff --name-only` would silently miss exactly the Bash-written untracked
  file the guarantee exists to catch.
- **A plan-scope resolver?** `_lib.py:354 plan_write_scope`. Reusable for the *transitional*
  period when scope still lives in front matter; the registry-native path reads the unit's
  `write_scope` field from the fold.
- **`core/` audit:** core owns nothing about repo paths or git and must not. `ops/effect_gate.py`
  and `ops/effect_catalog.py` own a **blast-radius axis for effectors**, which note §1.2
  non-goal 8 explicitly keeps separate ("the shared reversibility axis is an analogy, not a
  merger"). Do not import or extend the effector gate.

## 3. Investigation & grounding

- **Q1 — what exactly does `scope-guard` guarantee today?** Three arms, read at
  `_lib.py:431-478`: (i) `DENYLIST` match → deny, "foundation file … is never writable by a
  session" (`:437-440`); (ii) a design note whose on-disk status is ratified/superseded →
  deny, "the blessed record is …" (`:453`); (iii) a path outside the active plan's
  `write_scope` → deny, "outside plan '<id>' write_scope" (`:472`). Parity must cover **all
  three**, not just the third.
- **Q2 — what does the note *not* claim to replace?** §2.1, verbatim: "a store cannot stop a
  write to an arbitrary path (the write_scope problem)". And §2.6: level (a) gives up "the
  mid-flight 'you are about to stray' signal. A builder discovers the mis-scope at land time
  with the exact offending diff in hand — later than today, cheaper than today's per-write
  tax." ⇒ **This plan must not claim to replace pre-hoc denial.** It replaces the
  *guarantee* ("out-of-scope work does not reach consequence"), moving its location "from
  'before close' to 'before consequence'" (§2.6). Any journal or seal claiming otherwise is
  a completion-claims-honesty violation.
- **Q3 — what is "landing"?** The note uses the word without defining the operation.
  Grounded reading of §2.6: landing is the act that gives work consequence — in this repo,
  **a commit reaching `main`** (`CONVENTIONS.md` §Commits: "`main` is the ingestion branch";
  worktree work "enters the record at merge"). ⇒ Pinned: `land` takes a unit ref and a
  **diff range** (default: the worktree's changes against its merge base) and admits or
  refuses. It is a *check*, callable from a session, from a merge script, and from CI. It
  does not itself perform a merge — that would be an irreversible external effect this plan
  has no license for.
- **Q4 — what are levels (a) and (b)?** §2.6, verbatim: "(a) land-time admission — the
  registry refuses a landing whose diff touches paths outside the unit's declared scope.
  Unbypassable (landing goes through the registry), but the violation is discovered after
  the work, not during it. (b) worktree-as-scope — the agent physically cannot see files it
  may not write. Structural in the strongest sense; costs a worktree per unit and
  complicates read-only context." Decision: "**per-unit, not global — `write_scope` becomes
  an enforcement *level* declared at graduation. Default level = (a). Level (b) for units
  whose blast radius the delegation rubric already scores full-strength (enforcement
  surfaces, core invariants, migrations)**."
- **Q5 — is level (b) buildable here?** ⚑ Partially, and the plan says so rather than
  pretending. A worktree containing only the unit's scope is constructible with `git
  sparse-checkout`, but §2.6 itself flags that it "complicates read-only context" — a builder
  needs to *read* far more than it may write. ⇒ **This plan implements level (b) as a
  *declared level plus a verified precondition*** (Item 32): the unit records
  `scope_level: b`, and `land` additionally asserts the working tree contained no file
  outside the read-set. Constructing the restricted worktree is a delegation-harness concern
  (the **delegate** skill), not a registry concern, and is parked (§11). Do not build a
  worktree manager under this plan.
- **Q6 — where does the unit's `write_scope` come from?** Two sources during the transition:
  the plan's front matter (via `_lib.py:354 plan_write_scope`) and the registry entity's
  `write_scope` field (via `fold()`). They must agree — and after bp-143's migration they are
  the same data. Item 30 asserts the agreement and reports divergence rather than picking a
  winner.
- **Q7 — the bare-glob rule.** `_lib.py:218 _scalar` strips a trailing comment only from a
  *quoted* scalar, so `- path  # note` becomes the glob `path  # note` and matches nothing
  (finding-0085 / the bp-066 footgun). `land` must **detect** a scope entry containing ` #`
  and fail loudly with that exact explanation rather than silently admitting everything or
  nothing. This is a real defect class in this repo, hit at least three times.
- **Q8 — does the honest loss in (a) have a backstop?** §2.6: "the CI ratchet (nothing merges
  un-reconciled) and the fact that an unlanded worktree is, by the disposable-sessions
  doctrine, discardable state." The CI ratchet is bp-142's. ⇒ This plan's `land` must be
  runnable **in CI** with no machine-level store (same hermeticity argument as bp-142 §3 Q2:
  the committed snapshot plus the working tree).

**Additional risks or questions surfaced during reading:**

- `scope-guard`'s design-note status arm (Q1 ii) is *status*-driven and HEAD-keyed. At land
  time the equivalent question is "did this diff modify a file whose HEAD status is
  ratified/superseded" — which is Stop-gate clause (b2), not scope-guard. The two overlap;
  Item 31 must cover the union, and the journal must record which clause each assertion
  discharges, or bp-149 will not be able to tell which hooks are safe to remove.
- A parity test comparing "new says deny" with "old says deny" needs the **old** to be
  runnable. `.claude/hooks/*.sh` are dual-mode (`--standalone`) per `agent-workflow.md` §6's
  failure posture, so the parity harness can shell out to the real hook. ⚑ Per the
  build-plan skill's **falsifier-demo side-effect audit**: `_lib.py`'s scope-check path is
  read-only (it prints a decision; it writes nothing, dispatches nothing, and touches no
  credential — verified by reading `cmd_scope_check`), so no mocking is required for these
  demo runs. Record that audit in the journal; do not skip it because it came out clean.

## 4. Reconciliation

- `.claude/hooks/_lib.py:150 glob_match` → **cross-ref: extension.** Its docstring gains a
  line naming `ops/registry/land.py` as a second consumer, so the parity relationship is
  visible from the matcher. **No behavior change** — `_lib.py` is not in `write_scope` and a
  needed behavior change is a finding (§10).
- `docs/design-notes/agent-workflow.md` §6 (`scope-guard` row) → ⚑ **cross-ref only, and NOT
  by this plan.** The note is ratified and agent-immutable; §3(1) of the registry note makes
  its amendment an owner act. This plan **records** the parity relationship in
  `ops/registry/schema.md` and in the journal; it does not touch the design note, and it does
  not remove the hook the note names.
- `ops/registry/schema.md` → **cross-ref: extension**: gains a "Land-time admission" section
  mapping each `scope-guard` arm to the registry-side assertion that replicates it, and
  stating plainly what is **not** replicated (the mid-flight signal).
- Nothing is corrected in committed code.

## 5. Write scope

- `ops/registry/**` — `land.py` (the admission logic), `levels.py` (the enforcement-level
  field and its validation), edits to `fold.py` for the `scope_level` field, `schema.md`.
- `scripts/registry.py` — the `land` subcommand.
- `tests/unit/test_registry_land.py` — glob matching, denylist, bare-glob detection, levels.
- `tests/integration/test_registry_scope_parity.py` — the parity harness against the real
  hook.

**Deliberately OUT of scope:** ⚑ **every hook script and `.claude/settings.json`** — this
plan removes nothing and registers nothing; `scope-guard` keeps its teeth throughout.
`.claude/hooks/_lib.py` **beyond a docstring cross-reference** (a behavior change there is a
finding — its tests are not in this scope). `docs/design-notes/**` (ratified, and §3(1) makes
the amendment the owner's). The foundation denylist files. `.claude/skills/**` and
`docs/templates/build-plan.md` (the `write_scope`-gains-a-level template edit is bp-148's,
per note §2.7's table). Any worktree/sparse-checkout construction (§3 Q5, parked).

**Retrofit check.** This plan changes no existing symbol; `_lib.py` is read and imported, not
modified. `grep -rn "glob_match\|DENYLIST\|_changed_files" tests/` before starting — those
are `_lib`'s tests, and they must stay green; run them. If any must **change**, that is the
signal that `_lib.py` behavior is moving, and this plan must stop (§10).

## 6. Interfaces pinned inline

### 6.1 What is imported from `_lib.py`, verbatim

```python
# .claude/hooks/_lib.py:150
def glob_match(pattern: str, path: str) -> bool:
    """True if `path` matches `pattern`. `**` spans zero or more segments;
    `*`/`?` stay within a single segment. Both are repo-relative POSIX paths."""

# .claude/hooks/_lib.py:176
def matches_any(path: str, patterns) -> bool:
    return any(glob_match(pat, path) for pat in patterns)

# .claude/hooks/_lib.py:35-39
DENYLIST = [
    "CONSTITUTION.md",
    "eval/golden/**",
    "eval/golden.py",
]

# .claude/hooks/_lib.py:546 — untracked-inclusive by requirement (finding-0003)
def _changed_files() -> list: ...
```

Import idiom (as `scripts/board.py:34-38` does it):

```python
sys.path.insert(0, str(ROOT / ".claude" / "hooks"))
from _lib import DENYLIST, glob_match, matches_any  # type: ignore[import-not-found]
```

### 6.2 The land operation

```python
# ops/registry/land.py
@dataclass(frozen=True)
class LandVerdict:
    ok: bool
    unit_ref: str
    level: str                        # "a" | "b"
    out_of_scope: list[str]           # changed paths outside write_scope
    denylisted: list[str]             # changed paths on the foundation denylist
    immutable: list[str]              # changed paths whose HEAD status is ratified/superseded
    malformed_globs: list[str]        # scope entries containing ' #' (finding-0085)
    reason: str                       # human-readable; names WHICH arm refused

def land(registry: Registry, unit_ref: str, *, root: Path,
         changed: list[str] | None = None) -> LandVerdict:
    """Admit or refuse a unit's landing. `changed` defaults to the untracked-inclusive
    working-tree delta (_lib._changed_files). Refuses if ANY of:
      (i)   a changed path matches DENYLIST                     [scope-guard arm i]
      (ii)  a changed path's HEAD status is ratified|superseded [scope-guard arm ii / Stop (b2)]
      (iii) a changed path matches no write_scope glob          [scope-guard arm iii]
      (iv)  a write_scope entry contains ' #'                   [finding-0085 / bp-066]
    Always writes NOTHING. Landing is a CHECK; the merge is the caller's act."""
```

⚑ The plan's own `plan.md`, its `journal.md`, and `docs/findings/**` are always writable and
are never out-of-scope — the build-plan skill states this, and `land` must reproduce it or
every unit will refuse its own journal.

### 6.3 The enforcement level

```python
# ops/registry/levels.py
# note §2.6, verbatim: "per-unit, not global — write_scope becomes an enforcement LEVEL
# declared at graduation. Default level = (a). Level (b) for units whose blast radius the
# delegation rubric already scores full-strength (enforcement surfaces, core invariants,
# migrations)."
LEVELS = ("a", "b")
DEFAULT_LEVEL = "a"

def level_of(state: EntityState) -> str:
    """The unit's declared enforcement level; DEFAULT_LEVEL when absent. An unknown value is
    an ERROR, never a silent downgrade to (a) — a typo must not weaken enforcement."""
```

⚑ The foundation denylist "binds at admission for **every** unit at **every** level"
(note §2.6) — level (b) never relaxes it, and neither does level (a).

### 6.4 What this plan explicitly does NOT provide (note §2.6, verbatim)

> What is honestly given up at level (a): the mid-flight "you are about to stray" signal. A
> builder discovers the mis-scope at land time with the exact offending diff in hand — later
> than today, cheaper than today's per-write tax.

And §2.1: "a store cannot stop a write to an arbitrary path (the write_scope problem)."
Neither `schema.md` nor any journal entry may claim otherwise.

### 6.5 CLI

```
uv run scripts/registry.py land <unit-ref>            # verdict to stdout; exit 0 == admit
uv run scripts/registry.py land <unit-ref> --json
uv run scripts/registry.py land <unit-ref> --diff-from <ref>   # explicit range, for CI
```

## 7. Items

### Item 29 — the matcher and denylist, imported not rebuilt

- **Objective:** `land.py` resolves a unit's scope and classifies changed paths using
  `_lib`'s own `glob_match`, `matches_any`, and `DENYLIST`.
- **Files:** `ops/registry/land.py`, `tests/unit/test_registry_land.py`
- **Acceptance test:** `uv run pytest tests/unit/test_registry_land.py -q` green over a
  table of (pattern, path, expected) cases lifted from `_lib`'s own semantics — including
  `**` spanning zero segments, `*` not crossing `/`, and a denylist hit under every level.
- **Falsifier:** ⚑ the module imports `fnmatch`, `glob`, or `PurePath.match` anywhere. Assert
  it with an AST scan of `ops/registry/land.py`. A different matcher makes the parity test
  self-referential — it would prove the new code agrees with itself, not with `scope-guard`.
- **Invariant(s) it must not violate:** the denylist binds at every level; `_lib.py` is
  imported, never copied or modified.
- **Touches stored data?** No.
- **Parallelizable?** No.  **Depends on:** bp-140 Item 5.

### Item 30 — scope resolution, and the bare-glob trap

- **Objective:** resolve `write_scope` from the registry (and cross-check the plan's front
  matter), and refuse loudly on a comment-bearing glob.
- **Files:** `ops/registry/land.py`, `tests/unit/test_registry_land.py`
- **Acceptance test:** a unit whose scope contains `- eval/metrics.py  # absorbed` produces
  `malformed_globs == ["eval/metrics.py  # absorbed"]`, `ok is False`, and a `reason` naming
  finding-0085 and the fix ("put the rationale in §5, keep the entry a bare glob"). A unit
  whose registry scope and front-matter scope disagree reports the divergence and refuses.
- **Falsifier:** the malformed glob is silently normalized (comment stripped) and the landing
  admits. That would *hide* the defect while appearing to fix it — the builder's plan would
  keep granting a capability the guard never granted, and the next `scope-guard` denial would
  be as mysterious as it was in bp-066.
- **Invariant(s) it must not violate:** never rewrite a unit's declared scope; report only.
- **Touches stored data?** No.
- **Parallelizable?** Yes.  **Depends on:** Item 29.

### Item 31 — the three-arm verdict, including HEAD-keyed immutability

- **Objective:** `land()` returns a verdict covering all three `scope-guard` arms plus the
  HEAD-keyed ratified-note check, naming which arm refused.
- **Files:** `ops/registry/land.py`, `scripts/registry.py`,
  `tests/unit/test_registry_land.py`
- **Acceptance test:** four fixture landings — a denylist hit, a ratified-note edit, an
  out-of-scope path, and a clean one — each yields the right `ok` and a `reason` naming the
  arm. `uv run scripts/registry.py land <ref>` exits 0 on the clean case and non-zero
  otherwise. The plan's own `plan.md`/`journal.md` and `docs/findings/**` never appear in
  `out_of_scope`.
- **Falsifier:** ⚑ the diff is computed **without** `-uall`. Prove it: create an untracked
  out-of-scope file via a shell write and assert `land` catches it. `agent-workflow.md` §6's
  clarification on (b) (warrant finding-0003) says a plain `git diff` "omits new files
  entirely" — and the Bash-written untracked file is precisely the write the pre-hoc guard
  cannot see, so missing it means the replacement is strictly weaker than the hook.
- **Invariant(s) it must not violate:** `land` writes nothing — it is a read-only verdict.
- **Touches stored data?** No.
- **Parallelizable?** No.  **Depends on:** Items 29, 30.

### Item 32 — the enforcement level as a per-unit field

- **Objective:** `scope_level` is a validated per-unit field with default (a); level (b) adds
  a read-set precondition assertion; an unknown value is an error.
- **Files:** `ops/registry/levels.py`, `ops/registry/fold.py`, `ops/registry/land.py`,
  `tests/unit/test_registry_land.py`
- **Acceptance test:** a unit with no level folds to `"a"`; `scope_level: b` is accepted and
  its landing additionally asserts the recorded read-set; `scope_level: c` raises with a
  named reason (never silently defaults).
- **Falsifier:** an unknown or typo'd level silently degrades to (a). Enforcement that
  weakens on a typo is the failure direction that matters (the same one-directional argument
  `_lib.py:236 _normalize_status` makes for blessing detection: "normalization only ever
  refuses to recognize a malformed blessing, never fabricates one").
- **Invariant(s) it must not violate:** the denylist binds at every level; level (b) never
  relaxes (a)'s checks, it adds to them.
- **Touches stored data?** No.
- **Parallelizable?** Yes.  **Depends on:** Item 31.

### Item 33 — the parity harness against the live hook

- **Objective:** prove, mechanically, that `land()` refuses everything `scope-guard` refuses.
- **Files:** `tests/integration/test_registry_scope_parity.py`, `ops/registry/schema.md`
- **Acceptance test:** for a corpus of ≥ 30 (path, scope) cases spanning all three arms,
  `bash .claude/hooks/scope-guard.sh --standalone <file>` (dual-mode per `agent-workflow.md`
  §6) and `land()` agree on **deny**. `uv run pytest tests/integration/test_registry_scope_parity.py -q`
  green. `schema.md` records the arm-by-arm map and states what is not replicated.
- **Falsifier:** ⚑ **F7's precondition, and the parity claim itself.** Two distinct
  observables: (1) a case where `scope-guard` denies and `land` admits — parity fails and no
  retirement may proceed (this is F4's precondition, and bp-149 must not start); (2) F7
  proper — "measured post-adoption, mis-scoped work discovered at land time costs more
  (rework, abandoned diffs) than today's per-write denials cost in friction." (2) cannot be
  measured before adoption; this item's obligation is to record the **baseline** (how many
  `scope-guard` denials fire per build wave, from the journals) so F7 is measurable later,
  and to state in `schema.md` that F7 is open.
- **Invariant(s) it must not violate:** "a hook is retired only after a registry-side test
  proves its guarantee's parity" (invariant 8) — this test is that proof, and it retires
  nothing itself.
- **Touches stored data?** No. **Side-effect audit for the demo runs:** `cmd_scope_check`
  (`_lib.py:431-478`) prints a decision and writes nothing, dispatches nothing, and reads no
  credential — verified by reading it. No mocking required; the audit is recorded, not
  skipped (build-plan skill, warrant finding-0039 / oq-0017).
- **Parallelizable?** No.  **Depends on:** Items 31, 32.

## 8. Math carried explicitly

N/A — no mathematical object implemented. Glob matching is a string-matching algorithm
imported wholesale from `_lib.py`; the enforcement level is an enumerated field, not a
measure. The blast-radius axis that *does* carry mathematical content lives in
`ops/effect_catalog.py` for effectors, and note §1.2 non-goal 8 keeps it separate ("the
shared reversibility axis is an analogy, not a merger").

## 9. Non-goals

- ⚑ **No hook is retired, edited, weakened, or unregistered.** `.claude/settings.json` is
  untouched; `scope-guard` keeps full teeth. Retirement is bp-149, blocked on owner
  amendments to two ratified notes.
- ⚑ **No claim to replace pre-hoc denial.** The guarantee moves from "before close" to
  "before consequence"; the mid-flight signal is given up knowingly (§6.4).
- **No worktree or sparse-checkout construction** for level (b) — a delegation-harness
  concern, parked (§11).
- **No merge, no push, no commit performed by `land`.** It is a check.
- **No template or skill edit.** `write_scope` gaining an enforcement level in
  `docs/templates/build-plan.md` and `.claude/skills/build-plan/SKILL.md` is bp-148's row of
  note §2.7's table.
- **No `_lib.py` behavior change.**
- **No effector-gate merger** (note §1.2 non-goal 8).
- **No new dependency.**

## 10. Stop-and-raise conditions

- A `_lib.py` **behavior** change proves necessary — stop and file a `codebase` finding.
  `_lib.py`'s tests are outside this scope and every guard reads it.
- Parity fails on any case (Item 33 falsifier 1) — **stop and report**. This is the single
  most consequential outcome of the plan: it means bp-149 must not start, and the note's
  invariant 8 says so.
- The unit's registry scope and front-matter scope disagree in a way the plan cannot
  reconcile (§3 Q6) — report, park the criterion, continue.
- Any temptation to "helpfully" strip a comment from a malformed glob — stop; Item 30's
  falsifier says why.
- Any blessing this plan would have to perform — it must not.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| Level (b) worktree construction | **not built** — the level is declared and its precondition asserted; building the restricted worktree is a delegation-harness concern | building it here — §2.6 flags that it "complicates read-only context", and a registry has no business managing checkouts | The **delegate** skill gains restricted-worktree spawning; prerequisite: an owner ruling on how read-only context is supplied |
| Level assignment heuristics | (a) default; (b) at full-strength blast radius (the note's own parked row) | fixing a rubric now — the note parks it for the first post-registry graduation wave to review | The first post-registry graduation wave reviews the assignments |
| What "landing" means operationally | a check over a diff range, default = worktree vs merge base (§3 Q3) | tying it to `git merge` — would make the registry perform an irreversible external effect it has no license for | The owner wires `land` into a merge script or CI job |
| F7 measurement | baseline recorded (denials per wave from journals); F7 stays **open** | declaring F7 discharged — it is a post-adoption measurement and cannot be run before adoption | Post-adoption, after the first build wave under level (a) |

## 12. Dependency & ordering summary

**Within the plan.** Item 29 (pure matching) → Item 30 (pure scope resolution) → Item 31
(the verdict, reads git) → Item 32 (the level field) → Item 33 (the parity harness, shells
out to the live hook read-only). Blast radius is uniformly minimal: **nothing in this plan
writes anything outside `ops/registry/**`, `scripts/registry.py`, and its two test files.**
`land()` itself is a read-only verdict by construction.

**Across plans.** `depends_on: [bp-140]` — the store and the fold. `parallelizable_with:
[bp-144]` (disjoint scope). Not parallelizable with bp-141/142/143/145 (shared
`ops/registry/**`). **bp-147 depends on this plan** (the journal-gate clause map's land-time
clauses need `land`), and **bp-149 depends on both** — invariant 8 makes this plan's parity
proof the precondition for retiring `scope-guard`. `bp-138`/`bp-139` are independent of this
whole family (note §3(5)).
