"""The door (`core/ingest/door.py`, `scheduler/door.py`; dn-ingest-door D3, D5, D7): a command is
spooled under its role, the daemon drains the spool with the role bound to the directory, the
handler compiles again and lands, text never enters the queue, and a request a role may not say is
refused where it would have written. Hermetic: a temporary handoff directory and fakes."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from core.ingest import door
from core.kernel.config import get_config
from core.query import AMBASSADOR_OVERLAY, OPERATOR
from core.sentence import IllScopedSentence, ast, compile_sentence
from core.sentence.ast import Capture, Link
from scheduler.door import door_handler, drain_spool
from scheduler.queue import PRIORITY_BACKGROUND, PRIORITY_INTERACTIVE, Job
from scheduler.router import Router


@pytest.fixture
def cfg(tmp_path: Path) -> Any:
    base = get_config()
    return replace(base, interface=replace(base.interface, handoff_dir=tmp_path / "handoff"))


class _Queue:
    """Records enqueues; hands back a job with a fresh id."""

    def __init__(self) -> None:
        self.jobs: list[dict[str, Any]] = []

    def enqueue(self, kind: str, tier: str, num_ctx: int, *, priority: int = 0,
                payload: dict[str, Any] | None = None) -> Job:
        self.jobs.append({"kind": kind, "tier": tier, "priority": priority,
                          "payload": dict(payload or {}), "state": "queued"})
        return self._job(len(self.jobs))

    def list(self, state: str | None = None) -> list[Job]:
        return [self._job(i + 1) for i, j in enumerate(self.jobs)
                if state is None or j["state"] == state]

    def _job(self, i: int) -> Job:
        j = self.jobs[i - 1]
        return Job(id=i, kind=j["kind"], tier=j["tier"], num_ctx=1, priority=j["priority"],
                   state=j["state"], payload=dict(j["payload"]), result=None, error=None,
                   attempts=0, checkpoint=None, created_at="", started_at=None,
                   finished_at=None)


def _spooled(cfg: Any, role: str) -> list[Path]:
    return sorted((door.spool_root(cfg) / role).glob("*.json"))


# ── the spool ───────────────────────────────────────────────────────────────────────────────────


def test_a_command_is_spooled_under_its_role_and_names_no_role_itself(cfg: Any) -> None:
    plan = compile_sentence("do dream", door.grant_for("ambassador"))
    receipt = door.write_request(cfg, role="ambassador", plan=plan)
    assert receipt.state == "spooled" and receipt.kind == "dream" and receipt.job is None
    assert "sentence" not in receipt.to_dict()           # the request file is the text's one home
    (path,) = _spooled(cfg, "ambassador")
    doc = json.loads(path.read_text())
    assert doc["id"] == receipt.request and doc["sentence"] == "do dream"
    assert "role" not in doc                      # the role is the directory, never a field
    # a query is not a command and is never spooled
    with pytest.raises(ValueError, match="not a command"):
        door.write_request(cfg, role="ambassador", plan=compile_sentence('near "x"'))
    # a command this build cannot land is refused before anything is written
    with pytest.raises(NotImplementedError, match="DO-3b"):
        door.write_request(cfg, role="cli", plan=compile_sentence('do research "q"', OPERATOR))
    assert len(_spooled(cfg, "cli")) == 0


def test_the_roles_grants_decide_what_the_door_admits() -> None:
    assert door.roles() == ("ambassador", "cli")          # a role nothing writes for is a hole
    assert door.grant_for("cli") is OPERATOR
    assert door.grant_for("ambassador") in (AMBASSADOR_OVERLAY, door.AMBASSADOR)
    for intruder in ("intruder", "heartbeat", "watcher", "mcp", "webui", "owner"):
        with pytest.raises(IllScopedSentence, match="knows no role"):
            door.grant_for(intruder)
    # the operator may say what the Ambassador may not: the commit-clock commands (DOR-1)
    compile_sentence("do sync code", OPERATOR)
    compile_sentence("do observe code", OPERATOR)
    with pytest.raises(IllScopedSentence):
        compile_sentence("do sync code", door.grant_for("ambassador"))


def test_the_kinds_are_the_queues_kinds(cfg: Any) -> None:
    def command(text: str) -> ast.Command:
        term = compile_sentence(text, OPERATOR).term
        assert isinstance(term, ast.Do)
        return term.command

    kinds = {text: door.kind_of(command(text))[0]
             for text in ("do sync vault", "do sync chat", "do sync code", "do sync dialogue",
                          "do dream", "do curate", 'do ingest note "a.md"',
                          'do ingest turn c 1 "t"', "do ingest doc docs/a.md",
                          "do ingest code", "do observe code",
                          "do relate", 'do link "a" "b" supports', 'do capture "t"')}
    assert kinds["do sync vault"] == "vault_sync" and kinds["do sync chat"] == "chat_sync"
    assert kinds["do sync code"] == "code_sync" and kinds["do ingest code"] == "code_sync"
    # an atom this build would ignore is refused by name, never landed as less than it said
    for text in ("do ingest transcript s", "do observe code abc1234", "do ingest code abc1234"):
        with pytest.raises(NotImplementedError, match="DO-3b"):
            door.kind_of(command(text))
    assert kinds["do dream"] == "dream" and kinds["do curate"] == "curate"
    assert {kinds[k] for k in ('do ingest note "a.md"', 'do ingest turn c 1 "t"',
                               "do ingest doc docs/a.md")} == {"ingest"}
    assert kinds["do observe code"] == "code_observe" and kinds["do relate"] == "relate"
    assert kinds['do link "a" "b" supports'] == "link" and kinds['do capture "t"'] == "capture"
    assert kinds["do sync dialogue"] == "dialogue_sync"
    router = Router(cfg)
    pinned = cfg.pinned_model.tier
    assert all(router.tier_for(k) == pinned
               for k in ("ingest", "capture", "link", "code_observe", "dialogue_sync"))
    assert router.tier_for("relate") == "synthesis"


# ── the drain ───────────────────────────────────────────────────────────────────────────────────


def test_the_drain_binds_the_role_to_the_spool_and_keeps_text_out_of_the_queue(cfg: Any) -> None:
    queue, router = _Queue(), Router(cfg)
    door.write_request(cfg, role="cli", plan=compile_sentence("do sync vault", OPERATOR))
    door.write_request(cfg, role="ambassador",
                       plan=compile_sentence('do capture "remember the milk" in tea',
                                             door.grant_for("ambassador")))
    assert drain_spool(queue, router, cfg) == 2
    by_kind = {j["kind"]: j for j in queue.jobs}
    assert by_kind["vault_sync"]["payload"] == {}             # the watcher's job, as today
    assert by_kind["vault_sync"]["priority"] == PRIORITY_BACKGROUND
    cap = by_kind["capture"]
    assert set(cap["payload"]) == {"role", "request", "digest"}
    assert cap["payload"]["role"] == "ambassador"
    assert "milk" not in json.dumps(cap["payload"])           # the text stays in the request
    assert cap["priority"] == PRIORITY_INTERACTIVE           # above background, below reactive
    assert _spooled(cfg, "ambassador") == [] and _spooled(cfg, "cli") == []
    staged = door.read_request(cfg, "ambassador", cap["payload"]["request"])   # the daemon's copy
    assert staged.sentence == 'do capture "remember the milk" in tea'
    receipt = door.read_receipt(cfg, "ambassador", cap["payload"]["request"])
    assert receipt is not None and receipt.state == "queued" and receipt.job == cap_job_id(queue)
    # a delegated kind keeps no copy: its job names no request
    assert sorted(p.name for p in (door.spool_root(cfg) / "cli" / "queued").iterdir()) == []
    assert drain_spool(queue, router, cfg) == 0               # nothing waits twice


def cap_job_id(queue: _Queue) -> int:
    return next(i + 1 for i, j in enumerate(queue.jobs) if j["kind"] == "capture")


def test_a_forged_request_is_bounded_by_its_spool(cfg: Any) -> None:
    """A request written into the Ambassador's spool naming a command the Ambassador may not
    say is refused by the spool's grant and never enqueued; its own text names no role."""
    queue, router = _Queue(), Router(cfg)
    spool = door.spool_root(cfg) / "ambassador"
    spool.mkdir(parents=True)
    rid = "f0f0f0f0f0f0f0f0"
    (spool / f"{rid}.json").write_text(json.dumps(
        {"id": rid, "sentence": "do sync code", "role": "cli", "at": "now"}))
    assert drain_spool(queue, router, cfg, report=lambda _m: None) == 0
    assert queue.jobs == [] and not (spool / f"{rid}.json").exists()
    receipt = door.read_receipt(cfg, "ambassador", rid)
    assert receipt is not None and receipt.state == "refused"
    assert "IllScopedSentence" in str(receipt.detail.get("reason"))
    # a spool the door does not know is left as it is: not drained, not touched
    (door.spool_root(cfg) / "intruder").mkdir()
    foreign = door.spool_root(cfg) / "intruder" / "0123456789abcdef.json"
    foreign.write_text(json.dumps({"id": "0123456789abcdef", "sentence": "do dream"}))
    assert drain_spool(queue, router, cfg) == 0 and queue.jobs == [] and foreign.exists()
    assert not (door.spool_root(cfg) / "intruder" / "receipts").exists()


