---
type: build-plan
id: bp-137
track: workflow
status: proposed
design_ref:
  - docs/design-notes/dn-autopilot-and-delegated-blessing.md
contract: builder
write_scope:
  - scripts/autopilot_eligibility.py
  - tests/unit/test_autopilot_eligibility.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 200k
  actual: null
depends_on: []
parallelizable_with: [bp-135, bp-136]
created: 2026-07-27
updated: 2026-07-27
links:
  - docs/findings/finding-0263.md
  - docs/findings/finding-0193.md
  - docs/brainstorms/the-false-success-rule.md
  - docs/build-plans/bp-120/plan.md
re_entry: null
supersedes: null
superseded_by: null
warrant: docs/findings/finding-0263.md
---

# Build Plan — AP4: "low stakes" becomes a conjunctive structural predicate that refuses on absence exactly as it refuses on violation

## 0. Mode & provenance

**Graduated from `dn-autopilot-and-delegated-blessing` §2.4 (P1–P5) and §2.8 (the reversibility
mapping P1–P4 discharges)** (`status: ratified`). Investigation and planning produced this;
implementation proceeds item-by-item on owner approval. The `proposed → ready` blessing is the
owner's and is not performed in any session.

⚑ **Bootstrap wrinkle:** this plan builds part of *delegated* blessing and is itself blessed by the
owner's hand, at the keyboard, because no grant mechanism exists yet. Stated once per wave in
`bp-135` §0 and again here so a reader of this file alone is not misled.

⚑ **Warrant: `finding-0263`.** Grounding found that §2.4's P3 cites a machine-readable per-item
flag that **does not exist** — `touches_stored_data` is free prose with at least twenty spellings
across 111 plans, and the literal `touches_stored_data: false` appears in **zero** of them. A P3
built to the note's text passes on every plan in the repository, including one that rewrites the
vector store. This plan carries the correction (§4) rather than inheriting the defect.

⚑ **Third of the three seat-filling plans.** The eligibility predicate is the *necessary* condition
the verifier evaluates **before** it will accept any code (§2.4). It ships before the grant's
cryptography (`bp-135` §12).

## 1. Objective

P1–P5 become a conjunctive, mechanically-checkable predicate over a plan's own fields in which an
undetermined term fails the conjunction rather than passing it.

## 2. Context manifest

Read in this order, whole files before citing:

1. `docs/design-notes/dn-autopilot-and-delegated-blessing.md` — **§2.4 whole** (the P1–P5 table,
   the necessary-vs-sufficient split, the `finding-0193` paragraph), **§2.8 whole** (why P1–P4
   *are* the reversibility guarantee), **§1.2 non-goals 4 and 8**, **§2.9 invariants 5 and 7**, and
   the out-of-scope clause at `:102-104` (the foundation denylist is unreachable regardless of
   MFA). The authority for everything below.
2. `docs/findings/finding-0263.md` — this plan's `warrant`: the measured spelling census and the
   two degenerate readings of P3.
3. `docs/templates/build-plan.md` — whole. The shape P1–P5 reads: front-matter `write_scope`
   (`:9-13`), `session_budget` (`:14`), and the per-item body flag at `:111`.
4. `docs/build-plans/bp-120/plan.md` — a real, complete plan of this family to test against; its
   §7 items carry the flag in the `- **Touches stored data?** no` form.
5. `.claude/hooks/_lib.py:126-178` — `_seg_match` / `glob_match` / `matches_any`, the hand-rolled
   `**`-aware matcher `scope-guard` itself uses. ⚑ **P1/P2 must reuse this, not re-derive glob
   semantics** — a predicate whose glob math differs from the guard's would grant eligibility on a
   scope the guard reads differently.
6. `.claude/hooks/_lib.py:180-233` — `parse_front_matter` and `_scalar`, including the
   quoted-vs-unquoted comment-stripping asymmetry (§3 Q4).
7. `scripts/capsule.py` — whole. The stdlib-only, secret-free `scripts/` tool this one is modelled
   on; §6 pins the capsule's `achievable` field, which carries this predicate's output.
8. `docs/brainstorms/the-false-success-rule.md:17-31`, `:52-65` — the degenerate-input obligation
   and the mutation companion. ⚑ Every item here delivers a **gate**; the rule applies to all four.

