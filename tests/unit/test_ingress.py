"""The ingress (`core/ingest/ingress.py`, `scheduler/ingress.py`; dn-ingress D3, D5, D7;
dn-ingress-language §E6, §E7): a request is spooled under its role, the daemon drains the spool with
the role bound to the directory, the handler compiles it again, evaluates its script and lands the
plan through the writer, text never enters the queue, and a request a role may not say is refused
before anything lands. Hermetic: a temporary palace (`tests/fixtures/ingress.py`) and fakes."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from core.ingest import ingress
from core.query import AMBASSADOR_OVERLAY, OPERATOR
from core.sentence import IllScopedSentence, ParseError, ast, compile_sentence
from core.sentence.interpret import ScriptError
from core.sentence.plan import Plan
from scheduler.ingress import drain_spool, ingress_handler, library_handler
from scheduler.queue import PRIORITY_BACKGROUND, PRIORITY_INTERACTIVE, Job
from scheduler.router import Router
from tests.fixtures.ingress import Palace, palace_at, palace_config


@pytest.fixture
def cfg(tmp_path: Path) -> Any:
    return palace_config(tmp_path / "p")


@pytest.fixture
def palace(tmp_path: Path) -> Palace:
    return palace_at(tmp_path)


def _plan(text: str, role: str = "ambassador") -> Plan:
    return compile_sentence(text, ingress.grant_for(role), role=role)


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
    return sorted((ingress.spool_root(cfg) / role).glob("*.json"))


# ── the spool ───────────────────────────────────────────────────────────────────────────────────


def test_a_request_is_spooled_under_its_role_and_names_no_role_itself(cfg: Any) -> None:
    receipt = ingress.write_request(cfg, role="ambassador", plan=_plan("do dream"))
    assert receipt.state == "spooled" and receipt.kind == "script" and receipt.job is None
    assert "sentence" not in receipt.to_dict()           # the request file is the text's one home
    (path,) = _spooled(cfg, "ambassador")
    doc = json.loads(path.read_text())
    assert doc["id"] == receipt.request and doc["sentence"] == "do dream"
    assert "role" not in doc                      # the role is the directory, never a field
    # a query is not a request and is never spooled
    with pytest.raises(ValueError, match="not a request"):
        ingress.write_request(cfg, role="ambassador", plan=compile_sentence('near "x"'))
    # a script the library does not hold is refused when spoken, before anything is written
    with pytest.raises(ParseError, match="no library script 'research'"):
        ingress.write_request(cfg, role="cli", plan=_plan('do research(question: "q")', "cli"))
    assert len(_spooled(cfg, "cli")) == 0


def test_the_roles_grants_decide_what_the_ingress_admits() -> None:
    assert ingress.roles() == ("ambassador", "cli")          # a role nothing writes for is a hole
    assert ingress.grant_for("cli") is OPERATOR
    assert ingress.grant_for("ambassador") in (AMBASSADOR_OVERLAY, ingress.AMBASSADOR)
    for intruder in ("intruder", "heartbeat", "watcher", "mcp", "webui", "owner"):
        with pytest.raises(IllScopedSentence, match="knows no role"):
            ingress.grant_for(intruder)
    # the operator may say what the Ambassador may not: a script that starts a commit-clock job
    # (ING-1), by name or inline
    for text in ("do sync_code", "do observe_code", 'do { run "code_sync" }'):
        _plan(text, "cli")
        with pytest.raises(IllScopedSentence):
            _plan(text, "ambassador")


def test_the_kinds_are_the_queues_kinds(cfg: Any) -> None:
    """A bare call of a library script the table maps to one of the queue's coalescing kinds is
    that kind, so it coalesces with the watcher's and the heartbeat's rows; every other request is
    a `script` job, in the interactive lane when the table marks its script so."""
    def kind(text: str, role: str = "cli") -> tuple[str, str]:
        term = _plan(text, role).term
        assert isinstance(term, ast.Do)
        return ingress.kind_of(term)[0], ingress.lane_of(term)

    assert kind("do sync_vault") == ("vault_sync", "bulk")
    assert kind("do sync_dialogue") == ("dialogue_sync", "bulk")
    # with an argument it is a script of its own: the coalescing row syncs every reader
    assert kind('do sync_dialogue(reader: "opencode")') == ("script", "bulk")
    assert kind('do capture(text: "t")', "ambassador") == ("script", "interactive")
    for text in ("do dream", "do curate", "do relate", "do sync_code", "do sync_chat",
                 "do observe_code", 'do ingest_doc(path: "docs/LAWS.md")',
                 'do { store "x" in "observed" at "dialogue/ingress/cli/x" }'):
        assert kind(text) == ("script", "bulk"), text
    router = Router(cfg)
    pinned = cfg.pinned_model.tier
    assert all(router.tier_for(k) == pinned for k in ("script", "code_observe", "dialogue_sync"))
    assert router.tier_for("relate") == "synthesis"


# ── the drain ───────────────────────────────────────────────────────────────────────────────────


def test_the_drain_binds_the_role_to_the_spool_and_keeps_text_out_of_the_queue(cfg: Any) -> None:
    queue, router = _Queue(), Router(cfg)
    ingress.write_request(cfg, role="cli", plan=_plan("do sync_vault", "cli"))
    capture = 'do capture(text: "remember the milk", conversation: "tea")'
    ingress.write_request(cfg, role="ambassador", plan=_plan(capture))
    assert drain_spool(queue, router, cfg) == 2
    by_kind = {j["kind"]: j for j in queue.jobs}
    assert by_kind["vault_sync"]["payload"] == {}             # the watcher's job, as today
    assert by_kind["vault_sync"]["priority"] == PRIORITY_BACKGROUND
    cap = by_kind["script"]
    assert set(cap["payload"]) == {"role", "request", "digest", "lane"}
    assert cap["payload"]["role"] == "ambassador" and cap["payload"]["lane"] == "interactive"
    assert "milk" not in json.dumps(cap["payload"])           # the text stays in the request
    assert cap["priority"] == PRIORITY_INTERACTIVE           # above background, below reactive
    assert _spooled(cfg, "ambassador") == [] and _spooled(cfg, "cli") == []
    staged = ingress.read_request(cfg, "ambassador", cap["payload"]["request"])  # the daemon's copy
    assert staged.sentence == capture
    receipt = ingress.read_receipt(cfg, "ambassador", cap["payload"]["request"])
    assert receipt is not None and receipt.state == "queued"
    assert receipt.job == _job_id(queue, "script")
    # a coalescing kind keeps no copy: its job names no request
    assert sorted(p.name for p in (ingress.spool_root(cfg) / "cli" / "queued").iterdir()) == []
    assert drain_spool(queue, router, cfg) == 0               # nothing waits twice


def _job_id(queue: _Queue, kind: str) -> int:
    return next(i + 1 for i, j in enumerate(queue.jobs) if j["kind"] == kind)


def test_a_forged_request_is_bounded_by_its_spool(cfg: Any) -> None:
    """A request written into the Ambassador's spool naming a script the Ambassador may not say
    (one that starts a commit-clock job, by name or inline) is refused by the spool's grant and
    never enqueued; its own text names no role."""
    queue, router = _Queue(), Router(cfg)
    spool = ingress.spool_root(cfg) / "ambassador"
    spool.mkdir(parents=True)
    forged = {"f0f0f0f0f0f0f0f0": "do sync_code", "f1f1f1f1f1f1f1f1": 'do { run "code_sync" }'}
    for rid, sentence in forged.items():
        (spool / f"{rid}.json").write_text(json.dumps(
            {"id": rid, "sentence": sentence, "role": "cli", "at": "now"}))
    assert drain_spool(queue, router, cfg, report=lambda _m: None) == 0
    assert queue.jobs == []
    for rid in forged:
        assert not (spool / f"{rid}.json").exists()
        receipt = ingress.read_receipt(cfg, "ambassador", rid)
        assert receipt is not None and receipt.state == "refused"
        assert "IllScopedSentence" in str(receipt.detail.get("reason"))
    # a spool the ingress does not know is left as it is: not drained, not touched
    (ingress.spool_root(cfg) / "intruder").mkdir()
    foreign = ingress.spool_root(cfg) / "intruder" / "0123456789abcdef.json"
    foreign.write_text(json.dumps({"id": "0123456789abcdef", "sentence": "do dream"}))
    assert drain_spool(queue, router, cfg) == 0 and queue.jobs == [] and foreign.exists()
    assert not (ingress.spool_root(cfg) / "intruder" / "receipts").exists()


def test_a_request_is_trusted_only_as_a_regular_file_named_by_its_id(cfg: Any) -> None:
    """A file whose id is not its name, that is not an object, that is over the cap, or that is
    not a regular file (a FIFO would hang a reader) is moved to `rejected/` and reported; none
    stops the drain, and nothing of a file's content ever names a path."""
    import os
    queue, router = _Queue(), Router(cfg)
    ingress.ensure_spools(cfg)
    spool = ingress.spool_root(cfg) / "ambassador"
    bad = {
        "a1a1a1a1a1a1a1a1.json": json.dumps({"id": "../../../dialogue/x", "sentence": "do dream"}),
        "b2b2b2b2b2b2b2b2.json": "null",
        "c3c3c3c3c3c3c3c3.json": json.dumps({"id": "c3c3c3c3c3c3c3c3", "sentence": 7}),
        "d4d4d4d4d4d4d4d4.json": json.dumps({"id": "d4d4d4d4d4d4d4d4",
                                             "sentence": "x" * (ingress.MAX_REQUEST_BYTES + 1)}),
    }
    for name, text in bad.items():
        (spool / name).write_text(text)
    os.mkfifo(spool / "e5e5e5e5e5e5e5e5.json")
    ingress.write_request(cfg, role="ambassador", plan=_plan("do dream"))
    said: list[str] = []
    assert drain_spool(queue, router, cfg, report=said.append) == 1
    assert [j["kind"] for j in queue.jobs] == ["script"]
    rejected = sorted(p.name for p in (spool / "rejected").iterdir())
    assert rejected == sorted([*bad, "e5e5e5e5e5e5e5e5.json"])
    assert _spooled(cfg, "ambassador") == [] and len(said) == 5
    assert not (ingress.spool_root(cfg).parent / "dialogue").exists()   # where ../../../ led
    # the handler side: a queued id is checked before it names a path
    with pytest.raises(IllScopedSentence, match="not a request id"):
        ingress.read_request(cfg, "ambassador", "../../x")