def test_a_request_is_trusted_only_as_a_regular_file_named_by_its_id(cfg: Any) -> None:
    """A file whose id is not its name, that is not an object, that is over the cap, or that is
    not a regular file (a FIFO would hang a reader) is moved to `rejected/` and reported; none
    stops the drain, and nothing of a file's content ever names a path."""
    import os
    queue, router = _Queue(), Router(cfg)
    door.ensure_spools(cfg)
    spool = door.spool_root(cfg) / "ambassador"
    bad = {
        "a1a1a1a1a1a1a1a1.json": json.dumps({"id": "../../../dialogue/x", "sentence": "do dream"}),
        "b2b2b2b2b2b2b2b2.json": "null",
        "c3c3c3c3c3c3c3c3.json": json.dumps({"id": "c3c3c3c3c3c3c3c3", "sentence": 7}),
        "d4d4d4d4d4d4d4d4.json": json.dumps({"id": "d4d4d4d4d4d4d4d4",
                                             "sentence": "x" * (door.MAX_REQUEST_BYTES + 1)}),
    }
    for name, text in bad.items():
        (spool / name).write_text(text)
    os.mkfifo(spool / "e5e5e5e5e5e5e5e5.json")
    door.write_request(cfg, role="ambassador",
                       plan=compile_sentence("do dream", door.grant_for("ambassador")))
    said: list[str] = []
    assert drain_spool(queue, router, cfg, report=said.append) == 1
    assert [j["kind"] for j in queue.jobs] == ["dream"]
    rejected = sorted(p.name for p in (spool / "rejected").iterdir())
    assert rejected == sorted([*bad, "e5e5e5e5e5e5e5e5.json"])
    assert _spooled(cfg, "ambassador") == [] and len(said) == 5
    assert not (door.spool_root(cfg).parent / "dialogue").exists()   # where ../../../ led
    # the handler side: a queued id is checked before it names a path
    with pytest.raises(IllScopedSentence, match="not a request id"):
        door.read_request(cfg, "ambassador", "../../x")


def test_a_spool_writable_by_those_it_should_not_be_is_not_drained(cfg: Any) -> None:
    """The operator's spool is the daemon account's alone: group- or world-writable, it is
    reported once and not drained; the agents' spool may be group-writable, never
    world-writable."""
    import os
    import stat
    queue, router = _Queue(), Router(cfg)
    door.write_request(cfg, role="cli", plan=compile_sentence("do dream", OPERATOR))
    spool = door.spool_root(cfg) / "cli"
    mode = stat.S_IMODE(spool.stat().st_mode)
    for loose in (stat.S_IWGRP, stat.S_IWOTH):
        os.chmod(spool, mode | loose)
        said: list[str] = []
        assert drain_spool(queue, router, cfg, report=said.append) == 0
        assert len(_spooled(cfg, "cli")) == 1 and any("not drained" in m for m in said)
    os.chmod(spool, mode)
    assert drain_spool(queue, router, cfg) == 1
    amb = door.spool_root(cfg) / "ambassador"
    os.chmod(amb, stat.S_IMODE(amb.stat().st_mode) | stat.S_IWOTH)
    door.write_request(cfg, role="ambassador",
                       plan=compile_sentence("do dream", door.grant_for("ambassador")))
    said = []
    assert drain_spool(queue, router, cfg, report=said.append) == 0
    assert any("writable by others" in m for m in said)


