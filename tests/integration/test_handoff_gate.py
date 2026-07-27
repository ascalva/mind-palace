"""Session-handoff gate — ``cmd_stop_audit`` clause (e′).

Clause (e′) (``dn-role-state-and-scoped-handoff`` §2.10) **supersedes** clause (e) of
``dn-session-handoff-gate`` §2.2-2.3, which this file previously pinned. (e) blocked an
orchestrator close on the **mtime** of an unversioned state file, and its reason demanded a
hand-authored rewrite citing the final commit hashes — a doubly circular condition that fired
108 times in 8 days. (e′) keeps the *trigger* and replaces the *demand* with two checks that
are dischargeable by construction:

    BLOCK  iff  HEAD != content(.claude/state/session-baseline)      # commits this session
           and  plan is None                                        # orchestrator posture
           and  isdir(docs/roles/orchestrator)                      # the seat exists
           and  (  regenerating docs/roles/orchestrator/handoff.md is NOT a no-op   # check 1
                or mtime(docs/roles/orchestrator/journal.md)
                       < mtime(.claude/state/session-baseline) )                    # check 2

with: check 1 delegated to ``scripts/handoff.py --role orchestrator --check`` and **never**
re-implemented here (finding-0236 — that entry point renders TREE-PURE, so the *work* re-arms
the gate and the daemon never can); check 2 keyed to **session start**, not last-commit, so a
late commit cannot re-arm it; **MEASURED (``readings.md``) deliberately ungated** (§2.10.3);
and fail-open on every unevaluable signal — a missing/unreadable ``session-baseline``, an
absent seat directory, or any generator error.

Mirrors ``test_worktree_enforcement.py``'s pattern: a self-contained throwaway git repo,
``_lib.py stop-audit`` invoked with ``CLAUDE_PROJECT_DIR`` set, asserting on the
``ALLOW``/``BLOCK:`` decision line. **The clause is proven here before it is trusted to govern
a real session's close** (plan bp-126 Item 12).

The six cases this file pinned for (e) all survive, three unchanged and three re-expressed —
none is deleted, because their regression value is the *posture* coverage:

  (3) allow on no-commits                  -> survives verbatim as a posture invariant
  (5) fail-open allow on missing baseline  -> survives verbatim as a posture invariant
  (6) silent under an active plan          -> survives verbatim as a posture invariant
  (1) block on commits + stale brief       -> re-expressed twice: a stale DERIVED rendering
                                              (e′-1) and a NARRATIVE entry older than session
                                              start (e′-2)
  (2) block on commits + missing brief     -> re-expressed as a missing seat journal (the
                                              "infinitely stale" heir), plus the new fail-open
                                              cases that bound it
  (4) allow on fresh brief                 -> re-expressed as (e′-3): fresh rendering + an
                                              entry written this session

and four properties (e) could not have had are pinned for the first time:

  (e′-4)  a stale MEASURED readings log NEVER blocks — the explicit negative
  convergence  block -> regenerate -> commit -> close -> ALLOW, in ONE step (the falsifier
               that decides whether the circularity was removed or merely re-clothed)
  fail-open   an absent generator, and an absent seat directory, both ALLOW

No test reads the real repo's ``.claude/state/**``; every fixture is under ``tmp_path``.
``.claude/state/`` is gitignored in the fixture (as in the real repo) so runtime state never
enters the (b) out-of-scope audit.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import time
from pathlib import Path

import pytest

# The code under test: this worktree's own hooks (same convention as
# test_worktree_enforcement.py). ``scripts/handoff.py`` and its ``board`` dependency are
# copied too — clause (e′) check 1 shells out to the generator, so a fixture without it would
# exercise only the fail-open path and prove nothing about the check.
_REPO = Path(__file__).resolve().parents[2]
_HOOKS_SRC = _REPO / ".claude" / "hooks"
_SCRIPTS_SRC = _REPO / "scripts"

_SEAT = "docs/roles/orchestrator"


def _git(cwd: Path, *args: str, at: float | None = None) -> subprocess.CompletedProcess[str]:
    """``at`` pins the commit's author+committer epoch. Needed to separate *session start*
    from *last commit* on the timeline — without it both land in the same wall-clock second
    and a check keyed to the wrong one passes vacuously."""
    env = dict(os.environ)
    if at is not None:
        env["GIT_AUTHOR_DATE"] = env["GIT_COMMITTER_DATE"] = f"@{int(at)} +0000"
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )


def _plan(plan_id: str, write_scope: list[str]) -> str:
    ws = "\n".join(f'  - "{p}"' for p in write_scope)
    return (
        "---\n"
        "type: build-plan\n"
        f"id: {plan_id}\n"
        "status: in-progress\n"
        "contract: builder\n"
        "write_scope:\n"
        f"{ws}\n"
        "---\n\n"
        f"# {plan_id}\n"
    )


@pytest.fixture
def handoff_repo(tmp_path: Path):
    """A self-contained git repo in orchestrator posture (empty active-plan pointer) carrying
    a real orchestrator seat: ``journal.md``, ``readings.md`` and a generated ``handoff.md``.
    ``.claude/state/`` is gitignored so runtime files never appear in the (b) out-of-scope
    audit. Returns control helpers + a ``run`` invoking ``_lib.py stop-audit`` with
    ``CLAUDE_PROJECT_DIR`` set to the repo root.

    Mtimes are stamped explicitly rather than left to wall-clock ordering: ``session_start``
    pins ``session-baseline`` at ``t0`` and the journal helpers stamp relative to it, so the
    session-start key is exact regardless of filesystem timestamp granularity."""
    root = tmp_path / "main"
    root.mkdir()
    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "user.email", "t@t")
    _git(root, "config", "user.name", "t")

    (root / ".claude" / "hooks").mkdir(parents=True)
    for f in _HOOKS_SRC.glob("*.py"):
        shutil.copy(f, root / ".claude" / "hooks" / f.name)
    (root / "scripts").mkdir()
    for name in ("handoff.py", "board.py"):
        shutil.copy(_SCRIPTS_SRC / name, root / "scripts" / name)
    (root / ".claude" / "state").mkdir(parents=True)
    (root / ".claude" / "state" / "active-plan").write_text("")  # orchestrator posture
    (root / ".gitignore").write_text(".claude/state/\n")
    (root / "seed.txt").write_text("seed\n")

    seat = root / _SEAT
    seat.mkdir(parents=True)
    (seat / "journal.md").write_text(
        "---\ntype: seat-journal\nseat: orchestrator\n---\n\n"
        "# Seat journal — orchestrator\n\n## 2026-01-01 — the seat is opened\n\nJudgement.\n"
    )
    (seat / "readings.md").write_text(
        "---\ntype: readings\nseat: orchestrator\n---\n\n# Readings — orchestrator\n"
    )

    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "seed")

    state = root / ".claude" / "state"
    t0 = time.time()

    def handoff(*args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", str(root / "scripts" / "handoff.py"), "--role", "orchestrator", *args],
            cwd=str(root),
            capture_output=True,
            text=True,
        )

    def regen_handoff() -> None:
        """The one mechanical recovery command clause (e′) check 1's reason instructs."""
        assert handoff("--write").returncode == 0

    regen_handoff()  # the seat starts up to date, as a merged checkout does
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "seat")

    def session_start() -> None:
        """What ``session-brief.sh`` does at SessionStart: record HEAD as the baseline. Its
        CONTENT is (e′)'s commits-this-session guard; its MTIME is check 2's key."""
        b = state / "session-baseline"
        b.write_text(_git(root, "rev-parse", "HEAD").stdout.strip())
        os.utime(b, (t0, t0))

    def commit(msg: str = "work", *, at_offset: float | None = None) -> None:
        """``at_offset`` dates the commit at ``t0 + offset`` — i.e. that many seconds after
        the SessionStart baseline write."""
        n = len(list(root.glob("w-*.txt")))
        (root / f"w-{n}.txt").write_text("x\n")
        at = None if at_offset is None else t0 + at_offset
        _git(root, "add", "-A", at=at)
        _git(root, "commit", "-qm", msg, at=at)

    def write_journal_entry(*, this_session: bool, offset: float = 100.0) -> None:
        """NARRATIVE freshness is an mtime vs the SessionStart baseline write — nothing about
        the entry's text, deliberately (§2.10 R2: purity is review-grade, not gate-grade).
        ``offset`` places the entry that many seconds after (or before) session start."""
        j = seat / "journal.md"
        j.write_text(j.read_text() + "\n## 2026-01-02 — an entry\n\nMore judgement.\n")
        ts = t0 + offset if this_session else t0 - offset
        os.utime(j, (ts, ts))

    def stale_the_handoff() -> None:
        """Drift the committed rendering away from what the tree renders to."""
        (seat / "handoff.md").write_text("stale — hand-edited, which the banner forbids\n")

    def change_the_tree() -> None:
        """A real unit of work: a new artifact the rendering derives from. This is how the
        rendering goes stale in life — not by hand-editing it."""
        d = root / "docs" / "build-plans" / "bp-new"
        d.mkdir(parents=True, exist_ok=True)
        (d / "plan.md").write_text(_plan("bp-new", ["edge/**"]).replace(
            "status: in-progress", "status: proposed"))

    def run() -> str:
        env = dict(os.environ)
        env["CLAUDE_PROJECT_DIR"] = str(root)
        r = subprocess.run(
            ["python3", str(root / ".claude" / "hooks" / "_lib.py"), "stop-audit"],
            cwd=str(root),
            env=env,
            capture_output=True,
            text=True,
        )
        return r.stdout

    return {
        "root": root,
        "seat": seat,
        "state": state,
        "run": run,
        "session_start": session_start,
        "commit": commit,
        "write_journal_entry": write_journal_entry,
        "stale_the_handoff": stale_the_handoff,
        "change_the_tree": change_the_tree,
        "regen_handoff": regen_handoff,
        "handoff": handoff,
    }


