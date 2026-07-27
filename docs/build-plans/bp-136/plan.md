---
type: build-plan
id: bp-136
track: workflow
status: proposed
design_ref:
  - docs/design-notes/dn-autopilot-and-delegated-blessing.md
contract: builder
write_scope:
  - scripts/autopilot_halt.py
  - tests/unit/test_autopilot_halt.py
  - .claude/skills/autopilot/SKILL.md
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 200k
  actual: null
depends_on: []
parallelizable_with: [bp-135, bp-137]
created: 2026-07-27
updated: 2026-07-27
links:
  - docs/build-plans/bp-135/plan.md
  - docs/findings/finding-0193.md
  - docs/brainstorms/the-false-success-rule.md
  - .claude/skills/delegate/SKILL.md
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — AP3: the halt list is a total predicate over a declared run state, and every unknown halts

## 0. Mode & provenance

**Graduated from `dn-autopilot-and-delegated-blessing` §2.6 (H1–H8), §2.9 invariants 6 and 7, and
§4's "the halt-list supervisor as orchestrator-session logic (no daemon change)"** (`status:
ratified`). Investigation and planning produced this; implementation proceeds item-by-item on owner
approval. The `proposed → ready` blessing is the owner's and is not performed in any session.

⚑ **Bootstrap wrinkle:** this plan builds part of *delegated* blessing and is itself blessed by the
owner's hand, at the keyboard, because no grant mechanism exists yet. Stated once per wave in
`bp-135` §0 and again here so a reader of this file alone is not misled.

⚑ **Second in the wave, and part of the reason `bp-138` is gated.** §2.6's halt list is one of the
three things that occupy the reviewer's seat the §2.3 grant vacates. It ships **before** the
grant's cryptography, not after (`bp-135` §12).

## 1. Objective

H1–H8 become a **total** classifier over an explicitly declared run state, in which every absent or
undetermined input returns HALT rather than CONTINUE.

## 2. Context manifest

Read in this order, whole files before citing:

1. `docs/design-notes/dn-autopilot-and-delegated-blessing.md` — **§2.6 whole** (H1–H8 and the
   definition of "halt"), **§2.9 invariants 6 and 7**, **§2.4's last paragraph** (the finding-0193
   constraint and the conservative reading), **§1.2 non-goals 3, 5 and 6**, and **§4**'s
   supervisor sentence. The authority for everything below.
2. `docs/findings/finding-0193.md` — the disjoint-ftype constraint H1 inherits.
3. `docs/inbox/owner-questions.md:1624-1672` — **`oq-0047`, ANSWERED 2026-07-26**: *"YES — `ftype`
   BECOMES THE ROUTING AXIS. Option (b)."* ⚑ The ruling has landed; **nothing implements it**
   (§3 Q3). This changes what §2.6's H1 may assume and is the single most important thing to read
   before writing H1.
4. `docs/templates/finding.md:9-11` — the `ftype` and `route` keys as the template spells them
   today (still the pre-`oq-0047` vocabulary).
5. `docs/brainstorms/the-false-success-rule.md:17-31` and `:52-65` — the degenerate-input
   obligation and the mutation companion. ⚑ This plan is **made of** a gate; the rule applies to
   every item.
6. `scripts/capsule.py` — whole. The stdlib-only, secret-free `scripts/` tool this one is modelled
   on, including its argparse shape and its `Field`-dataclass style.
7. `tests/unit/test_capsule.py:414-431` — the AST invariant test to copy (imports allowlist +
   forbidden set).
8. `.claude/skills/delegate/SKILL.md` — whole. The skill this one composes with: worktrees, audit
   right-sizing, the gates that never loosen.
9. `.claude/skills/graduate/SKILL.md` — whole; §2.2's **router** discriminates on this skill's
   session-sizing heuristic, and the new skill must not restate it wrongly.
10. `docs/build-plans/bp-135/plan.md` §6 — the audit-record schema H2 reads.

**DRY audit — does `core/` already have this?** (owner rule.) **No.** There is no run-state type, no
halt classifier, and no supervisor state machine anywhere in the tree. `core/` holds nothing of
this shape — it is the sealed corpus/inference core and this is repo-workflow tooling, which by
standing convention never imports it (`scripts/board.py:17`, `scripts/capsule.py:45-50`,
`scripts/exhaust_report.py:16-19`). What must **not** be re-derived: front-matter parsing —
`_lib.parse_front_matter` via the `scripts/board.py:33-38` `sys.path` idiom (this plan needs it for
H1/H3, which read finding front matter); and the session-sizing heuristic, which lives in
`.claude/skills/graduate/SKILL.md:52-64` and is **cited**, never restated, by the new skill.

## 3. Investigation & grounding

- **Q1 — what run-state inputs actually exist as observable facts, and which do not?** Mixed, and
  the split decides the whole design.
  - **H6 (`HOOK-FAILURE`) is observable and persisted.** Every hook writes the failure into the
    active journal via `python3 "$LIB" marker` — `.claude/hooks/scope-guard.sh:32-36`, the sink at
    `.claude/hooks/_lib.py:1171-1186`. The exact string is
    `HOOK-FAILURE %s: %s — enforcement NOT applied`, identical across all six hooks.
  - **H5 (scope pressure) is NOT persisted.** `cmd_scope_check` (`.claude/hooks/_lib.py:431-477`)
    **prints** `DENY:` and the shell exits 2; nothing writes a denial ledger. **The code does not
    settle how a second denial on the same target is counted** — and nothing in `.claude/state/`
    holds one. What would settle it: either a denial ledger (a new hook write, out of scope here
    and forbidden by this plan's write_scope) or the supervisor counting denials it observes in its
    own tool results. This plan takes the second: H5's input is *declared by the supervisor*, and
    the classifier's job is to refuse when it is absent.
  - **H1/H3 (findings) are observable** — files under `docs/findings/` with `ftype`/`route` front
    matter, enumerable with `board.scan_findings` (`scripts/board.py:199`).
  - **H2 (audit dissent) is observable once `bp-135` lands** — `verdict_artifact` in an audit
    record.
  - **H4 (budget) and H7 (grant validity) are NOT computable here.** Budget is a harness figure
    (`claude -p "/usage"`); grant validity is `bp-138`'s. Both are injected.
  ⇒ **The design that follows from this:** the classifier is a **pure function over a declared
  run-state document**, not a scraper. Some fields it can verify itself; all of them it can refuse
  to assume.
- **Q2 — is there any existing supervisor or halt logic to extend?** **No.** `scripts/palace.py`
  and `ops/lifecycle/` supervise the *daemon*, not agent runs, and §4 explicitly says *"the
  halt-list supervisor as orchestrator-session logic (no daemon change)"*. Nothing to extend, and
  the daemon must not be touched.
- **Q3 — can H1 route on `ftype` today?** **The ruling exists; the mechanism does not.** `oq-0047`
  is **answered** (`docs/inbox/owner-questions.md:1653`): *"YES — `ftype` BECOMES THE ROUTING AXIS.
  Option (b)."* But `grep -rn ftype .claude/hooks/ scripts/ core/` returns **zero** — the same
  emptiness `oq-0047:1669` records — and `docs/templates/finding.md:9` still carries the
  pre-ruling vocabulary `blocker | spec-defect | question | discovery`, while `CLAUDE.md:51-54`
  routes on `design | math | direction` vs `codebase | spec-fidelity`. So the two vocabularies
  remain disjoint **in the artifacts**, exactly as `finding-0193` says. ⚑ Therefore §2.4's
  conservative reading stands and is what this plan implements: *"any finding not unambiguously
  `codebase | spec-fidelity` halts the run."* Implementing `oq-0047`'s ruling is a separate plan;
  this one must not sweep the template (§9).
- **Q4 — does a new skill directory need registering?** **No.** `grep -n 'skill' .claude/settings.json`
  returns nothing; the eight directories under `.claude/skills/` are discovered by directory. A
  ninth, `autopilot/`, needs no settings change — which is fortunate, because `.claude/settings.json`
  is out of scope.
- **Q5 — what may this script import?** stdlib + `_lib` reuse. `scripts/check_imports.py:2-11`
  constrains `core/` and the worker boundary only, **not** `scripts/`; the stdlib-only convention
  is enforced **per script by its own AST test** (`tests/unit/test_capsule.py:414-431`,
  `tests/unit/test_exhaust_report.py:163-179`) and by nothing else. A new script gets no discipline
  unless this plan writes its AST test — Item 9 does.
- **Q6 — mypy/ruff enrollment?** Automatic. `pyproject.toml:128` lists `scripts` as a whole
  directory and CI runs it as a **Tier-2 hard floor, 0 errors**
  (`.github/workflows/ci.yml:71`). ruff: `line-length = 100`, no per-file ignore covers `scripts/`
  (`pyproject.toml:104-112`). The `sys.path` bootstrap needs `# noqa: E402` on the imports that
  follow it and `# type: ignore[import-not-found]` on the `_lib` import (`scripts/board.py:35`).