def test_the_drain_is_bounded_a_tick_and_a_role(cfg: Any) -> None:
    queue, router = _Queue(), Router(cfg)
    for _ in range(3):
        door.write_request(cfg, role="ambassador",
                           plan=compile_sentence("do dream", door.grant_for("ambassador")))
    assert drain_spool(queue, router, cfg, max_per_tick=2) == 2
    assert len(_spooled(cfg, "ambassador")) == 1
    assert drain_spool(queue, router, cfg) == 1
    assert [j["payload"]["door"] for j in queue.jobs].count("ambassador") == 3   # counted by role


def test_a_full_lane_refuses_and_never_holds_the_other_lane(cfg: Any) -> None:
    """The quotas refuse, they do not hold: a role's bulk lane full of dreams refuses the next
    dream as busy (receipted, dropped), and its captures, the interactive lane, still land."""
    queue, router = _Queue(), Router(cfg)
    amb = door.grant_for("ambassador")
    quotas = {"interactive": 2, "bulk": 2}
    for _ in range(3):
        door.write_request(cfg, role="ambassador", plan=compile_sentence("do dream", amb))
    capture = door.write_request(cfg, role="ambassador",
                                 plan=compile_sentence('do capture "note this"', amb))
    assert drain_spool(queue, router, cfg, quotas=quotas) == 3     # two dreams and the capture
    kinds = [j["kind"] for j in queue.jobs]
    assert kinds.count("dream") == 2 and kinds.count("capture") == 1
    assert _spooled(cfg, "ambassador") == []                         # the third dream: refused
    busy = [door.read_receipt(cfg, "ambassador", p.stem)
            for p in (door.spool_root(cfg) / "ambassador" / "receipts").iterdir()]
    assert sum(1 for r in busy if r is not None and r.state == "refused"
               and "busy" in str(r.detail.get("reason"))) == 1
    receipt = door.read_receipt(cfg, "ambassador", capture.request)
    assert receipt is not None and receipt.state == "queued"


def test_a_surface_refuses_to_deepen_a_full_spool(cfg: Any, monkeypatch: Any) -> None:
    monkeypatch.setattr(door, "MAX_SPOOLED", 2)
    amb = door.grant_for("ambassador")
    for _ in range(2):
        door.write_request(cfg, role="ambassador", plan=compile_sentence("do dream", amb))
    with pytest.raises(door.Busy):
        door.write_request(cfg, role="ambassador", plan=compile_sentence("do dream", amb))
    assert len(_spooled(cfg, "ambassador")) == 2


def test_a_queued_request_is_never_overwritten(cfg: Any) -> None:
    queue, router = _Queue(), Router(cfg)
    receipt = door.write_request(cfg, role="cli", plan=compile_sentence("do dream", OPERATOR))
    assert drain_spool(queue, router, cfg) == 1
    replay = door.spool_root(cfg) / "cli" / f"{receipt.request}.json"
    replay.write_text(json.dumps({"id": receipt.request, "sentence": "do dream"}))
    said: list[str] = []
    assert drain_spool(queue, router, cfg, report=said.append) == 0
    assert not replay.exists() and (replay.parent / "rejected" / replay.name).exists()
    assert len(queue.jobs) == 1 and any("never reused" in m for m in said)
    again = door.read_receipt(cfg, "cli", receipt.request)
    assert again is not None and again.state == "queued"     # the first request's, untouched


class _Crash(BaseException):
    """The process dies: no handler of the drain's runs."""


def test_a_request_lands_once_however_many_jobs_name_it(cfg: Any, monkeypatch: Any) -> None:
    """A crash between the enqueue and the receipt leaves the request in the spool and its job in
    the queue; the next tick enqueues it again. The landing is idempotent at the request: the
    second job finds it receipted as landed and lands nothing."""
    queue, router = _Queue(), Router(cfg)
    door.write_request(cfg, role="ambassador",
                       plan=compile_sentence('do capture "once"', door.grant_for("ambassador")))
    write_receipt = door.write_receipt

    def crash(*_a: Any, **_k: Any) -> Any:
        raise _Crash

    monkeypatch.setattr(door, "write_receipt", crash)
    with pytest.raises(_Crash):
        drain_spool(queue, router, cfg)             # enqueued, then the process dies
    monkeypatch.setattr(door, "write_receipt", write_receipt)
    drain_spool(queue, router, cfg)                 # the next tick enqueues it again
    payloads = [j["payload"] for j in queue.jobs if j["kind"] == "capture"]
    assert len(payloads) == 2 and payloads[0]["request"] == payloads[1]["request"]
    capture = _Capture()
    handle = door_handler(cfg, landers=door.Landers(capture=capture))
    handle(_job(payloads[0]))
    summary = handle(_job(payloads[1]))
    assert "landed already" in str(summary) and len(capture.turns) == 1


# ── the handler ─────────────────────────────────────────────────────────────────────────────────


class _Store:
    def producers_of(self, hashes: set[str]) -> set[str]:
        return {f"att-for-{h}" for h in hashes}

    def get(self, att_id: str) -> Any:
        return type("A", (), {"action": "capture"})()


class _Attestor:
    store = _Store()


class _Capture:
    attestor = _Attestor()

    def __init__(self) -> None:
        self.turns: list[tuple[str, str, str, str]] = []

    def capture_turn(self, text: str, *, conversation: str, turn_id: str, role: str,
                     at: str | None = None) -> tuple[str, bool]:
        self.turns.append((text, conversation, turn_id, role))
        return ("d" + turn_id, True)


class _Edge:
    def __init__(self, u: str, v: str, rel_type: str, provenance: str) -> None:
        self.u, self.v, self.rel_type, self.provenance = u, v, rel_type, provenance


class _Edges:
    def __init__(self, held: list[_Edge]) -> None:
        self.held = held
        self.added: list[tuple[str, str, dict[str, Any]]] = []

    def all(self) -> list[_Edge]:
        return list(self.held)

    def add(self, u: str, v: str, **kw: Any) -> None:
        self.added.append((u, v, kw))


def _job(payload: dict[str, Any], kind: str = "capture") -> Job:
    return Job(id=7, kind=kind, tier="pinned", num_ctx=1, priority=0, state="running",
               payload=payload, result=None, error=None, attempts=1, checkpoint=None,
               created_at="", started_at=None, finished_at=None)


