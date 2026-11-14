"""The autopilot halt list as a TOTAL predicate — bp-136 Items 9-13.

Five properties, one file, each test named for the criterion, falsifier, degenerate input, or
mutant it encodes:

  * Item 9 — the run-state schema and **H0**: `classify` is total. Every one of the sixteen
    keys removed, nulled, or mistyped yields `H0` naming it; an extra key yields `H0`;
    unparseable JSON yields `H0` with no traceback. The degenerate input is `{}` — a
    classifier written the obvious way (walk H1..H8, `CONTINUE` if none matched) returns
    CONTINUE on the input that means *nothing was observed at all*, which is note invariant 7
    exactly inverted.
  * Item 10 — **H1/H3/H6**, decided from observable evidence. The degenerate input is
    `findings_since_base: []` (a real observation: "I looked, there were none") versus the key
    being absent ("nobody looked"); and a cited finding id with no file behind it, which a
    check that iterates only over files it can open silently skips.
  * Item 11 — **H2/H4/H5/H7**, decided from declared inputs. The degenerate input is
    `grant_valid: true, grant_checked: false` — a declaration that the grant is fine from a
    caller that never checked.
  * Item 12 — **H8**, the terminal halt, plus the source-level assertion that the verdict
    vocabulary has no word for "merge", "deskcheck", "done" or "complete". The degenerate input
    is all completion flags true with an empty audits directory: "Gate B is not `concerns`" is
    vacuously true of a directory holding no Gate B at all.
  * Item 13 — the **skill**: required literals read from RENDERED PROSE (a `substring in text`
    check passes on prose inside an HTML comment, which is not in force), every cited relative
    path resolves (`CONSTITUTION.md` §III.1), and the graduate skill's session-sizing heuristic
    is linked rather than restated.

Plus the tooling invariant (the `test_capsule.py` AST precedent): stdlib only apart from the
sanctioned `_lib` reuse, no `core`, no `config`, no `os`/`subprocess`, and no writer of any
kind — so the classifier structurally cannot reach a secret, extend a budget, or flip a status.
"""

from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

import autopilot_halt  # type: ignore[import-not-found]  # noqa: E402

MODULE = REPO / "scripts" / "autopilot_halt.py"
SOURCE = MODULE.read_text(encoding="utf-8")
SKILL = REPO / ".claude" / "skills" / "autopilot" / "SKILL.md"

HEX64 = "a" * 64


# ------------------------------------------------------------------------------------------
# Fixtures — a run state, findings, audit records
# ------------------------------------------------------------------------------------------


def _state(tmp_path: Path, **overrides: object) -> dict[str, object]:
    """A well-formed run state over `tmp_path` that classifies CONTINUE, plus the on-disk
    facts it declares. Every test starts here and perturbs exactly one thing."""
    (tmp_path / "findings").mkdir(exist_ok=True)
    (tmp_path / "audits").mkdir(exist_ok=True)
    (tmp_path / "journal.md").write_text("# journal\n\nnothing unusual.\n", encoding="utf-8")
    state: dict[str, object] = {
        "plan": "bp-999",
        "capsule_hash": HEX64,
        "findings_dir": "findings",
        "findings_since_base": [],
        "audits_dir": "audits",
        "remediation_cycles_used": 0,
        "budget_tokens_used": 12_000,
        "budget_tokens_ceiling": 200_000,
        "session_budget_remaining": 1,
        "scope_denials": [],
        "journal_path": "journal.md",
        "grant_valid": True,
        "grant_checked": True,
        "acceptance_all_closed": False,
        "artifacts_filed": False,
        "branch_merge_ready": False,
    }
    state.update(overrides)
    return state


def _finding(tmp_path: Path, fid: str, *, ftype: str | None, route: str | None) -> str:
    """Write a finding with the given front matter; `None` omits the key entirely."""
    lines = ["---", "type: finding", f"id: {fid}", "status: open"]
    if ftype is not None:
        lines.append(f"ftype: {ftype}")
    if route is not None:
        lines.append(f"route: {route}")
    lines += ["---", "", f"# {fid}", ""]
    (tmp_path / "findings" / f"{fid}.md").write_text("\n".join(lines), encoding="utf-8")
    return fid


