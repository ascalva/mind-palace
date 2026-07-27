#!/usr/bin/env python
"""Autopilot eligibility — §2.4's P1–P5 as a **conjunctive three-valued predicate** (bp-137).

`dn-autopilot-and-delegated-blessing` §2.4 defines low-stakes work structurally: *"work is
low-stakes iff its complete rollback is a git operation"*, decided by five conjunctive
predicates over a plan's own fields. §2.8 makes those five *the* reversibility guarantee —
P1–P4 jointly mean every effect of a run is uncommitted-to-main, git-tracked,
stored-data-free and live-state-free. This module computes them.

    uv run scripts/autopilot_eligibility.py check <plan-file>
      -> exit 0 iff all five predicates PASS; exit 1 otherwise, with one diagnostic line
         per non-PASS term naming the predicate, the result, and the evidence
    uv run scripts/autopilot_eligibility.py report <plan-file>
      -> prints the capsule-ready one-line `achievable:` block on stdout (the correction
         banner below goes to stderr, so stdout stays a single embeddable line);
         exit code as for `check`

WHAT THIS TOOL IS NOT. It computes a **necessary** condition and holds no authority. The
sufficient condition is the owner issuing a code from his phone (§2.4: *"The agent's role in
eligibility is exactly nothing"*). No code path here represents a grant, reads a secret, or
touches a `status:` line; the foundation denylist (`CONSTITUTION.md`, `eval/golden/**`,
`eval/golden.py`) binds beneath every grant regardless of what this returns (invariant 5).

THE THREE-VALUED DOMAIN, and why. Two-valued conjunction is where the vacuous pass lives:
"every glob resolves inside the worktree" is *true* over an empty `write_scope`, and "every
item carries the flag as no" is *true* over a plan with no items. Both are the false-success
shape (`docs/brainstorms/the-false-success-rule.md`): the observable the check consumes is
not causally downstream of the property claimed. So a term that the input did not answer
returns `UNDETERMINED`, and `UNDETERMINED` is **absorbing** under the conjunction —
invariant 7 (*"Ambiguity … always resolves toward halting"*) applied at the gate's mouth.
`conjoin` takes a **keyed mapping and requires the complete term set**, so there is no
overload on which `all(...)` can be vacuously true; overall PASS is unreachable while any
term is not PASS, and a test enumerates all 3**5 = 243 combinations to prove it.

REUSE, not re-derivation. The glob math is `_lib.matches_any` — the *same* matcher
`scope-guard` runs (`.claude/hooks/_lib.py:150-177`). A predicate with its own glob
semantics would bless a scope the guard reads differently; that is a security-relevant
duplication, not a style one. `_lib` is imported here and never edited (plan §9 non-goal 3).

Stdlib only otherwise — no `os`, no `subprocess`, no `core`, no `config`, so there is
structurally no route to an environment variable, a Keychain item or any other secret
(`finding-0207`'s constraint, held by construction; the AST is asserted in
`tests/unit/test_autopilot_eligibility.py`). It never writes: every path is read-only.

--- correction banner (finding-0263) ---

§2.4's P3 reads *"every plan item carries `touches_stored_data: false`"* — a machine-readable
per-item field that DOES NOT EXIST. Measured over `docs/build-plans/*/plan.md`: the plans
carry the flag as prose in at least twenty spellings and the literal string
`touches_stored_data: false` appears in ZERO of them. A P3 built to the note's text therefore
returns PASS on every plan in the repository, including one that rewrites the vector store.

The check implemented here reads the §7 item BODY with a pinned regex and requires the
captured value, normalized, to be exactly `no`. Every hedge — `no (reads the corpus)`,
`reads only` — is a FAIL. An absent or duplicated flag line, and a plan with zero
`### Item ` headings, are UNDETERMINED.

`docs/build-plans/bp-137/plan.md` §6 is the AUTHORITATIVE form until a superseding design
note says otherwise. `dn-autopilot-and-delegated-blessing` is ratified and agent-immutable
(A8), so the correction lives here rather than in the note. Any divergence between §6 and a
future note is a `spec-defect`, never a silent re-interpretation.

P1 and P2 read the plan's DECLARED `write_scope`, which is not the effective allow-set
`scope-guard` enforces: `cmd_scope_check` (`.claude/hooks/_lib.py:464-466`) widens it with
the plan file, the plan's `journal.md` and `docs/findings/**`. Harmless for P2 — findings are
not enforcement surfaces — but the asymmetry is real and is stated rather than dropped.

P4 is a LEXICAL scan with a pinned deny-list over §7's prose, fenced blocks included (a
command in a fence is still a command). It cannot see intent: an external call reached
through a helper, or a `deploy` spelled differently, passes it. It is conservative by
construction and will fire on a plan that merely *mentions* a token — including a non-goal
that promises never to run one. Announced, not elided; plan §11 row 2 rejects tuning it with
prose-context heuristics.

P5 checks the plan's declared bound only. Un-self-extendability is a property of the runtime,
not of the plan text, and is NOT checked here.

--- end correction banner ---
"""