def _drained(queue: _Queue, kind: str = "capture") -> dict[str, Any]:
    return next(j["payload"] for j in queue.jobs if j["kind"] == kind)


def test_the_handler_compiles_again_lands_observed_and_writes_the_receipt(cfg: Any) -> None:
    queue, router = _Queue(), Router(cfg)
    door.write_request(cfg, role="ambassador",
                       plan=compile_sentence('do capture "a thought" in tea',
                                             door.grant_for("ambassador")))
    drain_spool(queue, router, cfg)
    payload = _drained(queue)
    rid = payload["request"]
    capture = _Capture()
    handle = door_handler(cfg, landers=door.Landers(capture=capture))
    summary = handle(_job(payload))
    assert summary is not None and "landed" in summary
    (text, conversation, turn, role) = capture.turns[0]
    assert text == "a thought" and conversation == "door/ambassador/tea" and role == "assistant"
    receipt = door.read_receipt(cfg, "ambassador", rid)
    assert receipt is not None and receipt.state == "landed" and receipt.job == 7
    assert receipt.detail["provenance"] == "observed" and receipt.detail["created"] is True
    assert receipt.detail["ref"] == f"dialogue/door/ambassador/tea/{turn}"
    assert receipt.detail["attestations"] == [f"att-for-d{turn}"]   # what witness reads back
    assert "sentence" not in receipt.to_dict()
    assert not (door.spool_root(cfg) / "ambassador" / "queued" / f"{rid}.json").exists()


def test_the_handler_lands_only_the_request_that_was_drained(cfg: Any) -> None:
    """The job's payload carries the sentence's digest and the kind the drain compiled; a queued
    file rewritten after the drain, or a job whose kind is not the sentence's, lands nothing."""
    queue, router = _Queue(), Router(cfg)
    door.write_request(cfg, role="ambassador",
                       plan=compile_sentence('do capture "a thought"',
                                             door.grant_for("ambassador")))
    drain_spool(queue, router, cfg)
    payload = _drained(queue)
    queued = door.spool_root(cfg) / "ambassador" / "queued" / f"{payload['request']}.json"
    queued.write_text(json.dumps({"id": payload["request"], "sentence": "do relate pairs 50"}))
    capture = _Capture()
    handle = door_handler(cfg, landers=door.Landers(capture=capture, relate=lambda n: "ran"))
    with pytest.raises(IllScopedSentence, match="not the sentence that was drained"):
        handle(_job(payload))
    receipt = door.read_receipt(cfg, "ambassador", payload["request"])
    assert receipt is not None and receipt.state == "refused" and capture.turns == []
    assert "refused already" in str(handle(_job(payload)))   # a refused request stays refused
    # the digest right, the kind wrong: a capture job never runs a relate pass
    door.write_request(cfg, role="ambassador",
                       plan=compile_sentence('do capture "another"',
                                             door.grant_for("ambassador")))
    drain_spool(queue, router, cfg)
    second = [j["payload"] for j in queue.jobs if j["kind"] == "capture"][-1]
    queued = door.spool_root(cfg) / "ambassador" / "queued" / f"{second['request']}.json"
    queued.write_text(json.dumps({"id": second["request"], "sentence": "do relate pairs 50"}))
    forged = {**second, "digest": door.sentence_digest("do relate pairs 50")}
    with pytest.raises(IllScopedSentence, match="compiles to relate"):
        handle(_job(forged, kind="capture"))


def test_the_handler_refuses_what_the_spools_grant_refuses_before_landing(cfg: Any) -> None:
    """The second check: a queued request whose role may not say its sentence (here, one written
    straight into `queued/`) lands nothing and is receipted as refused."""
    door.ensure_spools(cfg)
    queued = door.spool_root(cfg) / "ambassador" / "queued"
    rid = "1a7e1a7e1a7e1a7e"
    (queued / f"{rid}.json").write_text(json.dumps({"id": rid, "sentence": "do observe code"}))
    capture = _Capture()
    handle = door_handler(cfg, landers=door.Landers(capture=capture))
    with pytest.raises(IllScopedSentence):
        handle(_job({"role": "ambassador", "request": rid,
                     "digest": door.sentence_digest("do observe code")}, kind="code_observe"))
    assert capture.turns == []
    receipt = door.read_receipt(cfg, "ambassador", rid)
    assert receipt is not None and receipt.state == "refused"
    assert not (queued / f"{rid}.json").exists()           # a refused request is spent


def test_link_lands_interpreted_and_never_overwrites_an_authored_edge(cfg: Any,
                                                                      monkeypatch: Any) -> None:
    import core.ingest.door as module

    class _Engine:
        def __init__(self, _cfg: Any = None) -> None:
            pass

        def note_graph(self) -> tuple[list[dict[str, Any]], Any, Any]:
            return ([{"source_path": "a.md", "title": "A", "digest": "da"},
                     {"source_path": "b.md", "title": "B", "digest": "db"}], None, None)

        def index_of(self, notes: list[dict[str, Any]], atom: str) -> int:
            return next(i for i, n in enumerate(notes) if atom in (n["source_path"], n["title"]))

    monkeypatch.setattr("core.query.QueryEngine", _Engine)
    edges = _Edges([_Edge("da", "db", "contradicts", "authored-solo")])
    out = module.perform(Link("a.md", "b.md", "supports"), cfg, door.Landers(edges=edges))
    assert out["provenance"] == "interpreted" and edges.added[0][2]["provenance"] == "interpreted"
    with pytest.raises(IllScopedSentence, match="never overwrites"):
        module.perform(Link("a.md", "b.md", "contradicts"), cfg, door.Landers(edges=edges))
    assert len(edges.added) == 1


def test_a_capture_sentence_is_observed_by_construction(cfg: Any) -> None:
    capture = _Capture()
    out = door.perform(Capture("x", None), cfg, door.Landers(capture=capture), role="ambassador")
    assert capture.turns[0][1] == "door/ambassador/captures" and capture.turns[0][3] == "assistant"
    assert out["provenance"] == "observed"


