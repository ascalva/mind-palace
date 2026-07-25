"""bp-101 Item 3 — enqueue coalescing for idempotent kinds (finding-0170).

The measured defect: with the single worker pinned by a long job, `chat_sync`/`vault_sync` stacked
13 → 1,766 queued rows in ~21 h, unbounded. The fix collapses an idempotent kind onto the row
already waiting.

Three guards are load-bearing here, each with its own test:

* **only QUEUED rows collapse** — `test_a_kind_running_not_queued_still_enqueues` is the falsifier
  from plan §7 Item 3: a `code_backfill` requested while one is RUNNING must still insert, or the
  follow-up pass silently never happens;
* **the key is `(kind, payload)`** — distinct payloads must produce distinct rows;
* **the FIRST row wins** — `created_at` is what anti-starvation aging measures (Q3).
"""

from __future__ import annotations

import pytest

from scheduler.queue import (
    _IDEMPOTENT_KINDS,
    PRIORITY_BACKGROUND,
    PRIORITY_DEFAULT,
    PRIORITY_REACTIVE,
    QUEUED,
    RUNNING,
    JobQueue,
)


@pytest.fixture
def q(tmp_path):
    queue = JobQueue(tmp_path / "q.sqlite")
    yield queue
    queue.close()


def test_idempotent_kind_literals_match_the_kind_constants():
    """`_IDEMPOTENT_KINDS` holds string literals because the handler modules import
    `scheduler.queue` (importing them back would cycle). This test is what keeps that duplication
    honest: rename a kind constant and it fails here rather than silently disabling coalescing."""
    from scheduler.chat_sync import CHAT_SYNC_KIND
    from scheduler.code_sync import CODE_BACKFILL_KIND, CODE_SYNC_KIND
    from scheduler.cron import (
        CHAT_EVENTS_KIND,
        CURATE_KIND,
        DREAM_KIND,
        INTEGRATE_KIND,
        SHADOW_KIND,
    )
    from scheduler.interface import AMBASSADOR_KIND, AMBASSADOR_TASK_KIND
    from scheduler.research import RESEARCH_KIND
    from scheduler.vault_sync import VAULT_SYNC_KIND

    assert _IDEMPOTENT_KINDS == {
        CHAT_SYNC_KIND, VAULT_SYNC_KIND, CODE_SYNC_KIND, CODE_BACKFILL_KIND,
        CHAT_EVENTS_KIND, INTEGRATE_KIND,
    }
    # The classification's other half, asserted rather than assumed: model-driven passes mint fresh
    # ledger rows per call, and payload-bearing kinds must never be swallowed by a sibling.
    for not_collapsible in (DREAM_KIND, CURATE_KIND, SHADOW_KIND, RESEARCH_KIND,
                            AMBASSADOR_TASK_KIND, AMBASSADOR_KIND):
        assert not_collapsible not in _IDEMPOTENT_KINDS


def test_a_thousand_chat_syncs_with_no_drain_produce_exactly_one_row(q):
    """The acceptance test — the 1,766-row pileup, reproduced and bounded."""
    first = q.enqueue("chat_sync", "pinned", 8192, priority=PRIORITY_BACKGROUND)
    for _ in range(999):
        again = q.enqueue("chat_sync", "pinned", 8192, priority=PRIORITY_BACKGROUND)
        assert again.id == first.id          # `enqueue` still returns a Job — the EXISTING one
    assert q.depth() == 1
    assert len(q.list(QUEUED)) == 1


def test_a_kind_running_not_queued_still_enqueues(q):
    """THE FALSIFIER (plan §7 Item 3). `code_backfill` is claimed and RUNNING; a fresh request
    arrives. Collapsing onto the running row would silently cancel the follow-up pass — the
    request would report success and the work would never happen."""
    first = q.enqueue("code_backfill", "pinned", 8192, priority=PRIORITY_BACKGROUND)
    claimed = q.claim()
    assert claimed is not None and claimed.id == first.id and claimed.state == RUNNING

    second = q.enqueue("code_backfill", "pinned", 8192, priority=PRIORITY_BACKGROUND)

    assert second.id != first.id
    assert second.state == QUEUED
    assert q.depth() == 1


