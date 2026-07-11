"""Cron wiring for curator + dreaming (BUILD-SPEC §9, §13).

Proves: dream/curate route to the synthesis tier; the supervisor's foreground gate keeps them
QUEUED while the owner is present and runs them in a trough — *never concurrent with
foreground use* (§13). Deterministic: warm=False, fake agents, no Ollama.
"""

from types import SimpleNamespace
from typing import cast

from config.loader import load_config
from core.models.loader import TwoSlotLoader
from core.models.ollama_client import OllamaClient
from core.models.registry import Registry
from scheduler.cron import (
    CURATE_KIND,
    DREAM_KIND,
    cron_handlers,
    enqueue_curate,
    enqueue_dream,
)
from scheduler.presence import Presence
from scheduler.queue import QUEUED, Job, JobQueue
from scheduler.router import Router
from scheduler.supervisor import Supervisor


class FakeDreamer:
    def __init__(self):
        self.runs = 0

    def dream(self):
        self.runs += 1
        return []


class FakeCurator:
    def __init__(self):
        self.runs = 0

    def curate(self):
        self.runs += 1
        return SimpleNamespace(findings=())


def _loader(cfg):
    return TwoSlotLoader(config=cfg, client=OllamaClient(cfg.ollama), registry=Registry(cfg))


def _present(active):
    return Presence(idle_probe=lambda: 0.0 if active else 10_000.0)


def test_dream_and_curate_route_to_the_synthesis_tier():
    router = Router(load_config())
    for kind in (DREAM_KIND, CURATE_KIND):
        plan = router.plan(kind)
        assert plan.tier == "synthesis"          # earns the big model, runs in troughs (§9)


def test_cron_jobs_are_gated_during_foreground_then_run_in_a_trough(tmp_path):
    cfg = load_config()
    dreamer, curator = FakeDreamer(), FakeCurator()
    router = Router(cfg)
    queue = JobQueue(tmp_path / "q.db")

    def make_supervisor(active):
        return Supervisor(queue=queue, loader=_loader(cfg),
                          handlers=cron_handlers(dreamer, curator),
                          presence=_present(active), warm=False)

    d = enqueue_dream(queue, router)
    c = enqueue_curate(queue, router)

    # Owner present: both are synthesis-tier, so the foreground gate blocks them.
    present = make_supervisor(active=True)
    present.loader.ensure_pinned(warm=False)
    assert present.run() == 0
    assert queue.get(d.id).state == QUEUED and queue.get(c.id).state == QUEUED
    assert dreamer.runs == 0 and curator.runs == 0

    # Trough (owner idle): both run.
    trough = make_supervisor(active=False)
    trough.loader.ensure_pinned(warm=False)
    assert trough.run() == 2
    assert dreamer.runs == 1 and curator.runs == 1


def test_cron_handlers_summarize_results(tmp_path):
    handlers = cron_handlers(FakeDreamer(), FakeCurator())
    # Both handlers ignore their Job argument entirely (see scheduler/cron.py) -- a bare
    # placeholder is the right test double; the cast says "this never matters here."
    job = cast(Job, SimpleNamespace())
    dream_result = handlers[DREAM_KIND](job)
    curate_result = handlers[CURATE_KIND](job)
    assert dream_result is not None and "theme" in dream_result
    assert curate_result is not None and "finding" in curate_result
