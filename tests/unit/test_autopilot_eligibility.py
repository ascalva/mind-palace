"""bp-137 — the autopilot-eligibility predicate: falsifiers, degenerate inputs, and the census.

Every item of bp-137 delivers a **gate**, so the false-success rule applies to all four
(`docs/brainstorms/the-false-success-rule.md:17-31`): each check's degenerate input — the case
on which it would pass *without testing its claim* — is named and asserted to redden. The
degenerate inputs here are all the same shape: a term whose evidence is absent rather than
violated, over which "for every x, P(x)" is vacuously true.
"""

from __future__ import annotations

import ast
import itertools
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / ".claude" / "hooks"))

import _lib  # type: ignore[import-not-found]  # noqa: E402
from autopilot_eligibility import (  # type: ignore[import-not-found]  # noqa: E402
    FORBIDDEN_SCOPE,
    FORBIDDEN_WITNESSES,
    LIVE_STATE_TOKENS,
    P3_CORRECTION_BANNER,
    TERM_NAMES,
    Evaluation,
    Result,
    Term,
    check_p1,
    check_p2,
    check_p3,
    check_p4,
    check_p5,
    conjoin,
    deglue,
    diagnostics,
    escapes_root,
    evaluate,
    item_bodies,
    main,
    matches_any,
    normalize_flag,
    report_line,
    section_seven,
    write_scope,
)

TOOL = REPO / "scripts" / "autopilot_eligibility.py"
PLANS = sorted((REPO / "docs" / "build-plans").glob("*/plan.md"))


# ------------------------------------------------------------------------------------------
# Fixture construction — a minimal but real-shaped plan
# ------------------------------------------------------------------------------------------


def make_plan(
    *,
    scope: Sequence[str] | None = ("scripts/foo.py",),
    budget: str | None = "1",
    items: Sequence[str | None] | None = None,
    extra_item_prose: str = "",
    omit_section_7: bool = False,
    zero_items: bool = False,
) -> str:
    """Build a plan's text. `items` is one entry per §7 item: the raw text after
    `**Touches stored data?**`, or None for an item that carries no flag line at all.
    `scope=None` omits the `write_scope` key entirely; `scope=[]` writes `write_scope: []`."""
    lines = ["---", "type: build-plan", "id: bp-999", "status: ready"]
    if scope is not None:
        if len(scope) == 0:
            lines.append("write_scope: []")
        else:
            lines.append("write_scope:")
            lines += [f"  - {entry}" for entry in scope]
    if budget is not None:
        lines.append(f"session_budget: {budget}")
    lines += ["---", "", "# Build Plan — fixture", "", "## 1. Objective", "", "A fixture.", ""]
    if not omit_section_7:
        lines += ["## 7. Items", ""]
        if not zero_items:
            for i, flag in enumerate(items if items is not None else ["No."], start=1):
                lines += [
                    f"### Item {i} — fixture item",
                    "",
                    "- **Objective:** one line",
                    "- **Acceptance test:** `uv run pytest -q` green",
                ]
                if flag is not None:
                    lines.append(f"- **Touches stored data?** {flag}")
                if extra_item_prose:
                    lines.append(extra_item_prose)
                lines.append("")
    lines += ["## 9. Non-goals", "", "1. Nothing.", ""]
    return "\n".join(lines) + "\n"


CLEAN_ITEM = "No."


# ------------------------------------------------------------------------------------------
# Item 14 — P1: repo-confined
# ------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "entry",
    [
        "/etc/passwd",
        "/Users/someone/elsewhere/**",
        "../outside/**",
        "docs/../../outside.py",
        "~/secrets.txt",
        "C:/windows/**",
    ],
)
def test_p1_fails_for_a_glob_that_leaves_the_worktree(entry: str) -> None:
    term = check_p1([entry])
    assert term.result is Result.FAIL, term
    assert entry in term.evidence


