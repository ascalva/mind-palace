"""The foreground research path — Ambassador TASK-intent → airlock (bp-028 Item 25).

A research-shaped TASK routes to the `"research"` airlock kind (de-identified criteria only),
narrates the effort, and surfaces the ranked reading list on a later turn — while a non-research
TASK still routes to the existing `librarian.answer` path (no regression). Driven through the
real gateway → handoff → inbox → Ambassador path with only the model + the fetcher faked.
"""

from __future__ import annotations

import dataclasses
from typing import cast

from config.loader import load_config
from core.librarian import Librarian
from core.research.airlock import ResearchResult
from core.research.criteria import Paper, ResearchCriteria
from core.stores.rawstore import RawStore
from core.stores.vectorstore import VectorStore
from scheduler.interface import (
    AMBASSADOR_TASK_KIND,
    build_conversation_runtime,
    build_task_delegation,
)
from scheduler.queue import JobQueue
from scheduler.research import RESEARCH_KIND
from scheduler.router import Router
from tests.fixtures.fakes import HashingEmbedder, ReplyServer

DIM = 32


class RespondingAirlock:
    """A Zone-C fetcher that has already answered: it records the de-identified request emitted
    and returns a canned public-literature result keyed to it (so the driver can rank it)."""

    def __init__(self) -> None:
        self._id: str | None = None

    def emit(self, criteria: ResearchCriteria) -> str:
        criteria.assert_clean()          # the real airlock re-asserts; keep the firewall honest
        self._id = criteria.id
        return criteria.id

    def collect_one(self, criteria_id: str, *, consume: bool = True) -> ResearchResult | None:
        if criteria_id != self._id:
            return None
        paper = Paper(source="openalex", id="rel", title="Migraine prophylaxis review",
                      abstract="abstract", year=2020, venue="Headache", type="review",
                      doi="10.1/x", url="https://doi.org/10.1/x", is_preprint=False)
        return ResearchResult(criteria_id=criteria_id, papers=(paper,),
                              sources_queried=("openalex",), ts="2026-07-13T00:00:00")


def _runtime(tmp_path, airlock):
    base = load_config()
    paths = dataclasses.replace(
        base.paths, data_dir=tmp_path, raw_store=tmp_path / "raw",
        vector_store=tmp_path / "v.lance", vault_catalog=tmp_path / "cat.sqlite",
        attestation_store=tmp_path / "att.sqlite", derived_store=tmp_path / "d.sqlite",
        telemetry_db=tmp_path / "t.duckdb",
    )
    itf = dataclasses.replace(base.interface, handoff_dir=tmp_path / "handoff")
    al = dataclasses.replace(base.airlock, handoff_dir=tmp_path / "airlock")
    cfg = dataclasses.replace(base, paths=paths, interface=itf, airlock=al,
                              embedding=dataclasses.replace(base.embedding, dim=DIM))
    emb = HashingEmbedder(DIM)
    store = VectorStore(cfg.paths.vector_store, dim=DIM)
    raw = RawStore(cfg.paths.raw_store)
    t1 = "migraine triggers I have noticed; bright light and skipped meals"
    d1, _ = raw.add_text(t1)
    vec = emb.embed_documents(["migraine triggers bright light skipped meals"])[0]
    store.add([{"id": f"{d1}:0", "digest": d1, "title": "migraine", "source_path": "/m",
                "chunk_index": 0, "provenance": "authored-solo", "text": t1, "vector": vec}])

    def fn(_tier, messages):
        return "Based on your notes, here's what I see."

    runtime = build_conversation_runtime(cfg, server=ReplyServer(fn=fn), embedder=emb,
                                         store=store, airlock=airlock)
    return runtime


def test_research_task_enqueues_a_deidentified_research_job(tmp_path):
    runtime = _runtime(tmp_path, RespondingAirlock())
    reply = runtime.send("do some research on migraine prophylaxis papers")

    # The effort is narrated (nothing answered inline); a research job — not a task — is queued.
    assert "dig" in reply.lower() or "come back" in reply.lower()
    jobs = runtime.queue.list()
    research = [j for j in jobs if j.kind == RESEARCH_KIND]
    assert len(research) == 1
    job = research[0]
    # De-identified: the payload carries scrubbed criteria, NOT raw conversation text (Inv 11).
    assert set(job.payload["criteria"]) == {"id", "topic", "terms", "filters"}
    assert "query" not in job.payload
    assert job.payload["conversation"] == "default"
    runtime.queue.close()


def test_nonresearch_task_still_routes_to_the_answer_path(tmp_path):
    runtime = _runtime(tmp_path, RespondingAirlock())
    runtime.send("look into whether I get short with people when stressed")
    jobs = runtime.queue.list()
    # No research job; the existing ambassador_task path carries the raw query (unchanged behavior).
    assert not any(j.kind == RESEARCH_KIND for j in jobs)
    task = [j for j in jobs if j.kind == AMBASSADOR_TASK_KIND]
    assert len(task) == 1
    assert "query" in task[0].payload
    runtime.queue.close()


def test_research_result_surfaces_on_a_later_turn(tmp_path):
    runtime = _runtime(tmp_path, RespondingAirlock())
    runtime.send("do some research on migraine prophylaxis papers")
    assert runtime.run_pending_tasks() == 1          # the supervisor stand-in drives the airlock

    surfaced = runtime.send("thanks")
    # The transiently-ranked reading list comes back as an expected update (public titles, safe).
    assert "here's what i found" in surfaced.lower()
    assert "Migraine prophylaxis review" in surfaced
    runtime.queue.close()


def test_delegate_without_a_librarian_never_routes_to_research(tmp_path):
    # Structural guard: with no librarian wired, the research route is OFF — even an explicitly
    # research-shaped query stays on the general task path (the de-identify seam is mandatory).
    queue = JobQueue(tmp_path / "q.db")
    delegate, _ = build_task_delegation(queue, Router(load_config()))   # no librarian
    ref = delegate("do some research on migraine prophylaxis papers", "conv")
    assert queue.get(int(ref)).kind == AMBASSADOR_TASK_KIND
    queue.close()


def test_undeidentifiable_research_query_falls_back_closed(tmp_path):
    # A research-shaped query that yields no de-identifiable terms must FAIL CLOSED (nothing
    # emitted) and fall back to the general path — never crash the turn (§11 default-on-doubt).
    from core.research.criteria import DeidentificationError

    class RefusingLibrarian:
        def research_criteria(self, query: str, **_kw: object):
            raise DeidentificationError("no usable de-identified terms remained")

    queue = JobQueue(tmp_path / "q.db")
    librarian = cast(Librarian, RefusingLibrarian())
    delegate, _ = build_task_delegation(queue, Router(load_config()), librarian=librarian)
    ref = delegate("do some research on the literature", "conv")
    # Fell back to the general task path — no research job, no crash.
    assert queue.get(int(ref)).kind == AMBASSADOR_TASK_KIND
    assert not any(j.kind == RESEARCH_KIND for j in queue.list())
    queue.close()