# ── (e′-1) DERIVED: idempotence, not mtime ──────────────────────────────────────────────


@pytest.mark.integration
def test_e_prime_blocks_on_a_stale_derived_rendering(handoff_repo):
    """(e′-1), heir to case (1): commits landed this session and regenerating the handoff is
    NOT a no-op -> BLOCK. The reason must BE the automation: it names the exact command."""
    h = handoff_repo
    h["session_start"]()
    h["commit"]()
    h["write_journal_entry"](this_session=True)  # isolate check 1 from check 2
    h["stale_the_handoff"]()
    out = h["run"]()
    assert out.startswith("BLOCK:"), f"expected BLOCK, got: {out!r}"
    assert "(e′)" in out, f"expected the (e′) reason, got: {out!r}"
    assert "handoff.md" in out, f"the reason must name the stale artifact: {out!r}"
    assert "--write" in out, f"the reason must state the one-step recovery: {out!r}"


@pytest.mark.integration
def test_e_prime_blocks_when_the_work_itself_moved_the_rendering(handoff_repo):
    """The lifelike form of (e′-1): no one hand-edits the rendering — a unit of work adds an
    artifact the rendering derives from, so the committed file no longer matches the tree."""
    h = handoff_repo
    h["session_start"]()
    h["change_the_tree"]()
    h["commit"]()
    h["write_journal_entry"](this_session=True)
    out = h["run"]()
    assert out.startswith("BLOCK:"), f"expected BLOCK, got: {out!r}"
    assert "(e′)" in out, f"expected the (e′) reason, got: {out!r}"


