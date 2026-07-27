"""F1b — the seat-narrative purity lint, and the future-dated readings check (bp-127 Item 15).

`dn-role-state-and-scoped-handoff` §2.11: *"zero word-bounded `[0-9a-f]{7,40}` tokens and zero
`status:`-transition phrases in the seat journal's authoritative segment (capsule + suffix);
hit = FAIL."* §2.5 is the rule it enforces: narrative names artifacts by stable id and never
states a machine-derivable value.

⚑ **This file is written to the false-success rule**, because a lint is exactly the artifact class
that rule exists for: *every check here has an input on which it passes without testing its claim,
and each such input is named and asserted to redden.* The four that matter:

  * **D1 — the inverted direction.** §2.8 states the authority rule TEMPORALLY ("the latest capsule
    plus all entries *after* it"); the seat journal is NEWEST-FIRST, so "after" is *above*.
    Implementing the sentence physically (`lines[capsule:]`) lints the history nobody may edit,
    ignores the live narrative anyone can write, and **reports green**. Pinned by putting the SAME
    token above and below one capsule and asserting opposite verdicts.
  * **D2 — the unanchored marker.** `## CAPSULE` unanchored matches the journal's own prose
    *defining* the marker (4 hits on a file with 0 capsules — finding-0242, finding-0251), which
    scopes the lint to an arbitrary fragment and passes green.
  * **D3 — the empty segment.** No narrative ⇒ nothing to be pure about ⇒ "0 violations" is not
    evidence. Reported INDETERMINATE (rc 3), never clean.
  * **D4 — the dropped `\\b`.** Without the word boundary the pattern fires inside ordinary words,
    the lint cries wolf on legitimate judgement, and people learn to ignore it (Item 15's own
    falsifier). Pinned from the other side: an embedded hex run must PASS.

⚑ **What this file deliberately does NOT assert: that the live seat journal is clean.** It is not.
A correct F1b FAILS on it today with 6 hits (finding-0251, re-measured this session). The plan's
Item 15 acceptance said "the live journal's authoritative segment → PASS"; that acceptance is
falsified by measurement, and the honest resolution is to keep the pattern and record the verdict,
never to narrow the pattern or the segment until the artifact passes. The live file gets the
assertions that are *true and stable* — the lint runs on it, it is non-vacuous, and its segment
covers the whole file while no capsule exists — and its red verdict lives in `readings.md` and the
bp-127 journal, where a measurement belongs.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

import handoff  # type: ignore[import-not-found]  # noqa: E402

SHA = "a1b2c3d"  # 7 hex, word-bounded — the smallest thing §2.11 forbids
CAPSULE = "## CAPSULE — 2026-07-27"


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True)


def _commit(cwd: Path, epoch: int) -> None:
    """A commit at a PINNED time — the readings lint compares against committer-time, so the test
    fixes both sides rather than racing the wall clock."""
    subprocess.run(["git", "-C", str(cwd), "commit", "-q", "-m", "seed"], check=True,
                   capture_output=True,
                   env={"GIT_COMMITTER_DATE": f"{epoch} +0000", "GIT_AUTHOR_DATE": f"{epoch} +0000",
                        "PATH": "/usr/bin:/bin", "HOME": str(cwd)})


def _journal(*entries: str) -> str:
    """A seat journal in the real idiom: a preamble, then entries NEWEST-FIRST."""
    return "\n".join(["---", "type: seat-journal", "seat: orchestrator", "---", "",
                      "# Seat journal — orchestrator", "",
                      "Append-only: entries are added at the top.", "", *entries]) + "\n"


# ── the segment: direction and anchoring ────────────────────────
def test_no_capsule_means_the_whole_file_is_authoritative():
    """finding-0242(a): zero capsules is the NORMAL state until the first compaction, not an
    error — so the lint must fall back to the whole file rather than to nothing."""
    lines = _journal("## 2026-07-27 — an entry", "", "judgement about bp-110").splitlines()
    segment, capsule = handoff.authoritative_segment(lines)
    assert capsule is None
    assert segment == lines


def test_the_segment_is_the_capsule_plus_everything_above_it():
    lines = _journal("## 2026-07-27 — newest", "", CAPSULE, "",
                     "## 2026-07-01 — history").splitlines()
    segment, capsule = handoff.authoritative_segment(lines)
    assert lines[capsule - 1] == CAPSULE            # 1-based, and it IS the capsule line
    assert segment[-1] == CAPSULE                   # inclusive of the capsule
    assert "## 2026-07-27 — newest" in segment      # live narrative is IN
    assert "## 2026-07-01 — history" not in segment  # history is OUT


def test_the_latest_capsule_is_the_topmost_one():
    """Entries are prepended, so the NEWEST capsule is the one physically highest. Bounding on the
    last match instead would carry two capsules' worth of demoted history back into the segment."""
    lines = _journal("newest", "", CAPSULE, "", "middle", "",
                     "## CAPSULE — 2026-07-01", "", "oldest").splitlines()
    segment, capsule = handoff.authoritative_segment(lines)
    assert lines[capsule - 1] == CAPSULE
    assert "middle" not in segment and "oldest" not in segment