def test_a_spool_writable_by_those_it_should_not_be_is_not_drained(cfg: Any) -> None:
    """The operator's spool is the daemon account's alone: group- or world-writable, it is
    reported once and not drained; the agents' spool may be group-writable, never
    world-writable."""
    import os
    import stat
    queue, router = _Queue(), Router(cfg)
    ingress.write_request(cfg, role="cli", plan=_plan("do dream", "cli"))
    spool = ingress.spool_root(cfg) / "cli"
    mode = stat.S_IMODE(spool.stat().st_mode)
    for loose in (stat.S_IWGRP, stat.S_IWOTH):
        os.chmod(spool, mode | loose)
        said: list[str] = []
        assert drain_spool(queue, router, cfg, report=said.append) == 0
        assert len(_spooled(cfg, "cli")) == 1 and any("not drained" in m for m in said)
    os.chmod(spool, mode)
    assert drain_spool(queue, router, cfg) == 1
    amb = ingress.spool_root(cfg) / "ambassador"
    os.chmod(amb, stat.S_IMODE(amb.stat().st_mode) | stat.S_IWOTH)
    ingress.write_request(cfg, role="ambassador",
                       plan=_plan("do dream"))
    said = []
    assert drain_spool(queue, router, cfg, report=said.append) == 0
    assert any("writable by others" in m for m in said)


def test_the_drain_is_bounded_a_tick_and_a_role(cfg: Any) -> None:
    queue, router = _Queue(), Router(cfg)
    for _ in range(3):
        ingress.write_request(cfg, role="ambassador",
                           plan=_plan("do dream"))
    assert drain_spool(queue, router, cfg, max_per_tick=2) == 2
    assert len(_spooled(cfg, "ambassador")) == 1
    assert drain_spool(queue, router, cfg) == 1
    assert [j["payload"]["role"] for j in queue.jobs].count("ambassador") == 3   # counted by role


def test_a_full_lane_refuses_and_never_holds_the_other_lane(cfg: Any) -> None:
    """The quotas refuse, they do not hold: a role's bulk lane full of dreams refuses the next
    dream as busy (receipted, dropped), and its captures, the interactive lane, still land."""
    queue, router = _Queue(), Router(cfg)
    amb = ingress.grant_for("ambassador")
    quotas = {"interactive": 2, "bulk": 2}
    for _ in range(3):
        ingress.write_request(cfg, role="ambassador", plan=_plan("do dream"))
    capture = ingress.write_request(cfg, role="ambassador",
                                 plan=compile_sentence('do capture(text: "note this")', amb,
                                                       role="ambassador"))
    assert drain_spool(queue, router, cfg, quotas=quotas) == 3     # two dreams and the capture
    lanes = [j["payload"]["lane"] for j in queue.jobs]
    assert lanes.count("bulk") == 2 and lanes.count("interactive") == 1
    assert _spooled(cfg, "ambassador") == []                         # the third dream: refused
    busy = [ingress.read_receipt(cfg, "ambassador", p.stem)
            for p in (ingress.spool_root(cfg) / "ambassador" / "receipts").iterdir()]
    assert sum(1 for r in busy if r is not None and r.state == "refused"
               and "busy" in str(r.detail.get("reason"))) == 1
    receipt = ingress.read_receipt(cfg, "ambassador", capture.request)
    assert receipt is not None and receipt.state == "queued"