# ── (e′-2) NARRATIVE: an entry for THIS session ─────────────────────────────────────────


@pytest.mark.integration
def test_e_prime_blocks_when_the_seat_journal_predates_session_start(handoff_repo):
    """(e′-2), heir to case (1)'s staleness half: the seat journal's newest write is older
    than the SessionStart baseline -> BLOCK, even with a perfectly fresh rendering."""
    h = handoff_repo
    h["session_start"]()
    h["commit"]()
    h["regen_handoff"]()  # isolate check 2 from check 1
    h["write_journal_entry"](this_session=False)
    out = h["run"]()
    assert out.startswith("BLOCK:"), f"expected BLOCK, got: {out!r}"
    assert "(e′)" in out, f"expected the (e′) reason, got: {out!r}"
    assert "journal.md" in out, f"the reason must name the seat journal: {out!r}"
    assert "handoff.md" not in out, f"check 1 must be satisfied here: {out!r}"


@pytest.mark.integration
def test_e_prime_blocks_when_the_seat_journal_is_missing(handoff_repo):
    """(e′-2), heir to case (2): a seat that exists but carries no journal at all is the
    'infinitely stale' case — the narrative is owed, so the close blocks."""
    h = handoff_repo
    h["session_start"]()
    h["commit"]()
    h["regen_handoff"]()
    (h["seat"] / "journal.md").unlink()
    out = h["run"]()
    assert out.startswith("BLOCK:"), f"expected BLOCK, got: {out!r}"
    assert "(e′)" in out, f"expected the (e′) reason, got: {out!r}"
    assert "journal.md" in out, f"the reason must name the seat journal: {out!r}"