**DRY audit — does `core/` already have this?** (owner rule.) **No, and the relevant reuse is
outside `core/`.** There is no eligibility predicate, no stakes check, and no plan-field validator
anywhere. What must **not** be re-derived, and what this plan reuses verbatim through the
`scripts/board.py:33-38` `sys.path` idiom: `_lib.glob_match` / `_lib.matches_any` (the guard's own
matcher) and `_lib.parse_front_matter` / `_lib._normalize_status`. Re-implementing glob semantics
would be a duplicated implementation — a defect, not a nit (`CONVENTIONS.md:10`) — and here it
would be a *security-relevant* one, because two matchers that disagree mean the predicate blesses a
scope the guard would read differently.

## 3. Investigation & grounding

- **Q1 — does `touches_stored_data: false` exist anywhere as a machine-readable field?** **No.**
  Measured 2026-07-27 over `docs/build-plans/*/plan.md`: 111 plans carry the flag, the literal
  string `touches_stored_data: false` appears in **zero**, and the prose form has ≥20 spellings.
  The top eight by count are tabulated in `docs/findings/finding-0263.md`. The template's own form
  is prose: `docs/templates/build-plan.md:111` — `- **Touches stored data?** <yes/no — blast-radius
  flag; …>`. `docs/design-notes/agent-workflow.md:80` lists it among **body-section** fields
  explicitly contrasted with front-matter keys. ⇒ P3 must parse the §7 **body**, and it must refuse
  every hedged spelling.
- **Q2 — what does `write_scope` look like in practice, and what breaks a naive P1?** Front-matter
  block list of bare globs (`docs/templates/build-plan.md:9-13`), read by
  `_lib.plan_write_scope` (`.claude/hooks/_lib.py:354-361`) and matched by the hand-rolled
  `glob_match` (`:150-174`). ⚑ Three real shapes P1 must handle and the guard already does:
  `**` segments; an entry with an inline `#` comment, which `_scalar` (`:218-233`) leaves **glued**
  to the glob when unquoted (the `bp-066`/finding-0085 footgun) — such an entry matches nothing, so
  a *scope-guard-denied* plan can look P1-clean; and `docs/findings/**` plus the plan's own
  `plan.md`/`journal.md`, which the guard **adds** at `:464-466` and which are therefore in the
  effective scope even when absent from the list.
- **Q3 — is `scope-guard`'s allow-set the same as `write_scope`?** **No, and P1/P2 must use the
  effective set.** `cmd_scope_check` widens it at `.claude/hooks/_lib.py:464-466`:
  ```python
  allowed = list(plan_write_scope(plan))
  plandir = os.path.dirname(plan)
  allowed += [plan, f"{plandir}/journal.md", "docs/findings/**"]
  ```
  A P2 that checks only the declared list would miss that every plan can always write
  `docs/findings/**`. That is fine for P2's forbidden set (findings are not enforcement surfaces),
  but the asymmetry must be **stated in the report**, not silently dropped.
- **Q4 — can `_lib.parse_front_matter` read everything P1/P2/P5 need?** Yes for `write_scope`
  (block list), `session_budget` (scalar) and `design_ref` (block list). ⚑ It is a **YAML subset**
  parser (`:180-182`): scalars and simple block/flow lists only, no nesting, and `null` returns as
  the literal string `"null"` (which is why `scripts/board.py:58-67` has `_is_absent`). P5 must
  therefore treat `"null"`, `""` and a missing key as the same thing: **undetermined ⇒ fail**.
- **Q5 — what is in P2's forbidden set, exactly?** §2.4 pins it verbatim (§6). Note it is
  **broader** than the foundation denylist: it walls off the *whole* design-note tree and the
  enforcement surfaces, while the denylist (`CONSTITUTION.md`, `eval/golden/**`, `eval/golden.py`)
  binds beneath every grant regardless (`:102-104`, invariant 5). P2 checks the §2.4 set; the
  denylist is not P2's to re-implement and is asserted separately as an invariant.
- **Q6 — how does P4 detect a "live-state mutation"?** ⚑ **The code does not settle this.** §2.4's
  P4 reads *"no acceptance step or action runs `deploy`, `palace` lifecycle mutation, or any
  credentialed external call"* — three categories, of which only the first two name a concrete
  token. There is no machine-readable "actions" field on a plan; acceptance steps are prose. What
  would settle it: a structured acceptance field, which does not exist and which this plan does not
  invent. ⇒ P4 is implemented as a **token scan over §7's prose with a pinned deny-list**, and its
  report explicitly states that it is a *lexical* check that cannot see intent — a limitation named
  in the output rather than hidden by it (§7 Item 16, §11 row 2).
