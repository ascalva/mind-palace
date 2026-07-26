#!/usr/bin/env python
"""The INTENT capsule as a typed artifact with a stable hash (bp-120).

The capsule is the SMART readback a remote `proposed -> ready` grant binds to
(`docs/design-notes/dn-autopilot-and-delegated-blessing.md` §2.2/§2.3), so that a grant
authorizes **a text** rather than an occasion. Template: `docs/templates/intent-capsule.md`.
⚑ NOT `docs/templates/capsule.md`, which is the unrelated brainstorm SESSION capsule
(chat-side protocol §8) — different artifact, different lifecycle, no shared machinery.

    uv run scripts/capsule.py hash <capsule-file>
      -> prints the 64-char lowercase hex digest, exit 0
    uv run scripts/capsule.py validate <capsule-file>
      -> exit 0 if every required field is present and non-empty AND both caps hold;
         exit 1 with one diagnostic line per violation, naming the field or the cap
    uv run scripts/capsule.py check-embedding <capsule-file> <plan-file>
      -> exit 0 iff the plan's §1 and §9 carry the capsule's goal and non-goals verbatim
         (canonical comparison); exit 1 naming the divergences, first one first

CANONICAL FORM (defined by `docs/build-plans/bp-120/plan.md` §6 — the ratified note says
`sha256(capsule)` but leaves the canonical form open, so bp-120 §6 is authoritative until a
superseding note says otherwise; a divergence between the two is a `spec-defect`, never a
silent re-interpretation). `canonical(bytes) -> bytes` is:

  1. decode UTF-8, STRICT — invalid input raises, never a silent replacement character;
  2. normalize line endings `\\r\\n` and `\\r` -> `\\n`;
  3. strip trailing horizontal whitespace (space, tab) from every line;
  4. strip trailing blank lines, then append exactly one `\\n`;
  5. re-encode UTF-8.

`capsule_hash = sha256(canonical(raw)).hexdigest()`. The equivalence class is therefore
exactly "differs only in trailing whitespace and line endings", which cannot change meaning:
invariant 3's *"byte-identical"* is implemented as **canonically identical**, a deliberate and
bounded weakening (bp-120 §6) that keeps a CRLF introduced by the phone from silently voiding
a valid grant. Degenerate case, stated so it is not a surprise: an all-blank file canonicalizes
to a lone `"\\n"` — step 4 read literally — and so hashes equal to the empty file. `validate`
rejects it for want of every field.

COUNTING, pinned (bp-120 §6, so two implementations cannot disagree): a *word* is a maximal
run of non-whitespace characters in the canonical text, counted over the whole file including
field labels and comments; *lines* is the number of `\\n`-separated lines in the canonical
text. Caps: <= 40 lines and <= 300 words, both inclusive, both HARD ERRORS — never warnings,
because §2.2's cap exists to protect the owner's read and a warning does not protect a read.
The caps are hard-coded on purpose (bp-120 §11): a cap the run can raise is not a cap.

Repo-workflow tooling (the `exhaust_report.py` / `docket.py` precedent), and here the tightest
form of it: **stdlib only** — not even `config`, since nothing here needs configuration. It
imports no `os` and no `subprocess`, so it structurally cannot read an environment variable, a
Keychain item, or any other secret — `docs/findings/finding-0207.md` forbids this plan from
touching a secret path, and `tests/unit/test_capsule.py` asserts the import set. It also never
writes: `check-embedding` READS a plan and in particular never touches its `status:` line.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from dataclasses import dataclass
from pathlib import Path

LINE_CAP = 40
WORD_CAP = 300

#: The eight capsule fields (bp-120 §6, copied from the note's §2.2 table) in SMART order:
#: Specific, Measurable, Achievable, Relevant, Time-bound, then the three fields SMART lacks
#: (named falsifier, explicit non-goals, the readback close). All eight are required.
REQUIRED_FIELDS: tuple[str, ...] = (
    "goal",
    "definition-of-done",
    "achievable",
    "relevant",
    "time-bound",
    "falsifier",
    "non-goals",
    "readback",
)

#: `non-goals` is the one list-valued field; the rest are scalars.
LIST_FIELDS: frozenset[str] = frozenset({"non-goals"})

_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
_PLACEHOLDER = re.compile(r"<[^<>]*>")
_FIELD = re.compile(r"^([A-Za-z][A-Za-z0-9-]*):[ \t]*(.*)$")
_BULLET = re.compile(r"^(?:[-*]|\d+[.)])[ \t]+(.*)$")
_HEADING = re.compile(r"^##[ \t]+(\d+)\.")


# ------------------------------------------------------------------------------------------
# Item 2 — the canonical form and the stable hash
# ------------------------------------------------------------------------------------------


def canonical_text(raw: bytes) -> str:
    """The canonical text of `raw` per bp-120 §6. Raises `UnicodeDecodeError` on invalid
    UTF-8 — a capsule whose bytes do not decode has no canonical form, and substituting a
    replacement character would change the text the owner read."""
    text = raw.decode("utf-8")  # strict by default — no errors= argument, deliberately
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip(" \t") for line in text.split("\n")]
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines) + "\n"


def canonical(raw: bytes) -> bytes:
    """`canonical(bytes) -> bytes`, the object that is hashed (bp-120 §6)."""
    return canonical_text(raw).encode("utf-8")


def capsule_hash(raw: bytes) -> str:
    """`sha256(canonical(raw))` as 64 lowercase hex characters — the binding commitment a
    grant is issued against (note §2.3: the code is `f(secret, artifact-hash)`)."""
    return hashlib.sha256(canonical(raw)).hexdigest()


def line_count(text: str) -> int:
    """Lines of canonical `text` — `\\n`-separated (bp-120 §6). Canonical text always ends
    with exactly one `\\n` and holds no trailing blank line, so counting terminators counts
    lines."""
    return text.count("\n")


def word_count(text: str) -> int:
    """Words of canonical `text` — maximal runs of non-whitespace (bp-120 §6)."""
    return len(text.split())


# ------------------------------------------------------------------------------------------
# Item 3 — parsing and validation
# ------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Field:
    """One parsed capsule field. `value` is the scalar text (empty for a list field);
    `items` are the bullet items (empty for a scalar field); `line` is the 1-based line the
    label sat on, for diagnostics."""

    name: str
    value: str
    items: tuple[str, ...]
    line: int

    @property
    def is_empty(self) -> bool:
        """A field is EMPTY when it carries no content beyond `<...>` placeholders. An
        unreplaced placeholder is *want of content*, not content: this is what lets the empty
        template be structurally valid while still failing validation, and it stops a capsule
        with a forgotten field from ever reaching a grant.

        A list field with no items is empty — `all(())` is True — because `check-embedding`
        compares items, so a `non-goals:` answered as prose has not answered it."""
        if self.name in LIST_FIELDS:
            return all(_is_blank(item) for item in self.items)
        if self.items:
            return _is_blank(self.value) and all(_is_blank(item) for item in self.items)
        return _is_blank(self.value)


def _is_blank(value: str) -> bool:
    """True when `value` holds nothing but whitespace and `<...>` placeholders."""
    return not _PLACEHOLDER.sub(" ", value).strip()


def _blank_comments(text: str) -> str:
    """Replace every HTML comment with its own newlines, so comment text is invisible to the
    field parser while every following line keeps its number. Comments still count toward the
    caps and the hash — those are whole-file properties (bp-120 §6)."""
    return _COMMENT.sub(lambda m: "\n" * m.group(0).count("\n"), text)


def parse_capsule(text: str) -> dict[str, Field]:
    """Parse canonical capsule `text` into its fields.

    The format (defined here, since bp-120 §6 pins the field set and the counting rules but
    not a serialization): a field label is `name:` at column 0; the rest of that line is the
    scalar value; bullet lines (`- `, `* `, `1. `) are list items; **any other non-blank,
    non-heading line continues the current field**. That last rule is deliberate — the capsule
    is the hashed authority, so a wrapped line must never be silently dropped from the value
    the embedding check compares. HTML comments are ignored. Unknown labels are ignored rather
    than rejected: `validate`'s contract is that the eight REQUIRED_FIELDS are present and
    non-empty, not that nothing else may be said.
    """
    scalars: dict[str, list[str]] = {}
    items: dict[str, list[str]] = {}
    first_line: dict[str, int] = {}
    current: str | None = None

    for lineno, line in enumerate(_blank_comments(text).split("\n"), start=1):
        stripped = line.strip()
        label = _FIELD.match(line)
        if label:
            current = label.group(1)
            scalars.setdefault(current, [])
            items.setdefault(current, [])
            first_line.setdefault(current, lineno)
            rest = label.group(2).strip()
            if rest:
                scalars[current].append(rest)
            continue
        if current is None or not stripped or stripped.startswith("#"):
            continue
        bullet = _BULLET.match(stripped)
        if bullet:
            items[current].append(bullet.group(1).strip())
        else:
            # a continuation extends the most recent item, else the scalar
            (items[current] if items[current] else scalars[current]).append(stripped)

    return {
        name: Field(
            name=name,
            value=" ".join(scalars[name]),
            items=tuple(items[name]),
            line=first_line[name],
        )
        for name in scalars
    }


def validate(raw: bytes) -> list[str]:
    """Diagnostics for capsule `raw` — empty means valid. One line per violation, each naming
    the cap or the field it is about (bp-120 §6 CLI surface). Caps are hard errors."""
    text = canonical_text(raw)
    diagnostics: list[str] = []

    lines, words = line_count(text), word_count(text)
    if lines > LINE_CAP:
        diagnostics.append(f"cap: {lines} lines exceeds the {LINE_CAP}-line cap")
    if words > WORD_CAP:
        diagnostics.append(f"cap: {words} words exceeds the {WORD_CAP}-word cap")

    fields = parse_capsule(text)
    for name in REQUIRED_FIELDS:
        field = fields.get(name)
        if field is None:
            diagnostics.append(f"field: `{name}` is missing")
        elif field.is_empty:
            want = " — expected at least one filled `- ` item" if name in LIST_FIELDS else ""
            diagnostics.append(f"field: `{name}` is empty (line {field.line}){want}")
    return diagnostics


# ------------------------------------------------------------------------------------------
# Item 4 — the verbatim-embedding check (note invariant 3)
# ------------------------------------------------------------------------------------------


def _norm(text: str) -> str:
    """Comparison form: canonical text with internal whitespace runs collapsed, so a goal
    wrapped across two lines in a plan compares equal to the same goal on one line in a
    capsule. Nothing else is normalized — no case folding, no punctuation stripping — so a
    single altered word still diverges (bp-120 §11: raw Markdown under §6 canonicalization,
    deliberately strict; a Markdown renderer would make the check depend on renderer
    version)."""
    return " ".join(text.split())


def plan_section(plan_text: str, number: int) -> str | None:
    """The body of the plan's `## <number>. ...` section, or None if absent. Ends at the next
    `## ` heading. Read-only: this function never writes a plan, and in particular never
    touches `status:` — a tool that tried has misunderstood its job (bp-120 Item 4)."""
    body: list[str] | None = None
    for line in _blank_comments(plan_text).split("\n"):
        heading = _HEADING.match(line)
        if heading:
            if body is not None:
                break
            if int(heading.group(1)) == number:
                body = []
            continue
        if body is not None:
            body.append(line)
    return "\n".join(body) if body is not None else None


def _bullets(section: str) -> list[str]:
    """The list items of a plan section, one string each, INDENTED continuation lines folded
    in. Indentation is required here — unlike the capsule parser, which folds any wrapped line
    — because a plan section legitimately ends in a column-0 closing paragraph, and folding
    that into the last item would manufacture a divergence. The asymmetry is intentional: on
    the capsule side never drop content, on the plan side follow Markdown convention."""
    found: list[str] = []
    for line in section.split("\n"):
        stripped = line.strip()
        bullet = _BULLET.match(stripped)
        if bullet:
            found.append(bullet.group(1).strip())
        elif found and stripped and line[:1] in (" ", "\t"):
            found[-1] = f"{found[-1]} {stripped}"
    return found


def check_embedding(capsule_raw: bytes, plan_raw: bytes) -> list[str]:
    """Diagnostics for "the plan embeds the capsule verbatim" — empty means it does.

    Checks note invariant 3 in BOTH directions, which is the point: the plan may elaborate
    execution but *may not exceed the capsule* (§2.2), so a non-goal present in the plan and
    absent from the capsule is a violation exactly as much as a dropped one. Containment in
    one direction only would give Gate A false assurance (bp-120 Item 4 falsifier).
    """
    capsule_text = canonical_text(capsule_raw)
    plan_text = canonical_text(plan_raw)
    fields = parse_capsule(capsule_text)
    diagnostics: list[str] = []

    goal = fields.get("goal")
    if goal is None or goal.is_empty:
        diagnostics.append("capsule: `goal` is missing or empty — run `validate` first")
    else:
        objective = plan_section(plan_text, 1)
        if objective is None:
            diagnostics.append("plan: no `## 1.` section — the objective the goal embeds into")
        elif _norm(goal.value) not in _norm(objective):
            diagnostics.append(f'goal: plan §1 does not carry the capsule goal: "{goal.value}"')

    non_goals = fields.get("non-goals")
    if non_goals is None or non_goals.is_empty:
        diagnostics.append("capsule: `non-goals` is missing or empty — run `validate` first")
    else:
        section = plan_section(plan_text, 9)
        if section is None:
            diagnostics.append("plan: no `## 9.` section — the non-goals embed into it")
        else:
            planned = {_norm(item): item for item in _bullets(section)}
            wanted = {_norm(item): item for item in non_goals.items}
            for key, item in wanted.items():
                if key not in planned:
                    diagnostics.append(f'non-goal: missing from plan §9: "{item}"')
            for key, item in planned.items():
                if key not in wanted:
                    diagnostics.append(
                        f'non-goal: plan §9 exceeds the capsule — not in the capsule: "{item}"'
                    )
    return diagnostics


# ------------------------------------------------------------------------------------------
# CLI
# ------------------------------------------------------------------------------------------


def _read(path: Path) -> bytes:
    return path.read_bytes()


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="capsule.py",
        description="Hash, validate, and embedding-check an intent capsule (bp-120).",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    for name, help_text in (
        ("hash", "print sha256 of the capsule's canonical bytes"),
        ("validate", "check the eight required fields and both size caps"),
    ):
        one = sub.add_parser(name, help=help_text)
        one.add_argument("capsule", type=Path, help="the capsule file")
    embedding = sub.add_parser(
        "check-embedding", help="check the plan carries the capsule's goal and non-goals"
    )
    embedding.add_argument("capsule", type=Path, help="the capsule file")
    embedding.add_argument("plan", type=Path, help="the build plan that must embed it")
    args = parser.parse_args(argv)

    try:
        capsule_raw = _read(args.capsule)
        plan_raw = _read(args.plan) if args.command == "check-embedding" else b""
        if args.command == "hash":
            print(capsule_hash(capsule_raw))
            return 0
        diagnostics = (
            validate(capsule_raw)
            if args.command == "validate"
            else check_embedding(capsule_raw, plan_raw)
        )
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    except UnicodeDecodeError as e:
        print(f"error: capsule is not valid UTF-8: {e}", file=sys.stderr)
        return 1

    for line in diagnostics:
        print(line, file=sys.stderr)
    return 1 if diagnostics else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