from __future__ import annotations

import argparse
import enum
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Reuse the guard's own matcher and front-matter parser — never re-derive them (plan §2 DRY
# audit; the `scripts/board.py:33-38` idiom).
sys.path.insert(0, str(ROOT / ".claude" / "hooks"))
from _lib import matches_any, parse_front_matter  # type: ignore[import-not-found]  # noqa: E402

_BANNER_START = "--- correction banner (finding-0263) ---"
_BANNER_END = "--- end correction banner ---"


def _correction_banner() -> str:
    """Slice the correction banner out of this module's own docstring.

    Sliced rather than duplicated into a literal so the docstring a builder reads and the
    caveat the owner reads cannot drift (owner DRY rule). It raises rather than returning
    `""` when the markers are gone: a report that silently loses its caveat is precisely the
    false statement §2.4's *"printed in the capsule the owner reads"* makes dangerous.
    """
    doc = __doc__ or ""
    start = doc.find(_BANNER_START)
    end = doc.find(_BANNER_END, start + 1)
    if start == -1 or end == -1:
        raise RuntimeError(
            "the finding-0263 correction banner is missing from the module docstring; "
            "this tool must not report an eligibility verdict without it"
        )
    return doc[start + len(_BANNER_START) : end].strip()


P3_CORRECTION_BANNER = _correction_banner()


class Result(enum.Enum):
    """A predicate's verdict. `UNDETERMINED` means *the input did not answer the question* —
    it is not a weak PASS, and it is absorbing under `conjoin`."""

    PASS = "pass"
    FAIL = "fail"
    UNDETERMINED = "undetermined"


@dataclass(frozen=True)
class Term:
    """One of P1–P5: its verdict plus the evidence a diagnostic line prints."""

    name: str
    result: Result
    evidence: str


#: The complete term set. `conjoin` requires exactly these keys — see its docstring.
TERM_NAMES: tuple[str, ...] = ("P1", "P2", "P3", "P4", "P5")

#: §2.4's P2 forbidden set, verbatim (`dn-autopilot-and-delegated-blessing.md:320`). Broader
#: than the foundation denylist, which binds beneath every grant regardless (invariant 5) and
#: is deliberately NOT re-implemented here.
FORBIDDEN_SCOPE: tuple[str, ...] = (
    "CLAUDE.md",
    ".claude/hooks/**",
    ".claude/settings.json",
    "docs/design-notes/**",
    "eval/**",
)

#: Concrete paths inside the forbidden set, used for the *covering* direction of P2: a scope
#: glob like `.claude/**`, `docs/**` or `**` names no forbidden pattern but reaches one.
FORBIDDEN_WITNESSES: tuple[str, ...] = (
    "CLAUDE.md",
    ".claude/hooks/_lib.py",
    ".claude/hooks/scope-guard.sh",
    ".claude/settings.json",
    "docs/design-notes/agent-workflow.md",
    "eval/golden.py",
    "eval/metrics.py",
)

#: P4's pinned deny-list (plan §7 Item 16), `(label, pattern)`, matched case-insensitively
#: over §7's prose INCLUDING fenced blocks. Conservative by construction: `deploy` also fires
#: on "deployment" and on a non-goal that merely says "this plan never runs `deploy`". That
#: is a stated property, not a bug — plan §11 row 2 rejects prose-context heuristics.
LIVE_STATE_TOKENS: tuple[tuple[str, str], ...] = (
    ("deploy", r"deploy"),
    ("palace lifecycle mutation", r"palace\s+(?:start|stop|restart|up|down)\b"),
    ("keychain read", r"security\s+find-generic-password"),
    ("secret read", r"get_secret"),
    ("aws sdk", r"\bboto3\b"),
    ("aws cli", r"\baws\s"),
    ("network call", r"\bcurl\b"),
    ("shell-out", r"\bsubprocess\b"),
)