- **Q7 — enrollment, imports, lint?** As `bp-136` §3 Q5/Q6: `pyproject.toml:128` enrolls `scripts/`
  by directory at a **Tier-2 0-error hard floor** (`.github/workflows/ci.yml:71`);
  `scripts/check_imports.py:2-11` constrains `core/` and the worker boundary only, so the
  stdlib-only discipline exists **only** if this plan writes its own AST test (Item 17 does);
  ruff `line-length = 100`, no per-file ignore for `scripts/`; the `sys.path` bootstrap needs
  `# noqa: E402` and `# type: ignore[import-not-found]` (`scripts/board.py:35`).

**Additional risks or questions surfaced during reading:**

⚑ **Tightening P3 will fail most existing plans, and that is correct.** P1–P5 gates *autopilot
eligibility*, not repo hygiene. A large majority of the 111 plans will not pass — because they
were never written to. The obvious "fix" (normalizing 111 historical plans to a strict flag) is a
100-file sweep nobody asked for and is a **non-goal** (§9). The builder must resist it and record
the census honestly instead.

⚑ **The predicate's output is rendered to the owner's phone.** §2.4: *"their results are printed in
the capsule the owner reads."* A vacuous PASS is therefore not merely an un-enforced check — it is
a **false statement shown to the owner at the moment he decides whether to grant**. This is why
every item below carries a degenerate-input criterion rather than only a falsifier.

## 4. Reconciliation

- `dn-autopilot-and-delegated-blessing.md:321` — P3's check, quoted: *"every plan item carries
  `touches_stored_data: false`"*, grounded on *"flag exists per-item [GROUNDED
  agent-workflow.md:80]"* → **[banner: correction]**, warrant `finding-0263`. The note is
  **ratified and agent-immutable (A8)**, so the correction cannot be written back into it. This
  plan carries the banner instead: `scripts/autopilot_eligibility.py`'s module docstring states, in
  full, that §2.4's P3 names a field that does not exist; that the implemented check is a pinned
  regex over the §7 item body requiring the value to normalize to exactly `no`; and that **§6 here
  is the authoritative form until a superseding note says otherwise**. Any divergence between §6 and
  a future note is a `spec-defect`, not a silent re-interpretation. The same statement is repeated
  in the predicate's own **report output**, so the owner reading the capsule sees the caveat, not
  only a builder reading the source.

- `dn-autopilot-and-delegated-blessing.md:322` — P4's check → **[banner: correction]**, minor. The
  note implies a checkable "acceptance step or action"; no such structured field exists (§3 Q6).
  The docstring and the report state that P4 is a **lexical scan with a pinned deny-list** and name
  what it cannot see (an external call reached through a helper, a `deploy` spelled differently).
  Announced, not elided.

- `docs/templates/build-plan.md:111` — the prose flag → **[cross-ref: extension]**, deliberately
  **not** edited. Making `touches_stored_data` a real per-item front-matter key changes the
  build-plan template and therefore `dn-agent-workflow`'s front-matter schema — an owner-ratified
  amendment, not a builder's edit (`finding-0263` §Re-entry). The template is out of `write_scope`
  and stays as it is; the cross-reference lives in this plan and in the finding.

## 5. Write scope

Two paths, both **new**:

- `scripts/autopilot_eligibility.py` — the predicate. stdlib + `_lib` reuse only; no `os`, no
  `subprocess`, no `core`, no `config`.
- `tests/unit/test_autopilot_eligibility.py` — the falsifiers, the degenerate inputs, the AST
  invariant, and the read-only census against the real tree.

**Deliberately OUT of scope** — a denial means file a finding, never widen by hand:

- `docs/templates/build-plan.md` and every `docs/build-plans/*/plan.md` — no template change, and
  **no normalization sweep of the 111 historical plans** (§9, and the §3 risk above).
- `.claude/hooks/**` — `_lib` is **imported**, never edited. If P1's glob semantics appear to need
  a change in `_lib.glob_match`, that is a change to the guard itself: file a finding and stop.
- `scripts/board.py`, `scripts/autopilot_halt.py` — owned by `bp-135`/`bp-136` this wave; disjoint
  scope is what makes the three parallelizable.
- `docs/design-notes/**` (A8, agent-immutable) and the foundation denylist (`CONSTITUTION.md`,
  `eval/golden/**`, `eval/golden.py`), which binds regardless of write_scope.

**Acceptance-reachability check** (findings 0177/0191/0204):

| item | files its acceptance must modify | all in §5? |
|---|---|---|
| 14 | `scripts/autopilot_eligibility.py`; `tests/unit/test_autopilot_eligibility.py` | ✓ |
| 15 | same two | ✓ |
| 16 | same two | ✓ |
| 17 | same two | ✓ |

