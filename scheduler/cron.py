"""Cron / trough jobs — wiring the curator + dreaming agents into the supervisor
(BUILD-SPEC §9, §13).

These are the §9 cognitive-tier jobs that "earn the big model": dreaming synthesis and
curation. Both kinds already route to the **synthesis** tier (`scheduler.router`), and the
supervisor's foreground gate keeps that tier out of foreground time (`HEAVY_TIERS`) — so
these run **trough-only, never concurrent with the owner's use** (§13), and the two-slot
loader's ceiling + swap discipline apply to them for free.

This module only builds the handlers and the enqueue helpers; the supervisor owns the loop.
A full dreaming pass is run-to-completion here (the dreamer caps `max_clusters`); rewriting
it as checkpointed per-cluster steps (the `queue.checkpoint` seam, roadmap §7) is a later
refinement if a pass ever grows long enough to want to yield mid-way.
"""

from __future__ import annotations

from collections.abc import Callable

from core.curator import Curator
from core.dreaming import Dreamer
from scheduler.queue import Job, JobQueue
from scheduler.router import Router

DREAM_KIND = "dream"
CURATE_KIND = "curate"

Handler = Callable[[Job], "str | None"]


def dream_handler(dreamer: Dreamer) -> Handler:
    def handle(_job: Job) -> str:
        themes = dreamer.dream()
        grounded = sum(1 for t in themes if t.check.passed)
        return f"dreamed {len(themes)} theme(s); {grounded} grounded"
    return handle


def curate_handler(curator: Curator) -> Handler:
    def handle(_job: Job) -> str:
        report = curator.curate()
        return f"flagged {len(report.findings)} finding(s)"
    return handle


def cron_handlers(dreamer: Dreamer, curator: Curator) -> dict[str, Handler]:
    """The handler map for a supervisor that runs the trough jobs."""
    return {DREAM_KIND: dream_handler(dreamer), CURATE_KIND: curate_handler(curator)}


def enqueue_dream(queue: JobQueue, router: Router) -> Job:
    plan = router.plan(DREAM_KIND)          # -> synthesis tier, background priority
    return queue.enqueue(plan.kind, plan.tier, plan.num_ctx, priority=plan.priority)


def enqueue_curate(queue: JobQueue, router: Router) -> Job:
    plan = router.plan(CURATE_KIND)         # -> synthesis tier, background priority
    return queue.enqueue(plan.kind, plan.tier, plan.num_ctx, priority=plan.priority)