**Additional risks or questions surfaced during reading:**

⚑ **"Halt" is defined in §2.6 as five actions, of which this classifier performs none.** §2.6:
*"halt meaning: stop work, checkpoint the journal, file what exists, park with a re-entry
condition, notify via the exhaust lane."* A classifier that *decides* is not a supervisor that
*acts*. The split is deliberate — a pure decision function is testable and a side-effecting one is
not — but it means the **skill** (Item 13) carries the five actions as an obligation on the
supervisor, and the classifier's output names which of them are owed. If those two ever disagree,
the skill is authoritative for behaviour and the classifier for the decision.

⚑ **H8 is a halt, not a completion ceremony.** §2.6 H8 ends: *"Autopilot then **stops**: no merge,
no deskcheck, no self-declared done."* The classifier must therefore have **no** output value that
means "done" in the deskcheck sense — its terminal value is `HALT (H8 — complete, merge-ready)`.
Non-goals 5 and 6 of the note are enforced by the absence of a vocabulary word, which is the
cheapest possible enforcement and worth stating.

## 4. Reconciliation

- `dn-autopilot-and-delegated-blessing.md:321` / §2.4's P3 → **[banner: correction]**, carried by
  `bp-137`, not here. Recorded so this plan's reader knows the sibling carries it.
