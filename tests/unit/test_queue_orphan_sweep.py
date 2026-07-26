"""bp-101 Item 2 — `JobQueue.sweep_orphans`: reclaim RUNNING rows stranded by a dead run.

Two tests carry the weight:

* `test_the_live_orphan_job_300246_is_reclaimed` — the acceptance fixture, a `code_sync` row left
  RUNNING with no owning run, exactly as the 2026-07-25 `kill -9` left it (finding-0173).
* `test_a_job_the_live_run_is_running_is_never_reclaimed` — **the falsifier**. A sweep that takes
  back a row a live worker holds causes double execution, which is worse than the orphan it fixes.
  The case is exercised with a live-run-owned RUNNING row present alongside a genuine orphan, so a
  sweep that "reclaims everything running" fails loudly rather than passing by accident.
"""

from __future__ import annotations

import pytest

from scheduler.queue import (
    DEFERRED,
    DONE,
    FAILED,
    QUEUED,
    RUNNING,
    JobQueue,
    OrphanSweep,
)

LIVE_RUN = 36          # the run doing the sweeping
DEAD_RUN = 35          # the run that was kill -9'd


@pytest.fixture
def q(tmp_path):
    queue = JobQueue(tmp_path / "q.sqlite")
    yield queue
    queue.close()


def _running_row(q: JobQueue, kind: str, *, owner: int | None) -> int:
    """A row parked in RUNNING owned by `owner` — how the file looks after a run dies mid-job."""
    job = q.enqueue(kind, "pinned", 8192)
    q._conn.execute("UPDATE jobs SET state = ?, started_at = ?, claimed_by_run = ? WHERE id = ?",
                    [RUNNING, "2026-07-25T03:45:07", owner, job.id])
    q._conn.commit()
    return job.id


def test_the_live_orphan_job_300246_is_reclaimed(q):
    """The acceptance fixture: `code_sync`, RUNNING, no owning run (the column did not exist when
    the row was written), stranded at 03:45:07."""
    orphan = _running_row(q, "code_sync", owner=None)

    swept = q.sweep_orphans(LIVE_RUN)

    assert swept == OrphanSweep(requeued=(orphan,), failed=())
    reclaimed = q.get(orphan)
    assert reclaimed.state == QUEUED          # code_sync is idempotent -> back in line
    assert reclaimed.started_at is None
    assert reclaimed.claimed_by_run is None
    assert q.claim() is not None              # and it is genuinely runnable again


def test_a_job_the_live_run_is_running_is_never_reclaimed(q):
    """THE FALSIFIER (plan §7 Item 2). A live worker's row and a dead run's row sit side by side;
    only the dead one may move. If this ever fails, the sweep is causing double execution."""
    live = _running_row(q, "code_sync", owner=LIVE_RUN)      # same kind, so kind cannot mask it
    orphan = _running_row(q, "code_sync", owner=DEAD_RUN)

    swept = q.sweep_orphans(LIVE_RUN)

    assert swept.requeued == (orphan,)
    assert q.get(live).state == RUNNING                      # untouched
    assert q.get(live).claimed_by_run == LIVE_RUN
    assert q.get(orphan).state == QUEUED


def test_a_non_idempotent_kind_fails_explicitly_instead_of_being_rerun(q):
    orphan = _running_row(q, "dream", owner=DEAD_RUN)

    swept = q.sweep_orphans(LIVE_RUN)

    assert swept == OrphanSweep(requeued=(), failed=(orphan,))
    failed = q.get(orphan)
    assert failed.state == FAILED
    assert failed.error == "orphaned by unclean exit of run #35"
    assert failed.finished_at is not None                     # visible, not silently pending


def test_an_unowned_non_idempotent_orphan_names_an_unknown_run(q):
    orphan = _running_row(q, "ambassador_task", owner=None)
    q.sweep_orphans(LIVE_RUN)
    assert q.get(orphan).error == "orphaned by unclean exit of run #?"


