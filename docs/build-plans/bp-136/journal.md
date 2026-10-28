# bp-136 — journal

## Pre-build notes for whoever picks this up

- ⚑ **The single most important degenerate input in this plan is `classify({})`.** The obvious
  implementation — walk H1…H8, return CONTINUE if none matched — returns **CONTINUE** on the empty
  object, which is invariant 7 exactly inverted. Write Item 9 first and let every later item compose
  on a function that is already total.

- ⚑ **`oq-0047` is ANSWERED** (`docs/inbox/owner-questions.md:1653`, *"YES — `ftype` BECOMES THE
  ROUTING AXIS"*) **and nothing implements it.** `grep -rn ftype .claude/hooks/ scripts/ core/`
  returns zero and `docs/templates/finding.md:9` still carries the old vocabulary. So H1 ships the
  conservative reading §2.4 licenses. Do **not** sweep the template — that is a separate plan.

- **H5 has no evidence source.** `scope-guard` prints `DENY:` and nothing persists it. The plan's
  answer is declaration-plus-refusal, not a new hook write. If you find yourself editing
  `.claude/hooks/`, stop: that is `oq-0036`'s territory and it is parked.

- ⚑ **Exit 1 means HALT — the safe outcome.** Document the inversion loudly in the module docstring.
  A caller that reads non-zero as "the tool broke" and proceeds has inverted the whole mechanism.

- **Item 12 enforces two of the note's non-goals by vocabulary alone**: there is no verdict code
  meaning "merge", "deskcheck" or "done". That is the cheapest possible enforcement. Do not add one
  for convenience.

- **The skill (Item 13) must link the graduate skill's session-sizing heuristic, never restate it.**
  A drifted copy routes design-scale work into autopilot, which is the one thing §2.2's router
  exists to prevent. Grep your own file for the heuristic's phrases before you finish.

## 2026-07-27 — session start, context read

Delegated builder, own worktree branched from `origin/main` at `69a065c`. Hooks are disabled
repo-wide by owner ruling tonight; the write_scope is honoured by discipline plus the
orchestrator's pre-merge diff review.

Read in the §2 order: the ratified note whole (§1.2, §2.2–§2.9, §4), `finding-0193`,
`scripts/capsule.py` whole, the AST-invariant precedent at `tests/unit/test_capsule.py:414-431`,
`scripts/board.py:1-60` (the `sys.path` + `_lib.parse_front_matter` idiom, copied verbatim),
`bp-135` §6 (the audit-record schema this plan READS), `the-false-success-rule.md`,
`docs/templates/finding.md`, and the front-matter shape of four existing skills.

**Confirmed before writing a line:**

- `scripts/autopilot_halt.py`, `tests/unit/test_autopilot_halt.py` and `.claude/skills/autopilot/`
  do not exist. All three files are new; nothing is edited.
- `docs/audits/` holds six documents and **none** is a bp-135-schema audit record —
  `grep -l 'gate:' docs/audits/*.md` returns nothing. So H2/H8's record reader is written against
  the pinned schema and exercised by fixtures only. Stated here so a later reader does not mistake
  fixture coverage for integration coverage against a landed `bp-135`.
- `_lib.parse_front_matter` (`.claude/hooks/_lib.py:182-215`) is a YAML-subset parser: flat scalars
  and simple lists, no nested mappings. bp-135 §6 pins the **flat** keys `verdict_artifact:` /
  `verdict_record:` for exactly that reason, and this plan reads the flat keys.
- Next free finding id is `finding-0271`.

Two interpretation questions are open going in, both to be settled at the item that owns them and
recorded there in full: (1) H1's "unambiguously `codebase | spec-fidelity`" versus the same item's
"H1 does not fire on `route: builder` + `ftype: spec-defect`"; (2) whether H2's intent-vs-mechanism
layer is determinable from bp-135's record schema.

Next: Item 9.

## 2026-07-27 — Item 9 CLOSED: the run-state schema and H0

`scripts/autopilot_halt.py` written: `Verdict`, `HALT_ACTIONS`, `REQUIRED_KEYS` (the sixteen §6
keys with a kind each), the structural H0 pass, and the fixed precedence
`H0 → H6 → H7 → H3 → H1 → H2 → H5 → H4 → H8 → CONTINUE` as a stage tuple.

**Design point worth keeping.** Precedence orders *halt reasons*; H0 is not only the first
stage. Any later stage that cannot determine its own answer also returns `H0` — H2 on an audit
record with no legible `verdict_artifact`, H8 on a completion claim with no Gate B record. That
is invariant 7 read literally, and it is what makes Item 12's degenerate input (all completion
flags true, audits dir empty) come out `H0` rather than `CONTINUE`. Documented in the module
docstring and in `explain`'s output so no reader thinks the precedence list was violated.