_SECTION_7 = re.compile(r"^##[ \t]*7[.)]?[ \t]", re.M)
_ANY_SECTION = re.compile(r"^##[ \t]", re.M)
_ITEM_HEADING = re.compile(r"^###[ \t]+Item[ \t]", re.M)

#: P3's pinned regex (plan §6, the finding-0263 correction). The value is what follows the
#: bolded question on the same line; §7 items in this repo carry it as a bullet.
_FLAG_LINE = re.compile(
    r"^[ \t]*[-*][ \t]*\*\*Touches stored data\?\*\*[ \t]*(?P<value>.*)$", re.M
)

#: The flag line commonly runs on into the next bolded field (57 of the measured 111 plans),
#: so the captured value is truncated at whichever of these appears first.
_TRUNCATE_AT: tuple[str, ...] = ("**Parallelizable?**", "**Depends on:**")

#: The standing caveats carried in the one-line report. The full statements are in
#: `P3_CORRECTION_BANNER`, which `report` writes to stderr; this is the phone-sized pointer.
REPORT_CAVEATS = "P3=finding-0263 form; P4 lexical, blind to intent; P5 plan-side bound only"

_ABSENT = ("", "null", "none", "~")


def _is_absent(value: object) -> bool:
    """`_lib.parse_front_matter` does not interpret scalars, so a YAML `null` arrives as the
    literal string `"null"` (the `scripts/board.py:58-67` observation). Absent, empty and
    `null` are the same thing here: **undetermined**."""
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip().lower() in _ABSENT
    if isinstance(value, (list, tuple)):
        return len(value) == 0
    return False


def write_scope(front_matter: dict[str, object]) -> list[str]:
    """The plan's declared capability, as `_lib.plan_write_scope` reads it.

    ⚑ NOT the effective allow-set `scope-guard` enforces: `cmd_scope_check`
    (`.claude/hooks/_lib.py:464-466`) widens it with the plan file, the plan's `journal.md`
    and `docs/findings/**`. That asymmetry is stated in the report rather than silently
    dropped — it is harmless for P2 (findings are not enforcement surfaces) but it is real.
    """
    raw = front_matter.get("write_scope")
    if isinstance(raw, list):
        return [str(x).strip() for x in raw if str(x).strip()]
    if isinstance(raw, str) and not _is_absent(raw):
        return [raw.strip()]
    return []


def deglue(entry: str) -> tuple[str, bool]:
    """Split a `write_scope` entry from an inline `#` comment glued to it.

    `_lib._scalar` deliberately leaves a `#` intact on an UNQUOTED scalar (`:218-233`), so
    `- eval/metrics.py  # absorbed` reaches the guard as the *glob* `eval/metrics.py  #
    absorbed`, which matches nothing — the `bp-066` / `finding-0085` footgun. Returns the
    intended glob and whether a comment was glued to it.
    """
    idx = entry.find("#")
    if idx == -1:
        return entry.strip(), False
    return entry[:idx].strip(), True


def escapes_root(glob: str) -> bool:
    """True if the glob cannot resolve inside the worktree: absolute, home-relative, a drive
    letter, empty, or a `..` chain that walks above the repo root. Pure string arithmetic —
    no filesystem, no `os`."""
    g = glob.replace("\\", "/").strip()
    if not g:
        return True
    if g.startswith("/") or g.startswith("~"):
        return True
    if re.match(r"^[A-Za-z]:", g):
        return True
    depth = 0
    for seg in g.split("/"):
        if seg in ("", "."):
            continue
        if seg == "..":
            depth -= 1
            if depth < 0:
                return True
        else:
            depth += 1
    return False