@pytest.mark.parametrize(
    "entry",
    [
        "scripts/autopilot_eligibility.py",
        "tests/unit/**",
        "**/conftest.py",
        "docs/build-plans/bp-137/**",
        "core/stores/*.py",
        "docs/..",
    ],
)
def test_p1_passes_for_ordinary_repo_relative_globs(entry: str) -> None:
    assert check_p1([entry]).result is Result.PASS


def test_p1_degenerate_empty_scope_is_undetermined_not_pass() -> None:
    """⚑ THE DEGENERATE INPUT (plan §7 Item 14). "Every glob resolves inside the worktree" is
    VACUOUSLY TRUE over an empty scope, so a two-valued P1 returns PASS for a plan that
    declares no capability at all. Absence must refuse exactly as violation does."""
    for scope in ([], list(write_scope({})), write_scope({"write_scope": "null"})):
        term = check_p1(list(scope))
        assert term.result is Result.UNDETERMINED, term
        assert term.result is not Result.PASS
        assert "vacuous" in term.evidence


def test_p1_reads_absent_empty_and_null_write_scope_all_as_absent() -> None:
    assert write_scope({}) == []
    assert write_scope({"write_scope": ""}) == []
    assert write_scope({"write_scope": "null"}) == []
    assert write_scope({"write_scope": []}) == []
    assert write_scope({"write_scope": ["a.py", "  ", "b.py"]}) == ["a.py", "b.py"]


def test_escapes_root_is_pure_string_arithmetic() -> None:
    assert escapes_root("") is True
    assert escapes_root("   ") is True
    assert escapes_root("a/../b") is False
    assert escapes_root("a/../../b") is True
    assert escapes_root("a\\..\\..\\b") is True  # backslashes normalized like glob_match does


# ------------------------------------------------------------------------------------------
# Item 14 — P2: record/enforcement-free
# ------------------------------------------------------------------------------------------


@pytest.mark.parametrize("member", list(FORBIDDEN_SCOPE))
def test_p2_fails_for_each_forbidden_member_named_directly(member: str) -> None:
    term = check_p2([member])
    assert term.result is Result.FAIL, term


@pytest.mark.parametrize(
    "member_path",
    [
        "CLAUDE.md",
        ".claude/hooks/_lib.py",
        ".claude/settings.json",
        "docs/design-notes/agent-workflow.md",
        "eval/metrics.py",
        "eval/some/deep/new_file.py",
    ],
)
def test_p2_fails_for_a_concrete_path_inside_a_forbidden_tree(member_path: str) -> None:
    """Direction (a): the entry read as a PATH against the forbidden patterns. `eval/…` deep
    files are matched by no witness, so only this direction sees them."""
    assert check_p2([member_path]).result is Result.FAIL


@pytest.mark.parametrize("covering", [".claude/**", "docs/**", "**", ".claude/hooks/*.py"])
def test_p2_fails_for_a_glob_that_covers_a_forbidden_surface_without_naming_it(
    covering: str,
) -> None:
    """Direction (b): a forbidden WITNESS against the entry read as a pattern. `.claude/**`
    is not matched by the pattern `.claude/hooks/**`, so direction (a) alone would miss it —
    which is why P2 checks both, and why this test would redden if either were dropped."""
    term = check_p2([covering])
    assert term.result is Result.FAIL, term
    assert "covers forbidden surface" in term.evidence or "forbidden set" in term.evidence


def test_p2_passes_for_a_disjoint_scope() -> None:
    term = check_p2(["scripts/autopilot_eligibility.py", "tests/unit/**", "core/stores/*.py"])
    assert term.result is Result.PASS, term


def test_p2_degenerate_empty_scope_is_undetermined_not_pass() -> None:
    """⚑ THE DEGENERATE INPUT. "scope ∩ forbidden = ∅" is VACUOUSLY TRUE over an empty scope."""
    term = check_p2([])
    assert term.result is Result.UNDETERMINED, term
    assert term.result is not Result.PASS
    assert "vacuously true" in term.evidence