# ⚑ D1 — THE INVERTED DIRECTION. One token, two positions, opposite verdicts.
def test_a_hash_ABOVE_the_capsule_fails():
    res = handoff.lint_narrative(_journal(f"live narrative citing `{SHA}`", "", CAPSULE, "", "old"))
    assert not res.ok
    assert [v.token for v in res.violations] == [SHA]


def test_the_same_hash_BELOW_the_capsule_passes():
    """History is not back-filled (the readmap precedent, note §2.11). Together with the test
    above this is the direction pin: an implementation of `lines[capsule:]` inverts BOTH."""
    res = handoff.lint_narrative(_journal("live narrative", "", CAPSULE, "", f"old text `{SHA}`"))
    assert res.ok, [v.token for v in res.violations]


# ⚑ D2 — THE UNANCHORED MARKER.
def test_prose_mentioning_the_marker_does_not_bound_the_segment():
    text = _journal(f"the marker is the literal heading `## CAPSULE — <date>`, and `{SHA}` leaked")
    assert "## CAPSULE" in text                    # an unanchored grep WOULD match
    segment, capsule = handoff.authoritative_segment(text.splitlines())
    assert capsule is None                          # …but an anchored one does not
    assert not handoff.lint_narrative(text).ok      # so the violation is still in scope


def test_the_capsule_pattern_is_itself_anchored():
    """⚑ Pins the CONSTANT, not just its current caller. `CAPSULE_RE.match` anchors on its own, so
    a mutant that deletes the `^` is invisible through `authoritative_segment` — the two guards
    mask each other and the campaign cannot tell "doubly protected" from "untested". `CAPSULE_RE`
    is module-level and exported; the next consumer may reach for `.search`."""
    assert handoff.CAPSULE_RE.search(f"> the marker is `{CAPSULE}`") is None
    assert handoff.CAPSULE_RE.search(f"  {CAPSULE}") is None
    assert handoff.CAPSULE_RE.search(CAPSULE) is not None


def test_an_indented_or_quoted_marker_does_not_bound_the_segment():
    for prefix in ("> ", "  ", "…see "):
        text = _journal(f"{prefix}## CAPSULE — 2026-07-27", "", f"and `{SHA}` below it")
        assert handoff.authoritative_segment(text.splitlines())[1] is None
        assert not handoff.lint_narrative(text).ok, prefix


# ── what fires and what must not ────────────────────────────────
def test_stable_ids_are_never_violations():
    """§2.5: the id IS the join key. A lint that fired on these would forbid the very thing the
    rule prescribes."""
    res = handoff.lint_narrative(_journal(
        "bp-110 is bigger than priced; see finding-0227 and oq-0051 (also dn-role-state)."))
    assert res.ok, [v.token for v in res.violations]