def test_collapsing_ignores_terminal_and_deferred_rows(q):
    """A completed/failed/deferred sync must not absorb a new request either — same falsifier,
    different resting state."""
    done = q.enqueue("vault_sync", "pinned", 8192)
    q.complete(done.id, "ok")
    failed = q.enqueue("vault_sync", "pinned", 8192)
    q.fail(failed.id, "boom")
    deferred = q.enqueue("vault_sync", "pinned", 8192)
    q.defer(deferred.id, "ceiling")

    fresh = q.enqueue("vault_sync", "pinned", 8192)
    assert fresh.id not in {done.id, failed.id, deferred.id}
    assert fresh.state == QUEUED


def test_distinct_payloads_produce_distinct_rows(q):
    """The key is `(kind, payload)`, never `kind` alone — a payload-bearing job is never dropped
    into an unrelated one. (No collapsible kind carries a payload today; this holds the door.)"""
    a = q.enqueue("code_sync", "pinned", 8192, payload={"repo": "alpha"})
    b = q.enqueue("code_sync", "pinned", 8192, payload={"repo": "beta"})
    c = q.enqueue("code_sync", "pinned", 8192, payload={"repo": "alpha"})
    bare = q.enqueue("code_sync", "pinned", 8192)

    assert len({a.id, b.id, bare.id}) == 3     # three genuinely different requests
    assert c.id == a.id                        # same payload -> collapses
    assert q.depth() == 3


def test_non_collapsible_kinds_behave_exactly_as_before(q):
    for kind in ("dream", "curate", "shadow", "research", "ambassador_task", "ambassador",
                 "librarian", "some_future_kind"):
        first = q.enqueue(kind, "synthesis", 32768)
        second = q.enqueue(kind, "synthesis", 32768)
        assert first.id != second.id, f"{kind} must not collapse"


def test_the_first_row_wins_so_aging_is_preserved(q):
    """Q3: `_effective_priority` measures wait from `created_at`. Collapsing onto a FRESH row would
    reset that clock, so a kind that sustained load keeps re-enqueueing could starve forever."""
    first = q.enqueue("chat_sync", "pinned", 8192)
    q._conn.execute("UPDATE jobs SET created_at = ? WHERE id = ?",
                    ["2026-07-24T01:00:00", first.id])
    q._conn.commit()

    again = q.enqueue("chat_sync", "pinned", 8192)

    assert again.id == first.id
    assert again.created_at == "2026-07-24T01:00:00"      # the age it earned, not now


def test_collapsing_never_demotes_and_may_promote(q):
    """A collapse must not lose urgency: if the incoming request is more urgent than the row that
    is waiting, the waiting row is promoted (its `created_at`, and so its aging, stands)."""
    background = q.enqueue("chat_sync", "pinned", 8192, priority=PRIORITY_BACKGROUND)

    promoted = q.enqueue("chat_sync", "pinned", 8192, priority=PRIORITY_REACTIVE)
    assert promoted.id == background.id and promoted.priority == PRIORITY_REACTIVE

    unchanged = q.enqueue("chat_sync", "pinned", 8192, priority=PRIORITY_DEFAULT)
    assert unchanged.id == background.id and unchanged.priority == PRIORITY_REACTIVE
    assert q.depth() == 1


def test_a_different_tier_or_window_does_not_collapse(q):
    """The match key is narrowed with `tier`/`num_ctx` — routing is deterministic per kind today,
    so this never fires in production; it is here so a future re-route cannot mis-tier a job by
    folding it into a row planned for a different model load."""
    pinned = q.enqueue("chat_sync", "pinned", 8192)
    other_tier = q.enqueue("chat_sync", "routine", 8192)
    other_ctx = q.enqueue("chat_sync", "pinned", 16384)
    assert len({pinned.id, other_tier.id, other_ctx.id}) == 3


def test_a_reclaimed_orphan_is_a_collapse_target_again(q):
    """The two halves compose: after `sweep_orphans` puts an idempotent job back to QUEUED, later
    enqueues fold into it instead of stacking behind it."""
    first = q.enqueue("code_sync", "pinned", 8192)
    q._conn.execute("UPDATE jobs SET state = ?, claimed_by_run = ? WHERE id = ?",
                    [RUNNING, 35, first.id])
    q._conn.commit()

    assert q.enqueue("code_sync", "pinned", 8192).id != first.id   # running -> a new row
    q.sweep_orphans(36)
    assert q.depth() == 2
    assert q.enqueue("code_sync", "pinned", 8192).id == first.id   # reclaimed -> the oldest wins