def test_p2_degenerate_glued_inline_comment_fails_and_names_finding_0085() -> None:
    """⚑ THE SECOND DEGENERATE INPUT (finding-0085 / bp-066). `- eval/metrics.py  # absorbed`
    reaches the guard with the comment GLUED to the glob, so it matches nothing — the
    forbidden-set intersection is empty and a naive P2 passes a scope that names `eval/`."""
    term = check_p2(["eval/metrics.py  # absorbed into the sweep"])
    assert term.result is Result.FAIL, term
    assert "finding-0085" in term.evidence
    # And the vacuity is real: the glued entry genuinely matches nothing under the guard.
    assert not matches_any("eval/metrics.py", ["eval/metrics.py  # absorbed into the sweep"])


def test_p2_glued_comment_fails_even_on_an_otherwise_harmless_glob() -> None:
    """A glued entry means the declared capability is not what it reads as, whatever it
    names. Refusing on the ambiguity is invariant 7 at the gate's mouth."""
    term = check_p2(["scripts/foo.py  # just a note"])
    assert term.result is Result.FAIL, term
    assert "finding-0085" in term.evidence


def test_deglue_splits_the_footgun_and_leaves_a_clean_entry_alone() -> None:
    assert deglue("eval/metrics.py  # absorbed") == ("eval/metrics.py", True)
    assert deglue("  scripts/foo.py ") == ("scripts/foo.py", False)
    assert deglue("# only a comment") == ("", True)


# ------------------------------------------------------------------------------------------
# Item 14 — the matcher is the guard's own, not a re-implementation
# ------------------------------------------------------------------------------------------


def test_the_matcher_is_lib_matches_any_by_identity() -> None:
    """Two matchers that disagree mean the predicate blesses a scope `scope-guard` reads
    differently — a security-relevant duplication (plan §2 DRY audit)."""
    import autopilot_eligibility

    assert autopilot_eligibility.matches_any is _lib.matches_any


def test_the_module_defines_no_local_glob_implementation() -> None:
    """The AST half of the same assertion: no local glob function, no `fnmatch`, no `glob`."""
    tree = ast.parse(TOOL.read_text(encoding="utf-8"))
    defined = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    for forbidden in ("glob_match", "_seg_match", "fnmatch", "_glob", "match_glob"):
        assert forbidden not in defined, f"{forbidden} re-derives the guard's glob semantics"
    imported = _imported_top_level(tree)
    assert "fnmatch" not in imported and "glob" not in imported


PROBE_PATHS = [
    "CLAUDE.md",
    ".claude/hooks/_lib.py",
    ".claude/settings.json",
    "docs/design-notes/agent-workflow.md",
    "docs/build-plans/bp-137/plan.md",
    "eval/golden.py",
    "eval/metrics.py",
    "core/stores/sourceset.py",
    "scripts/board.py",
    "tests/unit/test_capsule.py",
    "a/deep/nested/path/file.py",
]


def test_p1_p2_agree_with_the_guards_matcher_on_five_real_write_scopes() -> None:
    """⚑ ITEM 14's FALSIFIER, drilled. Take five real `write_scope` lists from the tree, run
    `_lib.matches_any` and this predicate's own covering decision over a fixed probe set, and
    assert identical verdicts. A disagreement is a change to the guard's semantics and is not
    this plan's to make (plan §10) — it would stop the build, not be tuned away."""
    real: list[list[str]] = []
    for plan in PLANS:
        scope = write_scope(_lib.parse_front_matter(plan.read_text(encoding="utf-8")))
        if scope:
            real.append(scope)
        if len(real) == 5:
            break
    assert len(real) == 5, "expected at least five real plans with a non-empty write_scope"

    import autopilot_eligibility

    for scope in real:
        for probe in PROBE_PATHS:
            guard = _lib.matches_any(probe, scope)
            ours = autopilot_eligibility.matches_any(probe, scope)
            assert guard == ours, f"matcher disagreement on {probe!r} vs {scope!r}"

        # The semantic bridge, not just the identity: if the GUARD would let this scope write
        # a forbidden surface, P2 must refuse the plan. A P2 that called such a scope clean is
        # exactly the falsifier — the predicate measuring its own glob code, not the guard's
        # capability.
        guard_reaches_forbidden = any(
            _lib.matches_any(witness, scope) for witness in FORBIDDEN_WITNESSES
        )
        if guard_reaches_forbidden:
            assert check_p2(list(scope)).result is Result.FAIL, scope