# ⚑ D4 — THE DROPPED `\b`, from the cry-wolf side.
@pytest.mark.parametrize("word", ["xdeadbeefx", "cafebabe1234z", "prefixaccede9suffix"])
def test_hex_runs_inside_ordinary_words_do_not_fire(word):
    assert handoff.lint_narrative(_journal(f"a word: {word}")).ok


@pytest.mark.parametrize("token",
                         ["a1b2c3d", "deadbeef", "0123456789abcdef0123456789abcdef01234567"])
def test_word_bounded_hex_of_7_to_40_fires(token):
    res = handoff.lint_narrative(_journal(f"Head `{token}`, pushed."))
    assert [v.token for v in res.violations] == [token]


@pytest.mark.parametrize("token", ["a1b2c3", "0123456789abcdef0123456789abcdef012345678"])
def test_hex_outside_the_7_to_40_window_does_not_fire(token):
    assert handoff.lint_narrative(_journal(f"a token {token} here")).ok


@pytest.mark.parametrize("phrase", [
    "status: ready", "status:in-progress", "Status: Complete",
    "proposed → ready", "draft→ratified", "in-progress -> complete",
])
def test_status_transition_phrasing_fires(phrase):
    res = handoff.lint_narrative(_journal(f"I flipped it — {phrase} — and moved on."))
    assert [v.kind for v in res.violations] == ["status"], phrase


@pytest.mark.parametrize("phrase", [
    "the plan is ready to build", "a draft I will complete", "the status of the wave",
    "build → audit → possible return", "proposed a different split",
    # ⚑ BOTH SIDES of the arrow must be statuses, or the lint fires on any sentence that happens
    # to start a clause with a status word — a cry-wolf widening that mutation caught (M12).
    "ready → I spawned the wave", "complete → then the deskcheck",
    # ⚑ And `status:` must be followed by a STATUS, not by anything at all (M15). Narrative may
    # legitimately write the word; what §2.5 forbids is stating the machine-derivable VALUE.
    "status: see the board", "status: whatever the docket says",
])
def test_ordinary_narrative_about_work_does_not_fire(phrase):
    """The honest tier (LINT_TIER): the English 'X to Y' form is NOT matched, because `to` collides
    with ordinary judgement and a lint that cries wolf gets suppressed — and then the rule is gone.
    Recorded as a deliberate limit, not an oversight."""
    assert handoff.lint_narrative(_journal(phrase)).ok, phrase


def test_the_lint_reports_every_violation_not_just_the_first():
    res = handoff.lint_narrative(_journal(f"`{SHA}` and `deadbeef` and status: ready"))
    assert len(res.violations) == 3


def test_violation_line_numbers_are_absolute_in_the_file():
    text = _journal("first", "", f"`{SHA}`")
    res = handoff.lint_narrative(text, "j.md")
    assert text.splitlines()[res.violations[0].line - 1].strip() == f"`{SHA}`"
    assert res.violations[0].render("j.md").startswith(f"j.md:{res.violations[0].line}: hex:")


# ⚑ D3 — THE EMPTY SEGMENT: a clean verdict over nothing is not evidence.
def test_an_empty_segment_is_indeterminate_not_clean():
    res = handoff.lint_narrative(f"{CAPSULE}\n\nall of this is history `{SHA}`\n")
    assert res.violations == ()          # nothing IS in scope…
    assert res.vacuous                    # …and that is exactly why it cannot be a pass
    assert not res.ok


def test_an_empty_file_is_indeterminate_not_clean():
    for text in ("", "\n\n\n", "   \n\t\n"):
        assert not handoff.lint_narrative(text).ok


def test_a_segment_with_narrative_is_not_vacuous():
    assert not handoff.lint_narrative(_journal("a real judgement about bp-110")).vacuous


# ── the CLI: three distinguishable verdicts ─────────────────────
def _seat(root: Path, journal: str, readings: str = "") -> None:
    seat = root / "docs" / "roles" / "orchestrator"
    seat.mkdir(parents=True, exist_ok=True)
    (seat / "journal.md").write_text(journal, encoding="utf-8")
    if readings:
        (seat / "readings.md").write_text(readings, encoding="utf-8")