@pytest.mark.integration
def test_e_prime_check_2_is_keyed_to_session_start_not_to_the_last_commit(handoff_repo):
    """⚑ The circularity, cut precisely — and the one property the convergence test alone does
    NOT pin (verified: a mutant keying check 2 to ``last_commit`` survives every other test in
    this file).

    An entry written at the *earliest legal moment* (session start), followed by a commit an
    hour later, must still ALLOW. Keying check 2 to last-commit time is exactly what (e) did,
    and it is why every late commit — a seal, a board regen, a capture — forced another
    hand-authored rewrite. Under such a mutation this test blocks; under the specified clause
    it allows."""
    h = handoff_repo
    h["session_start"]()  # baseline mtime := t0
    h["write_journal_entry"](this_session=True, offset=0)  # entry mtime := t0, the boundary
    h["commit"]("a commit an HOUR after the entry", at_offset=3600)
    h["regen_handoff"]()  # isolate check 1
    out = h["run"]()
    assert out.strip() == "ALLOW", (
        f"a commit made AFTER the narrative entry must NOT re-arm check 2 — that is the (e) "
        f"circularity, and §2.10 keys check 2 to session START precisely to cut it. Got: {out!r}"
    )
    assert "(e′)" not in out, f"(e′) must not fire here: {out!r}"


# ── (e′-3) both fresh -> ALLOW ──────────────────────────────────────────────────────────


@pytest.mark.integration
def test_e_prime_allows_on_a_fresh_rendering_and_a_fresh_entry(handoff_repo):
    """(e′-3), heir to case (4): commits landed, the rendering is a no-op to regenerate and an
    entry was written this session -> ALLOW."""
    h = handoff_repo
    h["session_start"]()
    h["commit"]()
    h["write_journal_entry"](this_session=True)
    h["regen_handoff"]()
    out = h["run"]()
    assert out.strip() == "ALLOW", f"expected ALLOW, got: {out!r}"
    assert "(e′)" not in out, f"a fresh seat must clear (e′): {out!r}"


# ── (e′-4) MEASURED is never gated — the explicit negative ──────────────────────────────


