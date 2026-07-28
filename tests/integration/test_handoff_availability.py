"""F1c — the handoff is readable with no running system (bp-127 Item 16).

`dn-role-state-and-scoped-handoff` §2.11 F1c: *"in a **fresh worktree of `origin/main` with no
daemon running**, the generator must exit 0, rendering `queue: unavailable` rather than erroring,
and the committed journal + rendering must be present (tracked ⇒ present in every checkout). This
is the §2.6 hard constraint as a test, run in the environment that motivated it."*

§2.6 is what it defends: the queue was rejected as the handoff *substrate* because **fresh
worktrees have no queue** — `data/` is not in the tree, so `data/queue.sqlite` does not exist in
the checkout where a delegated resume actually happens. A handoff that needs a running system is
not a handoff. This test runs the generator in a **real** worktree, built by `git worktree add`,
the `test_worktree_enforcement.py` pattern — a mocked filesystem cannot falsify a claim about what
exists in a checkout, which is the entire point.

⚑ **Two deviations from the plan's literal wording, both deliberate and both STRENGTHENING.**

1. **The worktree is built from `HEAD`, not from `origin/main`.** `origin/main` is the wrong
   subject twice over: it may not be fetched in a CI or shallow clone (the test would skip or
   error for an unrelated reason), and — the real objection — **a test against `origin/main`
   passes no matter what the working tree contains.** Delete the seat from this branch and an
   `origin/main` test still goes green, which is precisely the false-success shape this wave is
   trying to stamp out. HEAD is what this checkout is about to publish, so HEAD is what must
   carry the artifacts.
2. **The queue pane is checked in BOTH directions.** The degenerate input for F1c is a generator
   that prints `queue: unavailable` *unconditionally* — in a checkout with no queue that is
   indistinguishable from correct, and every future run reports a graceful degradation that was
   never computed. So the test also drops a real SQLite queue into the fresh worktree and asserts
   the pane CHANGES. The observable has to be causally downstream of the file, or the assertion is
   decoration.

The other named degenerate inputs: a worktree that is not actually fresh (asserted: no `data/`, and
`.claude/state/` holds nothing but its `.gitignore`), and a "the files are present" check that is
silently reading the MAIN checkout instead (asserted: the generator's own output moves when the
WORKTREE's journal changes).
"""

from __future__ import annotations

import os
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SEAT = Path("docs") / "roles" / "orchestrator"
QUEUE = Path("data") / "queue.sqlite"


def _git(*args: str, cwd: Path = REPO) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", "-C", str(cwd), *args],
                          capture_output=True, text=True, check=False)


# The code under test, overlaid onto the checkout. See `fresh_worktree`.
_OVERLAY = (Path("scripts") / "handoff.py", Path("scripts") / "board.py",
            Path(".claude") / "hooks" / "_lib.py")


@pytest.fixture
def fresh_worktree(tmp_path):
    """A REAL `git worktree add --detach HEAD`, with the WORKING TREE's generator overlaid onto it,
    removed deterministically.

    Never `git init` + copy: the claim "tracked ⇒ present in every checkout" can only be falsified
    by a genuine checkout of this repo's index.

    ⚑ **The overlay is load-bearing, and it was added because mutation proved the test vacuous
    without it.** `git worktree add HEAD` checks out the last COMMIT, so a suite that runs the
    checked-out `handoff.py` reports on HEAD and is completely insensitive to the diff under
    review. Five behaviour-destroying mutants — a hard-coded queue pane, a raising degradation
    path, a `CLAUDE_PROJECT_DIR` bleed — ALL SURVIVED, at 8 passed, because the mutated file was
    never the file being executed. That is the exact false-success shape `finding-0249` names:
    green became evidence for green.

    So the two claims are sourced separately, on purpose: **the checkout** supplies the tracked
    artifacts and the absence of runtime state (what a fresh worktree really has), and **the
    working tree** supplies the code whose behaviour is being asserted.
    """
    wt = tmp_path / "fresh"
    made = _git("worktree", "add", "--detach", str(wt), "HEAD")
    if made.returncode != 0:  # pragma: no cover — a broken git is not this test's subject
        pytest.skip(f"git worktree add unavailable: {made.stderr.strip()}")
    try:
        for rel in _OVERLAY:
            shutil.copyfile(REPO / rel, wt / rel)
        yield wt
    finally:
        _git("worktree", "remove", "--force", str(wt))
        _git("worktree", "prune")