- `.claude/skills/graduate/SKILL.md:52-64` (the session-sizing heuristic) →
  **[cross-ref: extension]**. §2.2's router discriminates on exactly this heuristic. The new
  `autopilot` skill **links** to it and does not restate it: a second copy of a heuristic is the
  duplication the owner grades as a defect, and a drifted copy inside an autopilot skill would
  route real work into the wrong lane. Proposed text: *"The router's discriminators are the
  graduate skill's session-sizing heuristic, read early — see `.claude/skills/graduate/SKILL.md`
  §Session-sizing heuristic. It is not restated here; if the two ever disagree, graduate wins."*
- `.claude/skills/delegate/SKILL.md` → **[cross-ref: extension]**. The autopilot skill composes
  with delegate (worktrees, audit right-sizing) rather than replacing it; it links and states the
  one thing that differs — under a grant the orchestrator's **blessing authority is replaced by the
  grant**, and every other gate is unchanged (`dn-autopilot-and-delegated-blessing.md:493-496`).
  ⚑ No edit is made to `delegate/SKILL.md`: it is out of `write_scope`, and a cross-reference from
  the new file is sufficient in the direction that matters.

## 5. Write scope

Three paths, all **new**:

- `scripts/autopilot_halt.py` — the classifier. stdlib + `_lib` reuse; no `os`, no `subprocess`,
  no `core`, no `config`.
- `tests/unit/test_autopilot_halt.py` — the falsifiers, the degenerate inputs and the AST
  invariant, executable.
- `.claude/skills/autopilot/SKILL.md` — the supervisor's operating contract: what a run is, the
  five halt actions, how the two audit gates are spawned, and the list of things autopilot never
  does.

**Deliberately OUT of scope** — a denial means file a finding, never widen by hand:

- `.claude/hooks/**` and `.claude/settings.json` — no hook, no denial ledger, no gate change. H5's
  un-persisted denial is handled by declaration (§3 Q1), not by teaching a hook to write state.
  The `oq-0036` questions are parked.
- `.claude/skills/delegate/SKILL.md`, `.claude/skills/graduate/SKILL.md` — cross-referenced from
  the new file only (§4).
- `docs/templates/finding.md` — `oq-0047`'s ruling is real but its implementation is a separate
  plan; sweeping the template here would be a vocabulary change nobody asked this plan for (§9).
- `scripts/board.py` — `bp-135` owns it this wave; disjoint scope is what makes the three plans
  parallelizable.
- `docs/design-notes/**` (A8, agent-immutable) and the foundation denylist (`CONSTITUTION.md`,
  `eval/golden/**`, `eval/golden.py`), which binds regardless.

**Acceptance-reachability check** (findings 0177/0191/0204):

| item | files its acceptance must modify | all in §5? |
|---|---|---|
| 9 | `scripts/autopilot_halt.py`; `tests/unit/test_autopilot_halt.py` | ✓ |
| 10 | same two | ✓ |
| 11 | same two | ✓ |
| 12 | same two | ✓ |
| 13 | `.claude/skills/autopilot/SKILL.md`; `tests/unit/test_autopilot_halt.py` (the link-resolution test) | ✓ |