@pytest.mark.integration
def test_e_prime_never_gates_the_measured_readings_log(handoff_repo):
    """(e′-4): a readings log untouched for a decade must NOT block a close. Gating a
    17-minute suite reading at every close is the cry-wolf disqualifier (§2.10.3); this test
    exists so a future 'improvement' that adds a readings-freshness check reddens here."""
    h = handoff_repo
    h["session_start"]()
    h["commit"]()
    h["write_journal_entry"](this_session=True)
    h["regen_handoff"]()
    r = h["seat"] / "readings.md"
    ancient = time.time() - 10 * 365 * 24 * 3600
    os.utime(r, (ancient, ancient))
    out = h["run"]()
    assert out.strip() == "ALLOW", f"MEASURED is deliberately ungated: {out!r}"
    assert "readings" not in out, f"(e′) must never mention the readings log: {out!r}"


# ── the falsifier that decides the whole cutover: ONE-STEP CONVERGENCE ──────────────────


@pytest.mark.integration
def test_e_prime_converges_in_exactly_one_step(handoff_repo):
    """⚑ bp-126 Item 12's named falsifier. The whole cutover rests on (e′) being dischargeable
    by one mechanical command. The sequence is asserted end to end — block, regenerate, commit
    (which moves HEAD *again*, exactly the event that re-armed (e)), close -> ALLOW.

    If this ever reddens, the circularity has been reproduced in new clothes: a value that is
    not a pure function of the artifact tree has crept back into the committed rendering, and
    ``finding-0236`` is the first place to look."""
    h = handoff_repo
    h["session_start"]()
    h["change_the_tree"]()
    h["commit"]("a unit of work")
    h["write_journal_entry"](this_session=True)

    first = h["run"]()
    assert first.startswith("BLOCK:"), f"step 1 must block: {first!r}"
    assert "(e′)" in first and "handoff.md" in first, f"blocked for the wrong reason: {first!r}"

    h["regen_handoff"]()  # the instructed recovery, verbatim
    h["commit"]("regenerate the handoff")  # HEAD moves again — (e) would have re-armed here

    second = h["run"]()
    assert second.strip() == "ALLOW", (
        f"ONE-STEP CONVERGENCE FAILED — a second close still blocks after regenerate+commit. "
        f"That is the (e) circularity in new clothes and it falsifies the note's central "
        f"by-construction claim (§2.10). Got: {second!r}"
    )

    # ...and the recovery is genuinely idempotent, not merely quiet once.
    assert h["handoff"]("--check").returncode == 0
    assert h["run"]().strip() == "ALLOW"


# ── fail-open: enforcement never crashes a close ────────────────────────────────────────


@pytest.mark.integration
def test_e_prime_fails_open_when_the_generator_is_absent(handoff_repo):
    """Check 1 delegates to a subprocess, so it must fail OPEN on any generator error — a
    checkout without the generator is simply not gated on it. Check 2 still governs, so the
    fresh entry below is what carries the ALLOW.

    This is the rc-2 path, and it is also what stops the discriminator being widened to
    ``rc != 0``: an absent script exits 2, which must not read as staleness."""
    h = handoff_repo
    h["session_start"]()
    h["commit"]()
    h["write_journal_entry"](this_session=True)
    h["stale_the_handoff"]()  # check 1 WOULD block...
    (h["root"] / "scripts" / "handoff.py").unlink()  # ...but cannot be evaluated
    out = h["run"]()
    assert out.strip() == "ALLOW", f"an absent generator must fail open: {out!r}"
    assert "(e′)" not in out, f"(e′) must skip an unevaluable signal: {out!r}"