**H0 fires on:** a non-object; any of the sixteen keys absent; any key `null`; any key of the
wrong kind (bools checked as `isinstance(v, bool)`, ints as `int and not bool` — so both
`"grant_valid": "yes"` and `"grant_valid": 1` halt); an empty string where a path or id is
wanted; a `capsule_hash` that is not 64 **lowercase** hex; **any extra key**; a negative
integer; `budget_tokens_ceiling == 0`; a malformed `scope_denials` entry; a finding id in
`findings_since_base` that does not resolve under `findings_dir` (`CONSTITUTION.md` §III.1); an
unreadable finding file; unparseable JSON; a missing state file at the CLI.

**⚑ Falsifier drilled — "a real supervisor cannot assemble sixteen fields honestly, so it fills
some with guesses."** Hand-assembled a run state and ran it against the **real** repo:

    uv run scripts/autopilot_halt.py classify /tmp/run-state.json
    -> H7: `grant_checked` is false — the grant was never re-verified …        (exit 1)
    # then, with the grant honestly checked:
    -> CONTINUE: no halt condition fired over a fully determined run state      (exit 0)
    # then, declaring one real finding from the corpus:
    -> H1: `finding-0270` is not unambiguously builder-routed
           (ftype=codebase, route=orchestrator) …                              (exit 1)