def check_p1(scope: list[str]) -> Term:
    """P1 — repo-confined: every `write_scope` glob resolves inside the worktree.

    ⚑ Degenerate input: an empty or absent `write_scope`. "Every glob resolves inside the
    worktree" is **vacuously true** over the empty set, so a two-valued P1 returns PASS for a
    plan that declares no capability at all. That is UNDETERMINED here.
    """
    if not scope:
        return Term(
            "P1",
            Result.UNDETERMINED,
            "write_scope is absent or empty — no capability is declared, so "
            "'every glob resolves inside the worktree' is vacuously true and answers nothing",
        )
    escaping = []
    for entry in scope:
        glob, _ = deglue(entry)
        if escapes_root(glob):
            escaping.append(entry)
    if escaping:
        return Term(
            "P1",
            Result.FAIL,
            "write_scope entries do not resolve inside the worktree: "
            + ", ".join(repr(e) for e in escaping),
        )
    return Term("P1", Result.PASS, f"{len(scope)} globs, all repo-relative and root-confined")


def check_p2(scope: list[str]) -> Term:
    """P2 — record/enforcement-free: `scope ∩ FORBIDDEN_SCOPE = ∅`.

    Checked in **both** glob directions, both through `_lib.matches_any`, because neither
    alone is sufficient: (a) the entry read as a path against the forbidden patterns catches
    `eval/foo.py`; (b) a forbidden witness against the entry read as a pattern catches a
    glob that *covers* a forbidden surface without naming it (`.claude/**`, `docs/**`, `**`).

    ⚑ Degenerate inputs. An empty `write_scope` makes the intersection vacuously empty →
    UNDETERMINED. An entry with a glued inline comment (`finding-0085`) matches nothing, so
    the intersection is *also* vacuously empty even on a scope that names `eval/` → FAIL,
    because the declared capability is not what it reads as.
    """
    if not scope:
        return Term(
            "P2",
            Result.UNDETERMINED,
            "write_scope is absent or empty — 'scope ∩ forbidden = ∅' is vacuously true "
            "over an empty scope and answers nothing",
        )
    hits: list[str] = []
    for entry in scope:
        glob, glued = deglue(entry)
        if glued:
            hits.append(
                f"{entry!r} carries an inline comment glued to the glob (finding-0085 / "
                "bp-066): it matches nothing, so the forbidden-set intersection would be "
                "vacuously empty and the declared scope is not what it reads as"
            )
        if not glob:
            continue
        if matches_any(glob, list(FORBIDDEN_SCOPE)):
            hits.append(f"{glob!r} lies inside the §2.4 forbidden set")
            continue
        covered = [w for w in FORBIDDEN_WITNESSES if matches_any(w, [glob])]
        if covered:
            hits.append(f"{glob!r} covers forbidden surface(s) {', '.join(covered)}")
    if hits:
        return Term("P2", Result.FAIL, "; ".join(hits))
    return Term("P2", Result.PASS, "scope is disjoint from the §2.4 record/enforcement set")


def section_seven(text: str) -> str | None:
    """The plan's §7 body, or None if the plan has no §7 heading."""
    match = _SECTION_7.search(text)
    if match is None:
        return None
    rest = text[match.start() :]
    nxt = _ANY_SECTION.search(rest, 1)
    return rest if nxt is None else rest[: nxt.start()]


def item_bodies(section: str) -> list[str]:
    """The `### Item ` blocks of a §7 body, in order."""
    starts = [m.start() for m in _ITEM_HEADING.finditer(section)]
    bounds = starts + [len(section)]
    return [section[bounds[i] : bounds[i + 1]] for i in range(len(starts))]


def item_label(body: str) -> str:
    """The item's heading line, trimmed, for use in a diagnostic."""
    head = body.splitlines()[0] if body.splitlines() else "### Item ?"
    return head.lstrip("# ").strip()


def normalize_flag(value: str) -> str:
    """P3's normalization, pinned (plan §6).

    Truncate at a run-on bolded field, then strip surrounding emphasis and a trailing period,
    then lowercase. `no`, `No`, `No.`, `**No.**` and `No. **Parallelizable?** yes` all become
    `no`; `No (reads the corpus)` and `Reads only.` do not, and must not — reading the first
    two characters of an English sentence is not a blast-radius decision.
    """
    v = value.strip()
    for marker in _TRUNCATE_AT:
        idx = v.find(marker)
        if idx != -1:
            v = v[:idx]
    return v.strip().strip("*").strip().rstrip(".").strip().lower()