Non-obvious targets checked: **no protocol member** on an out-of-scope class; **no
allowlist/registry enrollment** — `pyproject.toml:128` covers `scripts/` by directory (§3 Q7);
**no test outside this plan's own test file** asks the changed surface a question, because every
surface is new and `_lib` is imported unchanged. ⚑ Items 14–17 read `docs/build-plans/*/plan.md`
and `.claude/hooks/_lib.py` — **reading is not writing**, and `scope-guard` gates writes only, so
no scope entry is needed for a read. Item 17's census is explicitly read-only.

## 6. Interfaces pinned inline

**§2.4's predicate table, verbatim** (`dn-autopilot-and-delegated-blessing.md:316-324`) — the
builder implements these five and not five paraphrases:

| predicate | check | grounding |
|---|---|---|
| P1 — repo-confined | every `write_scope` glob resolves inside the worktree | write_scope is the capability |
| P2 — record/enforcement-free | scope ∩ {`CLAUDE.md`, `.claude/hooks/**`, `.claude/settings.json`, `docs/design-notes/**`, `eval/**`} = ∅ | non-goal 3; NN-9 beneath it |
| P3 — no stored-data blast | every plan item carries `touches_stored_data: false` | flag exists per-item |
| P4 — no live-state mutation | no acceptance step or action runs `deploy`, `palace` lifecycle mutation, or any credentialed external call | standing owner rules; NN-4 |
| P5 — bounded | `session_budget` finite and un-self-extendable; cost ceiling stated in the capsule | §2.6 H4 |

**And the sentence that makes them a gate** (`:325-327`, verbatim): *"P1–P5 are conjunctive,
hook-checkable (glob math and grep, the same machinery scope-guard already runs), and evaluated by
the verifier **before** it will accept any code — their results are printed in the capsule the
owner reads."*

**The three-valued result — DEFINED HERE**, because "conjunctive" over a two-valued domain is
where the vacuous pass lives:

```python
class Result(enum.Enum):
    PASS = "pass"
    FAIL = "fail"
    UNDETERMINED = "undetermined"   # the input did not answer the question
```

**The conjunction rule, pinned:** overall eligibility is `PASS` **iff all five are `PASS`**. Any
`UNDETERMINED` makes the whole `FAIL`, never `PASS` and never `UNDETERMINED` — invariant 7
(*"Ambiguity … always resolves toward halting"*) applied at the gate's mouth. ⚑ There is **no**
code path that returns overall `PASS` while any term is not `PASS`; a test asserts this by
enumerating all 3^5 = 243 term combinations.

**P3's form — DEFINED HERE (the `finding-0263` correction, §4).** For each `### Item ` heading in
the plan's §7, the item body must contain exactly one line matching:

```
^\s*[-*]\s*\*\*Touches stored data\?\*\*\s*(?P<value>.*)$
```

and `value`, lowercased and stripped of surrounding `*` and trailing `.`, must be **exactly `no`**.
Every other value — `reads only`, `no (reads the corpus)`, `no. **parallelizable?** yes` truncated
at the first sentence, `yes`, an absent line, or two matching lines — is **not `no`**:
`no (…)` and `reads only` are `FAIL`; an absent or duplicated line is `UNDETERMINED`. A plan with
**zero** `### Item ` headings is `UNDETERMINED`, never `PASS`.
⚑ Because the flag line commonly runs on into `**Parallelizable?**` (57 of 111 plans), `value` is
first truncated at the literal `**Parallelizable?**` or `**Depends on:**` if present, and the
remainder is what must equal `no`.

**P5's form — DEFINED HERE.** `session_budget` must parse as an integer `>= 1`; `"null"`, empty, or
absent is `UNDETERMINED` (§3 Q4). "Un-self-extendable" is a property of the *runtime*, not of the
plan text, and is **not** checkable here — the report says so explicitly rather than implying it
was checked. The capsule's cost ceiling is `bp-139`'s render; P5 checks the plan's half.

**CLI surface — DEFINED HERE:**

```
uv run scripts/autopilot_eligibility.py check <plan-file>
    -> exit 0 iff all five predicates PASS
    -> exit 1 otherwise, one diagnostic line per non-PASS term, naming the predicate,
       the result (fail|undetermined) and the evidence (the glob, the item, the token)
uv run scripts/autopilot_eligibility.py report <plan-file>
    -> prints the capsule-ready `achievable:` block on stdout, exit code as for `check`
```

