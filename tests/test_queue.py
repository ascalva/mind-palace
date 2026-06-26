"""Durable job queue (BUILD-SPEC §8, §13): priority, swap-avoidance, foreground gate,
lifecycle transitions, defer/revive, and checkpoint-requeue."""

from scheduler.queue import (
    DEFERRED,
    DONE,
    FAILED,
    PRIORITY_BACKGROUND,
    PRIORITY_DEFAULT,
    PRIORITY_REACTIVE,
    QUEUED,
    RUNNING,
    JobQueue,
)


def _q(tmp_path):
    return JobQueue(tmp_path / "q.db")


def test_enqueue_get_and_depth(tmp_path):
    q = _q(tmp_path)
    j = q.enqueue("librarian", "routine", 16384)
    assert j.state == QUEUED and j.tier == "routine" and j.num_ctx == 16384
    assert q.depth() == 1
    assert q.get(j.id).kind == "librarian"


def test_claim_orders_by_priority(tmp_path):
    q = _q(tmp_path)
    q.enqueue("dream", "synthesis", 32768, priority=PRIORITY_BACKGROUND)
    hi = q.enqueue("route", "router", 8192, priority=PRIORITY_REACTIVE)
    got = q.claim()
    assert got.id == hi.id and got.state == RUNNING and got.attempts == 1


def test_claim_avoids_swap_within_priority_band(tmp_path):
    q = _q(tmp_path)
    q.enqueue("a", "synthesis", 32768, priority=PRIORITY_DEFAULT)   # would force a swap
    match = q.enqueue("b", "routine", 16384, priority=PRIORITY_DEFAULT)  # matches loaded
    got = q.claim(loaded_key=("routine", 16384))
    assert got.id == match.id   # no-swap preferred over FIFO within the band


def test_claim_skips_blocked_tiers_and_leaves_them_queued(tmp_path):
    q = _q(tmp_path)
    syn = q.enqueue("dream", "synthesis", 32768)
    assert q.claim(blocked_tiers=frozenset({"synthesis"})) is None
    assert q.get(syn.id).state == QUEUED   # gated, not consumed


def test_complete_and_fail(tmp_path):
    q = _q(tmp_path)
    j = q.enqueue("x", "routine", 16384)
    q.claim()
    q.complete(j.id, "ok")
    assert q.get(j.id).state == DONE and q.get(j.id).result == "ok"

    k = q.enqueue("y", "routine", 16384)
    q.claim()
    q.fail(k.id, "boom")
    assert q.get(k.id).state == FAILED and "boom" in q.get(k.id).error


def test_defer_then_revive(tmp_path):
    q = _q(tmp_path)
    j = q.enqueue("big", "stretch", 32768)
    q.claim()
    q.defer(j.id, "ceiling")
    assert q.get(j.id).state == DEFERRED
    assert q.claim() is None              # deferred jobs are not re-selected
    assert q.revive_deferred() == 1
    assert q.claim().id == j.id


def test_checkpoint_requeues_with_token(tmp_path):
    q = _q(tmp_path)
    j = q.enqueue("dream", "synthesis", 32768)
    q.claim()
    q.checkpoint(j.id, "step-2")
    jj = q.get(j.id)
    assert jj.state == QUEUED and jj.checkpoint == "step-2" and q.depth() == 1


def test_counts(tmp_path):
    q = _q(tmp_path)
    q.enqueue("x", "routine", 16384)
    q.enqueue("y", "routine", 16384)
    got = q.claim()
    q.complete(got.id, None)
    assert q.counts() == {QUEUED: 1, DONE: 1}