def _audit(
    tmp_path: Path,
    stem: str,
    *,
    gate: str,
    artifact: str,
    plan: str = "bp-999",
    record: str = "accurate",
) -> None:
    """An audit record on bp-135 §6's schema — FLAT `verdict_artifact` / `verdict_record`,
    because `_lib.parse_front_matter` is a YAML subset that does not read nested mappings."""
    (tmp_path / "audits" / f"{stem}.md").write_text(
        "\n".join(
            [
                "---",
                "type: audit",
                f"id: {stem}",
                f"gate: {gate}",
                f"plan: {plan}",
                f"capsule_hash: {HEX64}",
                "method: cold-read",
                "auditor_context: fresh-session",
                f"verdict_artifact: {artifact}",
                f"verdict_record: {record}",
                "unverified: []",
                "dissent_finding: null",
                "---",
                "",
                "## Verdict",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _classify(tmp_path: Path, state: object) -> autopilot_halt.Verdict:
    return autopilot_halt.classify(state, root=tmp_path)


# ------------------------------------------------------------------------------------------
# Item 9 — the run-state schema and H0: absence is a halt
# ------------------------------------------------------------------------------------------


def test_the_baseline_state_continues(tmp_path: Path) -> None:
    """CONTINUE must be REACHABLE — a classifier that halts on everything is as useless as one
    that clears everything, and it would make every test below vacuous."""
    verdict = _classify(tmp_path, _state(tmp_path))
    assert verdict.code == "CONTINUE"
    assert verdict.halt is False
    assert verdict.actions_owed == ()


@pytest.mark.parametrize("key", sorted(autopilot_halt.REQUIRED_KEYS))
def test_each_required_key_removed_one_at_a_time_yields_h0_naming_it(
    tmp_path: Path, key: str
) -> None:
    """§6: *"Every key is required. An absent key is not a default — it is HALT (H0)."*"""
    state = _state(tmp_path)
    del state[key]
    verdict = _classify(tmp_path, state)
    assert verdict.halt is True
    assert verdict.code == "H0"
    assert key in verdict.reason, verdict.reason


@pytest.mark.parametrize("key", sorted(autopilot_halt.REQUIRED_KEYS))
def test_each_required_key_set_to_null_yields_h0_naming_it(tmp_path: Path, key: str) -> None:
    """A key present but `null` is not an observation — it is the absence of one, wearing a
    key's clothes."""
    verdict = _classify(tmp_path, _state(tmp_path, **{key: None}))
    assert verdict.code == "H0"
    assert key in verdict.reason, verdict.reason


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("grant_valid", "yes"),  # §7 Item 9's named case
        ("grant_valid", 1),  # bool is an int subclass; 1 is not a boolean observation
        ("acceptance_all_closed", "true"),
        ("remediation_cycles_used", True),  # ... and an int field must not accept a bool
        ("remediation_cycles_used", "0"),
        ("remediation_cycles_used", -1),
        ("budget_tokens_used", 1.5),
        ("plan", ""),
        ("journal_path", 42),
        ("capsule_hash", "A" * 64),  # uppercase is not the pinned form
        ("capsule_hash", "abc"),
        ("findings_since_base", "finding-0001"),  # a string is not a list of ids
        ("findings_since_base", [7]),
        ("scope_denials", {"target": "x", "count": 1}),  # an object is not a list
        ("scope_denials", [{"target": "x"}]),  # missing `count`
        ("scope_denials", [{"target": "x", "count": 1, "extra": 2}]),
        ("scope_denials", [{"target": "", "count": 1}]),
        ("scope_denials", [{"target": "x", "count": True}]),
    ],
)
def test_a_key_of_the_wrong_type_yields_h0_naming_it(
    tmp_path: Path, key: str, value: object
) -> None:
    verdict = _classify(tmp_path, _state(tmp_path, **{key: value}))
    assert verdict.code == "H0", (key, value, verdict)
    assert key in verdict.reason, verdict.reason


def test_an_extra_unknown_key_yields_h0(tmp_path: Path) -> None:
    """*"a run state the classifier does not fully understand is not one it may clear."*"""
    verdict = _classify(tmp_path, _state(tmp_path, stakes="low"))
    assert verdict.code == "H0"
    assert "stakes" in verdict.reason


def test_unparseable_json_yields_h0_and_no_traceback() -> None:
    verdict = autopilot_halt.classify_json("{ not json at all")
    assert verdict.code == "H0"
    assert "parseable" in verdict.reason


@pytest.mark.parametrize("state", [None, [], 3, "bp-999", True])
def test_classify_is_total_over_non_objects(tmp_path: Path, state: object) -> None:
    """Total means total: a JSON scalar, a list, and `null` all return a Verdict."""
    verdict = _classify(tmp_path, state)
    assert isinstance(verdict, autopilot_halt.Verdict)
    assert verdict.code == "H0"
    assert verdict.halt is True


def test_the_empty_object_is_h0_not_continue(tmp_path: Path) -> None:
    """⚑ THE degenerate input of this plan. A classifier that walks H1..H8 and returns CONTINUE
    when none matched clears `{}` — the input that means *nothing was observed at all*. That is
    invariant 7 inverted, and it is the single failure this whole module is shaped to prevent."""
    verdict = _classify(tmp_path, {})
    assert verdict.halt is True
    assert verdict.code == "H0"


def test_a_partial_object_is_h0_not_continue(tmp_path: Path) -> None:
    verdict = _classify(tmp_path, {"plan": "bp-999"})
    assert verdict.halt is True
    assert verdict.code == "H0"


def test_a_zero_budget_ceiling_is_h0_not_a_vacuous_h4(tmp_path: Path) -> None:
    """`0 >= 0` would make H4 fire on a run whose ceiling was never stated. An unstated budget
    is undetermined, not exhausted — the reason a run stops must be true."""
    verdict = _classify(tmp_path, _state(tmp_path, budget_tokens_ceiling=0, budget_tokens_used=0))
    assert verdict.code == "H0"
    assert "budget_tokens_ceiling" in verdict.reason


def test_every_halt_owes_the_five_actions(tmp_path: Path) -> None:
    """Invariant 6 — *"Every halt leaves a parked state with a re-entry condition — a run never
    evaporates."* `actions_owed` is non-empty for EVERY halt code, H8 included."""
    verdict = _classify(tmp_path, {})
    assert verdict.actions_owed == (
        "stop work",
        "checkpoint the journal",
        "file what exists",
        "park with a re-entry condition",
        "notify via the exhaust lane",
    )


# ------------------------------------------------------------------------------------------
# Item 10 — H1, H3, H6: the conditions the classifier verifies itself
# ------------------------------------------------------------------------------------------


def test_h3_fires_on_a_blocker_finding(tmp_path: Path) -> None:
    state = _state(tmp_path, findings_since_base=["finding-9001"])
    _finding(tmp_path, "finding-9001", ftype="blocker", route="builder")
    verdict = _classify(tmp_path, state)
    assert verdict.code == "H3"
    assert "finding-9001" in verdict.reason


def test_h3_is_case_insensitive(tmp_path: Path) -> None:
    """⚑ MUTANT m3 — dropping `.lower()` lets `Blocker` slip past H3 into H1, which halts for
    the wrong reason and reports the wrong condition to the supervisor."""
    state = _state(tmp_path, findings_since_base=["finding-9002"])
    _finding(tmp_path, "finding-9002", ftype="Blocker", route="builder")
    assert _classify(tmp_path, state).code == "H3"


def test_h3_outranks_h1(tmp_path: Path) -> None:
    """Precedence: the finding classes are ordered by severity, blocker first."""
    state = _state(tmp_path, findings_since_base=["finding-9003", "finding-9004"])
    _finding(tmp_path, "finding-9003", ftype="design", route="orchestrator")
    _finding(tmp_path, "finding-9004", ftype="blocker", route="builder")
    assert _classify(tmp_path, state).code == "H3"


@pytest.mark.parametrize("ftype", ["codebase", "spec-fidelity", "spec-defect"])
def test_h1_does_not_fire_for_an_explicitly_builder_routed_finding(
    tmp_path: Path, ftype: str
) -> None:
    """§7 Item 10, verbatim: *"H1 does not fire for a finding explicitly `route: builder` with
    `ftype: spec-defect`."* The pass set is the builder lane named across BOTH live vocabularies
    (`finding-0193`'s census; the reconciliation is `finding-0271`)."""
    state = _state(tmp_path, findings_since_base=["finding-9005"])
    _finding(tmp_path, "finding-9005", ftype=ftype, route="builder")
    assert _classify(tmp_path, state).code == "CONTINUE"


def test_h1_fires_on_route_orchestrator(tmp_path: Path) -> None:
    state = _state(tmp_path, findings_since_base=["finding-9006"])
    _finding(tmp_path, "finding-9006", ftype="design", route="orchestrator")
    verdict = _classify(tmp_path, state)
    assert verdict.code == "H1"
    assert "finding-9006" in verdict.reason


def test_h1_fires_when_route_is_absent(tmp_path: Path) -> None:
    """⚑ MUTANT m1 — relaxing H1 to fire only on `route: orchestrator` drops the conservative
    arm, and a finding with NO route sails through. Ambiguity resolves toward stopping."""
    state = _state(tmp_path, findings_since_base=["finding-9007"])
    _finding(tmp_path, "finding-9007", ftype="spec-defect", route=None)
    assert _classify(tmp_path, state).code == "H1"


def test_h1_fires_when_ftype_is_absent(tmp_path: Path) -> None:
    """⚑ MUTANT m1, second arm."""
    state = _state(tmp_path, findings_since_base=["finding-9008"])
    _finding(tmp_path, "finding-9008", ftype=None, route="builder")
    assert _classify(tmp_path, state).code == "H1"


@pytest.mark.parametrize("ftype", ["discovery", "question", "design", "math", "direction", "??"])
def test_h1_fires_on_a_non_builder_ftype_even_when_routed_builder(
    tmp_path: Path, ftype: str
) -> None:
    """⚑ MUTANT m1, third arm — the pass set is a CLOSED allowlist, not "anything but
    orchestrator"."""
    state = _state(tmp_path, findings_since_base=["finding-9009"])
    _finding(tmp_path, "finding-9009", ftype=ftype, route="builder")
    assert _classify(tmp_path, state).code == "H1"


def test_an_empty_findings_list_is_a_real_observation(tmp_path: Path) -> None:
    """⚑ Degenerate input. `[]` says "I looked, there were none" and must NOT halt; the key
    being absent says "nobody looked" and must halt (the test above). The naive implementation
    cannot tell them apart and passes both."""
    assert _classify(tmp_path, _state(tmp_path, findings_since_base=[])).code == "CONTINUE"
    state = _state(tmp_path)
    del state["findings_since_base"]
    assert _classify(tmp_path, state).code == "H0"


def test_an_unresolvable_finding_id_yields_h0(tmp_path: Path) -> None:
    """⚑ Degenerate input. A check that iterates only over files it can open silently skips a
    cited id with no file — `CONSTITUTION.md` §III.1: a cited identifier that does not resolve
    is a failure."""
    state = _state(tmp_path, findings_since_base=["finding-9999"])
    verdict = _classify(tmp_path, state)
    assert verdict.code == "H0"
    assert "finding-9999" in verdict.reason


def test_h6_fires_on_a_hook_failure_line(tmp_path: Path) -> None:
    state = _state(tmp_path)
    (tmp_path / "journal.md").write_text(
        "# journal\n\nHOOK-FAILURE scope-guard: boom — enforcement NOT applied\n", encoding="utf-8"
    )
    verdict = _classify(tmp_path, state)
    assert verdict.code == "H6"
    assert "HOOK-FAILURE" in verdict.reason


def test_h6_fires_when_the_journal_does_not_exist(tmp_path: Path) -> None:
    """⚑ MUTANT m2 — making the missing-journal case return CONTINUE means an autopilot run
    whose journal was never written reads as "no enforcement failure observed". An unreadable
    journal is an UNCHECKED one, and §2.6 says autopilot must not self-reconcile its own cage."""
    state = _state(tmp_path, journal_path="does-not-exist.md")
    assert _classify(tmp_path, state).code == "H6"


def test_h6_outranks_h7_and_h1(tmp_path: Path) -> None:
    """Enforcement failure first: it voids the run's PREMISE, so nothing decided under it is
    trustworthy — including the grant check and the finding scan."""
    state = _state(
        tmp_path, grant_valid=False, grant_checked=False, findings_since_base=["finding-9010"]
    )
    _finding(tmp_path, "finding-9010", ftype="design", route="orchestrator")
    (tmp_path / "journal.md").write_text("HOOK-FAILURE gate-guard: x\n", encoding="utf-8")
    assert _classify(tmp_path, state).code == "H6"


# ------------------------------------------------------------------------------------------
# Item 11 — H2, H4, H5, H7: the injected conditions
# ------------------------------------------------------------------------------------------


def test_h7_fires_when_the_grant_was_never_checked_however_valid_it_claims_to_be(
    tmp_path: Path,
) -> None:
    """⚑ Degenerate input: `grant_valid: true, grant_checked: false` — a declaration that the
    grant is fine from a caller that never checked. A classifier reading only `grant_valid`
    passes it."""
    verdict = _classify(tmp_path, _state(tmp_path, grant_valid=True, grant_checked=False))
    assert verdict.code == "H7"
    assert "grant_checked" in verdict.reason


def test_h7_fires_when_the_grant_is_invalid(tmp_path: Path) -> None:
    verdict = _classify(tmp_path, _state(tmp_path, grant_valid=False))
    assert verdict.code == "H7"
    assert "grant_valid" in verdict.reason


def test_h7_outranks_the_finding_classes(tmp_path: Path) -> None:
    state = _state(tmp_path, grant_valid=False, findings_since_base=["finding-9011"])
    _finding(tmp_path, "finding-9011", ftype="blocker", route="builder")
    assert _classify(tmp_path, state).code == "H7"


def test_h2_fires_immediately_on_a_gate_a_dissent(tmp_path: Path) -> None:
    """Gate A is the intent-fidelity gate (§2.5's table), so a Gate A dissent IS intent-level —
    read from the record's own `gate:` field, not guessed."""
    state = _state(tmp_path)
    _audit(tmp_path, "audit-bp-999-a", gate="A", artifact="concerns")
    verdict = _classify(tmp_path, state)
    assert verdict.code == "H2"
    assert "Gate A" in verdict.reason


def test_h2_permits_the_one_gate_b_remediation_cycle(tmp_path: Path) -> None:
    """§2.5: *"a mechanism CONCERNS permits ONE remediation cycle"* — so the FIRST Gate B
    `concerns` does not halt."""
    state = _state(tmp_path, remediation_cycles_used=0)
    _audit(tmp_path, "audit-bp-999-b", gate="B", artifact="concerns")
    assert _classify(tmp_path, state).code == "CONTINUE"


def test_h2_halts_on_a_second_gate_b_concerns(tmp_path: Path) -> None:
    state = _state(tmp_path, remediation_cycles_used=1)
    _audit(tmp_path, "audit-bp-999-b", gate="B", artifact="concerns")
    verdict = _classify(tmp_path, state)
    assert verdict.code == "H2"
    assert "remediation_cycles_used=1" in verdict.reason


def test_h2_halts_immediately_on_a_gate_b_serious_verdict(tmp_path: Path) -> None:
    """The conservative fallback of `finding-0273`: `serious` is not a one-cycle matter, and
    the layer it sits at is not a field of the record, so it halts rather than being remediated."""
    state = _state(tmp_path, remediation_cycles_used=0)
    _audit(tmp_path, "audit-bp-999-b", gate="B", artifact="serious")
    assert _classify(tmp_path, state).code == "H2"


def test_h2_ignores_audit_records_belonging_to_another_plan(tmp_path: Path) -> None:
    state = _state(tmp_path)
    _audit(tmp_path, "audit-bp-111-a", gate="A", artifact="serious", plan="bp-111")
    assert _classify(tmp_path, state).code == "CONTINUE"


@pytest.mark.parametrize(
    ("gate", "artifact"), [("C", "clean"), ("", "clean"), ("B", "fine"), ("B", "")]
)
def test_an_illegible_audit_record_is_h0(tmp_path: Path, gate: str, artifact: str) -> None:
    """An illegible verdict is an undetermined one — invariant 7 again, applied to the record
    rather than to the routing."""
    state = _state(tmp_path)
    _audit(tmp_path, "audit-bp-999-b", gate=gate, artifact=artifact)
    assert _classify(tmp_path, state).code == "H0"


def test_h4_fires_when_the_token_ceiling_is_reached(tmp_path: Path) -> None:
    state = _state(tmp_path, budget_tokens_used=200_000, budget_tokens_ceiling=200_000)
    verdict = _classify(tmp_path, state)
    assert verdict.code == "H4"
    assert "200000" in verdict.reason


def test_h4_fires_when_the_session_budget_is_spent(tmp_path: Path) -> None:
    verdict = _classify(tmp_path, _state(tmp_path, session_budget_remaining=0))
    assert verdict.code == "H4"
    assert "session_budget_remaining" in verdict.reason


def test_h5_fires_on_a_second_denial_on_the_same_target(tmp_path: Path) -> None:
    state = _state(tmp_path, scope_denials=[{"target": "core/store.py", "count": 2}])
    verdict = _classify(tmp_path, state)
    assert verdict.code == "H5"
    assert "core/store.py" in verdict.reason


def test_h5_does_not_fire_on_a_single_denial(tmp_path: Path) -> None:
    """§2.6: *"One denial means narrow-or-file-a-finding"* — that is not yet a halt."""
    state = _state(tmp_path, scope_denials=[{"target": "core/store.py", "count": 1}])
    assert _classify(tmp_path, state).code == "CONTINUE"


def test_an_empty_scope_denials_list_is_a_real_observation(tmp_path: Path) -> None:
    """⚑ Degenerate input, the `[]`-versus-absent ambiguity again. The supervisor's obligation
    to actually collect denials is carried by the skill; this module's job is to refuse the
    absent case, which it does as H0."""
    assert _classify(tmp_path, _state(tmp_path, scope_denials=[])).code == "CONTINUE"
    state = _state(tmp_path)
    del state["scope_denials"]
    assert _classify(tmp_path, state).code == "H0"


def test_h5_outranks_h4(tmp_path: Path) -> None:
    """Process pressure before budget: a mis-scoped plan is a design fact, an exhausted budget
    is an arithmetic one, and the more informative reason should be the one reported."""
    state = _state(
        tmp_path,
        scope_denials=[{"target": "core/store.py", "count": 3}],
        session_budget_remaining=0,
    )
    assert _classify(tmp_path, state).code == "H5"


# ------------------------------------------------------------------------------------------
# Item 12 — H8, the terminal halt, and the words the classifier cannot say
# ------------------------------------------------------------------------------------------


def _complete(tmp_path: Path, **overrides: object) -> dict[str, object]:
    flags: dict[str, object] = dict.fromkeys(autopilot_halt.COMPLETION_FLAGS, True)
    flags.update(overrides)
    return _state(tmp_path, **flags)


def test_h8_fires_when_all_four_conditions_hold(tmp_path: Path) -> None:
    state = _complete(tmp_path)
    _audit(tmp_path, "audit-bp-999-b", gate="B", artifact="clean")
    verdict = _classify(tmp_path, state)
    assert verdict.code == "H8"


def test_h8_is_a_halt_and_owes_the_five_actions(tmp_path: Path) -> None:
    """§2.6 H8: *"Autopilot then STOPS: no merge, no deskcheck, no self-declared done."*"""
    state = _complete(tmp_path)
    _audit(tmp_path, "audit-bp-999-b", gate="B", artifact="clean")
    verdict = _classify(tmp_path, state)
    assert verdict.halt is True
    assert verdict.actions_owed == autopilot_halt.HALT_ACTIONS
    assert len(verdict.actions_owed) == 5


def test_h8_does_not_fire_with_an_empty_audits_directory(tmp_path: Path) -> None:
    """⚑ THE degenerate input of Item 12. "Gate B is not `concerns`" is TRUE of a directory
    with no Gate B in it, so a negatively-phrased check declares a run complete with **no audit
    at all** — the precise failure §2.7 exists to prevent. The answer is H0, not CONTINUE."""
    verdict = _classify(tmp_path, _complete(tmp_path))
    assert verdict.code == "H0"
    assert verdict.halt is True
    assert "Gate B" in verdict.reason


def test_h8_does_not_fire_on_a_gate_a_record_alone(tmp_path: Path) -> None:
    """A clean Gate A is not a Gate B: the post-build mechanism audit is a separate obligation."""
    state = _complete(tmp_path)
    _audit(tmp_path, "audit-bp-999-a", gate="A", artifact="clean")
    assert _classify(tmp_path, state).code == "H0"


def test_h8_does_not_fire_on_duplicate_gate_b_records(tmp_path: Path) -> None:
    state = _complete(tmp_path)
    _audit(tmp_path, "audit-bp-999-b", gate="B", artifact="clean")
    _audit(tmp_path, "audit-bp-999-b2", gate="B", artifact="clean")
    verdict = _classify(tmp_path, state)
    assert verdict.code == "H0"


def test_h8_does_not_fire_while_any_completion_flag_is_false(tmp_path: Path) -> None:
    for flag in autopilot_halt.COMPLETION_FLAGS:
        state = _complete(tmp_path, **{flag: False})
        _audit(tmp_path, "audit-bp-999-b", gate="B", artifact="clean")
        assert _classify(tmp_path, state).code == "CONTINUE", flag


def test_h8_is_the_last_condition_evaluated(tmp_path: Path) -> None:
    """*"completion last, since completion is only meaningful if nothing else fired."*"""
    state = _complete(tmp_path, scope_denials=[{"target": "x.py", "count": 2}])
    _audit(tmp_path, "audit-bp-999-b", gate="B", artifact="clean")
    assert _classify(tmp_path, state).code == "H5"


def _verdict_code_literals() -> set[str]:
    """Every `code` a `Verdict` can be constructed with, read from the SOURCE rather than from
    behaviour — a code only reachable on an input no test supplies is still a word the module
    can say. Non-literal codes are rejected outright (the sole exception is `_halt`'s own
    pass-through parameter), because a computed code is one this check cannot audit."""
    tree = ast.parse(SOURCE)
    inside_halt = {
        id(node)
        for fn in ast.walk(tree)
        if isinstance(fn, ast.FunctionDef) and fn.name == "_halt"
        for node in ast.walk(fn)
    }
    found: set[str] = set()
    for call in ast.walk(tree):
        if not isinstance(call, ast.Call) or not isinstance(call.func, ast.Name):
            continue
        if call.func.id == "_halt":
            assert call.args, "_halt must be called with a positional code"
            code: ast.expr | None = call.args[0]
        elif call.func.id == "Verdict":
            code = next((kw.value for kw in call.keywords if kw.arg == "code"), None)
        else:
            continue
        if id(call) in inside_halt:
            continue
        assert isinstance(code, ast.Constant) and isinstance(code.value, str), ast.dump(call)
        found.add(code.value)
    return found


def test_the_verdict_vocabulary_is_exactly_continue_and_h0_through_h8() -> None:
    codes = _verdict_code_literals()
    assert codes == set(autopilot_halt.VERDICT_CODES)
    assert codes == {"CONTINUE", "H0", "H1", "H2", "H3", "H4", "H5", "H6", "H7", "H8"}


@pytest.mark.parametrize("word", ["merge", "deskcheck", "done", "complete"])
def test_no_verdict_code_can_say_merge_deskcheck_done_or_complete(word: str) -> None:
    """§1.2 non-goals 5 and 6 enforced by the ABSENCE of a vocabulary word — the cheapest
    possible enforcement, and the only one available to a module that performs no actions."""
    for code in _verdict_code_literals() | set(autopilot_halt.VERDICT_CODES):
        assert word not in code.lower(), code


def test_the_precedence_order_is_the_pinned_one() -> None:
    assert autopilot_halt.PRECEDENCE == (
        "H0",
        "H6",
        "H7",
        "H3",
        "H1",
        "H2",
        "H5",
        "H4",
        "H8",
        "CONTINUE",
    )


# ------------------------------------------------------------------------------------------
# Item 13 — the skill
# ------------------------------------------------------------------------------------------

_FENCE = re.compile(r"^```.*?^```", re.MULTILINE | re.DOTALL)
_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
#: A cited repo-relative path: backticked, contains at least one `/`, ends in a known
#: extension. The `/` requirement is what keeps a bare `autopilot_halt.py` mentioned in prose
#: from being read as a path claim about the repo root.
_CITED = re.compile(
    r"`(\.?[A-Za-z0-9_][A-Za-z0-9_.-]*(?:/[A-Za-z0-9_.-]+)+\.(?:md|py|toml|json|sh|yml|yaml))`"
)

#: The five halt actions, verbatim from §2.6.
FIVE_ACTIONS = autopilot_halt.HALT_ACTIONS

#: §1.2's non-goals, in the words Item 13's acceptance names them.
NON_GOALS = (
    "`draft → ratified` is permanently non-delegable",
    "autopilot never originates a goal",
    "autopilot never merges to main",
    "`deploy` stays owner-in-loop",
    "the deskcheck is never delegable",
    "one grant, one plan",
)

EXIT_SENTENCE = "exit 1 from `autopilot_halt.py` means HALT, the safe outcome"


def _prose(text: str) -> str:
    """The skill's RENDERED prose: fenced code blocks and HTML comments removed. ⚑ Degenerate
    input for Item 13 — a `substring in text` check passes on a required literal parked inside
    a comment or an example block, which is prose that is not in force."""
    return _FENCE.sub("", _COMMENT.sub("", text))


def _cited_paths(text: str) -> list[str]:
    """Every repo-relative path the text cites in backticks, `:NN` line suffixes stripped."""
    return sorted({m.group(1) for m in _CITED.finditer(text)})


def test_the_skill_exists_with_standard_front_matter() -> None:
    assert SKILL.is_file(), f"{SKILL} does not exist"
    text = SKILL.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    front = text.split("---", 2)[1]
    assert re.search(r"^name:\s*autopilot\s*$", front, re.MULTILINE), front
    assert re.search(r"^description:\s*\S", front, re.MULTILINE), front


@pytest.mark.parametrize("code", ["H1", "H2", "H3", "H4", "H5", "H6", "H7", "H8"])
def test_the_skill_states_every_halt_code(code: str) -> None:
    assert code in _prose(SKILL.read_text(encoding="utf-8"))


@pytest.mark.parametrize("action", FIVE_ACTIONS)
def test_the_skill_carries_the_five_halt_actions_verbatim(action: str) -> None:
    """The classifier decides; the SKILL carries the five actions as an obligation on the
    supervisor. If the two ever disagree, the skill is authoritative for behaviour."""
    assert action in _prose(SKILL.read_text(encoding="utf-8"))


@pytest.mark.parametrize("non_goal", NON_GOALS)
def test_the_skill_carries_the_non_goals(non_goal: str) -> None:
    assert non_goal in _prose(SKILL.read_text(encoding="utf-8"))


def test_the_skill_states_the_exit_inversion_literally() -> None:
    """A caller that treats non-zero as "the tool broke" and proceeds has inverted the entire
    mechanism, so the operating contract must say so in words."""
    assert EXIT_SENTENCE in _prose(SKILL.read_text(encoding="utf-8"))


@pytest.mark.parametrize("skill", ["graduate", "delegate", "finding"])
def test_the_skill_cross_references_its_neighbours(skill: str) -> None:
    assert f".claude/skills/{skill}/SKILL.md" in _prose(SKILL.read_text(encoding="utf-8"))


def test_every_relative_path_the_skill_cites_resolves() -> None:
    """`CONSTITUTION.md` §III.1 — *"A cited identifier that does not resolve is a failure"* —
    applied to the skill's own citations."""
    cited = _cited_paths(SKILL.read_text(encoding="utf-8"))
    assert cited, "the skill cites no paths at all — the check would be vacuous"
    unresolved = [p for p in cited if not (REPO / p).exists()]
    assert not unresolved, f"the autopilot skill cites paths that do not exist: {unresolved}"


def test_the_link_resolution_check_reddens_on_a_fabricated_path() -> None:
    """⚑ Degenerate input — the link check must be able to FAIL, or its green means nothing."""
    text = SKILL.read_text(encoding="utf-8") + "\n\nSee `docs/design-notes/dn-not-a-note.md`.\n"
    unresolved = [p for p in _cited_paths(text) if not (REPO / p).exists()]
    assert unresolved == ["docs/design-notes/dn-not-a-note.md"]


def test_the_prose_check_ignores_comments_and_code_fences() -> None:
    """⚑ Degenerate input — a skill file containing every required literal inside an HTML
    comment or a fenced block would pass a naive `substring in text` check. Prove the stripper
    works by moving a required literal into each, and asserting the check reddens."""
    assert EXIT_SENTENCE in _prose(SKILL.read_text(encoding="utf-8"))
    commented = f"# skill\n\n<!--\n{EXIT_SENTENCE}\n-->\n"
    assert EXIT_SENTENCE in commented and EXIT_SENTENCE not in _prose(commented)
    fenced = f"# skill\n\n```\n{EXIT_SENTENCE}\n```\n"
    assert EXIT_SENTENCE in fenced and EXIT_SENTENCE not in _prose(fenced)
    for non_goal in NON_GOALS:
        parked = f"# skill\n\n<!-- {non_goal} -->\n"
        assert non_goal in parked and non_goal not in _prose(parked)


@pytest.mark.parametrize("phrase", ['needs an "and"', "sprawls across zones"])
def test_the_skill_links_the_session_sizing_heuristic_rather_than_restating_it(
    phrase: str,
) -> None:
    """⚑ FALSIFIER for Item 13. Two copies of a heuristic drift, and a drifted router sends
    design-scale work into autopilot — the one thing §2.2's router exists to prevent. A hit on
    either distinctive phrase IS the falsifier firing. (The phrases are live in
    `.claude/skills/graduate/SKILL.md`, so this test also fails if that file loses them.)"""
    graduate = (REPO / ".claude" / "skills" / "graduate" / "SKILL.md").read_text(encoding="utf-8")
    assert phrase in graduate, "the heuristic moved; re-anchor this falsifier"
    assert phrase not in SKILL.read_text(encoding="utf-8")


# ------------------------------------------------------------------------------------------
# The tooling invariant — stdlib plus `_lib`, and no writer of any kind
# ------------------------------------------------------------------------------------------


def test_the_classifier_imports_stdlib_only_plus_the_sanctioned_lib_reuse() -> None:
    """The `test_capsule.py:414-431` AST precedent. `ast.walk` catches imports nested in
    function bodies, not just module-level ones. `_lib` is the ONE non-stdlib name: re-deriving
    a front-matter parser is a DRY defect (`CONVENTIONS.md`), and importing it is how
    `scripts/board.py:33-38` already does this."""
    tree = ast.parse(SOURCE)
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name.split(".")[0])

    allowed = {"__future__", "argparse", "json", "sys", "dataclasses", "pathlib", "_lib"}
    assert imported <= allowed, f"unexpected imports: {imported - allowed}"
    for forbidden in ("core", "config", "os", "subprocess", "keyring", "hmac", "hashlib"):
        assert forbidden not in imported, f"the halt classifier must never import {forbidden}"