def check_p3(section: str | None) -> Term:
    """P3 — no stored-data blast, as corrected by `finding-0263` (see the module banner).

    ⚑ Degenerate inputs. A plan with zero `### Item ` headings makes "every item carries the
    flag as no" **vacuously true** → UNDETERMINED. And the literal §2.4 reading — grep for
    `touches_stored_data:`, find nothing, see no `true`, return PASS — passes on every plan
    in the repository; it is not implemented here, and a test constructs a plan whose §7 says
    `**Touches stored data?** Yes — rewrites the vector store` and requires FAIL.
    """
    if section is None or not section.strip():
        return Term(
            "P3",
            Result.UNDETERMINED,
            "the plan has no §7 section, so 'every item carries the flag' is vacuous",
        )
    bodies = item_bodies(section)
    if not bodies:
        return Term(
            "P3",
            Result.UNDETERMINED,
            "§7 carries zero '### Item ' headings — 'every item carries the flag as no' is "
            "vacuously true over the empty set and answers nothing",
        )
    fails: list[str] = []
    undetermined: list[str] = []
    for body in bodies:
        label = item_label(body)
        values = [m.group("value") for m in _FLAG_LINE.finditer(body)]
        if len(values) == 0:
            undetermined.append(f"{label}: no '**Touches stored data?**' line")
            continue
        if len(values) > 1:
            undetermined.append(f"{label}: {len(values)} '**Touches stored data?**' lines")
            continue
        normalized = normalize_flag(values[0])
        if normalized != "no":
            fails.append(f"{label}: {values[0].strip()!r} normalizes to {normalized!r}, not 'no'")
    if fails:
        return Term("P3", Result.FAIL, "; ".join(fails))
    if undetermined:
        return Term("P3", Result.UNDETERMINED, "; ".join(undetermined))
    return Term("P3", Result.PASS, f"all {len(bodies)} items carry the flag as exactly 'no'")


def check_p4(section: str | None) -> Term:
    """P4 — no live-state mutation, as a lexical scan that admits what it cannot see.

    §2.4's P4 names "no acceptance step or action runs `deploy`, `palace` lifecycle mutation,
    or any credentialed external call". There is no structured acceptance field on a plan and
    this plan does not invent one (§9 non-goal 2), so this is a token scan over §7's prose
    with `LIVE_STATE_TOKENS` — **fenced blocks included**, because a command in a fence is
    still a command and a fence is exactly where an acceptance step lives.

    ⚑ Degenerate inputs. An absent or empty §7 makes "no acceptance step runs `deploy`"
    vacuously true → UNDETERMINED. And a scanner that skips fences — the natural "ignore
    code" instinct — passes a plan whose acceptance is literally ```mind-palace deploy```;
    fences are deliberately NOT skipped, and a test pins that.
    """
    if section is None or not section.strip():
        return Term(
            "P4",
            Result.UNDETERMINED,
            "the plan has no §7 section, so 'no acceptance step runs deploy' is vacuous",
        )
    if not item_bodies(section):
        return Term(
            "P4",
            Result.UNDETERMINED,
            "§7 carries zero '### Item ' headings — there is no acceptance prose to scan, so "
            "'no acceptance step runs deploy' is vacuously true and answers nothing",
        )
    hits: list[str] = []
    for label, pattern in LIVE_STATE_TOKENS:
        match = re.search(pattern, section, re.I)
        if match is not None:
            hits.append(f"{label} ({match.group(0).strip()!r})")
    if hits:
        return Term(
            "P4",
            Result.FAIL,
            "§7 prose contains live-state token(s): " + ", ".join(hits),
        )
    return Term("P4", Result.PASS, "no live-state token in §7 (lexical scan, fences included)")


def check_p5(front_matter: dict[str, object]) -> Term:
    """P5 — bounded: `session_budget` parses as an integer >= 1.

    A trailing YAML `#` comment is tolerated because `_lib._scalar` leaves one glued to an
    unquoted scalar by design; rejecting legal YAML would enforce a spelling rather than a
    property. `"null"`, empty and absent are the same thing: UNDETERMINED.

    ⚑ Not checked, and said so rather than implied: un-self-extendability is a property of
    the runtime, not of the plan text (plan §11 row 4).
    """
    raw = front_matter.get("session_budget")
    if _is_absent(raw):
        return Term(
            "P5",
            Result.UNDETERMINED,
            "session_budget is absent, empty or null — the run's bound is undeclared",
        )
    match = re.match(r"^(-?\d+)[ \t]*(?:#.*)?$", str(raw).strip())
    if match is None:
        return Term("P5", Result.FAIL, f"session_budget {str(raw).strip()!r} is not an integer")
    budget = int(match.group(1))
    if budget < 1:
        return Term("P5", Result.FAIL, f"session_budget is {budget}, not a finite bound >= 1")
    return Term(
        "P5",
        Result.PASS,
        f"session_budget is {budget} (the plan's declared bound; the runtime half is unchecked)",
    )


