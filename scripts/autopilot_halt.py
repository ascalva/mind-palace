#!/usr/bin/env python
"""The autopilot HALT LIST as a total predicate over a declared run state (bp-136).

`dn-autopilot-and-delegated-blessing.md` §2.6 enumerates eight halt conditions H1-H8; §2.9
invariant 7 says *"Ambiguity — in routing, in a verdict, in a hash check — always resolves
toward halting."* This module is that list, made a **total function**: every input, including
a malformed or partial one, returns a `Verdict`, and every unknown returns HALT.

⚑ **EXIT 1 MEANS "HALT", WHICH IS THE SAFE OUTCOME.** The inversion is deliberate. A caller
that treats a non-zero exit as "the tool broke" and proceeds anyway has inverted the entire
mechanism — the run continues precisely when the classifier said stop. `explain` exists so
that inversion is one command away from being caught.

    uv run scripts/autopilot_halt.py classify <run-state.json>
      -> prints "<code>: <reason>" to stdout; exit 0 for CONTINUE, 1 for any halt
    uv run scripts/autopilot_halt.py classify -        # reads the JSON from stdin
    uv run scripts/autopilot_halt.py explain           # H0..H8 and the precedence order

THE RUN STATE is a JSON object carrying exactly the sixteen `REQUIRED_KEYS` below (bp-136 §6,
which defines the schema the note describes only in prose). **Every key is required. An absent
key is not a default — it is `H0`.** An *extra* key is also `H0`: a run state the classifier
does not fully understand is not one it may clear.

WHAT THIS DOES NOT DO. §2.6 defines "halt" as five actions — *stop work, checkpoint the
journal, file what exists, park with a re-entry condition, notify via the exhaust lane*. This
module performs **none** of them. It is a pure decision function; the actions belong to the
supervising orchestrator session (note §4: *"the halt-list supervisor as orchestrator-session
logic (no daemon change)"*), and `Verdict.actions_owed` names which of the five are owed. The
operating contract is `.claude/skills/autopilot/SKILL.md`; if the two ever disagree, the skill
is authoritative for BEHAVIOUR and this module for the DECISION.

VOCABULARY. `Verdict.code` is drawn from exactly `CONTINUE`, `H0` (undetermined), `H1`..`H8`.
**There is no value meaning "done", "merge" or "deskcheck"** — non-goals 5 and 6 of the note's
§1.2 are enforced by the absence of the word, which is the cheapest enforcement there is, and
`tests/unit/test_autopilot_halt.py` asserts it at the source level. H8 is *completion*, and
completion is a halt: "Autopilot then **stops**: no merge, no deskcheck, no self-declared done."

PRECEDENCE (bp-136 §6 — §2.6 lists conditions without an order and two can fire at once).
Evaluate in this fixed order, return the first hit:

    H0 -> H6 -> H7 -> H3 -> H1 -> H2 -> H5 -> H4 -> H8 -> CONTINUE

  * H0 first  — an undetermined run state decides nothing else.
  * H6 next   — enforcement failure voids the run's premise.
  * H7 next   — a void grant voids the run's authority.
  * H3, H1    — then the finding classes, by severity (a blocker outranks an owner question).
  * H2        — then audit dissent, which is a judgement about work already done.
  * H5        — then process pressure.
  * H4        — then budget.
  * H8 last   — completion is only meaningful if nothing else fired.

⚑ **H0 is not only the first stage.** Precedence orders the halt *reasons*; any later stage
that cannot determine its own answer also returns `H0` — H2 on an audit record with no legible
`verdict_artifact`, H8 on a completion claim with no Gate B record at all. That is invariant 7
read literally, and it is why "all completion flags true, audits directory empty" comes out
`H0` rather than the vacuous `CONTINUE` a negatively-phrased check would produce.

Repo-workflow tooling, the `scripts/capsule.py` / `scripts/board.py` precedent: stdlib plus one
sanctioned reuse, `_lib.parse_front_matter` (re-deriving a front-matter parser is a DRY defect,
`CONVENTIONS.md`). No `os`, no `subprocess`, no `core`, no `config` — asserted by an AST test —
so this tool structurally cannot reach an environment variable or a Keychain item. It also never
writes: it computes no grant validity, extends no budget, and flips no status. Reading is all it
can do.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Reuse the artifact front-matter machinery — never re-derive it (bp-136 §2 DRY audit).
sys.path.insert(0, str(ROOT / ".claude" / "hooks"))
from _lib import parse_front_matter  # type: ignore[import-not-found]  # noqa: E402

# ------------------------------------------------------------------------------------------
# Item 12 — the vocabulary, and the words it does not contain
# ------------------------------------------------------------------------------------------

#: Every legal `Verdict.code`. `H0` is "undetermined"; `H1`..`H8` are §2.6's halt list. There
#: is deliberately no code meaning "done", "merge", "deskcheck" or "complete" (§1.2 non-goals
#: 5 and 6). The test walks this module's AST and proves no other literal is ever used.
VERDICT_CODES: frozenset[str] = frozenset(
    {"CONTINUE", "H0", "H1", "H2", "H3", "H4", "H5", "H6", "H7", "H8"}
)

#: The five actions §2.6 defines "halt" to mean, verbatim and in order. They populate
#: `Verdict.actions_owed` for EVERY halt code, H8 included — invariant 6: "every halt leaves a
#: parked state with a re-entry condition; a run never evaporates."
HALT_ACTIONS: tuple[str, ...] = (
    "stop work",
    "checkpoint the journal",
    "file what exists",
    "park with a re-entry condition",
    "notify via the exhaust lane",
)

#: One line per code, printed by `explain` — the anti-inversion surface.
CODE_MEANINGS: tuple[tuple[str, str], ...] = (
    ("H0", "undetermined — a required input is absent, null, ill-typed, or unresolvable"),
    ("H1", "owner-level finding — not unambiguously builder-routed (§2.4 conservative reading)"),
    ("H2", "audit dissent — Gate A any dissent; Gate B after the one permitted remediation"),
    ("H3", "blocker finding — already ends any session"),
    ("H4", "budget — token ceiling reached or session_budget exhausted; neither self-extendable"),
    ("H5", "scope pressure — a second scope-guard denial on the same target"),
    ("H6", "enforcement failure — a HOOK-FAILURE line, or a journal that cannot be read"),
    ("H7", "grant void — hash mismatch, TTL expiry, base drift, or a grant never checked"),
    ("H8", "completion, the only terminal halt — and it is a HALT: no merge, no deskcheck"),
    ("CONTINUE", "nothing fired; the run may proceed to its next unit of work"),
)

PRECEDENCE: tuple[str, ...] = ("H0", "H6", "H7", "H3", "H1", "H2", "H5", "H4", "H8", "CONTINUE")

# ------------------------------------------------------------------------------------------
# Item 9 — the run-state schema
# ------------------------------------------------------------------------------------------

#: Kinds a required key may take. `path` and `id` are strings that must also be non-empty;
#: `int` excludes `bool` (which is an `int` subclass in Python, and a `True` where a count is
#: wanted is exactly the kind of confusion invariant 7 says to halt on).
KIND_STR = "str"
KIND_PATH = "path"
KIND_HEX64 = "hex64"
KIND_INT = "int"
KIND_BOOL = "bool"
KIND_ID_LIST = "id-list"
KIND_DENIALS = "denials"

#: The sixteen keys of the run-state document (bp-136 §6). Order is diagnostic order.
REQUIRED_KEYS: dict[str, str] = {
    "plan": KIND_STR,
    "capsule_hash": KIND_HEX64,
    "findings_dir": KIND_PATH,
    "findings_since_base": KIND_ID_LIST,
    "audits_dir": KIND_PATH,
    "remediation_cycles_used": KIND_INT,
    "budget_tokens_used": KIND_INT,
    "budget_tokens_ceiling": KIND_INT,
    "session_budget_remaining": KIND_INT,
    "scope_denials": KIND_DENIALS,
    "journal_path": KIND_PATH,
    "grant_valid": KIND_BOOL,
    "grant_checked": KIND_BOOL,
    "acceptance_all_closed": KIND_BOOL,
    "artifacts_filed": KIND_BOOL,
    "branch_merge_ready": KIND_BOOL,
}

_HEX = frozenset("0123456789abcdef")

#: The three completion booleans H8 reads. Gate B is the fourth condition and is not a
#: boolean — it is a record that must be PRESENT and CLEAN (Item 12's degenerate input).
COMPLETION_FLAGS: tuple[str, ...] = (
    "acceptance_all_closed",
    "artifacts_filed",
    "branch_merge_ready",
)

# ------------------------------------------------------------------------------------------
# Item 10 — the H1 routing vocabulary
# ------------------------------------------------------------------------------------------

#: The builder-side lane, named across BOTH live vocabularies. `CLAUDE.md`'s routing rule calls
#: it `codebase | spec-fidelity`; `docs/templates/finding.md:9` calls the same lane
#: `spec-defect` — `finding-0193`'s census shows the two sets are disjoint NAMES FOR TWO LANES,
#: not two taxonomies, and `spec-defect` is joint-most-used. The pass set is therefore this
#: closed three-name allowlist, and it only applies together with an EXPLICIT `route: builder`.
#: Everything else halts, per §2.4: *"any finding not unambiguously `codebase | spec-fidelity`
#: halts the run. Ambiguity resolves toward stopping."* See `docs/findings/finding-0271.md`.
BUILDER_FTYPES: frozenset[str] = frozenset({"codebase", "spec-fidelity", "spec-defect"})

#: `ftype: blocker` is H3 regardless of route. Compared case-insensitively on purpose.
BLOCKER_FTYPE = "blocker"

# ------------------------------------------------------------------------------------------
# Item 11 — the audit-record vocabulary (bp-135 §6's schema, read with FLAT verdict keys)
# ------------------------------------------------------------------------------------------

AUDIT_ARTIFACT_VERDICTS: frozenset[str] = frozenset({"clean", "concerns", "serious"})
AUDIT_GATES: frozenset[str] = frozenset({"A", "B"})


@dataclass(frozen=True)
class Verdict:
    """The classifier's answer. `reason` is one line and always names the field, finding, or
    record that decided — a halt whose reason does not name its cause is a halt a supervisor
    cannot act on."""

    halt: bool
    code: str
    reason: str
    actions_owed: tuple[str, ...]


def _halt(code: str, reason: str) -> Verdict:
    """A halt verdict. Every halt owes all five §2.6 actions (invariant 6)."""
    return Verdict(halt=True, code=code, reason=reason, actions_owed=HALT_ACTIONS)


def _proceed() -> Verdict:
    """The only non-halt verdict. Reachable ONLY when the run state is complete, well-typed,
    fully resolvable, and no condition fired."""
    return Verdict(
        halt=False,
        code="CONTINUE",
        reason="no halt condition fired over a fully determined run state",
        actions_owed=(),
    )


# ------------------------------------------------------------------------------------------
# Reading helpers — read-only, every one of them
# ------------------------------------------------------------------------------------------


def _text(value: object) -> str:
    """A front-matter scalar as stripped text; anything non-string reads as absent."""
    return value.strip() if isinstance(value, str) else ""


def _resolve(root: Path, value: object) -> Path:
    """A declared path against `root`. Absolute declarations are honoured as given."""
    path = Path(str(value))
    return path if path.is_absolute() else root / path


def _read(path: Path) -> str | None:
    """File text, or None when it is absent, unreadable, or not UTF-8. The caller decides what
    "cannot read" means for its condition; nowhere does it mean "fine"."""
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError, ValueError):
        return None


def _finding_path(root: Path, state: dict[str, object], fid: str) -> Path:
    """`findings_dir/<id>.md`. A `.md` suffix already present is honoured rather than doubled."""
    name = fid if fid.endswith(".md") else f"{fid}.md"
    return _resolve(root, state["findings_dir"]) / name


def _findings(root: Path, state: dict[str, object]) -> list[tuple[str, dict[str, object]]]:
    """`(id, front matter)` for every id in `findings_since_base`. Safe to call only after the
    structural pass, which has already proved every id resolves and every file reads."""
    ids = state["findings_since_base"]
    out: list[tuple[str, dict[str, object]]] = []
    if not isinstance(ids, list):
        return out
    for fid in ids:
        raw = _read(_finding_path(root, state, str(fid)))
        out.append((str(fid), parse_front_matter(raw) if raw is not None else {}))
    return out


def _audits(root: Path, state: dict[str, object]) -> list[tuple[str, dict[str, object]]]:
    """`(stem, front matter)` for every audit record in `audits_dir` that names this `plan`.

    An audit record is identified structurally — `type: audit` plus a matching `plan:` — so a
    hand-written document that happens to sit in the directory is not mistaken for one. Sorted,
    so the reason a run halts does not depend on directory iteration order."""
    directory = _resolve(root, state["audits_dir"])
    plan = _text(state["plan"])
    out: list[tuple[str, dict[str, object]]] = []
    try:
        candidates = sorted(directory.glob("*.md"))
    except OSError:
        return out
    for record in candidates:
        raw = _read(record)
        if raw is None:
            continue
        front = parse_front_matter(raw)
        if _text(front.get("type")) == "audit" and _text(front.get("plan")) == plan:
            out.append((record.stem, front))
    return out


# ------------------------------------------------------------------------------------------
# Item 9 — the structural pass. Absence is a halt.
# ------------------------------------------------------------------------------------------


def _kind_problem(name: str, kind: str, value: object) -> str | None:
    """One diagnostic line, or None when `value` is a legal instance of `kind`."""
    if value is None:
        return f"`{name}` is null — a null is not an observation"
    if kind in (KIND_STR, KIND_PATH, KIND_HEX64):
        if not isinstance(value, str) or not value.strip():
            return f"`{name}` must be a non-empty string, got {type(value).__name__}"
        if kind == KIND_HEX64 and (len(value) != 64 or not set(value) <= _HEX):
            return f"`{name}` must be 64 lowercase hex characters"
        return None
    if kind == KIND_BOOL:
        if not isinstance(value, bool):
            return f"`{name}` must be a JSON boolean, got {type(value).__name__}"
        return None
    if kind == KIND_INT:
        if isinstance(value, bool) or not isinstance(value, int):
            return f"`{name}` must be a non-negative integer, got {type(value).__name__}"
        if value < 0:
            return f"`{name}` must be a non-negative integer, got {value}"
        return None
    if kind == KIND_ID_LIST:
        if not isinstance(value, list):
            return f"`{name}` must be a list, got {type(value).__name__}"
        for item in value:
            if not isinstance(item, str) or not item.strip():
                return f"`{name}` holds a non-string or empty id"
        return None
    if kind == KIND_DENIALS:
        if not isinstance(value, list):
            return f"`{name}` must be a list, got {type(value).__name__}"
        for entry in value:
            if not isinstance(entry, dict) or set(entry) != {"target", "count"}:
                return f"`{name}` entries must be objects with exactly `target` and `count`"
            target, count = entry["target"], entry["count"]
            if not isinstance(target, str) or not target.strip():
                return f"`{name}` entry has an empty or non-string `target`"
            if isinstance(count, bool) or not isinstance(count, int) or count < 0:
                return f"`{name}` entry `{target}` has a non-integer or negative `count`"
        return None
    return f"`{name}` has an unknown kind `{kind}`"  # unreachable; a total function says so


def _structural(state: dict[str, object], root: Path) -> Verdict | None:
    """H0 — the total-function floor. Every unknown halts, in a fixed diagnostic order so the
    same defective state always names the same field."""
    for name in REQUIRED_KEYS:
        if name not in state:
            return _halt(
                "H0", f"required key `{name}` is absent — an absent key is not a default"
            )
    extra = sorted(set(state) - set(REQUIRED_KEYS))
    if extra:
        return _halt(
            "H0",
            f"unknown key `{extra[0]}` — a run state the classifier does not fully understand "
            "is not one it may clear",
        )
    for name, kind in REQUIRED_KEYS.items():
        problem = _kind_problem(name, kind, state[name])
        if problem is not None:
            return _halt("H0", problem)

    if state["budget_tokens_ceiling"] == 0:
        return _halt(
            "H0",
            "`budget_tokens_ceiling` is 0 — a zero ceiling is an unstated budget, not an "
            "exhausted one, and must not read as a vacuous H4",
        )

    ids = state["findings_since_base"]
    if isinstance(ids, list):
        for fid in ids:
            path = _finding_path(root, state, str(fid))
            if not path.is_file():
                return _halt(
                    "H0",
                    f"`findings_since_base` cites `{fid}`, which does not resolve to "
                    f"`{path}` — a cited identifier that does not resolve is a failure "
                    "(CONSTITUTION §III.1)",
                )
            if _read(path) is None:
                return _halt("H0", f"finding `{fid}` resolves but cannot be read as UTF-8 text")
    return None


# ------------------------------------------------------------------------------------------
# Item 10 — the conditions with observable evidence
# ------------------------------------------------------------------------------------------


def _stage_h6(state: dict[str, object], root: Path) -> Verdict | None:
    """H6 — enforcement failure. Any `HOOK-FAILURE` line in the run's journal; and a journal
    that cannot be read is an UNCHECKED journal, which is the same thing as an unchecked cage.
    §2.6: *"autopilot must not self-reconcile its own cage."*"""
    path = _resolve(root, state["journal_path"])
    text = _read(path)
    if text is None:
        return _halt(
            "H6",
            f"journal `{path}` is absent or unreadable — an unread journal is an unchecked "
            "one, and enforcement cannot be shown to have applied",
        )
    if "HOOK-FAILURE" in text:
        return _halt(
            "H6", f"journal `{path}` carries a HOOK-FAILURE line — enforcement was NOT applied"
        )
    return None


def _stage_h7(state: dict[str, object], root: Path) -> Verdict | None:
    """H7 — grant void. This module computes NO grant validity and imports nothing from the
    grant's cryptography (bp-138): `grant_valid` is data, which is what lets the halt list ship
    before the grant does. `grant_checked` is asked FIRST — a caller that declares the grant
    fine without ever checking it is the degenerate input this condition exists to catch."""
    if state["grant_checked"] is not True:
        return _halt(
            "H7",
            "`grant_checked` is false — the grant was never re-verified, and an unchecked "
            "grant is a void grant regardless of what `grant_valid` claims",
        )
    if state["grant_valid"] is not True:
        return _halt(
            "H7",
            "`grant_valid` is false — capsule/plan hash mismatch, TTL expiry, base drift, or "
            "a grant record that failed offline re-verification",
        )
    return None


def _stage_h3(state: dict[str, object], root: Path) -> Verdict | None:
    """H3 — blocker finding. Compared case-insensitively: `Blocker` is a blocker."""
    for fid, front in _findings(root, state):
        if _text(front.get("ftype")).lower() == BLOCKER_FTYPE:
            return _halt("H3", f"`{fid}` is a blocker finding — a blocker ends any session")
    return None


def _stage_h1(state: dict[str, object], root: Path) -> Verdict | None:
    """H1 — owner-level finding, read conservatively (§2.4, verbatim): *"any finding not
    unambiguously `codebase | spec-fidelity` halts the run. Ambiguity resolves toward
    stopping."* The pass condition is therefore a CLOSED allowlist over an EXPLICIT
    `route: builder`; an absent route, an absent ftype, and any unrecognised value all halt."""
    for fid, front in _findings(root, state):
        route = _text(front.get("route")).lower()
        ftype = _text(front.get("ftype")).lower()
        if route == "builder" and ftype in BUILDER_FTYPES:
            continue
        return _halt(
            "H1",
            f"`{fid}` is not unambiguously builder-routed "
            f"(ftype={ftype or '<absent>'}, route={route or '<absent>'}) — a low-stakes run "
            "that raises an owner-level question has left the low-stakes envelope",
        )
    return None


# ------------------------------------------------------------------------------------------
# Item 11 — the injected conditions
# ------------------------------------------------------------------------------------------


def _stage_h2(state: dict[str, object], root: Path) -> Verdict | None:
    """H2 — audit dissent (§2.5).

    The layer question, answered honestly rather than guessed. bp-135 §6's record carries
    `gate: A | B`, and §2.5's table DEFINES Gate A as the intent-fidelity gate and Gate B as
    the mechanism gate — so the top-level layer mapping is a field of the record, not an
    inference. What is NOT determinable is §2.5's refinement *"or any intent-level CONCERNS"*
    raised AT Gate B: no field carries that. The conservative fallback is applied and stated
    (`docs/findings/finding-0273.md`), never a guess at layer:

      * Gate A, any non-clean verdict            -> halt immediately (intent-level by gate).
      * any gate, `serious`                      -> halt immediately; `serious` is not a
                                                    one-remediation-cycle matter.
      * Gate B, `concerns`                       -> halt iff a remediation cycle was already
                                                    used; the first is the one §2.5 permits.

    An illegible record — no `verdict_artifact`, or a `gate` outside `A|B` — is `H0`."""
    remediations = state["remediation_cycles_used"]
    used = remediations if isinstance(remediations, int) else 0
    for stem, front in _audits(root, state):
        gate = _text(front.get("gate")).upper()
        artifact = _text(front.get("verdict_artifact")).lower()
        if gate not in AUDIT_GATES:
            return _halt("H0", f"audit `{stem}` has gate `{gate or '<absent>'}`, not A or B")
        if artifact not in AUDIT_ARTIFACT_VERDICTS:
            return _halt(
                "H0",
                f"audit `{stem}` has no legible `verdict_artifact` "
                f"(`{artifact or '<absent>'}`) — an illegible verdict is an undetermined one",
            )
        if artifact == "clean":
            continue
        if gate == "A":
            return _halt(
                "H2",
                f"audit `{stem}` is a Gate A dissent (`{artifact}`) — intent-level dissent "
                "halts immediately; remediating intent unattended is goal origination",
            )
        if artifact == "serious":
            return _halt(
                "H2",
                f"audit `{stem}` is a Gate B `serious` verdict — not a matter for the one "
                "permitted remediation cycle",
            )
        if used >= 1:
            return _halt(
                "H2",
                f"audit `{stem}` is a second Gate B `concerns` "
                f"(remediation_cycles_used={used}) — autopilot never adjudicates its own audit",
            )
    return None


def _stage_h5(state: dict[str, object], root: Path) -> Verdict | None:
    """H5 — scope pressure. §2.6: *"A second scope-guard denial on the same target."* No hook
    persists denials (`scope-guard` prints and exits 2), so the supervisor DECLARES them and
    this module's contribution is to refuse when the declaration is absent (that is H0, above),
    never to assume none happened."""
    denials = state["scope_denials"]
    if not isinstance(denials, list):
        return None
    for entry in denials:
        if isinstance(entry, dict) and isinstance(entry.get("count"), int):
            count = entry["count"]
            if not isinstance(count, bool) and count >= 2:
                return _halt(
                    "H5",
                    f"{count} scope-guard denials on `{entry['target']}` — repeated pressure "
                    "on one target means the plan is mis-scoped; never route around",
                )
    return None


def _stage_h4(state: dict[str, object], root: Path) -> Verdict | None:
    """H4 — budget. Neither ceiling is self-extendable: this module has no writer at all."""
    used = state["budget_tokens_used"]
    ceiling = state["budget_tokens_ceiling"]
    if isinstance(used, int) and isinstance(ceiling, int) and used >= ceiling:
        return _halt(
            "H4",
            f"budget_tokens_used={used} has reached the capsule ceiling {ceiling} — "
            "a ceiling the run can raise is not a ceiling",
        )
    sessions = state["session_budget_remaining"]
    if isinstance(sessions, int) and sessions <= 0:
        return _halt("H4", f"session_budget_remaining={sessions} — the session budget is spent")
    return None


# ------------------------------------------------------------------------------------------
# Item 12 — the terminal halt
# ------------------------------------------------------------------------------------------


def _stage_h8(state: dict[str, object], root: Path) -> Verdict | None:
    """H8 — completion, and completion is a HALT: *"Autopilot then stops: no merge, no
    deskcheck, no self-declared done."*

    Four conditions, phrased POSITIVELY on purpose. "Gate B is not `concerns`" is vacuously
    true of a directory holding no Gate B at all, so a negative phrasing would declare a run
    complete with no audit — the precise failure §2.7 exists to prevent. The Gate B record must
    be PRESENT, unique, and `clean`; anything less is `H0`, not `CONTINUE` and not `H8`."""
    if not all(state[flag] is True for flag in COMPLETION_FLAGS):
        return None
    gate_b = [
        (stem, front)
        for stem, front in _audits(root, state)
        if _text(front.get("gate")).upper() == "B"
    ]
    if not gate_b:
        return _halt(
            "H0",
            "completion is claimed but no Gate B audit record exists for this plan — a run "
            "with no audit is not a complete run, it is an unaudited one",
        )
    if len(gate_b) > 1:
        return _halt(
            "H0",
            f"completion is claimed but {len(gate_b)} Gate B records exist for this plan "
            f"({', '.join(stem for stem, _ in gate_b)}) — which one is the verdict is undetermined",
        )
    stem, front = gate_b[0]
    if _text(front.get("verdict_artifact")).lower() != "clean":
        return _halt("H0", f"Gate B record `{stem}` is not clean and was not caught by H2")
    return _halt(
        "H8",
        f"acceptance closed, Gate B `{stem}` clean, artifacts filed, branch merge-ready — "
        "autopilot STOPS here; the merge and the deskcheck are the owner's",
    )


#: The precedence order of §6, as executable stages. H0 runs first as `_structural`; any stage
#: below may also return `H0` when it cannot determine its own answer (see the module docstring).
_STAGES = (_stage_h6, _stage_h7, _stage_h3, _stage_h1, _stage_h2, _stage_h5, _stage_h4, _stage_h8)


def classify(state: object, root: Path | None = None) -> Verdict:
    """Classify a declared run state. **Total**: every input returns a `Verdict`, and every
    unknown returns a halt. `root` resolves the state's relative paths (the repo root by
    default); tests pass a `tmp_path`."""
    base = ROOT if root is None else root
    if not isinstance(state, dict):
        return _halt(
            "H0",
            f"the run state is not a JSON object (got {type(state).__name__}) — nothing was "
            "observed, and nothing observed is not a clear run",
        )
    if not all(isinstance(key, str) for key in state):
        return _halt("H0", "the run state has a non-string key")
    structural = _structural(state, base)
    if structural is not None:
        return structural
    for stage in _STAGES:
        verdict = stage(state, base)
        if verdict is not None:
            return verdict
    return _proceed()


def classify_json(raw: str, root: Path | None = None) -> Verdict:
    """`classify` over undecoded text. Unparseable JSON is `H0` with no traceback — a crash
    would exit non-zero too, but for the wrong reason and with no line a supervisor can log."""
    try:
        state = json.loads(raw)
    except (json.JSONDecodeError, ValueError, TypeError) as exc:
        return _halt("H0", f"the run state is not parseable JSON: {exc}")
    return classify(state, root)


# ------------------------------------------------------------------------------------------
# CLI
# ------------------------------------------------------------------------------------------


def explain_text() -> str:
    """The anti-inversion surface: what each code means, the precedence order, and the exit
    convention spelled out in words."""
    lines = [
        "autopilot halt classifier — dn-autopilot-and-delegated-blessing §2.6 (bp-136)",
        "",
        "EXIT 1 MEANS HALT, WHICH IS THE SAFE OUTCOME. Exit 0 means CONTINUE.",
        "A caller that reads a non-zero exit as 'the tool broke' and proceeds has inverted",
        "the entire mechanism.",
        "",
        "codes:",
    ]
    lines += [f"  {code:<9} {meaning}" for code, meaning in CODE_MEANINGS]
    lines += [
        "",
        "precedence (first hit wins):",
        f"  {' -> '.join(PRECEDENCE)}",
        "",
        "H0 is not only the first stage: any stage that cannot determine its own answer also",
        "returns H0 (invariant 7 — ambiguity always resolves toward halting).",
        "",
        "on any halt, these five actions are owed (§2.6's definition of 'halt'):",
    ]
    lines += [f"  - {action}" for action in HALT_ACTIONS]
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="autopilot_halt.py",
        description="Classify an autopilot run state against the §2.6 halt list (bp-136).",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    one = sub.add_parser("classify", help="classify a declared run state; exit 1 means HALT")
    one.add_argument("state", help="the run-state JSON file, or `-` for stdin")
    one.add_argument(
        "--root", type=Path, default=None, help="root the state's relative paths resolve against"
    )
    sub.add_parser("explain", help="print the codes, the precedence order, and the exit inversion")
    args = parser.parse_args(argv)

    if args.command == "explain":
        print(explain_text())
        return 0

    if args.state == "-":
        raw = sys.stdin.read()
    else:
        text = _read(Path(args.state))
        if text is None:
            print(f"H0: run state `{args.state}` is absent or unreadable")
            return 1
        raw = text

    verdict = classify_json(raw, args.root)
    print(f"{verdict.code}: {verdict.reason}")
    return 1 if verdict.halt else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