def test_item_bodies_splits_section_7_at_each_item_heading() -> None:
    section = section_seven(make_plan(items=["No.", "No.", "No."]))
    assert section is not None
    bodies = item_bodies(section)
    assert len(bodies) == 3
    assert all(body.startswith("### Item ") for body in bodies)
    assert section_seven(make_plan(omit_section_7=True)) is None


# ------------------------------------------------------------------------------------------
# Item 15 — P3: the stored-data flag against the pinned regex (finding-0263)
# ------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "value",
    [
        "no",
        "No",
        "No.",
        "**No.**",
        "No. **Parallelizable?** yes  **Depends on:** none",
        "no  **Depends on:** none",
        "**No.** **Parallelizable?** no",
    ],
)
def test_p3_passes_only_on_a_value_that_normalizes_to_exactly_no(value: str) -> None:
    assert normalize_flag(value) == "no"
    assert check_p3(section_seven(make_plan(items=[value]))).result is Result.PASS


@pytest.mark.parametrize(
    "value",
    [
        "yes",
        "Yes — a new SQLite table under data/",
        "Reads only.",
        "No (reads the corpus)",
        "No — reads the vault",
        "No, but it reads the store",
        "Not directly.",
    ],
)
def test_p3_fails_on_every_hedged_spelling_from_the_census(value: str) -> None:
    term = check_p3(section_seven(make_plan(items=[value])))
    assert term.result is Result.FAIL, term
    assert term.result is not Result.PASS


def test_p3_undetermined_for_an_item_with_no_flag_line() -> None:
    term = check_p3(section_seven(make_plan(items=[CLEAN_ITEM, None])))
    assert term.result is Result.UNDETERMINED, term
    assert "no '**Touches stored data?**' line" in term.evidence


def test_p3_undetermined_for_two_flag_lines_in_one_item() -> None:
    plan = make_plan(items=["No."], extra_item_prose="- **Touches stored data?** No.")
    term = check_p3(section_seven(plan))
    assert term.result is Result.UNDETERMINED, term
    assert "2 '**Touches stored data?**' lines" in term.evidence


def test_p3_degenerate_zero_items_is_undetermined_not_pass() -> None:
    """⚑ THE DEGENERATE INPUT (plan §7 Item 15). "Every item carries the flag as `no`" is
    VACUOUSLY TRUE over a plan with no items, so a naive P3 returns PASS for a plan with no
    §7 at all. Absence refuses exactly as violation does."""
    for plan in (make_plan(zero_items=True), make_plan(omit_section_7=True)):
        term = check_p3(section_seven(plan))
        assert term.result is Result.UNDETERMINED, term
        assert term.result is not Result.PASS


def test_p3_degenerate_the_literal_2_4_reading_would_pass_the_vector_store_plan() -> None:
    """⚑ THE SECOND DEGENERATE INPUT. §2.4's literal check — grep for `touches_stored_data:`,
    find nothing, see no `true`, return PASS — passes on EVERY plan in the repository. This
    test is the one that reddens if the implementation ever regresses to the front-matter key:
    it asserts FAIL on a plan whose §7 says it rewrites the vector store, and demonstrates in
    the same breath that the literal reading finds nothing to object to."""
    plan = make_plan(items=["Yes — rewrites the vector store"])
    assert check_p3(section_seven(plan)).result is Result.FAIL
    assert "touches_stored_data:" not in plan  # the literal field simply is not there
    assert "true" not in plan.lower().split("## 7.")[1]  # ...and there is no `true` to catch


def test_p3_fail_dominates_undetermined_within_one_plan() -> None:
    term = check_p3(section_seven(make_plan(items=["Yes", None])))
    assert term.result is Result.FAIL


def test_normalize_flag_does_not_prefix_match() -> None:
    """m1 of the mutation campaign: `value.startswith("no")` in place of exact equality is
    caught here and by the `No (reads the corpus)` fixture above."""
    assert normalize_flag("No (reads the corpus)") != "no"
    assert normalize_flag("Not directly.") != "no"
    assert normalize_flag("No — reads the vault") != "no"