def test_a_surface_refuses_to_deepen_a_full_spool(cfg: Any, monkeypatch: Any) -> None:
    monkeypatch.setattr(ingress, "MAX_SPOOLED", 2)
    for _ in range(2):
        ingress.write_request(cfg, role="ambassador", plan=_plan("do dream"))
    with pytest.raises(ingress.Busy):
        ingress.write_request(cfg, role="ambassador", plan=_plan("do dream"))
    assert len(_spooled(cfg, "ambassador")) == 2


def test_a_queued_request_is_never_overwritten(cfg: Any) -> None:
    queue, router = _Queue(), Router(cfg)
    receipt = ingress.write_request(cfg, role="cli", plan=_plan("do dream", "cli"))
    assert drain_spool(queue, router, cfg) == 1
    replay = ingress.spool_root(cfg) / "cli" / f"{receipt.request}.json"
    replay.write_text(json.dumps({"id": receipt.request, "sentence": "do dream"}))
    said: list[str] = []
    assert drain_spool(queue, router, cfg, report=said.append) == 0
    assert not replay.exists() and (replay.parent / "rejected" / replay.name).exists()
    assert len(queue.jobs) == 1 and any("never reused" in m for m in said)
    again = ingress.read_receipt(cfg, "cli", receipt.request)
    assert again is not None and again.state == "queued"     # the first request's, untouched


class _Crash(BaseException):
    """The process dies: no handler of the drain's runs."""


def test_a_request_lands_once_however_many_jobs_name_it(palace: Palace, monkeypatch: Any) -> None:
    """A crash between the enqueue and the receipt leaves the request in the spool and its job in
    the queue; the next tick enqueues it again. The landing is idempotent at the request: the
    second job finds it receipted as landed and lands nothing."""
    cfg = palace.cfg
    queue, router = _Queue(), Router(cfg)
    ingress.write_request(cfg, role="ambassador", plan=_plan('do capture(text: "once")'))
    write_receipt = ingress.write_receipt

    def crash(*_a: Any, **_k: Any) -> Any:
        raise _Crash

    monkeypatch.setattr(ingress, "write_receipt", crash)
    with pytest.raises(_Crash):
        drain_spool(queue, router, cfg)             # enqueued, then the process dies
    monkeypatch.setattr(ingress, "write_receipt", write_receipt)
    drain_spool(queue, router, cfg)                 # the next tick enqueues it again
    payloads = [j["payload"] for j in queue.jobs if j["kind"] == "script"]
    assert len(payloads) == 2 and payloads[0]["request"] == payloads[1]["request"]
    handle = ingress_handler(cfg, stores=lambda: palace.stores)
    handle(_job(payloads[0]))
    summary = handle(_job(payloads[1]))
    assert "landed already" in str(summary)
    assert len(palace.stores.catalog.active_entries()) == 1 and palace.att.count() == 1


# ── the handler ─────────────────────────────────────────────────────────────────────────────────


def _job(payload: dict[str, Any], kind: str = "script") -> Job:
    return Job(id=7, kind=kind, tier="pinned", num_ctx=1, priority=0, state="running",
               payload=payload, result=None, error=None, attempts=1, checkpoint=None,
               created_at="", started_at=None, finished_at=None)


def _drained(queue: _Queue, kind: str = "script") -> dict[str, Any]:
    return next(j["payload"] for j in queue.jobs if j["kind"] == kind)


def test_the_handler_compiles_again_lands_observed_and_writes_the_receipt(palace: Palace) -> None:
    cfg = palace.cfg
    queue, router = _Queue(), Router(cfg)
    ingress.write_request(cfg, role="ambassador",
                       plan=_plan('do capture(text: "a thought", conversation: "tea")'))
    drain_spool(queue, router, cfg)
    payload = _drained(queue)
    rid = payload["request"]
    summary = ingress_handler(cfg, stores=lambda: palace.stores)(_job(payload))
    assert summary is not None and "landed" in summary
    (entry,) = palace.stores.catalog.active_entries()
    assert entry.source_path.startswith("dialogue/ingress/ambassador/tea/")
    assert str(entry.provenance) == "observed"
    receipt = ingress.read_receipt(cfg, "ambassador", rid)
    assert receipt is not None and receipt.state == "landed" and receipt.job == 7
    assert receipt.detail["effects"] == {"landed": 1} and receipt.detail["work"] > 0
    (landed,) = receipt.detail["changed"]
    assert landed["path"] == entry.source_path and landed["digest"] == entry.digest
    (att_id,) = landed["attestations"]                         # what `witness` reads back
    att = palace.att.get(att_id)
    assert att is not None and set(att.output_hashes) == {entry.digest}
    assert "sentence" not in receipt.to_dict()
    assert not (ingress.spool_root(cfg) / "ambassador" / "queued" / f"{rid}.json").exists()


def test_the_handler_lands_only_the_request_that_was_drained(palace: Palace) -> None:
    """The job's payload carries the sentence's digest and the kind the drain compiled; a queued
    file rewritten after the drain, or a job whose kind is not the sentence's, lands nothing."""
    cfg = palace.cfg
    queue, router = _Queue(), Router(cfg)
    ingress.write_request(cfg, role="ambassador", plan=_plan('do capture(text: "a thought")'))
    drain_spool(queue, router, cfg)
    payload = _drained(queue)
    queued = ingress.spool_root(cfg) / "ambassador" / "queued" / f"{payload['request']}.json"
    queued.write_text(json.dumps({"id": payload["request"], "sentence": "do relate(pairs: 50)"}))
    handle = ingress_handler(cfg, stores=lambda: palace.stores)
    with pytest.raises(IllScopedSentence, match="not the sentence that was drained"):
        handle(_job(payload))
    receipt = ingress.read_receipt(cfg, "ambassador", payload["request"])
    assert receipt is not None and receipt.state == "refused"
    assert palace.stores.catalog.active_entries() == [] and palace.jobs == []
    assert "refused already" in str(handle(_job(payload)))   # a refused request stays refused
    # the digest right, the kind wrong: a script job never runs a coalescing kind's request
    ingress.write_request(cfg, role="ambassador", plan=_plan('do capture(text: "another")'))
    drain_spool(queue, router, cfg)
    second = [j["payload"] for j in queue.jobs if j["kind"] == "script"][-1]
    queued = ingress.spool_root(cfg) / "ambassador" / "queued" / f"{second['request']}.json"
    queued.write_text(json.dumps({"id": second["request"], "sentence": "do sync_vault"}))
    forged = {**second, "digest": ingress.sentence_digest("do sync_vault")}
    with pytest.raises(IllScopedSentence, match="compiles to vault_sync"):
        handle(_job(forged))
    assert palace.stores.catalog.active_entries() == []