@pytest.mark.integration
@pytest.mark.parametrize(
    ("label", "body"),
    [
        ("ImportError", "import a_module_that_does_not_exist_anywhere\n"),
        ("RuntimeError", 'raise RuntimeError("boom")\n'),
        ("SyntaxError", "def broken(:\n"),
    ],
)
def test_e_prime_fails_open_when_the_generator_crashes(handoff_repo, label, body):
    """⚑ The wedge case, and the reason this clause may not key on the return code alone.

    **CPython exits 1 on any unhandled exception**, and ``--check`` exits 1 on drift — so by rc
    a crashing generator is byte-identical to a stale one. Keying on ``rc == 1`` made a broken
    generator read as STALE and BLOCK; the instructed recovery (``--write``) would then fail
    identically, and the close would be **wedged**, because a Stop BLOCK is a hard deny. That
    is strictly worse than the staleness it prevents: it also wedges the session trying to
    repair the generator.

    Staleness is therefore identified POSITIVELY, by the generator's own rendered signature.
    Every crash mode — enumerated or not — falls through to fail-open."""
    h = handoff_repo
    h["session_start"]()
    h["commit"]()
    h["write_journal_entry"](this_session=True)
    h["stale_the_handoff"]()  # genuinely stale, so only the crash can be what is observed
    (h["root"] / "scripts" / "handoff.py").write_text(body)

    # The premise, asserted rather than assumed: this really does exit 1, like a stale render.
    crash = h["handoff"]("--check")
    assert crash.returncode == 1, f"{label} must exit 1 for this test to mean anything"
    assert _lib_module().HANDOFF_STALE_SIGNATURE not in (crash.stderr + crash.stdout), (
        f"{label}'s output must not carry the staleness signature"
    )

    out = h["run"]()
    assert out.strip() == "ALLOW", (
        f"a generator crashing with {label} exits 1 exactly as a stale render does; keying on "
        f"the return code alone WEDGES every close. Got: {out!r}"
    )
    assert "(e′)" not in out, f"(e′) must skip an unevaluable signal: {out!r}"


@pytest.mark.integration
@pytest.mark.parametrize(
    "vector",
    [
        "the-real-generator-raises-at-its-own-STALE-print",
        "a-synthetic-crash-carrying-the-bare-marker",
    ],
)
def test_e_prime_is_not_spoofed_by_a_crash_that_merely_MENTIONS_stale(handoff_repo, vector):
    """⚑ The behavioural pin for the **seat qualifier** — the single most subtle choice in check 1,
    and the one that was previously proved only by a string-identity assertion on the constant.

    Mutation A2 (drop the qualifier at the **use site**: `": STALE" in output`) survived all
    eighteen preceding tests, because every crash fixture here produces a traceback containing no
    form of the marker at all — so none of them could tell a bare probe from a qualified one. This
    test supplies the discriminating input.

    **The vector is real, not contrived.** `--check`'s staleness branch is
    ``print(f"{dest.relative_to(ROOT)}: STALE — regenerate with …")``. If `dest` is ever outside
    `ROOT`, `relative_to` raises **at that line**, and CPython echoes the line's **source** into
    the traceback — source that contains the f-string *template* ``{dest.relative_to(ROOT)}:
    STALE``. So a crash can emit a bare ``": STALE"`` while the rendered
    ``orchestrator/handoff.md: STALE`` never existed. Under a bare probe that reads as staleness
    and BLOCKS; `--write` then dies the same way, and the close is **wedged** — the exact failure
    the whole fix exists to remove, walking back in through the discriminator.

    Two vectors: the faithful reconstruction against the **real** generator (proves the vector is
    reachable in the shipped code), and a synthetic crash carrying the marker (survives any
    reshaping of that source line, so the behaviour stays pinned even if the reconstruction's
    anchor goes stale)."""
    h = handoff_repo
    sig = _lib_module().HANDOFF_STALE_SIGNATURE
    src_path = h["root"] / "scripts" / "handoff.py"

    h["session_start"]()
    h["commit"]()
    h["write_journal_entry"](this_session=True)  # isolate check 1
    h["stale_the_handoff"]()  # genuinely stale, so only the crash decides the verdict

    if vector.startswith("the-real-generator"):
        src = src_path.read_text()
        anchor = '        print(f"{dest.relative_to(ROOT)}: STALE'
        assert src.count(anchor) == 1, (
            "the generator's staleness branch no longer matches this reconstruction; re-derive "
            "the anchor from scripts/handoff.py before trusting this test"
        )
        # `dest` outside ROOT -> relative_to raises AT the print, echoing its source verbatim.
        src_path.write_text(
            src.replace(anchor, '        dest = Path("/nowhere") / "handoff.md"\n' + anchor)
        )
    else:
        src_path.write_text(
            'raise RuntimeError("regenerating: STALE — a crash, not a staleness report")\n'
        )

    crash = h["handoff"]("--check")
    combined = crash.stderr + crash.stdout
    assert crash.returncode == 1, f"the spoof must exit 1, like a stale render: {crash!r}"
    assert ": STALE" in combined, (
        f"this test is vacuous unless the crash really does carry the bare marker: {combined!r}"
    )
    assert sig not in combined, (
        f"the crash must NOT carry the seat-qualified signature, or it proves nothing: {combined!r}"
    )

    out = h["run"]()
    assert out.strip() == "ALLOW", (
        f"a crash that merely MENTIONS ': STALE' must not be read as staleness — that wedges the "
        f"close, since the instructed `--write` recovery fails identically. This is why the "
        f"signature is seat-qualified ({sig!r}) rather than a bare ': STALE'. Got: {out!r}"
    )
    assert "(e′)" not in out, f"(e′) must skip an unevaluable signal: {out!r}"