Non-obvious targets checked: **no protocol member** on an out-of-scope class; **no
allowlist/registry enrollment** — `pyproject.toml:128` covers `scripts/` by directory and
`.claude/settings.json` registers no skills (§3 Q4/Q6); **no test outside this plan's own test
file** asks the changed surface a question, because every surface here is new. Item 13's acceptance
asserts that the skill's cross-reference targets **resolve** — that reads `.claude/skills/*/SKILL.md`
but writes only this plan's own two files.

## 6. Interfaces pinned inline

**§2.6's halt list, verbatim** (`dn-autopilot-and-delegated-blessing.md:388-415`), because the
builder must implement these eight and not eight paraphrases:

> Any one of these halts the run — halt meaning: stop work, checkpoint the journal, file what
> exists, park with a re-entry condition, notify via the exhaust lane:
> **H1 — owner-level finding.** Any finding routed `orchestrator` (`design | math | direction`,
> conservatively read per §2.4). … A low-stakes run that raises a design question has left the
> low-stakes envelope by that very fact.
> **H2 — audit dissent** per §2.5 (intent-level immediately; mechanism-level after the one
> permitted remediation cycle).
> **H3 — blocker finding.** Already ends any session.
> **H4 — budget.** Token/cost ceiling from the capsule, or `session_budget` exhausted. Neither is
> self-extendable.
> **H5 — scope pressure.** A second scope-guard denial on the same target. …
> **H6 — enforcement failure.** Any `HOOK-FAILURE` line. … autopilot must not self-reconcile its
> own cage.
> **H7 — grant void.** Capsule/plan hash mismatch at any checkpoint, TTL expiry, or base drift
> (§2.3). Also fired if the flip commit's grant record fails offline re-verification.
> **H8 — completion (the only terminal halt).** All acceptance closed, Gate B CLEAN, artifacts
> filed (§2.7), branch merge-ready. Autopilot then **stops**: no merge, no deskcheck, no
> self-declared done.

**§2.4's conservative H1 reading, verbatim** (`:345-348`): *"Until the owner rules on the
authoritative set, autopilot applies the conservative reading — **any finding not unambiguously
`codebase | spec-fidelity` halts the run.** Ambiguity resolves toward stopping."*

**Invariant 7, verbatim** (`:471`): *"Ambiguity — in routing, in a verdict, in a hash check —
always resolves toward halting."*

**The run-state document — DEFINED HERE** (the note describes inputs in prose; no schema exists).
A JSON object. **Every key is required. An absent key is not a default — it is `HALT (H0)`.**

```json
{
  "plan": "bp-NNN",
  "capsule_hash": "<64 lowercase hex>",
  "findings_dir": "docs/findings",
  "findings_since_base": ["finding-NNNN", "..."],
  "audits_dir": "docs/audits",
  "remediation_cycles_used": 0,
  "budget_tokens_used": 0,
  "budget_tokens_ceiling": 0,
  "session_budget_remaining": 1,
  "scope_denials": [{"target": "<path>", "count": 0}],
  "journal_path": "docs/build-plans/bp-NNN/journal.md",
  "grant_valid": true,
  "grant_checked": true,
  "acceptance_all_closed": false,
  "artifacts_filed": false,
  "branch_merge_ready": false
}
```

**The verdict — DEFINED HERE.** `classify(state) -> Verdict`, a frozen dataclass:

```python
@dataclass(frozen=True)
class Verdict:
    halt: bool
    code: str            # "H0".."H8", or "CONTINUE"
    reason: str          # one line, names the field that decided
    actions_owed: tuple[str, ...]   # the five §2.6 halt actions still owed; () when CONTINUE
```

`code` is drawn from exactly: `CONTINUE`, `H0` (undetermined), `H1`…`H8`. **There is no value
meaning "done", "merge" or "deskcheck"** — §1.2 non-goals 5 and 6 enforced by vocabulary (§3).

**Precedence — DEFINED HERE, because §2.6 lists conditions without an order and two can fire at
once.** Evaluate in this fixed order and return the first hit: `H0` (any required key absent,
null, or of the wrong type) → `H6` → `H7` → `H3` → `H1` → `H2` → `H5` → `H4` → `H8` →
`CONTINUE`. Rationale, one line each, to be reproduced in the module docstring: enforcement failure
first because it voids the run's premise; grant void next because it voids the run's authority;
then the finding classes by severity; then process pressure; then budget; completion last, since
completion is only meaningful if nothing else fired.

**The five halt actions, verbatim from §2.6**, which populate `actions_owed`:
`stop work` · `checkpoint the journal` · `file what exists` · `park with a re-entry condition` ·
`notify via the exhaust lane`.

