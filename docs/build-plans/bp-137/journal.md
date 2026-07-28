# bp-137 — journal

## Pre-build notes for whoever picks this up

- ⚑ **The warrant is real and measured.** `finding-0263`: `touches_stored_data: false` appears in
  **zero** of the 111 plans carrying the flag; the prose form has ≥20 spellings. A P3 built to
  §2.4's literal text returns PASS on **every plan in the repository**. Read the finding before the
  plan.

- ⚑ **Most existing plans will fail P3 as tightened, and that is correct.** P1–P5 gates autopilot
  eligibility, not repo hygiene. The tempting "fix" is a 111-file normalization sweep. It is a
  non-goal (§9) and it would be a template/schema change that belongs to the owner.

- ⚑ **Every predicate has a vacuous-pass twin.** Empty `write_scope` ⇒ P1 and P2 both true over the
  empty set. Zero `### Item ` headings ⇒ P3 true over the empty set. Empty §7 ⇒ P4 true. That is why
  the result type is three-valued and why `UNDETERMINED` is absorbing under conjunction. The
  243-combination enumeration in Item 17 is the assertion that a naive `all(t is not FAIL)` cannot
  survive — write it early, not last.

- **Reuse `_lib.matches_any`, do not write glob code.** Two matchers that disagree mean the
  predicate blesses a scope `scope-guard` reads differently — a security-relevant duplication, not
  a style one.

- **The finding-0085 footgun is a P2 degenerate input, not a footnote.** An entry with a glued
  inline comment (`- eval/metrics.py  # absorbed`) matches nothing, so the forbidden-set
  intersection is empty and P2 passes on a scope that names `eval/`.

- **This predicate's output is rendered to the owner's phone.** A vacuous PASS is a false statement
  shown to him at the moment he decides whether to grant. Weight the degenerate-input criteria
  accordingly.

---

## 2026-07-27 — session start (delegated builder, worktree `worktree-agent-a25e8e55678c3749c`)

**Base:** `69a065c` (origin/main at spawn). Hooks are disabled repo-wide by owner ruling, so
write-scope discipline is held by hand and by the reviewer's pre-merge diff read. Write scope:
`scripts/autopilot_eligibility.py`, `tests/unit/test_autopilot_eligibility.py` (+ this journal,
+ new files under `docs/findings/`).

**Read:** plan §0–§12 whole; `dn-autopilot-and-delegated-blessing` §1.2 non-goals 4/8 and the
`:102-104` out-of-scope clause, §2.4 whole, §2.8 whole, §2.9 invariants 5 and 7;
`finding-0263` whole; `.claude/hooks/_lib.py:126-233` (`_seg_match` / `glob_match` /
`matches_any` / `parse_front_matter` / `_scalar`), `:354-361` (`plan_write_scope`), `:455-475`
(`cmd_scope_check`'s widened allow-set); `scripts/board.py:25-70` (the `sys.path` idiom and
`_is_absent`); `scripts/capsule.py:1-90`; `tests/unit/test_capsule.py:405-431` (the AST
precedent); `docs/templates/build-plan.md:1-20,100-120`; `docs/templates/intent-capsule.md`;
`the-false-success-rule.md:15-70`; `pyproject.toml:103-135`.

**Grounding confirmed before writing code:**