def test_the_handler_refuses_what_the_spools_grant_refuses_before_landing(palace: Palace) -> None:
    """The second check: a queued request whose role may not say its sentence (here, one written
    straight into `queued/`) lands nothing and is receipted as refused."""
    cfg = palace.cfg
    ingress.ensure_spools(cfg)
    queued = ingress.spool_root(cfg) / "ambassador" / "queued"
    rid = "1a7e1a7e1a7e1a7e"
    (queued / f"{rid}.json").write_text(json.dumps({"id": rid, "sentence": "do observe_code"}))
    handle = ingress_handler(cfg, stores=lambda: palace.stores)
    with pytest.raises(IllScopedSentence):
        handle(_job({"role": "ambassador", "request": rid,
                     "digest": ingress.sentence_digest("do observe_code")}))
    assert palace.jobs == []
    receipt = ingress.read_receipt(cfg, "ambassador", rid)
    assert receipt is not None and receipt.state == "refused"
    assert not (queued / f"{rid}.json").exists()           # a refused request is spent


def test_a_script_its_evaluation_refuses_lands_nothing_and_is_receipted(palace: Palace) -> None:
    """A request admitted when spoken can still be refused when evaluated (here, a path that is
    no item of the source): nothing lands, and the receipt says why."""
    cfg = palace.cfg
    queue, router = _Queue(), Router(cfg)
    ingress.write_request(cfg, role="ambassador",
                       plan=_plan('do ingest_doc(path: "data/query_log.jsonl")'))
    drain_spool(queue, router, cfg)
    payload = _drained(queue)
    with pytest.raises(ScriptError, match="not an item of the source"):
        ingress_handler(cfg, stores=lambda: palace.stores)(_job(payload))
    receipt = ingress.read_receipt(cfg, "ambassador", payload["request"])
    assert receipt is not None and receipt.state == "refused"
    assert "ScriptError" in str(receipt.detail["reason"])
    assert palace.stores.catalog.active_entries() == []


def test_a_source_opens_only_its_own_items(palace: Palace, tmp_path: Path) -> None:
    """`file` names an item of a directory source or nothing: under its location, matching its
    pattern, outside its excluded directories, spelled as the disk spells it; a vault configured
    through a symlink names its notes as the sync names them. What is no item is not there."""
    from core.ingest.readers import PalaceView
    from core.ingest.table import build_table

    vault = palace.vault
    (vault / "pages").mkdir()
    (vault / ".recycle").mkdir()
    (vault / "pages" / "a.md").write_text("- a\n")
    (vault / ".recycle" / "gone.md").write_text("- gone\n")
    (vault / "pages" / "scan.pdf").write_bytes(b"%PDF")
    (tmp_path / "outside.md").write_text("- outside\n")
    (tmp_path / "link").symlink_to(vault, target_is_directory=True)
    linked = replace(palace.cfg, ingestion=replace(
        palace.cfg.ingestion, vault=replace(palace.cfg.ingestion.vault, path=tmp_path / "link")))
    view = PalaceView(build_table(linked), "ambassador", palace.stores.catalog, refresh=False)
    notes = view.open("vault")
    assert str(view.file(notes, "pages/a.md")["path"]) == str(tmp_path / "link" / "pages" / "a.md")
    for path in (".recycle/gone.md", "pages/scan.pdf", "pages/missing.md", "../outside.md",
                 str(tmp_path / "outside.md"), "PAGES/a.md", "pages/A.md", ".RECYCLE/gone.md"):
        with pytest.raises(ScriptError):
            view.file(notes, path)
        assert not view.exists(notes, path), path
    docs = view.open("docs")
    assert str(view.file(docs, "docs/LAWS.md")["path"]).endswith("docs/LAWS.md")
    for path in ("data/query_log.jsonl", "config/defaults.toml", "pyproject.toml", "../etc"):
        with pytest.raises(ScriptError):
            view.file(docs, path)


# ── the surface ─────────────────────────────────────────────────────────────────────────────────


def test_ask_logged_writes_the_request_and_returns_the_receipt(cfg: Any, tmp_path: Path) -> None:
    from core.sentence.surface import QueryLog, ask_logged

    class _E:
        config = cfg

    log = QueryLog(tmp_path / "log.jsonl")
    answer = ask_logged("do dream", ingress.grant_for("ambassador"), surface="mcp",
                        role="ambassador", engine=_E(), log=log, trace=True)   # type: ignore[arg-type]
    (hit,) = answer.hits
    assert hit.ref.startswith("ingress:") and hit.stratum == "ingress" and hit.title == "dream"
    assert hit.detail["state"] == "spooled" and hit.detail["role"] == "ambassador"
    assert hit.detail["kind"] == "script"
    assert len(_spooled(cfg, "ambassador")) == 1
    assert answer.trace is not None and any(s.stage == "act" for s in answer.trace.steps)
    assert log.entries()[-1].outcome == "requested"
    # a captured text never enters the query log: a string is logged as its length
    ask_logged('do capture(text: "remember the milk")', ingress.grant_for("ambassador"),
               surface="mcp", role="ambassador", engine=_E(), log=log)   # type: ignore[arg-type]
    assert log.entries()[-1].sentence == 'do capture(text: "<17>")'
    assert "milk" not in (tmp_path / "log.jsonl").read_text()
    # an inline script is titled as one, its text never
    (hit,) = ask_logged('do { store "secret words" in "observed" at '
                        '"dialogue/ingress/ambassador/x" }',
                        ingress.grant_for("ambassador"), surface="mcp", role="ambassador",
                        engine=_E(), log=log).hits            # type: ignore[arg-type]
    assert hit.title == "inline script" and "secret" not in json.dumps(hit.detail)
    # `--as` labels the asker; the CLI speaks to the ingress as `cli`, whatever the label
    import io

    from core.sentence.surface import run_query
    out = io.StringIO()
    assert run_query(["--as", "owner", "--json", "do dream"], out=out, engine=_E(),   # type: ignore[arg-type]
                     log=log) == 0
    assert len(_spooled(cfg, "cli")) == 1 and not (ingress.spool_root(cfg) / "owner").exists()
    assert log.entries()[-1].role == "owner"
    # the Ambassador may not say a commit-clock script, at the ingress as everywhere
    with pytest.raises(IllScopedSentence):
        ask_logged("do sync_code", ingress.grant_for("ambassador"), surface="mcp",
                   role="ambassador", engine=_E(), log=log)   # type: ignore[arg-type]
    assert log.entries()[-1].outcome == "refused"


