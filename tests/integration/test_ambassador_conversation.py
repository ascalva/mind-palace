"""The Ambassador conversation loop, end to end through the real gateway → handoff → inbox path
(Track B — the definition-of-done as a test).

Uses the real machinery (LocalAdapter, GatewayChannel, CoreInbox, the queue, the stores) with
only the two model-backed pieces faked, over a throwaway temp config. Proves the owner can:
retrieve, see the exchange land as authored-dialogue, ask status, delegate a task and get a
DEFERRED result on a later turn — the "interact meaningfully" bar.
"""

import dataclasses

from config.loader import load_config
from core.ingest.index import semantic_search
from core.kernel.clearance import MIRROR_READ
from core.kernel.provenance import Provenance
from core.kernel.stores.rawstore import RawStore
from core.stores.vectorstore import VectorStore
from scheduler.interface import build_conversation_runtime
from tests.fixtures.clearances import grant
from tests.fixtures.fakes import HashingEmbedder, ReplyServer

DIM = 32


def _runtime(tmp_path):
    base = load_config()
    paths = dataclasses.replace(
        base.paths, data_dir=tmp_path, raw_store=tmp_path / "raw",
        vector_store=tmp_path / "v.lance", vault_catalog=tmp_path / "cat.sqlite",
        attestation_store=tmp_path / "att.sqlite", derived_store=tmp_path / "d.sqlite",
        telemetry_db=tmp_path / "t.duckdb",
    )
    itf = dataclasses.replace(base.interface, handoff_dir=tmp_path / "handoff")
    cfg = dataclasses.replace(base, paths=paths, interface=itf,
                              embedding=dataclasses.replace(base.embedding, dim=DIM))
    emb = HashingEmbedder(DIM)
    store = VectorStore(cfg.paths.vector_store, dim=DIM)
    # Seed notes that are genuinely raw-backed: the Librarian now verifies each retrieved chunk
    # against the immutable raw store (audit G9.5), so a row's text must reproduce from a real blob
    # (each short note is a single chunk equal to its own text). This keeps RETRIEVE exercising the
    # real path rather than silently dropping raw-less rows.
    raw = RawStore(cfg.paths.raw_store)
    t1 = "racing thoughts at night; slow breathing helps me sleep"
    t2 = "deadline pressure; I get short with people when stressed at work"
    d1, _ = raw.add_text(t1)
    d2, _ = raw.add_text(t2)
    store.add([
        {"id": f"{d1}:0", "digest": d1, "title": "sleep", "source_path": "/sleep",
         "chunk_index": 0, "provenance": "authored-solo", "text": t1,
         "vector": emb.embed_documents(["racing thoughts at night slow breathing sleep"])[0]},
        {"id": f"{d2}:0", "digest": d2, "title": "work", "source_path": "/work",
         "chunk_index": 0, "provenance": "authored-solo", "text": t2,
         "vector": emb.embed_documents(["deadline pressure stressed at work"])[0]},
    ])

    def fn(_tier, messages):
        return "Based on your notes, here's what I see."

    runtime = build_conversation_runtime(cfg, server=ReplyServer(fn=fn), embedder=emb, store=store)
    return runtime, store, emb


def test_full_conversation_loop(tmp_path):
    runtime, store, emb = _runtime(tmp_path)

    # 1) RETRIEVE — a grounded answer from the mirror.
    r1 = runtime.send("what did I write about sleep?")
    assert "your notes" in r1.lower()

    # 2) the exchange landed as authored-dialogue, retrievable on a later search (the capture loop)
    dialogue = store.all_rows(clearance=grant(Provenance.AUTHORED_DIALOGUE))
    assert any("sleep" in r["text"] for r in dialogue)
    hits = semantic_search("what did I write about sleep", emb, store, k=3,
                           clearance=MIRROR_READ)
    assert any(h["provenance"] == "authored-dialogue" for h in hits)

    # 3) STATUS — plain-language narration of what it's been doing.
    r3 = runtime.send("what have you been doing?")
    assert "logged" in r3.lower() or "recorded" in r3.lower()

    # 4) TASK — delegated; effort narrated, nothing answered inline.
    r4 = runtime.send("look into whether I get stressed at work")
    assert "dig" in r4.lower()
    assert runtime.run_pending_tasks() == 1            # the supervisor stand-in completes it

    # 5) the DEFERRED result is delivered on the next turn (an expected update).
    r5 = runtime.send("any update?")
    assert "here's what i found" in r5.lower()

    runtime.queue.close()


def test_capture_then_recall_across_turns(tmp_path):
    runtime, store, emb = _runtime(tmp_path)
    runtime.send("I have been feeling unusually optimistic about the move to the coast")
    # a later retrieval surfaces the captured dialogue turn
    hits = semantic_search("optimistic about the coast move", emb, store, k=3,
                           clearance=MIRROR_READ)
    assert hits and any(h["provenance"] == "authored-dialogue" for h in hits)
    runtime.queue.close()


def test_run_pending_tasks_claims_a_job_before_it_runs_it(tmp_path):
    """The in-process runner claims each job (QUEUED -> RUNNING, one attempt) before the handler
    runs and leaves a kind it has no handler for QUEUED. The old runner completed rows it never
    claimed, so the handler saw a QUEUED row with no attempt."""
    runtime, _store, _emb = _runtime(tmp_path)
    q = runtime.queue
    task = q.enqueue("ambassador_task", "synthesis", 4096, priority=5, payload={"q": "x"})
    other = q.enqueue("some_other_kind", "synthesis", 4096, priority=5)
    seen: list[tuple[str, int]] = []

    def handler(job):
        row = q.get(job.id)
        seen.append((row.state, row.attempts))
        return "done"

    runtime.task_handler = handler
    assert runtime.run_pending_tasks() == 1
    assert seen == [("running", 1)]
    assert q.get(task.id).state == "done"
    assert q.get(other.id).state == "queued"             # not ours: untouched, not claimed
    q.close()


def test_talk_leaves_delegated_work_to_a_live_daemon(tmp_path, capsys):
    """One writer: with a daemon live the REPL's runner claims nothing and says so; with none it
    claims and completes. The old REPL ran the jobs itself either way."""
    from scripts.talk import run_delegated

    runtime, _store, _emb = _runtime(tmp_path)
    q = runtime.queue
    job = q.enqueue("ambassador_task", "synthesis", 4096, priority=5, payload={"q": "x"})
    runtime.task_handler = lambda j: "done"

    class _Live:
        id = 7

    assert run_delegated(runtime, _Live()) == 0
    assert "run #7 is live" in capsys.readouterr().out
    assert q.get(job.id).state == "queued" and q.get(job.id).attempts == 0

    assert run_delegated(runtime, None) == 1             # no daemon: claimed and completed
    assert q.get(job.id).state == "done"
    q.close()