def test_the_classifier_never_writes() -> None:
    """A halt classifier needs no authority whatsoever to do its job (§9 non-goal 7): no
    secret, no MFA code, no power to flip a status — and no writer, which is what makes
    "budget is not self-extendable" structural rather than a promise."""
    for writer in ("write_text", "write_bytes", "open(", "unlink", "rename", "mkdir", "rmtree"):
        assert writer not in SOURCE, f"the halt classifier must not call {writer}"


def test_the_classifier_computes_no_grant_validity(tmp_path: Path) -> None:
    """Item 11's invariant: `grant_valid` is DATA — the module contains no cryptography and
    calls nothing that could produce any. That independence from bp-138 is what lets the halt
    list ship before the grant's cryptography exists (`bp-135` §12)."""
    tree = ast.parse(SOURCE)
    called = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    } | {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    for crypto in ("sha256", "new", "compare_digest", "hexdigest", "digest", "urandom"):
        assert crypto not in called, f"the halt classifier must not call {crypto}"
    # ... and it is answered purely from the declaration, whatever the world looks like.
    assert _classify(tmp_path, _state(tmp_path, grant_checked=False)).code == "H7"


# ------------------------------------------------------------------------------------------
# CLI — the exit inversion, and the `explain` surface that exists to catch it
# ------------------------------------------------------------------------------------------


def test_cli_exits_1_on_a_halt_and_prints_code_and_reason(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """⚑ EXIT 1 MEANS HALT — THE SAFE OUTCOME."""
    path = tmp_path / "run-state.json"
    path.write_text(json.dumps({}), encoding="utf-8")
    assert autopilot_halt.main(["classify", str(path), "--root", str(tmp_path)]) == 1
    assert capsys.readouterr().out.startswith("H0: ")


def test_cli_exits_0_on_continue(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "run-state.json"
    path.write_text(json.dumps(_state(tmp_path)), encoding="utf-8")
    assert autopilot_halt.main(["classify", str(path), "--root", str(tmp_path)]) == 0
    assert capsys.readouterr().out.startswith("CONTINUE: ")


def test_cli_reads_stdin(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    import io

    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps({"plan": "bp-999"})))
    assert autopilot_halt.main(["classify", "-", "--root", str(tmp_path)]) == 1
    assert capsys.readouterr().out.startswith("H0: ")


def test_cli_missing_state_file_is_h0_not_a_traceback(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert autopilot_halt.main(["classify", str(tmp_path / "nope.json")]) == 1
    assert capsys.readouterr().out.startswith("H0: ")


def test_cli_explain_prints_the_codes_the_order_and_the_inversion(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert autopilot_halt.main(["explain"]) == 0
    out = capsys.readouterr().out
    assert "EXIT 1 MEANS HALT, WHICH IS THE SAFE OUTCOME." in out
    for code in autopilot_halt.VERDICT_CODES:
        assert code in out
    assert " -> ".join(autopilot_halt.PRECEDENCE) in out
    for action in autopilot_halt.HALT_ACTIONS:
        assert action in out
