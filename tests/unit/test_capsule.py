"""The INTENT capsule as a typed artifact with a stable hash — bp-120 Items 1-4.

Four properties, one file, each test named for the criterion or falsifier it encodes:

  * Item 1 — the TEMPLATE (`docs/templates/intent-capsule.md`) carries all eight fields, is
    well-formed, and `validate` reports ONLY empty-field violations against it. Its falsifier
    ("the empty template already exceeds a cap", which would mean the note's <= 40-line rule is
    wrong rather than the template) is drilled directly.
  * Item 2 — the CANONICAL FORM and the hash: CRLF/LF and trailing-whitespace variants collapse
    to one digest; a one-character change inside a field moves it (the falsifier: canonicalization
    lossy beyond trailing whitespace); invalid UTF-8 raises rather than substituting.
  * Item 3 — VALIDATE: a missing field, an empty field, 41 lines, and 301 words each produce a
    naming diagnostic and a non-zero exit; the caps are hard errors, never warnings.
  * Item 4 — CHECK-EMBEDDING, in BOTH directions. The falsifier is the load-bearing one: a plan
    that ADDS a non-goal the capsule does not carry must FAIL, because "the plan may not exceed
    the capsule" (note §2.2) is exactly what Gate A audits.

Plus the tooling invariant (the `exhaust_report.py` AST precedent): stdlib only, no `core`, no
`config`, and — `docs/findings/finding-0207.md` — no `os`/`subprocess`, so the tool structurally
cannot reach an environment variable, a Keychain item, or any other secret.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

import capsule  # type: ignore[import-not-found]  # noqa: E402

TEMPLATE = REPO / "docs" / "templates" / "intent-capsule.md"

# A realistic filled capsule for the owner's own named use case (the spell-check class,
# dn-autopilot-and-delegated-blessing §1.1) — the fixture the "well-formed" cases use.
GOOD = """\
<!-- The INTENT capsule (dn-autopilot-and-delegated-blessing §2.2) — the SMART readback a
grant binds to. NOT docs/templates/capsule.md (the brainstorm SESSION capsule). -->

goal: Add spell-check to markdown buffers in the owner's nvim config, on by default.
definition-of-done: `:set spell?` reports `spell` in a markdown buffer and a deliberate
  misspelling renders underlined.
achievable: write_scope is one plugin file; P1-P5 all pass; no open decisions.
relevant: design-inert — changes no designed contract, boundary, or behaviour.
time-bound: 60k tokens, base commit 7941da1, TTL 72h.
falsifier: spell-check fires inside fenced code blocks, making every identifier an error.
non-goals:
  - No spell-check for filetypes other than markdown.
  - No custom dictionary and no repo-committed wordlist.
readback: "Yes — markdown spell-check on by default, nothing else touched."
"""

# A plan that embeds GOOD's goal in §1 and its non-goals in §9, verbatim. The second non-goal
# is deliberately WRAPPED across two lines, so the fixture also proves the fold.
PLAN = """\
---
type: build-plan
id: bp-999
status: proposed
---

# Build Plan — markdown spell-check

## 1. Objective

Add spell-check to markdown buffers in the owner's nvim config, on by default.

## 9. Non-goals

Explicitly NOT in this plan, so a builder does not helpfully overreach:

1. No spell-check for filetypes other than markdown.
2. No custom dictionary and no repo-committed
   wordlist.

## 10. Stop-and-raise conditions