def test_normalize_flag_truncation_at_a_run_on_bolded_field_is_load_bearing() -> None:
    """m3: dropping the truncation makes the 57-plan run-on form fail. Pin it explicitly."""
    run_on = "No. **Parallelizable?** yes  **Depends on:** none"
    assert normalize_flag(run_on) == "no"
    assert run_on.strip().strip("*").strip().rstrip(".").strip().lower() != "no"


def test_module_docstring_carries_the_finding_0263_correction_banner_verbatim() -> None:
    """Plan §4: the ratified note is agent-immutable (A8), so the correction is carried in the
    tool's own docstring and repeated in its report output. The banner is SLICED from
    `__doc__`, so docstring and report cannot drift."""
    import autopilot_eligibility

    doc = autopilot_eligibility.__doc__ or ""
    assert P3_CORRECTION_BANNER
    assert P3_CORRECTION_BANNER in doc
    for phrase in (
        "DOES NOT EXIST",
        "appears in ZERO",
        "exactly `no`",
        "AUTHORITATIVE",
        "`spec-defect`, never a silent re-interpretation",
        "LEXICAL scan",
        "Un-self-extendability",
    ):
        assert phrase in P3_CORRECTION_BANNER, phrase


# ------------------------------------------------------------------------------------------
# Item 16 — P4: the lexical scan, and P5: the bound
# ------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "prose",
    [
        "- run `mind-palace deploy` at the end",
        "- DEPLOY the stack",
        "- `palace restart` after the change",
        "- palace stop, then start again",
        "- read the token with `security find-generic-password -s x`",
        "- call `get_secret('x')`",
        "- upload with boto3",
        "- run `aws s3 cp ...`",
        "- fetch it with curl https://example.com",
        "- shell out via subprocess.run",
    ],
)
def test_p4_fails_on_every_deny_list_token(prose: str) -> None:
    term = check_p4(section_seven(make_plan(items=[CLEAN_ITEM], extra_item_prose=prose)))
    assert term.result is Result.FAIL, term


def test_p4_passes_for_a_plan_whose_section_7_contains_no_token() -> None:
    term = check_p4(section_seven(make_plan(items=[CLEAN_ITEM])))
    assert term.result is Result.PASS, term


def test_p4_degenerate_absent_or_empty_section_7_is_undetermined_not_pass() -> None:
    """⚑ THE DEGENERATE INPUT (plan §7 Item 16). "No acceptance step runs `deploy`" is
    VACUOUSLY TRUE when there is nothing to scan."""
    for plan in (make_plan(omit_section_7=True), make_plan(zero_items=True)):
        term = check_p4(section_seven(plan))
        assert term.result is Result.UNDETERMINED, term
        assert term.result is not Result.PASS


def test_p4_degenerate_a_token_inside_a_fenced_block_still_fails() -> None:
    """⚑ THE SECOND DEGENERATE INPUT. A scanner that skips fences — the natural "ignore code"
    instinct — passes a plan whose acceptance is literally a fenced `mind-palace deploy`. The
    second assertion is what would redden if fence-skipping were introduced: the fence is the
    ONLY carrier of the token here, so a fence-blind scan sees a clean §7."""
    fenced = "\n```\nmind-palace deploy\n```\n"
    section = section_seven(make_plan(items=[CLEAN_ITEM], extra_item_prose=fenced))
    assert section is not None
    assert check_p4(section).result is Result.FAIL

    defenced = _strip_fences(section)
    assert "deploy" not in defenced.lower(), "fixture no longer isolates the token to the fence"
    assert check_p4(defenced).result is Result.PASS


def _strip_fences(text: str) -> str:
    """A fence-skipping scanner's view of the text — used only to prove what one would miss."""
    out, inside = [], False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            inside = not inside
            continue
        if not inside:
            out.append(line)
    return "\n".join(out)