def test_the_surface_refuses_at_once_what_the_checking_pass_sees(cfg: Any) -> None:
    """What the checking pass can see is refused when spoken, before anything is spooled: a script
    the library does not hold, a parameter it does not take or one it needs, a store whose content
    may carry a label the place does not take (R2), a place or a job the table does not hold, a job
    the role's grant does not admit. What only the evaluation sees (a path outside the role's
    namespace, a job's argument past its bound) the writer refuses, and the receipt says so."""
    for text in ('do research(question: "x")', "do dream(bogus: 1)", "do capture",
                 'do { store "x" in "mirror_authored" at "a.md" }',
                 'do { store "x" in "nowhere" at "a" }', 'do { run "nojob" }', "do sync_code"):
        with pytest.raises((ParseError, ScriptError, IllScopedSentence)):
            ingress.write_request(cfg, role="ambassador", plan=_plan(text))
    assert _spooled(cfg, "ambassador") == []


def test_every_mcp_alias_is_a_request_the_ambassador_may_say(cfg: Any, monkeypatch: Any) -> None:
    """The MCP's write tools are aliases of ingress requests: each one's sentence compiles under the
    Ambassador's grant and is spooled, so no tool is a name the ingress refuses."""
    from agents.ambassador.mcp import Ambassador

    said: list[str] = []

    def query(self: Any, sentence: str, trace: bool = False) -> dict[str, Any]:
        said.append(sentence)
        return {}

    monkeypatch.setattr(Ambassador, "query", query)
    tools = Ambassador.__new__(Ambassador)          # the aliases need no engine
    tools.sync_dialogue()
    tools.sync_notes()
    tools.dream()
    tools.relate(5)
    tools.capture('a "quoted" thought\non two lines', "tea")
    tools.link("a.md", "b.md", "supports")
    assert len(said) == 6
    for sentence in said:
        receipt = ingress.write_request(cfg, role="ambassador", plan=_plan(sentence))
        assert receipt.state == "spooled"


def test_the_daemon_makes_the_spools_with_their_modes(cfg: Any, monkeypatch: Any) -> None:
    """The root: the daemon adds every entry (`755`). The operator's spool: the owner's account
    alone (`700`). The agents' spool: under a dedicated group, the group writes and the sticky bit
    guards (`3770`, the setgid bit the platform's to grant), and only their receipts are the
    group's to read; `queued/` and `rejected/` are the daemon's alone."""
    import stat
    monkeypatch.setattr(ingress, "_EVERYONE_GROUPS", frozenset())   # the tmp dir's group: dedicated
    assert ingress.ensure_spools(cfg) == ["ambassador", "cli"]
    root = ingress.spool_root(cfg)
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
    root = ingress.spool_root(cfg)
    root.parent.mkdir(parents=True)
    group = ingress._group_name(os.stat(root.parent).st_gid)
    monkeypatch.setattr(ingress, "_EVERYONE_GROUPS", frozenset({group}))
    assert ingress.ensure_spools(cfg) == ["ambassador", "cli"]
    amb = root / "ambassador"
    assert stat.S_IMODE(amb.stat().st_mode) & 0o777 == 0o700
    os.chmod(amb, 0o3770)
    said: list[str] = []
    assert ingress.ensure_spools(cfg, report=said.append) == ["cli"]
    assert any("holds every local account" in m for m in said)


def test_a_symlinked_spool_is_never_followed(cfg: Any, tmp_path: Path) -> None:
    """A symlink in a spool's place, or in the root's, is not a directory the daemon drains: the
    role (or every role) is reported and left, and the other roles are served."""
    root = ingress.spool_root(cfg)
    root.parent.mkdir(parents=True)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    root.mkdir(mode=0o755)
    (root / "cli").symlink_to(elsewhere, target_is_directory=True)
    rid = "0123456789abcdef"
    (elsewhere / f"{rid}.json").write_text(json.dumps({"id": rid, "sentence": "do sync_code"}))
    ingress.write_request(cfg, role="ambassador", plan=_plan("do dream"))
    said: list[str] = []
    queue, router = _Queue(), Router(cfg)
    assert drain_spool(queue, router, cfg, report=said.append) == 1
    assert [j["kind"] for j in queue.jobs] == ["script"]                # the other role served
    assert (elsewhere / f"{rid}.json").exists() and not (elsewhere / "queued").exists()
    assert any("cli spool is not drained" in m for m in said)
    # the root itself a symlink: nothing is drained
    cfg2 = replace(cfg, interface=replace(cfg.interface, handoff_dir=tmp_path / "h2"))
    (tmp_path / "h2").mkdir()
    (tmp_path / "h2" / "ingress").symlink_to(root, target_is_directory=True)
    said = []
    assert drain_spool(_Queue(), router, cfg2, report=said.append) == 0
    assert any("nothing is drained" in m for m in said)


def test_a_ingress_sync_coalesces_with_a_waiting_row_and_never_with_a_running_one(cfg: Any) -> None:
    """The note's §6 falsifier, on the real queue: a `do sync_vault` drained while the watcher's
    `vault_sync` waits is that row (the watcher's job, as today); drained while one runs, it is a
    second row, so a follow-up pass is never swallowed by the pass already reading the state."""
    from scheduler.queue import QUEUED, RUNNING, JobQueue
    queue, router = JobQueue(Path(":memory:")), Router(cfg)
    plan = router.plan("vault_sync")
    waiting = queue.enqueue(plan.kind, plan.tier, plan.num_ctx, priority=plan.priority)
    ingress.write_request(cfg, role="cli", plan=_plan("do sync_vault", "cli"))
    assert drain_spool(queue, router, cfg) == 1
    assert [j.id for j in queue.list(QUEUED)] == [waiting.id]          # coalesced
    running = queue.claim()
    assert running is not None and running.id == waiting.id
    ingress.write_request(cfg, role="cli", plan=_plan("do sync_vault", "cli"))
    assert drain_spool(queue, router, cfg) == 1
    (follow_up,) = queue.list(QUEUED)
    assert follow_up.id != waiting.id and follow_up.kind == "vault_sync"
    assert [j.id for j in queue.list(RUNNING)] == [waiting.id]
    # a bare `do sync_dialogue` is the queue's own coalescing kind, like the other syncs
    for _ in range(2):
        ingress.write_request(cfg, role="cli", plan=_plan("do sync_dialogue", "cli"))
    assert drain_spool(queue, router, cfg) == 2
    assert [j.kind for j in queue.list(QUEUED)].count("dialogue_sync") == 1