def test_terminal_and_waiting_rows_are_never_examined(q):
    done = q.enqueue("dream", "synthesis", 32768)
    q.complete(done.id, "ok")
    failed = q.enqueue("curate", "synthesis", 32768)
    q.fail(failed.id, "boom")
    deferred = q.enqueue("shadow", "synthesis", 32768)
    q.defer(deferred.id, "ceiling")
    waiting = q.enqueue("chat_sync", "pinned", 8192)

    assert q.sweep_orphans(LIVE_RUN) == OrphanSweep()
    assert q.get(done.id).state == DONE and q.get(done.id).result == "ok"
    assert q.get(failed.id).state == FAILED and q.get(failed.id).error == "boom"
    assert q.get(deferred.id).state == DEFERRED
    assert q.get(waiting.id).state == QUEUED


def test_the_sweep_is_idempotent_and_clean_on_a_clean_exit(q):
    orphan = _running_row(q, "vault_sync", owner=DEAD_RUN)
    first = q.sweep_orphans(LIVE_RUN)
    second = q.sweep_orphans(LIVE_RUN)
    assert first.requeued == (orphan,)
    assert second == OrphanSweep()                # nothing left stranded; render says so
    assert second.render() == "orphan sweep: nothing stranded"


def test_the_sweep_adopts_the_run_so_later_claims_are_stamped(q):
    """Why the sweep is safe to run once at start: after it, every claim carries the stamp, so a
    LATER sweep (a second supervisor, a defensive re-run) can still tell live from stranded."""
    q.enqueue("chat_sync", "pinned", 8192)
    assert q.active_run_id is None
    q.sweep_orphans(LIVE_RUN)

    claimed = q.claim()
    assert claimed is not None and claimed.claimed_by_run == LIVE_RUN
    assert q.sweep_orphans(LIVE_RUN) == OrphanSweep()          # its own live work is protected
    assert q.get(claimed.id).state == RUNNING


# =================================================================================================
# bp-109 — the lease does NOT widen what the sweep reclaims
# =================================================================================================
#
# A reclaim that races a live worker is worse than the orphan it fixes (this file's second test).
# bp-109 gives a row a deadline, and a lapsed deadline is NOT evidence that the holder is dead — a
# hung-but-alive worker has exactly that shape. So `claimed_by_run == active_run_id` stays an
# absolute VETO that no deadline overrides: such rows are counted into `OrphanSweep.lease_expired`
# and reported, never touched (plan §9 — stamping is here, killing is a later plan's).

def test_a_lapsed_deadline_on_this_runs_own_row_is_reported_not_reclaimed(q):
    """⚑ THE WIDENING FALSIFIER. The row is RUNNING, owned by the LIVE run, and hours past its
    deadline. It must still be RUNNING afterwards: this run's stamp says a worker holds it, and the
    only thing the sweep may do about a lapsed lease is say so."""
    q.sweep_orphans(LIVE_RUN)
    q.enqueue("code_sync", "pinned", 8192)
    live = q.claim()
    assert live is not None and live.claimed_by_run == LIVE_RUN
    q._conn.execute("UPDATE jobs SET lease_expires_at = ? WHERE id = ?",
                    ["2020-01-01T00:00:00", live.id])
    q._conn.commit()

    swept = q.sweep_orphans(LIVE_RUN)

    assert swept.requeued == () and swept.failed == ()     # nothing MOVED …
    assert swept.lease_expired == (live.id,)               # … and the lapse is visible
    assert swept.total == 0                                # `total` counts what it did
    assert "reported, NOT reclaimed" in swept.render()
    still = q.get(live.id)
    assert still.state == RUNNING
    assert still.claimed_by_run == LIVE_RUN
    assert still.started_at == live.started_at
    assert still.attempts == live.attempts                 # not re-attempted behind its back