**The `achievable` block the capsule embeds** — the capsule's field is spelled `achievable`
(`scripts/capsule.py:68-77`, `REQUIRED_FIELDS`), and its template line reads
`achievable: <write-surface summary + P1-P5 predicate results + no open decisions>`
(`docs/templates/intent-capsule.md:11`). `report` emits a single line of the form:

```
achievable: <n> globs; P1 pass P2 pass P3 pass P4 pass(lexical) P5 pass; <caveats or "no caveats">
```

⚑ It must fit the capsule's caps (`LINE_CAP = 40`, `WORD_CAP = 300` at `scripts/capsule.py:62-63`)
alongside seven other fields — so `report` emits **one line**, and a test asserts that a plan with
twenty globs still produces one line under 200 characters. ⚑ **The caps bound shape, not bytes**
(`finding-0219` / `oq-0054`, still `open` with no recorded ruling): this plan must **not** assume a
character bound exists, and must not add one — it simply keeps its own output short.

**Reuse, verbatim** (`scripts/board.py:33-38`):

```python
sys.path.insert(0, str(ROOT / ".claude" / "hooks"))
from _lib import matches_any, parse_front_matter  # type: ignore[import-not-found]  # noqa: E402
```

## 7. Items

Ordered by blast radius: pure glob math → prose parsing → lexical scan → the conjunction and its
report. All read-only; nothing writes outside this plan's two files. Item numbering continues the
family (`bp-120` 1–4, `bp-135` 5–8, `bp-136` 9–13).

### Item 14 — P1 and P2: the scope predicates, on the guard's own matcher

- **Objective:** a plan's declared capability is checked to be repo-confined and free of the record
  and enforcement surfaces, using the same glob semantics `scope-guard` uses.
- **Files:** `scripts/autopilot_eligibility.py`, `tests/unit/test_autopilot_eligibility.py`
- **Acceptance test:** `uv run pytest tests/unit/test_autopilot_eligibility.py -q` green on:
  P1 `FAIL` for an absolute path, for a `../` escape, and for an entry whose normalized form leaves
  the repo root; P1 `PASS` for ordinary relative globs including `**`; P2 `FAIL` for each of the
  five §2.4 members individually (`CLAUDE.md`, `.claude/hooks/**`, `.claude/settings.json`,
  `docs/design-notes/**`, `eval/**`), including via a glob that *covers* one without naming it
  (`.claude/**`, `docs/**`, `**`); P2 `PASS` for a disjoint scope. Plus a test asserting the
  matcher used is `_lib.matches_any` (AST or identity), not a local re-implementation.
- **Falsifier:** a scope this predicate calls P2-clean that `scope-guard` would nonetheless allow
  into an enforcement surface, or vice versa — the two matchers disagree, and the predicate is
  measuring its own glob code rather than the guard's capability. ⚑ Drill it: take five real
  `write_scope` lists from `docs/build-plans/`, run both `_lib.matches_any` and this predicate over
  a fixed probe set of paths, and assert identical verdicts.
- **⚑ Degenerate input (false-success rule):** **`write_scope: []` — an empty list.** "Every glob
  resolves inside the worktree" is **vacuously true** over the empty set, and "scope ∩ forbidden =
  ∅" is **vacuously true** too, so a naive P1∧P2 returns `PASS` for a plan that declares no
  capability at all. Assert both return `UNDETERMINED` (not `PASS`) for an empty or absent
  `write_scope`. Second degenerate: **an entry with a glued inline comment**
  (`- eval/metrics.py  # absorbed`, the finding-0085 footgun) — it matches nothing, so P2's
  intersection is empty and P2 passes on a scope that names `eval/`. Assert P2 `FAIL`s on a glued
  entry, and that the diagnostic names finding-0085.
- **⚑ Mutation obligation** (`the-false-success-rule.md:52-65`, `finding-0249`): P2 is the leg that
  keeps autopilot out of its own cage. Mutate (m1) the forbidden set to omit `.claude/hooks/**`;
  (m2) the intersection to compare literal strings instead of glob-matching; (m3) the empty-scope
  case to return `PASS`. Each must be caught by a named test; record the campaign in the journal.
- **Invariant(s) it must not violate:** invariant 5 — the foundation denylist binds beneath every
  grant; this predicate never asserts a denylist path is reachable. It imports `_lib`; it never
  edits it. stdlib only otherwise.
- **Touches stored data?** No.
- **Parallelizable?** yes  **Depends on:** none

### Item 15 — P3: the stored-data flag, read against a pinned regex (carries finding-0263)