def test_the_doors_turns_live_under_their_role_and_name_no_path(cfg: Any) -> None:
    """The owner's turns are `dialogue/<source>/<chat>/<id>`; a command's turn is
    `dialogue/door/<role>/<conversation>/<turn>`, and a conversation or turn with a path in it
    is refused, so no role can name another's identity, least of all the owner's."""
    from core.sentence.ast import Ingest, Source, SourceKind
    capture = _Capture()
    L = door.Landers(capture=capture)
    out = door.perform(Ingest(Source(SourceKind.TURN, atom="c", turn="7", text="x")), cfg, L,
                       role="ambassador")
    assert out["ref"] == "dialogue/door/ambassador/c/7"
    for conv, turn in (("openwebui/abc", "7"), ("..", "7"), ("c", "../m1"), ("", "7")):
        with pytest.raises(IllScopedSentence, match="never a path|a name is"):
            door.perform(Ingest(Source(SourceKind.TURN, atom=conv, turn=turn, text="x")), cfg,
                         L, role="ambassador")
    with pytest.raises(IllScopedSentence):
        door.perform(Capture("x", "../../x"), cfg, L, role="ambassador")
    assert len(capture.turns) == 1


def test_ingest_doc_is_allow_listed_on_every_call(cfg: Any) -> None:
    from core.sentence.ast import Ingest, Source, SourceKind
    seen: list[list[Path]] = []

    def curated(paths: list[Path]) -> str:
        seen.append(paths)
        return "ok"

    L = door.Landers(curated=curated)
    door.perform(Ingest(Source(SourceKind.DOC, atom="docs/LAWS.md")), cfg, L)
    assert len(seen) == 1 and seen[0][0].name == "LAWS.md"
    for atom in ("data/query_log.jsonl", "config/defaults.toml", "pyproject.toml", "../etc"):
        with pytest.raises(IllScopedSentence):
            door.perform(Ingest(Source(SourceKind.DOC, atom=atom)), cfg, L)
    assert len(seen) == 1                                   # the lander ran once


def test_ingest_note_is_bound_by_the_vaults_scope(cfg: Any, tmp_path: Path) -> None:
    from core.sentence.ast import Ingest, Source, SourceKind
    vault = tmp_path / "vault"
    (vault / "pages").mkdir(parents=True)
    (vault / ".recycle").mkdir()
    (vault / "pages" / "a.md").write_text("- a\n")
    (vault / ".recycle" / "gone.md").write_text("- gone\n")
    (vault / "pages" / "scan.pdf").write_bytes(b"%PDF")
    (tmp_path / "link").symlink_to(vault, target_is_directory=True)
    # the vault configured through a symlink: a note is named as the rescan names it
    scoped = replace(cfg, ingestion=replace(cfg.ingestion, vault=replace(cfg.ingestion.vault,
                                                                         path=tmp_path / "link")))
    from core.ingest.sync import VaultSync
    from core.kernel.stores.rawstore import RawStore
    from core.stores.catalog import VaultCatalog
    from core.stores.vectorstore import VectorStore
    from tests.fixtures.embedding import DIM, FakeEmbedder

    real = VaultSync(vault=tmp_path / "link", raw=RawStore(tmp_path / "raw"),
                     store=VectorStore(tmp_path / "vec", dim=DIM),
                     catalog=VaultCatalog(tmp_path / "cat.sqlite"),
                     embedder=FakeEmbedder())  # type: ignore[arg-type]

    class _Sync:
        attestor = None

        def __init__(self) -> None:
            self.synced: list[Path] = []
            self.catalog = type("C", (), {"get": staticmethod(lambda _p: None)})()

        def in_scope(self, path: Path) -> bool:
            return real.in_scope(path)          # the real pattern and the excluded directories

        def sync_one(self, path: Path) -> str:
            self.synced.append(path)
            return "indexed"

    sync = _Sync()
    L = door.Landers(vault_sync=sync)
    out = door.perform(Ingest(Source(SourceKind.NOTE, atom="pages/a.md")), scoped, L)
    assert out["outcome"] == "indexed" and sync.synced == [tmp_path / "link" / "pages" / "a.md"]
    for atom in (".recycle/gone.md", "pages/scan.pdf", "pages/missing.md", "../outside.md"):
        with pytest.raises(IllScopedSentence):
            door.perform(Ingest(Source(SourceKind.NOTE, atom=atom)), scoped, L)
    assert len(sync.synced) == 1


def test_relate_pairs_is_capped(cfg: Any) -> None:
    from core.sentence.ast import RelatePass
    ran: list[int | None] = []

    def relate(n: int | None) -> str:
        ran.append(n)
        return "ok"

    L = door.Landers(relate=relate)
    door.perform(RelatePass(pairs=door.RELATE_PAIRS_MAX), cfg, L)
    with pytest.raises(IllScopedSentence, match="at most"):
        door.perform(RelatePass(pairs=door.RELATE_PAIRS_MAX + 1), cfg, L)
    assert ran == [door.RELATE_PAIRS_MAX]


# ── the surface ─────────────────────────────────────────────────────────────────────────────────


def test_ask_logged_writes_the_request_and_returns_the_receipt(cfg: Any, tmp_path: Path) -> None:
    from core.sentence.surface import QueryLog, ask_logged

    class _E:
        config = cfg

    log = QueryLog(tmp_path / "log.jsonl")
    answer = ask_logged("do dream", door.grant_for("ambassador"), surface="mcp",
                        role="ambassador", engine=_E(), log=log, trace=True)   # type: ignore[arg-type]
    (hit,) = answer.hits
    assert hit.ref.startswith("door:") and hit.stratum == "door" and hit.title == "dream"
    assert hit.detail["state"] == "spooled" and hit.detail["role"] == "ambassador"
    assert len(_spooled(cfg, "ambassador")) == 1
    assert answer.trace is not None and any(s.stage == "act" for s in answer.trace.steps)
    assert log.entries()[-1].outcome == "requested"
    # a captured text never enters the query log: a literal is logged as its length
    ask_logged('do capture "remember the milk"', door.grant_for("ambassador"), surface="mcp",
               role="ambassador", engine=_E(), log=log)   # type: ignore[arg-type]
    assert log.entries()[-1].sentence == 'do capture "<17>"'
    assert "milk" not in (tmp_path / "log.jsonl").read_text()
    # `--as` labels the asker; the CLI speaks to the door as `cli`, whatever the label
    import io

    from core.sentence.surface import run_query
    out = io.StringIO()
    assert run_query(["--as", "owner", "--json", "do dream"], out=out, engine=_E(),   # type: ignore[arg-type]
                     log=log) == 0
    assert len(_spooled(cfg, "cli")) == 1 and not (door.spool_root(cfg) / "owner").exists()
    assert log.entries()[-1].role == "owner"
    # the Ambassador may not say a commit-clock command, at the door as everywhere
    with pytest.raises(IllScopedSentence):
        ask_logged("do sync code", door.grant_for("ambassador"), surface="mcp",
                   role="ambassador", engine=_E(), log=log)   # type: ignore[arg-type]
    assert log.entries()[-1].outcome == "refused"