def _run(wt: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """The generator, from the worktree's (overlaid) copy. No `uv run`: a fresh worktree has no
    `.venv`, and syncing one would be the opposite of the availability property under test — the
    script is stdlib-only by design, plus its two in-repo siblings.

    Two hostile conditions are supplied deliberately rather than avoided:

      * **`CLAUDE_PROJECT_DIR` points at the MAIN checkout.** This is the literal bleed that
        `finding-0031` describes — the delegate harness sets it even for worktree-isolated agents —
        and it is how a "the files are present" assertion silently reads the wrong tree.
      * **The CWD is NOT the worktree.** Anything the generator resolves relative to `.` instead of
        to its own `ROOT` breaks here, which is the only way a CWD-relative path bug is visible.
    """
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(REPO)}
    return subprocess.run([sys.executable, str(wt / "scripts" / "handoff.py"), *args],
                          cwd=str(wt.parent), capture_output=True, text=True, check=False, env=env)


# ── the fixture is genuinely what it claims to be ───────────────
def test_the_overlay_actually_replaced_the_checked_out_generator(fresh_worktree):
    """⚑ The degenerate input for the OVERLAY itself. If the copy silently no-ops the whole suite
    reverts to reporting on HEAD — green, and blind to the diff under review."""
    for rel in _OVERLAY:
        assert (fresh_worktree / rel).read_bytes() == (REPO / rel).read_bytes(), \
            f"{rel} in the worktree is not the file under review — the suite would test HEAD"


def test_the_fresh_worktree_has_no_runtime_state_at_all(fresh_worktree):
    """⚑ The degenerate input for every other test in this file: if the worktree inherited `data/`
    or a populated `.claude/state/`, every assertion below passes for the wrong reason."""
    assert not (fresh_worktree / "data").exists(), \
        "data/ is gitignored — a checkout must never have it"
    assert not (fresh_worktree / QUEUE).exists()
    state = fresh_worktree / ".claude" / "state"
    assert [p.name for p in state.iterdir()] == [".gitignore"], \
        "the sitting's state is per-worktree and regenerable (note §2.7)"
    assert not (fresh_worktree / ".claude" / "state" / "session-baseline").exists()


# ── F1c proper ──────────────────────────────────────────────────
def test_the_seat_artifacts_are_present_in_a_fresh_checkout(fresh_worktree):
    """The §2.7 versioning ruling, mechanically. If these are absent the whole ruling was never
    built — the plan's Item 16 falsifier, and a STOP condition rather than a nit."""
    for name in ("journal.md", "handoff.md", "readings.md"):
        path = fresh_worktree / SEAT / name
        assert path.is_file(), f"{name} is not present in a fresh checkout — was it ever tracked?"
        assert path.read_text(encoding="utf-8").strip(), f"{name} is present but empty"
    tracked = _git("ls-files", "--", str(SEAT)).stdout.split()
    assert {f"{SEAT.as_posix()}/{n}" for n in ("journal.md", "handoff.md", "readings.md")} \
        <= set(tracked), "tracked ⇒ present in every checkout — the claim starts with 'tracked'"


def test_the_generator_exits_zero_with_no_daemon_and_no_queue(fresh_worktree):
    """The §2.6 hard constraint: a missing queue is a VALUE, never an exception. Asserted on the
    LIVE stdout path — `--check` exits 0 in a fresh worktree without ever reaching the queue, so
    asserting F1c against it would be a green test that proves nothing (finding-0236)."""
    res = _run(fresh_worktree, "--role", "orchestrator")
    assert res.returncode == 0, f"stderr: {res.stderr}"
    assert "queue: unavailable" in res.stdout
    assert "Traceback" not in res.stderr


def test_the_generator_creates_no_queue_before_or_after(fresh_worktree):
    """Creating it would breach the single-writer model (`scheduler/queue.py:17-18`) — the other
    half of Item 16's falsifier."""
    assert not (fresh_worktree / QUEUE).exists()
    for args in (("--role", "orchestrator"), ("--role", "orchestrator", "--json"),
                 ("--role", "orchestrator", "--check")):
        assert _run(fresh_worktree, *args).returncode in (0, 1)
        assert not (fresh_worktree / QUEUE).exists(), f"{args} created the queue"
    assert not (fresh_worktree / "data").exists()