Field-by-field, which came from an observable fact: `plan` (the plan being built) · `findings_dir`
/ `audits_dir` / `journal_path` (fixed repo paths and the plan's own journal) · `capsule_hash`
(`uv run scripts/capsule.py hash <capsule>` — ran it, real digest) · `findings_since_base`
(`git diff --name-only <base>..HEAD -- docs/findings/` — ran it, 0 on this branch at the time) ·
`remediation_cycles_used` (the supervisor counts the cycles it ran) · `budget_tokens_used`
(`claude -p "/usage"`, the standing pre-flight probe) · `budget_tokens_ceiling` (the capsule's
Time-bound field) · `session_budget_remaining` (the plan's `session_budget` minus sessions
spent) · `scope_denials` (the supervisor's own tool results, §3 Q1's decision) · `grant_valid` /
`grant_checked` (injected; and `grant_checked: false` is the **honest** value before bp-138
lands, which is why the first run above halts) · the three completion flags (the supervisor's
own §7 ledger).

**Zero fields required a guess.** The stated threshold was "more than two guesses ⇒ the schema
is wrong and that is a `spec-defect`". Not tripped. The nearest thing to a guess is
`budget_tokens_used`, which is a harness figure the supervisor must *probe* rather than
estimate — and the schema's answer to "I did not probe" is to leave the key out, which is `H0`.
That is the strictness paying for itself rather than being routed around. ⚑ Note also that the
first classification above halted at `H7` on the honest `grant_checked: false`, which is the
schema doing exactly its job on a run whose grant machinery does not exist yet.

Tests for Item 9 green: the sixteen one-at-a-time removals, the sixteen nulls, eighteen
wrong-type cases, the extra-key case, unparseable JSON, five non-object inputs, and the two
degenerate inputs `{}` and `{"plan": "bp-999"}`.

## 2026-07-27 — Item 10 CLOSED: H1, H3, H6 — the observable conditions

**⚑ The H1 vocabulary reconciliation.** Item 10's acceptance carries two clauses that are not
literally consistent (the §2.4 conservative reading says the pass set is
`codebase | spec-fidelity`; the next clause says `route: builder` + `ftype: spec-defect` must
NOT fire). Resolved as: **H1 does not fire iff `route == builder` AND
`ftype ∈ {codebase, spec-fidelity, spec-defect}`** — the builder-side lane named across both
live vocabularies, per `finding-0193`'s census, gated on an explicit route. Still conservative:
a closed three-name allowlist, and every ambiguity (absent route, absent ftype, unknown value)
halts. Filed as **`finding-0271`** (`spec-fidelity`, builder-resolved) so the plan that
implements `oq-0047` inherits the reconciliation instead of re-deriving it.

**⚑ Falsifier drilled — "H1 fires on essentially every run."** Measured against the **real**
`docs/findings/` corpus, read-only, with the shipped predicate:

    the 30 most recent findings (finding-0241 … finding-0270):  28 / 30 halt  = 93%
    the whole corpus (243 findings):                           199 / 243 halt = 82%

Halting breakdown by `(ftype, route)`: `(discovery, orchestrator)` 9 · `(spec-defect,
orchestrator)` 6 · `(design, orchestrator)` 6 · `(codebase, orchestrator)` 4 ·
`(spec-fidelity, orchestrator)` 3. The two passing are `finding-0244` and `finding-0252`.

**The falsifier fires, and I did not soften the rule** (§10, second stop-and-raise condition).
The measurement is recorded, **`finding-0272`** is filed as `design` and routed to the
orchestrator, and the predicate ships exactly as §2.4 specifies. The honest reading: 93% is
over the population of *finding-raising* runs, and autopilot's envelope (design-inert QoL) is
expected to file **zero** findings — `findings_since_base: []` is the normal case and yields no
H1. What the number establishes is the sharp form of §2.6's own claim: any autopilot run that
files any finding halts, near enough. ⚑ The most informative detail is that **7 of the 28 carry
a builder-lane `ftype` but `route: orchestrator`** — `route:` dominates, which bounds what
implementing `oq-0047` can buy without a corpus sweep. That is in the finding.

**⚑ Degenerate inputs, both asserted.** `findings_since_base: []` (a real observation) reaches
CONTINUE; the key absent yields `H0`. A cited finding id with no file yields `H0` naming the id,
not a silent skip.

**⚑ Mutation campaign — three mutants, three caught.** Each applied to
`scripts/autopilot_halt.py`, `uv run pytest tests/unit/test_autopilot_halt.py -q` run, file
restored from a pristine copy afterwards (final restore re-verified: 150 passed).

| mutant | change | result |
|---|---|---|
| m1 | H1 fires only on `route == "orchestrator"` (conservative arm dropped) | **8 failed**, 142 passed — `test_h1_fires_when_route_is_absent`, `test_h1_fires_when_ftype_is_absent`, and all six `test_h1_fires_on_a_non_builder_ftype_even_when_routed_builder[...]` |
| m2 | H6's missing-journal case returns `None` (falls through) | **1 failed**, 149 passed — `test_h6_fires_when_the_journal_does_not_exist` (`- H6 / + CONTINUE`) |
| m3 | H3 compares `ftype == "blocker"` without `.lower()` | **1 failed**, 149 passed — `test_h3_is_case_insensitive` (`- H3 / + H1`) |

No surviving mutants on the load-bearing leg. Note m3's diff: the case-sensitive H3 does not
merely miss — it reports **H1**, halting for the wrong reason, which is why the mutant matters
even though the run still stops.

## 2026-07-27 — Item 11 CLOSED: H2, H4, H5, H7 — the injected conditions

**⚑ Falsifier drilled — "H2's intent-vs-mechanism distinction is unmakeable from the record."**
**Half true**, and the split is the honest answer. `bp-135` §6's schema carries `gate: A | B`,
and §2.5's table *defines* Gate A as the intent-fidelity gate and Gate B as the mechanism gate
— so the top-level layer mapping IS a field of the record, not a guess. What is **not**
determinable is §2.5's refinement *"or any intent-level CONCERNS"* raised **at Gate B**: no
field carries that.

Fallback applied and stated, never a guess at layer: Gate A + any non-clean ⇒ H2 immediately;
any gate + `serious` ⇒ H2 immediately; Gate B + `concerns` ⇒ H2 iff
`remediation_cycles_used >= 1` (the first is the one cycle §2.5 grants); illegible `gate` or
`verdict_artifact` ⇒ **H0**. Filed as **`finding-0273`** (`spec-fidelity`, builder-resolved)
with two named residual gaps and a two-option re-entry condition: a `layer:` key in bp-135 §6,
or one clarifying sentence in §2.5.

⚑ **`verdict_record` is not consumed by any halt condition.** Item 11's acceptance names
`verdict_artifact` only. Recorded here and in `finding-0273` so the omission is visible rather
than silent — a `misleading` record beside a `clean` artifact currently does not halt.

**⚑ Degenerate inputs, both asserted.** `grant_valid: true, grant_checked: false` yields **H7**
— `grant_checked` is tested first so the reason names the field that actually decided.
`scope_denials: []` is a real observation and yields no H5; the key absent yields H0.

**Invariant held.** This item computes no grant validity and imports nothing from bp-138:
`grant_valid` is data. Enforced structurally by two tests — the AST import allowlist, and
`test_the_classifier_computes_no_grant_validity`, which walks every call in the module and
asserts none of `sha256 / new / compare_digest / hexdigest / digest / urandom` is among them.
The module has no writer of any kind either (`test_the_classifier_never_writes`), which is what
makes "budget is not self-extendable" structural rather than a promise.

## 2026-07-27 — Item 12 CLOSED: H8 and the words the classifier cannot say

H8 fires only when the three completion flags are all true **and** exactly one Gate B record
for the plan exists in `audits_dir` with `verdict_artifact: clean`. `halt` is `True`;
`actions_owed` is the five §2.6 actions verbatim.

**⚑ Degenerate input asserted.** All three flags true with an empty audits directory yields
**`H0`** — not `CONTINUE`, not `H8`. The check is phrased **positively** (the record must be
present, unique, and clean) precisely because "Gate B is not `concerns`" is vacuously true of a
directory holding no Gate B at all, which would declare a run complete with no audit — the
failure §2.7 exists to prevent. Also covered: a clean **Gate A** alone is still `H0`, and
duplicate Gate B records are `H0`.

**Vocabulary enforcement, source-level.** `test_the_verdict_vocabulary_is_exactly_continue_and_
h0_through_h8` parses the module's AST, collects the `code` argument of every `Verdict(...)`
construction and every `_halt(...)` call, asserts each is a **string literal** drawn from
`VERDICT_CODES` (the sole exception being `_halt`'s own pass-through parameter), and asserts the
set found equals `{CONTINUE, H0..H8}` exactly. A companion test asserts none of `merge`,
`deskcheck`, `done`, `complete` occurs in any code. ⚑ A future edit that *computes* a code from
a variable reddens the test too — a non-literal code is one this check cannot audit.

**⚑ Falsifier drilled — "a supervisor reads H8 and merges."** Grepped the new skill for every
place H8's meaning is stated: `grep -n 'H8' .claude/skills/autopilot/SKILL.md` → 6 hits (the
`description` front matter, the run diagram, the halt-table row, the precedence line, the
"do not read `H8` as permission" line, and the five-actions preamble). **Every one says stop.**
The only sentence pairing H8 with the word "merge" is *"H8 is a halt. Autopilot **stops** at a
merge-ready branch and does not merge it, does not deskcheck it, and does not declare it done"*
— which states the prohibition, not the action.

## 2026-07-27 — Item 13 CLOSED: `.claude/skills/autopilot/SKILL.md`

Written with the standard `name`/`description` front matter (the shape the eight existing
skills use). It carries: what a run is (one plan, one grant, one branch) and the run-state
document's two supervisor-bookkeeping obligations (`scope_denials`, `remediation_cycles_used`);
the router; the halt table H0–H8 with the precedence order and its rationale; the exit
inversion; the five halt actions verbatim; the two audit gates with both verbatim adversarial
questions and the dissent semantics; the six §1.2 non-goals verbatim; and the trail every run
leaves. It registers nothing in `.claude/settings.json` (§3 Q4 — skills are discovered by
directory) and edits no existing skill.

**⚑ Falsifier drilled — "the skill duplicates the graduate skill's session-sizing heuristic."**
The skill **links** it with §4's proposed sentence carried verbatim. Greps:

    grep -c 'needs an "and"'      .claude/skills/autopilot/SKILL.md  -> 0
    grep -c 'sprawls across zones' .claude/skills/autopilot/SKILL.md -> 0

Falsifier does not fire, and a test pins both at zero — the test also asserts the phrases are
still **live in the graduate skill**, so it reddens if the anchor moves rather than passing
vacuously.

**⚑ Degenerate input asserted.** "Every required literal present, but inside a fenced block or
an HTML comment." All literal checks run against **rendered prose** (`_prose` strips HTML
comments and fenced blocks), and `test_the_prose_check_ignores_comments_and_code_fences` proves
the stripper reddens on the exit sentence parked in each, plus on every one of the six
non-goals parked in a comment. The link-resolution test likewise is proved to redden on a
fabricated path (`docs/design-notes/dn-not-a-note.md`) and asserts the cited set is non-empty
first, so it cannot pass vacuously on a skill that cites nothing.