def test_the_surface_refuses_at_once_what_the_landing_would(cfg: Any) -> None:
    """A name with a path in it, or a relation pass over the cap, is refused when spoken, so the
    speaker hears it in the answer instead of in a receipt; nothing is spooled."""
    amb = door.grant_for("ambassador")
    with pytest.raises(IllScopedSentence, match="never a path"):
        door.write_request(cfg, role="ambassador",
                           plan=compile_sentence('do capture "x" in "openwebui/abc"', amb))
    with pytest.raises(IllScopedSentence, match="at most"):
        door.write_request(cfg, role="ambassador",
                           plan=compile_sentence("do relate pairs 99999999", amb))
    assert _spooled(cfg, "ambassador") == []


def test_the_daemon_makes_the_spools_with_their_modes(cfg: Any, monkeypatch: Any) -> None:
    """The root: the daemon adds every entry (`755`). The operator's spool: the owner's account
    alone (`700`). The agents' spool: under a dedicated group, the group writes and the sticky bit
    guards (`3770`, the setgid bit the platform's to grant), and only their receipts are the
    group's to read; `queued/` and `rejected/` are the daemon's alone."""
    import stat
    monkeypatch.setattr(door, "_EVERYONE_GROUPS", frozenset())   # the tmp dir's group: dedicated
    assert door.ensure_spools(cfg) == ["ambassador", "cli"]
    root = door.spool_root(cfg)
    assert stat.S_IMODE(root.stat().st_mode) == 0o755
    assert stat.S_IMODE((root / "cli").stat().st_mode) == 0o700
    assert stat.S_IMODE((root / "ambassador").stat().st_mode) & 0o1777 == 0o1770
    for sub in ("queued", "receipts", "rejected"):
        assert stat.S_IMODE((root / "cli" / sub).stat().st_mode) == 0o700
        mode = stat.S_IMODE((root / "ambassador" / sub).stat().st_mode) & 0o777
        assert mode == (0o750 if sub == "receipts" else 0o700), sub


def test_under_a_group_every_account_is_in_the_agents_spool_is_the_owners(
        cfg: Any, monkeypatch: Any) -> None:
    """A spool group-writable for `staff` would let any local account speak as the Ambassador: the
    daemon makes it the owner's alone instead, and refuses one someone made group-writable."""
    import os
    import stat
    root = door.spool_root(cfg)
    root.parent.mkdir(parents=True)
    group = door._group_name(os.stat(root.parent).st_gid)
    monkeypatch.setattr(door, "_EVERYONE_GROUPS", frozenset({group}))
    assert door.ensure_spools(cfg) == ["ambassador", "cli"]
    amb = root / "ambassador"
    assert stat.S_IMODE(amb.stat().st_mode) & 0o777 == 0o700
    os.chmod(amb, 0o3770)
    said: list[str] = []
    assert door.ensure_spools(cfg, report=said.append) == ["cli"]
    assert any("holds every local account" in m for m in said)


def test_a_symlinked_spool_is_never_followed(cfg: Any, tmp_path: Path) -> None:
    """A symlink in a spool's place, or in the root's, is not a directory the daemon drains: the
    role (or every role) is reported and left, and the other roles are served."""
    root = door.spool_root(cfg)
    root.parent.mkdir(parents=True)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    root.mkdir(mode=0o755)
    (root / "cli").symlink_to(elsewhere, target_is_directory=True)
    rid = "0123456789abcdef"
    (elsewhere / f"{rid}.json").write_text(json.dumps({"id": rid, "sentence": "do sync code"}))
    door.write_request(cfg, role="ambassador",
                       plan=compile_sentence("do dream", door.grant_for("ambassador")))
    said: list[str] = []
    queue, router = _Queue(), Router(cfg)
    assert drain_spool(queue, router, cfg, report=said.append) == 1
    assert [j["kind"] for j in queue.jobs] == ["dream"]                 # the other role served
    assert (elsewhere / f"{rid}.json").exists() and not (elsewhere / "queued").exists()
    assert any("cli spool is not drained" in m for m in said)
    # the root itself a symlink: nothing is drained
    cfg2 = replace(cfg, interface=replace(cfg.interface, handoff_dir=tmp_path / "h2"))
    (tmp_path / "h2").mkdir()
    (tmp_path / "h2" / "door").symlink_to(root, target_is_directory=True)
    said = []
    assert drain_spool(_Queue(), router, cfg2, report=said.append) == 0
    assert any("nothing is drained" in m for m in said)


def test_a_door_sync_coalesces_with_a_waiting_row_and_never_with_a_running_one(cfg: Any) -> None:
    """The note's §6 falsifier, on the real queue: a `do sync vault` drained while the watcher's
    `vault_sync` waits is that row (the watcher's job, as today); drained while one runs, it is a
    second row, so a follow-up pass is never swallowed by the pass already reading the state."""
    from scheduler.queue import QUEUED, RUNNING, JobQueue
    queue, router = JobQueue(Path(":memory:")), Router(cfg)
    plan = router.plan("vault_sync")
    waiting = queue.enqueue(plan.kind, plan.tier, plan.num_ctx, priority=plan.priority)
    door.write_request(cfg, role="cli", plan=compile_sentence("do sync vault", OPERATOR))
    assert drain_spool(queue, router, cfg) == 1
    assert [j.id for j in queue.list(QUEUED)] == [waiting.id]          # coalesced
    running = queue.claim()
    assert running is not None and running.id == waiting.id
    door.write_request(cfg, role="cli", plan=compile_sentence("do sync vault", OPERATOR))
    assert drain_spool(queue, router, cfg) == 1
    (follow_up,) = queue.list(QUEUED)
    assert follow_up.id != waiting.id and follow_up.kind == "vault_sync"
    assert [j.id for j in queue.list(RUNNING)] == [waiting.id]
    # `do sync dialogue` is the queue's own coalescing kind now, like the other syncs
    for _ in range(2):
        door.write_request(cfg, role="cli", plan=compile_sentence("do sync dialogue", OPERATOR))
    assert drain_spool(queue, router, cfg) == 2
    assert [j.kind for j in queue.list(QUEUED)].count("dialogue_sync") == 1