def conjoin(results: dict[str, Result]) -> Result:
    """The conjunction, pinned (plan §6): PASS **iff** the term set is exactly `TERM_NAMES`
    and every term is PASS. Everything else — including any `UNDETERMINED` — is FAIL.

    ⚑ The signature is the guard. A `Sequence[Result]` overload would make `all(...)` return
    True over the empty sequence, so a caller that computed nothing would receive PASS; and
    the natural `all(t is not Result.FAIL)` returns PASS when every term is UNDETERMINED,
    i.e. when nothing was determined about anything. Requiring the complete keyed term set
    makes both unreachable rather than merely untested. There is no other conjunction in this
    module and no code path returns overall PASS while any term is not PASS.
    """
    if set(results) != set(TERM_NAMES):
        return Result.FAIL
    return Result.PASS if all(results[n] is Result.PASS for n in TERM_NAMES) else Result.FAIL


@dataclass
class Evaluation:
    """All five terms for one plan, plus the scope they were computed over."""

    terms: dict[str, Term] = field(default_factory=dict)
    scope: list[str] = field(default_factory=list)

    @property
    def overall(self) -> Result:
        return conjoin({name: term.result for name, term in self.terms.items()})


def evaluate(text: str) -> Evaluation:
    """Evaluate P1–P5 over one plan's text. Read-only; nothing here writes a file."""
    front_matter = parse_front_matter(text)
    scope = write_scope(front_matter)
    section = section_seven(text)
    terms = {
        "P1": check_p1(scope),
        "P2": check_p2(scope),
        "P3": check_p3(section),
        "P4": check_p4(section),
        "P5": check_p5(front_matter),
    }
    return Evaluation(terms=terms, scope=scope)


def report_line(evaluation: Evaluation) -> str:
    """The single capsule-ready `achievable:` line (plan §6).

    One line, because seven other fields share the capsule's 40-line / 300-word budget
    (`scripts/capsule.py:62-63`). ⚑ Those caps bound **shape, not bytes** (`finding-0219` /
    `oq-0054`, open with no recorded ruling), so this assumes no character bound exists and
    simply keeps its own output short.

    The marks are rendered from the computed terms, never from a template, so the line for a
    FAIL plan differs from the line for a PASS plan in exactly the term positions. The
    caveats are standing — they hold for every plan — so §6's `"no caveats"` alternative is
    never taken; that is stated here rather than left as a surprising absence.
    """
    marks = " ".join(
        f"{name} {evaluation.terms[name].result.value}" + ("(lexical)" if name == "P4" else "")
        for name in TERM_NAMES
    )
    return f"achievable: {len(evaluation.scope)} globs; {marks}; {REPORT_CAVEATS}"


def diagnostics(evaluation: Evaluation) -> list[str]:
    """One line per non-PASS term, in term order: predicate, result, evidence."""
    return [
        f"{name} {evaluation.terms[name].result.value}: {evaluation.terms[name].evidence}"
        for name in TERM_NAMES
        if evaluation.terms[name].result is not Result.PASS
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="autopilot_eligibility.py",
        description="§2.4's P1-P5 autopilot-eligibility predicate over a build plan.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name, help_text in (
        ("check", "exit 0 iff all five predicates PASS; else one diagnostic line per term"),
        ("report", "print the capsule-ready one-line `achievable:` block"),
    ):
        cmd = sub.add_parser(name, help=help_text)
        cmd.add_argument("plan", help="path to a build plan's plan.md")
    args = parser.parse_args(argv)

    try:
        text = Path(args.plan).read_text(encoding="utf-8")
    except OSError as exc:
        print(f"error: cannot read {args.plan}: {exc}", file=sys.stderr)
        return 1

    evaluation = evaluate(text)
    if args.cmd == "report":
        print(report_line(evaluation))
        for line in P3_CORRECTION_BANNER.splitlines():
            print(f"# {line}" if line.strip() else "#", file=sys.stderr)
    else:
        for line in diagnostics(evaluation):
            print(line)
    return 0 if evaluation.overall is Result.PASS else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