def _lib_module():
    """Import the hook library in-process. Deliberately lazy and function-local: only the two
    tests below need it, and ``_lib`` is a bare top-level module name, so keeping the
    ``sys.path`` insert out of import time keeps it from leaking into unrelated collection.
    Only ``.claude/hooks`` is inserted — never ``scripts/``, which shadows the ``eval`` package
    (finding-0238)."""
    import sys

    p = str(_REPO / ".claude" / "hooks")
    if p not in sys.path:
        sys.path.insert(0, p)
    import _lib  # type: ignore[import-not-found]

    return _lib


@pytest.mark.integration
def test_e_prime_fails_open_when_the_subprocess_cannot_be_LAUNCHED(monkeypatch):
    """The ``except`` arm of check 1, exercised directly — it had NO coverage at all (the
    auditor's surviving mutation N1), which meant the fail-open branch the whole clause leans
    on was unproven.

    The launch failures it guards — a missing or non-executable interpreter, a vanished cwd, a
    timeout — cannot be provoked end-to-end from a fixture without either breaking the test
    runner's own interpreter or sleeping out a 30-second timeout, so the branch is driven at
    the seam instead: any exception from ``subprocess.run`` must yield 'not stale'."""
    lib = _lib_module()

    for exc in (OSError("cannot launch"), TimeoutError("hung"), MemoryError()):
        def boom(*_a, _exc=exc, **_kw):
            raise _exc

        monkeypatch.setattr(lib.subprocess, "run", boom)
        assert lib._handoff_is_stale() is False, (
            f"{type(exc).__name__} from the launch must fail OPEN — enforcement never crashes "
            f"a close, and it must never be reported as staleness"
        )


@pytest.mark.integration
def test_the_staleness_signature_is_what_the_real_generator_actually_renders(handoff_repo):
    """Pins the contract between the hook and `scripts/handoff.py`, which is out of bp-126's
    write_scope and can therefore move without this file noticing.

    The signature is seat-qualified on purpose: were the generator to raise AT its own staleness
    `print`, the traceback would echo that line's SOURCE, which contains the f-string template
    `{dest.relative_to(ROOT)}: STALE` — so a bare ": STALE" probe could be satisfied by a crash.
    Only the rendered form carries `<seat>/handoff.md: STALE`."""
    h = handoff_repo
    sig = _lib_module().HANDOFF_STALE_SIGNATURE
    assert sig == "orchestrator/handoff.md: STALE"

    h["stale_the_handoff"]()
    r = h["handoff"]("--check")
    assert r.returncode == 1
    assert sig in (r.stderr + r.stdout), (
        f"the real generator no longer renders {sig!r}; clause (e′) check 1 has silently "
        f"degraded to fail-open. Re-derive the signature from the generator's message."
    )

    h["regen_handoff"]()
    ok = h["handoff"]("--check")
    assert ok.returncode == 0 and sig not in (ok.stderr + ok.stdout)