# ── the second review's falsifiers ──────────────────────────────────────────────────────────────


def test_the_operators_spool_takes_only_the_daemon_accounts_requests(cfg: Any,
                                                                     monkeypatch: Any) -> None:
    """A request in the operator's spool written by another account is rejected; the agents'
    spool is the group's to write, so there the same file is read."""
    import os
    door.ensure_spools(cfg)
    rid = "abcdefabcdefabcd"
    said: list[str] = []
    for role in ("cli", "ambassador"):
        f = door.spool_root(cfg) / role / f"{rid}.json"
        f.write_text(json.dumps({"id": rid, "sentence": "do dream"}))
        real = os.getuid()
        monkeypatch.setattr(door.os, "getuid", lambda real=real: real + 1)
        got = door._load_request(f, role, said.append)
        monkeypatch.undo()
        assert (got is None) == (role == "cli")
    assert any("the cli spool is the daemon account's alone" in m for m in said)


def test_a_hard_linked_or_symlinked_request_is_rejected(cfg: Any) -> None:
    """A writer that keeps a second name for its request could change it after the daemon's check;
    a symlink at a request's name could point at a pipe. Both are rejected, and nothing blocks."""
    import os
    door.ensure_spools(cfg)
    spool = door.spool_root(cfg) / "ambassador"
    rid = "1111222233334444"
    (spool / f"{rid}.json").write_text(json.dumps({"id": rid, "sentence": "do dream"}))
    os.link(spool / f"{rid}.json", spool.parent / "kept")
    pipe = spool.parent / "pipe"
    os.mkfifo(pipe)
    (spool / "5555666677778888.json").symlink_to(pipe)
    said: list[str] = []
    assert drain_spool(_Queue(), Router(cfg), cfg, report=said.append) == 0
    rejected = sorted(p.name for p in (spool / "rejected").iterdir())
    assert rejected == [f"{rid}.json", "5555666677778888.json"]
    assert any("2 links" in m for m in said)


def test_a_failed_request_may_be_spooled_again_and_a_seen_one_may_not(cfg: Any) -> None:
    queue, router = _Queue(), Router(cfg)
    amb = door.grant_for("ambassador")
    receipt = door.write_request(cfg, role="ambassador",
                                 plan=compile_sentence('do capture "again"', amb))
    assert drain_spool(queue, router, cfg) == 1
    staged = door.spool_root(cfg) / "ambassador" / "queued" / f"{receipt.request}.json"
    # the landing fails: the receipt says so and the daemon's copy stays
    door.write_receipt(cfg, door.Receipt(receipt.request, "ambassador", "capture", "failed"))
    staged.replace(door.spool_root(cfg) / "ambassador" / staged.name)   # the operator re-spools
    assert drain_spool(queue, router, cfg) == 1
    again = door.read_receipt(cfg, "ambassador", receipt.request)
    assert again is not None and again.state == "queued" and again.job == 2


def test_an_orphaned_door_job_goes_back_to_the_queue(tmp_path: Path) -> None:
    """A crash mid-landing leaves a door job RUNNING; the next start's sweep puts it back in the
    queue (it is re-runnable at the request), where a dream it left is failed as before."""
    from scheduler.queue import _IDEMPOTENT_KINDS, _REQUEUE_KINDS, FAILED, QUEUED, JobQueue
    assert _REQUEUE_KINDS - _IDEMPOTENT_KINDS == door.DOOR_KINDS
    queue = JobQueue(tmp_path / "q.sqlite")
    cap = queue.enqueue("capture", "pinned", 1, payload={"role": "ambassador",
                                                         "request": "0" * 16, "digest": "d"})
    dream = queue.enqueue("dream", "synthesis", 1)
    for _ in range(2):
        assert queue.claim() is not None
    sweep = queue.sweep_orphans(active_run_id=99)
    assert sweep.requeued == (cap.id,) and sweep.failed == (dream.id,)
    assert queue.get(cap.id).state == QUEUED and queue.get(dream.id).state == FAILED


def test_a_request_that_fails_to_enqueue_is_set_aside_and_the_next_is_served(cfg: Any) -> None:
    class _Broken(_Queue):
        def enqueue(self, kind: str, tier: str, num_ctx: int, *, priority: int = 0,
                    payload: dict[str, Any] | None = None) -> Job:
            if kind == "dream":
                raise RuntimeError("database is locked")
            return super().enqueue(kind, tier, num_ctx, priority=priority, payload=payload)

    queue, router = _Broken(), Router(cfg)
    first = door.write_request(cfg, role="cli", plan=compile_sentence("do dream", OPERATOR))
    door.write_request(cfg, role="cli", plan=compile_sentence("do sync vault", OPERATOR))
    said: list[str] = []
    assert drain_spool(queue, router, cfg, report=said.append) == 1
    assert [j["kind"] for j in queue.jobs] == ["vault_sync"]
    failed = door.read_receipt(cfg, "cli", first.request)
    assert failed is not None and failed.state == "failed" and "locked" in str(failed.detail)
    assert (door.spool_root(cfg) / "cli" / "rejected" / f"{first.request}.json").exists()


def test_the_serve_loop_survives_a_drain_that_raises(capsys: Any) -> None:
    from ops.lifecycle.launcher import drain_guarded

    def broken() -> int:
        raise OSError("disk full")

    assert drain_guarded(broken) == 0 and drain_guarded(lambda: 3) == 3
    assert "the drain failed this tick (OSError: disk full)" in capsys.readouterr().out


def test_a_failed_dialogue_sync_fails_its_job() -> None:
    from scheduler.door import dialogue_sync_handler
    assert dialogue_sync_handler(lambda: 0)(_job({}, kind="dialogue_sync")) == "dialogue sync: done"
    with pytest.raises(RuntimeError, match="exit 1"):
        dialogue_sync_handler(lambda: 1)(_job({}, kind="dialogue_sync"))


