"""The research trough job — routing, the foreground gate, and the drain (bp-028 Item 24).

Proves: `"research"` routes to the synthesis tier at BACKGROUND priority; the supervisor's
foreground gate keeps it QUEUED while the owner is present and runs it in a trough (§13); and
draining the queue invokes the Item-23 driver (emit → collect → rank), returning a plain
reading list. Deterministic: warm=False, a fake airlock, a stubbed note retrieval, no Ollama.
"""

from __future__ import annotations

from typing import cast

import core.research.rank as rank_mod
from config.loader import load_config
from core.ingest.embed import Embedder
from core.models.loader import TwoSlotLoader
from core.models.ollama_client import OllamaClient
from core.models.registry import Registry
from core.research.airlock import ResearchAirlock, ResearchResult
from core.research.criteria import Paper, ResearchCriteria, deidentify
from core.stores.vectorstore import VectorStore
from scheduler.cron import enqueue_research, research_handler
from scheduler.presence import Presence
from scheduler.queue import DONE, PRIORITY_BACKGROUND, QUEUED, JobQueue
from scheduler.research import RESEARCH_KIND
from scheduler.router import Router
from scheduler.supervisor import Supervisor


class FakeEmbedder:
    def _vec(self, text: str) -> list[float]:
        return [1.0, 0.0, 0.0] if "migraine" in text.lower() else [0.0, 0.0, 1.0]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._vec(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vec(text)


class FakeAirlock:
    def __init__(self, result: ResearchResult | None):
        self._result = result
        self.emitted: list[ResearchCriteria] = []

    def emit(self, criteria: ResearchCriteria) -> str:
        criteria.assert_clean()
        self.emitted.append(criteria)
        return criteria.id

    def collect_one(self, criteria_id: str, *, consume: bool = True) -> ResearchResult | None:
        if self._result is None or self._result.criteria_id != criteria_id:
            return None
        return self._result


def _paper(pid: str, title: str) -> Paper:
    return Paper(source="openalex", id=pid, title=title, abstract="abstract", year=2020,
                 venue="V", type="review", doi="10.1/x", url="https://doi.org/10.1/x",
                 is_preprint=False)


def _result(criteria_id: str) -> ResearchResult:
    return ResearchResult(criteria_id=criteria_id,
                          papers=(_paper("rel", "Migraine prophylaxis review"),),
                          sources_queried=("openalex",), ts="2026-07-13T00:00:00")


def _emb() -> Embedder:
    return cast(Embedder, FakeEmbedder())


def _store() -> VectorStore:
    return cast(VectorStore, object())          # ranking's store use is stubbed via semantic_search


def _airlock(al: FakeAirlock) -> ResearchAirlock:
    return cast(ResearchAirlock, al)


def _loader(cfg):
    return TwoSlotLoader(config=cfg, client=OllamaClient(cfg.ollama), registry=Registry(cfg))


def _present(active):
    return Presence(idle_probe=lambda: 0.0 if active else 10_000.0)


def test_research_routes_to_synthesis_background():
    router = Router(load_config())
    plan = router.plan(RESEARCH_KIND)
    assert plan.tier == "synthesis"                 # earns the big model, runs in troughs (§9)
    assert plan.priority == PRIORITY_BACKGROUND      # never foreground (§13)


def test_research_is_gated_during_foreground_then_runs_in_a_trough(tmp_path, monkeypatch):
    monkeypatch.setattr(rank_mod, "semantic_search", lambda *a, **k: [{"text": "migraine notes"}])
    cfg = load_config()
    router = Router(cfg)
    queue = JobQueue(tmp_path / "q.db")

    criteria = deidentify("migraine prophylaxis", ["migraine prophylaxis", "migraine"])
    airlock = FakeAirlock(_result(criteria.id))
    handler = research_handler(_airlock(airlock), _emb(), store=_store())

    def make_supervisor(active):
        return Supervisor(queue=queue, loader=_loader(cfg),
                          handlers={RESEARCH_KIND: handler},
                          presence=_present(active), warm=False)

    job = enqueue_research(queue, router, criteria)
    # The enqueued payload is de-identified — no raw query text crosses into the queue (Inv 11).
    assert set(job.payload["criteria"]) == {"id", "topic", "terms", "filters"}

    # Owner present: synthesis tier → the foreground gate blocks it.
    present = make_supervisor(active=True)
    present.loader.ensure_pinned(warm=False)
    assert present.run() == 0
    assert queue.get(job.id).state == QUEUED
    assert airlock.emitted == []                     # nothing emitted while gated

    # Trough (owner idle): it runs — emit happened, the driver ranked, the result is surfaced.
    trough = make_supervisor(active=False)
    trough.loader.ensure_pinned(warm=False)
    assert trough.run() == 1
    done = queue.get(job.id)
    assert done.state == DONE
    assert len(airlock.emitted) == 1                 # the driver emitted the de-identified request
    assert done.result is not None and "Migraine prophylaxis review" in done.result


def test_research_handler_degrades_when_no_result_yet(tmp_path, monkeypatch):
    monkeypatch.setattr(rank_mod, "semantic_search", lambda *a, **k: [])
    cfg = load_config()
    router = Router(cfg)
    queue = JobQueue(tmp_path / "q.db")
    criteria = deidentify("migraine prophylaxis", ["migraine prophylaxis"])
    airlock = FakeAirlock(None)                      # fetcher has not responded / is absent
    handler = research_handler(_airlock(airlock), _emb(), store=_store())

    job = enqueue_research(queue, router, criteria)
    result = handler(queue.get(job.id))
    assert len(airlock.emitted) == 1                 # request emitted
    assert result is not None and "nothing has come back" in result.lower()  # graceful, not a crash