**CLI surface — DEFINED HERE:**

```
uv run scripts/autopilot_halt.py classify <run-state.json>
    -> prints "<code>: <reason>" to stdout; exits 0 for CONTINUE, 1 for any halt
uv run scripts/autopilot_halt.py classify -            # reads the JSON from stdin
uv run scripts/autopilot_halt.py explain               # prints H0..H8 and the precedence order
```

⚑ **Exit 1 means "halt", which is the SAFE outcome** — the inversion is deliberate and must be
documented in the module docstring, because a caller that treats non-zero as "tool broke" and
proceeds has inverted the entire mechanism. The `explain` subcommand exists so that inversion is
one command away from being caught.

**Reuse, verbatim** (`scripts/board.py:33-38`):

```python
sys.path.insert(0, str(ROOT / ".claude" / "hooks"))
from _lib import parse_front_matter  # type: ignore[import-not-found]  # noqa: E402
```

## 7. Items

Ordered by blast radius: the total-function skeleton that refuses on absence → the observable
conditions → the injected conditions → the terminal condition → the prose contract. Item numbering
continues the family (`bp-120` used 1–4, `bp-135` uses 5–8).

### Item 9 — the run-state schema and H0: absence is a halt

- **Objective:** `classify` is **total** — every input, including a malformed or partial one,
  returns a `Verdict`, and every unknown returns `HALT`.
- **Files:** `scripts/autopilot_halt.py`, `tests/unit/test_autopilot_halt.py`
- **Acceptance test:** `uv run pytest tests/unit/test_autopilot_halt.py -q` green on: the §6
  key list is required; each of the sixteen keys, removed one at a time, yields
  `H0` naming that key; a key present but `null` yields `H0`; a key of the wrong type
  (`"grant_valid": "yes"`) yields `H0`; unparseable JSON yields `H0` and no traceback; an **extra**
  unknown key yields `H0` (a run state the classifier does not fully understand is not one it may
  clear).
- **Falsifier:** a real supervisor cannot assemble sixteen fields honestly, so it fills some with
  guesses — then `H0` never fires and the strictness bought nothing. ⚑ Drill it: the builder
  hand-assembles one run state for a plausible trivial run (the spell-check class) and records in
  the journal which fields it could **not** fill from observable facts. If more than two are
  guesses, the schema is wrong and that is a `spec-defect`, not a number to soften.
- **⚑ Degenerate input (false-success rule):** **the empty object `{}`**. A classifier written the
  obvious way — walk H1…H8, return `CONTINUE` if none matched — returns **CONTINUE** on `{}`. That
  is the check passing without testing its claim, on the input that means *nothing was observed at
  all*, and it is invariant 7 inverted. Assert `classify({})` returns `halt=True, code="H0"`.
  Assert the same for `{"plan": "bp-999"}`.
- **Invariant(s) it must not violate:** invariant 7 (ambiguity resolves toward halting). stdlib +
  `_lib` only; no `os`, no `subprocess`, no `core`, no `config` — asserted by an AST test in the
  same file modelled on `tests/unit/test_capsule.py:414-431`, using `ast.walk` (which catches
  imports nested in function bodies, as the precedent already does).
- **Touches stored data?** No.
- **Parallelizable?** no  **Depends on:** none

### Item 10 — H1, H3, H6: the conditions the classifier can verify itself

- **Objective:** the three halt conditions with observable evidence are decided from that evidence,
  not from a declaration.
- **Files:** `scripts/autopilot_halt.py`, `tests/unit/test_autopilot_halt.py`
- **Acceptance test:** green on fixtures under `tmp_path`: **H3** fires for any finding in
  `findings_since_base` whose front-matter `ftype` is `blocker`; **H1** fires for any such finding
  whose `route` is `orchestrator` **or** whose `ftype`/`route` pair is not unambiguously
  `codebase | spec-fidelity` (the §6 conservative reading, quoted in the docstring); **H1 does not
  fire** for a finding explicitly `route: builder` with `ftype: spec-defect`; **H6** fires when
  `journal_path`'s contents contain the literal `HOOK-FAILURE`; **H6 fires** when `journal_path`
  does not exist (an unreadable journal is an unchecked one).
- **Falsifier:** H1 fires on essentially every run because real builders file `question`/`discovery`
  findings routinely — then the conservative reading makes autopilot unusable rather than safe, and
  `finding-0193`'s constraint is not merely inconvenient but disqualifying. ⚑ Drill it: run H1
  against the **real** `docs/findings/` corpus (read-only) and record in the journal what fraction
  of the last 30 findings would have halted a run. That number is the honest cost of the
  conservative reading and belongs in the seal.