def test_prune_keeps_a_week_and_never_a_copy_whose_job_may_run(cfg: Any) -> None:
    import os
    import time as _time
    door.ensure_spools(cfg)
    base = door.spool_root(cfg) / "ambassador"
    old, new = "aaaaaaaaaaaaaaaa", "bbbbbbbbbbbbbbbb"
    door.write_receipt(cfg, door.Receipt(old, "ambassador", "capture", "failed"))
    door.write_receipt(cfg, door.Receipt(new, "ambassador", "capture", "queued"))
    for rid in (old, new):
        door.stage(cfg, door.Request(rid, "ambassador", 'do capture "x"', ""))
    (base / "rejected" / "junk.json").write_text("{}")
    week_ago = _time.time() - door.PRUNE_AFTER_S - 60
    for f in [*(base / "receipts").iterdir(), *(base / "queued").iterdir(),
              *(base / "rejected").iterdir()]:
        os.utime(f, (week_ago, week_ago))
    # the failed request's copy, both receipts and the rejected file; the copy whose receipt said
    # `queued` is kept, since its job may still run
    assert door.prune(cfg) == 4
    assert (base / "queued" / f"{new}.json").exists()
    assert not (base / "queued" / f"{old}.json").exists()



# ── the third review's falsifiers ───────────────────────────────────────────────────────────────


def test_a_text_that_escapes_past_the_cap_is_refused_at_the_surface(cfg: Any) -> None:
    """A command under the sentence cap can still write a file over the daemon's cap, since
    escaping grows a text (a quote takes two bytes, a control character six): the surface refuses
    what the daemon would reject, so nothing is spooled that can never land."""
    from core.sentence import quote
    amb = door.grant_for("ambassador")
    text = "\x01" * 11_000
    with pytest.raises(ValueError, match="as written"):
        door.write_request(cfg, role="ambassador",
                           plan=compile_sentence(f"do capture {quote(text)}", amb))
    assert _spooled(cfg, "ambassador") == []


def test_a_rejected_request_is_receipted_once_and_never_over_a_seen_one(cfg: Any) -> None:
    door.ensure_spools(cfg)
    spool = door.spool_root(cfg) / "ambassador"
    rid = "9999aaaa9999aaaa"
    (spool / f"{rid}.json").write_text("null")
    drain_spool(_Queue(), Router(cfg), cfg, report=lambda _m: None)
    receipt = door.read_receipt(cfg, "ambassador", rid)
    assert receipt is not None and receipt.state == "refused"
    assert "not an object" in str(receipt.detail["reason"])
    # a second file of the same name lands beside the first in rejected/, and the receipt stays
    (spool / f"{rid}.json").write_text("[]")
    drain_spool(_Queue(), Router(cfg), cfg, report=lambda _m: None)
    names = sorted(p.name for p in (spool / "rejected").iterdir())
    assert names == [f"{rid}.json", f"{rid}.json.1"]


def test_a_directory_posing_as_a_request_never_stops_the_drain_or_the_prune(cfg: Any) -> None:
    import os
    import time as _time
    door.ensure_spools(cfg)
    spool = door.spool_root(cfg) / "ambassador"
    (spool / "abababababababab.json").mkdir()
    door.write_request(cfg, role="ambassador",
                       plan=compile_sentence("do dream", door.grant_for("ambassador")))
    said: list[str] = []
    assert drain_spool(_Queue(), Router(cfg), cfg, report=said.append) == 1
    moved = spool / "rejected" / "abababababababab.json"
    assert moved.is_dir()
    week_ago = _time.time() - door.PRUNE_AFTER_S - 60
    os.utime(moved, (week_ago, week_ago))
    assert door.prune(cfg) >= 0 and moved.is_dir()          # skipped, and nothing raised


def test_a_door_job_that_kills_the_process_is_failed_on_the_third_start(tmp_path: Path) -> None:
    from scheduler.queue import FAILED, QUEUED, JobQueue
    queue = JobQueue(tmp_path / "q.sqlite")
    job = queue.enqueue("capture", "pinned", 1, payload={"role": "ambassador",
                                                         "request": "0" * 16, "digest": "d"})
    for run in (11, 12):
        assert queue.claim() is not None
        assert queue.sweep_orphans(active_run_id=run).requeued == (job.id,)
        assert queue.get(job.id).state == QUEUED
    assert queue.claim() is not None
    assert queue.sweep_orphans(active_run_id=13).failed == (job.id,)
    assert queue.get(job.id).state == FAILED


def test_the_edge_readers_find_podman_where_homebrew_keeps_it(monkeypatch: Any) -> None:
    from ops.lifecycle.launcher import _edge_env
    monkeypatch.setenv("PATH", "/usr/bin:/bin")
    path = _edge_env()["PATH"].split(":")
    assert path[:2] == ["/usr/bin", "/bin"] and "/opt/homebrew/bin" in path


def test_only_the_daemons_account_makes_the_spools(cfg: Any, monkeypatch: Any) -> None:
    """A surface running as another account (the agents', under the split) never makes the
    spools: the daemon does, so no other account owns `door/` and can rename what lies in it."""
    import os
    real = os.getuid()
    door.spool_root(cfg).parent.mkdir(parents=True)
    monkeypatch.setattr(door.os, "getuid", lambda: real + 1)
    with pytest.raises(PermissionError, match="the daemon's to make"):
        door.write_request(cfg, role="ambassador",
                           plan=compile_sentence("do dream", door.grant_for("ambassador")))
    assert not door.spool_root(cfg).exists()


def test_relate_pairs_zero_judges_none(cfg: Any, monkeypatch: Any) -> None:
    import core.relations as relations
    from core.sentence.ast import RelatePass
    asked: list[int] = []

    def detector(_cfg: Any, *, max_pairs: int) -> Any:
        asked.append(max_pairs)
        return type("D", (), {"run": staticmethod(lambda: "ran")})()

    monkeypatch.setattr(relations, "build_relation_detector", detector)
    door.perform(RelatePass(pairs=0), cfg, door.Landers())
    door.perform(RelatePass(pairs=None), cfg, door.Landers())
    assert asked == [0, 24]


def test_a_receipt_names_only_its_own_actions_attestations() -> None:
    class _Att:
        def __init__(self, action: str) -> None:
            self.action = action

    class _Ledger:
        held = {"a1": _Att("capture"), "a2": _Att("ingest_note")}

        def producers_of(self, hashes: set[str]) -> set[str]:
            return set(self.held)

        def get(self, att_id: str) -> Any:
            return self.held.get(att_id)

    attestor = type("A", (), {"store": _Ledger()})()
    assert door._attestations_of(attestor, "d", "capture") == ["a1"]
    assert door._attestations_of(attestor, "d", "ingest_note") == ["a2"]