def test_cmd_lint_exit_codes(git_seat, capsys):
    """0 clean / 1 violation / 3 indeterminate. The third is the false-success guard: a check that
    could not RUN must never be indistinguishable from one that ran and found nothing."""
    _seat(git_seat, _journal("clean judgement about bp-110"))
    assert handoff.cmd_lint(git_seat, "orchestrator") == handoff.LINT_CLEAN
    _seat(git_seat, _journal(f"leaked `{SHA}`"))
    assert handoff.cmd_lint(git_seat, "orchestrator") == handoff.LINT_VIOLATION
    _seat(git_seat, f"{CAPSULE}\n\nhistory only\n")
    assert handoff.cmd_lint(git_seat, "orchestrator") == handoff.LINT_INDETERMINATE
    out = capsys.readouterr()
    assert "LINTABLE CLASS ONLY" in out.out, "the lint must never overclaim its tier (R2)"


def test_an_absent_readings_log_is_indeterminate_not_clean(tmp_path):
    """⚑ Another degenerate input: the seat has no readings log, so no row can be future-dated and
    the check trivially "passes". It must not — a mis-pointed path lands here identically."""
    _seat(tmp_path, _journal("clean judgement about bp-110"))
    assert not (tmp_path / "docs" / "roles" / "orchestrator" / "readings.md").exists()
    assert handoff.cmd_lint(tmp_path, "orchestrator") == handoff.LINT_INDETERMINATE


@pytest.fixture
def git_seat(tmp_path):
    """A seat inside a REAL repo with an honest, committed readings log — so the CLI's journal
    verdict is not swamped by an unanswerable readings check."""
    _git(tmp_path, "init", "-q", "-b", "main", str(tmp_path))
    for k, v in (("user.email", "t@t"), ("user.name", "t")):
        _git(tmp_path, "config", k, v)
    seat = tmp_path / "docs" / "roles" / "orchestrator"
    seat.mkdir(parents=True)
    (seat / "readings.md").write_text(
        "| timestamp | command | result |\n|---|---|---|\n"
        "| 2026-07-27T03:56Z | uv run pytest -q | honest |\n", encoding="utf-8")
    (seat / "journal.md").write_text(_journal("seed"), encoding="utf-8")
    _git(tmp_path, "add", "docs")
    _commit(tmp_path, 1785128160)
    return tmp_path


def test_cmd_lint_reports_a_missing_journal_as_indeterminate(tmp_path):
    (tmp_path / "docs" / "roles" / "orchestrator").mkdir(parents=True)
    assert handoff.cmd_lint(tmp_path, "orchestrator") == handoff.LINT_INDETERMINATE