# ⚑ THE DEGENERATE INPUT for the pane itself: an unconditional string.
def test_the_queue_pane_is_causally_downstream_of_the_queue_file(fresh_worktree):
    """`queue: unavailable` in a checkout with no queue is what a HARD-CODED string looks like too.
    Put a real queue there and the pane must change, or the graceful-degradation claim is untested
    decoration."""
    before = _run(fresh_worktree, "--role", "orchestrator")
    assert "queue: unavailable" in before.stdout

    path = fresh_worktree / QUEUE
    path.parent.mkdir(parents=True)
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE jobs (id INTEGER PRIMARY KEY, kind TEXT, state TEXT, "
                 "lease_expires_at TEXT)")
    conn.executemany("INSERT INTO jobs (id, kind, state, lease_expires_at) VALUES (?, ?, ?, ?)",
                     [(1, "embed", "queued", None), (2, "dream", "queued", None)])
    conn.commit()
    conn.close()
    try:
        after = _run(fresh_worktree, "--role", "orchestrator")
        assert after.returncode == 0
        assert "queue: unavailable" not in after.stdout
        assert "queue: depth 2" in after.stdout
    finally:
        shutil.rmtree(fresh_worktree / "data")
    assert "queue: unavailable" in _run(fresh_worktree, "--role", "orchestrator").stdout


# ⚑ THE DEGENERATE INPUT for "present": reading the MAIN checkout by accident.
def test_the_generator_reads_the_worktree_s_own_seat_not_the_main_checkout(fresh_worktree):
    """A `CLAUDE_PROJECT_DIR` bleed or a bad `ROOT` would make every "present" assertion above pass
    while the process actually read main's files (the finding-0031 defect class, one tool over).
    Change the WORKTREE's journal and the generator's own measurement must move with it."""
    import json
    first = json.loads(_run(fresh_worktree, "--role", "orchestrator", "--json").stdout)
    journal = fresh_worktree / SEAT / "journal.md"
    # ⚑ Prepend at the TOP — the newest-first journal's authoritative end. This probe originally
    # appended at the BOTTOM, which landed below the first `## CAPSULE` heading the moment one
    # existed (2026-07-27): outside the authoritative segment, so the count stayed flat and this
    # test went red against a CORRECT generator. It was green only in the pre-first-compaction
    # state (`authoritative_segment` returns the whole file when no capsule exists) — a latent
    # geometry dependence. Mutate where a real entry lands and the probe is capsule-proof.
    journal.write_text("a prepended probe line\n\n" + journal.read_text(encoding="utf-8"),
                       encoding="utf-8")
    second = json.loads(_run(fresh_worktree, "--role", "orchestrator", "--json").stdout)
    assert second["journal_segment_lines"] == first["journal_segment_lines"] + 2, \
        "the generator measured a journal that is not the one it was pointed at"


def test_f1a_reaches_a_definite_verdict_in_a_fresh_checkout(fresh_worktree):
    """F1a (bp-124's `--check`) travels with the checkout: it must reach a DEFINITE verdict — 0 or
    1, with the matching signature — rather than crash for want of a runtime.

    ⚑ It deliberately does NOT assert rc 0. Whether `handoff.md` is currently regenerated is a
    property of the last committer's hygiene, not of availability, and clause (e′) check 1 is where
    the note put that duty. A suite that reddens because someone has a regen owed is the cry-wolf
    shape this wave is trying to remove — and it would be CI wiring, which bp-127 §9 excludes."""
    res = _run(fresh_worktree, "--role", "orchestrator", "--check")
    assert res.returncode in (0, 1), f"F1a could not run in a fresh checkout: {res.stderr}"
    assert ("up to date" in res.stdout) or ("STALE" in res.stderr)
    assert "Traceback" not in res.stderr


def test_the_lint_is_runnable_in_a_fresh_checkout(fresh_worktree):
    """F1b travels too — it needs only the tracked files and git, both of which a checkout has. Its
    VERDICT is not asserted here: the live artifact is non-compliant today (finding-0251) and this
    test's subject is availability, not compliance."""
    res = _run(fresh_worktree, "--role", "orchestrator", "--lint")
    assert res.returncode in (0, 1), f"the lint could not run in a fresh checkout: {res.stderr}"
    assert "authoritative segment" in res.stdout
    assert "Traceback" not in res.stderr