def test_p4_token_table_is_the_pinned_deny_list() -> None:
    labels = {label for label, _ in LIVE_STATE_TOKENS}
    assert labels == {
        "deploy",
        "palace lifecycle mutation",
        "keychain read",
        "secret read",
        "aws sdk",
        "aws cli",
        "network call",
        "shell-out",
    }


def test_p5_passes_for_a_finite_bound() -> None:
    assert check_p5({"session_budget": "1"}).result is Result.PASS
    assert check_p5({"session_budget": "3  # comment"}).result is Result.PASS


@pytest.mark.parametrize("budget", ["0", "-1", "1.5", "one", "many", "1 2"])
def test_p5_fails_for_a_non_positive_or_non_integer_bound(budget: str) -> None:
    assert check_p5({"session_budget": budget}).result is Result.FAIL


@pytest.mark.parametrize("budget", [None, "", "   ", "null", "none", "~"])
def test_p5_degenerate_absent_empty_or_null_is_undetermined_not_pass(budget: str | None) -> None:
    """⚑ `_lib.parse_front_matter` returns a YAML `null` as the literal string `"null"`
    (§3 Q4), so an unfilled budget field looks like a value. Undetermined ⇒ refuse."""
    front_matter: dict[str, object] = {} if budget is None else {"session_budget": budget}
    term = check_p5(front_matter)
    assert term.result is Result.UNDETERMINED, term
    assert term.result is not Result.PASS


def test_p5_evidence_states_that_the_runtime_half_is_unchecked() -> None:
    assert "runtime half is unchecked" in check_p5({"session_budget": "1"}).evidence


# ------------------------------------------------------------------------------------------
# Item 17 — the conjunction
# ------------------------------------------------------------------------------------------


def test_conjunction_over_all_243_term_combinations() -> None:
    """⚑ THE LOAD-BEARING TEST. All 3**5 = 243 combinations: exactly ONE is overall PASS, and
    no combination containing an UNDETERMINED is. This is the assertion that the natural
    `all(t is not Result.FAIL)` — which returns PASS when every term is UNDETERMINED, i.e.
    when nothing was determined about anything — is impossible here."""
    passes = []
    for combo in itertools.product(Result, repeat=len(TERM_NAMES)):
        results = dict(zip(TERM_NAMES, combo, strict=True))
        overall = conjoin(results)
        assert overall in (Result.PASS, Result.FAIL)
        if overall is Result.PASS:
            passes.append(results)
        if any(r is Result.UNDETERMINED for r in combo):
            assert overall is Result.FAIL, results
    assert len(passes) == 1
    assert passes[0] == dict.fromkeys(TERM_NAMES, Result.PASS)


def test_the_naive_conjunction_would_admit_thirty_two_combinations() -> None:
    """The mutation, stated as arithmetic: `all(t is not FAIL)` admits 2**5 = 32 combinations
    including the all-UNDETERMINED one. `conjoin` admits exactly 1. If the two counts ever
    agree, the conjunction has become two-valued in disguise."""
    naive = [
        combo
        for combo in itertools.product(Result, repeat=len(TERM_NAMES))
        if all(r is not Result.FAIL for r in combo)
    ]
    assert len(naive) == 32
    assert conjoin(dict.fromkeys(TERM_NAMES, Result.UNDETERMINED)) is Result.FAIL


@pytest.mark.parametrize(
    "results",
    [
        {},
        {"P1": Result.PASS},
        dict.fromkeys(("P1", "P2", "P3", "P4"), Result.PASS),
        dict.fromkeys(("P1", "P2", "P3", "P4", "P5", "P6"), Result.PASS),
        dict.fromkeys(("P1", "P2", "P3", "P4", "PX"), Result.PASS),
    ],
)
def test_conjunction_refuses_an_incomplete_or_wrong_term_set(results: dict[str, Result]) -> None:
    """⚑ Absence at the conjunction itself. `all(...)` over an empty sequence is True — the
    purest vacuous pass in the module — so `conjoin` requires the COMPLETE keyed term set as a
    precondition rather than trusting its caller to have computed one."""
    assert conjoin(results) is Result.FAIL