⚑ Two build-time bugs in the checks themselves, caught by their own degenerate tests and worth
recording: the citation regex first matched a bare `autopilot_halt.py` mentioned in prose (fixed
by requiring at least one `/`), and it did not match a leading-dot path, so
`.claude/skills/graduate/SKILL.md` was silently being checked as `claude/skills/...`. Both would
have made the link check quietly wrong in opposite directions.

## 2026-07-27 — green gate, and the seal

Every leg run **separately**, never `&&`-chained, each result read:

| leg | result |
|---|---|
| `uv run ruff check .` | `All checks passed!` |
| `uv run mypy core agents eval ops scheduler scripts` | `Success: no issues found in 263 source files` |
| `uv run mypy` (argless) | `Found 69 errors in 20 files (checked 564 source files)` — **the baseline is exactly 69**, unmoved; the new test file contributes none |
| `uv run python -m ops.type_gate` | Tier-2 membership OK · bare-ignore scan OK · one parked non-fatal `psutil` shim report (`finding-0223`, pre-existing) |
| `uv run pytest -q` | `6 failed, 2567 passed, 15 skipped` in 9m46s |

⚑ **The six failures are pre-existing and none is mine — established, not assumed.** Stashed
the entire working tree including untracked files (`git stash push -u`), confirmed the tree was
clean at `origin/main`, and re-ran exactly those six: **all six fail identically on the pristine
tree** (`6 failed, 5 passed in 5.64s`). Restored with `git stash pop` and re-verified the new
suite (150 passed). The six:

- `test_core_imports_nothing_outside_core` — the standing green-gate deselect (owner's local-CI
  rule); `core/temporal/spine.py:98 → eval`.
- `test_worktree_enforcement.py` ×3 and `test_handoff_availability` — hook-enforcement and
  worktree-seat tests, and **agent hooks are disabled repo-wide tonight** by owner ruling
  (`69a065c` removed the `hooks` key from `.claude/settings.json`). These test the disabled cage.
- `test_dream_v2_live` — a live e2e needing a resident model.

New-file suite: **150 passed in 0.32s** (`tests/unit/test_autopilot_halt.py`).

**Write scope honoured.** `git status` shows exactly: `scripts/autopilot_halt.py`,
`tests/unit/test_autopilot_halt.py`, `.claude/skills/autopilot/SKILL.md`, this journal, and
three new files under `docs/findings/`. Nothing outside. No `status:` field was flipped on any
artifact; `docs/templates/finding.md` was **not** swept (§9 non-goal 4);
`.claude/settings.json` and `.claude/hooks/**` were not touched (§5, §9 non-goal 3).

**Findings filed.** `finding-0271` (spec-fidelity, builder-resolved — H1's pass set) ·
`finding-0272` (design → orchestrator — the measured 93%/82% halt rate; **needs an owner
ruling**) · `finding-0273` (spec-fidelity, builder-resolved — H2's half-determinable layer, two
residual gaps named).

**Left undone, deliberately, with reasons:**

1. **`verdict_record` participates in no halt condition.** Item 11's acceptance names
   `verdict_artifact` only. A `misleading` record beside a `clean` artifact does not halt.
   Recorded in `finding-0273` with a re-entry condition rather than fixed on builder authority.
2. **No integration coverage against a real `bp-135` audit record** — none exists in the tree
   (`grep -l 'gate:' docs/audits/*.md` → nothing). Fixture coverage only, against the schema
   `bp-135` §6 pins. When `bp-135` lands, the first real Gate A/B pair is the integration test.
3. **`oq-0047` is not implemented and the finding template is not swept** — §9 non-goal 4.
   `finding-0271` carries the H1 reconciliation forward to that plan.
4. **No supervisor exists** (§9 non-goal 1). This plan shipped a decision function and its
   operating contract; the five halt actions are the supervising session's, and
   `.claude/skills/autopilot/SKILL.md` is where that obligation now lives.

**Fresh-agent note.** Everything a successor needs is here plus the plan. The one thing not
recoverable from the artifacts alone: the citation-regex bugs recorded in Item 13's entry were
found because the *degenerate* tests were written before the checks were trusted — if a future
edit touches `_CITED` or `_prose` in the test file, re-run
`test_the_link_resolution_check_reddens_on_a_fabricated_path` and
`test_the_prose_check_ignores_comments_and_code_fences` first; they are the only things
standing between that check and a vacuous green.