- 137 plan directories; **118** carry a `**Touches stored data?**` line (the finding measured
  111 — this wave's own new plans account for the delta). `touches_stored_data: false` still
  appears **zero** times.
- `## 7. Items` is the §7 heading form in **132** plans — one stable spelling, so a
  `^##\s*7[.)]?\s` section locator is safe.
- `_lib.parse_front_matter` yields `[]` for `write_scope: []` (the flow-list branch) and `""`
  for a key with no entries. Both must read as **absent** — UNDETERMINED, never PASS.

**Design decisions taken before the first line of code (recorded so they are reviewable):**

1. **The conjunction takes a keyed mapping, not a sequence.** `conjoin(dict[str, Result])`
   returns PASS iff the key set is exactly `{P1..P5}` **and** all five are PASS. A sequence
   would let `all(...)` be vacuously true over the empty list — Item 17's degenerate in its
   purest form. Making the complete term set a *precondition* kills it structurally rather
   than by a guard clause bolted on afterwards.
2. **P2 is checked in both glob directions**, both through `_lib.matches_any`:
   (a) `matches_any(scope_entry, FORBIDDEN)` catches a concrete entry inside a forbidden tree
   (`eval/foo.py`); (b) `matches_any(forbidden_witness, [scope_entry])` catches a scope glob
   that *covers* a forbidden surface without naming it (`.claude/**`, `docs/**`, `**`).
   Neither direction alone suffices — checked by hand against `glob_match`: the path
   `.claude/**` is **not** matched by the pattern `.claude/hooks/**`, so only (b) sees it;
   and the path `eval/foo.py` is matched by no witness, so only (a) sees it.
3. **The correction banner is sliced out of `__doc__`**, not duplicated into a constant, so
   the docstring and the report output cannot drift (owner DRY rule). Extraction raises
   loudly if the markers are missing rather than yielding an empty caveat — a silently
   caveat-free report is exactly the false statement §2.4 warns about.
4. **P5 tolerates a trailing YAML `#` comment** on `session_budget` (`_lib._scalar` leaves it
   glued on unquoted scalars, by deliberate design at `:218-233`). Rejecting legal YAML would
   be enforcing a spelling rather than a property — Item 15's falsifier shape. The integer
   itself is still exact.

## 2026-07-27 — Items 14–17 complete; 109 tests green; mutation campaign 12/12 killed

**Delivered** (both files new, both inside `write_scope`; nothing else in the tree was
touched — `git status` shows exactly `scripts/autopilot_eligibility.py`,
`tests/unit/test_autopilot_eligibility.py`, `docs/findings/finding-0274.md`, and this
journal):

- `scripts/autopilot_eligibility.py` — `Result` (3-valued), `Term`, `Evaluation`,
  `check_p1..check_p5`, `conjoin`, `report_line`, `diagnostics`, and the `check` / `report`
  CLI. Stdlib + `_lib` only; imports `{__future__, argparse, enum, re, sys, dataclasses,
  pathlib, _lib}` and nothing else.
- `tests/unit/test_autopilot_eligibility.py` — 109 tests.

**Acceptance actually run, per item:**

| item | acceptance | result |
|---|---|---|
| 14 | P1 FAIL on absolute / `../` / normalized-escape; PASS on ordinary + `**`; P2 FAIL on each of the five §2.4 members and on covering globs `.claude/**`, `docs/**`, `**`, `.claude/hooks/*.py`; PASS disjoint; matcher-identity + AST tests | green |
| 15 | PASS only for `no`/`No`/`No.`/`**No.**`/run-on; FAIL for `yes`, `Yes — …`, `Reads only.`, `No (reads the corpus)`, `No — reads the vault`, `Not directly.`; UNDETERMINED for absent / duplicated / zero-item; docstring banner asserted | green |
| 16 | P4 FAIL on all eight deny-list tokens incl. inside a fence; PASS clean; UNDETERMINED on absent/empty §7. P5 PASS `1`; FAIL `0`, `-1`, `1.5`, `one`, `1 2`; UNDETERMINED absent/`""`/`null`/`none`/`~` | green |
| 17 | all 3⁵ = **243** combinations enumerated — exactly **one** overall PASS, and **no** combination containing an `UNDETERMINED` passes; `check` exit 0 iff PASS; `report` one line, 145 chars for 20 globs (<200); AST invariant; read-only census | green |

`uv run pytest tests/unit/test_autopilot_eligibility.py -q` → **109 passed in 0.33s**.

**⚑ The predicate reddens on ABSENCE, not only on violation — the proof, by named test:**

| absence | vacuously-true reading | named test | verdict |
|---|---|---|---|
| `write_scope` empty/absent | "every glob is inside the worktree" | `test_p1_degenerate_empty_scope_is_undetermined_not_pass` | UNDETERMINED |
| `write_scope` empty/absent | "scope ∩ forbidden = ∅" | `test_p2_degenerate_empty_scope_is_undetermined_not_pass` | UNDETERMINED |
| glued `#` entry (finding-0085) | intersection empty on a scope naming `eval/` | `test_p2_degenerate_glued_inline_comment_fails_and_names_finding_0085` | FAIL |
| zero `### Item ` headings | "every item carries the flag as no" | `test_p3_degenerate_zero_items_is_undetermined_not_pass` | UNDETERMINED |
| absent / duplicated flag line | — | `test_p3_undetermined_for_{an_item_with_no_flag_line,two_flag_lines_in_one_item}` | UNDETERMINED |
| §7 absent or item-less | "no acceptance step runs `deploy`" | `test_p4_degenerate_absent_or_empty_section_7_is_undetermined_not_pass` | UNDETERMINED |
| `session_budget` absent/`null` | — | `test_p5_degenerate_absent_empty_or_null_is_undetermined_not_pass` | UNDETERMINED |
| **the term set itself incomplete** | `all(...)` over an empty sequence | `test_conjunction_refuses_an_incomplete_or_wrong_term_set` | FAIL |
| all five UNDETERMINED | `all(t is not FAIL)` | `test_conjunction_over_all_243_term_combinations` | FAIL |

The last two are the structural half: `conjoin` takes a **keyed mapping and requires the
complete `{P1..P5}` key set**, so a caller that computed nothing receives FAIL rather than a
vacuous PASS. `test_the_naive_conjunction_would_admit_thirty_two_combinations` pins the
arithmetic — the naive form admits 2⁵ = 32 combinations, `conjoin` admits exactly 1.

**Mutation campaign — 12 mutants, 12 KILLED, 0 survivors** (harness: patch in place, run the
suite, restore; the restored file was `diff`-verified identical to the pre-campaign copy).

| mutant | killed by |
|---|---|
| 14-m1 forbidden set omits `.claude/hooks/**` | `test_the_forbidden_set_is_the_verbatim_2_4_membership` |
| 14-m2 intersection compares literal strings, not globs | `…concrete_path_inside_a_forbidden_tree[eval/some/deep/new_file.py]` |
| 14-m2b covering direction dropped | `…covers_a_forbidden_surface_without_naming_it[**, .claude/**, docs/**]` (3) |
| 14-m3 / m3b empty scope → PASS (P1, then P2) | `…p1_degenerate_empty_scope…`, `test_diagnostics_name_every_non_pass_term_in_order`, `test_check_exits_zero_iff_overall_pass` |
| 15-m1 `startswith("no")` for exact equality | `…hedged_spelling_from_the_census[No (reads the corpus), No —…, No, but…, Not directly.]` (4) |
| 15-m2 zero-item case → PASS | `test_p3_degenerate_zero_items_is_undetermined_not_pass` |
| 15-m3 drop truncation at `**Parallelizable?**` | `…truncation_at_a_run_on_bolded_field_is_load_bearing` + 3 census fixtures |
| 16-m1 skip fenced blocks | `test_p4_degenerate_a_token_inside_a_fenced_block_still_fails` |
| 16-m2 empty §7 → PASS for P4 | `test_p4_degenerate_absent_or_empty_section_7…` |
| **17-m1 `all(t is not Result.FAIL)`** | `test_conjunction_over_all_243_term_combinations` + the 32-vs-1 arithmetic test |
| 17-m2 conjunction accepts an incomplete term set | `test_conjunction_refuses_an_incomplete_or_wrong_term_set` (all 5 params) |

**Census (Item 17, read-only over all 137 `docs/build-plans/*/plan.md`):**

```
overall: {'pass': 13, 'fail': 124, 'undetermined': 0}
  P1: {'pass': 137, 'fail':  0, 'undetermined':  0}
  P2: {'pass': 100, 'fail': 37, 'undetermined':  0}
  P3: {'pass':  32, 'fail': 80, 'undetermined': 25}
  P4: {'pass': 104, 'fail': 27, 'undetermined':  6}
  P5: {'pass': 137, 'fail':  0, 'undetermined':  0}
```

13 of 137 pass all five — **not** a constant function, so §8's *"fails its keep if the census
shows the predicate returns the same value for every real plan"* does not trip. No term is
constant-`UNDETERMINED`, so **Item 17's falsifier does not fire** and §10's first stop
condition is not met. `bp-120` — the real plan §2 item 4 named as the test target — passes all
five (`achievable: 3 globs; P1 pass P2 pass P3 pass P4 pass(lexical) P5 pass; …`).

**Falsifiers, considered explicitly:**

- **Item 14 — "the two matchers disagree."** *Did not fire.* Drilled as the plan specifies:
  five real `write_scope` lists × an 11-path probe set, `_lib.matches_any` vs the predicate's
  — identical verdicts on every pair (the predicate *is* `_lib.matches_any`, asserted by
  identity and by an AST test that no local glob function exists). Plus the semantic bridge:
  wherever the guard would let a real scope reach a forbidden witness, P2 must FAIL — it does.
- **Item 15 — "the regex rejects a correctly-written plan on a formatting detail."**
  *Fires partially; does NOT disqualify.* Inspected every one of the 25 `UNDETERMINED`.
  Nine plans fold the flag onto another field's bullet (`- **Invariant(s):** … **Touches
  stored data?** no.`), which the bullet-anchored §6 regex misses; 5 of the 25 are
  UNDETERMINED for that reason. §10's condition is *"dominated by"* — 5/25 = 20% is not
  domination, and the folded form is not template-legal (`build-plans.md:111` gives the flag
  its own bullet). The other 20: 5 plans predate §7 entirely, 1 uses bold-paragraph items and
  carries the flag zero times, 14 genuinely omit it. ⚑ **The miss is safe by construction** —
  a folded flag leaves its item with no bullet-anchored line, so the item is `UNDETERMINED`
  and the plan FAILs; it can never produce a false PASS, not even on a folded `Yes`. I did
  **not** widen the regex (§6 is the pinned authoritative form; §4 forbids silent
  re-interpretation). **Filed `finding-0274`**, routed to the orchestrator with three options.
- **Item 16 — "P4 fires on a plan that merely mentions `deploy`."** *Fires, as predicted, and
  is recorded rather than tuned away.* 27 of 137 plans FAIL P4. Most are true positives
  (plans that genuinely shell out or deploy). The clearest false fire is **`bp-137` itself**:
  its Item 16 enumerates the deny-list, so the plan that builds P4 fails P4 on all eight
  tokens. Not disqualifying for the QoL plans §2.4 targets (spell check, a keybinding), so no
  `spec-defect` is filed per Item 16's own condition; the limitation is stated in the tool's
  docstring **and in its report output**, which is where §2.4 requires it.
- **Item 17 — "every real plan UNDETERMINED on the same term."** *Did not fire* (census above).

**§3 Q3 obligation discharged:** the widened allow-set asymmetry (`cmd_scope_check` adds the
plan, its journal and `docs/findings/**`) is stated in the correction banner the `report`
subcommand emits, not only in a docstring a builder would read.

**Green gate, every leg run separately:**

| leg | result |
|---|---|
| `uv run ruff check .` | All checks passed! |
| `uv run mypy core agents eval ops scheduler scripts` | Success: no issues found in 263 source files |
| `uv run mypy` | **Found 69 errors** in 20 files (checked 564) — baseline **69**, asserted |
| `uv run python -m ops.type_gate` | exit 0; Tier-2 membership OK, bare-ignore scan OK |
| `uv run pytest -q` (CI form) | 4 failed, 2511 passed, 11 skipped, 21 deselected |

⚑ The 4 failures are **pre-existing and environmental, proved twice.** (1) With this plan's
three new files moved out of the tree, the identical set fails. (2) Three of them
(`test_worktree_enforcement::test_{a,c,d}`) pass under `env -u OUROBOROS_HOOKS_OFF` — they are
the direct consequence of the owner's hook escape hatch armed tonight (`1c907f5`;
`scope-guard.sh:7` short-circuits on it), so `scope-guard` returns ALLOW where the test expects
DENY. CI does not export the variable and is unaffected. The fourth,
`test_handoff_availability::test_the_generator_reads_the_worktree_s_own_seat_not_the_main_checkout`,
fails under both and is a worktree-nesting artifact of running inside a worktree; it is outside
this plan's `write_scope` and untouched by it. `test_core_imports_nothing_outside_core` is the
standing finding-0105 deselect the CI form already carries.

**Findings filed:** `finding-0274` (spec-defect → orchestrator, non-blocking) — P3's
bullet-anchored regex vs the folded-flag authoring form, with the 9-plan measurement, the
safety argument, and three options for the owner batched onto `finding-0263`.

**Not done, and why:** nothing from §7 is outstanding. Deliberately not done, per §9: no
template edit, no normalization sweep of the historical plans, no `_lib` edit, no
prose-context heuristics in P4, no character cap on the capsule, no grant/secret/status flip.