# ------------------------------------------------------------------------------------------
# Item 17 — the report
# ------------------------------------------------------------------------------------------


def _clean_plan(n_globs: int = 1) -> str:
    return make_plan(
        scope=[f"scripts/generated_{i}.py" for i in range(n_globs)],
        items=[CLEAN_ITEM, CLEAN_ITEM],
    )


def test_a_fully_clean_plan_passes_all_five_terms() -> None:
    evaluation = evaluate(_clean_plan())
    assert evaluation.overall is Result.PASS, diagnostics(evaluation)
    assert all(t.result is Result.PASS for t in evaluation.terms.values())


def test_report_is_one_line_under_200_chars_for_a_plan_with_twenty_globs() -> None:
    evaluation = evaluate(_clean_plan(20))
    line = report_line(evaluation)
    assert "\n" not in line
    assert len(line) < 200, len(line)
    assert line.startswith("achievable: 20 globs;")


def test_report_line_is_rendered_from_the_computed_terms_not_a_template() -> None:
    """⚑ THE SECOND DEGENERATE INPUT for Item 17: a `report` that prints `P1 pass P2 pass …`
    from a template rather than from the computed terms. The FAIL plan's line must differ from
    the PASS plan's in exactly the term positions that differ."""
    good = report_line(evaluate(_clean_plan()))
    bad = report_line(
        evaluate(
            make_plan(scope=["eval/**"], items=["Yes — rewrites the vector store"], budget="0")
        )
    )
    assert good != bad
    assert "P1 pass P2 pass P3 pass P4 pass(lexical) P5 pass" in good
    assert "P2 fail" in bad and "P3 fail" in bad and "P5 fail" in bad


def test_report_line_carries_the_standing_caveats() -> None:
    line = report_line(evaluate(_clean_plan()))
    assert "P3=finding-0263 form" in line
    assert "P4 lexical" in line
    assert "P5 plan-side bound only" in line


def test_report_line_worst_case_width_is_bounded() -> None:
    evaluation = Evaluation(
        terms={n: Term(n, Result.UNDETERMINED, "") for n in TERM_NAMES},
        scope=[f"g{i}/**" for i in range(20)],
    )
    assert len(report_line(evaluation)) < 200


def test_diagnostics_name_every_non_pass_term_in_order() -> None:
    evaluation = evaluate(make_plan(scope=[], items=None, budget=None, zero_items=True))
    lines = diagnostics(evaluation)
    assert [line.split()[0] for line in lines] == list(TERM_NAMES)
    assert all("undetermined" in line for line in lines)


# ------------------------------------------------------------------------------------------
# Item 17 — the CLI
# ------------------------------------------------------------------------------------------


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(TOOL), *args], capture_output=True, text=True, check=False
    )


def test_check_exits_zero_iff_overall_pass(tmp_path: Path) -> None:
    good = tmp_path / "good.md"
    good.write_text(_clean_plan(), encoding="utf-8")
    bad = tmp_path / "bad.md"
    bad.write_text(make_plan(scope=[], items=["Yes"]), encoding="utf-8")

    ok = _run("check", str(good))
    assert ok.returncode == 0, ok.stdout + ok.stderr
    assert ok.stdout.strip() == ""

    nope = _run("check", str(bad))
    assert nope.returncode == 1
    assert "P1 undetermined:" in nope.stdout
    assert "P3 fail:" in nope.stdout


def test_report_stdout_is_exactly_one_line_and_the_banner_goes_to_stderr(tmp_path: Path) -> None:
    plan = tmp_path / "p.md"
    plan.write_text(_clean_plan(), encoding="utf-8")
    out = _run("report", str(plan))
    assert out.returncode == 0, out.stdout + out.stderr
    assert len(out.stdout.strip().splitlines()) == 1
    assert out.stdout.startswith("achievable: ")
    assert "DOES NOT EXIST" in out.stderr
    assert "LEXICAL scan" in out.stderr


def test_main_returns_one_for_an_unreadable_plan(tmp_path: Path) -> None:
    assert main(["check", str(tmp_path / "nope.md")]) == 1