- **Objective:** the blast-radius flag becomes a decision rather than the first two characters of
  an English sentence.
- **Files:** `scripts/autopilot_eligibility.py`, `tests/unit/test_autopilot_eligibility.py`
- **Acceptance test:** green on fixtures covering the measured spelling census
  (`finding-0263`): `PASS` only for `no`, `No`, `No.`, `**No.**` and the run-on form truncated at
  `**Parallelizable?**`; `FAIL` for `yes`, `Yes — …`, `Reads only.`, `No (reads the corpus)`,
  `No — reads the vault`; `UNDETERMINED` for an item with no flag line, for two flag lines in one
  item, and for a plan with zero `### Item ` headings. Plus: the module docstring carries the §4
  correction banner verbatim, asserted by a test.
- **Falsifier:** the pinned regex rejects a *correctly-written* new plan because of a formatting
  detail the template permits — then the check is enforcing a spelling, not a property, and it will
  train authors to game it. ⚑ Drill it: run P3 over all 111 existing plans (read-only) and inspect
  every `UNDETERMINED`. An `UNDETERMINED` caused by a template-legal shape the regex missed is the
  falsifier firing; an `UNDETERMINED` caused by an author hedging is the check working.
- **⚑ Degenerate input (false-success rule):** **a plan with zero items.** "Every item carries the
  flag as `no`" is **vacuously true** over the empty set, so a naive P3 returns `PASS` for a plan
  with no §7 at all. Assert `UNDETERMINED`. Second degenerate: **the literal §2.4 reading** —
  a check that greps for `touches_stored_data:` finds nothing, sees no `true`, and returns `PASS`
  **on every plan in the repository**. Assert a test exists that would redden if the implementation
  regressed to the front-matter key: it constructs a plan whose §7 says `**Touches stored data?**
  Yes — rewrites the vector store` and asserts `FAIL`.
- **⚑ Mutation obligation:** P3 is the term that guards the corpus. Mutate (m1)
  `value.startswith("no")` in place of exact equality — must be caught by the
  `No (reads the corpus)` fixture; (m2) the zero-item case to `PASS`; (m3) drop the truncation at
  `**Parallelizable?**` — must be caught by the run-on fixture. Record the campaign.
- **Invariant(s) it must not violate:** it edits **no** existing plan and **no** template (§9). It
  is read-only over `docs/build-plans/`.
- **Touches stored data?** No.
- **Parallelizable?** yes  **Depends on:** none

### Item 16 — P4 and P5: the lexical scan that admits what it cannot see, and the bound

- **Objective:** live-state mutation and unboundedness are screened, and the screen's blind spot is
  stated in its own output.
- **Files:** `scripts/autopilot_eligibility.py`, `tests/unit/test_autopilot_eligibility.py`
- **Acceptance test:** green on: P4 `FAIL` when §7's prose contains any deny-list token —
  `deploy`, `mind-palace deploy`, `palace start|stop|restart|up|down`, `security find-generic-password`,
  `get_secret`, `boto3`, `aws `, `curl`, `subprocess` — case-insensitively, **including inside
  fenced code blocks** (a command in a fence is still a command); P4 `PASS` for a plan whose §7
  contains none; P4 `UNDETERMINED` when §7 is absent or empty. P5 `PASS` for `session_budget: 1`;
  `FAIL` for `0`, a negative, or a non-integer; `UNDETERMINED` for absent, empty or the literal
  string `"null"` (§3 Q4).
- **Falsifier:** P4 fires on a plan that merely *mentions* `deploy` in prose — e.g. a non-goal
  saying "this plan never runs `deploy`" — and so the safest-written plans fail hardest. ⚑ That is
  a real and expected effect: the correct response is **not** to add prose-context heuristics (a
  lexical check that tries to understand English is worse than one that admits it cannot) but to
  record it, and to state in the report that P4 is conservative by construction. If the false-fire
  rate makes autopilot unusable on real QoL plans, that is a `spec-defect` against §2.4's P4 and is
  filed, not tuned away.
- **⚑ Degenerate input (false-success rule):** **a plan whose §7 is empty or whose items carry no
  acceptance prose.** "No acceptance step runs `deploy`" is vacuously true, so P4 returns `PASS`
  for a plan with nothing to scan. Assert `UNDETERMINED`. Second degenerate: **the token inside a
  fenced block** — a scanner that skips fences (the natural "ignore code" instinct) passes a plan
  whose acceptance is literally ```` ```mind-palace deploy``` ````. Assert `FAIL`, and assert a
  named test would redden if fence-skipping were introduced.