def test_a_live_workers_checkpointed_row_is_never_reclaimable(q):
    """⚑ The composite case bp-109 must not create: a worker that has checkpointed once and been
    re-claimed is mid-resume on a PARTIALLY ADVANCED row. Reclaiming that hands the same cursor to a
    second worker — double execution over already-covered units. Two independent things stop it:
    the row is owned by the live run (the veto above), and `checkpoint` clears the lease so the
    intermediate QUEUED state carries no deadline to lapse in the first place.

    The whole sequence is exercised, including a sweep at the yielded moment — the window a second
    supervisor's defensive sweep would land in."""
    q.sweep_orphans(LIVE_RUN)
    q.enqueue("code_backfill", "pinned", 8192)
    first = q.claim()
    assert first is not None
    q.checkpoint(first.id, "cursor:12000")

    # (a) yielded: QUEUED, holding a token, holding NO deadline. A sweep here examines only RUNNING
    #     rows, so it cannot see it at all — and there is no lapsed lease to see even if it could.
    yielded = q.get(first.id)
    assert yielded.state == QUEUED and yielded.checkpoint == "cursor:12000"
    assert yielded.lease_expires_at is None
    assert q.sweep_orphans(LIVE_RUN) == OrphanSweep()
    assert q.get(first.id).checkpoint == "cursor:12000"

    # (b) re-claimed and mid-resume, with an artificially lapsed deadline: still untouchable.
    resumed = q.claim()
    assert resumed is not None and resumed.id == first.id
    assert resumed.checkpoint == "cursor:12000"            # the cursor survived the re-claim
    q._conn.execute("UPDATE jobs SET lease_expires_at = ? WHERE id = ?",
                    ["2020-01-01T00:00:00", resumed.id])
    q._conn.commit()

    swept = q.sweep_orphans(LIVE_RUN)

    assert swept.requeued == () and swept.failed == ()
    assert swept.lease_expired == (resumed.id,)            # reported …
    live = q.get(resumed.id)
    assert live.state == RUNNING                           # … never reclaimed
    assert live.claimed_by_run == LIVE_RUN
    assert live.checkpoint == "cursor:12000"               # and the cursor is not rewound
    assert live.attempts == resumed.attempts


def test_a_lapsed_deadline_does_not_change_the_set_the_sweep_acts_on(q):
    """The set is decided by the stamp and by nothing else. Four rows — live/lapsed, live/fresh,
    dead/lapsed, dead/fresh — and the reclaimed set is exactly the two dead ones, deadlines
    irrelevant. If a deadline ever moves a row across this line, this test fails."""
    q.sweep_orphans(LIVE_RUN)
    ids = {}
    for label, owner, deadline in (("live_lapsed", LIVE_RUN, "2020-01-01T00:00:00"),
                                   ("live_fresh", LIVE_RUN, "2099-01-01T00:00:00"),
                                   ("dead_lapsed", DEAD_RUN, "2020-01-01T00:00:00"),
                                   ("dead_fresh", DEAD_RUN, "2099-01-01T00:00:00")):
        job_id = _running_row(q, "code_sync", owner=owner)
        q._conn.execute("UPDATE jobs SET lease_expires_at = ? WHERE id = ?", [deadline, job_id])
        ids[label] = job_id
    q._conn.commit()

    swept = q.sweep_orphans(LIVE_RUN)

    assert set(swept.requeued) == {ids["dead_lapsed"], ids["dead_fresh"]}
    assert swept.lease_expired == (ids["live_lapsed"],)
    assert q.get(ids["live_lapsed"]).state == RUNNING
    assert q.get(ids["live_fresh"]).state == RUNNING


def test_a_reclaimed_job_keeps_the_age_it_earned(q):
    """`created_at` must survive the reclaim — anti-starvation aging measures wait from it (Q3),
    so resetting it would push a repeatedly-orphaned job to the back of the line forever."""
    orphan = _running_row(q, "code_backfill", owner=DEAD_RUN)
    created = q.get(orphan).created_at
    attempts = q.get(orphan).attempts

    q.sweep_orphans(LIVE_RUN)

    assert q.get(orphan).created_at == created
    assert q.get(orphan).attempts == attempts     # the dead run did consume an attempt