@pytest.mark.integration
def test_e_prime_fails_open_when_the_seat_does_not_exist(handoff_repo):
    """A checkout with no ``docs/roles/<seat>/`` has nothing to be fresh about — neither check
    can be evaluated, so the clause skips entirely rather than deadlocking every close."""
    h = handoff_repo
    h["session_start"]()
    h["commit"]()
    shutil.rmtree(h["seat"])
    out = h["run"]()
    assert out.strip() == "ALLOW", f"an absent seat must fail open: {out!r}"
    assert "(e′)" not in out, f"(e′) must skip an unevaluable signal: {out!r}"


# ── the three posture invariants, carried over verbatim from clause (e) ─────────────────


@pytest.mark.integration
def test_allow_when_no_commits_this_session(handoff_repo):
    """(3), unchanged: baseline == HEAD (a pure chat/design session — no commits) -> ALLOW,
    even with BOTH seat halves stale. The content guard keeps commit-less sessions from ever
    blocking, and it is the reason a reading-only session is never taxed."""
    h = handoff_repo
    h["commit"]()  # commit BEFORE capturing the baseline
    h["session_start"]()  # baseline == HEAD -> no session commits
    h["stale_the_handoff"]()
    h["write_journal_entry"](this_session=False)
    out = h["run"]()
    assert out.strip() == "ALLOW", f"expected ALLOW, got: {out!r}"
    assert "(e′)" not in out, f"(e′) must not fire with no session commits: {out!r}"


@pytest.mark.integration
def test_fail_open_on_missing_baseline(handoff_repo):
    """(5), unchanged: commits landed and the seat is stale, but ``session-baseline`` is
    absent (first session / cleaned state) -> fail-open ALLOW. The signal cannot be evaluated,
    so (e′) skips — the same posture (e) held (gate note §2.5)."""
    h = handoff_repo
    assert not (h["state"] / "session-baseline").exists()
    h["commit"]()
    h["stale_the_handoff"]()
    out = h["run"]()
    assert out.strip() == "ALLOW", f"missing baseline must fail-open ALLOW: {out!r}"
    assert "(e′)" not in out, f"(e′) must skip on an unevaluable signal: {out!r}"


@pytest.mark.integration
def test_silent_under_active_plan(handoff_repo):
    """(6), unchanged: with an active plan (builder posture), (e′) is silent — the session is
    governed by (a)-(d). Commits landed and BOTH seat halves are deliberately stale, yet (e′)
    never fires; a fresh plan journal keeps (a) quiet so the decision is ALLOW.

    ⚑ (e′) firing in builder posture is one of Item 12's named falsifiers: a builder does not
    occupy the orchestrator seat and must never be asked to keep its state fresh."""
    h = handoff_repo
    root = h["root"]
    plandir = root / "docs" / "build-plans" / "bp-xx"
    plandir.mkdir(parents=True)
    # `docs/roles/**` is in this fixture plan's write_scope for the same reason it is in
    # bp-126's: a builder that dirties the seat would otherwise be blocked by (b), and (b)
    # blocking is not what this test is about. Isolating (e′)'s SILENCE is.
    (plandir / "plan.md").write_text(_plan("bp-xx", ["edge/**", "docs/roles/**"]))
    (plandir / "journal.md").write_text("# journal\n")
    (h["state"] / "active-plan").write_text("bp-xx")  # builder posture

    h["session_start"]()
    h["commit"]()  # commits this session
    h["stale_the_handoff"]()  # a stale seat that (e′) would block on, if it ran
    h["write_journal_entry"](this_session=False)
    os.utime(plandir / "journal.md", None)  # plan journal fresh -> (a) stays quiet

    out = h["run"]()
    assert "(e′)" not in out, f"(e′) must be silent under an active plan: {out!r}"
    assert out.strip() == "ALLOW", (
        f"fresh journal + in-scope tree under an active plan -> ALLOW: {out!r}"
    )