- **⚑ Degenerate input (false-success rule):** **`"findings_since_base": []` versus the key being
  absent.** An empty list is a real observation ("I looked, there were none"); an absent key is
  "nobody looked". The naive implementation cannot tell them apart and passes both. Assert `[]`
  yields no H1/H3 and absence yields `H0` (Item 9). Second degenerate: **a finding id in the list
  with no corresponding file** — a check that iterates only over files it can open silently skips
  it and passes; assert an unresolvable finding id yields `H0`, per `CONSTITUTION.md` §III.1
  (*"A cited identifier that does not resolve is a failure"*).
- **⚑ Mutation obligation** (`the-false-success-rule.md:52-65`, `finding-0249`): H1 is the
  load-bearing leg. Run at least: (m1) relax H1 to fire only on `route: orchestrator` (dropping the
  conservative arm); (m2) make the missing-journal case in H6 return `CONTINUE`; (m3) make H3
  case-sensitive so `Blocker` slips through. Each must be caught by a named test; record the
  campaign in the journal.
- **Invariant(s) it must not violate:** read-only with respect to `docs/findings/` and the journal.
  Reuses `_lib.parse_front_matter`; re-deriving a front-matter parser is a DRY defect
  (`CONVENTIONS.md:10`).
- **Touches stored data?** No.
- **Parallelizable?** no  **Depends on:** Item 9

### Item 11 — H2, H4, H5, H7: the injected conditions, and the seam that keeps this plan independent of `bp-138`

- **Objective:** the four conditions whose evidence lives outside this tool are decided from
  declared inputs, and a missing declaration halts.
- **Files:** `scripts/autopilot_halt.py`, `tests/unit/test_autopilot_halt.py`
- **Acceptance test:** green on: **H2** fires when any audit record for `plan` in `audits_dir` has
  `verdict_artifact != clean`, immediately if the record is intent-level and after
  `remediation_cycles_used >= 1` otherwise; **H4** fires when `budget_tokens_used >=
  budget_tokens_ceiling` or `session_budget_remaining <= 0`; **H5** fires when any entry in
  `scope_denials` has `count >= 2`; **H7** fires when `grant_valid` is false **or**
  `grant_checked` is false. Plus: `budget_tokens_ceiling == 0` yields `H0`, not a vacuous H4 pass.
- **Falsifier:** H2's intent-vs-mechanism distinction cannot be made from an audit record's fields
  — the record says `concerns` but not *at what layer* — so the "one remediation cycle" rule is
  unimplementable as specified. ⚑ If so, that is a `spec-defect` against §2.5 **and** against
  `bp-135` §6's schema, filed as a finding; the conservative fallback (treat every `concerns` as
  intent-level, i.e. halt immediately) is applied and stated, never a guess at layer.
- **⚑ Degenerate input (false-success rule):** **`"grant_valid": true, "grant_checked": false`** —
  a declaration that the grant is fine from a caller that never checked. A classifier reading only
  `grant_valid` passes. Assert `grant_checked: false` yields H7 regardless of `grant_valid`. Second
  degenerate: **`"scope_denials": []`** where the supervisor simply never collected denials — the
  same `[]`-vs-absent ambiguity as Item 10, resolved the same way (absence ⇒ `H0`), and the skill
  (Item 13) makes collecting them an explicit supervisor obligation.
- **Invariant(s) it must not violate:** ⚑ **This item computes no grant validity and imports
  nothing from `bp-138`.** `grant_valid` is data. That is what keeps the halt list buildable
  *before* the grant's cryptography exists, which is the wave's ordering constraint
  (`bp-135` §12). Budget is likewise never self-extendable here — the classifier has no writer.
- **Touches stored data?** No.
- **Parallelizable?** no  **Depends on:** Item 9

### Item 12 — H8: the terminal halt, and the words the classifier cannot say

- **Objective:** completion is a **halt**, and the classifier has no vocabulary for merging or
  deskchecking.
- **Files:** `scripts/autopilot_halt.py`, `tests/unit/test_autopilot_halt.py`
- **Acceptance test:** green on: H8 fires only when **all four** of `acceptance_all_closed`,
  Gate B present-and-`clean` (read from `audits_dir`), `artifacts_filed` and `branch_merge_ready`
  are true, and every other condition is clear; H8's `halt` is `True`; `actions_owed` contains the
  five §2.6 actions; and a source-level assertion that the module's verdict-code vocabulary is
  exactly `{CONTINUE, H0..H8}` — the literals `merge`, `deskcheck`, `done` and `complete` appear
  in **no** verdict `code` anywhere in the module.