# ── the second review's falsifiers ──────────────────────────────────────────────────────────────


def test_the_operators_spool_takes_only_the_daemon_accounts_requests(cfg: Any,
                                                                     monkeypatch: Any) -> None:
    """A request in the operator's spool written by another account is rejected; the agents'
    spool is the group's to write, so there the same file is read."""
    import os
    ingress.ensure_spools(cfg)
    rid = "abcdefabcdefabcd"
    said: list[str] = []
    for role in ("cli", "ambassador"):
        f = ingress.spool_root(cfg) / role / f"{rid}.json"
        f.write_text(json.dumps({"id": rid, "sentence": "do dream"}))
        real = os.getuid()
        monkeypatch.setattr(ingress.os, "getuid", lambda real=real: real + 1)
        got = ingress._load_request(f, role, said.append)
        monkeypatch.undo()
        assert (got is None) == (role == "cli")
    assert any("the cli spool is the daemon account's alone" in m for m in said)


def test_a_hard_linked_or_symlinked_request_is_rejected(cfg: Any) -> None:
    """A writer that keeps a second name for its request could change it after the daemon's check;
    a symlink at a request's name could point at a pipe. Both are rejected, and nothing blocks."""
    import os
    ingress.ensure_spools(cfg)
    spool = ingress.spool_root(cfg) / "ambassador"
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
    amb = ingress.grant_for("ambassador")
    receipt = ingress.write_request(cfg, role="ambassador",
                                 plan=compile_sentence('do capture(text: "again")', amb,
                                                       role="ambassador"))
    assert drain_spool(queue, router, cfg) == 1
    staged = ingress.spool_root(cfg) / "ambassador" / "queued" / f"{receipt.request}.json"
    # the landing fails: the receipt says so and the daemon's copy stays
    ingress.write_receipt(cfg, ingress.Receipt(receipt.request, "ambassador", "script", "failed"))
    staged.replace(ingress.spool_root(cfg) / "ambassador" / staged.name)   # the operator re-spools
    assert drain_spool(queue, router, cfg) == 1
    again = ingress.read_receipt(cfg, "ambassador", receipt.request)
    assert again is not None and again.state == "queued" and again.job == 2