def test_lint_is_role_only_and_writes_nothing(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(handoff, "ROOT", tmp_path)
    (tmp_path / "docs" / "tracks").mkdir(parents=True)
    (tmp_path / "docs" / "tracks" / "alpha.md").write_text(
        "---\ntype: track\nslug: alpha\nstatus: active\n---\n", encoding="utf-8")
    assert handoff.main(["--track", "alpha", "--lint"]) == 2
    assert not (tmp_path / "docs" / "roles").exists()
    capsys.readouterr()


# ── the future-dated readings lint (finding-0243) ───────────────
def _row(line: int, stamp: str, epoch: int, sha: str = "b" * 40) -> handoff.BlamedRow:
    return handoff.BlamedRow(line, stamp, sha, epoch)


def test_a_row_stamped_after_its_own_commit_is_flagged():
    # 2026-07-27T04:56Z == 1785128160; the commit landed 55 min earlier.
    ahead = handoff.future_dated([_row(1, "2026-07-27T04:56Z", 1785128160 - 55 * 60)])
    assert [lead for _r, lead in ahead] == [55 * 60]


def test_a_row_stamped_before_its_commit_is_fine():
    assert handoff.future_dated([_row(1, "2026-07-27T04:00Z", 1785128160)]) == []


def test_the_tolerance_is_exactly_one_stamp_quantum():
    """Rows carry MINUTE precision, so an honestly-read stamp can round up to a minute ahead. The
    allowance is fixed by the format, not by what makes the live file pass — its leads run to 55
    minutes and stay red either way."""
    base = 1785128160
    at = handoff.STAMP_PRECISION_SECONDS
    assert handoff.future_dated([_row(1, "2026-07-27T04:56Z", base - at)]) == []
    assert handoff.future_dated([_row(1, "2026-07-27T04:56Z", base - at - 1)]) != []


def test_an_uncommitted_line_is_skipped_not_flagged():
    """A working-tree line has no introducing commit yet, so the question is not yet askable."""
    assert handoff.future_dated([_row(1, "2026-07-27T23:59Z", 0, sha="0" * 40)]) == []


def test_an_unparseable_stamp_is_skipped():
    assert handoff.future_dated([_row(1, "yesterday", 0)]) == []


@pytest.mark.parametrize("line,expected", [
    ("| 2026-07-27T04:56Z | uv run pytest -q | 2 failed |", "2026-07-27T04:56Z"),
    ("| timestamp | command | result |", None),
    ("|---|---|---|", None),
    ("just prose", None),
    ("| only | two |", None),
])
def test_row_detection_matches_the_pane_s_own(line, expected):
    """The lint and `read_readings` must agree about what a row IS, or the lint checks rows the
    pane never renders (or misses ones it does)."""
    assert handoff._row_stamp(line) == expected


def test_blame_parsing_against_a_real_repo(tmp_path):
    """⚑ The git half gets its own test. A pure comparator with an unproven blame parse is exactly
    the false-success shape: the observable would not be causally downstream of the claim."""
    _git(tmp_path, "init", "-q", "-b", "main", str(tmp_path))
    for k, v in (("user.email", "t@t"), ("user.name", "t")):
        _git(tmp_path, "config", k, v)
    seat = tmp_path / "docs" / "roles" / "orchestrator"
    seat.mkdir(parents=True)
    rpath = seat / "readings.md"
    # One honest row (stamped an hour BEFORE its commit) and one composed row (an hour after).
    commit_epoch = 1785128160
    rpath.write_text("| timestamp | command | result |\n|---|---|---|\n"
                     "| 2026-07-27T03:56Z | uv run pytest -q | honest |\n"
                     "| 2026-07-27T05:56Z | uv run ruff check . | composed |\n", encoding="utf-8")
    (seat / "journal.md").write_text(_journal("clean judgement about bp-110"), encoding="utf-8")
    _git(tmp_path, "add", "docs")
    _commit(tmp_path, commit_epoch)
    rows = handoff.blame_readings(tmp_path, rpath)
    assert rows is not None and len(rows) == 2, rows
    assert [r.stamp for r in rows] == ["2026-07-27T03:56Z", "2026-07-27T05:56Z"]
    assert {r.commit_epoch for r in rows} == {commit_epoch}
    assert [r.line for r in rows] == [3, 4], "blame line numbers must be 1-based file positions"
    ahead = handoff.future_dated(rows)
    assert [r.stamp for r, _ in ahead] == ["2026-07-27T05:56Z"]
    assert handoff.cmd_lint(tmp_path, "orchestrator") == handoff.LINT_VIOLATION


def test_blame_outside_a_repo_is_indeterminate_not_clean(tmp_path):
    """⚑ The degenerate input for the readings half: no git ⇒ the question cannot be asked. It
    must not read as 'no future-dated rows'."""
    seat = tmp_path / "docs" / "roles" / "orchestrator"
    seat.mkdir(parents=True)
    (seat / "journal.md").write_text(_journal("clean judgement about bp-110"), encoding="utf-8")
    (seat / "readings.md").write_text("| timestamp | command | result |\n", encoding="utf-8")
    assert handoff.blame_readings(tmp_path, seat / "readings.md") is None
    assert handoff.cmd_lint(tmp_path, "orchestrator") == handoff.LINT_INDETERMINATE


# ── the threshold instrument (finding-0245) ─────────────────────
def test_segment_line_count_is_measured_not_remembered(tmp_path):
    def _total() -> int:
        return len((tmp_path / "docs" / "roles" / "orchestrator" / "journal.md")
                   .read_text(encoding="utf-8").splitlines())

    _seat(tmp_path, _journal("a", "", "b"))
    assert handoff.journal_segment_lines(tmp_path, "orchestrator") == _total()
    # A capsule bounds it: the segment must now be strictly SHORTER than the file it lives in.
    _seat(tmp_path, _journal("a", "", CAPSULE, "", "history", "", "more history"))
    assert 0 < handoff.journal_segment_lines(tmp_path, "orchestrator") < _total()


def test_a_missing_journal_measures_zero_rather_than_raising(tmp_path):
    assert handoff.journal_segment_lines(tmp_path, "orchestrator") == 0


def test_the_threshold_is_surfaced_in_the_live_render_only(tmp_path, monkeypatch):
    """⚑ LIVE only, deliberately: the committed rendering is clause (e′) check 1's subject, and a
    value that moves on every journal append would arm that check on every narrative entry."""
    _seat(tmp_path, _journal(*["line" for _ in range(handoff.SEGMENT_THRESHOLD + 20)]))
    monkeypatch.setattr(handoff.board, "_build", lambda _r: ({}, {}, []))
    scope = handoff.resolve(tmp_path, "role", "orchestrator")
    live = handoff.handoff_text(tmp_path, scope, live=True)
    assert "Active segment:" in live and "⚑ OVER" in live
    assert "Active segment:" not in handoff.handoff_text(tmp_path, scope)


def test_the_threshold_is_in_the_structured_answer(tmp_path, monkeypatch):
    _seat(tmp_path, _journal("a", "", "b"))
    monkeypatch.setattr(handoff.board, "_build", lambda _r: ({}, {}, []))
    import json as _json
    scope = handoff.resolve(tmp_path, "role", "orchestrator")
    data = _json.loads(handoff.answer_json(tmp_path, scope))
    assert data["journal_segment_lines"] == handoff.journal_segment_lines(tmp_path, "orchestrator")
    assert handoff.answer_json(tmp_path, scope) == handoff.answer_json(tmp_path, scope)


# ── the live artifact: what is TRUE of it, not what we wish ─────
def test_the_lint_runs_on_the_live_seat_journal_and_is_not_vacuous():
    """⚑ Not an assertion that the live file is CLEAN — it is not (finding-0251: 6 hits, and a
    correct F1b reddens on it today). This asserts the two things that ARE true and stable: the
    lint can answer for the real artifact, and its answer is not the degenerate one. A
    mis-anchored or direction-inverted implementation collapses this segment to a fragment and
    trips the second assertion."""
    path = REPO / "docs" / "roles" / "orchestrator" / "journal.md"
    text = path.read_text(encoding="utf-8")
    res = handoff.lint_narrative(text, str(path))
    assert not res.vacuous
    if res.capsule_line is None:
        assert res.segment_lines == len(text.splitlines()), \
            "with no capsule the WHOLE file is authoritative (finding-0242a)"
    else:
        assert 0 < res.segment_lines <= len(text.splitlines())
        assert text.splitlines()[res.capsule_line - 1].startswith("## CAPSULE")


def test_the_live_seat_journal_carries_no_status_transition_phrasing():
    """The half of §2.11 the live artifact DOES satisfy — asserted so a regression in it is caught,
    while the hex half stays a recorded measurement rather than a wished-for green."""
    res = handoff.lint_narrative(
        (REPO / "docs" / "roles" / "orchestrator" / "journal.md").read_text(encoding="utf-8"))
    assert [v for v in res.violations if v.kind == "status"] == []