None beyond the standing set.
"""


def _b(text: str) -> bytes:
    return text.encode("utf-8")


def _write(tmp_path: Path, name: str, text: str) -> Path:
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


# ------------------------------------------------------------------------------------------
# Item 1 — the template
# ------------------------------------------------------------------------------------------


def test_template_exists_and_is_well_formed_markdown() -> None:
    """It exists, decodes as UTF-8, its HTML comment is terminated, and it opens no code fence
    it does not close — the mechanically checkable reading of "parses as Markdown"."""
    text = capsule.canonical_text(TEMPLATE.read_bytes())
    assert text.count("<!--") == text.count("-->") == 1
    assert text.count("```") % 2 == 0


def test_template_carries_all_eight_capsule_fields() -> None:
    """The eight §2.2 / bp-120 §6 fields, present as labels the parser actually finds."""
    fields = capsule.parse_capsule(capsule.canonical_text(TEMPLATE.read_bytes()))
    assert set(capsule.REQUIRED_FIELDS) <= set(fields)
    assert len(capsule.REQUIRED_FIELDS) == 8


def test_template_names_the_collision_with_the_session_capsule() -> None:
    """The §4 disambiguation is IN the new file (`capsule.md` is out of write_scope and stays
    untouched), so a builder told "the capsule template" cannot reach for the wrong one."""
    text = TEMPLATE.read_text(encoding="utf-8")
    assert "docs/templates/capsule.md" in text
    assert "SESSION capsule" in text


def test_template_reports_only_empty_field_violations() -> None:
    """Item 1's acceptance: the empty template is STRUCTURALLY valid and fails only for want of
    content — every diagnostic is an empty-field one, and there are exactly eight."""
    diagnostics = capsule.validate(TEMPLATE.read_bytes())
    assert diagnostics, "an unfilled template must not validate — a placeholder is not content"
    assert all(d.startswith("field:") and " is empty" in d for d in diagnostics), diagnostics
    assert len(diagnostics) == len(capsule.REQUIRED_FIELDS)


def test_template_falsifier_the_empty_template_fits_both_caps() -> None:
    """Item 1's FALSIFIER, drilled: if the empty template already exceeded a cap, the caps could
    not hold a real capsule and the note's <= 40-line rule would be wrong rather than the
    template. It does not fire — and the assertions record the HEADROOM left for content, which
    is the number that actually matters."""
    text = capsule.canonical_text(TEMPLATE.read_bytes())
    lines, words = capsule.line_count(text), capsule.word_count(text)
    assert lines <= capsule.LINE_CAP and words <= capsule.WORD_CAP, (lines, words)
    assert capsule.LINE_CAP - lines >= 15, f"only {capsule.LINE_CAP - lines} lines of headroom"
    assert capsule.WORD_CAP - words >= 100, f"only {capsule.WORD_CAP - words} words of headroom"


def test_a_realistic_filled_capsule_fits_the_caps_and_validates() -> None:
    """Item 3's falsifier, approached from the only angle a test can reach: a genuine capsule for
    the owner's own named ask (spell-check) both validates and stays a phone-sized read. A
    lines+words proxy that could not hold this would be measuring the wrong thing."""
    assert capsule.validate(_b(GOOD)) == []
    text = capsule.canonical_text(_b(GOOD))
    assert capsule.line_count(text) <= capsule.LINE_CAP
    assert capsule.word_count(text) <= capsule.WORD_CAP


# ------------------------------------------------------------------------------------------
# Item 2 — the canonical form and the stable hash
# ------------------------------------------------------------------------------------------


def test_digest_is_64_lowercase_hex_chars() -> None:
    digest = capsule.capsule_hash(_b(GOOD))
    assert len(digest) == 64
    assert all(c in "0123456789abcdef" for c in digest)


def test_crlf_and_cr_and_lf_hash_equal() -> None:
    """Step 2 of the canonical form: a CRLF introduced by the phone must not void a valid
    grant."""
    lf = capsule.capsule_hash(_b(GOOD))
    assert capsule.capsule_hash(_b(GOOD.replace("\n", "\r\n"))) == lf
    assert capsule.capsule_hash(_b(GOOD.replace("\n", "\r"))) == lf


def test_trailing_whitespace_variants_hash_equal() -> None:
    """Steps 3 and 4: trailing spaces/tabs per line, and trailing blank lines, are outside the
    hash — nor does a missing final newline change it."""
    lf = capsule.capsule_hash(_b(GOOD))
    assert capsule.capsule_hash(_b(GOOD.replace("\n", "   \n"))) == lf
    assert capsule.capsule_hash(_b(GOOD.replace("\n", "\t\n"))) == lf
    assert capsule.capsule_hash(_b(GOOD + "\n\n\n")) == lf
    assert capsule.capsule_hash(_b(GOOD.rstrip("\n"))) == lf


def test_canonical_form_is_idempotent_and_normally_shaped() -> None:
    """`canonical(canonical(x)) == canonical(x)`: the phone and the verifier cannot disagree by
    applying it a different number of times. And the shape is the one §6 specifies."""
    once = capsule.canonical(_b(GOOD.replace("\n", "  \r\n") + "\n\n"))
    assert capsule.canonical(once) == once
    text = once.decode("utf-8")
    assert text.endswith("\n") and not text.endswith("\n\n")
    assert not any(line != line.rstrip(" \t") for line in text.split("\n"))


@pytest.mark.parametrize(
    "field, before, after",
    [
        ("goal", "on by default", "on by request"),
        ("definition-of-done", "underlined", "underlmned"),
        ("achievable", "P1-P5 all pass", "P1-P5 all fail"),
        ("relevant", "design-inert", "design-heavy"),
        ("time-bound", "TTL 72h", "TTL 72d"),
        ("falsifier", "an error", "an errof"),
        ("non-goals", "other than markdown", "other than mardkown"),
        ("readback", "nothing else touched", "nothing else touchea"),
    ],
)
def test_item2_falsifier_a_meaning_change_in_any_field_moves_the_hash(
    field: str, before: str, after: str
) -> None:
    """Item 2's FALSIFIER, drilled per field as the plan directs: mutate a non-whitespace
    character inside a field and assert the hash MOVES. If any pair collided, canonicalization
    would be lossy beyond trailing whitespace and §6's trade would be wrong as specified."""
    assert before in GOOD, f"fixture drifted — {field!r} no longer contains {before!r}"
    mutated = GOOD.replace(before, after)
    assert mutated != GOOD
    assert capsule.capsule_hash(_b(mutated)) != capsule.capsule_hash(_b(GOOD))