- **Falsifier:** a supervisor reads `H8` and merges. Then the halt list did not prevent the thing
  non-goal 5 exists to prevent, and the enforcement has to move from vocabulary into the skill's
  procedure — or into a real gate. ⚑ Drill it: the builder greps the new skill for every place
  H8's meaning is stated and confirms all of them say "stop", none say "merge".
- **⚑ Degenerate input (false-success rule):** **all four booleans true and the audits directory
  empty.** "Gate B is not `concerns`" is true of a directory with no Gate B in it, so a check
  phrased negatively returns H8 — declaring a run complete with **no audit at all**, which is the
  precise failure §2.7 exists to prevent. Assert H8 **does not** fire when Gate B is absent; assert
  the result is `H0`, not `CONTINUE`.
- **Invariant(s) it must not violate:** non-goals 5 and 6 (never merges to main; the deskcheck is
  never delegable). Invariant 6: every halt leaves a parked state with a re-entry condition —
  `actions_owed` is non-empty for every halt code including H8.
- **Touches stored data?** No.
- **Parallelizable?** no  **Depends on:** Items 10, 11

### Item 13 — `.claude/skills/autopilot/SKILL.md`, the supervisor's operating contract

- **Objective:** the classifier has an operator: a skill stating what a run is, what the five halt
  actions are, how the two audit gates are spawned, and the list of things autopilot never does.
- **Files:** `.claude/skills/autopilot/SKILL.md`, `tests/unit/test_autopilot_halt.py`
- **Acceptance test:** the file exists with the standard skill front matter (`name`, `description`
  — the shape used by the eight existing skills); a test asserts it contains: all eight halt codes
  `H1`–`H8`; the five halt actions verbatim; the §1.2 non-goals list (**`draft → ratified` is
  permanently non-delegable · autopilot never originates a goal · autopilot never merges to main ·
  `deploy` stays owner-in-loop · the deskcheck is never delegable · one grant, one plan**); the
  literal sentence that **exit 1 from `autopilot_halt.py` means HALT, the safe outcome**; and
  cross-references to `graduate`, `delegate` and `finding`. A second test asserts **every relative
  path the skill cites resolves to an existing file** — the `CONSTITUTION.md` §III.1 rule applied
  to the skill's own citations.
- **Falsifier:** the skill duplicates the graduate skill's session-sizing heuristic instead of
  linking it (§4). Two copies drift, and a drifted router sends design-scale work into autopilot —
  which is the one thing §2.2's router exists to prevent. ⚑ Drill it: grep the new skill for the
  heuristic's distinctive phrases (`needs an "and"`, `sprawls across zones`); a hit is the
  falsifier firing.
- **⚑ Degenerate input (false-success rule):** **a skill file containing every required literal
  inside a fenced code block or an HTML comment.** A `substring in text` check passes on prose that
  is not in force. Assert the link-resolution test reddens on a cited path that does not exist, and
  that the non-goals check reads the rendered prose rather than the whole file including comments.
- **Invariant(s) it must not violate:** it registers nothing in `.claude/settings.json` (§3 Q4) and
  edits no existing skill (§5). It describes the supervisor; it grants nothing.
- **Touches stored data?** No.
- **Parallelizable?** yes  **Depends on:** Item 12 (so the vocabulary it documents is final)

## 8. Math carried explicitly

`N/A — no mathematical object implemented.` The classifier is a total function over a finite
labelled product; there is no measure, estimator, or geometric object. The wave's one mathematical
object is `bp-138` §8.

## 9. Non-goals

1. **No supervisor is built.** This plan builds a decision function and its operating contract.
   Nothing in it stops work, checkpoints a journal, files an artifact, or notifies anything — the
   five §2.6 actions are the supervising *session's*, per §4's "orchestrator-session logic".
2. **No grant validity is computed.** `grant_valid` is injected (Item 11). `bp-138` owns the
   cryptography, and this plan is deliberately buildable before it.
3. **No denial ledger, no hook change, no `.claude/settings.json`.** H5 reads a declaration
   (§3 Q1).
4. **No `ftype` sweep.** `oq-0047` ruled ftype the routing axis and nothing implements it; the
   conservative reading §2.4 licenses is what ships here. Implementing the ruling — and updating
   `docs/templates/finding.md:9` — is its own plan (§11 row 1).
