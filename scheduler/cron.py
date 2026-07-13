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
from core.ingest.embed import Embedder
from core.research.airlock import ResearchAirlock
from core.research.criteria import ResearchCriteria
from core.stores.vectorstore import VectorStore
from scheduler.queue import Job, JobQueue
from scheduler.research import (
    RESEARCH_KIND,
    criteria_from_request,
    render_ranked,
    run_research,
)
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


# --- research: the dormant airlock, wired as a trough job (bp-028, §16) ----------------------
# `"research"` is already a synthesis kind (router.py:31) → same trough discipline as dreaming:
# background priority + the supervisor's HEAVY_TIERS foreground gate keep it out of the owner's
# conversation time (§13). The airlock diode is one-way filesystem; the handler never touches
# the network and never persists a paper (transient — persistence is bp-029).
def research_handler(airlock: ResearchAirlock, embedder: Embedder, store: VectorStore) -> Handler:
    """Run one research job: reconstruct the de-identified criteria from the payload, drive
    `emit → collect → rank`, and return a plain reading list. If no criteria is present, or no
    result is back from the fetcher yet, it degrades to a plain message — never raises."""
    def handle(job: Job) -> str:
        request = job.payload.get("criteria")
        if not request:
            return "research: no criteria in payload"
        criteria = criteria_from_request(request)
        ranked = run_research(criteria, airlock, embedder, store)
        return render_ranked(ranked)
    return handle


def enqueue_research(queue: JobQueue, router: Router, criteria: ResearchCriteria) -> Job:
    """Enqueue a research job (synthesis tier, background — trough-gated). The payload carries the
    ALREADY de-identified criteria (`to_request()`), never raw query text (Inv 11): the criteria
    was scrubbed by `research_criteria`/`deidentify` at the enqueue boundary, and `emit()` will
    re-assert cleanliness on the way out."""
    plan = router.plan(RESEARCH_KIND)       # -> synthesis tier, background priority
    return queue.enqueue(plan.kind, plan.tier, plan.num_ctx, priority=plan.priority,
                         payload={"criteria": criteria.to_request(), "topic": criteria.topic})