def test_invalid_utf8_raises_rather_than_substituting() -> None:
    """A capsule whose bytes do not decode has no canonical form: substituting U+FFFD would
    silently change the text the owner read into a text that hashes."""
    with pytest.raises(UnicodeDecodeError):
        capsule.canonical(b"goal: caf\xe9 (latin-1, not utf-8)\n")
    with pytest.raises(UnicodeDecodeError):
        capsule.capsule_hash(b"\xff\xfe\x00garbage\n")


def test_cli_hash_prints_the_digest(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = _write(tmp_path, "c.md", GOOD)
    assert capsule.main(["hash", str(path)]) == 0
    assert capsys.readouterr().out.strip() == capsule.capsule_hash(_b(GOOD))


def test_cli_reports_a_missing_file_and_bad_utf8_without_a_traceback(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert capsule.main(["hash", str(tmp_path / "nope.md")]) == 1
    assert "error:" in capsys.readouterr().err
    bad = tmp_path / "bad.md"
    bad.write_bytes(b"goal: caf\xe9\n")
    assert capsule.main(["validate", str(bad)]) == 1
    assert "not valid UTF-8" in capsys.readouterr().err


# ------------------------------------------------------------------------------------------
# Item 3 — validate: required fields and both caps
# ------------------------------------------------------------------------------------------


def test_validate_accepts_a_well_formed_capsule(tmp_path: Path) -> None:
    assert capsule.validate(_b(GOOD)) == []
    assert capsule.main(["validate", str(_write(tmp_path, "c.md", GOOD))]) == 0


@pytest.mark.parametrize("field", capsule.REQUIRED_FIELDS)
def test_validate_names_a_missing_field(field: str) -> None:
    """Drop each required field in turn; the diagnostic must NAME it (bp-120 §6 CLI surface)."""
    kept = [line for line in GOOD.split("\n") if not line.startswith(f"{field}:")]
    if field == "non-goals":  # its bullets would otherwise fold into the previous field
        kept = [line for line in kept if not line.strip().startswith("- No ")]
    diagnostics = capsule.validate(_b("\n".join(kept)))
    assert any(d == f"field: `{field}` is missing" for d in diagnostics), diagnostics


@pytest.mark.parametrize("field", capsule.REQUIRED_FIELDS)
def test_validate_names_an_empty_field(field: str) -> None:
    """A field present but unfilled — including one left as a bare `<placeholder>`, which is
    want of content, not content."""
    blanked: list[str] = []
    for line in GOOD.split("\n"):
        if line.startswith(f"{field}:"):
            blanked.append(f"{field}: <still to fill>")
        elif field == "non-goals" and line.strip().startswith("- No "):
            continue
        elif blanked and blanked[-1].startswith(f"{field}: <") and line.startswith("  "):
            continue  # drop the removed field's continuation lines
        else:
            blanked.append(line)
    diagnostics = capsule.validate(_b("\n".join(blanked)))
    assert any(d.startswith(f"field: `{field}` is empty") for d in diagnostics), diagnostics


def test_validate_names_the_line_cap_at_41_lines(tmp_path: Path) -> None:
    """41 lines is one over; the cap is inclusive at 40 (bp-120 §6)."""
    base = capsule.line_count(capsule.canonical_text(_b(GOOD)))
    at_cap = GOOD.rstrip("\n") + "\n" + "\n".join(["x"] * (40 - base)) + "\n"
    assert capsule.line_count(capsule.canonical_text(_b(at_cap))) == 40
    assert not any(d.startswith("cap:") for d in capsule.validate(_b(at_cap)))

    over = GOOD.rstrip("\n") + "\n" + "\n".join(["x"] * (41 - base)) + "\n"
    assert capsule.line_count(capsule.canonical_text(_b(over))) == 41
    diagnostics = capsule.validate(_b(over))
    assert "cap: 41 lines exceeds the 40-line cap" in diagnostics, diagnostics
    assert capsule.main(["validate", str(_write(tmp_path, "c.md", over))]) == 1


def test_validate_names_the_word_cap_at_301_words(tmp_path: Path) -> None:
    """301 words is one over; the cap is inclusive at 300. Padded on ONE line so the line cap
    cannot be what fires — each cap is proved independently."""
    base = capsule.word_count(capsule.canonical_text(_b(GOOD)))
    at_cap = GOOD.rstrip("\n") + "\nrelevant-note: " + "w " * (300 - base - 1) + "\n"
    assert capsule.word_count(capsule.canonical_text(_b(at_cap))) == 300
    assert not any(d.startswith("cap:") for d in capsule.validate(_b(at_cap)))

    over = GOOD.rstrip("\n") + "\nrelevant-note: " + "w " * (301 - base - 1) + "\n"
    assert capsule.word_count(capsule.canonical_text(_b(over))) == 301
    diagnostics = capsule.validate(_b(over))
    assert "cap: 301 words exceeds the 300-word cap" in diagnostics, diagnostics
    assert capsule.main(["validate", str(_write(tmp_path, "c.md", over))]) == 1


def test_item3_falsifier_the_caps_do_not_bound_characters_finding_0219() -> None:
    """Item 3's FALSIFIER, and it FIRES — recorded here rather than hidden.

    A capsule with all eight fields filled plus 30 lines of seven 180-character tokens measures
    39 lines and 227 words — inside both caps — and is 38 KB. `validate` passes it, so
    `<= 40 lines / <= 300 words` bounds SHAPE, not the size of the read that
    dn-autopilot-and-delegated-blessing §2.2 says the cap exists to protect. lines x words has
    no character bound because a "word" has no maximum length.

    NOT fixed here, deliberately: bp-120 §6 pins these two counts exactly and §11 row 3 pins
    them as non-configurable, so adding a third cap changes a pinned interface — a design act.
    Filed as `docs/findings/finding-0219.md` (spec-defect -> orchestrator) with candidate
    resolutions. **When the owner rules and a character or token cap lands, this test flips to
    failing — that is the point: update it and the finding together.**
    """
    filled = "".join(f"{name}: filled\n" for name in capsule.REQUIRED_FIELDS if name != "non-goals")
    filled += "non-goals:\n  - none.\n"
    padded = filled + "".join(("W" * 180 + " ") * 7 + "\n" for _ in range(30))
    text = capsule.canonical_text(_b(padded))

    assert capsule.line_count(text) <= capsule.LINE_CAP
    assert capsule.word_count(text) <= capsule.WORD_CAP
    assert len(text) > 30_000, "fixture drifted — it must be far too large to read on a phone"
    assert capsule.validate(_b(padded)) == [], "finding-0219: the caps admit an enormous capsule"


def test_the_caps_are_hard_errors_not_warnings() -> None:
    """§2.2's cap exists to protect the owner's read, and a warning does not protect a read: an
    over-cap capsule whose eight fields are all filled must STILL be rejected."""
    over = GOOD.rstrip("\n") + "\n" + "\n".join(["padding"] * 40) + "\n"
    diagnostics = capsule.validate(_b(over))
    assert diagnostics
    assert all(d.startswith("cap:") for d in diagnostics), diagnostics


# ------------------------------------------------------------------------------------------
# Item 4 — check-embedding: the capsule is in the plan verbatim
# ------------------------------------------------------------------------------------------


def test_embedding_passes_when_the_plan_carries_the_capsule_verbatim(tmp_path: Path) -> None:
    """Including the wrapped second non-goal: a plan may re-wrap, it may not re-word."""
    assert capsule.check_embedding(_b(GOOD), _b(PLAN)) == []
    capsule_path = _write(tmp_path, "c.md", GOOD)
    plan_path = _write(tmp_path, "p.md", PLAN)
    assert capsule.main(["check-embedding", str(capsule_path), str(plan_path)]) == 0


def test_embedding_fails_when_one_word_of_the_goal_is_altered() -> None:
    altered = PLAN.replace("on by default", "on by request")
    diagnostics = capsule.check_embedding(_b(GOOD), _b(altered))
    assert diagnostics and diagnostics[0].startswith("goal:"), diagnostics


def test_embedding_fails_when_a_non_goal_is_dropped() -> None:
    dropped = PLAN.replace("2. No custom dictionary and no repo-committed\n   wordlist.\n", "")
    diagnostics = capsule.check_embedding(_b(GOOD), _b(dropped))
    assert any("missing from plan §9" in d for d in diagnostics), diagnostics


def test_item4_falsifier_the_plan_may_not_exceed_the_capsule() -> None:
    """Item 4's FALSIFIER, and the load-bearing direction: a plan that ADDS a non-goal the
    capsule does not carry MUST fail. If it passed, the check would be testing containment the
    wrong way round and would hand Gate A false assurance on exactly the property §2.2 says it
    audits — "the plan may elaborate execution; it may not exceed the capsule"."""
    added = PLAN.replace(
        "   wordlist.\n", "   wordlist.\n3. No support for the Neovim 0.9 line.\n"
    )
    diagnostics = capsule.check_embedding(_b(GOOD), _b(added))
    assert any("exceeds the capsule" in d for d in diagnostics), diagnostics


def test_embedding_reports_an_unfilled_capsule_rather_than_guessing() -> None:
    """Run against the empty template: the answer is "validate first", not a comparison against
    a placeholder."""
    diagnostics = capsule.check_embedding(TEMPLATE.read_bytes(), _b(PLAN))
    assert any(d.startswith("capsule:") for d in diagnostics), diagnostics


def test_embedding_reports_a_plan_missing_the_sections_it_embeds_into() -> None:
    stub = "---\nid: bp-999\n---\n\n# Build Plan\n\n## 2. Context manifest\n\nnothing.\n"
    diagnostics = capsule.check_embedding(_b(GOOD), _b(stub))
    assert any("no `## 1.` section" in d for d in diagnostics), diagnostics
    assert any("no `## 9.` section" in d for d in diagnostics), diagnostics


def test_plan_section_ignores_commented_out_bullets() -> None:
    """The build-plan TEMPLATE's §9 is nothing but an HTML comment; a comment is guidance, not a
    non-goal, and must not read as one."""
    commented = PLAN.replace(
        "1. No spell-check for filetypes other than markdown.",
        "<!-- 1. No spell-check for filetypes other than markdown. -->",
    )
    diagnostics = capsule.check_embedding(_b(GOOD), _b(commented))
    assert any("missing from plan §9" in d for d in diagnostics), diagnostics


# ------------------------------------------------------------------------------------------
# The tooling invariant — stdlib only, and structurally secret-free (finding-0207)
# ------------------------------------------------------------------------------------------


def test_capsule_tool_imports_stdlib_only_and_cannot_reach_a_secret() -> None:
    """The `exhaust_report.py` AST precedent, tightened. bp-120 Item 2's invariant is "stdlib
    only; reads no secret, no environment, no config" — proved structurally: absent `os` and
    `subprocess` there is no route to an environment variable, the `security` CLI, or any other
    secret path, so finding-0207's constraint holds by construction rather than by convention."""
    tree = ast.parse((REPO / "scripts" / "capsule.py").read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name.split(".")[0])

    allowed = {"__future__", "argparse", "hashlib", "re", "sys", "dataclasses", "pathlib"}
    assert imported <= allowed, f"unexpected imports: {imported - allowed}"
    for forbidden in ("core", "config", "os", "subprocess", "keyring", "hmac"):
        assert forbidden not in imported, f"the capsule tool must never import {forbidden}"


def test_capsule_tool_never_writes(tmp_path: Path) -> None:
    """`check-embedding` READS a plan: it must never edit one, and in particular never touch
    `status:` — gate-guard would deny it, and a tool that tried has misunderstood its job."""
    source = (REPO / "scripts" / "capsule.py").read_text(encoding="utf-8")
    for writer in ("write_text", "write_bytes", "open(", "unlink", "rename", "mkdir"):
        assert writer not in source, f"the capsule tool must not call {writer}"

    plan = _write(tmp_path, "p.md", PLAN)
    before = plan.read_bytes()
    capsule.main(["check-embedding", str(_write(tmp_path, "c.md", GOOD)), str(plan)])
    assert plan.read_bytes() == before