- **Invariant(s) it must not violate:** non-goal 4 of the note — `deploy` stays owner-in-loop by
  standing rule, *out of reach regardless of grant*. P4 screens; it never authorizes. The report
  states that P5 checks the plan's bound only and **cannot** verify un-self-extendability at
  runtime (§6).
- **Touches stored data?** No.
- **Parallelizable?** yes  **Depends on:** none

### Item 17 — the conjunction, the report, and the census

- **Objective:** the five terms compose into one gate that cannot return `PASS` while any term is
  not `PASS`, and whose output is the line the owner reads on his phone.
- **Files:** `scripts/autopilot_eligibility.py`, `tests/unit/test_autopilot_eligibility.py`
- **Acceptance test:** green on: **all 3^5 = 243 term combinations** enumerated, asserting overall
  `PASS` for exactly one of them and `FAIL` for the other 242 — in particular that no combination
  containing an `UNDETERMINED` yields `PASS`; `check` exits 0 iff overall `PASS`; `report` emits
  **one** line, under 200 characters, for a plan with twenty globs; the report line names every
  non-`PASS` term and carries the §4 caveats (P3's corrected form, P4's lexical limitation, P5's
  un-checkable half); the AST invariant test (stdlib + `_lib` only; **no** `os`, `subprocess`,
  `core`, `config`, `keyring`, `hmac`), modelled on `tests/unit/test_capsule.py:414-431` and using
  `ast.walk`. Plus the **census**: a read-only test that runs the predicate over every
  `docs/build-plans/*/plan.md` and asserts only that it terminates and returns a `Result` for each
  — printing the tally, never asserting a pass rate.
- **Falsifier:** the census shows **every** real plan `UNDETERMINED` on the same term. Then the
  predicate is measuring an authoring convention nobody follows rather than a property, and P1–P5
  cannot gate anything real until the convention changes — a `spec-defect` against §2.4 routed to
  the orchestrator, not a threshold to relax.
- **⚑ Degenerate input (false-success rule):** **a conjunction implemented as `all(t is not FAIL)`**
  — the single most natural way to write it, and it returns `PASS` when every term is
  `UNDETERMINED`, i.e. when *nothing was determined about anything*. The 243-combination
  enumeration is precisely the assertion that this is impossible. Second degenerate: a `report`
  that prints `P1 pass P2 pass …` from a template rather than from the computed terms — assert the
  report line for a known-`FAIL` plan differs from the line for a known-`PASS` one in the expected
  positions.
- **⚑ Mutation obligation:** mutate the conjunction to `all(t is not Result.FAIL)` and assert the
  243-combination test reddens. This is the load-bearing line of the whole plan.
- **Invariant(s) it must not violate:** invariant 7 (ambiguity resolves toward halting) and §2.4's
  necessary-vs-sufficient split — **this tool never grants anything.** A `PASS` is a *necessary*
  condition; the sufficient condition is the owner issuing a code, and no code path here even
  represents one. The census is **read-only**; it writes no plan.
- **Touches stored data?** No.
- **Parallelizable?** no  **Depends on:** Items 14, 15, 16

## 8. Math carried explicitly

- **The eligibility conjunction as a three-valued predicate.** *measures:* whether a plan's own
  declared fields are sufficient to establish that the run's complete rollback is a git operation —
  §2.8's reversibility guarantee, computed rather than asserted. *valid when:* the five terms are
  genuinely independent (no term's evidence is another's), the plan's declared fields are the ones
  actually enforced at runtime (P1/P2 hold only because `scope-guard` reads the same `write_scope`
  with the same matcher — §3 Q3), and `UNDETERMINED` is absorbing under conjunction. *fails its
  keep if:* the 243-combination enumeration ever admits a `PASS` containing a non-`PASS` term (the
  absorption is broken and the gate is two-valued in disguise), or if the census shows the
  predicate returns the same value for every real plan — a constant function measures nothing and
  earns no place.

## 9. Non-goals

1. **No normalization sweep of the 111 existing plans.** P1–P5 gates autopilot eligibility, not
   repo hygiene. Most existing plans will not pass; that is correct (§3, `finding-0263`).
2. **No template change.** Making `touches_stored_data` a real per-item front-matter key amends
   `dn-agent-workflow`'s front-matter schema and is the owner's, not a builder's (§4).
3. **No edit to `.claude/hooks/_lib.py`.** It is imported, never changed. If P1 seems to need
   different glob semantics, that is a change to the guard — file a finding and stop.