5. **No audit records are written or spawned.** `bp-135` owns the record; this plan reads it.
6. **No merge, no deskcheck, no "done".** Enforced by the absence of the vocabulary (Item 12).
7. **No secret, no HMAC, no MFA code, no status flip of anything.** [INFERENCE — that a halt
   classifier needs no authority whatsoever to do its job. If a future supervisor wants the
   classifier to *act*, that is a different tool with a different blast radius and a different
   plan.]

## 10. Stop-and-raise conditions

STOP and surface rather than proceed if:

- H2's intent-vs-mechanism distinction proves unmakeable from `bp-135`'s record schema (Item 11's
  falsifier) — file a `spec-defect` against §2.5 and `bp-135` §6, apply the conservative fallback,
  park the criterion, continue.
- the conservative H1 reading halts on a majority of real findings (Item 10's falsifier) — record
  the measurement, file a `design` finding routed to the orchestrator, and **do not** soften the
  rule on your own authority. Ambiguity resolves toward stopping (invariant 7); making autopilot
  usable by loosening its halt list is exactly the drift this note exists to prevent.
- any acceptance appears to need a file outside §5 — finding, park, continue. **Never widen the
  scope by hand and never route around a `scope-guard` denial**; a second denial on the same target
  means the plan is mis-scoped (which is H5, filed against this plan itself).
- a `HOOK-FAILURE` line appears — rerun the named hook standalone, reconcile, say so in the journal
  before continuing. ⚑ Note the recursion: that is H6 applied to the session building H6.
- **any item would give this code a secret, an MFA code, or the power to flip a status.** It needs
  none of the three. If one appears necessary, that is not a design choice — stop and raise it.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| H1's routing vocabulary while `oq-0047`'s ruling is unimplemented | §2.4's conservative reading: any finding not unambiguously `codebase \| spec-fidelity` halts | *Route on `ftype` now* — rejected: `oq-0047` is answered but `grep -rn ftype .claude/hooks/ scripts/ core/` is empty and `docs/templates/finding.md:9` still carries the old vocabulary, so routing on it would read a field nobody writes. *Route on `route:`* — rejected: `finding-0193` shows the two vocabularies are disjoint in the artifacts | A plan implements `oq-0047` (ftype as the routing axis, template + a reader); then H1 routes on the authoritative set |
| How a second scope-guard denial is counted, given no ledger exists | The supervisor declares `scope_denials`; the classifier refuses when the key is absent | *Teach `scope-guard` to write a ledger* — rejected: a hook change, out of scope, and `oq-0036`'s enforcement questions are parked. *Drop H5* — rejected: it is one of the eight the note enumerates, and dropping a halt condition is a design act | `oq-0036`'s Fable pass rules on hook-side state, or a run demonstrates the declaration is unreliable |
| Whether the classifier should also *perform* the five halt actions | No — pure decision function; the skill carries the actions as a supervisor obligation | *One tool that decides and acts* — rejected: a side-effecting classifier is untestable, and §4 puts the supervisor in the orchestrator session, not in a script | A supervisor implementation exists and the split proves to cause drift between decision and action |
| Precedence order among simultaneously-firing halt conditions | Fixed order pinned in §6 (`H0→H6→H7→H3→H1→H2→H5→H4→H8`) | *Report all firing conditions* — rejected: a halt is a halt; a list invites triage, and triage is where an unattended run talks itself past a stop. *Alphabetical/numeric order* — rejected: it would put H1 ahead of H6, deciding on findings before noticing enforcement never applied | The order produces a misleading `reason` in a real run |

## 12. Dependency & ordering summary

**Within the plan:** Item 9 first and alone (everything composes on the total-function skeleton).
Items 10 and 11 are independent of each other and both depend on Item 9. Item 12 depends on both.
Item 13 depends on Item 12 so the vocabulary it documents is final. Blast-radius order is the item
order: pure function → read-only file reads → injected data → terminal condition → prose. Nothing
is irreversible; every effect is a new file under `git`.

**Across the wave:** see `bp-135` §12 for the full map, the three un-minted stages
(**AP-actor** parked on `oq-0037` + `finding-0262`; **AP-posthoc** parked on `oq-0036`;
**AP-const** parked on the owner's A10 amendment) and the blessing-round recommendation. This plan
is `parallelizable_with: [bp-135, bp-137]` — three disjoint write scopes, no shared file. ⚑ It has
**no `depends_on`** and must not acquire one: its independence from `bp-138` is the property that
lets the reviewer's seat be filled before the grant's cryptography exists.