# ------------------------------------------------------------------------------------------
# Item 17 — the tooling invariant (the tests/unit/test_capsule.py:414-431 precedent)
# ------------------------------------------------------------------------------------------


def _imported_top_level(tree: ast.Module) -> set[str]:
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name.split(".")[0])
    return imported


def test_the_tool_imports_stdlib_and_lib_only_and_cannot_reach_a_secret() -> None:
    """Absent `os` and `subprocess` there is no route to an environment variable, the
    `security` CLI, or any other secret path — finding-0207's constraint held by construction
    rather than by convention. §2.4: *"The agent's role in eligibility is exactly nothing."*"""
    imported = _imported_top_level(ast.parse(TOOL.read_text(encoding="utf-8")))
    allowed = {"__future__", "argparse", "enum", "re", "sys", "dataclasses", "pathlib", "_lib"}
    assert imported <= allowed, f"unexpected imports: {imported - allowed}"
    for forbidden in ("os", "subprocess", "core", "config", "keyring", "hmac"):
        assert forbidden not in imported, f"the predicate must never import {forbidden}"


def test_the_tool_never_writes_a_file() -> None:
    """It computes a necessary condition and holds no authority: no `open(...,'w')`, no
    `write_text`, no `status` flip."""
    source = TOOL.read_text(encoding="utf-8")
    for forbidden in ("write_text(", "open(", "unlink(", "mkdir(", "rename("):
        assert forbidden not in source, forbidden


def test_the_forbidden_set_is_the_verbatim_2_4_membership() -> None:
    """m1 of the campaign: dropping `.claude/hooks/**` from the forbidden set is caught here
    and by the covering test above. P2 is the leg that keeps autopilot out of its own cage."""
    assert set(FORBIDDEN_SCOPE) == {
        "CLAUDE.md",
        ".claude/hooks/**",
        ".claude/settings.json",
        "docs/design-notes/**",
        "eval/**",
    }
    for witness in FORBIDDEN_WITNESSES:
        assert matches_any(witness, list(FORBIDDEN_SCOPE)), witness


# ------------------------------------------------------------------------------------------
# Item 17 — the census (READ-ONLY over the real tree; asserts termination, never a pass rate)
# ------------------------------------------------------------------------------------------


def test_census_over_every_real_plan_terminates_with_a_result_for_each() -> None:
    """Plan §7 Item 17: run the predicate over every `docs/build-plans/*/plan.md`, assert only
    that it terminates and returns a `Result` for each, and print the tally. It asserts NO
    pass rate: most existing plans will not pass, and that is correct — P1–P5 gates autopilot
    eligibility, not repo hygiene (plan §9 non-goal 1).

    ⚑ Item 17's falsifier lives here: if EVERY real plan were UNDETERMINED on the same term,
    the predicate would be measuring an authoring convention nobody follows rather than a
    property — a `spec-defect` against §2.4, routed to the orchestrator, not a threshold to
    relax. The assertion below is exactly that no term is constant-UNDETERMINED across the
    tree, which is also the "a constant function measures nothing" keep from plan §8.
    """
    assert len(PLANS) > 50, "expected the real build-plan tree"
    tally: dict[str, dict[str, int]] = {n: {r.value: 0 for r in Result} for n in TERM_NAMES}
    overall = {r.value: 0 for r in Result}
    for plan in PLANS:
        evaluation = evaluate(plan.read_text(encoding="utf-8"))
        assert set(evaluation.terms) == set(TERM_NAMES), plan
        for name, term in evaluation.terms.items():
            assert isinstance(term.result, Result), plan
            tally[name][term.result.value] += 1
        overall[evaluation.overall.value] += 1

    print(f"\ncensus over {len(PLANS)} plans — overall: {overall}")
    for name in TERM_NAMES:
        print(f"  {name}: {tally[name]}")

    for name in TERM_NAMES:
        assert tally[name]["undetermined"] < len(PLANS), (
            f"{name} is UNDETERMINED on every plan in the tree — the predicate is measuring an "
            f"authoring convention nobody follows. STOP and file a spec-defect against §2.4."
        )