4. **No grant, no secret, no MFA code, no status flip.** This tool computes a *necessary*
   condition and holds no authority. `bp-138` owns the cryptography.
5. **No stakes taxonomy.** Non-goal 8 of the note; blocked on `finding-0193` and structurally
   unnecessary in v1.
6. **No character cap on the capsule** — `oq-0054` is `open` with **no recorded ruling**
   (`docs/inbox/owner-questions.md:1922-1933`). This plan keeps its own output short and assumes no
   byte bound exists (§6).
7. **No prose-context heuristics in P4.** [INFERENCE — that a conservative lexical screen whose
   blind spot is *stated* is safer than a clever one whose blind spot is *hidden*. If the
   false-fire rate proves disqualifying, that is a design question for the owner, not a heuristic
   for a builder.]

## 10. Stop-and-raise conditions

STOP and surface rather than proceed if:

- the census (Item 17) shows every real plan `UNDETERMINED` on one term, or P3's `UNDETERMINED`
  set is dominated by template-legal shapes the regex missed (Item 15's falsifier) — file a
  `spec-defect` against §2.4, park the criterion, continue the rest.
- P1 and `_lib.matches_any` disagree on any probe path (Item 14's falsifier) — that is a change to
  the guard's semantics, which is **not** this plan's to make. File a finding and stop.
- any acceptance appears to need a file outside §5 — finding, park, continue. **Never widen the
  scope by hand and never route around a `scope-guard` denial**; a second denial on the same target
  means the plan is mis-scoped.
- a `HOOK-FAILURE` line appears — rerun the named hook standalone, reconcile, say so in the journal
  before continuing.
- **any item would give this code a secret, an MFA code, or the power to flip a status.** It needs
  none of the three; §2.4 is explicit that *"The agent's role in eligibility is exactly nothing."*
  If one appears necessary, that is not a design choice — stop and raise it.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| Whether `touches_stored_data` should become a real per-item front-matter key | No — read the prose with a pinned regex, and refuse every hedge (§6) | *Add the front-matter key and sweep 111 plans* — rejected: amends `dn-agent-workflow`'s schema (owner's act, A8) and is a 100-file sweep nobody asked for. *Accept the note's literal reading* — rejected: it passes on every plan in the repo (`finding-0263`) | The owner rules on `finding-0263`'s design half, batched alongside the `oq-0047` ftype question |
| How P4 detects a credentialed external call | Conservative lexical deny-list over §7 prose, fences included, with the blind spot stated in the report | *Parse acceptance into a structured field* — rejected: no such field exists and inventing one is a template change (row 1). *Skip fenced blocks* — rejected: a command in a fence is still a command, and it is the obvious place an acceptance step lives | The false-fire rate is measured on real QoL plans and proves disqualifying |
| Whether the report should be one line or a block | One line, < 200 chars, because seven other capsule fields share a 40-line/300-word budget (`scripts/capsule.py:62-63`) | *A multi-line block per predicate* — rejected: it would crowd out the fields the owner actually reads, defeating §2.2's cap rationale | `oq-0054` is ruled and the capsule's budget is restated |
| Whether P5 should verify un-self-extendability | No — it checks the plan's declared bound and says in the report that the runtime half is unchecked | *Assert it* — rejected: unverifiable from a text, and an unverifiable assertion printed to the owner's phone is exactly the false statement §2.4's "printed in the capsule" makes dangerous | A runtime budget enforcer exists (H4's other half) and can be queried |

## 12. Dependency & ordering summary

**Within the plan:** Items 14, 15 and 16 are mutually independent and may be built in any order —
each is one predicate group with its own fixtures. Item 17 depends on all three (it composes them).
Blast-radius order is the item order: pure glob math (no file reads beyond the plan under test) →
prose parsing → lexical scan → the conjunction plus a read-only census over the real tree. Nothing
is irreversible; every effect is a new file under `git`, which is this plan's own §2.8 property
holding trivially.

**Across the wave:** see `bp-135` §12 for the full map, the three un-minted stages (**AP-actor**
parked on `oq-0037` + `finding-0262`; **AP-posthoc** parked on `oq-0036`; **AP-const** parked on
the owner's A10 amendment) and the blessing-round recommendation. This plan is
`parallelizable_with: [bp-135, bp-136]` — three disjoint write scopes, no shared file. ⚑ It has
**no `depends_on`** and must not acquire one: like `bp-136`, its independence from `bp-138` is what
lets the reviewer's seat be filled before the grant's cryptography exists.