def test_an_orphaned_ingress_job_goes_back_to_the_queue(tmp_path: Path) -> None:
    """A crash mid-landing leaves an ingress job RUNNING; the next start's sweep puts it back in the
    queue (it is re-runnable at the request), where a dream it left is failed as before."""
    from scheduler.queue import _IDEMPOTENT_KINDS, _REQUEUE_KINDS, FAILED, QUEUED, JobQueue
    assert _REQUEUE_KINDS - _IDEMPOTENT_KINDS == ingress.INGRESS_KINDS | {"relate", "code_observe"}
    queue = JobQueue(tmp_path / "q.sqlite")
    cap = queue.enqueue("script", "pinned", 1, payload={"role": "ambassador",
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
            if kind == "script":
                raise RuntimeError("database is locked")
            return super().enqueue(kind, tier, num_ctx, priority=priority, payload=payload)

    queue, router = _Broken(), Router(cfg)
    first = ingress.write_request(cfg, role="cli", plan=_plan("do dream", "cli"))
    ingress.write_request(cfg, role="cli", plan=_plan("do sync_vault", "cli"))
    said: list[str] = []
    assert drain_spool(queue, router, cfg, report=said.append) == 1
    assert [j["kind"] for j in queue.jobs] == ["vault_sync"]
    failed = ingress.read_receipt(cfg, "cli", first.request)
    assert failed is not None and failed.state == "failed" and "locked" in str(failed.detail)
    assert (ingress.spool_root(cfg) / "cli" / "rejected" / f"{first.request}.json").exists()


def test_the_serve_loop_survives_a_drain_that_raises(capsys: Any) -> None:
    from ops.lifecycle.launcher import drain_guarded

    def broken() -> int:
        raise OSError("disk full")

    assert drain_guarded(broken) == 0 and drain_guarded(lambda: 3) == 3
    assert "the drain failed this tick (OSError: disk full)" in capsys.readouterr().out


def test_a_library_job_whose_call_fails_fails_after_the_others_run(palace: Palace) -> None:
    """The queue's own kinds run library scripts (`library_handler`): a call that fails fails the
    job, after the calls beside it have run, so the queue shows it and the rest still land."""
    handle = library_handler(palace.cfg, "relate", [{"pairs": 3}, {"bogus": 1}, {"pairs": 4}],
                             stores=lambda: palace.stores)
    with pytest.raises(RuntimeError, match="no parameter 'bogus'|has no parameter 'bogus'"):
        handle(_job({}, kind="relate"))
    assert palace.jobs == [("relate", {"pairs": 3}), ("relate", {"pairs": 4})]


def test_prune_keeps_a_week_and_never_a_copy_whose_job_may_run(cfg: Any) -> None:
    import os
    import time as _time
    ingress.ensure_spools(cfg)
    base = ingress.spool_root(cfg) / "ambassador"
    old, new = "aaaaaaaaaaaaaaaa", "bbbbbbbbbbbbbbbb"
    ingress.write_receipt(cfg, ingress.Receipt(old, "ambassador", "script", "failed"))
    ingress.write_receipt(cfg, ingress.Receipt(new, "ambassador", "script", "queued"))
    for rid in (old, new):
        ingress.stage(cfg, ingress.Request(rid, "ambassador", 'do capture(text: "x")', ""))
    (base / "rejected" / "junk.json").write_text("{}")
    week_ago = _time.time() - ingress.PRUNE_AFTER_S - 60
    for f in [*(base / "receipts").iterdir(), *(base / "queued").iterdir(),
              *(base / "rejected").iterdir()]:
        os.utime(f, (week_ago, week_ago))
    # the failed request's copy, both receipts and the rejected file; the copy whose receipt said
    # `queued` is kept, since its job may still run
    assert ingress.prune(cfg) == 4
    assert (base / "queued" / f"{new}.json").exists()
    assert not (base / "queued" / f"{old}.json").exists()



# ── the third review's falsifiers ───────────────────────────────────────────────────────────────


def test_a_text_that_escapes_past_the_cap_is_refused_at_the_surface(cfg: Any) -> None:
    """A command under the sentence cap can still write a file over the daemon's cap, since
    escaping grows a text (a quote takes two bytes, a control character six): the surface refuses
    what the daemon would reject, so nothing is spooled that can never land."""
    from core.sentence.script import quote
    text = "\x01" * 11_000
    with pytest.raises(ValueError, match="as written"):
        ingress.write_request(cfg, role="ambassador",
                           plan=_plan(f"do capture(text: {quote(text)})"))
    assert _spooled(cfg, "ambassador") == []


def test_a_rejected_request_is_receipted_once_and_never_over_a_seen_one(cfg: Any) -> None:
    ingress.ensure_spools(cfg)
    spool = ingress.spool_root(cfg) / "ambassador"
    rid = "9999aaaa9999aaaa"
    (spool / f"{rid}.json").write_text("null")
    drain_spool(_Queue(), Router(cfg), cfg, report=lambda _m: None)
    receipt = ingress.read_receipt(cfg, "ambassador", rid)
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
    ingress.ensure_spools(cfg)
    spool = ingress.spool_root(cfg) / "ambassador"
    (spool / "abababababababab.json").mkdir()
    ingress.write_request(cfg, role="ambassador",
                       plan=_plan("do dream"))
    said: list[str] = []
    assert drain_spool(_Queue(), Router(cfg), cfg, report=said.append) == 1
    moved = spool / "rejected" / "abababababababab.json"
    assert moved.is_dir()
    week_ago = _time.time() - ingress.PRUNE_AFTER_S - 60
    os.utime(moved, (week_ago, week_ago))
    assert ingress.prune(cfg) >= 0 and moved.is_dir()          # skipped, and nothing raised


def test_a_ingress_job_that_kills_the_process_is_failed_on_the_third_start(tmp_path: Path) -> None:
    from scheduler.queue import FAILED, QUEUED, JobQueue
    queue = JobQueue(tmp_path / "q.sqlite")
    job = queue.enqueue("script", "pinned", 1, payload={"role": "ambassador",
                                                        "request": "0" * 16, "digest": "d"})
    for run in (11, 12):
        assert queue.claim() is not None
        assert queue.sweep_orphans(active_run_id=run).requeued == (job.id,)
        assert queue.get(job.id).state == QUEUED
    assert queue.claim() is not None
    assert queue.sweep_orphans(active_run_id=13).failed == (job.id,)
    assert queue.get(job.id).state == FAILED


def test_the_edge_readers_find_podman_where_homebrew_keeps_it(monkeypatch: Any) -> None:
    from core.ingest.readers import edge_env
    monkeypatch.setenv("PATH", "/usr/bin:/bin")
    path = edge_env()["PATH"].split(":")
    assert path[:2] == ["/usr/bin", "/bin"] and "/opt/homebrew/bin" in path


def test_only_the_daemons_account_makes_the_spools(cfg: Any, monkeypatch: Any) -> None:
    """A surface running as another account (the agents', under the split) never makes the
    spools: the daemon does, so no other account owns `ingress/` and can rename what lies in it."""
    import os
    real = os.getuid()
    ingress.spool_root(cfg).parent.mkdir(parents=True)
    monkeypatch.setattr(ingress.os, "getuid", lambda: real + 1)
    with pytest.raises(PermissionError, match="the daemon's to make"):
        ingress.write_request(cfg, role="ambassador",
                           plan=_plan("do dream"))
    assert not ingress.spool_root(cfg).exists()


def test_relate_pairs_zero_judges_none(cfg: Any, monkeypatch: Any) -> None:
    """The `relate` job a script starts judges the pairs it was given, none when given none, and
    the default when the payload names no count (the heartbeat's job)."""
    import core.relations as relations
    from ops.lifecycle.launcher import _relate
    asked: list[int] = []

    def detector(_cfg: Any, *, max_pairs: int) -> Any:
        asked.append(max_pairs)
        return type("D", (), {"run": staticmethod(lambda: "ran")})()

    monkeypatch.setattr(relations, "build_relation_detector", detector)
    _relate(cfg)(_job({"pairs": 0}, kind="relate"))
    _relate(cfg)(_job({}, kind="relate"))
    assert asked == [0, 24]


def test_a_receipt_names_only_its_own_actions_attestations() -> None:
    from core.ingest.landing import attested_by

    class _Att:
        def __init__(self, action: str) -> None:
            self.action = action

    class _Ledger:
        held = {"a1": _Att("capture"), "a2": _Att("ingest_note")}

        def producers_of(self, hashes: set[str]) -> set[str]:
            return set(self.held)

        def get(self, att_id: str) -> Any:
            return self.held.get(att_id)

    attestor: Any = type("A", (), {"store": _Ledger()})()
    assert attested_by(attestor, "capture", "d") == ["a1"]
    assert attested_by(attestor, "ingest_note", "d") == ["a2"]


# ── the audits of the second form (2026-11-05) ──────────────────────────────────────────────────


def test_a_job_a_script_starts_counts_against_its_roles_share_and_starts_once(cfg: Any) -> None:
    """A request's `run` was a job no quota saw: one request could queue hundreds of dreams. A job
    a script starts now carries its role and counts against the role's bulk lane; past the share
    it is refused as busy; a plan starts a job once; a script run again after a crash finds the
    job it started; a coalescing kind still folds into the row that waits."""
    from core.ingest.table import build_table
    from core.ingest.writer import Stores, Writer
    from core.sentence.interpret import RunEff
    from scheduler.ingress import job_enqueuer
    from scheduler.queue import JobQueue

    queue, router = JobQueue(Path(":memory:")), Router(cfg)
    enqueue = job_enqueuer(queue, router, quotas={"interactive": 2, "bulk": 2})
    stores = Stores(raw=None, plane=None, embedder=None, catalog=None, enqueue=enqueue)
    table = build_table(cfg)

    def land(plan: list[Any], request: str | None = None) -> list[str]:
        w = Writer(table, "ambassador", stores, has=lambda _p: False, request=request)
        return [o.status + (":" + o.why if o.why else "") for o in w.land(plan)]

    assert land([RunEff("dream", ()), RunEff("dream", ())], "r1")[1].startswith("refused:R1")
    assert land([RunEff("dream", ())], "r1") == ["queued"]           # the same request: found
    assert len(queue.list("queued")) == 1
    assert land([RunEff("curate", ())], "r2") == ["queued"]
    (busy,) = land([RunEff("dream", ())], "r3")
    assert busy.startswith("refused:R1") and "busy" in busy
    assert {j.payload.get("ingress") for j in queue.list("queued")} == {"ambassador"}
    land([RunEff("code_sync", ())], "r4")                             # coalescing: no role
    land([RunEff("code_sync", ())], "r5")
    assert [j.kind for j in queue.list("queued")].count("code_sync") == 1


def test_a_receipt_says_refused_when_every_effect_was(palace: Palace) -> None:
    cfg = palace.cfg
    queue, router = _Queue(), Router(cfg)
    ingress.write_request(cfg, role="ambassador",
                       plan=_plan('do { store "x" in "observed" at "dialogue/ingress/cli/x" }'))
    drain_spool(queue, router, cfg)
    payload = _drained(queue)
    summary = ingress_handler(cfg, stores=lambda: palace.stores)(_job(payload))
    assert summary is not None and "refused" in summary
    receipt = ingress.read_receipt(cfg, "ambassador", payload["request"])
    assert receipt is not None and receipt.state == "refused"
    assert receipt.detail["effects"] == {"refused": 1}


def test_the_ambassador_may_not_say_a_commit_clock_script_through_a_call(cfg: Any) -> None:
    """ING-1 for a request whose script calls another: the checker collects the requirements of
    every script it calls (the formal audit's mutation, a checker that did not descend into
    `call`, would admit this)."""
    with pytest.raises(IllScopedSentence):
        _plan("do { call sync_code }", "ambassador")
    _plan("do { call sync_code }", "cli")


def test_the_mcp_relate_refuses_a_bound_it_cannot_land(monkeypatch: Any) -> None:
    from agents.ambassador.mcp import Ambassador

    monkeypatch.setattr(Ambassador, "query", lambda self, sentence, trace=False: {})
    tools = Ambassador.__new__(Ambassador)
    with pytest.raises(ValueError, match="from 0 to 50"):
        tools.relate(51)
    tools.relate(50)


def test_the_dialogue_readers_are_the_tables_and_the_scripts(cfg: Any) -> None:
    from core.ingest.table import build_table
    from core.sentence.script import load
    from scheduler.ingress import DIALOGUE_READERS

    sources = {n.split("/", 1)[1] for n in build_table(cfg).sources if n.startswith("dialogue/")}
    assert set(DIALOGUE_READERS) == sources
    text = (Path(__file__).resolve().parents[2] / "ingress" / "sync_dialogue.palace").read_text()
    assert all(f'"{r}"' in text for r in sources)
    load("sync_dialogue")


# ── the first form's stored state, taken over ───────────────────────────────────────────────────


def test_a_legacy_door_spool_is_adopted_with_nothing_lost_and_nothing_run_twice(cfg: Any) -> None:
    """A request the first form spooled under `door/`, its receipts and its staged copy move into
    `ingress/` by the daemon: the pending one drains once, a receipted id stays seen, a surface
    finds its receipt, and a file that is not a request id's, or is not regular, stays put."""
    import os
    ingress.ensure_spools(cfg)
    old = ingress.spool_root(cfg).parent / ingress.LEGACY_SPOOL
    for role in ("ambassador", "cli"):
        for sub in ("", "queued", "receipts", "rejected"):
            (old / role / sub).mkdir(parents=True)
    pending, done = "a1a1a1a1a1a1a1a1", "b2b2b2b2b2b2b2b2"
    (old / "ambassador" / f"{pending}.json").write_text(
        json.dumps({"id": pending, "sentence": "do dream", "at": "2026-11-05T00:00:00"}))
    (old / "ambassador" / f"{done}.json").write_text(      # drained before the daemon stopped
        json.dumps({"id": done, "sentence": "do dream", "at": "2026-11-05T00:00:00"}))
    (old / "ambassador" / "receipts" / f"{done}.json").write_text(
        json.dumps({"request": done, "role": "ambassador", "kind": "script", "state": "queued",
                    "job": 7}))
    (old / "ambassador" / "notes.txt").write_text("not a request")
    os.symlink("/etc/hosts", old / "ambassador" / "c3c3c3c3c3c3c3c3.json")
    assert ingress.ensure_spools(cfg) == ["ambassador", "cli"]
    new = ingress.spool_root(cfg)
    assert (new / "ambassador" / f"{pending}.json").exists()
    assert not (old / "ambassador" / f"{pending}.json").exists()
    receipt = ingress.read_receipt(cfg, "ambassador", done)
    assert receipt is not None and receipt.job == 7 and ingress.seen(cfg, "ambassador", done)
    assert (old / "ambassador" / "notes.txt").exists()
    assert os.path.islink(old / "ambassador" / "c3c3c3c3c3c3c3c3.json")
    queue, router = _Queue(), Router(cfg)
    assert drain_spool(queue, router, cfg) == 1 and [j["kind"] for j in queue.jobs] == ["script"]
    assert ingress.ensure_spools(cfg) == ["ambassador", "cli"]
    assert drain_spool(queue, router, cfg) == 0 and len(queue.jobs) == 1
    assert ingress.read_receipt(cfg, "ambassador", pending).state == "queued"  # type: ignore[union-attr]
    assert (new / "ambassador" / "rejected" / f"{done}.json").exists()   # the replay is set aside


def test_a_job_naming_its_role_under_door_is_read_as_ingress(cfg: Any) -> None:
    from scheduler.ingress import _ingress_role
    queue = _Queue()
    first = queue.enqueue("vault_sync", "small", 1, payload={"door": "ambassador"})
    now = queue.enqueue("vault_sync", "small", 1, payload={"ingress": "cli"})
    assert _ingress_role(first) == "ambassador" and _ingress_role(now) == "cli"


def test_a_role_retires_under_a_prefix_it_only_retires_and_writes_only_its_own(cfg: Any) -> None:
    """ING-15's two parts on the table (R3): the Ambassador's own prefix takes a store and a
    retire; the first form's prefix, which it only retires, takes a retire and never a store; a
    path in neither takes neither, and a path that leaves either by `..` is not normal."""
    from core.ingest.table import LEGACY_DIALOGUE, build_table

    table = build_table(cfg)
    own = "dialogue/ingress/ambassador/c/1"
    legacy = LEGACY_DIALOGUE + "ambassador/c/1"
    for place in ("dialogue", "observed"):
        assert table.may_write("ambassador", place, own)
        assert table.may_retire("ambassador", place, own)
        assert table.may_retire("ambassador", place, legacy)
        assert not table.may_write("ambassador", place, legacy)
        for other in ("dialogue/ingress/cli/c/1", LEGACY_DIALOGUE + "cli/c/1",
                      LEGACY_DIALOGUE + "ambassador/../cli/c/1"):
            assert not table.may_write("ambassador", place, other), other
            assert not table.may_retire("ambassador", place, other), other
    # the operator's role writes every path, so it has no prefix it only retires
    assert table.may_write("cli", "dialogue", legacy) and table.roles["cli"].retire_only == {}
